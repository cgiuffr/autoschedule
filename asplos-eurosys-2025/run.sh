#!/bin/sh

set -e

# Definitions
ROOT="$(pwd)"

EVENT="asplos-eurosys-2025"
EVENT_PRIMARY_COLOR="#0055A4"
EVENT_LOGO="media/asplos-eurosys-logo.png"

INPUT_REF_CSV="input.ref.csv"
INPUT_SPREADSHEET_ID=""
INPUT_SPREADSHEET_GID=""

PYTHON="python"
HTML_EXPORT_DIR="$("$PYTHON" -m site --user-site)/data/htmlexport"

# Clean up
cleanup() {
    "$PYTHON" -m pretalx flush --noinput
    (cd $HTML_EXPORT_DIR && rm -rf $EVENT*)
}

# Create configurations files
create_config_files() {
    cat <<EOF >params_workshops.py
import params_default as d
globals().update({k: v for k, v in vars(d).items() if not k.startswith("__")})

EVENT_LOGO = "$EVENT_LOGO"
CSV_FILE = "input.csv"
ACTION_DELETE_ALL = False
ACTION_REBUILD = False
START_DATE = "2025-03-30"
END_DATE = "2025-03-31"
TIMEZONE = "CET"
EVENT_SLUG = "asplos-eurosys-2025-workshops"
EVENT_NAME = "ASPLOS/EuroSys 2025 Workshops and Tutorials"
EVENT_DATE = datetime(2025, 3, 30)
EVENT_END_DATE = EVENT_DATE + timedelta(days=1)
EVENT_PRIMARY_COLOR = "$EVENT_PRIMARY_COLOR"
TRACKS = [
    {"name": "ASPLOS",          "color": "#8B0000"},
    {"name": "EuroSys",         "color": "#3B5998"},
    {"name": "ASPLOS+EuroSys",  "color": "#6A0DAD"},
    {"name": "ASPLOS Tutorial", "color": "#006B3F"},
    {"name": "Catering area",   "color": "#DAA520"},
    {"name": "Postillion Hotel, back side", "color": "#DAA520"},
    {"name": "SS Rotterdam",    "color": "#DAA520"}
]
ROOMS = [
    "Empty",
    "Mees I",
    "Mees II",
    "Penn I",
    "Penn II",
    "Leeuwen I",
    "Leeuwen II",
    "Goudriaan I",
    "Goudriaan II",
    "J.F. Staal",
    "New York I",
    "New York II",
    "Tokyo",
    "Blue",
    "Rotterdam hall 1A",
    "Rotterdam hall 1B",
    "Mees",
    "Diamond",
    "Van Oldebarneveldt",
    "Penn"
]
EOF

    cat <<EOF >params_conference.py
import params_workshops as d
globals().update({k: v for k, v in vars(d).items() if not k.startswith("__")})

START_DATE = "2025-04-01"
END_DATE = "2025-04-03"
EVENT_SLUG = "asplos-eurosys-2025"
EVENT_NAME = "ASPLOS/EuroSys 2025 Conference"
EVENT_DATE = datetime(2025, 4, 1)
EVENT_END_DATE = EVENT_DATE + timedelta(days=2)
EOF
}

# Create CSV
create_input_csv() {
    rm -f input.csv

    if [ -z "$INPUT_REF_CSV" ]; then
        CSV_URL="https://docs.google.com/spreadsheets/d/$INPUT_SPREADSHEET_ID/export?format=csv&gid=$INPUT_SPREADSHEET_GID"

        curl -L -o input.csv "$CSV_URL"
    else
        cp $INPUT_REF_CSV input.csv
    fi
}

# Generate HTML
generate_html() {
    cp params_workshops.py ../params.py
    "$PYTHON" ../autoschedule.py

    cp params_conference.py ../params.py
    "$PYTHON" ../autoschedule.py
}

merge_html() {
    mkdir $HTML_EXPORT_DIR/$EVENT-merged
    (cd $HTML_EXPORT_DIR/$EVENT && cp -r * ../$EVENT-merged)
    (cd $HTML_EXPORT_DIR/$EVENT-workshops && cp -r * ../$EVENT-merged)
    cp $ROOT/media/* $HTML_EXPORT_DIR/$EVENT-merged/media
    cp $ROOT/static/* $HTML_EXPORT_DIR/$EVENT-merged/static
}

fix_home_page() {
    sed -i '/<div class="row mb-4 url-links">/,/<\/div>/c\
    <div class="row mb-4 url-links">\
        <a class="btn btn-success btn-lg btn-block" href="/asplos-eurosys-2025/schedule">View conference schedule</a>\
    </div>\
    <div class="row mb-4 url-links">\
        <a class="btn btn-success btn-lg btn-block" href="/asplos-eurosys-2025-workshops/schedule/">View workshop\/tutorial schedule</a>\
    </div>' $1
}

fix_schedule_page() {
    if [ "$1" = "Conference" ]; then
        #sed -i 's/\/speaker\//-workshops\/schedule/g' $2
        prefix="asplos-eurosys-2025"
        other_prefix="asplos-eurosys-2025-workshops"
        other="Workshops"
    else
        #sed -i 's/-workshops\/speaker\//\/schedule/g' $2
        prefix="asplos-eurosys-2025-workshops"
        other_prefix="asplos-eurosys-2025"
        other="Conference"
    fi
    # Change Speakers to Conference/Workshops button and add Map button
    sed -i "s/$prefix\/speaker/$other_prefix\/schedule/g" $2
    sed -i "s/Speakers/$other<\/a><a href=\"\/media\/postillion-floorplan.pdf\" class=\"btn btn-outline-success\">Map/g" $2

    # Fix horizontal scroll on mobile and no-room sessions
    sed -i 's|</head>|<link rel="stylesheet" type="text/css" href="/static/extras.css" /><script src="/static/extras.js"></script></head>|' $2

}

fix_primary_color() {
    find $1 -type f -name "*.css" -exec sed -i "s/#3aa57c/$EVENT_PRIMARY_COLOR/g" {} +
}

# Run
echo "*** Building html files..."
cleanup
create_config_files
create_input_csv
generate_html

echo "*** Merging html files..."
merge_html

echo "*** Postprocessing..."
cd $HTML_EXPORT_DIR/$EVENT-merged
fix_home_page $EVENT/index.html
fix_schedule_page "Conference" $EVENT/schedule/index.html
fix_schedule_page "Conference" $EVENT/talk/index.html
fix_schedule_page "Workshops" $EVENT-workshops/schedule/index.html
fix_schedule_page "Workshops" $EVENT-workshops/talk/index.html
fix_primary_color .

if type upload &>/dev/null; then
    echo "*** Uploading..."
    upload .
fi