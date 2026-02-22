"""
Route: /health — Railway health check endpoint.
"""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Simple health check for Railway monitoring."""
    return jsonify({"status": "ok"}), 200
