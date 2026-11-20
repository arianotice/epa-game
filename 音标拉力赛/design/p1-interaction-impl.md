# 音标拉力赛 · P1 交互工程实现规格（E1）

> ## ⚠ 实施口径覆盖声明（team-lead · 2026-11-14 · 优先级高于本文件全部正文）
>
> 用户 2026-11-14 通过选择工具最终拍板 **「只做单跳必过」**，推翻此前「一次跳完美过 + 双击跳更高」两条都做的解读。本文件撰写时尚未收到该拍板，以下章节**整段作废、不得实现**（原文保留作历史留痕，不删除、不改写）：
>
> - **§A2（原 :29-50）**：260ms 双击输入事件间隔、`fireJump()`、`input.jump` / `input.jump2` 双沿产出 —— 作废；但该节「`hopWindow` 是死代码、删除」「容错目标由滞空见证式承接」「二段跳不是单跳通关前提」仍生效。
> - **§2.2「二段跳 260ms 状态机」**：`lastJumpAt` / `jump2Edge` / `readInput()` 扩 `jump2` / `race.js` 消费 `input.jump2` / `hop===2` / `airMax 0.5→0.74` / `PN-JUMP-02/04/05` 二段验收 —— 全部作废。**仅保留**「删 `dashLeft=140` / `jumpCd` / `mk()` 对应字段 / `updateKart:293-297` 额外 `odo` 分摊 / `updateKart:279` 递减」与 `PN-JUMP-03` 的 `blockSplitter` 护栏例外。
> - **§A4 `js/main.js` 行**：`fireJump()` 260ms 状态机 + `input.jump2` —— 作废；同行其余项（`syncCheer()` 序号去重、`burstConfetti()` 局部彩带、半屏 `onHalfTap`、`window.__rally` getter 扩、`syncFork()` 清理、`merge:0.012` 统一）仍生效。
> - **§3 `PM-3`**：「补 260ms 窗内第二击生效、窗外不生效」—— 作废；`PM-2`「键盘 + 半屏两来源投影方向一致」仍生效。
> - **§4.2「双沿事件字段名（定稿）」整节** + `window.__rally.get jumpEvents()` 的 `edge:"jump2"` 分支 —— 作废；若保留 `jumpEvents` 只读环形缓冲，只记 `edge:"jump"` 单边沿。
> - 视觉层两级 `lift`（单跳 `0.55m` / 二段 `0.85m`）统一收敛为 **单级 `lift=0.55m`**（`h_rock=0.32m` 半埋）；双击空格 / 触屏点两下**无任何额外效果**。
>
> **仍完整生效**：§1 根因定位、§2.1 单跳必过 + 滞空见证式、`PN-JUMP-00` 为唯一 P0、§2.3 撞石 ≤2 整数硬上限、§2.4 词表 `Good / Excellent / Marvellous` + `c.seq`、§2.5 NPC（阈值以 `qa.md` 为准取 `0.94 · v_player_now`）、§2.6 半屏点选 + 键盘左右并存、§2.7 方案 B `VISUAL_FLOW_GAIN` 只作用渲染层、§2.8 3D 只读几何、§0 ADR-2 双锚定重锚、§4.1 / §4.3 / §4.4 / §4.5。
>
> **口径优先级**：用户最新拍板 > 本覆盖声明 > 本文件正文 > 其余三份规格。`qa.md` v1.2 已同步作废对应 `PN-JUMP-02/04/05/06` 与 R-2。
>
> **3D 构建链补正（前序规格未写明，实现必读）**：浏览器实际加载 `assets/p1/scene3d.js`（esbuild IIFE bundle，1.16 MB），**不是** `js/scene3d.jsx` 源码。改完 `js/scene3d.jsx` / `js/scene3d-model.mjs` 后必须跑 `npm run build:p1`（`js/build-p1.mjs`）重建 bundle，否则 3D 石头/分叉几何不会出现。统一 bump `?v=` tag 时须同步 `js/build-p1.mjs:40` 写死的 `hud-20261108` 字面量护栏，并遵守该文件 `.setItem(` / `.webp|.png` / `fogType` 零命中约束。

> **IMPL-1A 未解决① 裁定（team-lead · 2026-11-14 · 回执后逐行复核代码）**：跨圈复位只清 `state.pickups[].taken/armed/cleared`，**`state.rockHits` 整局累计、跨圈不复位**（跨圈分支注释 + `settleRock()` 在 `openQuiz("rock")` 前的 `rockBudget` 封顶）。裁定 **保持现状、不修改跨圈语义**：① 用户硬口径「每局撞到石头次数 ≤2」由 `rockHits` + `rockBudget=2` 严格保证，第 2 圈重现不会多撞，也不再计入 `quizReasons.rock`；② `PN-ROCK-05a`「生成总数 ≤2 颗」指 `state.pickups` 中 rock **条目配额**（实跑恰 2 条），**不是**「整局出现次数 / 交互次数 ≤2」，规格措辞按此澄清；③ 两圈赛道本就重复跑，同位置重现是可预期的，不属于「随机出现让用户碰上」；④ 若封顶后把石头做成不可交互的假障碍，正是 `visual.md` v1.4 明令禁止的 L1/L2 混淆。质量线在 `remap.md` 与 `PN-ROCK-05a` 措辞中按此登记，**不得把「跨圈重现」判为 FAIL**。
>
> **IMPL-1A 未解决③ 已闭环**：本文件顶部覆盖声明（15:35 落盘）已作废 §A2 / §2.2 / §A4 / §3 PM-3 / §4.2 的 260ms 二段跳内容；`qa.md` v1.2 已作废 `PN-JUMP-02/04/05/06` 与 R-2。工程线按「用户最新拍板 > impl.md」实现，方向正确。

> **文件性质**：engineering-lead 程基岩 · **只读盘查 + 精确根因定位 + 可直接落地的工程实现规格**（规范性文档，非实现、非测试证据）。
> **任务**：E1 —— 定位「只点一次空格键跳不过石头」精确根因 + 写完整工程实现规格。
> **边界（逐字遵守）**：本轮**只写本文件**；**产品代码零改动**、未跑任何门控、未改任何 `verify_*.py`、未 commit / push、未部署。所有 `文件:行号` 均经本轮 `Read` / `Grep` 逐条以当前磁盘复核。
> **上游**：`design/p1-interaction-spec.md` v1.2（design-strategist 裁定书，只给交互口径、P11 把实现载体交 E1 定夺）、`design/p1-interaction-visual.md` v1.2（art-director 视觉规格，方案 B 已拍板）、`design/p1-interaction-qa.md` v1.0（quality-lead 最终回归计划，含批准登记与 `PN-*` 判据）、engineering-lead R1 玩法盘查、`result.json`（`REAL_RUN` 121 PASS / 0 FAIL）。
> **生效**：依据用户 2026-11-14 最终拍板 + team-lead 2026-11-14 E1 补充取证（质量线磁盘纠错）。
> **术语**：简体中文；技术术语 / 代码标识符保留原文。`unit` = 判定里程单位（`diff.speed=260/300 unit/s`），`m` = 3D 米制（`WORLD_SCALE=0.008`），二者换算 `1 unit = 0.008 m`，**严禁混算**（§1.3）。

---

## A. 决策级结论速查（E1 优先交付 · 4 项 + 视觉对齐 + P4 + 改动清单）

> 主理人 2026-11-14 催交「先交结论、长清单后补」。本节自包含，可直接据此拍板；`§0` 之后为完整全景规格（已落盘，明细不再扩写）。

### A1. P0「单跳跳不过」根因主因排序（证据 + `文件:行号`）

| 序 | 裁定 | 证据 | 层级 |
| --- | --- | --- | --- |
| ① | **主因 · 时机不可判**：3D 完全没有 pickups 几何 → 玩家看不见石头、判断不了「该在哪一段点一次」 | `SNAPSHOT_KEYS`(`scene3d-model.mjs:64-66`) 无 `pickups`；`scene3d.jsx createWorld()`(:190) 无石头/宝石 mesh | 3D 层 |
| ② | **主因 · 判定侧点采样**：首帧进 `±78` 窗口即 `item.taken=true` 并**仅该帧**判 `air>0.05`；`hopWindow` 死代码使「提前起跳宽容窗」从未生效 | `scanPickups()` `race.js:566-595`（`:574` 锁定 / `:578` 点采样）；`air` 有效窗 `0.45s`=117unit(follow)/135unit(listen)（`:283` 逐帧 -dt、`airMax=0.5` :650），碰撞带共 156unit、通过 0.600/0.520s；`hopWindow`(`:284-285`) 只递减、全项目零赋值零读取 | 判定层 |
| ③ | **主因 · 视觉穿石**：`lift=air*0.008≈0.004m` 几乎不可见；3D 石头外露 0.72–0.96m > 原单跳 `lift` 0.45m → 画面穿石；`KART_KEYS` 缺 `hop/airMax` 一段/二段无差 | `scene3d-model.mjs:209`、`:67-69` | 3D 层 |
| ④ | **次因**：`hold` 决策 3s 冻结吞掉石头前起跳 | `race.js:631-641` `return` 不处理 jump（jump 在 `:643` 后）；`blocked()`(`:114-120`) 仅排 `±0.04L=770unit` < 真实分叉窗 1475.1/1559.1unit，第 5 石 `t≈0.62875` 落入 listen 窗 `[0.62703,0.70800]` | 判定层 |
| ⑤ | **非主因但必删**：`dashLeft=140` 按 900/s 推 odo | **仅二段跳 `hop===2` 产生，单跳不触发**（`:660`/`:293-297`）；违反「水平速度不变」+ 污染 `blockSplitter` 回滚 | 判定层 |
| — | **非主因**：`jumpCd=0.9` 只在二段跳分支、不拦首击；`e.repeat`(`main.js:317`) 只拦按住重复、不影响单次边沿 | `race.js:661`/`:279`、`main.js:317/:320` | — |

**一句话**：主因是「①看不见（时机）+ ②首帧点采样（无容错）+ ③穿石（观感）」三者叠加；**不是「高度不够」**——把 `lift` 调高只治 ③ 观感，治不了 ①②。故「单跳必过」必须同时修 3D 可见性 + 判定式，非单纯加高。

### A2. 跳跃实现载体三选一（权威结论）+「一次点击必过」保证式

**裁定：新建独立状态机（`main.js` 输入层）+ 判定侧「滞空见证式」；`hopWindow` 死代码删除、不复活；不单独「收窄 `air` 判定」。**
- 「收窄 `air`」反向：`0.05` 收窄只会让容错更小，与「单跳必过」相悖；应**放宽**为窗内任一帧 `air>0`（§2.1）。
- `hopWindow` 语义是「起跳后宽容窗口」，与 260ms 双击**输入事件间隔**完全不同，拿它当二段跳计时器是语义错配 → 删 `:284-285`，容错目标由滞空见证式承接。
- 260ms 状态机放 `main.js`（`performance.now()` + `lastJumpAt`），产出 `input.jump`/`input.jump2` 两个布尔边沿；`race.js` 只消费、保持 `headless_laps.mjs:30-33 seeded()` 确定性（≥1000 seed 硬验收依赖）。**二段跳不是单跳通关前提**。

**「一次点击必过」保证式（绑 `air` 有效窗覆盖石头碰撞区，不绑双击）**：
- 判定层：`scanPickups()` 改「滞空见证式」——进入 `|Δodo|<=78` 且同车道窗口内**任一帧** `(player.air||0)>0` 即 `item.cleared=true`，出窗/落地定案 `cleared?规避:撞击`（§2.1）。`air>0` ⇔ 本次起跳未落地（`:287` hop 未复位），容错窗 = 通过窗 ∩ 滞空窗，与 `hop===2` 无关；`PN-JUMP-00` 绑此量、`hop===1` 即完成。
- 视觉层 `lift` 与 `air` **共用同一归一化相位**，杜绝两套常数漂移：
  ```
  p       = 1 - air/airMax          // ∈[0,1]；p=0 起跳、p=1 落地；air 由 race.js:283 逐帧 -dt 驱动
  lift(p) = peak(hop) · sin(π·p)   // peak(1)=0.55m, peak(2)=0.85m（美术线 v1.2 定稿）
  H_ROCK  = 0.32m                   // 半埋外露高，scene3d-model.mjs 顶部导出常量，几何/判定共用
  // 走 scene3d.jsx:257 现成 k.lift y 通道，0 新增 mesh；airMax 为唯一常数来源
  ```
- **诚实标注数值张力（须拍板）**：`lift>H_ROCK` 时段占滞空比例 = `1 - 2·arcsin(H_ROCK/peak)/π` → 单跳 0.55m 为 **60.6%**、二段 0.85m 为 **74.8%**；判定带通过 `T_band=156/speed` = 0.600s(follow)/0.520s(listen)，单跳滞空 = `airMax=0.5s` → `T_clear=0.303s < T_band`。**严格字面「lift 全程压过 h_rock 并覆盖整个 78unit 判定带」在现 `airMax` 下不成立**：
  - **选项甲（工程推荐，零判定手感改动）**：不改 `airMax`；「覆盖」由「贴地起跳标线 + 滞空见证式」保证——标线置石头前 `AIR_COVER = airMax·speed + 78 ≈ 195/213 unit`，起跳时 `p=0`、进窗时 `p≈0.4–0.6`（lift 峰值段），窗内任一帧 `air>0` 即见证规避。**E1 规格按甲落地**。
  - **选项乙（严格字面）**：延长单跳 `airMax ≥ T_band/0.606 = 0.99s`(follow)/`0.86s`(listen)；代价 = 判定层滞空手感与 `render.js drawKart()` 动画跟随改变、须重跑六维门禁。列待裁决。
  - 两选项 `lift`/`air` 均共用 `p` 与 `airMax` 单一相位，**零常数漂移**。
- **贴地起跳标线**：只读派生，数据源 `race.state.pickups[].t` + `track.sample()` + `zone`（`scene3d-model.mjs meta.zone` 既有），3D 层纯算；**不写回** `odo/lateral/g.line`/`localStorage`（B8 `verify_p1_gate.py:510-515`）、**不进** `GATE_KEYS`（`["id","lap","commitT"]` 三键锁定）、不夹 `FORBID` 答案域；与选道态互斥（分叉窗口内不显示，§2.3 里程互斥）。
- **L2 路侧装饰**：**不进** `state.pickups`、不参与 `scanPickups()` 任何碰撞/计数 → 不污染 `PN-ROCK-05a`「生成 ≤2 颗/局」；纯 `createWorld()` 静态 mesh、按 `zone` 派生密度。

### A3. P4 结论（额外惩罚题是否计入 `finishTime` / 会不会撑破 ≤180s）

**明确答案：额外惩罚题「答题本身」不计入 `finishTime`，「答错触发的 `SLOW 1.4s` 减速」计入；本轮改动净利好、不会因额外题撑破 ≤180s，但 ≤180s 基线必须重跑、禁止沿用 174.57s。**
- 时钟机制：`main.js:1073 frozen = mode==="quiz"||boardOpen||shopOpen` → `simTime` 不累加；`:1093-1095` 仅 `mode==="racing"` 才调 `race.update(dt,input)`，`openQuizCard()`(`:897`) 切 `mode="quiz"` 后**不调** update → `race.js:605 state.time+=dt` 不推进 → 答题墙钟不占 `finishTime=state.finishTime`(`:740`)。`headless_laps.mjs:74-83` 逐字确认「浏览器里 mode==="quiz" 会冻结仿真，答题不占 state.time；这里立即结算」。
- 但答错 `finishQuiz()` `race.js:508 player.slow=1.4`（`SLOW.mul=0.54` `config.js:226`）→ `updateKart`(:269) 降速 1.4s → 拉长 `state.time`；这份减速**已计入** headless 最慢 174.57s（worst 工况故意答错）。
- 本轮：撞石封顶 2 次 + 生成 ≤2 颗（§2.3）→ 额外 rock 题数量下降 → `SLOW` 触发下降 → **净利好**；删 `dashLeft`（headless 不触发）、新增分叉 hold、惩罚题数量变化是变量但方向偏利好。
- 结论：`≤180s` 门槛不变、理论不会因额外题撑破；但 174.57s 余量仅 **5.43s**，删 `dashLeft` / 分叉 hold / 惩罚题数量变化均影响实跑 → **`PN-SPEED-01` 必须新实跑，不沿用 174.57s**（质量线 §2/§7 同口径）。

### A4. 改动文件清单（供主理人向用户申请放行）

| 文件 | 本轮改动性质 |
| --- | --- |
| `js/race.js` | **判定核心，确实要改**（ADR-2 已书面放行）：`buildField()` 石头配额 ≤2、`blocked()` 按 `g.line` 绝对里程排除、`scanPickups()` 滞空见证式 + `rockHits` 封顶 + 成功跳石触发欢呼、删 `dashLeft`/`jumpCd`、`pressRivals()`/`judge()`/`baseMul()` NPC 错峰与速度下限、`cheer()` 序号字段 |
| `js/main.js` | `fireJump()` 260ms 状态机 + `input.jump2`、`readInput()` 扩字段、`syncCheer()` 序号去重、`burstConfetti()` 参数化局部彩带、半屏 `onHalfTap` 事件委托、`window.__rally` 只读 getter 扩、`syncFork()` 死代码清理、`merge:0.012` 统一 |
| `js/config.js` | 仅登记常量（如集中定义 `ROCK_QUOTA`）；**`DIFFICULTY.speed` 260/300 逐字不动**（方案 B） |
| `js/scene3d-model.mjs` | `SNAPSHOT_KEYS` 加 `pickups`、`KART_KEYS` 加 `hop/airMax`、`lift` 抛物线归一化、`buildSceneFrame()` 中性分叉/起跳标线只读派生、`VISUAL_FLOW_GAIN`（方案 B，仅视觉相位） |
| `js/scene3d.jsx` | `createWorld()` 补石头/宝石 `InstancedMesh` + L2 装饰（不进 pickups）、分叉左右 ribbon + 中央岛、贴地起跳标线、`window.__P1_SCENE__ rocks[]`/forkVisible 只读投影 |
| `js/render.js` | 2D L0 降级层石头/分叉视觉与 3D 对齐；`drawKart()` lift 跟随 airMax（仅选项乙时） |
| `css/game.css` | 半屏命中层 `#half-tap`（可选高亮层 `pointer-events:none`）、局部彩带/欢呼微调；z 栈不动 |
| `index.html` | `#half-tap` 容器（可选）、`:188` 动态注入 tag 手工核对；7 处 `../音标大闯关/` 引用不动 |
| `verify_*.py` / `result.json` / `gate-logs/` | **断言期望值同步**（§3 清单）：BD-1/B3 重锚、三条只读白名单扩、PM-6 重定义、取时正则、tag 46→N；**不删/不豁免/不改 NOTE** |
| `.workbuddy/backups/p1-interaction-20261114/` | **新建**独立快照（8 文件 sha256），不覆盖 `p1-pre-20261110/` / `p0-pre-20261109/` |

> **终裁口径已逐条对齐**：NPC `v_i ≥ 0.94·v_player_now`（§2.5）；词表 `Good/Excellent/Marvellous` 逐字不动、`cheer()` 取词维持现状 combo 索引、不做连击偏向词（§2.4）；方案 B 判定层 260/300 不变；`race.js` 判定核心确实要改（覆盖设计线 v1.1「放行≠要求改/不触碰判定核心」已令删）；批准 **2026-11-14 09:53 +0800**、BD-1 五 + B3 七 = 并集 8 文件、新建独立快照重锚、不删断言/不豁免；L2 装饰不进 `state.pickups`；撞石每局 ≤2 次硬上限（「生成 ≤2 颗」为主理人加的额外保险、用户可单独撤销）。

---

## 0. ADR-2 判定核心放行 · 批准登记（口径与质量线 §0.1–§0.3 一致，不另写一套）

### 0.1 批准原文与时间（逐字登记，勿改写）

- **批准结论（主理人转达，逐字，同 `p1-interaction-qa.md` §0.1 / `p1-interaction-spec.md` §0.3）**：
  > 放行 `race.js` 判定核心 —— ADR-2 / `BD-1`(`verify_p0_gate.py:159`) / `B3`(`verify_p1_gate.py:451-457`) sha256 双锚定获用户**书面批准**。
- **用户原话逐字（team-lead 2026-11-14 E1 补充派单附送，登记用、勿改写）**：
  > 放行动 race.js 判定核心。限定每局撞到石头的次数不超过2次。奖励保持现有词表Good / Excellent / Marvellous，成功跳过给欢呼/纸屑。我实测如果只点一次空格键跳不过石头，要么你就确保用户只需点击一次空格键或者点击"跳跃"就能完美刚好跳过石头的高度，要么就支持双击空格键，能够将卡丁车跳得高点。NPC卡丁车要确保看起来像真人驾车，不要龟速或者扎堆。
- **时间**：**2026-11-14 09:53 +0800**（本机时钟，同质量线 §0.1）。
- **证据层级（QA 留痕，不臆造）**：用户原话授权的是「放行动 `race.js` 判定核心」及五项玩法裁决；「ADR-2 / `BD-1` / `B3` sha256 双锚定获书面批准」是**主理人转达的结论与依据**，用户未就 sha256 双锚定单独措辞，本文件不代为拟写。E1 补充派单已附送上述用户原话逐字，可据此关闭质量线 §10.1「用户批准原话待补录」项（回执同步 quality-lead）。
- **与既有裁决关系**：本次放行**只针对判定核心 sha256 双锚定**，不推翻 2026-11-12「四套旧门控整体退役」书面裁决（`p1-gate-retirement.md:5`），不改变 `result.json` 的 `gate_definition`，不改变 D6 终点定义。**判定核心确实要改**（team-lead 2026-11-14 终裁）：用户「放行动 race.js 判定核心」就是为 `buildField()` 石头配额、`blocked()` 按 `g.line` 排除、`scanPickups()` 撞石计数、删 `dashLeft`、跳跃判定放行的；设计线 v1.1「放行≠要求改、不触碰判定核心」措辞已令其删除。**方案 B 唯一不动的是判定层 `DIFFICULTY.speed` 260/300**（§2.7），不是「整个判定核心」。改动清单见 §A4 / §2.1–§2.5。

### 0.2 锚定文件清单（并集 8 个，旧 sha256 前 16 位）

`BD-1`（`verify_p0_gate.py:35-36` `CORE_FILES`，比对 `.workbuddy/backups/p0-pre-20261109/file-hashes.json`）5 文件 ∪ `B3`（`verify_p1_gate.py:451-453`，比对 `.workbuddy/backups/p1-pre-20261110/manifest.txt`）7 文件 = **并集 8 文件**。旧 sha 前 16 位逐字取自 `p1-pre-20261110/manifest.txt`（本轮 `Read` 复核）：

| # | 路径 | 旧 sha256（前 16） | 锚定来源 |
| --- | --- | --- | --- |
| 1 | `音标拉力赛/js/race.js` | `e9a17cf03dabcada` | BD-1 + B3 |
| 2 | `音标拉力赛/js/track.js` | `15b77aff0548a046` | BD-1 + B3 |
| 3 | `音标拉力赛/js/config.js` | `0dfe653c7552aab3` | BD-1 + B3 |
| 4 | `音标拉力赛/js/main.js` | `2db27bd0c1010faf` | BD-1 + B3 |
| 5 | `音标拉力赛/js/headless_laps.mjs` | `41443f3fe153b8f9` | BD-1（质量线 §0.2 未列前 16，本行由 `manifest.txt:11` 补齐） |
| 6 | `音标拉力赛/js/render.js` | `7b65bafa994de5cc` | B3 |
| 7 | `音标拉力赛/js/probe.jsx` | `d149c0f0d409eea8` | B3 |
| 8 | `音标拉力赛/probe.html` | `4f045d8159569edc` | B3 |

> 原派单「7 个锚定文件」= B3 上表除 `headless_laps.mjs` 的 7 行；`headless_laps.mjs` 因新增 ≥1000 seed 批量重放极可能改动，须一并重锚（质量线 §0.2 已明示）。
> **注**：`BD-1` 与 `B3` 比对目标快照不同（`p0-pre-20261109/` vs `p1-pre-20261110/`）；若两快照对同一文件记录不同 sha，须在重锚 `detail` 中分别登记「旧(P0)→新」与「旧(P1)→新」，不合并。
> **不得随之放宽**：`BD-1b`（:163，五套验收脚本 sha256 全等）、`BD-1c`（:164-167，`音标大闯关/js/data.js` / `js/ipa-display.js` 字节全等）、`B4/B5/B6`（IPA 48 闭集 / 49 卡面 / D4 教研表）。本次只放行判定核心，不放行权威表与资产链。
> `probe.jsx` / `probe.html` 按 `PVIS-5`（`verify_p1_gate.py:179`）仍须逐字不动；确需改动须另走用户裁决，不得夹带本次重锚。

### 0.3 重锚方式（按新口径改期望值，不删断言）

1. 实现落地后**新建**独立快照目录 `.workbuddy/backups/p1-interaction-20261114/`，对 §0.2 并集 8 文件逐字节计算 sha256 写入新 `manifest.txt` / `file-hashes.json`；**不覆盖、不删除** `p1-pre-20261110/` 与 `p0-pre-20261109/`（历史证据链永久保留）。
2. 把 `BD-1`（`verify_p0_gate.py:159-161`）与 `B3`（`verify_p1_gate.py:456-457`）的**比对目标路径**切到新快照，`detail` 逐字登记「旧 sha → 新 sha」与批准时间 2026-11-14 09:53。
3. **断言强度不降**：仍是「逐字节 sha256 全等」的硬 `chk`，仍要求 `len(want)>0` / `all(core_eq.values())` / `len(mism)==0`；只是期望值从「与旧基线全等」改为「与用户批准的新基线全等」。
4. **铁律（逐字，同质量线 §0.3-4）**：**按新口径改期望值，不删断言 / 不豁免 / 不改 NOTE**。任何把 `BD-1` / `B3` 改成 `NOTE`、跳过、或 `or True` 豁免的写法一律判 **FAIL**，不得以「用户已放行」为由实施。

---

## 1. 「单跳跳不过石头」精确根因定位

### 1.1 判定链路（本轮磁盘复核，全部精确到行）

`update(dt, input)`（`race.js:597-763`）主循环顺序（决定一切先后关系）：

```
:631-641  hold 冻结（decide.phase==="hold" → pressRivals() → return，不处理 jump）
:643-664  jump 处理（input.jump → hop=1 air=0.5 / hop=2 air=0.74+dashLeft=140+jumpCd=0.9）
:665      updateKart(player, dt) → :283 air -= dt、:285 hopWindow -= dt、:287 air===0→hop=0、:290 odo+=base*mul*dt、:293-297 dashLeft 分摊推 odo
:667      blockSplitter(prevOdo, input) → 可能回滚 player.odo（:386）
:668      scanPickups() → :566-595 石头判定
```

`scanPickups()` 现状（`race.js:566-595`）：

```js
let odo = Math.floor(player.odo / L) * L + item.t * L;   // :570 石头本圈绝对里程(unit)
if (odo > player.odo + 90) odo -= L;                      // :571 跨圈修正
if (Math.abs(player.odo - odo) > 78) continue;            // :572 碰撞窗口 ±78 unit
if (Math.abs(player.lateral - item.lateral) > 0.2) continue; // :573 同车道
item.taken = true;                                        // :574 ★首次满足即一次性锁定
if (item.kind === "gem") { ... }
else if ((player.air || 0) > 0.05) state.ribbonT = 1.0;  // :578-581 成功规避（仅点采样）
else if ((state.shields||0) > 0) { ... }                  // :582-586
else { state.shake=6; audio.bump(); openQuiz("rock"); }   // :587-593 撞石弹题
```

### 1.2 逐个候选根因裁定（证据 + 主因 / 次因 / 非主因）

| # | 候选 | 磁盘证据 | 裁定 |
| --- | --- | --- | --- |
| **A** | **3D 石头完全不可见 → 时机不可判** | `SNAPSHOT_KEYS`（`scene3d-model.mjs:64-66`）=`["lap","laps","zone","span","time","karts","gates"]`，**无 `pickups`**；`scene3d.jsx createWorld()`（:190）**无石头/宝石 mesh**；`KART_KEYS`（:67-69）**缺 `hop/airMax`**；`lift = air*scale`（`scene3d-model.mjs:209`）= `0.5×0.008 = 0.004 m`（车高 1.05 m 的 0.4%），一段/二段跳视觉无差 | **主因①（P0 体验根，时机问题而非高度问题）**：3D 主形态（`renderMode=3d`）玩家既看不见石头，也看不出跳没跳、跳没跳够，根本无法判断「该在哪一段点一次」。2D 降级层有石头绘制（`render.js:348-380`）但 3D 下不生效。 |
| **B** | **`scanPickups` 首帧点采样 `air>0.05` + `hopWindow` 死代码 → 容错窗口从未生效** | `:574` 首次进 `±78` 窗口即 `item.taken=true` 一次性判定，那**一帧**须 `air>0.05`（`:578`）；起跳稍早（进窗前 `air` 已耗尽）或稍晚（`taken` 已消费，`if(item.taken) continue` :569）都撞。`hopWindow`（`:284-285` 注释「起跳后的宽容窗口，提前一点起跳也能算成功规避石头」，仅 `Math.max(0,(kart.hopWindow||0)-dt)` 递减）**全项目零赋值、零读取**（`js/` 全量 Grep 仅此一处，质量线 / spec F3 双确认） | **主因②（可取证判定侧根因）**：容错窗口宣称了但从未实现；「单跳必过」被压成「恰好命中进窗首帧」的点采样赌博。`hopWindow` 语义是「起跳后宽容窗口」，与 260ms 双击计时器**完全不同**，不可复用（§1.4）。 |
| **C** | `air` 有效窗与碰撞窗口错配（**量化**） | `airMax=0.5`（:650）、`air -= dt`（:283，DT=1/60）、阈值 `>0.05`（:578）→ 有效窗 `0.5-0.05 = 0.45 s`（离散帧 0.45–0.467 s）= `117 unit`(follow 260) / `135 unit`(listen 300)。碰撞窗口 `±78` 共 `156 unit`，通过耗时 `0.600 s`(follow) / `0.520 s`(listen) | **主因②的量化佐证**：`air` 有效里程（117–135）本身**小于**碰撞窗口通过里程（156），且窗口是点采样，二者叠加使「提前量稍大」必失败。质量线 / 美术线独立实算一致（0.45s / 117–135m）。 |
| **D** | `hold` 冻结吞掉石头前起跳 | `:631-641` `decide.phase==="hold"` 3 秒整体 `return`，`jump` 处理在 :643 之后 → 冻结期按 Space 无效。`blocked()`（`:114-120`）只按相对 `commitT` 排除 `±0.04`（`0.04L=770 unit`），而真实分叉窗口 `span*L+merge*L = 1475.1 unit`(follow) / `1559.1 unit`(listen)（本轮纯计算复核）；第 5 石 `t≈0.62875`（`0.12+0.74×5.5/8`）落入 listen 窗口 `[0.62703, 0.70800]` | **次因（特定场景主因）**：石头与分叉决策窗口未做里程互斥，落入窗口的石头撞上 hold 冻结时，玩家起跳被吞 → 必撞。属 §2.3 `blocked()` 修复范围。 |
| **E** | `jumpCd=0.9` 冷却让「一次点击」实际未生效 | `jumpCd=0.9`（:661）**只在二段跳分支** `hop===2` 内设置，且仅 :659 `if((player.jumpCd||0)<=0)` 守护 `dashLeft`；首击走 `:645-652 if(!up && !player.hop)` 分支，**不查 `jumpCd`**；`updateKart:279` 每帧递减 | **非主因**：冷却只约束二段跳冲刺，不拦截任何首击。 |
| **F** | `e.repeat` 拦截影响单次点击 | `main.js:317 if (e.repeat) return;` 只拦按住键的自动重复；单次 `keydown(Space)` → `:320 jumpEdge=true` → `readInput:367-368` 消费一次边沿 | **非主因**：单次点击/轻点键盘边沿正常产生 `input.jump`，<｜hy_place▁holder▁no▁813｜>全产品层 `dblclick` / `e.detail===2` / 双击计时器 **0 命中**（R1 + 质量线双确认）。 |
| **G** | `dashLeft=140` 掠过判定窗口、缩短 `air` 覆盖 | `dashLeft=140`（:660）仅二段跳 `hop===2` 产生，按 `min(dashLeft, 900*dt)` 分摊推 `odo`（:293-297）；**单跳不触发** | **非「单跳失败」主因**，但**违反「保持前行、水平速度不变」**（额外推进 `odo`）+ 与 `blockSplitter` 回滚互相污染 → **必须删除**（§2.2、`PN-JUMP-03`）。 |

### 1.3 主因的深层数值：判定 `unit` 与 3D 米制 `m` 的量级错配（工程侧必须点明）

- 判定窗口 `±78 unit` = `±0.624 m`；`air` 有效里程 `117–135 unit` = `0.94–1.08 m`。
- 3D 视觉可见距离（`p1-interaction-visual.md` §3.4）：`aheadM=48 m`、雾中渐显 `34→18 m`、全清晰 `≤18 m`；`dzM = wrapHalf(ti-t0)*L*scale`（`scene3d-model.mjs:203`），一圈 `L*scale=154.036 m`。
- ⇒ 石头在「全清晰 18 m」出现时，距判定碰撞点还有 `≈18/0.008 = 2250 unit`（约 `8.6 s` @260）。若用户「看到就跳」，`0.45 s` 的 `air` 在到达石头前早已归零 → 必撞。
- **结论**：让「看到就跳」成立，**不能**靠加长 `air`（会把滞空做成起飞失真、且仍追不上米级提前量），必须靠「**可见锚点 + 判定窗口对齐**」：① 3D 补石头几何（§2.8）；② 在判定里程 `airCover + 78` 处放**贴地起跳标线**（美术线 §10.2），把「该点一下」的那一段变成可见、可预期的操作区；③ 判定式从点采样改为窗口结算（§2.1），使容错窗 = 整个通过窗口。`unit` 与 `m` 之间只通过 `WORLD_SCALE=0.008` 换算，**禁止把 `78 unit` 直接当 `78 m` 或反之**。

### 1.4 权威结论（team-lead 点名三选一 + 绑定量，工程侧定稿）

> 质量线已纠正主理人原派单「复用 `hopWindow` 做 260ms 窗口」的措辞；`design-strategist` spec F3 / §2.3 / P11 亦把三选一交 E1。工程侧裁定如下：

1. **`hopWindow` 删除，不复活。** 它是 `race.js:284-285` 声明「提前起跳宽容窗口」却零赋值、零读取的死代码；其语义（起跳后一段时间经过石头仍算规避的**容错窗口**）与 260ms 二段跳**输入事件间隔**是两回事，拿它当二段跳计时器是语义错配。**处置**：删除 `:284-285` 两行；其宣称的容错目标由 §2.1 新建的、绑定 `air` 有效窗的**滞空见证式规避机制**承接。→ 质量线 `PN-JUMP-06` 二选一，选「**删除死字段 + 由新机制承接容错语义**」，不是「不修只删」也不是「复活字段」（回执同步 quality-lead）。
2. **260ms 二段跳 = 新建独立状态机，落在 `main.js` 输入层。** 判定核心 `race.js` 只有 `update(dt, input)` 的**仿真时间 `dt`**，没有墙钟；260ms 是真实墙钟间隔，必须 `performance.now()` 打点。若把墙钟塞进 `race.js`，`headless_laps.mjs` 的 `seeded(seed)`（:30-33）确定性重放会失去可复现性（≥1000 seed 硬验收依赖它）。→ `main.js` 记 `lastJumpAt`，产出 `input.jump`（首击）+ `input.jump2`（260ms 内第二击）两个布尔边沿，`race.js` 只消费、保持确定性（字段名定稿见 §4.2）。
3. **「单跳必过」100% 验收绑定量 = `air` 有效窗覆盖石头碰撞判定窗口，不绑定双击。** 用户原话「要么确保点一次就能完美跳过，要么支持双击跳更高」——主路径必须单次 100%；绑定双击会把「必须会双击」变成门槛，直接违反 `PN-JUMP-00`「二段跳不是单跳能过的前提」。→ 具体绑定为 §2.1 判定式：**单次起跳的滞空窗与石头 `[rockOdo-78, rockOdo+78]` 通过窗口有交集即判规避**，`hop===1` 即完成、`hop===2` 分支不参与该判定。

---

## 2. 工程实现规格（函数 / 行号 / 参数 / 验收判据）

### 2.1 【P0】单跳必过（判定核心 `race.js`，ADR-2 已放行）

**A. `scanPickups()`（`race.js:566-595`）改「滞空见证式」**，替换 `:574` 首帧 `taken=true` 点采样。**保留 `:570-573` 的 odo 换算与 `|Δodo|<=78` 绝对值窗口判定**——`:571 if (odo > player.odo+90) odo -= L` 把「前方 >90 unit」的石头折算到后方，使玩家经过石头时 `d = player.odo-odo` 在 `[-78, +78]` 窗口内连续、无 wrap 跳变；结算**不得**用「`d>78` 当作已越过」的单向判据（会把前方 90 unit 外的石头误判为已越过）。gem 保持即时拾取语义不变，只有 rock 走见证式：

```js
// 参数（新增常量，置于 createRace 顶部）：
const ROCK_HIT_BAND = 78;   // unit，保留现状 ±78（:572）
const ROCK_LAT_BAND = 0.2;  // 保留现状同车道阈值（:573）
// 每颗 rock 新状态（mk 不改、动态挂）：item.armed（进过窗）/ item.cleared（窗内见证滞空）
for (const item of state.pickups) {
  if (item.taken) continue;                                    // :569 保留
  let odo = Math.floor(player.odo / L) * L + item.t * L;     // :570 保留（换算不改）
  if (odo > player.odo + 90) odo -= L;                        // :571 保留（窗口内 d 连续的前提）
  const d = player.odo - odo;
  const inBand = Math.abs(d) <= ROCK_HIT_BAND;                // :572 绝对值判定，避开 wrap 误判
  const sameLane = Math.abs(player.lateral - item.lateral) <= ROCK_LAT_BAND; // :573
  if (item.kind === "gem") {                                  // gem 即时拾取，:575-577 语义零改动
    if (!inBand || !sameLane) continue;
    item.taken = true; applyWalletDelta(1, 0); audio.hit();
    continue;
  }
  // —— 以下仅 rock：滞空见证式（清除「进窗首帧点采样」歧义）——
  if (inBand && sameLane) {
    item.armed = true;
    if ((player.air || 0) > 0) item.cleared = true;          // ★窗内任一帧滞空即见证规避（0.05→0）
  }
  // 定案：已进过窗，且（已见证规避 或 滞空结束 air===0 或 已出窗 |d|>78）
  const settle = item.armed && (item.cleared || (player.air || 0) === 0 || !inBand);
  if (settle) {
    item.taken = true;
    settleRock(item);   // cleared→规避(ribbonT+cheer+局部彩带)；否则→撞击(shake/bump/rockHits++/封顶/openQuiz)
  }
}
```

- **判定式核心**：`settleRock(item)` = `item.cleared ? 成功规避 : 撞击`。规避分支 = 现 `:581` `state.ribbonT=1.0` **+ §2.4 欢呼 + 局部小彩带**；撞击分支 = 现 `:587-593`（`state.shake` / `audio.bump()` / `openQuiz("rock")`）+ §2.3 `rockHits++` 与封顶。
- **`air>0.05` → `air>0` 且由「首帧」放宽为「窗内任一帧」**：`air` 每帧 `-dt`（:283），`air>0` 恰好 = 「本次起跳尚未落地」，等价于 `hop>=1` 未复位（:287）。玩家不跳时 `air===0`，进窗首帧即定案为撞击（即时性不变）；玩家在窗口内起跳则 `item.cleared=true` 立即定案为规避。容错窗 = 整个通过窗口（0.52–0.60 s）∩ 起跳滞空（0.45 s），完全由 `air` 驱动、与 `hop===2` 无关。
- **先后关系（硬约束）**：`scanPickups()` 仍必须在 `blockSplitter(prevOdo, input)`（:667）**之后**调用（:668），用回滚后的最终 `odo`；`blockSplitter` 合法回滚 `player.odo = prevOdo`（:386）会让 `d` 在窗口边缘反复跨越 → `item.taken` 一旦 true 不再处理（幂等），`item.armed/cleared` 为单调累积、不因回滚清除，`PN-JUMP-03` 断言须显式排除该回滚（质量线 §4 已要求）。
- **行为变更登记（须 `PDCORE-4`/`PDEG-4` 两形态一致性复跑）**：现状「不同车道 → `continue`、石头永不 `taken`」；改后不同车道绕过（未 `armed`）仍不结算、保持现状，只有进入同车道窗口的石头在「见证规避 / 落地 / 出窗」时定案一次。跨圈复位 `:614 state.pickups.forEach(it => it.taken=false)` 须同步清 `armed/cleared`。

**B. 可见提前量 + 起跳标线（3D 视觉层只读，不改判定）**：
- `SNAPSHOT_KEYS` 加 `pickups`（§2.8），`scene3d.jsx createWorld()` 补石头 `InstancedMesh`（美术线 §3.3 半埋低矮石块，可见高 `h_rock≈0.32 m`）+ 地面警示光圈。
- **起跳标线里程**：置于石头前 `AIR_COVER = airMax*speed + ROCK_HIT_BAND ≈ 195 unit`(follow) / `213 unit`(listen)，换算 `×0.008 ≈ 1.56–1.70 m`；贴地金线 + 一次性「跳」提示（美术线 §10.2）。用户在此标线**附近**任意时刻点一次即 100% 规避。
- **标准时机定义（`PN-JUMP-00` `detail` 逐字写出）**：`player.odo ∈ [rockOdo - AIR_COVER - ROCK_HIT_BAND, rockOdo - ROCK_HIT_BAND]` 区间内产生单次 `input.jump`。

**C. 验收判据**：
- `PN-JUMP-00`：≥1000 seed headless 重放（沿用 `headless_laps.mjs:30-33 seeded(seed)`），标准时机下单次 Space / 点击 `#jump` 规避成功率 **100%**；断言 `hop===1` 即完成规避、`hop===2` 分支不参与；`quizReasons.rock` 该次为 0。
- `PN-JUMP-01`：首击 `t(pointerdown)→t(air>0)` ≤1 帧（禁原生 `dblclick` ~300ms 延迟）。
- 视觉侧：`lift > h_rock`（判定帧车底越过石顶）、单跳峰值 `0.55 m`、二段 `0.85 m`（美术线 §5.3）；`lift` 由 `air` 归一化相位 `p = 1 - air/airMax` 推导（`lift(p)=peak·sin(π·p)`，见 §A2），与判定**共用 `airMax` 单一常数源**但**不参与**碰撞判定（判定只看 `air>0`）——即「同相位、不耦合判定结果」，避免两套常数漂移。

### 2.2 二段跳 260ms 状态机（`main.js` 输入层新建，删 `dashLeft`）

- **状态字段（模块级）**：`let lastJumpAt = -Infinity;`（`performance.now()`，单位 ms）；`let jump2Edge = false;`。
- **边沿处理**（复用 `main.js:298-302 ui.jump pointerdown` 与 `:316-328 keydown`，两处都调同一个 `fireJump()`）：
  ```js
  function fireJump() {
    const now = performance.now();
    if (now - lastJumpAt <= 260) jump2Edge = true;  // 260ms 窗内第二击
    else jumpEdge = true;                           // 首击 / 窗外重新起跳
    lastJumpAt = now;
  }
  ```
  - 键盘 `Space`（:320）与触屏 `#jump`（:298-301）**共用同一 `jumpEdge`/`jump2Edge`**，与现状「键盘触屏同源」（`main.js:79`、`:296-297` 注释）一致。
  - `e.repeat` 拦截（:317）保留 → 按住不触发第二击。
- **`readInput()`（:351-370）返回值扩字段**：`return { left, right, replay, rocket, jump, jump2 }`，其中 `jump2 = jump2Edge; jump2Edge = false;`（与 `jump` 同款一次性消费）。
- **`race.js:643-664` 消费**：`if (input.jump && !holding)` 维持首击逻辑（`:645-652` 设 `hop=1/air=0.5`）；`input.jump2 && player.hop===1` 走二段（`:653-656` 设 `hop=2/air=0.74`）。**删除 `:657-662` 整个 `if(jumpCd<=0){ dashLeft=140; jumpCd=0.9; }` 块**、`mk()` 中 `dashLeft:0`（:27）、`updateKart:293-297` 的 `dashLeft` 分摊 `odo` 推进、`updateKart:279` 的 `jumpCd` 递减、`mk():26 jumpCd:0`。
- **验收 `PN-JUMP-03`**：删后 `dashLeft` 全产品层 0 命中或恒为 0；二段跳期间 `Δodo/Δt === diff.speed*mul` 恒定、零冻结；`blockSplitter` 回滚显式排除（护栏例外）。
- **验收 `PN-JUMP-02/04/05`**：260ms 窗内第二击追加抬升（`airMax 0.5→0.74`）、窗外不追加；触屏一下跳 / 两下二段跳；`air===0 → hop=0`（:287）落地才复位段数。

### 2.3 撞石 ≤2 次/局（用户最终拍板，取代 1/6）

**A. `buildField()`（`race.js:111-150`）生成配额 ≤2 颗/局**：
- 现状 `for (let i=0; i<8; i++)`（:128）每圈 8 rock × `TUNING.laps=2`（`config.js:15`）= **16 颗/局**。改为**整局（跨圈）恰好 `ROCK_QUOTA=2` 颗**：在 `createRace` 层一次性生成 2 颗、分配到两圈各 1 颗（或按 `lap` 命中），`state.pickups.filter(k==="rock").length <= 2` 可观测。gem 保留 10 颗（:138）不动。
- **`blocked()`（:114-120）改按 `g.line` 绝对里程区间排除**（现按相对 `commitT` 只排 `±0.04L=770 unit`，小于真实窗口 1475.1/1559.1 unit）：
  ```js
  const margin = 60; // unit 安全余量
  const blocked = (t) => {
    const odo = player.startOdo + t * L;             // 与 :83 g.line 同基准
    if (Math.min(Math.abs(t - startT), 1 - Math.abs(t - startT)) < 0.04) return true;
    return gates.some((g) =>
      odo >= g.line - span * L - margin && odo <= g.line + merge * L + margin);
  };
  ```
  → 石头严格落在单车道直行段、与分叉「张开→选择→闭合」窗口不重叠（触屏手势互斥），根治 §1.2-D hold 冻结吞跳。窗口边界由 `g.line`（`race.js:83` = `startOdo + lineT*L`）、`span=forkSpan(diff,L)`（`config.js:301-303`）、`merge=TUNING.mergeDt`（`config.js:17`）定义，判定侧唯一真值。
- **B. 碰撞计数封顶（双保险二）**：`state.rockHits`（本局累计，开局 0，跨圈**不**复位）、`state.rockBudget = 2`。`settleRock()` 撞击分支先判 `if (state.rockHits >= state.rockBudget) { 静默越过，不 openQuiz、不计 quizReasons.rock }`，否则 `state.rockHits++; openQuiz("rock")`。
- **验收**：`PN-ROCK-04`（`rockHits<=2` 整数硬上限）、`PN-ROCK-05a`（生成 ≤2 颗）、`PN-ROCK-05b`（封顶）、`PN-ROCK-06`（`gate-logs/S4.log` 改动前超标 `{kart:13,rock:7}` / `{kart:11,rock:4}` 原样留痕 FAIL，不悄悄改绿）、`PN-ROCK-01/02/03`（提前可见 / 存在跳跃窗 / 无生成即碰撞）。撞石封顶减少额外惩罚题、对 `≤180s` 利好，但不得据此免跑 `PN-SPEED-01` 基线。

### 2.4 词表 / 欢呼 / 局部小彩带 / 序号去重

- **词表零改动**：`cheer()`（`race.js:205-211`）= `["Good","Excellent","Marvellous"]`（:206）**原样保留，不换 `Amazing`**（质量线口径更正，推翻早前指令）。**取词维持现状 `combo` 索引**（:207 `words[Math.min(len-1, Math.max(0,(combo||1)-1))]`）、**不做连击偏向词 / 不擅自加任何新规则**（team-lead 2026-11-14 终裁：用户只说「保持现有词表」）；成功跳石调用 `cheer(1)` 即取首词 `Good`（每次恰好一次欢呼）。
- **成功跳石补欢呼（推翻 A5 旧注释）**：`settleRock()` 规避分支（`race.js:581` 现状只有 `state.ribbonT=1.0`）新增**一次** `cheer(1)`（复用 :205，无需新函数）。`state.cheer` 结构扩为 `{ word, seq, until }`：
  - `cheer()` 内维护 `state.cheerSeq = (state.cheerSeq||0)+1`，`state.cheer = { word, seq: state.cheerSeq, until: state.time+3.4 }`（`banner`/`bannerT` 保持 :209-210）。
  - 判门命中 `judge():237 cheer(player.combo)` 与成功跳石共用同一 `seq` 计数器，**不新增 DOM/canvas/层**。
- **`syncCheer()`（`main.js:743-755`）去重由词改序号**：`cheerShown` 存 `seq`（`:94` 初始化改 `let cheerShown = -1;`），`:748 if (on && cheerShown !== c.seq)`、`:749 cheerShown = c.seq;`、`:753 if(!on) cheerShown = -1;`。→ 同词连续触发仍重播（`PN-QUIZ-05`）。
- **`burstConfetti()`（`main.js:705-720`）参数化**：`function burstConfetti(cx, cy, count = 16)`，以 `#cheer-word` 的 `getBoundingClientRect()` 中心为原点（`syncCheer:751` 调用时传入），`14–18 片`放射外抛（`vx=cos·s, vy=sin·s - 上抛`，`s≈120–220 px/s`，`life≈0.9–1.2s`，`w≈4–7px`），复用 `ui.confetti` 第二 2d context（`main.js:725 ctx2`），**不新增层**；`drawConfetti()`（:722-741）全屏 `clearRect`（:729）保留。现 90 片全屏（:708）降级为局部小簇。
- **验收**：`PN-QUIZ-03`（成功跳过恰好一次欢呼 + 恰好一次局部彩带、词表逐字锁定、零 `Amazing`）、`PN-QUIZ-03b`（撞墙 `race.js:529` / 撞车 :547 / 护身卡 :583-586 三分支零弹出）、`PN-QUIZ-05`（`seq` 去重、同词连播）。

### 2.5 NPC 不龟速 / 不扎堆（判定核心，ADR-2 已放行）

根治三处「陪跑脚本」（本轮磁盘复核）：

| 落点 | 现状 | 规格 |
| --- | --- | --- |
| `baseMul()`（`:177-180`） | `a=1.02 / b=1.008` 几乎同速 | 抬到 `≈0.96–1.06` 区间 + 缓慢正弦起伏（非恒定），给微速差；**判定层 `diff.speed` 260/300 不变**（§2.7） |
| `judge()`（`:230-234`） | 命中时 `r.odo = min(r.odo, player.odo-220-i*60)` 硬压玩家后方 | 改「软跟随」：只在 `r.odo > player.odo + 上限` 时轻收，不硬 clamp 到固定负值 |
| `pressRivals()`（`:397-407`，`:633`/`:735` 调用） | `behind = player.odo-260-i*80`，`r.odo>behind → r.odo=behind`，横向强设 `±0.1`（:403-405） | 删除硬拉回；改各自 `laneTarget`（a 偏左 / b 偏右）+ 错峰里程，不在 `answering()` 期强设同侧 |
| `shoveRival()`（`:409-419`） | `:416 r.odo = player.odo-240` | 保留碰撞推离，但去掉瞬时里程回拉 |
| `createRace` 起跑（`:38-41`） | 三车 `startT=0.02` 完全同里程 | 错峰起始里程：a/b 各错开 `±Δ`（按 `id` 相位），非全部 `0.02` |
| `speedNow`/`updateKart` 下限 | 无 | **速度下限（team-lead 2026-11-14 终裁）**：任意 rival `v_i ≥ 0.94 · v_player_now`（设计线 §6 N8 = 0.94×，质量线原 0.9× 已令收紧到 0.94×，比 0.9× 更严；本值已拍板、非待确认）；`updateKart:270-273 gap>0.12 时 mul*=0.94` 的追尾降速不得把 rival 压到下限以下 |

- 验收 `PN-NPC-01`（速度下限 **0.94×**、连续低于下限帧占比 ≤5%；阈值已拍板，取代质量线原 0.9× 建议值）、`PN-NPC-02`（里程差 `>= max(220m,0.02*L)`、横向 `|lat_a-lat_b|>=0.3`、投影包围盒重合帧占比 ≤5%，复用 `verify_p1_visual.py:176-180 kartProjected`）、`PN-NPC-03`（`laneTarget` 变化次数、`lateral` 按 `rate*dt` 非瞬切 :299-303、名次交换可观测、`odo` 无冻结/瞬移）。删 `dashLeft` 后须重跑 `PDCORE-4`/`PDEG-4` 两形态一致性与 `PC-1`（相机跟随 `odo` 单调）。

### 2.6 点左右半屏 + 键盘左右并存（触屏优先，`main.js`）

- **实现方式**：`window` 级 `pointerdown` **事件委托**（不新增物理全屏层，避免打乱 z 栈 / `PM-6` 零相交判据）：
  ```js
  const HIT_EXCLUDE = "#hud, #touch, .panel, #confetti, #cheer, #signs, #tags, #minimap, #quiz, #board, #shop";
  function onHalfTap(e) {
    if (mode !== "racing") return;
    if (e.target.closest(HIT_EXCLUDE)) return;         // 关键层不映射左右
    const left = e.clientX < window.innerWidth / 2;     // 左右半屏映射
    tapSteer = left ? "left" : "right";                  // 喂 readInput() 的 left/right
  }
  window.addEventListener("pointerdown", onHalfTap, { passive: true });
  ```
- **层级避让（质量线实测）**：`css/game.css:44 #hud` z5 / `:194 #touch` z7 / `:223 .panel` z8 / `:144 #confetti` z11 / `:136 #cheer` z12；另有 `#tags`/`#signs` z4、`.fork-card`/`.count` z8、z9/z10 若干 → 一律进 `HIT_EXCLUDE`。`#confetti`/`#cheer` 本身 `pointer-events:none`，物理上不吞点击，逻辑上并列排除。现热区 `index.html:56-61` 仅底部 4 个 `#touch` 按钮，扩大到全屏后 `bindHold()`（`main.js:284-293`）的按键按住态与半屏点触须合并去重（`pointer.left/right` 单一真值）。
- **`readInput():353-354`** 保留 `ArrowLeft/KeyA/ArrowRight/KeyD` + `pointer.left/right`，叠加 `tapSteer` 来源 → 键盘与半屏两来源投影方向一致（`PM-2`、`PN-JUMP-04`）。
- **`PM-6` 同步重定义（不降级）**：由「顶栏与关键可视区零相交、canvas 不吞点击」重定义为「命中层 `pointer-events` 边界 = `HIT_EXCLUDE` 不覆盖 `#hud`/`#touch`/`.panel`/`#confetti`/`#cheer` + 左右半屏映射正确」，**保留原「零相交 / 不吞点击」硬判据不降级**（质量线 §1）。

### 2.7 提速默认 = 美术线方案 B（`VISUAL_FLOW_GAIN` 环境流速增益）

- **采纳 `p1-interaction-visual.md` §2.3-B / §9**：车体 / 门位 / 分叉 / 石头**严格绑定判定 `t`**（几何零漂移、六维阈值与 `p1-3d-art-spec.md` §5 构图校验零复验）；新建**单一全局标量** `VISUAL_FLOW_GAIN` 只放大纯环境元素滚动相位（中央虚线 `scene3d.jsx:245`、路肩标记、雾中远景、路面粒子、路牌后退速率）。`opts.worldScale`（`scene3d-model.mjs:162`）保持 `0.008` 不动。
- **判定层 `DIFFICULTY.speed` 零改动**：`config.js:36 follow=260` / `:46 listen=300` 逐字不变；`VISUAL_FLOW_GAIN` 全产品层当前 **0 命中**（质量线磁盘实证），实现后**零进** `race.js` / `track.js` / `config.js` / `headless_laps.mjs`。
- **撤回旧判断**：「提速必使 `PLR-CSEG-S2` / `PLR-CSEG-A6` FAIL」基于「判定层 `speed` 会改」的旧假设，方案 B 下不成立 → **`S2`/`A6` 期望值维持原样、原样全绿、不改注释不改常量不豁免**；改补 `PN-SPEED-04`（零进判定核心 + `speed===260&&300` 逐字不变）/ `PN-SPEED-05`（只作用渲染层、串联 `B8`）/ `PN-SPEED-06`（若动 `preview`/`fork` 按 `forkSpan=fork*speed/L` 重算窗口）静态防泄漏断言。
- **丝滑**：`scene3d.jsx:382 useFrame` 启用 R3F `delta`，`world.update()` 升级 `updateInterpolated(f, delta)` 阻尼 lerp（`λ≈12–18/s`），0 新增 mesh / drawCall；`main.js:1069 dt clamp 0.033` 保留。
- **`≤180s` 门槛不变**：最慢 `174.57s` 仅 `5.43s` 余量（`gate-logs/S4.log:17-19`）；方案 B 下 `finishTime` 理论不变，但新增分叉 hold、删 `dashLeft`、撞石封顶、惩罚题 `SLOW 1.4s`（`race.js:508`）都会影响 → **必须以新实跑为准，不沿用 174.57s**（`PN-SPEED-01`）。

### 2.8 3D 只读几何补齐（视觉层，B8 / 答案域零泄露）

| 缺口 | 落点 | 白名单 / 断言同步 |
| --- | --- | --- |
| 石头 / 宝石几何 | `SNAPSHOT_KEYS` 加 `pickups` + 新建 `PICKUP_KEYS=["id","kind","t","lateral","taken"]`；`snapshot3d()` 纯投影 `state.pickups`；`scene3d.jsx createWorld()` 补 2 个 `InstancedMesh` | `EXPECTED_SNAPSHOT_KEYS`（`verify_p1_visual.py:41`）同步扩 `pickups` 并逐字留痕 |
| 跳跃两级可见 | `KART_KEYS`（`scene3d-model.mjs:67-69`）加 `hop/airMax`；`lift`（:209）改抛物线（`peak` 单跳 0.55m / 二段 0.85m，`H_ROCK=0.32m` 顶部导出常量与几何共用） | `EXPECTED_KART_KEYS`（:42）同步扩；`scene3d.jsx:257` y 通道现成、0 新增 mesh |
| 可见分叉五阶段 | `buildSceneFrame()` 增纯中性 `fork{flare,left,right,island,signL,signR}`（进 `SCENE_KEYS`），逐帧按判定 `t` 纯算、禁时间补间；`createWorld()` 增 2–3 mesh | `EXPECTED_GATE_KEYS`（:43）三键不动；`FORBID`（:37-39）不得夹带答案域 |
| `RECURSIVE_LEAK` | `verify_p1_visual.py:95-109` | 新增 `pickups`/`hop`/`forkPhase` 后不得命中 `FORBID`（`correct/answer/spoken/left/right/pairkey/qtype`…）；`GATE_KEYS` 保持 `["id","lap","commitT"]` |

> **B8 静态禁写（`verify_p1_gate.py:510-515`）**：3D 层硬禁 `localStorage.setItem` / `sessionStorage.setItem` / `race.state.\w+=` / `.odo=` / `.lateral=` / `g.line=`。新增字段**一律只读投影**，把石头/分叉状态写进 3D 层即 FAIL。方案 B 的 `VISUAL_FLOW_GAIN` 同样零写回上述判定量。

---

## 3. ADR-2 双锚定重锚 + 须同步改期望值的既有断言（不删 / 不豁免 / 不改 NOTE）

> 口径与 `p1-interaction-qa.md` §1 一致；下表为工程侧逐条落地清单。

| 断言 / 位置 | 现状 | 处置 | 是否放宽 |
| --- | --- | --- | --- |
| `BD-1` `verify_p0_gate.py:159-161` | 判定核心 5 文件 sha256 与 `p0-pre-20261109` 全等 | 切到 §0.3 新快照，逐字登记「旧→新」+ 批准时间；断言强度不降（§0.3） | 否 |
| `B3` `verify_p1_gate.py:451-457` | 7 文件 sha256 与 `p1-pre-20261110` 全等 | 同上；并集 8 文件（含 `headless_laps.mjs`） | 否 |
| `PLR-CSEG-S2` `verify_cseg_gate.py:61-62` | 写死 `"speed: 260"` / `"speed: 300"` | **期望值不变**（方案 B 判定层 `speed` 不动）；仅补 `PN-SPEED-04/05` 静态防泄漏 | 否 |
| `PLR-CSEG-A6` `verify_cseg_gate.py:164-166` | `2*19254.50/s<=150 for s in (260,300)` | **期望值不变**（`L=19254.50` 亦不动）；撤回「提速必 FAIL」旧判断 | 否 |
| `verify_p1_gate.py:396` 取时 | 正则 `\b(1[0-7]\d\.\d\d)\b` 只匹配 `100.00–179.99s` | **预防性修取法**：改解析 `headless_laps.mjs` `用时s` 列或末次汇总；**180s 门槛不变**。方案 B 下本轮不跌破 100s（理论下限 128.4s、实测 135.8–174.57s），但用户已点名须修，**不得以「本轮不触发」跳过** | 否 |
| `B1` `verify_p1_gate.py:426-427` / `BC-1` `verify_p0_gate.py:192-193` | `SRC_TAG="hud-20261108"`、`SRC_TAG_COUNT=46`、9 文件白名单 `SRC_SCAN_FILES`(:29-34) | tag 统一 bump 后按新 tag 值改常量、按**新实测总数**改 `46`；仍须「唯一且恰好 N」 | 否 |
| `BC-3` `verify_p0_gate.py:220-222` / `BC-6` `:268-271` | `dict(cnt)=={SRC_TAG:46}`、`vendor.manifest.json source_layer.count==46`、`VENDOR_TAG!="hud-20261108"` | 同上同步；`VENDOR_TAG="p0-20261109"` / `P1_TAG="p1-20261110"` 双层互不混算（`B7 :503-508`）口径不变 | 否 |
| 三条只读白名单 `verify_p1_visual.py:41-43` / `:198-203` | `EXPECTED_SNAPSHOT_KEYS` / `_KART_KEYS` / `_GATE_KEYS` **逐字锁定** | 新增 `pickups`/`hop`/`airMax`/`forkPhase` 后**同步扩期望值并逐字留痕**；`RECURSIVE_LEAK`(:95-109) 的 `FORBID`(:37-39) 不得夹带答案域。**加字段不改期望 = 必 FAIL，这是特性不是缺陷** | 否 |
| `PM-6` `verify_p1_gate.py:146` | 「零相交 / canvas 不吞点击」 | **重定义**为「`HIT_EXCLUDE` 边界不覆盖关键层 + 左右半屏映射正确」，保留原硬判据不降级（§2.6） | 否 |
| `PM-3` `:143` / `PM-2` `:142` | `#jump` 生效 / 左右选道改变投影 | `PM-3` 补「260ms 窗内第二击生效、窗外不生效、首击 ≤1 帧」；`PM-2` 补「键盘 + 半屏两来源投影方向一致」 | 否 |
| `index.html:188` 动态注入 | `s.setAttribute("src","assets/p1/"+"scene3d.js?v="+tag)` 拼接，**静态扫描抓不到 `?v=` 字面量** | bump 时**手工核对**该拼接变量；新增运行时断言「动态注入 URL 带当前 tag 且资源按字节送达」（`PVB-*` / `BV-1` 四重判定：逐字节 + magic + sha256 + Content-Type 非 `text/html`） | 否 |
| QA 补充：`PLR-CSEG-S1/S3/S4/S5/S6/S12/S13` `verify_cseg_gate.py:59-90` | 全是 `race.js`/`main.js`/`render.js` **源码字面量断言** | 改判定核心必破；按新源码逐字核对，改期望值须逐条给替代依据，**不得整族跳过** | 否 |
| QA 补充：`PLR-FRESH-F9b`、`verify_hud_spec.py:477/496` H11、`BC-2/BC-4`、`PDCORE-4`(:95)/`PDEG-4`(:187) | 卡面 URL 带 tag / tag 唯一 46 / 20 图零裸引用 / 两形态一致性 | tag bump + 交互改动后逐条复核；两形态 `finishTime` / 判定序列 / `rally.*` 仍须逐项一致 | 否 |
| `B8` `verify_p1_gate.py:510-515` | 3D 层静态禁写 | 新增只读字段后复跑；`VISUAL_FLOW_GAIN` 零写回判定量 | 否 |

**回归顺序（质量线 §7，不变）**：`S3 → S5 → S0 → S1 → S2 → S4 → S6`（S5 swiftshader WebGL 取证前置），新增 `S7 verify_p1_interaction.py` 独立承接 `PN-*` 真实 Chromium 交互，避免污染现有 121 计数；四项错误计数（`pageerror/console_error/requestfailed/bad_status`）归零仍是硬 `chk`；人工签收项仍列 `result.json.not_covered`，不冒充 PASS。

---

## 4. 只读观测点定稿（回执 quality-lead，供 `S7 verify_p1_interaction.py` / §8 断言总表用）

> 全部为**只读投影**，不新增判定状态、不写回 `odo/lateral/g.line`（B8）。以下字段名为**工程侧定稿**，可直接写进断言。

### 4.1 `window.__rally`（`main.js:1160-1181`）getter 扩

| 观测项 | getter / 投影路径 | 说明 |
| --- | --- | --- |
| 跳跃态 | `get playerJump()` → `{ hop, air, airMax, jumpCd, dashLeft, odo }` | 从 `race.state.player` 只读投影；`dashLeft`/`jumpCd` 删除后恒为 0/缺失，供 `PN-JUMP-03` 取证 |
| 撞石计数 | `get rockHits()` / `get rockBudget()` | `state.rockHits` / `state.rockBudget`（§2.3） |
| 道具 | `get pickups()` → `[{ id, kind, t, odo, lateral, taken, armed, cleared, visible }]` | `odo` 用 `race.js:570-571` 同款换算；`visible` 由渲染层派生 |
| 欢呼 | `get cheer()` → `{ word, seq, until }` | `state.cheer`（§2.4） |
| 彩带 | `get ribbonT()` | `state.ribbonT`（:581） |
| 分叉相位 | `get forkPhase()` → `"open"→"cards"→"decide"→"closing"→"single"` | 由 `state.decide.phase` + `splitterHalf()` f 派生，不新增判定状态 |
| 分叉张开 | `get splitterHalf()` → 逐帧 `f`（0..0.34） | `race.js:360-373` |
| 门 | `get gates()` → `[{ id, lap, commitT, line, span, merge, played, judged, hit }]` | `g.line`（:83）、`span`/`merge`（`race.state`） |
| 对手 | `get rivals()` → `[{ id, odo, lateral, laneTarget, home }]` | `race.state.rivals` |

### 4.2 双沿事件字段名（**定稿**，quality-lead 等此写断言）

- `input.jump`：首击 / 窗外重新起跳边沿（沿用现有 `jumpEdge` 消费链，`readInput:367-368`）。
- `input.jump2`：260ms 窗内第二击边沿（`jump2Edge`，`readInput` 新增）。
- 打点：两次 `pointerdown` / `keydown(Space)` 的 `performance.now()`（ms）差值 `<= 260`（±1 帧容差）；模块级 `lastJumpAt`（`main.js`）。键盘与触屏同源，`e.repeat` 拦截保留。
- 断言取证：`window.__rally` 增 `get jumpEvents()` → `[{ t: performance.now(), source: "key"|"pointer"|"halfTap", edge: "jump"|"jump2" }]`（只读环形缓冲，≤32 条）。

### 4.3 `window.__P1_SCENE__`（`scene3d.jsx:33`）快照扩

- 扩 `rocks[]`（屏占比 / 投影包围盒，复用 `kartProjected` 的 Box3 八点投影，`scene3d.jsx:295-306`）、`forkVisible: { left, right }`（左右分支可见标记）。
- **硬约束**：`EXPECTED_SNAPSHOT_KEYS` / `KART_KEYS` / `GATE_KEYS`（`verify_p1_visual.py:41-43`、`:198-203`）**逐字锁定**，加字段必须同步改期望值并留痕，否则必 FAIL；`RECURSIVE_LEAK`（:95-109）的 `FORBID`（:37-39）名单不得夹带答案域（`correct/answer/spoken/left/right/pairkey/qtype`）。

### 4.4 半屏命中层（DOM / `pointer-events` 边界 / 映射函数，**定稿**）

- **命中方式**：`window` 级 `pointerdown` 事件委托（不新增物理全屏层）。逻辑命中层标识 `#half-tap`（若需视觉高亮则为 `pointer-events:none` 的透明层，不参与命中）。
- **`pointer-events` 边界** = `HIT_EXCLUDE = "#hud, #touch, .panel, #confetti, #cheer, #signs, #tags, #minimap, #quiz, #board, #shop"`；`e.target.closest(HIT_EXCLUDE)` 命中则 return。层级实测 `css/game.css:44/194/223/144/136`。
- **左右半屏映射函数**：`onHalfTap(e)` → `left = e.clientX < window.innerWidth / 2` → `tapSteer`。取证用 `get halfTap()` → `{ left, right, lastClientX }`。

### 4.5 静态禁区

- `B8`（`verify_p1_gate.py:510-515`）：禁 `.odo=` / `.lateral=` / `g.line=` / `race.state.*=` / `localStorage.setItem` 写进 3D 层。
- `VISUAL_FLOW_GAIN`：**零进** `race.js` / `track.js` / `config.js` / `headless_laps.mjs`（`PN-SPEED-04`）；`DIFFICULTY.follow.speed===260 && DIFFICULTY.listen.speed===300` 逐字不变。

---

## 5. 三处低风险清理（team-lead 原派单 §2.7，登记不改）

| # | 落点 | 磁盘事实 | 清理 |
| --- | --- | --- | --- |
| 1 | `syncFork()` / `#fork-card` 死代码 | `ui.fork=querySelector("#fork-card")`（`main.js:28`）、`forkLeft/forkRight`（:29-30）在 `index.html` **无对应 DOM**（本轮 Grep 仅 `:50 #fork-count` 存在）；`syncFork()`（:695-703，`:1139` 调用）里 `if (ui.fork) ui.fork.hidden=true`（:697）恒不执行，实际只驱动 `#fork-count` 倒计时（:702） | 删除 `ui.fork/forkLeft/forkRight` 引用与 `syncFork` 中的死分支，保留 `#fork-count` 逻辑（或并入 `syncSigns`）；零行为变更 |
| 2 | `merge` 真值不一致 | `main.js:1123` 硬编码 `merge: 0.012` 传给 `render()`，而 `race.state.merge = TUNING.mergeDt = 0.028`（`race.js:9` / `config.js:17`）→ 2D 闭合视觉早于判定 | 统一到单一真值 `race.state.merge`（或作为 `buildSceneFrame()` 的 `opts` 常量传入）；分叉项开工前先修，否则 2D/3D 闭合相位分裂（美术线 §4.1 R3） |
| 3 | 3D `lift` 口径错误 | `scene3d-model.mjs:209 lift = air*scale` 把「滞空剩余秒数」误当高度（`0.004 m` 几乎不可见） | 改 `lift(p)=peak·sin(π·p)`、`p=1-air/airMax`（§A2，美术线 §5.3，`peak` 单跳 0.55m / 二段 0.85m、`H_ROCK=0.32m` 半埋）；与判定 `air` 共用归一化相位但纯视觉、不参与碰撞；`scene3d.jsx:257` y 通道现成、0 新增 mesh |

---

## 6. 待拍板 / 待确认（不阻塞本文件交付，阻塞最终回归放行）

> 已由 team-lead 2026-11-14 终裁关闭、不再待拍板：**NPC 速度下限 = 0.94×**（原 0.9× 作废，§2.5）、**词表 `Good/Excellent/Marvellous` 且不做连击偏向词**（§2.4）、**`race.js` 判定核心确实要改**（§0.1）、**方案 B 判定层 260/300 不变**（§2.7）、**批准 2026-11-14 09:53 + 并集 8 文件独立快照重锚**（§0）、**L2 装饰不进 `state.pickups`**（§A2）、**撞石 ≤2 次硬上限**（§2.3）。**P4 已给明确结论：答题不占 `finishTime`、答错 `SLOW 1.4s` 计入，净利好不撑破 ≤180s，但基线必须重跑**（§A3）。

1. **跳跃载体三选一**：工程侧已裁定「新建 `main.js` 输入层状态机 + 判定侧滞空见证式；删 `hopWindow` 死代码、不复活」（§1.4 / §A2），回执 quality-lead 关闭 `PN-JUMP-06` 二选一；如主理人有异议可推翻。
2. **「lift 覆盖 78unit 判定带」两选项**（§A2）：工程推荐**选项甲**（不改 `airMax`，靠标线 + 滞空见证式保证）；**选项乙**（延长 `airMax ≥ 0.99s` 满足严格字面）需主理人拍板取舍，E1 规格默认按甲落地。
3. **石头双保险**：`PN-ROCK-05a`（生成 ≤2 颗）+ `05b`（碰撞封顶）建议**两条都采纳**（§2.3）；用户最新拍板仅锁定「撞到 ≤2 次」硬上限，「生成 ≤2 颗」为主理人加的额外保险、用户可单独撤销。
4. **`VISUAL_FLOW_GAIN` 常量名 / 落点**：全产品层当前 0 命中，实现后由工程侧同步字段名供 `PN-SPEED-04/05` 定位。
5. **§2.1「滞空见证式」带来的行为变更**（进窗石头在见证/落地/出窗时定案一次）须 `PDCORE-4`/`PDEG-4` 两形态一致性实跑取证，不沿用旧基线。
6. **视觉定稿数值**（美术线 v1.2）：`h_rock=0.32m` 半埋、单跳 `lift` 峰值 0.55m / 二段 0.85m、`lift(p)=peak·sin(π·p)` 与 `air` 共用归一化相位；`H_ROCK` 与几何共用常量，避免两处漂移（§A2）。

---

## 7. 边界声明

- 本轮**仅写入本文件** `design/p1-interaction-impl.md`；产品代码（`.js/.jsx/.mjs/.html/.css`）、`verify_*.py`、`result.json`、`gate-logs/`、`deploy.sh` **零改动**。
- **未运行任何门控**：未执行 `py -3.13 verify_*.py`、未执行 `npm run *`、未启浏览器 / HTTP 服务、未部署 / 上线 / commit / push。
- 全文 `文件:行号` 经本轮磁盘逐条复核；纯计算（分叉窗口 1475.1/1559.1 unit、第 5 石 t≈0.62875、`air` 有效窗 0.45s/117–135 unit、碰撞窗口 156 unit、lift 0.004m）经本轮独立复算，与质量线 / 美术线一致。
- 本文为**工程实现规格**，全部改动**均未实现、未实跑、未验证**，不构成 PASS 结论；质量门 advisory，最终放行与发布签字由用户决定。

---

*P1 交互工程实现规格 v1.0 · engineering-lead 程基岩 · 2026-11-14 · 依据用户 2026-11-14 最终拍板 + team-lead E1 补充取证 + 质量线磁盘纠错 + 本轮只读盘查与纯计算 · 主因=3D 石头不可见(时机) + scanPickups 首帧点采样/hopWindow 死代码 · 权威裁定：删 hopWindow / 260ms 状态机新建于 main.js 输入层 / 单跳必过绑 air 覆盖碰撞窗不绑双击 · ADR-2 双锚定与质量线 §0.1–§0.3 口径一致 · 产品代码零改动*
