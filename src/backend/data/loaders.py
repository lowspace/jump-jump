# /src/backend/data/loaders.py
# Data loaders for NPC configs, decision flows, and scene texts

import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Base path for data files
DATA_DIR = Path(__file__).parent
NPCS_DIR = DATA_DIR / "npcs"
DECISIONS_DIR = DATA_DIR / "decisions"
SCENES_DIR = DATA_DIR / "scenes"


@dataclass
class NPCConfig:
    """NPC configuration loaded from YAML"""
    npc_id: str
    name: str
    scene: str
    description: str
    initial_state: Dict[str, Any]
    hidden_intent: Dict[str, Any]
    dialogue_nodes: List[Dict[str, Any]]
    insight_opportunities: List[Dict[str, Any]]
    variable_effects: Dict[str, List[Dict[str, Any]]]
    raw_config: Dict[str, Any]


@dataclass
class DecisionConfig:
    """Decision flow configuration loaded from YAML"""
    decision_id: str
    decision_name: str
    scene: str
    phase: str
    context: str
    prerequisite: Optional[str]
    choices: List[Dict[str, Any]]
    variable_effects: Dict[str, Any]
    raw_config: Dict[str, Any]


class DataLoader:
    """Load and cache game configuration data"""

    _npc_cache: Dict[str, NPCConfig] = {}
    _decision_cache: Dict[str, DecisionConfig] = {}
    _scene_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def load_npc_configs(cls) -> Dict[str, NPCConfig]:
        """Load all NPC configurations from YAML files"""
        if cls._npc_cache:
            return cls._npc_cache

        configs = {}
        for yaml_file in NPCS_DIR.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    raw = yaml.safe_load(f)

                npc_id = raw.get('npc_id', yaml_file.stem)
                configs[npc_id] = NPCConfig(
                    npc_id=npc_id,
                    name=raw.get('name', 'Unknown'),
                    scene=raw.get('scene', ''),
                    description=raw.get('description', ''),
                    initial_state=raw.get('initial_state', {}),
                    hidden_intent=raw.get('hidden_intent', {}),
                    dialogue_nodes=raw.get('dialogue_nodes', []),
                    insight_opportunities=raw.get('insight_opportunities', []),
                    variable_effects=raw.get('variable_effects', {}),
                    raw_config=raw
                )
            except Exception as e:
                print(f"Error loading NPC config {yaml_file}: {e}")

        cls._npc_cache = configs
        return configs

    @classmethod
    def load_npc_by_id(cls, npc_id: str) -> Optional[NPCConfig]:
        """Load a specific NPC configuration"""
        configs = cls.load_npc_configs()
        return configs.get(npc_id)

    @classmethod
    def load_npcs_by_scene(cls, scene_id: str) -> List[NPCConfig]:
        """Load all NPCs for a specific scene"""
        configs = cls.load_npc_configs()
        return [npc for npc in configs.values() if npc.scene == scene_id]

    @classmethod
    def load_decision_configs(cls) -> Dict[str, DecisionConfig]:
        """Load all decision flow configurations from YAML files"""
        if cls._decision_cache:
            return cls._decision_cache

        configs = {}
        for yaml_file in DECISIONS_DIR.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    raw = yaml.safe_load(f)

                decision_id = raw.get('decision_id', yaml_file.stem)
                configs[decision_id] = DecisionConfig(
                    decision_id=decision_id,
                    decision_name=raw.get('decision_name', 'Unknown'),
                    scene=raw.get('scene', ''),
                    phase=raw.get('phase', ''),
                    context=raw.get('context', ''),
                    prerequisite=raw.get('prerequisite'),
                    choices=raw.get('choices', []),
                    variable_effects=raw.get('variable_effects', {}),
                    raw_config=raw
                )
            except Exception as e:
                print(f"Error loading decision config {yaml_file}: {e}")

        cls._decision_cache = configs
        return configs

    @classmethod
    def load_decision_by_id(cls, decision_id: str) -> Optional[DecisionConfig]:
        """Load a specific decision configuration"""
        configs = cls.load_decision_configs()
        return configs.get(decision_id)

    @classmethod
    def load_decisions_by_scene(cls, scene_id: str) -> List[DecisionConfig]:
        """Load all decisions for a specific scene"""
        configs = cls.load_decision_configs()
        return [d for d in configs.values() if d.scene == scene_id]

    @classmethod
    def get_scene_narrative(cls, scene_id: str, narrative_id: str) -> str:
        """Get scene narrative text"""
        scene_file = SCENES_DIR / f"{scene_id}.json"
        if scene_file.exists():
            with open(scene_file, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
                return scene_data.get('narratives', {}).get(narrative_id, '')
        return ''

    @classmethod
    def get_opening_narrative(cls, scene_id: str) -> str:
        """Get opening narrative for a scene"""
        # Try to load from scene file
        scene_file = SCENES_DIR / f"{scene_id}.json"
        if scene_file.exists():
            with open(scene_file, 'r', encoding='utf-8') as f:
                scene_data = json.load(f)
                return scene_data.get('opening', '')

        # Default opening narratives
        defaults = {
            "scene-0-wuzhishan": "你站在五指山上。风吹过烧焦的桃树残根，带来远处山下的气息。",
            "scene-1-chentangguan": "你是陈塘关的武师。今日，总兵李靖的第三子哪吒又惹了祸。",
            "scene-2-tianhe": "你是天河的记账仙官陆执。今日，你发现了不该发现的账目。",
            "scene-3-huaguoshan": "你是花果山的一只幼猴。大王已经不在了，但山还在。",
            "scene-4-lingtai": "你是灵台方寸山的抄经僧法明。今日，你发现经书是空白的。",
        }
        return defaults.get(scene_id, "场景开始。")

    @classmethod
    def clear_cache(cls):
        """Clear all cached data"""
        cls._npc_cache.clear()
        cls._decision_cache.clear()
        cls._scene_cache.clear()


# Convenience functions
def get_npc(npc_id: str) -> Optional[NPCConfig]:
    """Get NPC configuration by ID"""
    return DataLoader.load_npc_by_id(npc_id)


def get_decision(decision_id: str) -> Optional[DecisionConfig]:
    """Get decision configuration by ID"""
    return DataLoader.load_decision_by_id(decision_id)


def get_scene_npcs(scene_id: str) -> List[NPCConfig]:
    """Get all NPCs for a scene"""
    return DataLoader.load_npcs_by_scene(scene_id)


def get_scene_decisions(scene_id: str) -> List[DecisionConfig]:
    """Get all decisions for a scene"""
    return DataLoader.load_decisions_by_scene(scene_id)


def get_dialogue_node(npc_id: str, node_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific dialogue node for an NPC"""
    npc = get_npc(npc_id)
    if npc:
        for node in npc.dialogue_nodes:
            if node.get('node_id') == node_id:
                return node
    return None


def get_decision_choices(decision_id: str) -> List[Dict[str, Any]]:
    """Get choices for a decision"""
    decision = get_decision(decision_id)
    if decision:
        return decision.choices
    return []
