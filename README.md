# autoschedule
Create a conference schedule from CSV via pretalx

# Setup
```
pip install pretalx
python -m pretalx migrate
```

# Run
```
cp params_default.py params.py # And edit
./autoschedule.py
```

# Manual adjustments
```
# find HTML export in $PYTHON_DIR/site-packages/data/htmlexport
# start python -m pretalx runserver 0.0.0.0:8000 and check live version at http://127.0.0.1:8000/<your-event>/schedule
# make manual changes and retrigger HTML export manually:
# python -m pretalx rebuild
# python -m pretalx compress
# python -m pretalx export_schedule_html <your-event>
```

# Reproducing the ASPLOS/EuroSys 2025 Schedule
```
cd asplos-eurosys-2025
./run.sh # for the online digital schedule
./display-schedule.py # for the schedule as displayed on the conference screens
```

## 🐝 License

This project is licensed under the **Apache-2.0 license**. Free to use and modify.