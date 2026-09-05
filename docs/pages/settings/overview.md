# Settings — what it is

The Settings page is the **profile view at `/app/settings`**. It is a
read-only display of the logged-in user's account information. There
is no form to fill in and nothing to save — the page just shows what
the backend knows about you.

It is the smallest page in the app. It exists mostly for completeness
(it is a target of the "Settings" link in the user menu) and to give
the user a place to confirm their session is theirs.

The theme toggle (light/dark) is **not** on this page — it lives in
the topbar of every `/app/*` page. The settings page does not have
toggle-able settings at all.

## What visitors see

A title "Settings" and a single card titled "Profile" with four rows:

| Row | What it shows | Source |
|---|---|---|
| **Username** | The display name used across the app | `user.username` |
| **Role** | The user's role (typically "user" or "admin") | `user.role` |
| **User ID** | The unique user identifier (UUID) | `user.id` |
| **Member since** | The account creation date | `user.created_at` |

Each row has a muted label on the left and the value on the right
(mono font). A `<Separator />` divides the rows.

The page is a single column with a max width of 672px (`max-w-2xl`).
It is the narrowest page in the app.

## A real example

You are logged in as the demo user:

- **Settings** (title).
- **Profile** (card title).
  - **Username**: `demo`
  - **Role**: `user`
  - **User ID**: `8a3f...b21c` (truncated, 16rem max)
  - **Member since**: `4/17/2026` (locale-formatted)

The values are all mono font. The labels are muted. The user ID is
truncated with an ellipsis if it exceeds 16rem — the full ID is
available by selecting the text.

## What the page does not do

- **It does not let you change anything.** No password change, no
  email change, no display name change. The backend does not expose
  these endpoints today.
- **It does not show a "Delete account" button.** Account deletion is
  out of scope.
- **It does not show the session info** (e.g. when the access token
  expires). The session is managed silently.
- **It does not show API keys or developer settings.** There is no
  API key system.

## Where it lives in the codebase

- Page: `frontend/app/(app)/app/settings/page.tsx` (45 lines)
- Hook: `useMe` from `frontend/lib/hooks/use-auth.ts`
- Components used:
  - `Card`, `CardContent`, `CardHeader`, `CardTitle` from
    `@/components/ui/card`
  - `Separator` from `@/components/ui/separator`

The page is the **second-shortest** in the app, after the markets
tabs that are not pages themselves.

## Backend modules used

- [Auth](../../modules/auth/overview.md) — the only module. The page calls `GET /auth/me`
  to render the profile card.

## Related pages in this folder

- [How it works](how-it-works.md) — the data flow, the layout, the
  formatter chain, the role/types.
- [Implementation](implementation.md) — file map, the User type, the
  request trace.