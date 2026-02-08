# Round 3: NPC 社会 + 弹性 NPC + 双层输出 + 自然交互范式

---

## 背景

Human 在 Round 2 后给出 4 条关键方向：
1. NPC 是一个"社会"——20-30 个 NPC 在后台运转，玩家只能访问其中一部分
2. 弹性 NPC——GM 可以动态创建新 NPC（n-shot 模板）
3. 自然交互范式（RL 风格）——NPC 只能观测：环境信息、伴随行为/语气/语态的语言、决策。不暴露真实意图
4. 双层输出：Observable（对外可见）+ Hidden Intent（仅开发/debug）

---

## 关键架构创新

### 创新 1: 三层 NPC 激活模型（SA）

```
┌─────────────────────────────────────────────┐
│  Layer 0: Active NPC (活跃层)                │
│  ─ 正在与玩家直接交互                         │
│  ─ 完整 LLM 调用 (NPC-React prompt)          │
│  ─ 数量: 1-3 个                              │
│  ─ 持有完整 context: 人格+记忆+信息域+对话历史  │
├─────────────────────────────────────────────┤
│  Layer 1: Background NPC (半活跃层)           │
│  ─ 不在与玩家交互，但在后台与其他NPC互动        │
│  ─ 混合模式: 规则引擎为主 + 关键节点LLM调用     │
│  ─ 数量: 5-10 个                             │
│  ─ 持有压缩 context: 人格+关键记忆摘要         │
├─────────────────────────────────────────────┤
│  Layer 2: Dormant NPC (休眠层)               │
│  ─ 存在于世界中但无当前互动                    │
│  ─ 纯数据: 只维护状态快照 (state card)         │
│  ─ 数量: 10-20 个                            │
│  ─ 零计算开销，仅在被激活时加载                 │
└─────────────────────────────────────────────┘
```

**层间迁移规则（事件驱动状态机）：**
- Dormant → Background：GM 判定该 NPC 的利益/关系与当前事件相关
- Background → Active：玩家 @NPC 对话 / 玩家行动直接影响该 NPC / GM 编排参与
- Active → Background：当前回合无玩家交互 + end_interaction 已设 + 无 pending 传播
- Background → Dormant：连续 5 回合未参与任何互动
- **不允许 Active → Dormant 直接跳级**，必须经 Background 过渡

### 创新 2: 后台社会三级模拟精度（SA）

| 精度 | 适用场景 | 实现方式 | 示例 |
|------|---------|---------|------|
| **L0: 规则模拟** | 日常行为、位置移动、情绪衰减 | 纯代码 State Engine | "张铁匠每天早上去铁匠铺，傍晚回家" |
| **L1: 模板模拟** | NPC 间例行交互、信息自然传播 | 预定义行为模板 + 概率 | "刘商人和张铁匠在市集碰面，有40%概率聊到庙里的事" |
| **L2: LLM 模拟** | 高利害关系的后台互动 | 简化 NPC-React 调用 | "村长召集会议讨论旱灾对策" |

**L2 触发条件（GM 判定）：**
- 涉及暗线触发条件中的关键信息
- 会显著改变某个 Active NPC 的立场
- Story Tracker 标记的关键剧情节点即将被触发
- 玩家行动产生蝴蝶效应，需后台 NPC 真实反应

### 创新 3: NPC State Card（SA）

每个 NPC 的最小持久化单元：

```yaml
npc_state_card:
  id: "npc_village_blacksmith"
  identity:
    name: "张铁匠"
    role: "村东头铁匠铺老板"
    status_tier: "平民/匠人"
  personality_hash: "template_ref:artisan_stubborn_v2"
  current_state:
    location: "铁匠铺"
    emotional_state: "焦虑"
    disposition_toward_player: "neutral"
    active_goals: ["凑够女儿嫁妆", "找到失踪的铁矿来源"]
    known_info_keys: ["village_drought", "temple_robbery_rumor"]
  relationships:
    - target: "npc_village_chief"
      type: "subordinate"
      trust: 0.6
    - target: "npc_merchant_liu"
      type: "trade_partner"
      trust: 0.8
  memory_digest: "最近三天：与刘商人吵了一架关于铁价。听到庙里被偷的传言。"
  last_active_turn: 12
  creation_type: "predefined" | "dynamic"
```

### 创新 4: 双层 NPC 输出（SA + AA 联合设计）

**Observable Output（可观测层）——传给其他 NPC/玩家：**

```yaml
observable_output:
  speaker: "npc_id"
  speech:
    content: "这旱灾再不下雨，我这铁匠铺也开不下去了。"
    tone: "frustrated"          # 枚举
    volume: "normal"            # 枚举
    speech_style_markers: ["叹气", "摇头"]
  actions:
    - type: "gesture"
      description: "重重放下锤子"
    - type: "movement"
      description: "走向门口张望天色"
  expression:
    primary: "愁眉不展"
    micro_expression: null      # 高洞察值才能读取
  tool_calls: [...]
  end_interaction: false
```

**Hidden Intent（隐藏层）——仅开发/debug：**

```yaml
hidden_intent:
  speaker: "npc_id"
  true_intent: "试探玩家是否知道旱灾的真正原因（村长截留了水源）"
  reasoning:
    - "玩家刚从村长那边来，可能知道些什么"
    - "但我不能直接问，因为如果玩家和村长是一伙的我就完了"
    - "先用抱怨旱灾做试探，看玩家怎么接"
  counterpart_assessment:
    perceived_intent: "玩家似乎只是路过，但问的问题太有针对性"
    trust_level: 0.3
    threat_level: 0.2
  info_strategy:
    willing_to_share: ["drought_severity", "trade_disruption"]
    withholding: ["village_chief_water_diversion"]
    looking_to_extract: ["player_relationship_with_chief"]
  true_emotional_state: "恐惧（怕被村长知道自己在调查）"
  next_move_plan: "如果玩家表现出对村长的不满，透露水源的线索"
```

**核心规则：NPC 间只传递 observable 部分。hidden 层绝不跨越 NPC 边界。**

### 创新 5: "缝隙参与"原则（GD）

**核心悖论**：P1 要求玩家感到"被忽视"，但游戏本身要求"有参与感"。

**解法**：
- NPC 社会运转正常时，玩家无法介入。玩家的窗口是 NPC 社会出现"裂缝"的时候——两个 NPC 的利益冲突导致双方都需要一个不起眼的人帮忙、传话、跑腿、做脏活
- 玩家的价值不是"重要"，而是"刚好在这里"——因为你不引人注意、因为你碰巧听到了什么、因为你无足轻重到不会被怀疑
- 情感锚点：至少有 1 个 NPC 真正"看见"了玩家角色——不是因为你有用，而是因为某种私人原因。这是 P8 的微光来源

### 创新 6: "痕迹浮现"机制（GD）

后台 NPC 互动的痕迹渗透到前台，分三层信息获取：

| 层次 | 获取方式 | 获得内容 |
|------|---------|---------|
| **Level 1（被动浮现）** | 旁观即可 | NPC 情绪变化、突然改变态度、话里带刺 |
| **Level 2（主动探索）** | D20+洞察检定 | 碎片信息（一个线索片段，不是完整真相） |
| **Level 3（暗线贯穿）** | 多个碎片拼合 | 理解后台正在发生的一条完整博弈链 |

**关键设计决策（GD）**：洞察检定不应直接看穿 Hidden Intent，只应给"线索和感觉"——直接看穿破坏 P7（发现感）和 P5（暗线隐晦）。

### 创新 7: 弹性 NPC 创建管线（SA）

**创建流程：**
1. Orchestrator GM 做出决策（需要什么样的 NPC、叙事用途）
2. GM 发出结构化创建指令（role、purpose、must_know/must_not_know）
3. Dispatcher 加载 n-shot 模板（3 个 shot，~800 token），单次 LLM 调用生成
4. State Engine 执行融入管线（自动建立关系网、初始化信息域、注入公共知识）
5. 生成 State Card → 进入对应层级

**持久化规则：**
- Named NPC（与玩家有意义对话 ≥2 轮 / 被其他 NPC 引用 / 承载暗线信息）→ 持久化
- Unnamed NPC → 场景结束后回收。被玩家 @对话 → 升级为 Named

### 创新 8: 信息传播失真设计（GD）

**"衰减+校准"双机制：**

- **衰减机制**：信息每传播一次，可信度标签降一级：`确认事实 → 可靠传闻 → 未证实消息 → 街头谣言`。谨慎的 NPC 不会基于"街头谣言"做关键决策
- **校准机制**：关键决策前给 NPC 一次"向当事人直接确认"的机会；某些核心事实 GM 确保至少有一条可靠传播路径

**GD 核心观点**：失真是特性不是缺陷——创造发现感、制造道德困境、生成自然戏剧性。玩家可以主动利用失真（信息操纵作为高级玩法）。

### 创新 9: Information Ledger 系统（AA 提出）

**解决"谁知道什么"的追踪问题：**
- 每条信息有唯一 InfoID、来源、内容摘要、可信度
- 每个 NPC 持有 `known_info: Set[InfoID]` + 每条信息的主观置信度
- 传播时不复制原始内容，只传 InfoID + 传播者的"版本"。变异版本获新 InfoID，标注 `derived_from: original_InfoID`
- 追踪"谁知道什么" = 查 Set 操作，State Engine 维护 NPC × InfoID 稀疏矩阵

### 创新 10: 误判矫正机制（AA 提出）

防止 NPC 社会"认知失控"的四重防线：

**A. 真相锚点**：State Engine 维护客观事实层（ground truth），NPC 主观认知偏离度有上限。超过阈值 → 触发矫正事件（安排直接互动机会，叙事自然的"澄清误会"）

**B. 信息衰减**：每条 InfoItem 有 `freshness` 属性，随轮次递减，低 freshness 信息权重降低

**C. 社会圈层拓扑**：定义社会圈层（寺庙僧侣圈、集市商人圈、官府圈），圈层间传播有瓶颈，限制误判扩散

**D. AA 认知一致性审计**：定期抽取 NPC 社会的"认知快照"，对比 ground truth 偏离度。全社会平均偏离度超阈值 → 向 GM 发预警

---

## 每回合处理流程更新

在 Round 2 的 4 阶段飞轮基础上，新增 Phase 0.5 和 Phase 5：

```
Phase 0:   GM 解析玩家行动
Phase 0.5: 后台社会 Tick ★ 新增
           ├── State Engine 执行 L0/L1 后台模拟 (毫秒级)
           ├── GM 判定是否需要 L2 后台互动 (最多 2 次 LLM)
           ├── 后台信息传播结果更新所有 NPC State Cards
           └── 如果后台互动改变了 Active NPC 的状态，标记 dirty
Phase 1:   BFS — 受影响 NPC 并行反应 (双层输出)
Phase 2:   GM 裁决
Phase 3:   DFS — 递归执行 (只传 observable)
Phase 4:   GM 终局 + 状态更新
Phase 5:   NPC 层级迁移 ★ 新增
           ├── 检查层级迁移条件
           ├── 执行 Active↔Background↔Dormant 转换
           ├── 对新降级的 NPC 做 memory compress
           └── 回收临时 NPC (unnamed + 场景结束)
```

---

## 成本与延迟估算更新

| 场景 | Round 2 估算 | Round 3 估算 | 增量原因 |
|------|------------|------------|---------|
| 简单回合（1 Active, 无后台事件） | ~12,000 token / 3-5s | ~12,000 token / 3-5s | 无（L0/L1 纯代码） |
| 典型回合（2 Active + 后台 L1 传播） | ~24,000 token / 6-10s | ~24,000 token / 6-10s | 无（L1 纯代码） |
| 复杂回合（3 Active + 1次 L2 后台） | ~24,000 token / 6-10s | ~28,000 token / 7-12s | +4,000 token / +2s |
| 含弹性创建回合（创建2 NPC + 正常） | N/A | ~30,000 token / 8-13s | 创建调用 ~2,000 token |

**关键：后台社会大部分时候是零 LLM 开销。只有关键节点才触发 L2。**

---

## 硬性限制参数（新增/更新）

| 参数 | 值 | 理由 |
|------|-----|------|
| 单场景最大 NPC 总数 | **30** | 超过 30 State Card 管理复杂度过高 |
| Active NPC 上限 | **4** | 与 Round 2 "单 NPC 被调用上限 4" 兼容 |
| Background NPC 上限 | **10** | L1 模拟无成本，但过多增加 State Engine 计算 |
| 每回合 L2 后台 LLM 调用 | **2** | 控制延迟和成本 |
| 每回合弹性创建 NPC 数 | **3** | 单次批量创建，超过 3 个不自然 |
| 临时 NPC 存活回合 | **当前场景结束** | 除非被升级为 named |
| Background→Dormant 冷却 | **5 回合无互动** | 避免频繁休眠/唤醒 |

---

## AA 审计发现（15 项，7 个 Critical）

| 编号 | 风险项 | 严重性 | 核心缓解策略 |
|------|--------|--------|-------------|
| 1.1.1 | **双世界割裂**——后台规则模拟 vs 前台 LLM 驱动的行为粒度不同 | 🔴 | 后台事件摘要（模板生成）+ AA 一致性校验 |
| 1.1.2 | **后台→前台过渡**——NPC 被激活时 prompt 信息量可能过大 | 🔴 | 压缩记忆档案（~800 token）+ 首次校验 |
| 1.1.3 | 后台逻辑错误（NPC 死后仍互动等矛盾状态） | 🟡 | 硬约束检查 + 叙事修补机制 |
| 1.2.1 | 190 条关系的状态管理 | 🟡 | 稀疏表示（只维护有意义的边）+ 复合标签 |
| 1.2.2 | **"谁知道什么"追踪** | 🔴 | Information Ledger（InfoID 系统） |
| 1.2.3 | 状态空间爆炸 | 🟡 | 分层管理 + 状态上限 |
| 2.1.1 | 弹性 NPC 人格稳定性 | 🟡 | 每次调用含完整模板 + 对话轮次上限（5-8轮） |
| 2.1.2 | 多次调用后人格漂移 | 🟡 | 首次特征缓存 + 调用超2次自动升级 |
| 2.1.3 | **弹性 NPC 信息域初始化** | 🔴 | 公共知识层 + 信息黑名单 + 角色类型知识子集 |
| 2.2.1 | **"茶馆钓鱼"攻击**——批量创建弹性 NPC 套信息 | 🔴 | 频率限制 + 信息天花板 + 行为模式检测 |
| 2.2.2 | **弹性 NPC 注入攻击** | 🔴 | 同等 PI 防御 + 权限最小化（只能访问公共知识层） |
| 3.1.1 | **Hidden Intent 直接泄露**——同一 LLM 调用的注意力耦合 | 🔴 | 两次独立调用（高风险 NPC）或 AA 后处理 |
| 3.1.2 | 措辞中的无意识信号（LLM "不会说谎"的内在张力） | 🟡 | 转化为游戏机制（NPC 表演能力等级） |
| 3.2.1 | 观测粒度平衡 | 🟡 | Observable 禁止情绪形容词，用枚举标签 |
| 4.1.1 | **误判雪球效应**——NPC 社会认知失控 | 🔴 | 真相锚点 + 信息衰减 + 圈层拓扑 + AA 认知审计 |

---

## 分歧点

### 分歧 1: 双层输出是否需要两次独立 LLM 调用

| 立场 | 支持者 | 理由 |
|------|--------|------|
| **高风险 NPC 用两次调用** | AA | 单次调用存在注意力耦合导致的结构性泄露，尤其在极端欺骗场景 |
| **全部单次调用 + AA 后处理** | SA (隐含) | 成本翻倍不可接受，后处理校验足够 |

**AA 建议折中**：只对"有主动欺骗意图"的 NPC 交互启用两次调用。这个决策影响 token 成本预算。

### 分歧 2: 后台社会 Tick 的执行时机

| 方案 | 说明 |
|------|------|
| **Phase 0 之前**（世界先动） | 更像真实世界——后台变化先于玩家行动生效 |
| **Phase 0 之后**（Phase 0.5）| 可以根据玩家行动影响范围调整后台模拟精度 |

**SA 暂选 Phase 0 之后**，但标记为 UNCERTAIN。

### 分歧 3: LLM "不会说谎"的问题如何处理

| 立场 | 支持者 | 理由 |
|------|--------|------|
| **转化为游戏机制** | AA, GD | 引入"表演能力等级"，LLM 的局限性变成 NPC 的角色特征 |
| **结构性解决** | 隐含需求 | 通过 prompt engineering 和两次调用彻底解决 |

**GD 和 AA 倾向于**：这是一个可接受的风险，甚至可以是设计优势。

---

## 达成共识

1. **三层 NPC 激活模型**：Active / Background / Dormant，按与玩家交互距离分配计算资源
2. **后台社会三级模拟**：L0 规则 / L1 模板 / L2 LLM，绝大部分时候零 LLM 开销
3. **NPC State Card 作为最小持久化单元**：所有 NPC 无论层级都有 State Card
4. **双层输出 Observable + Hidden Intent**：Observable 用枚举标签和结构化字段，禁止情绪形容词
5. **"缝隙参与"原则**：玩家在 NPC 社会的价值来自"被忽视"本身，介入窗口是 NPC 社会的裂缝
6. **"痕迹浮现"机制**：三层信息获取（被动浮现 / 主动探索 / 暗线贯穿），洞察检定给线索不给答案
7. **弹性 NPC 创建管线**：GM 决策 → Dispatcher 执行 → State Engine 融入，n-shot 3 个 shot
8. **弹性 NPC 叙事权重严格分层**：不承载暗线核心，不建立深层情感连接，信息价值为碎片级
9. **Information Ledger 系统**：InfoID + 传播版本追踪 + NPC × InfoID 稀疏矩阵
10. **误判矫正四重防线**：真相锚点 + 信息衰减 + 圈层拓扑 + AA 认知审计
11. **信息失真"衰减+校准"双机制**：可信度标签降级 + 关键事实锚点保障
12. **每回合新增 Phase 0.5（后台 Tick）和 Phase 5（层级迁移）**

---

## Human 决定（Round 3 后反馈）

### 已决定：洞察值系统大幅简化

Human 在 Round 3 后决定简化洞察值机制，取代原有的 D20+Insight 检定系统：

**新洞察值机制：**
- 每个场景固定分配洞察值（不可累积、不可叠加）
- 每场景 2 次「真实目的」+ 2 次「幕后对话」，独立计数
- **洞察力是 per-query 的**：每次消耗针对一个具体的 player query（一问一答），不是 per-NPC 或 per-conversation
- 「真实目的」揭示：该 query 中 NPC 回复的 Hidden Intent（true_intent + reasoning + info_strategy）
- 「幕后对话」揭示：该 query 触发的 NPC 间幕后交互的完整过程（DFS 链的所有 observable + hidden + 各自真实意图）
- Hidden intent 绝不暴露给其他 NPC

**场景结算的信息博弈：**
- 场景内没用洞察 → 场景结束后揭示所有真实（完整 debrief）
- 场景内用了洞察 → 完整 review 要等到整局游戏结束后才能从头看

**架构影响：**
- D20+Insight 检定系统删除（无骰子、无修正值、无检定难度）
- State Engine 的骰子模块缩减为简单资源扣减
- Layer 2 信息过滤查表删除
- Hidden 层每次都生成，按需展示（不是可选生成）
- Narrative Director 新增职责：场景结算时根据洞察使用情况决定输出内容

### 待决定

1. **双层输出是否需要两次调用？** AA 建议至少对"有主动欺骗意图"的 NPC 交互启用。影响 token 成本和延迟预期。
2. **后台社会 Tick 的执行时机？** Phase 0 之前（世界先动）还是 Phase 0 之后（可根据玩家行动调整精度）？
3. **弹性 NPC 数量上限**：每回合 3 个、每场景 10 个是否合适？
4. **Background NPC 的 L2 LLM 调用是否用更小的模型**以降低成本？
5. **临时 NPC 是否可以跨场景存活**（比如茶馆中动态创建的 NPC 在玩家下次回到茶馆时还在）？
6. **observable 中的 `micro_expression` 过滤方式**：代码层过滤（Dispatcher）还是交给 NPC LLM 自行判断？
7. **NPC 社会的"认知偏离度阈值"**：偏离多少触发矫正事件？这需要 playtest，但初始值应在此确定。
