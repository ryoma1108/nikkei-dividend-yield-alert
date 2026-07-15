from datetime import datetime


def normalize_date(value):
    text = str(value).strip()
    if not text:
        return ""

    text = text.replace("/", "-")
    text = text.split(" ")[0]
    text = text.split("T")[0]

    try:
        return datetime.strptime(text, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return text


def sort_market_data(data):
    return sorted(data, key=lambda row: normalize_date(row[1]), reverse=True)


def count_business_days_since_last_notify(data, last_data_date):
    normalized_last_data_date = normalize_date(last_data_date)

    if not normalized_last_data_date:
        print("last_data_date is empty; skip status notification")
        return 0, False

    count = 0

    for row in data:
        data_date = normalize_date(row[1])

        if data_date == normalized_last_data_date:
            return count, True

        count += 1

    print("last_data_date was not found in market data; skip status notification")
    return 0, False
