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

/** How many articles landed on each side. */
export interface InsightCounts {
  positive: number;
  neutral: number;
  negative: number;
}

/** The window the stored score actually covers. */
export interface InsightWindow {
  start: string | null;
  end: string | null;
}

export interface InsightNews {
  score: number;
  label: string;
  article_count: number;
  counts: InsightCounts;
  avg_confidence: number;
  window: InsightWindow;
  detail: HeadlineSentiment[];
}

/** One period card (1M / 3M / 1Y / 3Y). */
export interface SentimentPeriodCard {
  period: string;
  title: string;
  days: number;
  available: boolean;
  score: number | null;
  label: string;
  article_count: number;
  pos_count: number;
  neu_count: number;
  neg_count: number;
  avg_confidence: number;
  sentiment_change: number | null;
  window_start: string | null;
  window_end: string | null;
  price_start: number | null;
  price_end: number | null;
  price_change_pct: number | null;
}

/** One stored headline with its stored score. */
export interface StoredArticle {
  id: number | null;
  title: string;
  source: string | null;
  published_at: string | null;
  url: string | null;
  score: number;
  label: string;
}

/**
 * The one payload the news-and-mood card needs.
 *
 * `isStoredData` says where the news numbers came from: `true` from our
 * archive (pre-scored, with the period breakdown), `false` from a live scrape
 * for a stock we have never stored.
 */
export interface SentimentInsightResponse {
  symbol: string;
  isStoredData: boolean;
  source: "stored" | "live";
  news: InsightNews;
  technical: TechnicalSentiment;
  periods: Record<string, SentimentPeriodCard>;
  top_articles: StoredArticle[];
  top_positive: StoredArticle[];
  top_negative: StoredArticle[];
  model_version: string | null;
  updated_at: string | null;
  generated_at: string;
}

/**
 * News sentiment for a stock.
 *
 * Replaces the old `/sentiment/score` and `/sentiment/news` calls: the backend
 * serves stored sentiment when it has it and falls back to a live scrape when
 * it does not, and `isStoredData` tells the UI which one happened.
 */
export async function getSentimentInsight(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
): Promise<SentimentInsightResponse> {
  const params = new URLSearchParams({ symbol, interval, period });
  return api.get<SentimentInsightResponse>(`/sentiment/insight?${params}`);
}
