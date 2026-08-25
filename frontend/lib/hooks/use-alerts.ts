"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createAlert, deleteAlert, getAlerts, clearAlerts } from "@/lib/api/alerts";

export function useAlerts() {
  return useQuery({
    queryKey: ["alerts"],
    queryFn: getAlerts,
    refetchInterval: 30_000,
  });
}

export function useCreateAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createAlert,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useDeleteAlert() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteAlert,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}

export function useClearAlerts() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (firedOnly: boolean) => clearAlerts(firedOnly),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
  });
}
