# /src/backend/app/ws_handler.py
# WebSocket Handler for Jump Jump - Real-time game communication

import json
from typing import Dict, Any, Optional
from datetime import datetime

# FastAPI WebSocket (will be imported from main.py)
# from fastapi import WebSocket


class WebSocketManager:
    """
    WebSocket Connection Manager

    Handles multiple client connections and routes messages
    between frontend and game engine.
    """

    def __init__(self):
        # Map session_id to WebSocket connection
        self.active_connections: Dict[str, Any] = {}
        # Map session_id to player state
        self.session_states: Dict[str, Dict[str, Any]] = {}

    async def connect(self, session_id: str, websocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_states[session_id] = {
            "connected_at": datetime.now().isoformat(),
            "last_ping": datetime.now().isoformat()
        }
        print(f"WebSocket connected: {session_id}")

    async def disconnect(self, session_id: str):
        """Handle disconnection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_states:
            del self.session_states[session_id]
        print(f"WebSocket disconnected: {session_id}")

    async def send_message(self, session_id: str, message: Dict[str, Any]):
        """Send message to specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to {session_id}: {e}")

    async def handle_message(
        self,
        session_id: str,
        data: Dict[str, Any],
        game_engine
    ) -> Dict[str, Any]:
        """
        Handle incoming WebSocket message

        Message types:
        - action: Player action (dialogue, decision, move, observe)
        - insight: Use insight
        - ping: Keep-alive
        - get_state: Request current state
        """
        msg_type = data.get("type")
        payload = data.get("payload", {})

        if msg_type == "action":
            return await self._handle_action(session_id, payload, game_engine)

        elif msg_type == "insight":
            return await self._handle_insight(session_id, payload, game_engine)

        elif msg_type == "ping":
            return {"type": "pong", "timestamp": datetime.now().isoformat()}

        elif msg_type == "get_state":
            return await self._handle_get_state(session_id, game_engine)

        elif msg_type == "transition_scene":
            return await self._handle_scene_transition(session_id, payload, game_engine)

        else:
            return {
                "type": "error",
                "error": f"Unknown message type: {msg_type}"
            }

    async def _handle_action(
        self,
        session_id: str,
        payload: Dict[str, Any],
        game_engine
    ) -> Dict[str, Any]:
        """Handle player action"""
        result = await game_engine.process_action(session_id, payload)

        if "error" in result:
            return {
                "type": "error",
                "error": result["error"]
            }

        # Format response for frontend
        response = {
            "type": "narrative",
            "payload": {
                "text": result.get("narrative_text", ""),
                "emotion_beat": result.get("emotion_beat", ""),
                "typing_effect": True
            }
        }

        # Send narrative first
        await self.send_message(session_id, response)

        # Send available actions
        if result.get("available_actions"):
            await self.send_message(session_id, {
                "type": "available_actions",
                "payload": result["available_actions"]
            })

        # Send behind-the-scenes reveals if any
        if result.get("behind_scenes_reveals"):
            await self.send_message(session_id, {
                "type": "reveal",
                "payload": {
                    "reveals": result["behind_scenes_reveals"],
                    "requires_ack": True
                }
            })

        # Send insight quota update
        if result.get("insight_quota_remaining"):
            await self.send_message(session_id, {
                "type": "insight_update",
                "payload": result["insight_quota_remaining"]
            })

        # Send decision prompt if pending
        if result.get("pending_decision"):
            await self.send_message(session_id, {
                "type": "decision_prompt",
                "payload": result["pending_decision"]
            })

        # Send scene transition if complete
        if result.get("scene_complete"):
            await self.send_message(session_id, {
                "type": "scene_complete",
                "payload": {
                    "scene_summary": result.get("scene_summary"),
                    "next_scene": None  # Will be determined by game flow
                }
            })

        return {"type": "ack", "action_processed": True}

    async def _handle_insight(
        self,
        session_id: str,
        payload: Dict[str, Any],
        game_engine
    ) -> Dict[str, Any]:
        """Handle insight usage"""
        result = await game_engine.use_insight(
            session_id,
            payload.get("insight_type"),
            payload.get("target")
        )

        if not result.get("success"):
            return {
                "type": "error",
                "error": result.get("error", "Insight failed")
            }

        # Send insight reveal
        await self.send_message(session_id, {
            "type": "insight_reveal",
            "payload": {
                "revealed_content": result["revealed"],
                "quota_remaining": result["quota_remaining"]
            }
        })

        return {"type": "ack", "insight_used": True}

    async def _handle_get_state(
        self,
        session_id: str,
        game_engine
    ) -> Dict[str, Any]:
        """Handle state request"""
        state = await game_engine.get_game_state(session_id)

        if not state:
            return {
                "type": "error",
                "error": "Session not found"
            }

        return {
            "type": "state_update",
            "payload": state
        }

    async def _handle_scene_transition(
        self,
        session_id: str,
        payload: Dict[str, Any],
        game_engine
    ) -> Dict[str, Any]:
        """Handle scene transition request"""
        new_scene = payload.get("new_scene")

        result = await game_engine.transition_to_scene(session_id, new_scene)

        if "error" in result:
            return {
                "type": "error",
                "error": result["error"]
            }

        # Send scene transition
        await self.send_message(session_id, {
            "type": "scene_transition",
            "payload": {
                "from": result.get("from_scene"),
                "to": result["current_scene"],
                "transition_text": result["narrative_text"]
            }
        })

        # Send initial state for new scene
        await self.send_message(session_id, {
            "type": "narrative",
            "payload": {
                "text": result["narrative_text"],
                "emotion_beat": "",
                "typing_effect": True
            }
        })

        await self.send_message(session_id, {
            "type": "available_actions",
            "payload": result["available_actions"]
        })

        return {"type": "ack", "scene_transitioned": True}


# Message formatters for frontend
def format_narrative_message(
    text: str,
    emotion_beat: str = "",
    typing_effect: bool = True
) -> Dict[str, Any]:
    """Format narrative message"""
    return {
        "type": "narrative",
        "payload": {
            "text": text,
            "emotion_beat": emotion_beat,
            "typing_effect": typing_effect
        }
    }


def format_reveal_message(
    reveals: List[Dict[str, Any]],
    requires_ack: bool = True
) -> Dict[str, Any]:
    """Format reveal message"""
    return {
        "type": "reveal",
        "payload": {
            "reveals": reveals,
            "requires_ack": requires_ack
        }
    }


def format_decision_prompt(
    decision_id: str,
    description: str,
    choices: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Format decision prompt"""
    return {
        "type": "decision_prompt",
        "payload": {
            "decision_id": decision_id,
            "description": description,
            "choices": choices
        }
    }


def format_scene_transition(
    from_scene: str,
    to_scene: str,
    transition_text: str
) -> Dict[str, Any]:
    """Format scene transition"""
    return {
        "type": "scene_transition",
        "payload": {
            "from": from_scene,
            "to": to_scene,
            "transition_text": transition_text
        }
    }


# Global instance
ws_manager = WebSocketManager()
