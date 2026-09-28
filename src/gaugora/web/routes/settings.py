"""SMTP settings routes."""

from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for

from gaugora.extensions import session_scope
from gaugora.repositories.mail import MailRepository

bp = Blueprint("settings", __name__, url_prefix="/settings")


@bp.route("/smtp", methods=["GET", "POST"])
def smtp_settings():
    if request.method == "POST":
        host = request.form.get("host", "").strip()
        port = int(request.form.get("port", "587"))
        use_tls = request.form.get("use_tls") == "on"
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        from_address = request.form.get("from_address", "").strip()
        to_raw = request.form.get("to_addresses", "")
        to_addresses = [a.strip() for a in to_raw.replace(";", ",").split(",") if a.strip()]
        with session_scope() as session:
            MailRepository(session).update_smtp(
                host=host,
                port=port,
                use_tls=use_tls,
                username=username,
                password=password,
                from_address=from_address,
                to_addresses=to_addresses,
            )
        flash("SMTP settings saved.", "success")
        return redirect(url_for("settings.smtp_settings"))

    with session_scope() as session:
        smtp = MailRepository(session).get_smtp()
        row = {
            "host": smtp.host,
            "port": smtp.port,
            "use_tls": smtp.use_tls,
            "username": smtp.username,
            "from_address": smtp.from_address,
            "to_addresses": ", ".join(smtp.to_addresses or []),
            "has_password": bool(smtp.password),
        }
    return render_template("settings.html", smtp=row)
