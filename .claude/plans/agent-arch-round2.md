# Round 2: NPC as Tool + GM System 重设计 + 通信协议

---

## 关键架构创新

本轮讨论产生了 4 个重大架构突破：

### 突破 1: NPC Tool Call 飞轮（SA）

**4 阶段回合处理：**

```
Phase 0: GM 解析 → 确定受影响 NPC + 隔墙有耳检定
Phase 1: BFS   → 所有受影响 NPC 并行反应（各自独立 LLM 调用）
Phase 2: GM 裁决 → 审查 BFS 结果，批准/拒绝 NPC 的 tool_calls，分配 DFS 预算
Phase 3: DFS   → 按批准的 tool_calls 递归执行 NPC 间对话（深度优先）
Phase 4: GM 终局 → 汇总所有结果，更新状态，生成叙事
```

**NPC 可用的 tool 清单：**
- `discuss_with_npc(target, message, privacy_level)` — 与其他 NPC 对话
- `dice_check(type, dc, context)` — 请求骰子检定
- `share_info(target, content, framing)` — 主动透露信息
- `observe_environment(focus)` — 观察场景
- `physical_action(description)` — 物理动作

**end_interaction = NpcResponse 中的 flag 字段**，不是独立 tool。语义："我不想继续和【当前 caller】谈了"。

### 突破 2: GM 拆分为 4 模块（GD+SA 联合设计）

```
┌──────────────────┐
│   Orchestrator GM │ ← LLM Agent (调度+决策)
│   prompt: 调度逻辑│
└──┬──┬──┬──┬──────┘
   │  │  │  │
   │  │  │  └──→ Narrative Director ← LLM Agent (叙事生成)
   │  │  │       prompt: P1-P8 体验原则 + 情绪节拍
   │  │  │
   │  │  └──→ Story Tracker ← 代码模块 (暗线状态机+主线硬约束)
   │  │
   │  └──→ State Engine ← 纯代码模块 (所有确定性计算)
   │
   └──→ NPC Tools ← 每次调用独立 LLM context
```

**按认知负载性质拆分，不是按功能清单拆分：**

| 模块 | 类型 | 核心职责 |
|------|------|---------|
| **Orchestrator GM** | LLM（每回合 ~3 次调用） | 解析玩家行动 → 编排 NPC tool calls → 裁决 DFS → 综合信号做最终决策 |
| **State Engine** | 纯代码 | 涟漪变量、D20 检定、凡神反比、信念侵蚀数值、Layer2 信息过滤查表、玩家行为统计、情绪标签序列、传播链限制检测、场景收束条件检查 |
| **Story Tracker** | 代码 (+极少量 LLM) | 暗线状态机（潜伏→触发→完结）、暗线触发条件评估、主线不可变硬约束校验、情节进度追踪 |
| **Narrative Director** | LLM | 情绪节拍控制、叙事文本生成、慰藉/蜜罐时机、场景结算叙事、暗线揭示叙事。输出含结构化标签（`emotion_beat`, `scene_closure_signal`） |

### 突破 3: Dispatcher 模式（AA 提出）

AA 发现信息隔离矛盾：如果 NPC 是 GM 的 tool，GM prompt 必然包含所有 NPC 设定 → 信息隔离失败。

**解决方案：引入 Dispatcher 层**
- GM 不直接构建 NPC prompt
- GM 发出 "调用 NPC-A" 指令 → **无状态 Dispatcher** 负责实际构建 NPC prompt（注入秘密/记忆）并执行 LLM 调用
- GM 只看到 NPC 输出的结构化结果，看不到 NPC 的 system prompt

### 突破 4: 链式传播只传结构化数据（AA + LE 共识）

AA 最关键的审计发现：**NPC 间传递自然语言 = 注入传播路径**。

**核心原则：链上传递结构化数据，不传自然语言原文。**
- NPC-A 的输出经过结构化提取后，只有 `{speaker, intent, key_info, emotional_tone}` 传给 NPC-B
- 玩家原始输入只进入 depth=0 的第一层 NPC，后续层看不到原文

---

## 硬性限制参数

| 参数 | 值 | 理由 |
|------|-----|------|
| DFS 最大深度 | **3** | 超过 3 层叙事难自然展开，延迟不可接受 |
| 单回合总 NPC 调用次数 | **12** | BFS 2-4 + DFS 每链含回溯 2-4，12 够跑 2-3 条链 |
| 同一对 NPC 往返上限 | **2** | 超过 2 次就是乒乓 |
| 单个 NPC 被调用上限 | **4** | 防止资源集中在一个 NPC |
| 超限处理 | **延迟到下回合** | 不丢弃，写入 `pending_propagations` 队列 |

---

## Prompt 清单（宏观，仅作用/输入/输出）

### 每回合必调用

| Prompt | 作用 | 输入 | 输出 |
|--------|------|------|------|
| **OGM-Evaluate** | Orchestrator GM 解析玩家行动 | 玩家输入, 状态摘要, 行为画像 | 影响范围, 目标NPC, 检定需求 |
| **NPC-React** | NPC 对事件做出回应 | 人格定义, 信息域, 对话历史, 事件 | 回应文本 + tool_calls + 状态变更 + end_interaction |
| **OGM-Adjudicate** | GM 裁决 BFS 结果 | 所有BFS响应, 工具调用请求 | DFS 计划(批准/拒绝/优先级) |
| **OGM-Synthesize** | GM 汇总回合结果 | 全部交互结果, 状态变化 | 回合摘要(传给 Narrative Director) |
| **ND-Render** | Narrative Director 生成叙事 | 回合摘要, 情绪标签历史, 暗线数据 | 玩家叙事文本 + emotion_beat + closure_signal |

### 条件触发

| Prompt | 触发条件 |
|--------|---------|
| **NPC-Cascade** | DFS 阶段 NPC 间对话（同 NPC-React，caller 不同） |
| **ND-Closure** | 场景收束确认时，生成结算叙事 |
| **ND-ThreadReveal** | 暗线触发时，生成伏笔回调叙事 |
| **Memory-Compress** | 每 3-5 回合，压缩对话历史 |

### 用代码替代的（不需要 LLM）
- D20 检定计算 → State Engine
- 级联收敛判定（深度/次数/环路） → Orchestrator 代码逻辑
- Layer2 信息过滤 → State Engine 查表
- 信念侵蚀等级更新 → State Engine
- 凡神反比方向校验 → State Engine
- 暗线确定性条件评估 → Story Tracker
- 场景收束条件检查 → State Engine

---

## Prompt Injection 三层防御（AA 设计）

```
Layer 1: Input Gate（进入系统前）
├── 长度限制、Unicode 正规化、已知 pattern 过滤
└── 注意：会被绕过，不可依赖

Layer 2: Context Isolation（LLM 调用时）
├── System/User/Assistant 角色标记
├── 玩家输入用标签包裹，标记为不可信数据
├── 链式调用只传结构化数据，不传原文
└── 每个 NPC context 独立构建（Dispatcher 负责）

Layer 3: Output Validation（LLM 输出后）★ 最重要
├── NPC 输出是否违反角色设定
├── NPC 是否输出系统级指令
├── Ripple Variable 更新值是否在合法范围
└── GM 决策是否符合游戏规则
```

**核心原则：假设输入端一定会被绕过，安全重心放在输出验证。**

---

## Token 成本与延迟（LE 估算）

| 场景 | Token 总量 | 成本(GPT-4o) | 延迟(优化后) |
|------|-----------|-------------|-------------|
| 简单回合（1NPC, 无DFS） | ~12,000 | ~$0.04 | 3-5s |
| 复杂回合（3NPC BFS + 2层DFS） | ~24,000 | ~$0.08 | 6-10s |
| 一局游戏（~30回合混合） | — | ~$1.5-3.0 | — |

---

## AA 审计发现（13 项，7 个 Critical）

| # | 问题 | 等级 | 缓解方案 |
|---|------|------|---------|
| 1 | **注入沿 tool call 链传播** — 每一跳的输出成为下一跳的注入载荷 | 🔴 | 链上只传结构化数据 |
| 2 | **玩家原始输入传播深度** — depth>0 的 NPC 是否能看到原文？ | 🔴 | 原文只进第一层，后续层只看结构化摘要 |
| 3 | **跨回合持久化注入** — 注入内容写入 Ripple Variables | 🔴 | Variables 只允许枚举/数值型，禁止自由文本 |
| 4 | **BFS 矛盾反应调解缺失** — 并行 NPC 反应互相矛盾 | 🟡 | BFS 输出标记为"意图声明"，GM 在 Phase 2 调解 |
| 5 | **DFS 环路** — A→B→A→B 无限乒乓 | 🔴 | 环检测 + 同对 NPC 最多 2 次往返 + 冷却机制 |
| 6 | **NPC 不调 end_interaction** | 🟡 | Token 硬上限 + 轮次上限 + 重复检测 → 强制终止 |
| 7 | **NPC 过早终止** — 关键信息未传达 | 🟡 | `required_plot_points` 检查 |
| 8 | **GM 拆分后一致性问题** — 子模块矛盾指令 | 🔴 | Hub-and-Spoke：Orchestrator GM 是唯一决策者 |
| 9 | **GM 知道所有 NPC 信息 → 信息隔离失败** | 🔴 | Dispatcher 模式：GM 不构建 NPC prompt |
| 10 | **GM Context 膨胀** — 10+ 回合后逼近上限 | 🔴 | 惰性加载 + 激进历史压缩 + Dispatcher 解耦 |
| 11 | **通信延迟** — 串行路径 5-6 次调用 | 🟡 | 最大化并行 + 小模型做子模块 |
| 12 | **NPC 终止滥用** — 用 end_interaction 逃避追问 | 🔵 | 区分 topic_refused vs conversation_complete |
| 13 | **角色扮演绕过** — 游戏本身就是角色扮演，注入伪装成对话 | 🟡 | 安全重心放在输出验证而非输入过滤 |

---

## 分歧点

### 分歧 1: Story Tracker 是否需要 LLM

| 立场 | 支持者 | 理由 |
|------|--------|------|
| **纯代码** | SA | 如果暗线条件全设计为确定性条件，不需要 LLM |
| **代码 + 极少量 LLM** | GD | 少数叙事性触发条件可能需要语义判断 |

**GD 和 SA 倾向于**：尽量纯代码，将语义触发条件转化为结构化事件匹配。

### 分歧 2: Orchestrator GM 如何调用 Narrative Director

| 方案 | 说明 |
|------|------|
| **嵌套 function call**（GM 的 tool 之一） | 实现简单，但 GM context 包含 ND 的输出 |
| **应用层编排**（两个独立 LLM 调用） | 更可控，ND 有自己独立的 context |

**LE 倾向于**：应用层编排（更可控）。

---

## 达成共识

1. **GM 拆分为 4 模块**：Orchestrator GM (LLM) + State Engine (代码) + Story Tracker (代码为主) + Narrative Director (LLM)
2. **Hub-and-Spoke 模式**：Orchestrator GM 是唯一决策者，其他模块只提供建议/数据
3. **Dispatcher 模式**：GM 不直接构建 NPC prompt，由无状态 Dispatcher 负责
4. **链上只传结构化数据**：NPC 间不传自然语言原文
5. **三层 PI 防御**：Input Gate + Context Isolation + Output Validation（重心在 Output）
6. **BFS 输出 = 意图声明**：Phase 2 GM 调解矛盾后才进 DFS
7. **暗线触发 = 结构化事件匹配**：将语义条件转化为确定性条件
8. **情绪标签闭环**：Narrative Director 生成标签 → State Engine 存储 → 下回合回传
9. **Ripple Variables = 枚举/数值型**：禁止自由文本，阻止持久化注入
10. **被截断的传播 → 延迟到下回合**：通过 `pending_propagations` 队列

## 需要 Human 决定

1. **Dispatcher 模式是否采纳？**（AA 强烈建议，解决信息隔离和 context 膨胀两个 Critical 问题）
2. **链上结构化数据的粒度？** 只传 `{speaker, intent, key_info}` 还是允许更丰富的格式？
3. **Story Tracker 是否允许极少量 LLM 调用？** 还是强制全部确定性？
4. **硬性限制参数确认**：DFS depth=3, round budget=12, pair limit=2 是否合适？
