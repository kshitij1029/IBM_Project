"""
app.py
───────
Flask application entry point.
Run with:  python app.py
Production: gunicorn -w 4 -b 0.0.0.0:5000 app:app
"""

import os
import logging
from flask import Flask
from flask_session import Session
from dotenv import load_dotenv

# ── Load .env before importing config ─────────────────────────────────────────
load_dotenv()

from config.settings import Config
from routes import main_bp, chat_bp, planner_bp, destinations_bp, budget_bp, auth_bp

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # ── Config ─────────────────────────────────────────────────────────────────
    app.secret_key = Config.SECRET_KEY
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = os.path.join(os.path.dirname(__file__), ".flask_sessions")
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True

    # ── Server-side sessions ────────────────────────────────────────────────────
    os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
    Session(app)

    # ── Blueprints ──────────────────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(planner_bp)
    app.register_blueprint(destinations_bp)
    app.register_blueprint(budget_bp)

    logger.info("Voyager Travel Planner started | model=%s", Config.WATSONX_MODEL_ID)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=Config.DEBUG,
    )
