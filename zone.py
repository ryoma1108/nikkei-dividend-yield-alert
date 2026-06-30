def get_zone(yield_value):
    if yield_value >= 2.5:
        return {
            "level": 4,
            "name": "🔴 歴史的割安ゾーン"
        }

    elif yield_value >= 2.2:
        return {
            "level": 3,
            "name": "🟢 割安ゾーン"
        }

    elif yield_value >= 2.0:
        return {
            "level": 2,
            "name": "🟡 注目ゾーン"
        }

    elif yield_value >= 1.8:
        return {
            "level": 1,
            "name": "👀 監視ゾーン"
        }

    else:
        return {
            "level": 0,
            "name": "⚪ 対象外"
        }


def zone_changed(current_level, previous_level):
    return current_level != previous_level


def get_zone_direction(current_level, previous_level):
    diff = current_level - previous_level

    if diff > 0:
        return "jump_up" if diff >= 2 else "up"

    elif diff < 0:
        return "jump_down" if abs(diff) >= 2 else "down"

    return "same"
