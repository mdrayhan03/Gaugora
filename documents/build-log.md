# Gaugora build log

Running notes from implementation.

## 2026-09-28 — v1 scaffold and app

### Done
- Initialized uv package project (`src/gaugora`).
- Dependencies: flask, sqlalchemy, psutil, apscheduler, python-dotenv, waitress.
- Thin layered layout: models → repositories → services / channels / jobs / web.
- Channel Strategy: `EmailChannel` only; telegram/slack shown disabled in UI.
- SQLite + `create_all` seed for metric definitions and SMTP singleton.
- One process: Flask (waitress) + APScheduler (sample, mail retry, retention).
- Docker + compose with `/data` volume for SQLite.

### Notes / decisions during build
- Cooldown is applied at **enqueue** time so a sustained breach does not flood the mail queue every sample tick.
- New queue items leave `next_retry_at` null until the first failed attempt, avoiding a race between immediate send and the retry job.
- Dockerfile uses `uv sync --frozen` and runs the `gaugora` console script from the project venv.
- Bugfix: `db.init_database` must read `extensions.engine` via the module (not a stale imported name), otherwise it always sees `None`.

### Verify locally
```bash
uv sync
cp .env.example .env
uv run gaugora
```

Smoke-tested: dashboard/metrics/rules/smtp/mail routes 200; collector readings; alert enqueue + failed SMTP attempt recorded as `pending` with retry scheduled.
