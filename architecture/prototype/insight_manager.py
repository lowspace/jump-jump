# /architecture/prototype/insight_manager.py

from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass
from enum import Enum

class InsightType(str, Enum):
    TRUE_PURPOSE = "true_purpose"
    BEHIND_DIALOGUE = "behind_dialogue"

@dataclass
class InsightUsage:
    """洞察力使用记录"""
    turn: int
    insight_type: InsightType
    target: str
    query_content: str
    revealed_content: Dict[str, Any]

class InsightManager:
    """洞察力系统管理器"""

    DEFAULT_QUOTA = {
        InsightType.TRUE_PURPOSE: 2,
        InsightType.BEHIND_DIALOGUE: 2
    }

    def __init__(self):
        self.usage_history: List[InsightUsage] = []

    def initialize_scene(self, scene_id: str) -> Dict[str, int]:
        """新场景初始化配额"""
        return {
            "true_purpose_remaining": self.DEFAULT_QUOTA[InsightType.TRUE_PURPOSE],
            "behind_dialogue_remaining": self.DEFAULT_QUOTA[InsightType.BEHIND_DIALOGUE],
            "scene_id": scene_id,
            "used_in_this_scene": []
        }

    def consume_insight(
        self,
        state: Dict[str, Any],
        insight_type: InsightType,
        target: str,
        query_content: str
    ) -> Dict[str, Any]:
        """消耗洞察力并返回揭示内容"""
        quota = state["player_insights"]

        key = f"{insight_type.value}_remaining"
        if quota[key] <= 0:
            return {
                "success": False,
                "error": f"No remaining {insight_type.value} for this scene",
                "quota": quota
            }

        quota[key] -= 1

        if insight_type == InsightType.TRUE_PURPOSE:
            revealed = self._reveal_true_purpose(state, target)
        else:
            revealed = self._reveal_behind_dialogue(state, target)

        usage = InsightUsage(
            turn=state["turn_count"],
            insight_type=insight_type,
            target=target,
            query_content=query_content,
            revealed_content=revealed
        )
        self.usage_history.append(usage)
        quota["used_in_this_scene"].append(usage.__dict__)

        return {
            "success": True,
            "revealed": revealed,
            "quota_remaining": {
                "true_purpose": quota["true_purpose_remaining"],
                "behind_dialogue": quota["behind_dialogue_remaining"]
            }
        }

    def _reveal_true_purpose(self, state: Dict[str, Any], npc_id: str) -> Dict[str, Any]:
        """揭示「真实目的」"""
        hidden = state.get("hidden_layers_generated", {}).get(npc_id)

        if not hidden:
            return {"error": "No hidden intent recorded for this NPC"}

        return {
            "type": "true_purpose",
            "npc_id": npc_id,
            "npc_name": hidden.get("speaker", npc_id),
            "true_intent": hidden.get("true_intent"),
            "reasoning": hidden.get("reasoning", []),
            "info_strategy": hidden.get("info_strategy", {}),
            "true_emotional_state": hidden.get("true_emotional_state"),
            "next_move_plan": hidden.get("next_move_plan")
        }

    def _reveal_behind_dialogue(self, state: Dict[str, Any], query_id: str) -> Dict[str, Any]:
        """揭示「幕后对话」"""
        dfs_chain = state.get("dfs_chain", [])

        revealed_chain = []
        for interaction in dfs_chain:
            revealed_chain.append({
                "turn": interaction.get("turn"),
                "speaker": interaction.get("speaker"),
                "target": interaction.get("target"),
                "observable": interaction.get("observable"),
                "hidden": interaction.get("hidden"),
                "true_intent": interaction.get("hidden", {}).get("true_intent")
            })

        return {
            "type": "behind_dialogue",
            "query_id": query_id,
            "chain_length": len(revealed_chain),
            "interactions": revealed_chain
        }

    def generate_scene_debrief(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """场景结算信息博弈"""
        insights_used = state["player_insights"].get("used_in_this_scene", [])

        if len(insights_used) == 0:
            return {
                "debrief_type": "full",
                "message": "你在本场景中没有使用洞察力。现在揭示所有隐藏信息...",
                "all_hidden_intents": state.get("hidden_layers_generated", {}),
                "all_dfs_chains": self._format_dfs_chains(state)
            }
        else:
            return {
                "debrief_type": "partial",
                "message": f"你在本场景中使用了 {len(insights_used)} 次洞察力。完整回顾将在游戏结束后解锁。",
                "insights_used": insights_used,
                "hint": "某些真相只有在游戏结束时才能完全理解..."
            }

    def _format_dfs_chains(self, state: Dict[str, Any]) -> List[Dict]:
        """格式化 DFS 链"""
        return state.get("dfs_chain", [])

    def generate_final_review(self, all_sessions: List[Dict]) -> Dict[str, Any]:
        """游戏结束后的完整回顾"""
        review = {
            "total_insights_used": len(self.usage_history),
            "scene_reviews": []
        }

        for session in all_sessions:
            review["scene_reviews"].append({
                "scene_id": session["scene_id"],
                "all_hidden": session.get("hidden_layers_generated", {}),
                "all_dfs_chains": session.get("dfs_chains", [])
            })

        return review
