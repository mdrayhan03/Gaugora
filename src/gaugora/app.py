"""Flask application factory."""

from __future__ import annotations

from flask import Flask

from gaugora.config import Settings, load_settings
from gaugora.db import init_database
from gaugora.extensions import init_db
from gaugora.jobs import start_scheduler
from gaugora.web import register_blueprints


def create_app(settings: Settings | None = None, *, start_jobs: bool = True) -> Flask:
    settings = settings or load_settings()
    app = Flask(
        __name__,
        template_folder="web/templates",
        static_folder="web/static",
    )
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["GAUGORA_SETTINGS"] = settings

    init_db(settings.database_url)
    init_database()
    register_blueprints(app)

    if start_jobs:
        start_scheduler(app, settings)

    @app.context_processor
    def inject_globals():
        return {"app_name": "Gaugora"}

    return app
