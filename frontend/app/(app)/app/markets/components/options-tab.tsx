"use client";

import { useMemo, useState } from "react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Loader } from "@/components/motion/loader";
import { InfoTip } from "@/components/info-tip";
import { useDebouncedValue } from "@/lib/hooks/use-debounce";
import { useOptionChain } from "@/lib/hooks/use-nse";
import { formatCompact, formatNumber } from "@/lib/utils/format";
import { cn } from "@/lib/utils";

import {
  CHAIN_PAGE_SIZE,
  DEFAULT_OPTION_SYMBOL,
  OPTION_INDICES,
  SEARCH_DEBOUNCE_MS,
} from "../constants";
import { Pager } from "./pager";

function ToggleChip({
  active,
  onClick,
  children,
  label,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      onClick={onClick}
      className={cn(
        "rounded-md px-2.5 py-1 font-mono text-xs transition-colors",
        active
          ? "bg-secondary text-secondary-foreground"
          : "text-muted-foreground hover:text-foreground",
      )}
    >
      {children}
    </button>
  );
}

function HeadCell({
  children,
  tip,
  align = "right",
}: {
  children: React.ReactNode;
  tip: string;
  align?: "left" | "right";
}) {
  return (
    <th
      className={cn(
        "px-4 py-2 font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground",
        align === "right" ? "text-right" : "text-left",
      )}
    >
      <span className={cn("inline-flex items-center gap-1", align === "right" && "flex-row-reverse")}>
        {children}
        <InfoTip label={`What is ${children}?`}>{tip}</InfoTip>
      </span>
    </th>
  );
}

/** Options/PCR tab — index picker, ATM window, strike filter and pagination. */
export function OptionsTab() {
  const [symbol, setSymbol] = useState<string>(DEFAULT_OPTION_SYMBOL);
  const [customSymbol, setCustomSymbol] = useState("");
  const debouncedCustom = useDebouncedValue(customSymbol.trim().toUpperCase(), SEARCH_DEBOUNCE_MS);
  const effectiveCustom = debouncedCustom.length >= 2 ? debouncedCustom : "";

  // Custom equity symbol wins over the index chips once entered.
  const chainSymbol = effectiveCustom || symbol;

  const [nearAtm, setNearAtm] = useState(true);
  const [strikeQuery, setStrikeQuery] = useState("");
  const debouncedStrike = useDebouncedValue(strikeQuery.trim(), SEARCH_DEBOUNCE_MS);
  const [page, setPage] = useState(0);

  const { data, isLoading, isError } = useOptionChain(chainSymbol);
  const rows = useMemo(() => data?.rows ?? [], [data]);
  const spot = data?.underlying_value ?? 0;

  const visibleRows = useMemo(() => {
    let list = [...rows];
    if (debouncedStrike) {
      list = list.filter((r) => String(r.strike).includes(debouncedStrike));
    }
    if (nearAtm && spot > 0) {
      list.sort((a, b) => Math.abs(a.strike - spot) - Math.abs(b.strike - spot));
      list = list.slice(0, 21); // ~10 strikes each side of spot
    }
    return list;
  }, [rows, debouncedStrike, nearAtm, spot]);

  const pageCount = Math.max(1, Math.ceil(visibleRows.length / CHAIN_PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const pageRows = visibleRows.slice(
    safePage * CHAIN_PAGE_SIZE,
    (safePage + 1) * CHAIN_PAGE_SIZE,
  );

  if (isLoading) {
    return (
      <div className="flex flex-col items-center gap-3 py-20 text-muted-foreground">
        <Loader variant="dots" size={28} label="Loading option chain" />
        <p className="text-sm">Loading option chain…</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Symbol picker: index chips + optional custom equity */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1 rounded-lg border border-border bg-card p-1">
          {OPTION_INDICES.map((idx) => (
            <ToggleChip
              key={idx}
              label={`Show ${idx} option chain`}
              active={!effectiveCustom && symbol === idx}
              onClick={() => {
                setSymbol(idx);
                setCustomSymbol("");
                setPage(0);
              }}
            >
              {idx}
            </ToggleChip>
          ))}
        </div>
        <Input
          value={customSymbol}
          onChange={(e) => {
            setCustomSymbol(e.target.value.toUpperCase());
            setPage(0);
          }}
          placeholder="Or equity symbol…"
          className="h-9 w-44 font-mono text-xs"
          aria-label="Custom option chain symbol"
        />
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-4">
        {[
          {
            label: "Spot",
            value: spot > 0 ? formatNumber(spot) : "—",
            tip: "The current price of the index or stock that the options are written on.",
          },
          {
            label: "PCR (OI)",
            value: data?.pcr != null ? data.pcr.toFixed(3) : "—",
            tip: "Put-Call ratio: total puts divided by total calls. Above 1 = more downside bets (fear); below 1 = more upside bets (greed).",
          },
          {
            label: "Max pain",
            value: data?.max_pain != null ? formatNumber(data.max_pain) : "—",
            tip: "The price where the most option buyers lose money — the level option writers profit most at. Price often drifts toward it near expiry.",
          },
        ].map(({ label, value, tip }) => (
          <Card key={label}>
            <CardContent className="p-4 text-center">
              <p className="flex items-center justify-center gap-1 font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
                {label}
                <InfoTip label={`What is ${label}?`}>{tip}</InfoTip>
              </p>
              <p className="mt-1 font-mono text-lg font-semibold">{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Chain table */}
      <Card>
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3 space-y-0 pb-3">
          <CardTitle className="text-sm">
            Option chain — {chainSymbol}
            <span className="ml-2 font-mono text-xs font-normal text-muted-foreground">
              {visibleRows.length} strikes
            </span>
          </CardTitle>
          <div className="flex flex-wrap items-center gap-2">
            <Input
              value={strikeQuery}
              onChange={(e) => {
                setStrikeQuery(e.target.value);
                setPage(0);
              }}
              placeholder="Filter strike…"
              className="h-8 w-32 font-mono text-xs"
              aria-label="Filter strikes"
            />
            <span className="flex items-center gap-1.5">
              <ToggleChip
                label="Show only strikes near the money"
                active={nearAtm}
                onClick={() => {
                  setNearAtm((v) => !v);
                  setPage(0);
                }}
              >
                Near ATM
              </ToggleChip>
              <InfoTip label="What is Near ATM?">
                Only show strikes closest to the current price (about 10 on
                each side) — where most trading happens. ATM = at the money.
              </InfoTip>
            </span>
          </div>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          {isError || rows.length === 0 ? (
            <div className="py-14 text-center text-sm text-muted-foreground">
              Option chain unavailable for this symbol.
            </div>
          ) : (
            <>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50">
                    <HeadCell tip="The price level at which the option can be exercised.">
                      Strike
                    </HeadCell>
                    <HeadCell tip="CE = call option (a bet the price rises). OI = open interest, contracts still open.">
                      CE OI
                    </HeadCell>
                    <HeadCell tip="Change in open interest today — builds show new positions, unwinds show exits.">
                      CE ΔOI
                    </HeadCell>
                    <HeadCell tip="Last traded price of this call, in ₹.">
                      CE LTP
                    </HeadCell>
                    <HeadCell tip="Last traded price of this put, in ₹.">
                      PE LTP
                    </HeadCell>
                    <HeadCell tip="Change in open interest today for this put.">
                      PE ΔOI
                    </HeadCell>
                    <HeadCell tip="PE = put option (a bet the price falls). OI = open interest, contracts still open.">
                      PE OI
                    </HeadCell>
                  </tr>
                </thead>
                <tbody>
                  {pageRows.map((r) => (
                    <tr
                      key={r.strike}
                      className={cn(
                        "border-b border-border/50 transition-colors hover:bg-muted/40",
                        spot > 0 &&
                          Math.abs(r.strike - spot) ===
                            Math.min(...visibleRows.map((x) => Math.abs(x.strike - spot))) &&
                          "bg-primary/5",
                      )}
                    >
                      <td className="px-4 py-2 text-left font-mono text-xs font-semibold">
                        {formatNumber(r.strike, 0)}
                      </td>
                      <td className="px-4 py-2 text-right font-mono text-xs">{formatCompact(r.ce_oi)}</td>
                      <td className="px-4 py-2 text-right font-mono text-xs">{formatCompact(r.ce_chg_oi)}</td>
                      <td className="px-4 py-2 text-right font-mono text-xs">{formatCompact(r.ce_ltp)}</td>
                      <td className="px-4 py-2 text-right font-mono text-xs">{formatCompact(r.pe_ltp)}</td>
                      <td className="px-4 py-2 text-right font-mono text-xs">{formatCompact(r.pe_chg_oi)}</td>
                      <td className="px-4 py-2 text-right font-mono text-xs">{formatCompact(r.pe_oi)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="border-t border-border">
                <Pager
                  page={safePage}
                  pageCount={pageCount}
                  onPage={setPage}
                  hint={`${visibleRows.length} strikes`}
                />
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
