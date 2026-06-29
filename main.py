import os
import csv
import requests
from io import StringIO

# =========================
# 設定
# =========================
SHEET_CSV_URL = os.environ["SHEET_CSV_URL"]
GAS_WEBHOOK_URL = os.environ["GAS_WEBHOOK_URL"]

# =========================
# CSV取得
# =========================
response = requests.get(SHEET_CSV_URL)
response.raise_for_status()

rows = list(csv.reader(StringIO(response.text)))

# ヘッダーを除く
data = rows[1:]

# 最新行
latest = data[0]

# データ取得
data_date = latest[1]
nikkei = latest[2]
per = latest[3]
pbr = latest[4]
eps = latest[5]
dividend = latest[6]

message = f"""📊 テスト

データ日付：{data_date}

日経平均：{nikkei}

PER：{per}
PBR：{pbr}
EPS：{eps}

配当利回り：{dividend}%"""

# =========================
# LINE送信
# =========================
response = requests.post(GAS_WEBHOOK_URL, data=message)

print(response.text)
