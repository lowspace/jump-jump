#!/usr/bin/env python3
"""
Jump Jump CLI v5 - COMPLETE GAME
整合：LLM Agent + 游戏流程（目标、决策、回合限制、洞察力）
"""

import asyncio
import sys
import argparse
from pathlib import Path

# 用相对路径计算 src/ 目录
_src_dir = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, _src_dir)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from rich.progress import Progress, TaskID

# 导入模块
import importlib.util

_app_dir = Path(__file__).resolve().parent.parent / "backend" / "app"

spec_agent = importlib.util.spec_from_file_location(
    "llm_npc_agent", str(_app_dir / "llm_npc_agent.py")
)
llm_module = importlib.util.module_from_spec(spec_agent)
spec_agent.loader.exec_module(llm_module)
create_scene_0_agents = llm_module.create_scene_0_agents
create_agents_for_scene = llm_module.create_agents_for_scene
set_llm_config = llm_module.set_llm_config

spec_flow = importlib.util.spec_from_file_location(
    "game_flow", str(_app_dir / "game_flow.py")
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
        "scene-2-tianhe": [
            ("tianpeng_s2", "天蓬元帅", "天河统帅，为爱即将被贬"),
            ("juanlian_s2", "卷帘大将", "天庭安全系统的眼睛"),
            ("xuanming_s2", "宣明", "灵蕴部主管，完美的官僚"),
        ],
        "scene-3-huaguoshan": [
            ("laohou_s3", "老猴", "最年长的猴子，活过两个时代"),
            ("tietou_s3", "铁头", "年轻猴将，用愤怒掩盖恐惧"),
            ("tianbing_s3", "天兵巡逻队长", "执行命令的人"),
        ],
        "scene-4-lingtai": [
            ("tangseng_s4", "唐僧", "取经人，知道真相仍选择前行"),
            ("huikong_s4", "慧空", "资深抄经僧，已看过无字真经"),
            ("jianyuan_s4", "监院", "寺院管理者，体制的执行者"),
        ],
    }

    # 场景观察文本
    SCENE_OBSERVATIONS = {
        "scene-0-wuzhishan": [
            "烧焦的桃树残根在风中摇晃，根部隐略有新芽——那是大圣种下的树，还在等待。",
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
        "scene-2-tianhe": [
            "天河的水流在深夜发出异常的微光，那是灵蕴传输的痕迹。",
            "天蓬元帅的府邸灯火通明，他在做最后的巡视准备。",
            "灵蕴部的档案室深锁，账目异常就藏在那些数字背后。",
            "卷帘大将的身影在走廊尽头一闪而过，他永远在观察。",
        ],
        "scene-3-huaguoshan": [
            "水帘洞深处的石头宝座落满灰尘，但没有猴子敢坐上去。",
            "一根桃木棍搁在宝座旁的石缝里，那是大王随手削的。",
            "山顶最后一棵桃树在风中摇晃，所有桃树都被烧了，只有这棵活着。",
            "天兵的旗帜在远处的山脊上若隐若现，他们在等待命令。",
        ],
        "scene-4-lingtai": [
            "抄经房的油灯彻夜不熄，有人在抄写空白的经卷。",
            "后山小径上有个人在独自打坐，穿着最普通的僧袍。",
            "慧空师兄的经卷永远工整，但他已经十五年没有真正'读'过经了。",
            "监院的脚步声在走廊回响，他在检查每个人的进度。",
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
        tp_used = state.get("insights_true_purpose_used", 0)
        bd_used = state.get("insights_behind_dialogue_used", 0)
        insight_info = f"洞察 真实目的{tp_used}/2 幕后{bd_used}/2"

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
        """使用洞察力（2x真实目的 + 2x幕后对话）"""
        state = self.flow_manager.state
        tp_used = state.get("insights_true_purpose_used", 0)
        bd_used = state.get("insights_behind_dialogue_used", 0)

        if tp_used >= 2 and bd_used >= 2:
            console.print("[red]本场景洞察力已全部用完（真实目的 2/2，幕后 2/2）[/red]")
            return

        console.print("\n[bold yellow]使用洞察力[/bold yellow]")
        tp_label = f"真实目的 - 揭示NPC隐藏意图 [{'已用完' if tp_used >= 2 else f'剩余{2 - tp_used}次'}]"
        bd_label = f"幕后对话 - 发现隐藏信息 [{'已用完' if bd_used >= 2 else f'剩余{2 - bd_used}次'}]"
        console.print(f"[1] {tp_label}")
        console.print(f"[2] {bd_label}")

        choice = Prompt.ask("选择", choices=["1", "2", "q"])
        if choice == "q":
            return

        # 获取当前场景的NPC列表
        npc_list = self.SCENE_NPCS.get(self.current_scene_id, [])

        if choice == "1":
            if tp_used >= 2:
                console.print("[red]真实目的洞察已用完[/red]")
                return
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
            state["insights_true_purpose_used"] = tp_used + 1
            state["insights_used"] += 1
            console.print(f"\n[dim]真实目的剩余: {2 - tp_used - 1}/2[/dim]")

        elif choice == "2":
            if bd_used >= 2:
                console.print("[red]幕后对话洞察已用完[/red]")
                return
            console.print("\n[magenta]【洞察】[/magenta]")
            console.print("[dim]你静下心来，感知周围的微妙信息...[/dim]")

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
                "scene-2-tianhe": [
                    "天蓬元帅在没人注意的时候，会拿出一块玉佩默默抚摸。",
                    "卷帘大将看你的眼神不像看一个人，更像看一个待分类的标签。",
                    "宣明主管的案头放着一份被封存的旧报告，落款是十五年前。",
                ],
                "scene-3-huaguoshan": [
                    "老猴在深夜会对着大王留下的木棍发呆，但他从不敢碰它。",
                    "铁头每次听到天兵的号角都会抖一下，但他不会让你看见。",
                    "天兵队长巡逻时会刻意绕开有幼猴玩耍的地方。",
                ],
                "scene-4-lingtai": [
                    "唐僧的问题看似随意，但每一个都直指你内心最不敢想的地方。",
                    "慧空师兄抄写时从不看经卷，他的眼睛一直盯着笔尖。",
                    "监院的训话总是千篇一律，但今天他多看了你一眼。",
                ],
            }
            insights = scene_insights.get(self.current_scene_id, ["似乎有什么重要的事情即将发生..."])
            import random
            console.print(f"\n[italic]{random.choice(insights)}[/italic]")
            state["insights_behind_dialogue_used"] = bd_used + 1
            state["insights_used"] += 1
            console.print(f"\n[dim]幕后对话剩余: {2 - bd_used - 1}/2[/dim]")

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
            self._show_impact_report()
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


    def _show_impact_report(self):
        """显示影响力报告"""
        report = self.flow_manager.generate_impact_report()

        console.print("\n\n")
        console.print(Panel.fit(
            "[bold cyan]影响力报告[/bold cyan]\n"
            "[dim]你的决策在西游世界中产生的涟漪[/dim]",
            border_style="cyan",
            padding=(1, 4)
        ))

        # 统计行
        stats_grid = Table.grid(expand=True)
        stats_grid.add_column(justify="center")
        stats_grid.add_column(justify="center")
        stats_grid.add_column(justify="center")
        stats_grid.add_column(justify="center")
        stats_grid.add_row(
            f"[bold]{len(report['scenes_visited'])}[/bold] 个场景",
            f"[bold]{len(report['decisions_detail'])}[/bold] 个决策",
            f"[bold]{report['collected_info_count']}[/bold] 条信息",
            f"[bold]{report['insights_total_used']}[/bold] 次洞察",
        )
        console.print(stats_grid)
        console.print()

        # 逐场景涟漪
        for ripple in report["scene_ripples"]:
            console.print(Panel(
                f"[dim]你的选择：[/dim][yellow]{ripple['choice_text']}[/yellow]\n\n"
                f"[italic]{ripple['ripple']}[/italic]",
                title=f"[bold]{ripple['scene_name']}[/bold]",
                border_style="yellow",
                padding=(1, 2)
            ))

        # 行为画像
        profile = report["profile"]
        profile_table = Table.grid(padding=(0, 2))
        profile_table.add_column(justify="right", style="dim", min_width=8)
        profile_table.add_column(min_width=30)

        def _bar(value: float) -> str:
            filled = int(value * 20)
            return "[cyan]" + "█" * filled + "[/cyan]" + "[dim]░[/dim]" * (20 - filled) + f" {value:.0%}"

        profile_table.add_row("理想主义", _bar(profile["idealism_index"]))
        profile_table.add_row("变革参与", _bar(profile["change_participation"]))
        profile_table.add_row("记忆守护", _bar(profile["memory_guardian_index"]))

        console.print(Panel(
            f"[bold yellow]{profile['label']}[/bold yellow]",
            title="[bold]行为画像[/bold]",
            border_style="magenta",
            padding=(0, 2)
        ))
        console.print(profile_table)
        console.print()

        # 结尾叙事
        console.print(Panel(
            f"[italic]{report['ending_narrative']}[/italic]\n\n"
            f"[bold cyan]{report['closing']}[/bold cyan]",
            border_style="cyan",
            padding=(1, 4)
        ))
        console.print()


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
