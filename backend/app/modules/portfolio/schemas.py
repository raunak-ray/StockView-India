from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WatchlistAddRequest(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=32, examples=["RELIANCE.NS"])


class WatchlistItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    sort_order: int
    created_at: datetime


class WatchlistResponse(BaseModel):
    count: int
    items: list[WatchlistItemOut]


class MessageResponse(BaseModel):
    message: str
