def get_zone(yield_value):
    if yield_value >= 2.5:
        return "🔴 歴史的チャンス"
    elif yield_value >= 2.2:
        return "🟢 積極買い"
    elif yield_value >= 2.0:
        return "🟡 買い始め"
    elif yield_value >= 1.8:
        return "👀 監視開始"
    else:
        return "⚪ 対象外"


def zone_changed(current_zone, previous_zone):
    return current_zone != previous_zone
