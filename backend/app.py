"""
Flask application entry point for Voyager.
Run from the repository root with: python app.py
Production: gunicorn app:app
"""

import os
import sys
import logging
from pathlib import Path

from flask import Flask
from flask_session import Session
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Keep the existing top-level package imports working after backend relocation.
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(PROJECT_ROOT / ".env")

from config.settings import Config
from routes import main_bp, chat_bp, planner_bp, destinations_bp, budget_bp, auth_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR / "templates"),
        static_folder=str(FRONTEND_DIR / "static"),
    )

    app.secret_key = Config.SECRET_KEY
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_FILE_DIR"] = str(PROJECT_ROOT / ".flask_sessions")
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True

    os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
    Session(app)

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
