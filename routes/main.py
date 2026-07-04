"""
routes/main.py
───────────────
Dashboard, saved trips, profile, and misc pages.
"""

import json
import logging
from flask import Blueprint, render_template, session, request, jsonify, redirect, url_for
from utils.helpers import new_id, days_until

logger = logging.getLogger(__name__)
main_bp = Blueprint("main", __name__)


def _get_profile() -> dict:
    return session.get("profile", {
        "name": "Traveler",
        "travel_style": "mid-range",
        "traveler_type": "solo",
        "home_country": "India",
        "currency": "INR",
        "interests": [],
        "favorite_destinations": [],
    })


def _save_profile(profile: dict):
    session["profile"] = profile
    session.modified = True


@main_bp.route("/")
def index():
    profile = _get_profile()
    saved_trips = session.get("saved_trips", [])
    recent_trips = saved_trips[-3:][::-1]
    return render_template(
        "index.html",
        profile=profile,
        recent_trips=recent_trips,
        saved_trips_count=len(saved_trips),
    )


@main_bp.route("/profile", methods=["GET", "POST"])
def profile():
    if request.method == "POST":
        data = request.form
        p = _get_profile()
        p["name"] = data.get("name", p["name"])
        p["travel_style"] = data.get("travel_style", p["travel_style"])
        p["traveler_type"] = data.get("traveler_type", p["traveler_type"])
        p["home_country"] = data.get("home_country", p["home_country"])
        p["currency"] = data.get("currency", p["currency"])
        interests_raw = data.get("interests", "")
        p["interests"] = [i.strip() for i in interests_raw.split(",") if i.strip()]
        _save_profile(p)
        return redirect(url_for("main.index"))
    return render_template("profile.html", profile=_get_profile())


@main_bp.route("/saved-trips")
def saved_trips():
    trips = session.get("saved_trips", [])
    profile = _get_profile()
    return render_template("saved_trips.html", trips=trips[::-1], profile=profile)


@main_bp.route("/api/trip/save", methods=["POST"])
def save_trip():
    data = request.get_json(silent=True) or {}
    trips = session.get("saved_trips", [])
    data["id"] = new_id()
    trips.append(data)
    session["saved_trips"] = trips
    session.modified = True
    return jsonify({"status": "ok", "id": data["id"]})


@main_bp.route("/api/trip/delete/<trip_id>", methods=["DELETE"])
def delete_trip(trip_id: str):
    trips = session.get("saved_trips", [])
    session["saved_trips"] = [t for t in trips if t.get("id") != trip_id]
    session.modified = True
    return jsonify({"status": "ok"})


@main_bp.route("/api/trip/favorite/<trip_id>", methods=["POST"])
def toggle_favorite(trip_id: str):
    trips = session.get("saved_trips", [])
    for t in trips:
        if t.get("id") == trip_id:
            t["is_favorite"] = not t.get("is_favorite", False)
    session["saved_trips"] = trips
    session.modified = True
    return jsonify({"status": "ok"})


@main_bp.route("/api/countdown/<start_date>")
def countdown(start_date: str):
    return jsonify({"days": days_until(start_date)})
