from pydantic import BaseModel
from typing import List

class Alert(BaseModel):
    type: str
    severity: str
    message: str

class SKUAlert(BaseModel):
    sku: str
    alerts: List[Alert]

class ForecastResult(BaseModel):
    forecast: List[dict]
    alerts: List[SKUAlert]
