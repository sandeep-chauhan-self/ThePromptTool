"""Create prompts, serve_log, and app_state tables

Revision ID: 001
Revises: None
Create Date: 2026-02-22
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- prompts table ---
    op.create_table(
        "prompts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("prompt_body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False, server_default="general"),
        sa.Column("source_slug", sa.String(255), nullable=False, unique=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("is_served", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("served_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("serve_order", sa.Integer(), nullable=True),
    )

    # Partial index for fast unserved prompt queries
    op.create_index(
        "idx_prompts_unserved",
        "prompts",
        ["id"],
        postgresql_where=sa.text("is_served = FALSE"),
    )

    # --- serve_log table ---
    op.create_table(
        "serve_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("prompt_id", sa.Integer(), sa.ForeignKey("prompts.id"), nullable=False),
        sa.Column("served_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("client_ip", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
    )

    op.create_index("idx_serve_log_prompt", "serve_log", ["prompt_id"])
    op.create_index("idx_serve_log_time", "serve_log", ["served_at"])

    # --- app_state table ---
    op.create_table(
        "app_state",
        sa.Column("key", sa.String(50), primary_key=True),
        sa.Column("value_int", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )

    # Seed app_state
    op.execute("INSERT INTO app_state (key, value_int) VALUES ('serve_counter', 0)")
    op.execute("INSERT INTO app_state (key, value_int) VALUES ('total_prompts', 0)")


def downgrade() -> None:
    op.drop_table("serve_log")
    op.drop_table("prompts")
    op.drop_table("app_state")
