import os
import csv
import requests
from io import StringIO

SHEET_CSV_URL = os.environ["SHEET_CSV_URL"]
SETTINGS_CSV_URL = os.environ["SETTINGS_CSV_URL"]
GAS_WEBHOOK_URL = os.environ["GAS_WEBHOOK_URL"]


def fetch_csv(url):
    response = requests.get(url)
    response.raise_for_status()
    return list(csv.reader(StringIO(response.text)))


def load_market_data():
    rows = fetch_csv(SHEET_CSV_URL)
    return rows[1:]


def load_notification_settings():
    rows = fetch_csv(SETTINGS_CSV_URL)

    settings = {}

    for row in rows[1:]:
        if len(row) >= 4:
            settings[row[0]] = {
                "enabled": row[1].strip().upper() == "ON",
                "condition": row[2].strip(),
                "value": float(row[3])
            }

    return settings


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


def send_line(message):
    response = requests.post(GAS_WEBHOOK_URL, data=message)
    response.raise_for_status()


def should_notify(setting, latest_yield):
    if setting is None:
        return False

    if not setting["enabled"]:
        return False

    condition = setting["condition"]
    value = setting["value"]

    if condition == ">=":
        return latest_yield >= value
    elif condition == "<=":
        return latest_yield <= value
    elif condition == ">":
        return latest_yield > value
    elif condition == "<":
        return latest_yield < value
    elif condition == "==":
        return latest_yield == value

    return False


def main():
    data = load_market_data()
    settings = load_notification_settings()

    latest = data[0]
    previous = data[1]

    latest_yield = float(latest[6])
    previous_yield = float(previous[6])

    current_zone = get_zone(latest_yield)
    previous_zone = get_zone(previous_yield)

    changed = "あり" if current_zone != previous_zone else "なし"

    high_dividend_setting = settings.get("高配当通知")

    if not should_notify(high_dividend_setting, latest_yield):
        print("通知条件に一致しないため送信しません")
        return

    message = f"""📊 高配当株通知テスト

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

    send_line(message)
    print("LINE通知を送信しました")


if __name__ == "__main__":
    main()
