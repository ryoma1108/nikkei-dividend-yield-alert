import requests
from config import GAS_WEBHOOK_URL


def get_state(key):
    payload = {
        "action": "get_state",
        "key": key
    }

    response = requests.post(GAS_WEBHOOK_URL, json=payload)
    response.raise_for_status()

    return response.text.strip()


def update_state(key, value):
    payload = {
        "action": "update_state",
        "key": key,
        "value": value
    }

    response = requests.post(GAS_WEBHOOK_URL, json=payload)
    response.raise_for_status()
