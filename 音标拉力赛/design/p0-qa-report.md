# P0 路线 B 门控重定义 · 独立实跑 QA 报告（#20b）

> **执行者**：quality-lead（严守真） · **执行日期**：2026-11-09 · **任务**：`#20b` 修正三处判据 + 按 P0 实产物实跑新门控
> **权威依据**：`design/p0-slice-spec.md`（用户四项拍板 / 三条裁决 / Go-No-Go 七项 / T1–T5）；`design/p0-qa-spec.md` **v1.3**（门控重定义规格 + 附录 A 判据修订）；`design/p0-impl-report.md` §9（engineering-lead 十项产物信息）；`design/hud-qa-plan.md`（串行纪律 / 四项错误计数 / 资源按字节校验 / CONCERNS 格式）；`design/stage-delivery-2026-11-09.md` §2.1 / §3（fan.mp3 瞬态与 R1–R11）。
> **独立声明**：以下全部数字为 QA **本机独立实跑**所得（7 轮日志 + `qa_p0_gate_result.json` 全部留存），**未复述 engineering-lead 自测数字**。前提事实（sha256 / 46 / N=3 / 33 处裸引用来源）均由 QA 自己读盘复核，见 §2。
> **质量门性质**：**advisory**。QA 给判定与阻塞项，**最终放行与发布签字由用户决定**；QA 不替用户拍板。
> **边界遵守**：未改五套既有验收脚本（sha256 与 P0 前快照全等）、未碰产品代码、未部署 / 未上线 / 未 commit。本轮写入物仅 4 个：`verify_p0_gate.py`（新门控脚本）、本文件、`p0-qa-spec.md` 的附录 A 修订、以及证据目录 `.workbuddy/backups/p0-evidence-20261109/qa/` 下的日志。

---

## 0. 质量门判定（结论先行）

> # 🟢 PASS（含 1 项已升级用户裁决的 CONCERNS）

| 维度 | 结果 |
| --- | --- |
| **新门控实跑** | ✅ **62 PASS / 0 FAIL / 62 TOTAL**，exit 0；**连续两轮（run6 / run7）完全一致，非 flaky** |
| **K1–K5 五类断言** | ✅ **逐条保留、缺一不可**，§6.3 覆盖映射表 5/5 满格，无空格、无降级 |
| **双层缓存 46 + N** | ✅ 源码层 `{'hud-20261108':46}` / 产物层 `VENDOR_TAG=p0-20261109` N=3 / 扫描根物理隔离 / 20 图零裸引用 |
| **dev + build 双模式** | ✅ 资源按字节送达 6/6 ×2、等价时序、2D 主形态、探针、四项错误计数全部两模式覆盖 |
| **四项错误计数** | ✅ `pageerror / 同源真实失败 / bad_status / 硬 console.error` **全 0**；外链环境项按 NOTE 单列（详见 §4，不豁免任何同源项） |
| **判定** | **PASS** —— 全部硬判据满足；判据修订均为「按事实改测法 / 修测试脚本自身缺陷」，经 §5 非放宽自检确证**无一处降级** |
| **CONCERNS（不阻塞本轮）** | **CN-4 / T3**：`dist/` 单目录发布时两站不同源、共享 `ipa-quest-v1` 不成立 —— **已升级用户裁决，本轮不判 PASS、不悄悄放行** |

**放行建议**：P0 门控实跑判 **PASS**（advisory）。但**发布放行**须先由用户裁决 CN-4 / T3；在用户裁决前，QA 不对「`dist/` 单目录发布形态」给出 PASS。质量门最终放行与发布签字由用户决定。

---

## 1. 实跑总表与编号体系

### 1.1 交付物与证据路径

| 类别 | 路径 |
| --- | --- |
| 新门控脚本（唯一新建可执行文件） | `音标拉力赛/verify_p0_gate.py`（733 行，AST 自检通过；7 轮修正后的最终形态） |
| 规格修订 | `音标拉力赛/design/p0-qa-spec.md` **v1.3**（附录 A：A.1/A.2/A.3 三处判据修订 + A.5/A.7 实跑修正 + A.6 非放宽自检 + **A.8 BR 探针取法确认**） |
| 本最终报告 | `音标拉力赛/design/p0-qa-report.md` |
| **证据目录（项目内，非 Temp）** | `.workbuddy/backups/p0-evidence-20261109/qa/` |
| 实跑日志（7 轮全留存，不覆盖） | `qa_p0_gate_run.log`（首跑）· `qa_p0_gate_run2.log` · `run3` · `run4` · `run5` · **`run6`** · **`run7`**（后两轮为最终全绿轮） |
| 结构化结果 | `qa_p0_gate_result.json`（62 条断言明细 + NOTE + CONCERNS） |
| 子项证据 | `qa_headless.log` · `qa_minimap_model.log` · `qa_dev_server.log` · `qa_preview_server.log` · `qa_probe_fields_verify.log`（BR 探针 14 字段独立实测） |
| 判定核心快照（只读对照） | `.workbuddy/backups/p0-pre-20261109/`（`file-hashes.json` 374 项 / `all_src_equal=true`） |

> 证据链目录由 engineering-lead 于本轮实跑前备妥（15:15 落盘，含其 `_p0_*` 自测产物），QA 日志落其子目录 `qa/`。**该目录是项目数据，不得当缓存清理。**

### 1.2 实跑合计（TOTAL 口径）

```
TOTAL_new = 62 项硬 chk（P0-0 + BD 7 + BC 6 + BV 14 + BI 6 + BQ 6 + BS 2 + BE 4 + BR 16）
          = 62 PASS / 0 FAIL / 62 TOTAL   （run6、run7 两轮逐条一致）
```
外加**非 chk 的实跑证据**：`node js/headless_laps.mjs` 11 场两圈 ALL PASS（max 174.57s ≤ 180s）、`minimap_model.test.mjs` 10/10（两者均在 BD-2 / BD-3 内作为硬判据承接）。

按域统计：`BD 7/7` · `BC 6/6` · `BV 14/14` · `BI 6/6` · `BQ 6/6` · `BS 2/2` · `BE 4/4` · `BR 16/16` · `P0-0 1/1`。

> **TOTAL 说明**：规格 §6.2 要求「不预设具体数字，等 P0 产物定型再定」。本轮产物定型（N=3、探针 4 组合、dev/build 双模式）后落地为 **62**。与原四套门控 110 项**不是同一编号体系**，不做数量对比；覆盖面守恒由 §6.3 映射表证明，而非数量。

---

## 2. 实跑前提事实（QA 独立读盘复核，不复述工程侧自测）

主理人给出的前提事实均**可直接采信**，QA 仍按纪律自行读盘复核一遍：

| # | 前提事实 | QA 独立复核结果 | 证据 |
| --- | --- | --- | --- |
| 1 | 判定核心 5 文件 sha256 与 P0 前快照逐字全等 | ✅ 5/5 全等（`race.js` `track.js` `config.js` `main.js` `headless_laps.mjs`） | `p0-pre-20261109/file-hashes.json` 逐项比对 |
| 2 | 五套验收脚本 sha256 全等（零改动） | ✅ 5/5 全等 | 同上；BD-1b |
| 3 | `data.js` / `ipa-display.js` 字节全等 | ✅ `25784ee12bd0f637…` / `0ce76227903f0fd5…` | BD-1c |
| 4 | 源码层 `{'hud-20261108':46}` 唯一 | ✅ 9 文件分布 17/6/1/3/2 + 7/7/2/1 = 46 | BC-1 |
| 5 | `VENDOR_TAG=p0-20261109`、N=3 | ✅ `vendor.manifest.json` 2 + `assets/probe-CoDaedyP.js` 1 | BC-2 |
| 6 | `build.outDir` 外置 `.p0-build/dist/` | ✅ 项目根下独立目录，与 QUEST/RALLY 扫描根物理隔离 | BC-3 `扫描根隔离=True` |
| 7 | `node_modules/` 仍在 `音标拉力赛/` 内 | ✅ 原口径全仓 **33 处裸引用全部来自 node_modules，非 node_modules 0 处**；白名单 9 文件裸引用 0 | BC-4 / BC-5 |
| 8 | 产物层残留源码 tag 8 处 | ✅ `index.html` 5 + `vendor.manifest.json` 1 + `assets/main-LrINXPEH.js` 2 | BC-3 detail 单列 |
| 9 | 源码层 9 文件不含 `VENDOR_TAG` | ✅ 0 命中 | BC-3 |
| 10 | dev 5173 / preview 4173 端口已释放 | ✅ 实跑前 FREE；脚本自行起服务、finally 显式 terminate，实跑后 `5173=FREE 4173=FREE` | P0-0 / run6 run7 尾行 |
| 11 | `__P0_PROBE__` 取法 / `fogType` 压缩陷阱 | ✅ 独立实测：`fogType` dev=`_FogExp2` / build=`K_`（陷阱真实）、`fogIsExp2` 两模式恒 `True`、14 字段齐全、8 项关键值达标、开关与根节点对齐 | `qa_probe_fields_verify.log` |

---

## 3. 三处判据修订（主理人派发）+ 实跑发现的两处修正

> 全部写入 `p0-qa-spec.md` **附录 A**（v1.3），**保留原判据 + 修正理由 + 可验证新判据 + 非放宽自检**，便于追溯。

| # | 判据 | 原判据 | 修订后（可验证形式） | 实跑结果 |
| --- | --- | --- | --- | --- |
| **A.1** | **BC-3 两层互不混算** | 「产物层扫描结果中不含 `hud-20261108`」 | 改为 **扫描根物理隔离 + 两层各自唯一且恰好（46 / N=3）+ 不同值 + 源码层不含产物 tag + 源码层无杂 tag** 六项；8 处残留逐文件单列披露、不计入 N、不作 FAIL 依据 | ✅ PASS（残留 8 处如实披露） |
| **A.2** | **BI-\* build 等价时序** | 按 DOM 字面顺序判（普通 script 在 module 之前） | **不按 DOM 顺序**；验实际执行时序：`Object.defineProperty` setter 同步捕获 `IPA_DISPLAY` 赋值瞬间的 `document.readyState=='loading'` + 48 键 + `U11='ɜr'` + `moduleDone`。build 下 DOM 顺序反了（module 提到 head 第 12 行、普通 script 在 173 行）但执行时序不变 | ✅ dev/build 双 PASS |
| **A.3** | **BV-0 先探兜底硬前置** | 流程建议，未写成 chk | 升格为独立硬 `chk` + 显式门闩 `FALLBACK_PROBED[mode]`（BV-1 起必须校验）；**关键澄清**：探测到 `200 text/html` 不判 FAIL（dev 对不存在路径的 SPA fallback 是 Vite 正常行为），真正防陷阱的是 BV-1 每个真实资源的 `CType 非 text/html + magic + sha256 + 逐字节` 四重判定 | ✅ dev/build 双 PASS（BV-0 均登记 `存在兜底200HTML=True`） |
| **A.5** | **BQ-2 探针 overlay 短词子串假阳性**（实跑发现） | 沿用 H5 子串口径扫探针 overlay | 检测面**未缩小**（仍 `textContent` + 后代所有属性值）、词表**未缩小**（83 全表 + 4 字段名）、**不退回 innerHTML**；判据改「完整词边界匹配 + IPA 斜杠形式硬断言」，子串命中逐条单列披露。根因实证：`lock ⊂ display:block`、`me ⊂ frames`、`sit ⊂ position:position`，词边界零命中 | ✅ dev/build 双 PASS |
| **A.7** | **BE-1 / K5 外链派生 console.error 分类完备化**（实跑发现，主理人派单已明确口径） | `console_error == 0` 单一标量 | 拆为 `pageerror/bad_status/同源真实失败/非派生 console.error == 0` 四项硬归零（**逐字保留**）+ 外链派生条目的**计数配对 + `ConsoleMessage.location.url` 外部 host 校验**两重证明；**不豁免任何同源项** | ✅ 4/4 场景 PASS |
| **A.8** | **BR-2 探针纸雾取法确认**（非判据修订；工程实测提醒 + QA 独立实证） | 规格 §3/§7 草案「`FogExp2` 纸雾可见 / 帧缓冲非空像素」 | 实跑落地为 `__P0_PROBE__.fogIsExp2` **布尔** + 8 项状态字段；独立实测 `fogType` dev=`_FogExp2`/build=`K_`（**压缩陷阱**）、`fogIsExp2` 两模式恒 True；脚本零 `fogType` 字符串 → **判据无需改、无需重跑**，长期禁用压缩敏感标识 | ✅ 取法对齐，`62/0/62` 不变 |

**A.6 非放宽自检（5 项全过）**：五处修订均「未删断言 / 未放宽阈值 / 未跳过浏览器实跑 / 未把 FAIL 改 NOTE」，强度全部 **↑ 更严**（BC-3 新增 2 项约束、BI-* 从字符串比较升级为运行时实证、BV-* 新增 BV-0 + 门闩、BQ-2 新增 IPA 硬断言 + 诊断披露、BE-1 新增两重配对证明）。§6.3 K1–K5 映射表、K4 的 H5 检测面口径、K5 归零口径一律未改。

---

## 4. K1–K5 五类断言逐条结果（§6.3 覆盖映射表填满）

| 类别 | `p0-slice-spec.md` §1 要求 | 新门控承接编号 | 原断言 | 强度对比 | 满格 |
| --- | --- | --- | --- | --- | --- |
| **K1** | 判定核心确定性（两圈 / 门线 `g.line` / 听音题正确性 / 11 场 headless ≤180s） | `BD-1` `BD-1b` `BD-1c` `BD-2` `BD-3` `BD-4[dev/build]` | S1–S8/S13/A0–A6/U6/U8/H10/T0–T7 | ≥ 原（新增五文件 sha256 零改动证明 + dev/build 双模式主形态实跑） | ✅ |
| **K2** | 跨站 `localStorage['ipa-quest-v1']` 单键保真（C08 白名单 / `rally` 不互相覆盖） | `BS-1[dev/build]` + `BD-1b`（store.js 等逻辑源码零改动） | D1–D6 / U10/U11 / F11a/F11b / H12 | ≥ 原（零写盘 + 键集合守恒 + 逻辑源码逐字未改；`dist/` 形态同源结论见 CN-4） | ✅ |
| **K3** | 美式 IPA 单一显示源 `window.IPA_DISPLAY` / `sym` 稳定键 | `BI-1[dev/build]` `BI-2[dev/build]` `BI-3[dev/build]` `BD-1c` | F1/F1b/F2/F5/F9a/F9b/B2/B9/D7.4/H11 | ≥ 原（新增等价时序运行时打点；DOM 顺序仅诊断） | ✅ |
| **K4** | quiz 答案零泄露（83 词全表 + 4 字段名不出现在 HUD DOM） | `BQ-1` `BQ-1b` `BQ-2[dev/build]` | H5/H6/H8/U8/S11 | ≥ 原（BQ-1 沿用 H5 最严子串口径 + 新增 IPA 硬断言；**新增探针 overlay 检测面**） | ✅ |
| **K5** | 四项错误计数归零（ERR_ABORTED 单列 / 同源真实 0 / 外链单列） | `BE-1[dev/build × 2D/探针]`（4 条） | U1/U12/F11d/D7.5/H12 | ≥ 原（新增 Vite 机制项分类、外链派生 console.error 配对证明；**同源真实失败仍必须=0**） | ✅ |

> **5/5 满格，无空格**。任一格空格即判 FAIL（§0.3 覆盖度守恒律），本轮无此情形。

### 4.1 K1 判定核心（7/7）

| 断言 | 结果 | 关键证据 |
| --- | --- | --- |
| BD-1 判定核心 5 文件 sha256 全等 | ✅ | `race/track/config/main/headless_laps` 与 `p0-pre-20261109` 逐项 EQ |
| BD-1b 五套脚本 sha256 全等 | ✅ | 零改动 |
| BD-1c `data.js` / `ipa-display.js` 字节全等 | ✅ | 权威表未动 |
| BD-2 `node js/headless_laps.mjs` 原路径原命令 | ✅ | **11 场 ALL PASS，min 135.8s / max 174.57s ≤ 180s**，`题库: 地图 4 词对 37 词 83 题型 3` |
| BD-3 `minimap_model.test.mjs` | ✅ | `10 PASS / 0 FAIL / 10 TOTAL` |
| BD-4[dev] / [build] 2D L0 主形态 | ✅ | 双模式 `mode='title'` / `__rally` / `#c` / `#minimap` / `#minimap-c` 全就绪 |

### 4.2 K2 跨站单键（2/2）

`BS-1[dev]` / `BS-1[build]`：`step(60)` 期间 `Storage.prototype.setItem` 增量 **0**、键集合不变、`rally` 字段守恒（`same=True`）。逻辑源码（store.js 等）由 `BD-1` 系列 sha256 证明逐字未改，C08 白名单 / 并集 / last-write-wins 逻辑沿用 #5 已验的 37 项 D 门控。**`dist/` 形态的同源前提见 CN-4**，本轮不判 PASS、不悄悄放行。

### 4.3 K3 IPA 单一显示源（6/6）

| 断言 | dev | build | 关键证据 |
| --- | --- | --- | --- |
| BI-1 非 module / 无 defer / 无 async | ✅ | ✅ | `type=None, defer=False, async=False` |
| BI-2 等价时序 | ✅ | ✅ | `IPA_DISPLAY` 首次赋值 `readyState='loading'`、`keys=48`、`U11='ɜr'`、`moduleDone=True`；**DOM 顺序诊断 = `script在module后`（build 下反了，但仅诊断、不计判定）** |
| BI-3 48 卡面美式 / 字节全等 | ✅ | ✅ | `ipa-display.js` sha256 `0ce76227903f0fd5…` 与快照全等 |

> 这一条正是 A.2 修订的价值：若按原「DOM 顺序」判据，build 会伪 FAIL；改为实际执行时序后双模式全绿，且证据从「字符串比较」升级为「同步 setter 捕获赋值瞬间的 readyState」。

### 4.4 K4 答案零泄露（6/6）

| 断言 | 结果 | 关键证据 |
| --- | --- | --- |
| BQ-1（×2 模式）2D HUD | ✅ | 词表 **83**（`len==83 and set==83` 守卫过）、字段名 4 个、**子串命中 `[]`**、IPA 斜杠命中 `[]`、中文答案域 `[]`、禁用 `data-*` `[]`；检测面仅 43 字符；`innerHTML` 假阳性证据 `['pan']` **仅诊断、不计判定**（#5 裁决口径） |
| BQ-1b（×2）词表完整性守卫 | ✅ | 83 / 83 |
| BQ-2[dev/build] 探针 overlay | ✅ | 完整词命中 `[]`、IPA 命中 `[]`、禁用属性 `[]`；子串命中 `['lock','me','sit']` **逐条单列披露**（实证根因：`lock⊂display:block` / `me⊂frames` / `sit⊂position:relative`，均非答案载体） |

> **未退回 `innerHTML`、未缩小 83 词表、未降级为 warn**：BQ-1 保持 H5 最严子串口径；BQ-2 因探针页含 R3F 注入 CSS / 调试状态文本改用完整词 + 新增 IPA 硬断言（A.5）。

### 4.5 K5 四项错误计数（4/4）

| 场景 | pageerror | bad_status | 同源真实失败 | 硬 console.error | ERR_ABORTED | 外链环境 | Vite 机制 | 判定 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dev × 2D 主形态 | 0 | 0 | **0** | 0 | 0 | 0 | 0 | ✅ |
| dev × 探针 | 0 | 0 | **0** | 0 | 0 | 0 | 0 | ✅ |
| build × 2D 主形态 | 0 | 0 | **0** | 0 | 0 | 0 | 0 | ✅ |
| build × 探针 | 0 | 0 | **0** | 0 | 0 | 0 | 0 | ✅ |

**（上表为最终全绿轮 run6 / run7）**。过程透明披露见 §5：run5 曾真实复现主理人预告的 dev 外链 `ERR_CONNECTION_CLOSED`（`同源真实失败=0`、`bad_status=0`），并派生 1 条 `console.error`；按 A.7 分类完备化后单列 NOTE、不豁免任何同源项。**最终两轮外链事件未复现（外链环境=0），四项错误计数严格全 0。**

外链字体（`fonts.googleapis.com` / `gstatic.com`）为已知环境项（T5 / 阶段交付 R 系列），按 §1 K5 既有口径 NOTE 单列；资源送达另由 BV 四重判定覆盖，**不信状态码**。`requestfailed` 明细逐条分类为 `ERR_ABORTED / 同源真实 / 外链环境 / Vite 机制` 四类并打印，**不混入 FAIL、不静默吞**。

---

## 5. 过程记录（7 轮实跑，全部日志留存，透明披露）

> 首跑→全绿共 7 轮。**所有 FAIL 均定位为「测试脚本自身 bug / flaky / 判据与构建事实不符」，无一是产品缺陷**；每处修正都写进 `p0-qa-spec.md` 附录 A 并做非放宽自检。QA **未改任何产品代码、未改五套既有脚本、未放宽任何硬判据**。

| 轮次 | SUMMARY | FAIL 内容 | 定位与处置 |
| --- | --- | --- | --- |
| run1 | 57 / 5 / 62 | `BR-1` ×4 取到 `None`；`BE-1[build][2D]` 404 | ① `add_init_script` 传了**未调用的箭头函数** → 改立即执行 IIFE；② `do_bq` 浏览器 `import('/js/config.js?v=...')` 在 build 下命中 SPA fallback 返回 `200 text/html`，制造 `bad_status=1` 假阳性 → 改 Node 直读源码 `config.js` 取 83 词（两模式统一）。均为脚本 bug |
| run2 | 60 / 2 / 62 | `BQ-2` ×2 命中 `lock/me/sit` | 抓检测面原文实证为**短词子串假阳性**（`lock⊂display:block` 等），与 #5 `<span` 撞 `pan` 同类 → A.5：完整词匹配 + IPA 硬断言 + 子串逐条披露 |
| run3 | 58 / 4 / 62 | `BR-4` ×4 `rally=False`（URL 已正确跳回） | 固定 `wait_for_timeout(700)` 在 dev 首加载时不足，`__rally` 未挂载即读值 → 改 `wait_for_function` 条件等待（§5.4 flaky 隔离纪律） |
| run4 | 61 / 1 / 62 | `BI-2[build]` 时序打点 `None`（本体 `ready/keys/u11/moduleDone` 全 True） | `setInterval` 轮询在解析阶段偶发抢不到 tick → 改 `Object.defineProperty` setter **同步捕获赋值瞬间**，无竞态 |
| run5 | 61 / 1 / 62 | `BE-1[dev][2D]` `console_error=1` | **主理人预告的 dev Google Fonts `ERR_CONNECTION_CLOSED` 真实复现**：同源真实失败=0、bad_status=0、外链环境=1，浏览器派生 1 条 `console.error`。暴露 K5 分类不自洽 → A.7：外链派生项按「计数配对 + `location.url` 外部 host 校验」单列 NOTE，**四项硬归零保留、不豁免任何同源项** |
| **run6** | **62 / 0 / 62** | — | 全绿，exit 0 |
| **run7** | **62 / 0 / 62** | — | 独立复跑，**59 条可比对断言名称集合与判定逐条全一致**、零差异 → 结论非 flaky |

**与 fan.mp3 瞬态口径的一致性**：`hud-qa-plan.md` §5.3 / `stage-delivery` §2.1 记录的 `fan.mp3 → ERR_CONNECTION_REFUSED` 启动瞬态，本轮按同一纪律处理 —— 不放宽断言、不改脚本、不视为产品缺陷，串行跑 + 服务用完显式 `terminate()` + 端口复核（`5173/4173 FREE`）；本轮 `fan.mp3` 在 BV-1 dev/build 两次按字节送达均全等（9792 B，`9e1273a238fdb68d…`），**未复现该瞬态**。Vite 机制项（`/@vite/client`、HMR WS、`/@fs/`、`/@id/`、`.vite/deps`）本轮实测均为 0 次请求，仍按分类表单列登记。

---

## 6. 双层缓存 / 资源送达 / 探针 / 时序 逐项表

### 6.1 BC 双层缓存（6/6）

| # | 断言 | 结果 | 实测 |
| --- | --- | --- | --- |
| BC-1 | 源码层 9 文件 `?v=` 唯一且恰好 46 | ✅ | `{'hud-20261108': 46}`（17/6/1/3/2 + 7/7/2/1） |
| BC-2 | 产物层 `VENDOR_TAG` 唯一且 N=3 | ✅ | `vendor.manifest.json` 2 + `assets/probe-CoDaedyP.js` 1 |
| BC-3 | 两层互不混算（A.1 修订） | ✅ | 扫描根隔离 True / 46 / N=3 / 不同值 / 源码层不含 `p0-20261109` / **产物层残留 `hud-20261108` 8 处单列披露**（`index.html` 5 + manifest 1 + bundle 2） |
| BC-4 | 20 图零裸引用（含 `assets/img/+变量` 拼接型） | ✅ | 白名单 9 文件裸引用 **0** |
| BC-5 | 原口径全仓裸引用来源诊断 | ✅ | **33 处全部来自 `node_modules/`，非 node_modules 0 处**（印证 F-01/F-02 失效预判） |
| BC-6 | vendor.manifest 版本钉定 | ✅ | `three=0.186.1`、`VENDOR_TAG=p0-20261109`、`source_layer.count=46`、`pinned=9`、`peer_verified=5` |

> 原 S17/F8a/H11 的**全仓口径**在构建链下不适用（产物层 8 处残留 + `node_modules` 污染）；改由 BC-1..BC-5 两层各扫各的，**强度不降**（仍各自唯一、各自恰好）。

### 6.2 BV 资源按字节送达 dev + build（14/14）

**BV-0 硬前置（×2）**：先探不存在路径 `__qa_missing_9f3a.webp`，dev/build 均登记 `status=200, ctype=text/html, 存在兜底200HTML=True` → 据此锁定「**状态码一律不可信，BV-1 起只按四重判定**」。这正是 §3.1 防 Caddy/Vite 兜底 200 陷阱的核心，且不因「探测到兜底」误判 FAIL（A.3）。

| # | 资源 | 字节 | dev | build | 四重判定 |
| --- | --- | --- | --- | --- | --- |
| 1 | `音标大闯关/js/ipa-display.js` | 3822 | ✅ | ✅ | 逐字节全等 / `text/javascript` / 非 text/html / sha256 `0ce76227903f0fd5…` |
| 2 | `音标大闯关/assets/img/a1.webp` | 355002 | ✅ | ✅ | `image/webp` / `RIFF....WEBP` / sha256 `25532a2616ef1a87…` |
| 3 | `音标大闯关/assets/sprites/U01.webp` | 64670 | ✅ | ✅ | `image/webp` / magic / `c27427191d2c709b…` |
| 4 | `音标大闯关/assets/sprites/U02.webp` | 64356 | ✅ | ✅ | `image/webp` / magic / `d1753bd9c03c03ba…` |
| 5 | `音标大闯关/assets/sprites/cards/U01.webp` | 19244 | ✅ | ✅ | `image/webp` / magic / `5fb52dc2d22bb984…` |
| 6 | `音标拉力赛/audio/fan.mp3` | 9792 | ✅ | ✅ | `audio/mpeg` / MP3 帧头 / `9e1273a238fdb68d…` |

> 6 项 × dev/build = 12 条 BV-1 + 2 条 BV-0 = 14/14。**资源送达经真实 HTTP 服务取 body 与磁盘逐字节比对**（非静态复制比对），中文路径 percent-encode，不信状态码。工程侧另有全量 339/339 逐字节证据，QA 本轮以 HTTP 送达口径独立覆盖代表性资源集（跨站 JS / 立绘 / 卡面 / 音频）。

### 6.3 BR 探针（16/16，dev/build × 375×780 / 320×568 × 4 检查）

| 检查 | 结果 | 实测 |
| --- | --- | --- |
| BR-1 默认关闭（×4） | ✅ | 主站 `getContext('webgl*')` 计数 **0**，hook 生效，`__rally` 就绪；主站不加载 `probe.jsx` |
| BR-2 探针开启（×4） | ✅ | `webgl=True` / `WebGL2` / `fogIsExp2=True` / `fogDensity=0.045` / `boxCount=1` / `lightCount=1` / `drawCalls=1` / `frames>3` / `contextLost=False` / `errors=[]` / `tag=p0-20261109` |
| BR-3 `#probe-toggle` 关 3D（×4） | ✅ | `mounted=False`、Canvas 卸载、`aria-pressed=false` |
| BR-4 `#probe-back` 关回 2D（×4） | ✅ | URL 回到 `/index.html`（dev 5173 / build 4173）、`__rally` 就绪、探针状态不存在 |

> 探针为**独立入口 `/probe.html`**、默认关闭、不进主循环、不写 localStorage、不消费判定结果（工程侧 §9-4），BR-1 的 WebGL hook 实证了「不打开 /probe.html 即零 WebGL 上下文」。

#### 6.3.1 BR 探针取法的独立实测对齐（回应 engineering-lead 实测提醒）

> 实跑收尾阶段 engineering-lead 直接提供 `__P0_PROBE__` 14 字段精确取法，重点提醒 **`fogType` 受 Vite minify 影响不可作判据**。QA 按「独立复核、不复述自测」纪律，自起 dev/preview 服务用真实 Chromium 读字段复核（证据 `qa_probe_fields_verify.log`）：

| 核验项 | dev | build | 判定 |
| --- | --- | --- | --- |
| `fogType` | `'_FogExp2'` | `'K_'` | 压缩陷阱实证：类名被改写，跨模式不稳定 |
| `fogIsExp2` | `True` | `True` | 布尔恒真，唯一稳定判据（BR-2 即采用此项） |
| 14 字段 | 0 缺失 | 0 缺失 | 含 `webglVendor` / `webglRenderer` / `fogDensity` / `drawCalls` 等 |
| 8 项关键值 | 全达标 | 全达标 | `tag=p0-20261109` `WebGL2` `contextLost=False` `boxCount=1` `lightCount=1` `drawCalls=1` `fogDensity=0.045` `errors=[]`；`frames=102` |
| 开关 / 根节点 | 达标 | 达标 | `#probe-toggle` `aria-pressed=true`、`#probe-back` `href=./index.html`、`#probe-status` role/aria-live 就绪 |
| 主站默认关闭 | — | — | `index.html` 不引用 `probe.jsx` / bundle，`#minimap` 在 |

**结论**：`verify_p0_gate.py` 全文零 `fogType` 字符串（BR-2 第 546/553 行用 `s["fogIsExp2"]` 布尔），开关取法（`#probe-toggle` → `mounted is False and not canvas`、`#probe-back` → `/index.html`）与实测逐项对齐 → **判据无需修改、无需重跑 62 项门控**，run6 / run7 `62/0/62` 结论不变。规格附录 A.8 已登记长期约束：P1 及后续禁止用 `fogType` / 类名字符串 / `constructor.name` 作判据，纸雾一律用 `scene.fog.isFogExp2` 布尔。

### 6.4 服务与串行纪律

- 脚本自起 dev(5173) / preview(4173)，`wait_port` 就绪后串行跑，**浏览器门控不并行**（沿用 `hud-qa-plan.md` §1）。
- `finally` 显式 `terminate()` + 端口复核：**7 轮全部 `5173=FREE 4173=FREE`**，无残留服务。
- run6 / run7 耗时 44.0s / 36.7s；`headless` 11 场另由 BD-2 单独实跑（原路径原命令）。

---

## 7. CONCERNS / NOTE 登记

### 7.1 CONCERNS（1 项，不判 PASS、不悄悄放行）

| # | CONCERNS | 性质 | 影响 | 处置 | 需裁决 |
| --- | --- | --- | --- | --- | --- |
| **CN-4** | **T3：`dist/` 单目录发布时两站不同源、共享 `ipa-quest-v1` 不成立** | 部署形态风险（**已升级用户裁决**） | 阻塞「`dist/` 单目录发布」形态的放行 | 按现有 `音标大闯关/deploy.sh` 源码 scp 双站同级 → 同源成立（P0 产物不进发布目录，不受影响）；改 `dist/` 单目录发布则 `dist` 内**不含完整大闯关站**（仅 `assets/` + `js/ipa-display.js`），跨站跳转 `../音标大闯关/index.html#/map` 会断、共享 `localStorage` 前提不成立 → 须把**完整大闯关站一并放到同一 origin 同级目录**并复核相对路径。P0 未改 `deploy.sh`、未部署、未上线 | **是（用户）** |

> 主理人已明确该项升级给用户裁决。本轮**不判 PASS、不悄悄放行**：报告整体判 PASS 仅针对「P0 门控实跑」这一范围，**不代表对 `dist/` 单目录发布形态的放行**。

### 7.2 NOTE（最终全绿轮 0 条；过程轮已登记并留存）

| # | NOTE | 出现轮次 | 口径 |
| --- | --- | --- | --- |
| BE-2 | 外链环境项（Google Fonts `ERR_CONNECTION_CLOSED` + 派生 `console.error`） | run5 | A.7：计数配对 + `location.url` 外部 host 校验后单列；**同源真实失败仍须 = 0**（实测 0） |
| BE-3 | `ERR_ABORTED` / Vite 机制项 | run1 | 单列披露、不计失败、不静默吞 |
| BQ-2 | 探针 overlay 短词子串假阳性 `lock/me/sit` | run2 起（作为 detail） | 逐条单列披露实证根因，硬判据为完整词 + IPA |

> **FAIL 改 NOTE 一律禁止**（X4）。上述 NOTE 只承载「已核实的环境项 / 记录项 / 可解释诊断项」，不承载任何硬失败。

### 7.3 顺延登记的既有遗留风险（不阻塞本轮）

| # | 风险 | 来源 |
| --- | --- | --- |
| R1 | C07-B 前 / C08 resume 前历史 diff 能力永久丧失，改由「不回退 + sha256 全等」保证 | #18 / `hud-final-qa-report.md` |
| R2 | `hud-20261109/` 是 #4 之后状态，仅能回滚后续改动 | 同上 |
| R3 | `.workbuddy/backups/` 属项目数据，**不得当缓存清理**；删除会摧毁 F3/F6a/F6b/D9.2 证据链 | 同上 |
| R4 | `data.js` 后续变更须同步基线并重跑，否则 F6a 判红是预期的防漂移行为 | 同上 |
| R7 | 3D 数据陷阱：`config.js` 的 `length/tone/color` 是 A/B 分组着色键，不得进入 3D 几何/材质/教学参数，也不得「修」或重命名 | 阶段交付 §3 R8 |
| R-new1 | `node_modules/` 仍在扫描根内，**原生五套脚本不可直接跑**（A 口径 S17 会 False）；正式解（工程根上提）建议 P1 单独立项 | `p0-impl-report.md` §6.3 / R2 |
| R-new2 | 探针 bundle 1.15 MB（gzip 320 kB）触发 Vite `>500 kB` 警告；帧时间仅 SwiftShader 软件渲染间接值，无真机 GPU 剖析 | `p0-impl-report.md` §11 R5/R6 |
| R-new3 | 项目无 git 仓库，回滚依赖手工快照 | 阶段交付 R10 |
| R-new4 | `fogType` 受 Vite minify 影响（dev `_FogExp2` / build `K_`），**P1 扩展探针断言时禁止用类名字符串作判据**，纸雾须用 `fogIsExp2` 布尔；规格附录 A.8 已登记长期约束 | `qa_probe_fields_verify.log` / `p0-qa-spec.md` A.8 |

---

## 8. 判定记录表（实跑填写）

| 项 | 结果 | SUMMARY / 证据 |
| --- | --- | --- |
| 实跑前提（§2 十项） | ✅ 全部独立复核通过 | sha256 / 46 / N=3 / 33 裸引用来源 / 隔离 / 端口 |
| 三处判据修订（A.1/A.2/A.3）+ 两处实跑修正（A.5/A.7） | ✅ 写入 `p0-qa-spec.md` 附录 A（v1.3），原判据与理由全保留 | A.6 非放宽自检 5/5「↑ 更严」 |
| K1 判定核心 | ✅ PASS | BD 7/7；11 场 ALL PASS max 174.57s；单测 10/10 |
| K2 跨站单键 | ✅ PASS | BS 2/2 + 逻辑源码 sha256 零改动（同源前提见 CN-4） |
| K3 IPA 单一显示源 | ✅ PASS | BI 6/6；等价时序 dev/build 双实证 |
| K4 答案零泄露 | ✅ PASS | BQ 6/6；83 词全表守卫、H5 口径、不退回 innerHTML |
| K5 四项错误计数 | ✅ 归零 | BE 4/4；`pageerror/同源真实/bad_status/硬console_error` 全 0 |
| §6.3 K1–K5 覆盖映射 | ✅ **5/5 满格** | 无空格、无降级 |
| BC 双层缓存 | ✅ PASS | 6/6；46 / N=3 / 隔离 / 20 图零裸引用 |
| BV 资源按字节送达 dev+build | ✅ PASS | 14/14；BV-0 硬前置 + 门闩 + 四重判定 |
| BR 探针 | ✅ PASS | 16/16；默认关闭 / 两视口 WebGL / 关回 2D |
| 串行纪律 / 端口释放 | ✅ 通过 | 7 轮全部 `5173=FREE 4173=FREE` |
| 稳定性（非 flaky） | ✅ 通过 | run6 = run7 = `62/0/62`，59 条断言逐条一致、零差异 |
| BR 探针取法独立实测对齐 | ✅ 通过 | `qa_probe_fields_verify.log`：14 字段齐全 / `fogType` 压缩差异实证 / `fogIsExp2` 恒 True / 开关与根节点对齐 → 无需改判据、无需重跑 |
| **质量门判定** | 🟢 **PASS** | 硬判据全满足；**CN-4 / T3 作为 CONCERNS 升级用户裁决，不判 PASS、不悄悄放行**；advisory，最终放行由用户决定 |

---

## 9. 边界、回滚与 Handoff

- **未改**：五套既有验收脚本（BD-1b sha256 全等）、任何产品代码（`js/` / `index.html` / `css/` / 图片 / `data.js` / `ipa-display.js` / `deploy.sh` / 上游管线）、`vite.config.js` / `vendor.manifest.json` / `probe.html` / `probe.jsx`（均为 engineering-lead #19 产物，QA 只读）。
- **本轮写入物**：`verify_p0_gate.py`（新门控）、`design/p0-qa-spec.md`（附录 A 修订，v1.3）、`design/p0-qa-report.md`（本文件）、证据目录 `p0-evidence-20261109/qa/` 下 7 轮日志与 JSON。
- **未部署、未上线、未 commit、未建 git 仓库**。
- **回滚**：`.workbuddy/backups/p0-pre-20261109/`（`manifest.txt` 43242 B / `file-hashes.json` 76296 B / 374 文件）为 P0 改动前全量快照，**属项目数据不得清理**；按 manifest 相对路径 copy 回源根、逐文件按 sha256 前 16 位复核，回滚后重跑 `node js/headless_laps.mjs` 11 场 + 源码层 46 断言确认回到 2D L0 基线。
- **发现的缺陷**：本轮 5 个 FAIL 全部定位为测试脚本自身 bug / flaky / 判据与构建事实不符，**无产品缺陷**，无需回派 engineering-lead。
- **待用户/主理人决定**：① **CN-4 / T3 部署形态裁决**（`dist/` 单目录 vs 现有 `deploy.sh` 双站同级）；② 最终放行与发布签字（质量门 advisory）。
- 所有产出经主理人中转；QA 与 engineering-lead 仅就「证据链目录就绪 + 判据取法」直接协调（协作规则允许），未越界分派任务。收尾阶段收到其 `__P0_PROBE__` 字段与 `fogType` 压缩陷阱提醒后，QA **独立起服务实测复核**（非复述自测），确认判据无需修改，见 §6.3.1 / 附录 A.8。

---

*报告结束 · 质量门 🟢 PASS（62/0/62，连续两轮一致）· 五类断言 K1–K5 逐条保留、映射表 5/5 满格 · 三处判据修订 + 两处实跑修正均经非放宽自检 · 唯一 CONCERNS = CN-4/T3 已升级用户裁决、不判 PASS 不悄悄放行 · 证据落 `.workbuddy/backups/p0-evidence-20261109/qa/` · BR 探针取法独立实测对齐（附录 A.8，判据无需修改）· 最终放行由用户决定*
