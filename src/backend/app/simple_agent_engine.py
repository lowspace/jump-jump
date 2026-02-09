# /src/backend/app/simple_agent_engine.py
# Simplified Agent Engine - Implements BFS->Adjudicate->DFS workflow
# Without LLM, but with real information propagation between NPCs

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import random
import asyncio

try:
    from .npc_society import NPCSociety, initialize_scene_0_society, PrivacyLevel
except ImportError:
    # Allow direct import for CLI
    from npc_society import NPCSociety, initialize_scene_0_society, PrivacyLevel


class GamePhase(Enum):
    """Game phases in the agent workflow"""
    EVALUATE = "evaluate"       # GM evaluates player action
    BFS = "bfs"                 # Breadth-first: all affected NPCs react
    ADJUDICATE = "adjudicate"   # GM approves/rejects NPC tool calls
    DFS = "dfs"                 # Depth-first: NPCs talk to each other
    FINALIZE = "finalize"       # GM finalizes results
    NARRATIVE = "narrative"     # Generate player-facing narrative


@dataclass
class PlayerAction:
    """A player action in the game"""
    action_type: str  # dialogue, observe, decision, etc.
    target: Optional[str]  # NPC or object
    content: str
    turn: int


@dataclass
class NPCReaction:
    """An NPC's reaction to player action"""
    npc_id: str
    observable: str  # What player sees
    hidden_intent: str  # What NPC is really thinking
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class RoundResult:
    """Result of one game round"""
    phase_transitions: List[GamePhase]
    npc_reactions: List[NPCReaction]
    npc_npc_interactions: List[Dict[str, Any]]
    narrative_text: str
    behind_scenes: List[Dict[str, Any]]
    state_changes: Dict[str, Any]


class SimpleAgentEngine:
    """
    Simplified Agent Engine

    Implements the core agent architecture without LLM:
    1. BFS: All affected NPCs react to player action (in parallel)
    2. Adjudicate: Determine which NPCs want to talk to each other
    3. DFS: Execute NPC-NPC conversations (propagates information)
    4. Finalize: Update all states

    Key principle: Information actually flows between NPCs
    """

    def __init__(self):
        self.npc_society: Optional[NPCSociety] = None
        self.current_turn: int = 0
        self.scene: str = ""
        self.session_id: str = ""

    async def create_session(self, scene: str = "scene-0-wuzhishan") -> str:
        """Create a new game session"""
        import uuid
        self.session_id = str(uuid.uuid4())[:8]
        self.scene = scene
        self.current_turn = 0

        # Initialize NPC society for this scene
        if scene == "scene-0-wuzhishan":
            self.npc_society = initialize_scene_0_society()

        return self.session_id

    async def process_player_action(self, action: PlayerAction) -> RoundResult:
        """
        Main entry point - process one player action through the full workflow
        """
        self.current_turn += 1

        # Phase 0: EVALUATE - Determine what player did and who is affected
        affected_npcs = self._evaluate_action(action)

        # Phase 1: BFS - All affected NPCs react (parallel)
        npc_reactions = await self._bfs_reactions(action, affected_npcs)

        # Phase 2: ADJUDICATE - Determine NPC tool calls
        approved_interactions = self._adjudicate_interactions(npc_reactions)

        # Phase 3: DFS - Execute NPC-NPC conversations
        npc_npc_results = await self._dfs_conversations(approved_interactions)

        # Phase 4: FINALIZE - Update all states
        state_changes = self._finalize_round(action, npc_reactions, npc_npc_results)

        # Phase 5: NARRATIVE - Generate player-facing text
        narrative = self._generate_narrative(action, npc_reactions)

        # Phase 6: BEHIND SCENES - What info propagated
        behind_scenes = self._generate_behind_scenes(npc_npc_results)

        return RoundResult(
            phase_transitions=[
                GamePhase.EVALUATE,
                GamePhase.BFS,
                GamePhase.ADJUDICATE,
                GamePhase.DFS,
                GamePhase.FINALIZE,
                GamePhase.NARRATIVE
            ],
            npc_reactions=npc_reactions,
            npc_npc_interactions=npc_npc_results,
            narrative_text=narrative,
            behind_scenes=behind_scenes,
            state_changes=state_changes
        )

    # ============ Phase 0: EVALUATE ============

    def _evaluate_action(self, action: PlayerAction) -> List[str]:
        """
        Determine which NPCs are affected by player action

        Rules:
        - Direct target is always affected
        - Nearby NPCs may be affected ("隔墙有耳")
        - NPCs with high suspicion may be watching player
        """
        affected = set()

        if action.action_type == "dialogue" and action.target:
            # Direct target
            affected.add(action.target)

            # Check for "eavesdroppers" - other NPCs nearby
            if self.npc_society:
                for npc_id in self.npc_society.npcs.keys():
                    if npc_id != action.target:
                        npc = self.npc_society.npcs[npc_id]
                        # High suspicion NPCs might be watching
                        if npc.suspicion_toward_player > 0.5:
                            if random.random() < 0.4:  # 40% chance
                                affected.add(npc_id)
                                # They learn about this conversation
                                gossip_id = f"heard_convo_{self.current_turn}"
                                self.npc_society.add_info_to_npc(
                                    npc_id, gossip_id,
                                    f"看到玩家与{action.target}在说话",
                                    reliability=0.9, source="observation"
                                )

        elif action.action_type == "observe":
            # Observation affects no NPCs directly
            pass

        elif action.action_type == "decision":
            # Decisions may affect all NPCs who care about player
            if self.npc_society:
                for npc_id, npc in self.npc_society.npcs.items():
                    if npc.trust_toward_player > 0.3:
                        affected.add(npc_id)

        return list(affected)

    # ============ Phase 1: BFS (NPC Reactions) ============

    async def _bfs_reactions(self, action: PlayerAction,
                             affected_npcs: List[str]) -> List[NPCReaction]:
        """
        All affected NPCs react in parallel (simulated)

        Each NPC generates:
        1. Observable response (what player sees)
        2. Hidden intent (what they're really thinking)
        3. Tool calls (what they want to do - e.g., tell another NPC)
        """
        reactions = []

        for npc_id in affected_npcs:
            if npc_id not in self.npc_society.npcs:
                continue

            npc = self.npc_society.npcs[npc_id]

            # Generate reaction based on action type and NPC state
            reaction = self._generate_npc_reaction(npc_id, npc, action)
            reactions.append(reaction)

        return reactions

    def _generate_npc_reaction(self, npc_id: str, npc,
                               action: PlayerAction) -> NPCReaction:
        """Generate a single NPC's reaction"""

        observable = "..."
        hidden_intent = "..."
        tool_calls = []

        if action.action_type == "dialogue":
            # Check if this NPC is the target
            if action.target == npc_id:
                # Direct dialogue - generate response based on trust
                if npc.trust_toward_player > 0.6:
                    observable = self._get_friendly_response(npc_id, action)
                    hidden_intent = "玩家值得信任，我可以分享一些信息"
                elif npc.suspicion_toward_player > 0.5:
                    observable = self._get_guarded_response(npc_id, action)
                    hidden_intent = "这个孩子在试探什么？我要小心"
                else:
                    observable = self._get_neutral_response(npc_id, action)
                    hidden_intent = "还在观察这个少年"

                # NPC might want to share this conversation with others
                if npc.trust_toward_player > 0.7:
                    # Find someone to gossip to
                    for other_id in self.npc_society.npcs.keys():
                        if other_id != npc_id:
                            rel = npc.get_relationship(other_id)
                            if rel["trust"] > 0.5:
                                tool_calls.append({
                                    "tool": "gossip_about_player",
                                    "target": other_id,
                                    "params": {
                                        "observation": f"玩家问我关于'{action.content}'",
                                        "sentiment": "positive" if npc.trust_toward_player > 0.7 else "neutral"
                                    }
                                })
                                break  # Only gossip to one person per turn

            else:
                # This NPC overheard
                if npc.suspicion_toward_player > 0.6:
                    observable = self._get_overheard_response(npc_id, action)
                    hidden_intent = "他们在说什么秘密？我要留意"
                    # May want to investigate

        elif action.action_type == "observe":
            # Observation doesn't trigger NPC reactions directly
            pass

        return NPCReaction(
            npc_id=npc_id,
            observable=observable,
            hidden_intent=hidden_intent,
            tool_calls=tool_calls
        )

    def _get_friendly_response(self, npc_id: str, action: PlayerAction) -> str:
        """Get a friendly NPC response"""
        responses = {
            "grandmother_s0": [
                f"祖母慈祥地看着你：\"{action.content}？这倒是让我想起了一些事...\"",
                "祖母点点头：\"你果然是个聪明孩子。\"",
                "祖母压低声音：\"这事我只跟你说..."
            ],
            "traveler_s0": [
                f"行者眼中闪过一丝光芒：\"{action.content}...你问到了关键。\"",
                "行者环顾四周，确认无人偷听后才开口...",
                "行者微微一笑：\"看来这座山不止我一个在找答案。\""
            ]
        }
        return random.choice(responses.get(npc_id, ["..."]))

    def _get_guarded_response(self, npc_id: str, action: PlayerAction) -> str:
        """Get a guarded/suspicious NPC response"""
        responses = {
            "grandmother_s0": [
                "祖母皱了皱眉：\"你问这个做什么？\"",
                "祖母摇摇头：\"有些事不知道比较好。\"",
                "祖母看了看天色：\"时候不早了，你该回家了。\""
            ],
            "traveler_s0": [
                "行者警惕地打量着你：\"你为何对此感兴趣？\"",
                "行者转移了话题：\"这山上的风景不错，不是吗？\"",
                "行者沉默片刻，没有回答你的问题。"
            ]
        }
        return random.choice(responses.get(npc_id, ["..."]))

    def _get_neutral_response(self, npc_id: str, action: PlayerAction) -> str:
        """Get a neutral NPC response"""
        responses = {
            "grandmother_s0": [
                f"祖母想了想：\"{action.content}...我听说过一些。\"",
                "祖母看着远处的山：\"这山里的故事多着呢。\"",
                "祖母叹了口气：\"都是过去的事了。\""
            ],
            "traveler_s0": [
                "行者望向岩壁：\"这山比看上去要有故事得多。\"",
                "行者似乎在回忆什么：\"我也还在寻找答案。\"",
                "行者轻声说：\"有些真相，知道了未必是好事。\""
            ]
        }
        return random.choice(responses.get(npc_id, ["..."]))

    def _get_overheard_response(self, npc_id: str, action: PlayerAction) -> str:
        """Response when NPC overhears player talking to someone else"""
        return f"[远处]{self.npc_society.npcs[npc_id].name}似乎注意到了这边的对话。"

    # ============ Phase 2: ADJUDICATE ============

    def _adjudicate_interactions(self, npc_reactions: List[NPCReaction]) -> List[Dict[str, Any]]:
        """
        Review NPC tool calls and approve/reject them

        Rules:
        - NPCs can only call tools they have access to
        - Some calls may be rejected based on game state
        """
        approved = []

        for reaction in npc_reactions:
            for tool_call in reaction.tool_calls:
                # Simple adjudication - check if target exists
                if tool_call["tool"] == "gossip_about_player":
                    target = tool_call.get("target")
                    if target in self.npc_society.npcs:
                        approved.append({
                            "from": reaction.npc_id,
                            "to": target,
                            "tool": tool_call["tool"],
                            "params": tool_call["params"]
                        })

                elif tool_call["tool"] == "share_info":
                    # May be rejected if trust too low
                    approved.append({
                        "from": reaction.npc_id,
                        "tool": tool_call["tool"],
                        **tool_call.get("params", {})
                    })

        return approved

    # ============ Phase 3: DFS (NPC-NPC Conversations) ============

    async def _dfs_conversations(self, approved_interactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute approved NPC-NPC interactions

        This is where information actually propagates between NPCs
        """
        results = []

        for interaction in approved_interactions:
            tool = interaction.get("tool")

            if tool == "gossip_about_player":
                result = self.npc_society.tool_gossip_about_player(
                    interaction["from"],
                    interaction["to"],
                    interaction["params"]["observation"],
                    interaction["params"]["sentiment"]
                )
                results.append({
                    "type": "gossip",
                    "from": interaction["from"],
                    "to": interaction["to"],
                    "result": result
                })

            elif tool == "share_info":
                # Can trigger chain reactions
                pass

        # Also run background simulation for NPCs not directly involved
        background_results = await self.npc_society.run_background_simulation(
            num_interactions=random.randint(1, 2)
        )
        results.extend(background_results)

        return results

    # ============ Phase 4: FINALIZE ============

    def _finalize_round(self, action: PlayerAction,
                       npc_reactions: List[NPCReaction],
                       npc_npc_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update all game states after the round"""

        changes = {
            "turn": self.current_turn,
            "player_action": action.action_type,
            "npcs_affected": len(npc_reactions),
            "npc_interactions": len(npc_npc_results),
            "info_propagation": []
        }

        # Track what info moved where
        for result in npc_npc_results:
            if result.get("type") == "discuss":
                exchanges = result.get("result", {}).get("exchanges", [])
                for exchange in exchanges:
                    changes["info_propagation"].append(exchange)

        return changes

    # ============ Phase 5: NARRATIVE ============

    def _generate_narrative(self, action: PlayerAction,
                           npc_reactions: List[NPCReaction]) -> str:
        """Generate player-facing narrative"""

        # Find the primary reaction (target NPC)
        primary_reaction = None
        for r in npc_reactions:
            if r.npc_id == action.target:
                primary_reaction = r
                break

        if primary_reaction:
            return primary_reaction.observable

        return "你完成了行动。"

    # ============ Phase 6: BEHIND SCENES ============

    def _generate_behind_scenes(self, npc_npc_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate behind-the-scenes reveals for player"""

        reveals = []

        for result in npc_npc_results:
            if result.get("type") == "gossip":
                reveals.append({
                    "type": "npc_npc_communication",
                    "npcs": [result["from"], result["to"]],
                    "content": f"{result['from']}向{result['to']}谈论了玩家",
                    "hint": "使用'幕后对话'洞察力可以了解更多"
                })
            elif result.get("type") == "discuss":
                exchanges = result.get("result", {}).get("exchanges", [])
                if exchanges:
                    reveals.append({
                        "type": "info_exchange",
                        "npcs": result.get("between", []),
                        "content": f"NPC间交换了{len(exchanges)}条信息",
                        "hint": "这些信息可能改变NPC对世界的认知"
                    })

        return reveals

    # ============ Public API ============

    def get_npc_state(self, npc_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of an NPC"""
        if not self.npc_society or npc_id not in self.npc_society.npcs:
            return None

        npc = self.npc_society.npcs[npc_id]
        return {
            "npc_id": npc_id,
            "name": npc.name,
            "trust_toward_player": npc.trust_toward_player,
            "suspicion_toward_player": npc.suspicion_toward_player,
            "known_info_count": len(npc.known_info),
            "relationships": npc.relationships,
            "willing_to_share": npc.trust_toward_player > 0.5
        }

    def get_player_reputation_network(self) -> Dict[str, Any]:
        """Get how all NPCs view the player (for insight system)"""
        if not self.npc_society:
            return {}

        return {
            npc_id: {
                "name": npc.name,
                "trust": npc.trust_toward_player,
                "suspicion": npc.suspicion_toward_player,
                "what_they_know_about_player": [
                    info.content for info in npc.known_info.values()
                    if "gossip_player" in info.info_id
                ]
            }
            for npc_id, npc in self.npc_society.npcs.items()
        }

    def use_insight_behind_dialogue(self) -> Dict[str, Any]:
        """Use insight to see NPC-NPC communications"""
        if not self.npc_society:
            return {"error": "No society initialized"}

        # Get overhearable conversations
        conversations = self.npc_society.get_overhearable_conversations(insight_level="deep")

        if not conversations:
            return {
                "success": True,
                "revealed": "最近没有听到NPC间的对话",
                "hint": "继续游戏，NPC会在后台交流"
            }

        # Format for player
        reveals = []
        for conv in conversations[-3:]:  # Last 3 conversations
            if conv["type"] == "gossip_player":
                reveals.append(f"{conv['participants'][0]}对{conv['participants'][1]}说：{conv.get('observation', '...')}")
            elif conv["type"] == "discuss":
                reveals.append(f"{conv['participants'][0]}和{conv['participants'][1]}讨论了{conv.get('topic', '某些事')}")

        return {
            "success": True,
            "revealed": "\n".join(reveals),
            "conversations_revealed": len(reveals)
        }

    def get_info_propagation_map(self) -> Dict[str, Any]:
        """Get map of how information has spread"""
        if not self.npc_society:
            return {}

        propagation = {}
        for npc_id, npc in self.npc_society.npcs.items():
            propagation[npc_id] = {
                "name": npc.name,
                "knows": list(npc.known_info.keys()),
                "learned_from": {
                    info_id: info.shared_by
                    for info_id, info in npc.known_info.items()
                }
            }

        return propagation
