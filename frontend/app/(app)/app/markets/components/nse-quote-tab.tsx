"use client";

import { useState } from "react";
import { Search, TrendingUp } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useInstrumentSearch,
  type Instrument,
} from "@/lib/hooks/use-instruments";
import { useDebouncedValue } from "@/lib/hooks/use-debounce";
import { useNseQuote } from "@/lib/hooks/use-nse";
import type { NseQuote } from "@/lib/api/nse";
import { SEARCH_DEBOUNCE_MS } from "../constants";
import {
  formatCompact,
  formatINR,
  formatNumber,
  formatPct,
  toneBadgeClass,
} from "@/lib/utils/format";
import { cn } from "@/lib/utils";

function QuoteCard({ quote }: { quote: NseQuote }) {
  const up = quote.change_pct >= 0;
  return (
    <Card>
      <CardContent className="space-y-4 p-5">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-sm font-semibold">{quote.company_name}</p>
            <p className="mt-0.5 font-mono text-xs text-muted-foreground">
              {quote.symbol} · NSE
              <span className="mx-1.5 text-border">|</span>
              {quote.trading_status}
            </p>
          </div>
          <div className="flex items-baseline gap-3">
            <span
              className={cn(
                "font-mono text-2xl font-semibold",
                up ? "text-up" : "text-down",
              )}
            >
              ₹{formatNumber(quote.last_price)}
            </span>
            <span
              className={cn(
                "inline-flex items-center gap-0.5 rounded-full border px-2 py-0.5 font-mono text-xs font-semibold",
                toneBadgeClass[up ? "up" : "down"],
              )}
            >
              {formatPct(quote.change_pct)}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {[
            ["Open", formatINR(quote.open)],
            ["Prev close", formatINR(quote.prev_close)],
            ["Day high", formatINR(quote.day_high)],
            ["Day low", formatINR(quote.day_low)],
            ["52W high", formatINR(quote.week_high)],
            ["52W low", formatINR(quote.week_low)],
            ["Volume", formatCompact(quote.volume)],
            ["VWAP", formatINR(quote.vwap)],
          ].map(([label, value]) => (
            <div
              key={label}
              className="flex items-center justify-between rounded-lg bg-muted/60 px-3 py-2"
            >
              <span className="text-xs text-muted-foreground">{label}</span>
              <span className="font-mono text-sm font-medium">{value}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/** NSE Quote tab — debounced instrument search feeding a live quote card. */
export function NseQuoteTab() {
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<Instrument | null>(null);
  const debounced = useDebouncedValue(query, SEARCH_DEBOUNCE_MS);
  const { data } = useInstrumentSearch(debounced, 8);
  const results = data?.results ?? [];
  const quote = useNseQuote(selected?.ticker ?? null);

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search an NSE stock… e.g. RELIANCE"
          className="pl-9"
          aria-label="Search NSE stock for quote"
        />
      </div>

      {/* Results */}
      {debounced && results.length > 0 && (
        <Card>
          <CardContent className="max-h-64 divide-y divide-border overflow-y-auto p-1">
            {results.map((r) => (
              <button
                key={r.ticker}
                type="button"
                onClick={() => {
                  setSelected(r);
                  setQuery("");
                }}
                className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-muted"
              >
                <span className="flex items-center gap-2 truncate">
                  <TrendingUp className="size-3.5 text-muted-foreground" />
                  {r.name}
                </span>
                <span className="font-mono text-xs text-muted-foreground">
                  {r.ticker}
                </span>
              </button>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Quote card */}
      {!selected && !debounced && (
        <div className="rounded-xl border border-dashed border-border py-16 text-center">
          <p className="text-sm font-medium">Search to see a live NSE quote</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Direct NSE feed with automatic fallbacks.
          </p>
        </div>
      )}
      {quote.isLoading && selected && (
        <Skeleton className="h-56 w-full rounded-xl" />
      )}
      {selected && quote.data && <QuoteCard quote={quote.data} />}
    </div>
  );
}
