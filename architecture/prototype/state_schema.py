# /architecture/prototype/state_schema.py

from typing import TypedDict, List, Dict, Any, Optional, Literal
from dataclasses import dataclass
from enum import Enum

# ==================== Enums ====================

class SceneId(str, Enum):
    SCENE_0 = "scene-0-wuzhishan"
    SCENE_1 = "scene-1-chentangguan"
    SCENE_2 = "scene-2-tianhe"
    SCENE_3 = "scene-3-huaguoshan"
    SCENE_4 = "scene-4-lingtai"

class PhaseId(str, Enum):
    S1_PHASE_1 = "s1-phase-1-daily"
    S1_PHASE_2 = "s1-phase-2-crisis"
    S1_PHASE_3 = "s1-phase-3-confrontation"
    S1_PHASE_4 = "s1-phase-4-bone-cutting"
    S1_PHASE_5 = "s1-phase-5-aftermath"

class NPCLayer(str, Enum):
    ACTIVE = "active"
    BACKGROUND = "background"
    DORMANT = "dormant"

class InsightType(str, Enum):
    TRUE_PURPOSE = "true_purpose"
    BEHIND_DIALOGUE = "behind_dialogue"

class EmotionalTone(str, Enum):
    CALM = "calm"
    TENSE = "tense"
    ANGRY = "angry"
    SAD = "sad"
    HOPEFUL = "hopeful"
    FEARFUL = "fearful"

# ==================== Sub-state Types ====================

@dataclass
class Message:
    """对话消息"""
    speaker: str
    content: str
    tone: EmotionalTone
    timestamp: int

@dataclass
class ObservableOutput:
    """NPC 可观测输出 (传给其他 NPC/玩家)"""
    speaker: str
    speech_content: str
    tone: EmotionalTone
    volume: Literal["whisper", "normal", "loud"]
    speech_style_markers: List[str]
    actions: List[Dict[str, str]]
    expression: str
    tool_calls: List[Dict[str, Any]]
    end_interaction: bool

@dataclass
class HiddenIntent:
    """NPC 隐藏意图 (仅开发/debug/洞察揭示)"""
    speaker: str
    true_intent: str
    reasoning: List[str]
    counterpart_assessment: Dict[str, Any]
    info_strategy: Dict[str, List[str]]
    true_emotional_state: str
    next_move_plan: str

@dataclass
class NPCStateCard:
    """NPC 最小持久化单元"""
    npc_id: str
    name: str
    layer: NPCLayer
    location: str
    emotional_state: str
    disposition_toward_player: float
    active_goals: List[str]
    known_info_ids: List[str]
    relationships: Dict[str, Dict[str, Any]]
    memory_digest: str
    last_active_turn: int
    creation_type: Literal["predefined", "dynamic"]

@dataclass
class PlayerAction:
    """玩家行动记录"""
    turn: int
    action_type: Literal["dialogue", "decision", "insight", "move", "observe"]
    target: Optional[str]
    content: str
    outcome_summary: str

@dataclass
class Decision:
    """决策点"""
    decision_id: str
    phase_id: str
    description: str
    choices: List[Dict[str, Any]]
    deadline_turn: Optional[int]

@dataclass
class RevealEvent:
    """背后博弈展示事件"""
    event_type: Literal["variable_change", "npc_intent", "echo_preview", "behind_dialogue"]
    content: str
    priority: int

@dataclass
class InsightQuota:
    """洞察力配额"""
    true_purpose_remaining: int
    behind_dialogue_remaining: int

# ==================== Main GameState ====================

class GameState(TypedDict):
    # === Session Identity ===
    session_id: str
    created_at: str
    updated_at: str

    # === Scene Progression ===
    current_scene: SceneId
    current_phase: PhaseId
    completed_phases: List[PhaseId]
    turn_count: int

    # === Player State ===
    player_role: str
    player_insights: InsightQuota
    player_history: List[PlayerAction]
    faith_erosion_level: int
    belief_reconstruction: Optional[str]

    # === World State (38 Variables) ===
    variables: Dict[str, Any]

    # === Echo System (37 Echoes) ===
    echoes_triggered: List[str]
    echoes_pending: List[str]

    # === NPC Society ===
    npc_registry: Dict[str, NPCStateCard]
    active_npcs: List[str]
    background_npcs: List[str]

    # === Current Interaction ===
    current_npc: Optional[str]
    dialogue_context: List[Message]
    pending_decision: Optional[Decision]

    # === Turn Processing ===
    bfs_results: List[ObservableOutput]
    dfs_chain: List[ObservableOutput]
    gm_arbitration: Dict[str, Any]

    # === Behind-the-Scenes Queue ===
    behind_scenes_queue: List[RevealEvent]

    # === Insight Tracking ===
    insights_used_this_scene: List[Dict[str, Any]]
    hidden_layers_generated: Dict[str, HiddenIntent]

    # === System ===
    pending_propagations: List[Dict[str, Any]]
    error_count: int
    last_checkpoint: str
