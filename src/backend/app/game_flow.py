# /src/backend/app/game_flow.py
# Complete Game Flow System - Goals, Decisions, Time Limits, Insights

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import random


class GamePhase(Enum):
    EXPLORATION = "exploration"  # 自由探索/对话
    DECISION = "decision"        # 关键决策点
    TRANSITION = "transition"    # 场景过渡
    ENDING = "ending"            # 结局


@dataclass
class SceneGoal:
    """场景目标"""
    goal_id: str
    description: str
    required_info: List[str] = field(default_factory=list)  # 需要收集的信息
    required_trust: Dict[str, float] = field(default_factory=dict)  # 需要的信任度
    min_insights_used: int = 0  # 最少使用洞察力次数
    max_turns: int = 20  # 最大回合数

    def check_completion(self, game_state: Dict) -> bool:
        """检查目标是否完成"""
        # 检查信息收集
        collected = game_state.get("collected_info", [])
        for info_id in self.required_info:
            if info_id not in collected:
                return False

        # 检查信任度
        trust_levels = game_state.get("trust_levels", {})
        for npc_id, required_trust in self.required_trust.items():
            if trust_levels.get(npc_id, 0) < required_trust:
                return False

        # 检查洞察力使用
        insights_used = game_state.get("insights_used", 0)
        if insights_used < self.min_insights_used:
            return False

        return True


@dataclass
class DecisionPoint:
    """决策点"""
    decision_id: str
    title: str
    description: str
    choices: List[Dict[str, Any]]  # [{"id": "choice_a", "text": "...", "effects": {...}}]
    condition: Optional[Callable] = None  # 触发条件


@dataclass
class GameEvent:
    """游戏事件"""
    event_id: str
    trigger_type: str  # "turn", "trust", "info", "insight"
    trigger_condition: Dict[str, Any]
    content: str
    effects: Dict[str, Any]


class GameFlowManager:
    """
    游戏流程管理器

    整合：目标驱动 + 决策点 + 回合限制 + 洞察力系统
    """

    def __init__(self):
        self.current_scene: str = "scene-0-wuzhishan"
        self.current_phase: GamePhase = GamePhase.EXPLORATION
        self.turn_count: int = 0
        self.max_turns_per_scene: int = 20

        # 游戏状态
        self.state = {
            "collected_info": [],
            "trust_levels": {},
            "insights_used": 0,
            "decisions_made": [],
            "events_triggered": [],
            "secrets_unlocked": [],
        }

        # 场景定义
        self.scenes = self._define_scenes()
        self.current_goals: List[SceneGoal] = []
        self.pending_decisions: List[DecisionPoint] = []

    def _define_scenes(self) -> Dict[str, Dict]:
        """定义所有场景"""
        return {
            "scene-0-wuzhishan": {
                "name": "五指山·尘埃",
                "description": "序章：少年樵夫在五指山的日常",
                "goals": [
                    SceneGoal(
                        goal_id="s0_learn_family_secret",
                        description="从祖母处了解家族秘密",
                        required_info=["story_nezha"],
                        required_trust={"grandmother_s0": 0.7},
                        max_turns=15
                    ),
                    SceneGoal(
                        goal_id="s0_meet_traveler",
                        description="与行者建立初步联系",
                        required_trust={"traveler_s0": 0.5},
                        max_turns=15
                    ),
                ],
                "decisions": [
                    DecisionPoint(
                        decision_id="s0_final_choice",
                        title="最后的选择",
                        description="黄昏将至，你需要做出一个决定...",
                        choices=[
                            {
                                "id": "tell_grandma",
                                "text": "告诉祖母今天见到的一切",
                                "effects": {"grandmother_s0_trust": 0.2, "collected_info": ["family_bond"]}
                            },
                            {
                                "id": "keep_secret",
                                "text": "将秘密埋在心底",
                                "effects": {"insight": 1, "collected_info": ["burden_of_knowledge"]}
                            },
                            {
                                "id": "follow_traveler",
                                "text": "悄悄跟上那个行者",
                                "effects": {"traveler_s0_trust": 0.3, "collected_info": ["curiosity"]}
                            }
                        ]
                    )
                ],
                "events": [
                    GameEvent(
                        event_id="s0_wukong_whisper",
                        trigger_type="insight",
                        trigger_condition={"min_insights": 1},
                        content="你似乎听到山体深处传来一声叹息...",
                        effects={"unlock_wukong": True}
                    ),
                    GameEvent(
                        event_id="s0_heaven_watching",
                        trigger_type="trust",
                        trigger_condition={"traveler_s0": 0.6},
                        content="行者悄悄告诉你：天庭的人可能在监视这座山...",
                        effects={"collected_info": ["heaven_secret"]}
                    ),
                ]
            },
            "scene-1-chentangguan": {
                "name": "陈塘关",
                "description": "第一章：哪吒的抉择",
                "goals": [
                    SceneGoal(
                        goal_id="s1_understand_nezha",
                        description="理解哪吒剔骨的真正原因",
                        required_info=["nezha_truth", "lijing_pressure"],
                        max_turns=20
                    ),
                ],
            }
        }

    def start_scene(self, scene_id: str) -> Dict[str, Any]:
        """开始新场景"""
        self.current_scene = scene_id
        self.current_phase = GamePhase.EXPLORATION
        self.turn_count = 0

        scene_data = self.scenes.get(scene_id, {})
        self.current_goals = scene_data.get("goals", [])

        return {
            "scene_id": scene_id,
            "name": scene_data.get("name"),
            "description": scene_data.get("description"),
            "goals": [g.description for g in self.current_goals],
            "phase": self.current_phase.value,
            "turns_remaining": self.max_turns_per_scene
        }

    def process_turn(self, action_type: str, action_data: Dict) -> Dict[str, Any]:
        """处理一个回合"""
        self.turn_count += 1

        results = {
            "turn": self.turn_count,
            "phase": self.current_phase.value,
            "events": [],
            "goal_progress": [],
            "scene_complete": False,
            "show_decision": False,
        }

        # 检查回合限制
        if self.turn_count >= self.max_turns_per_scene:
            results["warning"] = "回合即将用尽，需要尽快做出决定"

        # 更新状态（从action_data中提取）
        if "collected_info" in action_data:
            self.state["collected_info"].extend(action_data["collected_info"])
        if "trust_change" in action_data:
            npc_id = action_data.get("npc_id")
            if npc_id:
                current_trust = self.state["trust_levels"].get(npc_id, 0.5)
                self.state["trust_levels"][npc_id] = max(0, min(1,
                    current_trust + action_data["trust_change"]))
        if "insight_used" in action_data:
            self.state["insights_used"] += 1

        # 检查事件触发
        triggered_events = self._check_events()
        results["events"].extend(triggered_events)

        # 检查目标进度
        goal_progress = self._check_goals()
        results["goal_progress"] = goal_progress

        # 检查是否进入决策点
        if self._should_trigger_decision():
            self.current_phase = GamePhase.DECISION
            results["show_decision"] = True
            results["decision"] = self._get_next_decision()

        # 检查场景完成
        if self._check_scene_complete():
            results["scene_complete"] = True
            results["completion_reason"] = self._get_completion_reason()

        results["state"] = self._get_public_state()
        return results

    def _check_events(self) -> List[Dict]:
        """检查并触发事件"""
        triggered = []
        scene_data = self.scenes.get(self.current_scene, {})

        for event in scene_data.get("events", []):
            if event.event_id in self.state["events_triggered"]:
                continue

            # 检查触发条件
            should_trigger = False

            if event.trigger_type == "insight":
                min_insights = event.trigger_condition.get("min_insights", 0)
                if self.state["insights_used"] >= min_insights:
                    should_trigger = True

            elif event.trigger_type == "trust":
                for npc_id, required_trust in event.trigger_condition.items():
                    if self.state["trust_levels"].get(npc_id, 0) >= required_trust:
                        should_trigger = True
                        break

            elif event.trigger_type == "turn":
                target_turn = event.trigger_condition.get("turn", 0)
                if self.turn_count >= target_turn:
                    should_trigger = True

            if should_trigger:
                self.state["events_triggered"].append(event.event_id)
                triggered.append({
                    "event_id": event.event_id,
                    "content": event.content,
                    "effects": event.effects
                })
                # 应用效果
                self._apply_effects(event.effects)

        return triggered

    def _check_goals(self) -> List[Dict]:
        """检查目标进度"""
        progress = []
        for goal in self.current_goals:
            completed = goal.check_completion(self.state)
            progress.append({
                "goal_id": goal.goal_id,
                "description": goal.description,
                "completed": completed,
                "progress": self._calculate_goal_progress(goal)
            })
        return progress

    def _calculate_goal_progress(self, goal: SceneGoal) -> float:
        """计算目标完成百分比"""
        total_requirements = len(goal.required_info) + len(goal.required_trust)
        if total_requirements == 0:
            return 1.0

        completed = 0
        for info_id in goal.required_info:
            if info_id in self.state["collected_info"]:
                completed += 1

        for npc_id, required_trust in goal.required_trust.items():
            if self.state["trust_levels"].get(npc_id, 0) >= required_trust:
                completed += 1

        return completed / total_requirements

    def _should_trigger_decision(self) -> bool:
        """是否应该触发决策点"""
        # 当目标基本完成或回合快用完时触发
        if self.turn_count >= self.max_turns_per_scene - 3:
            return True

        # 或者当主要目标完成时
        for goal in self.current_goals:
            if goal.check_completion(self.state) and goal.goal_id not in self.state["decisions_made"]:
                return True

        return False

    def _get_next_decision(self) -> Optional[Dict]:
        """获取下一个决策点"""
        scene_data = self.scenes.get(self.current_scene, {})
        for decision in scene_data.get("decisions", []):
            if decision.decision_id not in self.state["decisions_made"]:
                return {
                    "decision_id": decision.decision_id,
                    "title": decision.title,
                    "description": decision.description,
                    "choices": decision.choices
                }
        return None

    def make_decision(self, decision_id: str, choice_id: str) -> Dict[str, Any]:
        """做出决策"""
        self.state["decisions_made"].append(decision_id)

        # 查找决策和选择
        scene_data = self.scenes.get(self.current_scene, {})
        for decision in scene_data.get("decisions", []):
            if decision.decision_id == decision_id:
                for choice in decision.choices:
                    if choice["id"] == choice_id:
                        # 应用选择效果
                        self._apply_effects(choice.get("effects", {}))

                        self.current_phase = GamePhase.EXPLORATION

                        return {
                            "success": True,
                            "choice_text": choice["text"],
                            "effects_applied": choice.get("effects", {}),
                            "new_phase": self.current_phase.value
                        }

        return {"success": False, "error": "Decision or choice not found"}

    def _apply_effects(self, effects: Dict[str, Any]):
        """应用效果"""
        if "collected_info" in effects:
            self.state["collected_info"].extend(effects["collected_info"])
        if "grandmother_s0_trust" in effects:
            self.state["trust_levels"]["grandmother_s0"] = \
                self.state["trust_levels"].get("grandmother_s0", 0.5) + effects["grandmother_s0_trust"]
        if "traveler_s0_trust" in effects:
            self.state["trust_levels"]["traveler_s0"] = \
                self.state["trust_levels"].get("traveler_s0", 0.3) + effects["traveler_s0_trust"]
        if "insight" in effects:
            self.state["insights_used"] += effects["insight"]
        if "unlock_secret" in effects:
            self.state["secrets_unlocked"].append(effects["unlock_secret"])

    def _check_scene_complete(self) -> bool:
        """检查场景是否完成"""
        # 如果已经做过决策，场景完成
        scene_data = self.scenes.get(self.current_scene, {})
        scene_decisions = [d.decision_id for d in scene_data.get("decisions", [])]
        if any(d in self.state["decisions_made"] for d in scene_decisions):
            return True

        # 或者回合用尽
        if self.turn_count >= self.max_turns_per_scene:
            return True

        return False

    def _get_completion_reason(self) -> str:
        """获取完成原因"""
        scene_data = self.scenes.get(self.current_scene, {})
        scene_decisions = [d.decision_id for d in scene_data.get("decisions", [])]
        if any(d in self.state["decisions_made"] for d in scene_decisions):
            return "decision_made"
        if self.turn_count >= self.max_turns_per_scene:
            return "turns_exhausted"
        return "unknown"

    def get_next_scene(self) -> str:
        """获取下一个场景"""
        scene_order = ["scene-0-wuzhishan", "scene-1-chentangguan"]
        try:
            current_idx = scene_order.index(self.current_scene)
            if current_idx + 1 < len(scene_order):
                return scene_order[current_idx + 1]
        except ValueError:
            pass
        return "ending"

    def _get_public_state(self) -> Dict[str, Any]:
        """获取公开状态（给玩家看的）"""
        return {
            "turn": self.turn_count,
            "max_turns": self.max_turns_per_scene,
            "collected_info_count": len(self.state["collected_info"]),
            "insights_used": self.state["insights_used"],
            "goals_completed": sum(1 for g in self.current_goals if g.check_completion(self.state)),
            "total_goals": len(self.current_goals),
        }

    def get_game_summary(self) -> Dict[str, Any]:
        """获取游戏总结"""
        return {
            "scenes_visited": [self.current_scene],  # 简化版
            "decisions_made": self.state["decisions_made"],
            "collected_info": self.state["collected_info"],
            "secrets_unlocked": self.state["secrets_unlocked"],
            "final_trust_levels": self.state["trust_levels"],
        }
