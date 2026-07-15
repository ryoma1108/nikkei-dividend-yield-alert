from datetime import datetime

from date_utils import (
    count_business_days_since_last_notify,
    normalize_date,
    sort_market_data,
)
from market import load_market_data
from settings import load_notification_settings
from notification import (
    send_line,
    create_zone_message,
    create_sudden_change_message,
    create_status_message,
    create_history_summary,
)
from state import (
    get_all_state,
    update_notify_state,
    increment_notification_id,
)
from history import add_notification_history
from zone import get_zone, zone_changed


def get_setting_value(settings, name, default):
    setting = settings.get(name)

    if setting is None:
        return default

    value = setting.get("value")

    if value is None:
        return default

    try:
        return float(value)
    except:
        return default


def is_enabled(settings, name):
    setting = settings.get(name)

    if setting is None:
        return False

    return setting.get("enabled", False)


def main():
    data = sort_market_data(load_market_data())
    settings = load_notification_settings()
    state = get_all_state()

    sudden_change_threshold = get_setting_value(settings, "急変通知", 0.10)
    status_notify_days = int(get_setting_value(settings, "現在地通知", 30))

    latest = data[0]
    previous = data[1]

    data_date = normalize_date(latest[1])
    latest_yield = float(latest[6])
    previous_yield = float(previous[6])

    current_zone = get_zone(latest_yield)
    current_level = current_zone["level"]
    current_zone_name = current_zone["name"]

    last_level = state["last_zone_level"]
    last_zone_name = state["last_zone_name"]
    last_data_date = normalize_date(state["last_data_date"])

    print(f"current_data_date: {data_date}")
    print(f"last_data_date: {last_data_date}")
    print(f"status_notify_days: {status_notify_days}")

    diff_yield = latest_yield - previous_yield

    message = None
    notification_type = None
    notify_reason = None

    # ① ゾーン変化通知
    if is_enabled(settings, "ゾーン通知") and zone_changed(current_level, last_level):
        message = create_zone_message(
            current_yield=latest_yield,
            previous_zone=last_zone_name,
            current_zone=current_zone_name,
            diff=diff_yield,
        )

        if current_level > last_level:
            notification_type = "ゾーン上昇通知"
            notify_reason = "zone_up"
        else:
            notification_type = "ゾーン下落通知"
            notify_reason = "zone_down"

    # ② 急変通知
    elif (
        is_enabled(settings, "急変通知")
        and current_level >= 1
        and abs(diff_yield) >= sudden_change_threshold
    ):
        message = create_sudden_change_message(
            previous_yield=previous_yield,
            current_yield=latest_yield,
            current_zone=current_zone_name,
        )

        notification_type = "急変通知"
        notify_reason = "sudden_change"

    # ③ 30営業日現在地通知
    elif is_enabled(settings, "現在地通知"):
        business_days, found_last_data_date = count_business_days_since_last_notify(data, last_data_date)

        print(f"last_data_date_found: {found_last_data_date}")
        print(f"calculated_business_days: {business_days}")

        if data_date == last_data_date:
            print("notification decision: skip status notification because data_date already notified")

        elif found_last_data_date and business_days >= status_notify_days:
            message = create_status_message(
                current_yield=latest_yield,
                current_zone=current_zone_name,
            )

            notification_type = "現在地通知"
            notify_reason = "monthly_status"

        else:
            print("notification decision: skip status notification")

    if message is None:
        print("通知条件に一致しないため送信しません")
        return

    send_line(message)

    notify_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    notification_id = increment_notification_id()

    history_summary = create_history_summary(
        notification_type=notification_type,
        previous_zone=last_zone_name,
        current_zone=current_zone_name,
        previous_yield=previous_yield,
        current_yield=latest_yield,
        diff_yield=diff_yield,
    )

    add_notification_history(
        notification_id=notification_id,
        notify_datetime=notify_date,
        data_date=data_date,
        notification_type=notification_type,
        yield_value=latest_yield,
        message=history_summary,
        result="成功",
        notify_reason=notify_reason,
    )

    update_notify_state(
        zone_level=current_level,
        zone_name=current_zone_name,
        notify_date=notify_date,
        notify_yield=latest_yield,
        notification_type=notification_type,
        notify_reason=notify_reason,
        data_date=data_date,
    )

    print(f"{notification_type}を送信しました")


if __name__ == "__main__":
    main()
