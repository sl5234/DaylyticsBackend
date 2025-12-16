from pydantic import BaseModel
from typing import Dict, Any


class MetricsData(BaseModel):
    timestamp: str
    date: str
    categories: Dict[str, float]  # category -> hours
    total_hours: float
    metadata: Dict[str, Any] = {}

