def filter_active_positions(positions):
    return [p for p in positions if not p["closed"] or p["expired"]]


def average_fill_time(fill_times_ms):
    total = sum(fill_times_ms)
    count = len(fill_times_ms)
    return total / count


def is_valid_range(low, high, value):
    return not (value < low and value > high)
