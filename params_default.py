from datetime import datetime, timedelta

##################################################
# General CSV Settings
##################################################

# Format settings
CSV_DELIMITER = ","
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M-%H:%M"

# Column header identifiers
DATE_ROW_INDEX = 0
ROOM_ROW_INDEX = 1
SESSION_START_ROW_INDEX = 2

# Session parsing format
SESSION_NAME_REGEX = r"^(.*?)(?=\s*\[|\n|$)"
SESSION_TRACK_REGEX = r"\[(.*?)\]"
SESSION_DESC_REGEX = r"^[^\n]*\n(.*)$"

# Abstract placeholder (zero-width space U+200B)
SESSION_ABSTRACT = "\u200B"

##################################################
# General Pretalx Settings
##################################################

# Admin
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "admin"
ADMIN_NAME = "admin"
ADMIN_TEAM = "admin team"

# Organizer
ORGANIZER_SLUG = "organizer"
ORGANIZER_NAME = "organizer"

# Event
TIMEZONE = "CET"
EVENT_SCHEDULE_MODE = "grid"
EVENT_PRIMARY_COLOR = None
EVENT_HEADER_IMAGE = None
EVENT_LOGO = None

##################################################
# User Settings
##################################################

# CSV file path
CSV_FILE = "input.csv"

# Columns filtering
START_DATE = "2000-01-01"
END_DATE = "3000-01-01"

# Actions
ACTION_DELETE_ALL_ONLY = False
ACTION_DELETE_ALL = True
ACTION_EXPORT_HTML = True
ACTION_REBUILD = True

# Event
EVENT_SLUG = "default"
EVENT_NAME = "Default Event"
EVENT_DATE = datetime(2100, 1, 1)
EVENT_END_DATE = EVENT_DATE
SCHEDULE_RELEASE_NAME = "1.0"

# Tracks
TRACKS = []

# Rooms
ROOMS = ["Default Room"]
