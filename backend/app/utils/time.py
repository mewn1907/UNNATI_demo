"""Time helpers used across engines and services."""

from datetime import datetime, timedelta


def hours_between(start: datetime, end: datetime) -> float:
    """Signed hour difference end - start."""
    return (end - start).total_seconds() / 3600.0


def format_hours_minutes(hours: float) -> str:
    """Format a duration as '18h 42m'."""
    total_minutes = max(0, int(round(hours * 60)))
    h, m = divmod(total_minutes, 60)
    return f"{h}h {m:02d}m"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def ensure_utc_naive(dt: datetime) -> datetime:
    """Strip tzinfo so naive DB datetimes compare safely."""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


def parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO-8601 input; returns None when invalid/missing."""
    if not value:
        return None
    try:
        return ensure_utc_naive(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        return None


def relative_day_label(target: datetime, now: datetime) -> str:
    """Human-friendly day label like 'Today', 'Tomorrow', or a date."""
    delta_days = (target.date() - now.date()).days
    if delta_days == 0:
        return "Today"
    if delta_days == 1:
        return "Tomorrow"
    if delta_days == -1:
        return "Yesterday"
    return target.strftime("%d %b")


def add_hours(dt: datetime, hours: float) -> datetime:
    return dt + timedelta(hours=hours)
