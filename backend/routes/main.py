"""
routes/main.py
───────────────
Dashboard, saved trips, profile, and misc pages.
"""

import json
import logging
from flask import Blueprint, render_template, session, request, jsonify, redirect, url_for
from utils.helpers import new_id, days_until, login_required
from routes.auth import update_user_profile

logger = logging.getLogger(__name__)
main_bp = Blueprint("main", __name__)


def _get_profile() -> dict:
    profile = session.get("profile", {})
    return {
        "name": profile.get("name") or session.get("user_name", "Traveler"),
        "email": profile.get("email") or session.get("user_email", ""),
        "travel_style": profile.get("travel_style", "mid-range"),
        "traveler_type": profile.get("traveler_type", "solo"),
        "home_country": profile.get("home_country", "India"),
        "currency": profile.get("currency", "INR"),
        "interests": profile.get("interests", []),
        "favorite_destinations": profile.get("favorite_destinations", []),
        "created_at": profile.get("created_at", ""),
        "last_login": profile.get("last_login", ""),
        "user_id": profile.get("user_id") or session.get("user_id", ""),
        "avatar": profile.get("avatar", ""),
        "bio": profile.get("bio", ""),
    }


def _save_profile(profile: dict):
    session["profile"] = profile
    session["user_name"] = profile.get("name", session.get("user_name", "Traveler"))
    session["user_email"] = profile.get("email", session.get("user_email", ""))
    session["user_initials"] = _initials(profile.get("name", "Traveler"))
    if session.get("user_email"):
        update_user_profile(session["user_email"], profile)
    session.modified = True


def _initials(name: str) -> str:
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "?"


@main_bp.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("main.index"))
    return render_template("landing.html", now=__import__("datetime").datetime.now(__import__("datetime").timezone.utc))


@main_bp.route("/dashboard")
@login_required
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
@login_required
def profile():
    if request.method == "POST":
        data = request.form
        p = _get_profile()
        p["name"] = (data.get("name", p["name"]) or "Traveler").strip()
        p["email"] = p.get("email") or session.get("user_email", "")
        p["travel_style"] = data.get("travel_style", p["travel_style"])
        p["traveler_type"] = data.get("traveler_type", p["traveler_type"])
        p["home_country"] = data.get("home_country", p["home_country"])
        p["currency"] = data.get("currency", p["currency"])
        p["avatar"] = data.get("avatar", p.get("avatar", ""))
        p["bio"] = data.get("bio", p.get("bio", ""))
        interests_raw = data.get("interests", "")
        p["interests"] = [i.strip() for i in interests_raw.split(",") if i.strip()]
        _save_profile(p)
        return redirect(url_for("main.profile"))
    return render_template("profile.html", profile=_get_profile())


@main_bp.route("/saved-trips")
@login_required
def saved_trips():
    trips = session.get("saved_trips", [])
    profile = _get_profile()
    return render_template("saved_trips.html", trips=trips[::-1], profile=profile)


@main_bp.route("/api/trip/save", methods=["POST"])
@login_required
def save_trip():
    data = request.get_json(silent=True) or {}
    trips = session.get("saved_trips", [])
    data["id"] = new_id()
    trips.append(data)
    session["saved_trips"] = trips
    session.modified = True
    return jsonify({"status": "ok", "id": data["id"]})


@main_bp.route("/api/trip/delete/<trip_id>", methods=["DELETE"])
@login_required
def delete_trip(trip_id: str):
    trips = session.get("saved_trips", [])
    session["saved_trips"] = [t for t in trips if t.get("id") != trip_id]
    session.modified = True
    return jsonify({"status": "ok"})


@main_bp.route("/api/trip/favorite/<trip_id>", methods=["POST"])
@login_required
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
