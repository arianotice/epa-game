# P0 切片规格 · 路线 B（Vite + React + R3F）整站接管

> **文档性质**：team-lead 综合用户四项拍板后写下的**实施规格**，供 engineering-lead（实现）与 quality-lead（门控重定义）共同执行。**不是已生效的产品代码变更**。
> **日期**：2026-11-09 · **上游**：`3d-tech-feasibility.md` §8 P0、`3d-adr.md`、`stage-delivery-2026-11-09.md` §5。
> **边界**：本地工程改造，**不部署、不上线、不 commit、不建 git 仓库**（除非用户单独批准）。

---

## 0. 用户拍板记录（2026-11-09）

| 决策 | 结果 |
| --- | --- |
| 阶段主线 | 锁定 3D 路线并做 **P0 切片**（非发布、非只出探索稿） |
| 技术路线 | **路线 B · Vite + React + R3F**（推翻工程侧原推荐的路线 A） |
| 验收基线 | **允许重定义门控**（不再要求 110 项原样全绿） |
| 缓存治理 | **46 + N 各自唯一**：2D 遗产层 46 处一组、构建/vendor 层 N 处一组 |
| three 版本 | **0.186.1**（与 Polyspoon pinned 一致，且在 postprocessing peer `<0.188.0` 内） |
| 落地形态 | **直接改造 `音标拉力赛/` 主站**，由 Vite 接管；2D 保留为 L0 降级层 |
| ADR-2 | 硬约束，**不接受放宽、无需拍板**：Rapier 只进视觉层，绝不替换 `odo/lateral + g.line` 判定 |

P0 阶段默认不启用：Rapier、GLB / Polyspoon 社区模型、听障视觉冗余、M9 回放日志（不新增 localStorage 字段）。

---

## 1. 三条主理人裁决（当场指出的内在冲突）

### 裁决 1 · 判定核心零改动（最高优先级）

预研 §3 写「路线 B 判定逻辑需移植为 TS 模块」，**与 ADR-2 / §7-1 硬约束直接冲突，本规格否决该表述**。

- `js/race.js`、`js/track.js`、`js/config.js` 中的 `odo/lateral`、`g.line = startOdo + lineT·L`、`buildGates()`、`judge()`、`beginDecide()`、`hitsLane()`、`TUNING.laps=2`、follow 260 / listen 300 —— **保持独立原生 JS ESM 模块，逐字不改、不移植 TS、不进 React state、不由 rAF 驱动判定**。
- Vite 只做 `import` 消费；R3F 组件只能通过 `snapshot()` 只读取判定结果用于渲染。
- `js/headless_laps.mjs` 必须**原路径、原命令**可跑，11 场 `ALL PASS`、最慢 174.57s ≤ 180s 仍是 Go/No-Go 硬条件。
- `main.js` 主循环本轮**不改**；P0 不接 GLB、不引 Rapier。

### 裁决 2 · 「46 + N」在构建链下的准确含义

Vite 会把 `index.html` 与模块打包，源码里的 `?v=` 字面量在**产物层**会消失或变形。因此：

- **源码层（2D 遗产层）**：`hud-20261108` 的 46 处字面量**保留、不删除、不批量替换**，作为 2D 主形态与四套历史门控的溯源标识；这一层继续唯一且恰好 46。
- **产物层（构建层）**：Vite content-hash 文件名 + 一份 `vendor.manifest.json`（three / R3F / drei / postprocessing 及后续 GLB），构成 N 处独立清单，**单独一个 `VENDOR_TAG`**。
- 两层**各自唯一、互不混算**；S17/F8a/H11 的「恰好 46」不再对 `dist/` 生效，改由新门控分别锁源码层 46 与产物层 N。
- 20 个图片 URL「零裸引用」口径**继续有效**，源码层不得出现无 tag 的图片 URL。

### 裁决 3 · 重定义门控 ≠ 降级门控

用户允许重定义的是**测法**，不是**覆盖面**。以下五类断言重定义后逐条保留，缺一不可：

1. 判定核心确定性（两圈、门线、听音题正确性、11 场 headless ≤180s）
2. 跨站 `localStorage['ipa-quest-v1']` 单键保真（C08 白名单、`rally` 嵌套字段不互相覆盖）
3. 美式 IPA 单一显示源 `window.IPA_DISPLAY` 不被破坏；`sym` 稳定键不动
4. quiz 答案零泄露（83 词全表 + `correctLateral/spoken/left/right` 字段名不出现在 HUD DOM）
5. 四项错误计数 `pageerror / console_error / requestfailed / bad_status` 归零口径

**不得**以「门控重写」为由删断言、放宽阈值、跳过浏览器实跑或把 FAIL 改 NOTE。

---

## 2. P0 范围（最小、零玩法风险）

### 做

1. 在 `音标拉力赛/` 建 `package.json` + `vite.config.js`，Vite 接管主站的 dev server 与 build；2D 游戏作为 **L0 主形态**继续原样运行。
2. 新增一个**可开关的 R3F 探针**（独立入口或 overlay，默认关闭，不进主循环）：一个立方体 + `FogExp2` 纸雾 + 单一暖主光，仅用于验证 WebGL / importmap 等价物 / 构建链。
3. 解决跨目录资源（见 §3），实测 `../音标大闯关/` 下 48 立绘 / 29 成稿图 / 音频 / `ipa-display.js` 在 dev 与 build 两种模式下**按字节送达全等**。
4. 落 `vendor.manifest.json` 与 `VENDOR_TAG`，版本钉定 three `0.186.1`；核实 `@react-three/fiber` / `drei` / `@react-three/postprocessing` 的 peer 上界后再钉其余版本。
5. 更新 `3d-adr.md`：ADR-1 / 3 / 4 / 5 / 6 状态由 Proposed → 按路线 B 重写或标 Superseded；**ADR-2 保持 Accepted 且内容不变**。
6. P0 前在 `.workbuddy/backups/` 新建一份**改动前全量快照**（产品代码 + 四套门控脚本），manifest 写明日期与可回滚范围。

### 不做

- 不改 `js/main.js` 主循环、不把 2D `render()` 迁进 React
- 不碰 `data.js` / `ipa-display.js` / 48 立绘 / 48 卡面 / 29 成稿图 / 上游构建管线（`content_raw.json`、`build_data.py`、`augment_data.py`）
- 不重跑上游管线、不新增 localStorage 字段、不引 CDN 运行时依赖
- 不装 Rapier、不接 GLB、不引 Polyspoon 社区模型
- 不部署、不上线、不 commit、不改 `音标大闯关/deploy.sh`

### Go / No-Go

| 条件 | 判据 |
| --- | --- |
| 判定未受影响 | `node js/headless_laps.mjs` 11 场 ALL PASS，最慢 ≤180s |
| 2D 主形态可用 | 现有 2D 页面在 dev 与 build 下完整可玩（真实 Chromium 冒烟，含 375×780） |
| 3D 探针可用 | 375px / 320×568 下 WebGL 上下文创建成功、立方体与纸雾可见、可一键关回 2D |
| 资源送达 | 跨目录资源按**逐字节 + magic + sha256 + Content-Type 非 `text/html`** 复核（**不信状态码**） |
| 零外链 | network 面板无产品功能依赖的外部 host 请求（现有 Google Fonts 属已知项，需单列披露） |
| 体积 | 记录 dev/build 首屏 JS 体积、请求数、帧时间，作为 Rapier 取舍的实测依据 |
| 门控 | quality-lead 出的新一轮规格跑通，覆盖面满足 §1 裁决 3 |

---

## 3. 必须实测的技术风险（不臆造方案）

| # | 风险 | 说明 |
| --- | --- | --- |
| T1 | **跨目录资源** | Vite root 在 `音标拉力赛/`，但 `index.html` 大量引用 `../音标大闯关/`：`ipa-display.js`、favicon、a1.webp、U01/U02 立绘，运行时还有 48 立绘 / 29 成稿 / 音频。`server.fs.strict` 默认会拦 root 外访问；`vite build` 对 `../` 引用可能打包失败或产出到 `dist` 外。**方案由 engineering-lead 实测后给出，本规格不预设**。 |
| T2 | `ipa-display.js` 是普通同步 script | 依赖「普通脚本先于 module 执行，`window.IPA_DISPLAY` 就绪」的时序（见 index.html 注释）。Vite 处理 HTML script 后须验证该时序不变，否则 48 卡面与答案显示会失效。 |
| T3 | `../音标大闯关/index.html#/map` 跨站跳转 | `deploy.sh` 目前是 scp 静态文件；`dist/` 形态下两站是否仍同 root / 同源，直接决定共享 `localStorage['ipa-quest-v1']` 是否成立。**P0 只需给出结论与部署建议，不实施发布**。 |
| T4 | 缓存双命名空间 | 源码层 `?v=` 与产物层 content-hash 并存；importmap / 模块 specifier 与相对路径混用的浏览器缓存行为（预研 K-7）需抓 network 面板实测。 |
| T5 | 字体外链 | `fonts.googleapis.com` / `gstatic.com` 当前存在；四项错误计数口径把外链失败列为环境项单列，实测时不得把它算进产品失败，也不得反过来用它掩盖同源失败。 |

---

## 4. 分派

- **engineering-lead**：按 §1 / §2 / §3 落地 P0，自测后出实现报告（落 `design/p0-impl-report.md`），消息只回 3–6 行结论 + 路径。
- **quality-lead**：出「路线 B 门控重定义规格」（落 `design/p0-qa-spec.md`），只写规格与脚本草案，**不修改现有四套门控脚本、不碰产品代码**；待 engineering-lead 产物定型后再实跑。
- 两条线**文件不重叠，可并行**；长报告一律落盘，消息通道只回结论。

---

*规格 v1.0 · team-lead · 2026-11-09 · 本文只定义边界与验收，不含产品代码；发布边界不变。*
