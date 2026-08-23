from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, status

from app.core.deps import get_current_user
from app.modules.nse import service
from app.modules.nse.schemas import (
    AdvDecResponse,
    FiiDiiResponse,
    FiiDiiRow,
    NseQuoteResponse,
    OptionChainResponse,
    OptionChainRow,
)

router = APIRouter(
    prefix="/nse",
    tags=["nse"],
    dependencies=[Depends(get_current_user)],
)

_UPSTREAM = HTTPException(
    status_code=status.HTTP_502_BAD_GATEWAY,
    detail="NSE feed unavailable right now.",
)


def _num(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


@router.get("/quote/{symbol}", response_model=NseQuoteResponse)
async def nse_quote(
    symbol: str = Path(..., min_length=1, max_length=32),
) -> NseQuoteResponse:
    raw = await service.get_nse_quote(symbol.strip().upper())
    price = (raw or {}).get("priceInfo") or {}
    if not price:
        raise _UPSTREAM
    meta = raw.get("metadata") or {}
    intraday = price.get("intraDayHighLow") or {}
    week = price.get("weekHighLow") or {}
    volume_block = raw.get("priceVolumeBlockData") or {}
    clean = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
    return NseQuoteResponse(
        symbol=clean,
        company_name=str(meta.get("companyName") or clean),
        industry=meta.get("industry"),
        last_price=_num(price.get("lastPrice")),
        open=_num(price.get("open")),
        day_high=_num(intraday.get("max")),
        day_low=_num(intraday.get("min")),
        prev_close=_num(price.get("previousClose")),
        change=_num(price.get("change")),
        change_pct=_num(price.get("pChange")),
        week_high=_num(week.get("max")),
        week_low=_num(week.get("min")),
        volume=int(_num(volume_block.get("totalTradedVolume"))),
        vwap=_num(price.get("vwap")),
        trading_status=str((raw.get("securityInfo") or {}).get("tradingStatus") or "—"),
    )


@router.get("/fii-dii", response_model=FiiDiiResponse)
async def fii_dii() -> FiiDiiResponse:
    data = await service.get_fii_dii()
    rows = [
        FiiDiiRow(
            date=str(r.get("Date", "")),
            fii_buy=_num(r.get("FII Buy")),
            fii_sell=_num(r.get("FII Sell")),
            fii_net=_num(r.get("FII Net")),
            dii_buy=_num(r.get("DII Buy")),
            dii_sell=_num(r.get("DII Sell")),
            dii_net=_num(r.get("DII Net")),
        )
        for r in data.get("rows", [])
    ]
    return FiiDiiResponse(source=data.get("source", "static"), rows=rows)


@router.get("/advances-declines", response_model=AdvDecResponse)
async def advances_declines() -> AdvDecResponse:
    data = await service.get_advances_declines()
    if not data or ("advances" not in data and "declines" not in data):
        raise _UPSTREAM
    return AdvDecResponse(
        advances=int(_num(data.get("advances"))),
        declines=int(_num(data.get("declines"))),
        unchanged=int(_num(data.get("unchanged"))),
        source=str(data.get("_source", "nse")),
    )


@router.get("/option-chain/{symbol}", response_model=OptionChainResponse)
async def option_chain(
    symbol: str = Path(..., min_length=1, max_length=32),
) -> OptionChainResponse:
    data = await service.get_option_chain(symbol.strip().upper())
    if not data:
        raise _UPSTREAM
    clean = symbol.strip().upper().replace(".NS", "").replace(".BO", "")
    return OptionChainResponse(
        symbol=clean,
        source=str(data.get("source", "nse")),
        underlying_value=_num(data.get("underlying_value")),
        expiries=[str(e) for e in data.get("expiries", [])],
        pcr=data.get("pcr"),
        max_pain=data.get("max_pain"),
        rows=[
            OptionChainRow(
                strike=_num(r.get("strike")),
                ce_oi=int(_num(r.get("ce_oi"))),
                ce_chg_oi=int(_num(r.get("ce_chg_oi"))),
                ce_ltp=_num(r.get("ce_ltp")),
                pe_oi=int(_num(r.get("pe_oi"))),
                pe_chg_oi=int(_num(r.get("pe_chg_oi"))),
                pe_ltp=_num(r.get("pe_ltp")),
            )
            for r in data.get("rows", [])
        ],
    )
