# /src/tests/test_state_manager.py
# Tests for State Manager

import pytest
import sys
import os
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.state_manager import StateManager
from backend.core.config import DEFAULT_VARIABLES


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def state_manager(temp_db):
    return StateManager(db_path=temp_db)


def test_create_session(state_manager):
    """Test creating a new session"""
    session_id = state_manager.create_session(
        start_scene="scene-0-wuzhishan",
        player_role="少年樵夫"
    )

    assert session_id is not None
    assert len(session_id) > 0


def test_load_session(state_manager):
    """Test loading a session"""
    session_id = state_manager.create_session()
    state = state_manager.load_session(session_id)

    assert state is not None
    assert state["session_id"] == session_id
    assert state["current_scene"] == "scene-0-wuzhishan"
    assert state["player_role"] == "少年樵夫"


def test_load_nonexistent_session(state_manager):
    """Test loading a non-existent session"""
    state = state_manager.load_session("nonexistent-id")
    assert state is None


def test_save_session(state_manager):
    """Test saving a session"""
    session_id = state_manager.create_session()
    state = state_manager.load_session(session_id)

    # Modify state
    state["turn_count"] = 5
    state["variables"]["curiosity_level"] = "high"

    # Save
    success = state_manager.save_session(state)
    assert success is True

    # Reload and verify
    loaded_state = state_manager.load_session(session_id)
    assert loaded_state["turn_count"] == 5
    assert loaded_state["variables"]["curiosity_level"] == "high"


def test_update_variable(state_manager):
    """Test updating a variable"""
    session_id = state_manager.create_session()
    state = state_manager.load_session(session_id)

    # Update variable
    change = state_manager.update_variable(
        state,
        "curiosity_level",
        "high",
        reason="Test update"
    )

    assert change["var"] == "curiosity_level"
    assert change["new"] == "high"
    assert change["reason"] == "Test update"
    assert state["variables"]["curiosity_level"] == "high"


def test_advance_turn(state_manager):
    """Test advancing turn counter"""
    session_id = state_manager.create_session()
    state = state_manager.load_session(session_id)

    initial_turn = state["turn_count"]
    new_turn = state_manager.advance_turn(state)

    assert new_turn == initial_turn + 1
    assert state["turn_count"] == initial_turn + 1


def test_record_player_action(state_manager):
    """Test recording player actions"""
    session_id = state_manager.create_session()
    state = state_manager.load_session(session_id)

    state_manager.record_player_action(
        state,
        "dialogue",
        "Hello",
        "wukong_s0"
    )

    assert len(state["player_history"]) == 1
    assert state["player_history"][0]["action_type"] == "dialogue"
    assert state["player_history"][0]["content"] == "Hello"
    assert state["player_history"][0]["target"] == "wukong_s0"


def test_get_player_history(state_manager):
    """Test getting player history"""
    session_id = state_manager.create_session()
    state = state_manager.load_session(session_id)

    # Add some actions
    for i in range(5):
        state_manager.record_player_action(state, "dialogue", f"Message {i}")

    # Get all history
    history = state_manager.get_player_history(state)
    assert len(history) == 5

    # Get limited history
    limited = state_manager.get_player_history(state, limit=3)
    assert len(limited) == 3

    # Get by type
    dialogue_history = state_manager.get_player_history(state, action_type="dialogue")
    assert len(dialogue_history) == 5


def test_create_checkpoint(state_manager):
    """Test creating checkpoints"""
    session_id = state_manager.create_session()
    state = state_manager.load_session(session_id)

    # Advance a few turns
    for _ in range(3):
        state_manager.advance_turn(state)
    state_manager.save_session(state)

    # Create checkpoint
    checkpoint_id = state_manager.create_checkpoint(state)
    assert checkpoint_id is not None

    # Load checkpoint
    checkpoint_state = state_manager.load_checkpoint(checkpoint_id)
    assert checkpoint_state is not None
    assert checkpoint_state["turn_count"] == 3


def test_get_session_checkpoints(state_manager):
    """Test getting session checkpoints"""
    session_id = state_manager.create_session()
    state = state_manager.load_session(session_id)

    # Create multiple checkpoints
    for _ in range(3):
        state_manager.advance_turn(state)
        state_manager.create_checkpoint(state)

    checkpoints = state_manager.get_session_checkpoints(session_id)
    assert len(checkpoints) == 3


def test_transition_scene(state_manager):
    """Test scene transition"""
    session_id = state_manager.create_session()
    state = state_manager.load_session(session_id)

    # Add some scene-specific data
    state["dialogue_context"] = [{"speaker": "test", "content": "test"}]
    state["turn_count"] = 5

    # Transition
    success = state_manager.transition_scene(state, "scene-1-chentangguan")
    assert success is True

    # Verify reset
    assert state["current_scene"] == "scene-1-chentangguan"
    assert state["current_phase"] == "opening"
    assert state["dialogue_context"] == []
    assert state["turn_count"] == 5  # Turn count should persist

    # Verify insight quota reset
    assert state["player_insights"]["true_purpose_remaining"] == 2
    assert state["player_insights"]["behind_dialogue_remaining"] == 2


def test_list_sessions(state_manager):
    """Test listing sessions"""
    # Create multiple sessions
    ids = []
    for _ in range(3):
        sid = state_manager.create_session()
        ids.append(sid)

    sessions = state_manager.list_sessions(limit=10)
    assert len(sessions) == 3


def test_delete_session(state_manager):
    """Test deleting a session"""
    session_id = state_manager.create_session()

    # Verify exists
    assert state_manager.load_session(session_id) is not None

    # Delete
    success = state_manager.delete_session(session_id)
    assert success is True

    # Verify deleted
    assert state_manager.load_session(session_id) is None


def test_default_variables(state_manager):
    """Test that default variables are set correctly"""
    session_id = state_manager.create_session()
    state = state_manager.load_session(session_id)

    # Check key variables exist
    assert "variables" in state
    assert "nezha_trust" in state["variables"]
    assert "faith_erosion_level" in state
    assert state["faith_erosion_level"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
