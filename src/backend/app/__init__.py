# /src/backend/app/__init__.py
# App module exports

from .main import app
from .game_engine import game_engine, GameEngine
from .state_manager import state_manager, StateManager
from .insight_system import insight_system, InsightSystem, InsightType
from .behind_scenes_renderer import behind_scenes_renderer, BehindScenesRenderer, RevealEvent, RevealType
from .npc_agents import NPCAgent, NPCAgentPool, initialize_npcs_for_scene
from .ws_handler import ws_manager, WebSocketManager

__all__ = [
    "app",
    "game_engine",
    "GameEngine",
    "state_manager",
    "StateManager",
    "insight_system",
    "InsightSystem",
    "InsightType",
    "behind_scenes_renderer",
    "BehindScenesRenderer",
    "RevealEvent",
    "RevealType",
    "NPCAgent",
    "NPCAgentPool",
    "initialize_npcs_for_scene",
    "ws_manager",
    "WebSocketManager",
]
