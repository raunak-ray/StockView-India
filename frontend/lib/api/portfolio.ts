import { api } from "./client";

// ── Watchlist ──────────────────────────────────────────────────────────────

export interface WatchlistItem {
  ticker: string;
  sort_order: number;
  created_at: string;
}

export interface WatchlistResponse {
  count: number;
  items: WatchlistItem[];
}

interface MessageResponse {
  message: string;
}

export async function getWatchlist(): Promise<WatchlistResponse> {
  return api.get<WatchlistResponse>("/portfolio/watchlist");
}

export async function addToWatchlist(ticker: string): Promise<MessageResponse> {
  return api.post<MessageResponse>("/portfolio/watchlist", { ticker });
}

export async function removeFromWatchlist(ticker: string): Promise<MessageResponse> {
  const encoded = encodeURIComponent(ticker);
  return api.del<MessageResponse>(`/portfolio/watchlist/${encoded}`);
}

// ── Paper trading ──────────────────────────────────────────────────────────

export interface PaperSummary {
  cash: number;
  positions_count: number;
  orders_count: number;
  pnl: number;
  initial_cash: number;
}

export interface PaperOrder {
  id: string;
  ts: string;
  symbol: string;
  type: string;
  qty: number;
  price: number;
  value: number;
  mode: string;
}

export interface PaperPosition {
  symbol: string;
  qty: number;
  avg_cost: number;
  ltp: number;
  unrealised_pnl: number;
  pnl_pct: number;
}

export async function getPaperSummary(): Promise<PaperSummary> {
  return api.get<PaperSummary>("/portfolio/paper");
}

export async function placePaperOrder(
  symbol: string,
  side: "BUY" | "SELL",
  qty: number,
  price: number,
): Promise<PaperOrder> {
  return api.post<PaperOrder>("/portfolio/paper/order", { symbol, side, qty, price });
}

export async function getPaperPositions(): Promise<PaperPosition[]> {
  return api.get<PaperPosition[]>("/portfolio/paper/positions");
}

export async function getPaperOrders(): Promise<PaperOrder[]> {
  return api.get<PaperOrder[]>("/portfolio/paper/orders");
}

export async function resetPaperPortfolio(): Promise<PaperSummary> {
  return api.post<PaperSummary>("/portfolio/paper/reset");
}
