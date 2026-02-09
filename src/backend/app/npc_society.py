# /src/backend/app/npc_society.py
# NPC Society Simulation - Simplified but correct version
# NPCs can communicate, share info, and form relationships behind the scenes

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import asyncio
from datetime import datetime


class PrivacyLevel(Enum):
    """Privacy level for NPC communication"""
    PUBLIC = "public"      # Anyone nearby can hear
    PRIVATE = "private"    # Only intended recipient
    SECRET = "secret"      # Covert, hidden from player


class InfoReliability(Enum):
    """How reliable is this information"""
    CERTAIN = 1.0
    LIKELY = 0.8
    RUMOR = 0.5
    UNSURE = 0.3


@dataclass
class InfoPacket:
    """Structured information that NPCs pass between each other"""
    info_id: str
    content: str
    source_npc: str           # Who originally knew this
    shared_by: str            # Who is sharing it now
    reliability: float
    privacy_level: PrivacyLevel
    timestamp: int
    propagation_count: int = 0  # How many times this has been shared

    def to_observable(self) -> Dict[str, Any]:
        """Convert to what other NPCs can observe"""
        return {
            "info_id": self.info_id,
            "content_summary": self.content[:50] + "..." if len(self.content) > 50 else self.content,
            "source": self.source_npc,
            "shared_by": self.shared_by,
            "reliability": self.reliability,
            "privacy": self.privacy_level.value,
        }


@dataclass
class NPCToolCall:
    """A tool call that an NPC wants to make"""
    tool_name: str
    params: Dict[str, Any]
    reason: str


@dataclass
class NPCInternalState:
    """Internal state of an NPC agent"""
    npc_id: str
    name: str

    # Information domain
    known_info: Dict[str, InfoPacket] = field(default_factory=dict)
    beliefs: Dict[str, float] = field(default_factory=dict)  # What they believe about world state

    # Relationships with other NPCs
    relationships: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    # Format: {npc_id: {"trust": 0-1, "suspicion": 0-1, "shared_secrets": [info_ids]}}

    # Current goals and agenda
    active_goals: List[str] = field(default_factory=list)
    current_agenda: str = ""  # What they're trying to accomplish right now

    # Perception of player
    trust_toward_player: float = 0.5
    suspicion_toward_player: float = 0.0
    player_reputation: Dict[str, Any] = field(default_factory=dict)

    def get_relationship(self, other_npc_id: str) -> Dict[str, Any]:
        """Get relationship with another NPC, creating default if not exists"""
        if other_npc_id not in self.relationships:
            self.relationships[other_npc_id] = {
                "trust": 0.5,
                "suspicion": 0.0,
                "shared_secrets": [],
                "last_interaction": 0,
            }
        return self.relationships[other_npc_id]


class NPCSociety:
    """
    NPC Society - Manages all NPC-to-NPC interactions

    Key features:
    1. Background simulation loop - NPCs talk to each other without player
    2. Information propagation - Info spreads through the network
    3. Relationship evolution - Trust/suspicion changes based on interactions
    4. Observable by player - Can use insight to "overhear" some conversations
    """

    def __init__(self):
        self.npcs: Dict[str, NPCInternalState] = {}
        self.conversation_log: List[Dict[str, Any]] = []  # Record of all NPC-NPC talks
        self.current_turn: int = 0

    def register_npc(self, npc_id: str, name: str, initial_info: List[str] = None):
        """Register an NPC in the society"""
        npc = NPCInternalState(npc_id=npc_id, name=name)
        self.npcs[npc_id] = npc
        return npc

    def add_info_to_npc(self, npc_id: str, info_id: str, content: str,
                       reliability: float = 1.0, source: str = None):
        """Give an NPC some initial information"""
        if npc_id not in self.npcs:
            return

        packet = InfoPacket(
            info_id=info_id,
            content=content,
            source_npc=source or npc_id,
            shared_by=source or npc_id,
            reliability=reliability,
            privacy_level=PrivacyLevel.PRIVATE,
            timestamp=self.current_turn
        )
        self.npcs[npc_id].known_info[info_id] = packet

    def set_relationship(self, npc_a: str, npc_b: str, trust: float = None,
                        suspicion: float = None):
        """Set initial relationship between two NPCs"""
        if npc_a not in self.npcs or npc_b not in self.npcs:
            return

        rel_a = self.npcs[npc_a].get_relationship(npc_b)
        rel_b = self.npcs[npc_b].get_relationship(npc_a)

        if trust is not None:
            rel_a["trust"] = trust
            rel_b["trust"] = trust
        if suspicion is not None:
            rel_a["suspicion"] = suspicion
            rel_b["suspicion"] = suspicion

    # ============ Tool Implementations ============

    def tool_share_info(self, from_npc: str, to_npc: str, info_id: str,
                       privacy: PrivacyLevel = PrivacyLevel.PRIVATE) -> Dict[str, Any]:
        """
        NPC shares information with another NPC

        Rules:
        - Trust affects willingness to share
        - Information reliability may degrade when shared
        - Some info may be withheld based on privacy level
        """
        if from_npc not in self.npcs or to_npc not in self.npcs:
            return {"success": False, "reason": "NPC not found"}

        sender = self.npcs[from_npc]
        recipient = self.npcs[to_npc]
        relationship = sender.get_relationship(to_npc)

        # Check if sender actually knows this info
        if info_id not in sender.known_info:
            return {"success": False, "reason": "Sender doesn't know this info"}

        info_packet = sender.known_info[info_id]

        # Trust check - high trust needed for secret info
        if privacy == PrivacyLevel.SECRET and relationship["trust"] < 0.7:
            return {"success": False, "reason": "Trust too low for secret sharing"}

        # Create new packet for recipient (with possible degradation)
        reliability_degradation = 0.1 * info_packet.propagation_count
        new_reliability = max(0.3, info_packet.reliability - reliability_degradation)

        new_packet = InfoPacket(
            info_id=info_id,
            content=info_packet.content,
            source_npc=info_packet.source_npc,
            shared_by=from_npc,
            reliability=new_reliability,
            privacy_level=privacy,
            timestamp=self.current_turn,
            propagation_count=info_packet.propagation_count + 1
        )

        # Give to recipient
        recipient.known_info[info_id] = new_packet

        # Update relationship - sharing secrets builds trust
        if privacy in [PrivacyLevel.PRIVATE, PrivacyLevel.SECRET]:
            relationship["shared_secrets"].append(info_id)
            relationship["trust"] = min(1.0, relationship["trust"] + 0.1)
            relationship["last_interaction"] = self.current_turn

        # Log the conversation
        self._log_conversation(from_npc, to_npc, "share_info", {
            "info_id": info_id,
            "privacy": privacy.value,
            "success": True
        })

        return {
            "success": True,
            "info_transferred": info_id,
            "reliability": new_reliability,
            "trust_change": +0.1 if privacy == PrivacyLevel.SECRET else 0
        }

    def tool_discuss_with_npc(self, npc_a: str, npc_b: str, topic: str) -> Dict[str, Any]:
        """
        Two NPCs have a discussion about a topic

        Rules:
        - Discussion may reveal shared information
        - Relationship affects what gets revealed
        - Some discussions are about the player
        """
        if npc_a not in self.npcs or npc_b not in self.npcs:
            return {"success": False, "reason": "NPC not found"}

        npc1 = self.npcs[npc_a]
        npc2 = self.npcs[npc_b]
        rel = npc1.get_relationship(npc_b)

        # Determine what gets discussed based on relationship
        shared_knowledge = set(npc1.known_info.keys()) & set(npc2.known_info.keys())
        only_npc1_knows = set(npc1.known_info.keys()) - set(npc2.known_info.keys())
        only_npc2_knows = set(npc2.known_info.keys()) - set(npc1.known_info.keys())

        # If trust is high, NPCs share unique knowledge
        exchanges = []
        if rel["trust"] > 0.5:
            # NPC1 might share something with NPC2
            for info_id in list(only_npc1_knows)[:2]:  # Max 2 pieces
                if random.random() < rel["trust"]:
                    result = self.tool_share_info(npc_a, npc_b, info_id, PrivacyLevel.PRIVATE)
                    if result["success"]:
                        exchanges.append(f"{npc1.name}告诉了{npc2.name}关于{info_id}的事")

        if rel["trust"] > 0.6:
            # NPC2 might share back
            for info_id in list(only_npc2_knows)[:2]:
                if random.random() < rel["trust"]:
                    result = self.tool_share_info(npc_b, npc_a, info_id, PrivacyLevel.PRIVATE)
                    if result["success"]:
                        exchanges.append(f"{npc2.name}告诉了{npc1.name}关于{info_id}的事")

        # Update relationship
        rel["last_interaction"] = self.current_turn

        # Log
        self._log_conversation(npc_a, npc_b, "discuss", {
            "topic": topic,
            "exchanges": exchanges,
            "shared_knowledge_count": len(shared_knowledge)
        })

        return {
            "success": True,
            "exchanges": exchanges,
            "shared_knowledge": list(shared_knowledge),
            "trust_level": rel["trust"]
        }

    def tool_gossip_about_player(self, from_npc: str, to_npc: str,
                                  observation: str, sentiment: str) -> Dict[str, Any]:
        """
        NPC tells another NPC something about the player

        This is how player reputation spreads through the society
        """
        if from_npc not in self.npcs or to_npc not in self.npcs:
            return {"success": False}

        sender = self.npcs[from_npc]
        recipient = self.npcs[to_npc]

        # Create gossip info packet
        gossip_id = f"gossip_player_{self.current_turn}_{from_npc}_{to_npc}"
        gossip_packet = InfoPacket(
            info_id=gossip_id,
            content=f"[{from_npc}说] 关于那个少年: {observation}",
            source_npc=from_npc,
            shared_by=from_npc,
            reliability=0.7,  # Gossip is somewhat reliable
            privacy_level=PrivacyLevel.PRIVATE,
            timestamp=self.current_turn
        )

        recipient.known_info[gossip_id] = gossip_packet

        # Update recipient's perception of player
        if sentiment == "positive":
            recipient.trust_toward_player = min(1.0, recipient.trust_toward_player + 0.1)
        elif sentiment == "negative":
            recipient.trust_toward_player = max(0.0, recipient.trust_toward_player - 0.1)
            recipient.suspicion_toward_player = min(1.0, recipient.suspicion_toward_player + 0.15)

        self._log_conversation(from_npc, to_npc, "gossip_player", {
            "observation": observation,
            "sentiment": sentiment
        })

        return {"success": True, "gossip_id": gossip_id}

    # ============ Background Simulation ============

    async def run_background_simulation(self, num_interactions: int = 3) -> List[Dict[str, Any]]:
        """
        Run background simulation - NPCs talk to each other without player

        This happens "between" player turns
        """
        results = []
        npc_ids = list(self.npcs.keys())

        if len(npc_ids) < 2:
            return results

        for _ in range(num_interactions):
            # Pick two NPCs to interact
            npc_a, npc_b = random.sample(npc_ids, 2)

            # Determine what they talk about
            topics = ["recent_events", "player", "rumors", "personal"]
            topic = random.choice(topics)

            if topic == "player":
                # Gossip about player
                npc1 = self.npcs[npc_a]
                if npc1.trust_toward_player > 0.6:
                    sentiment = "positive"
                    obs = "那个孩子看起来是个好人"
                elif npc1.suspicion_toward_player > 0.4:
                    sentiment = "negative"
                    obs = "那个孩子问太多问题了"
                else:
                    sentiment = "neutral"
                    obs = "那个孩子还在山上转悠"

                result = self.tool_gossip_about_player(npc_a, npc_b, obs, sentiment)
                results.append({
                    "type": "gossip",
                    "from": npc_a,
                    "to": npc_b,
                    "result": result
                })
            else:
                # General discussion
                result = self.tool_discuss_with_npc(npc_a, npc_b, topic)
                results.append({
                    "type": "discuss",
                    "between": [npc_a, npc_b],
                    "result": result
                })

        self.current_turn += 1
        return results

    # ============ Player Interaction Effects ============

    def on_player_talk_to_npc(self, npc_id: str, content: str,
                               trust_change: float = 0, suspicion_change: float = 0):
        """
        Called when player talks to an NPC
        This may trigger the NPC to later share this interaction with others
        """
        if npc_id not in self.npcs:
            return

        npc = self.npcs[npc_id]
        npc.trust_toward_player = max(0.0, min(1.0, npc.trust_toward_player + trust_change))
        npc.suspicion_toward_player = max(0.0, min(1.0, npc.suspicion_toward_player + suspicion_change))

        # If trust is high, NPC might tell others about this conversation later
        if npc.trust_toward_player > 0.7:
            # Queue for later gossip
            npc.player_reputation["last_conversation"] = {
                "content": content[:50],
                "trust_change": trust_change,
                "timestamp": self.current_turn
            }

    def get_npc_perception_of_player(self, npc_id: str) -> Dict[str, Any]:
        """Get how an NPC currently views the player"""
        if npc_id not in self.npcs:
            return {}

        npc = self.npcs[npc_id]
        return {
            "trust": npc.trust_toward_player,
            "suspicion": npc.suspicion_toward_player,
            "willing_to_share": npc.trust_toward_player > 0.5,
            "might_gossip": npc.trust_toward_player > 0.7
        }

    # ============ Insight System Integration ============

    def get_overhearable_conversations(self, insight_level: str = "normal") -> List[Dict[str, Any]]:
        """
        Get conversations that player might overhear using insight

        Different insight levels reveal different types:
        - normal: Only PUBLIC conversations
        - deep: PRIVATE conversations between NPCs
        - secret: SECRET conversations
        """
        overhearable = []

        for log in self.conversation_log[-10:]:  # Last 10 conversations
            if log["type"] == "share_info":
                privacy = log.get("privacy", "private")
                if insight_level == "normal" and privacy == "public":
                    overhearable.append(log)
                elif insight_level == "deep" and privacy in ["public", "private"]:
                    overhearable.append(log)
                elif insight_level == "secret":
                    overhearable.append(log)
            elif log["type"] == "gossip_player" and insight_level in ["deep", "secret"]:
                overhearable.append(log)

        return overhearable

    def get_info_propagation_chain(self, info_id: str) -> List[str]:
        """
        Trace how an info packet has propagated through the society
        Returns: [original_source, intermediate_sharers..., current_holder]
        """
        chain = []
        for npc_id, npc in self.npcs.items():
            if info_id in npc.known_info:
                packet = npc.known_info[info_id]
                chain.append(f"{packet.source_npc} -> {packet.shared_by} -> {npc_id}")
        return chain

    # ============ Internal Methods ============

    def _log_conversation(self, npc_a: str, npc_b: str, conv_type: str,
                         details: Dict[str, Any]):
        """Log an NPC-NPC conversation"""
        self.conversation_log.append({
            "turn": self.current_turn,
            "participants": [npc_a, npc_b],
            "type": conv_type,
            "privacy": details.get("privacy", "private"),
            **details
        })

    def get_society_state(self) -> Dict[str, Any]:
        """Get full state of NPC society for debugging/saving"""
        return {
            "current_turn": self.current_turn,
            "npcs": {
                npc_id: {
                    "known_info_count": len(npc.known_info),
                    "trust_toward_player": npc.trust_toward_player,
                    "suspicion_toward_player": npc.suspicion_toward_player,
                    "relationships": npc.relationships
                }
                for npc_id, npc in self.npcs.items()
            },
            "conversation_log_count": len(self.conversation_log)
        }


# ============ Scene-specific Initializers ============

def initialize_scene_0_society() -> NPCSociety:
    """Initialize NPC society for Scene 0 (五指山)"""
    society = NPCSociety()

    # Register NPCs
    society.register_npc("grandmother_s0", "祖母")
    society.register_npc("traveler_s0", "行者")
    # 悟空不直接参与对话，但作为信息源存在
    society.register_npc("wukong_s0", "悟空", initial_info=["wukong_whisper"])

    # Set up initial information
    # 祖母知道一些民间故事
    society.add_info_to_npc("grandmother_s0", "story_nezha",
                           "听说过一个关于剔骨还子的故事，那孩子最后没有复活",
                           reliability=0.9, source="grandmother_s0")
    society.add_info_to_npc("grandmother_s0", "rumor_tianthe",
                           "天上有人在偷'灵蕴'，那是神仙的命根子",
                           reliability=0.8, source="grandmother_s0")
    society.add_info_to_npc("grandmother_s0", "peach_tree_legend",
                           "五指山上的桃树与齐天大圣有关",
                           reliability=0.7, source="common_knowledge")

    # 行者知道更多内幕
    society.add_info_to_npc("traveler_s0", "wukong_location",
                           "齐天大圣被压在这座山下",
                           reliability=0.95, source="traveler_s0")
    society.add_info_to_npc("traveler_s0", "traveler_identity",
                           "我其实是金蝉子转世，在找我的大徒弟",
                           reliability=1.0, source="traveler_s0")
    society.add_info_to_npc("traveler_s0", "peach_tree_legend",
                           "五指山上的桃树与齐天大圣有关",
                           reliability=0.7, source="common_knowledge")
    society.add_info_to_npc("traveler_s0", "heaven_secret",
                           "天庭害怕悟空东山再起，派了人监视",
                           reliability=0.85, source="traveler_s0")

    # 悟空知道的最少，但最关键
    society.add_info_to_npc("wukong_s0", "wukong_thoughts",
                           "我已经等了五百年，不知道还要等多久",
                           reliability=1.0, source="wukong_s0")

    # Set up relationships
    # 祖母和行者之间：陌生人，低信任
    society.set_relationship("grandmother_s0", "traveler_s0",
                            trust=0.3, suspicion=0.2)

    # 祖母对悟空：知道传说但不知道他在山下
    # 行者对悟空：知道他在山下

    return society
