# 音标拉力赛 · 3D 技术预研：四仓库评估、技术路线与创新机制

> **文档性质**：Task #14 / CSEG-3D-T · 只读技术预研与路线评估。**不写任何产品代码、不装依赖、不跑构建、不引入 CDN 运行时依赖到产品页**。产出两条技术路线交用户拍板，**本报告不替用户拍板**。
> **本轮唯一写入物**：本文件 + `design/3d-adr.md`。未改动 `js/` / `index.html` / `css/` / 任何图片资产 / 四套验收脚本 / `data.js` / `ipa-display.js` / 上游构建管线。不部署、不上线、不 commit。
> **作者**：engineering-lead（程基岩） · **优先级** P0 · **查证日期** 2026-11-09（联网实时查证，非凭记忆）
> **上游依据**：`design/hud-ux-spec.md`、`design/visual-direction-3d.md`(v1.1)、`design/hud-impl-plan.md`、`js/config.js`、`js/render.js`、`js/main.js`、`js/race.js`、`index.html`、`css/game.css`、四套验收脚本、`design/hud-impl-report.md`；并行方向稿 `design/visual-direction-3d-v2.md`（只读参考，工程侧不消费其技术判断，见 §0.4）。

---

## §0 阅读约定与本轮边界

### 0.1 三类信息严格分离（主理人硬要求）

全文每个实质结论都带以下标记之一，不得混淆：

| 标记 | 含义 | 依据 |
|---|---|---|
| **【事实·已查证】** | 本次联网从仓库/官网/npm registry 抓取到的原文或数值，附 URL（编号见附录 A） | WebFetch / npm registry JSON / 官方 README / LICENSE 原文 |
| **【推断】** | 由已查证事实 + 本项目代码现状推出的工程判断，可能随实现变化 | 明确写出推理链 |
| **【建议】** | 待用户/主理人拍板的方案、取舍、阈值，非既定结论 | 明确标注需拍板 |
| **【待核实】** | 本次未取到原文或无法确证，绝不臆造 API/数值 | 列入 §10 知识缺口 |

> **知识诚实条款**：凡引擎 API、许可证正文、体积、版本约束、活跃日期，一律以本次抓取到的原文为准；抓不到的写 `NOT SHOWN` 并登记为缺口。**不凭记忆写任何一个库的版本号或 API**。

### 0.2 引用规则

- 内联引用采用 `[F-n]`（Fact）/ `[D-n]`（本地源码事实）编号，URL 汇总在**附录 A**，正文关键处同时给裸链接。
- 本地源码事实（如 `TUNING.laps=2`）来自本轮 #3/#4 已核验的源码与 `hud-impl-report.md`，标 `[D-n]`。

### 0.3 只读边界自检（本报告执行前逐条确认）

- ✅ 禁止修改：`js/`、`index.html`、`css/`、图片资产、四套验收脚本、`data.js`、`ipa-display.js`、上游构建管线 —— 本轮零改动。
- ✅ 不装 npm 依赖、不跑构建、不引入 CDN 运行时依赖到产品页 —— 本报告里出现的所有 `importmap` / CDN 写法都是**未来路线的示意**，不是本轮落地。
- ✅ 可联网查仓库/文档 —— 已查，见附录 A。
- ✅ 不部署、不上线、不 commit。

### 0.4 与并行方向稿 v2 的关系（避免直连、避免冲突）

`design/visual-direction-3d-v2.md`（art-director 的 #15）§0.6 已声明：「渲染可行性 / 依赖 / 性能以 engineering-lead 的 `hud-impl-plan.md` 与 #14 预研为准」，且其 §0.5.2 新增「防泄题」硬约束（判定完成前只读音频包络与 `commitT`，严禁读 `gate.spoken` / `correctLateral` / `qType` / `hit`）。**这与本报告 §4 的隔离架构同向**，我在 §4.6 / M5 用工程手段把它落实为可测试的守卫。按 Handoff 要求，**不与其他成员直连**，v2 只作只读参考、不引用其未定稿的技术结论。

---

## §1 现状硬地基（技术预研的约束面）

### 1.1 项目技术栈【事实·本地源码 [D-1]】

- `音标拉力赛/` 与姊妹站 `音标大闯关/`：**原生 ESM + Canvas 2D，无构建、无框架、无 npm 运行时依赖**，纯静态托管（Caddy）。
- `index.html` 用 `<script type="module" src="js/main.js?v=hud-20261108">` 直接加载，模块间用 `import ... from "./xxx.js?v=hud-20261108"` 相对路径拼接；**全仓 46 处 `?v=` 字面量 + 6 处 `TAG` 常量统一**为 `hud-20261108`（#4 已落地并报 110/110 门控全绿）[D-2]。
- 两站共享 **localStorage 单键 `ipa-quest-v1` 的 `rally` 嵌套对象**；跨站写入经 `main.js commit(mutator)`、`race.js applyWalletDelta()`、大闯关 `store.js refreshFromRaw()` / `RALLY_FOREIGN` 保真；**不新增 localStorage 字段**是 #4 已守住的约束 [D-3]。

### 1.2 不可动摇的已验收资产【事实·本地源码 [D-4]】

| 资产 | 口径 |
|---|---|
| 赛制 | 2 圈制 `TUNING.laps=2`、`commits:[0.24,0.68]`、follow `speed:260` / listen `speed:300` |
| 判定 | **确定性轨道模型**：绝对里程 `odo` + 横向 `lateral`，`g.line = startOdo + lineT·L`；`track.length ≈ 19254.5`；`t = (odo/L) % 1` 只作轨道采样 |
| 计时 | 11 场 headless 两圈实跑最慢 **174.57s ≤ 180s**，`node js/headless_laps.mjs` ALL PASS |
| 题库 | 四区杯赛 37 词对 / 18 音素 / 3 题型 / 83 词 83 mp3 |
| IPA | 美式 IPA 唯一权威表 `window.IPA_DISPLAY`，`sym` 为英式稳定键（`displayIpa` 禁止作键，U05/U07 同为 `ɑ`） |
| 门控 | 四套脚本 `verify_cseg_gate.py` 38 + `verify_cseg_ui.py` 14 + `verify_fresh_gate.py` 21 + `verify_c08_gate.py` 37 = **110 项** |
| 资产 | 29 张成稿 + 48 立绘 `U01–U48.webp` + 48 卡面 + `rarity_progress.webp` + 20 个图片 URL 零裸引用 |
| HUD | #4 落地的 `#minimap` / `minimapModel(view)` 纯函数 / S0–S3 路牌状态机 / 事件契约 / `window.__rally` 只读 getter |

### 1.3 用户已拍板项与发布边界【事实·任务简报 [D-5]】

第三人称**跟车视角**、预告 = **路牌** + 右上角**该轮比赛小地图**、视觉方向 **「甲 · 立体书」**（世界层轻 3D / 平面层全 2D / 纸雾收敛 / 克制烫金）、真 3D 化在**发布之后**的下一轮、**不部署 / 不上线 / 不 commit**。

### 1.4 由此得出的第一性判断【推断 I-1】

> **「整个游戏做成 3D」在本项目里 = 渲染层（View）替换，不是玩法层（Model/Judge）重写。**

理由链：`odo/lateral` + `g.line` 判定与 2 圈 3 分钟计时是纯数值确定性逻辑，与绘制方式解耦（#4 已把 `minimapModel(view)` 抽成可 Node 单测的纯函数，证明 view 可以换而 model 不动）。因此任何 3D 路线都必须**保留 `race.js` / `track.js` / `config.js` 的判定核心与 110 项门控的判据基础**，只替换 `render()` 及在其之上叠加的视觉层。这条判断是 §3 两条路线与 §4 隔离架构的共同前提。

---

## §2 四仓库逐仓评估（联网实际查证）

### 2.0 查证方法与事实基线

本次对四个仓库逐一抓取了 **GitHub 仓库页 README / 文件树 / LICENSE 正文 / package.json**、**npm registry 的 `dist` 元数据（精确 `unpackedSize` / `fileCount` / peerDependencies / license）**、**官网首页与 docs**。全部 URL 与抓取结果见**附录 A**。查证日期 2026-11-09。

### 2.1 主理人「技术现实」的核实结果【事实·已查证】

> 主理人简报：`drei` / `react-three-rapier` / `react-postprocessing` 全是 R3F 生态，需 React + 构建链，本项目直接搬用不了；但底层能力都有非 React 形态。

**核实结论：完全成立，且比"需 React"更严格**——三个包不仅 peer-depend on `@react-three/fiber`，还**同时**把 `react ^19` 与 `three` 列为 peer：

| 包 | `peerDependencies`（原文） | `license` | 发布版本 |
|---|---|---|---|
| `@react-three/drei` | `@react-three/fiber ^9.0.0`、`react ^19`、`react-dom ^19`(optional)、`three >=0.159` [F-1][F-2] | MIT [F-3] | 10.7.9 [F-2] |
| `@react-three/rapier` | `@react-three/fiber ^9.0.4`、`react ^19`、`three >=0.159.0` [F-4] | MIT [F-5] | 2.2.0 [F-4] |
| `@react-three/postprocessing` | `@react-three/fiber >=9.7.0`、`postprocessing ^6.36.0`、`react ^19.0.0`、`three >=0.156.0` [F-6] | MIT [F-7] | 3.2.2 [F-6] |

**这三条是硬事实**：无 React 19 + 无 R3F v9 + 无构建链，则三类 R3F 包装器**均无法直接 import**。README 也逐字坐实：drei 是 "useful helpers for **@react-three/fiber**" 且 "using the stand-alone `three-stdlib` instead of `three/examples/jsm`" [F-8]；react-three-rapier 是 "a **wrapper library around the Rapier WASM-based physics engine**, designed to slot seamlessly into a `react-three/fiber` pipeline"，且 v2 明确 "adds support for @react-three/fiber v9 and react v19" [F-9]；react-postprocessing 是 "a **postprocessing wrapper for @react-three/fiber**"，基于独立库 `postprocessing` [F-10]。

**但"直接搬用不了"不是上限**：主理人点破的三种底层能力，本次逐一查证到非 React 形态确实存在且可原生 ESM 挂载（§2.7），这是路线 A 的地基。

### 2.2 四仓库逐仓评估总表

> 「判定」四档：**能直接用** / **需改造** / **只取思路** / **不该用**。体积列用 npm `dist.unpackedSize`（整个 tarball 解包后字节，**不等于浏览器加载量**，见 §2.2.1 的重要澄清）。

| 仓库 | 判定 | 许可证（SPDX） | 体积（unpackedSize） | 是否需构建 | 375px 触屏性能 | 离线可用性 | 与本项目契合点 |
|---|---|---|---|---|---|---|---|
| **Polyspoon** `DITlieD/polyspoon` | **需改造后可用**（本地 vendor `.mjs` / GLB），**创新主抓手** | 分域：engine/toolkit/recipe = **Apache-2.0**；starter 预设几何 = **CC0-1.0**；pinned `three` 0.186.1 = MIT、`typescript` 7.0.2 = Apache-2.0；每模型须随包保留 notices [F-11][F-12][F-13] | 模型级：单个 low-poly 158–2,912 tris [F-14]；GLB 为主、`.mjs` 快照内嵌 GLB；整包体积 NOT SHOWN（按 recipe 生成，无单一发布包） | **不需要构建链**：recipe 是 TypeScript 小程序，输出的是已生成好的 `.mjs` / GLB [F-15][F-16] | 【推断】低（low-poly、单模型 <3k tris，48 精灵若实例化则更省）；但 48 个独立 GLB 的请求数与内存需实测 | **可完全离线**：本地 toolkit 明确 "needs no Polyspoon account, provider account, API key or inference service" [F-15]；⚠️ 唯一例外：**HTML 预览包从 jsDelivr 加载 three，需联网** [F-16] | ① `createAsset(parameters)` 把发音特征映射成几何参数（§5 M1）；② GLB 保留 rig/clips [F-17]；③ recipe 参数可复现、可版本化，天然适配 `CACHE_TAG` 治理 |
| **drei** `@react-three/drei` | **只取思路**（算法/组件设计可移植，整包不引入） | MIT [F-3] | **1,753,692 B ≈ 1.67 MiB** / 483 files [F-2] | **需要**：rollup 构建产物 `index.js` / `index.cjs.js`；peer React19+R3F9 [F-1][F-2] | 【推断】整包含 `@mediapipe/tasks-vision`、`hls.js`、`troika-three-text` 等重依赖 [F-2]，375px 低配不宜整体引入 | 【推断】纯前端包，构建产物可本地化离线；但需 React/R3F 运行时 | 只摘 `Environment`/HDRI 思路、`Instances` 实例化、`useGLTF` 加载缓存、`Billboard`、`CameraControls`、`shaderMaterial` 的**算法与设计**，用原生 three 重写 [F-8] |
| **react-three-rapier** `@react-three/rapier` | **不该用**（R3F 绑定层）；其**底层 `@dimforge/rapier3d-compat` 需改造后可用** | MIT [F-5]；底层 rapier 引擎 **Apache-2.0** [F-18] | 包装器 2.2.0 体积 NOT SHOWN；底层 `@dimforge/rapier3d-compat` **15,038,573 B ≈ 14.34 MiB** / 54 files [F-19] | 包装器需构建；底层 compat 版**可原生 ESM**（`dist/rapier.mjs`）[F-19] | 【推断】14.34 MiB 主要是 base64 内联 WASM [F-19][F-20]，首屏 JS 体积是路线 A 最大单笔成本；375px 低配需懒加载 | **可完全离线**：compat 版把 WASM 内联进 JS，**不需要单独 `.wasm` 请求**、不需要服务器配 wasm MIME [F-20] | 只用于**视觉层**（悬挂/碰撞特效/道具/装饰），绝不替换判定（§4） |
| **react-postprocessing** `@react-three/postprocessing` | **不该用**（R3F 绑定层）；其**底层 `postprocessing` 需改造后可用** | MIT [F-7]；底层 `postprocessing` **Zlib** [F-21] | **2,774,205 B ≈ 2.65 MiB** / 9 files [F-22] | 包装器需构建（Vite）；底层独立库 `build/index.js` 为 ESM，`type:module` [F-22] | 【推断】后期全屏 pass 是 fill-rate 敏感；方案甲「克制烫金、禁全屏 bloom」[D-5] 下建议**默认关闭或仅 L2 档启用** | 【推断】可本地 vendor 离线 | 底层库可 vanilla three 直接用（`EffectComposer`/`EffectPass`/`RenderPass`/`BloomEffect`）[F-23]；但方案甲明确「禁止全屏 bloom / 多光源硬高光」[D-5]，契合度**最低** |

#### 2.2.1 体积口径的重要澄清【推断 I-2】

`unpackedSize` 是 **npm tarball 解包后的全部文件**，与浏览器实际下载量差异极大：

- `three` 0.187.0 = **21,030,536 B ≈ 20.06 MiB / 1277 files** [F-24]，但这是含 `examples/`、`src/`、`docs/` 的整包；浏览器只需 `build/three.module.js`（`module` 字段）[F-24] + 少量 `three/addons/*`。**不能用 20 MiB 当作首屏成本**。
- `@dimforge/rapier3d-compat` 0.21.0 = 14.34 MiB / **54 files** [F-19]，且 npm 描述逐字为 "Compatibility package with **inlined webassembly as base64**" [F-19] —— 这个体积**几乎全是必须加载的 WASM**，是实打实的首屏成本，且 README 明确 "This results in a **bigger package size**, but much wider bundler support" [F-20]。
- `postprocessing` 6.39.6 = 2.65 MiB / 9 files、`drei` 10.7.9 = 1.67 MiB / 483 files（后者大量小文件，HTTP 请求数劣势）[F-22][F-2]。

**结论**：路线 A 的真实首屏增量约 = three 的单文件 + rapier compat 的 ~14 MiB（若启用物理）+ GLB 资产；**是否启用 Rapier 是首屏预算的最大单点决策**。

### 2.3 Polyspoon 专项（创新主抓手，逐项复核主理人简报）

主理人简报的四形态与许可证要求**全部核实通过**，并补到更精确的再分发规则：

**① 定位**【事实·已查证 F-25】GitHub 仓库自述 "Polyspoon: an **open-source, AI-powered 3D asset community**. Turn recipes into editable models… every model human-reviewed. Starting with **low-poly** assets"；官网 "The open-source alternative to Polyfork. Every model is a **recipe: a small open-source program with named controls**" [F-14]。社区规模（查证时点）：**141 published models / 62 GitHub stars / 2 code contributors** [F-14]。`LICENSES/` 目录首次提交 **2026-10-26**（commit `89c7a1b` "Polyspoon open-source release"）[F-13]，与简报「2026-10 开源」一致；官网/仓库在 2026-11 上旬仍活跃（本次抓取到 `polyspoon-agent-4.zip` 等新产物）[F-26]。

**② 四种输出形态**（README "Choose an output" 原文）[F-16]：

| 形态 | 原文要点 | 对本项目的意义 |
|---|---|---|
| **GLB** | "Complete current asset in meters, with **semantic parts, anchors and declared joint groups**"；"GLB keeps **rigs and clips**，其他格式仅静态 mesh" [F-16][F-17] | 卡丁车/精灵可带语义部件与关节组，便于按部位换材质、做稀有度表现 |
| **Snapshot `.mjs`** | "Static embedded GLB. Its **asynchronous `createAsset()`** loads a scene; **it is not procedural**" [F-16] | 异步、内嵌 GLB，适合少量固定模型；不参与参数化创新 |
| **Procedural module `.mjs`** | "**Synchronous `createAsset(parameters)`** from the selected registered recipe, plus **metadata, types, cleanup and rigid-pose APIs**. The download starts from family defaults; **pass edits explicitly**" [F-16] | ⭐ **创新核心**：同步、纯参数驱动、带 cleanup / rigid-pose，可把发音特征直接编码成参数 |
| **Generator source ZIP** | "Editable **TypeScript**, default configuration, controls, **pinned rebuild tooling** and notices. It does not capture later browser edits" [F-16] | 可离线 rebuild；但需 TS 工具链，不是运行时依赖 |

另有 `controls JSON`（"every knob with its range, default, unit and current value"）[F-27]、`llms.txt` / `prompt.txt`（agent-readable）[F-27]。

**③ 关键工程约束**【事实·已查证 F-16】逐字：

> "The **HTML bundle preview loads Three.js from jsDelivr and needs internet**. **Procedural modules need the pinned Three dependency supplied by the consumer**."

这坐实两条：
- **HTML 预览包不能离线**，因此**绝不能把 HTML 预览包当产品资源**；只 vendor `.mjs` / GLB。
- **procedural `.mjs` 必须由消费方提供 pinned `three`** → 与本项目 `importmap` 的 `three` 版本钉定强耦合（§2.8）。

**④ 许可证与再分发（逐项核清，这是合规红线）**【事实·已查证 F-11][F-12][F-13]】：

`LICENSES/` 目录实际只有两个文件：`Apache-2.0.txt`、`CC0-1.0.txt` [F-13]。`docs/licensing.md` 的精确分域：

| 对象 | 许可证 | 再分发条件 |
|---|---|---|
| 原始 generator 实现 / runtime / authoring 工具 / control schemas | **Apache-2.0** | 保留 LICENSE、NOTICE、修改声明；不得覆盖既有第三方 notices [F-12] |
| 指定 starter 预设（work-lantern / cottage / tree / fence / crate / boulder / bench）的**原始生成几何/材质** | **CC0-1.0** | 在 distributed source ZIP 中 **`config.json` 是明确指定的 CC0 内容文件**；**TypeScript 代码与 `controls.json` 仍是 Apache-2.0** [F-12] |
| 新建 contributor recipe / preset / 私有编辑配置 | **不自动获得 CC0 或 project-authored 声明** | "Obtain a contributor's **explicit permission** and **record provenance/license scope before approving distribution**"；需在 `docs/contributing/source-packages.json` 的 recipe ID 下加声明，缺失或不支持的声明会被拒 [F-12] |
| 外部贴图/网格/字体/材质 | 保留各自条款 | "Generated outputs that incorporate **external textures, meshes, fonts or other material retain those materials' terms**" [F-12] |
| pinned 依赖 | **Three.js 0.186.1 (MIT)** + **TypeScript 7.0.2 (Apache-2.0)** | "Each archive includes **upstream license texts, TypeScript's NOTICE, and `dependency-licenses.json`**"；20 个可选平台包有 exact-version registry license/tarball/integrity 元数据，二进制不随 ZIP 分发 [F-12] |
| Unity fixtures / 编辑器模板 / 第三方资产 / 研究文档截图 | **排除**在 blanket declaration 与 public generator source archives 之外 [F-12] | 不纳入本项目 |

**⑤ `.mjs` 能否本地 vendor 进现有静态站**【推断 I-3，基于 F-15/F-16/F-12】：
- **可以，且这是最契合本项目的一步**：procedural `.mjs` 是同步 `createAsset(parameters)` 的纯模块、无网络依赖、本地生成；GLB 是单文件；两者都是静态资源，可直接放进站里用相对路径 + `?v=` 引用。
- **前提三条**：(a) 消费方提供 pinned `three`（用 importmap 钉版本）；(b) 保留随包的 license notices / `dependency-licenses.json` / TS NOTICE；(c) **只用自己写的 recipe 或明确 CC0/已获授权来源的 recipe**，不能把社区模型默认当成可自由商用——每个模型有独立 licence 与 review record [F-14][F-12]。
- **不引 CDN 运行时依赖**：`jsDelivr` 只出现在 HTML 预览包，产品页不引入预览包即可满足 #14 铁律。

**⑥ 对「所有资源带同一 `?v=` tag」缓存治理的影响**【推断 I-4，基于 D-2】：
- 现有 46 处 `?v=hud-20261108` 是**字面量硬编码 + 4 个验收脚本与 headless 的 TAG 常量**，S17/F8a/S1.7 断言「唯一且恰好 46 处」。
- Polyspoon 的 `.mjs` 是**JS 模块**，若按现有约定写成 `import { createAsset } from "./assets/vendor/U01.mjs?v=<TAG>"`，会**新增字面量、打破 46 计数**；且 `.mjs` 模块内部若再 `import "three"`，其 specifier 由 importmap 解析、**不带 `?v=`**，会造成「带 tag / 不带 tag」两套缓存命名空间。
- **【建议 R-1】**：3D 轮单独引入一个 `VENDOR_TAG`（或把 vendor 资源集中到一个 `assets/vendor/manifest.js` 单点导出），并把 S17 门控升级为「产品字面量 46 处 + vendor 清单 N 处，两处各自唯一」；**具体计数改动必须走新一轮 QA 规格，不在 #14 预研里定死**。这条直接列入 §9 需拍板问题。

### 2.4 drei 专项【事实 + 推断】

- **事实**：drei 是 R3F helpers 集合，`npm install @react-three/drei`；**显式采用 `three-stdlib` 而非 `three/examples/jsm`** [F-8]；`package.json` 有 20+ 运行时依赖（`@mediapipe/tasks-vision`、`hls.js`、`troika-three-text`、`camera-controls`、`three-mesh-bvh`、`maath`、`zustand` 等）[F-1][F-2]；`build` 脚本是 `rollup -c`，产物 `index.js`(ESM) + `index.cjs.js`(CJS) [F-1]；README 列出 `CameraControls` / `useHelper` / `Billboard` / `shaderMaterial` / `Gltf` / `useGLTF` 等分类 [F-8]。
- **推断 I-5**：drei 的价值对本项目**几乎全在"算法与思路"**：`Environment`（HDRI 环境光）、`Instances`（实例化 48 精灵/护栏）、`useGLTF`（GLB 加载 + 缓存 + preload）、`Text`/`Sky`/`CameraControls`（跟车相机阻尼）、`Billboard`（世界空间路牌朝向）、`shaderMaterial`（纸雾/烫金材质）。这些都能用原生 three + `three/addons/*` 重写，且**恰好命中方案甲「世界层轻 3D、禁全屏 bloom」的克制需求**——不需要 drei 的绝大多数重依赖。
- **【建议 R-2】**：路线 A 下 drei 判 **"只取思路"**；建立一份 `docs/engine-reference/three/算法移植清单.md`（下一轮产物，本轮不写），逐条记录从 drei 摘取的算法、原始 URL、许可证（MIT）、重写后的实现路径，满足 MIT 的版权声明保留义务。

### 2.5 react-three-rapier 专项【事实 + 推断】

- **事实**：包装器 v2.2.0，peer `@react-three/fiber ^9.0.4` / `react ^19` / `three >=0.159.0`，**硬依赖 `@dimforge/rapier3d-compat` `0.19.2`** [F-4]；README 明确是 Rapier WASM 的 R3F wrapper，v2 支持 R3F v9 / React 19 [F-9]；提供 `<Physics>` / `<RigidBody>` / 自动 collider / sensors / joints / `debug` / 手动步进 / snapshots 等 [F-9]。Rapier 引擎 LICENSE = **Apache-2.0**（Copyright 2020 Sébastien Crozet）[F-18]。
- **对隔离最关键的一条事实** [F-20]（npm README 逐字）：

> 主构建 `@dimforge/rapier3d` "**does not guarantee cross-platform determinism of the physics simulation** (but it is still locally deterministic, on the same machine)"；另有 `-simd` / `-deterministic` 三种构建；`-compat` 版 "**embed the `.wasm` file into the `.js` sources encoded with base64**" [F-20]。

- **推断 I-6**：这条**官方自述的不保证跨平台确定性**，是「Rapier 不得进入判定链」的**最强、最客观的论据**——即便同一台机器本地确定，跨设备/浏览器也无法保证 2 圈 3 分钟与听音判定的一致性，而本项目的 `odo/lateral` + `g.line` 是**纯数值、跨设备确定**的。故 §4 的隔离不是保守，是硬必需。
- **推断 I-7**：`@react-three/rapier` 钉的是 `0.19.2`，而 npm 上 `@dimforge/rapier3d-compat` 最新为 **0.21.0** [F-19] —— 两条路线会落在不同 rapier 版本；路线 A 直接 vendor 0.21.0 可绕过包装器的版本滞后，但也失去包装器的 `<Physics>`/自动 collider 便利，需自己写 RigidBody 生命周期。

### 2.6 react-postprocessing 专项【事实 + 推断】

- **事实**：v3.2.2，peer `@react-three/fiber >=9.7.0` / `postprocessing ^6.36.0` / `react ^19` / `three >=0.156.0` [F-6]；是独立库 `postprocessing` 的 R3F wrapper，`npm install @react-three/postprocessing` [F-10]；示例用 `<EffectComposer><DepthOfField/><Bloom/><Noise/><Vignette/></EffectComposer>` [F-10]；仓库用 Vite 构建、`pnpm`、React 19 [F-28]。
- **底层独立库事实**：`postprocessing` 6.39.6，**Zlib** [F-21]（Copyright © 2015 Raoul van Rüschen），`type:module`，`module: ./build/index.js`，**peer `three >= 0.168.0 < 0.188.0`** [F-22]；vanilla three 用法原文：`import { BloomEffect, EffectComposer, EffectPass, RenderPass } from "postprocessing"; const composer = new EffectComposer(renderer); composer.addPass(new RenderPass(scene, camera)); composer.addPass(new EffectPass(camera, new BloomEffect()));` 在 `requestAnimationFrame` 里 `composer.render()` [F-23]；自带 EffectPass 自动合并多效果、单三角形全屏渲染、WebGL2 MSAA [F-23]；效果清单含 Bloom/DOF/Vignette/SSAO/Noise/GodRays/Outline/ShockWave/ToneMapping 等 [F-23]。
- **推断 I-8**：这是四仓库里**与本项目契合度最低**的一层。方案甲 v1.1 §A.4 明确「**禁止多光源硬高光点与全屏 bloom**」「单一暖主光 + 柔和补光 + 轻 AO」[D-5]，而 postprocessing 的主要卖点（Bloom / GodRays / 强后期）恰是要克制的部分。**【建议 R-3】**：路线 A 默认**不启用**独立 postprocessing 库；纸雾收敛用 three 原生 `FogExp2` + 材质 `roughness` 实现即可，把 2.65 MiB 与 fill-rate 成本省下来；仅在 L2 高档、用户手动开启时作为可选模块懒加载。

### 2.7 底层非 React 能力：路线 A 的真正地基【事实·已查证】

| 底层库 | 版本 / license | ESM 入口 | 无构建可行性 | 关键事实 |
|---|---|---|---|---|
| **three** | 0.187.0 (r187, 2026-10-30) / **MIT** [F-24][F-29] | `build/three.module.js`（`module` 字段）；`exports` 含 `"./addons/*": "./examples/jsm/*"` [F-24] | ✅ 原生 ESM，README 用法即 `import * as THREE from 'three'` [F-30]；`build/` 目录在仓库中存在并随版本更新 [F-31] | `type:module`；`sideEffects` 仅 `./src/nodes/**/*` [F-24] |
| **@dimforge/rapier3d-compat** | 0.21.0 / **Apache-2.0** [F-19] | `dist/rapier.mjs`（`import` 条件导出）[F-19] | ✅ 可原生 ESM；**WASM 内联 base64，无单独 `.wasm` 请求** [F-20] | **0 dependencies** / 129 versions / 128 dependents [F-32]；`sideEffects:false` |
| **postprocessing** | 6.39.6 / **Zlib** [F-21][F-22] | `build/index.js` [F-22] | ✅ vanilla three 直接可用 [F-23] | peer `three >=0.168.0 <0.188.0` [F-22] |
| **three-stdlib** | drei 用它替代 `three/examples/jsm` [F-8] | — | 可选；路线 A 建议直接用 `three/addons/*`（three 自带 `examples/jsm`）[F-24] | 避免再引一层依赖 |

**importmap 官方口径【待核实 K-1】**：three.js 官方 Installation manual 页在本次抓取时返回 `Redirecting...`，GitHub `manual/en/introduction/` 路径返回 404，故**未取到官方 `<script type="importmap">` 示例的逐字原文**。但以下已查证事实足以支撑路线 A 的模块加载设计：three 的 `exports` 明确给出 `"./addons/*": "./examples/jsm/*"` [F-24]（这正是 importmap 中 `three/addons/` 前缀映射的落点）；Polyspoon 亦明确 procedural module 需「消费方提供 pinned Three」[F-16]。**importmap 属浏览器标准机制，但具体写法列入 §10 待核实，不在本轮臆造代码**。

### 2.8 版本钉定矩阵【事实·已查证 + 推断 I-9】

这是本次查证挖出的、对路线 A 影响最大的隐藏约束：

| 组件 | 版本 | 对 `three` 的约束 | 兼容性结论 |
|---|---|---|---|
| three（npm latest） | **0.187.0** [F-24] | — | 基线 |
| postprocessing | 6.39.6 [F-22] | **`>= 0.168.0 < 0.188.0`** | ✅ 0.187.0 在范围内，且是**上限内最后一批**；**升级到 three 0.188 会直接破 peer** |
| Polyspoon pinned three | **0.186.1** [F-12] | 精确 pin | ✅ 与 0.187.0 同 minor 段、在 postprocessing 范围内 |
| drei | 10.7.9 [F-2] | `>=0.159` | 宽 |
| @react-three/rapier | 2.2.0 [F-4] | `>=0.159.0` | 宽 |
| @react-three/postprocessing | 3.2.2 [F-6] | `>=0.156.0` | 宽 |

**推断 I-9**：路线 A 应把 `three` **钉在 0.186.1**（与 Polyspoon portable archive 完全一致）或 0.187.0（npm latest，仍在 postprocessing 上界内），并在 `docs/engine-reference/three/VERSION.md` 记录；**任何 three 升级必须同时复核 postprocessing 的 `< 0.188.0` 上界与 Polyspoon 的 pinned 版本**。这是 ADR-1 / ADR-3 的硬输入。

### 2.9 四判定汇总

| 仓库 | 最终判定 | 一句话 |
|---|---|---|
| Polyspoon | **需改造后可用（主抓手）** | 只 vendor `.mjs` / GLB、不引 HTML 预览包、随包保留 notices、pinned three 由 importmap 提供 |
| drei | **只取思路** | 摘 Environment/Instances/useGLTF/Billboard/CameraControls/shaderMaterial 算法，用原生 three 重写 |
| react-three-rapier | **不该用**（底层 compat 需改造） | 包装器是 R3F 绑定层；底层 `@dimforge/rapier3d-compat` 只进视觉层 |
| react-postprocessing | **不该用**（底层可选且默认不启用） | 方案甲禁全屏 bloom，独立库契合度最低；纸雾用原生 FogExp2 |

---

## §3 两条技术路线并列评估

### 3.1 路线 A · 原生 ESM 无构建

```
index.html  (静态，无构建)
  └─ <script type="importmap">  →  "three" / "three/addons/" → 本地 vendor/three/...【待核实 K-1 写法】
  └─ <script type="module" src="js/main.js?v=<TAG>">   ← 现有 46 处 tag 体系不动【建议 R-1 单独治理 vendor】
        ├─ race.js / track.js / config.js   ← 判定核心 100% 保留（零改动）
        ├─ render2d.js  ← 现有 render() 降级为 L0 低配/回退档
        ├─ render3d.js  ← 新增：three Scene/Camera/WebGLRenderer，消费 minimapModel(view) 同一 view
        ├─ hud/ (DOM+CSS)  ← 平面层 2D 100% 保留（#minimap / #signs / .panel）
        └─ assets/vendor/
             ├─ three.module.js (+ 少量 addons: GLTFLoader / FogExp2 / InstancedMesh)
             ├─ rapier3d-compat/ (懒加载，仅视觉层)   【可选】
             ├─ polyspoon/*.mjs  → createAsset(parameters) 生成 48 精灵 / 车体变体
             └─ polyspoon/*.glb  → 静态模型（带 semantic parts / rig / clips）
```

- **保留**：现有 `index.html` 结构、ESM 相对路径、`CACHE_TAG` 治理、localStorage 单键、四套门控的判据基础、`window.IPA_DISPLAY` / `sym`、48 张 `.webp` 立绘（作 decal / 对照）。
- **新增**：`importmap`、`render3d.js`、`assets/vendor/`、`minimapModel(view)` 的 3D 消费端、低配降级开关。
- **不引入**：React、Vite、任何 npm 运行时依赖、CDN 运行时依赖。

### 3.2 路线 B · Vite + React + R3F 重构

```
package.json / vite.config.ts / pnpm-lock.yaml  ← 新增构建链与依赖树
  └─ src/
      ├─ App.tsx (React 19 + <Canvas> @react-three/fiber v9)
      │    ├─ <Environment/> <Instances/> <useGLTF/>  ← drei 全量
      │    ├─ <Physics><RigidBody/></Physics>          ← @react-three/rapier
      │    └─ <EffectComposer><Bloom/></EffectComposer> ← @react-three/postprocessing
      ├─ game/  ← 把 race.js/track.js/config.js 判定逻辑移植成 TS/React 可消费模块
      └─ hud/   ← 现有 DOM HUD 重写为 React 组件
  构建产物 dist/ → 静态托管（不再能直接托管源码目录）
```

- **代价**：引入 React 19 + R3F v9 + drei 10.7.9 + rapier + postprocessing + Vite + TS + pnpm 整套工具链；`index.html` / 模块加载方式 / 缓存治理 / 四套验收脚本的**所有静态断言基础被替换**。

### 3.3 逐项对比矩阵

| 维度 | 路线 A · 原生 ESM 无构建 | 路线 B · Vite+React+R3F 重构 |
|---|---|---|
| **110 项门控** | ✅ **判据基础保留**：S17/F8a/S1.7 的 46 处 tag、S12/S13/S7/S11 源码字面量、20 图片 URL 零裸引用、C08 跨站保真、U1/U12 浏览器错误计数，全部仍可按原断言跑；只需为 vendor 资源新增少量断言 [D-2][D-4] | ❌ **大面积失效**：`index.html` 由构建生成、`<script src>` 与 `?v=` 形态变化、模块被打包、46 处字面量断言失去意义；四套脚本需重写并重新定义「全绿」的含义。**这是迁移成本的最大项** |
| **跨站 localStorage `ipa-quest-v1`** | ✅ 零影响：`commit()` / `applyWalletDelta()` / `RALLY_FOREIGN` 全保留 [D-3] | ⚠️ 需把副作用式 `commit()` 迁进 React 状态管理，跨站写入时序与「不新增字段」需重新验证；风险中等偏高 |
| **纯静态托管（Caddy 直接托管源码目录）** | ✅ 零影响，仍是拷贝目录即服务 | ❌ 必须先 `pnpm build` 产出 `dist/`，托管对象从源码变为构建产物；CI/CD 与回滚流程都要建 |
| **离线可用** | ✅ 全部本地 vendor；rapier compat 内联 WASM 免 `.wasm` 请求 [F-20]；Polyspoon 本地 toolkit 免账号/API [F-15]。⚠️ 唯一例外是 Polyspoon HTML 预览包（不引入即可）[F-16] | ⚠️ 构建产物可离线；但 dev 期依赖 npm registry、构建期需联网 |
| **375px 触屏 / 低配降级** | ✅ 可精确做**三档 L2/L1/L0**：L0 直接回退到现有 2D `render()`（v1.1 §H.3 已定义）；HUD 平面层 2D 不动，可读性与触控热区零回归 [D-5] | ⚠️ R3F/React 运行时本身是固定开销，L0 回退要额外维护一套非 React 渲染路径，等于同时维护两套栈 |
| **2 圈 3 分钟 / 174.57s ≤180s** | ✅ 判定核心零改动，headless `node js/headless_laps.mjs` 仍可直接跑，计时口径不变 [D-4] | ⚠️ 判定逻辑需移植为 TS 模块，headless 脚本要跟着改；计时与确定性需重新验收 |
| **29 成稿 + 48 立绘 + 48 卡面** | ✅ 100% 复用：48 张 `.webp` 作 decal / 徽章位 / 收集册对照，零改动、零乱码风险（v1.1 §C.3 / §I.3）[D-5] | ⚠️ 需把图片资源接入 Vite 的 asset 管线（hash 文件名），与 `?v=` 缓存治理冲突 |
| **`window.IPA_DISPLAY` / `sym` 稳定键 / 无字底版** | ✅ 平面层 2D DOM 合成，硬约束天然满足 | ⚠️ 若用 3D Text / troika 渲染 IPA，会踩「AI 直渲乱码」与「canvas 文字不受 CSS 缩放」两条红线（v1.1 §0.5 / §E.4），需额外约束 |
| **迁移成本** | 中：新增 `render3d.js` + vendor 目录 + importmap + 低配降级；判定/存档/题库零改动 | **高**：全栈重写 + 四套门控重写 + 构建部署链路 + 两套 HUD 维护 |
| **可回滚性** | ✅ **极高**：3D 是叠加层，`RENDER_MODE=2d` 或 L0 档一键回到现有 2D；回滚点沿用 #3 的 `hud_backup_20261108/` 思路 | ❌ 低：一旦切到构建产物，回到「无构建源码托管」需要完整反向迁移 |
| **主要风险** | importmap 写法待核实 [K-1]、vendor 资源与 46 处 tag 的缓存治理 [R-1]、rapier compat 14.34 MiB 首屏 [F-19]、three 版本上界 `<0.188.0` [I-9] | 门控体系重写、构建链引入、React 运行时开销、与「无构建」现状的根本性断裂 |

### 3.4 迁移成本 / 可回滚性 / 风险小结

| | 路线 A | 路线 B |
|---|---|---|
| 一次性迁移 | 新增 1 个渲染模块 + vendor 资源 + 降级开关 | 全项目重构 + 四套门控重写 + CI/CD |
| 长期维护 | 单栈（ESM），2D/3D 共用同一 model 与 HUD | 双栈并存（React 3D + 2D 回退） |
| 回滚 | 配置开关级，秒级 | 需反向迁移 |
| 与「发布边界」兼容 | ✅ 不改部署形态 | ❌ 改变部署形态 |

### 3.5 推荐及理由【建议 R-4，**不替用户拍板**】

> **工程侧推荐：路线 A · 原生 ESM 无构建**，并把 drei / react-three-rapier / react-postprocessing **全部判为「只取思路 / 不该用」，只消费其底层非 React 能力与 Polyspoon 的程序化 `.mjs`/GLB**。

**理由（按权重）**：
1. **判定与资产零回归**：110 项门控、跨站 localStorage、`odo/lateral` 判定、2 圈 3 分钟、83 词题库、48 立绘全部不用动，风险面最小 [D-2][D-4]。
2. **可回滚性决定试错成本**：3D 化是发布后下一轮的高不确定探索，路线 A 允许「做坏了立刻回 2D」，路线 B 是单向门 [§3.4]。
3. **与用户已拍板的「甲 · 立体书」天然吻合**：世界层 3D / 平面层 2D 的分层混合，正是"只换渲染层、HUD 保持 DOM" [D-5][v1.1 §F.3]。
4. **离线 + 静态托管 + 无 CDN 运行时依赖** 三条发布边界全部守住（§2.3⑤）。
5. **Polyspoon 的创新抓手在路线 A 下才能低成本兑现**：`createAsset(parameters)` 是同步纯模块，直接 vendor 即可；路线 B 反而要把 recipe 塞进 React 生命周期，多一层阻抗。
6. **路线 B 的收益（drei/rapier/postprocessing 开箱即用）在本项目被大幅稀释**：方案甲禁全屏 bloom 使 postprocessing 契合度最低；Rapier 被限制在视觉层（§4）；drei 只需 6 类算法而不需要整包。

**但必须诚实给出的路线 B 优势**：若未来目标是**大规模 3D 内容生产 + 复杂场景编排 + 团队化组件复用**，R3F 的声明式组件、drei 的成熟 helper、React 生态的工程化收益会随规模增长而反超。因此这是**"当前项目规模 + 当前发布边界"下的推荐**，不是对 R3F 的否定。

### 3.6 需用户拍板的问题（详见 §9）

- 是否接受「推荐路线 A」？（本报告不拍板）
- 是否启用 Rapier 物理（14.34 MiB 首屏 vs. 视觉层丰富度）？
- vendor 资源与 46 处 `?v=` tag 的治理口径？
- 3D 化的验收标准：是否要求 110 项门控**原样全绿**？

---

## §4 玩法判定与物理仿真隔离（硬约束）

### 4.1 为什么必须隔离

**【事实·已查证】** Rapier 主构建 "**does not guarantee cross-platform determinism** of the physics simulation" [F-20]；而本项目判定依赖绝对里程 `odo/lateral` + `g.line = startOdo + lineT·L` 的**纯数值确定性** [D-4]。

**【推断 I-10】** 一旦让 Rapier 参与门线判定或车速推进，则：① 跨设备帧率/浮点差异会让 11 场 headless 的 `finishTime` 不再可复现，174.57s ≤ 180s 的余量失去意义；② 听音题的 `beginDecide()` / `judge()` 时机与物理步进耦合，答对率不可控；③ 四套门控里所有基于确定性里程的断言失效。**故 Rapier 只能用于视觉层**——这是任务简报的硬约束，也是官方事实推出的必然结论。

### 4.2 双时钟架构

| 时钟 | 名称 | 驱动 | 步长 | 职责 | 是否受渲染帧率影响 |
|---|---|---|---|---|---|
| **CLK-S（Sim / 判定时钟）** | 确定性仿真时钟 | 固定步长累加器（accumulator） | `dt = race.js` 的固定仿真步（现有 `mergeDt:0.028` 等），与 `requestAnimationFrame` **解耦** | 推进 `odo`、`lateral`、`g.line` 判定、`beginDecide()`、`judge()`、计分、解锁、`simTime` | ❌ **完全不受影响** |
| **CLK-R（Render / 视觉时钟）** | 渲染时钟 | `requestAnimationFrame` / `renderer.setAnimationLoop` | 变步长（跟随显示器与设备） | 相机阻尼、粒子、车身悬挂、Rapier 视觉物理步进、纸雾、路牌屏幕空间投影、HUD 更新 | ✅ 随帧率波动 |

**关键机制（固定步长累加器）【推断 I-11，标准游戏循环模式，待实现时验证】**：

```
frame(now):
  const wall = clamp(now - last, 0, MAX_FRAME_DELTA)   // 防止后台标签页回来时的巨大跳变
  accumulator += wall
  while (accumulator >= SIM_DT):        // 固定步长，可能与本次 rAF 执行 0 / 1 / 多次
      race.step(SIM_DT)                 // ← 唯一的判定推进点，纯数值、无渲染、无 Rapier
      simTime += SIM_DT
      accumulator -= SIM_DT
  const alpha = accumulator / SIM_DT    // 仅用于视觉插值，不参与任何判定
  render3d(alpha, race.snapshot())      // ← 只读 snapshot，绝不回写 race
  updateHUD(race.snapshot())
```

- **判定只发生在 `race.step(SIM_DT)`**：与 rAF 频率无关；掉帧时循环会多跑几步补齐，卡顿时用 `MAX_FRAME_DELTA` 上限防止"螺旋死亡"。
- **`alpha` 只给视觉插值**：相机、车身、粒子可用它平滑，**任何 `g.line` / `odo` 比较都不读 `alpha`**。
- **quiz / paused 冻结**：#4 已实现的「冻结前后 `karts[0].odo` / `simTime` 相等」[D-2] 在 3D 下同样成立——冻结时 `accumulator` 不推进、`race.step()` 不调用，CLK-R 仍可继续渲染静态帧（HUD 保持显示但冻结）。

### 4.3 双坐标系

| 坐标系 | 数据 | 权威来源 | 用途 | 3D 渲染可否写回 |
|---|---|---|---|---|
| **COORD-ODO（判定域，1D+横向）** | `odo`（绝对里程）、`lateral`（横向）、`lap`、`g.line`、`commitT`、`lineT` | `race.js` / `track.js` / `config.js` | 判定、门线、分叉、计分、解锁、进度、`minimapModel.progress` | ❌ **禁止** |
| **COORD-XYZ（视觉域，3D）** | `Vector3` 位置、四元数朝向、Rapier rigid body transform、相机、光照 | three Scene + Rapier（视觉层） | 绘制、悬挂、碰撞特效、道具、装饰、纸雾 | ❌ 只单向读取 COORD-ODO |

**单向映射（ODO → XYZ，唯一合法方向）**：

```
odo ──► t = (odo / L) % 1 ──► track.sample(t) ──► (x, y) 曲线上的点
                                    │
                    lateral ────────┴──► 车道偏移 ──► Vector3(x, height, z)
                                                        │
                                      Rapier 视觉层 ◄────┘ （只读，做悬挂/抖动/特效）
```

- **禁止反向**：不得用 3D 物体的 `Vector3` 反推 `odo`，不得用 Rapier 碰撞结果修正 `lateral` 或 `g.line`。
- **`t` 只由 `odo` 派生**（#3 的 Q4 裁决：`t_i = (odo_i / L) % 1`）[D-2]；两圈同 `commitT` 用 `g.lap === lapNow` + `gate.id` 区分。
- 3D 世界单位与里程单位的换算系数由 `track.js` 的曲线采样统一提供，**只在渲染层应用**，不进判定。

### 4.4 数据流向图（文字）

```
┌───────────────────── 判定域（COORD-ODO / CLK-S，纯数值、可 Node headless）─────────────────────┐
│  config.js TUNING/DIFFICULTY/buildGates   race.js step()/beginDecide()/judge()/activeGate()   │
│        │                                                                                       │
│        ├──► g.line / odo / lateral / lap / gates[] / karts[] / simTime / score               │
│        │                                                                                       │
│        └──► race.snapshot()  ★只读视图，字段白名单（见 4.6）★                                │
└────────────────────────────────────────┬──────────────────────────────────────────────────────┘
                                         │ 单向、只读、每帧一次
                     ┌───────────────────┼────────────────────┐
                     ▼                   ▼                    ▼
        ┌────────────────────┐  ┌───────────────┐  ┌──────────────────────┐
        │  render3d.js       │  │  HUD (DOM 2D) │  │  audio / 事件契约     │
        │  three Scene       │  │  #minimap     │  │  rally:gate-preview  │
        │  ├ 相机(CLK-R 阻尼)│  │  minimapModel │  │  rally:gate-played   │
        │  ├ 赛道/GLB/精灵   │  │  #signs S0-S3 │  │  rally:gate-judged   │
        │  ├ FogExp2 纸雾    │  │  .panel quiz  │  │  rally:lap           │
        │  └ Rapier 视觉层   │  │  (平面层全 2D)│  │  payload 不含答案域  │
        │    悬挂/碰撞特效   │  └───────────────┘  └──────────────────────┘
        │    (只读 snapshot) │
        └─────────┬──────────┘
                  │ 只写视觉 transform，绝不回写判定域
                  ▼
        WebGLRenderer → <canvas>  （L0 低配回退 → 现有 2D render()）

   ⛔ 硬边界：COORD-XYZ / CLK-R / Rapier  →  odo|lateral|g.line|judge()  任何写入均禁止
   ⛔ 硬边界：gate.spoken / correctLateral / qType / hit  →  render3d.js / HUD / 环境特效  禁止读取
```

### 4.5 帧率波动下判定不受影响的机制（逐条可测试）

| # | 机制 | 可测试断言（供下一轮 QA） |
|---|---|---|
| 1 | 判定只在 `race.step(SIM_DT)` 固定步长内推进 | 人为把 rAF 降到 15fps / 提到 144fps，11 场 headless 的 `finishTime` 与门线判定序列**逐项一致** |
| 2 | `render3d` 与 Rapier 只读 `snapshot()` | 源码静态扫描：`render3d.js` / `physics-visual.js` 中零 `race.state.* =`、零 `judge(`、零 `beginDecide(` 调用 |
| 3 | `alpha` 不进判定 | `g.line - odo`、`D_preview` 比较式中不出现 `alpha` / `performance.now()` / `devicePixelRatio` |
| 4 | 冻结态不推进 CLK-S | `mode==='quiz'`：冻结前后 `karts[0].odo` / `simTime` 严格相等（#4 已有断言，3D 沿用）[D-2] |
| 5 | 视觉物理与判定物理分离 | 关闭 Rapier（L0/L1 档）后，判定结果与 L2 档**逐位一致**；Rapier 只影响车身抖动/特效 |
| 6 | WebGL 上下文丢失 | 上下文丢失/恢复期间 `race.step()` 继续按 CLK-S 推进或按 `MAX_FRAME_DELTA` 限幅，恢复后视觉与判定重新对齐，不产生"跳门" |

### 4.6 防泄题：单向铁律在 3D 世界的延伸【推断 I-12，基于 D-2 / v2 §0.5.2】

#4 已建立「`correctLateral` / `spoken` 只允许出现在 `audio.playWord()` 与 `judge()`，HUD 的 `innerHTML` / `fillText` / `data-*` / `alt` / `aria-label` 一律不得接触」[D-2]。3D 化后**攻击面从 DOM 扩大到整个世界层**（材质、光照、粒子、几何、动画都可能编码答案），故扩展为：

1. **字段白名单 `snapshot()`**：3D 渲染层只能拿到 `minimapModel(view)` 已定义的几何域（`id`/`lap`/`commitT`/`lineT`/`line`/`odo`/`laps`/`progress`/`nextGate.{id,lap,line,distance,secondsTo}`/`phase`）[D-2]；**`spoken`/`other`/`correctLateral`/`hit`/`qType`/`pairKey`/`left`/`right`/`word`/`ipa`/`displayIpa`/`sym` 一律不在 snapshot 里**。
2. **环境特效只读音频包络 + `commitT`**：声音可视化（M3）用 `AudioContext` 的时域/频域包络（能量、过零率、频带），**不读题库字段**；闸门几何只按 `commitT` 位置摆放。
3. **三层预告协同不泄答案（M5）**：路牌 S1 零文本中性态（#4 的 `paintForecast()` 只画 `◇`）、S2 两侧严格对称、小地图 `nextGate` 为中性菱形无左右指向；3D 世界空间指示牌同样只给「下一门距离/方位」，不给正确侧。
4. **可测试**：新增源码扫描断言（比 #5 的 H5 `<span>`/`pan` 陷阱更严）——`render3d.js` / `physics-visual.js` / `assets/vendor/polyspoon/*.mjs`（自写 recipe）中零答案域标识符；`rally:*` 事件 payload 不含 `hit`/`spoken`。

---

## §5 「教学 × 3D」创新机制（≥5 条，覆盖全部 6 方向 + 超出清单）

> 用户明确 **「不要把公开信息当作上限，要创新和突破上限」**；v2 §0.3 的防跑偏原则：「任何创新机制必须回答『它让哪个**教学难点**变可见了？』答不上来的一律归为装饰」。以下每条都先写教学难点，再给技术可行性 / 依赖 / 性能代价 / 防泄题，并标注 **【原创设想】** 或 **【现成可参考】**。

### M1 · 发音特征 → 几何参数：48 音标精灵与卡丁车造型变体【现成可参考：Polyspoon `createAsset(parameters)`】

- **教学难点**：48 个音标的**发音特征（舌位高低/前后、唇形圆展、气流阻塞方式、声带振动）**是抽象、不可见的；现有 48 张立绘是"各画各的图"，学生看不到特征与音素之间的**结构化对应**。
- **技术可行性**：Polyspoon procedural `.mjs` 的 **同步 `createAsset(parameters)`** [F-16] 正是为此而生：定义 1 套 `phoneme-sprite` recipe，把 `sym` → 参数向量 `{tongueHeight, tongueBackness, lipRounding, airflow, voicing, duration, manner, place}` 映射为几何旋钮（舌位→穹顶高度、圆唇→前端环半径、气流→尾迹条数与长度、声带→表面震颤振幅、时长→体块比例）。**一次生成、离线可复现、参数可版本化**；`controls.json` 天然承载每个音素的参数 [F-27]。卡丁车造型变体用同一 recipe 换 `preset`（波波/小 Q/咪咪剪影参数）。
- **⭐ 参数源硬约束（主理人 #14 补充 + 美术侧 v2 §3.4/R1，两份文档口径一致）**：`config.js:88-94` 的 `length` / `tone` / `color` 是 **A/B 分组着色键**（把最小对立对拆成 A/B 两组给左右车道配色），**不是语音学事实**——实证 `U09: ph("U09","ʊ","ʊ","短圆唇","长","long",…)`（/ʊ/ 实为短元音却标「长」）、`U10: ph("U10","u","uː","长圆唇","短","short",…)`（/uː/ 实为长元音却标「短」），字面值与语音学正好相反；`U03 ɛ` / `U21 p` 同样按分组需要交替赋值；`color: tone === "long" ? A_COLOR : B_COLOR` 也只是分组色 [D-6]。
  - **禁止**用 `length` / `tone` / `color` 生成**任何** 3D 几何、材质、稀有度、粒子或教学参数；照抄会让长短圆唇整体做反、并与 D1 三宝石语义冲突。
  - **参数表唯一权威源 = 另建一份经教研校验的发音特征表**（如 `phoneme-features.json`，按 `sym` 索引，schema 显式排除上述三字段）；直接消费现有字段时，**最小允许集 = `ipa` + `hint`**（与 v2 §3.4 逐字一致），`label` / `unit` 仅作索引与标识、**不驱动几何**。
  - **这不是 bug，不要「修」它**：改这些值会破坏最小对立对的 A/B 分组配色与 F5（`length:"长"` / `is-long` / `is-short`）、B7（同对 label 互异）等既有门控断言；报告仅标注为「**有意设计的分组键、命名易误导**」。
  - **可测试**：下一轮给参数表加最小对立一致性断言（如 `U10.lip.protrusion > U09.lip.protrusion`、`U32.voice.voiced === true && U31.voice.voiced === false`）；脚本交 quality-lead（与 v2 §3.4 建议一致，本报告不代写）。
- **依赖**：Polyspoon 程序化 `.mjs`（本地 vendor）+ pinned `three` 0.186.1（importmap）[F-12]；`sym` 作稳定键（**绝不用 `displayIpa`**）[D-4]；教研校验特征表（新建，非现有 UI/分组字段）。
- **性能代价**：【推断】同步生成在**构建/离线预处理期**完成，运行时直接加载 48 个 GLB/`.mjs`；单个 low-poly 模型 158–2,912 tris [F-14]，48 个合计仍在低配可接受范围；用 `InstancedMesh` 复用材质可进一步压 draw call（算法摘自 drei `Instances` [F-8]）。
- **防泄题**：参数表来自 `sym` 的**音素固有属性**，与某道题的 `correctLateral`/`spoken` 无关；生成过程在赛前完成，运行时只读。
- **合规**：只用**自写 recipe**（Apache-2.0，需保留 notices）或明确 CC0 来源 [F-12]；不把社区模型默认当可商用。

### M2 · 静态 F 口腔剖面 → 可交互 3D 口腔剖面【现成可参考：GLB semantic parts + three Raycaster】

- **教学难点**：现有 `音标大闯关/assets/img/f.webp` 是**静态二维**口腔剖面（舌位/唇形/气流/声带四要素）；学生无法从视角理解「舌尖抵上齿龈」这类空间关系，也无法看到发不同音时器官如何联动。
- **技术可行性**：用 Polyspoon GLB 的 **"semantic parts, anchors and declared joint groups"** [F-16] 建一个可拆解口腔：舌、齿、唇、软腭、声带各自是命名部件 + 锚点；three `Raycaster` 做拾取，点击部件高亮并联动显示对应 `sym` 的舌位参数；同一套模型按 M1 的参数驱动**变形**到不同音素，学生可拖动滑块看 /i/→/ɑ/ 的舌位连续变化。**IPA 文字全部 DOM 层后期合成**（无字底版硬约束）[D-5]。
- **依赖**：three `Raycaster` / `GLTFLoader`（`three/addons/*`，[F-24]）；Polyspoon GLB；`window.IPA_DISPLAY` 只用于 DOM 文本。
- **性能代价**：【推断】单场景、低 tris，可放在教学页（非比赛帧循环），几乎不影响 2 圈计时；建议按需懒加载，标题/教学页不常驻 WebGL 上下文。
- **防泄题**：教学页与比赛判定解耦，不接受 `gate` 对象。

### M3 · 声音可视化驱动环境（气流 → 粒子、声带 → 震颤）【原创设想 + 现成可参考：WebAudio AnalyserNode】

- **教学难点**：清/浊、送气/不送气、长/短、摩擦/爆破的差别**只在声音里**；2D 无法让"气流"和"声带振动"成为可观察的空间现象。
- **技术可行性**：用 `AudioContext.createAnalyser()` 从现有 83 个 mp3 实时取时域/频域包络（能量、过零率、低频占比、频谱质心），映射为：① **气流→粒子**：送气音触发前向锥形粒子流（数量/初速 ∝ 高频能量），塞音触发短促爆发；② **声带→震颤**：浊音让路面宝石标记、护栏、车身徽章产生低幅高频震颤（振幅 ∝ 低频能量），清音静止；③ **长短→拖尾长度**。关键在于这是**教学反馈**（让发音物理属性可见），不是背景特效。
- **依赖**：WebAudio `AnalyserNode`（浏览器原生，零依赖）；three `Points` / `InstancedMesh`；**不需要** postprocessing。
- **性能代价**：【推断】粒子用单个 `Points` + shader 而非逐粒子对象；包络每帧 1 次 `getByteFrequencyData`，成本极低；L0 档直接关闭粒子，仅保留静态色块（v1.1 §H.1「关闭后速度感改由 HUD 数字 + 静态尾焰表达」）。
- **防泄题**：⭐ **只读音频包络，绝不读 `gate.spoken`/`correctLateral`/`qType`** [v2 §0.5.2 / §4.6]。音频包络是**当前正在播放的声音的物理属性**，玩家本就听得到，不构成答案泄露；但必须杜绝"用题库字段预先点亮某一侧"的实现。
- **【原创设想】**：进一步做**「发音指纹」**——把每个音素的标准包络预烘焙成一条确定性曲线存进 `data`（构建期生成，运行时不计算），学生发声/听音后可对比自己的包络形状；这条曲线只用 `sym` 索引，与题目无关。

### M4 · 四区杯赛「立体书式」场景转场（方案甲）【原创设想：pop-up 几何动画；现成可参考：GLB + 纸卷擦除】

- **教学难点**：四区（camp 紧松元音 / castle 后元音圆唇 / kingdom 清浊辅音 / peak 摩擦鼻音卷舌）是**递进的知识结构**，现有切屏让「我在学哪一类音」的空间感断裂。
- **技术可行性**：v1.1 §D.2 已定义「纸卷擦除」转场 [D-5]；3D 下把它升级为**真 pop-up 立体书**：四区共用同一套「区门」几何，转场时纸卷从一侧卷起、下一区的微缩场景以折页立起（关节组动画，GLB 保留 clips [F-17]）；区色温/雾色按 §D.1 插值，天空穹顶保留纸纹（唯一允许纸纹的 3D 面，避免 mip 摩尔纹）[D-5]。**转场发生在杯赛之间（非比赛帧循环）**，不影响 2 圈计时。
- **依赖**：three `FogExp2`、`AnimationMixer`（GLB clips）；Polyspoon GLB 的 joint groups [F-16]。
- **性能代价**：【推断】转场是短时动画，可用低模 + 材质换色 + 镜像缩放（v1.1 §0.3「每区 ≤4 个可复用道具模块」）[D-5]，控制建模量；L0 档退化为 2D 纸带淡入。
- **防泄题**：转场只读 `mapId`/`zone`，不接触任何 gate 字段。

### M5 · 跟车视角下「路牌 / 世界空间指示 / 小地图」三层预告协同且不泄答案【原创设想：三层信息分层契约；现成可参考：#4 的 S0–S3 + minimapModel】

- **教学难点**：跟车视角**看不到整条赛道**，玩家必须在到达分叉前获得足够预告；但本作核心是**听音选车道**，预告绝不能暗示正确侧。
- **技术可行性**：把 #4 已落地的状态机 [D-2] 扩展到 3D 三层，且三层**共用同一个 `signState`**（#4 修过的"相位滞后一帧"问题，3D 下同样要单一来源）：

| 层 | S0 无门 | S1 中性预告 | S2 选项 | S3/判后 |
|---|---|---|---|---|
| **L2 世界空间路牌**（3D 锚定 + 屏幕空间最小尺寸锁，v1.1 §E.1） | 隐藏 | 零文本中性牌（◇ / 空白容器） | 两侧**严格对称**的候选项（文字 DOM 合成） | 隐藏 |
| **L1 世界空间指示**（地面宝石标记 / 暗红虚线 / 罗盘方位条） | 常驻中性 | 只给「下一门距离 + 方位」，无左右指向 | 同 S1，不放大单侧 | 常驻中性 |
| **L3 屏幕小地图**（`#minimap` DOM，平面层 2D） | `nextGate` 熄灭 | **中性菱形点亮**（`--gold-deep` 单色、无箭头、无高亮侧） | 保持 | 熄灭 |

- **依赖**：#4 的 `minimapModel(view)` / `computeSignState()` / `syncSigns()` / `rally:gate-preview` 事件契约 [D-2]；three 世界锚点投影（v1.1 §E.1 L2）。
- **性能代价**：【推断】三层共用同一状态，零重复判定；DOM 层保持 2D，成本可忽略。
- **防泄题**：⭐ 三层**全部**只能通过 §4.6 的 `snapshot()` 白名单取几何域；quiz 冻结时小地图显示但冻结、路牌隐藏（#4 已裁定口径）[D-2]；世界空间指示牌不得用材质/光照/粒子强弱暗示某一侧（这是 3D 新增的泄露面，需源码扫描断言）。

### M6 · 48 精灵作为可收集 3D 立绘，稀有度用材质 / 箔印 / 光照而非贴纸【现成可参考：GLB semantic parts + PBR 材质】

- **教学难点**：收集系统若只是「点亮一张图」，学生会把它当成就徽章而非**复习音素的入口**。
- **技术可行性**：把 48 精灵升级为可旋转、可打光的 3D 立绘（M1 的程序化形体），稀有度 `rarity_progress.webp` 的语义 [D-5] 用**材质语言**表达：铜/银/烫金边框对应 `metalness 0 → 0.7–0.85`、`roughness 0.9 → 0.3–0.4`、箔印走 `#c9a227→#f0d78c` 渐变贴图而非镜面反射（v1.1 §A.4 烫金规格）[D-5]；收集册里点击精灵可回放 M1 的发音参数动画 + M2 的口腔剖面，形成"收集→复习"闭环。**48 张现有 `.webp` 立绘 100% 保留**作对照与 decal，零重绘 [D-5]。
- **依赖**：three PBR 材质；Polyspoon GLB semantic parts（便于按部位换材质）[F-16]；`sym` 作解锁键 [D-4]。
- **性能代价**：【推断】收藏册是独立页面、非比赛帧；48 个模型用共享几何 + 实例化材质，只高亮当前选中的一个。
- **防泄题**：只读存档的解锁集合，不接触 gate。

### M7【原创设想】· 「可拆解立体书」音素构造台：把发音部位变成可拼装的几何

- **教学难点**：学生常把 `/p/`/`/b/`、`/f/`/`/v/` 记成孤立符号，不理解它们只是**「部位 + 方式 + 浊化」三个维度的组合**（kingdom 区「清浊双塔」的语义 [D-5]）。
- **技术可行性**：给一个 3 旋钮控制盘（部位 place / 方式 manner / 浊化 voicing），每个旋钮转到一个值时，**M1 的同一套 recipe 用 `createAsset(parameters)` 实时重建**对应音素的精灵与口腔剖面（M2），并高亮"当前组合落在哪个音素"。18 音素 [D-4] 全部由这三维张成，学生自己"拼"出音素而非背诵。参数化生成天然支持这种连续插值——这正是 48 张静态图做不到的。
- **依赖**：Polyspoon 程序化 `.mjs`（同步 `createAsset(parameters)` 是硬前提，异步 snapshot 做不到）[F-16] + M1 参数表。
- **性能代价**：【推断】同步生成在低频交互（用户转旋钮）时触发，非每帧；用 `cleanup` API [F-16] 及时释放旧几何避免内存增长——这正是 procedural module 自带 `cleanup` 的价值。
- **防泄题**：纯教学页，不接 gate。

### M8【原创设想】· 「声纹赛道」：把音素包络烘焙成赛道/护栏的几何节奏

- **教学难点**：「长短音」「紧松元音」的差别在 2D 里只靠颜色 label；跟车视角下学生需要**在驶过的路面本身**感知节奏。
- **技术可行性**：构建期把每个音素的标准音频包络（M3 的确定性曲线）烘焙成一段**路面浮雕 / 护栏间距 / 宝石标记节奏**的几何参数（长音→稀疏长条、短音→密集点、爆破→突然凸起、摩擦→连续细纹），随该区赛道铺设；学生"开过"这段路时，视觉节奏与刚听过的音互为印证。**烘焙是离线、确定性的，运行时零计算、零随机**，不破坏 2 圈计时。
- **依赖**：构建期脚本（新增，不进运行时）；three 几何生成；`sym` 索引。
- **性能代价**：【推断】用 `InstancedMesh` 沿曲线铺设，合并 draw call；L0 档退化为纯色路面。
- **风险**：必须与 v1.1 §A.4「英雄资产零污渍/噪声」「纸雾收敛」相容——节奏只用**几何起伏与刻线**，不用颜色噪声贴图，避免显脏。
- **防泄题**：铺设方案只由 `mapId`/`zone` 与该区音素集合决定，**不读当前 gate**，否则会在分叉前暴露题目。

### M9【原创设想】· 「时空复现回放」：3D ghost kart + 判定日志

- **教学难点**：学生答错后只看到对错，看不到「我是在哪一刻、离门多远时选错车道的」。
- **技术可行性**：判定域 CLK-S 是**固定步长、纯数值、完全确定**的（§4.2），因此一局比赛可只存 `{simTime, odo, lateral, gateId, phase, hit}` 的轻量日志（**不含音频**）；结算页用同一套 3D 场景 + 同一 `snapshot()` 重放，叠加一辆半透明 ghost kart 显示当时的选择。因为判定确定，回放与实况逐帧一致——**这是 2D 全景视角给不了的"时间维度"教学**，也顺带成为 §4.5 判定确定性的可视化验证工具。
- **依赖**：`race.step()` 的可重放性（现有 headless 已证明）；three；**localStorage 单键约束**：【建议 R-5】日志优先存内存/会话级，**不新增 localStorage 字段**（遵守 D-3）；若要持久化需单独拍板。
- **性能代价**：【推断】只在结算页重放，非比赛帧；日志体量小。
- **防泄题**：结算页展示 `hit` 属判后结果域（#4 白名单允许「判定后结果页可列」）[D-2]，但**比赛进行中不产生可读日志**。

> **创新机制计数：9 条**（M1–M9），覆盖任务清单全部 6 个方向（M1 / M2 / M3 / M4 / M5 / M6），并**超出清单 3 条原创设想**（M7 / M8 / M9）。其中 M1 的「参数化生成」、M3 的「只读音频包络驱动环境」、M5 的「三层预告不泄答案」、M8 的「声纹赛道离线烘焙」是本项目区别于通用 3D 特效堆砌的核心突破点。

---

## §6 风险与缓解（≥6 条）

| # | 风险 | 等级 | 缓解 |
|---|---|---|---|
| **R1** | **判定链被 3D/物理污染**：Rapier 官方**不保证跨平台确定性** [F-20]，若误用于 `odo/lateral`/`g.line`，11 场 headless 的 174.57s ≤180s 与听音题答对率不可控 | **P0** | §4 双时钟/双坐标系/单向 snapshot；`render3d.js` 与 physics-visual 源码扫描零 `race.state.*=` / 零 `judge(`；关闭 Rapier 判定逐位一致的回归断言（§4.5） |
| **R2** | **首屏体积**：rapier compat 14.34 MiB（base64 内联 WASM）[F-19] + three 单文件 + GLB，375px 低配与弱网首屏吃紧 | **P0** | ① Rapier **默认不启用**（§3.1 标可选/懒加载）；② 3D 资源按需懒加载，标题/选赛/教学页保持 2D（v1.1 §F.3.4）[D-5]；③ 三档 L2/L1/L0 降级，L0 回退现有 2D；④ 设定首屏预算并实测 |
| **R3** | **缓存治理被打破**：Polyspoon `.mjs` / GLB 新增资源引用会冲击「46 处 `?v=` 唯一」的 S17/F8a/S1.7 断言 [D-2]；`.mjs` 内部 `import "three"` 走 importmap 不带 `?v=`，形成两套命名空间 | **P0** | 【建议 R-1】单独 `VENDOR_TAG` 或集中 `assets/vendor/manifest.js` 单点导出，门控升级为「46 + N 各自唯一」；具体计数走新一轮 QA 规格，本轮不定死 |
| **R4** | **许可证/再分发合规**：Polyspoon 是**分域许可**（Apache-2.0 / CC0-1.0 / 各模型独立 licence / pinned deps notices）[F-11][F-12]；社区模型不自动 CC0，需 explicit permission + provenance [F-12] | **P1** | ① 只用**自写 recipe** 或明确 CC0/已授权来源；② 每个 vendor 包随附 `LICENSES/` 原文、TS NOTICE、`dependency-licenses.json`；③ drei 摘算法需保留 MIT 版权声明（§2.4 R-2）；④ 建立逐模型 provenance 台账 |
| **R5** | **版本钉定冲突**：postprocessing 6.39.6 peer 上界 `three < 0.188.0` [F-22]，Polyspoon pinned `three 0.186.1` [F-12]，npm latest `0.187.0` [F-24]；升级 three 会连锁破 | **P1** | `docs/engine-reference/three/VERSION.md` 钉 0.186.1（与 Polyspoon portable archive 一致）并锁 importmap；升级前跑 §2.8 矩阵复核；默认不启用 postprocessing 以缩小约束面（R-3） |
| **R6** | **CDN / 离线破口**：Polyspoon **HTML 预览包从 jsDelivr 加载 three 需联网** [F-16]，若误当产品资源将违反「不引 CDN 运行时依赖」铁律 | **P1** | 产品页**只 vendor `.mjs` / GLB**，明确排除 HTML 预览包；上线前跑「零外部 host 请求」断言（可复用四套门控的 requestfailed / bad_status 计数口径 [D-2]） |
| **R7** | **3D 新增的答案泄露面**：材质/光照/粒子/几何都可能编码 `correctLateral`；只防 DOM 不够（v2 §0.5.2） | **P0** | §4.6 `snapshot()` 字段白名单 + 环境特效只读音频包络 + 三层预告共用 `signState` + 世界空间指示牌源码扫描（§5 M5） |
| **R8** | **可访问性回退**：跟车视角眩晕、375px 两车道可读、系统字体缩放 200%（canvas 内文字不受 CSS 缩放）[D-5] | **P1** | 平面层 HUD 保持 DOM（§3.1）；沿用 v1.1 §H 的 `A11Y-TIER: Standard → Comprehensive`、三档降级、`prefers-reduced-motion` 复用现有 `reduced` 分支；关键文字全在 DOM，3D 不承担文本 |
| **R9** | **WebGL 上下文丢失 / 低配不支持 WebGL** | **P1** | L0 档直接回退现有 2D `render()`；上下文丢失期间按 `MAX_FRAME_DELTA` 限幅保护 CLK-S（§4.5 #6）；检测失败自动降级而非白屏 |
| **R10** | **importmap 官方写法待核实** [K-1]；且 `three/addons/*` 映射、模块 specifier 与现有 `?v=` 相对路径体系共存细节未验证 | **P2** | 列入 §10 与 phased P0 切片：先做**最小 importmap + 一个立方体**的技术验证切片，取到官方写法与浏览器实测后再扩面；不臆造代码 |
| **R11** | **并行方向稿 v2 与工程预研的口径漂移**（v2 的 M3/M5/M8 编号与本报告 M 编号不同） | **P2** | 本报告 M1–M9 为**工程侧独立编号**；不直连、由主理人中转对齐；v2 §0.6 已声明技术判断以 #14 为准 |
| **R12** | **参数源被 A/B 分组键污染（主理人 #14 补充 / v2 §3.4 + R1）**：`config.js:88-94` 的 `length` / `tone` / `color` 是**有意设计的 A/B 分组着色键、命名易误导**，字面值与语音学相反（`U09 /ʊ/` 标「长」、`U10 /uː/` 标「短」）[D-6]。若用于生成 3D 几何/材质/稀有度，**长短圆唇会整体做反**，并与 D1 三宝石语义冲突 | **P0** | ① **禁止**这三个字段进入任何几何/材质/粒子/教学参数；② **唯一权威源 = 另建经教研校验的发音特征表**（`sym` 索引、schema 显式排除三字段）；直接消费现有字段时最小允许集 `ipa` + `hint`；`label`/`unit` 仅作索引；③ 加最小对立一致性断言（脚本交 quality-lead）；④ **明确不修、不重命名** config.js 这些值——改了会破坏最小对立对 A/B 分组配色与 F5 / B7 门控断言；⑤ 详见 §5 M1 与 ADR-3 |

---

## §7 必须保留的现有硬约束清单（3D 轮逐条继承，不得突破）

> 以下为**发布边界与已验收资产**，任何 3D 实现方案都必须逐条通过。

1. **判定核心零改动**：`race.js` / `track.js` 的 `odo/lateral` + `g.line = startOdo + lineT·L` 确定性模型、`buildGates()`、`judge()`、`beginDecide()`、`hitsLane()`、两圈 `g.lap === lapNow` + `gate.id` 去重 [D-4]。
2. **2 圈 3 分钟**：`TUNING.laps=2`、follow 260 / listen 300、11 场 headless 最慢 174.57s ≤ 180s [D-4]。
3. **`TUNING` / `DIFFICULTY` 数值不动**；`DIFFICULTY.preview` 已由 #4 启用为 `D_preview = span·L + 0.5·preview·speed` [D-2][D-4]。
4. **IPA 唯一权威**：`window.IPA_DISPLAY`；`sym` 英式稳定键；**禁止 `displayIpa` 作键**（U05/U07 同为 `ɑ`）[D-4]。
5. **无字底版**：所有 IPA/中文/英文/数字由 DOM 层后期精确合成，**禁止 AI 直渲**；GLB 材质/参数化模型不含任何文字 [D-5][v2 §0.5.1]。
6. **防泄题单向铁律**：`correctLateral`/`spoken` 只出现在 `audio.playWord()` 与 `judge()`；3D 世界层扩展见 §4.6 [D-2][v2 §0.5.2]。
7. **跨站 localStorage**：单键 `ipa-quest-v1` 的 `rally` 嵌套对象、C08 合并逻辑、`RALLY_FOREIGN` 保真、**不新增字段** [D-3]。
8. **资产零改动**：29 张成稿 + 48 立绘 `U01–U48.webp` + 48 卡面 + `rarity_progress.webp` 原样保留 [D-5]；20 个图片 URL 零裸引用 [D-2]。
9. **缓存串治理**：`CACHE_TAG` 单一来源，新增 vendor 资源走 R-1 方案但不破坏 46 处产品字面量断言 [D-2]。
10. **右上角同位置角色切换**：`#route-map`（标题页）与比赛小地图（非标题页）互斥、不删不移、不新增第三层 [D-5]。
11. **可访问性分级**：`A11Y-TIER: Standard → Comprehensive`；三档 L2/L1/L0 降级只减特效不减信息与触控热区 [D-5]。
12. **四套门控 110 项判据基础**不得因渲染替换而失效 [D-4]。
13. **发布边界**：不部署、不上线、不 commit；真 3D 化在发布之后的下一轮 [D-5]。
14. **视觉方向「甲 · 立体书」**：世界层轻 3D / 平面层全 2D / 纸雾收敛 / 克制烫金；禁全屏 bloom、多光源硬高光 [D-5]。
15. **只读预研边界**：本轮（#14）除两个 md 外零产品文件改动、不装依赖、不跑构建、不引 CDN 运行时依赖。
16. **A/B 分组键不得作为参数源**：`config.js` 的 `length` / `tone` / `color` 是最小对立对 A/B 分组着色键、**不是语音学事实**（`U09 /ʊ/` 标「长」、`U10 /uː/` 标「短」）[D-6]；3D 几何/材质/稀有度/教学参数**一律不得消费**这三字段，只能取教研校验特征表或 `ipa` + `hint`；**不修、不重命名**这些值（会破 F5/B7 门控与 A/B 分组配色）。详见 §5 M1、§6 R12、ADR-3。
17. **持久化验收基线（#18 已落地）**：`.workbuddy/backups/` 是项目数据、不得删除/当缓存清理；`c07b-data-baseline.js` 锁当前已验收 `data.js`，`hud-20261109/` 是 **#4 之后**的回退点（**不能**回滚到 #4 前）。任何 `data.js` 变更须同步更新基线并重跑门控；详见 `design/baseline-rebuild-report.md`。

---

## §8 Phased 落地建议（垂直切片：最小成本验证「3D 版仍然好玩且仍能 3 分钟跑完」）

> 原则：**每个切片都可独立回滚到 2D**；先验证技术可行性，再验证玩法不变，最后才铺内容。判定核心在所有切片里零改动。

### P0 · 技术可行性切片（最小、零玩法风险）【建议 R-6】

- **做**：静态页里加 `importmap` + 本地 `three.module.js`，渲染**一个立方体 + 一个 `FogExp2` 雾**；取到官方 importmap 逐字写法 [K-1]；实测 375px 与低配的 WebGL 上下文创建成功率、首屏体积、帧时间。
- **验证**：`node js/headless_laps.mjs` 11 场仍 ALL PASS（证明判定未受影响）；四套门控仍 110/110（证明静态断言基础未破）；零外部 host 请求。
- **不做**：不改 `main.js` 主循环、不接 GLB、不引 Rapier。
- **Go/No-Go**：375px 实机 WebGL 可用率、首屏体积预算、门控全绿。

### P1 · 单区单圈视觉切片（验证「跟车视角还能看得清两条车道」）

- **做**：`render3d.js` 消费现有 `race.snapshot()`，只画 camp 区一段赛道 + 高追尾相机（v1.1 §B.1：3.4–3.8m / 16–20° 俯角 / 水平 FOV 60–66° / 临界阻尼）；HUD 保持现有 2D DOM 完全不动；`RENDER_MODE=2d|3d` 开关。
- **验证**：§4.5 的 6 条隔离断言全过；`mode==='quiz'` 冻结前后 `odo`/`simTime` 相等；三层预告 S0–S3 协同且不泄答案（M5）；**找 3–5 名目标年龄段用户试玩 30 秒，把主观眩晕评分作为 go/no-go**（v1.1 §I.2 明确这一步方向稿无法替代）[D-5]。
- **Go/No-Go**：两车道在 375px 可辨、无眩晕、判定逐位一致。

### P2 · 完整两圈玩法切片（验证「仍能 3 分钟跑完」）

- **做**：四区全赛道、两圈、`buildGates` 门位、路牌 S0–S3、小地图、quiz 冻结、结算全部在 3D 下跑一遍；接入 M5 三层预告。
- **验证**：11 场 headless 的 `finishTime` 与 2D 版**逐项一致**；110 项门控全绿；pageerror / console_error / requestfailed / bad_status 全 0；`RENDER_MODE=2d` 回退逐项一致。
- **Go/No-Go**：计时与答对率不退化 → 才可进入内容创新。

### P3 · 教学创新切片（一次只上一条，按教学价值排序）

- 顺序建议：**M1（发音→几何参数）→ M2（3D 口腔剖面）→ M3（声音可视化环境）→ M5（三层预告完善）→ M4（立体书转场）→ M6（收集立绘）→ M7/M8/M9（原创增强）**。
- 每条单独 A/B：能否让学生更快区分目标最小对立对（如 /i/ vs /ɪ/、/p/ vs /b/）；**答不上「让哪个教学难点变可见」的装饰一律砍掉**（v2 §0.3 防跑偏原则）。
- 每条上线前跑 §4.6 防泄题扫描 + 首屏/帧时间预算。

### P4 · 可选增强（默认关闭，按设备档位开）

- Rapier 视觉物理（车身悬挂 / 碰撞特效 / 道具）——**默认关闭**，仅 L2 档懒加载 [R2]。
- postprocessing（vignette / 轻 color grading）——**默认关闭**，方案甲禁全屏 bloom [R-3]。
- M8 声纹赛道需构建期烘焙脚本，单独评估。

---

## §9 需用户 / 主理人拍板的问题（本报告不拍板）

1. **技术路线**：是否采纳工程侧推荐的**路线 A · 原生 ESM 无构建**？还是选择路线 B 接受四套门控重写与构建链？
2. **Rapier 取舍**：是否接受 14.34 MiB 首屏代价启用视觉物理？还是默认关闭、仅 L2 档？
3. **缓存治理口径**：vendor 资源（`.mjs` / GLB / three / rapier）与现有 46 处 `?v=` 断言如何共存？是否同意 R-1 的「46 + N 各自唯一」升级（需 quality-lead 出新一轮 QA 规格）？
4. **3D 轮验收标准**：是否要求**110 项门控原样全绿**（路线 A 可满足）？还是允许重定义门控（路线 B 的必然结果）？
5. **three 版本钉定**：钉 0.186.1（与 Polyspoon pinned 一致）还是 0.187.0（npm latest，仍 `<0.188.0`）？
6. **Polyspoon 合规范围**：是否允许引入**社区模型**（需逐模型 provenance + explicit permission），还是**只用自写 recipe**（最安全）？
7. **听障视觉冗余**（v1.1 附录 3 已登记的独立议题）：3D 轮是否重开？它会改变「听音选车道」核心玩法口径，需用户 + 设计侧共同拍板。
8. **M9 回放日志持久化**：是否允许新增 localStorage 字段？工程侧建议会话级内存、不新增字段 [R-5]。

---

## §10 知识缺口与待核实项（绝不臆造）

| # | 缺口 | 现状 | 建议下一步 |
|---|---|---|---|
| **K-1** | three.js 官方 `<script type="importmap">` 逐字示例 | Installation manual 页本次抓取返回 `Redirecting...`，GitHub `manual/en/introduction/` 返回 404 → **NOT SHOWN** | 换 `threejs.org/docs/` / 官方 examples 源码 / jsDelivr `+esm` 文档取原文；P0 切片实测 |
| **K-2** | `three/addons/loaders/GLTFLoader.js` 的 Draco/meshopt 额外 decoder 需求 | 对应 manual 页同样 `Redirecting...` → **NOT SHOWN** | 查 `examples/jsm/loaders/GLTFLoader.js` 源码与 `exports` 映射 [F-24] |
| **K-3** | Polyspoon 各 GLB / `.mjs` 的**实测体积**与首屏请求数 | 官网只给 tris 数（158–2,912）[F-14]，`unpackedSize` 不适用 | P0/P1 切片实测 48 精灵与车体的 GLB 字节、draw call、内存 |
| **K-4** | 现有四套门控在「新增 vendor 资源」下的**精确断言改法** | 属 #5 / quality-lead 的规格范围，本轮不写 `verify_hud_spec.py`、不预设定数 | 由主理人转 quality-lead 出新一轮 QA 规格 |
| **K-5** | 375px 低配 WebGL 上下文成功率、纸雾 `FogExp2` 的实机帧时间 | 无实机数据 | P0 切片实测；沿用 #4 的 375×780 / 320×568 人工过眼流程 |
| **K-6** | `@dimforge/rapier3d-compat` 0.21.0 与 `@react-three/rapier` 2.2.0 所钉 0.19.2 的 API 差异 | 只查到版本号 [F-4][F-19]，未读 changelog | 若启用 Rapier，先读 0.19→0.21 migration；路线 A 直接用 0.21.0 可绕过 |
| **K-7** | 大脑/浏览器对 importmap + 现有 `?v=` 相对路径混用的缓存行为 | 【推断 I-4】已识别风险，未实测 | P0 切片抓 network 面板验证两套命名空间 |

---

## 附录 A · 查证 URL 全表（查证日期 2026-11-09）

| 编号 | URL | 查证到的事实 |
|---|---|---|
| F-1 | `https://raw.githubusercontent.com/pmndrs/drei/master/package.json` | peerDependencies（fiber ^9 / react ^19 / three >=0.159）、`three-stdlib ^2.35.6`、rollup build、license MIT |
| F-2 | `https://registry.npmjs.org/@react-three%2fdrei/latest` | 10.7.9 / `unpackedSize 1,753,692` / `fileCount 483` / MIT / 20+ deps / peerDeps |
| F-3 | `https://raw.githubusercontent.com/pmndrs/drei/master/LICENSE` | MIT, Copyright (c) 2020 react-spring |
| F-4 | `https://raw.githubusercontent.com/pmndrs/react-three-rapier/main/packages/react-three-rapier/package.json` | `@react-three/rapier 2.2.0` / peer fiber ^9.0.4, react ^19, three >=0.159.0 / dep `@dimforge/rapier3d-compat 0.19.2` |
| F-5 | `https://raw.githubusercontent.com/pmndrs/react-three-rapier/main/LICENSE` | MIT, Copyright (c) 2022 Poimandres |
| F-6 | `https://raw.githubusercontent.com/pmndrs/react-postprocessing/master/package.json` | 3.2.2 / MIT / peer fiber >=9.7.0, postprocessing ^6.36.0, react ^19, three >=0.156.0 / Vite build |
| F-7 | `https://raw.githubusercontent.com/pmndrs/react-postprocessing/master/LICENSE` | MIT, Copyright (c) 2020 react-spring |
| F-8 | `https://github.com/pmndrs/drei` | "useful helpers for @react-three/fiber"；"using the stand-alone `three-stdlib` instead of `three/examples/jsm`"；Controls/Gizmos/Abstractions/Shaders/Loading 分类 |
| F-9 | `https://github.com/pmndrs/react-three-rapier` | "wrapper library around the Rapier WASM-based physics engine… slot seamlessly into a react-three/fiber pipeline"；v2 支持 fiber v9 / react v19；`<Physics debug>` / RigidBody / colliders / joints / sensors / snapshots |
| F-10 | `https://github.com/pmndrs/react-postprocessing` | "postprocessing wrapper for @react-three/fiber"；基于独立 `postprocessing`；`<EffectComposer>` 示例；EffectPass 自动合并 / 单三角形 / WebGL2 MSAA |
| F-11 | `https://github.com/DITlieD/polyspoon` (README) | "open-source, AI-powered 3D asset community"；recipe = TypeScript program；输出 GLB/OBJ/FBX/USDZ + procedural/snapshot `.mjs` + source ZIP；`docs/licensing.md` / LICENSE (Apache-2.0) 位置 |
| F-12 | `https://raw.githubusercontent.com/DITlieD/polyspoon/main/docs/licensing.md` | 许可证分域全文：engine Apache-2.0、starter 7 项 CC0-1.0、`config.json` CC0 / TS+controls Apache-2.0、contributor 需 explicit permission + provenance、外部材质保留各自条款、pinned Three.js 0.186.1 (MIT) + TypeScript 7.0.2 (Apache-2.0)、每 archive 带 upstream notices / TS NOTICE / dependency-licenses.json |
| F-13 | `https://github.com/DITlieD/polyspoon/tree/main/LICENSES` | 目录仅 `Apache-2.0.txt` / `CC0-1.0.txt`；首次提交 2026-10-26 commit `89c7a1b` |
| F-14 | `https://polyspoon.com` | "The open-source alternative to Polyfork. Every model is a recipe"；141 published models / 2 contributors / 62 stars；tri 数 158–2,912；GLB/OBJ+MTL/FBX/USDZ；generator source Open, Apache-2.0；Works offline with your agent: Local toolkit |
| F-15 | `https://github.com/DITlieD/polyspoon` (Local toolkit details) | "needs no Polyspoon account, provider account, API key or inference service"；"This checkout is not an installable public npm package; use its checked-out sources and pinned dependencies" |
| F-16 | `https://github.com/DITlieD/polyspoon` ("Choose an output") | GLB 带 semantic parts/anchors/declared joint groups；Snapshot `.mjs` = async `createAsset()` 内嵌 GLB 非程序化；Procedural `.mjs` = **sync `createAsset(parameters)`** + metadata/types/cleanup/rigid-pose；Generator source ZIP = editable TS + pinned rebuild tooling；**"HTML bundle preview loads Three.js from jsDelivr and needs internet. Procedural modules need the pinned Three dependency supplied by the consumer"** |
| F-17 | `https://polyspoon.com/docs` | "Rigs and animation clips stay in the GLB; the other formats carry the static mesh"；`node .polyspoon/runtime.mjs build --family bench …` |
| F-18 | `https://raw.githubusercontent.com/dimforge/rapier/master/LICENSE` | Apache License 2.0, Copyright 2020 Sébastien Crozet |
| F-19 | `https://registry.npmjs.org/@dimforge%2frapier3d-compat/latest` | 0.21.0 / Apache-2.0 / `unpackedSize 15,038,573` / `fileCount 54` / `module dist/rapier.mjs` / description "Compatibility package with **inlined webassembly as base64**" / `sideEffects:false` |
| F-20 | `https://www.npmjs.com/package/@dimforge/rapier3d-compat` | 0.21.0 / 0 Dependencies / 128 Dependents / 129 Versions；"main build… **does not guarantee cross-platform determinism**"；"-compat versions… **embed the `.wasm` file into the `.js` sources encoded with base64**. This results in a **bigger package size**, but much wider bundler support" |
| F-21 | `https://raw.githubusercontent.com/pmndrs/postprocessing/main/LICENSE.md` | Zlib, Copyright © 2015 Raoul van Rüschen |
| F-22 | `https://registry.npmjs.org/postprocessing/latest` | 6.39.6 / Zlib / `unpackedSize 2,774,205` / `fileCount 9` / `type:module` / `module ./build/index.js` / **peer `three >= 0.168.0 < 0.188.0`** |
| F-23 | `https://github.com/pmndrs/postprocessing` | vanilla three 用法（EffectComposer/RenderPass/EffectPass/BloomEffect）；EffectPass 自动合并；单三角形全屏；效果清单；demo download ≈60 MB |
| F-24 | `https://registry.npmjs.org/three/latest` | 0.187.0 / MIT / `unpackedSize 21,030,536` / `fileCount 1277` / `type:module` / `module ./build/three.module.js` / `exports "./addons/*": "./examples/jsm/*"` |
| F-25 | `https://github.com/DITlieD/polyspoon` (About) | 仓库标题与 Vision 全文 |
| F-26 | `https://polyspoon.com/docs` | toolkit 下载包 `polyspoon-agent-4.zip`、agent 安装流程（2026-11 上旬仍活跃） |
| F-27 | `https://polyspoon.com` / `https://polyspoon.com/docs` | controls JSON（每 knob 的 range/default/unit/current value）、`llms.txt` / `prompt.txt` |
| F-28 | `https://github.com/pmndrs/react-postprocessing` (file list) | `vite.config.ts` / `pnpm-lock.yaml` / React 19 升级 / 3.2.2 (2026-10-21) |
| F-29 | `https://raw.githubusercontent.com/mrdoob/three.js/dev/LICENSE` | The MIT License, Copyright © 2010-2026 three.js authors |
| F-30 | `https://raw.githubusercontent.com/mrdoob/three.js/dev/README.md` | `import * as THREE from 'three'` 官方用法；WebGL/WebGPU renderers；jsDelivr badge |
| F-31 | `https://github.com/mrdoob/three.js` | `build/` 目录存在且 "Updated builds."(2026-11-06)；r187 (2026-10-30)；近期提交至 2026-11-08 |
| F-32 | `https://www.npmjs.com/package/@dimforge/rapier3d-compat` | 0 Dependencies / 129 Versions / 128 Dependents |

**本地源码事实（D 系）**：[D-1][D-2][D-3][D-4] = `design/hud-impl-plan.md` §0.0 / `design/hud-impl-report.md` / `design/hud-ux-spec.md` / `js/config.js` / 四套验收脚本（#3/#4 已核验）；[D-5] = `design/visual-direction-3d.md` v1.1 全文 + 用户拍板项；**[D-6] = `js/config.js:84-111` 本轮读码逐字核实的 `ph()` 定义与 A/B 分组键（`U09 /ʊ/` 标「长」、`U10 /uː/` 标「短」、`color` 由 `tone` 派生），并与 `design/visual-direction-3d-v2.md` §3.4 / R1 口径对齐（主理人 #14 补充）**；[D-7] = `design/baseline-rebuild-report.md`（#18 持久化基线重建）。

---

## 附录 B · 版本与体积速查（精确值，来自 npm registry `dist`）

| 包 | 版本 | license | unpackedSize (B) | ≈MiB | fileCount |
|---|---|---|---|---|---|
| `three` | 0.187.0 | MIT | 21,030,536 | 20.06 | 1,277 |
| `@dimforge/rapier3d-compat` | 0.21.0 | Apache-2.0 | 15,038,573 | 14.34 | 54 |
| `postprocessing` | 6.39.6 | Zlib | 2,774,205 | 2.65 | 9 |
| `@react-three/drei` | 10.7.9 | MIT | 1,753,692 | 1.67 | 483 |
| `@react-three/postprocessing` | 3.2.2 | MIT | NOT SHOWN | — | — |
| `@react-three/rapier` | 2.2.0 | MIT | NOT SHOWN | — | — |

> ⚠️ 再次强调 §2.2.1：`unpackedSize` 是整包解包体积，**不是浏览器加载量**。three 20.06 MiB 含 1277 个文件（examples/src/docs），浏览器只取 `build/three.module.js` + 少量 addons；rapier compat 14.34 MiB 几乎全是必须加载的 base64 WASM。

---

*文档版本 v1.0 · engineering-lead（程基岩）· Task #14 / CSEG-3D-T · 只读技术预研，唯一写入物为本文件与 `design/3d-adr.md`；未改任何产品文件 / 图片 / 脚本，未装依赖、未跑构建、未引 CDN 运行时依赖、未部署 / 未上线 / 未 commit。*
