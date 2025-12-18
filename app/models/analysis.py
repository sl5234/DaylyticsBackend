from pydantic import BaseModel
from enum import Enum
from typing import List
from app.models.toggl import TogglTimeEntry


class ResponseMode(str, Enum):
    TEXT = "TEXT"
    TABLE = "TABLE"
    METRIC = "METRIC"


class CreateAnalysisRequest(BaseModel):
    StartDate: str
    EndDate: str
    ResponseMode: ResponseMode
    ActivityLogs: List[TogglTimeEntry]


class OutputConfig(BaseModel):
    S3OutputPath: str


class AnalysisResponse(BaseModel):
    AnalysisRid: str
    OutputConfig: OutputConfig
