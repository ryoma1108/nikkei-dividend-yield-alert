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
