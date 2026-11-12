# P1 · D4 改档对 48 张资产的只读影响面评估（P1 Sprite Re-audit Impact v1.0）

> **文档性质**：**只读评估**，是「D4 资产重出另立一轮」开工前给用户的**具体代价依据**，不是重出方案、不是执行清单、不替用户拍板。
> **用户裁决（已下，不再论证）**：D4 资产 = **先落教研表，48 张卡面 / 立绘 / 六档总图重出另立一轮**；教研分档**认可现版**（`CI = A + B + 2C`、新分布 `14/12/9/6/4/3`、UR = `ɜː / θ / ð`）。本评估是「看到供下一轮直接开工」才被保留的输入文档。
> **本轮铁律**：**零重出、零改动**。未改任何资产 / 脚本 / 产品代码 / 已上线图鉴 / `rarity-map.json`；未下载、未跑生成管线、未部署、未上线、未 commit。除本文件外零写入。
> **评估对象**：`design/p1-gameplay-spec.md` §2.9 的 D4 改档（36/48 改档、SAMPLES 6/6 全变、48 立绘 prompt 内嵌旧档光环）。
> **上游依据（逐字核对，非推测）**：`design/p1-gameplay-spec.md` §2.3/§2.8/§2.9、`design/kart-visibility-diagnosis.md` §3 D4、`音标大闯关/sprite_gen/`（`manifest.json` / `image_profiles.py` / `gen_sprites.py` / `compose_cards.py` / `convert_webp.py` / `unkey_white.py`）、`音标大闯关/js/data.js` / `js/atlas.js`、`音标拉力赛/js/cards.js` / `js/main.js`、`design/3d-adr.md` ADR-3B、`design/p1-community-assets.md` §4.3。
> **产出经主理人中转，不与其他成员直连。**

---

## §0 结论先行（给用户的一句话）

**D4 改档的资产代价不是「改 36 个文字标签」，而是「36 张 AI 立绘必须整张重出 + 48 张卡面全量重合成 + 1 张六档总图重出 + 4 份档位数据源同步 + 缓存串 bump + 已上线图鉴原子替换」**；原因是稀有度**同时**被写进了 ① AI 生图 prompt 的光环（`image_profiles.py:30-37/130`）并 baked 进立绘像素，② 卡面边框/徽章/中文名（`compose_cards.py:27-34/47-66`），③ 六档总图的分组与数量（`compose_cards.py:141-211`），④ 运行时 DOM（`cards.js` / `data.js` / `atlas.js`）。**「只重出卡面文字层、立绘不动」会留下 36 处肉眼可见的档位自相矛盾**（§5 给逐张清单与用户可见位置），其中 4 张跨 ≥3 档最刺眼。

四个最关键的实测事实（下文逐条给证据）：

| # | 事实 | 影响 |
|---|---|---|
| F1 | 立绘光环是 **AI 生图时内嵌的像素**，不是后期文字层 —— `image_profiles.py:130` 把 `RARITY_AURA[rar]` 拼进 `prompt`，`manifest.json` 每条 `prompt` 与 `prompts/U*.txt` 48 个文件都带旧档光环 | 卡面重出**改不了**光环 → 折中方案必然不一致 |
| F2 | **已上线卡面** `assets/sprites/cards/U01.webp` 与 `sprite_gen/webp_american/U01.webp` **字节完全一致**（19244 B / 同 sha256），`rarity_progress.webp` 亦然（91442 B / 同 sha256）→ 线上来自**美式重出版** `cards_american/` | 但 `convert_webp.py:7` 的 `CARD` 仍硬编码 `sprite_gen/cards`（英式基线）→ **重出前必须先厘清管线错位，否则会重出到错误的一套** |
| F3 | 档位有 **4 份数据源**：`sprite_gen/manifest.json`（48 条）、`音标大闯关/js/data.js`（`phonemes[]` 48 条）、`音标拉力赛/js/cards.js`（`CARDS` 48 条）、以及 §2.9 拟建的 `rarity-map.json`（当前**不存在**） | 只改 1 份 → 图鉴 DOM 徽章与卡面图打架；`rarity-map.json` 是新建而非既有文件 |
| F4 | 缓存串 `?v=hud-20261108` 在 `index.html` / `atlas.js` / `main.js` 等共 **46 处**（ADR-3B 实测），两站同源部署、Caddy 对不存在路径兜底 200 返回首页 | 重出后必须 bump + 逐字节 / magic / sha256 / `Content-Type≠text/html` 四重复核（§4.3） |

---

## §1 逐文件清单（路径 + 张数 + 体积；区分卡面 / 立绘 / 六档总图 / webp 产物）

> 全部为**只读 `ls` / `os.path.getsize` / `sha256` 实测**（2026-11-10 本轮），未打开改写任何图片。体积为磁盘字节数。路径相对 `C:\Users\86135\WorkBuddy\英语音标播客`。

### 1.1 已上线正式资产（`音标大闯关/assets/`，用户当前能看到）

| 类别 | 路径 | 张数 | 体积（B） | 体积（KiB） | 档位耦合 |
|---|---|---:|---:|---:|---|
| **立绘**（含 baked 光环） | `音标大闯关/assets/sprites/U01.webp … U48.webp` | **48** | 3,112,774 | 3,039.8 | ✅ 光环颜色 / 星数 = 旧档 |
| **六档总图** | `音标大闯关/assets/sprites/rarity_progress.webp` | **1** | 91,442 | 89.3 | ✅ 六档分组 / 数量 / 代表立绘 = 旧档 |
| — 小计 | `音标大闯关/assets/sprites/`（一级，含上两项） | 49 | 3,204,216 | 3,129.1 | — |
| **卡面**（图鉴大图 / 车库存图） | `音标大闯关/assets/sprites/cards/U01.webp … U48.webp` | **48** | 999,580 | 976.2 | ✅ 边框色 / 徽章 / 中文名 = 旧档 |
| **与档位无关的成稿** | `音标大闯关/assets/img/`（`a1/a2/a3/f/cover` + `b02–b25` 共 29 webp + `favicon.png`） | 30 | 8,580 KiB（目录） | — | ❌ 不受 D4 影响 |

### 1.2 生成链中间产物（`音标大闯关/sprite_gen/`，未上线但重出必经）

| 类别 | 路径 | 张数 | 体积（B） | 体积（KiB） | 角色 |
|---|---|---:|---:|---:|---|
| **AI 原始白底图** | `sprite_gen/raw/U*.png` | 48 | 38,916,419 | 38,004.3 | `gen_sprites.py` 输出；重出**最先**被覆盖 |
| raw 附属 | `sprite_gen/raw/last_batch.json`、`sample`、`test_u01` | 3 | — | — | 批次记录 / 调试残留 |
| **透明立绘 PNG** | `sprite_gen/sprites/U*.png` | 48 | 23,090,677 | 22,549.5 | `unkey_white.py` 去白底输出 → 上游 |
| **卡面·英式基线** | `sprite_gen/cards/U*.png` (48) + `rarity_progress.png` + `sample_overview.png` | 50 | 5,167,318 | 5,046.2 | `convert_webp.py:7` **当前 CARD 指向此处**（但线上不来自此，见 F2） |
| **卡面·美式重出** | `sprite_gen/cards_american/U*.png` (48) + `rarity_progress.png` | 49 | 4,749,389 | 4,638.1 | `compose_cards.py:17` 的 `OUT`；**线上 webp 的真正来源** |
| **webp·美式产物** | `sprite_gen/webp_american/U*.webp` (48) + `rarity_progress.webp` | 49 | 1,091,022 | 1,065.5 | 与 1.1 已上线卡面 / 总图**字节一致**（实测 U01 + 总图） |
| **prompt 文本** | `sprite_gen/prompts/U01.txt … U48.txt` | 48 | 41,020 | 40.1 | 每条含旧档光环描述；`gen_sprites.py:30` 只读 `manifest.json`，**不读这些 txt** |
| 去白底脚本 | `sprite_gen/unkey_white.py` | 1 | — | — | 依赖 `scipy.ndimage` flood-fill |
| 辅助数据 | `sprite_gen/phoneme_pure.json` / `phoneme_words.json` | 2 | — | — | **不含 `rarity`**（实测 grep=0）→ 无需同步 |

### 1.3 档位数据源与消费代码（非图片，但决定用户可见层）

| 路径 | 内容 | 实测 | 消费方 |
|---|---|---|---|
| `音标大闯关/sprite_gen/manifest.json` | 48 条，每条 `rarity` + 内嵌光环的 `prompt`；54,364 B | 分布 `P5/SR17/SAR10/HR8/SSR4/UR4` | `compose_cards.py`、`gen_sprites.py` |
| `音标大闯关/js/data.js` | `window.IPA_DATA.phonemes[]` = **48 条**，顶层各 1 个 `rarity`；174,527 B / 7,684 行 | 全文件 `rarity` 字面量 **96 处** | `atlas.js`、`image_profiles.py:92-95` |
| `音标拉力赛/js/cards.js` | `CARDS` 48 条含 `rarity` + `cost`；`RARITY_RANK` 6 档 | 分布同旧档 | `main.js:961` |
| `音标大闯关/js/atlas.js` | `RARITY_ORDER` / `RARITY_CN`、`:103` DOM 徽章、`:177` 按 `p.rarity` 分组、`:174` 引用总图 | 13,300 B | 已上线图鉴页 |
| `音标拉力赛/js/main.js` | `:966` 引用 `cards/${id}.webp`、`:969` 渲染 `${card.rarity}` 文字 | — | 已上线车库 / 商店 |
| `rarity-map.json` | **当前不存在**（`find` 全仓 0 命中） | — | §2.9 拟建，本轮不动 |

> ⚠️ **`data.js` 的 96 处需澄清**：JSON 解析确认 `phonemes[]` 恰 **48 条**、每条顶层 1 个 `rarity`（权威源，分布 `5/17/10/8/4/4`）；另 48 处 `rarity` 字面量集中在文件后半段（约 5,909–7,632 行，成对出现，如 U45 条目），疑为 `levels[]` / 课程数据内的音素副本。**下一轮重出前必须由 engineering-lead 确认这 48 处是否需同步改档**；若漏改，图鉴六档分组与关卡页可能显示两套档位。本轮只读，不做判定。

### 1.4 关键单文件 sha256 基线（供回滚比对；下表为**前 16 位截断展示**，完整值可复算）

| 文件 | 字节 | sha256（前 16） |
|---|---:|---|
| `assets/sprites/rarity_progress.webp` | 91,442 | `76161bf3b5fd9fe8` |
| `assets/sprites/cards/U01.webp` | 19,244 | `5fb52dc2d22bb984` |
| `assets/sprites/U01.webp` | 64,670 | `c27427191d2c709b` |
| `sprite_gen/manifest.json` | 54,364 | `fdcc4b6ce86a8727` |
| `sprite_gen/image_profiles.py` | 8,679 | `075705d8921c58ef` |
| `sprite_gen/compose_cards.py` | 10,538 | `bbb0bfee7467f6ee` |
| `sprite_gen/gen_sprites.py` | 6,266 | `73ab4ada539797c2` |
| `sprite_gen/convert_webp.py` | 900 | `8d169939b2ac8983` |
| `js/data.js` | 174,527 | `25784ee12bd0f637` |
| `js/atlas.js` | 13,300 | `433e8d0ad75f4c7a` |

**目录级聚合指纹**（算法：该目录内按字典序拼接「文件名 + 文件字节流」后取 sha256，前 20 位；用于一键判断「重出后哪些目录变了」）：

```
assets/sprites/              49 文件  77165bffb251a8d0c0e5…
assets/sprites/cards/        48 文件  1998f5f01dd4d110cef2…
sprite_gen/sprites/          48 文件  a87383a1ff1981abd511…
sprite_gen/cards_american/   49 文件  725757500bbef117bd64…
sprite_gen/webp_american/    49 文件  f0058210287644ee04fa…
sprite_gen/prompts/          48 文件  c70f65697b19e35f2315…
```

复算命令（只读，本轮已执行）：`sha256sum <file>` / `Get-FileHash -Algorithm SHA256 <file>`；完整逐文件清单可由 `find … -exec sha256sum` 导出，本轮**不导出、不落盘**。另有 #33 已钉的「改动前 sha256 基线 + 全量快照」（`.workbuddy/backups/`）可作二级回滚源。

---

## §2 D4 改档的精确影响面（36/48 + SAMPLES 6/6）

### 2.1 新旧档位对照（脚本比对 `p1-gameplay-spec.md` §2.8 新表 vs `manifest.json` 旧表）

- 旧分布 `P5 / SR17 / SAR10 / HR8 / SSR4 / UR4` → 新分布 **`P14 / SR12 / SAR9 / HR6 / SSR4 / UR3`**（与用户认可的 `14/12/9/6/4/3` 一致）。
- **改档 36 张、未改档 12 张**：`U03 U05 U06 U12 U15 U28 U29 U30 U32 U34 U40 U46`。
- 迁移分组（旧 → 新）：

| 迁移 | 张数 | unit |
|---|---:|---|
| `SR → P` | 10 | U21 U22 U23 U24 U25 U26 U27 U31 U39 U43 |
| `P → SR` | 3 | U01 U02 U04 |
| `SAR → SR` | 3 | U13 U14 U35 |
| `SR → SAR` | 3 | U07 U09 U10 |
| `SAR → HR` | 3 | U16 U36 U42 |
| `HR → SSR` | 3 | U18 U19 U20 |
| `HR → SAR` | 2 | U45 U48 |
| `HR → SR` | 1 | U17 |
| `HR → P` | 1 | U47 |
| `SAR → UR` | 1 | U11 |
| `SAR → P` | 1 | U44 |
| `SSR → HR` | 1 | U38 |
| `SSR → SAR` | 1 | U37 |
| `SSR → SR` | 1 | U33 |
| `UR → HR` | 1 | U41 |
| `UR → SAR` | 1 | U08 |

- **跨 ≥3 档（视觉落差最大）4 张**：`U08 UR→SAR`（棱镜彩虹/5星 → 琥珀/2星）、`U11 SAR→UR`（琥珀/2星 → 棱镜彩虹/5星）、`U33 SSR→SR`、`U47 HR→P`。

### 2.2 六档光环定义（`image_profiles.py:30-37`，旧档 baked 进像素）

| 档 | 旧光环 prompt 关键词 | 立绘可见特征 |
|---|---|---|
| P | `soft cool silver-blue light aura, plain and simple, no stars` | 银蓝素光 / 无星 |
| SR | `emerald green glowing aura with one small star sparkle` | 翡翠绿 / 1 星 |
| SAR | `golden amber glowing aura with two small star sparkles` | 琥珀 / 2 星 |
| HR | `bold ruby-red radiant aura with three small star sparkles` | 宝石红 / 3 星 |
| SSR | `royal purple magical aura with a small crown halo and four small star sparkles` | 皇家紫 + 皇冠 / 4 星 |
| UR | `intense prismatic rainbow radiant aura with a radiant crown and five small star sparkles` | 棱镜彩虹 + 皇冠 / 5 星 |

`prompts/U01.txt` 实测含 `silver-blue light aura, plain and simple, no stars`；`manifest.json` 的 `U01.prompt` 同句 → **48 条 prompt / 48 个 txt 全部内嵌旧档光环，无一例外**。

### 2.3 SAMPLES 6/6 全变（比「改档」更严重的一层）

`gen_sprites.py:21` 硬编码 `SAMPLES = {"P":"U01","SR":"U21","SAR":"U13","HR":"U17","SSR":"U33","UR":"U41"}`，用途是 `--samples` **每档出 1 张**给风格确认。D4 后这 6 个 unit 的新档为：

| 样板 unit | 旧档（原用途） | 新档 | 结果 |
|---|---|---|---|
| U01 | P | **SR** | 不再是 P 样板 |
| U21 | SR | **P** | 不再是 SR 样板 |
| U13 | SAR | **SR** | 不再是 SAR 样板 |
| U17 | HR | **SR** | 不再是 HR 样板 |
| U33 | SSR | **SR** | 不再是 SSR 样板 |
| U41 | UR | **HR** | 不再是 UR 样板 |

**6/6 全部脱离原档**，且新档只覆盖 `P / SR / HR` **3 档**，`SAR / SSR / UR` 三档**无样板可用**。因此下一轮除重出外，还须**重选 6 个 unit** 才能让 `python gen_sprites.py --samples` 仍产出「每档 1 张」。建议从新分布里各挑 1 张（如 `P→U03`、`SR→U05`、`SAR→U15`、`HR→U36`、`SSR→U34`、`UR→U29`，均为未改档或新档成员，具体由设计侧确认），并同步改 `gen_sprites.py:21` 与 `compose_cards.py:218` 的默认 overview unit 列表（`U01,U21,U13,U17,U33,U41`）。

### 2.4 依赖脚本与责任链（下一轮改动点，本轮零改动）

| 脚本 | 当前行为 | D4 后需做什么 |
|---|---|---|
| `image_profiles.py` | `:122` 从 `data.js` 读 `p["rarity"]` → `:130` `RARITY_AURA[rar]` 拼进 prompt → `:139` 写 `manifest.json` + 48 txt | 档位来源须切到新教研表 / `rarity-map.json`；**若继续读 `data.js` 旧 `rarity`，重出仍是旧光环** |
| `manifest.json` | 48 条 `rarity` + `prompt` | 36 条 `rarity` 与 **48 条 `prompt`（光环文本）** 需重生成；`prompts/*.txt` 48 个随之 |
| `gen_sprites.py` | `:21` SAMPLES、`:30` `prompt_of=mf[u]["prompt"]`、`:97` 断点续传（**`raw/U*.png` 已存在即跳过**） | 重选 SAMPLES；重出必须 `--force` 或先清 `raw/`，否则 36 张被 `skip (cached)` 跳过、光环不变 |
| `unkey_white.py` | `raw/*.png` → `sprites/*.png` 透明立绘 | 36 张重跑去白底 |
| `compose_cards.py` | `:27-34` `RAR_META` 六档边框/徽章/中文名、`:48` `draw_card` 用 `m["rarity"]`、`:141-211` `make_progress()` 按 `m["rarity"]` 分组 + 数量 + 前 3 代表立绘、`:17` `OUT=cards_american` | 全量 48 张卡面重合成 + 1 张六档总图重出；`cards/` 英式基线是否同步由主理人定 |
| `convert_webp.py` | `:6-8` `SPR=sprite_gen/sprites`、`CARD=sprite_gen/cards`（**英式基线**）、`OUT=assets/sprites`；`:25` 从 `CARD` 读总图 | **F2 管线错位**：线上 webp 实测来自 `webp_american`（美式），此脚本若原样重跑会**把英式基线覆盖上线**。下一轮须先统一 `CARD`/产物链 |
| `compose_cards.py:16` 注释 | 「旧 `cards/` 的 49 张英式基线保持原样不动，待主理人验收后原子替换」 | 说明项目**已存在并行两套产物**的历史状态，重出前须先定哪套是权威 |
| `rarity-map.json` | 不存在 | §2.9 拟建；本轮不动 |

---

## §3 需重出资产总数与工作量

### 3.1 全量重出（口径 A：让所有层一致，推荐给下一轮做预算）

| 层 | 数量 | 动作 | 是否需 AI 生图 |
|---|---:|---|---|
| **AI 立绘** | **36 张**（改档者） | 新光环 prompt → `gen_sprites.py --force` → `raw/` → `unkey_white.py` → `sprites/` | ✅ 是（最贵） |
| 未改档立绘 | 12 张 | 光环不变，**可不动**；但 `manifest.json` 的 `prompt` 若整体重写会全量重生成 | ⚠️ 视实现口径 |
| **卡面** | **48 张**（全量重合成最稳妥） | `compose_cards.py all` → `cards_american/` → webp → `assets/sprites/cards/` | ❌ 纯 Pillow 合成 |
| **六档总图** | **1 张** | `compose_cards.py progress` → `rarity_progress.webp` | ❌ 纯 Pillow 合成 |
| **prompt 文本** | **48 个 txt** | `image_profiles.py make_prompts()` 重写 | ❌ |
| **档位数据源** | **4 份** | `manifest.json` / `data.js`（含待澄清的后 48 处）/ `cards.js` / 新建 `rarity-map.json` | ❌ |
| **SAMPLES** | **2 处** | `gen_sprites.py:21` + `compose_cards.py:218` 默认 overview 列表 | ❌ |
| **缓存串** | **46 处** | `?v=hud-20261108` → 新 TAG（ADR-3B：源码层 46 处须各自唯一，不删不混算） | ❌ |
| 合计（图片） | **85 张** = 36 立绘 + 48 卡面 + 1 总图；含中间产物则 **≈ 289 个文件**（raw 36 + sprites 36 + cards 48 + webp 48 + prompts 48 + 总图 3 套 + …） | | |

> **口径 B（最小）**：若只重出 36 张改档卡面 + 1 张总图 + 36 张立绘，未改档的 12 张卡面 / 12 张立绘保持旧文件 → 图片合计 **73 张**。但 `compose_cards.py` / `convert_webp.py` 是**全量循环**（`for u in mf` / `glob U*.png`），实际重跑会覆盖全部 48 张，口径 B 需额外加过滤逻辑，**建议按口径 A 做预算**。

### 3.2 工作量与风险（给用户的代价依据）

| 项 | 估计 / 风险 |
|---|---|
| AI 生图 36 张 | `gen_sprites.py:38` 全局节流 `min_gap=8s`、默认 `--workers 3`、429 退避 15/30/60/90/120s → **理想 ≈ 96s，实际含限流重试可能 10–40 分钟 + API 费用**；需 `AGNES_API_KEY`（`:130`） |
| **重出不可复现** | Agnes 文生图**非确定性**：即使 `PROFILES[u]` 形象锚点不变，36 张精灵的**脸型 / 姿态 / 配色会漂移**，与用户已收集、已看惯的 12 张旧立绘**风格断裂**。这不是「改个光环」，是整张换图 |
| 去白底 | `unkey_white.py` 依赖 `scipy.ndimage` flood-fill；浅色精灵（米白/奶油）靠「边缘连通近白区域」判定，新光环颜色改变（如 UR 棱镜彩虹 → SAR 琥珀）可能改变连通域 → **36 张需逐张目视验透明边缘** |
| 卡面 / 总图重合成 | 纯本地 Pillow，秒级；但依赖 `C:/Windows/Fonts/` 的 `ARIALUNI.TTF` / `msyhbd.ttc`（`compose_cards.py:20-25`）→ **仅 Windows 可跑**，换机器需补字体 |
| 六档总图版式 | `make_progress()` 按 `per[t][:3]` 取每档**前 3 只**立绘 + `len(per[t])` 数量 + `desc` 固定文案（`:200`，如 P「基础音·易解锁」、UR「神话音·最稀有」）；新分布 `14/12/9/6/4/3` 会让**六档代表立绘与数量全部变化**，`desc` 文案也需按新教研口径重写 |
| 缓存 / 部署 | 46 处 tag bump 牵动 4 套门控（`S17/F8a/S1.7` 等）与 headless；两站须同源部署；Caddy 200 兜底须四重复核（`p1-community-assets.md` §4.3） |
| 验收 | 需 48 立绘并排过审（v2 §3.7 一致性护栏）、色弱安全（不靠红绿）、无字底版（光环不含文字）、24px 剪影可辨、六档总图版式无溢出 |

---

## §4 与已上线图鉴卡面的兼容与回滚方式

### 4.1 已上线图鉴的四个可见位置（用户当前实际看到）

| 位置 | 代码 | 显示内容 | 档位来源 |
|---|---|---|---|
| 大闯关 `#/atlas/rarity` 六档分组 | `atlas.js:177-200` | 每档徽章 + 中文名 + `got/总数` + 每格立绘缩略图 | `data.js` 的 `p.rarity`（DOM） |
| 大闯关稀有度进阶总图 | `atlas.js:174` | `rarity_progress.webp` 整图 | 烘焙在图片里 |
| 大闯关 `#/atlas/cards` 卡片 + 弹窗 | `atlas.js:103`、`:138-141` | `rar-badge rar-{档}` DOM 徽章；`cards/${unit}.webp` 大图；锁定态遮罩写「稀有度 X」 | DOM 用 `data.js`，大图用烘焙图 |
| 拉力赛车库 / 商店「音标卡」 | `main.js:961-970` | `cards/${id}.webp` 缩略图 + **DOM 文字 `${card.rarity} · 已解锁`** | 图用烘焙图，文字用 `cards.js` |

> **兼容难点**：档位在**同一屏内并存于 DOM 与烘焙图两层**。若只改 `data.js` / `cards.js`（DOM）而不重出图片，图鉴会出现「DOM 徽章写 SR 绿、卡面大图边框仍是 P 银蓝」的直接矛盾；反之只重出图片不改 DOM，同样矛盾。**必须两层同步，或整体不动。**

### 4.2 建议的兼容路径（下一轮执行，本轮不动）

1. **先落教研表**：按用户裁决，先把 `CI=A+B+2C` / `14/12/9/6/4/3` / UR=`ɜː θ ð` 落成唯一权威（§2.9 的 `rarity-map.json` 或等价物），并明确 **4 份数据源的同步顺序**（`data.js` / `cards.js` / `manifest.json` / 新表），避免多源漂移。
2. **产物隔离，不覆盖线上**：参照 `compose_cards.py:16` 已有的先例（「旧 `cards/` 保持原样，待主理人验收后原子替换」）——重出产物写入**新目录**（如 `sprite_gen/cards_rarity_v2/`、`webp_rarity_v2/`），`assets/sprites/` 与 `assets/sprites/cards/` **保持原样**直到验收通过。
3. **原子替换 + 双轨校验**：验收通过后一次性替换 48 卡面 + 1 总图 + 36 立绘，并同步 4 份数据源、SAMPLES、46 处缓存串；部署后按 `p1-community-assets.md` §4.3 做「sha256 + byte_size + magic 头 + `Content-Type≠text/html`」四重复核（防 Caddy 兜底把首页 HTML 当图片送达）。
4. **两站同源**：`音标大闯关`（已上线）与 `音标拉力赛` 共享 `localStorage['ipa-quest-v1']` 与 `?v=` 资源，须同级部署到同一 origin，否则图鉴卡面 / 车库存图出现裂图。

### 4.3 回滚方式（三级）

| 级别 | 手段 | 依据 |
|---|---|---|
| L1 · 文件级 | 用 §1.4 的**逐文件 / 目录聚合 sha256 基线**比对，把变更文件按清单逐个还原；#33 已钉「改动前 sha256 基线 + 全量快照」（`.workbuddy/backups/`）作二级源 | 本评估 §1.4 / #33 |
| L2 · 目录级 | 保留旧 `assets/sprites/`、`assets/sprites/cards/`、`sprite_gen/cards_american/`、`webp_american/` 为回滚目录，替换前先整目录快照；按 ADR-3B「逐资源按 provenance / 清单下线、不改源码层 46 处 tag」 | `3d-adr.md` §115 |
| L3 · 缓存级 | 缓存串改回 `hud-20261108` 需**整批 46 处统一**，不可只改部分；若已 bump，回滚须同步 4 套门控的 TAG 常量与 headless | ADR-3B §96-97 / R3 |

> **零风险前提**：本轮**未改任何资产**，因此当前线上状态即为**天然回滚点**；用户可据此从容决定下一轮范围。

---

## §5 折中方案「只重出卡面文字层、立绘不动」的具体视觉不一致

> 这是本次评估最需要用户看清的一节。**结论：折中不可行**，因为立绘光环是 baked 像素（F1），卡面「文字层」改不动它。以下给出**哪几档、哪几张、用户在哪可见**。

### 5.1 不一致的三类（逐层）

| # | 不一致 | 机理 | 波及 |
|---|---|---|---|
| V1 | **同一张卡内**：立绘光环 = 旧档，卡面边框 / 徽章 / 中文名 = 新档 | `compose_cards.py:48` 用 `m["rarity"]` 画边框徽章；立绘是 `sprites/Uxx.png` 原样合成上去（`:85-92`），光环不随卡面变 | **36 张改档卡面**（12 张未改档一致） |
| V2 | **六档总图 vs 六档分组**：总图内仍是旧分组 / 旧数量 / 旧代表立绘，`atlas.js:177` 的 DOM 分组已是新档 | 总图是单张烘焙 PNG；若「只重出卡面文字层」不含总图，则总图与 DOM 分组两套数字 | **1 张总图 + 整个 `#/atlas/rarity` 页** |
| V3 | **DOM 徽章 vs 卡面大图**：`atlas.js:103` / `main.js:969` 若同步新档，`cards/*.webp` 边框仍是旧色 | 两层档位来源不同（DOM 读 `data.js`/`cards.js`，图读烘焙 PNG） | 图鉴卡片、锁定遮罩「稀有度 X」、车库「音标卡」列表 |
| V4 | **立绘本体在别处单独出现时**：`atlas.js:96` / `:138` 直接用 `assets/sprites/${unit}.webp`（**不带卡面**），旧光环**单独可见** | 图鉴 tile、六档分组每格、学习页都用裸立绘 | 大闯关图鉴 tile ×48、六档分组格 ×48 |

### 5.2 逐张冲突清单（36 张，立绘旧光环 → 卡面新档应配光环）

| unit | 立绘仍是（旧） | 卡面/徽章将是（新） | 用户可见矛盾 |
|---|---|---|---|
| U01 | 银蓝素光 / 无星 (P) | 翡翠绿 / 1星 (SR) | 微笑小姐：素光立绘装在绿框「稀有」卡里 |
| U02 | 银蓝素光 / 无星 (P) | 翡翠绿 / 1星 (SR) | 同上 |
| U04 | 银蓝素光 / 无星 (P) | 翡翠绿 / 1星 (SR) | 同上 |
| U07 | 翡翠绿 / 1星 (SR) | 琥珀 / 2星 (SAR) | 星数少 1 |
| **U08** | **棱镜彩虹 + 皇冠 / 5星 (UR)** | **琥珀 / 2星 (SAR)** | **跨 3 档：最华丽的彩虹立绘配「超凡」卡，落差最大** |
| U09 | 翡翠绿 / 1星 (SR) | 琥珀 / 2星 (SAR) | 星数少 1 |
| U10 | 翡翠绿 / 1星 (SR) | 琥珀 / 2星 (SAR) | 吹蜡烛 /uː/ 立绘星数少 1 |
| **U11** | **琥珀 / 2星 (SAR)** | **棱镜彩虹 + 皇冠 / 5星 (UR)** | **跨 3 档：新 UR 档「神话」却顶着朴素琥珀光环**（且 U11=ɜː 是用户认可的 UR 之一） |
| U13 | 琥珀 / 2星 (SAR) | 翡翠绿 / 1星 (SR) | 降档光环反而更华丽 |
| U14 | 琥珀 / 2星 (SAR) | 翡翠绿 / 1星 (SR) | 同上 |
| U16 | 琥珀 / 2星 (SAR) | 宝石红 / 3星 (HR) | 星数少 1 |
| U17 | 宝石红 / 3星 (HR) | 翡翠绿 / 1星 (SR) | 光环过华丽 |
| U18 | 宝石红 / 3星 (HR) | 皇家紫 + 皇冠 / 4星 (SSR) | 缺皇冠 |
| U19 | 宝石红 / 3星 (HR) | 皇家紫 + 皇冠 / 4星 (SSR) | 缺皇冠 |
| U20 | 宝石红 / 3星 (HR) | 皇家紫 + 皇冠 / 4星 (SSR) | 缺皇冠 |
| U21 | 翡翠绿 / 1星 (SR) | 银蓝素光 / 无星 (P) | /p/ 清音：绿光立绘配「普通」灰卡 |
| U22 | 翡翠绿 / 1星 (SR) | 银蓝素光 / 无星 (P) | 同上 |
| U23 | 翡翠绿 / 1星 (SR) | 银蓝素光 / 无星 (P) | 同上 |
| U24 | 翡翠绿 / 1星 (SR) | 银蓝素光 / 无星 (P) | 同上 |
| U25 | 翡翠绿 / 1星 (SR) | 银蓝素光 / 无星 (P) | 同上 |
| U26 | 翡翠绿 / 1星 (SR) | 银蓝素光 / 无星 (P) | 同上 |
| U27 | 翡翠绿 / 1星 (SR) | 银蓝素光 / 无星 (P) | /f/ 清音立绘仍带星 |
| U31 | 翡翠绿 / 1星 (SR) | 银蓝素光 / 无星 (P) | /s/ 小蛇：绿光立绘配「普通」卡（D5 已允许改造型，但本轮折中不改） |
| **U33** | **皇家紫 + 皇冠 / 4星 (SSR)** | **翡翠绿 / 1星 (SR)** | **跨 3 档：紫皇冠立绘配「稀有」绿卡** |
| U35 | 琥珀 / 2星 (SAR) | 翡翠绿 / 1星 (SR) | 光环过华丽 |
| U36 | 琥珀 / 2星 (SAR) | 宝石红 / 3星 (HR) | 星数少 1 |
| U37 | 皇家紫 + 皇冠 / 4星 (SSR) | 琥珀 / 2星 (SAR) | 缺皇冠却更华丽 |
| U38 | 皇家紫 + 皇冠 / 4星 (SSR) | 宝石红 / 3星 (HR) | 皇冠与星数双错 |
| U39 | 翡翠绿 / 1星 (SR) | 银蓝素光 / 无星 (P) | 立绘仍带星 |
| U41 | 棱镜彩虹 + 皇冠 / 5星 (UR) | 宝石红 / 3星 (HR) | 打鼾国王：彩虹立绘配「英雄」卡（跨 2 档） |
| U42 | 琥珀 / 2星 (SAR) | 宝石红 / 3星 (HR) | 星数少 1 |
| U43 | 翡翠绿 / 1星 (SR) | 银蓝素光 / 无星 (P) | 立绘仍带星 |
| U44 | 琥珀 / 2星 (SAR) | 银蓝素光 / 无星 (P) | 跨 2 档，光环明显过华丽 |
| U45 | 宝石红 / 3星 (HR) | 琥珀 / 2星 (SAR) | 光环过华丽 |
| **U47** | **宝石红 / 3星 (HR)** | **银蓝素光 / 无星 (P)** | **跨 3 档：红宝石立绘配「普通」灰卡** |
| U48 | 宝石红 / 3星 (HR) | 琥珀 / 2星 (SAR) | 光环过华丽 |

### 5.3 按档位归纳（哪几档最乱）

- **`P` 档（新 14 张）**：其中 **10 张**（U21/22/23/24/25/26/27/31/39/43）旧档是 SR → 立绘**全带翡翠绿 1 星**，而 P 档定义为「素光无星」。用户一进 `#/atlas/rarity` 的 P 分组，看到的将是「一整排带绿光星星的『普通』精灵」——**14 张里 10 张不一致，是全表最集中的视觉翻车**。
- **`UR` 档（新 3 张 = ɜː/θ/ð = U11/U29/U30）**：`U11` 旧 SAR 只有琥珀 2 星，而 `U29/U30` 旧档本就是 UR（未改档，棱镜彩虹 5 星）→ **同一档内 1 张朴素 + 2 张彩虹皇冠，档内自相矛盾**，且 UR 是用户明确认可的顶档，最容易被注意到。
- **`SSR` 档（新 4 张 = U18/U19/U20/U34）**：3 张由 HR 升上来（宝石红 3 星、无皇冠），1 张 U34 旧档本就 SSR（紫皇冠 4 星）→ **档内「有的戴皇冠有的不戴」**。
- **`SAR` 档（新 9 张）**：含 U08（旧 UR 彩虹 5 星，过于华丽）、U45/U48（旧 HR 红 3 星）、U37（旧 SSR 紫皇冠 4 星）与 U07/U09/U10（旧 SR 绿 1 星，偏朴素）→ **同档内从 1 星到 5 星、从无皇冠到双皇冠全都有**。
- **12 张未改档**（U03/05/06/12/15/28/29/30/32/34/40/46）本身一致，但**在六档分组里与上述 36 张混排**，反而把不一致衬得更明显。

### 5.4 用户在哪能看到（精确到页面 / 组件）

| 可见位置 | 看到什么 | 严重度 |
|---|---|---|
| `音标大闯关/#/atlas/rarity` 六档分组网格 | 每组 48 格裸立绘（`atlas.js:191` 用 `assets/sprites/${unit}.webp`），旧光环**无卡面遮挡直接暴露**；`got/总数` 是新数字 | 🔴 最高（P 组 10/14 带星、UR 组 1 朴素 2 彩虹） |
| 同页顶部 `atlas-progress` 总图 | `rarity_progress.webp` 旧分组 / 旧数量 / 旧代表立绘，与下方新 DOM 分组**两套数字同屏** | 🔴 最高（V2） |
| `音标大闯关/#/atlas/cards` 卡片 tile | `rar-badge`（新档色）+ 裸立绘（旧光环）叠在一格 | 🟠 高（V1+V4） |
| 图鉴弹窗 `openPhModal` | `cards/${unit}.webp` 大图：立绘旧光环 + 卡面新边框；锁定遮罩还写「稀有度 X」（`:141`，DOM 新档） | 🟠 高（V1+V3） |
| `音标拉力赛` 车库 / 商店「音标卡」 | `main.js:966` 卡面缩略图 + `:969` DOM 文字 `${card.rarity}` | 🟠 高（V3） |
| 已部署的线上站点 | 上述全部，且因缓存串未 bump 可能新旧资源混载 | 🔴 最高（部署风险） |

### 5.5 折中方案的唯一有限适用场景

若用户坚持「先只动文字、立绘留到下一轮」，**唯一不产生自相矛盾的做法是：卡面 / DOM / 总图也全部保持旧档，只把新教研表作为「未生效的下发数据」落盘**（即「先落教研表、可视化不动」，恰是用户已裁决的路径）。**任何「改了可见层但没改立绘」的中间态都会立刻暴露 36 处矛盾**——这正是 D4 资产重出必须另立完整一轮、而不能拆成半步的理由。

---

## §6 风险登记（下一轮开工前须带上的清单）

| # | 风险 | 缓解 |
|---|---|---|
| RR1 | **AI 重出不可复现** → 36 张精灵脸型/姿态漂移，与 12 张旧立绘风格断裂 | 保留 `PROFILES[u]` 锚点逐字不动；重出后 48 张并排过审（v2 §3.7）；必要时 48 张全量重出以统一风格（成本 ↑） |
| RR2 | **`gen_sprites.py` 断点续传**（`:98` 已存在即 skip）→ 不改 prompt 或不清 `raw/` 就重出，光环**纹丝不动** | 重出前 `--force` 或先快照并清 `raw/`；验收时比对 `prompts/*.txt` 是否含新档光环 |
| RR3 | **F2 管线错位**：`convert_webp.py` 指向 `cards/` 英式基线，线上却来自 `webp_american/` | 下一轮第一件事：由 engineering-lead 定权威产物链并统一脚本，再重出 |
| RR4 | **4 份档位数据源 + `data.js` 后 48 处待澄清** → 漏改即 DOM / 图片打架 | 先立唯一权威表，列同步顺序与逐份 diff 验收 |
| RR5 | **SAMPLES 6/6 全变且新档只剩 3 档有样板** | 重选 6 unit + 同步 `compose_cards.py:218` 默认 overview |
| RR6 | **缓存串 46 处 / 两站同源 / Caddy 200 兜底** | ADR-3B 双层缓存口径 + 四重送达复核 + 4 套门控同步 |
| RR7 | **六档总图 `desc` 文案**仍是旧教研口径（`:200`「越难辨越稀有」尚可，但 P「基础音·易解锁」/ UR「最稀有」需按新 CI 复核） | 教研侧复核文案，随总图一起重出 |
| RR8 | **去白底 flood-fill 受光环颜色影响** → 36 张透明边缘需逐张目视 | 重出后逐张验 alpha 边缘；保留旧 `sprites/` 作对照 |
| RR9 | **D5 已允许改造型**（`/s/` 蛇等不再是禁改锚点）→ 若下一轮顺带改立绘造型，需重开 48 立绘过审流程 | 明确本轮 D4 重出**只换光环、不动 `PROFILES` 形象锚点**，把 D5 造型改造再单独排期 |
| RR10 | **已上线图鉴用户已收集的解锁状态**与重出卡面并存 | 解锁状态存 `localStorage`（按 unit id），与图片无关 → 重出不影响解锁；但仍须同源部署避免裂图 |

---

## §7 结论与给用户的决策依据

1. **D4 改档的真实代价 = 85 张图片重出（36 AI 立绘 + 48 卡面 + 1 六档总图）+ 48 个 prompt + 4 份数据源 + 2 处 SAMPLES + 46 处缓存串 + 已上线图鉴原子替换**，其中 **36 张 AI 生图**是唯一有 API 成本与不可复现风险的环节（§3）。
2. **「只重出卡面文字层、立绘不动」不可行**：立绘光环是 baked 像素，会在 36 张卡面、六档分组网格、图鉴弹窗、车库列表产生肉眼可见的档位自相矛盾；其中 **P 档 14 张里 10 张带着绿星**、**UR 档 1 张朴素 + 2 张彩虹**最刺眼，用户在大闯关 `#/atlas/rarity` 一进页就能看到（§5）。
3. **用户已裁决的「先落教研表、资产另立一轮」恰好是唯一无矛盾的中间态**：教研表作为未生效数据落盘、所有可见层保持旧档，直到完整一轮重出就绪再原子替换（§5.5）。本评估即该轮的开工输入。
4. **下一轮开工前必须先解决 3 个前置**：(a) `convert_webp.py` 与线上产物的管线错位（F2）；(b) `data.js` 后半段 48 处 `rarity` 是否需同步；(c) 4 份数据源的唯一权威与同步顺序。三者未定就重出，会把错误固化进已上线图鉴。
5. **回滚基础已就绪**：本轮零改动，线上现状即天然回滚点；§1.4 的逐文件 / 目录级 sha256 基线 + #33 全量快照 + ADR-3B 逐资源下线口径构成三级回滚（§4.3）。

---

## 附：需主理人 / 用户 / 工程侧确认（本文不擅自决定）

1. **【下一轮】重出口径 A（全量 85 张）还是 B（最小 73 张）**——建议 A，因 `compose_cards.py` / `convert_webp.py` 是全量循环，B 需额外过滤逻辑。
2. **【下一轮】`convert_webp.py` 的 `CARD` 该指向 `cards/` 还是 `cards_american/`**（F2 管线错位，须 engineering-lead 定权威链）。
3. **【下一轮】`data.js` 后半段 48 处 `rarity` 是否同步**（§1.3 澄清项）。
4. **【下一轮】`rarity-map.json` 是否新建、以及与 `data.js` / `cards.js` / `manifest.json` 的主从关系**（§2.9 拟建，本轮未动）。
5. **【下一轮】SAMPLES 重选哪 6 个 unit**（§2.3 给了候选，需设计侧确认）。
6. **【下一轮】六档总图 `desc` 文案是否按新 CI 口径重写**（RR7）。
7. **【下一轮】D5 造型改造是否搭车**（RR9，建议不搭车，单独排期）。
8. **【本轮】无** —— 用户裁决已下，本评估只读交付，不请求任何本轮放行。

---

*文档版本 v1.0（D4 改档资产影响面 · 只读评估）· 美术方向 林绘澄（art-director）· Task #35 · 与 `p1-3d-art-spec.md` / `p1-community-assets.md` / v1.1 / v2 / `p1-gameplay-spec.md` 并列，均未改动 · 本轮仅写入本文件，未改任何资产 / 脚本 / 产品代码 / 已上线图鉴 / `rarity-map.json`，未重出、未下载、未跑生成管线、未部署、未上线、未 commit。*

---

## 附：2026-11-10 状态更新（team-lead 本地收口，追加，§1–§7 原文不动）

用户请求「厘清管线，需要根据美式重出版来」，已由 team-lead 用本地工具收口，结论见
**`design/asset-pipeline-american.md`**。对本文的直接影响：

| 本文条目 | 状态 | 说明 |
|---|---|---|
| **F2 / RR3 / §7 前置 (a)**：`convert_webp.py` 指向英式基线的管线错位 | **CLOSED** | `convert_webp.py` 已重写为 `cards_american/ → webp_american/ → assets/sprites/` 美式权威链，加结构守卫与 `--check` / `--check-fast` 只读校验；`--check-fast` PASS=10/FAIL=0、`--check` PASS=20/FAIL=0；线上资产零改动 |
| 附 2「`CARD` 该指向 `cards/` 还是 `cards_american/`」 | **CLOSED · 裁定 `cards_american/`** | 用 49/49 逐字节全等 + 美式 PNG 重编码复现 + 英式 4/4 全不等实证裁定，`cards/` 只留档、隔离 |
| §7 前置 (b) `data.js` 后半段 48 处 `rarity` | **仍 OPEN** | 本轮核实为 96 处（48 unit × 2 表），未动 |
| §7 前置 (c) 4 份数据源唯一权威与同步顺序 | **仍 OPEN，且已量化** | 4 份旧源分布均 `5/17/10/8/4/4`（`data.js` 为 ×2 的 `10/34/20/16/8/8`），而已 ACCEPTED 的 `rarity-map.json` 为 `14/12/9/6/4/3` → **36/48 档位不同**，下一轮重出前必须先统一权威源 |
| 附 1 / 3 / 4 / 5 / 6 / 7 及 §7 结论 1–3、5 | **不变** | 用户「先落教研表、资产另立一轮」裁决仍有效，本轮零重出、零改线上资产 |

**本轮边界复核**：除 `sprite_gen/convert_webp.py` 与两份设计文档外零写入；
未重出 85 张、未改 48 卡面 / 48 立绘 / 六档总图、未改 `manifest.json` / `data.js` / `cards.js` /
`compose_cards.py`、未部署、未上线、未 commit。
