import { api } from "./client";

export interface SymbolSnapshot {
  symbol: string;
  name: string;
  last_price: number;
  change_pct: number;
  volume: number;
  market_cap: number | null;
  pe_ratio: number | null;
  high_52w: number | null;
  low_52w: number | null;
  sma_20: number | null;
  sma_50: number | null;
  rsi: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_hist: number | null;
}

export interface NormalizedPoint {
  date: string;
  values: Record<string, number>;
}

export interface CompareResult {
  symbols: SymbolSnapshot[];
  normalized: NormalizedPoint[];
  period: string;
}

export async function getCompare(
  symbols: string[],
  period = "1y",
): Promise<CompareResult> {
  const params = new URLSearchParams({
    symbols: symbols.join(","),
    period,
  });
  return api.get<CompareResult>(`/compare?${params}`);
}
