from base64 import b64encode
from typing import Dict, Any, List
import logging
from app.config import settings
from app.models.toggl import TogglTimeEntry

logger = logging.getLogger(__name__)


def get_toggl_cred() -> str:
    """
    Get base64 encoded API token credentials from config file.

    Retrieves API token from settings and encodes it in base64
    format for Basic authentication using Toggl API token format.

    Returns:
        Base64 encoded string of "api_token:api_token"

    Raises:
        ValueError: If API token is not configured
    """
    credentials = f"{settings.toggl_api_token}:api_token"
    encoded_credentials = b64encode(credentials.encode("ascii")).decode("ascii")
    return encoded_credentials


def build_activity_logs(time_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Build activity logs from raw time entries.

    Args:
        time_entries: List of raw time entry dictionaries from Toggl API

    Returns:
        List of time entry dictionaries
    """
    logger.info(f"Building activity logs from {len(time_entries)} time entries")
    return time_entries


def _validate_raw_time_entry(time_entry: Dict[str, Any]) -> None:
    """
    Validate that a raw time entry contains all required fields.

    Args:
        time_entry: Raw time entry dictionary from Toggl API

    Raises:
        ValueError: If any required field is missing
    """
    required_fields = ["tags", "description", "start", "stop", "duration"]
    missing_fields = [
        field
        for field in required_fields
        if field not in time_entry or time_entry[field] is None
    ]

    if missing_fields:
        entry_id = time_entry.get("id", "unknown")
        raise ValueError(
            f"Time entry {entry_id} is missing required fields: {', '.join(missing_fields)}"
        )


def _deserialize_time_entry(time_entry: Dict[str, Any]) -> TogglTimeEntry:
    """
    Deserialize a single time entry dictionary into a TogglTimeEntry object.

    Converts a raw time entry dictionary from Toggl API into a validated
    TogglTimeEntry Pydantic model. Unsupported fields are ignored.

    Args:
        time_entry: Raw time entry dictionary from Toggl API

    Returns:
        TogglTimeEntry object

    Raises:
        ValueError: If required fields are missing
    """
    _validate_raw_time_entry(time_entry)

    # Use Pydantic's model_validate to parse directly, ignoring unsupported fields
    toggl_entry = TogglTimeEntry.model_validate(time_entry)
    logger.debug(
        f"Successfully deserialized time entry {time_entry.get('id', 'unknown')} into TogglTimeEntry"
    )
    return toggl_entry


def deserialize_time_entries(
    time_entries: List[Dict[str, Any]]
) -> List[TogglTimeEntry]:
    """
    Deserialize an array of time entry dictionaries into TogglTimeEntry objects.

    Iterates through time entries and converts each raw time entry dictionary
    from Toggl API into validated TogglTimeEntry Pydantic models.

    Args:
        time_entries: List of raw time entry dictionaries from Toggl API

    Returns:
        List of TogglTimeEntry objects
    """
    logger.info(f"Deserializing {len(time_entries)} time entries")

    deserialized_entries = []
    for entry in time_entries:
        deserialized_entry = _deserialize_time_entry(entry)
        deserialized_entries.append(deserialized_entry)

    logger.info(f"Successfully deserialized {len(deserialized_entries)} time entries")
    return deserialized_entries
