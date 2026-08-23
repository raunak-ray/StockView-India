"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { SectorTreemap } from "./components/sector-treemap";
import { useDebouncedValue } from "@/lib/hooks/use-debounce";
import { useSectorPerformance } from "@/lib/hooks/use-nse";
import type { SectorStock } from "@/lib/api/market";
import { formatPct, toneBadgeClass } from "@/lib/utils/format";
import { cn } from "@/lib/utils";

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
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Sector performance today</CardTitle>
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
                  "flex w-full items-center gap-3 rounded-lg px-2 py-1 text-left transition-colors hover:bg-muted",
                  selected === s.name && "bg-muted",
                )}
              >
                <span className="w-32 shrink-0 truncate text-xs">{s.name}</span>
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

/** Constituents of the selected sector with debounced search filter. */
function StockTable({ stocks }: { stocks: SectorStock[] }) {
  const [query, setQuery] = useState("");
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

  if (stocks.length === 0) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 space-y-0 pb-3">
        <CardTitle className="text-sm">Constituents</CardTitle>
        <div className="relative w-52">
          <Search className="absolute top-1/2 left-3 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter stocks…"
            className="h-8 pl-9 font-mono text-xs"
            aria-label="Filter sector constituents"
          />
        </div>
      </CardHeader>
      <CardContent className="overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border bg-muted/50 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
              <th className="px-4 py-2 text-left">Stock</th>
              <th className="px-4 py-2 text-left">Ticker</th>
              <th className="px-4 py-2 text-right">M-cap (₹ Cr)</th>
              <th className="px-4 py-2 text-right">Change</th>
              <th className="px-4 py-2 text-right" />
            </tr>
          </thead>
          <tbody>
            {filtered.map((s) => (
              <tr
                key={s.ticker}
                className="border-b border-border/50 transition-colors hover:bg-muted/40"
              >
                <td className="px-4 py-2">{s.label}</td>
                <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                  {s.ticker.replace(".NS", "")}
                </td>
                <td className="px-4 py-2 text-right font-mono text-xs">
                  {s.mcap.toLocaleString("en-IN")}
                </td>
                <td className="px-4 py-2 text-right">
                  <span
                    className={cn(
                      "inline-flex rounded-full border px-2 py-0.5 font-mono text-[11px] font-semibold",
                      toneBadgeClass[(s.change_pct ?? 0) >= 0 ? "up" : "down"],
                    )}
                  >
                    {formatPct(s.change_pct)}
                  </span>
                </td>
                <td className="px-4 py-2 text-right">
                  <Link
                    href={`/app/stocks/${encodeURIComponent(s.ticker)}`}
                    className="font-mono text-xs text-primary underline-offset-4 hover:underline"
                  >
                    Open →
                  </Link>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="py-8 text-center text-sm text-muted-foreground">
                  No constituents match “{debounced}”.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}

const SEARCH_MS = 300;

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
          Market-cap weighted view of today&apos;s sector moves.
        </p>
      </div>

      {isLoading ? (
        <Skeleton className="h-80 w-full rounded-xl" />
      ) : isError ? (
        <div className="rounded-xl border border-dashed border-border py-16 text-center">
          <p className="text-sm font-medium">Sector feed unavailable right now</p>
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
            onSelect={(name) =>
              setSelected((cur) => (cur === name ? null : name))
            }
          />
          <PerformanceBars
            sectors={sectors}
            selected={active}
            onSelect={setActiveName(setSelected)}
          />
          {activeSector && <StockTable stocks={activeSector.stocks} />}
        </>
      )}
    </div>
  );
}

// Small helper keeps the bars' select behaviour explicit.
function setActiveName(
  setSelected: React.Dispatch<React.SetStateAction<string | null>>,
) {
  return (name: string) => setSelected(name);
}
