from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class TogglTimeEntry(BaseModel):
    id: int
    description: str
    start: datetime
    stop: Optional[datetime]
    duration: int  # seconds
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    tags: Optional[List[str]] = None


class TogglDailyLogs(BaseModel):
    date: str
    entries: List[TogglTimeEntry]

