# /src/backend/app/behind_scenes_renderer.py
# Behind-the-Scenes Renderer for Jump Jump - based on architecture/prototype/behind_scenes_renderer.py

from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum


class RevealType(str, Enum):
    VARIABLE_CHANGE = "variable_change"
    NPC_INTENT = "npc_intent"
    ECHO_PREVIEW = "echo_preview"
    BEHIND_DIALOGUE = "behind_dialogue"


@dataclass
class RevealEvent:
    """Reveal event"""
    event_type: RevealType
    content: str
    priority: int = 5
    metadata: Dict[str, Any] = field(default_factory=dict)


class BehindScenesRenderer:
    """
    Behind-the-Scenes Renderer

    Renders variable changes, NPC intents, and echo previews
    for the behind-the-scenes reveal system.
    """

    TEMPLATES = {
        RevealType.VARIABLE_CHANGE: "【背后】{var_name}: {old_val} → {new_val}",
        RevealType.NPC_INTENT: "【幕后】{npc_name} 的真实意图: {intent}",
        RevealType.ECHO_PREVIEW: "【回响】这个选择将在 {target} 中回响...",
        RevealType.BEHIND_DIALOGUE: "【幕后】{npc_a} 与 {npc_b} 的暗中交锋: {summary}"
    }

    # Variable name translations
    VAR_TRANSLATIONS = {
        # Scene 1
        "nezha_trust": "哪吒信任度",
        "knife_choice": "选刀",
        "wushi_presence": "武师在场度",
        "lijing_hesitation": "李靖犹豫度",
        "armguard": "护腕去向",
        "yangjian_triggered": "杨戬触发",
        # Scene 2
        "ledger_choice": "账本处置",
        "tenpeng_last_words": "天蓬遗言",
        "juanlian_suspicion": "卷帘大将怀疑度",
        "seventh_aperture_awareness": "第七窍觉醒度",
        "lingshan_secret": "灵山秘密知晓度",
        "survival_method": "生存方式",
        # Scene 3
        "peach_tree_fate": "桃树命运",
        "monkey_unity": "猴群团结度",
        "wukong_stick": "金箍棒去向",
        "zixia_encounter": "紫霞相遇",
        "resistance_choice": "抵抗选择",
        "memory_kept": "记忆传承",
        # Scene 4
        "sutra_truth": "经文真相认知",
        "final_scroll": "最终经卷",
        "tangseng_encounter": "唐僧相遇",
        "huikong_relationship": "与慧空关系",
        "faith_state": "信仰状态",
        "pen_taken": "笔的去向",
        # Scene 0
        "wall_inscription": "石壁字迹",
        "mountain_voice": "山的声音",
        "final_act": "最后行为",
        "grandmother_stories": "听过的故事数",
        "curiosity_level": "好奇心",
        "wukong_awareness": "悟空感知度",
        # Cross-scene
        "faith_erosion_level": "信念侵蚀等级",
        "moral_consistency": "道德一致性",
        "info_exploration_rate": "信息探索率",
    }

    def __init__(self):
        self.reveal_queue: List[RevealEvent] = []

    def render_variable_change(
        self,
        var_name: str,
        old_val: Any,
        new_val: Any,
        reason: Optional[str] = None
    ) -> RevealEvent:
        """Render variable change"""
        content = self.TEMPLATES[RevealType.VARIABLE_CHANGE].format(
            var_name=self._translate_var_name(var_name),
            old_val=self._format_value(old_val),
            new_val=self._format_value(new_val)
        )

        if reason:
            content += f" ({reason})"

        return RevealEvent(
            event_type=RevealType.VARIABLE_CHANGE,
            content=content,
            priority=5,
            metadata={"var_name": var_name, "old": old_val, "new": new_val, "reason": reason}
        )

    def render_npc_intent(
        self,
        npc_id: str,
        npc_name: str,
        intent: str,
        insight_used: bool = False
    ) -> RevealEvent:
        """Render NPC true intent reveal"""
        if insight_used:
            content = self.TEMPLATES[RevealType.NPC_INTENT].format(
                npc_name=npc_name,
                intent=intent
            )
            priority = 8
        else:
            content = f"【幕后】{npc_name} 似乎另有目的...（使用洞察力揭示）"
            priority = 3

        return RevealEvent(
            event_type=RevealType.NPC_INTENT,
            content=content,
            priority=priority,
            metadata={"npc_id": npc_id, "full_intent": intent, "revealed": insight_used}
        )

    def render_echo_preview(
        self,
        echo_id: str,
        target_scene: str,
        preview_text: str,
        hint_level: Literal["subtle", "moderate", "strong"] = "subtle"
    ) -> RevealEvent:
        """Render echo preview"""
        content = f"【回响】"

        if hint_level == "subtle":
            content += "这个选择将在未来回响..."
        elif hint_level == "moderate":
            content += f"这个选择将在{self._translate_scene(target_scene)}产生回响..."
        else:  # strong
            content += f"这个选择将在{self._translate_scene(target_scene)}以意想不到的方式回响..."

        content += f"\n    {preview_text}"

        if target_scene == "scene-0":
            hint = "（在遥远的未来...）"
        else:
            hint = f"（在{self._translate_scene(target_scene)}...）"
        content += f" {hint}"

        return RevealEvent(
            event_type=RevealType.ECHO_PREVIEW,
            content=content,
            priority=7,
            metadata={"echo_id": echo_id, "target": target_scene, "hint_level": hint_level}
        )

    def render_behind_dialogue(
        self,
        npc_a: str,
        npc_b: str,
        summary: str,
        hidden_details: Optional[str] = None
    ) -> RevealEvent:
        """Render behind-the-scenes dialogue between NPCs"""
        content = self.TEMPLATES[RevealType.BEHIND_DIALOGUE].format(
            npc_a=npc_a,
            npc_b=npc_b,
            summary=summary
        )

        if hidden_details:
            content += f"\n    幕后：{hidden_details}"

        return RevealEvent(
            event_type=RevealType.BEHIND_DIALOGUE,
            content=content,
            priority=6,
            metadata={"npc_a": npc_a, "npc_b": npc_b, "summary": summary}
        )

    def render_faith_erosion(
        self,
        old_level: int,
        new_level: int,
        reason: str
    ) -> RevealEvent:
        """Render faith erosion change"""
        content = f"【信念侵蚀】等级 {old_level} → {new_level}\n    原因：{reason}"

        return RevealEvent(
            event_type=RevealType.VARIABLE_CHANGE,
            content=content,
            priority=9,
            metadata={
                "var_name": "faith_erosion_level",
                "old": old_level,
                "new": new_level,
                "reason": reason
            }
        )

    def render_echo_triggered(
        self,
        source_scene: str,
        echo_content: str,
        mechanical_effect: Optional[str] = None
    ) -> RevealEvent:
        """Render triggered echo from previous scene"""
        content = f"【回响触发】\n"
        content += f"    {self._translate_scene(source_scene)}的记忆浮现...\n"
        content += f"    \"{echo_content}\""

        if mechanical_effect:
            content += f"\n    效果：{mechanical_effect}"

        return RevealEvent(
            event_type=RevealType.ECHO_PREVIEW,
            content=content,
            priority=10,
            metadata={"source_scene": source_scene, "echo_content": echo_content}
        )

    def queue_reveals(self, events: List[RevealEvent]):
        """Add reveal events to queue"""
        for event in events:
            self.reveal_queue.append(event)

        # Sort by priority (higher first)
        self.reveal_queue.sort(key=lambda e: e.priority, reverse=True)

    def flush_reveals(
        self,
        format: Literal["narrative", "structured"] = "narrative"
    ) -> Any:
        """Output all queued reveals"""
        if format == "structured":
            result = [
                {
                    "type": event.event_type.value,
                    "content": event.content,
                    "priority": event.priority,
                    "metadata": event.metadata
                }
                for event in self.reveal_queue
            ]
            self.reveal_queue = []
            return result

        lines = []
        for event in self.reveal_queue:
            lines.append(event.content)

        self.reveal_queue = []
        return "\n\n".join(lines) if lines else None

    def get_queued_reveals(self) -> List[RevealEvent]:
        """Get current queued reveals without clearing"""
        return self.reveal_queue.copy()

    def clear_queue(self):
        """Clear reveal queue"""
        self.reveal_queue = []

    def _translate_var_name(self, var_name: str) -> str:
        """Translate variable name to player-friendly name"""
        return self.VAR_TRANSLATIONS.get(var_name, var_name)

    def _translate_scene(self, scene_id: str) -> str:
        """Translate scene ID to Chinese name"""
        translations = {
            "scene-0-wuzhishan": "五指山",
            "scene-1-chentangguan": "陈塘关",
            "scene-2-tianhe": "天河",
            "scene-3-huaguoshan": "花果山",
            "scene-4-lingtai": "灵台方寸山",
        }
        return translations.get(scene_id, scene_id)

    def _format_value(self, value: Any) -> str:
        """Format value for display"""
        if value is None:
            return "无"
        if isinstance(value, bool):
            return "是" if value else "否"
        if isinstance(value, (int, float)):
            return str(value)
        return str(value)

    def generate_phase_summary(
        self,
        phase_id: str,
        variable_changes: List[Dict[str, Any]]
    ) -> str:
        """Generate summary for phase end"""
        lines = [f"=== {phase_id} 阶段结束 ===", ""]

        if variable_changes:
            lines.append("本阶段的变化：")
            for change in variable_changes:
                var_name = self._translate_var_name(change.get("var", "unknown"))
                old_val = self._format_value(change.get("old"))
                new_val = self._format_value(change.get("new"))
                lines.append(f"  {var_name}: {old_val} → {new_val}")
        else:
            lines.append("本阶段没有显著变化。")

        return "\n".join(lines)

    def generate_scene_debrief(
        self,
        scene_id: str,
        all_variables: Dict[str, Any],
        key_decisions: List[str]
    ) -> str:
        """Generate scene debrief"""
        lines = [
            f"=== {self._translate_scene(scene_id)} 场景结束 ===",
            "",
            "关键决定："
        ]

        for decision in key_decisions:
            lines.append(f"  - {decision}")

        lines.extend(["", "当前状态："])

        # Show key variables
        key_vars = [
            "faith_erosion_level",
            "moral_consistency",
            "info_exploration_rate"
        ]
        for var in key_vars:
            if var in all_variables:
                lines.append(f"  {self._translate_var_name(var)}: {all_variables[var]}")

        return "\n".join(lines)


# Global instance
behind_scenes_renderer = BehindScenesRenderer()
