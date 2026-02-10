# /src/backend/app/state_manager.py
# State Manager for Jump Jump - Session persistence and state management

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..core.config import db_config, DEFAULT_VARIABLES, SCENE_ORDER
from ..core.state_schema import GameState


class StateManager:
    """
    State Manager for game session persistence

    Handles:
    - Session creation and loading
    - State persistence (SQLite)
    - Auto-save checkpoints
    - State serialization/deserialization
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or db_config.DB_PATH
        self._ensure_db()

    def _ensure_db(self):
        """Ensure database and tables exist"""
        # Create directory if needed
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_sessions (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                current_scene TEXT NOT NULL,
                current_phase TEXT NOT NULL,
                state_json TEXT NOT NULL
            )
        """)

        # Create checkpoints table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                turn_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                state_json TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES game_sessions(session_id)
            )
        """)

        conn.commit()
        conn.close()

    def create_session(
        self,
        start_scene: str = "scene-0-wuzhishan",
        player_role: str = "少年樵夫"
    ) -> str:
        """Create a new game session"""
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        # Initialize state
        state: GameState = {
            "session_id": session_id,
            "created_at": now,
            "updated_at": now,
            "current_scene": start_scene,
            "current_phase": "opening",
            "completed_phases": [],
            "turn_count": 0,
            "player_role": player_role,
            "player_insights": {
                "true_purpose_remaining": 2,
                "behind_dialogue_remaining": 2,
                "scene_id": start_scene,
                "used_in_this_scene": []
            },
            "player_history": [],
            "faith_erosion_level": 0,
            "belief_reconstruction": None,
            "variables": DEFAULT_VARIABLES.copy(),
            "echoes_triggered": [],
            "echoes_pending": [],
            "npc_registry": {},
            "active_npcs": [],
            "background_npcs": [],
            "current_npc": None,
            "dialogue_context": [],
            "pending_decision": None,
            "bfs_results": [],
            "dfs_chain": [],
            "gm_arbitration": {},
            "behind_scenes_queue": [],
            "insights_used_this_scene": [],
            "hidden_layers_generated": {},
            "pending_propagations": [],
            "error_count": 0,
            "last_checkpoint": now
        }

        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO game_sessions
            (session_id, created_at, updated_at, current_scene, current_phase, state_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                now,
                now,
                start_scene,
                "opening",
                json.dumps(state, ensure_ascii=False)
            )
        )
        conn.commit()
        conn.close()

        return session_id

    def load_session(self, session_id: str) -> Optional[GameState]:
        """Load a game session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT state_json FROM game_sessions WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            state_dict = json.loads(row[0])
            return state_dict
        return None

    def save_session(self, state: GameState) -> bool:
        """Save a game session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            now = datetime.now().isoformat()
            state["updated_at"] = now

            cursor.execute(
                """
                UPDATE game_sessions
                SET updated_at = ?, current_scene = ?, current_phase = ?, state_json = ?
                WHERE session_id = ?
                """,
                (
                    now,
                    state["current_scene"],
                    state["current_phase"],
                    json.dumps(state, ensure_ascii=False),
                    state["session_id"]
                )
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False

    def create_checkpoint(self, state: GameState) -> str:
        """Create a checkpoint for the current state"""
        checkpoint_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO checkpoints
            (checkpoint_id, session_id, turn_count, created_at, state_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                checkpoint_id,
                state["session_id"],
                state["turn_count"],
                now,
                json.dumps(state, ensure_ascii=False)
            )
        )
        conn.commit()
        conn.close()

        # Update last checkpoint time
        state["last_checkpoint"] = now

        return checkpoint_id

    def load_checkpoint(self, checkpoint_id: str) -> Optional[GameState]:
        """Load a specific checkpoint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT state_json FROM checkpoints WHERE checkpoint_id = ?",
            (checkpoint_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return None

    def get_session_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all checkpoints for a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT checkpoint_id, turn_count, created_at
            FROM checkpoints
            WHERE session_id = ?
            ORDER BY turn_count DESC
            """,
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "checkpoint_id": row[0],
                "turn_count": row[1],
                "created_at": row[2]
            }
            for row in rows
        ]

    def update_variable(
        self,
        state: GameState,
        var_name: str,
        new_value: Any,
        reason: str = ""
    ) -> Dict[str, Any]:
        """Update a variable and record the change"""
        old_value = state["variables"].get(var_name)
        state["variables"][var_name] = new_value

        # Add to behind-the-scenes queue
        change_record = {
            "type": "variable_change",
            "var": var_name,
            "old": old_value,
            "new": new_value,
            "reason": reason,
            "turn": state["turn_count"]
        }
        state["behind_scenes_queue"].append(change_record)

        return change_record

    def advance_turn(self, state: GameState) -> int:
        """Advance turn counter"""
        state["turn_count"] += 1

        # Auto-save checkpoint every N turns
        if state["turn_count"] % 5 == 0:
            self.create_checkpoint(state)

        return state["turn_count"]

    def transition_scene(self, state: GameState, new_scene: str) -> bool:
        """Transition to a new scene"""
        # Validate scene order
        current_idx = SCENE_ORDER.index(state["current_scene"]) if state["current_scene"] in SCENE_ORDER else -1
        new_idx = SCENE_ORDER.index(new_scene) if new_scene in SCENE_ORDER else -1

        if new_idx < current_idx and new_scene != "scene-0-wuzhishan":
            # Allow going back to scene 0 (rerender), but not other scenes
            print(f"Warning: Attempting to go back from {state['current_scene']} to {new_scene}")

        # Reset scene-specific state
        state["current_scene"] = new_scene
        state["current_phase"] = "opening"
        state["turn_count"] = 0
        state["completed_phases"] = []
        state["dialogue_context"] = []
        state["pending_decision"] = None
        state["bfs_results"] = []
        state["dfs_chain"] = []
        state["gm_arbitration"] = {}
        state["behind_scenes_queue"] = []
        state["insights_used_this_scene"] = []
        state["hidden_layers_generated"] = {}

        # Reset insight quota for new scene
        state["player_insights"] = {
            "true_purpose_remaining": 2,
            "behind_dialogue_remaining": 2,
            "scene_id": new_scene,
            "used_in_this_scene": []
        }

        return True

    def record_player_action(
        self,
        state: GameState,
        action_type: str,
        content: str,
        target: Optional[str] = None
    ):
        """Record a player action"""
        action = {
            "turn": state["turn_count"],
            "action_type": action_type,
            "target": target,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        state["player_history"].append(action)

    def get_player_history(
        self,
        state: GameState,
        action_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get player action history"""
        history = state["player_history"]

        if action_type:
            history = [h for h in history if h["action_type"] == action_type]

        return history[-limit:]

    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent sessions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT session_id, created_at, updated_at, current_scene, current_phase
            FROM game_sessions
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "session_id": row[0],
                "created_at": row[1],
                "updated_at": row[2],
                "current_scene": row[3],
                "current_phase": row[4]
            }
            for row in rows
        ]

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its checkpoints"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Delete checkpoints first
            cursor.execute(
                "DELETE FROM checkpoints WHERE session_id = ?",
                (session_id,)
            )

            # Delete session
            cursor.execute(
                "DELETE FROM game_sessions WHERE session_id = ?",
                (session_id,)
            )

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False


# Global instance
state_manager = StateManager()
