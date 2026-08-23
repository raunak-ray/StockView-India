import type { ReactNode } from "react";
import { Info } from "lucide-react";

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

/**
 * Small "?" affordance used across data surfaces: hover (or focus) reveals a
 * short plain-language explanation of the jargon it sits next to.
 */
export function InfoTip({
  children,
  side = "top",
  label = "What is this?",
}: {
  children: ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  label?: string;
}) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            type="button"
            aria-label={label}
            className="shrink-0 rounded-sm text-muted-foreground/60 transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:outline-ring"
          >
            <Info className="size-3.5" />
          </button>
        </TooltipTrigger>
        <TooltipContent side={side}>{children}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
