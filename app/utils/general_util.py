from datetime import datetime, timedelta


def get_previous_date(date: str) -> str:
    """
    Get the previous day's date in the same format.

    Args:
        date: ISO-8601 datetime string (e.g., 2026-01-01T00:00:00-08:00)

    Returns:
        Previous day's date in the same ISO-8601 format
    """
    date_normalized = date.replace("Z", "+00:00")
    date_parsed = datetime.fromisoformat(date_normalized)
    previous_date_obj = date_parsed - timedelta(days=1)
    return previous_date_obj.isoformat()


def get_next_date(date: str) -> str:
    """
    Get the next day's date in the same format.

    Args:
        date: ISO-8601 datetime string (e.g., 2026-01-01T00:00:00-08:00)

    Returns:
        Next day's date in the same ISO-8601 format
    """
    date_normalized = date.replace("Z", "+00:00")
    date_parsed = datetime.fromisoformat(date_normalized)
    next_date_obj = date_parsed + timedelta(days=1)
    return next_date_obj.isoformat()
