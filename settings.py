import csv
import requests
from io import StringIO
from config import SETTINGS_CSV_URL


def load_notification_settings():
    response = requests.get(SETTINGS_CSV_URL)
    response.raise_for_status()

    rows = list(csv.reader(StringIO(response.text)))

    settings = {}

    for row in rows[1:]:
        if len(row) >= 4:
            settings[row[0]] = {
                "enabled": row[1].strip().upper() == "ON",
                "condition": row[2].strip(),
                "value": float(row[3])
            }

    return settings
