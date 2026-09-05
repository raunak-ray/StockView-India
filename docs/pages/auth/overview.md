# Login and register pages — what it is

The auth pages are the **sign-in and sign-up screens** at `/login` and
`/register`. They are the gate into the app. Every user hits one of these
before reaching `/app`.

These two pages share a layout, share the same form library, and share the
same session machinery. They differ only in the validation rules and the
fields they show.

## What visitors see

### `/login`

A single card centred on a dark background with a subtle dot-grid texture
and a soft glow. The card contains:

- The "SV" logo and "StockView India" wordmark.
- A title: "Welcome back".
- A subtitle: "Sign in to continue to your trading terminal."
- Two inputs: Username and Password.
- A "Sign in" button (loading state while the request is in flight).
- A demo credentials hint: "Demo: `demo / demo123`" — click to autofill.
- A "No account? Create one" link to `/register`.

### `/register`

Same shell, different copy:

- Title: "Create your account".
- Subtitle: "Start researching, backtesting and paper trading."
- Three inputs: Username, Password, Confirm password.
- A "Create account" button.
- An "Already have an account? Sign in" link to `/login`.

## The route guard

The page is protected by a `proxy.ts` route guard. The guard runs on every
request and:

| Path | No session | Has session |
|---|---|---|
| `/login`, `/register` | show the page | redirect to `/app` |
| `/app/*` | redirect to `/login?next=…` | show the app |
| any other path | normal flow | normal flow |

So if a logged-in user navigates to `/login`, they bounce to `/app`. If a
logged-out user types `/app/stocks/RELIANCE.NS`, they bounce to
`/login?next=/app/stocks/RELIANCE.NS`. After they sign in, the form
redirects to the `next` param.

## The session

Login and register both set the same two cookies:

- `sv_access` — a 15-minute JWT, used on every API call.
- `sv_refresh` — a 7-day token, used to mint a new access token when the old
  one expires.

The browser stores these as `HttpOnly` cookies. The frontend never reads
them directly — it just calls the API endpoints with
`credentials: "include"` and the browser handles the rest.

When the access token expires, the API client (`apiFetch` in
`lib/api/client.ts`) catches the 401, calls `/auth/refresh` once, and retries
the original request. This is **invisible to the user** — they do not see a
re-login prompt unless the refresh token is also expired (7 days of
inactivity).

## A real example

You visit `/app/stocks/RELIANCE.NS` while logged out. The guard redirects
you to `/login?next=/app/stocks/RELIANCE.NS`. You type `demo` and the demo
password, click "Sign in". The server:

1. Hashes the password attempt, compares it to the stored hash.
2. Issues a new access JWT and a new refresh token.
3. Sets both as `HttpOnly` cookies.
4. Returns the user object.

The frontend:

1. Stores the user in React Query cache.
2. Shows a "Welcome back, demo" toast.
3. Calls `router.replace("/app/stocks/RELIANCE.NS")` — back to where you
   wanted to go.

Total visible delay: ~300ms.

## What the pages do not do

- **They do not handle "forgot password".** Not built. Edit
  `backend/app/modules/auth/router.py` and add the page if you need it.
- **They do not handle email verification.** The `register` endpoint creates
  the user immediately. There is no "click the link in your email" step.
- **They do not enforce a unique email.** The username is the identity. You
  can have two users with the same email address (but not the same
  username).
- **They do not show "wrong password" vs "no such user".** Both return the
  same `401 Invalid username or password` to prevent username enumeration.

## Where it lives in the codebase

- Pages: `frontend/app/(auth)/login/page.tsx`, `frontend/app/(auth)/register/page.tsx`
- Layout: `frontend/app/(auth)/layout.tsx` (shared card-on-glow shell)
- Forms: `frontend/app/(auth)/login/components/login-form.tsx`, `frontend/app/(auth)/register/components/register-form.tsx`
- API client: `frontend/lib/api/auth.ts`
- Hooks: `frontend/lib/hooks/use-auth.ts`
- Request wrapper: `frontend/lib/api/client.ts` (single-flight refresh)
- Route guard: `frontend/proxy.ts`
- Backend: `backend/app/modules/auth/` — see [auth module docs](../../modules/auth/overview.md)

## Backend modules used

- [Auth](../../modules/auth/overview.md) — the only module. The pages call `POST /auth/register`,
  `POST /auth/login`, `POST /auth/logout`, `POST /auth/refresh`, and `GET /auth/me`.

## Related pages in this folder

- [How it works](how-it-works.md) — the form library, the validation rules, the
  mutation flow, the toast handling, the session refresh mechanism.
- [Implementation](implementation.md) — file map, every input's validation
  rule, the api client contract, the route guard source, request traces.