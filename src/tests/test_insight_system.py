# /src/tests/test_insight_system.py
# Tests for Insight System

import pytest
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.insight_system import InsightSystem, InsightType


@pytest.fixture
def insight_system():
    return InsightSystem()


@pytest.fixture
def mock_state():
    return {
        "session_id": "test-session",
        "turn_count": 1,
        "player_insights": {
            "true_purpose_remaining": 2,
            "behind_dialogue_remaining": 2,
            "scene_id": "scene-0-wuzhishan",
            "used_in_this_scene": []
        },
        "hidden_layers_generated": {
            "wukong_s0": {
                "speaker": "悟空（山下存在）",
                "true_intent": "不确定。可能清醒，可能半梦半醒，可能已经遗忘了自己是谁。",
                "reasoning": ["被压太久", "记忆可能已被侵蚀"],
                "true_emotional_state": "迷茫",
                "next_move_plan": "继续沉睡"
            }
        },
        "dfs_chain": [
            {
                "turn": 1,
                "speaker": "哪吒",
                "target": "李靖",
                "observable": {"speech_content": "父亲..."},
                "hidden": {"true_intent": "渴望被阻止"}
            }
        ]
    }


def test_initialize_scene(insight_system):
    """Test scene initialization"""
    quota = insight_system.initialize_scene("scene-1-chentangguan")

    assert quota["true_purpose_remaining"] == 2
    assert quota["behind_dialogue_remaining"] == 2
    assert quota["scene_id"] == "scene-1-chentangguan"
    assert quota["used_in_this_scene"] == []


def test_check_available_insights(insight_system, mock_state):
    """Test checking available insights"""
    available = insight_system.check_available_insights(mock_state, "test-location")

    assert len(available) == 2
    assert any(a["type"] == "true_purpose" for a in available)
    assert any(a["type"] == "behind_dialogue" for a in available)


def test_consume_insight_true_purpose(insight_system, mock_state):
    """Test consuming true_purpose insight"""
    result = insight_system.consume_insight(
        mock_state,
        "true_purpose",
        "wukong_s0",
        "test query"
    )

    assert result["success"] is True
    assert result["quota_remaining"]["true_purpose"] == 1
    assert result["quota_remaining"]["behind_dialogue"] == 2
    assert "revealed" in result
    assert result["revealed"]["type"] == "true_purpose"
    assert result["revealed"]["npc_id"] == "wukong_s0"


def test_consume_insight_behind_dialogue(insight_system, mock_state):
    """Test consuming behind_dialogue insight"""
    result = insight_system.consume_insight(
        mock_state,
        "behind_dialogue",
        "test-query",
        "test query"
    )

    assert result["success"] is True
    assert result["quota_remaining"]["true_purpose"] == 2
    assert result["quota_remaining"]["behind_dialogue"] == 1
    assert "revealed" in result
    assert result["revealed"]["type"] == "behind_dialogue"


def test_consume_insight_no_quota(insight_system, mock_state):
    """Test consuming insight when no quota remains"""
    # Deplete quota
    mock_state["player_insights"]["true_purpose_remaining"] = 0

    result = insight_system.consume_insight(
        mock_state,
        "true_purpose",
        "wukong_s0",
        "test query"
    )

    assert result["success"] is False
    assert "error" in result


def test_consume_insight_invalid_type(insight_system, mock_state):
    """Test consuming insight with invalid type"""
    result = insight_system.consume_insight(
        mock_state,
        "invalid_type",
        "target",
        "test query"
    )

    assert result["success"] is False
    assert "error" in result


def test_reveal_true_purpose_no_hidden_data(insight_system, mock_state):
    """Test revealing true purpose when no hidden data exists"""
    # Remove hidden data
    mock_state["hidden_layers_generated"] = {}

    result = insight_system.consume_insight(
        mock_state,
        "true_purpose",
        "unknown_npc",
        "test query"
    )

    # Should fail gracefully or return default
    assert result["success"] is True  # Consumes insight
    assert "revealed" in result


def test_generate_scene_debrief_no_insights(insight_system, mock_state):
    """Test scene debrief when no insights used"""
    debrief = insight_system.generate_scene_debrief(mock_state)

    assert debrief["debrief_type"] == "full"
    assert "all_hidden_intents" in debrief
    assert "all_dfs_chains" in debrief


def test_generate_scene_debrief_with_insights(insight_system, mock_state):
    """Test scene debrief when insights were used"""
    # Use an insight first
    insight_system.consume_insight(
        mock_state,
        "true_purpose",
        "wukong_s0",
        "test query"
    )

    debrief = insight_system.generate_scene_debrief(mock_state)

    assert debrief["debrief_type"] == "partial"
    assert "insights_used" in debrief
    assert len(debrief["insights_used"]) == 1


def test_get_quota_status(insight_system, mock_state):
    """Test getting quota status"""
    status = insight_system.get_quota_status(mock_state)

    assert status["true_purpose"] == 2
    assert status["behind_dialogue"] == 2


def test_usage_history_tracking(insight_system, mock_state):
    """Test that usage history is tracked"""
    initial_count = len(insight_system.usage_history)

    insight_system.consume_insight(
        mock_state,
        "true_purpose",
        "wukong_s0",
        "test query"
    )

    assert len(insight_system.usage_history) == initial_count + 1
    last_usage = insight_system.usage_history[-1]
    assert last_usage.insight_type == InsightType.TRUE_PURPOSE
    assert last_usage.target == "wukong_s0"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
