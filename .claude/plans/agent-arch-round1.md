# Round 1: Agent 身份与职责边界

---

## 讨论过程

### SA（系统架构师）提案

**Agent 清单（6 类）：**

| Agent | 定义 | 是否 LLM |
|-------|------|----------|
| **Player Proxy** | 将人类自然语言输入标准化为结构化行动的 adapter/gateway | 视 UI 决定（CLI 结构化输入 = 非 LLM；自由文本 = 需要 LLM） |
| **NPC Agent** (×N) | 拥有独立人格、动机、信息域的自主博弈参与者 | ✅ 独立 LLM context |
| **Core GM** | 实时游戏运行引擎：接收行动、执行规则、驱动传播、渲染叙事 | ✅ 独立 LLM context |
| **Story Tracker** | 独立追踪叙事状态的被动查询服务 | 推荐纯数据服务，非 LLM |
| **Audit Module** | 独立第三方审计者，验证规则一致性和叙事合理性 | ✅ 独立 LLM context |
| **Skill Pipeline** | 统一机制执行层：骰子检定、洞察值计算、输出渲染 | 纯函数模块 |

**GM 拆分方案：** Story Tracker 是独立服务（非 GM 子模块）。
- Core GM → Story Tracker：单向事件推送（每回合结束时）
- Story Tracker → Core GM：同步查询响应（被动模式）
- **关键决策：Story Tracker 是被动的，不主动干预游戏流程。**

**Audit Module 位置：** 旁路观察者（Sidecar Observer），异步运行，不阻塞游戏。
- 审计谁：Core GM（规则执行）、NPC（人格一致性）、信息流（信息域隔离）
- 触发方式：每回合结束时 Core GM 推送事件日志
- 结果处理：持久化审计日志 + 违规警告通知 GM

**Player vs NPC 统一方式：** `BaseAgent` 抽象，差异封装在 `generate_action`（Human=输入解析，NPC=LLM生成）和 `filter_output`（Human=passthrough，NPC=LLM过滤）两个方法中。

**Demo 最小集合：** Core GM (LLM) + 2-3 NPC (LLM) + Player Proxy (非LLM) + Skill Pipeline (纯函数) = **3-4 个 LLM context**。Story Tracker 和 Audit Module 可暂时省略。

---

### LE（LLM 工程师）分析

**隔离方案：独立 LLM 调用（非共享 context）**
- 信息隔离是核心博弈机制，共享 context 下 LLM attention 机制无法保证信息隔离
- 每个 NPC 独立调用，信息域由代码层面硬隔离

**API 调用量估算（GPT-4o）：**

| 场景 | 调用次数 | 延迟（优化后） | 成本 |
|------|---------|--------------|------|
| 简单回合（单NPC对话） | 3-4 | 3-5s | ~$0.05 |
| 典型回合（2NPC + 1轮级联） | 4-6 | 4-7s | ~$0.07 |
| 复杂回合（3NPC + 2轮级联） | 6-8 | 6-10s | ~$0.10 |
| 完整一局（~20回合） | — | — | ~$1.5 |

**Context 预算分配：**
- Core GM：~5,000-9,000 token（角色定义 + 规则精简版 + 场景 + 状态快照 + 历史摘要）
- NPC Agent：~2,000-4,000 token（人格定义 + 信息域 + 对话历史）
- Audit Module：~1,500-2,600 token
- 远低于 GPT-4o 128k 上限，但建议控制在 40k-60k 有效区间内

**LE 与 SA 的分歧点 — Story Tracker 拆分：**
> LE 建议将 Story Tracker **合并到 Core GM 的 system prompt 中**，而非独立服务。理由：减少系统复杂性，Story Tracker 功能可以用 GM system prompt 中的状态段落承载。

**Prompt 清单（宏观）：**

| Prompt | 作用 | 输入 | 输出 | 频率 |
|--------|------|------|------|------|
| **GM-Action-Evaluate** | 解析玩家行动，判定影响范围 | 玩家输入, 场景状态, NPC位置 | 行动类型, 目标NPC, 检定需求 | 每回合1次 |
| **NPC-React** | NPC 对事件做出回应 | 人格定义, 信息域, 对话历史, 当前事件 | 内部推理 + 外部回应 + 信息域变更 | 每受影响NPC 1次 |
| **GM-Narrative** | 整合本回合事件为玩家可见叙事 | 所有NPC回应, 检定结果, 状态变更 | 玩家视角叙事 + 行动提示 | 每回合1次 |
| **NPC-Cascade** | 级联传播中NPC对其他NPC的反应 | 同NPC-React，输入来自其他NPC | 同NPC-React | 级联发生时 |
| **GM-Butterfly** | 判定蝴蝶效应 | 行动, 世界状态, 暗线触发条件 | 是否触发 + 具体影响 | 条件触发 |
| **Audit-Check** | 审计规则执行和一致性 | 本回合所有I/O | 违规清单 + 严重度 | 每回合（异步） |
| **Memory-Compress** | 压缩对话历史 | 最近N回合完整对话 | 结构化摘要 | 每3-5回合 |

**可用代码替代的（不需要LLM）：** D20骰子计算、级联收敛判定、Layer 2 信息过滤查表、信念侵蚀等级更新。

**核心风险（按严重度排序）：**
1. 🔴 NPC "讨好玩家"倾向（RLHF偏向，系统性问题）
2. 🔴 信息隔离依赖代码正确性（context管理bug = 隔离失败）
3. 🟡 凡神反比的LLM执行一致性差
4. 🟡 级联传播中多NPC叙事连贯性问题

---

### GD（游戏设计师）评估

**P1-P8 架构支撑评估：**

| 原则 | 评级 | 关键缺口 |
|------|------|---------|
| P1 被忽视者的主场 | ★★★☆☆ | 缺「身份→可用行动空间」权限映射 |
| P2 多元生存博弈 | ★★☆☆☆ | 场景 schema 无 `survival_dimension` 必填字段 |
| P3 道德重量 | ★★★☆☆ | 缺代价兑现追踪（蜜罐选项的延迟后果） |
| P4 理想与枷锁 | ★★★★☆ | 仅需命名清晰化（`ideal` / `chain` 字段） |
| P5 暗线隐晦 | ★★★☆☆ | 缺暗线可见性控制、心性闭合评估 |
| P6 涟漪而非巨浪 | ★★★☆☆ | 缺主线不可变的硬约束（`fixed_outcomes`） |
| P7 发现感 | ★★★☆☆ | 缺隐藏信息注册机制（`hidden_info[]`） |
| P8 无力感与微光 | ★★☆☆☆ | 缺情绪节拍追踪、微光时刻保障 |

**GD 关键提议 — Story Tracker 升级为「叙事导演 (Narrative Director)」：**
> Story Tracker 不应该只是被动记录器。它应该承担：
> - 情绪节拍追踪（`current_beat`: 紧张/喘息/发现/抉择/余波）
> - 慰藉时刻触发（`tension_level` 超阈值时向 GM 发 `comfort_needed` 信号）
> - 暗线触发条件评估
> - 弹性回合建议
> **这与 SA 的"Story Tracker 被动"提案直接冲突。**

**GD 的 NPC 人格表达层提议：**
每个 NPC 需增加：
- `voice`（语言风格）— 粗犷/文绉绉/阴阳怪气/沉默寡言
- `tell`（破绽）— 紧张/说谎时的行为特征
- `emotional_state`（动态情绪）— 随事件变化
- `irrationality_factor`（非理性因子）— 偏离最优策略的概率

**GD 最大体验风险判定：**
> 🔴 **"NPC 感觉像 NPC"** — 如果玩家感觉所有NPC都是同一个AI在扮演不同角色，整个信息不对称博弈设计就失败了。这是致命风险。

**GD 关于级联传播等待时间的建议：**
- 流式叙事：传播进行中给玩家发环境描写/氛围文字
- 时间预算（最大 T 秒而非最大 K 轮）
- 异步传播：部分结果延迟到下一回合兑现

---

### AA（对抗审计师）审计

**发现 13 个问题，其中 6 个 Critical：**

| # | 问题 | 等级 | 缓解建议 |
|---|------|------|---------|
| 1.1 | Core GM / Story Tracker **写入权冲突** — "更新世界状态"和"追踪叙事状态"语义重叠 | 🔴 | Story Tracker 只读追踪，所有写入归 Core GM |
| 1.2 | 叙事推进决策权模糊 — Story Tracker 是追踪器还是决策者？ | 🟡 | 明确为顾问角色，GM 有最终决定权 |
| 1.3 | **Audit 否决后无限循环** — GM 重试仍不通过怎么办？ | 🔴 | 最多重试2次，之后用模板化安全响应 fallback |
| 2.1 | **Core GM 是全系统单点故障** — 任何GM异常导致游戏卡死 | 🔴 | 每个GM职责定义 fallback 行为 |
| 2.2 | Audit Module 故障时静默通过 | 🟡 | 超时放行 + 标记"未审计" + 连续N次未审计触发告警 |
| 3.1 | **NPC 间 LLM 信息泄露** — context 管理错误 = 隔离失败 | 🔴 | 调用前强制 context 内容校验 + GM Layer 2 输出检查 |
| 3.2 | GM 全知导致叙事泄露 | 🟡 | GM 叙事 prompt 中列出"玩家已知信息清单"作为边界 |
| 4.1 | Audit 独立性与知情权矛盾 — 审计依据来自审计对象 | 🟡 | Audit 维护独立的"预期状态"副本做比对 |
| 4.2 | 审计粒度与成本 — 全量审计成本翻倍 | 🟡 | 分层：实时规则化检查 + 关键节点 LLM 深度审计 |
| 5.1 | Human/NPC "共享系统"定义过宽 — 输入处理路径完全不同 | 🟡 | 重定义为"共享下游评估系统"，上游分 Human/Agent pipeline |
| 5.2 | **Prompt Injection** — 玩家输入嵌入NPC prompt导致指令注入 | 🔴 | 输入 sanitization + user content 块严格分离 + 对抗指令 |
| 6.1 | GM 判断级联收敛不可靠 | 🟡 | 增加确定性终止条件（状态变化低于阈值自动终止） |
| 6.2 | **传播链异常放大** — 一个NPC异常输出污染整条传播链 | 🔴 | 每个NPC输出进入下一个前做轻量格式/合理性校验 |

---

## 分歧点汇总

### 分歧 1: Story Tracker 的角色定位

| 立场 | 支持者 | 理由 |
|------|--------|------|
| **被动查询服务**（仅追踪，不决策） | SA, AA | 避免写入权冲突、职责清晰、可测试性强 |
| **合并到 GM system prompt** | LE | 减少系统复杂性、降低延迟 |
| **升级为叙事导演**（主动发信号给GM） | GD | 情绪节拍、慰藉时刻、暗线触发需要主动能力 |

**这是 Round 1 最大的分歧，需要 Human 决定方向。**

### 分歧 2: Demo 阶段是否需要 Audit Module

| 立场 | 支持者 | 理由 |
|------|--------|------|
| **暂时省略，人工审查** | SA | Demo 规模小，人眼可检查 |
| **需要轻量版**（至少做信息域隔离验证） | GD, AA | 信息泄露是致命风险，即使 demo 也不能放任 |

---

## 结论（已达成共识部分）

1. **Agent 清单确认**：Player Proxy + NPC Agent(×N) + Core GM + Story Tracker + Audit Module + Skill Pipeline
2. **NPC 必须独立 LLM context**：信息隔离是核心博弈机制，不可妥协
3. **Skill Pipeline 是纯函数模块**：D20、洞察值计算、Level 2 信息过滤查表均用代码实现
4. **Player/NPC 共享下游评估系统**：上游输入处理分 Human/Agent pipeline，下游（信息域、洞察值、骰子检定）统一
5. **Core GM 是中枢**：需要定义每个职责的 fallback 行为
6. **级联传播终止 = 确定性规则 + GM 辅助判断**：代码层面状态变化阈值 + 硬上限 K，GM 可提前终止但不是唯一判据
7. **NPC 人格建模需增加表达层**：voice / tell / emotional_state / irrationality_factor
8. **Prompt Injection 防御是必须的**：输入 sanitization + user content 块分离
9. **NPC 输出进入传播链前需轻量校验**：防止异常放大

## 未解决问题（需 Human 决定）

1. **Story Tracker 定位**：被动追踪器 vs 合并到 GM vs 叙事导演？
2. **Demo 是否包含 Audit Module**？
3. **Player Proxy 是否需要 LLM**（取决于 UI 是自由文本还是结构化选项）？
4. **Audit 否决后的处理策略**：重试+fallback 的具体参数？
5. **Skill Pipeline 的 Output Skill 是否需要 LLM**（纯格式化 vs 叙事润色）？
