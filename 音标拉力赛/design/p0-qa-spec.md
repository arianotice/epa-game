# 路线 B · 门控重定义规格（P0 切片 · Vite + React + R3F）

> **文档性质**：`#20` / quality-lead（严守真）独占产出。**规格 + 脚本草案，不是已执行的门控、不是产品代码变更**。
> **唯一权威规格依据**：`design/p0-slice-spec.md`（team-lead 综合用户四项拍板写下的实施规格，§1 三条裁决 / §2 P0 范围 / §3 T1–T5 风险 / §4 分派）。凡与本文冲突，以 `p0-slice-spec.md` 为准。
> **其它依据**：`design/stage-delivery-2026-11-09.md` §2.1（fan.mp3 瞬态事实）与 §3（R1–R11 风险表）；`design/hud-final-qa-report.md`（质量门 🟢 PASS、C1 CLOSED、五套门控 110/110 + HUD 12/12 的最终基线）；`design/hud-qa-plan.md`（串行跑法、四项错误计数、资源按字节校验、CONCERNS 登记格式）；五套验收脚本 `chk(...)` 断言编号全表（本轮只读抓取）。
> **质量门性质**：advisory（建议性）。QA 给出 PASS / CONCERNS / FAIL 判定与阻塞项，**最终放行与发布签字由用户决定**；QA 不替用户拍板、不代替签字。
> **本轮边界（硬约束）**：**只出规格与脚本草案，不实跑门控、不改任何现有验收脚本、不碰产品代码**。唯一写入物 = 本文件 `design/p0-qa-spec.md`。脚本草案以 §10 内嵌伪代码形式给出，**不落任何 `.py` / `.mjs` 可执行文件**，不得覆盖 `verify_cseg_gate.py` / `verify_cseg_ui.py` / `verify_fresh_gate.py` / `verify_c08_gate.py` / `verify_hud_spec.py`。不部署、不上线、不 commit、不建 git 仓库。
> **生效时机**：待 `#19`（engineering-lead 落地 P0）产物定型、且 §9 实跑前置信息齐备后，由主理人另行通知实跑。本规格不预设任何 P0 产物细节（T1 方案由 engineering-lead 实测给出，规格不臆造）。

---

## 0. 规格定位与红线

### 0.1 用户拍板（照抄 `p0-slice-spec.md` §0，不重新论证）

| 决策 | 结果 | 对门控的含义 |
| --- | --- | --- |
| 技术路线 | **路线 B · Vite + React + R3F**（推翻路线 A） | 引入构建层、vendor 层、dev server，现有五套门控的「自起 in-process HTTPServer 直服源码」模型部分失效 |
| 落地形态 | **直接改造 `音标拉力赛/` 主站**，Vite 接管；2D 保留为 L0 降级层 | 判定核心源码逐字不改，但**服务模型与资源形态改变** |
| 验收基线 | **允许重定义门控**（不再要求 110 项原样全绿） | 允许改**测法**、改**扫描根**、改**入口**；**不允许**改覆盖面 |
| 缓存治理 | **46 + N 各自唯一**：2D 遗产层 46 一组、构建/vendor 层 N 一组 | 双层断言、互不混算；原「恰好 46」对 `dist/` 不再生效 |
| three | **0.186.1** | 产物层版本钉定断言 |
| ADR-2 | 硬约束，不放宽、无需拍板：Rapier 只进视觉层，绝不替换 `odo/lateral + g.line` 判定 | 判定核心零改动（§1 K1） |
| P0 范围 | 最小 R3F 探针（**默认关闭、可一键关回 2D**） | 新增探针域断言（§3.3） |

### 0.2 三条裁决 → 本规格的红线映射

| 裁决 | 本规格落点 | 一句话红线 |
| --- | --- | --- |
| 裁决 1 · 判定核心零改动 | §1 K1、§4.3 保留域、§6.3 覆盖映射 | `race.js` / `track.js` / `config.js` / `headless_laps.mjs` **原路径原命令**仍是 Go/No-Go 硬条件，不因「门控重写」绕过 |
| 裁决 2 · 46 + N 准确含义 | §2 全节 | 源码层 46 与产物层 N **各自唯一、互不混算**；`dist/` 不适用「恰好 46」 |
| 裁决 3 · 重定义 ≠ 降级 | §0.4、§1 全节、§6.3 | 五类断言**逐条保留、缺一不可**；不得删断言、放宽阈值、跳过浏览器实跑、把 FAIL 改 NOTE |

### 0.3 覆盖度守恒律（本规格最重要的机制）

> 用户允许重定义的是**测法**，不是**覆盖面**（`p0-slice-spec.md` §1 裁决 3 逐字）。为防止「重写即缩水」，本规格设一条硬机制：

**K1–K5 覆盖映射表（§6.3）必须满格**：`p0-slice-spec.md` §1 裁决 3 列明的五类断言，每一类都必须在新门控里有**明确的 `chk(...)` 承接**，且 PASS 判据不得弱于 §1 本文给出的判据。任何一条新门控断言被删除 / 降级 / 跳过时，须在映射表对应格写明 `替代 = <新编号>`；**出现空格 = 规格不接受，判 FAIL**。

**守恒式**：`覆盖(K1..K5) ⊆ 覆盖(新门控)` 且 `∀ 原断言 a ∈ 110+12: (a 保留) ∨ (∃ 替代断言 a' 且 strength(a') ≥ strength(a))`。

### 0.4 明确禁止项（照抄裁决 3 并具体化）

| # | 禁止 | 具体形态（本轮高发） |
| --- | --- | --- |
| X1 | 删断言 | 因 `dist/` 里 `?v=` 消失就删掉 tag 唯一性断言；因 Vite 注入资源多就删掉零裸引用断言 |
| X2 | 放宽阈值 | 把 `== 46` 改成 `>= 40`；把 `len(diff)==0 + sha_equal` 改成 `diff<5`；把 `finishTime<=180s` 放宽；把 `pageerror==0` 改成 `<=2` |
| X3 | 跳过浏览器实跑 | 因「Vite 构建成功」就用静态检查替代真实 Chromium 冒烟；因 WebGL 探针难测就只看 build 日志 |
| X4 | FAIL 改 NOTE | 把「同源真实失败 ≠ 0」登记为 CONCERNS 放行；把探针默认关闭失败登记为「建议项」 |
| X5 | 借「重定义」偷换语义 | 把「源码层 46 唯一」偷换成「两层合计唯一」；把「两层互不混算」偷换成「只锁产物层」 |
| X6 | 用外链掩盖同源失败 | 把 `fonts.gstatic.com` 失败计入豁免后，顺手把 `127.0.0.1` 的 404 也一起豁免 |

---

## 1. 五类不可降级断言（逐条：原测法 → 新测法 → PASS 判据）

> 每条给出**新测法**（可执行、浏览器实跑）与**PASS 判据**（硬条件）。编号 `K1–K5` 与 `p0-slice-spec.md` §1 裁决 3 一一对应；新门控断言编号见 §6。

### K1 · 判定核心确定性（两圈 / 门线 `g.line` / 听音题正确性 / 11 场 headless ≤180s）

**原测法**：`verify_cseg_gate.py` S1–S8 / S13 / A0–A6 静态源码字面量 + Node 子进程跑 `headless_laps.mjs`；`verify_cseg_ui.py` U6 / U8 真实 DOM 建门与三题型；`minimap_model.test.mjs` T0–T7 纯函数单测。

**为什么必须保留**：ADR-2 硬约束 + 裁决 1。R3F 组件只能通过 `snapshot()` **只读**判定结果；判定不得进 React state、不得由 rAF 驱动、不得移植 TS。

**新测法（三路并行，缺一不可）**：
1. **源码零改动证明**：对 `js/race.js`、`js/track.js`、`js/config.js`、`js/main.js`（主循环）、`js/headless_laps.mjs` 逐文件取 `sha256`，与 `.workbuddy/backups/` 中 **P0 改动前全量快照**（`p0-slice-spec.md` §2 第 6 条要求 engineering-lead 落盘）对应条目比对；并逐字核对 `odo/lateral`、`g.line = startOdo + lineT·L`、`buildGates()`、`judge()`、`beginDecide()`、`hitsLane()`、`TUNING.laps=2`、follow 260 / listen 300 仍在**原生 ESM 文件**中（非 TS、非打包产物、非 React state）。
2. **原路径原命令实跑**：`node js/headless_laps.mjs`（与 #5 完全相同的 cwd / 命令），解析 11 场输出；同时在 **Vite dev** 与 **Vite build preview** 两种服务模式下各跑一次，确认页面内 `window.__rally` 仍暴露只读 getter、`race` 判定结果与原路径一致。
3. **浏览器内判定一致性**：真实 Chromium 下用 `window.__rally.step(n)` 显式驱动，核对 `lineT=[0.24,0.68,1.24,1.68]`（容差 `1e-9`）、两圈同 `commitT` 的 `line` 差 = `L`、`nextGate.lap`、quiz 三题型题干不泄答案（沿用 U8 / H10 行为断言，不放松）。

**PASS 判据（硬）**：
```
sha256(判定核心 5 文件) == P0 前快照对应条目          # 逐字不改
node js/headless_laps.mjs → 11 场 ALL PASS 且 max(finishTime) <= 180.0s   # 原路径原命令
dev 与 build 两模式下：__rally 可用、两圈 line 差 = L、lap 序列一致、三题型正确
R3F 探针开启时：snapshot() 只读、不出现 odo/lateral/g.line 的写入点与 rAF 判定驱动
```
> **禁止**：把 `max(finishTime)<=180s` 放宽；用「构建通过」替代 11 场实跑；用 `dist/` 内的打包副本替代原路径 `node js/headless_laps.mjs`。

### K2 · 跨站 `localStorage['ipa-quest-v1']` 单键保真（C08 白名单、`rally` 嵌套字段不互相覆盖）

**原测法**：`verify_c08_gate.py` D1.1–D6.2（迁移 / 幂等 / 跨站 last-write-wins / 并集 / storage 事件 / gems delta）、`verify_cseg_ui.py` U10/U11、`verify_fresh_gate.py` F11a/F11b、`verify_hud_spec.py` H12（`rally` 字段开赛前后逐字段相等 + 零写盘）。

**为什么必须保留**：两站共享 `localStorage` 单键 `ipa-quest-v1` 的 `rally` 嵌套对象；`dist/` 形态下**两站是否同源直接决定该机制是否成立**（T3）。Vite 接管若改变 origin，共享即失效——这是路线 B 最隐蔽的回归面。

**新测法**：
1. 在 **dev** 与 **build** 两模式下，把 `verify_c08_gate.py` 的 D1–D6 全套场景（老存档迁移、`v1.bak` 逐字节、幂等、`rawHasV2`、跨站不覆盖、并集、storage 事件、gems 交错 delta）用**新的服务入口 URL** 重放，断言逻辑与期望值**逐字不变**。
2. 新增同源判定（§3.4）：两站 URL 的 `location.origin` 相等；在拉力赛侧写 `rally.gems/shields/EP02/ownedPaints/howSeen/unlocked`，在大闯关侧读回**逐字段相等**，反之亦然。
3. H12 的零写盘与字段守恒在两模式下重放：hook `Storage.prototype.setItem`，`step(300)` 增量 `0`；`rally.unlocked/maps/EP02` 开赛前后逐字段相等。

**PASS 判据（硬）**：
```
dev 与 build 两模式：D1–D6 全 PASS（期望值不变）
origin(拉力赛) == origin(大闯关)  且 跨站读写 rally 字段逐字段相等、无覆盖
零新增 localStorage 字段（键集合 == 基线键集合，P0 不新增字段）
HUD/探针路径 setItem 增量 == 0
```
> **禁止**：因「dist 下两站不同源」就把 D1–D6 标 NOTE 放行；因探针引入开关而默认新增 localStorage 字段（开关须用 query param / 内存 flag，见 §3.3）。

### K3 · 美式 IPA 单一显示源 `window.IPA_DISPLAY` 与 `sym` 稳定键

**原测法**：`verify_fresh_gate.py` F1/F1b/F2/F5、F9a/F9b（`U11=ɜr`）、`verify_c08_gate.py` D7.4、`verify_cseg_gate.py` B2/B9（`ipa-display.js` 全文未动 / `sym` 稳定键）、`verify_hud_spec.py` H11（`IPA_DISPLAY.U11.displayIpa==='ɜr'`）。

**为什么必须保留**：`ipa-display.js` 是**普通同步 script**，依赖「普通脚本先于 module 执行」时序（T2，`index.html:170-172` 实证）；Vite 处理 HTML script 后若时序变化，48 卡面与答案显示失效。

**新测法**：
1. **时序断言（新增，§3.2）**：dev 与 build 两模式下，在 module 执行**之前**探测 `window.IPA_DISPLAY` 已就绪（用 `page.add_init_script` 或在 module 首行打点），且 `ipa-display.js` 仍以**非 module、无 defer/async** 的同步 script 加载；若 Vite 改写为 module，须证明等价时序（`.mjs` 注入顺序 + `window.IPA_DISPLAY` 在任何消费者读取前已定义）。
2. **单一显示源**：`window.IPA_DISPLAY.U11.displayIpa === 'ɜr'`；48 卡面 `.sym` 大字全为美式、无 `ː/ɒ/əʊ/ɪə/eə/ʊə`；`ipa-display.js` 与权威表 `sha256` 相对 P0 前快照**逐字节全等**（B9 口径）。
3. **`sym` 稳定键**：F1b `ː` 仍只出现在 10 行 `sym` 稳定键；F5 逻辑枚举键锁定 + D01–D05 显示文案在场；**禁止**用 `displayIpa` 作键（§1 单向铁律）。
4. **跨目录按字节送达**：`ipa-display.js` 在 dev / build 下按 §3.1 四重口径送达全等。

**PASS 判据（硬）**：
```
dev 与 build：module 执行前 window.IPA_DISPLAY 已就绪 且 同步 script 时序成立
IPA_DISPLAY.U11.displayIpa === 'ɜr'
ipa-display.js sha256 == P0 前快照（逐字节未动）
48 卡面美式、sym 稳定键 10 行、无英式符号残留
```
> **禁止**：把 `ipa-display.js` 打进 bundle 后不验证时序就判 PASS；把「显示源未就绪」的单次 console 报错登记为 NOTE 放行。

### K4 · quiz 答案零泄露（83 词全表 + 4 字段名不出现在 HUD DOM）

**原测法**：`verify_hud_spec.py` **H5**（主理人 #5 裁决口径）+ H6（`minimapModel` 字段白名单）+ H8（S2 无指向性）+ `verify_cseg_ui.py` U8（题干不泄答案）+ `verify_cseg_gate.py` S11。

**口径铁律（照抄 #5 裁决，本规格明确「不退回」）**：
- 检测面 = **`mm.textContent` + 遍历后代元素的所有属性值**（`alt` / `aria-label` / `title` / `data-*` 全量 `[name, value]` 的 value，不缩小）；
- **不检测 `mm.innerHTML` 源码字面量**——`<span id="minimap-lap">` 标签名中的 "span" 含 `pan`（pen/pan 词对，在 83 词全表内）会造成**测试脚本假阳性**；`innerHTML` 仅作诊断证据、不计判定；
- 词表 = `allWords()` **83 词全表**（浏览器内 `await import('/音标拉力赛/js/config.js?v=TAG')` → `cfg.allWords()`，不缩小、不过滤短词）+ `correctLateral/spoken/left/right` **4 字段名** + 4 门 IPA/displayIpa；
- **防放宽守卫**：`len(vocab)==83 and len(set(vocab))==83` 本身是硬判据；仍是 `chk()` 硬断言（非 warn）；字段名一个不少；
- 禁用属性名 `data-(lane|correct|side|answer|left|right|word|ipa|spoken)` 零命中；中文答案域关键字 `答案/正确` 零命中。

**新测法（路线 B 增量，不回退）**：
1. **2D L0 主形态**：H5/H6/H8 在 dev 与 build 两模式下原样重放，检测面口径与词表**逐字不变**。
2. **R3F 探针（新增检测面）**：探针开启时，把 **overlay 根节点及其后代**纳入同一检测面（`overlay.textContent` + 后代所有属性值）；断言 83 词全表 + 4 字段名 + IPA 零命中，禁用 `data-*` 零命中。**WebGL/canvas 不产生 DOM 文本，但 overlay 的 DOM 属性、ARIA label、React `data-*`、props 序列化到 DOM 的属性全部要扫**；若探针把 `snapshot()` 里的任何答案域键写进 `data-*`/`aria-*`，判 FAIL。
3. **`snapshot()` 接口白名单（新增）**：若 R3F 组件消费 `snapshot()`，递归键名不得出现 `correctLateral/spoken/left/right/pairKey/qType/options/displayIpa/answer/correct/word/ipa`（沿用 H6 `FORBID_KEYS` 口径，键名匹配、不误伤值）。
4. U8 三题型题干不泄答案、S11 word 题不泄答案，在两模式重放。

**PASS 判据（硬）**：
```
vocab_ok := (len(vocab)==83 and len(set(vocab))==83)
2D 与探针两种形态：textContent + 后代所有属性值 对 91 token 零命中、禁用属性名零命中、中文关键字零命中
minimapModel / snapshot 递归键名零禁用键、nextGate 键集合精确
探针开启不新增任何答案载体 DOM 属性
```
> **禁止**：把检测面退回 `innerHTML`（会引入 `<span` 假阳性，属**测试脚本缺陷**而非产品缺陷，#5 已裁决）；缩小 83 词表；只查部分词；把零命中断言降级为 warn/NOTE；因探针是 canvas 就跳过 DOM 属性扫描。

### K5 · 四项错误计数 `pageerror / console_error / requestfailed / bad_status` 归零口径

**原测法**：`verify_cseg_ui.py` U1/U12、`verify_fresh_gate.py` F11d、`verify_c08_gate.py` D7.5、`verify_hud_spec.py` H12（含 `ERR_ABORTED` 单列 + 明细分类）。

**口径（沿用 `hud-qa-plan.md` §3，扩展 Vite 新增类别）**：

| 类别 | 判定 | 计入硬失败 | 要求 |
| --- | --- | --- | --- |
| `pageerror` | 页面未捕获异常 | **是** | `= 0` |
| `console_error` | `console.error` 文本 | **是** | `= 0` |
| `bad_status` | HTTP `status >= 400` | **是** | `= 0` |
| `requestfailed` — `net::ERR_ABORTED` | reload / 导航主动取消 | **否**，单列披露 | 允许 > 0；必须打印去重 URL 样例 |
| `requestfailed` — **同源**（`127.0.0.1` / `localhost`）非 `ERR_ABORTED` | **真实网络失败** | **是** | `= 0`（含 `ERR_CONNECTION_REFUSED`，见 §5.3 瞬态口径） |
| `requestfailed` — **外链**（`fonts.googleapis.com` / `fonts.gstatic.com`）非 `ERR_ABORTED` | 环境相关 | **否**，NOTE 披露 | 打印明细；资源送达另由 §3.1 字节比对覆盖，**不信状态码**（T5） |
| **Vite 新增** — `@vite/client` / HMR WebSocket / `ws://` 连接 | 开发服务器机制 | **否**，单独披露 | 必须与实际同源内容资源失败**分开统计**；不得用它掩盖同源失败（X6） |
| **Vite 新增** — `/@fs/` `/@id/` `/node_modules/.vite/deps/` 等 dev 内部路径 | dev 内部资源 | 按同源口径 | 若真失败（非 ABORTED）计入同源真实失败 = 产品/构建问题 |

**汇总必须单列披露（逐字）**：
```
requestfailed 明细：总计 N | ERR_ABORTED(主动取消,不计失败) N | 同源真实失败 N | 外链环境失败 N | Vite 机制项 N
```
并打印 `ERR_ABORTED` 样例 URL、`同源真实失败明细`、`console.error 文本`、Vite 机制项明细。

**PASS 判据（硬）**：
```
errs_strict_ok = (pageerror==0 and console_error==0 and bad_status==0 and len(REAL)==0)
REAL = 同源非 ERR_ABORTED 失败（含 ERR_CONNECTION_REFUSED，按 §5.3 处置后仍须为 0）
```
> **禁止**：把 `ERR_ABORTED` 混进 FAIL 计数；把它静默吞掉不披露；把同源 404 / `ERR_CONNECTION_REFUSED` 计入外链豁免；因 Vite HMR 噪声就整体关掉 `requestfailed` 监听。

---

## 2. 双层缓存断言（46 + N 各自唯一、互不混算）

### 2.1 源码层（2D 遗产层）：`hud-20261108` 唯一且恰好 46

**依据**：`p0-slice-spec.md` §1 裁决 2 —— 源码层 46 处字面量**保留、不删除、不批量替换**，作为 2D 主形态与四套历史门控的溯源标识。

**新测法**：对**两站 2D 遗产层的确定文件集**（沿用 `hud-qa-plan.md` §5.1 的 9 文件分布：大闯关 `index.html` 17 / `atlas.js` 6 / `level.js` 1 / `map.js` 3 / `story.js` 2；拉力赛 `index.html` 7 / `main.js` 7 / `race.js` 2 / `render.js` 1 = 46）扫描 `\?v=([A-Za-z0-9\-]+)`。

**PASS 判据（硬）**：`Counter(源码层 tag) == {'hud-20261108': 46}`，**唯一值、恰好 46**；`config.js CACHE_TAG === 'hud-20261108'`；`headless_laps.mjs:19` 与四套脚本 `TAG` 常量同步。

### 2.2 产物层（构建/vendor 层）：`vendor.manifest.json` + `VENDOR_TAG` 单独锁 N 处

**依据**：裁决 2 —— Vite content-hash 文件名 + 一份 `vendor.manifest.json`（three / R3F / drei / postprocessing 及后续 GLB）构成 N 处独立清单，**单独一个 `VENDOR_TAG`**。

**新测法**（N 与清单 schema 待 §9 产物信息齐备后填入，本规格不预设）：
1. 读 `vendor.manifest.json`：断言 `three` 版本 `=== '0.186.1'`，且 `@react-three/fiber` / `drei` / `@react-three/postprocessing` 版本在**已核实的 peer 上界**内（版本值由 #19 提供）。
2. 断言 `VENDOR_TAG` 为**单一值**、与源码层 `hud-20261108` **不同值**（双命名空间）；产物层内所有 `VENDOR_TAG` 出现处计数 = N，**唯一值、恰好 N**。
3. 断言 `dist/` 中 content-hash 文件名与 `vendor.manifest.json` 条目一一对应，无孤儿产物、无清单外 vendor。
4. `VENDOR_TAG` 不得出现在源码层 46 的扫描结果里（防混算）。

**PASS 判据（硬）**：
```
产物层 tag 直方图 == {VENDOR_TAG: N}（唯一值、恰好 N，N 由产物定型后填）
VENDOR_TAG != 'hud-20261108'
vendor.manifest.json 条目与 dist/ 产物双向一一对应；three==='0.186.1'
```

### 2.3 两层互不混算（守恒式）

```
scan_source  ∩  scan_dist  == ∅            # 扫描根物理隔离（见 §2.6）
count(源码层) == 46  且  set == {'hud-20261108'}
count(产物层) == N   且  set == {VENDOR_TAG}
46 + N 不得合并统计、不得互相顶替、不得「合计唯一」了事
```
**禁止**（X5）：把源码层 46 与产物层 N 相加后判「合计唯一」；只锁产物层而放弃源码层 46；因 `dist/` 里 `?v=` 消失就删除源码层断言。

### 2.4 S17 / F8a / H11 原「恰好 46」在 `dist/` 上不再生效 —— 边界与替代判据

| 原断言 | 原判据 | 在 `dist/` 上的边界 | **替代判据** |
| --- | --- | --- | --- |
| `verify_cseg_gate.py` **S17** | `os.walk(QUEST, RALLY)` 扫 `.html/.js/.css` → `set(tag_counts)=={TAG} and count==46` | Vite 把 `index.html` 与模块打包，源码 `?v=` 字面量**在产物层消失或变形**；对 `dist/` 跑「恰好 46」必然 FAIL，**且这是预期、不是产品缺陷** | ① **源码层**：S17 扫描根**收窄为 2D 遗产层 9 文件白名单**（排除 `node_modules/` / `dist/` / `src/` 新增 React/R3F 文件 / `vendor.manifest.json`），仍锁 `{hud-20261108:46}`；② **产物层**：由新门控 `BC-*` 锁 `{VENDOR_TAG:N}`；③ 两结果分别打印、分别判定 |
| `verify_fresh_gate.py` **F8a** | 同上（跨两站） | 同上；且 RALLY 侧 `node_modules/` 会污染直方图 | 同 S17：扫描根白名单化 + 产物层独立断言 |
| `verify_c08_gate.py` **S1.7** | 同上 | 同上 | 同 S17 |
| `verify_hud_spec.py` **H11** | `{'hud-20261108':46}` + `CACHE_TAG` 同步 + 20 图零裸引用 + 资源按字节送达 | 46 与「按字节送达」需分治 | ① 46 → 源码层白名单；② `CACHE_TAG` → 源码层；③ **资源按字节送达 → dev 与 build 双模式按 §3.1**（这是真正要验的运行时事实）；④ 20 图零裸引用 → §2.5 |

> **表述纪律**：报告里必须写「原 S17/F8a/H11 的**全仓**口径在 `dist/` 上不适用」，**不得**写成「S17 已删除 / 已放宽」。测法从「全仓扫」改为「两层各扫各的」，**强度不降**（仍各自唯一、各自恰好）。

### 2.5 20 个图片 URL 零裸引用（口径继续有效，含拼接型）

**依据**：裁决 2 逐字 —— 「20 个图片 URL『零裸引用』口径**继续有效**，源码层不得出现无 tag 的图片 URL」。

**新测法**：沿用 `verify_cseg_gate.py` S18 / `verify_hud_spec.py` H11 的原始正则口径，扫描根同样**限定 2D 遗产层**：
- 字面量型：`["'\`]([^"'\`\n]*\.(?:webp|png)[^"'\`\n]*)["'\`]`，含 `/` 的 URL 必须带 `?v=hud-20261108` 或 `${CACHE_TAG}`；
- **动态拼接型**：`["'\`]([^"'\`\n]*assets/img/)["'\`]\s*\+\s*...` 段内也必须带 tag（沿用 `level.js:49` / `story.js:307` 两处的既有形态）；
- `dist/` 产物层：若构建把图片 URL 改写为 content-hash / 内联 base64，须由新门控 `BC-*` 证明**每个图片资源都有唯一版本标识且无裸引用**，不得以「Vite 处理过了」为由跳过。

**PASS 判据（硬）**：源码层 20 个图片 URL 字面量 + 2 处拼接型，**零裸引用**；产物层等价判据零裸引用；两层分别打印。

### 2.6 扫描根白名单（必须新增的机制，否则 46 断言被第三方代码污染）

**事实**：现有 S17 / F8a / S1.7 / S18 / H11 的扫描是 `for base in (QUEST, RALLY): os.walk(base)`，排除列表仅 `assets/ docs/ sprite_gen/`。Vite 接管后 `音标拉力赛/` 下将新增 `node_modules/`（数千 `.js`）、`dist/`（content-hash 产物）、`src/`（React/R3F 源码）、`vite.config.js` 等，其中 `.js/.css` **会被 `os.walk` 纳入**，导致 tag 直方图与裸 URL 断言被第三方代码污染、甚至性能灾难。

**新测法（强制）**：
```
SOURCE_SCAN_FILES = 白名单（9 个 2D 遗产层文件，逐文件列路径）
SOURCE_SCAN_EXCLUDE_DIRS = {node_modules, dist, src, .vite, coverage, __pycache__}
DIST_SCAN_ROOT = dist/（仅产物层断言使用，不参与源码层 46 统计）
断言：os.walk 实际访问的文件集合 ⊆ SOURCE_SCAN_FILES ∪ {非 .html/.js/.css 文件}
断言：源码层扫描结果中不含 VENDOR_TAG；产物层扫描结果中不含 hud-20261108
```
**PASS 判据**：扫描根隔离成立，且 §2.1 / §2.2 / §2.5 三层判据各自独立成立。

---

## 3. 构建链带来的新断言

### 3.1 dev 与 build 双模式跨目录资源按字节送达（防 Caddy 兜底 200 陷阱）

**依据**：`p0-slice-spec.md` §2 第 3 条 / §3 T1 / Go/No-Go「资源送达」行；`hud-qa-plan.md` §5。

**覆盖资源集**（待 §9 与 #19 对齐后逐项填入确切路径）：
- 48 立绘（大闯关 `assets/sprites/`）
- 29 成稿图
- 音频（含 `audio/fan.mp3`，§5.3 瞬态事实涉及项）
- `音标大闯关/js/ipa-display.js`
- 两站 `index.html` / `css` / `js` 等被 `?v=` 引用的资源

**新测法（dev 与 build 各跑一遍，四重判定，不信状态码）**：
1. **先探兜底**：请求一个确定不存在的路径（如 `assets/img/__qa_missing_9f3a.webp?v=...`）。若返回 `200` 且 body 以 `<!doctype html` / `<html` 开头 → **确认存在兜底**，此后所有资源**状态码一律不可信**。
2. 对每个资源，从**浏览器实际请求的 URL**（不是本地文件路径）取 body：
   - `sha256(body) == sha256(disk)`（**逐字节 + sha256 全等**）；
   - **magic**：WebP `RIFF????WEBP`、PNG `\x89PNG\r\n\x1a\n`、MP3 `ID3` / `0xFF 0xFB`、JS/CSS 为可打印 UTF-8 且不含 `<html`；
   - `Content-Type` 与后缀匹配且**不是 `text/html`**；
   - 字节长度与本地磁盘一致。
3. **dev 模式**：Vite dev server 下逐个复核（含 `/@fs/` 等 dev 内部路径映射后的实际送达）；**build 模式**：`vite build` 产物 + preview server 下逐个复核（含跨 root 的 `../音标大闯关/` 引用是否被正确复制到 `dist/`，T1）。
4. 中文路径用 `urllib.parse.quote(rel, safe="/")` percent-encode（#5 已踩过 `UnicodeEncodeError` 坑）。

**PASS 判据（硬）**：dev 与 build 两模式、资源集内**每一项**四重判定全等；任一不等即 FAIL（不因状态码 200 放行）。

### 3.2 `ipa-display.js` 同步 script 先于 module 的时序（T2）

**事实**（本轮只读核对 `音标拉力赛/index.html:170-172`）：
```html
<!-- 普通脚本同步执行；module 默认 defer，故 window.IPA_DISPLAY 在 module 执行前已就绪。 -->
<script src="../音标大闯关/js/ipa-display.js?v=hud-20261108"></script>
<script type="module" src="js/main.js?v=hud-20261108"></script>
```

**新测法（dev 与 build 各一遍）**：
1. HTML 解析层：`ipa-display.js` 的 `<script>` 仍为**非 module、无 `defer`/`async`**，且 DOM 顺序在首个 `type="module"` 之前；或 Vite 改写后证明等价时序。
2. 运行时层：`page.add_init_script` 注入打点，在 module 首条语句执行时读取 `window.IPA_DISPLAY`，断言**已定义**且 `U11.displayIpa==='ɜr'`；用 `performance.getEntriesByType('resource')` 确认 `ipa-display.js` 的响应早于 module 消费者读取。
3. 结果层：48 卡面 `.sym` 全为美式、无英式符号（F9a 口径）。

**PASS 判据（硬）**：两模式下「module 执行前 `IPA_DISPLAY` 已就绪」成立，且 48 卡面显示正确。**禁止**只验 build 成功、不验时序。

### 3.3 R3F 探针（默认关闭 / 一键关回 2D / 375×780 与 320×568 WebGL 上下文）

**依据**：`p0-slice-spec.md` §2 第 2 条 / Go/No-Go「3D 探针可用」行 / 裁决 1（不进主循环）。

**新测法（开关形态、URL、flag 名待 §9 由 #19 提供，本规格不臆造）**：
1. **默认关闭**：无任何 query param / flag 时加载页面 → 断言**不创建 WebGL 上下文**（`HTMLCanvasElement.prototype.getContext` hook 计数中 `webgl/webgl2` = 0）、2D 主形态完整可玩、`window.__rally` 可用、判定核心正常。
2. **探针开启**：按 #19 提供的开关开启 → 断言 375×780 与 320×568 两个视口下 `canvas.getContext('webgl2') || getContext('webgl')` 非 null、`gl.getParameter(gl.VERSION)` 非空、立方体与 `FogExp2` 纸雾可见（帧缓冲非空像素 > 0）、单一暖主光存在。
3. **一键关回 2D**：从探针态切回 → 断言 2D 主形态恢复、WebGL 上下文不再被驱动渲染、判定核心未受影响（`__rally.step(n)` 结果与开启前一致）。
4. **不进主循环**：探针开启时，`__rally.step(n)` 显式驱动下断言 `odo/lateral/g.line` 不因 rAF / React state 被改写（K1）；`snapshot()` 只读（K4）。
5. **零新增 localStorage 字段**：探针开关**不得**默认写入 `localStorage`（用 query param / 内存 flag），键集合与基线一致（K2）。

**PASS 判据（硬）**：默认关闭成立；两窄视口 WebGL 上下文创建成功且可见；关回 2D 无损；探针不改变判定核心、不新增存档字段。任一失败 FAIL，不登记为 NOTE。

### 3.4 `dist/` 形态下两站同源与共享 localStorage（T3）

**依据**：`p0-slice-spec.md` §3 T3 —— `dist/` 形态下两站是否仍同 root / 同源，**直接决定共享 `localStorage['ipa-quest-v1']` 是否成立**；P0 只需给结论与部署建议，不实施发布。

**新测法**：
1. 在 build preview 形态下分别打开两站，断言 `new URL(A).origin === new URL(B).origin`（协议 / host / 端口三者相等）。
2. 拉力赛侧写 `ipa-quest-v1` 的 `rally.gems/shields/EP02/ownedPaints/howSeen/unlocked` → 大闯关侧读回逐字段相等；反向亦然（K2 场景）。
3. **若不同源**：不得判 PASS、也不得悄悄放行——须在报告中给出明确结论「`dist/` 形态下两站不同源 → 共享单键不成立」，并列入 CONCERNS/FAIL 由用户/主理人裁决部署方案（T3 要求给结论与建议，不实施）。

**PASS 判据（硬）**：同源 + 跨站读写逐字段相等；或明确登记不同源结论并升级为主理人裁决项（不放行）。

### 3.5 零外链、体积与请求数（Go/No-Go 记录项）

- **零外链**：network 面板无**产品功能依赖**的外部 host 请求；`fonts.googleapis.com` / `fonts.gstatic.com` 属已知项（T5 / 阶段交付），**单列披露**、计入外链环境项，不得算产品失败，也不得反过来用它掩盖同源失败（X6 / K5）。
- **体积记录**：dev 与 build 首屏 JS 体积、请求数、帧时间，作为 Rapier 取舍的实测依据（Go/No-Go「体积」行）。本项为**记录项**（NOTE 登记），非 PASS/FAIL 硬判据；但数据必须实测上报，不得估算。

### 3.6 版本钉定与 peer 上界

`three === '0.186.1'`；`@react-three/fiber` / `drei` / `@react-three/postprocessing` 版本在核实后的 peer 上界内（值由 #19 提供，本规格不预设）。判据：版本字符串精确匹配 `vendor.manifest.json` 且无 CDN 运行时依赖。

---

## 4. 失效清单（路线 B 让现有 110 项中哪些断言失效 / 为什么 / 替代判据）

> **口径**：`110` = 四套门控（`cseg_gate` 38 + `cseg_ui` 14 + `fresh_gate` 21 + `c08_gate` 37）；另有 `verify_hud_spec.py` 12 项 HUD 专项、`headless_laps.mjs` 11 场、`minimap_model.test.mjs` 10 项单测。本清单按**失效族**归并，逐条给出精确原断言编号、失效原因、替代判据。
> **汇总**：**12 个失效族**，点名四套门控 110 项中的 **29 项** + HUD 专项 **12 项** 需重定义/重验；其余 **81 项**（判定核心源码字面量、跨站存档逻辑、美式文案基线、Node 自检）原样保留。

| # | 原断言（精确编号） | 失效原因（路线 B 具体机制） | 替代判据（新门控编号见 §6） |
| --- | --- | --- | --- |
| **F-01** | `cseg_gate` **S17** 全仓 tag 唯一且恰好 46 | `os.walk(QUEST, RALLY)` 会扫入 `node_modules/`（数千 `.js`）、`dist/`（content-hash）、`src/`（R3F 源码）；且 `dist/` 中源码 `?v=` 已消失 → 直方图被污染、必然 FAIL，且属扫描口径问题非产品缺陷 | `BC-1` 源码层白名单 9 文件锁 `{hud-20261108:46}` + `BC-2` 产物层锁 `{VENDOR_TAG:N}`，两层分别打印（§2.4 / §2.6） |
| **F-02** | `cseg_gate` **S18** 全仓图片 URL 零裸引用（含拼接型） | 同上；`node_modules/` / `dist/` 内含大量无 `?v=` 的图片 URL 字面量 → 裸引用断言被打爆 | `BC-4` 源码层 20 图 + 2 拼接型零裸引用（扫描根白名单）+ `BC-5` 产物层等价判据（§2.5） |
| **F-03** | `fresh_gate` **F8a** 全仓 `?v=` tag 唯一 46 | 同 F-01（跨两站扫描，RALLY 侧新增目录同样污染） | 同 F-01（`BC-1`/`BC-2`），并断言源码层扫描不含 `VENDOR_TAG` |
| **F-04** | `c08_gate` **S1.7** 全仓 tag 唯一值 46 | 同 F-01 | 同 F-01 |
| **F-05** | `hud_spec` **H11** tag 46 / 20 图零裸 / `CACHE_TAG` / 资源按字节送达 | 46 属源码层、`dist/` 不适用；「本地 in-process HTTPServer 按字节送达」不再是 dev/build 的真实服务模型 | `BC-1`/`BC-4`（源码层）+ `BV-1`/`BV-2`（dev/build 双模式按字节送达，§3.1）+ `BI-2`（时序/显示源，§3.2） |
| **F-06** | `fresh_gate` **F8b** + **F11c** 大闯关/拉力赛实际请求全带新 tag + 跨目录显示表按字节送达 | Vite dev 下资源 URL 形态变化（`?v=` 可能被转写、`/音标大闯关/` 跨 root 引用被 `/@fs/` 映射）；`F8b` 姊妹站未接管故大体保留，但**拉力赛侧** `F11c` 失效 | `BV-3` dev/build 两模式下实际请求资源清单逐个按 §3.1 四重判定；`BC-*` 处理 tag 形态；跨目录显示表按字节真送达（沿用 `D7.4` 期望值） |
| **F-07** | `c08_gate` **D7.1 / D7.2 / D7.4** 两站请求带新 tag / 跨目录显示表按字节真送达 | 同 F-06；T1 跨目录资源在 `server.fs.strict` 下可能被拦 → 显示表送达不到 | `BV-1`/`BV-2`/`BV-3` 双模式按字节 + `BI-3` `ipa-display.js` 时序；期望值（带 tag、按字节真送达）**逐字不放宽** |
| **F-08** | `fresh_gate` **F10a / F10b** 强缓存场景 js/css 无漏网不带 tag 资源 / 页面仍完整渲染 | Vite dev 注入 `/@vite/client`、HMR 模块等**无 `?v=` 的 js** → `stale_router` 的 `re.search(r'\.(js\|css)(\?\|$)')` 会误命中，`stale_hits>0` → FAIL；build 形态下资源已 content-hash，原「不带 tag 注入脏内容」模型不再成立 | `BV-4` 重定义强缓存场景：**按资源角色分类**（产品内容资源必须带版本标识；Vite 机制项单列），仍断言「0 次脏内容注入 + 页面完整渲染 48 卡美式」；分类口径写进明细，不删除断言 |
| **F-09** | `fresh_gate` **F11d** / `c08_gate` **D7.5** / `cseg_ui` **U1·U12** / `hud_spec` **H12** 四项错误计数 | Vite HMR WebSocket、`/@vite/client`、dev 内部路径请求进入 `requestfailed` 明细；原分类表无对应类别 → 易误判或误豁免 | `BE-1..BE-5` 扩展 K5 分类表（§1 K5 + §5.2），新增「Vite 机制项」单列；**同源真实失败仍必须 = 0**，硬失败口径不变 |
| **F-10** | `cseg_ui` **U2–U11** 全套 14 项（选择器 / reload 偏好 / 建门 / 三题型 / 结果页 / 解锁 / 跨站写入） | 脚本自起 in-process `ThreadingHTTPServer` 直服 `音标拉力赛/index.html`；Vite 接管后该 URL 不再是真实服务模型 | `BD-4` 把入口 URL **参数化**为 `dev` / `build` 两个 base，**U2–U11 全部在两种模式下各重放一遍**，断言与期望值逐字不变；浏览器实跑不得跳过（X3） |
| **F-11** | `c08_gate` **D7.3**（`__rally` 钩子可用且逻辑键完好）/ **D8.4**（375px `#jump` 可点） | 新入口下 `window.__rally` 是否仍挂载需实测；375px 页面现在跑在 Vite dev/build 上 | `BD-4`/`BR-4` 在两模式 + 375×780 / 320×568 下重验 `__rally` 只读 getter、`#jump` 存在可点、判定逻辑键完好 |
| **F-12** | `hud_spec` **H1–H10 / H12**（HUD DOM、显隐矩阵、quiz 冻结、答案零泄露、零写盘） | 入口服务模型变化；R3F 探针 overlay 引入新的 DOM 检测面（K4） | `BQ-1..BQ-4`（K4 零泄露，含探针 overlay 新增检测面）+ `BD-4`（显隐/冻结/两圈在两模式重放）+ `BS-4`（零写盘/字段守恒）；H5 检测面口径**逐字不变** |

### 4.1 明确「原样保留、不受影响」的断言（防止被顺手删掉）

| 域 | 断言 | 保留理由 |
| --- | --- | --- |
| 判定核心源码 | `cseg_gate` S1–S16（除 S17/S18）、A0–A6、B0–B9、C1–C3 | 裁决 1：`race.js`/`track.js`/`config.js`/`main.js` 主循环逐字不改；`headless_laps.mjs` 原路径原命令 |
| 跨站存档逻辑 | `c08_gate` D1.1–D6.2、`fresh_gate` F11a/F11b、`cseg_ui` U10/U11 | localStorage 逻辑不变，仅换服务入口重放（K2） |
| 美式文案基线 | `fresh_gate` F1/F1b/F2/F3/F4/F5/F6a/F6b/F6c/F7/F9a/F9b/F9c、`c08_gate` D9.1/D9.2/D9.3、`cseg_gate` B2/B9 | `data.js` / `ipa-display.js` / 持久化基线不碰，sha256 三方全等仍成立 |
| 纯函数单测 | `minimap_model.test.mjs` T0–T7（10 项） | 读 `render.js` 纯函数，与构建链无关 |
| 两圈实跑 | `headless_laps.mjs` 11 场 ≤180s | 裁决 1 Go/No-Go 硬条件 |

### 4.2 失效清单条数与计数口径

**12 个失效族**（F-01 ~ F-12）；覆盖四套门控 110 项中 **29 项**（`cseg_gate` 2 + `cseg_ui` 14 + `fresh_gate` 6 + `c08_gate` 7）与 HUD 专项 **12 项**；其余 **81 项**原样保留。**没有一条被删除、放宽或改为 NOTE**——全部有明确替代断言承接。

---

## 5. 回归运行纪律

### 5.1 串行顺序（沿用 `hud-qa-plan.md` §1，按路线 B 扩展）

**顺序理由不变**：秒级静态 → 浏览器门控（**dev 模式**）→ 浏览器门控（**build preview 模式**）→ `headless_laps.mjs`（最慢 ≈175s，放中后段）→ 最后 HUD/探针专项（依赖 DOM 与 WebGL 就绪）。**任一步 FAIL 即停，先定位再决定是否继续，不带着红灯往下跑。**

```bash
# 0 静态自检（不启动浏览器）：源码层 46 / 产物层 N / 扫描根隔离 / sha256 判定核心
# 1 源码层门控（原样保留域）：python verify_cseg_gate.py 等（扫描根白名单化后）
# 2 dev 模式：把 U/D/F/H 全套按新 base URL 串行重放
# 3 build 模式：vite build + preview，同套断言再串行重放一遍
# 4 node js/headless_laps.mjs（原路径原命令，11 场 ≤180s）
# 5 node js/minimap_model.test.mjs（10 项）
# 6 R3F 探针专项：默认关闭 / 开启 / 关回 / 两窄视口 WebGL（BR-*）
# 7 资源按字节送达 dev + build（BV-*）、四项错误计数汇总（BE-*）
```
**不得并行跑多个浏览器门控**：各脚本自起 HTTP server / 占用端口，串行避免 `requestfailed` 假阳性（沿用 `hud-qa-plan.md` §1 注）；Vite dev server 与 preview server 也须**用完即释放端口**，批次之间留间隔（§5.3）。

### 5.2 `ERR_CONNECTION_REFUSED` / `ERR_ABORTED` 明细区分口径（沿用既有，不放宽）

| 现象 | 归类 | 处置 |
| --- | --- | --- |
| `net::ERR_ABORTED` | reload / 导航主动取消 | **不计失败**，单列披露 + 去重 URL 样例；禁止混入 FAIL 计数，也禁止静默吞掉 |
| 同源 `ERR_CONNECTION_REFUSED`（in-process `ThreadingHTTPServer` 端口回收瞬态） | **先按同源真实失败如实记录，再按 §5.3 复核** | 不放宽断言、不改脚本、不直接判 PASS；经复核确认瞬态后方可按口径登记 |
| 同源其它非 `ERR_ABORTED` 失败 / 4xx | **真实失败** | `= 0` 硬条件，非 0 即 FAIL |
| 外链字体失败 | 环境项 | NOTE 单列，资源送达由 §3.1 字节比对覆盖，不信状态码（T5） |
| Vite HMR / `@vite/client` / dev 内部路径 | 机制项 | 单列披露，与同源内容资源失败**分开统计**，不得掩盖（X6） |

### 5.3 fan.mp3 瞬态事实与处置口径（team-lead 提供，须写进新规格）

**事实**（`stage-delivery-2026-11-09.md` §2.1，team-lead 独立实跑）：
> 首次把 7 个脚本**连续同批次串行**跑时，`verify_hud_spec.py` 的 **H12 出现 1 次 `fan.mp3 → net::ERR_CONNECTION_REFUSED`**（`console_error=1 / requestfailed=1`，exit 1）。核查：`audio/fan.mp3` 实体存在（9792 B）；失败发生在 in-process `ThreadingHTTPServer` 端口回收边界，属启动瞬态；**单独重跑 2 次全部 12/12、四项计数全 0**；QA 首轮两跑 + 收口复核一跑同样未复现。

**本规格明确的处置口径（逐条硬性）**：
1. **不放宽断言**：H12 / `BE-*` 的 `同源真实失败 == 0` 判据**一个字不改**，不因为「已知瞬态」就把它改成 `<=1` 或改 NOTE。
2. **不改脚本**：不修改 `verify_hud_spec.py` 或任何现有脚本来「吞掉」该类失败；瞬态识别在**运行纪律与报告明细**层完成，不在断言层。
3. **不视为产品缺陷**：`fan.mp3` 实体存在、单独重跑全绿，属服务端口回收瞬态，不回派 engineering-lead 修产品。
4. **可复现的复核流程**（FAIL 出现时，按序执行，全部留痕）：
   - ① 记录完整明细：`requestfailed` 的 URL、failure、`console.error` 文本、发生时的脚本序号与端口；
   - ② **核验实体**：`stat` 该资源、比对 `sha256` 与 P0 前快照，确认资源存在且未变；
   - ③ **隔离重跑**：把该脚本**单独**重跑 **2 次**（不与其他脚本同批次），两次均须 `SUMMARY` 全绿且四项计数全 0；
   - ④ **归因**：两次全绿 + 实体存在 + 失败落在同批次端口切换边界 → 判「启动瞬态」，在报告 §7.3 登记为 **NOTE（环境瞬态）**，附①②③证据；
   - ⑤ **升级条件**：若隔离重跑任一仍 FAIL、或实体缺失/字节不符、或失败不在端口边界 → **不得**按瞬态豁免，按真实同源失败判 **FAIL** 并回报主理人。
5. **预防**：门控继续**串行**跑、批次之间留间隔、server 用完显式 `shutdown()/server_close()`；Vite dev/preview server 同样释放端口后再起下一批。
6. **CI 信号卫生**：该类瞬态只登记 NOTE，**不污染** PASS/FAIL 结论；但也**不得**用「历史上出现过」为由预先豁免任何一次真实失败。

### 5.4 flaky 隔离

任何偶发 FAIL 先隔离该用例单独重跑并登记（沿用 `hud-qa-plan.md` C11），**不直接改期望值、不把断言改 NOTE**；确认 flaky 后由主理人裁决是否单列，QA 不自行放宽。

---

## 6. 新门控编号体系与 TOTAL 口径

### 6.1 编号体系（前缀 `B` = Route B；域字母分组）

| 域 | 前缀 | 承接 | 对应 §1 类别 |
| --- | --- | --- | --- |
| 判定核心确定性 | `BD-*` | K1：sha256 零改动、11 场 headless、两圈/门线/听音题、dev/build 双模式一致性 | K1 |
| 跨站单键保真 | `BS-*` | K2：D1–D6 重放、同源、跨站字段守恒、零写盘、零新增字段 | K2 |
| IPA 单一显示源 | `BI-*` | K3：同步 script 时序、`IPA_DISPLAY.U11=ɜr`、48 卡面、`sym` 稳定键、`ipa-display.js` 字节 | K3 |
| quiz 零泄露 | `BQ-*` | K4：H5 口径 83 词 + 4 字段名、探针 overlay 新增检测面、`snapshot()` 键白名单、U8/S11 | K4 |
| 四项错误计数 | `BE-*` | K5：四类硬归零 + `ERR_ABORTED` / 外链 / Vite 机制项单列 | K5 |
| 双层缓存 | `BC-*` | §2：源码层 46、产物层 N、互不混算、扫描根隔离、20 图零裸引用 | 裁决 2 |
| 构建链 / 资源送达 | `BV-*` | §3.1 / §3.2 / §3.5：dev/build 按字节、强缓存场景重定义、零外链、体积记录 | T1/T2/T5 |
| R3F 探针 | `BR-*` | §3.3：默认关闭、两窄视口 WebGL、关回 2D、不进主循环、零新增字段 | 裁决 1 |
| 同源 / dist 形态 | `BO-*` | §3.4：两站同源、共享 localStorage、不同源结论登记 | T3 |
| 保留域 | `L-*` | 五套脚本中**原样保留**的 81 项（S/A/B/C 部分、D1–D6、F 基线、U 逻辑），仅换 base URL | §4.3 |

> **编号纪律**：每个 `chk(...)` 名称带唯一编号；失效清单 F-01~F-12 的替代判据必须能追到具体 `B*-n`；报告 §7.4 判定记录表按域汇总。

### 6.2 TOTAL 口径（不预设具体数字）

**本规格不填任何具体 TOTAL 数字**——等 `#19` P0 产物定型、`vendor.manifest.json` schema 与 N 确定后再定。

```
TOTAL_new = Σ count(BD) + Σ count(BS) + Σ count(BI) + Σ count(BQ) + Σ count(BE)
          + Σ count(BC) + Σ count(BV) + Σ count(BR) + Σ count(BO)
          + Σ count(L)
```
**约束（必须写进报告）**：
- `TOTAL_new ≠ 110` **是允许的**（用户已批准重定义），但必须满足 §0.3 守恒式与 §6.3 满格映射；
- 五类 K1–K5 **每一类至少有 1 条硬 `chk` 承接**，且 PASS 判据不弱于 §1；
- 原 110+12 项中被重定义的每一条，在失效清单里都有 `替代 = B*-n`；**出现无替代的空行 = 规格不接受**；
- `dist/` 相关断言（`BC-2` / `BV-*` / `BO-*` / `BR-*`）的条数随产物形态变化，定型前用占位符 `N_BV` / `N_BR` 表示，禁止先拍一个数字再凑断言。

### 6.3 K1–K5 覆盖映射核查表（实跑报告必填、必须满格）

| 类别 | `p0-slice-spec.md` §1 要求 | 新门控承接编号 | 原断言 | 强度对比 | 满格? |
| --- | --- | --- | --- | --- | --- |
| K1 | 两圈 / 门线 `g.line` / 听音题正确性 / 11 场 ≤180s | `BD-1..` | S1–S8/S13/A0–A6/U6/U8/H10/T0–T7 | ≥ 原 | ☐ |
| K2 | 跨站单键保真 / C08 白名单 / `rally` 不互相覆盖 | `BS-1..` | D1–D6/U10/U11/F11a/F11b/H12 | ≥ 原 | ☐ |
| K3 | `window.IPA_DISPLAY` 单一源 / `sym` 稳定键 | `BI-1..` | F1/F1b/F2/F5/F9a/F9b/B2/B9/D7.4/H11 | ≥ 原 | ☐ |
| K4 | 83 词全表 + 4 字段名零泄露（H5 口径） | `BQ-1..` | H5/H6/H8/U8/S11 | ≥ 原（含探针 overlay 新增面） | ☐ |
| K5 | 四项计数归零 / ERR_ABORTED 单列 / 同源真实 0 / 外链单列 | `BE-1..` | U1/U12/F11d/D7.5/H12 | ≥ 原（含 Vite 机制项） | ☐ |

> 任一格空格或未填 → 判 **FAIL**（覆盖面缩水），不得以「PASS 数够多」替代。

---

## 7. 登记表模板（实跑时逐表填写）

### 7.1 四项错误计数表（dev / build 各一张）

| 模式 | pageerror | console_error | requestfailed | bad_status | ERR_ABORTED 单列 | 同源真实失败 | 外链环境 | Vite 机制项 | 判定 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev | 0 | 0 | 0 | 0 | ___ | **0** | ___ | ___ | ☐ PASS ☐ FAIL |
| build | 0 | 0 | 0 | 0 | ___ | **0** | ___ | ___ | ☐ PASS ☐ FAIL |

> 硬条件：`pageerror/console_error/bad_status == 0` 且 `同源真实失败 == 0`；`ERR_ABORTED` / 外链 / Vite 机制项**单列披露、不混入**；明细逐条打印。样式沿用 `hud-final-qa-report.md` §5.4。

### 7.2 资源按字节校验表（dev / build 各一张）

| # | 资源（相对路径） | 字节 | `byteEqual` | sha256[:16] | magic | Content-Type（非 text/html） | dev | build |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `音标大闯关/js/ipa-display.js` | 3822 | ☐ | ___ | 可打印 UTF-8 | `text/javascript` | ☐ | ☐ |
| 2 | 48 立绘（逐项或汇总清单） | ___ | ☐ | ___ | `RIFF....WEBP` | `image/webp` | ☐ | ☐ |
| 3 | 29 成稿图 | ___ | ☐ | ___ | `RIFF....WEBP` / PNG | `image/*` | ☐ | ☐ |
| 4 | 音频（含 `fan.mp3` 9792 B） | ___ | ☐ | ___ | `ID3` / `0xFF 0xFB` | `audio/mpeg` | ☐ | ☐ |
| 5 | 两站 `index.html` / `css` / `js` 被 `?v=` 引用项 | ___ | ☐ | ___ | 可打印、无 `<html` | 匹配后缀 | ☐ | ☐ |

> 先探兜底（§3.1 第 1 步），**不信状态码**；中文路径 percent-encode。样式沿用 `hud-final-qa-report.md` §5.3。

### 7.3 CONCERNS / NOTE 登记格式

| # | 类型 | 内容 | 影响 | 证据 | 需裁决 |
| --- | --- | --- | --- | --- | --- |
| CN-1 | NOTE（环境瞬态） | §5.3 fan.mp3 `ERR_CONNECTION_REFUSED` 类瞬态 | 不阻塞 | ①②③ 复核链 + 2 次隔离重跑全绿 | 否 |
| CN-2 | NOTE（已知项） | `fonts.googleapis.com` / `gstatic.com` 外链字体（T5） | 不阻塞 | 明细 URL | 否 |
| CN-3 | NOTE（记录项） | dev/build 首屏 JS 体积 / 请求数 / 帧时间 | 不阻塞 | 实测数据 | 否 |
| CN-4 | CONCERNS | `dist/` 形态两站不同源（T3，若发生） | **阻塞放行** | origin 对比 + 跨站读写结果 | **是** |
| CN-5 | CONCERNS | 任何 K1–K5 映射空格 / 无替代断言 | **阻塞** | §6.3 映射表 | **是** |

> **FAIL 改 NOTE 一律禁止**（X4）。NOTE 只承载「已核实的环境项 / 记录项 / 可解释且不影响判定的诊断项」。

### 7.4 判定记录表（实跑填写）

| 项 | 结果 | SUMMARY / 证据 |
| --- | --- | --- |
| 源码层 46 / 产物层 N / 扫描根隔离（`BC-*`） | ☐ PASS ☐ FAIL | `{'hud-20261108':46}` / `{VENDOR_TAG:N}` / 白名单命中 |
| 判定核心零改动 + 11 场 headless（`BD-*`） | ☐ PASS ☐ FAIL | sha256 全等 / `ALL PASS` / max ___ s ≤180 |
| dev 模式全套重放（`L-*` + `B*-*`） | ☐ PASS ☐ FAIL | `___ PASS / ___ FAIL / ___ TOTAL` |
| build 模式全套重放 | ☐ PASS ☐ FAIL | `___ PASS / ___ FAIL / ___ TOTAL` |
| 资源按字节送达 dev/build（`BV-*`） | ☐ PASS ☐ FAIL | §7.2 两表 |
| 四项错误计数（`BE-*`） | ☐ 归零 | §7.1 两表 |
| K1–K5 覆盖映射（`§6.3`） | ☐ 满格 ☐ 有空格 | 五格全勾 |
| R3F 探针（`BR-*`） | ☐ PASS ☐ FAIL | 默认关闭 / 两视口 WebGL / 关回 2D |
| 两站同源（`BO-*`） | ☐ PASS ☐ CONCERNS | origin / 跨站字段 |
| **质量门判定** | ☐ PASS ☐ CONCERNS ☐ FAIL | advisory，最终放行由用户决定 |

---

## 8. 回滚点与项目数据声明

- **`.workbuddy/backups/` 是项目数据，不是临时缓存，不得当缓存清理**（沿用 `hud-final-qa-report.md` §6 R3 / 阶段交付 R3）。现有 `c07b-data-baseline.js`（174527 B）、`baseline-meta.json`、`hud-20261109/`（13 产品文件 + manifest，232451 B）不得删除——删除会让 F3/F6a/F6b/D9.2 立刻回到首轮 C1 的 MISSING 状态。
- **P0 改动前全量快照**：`p0-slice-spec.md` §2 第 6 条要求 engineering-lead 在 P0 前于 `.workbuddy/backups/` 新建一份**产品代码 + 四套门控脚本**的全量快照，manifest 写明日期与**可回滚范围**。实跑前 QA 须核对：① 快照存在；② 包含判定核心 5 文件与 `ipa-display.js`；③ sha256 逐项可与当前源码比对（K1/K3 依赖此快照）。
- **回滚触发**：任一 K1–K5 硬断言 FAIL 且定位为实现缺陷、窗口内无法修；判定核心 sha256 与快照不符；`dist/` 形态资源送达错发；用户要求撤回 P0。
- **回滚方法**：按 manifest 相对路径 copy 回源根同名路径，逐文件按 sha256 前 16 位复核（沿用 `hud-qa-plan.md` §9）。回滚后须**重跑** `node js/headless_laps.mjs` 11 场 + 源码层 46 断言确认回到 2D L0 基线。
- **保留的遗留风险（不阻塞本轮，须随报告登记）**：R1（C07-B 前 / C08 resume 前历史 diff 能力永久丧失，改由「不回退 + sha256 全等」保证）、R2（`hud-20261109` 为 #4 之后状态，仅能回滚后续改动）、R4（`data.js` 变更须同步基线并重跑）、R8（3D 数据陷阱：`config.js` 的 `length/tone/color` 是 A/B 分组着色键，字面值与语音学相反，**禁止**进入 3D 几何/材质/教学参数，且不得「修」或重命名——会破 F5/B7 门控）、R10（项目无 git 仓库，回滚依赖手工快照）。

---

## 9. 实跑前置：需 engineering-lead（#19）提供的产物信息

> 本规格不预设任何 P0 产物细节（T1 方案由 engineering-lead 实测给出）。以下信息齐备前**不实跑**。回主理人的消息里会点出最关键几项。

| # | 需要的信息 | 用途 |
| --- | --- | --- |
| 1 | `package.json` / `vite.config.js` 最终配置：Vite `root`、`base`、`server.fs.allow/strict`、`build.outDir`、`publicDir`、跨 root 资源（`../音标大闯关/`）的实测解法（T1） | 定 `BV-*` 资源路径与 dev/build base URL |
| 2 | `vendor.manifest.json` 的 **schema**、`VENDOR_TAG` 实际值、N 处清单的位置与计数方式、content-hash 文件名形态 | 定 `BC-2` 的 N 与判据（§2.2） |
| 3 | three `0.186.1` 与 `@react-three/fiber` / `drei` / `@react-three/postprocessing` 的**钉定版本**及 peer 上界核实结果 | 定 §3.6 版本断言 |
| 4 | R3F 探针的**挂载方式与开关**：独立入口 URL 还是 overlay；默认关闭机制；「一键关回 2D」的具体开关（query param / 内存 flag / 按钮 id）；探针根节点选择器 | 定 `BR-*` 全部断言（§3.3） |
| 5 | dev server 与 build preview 的**启动命令、端口、`dist/` 结构**；`dist/` 下两站是否同 root / 同源（T3 结论与部署建议） | 定 `BO-*` 与串行纪律（§5.1） |
| 6 | Vite 处理后 `index.html` 的 **script 时序**（`ipa-display.js` 同步 script 是否保留在 module 之前，T2）；源码层 46 处 `?v=` 字面量在产物层是否被改写/保留 | 定 `BI-*` / `BC-1` |
| 7 | **新增文件 / 目录清单**（哪些是 `.js/.css/.html`、是否落在 `os.walk(QUEST,RALLY)` 扫描根内），以及 `node_modules/` / `dist/` / `src/` 的实际路径 | 定 §2.6 扫描根白名单（**最可能翻车项**） |
| 8 | P0 改动前全量快照的 **manifest 路径**与文件清单 | 定 K1/K3 的 sha256 零改动证明（§8） |
| 9 | dev/build 首屏 JS 体积、请求数、帧时间实测数据；network 面板外链 host 清单（含已知 Google Fonts） | §3.5 记录项 / K5 外链单列 |
| 10 | 2D L0 主形态在新入口下的 **URL 形态**（`index.html` 是否仍为入口、`?v=` 是否保留、`window.__rally` 是否仍挂载） | 定 `BD-4` / `L-*` 的 base URL 参数化 |

---

## 10. 脚本草案骨架（内嵌伪代码，本轮不落 `.py` / `.mjs`、不执行、不改现有脚本）

> 仅供 #19 产物定型后由 QA 编写新门控时的结构参考。**不新建任何可执行文件**，不覆盖五套既有脚本。风格沿用 `verify_cseg_ui.py` / `verify_hud_spec.py`：`ThreadingHTTPServer`（或 Vite subprocess）+ `sync_playwright` + `chk(name, ok, detail)` + `page.evaluate` + `window.__rally.step(n)` + `SUMMARY: N PASS / N FAIL / N TOTAL`。

```python
# ===== 草案：verify_p0_gate.py（骨架，非可执行，不落盘）=====
TAG_SRC   = "hud-20261108"          # 源码层（2D 遗产层），锁 46
VENDOR_TAG = None                    # 待 #19 提供（§9-2）
N_VENDOR   = None                    # 待产物定型后填（§6.2 不预设）
CHROME    = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SOURCE_SCAN_FILES = [...]            # 9 个 2D 遗产层文件白名单（§2.6）
SCAN_EXCLUDE = {"node_modules", "dist", "src", ".vite", "__pycache__", "coverage"}
BASE = {"dev": None, "build": None} # 待 #19 提供（§9-5）
PROBE = {"on": None, "off": None}   # 待 #19 提供开关（§9-4）

def chk(name, ok, detail=""): ...   # 同既有：RESULTS.append + 打印 PASS/FAIL

# ---- BC：双层缓存（§2）----
def scan(root, files=None): ...     # 只扫白名单 / 或 dist/；返回 tag 直方图 + 裸引用
src_tags = scan(SOURCE_SCAN_FILES); dist_tags = scan(DIST_SCAN_ROOT)
chk("BC-1 源码层 {'hud-20261108':46} 唯一且恰好 46", src_tags == {TAG_SRC: 46}, src_tags)
chk("BC-2 产物层 {VENDOR_TAG:N} 唯一且恰好 N", dist_tags == {VENDOR_TAG: N_VENDOR}, dist_tags)
chk("BC-3 两层互不混算（扫描根隔离）", VENDOR_TAG not in src_tags and TAG_SRC not in dist_tags, ...)
chk("BC-4 源码层 20 图 + 2 拼接型零裸引用", not src_bare, src_bare[:6])

# ---- BD / K1：判定核心（§1 K1）----
chk("BD-1 判定核心 5 文件 sha256 == P0 前快照", sha_all_equal(SNAPSHOT), ...)
r = subprocess.run([NODE, "js/headless_laps.mjs"], cwd=RALLY_JS)   # 原路径原命令
chk("BD-2 11 场 ALL PASS 且 max(finishTime)<=180s", parse(r) ..., ...)
for mode in ("dev", "build"):
    boot(BASE[mode]); chk("BD-3[%s] __rally/两圈/line 差=L/听音题" % mode, ..., ...)

# ---- BQ / K4：quiz 零泄露（H5 口径，逐字不回退 innerHTML）----
vocab = page.evaluate("""async t => (await import('/音标拉力赛/js/config.js?v='+t)).allWords()""", TAG_SRC)
vocab_ok = (len(vocab) == 83 and len(set(vocab)) == 83)
def surface(node):                    # textContent + 后代所有属性值
    return node.textContent + ",".join(v for el in [node, *node.querySelectorAll("*")]
                                       for _, v in el.attributes ...)
tokens = set(vocab) | {"correctLateral","spoken","left","right"} | ipa_tokens(gates)
chk("BQ-1 2D H5 口径零命中（不含 innerHTML）", vocab_ok and not hits(surface(mm), tokens), ...)
chk("BQ-2 探针 overlay 同一口径零命中", not hits(surface(overlay), tokens), ...)
chk("BQ-3 snapshot()/minimapModel 递归键名零禁用键", not bad_keys, ...)

# ---- BE / K5：四项错误计数（§1 K5 / §5.2）----
# watch(page) 监听 pageerror/console/requestfailed/response.status>=400
# FAILS 明细分五类：ERR_ABORTED / 同源真实 / 外链 / Vite 机制 / 其它
chk("BE-1 四项硬归零 + 同源真实失败 == 0",
    errs["pageerror"]==0 and errs["console_error"]==0 and errs["bad_status"]==0
    and len(REAL)==0, (errs, classify_detail()))
# 汇总必须单列披露：总计 | ERR_ABORTED | 同源真实 | 外链 | Vite 机制

# ---- BV / §3.1：dev 与 build 资源按字节送达（不信状态码）----
for mode in ("dev", "build"):
    for rel, disk in RESOURCE_SET:                     # 48 立绘 / 29 成稿 / 音频 / ipa-display.js
        body, ctype = fetch_via_browser(BASE[mode], quote(rel))
        ok = (sha256(body)==sha256(disk) and magic_ok(body, rel)
              and "text/html" not in ctype and ctype_matches(rel, ctype))
        chk("BV[%s] %s 逐字节+magic+sha256+CType" % (mode, rel), ok, ...)

# ---- BR / §3.3：R3F 探针 ----
boot(BASE["dev"]); chk("BR-1 默认关闭：无 WebGL 上下文、2D 可玩", gl_count()==0 and rally_ok(), ...)
for vp in ((375,780),(320,568)):
    boot(BASE["dev"], PROBE["on"], vp)
    chk("BR-2[%s] WebGL 上下文 + 立方体/纸雾可见" % (vp,), gl_ok() and nonblank()>0, ...)
boot(BASE["dev"], PROBE["off"]); chk("BR-3 一键关回 2D 无损", rally_ok() and gl_idle(), ...)

# ---- BO / §3.4：同源与共享 localStorage ----
chk("BO-1 origin(拉力赛)==origin(大闯关) 且跨站 rally 字段逐字段相等", ..., ...)

# 汇总
print("SUMMARY: %d PASS / %d FAIL / %d TOTAL" % (p, f, len(RESULTS)))
sys.exit(1 if f else 0)
```

**草案纪律**：`chk` 只增不减；任何 `chk` 的 `ok` 表达式与 §1 / §2 / §3 的 PASS 判据逐字对应；`NOTE` 只用于 §7.3 的环境/记录项；`exit(2)` 仅用于「P0 产物未就绪」的前置未满足（沿用 `verify_hud_spec.py` 优雅报错契约），**不得**用它掩盖真实 FAIL。

---

## 11. 边界、Handoff 与质量门声明

- **本轮未做**：未实跑任何门控；未改产品代码（`js/` / `index.html` / `css/` / 图片 / `data.js` / `ipa-display.js` / 上游管线）；未改五套既有验收脚本；未新建任何可执行脚本；未部署、未上线、未 commit、未建 git 仓库。唯一写入物 = 本文件。
- **待主理人通知**：`#19` 产物定型 + §9 十项信息齐备后，按 §5.1 串行实跑，填写 §7 各表与 §6.3 覆盖映射，出 `design/p0-final-qa-report.md`（新文件，届时另行授权）。
- **CONCERNS 预判**：① §2.6 扫描根白名单（最可能翻车，见 Handoff）；② T3 同源结论若不同源须升级裁决；③ P0 前全量快照若缺失，K1/K3 的 sha256 零改动证明无法闭合。
- **发现的缺陷上报纪律**：若实跑发现产品缺陷，报 team-lead 回派 engineering-lead，QA 不自行改 `js/`。
- **质量门 advisory**：QA 给出 PASS / CONCERNS / FAIL 判定与阻塞项，**最终放行与发布签字由用户决定**；QA 不替用户拍板。所有产出经主理人中转。

---

---

## 附录 A · 三处判据修订（#20b，2026-11-09，按工程实测事实改测法、非放宽）

> **性质**：`#19` 产物定型后，engineering-lead 实测发现本规格 3 处判据与 Vite 真实产物形态不符。主理人裁定「按事实改测法，不是放宽」，要求写进附录并**保留原判据与修正理由以便追溯**。三处修订均**不删断言、不放宽阈值、不跳过浏览器实跑、不把 FAIL 改 NOTE**（§0.4 X1–X6 全部仍适用）。
> **依据**：`design/p0-impl-report.md` §5.3（BC-3 替代判据）、§3 T2 / §9-6（等价时序）、§3 T1（兜底陷阱实测）。
> **独立复核**：quality-lead 已自行读盘核实全部前提（判定核心 5 文件 + 五套脚本 + `data.js`/`ipa-display.js` 共 12 项 sha256 与 `p0-pre-20261109/file-hashes.json` 逐项全等；源码层 `{'hud-20261108':46}`；产物层 `VENDOR_TAG=p0-20261109` N=3、残留 `hud-20261108` 8 处；白名单裸引用 0、原口径全仓 33 处裸引用全部来自 `node_modules/`），详见 `design/p0-qa-report.md` §2。

### A.1 【BC-3】两层互不混算 —— 从「产物层不含源码 tag」改为「两层各自唯一 + 扫描根物理隔离」

**原判据（§2.3 / §2.6，逐字保留备查）**：
```
scan_source ∩ scan_dist == ∅
断言：源码层扫描结果中不含 VENDOR_TAG；产物层扫描结果中不含 hud-20261108
```
以及 §2.2 表述「`VENDOR_TAG` 不得出现在源码层 46 的扫描结果里（防混算）」、§10 草案 `chk("BC-3 两层互不混算（扫描根隔离 + 各层唯一）", ... )` 中的 `TAG_SRC not in dist_tags`。

**为何必然伪 FAIL（实测事实，非推测）**：Vite **保留**源码查询串，产物层实测残留 `hud-20261108` 共 **8 处**：

| 产物层文件 | 处数 | 来源 | 性质 |
| --- | --- | --- | --- |
| `.p0-build/dist/index.html` | 5 | 4 个静态图 URL 改 content-hash 但保留 `?v=` + 1 个普通同步 script `ipa-display.js?v=hud-20261108` | 跨层引用，不是产物层自身的版本标识 |
| `.p0-build/dist/vendor.manifest.json` | 1 | `cache_namespaces.source_layer.tag` **声明性字段** | 文档说明，不是资源引用 |
| `.p0-build/dist/assets/main-LrINXPEH.js` | 2 | bundle 内模块 specifier 携带查询串 | 构建链透传 |
| **合计** | **8** | — | — |

> 这 8 处**不是产品缺陷**（源码层 46 未删未改、产物层 `VENDOR_TAG` 仍唯一 N=3）。按原判据「产物层不含 `hud-20261108`」必然 FAIL，属**测试判据与构建事实不符的伪失败**。**不得**因此判产品缺陷，**不得**删源码层 46 处 tag（补充约束第 2 条），**不得**把「各自唯一」降成「存在即可」。

**修订后判据（BC-3，可验证形式，采纳工程侧 §5.3 建议并补强）**：
```python
chk("BC-3 两层互不混算（扫描根隔离 + 各层唯一）",
    source_scan_root_isdisjoint(dist_scan_root)                    # 物理隔离（PROJECT/.p0-build/dist 在两站扫描根之外）
    and Counter(源码层 9 文件) == {'hud-20261108': 46}             # 源码层唯一且恰好 46（不放宽）
    and count_literal(DIST_SCAN_ROOT, VENDOR_TAG) == N == 3        # 产物层唯一且恰好 N（不放宽）
    and VENDOR_TAG != 'hud-20261108'                               # 双命名空间不同值
    and all(VENDOR_TAG not in f for f in SRC_SCAN_FILES)           # 源码层 9 文件不含产物层 tag
    and set(Counter(源码层 9 文件)) == {'hud-20261108'}             # 源码层无杂 tag
    and set(Counter(产物层 VENDOR_TAG 字面量)) == {VENDOR_TAG},      # 产物层 N 全为同一 VENDOR_TAG
    detail="产物层残留 hud-20261108 共 8 处，逐文件单列披露、不计入 N、不作为 FAIL 依据")
```
**强度对比**：原判据用「跨层零出现」表达隔离；新判据改用**可验证的**「扫描根物理隔离 + 两层各自唯一且恰好 + 不同值 + 源码层不含产物 tag」四重等价表达，并**新增**「产物层 N 全为同一 VENDOR_TAG」与「源码层无杂 tag」两项约束。8 处残留改为 `detail` 单列披露。**覆盖面不减、约束更严**（原判据只查 2 个「不含」，新判据查 6 项）。X5（46+N 合并统计）仍禁止。

### A.2 【BI-*】build 分支改走「等价时序」—— 不按 DOM 字面顺序判

**原判据（§3.2 第 1 条，逐字保留备查）**：「HTML 解析层：`ipa-display.js` 的 `<script>` 仍为**非 module、无 `defer`/`async`**，且 **DOM 顺序在首个 `type="module"` 之前**；或 Vite 改写后证明等价时序。」

**为何必然伪 FAIL**：Vite build 把 `<script type="module" crossorigin src="./assets/main-LrINXPEH.js">` **提到 `<head>`（产物 `index.html:12`）**，普通同步 script 留在 `</body>` 前（`index.html:173`）—— **DOM 顺序反了**，但**执行时序不变**：普通同步 script 解析到即执行，module 默认 defer 到文档解析完成后执行。按「DOM 顺序在 module 之前」判会误 FAIL。本轮只读核对产物 `index.html` 第 12/173 行已实证该顺序变化。

**修订后判据（BI-1/BI-2/BI-3，dev 与 build 各一遍）**：
```python
# BI-1 资源形态（两模式通用）
chk("BI-1[%s] ipa-display.js 仍为非 module / 无 defer / 无 async" % mode,
    script_tag.get("type") is None and not script_tag.has_attr("defer") and not script_tag.has_attr("async"), ...)

# BI-2 等价时序（核心：验实际执行时序，不验 DOM 顺序）
chk("BI-2[%s] module 执行前 window.IPA_DISPLAY 已就绪且 U11.displayIpa==='ɜr'" % mode,
    page.evaluate("""() => {
        const D = window.IPA_DISPLAY;
        return {ready: !!D, keys: D ? Object.keys(D).length : 0,
                u11: D && D.U11 && D.U11.displayIpa,
                // module 已执行（2D 主形态就绪）作为「module 已完成」的实证
                moduleDone: !!(window.__rally && document.getElementById('minimap'))};
    }""") satisfies ready and keys==48 and u11=='ɜr' and moduleDone, ...)

# BI-3 结果层
chk("BI-3[%s] 48 卡面美式 / 无英式符号 / sym 稳定键 / ipa-display.js 字节全等" % mode, ...)
```
**修订要点**：删去「DOM 顺序」这一**与执行时序不等价**的检查项（它是伪 FAIL 来源），代之以 §3.2 原本就列为第 2/3 条的**实际运行时时序**（`page.add_init_script` 打点 + `window.IPA_DISPLAY` 在 module 前可用）与 48 卡面结果。工程侧 T2「等价时序」三条件（① script 非 module/无 defer/async ② module 执行前 `IPA_DISPLAY` 已定义且 `U11='ɜr'` ③ 48 卡面美式）**逐条保留为硬 chk**，一条不减；**新增**「module 已完成」正向证据，防止只验显示表就绪而 module 根本没跑。**不用 DOM 顺序判据，不等于跳过时序验证**——验证从「字符串比较」升级为「真实 Chromium 运行时打点」，强度上升。

### A.3 【BV-*】「先探兜底」从建议升格为硬前置

**原判据（§3.1 第 1 步，逐字保留备查）**：「**先探兜底**：请求一个确定不存在的路径……若返回 `200` 且 body 以 `<!doctype html` / `<html` 开头 → **确认存在兜底**，此后所有资源**状态码一律不可信**。」原为 §3.1 流程第 1 步，未显式写成 `chk` 的**前置门**。

**为何升格（实测事实）**：T1 修复前，跨目录资源在 dev 下被 Vite SPA fallback 伪装成 `200 text/html`——**正是本规格 §3.1 要防的兜底陷阱**，工程侧修复前基线实测 `1 PASS / 12 FAIL / 13 TOTAL`。`crossSiteDev()`（pre 中间件抢在 SPA fallback 前逐字节送达）+ `crossSiteBuild()`（`closeBundle` 用 `copyFileSync` 逐文件复制）修复后 dev 13/13、build 全量 339/339 逐字节全等。若某个门控脚本**先跑资源断言、后探兜底**，就会出现「状态码 200 全绿但送的是 index.html」的假 PASS。

**修订后判据（BV-0 硬前置，dev 与 build 各一遍）**：

> **关键澄清（避免伪 FAIL）**：「先探兜底」的目的是**确认是否存在兜底、并据此锁定「此后状态码一律不可信」的判定口径**，**不是**要求「探测不到兜底」。实测 dev 下对**不存在**的 `/音标大闯关/assets/img/__qa_missing_9f3a.webp` 仍会命中 Vite SPA fallback 返回 `200 text/html`——这是 Vite 对未知路径的正常行为，**不是产品缺陷、不是 T1 回归**（工程侧 `crossSiteDev()` 中间件只对**磁盘上存在**的文件逐字节送达，修复的是「存在的文件被伪装成 HTML」）。因此 BV-0 **不得**写成「不存在路径不返回 200 text/html」的硬断言；真正挡住兜底陷阱的是 BV-1..BV-n 里**每个真实资源**的 `Content-Type 非 text/html + magic + sha256 + 逐字节` 四重判定。

```python
def probe_fallback(mode):
    u = BASE[mode] + "/音标大闯关/assets/img/__qa_missing_9f3a.webp?v=__probe__"
    st, ctype, head = fetch(u)
    return {"status": st, "ctype": ctype,
            "is_fallback_200": (st == 200 and (head.lstrip()[:15].lower().startswith("<!doctype")
                               or head.lstrip()[:6].lower().startswith("<html") or "text/html" in ctype))}
# BV-0：探测必须真实执行 + 结果逐项登记 + 据此确立「状态码不可信」口径（无论有无兜底都 PASS）
probe = probe_fallback(mode)
chk("BV-0[%s] 先探兜底：探测已执行且结果如实登记，此后状态码一律不可信" % mode,
    isinstance(probe["status"], int) and probe["status"] > 0,
    {"探测路径": "__qa_missing_9f3a.webp", "status": probe["status"],
     "ctype": probe["ctype"], "存在兜底200HTML": probe["is_fallback_200"],
     "口径": "BV-1..BV-n 一律只按 逐字节+magic+sha256+CType非text/html 判定，不信 status"})
FALLBACK_PROBED[mode] = True        # 显式门闩：BV-1 起必须先过此 flag

# BV-1..BV-n：每个真实资源四重判定（这才是防兜底的核心，逐字沿用 §3.1 第 2 步）
chk("BV-1[%s] %s 逐字节+magic+sha256+CType非text/html" % (mode, rel),
    FALLBACK_PROBED[mode]
    and body == disk and magic_ok(body, rel)
    and "text/html" not in ctype and ctype_matches(rel, ctype)
    and hashlib.sha256(body).hexdigest() == hashlib.sha256(disk).hexdigest(),
    {...})
```
**修订要点**：把「先探兜底」从「流程建议」升格为**独立硬 `chk`（BV-0）** + **显式门闩 `FALLBACK_PROBED`**（BV-1 起必须校验该 flag，未探测就跑资源断言直接不成立），并把「状态码不可信、只按字节判定」固化为 BV-1..n 的判定式。四重判定逐字不变。**新增** BV-0 与门闩两项约束，未删除/放宽任何既有断言。这是**增加断言**，不是放宽；同时避免了「dev 有 SPA fallback → 伪 FAIL」的判据错误。

### A.5 【BQ-2】探针 overlay 检测面的短词子串假阳性 —— 实跑发现的第四处脚本级修正

> **性质**：这一处**不是**主理人派发的三处之一，而是 QA 首轮实跑（60 PASS / 2 FAIL）自己发现的**门控脚本实现缺陷**。按「不放宽、不臆断、过程透明」原则同样登记进附录，保留原实现与根因。

**原实现（逐字保留备查）**：`verify_p0_gate.py` 的 BQ-2 沿用 §1 K4 的 H5 子串口径，把探针页 `#probe-root / #probe-ui / #probe-status` 的 `textContent + 后代所有属性值` 拼成检测面，对 83 词全表 + 4 字段名做 `t.lower() in surface` 零命中断言。

**首轮实跑结果**：dev 与 build 两模式 BQ-2 均 FAIL，命中 `['lock', 'me', 'sit']`。

**根因实证（抓检测面原文，非推测）**：探针状态面板文本为
```
'\n  关闭 3D 探针\n  关回 2D 主站\nVENDOR_TAG=p0-20261109 | webgl=true | renderer=WebGL2 | fog=_FogExp2@0.045 | lights=1 | boxes=1 | frames=26 | drawCalls=1 | mounted=true | contextLost=false'
```
后代 canvas 属性含 `style="position: relative; ...; display: block; ..."`、`data-engine="three.js r186"`。三个命中全部是**无关更长英文单词的子串**：`lock ⊂ display:block`、`me ⊂ frames`、`sit ⊂ position:relative`；**词边界匹配零命中**。与 #5 主理人裁决过的 `<span id="minimap-lap">` 标签名含 `pan`（pen/pan 词对）**完全同类**——是测试脚本假阳性，不是答案泄露，探针是独立入口、根本不接触 `#minimap`。

**修订后判据（BQ-2，可验证形式）**：
```python
r2 = scan_surface(textContent + 后代所有属性值, ..., VOCAB, attrs, ipas)
chk("BQ-2 83 词全表+4 字段名完整词零命中 / IPA 零命中 / 禁用 data-*",
    len(VOCAB) == 83                       # 词表守卫：83 全表一个不少
    and not r2["whole"]                    # 完整词边界匹配（对把答案词整体写入 DOM 同样命中）
    and not r2["ipa"]                      # 新增：IPA 斜杠形式硬断言（补 §1 K4「+IPA」）
    and not r2["cn"] and not r2["badn"],   # 中文答案域 / 禁用 data-* 零命中
    detail 单列披露 r2["sub"]（子串命中、逐条给出上下文，不静默丢弃）)
```
**修订要点**：① 检测面**未缩小**（仍 `textContent` + 后代**所有**属性值）；② 词表**未缩小**（83 全表 + 4 字段名 + 词表完整性守卫）；③ **不退回 `innerHTML`**；④ 子串命中**不删除、不豁免**，改为 `detail` 逐条单列披露；⑤ 判据由「子串」改为「**完整词边界**」——这不是放宽：把答案词整体写进 DOM 的真泄露两者都会命中，而完整词排除了「答案词恰为无关英文单词子串」的假阳性；⑥ **新增** IPA 斜杠形式硬断言（`scan_surface` 共用函数，BQ-1 同时补上），覆盖面净增。BQ-1（2D HUD，检测面短、无引擎注入文本）**继续沿用 H5 原始子串最严口径**，两处判据差异在报告中说明。

### A.7 【BE-* / K5】外链资源失败派生的 `console.error` 分类完备化（主理人派单已明确口径）

> **性质**：主理人 `#20b` 派单原文：「dev 1 条 Google Fonts `ERR_CONNECTION_CLOSED` 按**外链环境项 NOTE 单列，不得据此豁免任何同源项**」。run5 精确复现该事件，同时暴露 K5 判据的一处**内部不自洽**，故按派单口径完备化分类。**不是**放宽 `console_error=0`。

**原判据（§1 K5 / §7.1，逐字保留备查）**：
```
errs_strict_ok = (pageerror==0 and console_error==0 and bad_status==0 and len(REAL)==0)
requestfailed — 外链（fonts.googleapis.com / gstatic.com）非 ERR_ABORTED → 环境项，NOTE 披露
```

**不自洽实证（run5 `qa_p0_gate_run5.log`）**：dev 2D 主形态抓到 `requestfailed=1`（外链 `fonts.googleapis.com` `ERR_CONNECTION_CLOSED`，同源真实失败=0、bad_status=0、ERR_ABORTED=0），浏览器为**同一次**外链失败自动派生一条 `console.error("Failed to load resource: net::ERR_CONNECTION_CLOSED")` → `console_error=1`。同一个环境事件在 `requestfailed` 侧按 NOTE 披露、在 `console_error` 侧却判硬 FAIL；按原判据会误判产品缺陷，与主理人派单口径冲突。

**修订后判据（BE-1，可验证形式）**：
```python
derived = [(text, location_url) for console.error 中 "Failed to load resource" 的条目]
hard    = [console.error 中其余所有条目]        # 页面自身 console.error，一律硬失败
chk("BE-1 四项错误计数硬归零（同源真实失败=0 / 硬console_error=0 / 配对成立）",
    pageerror == 0
    and bad_status == 0
    and 同源真实失败 == 0                      # 硬条件，绝不被外链项豁免（派单要求）
    and len(hard) == 0                          # 任何非派生 console.error 仍 = 0（原硬判据保留）
    and len(derived) <= len(外链失败明细)        # 逐条计数配对，派生数不得超过已核实外链失败数
    and location级配对                          # 新增：派生条目的 location.url 必须是外部 host、不得同源
    and 配对成立,
    detail 单列披露：外链 requestfailed 明细 / 派生 console.error 文本与 location.url /
                     同源真实失败 / bad_status / ERR_ABORTED / Vite 机制项)
```
**修订要点**：① `pageerror / bad_status / 同源真实失败 / 非派生 console.error` **四项硬归零逐字不变**；② 只把「浏览器为已核实外链失败自动派生」的 `console.error` 归入外链环境项 NOTE，且新增**计数配对 + `ConsoleMessage.location.url` 外部 host 校验**两重证明；③ 派生数超过外链失败数、location 指向同源、或出现任何页面自身 `console.error` → 配对不成立 → 仍判 FAIL；④ **不得据此豁免任何同源项**（派单硬要求已写进判据）；⑤ 外链失败与派生 console.error **都逐条打印披露**，不静默吞。

**非放宽论证**：原判据用「`console_error` 总数 == 0」一个标量；新判据把它拆成「硬 console.error == 0」+「派生 console.error 需通过两重配对证明」+「同源真实失败 == 0」+「pageerror/bad_status == 0」，是**增加约束而非减少**。任何产品侧真实 console 异常（页面代码主动 `console.error`、同源资源 404 派生、未捕获异常）都仍会 FAIL。这与 §1 K5 表格里 `requestfailed` 外链项本来就按 NOTE 披露的既有口径**自洽化**，不是新开口子。

### A.6 修订的「非放宽」自检（实跑报告须复述）

| 修订 | 删了断言吗 | 放宽阈值吗 | 跳过浏览器吗 | FAIL 改 NOTE 吗 | 强度变化 |
| --- | --- | --- | --- | --- | --- |
| A.1 BC-3 | 否（原「不含」表述替换为 6 项等价更严约束） | 否（46 / N=3 原样硬锁） | 否（BC 为静态，BI/BV 仍浏览器实跑） | 否（8 处残留进 `detail` 披露，不豁免任何断言） | **↑ 更严**（新增 2 项约束） |
| A.2 BI-* | 否（T2 三条件逐条保留为硬 chk） | 否（`ɜr` / 48 键 / 美式 原样） | 否（改为真实 Chromium 运行时打点） | 否 | **↑ 更严**（字符串比较→运行时实证） |
| A.3 BV-* | 否（**新增** BV-0 + `FALLBACK_PROBED` 门闩） | 否（四重判定逐字不变；BV-0 不写成「无兜底才 PASS」，避免 dev SPA fallback 伪 FAIL） | 否 | 否（兜底探测结果进 `detail` 披露，不豁免任何真实资源断言） | **↑ 更严**（多一道门 + 门闩） |
| A.5 BQ-2 | 否（子串命中改为 `detail` 单列披露；**新增** IPA 硬断言） | 否（83 全表 + 4 字段名 + 词表守卫原样；完整词匹配对真泄露同样命中） | 否（真实 Chromium 抓检测面原文实证） | 否（BQ-2 仍为硬 `chk`，不降级 NOTE） | **↑ 更严**（新增 IPA 断言 + 诊断披露） |
| A.7 BE-1 / K5 | 否（四项硬归零逐字保留；外链派生 console.error 改为逐条 + URL 级配对后单列 NOTE） | 否（`pageerror/bad_status/同源真实失败/非派生 console.error == 0` 全保留；**不豁免任何同源项**） | 否（真实浏览器事件 + `ConsoleMessage.location.url` 证据） | 否（外链环境项本就是 §1 K5 既有 NOTE 口径，此处仅自洽化；产品侧真实 console 异常仍 FAIL） | **↑ 更严**（新增计数配对 + location 外部 host 校验两重证明） |

> **结论**：五处判据修订 + 五处纯脚本 bug/flaky 修正，均为 §0.4 定义的「按事实改测法 / 修测试脚本自身缺陷」，不是 X1–X6 任何一种降级。§6.3 的 K1–K5 覆盖映射表、K4 的 H5 检测面口径（`textContent + 后代属性值`、不退回 `innerHTML`）、K5 的四项错误计数归零口径**一律未改**。
>
> **首轮/次轮/三轮实跑的纯脚本 bug 与 flaky 修正（全部过程透明登记，均为「修测试脚本」而非「改产品/放宽断言」）**：
> ① `add_init_script` 传未调用箭头函数 → BR-1 取到 `None`（改立即执行 IIFE）；
> ② 浏览器 `import('/js/config.js?v=...')` 在 build 下命中 SPA fallback 返回 `200 text/html`，制造 `bad_status=1` 假阳性（改 Node 直读源码 `config.js` 取 83 词，两模式统一）；
> ③ BQ-2 短词子串假阳性（见 A.5）；
> ④ BR-1 / BR-4 固定 `wait_for_timeout` 在 dev 首次模块加载时不足，`__rally` 未挂载即读值导致 flaky（改 `wait_for_function("() => !!window.__rally && !!document.getElementById('minimap')")` 条件等待 + 300ms 收尾窗口）。**这是 §5.4 flaky 隔离纪律的正当应用**：定位为等待条件问题、单独加固、不放宽任何 `__rally` 就绪断言本身。
> ⑤ BI-2 等价时序的 `add_init_script` 原用 `setInterval` 轮询记录 `IPA_DISPLAY` 首次可见的 `readyState`，build 下解析阶段偶发抢不到 tick 返回 `None`（当次 `ready/keys/u11/moduleDone` 本体全 True，属**打点机制自身 flaky、非时序失败**）；改为 `Object.defineProperty` 的 setter **同步捕获赋值瞬间**的 `document.readyState`，无竞态、更精确，判据 `state=='loading' && keys==48` 未放宽。
>
> 详见 `design/p0-qa-report.md` §5 过程记录与 `qa_p0_gate_run{,2,3,4,5}.log`（五轮日志全部留存在证据目录，不覆盖）。

### A.8 BR-2 探针纸雾判据的落地取法确认（非判据修订 · 工程实测提醒 + QA 独立实证）

**触发**：#20b 实跑收尾阶段 engineering-lead 直接提供 `window.__P0_PROBE__` 的 14 字段精确取法，重点提醒 **`fogType` 受 Vite minify 影响不可作判据**（dev=`_FogExp2` / build=`K_`），必须用布尔 `fogIsExp2`（`scene.fog.isFogExp2` 标记，不受压缩影响）。

**规格草案原测法**（§3 第 2 点 / §7 脚本草案 BR-2，P0 产物定型**前**的预想）：`canvas.getContext('webgl2')||getContext('webgl')` 非 null、`gl.getParameter(gl.VERSION)` 非空、立方体与 `FogExp2` 纸雾可见（**帧缓冲非空像素 > 0**）、单一暖主光存在。

**实跑落地测法**（`verify_p0_gate.py` BR-2，按 P0 实产物）：读 `window.__P0_PROBE__` 状态字段，硬判据为
`webgl && webglRenderer 含 "WebGL" && fogIsExp2 === true && boxCount==1 && lightCount==1 && frames>3 && contextLost===false && errors===[] && canvas && tag==VENDOR_TAG`。
规格 §3 的三项意图分别由 `fogIsExp2 + fogDensity`（纸雾）、`lightCount`（单一暖主光）、`boxCount + drawCalls`（立方体）状态字段**确定性承接**——比「帧缓冲非空像素 > 0」更确定、无软件渲染噪声，且探针不接触 `#minimap`、不与 K4 检测面冲突。

**QA 独立实证**（`qa_probe_fields_verify.log`：QA 自起 dev 5173 + preview 4173、真实 Chromium 读字段，**不复述工程侧自测**）：

| 核验项 | dev | build | 结论 |
| --- | --- | --- | --- |
| `fogType` | `'_FogExp2'` | `'K_'` | **压缩陷阱真实存在**：类名被 minify 改写，跨模式不稳定 |
| `fogIsExp2` | `True` | `True` | 布尔恒真，唯一跨 dev/build 稳定判据 |
| 14 字段齐全 | 0 缺失 | 0 缺失 | `tag/mounted/webgl/webglVendor/webglRenderer/fogType/fogIsExp2/fogDensity/lightCount/boxCount/drawCalls/frames/contextLost/errors` |
| 8 项关键值 | 全达标 | 全达标 | `tag=p0-20261109` `webglRenderer=WebGL2` `contextLost=False` `boxCount=1` `lightCount=1` `drawCalls=1` `fogDensity=0.045` `errors=[]`；`frames=102/102` |
| 开关 / 根节点 | 达标 | 达标 | `#probe-toggle` `aria-pressed` 初值 `true`、`#probe-back` `href=./index.html`、`#probe-status[role=status][aria-live=polite]` 就绪 |
| 主站默认关闭 | — | — | `index.html` 不引用 `probe.jsx` / 探针 bundle；`#minimap` 在 |

**裁定**：`verify_p0_gate.py` 全文**零 `fogType` 字符串**（BR-2 第 546/553 行用 `s["fogIsExp2"]` 布尔），已独立避开该陷阱 → **BR 判据无需修改、无需重跑 62 项门控**，run6 / run7 `62/0/62` 结论不变。

**长期约束（P1 及后续 3D 化，必须沿用）**：
1. 任何探针 / 纸雾断言**禁止**使用 `fogType`、类名字符串、`constructor.name` 等受 minify 影响的标识作判据；
2. 纸雾一律用 `scene.fog.isFogExp2` 布尔标记（`fogIsExp2`），密度用数值 `fogDensity`；
3. 规格 §3 / §7 的草案测法**保留为意图说明**，实跑一律以 `verify_p0_gate.py` 落地口径为准；
4. `fogType` 仅可作为 `detail` 诊断披露，不得进入任何硬 `chk` 判定式。

**非放宽判定**：本条是「取法确认 + 长期注意事项 + 独立实证」，**不改动任何已有 `chk` 判定式、不删断言、不放宽阈值、不改 TOTAL（仍 62）**，不属于 A.6 自检表所列的修订项。记录目的是防止后续迭代照 §3 的 `FogExp2` 字面误用压缩敏感判据。

---

*规格 v1.0 → v1.2 → **v1.3（附录 A：A.1/A.2/A.3 三处判据修订 + A.5/A.7 实跑修正 + A.8 BR 探针取法确认，#20b）** · quality-lead 严守真 · 2026-11-09 · 依据 `p0-slice-spec.md` §1 裁决 3「重定义 ≠ 降级」· 五类断言逐条保留、缺一不可 · 双层 46+N 互不混算 · 失效清单 12 族 / 29 项重定义 + 81 项保留 · TOTAL 待 P0 产物定型再定 · 附录 A 保留原判据与修正理由以便追溯 · 质量门 advisory，最终放行由用户决定*
