# Gaugora

Per-VM resource monitoring agent: samples CPU, memory, and disk with `psutil`,
stores history in SQLite, evaluates `metric > N%` alert rules, and sends email
via a mail queue (immediate send + retries). Managed through a Flask + Jinja UI.

## Quick start (local)

```bash
# Create venv and install
uv sync

# Config
cp .env.example .env

# Run (UI + sampler + mail worker in one process)
uv run gaugora
```

Open http://127.0.0.1:8080

## Docker

```bash
cp .env.example .env
docker compose up --build -d
```

SQLite is stored on the `gaugora-data` volume at `/data/gaugora.db`.

## First-time setup

1. Set `GAUGORA_PROJECT_NAME` in `.env` (shown in alert emails).
2. Open **SMTP** and configure host, from, and recipients.
3. Open **Rules** and create a threshold rule (e.g. memory > 85%).
4. Watch **Dashboard** / **Metrics** for samples; **Mail** for queue and attempts.

## Layout

See [documents/architecture.md](documents/architecture.md) and [documents/plan.md](documents/plan.md).

## Environment

| Variable | Default | Purpose |
|----------|---------|---------|
| `GAUGORA_PROJECT_NAME` | `Gaugora` | Project/VM name shown in alert emails |
| `GAUGORA_SECRET_KEY` | `dev-secret-change-me` | Flask secret |
| `GAUGORA_DATABASE_URL` | `sqlite:///./data/gaugora.db` | SQLAlchemy URL |
| `GAUGORA_SAMPLE_INTERVAL_SECONDS` | `60` | Metric sample interval |
| `GAUGORA_MAIL_RETRY_INTERVAL_SECONDS` | `30` | Mail retry loop |
| `GAUGORA_MAIL_MAX_ATTEMPTS` | `5` | Max send attempts |
| `GAUGORA_HOST` | `0.0.0.0` | Bind host |
| `GAUGORA_PORT` | `8080` | Bind port |
