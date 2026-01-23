from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class ActivityLogSource(str, Enum):
    """Source for activity log data."""

    TOGGL_API = "TOGGL_API"
    TOGGL_PDF = "TOGGL_PDF"


class InputConfig(BaseModel):
    """Configuration for activity log input source."""

    mode: ActivityLogSource = ActivityLogSource.TOGGL_API
    local_paths: Optional[List[str]] = None


class TogglTimeEntry(BaseModel):
    tags: List[str]
    description: str
    start: datetime
    stop: datetime
    duration: int  # seconds
