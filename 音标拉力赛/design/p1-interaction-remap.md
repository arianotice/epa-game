# P1 交互 · 门控重锚只读盘点清单（QA-GATE-MAP）

> v1.1 · 2026-11-14 · 严守真（quality-lead）
> 用户书面批准：`2026-11-14 09:53 +0800`（放行全量实现 +「只做单跳必过」）
> 口径优先级：**用户最新拍板 > `p1-interaction-impl.md`(E1) > `p1-interaction-qa.md` / `p1-qa-spec.md` / `p1-interaction-visual.md`**（engineering-lead 2026-11-14 确认）
> v1.1 增量：`QA-GATE-MAP-RULING` 三项待拍板裁定回填至 §9，并并入两条既有裁定；§1–§8 盘点快照与 50 条统计不回溯改写，执行口径以 §9 为准。

---

## 0. 本文件性质与边界（先读）

1. **性质**：本文件是**只读盘点的产物**，用于给最终回归准备精确的「断言期望值重锚清单」，避免实现落地后再逐条摸索。
2. **本轮不执行**：清单里所有标注「需改」的条目，都是**待主理人放行后**在「实现期 / 回归期」要做的动作；本轮 QA **不改任何 `verify_*.py`、不改 `result.json`、不改任何产品代码、不改其余四份规格、不跑门控、不启浏览器、不 commit / push**。
3. **唯一授权写入**：本文件 `design/p1-interaction-remap.md`（新建）。
4. **格式约定**：每条给 `文件:行号 → 当前期望值 → 新口径 → 「需改 / 维持原值」`。「维持原值」= 断言、常量、门槛、清单逐字不动，**不删、不豁免、不改 NOTE、不放宽**。
5. **硬约束继承**（不得被本清单改写）：
   - `SUITES` 顺序 `S3 → S5 → S0 → S1 → S2 → S4 → S6`（`verify_p1_gate.py:358-369`）；S5 真实 Chromium WebGL 取证必须前置，浏览器门控不并行。
   - 四项错误 `pageerror / console_error / requestfailed / bad_status` 归零硬 `chk` 未放宽；`ERR_ABORTED` 单列披露，不豁免同类错误。
   - 人工过眼一律进 `result.json.not_covered` / `manual_signoff`，**不进 PASS 计数、不冒充 PASS**。
   - 退役令口径：退役的是「四套旧套件作为发布阻断判据的地位」，**不是删 81 项 `PLR-*` 断言**。
6. **v1.1 裁定层**：§1–§7 的「需改 / 维持原值」判定与 §8 的 50 条统计是 **QA-GATE-MAP 盘点时点快照**，不因后续裁定回溯改写；三项待拍板项的最终执行口径统一见 **§9（已裁定）**，冲突时以 §9 为准。§4 / §5 的 deferred 项在 IMPL-1B 落盘前保持 deferred，本轮不提前动任何脚本。

## 0.1 本轮复核到的磁盘真值（2026-11-14，只读）

| 事实 | 值 |
| --- | --- |
| 权威门控 | `verify_p1_gate.py` REAL_RUN v1.2；`result.json` = `121 PASS / 0 FAIL / 121 TOTAL` |
| `race.js`（IMPL-1A） | **已落盘**：`ROCK_QUOTA` / `ROCK_HITS_MAX` / `ROCK_HIT_BAND` / `ROCK_LAT_BAND` / `ROCK_MARGIN` / `NPC_MIN_SPEED_RATIO` 已 import 并使用（`:1`）；`buildField()` 整局石头 = `ROCK_QUOTA(2)`（`:142-146`）；`state.pickups = buildField()`（`:170`）；`scanPickups()` 滞空见证式（`:642-652, :724-736`）；删 `hopWindow` 死字段与 `dashLeft`（`:326, :332`）；词表 `Good/Excellent/Marvellous`（`:231`）；`0.94` 下限（`:311-315`）；`:724` 明注「只做单跳必过，取消二段跳」 |
| `config.js` | 6 个纯判定域常量已落（`:22-27`）；`CACHE_TAG="hud-20261108"`（`:7`）；`TUNING.laps=2 / commits=[0.24,0.68] / mergeDt=0.028`（`:15-17`）；`DIFFICULTY.speed = 260 / 300` 逐字未动（`:45, :55`） |
| `scene3d.jsx`（IMPL-1B） | v1.0 盘点时点「尚未落」（仅有 `window.__rally` 基础只读）；**v1.1 只读复核已落盘**：`pickups` getter / `PICKUP_KEYS` / `VISUAL_FLOW_GAIN` / `airMax` / `hop` 均在磁盘（见 §9.7）。按 team-lead 边界，§4 / §5 的「需改」项**仍保持 deferred**，解除须待合并任务派单 |
| `verify_p1_interaction.py`（S7） | **不存在**（Glob = No files found） |
| 源码层 tag | 9 文件共 **46** 处，唯一值 `hud-20261108` |
| 双快照 | `p0-pre-20261109/file-hashes.json` = 374 条；`p1-pre-20261110/manifest.txt` = 30 行 |
| 产物层 tag | `P1_TAG="p1-20261110"` / `VENDOR_TAG="p0-20261109"`，与源码层独立、不混算 |

> **口径更正（覆盖派单「当前事实」）**：派单登记「`race.js` 尚未落盘」，实测已落盘（见上）。这不改变任何判定，只是把 §1 的重锚前提从「预判」升级为「已实证触发」——`race.js` 与 `config.js` 的 sha256 与两份旧快照**必然不等**，BD-1 / B3 当前必然 FAIL，重锚动作不可省略。

---

## 1. 锚定基线：BD-1 五文件 + B3 七文件 → 并集 8 文件

**并集 8 文件（精确路径，逐字）**

```
音标拉力赛/js/race.js
音标拉力赛/js/track.js
音标拉力赛/js/config.js
音标拉力赛/js/main.js
音标拉力赛/js/render.js
音标拉力赛/js/headless_laps.mjs
音标拉力赛/js/probe.jsx
音标拉力赛/probe.html
```

- BD-1 侧 `CORE_FILES` 5 文件 = `race.js / track.js / config.js / main.js / headless_laps.mjs`
- B3 侧 `core` 7 文件 = `race.js / track.js / config.js / main.js / render.js / probe.jsx / probe.html`
- 交集 4（`race/track/config/main`）+ BD-1 独有 1（`headless_laps.mjs`）+ B3 独有 3（`render.js / probe.jsx / probe.html`）= 并集 **8**

| # | 文件:行号 | 当前期望值 | 新口径 | 判定 |
| --- | --- | --- | --- | --- |
| 1 | `verify_p0_gate.py:150-151` | `SNAP/file-hashes.json` 的 `files[]` 映射（374 条），`snap_eq()` 逐路径比 sha256 | **新建独立 P0 快照**（新目录/新文件名），`SNAP` 指针改指新快照；旧 `p0-pre-20261109` 原地保留归档、不删不覆写 | **需改** |
| 2 | `verify_p1_gate.py:444-450` | `p1-pre-20261110/manifest.txt`（30 行）正则抽 `路径 \| B \| sha256=` 成 `want{}` | **新建独立 P1 快照**，快照指针改指新 manifest；旧 `p1-pre-20261110` 原地保留归档 | **需改** |
| 3 | 并集 8 文件（上列） | 旧快照哈希：`race.js` `e9a17cf0…`、`track.js` `15b77aff…` 等 | 以**改动后**实际字节重录全部 8 文件 sha256；已实证 `race.js` / `config.js` 变动触发重锚，**v1.1 复核须再纳入 `render.js`**（`VISUAL_FLOW_GAIN` 落 `render.js:8`，见 §9.7 预警 3） | **需改** |
| 4 | `verify_p0_gate.py:35-36` | `CORE_FILES` 5 文件清单 | 清单逐字不动，不增不减、不把 3D 层塞进判定核心锚 | **维持原值** |
| 5 | `verify_p0_gate.py:158-161` | `BD-1 判定核心 5 文件 sha256 与 P0 前快照逐字全等` + `all(core_eq.values())` | 断言文本、判据、NOTE 一字不改；**不删断言、不豁免、不改 NOTE** | **维持原值** |
| 6 | `verify_p0_gate.py:163` | `BD-1b 五套既有验收脚本 sha256 与快照全等（零改动）` | 不变 | **维持原值** |
| 7 | `verify_p0_gate.py:164-167` | `BD-1c data.js / ipa-display.js 字节全等` | 不变 | **维持原值** |
| 8 | `verify_p1_gate.py:451-453` | `core` 7 文件清单 | 清单逐字不动 | **维持原值** |
| 9 | `verify_p1_gate.py:454-457` | `B3 判定核心 + 2D L0 + P0 探针 7 文件 sha256 双锚定全等（PDCORE-1）` + `len(mism)==0 and len(want)>0` | 断言文本、双锚定口径、NOTE 一字不改；**不删断言、不豁免** | **维持原值** |

> **§1 小计：需改 3 / 维持原值 6（共 9 条）**
> 用户已批准「新建独立快照重锚」。执行时**只换数据源**，不动断言形状。禁止用「临时豁免 / 改 `all()` 为 `any()` / 删 chk」让门控变绿。

---

## 2. `≤180s` 门槛与取时正则（提速后理论 <100s）

| # | 文件:行号 | 当前期望值 | 新口径 | 判定 |
| --- | --- | --- | --- | --- |
| 1 | `verify_p1_gate.py:396` | `times = [float(x) for x in re.findall(r"\b(1[0-7]\d\.\d\d)\b", out)]` —— 仅匹配 **100.00–179.99s** | 提速后 `finishTime` 理论 <100s 会取不到样本 → `bool(times)=False` 假 FAIL。改为可匹配 <100s（如 `\b(\d{1,3}\.\d\d)\b`），或更稳地按 `用时s` 列 / 末次汇总定向解析。**不沿用 `174.57s`；主理人已给新基线 `170.72s`（见 §9.5）** | **需改** |
| 2 | `gate-logs/S4.log`（历史基线） | 最慢 `174.57s`，距 180s 仅 `5.43s`；**主理人 2026-11-14 提供新基线 `170.72s`** | 判定核心已改、答题墙钟不占 `finishTime`、答错 `SLOW1.4s` 计入 —— 旧数 `174.57s` **不得沿用**，采信主理人新基线 `170.72s`（QA 本轮未实跑复核，最终回归仍须重跑 11 场确认、不冒充 PASS）；见 §9.5 | **需改** |
| 3 | `verify_p1_gate.py:397` | `bool(times) and max(times) <= 180.0` | `≤180s` 门槛**不变**；只改取样正则，不改 `<= 180.0` | **维持原值** |
| 4 | `verify_p0_gate.py:171` | `re.findall(r"^\s*(?:follow|listen)\s+\S+\s+\S+\s+YES\s+([\d.]+)", hl, re.M)` —— `[\d.]+` **已可匹配 <100s** | 本条**无需改**（此前未登记的关键差异：P0 的 BD-2 正则与 P1 的 S4 正则不一致，只需改 S4 一侧）。**主理人 2026-11-14 已采纳该新发现，维持不改（§9.5）** | **维持原值** |
| 5 | `verify_p0_gate.py:173` | `len(times)==11 and max(times) <= 180.0` | 门槛与场数不变 | **维持原值** |
| 6 | `js/headless_laps.mjs:137` | `if (r.finishTime > 180) fails.push(...)` | 180s 硬判据不变；`:91` `finishTime.toFixed(2)`、`:126` 表头 `用时s`、`:129` 打印列不变（S4 定向解析依赖此格式） | **维持原值** |

> **§2 小计：需改 2 / 维持原值 4（共 6 条）**
> 附注：P4 结论（engineering-lead）——答题墙钟不占 `finishTime`、答错 `SLOW1.4s` 计入，净利好不撑破 180s。即便如此仍不得跳过重跑基线。新基线 `170.72s` 由主理人提供，`≤180s` 门槛不变，裁定见 §9.5。

---

## 3. `SRC_TAG_COUNT=46` 与统一 bump 落点

源码层 `?v=hud-20261108` 实测分布（9 文件 / 46 处，唯一值）：

```
音标大闯关/index.html        17
音标大闯关/js/atlas.js        6
音标大闯关/js/level.js        1
音标大闯关/js/map.js          3
音标大闯关/js/story.js        2
音标拉力赛/index.html          7
音标拉力赛/js/main.js          7
音标拉力赛/js/race.js          2
音标拉力赛/js/render.js        1
TOTAL literal ?v= = 46
```

| # | 文件:行号 | 当前期望值 | 新口径 | 判定 |
| --- | --- | --- | --- | --- |
| 1 | `verify_p1_gate.py:56` | `TAG = "hud-20261108"` | 统一 bump 一次后改为新 tag 值（值由主理人定，QA 不臆造） | **需改** |
| 2 | `verify_p0_gate.py:25` | `SRC_TAG = "hud-20261108"` | 与 1 同步为**同一新值**（两处必须一致，否则 B1 / BC-1 互相打架） | **需改** |
| 3 | `verify_p1_gate.py:58` + `:426-427` | `SRC_TAG_COUNT = 46`；B1 `set(tags)=={TAG} and tags.get(TAG)==46` | 若 bump 后 46 处**总数不变**则只改值、计数 46 保留；若因新增 script/link/import/图片 URL 导致处数变化，则**同步改计数常量与 chk**，并复核 `vendor.manifest` 的 `count`（见 #9） | **需改** |
| 4 | 上列 9 文件 46 处 `?v=` 字面量 | `?v=hud-20261108` | 全部 script / link / ESM import / 图片 URL **统一 bump 一次**，禁止出现新旧两值并存 | **需改** |
| 5 | `index.html:187-188` | `var tag = "hud-" + "20261108";` / `s.setAttribute("src", "assets/p1/" + "scene3d.js?v=" + tag);` | **静态 tag 扫描盲点**：B1 / BC-1 的 `\?v=([A-Za-z0-9\-]+)` 抓不到这段字符串拼接，故不计入 46；必须**人工同步**两段字面量，否则浏览器实际加载的 bundle 版本与门控统计脱节 | **需改** |
| 6 | `js/build-p1.mjs:40` | `(src.match(/hud-20261108/g) \|\| []).length` AUDIT 零命中护栏写死字面量 | 与 1/2 同步改字面量；否则新 tag 值不再被护栏覆盖，旧值护栏空转 | **需改** |
| 7 | `js/config.js:7` | `export const CACHE_TAG = "hud-20261108";` | 同步改。`?v=${CACHE_TAG}` 是模板字符串，门控正则抓不到、不计入 46，但它是实际图片缓存键，漏改会造成跨版本脏缓存 | **需改** |
| 8 | `js/headless_laps.mjs:19` | `const TAG = "hud-20261108";` | 同步改（headless 侧常量，避免实跑与门控值漂移） | **需改** |
| 9 | `vendor.manifest.json` → `verify_p0_gate.py:270` BC-6 | `cache_namespaces.source_layer.count == 46` | 若 #3 计数变化则同步；若仍 46 则仅 `VENDOR_TAG` 不动 | **需改** |
| 10 | `verify_p0_gate.py:26` | `VENDOR_TAG = "p0-20261109"` | 产物层，**不随源码层 bump**；双层互不混算口径不变 | **维持原值** |
| 11 | `vite.config.js:14` | `// 本文件是 .js，会被 S17 扫描 → 全文禁止出现源码层 tag 字面量` | 禁令不变；**禁止**为图省事把新 tag 字面量写进本文件 | **维持原值** |
| 12 | `vite.config.js:25` | `const VENDOR_TAG = "p0-20261109";` | 产物层，不变（`:71` header / `:130` define / `:121` 日志同源） | **维持原值** |
| 13 | `verify_p1_gate.py:60-64` | `SRC_WHITELIST` 9 文件 | 白名单清单不变 | **维持原值** |
| 14 | `verify_p0_gate.py:29-34` | `SRC_SCAN_FILES` 9 文件 | 白名单清单不变 | **维持原值** |

> **§3 小计：需改 9 / 维持原值 5（共 14 条）**
> 注意：`js/config.js` 不在 `SRC_SCAN_FILES` / `SRC_WHITELIST` 内，其 `CACHE_TAG` 不影响 46 计数，但属实际缓存键，仍列「需改」。

---

## 4. B8 静态禁写 3D 层 + `build-p1.mjs` 产物层零命中护栏

| # | 文件:行号 | 当前期望值 | 新口径 | 判定 |
| --- | --- | --- | --- | --- |
| 1 | `verify_p1_gate.py:510-515` | 扫 `js/scene3d.jsx`，6 条 `bad_pat` = `localStorage.setItem` / `sessionStorage.setItem` / `race.state.\w+\s*=` / `\.odo\s*=` / `\.lateral\s*=` / `g\.line\s*=` 零命中 → `B8 3D 层静态零 Storage 写入 / 零判定域写回` | 断言与 6 条模式**一条不放宽**。3D 层新增 `pickups` 只读快照与分叉几何后，**一律只读投影**（`project()` / 展开），新增字段绝不写回 `race.state.* / odo / lateral / g.line`；不得用注释绕过静态扫描 | **维持原值** |
| 2 | `js/build-p1.mjs:39-46` | AUDIT 6 项零命中：源码层 tag / `p0-20261109` / `process.env` / `fogType` / `\.setItem\s*\(` / `assets/img/\|\.webp\|\.png`；S3 `:391-392` 复核 `OK>=6` 且 `Storage 写入 API = 0`、`图片 URL 裸引用 = 0` | 护栏项与零命中口径**不放宽**；扫描对象是**产物 bundle** `assets/p1/scene3d.js`（esbuild 会把 `scene3d-model.mjs` 等依赖一起打进去），故源码里任何被 bundle 的字面量都会命中 | **维持原值** |
| 3 | 3D 层实现约束（新增几何 / 快照） | 当前 `scene3d.jsx` 仅有 `window.__rally` 基础只读（`:79, :483`） | IMPL-1B 新增 `pickups[]` / 分叉几何 / `forkVisible` 时：① 只经只读快照投影，不新增 `race.state.*=` 赋值；② 不引入 `\.setItem\s*\(` 字样（含字符串/注释）；③ 不引入 `.webp` / `.png` / `assets/img/` 裸字面量。规避上述误命中的唯一正解是「只读 + 无裸资源字面量」 | **需改**（实现侧 · deferred） |
| 4 | 产物重建链 | 浏览器实际加载 `assets/p1/scene3d.js` **esbuild IIFE bundle**，不是 `scene3d.jsx` 源码 | 改完 `js/scene3d.jsx` / `js/scene3d-model.mjs` **必须跑 `npm run build:p1`** 重建，否则 3D 改动不生效；该命令是 `SUITES` 的 S3 首位，回归前不得跳过（`vite.config.js:113` 亦注明 `closeBundle` 只做逐字节复制，要求源码层已跑过 `build:p1`） | **需改**（流程 · 必做） |
| 5 | `vite.config.js:105-121` | `closeBundle()` 把 `assets/p1` 逐字节复制进 dist | 复制链不变；不得改为在 Vite 侧现场编译 3D 源码（会破坏 S3 静态源码形态口径） | **需改**（口径登记 · 保持现状即通过） |

> **§4 小计：需改 3 / 维持原值 2（共 5 条）**
> 说明：#3 / #4 / #5 是**实现与流程侧**的「需改」，不是改断言。B8 与 AUDIT 两条硬护栏本身**维持原值、零放宽**。

---

## 5. 三条只读白名单同步（`EXPECTED_*` ↔ `SNAPSHOT/KART/GATE_KEYS`）

当前逐字锁定（`verify_p1_visual.py:41-43` / `:198-201`；`scene3d-model.mjs:64-70`）：

```python
EXPECTED_SNAPSHOT_KEYS = ["lap","laps","zone","span","time","karts","gates"]
EXPECTED_KART_KEYS     = ["id","kind","t","lateral","drift","boost","turbo","air","yaw"]
EXPECTED_GATE_KEYS     = ["id","lap","commitT"]
```
```javascript
SNAPSHOT_KEYS = Object.freeze(["lap","laps","zone","span","time","karts","gates"]);
KART_KEYS     = Object.freeze(["id","kind","t","lateral","drift","boost","turbo","air","yaw"]);
GATE_KEYS     = Object.freeze(["id","lap","commitT"]);
```

| # | 文件:行号 | 当前期望值 | 新口径 | 判定 |
| --- | --- | --- | --- | --- |
| 1 | `verify_p1_visual.py:41` ↔ `scene3d-model.mjs:64-66` | 两侧均为 7 键 `["lap"…"gates"]` | IMPL-1B 若把 `pickups` 只读快照挂到 snapshot 顶层，**两侧必须同步按同一顺序扩键**（`==` 比较列表，顺序敏感）；`:305` `snapshotKeys:[...SNAPSHOT_KEYS]` 随之投影 | **需改**（IMPL-1B deferred） |
| 2 | `verify_p1_visual.py:42` ↔ `scene3d-model.mjs:67-69` | 两侧均为 9 键，已含 `air` | 若新增 `airMax` / `hop` / `y` 等 kart 只读字段，**两侧同步按同一顺序扩键**；`E1` 选项甲「`lift` 与 `air` 共用相位」、`airMax` 保持 `0.5s`（**已裁定、选项乙作废，见 §9.3**；QA 不擅自改） | **需改**（IMPL-1B deferred） |
| 3 | `verify_p1_visual.py:43` | `EXPECTED_GATE_KEYS = ["id","lap","commitT"]` | **三键不动**。答案域零泄露：不得把题目 / 正确项 / `sym` / `displayIpa` 投影进 gates | **维持原值** |
| 4 | `scene3d-model.mjs:70` | `GATE_KEYS = Object.freeze(["id","lap","commitT"])` | 三键不动；`:340` `gates: (state.gates||[]).map(g => project(g, GATE_KEYS))` 投影口径不变 | **维持原值** |
| 5 | `verify_p1_visual.py:198-201` | `chk("%s 只读白名单逐字锁定（snapshot/kart/gate）", state["snapshotKeys"]==EXPECTED_… and …)` | 断言形式与逐字锁定强度不变；**不改为集合比较、不改为子集判断、不豁免** | **维持原值** |
| 6 | H5 / `RECURSIVE_LEAK FORBID` | 零答案域（题目答案不进 3D 只读快照 / `__P1_SCENE__`） | 零答案域口径不变；新增 `pickups[]` / `rocks[]` 只放里程 / 车道 / 可见性，**不放任何答案字段** | **维持原值** |

> **§5 小计：需改 2 / 维持原值 4（共 6 条）**
> 前提：engineering-lead 已明确 `__rally` getter / 三条白名单同步属 **IMPL-1B**，本批不碰。故 #1 / #2 是「待实现期同步」，本轮零改动。

---

## 6. `PLR-CSEG-S2` / `A6` 与 `VISUAL_FLOW_GAIN` 防泄漏

| # | 文件:行号 | 当前期望值 | 新口径 | 判定 |
| --- | --- | --- | --- | --- |
| 1 | `verify_cseg_gate.py:61-62` | `S2 提速落地 follow=260 / listen=300`：`"speed: 260" in config and "speed: 300" in config` | **维持原值**：方案 B 下 `VISUAL_FLOW_GAIN` 只作用视觉流速 / 环境元素滚动相位，判定层 `DIFFICULTY.speed` 逐字不动；期望值、注释、常量一概不改、不豁免 | **维持原值** |
| 2 | `verify_cseg_gate.py:164` | `A6 理论口径 2×L/speed <= 150s（两档）`：`all(2*19254.50/s <= 150 for s in (260,300))` | **维持原值**：公式、L、`150s` 门槛、两档速度均不改 | **维持原值** |
| 3 | `js/config.js:45, :55` | `speed: 260` / `speed: 300` | 实测逐字未动；继续逐字不动 | **维持原值** |
| 4 | `PN-SPEED-04` / `PN-SPEED-05`（S7 承接） | 现无此断言 | **新增**防泄漏断言：断言 `VISUAL_FLOW_GAIN` 只出现在视觉/渲染层，判定层（含 `config.js` 的 `DIFFICULTY`、`race.js` 的 `odo` 步进）不得引用。**常量名已锁定 `VISUAL_FLOW_GAIN`、不再待定（§9.2）**；实际 `文件:行号` 见 §9.7 只读复核，本轮不臆造、不改脚本 | **需改**（新断言 · S7） |

> **§6 小计：需改 1 / 维持原值 3（共 4 条）**
> 历史留痕：`p1-interaction-qa.md` §2 已撤回 R4「3D 提速必使 S2/A6 FAIL」的初判，本清单与之一致——**方案 B 下两条期望值维持原样**。

---

## 7. S7 `verify_p1_interaction.py`：`PN-*` 断言名集合与编号完整性

| # | 文件:行号 | 当前期望值 | 新口径 | 判定 |
| --- | --- | --- | --- | --- |
| 1 | `音标拉力赛/verify_p1_interaction.py` | **文件不存在** | **新建**，独立承接全部 `PN-*` 断言；不得把 `PN-*` 塞进现有任一 `verify_*.py` 以免改动既有断言定义 | **需改** |
| 2 | S7 断言名集合 / 编号完整性 | 无 | 按 `p1-interaction-qa.md` §8 断言总表逐条落名，编号连续无缺号、无重名；每条给 `chk(name, ok, detail)` 完整上下文；断言名加统一前缀便于与 121 项区分 | **需改** |
| 3 | `verify_p1_gate.py:358-369` `SUITES` | 7 项 `S3→S5→S0→S1→S2→S4→S6`，合计 121 | ~~二选一待主理人拍板~~ → **已裁定（见 §9.1）：S7 不挂进 `SUITES`**，保持独立脚本 `verify_p1_interaction.py`，在既定顺序之后作为**第 8 步单独执行**；`SUITES` 7 项与 121 项断言名集合维持原值、连续两轮一致；最终回归回执须**同时**报「121 项 SUMMARY」与「S7 `PN-*` SUMMARY」两套，缺一不可 | **需改**（盘点时点；已裁定见 §9.1） |
| 4 | `result.json` / 现有 121 计数 | `121 PASS / 0 FAIL / 121 TOTAL` | **不受污染**：S7 若独立跑，其 PASS 单列披露，不并入 121；`GATE_VERDICT` 仍只在 stdout 打印，JSON 顶层无该键（R4 已登记的口径差异，本轮不改） | **维持原值** |
| 5 | 作废项（**不得写入新断言**） | — | `PN-JUMP-02`、`PN-JUMP-04/05` 二段部分、`PN-JUMP-06` 二选一、`260ms` 双沿状态机、`input.jump2`、`lastJumpAt`、`jumpEvents[]`、双击跳更高 / 两下二段跳 / 两级 `lift`、`R-2` 二选一张力、`Amazing`、随机三选一、连击偏向词 / P7、`0.9×` —— 全部**用户 2026-11-14 拍板作废、不实现** | **维持原值**（关闭状态） |
| 6 | `PN-JUMP-00` | — | **唯一 P0 单跳判据**：标准时机下单次 Space 或点击 `#jump` 跳过石头成功率 = 100%，≥1000 seed headless、沿用 `seeded()`；措辞不含「双击更高 / 二段跳是前提」 | **维持原值**（唯一准入） |

> **§7 小计：需改 3 / 维持原值 3（共 6 条）**
> 作废依据：`p1-interaction-qa.md` v1.2 §4 / §10.3；`p1-interaction-impl.md` 顶部「实施口径覆盖声明」；engineering-lead 2026-11-14 确认 `race.js` 无 `input.jump2` / 260ms 双沿 / `hop===2` / 两级 `lift`（实测 `:724` 明注一致）。
> v1.1：#3 的 SUITES 二选一已由主理人裁定「不挂进、独立第 8 步、双 SUMMARY」（§9.1）；判定列保留盘点时点的「需改」以维持 50 条统计不回溯改写，`SUITES` 实际维持原值由 §9.1 约束，冲突时以 §9.1 为准。

---

## 8. 汇总（回执口径）

| 类 | 主题 | 需改 | 维持原值 | 合计 |
| --- | --- | ---: | ---: | ---: |
| §1 | BD-1 五 + B3 七 → 并集 8 文件重锚 | 3 | 6 | 9 |
| §2 | `≤180s` 门槛 / S4 取时正则 / 重跑基线 | 2 | 4 | 6 |
| §3 | `SRC_TAG_COUNT=46` 与统一 bump 落点 | 9 | 5 | 14 |
| §4 | B8 静态禁写 + `build-p1.mjs` 零命中护栏 | 3 | 2 | 5 |
| §5 | 三条只读白名单同步 | 2 | 4 | 6 |
| §6 | `PLR-CSEG-S2 / A6` + `VISUAL_FLOW_GAIN` 防泄漏 | 1 | 3 | 4 |
| §7 | S7 `PN-*` 断言名集合与编号完整性 | 3 | 3 | 6 |
| **合计** | | **23** | **27** | **50** |

> **统计口径（v1.1）**：上表 50 条（23 需改 / 27 维持）是 **QA-GATE-MAP 盘点时点快照**，已由 team-lead 采纳，v1.1 裁定回填**不回溯改写本表**。三项待拍板项的最终执行口径见 §9（已裁定）；执行时若盘点判定与 §9 裁定不一致，**以 §9 为准**并在回归回执中单列披露。50 条总数不变。

### 8.1 附录（不计入 7 类统计）

- `verify_p1_gate.py:48` docstring 仍写「本文件当前唯一可执行行为：静态自检清单完整性 → 打印 → exit(2)」，与同文件 `SUITES` / REAL_RUN 结构不一致 → **维持（本轮不改门控说明文字）**，仅登记为文档口径差异，留待后续文档修订统一。
- `PN-ROCK-06` 改动前超标留痕 FAIL：旧 `gate-logs/S4.log` worst `rock=7/4`、normal `0/5/3/6` 全部 >2，**禁止悄悄改绿**，回归须保留该历史证据。
- `PN-NPC-02` 里程差 / 横向间距 / 重合帧阈值待实跑标定；`v_i ≥ 0.94 · v_player_now` 已写死，**不得自行放宽**；若 headless 达不到只在风险条目留痕、不回退。
- ~~E1 §A2 选项甲 / 乙（是否延长 `airMax`）待主理人拍板~~ → **已裁定，见 §9.3**：取选项甲、`airMax` 保持 0.5s，乙案作废。
- ~~260ms 状态机残留冲突（R-5）留主理人统一~~ → **已闭环**：`p1-interaction-impl.md` 顶部「实施口径覆盖声明」已作废 §A2 / §2.2 / §A4 / §3 PM-3 / §4.2；`p1-interaction-qa.md` v1.2 已作废 `PN-JUMP-02/04/05/06` 与 R-2。
- **`PN-ROCK-05a` 措辞已裁定（§9.4）**：`state.pickups` 中 rock 条目配额 ≤2（实跑恰 2 条），非「整局出现 / 交互次数 ≤2」；跨圈重现为既定语义、`rockHits` 整局累计不复位、封顶后静默越过，**不得判 FAIL**。
- **BD-2 / 新基线已裁定（§9.4）**：`verify_p0_gate.py:171` 的 `[\d.]+` 维持不改；只改 `verify_p1_gate.py:396`；`≤180s` 门槛不变、不沿用 `174.57s`，新基线 `170.72s`。
- **IMPL-1B 落盘事实与回归风险（§9.6 / §9.7）**：工程侧已落盘，但 `verify_p1_visual.py:41-43` 仍为旧期望 → S5 白名单断言**必 FAIL**；`js/render.js` 属 B3 锚定 7 文件，须纳入 §1 重锚。deferred 状态按 team-lead 边界保持。

---

## 9. 主理人裁定回填（QA-GATE-MAP-RULING · 2026-11-14）

> 本节是 **v1.1 裁定层**，优先级高于本清单全部「待拍板」表述。三项待拍板项逐条标为「已裁定」，并并入两条既有裁定。
> §1–§8 的 50 条盘点快照不回溯改写；**执行口径以本节为准**。
> 本轮只改本清单文件；`verify_*.py` / `result.json` / 产品代码 / 其余四份规格零改动；未跑门控、未启浏览器、未 commit / push。

### 9.1 【已裁定】S7 不挂进 `SUITES`，独立脚本作为第 8 步
`verify_p1_gate.py:358-369` 的 `SUITES` **保持不变**（7 项 `S3→S5→S0→S1→S2→S4→S6`、合计 121）。S7 维持独立脚本 `音标拉力赛/verify_p1_interaction.py`，作为该既定顺序之后的**第 8 步**单独执行；S5 真实 Chromium WebGL 取证仍须前置、浏览器门控不并行，顺序硬约束不放宽。理由：保住权威门控 **121 项断言名集合连续两轮一致、不污染计数**。
**回归回执硬要求**：最终回归回执须**同时**报「121 项 SUMMARY」（`verify_p1_gate.py` REAL_RUN）与「S7 `PN-*` SUMMARY」（`verify_p1_interaction.py` 独立实跑）**两套，缺一不可**；S7 的 PASS 单列披露、不并入 121，`result.json.not_covered` / `manual_signoff` 人工过眼同样不冒充 PASS。`GATE_VERDICT` 仍只在 stdout 打印、JSON 顶层无该键（R4 口径差异，本轮不改）。

### 9.2 【已裁定】`VISUAL_FLOW_GAIN` 常量名锁定，不再待定
常量名即 `VISUAL_FLOW_GAIN`，不再待 IMPL-1B 同步。硬约束：① **零进** `race.js` / `track.js` / `config.js` / `headless_laps.mjs`；② 只作用渲染层纯环境元素滚动相位（中央虚线 / 贴地起跳标线 `lineDashOffset`），车体 / 门位 / 分叉 / 石头严格绑判定 `t`，零写回 `odo` / `lateral` / `g.line` / `diff.speed`；③ `opts.worldScale = 0.008` 不变；④ `DIFFICULTY.speed` `260 / 300` 逐字不动 → §6 #1/#2/#3 与 `PLR-CSEG-S2` / `A6` 期望值维持原样。
`PN-SPEED-04` / `PN-SPEED-05` 由 S7 独立承接（§9.1），断言「判定层零引用 + 只作用视觉相位」，不污染 121 计数。**实际 `文件:行号` 已由 QA 只读复核登记于 §9.6**；IMPL-1B 合并任务回填 §4 / §6 时以 §9.6 为准，QA 不臆造行号。

### 9.3 【已裁定】E1 §A2 取选项甲，`airMax = 0.5s`，选项乙作废
`airMax` **保持 0.5s**；选项乙（延至 0.99s）作废，避免卡丁车「起飞」失真。`lift(p) = 0.55 · sin(π·p)`、`p = 1 - air/airMax`，与 `air` **共用相位、零漂移**；单级 lift（无两级 / 无 `hop===2`）；容错由**滞空见证式 + 贴地起跳标线**承接，不靠延长滞空。IMPL-1A 已按 `airMax = 0.5` 落盘，IMPL-1B 派单已写死单级 lift，**不再是待拍板项**。QA 不擅自改 `airMax`、不冒充 PASS。

### 9.4 【并入两条既有裁定】`PN-ROCK-05a` 措辞 + 取时正则 / 新基线
- **`PN-ROCK-05a` 措辞**：`state.pickups` 中 rock **条目配额 ≤2**（IMPL-1A 实跑恰 2 条），**不是**「整局出现次数 / 交互次数 ≤2」。跨圈复位只清 `taken/armed/cleared`，`rockHits` 整局累计、跨圈不复位，达 `rockBudget = 2` 后静默越过；**跨圈重现为既定语义，不得判 FAIL**。裁定原文见 `p1-interaction-impl.md` 顶部覆盖声明。`PN-ROCK-04` / `05b` / `06` 三条维持不动，`PN-ROCK-06` 改动前超标留痕 FAIL 的历史证据禁止悄悄改绿。
- **取时正则 / 新基线**：采纳 QA-GATE-MAP 新发现① —— `verify_p0_gate.py:171` BD-2 的 `[\d.]+` 已兼容 <100s，**维持不改**；只需改 `verify_p1_gate.py:396` 的 `1[0-7]\d\.\d\d`。`≤180s` 门槛不变（§2 #3/#5/#6 三条维持原值）；基线**不沿用 `174.57s`**，新实跑最慢 **`170.72s`**（IMPL-1A / IMPL-1B 两侧自报一致；QA 本轮未实跑复核，最终回归仍须重跑 11 场确认、不冒充 PASS）。`174.57s` 仅作历史留痕保留在 §2 #2 / §8.1，不作回归判据。

### 9.5 【已裁定 · 边界】deferred 项保持，勿提前动脚本
按 team-lead `QA-GATE-MAP-RULING` 边界：§4 #3 / §5 #1/#2 的「需改（deferred）」在 **「重锚 + S7 编写 + 最终回归」合并任务派单前保持 deferred**，本轮不提前改任何脚本、不改 `verify_p1_visual.py`、不跑门控。
**事实更正**：派单登记「IMPL-1B getters / 白名单扩展尚未落盘」，但 engineering-lead 2026-11-14 同步已落盘、QA 只读复核属实（详见 §9.6）。**deferred 是流程状态而非落盘状态**——解除须由 team-lead 合并任务派单，不由 QA 自行改判。

### 9.6 IMPL-1B 落盘事实登记（engineering-lead 同步 + QA 只读复核 · 本轮零改动）

| 项 | 只读复核到的磁盘真值（2026-11-14） |
| --- | --- |
| `VISUAL_FLOW_GAIN` 落点 | `js/render.js:8` 本地 `const = 1.6`（消费 `:307` / `:380` 的 `ctx.lineDashOffset`）；`js/scene3d-model.mjs:34` `export const = 1.6`（`meta.visualFlowGain` 在 `:398`）；`js/scene3d.jsx:27/60/293-294/484` import + 消费 + `STATE` 投影。零进四判定核心文件，与 §9.2 硬约束一致 |
| `__P1_SCENE__` 只读观测点 | `js/scene3d.jsx:34/59-61/297/379/485-487`：`visualFlowGain` / `flowPhase` / `forkFlareMax` / `hRock` / `jumpPeak` / `pickupKeys` 等；`:381-383` pickups 只读投影消费 |
| 白名单新键序（**逐字**） | `SNAPSHOT_KEYS` = `["lap","laps","zone","span","time","karts","gates","pickups"]`（8 键，`:83-85`）；`KART_KEYS` = `["id","kind","t","lateral","drift","boost","turbo","air","airMax","hop","yaw"]`（11 键，`:86-88`）；`GATE_KEYS` 三键一字不动（`:89`）；新增 `PICKUP_KEYS` = `["id","kind","t","lateral","taken","armed","cleared"]`（7 键，`:91-93`）；投影见 `:396-397` / `:432-435` |
| 产物重建链 | 工程侧已跑 `npm run build:p1` → `assets/p1/scene3d.js` 1 169 114 bytes、AUDIT 6 项零命中；未引入 `.webp\|.png\|assets/img/\|fogType\|.setItem(` 字面量（与 §4 规避口径一致）。三项自测 18 PASS / build OK / headless 11 场 ALL PASS 最慢 `170.72s` |

### 9.7 回归风险预警（须在合并任务处理，本轮不改任何脚本）

1. **【必 FAIL】`verify_p1_visual.py:41-43` 仍是旧期望**：`EXPECTED_SNAPSHOT_KEYS` 7 键、`EXPECTED_KART_KEYS` 9 键、`EXPECTED_GATE_KEYS` 3 键；`:198-201` 逐字锁定 `chk` 用 `==` 比列表 → 与新的 8 / 11 键**必然不等**，S5 六场景白名单断言必 FAIL。须按 §9.6 **同序**重锚两组期望值（`GATE_KEYS` 三键不动）。
2. **【断言缺口】缺 `EXPECTED_PICKUP_KEYS` 与对应 `chk`**：新增 `PICKUP_KEYS` 七键，而 `verify_p1_visual.py` 目前只比较 snapshot/kart/gate 三组、无 `state["pickupKeys"] == …` 断言。若要覆盖 `pickups` 只读投影须**新增**期望与 `chk`；属 S5 63 项内扩充，**不得污染 121 计数口径**，是否纳入待主理人定。
3. **【重锚范围需扩】`js/render.js` 属 B3 锚定 7 文件之一**（`verify_p1_gate.py:451-453`），亦在 `SRC_SCAN_FILES` / `SRC_WHITELIST` 9 文件内（tag 1 处）。`VISUAL_FLOW_GAIN` 落 `render.js:8` 会改变其 sha256 → **§1 并集 8 文件重锚必须把 `render.js` 一并纳入**（此前仅按 `race.js` / `config.js` 变动计）；tag bump 时 `render.js` 的 1 处也须同步。
4. **【口径不变】** §9.6 的事实登记不改变 §1–§8 的 50 条统计；§4 / §5 deferred 状态不变；`verify_p1_gate.py:396` 取时正则、BD-1 / B3 重锚、tag bump 均留待合并任务。

### 9.8 裁定状态总览

| # | 待拍板 / 并入项 | 状态 |
| --- | --- | --- |
| 1 | S7 是否挂进 `SUITES` | **已裁定**（§9.1）：不挂，独立第 8 步，双 SUMMARY |
| 2 | `VISUAL_FLOW_GAIN` 常量名 | **已裁定**（§9.2）：锁定、不再待定；落点见 §9.6 |
| 3 | E1 §A2 选项甲 / 乙、`airMax` | **已裁定**（§9.3）：选项甲、`0.5s`、选项乙作废 |
| 4 | `PN-ROCK-05a` 措辞 / 跨圈重现 | **已并入**（§9.4）：条目配额 ≤2，跨圈重现不判 FAIL |
| 5 | BD-2 / S4 取时 / 新基线 | **已并入**（§9.4）：BD-2 维持、只改 S4、基线 `170.72s` |
| 6 | IMPL-1B 落盘 / deferred | **已登记**（§9.5 / §9.6）：事实已落盘，deferred 流程状态保持 |

---

*P1 交互 · 门控重锚只读盘点清单 v1.1 · QA-GATE-MAP（50 条）+ QA-GATE-MAP-RULING 裁定回填 · 严守真 · 2026-11-14*
*v1.0 为只读盘点快照（50 条 / 23 需改 / 27 维持）；v1.1 增量回填三项裁定、并入两条既有裁定，并登记 IMPL-1B 落盘只读复核与回归风险预警；统计不回溯改写，执行口径以 §9 为准。*
*本清单为只读盘点产物；所有「需改」项均为待执行动作，本轮未改任何 `verify_*.py` / `result.json` / 产品代码 / 其余四份规格，未跑门控、未启浏览器、未 commit / push。*
