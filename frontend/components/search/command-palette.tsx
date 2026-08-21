"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Search, TrendingUp } from "lucide-react";

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { useInstrumentSearch } from "@/lib/hooks/use-instruments";

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onOpenChange(!open);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onOpenChange]);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query), 200);
    return () => clearTimeout(t);
  }, [query]);

  const { data, isFetching } = useInstrumentSearch(debounced);
  const results = useMemo(() => data?.results ?? [], [data]);

  const select = useCallback(
    (ticker: string) => {
      onOpenChange(false);
      setQuery("");
      router.push(`/app/stocks/${encodeURIComponent(ticker)}`);
    },
    [onOpenChange, router],
  );

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput
        placeholder="Search stock or index… e.g. RELIANCE, TCS, Nifty"
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {debounced && results.length === 0 && !isFetching && (
          <CommandEmpty>No match for “{debounced}”.</CommandEmpty>
        )}
        {results.length > 0 && (
          <CommandGroup heading="Instruments">
            {results.map((r) => (
              <CommandItem
                key={r.ticker}
                value={`${r.name} ${r.ticker}`}
                onSelect={() => select(r.ticker)}
              >
                <TrendingUp className="size-4 text-muted-foreground" />
                <span className="flex-1 truncate">{r.name}</span>
                <span className="font-mono text-xs text-muted-foreground">
                  {r.ticker}
                </span>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
        {!debounced && (
          <div className="px-4 py-6 text-center text-sm text-muted-foreground">
            Type a name or ticker — NSE &amp; BSE instruments, plus indices.
          </div>
        )}
      </CommandList>
      <div className="flex items-center gap-4 border-t border-border px-4 py-2 text-[11px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <Search className="size-3" /> search
        </span>
        <span>
          <kbd className="rounded border border-border px-1">↑↓</kbd> navigate
        </span>
        <span>
          <kbd className="rounded border border-border px-1">↵</kbd> open terminal
        </span>
      </div>
    </CommandDialog>
  );
}
