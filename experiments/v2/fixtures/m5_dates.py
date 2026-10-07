from datetime import date, datetime, timedelta, timezone


def daterange(start: date, end: date):
    """Yield every date from start to end, inclusive."""
    d = start
    while d < end:
        yield d
        d += timedelta(days=1)


def business_days(start: date, end: date) -> int:
    """Number of Monday-Friday dates from start to end, inclusive."""
    return sum(1 for d in daterange(start, end) if d.weekday() < 5)


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, _days_in_month(year, month))
    return date(year, month, day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        return 31
    return (date(year, month + 1, 1) - date(year, month, 1)).days


def parse_timestamp(value: str) -> datetime:
    """Parse ISO-8601; naive timestamps are taken to be UTC."""
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def age_in_years(born: date, today: date) -> int:
    years = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        years -= 1
    return years


def quarter(d: date) -> int:
    return d.month // 3 + 1


def overlaps(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    """True if the inclusive ranges [a_start, a_end] and [b_start, b_end] share a day."""
    return a_start <= b_end and b_start <= a_end
