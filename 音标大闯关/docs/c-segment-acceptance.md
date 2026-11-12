# C 段验收规格 · 多圈三分钟 + 赛车出题多样性/准确性

> 状态：**已实现并完成本地全量验收（2026-11-08）；仍未部署、未上线、未 commit，发布须用户明确放行**。
> 2026-11-07 用户拍板两项硬约束：「C 段要确保多圈也要三分钟内跑完，并且赛车中的出题要多样性且准确」。
> 本文 §0–§3 保留**落地前的可复现实测基线**与**可执行验收断言**（基线取自 Node 直接 import 真实模块，非估算）；**落地结果与实测数据见 §5**。

---

## 0. 结论速览

| 硬约束 | 落地前基线（判定） | 落地后实测（判定） |
|---|---|---|
| 多圈 ≤ 3 分钟 | **FAIL**：1 圈制；直接改 2 圈理论 175.0s / 142.6s，且未计碰撞与答题停顿 | **PASS**：2 圈 + 提速 260/300；理论 148.1s / 128.4s，Node headless 11 场最慢 **174.57s ≤ 180s** |
| 出题多样性 | **FAIL**：2 音素 / 7 词对 / 1 题型；两对固定题 100%、额外题连续同对 14.1% | **PASS**：18 音素 / 37 词对 / 3 题型；固定题 0、任一对最大出现率 **0.515**、单局 4 对零重复、额外题连续同对 **0%** |
| 出题准确性 | **PASS**：7/7 最小对立正确、16/16 音频齐全、答案键正确 | **PASS**：37/37 unit 绑定与美式权威表逐字一致、83 词 / 83 mp3 零缺口、答案键与 `sym` 稳定键未动 |

---

## 1. 硬约束 A · 多圈也要三分钟内跑完

### 1.1 实测基线（Node 实跑，非估算）

`createTrack(TUNING).length = 19254.50` 单位（`straight 6800 × 2 + radius 900 的椭圆双半圆`）。

| 档位 | speed | 1 圈 | 2 圈 | 3 圈 | 与 180s 关系 |
|---|---|---|---|---|---|
| 跟读档 follow | 220 | 87.5s | **175.0s** | 262.6s | 2 圈仅余 5.0s；3 圈超 82.6s |
| 听辨档 listen | 270 | 71.3s | **142.6s** | 213.9s | 2 圈余 37.4s；3 圈超 33.9s |

上述是**纯匀速理论下限**，尚未计入：`SLOW` 倍率 0.54 / 0.85s、`COLLIDE.slow 2.2s`、`COLLIDE.think 2.7s`、分岔门 `decide.left = 3s` 的答题停顿、额外惩罚题、石头/撞墙。结论：

- **当前代码是单圈制**（`race.js:696` 的 `traveled >= track.length`），连「多圈」都还没实现。
- 若只把判定改成 `>= 2 * track.length` 而不提速，**跟读档实际必然超 180s**。
- **3 圈在现有速度下不可能达标**（两档理论值均已超），本轮锁定 **2 圈**（沿用 11-05 拍板）。

### 1.2 可执行口径（双口径，缺一不可）

1. **理论口径**：`laps × track.length / speed ≤ 150s`（两档都要），即给实际减速/答题预留 ≥ 30s 缓冲。
   - 按 2 圈反推：`speed ≥ 2 × 19254.5 / 150 = 256.7`。
   - 建议落值：**follow 220 → 260**（2 圈 148.1s）、**listen 270 → 300**（2 圈 128.4s），档位差保留。
   - 备选：保持速度但缩短 `straight/radius`，会连带改动门位置与赛道几何，**不推荐**。
2. **实测口径**：headless 以固定 `dt` 步进跑完整场比赛，断言 `race.state.finishTime ≤ 180.0s`。必须覆盖最坏工况：连续答错触发 `SLOW`、至少 2 次 `COLLIDE`、额外题全触发。理论口径放行不等于实测放行。

### 1.3 多圈实现约束（写死，防漏）

- 完成判定改 `traveled >= laps × track.length`，`laps` 为可配置常量（默认 2）。
- **按圈重置**：`gates[].judged / played / replayed / holdDone` 与 `state.pickups[].taken` 必须在跨圈时按圈复位，否则第 2 圈无题、无道具、无宝石。
- `commits` 按圈分配：建议每圈 2 个门（总题量仍 4），避免答题停顿随圈数翻倍把 180s 吃掉。
- `state.time` 在 `finished` 后仍累加（`race.js:571`）属既有行为；验收一律取 `state.finishTime`，**不要取 `state.time`**（会被结果页停留时间污染）。
- `result()` 的 `time` 字段、`main.js:610` 的「用时 X 秒」沿用 `finishTime`，无需改显示。

### 1.4 验收断言（C 段落地后跑）

```
A1  config: laps === 2
A2  follow: 2*L/speed <= 150  且 listen: 2*L/speed <= 150
A3  headless 正常工况 finishTime <= 180
A4  headless 最坏工况（连续答错 + 2 次碰撞 + 额外题）finishTime <= 180
A5  第 2 圈的 gates 全部可 judged、pickups 全部可 taken（按圈重置生效）
A6  result().time === state.finishTime，且不受结果页停留时长影响
```

---

## 2. 硬约束 B · 赛车出题多样性且准确

### 2.1 现状基线（Node 实跑 3000 局 + 20000 局模拟）

| 指标 | 现状 |
|---|---|
| 覆盖音素 | **2** 个（`/i/`、`/ɪ/`） |
| 词对池 `PAIRS` | **7** 对，`allWords()` 16 词 |
| 单局分岔门 | 4 道（`TUNING.commits`），4 对互不重复 ✓ |
| `buildGates` 固定对 | `seat/sit` **100%**、`sheep/ship` **100%**（`fixed = [PAIRS[0], PAIRS[1]]`） |
| 其余 5 对出现率 | 38.3% – 41.9% |
| 额外题 `openQuiz` | 从 7 对纯 `Math.random()` 取值、**无去重**，连续同一对 **14.1%** |
| 题型 | **1 种**：听单词 → 二选一选单词 |
| 音频覆盖 | 16/16 齐全；`leave.mp3` / `live.mp3` 两个冗余未使用（可并入扩池） |

### 2.2 准确性现状（PASS，扩池时须保持）

逐对核对，7/7 均为同一辅音框架下的 `/i/ ↔ /ɪ/` 最小对立，美式音值正确：

```
seat/sit   sheep/ship   feet/fit   beat/bit   sleep/slip   green/grin   cheek/chick
```

- `side()` 把 `ipa / length / hint` 从 `VOWELS` 注入每个词，答案判定 `finishQuiz()` 用 `word === spoken.word`，逻辑正确。
- `alias: "iː"` / `length: "长"` 是**逻辑枚举键与角标**，按 C07 裁决逐字不动；美式大字由 `window.IPA_DISPLAY` 提供。
- 音频 `audio/<word>.mp3` 16/16 存在，`playWord` 不会静默降级到 TTS 兜底。

### 2.3 C 段目标指标（落地后应达到）

| 指标 | 目标 |
|---|---|
| 覆盖音素 | ≥ 16（按 B2 四区杯赛分区，每区一组最小对立簇） |
| 词对池 | ≥ 24 对，按地图 `PAIRS_BY_MAP[mapId]` 分组 |
| 固定题 | **0 对**；任一词对单局出现率 ≤ 60% |
| 单局去重 | 分岔门词对**互不重复**；跨圈也不重复 |
| 额外题 | 连续两次不同对（去重窗口 ≥ 3），连续同对率 **0%** |
| 题型 | ≥ 3 种（听词选词 / 听音选音标 / 看词选发音类别），单局至少出现 2 种 |
| 答案键 | `options` 两项互异、`answer` 指向存在项、`spoken` 必在 `options` 内 |
| 音频 | 新增词 100% 有对应 mp3，缺失即 FAIL |

### 2.4 准确性硬约束（扩池时锁死，防 C07 已修的错配回潮）

1. 每个词**绑定唯一 unit id**（`U01`–`U48`），音值只取 `window.IPA_DISPLAY[unit].displayIpa`；**禁止**用 `displayIpa` 做键（U05/U07 同为 `ɑ` 会串）、禁止用 `sym` 做显示。
2. 每对必须是**同一辅音框架下的最小对立**，且两词都真实存在、音值与 unit 对应；禁止把 `ɒ/ɑː → ɑ` 的合并音做成对立题。
3. rhotic 组 `U11 ɜr / U18 ɪr / U19 ɛr / U20 ʊr` 的例词须带 r 色彩，不可套用英式 `ɜː/ɪə/eə/ʊə` 的词。
4. 新增词必须有 `audio/<word>.mp3`；`playWord` 的 TTS 兜底**不算**准确性达标。
5. 题库改动**禁止重跑** `build_data.py` / `augment_data.py` / `extract_content.py`，否则覆盖 C07 的 `data.js` 美式文案。

### 2.5 验收断言（C 段落地后跑）

```
B1  VOWELS/题库覆盖音素 >= 16，PAIRS_BY_MAP 四个 mapId 各非空
B2  buildGates(rand) 跑 3000 局：无任一 pair 出现率 = 100%，最大 <= 60%
B3  单局 4 题 pair 互不重复；跨 2 圈 4 题也互不重复
B4  openQuiz 连续同对率 = 0%（20000 局模拟）
B5  题型 >= 3 种，单局实际出现 >= 2 种
B6  全部 pair：两词互异、ipa 与 unit 一致、mp3 存在
B7  options 两词互异且含 spoken；answer/hit 判定不变
B8  美式显示表 ipa-display.js 全文未动、sym 稳定键未动
```

---

## 3. 本轮 fresh 全量复验结论（2026-11-07）

- `verify_fresh_gate.py`：**21 PASS / 0 FAIL / 21 TOTAL**，覆盖 §5.2 九条 + G3 + G5 双场景 + 不回退；四项错误计数全 0。
- `verify_c08_gate.py`：**37 PASS / 0 FAIL / 37 TOTAL**（连续多次复跑稳定）。
- 关键证据：与 C07-B 前基线同为 7684 行、**仅 155 行差异且逻辑键 0 处改动**；25 组镜像逐字一致；49 张发布卡面与美式源逐字节全等；上游 `content_raw.json` / `data.js.bak` mtime 均早于 `data.js`（构建管线未重跑）。
- **CONCERNS（原 1 项，C 段已解决）**：`atlas.js:97/195` 列表页立绘 + `:210` 图谱 URL 未带 `?v=`。C 段已把 atlas 6 处，以及教学页立绘、大地图、封面、叙事章插图、B 系列期配图等**共 20 个图片 URL 字面量全部补齐** `?v=cseg-20261107`（含 `assets/img/ + 变量` 动态拼接型），全仓 **46 处 tag 唯一、零裸引用**，并由 `verify_cseg_gate.py` S18 断言锁死。fresh 复验 CONCERNS 归 0。

## 4. 边界

- C 段**已实现并完成本地全量验收**；**未部署、未上线、未 commit**，发布须用户明确放行。
- 两站必须部署在同一站点根下（拉力赛跨目录引用大闯关 `ipa-display.js` 与卡图）。
- 剩余串行：人工审批发布 → 线上资源按字节复核（Caddy 对不存在路径兜底返回 `index.html` 且 200，**勿凭状态码判定送达**）。

## 5. C 段落地结果与验收矩阵（2026-11-08）

### 5.1 实现清单

| 模块 | 落地内容 |
|---|---|
| `config.js` | `TUNING.laps=2`；follow 220→**260**、listen 270→**300**；`RACE_MAPS` 四区杯赛、`CHARACTERS` 三车手、`PHONEMES` 18 音素、`PAIRS_BY_MAP` 37 词对、`QUIZ_TYPES` 三题型；`buildGates(mapId, rand)` 按圈生成独立门（`lap` + 绝对 `lineT`）；`pickQuizPair()` 最近 3 对去重；`allWords()` 单一词表来源 |
| `race.js` | 门判定 / rival 判定 / 终点判定全部改**绝对里程** `g.line`，弃用 `hasPassed(odo, commitT)` 与 wrapped `t`；跨圈 `pickups[].taken` 复位；额外题从当前地图词池出题 |
| `main.js` | 四区 / 车手选择器 + 偏好持久化；教学面板追加「本场杯赛重点」；quiz 三题型呈现（`word` 题不泄答案）；进度条分母按圈数放大、HUD 显示「第 X/Y 圈」；结果页按答对门所属 `unit` 解锁卡、`rally.maps` 记四区成绩；`rally` 新增字段同步进大闯关 `store.js` 白名单 |
| 音频 | `build_word_audio.py` 以 `config.allWords()` 为唯一词表，edge-tts `en-US-AriaNeural` 断点续跑生成；**83 词 / 83 mp3 / 零缺口 / 帧头全有效** |
| 缓存 | 全站统一 `?v=cseg-20261107`，**46 处字面量唯一**；20 个图片 URL 零裸引用 |

### 5.2 实测数据（非估算）

| 项 | 数值 |
|---|---|
| 赛道长度 / 2 圈里程 | 19254.50 / 38509.00 |
| 理论耗时（2×L/speed） | follow **148.1s**、listen **128.4s**（均 ≤150s） |
| Node headless 实跑 | 2 档 × 4 地图 normal + 3 个 worst/强制碰撞 = **11 场全部完赛**，`4/4` 门判定、跨圈 1 次；耗时 135.80–**174.57s**，最坏工况（15 次碰撞 + 20 额外题全错）仍 ≤180s |
| 题库 | 4 地图 / **37 词对**（camp 8、castle 10、kingdom 8、peak 11）/ 18 音素 / 3 题型 |
| 多样性 12000 局 | 固定题 0、任一对最大出现率 **0.515**、单局 4 对零重复、三题型各覆盖 12000 局、额外题连续同对 **0%** |
| 准确性 | unit 绑定与 `window.IPA_DISPLAY` 逐字一致 0 错配；美式权威表全文未动、`sym` 稳定键未动 |

### 5.3 四套门控（本地全绿，合计 110 项）

| 脚本 | 结果 | 覆盖 |
|---|---|---|
| `音标拉力赛/verify_cseg_gate.py` | **38 PASS / 0 FAIL** | S1–S18 源码接线（含零裸图片 URL）、A0–A6 多圈三分钟、B0–B9 出题、C1–C3 音频物理 |
| `音标拉力赛/verify_cseg_ui.py` | **14 PASS / 0 FAIL** | 真实 Chromium DOM：选择器点击与写盘、reload 偏好、教学动态区、两圈建门、三题型 quiz 卡片、结果页解锁、跨站字段保真 |
| `音标大闯关/verify_fresh_gate.py` | **21 PASS / 0 FAIL**，CONCERNS 0 | §5.2 九条 + G3 + G5 双场景 + 不回退；四项计数全 0 |
| `音标大闯关/verify_c08_gate.py` | **37 PASS / 0 FAIL** | C08 跨站覆盖 / 老存档迁移 / gems delta / A 段回归 / 补表 G；四项计数全 0 |

### 5.4 本轮额外修的两处（非 C 段规格要求，但属发布阻塞）

1. **图片 URL 版本化补齐**：除 atlas 6 处外，另有 8 个静态字面量与 2 处 `"assets/img/" + 变量` 拼接型裸 URL（叙事章 7 图、B 系列 24 张期配图、教学页立绘等）会命中旧缓存，已全部补齐并由 S18 锁死。
2. **验收脚本浏览器路径**：本机 Playwright 升至 1.64.1 后默认寻找 `chromium-1248`，而本机仅有 `1228`；`verify_fresh_gate.py` / `verify_c08_gate.py` 改用项目既有的系统 Chrome `executable_path`，避免把环境缺失误判为产品缺陷。
