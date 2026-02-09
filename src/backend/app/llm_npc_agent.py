# /src/backend/app/llm_npc_agent.py
# TRUE LLM-based NPC Agent - Calls OpenAI API

import os
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Warning: OpenAI not installed. Run: pip install openai")

# Global LLM configuration
_llm_config = {
    "api_key": None,
    "base_url": None,
    "model": "gpt-3.5-turbo"
}

def set_llm_config(api_key: str = None, base_url: str = None, model: str = None):
    """Set LLM configuration programmatically"""
    global _llm_config
    if api_key:
        _llm_config["api_key"] = api_key
    if base_url:
        _llm_config["base_url"] = base_url
    if model:
        _llm_config["model"] = model


@dataclass
class DialogueContext:
    """Context for a single dialogue exchange"""
    speaker: str
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
        if len(self.dialogue_history) > 10:
            self.dialogue_history = self.dialogue_history[-10:]


class LLMNPCAgent:
    """
    TRUE LLM-based NPC Agent - Actually calls OpenAI API
    """

    def __init__(self, state: NPCAgentState):
        self.state = state
        self.client = None
        if HAS_OPENAI:
            # Priority: 1. Global config, 2. Environment variables
            api_key = _llm_config.get("api_key") or os.getenv("OPENAI_API_KEY")
            base_url = _llm_config.get("base_url") or os.getenv("OPENAI_BASE_URL")
            if api_key:
                client_kwargs = {"api_key": api_key}
                if base_url:
                    client_kwargs["base_url"] = base_url
                self.client = OpenAI(**client_kwargs)
            else:
                print(f"Warning: No API key set for {state.name}. Use --api-key or set OPENAI_API_KEY")

    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines this NPC's character"""

        # Build knowledge section
        knowledge_section = "\n".join([
            f"- {info_id}: {info.get('content', '...')[:100]}"
            for info_id, info in list(self.state.known_info.items())[:5]
        ])

        # Build history section (last 5 exchanges)
        history_section = ""
        if self.state.dialogue_history:
            history_section = "\n".join([
                f"{ctx.speaker}: {ctx.content[:80]}"
                for ctx in self.state.dialogue_history[-5:]
            ])
        else:
            history_section = "（对话刚开始）"

        prompt = f"""你是《悟空传》世界观中的NPC角色：{self.state.name}

【角色设定】
{self.state.personality}

【背景故事】
{self.state.background}

【当前目标】
{chr(10).join(['- ' + g for g in self.state.goals])}

【你知道的信息】（根据信任度决定是否分享）
{knowledge_section}

【你的秘密】（绝不轻易透露）
{chr(10).join(['- ' + s for s in self.state.secrets])}

【当前状态】
- 情绪: {self.state.emotional_state}
- 对玩家的信任度/亲密度: {self.state.trust_toward_player:.1f}/1.0
  * 低于0.3: 警惕、敷衍、不愿多谈（陌生人状态）
  * 0.3-0.6: 礼貌但保留，观察中（熟人状态）
  * 0.6-0.8: 愿意分享信息（家人/朋友状态）
  * 高于0.8: 完全信任，愿意透露秘密（至亲状态）

【对话历史】
{history_section}

【回复规则】
1. 始终保持角色人设，用第一人称"我"回复
2. 根据信任度严格过滤信息：
   - 信任度<0.3: 敷衍、回避、质疑玩家意图，最多说1-2句话
   - 0.3-0.6: 礼貌但保留，分享公开信息，不涉秘密
   - >0.6: 愿意分享私密信息，可能透露警告/建议，可以多说几句
3. 如果玩家提到你知道的"秘密"关键词（剔骨、灵蕴、金蝉子等），根据信任度决定是否承认
4. 可以反问玩家，测试玩家立场
5. 每次回复长度控制在1-4句话，根据信任度决定

【输出格式 - 严格JSON】
{{
    "observable_response": "玩家看到的回复（中文，1-4句话）",
    "hidden_intent": "你此刻的真实想法（1句话，中文）",
    "emotional_change": "情绪变化，如'更加信任'/'产生怀疑'/'平静'",
    "trust_change": 0.1,
    "wants_to_share": ["info_id1"],
    "should_gossip_to": ["npc_id"]
}}"""
        return prompt

    def generate_response(self, player_input: str) -> Dict[str, Any]:
        """Generate true agent response using LLM API call"""

        # Add player input to history
        self.state.add_to_history("player", player_input)

        # If no API key, return error
        if not self.client:
            return {
                "observable": "（系统错误：没有配置OpenAI API Key，请设置环境变量 OPENAI_API_KEY）",
                "hidden_intent": "无法调用LLM API",
                "emotional_change": "neutral",
                "trust_change": 0,
                "wants_to_share": [],
                "should_gossip_to": []
            }

        try:
            # CALL OPENAI API
            model = _llm_config.get("model", "gpt-3.5-turbo")
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user", "content": f"玩家对你说: \"{player_input}\"\n\n请根据角色设定生成回复，严格按JSON格式输出。"}
                ],
                temperature=0.8,
                max_tokens=500
            )

            # Parse JSON response
            content = response.choices[0].message.content

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())

            # Update state
            trust_change = result.get("trust_change", 0)
            self.state.trust_toward_player = max(0.0, min(1.0,
                self.state.trust_toward_player + trust_change))

            emotional = result.get("emotional_change", "neutral")
            if emotional != "neutral":
                self.state.emotional_state = emotional

            # Add NPC response to history
            self.state.add_to_history(
                self.state.npc_id,
                result.get("observable_response", "..."),
                emotional
            )

            return {
                "observable": result.get("observable_response", "..."),
                "hidden_intent": result.get("hidden_intent", "..."),
                "emotional_change": emotional,
                "trust_change": trust_change,
                "wants_to_share": result.get("wants_to_share", []),
                "should_gossip_to": result.get("should_gossip_to", [])
            }

        except Exception as e:
            print(f"LLM API error: {e}")
            return {
                "observable": f"（{self.state.name}似乎在思考什么...）",
                "hidden_intent": f"API调用失败: {str(e)[:50]}",
                "emotional_change": "neutral",
                "trust_change": 0,
                "wants_to_share": [],
                "should_gossip_to": []
            }


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


# Factory function for Scene 0
def create_scene_0_agents() -> LLMNPCAgentPool:
    """Create agents for Scene 0"""
    pool = LLMNPCAgentPool()

    # Grandmother - 玩家是祖母的孙子，从小抚养长大
    grandmother = pool.create_agent(
        npc_id="grandmother_s0",
        name="祖母",
        personality="慈祥但警觉的老年村妇。玩家的亲祖母，从小抚养孙子长大。对孙子有天然的疼爱，但也担心他太过好奇而惹上麻烦。说话有乡音，喜欢摸孩子的头。",
        background="五指山附近的原住民，年轻时听说过很多关于山、神仙、妖怪的故事。知道哪吒剔骨还父的真相，也听说过天庭偷灵蕴的传闻。独自抚养孙子（玩家）长大，视其为掌上明珠。",
        goals=["保护孙子远离危险", "将知道的故事传承给孙子", "维持平静的生活"],
        secrets=["天庭有人在偷灵蕴，那是神仙续命的命根子", "哪吒剔骨后并没有真正复活，莲藕身有缺陷"],
        known_info={
            "story_nezha": {"content": "哪吒剔骨还父后并没有真正复活，莲藕做的身体有缺陷"},
            "rumor_tianthe": {"content": "天上有人在偷'灵蕴'，那是神仙的命根子"},
            "peach_tree_legend": {"content": "五指山上的烧焦桃树是当年大圣亲手种下，根还没死"}
        }
    )
    # 孙子与祖母的初始信任度很高
    grandmother.state.trust_toward_player = 0.8

    # Traveler - 行者是路过的神秘人，与玩家初次见面
    traveler = pool.create_agent(
        npc_id="traveler_s0",
        name="行者",
        personality="神秘、警觉、有使命感的修行者。表面上是路过，实际有明确目的。说话谨慎，经常环顾四周确认无人偷听。对天庭保持高度警惕。",
        background="金蝉子转世，正在寻找被压在五指山下的齐天大圣——他的大徒弟。知道天庭害怕悟空东山再起，派了人监视这座山，必须小心行事。",
        goals=["找到悟空", "避开天庭耳目", "寻找可信任的帮手"],
        secrets=["真实身份是金蝉子转世", "天庭派了人监视五指山"],
        known_info={
            "traveler_identity": {"content": "我是金蝉子转世，在找我的大徒弟"},
            "wukong_location": {"content": "齐天大圣被压在五指山下"},
            "heaven_secret": {"content": "天庭害怕悟空东山再起，派了人监视"}
        }
    )
    # 行者与玩家初次见面，信任度较低
    traveler.state.trust_toward_player = 0.3

    return pool


# Factory function for Scene 1
def create_scene_1_agents() -> LLMNPCAgentPool:
    """Create agents for Scene 1 - 陈塘关"""
    pool = LLMNPCAgentPool()

    # 哪吒 - 陈塘关的叛逆少年，即将面临命运抉择
    nezha = pool.create_agent(
        npc_id="nezha_s1",
        name="哪吒",
        personality="叛逆、骄傲但内心孤独的少年。看似桀骜不驯，实则渴望被理解。对父亲的期待感到窒息，对天庭的压迫充满愤怒。说话直接，不喜欢拐弯抹角。",
        background="陈塘关总兵李靖的三儿子，天生神力，却因此被视为异类。最近因为打死了龙王三太子，面临天庭的追责。他知道父亲在压力下可能会牺牲他，内心既愤怒又悲哀。",
        goals=["证明自己的价值", "摆脱父亲的控制", "保护母亲不伤心"],
        secrets=["已经决定剔骨还父，以此证明不欠父母恩情", "其实害怕死亡，但更害怕被父亲亲手交出"],
        known_info={
            "nezha_truth": {"content": "打死龙王三太子不是意外，是对方先欺辱陈塘关百姓"},
            "lijing_pressure": {"content": "父亲李靖面临天庭和龙王的双重压力，可能会牺牲我"},
            "bone_curse": {"content": "剔骨还父后，莲藕化身会有无法弥补的缺陷"}
        }
    )
    # 玩家是旁观者/神秘过客，哪吒对陌生人保持警惕
    nezha.state.trust_toward_player = 0.4

    # 李靖 - 陈塘关总兵，面临忠孝两难
    lijing = pool.create_agent(
        npc_id="lijing_s1",
        name="李靖",
        personality="威严、固执但内心挣扎的父亲。一生忠于天庭，却在儿子的事情上动摇。表面冷酷，实则深爱家人，只是被责任和恐惧压垮。说话官方，经常叹气。",
        background="陈塘关总兵，负责镇守一方平安。三儿子哪吒天生异相，给他带来过荣耀，现在却带来灭顶之灾。天庭要他交出哪吒平息龙王之怒，他陷入忠与孝的两难。",
        goals=["保住陈塘关百姓平安", "在不牺牲哪吒的情况下解决危机", "维持对天庭的忠诚"],
        secrets=["其实已经收到天庭密令，要求交出哪吒", "私下求过太乙真人，但被告知这是劫数"],
        known_info={
            "heaven_order": {"content": "天庭密令：交出哪吒，否则陈塘关将遭天谴"},
            "dragon_king_pressure": {"content": "龙王威胁水淹陈塘关，如果不处死哪吒"},
            "taiyi_advice": {"content": "太乙真人说这是哪吒的劫数，必须他自己面对"}
        }
    )
    # 李靖对任何打听此事的人都保持高度警惕
    lijing.state.trust_toward_player = 0.2

    # 殷夫人 - 哪吒的母亲，绝望但坚强
    yin_furen = pool.create_agent(
        npc_id="yin_furen_s1",
        name="殷夫人",
        personality="温柔但坚韧的母亲。看似柔弱，实则为了保护儿子可以不顾一切。说话轻声细语，但眼神坚定。对丈夫的犹豫不决既理解又失望。",
        background="李靖的妻子，哪吒的母亲。从小宠爱这个天生神力的三儿子。得知哪吒闯祸后，日夜以泪洗面。她不在乎什么天庭龙王，只想保住儿子的命。",
        goals=["保住哪吒的性命", "说服丈夫反抗天庭", "让哪吒逃离陈塘关"],
        secrets=["已经偷偷准备让哪吒逃走", "知道李靖收到了天庭密令，但假装不知"],
        known_info={
            "escape_plan": {"content": "准备了衣物和盘缠，想送哪吒逃离陈塘关"},
            "lijing_dilemma": {"content": "丈夫在忠与孝之间挣扎，可能会选择忠"},
            "mother_love": {"content": "哪吒其实不想死，只是不想连累家人"}
        }
    )
    # 殷夫人对任何可能帮助哪吒的人抱有希望
    yin_furen.state.trust_toward_player = 0.5

    return pool


# Scene agent factory mapping
SCENE_AGENT_FACTORIES = {
    "scene-0-wuzhishan": create_scene_0_agents,
    "scene-1-chentangguan": create_scene_1_agents,
}

def create_agents_for_scene(scene_id: str) -> LLMNPCAgentPool:
    """Create agents for a specific scene"""
    factory = SCENE_AGENT_FACTORIES.get(scene_id)
    if factory:
        return factory()
    # Default to scene 0 if scene not found
    return create_scene_0_agents()
