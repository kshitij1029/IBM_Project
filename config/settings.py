"""
config/settings.py
──────────────────
Central configuration loader. Reads all settings from environment variables
(populated by .env via python-dotenv in app.py).
"""

import os


class Config:
    # ── Flask ──────────────────────────────────────────────────────────────
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    # ── IBM Watsonx.ai ─────────────────────────────────────────────────────
    IBM_API_KEY: str = os.getenv("IBM_API_KEY", "")
    WATSONX_PROJECT_ID: str = os.getenv("WATSONX_PROJECT_ID", "")
    WATSONX_URL: str = os.getenv("WATSONX_URL", "https://au-syd.ml.cloud.ibm.com")
    WATSONX_MODEL_ID: str = os.getenv("WATSONX_MODEL_ID", "meta-llama/llama-3-3-70b-instruct")

    # ── External APIs (placeholders) ───────────────────────────────────────
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")

    # ── Model Generation Parameters ────────────────────────────────────────
    MAX_NEW_TOKENS: int = 1024
    MIN_NEW_TOKENS: int = 50
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    TOP_K: int = 50
    REPETITION_PENALTY: float = 1.1

    # ── Session ────────────────────────────────────────────────────────────
    SESSION_TYPE: str = "filesystem"
    MAX_CONVERSATION_HISTORY: int = 20      # max turns to keep in memory
