"use client";

import { useState } from "react";
import { Building2, Globe2 } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Loader } from "@/components/motion/loader";
import { InfoTip } from "@/components/info-tip";
import { Sparkline } from "@/components/charts/sparkline";
import { useFiiDii } from "@/lib/hooks/use-nse";
import type { FiiDiiRow } from "@/lib/api/nse";
import { formatSigned } from "@/lib/utils/format";
import { cn } from "@/lib/utils";

import { SESSIONS_PAGE_SIZE } from "../constants";
import { Pager } from "./pager";

function FlowSide({
  who,
  net,
  buy,
  sell,
}: {
  who: "FII" | "DII";
  net: number;
  buy: number;
  sell: number;
}) {
  const up = net >= 0;
  return (
    <div className="space-y-1">
      <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        {who}
        <span
          className={cn(
            "font-mono text-sm font-semibold",
            up ? "text-up" : "text-down",
          )}
        >
          {formatSigned(net)}
        </span>
      </p>
      <p className="font-mono text-[11px] text-muted-foreground/80">
        buy {formatSigned(buy, 0)} · sell {formatSigned(sell, 0)}
      </p>
    </div>
  );
}

function SessionCard({ row, latest }: { row: FiiDiiRow; latest: boolean }) {
  return (
    <Card className="transition-colors hover:border-primary/30">
      <CardContent className="space-y-3 p-4">
        <div className="flex items-center justify-between">
          <p className="font-mono text-xs text-muted-foreground">{row.date}</p>
          {latest ? (
            <span className="rounded-full border border-primary/30 bg-primary/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-primary">
              Latest
            </span>
          ) : null}
        </div>
        <div className="grid grid-cols-2 gap-2">
          <FlowSide who="FII" net={row.fii_net} buy={row.fii_buy} sell={row.fii_sell} />
          <FlowSide who="DII" net={row.dii_net} buy={row.dii_buy} sell={row.dii_sell} />
        </div>
      </CardContent>
    </Card>
  );
}

/** FII / DII cash-market flows — cards, trend sparkline and paged session cards. */
export function FiiDiiTab() {
  const { data, isLoading, isError } = useFiiDii();
  const [page, setPage] = useState(0);
  const rows = data?.rows ?? [];
  const latest = rows[0];
  // Rows arrive newest-first; the trend line reads left→right chronologically.
  const fiiSeries = [...rows].reverse().map((r) => r.fii_net);
  const diiSeries = [...rows].reverse().map((r) => r.dii_net);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center gap-3 py-20 text-muted-foreground">
        <Loader variant="dots" size={28} label="Loading FII/DII flows" />
        <p className="text-sm">Loading institutional flows…</p>
      </div>
    );
  }

  if (isError || rows.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border py-16 text-center">
        <p className="text-sm font-medium">Flows unavailable right now</p>
        <p className="mt-1 text-sm text-muted-foreground">
          Please check back shortly.
        </p>
      </div>
    );
  }

  const pageCount = Math.max(1, Math.ceil(rows.length / SESSIONS_PAGE_SIZE));
  const safePage = Math.min(page, pageCount - 1);
  const pageRows = rows.slice(
    safePage * SESSIONS_PAGE_SIZE,
    (safePage + 1) * SESSIONS_PAGE_SIZE,
  );

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        {(
          [
            {
              icon: Globe2,
              title: "FII net",
              tip: "Foreign Institutional Investors — big overseas funds trading Indian shares. Net = what they bought minus what they sold, in ₹ crore.",
              net: latest?.fii_net,
              series: fiiSeries,
            },
            {
              icon: Building2,
              title: "DII net",
              tip: "Domestic Institutional Investors — Indian mutual funds, insurers and pension funds. Net = buys minus sells, in ₹ crore.",
              net: latest?.dii_net,
              series: diiSeries,
            },
          ] as const
        ).map(({ icon: Icon, title, tip, net, series }) => (
          <Card key={title}>
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-1.5 text-sm">
                <Icon className="size-4 text-muted-foreground" />
                {title}
                <span className="font-mono text-xs font-normal text-muted-foreground">
                  ₹ Cr
                </span>
                <InfoTip label={`What is ${title}?`}>{tip}</InfoTip>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <p
                className={cn(
                  "font-mono text-xl font-semibold",
                  (net ?? 0) >= 0 ? "text-up" : "text-down",
                )}
              >
                {formatSigned(net)}
              </p>
              <Sparkline values={series} />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Session cards, paged */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Recent sessions</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="grid gap-3 p-4 pt-0 sm:grid-cols-2">
            {pageRows.map((row, i) => (
              <SessionCard
                key={row.date}
                row={row}
                latest={safePage === 0 && i === 0}
              />
            ))}
          </div>
          <div className="border-t border-border">
            <Pager
              page={safePage}
              pageCount={pageCount}
              onPage={setPage}
              hint={`${rows.length} sessions`}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
