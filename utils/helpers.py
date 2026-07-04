"""
utils/helpers.py
─────────────────
Shared utility functions.
"""

import uuid
from functools import wraps
from datetime import datetime, timedelta
from flask import session, redirect, url_for, request


def new_id() -> str:
    """Return a short unique id."""
    return uuid.uuid4().hex[:12]


def date_range(start: str, days: int) -> list[str]:
    """Return a list of ISO date strings starting from *start* for *days* days."""
    try:
        base = datetime.strptime(start, "%Y-%m-%d")
        return [(base + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    except ValueError:
        return [start] + [""] * (days - 1)


def days_until(target_date: str) -> int:
    """Return the number of days until *target_date* (ISO format). Negative = past."""
    try:
        target = datetime.strptime(target_date, "%Y-%m-%d")
        return (target - datetime.now()).days
    except ValueError:
        return 0


def format_currency(amount: float, symbol: str = "₹") -> str:
    return f"{symbol}{amount:,.0f}"


def sanitize_text(text: str, max_length: int = 10000) -> str:
    """Basic sanitization — strip leading/trailing whitespace, cap length."""
    return text.strip()[:max_length]


def login_required(f):
    """Decorator: redirect unauthenticated users to /login."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated
