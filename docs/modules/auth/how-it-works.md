# Auth — how it works

This page explains what happens when you register, log in, refresh, and log out.
Read this if you want to understand the token dance before reading the code.

## The big picture

```mermaid
flowchart LR
    Browser -->|username + password| Server
    Server -->|Argon2 hash stored| DB[(users table)]
    Server -->|access cookie 15m + refresh cookie 7d| Browser
    Browser -->|every API call with access cookie| Server
    Server -->|checks JWT signature, returns data| Browser
    Browser -->|access expired? calls /refresh| Server
    Server -->|rotates refresh, sends new access| Browser
```

The server never keeps your session in memory. It hands your browser two tokens; the
tokens themselves prove who you are.

## Registration

```mermaid
sequenceDiagram
    participant B as Browser
    participant S as Server
    participant D as Database

    B->>S: POST /api/v1/auth/register { username, password }
    S->>S: check_rate_limit(ip)
    S->>D: SELECT * FROM users WHERE username = ?
    alt username taken
        D-->>S: row found
        S-->>B: 409 Conflict
    else username free
        D-->>S: no row
        S->>S: hash_password(password) → Argon2 hash
        S->>D: INSERT INTO users (id, username, password_hash, role)
        S->>S: create_access_token(user.id)
        S->>D: INSERT INTO refresh_tokens (id, user_id, token_hash)
        S-->>B: 201 Created + Set-Cookie sv_access, sv_refresh
    end
```

Things to notice:

- The plain password **never reaches the database**. Only the Argon2 hash is stored.
- Both cookies are set with `HttpOnly`. JavaScript on the page cannot read them — that
  blocks a whole class of XSS token-stealing attacks.
- The refresh cookie holds a random 48-byte URL-safe string. Only its SHA-256 hash is
  saved. If the database leaks, attackers cannot replay refresh tokens.

## Login

```mermaid
sequenceDiagram
    participant B as Browser
    participant S as Server
    participant D as Database

    B->>S: POST /api/v1/auth/login { username, password }
    S->>S: check_rate_limit(ip) + record_attempt(ip)
    S->>D: SELECT * FROM users WHERE username = ?
    alt wrong username or wrong password
        D-->>S: no row OR verify_password fails
        S-->>B: 401 Unauthorized
    else correct
        D-->>S: user row
        S->>S: verify_password(attempt, stored_hash)
        S->>S: create_access_token(user.id)
        S->>D: INSERT INTO refresh_tokens
        S-->>B: 200 OK + Set-Cookie sv_access, sv_refresh
    end
```

The login error message is the **same** for "no such user" and "wrong password":
`Invalid username or password.` This stops username-enumeration attacks where an
attacker probes valid usernames by watching the error text change.

## Rate limiting

Login and register are limited to a small number of attempts per IP per minute
(default 5). The counter lives in a Python dict on the server. When the limit is hit,
the next call returns `429 Too Many Requests` until the window slides forward.

```mermaid
flowchart LR
    A[POST /login] --> B{check_rate_limit ip}
    B -->|under limit| C[record_attempt]
    C --> D[process login]
    B -->|over limit| E[429 Too Many Requests]
```

This is in-memory and per-process. If the backend runs as multiple workers, each
worker has its own counter, so the real limit is roughly `5 × workers`. The planned
move is to Redis (`plan/todo.md` S-02).

## Refresh — the silent part

```mermaid
sequenceDiagram
    participant B as Browser
    participant S as Server
    participant D as Database

    B->>S: POST /api/v1/auth/refresh (Cookie: sv_refresh=...)
    S->>S: sha256(refresh) → digest
    S->>D: SELECT * FROM refresh_tokens WHERE token_hash = digest
    alt not found / revoked / expired
        S-->>B: 401 Unauthorized
    else valid
        S->>D: UPDATE refresh_tokens SET revoked_at = now() WHERE id = ?
        S->>D: INSERT INTO refresh_tokens (new id, new hash)
        S->>S: create_access_token(user.id)
        S-->>B: 200 OK + Set-Cookie sv_access, sv_refresh (new)
    end
```

Each `/refresh` call **revokes** the old refresh token and issues a new one. That is
why we say refresh tokens **rotate**. If an attacker steals your refresh cookie and
tries to use it after you have refreshed, the server sees `revoked_at IS NOT NULL` and
rejects it.

## Logout

```mermaid
flowchart LR
    A[POST /logout with sv_refresh cookie] --> B[DELETE refresh_tokens WHERE hash = digest]
    B --> C[clear sv_access + sv_refresh cookies in browser]
    C --> D[200 OK]
```

The access cookie is stateless — there is nothing on the server to delete. We just
tell the browser to drop it. The refresh cookie is revoked in the DB, so even if the
cookie value is somehow remembered, it is dead.

## Protected routes

Every personal endpoint (watchlist, paper trading, alerts, etc.) depends on
`get_current_user` from `backend/app/core/deps.py`. That function:

1. Reads `sv_access` from the cookie jar.
2. Decodes the JWT with `SV_SECRET_KEY`.
3. Loads the user row by `sub` (the user id from the token).
4. Returns the `User`, or raises `401`.

```mermaid
flowchart LR
    A[Incoming request] --> B{sv_access cookie present?}
    B -->|no| Z[401 Not authenticated]
    B -->|yes| C[decode_access_token JWT]
    C -->|bad signature / expired| Z
    C -->|ok| D[db.get User by id from sub]
    D -->|not found| Z
    D -->|ok| E[route handler runs]
```

## Edge cases you might wonder about

- **Wrong password 5 times in a minute.** 6th attempt returns `429` for ~60 seconds.
- **Username already taken on register.** Returns `409 Conflict` with detail
  `Username already taken.`
- **Refresh token used twice.** First use succeeds and rotates it. Second use returns
  `401 Refresh token invalid or expired.`
- **Access token expires mid-session.** The frontend's `apiFetch` (in
  `frontend/lib/api/client.ts`) catches the `401`, calls `/refresh` once, and retries
  the original request. The user sees nothing.
- **Server restarts.** In-memory rate-limit counters reset to zero. Refresh tokens in
  the DB survive. The dev seed users (`demo`, `admin`) are re-created if missing.