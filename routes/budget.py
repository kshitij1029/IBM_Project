"""
routes/budget.py
──────────────────
Budget tracker and estimator routes.
"""

import logging
from flask import Blueprint, render_template, request, jsonify, session
from services.watsonx_service import estimate_budget as ai_estimate_budget
from services.budget_service import estimate_budget, breakdown_to_dict
from utils.helpers import sanitize_text

logger = logging.getLogger(__name__)
budget_bp = Blueprint("budget", __name__)


@budget_bp.route("/budget")
def budget():
    profile = session.get("profile", {})
    return render_template("budget.html", profile=profile)


@budget_bp.route("/api/budget/estimate", methods=["POST"])
def api_budget_estimate():
    """Fast client-side estimate (no AI call)."""
    data = request.get_json(silent=True) or {}
    duration_days = int(data.get("duration_days", 5))
    travelers = int(data.get("travelers", 1))
    travel_style = data.get("travel_style", "mid-range")
    is_international = bool(data.get("is_international", False))

    bb = estimate_budget(duration_days, travelers, travel_style, is_international)
    return jsonify(breakdown_to_dict(bb))


@budget_bp.route("/api/budget/ai-estimate", methods=["POST"])
def api_ai_budget_estimate():
    """AI-generated narrative budget estimate."""
    data = request.get_json(silent=True) or {}
    destination = sanitize_text(data.get("destination", ""))
    if not destination:
        return jsonify({"error": "Destination required"}), 400

    result = ai_estimate_budget(
        destination=destination,
        duration_days=int(data.get("duration_days", 5)),
        travelers=int(data.get("travelers", 1)),
        travel_style=data.get("travel_style", "mid-range"),
        traveler_type=data.get("traveler_type", "solo"),
    )
    return jsonify({"estimate": result})
