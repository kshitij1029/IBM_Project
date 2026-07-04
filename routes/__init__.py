"""
routes/__init__.py
"""
from .main import main_bp
from .chat import chat_bp
from .planner import planner_bp
from .destinations import destinations_bp
from .budget import budget_bp
from .auth import auth_bp

__all__ = ["main_bp", "chat_bp", "planner_bp", "destinations_bp", "budget_bp", "auth_bp"]
