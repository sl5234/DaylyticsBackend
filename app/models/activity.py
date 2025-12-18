from pydantic import BaseModel
from datetime import date
from enum import Enum


class Period(str, Enum):
    ONE_HOUR = "1hr"
    ONE_DAY = "1day"
    ONE_WEEK = "1week"


class Unit(str, Enum):
    INT = "int"
    MINS = "mins"
    HRS = "hrs"
    DAYS = "days"


class ActivityMetric(BaseModel):
    date: date
    period: Period
    unit: Unit
    value: float
    title: str
