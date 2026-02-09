# 洞察力系统技术规格

> 本文档定义《Jump Jump》洞察力系统的完整技术规格，包括触发点、消耗机制和展示方式。
> 基于设计文档：`agent-arch-round3.md` 及相关场景设计

---

## 1. 系统概述

### 1.1 核心机制

洞察力系统已简化（无D20，无修正值）：
- **每场景固定配额**：2×「真实目的」+ 2×「幕后对话」
- **消耗方式**：每条 user query 前可选择是否使用
- **未使用洞察**：场景结束时获得完整场景回顾
- **已使用洞察**：仅游戏结束时获得完整回顾

### 1.2 洞察类型

| 类型 | 消耗 | 揭示内容 |
|------|------|----------|
| **真实目的** | 1点 | NPC在此刻的真实目的、隐藏动机 |
| **幕后对话** | 1点 | 隐藏对话层、DFS链的隐藏层 |

---

## 2. 洞察力触发点完整列表

### 2.1 Scene 0 - 五指山·尘埃

| 位置 | 类型 | 消耗 | 揭示内容 |
|------|------|------|----------|
| S0_Decision_A (石壁字迹) | decision_pre | 1真实目的 | 这些字迹与悟空的直接关联，以及它们在风化的过程中仍在"抵抗" |
| S0_wukong_presence_p2 | exploration_pre | 1真实目的 | 五指山的佛法封印不仅压住了悟空的身体，也在缓慢侵蚀他的记忆 |
| S0_wukong_presence_p3 | exploration_mid | 1幕后对话 | 少年不知道山下有人，悟空不知道山上有人。两个不知道彼此存在的生命，隔着一座山呼吸 |
| S0_grandmother_stories | dialogue_pre | 1真实目的 | 祖母的每个故事都精确对应一个场景，但叙述方式像一个记忆模糊的老人 |
| S0_grandmother_story_select | dialogue_mid | 1幕后对话 | 通关后重新审视，每一句都精确对应某个场景的关键时刻 |
| S0_traveler_encounter | dialogue_pre | 1真实目的 | 行者的脸上有一种少年看不懂的表情——"知道前面没有路还要走" |
| S0_traveler_encounter | dialogue_mid | 1幕后对话 | 这是唐僧，取经出发前。他的存在暗示——有人正在朝这座山走来 |
| S0_Decision_C (最后的行为) | decision_pre | 1真实目的 | 这个选择将在"重新渲染"中与Scene 1-4的变量产生共鸣 |

### 2.2 Scene 1 - 陈塘关·骨与莲

| 位置 | 类型 | 消耗 | 揭示内容 |
|------|------|------|----------|
| S1_Decision_A | decision_pre | 1真实目的 | 三个方向各有优劣：找哪吒建立信任，找李靖影响犹豫度，找百姓获取信息 |
| S1_nezha_p1_opening | dialogue_pre | 1真实目的 | 哪吒问"打得过龙吗"的真正意思是："我做了那件事之后，还有人站在我这边吗？" |
| S1_nezha_A1_opening | dialogue_pre | 1真实目的 | 哪吒内心其实渴望被阻止。他的愤怒是恐惧的盔甲 |
| S1_nezha_A1_opening | dialogue_mid | 1幕后对话 | 哪吒在间接告诉你他在乎你的教导 |
| S1_lijing_A2_opening | dialogue_pre | 1真实目的 | 李靖聘武师不只是教武，也是监视。武师是他的眼睛，只是武师自己不知道 |
| S1_lijing_p3_denial | dialogue_mid | 1幕后对话 | 李靖的痛苦不在于选择本身，而在于这个选择太容易算了 |
| S1_Decision_B | decision_pre | 1真实目的 | 哪吒在最后时刻确认"有一个人在看着我"——这是他需要的全部 |
| S1_Decision_C | decision_pre | 1真实目的 | 这个护腕将成为跨场景的物理联结 |
| S1_yangjian_encounter | dialogue_pre | 1真实目的 | 杨戬在寻找"有心窍的人"。他的出现意味着玩家在本场景中表现出了足够的洞察力和情感共鸣 |
| S1_yangjian_encounter | dialogue_mid | 1幕后对话 | 杨戬自己也是"有心窍的人"。他说这话时，想起了自己曾经的某个选择 |

### 2.3 Scene 2 - 天河·坠落之前

| 位置 | 类型 | 消耗 | 揭示内容 |
|------|------|------|----------|
| S2_Decision_A | decision_pre | 1真实目的 | 宣明看到陆执进来时表情一闪而过的紧张——他已经知道账目有问题 |
| S2_xuanming_report | dialogue_pre | 1真实目的 | 宣明的第一反应不是"查清真相"，而是"这会不会影响我的部门考核" |
| S2_xuanming_warns | dialogue_mid | 1幕后对话 | 宣明知道这些数字是什么，他一直在假装不知道 |
| S2_juanlian_questioning | dialogue_pre | 1真实目的 | 卷帘大将的被动洞察修正值为+5，他永远在观察 |
| S2_juanlian_aftermath | dialogue_mid | 1幕后对话 | 卷帘大将知道天蓬和阿月的事很久了。他的"延迟上报"是他职业生涯唯一一次偏离标准流程 |
| S2_tianpeng_fall | dialogue_mid | 1真实目的 | 天蓬知道天庭和灵山之间有灵蕴交易。他不在乎，因为他只在乎阿月 |
| S2_tianpeng_final_words | dialogue_mid | 1幕后对话 | 天蓬故意让人发现他和阿月的关系。他受够了偷偷摸摸 |
| S2_Decision_B | dialogue_pre | 1真实目的 | 卷帘大将的每个问题都是陷阱，无论怎么回答都有风险 |
| S2_Decision_C | decision_pre | 1真实目的 | 这片碎甲将成为跨场景的物理联结，影响后续选择 |
| S2_Decision_D | decision_pre | 1真实目的 | 这个选择将决定陆执在体制中的生存方式，以及第七窍的觉醒程度 |

### 2.4 Scene 3 - 花果山·最后的桃

| 位置 | 类型 | 消耗 | 揭示内容 |
|------|------|------|----------|
| S3_Decision_A | decision_pre | 1真实目的 | 老猴选择"散"不是因为不在乎大王，而是因为他知道记忆的代价 |
| S3_laohou_meeting_argue | dialogue_pre | 1真实目的 | 老猴选择"忘记"不是因为不在乎悟空，而是因为他知道记忆的代价——记得齐天大圣的猴子不会老老实实活着 |
| S3_laohou_memory_debate | dialogue_mid | 1幕后对话 | 老猴曾经劝过悟空不要去天宫。他的愧疚不是没劝住，而是——悟空说得对，他确实怕 |
| S3_tietou_meeting_argue | dialogue_pre | 1真实目的 | 铁头怕死。非常怕。每次天兵巡逻经过，他的手都在发抖 |
| S3_tietou_meeting_argue | dialogue_mid | 1幕后对话 | 铁头是悟空精神的"失真复制品"。他学到了悟空的不屈，但没学到悟空的智慧 |
| S3_zixia_encounter | dialogue_pre | 1真实目的 | 紫霞不知道悟空被压在五指山下。她只知道悟空不见了 |
| S3_zixia_thanks | dialogue_mid | 1幕后对话 | 紫霞的存在不改变任何局势，但改变一个东西——石卵会知道，有人在找大王 |
| S3_tianbing_patrol | dialogue_pre | 1真实目的 | 天兵队长的小儿子也是属猴的。他有时候看着山上那些幼猴会想起自己的孩子 |
| S3_tianbing_patrol | dialogue_mid | 1幕后对话 | 天兵队长是"平庸之恶"的化身。他不坏，但他的"不坏"救不了任何人 |
| S3_Decision_B | decision_pre | 1真实目的 | 如果玩家自己想到移植到五指山，这是P6原则的极致体现 |
| S3_Decision_D | decision_pre | 1真实目的 | 去找大王是最危险的选择，但如果带着桃树去，这是P6原则的极致体现 |

### 2.5 Scene 4 - 灵台·空经

| 位置 | 类型 | 消耗 | 揭示内容 |
|------|------|------|----------|
| S4_Decision_A | decision_pre | 1真实目的 | 拥有物证会在后续对峙中提供优势，但也带来风险 |
| S4_huikong_discovery | dialogue_pre | 1真实目的 | 慧空十五年前就发现了无字真经。他选择继续抄，当作什么都没发生 |
| S4_huikong_core_line | dialogue_mid | 1幕后对话 | 慧空羡慕法明的震惊，因为震惊意味着还有信仰可以被动摇 |
| S4_jianyuan_confrontation | dialogue_pre | 1真实目的 | 监院知道无字真经。在他的层级，这不是秘密，而是政策 |
| S4_jianyuan_second_level | dialogue_mid | 1幕后对话 | 监院真诚地相信自己在做对的事。两种信仰的碰撞——法明的信仰需要理解，监院的信仰需要服从 |
| S4_tangseng_encounter | dialogue_pre | 1真实目的 | 唐僧知道取经的真相——经文本身不重要，这是一场被设计好的意识形态扩张行动 |
| S4_tangseng_encounter | dialogue_mid | 1幕后对话 | 唐僧选择走这条路，不是因为盲信，而是因为他相信：路上的经历比终点的经文更真实 |
| S4_Decision_B | dialogue_pre | 1真实目的 | 诉诸感情DC16（极难），诉诸利害DC12（中等）——监院的价值观排序 |
| S4_Decision_D | decision_pre | 1真实目的 | 这支笔将成为跨场景的物理联结 |

---

## 3. 洞察力消耗与恢复

### 3.1 每场景配额

```yaml
insight_quota_per_scene:
  real_purpose: 2
  behind_dialogue: 2
  total: 4
```

### 3.2 消耗时机

```yaml
consumption_timing: "每条user query前"
selection_method: "玩家主动选择是否使用"
```

### 3.3 未使用洞察的处理

```yaml
unused_insight_bonus:
  trigger: "场景结束"
  reward: "完整场景回顾（debrief）"
  content: "场景中的所有隐藏信息、变量变化、NPC真实目的汇总"
```

### 3.4 已使用洞察的限制

```yaml
used_insight_limitation:
  during_game: "仅显示已使用洞察对应的回顾内容"
  end_game: "完整回顾解锁"
```

---

## 4. 洞察揭示的技术实现

### 4.1 数据结构

```yaml
insight_reveal:
  id: unique_identifier
  location: "npc_dialogue_node_id OR decision_id"
  type: "real_purpose | behind_dialogue"
  cost: 1
  reveals:
    title: "揭示标题"
    content: "揭示内容"
    hidden_intent: "NPC隐藏意图（如适用）"
  prerequisites: []  # 可选前置条件
  mutual_exclusive: []  # 互斥的揭示（同位置不同类型）
```

### 4.2 触发检查流程

```
1. 玩家输入query
2. 系统检查当前位置是否有可用洞察
3. 如果有，提示玩家"是否使用洞察力？"
4. 玩家选择：
   - 使用：扣除对应类型洞察点，显示揭示内容，继续正常流程
   - 不使用：继续正常流程
5. 更新洞察使用记录
```

### 4.3 隐藏意图保护规则

```yaml
hidden_intent_protection:
  rule: "hidden_intent内容绝不暴露给其他NPC"
  scope: "仅当前玩家可见，仅通过洞察系统揭示"
  persistence: "存储在玩家存档中，用于影响力报告"
```

---

## 5. 与Architecture Team的接口

### 5.1 洞察力状态存储

```yaml
player_insight_state:
  scene_id: string
  real_purpose_remaining: int (0-2)
  behind_dialogue_remaining: int (0-2)
  used_insights: [insight_reveal_id]
  discovered_hidden_intents: [npc_id]
```

### 5.2 洞察触发API

```yaml
# 检查当前位置是否有可用洞察
GET /api/insight/available
Request: { scene_id, location_id, player_state }
Response: {
  available: boolean,
  insights: [{
    type: "real_purpose" | "behind_dialogue",
    cost: int,
    preview: string  # 提示性文字，如"揭示NPC隐藏动机"
  }]
}

# 使用洞察
POST /api/insight/use
Request: { scene_id, location_id, insight_type, player_state }
Response: {
  success: boolean,
  remaining: { real_purpose: int, behind_dialogue: int },
  reveal: { title: string, content: string }
}
```

### 5.3 场景回顾数据

```yaml
# 场景结束时生成
generate_scene_debrief:
  input: { scene_id, player_choices, used_insights }
  output: {
    standard_debrief: "基于已使用洞察的回顾",
    full_debrief: "所有隐藏信息（如果未使用洞察≤2）"
  }
```

---

## 6. 设计原则验证

### 6.1 简化原则检查

- [x] 无D20检定
- [x] 无修正值计算
- [x] 固定配额（2+2）
- [x] 二元选择（用/不用）

### 6.2 信息保护检查

- [x] hidden_intent绝不暴露给其他NPC
- [x] 洞察揭示仅玩家可见
- [x] 存储在玩家私有状态

### 6.3 激励机制检查

- [x] 未使用洞察 → 场景回顾奖励
- [x] 已使用洞察 → 游戏结束才解锁完整回顾
- [x] 鼓励策略性使用，而非囤积
