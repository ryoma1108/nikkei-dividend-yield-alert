import json
import requests
from config import GAS_WEBHOOK_URL


def send_line(message):
    payload = {
        "action": "send_line",
        "message": message
    }

    response = requests.post(
        GAS_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()


def create_zone_message(current_yield, previous_zone, current_zone, diff):
    if diff > 0:
        title = "📈 ゾーン上昇通知"
    else:
        title = "📉 ゾーン下落通知"

    sign = "+" if diff >= 0 else ""

    return f"""{title}

配当利回り
{current_yield:.2f}%

前回ゾーン
{previous_zone}

現在ゾーン
{current_zone}

前日比
{sign}{diff:.2f}%"""


def create_sudden_change_message(previous_yield, current_yield, current_zone):
    diff = current_yield - previous_yield
    sign = "+" if diff >= 0 else ""

    return f"""⚡ 配当利回り急変通知

前日
{previous_yield:.2f}%

現在
{current_yield:.2f}%

変化
{sign}{diff:.2f}%

現在ゾーン
{current_zone}"""


def create_status_message(current_yield, current_zone):
    return f"""📍 現在地通知

30営業日間、
ゾーン変化はありませんでした。

現在の状況をお知らせします。

配当利回り
{current_yield:.2f}%

現在ゾーン
{current_zone}"""

def create_history_summary(
    notification_type,
    previous_zone,
    current_zone,
    previous_yield,
    current_yield,
    diff_yield,
):
    sign = "+" if diff_yield >= 0 else ""

    if notification_type in ["ゾーン上昇通知", "ゾーン下落通知"]:
        return f"{previous_zone} → {current_zone}"

    if notification_type == "急変通知":
        return f"{previous_yield:.2f}% → {current_yield:.2f}%（{sign}{diff_yield:.2f}%）"

    if notification_type == "現在地通知":
        return f"30営業日経過：{current_zone}"

    return ""
