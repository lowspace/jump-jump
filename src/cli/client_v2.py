#!/usr/bin/env python3
"""
Jump Jump CLI v2 - 重构的交互系统
核心：信息分层 + 对话深度 + 缝隙参与
"""

import asyncio
import json
import random
import sys
from typing import Optional, Dict, List, Set
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

console = Console()


class InfoLevel(Enum):
    """信息层级"""
    PUBLIC = "public"      # 公开信息，任何人知道
    PRIVATE = "private"    # 私密信息，特定NPC知道
    HIDDEN = "hidden"      # 隐藏信息，需要洞察力
    SECRET = "secret"      # 机密信息，多条件触发


class DialogueDepth(Enum):
    """对话深度"""
    SURFACE = 1    # 表面寒暄
    CASUAL = 2     # 随意交谈
    DEEP = 3       # 深入询问（可能引起警觉）
    PROBE = 4      # 试探/施压（高风险高回报）


@dataclass
class Information:
    """信息单元"""
    info_id: str
    content: str
    level: InfoLevel
    source: str  # 信息来源NPC
    reliability: float  # 0-1 可靠性
    contradictions: List[str] = field(default_factory=list)  # 与其他信息的矛盾点
    implications: List[str] = field(default_factory=list)  # 暗示/线索


@dataclass
class NPCState:
    """NPC 动态状态"""
    npc_id: str
    trust_toward_player: float = 0.5  # 0-1 信任度
    alert_level: float = 0.0  # 警觉度（过高会拒绝深入对话）
    emotional_state: str = "neutral"
    known_info_ids: Set[str] = field(default_factory=set)  # NPC知道的信息
    shared_info_ids: Set[str] = field(default_factory=set)  # 已分享给玩家的信息
    player_knows_about: Set[str] = field(default_factory=set)  # 玩家知道这个NPC知道什么


class InformationLedger:
    """信息账本 - 全局信息管理系统"""

    def __init__(self):
        self.information_db: Dict[str, Information] = {}
        self.player_knowledge: Set[str] = set()  # 玩家已获取的信息ID
        self.npc_states: Dict[str, NPCState] = {}

        # Scene 0 - 五指山的信息库
        self._init_scene_0_info()

        # 环境感知信息(与悟空相关，通过观察获得)
        self._init_environmental_info()

    def _init_scene_0_info(self):
        """初始化Scene 0的信息"""
        # 公开信息
        self.add_info(Information(
            info_id="INFO_S0_PEACH_TREE",
            content="五指山上有一株烧焦的桃树残根，传说与齐天大圣有关",
            level=InfoLevel.PUBLIC,
            source="common_knowledge",
            reliability=0.7
        ))

    def _init_environmental_info(self):
        """初始化环境感知信息(通过观察和洞察力获取)"""
        # 与悟空相关的环境感知信息
        self.add_info(Information(
            info_id="INFO_S0_WUKONG_BREATH",
            content="山体深处传来如同呼吸般的低频声响，似乎来自某个巨大的存在",
            level=InfoLevel.PRIVATE,  # 需要观察才能发现
            source="environment",
            reliability=0.8
        ))

        self.add_info(Information(
            info_id="INFO_S0_WUKONG_MOVEMENT",
            content="岩壁偶尔会震动，仿佛山体本身在挣扎",
            level=InfoLevel.PRIVATE,
            source="environment",
            reliability=0.9
        ))

        self.add_info(Information(
            info_id="INFO_S0_WUKONG_SIGH",
            content="风中有时会传来一声叹息，来自地下深处",
            level=InfoLevel.HIDDEN,  # 难以察觉
            source="environment",
            reliability=0.85
        ))

        self.add_info(Information(
            info_id="INFO_S0_WUKONG_SHADOW",
            content="夕阳西下时，岩壁上的刻痕影子像一只被压在山下的猴子",
            level=InfoLevel.HIDDEN,
            source="environment",
            reliability=0.7
        ))

        self.add_info(Information(
            info_id="INFO_S0_INSCRIPTION",
            content="岩壁上有模糊的字迹，据说是'齐天大圣'四个字",
            level=InfoLevel.PUBLIC,
            source="common_knowledge",
            reliability=0.6
        ))

        # 祖母的私密信息
        self.add_info(Information(
            info_id="INFO_S0_GRANDMA_STORY_1",
            content="祖母知道一个关于剔骨还子的故事，那个孩子最后没有复活",
            level=InfoLevel.PRIVATE,
            source="grandmother_s0",
            reliability=0.9,
            implications=["INFO_S1_NEZHA_FATE"]
        ))

        self.add_info(Information(
            info_id="INFO_S0_GRANDMA_STORY_2",
            content="祖母听说过天河的账目，天上有人在偷灵蕴",
            level=InfoLevel.PRIVATE,
            source="grandmother_s0",
            reliability=0.8,
            implications=["INFO_S2_LEDGER_SECRET"]
        ))

        # 行者的隐藏信息
        self.add_info(Information(
            info_id="INFO_S0_TRAVELER_IDENTITY",
            content="行者其实是金蝉子转世，正在寻找他的大徒弟",
            level=InfoLevel.HIDDEN,
            source="traveler_s0",
            reliability=0.95,
            contradictions=["INFO_S0_TRAVELER_APPEARANCE"]
        ))

        # 悟空的机密信息（需要特殊条件触发）
        self.add_info(Information(
            info_id="INFO_S0_WUKONG_WHISPER",
            content="悟空能听到山上的声音，那是他在等一个人",
            level=InfoLevel.SECRET,
            source="wukong_s0",
            reliability=1.0,
            implications=["INFO_S3_WUKONG_WAITING"]
        ))

    def add_info(self, info: Information):
        self.information_db[info.info_id] = info

    def get_info(self, info_id: str) -> Optional[Information]:
        return self.information_db.get(info_id)

    def player_learns(self, info_id: str) -> bool:
        """玩家获取信息"""
        if info_id in self.information_db:
            self.player_knowledge.add(info_id)
            return True
        return False

    def get_npc_available_info(self, npc_id: str, depth: DialogueDepth) -> List[Information]:
        """获取NPC在特定对话深度下愿意分享的信息"""
        npc_state = self.npc_states.get(npc_id)
        if not npc_state:
            return []

        available = []
        for info_id in npc_state.known_info_ids:
            info = self.information_db.get(info_id)
            if not info:
                continue

            # 根据信息层级和对话深度判断可获取性
            if info.level == InfoLevel.PUBLIC:
                available.append(info)
            elif info.level == InfoLevel.PRIVATE and depth.value >= DialogueDepth.CASUAL.value:
                # 需要一定信任度
                if npc_state.trust_toward_player >= 0.3:
                    available.append(info)
            elif info.level == InfoLevel.HIDDEN and depth.value >= DialogueDepth.DEEP.value:
                # 需要高信任度和低警觉度
                if npc_state.trust_toward_player >= 0.6 and npc_state.alert_level < 0.5:
                    available.append(info)

        return available


class JumpJumpCLIV2:
    """重构的CLI客户端"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)
        self.ledger = InformationLedger()
        self.current_scene = "scene-0-wuzhishan"

    async def start_game(self):
        """开始游戏"""
        self._show_title()
        self._show_background()

        try:
            # 创建会话
            response = await self.client.post(
                f"{self.api_url}/game/start",
                json={"resume_session_id": None}
            )
            data = response.json()
            self.session_id = data["session_id"]

            # 初始化NPC状态
            self._init_npc_states()

            console.print(f"\n[dim]会话ID: {self.session_id[:8]}...[/dim]\n")

            # 显示开场
            await self._display_opening(data)

            # 主循环
            await self._main_loop()

        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            import traceback
            traceback.print_exc()
        finally:
            await self.client.aclose()

    def _show_title(self):
        """显示标题"""
        console.print(Panel.fit(
            "[bold cyan]Jump Jump - 悟空传[/bold cyan]\n"
            "[dim]文字探险游戏 CLI v2[/dim]\n"
            "[dim]核心机制：信息分层 × 对话深度 × 缝隙参与[/dim]",
            border_style="cyan"
        ))

    def _show_background(self):
        """显示背景"""
        from rich.text import Text

        content = Text()
        content.append("序章：五指山·尘埃\n\n", style="yellow")
        content.append("你是五指山附近的少年樵夫，今天走了一条不常走的小路。\n", style="white")
        content.append("这座山藏着很多故事。有些人知道部分真相，有些人知道全部，"
                      "但他们不会主动告诉你。你需要在对话中寻找缝隙，拼凑信息。\n\n", style="dim")

        content.append("【可对话对象】\n", style="bold")
        content.append("  • 祖母 - 你的家人，知道民间传说\n", style="green")
        content.append("  • 行者 - 路过的神秘人，似乎有目的\n\n", style="green")

        content.append("【无法对话，但可以感知】\n", style="bold")
        content.append("  • 山体深处 - 有某种存在，你无法与他交谈，\n    但可以通过观察和洞察力感知他的存在\n\n", style="magenta")

        content.append("提示：深入询问可能获得情报，也可能引起警觉。", style="italic dim")

        console.print(Panel(content, border_style="yellow", title="背景"))

    def _init_npc_states(self):
        """初始化NPC状态"""
        # Scene 0 NPCs
        self.ledger.npc_states["grandmother_s0"] = NPCState(
            npc_id="grandmother_s0",
            trust_toward_player=0.7,  # 祖母对少年信任较高
            known_info_ids={"INFO_S0_GRANDMA_STORY_1", "INFO_S0_GRANDMA_STORY_2", "INFO_S0_PEACH_TREE"}
        )

        self.ledger.npc_states["traveler_s0"] = NPCState(
            npc_id="traveler_s0",
            trust_toward_player=0.3,  # 行者对陌生人较谨慎
            known_info_ids={"INFO_S0_TRAVELER_IDENTITY", "INFO_S0_PEACH_TREE", "INFO_S0_INSCRIPTION"}
        )

        self.ledger.npc_states["wukong_s0"] = NPCState(
            npc_id="wukong_s0",
            trust_toward_player=0.1,  # 悟空几乎不信任任何人
            known_info_ids={"INFO_S0_WUKONG_WHISPER", "INFO_S0_INSCRIPTION"}
        )

    async def _display_opening(self, data: dict):
        """显示开场"""
        console.print(Panel(
            f"[white]{data['narrative_text']}[/white]",
            border_style="blue"
        ))

        # 显示已知公开信息
        console.print("\n[dim]你已知的传闻：[/dim]")
        for info_id in ["INFO_S0_PEACH_TREE", "INFO_S0_INSCRIPTION"]:
            info = self.ledger.get_info(info_id)
            if info:
                console.print(f"  · {info.content}")

    async def _main_loop(self):
        """主游戏循环"""
        while True:
            # 显示当前状态
            self._show_player_status()

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
                await self._make_decision()

    def _show_player_status(self):
        """显示玩家状态"""
        # 计算信息获取进度
        public_known = len([i for i in self.ledger.player_knowledge
                          if self.ledger.get_info(i) and self.ledger.get_info(i).level == InfoLevel.PUBLIC])
        private_known = len([i for i in self.ledger.player_knowledge
                           if self.ledger.get_info(i) and self.ledger.get_info(i).level == InfoLevel.PRIVATE])
        hidden_known = len([i for i in self.ledger.player_knowledge
                          if self.ledger.get_info(i) and self.ledger.get_info(i).level == InfoLevel.HIDDEN])

        status = f"""
[dim]场景: {self.current_scene} | [/dim]
信息收集: [green]公开{public_known}[/green] [yellow]私密{private_known}[/yellow] [red]隐藏{hidden_known}[/red]
        """.strip()
        console.print(f"\n{status}")

    def _show_main_menu(self) -> str:
        """显示主菜单"""
        console.print("\n" + "─" * 60)
        console.print("[bold cyan]请选择行动:[/bold cyan]\n")
        console.print("  [1] 与NPC交谈 (获取信息)")
        console.print("  [2] 观察环境 (发现线索)")
        console.print("  [3] 整理信息 (查看已知情报)")
        console.print("  [4] 使用洞察力 (揭示隐藏层)")
        console.print("  [5] 做出决策 (影响剧情)")
        console.print("  [q] 退出")
        console.print("─" * 60)

        return Prompt.ask("选择", choices=["1", "2", "3", "4", "5", "q"])

    async def _interact_with_npc(self):
        """与NPC交互 - 核心机制

        可对话Agent: 祖母、行者
        不可对话: 悟空(只能通过观察和洞察力感知)
        """
        # 选择NPC - 只有祖母和行者是可对话的agent
        npcs = ["grandmother_s0", "traveler_s0"]
        npc_names = {"grandmother_s0": "祖母", "traveler_s0": "行者"}

        console.print("\n[bold]选择交谈对象:[/bold]")
        console.print("[dim]你可以与他们对话，在交谈中获取信息。[/dim]\n")

        for i, npc_id in enumerate(npcs, 1):
            state = self.ledger.npc_states[npc_id]
            trust = "█" * int(state.trust_toward_player * 10) + "░" * (10 - int(state.trust_toward_player * 10))
            alert = "⚠️" if state.alert_level > 0.5 else "  "
            console.print(f"  [{i}] {npc_names[npc_id]} {alert} [信任:{trust}]")

        console.print("\n[dim]另外，你可以通过[观察环境]感知山体深处，[/dim]")
        console.print("[dim]或使用[洞察力]聆听山中的低语...[/dim]")

        choice = Prompt.ask("选择", choices=["1", "2", "q"])
        if choice == "q":
            return

        npc_id = npcs[int(choice) - 1]
        await self._dialogue_with_npc(npc_id)

    async def _dialogue_with_npc(self, npc_id: str):
        """对话系统 - 多层深度"""
        npc_state = self.ledger.npc_states[npc_id]
        npc_name = {"grandmother_s0": "祖母", "traveler_s0": "行者", "wukong_s0": "悟空"}[npc_id]

        # 对话循环
        while True:
            console.print(f"\n[bold cyan]与 {npc_name} 交谈中...[/bold cyan]")
            console.print(f"[dim]当前信任度: {npc_state.trust_toward_player:.1f} | 警觉度: {npc_state.alert_level:.1f}[/dim]")

            # 选择对话深度
            console.print("\n选择对话方式:")
            console.print("  [1] 表面寒暄 (安全，获取公开信息)")
            console.print("  [2] 随意交谈 (低风险，可能获得私密信息)")
            console.print("  [3] 深入询问 (可能引起警觉，获取隐藏信息)")
            console.print("  [4] 试探/施压 (高风险，可能破坏关系)")
            console.print("  [q] 结束对话")

            depth_choice = Prompt.ask("选择", choices=["1", "2", "3", "4", "q"])
            if depth_choice == "q":
                break

            depth = DialogueDepth(int(depth_choice))

            # 执行对话
            await self._execute_dialogue(npc_id, npc_state, depth)

            # 检查警觉度
            if npc_state.alert_level >= 0.8:
                console.print(f"[red]{npc_name} 变得警惕，拒绝继续深入交谈。[/red]")
                break

    async def _execute_dialogue(self, npc_id: str, npc_state: NPCState, depth: DialogueDepth):
        """执行对话"""
        npc_name = {"grandmother_s0": "祖母", "traveler_s0": "行者", "wukong_s0": "悟空"}[npc_id]

        # 计算结果
        if depth == DialogueDepth.SURFACE:
            # 表面寒暄 - 安全
            npc_state.trust_toward_player = min(1.0, npc_state.trust_toward_player + 0.05)
            messages = self._get_surface_dialogue(npc_id)
            console.print(Panel(random.choice(messages), title=f"{npc_name}", border_style="green"))

        elif depth == DialogueDepth.CASUAL:
            # 随意交谈
            npc_state.trust_toward_player = min(1.0, npc_state.trust_toward_player + 0.1)
            # 可能获得私密信息
            available = self.ledger.get_npc_available_info(npc_id, depth)
            new_info = [i for i in available if i.info_id not in npc_state.shared_info_ids]

            if new_info and random.random() < npc_state.trust_toward_player:
                info = random.choice(new_info)
                npc_state.shared_info_ids.add(info.info_id)
                self.ledger.player_learns(info.info_id)

                console.print(Panel(
                    f"[yellow]{npc_name}:[/yellow] {self._get_dialogue_for_info(npc_id, info.info_id)}",
                    border_style="yellow"
                ))
                console.print(f"\n[green]✓ 获得私密信息: {info.content[:50]}...[/green]")
            else:
                messages = self._get_casual_dialogue(npc_id)
                console.print(Panel(random.choice(messages), title=f"{npc_name}", border_style="green"))

        elif depth == DialogueDepth.DEEP:
            # 深入询问
            npc_state.alert_level += 0.2
            available = self.ledger.get_npc_available_info(npc_id, depth)
            new_info = [i for i in available if i.info_id not in npc_state.shared_info_ids]

            if new_info and npc_state.trust_toward_player >= 0.6:
                info = random.choice(new_info)
                npc_state.shared_info_ids.add(info.info_id)
                self.ledger.player_learns(info.info_id)

                console.print(Panel(
                    f"[yellow]{npc_name}压低声音:[/yellow] {self._get_dialogue_for_info(npc_id, info.info_id)}",
                    border_style="red"
                ))
                console.print(f"\n[red]✓ 获得隐藏信息: {info.content}[/red]")

                # 显示暗示
                if info.implications:
                    console.print(f"[dim]这让你联想到其他事情...[/dim]")
            else:
                console.print(Panel(
                    f"[yellow]{npc_name}:[/yellow] ...这个话题我不太方便说。",
                    border_style="yellow"
                ))
                console.print(f"[#FFA500]警觉度上升: {npc_state.alert_level:.1f}[/#FFA500]")

        elif depth == DialogueDepth.PROBE:
            # 试探/施压
            npc_state.alert_level += 0.4
            npc_state.trust_toward_player -= 0.2

            console.print(Panel(
                f"[red]{npc_name}明显感到不适:[/red] 你在问什么？！",
                border_style="red"
            ))
            console.print(f"[red]信任度下降，警觉度大幅上升！[/red]")

    def _get_surface_dialogue(self, npc_id: str) -> List[str]:
        """表面寒暄对话"""
        dialogues = {
            "grandmother_s0": [
                "祖母：回来啦。柴砍得怎么样？",
                "祖母：今天风大，多穿点衣服。",
                "祖母：晚饭快好了，去洗手吧。",
            ],
            "traveler_s0": [
                "行者：此山风景独特，小兄弟常来吗？",
                "行者：听说这山有些传说，你可知道？",
                "行者：天快黑了，你也该下山了。",
            ],
            "wukong_s0": [
                "... (山深处传来微弱的震动，但没有声音)",
                "... (你感觉有人在看着你，但找不到来源)",
                "... (风中似乎有叹息，但听不清楚)",
            ],
        }
        return dialogues.get(npc_id, ["..."])

    def _get_casual_dialogue(self, npc_id: str) -> List[str]:
        """随意交谈对话"""
        dialogues = {
            "grandmother_s0": [
                "祖母：这山上的故事啊...我老了，记不清了。",
                "祖母：以前这里很热闹的，现在只剩风了。",
                "祖母：你注意到那棵桃树了吗？烧了好多年了。",
            ],
            "traveler_s0": [
                "行者：我走过很多地方，这山给我的感觉很...特别。",
                "行者：你听说过'齐天大圣'吗？不只是传说那么简单。",
                "行者：有些真相，知道了反而不好。你还年轻。",
            ],
            "wukong_s0": [
                "... (你似乎听到地下传来一声叹息，但可能是错觉)",
                "... (岩壁上的刻痕在阳光下闪烁)",
                "... (一只猴子远远地看着你，然后消失在岩石后)",
            ],
        }
        return dialogues.get(npc_id, ["..."])

    def _get_dialogue_for_info(self, npc_id: str, info_id: str) -> str:
        """根据信息ID获取对话"""
        dialogues = {
            ("grandmother_s0", "INFO_S0_GRANDMA_STORY_1"): "我年轻时听说过一个故事...有个孩子剔骨还父，但最后没有复活。莲藕做的身体，还是原来的那个人吗？",
            ("grandmother_s0", "INFO_S0_GRANDMA_STORY_2"): "天上也不干净。听说有人在偷'灵蕴'，那是神仙的命根子。这事知道的人不多...",
            ("traveler_s0", "INFO_S0_TRAVELER_IDENTITY"): "...实不相瞒，我在找一个人。他曾经是齐天大圣，现在被压在这座山下。我是他的师父。",
        }
        return dialogues.get((npc_id, info_id), "我有件事要告诉你...")

    async def _observe_environment(self):
        """观察环境 - 感知山体

        环境是独立于NPC的信息源，特别是对悟空的感知。
        你无法与他对话，但可以通过环境线索了解他的存在与状态。
        """
        console.print("\n[dim]你仔细观察周围环境，感知山体的气息...[/dim]")

        # 环境观察分为两类：普通环境线索、与悟空相关的感知
        environmental_clues = [
            {
                "text": "路边有一株烧焦的桃树残根，根部焦黑但隐约有新芽冒出的痕迹。",
                "related_to": None,
                "info_id": None
            },
            {
                "text": "岩壁上有模糊的刻痕，像是字迹，但已经被风化得几乎看不清。你靠近观察，隐约能看出是四个字的轮廓。",
                "related_to": "wukong",
                "info_id": "INFO_S0_INSCRIPTION"
            },
            {
                "text": "一块不属于这座山的金属碎片，嵌在岩缝中，边缘异常锋利。",
                "related_to": None,
                "info_id": None
            },
            {
                "text": "一面风化的旗帜碎片，挂在一根已经折断的旗杆上，布面上隐约有红色纹路。",
                "related_to": None,
                "info_id": None
            },
            {
                "text": "某处平坦的岩面上有圆形凹痕，像是有人曾在这里坐了很久很久。",
                "related_to": None,
                "info_id": None
            },
        ]

        wukong_perceptions = [
            {
                "text": "山体深处传来低频声响，不像风声，更像某种极其缓慢的呼吸。那呼吸似乎来自地下很深的地方，带着压抑的力量。",
                "sensitivity": 0.3,  # 容易感知
                "info_id": "INFO_S0_WUKONG_BREATH"
            },
            {
                "text": "岩壁突然轻微震动，一些碎石滚落。你感到脚下的大山似乎...动了一下？",
                "sensitivity": 0.5,
                "info_id": "INFO_S0_WUKONG_MOVEMENT"
            },
            {
                "text": "风中传来一声极轻的叹息，若有若无。你屏住呼吸，但那声音再也没有出现。",
                "sensitivity": 0.7,  # 需要更敏锐的感知
                "info_id": "INFO_S0_WUKONG_SIGH"
            },
            {
                "text": "夕阳西下时，岩壁上的刻痕投下长长的阴影。那阴影的形状，隐约像一只被压在山下的猴子。",
                "sensitivity": 0.9,  # 很难察觉，需要洞察力
                "info_id": "INFO_S0_WUKONG_SHADOW"
            },
        ]

        # 30%概率感知到悟空相关的迹象
        if random.random() < 0.3:
            # 根据玩家已知信息数量决定感知深度
            known_count = len(self.ledger.player_knowledge)
            available_perceptions = [p for p in wukong_perceptions
                                      if p["sensitivity"] <= (0.3 + known_count * 0.1)]

            if available_perceptions:
                obs = random.choice(available_perceptions)
                console.print(Panel(
                    f"[magenta]{obs['text']}[/magenta]",
                    title="感知到山体深处",
                    border_style="magenta"
                ))

                if obs["info_id"] and obs["info_id"] not in self.ledger.player_knowledge:
                    self.ledger.player_learns(obs["info_id"])
                    console.print(f"[dim]✓ 你感知到了山中的存在...[/dim]")
            else:
                # 感知太弱，选择普通环境线索
                obs = random.choice(environmental_clues)
                console.print(Panel(f"[cyan]{obs['text']}[/cyan]", title="观察发现", border_style="cyan"))
        else:
            obs = random.choice(environmental_clues)
            console.print(Panel(f"[cyan]{obs['text']}[/cyan]", title="观察发现", border_style="cyan"))

        # 普通环境线索的信息获取
        if obs.get("info_id") and obs["info_id"] not in self.ledger.player_knowledge:
            self.ledger.player_learns(obs["info_id"])
            console.print(f"[green]✓ {obs['info_id']} 已记录[/green]")

    async def _check_information(self):
        """查看已收集的信息"""
        if not self.ledger.player_knowledge:
            console.print("\n[yellow]你还没有收集到任何信息。[/yellow]")
            return

        console.print("\n[bold]已收集的情报：[/bold]\n")

        # 分类显示
        public = []
        private = []
        hidden = []

        for info_id in sorted(self.ledger.player_knowledge):
            info = self.ledger.get_info(info_id)
            if not info:
                continue

            if info.level == InfoLevel.PUBLIC:
                public.append(info)
            elif info.level == InfoLevel.PRIVATE:
                private.append(info)
            elif info.level == InfoLevel.HIDDEN:
                hidden.append(info)

        if public:
            console.print("[green]【公开信息】[/green]")
            for info in public:
                console.print(f"  · {info.content}")
            console.print()

        if private:
            console.print("[yellow]【私密信息】[/yellow]")
            for info in private:
                console.print(f"  · {info.content} [来源: {info.source}]")
                if info.implications:
                    console.print(f"    [dim]暗示: 可能与{', '.join(info.implications)}有关[/dim]")
            console.print()

        if hidden:
            console.print("[red]【隐藏信息】[/red]")
            for info in hidden:
                console.print(f"  · {info.content} [来源: {info.source}]")
            console.print()

        # 显示矛盾点
        contradictions = []
        for info_id in self.ledger.player_knowledge:
            info = self.ledger.get_info(info_id)
            if info and info.contradictions:
                for contra_id in info.contradictions:
                    if contra_id in self.ledger.player_knowledge:
                        contradictions.append((info, self.ledger.get_info(contra_id)))

        if contradictions:
            console.print("[bold red]【发现矛盾】[/bold red]")
            for info1, info2 in contradictions:
                console.print(f"  ! {info1.source}说的与{info2.source}说的不一致")

    async def _use_insight(self):
        """使用洞察力

        真实目的: 揭示可对话NPC的真实意图
        山中低语: 感知山体深处(悟空)的状态 - 你无法与他对话，但可以通过洞察力"听到"
        """
        console.print("\n[bold yellow]使用洞察力[/bold yellow]")
        console.print("[1] 真实目的 - 揭示可对话NPC的真实目的")
        console.print("[2] 山中低语 - 聆听山体深处的思绪(悟空)")
        console.print("[q] 取消")

        choice = Prompt.ask("选择", choices=["1", "2", "q"])
        if choice == "q":
            return

        if choice == "1":
            # 真实目的 - 只适用于可对话的agent
            npcs = ["grandmother_s0", "traveler_s0"]
            npc_names = {"grandmother_s0": "祖母", "traveler_s0": "行者"}

            console.print("选择目标:")
            for i, npc_id in enumerate(npcs, 1):
                console.print(f"  [{i}] {npc_names[npc_id]}")

            npc_choice = Prompt.ask("选择", choices=["1", "2", "q"])
            if npc_choice == "q":
                return

            npc_id = npcs[int(npc_choice) - 1]
            npc_state = self.ledger.npc_states[npc_id]

            # 显示真实目的
            true_intents = {
                "grandmother_s0": "祖母想保护你远离危险，但又觉得你有权知道真相。她在犹豫要不要告诉你那些故事。",
                "traveler_s0": "行者在确认你是否值得信任。他在找徒弟，但不能让天庭发现。",
            }

            console.print(Panel(
                f"[bold]真实目的揭示[/bold]\n\n{true_intents.get(npc_id, '未知')}",
                border_style="yellow"
            ))

            # 洞察力降低警觉度
            npc_state.alert_level = max(0, npc_state.alert_level - 0.3)
            console.print(f"[dim]通过洞察力，你更好地理解了对方，警觉度降低。[/dim]")

        elif choice == "2":
            # 山中低语 - 感知悟空的状态
            await self._mountain_whispers()

    async def _mountain_whispers(self):
        """山中低语 - 感知悟空的思绪

        你无法与悟空对话，但可以通过洞察力"听到"他的低语。
        这是单向的感知，他不知道你能听到。
        """
        console.print("\n[dim]你静下心来，将耳朵贴近山体...[/dim]")
        console.print("[dim italic]这不是对话，只是...倾听。[/dim]\n")

        # 不同的低语内容，基于你对这座山的了解程度
        known_count = len(self.ledger.player_knowledge)

        whispers = [
            {
                "text": "五百年...还要等多久...",
                "thought": "[悟空在计算时间，他不确定自己是否还相信那个传说]",
                "min_knowledge": 0
            },
            {
                "text": "那个孩子...他能听到我吗？",
                "thought": "[悟空注意到你的存在，但不确定你是否值得信任]",
                "min_knowledge": 2
            },
            {
                "text": "金蝉子...你终于来了。但为什么是现在？",
                "thought": "[悟空感知到了行者的存在，他认出了那股熟悉的气息]",
                "min_knowledge": 4
            },
            {
                "text": "如果我出去...还是我吗？还是另一个傀儡？",
                "thought": "[悟空在质疑自己的身份，他害怕自由只是另一种枷锁]",
                "min_knowledge": 6
            },
            {
                "text": "斗战胜佛...齐天大圣...哪个才是真正的我？",
                "thought": "[悟空在身份认同中挣扎，他害怕取经只是另一场骗局]",
                "min_knowledge": 8
            },
        ]

        # 根据知识量选择可感知的低语
        available_whispers = [w for w in whispers if w["min_knowledge"] <= known_count]

        if available_whispers:
            whisper = random.choice(available_whispers)

            console.print(Panel(
                f"[magenta italic]\"{whisper['text']}\"[/magenta italic]\n\n"
                f"[dim]{whisper['thought']}[/dim]",
                title="山中低语",
                border_style="magenta"
            ))

            # 学习到机密信息
            if "INFO_S0_WUKONG_WHISPER" not in self.ledger.player_knowledge:
                self.ledger.player_learns("INFO_S0_WUKONG_WHISPER")
                console.print("[red]✓ 获得机密信息: 悟空能听到山上的声音，那是他在等一个人[/red]")

            console.print("\n[dim]低语渐渐消散在山风中...[/dim]")
            console.print("[dim]他并不知道自己被听见了。这是你与他的秘密。[/dim]")
        else:
            console.print("[dim]你什么也没听到，只有风声。[/dim]")
            console.print("[dim]或许你需要先了解更多关于这座山的故事...[/dim]")

    async def _make_decision(self):
        """做出决策"""
        console.print("\n[bold]关键决策点[/bold]")
        console.print("你意识到必须做出一个可能影响未来的选择...")
        console.print("[dim](完整决策系统将在后续版本中实现)[/dim]")

    def _show_exit_summary(self):
        """退出总结"""
        console.print("\n" + "=" * 60)
        console.print("[bold]游戏总结[/bold]\n")

        total_info = len(self.ledger.player_knowledge)
        if total_info == 0:
            console.print("你还没有发现任何有价值的信息。")
        elif total_info < 3:
            console.print(f"你收集到了 {total_info} 条信息。这只是冰山一角。")
        else:
            console.print(f"你收集到了 {total_info} 条信息，包括一些不为人知的秘密。")

        console.print("\n[dim]提示：不同对话深度会获得不同层级的信息。[/dim]")
        console.print("[dim]在缝隙中参与，在信息中博弈。[/dim]")


async def main():
    cli = JumpJumpCLIV2()
    await cli.start_game()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]游戏已退出[/yellow]")
