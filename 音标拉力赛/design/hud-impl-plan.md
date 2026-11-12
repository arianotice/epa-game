# 音标拉力赛 · 本轮 2D HUD 落地实现方案（CSEG-E0 只读盘查）

> 作者：engineering-lead（程基岩 / 技术方向） · 阶段：Task #3 只读盘查，实现另见 #4
> 范围：进入比赛页右上角「该轮比赛小地图」＋「分叉预告路牌」的**实现方案与影响面**，本轮不落地、不改渲染层视角（真 3D 化下一轮）。
> 基准：`C:/Users/86135/WorkBuddy/英语音标播客`，所有行号基于本阶段备份时的文件快照（sha256 见 §F manifest）。
> **本阶段未修改任何产品文件**。唯一写操作 = 本文档 + `C:/Users/86135/AppData/Local/Temp/hud_backup_20261108/`（回滚点）。
> 依赖：`design/hud-ux-spec.md`（#1 design-strategist，**已定稿并逐节核对**）、`design/visual-direction-3d.md`（#2 art-director，下一轮 3D 方向稿，本轮不消费）。#4 的视觉尺寸、文案、触发单位以 **§0.0 收尾基线 + #1 规格 + 主理人另行下发的 #4 规格** 为准。
> **修订记录 2026-11-08**：并入 team-lead 独立读码下发的事实纠正（5 条）、Q1–Q4 裁决（4 条）与缓存串定值。见 §0.0；§A–§I 与之冲突处一律以 §0.0 为准。

---

## 0.0 收尾基线 · 主理人独立核实与 Q1–Q4 裁决（优先级最高）

> 本节为 Task #3 的**收尾裁决记录（ADR 式）**。team-lead 独立读码后下发 5 条事实基线 + Q1–Q4 裁决 + 缓存串定值；我已用 `Read` / `Grep` 对源码逐条复核（复核结果见 0.0.1「实证」列）。
> **效力**：§A–§I 中凡与本节冲突者，**一律以本节为准**；本节未覆盖的链路盘点、精确行号、tag 直方图、四套门控断言、回滚点等实证事实**继续有效**（均为只读核实，无产品文件改动）。
> **本阶段仍只读**：唯一写操作 = 本文档 + `C:/Users/86135/AppData/Local/Temp/hud_backup_20261108/`。不部署、不上线、不 commit；**#4 完整实现规格由主理人在 #3 回传后单独下发**，本阶段不动 #4、不改产品文件。

### 0.0.1 事实基线（5 条，已复核）

| # | 事实基线 | 源码实证（已复核） | 对我原报告的影响 |
|---|---|---|---|
| **F1** | `drawMinimap()` **已存在**，本轮是**增强既有实现**（DOM 化 + 信息层级 + 显式显隐），**不是从零新建第二套小地图** | `render.js:420 drawMinimap(ctx,w,track,karts)`；`render.js:416 if (view.minimap !== false) drawMinimap(...)`；`main.js:987 minimap: mode !== "title"`。固定 `132×86`、`x0=w-132-16 / y0=16`，画赛道闭环 + 3 车点（player `#2f6f8f` / rival a `#a33b3b` / rival b `#3d6b45`） | §0-1 / §A.1 已写「不是从零新建」，一致；但 §B.2 方案 ① 措辞像「另起炉灶」→ 修订为「**把既有 `drawMinimap()` 迁入 DOM 容器的内嵌 canvas**」，不新增第三套绘制 |
| **F2** | 美术方向稿 `design/visual-direction-3d.md` §I.5 / 附录① 断言「`#route-map` 与 `drawMinimap` 当前位置重叠」**不成立**：两者**互斥** | `#route-map`（`index.html:16-18`、`game.css:20-34`，176×118 / right16 / top16）由 `main.js:256 ui.routeMap.hidden = next !== "title"` 控制，**只在 title 页显示**；`drawMinimap` 只在 `mode !== "title"` 绘制。右上角裁定为**「title 页 = a1 四区大地图入口 / 比赛中 = 该轮闭环小地图」的同位置角色切换，不新增第三层** | **#4 不得据此做位移或删除 `#route-map`** —— 它在标题页承担世界观导航与跨站入口（`href="../音标大闯关/index.html#/map"`），删了会丢功能。原报告 §A.2「右上角归属」保留并补强此互斥结论（原文本已写「比赛态隐藏」，未误判重叠） |
| **F3** | `DIFFICULTY.preview = 4.2 / 4.0` 定义后**无任何代码读取**；`race.js:777 previewSteer()` 是同名不同物（倒计时转向插值），不消费该配置。**本轮可直接启用为预告阈值** | `config.js:38 / :48`；全仓 `preview` 仅命中定义 2 处 + `main.js:943` / `race.js:777` / `race.js:838` 的 `previewSteer` | §0-2 / §C.1 / §G6「死字段」结论一致；单位与公式的**最终口径见 0.0.3（以 #1 `D_preview` 为准）**，我原 §C.2 的 `preview*v` 降级为盘查阶段估算 |
| **F4** | `#signs`（`index.html:19`）经 `main.js:493-494 placeLaneSign(ui.signL/ui.signR, ...)` 呈现，是**分叉门两侧词牌，含 word / IPA，属于答案载体**，不是「预告路牌」 | `main.js:458-496 syncSigns()` + `paintLane()`；`game.css:125` `#signs` z=4 / pointer-events:none | 新增预告须**另立 S1 零文本中性态**，且 S2 **严格对称、不得指向 `correctLateral` / `spoken`**。§A.4「既有路牌不是分叉预告」结论一致；§C.4 不泄答案约束保留并强化 |
| **F5** | `minimap: mode !== "title"` 会在 `teach / results / quiz / boardOpen / shopOpen` 下**误绘**，属实，须改**显式显隐** | 现有 mode 取值：`title / teach / countdown / racing / paused / quiz / results`；`boardOpen` / `shopOpen` 是叠加软锁（打开时 `mode` 仍是 `racing`，`main.js:811-821`、`874-889`），**不能只看 mode** | §A.5 / §D.5-1 的显隐口径被覆盖 → 按 0.0.3 的 `visible` 表达式；`results` 由「可见」改「隐藏」 |

### 0.0.2 Q1–Q4 裁决（已定，4 条）+ 缓存串定值

| 裁决 | 结论 | 落地要点（供 #4） |
|---|---|---|
| **Q1** | **A · 小地图 DOM 化**（QA 需 DOM 存在性 / 不重叠断言；3D 轮 HUD 直接复用同一契约） | 采用 #1 §2.1.1 方案 A：`<div id="minimap" aria-hidden="true">` + 内嵌 `<canvas id="minimap-c">` + `<span id="minimap-lap">`，`position:fixed; z-index:5`，**DOM 顺序置于 `#hud` 之后**（同层时在其上），`pointer-events:none`，半透明底板 alpha ≥ .82。**覆盖**我原 §B.2 AD-1 的「内联 SVG + 建议 z-index 6」 |
| **Q2** | **quiz 冻结时路牌隐藏**（避免 `#quiz-prompt` 在 ipa/type 题写出 `q.spoken.word` 与分叉门两侧词同屏构成提示） | `#signs.hidden = true`；小地图在 quiz 下**显示但冻结**（`karts[].odo` 不推进、`simTime` 不增）。回 `racing` 按 `played` 无缝重现 S2，不重新 `audio.playWord`、不重播 `open` 动画。**覆盖**我原 §A.5 / §C.4 / §G4「保持显示但静止」 |
| **Q3** | **两者都做**：S1 世界空间中性牌 + 小地图中性菱形（用户已拍板「预告给路牌」，仅菱形不算路牌落地） | **S1 复用现有 `#sign-l / #sign-r`，零新增路牌 DOM**，仅把 `placeLaneSign()` 的 `span` 参数化为 `spanEff`（S1 传 `D_preview/L`，S2 传 `race.state.span`）；`syncSigns()` 改为 #1 §2.2.1 完整 **S0–S3 状态机**，S1 调 `paintForecast()`（零文本中性外壳），S2 调现 `paintLane()`；`signKey` 纳入 `phase`。小地图侧同步点亮 #1 §2.1.2 的**中性菱形** `nextGate`。**覆盖**我原 §C.1 AD-2 / §D.1 的「新增 `syncForkHint()` + `#fork-hint` DOM」 |
| **Q4** | **本轮不改** `placeLaneSign` 的 `t` / `odo` `0.02·L` 偏差（修正会移动所有既有路牌、扩大回归面）；新增逻辑一律用 **`t_i = (odo_i / L) % 1`** 从绝对 `odo` 派生；旧不一致**登记为遗留项** | 偏差根因：`t0 = gate.commitT − k·span`（相对）与 `odo0 = gate.line − k·span·L`（绝对）差 `startOdo/L = 0.02`（≈385 里程），因 `commitT` 未含 `startOdo` 偏移（`race.js:83`）。**不改**既有 `0.66 / 0.34 / 0.36` 系数、`project()` 调用、`--lane`、`visible` 裁剪；S12 字面量 `"race.branchLateral(gate, odo0, side)"` 不得删除。遗留项见 §G12 |
| **缓存串** | 新 tag 定为 **`hud-20261108`**（本轮统一 bump 一次） | 三套脚本 `TAG` 常量（`verify_cseg_gate.py:24` / `verify_fresh_gate.py:30` / `verify_c08_gate.py:29`）与 **S18** 判据同步；另含 `verify_cseg_ui.py:26` 死常量、`config.js:7 CACHE_TAG`、`headless_laps.mjs:19`。**覆盖**我原 §D.4-1 / §H-4 的「`cseg-20261108` 或主理人指定」 |

> **Q1 与 Q3「DOM」范围澄清（防误读）**：Q1 的 DOM 化**允许**新增 `#minimap` 容器 + 内嵌 canvas + lap span（这是小地图载体）；Q3 的「零新增 DOM」**专指路牌预告**（复用 `#signs`）。两者不矛盾，#4 不得把 Q3 误读成「整个 HUD 都不许加任何 DOM 节点」。

### 0.0.3 与 #4 直接相关的收敛口径（#1 已定稿，#4 以主理人下发规格为最终准）

1. **显隐表达式**（#1 §2.1.6，覆盖 F5）：
   ```
   visible = (mode ∈ {countdown, racing, paused, quiz}) && !boardOpen && !shopOpen && !!race
   ```
   `title / teach / results` 隐藏；`boardOpen || shopOpen` 隐藏（此时 mode 仍是 racing）；quiz 显示但冻结 + 路牌隐藏（Q2）。**不得**再依赖 `minimap: mode !== "title"` 或「画面冻结了就不会变」——`render()` 与 `syncSigns()` 在 frozen 期每帧仍执行（`main.js:990`）。
2. **预告阈值**（#1 §2.2.2）：`D_preview = span·L + 0.5·p·v` = **follow 1482 里程 / 5.70 s**、**listen 1620 里程 / 5.40 s**；`span·L = fork·v` = 936 / 1020；`0.5·p·v` = 546 / 600。时序 `D_preview > lead(1036/1107) > S1 定位(534/583) > S2 定位(337/367) > 0`。**覆盖**我原 §C.2 的 `preview*v = 1092/1200`（仅比 lead 早 0.22 / 0.31 s，玩家几乎无感知）。阈值用**名义 `diff.speed` 常量**，不读 `speedNow()`（防 BOOST/TURBO/SLOW 抖动）。
3. **375px 避让**（#1 §2.1.3 / 2.1.4）：`--mm-w` PC 160px / 触屏 `min(96px, 26vw)`；`--mm-h` 104 / `min(64px, 17vw)`；`#hud { padding-right: var(--mm-right-gutter) }`（PC 184px / 触屏 120px）是**核心机制**，不靠 JS 动态测 HUD 高度；`#banner` 窄屏下移 `top: calc(var(--mm-h) + 20px)`；375px 硬约束 `mm.width ≤ 112.5px`、`left ≥ 0 && right ≤ 375 && bottom < 667`；`placeLaneSign()` 增**小地图矩形避让裁剪**（牌中心落入 `mm.rect` 外扩 8px 则 `el.style.visibility="hidden"`）。
4. **坐标与数据**：小地图环线点位 / 进度弧 / 圈数一律用 `odo / (laps · L)`，**不用 `t`**（两圈会重复）；`nextGate` 菱形位置 `track.sample((nextGate.line / L) % 1)`；保留纯函数 `minimapModel(view)` 供 Node 单测与 QA 断言（#1 §2.1.1 / H1 / H10 均引用）。
5. **不泄答案（单向铁律）**：`correctLateral` 与 `spoken` 只允许出现在 `audio.playWord()`（`race.js:436`）与 `judge()`（`race.js:213-262`）；任何 HUD 生成路径（DOM `innerHTML`、canvas `fillText`、CSS `data-*`、alt、aria-label）不得接触。S1 零文本（无 word / IPA / label / sprite / 左右色差 / 先后差异），S2 两侧同帧同尺寸同不透明度。
6. **tag 计数仍 46**：`#minimap` / `#minimap-c` / `#minimap-lap` 均**无 `src`**，不产生 `?v=` 字面量；但若把 `minimapModel` 抽成新模块 `js/minimap.js` 并 import 会 +1 → 47，触发 S17/F8a/S1.7 三处 `==46` FAIL。**控制项：逻辑并入既有 `main.js` / `render.js`，不新建模块** → 46 保持，三处断言不用改。
7. **跨站零影响**：Q1–Q4 均不新增 localStorage 字段，`音标大闯关/js/store.js` 零改动、`RALLY_FOREIGN` 不扩充（§E 结论不变）。
8. **headless 零影响**：Q3「激活 `preview` 读取」只改 HUD 消费侧，不改 `DIFFICULTY` 数值、`TUNING`、`track.js`、`race.js` 仿真与 `createRace()` 入参 → `headless_laps.mjs` 11 场 finishTime 不变（§D.2(5) 结论不变）。

### 0.0.4 冲突对照表（原报告 → 收尾裁定）

> 阅读方式：**「原表述」列全部为已作废的盘查阶段旧口径**（故其内可能出现 `preview*v` / `z-index:6` / 「保持显示但静止」等字样，仅为对照，不是指令）；**只有「收尾裁定」列是 #4 的执行依据**。

| 原报告位置 | 原表述（已作废，仅作对照） | 收尾裁定（以此为准） |
|---|---|---|
| §0-6 / §H | 「需主理人裁决 3 项」/ 待裁决清单 | Q1–Q4 + tag **全部已裁决**；§H 改为「已裁决记录 + 剩余知识缺口」 |
| §B.2 AD-1 | 推荐「独立 DOM 层 + 内联 SVG」，建议 `z-index:6` | **Q1=A DOM 化**：`#minimap` + 内嵌 `#minimap-c` + `#minimap-lap`，`z-index:5`，DOM 顺序在 `#hud` 后；SVG 方案作废 |
| §C.1 AD-2 / §D.1 | 新增 `syncForkHint()` 与 `#fork-hint` DOM | **Q3**：改造 `syncSigns()` 为 S0–S3；复用 `#sign-l/r`；**零新增路牌 DOM** |
| §C.2 | 预告阈值 `preview*v` = 1092 / 1200 里程（4.20 / 4.00 s） | **#1 `D_preview`** = 1482 / 1620 里程（5.70 / 5.40 s） |
| §A.5 / §C.4 / §G4 / §D.5-6 | quiz 时「路牌保持显示但静止 / 预告牌静态」 | **Q2**：quiz 时 `#signs.hidden = true`；小地图显示但冻结 |
| §D.5-1 | 「countdown/racing/paused/quiz/**results** 可见」 | 按 #1 §2.1.6：`results` **隐藏**；`boardOpen/shopOpen` 隐藏 |
| §D.4-1 / §H-4 | 新 tag「`cseg-20261108` 或主理人指定」 | **`hud-20261108`**（定值） |
| §G1 | 建议 `z-index:6`、「缩小到 ~96×64 并下移」 | `z-index:5` + `#hud` gutter 为避让核心；尺寸按 #1 §2.1.3 CSS 变量 |
| §A.2 右上角归属 | 「比赛态隐藏 → 右上角空间释放」 | 保留，并补 **F2**：`#route-map` 与 `drawMinimap` 互斥、同位置角色切换、**不新增第三层、不位移/不删除 `#route-map`**（美术方向稿 §I.5/附录① 的重叠断言不成立） |

---

## 0. 结论摘要（先看）

1. **右上角小地图不是从零新建**：`js/render.js:420-458` 已有 `drawMinimap()`，由 `render.js:416` 在 `view.minimap !== false` 时调用，`main.js:987` 以 `minimap: mode !== "title"` 控制。它画一个 132×86 的椭圆赛道轮廓 + 3 个车点（右上 `x0=w-132-16, y0=16`）。它**不含**圈数、闸门/分叉标记、四区地图差异化、路牌预告，且画在无 z-index 的主 canvas 内，比赛时会被 `#hud`(z-index 5) / `#banner`(z-index 6) 遮挡 → 这正是本轮要「**增强 + DOM 化 + 显式显隐**」的对象，而非新建第二套小地图（F1 / Q1）。**注意 F2**：`#route-map`（title 页 a1 四区大地图入口）与它**互斥**，右上角是**同位置角色切换、不新增第三层**，`#route-map` 不动不删。
2. **`DIFFICULTY.preview`（4.2 / 4.0）是死字段**：`config.js:38`、`config.js:48` 定义，但全仓运行时代码从未读取 `diff.preview`（已 grep 验证）；`race.previewSteer()`（`race.js:777`）是倒计时转向插值，同名不同物、与此数值无关（F3）。本轮直接启用为预告阈值，不改数值；公式以 #1 `D_preview = span·L + 0.5·p·v` 为准（§0.0.3）。
3. **缓存串口径**：46 处 `?v=cseg-20261107` 字面量（9 个文件，S17 / F8a / S1.7 三处断言都锁 `count==46`），另有 6 处 `cseg-20261107` 字符串（config `CACHE_TAG` + 4 个脚本 `TAG` + headless `TAG`）**不计入 46**。裁决方案「逻辑并入既有 main.js/render.js、**不新建模块**、HUD 用无 src 的 DOM、样式进既有 game.css」→ **新增 `?v=` 字面量净变化 = 0**，46 保持，三处 `==46` 断言无需改；46 处字符串整体替换 + 6 处 TAG 常量同步，新值定为 **`hud-20261108`**（§0.0.2）。
4. **不新增任何 localStorage 字段** → `音标大闯关/js/store.js` 零改动，`RALLY_FOREIGN` 无需新增，跨站影响为零（§0.0.3-7 确认）。
5. **headless_laps.mjs 的 11 场 finishTime 零影响**：它只 import `config.js / track.js / race.js`，不 import `main.js / render.js`；只要 #4 不动 `TUNING` / `DIFFICULTY` 数值、`track.js` 几何、`race.js` 仿真与 `createRace()` 入参，A0–A6 全绿（§0.0.3-8 确认）。
6. **Q1–Q4 已全部裁决**（DOM 化 / quiz 隐藏路牌 / S1+菱形两者都做 / 不改 0.02·L 偏差），tag 定为 `hud-20261108` → 见 **§0.0 收尾基线**（优先级最高）与 §H 裁决记录；#4 规格由主理人另行下发。

---

## A. 现有链路盘点（精确行号）

### A.1 文件职责与 HUD 绘制入口

| 文件 | 行数 | 与 HUD 相关的职责 | 关键行号 |
|---|---|---|---|
| `音标拉力赛/index.html` | 165 | DOM 骨架；2 个 canvas；全部浮层；2 处带 tag 的脚本/样式引用 | 15 `#c`；16-18 `#route-map`；19-22 `#signs/#sign-l/#sign-r`；23 `#tags`；25-39 `#hud`；41 `#fork-count`；42 `#cheer`；43 `#confetti`；44 `#banner`；45 `#live`；47-52 `#touch`；54-158 各 panel；162-163 scripts |
| `音标拉力赛/css/game.css` | 361 | 全部 z-index / 定位 / 375px 媒体查询；**本文件 0 处 `?v=` 字面量** | 详见 A.2 |
| `音标拉力赛/js/main.js` | 1015 | 状态机 `setMode`、帧循环 `frame`、`render()` 调用与 view 组装、路牌/标签/预告同步、HUD 文本、存档 `commit` | 13 `ctx=#c.getContext("2d")`；18-74 `ui` 表；244-274 `setMode`；458-496 `syncSigns`；498-521 `placeLaneSign`；523-535 `syncTags`；537-542 `placeSign`（**死函数，未被调用**）；544-558 `syncQuizTilt`；560-568 `syncFork`；587-606 `drawConfetti`（590 第二个 2d ctx）；622-657 `syncHud`；731-739 `resize`；933-995 `frame`；996-1013 `window.__rally` |
| `音标拉力赛/js/render.js` | 463 | 主 canvas 全部 2D 绘制；离屏纸纹缓存；**既有小地图**；世界→屏幕投影 | 3-31 `paper()`（10 离屏 `getContext("2d")`，第三个 2d ctx）；43-57 `flareAt`；218-418 `render()`（220 `setTransform(dpr…)`，233 `matrix=getTransform()`，408 `restore()`，410-414 vignette，416 调 minimap，417 `return matrix`）；420-458 `drawMinimap`；460-463 `project` |
| `音标拉力赛/js/race.js` | 853 | 纯仿真：状态、门线绝对里程、判定、钱包 delta | 8 `span=forkSpan`；48-79 `state`；83 `g.line=startOdo+lineT*L`；164-175 `activeGate`（按 `g.line-player.odo`）；182-188 `speedNow`；298 `kart.t=(odo/L)%1`；336-358 `branchLateral`；421-439 `beginDecide`；597-763 `update`（605 `state.time+=dt`，611-617 跨圈）；777-794 `previewSteer`；847-850 `pointAt` |
| `音标拉力赛/js/track.js` | 79 | 固定椭圆几何（**只吃 TUNING，不吃 mapId**） | 3-71 `createTrack`（27-29 累计长度，51-64 `sample(t)`，66-68 `samples` N=520，70 返回 `{length,sample,samples,roadHalf}`）；73-75 `offsetPoint` |
| `音标拉力赛/js/config.js` | 316 | 参数/题库/门生成；`CACHE_TAG` | 7 `CACHE_TAG`；9-18 `TUNING`（laps=2, commits=[0.24,0.68]）；31-52 `DIFFICULTY`（260/300、preview 4.2/4.0、fork 3.6/3.4）；69/78/92 `${CACHE_TAG}` 模板；179-204 `RACE_MAPS`；264-299 `buildGates`；301-303 `forkSpan` |
| `音标拉力赛/js/headless_laps.mjs` | 154 | 11 场两圈实跑，产出 finishTime | 19 `const TAG`；21-23 动态 import；111-120 11 场；134-148 断言 |
| 4 套验收脚本 | 300/240/346/315 | 静态源码 + 浏览器 DOM + 物理文件 | 见 §D |

**三个 2D context（勿混淆）**：`main.js:13`（主 `#c`）、`main.js:590`（`#confetti`，独立 canvas，z-index 11）、`render.js:10`（离屏 `paper()` 缓存，非 DOM）。新增小地图若用独立 canvas 会是第四个 2d ctx。

### A.2 DOM 结构与 canvas 叠放顺序（z-index 实证）

`#c` 在 `index.html:15` 是**无定位、无 z-index** 的普通流元素（`game.css` 中查无 `#c` / `canvas` 规则；body `overflow:hidden`，`game.css:17`）。尺寸只由 `main.js:731-737 resize()` 写位图属性 `canvas.width=round(w*dpr)` / `height=round(h*dpr)`（`dpr=min(2,devicePixelRatio)`），`render.js:220` 用 `setTransform(dpr,…)` 绘制。**结论：canvas 处于叠放最底层，所有 `position:fixed` 且带 z-index 的浮层都在它之上。**

| 层 | 元素 | z-index | 定位 / 尺寸 | 出处 |
|---|---|---|---|---|
| 底 | `#c`（主 canvas，含 `drawMinimap` 画的小地图） | 无（auto，文档流） | 位图 w×h×dpr | index.html:15 |
| 4 | `#tags` / `#signs` | 4 | fixed inset:0，pointer-events:none | game.css:82 / 125 |
| 5 | **`#hud`** | 5 | fixed top:0 left:0 right:0，`padding:8px 12px 0`；`.hud-row` flex-wrap，含 place/kart-type/gates/gems/shields/btn-board/combo/spacer/btn-mute/btn-pause | game.css:37-58；index.html:25-39 |
| 6 | `#route-map` | 6 | fixed top:16 right:16，176×118，图片「探险地图」 | game.css:20-33；index.html:16-18 |
| 6 | `#banner` | 6 | fixed top:78px 居中，max-width min(640, 100%-24px) | game.css:118-123 |
| 6 | `#fork-count` | 6 | fixed top:38% 居中 | game.css:150-155 |
| 7 | `#touch` | 7 | fixed bottom:0，4 列栅格 | game.css:165-180 |
| 8 | `.panel` / `.count` / `.fork-card` | 8 | 居中面板；`.fork-card` 有 CSS **但 index.html 无对应 DOM** | game.css:93-105 / 194-199 / 338 |
| 9 | `#how` | 9 | 左侧竖排 tab | game.css:226-235 |
| 10 | `#how-panel` | 10 | 居中 | game.css:256-269 |
| 11 | `#confetti` | 11 | fixed inset:0，pointer-events:none | game.css:116 |
| 12 | `#cheer` / `#shop-panel` | 12 | 居中 / 左上 | game.css:108-115 / 203-211 |

**右上角归属（F2 收尾纠错，优先级最高）**：`#route-map`（176×118 @ top16/right16）在 `setMode()` 里由 `main.js:256` 控制 `ui.routeMap.hidden = next !== "title"`，**只在 title 页显示**；既有 `drawMinimap`（`x0=w-148, y0=16, 132×86`）只在 `mode !== "title"` 绘制 → **两者互斥，从不同时出现**，因此美术方向稿 `visual-direction-3d.md` §I.5 / 附录① 断言「`#route-map` 与 `drawMinimap` 当前位置重叠」**不成立**。
- ✅ **主理人裁定**：右上角 = 「**title 页 = a1 四区大地图入口 / 比赛中 = 该轮闭环小地图**」的**同位置角色切换，不新增第三层**。`#route-map` **保持不动、不位移、不删除** —— 它在标题页承担四区世界观导航与跨站入口（`href="../音标大闯关/index.html#/map"`、`a1.webp`），删了会丢功能（§G11）。`#minimap`（Q1 DOM 化后，`z-index:5`）占用的是同一右上角锚点，但不是叠加在 `#route-map` 之上。
- **`#hud`(z5) 在比赛态占满顶部整条，375px 下 `.hud-row` flex-wrap 成 2–3 行（≥90px 高），`y=8..100` 区域被 HUD 覆盖；`#banner`(z6, top78) 窄屏近全宽，压住小地图下部** —— 这才是「375px 右上角拥挤」的结构性根因，也是既有 **canvas 内**小地图显示不全的原因（主 canvas 无 z-index，位于最底）。Q1 DOM 化 + `#hud` gutter + `#banner` 下移解决之 → 见 §B / §G1。

**死钩子（可复用，非既有功能）**：`ui.fork=#fork-card`、`ui.forkLeft=#fork-left`、`ui.forkRight=#fork-right`（`main.js:28-30`）在 index.html 中**不存在**，`syncFork()` 用 `if (ui.fork)` 保护；`placeSign()`（`main.js:537-542`）定义后从未调用；`.fork-card` CSS（`game.css:93-105`）无对应 DOM。⚠️ **Q3 已裁决「零新增路牌 DOM」（复用 `#signs`）→ 本轮这套遗留不启用**，仅登记为可清理的死代码。

### A.3 坐标系与 `pointAt()` / `branchLateral()` 用法

- **世界坐标**：`track.js:1` 明确「y 向下」。`createTrack(TUNING)` → `length=19254.50`、`samples[520]`、`roadHalf=520`（`track.js:70`）。**几何与 mapId 无关**：`track.js` 只接收 `TUNING`，四区共用同一椭圆（§B 差异化约束）。
- **`sample(t)`**（`track.js:51-64`）：`t` 归一化 0..1（`t%1` 取模），返回 `{x,y,fx,fy,rx,ry,t}`，`fx/fy` 单位切向，`rx/ry=(-fy,fx)` 右法向。
- **`offsetPoint(s, lateral)`**（`track.js:73-75`）：`{x:s.x+s.rx*lateral, y:s.y+s.ry*lateral}` —— 此处 `lateral` 是**世界单位（像素量级）**，不是归一化。
  - `render.js:88` / `render.js:62` 用 `offsetPoint(s, lateral*H)`，`H=roadHalf`，`lateral` 为归一化 ±1。
- **`race.pointAt(t, lateral)`**（`race.js:847-850`）：`offsetPoint(track.sample(t), lateral*track.roadHalf)` —— **入口 lateral 是归一化 ±1**，内部乘 `roadHalf` 转世界单位；`t` 是**相对圈内位置**（`track.sample` 内部取模）。
- **`race.branchLateral(gate, odo, side)`**（`race.js:336-358`）：返回**归一化** lateral（车道中心/岛沿以 ±1、0.28 等表达），其 flare 曲线由**绝对里程 `odo`** 相对 `gate.line` 计算（`start=gate.line-spanLen`、`full=gate.line-0.42*spanLen`、`end=gate.line+merge*L`，337-345）。
- **`project(matrix, x, y, dpr)`**（`render.js:460-463`）：`DOMPoint(x,y).matrixTransform(matrix)` 后 `/dpr` → 屏幕 CSS 像素。`matrix` 是 `render()` 内 `ctx.getTransform()`（`render.js:233`），含 `setTransform(dpr…)` + `translate(w/2,h*anchor)` + `rotate(-heading-π/2)` + `scale(zoom)` + `translate(-camera)`（220-232），`render()` 在 417 返回它，`frame()` 在 972 接收，供 `syncSigns/syncTags/syncQuizTilt` 使用。
- **HUD 关键推论**：`project()` 是**主相机矩阵**，与小地图的「赛道俯视全图」不是同一变换。小地图投影应复用既有 `drawMinimap()` 自己的线性变换（431-440 的 `minX/minY/maxX/maxY → sc/ox/oy`），**不要**用 `project()`；`pointAt()` / `branchLateral()` 只用于主视野内的路牌/标签定位。

### A.4 `placeLaneSign()` 现状与可复用点

`main.js:498-521`：

```
span = race.state.span                       // 499, 归一化 = fork*speed/L
t0/t1/t = gate.commitT - span*{0.66,0.34,0.36}   // 500-502 相对圈内 t
L = track.length; odo0/odo1/odo = gate.line - span*L*{0.66,0.34,0.36}  // 505-508 绝对里程
p0 = race.pointAt(t0, race.branchLateral(gate, odo0, side))  // 509-511
a/b/c = project(matrix, p.x, p.y, dpr)      // 512-514
ang = atan2(b.x-a.x, a.y-b.y)               // 515 路牌旋转
visible = c.x>-80 && c.x<w+80 && c.y>-80 && c.y<h-20  // 516
el.style.left/top/--lane                    // 517-520
```

- `main.js:503-504` 的 C 段注释是**必须遵守的口径**：`pointAt` 用相对 `t`，`branchLateral` 已改绝对里程、必须传 `gate.line` 对应的绝对 `odo`，否则横向偏移恒为 0、路牌贴中线不动。`verify_cseg_gate.py:86-87`（S12）以字面量 `"race.branchLateral(gate, odo0, side)"` 锁死此写法 → **#4 重构不得删除该字面量**。
- **可复用点**：整套「相对 t + 绝对 odo → pointAt → project → DOM style」管线可被分叉预告牌直接复用（只需换系数与侧别）；`syncSigns()` 的 `signKey = \`${gate.id}:${gate.left.word}:${gate.right.word}\``（`main.js:475`, 变量在 94）是**按 gate.id 去重/复位**的现成机制，两圈天然不串；`beginCountdown()` 的 `signKey=""`（`main.js:387`）是开局复位点。
- **显示条件**：`syncSigns()`（`main.js:458-462`）`show = !!(deciding || (act && act.gate.played && !act.gate.judged))`，其中 `act=race.activeGate()`；`paintLane()`（439-444）把左右候选的 word/ipa/sprite 写进 `#sign-l/#sign-r`。**既有路牌是「闸门车道标签」，不是「分叉预告」**；预告需在更远处触发、且不能带答案。
- `#signs` 容器 `z-index:4` / pointer-events:none（`game.css:125`），`.sign.on-lane` 用 `translate(-50%,-50%) rotate(var(--lane))`（134-145）。

### A.5 仿真冻结与 `frame()` 循环（双累加器）

`main.js:931-995`：

```
last = performance.now(); simTime = 0                        // 931-932 渲染/仿真时钟
frame(now):
  dt = clamp((now-last)/1000, 0, 0.033)                     // 934
  frozen = paused|results|quiz|boardOpen|shopOpen            // 938
  if (!frozen) simTime += dt                                // 939  ← 冻结期不累加
  input = readInput()                                       // 940
  title/teach → updateDemo(dt)                              // 941
  countdown   → previewSteer / nitro / count / launch       // 942-957（不调 race.update）
  racing      → if(!boardOpen&&!shopOpen) race.update(dt,input) // 959 ← 唯一推进仿真处
                 race.state.quiz → openQuizCard()            // 960
  quiz        → 只 followCamera(dt,false)                    // 963-965
  karts = demo | race.state.karts                           // 966
  visibleGates = gates.filter(g => g.lap === lapNow)         // 967-971
  const matrix = render(ctx, {...view, time: simTime, minimap: mode!=="title" ...})  // 972-989
  syncSigns(matrix); syncTags(matrix); syncFork(); syncQuizTilt(matrix)  // 990（quiz 态也执行！）
  syncCheer(dt); syncHud()                                  // 992-993
  if(!window.__rally._stepping) requestAnimationFrame(frame) // 994
```

- **两个累加器**：`simTime`（main.js:932，渲染时钟，frozen 时停）与 `race.state.time`（race.js:605，仿真时钟，仅 `race.update()` 内递增）。quiz / paused / results / 开榜 / 开店时两者都停；`countdown` 时 `simTime` 走而 `state.time` 不走。
- **`render()` 每帧都调用，即使 frozen**（972）→ 小地图/路牌在 quiz 期间仍会被重绘，但 `player.odo`、`g.line`、`eta` 不变 → 内容自然静止。`syncSigns()` 内部 `main.js:459` 显式包含 `"quiz"`，故**现状**路牌 DOM 在答题期间保持显示但不移动。⚠️ **Q2 已裁决改为隐藏**（`#signs.hidden = true`），且显隐必须由 §0.0.3-1 的 `visible` 显式控制、**不能**依赖「画面冻结了就不会变」；`boardOpen/shopOpen` 时 `mode` 仍是 `racing`（F5）。详见 §C.4 / §G4 / §G13。
- **禁止墙钟**：任何倒计时/淡出/节流若用 `performance.now()` / `Date.now()` / `setTimeout`，会穿过冻结窗口，恢复后跳变，且 headless 无法复现。一律用 `simTime` 或直接由 `odo/Δ` 派生（§C）。
- `render.js:220` 的 `setTransform(dpr,…)` 与 `drawMinimap`（416）在 `ctx.restore()`（408）之后执行 → **小地图用 CSS 像素 `w/h`，不受相机矩阵影响**，但它仍在 canvas 位图内、受 dpr 缩放与 z-index 遮挡影响。
- `window.__rally`（996-1013）暴露 `mode/race/camera/boardOpen/shopOpen/simTime/frame/step(n)/vowels`，是 `verify_cseg_ui.py` 与 #5 补断言的钩子；新增 HUD 状态建议同样挂只读 getter，不新增写接口。

### A.6 两圈 gate 过滤逻辑（同 commitT 不重绘）

- `buildGates()`（`config.js:264-299`）：`need = laps*commits.length = 4`，每圈每 commit 生成**独立 gate 对象**，`id=lap*2+ci ∈ 0..3`、`commitT ∈ {0.24, 0.68}`（两圈相同）、`lineT = lap + commitT ∈ {0.24,0.68,1.24,1.68}`、`lap ∈{0,1}`；`played/replayed/judged/hit` 逐门独立（不再跨圈重置）。
- `race.js:83`：`g.line = player.startOdo + g.lineT*L`，`startOdo=0.02*L=385.09`。**绝对门线里程**（L=19254.50）：
  - lap0@0.24 → **5006.17**；lap0@0.68 → **13478.15**；lap1@0.24 → **24260.67**；lap1@0.68 → **32732.66**。
- `flareAt(t, gates, span, merge)`（`render.js:43-57`）与门线画法（309-325）都用 **`g.commitT`（相对）**。若把 4 个门全量交给 `render()`，lap0/lap1 的相同 `commitT` 会在**同一屏幕位置画两遍** flare 与车道色。
- `main.js:967-971`：`lapNow = race.state.lap`；`visibleGates = (mode∉{title,teach}) ? gates.filter(g=>g.lap===lapNow) : []`，在 974 作为 `gates` 传入 `render()`。判定与路牌仍用 `race.state.gates` 全量（`syncSigns → race.activeGate()`）。
- `race.state.lap` 由 `race.js:611-617` 按 `floor((player.odo-player.startOdo)/L)` 更新，跨圈时复位 `pickups[].taken`。
- 断言锁：`verify_cseg_gate.py:89`（S13）以字面量 `"g.lap === lapNow"` 锁死该过滤；`verify_cseg_gate.py:66-69`（S4/S5）锁 `player.odo >= g.line` / `before < upcoming.line`；`race.js:152-156 / 441-468` 的 `wrapDelta/hasPassed/crossed/nextLine/commitMark` 是 **C 段已弃用的相对圈坐标逻辑**（注释 689-691 明说改用 `g.line`），新 HUD 不得复活它们。

---

## B. 小地图实现方案（不落地）

### B.1 数据来源（全部只读、已存在，无需新 state 字段）

| 数据 | 来源 | 用途 |
|---|---|---|
| 赛道几何 `track.samples[520]`、`track.length`、`track.roadHalf` | `createTrack(TUNING)`（`main.js:15`）→ `render()` 的 `view.track`（`main.js:973`） | 底图 path；线性变换 min/max→`sc/ox/oy` |
| 车点 `karts[]`（player + 2 rivals），`kart.t` 已是 `(odo/L)%1` | `race.state.karts`（`race.js:298`，**天然取模**）/ demo | 3 个圆点；player 用蓝 `#2f6f8f`、a 红、b 绿（既有 `render.js:453`） |
| 闸门 `gates[]`（`g.line` / `g.lineT` / `g.commitT` / `g.lap` / `g.judged` / `g.hit` / `g.left` / `g.right`） | `race.state.gates` + `visibleGates`（`main.js:970`） | 分叉点标记；按 `g.lap===lapNow` 过滤 |
| 圈数 `state.lap` / `state.laps` | `race.js:74-75` | 「第 n/2 圈」文本、圈点 |
| 地图 `state.mapId` + `RACE_MAPS` + `PHONEMES[unit].color` | `race.js:73`；`config.js:179-204` / 88-93 | 四区差异化：区名/主题色/音素色 |
| 绝对里程 `player.odo` / `startOdo` | `race.state.player` | `Δ=g.line-player.odo`（§C 共用） |
| `state.span`、`reduced` | `race.state.span` / `main.js:16` | 分叉张开范围、减动效降级 |

**无需新增 `race.state` 字段、无需改 `createRace()` 入参、无需读 localStorage。**

### B.2 绘制载体：推荐 + 2 个备选（含取舍）

> **决策记录 AD-1（上下文/备选/决定/后果）** — ⚠️ **本节「决定」已被 §0.0 收尾基线 / Q1 覆盖：最终采用「DOM 化 + 内嵌 canvas」（#1 方案 A，`z-index:5`，DOM 顺序在 `#hud` 之后），不再是内联 SVG / `z-index:6`；下表三种备选作为评估记录保留。以 §0.0.2 Q1 为准。**
> 上下文：用户要「进入比赛页右上角出现该轮比赛小地图」；既有 `drawMinimap()` 画在主 canvas 且被 `#hud`(z5)/`#banner`(z6) 遮挡；#5 需能对小地图写 DOM 冒烟断言；tag 字面量锁 46；3D 轮 HUD 需复用同一 DOM 契约。
>
> ⚠️ **表格阅读提示**：下表中的「① 推荐 / 内联 SVG / `z-index:6`」「②/③ 回退」均为**盘查阶段评估，已作废**。**收尾采用方案见表格下方「✅ 收尾决定」**：`div#minimap` + 内嵌 `canvas#minimap-c` + `span#minimap-lap`、`z-index:5`、`#hud` gutter 避让、`dpr=min(2,·)`；QA H1 直接断言 DOM 存在性。

| 方案 | 做法 | 新增 `?v=` | 优点 | 缺点 / 风险 |
|---|---|---|---|---|
| **①（SVG 载体已作废，仅作评估）：独立 DOM 层 + 内联 SVG**（几何/坐标逻辑抽成 `render.js` 的纯函数 `minimapModel(view)`，main.js 每帧把结果写进 SVG） | `index.html` 增 `<div id="minimap">` 内含 `<svg viewBox>`：静态 `<path d>`（启动时由 `track.samples` 生成一次）、3 个 `<circle>` 车点、≤2 个闸门点、`<text>` 圈数/区名；CSS 给 `z-index`（建议 6，与 `#hud` 同层但右侧独立定位）与 `pointer-events:none`；`setMode()` 控制显隐 | **0** | z-index / 375px 布局可显式控制；与相机、dpr、canvas 尺寸完全解耦；无 canvas 缩放模糊；DOM 可被 Playwright 直接断言（#5 友好）；path 只算一次，每帧仅更新 5 个圆点坐标 → 最省 | 每帧 ~5 次 DOM 属性写（60fps 下极轻）；需维护 viewBox 与世界坐标的线性变换（可复用 `drawMinimap` 的 min/max→ox/oy/sc 公式 431-440）；新增 DOM 元素（无 src，不产生请求，U1/U12 无影响） |
| ② 增强既有 `render.js:drawMinimap()`（继续画在主 canvas） | 给 `view` 增 `mapId/lap/laps/gates`，在 420-458 内补闸门点、圈数、区名、四区配色 | **0** | 改动最小、零新增 DOM、一次 `render()` 顺带画完、无额外刷新循环 | **遮挡问题无解**：canvas 无 z-index，HUD(5)/banner(6) 必盖其上；要么给 `#c` 加 `position:fixed;inset:0;z-index`（改变既有布局模型、风险中等），要么给 `.hud-row` 右侧让位且把小地图下移（与「右上角」诉求冲突）；dpr>1 时位图尺寸与 CSS 显示尺寸一致性需复核（该缺口已由 Q1 方案 A 的 `dpr=min(2,·)` + `setTransform` 契约收敛，见 §G9） |
| ③ 独立 `<canvas id="minimap">` 小画布 | 新增 canvas + 第 4 个 2d ctx，main.js 内单独绘制，可独立节流 | **0**（canvas 无 src） | 绘制性能最好（纯位图）、可独立降频到 20–30fps、可用 `devicePixelRatio` 精确控制清晰度 | 多一个 context 与 resize/dpr 管理；仍需 CSS z-index 处理遮挡；#5 无法直接断言画布内容（需 `toDataURL`/像素比对，脆弱）；与 ② 同样受 HUD 遮挡 |

**~~决定（原始盘查结论，已作废）~~**：原推荐 ①（独立 DOM/SVG 层，`z-index:6`）。

> ✅ **收尾决定（Q1 已裁决，见 §0.0.2）**：采用 **#1 §2.1.1 方案 A「DOM 化」** —— `<div id="minimap" aria-hidden="true">` + **内嵌 `<canvas id="minimap-c">`** + `<span id="minimap-lap">`，`position:fixed; z-index:5`，**DOM 顺序置于 `#hud` 之后**，`pointer-events:none`，半透明底板；把既有 `drawMinimap()` 的绘制**迁入**内嵌 canvas（不是另起一套），并把「几何→小地图坐标」的纯计算抽到 `minimapModel(view)`（Node 可单测、验证驱动，QA H1/H10 也读它）。`main.js:987` 的 `minimap: mode !== "title"` 改为 §0.0.3-1 的显式 `visible` 表达式。**后果**：`render.js` 改动仅限迁绘制 + 加纯函数（不动 `flareAt`/`project`/`render` 既有绘制语义）；`index.html`/`css/game.css`/`main.js` 各改一处；**不新建模块** → tag 计数保持 46。**SVG 方案与「`z-index:6`」作废；方案 ②/③ 仅作评估记录，不再作为回退项。**

### B.3 刷新频率与性能开销

- **不新增 rAF 循环、不新增定时器**：挂在既有 `frame()`（994 的 rAF / `__rally.step()` 手动步进）内，与 `syncSigns` 同批在 990 附近调用。
- 位置类更新跟 `simTime` 节奏即可；frozen 态 `odo` 不变 → 无需特殊分支，天然静止。**禁止用 `performance.now()` 做节流**（§A.5）。
- 建议节流到 **20–30fps**（每 2–3 帧更新一次圆点），或按 `Δodo > 8` 世界单位才写 DOM；赛车 260–300 单位/s，8 单位 ≈ 27ms，视觉足够平滑。
- **预算**：既有 `drawMinimap` 每帧遍历 520 samples 求 min/max（431-435）+ 画环线 path（442-446）+ 3 车点，O(520)/帧。**Q1 收尾方案（内嵌 canvas）**同样把 min/max 与环线 path 的 `samples` 投影**启动时算一次并缓存**（几何固定，`track.js` 只吃 TUNING），每帧只重绘环线 + 更新 3 车点 / 进度弧 / `nextGate` 菱形 → 主计算从 O(520) 降到 O(1)，实为性能改善（不是 SVG 属性写，而是内嵌 canvas 每帧一次轻量绘制）。
- 编码标准：`core` 热路径零分配 —— `minimapModel(view)` 复用预分配对象/数组，不在 `frame()` 内 `map`/`filter` 生成大数组；UI 层不持有游戏状态，只读 `race.state`。
- 建议给 `minimapModel(view)` 写 Node 单测（不依赖 DOM）：喂固定的 `samples`/`karts`/`gates`，断言输出坐标范围、lap 过滤、四区 zone 映射。

### B.4 两圈制下 `odo` 取模映射

> ⚠️ **收尾修订（§0.0.3-4 / #1 §1.3）**：#1 规定「小地图环线点位、进度弧、圈数**一律用 `odo / (laps·L)`，不用 `t`**（`t` 在两圈会重复）」；**Q4** 又规定新增逻辑一律 `t_i = (odo_i/L) % 1` 从绝对 `odo` 派生。二者统一口径为：**绝对 `odo` 是唯一跨轮坐标**，`t` 只允许由 `odo` 派生、不得反向用 `commitT` 推绝对位置。下方「车点直接用 `kart.t`」是既有 `drawMinimap` 的**现状描述**，#4 落地时应改为在 `minimapModel(view)` 内统一由 `odo` 派生（保持单一数据源），但**不得改动 `race.js:298` 的 `kart.t`**（headless 零影响）。

- **不要自己取模**：`race.js:298` 已维护 `kart.t = (kart.odo / L) % 1`，既有 `drawMinimap`（451-457）就是 `track.sample(kart.t)`。车点直接用 `kart.t` → `sample(t).x/y` → 小地图线性变换；`kart.t` 本身就是 `odo` 的派生值，符合 Q4「`t` 由 `odo` 派生」。
- 若必须从绝对 `odo` 出发（例如 #5 直接读 `race.state.player.odo` 断言）：`t = (((odo % L) + L) % L) / L`，等价于 `kart.t`。
- **进度/圈数分离**：`lap = floor((odo - startOdo)/L)`（与 `race.js:611` 同源，或直接用 `state.lap`），全赛进度 `frac = (odo-startOdo)/(laps*L)`（`syncHud` 进度条口径，`main.js:635-636`）。小地图车点只表示**圈内位置**，不编码第几圈；圈数用独立 `#minimap-lap` 文本 `1/2`、`2/2` 表达（#1 §2.1.2，字号 11px、不重复「听对 N」），否则两圈视觉完全重叠、无法区分「该轮」。

### B.5 `g.line` 绝对里程转圈内位置

- `t_in_lap = (g.line / L) % 1`，等价于 `g.lineT % 1` = **`g.commitT`**（实证：lap0@0.24→0.24，lap1@0.24→0.24；lap0@0.68→0.68，lap1@0.68→0.68）。#1 §2.1.2 的 `nextGate` 菱形位置写作 `track.sample((nextGate.line / L) % 1)`（同源）。
- 小地图闸门标记用 `g.commitT` 定位即可（与 `flareAt`/门线画法同源），但**必须按 `g.lap === lapNow` 过滤**（沿用 `main.js:970`），否则两圈 4 个门塌成 2 个重叠点 —— 与 §A.6 同一陷阱。
- ⚠️ **收尾修订（#1 §2.1.2 / Q3）**：`nextGate` 一律为**中性单色菱形**（`--gold-deep`，无箭头/无左右指向/无高亮侧），S1 点亮、S2 保持、S3/无门熄灭；**不用** `judged&&hit` 绿 / `judged&&!hit` 灰的状态色（会重复 HUD 信息、且 `hit` 属判定后信息）；**不得**用 `gate.left.color`/`gate.right.color` 作左右分叉着色（#1 明令禁止，易被误读为指向）；**颜色不可绑定 `correctLateral`/`onRight`**（泄答案，§C.4）。~~原「状态色 / 左右两半着色」建议作废~~。
- 起终点线：`render.js:327` 用 `track.sample(0.012)` 画 finish；小地图复用同一 `t` 画单个中性旗形/菱形标记（单色 `--gold-deep`，#1 §2.1.2）。

### B.6 四区地图差异化（含硬约束）

- `track.js` **只吃 `TUNING`**，四区共用同一椭圆几何 → **本轮不能靠赛道形状做差异化**（真 3D 化下一轮才改视角/几何，用户已拍板本轮不改渲染层视角）。
- 可用差异化维度（全部来自既有静态数据，**且须符合 #1 §2.1.2 的「不显示」硬清单**）：
  - 区名/主题：`RACE_MAPS[mapId].zone` / `.name` / `.short`（`config.js:179-204`）→ 小地图 zone 标签与边框色（#5 H10 断言四区随 `mapId` 变化）；
  - ⚠️ **收尾修订**：音素色 `PHONEMES[unit].color` → **仅可作底板/边框/图例的主题色**，**不得**作 `gate.left/right.color` 的左右分叉着色或 `nextGate` 菱形着色（#1 §2.1.2 明令统一中性单色 `--gold-deep`，§B.5 / §C.4）；
  - 圈数：`state.lap/laps` → `#minimap-lap` 的 `1/2`、`2/2`（**不重复**「听对 N」「宝石/护身/combo/名次」等 `#hud` 已有信息，防认知过载）；
  - 车手/车色：`playerLook()`（`main.js:183-193`）已返回 `body/trim`，可给 **player 点**上色（存档字段已存在）；对手点沿用既有红/绿，`g.judged/g.hit` **不作状态色**（§B.5）。
- **不新增 localStorage 字段**（§E / §H.1 已裁决），不改 `buildGates()` / `poolOf()`，不动 `data.js` / `ipa-display.js`。

---

## C. 路牌预告实现方案（不落地）

### C.1 与 `placeLaneSign()` / `preview` 的关系

| 概念 | 现状 | 与预告的关系 |
|---|---|---|
| `DIFFICULTY.preview` = **4.2 / 4.0** | `config.js:38 / 48` 定义，**F3 已核实运行时从未读取**（死字段；`race.previewSteer()` 是同名不同物） | ✅ **单位已定 = 秒数基准**（#1 §2.2.2）：`D_preview = span·L + 0.5·preview·speed` → follow 1482 / listen 1620 里程。激活读取、**不改数值**、不新造参数（§0.0.3-2 / §C.2） |
| `DIFFICULTY.fork` = 3.6 / 3.4 | 已被 `forkSpan(diff,L)=fork*speed/L`（`config.js:301-303`）使用 → `span`（`race.js:8`） | 决定分叉几何张开长度 `spanLen = span*L = fork*speed` = **936 / 1020** 世界单位，也是 `D_preview` 的第一项 |
| `beginDecide()` 音频开播 | `race.js:421-439`：`mouth=span*L*0.55`（515 / 561）、`lead=mouth+360+speedNow*0.62`（**1036 / 1107**）→ 满足 `dist<=lead` 时 `gate.played=true; audio.playWord(spoken.word)`（434-437） | S1 预告须在**音频开播之前**出现（`D_preview > lead`），此前不得暴露词面、不得提前播放音频；`played` 边沿触发 S1→S2 |
| `placeLaneSign()` | `main.js:498-521`，用 `span*{0.66,0.34,0.36}` 定位闸门车道标签 | ⚠️ **Q3**：整条投影管线复用（相对 `t` + 绝对 `odo` → `pointAt` → `project` → DOM style）；**仅**把 `const span = race.state.span` 参数化为 `spanEff`（S1 传 `D_preview/L`，S2 传 `race.state.span`），`0.66/0.34/0.36` 系数、`project()`、`--lane`、屏幕裁剪、S12 字面量全部保留；**零新增路牌 DOM**，复用 `#sign-l/#sign-r`；**Q4 不修 `0.02·L` 偏差** |
| `syncSigns()` 显示条件 | `main.js:461`：`deciding \|\| (act.gate.played && !act.gate.judged)`，即**音频播放后**才出现 | ⚠️ **Q3 已裁决**：不新增 `syncForkHint()`；改为把 `syncSigns()` **改造成 #1 §2.2.1 完整 S0–S3 状态机**（S0 隐藏 / S1 中性预告 / S2 对称选项 / S3 判后隐藏），S1 调 `paintForecast()`、S2 调现 `paintLane()`；`signKey` 纳入 `phase`；Q2 增 quiz 隐藏分支 |
| `flareAt()` | `render.js:43-57`，按 `commitT` 画闸门光晕 | 预告「分叉将至」视觉用同一 `span/merge` 口径，但不得读取 `spoken/correctLateral`；小地图侧用中性菱形 `nextGate`（#1 §2.1.2） |
| 遗留钩子 | `.fork-card` CSS（93-105）、`#fork-count`（41）、`placeSign()`（537，死）、`ui.fork/forkLeft/forkRight`（28-30，指向不存在 DOM） | ⚠️ **Q3 已裁决「零新增路牌 DOM」**：这些遗留钩子**本轮不启用**（复用 `#signs`）；仅登记为可清理的死代码 |

> **决策记录 AD-2（收尾修订）**：⚠️ 原结论「新增 `syncForkHint()` + `#fork-hint` DOM」**作废**（被 Q3 覆盖）。**收尾决定**：预告牌采用「**S0–S3 状态机改造 `syncSigns()` + 中性内容 + 复用并参数化 `placeLaneSign()` 投影 + 小地图中性菱形**」，**零新增路牌 DOM**、不新增题型/音频/state 持久字段；触发态由 `race.activeGate()` 派生（纯读），不写 `gate.*` 标志位。`signKey` 纳入 `phase` 以触发 S1→S2 重绘（#1 §2.2.5）。后果：无需改 `race.js`，headless 零影响；冻结口径改为 **Q2「quiz 时 `#signs.hidden = true`」**（见 §C.4 收尾修订）。

### C.2 按绝对里程 `g.line - player.odo` 触发阈值（follow 260 / listen 300 的秒数）

> ⚠️ **收尾修订（§0.0.3-2）**：下表「预告牌出现 = `preview*v`（1092/1200）」是**盘查阶段的朴素估算，已被 #1 §2.2.2 的 `D_preview` 覆盖**。`preview*v` 仅比 `lead`(1036/1107) 早 56/93 里程（0.22/0.31 s），玩家几乎无感知；#1 取「分叉展开起点再往前半个 preview 秒」，得约 1.7 s 有效预警窗口，且**复用 `preview` 与 `span` 两个既有常量、不新增参数**。最终口径：
>
> | 量 | 公式 | follow（v=260, fork=3.6, p=4.2） | listen（v=300, fork=3.4, p=4.0） |
> |---|---|---|---|
> | `spanLen = span*L = fork*v` | `3.6*260` / `3.4*300` | 936 → 3.60 s | 1020 → 3.40 s |
> | `0.5·p·v` | `0.5*4.2*260` / `0.5*4.0*300` | 546 → 2.10 s | 600 → 2.00 s |
> | **`D_preview`（T0 / S1 上限，预告牌出现）** | **`span·L + 0.5·p·v`** | **1482 里程 → 5.70 s** | **1620 里程 → 5.40 s** |
> | S1 牌世界定位 | `gate.line − 0.36·D_preview` | 534 → 2.05 s | 583 → 1.94 s |
> | S2 牌世界定位 | `gate.line − 0.36·span·L` | 337 → 1.30 s | 367 → 1.22 s |
>
> **时间轴（从远到近）**：`Δ=1482/1620`（S1 预告牌 + 小地图菱形点亮）→ `Δ=1036/1107`（`beginDecide` 音频播放，S1→S2）→ `Δ=936/1020`（分叉几何张开）→ `Δ=618/673` → `Δ=337/367`（S2 牌中心）→ `Δ=0`（`judge()`）。恒有 `D_preview > lead > S1定位 > S2定位 > 0`。

设 `Δ = g.line - player.odo`（世界单位，绝对里程差），标称速度 `v = diff.speed`。所有秒数按 `Δ/v` 换算。**下表保留作为盘查阶段的计算底稿（含各既有事件里程），预告阈值行以 §0.0.3-2 / 上表为准**：

| 事件 | 公式 | follow（v=260） | listen（v=300） |
|---|---|---|---|
| ~~预告牌出现~~（原估算，已作废） | ~~`Δ ≤ preview * v`~~ | ~~1092 / 4.20 s~~ | ~~1200 / 4.00 s~~ |
| 音频开播 `lead`（`beginDecide`） | `0.55*spanLen + 360 + 0.62*v` | `515+360+161.2=1036` → **3.98 s** | `561+360+186=1107` → **3.69 s** |
| 分叉几何张开起点 | `Δ = spanLen = fork*v` | `3.6*260 = 936` → **3.60 s** | `3.4*300 = 1020` → **3.40 s** |
| `placeLaneSign` 的 `t0` 带（0.66·spanLen） | `0.66*spanLen` | `618` → **2.38 s** | `673` → **2.24 s** |
| `placeLaneSign` 的中心 `t`（0.36·spanLen） | `0.36*spanLen` | `337` → **1.30 s** | `367` → **1.22 s** |
| 门线判定 | `Δ = 0` | 0 s | 0 s |

**口径统一（重要）**：`speedNow()`（`race.js:182-188`）会因 `BOOST/1.48`、`TURBO/1.92`、`SLOW/0.54` 波动，因此「秒数」是**标称值**。建议：
- **触发用里程常量 `Δ ≤ D_preview`（= `spanLen + 0.5·preview·diff.speed`）**，用**名义 `diff.speed`**，不读 `speedNow()`（不受加速/减速影响，可复现；#1 §2.2.2 / R6）；
- 若 UI 要显示「还有几秒」，用 `Δ / speedNow(player)`（与 `activeGate().eta`，`race.js:171` 同源）实时算，不要用墙钟倒计时；
- 不要用 `wrapDelta/hasPassed/commitT` 做筛选（§A.6）。

### C.3 两圈同 `commitT` 下路牌复用 / 复位

> ⚠️ **收尾修订（Q3 / Q4，见 §0.0）**：本节下方正文里「预告牌用 `hint:${gate.id}` 新键」「建议在 `syncForkHint()` 里 lap 变化清空 DOM」属**已作废的盘查底稿**。最终口径：
> - **状态 key 唯一用 `gate.id`（0..3，含 lap）**：不新增 `hint:` 前缀键，直接把 `syncSigns()` 的 `signKey`（`main.js:475`）改为 `` `${gate.id}:${phase}:${gate.left.word}:${gate.right.word}` ``，**纳入 `phase`**（#1 §2.2.5），使 S1→S2 切换触发 `paintLane()` 重绘与 `open` 动画重置。**禁止** `commitT` / `lineT % 1` / `pairKey` 作 key。
> - **圈切换**：`signKey` 含 `gate.id` + `phase`，跨圈必变化，自然重算、无残留；不靠额外清空函数。
> - **Q4**：新增逻辑一律 `t_i = (odo_i / L) % 1` 从绝对 `odo` 派生；既有 `0.02·L` 偏差本轮不修（§G12 遗留项）。
> - 其余（`activeGate()` 筛选、`g.lap===lapNow`、`visibleGates` 保持 S13 字面量、不改 `buildGates()`）**继续有效**。

- **筛选复用 `race.activeGate()`**（`race.js:164-175`）：它遍历全量 `gates`，跳过 `judged/unheard`，按 `g.line - player.odo ≥ 0` 找 `eta` 最小者 → **天然跨圈正确**（lap1 门 `g.line` 更大，不会在 lap0 被误选）。预告牌直接消费 `act.gate` 与 `act.eta`，不自己扫门。
- **状态 key 用 `gate.id`（收尾口径）**：~~原「预告牌用独立 hint 键」作废~~ → 直接改造 `syncSigns()` 的 `signKey`（`main.js:475`）为 `` `${gate.id}:${phase}:${gate.left.word}:${gate.right.word}` ``；`gate.id` 两圈 0..3 唯一且含 lap，`phase` 使 S1→S2 触发重绘 → 每圈自动重绘、无残留；`beginCountdown()` 的 `signKey=""`（387）复用为开局复位。
- **圈切换（收尾口径）**：~~原「在 `syncForkHint()` 里清空 DOM」作废~~ → `state.lap` 变化（`race.js:611`）时 `activeGate()` 结果随之改变，`signKey` 含 `gate.id`+`phase` 必变化 → 状态机自然重算、无冻结帧残留，无需额外清空函数。
- **小地图 `nextGate` 菱形同样按 `g.lap===lapNow` 过滤**（§B.5）；**渲染层 `visibleGates` 过滤（main.js:970）保持不变**（S13 锁字面量）。
- 不改 `buildGates()`（逐门独立对象，`config.js:262-263` 注释已说明「不用跨圈重置 judged/played」）。

### C.4 quiz 冻结时的状态 / 不泄露听音题答案

**冻结行为（⚠️ Q2 已裁决：quiz 时路牌隐藏，本节原「保持显示但静止」结论作废）**：
- `frozen` 集合（`main.js:938`）含 `quiz`（也含 `paused/results/boardOpen/shopOpen`）：`simTime` 不累加（939）、`race.update()` 不调用 → `race.state.time` / `player.odo` / `Δ` / `eta` **全部冻结**。
- `render()` 每帧仍调用（972）、`syncSigns()` 在 990 仍执行，且 `syncSigns` 内部 `main.js:459` 显式把 `mode === "quiz"` 列入 `activeGate()` 条件 → **现状是 quiz 期间路牌保持显示且静止**。这正是 Q2 要修的冲突点（#1 §2.2.6 / R4）。
- ✅ **收尾决定（Q2）**：`syncSigns()` 状态机增隐藏分支 → **`#signs.hidden = true`（quiz 冻结时路牌隐藏）**；小地图在 quiz 下**显示但冻结**（`karts[].odo` 不推进、`simTime` 不增，§0.0.3-1）。回 `racing` 后按 `played` 无缝重现 S2，**不重新 `audio.playWord`、不重播 `open` 动画**。
  - **理由**（主理人 + #1 §2.2.6）：`#quiz` 是 z=8 `.panel`，375px 下几乎全宽；`ipa` / `type` 题会在 `#quiz-prompt` 写出 `词：<b>${q.spoken.word}</b>`（`main.js:774`），若 `#signs` 仍显示分叉门两侧词 → **两套题目同屏**，可能构成意外提示、加重认知负荷。
- 预告牌**不得**用 `performance.now()` / `Date.now()` / `setTimeout` / CSS animation 驱动倒计时或淡出（会穿过冻结窗口，恢复后跳变，且 headless 无法复现）；若需动画用 `simTime`（frozen 时停）。**S1 中性牌与 S2 选项牌本身都是静态的**（无计时动画）。
- quiz 是撞墙/石头/车的**惩罚题**，与分叉门无关。`headless_laps.mjs:75-83` 注释确认「浏览器里 mode==='quiz' 会冻结仿真，答题不占 state.time」。

**不泄答案（硬约束）**：
- 既有口径 `openQuizCard()`（`main.js:769-775`）：**word 题型题干只提示重听、不写词面**；ipa/type 题才写 `q.spoken.word`。`verify_cseg_ui.py:176`（U8）断言 `q["word"] not in q["prompt"]`。
- 分叉门的答案 = `gate.spoken`（音频播放的词）＋ `gate.correctLateral` / `onRight`（哪条车道对）。**预告牌绝不能包含**：`spoken.word`、`spoken.ipa`、`spoken.label`、`correctLateral` 的单侧箭头/高亮、`onRight`、以及任何单侧突出；也**不得提前调用** `audio.playWord()`（那属于 `beginDecide`，`race.js:434-437`）。
- 安全内容：分叉图标 / 几何符号 `◇`、`↖ ↗` / 距离或圈数 / 四区区名。⚠️ **Q3 已裁决「S1 零文本」**：S1 中性预告牌**完全不显示候选词**（无 word / IPA / label / sprite / 左右色差 / 先后出现差异，去掉 `.is-long/.is-short`），两侧统一 `var(--card)` + `var(--line)`；词面等 `beginDecide()` 播音后由 **S2** `paintLane()` 成对同时给出、不标注哪个正确、不因 `onRight` 交换而单侧强调（#1 §2.2.1 / §2.2.3）。
- ⚠️ **小地图侧**：`nextGate` 用**中性单色菱形**（`--gold-deep`，无箭头/无左右指向/无高亮侧）；不显示 `gate.left.color`/`gate.right.color` 作为左右分叉着色（#1 §2.1.2 明令禁止，易被误读为指向）。**单向铁律**：`correctLateral` / `spoken` 只允许出现在 `audio.playWord()`（`race.js:436`）与 `judge()`（`race.js:213-262`），任何 HUD 生成路径（DOM `innerHTML`、canvas `fillText`、CSS `data-*`、alt、aria-label）不得接触。
- 建议 #5 补断言（对齐 #1 H5/H6/H8/H9）：S1 两牌 `textContent` 无任何字母与 `/`、无 `spoken.word`、无 `correctLateral` 单侧标记、`className` 不含 `is-long/is-short`；S2 两牌 `rect.width` ±1px 相等、`opacity` 相等、`className` 不含 `ok/bad/correct/answer`；**`mode==='quiz'` 时 `#signs.hidden===true`**（Q2）、`simTime` 与 `karts[0].odo` 在 `__rally.step(60)` 后不变、quiz 期间 `localStorage.setItem` 未被调用。

---

## D. 影响面与回归清单

### D.1 本轮预计改动的文件（#4 实施范围建议）

> ⚠️ **收尾修订（§0.0）**：下表左列原含「新增 `syncForkHint()`」「`#fork-hint` DOM」「SVG 容器」「`.hud-row` 让位」等，已被 **Q1（DOM 化 + 内嵌 canvas）、Q3（零新增路牌 DOM、复用 `#signs`）、#1 §2.1.3/2.1.4（`#hud` gutter）** 覆盖。以下为**收尾后**的 #4 实施范围建议（#4 以主理人下发规格为最终准）：

| 文件 | 改动性质（收尾后） | 是否新增 `?v=` |
|---|---|---|
| `音标拉力赛/js/main.js` | `syncSigns()` 改 S0–S3 状态机（增 `paintForecast()`；Q2 quiz 隐藏分支）；`placeLaneSign()` 参数化 `spanEff` + 增小地图矩形避让裁剪；`frame()` 的 `minimap:` 改 §0.0.3-1 显式 `visible`；`signKey` 纳入 `phase`；`window.__rally` 增只读 getter；启用 `diff.preview` 为 `D_preview` 秒数基准 | 否（既有 7 处字面量随 bump 替换） |
| `音标拉力赛/js/render.js` | 把 `drawMinimap()` 迁到内嵌 canvas、补圈数/进度弧/起终点/中性 `nextGate` 菱形；抽 `minimapModel(view)` 纯函数（Node 可单测）；保留既有 `flareAt`/`project`/`render` 语义 | 否（既有 1 处替换） |
| `音标拉力赛/index.html` | **仅新增 `#minimap`（DOM 容器 + 内嵌 `<canvas id="minimap-c">` + `<span id="minimap-lap">`）**，DOM 顺序置于 `#hud` 之后；**`#route-map` 不动不删**；**不新增路牌 DOM**（Q3 复用 `#signs`）；**不新增 `<script src>` / `<link>` / `<img src>` / 新模块** | 否 |
| `音标拉力赛/css/game.css` | `#minimap` / `#minimap-c` / `#minimap-lap` 样式、`z-index:5`、`pointer-events:none`、半透明底板、CSS 变量 `--mm-*`；**`#hud { padding-right: var(--mm-right-gutter) }`（375px 避让核心）**；`#banner` 窄屏下移；复用既有 `@media (max-width:640px)` 断点，不新增断点 | 否（本文件 0 处 `?v=`；`index.html:12` 的引用已计入 46） |
| `音标拉力赛/js/config.js` | **仅** `CACHE_TAG`（:7）换 `hud-20261108`；`TUNING` / `DIFFICULTY` 数值**一律不动**（`preview` 4.2/4.0 只被读取、不赋值修改）；**Q4：不改 `placeLaneSign` 的 `t/odo` 偏差**（该项在 main.js，此处仅提示不改 `race.js:83` 的 `startOdo`） | 否（`CACHE_TAG` 不是 `?v=` 字面量，见 D.3） |
| 两站 `index.html` + `音标大闯关/js/{atlas,level,map,story}.js` + 拉力赛 `js/{main,race,render}.js` | 46 处 `?v=cseg-20261107` → `?v=hud-20261108` 整体替换 | 否（净 0） |
| 4 套验收脚本 `TAG` 常量 + `headless_laps.mjs:19` | 同步替换为 `hud-20261108`（**`verify_cseg_gate.py:24` 的 S18 判据必改**） | 否（不计入 46） |
| **不改动**：`race.js` 仿真逻辑与 `startOdo`、`track.js` 几何、`cards.js`、`audio.js`、`data.js`、`ipa-display.js`、`story.js`、`store.js`、`#route-map` 的 title 页显隐、48 张立绘/卡面、`content_raw.json` / `build_data.py` / `augment_data.py` | — | — |

### D.2 四套门控 110 项断言冲击（38 + 14 + 21 + 37，采用主理人实测口径）

> 说明：静态 `chk()` 调用点计数为 41 / 13 / 23 / 38（含互斥条件分支，如 B0、F6 三分支、F9c note、D9 条件执行），与运行时 PASS 数 38/14/21/37 略有出入；以下按运行时 110 项分析，结论不受影响。

**（1）tag 类断言 —— 最高风险，三处同时联动**

| 断言 | 位置 | 判据 | 冲击 |
|---|---|---|---|
| S17 | `verify_cseg_gate.py:100-113` | `set(tag_counts)=={TAG} and count(TAG)==46` | 见下 |
| F8a | `verify_fresh_gate.py:162-174` | `set(tags)=={TAG} and tags.get(TAG,0)==46` | 同 S17 |
| S1.7 | `verify_c08_gate.py:80-92` | `set(tags)=={TAG} and tags.get(TAG,0)==46` | 同 S17 |

- 三处都扫两站 `.html/.js/.css`（排除 `assets/ docs/ sprite_gen/`），正则 `\?v=([A-Za-z0-9\-]+)`。**`.mjs` / `.py` 不扫描**。
- **绿的条件**：46 处字面量全部换成新 tag + 三个脚本 `TAG` 同步 → 计数仍 46、集合仍单值 → 全绿，`==46` 断言**无需改**。
- **FAIL 情形 A**：漏改任一处字面量（残留旧 tag）→ `set` 含 2 值 → 三处同时 FAIL。
- **FAIL 情形 B**：新增任何 `?v=` 字面量（新模块 import / 新 `<img>` / 新 `<link>`）→ count 47+ → 三处同时 FAIL，需同步把三处 `== 46` 与断言描述里的「46 处」改成新值。
- 实证分布（本阶段扫描）：`音标大闯关/index.html` 17、`js/atlas.js` 6、`js/level.js` 1、`js/map.js` 3、`js/story.js` 2、`音标拉力赛/index.html` 7、`js/main.js` 7、`js/race.js` 2、`js/render.js` 1 = **46**；直方图 `{'cseg-20261107': 46}`（唯一值）。

**（2）S18 零裸图片 URL（`verify_cseg_gate.py:115-140`）**

- 判据靠 `:24` 的 `TAG`：字面量分支 `:134` 要求 URL 含 `?v=TAG` 或 `${CACHE_TAG}`（白名单）；`concat` 分支 `:136-139` 要求 `"assets/img/" + 变量` 段内 `:138` 含 `?v=TAG`。
- **bump 必须同步改 `:24` TAG**，否则所有带新 tag 的 URL 都被判「裸引用」→ S18 FAIL。
- 实证：含 `/` 的 `.webp/.png` 字面量 **20** 个，全部带 tag；拼接型 **2** 处（`音标大闯关/js/level.js:49`、`js/story.js:307`），段内均带 `?v=cseg-20261107`。主理人口径「20 个图片 URL 零裸引用」应指字面量集合，拼接型另计 2 处，结论一致：当前零裸引用。
- **HUD 建议零新增图片**（用矢量/纯色）→ S18 零风险。若新增贴图，必须带新 tag（会 +1 计数，触发 D.2(1) FAIL 情形 B）或走 `${CACHE_TAG}` 白名单。
- 关联：`S16`（`:96-97`）`atlas_js.count("?v="+TAG)==6` → TAG 同步即可；`F9b`（`verify_fresh_gate.py:234-238`）`card_urls` 正则抓 2 处 `?v=([A-Za-z0-9\-]+)` + 硬编码 `rarity_progress.webp?v=TAG` → atlas.js 6 处字面量与 TAG 都要同步。

**（3）浏览器「实际请求带 tag」类**

- `F8b`（`verify_fresh_gate.py:217-221`）、`F11c`（`:278-282`）、`D7.1/D7.2`（`verify_c08_gate.py:229-230`）：运行时用各自脚本 `TAG` 常量比对（`verify_fresh_gate.py:30` / `verify_c08_gate.py:29`）→ 同步改。
- `F10a`（`:291-314` 强缓存注入）：判据是 `"?v=" in u` 与 `.js/.css` 后缀，**与 tag 值无关** → bump 不影响；但新 HUD 若引入**不带 `?v=` 的 js/css 请求**会被注入 `/* STALE CACHE COPY */` → F10a FAIL。推荐方案无新请求，零风险。
- ⚠️ **发布边界**：线上 Caddy 对不存在路径兜底返回 `index.html(200)`。判资源送达必须**比字节/内容**（如 `IPA_DISPLAY.U11.displayIpa==='ɜr'`，`D7.4` / `F11c` 已这么做），**不可信状态码**。

**（4）DOM 冒烟（`verify_cseg_ui.py` 14 项，U1–U12）**

| 断言 | 冲击 |
|---|---|
| U1 / U12 四项错误计数（pageerror / console.error / 4xx / requestfailed） | 新增 HUD 若产生 404、JS 异常、console error → FAIL。推荐方案新增的是**无 src 的 DOM**（无新请求）→ 只要 JS 无异常即绿。Caddy 兜底 200 但内容不对会触发 pageerror |
| U2–U6（选择器、教学面板、开局 4 门/2 圈/3 题型） | 不动 `#map-pick/#char-pick/#teach-focus`、`buildGates()`、`race.state.gates` → 绿 |
| U7（`#gates` 含 "1/2"、`#progress span` 宽度 0<w<100） | 只要**不改 `syncHud()`（main.js:622-657）**且小地图不占用 `#gates`/`#progress` 的 id/文本 → 绿 |
| U8（三题型 quiz 卡片 + word 题不泄答案） | 只查 `#quiz-prompt`；预告牌是新 DOM，U8 不覆盖 → 需 #5 补断言（§D.4） |
| U9 / U10 / U11（结果页、解锁写盘、大闯关真实写入后 C 段字段不丢） | 不新增 localStorage 字段、不动 `openResults()`/`commit()` → 绿（§E） |

- `verify_cseg_ui.py:26` 的 `TAG` 是**死常量**（grep 全文仅此 1 处，U1–U12 无 tag 断言）；不影响断言，但为口径统一建议一并同步。

**（5）headless_laps.mjs 11 场 finishTime（A0–A6，`verify_cseg_gate.py:142-166`）**

- `headless_laps.mjs:21-23` 只 import `config.js / track.js / race.js`，**不 import `main.js / render.js`** → HUD 改动（main/render/index/css）对 `finishTime` **零影响**。
- 前提约束（#4 必须遵守）：不动 `TUNING`（laps/commits/straight/radius/roadHalf/mergeDt）、`DIFFICULTY`（speed/steer/fork/preview 数值 → 若只激活读取不改值亦可）、`BOOST/TURBO/SLOW/COLLIDE`、`track.js`、`race.js` 仿真与 `createRace()` 入参（headless 调 `createRace` 不传 `mapId`，默认 `"camp"`，`race.js:4`）。
- `A6`（`:164-166`）硬编码 `2*19254.50/speed<=150` → 不动 `track.js` 几何即绿。
- `headless_laps.mjs:19` `const TAG` 不计入 46（`.mjs` 不被扫描）；改不改都不影响断言，但为口径统一建议同步。Node 对本地文件 `?v=` 查询串不敏感，功能上不会因旧 tag 失败。

**（6）源码字面量断言 —— HUD 重构最易误伤的一组**

- `verify_cseg_gate.py`：S12 `"race.branchLateral(gate, odo0, side)"`（:86-87）、S13 `"g.lap === lapNow"`（:89）、S7 进度条分母 `track.length * (race.state.laps || TUNING.laps)`（:72-73）、S3/S4/S5/S6（race.js 字面量）、S10 `ui.teachFocus.innerHTML`（:80）、S11 `QUIZ_TITLES[kind]` / `quizPrompt.textContent` / `quizPrompt.innerHTML`（:83-85）、S15 store.js 白名单 `"maps"/"lastMap"/"lastChar"`（:94-95）。
  → **重构 `placeLaneSign()` / `syncSigns()` / `frame()` 时不得删除这些字面量**（尤其 S12、S13、S7）。预告牌新增函数应**并列新增**，不要改写既有函数体里的关键行。
- `verify_c08_gate.py`：S1.4 `len(re.findall(r'writeStore\(', main)) == 2`（:68-71）→ **新增 HUD 不得在 main.js 里写 `writeStore(` 调用**；S1.1–S1.3（`store.js` 结构）→ 不改 store.js 即绿；S1.5 / S1.6 / D8.1–D8.3 → 不动 race.js/main.js 的既有逻辑即绿。
- `verify_fresh_gate.py`：F1–F7（data.js 文案）、F5（`=== "长"`/`is-long`/`图鉴 iː · 紧音`）、F6a–F6c（`data.js / content_raw.json / data.js.bak` 的 diff 与 mtime）、F9c（49 张卡面逐字节）、D9（真双元音 13 行）→ **本轮禁改清单**（`data.js` / `ipa-display.js` / 48 张资产 / 上游构建管线）全部不碰即绿。
- `B9`（`verify_cseg_gate.py:270-272`）、`S1.6`（`verify_c08_gate.py:76-78`）、`F5`：锁 `seen[p.sym]` 与 `sym` 稳定键 → **HUD 若展示音标，必须按 unit id 查 `IPA_DISPLAY[unit].displayIpa`（`main.js:9`），禁止用 `displayIpa` 做键/去重**（U05/U07 同为 `ɑ`，换键会丢 U07）。

**（7）375px 触屏（`verify_c08_gate.py:255-259` D8.4）**：只断言 `#jump` 存在（`!!document.querySelector`），新增右上 HUD 不得移除/遮挡它；布局若引发 JS 异常会经 U1/F11d/D7.5 的错误计数 FAIL。

### D.3 新增 HUD 后 tag 字面量预计变化数

> ✅ **收尾定值（§0.0.2 / §0.0.3-6）**：Q1/Q3 落地方式已定 —— **不新建模块、不加任何 `<src>`**，`#minimap` 容器 + 内嵌 `canvas#minimap-c` + `span#minimap-lap` 均无 `src` → **46 → 46，净 +0**，三处 `== 46` 断言不用改、S18 零风险。下表其余行是「若偏离收尾方案」的风险预案（#4 不应触发）。

| 实施选择 | `?v=` 字面量变化 | 断言改动 |
|---|---|---|
| **✅ 收尾方案（Q1/Q3）**：逻辑并入既有 main.js/render.js；`#minimap` 为**无 src 的 DOM 容器 + 内嵌 canvas + lap span**；路牌复用 `#signs` 零新增 DOM；样式进既有 game.css | **46 → 46，净 +0**（46 处字符串 `cseg-20261107 → hud-20261108` 整体替换） | 三处 `== 46` **不用改** |
| ⚠️ 偏离：新建 `js/hud.js` / `js/minimap.js` 模块 | main.js 多 1 个 `from "./hud.js?v=NEW"` → 47；若新模块自身再 import config.js → 48 | 三处 `== 46` 改 47/48；S18 需检查新文件 |
| ⚠️ 偏离：新增 1 个带 tag 的 `<img>` 贴图 | +1 → 47 | 同上 + S18 校验 |
| ⚠️ 偏离：新增第二个 CSS 文件并 `<link ...?v=NEW>` | +1 → 47 | 同上 |

**预计变化数：0（收尾方案，唯一允许）～ +2（偏离方案，#4 不得触发）**。另需同步的字符串（**不计入 46**）：
- `config.js:7` `CACHE_TAG`（驱动 69/78/92 的 `${CACHE_TAG}` 模板；S17 正则抓不到 `${…}`，S18:134 白名单放行 → **改它不改变 46 计数**，这点最易误判）；
- 4 套脚本 `TAG`：`verify_cseg_gate.py:24`（S16/S17/S18 依赖）、`verify_cseg_ui.py:26`（死常量，建议同步）、`verify_fresh_gate.py:30`（F8a/F8b/F9b/F11c）、`verify_c08_gate.py:29`（S1.7/D7.1/D7.2）；
- `headless_laps.mjs:19`（不计入，建议同步）。
- 合计 **6 处** TAG/CACHE_TAG 字符串；`cseg-20261107` 全仓共 **52** 处（46 字面量 + 6 常量）。

### D.4 三套脚本 TAG 常量与 S18 的同步操作清单（给 #4）

> ✅ **收尾定值（§0.0.2）**：新 tag = **`hud-20261108`**（本轮统一 bump 一次）。原第 1 步「建议 `cseg-20261108` 或主理人指定」已作废。主理人点名「**三套脚本 TAG 常量与 S18 同步**」——即 `verify_cseg_gate.py:24`（含 S18）、`verify_fresh_gate.py:30`、`verify_c08_gate.py:29`；下表再补另外 3 处口径统一项。

1. ~~定新 tag~~ → **已定 `hud-20261108`**（不再需要裁决）。
2. 全仓 **46 处** `?v=cseg-20261107` → `?v=hud-20261108`（9 个文件，分布见 D.2(1)）。
3. `音标拉力赛/js/config.js:7` `CACHE_TAG` → `hud-20261108`（不改 `TUNING`/`DIFFICULTY` 数值）。
4. `音标拉力赛/verify_cseg_gate.py:24` `TAG` → `hud-20261108`（**S16/S17/S18 全依赖，`S18` 判据漏改必 FAIL**）。
5. `音标拉力赛/verify_cseg_ui.py:26` `TAG` → `hud-20261108`（死常量，口径统一）。
6. `音标大闯关/verify_fresh_gate.py:30` `TAG` → `hud-20261108`（F8a/F8b/F9b/F11c）。
7. `音标大闯关/verify_c08_gate.py:29` `TAG` → `hud-20261108`（S1.7/D7.1/D7.2）。
8. `音标拉力赛/js/headless_laps.mjs:19` `const TAG` → `hud-20261108`（不计入 46，口径统一）。
9. **仅当**计数变化时：同步改三处 `== 46` 与断言描述文案中的「46 处」。**收尾方案（Q1/Q3：不新建模块、不新增 `<img>` / `<link>` / `<script src>`）净变化 = 0 → 本步不执行**（§0.0.3-6）。
10. 回归：四套门控 + `node headless_laps.mjs`；资源送达按**字节/内容**校验（Caddy 兜底 200 陷阱）；不部署、不上线、不 commit。

### D.5 建议 #5（quality-lead）补的 HUD 断言

> ⚠️ **收尾修订**：原 1（results 可见）、5（`preview*speed`）、6（quiz 时预告牌「内容与位置不变」）与 §0.0 冲突 → 按 Q1/Q2/Q3 与 #1 §2.1.6 显隐矩阵 / H1–H10 重写如下：

1. **H1 DOM 存在性**：`#minimap` 与内嵌 `#minimap-c` 存在、`aria-hidden="true"`、`pointerEvents === 'none'`、底板 alpha ≥ .82。
2. **H2 显隐矩阵**（#1 §2.1.6）：`mm.hidden` 在 `title/teach/results` = `true`；`countdown/racing/paused` = `false`；`mode 仍 racing 但 boardOpen||shopOpen` = `true`；`quiz` 按 Q2 → **小地图显示但冻结**（`visible` 表达式 §0.0.3-1）。用 `window.__rally.mode/.boardOpen/.shopOpen` + 真实点击覆盖「mode 未变但面板打开」。
3. 375×780 触屏：`#minimap` rect 满足 `left≥0 && right≤375 && bottom<667 && width≤112.5`；与 `#hud` / `#banner` 无重叠（gutter + banner 下移）；`#jump` 仍在且可点（D8.4）。
4. **H7 路牌阈值**：手动设 `odo = g.line − (D_preview + 50)` → `#signs.hidden===true`；推进到 `dist = D_preview − 20`（`!g.played`）→ S1 两牌出现且 `textContent` 无字母/无 `/`；`g.played=true` → S2 两牌含 `word` 与 `/ipa/`。`D_preview` 用 follow 1482 / listen 1620（§0.0.3-2）。
5. **H8 对称性 / 不泄答案**：S1 两牌 `className` 均无 `is-long/is-short`、`textContent` 无任何字母与 `/`；S2 两牌 `rect.width` ±1px 相等、`opacity` 相等、`className` 不含 `ok/bad/correct/answer`；`#signs.innerHTML` 不含「正确」「答案」及 `g.correctLateral` 提示；小地图 `nextGate` 为中性单色菱形、无箭头/无高亮侧。
6. **H9 quiz 冻结（Q2）**：注入 `r.state.quiz` → `#signs.hidden===true`；`simTime` / `karts[0].odo` / 小地图内容在 `step(60)` 后不变；quiz 期间 `localStorage.setItem` 未调用；答完回 `racing` 后 `#signs.hidden` 恢复 `false` 且 S2 内容与进 quiz 前一致。
7. **H10 两圈**：`lap===1` 时 `#signs .sign` ≤2；`signKey` 以 `gate.id` 开头且含 `phase`；两圈同 `commitT` 门 `line` 差 = `L`（±1）；`minimapModel().nextGate.lap===1`；四区 `zone` 标签随 `mapId` 变化；圈数文本 `1/2 → 2/2`。

---

## E. 跨站影响

**结论：本轮 HUD（小地图 + 分叉预告）不需要任何新 localStorage 字段，`音标大闯关/js/store.js` 零改动，`RALLY_FOREIGN` 无需新增。**

> ✅ **收尾确认（§0.0.3-7 / §H.1）**：主理人 Q1（DOM 化）、Q2（quiz 隐藏路牌）、Q3（S0–S3 状态机 + 中性菱形）、Q4（不改 `t/odo` 偏差）**全部是纯渲染/纯 DOM 层改动，均不涉及持久化**；原 §H-3「是否持久化 HUD 偏好」已裁决为「**否**」。本节「若需持久化则必须同步 `RALLY_FOREIGN`」的分析保留为**假设性参考**（当前不触发）。

- 小地图数据源全部是**内存态**（`race.state` / `createTrack(TUNING)` 静态几何 / `RACE_MAPS` 静态表）；预告牌是**纯渲染派生**（`race.activeGate()` + `Δ`）；两者都不写盘、不读 `readPack()`、不调用 `commit()` / `applyWalletDelta()`。
- 因此 `verify_cseg_ui.py` U11、`verify_fresh_gate.py` F11b、`verify_c08_gate.py` D3.1/D3.3 等跨站断言全部不受影响。

**若 #1 规格要求持久化（如「记住小地图开关」「预告已读」）——必须同步的字段名与失败模式**：

- 需加入 `音标大闯关/js/store.js:47-48` 的 `RALLY_FOREIGN` 白名单（现为 `["gems","shields","paint","trim","ownedPaints","ownedTrims","EP02","howSeen","maps","lastMap","lastChar"]`）。示例字段名（占位，以 #1 为准）：`hudMinimap`（布尔开关）、`forkHintSeen`（布尔）。
- 同时必须：① 加入 `音标拉力赛/js/main.js:117-134 readPack()`；② 走 `commit(mutator)` 写入（`main.js:220-235`），**禁止**新增 `writeStore(` 调用（S1.4 锁 `==2`）；③ 遵守 `commit()` 的 union/LWW/delta 规则（215-235）。
- **不同步时 C08 门控如何失败**：`store.js:79-95 refreshFromRaw()` 只把 `RALLY_FOREIGN` 里的 rally 子字段并回内存视图（`:86`），新字段不在白名单 → 大闯关侧 `save()`（`:97-101`）`refreshFromRaw(data, rawRead())` 不保留它，随后 `writeRaw(data)` **全量写回会把拉力赛写入的新字段抹掉**（生产上的跨站覆盖丢字段）。门控层面：现有 `D3.1`（`:169-172`）/ `F11b`（`verify_fresh_gate.py:271-274`）/ `U11`（`verify_cseg_ui.py:220-224`）检查的是**固定字段集**，不会因新字段自动 FAIL；但一旦 #5 按规格补上「新字段跨站保真」断言（或把新字段加入 D3.1/U11 的检查集），就会因白名单缺失而 FAIL。此外 `D1.5`（`verify_c08_gate.py:127-129`）迁移产物「不含任何拉力赛 rally 子字段」检查的是另一固定名单，语义上同样会被违背。`S1.3`（`:66-67`）锁 `refreshFromRaw` 的源码字面量 → **扩充白名单只能改数组内容，不能改写 `:86` 那行代码**。
- 建议：**不新增字段**，若确需持久化，把该决策与字段名一并提交主理人裁决（§H）。

---

## F. 回滚点（本阶段唯一写操作之一，已完成）

- 路径：`C:/Users/86135/AppData/Local/Temp/hud_backup_20261108/`
- 生成时间：2026-11-08 14:51:05；**13 个文件，合计 214,840 字节**；副本已置只读属性；源根 `C:/Users/86135/WorkBuddy/英语音标播客` 产品文件**全部未改动**（已逐字节比对 `all byte-identical = True`）。
- 覆盖主理人清单：拉力赛 `js/config.js`、`js/main.js`、`js/race.js`、`js/render.js`、`index.html`、`css/game.css`；两站 `index.html`；`音标大闯关/js/store.js`；四套验收脚本；**附加** `js/headless_laps.mjs`（回归链入口）。
- `manifest.txt` 内容（相对路径 / 字节 / sha256 前 16 位）：

```
音标拉力赛/js/config.js                    12077  d3d1e721c9cafd37
音标拉力赛/js/main.js                      43451  f5f24c8bcda3eb41
音标拉力赛/js/race.js                      31070  f25c65d268043ac1
音标拉力赛/js/render.js                    15063  c9de8088b61315bb
音标拉力赛/index.html                       7283  63788fa597c5c9cc
音标拉力赛/css/game.css                    15590  03fddf51c2461db3
音标大闯关/index.html                       3531  d3421e8242bc299c
音标大闯关/js/store.js                     12981  35cd51332a55c7c2
音标拉力赛/verify_cseg_gate.py             14022  127957baf0df1daa
音标拉力赛/verify_cseg_ui.py               12884  14d9397efb03ab9f
音标大闯关/verify_fresh_gate.py            18864  f292af8764abe6dc
音标大闯关/verify_c08_gate.py              20624  0db9877209841b8a
音标拉力赛/js/headless_laps.mjs             7400  478d0223dace4e03  [附加/回归链]
```

- 回滚方法：按上表相对路径，从备份目录 copy 回源根同名路径（注意副本只读属性，copy 后按需清除）；随后用 manifest 的 sha256 前 16 位复核。
- ✅ **收尾复核（2026-11-08）**：本阶段并入主理人事实纠正与 Q1–Q4 裁决后，再次确认备份目录 13 个文件齐全、`manifest.txt` 存在、`FILES=13 / TOTAL_BYTES=214840 / SOURCE_FILES_UNMODIFIED=YES`；**源根产品文件在本阶段始终未被修改**（唯一写操作 = 本文档 + Temp 回滚点）。因此该回滚点仍是 #4 改动前的干净基线，可直接沿用，无需重建。

---

## G. 风险与缓解

| # | 风险 | 影响 | 缓解 |
|---|---|---|---|
| **G1** | **375px 触屏右上角与现有 HUD 拥挤**（结构性） | `#hud`(z5, flex-wrap 2–3 行, y≈8..100) + `#banner`(z6, top78, 窄屏近全宽) 会盖住右上 `y=16..102` 的小地图；既有 canvas 小地图正是因此显示不全 | ✅ **Q1 收尾口径**：`#minimap` `z-index:5`、`pointer-events:none`、DOM 顺序在 `#hud` 之后；**核心机制 = `#hud { padding-right: var(--mm-right-gutter) }`**（PC 184 / 触屏 120，不靠 JS 测 HUD 高度，换行不失效）；`--mm-w/h` 触屏 `min(96px,26vw)` / `min(64px,17vw)`；`#banner` 窄屏 `top: calc(var(--mm-h)+20px)`；`placeLaneSign()` 增 `mm.rect` 外扩 8px 避让裁剪；**不新增 `#fork-hint`**（复用 `#signs`）；#5 补 H2/H3 rect 断言。~~原「`z-index:6` / 缩小下移 / `.hud-row` 让位」作废~~ |
| **G2** | **两圈同 `commitT`** | 4 个门塌成 2 个位置：`flareAt` 重复画（§A.6）、小地图 `nextGate` 菱形重叠、路牌误选上一圈门、`signKey` 残留 | 复用 `race.activeGate()`（按绝对 `g.line` 选最近门，`race.js:164-175`）；小地图标记按 `g.lap===lapNow` 过滤（同 `main.js:970`）；**`signKey` 用 `` `${gate.id}:${phase}:...` ``**（含 lap 与 phase，Q3/#1 §2.2.5）；**禁用** `commitT/lineT%1/pairKey` 作 key 及 `wrapDelta/hasPassed` 相对圈逻辑；不删 S12/S13 字面量 |
| **G3** | **tag 未同步 bump 导致老用户缓存串** | ① 漏改任一处字面量 → `set` 双值 → S17/F8a/S1.7 同时 FAIL；② 新增 `?v=` → count≠46 → 三处 FAIL；③ 漏改 `verify_cseg_gate.py:24 TAG` → S18 把全部 URL 判裸引用 FAIL；④ **生产侧**：旧缓存命中旧 `main.js/render.js/game.css`，新 HUD 根本不出现，而 Caddy 兜底 200 会掩盖 404，状态码不可信 | 严格执行 §D.4 十步清单，新值 **`hud-20261108`**；收尾方案（不新建模块 / 无新 `src`）保持 46 不变；`config.js:7 CACHE_TAG` 必改（否则 config 内 3 处 sprite 模板仍是旧串）；回归按**字节/内容**校验资源送达（`IPA_DISPLAY.U11.displayIpa==='ɜr'`）；四套门控 + headless 全跑；不部署不上线不 commit |
| **G4** | **quiz 冻结时的计时与信息叠加口径** | 双累加器（`simTime` / `race.state.time`）在 frozen 时停，但 `render()` 每帧仍跑、`syncSigns()` 在 quiz 态仍执行 → ① 若用 `performance.now()`/`setTimeout`/CSS animation 做倒计时或淡出会穿过冻结窗口、恢复后跳变且 headless 无法复现；② `ipa/type` 题 `#quiz-prompt` 写出 `q.spoken.word`（`main.js:774`）与 `#signs` 两侧词同屏构成提示 | ✅ **Q2**：`syncSigns()` 增分支 → **`#signs.hidden = true`**（quiz 隐藏路牌），小地图**显示但冻结**；回 `racing` 按 `played` 重现 S2、不重新播音/不重播动画。S1/S2 牌**静态无计时动画**；触发用里程常量 `Δ ≤ D_preview`（名义 `diff.speed`，不读 `speedNow`）；动画一律用 `simTime`；#5 补 H9「quiz 下 `step(60)` 前后 `simTime`/`odo` 不变、`setItem` 未调用」断言。~~原「保持显示但静止」作废~~ |
| G5 | **既有 `drawMinimap()` 被误当「新建」或改错层** | #4 可能重复实现第二套小地图，或把小地图仍画在主 canvas `#c` 内导致遮挡依旧 | ✅ **F1/Q1**：既有绘制**迁入** `#minimap` 的内嵌 `#minimap-c`（不是另起一套、不是停用）；主 canvas 侧 `minimap:` 改显式 `visible`；开工前先跑一次浏览器截图确认现状。**另见 G11：`#route-map` 不得被误判为重叠而位移/删除** |
| G6 | **`preview` 是死字段** | 若误把 `race.previewSteer()`（`race.js:777`，倒计时转向插值）当成消费者，或改动 4.2/4.0 数值 → 触发距离错、动难度平衡与 headless | ✅ **F3 已澄清 + #1 §2.2.2 已定单位**：`preview` 是**秒数基准**，`D_preview = span·L + 0.5·preview·speed`（follow 1482 / listen 1620 里程）；激活读取但**不改值**；不与 `previewSteer()` 混淆；不新增参数 |
| G7 | **`sym` 稳定键 / 不泄答案** | HUD 若用 `displayIpa` 做键或去重，U05/U07 同为 `ɑ` 会丢 U07（`story.js:206 seen[p.sym]`）；路牌若写 `spoken.word` 或单侧箭头即泄答案 | 按 unit id 查 `IPA_DISPLAY[unit].displayIpa`（`main.js:9`）；**单向铁律**：`correctLateral`/`spoken` 只许出现在 `audio.playWord()`（`race.js:436`）与 `judge()`（`race.js:213-262`）；S1 零文本、S2 两侧严格对称、小地图中性菱形；S11/B9/S1.6/F5 锁字面量不动；#5 补 H5/H6/H8 |
| G8 | **性能** | `drawMinimap` 现每帧 O(520)；内嵌 canvas 每帧重绘 + 额外 rAF 会叠加 | 几何 min/max 与环线 path **启动时算一次缓存**（`track.js` 只吃 TUNING）；每帧只更新 3 车点 + 进度弧 + `nextGate`；节流 20–30fps / `Δodo>8`；不新增 rAF/定时器；`minimapModel()` 热路径零分配、可 Node 单测；`reduced`（`main.js:16`）下关闭非必要动效；`backdrop-filter` 不强制 |
| G9 | **内嵌 canvas 的 dpr / CSS 尺寸一致性** | `#minimap-c` 若只写位图 `width/height` 而不设 dpr，高分屏会模糊；坐标换算需与 CSS 显示尺寸一致 | ✅ **Q1 方案 A 已给契约**：`dpr = min(2, devicePixelRatio)` 设位图尺寸，绘制前 `ctx.setTransform(dpr,0,0,dpr,0,0)`，与 `main.js:731-737 resize()` 同源（#1 §2.1.3）。**不再是「无解的知识缺口」**；仍建议 #5 在 `device_scale_factor=2/3` 复核一次 |
| G10 | **发布边界** | 误部署/上线/commit 会越过用户审批 | 本轮不部署、不上线、不 commit；所有高影响动作留人工审批 |
| **G11** | **`#route-map` 被误判为「与小地图重叠」而遭位移/删除**（F2 纠错） | 美术方向稿 `visual-direction-3d.md` §I.5 / 附录① 断言「`#route-map` 与 `drawMinimap` 当前位置重叠」**不成立**。二者互斥（`main.js:256 ui.routeMap.hidden = next !== "title"`；`drawMinimap` 仅 `mode !== "title"`）。误删会丢**标题页四区世界观导航 + 跨站入口**（`href="../音标大闯关/index.html#/map"`） | ✅ **裁定**：右上角 = **「title 页 = a1 四区大地图入口 / 比赛中 = 该轮闭环小地图」同位置角色切换，不新增第三层**；`#route-map` **保持不动、不位移、不删除**；#4 不得据美术方向稿该断言做布局改动；如需修订方向稿文字，由 art-director 处理（不属 #3/#4 范围） |
| **G12** | **`placeLaneSign` 的 `t`/`odo` `0.02·L` 偏差被顺手「修正」**（Q4） | `t0 = gate.commitT − k·span`（相对）与 `odo0 = gate.line − k·span·L`（绝对）差 `startOdo/L = 0.02`（≈385 里程），因 `commitT` 未含 `startOdo` 偏移（`race.js:83`）。若 #4 顺带统一，会**移动所有既有路牌**、扩大回归面 | ✅ **Q4 裁定：本轮不改**。`placeLaneSign()` 只做 `span → spanEff` 参数化，`0.66/0.34/0.36` 系数、`project()`、`--lane`、屏幕裁剪、S12 字面量全部保留；**新增逻辑一律 `t_i = (odo_i/L) % 1` 从绝对 `odo` 派生**；旧不一致**登记为遗留项**，下一轮或单独回归窗口评估（若修需 #5 补路牌投影位置回归断言） |
| **G13** | **`boardOpen` / `shopOpen` 叠加态漏判显隐**（F5） | 打开排行榜/商店时 `mode` **仍是 `racing`**（`main.js:811-821`、`874-889`），只看 `mode !== "title"` 会继续绘制小地图 → `.panel`(z8)/`#shop-panel`(z12) 下出现幽灵轮廓，且 #5 断言失效 | ✅ 按 §0.0.3-1 的 `visible` 表达式：`(mode ∈ {countdown,racing,paused,quiz}) && !boardOpen && !shopOpen && !!race`；`render()`/`syncSigns()` 在 frozen 期每帧仍执行（`main.js:990`），显隐**必须显式控制**，不能依赖「画面冻结了就不会变」；#5 H2 必须覆盖「mode 仍 racing 但 boardOpen=true」 |
| **G14** | **`D_preview` 阈值用 `speedNow()` 抖动 / 单帧 `odo` 跳变**（#1 E3/R6） | `speedNow()` 受 `BOOST 1.48`/`TURBO 1.92`/`SLOW 0.54` 影响，阈值忽长忽短；`launch()` 单帧最多 +1200 里程可能从 `dist > D_preview` 直接跳到 `dist ≤ lead` | 阈值用**名义 `diff.speed` 常量**（`D_preview` 固定 1482/1620），不读 `speedNow()`；允许 S1 被跳过直接进 S2（`played` 由 `beginDecide()` 兜底置位），**不允许 S1 内容残留在 S2**；#1 §E3 |

---

## H. 裁决记录 / 与 #1 的依赖 / 剩余知识缺口（收尾版）

> ⚠️ 本节原为「待主理人裁决 6 项」。**Q1–Q4 + tag 已由主理人独立读码后全部裁决（§0.0.2）**，#1 `hud-ux-spec.md` 亦已定稿（Task #1 completed）。以下改为**裁决结果登记 + 剩余依赖/缺口**。

### H.1 已裁决（无需再问）

| 原待裁决项 | 裁决结果 | 依据 |
|---|---|---|
| 小地图载体 | **Q1 = A DOM 化**（`#minimap` + 内嵌 canvas + lap span，`z-index:5`，DOM 顺序在 `#hud` 后） | §0.0.2 / #1 §2.1.1；原「SVG / 方案 ②回退」作废 |
| `preview` 单位与阈值 | **秒数基准**；`D_preview = span·L + 0.5·preview·speed` = 1482 / 1620 里程（5.70 / 5.40 s）；S1 零文本、S2 才给对称候选词 | F3 / #1 §2.2.2 / §2.2.1；原 `preview*v`（1092/1200）作废 |
| 预告载体 | **Q3 = 两者都做**：S1 世界空间中性牌（复用 `#sign-l/r`）+ 小地图中性菱形；零新增路牌 DOM | §0.0.2；原 `#fork-hint` + `syncForkHint()` 作废 |
| quiz 冻结 | **Q2 = 路牌隐藏**（`#signs.hidden = true`），小地图显示但冻结 | §0.0.2 / #1 §2.2.6 |
| `t`/`odo` 偏差 | **Q4 = 本轮不改**，新增逻辑 `t_i = (odo_i/L)%1`，旧偏差登记遗留项 G12 | §0.0.2 / #1 §2.2.4 |
| HUD 偏好持久化 | **不新增 localStorage 字段** → `store.js` 零改动、`RALLY_FOREIGN` 不扩充 | §E / §0.0.3-7（裁决维持「否」） |
| 新缓存串 | **`hud-20261108`**（统一 bump 一次） | §0.0.2 / §D.4 |
| 美术方向稿重叠断言 | **不成立**；`#route-map` 不动不删；同位置角色切换、不新增第三层 | F2 / §G11 |

### H.2 剩余依赖与知识缺口（非阻塞 #3，供主理人下发 #4 规格时纳入）

1. **#4 完整实现规格**：主理人已明确「在 #3 回传后单独下发」。本报告 §0.0 / §B / §C / §I 是盘查侧的控制基线，#4 以主理人规格 + #1 `hud-ux-spec.md` 为最终准；若两者有差异，#4 应回问主理人，不自行折中。
2. **#1 与本报告的一处待澄清**（已在 §0.0.4 登记）：#1 §2.1.4「面板打开时显式隐藏小地图」与 §2.1.6「quiz 显示但冻结」对 `quiz` 口径略有张力；Q2 只裁决了**路牌**隐藏。建议 #4 规格明确 quiz 下 `#minimap` 究竟「显示但冻结」还是「随面板隐藏」——两者都不影响本报告结论，但会影响 #5 的 H2 断言期望值。
3. **`minimapModel(view)` 单测**：建议 #4 先写 Node 单测（坐标范围 / lap 过滤 / 四区映射 / `odo/(laps·L)` 进度），再实现（验证驱动）。
4. **G9 已收敛**：Q1 方案 A 已给内嵌 canvas 的 `dpr = min(2, devicePixelRatio)` + `setTransform(dpr,…)` 契约（与 `main.js:731-737` 同源），不再需要补引擎/浏览器参考；仍建议 #5 在 `device_scale_factor=2/3` 复核一次。
5. **`design/visual-direction-3d.md`（#2）**：下一轮 3D 方向稿，本轮不消费；其 §I.5 / 附录① 的重叠断言按 F2 纠错（§G11），**文字修订由 art-director 处理，不属 #3/#4 范围**。用户已拍板本轮不改渲染层视角。
6. **发布边界**：不部署、不上线、不 commit；所有高影响动作留人工审批。

---

## I. 给 #4 程序员的一页控制清单（收尾版，可直接执行）

> 依据：**§0.0 收尾基线（Q1–Q4 + tag 定值）＞ `design/hud-ux-spec.md`（#1，已定稿）＞ 主理人另行下发的 #4 规格**。三者有差异时回问主理人，不自行折中。

1. **先读**：本报告 **§0.0** → `design/hud-ux-spec.md`（#1 全文，尤其 §2.1／§2.2／§5 裁决表／§6 QA H1–H10）→ §B/§C/§D/§G → §F 备份 manifest → **主理人下发的 #4 规格**。
2. **禁改**：`data.js`、`ipa-display.js`、`story.js`、`track.js` 几何、`cards.js`、`audio.js`、`race.js` 仿真与 `startOdo`、48 张立绘/卡面、`content_raw.json` / `build_data.py` / `augment_data.py`；不重跑上游管线；**`#route-map` 的 DOM 与 `main.js:256` title 显隐不动不删**（F2/G11）。
3. **不改数值**：`TUNING` / `DIFFICULTY`（含 `preview` 4.2/4.0、`fork` 3.6/3.4、`speed` 260/300）/ `forkSpan` / `buildGates` / `race.js` 仿真 / `createRace()` 入参 → 保 `headless_laps.mjs` 11 场 finishTime；**只读取** `diff.preview` 作为 `D_preview` 秒数基准，不赋值改动。
4. **Q1 小地图 DOM 化**：新增 `#minimap`（DOM 顺序在 `#hud` 之后）+ 内嵌 `#minimap-c` + `#minimap-lap`；`z-index:5`、`pointer-events:none`、`aria-hidden="true"`、半透明底板；**把既有 `drawMinimap()` 迁入内嵌 canvas**（不是另起一套、不是停用）；内嵌 canvas `dpr = min(2, devicePixelRatio)` + `setTransform(dpr,…)`；CSS 变量 `--mm-*` + `#hud padding-right: var(--mm-right-gutter)` + `#banner` 窄屏下移；`pointer-events:none`。
5. **显式显隐（F5）**：`frame()` 的 `minimap:` 改 `visible = (mode ∈ {countdown,racing,paused,quiz}) && !boardOpen && !shopOpen && !!race`；面板打开时显式隐藏，不依赖遮挡或「画面冻结就不会变」。`render()`/`syncSigns()` 在 frozen 期每帧仍执行。
6. **Q3 路牌 S0–S3**：改造 `syncSigns()`（S0 隐藏 / S1 `paintForecast()` 零文本中性 / S2 `paintLane()` 对称选项 / S3 判后隐藏）；`placeLaneSign()` 仅参数化 `span → spanEff`（S1 传 `D_preview/L`、S2 传 `race.state.span`），**保留** `0.66/0.34/0.36` 系数、`project()`、`--lane`、屏幕裁剪；增 `mm.rect` 外扩 8px 避让裁剪；**零新增路牌 DOM**（复用 `#sign-l/r`）；`signKey` 改 `` `${gate.id}:${phase}:${left.word}:${right.word}` ``。
7. **Q2 quiz**：`syncSigns()` 增分支 `#signs.hidden = true`；小地图显示但冻结；回 `racing` 按 `played` 重现 S2、不重新 `playWord`、不重播 `open` 动画。
8. **阈值与坐标**：`D_preview = span·L + 0.5·preview·speed`（follow 1482 / listen 1620 里程），用名义 `diff.speed`、**不读** `speedNow()`；新增逻辑一律 `t_i = (odo_i/L) % 1` 从绝对 `odo` 派生；小地图进度/圈数用 `odo/(laps·L)`、**不用 `t`**；`pointAt(t, 归一化lateral)` / `branchLateral(gate, 绝对odo, side)` 保持现状；小地图投影用 min/max→ox/oy/sc，**不要**用 `project(matrix,…)`（那是主相机）；**Q4：不修 `0.02·L` 偏差**（G12 遗留项）。
9. **两圈**：一律按 `g.line` 绝对里程；渲染/小地图按 `g.lap===lapNow`；key 用 `gate.id`（含 lap）+ `phase`；**禁用** `commitT/lineT%1/pairKey` 作 key 与 `wrapDelta/hasPassed` 相对圈逻辑。
10. **冻结与不泄答案**：S1/S2 牌静态、无墙钟/`setTimeout`/CSS 计时动画；动画用 `simTime` 或 `Δ` 派生；**单向铁律** —— `correctLateral`/`spoken` 只许出现在 `audio.playWord()`（`race.js:436`）与 `judge()`（`race.js:213-262`），HUD 的 `innerHTML`/`fillText`/`data-*`/alt/aria-label 一律不得接触；S1 零文本、S2 两侧同帧同尺寸同不透明度、小地图 `nextGate` 中性单色菱形。
11. **`sym` 是英式稳定键**：查表/去重/角标/alt 按 unit id 查 `IPA_DISPLAY[unit].displayIpa`；禁止 `displayIpa` 做键（U05/U07 同为 `ɑ`）。
12. **tag = `hud-20261108`**：按 §D.4 十步；46 处字面量 + `config.js:7 CACHE_TAG` + 4 脚本 `TAG` + `headless_laps.mjs:19`；**`verify_cseg_gate.py:24 TAG`（S18 判据）必改**。**不新建模块 / 不加 `<src>` → 保持 46**，三处 `==46` 断言不改。
13. **不新增 `writeStore(` 调用**（S1.4 锁 `==2`）、**不新增 localStorage 字段**（`store.js` / `RALLY_FOREIGN` 零改动）。
14. **保留源码字面量**：S12 `race.branchLateral(gate, odo0, side)`、S13 `g.lap === lapNow`、S7 进度条分母、S11 `quizPrompt.*`、S1.1–S1.3 `store.js` 结构行、B9 `seen[p.sym]`。
15. **验证驱动 / 回归 / 边界**：先给 `minimapModel(view)` 写 Node 单测再实现；#5 按 §D.5（对齐 #1 H1–H10）补断言；四套门控 110 项 + `node headless_laps.mjs` 全绿；资源按**字节/内容**校验（Caddy 兜底 200 陷阱）；375×780 视口人工过一眼；**不部署、不上线、不 commit**，高影响动作人工审批；出问题按 §F 从 `Temp/hud_backup_20261108/` 回滚。
