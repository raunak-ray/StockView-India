import { api } from "./client";

export type Interval = "1d" | "1wk" | "1mo";
export type Period = "2y" | "5y" | "10y";

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number | null;
}

export interface HistoryResponse {
  symbol: string;
  interval: Interval;
  period: Period;
  count: number;
  candles: Candle[];
}

export interface Quote {
  symbol: string;
  price: number;
  previous_close: number | null;
  change: number | null;
  change_pct: number | null;
}

export interface InfoResponse {
  symbol: string;
  info: Record<string, unknown>;
}

export interface IndexQuote {
  name: string;
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
}

export interface MarketSummaryResponse {
  indices: IndexQuote[];
}

export interface Mover {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
}

export interface GainersLosersResponse {
  gainers: Mover[];
  losers: Mover[];
}

export async function getHistory(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
): Promise<HistoryResponse> {
  const params = new URLSearchParams({ symbol, interval, period });
  return api.get<HistoryResponse>(`/market/history?${params}`);
}

export async function getQuote(symbol: string): Promise<Quote> {
  return api.get<Quote>(`/market/quote?symbol=${encodeURIComponent(symbol)}`);
}

export async function getInfo(symbol: string): Promise<InfoResponse> {
  return api.get<InfoResponse>(`/market/info?symbol=${encodeURIComponent(symbol)}`);
}

export async function getMarketSummary(): Promise<MarketSummaryResponse> {
  return api.get<MarketSummaryResponse>("/market/market-summary");
}

export async function getGainersLosers(): Promise<GainersLosersResponse> {
  return api.get<GainersLosersResponse>("/market/gainers-losers");
}
