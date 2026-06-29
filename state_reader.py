import csv
import requests
from io import StringIO
from config import STATE_CSV_URL


def load_state():
    response = requests.get(STATE_CSV_URL)
    response.raise_for_status()

    rows = list(csv.reader(StringIO(response.text)))

    state = {}

    for row in rows[1:]:
        if len(row) >= 2:
            state[row[0]] = row[1]

    return state
