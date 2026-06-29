import csv
import requests
from io import StringIO
from config import SHEET_CSV_URL


def fetch_csv(url):
    response = requests.get(url)
    response.raise_for_status()
    return list(csv.reader(StringIO(response.text)))


def load_market_data():
    rows = fetch_csv(SHEET_CSV_URL)
    return rows[1:]
