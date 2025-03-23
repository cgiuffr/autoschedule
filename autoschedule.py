import csv
import sys
import re
import django
import os
import pytz

from django_scopes import scope, scopes_disabled
from django.core.files import File
from django.core.management import call_command

# Set up Django environment (adjust path as needed)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pretalx.settings")
django.setup()

from pretalx.mail.models import MailTemplate
from pretalx.schedule.models import Room, TalkSlot, Schedule
from pretalx.submission.models import Submission, SubmissionType, Track, CfP
from pretalx.person.models import User
from pretalx.event.models import Event, Organiser, Team
from datetime import datetime, timedelta

try:
    import params as p
except ImportError:
    print("Please create params.py based on params_default.py first.")
    sys.exit(1)


class Session:
    def __init__(self, name, track, description, start_time, end_time, abstract):
        self.name = name
        self.track = track
        self.start_time = start_time
        self.end_time = end_time
        self.abstract = abstract

        self.description = description

    def __str__(self):
        return (
            f"Session: {self.name} | Track: {self.track} | {self.start_time}-{self.end_time}\n"
            f"Description: {self.description}\n"
            f"Abstract: {self.abstract}"
        )


class Day:
    def __init__(self, date, room):
        self.date = date
        self.room = room
        self.sessions = []

    def add_session(self, session):
        self.sessions.append(session)

    def __str__(self):
        session_details = "\n".join(str(session) for session in self.sessions)
        return f"Date: {self.date} | Room: {self.room}\n{session_details}"


def parse_session_data(session_text, room):
    """Extracts session name, track, and description from the given text."""

    # Extract name
    name_match = re.search(p.SESSION_NAME_REGEX, session_text)
    name = name_match.group(1).strip() if name_match else None
    if not name:
        return None

    # Extract track
    track_match = re.search(p.SESSION_TRACK_REGEX, session_text)
    track = track_match.group(1).strip(
    ) if track_match else None
    if not track:
        return None

    # Extract description
    desc_match = re.search(p.SESSION_DESC_REGEX, session_text, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""

    return name, track, description


def parse_time(time_string):
    """
    Parses the start and end times from a string.
    """
    start_time_str, end_time_str = time_string.split("-")
    start_time = datetime.strptime(
        start_time_str.strip(), p.TIME_FORMAT.split("-")[0]).time()
    end_time = datetime.strptime(
        end_time_str.strip(), p.TIME_FORMAT.split("-")[1]).time()
    return start_time, end_time


def parse_csv(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=p.CSV_DELIMITER)
        data = list(reader)

    days = []

    # Identify day columns and their time columns
    date_row = data[p.DATE_ROW_INDEX]
    room_row = data[p.ROOM_ROW_INDEX]

    start_date = datetime.strptime(p.START_DATE, p.DATE_FORMAT).date()
    end_date = datetime.strptime(p.END_DATE, p.DATE_FORMAT).date()

    day_columns = {}
    time_column = None

    for col_idx, cell in enumerate(date_row):
        if room_row[col_idx] == "Time":
            time_column = col_idx
            continue
        date = datetime.strptime(cell, p.DATE_FORMAT).date()
        if date < start_date or date > end_date:
            continue
        day_columns[col_idx] = (time_column, date)

    # Parse the data
    for col_idx, t in day_columns.items():
        time_column, date = t
        room = room_row[col_idx]
        day = Day(date, room)

        for row_idx in range(p.SESSION_START_ROW_INDEX, len(data)):
            row = data[row_idx]

            if col_idx >= len(row) or not row[col_idx]:
                continue

            session_text = row[col_idx]
            ret = parse_session_data(session_text, room)
            if not ret:
                continue
            name, track, description = ret
            start_time, end_time = parse_time(row[time_column])

            session = Session(name, track, description,
                              start_time, end_time, p.SESSION_ABSTRACT)
            day.add_session(session)

        days.append(day)

    return days


def object_lookup(objects, name):
    object = None
    if objects.exists():
        for o in objects:
            if name == str(o.name):
                object = o
                break
    if not object:
        raise ValueError(
            f"Object '{name}' does not exist in event '{p.EVENT_SLUG}'.")
    return object


def create_session(event, day, session):
    # Session details
    print(f"Creating new session: {session.name}")

    # Check if the track exists, otherwise raise an error
    track = object_lookup(Track.objects.filter(event=event), session.track)

    # Check if the room exists, otherwise raise an error
    room = object_lookup(Room.objects.filter(event=event), day.room)

    # Get the submission type (or use the first one found)
    submission_type = SubmissionType.objects.filter(event=event).first()
    if not submission_type:
        raise ValueError(
            f"No default submission type found for event '{p.EVENT_SLUG}'")

    # Create the session (submission)
    submission = Submission.objects.create(
        event=event,
        submission_type=submission_type,
        title=session.name,
        description=session.description,
        abstract=session.abstract,
        track=track,
        state="confirmed",  # Possible states: submitted, accepted, confirmed, rejected
    )
    submission.save()

    # Define schedule slot (Start and End times)
    tz = pytz.timezone(p.TIMEZONE)
    start_time = tz.localize(datetime.combine(day.date, session.start_time))
    end_time = tz.localize(datetime.combine(day.date, session.end_time))

    # Create a scheduled TalkSlot
    talk_slot = TalkSlot.objects.create(
        submission=submission,
        room=room,
        start=start_time,
        end=end_time,
        schedule=event.wip_schedule
    )

    return


def create_schedule(event, days):
    for day in days:
        for session in day.sessions:
            create_session(event, day, session)
    schedule = event.wip_schedule
    schedule.freeze(name=p.SCHEDULE_RELEASE_NAME)  # Freeze and publish


def delete_existing_data():
    # Delete existing data
    existing_event = Event.objects.filter(slug=p.EVENT_SLUG).first()
    if existing_event:
        print(f"Deleting existing event '{p.EVENT_NAME}'...")
        existing_event.shred()

    existing_team = Team.objects.filter(
        organiser__slug=p.ORGANIZER_SLUG, name=p.ADMIN_TEAM).first()
    if existing_team:
        print(f"Deleting existing admin team {p.ADMIN_TEAM} exists...")
        existing_team.delete()

    existing_organizer = Organiser.objects.filter(
        slug=p.ORGANIZER_SLUG).first()
    if existing_organizer:
        print(f"Deleting existing organizer '{p.ORGANIZER_NAME}'...")
        existing_organizer.delete()

    existing_user = User.objects.filter(email=p.ADMIN_EMAIL).first()
    if existing_user:
        print(f"Deleting existing user '{p.ADMIN_EMAIL}'...")
        existing_user.delete()
    if p.ACTION_DELETE_ALL_ONLY:
        return


def create_event():
    if not p.ACTION_DELETE_ALL:
        event = Event.objects.filter(slug=p.EVENT_SLUG).first()
        if event:
            return event

    # Create a new admin user
    admin_user = User.objects.filter(name=p.ADMIN_NAME).first()
    if not admin_user:
        print(f"Creating new admin user: {p.ADMIN_EMAIL}...")
        admin_user = User.objects.create_superuser(
            email=p.ADMIN_EMAIL,
            password=p.ADMIN_PASSWORD,
            name=p.ADMIN_NAME,
            is_active=True
        )

    # Create a new organizer
    organizer = Organiser.objects.filter(name=p.ORGANIZER_NAME).first()
    if not organizer:
        print(f"Creating new organizer: {p.ORGANIZER_NAME}...")
        organizer = Organiser.objects.create(
            name=p.ORGANIZER_NAME,
            slug=p.ORGANIZER_SLUG
        )

    # Create a new admin team
    admin_team = Team.objects.filter(name=p.ADMIN_TEAM).first()
    if not admin_team:
        print(f"Creating new admin team: {p.ADMIN_TEAM}...")
        admin_team = Team.objects.create(
            organiser=organizer,
            name=p.ADMIN_TEAM,
            can_create_events=True,
            can_change_teams=True,
            can_change_organiser_settings=True,
            can_change_event_settings=True,
            can_change_submissions=True
        )
        admin_team.members.add(admin_user)  # Assign the admin user to the team

    # Create a new event under the new organizer
    print(f"Creating new event: {p.EVENT_NAME}...")
    event = Event.objects.create(
        name=p.EVENT_NAME,
        slug=p.EVENT_SLUG,
        organiser=organizer,  # Assign the newly created organizer
        date_from=p.EVENT_DATE,
        date_to=p.EVENT_END_DATE,
        timezone=p.TIMEZONE
    )

    event.email = p.ADMIN_EMAIL
    event.display_settings['schedule'] = p.EVENT_SCHEDULE_MODE
    if p.EVENT_PRIMARY_COLOR:
        event.primary_color = p.EVENT_PRIMARY_COLOR
    if p.EVENT_HEADER_IMAGE:
        with open(p.EVENT_HEADER_IMAGE, "rb") as image_file:
            event.header_image.save(os.path.basename(
                p.EVENT_HEADER_IMAGE), File(image_file))
    if p.EVENT_LOGO:
        with open(p.EVENT_LOGO, "rb") as image_file:
            event.logo.save(os.path.basename(p.EVENT_LOGO), File(image_file))
    event.save()

    return event


def create_tracks_rooms(event):
    # Add tracks
    for track_info in p.TRACKS:
        track = Track.objects.get_or_create(
            event=event,
            name=track_info["name"],
            color=track_info["color"]
        )

    # Add rooms
    for room_name in p.ROOMS:
        room = Room.objects.get_or_create(event=event, name=room_name)


def main():
    if p.ACTION_DELETE_ALL:
        delete_existing_data()
    if p.ACTION_DELETE_ALL_ONLY:
        sys.exit(0)
    event = create_event()
    create_tracks_rooms(event)

    print("Parsing CSV file...")
    days = parse_csv(p.CSV_FILE)

    create_schedule(event, days)

    if p.ACTION_EXPORT_HTML:
        try:
            if p.ACTION_REBUILD:
                call_command("rebuild")
        except Exception as e:
            pass
        try:
            if p.ACTION_REBUILD:
                call_command("compress")
        except Exception as e:
            pass
        try:
            call_command("export_schedule_html", p.EVENT_SLUG)
            print("HTML export completed successfully.")
        except Exception as e:
            print(f"Error triggering HTML export: {e}")


if __name__ == "__main__":
    with scopes_disabled():
        main()
