from __future__ import annotations

from pydantic import BaseModel


class NseQuoteResponse(BaseModel):
    symbol: str
    company_name: str
    industry: str | None = None
    last_price: float
    open: float
    day_high: float
    day_low: float
    prev_close: float
    change: float
    change_pct: float
    week_high: float
    week_low: float
    volume: int
    vwap: float
    trading_status: str


class FiiDiiRow(BaseModel):
    date: str
    fii_buy: float
    fii_sell: float
    fii_net: float
    dii_buy: float
    dii_sell: float
    dii_net: float


class FiiDiiResponse(BaseModel):
    source: str  # nse / nsepython / moneycontrol / trendlyne / static
    rows: list[FiiDiiRow]


class AdvDecResponse(BaseModel):
    advances: int
    declines: int
    unchanged: int = 0
    source: str


class OptionChainRow(BaseModel):
    strike: float
    ce_oi: int
    ce_chg_oi: int
    ce_ltp: float
    pe_oi: int
    pe_chg_oi: int
    pe_ltp: float


class OptionChainResponse(BaseModel):
    symbol: str
    source: str
    underlying_value: float
    expiries: list[str]
    pcr: float | None = None
    max_pain: float | None = None
    rows: list[OptionChainRow]
