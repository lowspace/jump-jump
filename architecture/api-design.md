# 《Jump Jump》Web API 设计

## Base URL
- Development: `http://localhost:8000/api`
- Production: `https://api.jumpjump.game/v1`

## Authentication
Session-based (no login required for gameplay). Session ID in URL path.

## Endpoints

### POST /game/start
开始新游戏或继续存档。

**Request:**
```json
{
  "resume_session_id": null
}
```

**Response:**
```json
{
  "session_id": "string",
  "current_scene": "scene-0-wuzhishan",
  "current_phase": "opening",
  "narrative_text": "string",
  "available_actions": [
    {
      "type": "dialogue|move|observe|decision",
      "target": "string|null",
      "description": "string"
    }
  ],
  "insight_quota": {
    "true_purpose": 2,
    "behind_dialogue": 2
  },
  "player_state": {
    "role": "string",
    "faith_erosion_level": 0
  }
}
```

### POST /game/{session_id}/action
提交玩家行动。

**Request:**
```json
{
  "action_type": "dialogue|decision|move|observe",
  "target": "string|null",
  "content": "string"
}
```

**Response:**
```json
{
  "narrative_text": "string",
  "emotion_beat": "string",
  "turn_completed": true,
  "current_phase": "string",
  "phase_changed": false,
  "available_actions": [],
  "behind_scenes_reveals": [
    {
      "type": "variable_change|npc_intent|echo_preview",
      "content": "string",
      "priority": 5
    }
  ],
  "insight_quota_remaining": {
    "true_purpose": 2,
    "behind_dialogue": 2
  },
  "pending_decision": {
    "decision_id": "string",
    "description": "string",
    "choices": [
      {
        "id": "string",
        "text": "string",
        "preview_hint": "string|null"
      }
    ]
  },
  "scene_complete": false,
  "scene_summary": null
}
```

### POST /game/{session_id}/insight
使用洞察力。

**Request:**
```json
{
  "insight_type": "true_purpose|behind_dialogue",
  "target": "string"
}
```

**Response:**
```json
{
  "success": true,
  "revealed_content": {
    "type": "true_purpose|behind_dialogue",
    "npc_id": "string",
    "true_intent": "string",
    "reasoning": ["string"]
  },
  "quota_remaining": {
    "true_purpose": 2,
    "behind_dialogue": 2
  }
}
```

### GET /game/{session_id}/state
获取当前游戏状态。

**Response:**
```json
{
  "session_id": "string",
  "current_scene": "string",
  "current_phase": "string",
  "turn_count": 0,
  "player_role": "string",
  "faith_erosion_level": 0,
  "insight_quota": {
    "true_purpose": 2,
    "behind_dialogue": 2
  },
  "variables_snapshot": {},
  "echoes_triggered": [],
  "active_npcs": [],
  "current_dialogue_context": []
}
```

## WebSocket Events

**Connection:** `ws://api.jumpjump.game/ws/{session_id}`

### Client -> Server
```json
{ "type": "action", "payload": {...} }
{ "type": "insight", "payload": {...} }
```

### Server -> Client
```json
{
  "type": "narrative",
  "payload": {
    "text": "string",
    "emotion_beat": "string",
    "typing_effect": true
  }
}

{
  "type": "reveal",
  "payload": {
    "reveals": [],
    "requires_ack": true
  }
}

{
  "type": "decision_prompt",
  "payload": {...}
}

{
  "type": "scene_transition",
  "payload": {
    "from": "string",
    "to": "string",
    "transition_text": "string"
  }
}
```
