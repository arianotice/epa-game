# epa-game · 声音探险队

面向小学六年级的英语音标启蒙项目：**78 段播客 + 29 张探险地图插画 + 48 个音标精灵**，落成两套互补的互动玩法。

| 站点 | 入口 | 形态 |
| --- | --- | --- |
| **音标拉力赛** | `音标拉力赛/index.html` | 3D 第三人称跟车卡丁车，听音选车道、四大杯赛、两圈计时、赛事解锁音标卡 |
| **音标大闯关** | `音标大闯关/index.html` | 滚动叙事 9 幕 + 30 关闯关 + 48 音标图鉴（含稀有度进阶图鉴） |
| 根导航页 | `index.html` | 两站入口 |

两站共享同一个 `localStorage['ipa-quest-v1']` 单键进度，因此**必须部署在同一 origin 下且互为兄弟目录**。GitHub Pages 以仓库根为站点根，上述布局即天然满足；`音标拉力赛/` 内 `../音标大闯关/...` 共 7 处字面引用依赖这一点。

## 快速开始

两站都是静态站，无需构建即可打开（同源前提下）：

```bash
# 在项目根起任意静态服务器，再访问 /index.html
python -m http.server 8000
```

`音标拉力赛/` 另带 `Vite + React Three Fiber` 工程链（`package.json`），用于开发与预构建 3D 产物；发布用的是已提交的 `assets/p1/scene3d.js`（IIFE，零外部运行时依赖），**不依赖 CDN**。

```bash
cd 音标拉力赛
npm install
npm run build:p1          # 重建 assets/p1/scene3d.js
npm run test:scene3d      # 18 项纯函数单测
npm run test:minimap      # 10 项纯函数单测
npm run headless          # 两圈 11 场确定性实跑
```

## 验证与判据

统一门控入口：

```bash
cd 音标拉力赛
py -3.13 verify_p1_gate.py        # 实跑，产出 result.json
py -3.13 verify_p1_gate.py --spec-only   # 仅清单自检
```

当前 `result.json`：**121 PASS / 0 FAIL / 121 TOTAL，`GATE_VERDICT = PASS`**（连续两轮一致）。组成：

- 路线 B 重定义套件 `verify_p0_gate.py` 62 项 + `verify_p1_gate.py` 静态断言 B1–B10
- **81 项 `PLR-*` 迁移重放**：四套旧门控已于 2026-11-12 经用户书面裁决「整体退役」，但 81 条断言一条未删，通过 `verify_p1_plr.py` 重放适配器以正确扫描域逐条重放（承接表见 `音标拉力赛/design/p1-gate-retirement.md` §3）
- `verify_p1_visual.py` 真实 Chromium 六场景 63 项（3D 三车可见 / 375px 竖屏 / 320×568 / 一键回退 / 无 WebGL 降级）
- `js/headless_laps.mjs` 11 场 ALL PASS，最慢 174.57s ≤ 180s

规范文档集中在 `音标拉力赛/design/`：`p1-qa-spec.md`（判据）、`p1-gameplay-spec.md`（玩法与教研）、`p1-3d-art-spec.md`（视觉）、`3d-adr.md`（技术决策）、`asset-pipeline-american.md`（美式重出版资产链）、`p1-impl-report.md`（3D 实现报告）、`p1-legacy-gate-fail-scan.md`（旧门控 6 条真实 FAIL 留痕）。

## 关键口径（改动前请读）

- **美式 IPA 唯一权威源**：`音标大闯关/js/ipa-display.js` 的 `window.IPA_DISPLAY`（U11=`ɜr`、U18=`ɪr`、U19=`ɛr`、U20=`ʊr`）。`sym` 是英式稳定键，**只作存档 / 查表 / 去重 / 角标 / alt，禁止改、禁止拿 `displayIpa` 当键**（U05/U07 同为 `ɑ` 会丢 U07）。
- **卡面资产链**：`cards_american/ → webp_american/ → assets/sprites/cards/`。`音标大闯关/sprite_gen/convert_webp.py` 已按美式重出版修正；旧 `cards/` 是英式基线，仅隔离留档。无意重跑上游 `content_raw.json` / `build_data.py` / `augment_data.py` 会覆盖美式文案改写。
- **判定核心逐字不改**：`音标拉力赛/js/race.js` / `track.js` / `config.js`。3D 层只读快照驱动，绝不写回 `odo` / `lateral` / `g.line`。
- **双层缓存**：源码层 `?v=hud-20261108`（46 处字面量）与产物层 `P1_TAG=p1-20261110` 互不混算；所有 script / link / ESM import / 图片 URL 必须带同一 tag，改动后统一 bump。
- **音标卡只能靠赛事地图解锁**，商店宝石不能兑换。
- **答案零泄露**：H5 检测面 = `textContent` + 后代所有属性值 + 83 词全表 + 4 字段名，不退回 `innerHTML`。
- 线上若经 Caddy 部署，**不存在路径会兜底返回 `index.html` 且状态码 200**；判定资源是否真送达必须比对字节数 / magic / sha256 / Content-Type，不能只看 HTTP 状态。

## 仓库边界（明确排除项）

项目自身成果全量纳入。以下不是交付物，见 `.gitignore`：

| 排除项 | 体积 | 理由 |
| --- | --- | --- |
| `音频/` | ≈ 2.0 GB | 播客 WAV 母带与中间音频。网站运行只需 `音标大闯关/assets/audio/` 内 78 个已转码 Opus（随大闯关一并纳入） |
| `node_modules/`、`dist/`、`.p0-build/` | ≈ 300 MB | 依赖与构建产物，可由 `package.json` / 构建脚本重建 |
| `agent-sprite-forge/`、`agnes-ai-generation-skill/`、`_phrepo/`、`_ph_combined_tmp/` | ≈ 215 MB | 第三方开源仓库 clone（自带 `.git`，直接纳入会变成 gitlink 导致 clone 后内容为空）及临时素材 |
| `.workbuddy/`、`*.genie` | ≈ 153 MB | 本地状态、快照备份与内部产物 |
| `音标大闯关/tmp_crops/`、`tmp_shots/` | ≈ 13 MB | 图片处理临时裁图 / 截图 |

`图片/`（成稿 / 定稿 / 方向稿 / 合成脚本，≈ 247 MB）与 `音标大闯关/sprite_gen/`（美式卡面 PNG 源）均作为正式资产纳入。

## 外部依赖

第三方工具仓库未打包进本仓库，需要复现资产生成时请单独获取：

- `agent-sprite-forge` — 参数化精灵生成器参考实现（D5 允许改动原 2D 立绘标志性造型）
- `agnes-ai-generation-skill` — 免费生图通道，48 张精灵立绘由 `agnes-image-2.1-flash` 生成
- `_phrepo` — 音素词库与发音素材，供 `build_phoneme_*.py` 使用

社区 3D 模型：**0 个进仓、0 个下载**。`音标拉力赛/design/p1-community-assets.md` 只登记了 7 条 candidate 及 provenance 规范；未取得 explicit permission 的模型一律不进仓。

## 部署

GitHub Pages：仓库根即站点根，`index.html` 为入口，两站为兄弟目录。需在仓库 Settings → Pages 选择 `main` 分支 / `/(root)` 后生效。

历史腾讯云脚本 `音标大闯关/deploy.sh` **不适用于本仓库布局**：它把大闯关内容直接落 `$DEST/` 根、拉力赛落 `$DEST/音标拉力赛/`，未创建 `$DEST/音标大闯关/`，回退路径下 7 处 `../音标大闯关/` 会落空（详见 `3d-adr.md` ADR-4C）。本次发布不执行该脚本。
