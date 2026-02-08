# 场景依赖图

> 本文档描述《Jump Jump》5 个场景之间的变量依赖关系。
> "写入方"指变量的产出场景，"读取方"指消费该变量的场景。
> Scene 0 比较特殊：它既产出自己的 6 个变量（流向影响力报告），又作为"重新渲染"的接收端读取所有 Scene 1-4 的变量。
> 数据来源：`scene-0-wuzhishan.md`、`scene-1-chentangguan.md`、`scene-2-tianhe.md`、`scene-3-huaguoshan.md`、`scene-4-lingtai.md`。

---

## 文本描述

```
Scene 1（陈塘关·骨与莲）— 无入站依赖
  ├──→ Scene 0: knife_choice, nezha_trust, wushi_presence, lijing_hesitation, armguard
  ├──→ Scene 2: yangjian_triggered, player_philosophy
  ├──→ Scene 3: wushi_presence, armguard
  └──→ Scene 4: knife_choice

Scene 2（天河·坠落之前）— 入站依赖：Scene 1
  ├──→ Scene 0: tenpeng_last_words, ledger_choice, marshal_memory(派生), moon_response(派生), clerk_choice(派生)
  ├──→ Scene 3: ledger_choice
  └──→ Scene 4: seventh_aperture_awareness

Scene 3（花果山·最后的桃）— 入站依赖：Scene 1, Scene 2
  ├──→ Scene 0: peach_tree_fate, memory_kept, monkey_unity(→monkey_survivors), huaguoshan_fire(派生)
  └──→ Scene 4: peach_tree_fate, memory_kept

Scene 4（灵台·空经）— 入站依赖：Scene 1, Scene 2, Scene 3
  └──→ Scene 0: final_scroll, faith_state(→faming_faith), sutra_truth(→scripture_truth), tangseng_encounter(→traveler_destination)

Scene 0（五指山·尘埃）— 纯接收端（重新渲染）
  入站依赖：Scene 1, Scene 2, Scene 3, Scene 4（全部）
  出站：仅流向影响力报告（wall_inscription, mountain_voice, final_act, grandmother_stories, curiosity_level, wukong_awareness）
```

---

## 依赖矩阵

### 写入 → 读取方向

| 写入方 ↓ / 读取方 → | Scene 0 | Scene 1 | Scene 2 | Scene 3 | Scene 4 | 影响力报告 |
|---------------------|---------|---------|---------|---------|---------|-----------|
| **Scene 0** | — | — | — | — | — | wall_inscription, mountain_voice, final_act, grandmother_stories, curiosity_level, wukong_awareness |
| **Scene 1** | knife_choice, nezha_trust, wushi_presence, lijing_hesitation, armguard | — | yangjian_triggered, player_philosophy | wushi_presence, armguard | knife_choice | nezha_trust, knife_choice, wushi_presence, lijing_hesitation, armguard, yangjian_triggered, crowd_attitude, player_philosophy |
| **Scene 2** | tenpeng_last_words, ledger_choice + 派生变量 | — | — | ledger_choice | seventh_aperture_awareness | ledger_choice, tenpeng_last_words, juanlian_suspicion, seventh_aperture_awareness, lingshan_secret, survival_method, tenpeng_fragment, scene2_philosophy |
| **Scene 3** | peach_tree_fate, memory_kept, monkey_unity + 派生变量 | — | — | — | peach_tree_fate, memory_kept | peach_tree_fate, monkey_unity, wukong_stick, zixia_encounter, resistance_choice, memory_kept, iron_head_fate, old_monkey_trust |
| **Scene 4** | final_scroll, faith_state, sutra_truth, tangseng_encounter + 派生变量 | — | — | — | — | sutra_truth, final_scroll, tangseng_encounter, huikong_relationship, faith_state, monastery_fate, faith_erosion_depth, pen_taken |

### 简化矩阵（✓ = 有依赖）

| 写入方 ↓ / 读取方 → | Scene 0 | Scene 1 | Scene 2 | Scene 3 | Scene 4 |
|---------------------|---------|---------|---------|---------|---------|
| **Scene 0** | — | — | — | — | — |
| **Scene 1** | ✓ | — | ✓ | ✓ | ✓ |
| **Scene 2** | ✓ | — | — | ✓ | ✓ |
| **Scene 3** | ✓ | — | — | — | ✓ |
| **Scene 4** | ✓ | — | — | — | — |

---

## 依赖链深度

场景的游玩顺序（按时间线）为 Scene 1 → Scene 2 → Scene 3 → Scene 4，Scene 0 在游玩时是序章（首次游玩使用默认值），在影响力报告中被重新渲染。

```
依赖链：

Scene 1（独立源头，无入站依赖）
   │
   ├───────────────────────────────┐
   ↓                               ↓
Scene 2                          Scene 3 ←── Scene 2
   │                               │
   ├───────────────────────────────┤
   ↓                               ↓
Scene 4 ←── Scene 1, Scene 2, Scene 3
   │
   ↓
Scene 0 ←── Scene 1, Scene 2, Scene 3, Scene 4（全汇入，重新渲染）
   │
   ↓
影响力报告 ←── Scene 0 + Scene 1-4 全部变量
```

---

## 各场景入站变量详细列表

### Scene 0 入站（重新渲染读取）

| 来源 | 变量 | 渲染效果概要 |
|------|------|------------|
| Scene 1 | `knife_choice` | 风中声音细节 |
| Scene 1 | `nezha_trust` | 桃树残根旁布带碎片 |
| Scene 1 | `wushi_presence` | 岩壁额外刻痕 |
| Scene 1 | `lijing_hesitation` | 祖母故事一额外台词 |
| Scene 1 | `armguard` | 废墟中布带细节 |
| Scene 2 | `tenpeng_last_words` | 祖母故事二额外台词 |
| Scene 2 | `ledger_choice` 派生 | 村中议论 / 月亮亮度 / 光滑石头 |
| Scene 3 | `peach_tree_fate` | 桃树存活状态 |
| Scene 3 | `memory_kept` | 字迹清晰度 + DC 修正 |
| Scene 3 | `monkey_unity` 派生 | 山上是否有猴子 |
| Scene 4 | `final_scroll` | 少年是否发现折叠纸条 |
| Scene 4 | `faith_state` | 祖母故事四语气 |
| Scene 4 | `sutra_truth` | 岩石纹路"空"字 |
| Scene 4 | `tangseng_encounter` 派生 | 行者脚步坚定度 |
| 综合 | 4 场景核心选择倾向 | 好奇心基础值 / 叙述语气 |
| 综合 | 杨戬全触发 | 黑狗彩蛋 |
| 综合 | `grandmother_stories` = 4 + 全完成 | 祖母额外长台词 |

### Scene 2 入站

| 来源 | 变量 | 影响 |
|------|------|------|
| Scene 1 | `yangjian_triggered` | 天河边闪回"有心窍的人活着更难" + 全场洞察 +1 |
| Scene 1 | `player_philosophy` | 冲动/坚守/回避三种闪回 + 对应检定修正 |

### Scene 3 入站

| 来源 | 变量 | 影响 |
|------|------|------|
| Scene 1 | `wushi_presence` | 石卵梦境（"在旁边看着"的意义） |
| Scene 1 | `armguard` | 水帘洞额外发现（布料绑带） |
| Scene 2 | `ledger_choice` | 天兵巡逻频率（揭发 → 每天一次） |

### Scene 4 入站

| 来源 | 变量 | 影响 |
|------|------|------|
| Scene 1 | `knife_choice` | 师刀 → 抄写"师徒传承"经文时停笔闪回 |
| Scene 2 | `seventh_aperture_awareness` | 觉察 → 打坐时不安闪回 |
| Scene 3 | `peach_tree_fate` | 保留 → 看到桃树时莫名觉得重要 |
| Scene 3 | `memory_kept` | 铭记 → 听到"齐天大圣"时心跳闪回 |
