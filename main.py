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

# 最新・前日データ
latest = data[0]
previous = data[1]

# 配当利回り
latest_yield = float(latest[6])
previous_yield = float(previous[6])

# =========================
# ゾーン判定
# =========================
def get_zone(yield_value):
    if yield_value >= 2.5:
        return "🔴 歴史的チャンス"
    elif yield_value >= 2.2:
        return "🟢 積極買い"
    elif yield_value >= 2.0:
        return "🟡 買い始め"
    elif yield_value >= 1.8:
        return "👀 監視開始"
    else:
        return "⚪ 対象外"

current_zone = get_zone(latest_yield)
previous_zone = get_zone(previous_yield)

changed = "あり" if current_zone != previous_zone else "なし"

message = f"""📊 ゾーン判定テスト

現在
{latest_yield:.2f}%

前日
{previous_yield:.2f}%

現在ゾーン
{current_zone}

前日ゾーン
{previous_zone}

ゾーン変化
{changed}
"""

# =========================
# LINE送信
# =========================
requests.post(GAS_WEBHOOK_URL, data=message)
