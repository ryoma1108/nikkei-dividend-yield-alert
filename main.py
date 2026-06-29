import os
import csv
import requests
from io import StringIO

SHEET_CSV_URL = os.environ["SHEET_CSV_URL"]

response = requests.get(SHEET_CSV_URL)
response.raise_for_status()

csv_text = response.text
rows = list(csv.reader(StringIO(csv_text)))

print("読み込み成功")
print("行数:", len(rows))
print("先頭行:", rows[0])
print("最新データ:", rows[1])
