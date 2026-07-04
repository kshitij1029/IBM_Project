"""
services/weather_service.py
─────────────────────────────
Live weather via OpenWeatherMap (free tier).
Falls back to an AI-generated summary when the API key is absent.
"""

import logging
import requests

from config.settings import Config

logger = logging.getLogger(__name__)

OWM_BASE = "https://api.openweathermap.org/data/2.5"


def get_current_weather(city: str) -> dict:
    """
    Fetch current weather for *city*.
    Returns a dict with keys: city, temp_c, description, humidity, wind_kph, icon_url.
    Falls back to placeholder data when API key is missing.
    """
    if not Config.OPENWEATHER_API_KEY:
        return _placeholder_weather(city)

    try:
        url = f"{OWM_BASE}/weather"
        params = {
            "q": city,
            "appid": Config.OPENWEATHER_API_KEY,
            "units": "metric",
        }
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        return {
            "city": data.get("name", city),
            "temp_c": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "description": data["weather"][0]["description"].title(),
            "humidity": data["main"]["humidity"],
            "wind_kph": round(data["wind"]["speed"] * 3.6, 1),
            "icon_url": f"https://openweathermap.org/img/wn/{data['weather'][0]['icon']}@2x.png",
            "source": "live",
        }
    except Exception as exc:
        logger.warning("Weather API error for %s: %s", city, exc)
        return _placeholder_weather(city)


def _placeholder_weather(city: str) -> dict:
    """Return dummy weather data when API key is not configured."""
    return {
        "city": city,
        "temp_c": "--",
        "feels_like": "--",
        "description": "Configure OPENWEATHER_API_KEY in .env for live data",
        "humidity": "--",
        "wind_kph": "--",
        "icon_url": "",
        "source": "placeholder",
    }
