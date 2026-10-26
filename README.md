# Gaugora

Per-VM resource monitoring agent: samples CPU, memory, and disk with `psutil`, stores history in SQLite (or PostgreSQL), evaluates threshold alert rules with consecutive spike guards, and sends email notifications with diagnostics via a retryable mail queue. Managed through a clean Flask + Jinja UI.

## Features

- **Host Metrics Sampling**: Periodic sampling of CPU, memory, and disk usage via `psutil`.
- **Consecutive Spike Guard**: Avoids false alarms on momentary 1-second spikes; alerts only trigger after continuous consecutive threshold breaches (e.g. 3 checks in a row).
- **Automated Data Retention**: Hourly retention job cleans old samples based on per-metric retention days, logging execution duration, rows cleaned, and status banner in the UI.
- **Diagnostics in Alerts**: Alert emails include top processes and host CPU/memory diagnostics taken at the time of the spike.
- **Reliable Mail Queue**: Immediate send with exponential backoff retries on SMTP failure.
- **Database Migrations via Alembic**: File-based migration tracking with automatic startup migration or manual CLI control.

---

## Quick start (local)

```bash
# Create venv and install dependencies
uv sync

# Configure environment
cp .env.example .env

# Run (UI + sampler + mail worker in one process)
uv run gaugora
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080)

---

## Docker

```bash
cp .env.example .env
docker compose up --build -d
```

* SQLite is stored on the `gaugora-data` volume at `/data/gaugora.db`.
* Compose uses `pid: host` so alert emails can list **host** top processes (who is hot), not only processes inside the Gaugora container.

---

## First-time setup

1. Set `GAUGORA_PROJECT_NAME` in `.env` (shown in alert emails).
2. Open **SMTP** in the web UI and configure host, from-address, credentials, and recipients.
3. Open **Rules** and create a threshold rule (e.g. CPU > 85%, 3 consecutive spikes required).
4. Watch **Dashboard** / **Metrics** for live graphs and auto-retention status banner; **Mail** for queue status and delivery attempts.

---

## Database Migrations (Alembic)

Gaugora uses **Alembic** to manage database schema migrations file-by-file in the `alembic/versions/` directory.

### Automatic Migrations (Default)
By default (`GAUGORA_AUTO_MIGRATE=true`), Gaugora automatically checks and applies any pending migrations up to `head` on application startup.

### Manual Migrations (CLI)
To run migrations manually (e.g., in CI/CD or strict production deployments), set `GAUGORA_AUTO_MIGRATE=false` in your `.env`, and use the following commands:

```bash
# Apply all pending migrations (like Django's migrate)
uv run alembic upgrade head

# Check the current database migration revision
uv run alembic current

# View migration history
uv run alembic history

# Rollback the last migration step
uv run alembic downgrade -1
```

### Creating New Migrations
When you make changes to models in `src/gaugora/models/`:

```bash
# Auto-generate a new migration script from SQLAlchemy models
uv run alembic revision --autogenerate -m "describe_your_change"
```
Review the newly generated file in `alembic/versions/`, then apply it with `uv run alembic upgrade head`.

---

## Environment Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `GAUGORA_PROJECT_NAME` | `Gaugora` | Project/VM name shown in alert emails |
| `GAUGORA_SECRET_KEY` | `dev-secret-change-me` | Flask secret key |
| `GAUGORA_DATABASE_URL` | `sqlite:///./data/gaugora.db` | SQLAlchemy database URL |
| `GAUGORA_SAMPLE_INTERVAL_SECONDS` | `60` | Metric sample interval |
| `GAUGORA_MAIL_RETRY_INTERVAL_SECONDS` | `30` | Mail retry loop interval |
| `GAUGORA_MAIL_MAX_ATTEMPTS` | `5` | Maximum retry attempts for failed emails |
| `GAUGORA_AUTO_MIGRATE` | `true` | Automatically apply migrations on startup (`true` / `false`) |
| `GAUGORA_HOST` | `0.0.0.0` | HTTP bind host |
| `GAUGORA_PORT` | `8080` | HTTP bind port |

---

## Layout

See [documents/architecture.md](documents/architecture.md) and [documents/plan.md](documents/plan.md).
