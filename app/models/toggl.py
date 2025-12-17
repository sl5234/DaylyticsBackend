from pydantic import BaseModel
from datetime import datetime
from typing import List


class TogglTimeEntry(BaseModel):
    tags: List[str]
    description: str
    start: datetime
    stop: datetime
    duration: int  # seconds

