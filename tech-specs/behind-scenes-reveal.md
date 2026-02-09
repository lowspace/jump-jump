# 背后博弈展示系统技术规格

> 本文档定义《Jump Jump》"背后博弈"展示系统的完整技术规格，包括何时、如何向玩家展示变量变化和隐藏机制。
> 基于设计文档：`agent-arch-round3.md` 及相关场景设计

---

## 1. 系统概述

### 1.1 核心概念

"背后博弈"是指玩家不可直接观察到的变量变化、NPC隐藏意图、世界状态改变。这些变化需要通过特定时机和方式展示给玩家，以创造"恍然大悟"的体验。

### 1.2 展示原则

1. **延迟揭示**：变量变化不立即展示，而是在特定节点汇总展示
2. **回响提示**：通过"echo_preview"暗示未来影响
3. **程度弹性**：同一选择在不同条件下呈现不同强度
4. **闭环验证**：Scene 0重新渲染时验证所有选择的回响

---

## 2. 展示触发点

### 2.1 触发类型

| 触发类型 | 触发时机 | 展示内容 | 示例 |
|----------|----------|----------|------|
| `decision_made` | 决策确认后 | echo_preview | "这个选择将在未来回响..." |
| `phase_end` | 阶段结束时 | 该阶段变量变化 | "哪吒对你的信任：0 → 2" |
| `scene_end` | 场景结束时 | 场景变量汇总 | 场景debrief |
| `echo_triggered` | 回响触发时 | 跨场景影响 | Scene 2中Scene 1的闪回 |
| `insight_used` | 使用洞察时 | 隐藏层揭示 | NPC真实意图 |

### 2.2 触发点详细列表

#### Scene 1 - 陈塘关

| 触发点 | 类型 | 展示内容 | 格式 |
|--------|------|----------|------|
| Decision A 选择后 | decision_made | echo_preview | "这个选择将在未来回响..." |
| Decision B 选择后 | decision_made | 变量变化 | "武师在场度：无 → 高" |
| Decision C 选择后 | decision_made | echo_preview | "这个物件将在未来回响..." |
| 阶段2结束 | phase_end | 信任度变化 | "哪吒对你的信任：{old} → {new}" |
| 阶段3结束 | phase_end | 李靖犹豫度 | "李靖犹豫度：{value}" |
| 阶段5结束 | phase_end | 护腕去向 | "护腕：{location}" |
| 场景结束 | scene_end | 全部变量汇总 | 完整debrief |
| 杨戬触发 | echo_triggered | 条件达成 | "有心窍的人..." |

#### Scene 2 - 天河

| 触发点 | 类型 | 展示内容 | 格式 |
|--------|------|----------|------|
| Decision A 选择后 | decision_made | 信息获取度 | "灵山秘密：{level}" |
| Decision B 选择后 | decision_made | 怀疑度变化 | "卷帘大将怀疑度：{old} → {new}" |
| Decision C 选择后 | decision_made | echo_preview | "这片碎甲将在未来回响..." |
| Decision D 命运检定后 | decision_made | 生存方式 | "生存方式：{method}" |
| 阶段2结束 | phase_end | 第七窍觉醒度 | "第七窍：{level}" |
| 阶段5结束 | phase_end | 账本处置 | "账本选择：{choice}" |
| 场景结束 | scene_end | 全部变量汇总 | 完整debrief |
| 天蓬坠落时 | echo_triggered | 闪回触发 | "有心窍的人活着更难" |

#### Scene 3 - 花果山

| 触发点 | 类型 | 展示内容 | 格式 |
|--------|------|----------|------|
| Decision A 选择后 | decision_made | 猴群立场 | "猴群倾向：{direction}" |
| Decision B 选择后 | decision_made | 桃树命运 | "桃树：{fate}" |
| Decision C 选择后 | decision_made | 记忆方式 | "记忆传承：{method}" |
| Decision D 选择后 | decision_made | 石卵去留 | "石卵选择：{choice}" |
| 阶段3结束 | phase_end | 猴群团结度 | "猴群团结度：{level}" |
| 阶段4结束 | phase_end | 桃树状态 | "桃树状态：{status}" |
| 阶段6结束 | phase_end | 记忆存续 | "齐天大圣记忆：{status}" |
| 场景结束 | scene_end | 全部变量汇总 | 完整debrief |
| 紫霞出现时 | echo_triggered | 条件触发 | "有人在找大王" |

#### Scene 4 - 灵台

| 触发点 | 类型 | 展示内容 | 格式 |
|--------|------|----------|------|
| Decision A 选择后 | decision_made | 发现方式 | "发现方式：{method}" |
| Decision B 选择后 | decision_made | 监院态度 | "监院态度：{attitude}" |
| Decision D 选择后 | decision_made | echo_preview | "这支笔将在未来回响..." |
| 阶段2结束 | phase_end | 慧空关系 | "与慧空关系：{level}" |
| 阶段3结束 | phase_end | 调查进度 | "无字真经认知：{level}" |
| 阶段6结束 | phase_end | 信仰状态 | "信仰状态：{state}" |
| 场景结束 | scene_end | 全部变量汇总 | 完整debrief |
| 唐僧出现时 | echo_triggered | 微光触发 | "有人在走没有路的路" |

#### Scene 0 - 五指山

| 触发点 | 类型 | 展示内容 | 格式 |
|--------|------|----------|------|
| Decision A 选择后 | decision_made | 好奇心变化 | "好奇心：{old} → {new}" |
| Decision B 选择后 | decision_made | 感知度变化 | "对山的感知：{level}" |
| Decision C 选择后 | decision_made | echo_preview | "这个行为将在未来回响..." |
| 阶段1结束 | phase_end | 发现汇总 | "发现物品：{items}" |
| 阶段2结束 | phase_end | 故事收集 | "听过的故事：{count}/4" |
| 行者触发 | echo_triggered | 条件达成 | "有人向西行" |
| 场景结束 | scene_end | 基础变量汇总 | 首次游玩debrief |
| **重新渲染** | special | 全部回响验证 | 基于Scene 1-4变量的完整重渲染 |

---

## 3. 展示格式规范

### 3.1 变量变化格式

```yaml
variable_change_display:
  format: "{variable_name}：{old_value} → {new_value}"
  optional_context: "{explanation}"

examples:
  - "哪吒对你的信任：0 → 2"
  - "李靖犹豫度：低 → 高（他在当众否认时有明显停顿）"
  - "卷帘大将怀疑度：0 → 3（你被标记为待复查对象）"
```

### 3.2 Echo Preview格式

```yaml
echo_preview_display:
  format: "这个{choice_type}将在未来回响..."
  hint_level: subtle | moderate | strong

examples:
  subtle: "这个物件将在未来回响..."
  moderate: "这个护腕将在某个关键时刻出现..."
  strong: "Scene 3中，你会在水帘洞深处发现这个护腕的碎片..."
```

### 3.3 回响触发格式

```yaml
echo_trigger_display:
  format: |
    【回响】
    {source_scene}的记忆浮现...
    {echo_content}
    {mechanical_effect_if_any}

examples:
  - |
    【回响】
    陈塘关的记忆浮现...
    "有心窍的人，在这个世界活着比没有心窍的更难。"
    本场景所有洞察检定+1
  - |
    【回响】
    花果山的记忆浮现...
    你梦见一个人站在另一个人旁边，始终没有走。
    你的选择更加从容。
```

### 3.4 隐藏层揭示格式

```yaml
hidden_layer_display:
  format: |
    【洞察】{insight_type}
    {reveal_content}

    幕后：{behind_the_scenes}

examples:
  - |
    【洞察】真实目的
    哪吒内心其实渴望被阻止。

    幕后：他的愤怒是恐惧的盔甲。在最后一刻，他只需要确认"有一个人在看着我"。
  - |
    【洞察】幕后对话
    卷帘大将知道天蓬和阿月的事很久了。

    幕后：他的"延迟上报"是他职业生涯唯一一次偏离标准流程的行为。
```

---

## 4. 程度弹性系统

### 4.1 弹性变量定义

```yaml
degree_elasticity:
  variable: wushi_presence  # 武师在场度
  levels:
    - value: 高
      conditions:
        - "player_chose_B1_rush_stop"
      narrative: "你在最后一刻冲了上去。哪吒看到了你。"
      echo_strength: strong
    - value: 中
      conditions:
        - "player_chose_B2_stand_watch"
      narrative: "你站在那里，没有走。哪吒知道你在。"
      echo_strength: moderate
    - value: 低
      conditions:
        - "player_chose_B3_turn_leave"
      narrative: "你离开了。哪吒没有看到你。"
      echo_strength: subtle
```

### 4.2 弹性展示逻辑

```python
def display_with_elasticity(variable, conditions):
    """
    根据条件确定变量的具体展示形式
    """
    level = determine_level(variable, conditions)

    # 基础变化展示
    display = f"{variable.name}：{variable.old_value} → {level.value}"

    # 添加上下文描述
    if level.narrative:
        display += f"\n{level.narrative}"

    # 添加回响提示
    if level.echo_strength == "strong":
        display += "\n【强回响】这个选择将在多个场景中产生深远影响。"
    elif level.echo_strength == "moderate":
        display += "\n【中度回响】这个选择将在未来某个时刻回响。"

    return display
```

---

## 5. Scene 0 重新渲染系统

### 5.1 重新渲染触发条件

```yaml
rerender_trigger:
  condition: "完成Scene 1-4后返回Scene 0"
  mode: "影响力报告的一部分"
  purpose: "验证所有选择的回响，创造情感闭环"
```

### 5.2 重新渲染变量映射

| Scene 0 元素 | 源变量 | 影响方式 |
|--------------|--------|----------|
| 桃树状态 | peach_tree_fate | 保留=活着的小桃树，砍掉=烧焦残根 |
| 石壁字迹清晰度 | memory_kept | 铭记=更清晰，遗忘=更模糊 |
| 祖母故事内容 | 多个变量 | 根据变量值调整故事细节 |
| 行者出现 | tangseng_encounter | 遇见=行者更坚定，未遇=无行者 |
| 山体震动频率 | wukong_awareness | 意识到=更频繁，不知道=无震动 |
| 月亮亮度 | tenpeng_last_words | 听到=月亮特别亮 |
| 风中声音 | knife_choice | 父刀=金属碰撞，师刀=模糊人声 |
| 废墟细节 | armguard | 留下=看到布带，带走=无 |

### 5.3 重新渲染展示格式

```yaml
rerender_display:
  introduction: |
    你再次站在五指山上。
    但这一次，你看到的不再是第一次的样子。
    你之前的选择，在这里留下了痕迹...

  element_changes:
    - element: "烧焦的桃树残根"
      condition: "peach_tree_fate = 保留"
      new_description: "那株烧焦的桃树残根旁，竟然冒出了一株新芽。很瘦，很矮，但确实活着。"

    - element: "石壁字迹"
      condition: "memory_kept = 铭记"
      new_description: "那四个字的刻痕比记忆中清晰了许多，像是有人在保护它们不被风化。"

    - element: "祖母的故事"
      condition: "grandmother_stories = 4"
      new_description: "祖母讲完故事后，轻声说：'这些故事啊……有时候我觉得这些故事比我的命还真。'"

  conclusion: |
    你终于明白了。
    那些你以为是独立的故事——
    陈塘关的孩子、天上看月亮的将军、花果山的猴子、说经书没字的和尚——
    他们都是真实存在的。
    而你，以某种方式，参与了他们的故事。
```

---

## 6. 技术实现接口

### 6.1 变量变化记录

```yaml
variable_change_log:
  entry:
    timestamp: datetime
    scene_id: string
    phase_id: string
    decision_id: string
    variable: string
    old_value: any
    new_value: any
    reason: string  # 触发原因
    display_trigger: "immediate" | "phase_end" | "scene_end"
```

### 6.2 回响触发检查

```yaml
echo_trigger_check:
  input:
    current_scene: string
    current_phase: string
    player_variables: map
    completed_scenes: [string]

  output:
    echoes_to_trigger: [{
      source_scene: string,
      source_variable: string,
      echo_content: string,
      display_format: string
    }]
```

### 6.3 展示API

```yaml
# 获取变量变化展示
GET /api/behind-scenes/variable-changes
Request: { scene_id, phase_id, player_state }
Response: {
  changes: [{
    variable: string,
    old_value: any,
    new_value: any,
    display_text: string
  }]
}

# 获取echo preview
GET /api/behind-scenes/echo-preview
Request: { decision_id, player_state }
Response: {
  preview_text: string,
  hint_level: string
}

# 获取回响触发
GET /api/behind-scenes/echoes
Request: { scene_id, phase_id, player_state }
Response: {
  echoes: [{
    source: string,
    content: string,
    mechanical_effect: string | null
  }]
}

# 获取Scene 0重新渲染
GET /api/behind-scenes/rerender
Request: { player_complete_state }
Response: {
  element_changes: [{
    element: string,
    original_description: string,
    rerendered_description: string,
    source_variable: string
  }],
  full_narrative: string
}
```

---

## 7. 与Architecture Team的交接要点

### 7.1 状态管理要求

1. **变量变化必须实时记录**，但展示时机由本规格控制
2. **回响触发检查**需要在每个phase开始时执行
3. **Scene 0重新渲染**需要访问所有Scene 1-4的变量

### 7.2 展示时机控制

1. `decision_made`：玩家确认选择后立即显示
2. `phase_end`：阶段叙事结束后，进入下一阶段前显示
3. `scene_end`：场景完全结束后显示
4. `echo_triggered`：在叙事中自然融入

### 7.3 性能考虑

1. 变量变化日志需要持久化存储
2. 回响触发检查可以缓存结果
3. Scene 0重新渲染可以预计算关键元素

---

## 8. 设计验证清单

### 8.1 P6原则验证

- [x] 每个核心选择都有明确的变量记录
- [x] 变量变化在Scene 0重新渲染中有体现
- [x] 小选择（护腕、碎甲、笔）也有回响
- [x] 桃树移植到五指山是终极涟漪

### 8.2 凡神反比验证

- [x] 凡人选择影响神/英雄的命运呈现
- [x] 哪吒莲藕重塑后的记忆残留受武师影响
- [x] 悟空被压状态下的感知受少年影响

### 8.3 信念侵蚀验证

- [x] 信息获取影响faith_state
- [x] 信息越多，盲目信仰越弱
- [x] 最终选择反映真实信念质量
