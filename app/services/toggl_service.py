from datetime import date
from typing import Dict, Any
import logging
import httpx
from app.models.toggl import TogglDailyLogs
from app.services.helpers.toggl_service_helper import get_toggl_cred

logger = logging.getLogger(__name__)


def _authenticate_with_credentials(encoded_credentials: str) -> Dict[str, Any]:
    """
    Authenticate with Toggl Track API using base64 encoded credentials.

    Uses Basic authentication with pre-encoded credentials to reset the API token.

    Args:
        encoded_credentials: Base64 encoded "email:password" string

    Returns:
        Dictionary containing the API response with the new token

    Raises:
        httpx.HTTPStatusError: If the API request fails (403, 500, etc.)
    """
    logger.info("Authenticating with Toggl Track API")

    headers = {
        "content-type": "application/json",
        "Authorization": f"Basic {encoded_credentials}",
    }

    url = "https://api.track.toggl.com/api/v9/me/reset_token"

    with httpx.Client() as client:
        response = client.post(url, headers=headers)
        response.raise_for_status()  # Raises HTTPStatusError for 4xx/5xx responses
        logger.info("Successfully authenticated with Toggl Track API")
        return response.json()


def authenticate() -> Dict[str, Any]:
    """
    Authenticate with Toggl Track API and reset token.

    Retrieves credentials from config, encodes them, and authenticates with Toggl API.

    Returns:
        Dictionary containing the API response with the new token

    Raises:
        ValueError: If email or password is not configured
        httpx.HTTPStatusError: If the API request fails (403, 500, etc.)
    """
    encoded_credentials = get_toggl_cred()
    return _authenticate_with_credentials(encoded_credentials)


def get_daily_logs(target_date: date) -> TogglDailyLogs:
    """
    Retrieve time entries from Toggl Track API for a specific day.

    Args:
        target_date: The date to retrieve logs for

    Returns:
        TogglDailyLogs containing the day's time entries
    """
    raise NotImplementedError("Toggl Track API integration pending")
