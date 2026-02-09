# Jump Jump - 悟空传 Web 游戏

基于《悟空传》的 Web 文字探险游戏，采用 FastAPI + LangGraph 架构。

## 项目结构

```
/src
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── game_engine.py       # LangGraph 游戏引擎
│   │   ├── npc_agents.py        # NPC Tool 实现
│   │   ├── insight_system.py    # 洞察力系统
│   │   ├── state_manager.py     # 状态管理
│   │   └── ws_handler.py        # WebSocket 处理
│   ├── core/
│   │   ├── state_schema.py      # 状态定义
│   │   └── config.py            # 配置
│   └── data/
│       ├── npcs/                # NPC 配置 (YAML)
│       ├── decisions/           # 决策配置 (YAML)
│       └── loaders.py           # 数据加载器
├── frontend/
│   ├── index.html
│   ├── app.js                   # 主应用逻辑
│   ├── gameUI.js                # 游戏界面
│   └── styles.css               # 样式
├── tests/                       # 测试套件
└── requirements.txt             # 依赖
```

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+ (可选，用于前端开发服务器)

### 安装依赖

```bash
cd /src
pip install -r requirements.txt
```

### 运行后端

```bash
cd /src
python -m backend.app.main
```

或使用 uvicorn 直接运行：

```bash
cd /src
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 运行前端

前端是静态 HTML/JS，可以直接在浏览器打开 `frontend/index.html`，或使用任意静态文件服务器：

```bash
cd /src/frontend
python -m http.server 8080
```

然后访问 http://localhost:8080

### 访问 API 文档

启动后端后，访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### REST API

| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | API 信息 |
| `/health` | GET | 健康检查 |
| `/api/game/start` | POST | 开始新游戏 |
| `/api/game/{session_id}/state` | GET | 获取游戏状态 |
| `/api/game/{session_id}/action` | POST | 提交玩家行动 |
| `/api/game/{session_id}/insight` | POST | 使用洞察力 |

### WebSocket

| 端点 | 描述 |
|------|------|
| `/ws/{session_id}` | 实时游戏通信 |

## 游戏机制

### 洞察力系统

- 每场景固定配额：2×「真实目的」+ 2×「幕后对话」
- 无 D20 检定，无修正值
- 未使用洞察 → 场景结束时获得完整回顾
- 已使用洞察 → 仅游戏结束时解锁完整回顾

### NPC 系统

- NPC as Tool 模式
- 双层输出：Observable (对外) + Hidden Intent (对内)
- 三层激活：Active (4个) / Background (10个) / Dormant

### 场景流程

1. Scene 0: 五指山 (倒叙起点)
2. Scene 1: 陈塘关
3. Scene 2: 天河
4. Scene 3: 花果山
5. Scene 4: 灵台方寸山
6. Scene 0: 五指山 (重新渲染，影响力报告)

## 测试

```bash
cd /src
pytest tests/ -v
```

## Docker 部署

### 构建镜像

```bash
cd /src
docker build -t jump-jump .
```

### 运行容器

```bash
docker run -p 8000:8000 jump-jump
```

### 使用 Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./data:/app/data
```

## 配置

### 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `OPENAI_API_KEY` | OpenAI API 密钥 | None |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | None |
| `DB_PATH` | SQLite 数据库路径 | ./data/game_sessions.db |
| `PORT` | 服务器端口 | 8000 |
| `DEBUG` | 调试模式 | True |

### 游戏配置

修改 `backend/core/config.py` 中的 `GameConfig` 类：

- `MAX_ACTIVE_NPCS`: 最大激活 NPC 数 (默认: 4)
- `MAX_DFS_DEPTH`: DFS 最大深度 (默认: 3)
- `INSIGHT_TRUE_PURPOSE_QUOTA`: 真实目的配额 (默认: 2)
- `INSIGHT_BEHIND_DIALOGUE_QUOTA`: 幕后对话配额 (默认: 2)

## 开发

### 添加新 NPC

1. 在 `backend/data/npcs/` 创建 YAML 文件
2. 参考现有配置格式 (如 `nezha.yaml`)
3. 定义对话节点、隐藏意图、洞察触发点

### 添加新决策

1. 在 `backend/data/decisions/` 创建 YAML 文件
2. 定义选择、变量影响、回响预告

### 扩展游戏引擎

游戏引擎使用 LangGraph 实现 5 阶段流程：

1. Phase 0: GM Evaluate
2. Phase 1: BFS (NPC 并行反应)
3. Phase 2: GM Arbitrate
4. Phase 3: DFS (递归执行)
5. Phase 4: GM Finalize
6. Phase 5: NPC Layer Migration

在 `backend/app/game_engine.py` 中修改 `_process_*` 方法。

## 技术栈

- **Backend**: Python, FastAPI, WebSocket
- **Game Engine**: LangGraph (预留接口)
- **State**: SQLite (aiosqlite)
- **Frontend**: Vanilla JavaScript, CSS3
- **Data**: YAML

## 设计文档

详细设计文档位于项目根目录：
- `/tech-specs/`: Scene Team 输出
- `/architecture/`: Architecture Team 输出
- `/.claude/plans/`: 设计规划文档

## License

MIT License
