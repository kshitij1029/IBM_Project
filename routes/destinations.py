"""
routes/destinations.py
───────────────────────
Destination discovery and AI recommendations.
"""

import logging
from flask import Blueprint, render_template, request, jsonify, session
from services.watsonx_service import recommend_destinations, get_weather_travel_info
from utils.helpers import sanitize_text, login_required

logger = logging.getLogger(__name__)
destinations_bp = Blueprint("destinations", __name__)


@destinations_bp.route("/destinations")
@login_required
def destinations():
    profile = session.get("profile", {})
    return render_template("destinations.html", profile=profile)


@destinations_bp.route("/api/destinations/recommend", methods=["POST"])
def api_recommend():
    data = request.get_json(silent=True) or {}
    profile = session.get("profile", {})

    travel_style = data.get("travel_style") or profile.get("travel_style", "mid-range")
    traveler_type = data.get("traveler_type") or profile.get("traveler_type", "solo")
    duration_days = int(data.get("duration_days", 7))
    budget_inr = float(data.get("budget_inr", 50000))
    interests = data.get("interests") or profile.get("interests", ["adventure"])
    home_country = data.get("home_country") or profile.get("home_country", "India")

    result = recommend_destinations(
        travel_style=travel_style,
        traveler_type=traveler_type,
        duration_days=duration_days,
        budget_inr=budget_inr,
        interests=interests,
        home_country=home_country,
    )
    return jsonify({"recommendations": result})


@destinations_bp.route("/api/destinations/weather", methods=["POST"])
def api_weather_info():
    data = request.get_json(silent=True) or {}
    destination = sanitize_text(data.get("destination", ""))
    month = data.get("month", "January")
    if not destination:
        return jsonify({"error": "Destination required"}), 400
    info = get_weather_travel_info(destination, month)
    return jsonify({"weather_info": info})
