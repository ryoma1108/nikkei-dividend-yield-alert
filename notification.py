import requests
from config import GAS_WEBHOOK_URL


def send_line(message):
    payload = {
        "action": "send_line",
        "message": message
    }

    response = requests.post(GAS_WEBHOOK_URL, json=payload)
    response.raise_for_status()
