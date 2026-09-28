"""Web package: blueprints and templates."""

from __future__ import annotations

from flask import Flask


def register_blueprints(app: Flask) -> None:
    from gaugora.web.routes.dashboard import bp as dashboard_bp
    from gaugora.web.routes.mail import bp as mail_bp
    from gaugora.web.routes.metrics import bp as metrics_bp
    from gaugora.web.routes.rules import bp as rules_bp
    from gaugora.web.routes.settings import bp as settings_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(metrics_bp)
    app.register_blueprint(rules_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(mail_bp)
