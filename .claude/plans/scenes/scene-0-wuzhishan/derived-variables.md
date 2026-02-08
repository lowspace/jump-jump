# Scene 0 派生变量逻辑文档

> 本文档定义 Scene 0 重新渲染机制中使用的派生变量。这些变量不是由各场景直接输出，而是基于源变量通过特定规则派生得出。

---

## 派生变量映射表

| 派生变量 | 源变量 | 派生规则 |
|----------|--------|----------|
| `moon_response` | `tenpeng_last_words` | 若 `tenpeng_last_words`=是 且 Scene 2 中陆执选择「等待/观察」路线 → 回应；否则 → 沉默 |
| `marshal_memory` | `survival_method` | 若 `survival_method` ∈ {记得自己是谁, 有牵绊, 留了后手的沉默} → 记得；否则 → 遗忘 |
| `clerk_choice` | `ledger_choice` | 若 `ledger_choice`=揭发 → 反抗体制；否则 → 服从 |
| `monkey_survivors` | `monkey_unity` | 若 `monkey_unity`=团结 → 存活；若 `monkey_unity`=分裂 → 部分存活；若 `monkey_unity`=散去 → 无 |
| `huaguoshan_fire` | `peach_tree_fate` + `resistance_choice` | 若 `peach_tree_fate`=砍掉 或 (`resistance_choice`=反抗 且未满足隐藏条件) → 全毁；否则 → 未烧/控制 |
| `faming_faith` | `faith_state` | 直接映射：坚定→保持, 动摇→困惑, 重建→重建, 崩塌→崩塌 |
| `scripture_truth` | `sutra_truth` | 直接映射：禅意→禅意, 政治→揭露, 悖论→揭露, 不理解→隐藏 |
| `traveler_destination` | `tangseng_encounter` + `faith_state` | 若 `tangseng_encounter` 有深度对话 且 `faith_state`≠崩塌 → 继续西行；否则 → 放弃/转向 |

---

## 派生规则详解

### 1. `moon_response` — 月的回应

**源变量**：`tenpeng_last_words` (Scene 2)

**派生逻辑**：
- 基础条件：`tenpeng_last_words` = 是（陆执听到了天蓬最后叫阿月的名字）
- 附加条件：Scene 2 中陆执在面对天蓬坠落时选择了「等待/观察」路线（非立即行动或逃离）
- 满足以上两个条件 → **回应**：Scene 0 中少年看到的月亮比平时亮，暗示阿月听到了天蓬的呼唤
- 任一条件不满足 → **沉默**：月亮如常

**叙事意义**：月的回应象征着跨越天界的情感连接是否被感知。

---

### 2. `marshal_memory` — 天蓬的记忆

**源变量**：`survival_method` (Scene 2)

**派生逻辑**：
- 若 `survival_method` 属于以下取值之一：
  - 「记得自己是谁」
  - 「有牵绊」
  - 「留了后手的沉默」
- → **记得**：Scene 0 中出现光滑石头，暗示有人（天蓬）在此反复摩擦，保持自我记忆
- 其他取值 → **遗忘**：无此细节

**叙事意义**：天蓬是否在被贬下凡后仍保持天蓬元帅的自我认同。

---

### 3. `clerk_choice` — 小吏的选择

**源变量**：`ledger_choice` (Scene 2)

**派生逻辑**：
- 若 `ledger_choice` = 揭发 → **反抗体制**：Scene 0 中山脚村民开始议论「天上的规矩也不是铁打的」
- 其他取值（隐瞒/部分揭露）→ **服从**：无此议论

**叙事意义**：陆执的选择是否在人界产生了涟漪效应，启发了凡人对体制的质疑。

---

### 4. `monkey_survivors` — 猴群幸存者

**源变量**：`monkey_unity` (Scene 3)

**派生逻辑**：
- 若 `monkey_unity` = 团结 → **存活**：Scene 0 中少年偶尔能看到猴子，它们在等待某人
- 若 `monkey_unity` = 分裂 → **部分存活**：Scene 0 中少年偶尔能看到一两只猴子，但很快消失
- 若 `monkey_unity` = 散去 → **无**：Scene 0 中山上没有猴子

**叙事意义**：花果山猴群的最终命运，以及它们是否仍在等待齐天大圣的归来。

---

### 5. `huaguoshan_fire` — 花果山之火

**源变量**：`peach_tree_fate` (Scene 3) + `resistance_choice` (Scene 3)

**派生逻辑**：
- 触发全毁的条件（满足任一）：
  - `peach_tree_fate` = 砍掉（桃树被砍，花果山失去精神象征，天兵全面清剿）
  - `resistance_choice` = 反抗 且未满足隐藏条件（盲目反抗导致天兵激烈镇压）
- → **全毁**：Scene 0 中旗帜碎片只剩几根丝线
- 其他情况 → **未烧/控制**：旗帜碎片上的红色纹路更完整，隐约能看出王旗图案

**隐藏条件**：满足以下至少两项视为满足隐藏条件：
- `monkey_unity` = 团结
- `iron_head_fate` = 存活
- `memory_kept` = 铭记

**叙事意义**：花果山是否在天兵清剿中幸存，以及抗争的代价。

---

### 6. `faming_faith` — 法明的信仰

**源变量**：`faith_state` (Scene 4)

**派生逻辑**（直接映射）：

| `faith_state` | `faming_faith` | Scene 0 效果 |
|---------------|----------------|--------------|
| 坚定 | 保持 | 祖母讲故事四时语气笃定，认同无字真经的观点 |
| 动摇 | 困惑 | 祖母讲完故事四后表示困惑，听不懂 |
| 重建 | 重建 | 祖母讲故事四时语气充满希望，提到「重新找到相信的东西」 |
| 崩塌 | 崩塌 | 祖母不讲此故事，或讲述时语气悲凉 |

**叙事意义**：法明对信仰的探索如何影响民间口述传统的传承。

---

### 7. `scripture_truth` — 经文的真相

**源变量**：`sutra_truth` (Scene 4)

**派生逻辑**（直接映射）：

| `sutra_truth` | `scripture_truth` | Scene 0 效果 |
|---------------|-------------------|--------------|
| 禅意 | 禅意 | 山上某处岩石的自然纹路在特定角度看起来像一个「空」字 |
| 政治 | 揭露 | 同上（「空」字显现） |
| 悖论 | 揭露 | 同上（「空」字显现） |
| 不理解 | 隐藏 | 无此细节 |

**叙事意义**：法明对无字真经的理解是否以某种神秘方式「刻印」在五指山的环境中。

---

### 8. `traveler_destination` — 行者的目的地

**源变量**：`tangseng_encounter` (Scene 4) + `faith_state` (Scene 4)

**派生逻辑**：
- 继续西行的条件（需同时满足）：
  - `tangseng_encounter` 有深度对话（非「未遇见」，且对话深度 ≥ 2）
  - `faith_state` ≠ 崩塌（信仰未完全崩塌）
- → **继续西行**：Scene 0 中行者脚步坚定，身上有「知道自己要去哪」的气质
- 任一条件不满足 → **放弃/转向**：行者脚步正常，表情平静但看不出方向感

**叙事意义**：唐僧与法明的相遇是否成为唐僧继续西行的精神支撑。

---

## 派生变量与源变量名称对照

| Scene 0 重新渲染中使用的名称 | 对应源场景输出变量 | 派生类型 |
|---------------------------|-------------------|----------|
| `moon_response` | `tenpeng_last_words` (Scene 2) | 条件派生 |
| `marshal_memory` | `survival_method` (Scene 2) | 集合派生 |
| `clerk_choice` | `ledger_choice` (Scene 2) | 二元派生 |
| `monkey_survivors` | `monkey_unity` (Scene 3) | 映射派生 |
| `huaguoshan_fire` | `peach_tree_fate` + `resistance_choice` (Scene 3) | 复合派生 |
| `faming_faith` | `faith_state` (Scene 4) | 直接映射 |
| `scripture_truth` | `sutra_truth` (Scene 4) | 直接映射 |
| `traveler_destination` | `tangseng_encounter` + `faith_state` (Scene 4) | 复合派生 |

---

## 使用说明

1. **派生时机**：这些变量在 Scene 0 重新渲染时实时计算，不存储于存档中
2. **调试方式**：开发模式下可查看派生变量的计算过程和中间结果
3. **扩展规则**：新增派生变量需在此文档中登记，并说明派生逻辑和叙事意义
