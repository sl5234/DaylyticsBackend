from pydantic import BaseModel
from enum import Enum
from typing import List, Any, Optional
from app.models.toggl import TogglTimeEntry


class ResponseMode(str, Enum):
    TEXT = "TEXT"
    TABLE = "TABLE"
    METRIC = "METRIC"


class CreateAnalysisRequest(BaseModel):
    prompt: str
    response_mode: ResponseMode
    activity_logs: List[TogglTimeEntry]


class OutputConfig(BaseModel):
    s3_output_path: str


class CreateAnalysisResponse(BaseModel):
    analysis_rid: str
    output_config: OutputConfig
    raw_output: Optional[Any] = None
