"""
routes/auth.py
───────────────
Authentication routes: login, register, logout.
Uses server-side session storage — no database required.
Passwords are hashed with werkzeug's pbkdf2-sha256.
"""

import logging
from datetime import datetime, timezone

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, jsonify, flash,
)
from werkzeug.security import generate_password_hash, check_password_hash

from utils.helpers import new_id

logger = logging.getLogger(__name__)
auth_bp = Blueprint("auth", __name__)

# ── In-memory user store (persists for process lifetime) ─────────────────────
# Structure: { email: { id, name, email, password_hash, created_at, last_login, ... } }
_users: dict[str, dict] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_user_by_email(email: str) -> dict | None:
    return _users.get(email.lower().strip())


def get_current_user() -> dict | None:
    email = session.get("user_email")
    if not email:
        return None
    return get_user_by_email(email)


def update_user_profile(email: str, profile_data: dict) -> dict | None:
    user = get_user_by_email(email)
    if not user:
        return None
    user.update({
        "name": profile_data.get("name", user.get("name", "Traveler")),
        "email": email,
        "travel_style": profile_data.get("travel_style", user.get("travel_style", "mid-range")),
        "traveler_type": profile_data.get("traveler_type", user.get("traveler_type", "solo")),
        "home_country": profile_data.get("home_country", user.get("home_country", "India")),
        "currency": profile_data.get("currency", user.get("currency", "INR")),
        "interests": profile_data.get("interests", user.get("interests", [])),
        "favorite_destinations": profile_data.get("favorite_destinations", user.get("favorite_destinations", [])),
        "avatar": profile_data.get("avatar", user.get("avatar", "")),
        "bio": profile_data.get("bio", user.get("bio", "")),
        "created_at": profile_data.get("created_at", user.get("created_at", _now_iso())),
        "last_login": profile_data.get("last_login", user.get("last_login", _now_iso())),
    })
    _users[email] = user
    return user


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _is_logged_in() -> bool:
    return bool(session.get("user_id"))


# ── Register ──────────────────────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Redirect already logged-in users to dashboard
    if _is_logged_in():
        return redirect(url_for("main.index"))

    if request.method == "GET":
        return render_template("register.html")

    data = request.get_json(silent=True) or {}
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    confirm  = data.get("confirm_password", "")

    # ── Validation ────────────────────────────────────────────────────────────
    errors: list[str] = []
    if not name:
        errors.append("Full name is required.")
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        errors.append("A valid email address is required.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one number.")
    if password != confirm:
        errors.append("Passwords do not match.")
    if get_user_by_email(email):
        errors.append("An account with this email already exists.")

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    # ── Create user ───────────────────────────────────────────────────────────
    user_id = new_id()
    now = _now_iso()
    user = {
        "id":            user_id,
        "name":          name,
        "email":         email,
        "password_hash": generate_password_hash(password),
        "created_at":    now,
        "last_login":    now,
        # default travel profile
        "travel_style":  "mid-range",
        "traveler_type": "solo",
        "home_country":  "India",
        "currency":      "INR",
        "interests":     [],
        "favorite_destinations": [],
    }
    _users[email] = user
    logger.info("New user registered: %s (%s)", name, email)

    # ── Auto-login after registration ─────────────────────────────────────────
    _start_session(user)
    return jsonify({"ok": True, "redirect": url_for("main.index")})


# ── Login ─────────────────────────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if _is_logged_in():
        return redirect(url_for("main.index"))

    if request.method == "GET":
        next_url = request.args.get("next", "")
        return render_template("login.html", next_url=next_url)

    data = request.get_json(silent=True) or {}
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    remember = data.get("remember", False)

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"ok": False, "errors": ["Invalid email or password."]}), 401

    # ── Update last login ────────────────────────────────────────────────────
    user["last_login"] = _now_iso()
    _start_session(user, permanent=remember)
    logger.info("User logged in: %s", email)
    next_url = data.get("next") or url_for("main.index")
    return jsonify({"ok": True, "redirect": next_url})


# ── Logout ────────────────────────────────────────────────────────────────────

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.landing"))


# ── Landing page ──────────────────────────────────────────────────────────────

@auth_bp.route("/landing")
def landing():
    if _is_logged_in():
        return redirect(url_for("main.index"))
    return render_template("landing.html", now=datetime.now(timezone.utc))


# ── Session helper ────────────────────────────────────────────────────────────

def _start_session(user: dict, permanent: bool = False):
    """Write auth data into the Flask session."""
    session.permanent = permanent
    session["user_id"]    = user["id"]
    session["user_name"]  = user["name"]
    session["user_email"] = user["email"]
    session["user_initials"] = _initials(user["name"])
    session["profile"] = {
        "name": user["name"],
        "email": user["email"],
        "travel_style": user.get("travel_style", "mid-range"),
        "traveler_type": user.get("traveler_type", "solo"),
        "home_country": user.get("home_country", "India"),
        "currency": user.get("currency", "INR"),
        "interests": user.get("interests", []),
        "favorite_destinations": user.get("favorite_destinations", []),
        "created_at": user.get("created_at", ""),
        "last_login": user.get("last_login", ""),
        "user_id": user["id"],
        "avatar": user.get("avatar", ""),
        "bio": user.get("bio", ""),
    }
    session.modified = True


def _initials(name: str) -> str:
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "?"
