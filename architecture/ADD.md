# 《Jump Jump》LangGraph Agent 架构设计文档 (ADD)

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Web Frontend Layer                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  React/Vue UI   │  │  WebSocket      │  │  State Manager  │             │
│  │  (Player View)  │  │  (Real-time)    │  │  (Zustand/Redux)│             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
└───────────┼────────────────────┼────────────────────┼──────────────────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Game Session Manager                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  - Session lifecycle (create/load/save)                             │   │
│  │  - Multi-session support                                            │   │
│  │  - Auto-save checkpoint system                                      │   │
│  │  - Player authentication (optional)                                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         LangGraph Core Engine                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ORCHESTRATOR GM (LLM Agent)                                        │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │    │
│  │  │  OGM-       │  │  OGM-       │  │  OGM-       │                 │    │
│  │  │  Evaluate   │  │  Adjudicate │  │  Synthesize │                 │    │
│  │  │  (每回合)    │  │  (BFS后)    │  │  (DFS后)    │                 │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                    ┌───────────────┼───────────────┐                        │
│                    ▼               ▼               ▼                        │
│  ┌─────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐       │
│  │   STATE ENGINE      │ │  STORY TRACKER  │ │  NARRATIVE DIRECTOR │       │
│  │   (Pure Code)       │ │  (Code + Rules) │ │   (LLM Agent)       │       │
│  │  ┌───────────────┐  │ │  ┌───────────┐  │ │  ┌───────────────┐  │       │
│  │  │Variable Ledger│  │ │  │Dark Thread│  │ │  │ ND-Render     │  │       │
│  │  │Dice Engine    │  │ │  │  State    │  │ │  │ ND-Closure    │  │       │
│  │  │Echo Trigger   │  │ │  │  Machine  │  │ │  │ ND-ThreadReveal│ │       │
│  │  │Faith Erosion  │  │ │  └───────────┘  │ │  └───────────────┘  │       │
│  │  └───────────────┘  │ └─────────────────┘ └─────────────────────┘       │
│  └─────────────────────┘                                                   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  DISPATCHER (Stateless, per-call)                                   │    │
│  │  - Prompt construction (no secret leakage)                          │    │
│  │  - NPC context isolation                                            │    │
│  │  - Output validation gate                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                          │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
┌─────────────────────────┐ ┌─────────────────────────┐ ┌─────────────────────┐
│   NPC AGENT POOL        │ │   NPC AGENT POOL        │ │   NPC AGENT POOL    │
│   (Active Layer)        │ │   (Background Layer)    │ │   (Dormant Layer)   │
│   ┌─────┐ ┌─────┐      │ │   ┌─────┐ ┌─────┐      │ │   ┌─────┐ ┌─────┐   │
│   │哪吒  │ │李靖 │      │ │   │百姓A│ │士兵B│      │ │   │其他 │ │其他 │   │
│   │Tool │ │Tool │      │ │   │L1   │ │L1   │      │ │   │State│ │State│   │
│   └─────┘ └─────┘      │ │   └─────┘ └─────┘      │ │   └─────┘ └─────┘   │
│   Max 4 concurrent      │ │   Max 10, mixed L0/L1   │ │   State cards only  │
└─────────────────────────┘ └─────────────────────────┘ └─────────────────────┘
```

## 2. 核心设计原则

### 2.1 NPC as Tool
- 每个 NPC 是一个 LangChain Tool
- **双层输出**: Observable (对外) + Hidden Intent (对内)
- **信息隔离**: Hidden 层绝不跨越 NPC 边界
- **结构化通信**: NPC 间只传递结构化数据，不传自然语言原文

### 2.2 洞察力系统 (简化版)
- **无 D20 检定**、无修正值
- **每场景固定配额**: 2×「真实目的」+ 2×「幕后对话」
- **Per-query 消耗**: 每次使用针对一个具体 player query

### 2.3 LangGraph 工作流
- Phase 0: GM 解析玩家行动
- Phase 0.5: 后台社会 Tick
- Phase 1: BFS - NPC 并行反应
- Phase 2: GM 裁决
- Phase 3: DFS - 递归执行
- Phase 4: GM 终局
- Phase 5: NPC 层级迁移
- Narrative Render: 生成玩家叙事

### 2.4 硬性限制
- Active NPC 上限: 4
- Background NPC 上限: 10
- DFS 最大深度: 3
- 单回合总 NPC 调用: 12
- 同一对 NPC 往返上限: 2
- 每回合 L2 后台 LLM: 2

## 3. 与现有设计的对齐

| 设计资产 | 架构实现 |
|---------|---------|
| GM 4-module split | Orchestrator GM + State Engine + Story Tracker + Narrative Director |
| NPC as Tool | NPCTool 基类 + Dispatcher 模式 |
| 三层 NPC 激活 | Active/Background/Dormant layers |
| 双层输出 | ObservableOutput + HiddenIntent |
| 简化洞察系统 | InsightManager with per-scene quota |
| 38 变量系统 | variables: Dict[str, Any] |
| 37 回响系统 | echoes_triggered + echoes_pending |

## 4. 技术栈

- **LangGraph**: 状态机编排
- **LangChain**: Tool 抽象和 LLM 调用
- **Pydantic**: 结构化输出验证
- **aiosqlite**: 状态持久化
- **FastAPI**: Web API
- **WebSocket**: 实时叙事推送
