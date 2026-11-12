# 旧门控真实 FAIL 扫描报告（P1 · 2026-11-10）

> 用户请求：**「扫描出旧门控 FAIL」**
> 硬纪律：**逐条记录真实 FAIL，不静默改成 NOTE、不放宽阈值、不删断言、不改任何门控脚本。**
> 执行：team-lead 本地工具收口（用户授权「我自己用本地工具收口」），未派同事、未编造回报。
> 环境：Windows / `py -3.13` (Pillow 12.3) / Node v22.22.2 / 系统 Chrome + Playwright / 各脚本自起 in-process http.server。

---

## §1 扫描范围与汇总

实跑 **10 个门控脚本 + 4 个 Node/npm 套件**。命令均为脚本原用法，零参数改写。

| # | 脚本 | exit | 结果 | 判定 |
|---|---|---|---|---|
| 1 | `音标拉力赛/verify_cseg_gate.py` | **1** | **36 PASS / 2 FAIL / 38** | S17、S18 真实 FAIL |
| 2 | `音标拉力赛/verify_cseg_ui.py` | 0 | 14 PASS / 0 FAIL / 14 | 全绿（真实 Chromium DOM） |
| 3 | `音标大闯关/verify_fresh_gate.py` | **1** | **20 PASS / 1 FAIL / 21**，CONCERNS 0 | F8a 真实 FAIL |
| 4 | `音标大闯关/verify_c08_gate.py` | **1** | **36 PASS / 1 FAIL / 37** | S1.7 真实 FAIL |
| 5 | `音标拉力赛/verify_hud_spec.py` | **1** | **11 PASS / 1 FAIL / 12**，NOTE 2 | H11 真实 FAIL（复合断言） |
| 6 | `音标拉力赛/verify_p0_gate.py` | 0 | **62 PASS / 0 FAIL / 62**，CONCERN 1 | 全绿；CN-4 为既有部署口径提示 |
| 7 | `音标拉力赛/verify_p1_gate.py` | **2** | SPEC_ONLY 静态自检 OK | **非 FAIL**；骨架未实跑、未启浏览器、未出 SUMMARY |
| 8 | `音标拉力赛/verify_p1_visual.py`（本轮新建） | 0 | **63 PASS / 0 FAIL / 63**（连续两轮） | 3D 三车可见 / 竖屏 / 降级全绿 |
| 9 | `音标大闯关/verify_atlas_sprites.py` | 0\* | **1 FAIL / 8 PASS**，输出「存在失败 ❌」 | 真实断言 FAIL；\*脚本未用 exit code 表达失败 |
| 10 | `音标大闯关/verify_features.py` | 1 | Playwright click 超时 | 交互超时，非断言 FAIL（见 §4） |
| 11 | `音标大闯关/verify_audio_fix.py` | 1 | Playwright click 超时 | 交互超时，非断言 FAIL（见 §4） |

**Node / npm 套件（同轮实跑）**：`npm run test:scene3d` **18/18**、`npm run test:minimap` **10/10**、
`npm run build:p1` 6 项静态自检全 OK 且连跑两次产物 sha 相同、`npm run headless` **11 场 ALL PASS**（最慢 174.57s ≤ 180s）。
另 `sprite_gen/convert_webp.py --check-fast` 10/10、`--check` 20/20（见 `asset-pipeline-american.md`）。

**合计真实断言 FAIL = 6 条**（§2 五条 + §3 一条）。

---

## §2 五条真实 FAIL：缓存串 / 裸引用扫描域被 `node_modules/` 污染

### 2.1 逐条原文

| 编号 | 脚本 | FAIL 断言 | 实际命中 |
|---|---|---|---|
| F-1 | `verify_cseg_gate.py` | `S17 全仓 tag 唯一且恰好 46 处` | `{'hud-20261108': 46, 'r': 1, 'DxMfblPzFNc': 1, '6B7IF6GOu7s': 3, 'e': 4}` |
| F-2 | `verify_cseg_gate.py` | `S18 全仓图片 URL 零裸引用（含动态拼接型）` | 33 处，示例 `node_modules/@react-three/drei/index.cjs.js` → `/px.png` `/nx.png` `/py.png` `/ny.png` `/pz.png` `/nz.png` |
| F-3 | `verify_fresh_gate.py` | `F8a 全仓 ?v= tag 唯一（46 处字面量…）` | 同 F-1 直方图 |
| F-4 | `verify_c08_gate.py` | `S1.7 全仓 tag 唯一值（46 处字面量…）` | 同 F-1 直方图 |
| F-5 | `verify_hud_spec.py` | `H11 tag 唯一且恰好 46 处 / CACHE_TAG 同步 / 20 个图片 URL 零裸引用 / 资源按字节送达` | 同 F-1 + 33 裸引用 + `node_modules/.vite/deps/@react-three_fiber.js` 的 `./chunk-*.js` 裸 import；**但 `CACHE_TAG 同步=True`、`按字节比对=True`、`带错 tag 的请求=[]`、`IPA_DISPLAY.U11=ɜr` 全部仍 PASS** |

### 2.2 根因（实证，非推测）

四套旧门控的扫描实现是 `os.walk(QUEST/RALLY)`，排除项只有 `assets/`、`docs/`、`sprite_gen/`：

- `音标拉力赛/verify_cseg_gate.py:99-112`（S17）、`:115-140`（S18）
- `音标大闯关/verify_fresh_gate.py:178-186`（F8a）
- `音标大闯关/verify_c08_gate.py` S1.7、`音标拉力赛/verify_hud_spec.py` H11 同构

**P0（Vite + R3F 接管）在 `音标拉力赛/` 下新增了 `node_modules/`，旧门控的 `os.walk` 没有排除它。**

逐文件定位（本轮独立复算）：

| 杂 tag | 唯一来源文件 |
|---|---|
| `r` | `node_modules/bidi-js/dist/bidi.min.js` |
| `DxMfblPzFNc` | `node_modules/stats-gl/node_modules/three/examples/jsm/geometries/TeapotGeometry.js` |
| `6B7IF6GOu7s` | `node_modules/three/examples/jsm/shaders/WaterRefractionShader.js` 等 3 处 |
| `e` | `node_modules/troika-three-text/dist/troika-three-text.umd.min.js` |

按 S18 **原口径**重算全仓裸引用共 **33 处**：
**产品层 0 处 / `node_modules/` 33 处（100%）**。
按 S17 **原口径**重算产品层 tag：`{hud-20261108: 46}`，**唯一且恰好 46，一字未变**。

> 结论：**产品源码层缓存串与图片 URL 仍然完全合规**；5 条 FAIL 全部由「第三方依赖被误纳入扫描域」产生，
> 属门控扫描域缺陷，不是 3D 改动造成的产品回归。

### 2.3 规格里早已有承接（不是新发现的未知风险）

`design/p1-qa-spec.md` §2.6 第 324 行已明文规定：

> 源码层：白名单 9 文件锁 `{hud-20261108: 46}`，唯一且恰好 46；扫描根 `os.walk(QUEST/RALLY)`
> 且**排除** `node_modules/` / `dist/` / `.p0-build/` / `.workbuddy/`（`p0-qa-spec.md` §2.6 白名单，
> **防 33 处 `node_modules` 裸引用污染**）。

即 `PB-*` 双层缓存判据已预设该排除清单，`verify_p0_gate.py` 已采用（本轮 62/62 全绿），
**四套旧门控尚未跟进**。本轮**不改任何门控脚本**，因为改扫描域属于门控口径变更，
须用户拍板后才能执行（见 §6）。

---

## §3 第六条真实 FAIL：图鉴收集态注入口径过时

`音标大闯关/verify_atlas_sprites.py`：

```
[FAIL] 收集后 got 卡 + 稀有度徽章  -> {'got': 0, 'rar': 0}
总体: 存在失败 ❌     （但进程 exit=0，脚本未用退出码表达失败）
```

根因在脚本 `:35`：

```js
const o={stars:{},collected:['iː','p'],sound:true,lastEp:'EP00'};
localStorage.setItem('ipa-quest-v1', JSON.stringify(o));
```

双重过时：
1. `collected` 早在 FIX-B01 / G4 已**退役为恒 `[]`**（`js/store.js:12` 注释「退役字段：键保留、值恒为空」），
   老存档迁移会把注入值搬进 `legacyCollected` 并清空 `collected`（`store.js:107-121`）；
2. 当前**唯一解锁源是 `rally.unlocked`，按 unit id `U01–U48`**（`store.js:4,14`），
   而脚本注入的是英式 IPA 符号 `iː / p`，既不是 unit id 也不是美式口径。

因此 `got=0 / rar=0` 是必然结果。**属旧测试脚本数据口径过时，不是图鉴产品缺陷**；
同脚本其余 8 项（48 张立绘加载、dim 灰化、身份卡大图、六档分组、webp 200、JS 无错误）全 PASS。

---

## §4 非断言失败 / 环境前置（不计入 6 条 FAIL，但如实登记）

| 项 | 现象 | 定性 |
|---|---|---|
| `verify_features.py` | `Page.click` 超时：`<button class="word-chip">` 被 `#modal-layer` 子树 `intercepts pointer events` | 交互前置未关弹层；非断言 FAIL |
| `verify_audio_fix.py` | `Page.click` 超时：`.play-btn` 被 `<div class="modal projcard">` / `#modal-layer` 拦截 | 同上 |
| 三个脚本初始 `ERR_CONNECTION_REFUSED localhost:8765` | 依赖固定端口外部服务器，而该服务器此前已按用户要求关闭 | 环境前置；本轮临时起 8765 补跑后**立即关闭**，复核 `http=000 connection refused`、PowerShell `Get-NetTCPConnection` 无 listener |
| `verify_p1_gate.py` exit=2 | `SPEC_ONLY` 骨架，未启浏览器、未起服务、未产生验收 SUMMARY | **未就绪，不是 FAIL**；`design/p1-qa-spec.md` §10 前置齐备后才实跑 |
| `verify_p0_gate.py` CONCERN CN-4 | `dist/` 单目录发布时两站不同源、共享 `ipa-quest-v1` 不成立 | 既有部署口径提示（脚本明写「不判 PASS、不悄悄放行」）；现行 `deploy.sh` 源码 scp 双站同级 → 同源成立 |

---

## §5 PF-01~PF-10 失效族映射

`design/p1-qa-spec.md` §3.1 定义的 10 族，本轮实跑映射如下（**没有一条被删除、放宽或改 NOTE**）：

| 族 | 规格预测 | 本轮实测 | 承接 |
|---|---|---|---|
| PF-01 | 主站「零 WebGL」断言方向反转 | `verify_p0_gate.py` **62/62 仍全绿**——因 `scene3d.jsx:68` `ACTIVE_MODES` 只在 countdown/racing/paused/quiz 挂载，title/teach 仍零 WebGL 上下文；3D 主形态由 `verify_p1_visual.py` V1–V3 证 WebGL 真创建 | `PV-1..PV-4` 已由 V1–V3 的 `webgl/meshCount/drawCalls/kartScreenRatio` 取证 |
| PF-02 | `boxCount==1` 不再是验收对象 | 探针 `probe.jsx`/`probe.html` 逐字不动；P1 实测 63 卡丁 mesh / 95 总 mesh / 71 drawCalls | `PV-2/3` + `PVIS-5`（实测 light.count=2 / FogExp2 density 0.045） |
| PF-03 / PF-04 | 探针开关 / 回退入口语义变化 | `?p1=off`、`?render=2d` 两条路径实测 `renderMode=2d / mounted=false / 2D L0 完整可玩` | V4 / V5 + `PDEG-*` |
| PF-05 | `#c` 2D canvas 不再是主渲染面 | 3D 主形态下 `__rally` 只读 getter 仍挂载、`__rally.mode=racing`、2D HUD DOM 14/14 (`verify_cseg_ui`) | V1–V3 + `BD-4'` |
| PF-06 | 资源集需扩充、四重判定不变 | H11 的 `按字节比对=True`（index.html / main.js / ipa-display.js 三份字节全等）仍 PASS | `PVB-*` |
| **PF-07** | **双层 tag / 扫描根隔离** | **F-1/F-3/F-4/F-5 四条 FAIL 正落此族**：旧门控未按 §2.6 排除 `node_modules/` | **`PB-*` 已在规格预设排除清单，待用户拍板后落地** |
| PF-08 | 检测面扩大、词表不变 | V1–V3 `H5 零泄露` + 三条白名单逐字锁定全 PASS | `PQ-4` / `PQ-5` |
| PF-09 | 新增 WebGL 事件噪声源 | V1–V6 四项错误计数（pageerror / console_error / requestfailed / bad_status）**全 0** | `PE-*` |
| **PF-10** | **H 系列不得静默删除，逐条须有 PASS/FAIL 或替代编号** | H11 真实 FAIL 已如实登记（F-5），未改 NOTE；`verify_hud_spec.py` 其余 11 项 PASS | 本报告即 §3.1 要求的「实跑报告逐条登记」 |

---

## §6 处置口径（本轮零改动，等用户拍板）

**本轮没有修改任何门控脚本 / 阈值 / 断言 / NOTE，没有把 FAIL 静默改绿，没有重跑上游构建管线。**

5 条扫描域 FAIL 的修法有两种，须你选择后才可执行：

- **甲（规格既定，推荐）**：四套旧门控的 `os.walk` 统一加上
  `node_modules/`、`dist/`、`.p0-build/`、`.workbuddy/` 排除，与 `p1-qa-spec.md` §2.6 `PB-*`、
  `verify_p0_gate.py` 现有口径一致；**同时补一条补偿断言**（依赖层单独扫、且明确不得作为产品层依据），
  保证覆盖面不缩水。改完后四套门控应回到 38/38、21/21、37/37、12/12。
- **乙**：不动旧门控，把它们整体标记为「P0 之前的历史套件、在 3D 主形态下不作验收依据」，
  终点判据只认路线 B 重定义套件（`verify_p1_gate.py` 实跑）+ 81 项原样保留 + 11 场 headless。
  此路径等价于**退役旧断言**，按 `p1-qa-spec.md` §0 第 28 行「不得借门控重写删断言」，需要你明确书面放行。

第 6 条 `verify_atlas_sprites.py` FAIL 的修法：把注入改成
`rally:{schemaVersion:2, unlocked:['U01','U02']}`，并把 `exit code` 与断言结果挂钩
（当前脚本 FAIL 却返回 0，属脚本自身缺陷）。**同样本轮未改。**

---

## §7 对发布的影响

- 按用户拍板的 **D6 终点 =「门控全绿 + 375px 可玩」**，当前 **「门控全绿」未达成**：
  四套旧门控 exit=1、`verify_p1_gate.py` 仍 SPEC_ONLY 未实跑。
- **375px 可玩已达成**：`verify_p1_visual.py` V2（375×780）与 V3（320×568）三车可见、
  无横向溢出、四项错误 0；`npm run headless` 11 场 ALL PASS 且 ≤180s。
- 因此 **Phase B（建仓 / 同源部署 / 上线 / commit）仍为阻断态**，须先按 §6 拍板并完成
  `verify_p1_gate.py` 实跑，再由你放行。本轮未部署、未上线、未 commit、未建 git 仓库。

---

*本报告只记录实跑事实与待办口径；所有 FAIL 原文、命中明细、退出码均已保留，未作任何放宽处理。*
