"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import {
  getPaperSummary,
  getPaperPositions,
  getPaperOrders,
  placePaperOrder,
  resetPaperPortfolio,
} from "@/lib/api/portfolio";

const PAPER_KEYS = {
  summary: ["portfolio", "paper", "summary"] as const,
  positions: ["portfolio", "paper", "positions"] as const,
  orders: ["portfolio", "paper", "orders"] as const,
};

export function usePaperSummary() {
  return useQuery({
    queryKey: PAPER_KEYS.summary,
    queryFn: getPaperSummary,
    staleTime: 0,
  });
}

export function usePaperPositions() {
  return useQuery({
    queryKey: PAPER_KEYS.positions,
    queryFn: getPaperPositions,
    staleTime: 0,
  });
}

export function usePaperOrders() {
  return useQuery({
    queryKey: PAPER_KEYS.orders,
    queryFn: getPaperOrders,
    staleTime: 0,
  });
}

export function usePlacePaperOrder() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      symbol,
      side,
      qty,
      price,
    }: {
      symbol: string;
      side: "BUY" | "SELL";
      qty: number;
      price: number;
    }) => placePaperOrder(symbol, side, qty, price),
    onSuccess: (order) => {
      toast.success(`${order.type} ${order.qty}× ${order.symbol} @ ₹${order.price.toLocaleString("en-IN")}`);
      qc.invalidateQueries({ queryKey: PAPER_KEYS.summary });
      qc.invalidateQueries({ queryKey: PAPER_KEYS.positions });
      qc.invalidateQueries({ queryKey: PAPER_KEYS.orders });
    },
    onError: (e) =>
      toast.error(e instanceof Error ? e.message : "Order failed"),
  });
}

export function useResetPaper() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: resetPaperPortfolio,
    onSuccess: () => {
      toast.success("Portfolio reset to ₹1,00,000");
      qc.invalidateQueries({ queryKey: PAPER_KEYS.summary });
      qc.invalidateQueries({ queryKey: PAPER_KEYS.positions });
      qc.invalidateQueries({ queryKey: PAPER_KEYS.orders });
    },
  });
}
