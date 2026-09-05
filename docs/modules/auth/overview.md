# Auth — what it is

The auth module handles **who you are**. It runs registration, login, logout, and the silent
"keep me signed in" refresh that happens while you use the app.

Without auth, the app would have no idea which watchlist is yours, which paper trades are
yours, or which alerts belong to you. Auth sits in front of every personal feature.

## What you can do with it

- **Register** a new account with a username and password.
- **Log in** and get two cookies set in your browser.
- **Stay logged in** for 7 days. The site refreshes your session in the background — no
  re-login popups.
- **Log out** and clear both cookies.
- **Ask "who am I?"** with `/me` so the header can show your name.

## What it does not do

- It does not store your password in plain text. Only an Argon2 hash is saved.
- It does not use sessions on the server. It uses two short-lived tokens stored as
  cookies in your browser.
- It does not let you reset a forgotten password. That feature is not built yet.
- It does not use email. Your username is your identity.

## A real example

You click **Register**, type `demo2` and a password. The server hashes the password,
saves the user, and sets two cookies:

- `sv_access` — good for 15 minutes, used on every request to prove who you are.
- `sv_refresh` — good for 7 days, used only when the access one expires.

You open `/app`. The header reads `/me` and shows `demo2`. Fifteen minutes pass. The site
quietly calls `/refresh`, gets a fresh access cookie, and you keep working. After 7 days
without activity, you log in again.

## Why two cookies, not one

One long-lived token is risky — if it leaks, an attacker has access for days. So we use
two:

| Cookie | Lifetime | Purpose | Where it travels |
|---|---|---|---|
| `sv_access` | 15 minutes | Proves identity on every API call | Sent on every request |
| `sv_refresh` | 7 days | Mints a new access cookie when the old one expires | Sent only to `/refresh` |

A leaked access cookie is useful for at most 15 minutes. A leaked refresh cookie is
useful only until it is used once — the first refresh **rotates** (replaces) it, so the
attacker cannot reuse it.

## Where it lives in the codebase

- Backend code: `backend/app/modules/auth/`
- Backend dev notes: `backend/docs/auth/`
- Frontend pages: `frontend/app/(auth)/login/` and `frontend/app/(auth)/register/`
- Frontend API client: `frontend/lib/api/auth.ts`
- Frontend hook: `frontend/lib/hooks/use-auth.ts`

## Consumed by (frontend pages)

- [Auth pages](../../pages/auth/overview.md) — `/login` and `/register` are the entry points.
- [Settings](../../pages/settings/overview.md) — reads the `useMe` query to display the profile card.
- [Dashboard](../../pages/dashboard/overview.md) — uses `useMe` for the greeting.
- All other `/app/*` pages — gated by `RequireAuth`, which calls `useMe`; the route guard
  in `proxy.ts` redirects unauthenticated users to `/login`.

## Related pages in this folder

- [How it works](how-it-works.md) — the request flow, the token dance, the rate limit.
- [Implementation](implementation.md) — file-by-file reading order, the two DB tables,
  the endpoints.