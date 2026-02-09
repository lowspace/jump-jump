# /src/tests/test_npc_agents.py
# Tests for NPC Agents

import pytest
import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.npc_agents import NPCAgent, NPCAgentPool, NPCLayer


@pytest.fixture
def npc_agent():
    config = {
        "initial_state": {
            "trust": 3,
            "emotional_state": "guarded"
        },
        "hidden_intent": {
            "core": "渴望被理解"
        }
    }
    return NPCAgent(
        npc_id="test_npc",
        name="测试NPC",
        scene="scene-test",
        layer=NPCLayer.ACTIVE,
        config=config
    )


@pytest.fixture
def npc_pool():
    return NPCAgentPool()


def test_npc_agent_initialization(npc_agent):
    """Test NPC agent initialization"""
    assert npc_agent.npc_id == "test_npc"
    assert npc_agent.name == "测试NPC"
    assert npc_agent.trust == 3
    assert npc_agent.emotional_state == "guarded"


@pytest.mark.asyncio
async def test_npc_process_input(npc_agent):
    """Test NPC processing input"""
    context = {
        "variables": {},
        "current_dialogue_node": None
    }

    response = await npc_agent.process_input(
        "你好",
        context,
        turn=1
    )

    assert response.npc_id == "test_npc"
    assert response.observable.speaker == "测试NPC"
    assert response.hidden.speaker == "测试NPC"
    assert response.hidden.true_intent == "渴望被理解"


def test_npc_update_state(npc_agent):
    """Test updating NPC state"""
    npc_agent.update_state({
        "trust": 5,
        "emotional_state": "open"
    })

    assert npc_agent.trust == 5
    assert npc_agent.emotional_state == "open"


def test_npc_to_state_card(npc_agent):
    """Test converting NPC to state card"""
    card = npc_agent.to_state_card()

    assert card["npc_id"] == "test_npc"
    assert card["name"] == "测试NPC"
    assert card["trust"] == 3
    assert card["layer"] == "active"


def test_npc_pool_add(npc_pool, npc_agent):
    """Test adding NPC to pool"""
    npc_pool.add_npc(npc_agent, NPCLayer.ACTIVE)

    assert len(npc_pool.active_npcs) == 1
    assert "test_npc" in npc_pool.active_npcs


def test_npc_pool_get(npc_pool, npc_agent):
    """Test getting NPC from pool"""
    npc_pool.add_npc(npc_agent, NPCLayer.ACTIVE)

    retrieved = npc_pool.get_npc("test_npc")
    assert retrieved is not None
    assert retrieved.npc_id == "test_npc"


def test_npc_pool_get_nonexistent(npc_pool):
    """Test getting non-existent NPC"""
    retrieved = npc_pool.get_npc("nonexistent")
    assert retrieved is None


def test_npc_pool_activate(npc_pool, npc_agent):
    """Test activating NPC"""
    # Add to background first
    npc_pool.add_npc(npc_agent, NPCLayer.BACKGROUND)
    assert "test_npc" in npc_pool.background_npcs

    # Activate
    activated = npc_pool.activate_npc("test_npc")
    assert activated is not None
    assert "test_npc" in npc_pool.active_npcs
    assert "test_npc" not in npc_pool.background_npcs


def test_npc_pool_max_active_limit(npc_pool):
    """Test max active NPC limit"""
    # Add 5 NPCs (max is 4)
    for i in range(5):
        npc = NPCAgent(
            npc_id=f"npc_{i}",
            name=f"NPC {i}",
            scene="scene-test"
        )
        npc_pool.add_npc(npc, NPCLayer.ACTIVE)

    # Should only have 4 active
    assert len(npc_pool.active_npcs) == 4
    # Oldest should be moved to background
    assert len(npc_pool.background_npcs) == 1


def test_npc_pool_max_background_limit(npc_pool):
    """Test max background NPC limit"""
    # Add 12 NPCs to background (max is 10)
    for i in range(12):
        npc = NPCAgent(
            npc_id=f"npc_{i}",
            name=f"NPC {i}",
            scene="scene-test"
        )
        npc_pool.add_npc(npc, NPCLayer.BACKGROUND)

    # Should only have 10 background
    assert len(npc_pool.background_npcs) == 10
    # Oldest should be moved to dormant
    assert len(npc_pool.dormant_cards) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
