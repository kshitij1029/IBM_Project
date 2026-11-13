"""
models/trip.py
──────────────
Simple in-memory data models (dataclasses).
Swap these with SQLAlchemy models when adding a database.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict


@dataclass
class TripDay:
    day_number: int
    date: str
    morning: str = ""
    afternoon: str = ""
    evening: str = ""
    accommodation: str = ""
    notes: str = ""


@dataclass
class BudgetBreakdown:
    accommodation: float = 0.0
    transport: float = 0.0
    food: float = 0.0
    sightseeing: float = 0.0
    shopping: float = 0.0
    miscellaneous: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.accommodation
            + self.transport
            + self.food
            + self.sightseeing
            + self.shopping
            + self.miscellaneous
        )


@dataclass
class Trip:
    id: str
    destination: str
    start_date: str
    end_date: str
    duration_days: int
    travel_style: str          # budget / mid-range / luxury
    travelers: int = 1
    traveler_type: str = "solo"  # solo / couple / family / group
    budget_inr: float = 0.0
    itinerary: List[TripDay] = field(default_factory=list)
    budget_breakdown: Optional[BudgetBreakdown] = None
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    is_favorite: bool = False


@dataclass
class Destination:
    name: str
    country: str
    region: str
    travel_styles: List[str]
    best_months: List[str]
    avg_budget_per_day_inr: Dict[str, float]   # {"budget": x, "mid": y, "luxury": z}
    highlights: List[str]
    description: str = ""
    visa_required: bool = False
    language: str = ""
    currency: str = ""
    time_zone: str = ""
