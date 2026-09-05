# Setup

This guide is for **Windows users on the team**. You're getting a
pre-made `.env` file from the project lead — paste it in, run two
commands, you're done. The `.env` points to a hosted PostgreSQL and
hosted Redis, so **no Docker, no local database, nothing extra to
install**.

Total time: about 5 minutes.

## What you need to install (one-time)

1. **Python 3.12** — download from
   [python.org/downloads](https://www.python.org/downloads/). In the
   installer, tick **"Add Python to PATH"**. Click Install Now.
2. **Node.js 20+** — download the **LTS** installer from
   [nodejs.org](https://nodejs.org/). Use all the default options.
3. **Git** — download from [git-scm.com](https://git-scm.com/). Use
   all the default options.

You do **not** need Docker, PostgreSQL, or Redis. The hosted
services in the `.env` cover that.

## The 5 steps

### 1. Open PowerShell and clone the repo

Press the **Windows key**, type `powershell`, hit **Enter**. Then:

```powershell
git clone <repo-url> StockView
cd StockView
```

### 2. Put the `.env` file in the backend folder

The project lead gave you a file called `.env`. **Move or copy it
into `StockView\backend\`** so the full path is
`StockView\backend\.env`.

You can do this in File Explorer (it'll warn you about the dot
prefix — click "Yes"), or in PowerShell:

```powershell
# If your .env is on the Desktop, for example:
Copy-Item "$env:USERPROFILE\Desktop\.env" "StockView\backend\.env"

# Sanity check
Test-Path "StockView\backend\.env"   # should print: True
```

The file is small (4 lines). It looks like:

```env
SV_DEBUG=false
SV_DATABASE_URL=postgresql+asyncpg://...
SV_REDIS_URL=redis://...
SV_SECRET_KEY=...
```

Don't edit it. The values point to hosted services — they already
work.

### 3. Set up the backend (one copy-paste)

In the same PowerShell window:

```powershell
cd StockView\backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Wait until pip finishes (about 1–2 minutes). You'll see a wall of
"Requirement already satisfied" / "Successfully installed" lines.
At the end you should be back at a prompt that looks like:

```
(.venv) PS C:\...\StockView\backend>
```

**If PowerShell says "running scripts is disabled"** when you run
`.\.venv\Scripts\Activate.ps1`, run this once (and only once) in a
PowerShell **opened as Administrator**:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Then close the admin window, go back to your normal PowerShell, and
re-run `.\.venv\Scripts\Activate.ps1`.

### 4. Start the backend (one command)

Still in the same PowerShell window, with `(.venv)` showing:

```powershell
stockview-backend dev
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [...]
INFO:     Application startup complete.
```

If you see `Application startup complete.` — the backend is live.
**Leave this window open.** Open a new PowerShell window for the
frontend (next step).

If you see an error, jump to [Troubleshooting](#troubleshooting) at
the bottom of this page.

### 5. Start the frontend (new PowerShell window)

Press **Win + R**, type `powershell`, hit **Enter**. In the new
window:

```powershell
cd StockView\frontend
npm install
npm run dev
```

Wait until you see:

```
▲ Next.js 16.x
- Local:        http://localhost:3000
✓ Ready in 3s
```

**Open your browser** at <http://localhost:3000>. You should see
the StockView landing page.

### 6. Log in

The app ships with a demo account:

- **Username**: `demo`
- **Password**: `demo123`

You land on the dashboard. That's it — you're set up.

---

## Day-to-day use

You only do steps 1, 2, 5 once. After that, every time you want to
work on the project:

1. **Open PowerShell window A** (the backend):

   ```powershell
   cd StockView\backend
   .\.venv\Scripts\Activate.ps1
   stockview-backend dev
   ```

2. **Open PowerShell window B** (the frontend):

   ```powershell
   cd StockView\frontend
   npm run dev
   ```

3. Open <http://localhost:3000> in your browser.

To **stop** everything: press **Ctrl+C** in each window.

## What if I need to re-clone or wipe everything?

```powershell
# Remove the project folder entirely
Remove-Item -Recurse -Force StockView

# Start fresh
git clone <repo-url> StockView
# Then redo steps 2–5
```

## Useful commands (all run from `StockView\backend` with `.venv` active)

| Command | What it does |
|---|---|
| `stockview-backend dev` | Start the backend with auto-reload on :8000 |
| `stockview-backend start` | Start the backend without auto-reload (production-style) |
| `stockview-backend migrate` | Apply database migrations |
| `stockview-backend seed` | Insert demo data (idempotent) |
| `stockview-backend test` | Run the test suite |
| `stockview-backend lint` | Run the linter |

For the frontend, `package.json` already gives you:

| Command | What it does |
|---|---|
| `npm run dev` | Start the frontend on :3000 |
| `npm run build` | Build for production |
| `npm run lint` | Run the linter |

## Troubleshooting

### "running scripts is disabled on this system"

You ran `.\.venv\Scripts\Activate.ps1` for the first time and
PowerShell blocked it. See step 3 above — open PowerShell **as
Administrator** once and run `Set-ExecutionPolicy -Scope CurrentUser
-ExecutionPolicy RemoteSigned`. Then go back to your normal
window.

### `py -3.12` says "the Python version is not found"

You either:

1. Didn't tick **"Add Python to PATH"** in the Python installer.
   Re-run the installer, choose "Modify", tick the box, save.
2. Installed Python 3.13 instead of 3.12. The project requires 3.12
   specifically. Uninstall and install 3.12.

To check what you have:

```powershell
python --version
# Should print: Python 3.12.x
```

### `stockview-backend: command not found`

The `pip install -e ".[dev]"` step either didn't run, didn't finish,
or ran in a different terminal than the one you're using now.

Fix:

```powershell
# Make sure the venv is active (you should see (.venv) in the prompt)
cd StockView\backend
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
# Look for "Successfully installed stockview-backend-0.1.0"
stockview-backend dev
```

### Backend startup error: "could not connect to server" or "password authentication failed"

The `.env` file is wrong, missing, or in the wrong place. Check:

```powershell
Test-Path "StockView\backend\.env"   # should print: True
Get-Content "StockView\backend\.env"  # should print 4 lines
```

If the file is empty, you didn't get a real `.env` from the project
lead — ask for it again. **Do not edit the values yourself.** The
URLs point to hosted services with credentials baked in.

### Backend startup error: "FATAL: role ... does not exist"

Same as above — the `.env` isn't being read. Check the file exists at
`StockView\backend\.env` and has 4 non-empty lines.

### Frontend shows "Failed to fetch" on every page

The backend isn't running. In window A, did you see
`Application startup complete.`? If not, restart it with
`stockview-backend dev`.

If the backend is running but the frontend still says "Failed to
fetch", check that the frontend is reading the right backend URL.
In the frontend window, look at the first lines of output — it
should mention `http://localhost:8000`.

### Port 8000 is already in use

Another program is using port 8000. Either close that program, or
change the backend port. Easiest:

```powershell
# Edit .env and add this line:
#   SV_PORT=8001
# Then restart `stockview-backend dev`
```

(You'll also need to update `frontend/.env.local` with
`NEXT_PUBLIC_API_BASE=http://localhost:8001/api/v1`.)

### `npm install` is slow or fails

Try once more — npm sometimes has flaky network. If it keeps
failing:

```powershell
# Clear npm's cache
npm cache clean --force
npm install
```

### A page shows "Failed to load NSE data"

The NSE section uses nsepython. NSE sometimes blocks non-India
networks. This is normal — the app falls back to a static fixture.
Other pages (dashboard, stock terminal, sectors) still work.

### First ML prediction takes 30–60 seconds

Expected. The ML model trains on first call per stock. Subsequent
calls are fast (~50ms). See the [ML module docs](modules/ml/overview.md).

### Alerts fire within seconds of being created

Known bug. The `lastPrice` vs `price` mismatch in
`backend\app\modules\alerts\service.py` makes every alert fire
immediately. The fix is a 4-line change documented in
[alerts implementation](modules/alerts/implementation.md#the-fix-in-detail).
Until the fix lands, every alert goes straight to "Triggered".

### How do I know the backend is actually working?

Open <http://localhost:8000/healthz> in your browser. You should
see:

```json
{"status":"ok"}
```

If you see that, the backend is up and talking to the database.

## Related

- [Getting started](getting-started.md) — the 5-minute first-time user walkthrough.
- [Database](database.md) — the schema and tables.
- [Architecture](architecture.md) — the bigger picture.
- [Demo guide](demo-guide.md) — the 7-minute walkthrough for examiners.