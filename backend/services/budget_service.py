"""
services/budget_service.py
───────────────────────────
Client-side budget calculations that do NOT require an AI call.
For AI-generated narrative estimates, see watsonx_service.estimate_budget().
"""

from models.trip import BudgetBreakdown

# Rough per-person-per-day benchmarks in INR (2024)
_BENCHMARKS = {
    "budget": {
        "accommodation": 800,
        "transport_local": 300,
        "food": 500,
        "sightseeing": 300,
        "shopping": 200,
        "miscellaneous": 200,
    },
    "mid-range": {
        "accommodation": 3000,
        "transport_local": 700,
        "food": 1200,
        "sightseeing": 700,
        "shopping": 600,
        "miscellaneous": 500,
    },
    "luxury": {
        "accommodation": 10000,
        "transport_local": 2000,
        "food": 3500,
        "sightseeing": 2000,
        "shopping": 3000,
        "miscellaneous": 1500,
    },
}

# Rough round-trip domestic flight benchmark (INR, per person)
_FLIGHT_DOMESTIC = {"budget": 4000, "mid-range": 7000, "luxury": 15000}
# International multiplier
_FLIGHT_INTL_MULTIPLIER = 5


def estimate_budget(
    duration_days: int,
    travelers: int,
    travel_style: str,
    is_international: bool = False,
) -> BudgetBreakdown:
    """
    Return a BudgetBreakdown (all figures = total for all travelers combined).
    """
    style = travel_style if travel_style in _BENCHMARKS else "mid-range"
    bench = _BENCHMARKS[style]

    flight_pp = _FLIGHT_DOMESTIC.get(style, 7000)
    if is_international:
        flight_pp *= _FLIGHT_INTL_MULTIPLIER

    return BudgetBreakdown(
        accommodation=bench["accommodation"] * duration_days * travelers,
        transport=flight_pp * travelers + bench["transport_local"] * duration_days * travelers,
        food=bench["food"] * duration_days * travelers,
        sightseeing=bench["sightseeing"] * duration_days * travelers,
        shopping=bench["shopping"] * duration_days * travelers,
        miscellaneous=bench["miscellaneous"] * duration_days * travelers,
    )


def breakdown_to_dict(bb: BudgetBreakdown) -> dict:
    return {
        "accommodation": bb.accommodation,
        "transport": bb.transport,
        "food": bb.food,
        "sightseeing": bb.sightseeing,
        "shopping": bb.shopping,
        "miscellaneous": bb.miscellaneous,
        "total": bb.total,
    }
