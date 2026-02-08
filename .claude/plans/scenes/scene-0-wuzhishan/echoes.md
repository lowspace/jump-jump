# 回响（Echoes）

## 入站回响（从其他场景流入 Scene 0）

Scene 0 在首次游玩时使用所有变量的**默认值**。以下变量在通关后"重新渲染"时从对应场景流入：

### 来自 Scene 1（陈塘关·骨与莲）
- `knife_choice` — 父刀/师刀
- `nezha_trust` — 信任等级
- `wushi_presence` — 武师存在感
- `armguard` — 护腕处置
- `lijing_hesitation` — 李靖犹豫程度

### 来自 Scene 2（天蓬·月与逐）
- `tenpeng_last_words` — 天蓬最后的话是否被听到
- `moon_response` — 月亮是否回应
- `marshal_memory` — 元帅记忆状态
- `clerk_choice` — 书记官选择

### 来自 Scene 3（花果山·石与火）
- `memory_kept` — 铭记/遗忘
- `peach_tree_fate` — 桃树命运
- `monkey_survivors` — 猴群存续
- `huaguoshan_fire` — 花果山火焰程度

### 来自 Scene 4（经卷·字与空）
- `final_scroll` — 经卷内容
- `faming_faith` — 法明信念状态
- `scripture_truth` — 真相是否揭露
- `traveler_destination` — 行者去向

### 跨场景综合条件
- 四个场景中 ≥ 3 个场景的核心选择倾向（铭记/反抗/坚守 vs 遗忘/服从/放弃）
- 所有四个场景是否完成"杨戬/杨戬线索"的条件触发
- `grandmother_stories` = 4 且所有场景均完成

## 出站回响（从 Scene 0 流向其他场景）

Scene 0 的输出变量（`wall_inscription`、`mountain_voice`、`final_act`、`grandmother_stories`、`curiosity_level`、`wukong_awareness`）全部流向**影响力报告**，不直接流向其他可玩场景。
