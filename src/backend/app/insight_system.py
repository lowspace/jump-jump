# /src/backend/app/insight_system.py
# Insight System for Jump Jump - based on architecture/prototype/insight_manager.py

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class InsightType(str, Enum):
    TRUE_PURPOSE = "true_purpose"
    BEHIND_DIALOGUE = "behind_dialogue"


@dataclass
class InsightUsage:
    """Insight usage record"""
    turn: int
    insight_type: InsightType
    target: str
    query_content: str
    revealed_content: Dict[str, Any] = field(default_factory=dict)


class InsightSystem:
    """
    Insight System Manager

    Simplified version (no D20, no modifiers):
    - Fixed quota per scene: 2x "True Purpose" + 2x "Behind Dialogue"
    - Per-query consumption
    - Unused insights -> full scene debrief
    - Used insights -> full review only at game end
    """

    DEFAULT_QUOTA = {
        InsightType.TRUE_PURPOSE: 2,
        InsightType.BEHIND_DIALOGUE: 2
    }

    def __init__(self):
        self.usage_history: List[InsightUsage] = []

    def initialize_scene(self, scene_id: str) -> Dict[str, Any]:
        """Initialize quota for a new scene"""
        return {
            "true_purpose_remaining": self.DEFAULT_QUOTA[InsightType.TRUE_PURPOSE],
            "behind_dialogue_remaining": self.DEFAULT_QUOTA[InsightType.BEHIND_DIALOGUE],
            "scene_id": scene_id,
            "used_in_this_scene": []
        }

    def check_available_insights(
        self,
        state: Dict[str, Any],
        location_id: str
    ) -> List[Dict[str, Any]]:
        """Check what insights are available at current location"""
        quota = state.get("player_insights", {})
        available = []

        # Check for True Purpose availability
        if quota.get("true_purpose_remaining", 0) > 0:
            available.append({
                "type": "true_purpose",
                "cost": 1,
                "preview": "揭示NPC隐藏动机",
                "description": "揭示此NPC此刻的真实目的"
            })

        # Check for Behind Dialogue availability
        if quota.get("behind_dialogue_remaining", 0) > 0:
            available.append({
                "type": "behind_dialogue",
                "cost": 1,
                "preview": "揭示隐藏对话层",
                "description": "揭示幕后对话和隐藏信息"
            })

        return available

    def consume_insight(
        self,
        state: Dict[str, Any],
        insight_type_str: str,
        target: str,
        query_content: str = ""
    ) -> Dict[str, Any]:
        """Consume insight and return revealed content"""
        quota = state.get("player_insights", {})

        # Validate insight type
        try:
            insight_type = InsightType(insight_type_str)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid insight type: {insight_type_str}",
                "quota": quota
            }

        # Check quota
        key = f"{insight_type.value}_remaining"
        if quota.get(key, 0) <= 0:
            return {
                "success": False,
                "error": f"本场景已无剩余{self._get_type_name(insight_type)}",
                "quota": quota
            }

        # Deduct quota
        quota[key] = quota.get(key, 0) - 1

        # Generate revealed content
        if insight_type == InsightType.TRUE_PURPOSE:
            revealed = self._reveal_true_purpose(state, target)
        else:
            revealed = self._reveal_behind_dialogue(state, target)

        # Record usage
        usage = InsightUsage(
            turn=state.get("turn_count", 0),
            insight_type=insight_type,
            target=target,
            query_content=query_content,
            revealed_content=revealed
        )
        self.usage_history.append(usage)

        if "used_in_this_scene" not in quota:
            quota["used_in_this_scene"] = []
        quota["used_in_this_scene"].append({
            "turn": usage.turn,
            "type": insight_type.value,
            "target": target
        })

        return {
            "success": True,
            "revealed": revealed,
            "quota_remaining": {
                "true_purpose": quota.get("true_purpose_remaining", 0),
                "behind_dialogue": quota.get("behind_dialogue_remaining", 0)
            }
        }

    def _reveal_true_purpose(self, state: Dict[str, Any], npc_id: str) -> Dict[str, Any]:
        """Reveal "True Purpose" - NPC's hidden intent"""
        hidden = state.get("hidden_layers_generated", {}).get(npc_id)

        if not hidden:
            # Try to get from NPC config
            from ..data.loaders import get_npc
            npc = get_npc(npc_id)
            if npc and npc.hidden_intent:
                return {
                    "type": "true_purpose",
                    "npc_id": npc_id,
                    "npc_name": npc.name,
                    "true_intent": npc.hidden_intent.get("core", "未知"),
                    "surface_mask": npc.hidden_intent.get("surface_mask", ""),
                    "insight_reveal_text": npc.hidden_intent.get("insight_reveal_text", ""),
                    "reasoning": ["基于NPC配置文件"]
                }

            return {
                "type": "true_purpose",
                "npc_id": npc_id,
                "error": "该NPC暂无隐藏意图记录",
                "true_intent": "未知"
            }

        return {
            "type": "true_purpose",
            "npc_id": npc_id,
            "npc_name": hidden.get("speaker", npc_id),
            "true_intent": hidden.get("true_intent", "未知"),
            "reasoning": hidden.get("reasoning", []),
            "info_strategy": hidden.get("info_strategy", {}),
            "true_emotional_state": hidden.get("true_emotional_state", ""),
            "next_move_plan": hidden.get("next_move_plan", "")
        }

    def _reveal_behind_dialogue(self, state: Dict[str, Any], query_id: str) -> Dict[str, Any]:
        """Reveal "Behind Dialogue" - hidden layer of DFS chain"""
        dfs_chain = state.get("dfs_chain", [])

        revealed_chain = []
        for interaction in dfs_chain:
            revealed_chain.append({
                "turn": interaction.get("turn"),
                "speaker": interaction.get("speaker"),
                "target": interaction.get("target"),
                "observable": interaction.get("observable", {}),
                "hidden": interaction.get("hidden", {}),
                "true_intent": interaction.get("hidden", {}).get("true_intent", "")
            })

        return {
            "type": "behind_dialogue",
            "query_id": query_id,
            "chain_length": len(revealed_chain),
            "interactions": revealed_chain,
            "summary": f"揭示了{len(revealed_chain)}层幕后对话"
        }

    def generate_scene_debrief(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate scene debrief based on insight usage"""
        quota = state.get("player_insights", {})
        insights_used = quota.get("used_in_this_scene", [])

        if len(insights_used) == 0:
            # No insights used - full debrief
            return {
                "debrief_type": "full",
                "message": "你在本场景中没有使用洞察力。现在揭示所有隐藏信息...",
                "all_hidden_intents": state.get("hidden_layers_generated", {}),
                "all_dfs_chains": self._format_dfs_chains(state),
                "variable_changes": self._get_variable_changes(state)
            }
        else:
            # Insights used - partial debrief
            return {
                "debrief_type": "partial",
                "message": f"你在本场景中使用了 {len(insights_used)} 次洞察力。完整回顾将在游戏结束后解锁。",
                "insights_used": insights_used,
                "hint": "某些真相只有在游戏结束时才能完全理解..."
            }

    def generate_final_review(self, all_sessions: List[Dict]) -> Dict[str, Any]:
        """Generate final review after game completion"""
        review = {
            "total_insights_used": len(self.usage_history),
            "scene_reviews": []
        }

        for session in all_sessions:
            review["scene_reviews"].append({
                "scene_id": session.get("scene_id"),
                "all_hidden": session.get("hidden_layers_generated", {}),
                "all_dfs_chains": session.get("dfs_chains", [])
            })

        return review

    def _format_dfs_chains(self, state: Dict[str, Any]) -> List[Dict]:
        """Format DFS chains for display"""
        return state.get("dfs_chain", [])

    def _get_variable_changes(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get variable changes for debrief"""
        return state.get("variables", {})

    def _get_type_name(self, insight_type: InsightType) -> str:
        """Get Chinese name for insight type"""
        names = {
            InsightType.TRUE_PURPOSE: "真实目的",
            InsightType.BEHIND_DIALOGUE: "幕后对话"
        }
        return names.get(insight_type, insight_type.value)

    def get_quota_status(self, state: Dict[str, Any]) -> Dict[str, int]:
        """Get current quota status"""
        quota = state.get("player_insights", {})
        return {
            "true_purpose": quota.get("true_purpose_remaining", 0),
            "behind_dialogue": quota.get("behind_dialogue_remaining", 0)
        }


# Global instance
insight_system = InsightSystem()
