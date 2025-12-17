from base64 import b64encode
from app.config import settings


def get_toggl_cred() -> str:
    """
    Get base64 encoded credentials from config file.

    Retrieves email and password from settings and encodes them in base64
    format for Basic authentication.

    Returns:
        Base64 encoded string of "email:password"

    Raises:
        ValueError: If email or password is not configured
    """
    email = settings.toggl_email
    password = settings.toggl_password

    if not email or not password:
        raise ValueError("Toggl email and password must be configured")

    credentials = f"{email}:{password}"
    encoded_credentials = b64encode(credentials.encode("ascii")).decode("ascii")
    return encoded_credentials
