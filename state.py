import requests
from config import GAS_WEBHOOK_URL


def update_state(key, value):
    payload = {
        "action": "update_state",
        "key": key,
        "value": value
    }

    response = requests.post(GAS_WEBHOOK_URL, json=payload)
    response.raise_for_status()
