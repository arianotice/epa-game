# 音标拉力赛 · HUD 信息架构与 UX 规格
## 路牌预告 ＋ 右上角小地图（本轮 2D 落地）／3D 跟车视角（下一轮演进）

| 项 | 值 |
| --- | --- |
| 阶段 | CSEG-D1 · 设计规格（只读交付） |
| 作者 | design-strategist（文策渊） |
| 状态 | **已裁决（Q1–Q4 全部锁定，见第 7 节）**；A/B/C/D/E 与 H1–H12 为可直接照做/照断言的精确规格 |
| 裁决记录 | 主理人裁决 · 缓存串锁定 `hud-20261108` · `A11Y-TIER: Standard（本轮底线）→ Comprehensive（下一轮 3D 目标）` |
| 目标文件 | `音标拉力赛/design/hud-ux-spec.md`（本文件） |
| 主战场 | `音标拉力赛/`（原生 ESM + Canvas 2D 静态站，无构建、无 WebGL） |
| 目标平台 | 375px 触屏优先 + PC 浏览器 |
| 受众 | 小学生 / 初中生 ·「有趣味但不低幼」 |
| 上游拍板 | ①第三人称跟车视角（下一轮）②预告方式＝路牌 ③右上角小地图 ④本轮交付「3D 方向稿 + 本轮 2D HUD 落地」⑤**2D 全景下小地图是信息冗余，价值在提前锁死 HUD 位置与样式** |

> **硬约束自检**：本文件是唯一写入物。未改动 `js/`、`index.html`、`css/`、图片资产、验收脚本；未触碰 `js/data.js` / `js/ipa-display.js`；未重跑 `content_raw.json` / `build_data.py` / `augment_data.py`；未动 48 张精灵立绘与 48 张卡面；未部署、未上线、未 commit。`sym` 仅作存档/查表/去重/角标/alt，规格中**禁止**以 `displayIpa` 作键；U11=ɜr、U18=ɪr、U19=ɛr、U20=ʊr 的美式 IPA 唯一权威表保持原样。

---

## 0. 基线事实校准（必读 · 与任务简报的偏差）

动笔前逐行核对了 `js/`、`index.html`、`css/game.css`、`verify_cseg_ui.py`。有 **5 条与「从零新增」直觉相反的事实**，直接决定本轮工作量与规格写法，须先对齐：

### 0.1 「小地图」不是从零新建，而是**增强既有实现**
- `js/render.js:420-458` 已有 `drawMinimap(ctx, w, track, karts)`；`js/render.js:416` 有 `if (view.minimap !== false) drawMinimap(...)`。
- `js/main.js:987` 已传入 `minimap: mode !== "title"`。
- 现状小地图：**画在主画布 `#c` 上**（不是 DOM），固定 `mw=132, mh=86`，`x0 = w - 148, y0 = 16`；半透明底板 `rgba(255,250,240,.88)` + `#b99b6b` 描边；内容只有**赛道环线 + 3 个圆点**（玩家蓝 `#2f6f8f` r=4.5、对手 A 红 / B 绿 r=3.2）。
- **没有**：圈数、起终点、下一个闸门/分叉、任何文本、任何答案。
- **本轮性质因此是「改造 `drawMinimap` + 补 HUD 契约」，不是新增组件**。第 2.1.1 节给出载体决策。

### 0.2 「路牌」的真实身份是**两侧词牌（答案载体）**，不是中性指示牌
- `index.html:19-22` 的 `#signs > #sign-l / #sign-r`，由 `js/main.js:458-496 syncSigns()` 驱动、`js/main.js:498-521 placeLaneSign()` 投影定位。
- `paintLane()`（`main.js:439-444`）向两侧填入 `gate.left` / `gate.right` 的 **`word` + `/ipa/` + 紧松 label + sprite**，即**题目选项本身**。
- 因此「怎样不泄露答案」不是"路牌能不能写单词"，而是**「两侧必须永远对称、且不得指向 `correctLateral`／`spoken`」**。第 2.2.3 节逐项裁决。

### 0.3 `DIFFICULTY.preview` 是**已定义但从未被消费**的闲置常量
- `js/config.js:38 / :48` 定义 `preview: 4.2`（follow）/ `4.0`（listen）。
- 全仓 grep `preview` 仅命中：定义 2 处、`race.previewSteer()` 定义/调用（`main.js:943`、`race.js:777/838`，**与 `preview` 常量无关，是倒计时转向方法**）。
- `race.js:421-439 beginDecide()` 用的是硬编码 `lead = span*L*0.55 + 360 + speedNow*0.62`，**没有读 `diff.preview`**。
- **本轮正好把它启用为「预告提前秒数」**（第 2.2.2 节），无需新增常量、无需改判定核心。

### 0.4 两套坐标系并存，两圈 `commitT` 相同
- 绝对里程：`race.js:83` `g.line = player.startOdo + g.lineT * L`；`buildGates`（`config.js:264-299`）产出 `lineT = lap + commitT` → `0.24 / 0.68 / 1.24 / 1.68`，`id = 0..3`（**含 lap，天然唯一**）。
- 相对参数：`t = odo / L % 1`，只用于 `track.sample(t)` / `pointAt`。`flareAt()`（`render.js:43-57`）与 `placeLaneSign()` 的 `t0/t1` 用 **`gate.commitT`**（圈内相对，`0.24/0.68`）；`branchLateral()`（`race.js:336-358`）用**绝对 `odo`**。
- `main.js:969-971` 已按 `g.lap === lapNow` 过滤 `visibleGates`，解决"4 个门画在 2 个位置"。**路牌 DOM 未走该过滤，靠 `activeGate()` 只返回一个门来去重**。
- 现状 `signKey = ${gate.id}:...`（`main.js:475`）已用 `id`，**现状安全**；本轮须把它写成硬约束（第 2.2.5 节）。

### 0.5 冗余性声明（**不假装玩法刚需**）
用户与主理人已点明：**「看不到整条赛道才需要预告」这个前提只在第三人称跟车视角下成立**。当前 2D 是全景俯视伪 3D（`render.js:218-233` 把整条 `track.samples` 环线一次画全，`anchor=0.52`），玩家**本就看得见分叉口、看得见对手、看得见自己在哪**。

> **本轮小地图在信息上是冗余的。** 它不提供任何当前主画面缺失的决策信息，因而不是玩法刚需，也不得被包装成"提升听辨准确率"的功能。它的价值**仅**在于：①提前锁死右上角 HUD 位置、尺寸、z-index、显隐契约与响应式规则；②定义一份与渲染器解耦的 `minimapModel` 数据接口与事件契约；③让下一轮 3D 跟车视角可以**直接实现**而不必重新做 HUD 设计决策。3D 轮它才升级为「必要导航」。

**支柱漂移红线**：不得因为"小地图看起来该有点用"，就把「下一个分叉的正确侧」「听到的词」「答案高亮」画上去——那会直接破坏「听音选车道」这一核心支柱。

### 0.6 本轮范围
| 做 | 不做 |
| --- | --- |
| 小地图：DOM 化契约、响应式、避让、显隐、信息边界、数据接口 | 真 3D / WebGL / 透视投影 / 视锥裁剪 |
| 路牌：两级预告状态机、阈值、信息边界、两圈防串、冻结行为 | 改 `buildGates` / `judge` / `hitsLane` / 计分 / 解锁口径 |
| 3D 方向稿：HUD 职责升级、可读性规则、预留接口 | 改 `config.js` 的 `TUNING` / `DIFFICULTY` 数值 |
| QA 断言建议、风险清单 | 改 `data.js` / `ipa-display.js` / 资产 / 构建管线 / 存档结构 |

**可访问性分级（本轮锁定 · 显式引用）**：`A11Y-TIER: Standard（本轮底线）→ Comprehensive（下一轮 3D 目标）`。
- **本轮 Standard 底线**：`#minimap` 与路牌 `aria-hidden="true"` + `pointer-events:none`（纯视觉冗余，不承载唯一信息）；`prefers-reduced-motion` 降级；`#live` 的 `aria-live="polite"` 播报保持；键盘 / 触屏输入不受 HUD 影响；羊皮纸底板上文字对比 ≥ 4.5:1。
- **下一轮 Comprehensive 目标**：3D 跟车视角下补齐完整无障碍通道（含空间音频 / 方位播报、可配置字号与高对比模式）。
- **不纳入本轮（独立议题）**：为听障玩家提供「视觉冗余提示」（把听到的词 / 音标可视化）会把「听音选车道」核心玩法口径从「听觉判别」改成「视觉匹配」，属**玩法变更**。登记为「下一轮需用户与设计侧共同拍板的独立议题」，不得借本轮 HUD 落地夹带。

**右上角同位置角色切换（主理人裁定 · 本轮锁定）**：`#route-map`（`main.js:256 ui.routeMap.hidden = next !== "title"`，仅标题页）与比赛小地图（`main.js:987 minimap: mode !== "title"`，仅非标题页）**互斥**，右上角**不存在三元素叠压**。保持「**标题页 = a1 四区大地图入口 ／ 比赛中 = 该轮闭环小地图**」的同位置角色切换；`#route-map` 保留不动、**不新增第三层**。本规格 2.1.4 / 2.1.6 原本即按互斥书写，无需改写；2.1.3 的 `#hud padding-right` gutter 解 375px 拥挤方案继续有效。D 节 H4 中 `#route-map（可见时）` 因互斥恒不可见，该子项为空断言，保留不改。

---

## 1. 数据契约（防泄露白名单 · 跨轮通用）

### 1.1 门对象字段分级（`config.js:279-295`）

| 域 | 字段 | 小地图 | 路牌 S1（预告） | 路牌 S2（选项） | HUD 文本 |
| --- | --- | --- | --- | --- | --- |
| **答案域（绝密）** | `spoken`、`other`（作为答案判定）、`correctLateral`、`hit` | ❌ 禁 | ❌ 禁 | ❌ 禁 | 判定后结果页可列 |
| **题干域（对称）** | `left`、`right`（`word`/`ipa`/`label`/`sprite`/`color`/`length`/`tone`） | ❌ 禁 | ❌ 禁 | ✅ **两侧同时、等量、同样式** | ❌ 禁 |
| **几何域（中性）** | `id`、`lap`、`commitT`、`lineT`、`line` | ✅ 可用 | ✅ 可用 | ✅ 可用 | `lap` → 圈数 |
| **状态域** | `played`、`judged`、`replayed`、`unheard` | ✅ 可用 | ✅ 可用 | ✅ 可用 | `correct` 计数 |
| **元信息** | `qType`、`pairKey` | ❌ 禁 | ❌ 禁 | ❌ 禁 | ❌ 禁 |

> **单向铁律**：`correctLateral` 与 `spoken` 只允许出现在 `audio.playWord()`（`race.js:436`）与 `judge()`（`race.js:213-262`）。**任何 HUD 生成路径（DOM `innerHTML`、canvas `fillText`、CSS `data-*`、`alt`、`aria-label`）都不得接触它们。**

### 1.2 `minimapModel` 数据接口（本轮就要定义，3D 轮直接复用）

建议挂在 `window.__rally.minimapModel()`（`main.js:996-1013` 的导出对象扩展），或作为 `render(view)` 的 `view.minimapData`。**纯函数、零副作用、不写盘**。

```js
minimapModel() => {
  // 几何域
  trackPath : Array<{x:number, y:number}>,   // 直接引用 track.samples，只读
  length    : number,                        // = track.length ≈ 19254.5 里程单位
  startOdo  : number,                        // = player.startOdo
  // 参与者（只给运动学，不给答案）
  karts     : Array<{ id:string, kind:'player'|'rival', odo:number, lateral:number }>,
  // 进度
  lap        : number,  laps: number,        // 0-based lap / TUNING.laps
  progress   : number,                       // (player.odo - startOdo) / (laps * L)，0..1
  // 下一个分叉（中性几何点，严禁指向正确侧）
  nextGate  : null | {
    id        : number,                      // 0..3，含 lap，唯一键
    lap       : number,
    line      : number,                      // 绝对里程
    distance  : number,                      // = line - player.odo，里程单位
    secondsTo : number,                      // = distance / diff.speed，秒（名义速度）
  },
  // 渲染元信息
  phase     : 'S0'|'S1'|'S2'|'S3',           // 见 2.2.1
  reduced   : boolean,
}
```

**禁止字段（QA 逐键扫描）**：`spoken`、`other`、`correctLateral`、`left`、`right`、`pairKey`、`qType`、`options`、`displayIpa`、`sym`（作为显示）、`hit`、`answer`、`correct`、`word`、`ipa`、`label`。
**禁止属性**：`data-lane` / `data-side` / `data-correct` / `data-answer` / `data-word` / `data-ipa`。

### 1.3 事件契约（本轮即使只由 2D 侧触发也要发）

自定义事件挂 `document`，payload **一律不含答案域**：

| 事件 | 触发时机 | payload |
| --- | --- | --- |
| `rally:gate-preview` | 进入 S1（T0） | `{gateId, lap, distance, secondsTo}` |
| `rally:gate-played` | `g.played` 置位（T1） | `{gateId, lap, distance}` |
| `rally:gate-judged` | `judge()` 后（T3） | `{gateId, lap}` —— **不含 `hit`/`spoken`** |
| `rally:lap` | `state.lap` 自增（`race.js:611-617`） | `{lap, laps}` |

用途：3D 轮的 HUD / 世界空间预告牌 / 音画对齐可订阅，无需再解析 `race.state.gates`。

### 1.4 坐标系契约（本轮锁死）
1. **唯一跨轮坐标 = 绝对里程 `odo`**（`g.line`、`player.odo`、`player.startOdo`）。相对 `t = (odo / L) % 1` **只允许**由 `odo` 派生，禁止反向用 `commitT` 推绝对位置。
2. 小地图环线点位、进度弧、圈数一律用 `odo / (laps * L)`，**不用 `t`**（`t` 在两圈会重复）。
3. `nextGate` 取 `race.activeGate()` 的返回（`race.js:164-175`，按 `dist = g.line - player.odo` 最小正值），**不遍历全量 gates**。
4. 单位：里程单位（`L ≈ 19254.5`，约 1 世界像素量级）；速度 `diff.speed` 单位 = 里程/秒；时间 = 秒。

---

## 2. A. 本轮 2D 落地规格

### 2.1 右上角小地图

#### 2.1.1 载体决策（**裁决项 Q1**，默认推荐 A）

| 方案 | 说明 | 优点 | 代价 |
| --- | --- | --- | --- |
| **A（推荐）DOM 化** | 新增 `<div id="minimap" aria-hidden="true">` + 内嵌 `<canvas id="minimap-c">` + `<span id="minimap-lap">`，`position:fixed`；把 `drawMinimap()` 迁到内嵌 canvas 上绘制 | 响应式 / z-index / `pointer-events` / 半透明底板 / 显隐全部可用 CSS 精确表达；QA 可直接做 DOM 存在性、rect 不重叠、不含答案文本断言；3D 轮零改动复用 | 需改 `index.html`、`css/game.css`、`render.js`、`main.js` 四处（#3/#4 工作量） |
| B（备选）Canvas 原地增强 | 保留画在 `#c` 上，扩充 `drawMinimap()` 参数并加圈数/分叉标记 | 改动最小，不动 HTML/CSS | `#c` 无 z-index 位于最底，会被 `#hud`(5)/`#banner`(6)/`#signs`(4) 覆盖；**375px 避让只能靠 JS 算**；QA 无法做 DOM 断言，只能读 `minimapModel` + 像素元数据 |

> 本文**按方案 A 给出完整规格**；若裁决选 B，第 2.1.3/2.1.4 节的 CSS 变量需改写为 `main.js` 内 `resize()` 中的 JS 布局计算，且 D 节 H1/H4 断言改为 `window.__rally.minimapRect()` 供断言读取。

#### 2.1.2 显示什么 / **不显示什么**

| 显示（本轮） | 规格 |
| --- | --- |
| 赛道环线 | `track.samples` 投影，沿用 `drawMinimap()` 的等比缩放 `sc = min(sx, sy)`，描边 `#6b4a32` 3px |
| 玩家位置 | 蓝 `#2f6f8f` 实心圆 r=4.5（PC）/ r=3.5（触屏） |
| 对手位置 | A 红 `#a33b3b` / B 绿 `#3d6b45`，r=3.2 / 2.6 |
| 起终点 | 单个中性旗形/菱形标记，位置 `track.sample(0.012)`（`render.js:327` 同源），**单色 `--gold-deep`** |
| 圈数 | 极简文本 `1/2`、`2/2`，字号 11px，位于底板内右下角；**不得重复「听对 N」**（`#gates` 已有，防认知过载） |
| 进度弧 | 沿环线的高亮弧，长度 = `minimapModel.progress`，色 `--gold` |
| 下一个分叉/闸门 | **中性菱形点**（单色 `--gold-deep`，无左右指向、无箭头、无高亮侧），位置 `track.sample((nextGate.line / L) % 1)`；S1 点亮、S2 保持、S3/无门熄灭 |

| **不显示（硬性）** | 理由 |
| --- | --- |
| `spoken.word` / `other.word` / `left.word` / `right.word` | 答案泄露 |
| 任何 IPA 串（`/i/`、`/ɪ/`、`ɜr` 等）、`displayIpa`、`sym` 作为可见文本 | 答案泄露 + 违反 `sym` 用途约束 |
| `gate.left.color` / `gate.right.color` 作为**左右分叉着色** | 易被误读为左右指向；本轮统一中性单色 |
| 指向 `correctLateral` 的箭头 / 高亮 / 勾选 / 单侧放大 | 直接泄露答案 |
| 「正确答案在左」「往右」等方位提示 | 直接泄露答案 |
| 额外惩罚题（`state.quiz`）的题目、选项、词 | 与 `#quiz` 双份信息叠加 |
| 宝石 / 石头 / 护身 / combo / 名次数字 | 与 `#hud`、`#gems`、`#shields` 重复，认知过载 |

#### 2.1.3 尺寸与响应式（具体 px / 断点）

CSS 变量（写在 `:root` / 覆盖写在媒体查询内）：

| 变量 | PC（> 640px） | 触屏（≤ 640px，含 375px） | 说明 |
| --- | --- | --- | --- |
| `--mm-w` | `160px` | `min(96px, 26vw)` | 375px→96px；320px→83px |
| `--mm-h` | `104px` | `min(64px, 17vw)` | 375px→64px；320px→54px |
| `--mm-right` | `16px` | `10px` | 右外边距 |
| `--mm-top` | `16px` | `calc(8px + env(safe-area-inset-top))` | 刘海/状态栏安全区 |
| `--mm-right-gutter` | `184px` | `120px` | `= --mm-w(PC160/触屏96) + 24px`，喂给 `#hud` 的 `padding-right` |

断点：`@media (max-width: 640px)`（与 `css/game.css:353` 现有断点**对齐，不新增断点**）。

```
#minimap {
  position: fixed; z-index: 5;
  right: var(--mm-right); top: var(--mm-top);
  width: var(--mm-w); height: var(--mm-h);
  pointer-events: none;
  border-radius: 12px; border: 2px solid var(--line);
  background: var(--card);              /* rgba(255,250,240,.94) */
  box-shadow: var(--shadow);
  overflow: hidden;
}
#minimap-c { display:block; width:100%; height:100%; }
#hud { padding-right: var(--mm-right-gutter); }   /* 关键避让，见 2.1.4 */
```

- 内嵌 canvas 按 `dpr = min(2, devicePixelRatio)` 设置 `width/height` 位图尺寸，绘制前 `ctx.setTransform(dpr,0,0,dpr,0,0)`，与 `main.js:731-737 resize()` 同源。
- **375px 硬约束**：`mm.getBoundingClientRect()` 必须满足 `left ≥ 0 && right ≤ 375 && top ≥ 0 && bottom < 667`，且 `mm.width ≤ 0.30 × 375 = 112.5px`。

#### 2.1.4 避让与 z-index（完整层级表）

现有层级（读自 `css/game.css`）：`#c` 无 z-index（DOM 首位，最底）→ `#tags`/`#signs` **4** → `#hud` **5** → `#route-map`/`#banner`/`#fork-count` **6** → `#touch` **7** → `.panel`/`.count` **8** → `#how` **9** → `#how-panel` **10** → `#confetti` **11** → `#cheer`/`#shop-panel` **12**。

| 元素 | z-index | 与小地图关系与处理 |
| --- | --- | --- |
| `#minimap`（新增） | **5** | 与 `#hud` 同层；**DOM 顺序置于 `#hud` 之后**，确保同层时在其上 |
| `#hud` | 5 | **`padding-right: var(--mm-right-gutter)`** → HUD 所有 chip/按钮的 content box 右边界被收窄，几何上不可能与小地图水平相交（即使 `.hud-row` 在 375px 换 2~3 行，padding 对每一行都生效） |
| `#btn-mute` / `#btn-pause` / `#combo` | 5（继承） | 被 `.spacer` 推到右侧，正是 375px 下与小地图原位置冲突的元凶；由 HUD gutter 解决 |
| `#progress` | 5 | 顶部进度条在 HUD 内，同样受 gutter 收窄 |
| `#banner` | 6 | PC：居中 `max-width:640px`，x 不触右上角 ✓；**窄屏需下移**：`@media(max-width:640px){ #banner{ top: calc(var(--mm-h) + 20px); } }`，保证 `banner.top ≥ minimap.bottom + 12px`（现 `top:78px` 与 375px 下 `mm.bottom ≈ 72px` 仅 6px 间隙，风险高） |
| `#route-map` | 6 | **标题页专属**（`main.js:256 ui.routeMap.hidden = next !== "title"`），176×118 / `top:16 right:16`；与小地图互斥（title 不显示小地图）。**保持不动**，只作为「右上角锚点一致性」的视觉参照 |
| `#signs` / `#tags` | 4 | 路牌由 `placeLaneSign()` 投影，可能飘入右上角；z=5 的小地图会盖住它 → **须在 `placeLaneSign()` 增加小地图矩形避让裁剪**：若牌中心落入 `mm.rect` 外扩 8px 则 `el.style.visibility = "hidden"`（见 2.2.4） |
| `.panel`（quiz/results/pause/title/teach/board） | 8 | 高于小地图；**仅** `boardOpen` / `shopOpen` / `results` / `teach` 等显式隐藏小地图；**`quiz` 不隐藏**——靠 z-index 层叠（`#quiz` z=8 > `#minimap` z=5），**显示但冻结**（与 `paused` 对称，详见 2.1.6）。小地图字段白名单已锁死不含 `correctLateral` / `spoken` / `left` / `right`，显示不泄答案（真正泄答案的是 `#signs`，Q2 已裁隐藏）；且 quiz 属「比赛中」，隐藏会闪烁、违背「进入比赛页面右上角出现该轮比赛的小地图」 |
| `#shop-panel` | 12 | 同上，显式隐藏 |
| `#cheer` / `#confetti` | 12 / 11 | 全屏 `pointer-events:none` 装饰，透明覆盖，允许叠在小地图上 |
| `#touch` | 7 | 底部，不相交 |

> **`#hud` 的 gutter 是 375px 避让的核心机制**：不需要 JS 动态测量 HUD 高度，也不随 `.hud-row` 换行数变化而失效。代价是窄屏 HUD 可用宽度从 351px 收窄到 `375 - 12 - 120 = 243px`，`.hud-row` 会多换 1 行——可接受（HUD 是信息条，不是操作区；操作区在 `#touch`）。

#### 2.1.5 `pointer-events` 与半透明底板
- **必须 `pointer-events: none`**，且内嵌 canvas / `#minimap-lap` 继承 `none`。理由：375px 下小地图紧邻 `#btn-pause`（≥72px）与 `#btn-mute`（42px），若可点击会吃掉暂停/静音触屏事件；小地图**纯展示、零交互**（本轮与 3D 轮都不做点击缩放/拖拽）。
- **半透明底板必须有**：`background: var(--card)`（`rgba(255,250,240,.94)`，alpha ≥ 0.82），加 `2px solid var(--line)` 描边 + `--shadow`。理由：主画面是动态羊皮纸赛道 + 卡丁车 + 粒子，无底板时 3px 环线与圆点在 `#e7d3a8` 上对比不足；沿用现有 `drawMinimap()` 的 `.88` 底板设计并提高到 `.94`。
- `backdrop-filter` **不强制**（移动端性能），`prefers-reduced-motion` 下不做任何闪烁/脉动动画。

#### 2.1.6 显隐时机矩阵（**精确、可断言**）

现状 `minimap: mode !== "title"` 会在 `teach / results / quiz / board / shop` 下仍绘制，须改为下表的显式判定：

```
visible = (mode ∈ {countdown, racing, paused, quiz})
          && !boardOpen && !shopOpen
          && !!race
```
（读 `window.__rally.mode` / `.boardOpen` / `.shopOpen` / `.race`；`boardOpen`/`shopOpen` 打开时 `mode` **仍是 `racing`**，见 `main.js:811-821`、`main.js:874-889`，**不能只看 mode**。）

| 阶段 | `mode` | `#hud` | 小地图 | 路牌 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 标题页 | `title` | hidden | **隐藏** | 隐藏 | 显示 `#route-map`；与现状 `minimap:false` 一致 |
| 玩法说明面板展开 | `title`（`ui.title.hidden=true`） | hidden | **隐藏** | 隐藏 | `#how-panel` z=10 遮挡，仍显式隐藏 |
| 教学页「这两个音不要混」 | `teach` | hidden | **隐藏**（现状会画，本轮修正） | 隐藏 | 教学页无导航需求 |
| 倒计时 | `countdown` | 显示 | **显示**（静态：三车在起点、圈数 `1/2`、无 nextGate 或中性标记） | 隐藏 | `#panel-count` z=8 `pointer-events:none`，居中数字不触右上角 |
| **比赛中** | `racing` | 显示 | **显示（主场景）** | 按 2.2 状态机 | 核心场景 |
| quiz 冻结 | `quiz` | 显示 | **显示但冻结**（`karts[].odo` 不推进、`simTime` 不增） | **隐藏**（见 2.2.6，裁决 Q2） | `frozen` 见 `main.js:938` |
| 暂停 | `paused` | 显示 | **显示但冻结** | 冻结保持（不重绘、不重播） | |
| 结果页 | `results` | 显示 | **隐藏** | 隐藏 | 比赛已结束，导航信息无意义；`#panel-results` z=8 |
| 排行榜打开 | `racing` + `boardOpen=true` | 显示 | **隐藏** | 隐藏 | `mode` 未变，必须查 `boardOpen` |
| 商店打开（比赛中） | `racing` + `shopOpen=true` | 显示 | **隐藏** | 隐藏 | 同上 |
| 商店打开（标题页） | `title` + `shopOpen=true` | hidden | **隐藏** | 隐藏 | `#how-shop` 不改 `mode` |

> `main.js:938 frozen` 只冻结 `simTime` 与 `race.update()`；`render()` 与 `syncSigns()` 在 `mode !== "title" && !== "teach"` 时**每帧仍执行**（`main.js:990`）。因此显隐**必须**由上面的 `visible` 显式控制，不能依赖 `minimap: mode !== "title"` 或「画面冻结了就不会变」。

---

### 2.2 路牌预告

#### 2.2.1 两级信息 + 单一 DOM 载体（状态机）

**载体**：复用 `#signs > #sign-l / #sign-r`（`z-index:4`、`pointer-events:none`），由 `syncSigns()`（`main.js:458-496`）统一驱动，**不新增 DOM 元素**。仅把 `placeLaneSign()`（`main.js:498-521`）的 `span` 参数化。

| 状态 | 进入条件 | 两块牌内容 | 两块牌位置（`placeLaneSign` 的 `spanEff`） | `#signs.hidden` |
| --- | --- | --- | --- | --- |
| **S0** 无门临近 | `!act` 或 `dist > D_preview` | — | — | `true` |
| **S1 中性预告**（T0） | `act && !act.gate.played && dist ≤ D_preview` | **零文本**：完全对称的中性外壳（统一 `var(--card)` 底 + `var(--line)` 描边，去掉 `.is-long/.is-short`），内容为几何符号 `◇`／`↖ ↗`，**无 word / 无 IPA / 无 label / 无 sprite / 无左右色差 / 无先后出现差异** | `spanEff = D_preview / L` | `false` |
| **S2 选项路牌**（T1→T2） | `act.gate.played && !act.gate.judged && dist ≤ D_preview` | 现有 `paintLane()`：两侧同时、等量填入 `gate.left` / `gate.right` 的 `word` + `/ipa/` + 紧松 label | `spanEff = race.state.span`（现状值，保留 `0.66 / 0.34 / 0.36` 系数） | `false` |
| **S3 已判定** | `act.gate.judged` 或 `unheard` | — | — | `true` |

- S1→S2 的切换由 `g.played` 边沿触发（`beginDecide()` `race.js:434-437`）；切换时 `signKey` 必须变化（把 `phase` 纳入 key，见 2.2.5），以触发 `paintLane()` 重绘与 `open` 动画重置。
- S1/S2 两块牌**始终同帧显示、同尺寸、同不透明度、同动画时长**；`open` 类必须同时加到两块牌（`main.js:486-492` 现状已同步，保持）。
- `dist ≤ D_preview` 是**距离上限保险**（防跨门/跨圈提前显示）；实际 S2 的进入由 `played` 决定，而 `played` 只在 `dist ≤ lead` 时置位，且 `lead < D_preview`，故上限恒满足。

#### 2.2.2 阈值（公式标变量与单位 · 两档速度各给里程与秒）

记号：`L = track.length ≈ 19254.5`（里程单位）；`v = diff.speed`（里程/秒）；`f = diff.fork`（秒）；`p = diff.preview`（秒，本轮启用）；`span = forkSpan(diff, L) = f·v / L`（`config.js:301-303`，无量纲）；`span·L = f·v`（里程）。

| 阈值 | 公式 | follow（`v=260, f=3.6, p=4.2`） | listen（`v=300, f=3.4, p=4.0`） |
| --- | --- | --- | --- |
| 分叉展开起点 | `span·L = f·v` | **936** 里程 = 3.60 s | **1020** 里程 = 3.40 s |
| **`D_preview`（T0 / S1 上限）** | **`span·L + 0.5·p·v`** | **1482** 里程 = **5.70 s** | **1620** 里程 = **5.40 s** |
| `lead`（T1 播音，`beginDecide`） | `0.55·span·L + 360 + 0.62·speedNow` | **1036** 里程 ≈ 3.98 s | **1107** 里程 ≈ 3.69 s |
| S2 路牌世界定位 | `gate.line − 0.36·span·L` | 门线前 **337** 里程 ≈ 1.30 s | 门线前 **367** 里程 ≈ 1.22 s |
| S1 路牌世界定位 | `gate.line − 0.36·D_preview` | 门线前 **534** 里程 ≈ 2.05 s | 门线前 **583** 里程 ≈ 1.94 s |
| 判定 | `dist = 0`（`player.odo ≥ g.line`） | 0 | 0 |

**单调时序（两档均成立）**：
`D_preview (1482/1620) > lead (1036/1107) > S1 定位 (534/583) > S2 定位 (337/367) > 0`
→ 中性预告比播音早 **446 里程 / 1.72 s**（follow）与 **513 里程 / 1.71 s**（listen），两档提前量刻意对齐约 1.7 s，不制造难度档间的预告主导策略。

**为什么 `D_preview` 不直接等于 `p·v`**：`p·v` = 1092 / 1200 里程，仅比 `lead`（1036/1107）早 56 / 93 里程（0.22 / 0.31 s），玩家几乎无感知。故取「分叉展开起点再往前半个 preview 秒」，得约 1.7 s 有效预警窗口，同时**复用 `preview` 与 `span` 两个既有常量，不新增参数**。

**阈值用名义速度 `diff.speed`，不用 `speedNow()`**：`speedNow()`（`race.js:182-188`）受 `SLOW.mul=0.54` / `BOOST.mul=1.48` / `TURBO.mul=1.92` 影响，若预告阈值跟着波动，加速/减速时窗口忽长忽短，玩家无法形成稳定预期（伤害胜任感）。`beginDecide()` 的 `lead` 保持原样不动（不改判定核心），只让**HUD 预告**用常量。QA H7 因此可用固定数值断言。

#### 2.2.3 信息量边界与**不泄露答案的论证**

| 元素 | S1 预告态 | S2 选项态 | 裁决理由 |
| --- | --- | --- | --- |
| **单词 `word`** | ❌ 禁 | ✅ 两侧同时、等量 | 答案是「你听到的那个词」，只在 `audio.playWord(g.spoken.word)` 时经**听觉**给出；两侧词是对称候选项，视觉层信息量恒等，不指向答案 |
| **IPA（`/ipa/`、`displayIpa`）** | ❌ 禁 | ✅ 两侧同时、等量 | 同上；且 `choiceHtml()` 用的是 `PHONEMES[unit].ipa`（稳定英式键），**禁止**用 `displayIpa` 作键或作为可见文本单独标注 |
| **音标类别 `label`（紧音/松音/清音…）** | ❌ 禁 | ✅ 两侧同时、等量 | 类别是题干的对称分组键；两侧互异是**题目区分度**所需，不是答案指向 |
| **左右箭头** | ✅ 中性几何箭头 `↖ ↗`，**两块牌同形同色同时出现**，仅表示「此处有左右两条车道」 | ✅ 同左 | 只要**不指向 `correctLateral`**、不单侧放大/发光/变色/先出现，就不泄露；`↖` 与 `↗` 成对出现属于几何指示，允许 |
| **单侧高亮 / 勾选 / 「正确答案」/ `.ok` `.bad`** | ❌ 禁 | ❌ **绝对禁止** | 直接泄露 `correctLateral` |
| **`spoken` 单独标注 / `correctLateral` 文本化** | ❌ 禁 | ❌ 禁 | 见 1.1 单向铁律 |
| **`sprite` 精灵图** | ❌ 禁（避免 S1 提前暴露音素身份） | ✅ 两侧同时（`choiceHtml()` 现状） | 精灵与 unit 一一对应，S1 出现等于提前给题 |
| **`.is-long` / `.is-short` 蓝红着色** | ❌ 禁（两侧统一中性） | ✅ 两侧各自（现状） | S1 若上色等于提前给出两音素类别；S2 的左右配色由 `gate.left/right` 决定，而答案由 `spoken` 决定，二者独立 |

> **证明（听觉唯一通道）**：判定式是 `hitsLane(player.lateral, gate.correctLateral)`（`race.js:215` / `config.js:305-308`），而 `correctLateral` 由 `buildGates` 的 `onRight` 随机决定（`config.js:278,290`），`spoken` 由 `sayFirst` 随机决定（`config.js:276`）。玩家可获得的唯一映射线索是**音频 `spoken.word` 与两侧 `word` 的匹配**。视觉层（小地图、路牌、HUD）只接触 `id/lap/line`（几何）、`left/right`（对称题干）、`played/judged`（状态机）。**`spoken` 与 `correctLateral` 从不进入任何 DOM/canvas 文本生成路径 → 视觉不可能泄露答案。**
>
> **补充（3D 轮同样成立）**：下一轮把路牌变成世界空间物体，只改变「距离/透视」，不改变信息集合。只要坚持两侧对称 + 中性预告，信息边界不变。

#### 2.2.4 与 `placeLaneSign()` / `preview` / `flareAt()` 的关系

| 现有件 | 本轮处置 | 具体改动 |
| --- | --- | --- |
| `placeLaneSign()` `main.js:498-521` | **改造（复用全部投影逻辑，仅参数化）** | 签名改 `placeLaneSign(el, matrix, gate, side, spanEff)`：把 `const span = race.state.span` 换成入参 `spanEff`（S1 传 `D_preview/L`，S2 传 `race.state.span`）。`0.66 / 0.34 / 0.36` 三个系数、`project()` 调用、`--lane` 角度、`visible` 屏幕裁剪**全部保留** |
| 同上 · 坐标一致性 | **建议修正（可选，裁决 Q4）** | 现 `t0 = gate.commitT − k·span`（相对）与 `odo0 = gate.line − k·span·L`（绝对）差 `startOdo/L = 0.02`（≈385 里程），因为 `commitT` 未含 `startOdo` 偏移。本轮新增逻辑一律用 **`t_i = (odo_i / L) % 1`** 从绝对 odo 派生；若 #4 顺带统一旧代码，需 QA 补一条路牌投影位置回归断言 |
| 同上 · 避让裁剪 | **新增** | 在 `el.style.visibility` 判定中追加：牌中心 `(c.x, c.y)` 落入 `#minimap` 的 `getBoundingClientRect()` 外扩 8px 则强制 `hidden`（防 z=5 小地图盖住 z=4 路牌） |
| `DIFFICULTY.preview` `config.js:38/48` | **启用（复用闲置常量，不改数值）** | 作为 `D_preview = span·L + 0.5·preview·speed` 的秒数基准；3D 轮沿用同一常量，不新增参数 |
| `flareAt()` `render.js:43-57` | **不动** | 它驱动赛道分叉的几何张开与 `leftColor/rightColor` 着色，属主画面渲染；`visibleGates` 已按 lap 过滤（`main.js:969-971`）。路牌预告与之**解耦**，不复用 |
| `branchLateral()` `race.js:336-358` | **不动，只消费** | S1 的 `odo < gate.line − span·L` → 返回 `f=0`，两块预告牌自然并立于中线两侧约 `±0.502·roadHalf`（≈±261 里程），符合「预告牌还没分开」的语义；**不强制左右分离** |
| `syncSigns()` `main.js:458-496` | **改造** | 用 2.2.1 的 S0–S3 状态机替换现 `show = !!(deciding \|\| (act && act.gate.played && !act.gate.judged))`；S1 调 `paintForecast()`（中性外壳），S2 调现 `paintLane()`；`signKey` 纳入 phase，见下 |
| `render()` 的 `minimap` 参数 `main.js:987` | **改造** | 由 `mode !== "title"` 改为 2.1.6 的 `visible` 表达式；`drawMinimap()` 迁至 DOM 内嵌 canvas（方案 A）或原地扩参（方案 B） |

#### 2.2.5 两圈同 `commitT` 时如何避免路牌重复 / 错位

**机制风险**：两圈 `commitT` 都是 `0.24 / 0.68`；`flareAt()` 与 `placeLaneSign()` 的 `t0/t1` 用 `commitT`（相对），`branchLateral()` 用绝对 `odo`。若用 `commitT` / `lineT % 1` 作状态 key，或遍历全量 `gates` 生成路牌，第 2 圈会复用第 1 圈状态 → **重复出现 / 不出现 / 错位**。

**硬约束（5 条）**：
1. **状态 key 唯一用 `gate.id`**（`0..3`，含 lap）。`signKey` 改为 `` `${gate.id}:${phase}:${gate.left.word}:${gate.right.word}` ``（`main.js:475`）。**禁止** `commitT` / `lineT % 1` / `pairKey` 作 key。
2. **只消费 `race.activeGate()` 返回的唯一门**（`race.js:164-175`，按 `dist = g.line − player.odo` 取最小正值的未判定门）。禁止遍历 `state.gates` 批量生成 DOM 牌；`#signs` 内 `.sign` 元素恒为 2 个。
3. **小地图 `nextGate` 按 `race.state.lap` 过滤**，与 `visibleGates`（`main.js:971`）同源；`nextGate.id` 必须属于当前 lap。
4. **`t_i = (odo_i / L) % 1` 统一由绝对 odo 派生**；`odo_i = gate.line − k_i·spanEff·L`。因为 `gate.line` 含 `lap·L`，取模后自然得到正确的圈内相对位置，两圈不会串。
5. **跨圈不重置状态**：`beginCountdown()` 的 `signKey = ""`（`main.js:387`）只在开赛时重置；跨圈靠 `gate.id` 变化自然触发重绘，**不要**在 `rally:lap` 时清空 `signKey`（否则第 2 圈首门可能漏一次 `open` 动画，但不会漏显示）。

**验证口径**：两圈同 `commitT` 的门 `line` 相差恰好 `L`（`0.24→1.24`、`0.68→1.68`）；`branchLateral` 在两圈对同一相对 `odo` 算出相同 `f`（`race.js:341-345` 的 `start/full/end` 都相对各自 `g.line`），故横向偏移一致 → **位置不串**。QA H10。

#### 2.2.6 quiz 冻结时路牌状态（**裁决项 Q2**，默认推荐「隐藏」）

现状：`main.js:459` 把 `mode === "quiz"` 列入 `activeGate()` 计算条件，且 `frame()` 在 quiz 时仍调用 `syncSigns()`（`main.js:990`）→ **quiz 期间路牌保持显示且静止**。

**推荐规格（隐藏）**：quiz 冻结时 `#signs.hidden = true`，理由：
- `#quiz` 是 `.panel`（z=8，`left:50% top:46% width:min(640, 100%−24px)`），375px 下几乎全宽，会覆盖右上角与路牌区域；
- `ipa` / `type` 题会在 `#quiz-prompt` 写出 `词：<b>${q.spoken.word}</b>`（`main.js:774`），而 `#signs` 仍显示分叉门两侧词 —— **两套题目同屏**，可能构成意外提示，也加重小学生认知负荷；
- 隐藏后回到 `racing`，`played && !judged` 仍为真，路牌按原状态**无缝重现**，不打断心流。

**若裁决「冻结保持」**，则必须同时满足：牌 `textContent` 与进 quiz 前**逐字相同**、`simTime` 与 `karts[0].odo` 不推进、不重新播音、不重播 `open` 动画、且 `#quiz` 的 z=8 完整盖住路牌（z=4）不留边缘露出。

补充：暂停 `paused` 时路牌**冻结保持**（不隐藏），因为 `#panel-pause` 没有题目文本，无叠加风险。

#### 2.2.7 边缘情况（≥3 类，逐条给行为）

| # | 边缘情况 | 规定行为 |
| --- | --- | --- |
| E1 | **跨圈瞬间**（`state.lap` 自增，`race.js:611-617`）恰逢上一门 `judged` 与下一门 `dist ≤ D_preview` 重叠 | 以 `activeGate()` 返回为准，一次只显示一个门的 2 块牌；`nextGate.lap === state.lap`；`rally:lap` 事件先于 `rally:gate-preview` 发出 |
| E2 | **quiz 与分叉门同时触发**（撞石头/墙时 `answering()` 为真，`race.js:533` 会跳过碰撞，但仍可能 `state.quiz` 与 `state.decide` 同帧） | quiz 优先：隐藏路牌、冻结小地图；`state.decide` 保持不推进；回 `racing` 后按 `played` 恢复 S2，不重新 `audio.playWord` |
| E3 | **boost / turbo / 起跳冲刺导致 `odo` 单帧跳变**（`race.js:293-297` `900·dt`、`launch()` `main.js:800` 最多 +1200）跨过 `D_preview` 或 `lead` | 阈值用名义 `diff.speed` 常量，不随速度抖动；若单帧从 `dist > D_preview` 跳到 `dist ≤ lead`，允许 S1 被跳过、直接进 S2（`played` 由 `beginDecide` 兜底置位），**不允许**出现 S1 内容残留在 S2 |
| E4 | **`window.blur` 自动暂停**（`main.js:322`）时正处 S1/S2 | 冻结保持（不隐藏、不重绘、不播音）；恢复后按当前 `dist` 重新判定状态；`pointer.{left,right}` 不残留 |
| E5 | **`boardOpen` / `shopOpen` 从 `racing` 打开**（`mode` 不变） | 依 2.1.6 显式隐藏小地图与路牌；关闭后按当前 `dist` 恢复，**不得**因冻结期间未 `step` 而错位 |
| E6 | **`race === null`**（标题页 / 商店关闭后 `main.js:886`）但 `mode` 仍非 title | `visible` 中的 `&& !!race` 兜底；`minimapModel()` 返回 `null`，渲染层跳过绘制，不抛异常 |
| E7 | **极窄屏 320px / 横屏短高（如 375×320）** | `--mm-w/-h` 用 `min(px, vw)` 收敛；断言 `mm.bottom < innerHeight`；小地图高度 ≤ `#touch` 高度之前的空间；不与 `#count-num`（120px 字）在纵向重叠 |
| E8 | **`prefers-reduced-motion`** | 小地图无脉动/无进度弧补间；路牌 `open` 动画降级为直接显示（`css/game.css:141` 的 `lane-in` 由媒体查询禁用），两侧仍同帧 |
| E9 | **`g.unheard = true`**（`race.js:696` 越过门线从未播放） | 立即转 S3 隐藏路牌；小地图 `nextGate` 跳过该门；**不得**补显 S1/S2 内容（否则等于事后泄露词面） |

### 2.3 缓存串 bump 提示（**本规格不改，仅提示**）
全站 `?v=` 当前唯一 tag `cseg-20261107`（`config.js:7 CACHE_TAG`；任务口径：46 处字面量、20 个图片 URL 零裸引用）。本轮 #4 改动 `index.html` / `css/game.css` / `js/render.js` / `js/main.js` 后**必须统一 bump 到 `hud-20261108`（主理人裁决锁定值）**，`config.js` 的 `CACHE_TAG` 同步改为该值；覆盖：所有 `<link>` / `<script>` / `<img src>` / ESM `import "...?v="` / `CARDS`/`PHONEMES` 内拼出的 sprite URL。遗留任何旧 tag 会命中浏览器缓存导致 HUD 不更新。QA H11。

---

## 3. B. 下一轮 3D 跟车视角演进

### 3.1 前提差异
- 现状 2D：`render()` 一次画全 `track.samples` 环线（`render.js:239-249`），`camera` 只是平移+旋转+缩放的仿射矩阵（`render.js:228-233`），`project()` 是 `DOMPoint.matrixTransform`（`render.js:460-463`）。玩家**看得见整条赛道与所有分叉**。
- 3D 跟车：车在近处下方、赛道向远处消失，视锥只覆盖前方 N 米；`track.samples` 需视锥裁剪，`project()` 换透视投影（或 WebGL），`camera` 改为第三人称跟随位姿（沿用 `main.js:403-414 followCamera()` 的朝向语义）。`visibleGates` 仍按 `lap` 过滤。

> **「看不到整条赛道才需要预告」在此刻才成立**。本轮所有 HUD 契约按"下一轮会看不到全景"来设计，但**不提前引入任何 3D 依赖**。

### 3.2 同一套 HUD 在看不到全景时的信息职责升级

| 信息 | 2D 全景（本轮） | 3D 跟车（下一轮） |
| --- | --- | --- |
| 赛道全貌 | 主画面直接给 → 小地图**冗余** | 主画面只剩前方一段 → 小地图**唯一来源（必要）** |
| 自己在环线上的位置 | 主画面可见 | **小地图必需** |
| 对手位置 | 近处对手主画面可见 | 身后/远处对手**只能靠小地图** |
| 下一个分叉的距离 | 主画面可见 | **小地图 `nextGate` + 世界空间预告牌**（双通道） |
| 圈数 / 起终点 | HUD `#gates` + 小地图（冗余） | HUD + 小地图（**起终点标记必需**，用于判断还剩多远完赛） |
| 分叉两侧选项 | 世界空间投影 DOM 牌 | 世界空间物体（透视缩放） |
| 答案（听到哪个词） | **仅音频** | **仅音频**（不变） |

**HUD 契约不变项**：`#minimap` 的 DOM id、CSS 变量、`z-index:5`、`pointer-events:none`、显隐矩阵、`#hud` 的 `--mm-right-gutter`。3D 轮**不重做 HUD 设计决策**，只替换渲染器。

### 3.3 小地图从「冗余装饰」升级为「必要导航」时信息密度怎么变

| 级别 | 内容 | 本轮 / 下一轮 |
| --- | --- | --- |
| L0 基线 | 环线 + 玩家点 + 2 对手点 + 起终点 + 圈数 + 进度弧 + 中性 `nextGate` 菱形 | **本轮（全量落地）** |
| L1 导航 | + 当前圈高亮弧（用 `odo/(laps·L)`）+ 剩余分叉数（`2·laps − 已判定数`）+ `nextGate.secondsTo` 的**中性刻度**（进度点，非文字倒计时） | 下一轮 |
| L2 空间 | + 视锥扇形（把当前相机可见弧段在小地图上高亮）+ 身后对手的方向指示 | 下一轮（可选） |

**密度铁律**：L1/L2 的增加**只能靠几何符号**（弧、扇形、点、刻度），**不靠文本**，且**永不加入词 / IPA / 正确侧**。理由：受众是小学生/初中生，2D 全景下再加文字就是认知过载（`#gates` 已有「第 1/2 圈 · 听对 N」、`#place`、`#combo`）；3D 轮即使信息变必要，也要保持「一眼看懂」的图形化。**支柱漂移红线**：若出现「玩家只看小地图箭头而不听音」的主导策略苗头，立即回退到中性菱形标记。

### 3.4 路牌从 HUD 元素变成世界空间物体后的可读性规则

现状路牌其实**已经是世界空间投影的 DOM**（`placeLaneSign()` 用 `project(matrix, ...)` 把世界点投到屏幕再用 `left/top` 定位），距世界空间物体只差一个透视矩阵——这是本轮复用它的最大价值。

| 规则 | 规格 |
| --- | --- |
| 投影 | 把 `project()` 换透视版本；`--lane` 旋转角仍由两个投影点 `a,b` 算 `atan2(b.x−a.x, a.y−b.y)`，但须传**透视投影后**的点 |
| 近大远小 | 字号/尺寸随距离插值，但设下限：`clamp(13px, 2vmin, 26px)`（沿用 `css/game.css:139-140` 的 clamp 思路），**两侧牌必须同尺度** |
| 对比度 | 底板 `var(--card)` alpha ≥ .82 + 深墨描边，任意背景上文字对比 ≥ 4.5:1 |
| 太近淡出 | `dist < D_min = 0.15·span·L` 时牌淡出，避免透视放大后糊屏或挡住车 |
| 太远淡入 | `dist > D_preview` 不渲染（S0）；`dist ∈ (D_far, D_preview]` 用中性 S1 外壳 |
| 遮挡剔除 | 被 `#minimap` / `#hud` / `.panel` 矩形覆盖时隐藏（2.2.4 的避让裁剪升级为通用 HUD 矩形表） |
| **对称性** | 两块牌**始终同尺度、同亮度、同不透明度、同帧出现**；禁止任何单侧强调（透视下最容易因左右深度差意外产生"某侧更醒目"，须显式钳制） |
| 信息集合 | **不变**：S1 中性零文本 / S2 对称题干；`spoken`、`correctLateral` 永不进入 |

### 3.5 本轮必须为将来预留的规格（**逐条对应 1.2–1.4**）

| # | 预留项 | 本轮落地形式 | 3D 轮如何使用 |
| --- | --- | --- | --- |
| P1 | **数据接口** | `window.__rally.minimapModel()`，字段白名单见 1.2；渲染器只消费该对象，不直接读 `race.state.gates` | 换透视渲染器时 HUD 层零改动；QA 可断言「不含答案字段」 |
| P2 | **坐标系** | 唯一绝对 `odo`；`t = (odo/L)%1` 只由 odo 派生；`nextGate.line` 绝对里程 | 视锥裁剪、环线弧长映射、两圈进度全部沿用 |
| P3 | **事件** | `rally:gate-preview` / `gate-played` / `gate-judged` / `lap`（1.3），payload 无答案 | 3D 世界预告牌、音画对齐、视锥预加载订阅 |
| P4 | **HUD 契约** | `#minimap` id、CSS 变量、z-index=5、显隐矩阵、`#hud` gutter（2.1.3–2.1.6） | 3D 轮不改 HUD，只换 `render()` |
| P5 | **`diff.preview`** | 本轮启用为 `D_preview` 的秒数基准（2.2.2） | 3D 轮沿用同一常量，不新增参数；预告窗口随难度档自适应 |
| P6 | **`placeLaneSign` 参数化** | `spanEff` 入参 + `t_i=(odo_i/L)%1` | 透视 `project()` 替换后函数体几乎不变 |

---

## 4. C. 核心循环验证（「听到词 → 看到预告 → 选车道 → 判定」）

### 4.1 逐步决策链（2D 本轮 / 3D 下一轮对照）

| 步 | 触发与代码位置 | 2D 本轮玩家看到/听到 | 3D 下一轮 | 是否泄露答案 |
| --- | --- | --- | --- | --- |
| **T0 预告** | `dist ≤ D_preview`（1482 / 1620 里程，5.70 / 5.40 s），`rally:gate-preview` | 小地图 `nextGate` 中性菱形点亮；S1 两块**零文本中性牌**立在门线前 534/583 里程；`#hud` 圈数不变。**全景下这些信息冗余**（主画面本就看得见分叉） | **必要**：主画面只剩前方一段，小地图菱形 + 世界预告牌是唯一空间预警 | ❌ 无。S1 无 word/IPA/label/sprite，`spoken`/`correctLateral` 未进入渲染 |
| **T1 播音** | `beginDecide()` `dist ≤ lead`（1036 / 1107 里程，`race.js:421-439`）；`g.played=true; audio.playWord(g.spoken.word)`；`rally:gate-played` | **答案唯一通道：听觉**。同时 `state.decide = {phase:'reveal', arm:0.55}`，S1→S2 切换 | 同左，音画与透视预告牌对齐 | ⚠️ 这是**设计内的答案给出**（听觉），不是泄露 |
| **T2 选项 + 转向** | `g.played && !g.judged` → S2；`reveal 0.55s → hold 3s`（`race.js:669-677`）；`#fork-count` 显示 3/2/1（`main.js:560-568`）；`blockSplitter` 要求 `\|lateral\| ≥ half`（`race.js:375-391`） | 两侧牌**同时**呈现 `word + /ipa/ + 类别`；玩家把听到的词匹配到某侧 → 按 ←/→ 或触屏「向左/向右」，`laneTarget = ±0.55` | 同左，牌带透视缩放、近大远小、两侧同尺度 | ❌ 无。两侧信息量恒等、同帧、同样式；`correctLateral` 未出现 |
| **T3 判定** | `player.odo ≥ g.line` → `judge()` → `hitsLane(lateral, correctLateral)`；`rally:gate-judged` | 命中：`cheer` / `banner` / boost / combo；失误：`错了 · 是 X`（**判定后才显示**，此时已无决策价值）；路牌转 S3 隐藏 | 同左 | ✅ 判定后反馈可含 `spoken`，因决策已结束（与 `#quiz-result` 同理） |
| 循环 | 回 T0 等下一个门（同圈 `0.68` 或下一圈 `0.24`） | 小地图 `nextGate` 熄灭→下一个点亮 | 同左 | — |

### 4.2 不泄露答案 · 两轮通用证明
1. **答案的定义**：`correctLateral`（左/右）与 `spoken`（听到的词）由 `buildGates()` 两次独立随机（`onRight` / `sayFirst`）决定，二者无视觉关联。
2. **唯一映射线索**是音频：玩家须把 `audio.playWord(spoken.word)` 与两侧 `word` 匹配。
3. **视觉层字段白名单**（1.1/1.2）：只有 `id/lap/line`（几何）、`left/right`（对称题干）、`played/judged`（状态机）。`spoken` 与 `correctLateral` 被单向铁律隔离在 `audio.playWord()` 与 `judge()` 内。
4. **时序隔离**：S1（音频前）零文本 → T1 才播音 → S2（音频后）才给对称选项 → T3 判定后隐藏。任何时刻都不存在"未听音却能看到指向某侧的信息"。
5. **3D 轮不变**：只改变距离/透视/视锥，信息集合与时序完全一致。
6. **叠加风险受控**：quiz 冻结隐藏路牌（2.2.6），避免 `#quiz-prompt` 的 `q.spoken.word` 与分叉门两侧词同屏构成提示。

### 4.3 对自我决定论（胜任感）与心流的影响

| 维度 | 作用 | 设计意图 |
| --- | --- | --- |
| **胜任感（Competence）** | T0 预告消除「因看不见分叉而撞墙」的**非能力性失败**；失败归因回到「听没听准」这一真实技能维度 | 保护小学生/初中生的胜任感，避免"不是我听错，是游戏没告诉我"的挫败 |
| **胜任感 · 难度梯度** | follow（260 / 3.6s fork / 4.2s preview）比 listen（300 / 3.4s / 4.0s）更宽更慢；两档预告提前量刻意对齐 ≈1.7s，不制造"选某档更容易"的**主导策略** | 自我决定论的技能-挑战匹配 |
| **自主性（Autonomy）** | 预告只给"要分叉了"，不给"该往哪"；答案仍由玩家自己听、自己选 | 不剥夺决策权，避免把游戏退化成"跟着箭头开" |
| **心流 · 明确目标** | S1 中性预告 → T1 音频给目标 → S2 对称选项给可操作对象 | Csikszentmihalyi 的清晰目标 |
| **心流 · 即时反馈** | T3 判定即出 `cheer`/`banner`/boost；`#fork-count` 3/2/1 给时间边界 | 即时反馈 + 明确时间压力 |
| **心流 · 不打断** | 路牌 `judged` 后立即隐藏不滞留；quiz 冻结后回 `racing` 按 `played` 无缝重现；小地图 `pointer-events:none` 不抢输入；T0→T1→T2 单调时序无跳变 | 保持注意力在"听"上 |
| **认知负荷** | 小地图只放几何 + 极简 `1/2` 圈数，不重复「听对 N」；S1 零文本 | 防认知过载（受众年龄敏感） |

### 4.4 设计理论红线自检
| 红线 | 结论 |
| --- | --- |
| **主导策略** | 无。预告是中性信息，不提供任何可替代「听音」的取胜路径；两档提前量对齐。3D 轮需持续监控"只看小地图"苗头（3.3 已给回退规则） |
| **经济失衡** | 无。HUD/路牌**零写盘、零触碰 `gems`/`shields`/`unlocked`**，不调用 `commit()` / `applyWalletDelta()`；`minimapModel()` 是纯读函数 |
| **认知过载** | 已控。2D 全景下小地图刻意保持 L0 低密度并显式标注冗余；不重复 HUD 已有计数；S1 零文本；3D 轮升级只用几何符号 |
| **支柱漂移** | 已设铁律。「听音选车道」是核心支柱，任何把 `spoken`/`correctLateral` 搬上 HUD 的"增强"都属漂移，禁止 |

---

## 5. D. 给 QA 的验收断言建议（H1–H12，可直接自动化）

风格对齐 `verify_cseg_ui.py`（Playwright + `chk(name, ok, detail)` + `page.evaluate` + `window.__rally.step(n)`，PC viewport `1280×800`，另建 `375×667` context）。建议新增 `verify_hud_spec.py` 或并入 U 系列。

| # | 断言 | 实现要点 / 表达式 |
| --- | --- | --- |
| **H1 DOM 存在性 + pointer-events** | `#minimap` 与内嵌 `#minimap-c` 存在；`aria-hidden="true"`；`getComputedStyle(mm).pointerEvents === 'none'`；底板 `backgroundColor` 的 alpha ≥ .82 | `page.evaluate("() => { const m=document.querySelector('#minimap'); return {exists:!!m, canvas:!!m?.querySelector('canvas'), pe:getComputedStyle(m).pointerEvents, bg:getComputedStyle(m).backgroundColor, aria:m?.getAttribute('aria-hidden')}; }")` |
| **H2 显隐矩阵** | 逐阶段断言 `mm.hidden`：title/teach/results = `true`；countdown/racing/paused = `false`；**`quiz` → `mm.hidden === false`（显示但冻结）**，且冻结前后 `karts[0].odo` / `simTime` 相等；`boardOpen\|\|shopOpen`（mode 仍 racing）→ `mm.hidden === true` 保持 | 用 `window.__rally.mode` / `.boardOpen` / `.shopOpen` 配合 `#btn-board`/`#board-close`/`#how-shop` 真实点击；**必须覆盖"mode 仍 racing 但 boardOpen=true"**与 quiz 冻结前后数值不变 |
| **H3 375px 不溢出** | `375×667` 下 `r.left≥0 && r.right≤375 && r.top≥0 && r.bottom<667 && r.width≤112.5`；`320×568` 同样不溢出 | 新建 `browser.new_context(viewport={...})`；`getBoundingClientRect()` |
| **H4 位置不重叠（双视口）** | `mm.rect` 与 `#hud .hud-row > *`（含 `#btn-mute`/`#btn-pause`/`#combo`）、`#banner`、`#route-map`（可见时）两两不相交；PC 与 375px 各测一次 | 矩形相交判定 `!(a.right<=b.left\|\|b.right<=a.left\|\|a.bottom<=b.top\|\|b.bottom<=a.top)`；单独断言 `banner.top ≥ mm.bottom + 12`（窄屏） |
| **H5 小地图不含答案文本** | 对 4 个门逐一检查 `g.spoken.word`、`g.other.word`、`g.left.word`、`g.right.word`、各 `ipa`/`displayIpa` **均不出现**在 `mm.textContent`、`mm.innerHTML`、所有后代的 `alt`/`aria-label`/`data-*`；且无 `data-lane/data-correct/data-side/data-answer` 属性 | `page.evaluate` 内把 `mm.textContent` + `mm.innerHTML` + 所有后代属性值拼成一个字符串 `s`（用逗号连接，避免引入管道符），再对 4 门的 6 个词面/IPA 做 `s.includes(w)`，断言命中数 `bad.length===0`；同时扫描后代属性名不含 `data-lane/data-correct/data-side/data-answer` |
| **H6 数据接口无答案键** | `JSON.stringify(window.__rally.minimapModel())` 不含 `spoken\|correctLateral\|left\|right\|pairKey\|qType\|options\|displayIpa\|answer\|correct` 作为**键名**；`nextGate` 只含 `{id,lap,line,distance,secondsTo}` | 用 `Object.keys` 递归收集键名再匹配（避免误伤 `"distance"` 之类）；断言 `nextGate` 键集合精确相等 |
| **H7 路牌在阈值内出现** | 手动设 `r.state.player.odo = g.line − (D_preview + 50)` → `#signs.hidden===true`；推进到 `dist = D_preview − 20`（且 `!g.played`）→ `#signs.hidden===false` 且两牌 `textContent.trim()` 无字母/无 `/`；推进到 `g.played=true` → 两牌含 `word` 与 `/ipa/` | `D_preview` 用 2.2.2 常量：follow 1482 / listen 1620（里程）；先 `page.click("#btn-follow")` 或 `#btn-listen` 定档；`window.__rally.step(1)` 驱动一帧 |
| **H8 路牌对称、无指向性** | S2 下 `signL`/`signR` 的 `rect.width` 相等（±1px）、`opacity` 相等、`className` 不含 `ok\|bad\|correct\|answer`；两牌 `textContent` 分别含 `g.left.word` / `g.right.word` 且互异；S1 下两牌 `className` 均不含 `is-long\|is-short`、`textContent` 无任何字母与 `/` | 同时断言 `#signs.innerHTML` 不含「正确」「答案」及 `g.correctLateral` 符号提示 |
| **H9 quiz 冻结行为** | 注入 `r.state.quiz`（仿 `verify_cseg_ui.py:161-171`）→ `step(1)` 进 quiz；断言 `#signs.hidden===true`（Q2 推荐）；记录 `simTime`、`karts[0].odo`、`mm` 冻结前后相等，`step(60)` 后仍相等；答完回 `racing` 后 `#signs.hidden` 恢复 `false` 且内容与进 quiz 前一致 | 同时断言 quiz 期间**未调用** `localStorage.setItem`（hook 计数） |
| **H10 两圈不重复/不串位** | `r.state.lap===1` 时 `#signs .sign` 数量 ≤ 2；`signKey` 以 `gate.id` 开头且含 phase；两圈同 `commitT` 门 `line` 差 = `L`（±1）；`minimapModel().nextGate.lap===1`；把第 2 圈门置 `played=true` 后路牌正常出现 | 用 `window.__rally.step(n)` 或仿 U9 直接推进 `odo`；断言 `lineT=[0.24,0.68,1.24,1.68]` |
| **H11 缓存串唯一** | 全站 `?v=` 字面量集合大小为 1 且等于新 tag；`config.js CACHE_TAG` 与之相同；所有 `<img src>`/`<link href>`/`<script src>`/ESM `import` 的 `?v=` **零裸引用**；20 个图片 URL 全部带 tag | 静态扫 `index.html` / `css` / `js` / `config.js`；`re.findall(r'\?v=([A-Za-z0-9\-]+)')` |
| **H12 零回归 + 零写盘** | `pageerror/console_error/requestfailed/bad_status` 全 0（沿用 U1/U12）；HUD 路径**不写 localStorage**：hook `Storage.prototype.setItem` 计数后 `step(300)`，计数增量 = 0；`rally.unlocked`/`maps`/`EP02` 在开赛前后逐字段相等 | 防 HUD 改动引入跨站存档竞态（两站共享单键 `ipa-quest-v1`） |

**可选补充**：H13 `prefers-reduced-motion` 下无 `lane-in` 动画且两牌同帧；H14 `E9 unheard` 门不补显 S1/S2；H15 `E3` 单帧 `odo` 跳变不残留 S1 内容。

---

## 6. E. 已知风险与缓解（R1–R8）

| # | 风险 | 机制 / 具体位置 | 缓解 | 断言 |
| --- | --- | --- | --- | --- |
| **R1** | **2D 全景下小地图信息冗余**（用户/主理人已点明） | 现状 `render.js:239-249` 画全环线，玩家本就看得见分叉、对手、自己位置 | **诚实标注非玩法刚需**（0.5）；本轮只锁 HUD 位置/样式/`minimapModel`/事件契约，不做成可交互、不加玩法决策信息；L0 低密度；3D 轮才升 L1/L2；设支柱漂移红线（禁止把正确侧画上去） | H5/H6 |
| **R2** | **375px 触屏右上角与现有 HUD 拥挤** | `#hud`(`css:37-40`, z5, `.hud-row` flex-wrap 在 375px 换 2~3 行)；`#btn-mute`42px / `#btn-pause`≥72px 被 `.spacer` 推到右侧；现有小地图画在 `#c`（无 z-index，最底）固定 `w−148,16,132×86` → 被 HUD 与 `#banner`(`css:118-123`, top78、窄屏宽 351) 覆盖 | `#hud { padding-right: var(--mm-right-gutter) }` 从根上收窄 content box；小地图 DOM 化 z=5 + `pointer-events:none`；窄屏 `#banner` 下移到 `mm.bottom+20`；`placeLaneSign` 增小地图矩形避让裁剪 | H3/H4 |
| **R3** | **两圈同 `commitT` 的路牌状态** | `t0=gate.commitT−k·span`（相对）与 `odo0=gate.line−k·span·L`（绝对）两套坐标；两圈 `commitT` 都是 0.24/0.68；若用 `commitT`/`lineT%1` 作 key 或遍历全量 gates → 重复/错位/第 2 圈不出现 | 硬约束 5 条（2.2.5）：`gate.id` 唯一 key + 只消费 `activeGate()` + `nextGate` 按 lap 过滤 + `t=(odo/L)%1` + 跨圈不清 `signKey` | H10 |
| **R4** | **答案泄露（跨元素叠加）** | `#quiz-prompt` 在 ipa/type 题写 `q.spoken.word`（`main.js:774`），而 `#signs` 可能仍显示分叉门两侧词；小地图若误渲染 `left/right`/`correctLateral` 则直接泄露 | 字段白名单（1.1/1.2）+ 铁律；S1 零文本；S2 严格对称；**quiz 冻结隐藏路牌**（Q2）；`rally:gate-judged` payload 不含 `hit`/`spoken` | H5/H6/H8/H9 |
| **R5** | **冻结态仍调用 `syncSigns`/`render`，导致显隐错误** | `main.js:938 frozen` 只冻结 `simTime` 与 `race.update()`；`main.js:990` 在 `mode!=="title"&&"teach"` 每帧仍调 `syncSigns()`；`minimap: mode!=="title"` 在 teach/results/quiz/board/shop 下仍为 `true` | 显隐改由 2.1.6 的 `visible = mode∈{...} && !boardOpen && !shopOpen && !!race` 显式控制，**不依赖 `minimap: mode!=="title"`**；`boardOpen`/`shopOpen` 时 `mode` 仍是 `racing`，必须查标志位 | H2/H9 |
| **R6** | **`diff.preview` 闲置 / `speedNow()` 动态导致预告窗口抖动** | `preview` 定义未消费（0.3）；`beginDecide` 的 `lead` 用 `speedNow()`，受 `SLOW 0.54`/`BOOST 1.48`/`TURBO 1.92` 影响；若 HUD 阈值也用 `speedNow`，加速时窗口忽长忽短 | HUD 阈值用**名义常量** `D_preview = span·L + 0.5·preview·speed`（follow 1482 / listen 1620 里程），不读 `speedNow`；`lead` 保持不动（不改判定核心）；两档提前量对齐 ≈1.7s | H7 |
| **R7** | **缓存串 bump 遗漏** | 46 处 `?v=` 字面量 + 20 图片 URL；本轮改动 `index.html`/`css`/`render.js`/`main.js` 后任一处漏 bump → 命中旧缓存，HUD 不更新 | #4 统一 bump 到单一新 tag（值由主理人定），`config.js CACHE_TAG` 同步；本规格**仅提示不改** | H11 |
| **R8** | **认知过载 / 3D 轮主导策略** | 小地图若叠加圈数、分叉、对手、进度弧，与 `#gates`（「第 1/2 圈 · 听对 N」）、`#progress`、`#combo` 重复；受众为小学生/初中生 | 只放几何 + 极简 `1/2`，不重复计数；S1 零文本；3D 轮 L1/L2 只用几何符号不用文本；设「只看小地图不听音」监控与回退规则（3.3） | H5/H8 |

**跨文档一致性（具体冲突位置与修复建议）**：
- `render.js:416` + `main.js:987` 的 `minimap: mode !== "title"` 与 2.1.6 显隐矩阵**冲突**（teach/results/quiz/board/shop 会误绘）→ 按 2.2.4 改为 `visible` 表达式。
- `main.js:498-521 placeLaneSign()` 的 `t0=commitT−k·span` 与 `odo0=gate.line−k·span·L` **相差 `startOdo/L = 0.02`（≈385 里程）**，因 `commitT` 未含 `startOdo` 偏移（`race.js:83`）→ 建议统一为 `t_i=(odo_i/L)%1`（Q4，改则需补路牌投影位置回归断言）。
- `config.js:38/48 preview` **无任何消费点**，与 `race.js:426 lead` 的硬编码公式并存 → 本轮启用为 HUD 预告基准，不动 `lead`（避免改动判定核心）。
- `css/game.css:118-123 #banner top:78px` 与 375px 下 `mm.bottom≈72px` **仅 6px 间隙** → 窄屏按 2.1.4 下移。
- `main.js:459 syncSigns()` 把 `quiz` 列入 `activeGate()` 条件，与 2.2.6「quiz 隐藏路牌」**冲突** → 按 Q2 裁决改造。

---

## 7. 已裁决项（Q1–Q4 · 主理人锁定）

| # | 问题 | **裁决结论（锁定）** | 对规格 / 实现的影响 |
| --- | --- | --- | --- |
| **Q1** | 小地图是否 DOM 化（方案 A）还是保留画在主画布 `#c` 上（方案 B）？ | **A · DOM 化**。否则 `pointer-events` / z-index / 375px 避让只能靠 JS，且 QA 无法做「DOM 存在性 / 位置不重叠」断言，3D 轮也要重做 HUD | 2.1.1 方案 A 生效；#3 按 A 评估改动文件清单；D 节 H1/H4 按 DOM 写 |
| **Q2** | quiz 冻结时路牌隐藏还是冻结保持？ | **隐藏**。避免 `#quiz-prompt` 在 ipa/type 题写出 `spoken.word` 与分叉门两侧词同屏；回 racing 按 `played` 无缝重现 | 2.2.6 生效；`syncSigns()` 增隐藏分支；H9 断言期望 `#signs.hidden===true` |
| **Q3** | T0「中性预告」本轮载体：仅小地图菱形，还是同时做 S1 世界空间中性牌？ | **两者都做**（2.2.1 完整 S0–S3 状态机）。用户已拍板「预告给路牌」，仅菱形不算路牌落地；S1 复用现有 `#sign-l/#sign-r` + 参数化 `placeLaneSign`，零新增 DOM | 2.2.1 / 2.2.4 生效；#4 需改造 `placeLaneSign`；H7/H8 覆盖 S1 |
| **Q4** | 是否顺带统一 `placeLaneSign` 的 `t` / `odo` 坐标（现差 0.02·L）？ | **本轮不改**。修正会移动所有既有路牌、扩大回归面；**新增逻辑一律用 `t_i=(odo_i/L)%1` 从绝对 `odo` 派生**；旧不一致**登记为遗留项**（见下） | 2.2.4 的「建议修正」不执行；`race.js:83` 的 `startOdo` 偏移差异留给 #3 盘查后单独评估 |

**补充裁定（同批锁定）**
1. **右上角 = 同位置角色切换**：`#route-map`（仅 `title`，`main.js:256`）与比赛小地图（仅非 `title`，`main.js:987`）互斥，**不存在三元素叠压**；保持「标题页 = a1 四区大地图入口 ／ 比赛中 = 该轮闭环小地图」，`#route-map` 保留不动、不新增第三层。本规格 2.1.4 / 2.1.6 原即按互斥书写，无需改写；2.1.3 的 `#hud padding-right` gutter 解 375px 拥挤方案继续有效。
2. **缓存串锁定 `hud-20261108`**：替换 `cseg-20261107`，`config.js CACHE_TAG` 同步；全站 `?v=` 唯一、零裸引用（2.3 / H11 / R7）。D 节 H11 的「新 tag」与 E 节 R7 的「值由主理人定」一律读作 `hud-20261108`（按「正文不改」要求保留原措辞）。
3. **可访问性分级**：`A11Y-TIER: Standard（本轮底线）→ Comprehensive（下一轮 3D 目标）`，详见 §0.6。听障视觉冗余**不纳入本轮**，登记为下一轮需用户与设计侧共同拍板的独立议题。
4. **遗留项登记**：`placeLaneSign()` 的 `t` / `odo` 差 `startOdo/L = 0.02`（≈385 里程）本轮不修；下一轮或单独回归窗口评估，若修需 QA 补路牌投影位置断言。

> **一致性说明**：正文中残留的「裁决项 Qn / 默认推荐 / 按 Q2 裁决」均为**出处引用**，一律以本节锁定结论为准，不代表待定；A/B/C/D/E 与 H1–H12 断言内容未按本次裁决改写。

---

## 8. 交付边界与 Handoff

- **本文件是唯一写入物**。未修改任何 `js/` / `index.html` / `css/` / 图片 / 验收脚本；未触碰 `data.js`、`ipa-display.js`；未重跑上游管线；未部署/上线/commit。
- **给 #3（engineering-lead 盘查）**：优先核实 0.1–0.4 的 4 条事实（`drawMinimap` 已存在、`signs` 是答案载体、`preview` 闲置、两套坐标），以及 R2/R5 两个具体冲突位置；按已裁决 Q1=A（DOM 化）评估改动文件清单。
- **给 #4（实现）**：按第 2 节逐条落地；**所有新增 HUD 路径零写盘、零触碰 `gems/shields/unlocked`**；`sym` 不得作显示文本，禁止 `displayIpa` 作键；改动后统一 bump 缓存串到 `hud-20261108`。
- **给 #5（QA）**：第 5 节 H1–H12 可直接映射为 `verify_hud_spec.py` 的 `chk()`；务必覆盖 375px 双视口、board/shop 打开时 `mode` 仍为 `racing`、两圈 `lap===1`、缓存串唯一性。
- **给 #2（art-director）**：3D 视觉方向稿请对齐 3.4 的可读性规则与 2.1.3 的羊皮纸配色（`--paper #f6ead0` / `--ink #4a3520` / `--gold #c9a227` / `--gold-deep #a0720a`）；小地图底板沿用 `--card`；右上角按 §0.6 与第 7 节的「同位置角色切换」裁定处理，`#route-map` 与比赛小地图互斥、不新增第三层。

---

*规格结束 · Q1–Q4 已裁决锁定 · 缓存串 `hud-20261108` · 可进入实现*
