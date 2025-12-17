from pydantic import BaseModel
from enum import Enum


class ResponseMode(str, Enum):
    TEXT = "TEXT"
    TABLE = "TABLE"
    METRIC = "METRIC"


class CreateAnalysisRequest(BaseModel):
    StartDate: str
    EndDate: str
    ResponseMode: ResponseMode


class OutputConfig(BaseModel):
    S3OutputPath: str


class AnalysisResponse(BaseModel):
    AnalysisRid: str
    OutputConfig: OutputConfig
