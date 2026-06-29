import json
import requests
from config import GAS_WEBHOOK_URL


def post_json(payload):
    response = requests.post(
        GAS_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"}
    )
    response.raise_for_status()
    return response.text.strip()


def get_state(key):
    payload = {
        "action": "get_state",
        "key": key
    }

    return post_json(payload)


def update_state(key, value):
    payload = {
        "action": "update_state",
        "key": key,
        "value": value
    }

    post_json(payload)
