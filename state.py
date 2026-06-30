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


def get_state(key, default=""):
    payload = {
        "action": "get_state",
        "key": key
    }

    result = post_json(payload)

    if result == "" or result is None:
        return default

    return result


def update_state(key, value):
    payload = {
        "action": "update_state",
        "key": key,
        "value": str(value)
    }

    post_json(payload)


def get_int_state(key, default=0):
    value = get_state(key, default)

    try:
        return int(value)
    except:
        return default


def get_float_state(key, default=0.0):
    value = get_state(key, default)

    try:
        return float(value)
    except:
        return default


def get_all_state():
    return {
        "last_zone": get_state("last_zone", "⚪ 対象外"),
        "last_zone_level": get_int_state("last_zone_level", 0),
        "last_zone_name": get_state("last_zone_name", "⚪ 対象外"),
        "last_notify_date": get_state("last_notify_date", ""),
        "last_notify_yield": get_float_state("last_notify_yield", 0.0),
        "last_notification_type": get_state("last_notification_type", ""),
        "last_notify_reason": get_state("last_notify_reason", ""),
        "last_data_date": get_state("last_data_date", ""),
        "last_notification_id": get_int_state("last_notification_id", 0),
        "version": get_int_state("version", 2),
    }


def update_notify_state(
    zone_level,
    zone_name,
    notify_date,
    notify_yield,
    notification_type,
    notify_reason,
    data_date,
):
    update_state("last_zone", zone_name)
    update_state("last_zone_level", zone_level)
    update_state("last_zone_name", zone_name)
    update_state("last_notify_date", notify_date)
    update_state("last_notify_yield", notify_yield)
    update_state("last_notification_type", notification_type)
    update_state("last_notify_reason", notify_reason)
    update_state("last_data_date", data_date)


def increment_notification_id():
    current_id = get_int_state("last_notification_id", 0)
    new_id = current_id + 1
    update_state("last_notification_id", new_id)
    return new_id
