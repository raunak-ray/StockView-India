import { api } from "./client";
import type { Interval, Period } from "./market";

export interface NewsResponse {
  symbol: string;
  count: number;
  headlines: string[];
}

export interface HeadlineSentiment {
  headline: string;
  label: "positive" | "negative" | "neutral" | string;
  conf: number;
  score: number;
}

export interface NewsSentiment {
  score: number;
  label: "BULLISH" | "BEARISH" | "NEUTRAL" | string;
  detail: HeadlineSentiment[];
}

export interface TechnicalSignalItem {
  name: string;
  tone: "BULLISH" | "BEARISH" | "NEUTRAL" | string;
  message: string;
  weight: number;
}

export interface TechnicalSentiment {
  score: number;
  label: "BULLISH" | "BEARISH" | "NEUTRAL" | string;
  raw_score: number;
  signals: TechnicalSignalItem[];
}

export interface SentimentScoreResponse {
  symbol: string;
  finbert_available: boolean;
  news: NewsSentiment;
  technical: TechnicalSentiment;
}

export async function getNews(
  symbol: string,
  maxItems = 8,
): Promise<NewsResponse> {
  const params = new URLSearchParams({ symbol, max_items: String(maxItems) });
  return api.get<NewsResponse>(`/sentiment/news?${params}`);
}

export async function getSentimentScore(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
): Promise<SentimentScoreResponse> {
  const params = new URLSearchParams({ symbol, interval, period });
  return api.get<SentimentScoreResponse>(`/sentiment/score?${params}`);
}
