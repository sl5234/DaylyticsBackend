from typing import Dict, Any, List
import logging
import httpx
from datetime import datetime
from zoneinfo import ZoneInfo
from app.models.toggl import TogglTimeEntry
from app.services.helpers.toggl_service_helper import (
    get_toggl_cred,
    deserialize_time_entries,
)
from app.utils.general_util import get_previous_date

logger = logging.getLogger(__name__)


def _filter_entries_ending_on_date(
    time_entries: List[Dict[str, Any]], target_date: str
) -> List[Dict[str, Any]]:
    """
    Filter time entries that end on the target date.

    Args:
        time_entries: List of time entry dictionaries from Toggl API
        target_date: Target date as ISO-8601 datetime string (e.g., 2026-01-01T00:00:00-08:00)

    Returns:
        List of filtered time entry dictionaries that end on target_date
    """
    filtered_entries = []
    seattle_tz = ZoneInfo("America/Los_Angeles")
    utc_tz = ZoneInfo("UTC")

    target_date_normalized = target_date.replace("Z", "+00:00")
    target_date_parsed = datetime.fromisoformat(target_date_normalized)
    if target_date_parsed.tzinfo is None:
        target_utc = target_date_parsed.replace(tzinfo=utc_tz)
    else:
        target_utc = target_date_parsed.astimezone(utc_tz)
    target_seattle = target_utc.astimezone(seattle_tz)
    target_date_str = target_seattle.strftime("%Y-%m-%d")

    for entry in time_entries:
        stop_str = str(entry.get("stop", ""))
        if stop_str:
            stop_normalized = stop_str.replace("Z", "+00:00")
            try:
                stop_parsed = datetime.fromisoformat(stop_normalized)
                if stop_parsed.tzinfo is None:
                    stop_utc = stop_parsed.replace(tzinfo=utc_tz)
                else:
                    stop_utc = stop_parsed.astimezone(utc_tz)

                stop_seattle = stop_utc.astimezone(seattle_tz)
                stop_date_str = stop_seattle.strftime("%Y-%m-%d")
                if stop_date_str == target_date_str:
                    filtered_entries.append(entry)
            except (ValueError, AttributeError) as e:
                logger.warning(
                    f"Could not parse stop time for entry {entry.get('id', 'unknown')}: {e}"
                )

    return filtered_entries


def _get_time_entries(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Retrieve time entries from Toggl Track API for a date range using API token.

    Args:
        start_date: Start date as ISO-8601 datetime string (e.g., 2026-01-01T00:00:00-08:00)
        end_date: End date as ISO-8601 datetime string (e.g., 2026-01-01T00:00:00-08:00)

    Returns:
        List of time entry dictionaries from Toggl API

    Raises:
        httpx.HTTPStatusError: If the API request fails (403, 500, etc.)
    """
    logger.info(f"Retrieving Toggl time entries from {start_date} to {end_date}")

    encoded_credentials = get_toggl_cred()

    headers = {
        "content-type": "application/json",
        "Authorization": f"Basic {encoded_credentials}",
    }

    url = "https://api.track.toggl.com/api/v9/me/time_entries"

    params = {
        "start_date": start_date,
        "end_date": end_date,
    }

    with httpx.Client() as client:
        response = client.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
        time_entries = response.json()
        logger.info(f"Successfully retrieved {len(time_entries)} time entries")
        return time_entries


def get_toggl_track_activity_logs(
    start_date: str, end_date: str
) -> List[TogglTimeEntry]:
    """
    Get activity logs for a date range.

    Retrieves time entries from Toggl API and deserializes them into TogglTimeEntry objects.
    Also includes activity logs from the previous day that end on the start_date.

    Args:
        start_date: Start date as ISO-8601 datetime string (e.g., 2026-01-01T00:00:00-08:00)
        end_date: End date as ISO-8601 datetime string (e.g., 2026-01-01T00:00:00-08:00)

    Returns:
        List of TogglTimeEntry objects

    Raises:
        httpx.HTTPStatusError: If the API request fails (403, 500, etc.)
    """
    # Step 1: Get previous day's date
    previous_date = get_previous_date(start_date)

    # Step 2: Get time entries from previous day to start_date
    previous_day_entries = _get_time_entries(previous_date, start_date)

    # Step 3: Filter entries that end on start_date
    filtered_previous_entries = _filter_entries_ending_on_date(
        previous_day_entries, start_date
    )

    # Step 4: Get raw time entries from Toggl API for the original date range
    time_entries = _get_time_entries(start_date, end_date)

    # Step 5: Merge the two lists
    all_time_entries = filtered_previous_entries + time_entries
    print(all_time_entries)

    return deserialize_time_entries(all_time_entries)
