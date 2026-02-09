# /src/backend/data/__init__.py
# Data module exports

from .loaders import (
    DataLoader,
    NPCConfig,
    DecisionConfig,
    get_npc,
    get_decision,
    get_scene_npcs,
    get_scene_decisions,
    get_dialogue_node,
    get_decision_choices,
)

__all__ = [
    "DataLoader",
    "NPCConfig",
    "DecisionConfig",
    "get_npc",
    "get_decision",
    "get_scene_npcs",
    "get_scene_decisions",
    "get_dialogue_node",
    "get_decision_choices",
]
