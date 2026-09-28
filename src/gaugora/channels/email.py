"""Email channel implementation."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from gaugora.channels.base import ChannelMessage, ChannelResult
from gaugora.models.mail import SmtpSettings


class EmailChannel:
    name = "email"

    def __init__(self, smtp: SmtpSettings) -> None:
        self.smtp = smtp

    def send(self, message: ChannelMessage) -> ChannelResult:
        if not self.smtp.host:
            return ChannelResult(success=False, error="SMTP host is not configured")
        if not self.smtp.from_address:
            return ChannelResult(success=False, error="SMTP from address is not configured")
        recipients = message.to_addresses or list(self.smtp.to_addresses or [])
        if not recipients:
            return ChannelResult(success=False, error="No recipient addresses configured")

        email = EmailMessage()
        email["Subject"] = message.subject
        email["From"] = self.smtp.from_address
        email["To"] = ", ".join(recipients)
        email.set_content(message.body)

        try:
            with smtplib.SMTP(self.smtp.host, self.smtp.port, timeout=30) as server:
                if self.smtp.use_tls:
                    server.starttls()
                if self.smtp.username:
                    server.login(self.smtp.username, self.smtp.password)
                server.send_message(email)
            return ChannelResult(success=True)
        except Exception as exc:  # noqa: BLE001 — surface any SMTP failure to queue
            return ChannelResult(success=False, error=str(exc))
