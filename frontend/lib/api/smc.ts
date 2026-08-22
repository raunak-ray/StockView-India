import { api } from "./client";
import type { Interval, Period } from "./market";

/** Smart-money-concept structures returned by GET /api/v1/smc. */

export interface SwingPoint {
  time: string;
  value: number;
}

export interface MSSignal {
  time: string;
  price: number;
  /** BOS / CHoCH / CHoCH+ */
  label: string;
  bull: boolean;
}

export interface SmcBox {
  /** Bar where the zone originates; extends right on the chart. */
  time: string;
  top: number;
  btm: number;
  mitigated: boolean;
}

export interface FVGBox extends SmcBox {
  bull: boolean;
}

export interface SmcResponse {
  symbol: string;
  interval: Interval;
  period: Period;
  swing_highs: SwingPoint[];
  swing_lows: SwingPoint[];
  ms_signals: MSSignal[];
  bull_obs: SmcBox[];
  bear_obs: SmcBox[];
  fvgs: FVGBox[];
  range_high: number | null;
  range_low: number | null;
  equilibrium: number | null;
  itrend: number;
  strend: number;
}

export async function getSmc(
  symbol: string,
  interval: Interval = "1d",
  period: Period = "2y",
): Promise<SmcResponse> {
  const params = new URLSearchParams({ symbol, interval, period });
  return api.get<SmcResponse>(`/smc?${params}`);
}
