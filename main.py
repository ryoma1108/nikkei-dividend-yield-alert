from market import load_market_data
from settings import load_notification_settings
from notification import send_line
from state import get_state, update_state
from zone import get_zone


def should_notify(setting, latest_yield):
    if setting is None:
        return False

    if not setting["enabled"]:
        return False

    condition = setting["condition"]
    value = setting["value"]

    if condition == ">=":
        return latest_yield >= value
    elif condition == "<=":
        return latest_yield <= value
    elif condition == ">":
        return latest_yield > value
    elif condition == "<":
        return latest_yield < value
    elif condition == "==":
        return latest_yield == value

    return False


def main():
    data = load_market_data()
    settings = load_notification_settings()

    latest = data[0]

    latest_yield = float(latest[6])
    current_zone = get_zone(latest_yield)

    last_zone = get_state("last_zone")

    high_dividend_setting = settings.get("高配当通知")

    if not should_notify(high_dividend_setting, latest_yield):
        print("通知条件に一致しないため送信しません")
        return

    if last_zone == current_zone:
        print("前回通知ゾーンと同じため送信しません")
        return

    message = f"""📊 ゾーン変化通知

配当利回り
{latest_yield:.2f}%

前回ゾーン
{last_zone}

現在ゾーン
{current_zone}
"""

    send_line(message)
    update_state("last_zone", current_zone)

    print("ゾーン変化通知を送信しました")


if __name__ == "__main__":
    main()
