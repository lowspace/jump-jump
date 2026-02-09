#!/usr/bin/env python3
"""
Jump Jump CLI Client - Command Line Interface for the game
"""

import asyncio
import json
import sys
from typing import Optional

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich.table import Table

console = Console()

class JumpJumpCLI:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session_id: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def start_game(self):
        """Start a new game session"""
        console.print(Panel.fit(
            "[bold cyan]Jump Jump - 悟空传[/bold cyan]\n"
            "[dim]文字探险游戏 CLI 版[/dim]",
            border_style="cyan"
        ))

        try:
            response = await self.client.post(
                f"{self.api_url}/game/start",
                json={"resume_session_id": None}
            )
            data = response.json()
            self.session_id = data["session_id"]

            console.print(f"\n[dim]会话ID: {self.session_id[:8]}...[/dim]\n")

            # Display opening
            await self.display_scene(data)

            # Main game loop
            await self.game_loop()

        except Exception as e:
            console.print(f"[red]错误: {e}[/red]")
            sys.exit(1)
        finally:
            await self.client.aclose()

    async def game_loop(self):
        """Main game loop"""
        while True:
            # Get current state
            state = await self.get_state()

            # Show available actions
            actions = await self.get_available_actions()

            if not actions:
                console.print("[yellow]暂无可用行动[/yellow]")
                break

            # Display menu
            choice = await self.show_menu(actions)

            if choice is None:
                break

            # Execute action
            await self.execute_action(choice)

    async def get_state(self):
        """Get current game state"""
        response = await self.client.get(
            f"{self.api_url}/game/{self.session_id}/state"
        )
        return response.json()

    async def get_available_actions(self):
        """Get available actions from state"""
        state = await self.get_state()

        # Build actions list
        actions = []

        # Add insight actions if available
        quota = state.get("insight_quota", {})
        if quota.get("true_purpose", 0) > 0 or quota.get("behind_dialogue", 0) > 0:
            actions.append({
                "type": "insight",
                "description": "使用洞察力",
                "quota": quota
            })

        # Add transition action if scene complete
        if state.get("scene_complete"):
            actions.append({
                "type": "transition",
                "description": "进入下一个场景 (继续)",
                "scene": state.get("current_scene")
            })

        # Add standard actions
        for npc_id in state.get("active_npcs", []):
            actions.append({
                "type": "dialogue",
                "target": npc_id,
                "description": f"与 {self.get_npc_name(npc_id)} 对话"
            })

        # Add observe
        actions.append({
            "type": "observe",
            "description": "观察周围环境"
        })

        return actions

    def get_npc_name(self, npc_id: str) -> str:
        """Get NPC display name"""
        names = {
            "nezha": "哪吒",
            "lijing": "李靖",
            "yangjian": "杨戬",
            "tianpeng": "天蓬",
            "juanlian": "卷帘",
            "laohou": "老猴",
            "tietou": "铁头",
            "zixia": "紫霞",
            "huikong": "慧空",
            "tangseng": "唐僧",
            "grandmother_s0": "祖母",
            "wukong_s0": "悟空",
            "traveler_s0": "行者",
        }
        return names.get(npc_id, npc_id)

    async def show_menu(self, actions: list) -> Optional[dict]:
        """Show action menu and get user choice"""
        console.print("\n" + "─" * 50)
        console.print("[bold cyan]请选择行动:[/bold cyan]\n")

        for i, action in enumerate(actions, 1):
            desc = action["description"]
            if action["type"] == "insight":
                quota = action.get("quota", {})
                desc += f" [真实目的:{quota.get('true_purpose',0)} 幕后对话:{quota.get('behind_dialogue',0)}]"
            console.print(f"  [{i}] {desc}")

        console.print(f"  [q] 退出游戏")
        console.print("─" * 50)

        choice = Prompt.ask("选择", choices=[str(i) for i in range(1, len(actions) + 1)] + ["q"])

        if choice == "q":
            return None

        return actions[int(choice) - 1]

    async def execute_action(self, action: dict):
        """Execute selected action"""
        action_type = action["type"]

        try:
            if action_type == "insight":
                await self.use_insight()
            elif action_type == "transition":
                await self.transition_scene()
            elif action_type == "dialogue":
                await self.dialogue(action["target"])
            elif action_type == "observe":
                await self.observe()
            else:
                # Generic action
                response = await self.client.post(
                    f"{self.api_url}/game/{self.session_id}/action",
                    json={
                        "action_type": action_type,
                        "target": action.get("target"),
                        "content": action.get("description", "")
                    }
                )
                data = response.json()
                await self.display_scene(data)

        except Exception as e:
            console.print(f"[red]执行失败: {e}[/red]")

    async def use_insight(self):
        """Use insight system"""
        console.print("\n[bold yellow]使用洞察力[/bold yellow]")
        console.print("[1] 真实目的 - 揭示NPC此刻的真实目的")
        console.print("[2] 幕后对话 - 揭示隐藏对话层")

        choice = Prompt.ask("选择洞察类型", choices=["1", "2", "q"])

        if choice == "q":
            return

        insight_type = "true_purpose" if choice == "1" else "behind_dialogue"
        target = Prompt.ask("目标NPC (可选，直接回车跳过)", default="current")

        try:
            response = await self.client.post(
                f"{self.api_url}/game/{self.session_id}/insight",
                json={
                    "insight_type": insight_type,
                    "target": target if target != "current" else "current"
                }
            )
            data = response.json()

            if data.get("success"):
                revealed = data.get("revealed", {})
                console.print(Panel(
                    f"[bold yellow]洞察力揭示[/bold yellow]\n\n"
                    f"[cyan]类型:[/cyan] {revealed.get('type', '未知')}\n"
                    f"[cyan]内容:[/cyan] {revealed.get('true_intent', revealed.get('npc_name', '信息已揭示'))}\n",
                    border_style="yellow"
                ))

                # Show remaining quota
                quota = data.get("quota_remaining", {})
                console.print(f"[dim]剩余洞察力: 真实目的={quota.get('true_purpose')} 幕后对话={quota.get('behind_dialogue')}[/dim]")
            else:
                console.print(f"[red]{data.get('error', '洞察失败')}[/red]")

        except Exception as e:
            console.print(f"[red]洞察请求失败: {e}[/red]")

    async def transition_scene(self):
        """Transition to next scene"""
        console.print("\n[bold green]正在进入下一个场景...[/bold green]")

        try:
            response = await self.client.post(
                f"{self.api_url}/game/{self.session_id}/transition",
                json={}
            )
            data = response.json()

            if data.get("game_complete"):
                console.print(Panel(
                    "[bold green]游戏完成！[/bold green]\n\n"
                    "感谢游玩 Jump Jump - 悟空传",
                    border_style="green"
                ))
                sys.exit(0)

            await self.display_scene(data)

        except Exception as e:
            console.print(f"[red]场景切换失败: {e}[/red]")

    async def dialogue(self, npc_id: str):
        """Dialogue with NPC"""
        npc_name = self.get_npc_name(npc_id)
        console.print(f"\n[bold cyan]与 {npc_name} 对话[/bold cyan]")

        message = Prompt.ask("你说")

        try:
            response = await self.client.post(
                f"{self.api_url}/game/{self.session_id}/action",
                json={
                    "action_type": "dialogue",
                    "target": npc_id,
                    "content": message
                }
            )
            data = response.json()
            await self.display_scene(data)

        except Exception as e:
            console.print(f"[red]对话失败: {e}[/red]")

    async def observe(self):
        """Observe surroundings"""
        console.print("\n[dim]正在观察...[/dim]")

        try:
            response = await self.client.post(
                f"{self.api_url}/game/{self.session_id}/action",
                json={
                    "action_type": "observe",
                    "target": None,
                    "content": "观察周围环境"
                }
            )
            data = response.json()
            await self.display_scene(data)

        except Exception as e:
            console.print(f"[red]观察失败: {e}[/red]")

    async def display_scene(self, data: dict):
        """Display scene data"""
        # Narrative
        if data.get("narrative_text"):
            text = Text(data["narrative_text"])
            text.stylize("white")
            console.print(Panel(text, border_style="blue"))

        # Behind scenes reveals
        if data.get("behind_scenes_reveals"):
            for reveal in data["behind_scenes_reveals"]:
                console.print(f"[dim magenta]【幕后】{reveal.get('content', '')}[/dim magenta]")

        # Scene transition info
        if data.get("scene_transition"):
            console.print(f"\n[bold green]>>> 场景切换: {self.get_scene_name(data.get('from_scene'))} → {self.get_scene_name(data.get('to_scene'))}[/bold green]")

    def get_scene_name(self, scene_id: str) -> str:
        """Get scene display name"""
        names = {
            "scene-0-wuzhishan": "五指山",
            "scene-1-chentangguan": "陈塘关",
            "scene-2-tianhe": "天河",
            "scene-3-huaguoshan": "花果山",
            "scene-4-lingtai": "灵台方寸山",
        }
        return names.get(scene_id, scene_id)


async def main():
    """Main entry point"""
    cli = JumpJumpCLI()
    await cli.start_game()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]游戏已退出[/yellow]")
    except Exception as e:
        console.print(f"\n[red]错误: {e}[/red]")
