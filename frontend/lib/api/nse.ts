import { api } from "./client";
import type { Interval, Period } from "./market";

export interface NseQuote {
  symbol: string;
  company_name: string;
  industry: string | null;
  last_price: number;
  open: number;
  day_high: number;
  day_low: number;
  prev_close: number;
  change: number;
  change_pct: number;
  week_high: number;
  week_low: number;
  volume: number;
  vwap: number;
  trading_status: string;
}

export interface FiiDiiRow {
  date: string;
  fii_buy: number;
  fii_sell: number;
  fii_net: number;
  dii_buy: number;
  dii_sell: number;
  dii_net: number;
}

export interface FiiDiiResponse {
  /** nse / nsepython / moneycontrol / trendlyne / static */
  source: string;
  rows: FiiDiiRow[];
}

export interface AdvDecResponse {
  advances: number;
  declines: number;
  unchanged: number;
  source: string;
}

export interface OptionChainRow {
  strike: number;
  ce_oi: number;
  ce_chg_oi: number;
  ce_ltp: number;
  pe_oi: number;
  pe_chg_oi: number;
  pe_ltp: number;
}

export interface OptionChainResponse {
  symbol: string;
  source: string;
  underlying_value: number;
  expiries: string[];
  pcr: number | null;
  max_pain: number | null;
  rows: OptionChainRow[];
}

export async function getNseQuote(symbol: string): Promise<NseQuote> {
  return api.get<NseQuote>(
    `/nse/quote/${encodeURIComponent(symbol)}`,
  );
}

export async function getFiiDii(): Promise<FiiDiiResponse> {
  return api.get<FiiDiiResponse>("/nse/fii-dii");
}

export async function getAdvancesDeclines(): Promise<AdvDecResponse> {
  return api.get<AdvDecResponse>("/nse/advances-declines");
}

export async function getOptionChain(
  symbol: string,
): Promise<OptionChainResponse> {
  return api.get<OptionChainResponse>(
    `/nse/option-chain/${encodeURIComponent(symbol)}`,
  );
}

// Re-exported so the markets page can reuse the same interval types.
export type { Interval, Period };
