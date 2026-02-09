#!/usr/bin/env python3
"""
Jump Jump CLI v5 - COMPLETE GAME
整合：LLM Agent + 游戏流程（目标、决策、回合限制、洞察力）
"""

import asyncio
import sys
import argparse
sys.path.insert(0, '/Users/dnhb/Desktop/GitHub/My_Projects/jump-jump/src')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from rich.progress import Progress, TaskID

# 导入模块
import importlib.util

spec_agent = importlib.util.spec_from_file_location(
    "llm_npc_agent", "/Users/dnhb/Desktop/GitHub/My_Projects/jump-jump/src/backend/app/llm_npc_agent.py"
)
llm_module = importlib.util.module_from_spec(spec_agent)
spec_agent.loader.exec_module(llm_module)
create_scene_0_agents = llm_module.create_scene_0_agents
create_agents_for_scene = llm_module.create_agents_for_scene
set_llm_config = llm_module.set_llm_config

spec_flow = importlib.util.spec_from_file_location(
    "game_flow", "/Users/dnhb/Desktop/GitHub/My_Projects/jump-jump/src/backend/app/game_flow.py"
)
flow_module = importlib.util.module_from_spec(spec_flow)
spec_flow.loader.exec_module(flow_module)
GameFlowManager = flow_module.GameFlowManager
GamePhase = flow_module.GamePhase

console = Console()


class JumpJumpGame:
    """完整的Jump Jump游戏"""

    # 场景NPC配置
    SCENE_NPCS = {
        "scene-0-wuzhishan": [
            ("grandmother_s0", "祖母", "家人，信任度高"),
            ("traveler_s0", "行者", "神秘过客"),
        ],
        "scene-1-chentangguan": [
            ("nezha_s1", "哪吒", "叛逆少年，面临抉择"),
            ("lijing_s1", "李靖", "陈塘关总兵，忠孝两难"),
            ("yin_furen_s1", "殷夫人", "哪吒母亲，绝望但坚强"),
        ],
    }

    # 场景观察文本
    SCENE_OBSERVATIONS = {
        "scene-0-wuzhishan": [
            "烧焦的桃树残根在风中摇晃，根部隐约有新芽——那是大圣种下的树，还在等待。",
            "岩壁上的刻痕已经风化，但'齐天大圣'四个字的轮廓依稀可辨。",
            "山风带来一丝焦糊味，那是五百年前大闹天宫留下的痕迹。",
            "岩缝中的金属碎片在阳光下闪烁，边缘异常锋利，不知是哪场战斗的遗物。",
        ],
        "scene-1-chentangguan": [
            "陈塘关的城墙高耸，但守军的脸上写满忧虑。",
            "东海方向乌云密布，龙王的威胁如同悬在头顶的利剑。",
            "总兵府门前聚集着焦急的百姓，他们不知道灾难即将降临。",
            "哪吒的房间里传来器物破碎的声音，夹杂着压抑的抽泣。",
        ],
    }

    def __init__(self):
        self.agent_pool = None
        self.flow_manager = None
        self.current_scene_info = None
        self.current_scene_id = None

    async def start(self):
        """开始游戏"""
        self._show_title()

        # 初始化
        console.print("[dim]加载游戏流程...[/dim]")
        self.flow_manager = GameFlowManager()
        console.print("[green]✓ 游戏流程已加载[/green]")

        # 开始场景0
        self.current_scene_id = "scene-0-wuzhishan"
        self.current_scene_info = self.flow_manager.start_scene(self.current_scene_id)

        # 加载场景对应的NPC
        console.print("[dim]初始化NPC Agents...[/dim]")
        self.agent_pool = create_agents_for_scene(self.current_scene_id)
        console.print(f"[green]✓ Agents已激活: {self.current_scene_info['name']}[/green]\n")

        self._show_scene_intro()

        # 游戏主循环
        await self._game_loop()

    def _show_title(self):
        console.print(Panel.fit(
            "[bold cyan]Jump Jump - 悟空传[/bold cyan]\n"
            "[dim]CLI v5 - 完整版[/dim]\n"
            "[dim]LLM Agent × 目标驱动 × 决策系统[/dim]",
            border_style="cyan"
        ))

    def _show_scene_intro(self):
        """显示场景介绍"""
        scene = self.current_scene_info
        console.print(Panel(
            f"[bold yellow]{scene['name']}[/bold yellow]\n\n"
            f"[white]{scene['description']}[/white]\n\n"
            f"[dim]目标：{', '.join(scene['goals'])}[/dim]",
            border_style="yellow",
            title="当前场景"
        ))

    async def _game_loop(self):
        """游戏主循环"""
        while True:
            # 显示当前状态
            self._show_game_status()

            # 检查当前阶段
            if self.flow_manager.current_phase == GamePhase.EXPLORATION:
                await self._exploration_phase()
            elif self.flow_manager.current_phase == GamePhase.DECISION:
                await self._decision_phase()

            # 检查场景是否完成
            if self._check_scene_complete():
                if not await self._handle_scene_transition():
                    break

    def _show_game_status(self):
        """显示游戏状态"""
        state = self.flow_manager.state

        # 创建状态面板
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="center")
        grid.add_column(justify="right")

        turn_info = f"回合 {self.flow_manager.turn_count}/{self.flow_manager.max_turns_per_scene}"
        info_count = f"信息 {len(state['collected_info'])}"
        insight_info = f"洞察力 {state['insights_used']}"

        grid.add_row(turn_info, info_count, insight_info)
        console.print(grid)
        console.print("─" * 50)

    async def _exploration_phase(self):
        """探索阶段 - 自由对话"""
        console.print("\n[bold cyan]探索阶段[/bold cyan]")

        # 获取当前场景的NPC列表
        npc_list = self.SCENE_NPCS.get(self.current_scene_id, [])

        # 显示可用行动
        console.print("\n[bold]选择行动:[/bold]")

        # 动态显示NPC选项
        choices = []
        for i, (npc_id, npc_name, npc_desc) in enumerate(npc_list, 1):
            console.print(f"  [{i}] 与{npc_name}对话 ({npc_desc})")
            choices.append(str(i))

        console.print(f"  [{len(npc_list) + 1}] 观察环境")
        console.print(f"  [{len(npc_list) + 2}] 使用洞察力")
        console.print(f"  [{len(npc_list) + 3}] 查看已收集信息")
        console.print("  [q] 退出游戏")

        choices.extend([str(len(npc_list) + 1), str(len(npc_list) + 2), str(len(npc_list) + 3), "q"])
        choice = Prompt.ask("选择", choices=choices)

        if choice == "q":
            raise KeyboardInterrupt
        elif choice in [str(i) for i in range(1, len(npc_list) + 1)]:
            idx = int(choice) - 1
            npc_id, npc_name, _ = npc_list[idx]
            await self._talk_to_npc(npc_id, npc_name)
        elif choice == str(len(npc_list) + 1):
            await self._observe()
        elif choice == str(len(npc_list) + 2):
            await self._use_insight()
        elif choice == str(len(npc_list) + 3):
            self._show_collected_info()

    async def _talk_to_npc(self, npc_id: str, npc_name: str):
        """与NPC对话"""
        agent = self.agent_pool.get_agent(npc_id)
        if not agent:
            console.print(f"[red]找不到NPC: {npc_name}[/red]")
            return

        console.print(f"\n[bold cyan]开始与 {npc_name} 对话[/bold cyan]")
        console.print("[dim]输入 'exit' 结束对话[/dim]\n")

        # 显示当前信任度
        trust = agent.state.trust_toward_player
        trust_desc = "至亲" if trust > 0.8 else "家人" if trust > 0.6 else "熟悉" if trust > 0.4 else "陌生"
        console.print(f"[dim]当前关系: {trust_desc} (信任度: {trust:.1f})[/dim]")

        # 对话循环（每轮游戏可以进行多次对话）
        exchanges = 0
        max_exchanges = 3  # 每次行动最多3轮对话

        while exchanges < max_exchanges:
            message = Prompt.ask("你说")

            if message.lower() in ["exit", "退出", "再见"]:
                break

            # LLM生成回复
            console.print(f"[dim]{npc_name}正在思考...[/dim]")
            result = agent.generate_response(message)

            # 显示回复
            console.print(Panel(
                f"[white]{result['observable']}[/white]",
                title=npc_name,
                border_style="blue"
            ))

            # 处理游戏机制
            action_data = {
                "npc_id": npc_id,
                "trust_change": result.get("trust_change", 0),
            }

            # 如果NPC愿意分享信息
            if result.get("wants_to_share"):
                for info_id in result['wants_to_share']:
                    if info_id in agent.state.known_info:
                        info_content = agent.state.known_info[info_id]['content']
                        action_data.setdefault("collected_info", []).append(info_id)
                        console.print(f"\n[green]✓ 获得信息: {info_content[:50]}...[/green]")

            # 更新游戏状态
            flow_result = self.flow_manager.process_turn("dialogue", action_data)

            # 显示事件
            if flow_result.get("events"):
                for event in flow_result["events"]:
                    console.print(f"\n[magenta]【事件】{event['content']}[/magenta]")

            exchanges += 1

            # 检查是否触发决策
            if flow_result.get("show_decision"):
                console.print("\n[yellow]【重要】你需要做出一个决定...[/yellow]")
                break

        # 结束对话，推进一回合
        if exchanges > 0:
            console.print(f"\n[dim]对话结束，推进{exchanges}轮[/dim]")

    async def _observe(self):
        """观察环境"""
        console.print("\n[dim]你仔细观察周围环境...[/dim]")

        # 获取当前场景的观察文本
        observations = self.SCENE_OBSERVATIONS.get(self.current_scene_id, [
            "周围一片寂静，似乎有什么东西在暗处注视着你。"
        ])

        import random
        obs = random.choice(observations)
        console.print(Panel(f"[cyan]{obs}[/cyan]", title="观察", border_style="cyan"))

        # 可能获得观察信息
        if random.random() < 0.3:
            info_id = f"environment_observation_{self.current_scene_id}"
            if info_id not in self.flow_manager.state["collected_info"]:
                self.flow_manager.state["collected_info"].append(info_id)
                console.print("[green]✓ 记录了环境线索[/green]")

        # 推进回合
        self.flow_manager.process_turn("observe", {})

    async def _use_insight(self):
        """使用洞察力"""
        if self.flow_manager.state["insights_used"] >= 3:
            console.print("[red]本场景洞察力已用完[/red]")
            return

        console.print("\n[bold yellow]使用洞察力[/bold yellow]")
        console.print("[1] 真实目的 - 揭示NPC内心")
        console.print("[2] 幕后洞察 - 发现隐藏信息")

        choice = Prompt.ask("选择", choices=["1", "2", "q"])

        # 获取当前场景的NPC列表
        npc_list = self.SCENE_NPCS.get(self.current_scene_id, [])

        if choice == "1":
            console.print("\n[bold]NPC真实内心:[/bold]")
            for npc_id, npc_name, _ in npc_list:
                agent = self.agent_pool.get_agent(npc_id)
                if agent:
                    console.print(f"\n[cyan]{agent.state.name}:[/cyan]")
                    console.print(f"  信任度: {agent.state.trust_toward_player:.2f}")
                    console.print(f"  情绪: {agent.state.emotional_state}")
                    if agent.state.dialogue_history:
                        last = agent.state.dialogue_history[-1]
                        console.print(f"  最近想法: [dim]{last.content[:60]}...[/dim]")

        elif choice == "2":
            console.print("\n[magenta]【洞察】[/magenta]")
            console.print("[dim]你静下心来，感知周围的微妙信息...[/dim]")

            # 场景特定的洞察文本
            scene_insights = {
                "scene-0-wuzhishan": [
                    "你注意到祖母时不时望向山体深处，眼中闪过担忧。",
                    "行者似乎在躲避什么，他的目光总是扫向天空。",
                    "岩壁上的某块石头看起来不自然，似乎被人动过。",
                ],
                "scene-1-chentangguan": [
                    "哪吒眼中藏着绝望，他在强装坚强。",
                    "李靖独自站在城墙上，背影佝偻，似乎一夜苍老。",
                    "殷夫人偷偷抹泪，却在你看过来时强颜欢笑。",
                ],
            }
            insights = scene_insights.get(self.current_scene_id, ["似乎有什么重要的事情即将发生..."])
            import random
            console.print(f"\n[italic]{random.choice(insights)}[/italic]")

        self.flow_manager.state["insights_used"] += 1
        console.print(f"\n[dim]剩余洞察力: {3 - self.flow_manager.state['insights_used']}[/dim]")

    def _show_collected_info(self):
        """显示已收集信息"""
        info_list = self.flow_manager.state["collected_info"]

        if not info_list:
            console.print("\n[yellow]还没有收集到任何信息。[/yellow]")
            return

        console.print(f"\n[bold]已收集信息 ({len(info_list)}条):[/bold]")

        # 获取信息详情
        for info_id in info_list:
            content = self._get_info_content(info_id)
            console.print(f"\n  [cyan]• {content}[/cyan]")

    def _get_info_content(self, info_id: str) -> str:
        """获取信息内容"""
        # 从当前场景所有agent的known_info中查找
        npc_list = self.SCENE_NPCS.get(self.current_scene_id, [])
        for npc_id, _, _ in npc_list:
            agent = self.agent_pool.get_agent(npc_id)
            if agent and info_id in agent.state.known_info:
                return agent.state.known_info[info_id].get("content", info_id)

        # 默认返回
        info_map = {
            "environment_observation_scene-0-wuzhishan": "五指山环境观察记录",
            "environment_observation_scene-1-chentangguan": "陈塘关环境观察记录",
            "family_bond": "与家人的羁绊",
            "burden_of_knowledge": "知识的重担",
            "curiosity": "好奇心",
        }
        return info_map.get(info_id, info_id)

    async def _decision_phase(self):
        """决策阶段"""
        decision = self.flow_manager._get_next_decision()

        if not decision:
            self.flow_manager.current_phase = GamePhase.EXPLORATION
            return

        console.print(f"\n[bold red]═══ 决策点 ═══[/bold red]")
        console.print(Panel(
            f"[bold]{decision['title']}[/bold]\n\n"
            f"{decision['description']}",
            border_style="red"
        ))

        console.print("\n[bold]你的选择:[/bold]")
        for i, choice in enumerate(decision['choices'], 1):
            console.print(f"  [{i}] {choice['text']}")

        choice_idx = IntPrompt.ask(
            "选择",
            choices=[str(i) for i in range(1, len(decision['choices']) + 1)]
        )

        selected_choice = decision['choices'][int(choice_idx) - 1]

        # 应用决策
        result = self.flow_manager.make_decision(
            decision['decision_id'],
            selected_choice['id']
        )

        if result['success']:
            console.print(f"\n[green]你选择了: {result['choice_text']}[/green]")
            console.print("[dim]这个选择将影响后续剧情...[/dim]")

    def _check_scene_complete(self) -> bool:
        """检查场景是否完成"""
        return self.flow_manager._check_scene_complete()

    async def _handle_scene_transition(self) -> bool:
        """处理场景切换"""
        reason = self.flow_manager._get_completion_reason()

        console.print(f"\n[bold yellow]═══ 场景结束 ═══[/bold yellow]")

        if reason == "decision_made":
            console.print("[green]你已做出关键抉择，准备进入下一章...[/green]")
        elif reason == "turns_exhausted":
            console.print("[yellow]时间流逝，夜幕降临，你需要做出最后的决定...[/yellow]")

        # 显示场景总结
        summary = self.flow_manager.get_game_summary()

        console.print("\n[bold]本章总结:[/bold]")
        console.print(f"  收集信息: {len(summary['collected_info'])} 条")
        console.print(f"  做出的决策: {len(summary['decisions_made'])} 个")
        console.print(f"  解锁的秘密: {len(summary['secrets_unlocked'])} 个")

        # 获取下一章
        next_scene = self.flow_manager.get_next_scene()

        if next_scene == "ending":
            console.print("\n[bold cyan]═══ 游戏结束 ═══[/bold cyan]")
            return False

        # 询问是否继续
        continue_game = Prompt.ask(
            f"\n准备进入下一章？",
            choices=["y", "n"],
            default="y"
        )

        if continue_game == "y":
            # 更新当前场景ID并重新加载NPC
            self.current_scene_id = next_scene
            self.current_scene_info = self.flow_manager.start_scene(next_scene)

            # 重新加载新场景的NPC
            console.print(f"[dim]加载新场景NPC...[/dim]")
            self.agent_pool = create_agents_for_scene(self.current_scene_id)
            console.print(f"[green]✓ {self.current_scene_info['name']} 的角色已激活[/green]\n")

            self._show_scene_intro()
            return True
        else:
            return False


def main():
    parser = argparse.ArgumentParser(description='Jump Jump v5 - Complete Game')
    parser.add_argument('--api-key', type=str, help='OpenAI API Key')
    parser.add_argument('--base-url', type=str, help='API Base URL')
    parser.add_argument('--model', type=str, default='gpt-3.5-turbo', help='Model name')
    args = parser.parse_args()

    if args.api_key or args.base_url or args.model:
        set_llm_config(api_key=args.api_key, base_url=args.base_url, model=args.model)

    game = JumpJumpGame()
    try:
        asyncio.run(game.start())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]游戏已退出[/yellow]")


if __name__ == "__main__":
    main()
