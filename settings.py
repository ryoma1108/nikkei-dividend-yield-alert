import json
import requests
from config import GAS_WEBHOOK_URL


def load_notification_settings():
    payload = {
        "action": "get_settings"
    }

    response = requests.post(
        GAS_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()

    print("GAS response:", response.text)

    return response.json()
