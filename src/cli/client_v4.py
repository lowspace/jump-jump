#!/usr/bin/env python3
"""
Jump Jump CLI v4 - TRUE AGENT VERSION
NPCs understand player input and generate contextual responses
"""

import asyncio
import sys
sys.path.insert(0, '/Users/dnhb/Desktop/GitHub/My_Projects/jump-jump/src')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt

from backend.app.llm_npc_agent import create_scene_0_agents, LLMNPCAgentPool

console = Console()


class JumpJumpCLIV4:
    """真正的Agent版本CLI - NPC理解并生成回复"""

    def __init__(self):
        self.agent_pool: LLMNPCAgentPool = None
        self.player_knowledge = []
        self.insight_quota = {"true_purpose": 2, "behind_dialogue": 2}
        self.turn_count = 0

    async def start_game(self):
        """开始游戏"""
        self._show_title()

        # 初始化真正的Agent
        console.print("[dim]正在初始化NPC Agents...[/dim]")
        self.agent_pool = create_scene_0_agents()
        console.print("[green]✓ Agents已激活[/green]\n")

        self._show_background()
        self._show_npc_states()

        # 主循环
        await self._main_loop()

    def _show_title(self):
        console.print(Panel.fit(
            "[bold cyan]Jump Jump - 悟空传[/bold cyan]\n"
            "[dim]CLI v4 - 真正的Agent交互[/dim]\n"
            "[dim]NPC理解你的话语 × 生成情境化回复[/dim]",
            border_style="cyan"
        ))

    def _show_background(self):
        content = Text()
        content.append("序章：五指山·尘埃\n\n", style="yellow")
        content.append("你是五指山附近的少年樵夫。\n", style="white")
        content.append("这次，你面前的不是模板，而是真正的'人'——\n", style="dim")
        content.append("她们会理解你的话语，根据信任度和情境生成回复。\n\n", style="dim")
        content.append("试着用自然的语言与她们交流。\n", style="green")

        console.print(Panel(content, border_style="yellow", title="背景"))

    def _show_npc_states(self):
        """显示NPC当前状态"""
        console.print("\n[bold cyan]NPC状态[/bold cyan]")

        table = Table(show_header=True, header_style="bold")
        table.add_column("NPC")
        table.add_column("信任你")
        table.add_column("情绪")
        table.add_column("特点")

        for npc_id in ["grandmother_s0", "traveler_s0"]:
            agent = self.agent_pool.get_agent(npc_id)
            if agent:
                state = agent.state
                trust_bar = "█" * int(state.trust_toward_player * 10) + "░" * (10 - int(state.trust_toward_player * 10))

                desc = {
                    "grandmother_s0": "慈祥但警觉，知道民间传说",
                    "traveler_s0": "神秘修行者，寻找徒弟"
                }.get(npc_id, "")

                table.add_row(
                    state.name,
                    f"{trust_bar} {state.trust_toward_player:.1f}",
                    state.emotional_state,
                    desc
                )

        console.print(table)

    async def _main_loop(self):
        while True:
            self.turn_count += 1
            console.print(f"\n[dim]回合 {self.turn_count}[/dim]")

            choice = self._show_menu()

            if choice == "q":
                break
            elif choice == "1":
                await self._talk_to_npc()
            elif choice == "2":
                await self._observe()
            elif choice == "3":
                self._check_knowledge()
            elif choice == "4":
                self._show_npc_states()
            elif choice == "5":
                await self._use_insight()

    def _show_menu(self) -> str:
        console.print("\n" + "─" * 50)
        console.print("[bold cyan]请选择行动:[/bold cyan]\n")
        console.print("  [1] 与NPC对话 (自由输入)")
        console.print("  [2] 观察环境")
        console.print("  [3] 查看已知信息")
        console.print("  [4] 查看NPC状态")
        console.print("  [5] 使用洞察力")
        console.print("  [q] 退出")
        console.print("─" * 50)
        return Prompt.ask("选择", choices=["1", "2", "3", "4", "5", "q"])

    async def _talk_to_npc(self):
        """与NPC自由对话"""
        console.print("\n[bold]选择与谁对话:[/bold]")
        console.print("  [1] 祖母 (慈祥的老妇人)")
        console.print("  [2] 行者 (神秘的过路人)")

        choice = Prompt.ask("选择", choices=["1", "2", "q"])
        if choice == "q":
            return

        npc_id = "grandmother_s0" if choice == "1" else "traveler_s0"
        npc_name = "祖母" if choice == "1" else "行者"

        # 获取Agent
        agent = self.agent_pool.get_agent(npc_id)
        if not agent:
            console.print("[red]NPC未找到[/red]")
            return

        console.print(f"\n[bold cyan]开始与 {npc_name} 对话[/bold cyan]")
        console.print("[dim]输入 'exit' 结束对话[/dim]\n")

        # 对话循环
        while True:
            # 玩家输入（自由文本）
            message = Prompt.ask("你说")

            if message.lower() in ["exit", "退出", "再见"]:
                console.print(f"\n[dim]你结束了与{npc_name}的对话。[/dim]")
                break

            # Agent生成回复
            console.print(f"[dim]{npc_name}正在思考...[/dim]")

            try:
                result = agent.generate_response(message)

                # 显示NPC回复
                console.print(Panel(
                    f"[white]{result['observable']}[/white]",
                    title=f"{npc_name}",
                    border_style="blue"
                ))

                # 显示信任度变化
                if result.get('trust_change', 0) != 0:
                    change = result['trust_change']
                    color = "green" if change > 0 else "red"
                    console.print(f"[{color}]信任度变化: {change:+.2f}[/{color}]")

                # 检查是否获得信息
                if result.get('wants_to_share'):
                    for info_id in result['wants_to_share']:
                        if info_id in agent.state.known_info and info_id not in [k['id'] for k in self.player_knowledge]:
                            info = agent.state.known_info[info_id]
                            self.player_knowledge.append({
                                'id': info_id,
                                'content': info['content'],
                                'from': npc_name
                            })
                            console.print(f"\n[green]✓ 获得信息: {info['content'][:50]}...[/green]")

                # 显示隐藏意图（调试用，正式版需要insight才能看）
                # console.print(f"[dim]【隐藏】{result['hidden_intent']}[/dim]")

            except Exception as e:
                console.print(f"[red]生成回复时出错: {e}[/red]")

    async def _observe(self):
        """观察环境"""
        console.print("\n[dim]你仔细观察周围环境...[/dim]")

        observations = [
            "烧焦的桃树残根在风中微微摇晃，根部隐约有新芽。",
            "岩壁上的刻痕已经风化，但'齐天大圣'四个字的轮廓依稀可辨。",
            "山风带来一丝焦糊味，那是五百年前大战留下的痕迹。",
            "岩缝中的金属碎片在阳光下闪烁，边缘异常锋利。",
        ]

        import random
        obs = random.choice(observations)
        console.print(Panel(f"[cyan]{obs}[/cyan]", title="观察", border_style="cyan"))

    def _check_knowledge(self):
        """查看已知信息"""
        if not self.player_knowledge:
            console.print("\n[yellow]你还没有收集到任何信息。[/yellow]")
            return

        console.print("\n[bold]已知信息:[/bold]")
        for info in self.player_knowledge:
            console.print(f"\n[cyan]• {info['content']}[/cyan]")
            console.print(f"  [dim]来源: {info['from']}[/dim]")

    async def _use_insight(self):
        """使用洞察力"""
        console.print("\n[bold yellow]使用洞察力[/bold yellow]")
        console.print("[1] 真实目的 - 揭示NPC的隐藏意图")
        console.print("[q] 取消")

        choice = Prompt.ask("选择", choices=["1", "q"])
        if choice == "q":
            return

        if choice == "1":
            console.print("\n[bold]NPC真实意图:[/bold]")
            for npc_id in ["grandmother_s0", "traveler_s0"]:
                agent = self.agent_pool.get_agent(npc_id)
                if agent and agent.state.dialogue_history:
                    # 获取最后一次的隐藏意图（简化版）
                    last_context = agent.state.dialogue_history[-1] if agent.state.dialogue_history else None
                    if last_context:
                        console.print(f"\n[cyan]{agent.state.name}:[/cyan]")
                        console.print(f"  情绪: {agent.state.emotional_state}")
                        console.print(f"  信任度: {agent.state.trust_toward_player:.2f}")
                        console.print(f"  最近在想: [dim]{last_context.content[:50]}...[/dim]")

            self.insight_quota["true_purpose"] -= 1
            console.print(f"\n[dim]剩余真实目的洞察力: {self.insight_quota['true_purpose']}[/dim]")


def main():
    cli = JumpJumpCLIV4()
    try:
        asyncio.run(cli.start_game())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]游戏已退出[/yellow]")


if __name__ == "__main__":
    main()
