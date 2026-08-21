"use client";

import { useEffect } from "react";

/** Keeps the browser tab title in sync with the viewed symbol. */
export function useDocumentTitle(title: string) {
  useEffect(() => {
    document.title = `${title} — StockView India`;
  }, [title]);
}
