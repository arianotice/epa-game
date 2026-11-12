# 《声音拉力赛》P1 社区模型合规与逐模型 Provenance 台账（P1 Community Assets v1.0）

> **文档性质**：落实用户 **D2「允许引入社区模型」** 的**合规格与台账**，与 `p1-3d-art-spec.md` 并列。本文定义「一个社区模型要进仓，必须先满足什么」，并给出**逐模型 provenance 台账 schema、候选来源清单、sha256 校验方式、引入 SOP、合规红线**。
> **一句话结论**：**「允许」不等于「必须」；P1 默认用 `p1-3d-art-spec.md` 的 three 基础几何组合，社区模型是可选升级、完全不阻塞工程。截至本轮，台账实际状态 = 0 个模型进仓、0 个取得 explicit permission。** 本文是**规格与空台账**，不是采购清单、不是授权证明。
> **只读边界**：除本文件外**禁止修改任何文件**。**不下载、不 vendor、不替换任何二进制资产进仓**（本轮零模型落地）。不部署、不上线、不 commit。
> **上游依据（精确交叉引用）**：`design/kart-visibility-diagnosis.md` §3 D2 裁决（「需逐模型 provenance + explicit permission 校验；ADR-3 / ADR-5 需补合规流程」）、`design/3d-tech-feasibility.md` §2.3 Polyspoon 专项 + F-11~F-16 事实表 + §R4 合规风险、`design/3d-adr.md` ADR-3B 裁决 6 / §119「不设临时放行」+ ADR-3 §402、`design/visual-direction-3d-v2.md` §3.5/§3.6（GLB vs `.mjs` / 生成消费分离 / 参数源硬约束）、`js/probe.jsx`（P0 不引 GLB / Polyspoon / CDN）、`js/config.js`（`sym` 稳定键 / `length·tone·color` 数据陷阱）、`package.json`（pinned 依赖矩阵）。
> **并行分工**：合规事实以 engineering-lead #14 预研（已查证）为准；门控断言以 quality-lead #31 为准；玩法口径以 design-strategist #29 为准。产出经主理人中转，不与其他成员直连。

---

## §0 结论先行 + 六条硬规则（不可越界）

| # | 硬规则 | 来源 |
|---|---|---|
| **H1** | **「允许」≠「必须」**：D2 只是解除「禁止引入」，不产生「必须引入」的义务。P1 主形态 = 程序化几何（`p1-3d-art-spec.md` §3），社区模型为**可选升级、不阻塞工程** | D2 / Task #30 |
| **H2** | **未取得 explicit permission 的模型一律不进仓**。任何模型缺少作者/贡献者的**显式授权证据 + provenance / license scope 记录**，即视为不可用 | `3d-tech-feasibility.md` F-12 / `3d-adr.md` R4 |
| **H3** | **逐模型 provenance 台账**：每个进仓模型必须有 §2 定义的全字段记录；**一个模型一行，不得整包笼统声明** | D2 / ADR-3B 裁决 6 |
| **H4** | **本轮零模型落地**：除本文（规格）外不改任何文件、不下载任何二进制资产、不新增任何资源引用 | Task #30 / 本轮只读 |
| **H5** | **许可证合规不设「临时放行」**：任一 vendor 包缺 notices / provenance 即**整体回退该包**（不是「先上后补」） | `3d-adr.md` §119 / §439 |
| **H6** | **生成 / 消费分离 + 零 CDN 运行时**：procedural `.mjs` 只在离线 / 构建期跑、产物为带锚点 GLB；Polyspoon HTML 预览包（从 jsDelivr 加载 three、需联网）**绝不能当产品资源**；上线前跑「零外部 host 请求」断言 | v2 §3.6 / F-16 / R6 |

> **给 `engineering-lead #28` 的一句话**：现在就可以按 `p1-3d-art-spec.md` 建 3D 卡丁车 + 2 NPC + 跟车赛道，**不需要等任何社区模型、不需要任何下载、不需要联网**。本文的台账是「将来若要升级外观时先过的门」，不是 P1 的前置条件。

---

## §1 D2 裁决与边界（逐字登记，不推断）

`kart-visibility-diagnosis.md` §3：

> D2 | **「允许引入社区模型」** | 对应 `3d-tech-feasibility.md` §9-6 Polyspoon 合规范围 | ✅ 允许社区模型 | **需逐模型 provenance + explicit permission 校验；ADR-3 / ADR-5 需补合规流程**

- **D2 解除了什么**：原 ADR-3 的保守口径「只用自写 recipe / 明确 CC0 来源，不把社区模型默认当可自由商用」不再作为**禁止线**；社区模型**可以**被引入。
- **D2 没有解除什么**（这些仍是硬约束）：
  1. 社区模型**不自动获得 CC0 或 project-authored 声明**（F-12）；每个模型有独立 licence 与 review record（F-14）。
  2. contributor recipe / preset / 私有编辑配置需 **"Obtain a contributor's explicit permission and record provenance/license scope before approving distribution"**（F-12 逐字），且需在 `docs/contributing/source-packages.json` 的 recipe ID 下加声明，缺失或不支持的声明会被拒。
  3. **外部贴图 / 网格 / 字体 / 材质保留各自条款**："Generated outputs that incorporate external textures, meshes, fonts or other material retain those materials' terms"（F-12）。
  4. 每 archive 随附 **upstream license texts / TypeScript's NOTICE / `dependency-licenses.json`**（F-12）。
- **D3 连带约束**：用户「确保是听音选车道」= 核心玩法硬约束。任何社区模型 / 贴花 **不得成为看字 / 看口型选车道的泄题通道**（与 `p1-3d-art-spec.md` C3 防泄题一致）；无字底版（v1.1 §0.5）对社区模型同样生效——**含 baked-in 文字 / 字母 / IPA / 数字的模型一律不进仓**。
- **D6 连带**：用户已拍板「3D 成为主形态设终点」，社区模型若引入，其 2D 降级等价物仍按 `p1-3d-art-spec.md` §6.6 的三阶段 / 终点收敛处理，不因引入第三方模型而单独延长 2D 保留期。

---

## §2 逐模型 Provenance 台账 schema（H3，一个模型一行）

> 台账文件建议落点：`音标拉力赛/design/community-assets-manifest.json`（**本轮不创建**，仅定义 schema），与 `p1-3d-art-spec.md` §0.4 的 `VENDOR_TAG` / `vendor.manifest.json` 口径对齐（见 §10）。每一行 = 一个**具体模型 / 具体版本 / 具体下载产物**，不是「一个网站」「一个素材包」。

| 字段 | 类型 | 必填 | 说明 / 判据 |
|---|---|---|---|
| `model_id` | string | ✅ | 项目内唯一 id，命名沿用 v1.1 §0.3 前缀：`kart-* / prop-* / zone-* / spirit-* / decal-* / sky-*` |
| `source_url` | string | ✅ | **canonical 原始 URL**（模型详情页，非搜索页 / 非 CDN 临时链接），须可回溯 |
| `source_commit` | string | 建议 | 上游 commit / 版本号 / 发布日期，锁定「具体版本」 |
| `author` | string | ✅ | 作者 / 贡献者署名原文 |
| `license_id` | enum | ✅ | `CC0-1.0 / CC-BY-4.0 / CC-BY-SA / MIT / Apache-2.0 / 自定义 / 不明确`（见 §5 判定表） |
| `license_url` | string | ✅ | 该**模型**的许可证原文或声明页 URL（**不是**网站通用 ToS） |
| `commercial_ok` | bool | ✅ | 是否允许商用。**教学产品发布前必须明确**；不明确 = false |
| `redistribute_ok` | bool | ✅ | 是否允许再分发 / 随站打包。不明确 = false |
| `attribution_required` | bool | ✅ | 是否需署名；若 true，`attribution_text` 必填并进 `LICENSES/` 与 UI 致谢位 |
| `attribution_text` | string | 条件 | 署名原文（作者 / 作品名 / 许可证 / 链接 / 是否改编） |
| `explicit_permission` | object | ✅ | **H2 核心**：`{ obtained: bool, evidence_url, evidence_date, scope_note, reviewer }`。`obtained=false` → **整行不得进仓** |
| `explicit_permission.evidence_url` | string | ✅ | 作者明确授权的证据（issue / 邮件存档 / license 声明 / `source-packages.json` 记录），可回溯 |
| `provenance_scope` | string | ✅ | provenance / license scope 记录（F-12 逐字要求），说明该产物覆盖哪些部件、是否含外部材质 |
| `external_materials` | array | ✅ | 模型内嵌的贴图 / 网格 / 字体 / 材质清单及其各自条款（F-12「保留各自条款」）；空数组须显式写 `[]` |
| `local_path` | string | ✅ | 本地落点（§3 目录结构），含文件名与扩展名 |
| `format` | enum | ✅ | `GLB / .mjs(procedural) / .mjs(snapshot) / source-ZIP / WebP`（见 §4 形态取舍） |
| `sha256` | string | ✅ | 下载产物的 sha256 十六进制（§4 校验方式），**进仓前 + 上线后各验一次** |
| `byte_size` | int | ✅ | 字节数（配合 sha256 与 magic 复核，防 Caddy 200 兜底，见 §4.3） |
| `content_type` | string | ✅ | 期望 `Content-Type`（**不得为 `text/html`**）；GLB=`model/gltf-binary`、WebP=`image/webp` |
| `notices_attached` | array | ✅ | 随包 notices 清单：`LICENSES/` 原文 / TS NOTICE / `dependency-licenses.json` / 各外部材质许可证 |
| `review_record` | object | ✅ | `{ visual_review: bool, a11y_review: bool, leak_review: bool, reviewer, date }`——造型过审（与 2D 立绘并排）、可访问性冗余、防泄题三检 |
| `cache_tag` | string | ✅ | 该资源引用的 `VENDOR_TAG`（§10），不得复用源码层 `hud-20261108` |
| `used_in` | array | ✅ | 用在哪个部件 / 场景（如 `kart-player-body`），便于按台账**逐个下线**（ADR-3B §115） |
| `status` | enum | ✅ | `candidate（候选，未核验） / pending（待授权） / approved（已授权可进仓） / vendored（已进仓） / retired（已下线）` |

**硬判定**：`status` 从 `pending` → `approved` 的充分必要条件 = `explicit_permission.obtained===true` **且** `commercial_ok` / `redistribute_ok` / `license_id` / `license_url` / `sha256` / `notices_attached` **全部齐备**。**任一字段缺失或不明确 → 保持 `pending`，该模型不进仓（H2/H5）**。

---

## §3 本地落点与目录结构（【建议值】，本轮不创建）

> 与 `3d-adr.md` ADR-3B「产物层 `VENDOR_TAG` + `vendor.manifest.json`」及 `3d-tech-feasibility.md` §2.3 I-3「vendor `.mjs` / GLB 用相对路径 + `?v=`」对齐。P1 主形态（纯几何）**不产生这些目录**；仅当某个社区模型 `approved` 后才按此落点安放。

```
音标拉力赛/
└─ assets/vendor/community/                 # 社区模型统一根（与自写 recipe 的 polyspoon/ 分开）
   ├─ LICENSES/                            # 逐许可证原文（Apache-2.0.txt / CC0-1.0.txt / CC-BY / MIT ...）
   │   ├─ NOTICE                          # TS NOTICE 等上游 NOTICE（F-12）
   │   └─ dependency-licenses.json        # pinned 依赖许可证清单（F-12 / ADR-3B 裁决 6）
   ├─ models/                             # 运行时消费的 GLB（H6：产物，非生成器）
   │   └─ {model_id}.glb
   ├─ decals/                             # 贴花 / WebP（若含，需过无字底版检查）
   ├─ provenance/                         # 逐模型授权证据存档（邮件 / issue 截图 / 声明副本）
   │   └─ {model_id}.md
   └─ community-assets-manifest.json       # §2 schema 的台账实例（本轮 = 空 / 仅 candidate 行）
```

- **生成器不进站**：procedural `.mjs` / Generator source ZIP 属**离线 / 构建期**产物（v2 §3.5 / §3.6、F-16），放站外工具目录，不进 `assets/vendor/community/`；**站里只放生成好的 GLB 快照**。
- **HTML 预览包禁入**：Polyspoon HTML bundle preview 从 jsDelivr 加载 three、需联网（F-16），**绝不放进任何产品目录**（H6 / R6）。
- **命名**：`local_path` 用 snake_case `model_id`，与 v1.1 §0.3 前缀一致；禁止含空格 / 中文 / 版本号以外的特殊字符。

---

## §4 sha256 校验方式与资源形态取舍

### 4.1 下载 → 校验 → 登记流程（每个模型必走）

1. 从 `source_url` 取**具体版本**产物，记录 `source_commit` / 发布日期。
2. 计算 sha256（命令见 §4.2），与上游**公布的 checksum**（若有）比对；无公布值则在台账 `provenance_scope` 记「上游未公布 checksum，以本站首次下载值锁定」。
3. 记录 `byte_size` + 文件 magic（GLB 头 4 字节 `glTF`、WebP 头 `RIFF....WEBP`）+ `Content-Type`。
4. 校验产物**不含任何 baked-in 文字 / 字母 / IPA / 数字**（无字底版 C4 / D3 防泄题），含则退回。
5. 把许可证原文 / TS NOTICE / `dependency-licenses.json` / 外部材质条款收进 `LICENSES/`。
6. 填 §2 全字段，`explicit_permission.obtained=true` 且证据可回溯 → `status=approved` → 才可 `vendored`。
7. 上线后**再验一次**（§4.3 Caddy 兜底陷阱），不符即整体回退该包（H5）。

### 4.2 sha256 命令（跨平台）

```bash
# Git Bash / macOS / Linux
sha256sum assets/vendor/community/models/{model_id}.glb
# 只取哈希值： sha256sum file | cut -d' ' -f1
# 校验： echo "<expected>  <file>" | sha256sum -c -
```

```powershell
# Windows PowerShell
(Get-FileHash -Algorithm SHA256 "assets\vendor\community\models\{model_id}.glb").Hash
# 比对： (Get-FileHash ...).Hash -eq "<EXPECTED_UPPERCASE>"
```

> 台账 `sha256` 统一存**小写 64 位十六进制**；PowerShell `Get-FileHash` 返回大写，登记时 `.ToLower()` 归一。GLB 为二进制，校验前**不做任何转码 / 换行转换**（`sha256sum` 直接对二进制流）。

### 4.3 Caddy 200 兜底陷阱（必须防，来自 `kart-visibility-diagnosis.md` C6）

线上 Caddy 对不存在路径**兜底返回 200 + 首页 HTML**（曾导致「拉力赛 index.html 返回 3076 B 大闯关首页」）。因此**不信状态码**，资源送达必须按：

```
逐字节复核(sha256 一致)  ∧  byte_size 一致  ∧  magic 头一致  ∧  Content-Type 非 text/html
```

四项全过才算送达成功；任一不过即判该资源未送达、按 H5 整体回退。这条对**社区模型 / GLB / 贴花**尤其重要（二进制被替换成 HTML 时体积与 magic 都会露馅）。

### 4.4 GLB vs `.mjs` 形态取舍（v2 §3.5 / F-16 精确）

| 形态 | 是否可进站 | 用途 | 台账 `format` |
|---|---|---|---|
| **GLB**（含 semantic parts / anchors / declared joint groups，保留 rig + clips） | ✅ **运行时交付主形态** | 卡丁车 / 精灵 / 地标 / 闸门，带语义部件便于按部位换材质（六档稀有度 / LOD） | `GLB` |
| Snapshot `.mjs`（异步 `createAsset()`、内嵌 GLB、非程序化） | ⚠️ 一般不进站 | 单个资产轻量分发 / 版本锁定；大批量时内嵌 GLB 体积膨胀 | `.mjs(snapshot)` |
| Procedural `.mjs`（同步 `createAsset(parameters)` + metadata/types/cleanup/rigid-pose） | ❌ **不进运行时站** | **离线 / 构建期**批量生成 48 变体 / A/B 试造型，产出 GLB 后进站 | `.mjs(procedural)`（站外） |
| Generator source ZIP（可编辑 TS + pinned rebuild tooling） | ❌ 不进运行时站 | 美术侧维护参数 schema，站外工具链 | `source-ZIP`（站外） |
| **HTML bundle preview** | ❌ **严禁**（F-16 jsDelivr / 需联网） | 仅本地预览，绝不当产品资源 | — |

**H6 落地**：procedural `.mjs` 需要消费方提供 **pinned `three 0.186.1`**（F-16「Procedural modules need the pinned Three dependency supplied by the consumer」），与 `package.json` 已钉矩阵一致；但按生成/消费分离，**运行时只读 GLB、零额外联网 / 零额外构建依赖**。HTML 预览包不得作为交付物或验收依据（v2 §3.6 / R2）。

---

## §5 许可证分域与判定表（合规判定的依据）

### 5.1 Polyspoon 精确许可证分域（F-11/F-12/F-13，逐字，`3d-tech-feasibility.md` §2.3④）

> `LICENSES/` 目录实际只有两个文件：`Apache-2.0.txt`、`CC0-1.0.txt`（F-13）；首次提交 2026-10-26 commit `89c7a1b`（F-13）。社区规模查证时点：141 published models / 62 stars / 2 contributors，tri 158–2,912（F-14）。

| 对象 | 许可证 | 再分发条件 | 对本项目判定 |
|---|---|---|---|
| 原始 generator 实现 / runtime / authoring 工具 / control schemas | **Apache-2.0** | 保留 LICENSE、NOTICE、修改声明；不得覆盖既有第三方 notices | 用 toolkit 需随包 notices |
| 指定 starter 预设（work-lantern / cottage / tree / fence / crate / boulder / bench）的**原始生成几何 / 材质** | **CC0-1.0** | `config.json` 是明确指定的 CC0 内容文件；**TypeScript 代码与 `controls.json` 仍是 Apache-2.0** | 这 7 项几何可 CC0 用，但**代码层仍 Apache-2.0**，须分别记录 |
| 新建 contributor recipe / preset / 私有编辑配置 | **不自动获得 CC0 或 project-authored 声明** | **需 explicit permission + provenance / license scope 记录**；在 `docs/contributing/source-packages.json` 的 recipe ID 下加声明，缺失或不支持会被拒 | **H2 直接命中**：这类模型必须逐模型授权 |
| 外部贴图 / 网格 / 字体 / 材质 | 保留各自条款 | 生成物含外部材质则保留其条款 | `external_materials` 字段逐项记 |
| pinned 依赖 | **Three.js 0.186.1 (MIT)** + **TypeScript 7.0.2 (Apache-2.0)** | 每 archive 带 upstream license texts / TS NOTICE / `dependency-licenses.json` | `notices_attached` 必含 |
| Unity fixtures / 编辑器模板 / 第三方资产 / 研究文档截图 | **排除**在 blanket declaration 之外 | — | 不纳入本项目 |

### 5.2 通用许可证判定表（供 `license_id` 填空时对照）

| license_id | 商用 | 再分发 | 署名 | 关键附加义务 | 默认可得? |
|---|---|---|---|---|---|
| `CC0-1.0` | ✅ | ✅ | ❌ | 无（但仍建议记 provenance） | **仅明确标注 CC0 的产物**；社区模型不自动 CC0 |
| `CC-BY-4.0` | ✅ | ✅ | ✅ | 署名 + 许可证链接 + 注明改编 | 需读模型页声明 |
| `CC-BY-SA` | ✅ | ✅ | ✅ | **相同方式共享**（可能污染衍生作品） | ⚠️ 教学产品慎用，须法务确认 |
| `MIT` | ✅ | ✅ | ✅ | 保留版权 + 许可声明 | 多为**代码 / 引擎**，非模型 |
| `Apache-2.0` | ✅ | ✅ | ✅ | 保留 LICENSE / NOTICE / 修改声明 | 多为 **generator / toolkit / TS 代码** |
| `自定义 / 不明确` | ❓ | ❓ | ❓ | — | **一律 `commercial_ok=false / redistribute_ok=false`，保持 pending（H2）** |

> **诚实声明**：本轮为**只读规格**，除 F-11~F-16（主理人已查证、见 `3d-tech-feasibility.md`）外，**未对任何候选来源做新增联网核验**。下表 §6 的 URL / 许可状态均为「待核验候选」，**不构成授权证明，也不代表该来源当前仍可访问或其许可证未变**。真正 `approved` 必须由工程 / 法务在引入时按 §2 逐字段复核并留 `explicit_permission` 证据。

---

## §6 候选来源清单（candidate，逐来源登记；**当前 0 个 approved / 0 个进仓**）

> 用途：给后续「若要升级外观」一个**已按 §2 schema 预填、待核验**的候选池。每行都标 `status=candidate`、 `explicit_permission.obtained=false`。**这不是下载清单，不触发任何下载动作。**

| # | 来源 | canonical URL（待核验） | 许可（待核验） | 商用/再分发/署名 | explicit_permission | 备注 / 风险 |
|---|---|---|---|---|---|---|
| C-1 | **Polyspoon · engine / toolkit / 自写 recipe** | `https://github.com/DITlieD/polyspoon` [F-11] | generator/toolkit/recipe = **Apache-2.0** [F-12] | 商用✅ / 再分发✅ / 需保留 LICENSE+NOTICE | `obtained=false`（自写 recipe 可走内部声明，不属「社区模型」） | **最安全**：自写 recipe 只需保留 notices；是 v2 §3.6 参数化精灵的推荐底座，但**依赖 pinned three + 离线生成** |
| C-2 | **Polyspoon · 7 个 starter 预设几何** | `https://github.com/DITlieD/polyspoon` [F-13] | 原始几何/材质 = **CC0-1.0**（`config.json`）；TS/controls = Apache-2.0 [F-12] | 几何✅ / 代码需 Apache 义务 | `obtained=false` | work-lantern / cottage / tree / fence / crate / boulder / bench；**几何与代码许可不同，须分开记** |
| C-3 | **Polyspoon · 社区 contributor 模型** | `https://polyspoon.com` [F-14] | **逐模型独立 licence + review record** [F-14] | **不明确 = false** | `obtained=false`（**必须逐模型要 explicit permission**） | **D2 主要对象，也是 H2 主要风险**：141 模型不自动 CC0；须在 `source-packages.json` recipe ID 下加声明 [F-12] |
| C-4 | **Kenney**（游戏素材，常见 CC0） | `https://kenney.nl/assets`（待核验） | 通常 **CC0-1.0**（**待核对该具体包声明**） | 待核验 | `obtained=false` | low-poly 风格契合方案甲；但**须逐包确认 CC0 声明 URL**，不可凭「Kenney=CC0」的印象 |
| C-5 | **Sketchfab · CC0 筛选** | `https://sketchfab.com/search?...&licenses=...`（待核验） | 逐模型 `CC0` / `CC-BY`（**待核验**） | 逐模型不同 | `obtained=false` | 即便标 CC0 也须留作者 + 模型页 URL + 下载产物 sha256；CC-BY 需署名位 |
| C-6 | **three.js examples 示例资产** | `https://github.com/mrdoob/three.js/tree/dev/examples` [F-24/F-30] | 示例资产**各自条款**（多为特定许可，**待核验**）；three 本体 = **MIT** [F-24] | 待核验 | `obtained=false` | 项目已钉 `three 0.186.1`（MIT）；但**示例模型 ≠ three 本体 MIT**，不得混用许可 |
| C-7 | **three.js 本体 / addons（代码，非模型）** | `https://github.com/mrdoob/three.js` [F-30] | **MIT** [F-24] | 商用✅ / 需保留版权声明 | `obtained=false`（已在 `package.json` 依赖，非「引入模型」） | 仅登记说明：代码依赖不是社区模型，走 `dependency-licenses.json` 而非本台账模型行 |

**逐一提示**：
- C-1/C-2/C-7 严格说**不是「社区模型」**（自写 / 引擎 / 代码），列在此仅为说明「P1 更可能走的路」，其合规负担远小于 C-3/C-4/C-5/C-6。
- C-3/C-4/C-5/C-6 任一要 `approved`，**必须先补 §2 全字段 + explicit permission 证据 + §4 校验**，否则按 H2 保持 `pending`。
- **D2 允许的是 C-3 这类「社区模型」**，但 H1 明确它不阻塞 P1；P1 三车用 `p1-3d-art-spec.md` §3 的基础几何即可全部满足。

---

## §7 当前台账状态（本轮结论）

| 项 | 状态 |
|---|---|
| `approved` 模型数 | **0** |
| `vendored`（已进仓）模型数 | **0** |
| 取得 `explicit_permission` 的模型数 | **0** |
| 本轮下载 / vendor 的二进制资产 | **0**（H4，只读） |
| 本轮新增资源引用 / `VENDOR_TAG` 改动 | **0**（P1 主形态纯几何，`p1-3d-art-spec.md` §0.4） |
| 台账文件 `community-assets-manifest.json` | **本轮不创建**（仅定义 schema；候选行见 §6） |

**逐模型模板行（供将来 `approved` 时复制，当前全为占位）**：

```json
{
  "model_id": "kart-player-body-<slug>",
  "source_url": "<canonical model page>",
  "source_commit": "<commit / version / date>",
  "author": "<verbatim>",
  "license_id": "CC0-1.0 | CC-BY-4.0 | MIT | Apache-2.0 | 自定义 | 不明确",
  "license_url": "<model-specific license page>",
  "commercial_ok": false,
  "redistribute_ok": false,
  "attribution_required": false,
  "attribution_text": "",
  "explicit_permission": {
    "obtained": false, "evidence_url": "", "evidence_date": "",
    "scope_note": "", "reviewer": ""
  },
  "provenance_scope": "",
  "external_materials": [],
  "local_path": "assets/vendor/community/models/<model_id>.glb",
  "format": "GLB",
  "sha256": "<lowercase 64 hex>",
  "byte_size": 0,
  "content_type": "model/gltf-binary",
  "notices_attached": ["LICENSES/", "NOTICE", "dependency-licenses.json"],
  "review_record": {
    "visual_review": false, "a11y_review": false, "leak_review": false,
    "reviewer": "", "date": ""
  },
  "cache_tag": "<VENDOR_TAG>",
  "used_in": [],
  "status": "candidate"
}
```

> **默认全 false / 空 = 有意设计**：`obtained=false` 时该行**永远不进仓**（H2）。把模板的 `commercial_ok / redistribute_ok` 默认设为 `false`，是为了让「不明确」不被误当成「允许」。

---

## §8 引入一个新社区模型的标准作业流程（SOP，【建议值】）

> 只有当用户 / 主理人明确要求「升级某个具体外观」时才启动。P1 默认不启动。

1. **需求登记**：写明要替换/补充哪个部件（`used_in`）、为什么程序化几何不够（教学 / 造型理由），经主理人确认（H1：不是「允许了就该用」）。
2. **来源核验**：取 canonical `source_url` + 具体版本 `source_commit`；核对该**模型**（非站点通用）的 `license_id` / `license_url`。
3. **许可证判定**：按 §5.2 填 `commercial_ok / redistribute_ok / attribution_required`；任一「不明确」= false → 若无法满足则**停在 pending**。
4. **explicit permission**：对 contributor recipe / 非 CC0 模型，取得作者明确授权，留 `evidence_url` + `evidence_date` + `scope_note`；Polyspoon contributor 需在 `source-packages.json` recipe ID 下加声明（F-12）。
5. **外部材质清点**：填 `external_materials[]`，逐项记各自条款（F-12「保留各自条款」）。
6. **下载校验**：§4.1 全流程 + §4.2 sha256 + §4.3 magic/Content-Type；**无字底版检查**（C4 / D3）。
7. **notices 归档**：`LICENSES/` 原文 + TS NOTICE + `dependency-licenses.json` + 署名文本（若需）。
8. **三检过审**（`review_record`）：① `visual_review` 与 2D 立绘并排过审、对齐 `p1-3d-art-spec.md` §5 六维阈值与方案甲（禁写实 PBR / 污渍 / 糖果色）；② `a11y_review` 形状/明度冗余（不靠红绿）；③ `leak_review` 无 baked-in 文字、无泄题几何（C3）。
9. **台账定稿**：`status → approved → vendored`，填 `local_path` / `sha256` / `byte_size` / `cache_tag`。
10. **门控与上线复核**：跑 §10 门控；上线后按 §4.3 再验一次送达；**移除时按台账逐个下线、不改源码层 46 处 tag**（ADR-3B §115）。

**任一环失败 → 按 H5 整体回退该包，不设「临时放行 / 先上后补」。**

---

## §9 合规红线与整体回退（H5，逐字引用 ADR-3B）

- `3d-adr.md` ADR-3B 裁决 6：**「P1 引入任何 vendor 包须随附 `LICENSES/` 原文、TS NOTICE、`dependency-licenses.json` 与逐模型 provenance 台账」**。
- `3d-adr.md` §119 / §439：**「许可证合规问题不设『临时放行』：任一 vendor 包缺 notices / provenance 即整体回退该包」**。
- `3d-adr.md` §115：**「移除 P1 的 vendor 包时按 provenance 台账逐个下线，不改动源码层 46 处 tag」**。
- `3d-tech-feasibility.md` R4：**「只用自写 recipe（Apache-2.0，需保留 notices）或明确 CC0/已授权来源；不把社区模型默认当可商用；建立逐模型 provenance 台账」**。
- **CDN / 离线破口**（R6 / F-16）：产品页只 vendor `.mjs` / GLB，**明确排除 HTML 预览包**；上线前跑「零外部 host 请求」断言（复用四套门控的 `requestfailed` / `bad_status` 计数口径）。
- **缓存治理**（R3 / I-4 / ADR-3B）：社区模型 / vendor 资源引入独立 `VENDOR_TAG`（现产物层 `p0-20261109` 是 P0 值，P1 若引入须新开），**不得塞进现有 46 处 `hud-20261108` 字面量**；门控升级为「46 + N 各自唯一」，**不得把 46 与 N 相加判合计唯一**（ADR-3B §97 BC-3 修正）。`.mjs` 内部 `import "three"` 走 importmap 不带 `?v=` 的双命名空间问题（I-4）在生成/消费分离下不成立（运行时不加载 `.mjs`）。

---

## §10 与 QA #31 门控 / engineering-lead #28 的对接项（列需求，不写脚本）

| # | 门控 / 接口需求 | 归属 | 本文给的输入 |
|---|---|---|---|
| B1 | 「本轮 0 社区模型进仓」静态断言：`assets/vendor/community/` 不存在或为空、无新增 GLB / `.mjs` 文件 | quality-lead #31 | §7 状态表 / H4 |
| B2 | 「零外部 host 请求」断言（jsDelivr / 任何 CDN 不出现在产品资源） | quality-lead #31 | H6 / R6 / F-16 |
| B3 | 若将来引入：逐行 provenance 全字段齐备 + `explicit_permission.obtained===true` 才可 `vendored` | quality-lead #31 | §2 硬判定 / §8 SOP |
| B4 | 若将来引入：sha256 + byte_size + magic + `Content-Type≠text/html` 送达复核（防 Caddy 兜底 200） | quality-lead #31 | §4.3 / `kart-visibility-diagnosis.md` C6 |
| B5 | 若将来引入：`VENDOR_TAG` 独立 + 「46 + N 各自唯一」，两层扫描根物理隔离 | quality-lead #31 + ADR-3B | §9 / ADR-3B §96-97 |
| B6 | 防泄题：渲染层 / 模型内零 `spoken/correctLateral/qType/hit`，零 baked-in 文字 | quality-lead #31 + #29 | C3 / `p1-3d-art-spec.md` §6.7 / §4.1 step4 |
| B7 | P1 主形态用程序化几何即可跑通，不依赖任何社区模型 | engineering-lead #28 | H1 / `p1-3d-art-spec.md` §3 |
| B8 | 若采用 Polyspoon 参数化生成：procedural `.mjs` 只在离线/构建期、产物 GLB、需 pinned `three 0.186.1` | engineering-lead #28 | §4.4 / v2 §3.6 / F-16 / `package.json` |

---

## §11 风险与缓解

| # | 风险 | 缓解 |
|---|---|---|
| RC1 | **把「允许」误读成「必须引入」**，为等社区模型阻塞 P1 | H1 + §0 给工程的一句话 + B7；P1 纯几何起步 |
| RC2 | **社区模型不自动 CC0**，误当可自由商用导致发布侵权 | §5.1 F-12 分域 + H2 explicit permission + §2 台账 |
| RC3 | **contributor recipe 缺 provenance / license scope 声明**被上游拒 | §8 step4（F-12 `source-packages.json` 声明） |
| RC4 | **外部材质保留各自条款**被忽略，生成物带未授权贴图/字体 | §2 `external_materials[]` + §8 step5 |
| RC5 | **HTML 预览包 / CDN 破坏离线可用**（教室弱网） | H6 / §4.4 明确排除 / B2 零外部 host 断言 |
| RC6 | **Caddy 200 兜底把 HTML 当 GLB 送达** | §4.3 逐字节 + sha256 + magic + Content-Type 四重复核 |
| RC7 | **缓存治理被打破**（46 处 tag / 双命名空间） | §9 / B5 / 生成消费分离（运行时不加载 `.mjs`） |
| RC8 | **模型含 baked-in 文字 / 泄题几何**，破坏无字底版与听音选车道 | §4.1 step4 / §8 step8 `leak_review` / B6 |
| RC9 | **许可证「先上后补」** | H5 + §9「整体回退、不设临时放行」 |
| RC10 | **许可证状态随时间变化**（候选来源 URL / 条款变动） | §5.2 诚实声明 + `source_commit` 锁版本 + 引入时重新核验，不以本轮规格当授权证明 |

---

## 附：需用户 / 主理人 / 法务确认的问题（本文不擅自决定）

1. **【P1】是否真的要在 P1 引入任何社区模型**——H1 建议「不引入」，P1 纯几何即可满足「点开始就看得见 3D 车」。若用户只是想「允许将来用」，本台账保持空即可。
2. **【P1】explicit permission 的证据标准**：邮件存档 / issue 回复 / `source-packages.json` 声明，哪种算数？由主理人 + 法务定（本文只要求「可回溯」）。
3. **【P2】若引入 CC-BY / CC-BY-SA 模型**，署名位放哪（UI 致谢 / `LICENSES/`）、SA 是否污染衍生作品——需法务确认，本文对 `CC-BY-SA` 标 ⚠️ 慎用。
4. **【P2】`VENDOR_TAG` 具体值与 N 计数口径**：P1 若引入资源，须由 quality-lead #31 出新一轮计数规格（ADR-3B / R3），本文不定死。
5. **【P2】D6 终点与社区模型的 2D 降级等价物**：按 `p1-3d-art-spec.md` §6.6 三阶段同步处理，终点判据归 #29 / #31。
6. **【P3】Polyspoon 参数化精灵是否进入首批**：v2 §3.8 的许可证 / API 稳定性 / 离线可用性 / 锚点保留率复核项，交 #14 预研顺带核对（本文不越权）。

---

*文档版本 v1.0（D2 社区模型合规 · 逐模型 provenance 台账规格）· 美术方向 林绘澄（art-director）· Task #30 · 与 `p1-3d-art-spec.md` 并列，与 v1.1 / v2 方向稿并列，均未改动 · 本轮只读，仅写入本文件与 `p1-3d-art-spec.md`，未改任何产品代码 / 图片 / 脚本，**未下载任何二进制资产、0 模型进仓**，未部署、未上线、未 commit。*
