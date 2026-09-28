"""Metrics history and retention routes."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for

from gaugora.extensions import session_scope
from gaugora.repositories.metrics import MetricRepository

bp = Blueprint("metrics", __name__, url_prefix="/metrics")


@bp.route("/", methods=["GET", "POST"])
def metrics_page():
    if request.method == "POST":
        metric_id = int(request.form["metric_id"])
        retention_days = int(request.form["retention_days"])
        with session_scope() as session:
            updated = MetricRepository(session).update_retention(metric_id, retention_days)
            if updated is None:
                flash("Metric not found.", "error")
            else:
                flash(f"Retention updated for {updated.name}.", "success")
        return redirect(url_for("metrics.metrics_page"))

    selected_key = request.args.get("key")
    with session_scope() as session:
        repo = MetricRepository(session)
        definitions = repo.list_definitions()
        if not definitions:
            return render_template(
                "metrics.html",
                definitions=[],
                selected=None,
                chart_labels=[],
                chart_values=[],
            )
        if selected_key is None:
            selected_key = definitions[0].key
        selected = repo.get_definition_by_key(selected_key)
        since = datetime.now(timezone.utc) - timedelta(days=1)
        history = repo.history(selected_key, since=since, limit=500) if selected else []
        def_rows = [
            {
                "id": d.id,
                "key": d.key,
                "name": d.name,
                "retention_days": d.retention_days,
                "enabled": d.enabled,
            }
            for d in definitions
        ]
        selected_row = (
            {
                "id": selected.id,
                "key": selected.key,
                "name": selected.name,
                "retention_days": selected.retention_days,
            }
            if selected
            else None
        )
        chart_labels = [
            s.collected_at.strftime("%H:%M:%S") if s.collected_at else "" for s in history
        ]
        chart_values = [round(s.value, 2) for s in history]

    return render_template(
        "metrics.html",
        definitions=def_rows,
        selected=selected_row,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )
