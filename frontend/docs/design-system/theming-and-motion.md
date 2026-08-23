# Design System — Theming & Motion

## Theme switching

A small toggle in the header flips light/dark (handled by `next-themes`).
Your choice is remembered. The toggle's icon changes purely via CSS, so
there's no flicker and no hydration mismatch.

## Typography

- **IBM Plex Sans** — text
- **IBM Plex Mono** — numbers and tickers (the "terminal" feel)

## Motion rules

Subtle only, everywhere:

- Quick entrance fades/slides as sections appear
- Softly pulsing dots (live-data markers)
- Chart lines that slowly "draw" themselves
- The landing page's drifting aurora light and the footer's sweeping beam

Everything turns static when your OS requests **reduced motion**.

## For developers (short version)

- Tailwind CSS v4; tokens exposed as utilities (`text-up`, `bg-ai/10`…)
- shadcn-style primitives in `frontend/components/ui/`
- Reusable animation pieces in `frontend/components/motion/`
- One-off landing animations are CSS keyframes at the bottom of
  `globals.css` (`dash-flow`, `soft-pulse`, `float-y`, `beam-x`, `drift`)

## Editing landing content

All landing text lives in `frontend/app/constants.ts` — see
[landing/customize.md](../landing/customize.md).
