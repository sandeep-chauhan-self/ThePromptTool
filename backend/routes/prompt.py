"""
Route: /api/prompt/daily — Serve the next unserved prompt.
Route: /api/stats — Return prompt statistics.
"""

from flask import Blueprint, jsonify, request
from services.prompt_service import serve_next_prompt, get_stats

prompt_bp = Blueprint("prompt", __name__)


@prompt_bp.route("/api/prompt/daily", methods=["GET"])
def daily_prompt():
    """
    GET /api/prompt/daily

    Atomically selects a random unserved prompt, marks it as served,
    and returns it. Returns 404 if all prompts are exhausted.
    """
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent", "")

    try:
        result = serve_next_prompt(client_ip=client_ip, user_agent=user_agent)
    except Exception as e:
        return jsonify({
            "error": "service_error",
            "message": "Failed to fetch prompt. Please try again.",
        }), 503

    if result is None:
        stats = get_stats()
        return jsonify({
            "error": "all_prompts_exhausted",
            "message": "Every prompt from Anthropic's library has been served. No more remain.",
            "stats": stats,
        }), 404

    return jsonify(result), 200


@prompt_bp.route("/api/stats", methods=["GET"])
def stats():
    """
    GET /api/stats

    Returns total, served, and remaining prompt counts.
    """
    try:
        return jsonify(get_stats()), 200
    except Exception as e:
        return jsonify({
            "error": "service_error",
            "message": "Failed to fetch stats.",
        }), 503


@prompt_bp.route("/api/prompt", methods=["POST"])
def create_prompt():
    """
    POST /api/prompt

    Accepts a custom user prompt and saves it to the database for future serving.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "invalid_request", "message": "No JSON payload provided"}), 400
        
    title = data.get("title", "").strip()
    prompt_body = data.get("prompt_body", "").strip()
    
    if not title or not prompt_body:
        return jsonify({"error": "validation_error", "message": "Title and Prompt Body are required"}), 400
        
    category = data.get("category", "custom").strip() or "custom"
    description = data.get("description", "").strip()
    
    # Import db and models
    from models import db, Prompt
    import uuid
    
    # Generate unique source_slug specifically for custom user prompts
    slug = f"user-custom-prompt-{uuid.uuid4().hex[:12]}"
    
    new_prompt = Prompt(
        title=title,
        description=description,
        prompt_body=prompt_body,
        category=category,
        source_slug=slug,
        source_url="user-submission"
    )
    
    try:
        db.session.add(new_prompt)
        db.session.commit()
        return jsonify({
            "message": "Prompt submitted successfully!",
            "id": new_prompt.id,
            "slug": new_prompt.source_slug
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "service_error",
            "message": "Failed to save prompt."
        }), 503
