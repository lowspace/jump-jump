# /src/backend/core/state_schema.py
# Game state schema for Jump Jump - based on architecture/prototype/state_schema.py

from typing import TypedDict, List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum

# ==================== Enums ====================

class SceneId(str, Enum):
    SCENE_0 = "scene-0-wuzhishan"
    SCENE_1 = "scene-1-chentangguan"
    SCENE_2 = "scene-2-tianhe"
    SCENE_3 = "scene-3-huaguoshan"
    SCENE_4 = "scene-4-lingtai"

class PhaseId(str, Enum):
    PHASE_0 = "phase-0-evaluate"
    PHASE_1 = "phase-1-bfs"
    PHASE_2 = "phase-2-arbitrate"
    PHASE_3 = "phase-3-dfs"
    PHASE_4 = "phase-4-finalize"
    PHASE_5 = "phase-5-migrate"
    NARRATIVE = "phase-narrative-render"

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
    GUARDED = "guarded"
    DEFIANT = "defiant"

class ActionType(str, Enum):
    DIALOGUE = "dialogue"
    DECISION = "decision"
    INSIGHT = "insight"
    MOVE = "move"
    OBSERVE = "observe"

# ==================== Sub-state Types ====================

@dataclass
class Message:
    """Dialogue message"""
    speaker: str
    content: str
    tone: EmotionalTone
    timestamp: int

@dataclass
class ObservableOutput:
    """NPC observable output (passed to other NPCs/player)"""
    speaker: str
    speech_content: str
    tone: EmotionalTone
    volume: Literal["whisper", "normal", "loud"] = "normal"
    speech_style_markers: List[str] = field(default_factory=list)
    actions: List[Dict[str, str]] = field(default_factory=list)
    expression: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    end_interaction: bool = False

@dataclass
class HiddenIntent:
    """NPC hidden intent (dev/debug/insight reveal only)"""
    speaker: str
    true_intent: str
    reasoning: List[str] = field(default_factory=list)
    counterpart_assessment: Dict[str, Any] = field(default_factory=dict)
    info_strategy: Dict[str, List[str]] = field(default_factory=dict)
    true_emotional_state: str = ""
    next_move_plan: str = ""

@dataclass
class NPCStateCard:
    """NPC minimal persistence unit"""
    npc_id: str
    name: str
    layer: NPCLayer
    location: str = ""
    emotional_state: str = ""
    disposition_toward_player: float = 0.0
    active_goals: List[str] = field(default_factory=list)
    known_info_ids: List[str] = field(default_factory=list)
    relationships: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    memory_digest: str = ""
    last_active_turn: int = 0
    creation_type: Literal["predefined", "dynamic"] = "predefined"

@dataclass
class PlayerAction:
    """Player action record"""
    turn: int
    action_type: ActionType
    target: Optional[str] = None
    content: str = ""
    outcome_summary: str = ""

@dataclass
class Decision:
    """Decision point"""
    decision_id: str
    phase_id: str
    description: str
    choices: List[Dict[str, Any]] = field(default_factory=list)
    deadline_turn: Optional[int] = None

@dataclass
class RevealEvent:
    """Behind-the-scenes reveal event"""
    event_type: Literal["variable_change", "npc_intent", "echo_preview", "behind_dialogue"]
    content: str
    priority: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class InsightQuota:
    """Insight quota"""
    true_purpose_remaining: int = 2
    behind_dialogue_remaining: int = 2

@dataclass
class InsightUsage:
    """Insight usage record"""
    turn: int
    insight_type: InsightType
    target: str
    query_content: str
    revealed_content: Dict[str, Any] = field(default_factory=dict)

# ==================== Main GameState ====================

class GameState(TypedDict):
    # === Session Identity ===
    session_id: str
    created_at: str
    updated_at: str

    # === Scene Progression ===
    current_scene: str
    current_phase: str
    completed_phases: List[str]
    turn_count: int

    # === Player State ===
    player_role: str
    player_insights: Dict[str, Any]
    player_history: List[Dict[str, Any]]
    faith_erosion_level: int
    belief_reconstruction: Optional[str]

    # === World State (38 Variables) ===
    variables: Dict[str, Any]

    # === Echo System (37 Echoes) ===
    echoes_triggered: List[str]
    echoes_pending: List[str]

    # === NPC Society ===
    npc_registry: Dict[str, Dict[str, Any]]
    active_npcs: List[str]
    background_npcs: List[str]

    # === Current Interaction ===
    current_npc: Optional[str]
    dialogue_context: List[Dict[str, Any]]
    pending_decision: Optional[Dict[str, Any]]

    # === Turn Processing ===
    bfs_results: List[Dict[str, Any]]
    dfs_chain: List[Dict[str, Any]]
    gm_arbitration: Dict[str, Any]

    # === Behind-the-Scenes Queue ===
    behind_scenes_queue: List[Dict[str, Any]]

    # === Insight Tracking ===
    insights_used_this_scene: List[Dict[str, Any]]
    hidden_layers_generated: Dict[str, Dict[str, Any]]

    # === System ===
    pending_propagations: List[Dict[str, Any]]
    error_count: int
    last_checkpoint: str

# ==================== Response Types ====================

@dataclass
class GameStartResponse:
    """Response for game start endpoint"""
    session_id: str
    current_scene: str
    current_phase: str
    narrative_text: str
    available_actions: List[Dict[str, Any]]
    insight_quota: Dict[str, int]
    player_state: Dict[str, Any]

@dataclass
class ActionResponse:
    """Response for player action"""
    narrative_text: str
    emotion_beat: str
    turn_completed: bool
    current_phase: str
    phase_changed: bool
    available_actions: List[Dict[str, Any]]
    behind_scenes_reveals: List[Dict[str, Any]]
    insight_quota_remaining: Dict[str, int]
    pending_decision: Optional[Dict[str, Any]]
    scene_complete: bool
    scene_summary: Optional[str]

@dataclass
class InsightResponse:
    """Response for insight usage"""
    success: bool
    revealed_content: Dict[str, Any]
    quota_remaining: Dict[str, int]
    error: Optional[str] = None
