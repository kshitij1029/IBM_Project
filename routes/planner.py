"""
routes/planner.py
──────────────────
Trip planning routes: itinerary generation, packing list, family planner, PDF export.
"""

import json
import logging
from flask import Blueprint, render_template, request, jsonify, session, send_file
import io

from services.watsonx_service import (
    generate_itinerary,
    get_travel_tips,
    generate_packing_list,
    plan_family_trip,
)
from services.budget_service import estimate_budget, breakdown_to_dict
from utils.helpers import sanitize_text, new_id
from utils.pdf_export import generate_itinerary_pdf

logger = logging.getLogger(__name__)
planner_bp = Blueprint("planner", __name__)


@planner_bp.route("/planner")
def planner():
    profile = session.get("profile", {})
    return render_template("planner.html", profile=profile)


@planner_bp.route("/api/itinerary/generate", methods=["POST"])
def api_generate_itinerary():
    data = request.get_json(silent=True) or {}
    destination = sanitize_text(data.get("destination", ""))
    if not destination:
        return jsonify({"error": "Destination is required"}), 400

    duration_days = int(data.get("duration_days", 5))
    travel_style = data.get("travel_style", "mid-range")
    traveler_type = data.get("traveler_type", "solo")
    interests = data.get("interests", [])
    budget_inr = float(data.get("budget_inr", 50000))
    start_date = data.get("start_date", "")
    travelers = int(data.get("travelers", 1))

    # AI-generated itinerary text
    itinerary_text = generate_itinerary(
        destination=destination,
        duration_days=duration_days,
        travel_style=travel_style,
        traveler_type=traveler_type,
        interests=interests,
        budget_inr=budget_inr,
    )

    # Budget breakdown: split the user's entered budget proportionally
    # using the style ratios, capped to exactly budget_inr.
    is_international = data.get("is_international", False)
    bb = estimate_budget(duration_days, travelers, travel_style, is_international)
    raw_total = bb.total
    if raw_total > 0 and budget_inr > 0:
        scale = budget_inr / raw_total
        from models.trip import BudgetBreakdown
        bb = BudgetBreakdown(
            accommodation=round(bb.accommodation * scale),
            transport=round(bb.transport * scale),
            food=round(bb.food * scale),
            sightseeing=round(bb.sightseeing * scale),
            shopping=round(bb.shopping * scale),
            miscellaneous=round(bb.miscellaneous * scale),
        )
    budget_breakdown = breakdown_to_dict(bb)

    trip = {
        "id": new_id(),
        "destination": destination,
        "duration_days": duration_days,
        "travel_style": travel_style,
        "traveler_type": traveler_type,
        "travelers": travelers,
        "start_date": start_date,
        "budget_inr": budget_inr,
        "itinerary_text": itinerary_text,
        "budget_breakdown": budget_breakdown,
        "interests": interests,
    }

    # Cache the last generated trip for PDF export
    session["last_trip"] = trip
    session.modified = True

    return jsonify({"itinerary": itinerary_text, "budget_breakdown": budget_breakdown, "trip_id": trip["id"]})


@planner_bp.route("/api/itinerary/pdf", methods=["POST"])
def api_export_pdf():
    from datetime import date as _date
    data = request.get_json(silent=True) or {}
    # Fall back to the server-side cached trip when the client sends empty data
    if not data.get("itinerary_text"):
        data = session.get("last_trip", data)
    if not data:
        return jsonify({"error": "No trip data available. Please generate an itinerary first."}), 400
    pdf_bytes = generate_itinerary_pdf(data)
    if pdf_bytes is None:
        return jsonify({"error": "PDF generation failed. Please try again."}), 503
    dest = (data.get("destination") or "Trip").replace(" ", "_")
    today = _date.today().isoformat()
    filename = f"Trip_Report_{dest}_{today}.pdf"
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )


@planner_bp.route("/api/travel-tips", methods=["POST"])
def api_travel_tips():
    data = request.get_json(silent=True) or {}
    destination = sanitize_text(data.get("destination", ""))
    traveler_type = data.get("traveler_type", "solo")
    travel_month = data.get("travel_month", "January")
    if not destination:
        return jsonify({"error": "Destination is required"}), 400
    tips = get_travel_tips(destination, traveler_type, travel_month)
    return jsonify({"tips": tips})


@planner_bp.route("/api/packing-list", methods=["POST"])
def api_packing_list():
    data = request.get_json(silent=True) or {}
    destination = sanitize_text(data.get("destination", ""))
    duration_days = int(data.get("duration_days", 5))
    activities = data.get("activities", [])
    travel_month = data.get("travel_month", "January")
    if not destination:
        return jsonify({"error": "Destination required"}), 400
    checklist = generate_packing_list(destination, duration_days, activities, travel_month)
    return jsonify({"checklist": checklist})


@planner_bp.route("/api/family-trip", methods=["POST"])
def api_family_trip():
    data = request.get_json(silent=True) or {}
    destination = sanitize_text(data.get("destination", ""))
    duration_days = int(data.get("duration_days", 5))
    adults = int(data.get("adults", 2))
    children_ages = data.get("children_ages", [])
    budget_inr = float(data.get("budget_inr", 80000))
    if not destination:
        return jsonify({"error": "Destination required"}), 400
    result = plan_family_trip(destination, duration_days, adults, children_ages, budget_inr)
    return jsonify({"plan": result})
