"""CLI entrypoint: python -m gaugora / gaugora."""

from __future__ import annotations

import logging

from gaugora.app import create_app
from gaugora.config import load_settings


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    settings = load_settings()
    app = create_app(settings)

    from waitress import serve

    logging.getLogger(__name__).info(
        "Starting Gaugora on %s:%s", settings.host, settings.port
    )
    serve(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
