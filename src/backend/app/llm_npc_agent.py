# /src/backend/app/llm_npc_agent.py
# True LLM-based NPC Agent - Understands and generates responses

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Try to import OpenAI, but don't fail if not available
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class DialogueContext:
    """Context for a single dialogue exchange"""
    speaker: str  # 'player' or npc_id
    content: str
    timestamp: datetime
    emotional_tone: str = "neutral"


@dataclass
class NPCAgentState:
    """Full state of an NPC agent"""
    npc_id: str
    name: str
    personality: str
    background: str
    goals: List[str]
    secrets: List[str]
    known_info: Dict[str, Any]

    # Dynamic state
    trust_toward_player: float = 0.5
    emotional_state: str = "calm"
    dialogue_history: List[DialogueContext] = field(default_factory=list)

    def add_to_history(self, speaker: str, content: str, tone: str = "neutral"):
        """Add dialogue to history, keeping last 10 exchanges"""
        self.dialogue_history.append(DialogueContext(
            speaker=speaker,
            content=content,
            timestamp=datetime.now(),
            emotional_tone=tone
        ))
        # Keep only last 10
        if len(self.dialogue_history) > 10:
            self.dialogue_history = self.dialogue_history[-10:]


class LLMNPCAgent:
    """
    True LLM-based NPC Agent

    Key features:
    1. Understands player input using LLM
    2. Generates contextual responses based on:
       - NPC personality and background
       - Current emotional state
       - Trust level toward player
       - Conversation history
       - Information they possess
    3. Tracks hidden intent (what they really think vs what they say)
    """

    def __init__(self, state: NPCAgentState):
        self.state = state
        self.client = None
        if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
            self.client = OpenAI()

    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines this NPC's character"""

        # Build knowledge section
        knowledge_section = "\n".join([
            f"- {info_id}: {info.get('content', '...')[:100]}"
            for info_id, info in list(self.state.known_info.items())[:5]
        ])

        # Build history section
        history_section = "\n".join([
            f"{ctx.speaker}: {ctx.content[:50]}..."
            for ctx in self.state.dialogue_history[-5:]
        ])

        prompt = f"""你是《悟空传》世界观中的NPC角色：{self.state.name}

【角色设定】
{self.state.personality}

【背景故事】
{self.state.background}

【当前目标】
{', '.join(self.state.goals)}

【你知道的信息】
{knowledge_section}

【当前状态】
- 情绪: {self.state.emotional_state}
- 对玩家的信任度: {self.state.trust_toward_player:.1f}/1.0
  (低于0.3: 警惕, 0.3-0.7: 观察, 高于0.7: 信任)

【对话历史（最近5轮）】
{history_section}

【回复规则】
1. 始终保持角色人设，用第一人称回复
2. 根据信任度决定透露多少信息：
   - 信任度低: 敷衍、回避、质疑玩家意图
   - 信任度中: 礼貌但保留，分享公开信息
   - 信任度高: 愿意分享私密信息，给出警告/建议
3. 回复长度控制在2-4句话
4. 可以反问玩家，测试玩家立场
5. 如果玩家的问题涉及你知道的"秘密"，根据信任度决定是否透露

【输出格式】
请用JSON格式输出：
{{
    "observable_response": "玩家看到的回复（2-4句话）",
    "hidden_intent": "你此刻的真实想法（1句话）",
    "emotional_change": "情绪变化，如'更加信任'/'产生怀疑'/"平静"",
    "trust_change": 0.1,  // 建议的信任度变化，范围-0.2到+0.1
    "wants_to_share": ["info_id1", "info_id2"],  // 想分享给玩家的信息ID
    "gossip_targets": ["npc_id"]  // 想向谁gossip这次对话
}}"""
        return prompt

    def _build_user_prompt(self, player_input: str) -> str:
        """Build the user prompt with current context"""
        return f"玩家对你说: \"{player_input}\"\n\n请根据角色设定和当前状态生成回复。"

    def generate_response(self, player_input: str) -> Dict[str, Any]:
        """
        Generate true agent response using LLM

        Returns:
            {
                "observable": str,  # What player sees
                "hidden_intent": str,  # What NPC really thinks
                "emotional_change": str,
                "trust_change": float,
                "wants_to_share": List[str],
                "gossip_targets": List[str]
            }
        """
        # Add player input to history
        self.state.add_to_history("player", player_input)

        # If no LLM available, fall back to smart template
        if not self.client:
            return self._generate_smart_fallback(player_input)

        try:
            # Call LLM
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": self._build_user_prompt(player_input)}
                ],
                temperature=0.7,
                max_tokens=500
            )

            # Parse JSON response
            content = response.choices[0].message.content
            # Extract JSON if wrapped in markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())

            # Update state based on response
            self._update_state_from_response(result)

            # Add NPC response to history
            self.state.add_to_history(
                self.state.npc_id,
                result.get("observable_response", "..."),
                result.get("emotional_change", "neutral")
            )

            return {
                "observable": result.get("observable_response", "..."),
                "hidden_intent": result.get("hidden_intent", "..."),
                "emotional_change": result.get("emotional_change", "neutral"),
                "trust_change": result.get("trust_change", 0),
                "wants_to_share": result.get("wants_to_share", []),
                "gossip_targets": result.get("gossip_targets", [])
            }

        except Exception as e:
            print(f"LLM error: {e}, falling back to template")
            return self._generate_smart_fallback(player_input)

    def _generate_smart_fallback(self, player_input: str) -> Dict[str, Any]:
        """
        Smart template fallback when LLM unavailable

        Analyzes player input keywords and generates contextual response
        """
        # Simple keyword analysis
        keywords = {
            "故事": ["story", "legend", "tale"],
            "悟空": ["wukong", "monkey", "大圣"],
            "山": ["mountain", "hill", "cave"],
            "谁": ["who", "identity", "name"],
            "为什么": ["why", "reason", "purpose"],
            "天庭": ["heaven", "god", "immortal"],
            "桃子": ["peach", "tree", "fruit"],
        }

        # Detect what player is asking about
        matched_topics = []
        player_lower = player_input.lower()

        for chinese, english_keywords in keywords.items():
            if chinese in player_input or any(kw in player_lower for kw in english_keywords):
                matched_topics.append(chinese)

        # Generate contextual response based on trust and topics
        trust = self.state.trust_toward_player

        if self.state.npc_id == "grandmother_s0":
            response = self._generate_grandmother_response(player_input, trust, matched_topics)
        elif self.state.npc_id == "traveler_s0":
            response = self._generate_traveler_response(player_input, trust, matched_topics)
        else:
            response = self._generate_generic_response(trust)

        # Update state
        self.state.add_to_history(self.state.npc_id, response["observable"])

        return response

    def _generate_grandmother_response(self, player_input: str, trust: float, topics: List[str]) -> Dict[str, Any]:
        """Generate grandmother's contextual response"""

        # Check if asking about known stories
        if "故事" in topics or "legend" in topics:
            if trust > 0.6:
                return {
                    "observable": "你问起了故事...这让我想起了那个关于剔骨还子的传说。那孩子最后并没有复活，莲藕做的身体，还是原来的那个人吗？",
                    "hidden_intent": "这孩子值得信任，我可以分享一些民间秘闻",
                    "emotional_change": "陷入回忆",
                    "trust_change": 0.05,
                    "wants_to_share": ["story_nezha"],
                    "gossip_targets": []
                }
            elif trust > 0.3:
                return {
                    "observable": "山上的故事？多着呢。但那都是过去的事了，知道太多对你没好处。",
                    "hidden_intent": "还在观察这个孩子，不能轻易透露",
                    "emotional_change": "警惕",
                    "trust_change": 0.0,
                    "wants_to_share": [],
                    "gossip_targets": []
                }
            else:
                return {
                    "observable": "你问这些做什么？专心砍你的柴去，别打听不该知道的事。",
                    "hidden_intent": "这孩子太好奇了，得防着点",
                    "emotional_change": "警惕",
                    "trust_change": -0.05,
                    "wants_to_share": [],
                    "gossip_targets": ["traveler_s0"]
                }

        # Asking about the mountain
        if "山" in topics or "mountain" in topics:
            if trust > 0.5:
                return {
                    "observable": "这五指山...传说压着一位齐天大圣。不过那是老人们说的，谁知道真假呢。",
                    "hidden_intent": "可以分享一些公开传说",
                    "emotional_change": "平静",
                    "trust_change": 0.02,
                    "wants_to_share": ["peach_tree_legend"],
                    "gossip_targets": []
                }
            else:
                return {
                    "observable": "山就是山，有什么好问的。",
                    "hidden_intent": "不想多说",
                    "emotional_change": "冷淡",
                    "trust_change": 0.0,
                    "wants_to_share": [],
                    "gossip_targets": []
                }

        # Asking about sky/heaven (suspicious!)
        if "天庭" in topics or "heaven" in topics:
            if trust > 0.8:
                return {
                    "observable": "你...你怎么问起这个？（压低声音）我听说天上有人在偷'灵蕴'，那是神仙的命根子。这事知道的人不多，你可别乱说。",
                    "hidden_intent": "这孩子连这都知道？看来不是普通人，可以深谈",
                    "emotional_change": "震惊后谨慎",
                    "trust_change": 0.1,
                    "wants_to_share": ["rumor_tianthe"],
                    "gossip_targets": []
                }
            else:
                return {
                    "observable": "天庭？那是我们凡人该议论的吗？快走快走，别给我惹麻烦。",
                    "hidden_intent": "这孩子太危险了，得让行者知道",
                    "emotional_change": "恐惧",
                    "trust_change": -0.1,
                    "wants_to_share": [],
                    "gossip_targets": ["traveler_s0"]
                }

        # Generic response
        if trust > 0.6:
            return {
                "observable": f"你问'{player_input[:20]}'...（慈祥地笑）你这孩子，问题真多。来，到奶奶这边坐。",
                "hidden_intent": "喜欢这个孩子，愿意多聊聊",
                "emotional_change": "慈祥",
                "trust_change": 0.03,
                "wants_to_share": [],
                "gossip_targets": []
            }
        elif trust > 0.3:
            return {
                "observable": "嗯...（看了你一眼）你问这个做什么？",
                "hidden_intent": "还在观察",
                "emotional_change": "观察",
                "trust_change": 0.0,
                "wants_to_share": [],
                "gossip_targets": []
            }
        else:
            return {
                "observable": "（皱眉）我很忙，没空闲聊。",
                "hidden_intent": "不想理这个孩子",
                "emotional_change": "冷淡",
                "trust_change": -0.02,
                "wants_to_share": [],
                "gossip_targets": []
            }

    def _generate_traveler_response(self, player_input: str, trust: float, topics: List[str]) -> Dict[str, Any]:
        """Generate traveler's contextual response"""

        # Asking about identity
        if "谁" in topics or "identity" in topics or "name" in topics:
            if trust > 0.7:
                return {
                    "observable": "（环顾四周，确认无人后）实不相瞒，我在找一个人。他曾经是齐天大圣，现在被压在这座山下。我是他的师父——金蝉子。",
                    "hidden_intent": "这孩子值得信任，可以透露真实身份",
                    "emotional_change": "谨慎但坦诚",
                    "trust_change": 0.05,
                    "wants_to_share": ["traveler_identity", "wukong_location"],
                    "gossip_targets": []
                }
            elif trust > 0.4:
                return {
                    "observable": "我？只是一个路过的旅人，在这座山寻找...一些答案。",
                    "hidden_intent": "还不能完全信任",
                    "emotional_change": "保留",
                    "trust_change": 0.0,
                    "wants_to_share": [],
                    "gossip_targets": []
                }
            else:
                return {
                    "observable": "（警惕地）我是谁与你何干？倒是你，为何打探我的事？",
                    "hidden_intent": "这孩子可疑，需要防备",
                    "emotional_change": "警惕",
                    "trust_change": -0.05,
                    "wants_to_share": [],
                    "gossip_targets": []
                }

        # Asking about monkey/king
        if "悟空" in topics or "monkey" in topics or "wukong" in topics:
            if trust > 0.6:
                return {
                    "observable": "你...你知道他在山下？（压低声音）天庭派了人监视这座山，怕的是他东山再起。我得小心行事。",
                    "hidden_intent": "这孩子知道内情，可以合作",
                    "emotional_change": "谨慎兴奋",
                    "trust_change": 0.08,
                    "wants_to_share": ["heaven_secret"],
                    "gossip_targets": []
                }
            else:
                return {
                    "observable": "齐天大圣？那只是传说罢了。",
                    "hidden_intent": "不能暴露知道太多",
                    "emotional_change": "伪装",
                    "trust_change": 0.0,
                    "wants_to_share": [],
                    "gossip_targets": []
                }

        # Generic
        if trust > 0.6:
            return {
                "observable": f"（若有所思）'{player_input[:20]}'...你这孩子，知道的比看上去多。",
                "hidden_intent": "这个孩子不简单，值得培养",
                "emotional_change": "感兴趣",
                "trust_change": 0.03,
                "wants_to_share": [],
                "gossip_targets": []
            }
        else:
            return {
                "observable": "（看了你一眼，没有回答）",
                "hidden_intent": "还在观察这个孩子",
                "emotional_change": "观察",
                "trust_change": 0.0,
                "wants_to_share": [],
                "gossip_targets": []
            }

    def _generate_generic_response(self, trust: float) -> Dict[str, Any]:
        """Generic fallback response"""
        return {
            "observable": "...（沉默）" if trust < 0.3 else "嗯...（点点头）",
            "hidden_intent": "观察中",
            "emotional_change": "neutral",
            "trust_change": 0.0,
            "wants_to_share": [],
            "gossip_targets": []
        }

    def _update_state_from_response(self, result: Dict[str, Any]):
        """Update NPC state based on generated response"""
        # Update trust
        trust_change = result.get("trust_change", 0)
        self.state.trust_toward_player = max(0, min(1,
            self.state.trust_toward_player + trust_change))

        # Update emotional state
        emotional_change = result.get("emotional_change", "")
        if emotional_change and emotional_change != "neutral":
            self.state.emotional_state = emotional_change


class LLMNPCAgentPool:
    """Pool of LLM NPC agents"""

    def __init__(self):
        self.agents: Dict[str, LLMNPCAgent] = {}

    def create_agent(self, npc_id: str, name: str, personality: str,
                    background: str, goals: List[str], secrets: List[str],
                    known_info: Dict[str, Any]) -> LLMNPCAgent:
        """Create a new NPC agent"""
        state = NPCAgentState(
            npc_id=npc_id,
            name=name,
            personality=personality,
            background=background,
            goals=goals,
            secrets=secrets,
            known_info=known_info
        )
        agent = LLMNPCAgent(state)
        self.agents[npc_id] = agent
        return agent

    def get_agent(self, npc_id: str) -> Optional[LLMNPCAgent]:
        """Get agent by ID"""
        return self.agents.get(npc_id)

    def process_dialogue(self, npc_id: str, player_input: str) -> Dict[str, Any]:
        """Process dialogue with specific NPC"""
        agent = self.agents.get(npc_id)
        if not agent:
            return {"error": f"NPC {npc_id} not found"}

        return agent.generate_response(player_input)


# Factory functions for Scene 0 NPCs
def create_scene_0_agents() -> LLMNPCAgentPool:
    """Create agents for Scene 0"""
    pool = LLMNPCAgentPool()

    # Grandmother
    pool.create_agent(
        npc_id="grandmother_s0",
        name="祖母",
        personality="慈祥但警觉的老年村妇。经历过太多世事，知道民间传说和不为人知的秘密。对陌生人保持戒心，但对信任的人会分享 wisdom。",
        background="五指山附近的原住民，年轻时听说过很多关于山、神仙、妖怪的故事。知道一些天庭的秘密传闻，但从不轻易透露。独自抚养孙子（玩家）长大。",
        goals=["保护孙子远离危险", "维持平静的生活", "将知道的故事传承下去"],
        secrets=["知道天庭有人在偷灵蕴", "听说过哪吒剔骨还父的真相"],
        known_info={
            "story_nezha": {"content": "哪吒剔骨还父后并没有真正复活，莲藕身有缺陷"},
            "rumor_tianthe": {"content": "天上有人在偷灵蕴，那是神仙的命根子"},
            "peach_tree_legend": {"content": "五指山上的桃树与齐天大圣有关"}
        }
    )

    # Traveler
    pool.create_agent(
        npc_id="traveler_s0",
        name="行者",
        personality="神秘、警觉、有使命感的修行者。表面上是路过，实际有明确目的。对天庭保持高度警惕，在寻找值得信任的帮手。",
        background="金蝉子转世，正在寻找被压在五指山下的齐天大圣——他的大徒弟。知道天庭的阴谋，必须小心行事避免被发现。",
        goals=["找到悟空", "避开天庭耳目", "寻找可信任的帮手"],
        secrets=["真实身份是金蝉子", "天庭派了人监视五指山"],
        known_info={
            "traveler_identity": {"content": "我是金蝉子转世"},
            "wukong_location": {"content": "齐天大圣被压在五指山下"},
            "heaven_secret": {"content": "天庭害怕悟空东山再起，派了人监视"}
        }
    )

    return pool
