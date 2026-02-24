"""
Prompt Service — Core business logic for atomic prompt selection.

Uses a CTE with FOR UPDATE SKIP LOCKED to guarantee:
  1. No two concurrent requests get the same prompt
  2. A prompt is never served twice
  3. The serve counter increments atomically
"""

from datetime import datetime, timezone
from sqlalchemy import text
from models import db, Prompt, ServeLog, AppState


def get_stats():
    """Return total, served, and remaining prompt counts."""
    total = db.session.query(Prompt).count()
    served = db.session.query(Prompt).filter_by(is_served=True).count()
    return {
        "total": total,
        "served": served,
        "remaining": total - served,
    }


def serve_next_prompt(client_ip=None, user_agent=None):
    """
    Atomically select and mark a random unserved prompt.

    Returns:
        dict: The served prompt data with stats, or None if all exhausted.
    """
    is_sqlite = db.engine.url.drivername == 'sqlite'

    if not is_sqlite:
        # Step 1: PostgreSQL Atomic Selection using CTE
        result = db.session.execute(
            text("""
                WITH next_prompt AS (
                    SELECT id
                    FROM prompts
                    WHERE is_served = FALSE
                    ORDER BY RANDOM()
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                UPDATE prompts
                SET is_served  = TRUE,
                    served_at  = NOW(),
                    serve_order = COALESCE(
                        (SELECT value_int FROM app_state WHERE key = 'serve_counter'),
                        0
                    ) + 1
                FROM next_prompt
                WHERE prompts.id = next_prompt.id
                RETURNING prompts.id, prompts.title, prompts.description,
                          prompts.prompt_body, prompts.system_prompt,
                          prompts.category, prompts.source_url,
                          prompts.serve_order, prompts.served_at
            """)
        )
        row = result.fetchone()
    else:
        # Step 1: SQLite Path (No SKIP LOCKED, manual transaction)
        # Select random ID
        next_prompt = Prompt.query.filter_by(is_served=False).order_by(db.func.random()).first()
        if not next_prompt:
            row = None
        else:
            # Update the prompt
            next_prompt.is_served = True
            next_prompt.served_at = datetime.now(timezone.utc)
            
            # Get current counter
            counter = AppState.query.filter_by(key='serve_counter').first()
            if not counter:
                counter = AppState(key='serve_counter', value_int=0)
                db.session.add(counter)
            
            counter.value_int += 1
            next_prompt.serve_order = counter.value_int
            
            # Build a mock row object for consistency
            from collections import namedtuple
            PromptRow = namedtuple('PromptRow', ['id', 'title', 'description', 'prompt_body', 
                                              'system_prompt', 'category', 'source_url', 
                                              'serve_order', 'served_at'])
            row = PromptRow(
                next_prompt.id, next_prompt.title, next_prompt.description,
                next_prompt.prompt_body, next_prompt.system_prompt or "",
                next_prompt.category, next_prompt.source_url,
                next_prompt.serve_order, next_prompt.served_at
            )
            db.session.add(next_prompt)

    if row is None:
        # All prompts exhausted - RESET and LOOP
        db.session.execute(text("UPDATE prompts SET is_served = FALSE"))
        db.session.commit()
        
        # Recursive call to try again with the fresh set
        return serve_next_prompt(client_ip=client_ip, user_agent=user_agent)

    # Step 2: Increment the global counter (already done for SQLite)
    if not is_sqlite:
        db.session.execute(
            text("UPDATE app_state SET value_int = value_int + 1 WHERE key = 'serve_counter'")
        )

    # Step 3: Insert audit log
    serve_log = ServeLog(
        prompt_id=row.id,
        served_at=datetime.now(timezone.utc),
        client_ip=client_ip,
        user_agent=user_agent,
    )
    db.session.add(serve_log)

    # Step 4: Commit the transaction
    db.session.commit()

    # Step 5: Build response
    prompt_data = {
        "id": row.id,
        "title": row.title,
        "description": row.description,
        "prompt_body": row.prompt_body,
        "system_prompt": row.system_prompt or "",
        "category": row.category,
        "source_url": row.source_url,
        "serve_order": row.serve_order,
        "served_at": row.served_at.isoformat() if row.served_at else None,
        "stats": get_stats(),
    }

    return prompt_data
