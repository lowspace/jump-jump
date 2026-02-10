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
            "insights_true_purpose_used": 0,
            "insights_behind_dialogue_used": 0,
            "decisions_made": [],
            "decisions_detail": [],
            "scenes_visited": [],
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
                "decisions": [
                    DecisionPoint(
                        decision_id="s1_final_choice",
                        title="少年的选择",
                        description="哪吒即将做出不可挽回的决定，而你恰好在场...",
                        choices=[
                            {
                                "id": "try_persuade",
                                "text": "试图劝阻哪吒，告诉他还有别的路",
                                "effects": {"collected_info": ["persuade_attempt"]}
                            },
                            {
                                "id": "silent_witness",
                                "text": "默默见证这一切，不做干预",
                                "effects": {"collected_info": ["silent_witness"]}
                            },
                            {
                                "id": "relay_mother",
                                "text": "转告殷夫人的话——她准备了逃走的盘缠",
                                "effects": {"collected_info": ["mother_message"]}
                            }
                        ]
                    )
                ],
                "events": [
                    GameEvent(
                        event_id="s1_nezha_trust",
                        trigger_type="trust",
                        trigger_condition={"nezha_s1": 0.6},
                        content="哪吒看了你一眼，嘴角微动，似乎想说什么...",
                        effects={"collected_info": ["nezha_hesitation"]}
                    ),
                ],
            },
            "scene-2-tianhe": {
                "name": "天河·坠落之前",
                "description": "第二章：天蓬元帅被贬之前，天庭灵蕴黑幕",
                "goals": [
                    SceneGoal(
                        goal_id="s2_uncover_secret",
                        description="发现天庭灵蕴交易的真相",
                        required_info=["lingyun_secret", "tianpeng_love"],
                        max_turns=18
                    ),
                ],
                "decisions": [
                    DecisionPoint(
                        decision_id="s2_final_choice",
                        title="知情者的抉择",
                        description="你知道了不该知道的秘密，现在必须做出选择...",
                        choices=[
                            {
                                "id": "report_truth",
                                "text": "向上司报告发现的账目异常",
                                "effects": {"collected_info": ["bureaucrat_choice"]}
                            },
                            {
                                "id": "keep_silent",
                                "text": "装作什么都没看见",
                                "effects": {"collected_info": ["silent_complicity"]}
                            },
                            {
                                "id": "warn_tianpeng",
                                "text": "暗示天蓬元帅有人要害他",
                                "effects": {"collected_info": ["defiant_act"]}
                            }
                        ]
                    )
                ],
            },
            "scene-3-huaguoshan": {
                "name": "花果山·最后的桃",
                "description": "第三章：悟空被压后，花果山猴群的生存挣扎",
                "goals": [
                    SceneGoal(
                        goal_id="s3_survive_choice",
                        description="在忠诚与生存之间找到出路",
                        required_info=["monkey_memory", "survival_truth"],
                        max_turns=20
                    ),
                ],
                "decisions": [
                    DecisionPoint(
                        decision_id="s3_final_choice",
                        title="猴群的抉择",
                        description="天庭的围剿即将到来，你们该怎么办...",
                        choices=[
                            {
                                "id": "fight_on",
                                "text": "继续反抗，像大王那样战斗到底",
                                "effects": {"collected_info": ["defiant_legacy"]}
                            },
                            {
                                "id": "hide_survive",
                                "text": "躲起来，活着才有希望",
                                "effects": {"collected_info": ["pragmatic_survival"]}
                            },
                            {
                                "id": "surrender_memory",
                                "text": "向天庭投降，但偷偷保留大王的记忆",
                                "effects": {"collected_info": ["hidden_faith"]}
                            }
                        ]
                    )
                ],
            },
            "scene-4-lingtai": {
                "name": "灵台·空经",
                "description": "第四章：取经前夕，发现无字真经的抄经僧",
                "goals": [
                    SceneGoal(
                        goal_id="s4_faith_crisis",
                        description="在无字真经面前找到属于自己的信仰",
                        required_info=["empty_sutra_truth", "xuanzang_wisdom"],
                        max_turns=16
                    ),
                ],
                "decisions": [
                    DecisionPoint(
                        decision_id="s4_final_choice",
                        title="信仰的选择",
                        description="经文是空的，但你的路不能空。你选择...",
                        choices=[
                            {
                                "id": "continue_copy",
                                "text": "继续抄经，把空白当作另一种经文",
                                "effects": {"collected_info": ["faith_in_void"]}
                            },
                            {
                                "id": "leave_temple",
                                "text": "离开灵山，去路上寻找自己的答案",
                                "effects": {"collected_info": ["journey_begins"]}
                            },
                            {
                                "id": "confront_truth",
                                "text": "当众质问监院，要求真相",
                                "effects": {"collected_info": ["reckless_truth"]}
                            }
                        ]
                    )
                ],
            }
        }

    def start_scene(self, scene_id: str) -> Dict[str, Any]:
        """开始新场景"""
        self.current_scene = scene_id
        self.current_phase = GamePhase.EXPLORATION
        self.turn_count = 0

        # 记录访问过的场景
        if scene_id not in self.state["scenes_visited"]:
            self.state["scenes_visited"].append(scene_id)

        # 重置每场景洞察力计数
        self.state["insights_true_purpose_used"] = 0
        self.state["insights_behind_dialogue_used"] = 0

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
                        # 记录决策详情
                        self.state["decisions_detail"].append({
                            "scene": self.current_scene,
                            "decision_id": decision_id,
                            "choice_id": choice_id,
                            "choice_text": choice["text"],
                        })

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
        scene_order = [
            "scene-0-wuzhishan",
            "scene-1-chentangguan",
            "scene-2-tianhe",
            "scene-3-huaguoshan",
            "scene-4-lingtai"
        ]
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
            "scenes_visited": self.state["scenes_visited"],
            "decisions_made": self.state["decisions_made"],
            "decisions_detail": self.state["decisions_detail"],
            "collected_info": self.state["collected_info"],
            "secrets_unlocked": self.state["secrets_unlocked"],
            "final_trust_levels": self.state["trust_levels"],
            "insights_true_purpose_used": self.state["insights_true_purpose_used"],
            "insights_behind_dialogue_used": self.state["insights_behind_dialogue_used"],
        }

    def generate_impact_report(self) -> Dict[str, Any]:
        """
        生成影响力报告

        基于玩家行为画像，展示"你改变了什么微小的事"。
        涟漪而非巨浪（P6）。
        """
        decisions = self.state["decisions_detail"]

        # ── 1) 行为画像计算 ──
        # 三个维度：理想主义、变革参与度、记忆守护
        idealism = 0.0
        change_participation = 0.0
        memory_guardian = 0.0

        choice_scores = {
            # Scene 0
            "tell_grandma":     {"idealism": 0.3, "change": 0.1, "memory": 0.6},
            "keep_secret":      {"idealism": 0.5, "change": 0.2, "memory": 0.4},
            "follow_traveler":  {"idealism": 0.7, "change": 0.6, "memory": 0.2},
            # Scene 1
            "try_persuade":     {"idealism": 0.8, "change": 0.7, "memory": 0.3},
            "silent_witness":   {"idealism": 0.3, "change": 0.1, "memory": 0.7},
            "relay_mother":     {"idealism": 0.5, "change": 0.5, "memory": 0.5},
            # Scene 2
            "report_truth":     {"idealism": 0.7, "change": 0.8, "memory": 0.2},
            "keep_silent":      {"idealism": 0.2, "change": 0.1, "memory": 0.3},
            "warn_tianpeng":    {"idealism": 0.6, "change": 0.6, "memory": 0.5},
            # Scene 3
            "fight_on":         {"idealism": 0.9, "change": 0.9, "memory": 0.8},
            "hide_survive":     {"idealism": 0.2, "change": 0.2, "memory": 0.5},
            "surrender_memory": {"idealism": 0.4, "change": 0.3, "memory": 0.9},
            # Scene 4
            "continue_copy":    {"idealism": 0.4, "change": 0.2, "memory": 0.8},
            "leave_temple":     {"idealism": 0.7, "change": 0.7, "memory": 0.4},
            "confront_truth":   {"idealism": 0.9, "change": 0.9, "memory": 0.3},
        }

        decision_count = max(len(decisions), 1)
        for d in decisions:
            scores = choice_scores.get(d["choice_id"], {})
            idealism += scores.get("idealism", 0.5)
            change_participation += scores.get("change", 0.5)
            memory_guardian += scores.get("memory", 0.5)

        idealism /= decision_count
        change_participation /= decision_count
        memory_guardian /= decision_count

        # 组合得出 profile label
        profile = self._calculate_profile(idealism, change_participation, memory_guardian)

        # ── 2) 涟漪叙事 ──
        ripple_narratives = {
            # Scene 0
            "tell_grandma": "那天晚上祖母没有睡着。她翻出了压在箱底三十年的旧布包，里面是一片烧焦的桃叶。第二天早上，她把它别在了你的衣襟上。",
            "keep_secret": "你没有说出口的话，变成了夜里反复出现的梦。梦里五指山在震动，有什么东西快要醒了。后来你发现，梦里的震动是真的。",
            "follow_traveler": "行者走后，你在他歇脚的石头上发现了一个小小的刻痕——一只猴子的轮廓。你用手指描了一遍，石头是温热的。",
            # Scene 1
            "try_persuade": "哪吒多停顿了三秒。那三秒里他回头看了一眼母亲的方向。他最终还是拿起了刀，但那三秒，是他留给这个世界最后的犹豫。",
            "silent_witness": "你什么都没做。但你在场。多年后哪吒的莲藕身偶尔会感到一阵温热——那是被人注视过的温度，虽然他不知道是谁。",
            "relay_mother": "哪吒听完后沉默了很久。他没有逃走，但他把殷夫人准备的盘缠偷偷放回了母亲的枕头下。第二天剔骨时，他的眼睛是干的。",
            # Scene 2
            "report_truth": "你的报告石沉大海，没有人理会一个小吏的发现。但十五年后，有人在旧档案里找到了它，那时灵蕴危机已经不可收拾。你的名字被记在了一份没人看的备忘录上。",
            "keep_silent": "天蓬被贬的那天，你正常上班、正常下班。走过天河桥时，你低头看了一眼水面。水面平静如镜，什么都没有发生。",
            "warn_tianpeng": "天蓬收到暗示后笑了。他说他早就知道。但那天晚上他在阿月的窗下多站了一刻钟。守卫的记录上写着：'异常滞留，已上报。'",
            # Scene 3
            "fight_on": "最后一场战斗很短。天兵甚至没有认真打。但铁头冲锋时喊的那声'大王万岁'，在山谷里回响了三遍。巡逻队长在报告里写了六个字：'已清剿，无异常。'",
            "hide_survive": "猴群藏进了水帘洞最深处。五年后，一只小猴在洞壁上发现了一行字，是大王用指甲刻的：'俺老孙到此一游'。它不认识字，但用手指描了很多遍。",
            "surrender_memory": "猴群投降时，天兵收走了所有刻着大王故事的石板。但老猴提前把最重要的那块藏在了水帘洞入口的瀑布后面。一百年后，石板上的字已经被水冲得模糊，但还能辨认。",
            # Scene 4
            "continue_copy": "你继续抄经。空白的经卷在你笔下变成了一行行工整的字。慧空师兄路过时停下看了一眼，嘴角动了动，什么都没说，继续走了。",
            "leave_temple": "你离开灵山的那天是个阴天。走到山门时你回头看了一眼，慧空师兄站在抄经房的窗口。他朝你轻轻点了点头。后来你在路上遇到了一个穿普通僧袍的人。",
            "confront_truth": "监院把你逐出了寺院。理由是'信力不足'。慧空师兄在你走之前塞给你一张纸条，上面写着一个地名。你后来去了那里，发现了另一座藏经阁。",
        }

        scene_ripples = []
        scene_names = {
            "scene-0-wuzhishan": "五指山·尘埃",
            "scene-1-chentangguan": "陈塘关",
            "scene-2-tianhe": "天河·坠落之前",
            "scene-3-huaguoshan": "花果山·最后的桃",
            "scene-4-lingtai": "灵台·空经",
        }
        for d in decisions:
            scene_ripples.append({
                "scene": d["scene"],
                "scene_name": scene_names.get(d["scene"], d["scene"]),
                "choice_text": d["choice_text"],
                "ripple": ripple_narratives.get(d["choice_id"], "你的选择在世界的某个角落激起了微小的涟漪。"),
            })

        # ── 3) 结尾总结 ──
        profile_endings = {
            "革命者": "你试图改变一切。结果什么都没变。但因为你来过，有些人在做选择时多犹豫了一秒。那一秒，是你存在过的证据。",
            "守夜人": "你选择守护记忆而非创造新的。在这个遗忘比记住更容易的世界里，你是一根不肯熄灭的蜡烛。风吹不灭你，因为你知道黑暗的重量。",
            "幸存者": "你选择活下来。这听起来不够壮烈，但在这个世界里，活着本身就是一种反抗。你用呼吸证明：他们没有赢。",
            "见证者": "你什么都没做，但你什么都看到了。这个世界上多了一个记得真相的人。也许有一天，真相需要一个讲述者。",
            "理想主义者": "你相信事情可以不同。在一个命运已经被写定的世界里，你的相信本身就是最大的叛逆。",
            "实用主义者": "你做了能做的事，接受了不能改变的事。这不是妥协，是智慧。你知道什么时候该弯腰，什么时候该站直。",
            "叛逆者": "你拒绝所有既定的答案。你不一定找到了更好的，但你证明了：还有别的可能。",
            "沉默者": "你的沉默比大多数人的呐喊更重。因为你知道，在这个世界上，有些事说出来就碎了。你选择把它们完整地留在心里。",
        }

        ending = profile_endings.get(profile["label"], profile_endings["见证者"])
        closing = "你没有改变西游的结局。但因为你来过，这个世界上多了一些微小的、不同的东西。"

        return {
            "scenes_visited": self.state["scenes_visited"],
            "decisions_detail": decisions,
            "collected_info_count": len(self.state["collected_info"]),
            "insights_total_used": (
                self.state["insights_true_purpose_used"]
                + self.state["insights_behind_dialogue_used"]
            ),
            "profile": profile,
            "scene_ripples": scene_ripples,
            "ending_narrative": ending,
            "closing": closing,
        }

    def _calculate_profile(
        self, idealism: float, change: float, memory: float
    ) -> Dict[str, Any]:
        """根据三维度得分计算行为画像标签"""
        # 8种画像
        if idealism > 0.7 and change > 0.7:
            label = "革命者"
        elif memory > 0.7 and change < 0.4:
            label = "守夜人"
        elif idealism < 0.3 and change < 0.3:
            label = "幸存者"
        elif idealism < 0.4 and memory > 0.5:
            label = "见证者"
        elif idealism > 0.6 and change < 0.5:
            label = "理想主义者"
        elif idealism < 0.5 and change > 0.5:
            label = "实用主义者"
        elif change > 0.6 and memory < 0.4:
            label = "叛逆者"
        else:
            label = "沉默者"

        return {
            "label": label,
            "idealism_index": round(idealism, 2),
            "change_participation": round(change, 2),
            "memory_guardian_index": round(memory, 2),
        }
