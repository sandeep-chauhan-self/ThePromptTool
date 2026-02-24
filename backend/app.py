"""
Daily Prompt — Flask Application Factory

Creates and configures the Flask application with:
  - SQLAlchemy database connection
  - CORS for Vercel frontend
  - Route blueprints
  - Database initialization (creates tables + seeds app_state)
"""

import os
from flask import Flask
from flask_cors import CORS
from config import get_config
from models import db, AppState


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.config.from_object(get_config())

    # Initialize extensions
    db.init_app(app)

    # CORS — allow frontend origin(s)
    frontend_urls = app.config.get("FRONTEND_URL")
    if frontend_urls and frontend_urls.strip() != "*":
        # Remove trailing slashes and split by comma
        origins = [url.strip().rstrip('/') for url in frontend_urls.split(",")]
    else:
        # Fallback to wildcard or localhost
        origins = ["http://localhost:5173", "http://localhost:5174", "https://the-prompt-tool.vercel.app", "*"]

    CORS(app, origins=origins, methods=["GET", "OPTIONS"], allow_headers=["Content-Type"])

    # Register blueprints
    from routes.prompt import prompt_bp
    from routes.health import health_bp
    app.register_blueprint(prompt_bp)
    app.register_blueprint(health_bp)

    # Initialize database tables and seed app_state on first run
    with app.app_context():
        if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
            db.create_all()
        _ensure_app_state()

    return app


def _ensure_app_state():
    """Ensure app_state rows exist (idempotent)."""
    try:
        for key in ("serve_counter", "total_prompts"):
            existing = AppState.query.filter_by(key=key).first()
            if not existing:
                db.session.add(AppState(key=key, value_int=0))
        db.session.commit()
    except Exception:
        db.session.rollback()


# Create the app instance (used by gunicorn: `gunicorn app:app`)
app = create_app()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
