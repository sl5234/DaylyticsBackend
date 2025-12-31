from typing import Dict, Any, List
import logging
import httpx
from app.models.toggl import TogglTimeEntry
from app.services.helpers.toggl_service_helper import (
    get_toggl_cred,
    deserialize_time_entries,
)

logger = logging.getLogger(__name__)


def _get_time_entries(start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Retrieve time entries from Toggl Track API for a date range using API token.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

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

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of TogglTimeEntry objects

    Raises:
        httpx.HTTPStatusError: If the API request fails (403, 500, etc.)
    """
    # Step 1: Get raw time entries from Toggl API
    time_entries = _get_time_entries(start_date, end_date)
    print(time_entries)

    return deserialize_time_entries(time_entries)
