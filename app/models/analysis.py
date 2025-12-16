from pydantic import BaseModel
from datetime import date
from typing import Optional, Dict, Any


class CreateAnalysisRequest(BaseModel):
    date: date
    use_llm: Optional[bool] = False


class AnalysisResponse(BaseModel):
    status: str
    date: date
    metrics: Dict[str, Any]
    categories: Dict[str, Any]

