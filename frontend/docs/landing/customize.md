# Landing — Customize Without Coding

Almost all landing text lives in **one file**:
`frontend/app/constants.ts`. Change the text between quotes, save, done.

## What you can edit there

| Constant | Controls |
|---|---|
| `NAV_LINKS` | Header links (label + scroll target) |
| `HERO` | Badge, title lines, gradient word, subtitle, button labels |
| `HERO_STATS` | The four trust numbers (value + label) |
| `FEATURES` | Bento cards: icon, title, description, illustration key |
| `HOW_IT_WORKS_STEPS` | The four steps |
| `TEAM_MEMBERS` | Names, roles, one-line bios, profile links |
| `CTA_BAND` | Final call-to-action text + button |
| `FOOTER` | Tagline, link groups, disclaimer |
| `FOOTER_SOCIALS` | Social links (GitHub / X / LinkedIn) |

## Tips

- Keep titles short — they must fit on mobile.
- The hero's `gradientWord` is colored differently: keep it the last word of
  the last title line (e.g. "Trade.").
- Links starting with `#` scroll to a section; `/login` goes to a page.
- After saving, the dev server hot-reloads — just look at the browser.
