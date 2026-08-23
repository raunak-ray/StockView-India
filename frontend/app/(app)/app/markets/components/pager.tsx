"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";

/** Prev/next pager shared by paginated card lists and tables. */
export function Pager({
  page,
  pageCount,
  onPage,
  hint,
  className,
}: {
  page: number;
  pageCount: number;
  onPage: (next: number) => void;
  hint?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-between gap-3 px-4 py-3",
        className,
      )}
    >
      <span className="truncate font-mono text-xs text-muted-foreground">
        Page {pageCount > 0 ? page + 1 : 0} of {pageCount}
        {hint ? ` · ${hint}` : ""}
      </span>
      <div className="flex items-center gap-1">
        <button
          type="button"
          aria-label="Previous page"
          disabled={page === 0}
          onClick={() => onPage(Math.max(0, page - 1))}
          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:pointer-events-none disabled:opacity-40"
        >
          <ChevronLeft className="size-4" />
        </button>
        <button
          type="button"
          aria-label="Next page"
          disabled={page >= pageCount - 1}
          onClick={() => onPage(Math.min(pageCount - 1, page + 1))}
          className="rounded-md p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground disabled:pointer-events-none disabled:opacity-40"
        >
          <ChevronRight className="size-4" />
        </button>
      </div>
    </div>
  );
}
