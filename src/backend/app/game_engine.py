# /src/backend/app/game_engine.py
# Game Engine for Jump Jump - LangGraph-based game flow

from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
import asyncio

# LangGraph imports (commented out until installed)
# from langgraph.graph import StateGraph, END
# from langgraph.prebuilt import ToolExecutor

from ..core.state_schema import GameState, ActionType
from ..core.config import SCENE_ORDER, game_config
from ..data.loaders import (
    get_scene_npcs, get_scene_decisions,
    get_dialogue_node, get_decision_choices,
    DataLoader
)
from .state_manager import state_manager
from .insight_system import insight_system, InsightType
from .behind_scenes_renderer import behind_scenes_renderer, RevealEvent, RevealType
from .npc_agents import NPCAgentPool, initialize_npcs_for_scene


class GameEngine:
    """
    Game Engine - Core game logic and LangGraph workflow

    Implements the 5-phase NPC society simulation:
    - Phase 0: GM Evaluate
    - Phase 1: BFS (NPC parallel reaction)
    - Phase 2: GM Arbitrate
    - Phase 3: DFS (Recursive execution)
    - Phase 4: GM Finalize
    - Phase 5: NPC Layer Migration
    - Narrative Render
    """

    def __init__(self):
        self.state_manager = state_manager
        self.insight_system = insight_system
        self.behind_scenes = behind_scenes_renderer
        self.npc_pools: Dict[str, NPCAgentPool] = {}

    async def create_session(
        self,
        start_scene: str = "scene-0-wuzhishan",
        player_role: str = "少年樵夫"
    ) -> Dict[str, Any]:
        """Create a new game session"""
        session_id = self.state_manager.create_session(start_scene, player_role)
        state = self.state_manager.load_session(session_id)

        # Initialize NPCs for the scene
        self.npc_pools[session_id] = initialize_npcs_for_scene(start_scene)

        # Get opening narrative
        narrative = DataLoader.get_opening_narrative(start_scene)

        return {
            "session_id": session_id,
            "current_scene": start_scene,
            "current_phase": "opening",
            "narrative_text": narrative,
            "available_actions": self._get_available_actions(state),
            "insight_quota": {
                "true_purpose": 2,
                "behind_dialogue": 2
            },
            "player_state": {
                "role": player_role,
                "faith_erosion_level": 0
            }
        }

    async def process_action(
        self,
        session_id: str,
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process a player action"""
        # Load state
        state = self.state_manager.load_session(session_id)
        if not state:
            return {"error": "Session not found"}

        # Get or initialize NPC pool
        if session_id not in self.npc_pools:
            self.npc_pools[session_id] = initialize_npcs_for_scene(state["current_scene"])
        npc_pool = self.npc_pools[session_id]

        # Process based on action type
        action_type = action.get("action_type")

        if action_type == "dialogue":
            result = await self._process_dialogue(state, action, npc_pool)
        elif action_type == "decision":
            result = await self._process_decision(state, action)
        elif action_type == "insight":
            result = await self._process_insight(state, action)
        elif action_type == "move":
            result = await self._process_move(state, action)
        elif action_type == "observe":
            result = await self._process_observe(state, action)
        else:
            result = {"error": f"Unknown action type: {action_type}"}

        # Save state
        self.state_manager.save_session(state)

        return result

    async def _process_dialogue(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any],
        npc_pool: NPCAgentPool
    ) -> Dict[str, Any]:
        """Process dialogue action"""
        npc_id = action.get("target")
        content = action.get("content", "")

        if not npc_id:
            return {"error": "No target NPC specified"}

        # Get NPC response
        npc = npc_pool.get_or_load_npc(npc_id)
        if not npc:
            return {"error": f"NPC not found: {npc_id}"}

        # Generate response (simplified - would call LLM in production)
        context = {
            "variables": state["variables"],
            "current_dialogue_node": state.get("current_dialogue_context", [{}])[-1] if state.get("current_dialogue_context") else None
        }

        # For now, return a simple response
        npc_config = npc.config
        dialogue_nodes = npc_config.get("dialogue_nodes", [])

        if dialogue_nodes:
            node = dialogue_nodes[0]
            response_text = node.get("text", "...")
            options = node.get("player_options", [])
        else:
            response_text = f"{npc.name}看着你，没有说话。"
            options = []

        # Update state
        state["current_npc"] = npc_id
        state["dialogue_context"].append({
            "speaker": "player",
            "content": content,
            "turn": state["turn_count"]
        })
        state["dialogue_context"].append({
            "speaker": npc.name,
            "content": response_text,
            "turn": state["turn_count"]
        })

        # Record action
        self.state_manager.record_player_action(state, "dialogue", content, npc_id)

        # Advance turn
        self.state_manager.advance_turn(state)

        return {
            "narrative_text": response_text,
            "emotion_beat": npc.emotional_state,
            "turn_completed": True,
            "current_phase": state["current_phase"],
            "phase_changed": False,
            "available_actions": self._format_dialogue_options(options),
            "behind_scenes_reveals": [],
            "insight_quota_remaining": self.insight_system.get_quota_status(state),
            "pending_decision": None,
            "scene_complete": False,
            "scene_summary": None
        }

    async def _process_decision(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process decision action"""
        decision_id = action.get("decision_id")
        choice_id = action.get("choice_id")

        from ..data.loaders import get_decision
        decision = get_decision(decision_id)

        if not decision:
            return {"error": f"Decision not found: {decision_id}"}

        # Find the chosen option
        chosen_option = None
        for choice in decision.choices:
            if choice.get("id") == choice_id:
                chosen_option = choice
                break

        if not chosen_option:
            return {"error": f"Choice not found: {choice_id}"}

        # Apply effects
        variable_impact = chosen_option.get("variable_impact", {})
        for var_name, new_value in variable_impact.items():
            if isinstance(new_value, str) and new_value.startswith("+"):
                # Increment
                current = state["variables"].get(var_name, 0)
                delta = int(new_value[1:])
                new_value = current + delta
            elif isinstance(new_value, str) and new_value.startswith("-"):
                # Decrement
                current = state["variables"].get(var_name, 0)
                delta = int(new_value[1:])
                new_value = current - delta

            self.state_manager.update_variable(
                state, var_name, new_value,
                reason=f"Decision {decision_id}, choice {choice_id}"
            )

        # Generate narrative
        narrative = chosen_option.get("text", "你做出了选择。")
        if "narrative" in chosen_option:
            narrative = chosen_option["narrative"]

        # Check for echo preview
        echo_preview = chosen_option.get("echo_preview")
        behind_scenes = []
        if echo_preview:
            behind_scenes.append({
                "type": "echo_preview",
                "content": echo_preview
            })

        # Record action
        self.state_manager.record_player_action(
            state, "decision",
            f"{decision_id}: {choice_id}",
            decision_id
        )

        # Advance turn
        self.state_manager.advance_turn(state)

        # Check if scene should transition
        scene_complete = self._check_scene_complete(state)

        return {
            "narrative_text": narrative,
            "emotion_beat": "tense",
            "turn_completed": True,
            "current_phase": state["current_phase"],
            "phase_changed": False,
            "available_actions": self._get_available_actions(state),
            "behind_scenes_reveals": behind_scenes,
            "insight_quota_remaining": self.insight_system.get_quota_status(state),
            "pending_decision": None,
            "scene_complete": scene_complete,
            "scene_summary": None
        }

    async def _process_insight(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process insight usage"""
        insight_type = action.get("insight_type")
        target = action.get("target")

        result = self.insight_system.consume_insight(
            state, insight_type, target,
            query_content=action.get("query_content", "")
        )

        if not result["success"]:
            return {
                "error": result.get("error", "Insight usage failed"),
                "insight_quota_remaining": result.get("quota", {})
            }

        return {
            "narrative_text": "你使用了洞察力...",
            "revealed_content": result["revealed"],
            "insight_quota_remaining": result["quota_remaining"],
            "turn_completed": False
        }

    async def _process_move(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process move action"""
        destination = action.get("destination")

        # Record action
        self.state_manager.record_player_action(state, "move", f"Moved to {destination}")

        return {
            "narrative_text": f"你来到了{destination}。",
            "turn_completed": True,
            "available_actions": self._get_available_actions(state)
        }

    async def _process_observe(
        self,
        state: Dict[str, Any],
        action: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process observe action"""
        target = action.get("target", "周围")

        # Record action
        self.state_manager.record_player_action(state, "observe", f"Observed {target}")

        # Generate observation based on scene
        scene = state["current_scene"]
        observation = self._generate_observation(scene, target, state)

        return {
            "narrative_text": observation,
            "turn_completed": True,
            "available_actions": self._get_available_actions(state)
        }

    def _get_available_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available actions for current state"""
        actions = []
        scene = state["current_scene"]

        # Get scene NPCs
        npcs = get_scene_npcs(scene)
        for npc in npcs[:4]:  # Limit to 4 active NPCs
            actions.append({
                "type": "dialogue",
                "target": npc.npc_id,
                "description": f"与{npc.name}对话"
            })

        # Get scene decisions
        decisions = get_scene_decisions(scene)
        for decision in decisions[:3]:  # Limit to 3 decisions
            actions.append({
                "type": "decision",
                "target": decision.decision_id,
                "description": decision.decision_name
            })

        # Add observe
        actions.append({
            "type": "observe",
            "target": None,
            "description": "观察周围环境"
        })

        return actions

    def _format_dialogue_options(self, options: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format dialogue options for frontend"""
        return [
            {
                "type": "dialogue_option",
                "id": opt.get("id"),
                "text": opt.get("text"),
                "hidden": opt.get("hidden"),
                "insight_hint": opt.get("insight_hint")
            }
            for opt in options
        ]

    def _generate_observation(self, scene: str, target: str, state: Dict[str, Any]) -> str:
        """Generate observation text based on scene"""
        observations = {
            "scene-0-wuzhishan": {
                "周围": "五指山的风很大。烧焦的桃树残根在风中微微摇晃。",
                "石壁": "石壁上有四个模糊的字迹，被风雨侵蚀得只剩轮廓。",
                "山下": "山下传来极其微弱的气息，像是大地在呼吸。"
            },
            "scene-1-chentangguan": {
                "周围": "陈塘关的街道很安静。远处传来海浪的声音。",
                "总兵府": "总兵府的大门紧闭，门口站着两个士兵。",
                "海边": "海边的礁石上有一个人影，看起来像是哪吒。"
            },
            "scene-2-tianhe": {
                "周围": "天河的账目堆积如山。数字在账本上排列成整齐的行列。",
                "账目": "某些数字看起来不太对劲，但又说不上来哪里不对。",
                "窗外": "窗外的天河静静流淌，星辰在其中闪烁。"
            },
            "scene-3-huaguoshan": {
                "周围": "花果山的桃树在风中摇曳。猴子们在远处嬉戏。",
                "水帘洞": "水帘洞的瀑布依然飞流直下，但洞里已经空了。",
                "山顶": "山顶的石头在月光下泛着微光。"
            },
            "scene-4-lingtai": {
                "周围": "灵台方寸山的抄经房里，墨香弥漫。",
                "经卷": "经卷上的字迹清晰，但你总觉得哪里不对。",
                "窗外": "窗外的山景静谧，仿佛时间在这里停滞。"
            }
        }

        scene_obs = observations.get(scene, {})
        return scene_obs.get(target, "你仔细观察，但没有发现什么特别的东西。")

    def _check_scene_complete(self, state: Dict[str, Any]) -> bool:
        """Check if current scene is complete"""
        # Simple check: scene is complete after certain number of turns
        # In production, this would check for specific conditions
        return state["turn_count"] >= 20

    async def transition_to_scene(self, session_id: str, new_scene: str) -> Dict[str, Any]:
        """Transition to a new scene"""
        state = self.state_manager.load_session(session_id)
        if not state:
            return {"error": "Session not found"}

        # Perform transition
        self.state_manager.transition_scene(state, new_scene)

        # Reinitialize NPCs for new scene
        self.npc_pools[session_id] = initialize_npcs_for_scene(new_scene)

        # Get opening narrative
        narrative = DataLoader.get_opening_narrative(new_scene)

        # Save state
        self.state_manager.save_session(state)

        return {
            "session_id": session_id,
            "current_scene": new_scene,
            "current_phase": "opening",
            "narrative_text": narrative,
            "available_actions": self._get_available_actions(state),
            "insight_quota": {
                "true_purpose": 2,
                "behind_dialogue": 2
            },
            "scene_transition": True,
            "from_scene": state.get("previous_scene"),
            "to_scene": new_scene
        }

    async def get_game_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current game state"""
        state = self.state_manager.load_session(session_id)
        if not state:
            return None

        return {
            "session_id": state["session_id"],
            "current_scene": state["current_scene"],
            "current_phase": state["current_phase"],
            "turn_count": state["turn_count"],
            "player_role": state["player_role"],
            "faith_erosion_level": state["faith_erosion_level"],
            "insight_quota": self.insight_system.get_quota_status(state),
            "variables_snapshot": state["variables"],
            "echoes_triggered": state["echoes_triggered"],
            "active_npcs": state["active_npcs"],
            "current_dialogue_context": state["dialogue_context"][-5:] if state["dialogue_context"] else []
        }

    async def use_insight(
        self,
        session_id: str,
        insight_type: str,
        target: str
    ) -> Dict[str, Any]:
        """Use insight"""
        state = self.state_manager.load_session(session_id)
        if not state:
            return {"error": "Session not found"}

        result = self.insight_system.consume_insight(
            state, insight_type, target
        )

        if result["success"]:
            self.state_manager.save_session(state)

        return result


# Global instance
game_engine = GameEngine()
