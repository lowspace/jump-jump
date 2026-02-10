# /src/backend/app/npc_agents.py
# NPC Agents for Jump Jump - NPC as Tool pattern with dual output

from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum
import uuid


class NPCLayer(str, Enum):
    ACTIVE = "active"
    BACKGROUND = "background"
    DORMANT = "dormant"


@dataclass
class ObservableOutput:
    """
    Observable output - what other NPCs and player can see/hear
    """
    speaker: str
    speech_content: str
    tone: str = "calm"
    volume: Literal["whisper", "normal", "loud"] = "normal"
    speech_style_markers: List[str] = field(default_factory=list)
    actions: List[Dict[str, str]] = field(default_factory=list)
    expression: str = ""
    end_interaction: bool = False


@dataclass
class HiddenIntent:
    """
    Hidden intent - only for dev/debug/insight reveal
    NEVER exposed to other NPCs
    """
    speaker: str
    true_intent: str
    reasoning: List[str] = field(default_factory=list)
    counterpart_assessment: Dict[str, Any] = field(default_factory=dict)
    info_strategy: Dict[str, List[str]] = field(default_factory=dict)
    true_emotional_state: str = ""
    next_move_plan: str = ""


@dataclass
class NPCResponse:
    """Complete NPC response with dual output"""
    observable: ObservableOutput
    hidden: HiddenIntent
    npc_id: str
    turn: int


class NPCAgent:
    """
    NPC Agent - implements NPC as Tool pattern

    Key principles:
    1. Dual output: Observable (public) + Hidden (private)
    2. Information isolation: Hidden layer never crosses NPC boundaries
    3. Structured communication: Only structured data passed between NPCs
    """

    def __init__(
        self,
        npc_id: str,
        name: str,
        scene: str,
        layer: NPCLayer = NPCLayer.ACTIVE,
        config: Optional[Dict[str, Any]] = None
    ):
        self.npc_id = npc_id
        self.name = name
        self.scene = scene
        self.layer = layer
        self.config = config or {}

        # State
        self.emotional_state = config.get("initial_state", {}).get("emotional_state", "calm")
        self.trust = config.get("initial_state", {}).get("trust", 0)
        self.disposition_toward_player = 0.0
        self.known_info_ids: List[str] = []
        self.relationships: Dict[str, Dict[str, Any]] = {}

        # Hidden intent from config
        self.hidden_intent_config = config.get("hidden_intent", {})

    async def process_input(
        self,
        player_input: str,
        context: Dict[str, Any],
        turn: int
    ) -> NPCResponse:
        """
        Process player input and generate dual output

        Args:
            player_input: What the player said/did
            context: Current game context (variables, history, etc.)
            turn: Current turn number

        Returns:
            NPCResponse with both observable and hidden output
        """
        # Get current dialogue node if available
        current_node = context.get("current_dialogue_node")

        # Generate observable output (what others can see)
        observable = await self._generate_observable(
            player_input, current_node, context
        )

        # Generate hidden intent (private)
        hidden = await self._generate_hidden(
            player_input, current_node, context
        )

        return NPCResponse(
            observable=observable,
            hidden=hidden,
            npc_id=self.npc_id,
            turn=turn
        )

    async def _generate_observable(
        self,
        player_input: str,
        current_node: Optional[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> ObservableOutput:
        """Generate observable output (public)"""

        if current_node:
            # Use configured dialogue node
            text = current_node.get("text", "...")
            tone = current_node.get("tone", self.emotional_state)
        else:
            # Generate based on NPC personality
            text = await self._generate_dialogue_text(player_input, context)
            tone = self.emotional_state

        return ObservableOutput(
            speaker=self.name,
            speech_content=text,
            tone=tone,
            volume="normal",
            speech_style_markers=self._get_speech_markers(),
            expression=self._get_expression(),
            end_interaction=current_node.get("next_node", "").startswith("END_") if current_node else False
        )

    async def _generate_hidden(
        self,
        player_input: str,
        current_node: Optional[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> HiddenIntent:
        """Generate hidden intent (private)"""

        # Use configured hidden intent
        core_intent = self.hidden_intent_config.get("core", "")

        # Adjust based on context
        reasoning = ["基于NPC配置的核心意图"]

        # Add context-specific reasoning
        if self.trust > 3:
            reasoning.append("对玩家有一定信任")
        elif self.trust < 1:
            reasoning.append("对玩家保持警惕")

        return HiddenIntent(
            speaker=self.name,
            true_intent=core_intent or "维持当前状态",
            reasoning=reasoning,
            counterpart_assessment={
                "player_trust_level": self.trust,
                "player_recent_action": player_input[:50] if player_input else "无"
            },
            info_strategy={
                "reveal": [],
                "conceal": ["true_intent"]
            },
            true_emotional_state=self.emotional_state,
            next_move_plan="根据玩家反应调整"
        )

    async def _generate_dialogue_text(
        self,
        player_input: str,
        context: Dict[str, Any]
    ) -> str:
        """Generate dialogue text when no node is configured"""
        # This would typically call an LLM
        # For now, return a placeholder
        return f"{self.name}看着你，似乎在思考什么。"

    def _get_speech_markers(self) -> List[str]:
        """Get speech style markers based on NPC personality"""
        markers = []

        # Add markers based on emotional state
        if self.emotional_state == "guarded":
            markers.append("简短")
            markers.append("保留")
        elif self.emotional_state == "angry":
            markers.append("急促")
            markers.append("尖锐")
        elif self.emotional_state == "sad":
            markers.append("缓慢")
            markers.append("低沉")

        return markers

    def _get_expression(self) -> str:
        """Get facial expression based on emotional state"""
        expressions = {
            "calm": "平静",
            "guarded": "警惕",
            "angry": "愤怒",
            "sad": "悲伤",
            "defiant": "挑衅",
            "hopeful": "期待",
            "fearful": "恐惧"
        }
        return expressions.get(self.emotional_state, "平静")

    def update_state(self, variable_changes: Dict[str, Any]):
        """Update NPC state based on variable changes"""
        if "trust" in variable_changes:
            self.trust = max(0, min(5, variable_changes["trust"]))
        if "emotional_state" in variable_changes:
            self.emotional_state = variable_changes["emotional_state"]
        if "disposition" in variable_changes:
            self.disposition_toward_player = variable_changes["disposition"]

    def to_state_card(self) -> Dict[str, Any]:
        """Convert to state card for persistence"""
        return {
            "npc_id": self.npc_id,
            "name": self.name,
            "layer": self.layer.value,
            "emotional_state": self.emotional_state,
            "trust": self.trust,
            "disposition_toward_player": self.disposition_toward_player,
            "known_info_ids": self.known_info_ids,
            "relationships": self.relationships
        }

    @classmethod
    def from_config(cls, npc_config) -> "NPCAgent":
        """Create NPCAgent from configuration"""
        return cls(
            npc_id=npc_config.npc_id,
            name=npc_config.name,
            scene=npc_config.scene,
            config=npc_config.raw_config
        )


class NPCAgentPool:
    """
    Pool of NPC agents with layer management

    - Active layer: Max 4 concurrent NPCs (L2 LLM)
    - Background layer: Max 10 NPCs (mixed L0/L1)
    - Dormant layer: State cards only
    """

    def __init__(self):
        self.active_npcs: Dict[str, NPCAgent] = {}
        self.background_npcs: Dict[str, NPCAgent] = {}
        self.dormant_cards: Dict[str, Dict[str, Any]] = {}

    def add_npc(self, npc: NPCAgent, layer: NPCLayer = NPCLayer.ACTIVE):
        """Add NPC to pool"""
        if layer == NPCLayer.ACTIVE:
            if len(self.active_npcs) >= 4:
                # Move oldest to background
                oldest_id = next(iter(self.active_npcs))
                self._move_to_background(oldest_id)
            self.active_npcs[npc.npc_id] = npc
            npc.layer = NPCLayer.ACTIVE

        elif layer == NPCLayer.BACKGROUND:
            if len(self.background_npcs) >= 10:
                # Move oldest to dormant
                oldest_id = next(iter(self.background_npcs))
                self._move_to_dormant(oldest_id)
            self.background_npcs[npc.npc_id] = npc
            npc.layer = NPCLayer.BACKGROUND

        else:  # DORMANT
            self.dormant_cards[npc.npc_id] = npc.to_state_card()

    def get_npc(self, npc_id: str) -> Optional[NPCAgent]:
        """Get NPC by ID"""
        if npc_id in self.active_npcs:
            return self.active_npcs[npc_id]
        if npc_id in self.background_npcs:
            return self.background_npcs[npc_id]
        return None

    def get_or_load_npc(self, npc_id: str) -> Optional[NPCAgent]:
        """Get NPC or load from dormant"""
        npc = self.get_npc(npc_id)
        if npc:
            return npc

        # Try to load from dormant
        if npc_id in self.dormant_cards:
            from ..data.loaders import get_npc as get_npc_config
            config = get_npc_config(npc_id)
            if config:
                npc = NPCAgent.from_config(config)
                npc.update_state(self.dormant_cards[npc_id])
                self.add_npc(npc, NPCLayer.BACKGROUND)
                return npc

        return None

    def activate_npc(self, npc_id: str) -> Optional[NPCAgent]:
        """Move NPC to active layer"""
        npc = self.get_or_load_npc(npc_id)
        if not npc:
            return None

        # Remove from current layer
        self.background_npcs.pop(npc_id, None)
        self.dormant_cards.pop(npc_id, None)

        # Add to active
        self.add_npc(npc, NPCLayer.ACTIVE)
        return npc

    def _move_to_background(self, npc_id: str):
        """Move NPC from active to background"""
        if npc_id in self.active_npcs:
            npc = self.active_npcs.pop(npc_id)
            self.add_npc(npc, NPCLayer.BACKGROUND)

    def _move_to_dormant(self, npc_id: str):
        """Move NPC from background to dormant"""
        if npc_id in self.background_npcs:
            npc = self.background_npcs.pop(npc_id)
            self.dormant_cards[npc_id] = npc.to_state_card()

    def get_active_npcs(self) -> List[NPCAgent]:
        """Get all active NPCs"""
        return list(self.active_npcs.values())

    def get_background_npcs(self) -> List[NPCAgent]:
        """Get all background NPCs"""
        return list(self.background_npcs.values())

    def process_player_input(
        self,
        player_input: str,
        target_npc_id: str,
        context: Dict[str, Any],
        turn: int
    ) -> Optional[NPCResponse]:
        """Process player input with target NPC"""
        npc = self.get_or_load_npc(target_npc_id)
        if not npc:
            return None

        # Ensure NPC is active
        if npc.npc_id not in self.active_npcs:
            self.activate_npc(npc.npc_id)

        # Process input
        import asyncio
        return asyncio.run(npc.process_input(player_input, context, turn))


# Global pool instance
npc_pool = NPCAgentPool()


def initialize_npcs_for_scene(scene_id: str) -> NPCAgentPool:
    """Initialize NPC pool for a scene"""
    from ..data.loaders import get_scene_npcs

    pool = NPCAgentPool()
    npc_configs = get_scene_npcs(scene_id)

    for config in npc_configs:
        npc = NPCAgent.from_config(config)
        # Determine initial layer based on NPC importance
        if config.npc_id in ["grandmother_s0", "traveler_s0", "nezha_s1", "lijing_s1", "tianpeng_s2", "laohou_s3", "huikong_s4"]:
            pool.add_npc(npc, NPCLayer.ACTIVE)
        else:
            pool.add_npc(npc, NPCLayer.BACKGROUND)

    return pool
