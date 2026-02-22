"""
SQLAlchemy models for Daily Prompt.

Tables:
  - prompts: Stores all scraped prompts and their serving state.
  - serve_log: Audit trail of every prompt delivery.
  - app_state: Key-value store for global counters (e.g., serve_counter).
"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Prompt(db.Model):
    """A single prompt scraped from Anthropic's Prompt Library."""

    __tablename__ = "prompts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    prompt_body = db.Column(db.Text, nullable=False)
    system_prompt = db.Column(db.Text, nullable=True, default="")
    category = db.Column(db.String(100), nullable=False, default="general")
    source_slug = db.Column(db.String(255), nullable=False, unique=True)
    source_url = db.Column(db.Text, nullable=False)
    scraped_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Serving state
    is_served = db.Column(db.Boolean, nullable=False, default=False, index=True)
    served_at = db.Column(db.DateTime(timezone=True))
    serve_order = db.Column(db.Integer)

    # Relationships
    serve_logs = db.relationship("ServeLog", backref="prompt", lazy="dynamic")

    def to_dict(self):
        """Serialize to JSON-friendly dict."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "prompt_body": self.prompt_body,
            "system_prompt": self.system_prompt or "",
            "category": self.category,
            "source_url": self.source_url,
            "serve_order": self.serve_order,
            "served_at": self.served_at.isoformat() if self.served_at else None,
        }

    def __repr__(self):
        return f"<Prompt {self.id}: {self.title}>"


class ServeLog(db.Model):
    """Audit log entry for each prompt delivery."""

    __tablename__ = "serve_log"

    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey("prompts.id"), nullable=False)
    served_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    client_ip = db.Column(db.String(45))  # IPv6 max length
    user_agent = db.Column(db.Text)

    def __repr__(self):
        return f"<ServeLog prompt={self.prompt_id} at={self.served_at}>"


class AppState(db.Model):
    """Key-value store for global application state."""

    __tablename__ = "app_state"

    key = db.Column(db.String(50), primary_key=True)
    value_int = db.Column(db.Integer, nullable=False, default=0)

    def __repr__(self):
        return f"<AppState {self.key}={self.value_int}>"
