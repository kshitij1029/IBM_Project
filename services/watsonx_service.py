"""
services/watsonx_service.py
────────────────────────────
All IBM Watsonx.ai interactions are isolated here.
Every public function accepts plain Python types and returns plain strings,
keeping the rest of the app fully decoupled from the SDK.
"""

import logging
from typing import List, Dict

from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from config.settings import Config
from prompts.agent_instructions import SYSTEM_PROMPT, build_system_prompt

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
#  Config validation — fail fast with a clear message
# ──────────────────────────────────────────────────────────────────────────────
_CONFIG_ERROR: str | None = None

if not Config.IBM_API_KEY:
    _CONFIG_ERROR = (
        "IBM_API_KEY is missing. "
        "Create a .env file in the travel_agent/ folder and set IBM_API_KEY=<your key>."
    )
elif not Config.WATSONX_PROJECT_ID:
    _CONFIG_ERROR = (
        "WATSONX_PROJECT_ID is missing. "
        "Add WATSONX_PROJECT_ID=<your project id> to your .env file."
    )

if _CONFIG_ERROR:
    logger.warning("Watsonx configuration incomplete: %s", _CONFIG_ERROR)


# ──────────────────────────────────────────────────────────────────────────────
#  Singleton client / model initialisation
# ──────────────────────────────────────────────────────────────────────────────
_model: ModelInference | None = None


def _get_model() -> ModelInference:
    """Lazily initialise and cache the Watsonx model client."""
    global _model
    if _CONFIG_ERROR:
        raise RuntimeError(_CONFIG_ERROR)
    if _model is None:
        credentials = Credentials(
            api_key=Config.IBM_API_KEY,
            url=Config.WATSONX_URL,
        )
        # Chat API accepts max_tokens, temperature, top_p only
        params = {
            GenParams.MAX_NEW_TOKENS: Config.MAX_NEW_TOKENS,   # maps to max_tokens in chat
            GenParams.TEMPERATURE: Config.TEMPERATURE,
            GenParams.TOP_P: Config.TOP_P,
        }
        _model = ModelInference(
            model_id=Config.WATSONX_MODEL_ID,
            credentials=credentials,
            project_id=Config.WATSONX_PROJECT_ID,
            params=params,
        )
        logger.info("Watsonx ModelInference initialised | model=%s", Config.WATSONX_MODEL_ID)
    return _model


def _build_messages(system: str, history: List[Dict], user_message: str) -> List[Dict]:
    """Build a messages list for the chat API."""
    messages = [{"role": "system", "content": system}]
    for turn in history[-Config.MAX_CONVERSATION_HISTORY:]:
        role = turn.get("role", "user")
        content = turn.get("content", "")
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    return messages


def _generate(user_message: str, history: List[Dict] | None = None, system: str = SYSTEM_PROMPT) -> str:
    """Send a chat request to Watsonx and return the reply text."""
    try:
        model = _get_model()
        messages = _build_messages(system, history or [], user_message)
        response = model.chat(messages=messages)
        # chat() returns a dict; pull the assistant content out
        reply = response["choices"][0]["message"]["content"]
        return reply.strip() if reply else "I'm sorry, I couldn't generate a response. Please try again."
    except RuntimeError as exc:
        # Config error — surface the message directly
        logger.error("Watsonx config error: %s", exc)
        return f"⚙️ Configuration error: {exc}"
    except Exception as exc:
        logger.error("Watsonx generation error: %s", exc)
        # Surface the most useful part of the error, not the full SDK traceback
        msg = str(exc)
        if "project" in msg.lower() and "not_found" in msg.lower():
            return (
                "❌ Project ID not found on IBM Cloud. "
                "Please verify WATSONX_PROJECT_ID in your .env file matches "
                "an active Watsonx.ai project in your IBM Cloud account."
            )
        if "api_key" in msg.lower() or "apikey" in msg.lower() or "401" in msg:
            return (
                "❌ Invalid IBM API Key. "
                "Check that IBM_API_KEY in your .env file is correct and not expired."
            )
        if "inactive" in msg.lower() or "invalid_instance_status" in msg.lower():
            return (
                "❌ Your Watson Machine Learning service instance is Inactive. "
                "Go to IBM Cloud → Resource List → Watson Machine Learning → "
                "click your instance → click 'Activate' or upgrade your plan. "
                "Free Lite plans expire after 30 days of inactivity."
            )
        if "not supported" in msg.lower() and "model" in msg.lower():
            return (
                "❌ Model not available for your project. "
                "Update WATSONX_MODEL_ID in your .env file. "
                "Run find_project_id.py to see supported models for your project."
            )
        return f"❌ AI service error: {msg}"


# ──────────────────────────────────────────────────────────────────────────────
#  Public service functions
# ──────────────────────────────────────────────────────────────────────────────

def chat(user_message: str, history: List[Dict] | None = None) -> str:
    """General-purpose conversational turn."""
    return _generate(user_message, history=history or [])


def generate_itinerary(
    destination: str,
    duration_days: int,
    travel_style: str,
    traveler_type: str,
    interests: List[str],
    budget_inr: float,
) -> str:
    """Generate a structured day-by-day itinerary."""
    interests_str = ", ".join(interests) if interests else "general sightseeing"
    user_request = (
        f"Create a detailed {duration_days}-day travel itinerary for {destination}.\n"
        f"Travel style: {travel_style}\n"
        f"Traveler type: {traveler_type}\n"
        f"Interests: {interests_str}\n"
        f"MAXIMUM budget (must not be exceeded): ₹{budget_inr:,.0f}\n\n"
        f"IMPORTANT: The traveler has exactly ₹{budget_inr:,.0f} to spend. "
        "Every recommendation — accommodation, food, transport, activities — "
        "must fit within this budget. Do not suggest options that cost more. "
        "Format the itinerary day-by-day with Morning / Afternoon / Evening sections. "
        "Include attraction names, estimated visit durations, travel tips, and "
        "accommodation suggestions. End with a budget breakdown whose total does not exceed "
        f"₹{budget_inr:,.0f}."
    )
    return _generate(user_request)


def recommend_destinations(
    travel_style: str,
    traveler_type: str,
    duration_days: int,
    budget_inr: float,
    interests: List[str],
    home_country: str = "India",
) -> str:
    """Recommend top destinations matching the user's profile."""
    interests_str = ", ".join(interests) if interests else "adventure, culture"
    user_request = (
        f"Recommend 5 best travel destinations for the following traveler:\n"
        f"- Home country: {home_country}\n"
        f"- Travel style: {travel_style}\n"
        f"- Traveler type: {traveler_type}\n"
        f"- Trip duration: {duration_days} days\n"
        f"- Budget: ₹{budget_inr:,.0f}\n"
        f"- Interests: {interests_str}\n\n"
        "For each destination provide: name, country, why it matches, best months to visit, "
        "estimated cost per day, top 3 highlights, and visa requirements for Indian passport holders."
    )
    return _generate(user_request)


def estimate_budget(
    destination: str,
    duration_days: int,
    travelers: int,
    travel_style: str,
    traveler_type: str,
) -> str:
    """Generate a budget estimate with breakdown."""
    user_request = (
        f"Provide a detailed budget estimate for a trip to {destination}.\n"
        f"Duration: {duration_days} days | Travelers: {travelers} | "
        f"Style: {travel_style} | Type: {traveler_type}\n\n"
        "Break down the estimate into: Accommodation, Transport (flights + local), "
        "Food & Dining, Sightseeing & Activities, Shopping, Miscellaneous. "
        "Provide per-person costs and total costs in INR. "
        "Include budget-saving tips specific to this destination."
    )
    return _generate(user_request)


def get_travel_tips(destination: str, traveler_type: str, travel_month: str) -> str:
    """Return packing list, cultural tips, visa info, and travel advisories."""
    user_request = (
        f"Provide comprehensive travel tips for visiting {destination} in {travel_month}.\n"
        f"Traveler type: {traveler_type}\n\n"
        "Cover: 1) Packing checklist  2) Visa & entry requirements for Indian citizens  "
        "3) Local currency & payment  4) Cultural etiquette & dress code  "
        "5) Health & safety tips  6) Emergency contacts  7) Useful local phrases  "
        "8) Best local food to try  9) Transport tips  10) Hidden gems"
    )
    return _generate(user_request)


def generate_packing_list(
    destination: str,
    duration_days: int,
    activities: List[str],
    travel_month: str,
) -> str:
    """Generate a categorized packing checklist."""
    activities_str = ", ".join(activities) if activities else "sightseeing"
    user_request = (
        f"Create a detailed packing checklist for {destination} ({duration_days} days, {travel_month}).\n"
        f"Planned activities: {activities_str}\n\n"
        "Categorize into: Documents, Clothing, Footwear, Toiletries, Electronics, "
        "Medications, Money & Cards, Snacks, Miscellaneous. "
        "Mark items as ESSENTIAL or OPTIONAL."
    )
    return _generate(user_request)


def plan_family_trip(
    destination: str,
    duration_days: int,
    adults: int,
    children_ages: List[int],
    budget_inr: float,
) -> str:
    """Generate a family-friendly itinerary with child-specific activities."""
    ages_str = ", ".join(str(a) for a in children_ages) if children_ages else "none"
    user_request = (
        f"Plan a family trip to {destination} for {duration_days} days.\n"
        f"Adults: {adults} | Children ages: {ages_str} | Budget: ₹{budget_inr:,.0f}\n\n"
        "Include: family-friendly hotels, child-safe activities, kid-friendly restaurants, "
        "educational spots, rest breaks, stroller-accessibility notes, "
        "day-wise itinerary, and tips for traveling with children."
    )
    return _generate(user_request)


def get_weather_travel_info(destination: str, month: str) -> str:
    """Return seasonal weather summary and travel readiness for the destination."""
    user_request = (
        f"Describe the typical weather in {destination} during {month}. "
        "Include: temperature range, rainfall, humidity, weather-related travel risks, "
        "recommended clothing, and whether it is a good time to visit. "
        "Also mention the best and worst months to visit and why."
    )
    return _generate(user_request)
