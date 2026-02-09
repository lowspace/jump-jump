# Scene Team → Architecture Team 交接文档

> 本文档汇总Scene Team生成的所有技术规格，为Architecture Team提供实现《Jump Jump》对话系统和决策系统的完整参考。

---

## 1. 交付物清单

### 1.1 NPC对话配置 (16个YAML文件)

| 文件 | NPC | 场景 | 关键特性 |
|------|-----|------|----------|
| `nezha.yaml` | 哪吒 | Scene 1 | 信任度系统(0-5)，双刀抉择，隐藏渴望被阻止 |
| `lijing.yaml` | 李靖 | Scene 1 | 犹豫度系统，感情vs利害DC差异 |
| `yangjian.yaml` | 杨戬 | Scene 1 | 条件触发NPC，回响种子 |
| `tianpeng.yaml` | 天蓬元帅 | Scene 2 | 固定坠落事件，最后话语条件触发 |
| `juanlian.yaml` | 卷帘大将 | Scene 2 | +5被动洞察，永远在观察 |
| `xuanming.yaml` | 宣明 | Scene 2 | 官僚回避型，怕麻烦 |
| `laohou.yaml` | 老猴 | Scene 3 | 恐惧与保护，第三条路支持 |
| `tietou.yaml` | 铁头 | Scene 3 | 愤怒掩盖恐惧，激进选择 |
| `zixia.yaml` | 紫霞 | Scene 3 | 条件触发，寻找悟空 |
| `tianbing-duizhang.yaml` | 天兵队长 | Scene 3 | 平庸之恶，齿轮化身 |
| `huikong.yaml` | 慧空 | Scene 4 | 15年秘密，核心台词只说一次 |
| `jianyuan.yaml` | 监院 | Scene 4 | 体制执行者，DC分层 |
| `tangseng.yaml` | 唐僧 | Scene 4 | 条件触发，最多5句，全为问句 |
| `grandmother.yaml` | 祖母 | Scene 0 | 4个故事映射Scene 1-4 |
| `wukong-s0.yaml` | 悟空(山下) | Scene 0 | 绝不说话，物理现象存在 |
| `traveler.yaml` | 行者 | Scene 0 | 唐僧前兆，极简对话 |

### 1.2 决策流程配置 (17个YAML文件)

| 文件 | 决策点 | 场景 | 类型 |
|------|--------|------|------|
| `scene1-decision-a.yaml` | 你去找谁？ | Scene 1 | 核心分支 |
| `scene1-decision-b.yaml` | 剔骨进行时 | Scene 1 | 核心时刻 |
| `scene1-decision-c.yaml` | 离开前 | Scene 1 | 微决策 |
| `scene2-decision-a.yaml` | 第一步行动 | Scene 2 | 核心分支 |
| `scene2-decision-b.yaml` | 你怎么回答？ | Scene 2 | 陷阱对话 |
| `scene2-decision-c.yaml` | 回去的路上 | Scene 2 | 微决策 |
| `scene2-decision-d.yaml` | 灵蕴账目处置 | Scene 2 | 终极决策 |
| `scene3-decision-a.yaml` | 猴群会议 | Scene 3 | 立场表态 |
| `scene3-decision-b.yaml` | 桃树的命运 | Scene 3 | 核心P6涟漪 |
| `scene3-decision-c.yaml` | 齐天大圣的名号 | Scene 3 | 微决策 |
| `scene3-decision-d.yaml` | 石卵的去留 | Scene 3 | 微决策 |
| `scene4-decision-a.yaml` | 如何处理空白经卷 | Scene 4 | 初始选择 |
| `scene4-decision-b.yaml` | 是否质问监院 | Scene 4 | 核心对峙 |
| `scene4-decision-d.yaml` | 离开时 | Scene 4 | 微决策 |
| `scene0-decision-a.yaml` | 石壁字迹 | Scene 0 | 发现 |
| `scene0-decision-b.yaml` | 山体深处的声音 | Scene 0 | 感知 |
| `scene0-decision-c.yaml` | 最后的行为 | Scene 0 | 种子 |

### 1.3 系统规格文档

| 文件 | 内容 |
|------|------|
| `insight-system.md` | 洞察力系统完整规格，含40+触发点 |
| `behind-scenes-reveal.md` | 背后博弈展示系统规格 |

---

## 2. 核心系统架构

### 2.1 数据流图

```
┌─────────────────────────────────────────────────────────────┐
│                      Player Input                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ NPC Dialogue │  │   Decision   │  │   Insight    │      │
│  │   System     │  │    Flow      │  │   System     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           │                                │
│                           ▼                                │
│              ┌─────────────────────────┐                   │
│              │    Variable Engine      │                   │
│              │  (State + Echo System)  │                   │
│              └───────────┬─────────────┘                   │
│                          │                                 │
│         ┌────────────────┼────────────────┐               │
│         ▼                ▼                ▼               │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐          │
│  │   Output   │  │  Behind-   │  │   Scene    │          │
│  │  Generator │  │ the-Scenes │  │   Debrief  │          │
│  └────────────┘  └────────────┘  └────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 关键数据结构

#### NPC状态
```yaml
npc_state:
  npc_id: string
  trust: int (0-5)  # 哪吒专用
  emotional_state: enum
  hidden_intent_revealed: boolean
  relationship_variables: map
```

#### 玩家变量
```yaml
player_variables:
  # Scene 1
  nezha_trust: int (0-5)
  knife_choice: enum [父刀, 师刀]
  wushi_presence: enum [高, 中, 低]
  lijing_hesitation: enum [高, 中, 低]
  armguard: enum [带走, 留下]
  yangjian_triggered: boolean

  # Scene 2
  ledger_choice: enum [揭发, 隐瞒, 部分揭露]
  tenpeng_last_words: boolean
  juanlian_suspicion: int (0-10)
  seventh_aperture_awareness: enum
  lingshan_secret: enum [高, 中, 低, 无]
  survival_method: enum

  # Scene 3
  peach_tree_fate: enum [砍掉, 保留, 移植]
  monkey_unity: enum [团结, 分裂, 散去]
  wukong_stick: enum [保留, 留下, 未发现]
  zixia_encounter: enum
  resistance_choice: enum [留守, 隐匿, 反抗]
  memory_kept: enum [铭记, 暗中传承, 遗忘]

  # Scene 4
  sutra_truth: enum [禅意, 政治, 悖论, 不理解]
  final_scroll: enum [照抄, 空白, 自己的话, 什么都没写]
  tangseng_encounter: enum
  huikong_relationship: enum
  faith_state: enum [坚定, 动摇, 重建, 崩塌]
  pen_taken: enum [带走, 留下]

  # Scene 0
  wall_inscription: enum [描下, 辨认, 忽略, 抹掉]
  mountain_voice: enum [倾听, 逃跑, 对话, 告知]
  final_act: enum [种桃核, 刻名字, 无行动, 对山说话]
  grandmother_stories: int (0-4)
  curiosity_level: enum [高, 中, 低]
  wukong_awareness: enum [意识到, 隐约感觉, 完全不知道]

  # 跨场景累积
  philosophy_stance: vector
  decision_duration: int (seconds)
  moral_consistency: float (-1 to 1)
  info_exploration_rate: float (0-100%)
```

#### 洞察力状态
```yaml
insight_state:
  scene_id: string
  real_purpose_remaining: int (0-2)
  behind_dialogue_remaining: int (0-2)
  used_insights: [insight_id]
  discovered_hidden_intents: [npc_id]
```

---

## 3. 关键实现要点

### 3.1 NPC对话系统

#### 节点跳转逻辑
```python
class DialogueNode:
    node_id: str
    trigger: str  # phase_start, decision_X, condition_met
    text: str
    player_options: [PlayerOption]

class PlayerOption:
    id: str
    text: str
    skill_check: Optional[SkillCheck]
    effect: Effect
    next_node: str
    hidden: Optional[str]  # 隐藏信息，不显示给其他NPC
    insight_reveal: Optional[str]  # 使用洞察时揭示
```

#### 条件触发NPC
```python
# 杨戬、紫霞、唐僧、行者
class ConditionalNPC:
    trigger_conditions: [Condition]
    trigger_logic: "AND" | "OR"

    def should_trigger(self, player_state) -> bool:
        if self.trigger_logic == "OR":
            return any(c.check(player_state) for c in self.conditions)
        else:
            return all(c.check(player_state) for c in self.conditions)
```

### 3.2 决策系统

#### 技能检定
```python
class SkillCheck:
    skill: str  # persuasion, deception, insight, investigation, etc.
    dc: int
    modifier_source: Optional[str]  # 如 "yangjian_triggered: +1"

    def roll(self, player_state) -> Result:
        # 简化版：无需D20，直接比较
        # 或者使用固定结果基于玩家选择
        pass
```

#### 决策效果
```python
class DecisionEffect:
    variable_changes: [VariableChange]
    echo_preview: Optional[str]
    next_phase: Optional[str]
    unlock_options: [str]
    conditional_narrative: Optional[str]
```

### 3.3 洞察力系统

#### 使用流程
```
1. 玩家输入query
2. 系统检查：当前位置是否有可用洞察？
3. 提示玩家："是否使用洞察力？(剩余：真实目的{x}/幕后对话{y})"
4. 玩家选择：
   - 使用洞察 → 扣除点数，显示揭示内容
   - 不使用 → 继续正常流程
5. 记录使用
```

#### 揭示内容保护
```yaml
insight_reveal_protection:
  rule: "hidden_intent内容绝不暴露给其他NPC"
  implementation:
    - 存储在player私有状态
    - 不加入NPC对话上下文
    - 仅用于影响力报告
```

### 3.4 背后博弈展示

#### 展示时机
```python
class RevealTiming:
    triggers = {
        "decision_made": "决策确认后立即",
        "phase_end": "阶段叙事结束后",
        "scene_end": "场景完全结束后",
        "echo_triggered": "在叙事中自然融入",
        "insight_used": "使用洞察时立即"
    }
```

#### Scene 0重新渲染
```python
def generate_rerender(player_state):
    """
    基于Scene 1-4的所有变量，生成Scene 0的重新渲染版本
    """
    changes = []

    # 桃树状态
    if player_state.peach_tree_fate == "保留":
        changes.append({
            "element": "烧焦桃树残根",
            "new_description": "一株活着的小桃树，很瘦很矮但确实活着"
        })

    # 石壁字迹
    if player_state.memory_kept == "铭记":
        changes.append({
            "element": "石壁字迹",
            "new_description": "字迹明显更清晰，像在抵抗风化",
            "mechanical": "辨认DC降低2"
        })

    # ... 更多元素

    return changes
```

---

## 4. API接口规格

### 4.1 NPC对话API

```yaml
# 获取当前对话节点
GET /api/dialogue/current
Request: { scene_id, npc_id, player_state }
Response: {
  node: DialogueNode,
  available_options: [PlayerOption],
  insight_available: boolean
}

# 提交玩家选择
POST /api/dialogue/choose
Request: { scene_id, npc_id, option_id, player_state }
Response: {
  next_node: DialogueNode,
  effects: [Effect],
  variable_changes: [VariableChange]
}
```

### 4.2 决策API

```yaml
# 获取决策点
GET /api/decision/current
Request: { scene_id, phase_id, player_state }
Response: {
  decision: Decision,
  choices: [Choice],
  insight_available: boolean
}

# 提交决策
POST /api/decision/make
Request: { scene_id, decision_id, choice_id, player_state }
Response: {
  result: Result,
  narrative: string,
  variable_changes: [VariableChange],
  echo_preview: string
}
```

### 4.3 洞察力API

```yaml
# 检查可用洞察
GET /api/insight/available
Request: { scene_id, location_id, player_state }
Response: {
  available: boolean,
  insights: [{
    type: "real_purpose" | "behind_dialogue",
    cost: int,
    preview: string
  }]
}

# 使用洞察
POST /api/insight/use
Request: { scene_id, location_id, insight_type }
Response: {
  success: boolean,
  remaining: { real_purpose: int, behind_dialogue: int },
  reveal: { title: string, content: string, hidden: string }
}
```

### 4.4 背后博弈API

```yaml
# 获取变量变化
GET /api/behind-scenes/variable-changes
Request: { scene_id, phase_id, player_state }
Response: {
  changes: [VariableChangeDisplay]
}

# 获取回响
GET /api/behind-scenes/echoes
Request: { scene_id, phase_id, player_state }
Response: {
  echoes: [EchoDisplay]
}

# 获取Scene 0重新渲染
GET /api/behind-scenes/rerender
Request: { player_complete_state }
Response: {
  element_changes: [ElementChange],
  full_narrative: string
}
```

---

## 5. 测试要点

### 5.1 NPC对话测试

- [ ] 每个对话节点都能正确跳转
- [ ] 条件触发NPC在正确条件下出现
- [ ] 技能检定结果影响正确
- [ ] hidden内容不泄露给其他NPC

### 5.2 决策测试

- [ ] 所有决策路径可达
- [ ] 变量变化正确记录
- [ ] echo preview正确显示
- [ ] 程度弹性正确计算

### 5.3 洞察力测试

- [ ] 每场景配额正确(2+2)
- [ ] 消耗后剩余正确
- [ ] 揭示内容正确显示
- [ ] 未使用洞察奖励正确

### 5.4 回响测试

- [ ] Scene 1选择影响Scene 2
- [ ] Scene 2选择影响Scene 3
- [ ] Scene 3选择影响Scene 4
- [ ] 所有选择影响Scene 0重新渲染

---

## 6. 已知限制与建议

### 6.1 当前设计限制

1. **无随机性**：简化版洞察力系统无D20，所有结果基于玩家选择
2. **线性回响**：回响关系在设计文档中已固定，无动态生成
3. **固定NPC**：每个场景的NPC是固定的，无动态生成

### 6.2 扩展建议

1. **动态回响**：未来可考虑基于玩家行为模式生成新的回响
2. **NPC关系网**：可实现NPC之间的信息传递（需小心hidden_intent保护）
3. **多周目解锁**：可添加新洞察点，仅在多周目时可用

---

## 7. 联系与问题

如有问题，请参考：
- 设计文档：`/claude/plans/scenes/`
- 全局变量：`/claude/plans/scenes/_global/variable-registry.md`
- 回响映射：`/claude/plans/scenes/_global/echo-map.md`

---

**文档版本**: 1.0
**生成日期**: 2026-02-09
**生成者**: Scene Team Lead
