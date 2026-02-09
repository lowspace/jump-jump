#!/usr/bin/env python3
"""
完整NPC交互测试 - 展示信任度提升后的信息传播
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

async def test_full_interactions():
    """完整演示NPC交互与信息传播"""

    console.print(Panel.fit(
        "[bold cyan]Jump Jump v3 - NPC信息传播演示[/bold cyan]\n"
        "[dim]展示NPC间真实的 gossip 和信息传递[/dim]",
        border_style="cyan"
    ))

    cli = JumpJumpCLIV3()
    await cli.engine.create_session('scene-0-wuzhishan')

    # 手动调整NPC关系，使gossip更有可能发生
    cli.engine.npc_society.set_relationship('grandmother_s0', 'traveler_s0', trust=0.6, suspicion=0.0)
    cli.engine.npc_society.npcs['grandmother_s0'].trust_toward_player = 0.8

    console.print("\n[bold yellow]=== 初始状态（已调整信任度） ===[/bold yellow]")
    show_detailed_state(cli)

    # ============ 多轮对话促进交互 ============
    messages = [
        ('grandmother_s0', '奶奶，给我讲讲山上的故事吧'),
        ('grandmother_s0', '那个桃树有什么特别的吗？'),
        ('traveler_s0', '你在找什么？'),
        ('grandmother_s0', '我总觉得这座山怪怪的'),
    ]

    for i, (target, message) in enumerate(messages, 1):
        console.print(f"\n[bold green]=== 回合 {i}：与{get_name(target)}对话 ===[/bold green]")
        console.print(f"[dim]玩家说：{message}[/dim]")

        action = PlayerAction(
            action_type='dialogue',
            target=target,
            content=message,
            turn=i
        )

        result = await cli.engine.process_player_action(action)

        # 显示NPC反应
        for reaction in result.npc_reactions:
            if reaction.npc_id == target:
                console.print(Panel(
                    f"[white]{reaction.observable}[/white]",
                    title=get_name(target),
                    border_style="blue"
                ))

        # 显示幕后动态
        if result.behind_scenes:
            console.print("\n[magenta]【幕后动态】[/magenta]")
            for reveal in result.behind_scenes:
                console.print(f"  [dim magenta]• {reveal['content']}[/dim magenta]")

        # 显示NPC间交互
        if result.npc_npc_interactions:
            console.print("\n[dim]NPC间交互：[/dim]")
            for interaction in result.npc_npc_interactions:
                show_interaction_detail(interaction)

    # ============ 查看信息传播 ============
    console.print("\n[bold cyan]=== 信息传播网络（多轮后） ===[/bold cyan]")
    show_info_propagation(cli)

    # ============ 使用洞察力 ============
    console.print("\n[bold yellow]=== 使用洞察力：偷听幕后对话 ===[/bold yellow]")

    # 先运行一次后台模拟产生更多对话
    await cli.engine.npc_society.run_background_simulation(3)

    result = cli.engine.use_insight_behind_dialogue()
    if result.get('success'):
        revealed = result['revealed']
        if '暂无' in revealed:
            console.print("[dim]最近没有听到NPC间的私密对话[/dim]")
        else:
            console.print(Panel(
                f"[magenta]{revealed}[/magenta]",
                title="幕后对话",
                border_style="magenta"
            ))

    # ============ 对话日志 ============
    console.print("\n[bold cyan]=== 完整NPC对话日志 ===[/bold cyan]")
    show_conversation_log(cli)

    # ============ 最终状态 ============
    console.print("\n[bold yellow]=== 最终状态 ===[/bold yellow]")
    show_detailed_state(cli)

    # ============ 总结 ============
    console.print("\n[bold cyan]=== 演示总结 ===[/bold cyan]")

    total_interactions = len(cli.engine.npc_society.conversation_log)
    gossip_count = sum(1 for log in cli.engine.npc_society.conversation_log if log['type'] == 'gossip_player')
    discuss_count = sum(1 for log in cli.engine.npc_society.conversation_log if log['type'] == 'discuss')
    share_count = sum(1 for log in cli.engine.npc_society.conversation_log if log['type'] == 'share_info')

    table = Table(show_header=True, header_style="bold")
    table.add_column("指标")
    table.add_column("数值")
    table.add_column("说明")

    table.add_row("玩家行动次数", "4", "与NPC对话")
    table.add_row("NPC间总交互", str(total_interactions), "后台自动发生")
    table.add_row("  - 关于玩家的gossip", str(gossip_count), "NPC传播你的行为")
    table.add_row("  - NPC间讨论", str(discuss_count), "信息交换")
    table.add_row("  - 信息分享", str(share_count), "实际信息传递")

    console.print(table)

    console.print("\n[green]✓ 演示完成！NPC之间真实传递了信息。[/green]")
    console.print("[dim]关键洞察：当祖母信任度>0.7时，她会向行者gossip关于玩家的事情。[/dim]")


def show_detailed_state(cli):
    """显示详细NPC状态"""
    table = Table(show_header=True, header_style="bold")
    table.add_column("NPC")
    table.add_column("对玩家信任")
    table.add_column("对玩家怀疑")
    table.add_column("与其他NPC关系")
    table.add_column("信息数")

    for npc_id in ['grandmother_s0', 'traveler_s0', 'wukong_s0']:
        state = cli.engine.get_npc_state(npc_id)
        if state:
            rels = []
            for other_id, rel in state.get('relationships', {}).items():
                other_name = get_name(other_id)
                trust_color = "green" if rel['trust'] > 0.5 else "yellow" if rel['trust'] > 0.3 else "red"
                rels.append(f"[{trust_color}]{other_name}:信任{rel['trust']:.1f}[/{trust_color}]")

            trust = state['trust_toward_player']
            trust_str = f"[green]{trust:.1f}[/green]" if trust > 0.6 else f"[yellow]{trust:.1f}[/yellow]" if trust > 0.3 else f"[red]{trust:.1f}[/red]"

            table.add_row(
                get_name(npc_id),
                trust_str,
                f"{state['suspicion_toward_player']:.1f}",
                "\n".join(rels) if rels else "[dim]无[/dim]",
                str(state['known_info_count'])
            )

    console.print(table)


def show_interaction_detail(interaction):
    """显示交互详情"""
    itype = interaction.get('type')

    if itype == 'gossip':
        from_npc = get_name(interaction['from'])
        to_npc = get_name(interaction['to'])
        result = interaction.get('result', {})
        if result.get('success'):
            console.print(f"  [magenta]📢 {from_npc} → {to_npc}:[/magenta] 传播了关于玩家的消息")

    elif itype == 'discuss':
        npcs = interaction.get('between', [])
        result = interaction.get('result', {})
        exchanges = result.get('exchanges', [])

        if len(npcs) >= 2:
            name1, name2 = get_name(npcs[0]), get_name(npcs[1])
            if exchanges:
                console.print(f"  [cyan]💬 {name1} ↔ {name2}:[/cyan]")
                for ex in exchanges:
                    console.print(f"      • {ex}")
            else:
                console.print(f"  [dim]💬 {name1} 和 {name2} 交流了，但信任度不够分享秘密[/dim]")

    elif itype == 'share_info':
        console.print(f"  [yellow]📤 信息分享[/yellow]")


def show_info_propagation(cli):
    """显示信息传播图"""
    propagation = cli.engine.get_info_propagation_map()

    for npc_id, data in propagation.items():
        name = get_name(npc_id)
        knows = data.get('knows', [])
        learned_from = data.get('learned_from', {})

        console.print(f"\n[cyan]{name}[/cyan] 知道 {len(knows)} 条信息:")

        # 分类显示
        original = []
        learned = []

        for info_id in knows:
            source = learned_from.get(info_id, "unknown")
            if source == npc_id:
                original.append(info_id)
            else:
                from_name = get_name(source) if source else "未知"
                learned.append((info_id, from_name))

        if original:
            console.print("  [green]原本就知道:[/green]")
            for info_id in original:
                console.print(f"    ● {info_id}")

        if learned:
            console.print("  [yellow]从他人处获知:[/yellow]")
            for info_id, from_name in learned:
                console.print(f"    ○ {info_id} [dim](来自: {from_name})[/dim]")


def show_conversation_log(cli):
    """显示完整对话日志"""
    logs = cli.engine.npc_society.conversation_log

    if not logs:
        console.print("[dim]暂无对话记录[/dim]")
        return

    for i, log in enumerate(logs, 1):
        turn = log.get('turn', '?')
        itype = log.get('type')
        participants = log.get('participants', [])
        names = [get_name(p) for p in participants]

        if itype == 'share_info':
            privacy = log.get('privacy', 'unknown')
            console.print(f"  [{turn}] [green]分享[/green] {' ↔ '.join(names)} [dim](隐私: {privacy})[/dim]")

        elif itype == 'gossip_player':
            obs = log.get('observation', '...')[:30]
            console.print(f"  [{turn}] [magenta]Gossip[/magenta] {' → '.join(names)}")
            console.print(f"         [dim]\"{obs}...\"[/dim]")

        elif itype == 'discuss':
            topic = log.get('topic', 'unknown')
            exchanges = log.get('exchanges', [])
            console.print(f"  [{turn}] [cyan]讨论[/cyan] {' ↔ '.join(names)} [dim](话题: {topic})[/dim]")
            for ex in exchanges[:2]:  # 最多显示2条
                console.print(f"         [dim]• {ex}[/dim]")


def get_name(npc_id):
    """获取NPC显示名"""
    names = {
        'grandmother_s0': '祖母',
        'traveler_s0': '行者',
        'wukong_s0': '悟空'
    }
    return names.get(npc_id, npc_id)


if __name__ == "__main__":
    asyncio.run(test_full_interactions())
