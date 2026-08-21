from __future__ import annotations

from pydantic import BaseModel


class Instrument(BaseModel):
    name: str
    ticker: str


class InstrumentListResponse(BaseModel):
    count: int
    instruments: list[Instrument]


class InstrumentSearchResponse(BaseModel):
    query: str
    count: int
    results: list[Instrument]
