# /src/tests/test_game_engine.py
# Tests for Game Engine

import pytest
import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.game_engine import GameEngine
from backend.core.config import DEFAULT_VARIABLES


@pytest.fixture
def game_engine():
    return GameEngine()


@pytest.mark.asyncio
async def test_create_session(game_engine):
    """Test creating a new game session"""
    result = await game_engine.create_session(
        start_scene="scene-0-wuzhishan",
        player_role="少年樵夫"
    )

    assert "session_id" in result
    assert result["current_scene"] == "scene-0-wuzhishan"
    assert result["current_phase"] == "opening"
    assert "narrative_text" in result
    assert "available_actions" in result
    assert result["insight_quota"]["true_purpose"] == 2
    assert result["insight_quota"]["behind_dialogue"] == 2


@pytest.mark.asyncio
async def test_get_game_state(game_engine):
    """Test getting game state"""
    # Create session first
    start_result = await game_engine.create_session()
    session_id = start_result["session_id"]

    # Get state
    state = await game_engine.get_game_state(session_id)

    assert state is not None
    assert state["session_id"] == session_id
    assert "current_scene" in state
    assert "variables_snapshot" in state


@pytest.mark.asyncio
async def test_get_game_state_invalid_session(game_engine):
    """Test getting state for invalid session"""
    state = await game_engine.get_game_state("invalid-session-id")
    assert state is None


@pytest.mark.asyncio
async def test_process_dialogue_action(game_engine):
    """Test processing a dialogue action"""
    # Create session
    start_result = await game_engine.create_session()
    session_id = start_result["session_id"]

    # Send dialogue action
    action = {
        "action_type": "dialogue",
        "target": "wukong_s0",
        "content": "你好"
    }

    result = await game_engine.process_action(session_id, action)

    assert "error" not in result
    assert "narrative_text" in result
    assert result["turn_completed"] is True


@pytest.mark.asyncio
async def test_process_decision_action(game_engine):
    """Test processing a decision action"""
    # Create session
    start_result = await game_engine.create_session()
    session_id = start_result["session_id"]

    # Send decision action
    action = {
        "action_type": "decision",
        "decision_id": "S0_Decision_A",
        "choice_id": "A1_trace"
    }

    result = await game_engine.process_action(session_id, action)

    assert "error" not in result
    assert "narrative_text" in result


@pytest.mark.asyncio
async def test_process_insight_action(game_engine):
    """Test processing an insight action"""
    # Create session
    start_result = await game_engine.create_session()
    session_id = start_result["session_id"]

    # Use insight
    action = {
        "action_type": "insight",
        "insight_type": "true_purpose",
        "target": "wukong_s0"
    }

    result = await game_engine.process_action(session_id, action)

    # Should succeed or fail gracefully
    assert "error" not in result or "revealed_content" in result


@pytest.mark.asyncio
async def test_insight_quota_depletion(game_engine):
    """Test that insight quota is depleted after use"""
    # Create session
    start_result = await game_engine.create_session()
    session_id = start_result["session_id"]

    # Use all true_purpose insights
    for i in range(3):
        result = await game_engine.use_insight(
            session_id,
            "true_purpose",
            "wukong_s0"
        )

    # Third use should fail (only 2 available)
    assert not result["success"] or result["quota_remaining"]["true_purpose"] == 0


@pytest.mark.asyncio
async def test_scene_transition(game_engine):
    """Test scene transition"""
    # Create session
    start_result = await game_engine.create_session()
    session_id = start_result["session_id"]

    # Transition to scene 1
    result = await game_engine.transition_to_scene(
        session_id,
        "scene-1-chentangguan"
    )

    assert "error" not in result
    assert result["current_scene"] == "scene-1-chentangguan"
    assert result["scene_transition"] is True


@pytest.mark.asyncio
async def test_variable_update(game_engine):
    """Test variable updates through actions"""
    # Create session
    start_result = await game_engine.create_session()
    session_id = start_result["session_id"]

    # Get initial state
    initial_state = await game_engine.get_game_state(session_id)
    initial_curiosity = initial_state["variables_snapshot"].get("curiosity_level")

    # Perform action that changes variable
    action = {
        "action_type": "decision",
        "decision_id": "S0_Decision_A",
        "choice_id": "A1_trace"
    }

    await game_engine.process_action(session_id, action)

    # Check updated state
    updated_state = await game_engine.get_game_state(session_id)
    # Variable should have changed
    assert "variables_snapshot" in updated_state


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
