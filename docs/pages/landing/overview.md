# Landing page — what it is

The landing page is the **public homepage at `/`**. No login required. It is the
first thing anyone sees — examiners, recruiters, casual visitors. Its job is
to explain what StockView is, show off the features visually, and funnel
people to sign up.

It is purely a marketing page — no data fetches, no API calls. Everything
visible is rendered from static copy in `frontend/app/constants.ts`. Edit that
file and the next rebuild changes the page.

## What visitors see

Reading top to bottom:

| Section | Purpose |
|---|---|
| **Site header** | Logo, nav links, sign-in / register buttons |
| **Hero** | Big animated headline, the WebGL aurora, the "Start trading free" CTA |
| **Hero preview** | A mock terminal panel next to the headline, showing what the app looks like |
| **Ticker marquee** | Scrolling row of NSE tickers with live % change — adds motion, signals "real data" |
| **Bento features** | Six feature cards in a bento grid (terminal, signal, ML, NSE, backtest, sectors, ledger) |
| **How it works** | 4-step strip: Search → Analyze → Backtest → Trade |
| **Team section** | 4 placeholder team member cards |
| **CTA band** | Final call-to-action before the footer |
| **Site footer** | Link groups (Product, Account, Resources, Legal), social icons, disclaimer |

The page is dark by default (`defaultTheme="dark"` in the providers). It
works in light mode too, but every screenshot in the project shows dark.

## Why it is its own page

- **Public access.** No auth. The `proxy.ts` matcher excludes `/`.
- **Static content.** All copy lives in `constants.ts`. No backend calls.
  This is the one screen that can survive a backend outage.
- **Different layout system.** The landing uses full-bleed sections and
  large typography. The app (`/app/*`) uses a sidebar layout. They share
  fonts and primitives but nothing else.

## The constants file

Every text on the page lives in `frontend/app/constants.ts`. The file has
eight exported objects:

| Export | What it controls |
|---|---|
| `NAV_LINKS` | The three links in the header (Features, How it works, Team) |
| `HERO` | Badge text, title lines, gradient word, subtitle, both CTA buttons |
| `HERO_STATS` | The four small trust numbers under the buttons (646 NSE instruments, etc.) |
| `FEATURES` | The six bento feature cards — icon, title, description, graphic type |
| `HOW_IT_WORKS_STEPS` | The four steps in the strip |
| `TEAM_MEMBERS` | The four team cards — name, role, bio, link |
| `CTA_BAND` | The final CTA section's title, subtitle, button label |
| `FOOTER` | Tagline, four link groups, copyright, disclaimer |
| `FOOTER_SOCIALS` | The three social icons in the footer |

Edit the text between the quotes, save, and the next page load renders the
new copy. No code change needed.

## The WebGL aurora

The hero section has three background layers:

1. **CSS radial gradient** (always visible, even without WebGL).
2. **HeroShader** — a WebGL fragment shader rendering a moving aurora. Lives
   in `frontend/app/components/hero-shader.tsx`.
3. **Dot grid texture + drifting glow blobs** for the tactile feel.

The WebGL shader is GPU-accelerated. If WebGL is unavailable or disabled, the
CSS gradient still looks good — the page degrades gracefully.

## A real example

A visitor lands on `/`. They see:

- A dark page with a moving aurora behind the headline "Research. Signal.
  Backtest. Trade."
- A subtle SVG preview of the terminal on the right.
- Four small stats: "646 NSE instruments", "40+ Indicators & overlays",
  "6 Backtest strategies", "₹1L Paper trading capital".
- Below: a scrolling ticker tape of RELIANCE, TCS, INFY, HDFCBANK, ITC with
  their daily % change.
- Below: six feature cards in a bento grid.
- Below: "Search → Analyze → Backtest → Trade" steps.
- Below: four team cards.
- A "Create free account" CTA.
- A four-column footer.

They click "Start trading free" → `/register`. They click "Try the demo
account" → `/login` (the CTA assumes the visitor knows the demo creds).

## What it does not do

- It does not fetch any backend data. The ticker marquee is also static —
  the symbols are baked in.
- It does not redirect logged-in users. If you are already logged in, the
  page still shows the marketing content. The header's sign-in / register
  buttons hide because of the auth state, but the page itself is unchanged.
- It does not have a "logout" button. Logged-in visitors use the dashboard's
  settings page for that.

## Where it lives in the codebase

- Page: `frontend/app/page.tsx`
- Sections: `frontend/app/components/*.tsx` (11 components)
- Copy: `frontend/app/constants.ts`
- Layout: `frontend/app/layout.tsx` (root layout, sets fonts and providers)
- Providers: `frontend/components/providers.tsx` (theme + react-query)

## Backend modules used

None. The landing page is purely static — no API calls. The hero
preview is a mocked terminal rendered with `hero-preview.tsx`. To
go from the landing to the dashboard, click "Sign in" or "Get
started" — both route to `/login`.

## Related pages in this folder

- [How it works](how-it-works.md) — the section-by-section flow, the
  component tree, the data flow.
- [Implementation](implementation.md) — file map, every section's component,
  the constants schema, the providers chain, how to add a new section.