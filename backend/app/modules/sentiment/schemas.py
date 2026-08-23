from pydantic import BaseModel, Field


class NewsResponse(BaseModel):
    symbol: str
    count: int
    headlines: list[str]


class HeadlineSentiment(BaseModel):
    headline: str
    label: str
    conf: float
    score: float


class NewsSentiment(BaseModel):
    score: float
    label: str
    detail: list[HeadlineSentiment]


class TechnicalSignal(BaseModel):
    name: str
    tone: str
    message: str
    weight: float


class TechnicalSentiment(BaseModel):
    score: float
    label: str
    raw_score: float
    signals: list[TechnicalSignal]


class SentimentScoreResponse(BaseModel):
    symbol: str
    finbert_available: bool = Field(description="Whether the FinBERT model is installed")
    news: NewsSentiment
    technical: TechnicalSentiment
