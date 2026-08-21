import { api } from "./client";
import type { Interval, Period } from "./market";

export interface SeriesPoint {
  time: string;
  value: number;
}

export interface IndicatorsResponse {
  symbol: string;
  interval: Interval;
  period: Period;
  sma20: SeriesPoint[];
  sma50: SeriesPoint[];
  ema20: SeriesPoint[];
  bb_high: SeriesPoint[];
  bb_mid: SeriesPoint[];
  bb_low: SeriesPoint[];
  rsi: SeriesPoint[];
  atr: SeriesPoint[];
  macd: SeriesPoint[];
  macd_signal: SeriesPoint[];
  macd_hist: SeriesPoint[];
}

export interface SupportResistanceResponse {
  supports: number[];
  resistances: number[];
  nearest_support: number | null;
  nearest_resistance: number | null;
}

export async function getIndicators(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
): Promise<IndicatorsResponse> {
  const params = new URLSearchParams({ symbol, interval, period });
  return api.get<IndicatorsResponse>(`/analytics/indicators?${params}`);
}

export async function getSupportResistance(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
): Promise<SupportResistanceResponse> {
  const params = new URLSearchParams({ symbol, interval, period });
  return api.get<SupportResistanceResponse>(`/analytics/support-resistance?${params}`);
}
