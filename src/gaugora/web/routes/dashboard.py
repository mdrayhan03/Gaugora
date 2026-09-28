"""Dashboard routes."""

from __future__ import annotations

from flask import Blueprint, current_app, redirect, render_template, url_for

from gaugora.extensions import session_scope
from gaugora.repositories.mail import MailRepository
from gaugora.repositories.metrics import MetricRepository
from gaugora.services.collector import CollectorService

bp = Blueprint("dashboard", __name__)


@bp.get("/")
def index():
    with session_scope() as session:
        metrics_repo = MetricRepository(session)
        mail_repo = MailRepository(session)
        definitions = metrics_repo.list_definitions()
        latest = metrics_repo.latest_samples_map()
        # If no samples yet, take one immediately for a useful first paint.
        if not latest:
            CollectorService(session).collect_once()
            latest = metrics_repo.latest_samples_map()
        queue = mail_repo.list_queue(limit=10)
        cards = [
            {
                "key": d.key,
                "name": d.name,
                "value": latest[d.key].value if d.key in latest else None,
                "collected_at": latest[d.key].collected_at if d.key in latest else None,
            }
            for d in definitions
        ]
        queue_rows = [
            {
                "id": q.id,
                "subject": q.subject,
                "status": q.status,
                "attempts": q.attempts,
                "created_at": q.created_at,
                "last_error": q.last_error,
            }
            for q in queue
        ]
    settings = current_app.config["GAUGORA_SETTINGS"]
    return render_template(
        "dashboard.html",
        cards=cards,
        queue_rows=queue_rows,
        sample_interval=settings.sample_interval_seconds,
        project_name=settings.project_name,
    )


@bp.post("/refresh")
def refresh():
    """Take a fresh sample, then reload the dashboard."""
    with session_scope() as session:
        CollectorService(session).collect_once()
    return redirect(url_for("dashboard.index"))
