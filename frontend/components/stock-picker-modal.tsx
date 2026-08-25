"use client";

import { useState, useMemo, useEffect } from "react";
import { Search, TrendingUp } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { useInstrumentSearch } from "@/lib/hooks/use-instruments";

const POPULAR = [
  { ticker: "RELIANCE.NS", name: "Reliance Industries" },
  { ticker: "TCS.NS", name: "Tata Consultancy Services" },
  { ticker: "HDFCBANK.NS", name: "HDFC Bank" },
  { ticker: "INFY.NS", name: "Infosys" },
  { ticker: "ICICIBANK.NS", name: "ICICI Bank" },
  { ticker: "SBIN.NS", name: "State Bank of India" },
  { ticker: "BHARTIARTL.NS", name: "Bharti Airtel" },
  { ticker: "ITC.NS", name: "ITC" },
  { ticker: "KOTAKBANK.NS", name: "Kotak Mahindra Bank" },
  { ticker: "LT.NS", name: "Larsen & Toubro" },
  { ticker: "AXISBANK.NS", name: "Axis Bank" },
  { ticker: "BAJFINANCE.NS", name: "Bajaj Finance" },
  { ticker: "MARUTI.NS", name: "Maruti Suzuki" },
  { ticker: "SUNPHARMA.NS", name: "Sun Pharma" },
  { ticker: "TATAMOTORS.NS", name: "Tata Motors" },
  { ticker: "WIPRO.NS", name: "Wipro" },
  { ticker: "HCLTECH.NS", name: "HCL Technologies" },
  { ticker: "TITAN.NS", name: "Titan Company" },
  { ticker: "ASIANPAINT.NS", name: "Asian Paints" },
  { ticker: "HINDUNILVR.NS", name: "Hindustan Unilever" },
];

interface StockPickerModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (ticker: string, name: string) => void;
  exclude?: string[];
}

export function StockPickerModal({
  open,
  onOpenChange,
  onSelect,
  exclude = [],
}: StockPickerModalProps) {
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query), 200);
    return () => clearTimeout(t);
  }, [query]);

  const { data, isFetching } = useInstrumentSearch(debounced);
  const results = useMemo(() => data?.results ?? [], [data]);

  const filtered = POPULAR.filter((s) => !exclude.includes(s.ticker));

  const handleSelect = (ticker: string, name: string) => {
    onSelect(ticker, name);
    onOpenChange(false);
    setQuery("");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg gap-0 p-0">
        <DialogHeader className="border-b border-border px-6 py-4">
          <DialogTitle className="text-base">Select a stock</DialogTitle>
        </DialogHeader>

        {/* Search */}
        <div className="border-b border-border px-6 py-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search by name or ticker…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-9 font-mono text-sm"
              autoFocus
            />
          </div>
        </div>

        {/* Results */}
        <div className="max-h-[400px] overflow-y-auto px-6 py-4">
          {debounced ? (
            <>
              {isFetching && (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  Searching…
                </p>
              )}
              {!isFetching && results.length === 0 && (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  No match for &ldquo;{debounced}&rdquo;.
                </p>
              )}
              {results.length > 0 && (
                <div className="space-y-1">
                  {results
                    .filter((r) => !exclude.includes(r.ticker))
                    .map((r) => (
                      <button
                        key={r.ticker}
                        onClick={() => handleSelect(r.ticker, r.name)}
                        className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-muted"
                      >
                        <TrendingUp className="size-4 shrink-0 text-muted-foreground" />
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-sm font-medium">
                            {r.name}
                          </div>
                          <div className="font-mono text-xs text-muted-foreground">
                            {r.ticker}
                          </div>
                        </div>
                      </button>
                    ))}
                </div>
              )}
            </>
          ) : (
            <div className="space-y-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Popular stocks
              </p>
              <div className="grid grid-cols-1 gap-1 sm:grid-cols-2">
                {filtered.map((s) => (
                  <button
                    key={s.ticker}
                    onClick={() => handleSelect(s.ticker, s.name)}
                    className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-left transition-colors hover:bg-muted"
                  >
                    <TrendingUp className="size-3.5 shrink-0 text-emerald-500" />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-sm">{s.name}</div>
                      <div className="font-mono text-[10px] text-muted-foreground">
                        {s.ticker}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
