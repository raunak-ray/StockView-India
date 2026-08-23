"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ChevronRight, Search } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Loader } from "@/components/motion/loader";
import { InfoTip } from "@/components/info-tip";
import { SectorTreemap } from "./components/sector-treemap";
import { useDebouncedValue } from "@/lib/hooks/use-debounce";
import { useSectorPerformance } from "@/lib/hooks/use-nse";
import type { SectorStock } from "@/lib/api/market";
import { formatPct, toneBadgeClass } from "@/lib/utils/format";
import { cn } from "@/lib/utils";

const SEARCH_MS = 300;
const STOCKS_PER_PAGE = 6;

/** Horizontal performance bars — one per sector, signed colours. */
function PerformanceBars({
  sectors,
  selected,
  onSelect,
}: {
  sectors: { name: string; change_pct: number | null }[];
  selected: string | null;
  onSelect: (name: string) => void;
}) {
  const maxAbs = Math.max(
    ...sectors.map((s) => Math.abs(s.change_pct ?? 0)),
    0.01,
  );
  return (
    <Card className="h-fit">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-1.5 text-sm">
          Performance today
          <InfoTip label="What am I looking at?">
            Each bar is one sector&apos;s average % move today, pointing right
            for gains and left for losses. Click to select a sector.
          </InfoTip>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-1">
        {[...sectors]
          .sort((a, b) => (b.change_pct ?? 0) - (a.change_pct ?? 0))
          .map((s) => {
            const pct = s.change_pct ?? 0;
            const width = (Math.abs(pct) / maxAbs) * 50; // half-width each side
            const up = pct >= 0;
            return (
              <button
                key={s.name}
                type="button"
                onClick={() => onSelect(s.name)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-2 py-1.5 text-left transition-colors hover:bg-muted",
                  selected === s.name && "bg-muted",
                )}
              >
                <span className="w-28 shrink-0 truncate text-xs">{s.name}</span>
                <span className="relative flex h-4 flex-1 items-center">
                  <span
                    aria-hidden
                    className="absolute left-1/2 h-full w-px bg-border"
                  />
                  <span
                    className={cn(
                      "absolute h-2 rounded-sm transition-all duration-300",
                      up ? "left-1/2 bg-up" : "right-1/2 bg-down",
                    )}
                    style={{ width: `${width}%` }}
                  />
                </span>
                <span
                  className={cn(
                    "w-16 shrink-0 text-right font-mono text-xs font-semibold",
                    up ? "text-up" : "text-down",
                  )}
                >
                  {formatPct(pct)}
                </span>
              </button>
            );
          })}
      </CardContent>
    </Card>
  );
}

/** Stocks of the selected sector as paged cards, each linking to its page. */
function StockCards({
  sectorName,
  stocks,
}: {
  sectorName: string;
  stocks: SectorStock[];
}) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const debounced = useDebouncedValue(query.trim().toLowerCase(), SEARCH_MS);

  const filtered = useMemo(
    () =>
      stocks.filter(
        (s) =>
          !debounced ||
          s.label.toLowerCase().includes(debounced) ||
          s.ticker.toLowerCase().includes(debounced),
      ),
    [stocks, debounced],
  );

  const pageCount = Math.max(1, Math.ceil(filtered.length / STOCKS_PER_PAGE));
  const safePage = Math.min(page, pageCount - 1);
  const pageStocks = filtered.slice(
    safePage * STOCKS_PER_PAGE,
    (safePage + 1) * STOCKS_PER_PAGE,
  );

  return (
    <Card className="h-fit">
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 space-y-0 pb-3">
        <CardTitle className="text-sm">
          {sectorName}
          <span className="ml-2 font-mono text-xs font-normal text-muted-foreground">
            {filtered.length} stocks
          </span>
        </CardTitle>
        <div className="relative w-52">
          <Search className="absolute top-1/2 left-3 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setPage(0);
            }}
            placeholder="Filter stocks…"
            className="h-8 pl-9 font-mono text-xs"
            aria-label="Filter sector stocks"
          />
        </div>
      </CardHeader>
      <CardContent className="p-0">
        {filtered.length === 0 ? (
          <p className="py-10 text-center text-sm text-muted-foreground">
            No stocks match “{query}”.
          </p>
        ) : (
          <>
            <div className="grid gap-3 p-4 pt-1 sm:grid-cols-2">
              {pageStocks.map((s) => {
                const up = (s.change_pct ?? 0) >= 0;
                return (
                  <Link
                    key={s.ticker}
                    href={`/app/stocks/${encodeURIComponent(s.ticker)}`}
                    className="group flex items-center justify-between gap-3 rounded-xl border border-border bg-card px-4 py-3 transition-colors hover:border-primary/40"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium">{s.label}</p>
                      <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                        {s.ticker.replace(".NS", "")} · ₹
                        {s.mcap.toLocaleString("en-IN")} Cr cap
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <span
                        className={cn(
                          "rounded-full border px-2 py-0.5 font-mono text-[11px] font-semibold",
                          toneBadgeClass[up ? "up" : "down"],
                        )}
                      >
                        {formatPct(s.change_pct)}
                      </span>
                      <ChevronRight className="size-4 text-muted-foreground/50 transition-transform group-hover:translate-x-0.5 group-hover:text-foreground" />
                    </div>
                  </Link>
                );
              })}
            </div>
            {pageCount > 1 ? (
              <div className="flex items-center justify-between border-t border-border px-4 py-3">
                <span className="font-mono text-xs text-muted-foreground">
                  Page {safePage + 1} of {pageCount}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    aria-label="Previous page"
                    disabled={safePage === 0}
                    onClick={() => setPage((p) => Math.max(0, p - 1))}
                    className="text-xs text-primary underline-offset-4 transition-colors hover:underline disabled:pointer-events-none disabled:opacity-40 disabled:no-underline"
                  >
                    Prev
                  </button>
                  <button
                    type="button"
                    aria-label="Next page"
                    disabled={safePage >= pageCount - 1}
                    onClick={() =>
                      setPage((p) => Math.min(pageCount - 1, p + 1))
                    }
                    className="text-xs text-primary underline-offset-4 transition-colors hover:underline disabled:pointer-events-none disabled:opacity-40 disabled:no-underline"
                  >
                    Next
                  </button>
                </div>
              </div>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}

export default function SectorsPage() {
  const { data, isLoading, isError, refetch } = useSectorPerformance();
  const [selected, setSelected] = useState<string | null>(null);

  const sectors = data?.sectors ?? [];
  const active =
    selected && sectors.some((s) => s.name === selected)
      ? selected
      : (sectors[0]?.name ?? null);
  const activeSector = sectors.find((s) => s.name === active);

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Sectors — NIFTY 50</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Today&apos;s sector moves at a glance. Click any block or bar to see
          its stocks.
        </p>
      </div>

      {isLoading ? (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border py-24 text-muted-foreground">
          <Loader variant="dots" size={28} label="Loading sector data" />
          <p className="text-sm">Loading sector data…</p>
        </div>
      ) : isError ? (
        <div className="rounded-xl border border-dashed border-border py-16 text-center">
          <p className="text-sm font-medium">Sector data unavailable right now</p>
          <button
            type="button"
            onClick={() => refetch()}
            className="mt-2 text-sm text-primary underline-offset-4 hover:underline"
          >
            Retry
          </button>
        </div>
      ) : (
        <>
          <SectorTreemap
            sectors={sectors}
            selected={active}
            onSelect={setSelected}
          />
          <div className="grid gap-4 lg:grid-cols-5">
            <div className="lg:col-span-2">
              <PerformanceBars
                sectors={sectors}
                selected={active}
                onSelect={setSelected}
              />
            </div>
            <div className="lg:col-span-3">
              {activeSector ? (
                <StockCards
                  sectorName={activeSector.name}
                  stocks={activeSector.stocks}
                />
              ) : null}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
