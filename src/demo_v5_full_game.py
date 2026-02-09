#!/usr/bin/env python3
"""
CLI v5 完整游戏流程演示 - 自动化测试
"""

import sys
import asyncio
sys.path.insert(0, '/Users/dnhb/Desktop/GitHub/My_Projects/jump-jump/src')

import importlib.util

# 导入模块
spec_agent = importlib.util.spec_from_file_location(
    "llm_npc_agent", "/Users/dnhb/Desktop/GitHub/My_Projects/jump-jump/src/backend/app/llm_npc_agent.py"
)
llm_module = importlib.util.module_from_spec(spec_agent)
spec_agent.loader.exec_module(llm_module)
create_scene_0_agents = llm_module.create_scene_0_agents

spec_flow = importlib.util.spec_from_file_location(
    "game_flow", "/Users/dnhb/Desktop/GitHub/My_Projects/jump-jump/src/backend/app/game_flow.py"
)
flow_module = importlib.util.module_from_spec(spec_flow)
spec_flow.loader.exec_module(flow_module)
GameFlowManager = flow_module.GameFlowManager

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def demo_full_game():
    """演示完整游戏流程"""

    console.print(Panel.fit(
        "[bold cyan]Jump Jump v5 - 完整游戏演示[/bold cyan]\n"
        "[dim]目标驱动 + 决策系统 + LLM Agent[/dim]",
        border_style="cyan"
    ))

    # 初始化
    console.print("\n[dim]初始化游戏...[/dim]")
    agent_pool = create_scene_0_agents()
    flow_manager = GameFlowManager()

    # ============ 场景 0: 五指山 ============
    console.print("\n[bold yellow]╔══════════════════════════════════════╗[/bold yellow]")
    console.print("[bold yellow]║         场景 0: 五指山·尘埃          ║[/bold yellow]")
    console.print("[bold yellow]╚══════════════════════════════════════╝[/bold yellow]")

    scene_info = flow_manager.start_scene("scene-0-wuzhishan")
    console.print(Panel(
        f"[bold]{scene_info['name']}[/bold]\n\n"
        f"{scene_info['description']}\n\n"
        f"[green]目标: {' / '.join(scene_info['goals'])}[/green]",
        border_style="yellow"
    ))

    # 模拟游戏过程
    grandmother = agent_pool.get_agent("grandmother_s0")
    traveler = agent_pool.get_agent("traveler_s0")

    # 回合 1-3: 与祖母对话建立信任
    console.print("\n[bold cyan]回合 1-3: 与祖母对话[/bold cyan]")

    dialogues_grandma = [
        ("奶奶，给我讲讲山上的故事", "探索性提问"),
        ("奶奶你真好，愿意告诉我这些", "情感建立"),
        ("那个剔骨还子的故事，后来呢？", "深入询问"),
    ]

    for i, (msg, desc) in enumerate(dialogues_grandma, 1):
        console.print(f"\n[dim]回合 {i}: {desc}[/dim]")
        console.print(f"[green]玩家:[/green] {msg}")

        # 使用模板响应（因为没有API key）
        if grandmother.state.trust_toward_player > 0.7:
            response = "你问起了剔骨还子...（叹息）那孩子最后并没有复活。莲藕做的身体，还是原来的哪吒吗？"
            info_gained = ["story_nezha"]
        elif grandmother.state.trust_toward_player > 0.5:
            response = "山上的故事多着呢。但那都是过去的事了..."
            info_gained = []
        else:
            response = "你问这些做什么？专心砍你的柴去。"
            info_gained = []

        console.print(Panel(f"[white]{response}[/white]", title="祖母", border_style="blue"))

        # 更新信任度
        if "好" in msg or "谢谢" in msg:
            grandmother.state.trust_toward_player = min(1.0, grandmother.state.trust_toward_player + 0.1)

        # 推进游戏流程
        action_data = {
            "npc_id": "grandmother_s0",
            "trust_change": 0.05,
            "collected_info": info_gained
        }
        result = flow_manager.process_turn("dialogue", action_data)

        if info_gained:
            console.print(f"[green]✓ 获得信息: {info_gained}[/green]")

    # 回合 4-6: 与行者对话
    console.print("\n[bold cyan]回合 4-6: 与行者对话[/bold cyan]")

    dialogues_traveler = [
        ("你是谁？为什么在这里？", "试探性询问"),
        ("我也在找答案", "建立共鸣"),
        ("你在找齐天大圣吗？", "深入话题"),
    ]

    for i, (msg, desc) in enumerate(dialogues_traveler, 1):
        console.print(f"\n[dim]回合 {i+3}: {desc}[/dim]")
        console.print(f"[green]玩家:[/green] {msg}")

        if traveler.state.trust_toward_player > 0.6:
            response = "（环顾四周）实不相瞒，我在找我的徒弟...齐天大圣。"
            info_gained = ["traveler_identity"]
        elif traveler.state.trust_toward_player > 0.4:
            response = "我只是一个路过的旅人，在寻找答案。"
            info_gained = []
        else:
            response = "（警惕地）与你何干？"
            info_gained = []

        console.print(Panel(f"[white]{response}[/white]", title="行者", border_style="blue"))

        if "答案" in msg or "大圣" in msg:
            traveler.state.trust_toward_player = min(1.0, traveler.state.trust_toward_player + 0.15)

        action_data = {
            "npc_id": "traveler_s0",
            "trust_change": 0.1,
            "collected_info": info_gained
        }
        result = flow_manager.process_turn("dialogue", action_data)

        # 显示目标进度
        if i == 3:
            console.print("\n[yellow]【目标进度】[/yellow]")
            for goal in result['goal_progress']:
                status = "✓" if goal['completed'] else "○"
                console.print(f"  {status} {goal['description']}: {goal['progress']*100:.0f}%")

    # 使用洞察力
    console.print("\n[bold cyan]回合 7: 使用洞察力[/bold cyan]")
    flow_manager.state["insights_used"] += 1
    console.print("[magenta]【洞察】[/magenta] 你注意到祖母望向山体深处时，眼中闪过担忧...")

    result = flow_manager.process_turn("insight", {"insight_used": True})

    # 检查是否触发决策点
    if result.get("show_decision") or flow_manager._should_trigger_decision():
        console.print("\n[bold red]╔══════════════════════════════════════╗[/bold red]")
        console.print("[bold red]║           ⚠️  关键决策点              ║[/bold red]")
        console.print("[bold red]╚══════════════════════════════════════╝[/bold red]")

        decision = flow_manager._get_next_decision()
        if decision:
            console.print(Panel(
                f"[bold]{decision['title']}[/bold]\n\n"
                f"{decision['description']}\n\n"
                f"[yellow]这个选择将影响后续剧情...[/yellow]",
                border_style="red"
            ))

            console.print("[bold]可选行动:[/bold]")
            for choice in decision['choices']:
                console.print(f"  • {choice['text']}")

            # 模拟选择
            selected = decision['choices'][0]  # 选择第一个
            console.print(f"\n[green]→ 玩家选择: {selected['text']}[/green]")

            flow_manager.make_decision(decision['decision_id'], selected['id'])

    # 场景结束
    console.print("\n[bold yellow]═══ 场景 0 完成 ═══[/bold yellow]")

    summary = flow_manager.get_game_summary()

    table = Table(show_header=True)
    table.add_column("统计")
    table.add_column("数值")

    table.add_row("总回合", str(flow_manager.turn_count))
    table.add_row("收集信息", str(len(summary['collected_info'])))
    table.add_row("做出的决策", str(len(summary['decisions_made'])))
    table.add_row("使用洞察力", str(flow_manager.state['insights_used']))

    console.print(table)

    # 显示关系状态
    console.print("\n[bold cyan]最终关系状态:[/bold cyan]")
    for npc_id in ["grandmother_s0", "traveler_s0"]:
        agent = agent_pool.get_agent(npc_id)
        trust = agent.state.trust_toward_player
        name = "祖母" if npc_id == "grandmother_s0" else "行者"

        if trust > 0.8:
            status = "至亲"
        elif trust > 0.6:
            status = "家人"
        elif trust > 0.4:
            status = "熟人"
        else:
            status = "陌生"

        bar = "█" * int(trust * 10) + "░" * (10 - int(trust * 10))
        console.print(f"  {name}: [{bar}] {trust:.1f} ({status})")

    # 下一章预览
    next_scene = flow_manager.get_next_scene()
    if next_scene != "ending":
        console.print(f"\n[dim]准备进入: {next_scene}...[/dim]")

    console.print("\n[green]✓ 演示完成！[/green]")
    console.print("\n[dim]实际游戏中:[/dim]")
    console.print("  • 使用 LLM Agent 生成真实对话")
    console.print("  • 自由输入对话内容")
    console.print("  • 根据对话质量动态调整信任度")
    console.print("  • 收集信息完成目标")
    console.print("  • 关键时刻做出决策")


if __name__ == "__main__":
    asyncio.run(demo_full_game())
