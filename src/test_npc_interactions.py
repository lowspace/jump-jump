#!/usr/bin/env python3
"""
自动化测试脚本 - 演示CLI v3的NPC交互系统
"""

import asyncio
import sys
sys.path.insert(0, '/Users/dnhb/Desktop/GitHub/My_Projects/jump-jump/src')

from cli.client_v3 import JumpJumpCLIV3, PlayerAction
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

async def test_npc_interactions():
    """完整演示NPC交互系统"""

    console.print(Panel.fit(
        "[bold cyan]Jump Jump v3 - NPC交互演示[/bold cyan]",
        border_style="cyan"
    ))

    cli = JumpJumpCLIV3()
    await cli.engine.create_session('scene-0-wuzhishan')

    # ============ 初始状态 ============
    console.print("\n[bold yellow]=== 初始状态 ===[/bold yellow]")
    show_npc_network(cli)

    # ============ 第一轮：与祖母对话 ============
    console.print("\n[bold green]=== 回合 1：玩家与祖母对话 ===[/bold green]")
    console.print("[dim]玩家说：奶奶，这山上有什么故事吗？[/dim]")

    action1 = PlayerAction(
        action_type='dialogue',
        target='grandmother_s0',
        content='奶奶，这山上有什么故事吗？',
        turn=1
    )

    result1 = await cli.engine.process_player_action(action1)

    # 显示NPC反应
    for reaction in result1.npc_reactions:
        if reaction.npc_id == 'grandmother_s0':
            console.print(Panel(
                f"[white]{reaction.observable}[/white]",
                title="祖母",
                border_style="blue"
            ))

    # 显示幕后动态
    if result1.behind_scenes:
        console.print("\n[magenta]【幕后动态 - NPC间发生的事情】[/magenta]")
        for reveal in result1.behind_scenes:
            console.print(f"  [dim magenta]• {reveal['content']}[/dim magenta]")

    # 显示NPC交互详情
    console.print("\n[dim]NPC间交互详情：[/dim]")
    for interaction in result1.npc_npc_interactions:
        if interaction.get('type') == 'discuss':
            npcs = interaction.get('between', [])
            exchanges = interaction.get('result', {}).get('exchanges', [])
            if exchanges:
                console.print(f"  [yellow]{npcs[0]} ↔ {npcs[1]}:[/yellow]")
                for ex in exchanges:
                    console.print(f"    • {ex}")
            else:
                console.print(f"  [dim]{npcs[0]} 和 {npcs[1]} 交流了，但没有分享新信息[/dim]")

    # ============ 第二轮：与行者对话 ============
    console.print("\n[bold green]=== 回合 2：玩家与行者对话 ===[/bold green]")
    console.print("[dim]玩家说：你是谁？为什么在这里？[/dim]")

    action2 = PlayerAction(
        action_type='dialogue',
        target='traveler_s0',
        content='你是谁？为什么在这里？',
        turn=2
    )

    result2 = await cli.engine.process_player_action(action2)

    for reaction in result2.npc_reactions:
        if reaction.npc_id == 'traveler_s0':
            console.print(Panel(
                f"[white]{reaction.observable}[/white]",
                title="行者",
                border_style="blue"
            ))

    if result2.behind_scenes:
        console.print("\n[magenta]【幕后动态】[/magenta]")
        for reveal in result2.behind_scenes:
            console.print(f"  [dim magenta]• {reveal['content']}[/dim magenta]")

    # ============ 第三轮：观察环境 ============
    console.print("\n[bold green]=== 回合 3：玩家观察环境 ===[/bold green]")
    console.print("[dim]玩家仔细观察周围环境...[/dim]")

    action3 = PlayerAction(
        action_type='observe',
        target=None,
        content='观察环境',
        turn=3
    )

    result3 = await cli.engine.process_player_action(action3)

    # 可能触发NPC观察
    if result3.npc_reactions:
        console.print("\n[yellow]【注意】[/yellow] [dim]以下NPC注意到了你的行为：[/dim]")
        for reaction in result3.npc_reactions:
            console.print(f"  • {reaction.npc_id}: {reaction.observable}")

    # ============ 使用洞察力 ============
    console.print("\n[bold yellow]=== 使用洞察力：偷听幕后对话 ===[/bold yellow]")

    result = cli.engine.use_insight_behind_dialogue()
    if result.get('success'):
        console.print(Panel(
            f"[magenta]{result['revealed']}[/magenta]",
            title="幕后对话",
            border_style="magenta"
        ))
        console.print(f"\n[dim]共揭示 {result.get('conversations_revealed', 0)} 次NPC间对话[/dim]")

    # ============ 查看信息传播网络 ============
    console.print("\n[bold cyan]=== 信息传播网络 ===[/bold cyan]")

    propagation = cli.engine.get_info_propagation_map()
    for npc_id, data in propagation.items():
        name = {'grandmother_s0': '祖母', 'traveler_s0': '行者', 'wukong_s0': '悟空'}.get(npc_id, npc_id)
        knows = data.get('knows', [])
        learned_from = data.get('learned_from', {})

        console.print(f"\n[cyan]{name}[/cyan] 知道 {len(knows)} 条信息:")

        for info_id in knows:
            source = learned_from.get(info_id, "unknown")
            if source == npc_id:
                console.print(f"  [green]●[/green] {info_id} [dim](原本就知道)[/dim]")
            else:
                from_name = {'grandmother_s0': '祖母', 'traveler_s0': '行者', 'wukong_s0': '悟空'}.get(source, source)
                console.print(f"  [yellow]●[/yellow] {info_id} [dim](从{from_name}处获知)[/dim]")

    # ============ 最终NPC网络 ============
    console.print("\n[bold yellow]=== 最终NPC关系网络 ===[/bold yellow]")
    show_npc_network(cli)

    # ============ 总结 ============
    console.print("\n[bold cyan]=== 演示总结 ===[/bold cyan]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("指标")
    table.add_column("数值")

    total_interactions = len(cli.engine.npc_society.conversation_log)
    gossip_count = sum(1 for log in cli.engine.npc_society.conversation_log if log['type'] == 'gossip_player')
    discuss_count = sum(1 for log in cli.engine.npc_society.conversation_log if log['type'] == 'discuss')

    table.add_row("玩家行动次数", "3")
    table.add_row("NPC间总交互", str(total_interactions))
    table.add_row("  - 关于玩家的gossip", str(gossip_count))
    table.add_row("  - NPC间讨论", str(discuss_count))

    console.print(table)

    console.print("\n[dim]✓ 演示完成！NPC之间真的在传递信息。[/dim]")

def show_npc_network(cli):
    """显示NPC关系网络"""
    table = Table(show_header=True, header_style="bold")
    table.add_column("NPC")
    table.add_column("对你的信任")
    table.add_column("怀疑")
    table.add_column("与其他NPC关系")

    npcs = ['grandmother_s0', 'traveler_s0', 'wukong_s0']
    names = {'grandmother_s0': '祖母', 'traveler_s0': '行者', 'wukong_s0': '悟空(山体)'}

    for npc_id in npcs:
        state = cli.engine.get_npc_state(npc_id)
        if state:
            trust = state['trust_toward_player']
            suspicion = state['suspicion_toward_player']

            trust_str = f"{trust:.1f}"
            if trust > 0.6:
                trust_str = f"[green]{trust_str}[/green]"
            elif trust < 0.3:
                trust_str = f"[red]{trust_str}[/red]"
            else:
                trust_str = f"[yellow]{trust_str}[/yellow]"

            rels = []
            for other_id, rel in state.get('relationships', {}).items():
                if other_id in names:
                    rel_str = f"{names[other_id]}:信任{rel['trust']:.1f}"
                    if rel['trust'] > 0.5:
                        rel_str = f"[green]{rel_str}[/green]"
                    rels.append(rel_str)

            table.add_row(
                names[npc_id],
                trust_str,
                f"{suspicion:.1f}",
                "\n".join(rels) if rels else "[dim]无[/dim]"
            )

    console.print(table)

if __name__ == "__main__":
    asyncio.run(test_npc_interactions())
