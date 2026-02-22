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
