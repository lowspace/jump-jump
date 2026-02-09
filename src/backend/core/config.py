# /src/backend/core/config.py
# Configuration for Jump Jump backend

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class GameConfig:
    """Game configuration"""
    # NPC Limits
    MAX_ACTIVE_NPCS: int = 4
    MAX_BACKGROUND_NPCS: int = 10
    MAX_DFS_DEPTH: int = 3
    MAX_NPC_CALLS_PER_TURN: int = 12
    MAX_NPC_BACK_AND_FORTH: int = 2
    MAX_L2_BACKGROUND_LLM_PER_TURN: int = 2

    # Insight System
    INSIGHT_TRUE_PURPOSE_QUOTA: int = 2
    INSIGHT_BEHIND_DIALOGUE_QUOTA: int = 2

    # Session
    SESSION_TIMEOUT_MINUTES: int = 60
    AUTO_SAVE_INTERVAL: int = 5  # turns

@dataclass
class LLMConfig:
    """LLM configuration"""
    # Provider settings
    PROVIDER: str = "openai"  # openai, anthropic, local
    MODEL: str = "gpt-4"
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1000

    # API Keys (from environment)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    def __post_init__(self):
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

@dataclass
class DatabaseConfig:
    """Database configuration"""
    # SQLite for development
    DB_TYPE: str = "sqlite"
    DB_PATH: str = "./data/game_sessions.db"

    # For production (optional)
    POSTGRES_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None

@dataclass
class ServerConfig:
    """Server configuration"""
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    CORS_ORIGINS: list = None

    def __post_init__(self):
        if self.CORS_ORIGINS is None:
            self.CORS_ORIGINS = [
                "http://localhost:3000",
                "http://localhost:8080",
                "http://127.0.0.1:3000",
            ]

# Global config instances
game_config = GameConfig()
llm_config = LLMConfig()
db_config = DatabaseConfig()
server_config = ServerConfig()

# Scene order for progression
SCENE_ORDER = [
    "scene-0-wuzhishan",
    "scene-1-chentangguan",
    "scene-2-tianhe",
    "scene-3-huaguoshan",
    "scene-4-lingtai",
]

# Default initial variables
DEFAULT_VARIABLES = {
    # Scene 1 - Chentangguan
    "nezha_trust": 0,
    "knife_choice": None,
    "wushi_presence": None,
    "lijing_hesitation": "low",
    "armguard": None,
    "yangjian_triggered": False,

    # Scene 2 - Tianhe
    "ledger_choice": None,
    "tenpeng_last_words": False,
    "juanlian_suspicion": 0,
    "seventh_aperture_awareness": "none",
    "lingshan_secret": "none",
    "survival_method": None,

    # Scene 3 - Huaguoshan
    "peach_tree_fate": None,
    "monkey_unity": None,
    "wukong_stick": None,
    "zixia_encounter": False,
    "resistance_choice": None,
    "memory_kept": None,

    # Scene 4 - Lingtai
    "sutra_truth": None,
    "final_scroll": None,
    "tangseng_encounter": False,
    "huikong_relationship": "neutral",
    "faith_state": "firm",
    "pen_taken": None,

    # Scene 0 - Wuzhishan
    "wall_inscription": None,
    "mountain_voice": None,
    "final_act": None,
    "grandmother_stories": 0,
    "curiosity_level": "medium",
    "wukong_awareness": "none",

    # Cross-scene
    "philosophy_stance": [],
    "decision_duration": 0,
    "moral_consistency": 0.0,
    "info_exploration_rate": 0.0,
}
