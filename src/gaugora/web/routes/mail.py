"""Mail queue and send-log routes."""

from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from gaugora.extensions import session_scope
from gaugora.repositories.mail import MailRepository
from gaugora.services.mailer import MailerService

bp = Blueprint("mail", __name__, url_prefix="/mail")


@bp.get("/")
def mail_queue():
    selected_id = request.args.get("id", type=int)
    with session_scope() as session:
        repo = MailRepository(session)
        items = repo.list_queue(limit=100)
        attempts = (
            repo.list_attempts(selected_id)
            if selected_id
            else repo.list_recent_attempts(limit=50)
        )
        item_rows = [
            {
                "id": i.id,
                "subject": i.subject,
                "status": i.status,
                "attempts": i.attempts,
                "channel": i.channel,
                "to_addresses": i.to_addresses,
                "created_at": i.created_at,
                "sent_at": i.sent_at,
                "last_error": i.last_error,
                "next_retry_at": i.next_retry_at,
            }
            for i in items
        ]
        attempt_rows = [
            {
                "id": a.id,
                "queue_id": a.queue_id,
                "attempted_at": a.attempted_at,
                "success": a.success,
                "error": a.error,
            }
            for a in attempts
        ]
    return render_template(
        "mail_queue.html",
        items=item_rows,
        attempts=attempt_rows,
        selected_id=selected_id,
    )


@bp.post("/<int:item_id>/retry")
def retry_item(item_id: int):
    settings = current_app.config["GAUGORA_SETTINGS"]
    with session_scope() as session:
        repo = MailRepository(session)
        item = repo.get_item(item_id)
        if item is None:
            flash("Queue item not found.", "error")
        elif item.status == "sent":
            flash("Item already sent.", "error")
        else:
            MailerService(session, settings).send_queue_item(item)
            flash(f"Retry attempted for #{item_id}.", "success")
    return redirect(url_for("mail.mail_queue", id=item_id))
