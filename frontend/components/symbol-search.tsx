"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Search, TrendingUp } from "lucide-react";

import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useInstrumentSearch } from "@/lib/hooks/use-instruments";
import { cn } from "@/lib/utils";

interface SymbolSearchProps {
  value: string;
  onChange: (ticker: string, name?: string) => void;
  placeholder?: string;
  className?: string;
}

export function SymbolSearch({
  value,
  onChange,
  placeholder = "Search stock…",
  className,
}: SymbolSearchProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query), 200);
    return () => clearTimeout(t);
  }, [query]);

  const { data, isFetching } = useInstrumentSearch(debounced);
  const results = useMemo(() => data?.results ?? [], [data]);

  const select = useCallback(
    (ticker: string, name: string) => {
      onChange(ticker, name);
      setOpen(false);
      setQuery("");
    },
    [onChange],
  );

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          role="combobox"
          aria-expanded={open}
          aria-controls="symbol-search-listbox"
          className={cn(
            "flex h-9 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring disabled:cursor-not-allowed disabled:opacity-50 font-mono",
            className,
          )}
        >
          <span className={value ? "text-foreground" : "text-muted-foreground"}>
            {value || placeholder}
          </span>
          <Search className="ml-2 size-4 shrink-0 opacity-50" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-[--radix-popover-trigger-width] p-0" align="start">
        <Command shouldFilter={false}>
          <CommandInput
            placeholder="Type a name or ticker…"
            value={query}
            onValueChange={setQuery}
          />
          <CommandList>
            {debounced && results.length === 0 && !isFetching && (
              <CommandEmpty>No match for &ldquo;{debounced}&rdquo;.</CommandEmpty>
            )}
            {results.length > 0 && (
              <CommandGroup heading="Instruments">
                {results.map((r) => (
                  <CommandItem
                    key={r.ticker}
                    value={`${r.name} ${r.ticker}`}
                    onSelect={() => select(r.ticker, r.name)}
                  >
                    <TrendingUp className="mr-2 size-4 text-muted-foreground" />
                    <span className="flex-1 truncate">{r.name}</span>
                    <span className="ml-2 font-mono text-xs text-muted-foreground">
                      {r.ticker}
                    </span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
