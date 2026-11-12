# CSEG-E1 · 2D HUD 正式实现报告（Task #4）

- **角色**：engineering-lead（程基岩） · **优先级**：P0 · **状态**：实现完成，待 #5 回归
- **规格依据**：team-lead 下发的《Task #4 / CSEG-E1 正式实现规格》（优先级最高）＞ `design/hud-ux-spec.md`（#1 定稿）＞ `hud-impl-plan.md` §0.0 ＞ §B/§C/§D/§G
- **实现窗口**：2026-11-08 · **发布边界**：未部署、未上线、未 commit（保持）
- **本轮不消费** `design/visual-direction-3d.md`「甲 · 立体书」方向稿、不改渲染层视角；只为下一轮 3D 化留下 HUD DOM / `minimapModel` / 事件契约

---

## 1. 交付结论

右上角「该轮比赛小地图」与「路牌两级预告」已真实做进现有 2D 游戏：

- 小地图从 `render.js` 主画布 `drawMinimap()` **迁入** DOM 内嵌 canvas（增强，非另起一套），抽 `minimapModel(view)` 纯函数，补圈数 / 进度弧 / 起终点 / 中性 `nextGate` 菱形。
- 路牌预告复用既有 `#sign-l / #sign-r`，`syncSigns()` 改 S0–S3 状态机；S1 零文本中性牌 + 小地图菱形，S2 对称候选词。`D_preview = span·L + 0.5·preview·speed` 启用闲置常量。
- 全仓缓存串统一 bump `cseg-20261107 → hud-20261108`（46 处 `?v=` 字面量 + 6 个常量点，计数保持 46）。
- **四套门控 110 项全绿** + `headless_laps.mjs` 11 场 ALL PASS + Node 单测 10/10 + HUD 专项冒烟 27/27 + 状态机冒烟 13/13 + 8 个资源按字节全等。

---

## 2. 逐文件改动清单（严格照规格，未扩面）

| # | 文件 | 改动 | 字节变化 |
| --- | --- | --- | --- |
| 1 | `音标拉力赛/index.html` | 仅新增 `#minimap`（容器 + `<canvas id="minimap-c">` + `<span id="minimap-lap">`），DOM 顺序在 `#hud` 之后；`aria-hidden="true"`。**未新增** `<script src>` / `<link>` / `<img src>` / 路牌 DOM | +370 |
| 2 | `音标拉力赛/css/game.css` | `:root` 注入 `--mm-w/h/right/top/right-gutter`；`#hud { padding-right: var(--mm-right-gutter) }`（375px 避让核心）；新增 `#minimap` / `#minimap-c` / `#minimap-lap` / `.sign .fc` 样式；复用既有 `@media (max-width:640px)` 断点覆盖触屏值并下移 `#banner`（`top: calc(var(--mm-h) + 20px)`）。未新增断点 | +1575 |
| 3 | `音标拉力赛/js/render.js` | `render()` 末尾 `if (view.minimap && view.mmCtx && view.mmModel) drawMinimap(view.mmCtx, view.mmModel)`；新增 `MM_ZONES` / `mmProjector()` / **导出** `minimapModel(view)` / `drawDiamond()` / 重写 `drawMinimap(mmCtx, model)`。保留 `flareAt` / `project` / `render` 语义，主画布不再承载小地图 | +4423 |
| 4 | `音标拉力赛/js/main.js` | import 增 `minimapModel`；`ui` 增 `minimap/minimapC/minimapLap`；模块级增 `signPhase/lastSignState/lastMmModel/mmCtx/mmRect`；新增 `previewDistance()` / `paintForecast()` / `computeSignState()` / `buildMmView()` / `updateMinimap()` / `currentMmModel()` / `currentMmRect()`；`syncSigns()` 改 S0–S3 状态机（消费前置 `signState`）；`placeLaneSign()` 参数化 `span→spanEff` + 小地图 rect 外扩 8px 避让裁剪；`frame()` 显式 `visible` 表达式 + 相位前置；`window.__rally` 增只读 getter | +7697 |
| 5 | `音标拉力赛/js/config.js` | **仅** `:7 CACHE_TAG = "hud-20261108"`；`TUNING` / `DIFFICULTY` / `forkSpan` / `buildGates` 逐字未动 | −1 |
| 6 | 缓存串（9 文件 46 处 + 6 常量点） | 46 处 `?v=cseg-20261107 → ?v=hud-20261108`；同步 `verify_cseg_gate.py:24`（含 S18 判据）/ `verify_cseg_ui.py:26` / `verify_fresh_gate.py:30` / `verify_c08_gate.py:29` / `config.js:7` / `headless_laps.mjs:19`。三处 `==46` 断言与描述文案不动 | 净 0（tag 字符串各 −1 字节） |
| 7 | `音标拉力赛/js/minimap_model.test.mjs` | **新建** Node 单测（TDD 验证驱动）：坐标范围 / lap 过滤 / 两圈同 commitT / 四区映射 / `odo/(laps·L)` 进度 / 字段白名单 / 圈数文本 / 纯函数只读，10 项。`.mjs` 不被浏览器加载、不新增 `<script src>`、不进 `.html/.js/.css` tag 扫描 | 新增（测试证据） |

**未改动**（对照 §3 回滚点逐字节验证）：`data.js` / `ipa-display.js` / `story.js` / `track.js` / `race.js`（仅 2 处 tag）/ `cards.js` / `audio.js` / `store.js` / `RALLY_FOREIGN` / 48 张立绘卡面 / `content_raw.json` / `build_data.py` / `augment_data.py` / 上游构建管线；`#route-map` DOM 与 `setMode` 的 `ui.routeMap.hidden` 保持不动。

---

## 3. 关键架构 / 技术决策（ADR 摘要）

### ADR-1 · 小地图 DOM 化（Q1=A）
- **上下文**：`render.js:420 drawMinimap()` 已存在，画在主画布右上，被 `z-index` 浮层遮挡；规格要求「右上角该轮比赛小地图」且为 3D 轮留 DOM 契约。
- **决定**：`#minimap`（`z-index:5`，DOM 在 `#hud` 之后）+ 内嵌 `<canvas>`；`drawMinimap()` 迁入内嵌 canvas，不改停用；底板由 CSS 提供。
- **备选**：(a) 继续主画布绘制 —— 否决（无法做 `pointer-events:none` / `aria-hidden` 语义，且 3D 轮会改投影）；(b) 独立 DOM/SVG 层 —— 否决（新增 DOM 类型、偏离 #1 内嵌 canvas 口径）。
- **后果**：`render()` 新增 `mmCtx` / `mmModel` 入参；`updateMinimap()` 每帧设内嵌 canvas 位图尺寸 `mmW·dpr × mmH·dpr`（`dpr = Math.min(2, devicePixelRatio)`，`main.js:867` 同源），绘制前 `setTransform(dpr,…)`。

### ADR-2 · 显式显隐表达式（取代 `minimap: mode !== "title"`）
```js
visible = (mode === "countdown" || mode === "racing" || mode === "paused" || mode === "quiz")
          && !boardOpen && !shopOpen && !!race;
```
- `boardOpen` / `shopOpen` 打开时 `mode` 仍是 `racing`，不能只看 `mode`；`render()` / `syncSigns()` 在 frozen 期每帧仍执行，显隐必须每帧显式设置 `mm.hidden`，不能依赖「画面冻结就不会变」。
- **quiz 口径**（本规格裁定）：`quiz → mm.hidden === false`（显示但冻结），与 `paused` 对称；靠 `.panel` z=8 > `#minimap` z=5 层叠，不做几何不相交。

### ADR-3 · 相位前置单一来源（消除滞后一帧）
- **问题**：`updateMinimap()` 在 `render()` 前执行并读 `signPhase`，而 `syncSigns()` 在 `render()` 后才更新 `signPhase` → 小地图 `phase` 滞后一帧，S1 进入时菱形晚一帧点亮。
- **决定**：抽纯函数 `computeSignState()`（零 DOM 副作用），在 `frame()` 最前置计算一次 `signState = {phase, gate, deciding, spanEff, D_preview}`，`updateMinimap()` / `render()` / `syncSigns()` 共用同一结果。
- **冻结态**：`(frozen && lastSignState) ? lastSignState : computeSignState()` —— quiz / paused「显示但冻结」，`step(60)` 后 `phase` 与 `model` 逐字段相等、菱形不闪、不重新 `audio.playWord`。
- **后果**：`buildMmView(mmW, mmH, phase)` 接收显式 phase；`syncSigns(matrix, signState)` 不再重复判定相位。

### ADR-4 · S0–S3 状态机 + `D_preview`（Q3 两者都做 / Q2 quiz 隐藏）
```
D_preview = span·L + 0.5·preview·speed   // follow 1482 / listen 1620 里程 ≈5.70/5.40s
```
- S0 无门临近 / `dist > D_preview` → 隐藏；S1 `!played && dist ≤ D_preview` → 零文本中性牌（`◇`，`forecast` 类，`plainSteers()` 保持普通态）+ 小地图菱形；S2 `played` → `paintLane()` 两侧对称候选词；S3 `judged` / `unheard` → 隐藏。
- `signKey = ${gate.id}:${phase}:${gate.left.word}:${gate.right.word}`（纳入 `gate.id` 含 lap 与 `phase`），禁用 `commitT` / `lineT%1` / `pairKey` 作 key。
- `spanEff`：S1 = `D_preview/L`，S2 = `race.state.span`；`placeLaneSign()` 保留 `0.66/0.34/0.36` 系数与 `project()` / `--lane` / 屏幕裁剪，新增 `mmRect` 外扩 8px 避让。
- **Q2**：`mode === "quiz"` / `boardOpen` / `shopOpen` / `results` 显式隐藏路牌，刻意不触碰 `signKey` / `dataset.opened` / 牌内容 → 回 `racing` 按 `played` 无缝重现 S2，不重播 `open` 动画、不重新播音。
- **Q4**：不修 `placeLaneSign` 的 `t` / `odo` `0.02·L` 偏差（登记遗留项 G12）；新增逻辑一律 `t_i = (odo_i/L) % 1` 从绝对 `odo` 派生。

### ADR-5 · 不泄答案单向铁律 + 字段白名单
- `correctLateral` / `spoken` 只出现在 `audio.playWord()` 与 `judge()`；HUD 的 `innerHTML` / `fillText` / `data-*` / `alt` / `aria-label` 零接触。
- `minimapModel(view)` 输出白名单：`id/lap/commitT/lineT/line/odo/laps/mapId/zone/progress/nextGate{id,lap,line,distance,secondsTo}/phase`；`nextGate` 严格 5 键，中性单色菱形，无左右指向。
- S1 零文本、S2 两侧同帧同尺寸同不透明度同动画时长；`sym` 稳定键，不用 `displayIpa` 作键。

### ADR-6 · `window.__rally` 只读契约（为 #5 H1–H12）
- 新增 `minimapRect()` / `minimapModel()` / `signKey` / `signPhase` getter，全部零副作用、不写盘、不改游戏状态；`minimapModel()` 优先返回当前帧快照，未接线帧即时构建纯模型（保证 H6/H10 任意时刻可取值）。
- 既有 `mode` / `race` / `camera` / `boardOpen` / `shopOpen` / `simTime` / `frame` / `step` / `vowels` 保持。

---

## 4. 不可越界铁律 · 逐条核验

| 铁律 | 核验结果 |
| --- | --- |
| 禁改文件（data/ipa-display/story/track 几何/race 仿真与 startOdo/cards/audio/store） | 对照回滚点：除 `race.js` 仅 2 处 tag 字符串替换外，全部逐字节等价；`store.js` / `RALLY_FOREIGN` 零改动 |
| 不改 `TUNING` / `DIFFICULTY`（含 speed/fork/preview）数值 | `config.js` 去掉 `CACHE_TAG` 行后与回滚点全文相等；数值断言全在场 |
| `correctLateral` / `spoken` 单向铁律 | HUD 函数段零引用；`minimapModel` 递归键名零泄漏 |
| 两圈按 `g.line` / `g.lap === lapNow` / `gate.id + phase` | 冒烟实测 4 门 id `[0,1,2,3]`、同 commitT 两圈 `line` 差 = `L = 19254.5` |
| 新增逻辑 `t_i = (odo_i/L)%1`、进度用 `odo/(laps·L)` | `minimapModel` 单测 T2c / T4 覆盖 |
| 冻结态 S1/S2 牌静态、无墙钟 / `setTimeout` / CSS 计时动画 | 冻结态沿用 `lastSignState`；`step(60)` 后 `odo`/`simTime` 全等 |
| 不新增 localStorage 字段 / 不新增 `writeStore(` 调用 | `main.js writeStore(` = 2（S1.4 PASS）；9 个 HUD 函数段内 `localStorage`/`setItem`/`writeStore`/`save(` 全 NONE |
| 46 处 tag 唯一、20 图片 URL 零裸引用、三处 `==46` 不改 |直方图 `{'hud-20261108': 46}`；裸引用 0；S17/F8a/S1.7 全 PASS |
| 不替 #5 写 `verify_hud_spec.py` | 未创建；所有冒烟脚本均放 `C:/Users/86135/AppData/Local/Temp/`，不进产品仓 |
| 不部署 / 不上线 / 不 commit | 保持 |

---

## 5. 自测证据（可复跑）

### 5.1 验证驱动（TDD）
- `node js/minimap_model.test.mjs`：红阶段 `0 PASS / 10 FAIL`（`render.js 尚未 export minimapModel`）→ 实现后 **`10 PASS / 0 FAIL / 10 TOTAL`**。
- 证据：`音标拉力赛/js/minimap_model.test.mjs`。

### 5.2 四套门控 110 项全绿
| 门控 | 结果 | 关键数字 |
| --- | --- | --- |
| `音标拉力赛/verify_cseg_gate.py` | **38 PASS / 0 FAIL** | S17 `{'hud-20261108': 46}`、S18 零裸引用、A0–A6 headless 11 场、S12/S13/S7/S11 源码字面量全保留 |
| `音标拉力赛/verify_cseg_ui.py` | **14 PASS / 0 FAIL** | U1/U12 四项错误计数全 0；U7 HUD 第 1/2 圈；跨站保真 |
| `音标大闯关/verify_fresh_gate.py` | **21 PASS / 0 FAIL** | F8a `{'hud-20261108': 46}`、F11c 拉力赛实际请求全带新 tag、F11d 四项错误全 0 |
| `音标大闯关/verify_c08_gate.py` | **37 PASS / 0 FAIL** | S1.4 `writeStore(` 计数、S1.7 tag 唯一、D7.5 四项错误全 0、D8.4 375px `#jump` |
| **合计** | **110 / 110** | — |

> **浏览器门控偶发抖动披露（两类，均非产品缺陷，建议 #5 串行跑 + 失败复跑一次）**：
>
> 1. **`verify_cseg_ui.py` U12**：三套门控**并行**启动时曾报 `console_error:4 / requestfailed:4`（U1 初次加载为 0）。`_diag_u12.py` 逐阶段复现 U1–U11 全链路 → 四项错误计数**恒 0**；单独重跑 → 14/14 全绿、四项错误全 0。归因：Playwright 并发抢系统 Chrome / in-process server 的瞬态抖动。
> 2. **`verify_fresh_gate.py` F10a**（G5 强缓存场景）：偶发 `console_error:1~2`（`stale_hits=0` 核心判据恒过、`pageerror=0`）。`_diag_f10a.py` 连跑复现，捕获到的失败是 `net::ERR_CONNECTION_REFUSED`，URL 在 `U38.webp?v=hud-20261108` / `U34.webp?v=hud-20261108` 之间**随机变化**；两文件均物理存在（U38 = 74718 bytes），`atlas.js` 动态拼接型已正确带新 tag，`stale_hits=0` 恒过。归因：in-process `ThreadingHTTPServer` 在 48 张立绘并发请求下偶发拒连（脚本自身的服务器容量抖动，回滚前基线用同一套 server 逻辑同样存在）。连跑 3 次 fresh：`20/21（console_error=2）` → `21/21` → `21/21`，非确定性失败、与缓存串 / HUD 改动无关。
>
> **最终串行稳定回归（交付留档）**：逐套顺序执行 `verify_cseg_gate.py 38/38` → `verify_c08_gate.py 37/37` → `verify_cseg_ui.py 14/14` → `verify_fresh_gate.py 21/21` → `headless_laps.mjs ALL PASS`，**一次性 110/110 全绿、11 场 ALL PASS**。四套门控的**确定性判据（静态 / Node 内核 / 源码结构 / DOM 冒烟 / 跨站保真 / tag 唯一）全部稳定全绿**。

### 5.3 headless 实跑
- `node js/headless_laps.mjs`：**11 场 ALL PASS**，最慢 `174.57s ≤ 180s`，4/4 门判定、跨圈 1 次、`result.time === finishTime`；`finishTime` 与回滚前基线一致（无仿真改动）。

### 5.4 缓存串 / 图片 URL / 完整性
- 直方图 `{'hud-20261108': 46}`（唯一）；9 文件 46 处 `?v=` 字面量 + 6 常量点 = 52 处替换，产品/脚本文件 `cseg-20261107` 残留 **0**。
- 20 个含 `/` 图片 URL 零裸引用（含 2 处动态拼接型）。
- 回滚点 13 文件副本字节+sha 与 `manifest.txt` 全一致，**仍可用**；非 HUD 文件逐文件 `当前 == 备份.replace(OLD,NEW)`（逻辑零改动）。
- 8 个关键资源按字节送达（比 sha256，不信 Caddy 兜底 200）：`index.html` / `game.css` / `config.js` / `main.js` / `render.js` / `race.js` / `track.js` / `ipa-display.js` 全等。

### 5.5 HUD 专项冒烟（`_smoke_hud.py`，27 PASS / 0 FAIL）
- **375×780**：小地图显示、结构完整、`pointer-events:none`、`aria-hidden=true`、底板 `rgba(255,250,240,0.94)`（alpha .94 ≥ .82）；rect `{left:269,top:8,right:365,bottom:71.75,width:96,height:63.75}`（不溢出、`width ≤ 112.5`）；与 HUD chips / banner / route-map 零相交；`banner` 强制可见后 `gap = 12px`、不相交（CSS `computedTop=83.75px` 下移生效）；圈数「1/2」不含「听对」。
- **quiz 显示但冻结**：`mm.hidden === false`、`#signs.hidden === true`，`step(60)` 后 `karts[0].odo` / `simTime` 完全相等。
- **字段白名单**：`minimapModel()` 递归键名零答案域；`nextGate` 严格 5 键；语义口径（textContent + 属性）零词面。
- **320×568**：不溢出（`width 83.19 ≤ 96`）。
- **1280 显隐矩阵**：title/teach 隐藏、countdown/racing 显示、`boardOpen` 且 mode 仍 racing → 隐藏。
- 四项错误计数全 0；截图 `C:/Users/86135/AppData/Local/Temp/hud_375x780.png` 人工过眼（环线 + 圆点 + 圈数 1/2 正常，HUD 被 gutter 收窄后零遮挡、无溢出）。

### 5.6 S0–S3 状态机冒烟（`_smoke_s1s2.py`，13 PASS / 0 FAIL）
- `D_preview(listen) = 1620` 里程、`spanLen = 1020`、`L = 19254.5`（名义常量精确）。
- S0 `dist=D_preview+50` 隐藏 → S1 `dist=D_preview−20` 显示零文本 `◇`、`forecast` 类、`signKey=0:S1:pan:pen` → S2 `played=true` 两侧各含 `pan`/`pen` 且互异、等宽 ±1px、`signKey` 变化触发重绘 → S3 判后隐藏（`activeGate` 前移回落 S0 / `decide` 引用旧门命中 S3，两路径 `signs.hidden=true`）。
- `unheard` 门不补显（E9）；只读接口齐备；两圈同 commitT `line` 差 = L；`gate.id` 互异。

---

## 6. 需主理人裁决 / 转告 #5 的事项

### ⚠️ P0 · #5 的 H5 判据存在「`<span>` 标签名」子串误伤（可现实触发）
- `config.js:136` 有真实词对 `P("U03","pen","U04","pan")`（camp 地图），`allWords()` 含 `pan`。
- `#minimap` 的圈数载体是规格钉死的 `<span id="minimap-lap">`。若 #5 的 H5 按 `hud-qa-plan.md:128` / `hud-ux-spec.md:485` 字面「把 `mm.textContent` + **`mm.innerHTML`** + 后代属性值拼成 `s` 再 `s.includes(w)`」，则当题库抽到 pen/pan 门时，`s.includes("pan")` 会命中标签名 `<span>` 里的 `s·pan` → **误报 FAIL**，而小地图实际零答案泄漏。
- 实测：`_smoke_hud.py` 语义口径（`textContent` + 属性）命中 `[]`；字面口径（拼 `innerHTML`）命中 `['pan','pan']`，命中位置均为 `<span id="minimap-lap">` / `</span>`（`_diag_two_fails.py` 已定位）。
- **建议**（不自行折中、不改规格钉死的 `<span>`）：请主理人转告 quality-lead，H5 应**仅取 `mm.textContent` + 后代属性值**，或先把 `innerHTML` 的标签名/属性名剥离后再比对；对单字符 IPA（如 `i`/`p`）同理需做词边界匹配，避免命中固有 `id` / `minimap` / `lap` 等结构性字符串。产品侧保持规格 DOM 不变。

### ⚠️ P1 · `rg 'cseg-20261107' 全仓 0 命中` 的口径需收窄
- `design/*.md` / `音标大闯关/docs/*.md` 内保留 17 处 `cseg-20261107`，均为**历史盘查描述 / 回滚基线说明 / 冲突对照表旧表述**（如 `hud-impl-plan.md` 的「46 处 `?v=cseg-20261107 → hud-20261108` 整体替换」表格、`hud-qa-plan.md:289` 的回滚说明），改动会破坏文档史实性；且 S17/F8a/S1.7 均排除 `docs/` 且只扫 `.html/.js/.css`，不参与任何门控。
- `hud-qa-plan.md:151` 写「`rg -n 'cseg-20261107'` 全仓应为 0 命中」——若 #5 的 readiness check 按字面扫到 `design/` / `docs/`，会命中这些历史描述。建议 #5 把该检查**限定为产品/脚本文件**（`.html/.js/.css/.py/.mjs`，排除 `design/`、`docs/`），或明确豁免文档历史描述。产品/脚本文件实测残留 **0**。

### ℹ️ P2 · `js/minimap_model.test.mjs` 的口径说明
- 规格要求「先给 `minimapModel(view)` 写 Node 单测」，该文件是 TDD 必需交付物；用 `.mjs` 扩展名刻意使其**不被浏览器加载、不新增 `<script src>`、不进 `.html/.js/.css` tag 扫描**（46 计数不变）。
- 若团队把「不新建模块」严格解释为「`js/` 下不得新增任何文件」，可无损移到 `design/` 或 Temp（仅需调整 import 相对路径）；当前不影响任何门控。请主理人确认是否保留现位。

---

## 7. 遗留项与知识缺口

- **G12（Q4 已裁）**：`placeLaneSign()` 的 `t0 = gate.commitT − k·span` 与 `odo0 = gate.line − k·span·L` 差 `startOdo/L = 0.02`；本轮不改既有路牌位置口径，登记为遗留项，下轮统一。新增逻辑已全部用绝对 `odo` 派生。
- **知识缺口**：无。项目引擎为原生 ESM + Canvas 2D 静态站，所用 API（`getContext("2d")` / `setTransform` / `DOMPoint.matrixTransform` / `getBoundingClientRect` / `matchMedia`）均在实现时经真实 Chrome 冒烟验证，无臆造 API。
- 下一轮 3D 化「甲 · 立体书」不消费本轮方向稿；HUD 契约（`#minimap` DOM / `minimapModel` 纯函数 / `window.__rally` 只读 getter / S0–S3 事件）已为视角切换留好解耦点。

---

## 8. 回滚点与发布边界

- 回滚点：`C:/Users/86135/AppData/Local/Temp/hud_backup_20261108/`（13 文件 / 214,840 bytes，`manifest.txt` 记录大小 + sha256 前 16 位），副本只读、逐字节完好。
- 回滚方式：按 `manifest.txt` 的 relative path 从备份根 copy 回源根同名路径；回滚后缓存串回到 `cseg-20261107`，需重跑四套门控确认回到旧基线 110 项全绿。
- **未部署、未上线、未 commit**；本轮不触发任何发布动作。

---

## 9. 下一步建议（交 #5 quality-lead）

1. 先按 §6 的 P0/P1 修正 `verify_hud_spec.py` 的 H5 / readiness-check 判据口径（避免 `<span>` 误伤与文档历史描述误命中），再补 H1–H12。
2. 浏览器门控**串行**跑（§5.2 并发抖动披露）；H3 用 375×667 / 320×568 / 1280×800，375×780 为人工过眼尺寸（本轮已过）。
3. H7 定档后 `D_preview` 用 follow 1482 / listen 1620 里程；H9 quiz 断言 `mm.hidden === false`（本规格裁定）与 `#signs.hidden === true`；H10 `signKey` 以 `gate.id` 开头且含 `phase`。
4. 最终回归通过后由 team-lead 汇编 #6。

---

## 附录 · 测试证据路径

| 类别 | 路径 |
| --- | --- |
| Node 单测（产品内） | `音标拉力赛/js/minimap_model.test.mjs` |
| 临时冒烟 / 诊断（Temp，不进产品仓） | `_do_tag_bump.py` / `_tag_bump_scan.py` / `_spec_tag_lines.py` / `_final_integrity.py` / `_smoke_hud.py` / `_smoke_s1s2.py` / `_diag_u12.py` / `_diag_two_fails.py` / `_diag_s3.py` |
| 截图 | `C:/Users/86135/AppData/Local/Temp/hud_375x780.png` / `hud_320x568.png` / `hud_1280.png` |
| 回滚点 | `C:/Users/86135/AppData/Local/Temp/hud_backup_20261108/manifest.txt` |
