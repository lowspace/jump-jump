# /architecture/prototype/behind_scenes_renderer.py

from typing import Dict, Any, List, Optional, Literal
from dataclasses import dataclass
from enum import Enum

class RevealType(str, Enum):
    VARIABLE_CHANGE = "variable_change"
    NPC_INTENT = "npc_intent"
    ECHO_PREVIEW = "echo_preview"
    BEHIND_DIALOGUE = "behind_dialogue"

@dataclass
class RevealEvent:
    """揭示事件"""
    event_type: RevealType
    content: str
    priority: int
    metadata: Dict[str, Any]

class BehindScenesRenderer:
    """背后博弈渲染器"""

    TEMPLATES = {
        RevealType.VARIABLE_CHANGE: "【背后】{var_name}: {old_val} → {new_val}",
        RevealType.NPC_INTENT: "【幕后】{npc_name} 的真实意图: {intent}",
        RevealType.ECHO_PREVIEW: "【回响】这个选择将在 {echo_id} 中回响...",
        RevealType.BEHIND_DIALOGUE: "【幕后】{npc_a} 与 {npc_b} 的暗中交锋: {summary}"
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
        """渲染变量变化"""
        content = self.TEMPLATES[RevealType.VARIABLE_CHANGE].format(
            var_name=self._translate_var_name(var_name),
            old_val=old_val,
            new_val=new_val
        )

        if reason:
            content += f" ({reason})"

        return RevealEvent(
            event_type=RevealType.VARIABLE_CHANGE,
            content=content,
            priority=5,
            metadata={"var_name": var_name, "old": old_val, "new": new_val}
        )

    def render_npc_intent(
        self,
        npc_id: str,
        npc_name: str,
        intent: str,
        insight_used: bool = False
    ) -> RevealEvent:
        """渲染 NPC 真实意图揭示"""
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
        preview_text: str
    ) -> RevealEvent:
        """渲染回响预告"""
        content = self.TEMPLATES[RevealType.ECHO_PREVIEW].format(
            echo_id=echo_id
        )

        if target_scene == "scene-0":
            hint = "（在遥远的未来...）"
        else:
            hint = f"（在{target_scene}...）"

        content += f"\n    {preview_text} {hint}"

        return RevealEvent(
            event_type=RevealType.ECHO_PREVIEW,
            content=content,
            priority=7,
            metadata={"echo_id": echo_id, "target": target_scene}
        )

    def queue_reveals(self, events: List[RevealEvent], state: Dict[str, Any]):
        """将揭示事件加入队列"""
        for event in events:
            self.reveal_queue.append(event)

        self.reveal_queue.sort(key=lambda e: e.priority, reverse=True)

    def flush_reveals(self, format: Literal["narrative", "structured"] = "narrative") -> Any:
        """输出队列中的所有揭示"""
        if format == "structured":
            result = [event.__dict__ for event in self.reveal_queue]
            self.reveal_queue = []
            return result

        lines = []
        for event in self.reveal_queue:
            lines.append(event.content)

        self.reveal_queue = []
        return "\n\n".join(lines) if lines else None

    def _translate_var_name(self, var_name: str) -> str:
        """将变量名翻译为玩家友好的名称"""
        translations = {
            "nezha_trust": "哪吒信任度",
            "wushi_presence": "武师在场度",
            "lijing_hesitation": "李靖犹豫度",
            "knife_choice": "选刀",
            "armguard": "护腕",
            "faith_erosion_level": "信念侵蚀等级"
        }
        return translations.get(var_name, var_name)
