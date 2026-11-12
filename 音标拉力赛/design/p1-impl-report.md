# P1 3D 卡丁车主形态 · 定型实现报告

> 2026-11-11 · team-lead 本地收口（用户授权「我自己用本地工具收口」）
> 对应请求：**「定型 3D 卡丁车」**
> 结论：**3D 卡丁车主形态已可用、可观测、可回退，判定核心零改动 → 功能层面定型完成。**
> 但 **发布层面未定型**：旧门控 6 条真实 FAIL 未处置、`verify_p1_gate.py` 仍 SPEC_ONLY，详见 §6 / `p1-legacy-gate-fail-scan.md`。

---

## §1 定型判据与达成情况

| 判据 | 要求 | 实测 | 结论 |
|---|---|---|---|
| 玩家车 + 2 NPC 真的画出来 | mesh / drawCalls / 屏占比 > 0 且可区分，**禁止以「Canvas 存在」冒充** | `kartIds=["you","a","b"]`、`kartMeshCount=63`、`meshCount=95`、`drawCalls=71`、三车 `kartScreenRatio` 0.0167/0.0101/0.0130（桌面）、0.0282/0.0170/0.0219（375 竖屏） | ✅ |
| 第三人称跟车 | 车在近处、赛道向远处消失、看不到整圈 | `seesWholeLoop=false`、`visibleRangeM=66.667 < lapLengthM=154.036`、`cameraOdoEstM` 随里程单调 7.607→15.256 | ✅ |
| 竖屏可玩（D6 终点之一） | 375×780 与 320×568 可用、无横向溢出 | 两尺寸三车可见、四项错误 0、`scrollWidth == innerWidth`；垂直 FOV 分别 78° / 74°（桌面 60°） | ✅ |
| 听音选车道保真 | 判定核心逐字不改、3D 只读快照、零答案域 | 七文件 sha 全等基线；`storageWrites=0`；STATE 零答案域 + 三条白名单逐字锁定 | ✅ |
| 降级不白屏 | `?p1=off` / `?render=2d` / 无 WebGL / `webglcontextlost` | V4 / V5 / V6 三组实测 `renderMode=2d`、`mounted=false`、2D L0 `racing` 可玩、`#c` 画布有效 | ✅ |
| 判定确定性 | 2 圈 4 门、11 场 ALL PASS、≤180s | `npm run headless` 11/11，最慢 174.57s | ✅ |
| 旧门控 | 门控全绿 | **6 条真实 FAIL**（详见 §6） | ❌ 未达成 |

---

## §2 改动文件清单

### 2.1 P1 实现文件（以磁盘当前版本为准）

| 文件 | 大小 | 时间 | 作用 |
|---|---|---|---|
| `音标拉力赛/index.html` | 9008 B | 11-11 07:33 | 保留 `js/main.js?v=hud-20261108`；新增动态注入 `assets/p1/scene3d.js?v=hud-20261108`（字符串拼接构造，不污染源码层 46 处 tag 静态扫描）；`?p1=off` / `?render=2d` 置 `__P1_OFF__` |
| `音标拉力赛/js/scene3d.jsx` | 21772 B | 11-11 07:33 | R3F 场景 + 命令式 three：三车程序化几何、赛道 ribbon、闸门、跟车相机、FogExp2、双灯；暴露 `window.__P1_SCENE__`；`ACTIVE_MODES` 只在 countdown/racing/paused/quiz 挂载；`degrade()` / `webglProbe()` 降级 |
| `音标拉力赛/js/scene3d-model.mjs` | 16970 B | 11-10 22:37 | 只读白名单投影 `snapshot3d()` / `buildSceneFrame()` / `SNAPSHOT_KEYS`；不复制 state、不写回判定域 |
| `音标拉力赛/js/scene3d-model.test.mjs` | 12866 B | 11-10 22:32 | 18 项 Node 单测（含 T8 三车显形、T14 屏占比、T11 不泄答案、T17 mirrorZ） |
| `音标拉力赛/js/build-p1.mjs` | 2422 B | 11-10 22:38 | 把 jsx 构建成自包含 IIFE；6 项静态自检 |
| `音标拉力赛/assets/p1/scene3d.js` | **1164508 B** | 11-11 07:56 | 主站动态注入的预构建产物（本轮重建，见 §3.2） |
| `音标拉力赛/package.json` | 977 B | 11-10 22:39 | `dev/build/preview/headless/test:minimap/test:scene3d/build:p1` |
| `音标大闯关/deploy.sh` | 2136 B | 11-10 22:39 | 已补 `音标拉力赛/` 同源同级 scp（含 `assets/p1/`），**只改脚本、未执行** |

### 2.2 本轮（11-11）新增 / 修改

| 文件 | 动作 | 说明 |
|---|---|---|
| `音标拉力赛/verify_p1_visual.py` | **新建** | 真实 Chromium 六场景 63 项门控（3D 可见 / 竖屏 / 降级 / H5 / 四项错误），可复跑 |
| `音标拉力赛/assets/p1/scene3d.js` | **重建** | `npm run build:p1` 从 1164153 B → 1164508 B，见 §3.2 |
| `音标拉力赛/design/p1-impl-report.md` | 新建 | 本文 |
| `音标拉力赛/design/p1-legacy-gate-fail-scan.md` | 新建 | 旧门控 FAIL 扫描报告 |
| `音标拉力赛/design/asset-pipeline-american.md` | 新建 | 美式重出版资产管线厘清 |
| `音标大闯关/sprite_gen/convert_webp.py` | 重写 | 英式基线 → 美式权威链 + 结构守卫 + 只读校验 |
| `音标拉力赛/design/p1-sprite-reaudit-impact.md` | 追加状态 | F2 / RR3 / §7 前置 a 标 CLOSED |

> **时间线说明**：`index.html` / `scene3d.jsx` 在 **11-11 07:33** 有一次补齐更新
> （8805→9008 B、20760→21772 B），由工程侧落盘但**未附实现报告**。本轮不回滚、不覆盖，
> 直接以磁盘当前版本做全量实跑取证；以下所有结论均基于该版本。

---

## §3 ADR-2 硬约束证明：判定核心逐字不改

对照 `.workbuddy/backups/p1-pre-20261110/manifest.txt`（P1 改动前全量快照）：

| 文件 | 基线 sha256（前 16） | 当前 sha256（前 16） | 结论 |
|---|---|---|---|
| `js/race.js` | `e9a17cf03dabcada` | `e9a17cf03dabcada` | ✅ 全等 |
| `js/track.js` | `15b77aff0548a046` | `15b77aff0548a046` | ✅ 全等 |
| `js/config.js` | `0dfe653c7552aab3` | `0dfe653c7552aab3` | ✅ 全等 |
| `js/main.js` | `2db27bd0c1010faf` | `2db27bd0c1010faf` | ✅ 全等 |
| `js/render.js` | `7b65bafa994de5cc` | `7b65bafa994de5cc` | ✅ 全等 |
| `js/probe.jsx` | `d149c0f0d409ee…` | `d149c0f0d409ee…` | ✅ 全等（P0 探针逐字不动） |
| `probe.html` | `4f045d8159569ed…` | `4f045d8159569ed…` | ✅ 全等 |

**3D 层是纯增量**：只读 `snapshot3d()` 白名单投影，绝不写回 `odo / lateral / g.line`，
`storageWrites=0`；`odo/lateral + g.line` 判定链、`buildGates()`、`hitsLane`、quiz 三题型、83 词 mp3 全部未动。
`config.js` 的 `length/tone/color` 仍是 A/B 分组着色键，**不得用作 D4 教研维度**。

### 3.2 本轮修掉的一个真实问题：预构建产物陈旧

仓库里 `assets/p1/scene3d.js` 为 **1164153 B**，与源码构建的 **1164508 B** 不一致——
即线上/静态源码形态会加载到**相对源码陈旧的 bundle**，这正是「定型」必须排掉的隐患。

- `npm run build:p1` 重建 → 1164508 B；
- 连跑两次 sha256 均为 `737224d003249f178f3b44de…`，**构建可复现**；
- 6 项静态自检全 OK：源码层 tag=0 / P0 产物层 tag=0 / 未替换 `process.env`=0 /
  `fogType` 字符串=0 / Storage 写入 API=0 / 图片 URL 裸引用=0；
- 重建后立刻用真实 Chromium 复验（`verify_p1_visual.py` 连续两轮 63/63），证明新 bundle 可加载且三车可见。

---

## §4 实跑证据（本轮全部真实执行，非推断）

| 套件 | 结果 |
|---|---|
| `npm run test:scene3d` | **18 PASS / 0 FAIL / 18** |
| `npm run test:minimap` | **10 PASS / 0 FAIL / 10** |
| `npm run build:p1` | 6 项静态自检全 OK，产物 sha 两次一致 |
| `npm run headless` | **11 场 ALL PASS**，最慢 174.57s ≤ 180s；4 门 4/4、跨圈 1、额外题独立统计；题库「地图 4 / 词对 37 / 词 83 / 题型 3」 |
| `verify_p1_visual.py`（连续两轮） | **63 PASS / 0 FAIL / 63**，V1 桌面 / V2 375 竖屏 / V3 320 小屏 / V4 `?p1=off` / V5 `?render=2d` / V6 无 WebGL；六场景四项错误计数（pageerror / console_error / requestfailed / bad_status）**全 0** |
| `convert_webp.py --check-fast` / `--check` | 10/10、20/20（美式资产链，见 `asset-pipeline-american.md`） |

### 4.1 3D 主形态关键实测值（1280×800）

```
renderMode=3d  mounted=true  webgl=true  WebGL 2.0 (OpenGL ES 3.0 Chromium)
kartIds=["you","a","b"]   kartMeshCount=63   meshCount=95   drawCalls=71   frames=6
kartScreenRatio = {you:0.01669, a:0.009993, b:0.012857}
kartProjected   = 三车 NDC 包围盒均落在 [-1,1] 且面积为正
fog={isExp2:true, density:0.045}   light={count:2, main:2.1, fill:0.32}
convergence={seesWholeLoop:false, visibleRangeM:66.667, lapLengthM:154.036}
camera={fov:60, fovIsVertical:true, heightM:3.6, distanceM:8, pitchDeg:18}
storageWrites=0   errors=[]   degraded=false
```

375×780 与 320×568 下 `fov` 分别为 **78° / 74°**（竖屏以垂直 FOV 为锚），三车屏占比更大且全部可见。

### 4.2 一个测试侧假阳性（如实记录，未静默改绿）

`verify_p1_visual.py` 首轮 **57/60**，3 条 FAIL 全在自建 H5 检查：
`snapshotKeys / kartKeys / gateKeys` 被命中，因为我把裸词 `key` 放进禁用表，
而这三个是 **QA 白名单诊断字段的名字**（`…Keys`），不是答案域。

处置：去掉裸词 `key`，**同时新增三条白名单逐字断言**（必须严格等于 Node 单测 T3/T4 的
`snapshot/kart/gate` 白名单），使往白名单里夹带答案域字段必然 FAIL——**覆盖面比原来更严，不是放宽**。
修后 63/63 全绿。另有一轮 V2 单点 `console_error=1 / requestfailed=1` flake，
脚本已加错误明细捕获，随后两轮完整复跑均未复现（记录备查，未作豁免）。

---

## §5 旧门控结果（详见 `p1-legacy-gate-fail-scan.md`）

| 脚本 | 结果 |
|---|---|
| `verify_cseg_gate.py` | 36/38，**S17、S18 FAIL** |
| `verify_cseg_ui.py` | 14/14 全绿 |
| `verify_fresh_gate.py` | 20/21，**F8a FAIL** |
| `verify_c08_gate.py` | 36/37，**S1.7 FAIL** |
| `verify_hud_spec.py` | 11/12，**H11 FAIL**（复合断言） |
| `verify_p0_gate.py` | **62/62 全绿**，1 条既有 CONCERN CN-4 |
| `verify_p1_gate.py` | exit=2，**SPEC_ONLY 未实跑**（非 FAIL） |
| `verify_atlas_sprites.py` | 1 条真实断言 FAIL（旧脚本注入 `collected:['iː','p']`，字段已退役） |
| `verify_p1_visual.py`（新） | 63/63 全绿 |

**5 条 FAIL 同一根因**：四套旧门控 `os.walk` 只排除 `assets/docs/sprite_gen`，
P0 新增的 `node_modules/` 被误纳入 → 4 个第三方杂 tag（`bidi-js` / `three` examples /
`troika-three-text`）+ 33 处裸引用（100% 在 `node_modules/`）。
按原口径重算：**产品层 `{hud-20261108:46}` 唯一且恰好 46、裸引用 0**。
`p1-qa-spec.md` §2.6 第 324 行早已规定该排除清单（PF-07 / `PB-*`），`verify_p0_gate.py` 已采用。

**本轮零改门控脚本、零放宽、零 NOTE 化**；修法（甲：按 §2.6 补排除 + 补偿断言 / 乙：退役旧套件）须用户拍板。

---

## §6 回滚路径

1. **一键回退（用户侧，零部署）**：URL 加 `?p1=off` 或 `?render=2d`，
   实测 `renderMode=2d / mounted=false / 2D L0 racing 完整可玩`。
2. **自动降级**：WebGL 不可用 / `webglcontextlost` → `degrade()` → 2D L0，实测不白屏（V6）。
3. **源码级回滚**：删除 `index.html` 的 P1 注入段（11 行）即回到 P0 状态；
   `main.js` / `render.js` / 判定核心 / 48 资产逐字未动，2D L0 链路天然完整。
4. **全量快照**：`.workbuddy/backups/p1-pre-20261110/`（25 文件 / 536468 B + sha256 manifest），
   及更早的 `c07b-data-baseline.js` / `c08_resume_backup_20261107/`。

> D6 退役的是「**2D 作为默认主形态**」的地位，**不是删除 2D 代码路径与 48 资产**；
> 2D 保留为 L0 应急回滚能力。退役时点 / 发布签字仍归用户。

---

## §7 遗留风险与 OPEN 项

| # | 项 | 状态 |
|---|---|---|
| R1 | 旧门控 6 条 FAIL 未处置，门控全绿未达成 | **OPEN · 发布硬阻断**，见 §5 / FAIL 扫描报告 §6 |
| R2 | `verify_p1_gate.py` 仍 `SPEC_ONLY`，132 条判据未实跑 | **OPEN · 发布硬阻断**；`p1-qa-spec.md` §10 前置 |
| R3 | `design/3d-adr.md` 停在 11-09 15:07，**ADR-1C / ADR-4C 未重写**（全文零命中） | **OPEN**，Task #40 未完成项；不影响运行，影响架构可追溯性 |
| R4 | `deploy.sh` 已补同源 scp 但**未执行**；SSH 交互式密码在非交互环境无法代输 | **OPEN · Phase B 硬阻断**，需你确认凭据方式 |
| R5 | 项目**仍无 git 仓库**；用户已选「建仓且全量纳入」 | **OPEN · Phase B** |
| R6 | Caddy 对不存在路径兜底 200 返回首页；上线后资源须按字节 + magic + sha256 + Content-Type 复核 | 沿用既有纪律 |
| R7 | D4 资产重出另立一轮：4 份旧数据源 `5/17/10/8/4/4` vs 已 ACCEPTED `rarity-map.json` `14/12/9/6/4/3`，**36/48 档位不同** | **OPEN**，本轮零重出；见 `asset-pipeline-american.md` §4 |
| R8 | `verify_features.py` / `verify_audio_fix.py` 因 `#modal-layer` 弹层遮挡 click 超时；`verify_atlas_sprites.py` 注入口径过时且 FAIL 时 exit=0 | **OPEN**，旧脚本待修，非产品缺陷 |
| R9 | G9 儿童主观眩晕实测 | 已按裁决降为**上线后观察项 / advisory**，不计入门控、不阻断 |
| R10 | 社区模型：**0 进仓、0 下载**，7 条候选全为 candidate；P1 用程序化几何 | 符合 D2「允许 ≠ 必须」 |
| R11 | `verify_hud_spec.py` 既有 2 条 NOTE（H10 signKey 不可观测 / H4 quiz 层叠口径） | 沿用，未改 |

---

## §8 边界声明

- 本轮**未部署、未上线、未 commit、未建 git 仓库**；
- **未重跑上游构建管线**（`content_raw.json` / `build_data.py` / `augment_data.py`），
  `js/data.js` 美式文案改写保持原样；
- **未重出 48 张资产**、未改任何线上卡面 / 立绘 / 六档总图；
- **未改任何旧门控脚本 / 阈值 / 断言**；
- 8765 临时测试服务器已关闭（PowerShell `Get-NetTCPConnection` 无 listener，`curl http=000`）；
- 按用户拍板 **D6 终点 =「门控全绿 + 375px 可玩」**：后者已达成，前者未达成。
  **Phase B 须用户明确放行后方可执行。**

---

*本报告所有数字来自本轮真实实跑；未替用户放行任何退役、改档、部署、上线或提交动作。*
