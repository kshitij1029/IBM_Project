"""
routes/chat.py
───────────────
AI Chat endpoint — maintains per-session conversation history.
"""

import logging
from flask import Blueprint, render_template, request, jsonify, session

from services.watsonx_service import chat
from utils.helpers import sanitize_text

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)

MAX_HISTORY = 20


def _get_history() -> list:
    return session.get("chat_history", [])


def _push_message(role: str, content: str):
    history = _get_history()
    history.append({"role": role, "content": content})
    # Keep only the last MAX_HISTORY turns
    session["chat_history"] = history[-MAX_HISTORY:]
    session.modified = True


@chat_bp.route("/chat")
def chat_page():
    profile = session.get("profile", {})
    history = _get_history()
    return render_template("chat.html", history=history, profile=profile)


@chat_bp.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_message = sanitize_text(data.get("message", ""))
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    history = _get_history()
    _push_message("user", user_message)

    response = chat(user_message, history)
    _push_message("assistant", response)

    return jsonify({"reply": response})


@chat_bp.route("/api/chat/clear", methods=["POST"])
def clear_chat():
    session["chat_history"] = []
    session.modified = True
    return jsonify({"status": "ok"})
