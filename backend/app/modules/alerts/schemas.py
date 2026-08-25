from pydantic import BaseModel


class AlertCreate(BaseModel):
    symbol: str
    price: float
    condition: str           # "above" | "below"
    label: str               # "📈 Crosses Above" | "📉 Crosses Below"


class AlertOut(BaseModel):
    id: str
    symbol: str
    price: float
    condition: str
    label: str
    created: str
    triggered: bool


class AlertCheckResult(BaseModel):
    triggered_now: list[AlertOut]
    active: list[AlertOut]
    fired: list[AlertOut]
