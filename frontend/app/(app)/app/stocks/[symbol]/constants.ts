import type { Interval, Period } from "@/lib/api/market";

/** Live-quote auto-refresh options — parity with the Streamlit
 *  select_slider (app.py:1022): [5, 10, 15, 30, 60] seconds. */
export const REFRESH_INTERVALS = [5, 10, 15, 30, 60] as const;

export type RefreshInterval = (typeof REFRESH_INTERVALS)[number];

export const DEFAULT_REFRESH_INTERVAL: RefreshInterval = 10;

/** Chart timeframe presets — parity with TF_MAP (app.py:980-984). */
export interface Timeframe {
  label: "1D" | "1W" | "1M";
  interval: Interval;
  period: Period;
}

export const TIMEFRAMES: Timeframe[] = [
  { label: "1D", interval: "1d", period: "2y" },
  { label: "1W", interval: "1wk", period: "5y" },
  { label: "1M", interval: "1mo", period: "10y" },
];

export const DEFAULT_TIMEFRAME = TIMEFRAMES[0];
