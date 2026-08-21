"use client";

import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";

/** Light/dark switch. Dark is the product default (plan/03 §0.5).
 *  Icons are swapped purely via CSS `dark:` variants, so SSR output
 *  matches the first client render (no mounted gate needed). */
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const isDark = resolvedTheme === "dark";

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={
        resolvedTheme
          ? `Switch to ${isDark ? "light" : "dark"} mode`
          : ""
      }
      onClick={() => setTheme(isDark ? "light" : "dark")}
    >
      <Sun className="size-4 scale-100 rotate-0 transition-transform duration-200 dark:scale-0 dark:-rotate-90" />
      <Moon className="absolute size-4 scale-0 rotate-90 transition-transform duration-200 dark:scale-100 dark:rotate-0" />
    </Button>
  );
}
