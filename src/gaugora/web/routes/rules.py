"""Alert rules CRUD routes."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from gaugora.extensions import session_scope
from gaugora.repositories.alerts import AlertRepository
from gaugora.repositories.metrics import MetricRepository

bp = Blueprint("rules", __name__, url_prefix="/rules")

AVAILABLE_CHANNELS = [
    ("email", "Email", True),
    ("telegram", "Telegram (coming soon)", False),
    ("slack", "Slack (coming soon)", False),
]


def _parse_channels(form) -> list[str]:
    selected = form.getlist("channels")
    # Only persist implemented + selected; keep unknown for future but email is required for send
    return [c for c in selected if c in {"email", "telegram", "slack"}]


@bp.route("/", methods=["GET", "POST"])
def rules_list():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        metric_key = request.form.get("metric_key", "").strip()
        threshold = float(request.form.get("threshold", "0"))
        cooldown_seconds = int(request.form.get("cooldown_seconds", "300"))
        channels = _parse_channels(request.form)
        enabled = request.form.get("enabled") == "on"
        if not name or not metric_key:
            flash("Name and metric are required.", "error")
        elif not channels:
            flash("Select at least one channel.", "error")
        else:
            with session_scope() as session:
                AlertRepository(session).create_rule(
                    name=name,
                    metric_key=metric_key,
                    threshold=threshold,
                    channels=channels,
                    cooldown_seconds=cooldown_seconds,
                    enabled=enabled,
                )
            flash("Rule created.", "success")
        return redirect(url_for("rules.rules_list"))

    with session_scope() as session:
        rules = AlertRepository(session).list_rules()
        metrics = MetricRepository(session).list_definitions()
        rule_rows = [
            {
                "id": r.id,
                "name": r.name,
                "metric_key": r.metric_key,
                "operator": r.operator,
                "threshold": r.threshold,
                "channels": r.channels,
                "cooldown_seconds": r.cooldown_seconds,
                "enabled": r.enabled,
            }
            for r in rules
        ]
        metric_rows = [{"key": m.key, "name": m.name} for m in metrics]

    return render_template(
        "rules.html",
        rules=rule_rows,
        metrics=metric_rows,
        channels=AVAILABLE_CHANNELS,
    )


@bp.route("/<int:rule_id>", methods=["GET", "POST"])
def rule_edit(rule_id: int):
    if request.method == "POST":
        action = request.form.get("action", "save")
        with session_scope() as session:
            repo = AlertRepository(session)
            rule = repo.get_rule(rule_id)
            if rule is None:
                flash("Rule not found.", "error")
                return redirect(url_for("rules.rules_list"))
            if action == "delete":
                repo.delete_rule(rule)
                flash("Rule deleted.", "success")
                return redirect(url_for("rules.rules_list"))
            name = request.form.get("name", "").strip()
            metric_key = request.form.get("metric_key", "").strip()
            threshold = float(request.form.get("threshold", "0"))
            cooldown_seconds = int(request.form.get("cooldown_seconds", "300"))
            channels = _parse_channels(request.form)
            enabled = request.form.get("enabled") == "on"
            if not name or not metric_key or not channels:
                flash("Name, metric, and at least one channel are required.", "error")
            else:
                repo.update_rule(
                    rule,
                    name=name,
                    metric_key=metric_key,
                    threshold=threshold,
                    channels=channels,
                    cooldown_seconds=cooldown_seconds,
                    enabled=enabled,
                )
                flash("Rule updated.", "success")
        return redirect(url_for("rules.rule_edit", rule_id=rule_id))

    with session_scope() as session:
        rule = AlertRepository(session).get_rule(rule_id)
        metrics = MetricRepository(session).list_definitions()
        if rule is None:
            flash("Rule not found.", "error")
            return redirect(url_for("rules.rules_list"))
        rule_row = {
            "id": rule.id,
            "name": rule.name,
            "metric_key": rule.metric_key,
            "operator": rule.operator,
            "threshold": rule.threshold,
            "channels": list(rule.channels or []),
            "cooldown_seconds": rule.cooldown_seconds,
            "enabled": rule.enabled,
        }
        metric_rows = [{"key": m.key, "name": m.name} for m in metrics]

    return render_template(
        "rule_edit.html",
        rule=rule_row,
        metrics=metric_rows,
        channels=AVAILABLE_CHANNELS,
    )
