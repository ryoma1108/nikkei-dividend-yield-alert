import json
import requests
from config import GAS_WEBHOOK_URL


def add_notification_history(
    notification_id,
    notify_datetime,
    data_date,
    notification_type,
    yield_value,
    message,
    result,
    notify_reason,
):
    payload = {
        "action": "add_notification_history",
        "notification_id": notification_id,
        "notify_datetime": notify_datetime,
        "data_date": data_date,
        "notification_type": notification_type,
        "yield_value": yield_value,
        "message": message,
        "result": result,
        "notify_reason": notify_reason,
    }

    response = requests.post(
        GAS_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )

    response.raise_for_status()
