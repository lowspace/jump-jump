#!/usr/bin/env python3
"""
Jump Jump CLI v3 - 真正的NPC Agent交互系统
核心：NPC间信息传递 × 后台社会模拟 × 缝隙参与
"""

import asyncio
import random
import sys
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.table import Table
from rich.layout import Layout
from rich import box

# Import the simplified agent engine (avoid loading backend.__init__)
import importlib.util
import sys

# Load npc_society first (dependency)
spec_npc = importlib.util.spec_from_file_location(
    "npc_society",
    "/Users/dnhb/Desktop/GitHub/My_Projects/jump-jump/src/backend/app/npc_society.py"
)
npc_module = importlib.util.module_from_spec(spec_npc)
sys.modules["npc_society"] = npc_module
spec_npc.loader.exec_module(npc_module)

# Load simple_agent_engine
spec_engine = importlib.util.spec_from_file_location(
    "simple_agent_engine",
    "/Users/dnhb/Desktop/GitHub/My_Projects/jump-jump/src/backend/app/simple_agent_engine.py"
)
engine_module = importlib.util.module_from_spec(spec_engine)
spec_engine.loader.exec_module(engine_module)
SimpleAgentEngine = engine_module.SimpleAgentEngine
PlayerAction = engine_module.PlayerAction

console = Console()


class InfoLevel(Enum):
    """信息层级"""
    PUBLIC = "public"      # 公开信息
    PRIVATE = "private"    # 私密信息
    HIDDEN = "hidden"      # 隐藏信息
    SECRET = "secret"      # 机密信息


@dataclass
class Information:
    """信息单元"""
    info_id: str
    content: str
    level: InfoLevel
    source: str
    reliability: float
    learned_from: str = ""  # 从哪里获得这条信息


class JumpJumpCLIV3:
    """重构的CLI客户端 - 真正的Agent版本"""

    def __init__(self):
        self.engine = SimpleAgentEngine()
        self.session_id: Optional[str] = None
        self.current_scene = "scene-0-wuzhishan"
        self.player_knowledge: Dict[str, Information] = {}
        self.turn_count = 0
        self.insight_quota = {
            "true_purpose": 2,
            "behind_dialogue": 2
        }

    async def start_game(self):
        """开始游戏"""
        self._show_title()
        self._show_background()

        try:
            # 创建会话
            self.session_id = await self.engine.create_session(self.current_scene)
            console.print(f"\n[dim]会话ID: {self.session_id}[/dim]\n")

            # 显示开场
            self._show_opening()

            # 主循环
            await self._main_loop()

        except KeyboardInterrupt:
            self._show_exit_summary()
        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            import traceback
            traceback.print_exc()

    def _show_title(self):
        """显示标题"""
        console.print(Panel.fit(
            "[bold cyan]Jump Jump - 悟空传[/bold cyan]\n"
            "[dim]文字探险游戏 CLI v3 - 真正的Agent交互[/dim]\n"
            "[dim]NPC间信息传递 × 后台社会模拟[/dim]",
            border_style="cyan"
        ))

    def _show_background(self):
        """显示背景"""
        from rich.text import Text

        content = Text()
        content.append("序章：五指山·尘埃\n\n", style="yellow")
        content.append("你是五指山附近的少年樵夫，今天走了一条不常走的小路。\n", style="white")
        content.append("这座山藏着很多故事。更复杂的是，知道故事的人之间也在互相试探、传递情报。\n", style="dim")
        content.append("你看到的只是表象，背后的信息流动才是关键。\n\n", style="dim")

        content.append("【可对话Agent】\n", style="bold")
        content.append("  • 祖母 - 你的家人，知道民间传说，但会筛选告诉你什么\n", style="green")
        content.append("  • 行者 - 路过的神秘人，与其他NPC有秘密交流\n\n", style="green")

        content.append("【系统提示】\n", style="bold")
        content.append("  NPC会在你行动后私下交流。使用[洞察力]可以偷听到部分对话。\n", style="magenta")
        content.append("  当你与某人对话时，其他人可能在观察，并事后传播你的行为。\n", style="magenta")

        console.print(Panel(content, border_style="yellow", title="背景"))

    def _show_opening(self):
        """显示开场"""
        console.print(Panel(
            "[white]五指山的风很大。你站在烧焦的桃树旁，感到有些不安。[/white]\n\n"
            "[dim]祖母在不远处整理柴火，一个陌生的行者正在岩壁前徘徊。[/dim]\n"
            "[dim]你不知道的是，他们之间的关系，以及他们对你的看法，会随着你的每个行动而改变。[/dim]",
            border_style="blue"
        ))

        # 显示NPC初始状态
        self._show_npc_network()

    def _show_npc_network(self):
        """显示NPC关系网络"""
        console.print("\n[bold cyan]NPC关系网络[/bold cyan]")

        table = Table(show_header=True, header_style="bold")
        table.add_column("NPC")
        table.add_column("对你的态度")
        table.add_column("与其他NPC关系")
        table.add_column("掌握信息数")

        npcs = ["grandmother_s0", "traveler_s0", "wukong_s0"]
        names = {"grandmother_s0": "祖母", "traveler_s0": "行者", "wukong_s0": "悟空(山体)"}

        for npc_id in npcs:
            state = self.engine.get_npc_state(npc_id)
            if state:
                trust = state["trust_toward_player"]
                attitude = "[green]信任" if trust > 0.6 else "[yellow]中立" if trust > 0.3 else "[red]警惕"
                attitude += f"({trust:.1f})[/]"

                rels = []
                for other_id, rel in state.get("relationships", {}).items():
                    if other_id in names:
                        rel_str = f"{names[other_id]}:信任{rel['trust']:.1f}"
                        rels.append(rel_str)

                table.add_row(
                    names[npc_id],
                    attitude,
                    "\n".join(rels) if rels else "[dim]无直接联系[/dim]",
                    str(state["known_info_count"])
                )

        console.print(table)

    async def _main_loop(self):
        """主游戏循环"""
        while True:
            self.turn_count += 1
            console.print(f"\n[dim]回合 {self.turn_count}[/dim]")

            # 显示当前状态
            self._show_status()

            # 显示主菜单
            choice = self._show_main_menu()

            if choice == "q":
                self._show_exit_summary()
                break
            elif choice == "1":
                await self._interact_with_npc()
            elif choice == "2":
                await self._observe_environment()
            elif choice == "3":
                await self._check_information()
            elif choice == "4":
                await self._use_insight()
            elif choice == "5":
                await self._check_npc_network()

    def _show_status(self):
        """显示当前状态"""
        info_counts = {"public": 0, "private": 0, "hidden": 0}
        for info in self.player_knowledge.values():
            info_counts[info.level.value] += 1

        status = f"信息: [green]公开{info_counts['public']}[/green] [yellow]私密{info_counts['private']}[/yellow] [red]隐藏{info_counts['hidden']}[/red]"
        console.print(f"\n{status}")

    def _show_main_menu(self) -> str:
        """显示主菜单"""
        console.print("\n" + "─" * 60)
        console.print("[bold cyan]请选择行动:[/bold cyan]\n")
        console.print("  [1] 与NPC对话 (可能引发NPC间交流)")
        console.print("  [2] 观察环境 (可能触发NPC观察你)")
        console.print("  [3] 整理情报 (查看已知信息)")
        console.print("  [4] 使用洞察力 (偷听NPC对话 / 揭示真实目的)")
        console.print("  [5] 查看NPC网络 (关系与信息传播)")
        console.print("  [q] 退出")
        console.print("─" * 60)

        return Prompt.ask("选择", choices=["1", "2", "3", "4", "5", "q"])

    async def _interact_with_npc(self):
        """与NPC对话 - 这会触发完整的Agent流程"""
        npcs = ["grandmother_s0", "traveler_s0"]
        npc_names = {"grandmother_s0": "祖母", "traveler_s0": "行者"}

        console.print("\n[bold]选择与谁对话:[/bold]")
        for i, npc_id in enumerate(npcs, 1):
            state = self.engine.get_npc_state(npc_id)
            if state:
                trust = "█" * int(state["trust_toward_player"] * 10)
                trust += "░" * (10 - int(state["trust_toward_player"] * 10))
                console.print(f"  [{i}] {npc_names[npc_id]} [信任:{trust}]")

        choice = Prompt.ask("选择", choices=["1", "2", "q"])
        if choice == "q":
            return

        npc_id = npcs[int(choice) - 1]
        npc_name = npc_names[npc_id]

        # 获取玩家输入
        console.print(f"\n[bold cyan]与 {npc_name} 对话中...[/bold cyan]")
        message = Prompt.ask("你说")

        # 创建玩家行动
        action = PlayerAction(
            action_type="dialogue",
            target=npc_id,
            content=message,
            turn=self.turn_count
        )

        # 处理行动 - 这会触发完整的BFS→Adjudicate→DFS流程
        console.print("[dim]NPC正在处理你的话语...[/dim]")

        result = await self.engine.process_player_action(action)

        # 显示NPC的反应
        for reaction in result.npc_reactions:
            if reaction.npc_id == npc_id:
                console.print(Panel(
                    f"[white]{reaction.observable}[/white]",
                    title=f"{npc_name}",
                    border_style="blue"
                ))

        # 显示幕后发生的变化
        if result.behind_scenes:
            console.print("\n[magenta]【幕后动态】[/magenta]")
            for reveal in result.behind_scenes:
                console.print(f"  [dim magenta]• {reveal['content']}[/dim magenta]")
                if reveal.get('hint'):
                    console.print(f"    [dim]{reveal['hint']}[/dim]")

        # 尝试从对话中获取信息
        await self._try_acquire_info_from_dialogue(npc_id, message)

        # 显示NPC网络变化提示
        console.print("\n[dim]NPC关系可能已发生变化...[/dim]")

    async def _try_acquire_info_from_dialogue(self, npc_id: str, message: str):
        """尝试从对话中获取信息"""
        # 根据信任度和对话内容决定能获取什么信息
        state = self.engine.get_npc_state(npc_id)
        if not state:
            return

        trust = state["trust_toward_player"]

        # 定义可获取的信息
        available_info = {
            "grandmother_s0": [
                ("story_nezha", "祖母知道一个关于剔骨还子的故事", InfoLevel.PRIVATE, 0.5),
                ("rumor_tianthe", "天上有人在偷'灵蕴'", InfoLevel.PRIVATE, 0.7),
                ("peach_tree_legend", "桃树与齐天大圣有关", InfoLevel.PUBLIC, 0.0),
            ],
            "traveler_s0": [
                ("wukong_location", "齐天大圣被压在这座山下", InfoLevel.HIDDEN, 0.6),
                ("heaven_secret", "天庭派了人监视这座山", InfoLevel.HIDDEN, 0.8),
                ("traveler_identity", "行者是金蝉子转世", InfoLevel.SECRET, 0.9),
            ]
        }

        # 检查能获得什么
        for info_id, content, level, required_trust in available_info.get(npc_id, []):
            if info_id not in self.player_knowledge and trust >= required_trust:
                if random.random() < trust:  # 信任度越高，越可能分享
                    self.player_knowledge[info_id] = Information(
                        info_id=info_id,
                        content=content,
                        level=level,
                        source=npc_id,
                        reliability=0.8,
                        learned_from=npc_id
                    )
                    console.print(f"\n[green]✓ 获得{level.value}信息: {content}[/green]")
                    break

    async def _observe_environment(self):
        """观察环境"""
        console.print("\n[dim]你仔细观察周围环境...[/dim]")

        # 创建观察行动
        action = PlayerAction(
            action_type="observe",
            target=None,
            content="观察环境",
            turn=self.turn_count
        )

        result = await self.engine.process_player_action(action)

        observations = [
            "路边有一株烧焦的桃树残根，根部焦黑但隐约有新芽冒出的痕迹。",
            "岩壁上有模糊的刻痕，像是'齐天大圣'四个字，但已被风化。",
            "一块不属于这座山的金属碎片，嵌在岩缝中。",
            "山体深处传来低频声响，不像风声，更像某种呼吸。",
        ]

        obs = random.choice(observations)
        console.print(Panel(f"[cyan]{obs}[/cyan]", title="观察发现", border_style="cyan"))

        # 可能被发现
        if result.npc_reactions:
            console.print("\n[yellow]【注意】[/yellow] [dim]你注意到有人在观察你的行为...[/dim]")

    async def _check_information(self):
        """查看已收集的情报"""
        if not self.player_knowledge:
            console.print("\n[yellow]你还没有收集到任何信息。[/yellow]")
            return

        console.print("\n[bold]已收集的情报：[/bold]\n")

        by_level = {"public": [], "private": [], "hidden": [], "secret": []}
        for info in self.player_knowledge.values():
            by_level[info.level.value].append(info)

        for level_name, color in [("public", "green"), ("private", "yellow"), ("hidden", "red"), ("secret", "magenta")]:
            if by_level[level_name]:
                console.print(f"[{color}]【{level_name.upper()}】[/color]")
                for info in by_level[level_name]:
                    source_name = {"grandmother_s0": "祖母", "traveler_s0": "行者"}.get(info.source, info.source)
                    console.print(f"  • {info.content}")
                    console.print(f"    [dim]来源: {source_name} | 可靠度: {info.reliability:.0%}[/dim]")
                console.print()

    async def _use_insight(self):
        """使用洞察力"""
        console.print("\n[bold yellow]使用洞察力[/bold yellow]")
        console.print("[1] 真实目的 - 揭示NPC对你的真实看法")
        console.print("[2] 幕后对话 - 偷听NPC间的交流")
        console.print("[q] 取消")

        choice = Prompt.ask("选择", choices=["1", "2", "q"])
        if choice == "q":
            return

        if choice == "1":
            # 真实目的
            console.print("\n[bold]NPC真实看法:[/bold]")
            reputation = self.engine.get_player_reputation_network()
            for npc_id, rep in reputation.items():
                name = {"grandmother_s0": "祖母", "traveler_s0": "行者", "wukong_s0": "悟空"}.get(npc_id, npc_id)
                intent = self._get_hidden_intent(npc_id, rep)
                console.print(f"\n[cyan]{name}:[/cyan]")
                console.print(f"  信任度: {rep['trust']:.1f}")
                console.print(f"  真实想法: [dim]{intent}[/dim]")

            self.insight_quota["true_purpose"] -= 1

        elif choice == "2":
            # 幕后对话
            if self.insight_quota["behind_dialogue"] <= 0:
                console.print("[red]幕后对话洞察力已用完[/red]")
                return

            result = self.engine.use_insight_behind_dialogue()
            console.print(Panel(
                f"[magenta]{result.get('revealed', '暂无信息')}[/magenta]",
                title="幕后对话",
                border_style="magenta"
            ))
            self.insight_quota["behind_dialogue"] -= 1

        console.print(f"\n[dim]剩余洞察力: 真实目的={self.insight_quota['true_purpose']} 幕后对话={self.insight_quota['behind_dialogue']}[/dim]")

    def _get_hidden_intent(self, npc_id: str, rep: Dict) -> str:
        """获取NPC的隐藏意图描述"""
        intents = {
            "grandmother_s0": {
                "high_trust": "这孩子值得信任，但我该告诉他多少？",
                "medium_trust": "还需要观察这个孩子的品行...",
                "low_trust": "这个孩子在打听什么？我要小心。",
            },
            "traveler_s0": {
                "high_trust": "也许他就是我要找的人...",
                "medium_trust": "有意思的少年，但还不能完全信任。",
                "low_trust": "他在试探什么？不能被天庭发现。",
            },
            "wukong_s0": {
                "any": "五百年了...那个人会来吗？",
            }
        }

        trust = rep["trust"]
        npc_intents = intents.get(npc_id, {})

        if npc_id == "wukong_s0":
            return npc_intents.get("any", "...")

        if trust > 0.6:
            return npc_intents.get("high_trust", "...")
        elif trust > 0.3:
            return npc_intents.get("medium_trust", "...")
        else:
            return npc_intents.get("low_trust", "...")

    async def _check_npc_network(self):
        """查看NPC网络和信息传播"""
        console.print("\n[bold cyan]NPC社会状态[/bold cyan]\n")

        # 显示当前关系
        self._show_npc_network()

        # 显示信息传播图
        console.print("\n[bold]信息传播网络:[/bold]")
        propagation = self.engine.get_info_propagation_map()

        for npc_id, data in propagation.items():
            name = {"grandmother_s0": "祖母", "traveler_s0": "行者", "wukong_s0": "悟空"}.get(npc_id, npc_id)
            knows = data.get("knows", [])
            console.print(f"\n[cyan]{name}[/cyan] 知道 {len(knows)} 条信息:")

            for info_id in knows[:5]:  # 最多显示5条
                learned_from = data.get("learned_from", {}).get(info_id, "未知")
                from_name = {"grandmother_s0": "祖母", "traveler_s0": "行者", "wukong_s0": "悟空"}.get(learned_from, learned_from)

                if learned_from == npc_id:
                    console.print(f"  • {info_id} [dim](原本就知道)[/dim]")
                else:
                    console.print(f"  • {info_id} [dim](从{from_name}处获知)[/dim]")

    def _show_exit_summary(self):
        """退出总结"""
        console.print("\n" + "=" * 60)
        console.print("[bold]游戏总结[/bold]\n")

        console.print(f"存活回合: {self.turn_count}")
        console.print(f"收集信息: {len(self.player_knowledge)} 条")

        # 显示最终NPC状态
        console.print("\n[dim]最终NPC关系:[/dim]")
        reputation = self.engine.get_player_reputation_network()
        for npc_id, rep in reputation.items():
            name = {"grandmother_s0": "祖母", "traveler_s0": "行者", "wukong_s0": "悟空"}.get(npc_id, npc_id)
            console.print(f"  {name}: 信任 {rep['trust']:.1f}, 怀疑 {rep['suspicion']:.1f}")

        console.print("\n[dim]提示: NPC在你行动后会在后台交流。[/dim]")
        console.print("[dim]你在缝隙中见证了这个世界的运转。[/dim]")


async def main():
    cli = JumpJumpCLIV3()
    await cli.start_game()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]游戏已退出[/yellow]")
