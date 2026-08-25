import { api } from "./client";

// ── Backtesting ────────────────────────────────────────────────────────────

export interface BacktestStrategy {
  name: string;
  description: string;
}

export interface BacktestTrade {
  entry_date: string;
  exit_date: string;
  entry_px: number;
  exit_px: number;
  shares: number;
  pnl: number;
  pnl_pct: number;
  hold_days: number;
  exit_reason: string;
  win: boolean;
}

export interface MonthlyReturn {
  month: string;
  return_pct: number;
}

export interface BacktestResult {
  symbol: string;
  strategy: string;
  final_equity: number;
  total_ret_pct: number;
  cagr: number;
  sharpe: number;
  sortino: number;
  calmar: number;
  max_dd: number;
  dd_dur_days: number;
  total_trades: number;
  wins: number;
  losses: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number | null;
  expectancy: number;
  expectancy_pct: number;
  avg_hold: number;
  years: number;
  bh_ret: number;
  bh_cagr: number;
  alpha: number;
  initial_capital: number;
  equity_curve: { date: string; equity: number }[];
  trades: BacktestTrade[];
  monthly_returns: MonthlyReturn[];
}

export interface BacktestRequest {
  symbol: string;
  strategy: string;
  years: number;
  initial_capital: number;
  commission_pct: number;
  sl_pct: number;
  tp_pct: number;
  position_size_pct: number;
}

export async function getStrategies(): Promise<{ strategies: BacktestStrategy[] }> {
  return api.get<{ strategies: BacktestStrategy[] }>("/backtesting/strategies");
}

export async function runBacktest(req: BacktestRequest): Promise<BacktestResult> {
  return api.post<BacktestResult>("/backtesting/run", req);
}
