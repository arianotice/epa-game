# 声音拉力赛 · 正向设计规格 01：核心循环
### 让孩子自己点开第二局，并在这一局里真的把音听准

> **文件角色**：下一轮实现的唯一设计依据。含可落地规则与数值。
> **交付边界**：本轮只新增本文件；产品代码与既有 design 文档均保持原样，门控 / 构建 / 提交 / 部署均不在本轮执行。
> **上下文边界**：本派单即全部上下文。文中出现的 `js/*.js`、`index.html`、`css/game.css` 均为本轮只读盘点所得的产品代码事实，用于标注影响面。

---

## 0. 推导起点：两条不可再拆的事实

**事实 A —— 孩子为什么会自己点开第二局。**
上一局结束时，他脑子里必须留着**一个具体到能立刻补救的缺口**：「就差那一个词」「就差 0.8 秒」「就差一个名次」。奖励、集卡、徽章都排在后面，因为它们兑现得太远；动机产生在**结果页出现的那一秒**。同时他得相信下一局自己补得上（有变强的证据），而且补上之后有人看得见（有可比较的对象）。

→ 推导出：**近失缺口（M1）**、**可比较对象（M3）**、**变强证据（M2）**、**一局之内可自己决定的取舍（M4）**、**一局接一局的短钩子挂到长线上（M5）**。

**事实 B —— 音标听辨怎样才会自动化。**
/ɪ/ 与 /iː/ 的差别落在几十毫秒的时长与肌肉紧张度上，是耳朵的活，不是记规则的活。要自动化，反馈必须满足三件事：**紧贴判断**（判断后几百毫秒内，差异还在听觉记忆里）、**并排呈现两个音**（单独说「错了」不产生辨别力，「ship ↔ sheep」才产生）、**高频且不打断赛车节奏**（每局 4 道闸门 × 每天几局，闸门反馈单元必须 ≤ 1.3 秒、不新增冻结、零面板；撞石额外题的既有 850ms 答题窗口不属于这条链路，见 §4.5）。

→ 推导出：**判断后即时 A/B 对比音（§4）**、**把「撞石罚题」改成同一条连听链上的加时题（§3）**。

### 保持不变的骨架与四条硬约束（本轮全部继承，逐条作为设计边界）

| 项 | 保持不变的内容 | 代码事实（只读盘点） |
|---|---|---|
| 核心循环 | 每局 2 圈、4 道闸门；闸门播一个音标 / 单词；赛道真实分叉成左右车道；听音后把车开进对应车道；选完分叉闭合回正常赛道 | `js/config.js` `TUNING.laps=2`、`commits=[0.24,0.68]`、`buildGates()`；`js/race.js` `branchLateral()` / `blockSplitter()` / `judge()` |
| 硬约束 1 | 车速体感快且丝滑，靠环境流速增益放大中央虚线 / 路肩 / 远景 / 粒子 / 路牌的后退相位；判定层速度常量 **260 / 300 unit/s** 不动 | `js/render.js` `VISUAL_FLOW_GAIN=1.6`；`js/scene3d-model.mjs` `VISUAL_FLOW_GAIN` / `flowPhase`；`js/config.js` `DIFFICULTY.follow.speed=260`、`listen.speed=300` |
| 硬约束 2 | 赛道有石头，空格 / 点「跳跃」可躲过；没躲过则做一道额外听辨题，这是危机感来源 | `js/race.js` `settleRock()` / `scanPickups()` / `openQuiz("rock")`；`ROCK_QUOTA=2`、`ROCK_HITS_MAX=2`、`ROCK_HIT_BAND=78` |
| 硬约束 3 | 三辆卡丁车（玩家 + 2 NPC），NPC 有真人操控感、不龟速、不扎堆 | `js/race.js` `npcLaneTarget()` / `pressRivals()` / `baseMul()`；`NPC_MIN_SPEED_RATIO=0.94`、`skill=0.28/0.42`、`startBoost=1.8s` |
| 硬约束 4 | 成功跳过石头给 `Good / Excellent / Marvellous` 欢呼 + 单词周围局部小彩带 | `js/race.js` `cheer()` / `settleRock()`；`js/main.js` `syncCheer()` / `burstConfetti()`（16 片，life 0.9–1.4s）；`ribbonT=1.0s` |
| 已有系统 | 48 音标精灵 / 六档稀有度图鉴、30 关卡地图、四区杯赛、宝石 / 商店 / 角色、1~3 星、localStorage 单键 `ipa-quest-v1`、37 词对 / 18 音素题库 | `js/cards.js`（`P/SR/SAR/HR/SSR/UR`）、`js/config.js` `PAIRS_BY_MAP` / `PHONEMES` / `RACE_MAPS`、`js/main.js` `commit()`、`js/race.js` `applyWalletDelta()` |

**关键现成挂接点（本轮盘点发现，零新增字段即可启用）**
- `js/race.js` `state.warning` / `state.warningT` 已初始化但全项目零读取 → 直接启用为「耳朵预警」。
- `js/config.js` `buildGates()` 已为每门生成 `replayed:false` → 直接用于「一次听准」统计。
- `js/main.js` `openResults()` 已写入 `rally.maps[m.id].bestTime`、`bestAcc`、`rally.EP02.bestAcc` → 直接用于影子与近失计算。
- `js/main.js` `commit()` 已是「写入瞬间重读整对象 → 最小变更 → 写回」，拉力赛侧可安全接入新域；**但跨站共享键 `ipa-quest-v1` 有白名单前置条件，见下方 P0 项**。

> **P0 跨站实现前置条件（阻塞 Top1–3；只读盘点已实测确认）**：姊妹站 `音标大闯关/js/store.js:47-48` 的 `RALLY_FOREIGN` 白名单只有 11 键（`gems / shields / paint / trim / ownedPaints / ownedTrims / EP02 / howSeen / maps / lastMap / lastChar`）。其 `save()`（:97-100）执行 `refreshFromRaw(data, rawRead())` → `writeRaw(data)` **全量写回**，而 `refreshFromRaw()`（:86）只透传白名单内的键；已打开的大闯关标签任何一次 `save()` 都会**静默抹掉白名单外的全部新域**。落地前必须一次性把 `fwd / ear / shadow / rivals / weekly / ageBand` 共 **6 键（superset）** 加入 `RALLY_FOREIGN`，否则新统计与埋点全部会被覆写。第 6 位 `ageBand` 为**冗余保留位**：`refreshFromRaw()` 是 `if (k in src)` 包含性透传，多列一个当前不存在的键为零成本空操作；若 D1 最终取 `sessionStorage` 方案该位恒为空操作，若用户裁定 `ageBand` 留共享键则无需二次改白名单（FWD-2 D-6 / 附录 B.9 已与工程侧统一按 6 键落地）。此项属跨站工程改动，需经程基岩 / team-lead 排期。
- `css/game.css` 已有 `:root` 变量（`--display` / `--body` / `--ipa` / 配色）→ 年龄分层用一个 body class 覆盖变量即可，无需第三套样式。

---

## 1. 五个机制：把「愿意再玩一局」做出来（问题 1）

### 1.1 机制总表

| 编号 | 要做什么 | 触发时机 | 反馈 | 数值区间 | 现有系统挂接点 | 验收口径 |
|---|---|---|---|---|---|---|
| **M1** | **近失缺口 + 带目标的「再跑一场」**：结果页只给最紧的一条具体缺口，并把它写进按钮 | `openResults()` 结果页出现瞬间 | 一行大字 + 按钮文案变成带目标的动作 | 差 1 题 / 差 1 名次 / Δt ≤ 3.0s / `place=3` 败局，四者取最紧 1 条 | `scoreRace()`、`result()`、`rally.EP02` / `rally.maps[id]`、`#best`、`#panel-results` | 每局结果页恒有且仅有 1 条近失句；「再跑一场」按钮文案含具体目标 |
| **M2** | **一次听准率 + 最长连听**：把「技巧变强」做成每局可见的 Δ 数字 | 每道闸门 `judge()` + 结果页 | 结果页「这局 3/4 一次听准 · 比上局 +1」；段位 E1–E6 | firstListen 0–4 题/局；Δ ∈ [−4,+4]；滑动窗口 10 局；段位 E1–E6 | `gate.replayed`、`judge()`、`update()` replay 分支、`result()`、新域 `rally.ear`（走 `commit`） | 按了「再听一次」的门不计入 firstListen；star / acc / place 口径逐字不变 |
| **M3** | **影子条 + 成绩卡**：让每局都有可比较的对象（自己最好 / 上次 / 同学） | 比赛 `syncHud()` 每帧 + 结果页 | HUD 进度条上一个小三角 + 「领先影子 1.2s」；结果页「复制成绩卡」 | Δt 显示 ±0.3s 以上才出字；成绩卡 ≤ 12 字符；同学码最多存 5 条 | `#progress`、`syncHud()` 的 `frac`、`rally.maps[id].bestTime`、`commit()` 新域 `rally.shadow` / `rally.rivals` | 首局无 bestTime 时影子条隐藏；成绩卡可抄可贴、纯本地零后端 |
| **M4** | **外线宝石链 + 尾流超车**：一局之内自己决定「稳着跑」还是「赌一把」 | 非分叉段拾取 gem / 贴近 NPC 车尾 | 外线宝石 ×2；链完成给一次氮气；尾流期 HUD「贴住了 +15%」 | 外线 3 颗 ×2 宝石、中线 7 颗 ×1、单圈上限 13 宝石；尾流窗口 130–260 unit、蓄力 1.0s、1.15× / 1.5s、每局 ≤3 次 | `buildField()` gem 分布、`applyWalletDelta(1,0)`、`rocket()`、`COLLIDE.along=130` / `lateral=0.22`、`blocked()` 分叉避让 | 走外线与走中线宝石收益差可测；尾流不进分叉窗口；撞击即触发既有罚题 |
| **M5** | **周历 7 格 + 本局目标卡**：短局（≤150s）与长线咬合 | `openTeach()` 发卡 → 本局内判定 → `openResults()` 点亮 | 每局结果页「周历 3/7」；满 7 格给 30 宝石 + 1 款装饰 | 1 局 = 1 格；7 格/周；每周大奖励 ≤1 次 | `openTeach()` / `beginCountdown()` / `openResults()`、新域 `rally.weekly`、`PAINTS`/`TRIMS` 装备域 `ownedTrims` | 目标卡达成条件全部落在本局 2 圈内；周历按自然周重置；跨站共享键须先扩 `RALLY_FOREIGN` 白名单（§0 P0 项） |

### 1.2 逐机制规则与数值

#### M1 · 近失缺口（收益最高：动机产生的那一秒）

**计算（单位：题 / 名次 / 秒）**

```
total   = 4                                  // 题，TUNING.laps × commits.length
acc     = hits / total                        // 0~1，hits 来自 result().hits.length
Δ题     = ceil(0.8 × total) − hits            // 题；3 星门槛 acc≥0.8（4 题需全对）
Δ名次   = place − 1                           // 名次；3 星另需 place ≤ 2
Δt      = time − rally.maps[mapId].bestTime   // 秒；time 来自 result().time

显示条件：Δ题 ∈ {1,2} 或 Δ名次 = 1 或 |Δt| ≤ 3.0s 或 place = 3
取最紧 1 条，优先级：place=3（败局钩子） > Δ题=1（且 place≤2） > Δ名次=1 > |Δt| 最小
```

> `place=3` 时 3 星不可能（`place≤2` 是硬门槛），此时「差 1 题就三星」是假希望，故败局钩子优先级最高，只给「把名次追回前二」这一个可达目标。

**文案（正向，指到具体动作）**
- 第 3 名（败局）→ `第 3 名 · 先把车开回前二`；按钮 `再跑一场 · 追回一个名次`
- 差 1 题 → `就差 ${misses[0].spoken.word} 这一个词，三星就到手`；按钮 `再跑一场 · 把 ${word} 开对`
- 差 1 名次 → `第 2 名，离第 1 名只差一个车身`；按钮 `再跑一场 · 抢回第 1 名`
- 差时间 → `比自己最好慢 0.8 秒`；按钮 `再跑一场 · 追回 0.8 秒`
- 无历史（首局）→ `第一局已建档，下一局开始追自己`；按钮 `再跑一场 · 定个目标`

**配套**：结果页 `misses` 列表已可点播单词（`data-word` → `audio.playWord`），近失句直接复用这个列表，把「差的那一个词」变成可立刻重听的对象。

**自主性约束（供 FWD-2 的 FP-3 / D2 校正）**：`#btn-again` 恒为结果页**单一按钮**，由孩子**无提示自主点击**。近失句是「信息」不是「要求」——结果页不出现「再玩一局吧 / 再玩 X 局 / 还差 N 局」的引导语，不弹倒计时、不弹续玩弹窗，教学页与会话层均不告知本次要玩几局。M5 周历 `3/7` 只作跨天进度回显，不构成局数任务。按钮文案里的「追回 0.8 秒 / 把 sheep 开对」属设计机制本身的目标信息，与实验者提示严格区分。

**测量仪器约束（FWD-2 C-3，必须先于 M1 落地）**：M1 把 `#btn-again` 从中性按钮改成定向 CTA，**改的正是 A1 VRR / A2 重玩率的测量仪器**，会系统性抬高重玩率。因此：① M1 落地前先跑一轮**中性按钮基线**并完成阈值标定；② M1 作为**处理组**做 A/B 或前后分阶段，两组阈值分开标定，**不沿用 M1 前标定的阈值**；③ 实验记录中把 FP-3 的「被要求玩」与 M1 的「目标信息」分开标注。M1 之前标定的判据对 M1 之后一律无效。

#### M2 · 一次听准率 + 最长连听（可见变强）

```
firstListen  = |{ g ∈ judged : g.hit ∧ ¬g.replayed }|        // 题，0~4
Δ_first      = firstListen(本局) − firstListen(上局)           // 题，−4~+4
cleanChain   = 连续「答对 ∧ 未撞石 ∧ 未重听」的闸门数
             + 答对的救援题（撞石断链，救援题答对续链 +1，不清零）   // 题
cleanChainBest = max(跨局 cleanChain)                         // 题，写 rally.ear

段位 E1–E6，按近 10 局滑动 firstListen 率 R 与 cleanChainBest：
  E1 起始； E2  R≥0.50； E3  R≥0.65； E4  R≥0.80
  E5  R≥0.90 ∧ cleanChainBest≥8； E6  R≥0.95 ∧ cleanChainBest≥12
```

**观测窗口对齐（FWD-2 §4）**：单次会话观测窗口为「最多 4 局 / 25 分钟」，正确率斜率需 ≥4 局才成立。4 局内的可见进步由 `Δ_first`（每局结果页「比上局 +1」）承担；段位在 4 局内至少可达 **E3**（R≥0.65），E5 / E6 明确标注为 >10 局长线目标，不进 4 局 playtest 判据。周历 7 格跨天累计，4 局内最多推进 4 格，设计侧不设「必须玩满 N 局」门槛。

**题库口径（FWD-2 §4）**：`buildGates()` / `PAIRS_BY_MAP` 零改动；单局 4 对从 ≥8 池洗牌抽取且全局互不重复，`pickQuizPair()` 去重窗口 3。「首错音素再遇改善率」由跨局同 `mapId` 的词池按 `pairKey` / `unit` 自然聚合，可观测、无需为指标改题库，也不把首局做成同一词对。

**规则**：`firstListen` 只做展示，**不进 `scoreRace` 的 acc / stars、不进 place、不改速度**；「再听一次」保持可用（每门 1 次）且断 `combo` 的既有口径不变。结果页写「这局 3/4 一次听准」，不写「重听了 1 题」——避免把可访问性动作变成羞辱。新域 `rally.ear = { firstListenSum, cleanChainBest, recent[10] }`，全部经 `commit()` 增量写入。

#### M3 · 影子条 + 成绩卡

```
s_player = (odo − startOdo) / (laps × L)              // 0~1，syncHud() 已算 frac
s_ghost  = clamp(state.time / bestTime, 0, 1)         // 0~1，bestTime 单位 s
Δt       = s_player × bestTime − state.time           // 秒（等效秒差：影子按 bestTime 匀速）
```

- HUD：`#progress` 追加 1 个影子标记，位置 `s_ghost × 100%`；`|Δt| ≥ 0.3s` 显示「领先影子 1.2s」/「落后 0.6s」，否则显示「并排」。
- **成绩卡**：`R-<base36(code)>`，≤ 12 字符，编码 `{地图 1、星级 1、acc 2、time×10 3、firstListen 1、chain 2、rescue 1、版本 1}`。结果页一个「复制成绩卡」按钮（`navigator.clipboard`，失败则显示可手抄文本）；一个「贴同学码比一比」输入框，本地对比并最多存 5 条到 `rally.rivals`。零后端、零账号。
- 影子是 **HUD 刻度**，不是第 4 辆车 → 首批无需扩展 `js/scene3d-model.mjs` 的 `SNAPSHOT_KEYS` / `KART_KEYS` 白名单。真·半透明幽灵车列为 D4 备选。

#### M4 · 外线宝石链 + 尾流超车

- **外线宝石**：每圈 10 颗 gem 中，3 颗移到 `|lateral| ∈ [0.55, 0.66]`（外线，单颗 **2 宝石**），其余 7 颗保持中线附近（单颗 1 宝石）。单圈理论上限 `3×2 + 7×1 = 13` 宝石（现状 10，+30%）。外线正是 `buildField()` 里石头 `lateral` 的落点区间（`lanes=[-0.55,0,0.55] ± jitter`，clamp ±0.66），所以「贪宝石」与「躲石头」在同一条车道上正面冲突 —— 抉择成立。
- **链奖励**：连续吃到 3 颗外线且中途未回到 `|lateral| < 0.3`，给 **一次 `rocket()` 氮气 0.9s**（`ROCKET.mul=1.55`），不再追加宝石（护住商店经济）。单圈最多 1 次链。
- **尾流**：非分叉窗口内，玩家与某 NPC 满足 `along ∈ [130, 260] unit` 且 `|Δlateral| < 0.22` 持续 `≥1.0s` → 获得 `1.15×` 速度倍率持续 `1.5s`，每局最多 3 次。一旦 `along < COLLIDE.along=130` 即进入既有碰撞判定 → 罚一道听辨题。**风险与收益共用同一个距离带**，孩子自己决定贴多近。
- 该倍率与既有 `BOOST=1.48` / `TURBO=1.92` / `SLOW=0.54` 同级，属于机制层；`DIFFICULTY.speed` 260/300 与 `speedNow()` 判定口径保持不变。落地前需程基岩确认（D3）。
- **基线重标定（FWD-2 C-7）**：尾流 `1.15×` 改变有效速度 → `finishTime` 缩短，B3 EDPM / B1 会话时长 / D1 躲石率基线全部漂移。M4 落地后需按 FWD-2 重标定这三条阈值，**不能沿用旧基线**；D3 推荐「首批只做宝石链」正是把这轮漂移推后到有基线之后。

#### M5 · 周历 7 格 + 本局目标卡

- `openTeach()` 发 1 张目标卡，池：`一次听准 3 题` / `连听 5 题不断` / `一块石头都不碰` / `比影子快 1 秒`。按上一局短板（M1 的近失类型、M2 的 Δ）抽 1 张，每局只 1 条。
- 达成 → `openResults()` 点亮周历 1 格，显示「周历 3/7」；7 格满 → `+30 宝石` + 解锁 1 款车身装饰（`trim-week`，走 `ownedTrims` 并集域）。每周大奖励 ≤1 次。
- 短局咬合：目标全部在**本局 2 圈内**（`≤150s`，判定速度 260/300 下理论 148.1/128.4s）结算，结果页立刻给「再点亮一格」的理由；长线挂四区杯赛 / 30 关地图 / 图鉴，经 `rally.weekly = { year, week, filled }` 按自然周重置。

### 1.3 跨机制一致性自检

| 检查 | 结论与处理规则 |
|---|---|
| 主导策略 | 尾流 1.15× 有撞车罚题风险 + 每局 ≤3 次 + 分叉窗口禁用；外线链奖励给氮气而非宝石，避免「永远贴外线」成为唯一最优解 |
| 经济失衡 | 宝石单圈上限 10→13（+30%）；护身卡 80 宝石由约 4 局缩到约 3.1 局。列为 D3 请用户拍板；链奖励改氮气已把可叠加收益压到 0 |
| 认知过载 | 结果页**恒只有 1 条**近失句；HUD 新增仅 1 个三角 + 1 行 Δt；目标卡每局 1 条；小学生层用 4 个「小结算」切分 2 圈，初中生层给整局数据 |
| 支柱漂移 | 五个机制全部落在「听音选分叉」上：近失算的是闸门题、变强算的是 `gate.replayed`、影子比的是完赛时间、外线/尾流的代价仍是「罚一道听辨题」、周历目标卡全部是听辨目标 |
| 解锁口径 | `rally.unlocked` 的唯一来源保持为「赛事地图完赛答对的门」；M5 奖励走 `ownedTrims`，M3/M2 走全新域，均不触碰 `unlocked` / `stars` / `gems` 的既有写入语义 |

### 1.4 可观测统计与判定链不变式（供 FWD-2 指标直接取数）

| FWD-2 指标 | 本规格对应可观测值 | 取数位置 | 本规格是否改动 |
|---|---|---|---|
| **D1 躲石成功率 0.30–0.90** | 新增只读计数 `state.rockCleared`（成功跳过石头数，0–2）与 `state.rockSeen`（已定案石头数，0–2）；成功率 = `rockCleared / rockSeen` | `settleRock()` 的 `cleared` 分支、`scanPickups()` 的 `settle` 定案处各 +1 计数；经 `result()` 暴露为只读字段 | **判定零改动**：`ROCK_QUOTA=2` / `ROCK_HITS_MAX=2` / `ROCK_HIT_BAND=78`、护身卡抵消、滞空见证逻辑全部保持。§3 的 T−3.0s 预警与 T−1.2s 起跳标线**提高**成功率、M4 外线宝石与石头同车道**降低**成功率，两者是需实测落在带宽内的真实变量，带宽判据归 FWD-2 所有，本规格不另设阈值 |
| **D3 正反馈密度 ≥2 次/局** | `state.cheerSeq`（全局递增序号） | `cheer()` | **零改动**：欢呼词表、`combo≥3→turbo`、跳石 `cheer(1)`、闸门命中 `cheer(combo)` 触发条件逐字保持；§3 只新增 banner 文案与 `rescue` 计数，**不新增任何 `cheer()` 调用**，额外题答对沿用「不给欢呼 / 纸屑」现状，`cheerSeq` 语义纯净 |
| **D2 败局续玩率比** | M1 的 `place=3` 近失句 + `#btn-again` 无提示自主点击 | `openResults()` / `result().place` | 见 §1.2 M1 与「自主性约束」；`placeOf()` 判定零改动 |
| **学习侧斜率 / 首错音素再遇** | `firstListen`(0–4 题) / `cleanChain` / `rescue` / `Δt` | `result()` 追加只读字段 + `rally.ear` | 见 §1.2 M2 与 §3.4；`scoreRace()` 口径零改动 |

**判定链不变式（服务 FWD-2 Q2「喜欢画面 vs 喜欢竞速」判别）**：本规格**零新增纯视觉机制**；§2 年龄分层只覆盖 `css/game.css` 的 `:root` 变量与文案，M3 影子是 HUD 刻度，§4 是听觉反馈。任何分层呈现**不改变** `placeOf()` / `scanPickups()` / `settleRock()` / `judge()` 的判定输入，名次与躲石行为计数保持可测且不被压到 0；M4 反而强化竞速行为（尾流、外线取舍）。

**存档域隔离（服务 FWD-2 §5 埋点，含 C-1 / C-2 / C-6 修正）**：FWD-2 的 `rally.fwd`（9 字段，观测专用）与本规格 `rally.ear` / `rally.shadow` / `rally.rivals` / `rally.weekly` 键名互不重叠，均经 `commit()` 最小变更写回，互不覆盖；这 **5 键须先加入姊妹站 `RALLY_FOREIGN` 白名单**（见 §0 P0 项），否则会被 `save()` 全量写回抹掉。本规格的 `firstListen` / `cleanChain` / `rescue` / `rockCleared` 已由 `result()` 暴露为只读数值，FWD-2 可直接取数、无需重复埋点。
**年龄属性不进共享存档（C-2）**：分层档位改存独立键 `sessionStorage["ipa-rally-band"]`（或 URL `?band=` 仅内存），**不写 `ipa-quest-v1`、不进 `rally.fwd`**；FWD-2 playtest 期间分层由纸质表 / URL 临时指定，`rally.fwd` 不采集任何年龄属性。
**C-6 取数（0 新字段）**：连续游玩天数由 FWD-2 的 `ring` 扩 1 位 `dayOrdinal` 承担，周历 / 段位分别读本规格 `rally.weekly` / `rally.ear`，成绩卡复制次数人工勾选；本规格不为此新增任何存档键。

---

## 2. 同一内核、分层呈现（问题 2）

### 2.1 共用的内核（两档完全共享，零分叉）

听音选分叉的判定链、2 圈 4 门、`DIFFICULTY.speed` 260/300、环境流速增益、石头 / 跳跃 / 额外题、3 辆 NPC、37 词对 / 18 音素题库、四区杯赛、48 精灵六档图鉴、宝石 / 商店 / 3 角色、1~3 星 `scoreRace()`、`ipa-quest-v1` 单键存档、M1–M5 全部五个机制的**规则与数值**。

分层只改**呈现与统计的可见粒度**，机制数值两档一致（唯一的数值差异见 2.4，全部是「显示阈值」与「默认选中项」，不改判定）。

### 2.2 年龄分层矩阵

| 维度 | 6–12 小学生层 `band-kid` | 12–15 初中生层 `band-teen` | 切换实现点 |
|---|---|---|---|
| **视觉语气** | 圆体大字（`--display: ZCOOL KuaiLe`）、暖纸色 `--paper`、精灵拟人、彩带满强度 16 片 / 0.9–1.4s | 同一 3D 赛道，`--display` 覆盖为 `--body`（无衬线）、冷调描边、数字等宽对齐、成绩单式排版；欢呼词与局部彩带**保留**，缩为角标（尺寸 −40%、时长 2.0s） | `body.band-*` 覆盖 `:root` 变量；`css/game.css` 加一组覆盖块 |
| **单局时长呈现** | 仍是 2 圈；每道闸门后给一句「第 1 题达成！」小结算，把 2 圈切成 4 个短段（只一行 banner，零冻结） | 仍是 2 圈；整局当作一次计时赛，只给起跑 / 影子 / 冲线三个节点，无中途小结算 | `judge()` 后按 band 追加 banner；`main.js` `syncHud()` |
| **社交比较强度** | 只跟自己比：本机最好、影子条、周历格子；名次显示为柔和文字 | 名次 / 精确 Δt / 分享码 / 最多 5 个同学码 / 近 10 局 trend；结果页 3 行数据 | `syncHud()` / `openResults()` 按 band 选模板 |
| **奖励颗粒度** | 每门、每石、每格周历都给即时小反馈；4 门集满给一次欢呼 | 局末一次性结算（acc / firstListen / cleanChain / Δt / 名次），局内只保留必要的判定反馈 | `syncHud()` / `openResults()` |
| **技巧深度** | 词对层（`seat ↔ sit`）、默认选中 `follow`(260) 且可改；题型以 `word` 为主 | 音素层（`/iː/ 紧 ↔ /ɪ/ 松`）、默认选中 `listen`(300)；`word/ipa/type` 三题型全开 + 近 10 局错得最多的 3 对弱点表（可点播） | `renderPickers()` / `openTeach()` 默认项；`buildGates()` 的 `forcedTypes` 按 band 调度 |
| **叙事口吻** | 「探险队 / 精灵 / 耳朵变尖了 / 追上小 Q / 石头送了你一道加时题」 | 「赛季 / 计时赛 / PB / 影子 / 误差 / Relay Question / Chain intact」；去拟人化，用数据与赛事术语 | 文案表（§3.3）两列并存，`band-*` 选列 |
| **对比音粒度** | 两词各 1 遍 + 200ms 间隔 + 一声上扬提示；配「嘴角拉开 / 嘴放松」口型话术 | 两词各 1 遍 + 120ms 间隔、无提示音；配「紧 / 松」标签与现成 `hint` 字段 | `audio.playContrast()` 的 `gapMs` 参数 |
| **欢呼与彩带权重** | 全屏可读的大字 `Good/Excellent/Marvellous` 3.4s + 16 片彩带 | 同一词组 + 同一局部彩带，缩为 HUD 角标 2.0s；主视觉让位给数据条 | `syncCheer()` 按 band 调尺寸/时长，**触发条件与词表逐字不变** |

### 2.3 切换入口（三选一，推荐第 ① 个）

| 入口 | 做法 | 适用 | 代价 |
|---|---|---|---|
| ① **首次进入二选一（推荐）** | 标题页加两枚按钮「我是小学生 / 我是初中生」，写**独立键** `sessionStorage["ipa-rally-band"] = "kid" | "teen"`，`body` 立刻加 `band-*` class；**不写 `ipa-quest-v1`** | 直接给出清晰身份，两档都不觉得被当成另一拨人；年龄属性不落共享存档 | 标题页多 2 个按钮；刷新后同会话内保持，换设备需重选 |
| ② 按关卡进度自动 | `rally.maps[].wins` 合计 ≥ 12 或 `unlocked.length ≥ 24` 时自动升到 `teen`，并在标题页提示可改 | 免打扰 | 玩得久的小学生会被误判；**仅作辅助信号**，且不写任何存档 |
| ③ 家长 / 教师开关 | URL `?band=teen` **仅内存生效、不落盘**；玩法面板「家长设置」同样只写上述独立 sessionStorage 键 | 机房 / 班级统一投放；playtest 由纸质表 / URL 临时指定 | 不跨设备持久；需说明如何改回 |

**二值约束**：`band` 只有 `kid` / `teen` 两个取值，所有分层项按二值表取列；CSS 只有两套覆盖块，没有第三套中间态。切换发生在**局间**：局内切设置时，本局口吻保持不变，下一局生效（见 §6）。
**Playtest 伦理边界（FWD-2 C-2）**：`band` 是产品分层**设置项**，不是埋点字段；FWD-2 观测期间不在设备端持久化任何年龄属性，分层由纸质表 / URL 临时指定，`rally.fwd` 不采集该值。

### 2.4 两档差异数值一览（全部为呈现阈值，判定数值不动）

| 参数 | `kid` | `teen` | 单位 |
|---|---|---|---|
| 欢呼词显示时长 | 3.4 | 2.0 | s |
| 局部彩带尺寸系数 | 1.0 | 0.6 | — |
| 对比音间隔 `gapMs` | 200 | 120 | ms |
| 结果页近失句 | 1 行 | 1 行 + 3 行数据表 | 行 |
| 每局中途小结算 | 4（每门后） | 0 | 次 |
| 同学码上限 | 0（隐藏） | 5 | 条 |
| 默认难度选中 | `follow` (260) | `listen` (300) | unit/s |
| 默认题型分布 | `word` 为主 | 三题型全开 | — |

---

## 3. 撞石 → 额外题：做成正向张力（问题 3）

### 3.1 设计支点

石头与闸门抢的是**同一条听觉通道**。让「躲题」变成专注力，靠的是把额外题接进一条孩子能看见的**连听链**：

- 定义 `cleanChain`（§M2）= 连续「答对 ∧ 未撞石 ∧ 未重听」的闸门数 + 答对的救援题。
- **撞石是全场唯一的断链点**，所以石头前一秒孩子会主动把耳朵「腾出来」——不是怕罚，是怕断链。
- 撞了之后，**救援题答对可以续链（+1，不清零）**，于是他愿意认真再听一次；额外题从「惩罚」变成「加时题 / 可炫耀的救援数」。

**保留现状**：额外题独立统计（`quizCorrect` / `quizTotal`）、不扣星、不占闸门题、不进 acc / place / 速度；`pickQuizPair()` 去重窗口 3；`rockHits` 达 `ROCK_HITS_MAX=2` 后静默越过；成功跳石给 `Good` + 局部彩带。以上逐条保持，本机制只在其上叠加语义与计数。

### 3.2 反馈时序（石头前后 0–3 秒，文字版）

| 时刻 | 事件 | 听觉 | 视觉 / HUD | 数据 |
|---|---|---|---|---|
| **T−3.0s** | 石头进入预警里程（≈ `speed × 3` = 780 / 900 unit） | 一声 0.12–0.15s 低音「咔」（复用 `audio.beep(1)` 降增益，零新资产）；引擎增益临时 ×0.5，给耳朵腾通道 | 启用 `state.warning` / `warningT`：「前面有石头 · 别让耳朵断线」 | `warningT` 置 3.0s |
| **T−1.2s** | 进入 `AIR_COVER = 0.5×speed + 78 ≈ 208 / 228 unit`（`jumpLeadT` 已传给 render） | 引擎恢复常值 | 贴地起跳标线亮起（既有渲染）；`#jump` 按钮高亮；小字「保持听的节奏」 | — |
| **T−0.5s** | 起跳窗口开（`airMax = 0.5s`，单跳必过） | — | 触屏「跳」可点 | `player.air` 就绪 |
| **T0 · 跳过成功** | `settleRock()` 判定 `cleared` | `audio.hit()` 之外照常 `cheer(1)` | **`Good` / `Excellent` / `Marvellous` 大字 + 单词周围局部彩带 16 片 + `ribbonT=1.0s`（硬约束 4 原样保留）**；追加一行「没打断 · 连听 4 题」 | `cleanChain` 继续累加，不断链 |
| **T0 · 撞上** | `settleRock()` → `openQuiz("rock")`，**0ms 立即 `audio.playWord(spoken.word)`** | 单词音频起播 | quiz 卡 `eyebrow` 改为「石头送了你一道加时题」；`quiz-prompt` 保留「点喇叭可再听一遍」 | `cleanChain` 记断点；`quizTotal++` |
| **T+0.0–0.85s** | 作答（`finishQuiz()`，仿真冻结 850ms，现状） | 选定后 `audio.hit()`（答对）/ `audio.miss()`（答错） | `ui.quizResult`：「救援成功 · 链续上」/「这次是 `sheep /iː/`」；选项绿 / 红描边（现状） | 答对 `quizCorrect++`、`rescue++`、**cleanChain 续链 +1**；答错 `slow=1.4s` |
| **T+0.85s** | `setMode("racing")`，回赛道 | 引擎声恢复；**A/B 对比音在后台续播**（§4 最小单元，≤1.2s，音频不依赖 mode） | HUD 一行「救援 1 · 耳朵还在热」 | — |
| **T+0.9–2.0s** | 车已合流，环境流速增益继续放大后退相位 | 对比音结束（若下一门 `beginDecide` 已到，丢弃对比音，优先 `playWord`） | 跳过成功分支的欢呼 / 彩带自然淡出 | 对比音队列清空 |
| **T+2.0–3.0s** | 恢复常规 HUD，进入下一门 S1 预告前的空档 | — | 预警与起跳标线收起 | `warningT` 归零 |

**与闸门播音节流的共存规则**：`beginDecide()` 的节流为 `state.time − lastJudgeAt < 2.4s`，临近门线 `dist ≤ speed×0.55` 时强制放行。石头基准 `t=0.4 / 0.82`、闸门 `commitT=0.24 / 0.68`，且 `blocked()` 已用 `ROCK_MARGIN=60` 把石头排除出全部分叉窗口；额外题只刷新 `quizTotal`、保持 `lastJudgeAt` 由 `judge()` 独占。因此本时序的 3 秒窗口落在两门之间，对比音**总时长 ≤1.2s 且不排队**，不挤掉任何一次门播音。

### 3.3 文案措辞表（两档各一列，触发条件相同）

| 触发点 | `band-kid` | `band-teen` |
|---|---|---|
| T−3.0s 预警 | 前面有石头 · 别让耳朵断线 | 障碍接近 · 保持听辨节奏 |
| T0 跳过成功 | Good！没打断，连听 4 题 | Clean · Chain 4 |
| T0 撞击（quiz 标题） | 石头送了你一道加时题 | Relay Question · 链还在，答对续上 |
| 额外题答对 | 救援成功 · 连听链续上 | Saved · Chain intact |
| 额外题答错 | 这次是 `sheep /iː/`，下一题把它抓回来 | 正确 `sheep /iː/` · 你选 `ship /ɪ/` · 紧 / 松 |
| 结果页 | 额外听辨 2/2 · 救援 2 次 · 最长连听 6 | Relay 2/2 · Rescue 2 · Chain 6 · Δt −0.8s |

### 3.4 正向挂接

| 挂接对象 | 规则 |
|---|---|
| 计分 / 星级 / 名次 | 保持现状：额外题独立统计，不进 `acc` / `stars` / `place` / 速度，不占 4 道闸门题 |
| 新增统计 | `rescue`（本局救援成功次数）、`cleanChainBest`（跨局最长连听）；结果页与 `#best` 行可炫耀 |
| 48 图鉴 / 六档稀有度 | 救援数累计写 `rally.ear.rescueTotal`；**长线兑换方式见 D2**（推荐走周历 / 车身装饰，保持 `rally.unlocked` 唯一解锁来源不变） |
| 短局长线 | 每次救援成功给周历目标卡「一块石头都不碰」以外的补位进度：连续 3 局有救援 → 周历额外 +1 格（每周上限 1 格） |
| 欢呼与彩带 | 硬约束 4 逐字保留；额外题答对沿用现状「只给正确性反馈、不额外弹欢呼/纸屑」，防止把撞石变成娱乐 |

---

## 4. 听辨反馈紧贴刺激（问题 4）

### 4.1 支点：判断**之后**立刻对比，判断之前只给一次刺激

判断前给 A/B 会把听辨变成记忆任务，且可能污染「哪边是听到的词」。因此：
- 判断前：**只播 1 次** `spoken.word`（现状 `beginDecide()`），S1 预告牌保持零信息中性 `◇`（现状）。
- 判断后：**≤80ms** 内给最小反馈单元，其中核心是 **A/B 并排对比音** —— 让耳朵在刚做完判断、差异还在听觉记忆里时，听到「我选的 ↔ 另一个」。

复用资产：`audio/` 下已有 74 个预生成美式人声 mp3（`en-US-AriaNeural`），`ship/sheep`、`sit/seat` 等最小对立对齐全；`js/config.js` 每对已带 `word` / `ipa` / `label` / `length` / `hint` 字段。**零新增音频资产**。

### 4.2 闸门前后 0–2 秒时序（文字版）

| 时刻 | 事件 | 听觉 | 视觉 / 数据 |
|---|---|---|---|
| **T−0.6s** | `dist ≤ D_preview`（`span·L + 0.5·preview·speed ≈ 1482 / 1620 unit`）进入 S1 | 引擎 / 环境流（增益 1.6 放大后退相位，现状） | 两块中性 `◇` 预告牌，同帧同尺寸零答案信息（现状） |
| **T−0.0s** | `beginDecide()`，`lead = span·L·0.55 + 360 + speedNow×0.62` | `audio.playWord(spoken.word)` **单次刺激**；`reveal arm=0.55s → hold 3s` 选择窗口 | S2 两块牌显示 `word / ipa / 紧音·松音`；可按 `E` / `#replay` 再听一次（**单播、断 combo，口径保持**） |
| **T+0.00s** | `player.odo ≥ g.line` → `judge()`，判定延迟目标 **≤80ms** | 答对 `audio.hit()`（660Hz 0.08s + 880Hz 0.14s）；答错 `audio.miss()`（196Hz 0.18s） | 答对 `boost=2.8s` / `cheer(combo)` / `state.correct++`；答错 `slow=0.85s` / 对手前推（现状全部保持） |
| **T+0.08–0.30s** | **A/B 对比音起播** `playContrast()` | 两词各 ≈0.45–0.60s，`gapMs` 200(小) / 120(初)；**答错顺序 = 正确词在前**，答对顺序随机（与左右车道无关） | banner 同步（`T+0` 起 1.35s / cheer 3.4s） |
| **T+0.30–1.20s** | 对比音结束 | — | banner 写「错在哪」三层：① 词面 `sheep ↔ ship`；② 音标 `/iː/ ↔ /ɪ/`；③ 现成 `length` / `label` / `hint`（「嘴角拉开，肌肉绷紧」↔「嘴放松，轻轻一收」） |
| **T+1.20–1.35s** | 反馈单元收口 | 对比音队列清空 | 车已过门线并合流；环境流速恢复；答错 banner 淡出 |
| **T+1.35–2.00s** | 空档 → 下一门预告 | 若下一门 `beginDecide()` 已触发，**丢弃未播完的对比音，优先 `playWord`** | 闸门反馈链路零冻结、零面板、零额外输入（撞石额外题的 850ms quiz 窗口不受此约束） |

### 4.3 最小反馈单元（三类，各自上限）

| 单元 | 组成 | 时长上限 | 是否冻结仿真 | 是否改判定 | 是否新增资产 |
|---|---|---|---|---|---|
| **闸门答对** | `hit()` 双音 + 一行 `Good · sheep /iː/` + A/B 对比音 + `boost 2.8s` | **≤1.3s** | 否 | 否（沿用 `judge()` 全部数值） | 否 |
| **闸门答错** | `miss()` + 一行 `是 sheep /iː/ · 你开进了 ship /ɪ/` + A/B 对比音（正确在前）+ 现成 `hint` | **≤1.35s** | 否 | 否（沿用 `slow=0.85s`） | 否 |
| **额外题（救援）** | `hit()` / `miss()` + `ui.quizResult` 并排词 + 同一对比音在回 racing 后后台续播 | **≤1.2s**（跨 850ms 窗口续播） | 仅既有 850ms 答题窗口 | 否 | 否 |

「错在哪」只用 `js/config.js` 已有的 `length`（长/短）、`label`（紧音/松音/清音/浊音…）、`hint`（口型提示）与 `ipa`，**不编造毫秒时长数值**。

### 4.4 实现口径（零新资产、零判定改动）

- `js/audio.js` 新增一个导出 `playContrast(a, b, { gapMs, order })`：内部用现有 `playWord()` + `el.onended` 链串起两个词，`stopWord()` 语义不变；若 `speaking === true`（上一门音频未完）则**直接丢弃本次对比音**，不排队、不堆积。
- `js/race.js` `judge()` 的答对 / 答错两个分支各加 1 次调用（传入 `gate.spoken` / `gate.other`）。
- `js/main.js` `pickQuiz()` 加 1 次调用（传入 `q.spoken` 与另一选项）。
- `reveal arm 0.55s` / `hold 3s` / 节流 2.4s / `lastJudgeAt` 归属 / `gate.replayed` 单播口径，全部保持不变。

### 4.5 三条硬规则（保证闸门反馈链路不打断赛车节奏）

1. **闸门反馈链路不冻结**：对比音期间 `mode` 恒为 `racing`，`race.update()` 照常推进，`state.time` 照常累加。**范围限定为闸门判断→反馈链路**；撞石时 `openQuizCard()` 必然 `setMode("quiz")`，`finishQuiz()` 的既有 **850ms 答题窗口完整保留**（硬约束 2，不属于本条约束，见 §3.2 / §4.3）。
2. **不抢麦**：对比音总长 ≤1.2s，且遇到 `beginDecide()` 到点即丢弃；闸门 `playWord` 永远优先。
3. **不增输入**：孩子零新增按键 / 零新增点击；「再听一次」保持单播且断 combo 的既有语义。

**断言归类（FWD-2 C-5）**：`判断→反馈 ≤80ms` / `最小反馈单元 ≤1.35s` / `A/B 对比音 ≤1.2s` / `4 门 × 对比音触发率` 是**工程时序门控断言**，需在 `judge()` 两分支加打点才能取得，无法从 localStorage / `__rally` getter 读出，**不列为 playtest 的产品成功证据**。学习侧可从存档取证的是：正确率随局数斜率、首错音素再遇改善率、`firstListen` 的 `Δ_first`（见 §1.2 M2 与 §1.4）。

### 4.6 两档差异

小学生层用 200ms 间隔 + 上扬提示音 + 口型话术（「嘴角拉开」）；初中生层用 120ms 间隔、无提示音、改用「紧 / 松」标签与 `hint`，并在结果页给「近 10 局错得最多的 3 对」弱点表（点播复听）。反馈**时序与三类最小单元两档完全一致**。

---

## 5. Top3 首批实现项（问题 5）

### 5.1 排序（按「愿意玩」预期收益，从高到低）

| 序 | 机制 | 为什么排这里 | 杠杆 | 改动面 | 预期可观测收益 |
|---|---|---|---|---|---|
| **1** | **M1 近失缺口 + 带目标的「再跑一场」** | 唯一直接作用于「动机产生那一秒」的机制；改动全在结果页 | 最高 | **最小**：纯表现层 + 只读已有存档字段 | 结果页 → 再跑一场的点击率 |
| **2** | **M3 影子条 + 成绩卡** | 一次给全「同伴 / 异步成绩 / PB / 名次」的可比较对象，让每一局都有对手 | 高 | **小**：HUD 一个刻度 + 结果页一个码 | 人均局数、成绩卡复制/粘贴次数 |
| **3** | **M2 一次听准率 + 最长连听** | 给「我变强了」的证据，并把 M1 的缺口具体化到「哪一个词」 | 高 | **小**：只读 `gate.replayed` + 新统计域 | 连续游玩天数、段位 E1→E6 迁移 |

M4 / M5 排第 4 / 5：M4 有操作门槛且需工程确认倍率口径，M5 是长线、见效慢。**§3（撞石正向张力）与 §4（A/B 对比音）对「真的练到」是最高杠杆，按本派单「愿意玩」的排序口径不进 Top3，列为紧随第二批（5.3）。**

### 5.2 逐项影响面（只读盘点，精确到文件 / 函数 / 行段；本轮不改代码）

#### Top1 · M1 近失缺口

| 文件 | 位置 | 用途 |
|---|---|---|
| `js/main.js` | `openResults()` 835–905（结果页 HTML 模板、`#btn-again` → `beginCountdown()`）、`refreshBest()` 251–256（`#best` 文本） | 追加 1 条近失句 + 按钮文案；读取既有 `raw` 字段 |
| `js/config.js` | `scoreRace()` 319–325 | 只读引用 `acc≥0.4 / 0.6 / 0.8` 与 `place≤2` 阈值 |
| `js/race.js` | `result()` 876–897 | 只读 `place / correct / total / time / misses / hits / unheard / quizCorrect / quizTotal` |
| `js/main.js` | `commit()` 234–249 | 只读 `rally.EP02.{stars,bestAcc}` / `rally.maps[id].{bestTime,bestAcc}`；**字段已存在，无需新增 schema** |
| `index.html` | `#best`(67)、`#panel-results`(167) | 承载近失行 / 结果页 |
| `css/game.css` | 结果页样式区 | 新增 1 个 `.near-miss` 行样式 |

**首批改动范围限定为**：`js/main.js` 结果页与 HUD 文本、`css/game.css` 一行样式。判定层、`js/race.js` 判定链、题库、`js/scene3d-model.mjs` 白名单、3D bundle `assets/p1/scene3d.js`、`rally.unlocked` 解锁口径均保持原样。

**Top1 实现约束（FWD-2 C-3 / C-8）**：M1 只改结果页文案与 `#btn-again` 的**显示文案**，**不改绑定链** —— `#btn-again.onclick` → `beginCountdown()`、`openResults()` 内的 `commit()` 调用点原样保留，供 FWD-2 埋点挂在同三处（M1/M2/M3 恰好都改这三处）。M1 落地前须先完成中性按钮基线标定（见 §1.2「测量仪器约束」），否则 A1 VRR / A2 阈值不可比。

#### Top2 · M3 影子条 + 成绩卡

| 文件 | 位置 | 用途 |
|---|---|---|
| `js/main.js` | `syncHud()` 798–833（`frac` 已算）、`openResults()` 835–905、`commit()` 234–249 | 追加 `s_ghost` / `Δt` / 成绩卡按钮 / 同学码贴入；新增 `rally.shadow` / `rally.rivals`（≤5 条）两个域 |
| `index.html` | `#progress`(26)、`#panel-results`(167) | 进度条追加 1 个影子标记元素 |
| `css/game.css` | `#progress` 及 `:root` | 影子标记定位；`band-*` 变量覆盖（与 §2 共用） |
| `js/render.js` | `minimapModel(view)` 的 `progress` | 仅 **L2 真·幽灵车**备选才用；首批不动 |
| `js/scene3d-model.mjs` / `assets/p1/scene3d.js` | `SNAPSHOT_KEYS` / `KART_KEYS` 白名单 | **首批不动**：影子是 HUD 刻度，不是第 4 辆车 |

#### Top3 · M2 一次听准率 + 最长连听

| 文件 | 位置 | 用途 |
|---|---|---|
| `js/config.js` | `buildGates()` 273–308 | 只读既有 `gate.replayed:false` 字段，**无需改 buildGates** |
| `js/race.js` | `judge()` 241–295、`update()` replay 分支 746–752、`result()` 876–897 | 累计 `firstListen` / `cleanChain`；`result()` 追加两个展示字段 |
| `js/main.js` | `openResults()` 835–905、`commit()` 234–249 | 结果页追加「这局 3/4 一次听准 · 比上局 +1」；新增 `rally.ear` 域（滑动 10 局） |
| `js/main.js` | `scoreRace()` 调用链 | **口径逐字不变**：`firstListen` 不进 acc / stars / place / gems / unlocked |

### 5.3 紧随第二批（不占 Top3，对「练到」最高杠杆）

| 批次项 | 影响面 | 说明 |
|---|---|---|
| §4 判断后 A/B 对比音 | `js/audio.js`（新增 `playContrast`）、`js/race.js` `judge()` 两分支、`js/main.js` `pickQuiz()` | 复用 74 个既有 mp3，零新资产；是本规格里「听辨自动化」的唯一直接机制 |
| §3 撞石正向张力 | `js/race.js` `state.warning` / `warningT`（启用死字段）、`settleRock()` / `finishQuiz()` 文案与计数、`js/main.js` `openQuizCard()` / `pickQuiz()` 文案 | 与 Top1–3 共享 `cleanChain` / `rescue` 统计域 |
| §1.4 可观测统计 getter（FWD-2 D1 取数） | `js/race.js` `settleRock()` 的 `cleared` 分支、`scanPickups()` 的 `settle` 定案处各 +1 计数；`result()` 暴露 `rockCleared` / `rockSeen` / `firstListen` / `cleanChain` / `rescue` | **纯统计增量，零判定改动**；随 §3 同批落地，供 FWD-2 直接取数，不重复埋点 |
| M4 / M5 | `js/race.js` `buildField()` / `scanPickups()` / `resolveContacts()`、`js/main.js` `openTeach()` / `openResults()`、`css/game.css` | 待 D2 / D3 拍板后落地 |

### 5.4 明确保持不动的面

判定层速度常量 `260 / 300`、`speedNow()` 口径、`TUNING.laps=2` 与 `commits`、`buildGates()` 的门生成与题库、`scoreRace()` 星级公式、`rally.unlocked` 唯一解锁来源、`js/scene3d-model.mjs` 的白名单投影、预构建 bundle 的接线方式、`index.html` 的 3D 降级链、姊妹站共享键 `ipa-quest-v1` 的 `commit()` 协议（`RALLY_FOREIGN` 白名单扩展属**新增键**、不改协议，见 §0 P0 项）。

---

## 6. 边缘情况与处理规则（≥3 类）

| # | 情形 | 处理规则 |
|---|---|---|
| 1 | **首局 / 无历史成绩** | `bestTime` 缺失时影子条隐藏、Δt 不显示；M1 输出「第一局已建档」句式；M2 的 `Δ_first` 显示为「首次记录」，不显示负数 |
| 2 | **撞石与分叉窗口相邻** | `blocked()` 已用 `span·L ± ROCK_MARGIN=60` 排除分叉窗口，石头与闸门不重叠；额外题 / 对比音均不刷新 `lastJudgeAt`，2.4s 播音节流与 `dist ≤ speed×0.55` 强制放行规则保持 |
| 3 | **`rockHits` 达上限 2 或护身卡抵消** | 静默越过 / 抵消撞击：不出额外题、`rescue` 不增长、`cleanChain` 不断；**起跳标线与 T−3.0s 耳朵预警照常给出**，专注训练不被跳过 |
| 4 | **连续同词 / 对比音堆积** | `pickQuizPair()` 去重窗口 3、`buildGates()` 单局 4 对不重复；`playContrast()` 遇 `speaking===true` 直接丢弃，任何时刻最多 1 串对比音 |
| 5 | **localStorage 写失败（隐私模式）** | 所有新统计（`rally.ear` / `shadow` / `weekly` / `rivals`）降级为局内内存展示，`commit()` 既有 try/catch 兜底；比赛不中断、不弹错 |
| 6 | **局中切换年龄档 / 刷新页面** | 本局 `band` 冻结到完赛，下一局生效；刷新后从独立键 `sessionStorage["ipa-rally-band"]` 恢复（无值回默认 / 按 URL），**不读共享存档**；局内统计清零（`state` 本就是局内对象） |
| 7 | **按了「再听一次」后答对** | `firstListen` 不计该题，但 `hit` / `state.correct` / `combo` 断开 / 星级全部按现状口径处理；结果页只写正向的「一次听准 3/4」 |
| 8 | **额外题与下一门几乎同时** | 对比音允许跨 850ms quiz 窗口后台续播（音频不依赖 `mode`）；一旦 `beginDecide()` 触发 `playWord`，对比音立即让位 |
| 9 | **多标签 / 姊妹站并发写存档（含 C-1）** | 全部新域经 `commit()`「写入瞬间重读整对象 → 最小变更」；`gems` / `shields` 继续走 delta；`ownedPaints` / `ownedTrims` 继续走并集兜底。**前置**：`ear/shadow/rivals/weekly/fwd` 5 键须已加入姊妹站 `RALLY_FOREIGN`，否则已打开的大闯关标签 `save()` 会 `refreshFromRaw()` → `writeRaw()` 全量写回并静默抹掉全部新域（见 §0 P0 项）；白名单未扩时新域一律降级为局内内存展示 |

---

## 7. 需要用户拍板的决策点

| 编号 | 决策 | 选项 | 推荐 | 影响 |
|---|---|---|---|---|
| **D1** | 年龄分层切换入口（**C-2 修正**） | ① 首次二选一写独立 `sessionStorage["ipa-rally-band"]`；② 按关卡进度自动升档；③ URL `?band=` 仅内存 / 玩法面板开关；①+③ 组合 | **①+③**：分层档位**不写 `ipa-quest-v1`、不进 `rally.fwd`**；playtest 期间由纸质表 / URL 临时指定 | 决定标题页是否加 2 枚按钮；二值 `kid/teen` 无中间态；共享存档白名单因此只需扩 4 域 + `fwd` 共 5 键 |
| **D2** | 「救援题」长线挂接到哪 | ① 只给结果页炫耀 + 周历格，`rally.unlocked` 唯一解锁来源保持；② 满 5 次救援解锁 1 款车身装饰（`trim-week` 走 `ownedTrims`）；③ 满 5 次救援保底抽 1 张音标卡 | **①+②** | ③ 会打破「音标卡唯一解锁来源 = 赛事地图完赛答对的门」这一现有口径，需明确授权才可做 |
| **D3** | M4 的外线宝石经济与尾流倍率 | ① 外线 3 颗 ×2 宝石（单圈 10→13，+30%）+ 尾流 1.15×；② 只做外线宝石链、尾流留到后续；③ 两者都留到后续 | **②**（首批先做「为宝石偏离最优线」） | ① 使护身卡 80 宝石由约 4 局缩到约 3.1 局；尾流 1.15× 与 `BOOST/TURBO` 同级但属机制层新增倍率，需程基岩确认不触碰 260/300 判定口径；**落地后需按 FWD-2 重标定 B3 EDPM / B1 会话时长 / D1 躲石率阈值（C-7）** |
| **D4** | 影子的呈现层级 | ① HUD 影子刻度（首批，零 3D 改动）；② 真·第 4 辆半透明幽灵车 | **①**，② 另立一轮 | ② 需扩 `js/scene3d-model.mjs` 的 `SNAPSHOT_KEYS` / `KART_KEYS` 白名单 + `js/render.js` 绘制 + 重建 `assets/p1/scene3d.js` bundle，改动面显著变大 |
| **D5** | 同伴比较做到哪一步 | ① 纯本地成绩卡 / 同学码（≤5 条，零后端）；② 真·班级榜 | **①**，② 另立需求 | ② 需账号 / 后端 / 云服务，超出本轮「只读盘点、静态站」边界 |
| **D6** | 初中层欢呼词的呈现权重 | ① 保留 `Good/Excellent/Marvellous` + 局部彩带，缩为角标（尺寸 −40% / 2.0s）；② 两档完全同权重 | **①** | 硬约束 4 的触发条件与词表逐字不变，仅调尺寸 / 时长；请确认「缩小权重」符合「给欢呼 + 局部彩带」的原意 |
| **D7** | 对比音在额外题窗口的续播 | ① 保持 850ms 回 racing，对比音后台续播 ≤1.2s；② 把回 racing 延到 1.25s 等音频播完 | **①** | ② 会多 0.4s 冻结，与「不打断赛车节奏」冲突；① 靠 §4.5 的让位规则兜底 |

---

### 附：本规格的验收总口径（供下一轮门控引用）

1. 结果页恒有且仅有 1 条近失句，「再跑一场」按钮含具体目标；**M1 为处理组，落地前先跑中性按钮基线并分开标定阈值**（§1.2 测量仪器约束 / FWD-2 C-3）。
2. `firstListen` / `cleanChain` 只做展示，`scoreRace()` 的 acc / stars / place 逐字不变。
3. 影子为 HUD 刻度，3D 白名单与 bundle 零改动。
4. 成功跳石的欢呼词表、局部彩带、`ribbonT` 全部保持；额外题独立统计口径保持。
5. **闸门判断→反馈链路**零冻结（对比音期间 `mode === "racing"`）；撞石额外题保留既有 850ms `quiz` 窗口、`finishQuiz()` 后回 racing（硬约束 2）。`≤80ms` / `≤1.35s` / `≤1.2s` / 对比音触发率四项为**工程时序门控断言**，不作 playtest 产品成功证据（C-4 / C-5）。
6. `DIFFICULTY.speed` 260 / 300、`TUNING.laps=2`、`commits=[0.24,0.68]`、`rally.unlocked` 解锁来源、`ipa-quest-v1` 的 `commit()` 协议均保持不变。
7. `#btn-again` 保持单一按钮、无提示自主点击，且**只改显示文案、不改 `onclick` / `commit()` / `beginCountdown()` 绑定链**（C-8）；`cheerSeq` 触发链、`placeOf()` / `scanPickups()` / `settleRock()` / `judge()` 判定输入、`buildGates()` 题库抽取逐字不变。
8. `state.rockCleared` / `state.rockSeen` 为只读统计（D1 的分子 / 分母）；`rally.fwd` 与本规格四个新域键名隔离；分层档位 `band` 存独立 `sessionStorage` 键、**不进 `ipa-quest-v1` / `rally.fwd`**（C-2）。
9. **落地前置（C-1）**：姊妹站 `RALLY_FOREIGN` 已一次性加入 `ear` / `shadow` / `rivals` / `weekly` / `fwd` 共 5 键，否则第 2、7、8 条涉及的新域会被 `save()` 全量写回覆写。
