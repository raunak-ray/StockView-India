from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user
from app.modules.market_data.service import Interval, Period
from app.modules.sentiment import service
from app.modules.sentiment.schemas import (
    NewsResponse,
    NewsSentiment,
    SentimentScoreResponse,
    TechnicalSentiment,
    TechnicalSignal,
)

router = APIRouter(
    prefix="/sentiment",
    tags=["sentiment"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/news", response_model=NewsResponse)
async def news(
    symbol: str = Query(..., min_length=1, max_length=32),
    max_items: int = Query(8, ge=1, le=20),
) -> NewsResponse:
    clean = symbol.strip().upper()
    headlines = await service.get_headlines(clean, max_items)
    return NewsResponse(symbol=clean, count=len(headlines), headlines=headlines)


@router.get("/score", response_model=SentimentScoreResponse)
async def score(
    symbol: str = Query(..., min_length=1, max_length=32),
    interval: Interval = Query("1d"),
    period: Period = Query("2y"),
) -> SentimentScoreResponse:
    from app.modules.analytics import service as analytics
    from app.modules.market_data import service as market_data

    clean = symbol.strip().upper()

    headlines = await service.get_headlines(clean)
    news_sent = service.get_sentiment_score(headlines)

    candles = await market_data.get_history(clean, interval, period)
    df = analytics.candles_to_df(candles)
    df = analytics.add_indicators(df)
    tech_sent = service.compute_technical_sentiment(df)

    return SentimentScoreResponse(
        symbol=clean,
        finbert_available=service.FINBERT_OK,
        news=NewsSentiment(**news_sent),
        technical=TechnicalSentiment(
            score=tech_sent["score"],
            label=tech_sent["label"],
            raw_score=tech_sent["raw_score"],
            signals=[
                TechnicalSignal(name=n, tone=t, message=m, weight=w)
                for (n, t, m, w) in tech_sent["signals"]
            ],
        ),
    )
