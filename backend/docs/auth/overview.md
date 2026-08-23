# Auth — Overview

**Plain words:** the front door. It creates accounts, checks who you are, and
keeps you signed in while you use the site — so your watchlist is yours only.

## What it does

- **Register** — create a username + password.
- **Login** — verify the password, hand the browser two secure tokens
  (access + refresh) stored in httpOnly cookies.
- **Refresh** — silently swap an old token for a new one (stay logged in).
- **Logout** — clear the cookies.
- **Me** — "who am I?" (every page load).

Passwords are hashed with argon2 (one-way scramble) — the real password is
never stored. Too many failed logins from one place triggers a temporary
block (rate limiting).

## Demo accounts (pre-seeded)

- `demo` / `demo123`
- `admin` / `admin123`

## Where the code lives

`backend/app/modules/auth/` — `router.py`, `service.py`, `models.py` (user
table), `schemas.py`. Covered by `backend/tests/`.

## Analogy

A token is like a event wristband: proves you paid, expires, and the refresh
token gets you a new one at the door.
