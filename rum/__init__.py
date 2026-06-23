# rum/__init__.py
"""
RUM (Real User Monitoring) — privacy-first field measurement for the SEO analyzer.

Extends the lab/CrUX SEO auditor with continuous, per-session Core Web Vitals and
behavioral field data. See docs/RUM_SYSTEM.md for the full specification.

Call `register(flask_app)` from the main app to mount the ingest endpoint, the
open-source snippet, and the dashboard tabs.
"""
from __future__ import annotations


def register(app) -> bool:
    """Mount the RUM blueprint onto an existing Flask app. Safe no-op on failure."""
    try:
        from .api import bp
        app.register_blueprint(bp)
        return True
    except Exception as exc:  # pragma: no cover - keep host app resilient
        app.logger.warning("RUM blueprint not registered: %s", exc) if hasattr(app, "logger") else None
        return False
