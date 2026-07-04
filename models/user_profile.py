"""
models/user_profile.py
───────────────────────
Session-based user profile. No database required.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class UserProfile:
    session_id: str
    name: str = "Traveler"
    preferred_travel_style: str = "mid-range"   # budget / mid-range / luxury
    preferred_traveler_type: str = "solo"
    home_country: str = ""
    currency: str = "INR"
    favorite_destinations: List[str] = field(default_factory=list)
    saved_trip_ids: List[str] = field(default_factory=list)
    dietary_preferences: List[str] = field(default_factory=list)
    accessibility_needs: str = ""
    language: str = "English"
    interests: List[str] = field(default_factory=list)


@dataclass
class ConversationTurn:
    role: str       # "user" or "assistant"
    content: str
    timestamp: str = ""
