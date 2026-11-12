# P0 切片实现报告 · 路线 B（Vite + React + R3F）整站接管

> **文档性质**：Task #19 / CSEG-P0 的实现与自测报告（engineering-lead 程基岩）。**唯一权威规格** = `design/p0-slice-spec.md`；门控重定义规格 = `design/p0-qa-spec.md`（quality-lead，只读规格，本轮不改任何脚本）。
> **日期**：2026-11-09 · **上游依据**：`p0-slice-spec.md` §0 用户四项拍板 / §1 三条裁决 / §2 范围与 Go/No-Go / §3 T1–T5；`3d-tech-feasibility.md` §8 P0；`3d-adr.md`；`stage-delivery-2026-11-09.md`。
> **补充约束**：team-lead 转达 quality-lead 扫描根污染风险（§2.6 / §4 F-01~F-12 / §9），三条硬要求见本报告 §1.2。
> **边界**：本地工程改造。**不部署、不上线、不 commit、不建 git 仓库、不改 `音标大闯关/deploy.sh`**。P0 不装 Rapier、不接 GLB / Polyspoon 社区模型、不引 CDN 运行时依赖、不新增 localStorage 字段。
> **证据落点（已持久化）**：全部实测脚本与结论已**复制**（不剪切、不删除原件）到项目内 `.workbuddy/backups/p0-evidence-20261109/`（**384 文件 / 78,828,206 B**，逐文件字节数 + sha256 全值 + 用途见该目录 `manifest.txt`）；原始采集于 `%TEMP%`，**仅为溯源、不再作为运行时依赖**。该目录位于项目根、不在两站扫描根内。**P0 证据链 0 处 Temp 运行时依赖**。逐项路径见 §4.3 / §8.1。

---

## §0 交付结论与 Go/No-Go 七项逐条结果

**总体**：P0 切片已落地并自测完成。2D 作为 L0 主形态原样可玩；R3F 探针为**独立入口、默认关闭**；判定核心逐字未改；跨目录资源在 dev 与 build 双模式按字节送达；双层缓存命名空间实测隔离。

| # | Go/No-Go 条件（`p0-slice-spec.md` §2） | 判据 | 实测结果 | 判定 |
|---|---|---|---|---|
| 1 | 判定未受影响 | `node js/headless_laps.mjs` 11 场 ALL PASS，最慢 ≤180s | 11 场 ALL PASS，最慢 **174.57s**（follow camp/peak worst），`题库: 地图 4 词对 37 词 83 题型 3` | ✅ PASS |
| 2 | 2D 主形态可用 | dev 与 build 下完整可玩（真实 Chromium，含 375×780） | dev/build × 375×780：`canvas` / `#minimap` / `#panel-title` / `#btn-listen` / `window.__rally` / `mode==='title'` 全部就绪；触发听辨档 handler 后 `mode=teach` | ✅ PASS |
| 3 | 3D 探针可用 | 375px / 320×568 WebGL 上下文、立方体与纸雾可见、可一键关回 2D | 4 组合（dev/build × 375×780/320×568）全部 `WebGL2`、`boxCount=1`、`fogIsExp2=true`、`fogDensity=0.045`、`lightCount=1`、`drawCalls=1`、`frames>110`、`contextLost=false`；`#probe-toggle` 卸载 Canvas、`#probe-back` 返回 `index.html` | ✅ PASS |
| 4 | 资源送达 | 逐字节 + magic + sha256 + Content-Type 非 `text/html`（**不信状态码**） | dev **13/13**；build **spot 8/8 + 全量 339/339 逐字节全等**；兜底陷阱先探（§3 T1） | ✅ PASS |
| 5 | 零外链 | 无产品功能依赖的外部 host 请求（Google Fonts 单列） | `other_external=[]`；仅 `fonts.googleapis.com` / `fonts.gstatic.com` 已知项；dev 抓到 1 次外链 `ERR_CONNECTION_CLOSED`（环境项单列），**同源真实失败 = 0** | ✅ PASS |
| 6 | 体积 | 记录 dev/build 首屏 JS 体积、请求数、帧时间 | dev 101 entries / 2,701,464 B / JS 1,063,246 B；build 93 entries / 1,498,619 B / JS 27,869 B；探针 `frames` 112–123 / 1.8 s（SwiftShader 软件渲染 ≈62–68 fps，非真机 GPU，见 §11 R6） | ✅ 记录项 |
| 7 | 门控 | quality-lead 新规格跑通，覆盖面满足 §1 裁决 3 | **本轮未实跑**（依 §4 分派与 `p0-qa-spec.md` §11，实跑由 quality-lead 在新门控中、待主理人通知后进行）。本轮已备齐 §9 十项产物信息、未改任何验收脚本、源码层 46 静态核实精确通过；失效预测清单见 §7 | ⏸ 待 QA 实跑 |

> **诚实口径**：第 7 项不写「全绿」。原五套门控在 Vite 接管后**服务模型与扫描根已变**，本轮允许失败、如实报告（§7），不以「构建通过」替代浏览器实跑、不改脚本掩盖。

---

## §1 三条主理人裁决 + 补充约束三条硬要求 · 逐条核验

### 1.1 `p0-slice-spec.md` §1 三条裁决

| 裁决 | 核验方式 | 结果 |
|---|---|---|
| **裁决 1 · 判定核心零改动** | `js/race.js` / `js/track.js` / `js/config.js` / `js/main.js` / `js/headless_laps.mjs` 与 P0 前全量快照逐文件 sha256 比对；`node js/headless_laps.mjs` **原路径原命令**实跑 | 17/17 关键文件 sha256 全等（§8）；11 场 ALL PASS / 174.57s。`odo/lateral`、`g.line`、`buildGates()`、`judge()`、`beginDecide()`、`hitsLane()`、`TUNING.laps=2`、follow 260 / listen 300 仍在原生 JS ESM 文件中，未移植 TS、未进 React state、未由 rAF 驱动。`js/main.js` 主循环本轮**未改** |
| **裁决 2 · 46 + N 各自唯一** | 源码层 9 文件白名单扫 `\?v=`；产物层 `.p0-build/dist/` 扫 `VENDOR_TAG` 字面量 | 源码层 `{'hud-20261108': 46}`（9 文件分布 17/6/1/3/2 + 7/7/2/1）；产物层 `VENDOR_TAG=p0-20261109`，**N=3**。两层扫描根物理隔离（§5/§6）。20 个图片 URL 零裸引用实测 `bare_count=0` |
| **裁决 3 · 重定义 ≠ 降级** | 五类断言 K1–K5 的证据链是否齐备 | K1（sha256 + 11 场）、K2（跨站单键，逻辑源码零改动 + 零新增字段）、K3（`IPA_DISPLAY` 48 键 / `U01='i'` / `U07='ɑ'` / `ipa-display.js` 字节全等）、K4（83 词全表与 HUD DOM 零改动，探针为独立入口不接触 `#minimap`）、K5（四项错误计数全 0 + 同源真实失败 0）证据均已备齐；覆盖面是否最终判定由 quality-lead 的 §6.3 映射表填写，**engineering-lead 不替 QA 判定** |

**ADR-2 保持 Accepted 且内容不变**：Rapier 只进视觉层、绝不替换 `odo/lateral + g.line` 判定。P0 未安装 Rapier（`vendor.manifest.json` 的 `intentionally_not_installed` 已列明）；`3d-adr.md` 中 ADR-2 正文逐字未改，仅索引状态按 team-lead 指令由 Proposed 更正为 Accepted（§2 / §12 说明）。

### 1.2 补充约束三条硬要求（team-lead 转达 quality-lead）

| # | 硬要求 | 本轮处置 | 证据 |
|---|---|---|---|
| **1** | **不要修改五套验收脚本中的任何一行**；扫描根白名单化由 quality-lead 在新门控里做 | **零改动**。`verify_cseg_gate.py` / `verify_cseg_ui.py` / `verify_fresh_gate.py` / `verify_c08_gate.py` / `verify_hud_spec.py` 与 P0 前快照 sha256 全等（§8 表逐项）。本轮所有自测脚本已**持久化**到 `.workbuddy/backups/p0-evidence-20261109/`（原始采集于 `%TEMP%`，仅溯源），不落任何 `.py` / `.mjs` 到两站扫描根 | §8 sha256 表 / §8.1 |
| **2** | 源码层 `hud-20261108` 46 处 `?v=` 字面量一个都不能删、不能批量替换、不能为适配构建链改写 | **零删除、零替换**。9 文件白名单实测 `TOTAL=46 / HIST={'hud-20261108':46}`；`index.html` / `css/game.css` / `js/*` 与快照逐字节一致。产物层的 content-hash 是 Vite **自己生成**的另一层，源码层字面量原样保留（build 后 `index.html` 仍带 5 处 `?v=hud-20261108`，见 §9-6） | §5.1 / §9-6 |
| **3** | 若 Vite 配置允许，优先考虑把 `dist/` 与 `node_modules/` 落点放在两站扫描根之外；说明是否与 T3 冲突；冲突则如实给结论与部署建议 | **`dist` 已外置**：`build.outDir` = `<项目根>/.p0-build/dist/`（项目根下独立目录，两站扫描根之外），旧 `音标拉力赛/dist/` 已移出。**`node_modules` 未外置**：其落点由 npm 依 `package.json` 位置决定，**不由 Vite 配置控制**，外置需把工程根上提，与裁决 1「`node js/headless_laps.mjs` 原路径原命令」及 dev/build 启动 cwd 冲突 → 不硬凑，结论见 §6.2 / §6.3。**与 T3 不冲突**（论证见 §6.4） | §6 全节 |

**F-08 / F-09 实测留意项（无需改产品，不预先豁免）**：
- F-08：dev 下 Vite 注入 `/@vite/client`（实测 1 处请求，无 `?v=`）；原 `F10a` 的 `stale_router` 正则会误命中。本轮**不替 QA 预先豁免**，只如实分类（§4.2 network 分类表）。
- F-09：dev 下 `requestfailed` 明细捕获 1 条外链字体失败；HMR WebSocket / `/@fs/` / `/@id/` / `/node_modules/.vite/deps/` 本轮实测均为 0 次请求。**同源真实失败 = 0** 是硬口径，未因 Vite 机制项或外链而放宽。

---

## §2 逐文件改动清单

| 文件 | 性质 | 内容 | 是否落在扫描根 |
|---|---|---|---|
| `音标拉力赛/package.json` | 新增 | `ipa-rally-p0`；`type:module`；scripts `dev/build/preview/headless/test:minimap`；6 个 runtime + 2 个 dev 依赖精确钉版（§9-3） | 是（`.json`，不在 S17 的 `.html/.js/.css` 扫描范围） |
| `音标拉力赛/package-lock.json` | 新增 | npm 10.9.7 解析锁，87737 B | 是（`.json`） |
| `音标拉力赛/vite.config.js` | 新增 | `root/base/server.fs/build.outDir/publicDir` + `crossSiteDev()` / `crossSiteBuild()` 双插件；`VENDOR_TAG=p0-20261109`；**补充约束第 3 条：`OUT_DIR` 外置**（§9-1） | **是**（`.js`）。全文**不含**源码层 tag 字面量、不含裸图片 URL（第 14 行注释明确），故不污染 S17/S18 直方图 |
| `音标拉力赛/probe.html` | 新增 | R3F 探针独立入口；`#probe-root` / `#probe-ui` / `#probe-toggle` / `#probe-back` / `#probe-status`；`<link rel="icon" href="data:,">` 消除 favicon 404 | **是**（`.html`）。全文无 `?v=` 字面量、无裸图片 URL |
| `音标拉力赛/js/probe.jsx` | 新增 | React + `@react-three/fiber` 最小场景：1 立方体 + `FogExp2` 纸雾 + 1 暖主光；`window.__P0_PROBE__` 可观测状态；`fogIsExp2` 布尔判定规避 build minify 类名 | **是**（`.jsx`，不在 `.html/.js/.css` 扫描范围） |
| `音标拉力赛/vendor.manifest.json` | 新增 | `schema=ipa-rally/vendor-manifest/v1`；`VENDOR_TAG`；`cache_namespaces`；`pinned[]` 9 项；`peer_upper_bounds_verified[]` 5 项；`intentionally_not_installed[]` | 是（`.json`） |
| `.p0-build/dist/`（项目根） | 新增（构建产物） | `npm run build` 输出：351 文件（§9-5） | **否**（项目根下，两站扫描根之外） |
| `音标拉力赛/node_modules/` | 新增（依赖） | npm 安装 9361 文件 | **是**（数千 `.js`/`.css`，是扫描根污染的唯一剩余来源，§6.2） |
| `design/3d-adr.md` | 修改 | 按路线 B 增补 ADR-1B/3B/4B/5B/6B（每条含 Context/Decision/Consequences/Alternatives/回滚路径）；原 ADR-1/3/4/5/6 标 Superseded；**ADR-2 正文逐字未改**，索引状态更正为 Accepted | 否（`.md`） |
| `design/p0-impl-report.md` | 新增 | 本文件 | 否（`.md`） |
| **未改** | — | `index.html` / `css/game.css` / `js/race.js` / `js/track.js` / `js/config.js` / `js/main.js` / `js/render.js` / `js/headless_laps.mjs` / `js/minimap_model.test.mjs` / `js/data.js` / `js/ipa-display.js` / 48 立绘 / 48 卡面 / 29 成稿图 / 83 mp3 / 上游构建管线 / 五套验收脚本 / `音标大闯关/deploy.sh` | §8 sha256 逐项全等 |

> **明确未做**：未改 `js/main.js` 主循环、未把 2D `render()` 迁进 React、未新增 `<script src>`/`<link>`/`<img src>` 到主站 `index.html`、未重跑上游管线、未新增 localStorage 字段、未引 CDN 运行时依赖、未装 Rapier / GLB / Polyspoon 社区模型。

---

## §3 五个技术风险 T1–T5 实测结论（不臆造方案，全部附证据）

### T1 · 跨目录资源 —— 已解决

**实测事实（修复前 baseline）**：Vite `root=音标拉力赛/` 时，`index.html` 的 `../音标大闯关/...` 在浏览器里被规范化为 `/音标大闯关/...`，dev 下命中 **SPA fallback → `200 text/html`（伪装成资源，不是真资源）**。修复前 `_p0_resource_dev-baseline.json`：**1 PASS / 12 FAIL / 13 TOTAL**。

**根因（两条，缺一不可）**：
1. `server.fs.allow` 只解决 Vite 自身读取 root 外的**静态引用**；动态拼接的 48 立绘 / 48 卡面 / 83 audio 不是静态引用，Vite 静态分析抓不到。
2. `vite build` 只把 `index.html` 里 **4 个静态 `../` 图片** hash 化进 `assets/`；动态拼接资源、`ipa-display.js`、29 成稿图、83 audio **都不进产物**。

**解法（自定义双插件，非 `publicDir`、非 `server.fs` 单靠）**：
- `crossSiteDev()`（`apply:"serve"`，`configureServer` 注册为 **pre 中间件**，抢在 Vite SPA fallback 之前）：把 `/音标大闯关/<rel>` 映射到磁盘 `../音标大闯关/<rel>`，`decodeURIComponent` + `safeJoin` 防目录穿越，`createReadStream` **逐字节送达、不 transform**，带正确 MIME + `Cache-Control:no-cache` + `X-P0-Cross-Site`。
- `crossSiteBuild()`（`apply:"build"`，`closeBundle()`）：`copyTreeSync()` 纯 JS 逐文件 `copyFileSync` 递归，把 QUEST `assets/`（48 立绘 + 48 卡面 + 29 成稿图 + favicon/a1）、`js/ipa-display.js`、RALLY `audio/`（83 mp3 + 126 opus）、`vendor.manifest.json` 复制进 outDir，**保持与源码层完全一致的 URL 路径**。
- **Windows 中文路径坑（实测）**：Node v22.22.2 下 `fs.cpSync(src,dst,{recursive:true})` 会让进程**静默崩溃**（exit 127、try/catch 接不住、日志停在调用前，见 `_p0_diag_cp.log` / `_p0_diag_cp.mjs`）。改用 `copyFileSync` 逐文件递归，可捕获、可计数、可校验。

**实测结果**：dev **13/13**（`_p0_resource_dev-final3.json`）；build **spot 8/8 + 全量 339/339 逐字节全等**（`_p0_build_resource.json`）；build 日志 `copied 341 file(s) into dist`。

### T2 · `ipa-display.js` 普通同步 script 时序 —— 时序成立，但 DOM 顺序在 build 下改变（须如实告知 QA）

- **源码层**：`index.html` 逐字未改，普通 script 在首个 `type="module"` **之前**，注释明确「普通脚本同步执行；module 默认 defer」。
- **dev**：Vite 原样保留普通 script（非 module、无 `defer/async`），DOM 顺序不变。
- **build**：Vite 把 `<script type="module" crossorigin src="./assets/main-LrINXPEH.js">` **提到 `<head>`（产物 `index.html:12`）**，而普通同步 script 留在 `</body>` 前（`index.html:173`）——**DOM 顺序反了**，但**执行时序不变**：普通同步 script 在 HTML 解析到它时立即执行，module 默认 defer 到文档解析完成后执行。build 仅警告 `<script ...> can't be bundled without type="module" attribute`（`_p0_build5.log:2`）。
- **运行时实证**：dev 与 build 的 2D 冒烟均 `window.IPA_DISPLAY ready=true, keys=48, U01='i', U07='ɑ'`（U05/U07 同为 `ɑ`，`sym` 稳定键口径仍成立）。

> **给 QA 的口径**（`p0-qa-spec.md` §3.2 / `BI-*`）：build 形态属于「**Vite 改写后证明等价时序**」分支，**不能**用「普通 script DOM 顺序在 module 之前」当判据（会误判 FAIL）；正确判据 = ① script 仍非 module / 无 `defer`/`async`；② module 执行前 `window.IPA_DISPLAY` 已定义且 `U11.displayIpa==='ɜr'`；③ 48 卡面美式。本轮已证 ①②③ 中 ①③ 与「48 键就绪」，`ɜr` 单项沿用既有 `F9a`/`H11` 口径（源码零改动，未单独重跑）。

### T3 · `../音标大闯关/index.html#/map` 与 `dist/` 形态同源 —— 结论与部署建议（不实施发布）

见 §6.4（与补充约束第 3 条的 T3 冲突判断合并给出）。

### T4 · 缓存双命名空间 —— 并存且互不混算，但产物层**残留**源码层 tag（须如实告知 QA）

- **源码层**：`?v=hud-20261108` 46 处，唯一（§5.1）。
- **产物层**：`VENDOR_TAG=p0-20261109` + Vite content-hash 文件名（`main-LrINXPEH.js` / `probe-CoDaedyP.js` / `main-BTe9nwNt.css` / 4 个 `*-xxxxxxxx.webp|png`）。
- **network 实测**（`_p0_network_class.json`）：dev 18 个请求中 `?v=hud-20261108` **13** 处、content-hash **0** 处、`/@vite/client` 1 处；build 17 个请求中 `?v=` **5** 处、content-hash **3** 处、`/@vite/client` 0 处。冒烟脚本（networkidle 更完整）记录 dev **14** 处 / build **6** 处 `?v=` + build **4** 处 content-hash。两套数字口径不同（采样时机），均证明双命名空间并存。
- **重要事实**：Vite **保留**源码里的查询串（静态图片改为 `./assets/a1-D_38OaQl.webp?v=hud-20261108`），且普通 script 与 bundle 内模块 specifier 也带 `?v=`。因此产物层实测**残留 8 处 `hud-20261108`**（`index.html` 5 + `vendor.manifest.json` 1 + `main-LrINXPEH.js` 2），**不是「消失或变形」**。这直接影响 QA `BC-3` 的判据写法，见 §5.3。

### T5 · 字体外链 —— 单列披露，未用来掩盖同源失败

- 已知项：`fonts.googleapis.com` / `fonts.gstatic.com`（`index.html` 的 `preconnect` + ZCOOL KuaiLe stylesheet），P0 未改。
- 实测 `other_external=[]`（无其它外部 host）。
- dev 的 `network_class` 捕获 **1 条** `https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&display=swap :: net::ERR_CONNECTION_CLOSED`；build 0 条。**按 K5 口径属外链环境项，NOTE 单列**。
- **同源真实失败 = 0**（`_p0_rerun_summary.json: same_origin_real_failures=0`）。资源送达另由逐字节 + magic + sha256 四重判定覆盖，**不信状态码**。未把该外链失败计进产品失败，也**未**用它豁免任何同源项。

---

## §4 实测证据总表与串行运行纪律

### 4.1 结果总表（同一配置基线，`dist` 外置后重跑）

| 项 | 结果 | 证据 |
|---|---|---|
| 浏览器冒烟（dev/build × 2D/探针 × 375×780/320×568） | **39 PASS / 0 FAIL / 39 TOTAL** | `_p0_browser_smoke.json` / `_p0_browser_smoke2.log` |
| dev 资源送达（10 ASSET 逐字节 + 3 MODULE 分口径） | **13 PASS / 0 FAIL** | `_p0_resource_dev-final3.json` |
| build 产物跨目录资产 | **spot 8/8 + 全量 339/339 逐字节全等** | `_p0_build_resource.json` |
| `node js/headless_laps.mjs` 原路径原命令 | **11 场 ALL PASS**，max 174.57s ≤180s | `_p0_headless.log` / `_p0_rerun_all.log` |
| `vite build` | EXIT=0，56 modules，5.62s，341 文件复制 | `_p0_build5.log` |
| 四项错误计数（dev/build 2D + 探针） | `pageerror/console_error/requestfailed/bad_status` **全 0** | `_p0_browser_smoke.json` |
| 同源真实失败 | **0** | `_p0_network_class.json` / `_p0_rerun_summary.json` |
| 静态核实：17 关键文件 sha256 / 46 tag / 裸引用 | **17/17 全等** / `{'hud-20261108':46}` / `bare_count=0` | §8（本轮 python inline 输出） |
| 扫描根污染模拟 | A 口径 5092 文件 / 5 tag → S17 False；B 口径 24 文件 / 46 → PASS；C 9 文件白名单 / 46 → PASS | §6.2（本轮 python inline 输出） |

### 4.2 network 明细分类（F-08 / F-09 单列，不预先豁免）

| 类别 | dev | build | 口径 |
|---|---|---|---|
| `?v=hud-20261108` 请求 | 13 | 5 | 源码层命名空间 |
| content-hash 请求 | 0 | 3 | 产物层命名空间 |
| `/@vite/client` | **1** | 0 | Vite 机制项（F-08：无 `?v=`，原 F10a 正则会误命中） |
| `/@fs/` `/@id/` `/node_modules/.vite/deps/` | 0 | 0 | dev 内部路径（F-09） |
| HMR WebSocket | 0 | 0 | Vite 机制项 |
| `fonts.*` 外链 | 1 | 8 | 已知环境项（T5） |
| 其它外部 host | **0** | **0** | 零外链 |
| `bad_status(>=400)` | 0 | 0 | 硬失败口径 |
| `requestfailed` 明细 | 1（外链 `ERR_CONNECTION_CLOSED`） | 0 | 外链单列 |
| **同源真实失败** | **0** | **0** | **硬条件** |

### 4.3 证据文件与运行纪律（全部已持久化）

> **根路径**：以下所有 `_p0_*` 文件均位于 **`.workbuddy/backups/p0-evidence-20261109/`**（项目数据目录）。原始采集于 `%TEMP%`，**已复制持久化、不剪切**；`%TEMP%` 原件保留但**仅作溯源，不再是运行时依赖**。逐文件字节数 + sha256 全值 + 用途见该目录 `manifest.txt`（384 文件 / 78,828,206 B）。**P0 证据链 0 处 Temp 运行时依赖**——任何断言、门控、回滚动作均不得再读取 `%TEMP%`。

- 编排：`p0-evidence-20261109/_p0_rerun_all.py`（起 dev 5173 + preview 4173 → 串行 5 项实测 → VENDOR_TAG N → network 分类 → **显式 terminate 两个 server**，日志 `_p0_rerun_all.log` / 汇总 `_p0_rerun_summary.json`）。收尾实测 `port 5173 FREE` / `port 4173 FREE`。
- 单个脚本：`_p0_browser_smoke.py`、`_p0_resource_check.py`、`_p0_build_resource_check.py`、`_p0_snapshot.py`、`_p0_diag_cp.mjs`（复现 `fs.cpSync` 崩溃）、`_p0_diag_smoke.py`、`_p0_npm_scripts_check.py`（`npm run dev/preview` 启动命令直接实测）。
- 结论 JSON：`_p0_browser_smoke.json`、`_p0_resource_dev-final3.json`、`_p0_build_resource.json`、`_p0_vendor_n.json`、`_p0_network_class.json`、`_p0_rerun_summary.json`、`_p0_npm_scripts_check.json`；历史基线 `_p0_resource_dev-baseline.json`（1 PASS/12 FAIL，T1 陷阱证据）。
- 旧 dist 对照：`p0-evidence-20261109/_p0_dist_legacy_20261109/`（351 文件 / 76 M，**已全部复制**，未静默省略；内容可由 `npm run build` 重建，项目内已有等价 `.p0-build/dist/`）。
- **串行纪律**：沿用 `hud-qa-plan.md` §1 / `p0-qa-spec.md` §5.1，浏览器门控不并行、server 用完即释放端口。本轮编排脚本在 `finally` 中显式 `terminate()` + 端口复核。
- **持久化动机（历史教训）**：2026-11-09 系统 Temp 清理抹掉 5 个历史回滚点，导致 `verify_fresh_gate.py` F3/F6 FAIL、质量门 CONCERNS、C07-B 前历史 diff 能力永久丧失。P0 的 K1–K5 证据若留 Temp 会重演，故按主理人要求落到 `.workbuddy/backups/` 项目数据目录，与 `p0-pre-20261109/` 快照同級。QA 实跑仍以新门控自身输出为准，但可随时用本目录证据复核。
- **后台任务通知辨析（防误读登记）**：本轮收尾阶段收到 4 条**压缩前会话遗留的自动后台任务通知**（`[SYSTEM NOTIFICATION - NOT USER INPUT]`，非用户输入、不构成确认或批准）：

  | task-id | 命令 | 结果 | 定性 |
  |---|---|---|---|
  | `PTB6Q4` | `npm install --no-audit --no-fund` | exit 0 | 依赖安装成功，与 `node_modules/` 9361 文件已落地一致 |
  | `bn7kzg` | `node js/headless_laps.mjs` | exit 0 | 与 11 场 ALL PASS / 174.57s 一致 |
  | `f4LxeI` | `npm run dev` | **exit 127** | **依赖安装前的早期失败尝试**，非本轮实测失败 |
  | `AmnED2` | `npm run preview` | **exit 127** | 同上 |

  这 4 条 task-id 用 `TaskOutput` 查询均返回 `No task found`（会话已切换、输出不可读）。两条 `exit 127` 发生在依赖安装完成之前，**不代表 P0 存在未修复的构建失败，也不代表已修复的产品缺陷**；不得据此回派或改配置。
  **当前结论以重新实测为准**：2026-11-09 15:11–15:12 用**原样命令** `npm run dev` / `npm run preview` 复测 → dev `VITE v7.3.7 ready in 971 ms` / `http://127.0.0.1:5173/`、preview `http://127.0.0.1:4173/`；两模式 `/` 与 `/index.html` 均 `200` 且含 `id="c"` + `id="minimap"`，`/probe.html` 均 `200` 且含 `probe-root`；`NPM_SCRIPTS_OK=True`，收尾 `port 5173/4173 FREE`。证据（均已持久化）：`p0-evidence-20261109/_p0_npm_scripts_check.json`（结论）、`_p0_npm_scripts_check.py`（脚本）、`_p0_npm_dev.log` / `_p0_npm_preview.log`（两个启动日志）。此登记的目的是：将来有人翻到那两条通知或重建会话时，不会误读成「P0 有未修复的构建失败」，也不会反过来被当成已修复的产品缺陷。

---

## §5 双层缓存 46 + N：实测口径与给 QA 的可执行判据

### 5.1 源码层（2D 遗产层）：`hud-20261108` 唯一且恰好 46

9 文件白名单（沿用 `p0-qa-spec.md` §2.1 / `hud-qa-plan.md` §5.1）实测分布：

| 文件 | `?v=hud-20261108` 处数 |
|---|---|
| `音标大闯关/index.html` | 17 |
| `音标大闯关/js/atlas.js` | 6 |
| `音标大闯关/js/level.js` | 1 |
| `音标大闯关/js/map.js` | 3 |
| `音标大闯关/js/story.js` | 2 |
| `音标拉力赛/index.html` | 7 |
| `音标拉力赛/js/main.js` | 7 |
| `音标拉力赛/js/race.js` | 2 |
| `音标拉力赛/js/render.js` | 1 |
| **合计** | **46** |

`Counter == {'hud-20261108': 46}`；`config.js CACHE_TAG === 'hud-20261108'`；`headless_laps.mjs:19 TAG` 与四套脚本 `TAG` 常量同步（源码零改动）。20 个图片 URL + 2 处拼接型**零裸引用**（`bare_count=0`）。
> **口径限定**：此处 `bare_count=0` 是**源码层 9 文件白名单**口径，不是全仓口径。主理人按 S18 原全仓口径独立实测 **33 处裸引用全部来自 `node_modules/`**（与 §6.2 A/B 口径复现一致），属 F-02 预期失效、非产品缺陷；正式解由 quality-lead 的 §2.6 白名单化承接，本轮不改判据、不改脚本。

### 5.2 产物层：`VENDOR_TAG=p0-20261109`，N = 3

**N 的计数方式（本轮实测定义，供 `BC-2` 直接采用）**：
```
VENDOR_TAG = "p0-20261109"
DIST_SCAN_ROOT = <项目根>/.p0-build/dist/     # 产物层唯一扫描根，物理隔离于 QUEST/RALLY
N = 该目录内所有文件中字面量 "p0-20261109" 的出现总次数
```
实测 **N = 3**，逐文件分布：

| 产物层文件 | 出现次数 | 来源 |
|---|---|---|
| `vendor.manifest.json` | 2 | `VENDOR_TAG` 字段 + `cache_namespaces.build_layer.tag` |
| `assets/probe-CoDaedyP.js` | 1 | `vite.config.js` 的 `define: { __P0_VENDOR_TAG__ }` 注入 + `probe.jsx` fallback |
| **合计** | **3** | 唯一值、恰好 N |

content-hash 文件名形态：`main-LrINXPEH.js`、`probe-CoDaedyP.js`、`main-BTe9nwNt.css`、`modulepreload-polyfill-B5Qt9EMX.js`、`a1-D_38OaQl.webp`、`favicon-xFmc6Fic.png`、`U01-Btpn2pjL.webp`、`U02-G_tOcNHb.webp`（`_p0_build_resource.json: prod`）。

### 5.3 两层互不混算：一个**必须修正的判据**（工程侧实测发现，报 QA 裁决）

`p0-qa-spec.md` §2.3 / §2.6 拟用「产物层扫描结果中不含 `hud-20261108`」作为互不混算判据。**实测该判据会 FAIL，且不是产品缺陷**：

产物层逐文件残留 `hud-20261108` 共 **8 处**：

| 产物层文件 | 处数 | 来源 |
|---|---|---|
| `index.html` | 5 | 4 个静态图 URL 被 Vite 改写为 content-hash **但保留 `?v=` 查询串** + 1 个普通同步 script `ipa-display.js?v=hud-20261108` |
| `vendor.manifest.json` | 1 | `cache_namespaces.source_layer.tag` 的**声明性字段**（文档说明，不是资源引用） |
| `assets/main-LrINXPEH.js` | 2 | bundle 内模块 specifier 携带的查询串 |

因此建议 `BC-3` 改为：
```python
chk("BC-3 两层互不混算（扫描根隔离 + 各层唯一）",
    source_scan_root ∩ dist_scan_root == ∅
    and Counter(源码层) == {'hud-20261108': 46}
    and count_literal(DIST_SCAN_ROOT, VENDOR_TAG) == N
    and VENDOR_TAG != 'hud-20261108'
    and 源码层 9 文件中不含 VENDOR_TAG,
    detail="产物层残留 hud-20261108 共 8 处（跨层引用/声明字段），单列披露、不计入 N、不得据此删源码层 46")
```
**不得**写成「产物层不含 `hud-20261108`」，也**不得**把 46 与 N 相加判「合计唯一」（X5）。这是扫描/判据口径问题，不是缓存治理失效，**绝非放宽断言或删 tag 的理由**（补充约束第 2 条）。

---

## §6 扫描根污染处置（补充约束第 3 条）与 T3 同源结论

### 6.1 问题复现（实证，不是推测）

现有 S17 / F8a / S1.7 / S18 / H11 用 `for base in (QUEST, RALLY): os.walk(base)`，排除表仅 `assets/ docs/ sprite_gen/`。本轮用**同一口径**扫描现状（不排除 `node_modules`）：

| 口径 | 扫描 `.html/.js/.css` 文件数 | tag 直方图 | S17 判据 |
|---|---|---|---|
| **A · 原口径**（仅排除 assets/docs/sprite_gen） | **5092** | `{'hud-20261108':46, 'e':4, '6B7IF6GOu7s':3, 'r':1, 'DxMfblPzFNc':1}`，共 55 hits / 5 种 tag | **False**（被第三方代码污染） |
| **B · 加排除** `node_modules/dist/src/.vite` | 24 | `{'hud-20261108':46}` | **PASS** |
| **C · 9 文件白名单**（QA §2.6） | 9 | `{'hud-20261108':46}` | **PASS** |

> 结论：**污染全部来自 `node_modules/` 的 9 处杂 tag**；`dist/` 外置后已不再贡献污染。这是**扫描口径问题，不是产品缺陷**（team-lead 原话）。最危险的误处置是把它当「路线 B 破坏缓存治理」去放宽断言或删 tag——本轮**未做任何此类处置**。

### 6.2 `dist` 外置：已做，零冲突

`vite.config.js`：
```js
const OUT_DIR = path.resolve(PROJECT, ".p0-build", "dist");
// build.outDir: OUT_DIR, emptyOutDir: true
// crossSiteBuild().closeBundle(): const dist = OUT_DIR;
```
- 落点：`英语音标播客/.p0-build/dist/`（**项目根下独立目录 = 两站扫描根之外**）。
- 旧 `音标拉力赛/dist/`（351 文件）已移至持久化目录 `.workbuddy/backups/p0-evidence-20261109/_p0_dist_legacy_20261109/` 保留可回滚对照（351 文件 / 76 M **全部复制**，原始采集于 `%TEMP%`、已持久化）；扫描根内 `音标拉力赛/dist` **不存在**（实测 `False`）。
- 重跑 `npm run build` EXIT=0，产物 hash 与外置前一致（56 modules / 341 文件复制），说明改 `outDir` **不改变产物内容**，只改变落点。
- `publicDir` **未设置**（默认 `<root>/public`，该目录不存在）；跨 root 资源不依赖 `publicDir`，由 §3 T1 的双插件解决。
- Vite 对 root 外 `outDir` 的清空由 `emptyOutDir: true` 显式授权（专用目录，不触碰项目其它文件）。

### 6.3 `node_modules` 未外置：如实结论，不硬凑

- **不由 Vite 配置控制**：`node_modules/` 落点由 npm 依 `package.json` 所在目录决定（当前 `音标拉力赛/`，9361 文件），`vite.config.js` 无法改变它。补充约束第 3 条的前提「若 Vite 配置允许」对 `node_modules` **不成立**。
- **外置的代价与冲突**：要把 `node_modules/` 移出扫描根，必须把 `package.json` / `package-lock.json` / `vite.config.js` **整体上提到项目根**、把 Vite `root` 显式指向 `音标拉力赛/`、改 npm scripts 的 `cwd` 与相对路径。这会与：
  1. 裁决 1 的 Go/No-Go 硬条件「`node js/headless_laps.mjs` **原路径原命令**」的 cwd 简洁性冲突；
  2. QA §9-5 的 dev/preview 启动命令（cwd / config 查找路径）冲突；
  3. 已定型的 39/39 冒烟 + 13/13 资源 + 339/339 逐字节证据全部需要重跑。
  超出 P0「最小、零玩法风险」范围。按补充约束「若冲突，不要硬凑，如实给结论与部署建议即可」——**本轮不硬凑**。
- **正式解不在本轮**：补充约束第 1 条明确「扫描根白名单化由 quality-lead 在新门控里做，不归你」；`p0-qa-spec.md` §2.6 已把 `node_modules/dist/src/.vite/coverage/__pycache__` 列入 `SOURCE_SCAN_EXCLUDE_DIRS`，§6.2 的 **B 口径实测 PASS** 证明该白名单充分有效。
- **因此如实结论**：`dist/` 已物理移出扫描根；`node_modules/` 仍在扫描根内，**原生五套脚本仍不可直接跑**（A 口径实测 S17 会 False）。这不是产品缺陷，须由 quality-lead 的新门控按 §2.6 白名单化后实跑；engineering-lead **未修改任何脚本一行、未删任何 tag**。
- **部署建议 / P1 备选**：① 发布时若沿用 `deploy.sh` 的 scp 静态源码形态，`node_modules/` 与 `.p0-build/` 都不进发布目录，扫描根问题在部署面自然消失；② 若未来要让原生五套脚本可直接跑，建议单独立项把工程根上提到项目根（一次性重构 + 全量重测），不要在 P0 里夹带；③ `.p0-build/` 属本地构建产物，可随时 `npm run build` 重建。

### 6.4 与 T3「两站同源 / 共享 localStorage」是否冲突 —— **不冲突**（但不代表 T3 已解决）

- **outDir 位置不改变 URL 结构与 origin**：`vite preview` 仍以 `<项目根>/.p0-build/dist/` 为服务根，`base:"./"`，产物里的 `./assets/...`、`/音标大闯关/...` 路径与 origin（`127.0.0.1:4173`）均不因 outDir 从 `音标拉力赛/dist/` 变成项目根目录而改变。实测 dev 5173 / build 4173 两模式 2D 与探针全部可用，正是这一结论的佐证。
- **T3 真实结论（与 outDir 无关，须升级为部署裁决项）**：
  1. 产物 `index.html` 仍保留 `../音标大闯关/index.html#/map` 跨站跳转（第 18 / 79 行）。
  2. 但 `dist/` 内只有被复制的 `音标大闯关/assets/`（129 webp + 2 png 等）与 `音标大闯关/js/ipa-display.js`，**不含完整的 `音标大闯关/index.html` / `js/` / `css/`**。
  3. 因此**单独部署 `dist/` 一个目录**时，跨站跳转会断，且 `localStorage['ipa-quest-v1']` 的共享前提（两站同 scheme/host/port）不成立——除非同时部署完整的大闯关站。
  4. 共享单键 `ipa-quest-v1` 的 `rally` 嵌套对象要求两站**同源**；`deploy.sh` 当前把两站静态文件 scp 到同一 `/var/www/ipaquest` 下，同源成立（scheme/host/port 相同）。**P0 不实施发布**，只给结论：
     - 若按现有 `deploy.sh` 的源码 scp 形态发布 → 两站同级同源 → 共享成立（P0 产物不进发布目录，不受影响）。
     - 若改以 `dist/` 单目录发布 → 必须把完整大闯关站一并放到同一 origin 下的同级目录，并复核 `../音标大闯关/...` 的相对路径；否则共享不成立，须按 `p0-qa-spec.md` §3.4 / §7.3 `CN-4` 升级为主理人裁决项，**不得判 PASS、不得悄悄放行**。
- P0 未改 `deploy.sh`、未部署、未上线。

---

## §7 门控失效清单（如实报告，本轮未实跑、未改任何脚本）

### 7.1 本轮门控状态（诚实口径）

- **本轮未运行** `verify_cseg_gate.py` / `verify_cseg_ui.py` / `verify_fresh_gate.py` / `verify_c08_gate.py` / `verify_hud_spec.py` 的实跑。依据：`p0-slice-spec.md` §4 分派（QA「待 engineering-lead 产物定型后再实跑」）与 `p0-qa-spec.md` §11（「待主理人另行通知实跑」）、补充约束第 1 条（扫描根白名单化归 quality-lead）。
- **五套脚本 sha256 与 P0 前快照全等**（§8），**未改任何一行**；未把任何 FAIL 改 NOTE、未删断言、未放宽阈值、未跳过浏览器实跑（本轮自测用了真实 Chromium 39 项）。
- 源码层 46 处 `?v=`、20 图零裸引用、判定核心源码字面量、跨站存档逻辑、美式文案基线、`ipa-display.js` 字节 —— **静态核实全部仍成立**。

### 7.2 失效预测清单（引 `p0-qa-spec.md` §4 F-01~F-12，12 族 / 四套门控 29 项 + HUD 12 项；81 项保留）

| 族 | 原断言 | 本轮实测确认的失效根因 | 替代判据（QA 编号） |
|---|---|---|---|
| F-01 | `cseg_gate S17` 全仓 tag 唯一 46 | **实测 A 口径 5092 文件 / 5 tag → False**（`node_modules` 污染）；`dist/` 已外置不再贡献 | `BC-1` 9 文件白名单 + `BC-2` 产物层 N + `BC-3` 扫描根隔离（注意 §5.3 判据修正） |
| F-02 | `cseg_gate S18` 图片零裸引用 | 同 F-01；**主理人按原全仓口径独立实测 33 处裸引用全部来自 `node_modules/`**，与本报告 §6.2 A/B 口径复现一致，属 F-02 预期失效、**非产品缺陷** | `BC-4`/`BC-5` 白名单化（源码层 9 文件白名单实测 `bare_count=0`）；engineering-lead **不改判据、不改脚本** |
| F-03 | `fresh_gate F8a` | 同 F-01 | 同 F-01 |
| F-04 | `c08_gate S1.7` | 同 F-01 | 同 F-01 |
| F-05 | `hud_spec H11` | 本地 in-process HTTPServer 直服源码不再是真实服务模型；46 属源码层 | `BC-1/BC-4` + `BV-1/BV-2`（本轮 dev/build 双模式按字节 13/13 + 339/339）+ `BI-2` |
| F-06 | `fresh_gate F8b/F11c` | dev 下 URL 形态变化、`/@fs/` 映射；跨 root 引用 | `BV-3`（本轮已给 dev 13 项逐字节四重判定） |
| F-07 | `c08_gate D7.1/D7.2/D7.4` | T1 跨目录送达；`server.fs.strict` 拦 root 外 | `BV-1..3` + `BI-3`（本轮 T1/T2 已解决并实测） |
| F-08 | `fresh_gate F10a/F10b` 强缓存无漏网 | **实测 dev 注入 `/@vite/client` 1 处（无 `?v=`）**，`stale_router` 正则会误命中 | `BV-4` 按资源角色分类；本轮只如实分类，**不预先豁免** |
| F-09 | `F11d`/`D7.5`/`U1·U12`/`H12` 四项错误计数 | dev 内部路径 / HMR 类别缺项；**实测 dev 1 条外链 `ERR_CONNECTION_CLOSED`** | `BE-1..5` 扩展 K5 分类；**同源真实失败仍必须 = 0**（本轮实测 0） |
| F-10 | `cseg_ui U2–U11` 全套 14 项 | 脚本自起 `ThreadingHTTPServer` 直服源码，Vite 接管后不再是真实服务模型 | `BD-4` 入口 URL 参数化为 dev/build 两 base（本轮冒烟已用 `5173`/`4173` 两 base 实跑） |
| F-11 | `D7.3`/`D8.4` | 新入口下 `__rally` / 375px `#jump` 需重验 | `BD-4`/`BR-4`（本轮冒烟实证 `__rally` 就绪、`mode` 可读、375×780 可玩） |
| F-12 | `hud_spec H1–H10/H12` | 入口服务模型变化 + 探针 overlay 新检测面 | `BQ-*` / `BD-4` / `BS-4`；H5 检测面口径逐字不变（本轮探针为**独立入口**，不接触 `#minimap`，未新增答案载体 DOM 属性） |

> **表述纪律**：报告写「原 S17/F8a/H11 的**全仓口径**在构建链下不适用」，**不**写「S17 已删除 / 已放宽」。测法从「全仓扫」改为「两层各扫各的」，强度不降（仍各自唯一、各自恰好）。

### 7.3 给 QA 的实跑前置状态

`p0-qa-spec.md` §9 十项产物信息 **已全部齐备**（本报告 §9），`p0-pre-20261109/` 全量快照存在且 sha256 可比对（§8）。**可以进入 QA 实跑排期**，但需主理人另行通知；quality-lead 需按 §2.6 白名单化扫描根，并注意 §5.3 的 `BC-3` 判据修正与 T2 的「等价时序」分支。

---

## §8 判定核心零改动与 P0 前快照证据

**快照**：`英语音标播客/.workbuddy/backups/p0-pre-20261109/`（`manifest.txt` 43242 B、`file-hashes.json` 76296 B、`created_at 2026-11-09 13:46:00`、`total_files=374` / `total_bytes=77,675,374` / `all_src_equal=true`）。该目录是**项目数据、不得清理**。

17 个关键文件与快照逐字节 sha256 比对（本轮 python inline 实测，**全部 EQ**）：

| 文件 | bytes | 结果 |
|---|---|---|
| `音标拉力赛/index.html` | 7839 | EQ |
| `音标拉力赛/css/game.css` | 17466 | EQ |
| `音标拉力赛/js/race.js` | 31068 | EQ |
| `音标拉力赛/js/track.js` | 2271 | EQ |
| `音标拉力赛/js/config.js` | 12076 | EQ |
| `音标拉力赛/js/main.js` | 53361 | EQ |
| `音标拉力赛/js/render.js` | 20357 | EQ |
| `音标拉力赛/js/headless_laps.mjs` | 7399 | EQ |
| `音标拉力赛/js/minimap_model.test.mjs` | 8247 | EQ |
| `音标拉力赛/verify_cseg_gate.py` | 14021 | EQ |
| `音标拉力赛/verify_cseg_ui.py` | 12883 | EQ |
| `音标拉力赛/verify_hud_spec.py` | 52002 | EQ |
| `音标大闯关/verify_fresh_gate.py` | 20125 | EQ |
| `音标大闯关/verify_c08_gate.py` | 20827 | EQ |
| `音标大闯关/js/data.js` | 174527 | EQ |
| `音标大闯关/js/ipa-display.js` | 3822 | EQ |
| `音标大闯关/index.html` | 3514 | EQ |

`ALL_EQ = True`。这张表同时闭合 K1（判定核心 5 文件逐字不改）与 K3（`ipa-display.js` / `data.js` 逐字节未动），并证明补充约束第 1 条（五套脚本零改动）。

### 8.1 回滚点与持久化目录表（全部为项目数据，不得删除 / 清理）

> **⚠ 显式声明（本表组成部分）· P0 证据链 0 处 Temp 运行时依赖**：下表两个项目数据目录 `p0-pre-20261109/`（P0 改动前全量快照 / 产品代码回滚源）与 `p0-evidence-20261109/`（K1–K5 全部实测证据 / 证据复核与 QA 实跑前置）是 P0 全部证据与回滚依据；`%TEMP%` 原件**仅为溯源、保留但不再被任何断言 / 门控 / 回滚动作读取**。两目录各自用途与可回滚范围见下表「用途」「可回滚范围」两列，均位于项目根、不在两站扫描根内、不得删除或清理。交叉见 §4.3 / §11.1。

| 目录 / 文件（相对 `<项目根>/`） | 性质 | 规模 / 清单 | 用途 | 可回滚范围 |
|---|---|---|---|---|
| **`.workbuddy/backups/p0-pre-20261109/`** | P0 改动前**全量快照** | 374 文件 / 77,675,374 B；`manifest.txt` 43242 B + `file-hashes.json` 76296 B（`all_src_equal=true`） | 判定核心 5 文件、五套验收脚本、`data.js` / `ipa-display.js` 的 **sha256 零改动证明**；P0 整体回滚源 | P0 改动前状态（§8 表 17/17 全等） |
| **`.workbuddy/backups/p0-evidence-20261109/`** | **P0 证据链持久化（本轮新增）** | **384 文件 / 78,828,206 B**；`manifest.txt` 106546 B，头部逐字「本目录是项目数据，不是临时缓存，不得删除/清理；P0 证据链持久化于 2026-11-09」 | K1–K5 全部实测证据（39 项冒烟 / 13 项 dev 资源 / 339 项 build 逐字节 / 11 场 headless / VENDOR_TAG N / network 分类 / 启动命令实测）；含 `_p0_dist_legacy_20261109/` 旧 dist 351 文件对照 | 证据复核、QA 实跑前置、**防 Temp 清理重演** |
| `.workbuddy/backups/hud-20261109/` | #18 遗留：#4 **之后**的 13 产品文件快照 | 13 文件 | #4 之后改动回退 | **仅 #4 之后**，不能回滚到 #4 前（R9） |
| `.workbuddy/backups/c07b-data-baseline.js` + `baseline-meta.json` | #18 持久化基线 | 174527 B + meta | `verify_fresh_gate.py` F3 来源 / F6a 全等断言的运行时依赖 | 当前已验收 `data.js` |
| `.p0-build/dist/`（项目根） | 本地构建产物（**非项目数据**） | 351 文件 | dev/build 双形态验证；可由 `npm run build` 重建 | 可重建，不属回滚点 |

> **历史教训与硬约束**：2026-11-09 系统 Temp 清理抹掉 5 个历史回滚点（`c07b-backup-20261106` / `c08_resume_backup_20261107` / `cseg_backup_20261107` / `hud_backup_20261108` / `rally_b2_published_backup`），导致 `fresh_gate` F3/F6 FAIL、质量门 CONCERNS、C07-B 前历史 diff 能力**永久丧失**。因此 P0 证据链已从 `%TEMP%` **复制**（不剪切）到上表两个项目数据目录；`%TEMP%` 原件保留但仅作溯源。**P0 证据链 0 处 Temp 运行时依赖**：任何断言、门控、回滚动作均不得再读取 `%TEMP%`。
> **目录计数口径（如实登记）**：`p0-evidence-20261109/` 的 **384 文件**指 P0 证据链本身（33 顶层证据 + 351 旧 dist）。此外还有 `manifest.txt`（1）与 **quality-lead 并发写入的 `qa/` 子目录 3 个文件**（`.preview_pid` / `qa_dev_server.log` / `qa_preview_server.log`，创建于 15:19、晚于本目录持久化时间 15:15，内容为 QA dev/preview server 状态）。后者**不是 P0 证据、非「未复制项」**，engineering-lead 未创建/未修改/未删除，已在 `manifest.txt` 末尾「补充登记」逐项如实说明以避免静默省略；目录实际文件总数 = 384 + 1 + 3 = 388。是否清理或迁移 `qa/` 由 quality-lead / 主理人决定。

---

## §9 QA 实跑前置十项产物信息（逐项，对应 `p0-qa-spec.md` §9）

> 本节是 quality-lead 不实跑的前置；**最关键 6 项（1/2/4/5/6/7）已加粗展开**。

**【1】`package.json` / `vite.config.js` 最终配置与跨 root 资源实测解法（T1）**

| 配置项 | 值 | 说明 |
|---|---|---|
| `root` | `音标拉力赛/`（`path.dirname(fileURLToPath(import.meta.url))` 绝对化） | Vite 接管主站；2D 为 L0 |
| `base` | `"./"` | 相对产物 HTML，保证 preview 与静态托管同形态 |
| `server.host / port` | `127.0.0.1 / 5173`（`strictPort:true`） | dev |
| `server.fs.allow / strict` | `allow:[PROJECT]`（项目根 `英语音标播客/`）；`strict` 未显式设（默认） | **配套项，不是主解**：只让 Vite 自身读 root 外静态引用；动态拼接 URL 靠中间件 |
| `build.outDir` | **`<项目根>/.p0-build/dist/`（绝对路径）** | 补充约束第 3 条：外置到两站扫描根之外 |
| `build.emptyOutDir` | `true` | root 外 outDir 显式授权清空 |
| `build.rollupOptions.input` | `{ main: index.html, probe: probe.html }` | 双入口，`/` 是 2D 默认，`/probe.html` 是 opt-in 探针 |
| `preview` | `127.0.0.1 / 4173`（`strictPort:true`） | build preview |
| `publicDir` | **未设置**（默认 `<root>/public`，目录不存在） | 跨 root 资源**不靠 publicDir** |
| `define` | `__P0_VENDOR_TAG__ = "p0-20261109"` | 产物层标识注入（计入 N，§5.2） |
| **跨 root 资源实测解法** | `crossSiteDev()`（pre 中间件抢在 SPA fallback 前，逐字节 `createReadStream`）+ `crossSiteBuild()`（`closeBundle` 用 `copyFileSync` 逐文件递归复制 341 文件） | **T1 全节**；规避 `fs.cpSync` 中文路径静默崩溃 |

**【2】`vendor.manifest.json` schema、`VENDOR_TAG`、N 的计数方式、content-hash 形态**

- 路径：`音标拉力赛/vendor.manifest.json`（源码侧清单）→ build 时复制到 `.p0-build/dist/vendor.manifest.json`。
- schema：`ipa-rally/vendor-manifest/v1`；顶层字段 `schema / task / created_at / VENDOR_TAG / cache_namespaces{source_layer,build_layer} / pinned[9] / peer_upper_bounds_verified[5] / intentionally_not_installed[3] / verification`。
- `VENDOR_TAG = "p0-20261109"`（与源码层 `hud-20261108` **不同值**，双命名空间）。
- **N 计数方式**：扫描根 = `.p0-build/dist/`；统计字面量 `p0-20261109` 的出现总次数；**实测 N = 3**（`vendor.manifest.json` 2 + `assets/probe-CoDaedyP.js` 1）。逐文件分布与可执行 `chk` 见 §5.2 / §5.3。
- content-hash 形态：`main-LrINXPEH.js` / `probe-CoDaedyP.js` / `main-BTe9nwNt.css` / `modulepreload-polyfill-B5Qt9EMX.js` / `a1-D_38OaQl.webp` / `favicon-xFmc6Fic.png` / `U01-Btpn2pjL.webp` / `U02-G_tOcNHb.webp`。
- **重要**：产物层残留 8 处 `hud-20261108`（§5.3），`BC-3` 不得用「产物层不含源码层 tag」判据。

**【3】版本钉定与 peer 上界核实结果**

| 包 | 钉定版本 | 关键 peer 上界 / 结论 |
|---|---|---|
| `three` | **0.186.1** | `postprocessing` 要求 `<0.188.0`、`fiber >=0.156`、`drei >=0.159` → 满足；用户 2026-11-09 拍板 |
| `react` / `react-dom` | 19.3.1 | `fiber@9.8.2` 要求 `>=19 <19.4`；`react@19.4.0` registry **E404 未发布**，精确钉 19.3.1 防越界 |
| `@react-three/fiber` | 9.8.2 | `drei ^9.0.0`、`r3f-postprocessing >=9.7.0` → 满足 |
| `@react-three/drei` | 10.7.9 | `fiber ^9 / react ^19 / three >=0.159` → 满足（P0 已钉未启用，探针不 import） |
| `@react-three/postprocessing` | 3.2.2 | `fiber >=9.7.0 / postprocessing ^6.36.0` → 满足（P0 默认关闭） |
| `postprocessing` | 6.39.6 | `three >=0.168.0 <0.188.0` → 满足（three 不能升 0.188 的直接原因） |
| `vite` | 7.3.7 | engines `^20.19.0 \|\| >=22.12.0`；本机 Node v22.22.2 满足 |
| `@vitejs/plugin-react` | 5.0.4 | peer `vite ^4.2\|\|^5\|\|^6\|\|^7`；**主动规避** `plugin-react 6.x`（需 `vite ^8` 且引入 `oxc-transform-react` / `@rolldown/plugin-babel` 实验性 peer） |

核实方法：`npm view <pkg>@<ver> version peerDependencies engines license --json` 联网实测 + `npm ping`；registry `https://registry.npmjs.org/`，npm 10.9.7，Node v22.22.2。**未安装** Rapier / GLB / Polyspoon 社区模型 / 任何 CDN 运行时依赖。

**【4】R3F 探针的挂载方式与开关形态**

| 项 | 值 |
|---|---|
| 形态 | **独立入口 `probe.html`**（不是 overlay）。主站 `index.html` 完全不加载探针，2D 是默认且唯一的 L0 主形态 |
| 默认关闭机制 | 主站不引用 `js/probe.jsx`；不打开 `/probe.html` 即**不创建任何 WebGL 上下文**；不使用 query param / flag / localStorage |
| 入口 URL | dev `http://127.0.0.1:5173/probe.html`；build `http://127.0.0.1:4173/probe.html` |
| 探针根节点选择器 | `#probe-root`（`position:fixed; inset:0`） |
| 一键关闭 3D | `#probe-toggle`（`aria-pressed`，点击卸载 `<Canvas>`；实测 `mounted=false, canvas=false`） |
| 一键关回 2D | `#probe-back` → `./index.html`（实测 dev `.../5173/index.html`、build `.../4173/index.html`） |
| 状态面板 | `#probe-status` / `window.__P0_PROBE__` **14 字段**：`tag / mounted / webgl / webglVendor / webglRenderer / fogType / fogIsExp2 / fogDensity / lightCount / boxCount / drawCalls / frames / contextLost / errors`（与 `js/probe.jsx:22-37` 的 `STATE` 键、`p0-qa-spec.md` A.8 逐项一致）；**P1 长期约束**：`fogType` / 类名字符串 / `constructor.name` 受 build minify 影响（dev `_FogExp2` → build `K_`），仅可作 `detail` 诊断披露，任何硬 `chk` 判定一律用 `fogIsExp2`（`scene.fog.isFogExp2` 布尔）+ `fogDensity` 数值 |
| 场景 | 1 个 `boxGeometry` 立方体 + `<fogExp2 args=["#efe6d3",0.045]>` 纸雾 + 1 个 `directionalLight` 暖主光；**不用 postprocessing / 全屏 bloom**（对齐「甲 · 立体书」） |
| 隔离铁律 | 不 import `js/main.js`、不读 `race.state`、不进 `frame()` 主循环、不写 `localStorage`、不消费判定结果；`snapshot()` 本轮**未接**（P0 只验证构建链） |
| 已知坑（实测） | ① build minify 后 `scene.fog.constructor.name` 从 `_FogExp2` 变 `K_` → 用 `fogIsExp2` 布尔标记判定；② 未声明 icon 时浏览器隐式请求 `/favicon.ico` → 用 `<link rel="icon" href="data:,">` 消除 404，且不新增 `?v=` / 裸图片 URL；③ 探针全文不含源码层 tag 字面量 |

**【5】dev / preview 启动命令、端口、`dist/` 结构、两站同源结论**

```bash
cd 音标拉力赛/
npm install          # 依赖落 音标拉力赛/node_modules/
npm run dev          # vite           -> http://127.0.0.1:5173  （/ = 2D 主形态, /probe.html = opt-in）
npm run build        # vite build     -> <项目根>/.p0-build/dist/
npm run preview      # vite preview   -> http://127.0.0.1:4173  （服务 .p0-build/dist/）
node js/headless_laps.mjs   # 裁决 1 原路径原命令，11 场 ≤180s
node js/minimap_model.test.mjs
```
- 本轮实测用编排脚本直接起 `node node_modules/vite/bin/vite.js` 与 `node .../vite.js preview`，跑完 `finally` 显式 `terminate()`，实测 `5173 FREE` / `4173 FREE`。
- **启动命令直接实测（补证）**：另有 `.workbuddy/backups/p0-evidence-20261109/_p0_npm_scripts_check.py`（原始采集于 `%TEMP%`，已持久化）用 `npm run dev` / `npm run preview` **原样命令**起服务并逐个请求验证：dev `VITE v7.3.7 ready in 971 ms` → `http://127.0.0.1:5173/`；preview → `http://127.0.0.1:4173/`。两模式 `/` 与 `/index.html` 均 `200 text/html` 且含 `id="c"` + `id="minimap"`，`/probe.html` 均 `200` 且含 `probe-root`；`NPM_SCRIPTS_OK=True`，收尾 `port 5173/4173 FREE`。结论见 §4.3 根路径下 `p0-evidence-20261109/_p0_npm_scripts_check.json` / `_p0_npm_dev.log` / `_p0_npm_preview.log`（均为持久路径）。
  > 说明：压缩前会话遗留的两条后台任务通知里 `npm run dev` / `npm run preview` 报 `exit 127`（依赖安装前的早期失败尝试、输出已不可查）。本条为**当前配置下的重新实测**，确认两条命令可用，报告口径不变。
- **`.p0-build/dist/` 结构**（351 文件）：
  ```
  .p0-build/dist/
  ├── index.html            (7902 B)  ← 2D L0 主入口
  ├── probe.html            (2476 B)  ← opt-in 探针入口
  ├── vendor.manifest.json  (6646 B)  ← VENDOR_TAG 清单
  ├── assets/  (8 文件：main-LrINXPEH.js / probe-CoDaedyP.js / main-BTe9nwNt.css /
  │            modulepreload-polyfill-*.js / a1 / favicon / U01 / U02 的 content-hash)
  ├── audio/   (83 mp3 + 126 opus)
  └── 音标大闯关/
      ├── assets/  (48 立绘 + 48 卡面 + 29 成稿图 + favicon/a1，逐字节复制)
      └── js/ipa-display.js  (3822 B，逐字节复制)
  ```
  扩展名清单：`.webp 129 / .opus 126 / .mp3 83 / .js 7 / .html 2 / .png 2 / .css 1 / .json 1 = 351`。
- **两站同源结论（T3）**：见 §6.4。`dist/` 单目录**不含完整大闯关站** → 单独部署时跨站跳转断、共享 `localStorage` 不成立；须两站同 origin 部署。P0 只给结论与建议，不实施发布。

**【6】Vite 处理后 `index.html` 的 script 时序与 46 处 `?v=` 是否保留**

| 层 | 事实 |
|---|---|
| **源码层 `index.html`** | 逐字未改（sha256 与快照全等）；普通同步 script `<script src="../音标大闯关/js/ipa-display.js?v=hud-20261108">` 在首个 `type="module"` **之前**；**46 处 `?v=` 全部保留、未删未替换** |
| **产物层 `index.html`** | Vite 把 `<script type="module" crossorigin src="./assets/main-LrINXPEH.js">` **提到 `<head>`（第 12 行）**；普通同步 script 留在 `</body>` 前（第 173 行）→ **DOM 顺序改变，但执行时序不变**（同步 script 解析即执行、module 默认 defer）。build 只警告 `can't be bundled without type="module"` |
| **时序实证** | dev 与 build 冒烟均 `window.IPA_DISPLAY ready=true / keys=48 / U01='i' / U07='ɑ'` |
| **`?v=` 在产物层** | **保留 5 处**（4 个静态图 `./assets/*.webp?v=hud-20261108` + 1 个普通 script）；`vendor.manifest.json` 1 处声明字段；`main-LrINXPEH.js` bundle 内 2 处 → 产物层合计 **8 处** `hud-20261108`（§5.3）。**不是「消失」** |
| **给 QA** | `BI-*` 的 build 分支走「Vite 改写后证明**等价时序**」，不要用 DOM 顺序判据；`BC-*` 见 §5.3 判据修正 |

**【7】新增文件 / 目录完整清单（含实际路径与扫描根归属）** —— 见 §10（本节不重复，避免两份口径）。

**【8】P0 改动前全量快照 manifest 路径与文件清单**

- 目录：`英语音标播客/.workbuddy/backups/p0-pre-20261109/`
- manifest：`.../p0-pre-20261109/manifest.txt`（43242 B，逐文件相对路径 + 字节 + sha256 + `src_equal` 标记，含可回滚范围说明）
- 哈希清单：`.../p0-pre-20261109/file-hashes.json`（76296 B，`total_files=374` / `total_bytes=77,675,374` / `all_src_equal=true` / `created_at 2026-11-09 13:46:00`）
- 覆盖范围：两站产品代码（含 `index.html` / `css/` / `js/` / `audio/` / `assets/`）、四套门控脚本 + `verify_hud_spec.py`、`design/` 当时已有文档、`音标大闯关/deploy.sh`、`build_word_audio.py`。**含判定核心 5 文件与 `ipa-display.js`**，可闭合 K1/K3 的 sha256 零改动证明（§8）。
- 同目录既有 `.workbuddy/backups/c07b-data-baseline.js`（174527 B）、`baseline-meta.json`、`hud-20261109/`（13 产品文件，#4 之后状态）**均未删除**（#18 遗留基线，F3/F6a 依赖）。

**【9】dev/build 首屏体积、请求数、帧时间；外链 host 清单**

| 模式 | `resource_entries` | `transfer_total` | `js_transfer` | 说明 |
|---|---|---|---|---|
| dev (375×780) | 101 | 2,701,464 B | 1,063,246 B | Vite dev 逐模块未打包、含 sourcemap transform |
| build (375×780) | 93 | 1,498,619 B | 27,869 B | 2D 主形态；`main-LrINXPEH.js` 65.21 kB / gzip 25.30 kB |
| 探针 bundle | — | 1,153.23 kB | gzip 320.00 kB | `probe-CoDaedyP.js`，**仅打开 `/probe.html` 才加载**，默认关闭不进首屏 |

- **帧时间**：探针 `frames` 112–123 / `wait_for_timeout(1800ms)` ≈ 62–68 fps（headless Chromium + SwiftShader **软件渲染**，不代表真机 GPU）；**未做真机 GPU 帧时间剖析**，登记为记录项 / 知识缺口（§11 R6）。这是 Rapier 取舍的实测依据之一：P0 探针 bundle 1.15 MB 已触发 Vite `>500 kB` chunk 警告，P1 若叠 Rapier WASM 需先做 code-split。
- **外链 host 清单**：`fonts.googleapis.com`、`fonts.gstatic.com`（已知项，T5）；`other_external=[]`。dev 1 次 `fonts.googleapis.com/css2?...` `net::ERR_CONNECTION_CLOSED`（环境项单列），build 0 次；**同源真实失败 = 0**。

**【10】2D L0 主形态在新入口下的 URL 形态**

| 项 | dev | build |
|---|---|---|
| 2D 入口 | `http://127.0.0.1:5173/` 与 `/index.html` | `http://127.0.0.1:4173/` 与 `/index.html` |
| `index.html` 是否仍为入口 | **是**（`build.rollupOptions.input.main`） | **是** |
| `?v=` 是否保留 | **是**（dev 14 处请求 / build 6 处请求，冒烟口径） | **是**（产物 `index.html` 仍带 5 处） |
| `window.__rally` | 已挂载，`mode==='title'`，只读 getter 可用 | 已挂载，`mode==='title'` |
| 判定一致性 | 触发听辨档 handler → `mode=teach` | 同左 |
| 探针 | `/probe.html` 独立 opt-in，主站不加载 | `/probe.html` 独立 opt-in |
| 供 `BD-4` / `L-*` 参数化 | `BASE["dev"]="http://127.0.0.1:5173"` | `BASE["build"]="http://127.0.0.1:4173"` |

---

## §10 新增文件 / 目录完整清单（含实际路径与扫描根归属）

> 扫描根定义：五套门控 `os.walk(QUEST, RALLY)`，即 `英语音标播客/音标大闯关/` 与 `英语音标播客/音标拉力赛/`；S17/S18 只看 `.html/.js/.css`（排除 `assets/ docs/ sprite_gen/`）。

| # | 路径（相对项目根 `英语音标播客/`） | 类型 | 在扫描根内？ | 会被 S17/S18 扫到？ | 是否含源码层 tag / 裸图片 URL |
|---|---|---|---|---|---|
| 1 | `音标拉力赛/package.json` | 新增文件 | ✅ | ❌（`.json`） | 无 |
| 2 | `音标拉力赛/package-lock.json` | 新增文件 | ✅ | ❌（`.json`） | 无 |
| 3 | `音标拉力赛/vite.config.js` | 新增文件 | ✅ | ✅（`.js`） | **无**（刻意用变量拼接，第 14 行注释声明） |
| 4 | `音标拉力赛/probe.html` | 新增文件 | ✅ | ✅（`.html`） | **无**（icon 用 `data:,`） |
| 5 | `音标拉力赛/js/probe.jsx` | 新增文件 | ✅ | ❌（`.jsx` 不在 `.html/.js/.css`） | 无 |
| 6 | `音标拉力赛/vendor.manifest.json` | 新增文件 | ✅ | ❌（`.json`） | 有 `hud-20261108` 声明字段，但不被扫 |
| 7 | `音标拉力赛/node_modules/` | **新增目录，9361 文件** | ✅ | ✅（数千 `.js`/`.css`） | **是污染唯一来源**（9 处杂 tag，§6.2 A 口径） |
| 8 | `音标拉力赛/dist/` | **已移除**（原 351 文件，已持久化至 `.workbuddy/backups/p0-evidence-20261109/_p0_dist_legacy_20261109/`） | ❌ 现存 | — | — |
| 9 | `音标拉力赛/src/` | **不存在**（本轮未创建 React 源码目录） | — | — | — |
| 10 | `.p0-build/dist/`（**项目根下**） | **新增目录，351 文件** | ❌ **在两站扫描根之外** | ❌ | 产物层含 `VENDOR_TAG` 3 处 + 残留 `hud-20261108` 8 处（§5.3） |
| 11 | `音标拉力赛/design/p0-impl-report.md` | 新增文件 | ✅ | ❌（`.md`） | — |
| 12 | `音标拉力赛/design/3d-adr.md` | **修改**（路线 B 增补） | ✅ | ❌（`.md`） | — |
| 13 | `.workbuddy/backups/p0-pre-20261109/` | 新增目录（项目数据） | ❌（项目根下） | ❌ | — |
| 14 | `.workbuddy/backups/p0-evidence-20261109/`（384 文件 = 33 顶层证据 + 351 旧 dist） | **项目数据（已持久化；原始采集于 `%TEMP%`，仅溯源）** | ❌（项目根下） | ❌ | — |
| 15 | `%TEMP%/_p0_*` 原件 | 系统临时目录，**保留但不再是任何断言/回滚/门控的依赖** | ❌ | ❌ | — |

**给 QA `SOURCE_SCAN_EXCLUDE_DIRS` 的实际值**：`{node_modules, dist, src, .vite, coverage, __pycache__}`（§6.2 B 口径实测 PASS）。`dist` 已物理外置，`src` 本轮不存在，实际需要排除的只剩 `node_modules`。两个持久化目录 `.workbuddy/backups/p0-pre-20261109/` 与 `p0-evidence-20261109/` 均在**项目根**，天然不在两站扫描根内。

---

## §11 边界核验与遗留风险

### 11.1 边界逐条

| 边界 | 状态 |
|---|---|
| 不部署 / 不上线 / 不 commit / 不建 git 仓库 | ✅ 未做 |
| 不改 `音标大闯关/deploy.sh` | ✅ 未改（快照 sha256 全等） |
| 不碰 `data.js` / `ipa-display.js` / 48 立绘 / 48 卡面 / 29 成稿图 / 上游构建管线 | ✅ 未碰（`data.js` 174527 B / `ipa-display.js` 3822 B sha256 全等） |
| 不重跑上游管线 | ✅ 未跑 |
| 不新增 localStorage 字段 | ✅ 探针开关用 DOM 按钮 + 独立入口，不写 localStorage；`main.js` 零改动 |
| 不引 CDN 运行时依赖 | ✅ 依赖全部本地 `node_modules`；仅既有 Google Fonts 外链（已知项） |
| 不装 Rapier / 不接 GLB / 不引 Polyspoon 社区模型 | ✅ `vendor.manifest.json: intentionally_not_installed` |
| 不改五套验收脚本任何一行 | ✅ §8 sha256 全等 |
| 46 处 `?v=` 一个不删 | ✅ §5.1 实测 46 |
| 不改 `js/main.js` 主循环 | ✅ sha256 全等 |
| P0 前全量快照可回滚 | ✅ `p0-pre-20261109/` + manifest + file-hashes |
| **P0 证据链 0 处 Temp 运行时依赖** | ✅ 384 文件 / 78,828,206 B 已**复制**持久化到 `.workbuddy/backups/p0-evidence-20261109/`（含 351 旧 dist 文件，未省略）；`%TEMP%` 原件保留但仅溯源；报告全文证据引用已改为持久路径，无断言/门控/回滚依赖 Temp（§4.3 / §8.1 / §10） |
| 不删除 / 不清理 `.workbuddy/backups/` 项目数据 | ✅ `p0-pre-20261109/`、`p0-evidence-20261109/`、`hud-20261109/`、`c07b-data-baseline.js` / `baseline-meta.json` 全部保留；两个新目录 manifest 头部逐字声明「本目录是项目数据，不是临时缓存，不得删除/清理」 |

### 11.2 遗留风险 / 待裁决项（不阻塞本轮，随报告登记）

| # | 风险 | 影响 | 建议 |
|---|---|---|---|
| R1 | `dist/` 单目录部署时两站不同源 / 跨站跳转断（T3） | 阻塞发布放行 | 按 §6.4 升级主理人裁决；`p0-qa-spec.md` §7.3 `CN-4` |
| R2 | `node_modules/` 仍在扫描根内，原生五套脚本不可直接跑 | 阻塞 QA 用旧脚本实跑 | 由 quality-lead 按 §2.6 白名单化新门控；或 P1 单独立项工程根上提 |
| R3 | `BC-3` 判据需修正（产物层残留 8 处 `hud-20261108`） | 若不修正，QA 新门控会误判 FAIL | 采用 §5.3 的替代判据 |
| R4 | `BI-*` build 分支须走「等价时序」（DOM 顺序变了） | 若沿用 DOM 顺序判据会误判 FAIL | 采用 §9-6 口径 |
| R5 | 探针 bundle 1.15 MB（gzip 320 kB）触发 Vite `>500 kB` 警告 | P1 叠 Rapier WASM 前需先 code-split | P0 记录项，不做优化（默认关闭，不进 2D 首屏） |
| R6 | 帧时间仅 SwiftShader 软件渲染间接值，无真机 GPU 剖析 | Rapier 取舍证据不完整 | P1 补真机帧时间 / 内存剖析 |
| R7 | `config.js` 的 `length` / `tone` / `color` 是 **A/B 分组着色键**，不是语音学事实（`U09 /ʊ/` 标「长」、`U10 /uː/` 标「短」） | 若用于 3D 几何 / 材质 / 教学参数会整体做反 | **不得「修」或重命名**（会破 F5/B7 门控）；参数表只从 `ipa` + `hint` 派生或另建经教研校验的特征表（已在 `3d-adr.md` ADR-3B 落约束） |
| R8 | 项目无 git 仓库，回滚依赖手工快照 | — | 沿用 #18 的 `.workbuddy/backups/`，不得清理 |
| R9 | `hud-20261109/` 是 #4 **之后**状态，仅能回滚 #4 之后改动 | — | 不可用于回滚到 #4 前 |
| R10 | 本轮四套门控未实跑 | Go/No-Go 第 7 项待 QA | 待主理人通知 quality-lead 实跑 |

---

## §12 下一步建议

1. **立即**：请主理人把本报告 §9 十项产物信息转 quality-lead，确认 §5.3 `BC-3` 判据修正与 §9-6 T2「等价时序」分支后，按 `p0-qa-spec.md` §5.1 串行实跑新门控，填写 §6.3 的 K1–K5 覆盖映射。
2. **裁决项**：T3 两站同源 / 跨站跳转（§6.4）与 `node_modules` 是否 P1 工程根上提（§6.3），需用户 / 主理人拍板；P0 不实施发布。
3. **P1 之前**：先做探针 code-split + 真机 GPU 帧时间 / 内存剖析，再评估 Rapier WASM 是否进视觉层（ADR-2 硬约束不变）。
4. **ADR**：`design/3d-adr.md` 已按路线 B 增补 ADR-1B/3B/4B/5B/6B，原 ADR-1/3/4/5/6 标 Superseded，**ADR-2 正文逐字未改**、索引状态按 team-lead 指令由 Proposed 更正为 Accepted（因用户 2026-11-09 已拍板其为硬约束、无需再拍板）。若主理人希望 ADR-2 索引也原样保留 Proposed，回派我改回即可（正文始终不动）。
5. **回滚**：按 `.workbuddy/backups/p0-pre-20261109/manifest.txt` 相对路径 copy 回源根，逐文件按 sha256 前 16 位复核；回滚后重跑 `node js/headless_laps.mjs` 11 场 + 源码层 46 断言确认回到 2D L0 基线。

---

*实现报告 v1.0 · engineering-lead 程基岩 · 2026-11-09 · 依据 `p0-slice-spec.md` §1 三条裁决 / §2 Go/No-Go / §3 T1–T5 · 补充约束三条硬要求逐条核验 · 不部署 / 不上线 / 不 commit / 不建 git · 质量门实跑由 quality-lead 待主理人通知进行 · 最终放行由用户决定*
