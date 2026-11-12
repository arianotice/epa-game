# P1 门控规格与 3D 主形态终点验收判据（#31）

> **文档性质**：quality-lead（严守真）独占产出。**P1 代码落地前的验收规格与判据清单**，本轮**只出规格、不实跑、不改产品代码、不改五套既有验收脚本**；实跑待主理人另行通知。
> **日期**：2026-11-10 · **版本**：**v1.1**（并入主理人 2026-11-10 两批 P1 门控口径裁决 + design-strategist #29 交叉复核 C1/C2/C3 回执）· **任务**：`#31`（与 `#28` engineering-lead 实现、`#29` design-strategist 规格、`#30` art-director 视觉规格并行，文件不重叠）
> **权威依据**：`design/kart-visibility-diagnosis.md`（2026-11-10 用户拍板 D1–D6 / 发布前置 C1–C6 / §2 发布阻断判定）；`design/p0-slice-spec.md` §1 三条裁决 / §2 Go-No-Go；`design/p0-qa-spec.md` **v1.3**（62 项新门控、K1–K5、失效清单 12 族 / 29 重定义 + 81 保留、附录 A）；`design/p0-qa-report.md`（🟢 PASS 62/0/62）；`design/hud-qa-plan.md`（串行纪律 / 四项错误计数 / 资源按字节 / V1–V17 / DPR）；`design/stage-delivery-2026-11-09.md` §3 R1–R11（R8 3D 数据陷阱为 P0 阻断级）；`design/3d-tech-feasibility.md` §4.5 六条隔离断言 / §8 P1–P2 Go-No-Go / §M1 / §554；`design/3d-adr.md` §396-399；`design/visual-direction-3d.md` v1.1 §B.1 / §261；`design/visual-direction-3d-v2.md` §M6 / §262 / P8；**`design/p1-gameplay-spec.md`（#29，699 行，D4 权威映射表 + D3/D6 产品语义，按 `D3-Axx/D4-Axx/D6-Gxx` ID 引用）**；**`design/p1-3d-art-spec.md`（#30，六维阈值 §5 / 光照 §4.8 / 防泄题 §6.7 / provenance）**。
> **关键状态声明（v1.1 按主理人裁决 8 修订）**：用户上一轮问卷**已拍板 D6 终点 =「门控全绿 + 375px 可玩」**，不是未拍板；本规格的职责是把这句**已拍板的终点定义**可执行化为逐条 Go/No-Go 与硬 `chk`，**不得替换、不得重开、不得另立第三套口径**（design-strategist `p1-gameplay-spec.md` §3.5 三候选已归档为历史候选，甲 = 已拍板口径、乙 / 丙作废）。**仍待用户裁决**的是终点达成**之后**的执行项：2D L0 退役时点 / 是否收敛为单一 3D 形态 / 保留期（G10）、G8 发布前置与最终放行签字；**G9 为上线后观察项 / advisory，不计入 G1、不作发布阻断**。质量门 **advisory**，最终放行与发布签字由用户决定。

---

## 0. 规格定位与红线

### 0.1 任务来源（不重新论证）

| 来源 | 内容 |
| --- | --- |
| 主理人 `#31` 派单 | 把用户问卷终点「**门控全绿 + 375px 可玩**」变成真验收，而不是口号；在 P0 `verify_p0_gate.py` **62 项 / K1–K5** 基础上扩展，五类断言缺一不可、**重定义 ≠ 降级**；新增 7 族硬判据；登记发布前 C2–C6 验收方式 |
| **主理人补充裁决 A（门控口径）** | 「门控全绿」= **路线 B 重定义套件（本规格 P1 套件：K1–K5 + 硬判据族）+ 81 项原样保留断言 + `js/headless_laps.mjs` 11 场 ALL PASS**；失效断言逐条给重定义依据、禁止静默放宽，主理人逐条复核。**不得写成「原始 110 项原样全绿」**——Vite/R3F 构建链下其中 29 项已物理失效（#20/#27 F-01~F-12）。#29 R4 按此关闭 |
| **用户 2026-11-12 书面裁决 D（#45 退役令）** | 「四套旧门控整体退役。跑判据，继续任务，可以部署在我设置的 GitHub 仓库上」= `p1-legacy-gate-fail-scan.md` §6 **乙**。**退役的是「旧套件作为发布阻断判据的地位」，不是删 81 项断言**：81 项期望值逐字不改、迁移到新 P1 套件用正确扫描域重放，逐条承接编号 `PLR-*` 见 `design/p1-gate-retirement.md` §3（81 行零空白）；四套 `exit code` 不再计入 G1。门控全绿新口径见该令 §5 |
| **主理人补充裁决 B（视觉 / 降级 / 零答案域 / 六维 / D4 / 边界）** | 见 §0.5 逐条落地表；含光照断言单独定义（不复用 P0 `lightCount=1`）、WebGL 降级 L0 不白屏、3D 层零答案域读取、六维阈值可执行化、D4 教研校验具体化、#29 边界（按 ID 引用不复述语义） |
| **主理人补充裁决 C（终点）** | 用户已拍板 D6 终点 =「门控全绿 + 375px 可玩」；#29 §3.5 三候选已归档为**历史候选**（甲 = 已拍板口径，乙 / 丙作废），不得替换用户口径，也不得据此把 G10 写成「终点未拍板」 |
| 诊断文档 §3 D1–D6 | D1 放行部署/上线/commit（受 C1–C6 前置约束）· D2 允许社区模型（需逐模型 provenance）· D3 **核心玩法保持「听音选车道」** · D4 **六档稀有度绑定发音特征复杂度** · D5 允许改 2D 立绘标志性造型 · D6 **3D 成为主形态设终点，推翻「2D 永不删除」默认** |
| 诊断文档 §2 C1–C6 | 发布前置六项；质量门判定 **CONCERNS（发布阻断）**；C1「3D 卡丁车未实现」由 P1 解决，本规格不判 C1 |
| 诊断文档 §1 | 三种本地入口下 **2D 玩家车 + 2 NPC 均可见**、`pageerror/console_error/requestfailed` 全 0、里程 541→597；`probe.html` 仅 1 立方体；线上入口错配 + Caddy 兜底 200 |
| `p0-slice-spec.md` §1 裁决 3 | 允许重定义的是**测法**，不是覆盖面；五类断言逐条保留，缺一不可 |

### 0.2 三条不可协商红线

1. **判定核心零改动（最高优先级）**：`js/race.js` / `js/track.js` / `js/config.js` 逐字不改；`node js/headless_laps.mjs` **原路径原命令** 11 场 ALL PASS、最慢 ≤180s 是 Go/No-Go 硬条件。3D 只能通过 `snapshot()` **只读**判定结果，不得进 React state、不得由 rAF 驱动判定、不得移植 TS。
2. **重定义 ≠ 降级**：不得借「3D 成为主形态 / 门控重写」删断言、放宽阈值、跳过浏览器实跑、把 FAIL 改 NOTE。任何失效断言必须有**明确替代 `chk`** 与**逐字保留的期望值**。
3. **不替用户拍板（v1.1 精确化）**：D6 **终点定义**已由用户拍板，QA 不改、不重开；**L0 退役时点 / 单一 3D 形态收敛 / 保留期、发布放行、社区模型 provenance 合规结论**仍由用户/主理人裁决；QA 只给判据、判定与阻塞项。

### 0.3 覆盖度守恒律（沿用 `p0-qa-spec.md` §0.3，空格即 FAIL）

```
COVER(K1) ∧ COVER(K2) ∧ COVER(K3) ∧ COVER(K4) ∧ COVER(K5) == True
每一类 K 至少有 1 条硬 chk 承接，且 PASS 判据不弱于 p0-qa-spec.md §1
任一被重定义的旧断言，在 §3 失效清单里都有「替代 = 具体编号」；出现空行 = 规格不接受
§6.3 映射表任一格空格 → 判 FAIL，不得以「PASS 数够多」替代
```

### 0.4 明确禁止项（X1–X11，实跑报告须逐条复述）

| # | 禁止 |
| --- | --- |
| X1 | 删断言 / 缩小 83 词表 / 只查部分词 / 把零命中断言降级为 warn 或 NOTE |
| X2 | 放宽 `max(finishTime) <= 180s`、用「构建通过」替代 11 场实跑、用 `dist/` 打包副本替代原路径 `node js/headless_laps.mjs` |
| X3 | 跳过真实 Chromium 浏览器实跑；用「Canvas 元素存在」「`window.__P1_*` 对象存在」冒充「3D 车可见」 |
| X4 | 把 `K4` 检测面退回 `innerHTML`（`<span` 撞 `pan` 假阳性，#5 已裁决） |
| X5 | 把同源 404 / `ERR_CONNECTION_REFUSED` 混入外链豁免；把 `ERR_ABORTED` 混入 FAIL 或静默吞掉 |
| X6 | 因 headless 无 WebGL 就把「玩家车 + 2 NPC 可见」放宽为「接口对象存在」，或把 FAIL 改 NOTE 静默 PASS |
| X7 | 用 `config.js` 的 `length` / `tone` / `color` 作几何 / 材质 / 稀有度 / 教学参数；或「修」/重命名这三个值（会破 F5 / B7 门控与 A/B 配色，R8 P0 阻断级） |
| X8 | 用 `displayIpa` 作参数表键 / 去重键（U05 与 U07 同为 `ɑ`，会丢 U07）；或把 `sym` 误当作 `unit` 主键 / 反过来（C1 键契约，见 §0.6） |
| **X9** | **把「门控全绿」写成「原始 110 项原样全绿」或与之等价**（主理人裁决 A；29 项在 Vite/R3F 下物理失效，写死会把终点锁死） |
| **X10** | **复用 P0 `probe.jsx` 的 `lightCount=1` 作 P1 主站光照判据**（主理人裁决 B-2；P1 主站预期 2 盏，`probe.jsx`/`probe.html` 逐字不动、P0 62 项继续原样全绿） |
| **X11** | **把「WebGL 降级 L0」路径当作 PF-01 正常路径「主站必须有 WebGL 上下文」的 FAIL 证据**（主理人裁决 C-补充；两路径分开设 `chk`，见 §2.9 / §3.1） |

### 0.5 主理人补充裁决逐条落地表（v1.1 新增）

| 裁决 | 内容 | 落地位置 |
| --- | --- | --- |
| A-1 | 「门控全绿」= 路线 B 重定义套件 + 81 项原样保留 + 11 场 headless ALL PASS；≠ 原始 110 项原样全绿 | §0.1 / §3.2 / §4.1 G1 / §6.2 / X9 |
| B-2 | 光照断言为 **P1 主站场景单独定义**（预期 2 盏：1 主光 + 1 柔补光 ≤0.35 + AO），不复用 P0 `lightCount=1`；`probe.jsx`/`probe.html` 逐字不动，P0 62 项继续原样全绿；#30 A6 关闭 | §2.8 PVIS-5 / §3.1 PF-02 注 / X10 |
| B-3 | **新增硬判据**：WebGL 不可用 / `webglcontextlost` / 低配设备 → 自动降级 2D L0 且**不白屏**；降级后 2D 三车仍可玩、听音选车道仍可完成（关闭 #29 R2） | §2.9 `PDEG-*` / §4.1 G4 |
| B-4 | **新增硬判据**：3D 层零答案域读取——`gate.spoken`/`correctLateral`/`qType`/`hit`/`left`/`right` 及派生参数不得出现在 3D 场景、材质、几何、路牌纹理或任何 DOM 属性；与 H5 零泄露串联 | §1 K4 第 5 点 / `PQ-5` / §4.1 G5 |
| B-5 | 六维阈值可执行化：材质 3–5 层、饱和度 ≤45%、24px 黑剪影可辨、抖动 ≤3px、单一主光 + 1 柔补光 + AO、细节随距衰减，各给一条可观测判据 | §2.8 `PVIS-1..6` / §8.8 |
| B-6 | D4 教研校验：`CI=A+B+2C`、六档分布 `14/12/9/6/4/3` 严格单调不增、UR=`ɜː θ ð`；禁 `config.js` 的 `length/tone/color`；U10 标「短」/ U09 标「长」数据陷阱作交叉印证 | §2.5 重写 / `PRARITY-*` |
| B-7 | 与 #29 边界：`p1-gameplay-spec.md` 是产品/体验侧定义、不含 `chk()`，用 `D3-Axx/D4-Axx/D6-Gxx` ID；本规格负责可执行化并交叉引用，**不重复定义产品语义** | 全篇按 ID 引用 / §10 |
| B-8 | 用户已拍板 D6 终点 =「门控全绿 + 375px 可玩」；#29 §3.5 三候选只作细化，不得替换 | 头部状态声明 / §4 / G10 / §12 |
| C-1 | **C1 键契约**：`unit` = U01..U48 唯一主键；`sym` = 英式 IPA 稳定键（仅存档/查表/去重/角标/alt，不得作新表主键）；`displayIpa` 绝不进键位/去重 | §0.6 / §1 K3 / §2.5 / `PI-3`/`PRARITY-2` |
| C-2 | **C2 单调口径**：单调 = 逐音素按 CI 值单调不降；禁「整类 > 整类」断言；抽样按「档位边界处 CI 不倒置」 | §2.5 / `PRARITY-3` |
| C-3 | **PF-01 与降级路径分开**：正常路径 `PV-*` 证 WebGL 真创建 + 三车可量化可见；降级路径单独一组 `PDEG-*`；降级不作 PF-01 的 FAIL 证据 | §2.9 / §3.1 / X11 |

### 0.6 C1/C2 回执裁定（回 design-strategist #29，主理人已拍板）

- **C1 → 采纳甲方案，取消乙**：`p1-gameplay-spec.md` §2.8 JSON 的 `primaryKey:"unit"` / `stableSymKey:"sym"` / `displayIpaForKey:false` 为唯一键契约。本规格 `PD-*` 断言统一为「**按 `unit` 索引、48/48 唯一；`sym` 作为附带字段校验 48/48 唯一且与 `IPA_DISPLAY` 权威表一致；`displayIpa` 零进入任何键位/去重**」。已修订原文 `:252` / `:257` / `:264`，并**主动扩修 §1 K3 `:98` / `:104` 同类措辞**（原写「按 `sym`（unit id）索引」，同一混淆），避免规格内部两套键契约。**不要求 #29 追加 `bySym` 投影**。
- **C2 → 采纳建议**：单调限定为「每条 unit 的 `rarity` 等于 §2.2 阈值对 `CI` 的计算结果，且 `CI` 递增时档位不下降」（JSON 层不变式 + `D4-A07/A08`）；类别级只允许验「卷舌 / centring 双元音 / 后鼻音不落最低两档」；**禁**「所有双元音 > 所有单元音」「所有鼻音同档」。已修订 `:258` / `:265`。
- **C3 → 确认关闭**：#29 已把 `D6-G02` / §3.7 / R4 / §6-9 同步引用本规格 `110 = 29 重验 + 81 原样保留`，不再另立数字。
- **门控口径（`D6-G02` 显式交给 #31 定夺）→ 按主理人裁决 A**：「门控全绿」= 路线 B 重定义套件（本规格 §6 定义）+ 81 项原样保留（3D 主形态下重放）+ `headless_laps.mjs` 11 场 ALL PASS；**不等于**原始 110 项原样全绿。请 #29 按此同步 §3.2，避免两套判据。
- **§9-7 听障视觉冗余**：仍**未拍板**，本规格只登记、不写成已决、不纳入任何 `chk`（与 #29 §1.7 / `D3-A09` / §6-11 一致）。
- **口径张力留痕（提请 #29 同步）**：`p1-gameplay-spec.md` §498 前提声明、§3.5 标题、§6-6、R3 仍写「D6 终点具体判据未拍板 / 推荐乙」；主理人裁决 B-8 明确**用户已拍板终点定义**。本规格按主理人裁决写成「终点定义已拍板、退役时点待裁决」；建议 #29 把三候选降格为「已拍板终点定义下的细化展开」，避免双权威。QA 不替 #29 改文件。

---

## 1. 五类不可降级断言（K1–K5 逐条：原测法 → P1 新测法 → 硬 PASS 判据）

> 编号 `K1–K5` 与 `p0-slice-spec.md` §1 裁决 3 一一对应；新门控编号见 §6。**P1 相对 P0 的增量 = 3D 成为默认主形态后，五类断言必须在 3D 主形态下再成立一遍**，而不是只在 2D L0 下成立。

### K1 · 判定核心确定性

**原测法**：`BD-1` 五文件 sha256 与 P0 前快照全等、`BD-2` `node js/headless_laps.mjs` 11 场、`BD-3` `minimap_model.test.mjs` 10 项、`BD-4[dev/build]` 2D 主形态、`verify_cseg_gate.py` S1–S8/S13/A0–A6。

**P1 新测法（三路并行，缺一不可）**：
1. **源码零改动证明**：`js/race.js` / `js/track.js` / `js/config.js` 三文件取 sha256，与 `.workbuddy/backups/p0-pre-20261109/file-hashes.json`（374 项）对应条目**逐项全等**；并逐字核对 `odo/lateral`、`g.line = startOdo + lineT·L`、`buildGates()`、`judge()`、`beginDecide()`、`hitsLane()`、`TUNING.laps=2`、follow 260 / listen 300 仍在**原生 ESM 文件**中（非 TS、非打包产物、非 React state）。相对 P0 追加：**P1 改动前须先落一份新的全量快照**（§9），三文件同时与该新快照全等，证明「P1 全程未动判定核心」。
2. **原路径原命令实跑**：`node js/headless_laps.mjs`，解析 11 场输出，最慢 ≤180s；**3D 主形态下**也跑一遍，确认 `finishTime` 与 2D 版**逐项一致**（`3d-tech-feasibility.md` §8 P2 口径）。
3. **浏览器内判定一致性**：真实 Chromium 下 `window.__rally.step(n)` 显式驱动，核对 `lineT=[0.24,0.68,1.24,1.68]`（容差 `1e-9`）、两圈同 `commitT` 的 `line` 差 = `L`、`nextGate.lap`、quiz 三题型题干不泄答案；**3D 开启与 2D L0 回退两种形态各一遍，判定结果逐位一致**（§4.5 隔离断言 5）。

**硬 PASS 判据**：
```
sha256(race.js/track.js/config.js) == P0 前快照 == P1 前快照      # 逐字不改，双重锚定
node js/headless_laps.mjs → 11 场 ALL PASS 且 max(finishTime) <= 180.0s
3D 与 2D 两形态：finishTime 逐项一致 / lineT / 两圈 line 差 = L / lap 序列 / 三题型正确
snapshot() 只读，3D 层零 odo/lateral/g.line 写入点（与 R-* 联动）
```
**禁止**：X2；用 `RENDER_MODE=3d` 下重跑的打包副本替代原路径命令；因「3D 更好看」接受判定结果任一数值变化。

### K2 · 跨站 `localStorage['ipa-quest-v1']` 单键保真

**原测法**：`BS-1[dev/build]` 零写盘 + 键集合守恒 + `rally` 字段守恒；`verify_c08_gate.py` D1.1–D6.2；`verify_fresh_gate.py` F11a/F11b；`verify_cseg_ui.py` U10/U11；`verify_hud_spec.py` H12。

**P1 新测法**：
1. `verify_c08_gate.py` 的 D1–D6 全套（老存档迁移、`v1.bak` 逐字节、幂等、`rawHasV2`、跨站 last-write-wins、**`rally.unlocked` 并集**、storage 事件、gems 交错 delta）在 **3D 主形态**下用新服务入口重放，期望值**逐字不变**。
2. hook `Storage.prototype.setItem`：3D 场景 `step(300)` 期间增量 **0**；`rally.unlocked / maps / lastMap / lastChar / EP02` 开赛前后逐字段相等；**键集合 == 基线键集合**（P1 不新增 localStorage 字段，D3「听音选车道」不得靠新增存档字段实现）。
3. 同源判定：`location.origin(拉力赛) == origin(大闯关)`；拉力赛侧写 → 大闯关侧读回逐字段相等，反之亦然（C5 / CN-4 联动）。

**硬 PASS 判据**：
```
3D 主形态：D1–D6 全 PASS（期望值不变）/ unlocked 并集生效 / 零覆盖
setItem 增量 == 0 且 键集合 == 基线键集合
origin 相等 且 跨站读写 rally 字段逐字段相等
```
**禁止**：因「3D 引入开关」默认新增 localStorage 字段（开关须用 query param / 内存 flag / URL，不落盘）；因 `dist/` 不同源就把 D1–D6 标 NOTE 放行。

### K3 · `window.IPA_DISPLAY` 唯一权威美式显示源与稳定键（v1.1 按 C1 修订）

**原测法**：`BI-1/2/3[dev/build]` 等价时序（setter 同步捕获 `IPA_DISPLAY` 赋值瞬间 `readyState=='loading'`）、`U11='ɜr'`、48 卡面、`ipa-display.js` 字节全等；F1/F1b/F2/F5/F9a/F9b、B2/B9、D7.4、H11。

**P1 新测法**：
1. **等价时序**（沿用 `p0-qa-spec.md` A.2）：dev/build/3D 主形态下，`ipa-display.js` 仍非 module、无 defer/async；`window.IPA_DISPLAY` 在 module 执行**之前**已就绪（setter 同步打点，不按 DOM 字面顺序判）。
2. **单一显示源 + 稳定键**：`IPA_DISPLAY.U11.displayIpa === 'ɜr'`（U18=`ɪr`/U19=`ɛr`/U20=`ʊr` 同表权威）；48 卡面 `.sym` 大字全为美式、无 `ː/ɒ/əʊ/ɪə/eə/ʊə`；`ipa-display.js` sha256 与 P0 前快照逐字节全等；F1b `ː` 仍只出现在 10 行 `sym` 稳定键；F5 逻辑枚举键锁定 + D01–D05 在场。
3. **键契约与 U05/U07 去重陷阱（C1 裁定 · 主理人点名）**：**`unit`（U01..U48）是唯一主键**；**`sym` 是英式 IPA 稳定键**（`iː`/`ɑː` 等音素符号），仅作存档/查表/去重/角标/alt，**不是 unit id、不得作新表主键**；**`displayIpa`（美式）绝不进任何键位/去重**——U05 `ɑː` 与 U07 `ɒ` 的 `displayIpa` 同为 `ɑ`，用它去重会静默丢 U07（#29 §2.7 F5 实测全表唯一碰撞恰为此对）。硬断言：任何 3D 参数表 / 稀有度映射 / 精灵索引 / 收集图鉴 / `phoneme-features.json` **按 `unit` 索引**，`len(unique_unit)==48` 且 `len(unique_sym)==48`；`sym` 与 `IPA_DISPLAY` 权威表一致；扫描 3D 层源码/参数表零 `displayIpa` 作键用法；构造 `sym→displayIpa` 映射验证 `len(unique_displayIpa)<48` 以证明去重确实冲突。交叉引用 `p1-gameplay-spec.md` §2.7 `F4/F5`、§2.8 `primaryKey/stableSymKey/displayIpaForKey`、§2.10 `D4-A02/A03`。

**硬 PASS 判据**：
```
IPA_DISPLAY.U11.displayIpa === 'ɜr' / ipa-display.js sha256 == P0 前快照
module 执行前 IPA_DISPLAY 已就绪（等价时序，三形态）
48 unit 按 unit 索引且 48/48 唯一；sym 48/48 唯一且与权威表一致；零 displayIpa 作键
U05 与 U07 均可独立寻址（按 unit）
```
**禁止**：把 `ipa-display.js` 打进 bundle 后不验时序就 PASS；X8（含「`sym` 即 unit id」的混淆）；把「U05/U07 撞 `ɑ`」当成可接受的去重优化。

### K4 · quiz 答案零泄露（H5 口径 + 3D 层零答案域，逐字不回退）

**口径铁律（照抄 #5 裁决 / `p0-qa-spec.md` §1 K4，本规格逐字不回退）**：
- 检测面 = **`mm.textContent` + 遍历后代元素的所有属性值**（`alt` / `aria-label` / `title` / `data-*` 全量 `[name, value]` 的 value，不缩小）；
- **不检测 `mm.innerHTML` 源码字面量**（`<span id="minimap-lap">` 的 "span" 含 `pan`，撞 pen/pan 词对，属测试脚本假阳性）；`innerHTML` 仅作诊断证据、不计判定；
- 词表 = `allWords()` **83 词全表** + `correctLateral/spoken/left/right` **4 字段名** + 4 门 IPA/displayIpa；
- **防放宽守卫**：`len(vocab)==83 and len(set(vocab))==83` 本身是硬判据；仍是 `chk()` 硬断言（非 warn）；
- 禁用属性名 `data-(lane|correct|side|answer|left|right|word|ipa|spoken)` 零命中；中文答案域 `答案/正确` 零命中。

**P1 新测法（3D 增量，不回退）**：
1. **2D L0 与 3D 主形态两遍**：H5/H6/H8 在两种形态下原样重放，检测面与词表**逐字不变**。
2. **3D 场景新增检测面**：3D 渲染层若含任何 DOM overlay（HUD、路牌、aria 标签、React `data-*`、props 序列化到 DOM 的属性），全部纳入同一检测面；**WebGL canvas 不产生 DOM 文本，但不得因此跳过 DOM 属性扫描**。若 3D 把 `snapshot()` 里的答案域键写进 `data-*` / `aria-*` → FAIL。
3. **`snapshot()` / 3D 参数表键白名单**：递归键名不得出现 `correctLateral/spoken/left/right/pairKey/qType/options/displayIpa/answer/correct/word/ipa/hit`（沿用 H6 `FORBID_KEYS`，键名匹配、不误伤值）。
4. **D3 联动**：3D 场景**不得**用视觉冗余（显示目标词 / 口型 / 箭头指向）替代「听音选车道」；路牌 S2 两侧仍同帧同尺寸、无单侧高亮（H8），S1 零文本（H7）；交叉引用 `p1-gameplay-spec.md` §1.4 / §1.5 / `D3-Axx`、§2.7 `F6`。诊断 §72 行明确「不据此推断用户对听障视觉冗余的立场，§9-7 仍视为未拍板」——本规格只保证**当前口径不泄答案**，不替用户重开玩法口径。
5. **【v1.1 新增 · 主理人裁决 B-4】3D 层零答案域读取**：`gate.spoken` / `correctLateral` / `qType` / `hit` / `left` / `right` **及派生参数**不得出现在 3D 场景、材质、几何、路牌纹理或**任何 DOM 属性**；环境特效（声音可视化 / 三层预告 / 镜像闸门等）在判定完成前**只读**音频包络 + `commitT` 位置 + 圈数/位置 + 当前区 id + 玩家动作，**不得把答案画出来**。与 H5 检测面串联（`textContent` + 后代所有属性值 + 83 词全表 + 4 字段名，**不退回 `innerHTML`**）。交叉引用 `p1-3d-art-spec.md` §6.7（防泄题，「环境特效不得把答案画出来」；主理人裁决 4 转述为 §4.4，实为 §6.7，已按实际落点对齐）、§4.4 路牌几何、`p1-gameplay-spec.md` §2.7 `F6`。硬判据：静态源码零命中 + 运行时 3D DOM/材质属性零命中 + 环境特效只读白名单。

**硬 PASS 判据**：
```
vocab_ok := (len(vocab)==83 and len(set(vocab))==83)
2D 与 3D 两形态：textContent + 后代所有属性值 对 91 token 零命中 / 禁用属性名零命中 / 中文关键字零命中
snapshot 递归键名零禁用键、nextGate 键集合精确 / 3D overlay 不新增答案载体 DOM 属性
【新增】3D 场景/材质/几何/路牌纹理/DOM 属性 零 gate.spoken·correctLateral·qType·hit·left·right 及派生参数
```
**禁止**：X1、X4；因探针/3D 是 canvas 就跳过 DOM 属性扫描；把零命中断言降级为 NOTE；用「画面上看不出来」替代源码/属性扫描。

### K5 · 四项错误计数归零

**口径（沿用 `hud-qa-plan.md` §3 / `p0-qa-spec.md` §1 K5 / A.7）**：

| 类别 | 判定 | 计入硬失败 | 要求 |
| --- | --- | --- | --- |
| `pageerror` | 页面未捕获异常 | **是** | `= 0` |
| `console_error` | `console.error` 文本 | **是** | `= 0`（外链派生项按 A.7 计数配对 + `ConsoleMessage.location.url` 外部 host 校验后单列，不豁免任何同源项） |
| `bad_status` | `status >= 400` | **是** | `= 0` |
| `requestfailed` — `net::ERR_ABORTED` | reload / 导航主动取消 | **否**，单列披露 | 打印去重 URL 样例 |
| `requestfailed` — **同源**非 `ERR_ABORTED` | 真实网络失败 | **是** | `= 0`（含 `ERR_CONNECTION_REFUSED`，按 §7.3 瞬态口径处置后仍须为 0） |
| `requestfailed` — **外链**（Google Fonts） | 环境相关 | **否**，NOTE 披露 | 打印明细；资源送达另由 §5 四重判定覆盖，不信状态码 |
| **P1 新增** — WebGL 上下文丢失 / 恢复事件 | 环境 / 实现相关 | **单列披露** | `webglcontextlost` 计数与恢复时长登记；恢复后不得「跳门」（§4.5 隔离断言 6）；降级路径见 `PDEG-2` |
| Vite 机制项（`/@vite/client`、HMR WS、`/@fs/`） | 开发服务器机制 | 否 / 按同源口径 | 与实际同源内容资源失败**分开统计** |

**汇总必须单列披露**：`总计 N | ERR_ABORTED N | 同源真实失败 N | 外链环境 N | Vite 机制 N | WebGL 上下文事件 N`。

**硬 PASS 判据**：
```
errs_strict_ok = (pageerror==0 and 硬console_error==0 and bad_status==0 and len(REAL)==0)
REAL = 同源非 ERR_ABORTED 失败（含 ERR_CONNECTION_REFUSED，按 §7.3 处置后仍须为 0）
```
**禁止**：X5；因 Vite HMR 噪声整体关掉 `requestfailed` 监听；把 WebGL 上下文丢失当「环境项」静默豁免掉「恢复后不跳门」的判定。

---

## 2. P1 新增硬判据族（主理人点名七族 + 补充裁决新增两族，逐族：测法 → 硬 PASS 判据 → 禁止项）

> **接口占位声明**：#28（engineering-lead）P1 代码**尚未落盘**（截至本规格落盘，`js/` 最新仍为 11-09 的 `probe.jsx`）。以下所有 `__P1_*` / `snapshot()` / 相机字段 / 视觉参数均为**语义占位**，精确字段名/取值范围列入 §10 实跑前置，已直接向 engineering-lead 索取。**不臆造接口名，不因接口未定而放宽任何判据**。
> **v1.1 族数**：原 §2.1–2.7 七族（PV/PC/PM/PR/PD/PB/PL）基础上新增 **§2.8 `PVIS-*` 视觉六维阈值**与 **§2.9 `PDEG-*` WebGL 降级 L0** 两族；`PL-*` 仍为失效/保留域（不产生新 `chk`）。

### 2.1 `PV-*` 3D 可见性（点开始后玩家车 + 2 NPC 真的可见）

**依据**：诊断 §0/§1（2D 三车可见 vs `probe.html` 仅 1 立方体）、主理人 #31 第 1 条。

**测法**（真实 Chromium，dev + build 两模式，375×780 与 320×568 两视口）：
1. 完整走通入口链路 `#how-close` → 选跟读档 → 上赛道 → 倒计时 → `mode==='racing'`（诊断 §40 行坑：首次 `howSeen=false` 会主动隐藏标题页，不先关弹窗会误判「界面没起来」）。
2. 断言 WebGL 上下文**真实创建且非丢失**：`getContext('webgl2') || getContext('webgl')` 非 null、`gl.getParameter(gl.VERSION)` 非空、`contextLost===false`、连续 `frames > N`（渲染确实在跑）。
3. **可观测且非 0**：玩家车 + 2 NPC 的 **mesh 数 ≥ 3 且可按 id 区分**、**drawCalls > 0**、三车**屏占比（投影包围盒面积 / 视口面积）各 > 0 且落在可见视锥内**（非全屏、非 0、非屏外）。
4. **点开始后可见**：在 `mode==='racing'` 且里程推进（`odo` 单调增）的时间点取证，不得用 title/teach 态的静态画面充数。
5. **3D 与 2D 的可见性不互相冒充**：`#c`（2D canvas）与 3D canvas 的可见状态分别登记；不得用 2D 三车的 `drawKart()` 结果冒充 3D mesh。

**headless 无 WebGL 的降级取证（不放宽结论）**：
- 允许显式启用软件渲染（`--use-gl=swiftshader` / `--enable-unsafe-swiftshader`）并在报告登记 `webglVendor` / `webglRenderer` 字符串；或改用带 WebGL 的有头 Chromium 截图 + 像素证据（车辆区域非空像素 > 0）。
- **降级只改变取证方式，不改变结论**：仍须证明 mesh/drawCalls/屏占比 > 0 且三车可区分。
- 若所有取证路径都无法产生 WebGL 上下文 → 判 **CONCERNS（证据 MISSING）** 并上报主理人，**不静默 PASS、不把 FAIL 改 NOTE、不降为「Canvas 存在」**（X6）。
- **正常路径与降级路径分开**：本节 `PV-*` 是「WebGL 可用」正常路径；「WebGL 不可用 → 自动降级 2D L0 且不白屏」另见 §2.9 `PDEG-*`，**不得**用降级路径反证 PF-01 失败（X11，主理人裁决 C-3）。

**硬 PASS 判据**：
```
webgl_ok && contextLost==false && frames>N
meshCount >= 3 && 三车 id 可区分 && drawCalls > 0
三车屏占比各 > 0 且投影包围盒与视口相交（非屏外/非全屏）
mode==='racing' 且 odo 单调增的取证时刻
两模式 × 两视口共 4 组证据齐全
```
**禁止**：X3（只判 `canvas` 存在或 `window.__P1_*` 对象存在）、X6、X11；把 P0 `probe.html` 单立方体（`boxes=1/drawCalls=1`）当作「3D 车已实现」。

### 2.2 `PC-*` 第三人称跟车相机

**依据**：`visual-direction-3d.md` v1.1 §B.1（机位 **3.4–3.8 m**、俯角 **16°–20°**、水平 **FOV 60–66°**、临界阻尼时间常数 **0.18–0.28 s**）、§261（消失点在画面顶部 40%、路面占下方 60%、护栏向消失点收拢）、`p1-3d-art-spec.md` §2、`3d-tech-feasibility.md` §8 P1 Go-No-Go（两车道在 375px 可辨、无眩晕、判定逐位一致）。

**测法**：
1. **跟随单调**：连续采样 `step(n)` 下玩家 `odo` 与相机世界坐标（或相机跟随目标点），断言相机位置关于 `odo` **单调推进**、无整段跳变；阻尼时间常数落在 0.18–0.28 s（禁止逐帧硬跟随）。
2. **远端收敛**：取赛道远处若干采样点投影，断言投影 y 随距离**单调趋近消失点**、左右护栏投影宽度随距离**收窄**（收敛证据）；消失点位于画面顶部约 40%、路面占下方约 60%。
3. **无整条赛道俯视证据**：断言俯角落在 16°–20°（**不是 90° 俯视**）、机位高度 3.4–3.8 m、水平 FOV 60–66°；并断言**任意时刻可见赛道段占整圈比例 < 100%**（远裁面/雾化截断），不得出现「整条赛道同时可见」的俯视图。
4. **两车道可辨**：375×780 与 320×568 下左右车道在投影上**可分离**（横向投影间距 > 0 且大于线宽阈值），左右选道操作能改变玩家车投影 x 且方向正确。

**硬 PASS 判据**：
```
相机跟随 odo 单调 / 阻尼 0.18–0.28s / 无跳变
远端投影收敛 + 消失点位置 + 护栏收窄
俯角 ∈ [16°,20°] 且 机位高 ∈ [3.4,3.8]m 且 水平 FOV ∈ [60°,66°]
可见赛道段 < 100% 整圈（无俯视）
两视口下左右车道投影可分离、选道方向正确
```
**禁止**：用「相机对象存在」替代几何证据；因「画面好看」接受俯角越界；把「无眩晕」主观项直接判 PASS（该项属 Playtest，见 §4 Go/No-Go 表，须人工签收）。

### 2.3 `PM-*` 375px 竖屏可玩（走完一整局）

**依据**：主理人 #31 第 3 条、`p0-slice-spec.md` §2 Go-No-Go「2D 主形态可用」、`hud-qa-plan.md` §6 V1–V17 / §7 DPR、`3d-tech-feasibility.md` §8 P2、`p1-3d-art-spec.md` §2.5。

**测法**（375×780 主测 + 320×568 兼容，真实 Chromium，3D 主形态）：
1. **完整一局**：从入口到 `results`，真实走完 **2 圈 / 4 门**，期间覆盖 ① **左右选道**（触屏 `#touch` 左右转向 / 键盘）、② **`#jump` 可点且生效**（`D8.3` 源码保留 `pointerdown/jumpEdge`、沿用 `D8.4` 375px `#jump` 存在可点）、③ **quiz 三题型作答并进入结果页**；`finishTime` 与 2D 基线一致（不退化）。
2. **无横向溢出**：`document.documentElement.scrollWidth <= innerWidth`；3D canvas 与 `#hud` / `#banner` / `#quiz` / `#touch` 的 `getBoundingClientRect()` 均在视口内、无负 x / 超宽。
3. **顶栏不遮挡**：`#hud` 顶栏、状态栏、圈数、进度条矩形**不与玩家车 / 分叉路牌 / 3D 关键可视区相交**；`pointer-events:none` 的 3D canvas 不吞掉 `#btn-pause` / `#btn-mute` / `#jump` 的点击（V6 口径）。
4. **DPR**：`dpr = min(2, devicePixelRatio)`；DPR 3 clamp 到 2；canvas 位图尺寸 == CSS 尺寸 × clamp 后 dpr（±1px），DPR 2 与 3 位图尺寸相同。
5. **人工过眼**（自动脚本不覆盖，须人工签收）：V1–V17 中与 3D 相关的 V3/V4/V6/V7/V8/V9/V10/V11/V12/V13/V16 逐项；`prefers-reduced-motion` 下 3D 动效降级不破可玩性（`p1-3d-art-spec.md` §2.6）。

**硬 PASS 判据**：
```
375×780 与 320×568：各完整走完 2 圈 4 门 → results，finishTime 不退化
左右选道 / #jump / quiz 三题型作答 全程可操作且生效
scrollWidth <= innerWidth；顶栏矩形与关键可视区零相交；canvas 不吞点击
DPR clamp 生效；人工过眼清单无「阻塞」项
```
**禁止**：用「页面能打开」替代「走完一整局」；把 320×568 标为「建议」而不实测；跳过人工过眼直接判可玩。

### 2.4 `PR-*` 3D 层只读（不写判定 / 不写盘 / 不进主循环 rAF）

**依据**：`3d-tech-feasibility.md` §4.5 六条隔离断言、`p0-slice-spec.md` §1 裁决 1、ADR-2（Rapier 只进视觉层，绝不替换 `odo/lateral + g.line`）、`p1-gameplay-spec.md` §1.6 判定链冻结清单。

**测法（静态源码 + 运行时双证）**：
1. **静态**：扫描 3D 渲染层源码（`render3d.js` / `physics-visual.js` 或 #28 实际新增文件），零 `race.state.* =`、零 `judge(`、零 `beginDecide(`、零 `saveWallet`/绝对值写回（§4.5-2 / S1.5）；`g.line - odo` 与 `D_preview` 比较式中不出现 `alpha` / `performance.now()` / `devicePixelRatio`（§4.5-3）。
2. **运行时**：hook `Storage.prototype.setItem`，3D 路径增量 **0**；`snapshot()` 返回对象递归键名在白名单内、调用前后 `race.state` 深拷贝**逐字段相等**（只读证明）。
3. **主循环隔离**：3D 渲染 rAF 与 `main.js frame()` 判定固定步长 `race.step(SIM_DT)` **分离**；人为把 rAF 降到 15fps / 提到 144fps，11 场 headless 的 `finishTime` 与门线判定序列**逐项一致**（§4.5-1）。
4. **冻结态**：`mode==='quiz'` 冻结前后 `karts[0].odo` / `simTime` **严格相等**（§4.5-4、H9）；3D 不得在冻结期推进任何判定或视觉里程。
5. **视觉物理分离**：关闭 Rapier（L0/L1）后判定结果与 L2 **逐位一致**（§4.5-5）。
6. **WebGL 上下文丢失/恢复**：恢复后视觉与判定重新对齐、不产生「跳门」（§4.5-6）；与 `PDEG-2` 降级路径联动但各自独立判定。

**硬 PASS 判据**：
```
静态 6 项零命中 + 运行时 setItem 增量 0 + snapshot 只读（深拷贝相等）
rAF 15/144fps 下 11 场 finishTime 与判定序列逐项一致
quiz 冻结 odo/simTime 严格相等；L0/L1 与 L2 判定逐位一致
上下文恢复后无跳门
```
**禁止**：只做静态扫描不做运行时 hook；因「帧率影响只是视觉」跳过 15/144fps 复跑；把 Rapier 引入判定后接受 `finishTime` 漂移。

### 2.5 `PD-*` D4 六档稀有度映射教研校验（v1.1 按 C1/C2 + #29 权威表重写）

**依据**：诊断 §3 D4、`visual-direction-3d-v2.md` §M6(182-188) 与 P8(416-422) 六档材质递进、`3d-tech-feasibility.md` §M1 / §554、阶段交付 §3 **R8（P0 阻断级）**、**`p1-gameplay-spec.md`（#29）§2.1–§2.10（D4 权威映射表，按 `D4-A01..A12` ID 引用）**、`p1-3d-art-spec.md` §6.2/§6.5（参数 schema 与数据源硬约束）。

> **职责边界（主理人裁决 B-7）**：六档语义、维度定义、评分 rubric、48 音标全表、**教研评审依据**均为 `p1-gameplay-spec.md` 的产品/教研侧定义，本规格**按 ID 交叉引用、不复述语义、不另写一份**；QA 只把 §2.7 `F1–F8`、§2.8 JSON 层不变式、§2.10 `D4-Axx` 转成可执行 `chk`，验「表存在 + 可追溯 + schema 合规 + 公式可复算 + 分布单调 + 未被禁用字段/答案域污染」。

**上游事实（按 ID 引用，不臆造）**：六档名与顺序 `P / SR / SAR / HR / SSR / UR`（与 `cards.js RARITY_RANK` 逐项相等，`D4-A09`；材质对齐 v2 M6 / P8 ①–⑥）；三维 `A 部位难度 / B 方法复杂度 / C 中国学习者习得难度`（各 0..3 整数），公式 **`CI = A + B + 2·C`**（`C` 加权 ×2，面向中国学习者），`CI ∈ [0,12]` 全整数；分档阈值 `0–3→P / 4–5→SR / 6–7→SAR / 8–9→HR / 10→SSR / 11–12→UR`；分布 **`14/12/9/6/4/3 = 48` 严格单调不增**（`D4-A08`）；UR 典型音素 **`ɜː / θ / ð`**。**权威表落点**：`p1-gameplay-spec.md` **§2.3（48 行全表）+ §2.8（可消费 JSON 块，48 条完整）**；本轮**未落盘独立文件**（§2.9 给了未来 `sprite_gen/rarity-map.json` 的合并契约，QA 不预设落盘）。JSON 顶层字段 `schema / status / primaryKey:"unit" / stableSymKey:"sym" / displayIpaForKey:false / closedSet:48 / forbiddenFields[] / dimensions{A,B,C} / formula / ciRange / bands[] / rarityRank[] / distribution{} / units[]`；每条 unit 仅 `unit, sym, A, B, C, CI, rarity`（无 `displayIpa` / `type` / 答案域）。

**测法**：
1. **禁用三字段硬断言（F1/F2）**：`config.js` 的 `length` / `tone` / `color` **零进入**任何 3D 几何 / 材质 / **稀有度分档** / 粒子 / 教学参数，且 JSON 与任何下游产物 `forbiddenFields` 零命中（含答案域字段，`F6`）；扫描 3D 层源码与参数表 schema 零 `length` / `tone` / `color` 键。**反证**：`config.js:103-104` 的 U09 `/ʊ/` 标「长」、U10 `/uː/` 标「短」（字面与语音学相反），`:91` `color = tone==="long"?A_COLOR:B_COLOR` 只是 A/B 分组色；若分档结果与之同向即判 FAIL（主理人裁决 B-6 与 #30 独立标注交叉印证）。
2. **不得「修」三字段（F2 / `D4-A05`）**：`config.js` 中 `PHONEMES` / `VOWELS` 三个字段的值**逐字未改**（F5 `is-long/is-short` / B7 同对 `label` 互异 / A/B 分组配色依赖），sha256 与 P1 前快照全等；改了破门控。
3. **键契约（C1 裁定 · `F4/F5` · `D4-A02/A03`）**：发音特征表 / 六档映射**按 `unit`（U01..U48）唯一主键索引**，`len(units)==48`、`unit` 48 唯一**且** `sym` 48 唯一、`displayIpaForKey===false`、`displayIpa` 零进入任何键位/去重；`sym` 作为附带字段与 `IPA_DISPLAY` 权威表一致（U11=`ɜr`/U18=`ɪr`/U19=`ɛr`/U20=`ʊr` 不动）。**U05/U07 去重陷阱**：全表 `displayIpa` 唯一碰撞恰为 `ɑ`（U05 `ɑː` / U07 `ɒ`），二者在本表恰好分落 SR / SAR；误用 `displayIpa` 作键会静默合并两条并得到错误分布 → 判 FAIL（X8，与 K3 联动）。
4. **教研校验 + JSON 层不变式（`D4-A01/A06/A07/A08`）**：映射表须有**可追溯的教研评审依据**（`p1-gameplay-spec.md` §0.4 上游表 + §2.3「评分要点」逐档答辩：θ/ð 齿间 CI=12 满分、ɜː r-色彩央元音 CI=11、r/l 同 CI=9 同 HR、æ/ʌ 同 CI=5 同 SR 且「难听辨≠难发音」二维正交、双元音按汉语复韵母可及性分四档、浊化/鼻音梯度可断言、48 闭集无独立三元音 unit）。硬 `chk`：
   ```
   units.length === 48
   new Set(units.map(u => u.unit)).size === 48
   new Set(units.map(u => u.sym)).size === 48
   units.every(u => u.CI === u.A + u.B + 2*u.C)                 # A/B/C ∈ [0,3] 整数, CI ∈ [0,12]
   units.every(u => u.rarity === bands.find(b => u.CI >= b.ciMin && u.CI <= b.ciMax).rarity)
   Object.keys(units[0]) ∩ forbiddenFields === ∅                  # 键名匹配, 不误伤值
   distribution 六档计数与实际一致 且 单调不增                    # 14/12/9/6/4/3
   ```
   **单调口径（C2 裁定）**：单调 = **逐音素按 `CI` 值单调不降**（`CI` 递增时档位不下降），抽样验证按「**档位边界处 `CI` 不倒置**」（边界 3/4、5/6、7/8、9/10、10/11 全覆盖）；**禁止**「所有双元音 > 所有单元音」「卷舌/双元音/鼻音整类更高」「所有鼻音同档」这类整类断言（关滑 `eɪ/aɪ/aʊ` 因 `C=0` 落 SR、centring `ɪə/eə/ʊə` 落 SSR、鼻音 `m=P/n=SR/ŋ=HR` 类别内递进，整类断言必假 FAIL）。类别级只允许验「卷舌 / centring 双元音 / 后鼻音**不落最低两档**」。
5. **视觉负向约束 + 迁移断言（`D4-A09` / v2 P8 / §2.9）**：6 档轮廓与尺寸完全一致、牌面零文字/字母/数字/IPA/中文/水印，与 K4 零泄露联动；`rarityRank` 六档顺序与 `cards.js RARITY_RANK` 逐项相等；**登记但不臆造已改**：#29 实测 36/48 unit 改档、`gen_sprites.py:21` 的 `SAMPLES` 6/6 全部改档（§2.9 逐档迁移表），QA 在实跑时验「迁移是否按契约完成」，不把「建议改」写成「已改」。

**硬 PASS 判据**：
```
零 length/tone/color 进入 3D 参数/稀有度分档/JSON；config.js 三字段值逐字未改（sha256 全等）
特征表按 unit 索引、unit 48/48 唯一 且 sym 48/48 唯一、displayIpaForKey===false、零 displayIpa 作键
教研表存在且评审可追溯；CI 公式与 band 逐条可复算；按 CI 单调不降（禁整类断言）
分布 14/12/9/6/4/3 严格单调不增；UR = ɜː θ ð；六档名与 RARITY_RANK 逐项相等
六档轮廓/尺寸一致、牌面零文本；零答案域字段
```
**禁止**：X7、X8（含 `sym`/`unit` 混淆）；QA 自行编造六档定义或用 `config.js` 三字段「凑」复杂度；写「整类 > 整类」单调断言；把 R8 的 P0 阻断级降为 NOTE；把「未落盘独立 JSON」判成产品缺陷（#29 §2.8 明确本轮为规格内容）。

### 2.6 `PB-*` 双层缓存唯一（46 + N 互不混算）

**依据**：`p0-slice-spec.md` §1 裁决 2、`p0-qa-spec.md` §2 与附录 A.1（#20b 修订后的六项约束）、`p0-qa-report.md` BC 6/6。

**测法（沿用 A.1 已实跑口径，不回退）**：
1. **源码层**：白名单 9 文件锁 `{hud-20261108: 46}`，唯一且恰好 46；扫描根 `os.walk(QUEST/RALLY)` 且**排除** `node_modules/` / `dist/` / `.p0-build/` / `.workbuddy/`（`p0-qa-spec.md` §2.6 白名单，防 33 处 `node_modules` 裸引用污染）。
2. **产物层**：`VENDOR_TAG` 单独锁 N 处、N 由 P1 产物定型确定（P0 实测 `VENDOR_TAG=p0-20261109`、N=3）；`vendor.manifest.json` 版本钉定。
3. **互不混算**：① 两层扫描根**物理隔离**；② 源码层 46 / 产物层 N 各自唯一且恰好；③ 两 tag 值不同；④ 源码层 9 文件不含产物层 tag；⑤ 源码层无杂 tag；⑥ **产物层残留的源码 tag 逐文件单列披露、不计入 N、不作 FAIL 依据**（#20b A.1：Vite 实测残留 8 处属正常）。
4. **20 图零裸引用**：含字符串字面量与 `"assets/img/"+变量` 拼接型，源码层 0 裸引用。

**硬 PASS 判据**：
```
源码层 {hud-20261108:46} 唯一且恰好 / 产物层 {VENDOR_TAG:N} 唯一且恰好
扫描根隔离 True / 两 tag 不同 / 源码层无杂 tag 与产物 tag
20 图（含拼接型）零裸引用 / 产物层残留源码 tag 仅披露不计判定
```
**禁止**：把「各自唯一」悄悄降成「存在即可」；因产物层有源码 tag 判产品缺陷；把 `node_modules/` 纳入全仓扫描（§2.6 已证伪）。

### 2.7 `PL-*` 失效清单与 81 项原样保留

见 **§3**（逐条失效依据）与 **§3.3**（81 项逐条清单）。

### 2.8 `PVIS-*` 视觉六维阈值可执行化（v1.1 新增 · 主理人裁决 B-2 / B-5）

**依据**：`p1-3d-art-spec.md` §5 六维阈值表（①剪影精度 ②材质层次 ③光影与 AO ④动效克制 ⑤色彩饱和度带 ⑥细节密度梯度）、§3.0/§3.4/§3.5、§2.4/§2.6/§2.4、§4.7、§4.8、§8 `A5/A6`、v2 §1.2。主理人裁决：**各给一条可观测判据**（材质层数可数、hex 饱和度可算、光源数可数）。

**测法（6 条，各出「过 / 不过」，交叉引用 #30，不复述美术语义）**：
1. **PVIS-1 材质层数可数**（§3.0/§3.5/§5②）：逐主体统计材质分区层数，断言 `3 <= layers <= 5`；相邻层 `roughness` 差 ≥0.15、明度差 ≥8%；零后处理链。
2. **PVIS-2 饱和度可算**（§3.5/§5⑤）：从材质 hex 取 `S(HSV)`，主体色 `S <= 45%`；宝石点缀 `S ∈ [55%,75%]` 且屏幕占比 ≤8%；禁 `S>85%` 色块 >2% 面积。（hex → HSV 由脚本计算，不靠肉眼）
3. **PVIS-3 24px 黑剪影可辨**（§3.4/§5①）：把三车渲染成 **24px 高纯黑剪影**做两两辨识盲测，通过率 **100%**（人工盲测，须签收）；每主体 ≥3 结构特征、负空间 ≥包围盒 12%；不得只靠红绿/蓝配色区分。
4. **PVIS-4 抖动可测**（§2.4/§2.6/§5④）：375px 实机录屏逐帧取峰值位移，断言抖动 `<= 3px@375`、角位移 `<= 0.4°`、无 >30Hz 分量；`reduced=true`（`prefers-reduced-motion`）时抖动/侧倾/FOV 呼吸/速度线**全部归零**。
5. **PVIS-5 光照可数（主理人裁决 B-2 单独定义）**（§4.8/§5③/§8 A6）：**P1 主站场景**断言光源数 = **2**（1 单一暖主光 + 1 柔补光 `ambientLight/hemisphereLight` 强度 `<= 0.35`、暖色、无第二硬高光点）+ 接触 AO 覆盖 ≥80%、硬高光 ≤1/主体、禁 bloom / postprocessing。**不复用** P0 `probe.jsx` 的 `lightCount=1`；`probe.jsx` / `probe.html` **逐字不动**（sha256 与 P0 前快照全等），P0 62 项继续原样全绿。
6. **PVIS-6 细节随距衰减可数**（§4.7/§5⑥）：三档距离各截一屏数细节单元数量，断言近 `0–12m` 100% / 中 `12–45m` ≤40% / 远 `>45m` ≤10%（剪影化，收敛到纸色），留白 ≥15%；**随距衰减不随年龄**。

**硬 PASS 判据**：
```
PVIS-1..6 逐条出「过/不过」；可数值化项（1/2/4/5/6）由脚本计算、不靠主观印象
PVIS-3 剪影盲测 100% 且人工签收
P1 主站 lightCount==2 且柔补光<=0.35；probe.jsx/probe.html sha256 与 P0 前快照全等
```
**禁止**：X10；把可数值化阈值降级为「画面好看」的主观印象；因「P1 起步可能简化」跳过任一维（证据 MISSING 则判 CONCERNS 并上报，不静默 PASS）；复用 probe 计数导致误红；引入 postprocessing/bloom。

### 2.9 `PDEG-*` WebGL 降级 2D L0 不白屏（v1.1 新增 · 主理人裁决 B-3 / C-3）

**依据**：主理人裁决 3（关闭 #29 R2）、裁决 C-3（与 PF-01 分开写）、`p1-gameplay-spec.md` §3.3/§3.7（退役后无 WebGL 设备不得默认白屏）、`3d-tech-feasibility.md` §8、`p1-3d-art-spec.md` §2.6。

**测法（单独一组，不与 `PV-*` 正常路径混算）**：
1. **PDEG-1 模拟 WebGL 不可用**：浏览器禁用 WebGL / 强制 `getContext` 返回 null → 断言自动切到 2D L0 渲染、**不白屏**（`#c` 或等价 2D 画布有非空像素、关键 UI 可见）。
2. **PDEG-2 触发 `webglcontextlost`**：运行中派发上下文丢失事件 → 断言自动切 2D L0 且不白屏；恢复后按 `PR-6` 视觉与判定重新对齐、不跳门。
3. **PDEG-3 降级后仍可玩**：低配 / 降级形态下 **2D 三车仍可见可玩**、**听音选车道仍可完成**、走完整局（含 quiz 三题型 → results）、无横向溢出；不得只给「友好提示」而中断玩法。
4. **PDEG-4 降级前后判定一致**：降级前后 `finishTime` / 门线判定序列 / `rally.*` 存档与 2D L0 基线**逐项一致**；**本组不作 PF-01「主站必须有 WebGL 上下文」的 FAIL 证据**（X11）。

**硬 PASS 判据**：
```
WebGL 不可用 / contextlost / 低配 三条触发路径均自动切 2D L0 且零白屏
降级形态：三车可玩 + 听音选车道可完成 + 完整一局 + 零溢出
降级前后 finishTime / 判定序列 / 存档逐项一致
与 PV-* 正常路径分表登记，不互相冒充
```
**禁止**：X11；默认白屏；把降级路径当成 `PV-*` 正常路径失败来判；以「headless 本就无 WebGL」为由豁免「降级后仍可玩」的判定；把降级写成「不支持设备给提示」而不给可玩路径。

---

## 3. 3D 成为默认主形态的失效清单（逐条给重定义依据，禁止静默放宽）

> **P0 基线**：`verify_p0_gate.py` 62 项（`P0-0` 1 + `BD` 7 + `BC` 6 + `BV` 14 + `BI` 6 + `BQ` 6 + `BS` 2 + `BE` 4 + `BR` 16），`p0-qa-report.md` 🟢 PASS。另有四套门控 110 项中 81 项原样保留、HUD 12 项、headless 11 场、单测 10 项。
> **P1 触发点**：D6「3D 成为主形态设终点」推翻 P0「2D L0 为默认主形态、探针默认关闭」。**凡以「2D 默认 / 探针默认关闭」为前提的断言必然反转**，必须逐条给替代判据；其余断言在 3D 形态下重放，期望值逐字不变。

### 3.1 P0 62 项中因 3D 默认化而失效/反转的断言

| # | 原断言（P0 编号） | 失效原因（3D 成为默认） | 替代判据（P1 编号） | 非放宽论证 |
| --- | --- | --- | --- | --- |
| **PF-01** | `BR-1[dev/build × 2 视口]` 默认关闭：主站**零 WebGL 上下文** / 2D L0 就绪（4 条） | 3D 成默认主形态后，主站**必须**有 WebGL 上下文；原断言方向完全反转 | `PV-1..PV-4`（4 组证据：WebGL 真创建、mesh/drawCalls/屏占比 >0、racing 时刻可见）+ `PM-*`；**降级路径另见 `PDEG-*`，不作本条 FAIL 证据（X11）** | **↑ 更严**：从「零上下文」升级为「必须证明三车真实可见且可量化」，不是删断言 |
| **PF-02** | `BR-2` 探针开启：立方体 + FogExp2 纸雾（4 条） | P0 探针是「一个立方体」技术可行性切片；P1 是玩家车 + 2 NPC + 赛道，`boxes=1` 不再是验收对象 | `PV-2/3`（mesh≥3、三车可区分）+ `PC-*` 相机 + `PR-*` 只读 + **`PVIS-5` 光照单独定义** | **↑ 更严**：`boxCount==1` → `meshCount>=3` 且三车 id 可区分；纸雾判据沿用 `fogIsExp2` 布尔（A.8，禁 `fogType` 类名字符串）。**光照注**：P1 主站 `lightCount=2`，**不复用** probe `lightCount=1`；`probe.jsx`/`probe.html` 逐字不动 → P0 62 项继续原样全绿，A6 关闭 |
| **PF-03** | `BR-3` `#probe-toggle` 一键关 3D（4 条） | 探针独立入口 `/probe.html` 在 3D 主形态下不再是默认开关模型；若 P1 保留 `RENDER_MODE=2d|3d` 则开关语义变为「回退 L0」 | `PR-*` 中 L0/L1 与 L2 判定逐位一致 + `PM-*` 两种形态各跑一局；若 #28 保留开关则 `PV/PC` 在两形态各取证 | 强度不降：仍验「可关回 2D 且判定一致」，改的是入口取法 |
| **PF-04** | `BR-4` `#probe-back` 关回 2D 主站（4 条） | 同上；`/probe.html` 不再是主路径 | `PM-*` 中 `RENDER_MODE=2d` 回退路径 + URL/入口参数化 + `PDEG-*` 自动降级路径 | 强度不降 |
| **PF-05** | `BD-4[dev/build]` **2D L0 主形态**可用（`mode='title'` / `__rally` / `#c` / `#minimap` 就绪） | 默认形态改为 3D；`#c` 2D canvas 不再是主渲染面 | `PV-*` + `PM-*` + `BD-4'`（3D 主形态下 `__rally` 只读 getter 仍挂载、判定结果一致）+ `PDEG-*` 降级可玩 | **↑ 更严**：新增 3D 形态取证；2D 形态仍按 L0 回退/降级重放，不删 |
| **PF-06** | `BV-*` dev/build 资源按字节送达（14 条） | 3D 引入 GLB / 模型 / 新 vendor 资源，代表性资源集需扩充；四重判定口径本身**不变** | `PVB-*` / `BV-*`（资源集按 #28 产物扩充，四重判定逐字不变）+ §5 C6 线上复核 | 口径不变，只扩资源集 |
| **PF-07** | `BC-2/BC-3` 产物层 `VENDOR_TAG` N=3 / 两层互不混算 | P1 若引入社区模型（D2）与 3D vendor，N 会变；但「各自唯一、互不混算、扫描根隔离」六项约束**不变** | `PB-*` | 六项约束逐字沿用 A.1，N 由产物定型，不预设数字 |
| **PF-08** | `BQ-2` 探针 overlay 检测面（2 条） | 3D 主形态下 overlay 不再是「独立探针页」，而是常驻 HUD / 3D DOM 层 | `BQ-2'` / `PQ-4`（3D 主形态 DOM 检测面，83 词 + 4 字段名 + 完整词/IPA 硬断言，A.5 口径）+ **`PQ-5` 3D 层零答案域读取** | 检测面**扩大**而非缩小，词表/口径逐字不变 |
| **PF-09** | `BE-*` 四项错误计数（4 条） | 3D 新增 WebGL 上下文丢失/恢复事件、`webglcontextlost` 等新噪声源 | `PE-*` 新增 WebGL 事件单列类别，四项硬归零逐字保留 + `PDEG-2` 恢复后不跳门 | ↑ 更严（新增分类，不豁免同源） |
| **PF-10** | `H1–H4` / `H7–H8` / `H11`（2D HUD DOM、显隐、路牌、tag） | 3D canvas 成为主渲染面后，2D HUD DOM 是否保留需 #28 确认；若保留则断言原样重放，若改造则逐条重定义 | `PM-*` 顶栏不遮挡 / `PQ-*` 零泄露 / `PB-*` tag / §3.3 保留清单 | **不得静默删除**：每一条 H 断言在实跑报告中必须有 PASS/FAIL 或明确的「替代 = 编号」 |

> **10 个失效族**（PF-01~PF-10）覆盖 P0 62 项中的 **BR 16 条 + BD-4 2 条 + BV 资源集扩充 + BC N 值 + BQ-2 2 条 + BE 分类 + H 系列**。**没有一条被删除、放宽或改 NOTE**；BR 16 条全部由 `PV/PC/PM/PR/PVIS/PDEG` 承接且强度上升（零上下文 → 三车可量化可见 + 六维阈值 + 降级不白屏）。
> **【v1.1 补充裁决 C-3 协调】** PF-01「3D 默认主形态下主站必须有 WebGL 上下文」与裁决 B-3「WebGL 不可用 / contextlost → 自动降级 2D L0 不白屏」**不冲突**：正常路径 `PV-1..PV-4` 证 WebGL 真创建 + 三车可量化可见；**降级路径单独一组 `PDEG-1..4`**（模拟不可用 / 触发 lost）证切到 2D 且三车仍可玩、听音选车道可完成、不白屏、判定逐项一致。**不要把降级路径当成 PF-01 的 FAIL 证据**（X11）。
> **【v1.2 · 用户 2026-11-12 退役裁决后的 PF-07 / PF-10 状态更新】** 四套旧门控整体退役（乙）后：① **PF-07**——F-1/F-3/F-4/F-5 四条扫描域 FAIL 随旧套件退出判定链而**不再是发布阻断**，但**不得定性为「已修复」**：产品层 `{hud-20261108:46}` / 20 图零裸引用仍须由 `PB-1..PB-4` 在新套件逐条重验（正确扫描域 + 依赖层单列断言），`verify_p0_gate.py` 62/62 为现行载体；② **PF-10**——`verify_hud_spec.py` 归档、退出判定链，但 H1–H12 **逐条迁入新套件**（退役令 §4.3），H11 的 FAIL 原文 / 命中明细 / 退出码**永久保留**在 `p1-legacy-gate-fail-scan.md` §2 F-5，**不因退役抹掉、不改 NOTE、不放宽**。完整 10 族状态表见 `design/p1-gate-retirement.md` §6。

### 3.2 四套门控 110 项的 P1 增量判定（v1.2 · 用户 2026-11-12 裁决乙：整体退役 + 81 项迁移重放）

**用户 2026-11-12 书面裁决（乙 · 四套旧门控整体退役）**：四套旧门控（清单见 `design/p1-gate-retirement.md` §1.1）**不再作为发布阻断判据**，其 `exit code` 不计入 G1；但 **81 项断言一条不删**——期望值逐字不改，从旧四套**迁移到新 P1 套件**、用正确扫描域（排除 `node_modules/` / `dist/` / `.p0-build/` / `.workbuddy/`）重放，逐条承接编号 `PLR-*` 见该令 §3（**81 行零空白**）。

P0 已判定 29 项重定义 + 81 项原样保留（§3.3）。P1 相对 P0 **不新增失效族到 81 项保留域**——因为 81 项全部是「判定核心源码字面量 / 跨站存档逻辑 / 美式文案基线 / Node 自检」，与渲染形态无关。退役后仍须在 **3D 主形态下把 81 项迁移重放一遍**（不是只在 2D L0 下），证明 3D 默认化与载体迁移都没有破坏它们。**11-11 实跑的 6 条真实 FAIL 全部落在 29 项重验域 / HUD 12 项 / 辅助脚本，无一落在 81 项保留域**（`p1-legacy-gate-fail-scan.md` §2/§3；退役令 §4.1），这是「退役 ≠ 删断言」的实证。

> **「门控全绿」权威口径（2026-11-12 用户裁决乙后生效，逐字）**：
> ```
> 门控全绿 = 路线 B 重定义套件实跑
>            · verify_p0_gate.py 62 项（继续原样全绿，不退役）
>            · verify_p1_gate.py 实跑（#46 实跑化后；K1–K5 映射 5/5 满格，共 62 条新增/重定义 chk）
>          + 81 项迁移重放（p1-gate-retirement.md §3，正确扫描域，期望值逐字不变）
>          + node js/headless_laps.mjs 11 场 ALL PASS（max ≤180s）
> ```
> **四套旧门控 `exit code` 自 2026-11-12 起不计入上式**（用户裁决乙 · 整体退役；退役的是「发布阻断判据地位」，不是删断言）。
> **不等于「原始 110 项原样全绿」**（X9）：Vite/R3F 构建链下 110 项中的 29 项已物理失效（#20/#27 F-01~F-12），且旧套件扫描域缺陷已由 11-11 实跑实证，写死会把终点锁死。失效断言逐条给重定义依据、禁止静默放宽，主理人逐条复核。#29 `D6-G02` / §3.7 / R4 / §6-9 已按 `110 = 29 重验 + 81 原样保留` 关闭等价性风险（C3）。**终点定义本身不变**：D6 =「门控全绿 + 375px 可玩」用户已拍板，本次只改「门控全绿」的组成与载体。

### 3.3 81 项保留清单（逐条枚举 → 迁移到新套件重放，承接表见 `p1-gate-retirement.md` §3）

> 口径：`110 = cseg_gate 38 + cseg_ui 14 + fresh_gate 21 + c08_gate 37`；P0 判定 29 项重验（cseg_gate 2 + cseg_ui 14 + fresh_gate 6 + c08_gate 7），其余 **81 项原样保留** = 36 + 0 + 15 + 30。**期望值逐字不改，仅在 3D 主形态与新 base URL 下重放。**
> **载体迁移（2026-11-12 生效）**：旧四套退役后，本节 81 项不再由 `verify_cseg_gate.py` / `verify_fresh_gate.py` / `verify_c08_gate.py` 承载，而是逐条迁移到 `verify_p1_gate.py` 的 `PLR-*` 重放族；**原编号 → 承接编号 → 重放方式 → 期望值逐字不变** 的 81 行完整映射见 `design/p1-gate-retirement.md` §3（**零空白行**，满足 §0.3）。迁移只换载体与扫描域，**不换期望值、不删条目、不放宽阈值**。

**（1）`verify_cseg_gate.py` — 36 项**

| 组 | 编号与简称 |
| --- | --- |
| S1–S16（16） | S1 `TUNING.laps===2` / S2 提速 follow260·listen300 / S3 终点 `laps×L` / S4 `g.line` 绝对里程 / S5 rival `upcoming.line` / S6 跨圈复位 `pickups[].taken` / S7 进度条分母含 laps / S8 开局按地图建门 / S9 四区与车手选择器接 UI / S10 教学面板杯赛重点（C07 静态块保留） / S11 quiz 三题型且 word 题不泄答案 / S12 `placeLaneSign` 传绝对 odo / S13 render 只收当前圈（两圈 commitT 相同不重绘） / S14 结果页解锁取并集 / S15 跨站白名单含 `maps/lastMap/lastChar` / S16 atlas 6 处图片 URL 全带 tag |
| A0–A6（7） | A0 headless 退出码 0 / A1 2 档×4 地图+3 最坏=11 场 / A2 全部 ≤180s / A3 最坏工况（15 碰撞+20 全错）≤180s / A4 headless 含 4/4 门判定与跨圈 1 次 / A5 `result.time===finishTime` / A6 理论 `2×L/speed≤150s` |
| B0–B9（10） | B0 Node 自检可运行且输出可解析 / B1 四区地图非空、词对≥24、音素≥16 / B2 准确性（unit 绑定·ipa 与权威表一致·最小对立互异·0 错配） / B3 音频 100% 覆盖 `allWords()` / B4 题型≥3 / B5 固定题 0、任一词对出现率≤60% / B6 单局 4 门词对互不重复（12000 局） / B7 单局题型≥2 且三题型都出现 / B8 额外题连续同对率 0（去重窗口 3） / B9 `ipa-display.js` 全文未动 + `sym` 稳定键 |
| C1–C3（3） | C1 音频文件数 == `allWords()` 词数 / C2 全部 mp3 帧头有效且无 <500B 残 file / C3 生成脚本以 `config.allWords()` 为单一词表来源 |

**（2）`verify_cseg_ui.py` — 0 项**

> 14 项（U1–U7、U8×3 题型、U9–U12）在 P0 已按 F-10 判为「换 base URL 重放」，计入 29 项重验而非 81 项。**口径澄清**：P0 规格 §4.1 把 U10（解锁并集）/U11（跨站不覆盖）列入「原样保留域」，指的是**期望值逐字保留**；其测法仍随入口参数化。本规格沿用 P0 的 81 项口径，并追加硬约束：**U10/U11 的期望值不得因 3D 默认化改变**（与 K2 的 `rally.unlocked` 并集联动）。

**（3）`verify_fresh_gate.py` — 15 项**

F1 英式符号残留 0 / F1b `ː` 仅出现在 10 行 `sym` 稳定键 / F2 长短音·央化旧措辞残留 0 / F3 `/e/` 六行改 `/ɛ/` 且 `eɪ` 未被误伤 / F4 25 组 `episodes/phonemes` 镜像逐字一致 / F5 逻辑枚举键锁定 + D01–D05 美式显示文案在场 / F6a 与持久化已验收基线逐字一致（不回退 + sha256 全等） / F6b 图片·音频字段名与 `eɪ` 次数未改 / F6c 上游构建管线未重跑（mtime 早于 `data.js`） / F7 11 个重点 unit 教学文案走查无残留 / F9a G5 纯净页图鉴 48 卡大字全为美式 / F9b G5 卡面图·总图 URL 带当前 tag 且 `U11=ɜr` / F9c G5 49 张发布卡面与美式源逐字节全等 / F11a G4 老存档迁移逐字节回滚点（`collected=[]`/`legacyCollected`/v2） / F11b 跨站 last-write-wins 不覆盖。

**（4）`verify_c08_gate.py` — 30 项**

| 组 | 编号与简称 |
| --- | --- |
| S1.1–S1.6（6） | 迁移与 reset 走 `writeRaw` 绕过 merge / storage 监听不触发迁移·不写 bak / `save()` 写前重读 + 只并子字段 / 写点全收口 `commit` / `race.js` 无 `saveWallet`·绝对值写回 / 逻辑键与版本串未动 |
| D1.1–D1.5（5） | `v1.bak` 逐字节等于原串 / `collected` 已清空 / `legacyCollected` 恰为原 8 sym / `schemaVersion=2` 且 `unlocked=[]` / 迁移产物不含任何拉力赛 `rally` 子字段 |
| D2.1–D2.3（3） | 连续加载 bak 不覆写·快照不重复·`unlocked` 不重置 / `rawHasV2` 判据 / 从 `v1.bak` 逐字节还原后可重新迁移 |
| D3.1–D3.3（3） | B 的 `rally` 进度（gems/shields/EP02/owned*/howSeen/paint）全保住 / A 自己 `stars/lastEp/sound` 写入成功 / B 写入的 `unlocked` 未被陈旧快照抹掉（并集生效） |
| D4.1–D4.3（3） | `unlocked` 并集含 U07+U02 / 改 `unlocked` 不影响知识轨（`collected` 恒 []） / 卡轨 `isCardUnlocked` 生效且与 `hasLearned` 解耦 |
| D5.1–D5.2（2） | `storage` 事件刷新内存 `data.rally` / 监听未触发第二次迁移·未写 bak |
| D6.1–D6.2（2） | `+1` 与 `-100` 两种交错顺序最终 gems 都为 1（无双花/无回滚） / 源码无绝对值写回且 delta 函数存在 |
| D8.1–D8.3（3） | `race.js` 石头纯规避（仅 `ribbonT`） / `finishQuiz` 不污染 `correct`·不给额外奖励 / 源码保留 `pointerdown/jumpEdge` 触屏跳跃 |
| D9.1–D9.3（3） | 可见文案 C 类残留命中 0 / D9.2 真双元音滑动描述逐字未动 / 两题 `options` 长度·顺序·answer 不变 |

> **合计 36 + 0 + 15 + 30 = 81 项**。另有 `verify_hud_spec.py` 12 项 HUD 专项、`minimap_model.test.mjs` 10 项、`headless_laps.mjs` 11 场，不属于 110 项口径，但按 §3.1 PF-10 与 K1 在 P1 中同样重放。
> **退役后覆盖承接**：HUD 12 项逐条承接见 `p1-gate-retirement.md` §4.3（PF-10 硬约束，H11 真实 FAIL 原文永久留痕）；29 项重验域见该令 §4.2；辅助脚本 8 项有效断言见 §4.4。**6 条真实 FAIL 无一落在本节 81 项**（该令 §4.1）。

---

## 4. 3D 主形态终点验收判据（Go/No-Go 表 · 用户已拍板终点定义，逐条可执行化）

> **用户问卷终点（主理人 #31 派单原文 + 裁决 B-8）**：「**门控全绿 + 375px 可玩**」，**已由用户拍板**。本规格把这句已拍板定义拆成逐条硬条件，**不重开、不替换、不另立第三套口径**；`p1-gameplay-spec.md` §3.5 甲/乙/丙三候选已归档为**历史候选存档**（甲 = 已拍板口径，乙 / 丙作废），仅供追溯。
> **仍待用户裁决（终点达成之后的执行项，非终点定义本身）**：2D L0 退役时点 / 是否收敛为单一 3D 形态 / 保留期（G10）、G8 发布前置、最终放行与发布签字。**G9 为上线后观察项 / advisory，不计入 G1、不作发布阻断**。**本报告不预设终点已达成**（须实跑），也不替用户判退役。

### 4.1 Go/No-Go 表

| # | 条件 | 硬判据（可验证） | 证据来源 | 判定 | 裁决方 |
| --- | --- | --- | --- | --- | --- |
| G1 | **门控全绿** | **路线 B 重定义套件**（`verify_p0_gate.py` 62 PASS / 0 FAIL + `verify_p1_gate.py` `SUMMARY: N PASS / 0 FAIL / N TOTAL`，K1–K5 映射表 5/5 满格、无空格，含 `PVIS-*` / `PDEG-*` / `PQ-5`）+ **81 项迁移重放全绿**（`p1-gate-retirement.md` §3 承接表，正确扫描域、期望值逐字不变）+ `headless_laps.mjs` 11 场 ALL PASS；四项退出码全 0。**四套旧门控 `exit code` 自 2026-11-12 起不计入判定链**（用户裁决乙）；**≠ 原始 110 项原样全绿（X9）** | `verify_p1_gate.py` 实跑日志 + `result.json` + 退役令 §3 逐行 PASS 记录 | 待实跑 | QA 判定 → 用户放行 |
| G2 | 判定核心确定性 | `race.js/track.js/config.js` sha256 双重锚定全等；11 场 ALL PASS 且 max ≤180s；3D/2D `finishTime` 逐项一致 | `headless_laps.mjs` + K1 | 待实跑 | QA |
| G3 | **375px 可玩** | 375×780 与 320×568 各走完 2 圈 4 门 → results；左右选道 / `#jump` / quiz 三题型全程可操作；零横向溢出、顶栏不遮挡 | `PM-*` + 人工过眼 V 清单 | 待实跑 + **人工签收** | QA + team-lead 代签 |
| G4 | 3D 真的可见 + 视觉达标 + 降级可用 | 玩家车 + 2 NPC mesh/drawCalls/屏占比 >0 且可区分；相机跟随单调、远端收敛、无俯视；**`PVIS-1..6` 六维阈值全过**；**`PDEG-1..4` 降级 2D L0 不白屏且仍可玩** | `PV-*` / `PC-*` / `PVIS-*` / `PDEG-*` | 待实跑（PVIS-3 须人工盲测签收） | QA |
| G5 | 五类断言零降级 + 3D 零答案域 | K1–K5 逐条保留；失效清单每条有替代编号；**81 项迁移重放**（退役令 §3）在 3D 形态下重放全绿；**`PQ-5` 3D 层零答案域读取（与 H5 串联）** | §1 / §3 / §6.3 / `PQ-5` / 退役令 §3 | 待实跑 | QA |
| G6 | 双层缓存 / 零裸引用 | 源码层 46 + 产物层 N 各自唯一、互不混算；20 图零裸引用 | `PB-*` | 待实跑 | QA |
| G7 | 四项错误计数归零 | `pageerror / 硬console_error / bad_status / 同源真实失败` 全 0；`ERR_ABORTED` / 外链 / Vite 机制 / WebGL 事件单列 | `PE-*` | 待实跑 | QA |
| G8 | 发布前置 C2–C6 | 见 §5；`deploy.sh` 含 `音标拉力赛/`、两站同源、资源按字节送达 | `PX-*` | **Phase B #32**，本轮不判 | 用户 / 主理人 |
| G9 | 3D 眩晕风险（**上线后观察项 / advisory**） | 缓释手段：`prefers-reduced-motion` 下抖动 / 侧倾 / FOV 呼吸 / 速度线全归零、抖动 ≤3px、禁全屏径向模糊 / 景深 / bloom（`p1-3d-art-spec.md` §2.6 / §5）；`PVIS-3` 24px 剪影盲测归入 G4 客观判据。若用户后续明确要求儿童实测（3–5 名试玩 30s 主观眩晕评分），另立任务 | 缓释项实跑证据 + 上线后观察记录 | **不计入 G1 门控全绿、不作发布阻断** | QA 建议 / 用户可选 |
| G10 | **L0 退役执行 / 单一 3D 形态收敛时点**（终点定义已拍板） | 「门控全绿 + 375px 可玩」终点定义**已拍板**，G1–G7 即其可执行化；**仍待裁决**：2D L0 何时退役、是否收敛为单一 3D 形态、保留期、三方联签与用户签字（交叉引用 `p1-gameplay-spec.md` §3.3 `D6-G12` / §6-7 / §6-8） | 用户拍板 + 三方联签建议书 | **终点定义已拍板 · 退役时点待裁决** | **用户** |

### 4.2 QA 对终点的立场

1. **门控全绿 ≠ 可发布**：G1–G7 全绿只证明本地 P1 质量；G8（发布前置同源部署 / 逐字节复核）、G10（L0 退役时点与用户签字）未满足前，QA **不判发布 PASS**。G9 为上线后观察项（advisory），不在此列。
2. **终点定义已拍板、退役执行不与 P1 门控同批裁决**：`hud-final-qa-report.md` 已 PASS 的 2D HUD 资产与 **81 项迁移重放断言**（退役令 §3）是当前唯一的判定/显示回退基线；在 G10 用户签字前保留 L0，是**风险缓解**而非「不执行 D6」。
3. **CONCERNS 不静默放行**：若 G3 缺少人工签收，或 G4 在 headless 无 WebGL 下证据 MISSING，判 **CONCERNS / 证据 MISSING** 并上报，不改判 PASS、不把 FAIL 改 NOTE。
4. **质量门 advisory**：以上均为建议性门控，最终放行与发布签字由用户决定。
5. **【v1.1 新增】口径一致性**：终点定义 = 用户已拍板「门控全绿 + 375px 可玩」，本规格只做可执行化；`p1-gameplay-spec.md` §3.5 三候选（甲/乙/丙）已归档为**历史候选**（甲为已拍板口径，乙 / 丙作废），不得替换用户口径，也不得据此把 G10 写成「终点未拍板」。QA 已就此口径张力提请 #29 同步（§0.6 留痕）。

---

## 5. 发布前 C2–C6 验收方式（`PX-*`，本轮只登记，Phase B #32 执行）

> **现状事实**（QA 独立读盘复核）：`音标大闯关/deploy.sh` 的 `SRC` 指向 `音标大闯关/`，四条 `scp` 只发 `index.html` / `js` / `css` / `assets/sprites` / `assets/audio/ph`，`DEST=/var/www/ipaquest`；**完全不含 `音标拉力赛/`**；项目 `fatal: not a git repository`；诊断 §1 实测线上 `/音标拉力赛/index.html` 返回 3076 B 的大闯关首页（Caddy SPA fallback 兜底 200）。

| # | 前置 | 验收方式（PASS 判据） | 证据 |
| --- | --- | --- | --- |
| **C2** | `deploy.sh` 不含 `音标拉力赛/` | 逐行静态验 `deploy.sh` 含 `音标拉力赛/` 的 scp 条目；部署后线上 `GET /音标拉力赛/index.html` 按**逐字节 + magic + sha256 + Content-Type 非 `text/html`** 与本地比对，**不得**是 3076 B 大闯关首页；`/音标拉力赛/js/...` 同样复核 | `deploy.sh` diff + 线上 HTTP body 取证 |
| **C3** | 项目无 git 仓库 | `git rev-parse --is-inside-work-tree` 成功；首次提交**排除** `node_modules/`（9361 文件）/ `.p0-build/` / `.workbuddy/`；提交后 `git status` 干净；**`.workbuddy/backups/` 是项目数据，不得当缓存清理**（R3） | `git log -1` + `.gitignore` + 快照完整性复核 |
| **C4** | `scp` 交互式提示 SSH 密码 | 非交互环境**不得**由 QA 代输密码；须用户本地执行或提供凭据/免密；QA 只验「部署后资源按字节送达」，不接触凭据 | 部署执行记录（用户侧） |
| **C5** | D1 拍板「保持源码 scp 同源」 | 两站部署到**同一 origin 同级目录**；`location.origin` 相等；拉力赛侧写 `rally.*` → 大闯关侧读回逐字段相等，反之亦然；`unlocked` 并集生效（与 K2 / CN-4 联动） | 线上双站真实 Chromium 读写取证 |
| **C6** | 线上 Caddy 对不存在路径兜底 200 | **先探兜底**（`BV-0` 口径，A.3）：对不存在路径取证 `200 text/html` 并登记；据此锁定「状态码一律不可信」；每个**真实资源**按 **逐字节 + magic + sha256 + Content-Type 非 `text/html`** 四重判定，中文路径 percent-encode | `PX-*` 资源按字节校验表（dev / build / 线上三列） |

> **C1**（3D 卡丁车未实现）由 P1 解决，判据见 §2.1 `PV-*`；**D2 社区模型 provenance**：#30 已交付 `p1-3d-art-spec.md`（含 provenance / 参数化精灵造型 / 六维阈值），但 QA 本轮**只登记、不判合规结论**：若 #28 引入社区模型，须在 `vendor.manifest.json` / 资产清单中逐模型给出来源与 explicit permission 证据，QA 只验「证据存在且可追溯」，合规结论由用户/主理人裁决。

---

## 6. 编号体系、判据条数与覆盖映射

### 6.1 编号体系（沿用 P0 前缀 `B*` 便于对照，P1 新增域用 `P*`；v1.1 增补两族）

| 域 | 前缀 | 承接 | K 类 |
| --- | --- | --- | --- |
| 判定核心 | `PD-*` | K1：三文件 sha256 双锚定、11 场 headless、3D/2D 判定一致 | K1 |
| 跨站单键 | `PS-*` | K2：C08 白名单、`rally.unlocked` 并集、零写盘/零新增字段 | K2 |
| IPA 单一源 | `PI-*` | K3：等价时序、`U11=ɜr`、48 卡面、**`unit` 主键 / `sym` 稳定键 / 零 `displayIpa` 作键**、U05/U07 | K3 |
| 答案零泄露 | `PQ-*` | K4：H5 口径 83 词 + 4 字段名、3D overlay 检测面、`snapshot()` 键白名单、**`PQ-5` 3D 层零答案域读取** | K4 |
| 四项错误计数 | `PE-*` | K5：四项硬归零 + ERR_ABORTED/外链/Vite/WebGL 事件单列 | K5 |
| **3D 可见性** | `PV-*` | §2.1：WebGL 真创建、mesh/drawCalls/屏占比、racing 时刻、降级取证 | P1-1 |
| **跟车相机** | `PC-*` | §2.2：跟随单调、远端收敛、俯角/FOV 区间、无俯视、两车道可辨 | P1-2 |
| **375px 可玩** | `PM-*` | §2.3：完整一局、选道/跳跃/quiz、零溢出、顶栏、DPR、320×568、人工过眼 | P1-3 |
| **3D 层只读** | `PR-*` | §2.4：静态 6 项 + 运行时 hook + rAF 帧率 + 冻结 + 上下文恢复 | P1-4 |
| **D4 稀有度** | `PD4-*` | §2.5：禁三字段·不修三字段、`unit` 主键·`sym` 稳定键·零 `displayIpa` 作键、CI 公式逐条可复算·按 CI 单调、分布 14/12/9/6/4/3·UR、六档轮廓一致 | P1-5 |
| 双层缓存 | `PB-*` | §2.6：46 + N 各自唯一、互不混算、20 图零裸引用 | P1-6 |
| 资源送达 | `PVB-*` | 沿用 `BV-*`：dev/build 按字节四重判定（资源集按 P1 扩充） | T1/T5 |
| 失效/保留 | `PL-*` / `PLR-*` | §3：10 个失效族的替代承接 + **81 项迁移重放**（原编号 → `PLR-*` 承接编号，见 `p1-gate-retirement.md` §3） | P1-7 |
| **视觉六维阈值** | `PVIS-*` | **§2.8（v1.1 新增）**：材质层数 / 饱和度 / 24px 剪影 / 抖动 / 光照 2 盏+AO / 随距衰减 | P1-8 |
| **WebGL 降级 L0** | `PDEG-*` | **§2.9（v1.1 新增）**：不可用 / contextlost / 降级后可玩 / 判定逐项一致，与 PV 分表 | P1-9 |
| 终点汇总 | `PT-*` | §4：门控全绿 + 375px 可玩 两条汇总硬门 | Go/No-Go |
| 发布前 C2–C6 | `PX-*` | §5：5 条发布前验收（**不计入本地 P1 门控 TOTAL**） | Phase B |

> 注：`PD-*` 与 `PD4-*` 前缀相近易混，实跑脚本中分别写作 `PDCORE-*` / `PRARITY-*`；`PVIS-*` / `PDEG-*` 脚本同名。本规格为可读性保留表中写法，报告须用脚本实际名。

### 6.2 判据条数（规格阶段定义，TOTAL 实跑时按 #28 产物定型；v1.1 重算）

| 类别 | 条数 | 说明 |
| --- | --- | --- |
| K1–K5 五类（P0 62 项承接/扩展） | **19** | `PDCORE 5 + PS 3 + PI 4 + PQ 5 + PE 2`（PQ 因裁决 B-4 新增 `PQ-5` 3D 零答案域，4→5） |
| P1 原六族硬判据（§2.1–2.6） | **31** | `PV 5 + PC 4 + PM 7 + PR 6 + PRARITY 5 + PB 4` |
| **新增 `PVIS` 视觉六维（§2.8）** | **6** | 裁决 B-2 / B-5；`PVIS-1..6` |
| **新增 `PDEG` 降级 L0（§2.9）** | **4** | 裁决 B-3 / C-3；`PDEG-1..4` |
| 终点汇总门 `PT-*` | **2** | 门控全绿 / 375px 可玩 |
| 81 项迁移重放 `PL-*` / `PLR-*` | **81** | §3.3 逐条枚举；退役后由旧四套迁移到新 P1 套件、正确扫描域重放；承接表见 `p1-gate-retirement.md` §3（条数不变） |
| **本地 P1 门控规格定义合计** | **143** | `19 + 31 + 6 + 4 + 2 + 81`；**此为规格定义的判据条目数，不是实跑 SUMMARY 数字** |
| 发布前 C2–C6 `PX-*` | **5** | 单独登记，Phase B #32 执行，不计入本地 P1 TOTAL |
| 失效清单 | **10 族** | PF-01~PF-10，每条有替代编号，非 chk |

> **TOTAL 纪律（沿用 `p0-qa-spec.md` §6.2）**：实跑 SUMMARY 的 `N TOTAL` **在 #28 产物定型后确定**（`PVB` 资源集、`PB` 的 N、探针/相机/视觉组合数都会变）。规格阶段给出**下限 143** 与逐条清单；**禁止先拍一个数字再凑断言**。报告须写明「TOTAL ≠ 110 / ≠ 62 / ≠ 132 是允许的，但 §6.3 映射表必须满格」。
> **v1.1 变更留痕**：v1.0 为 132 条（`51 + 81`）；按主理人补充裁决新增 `PQ-5`（+1）、`PVIS`（+6）、`PDEG`（+4）共 **+11 条硬 chk**，规格定义合计 `132 → 143`；均为**新增/加严**，无一条删除或放宽。
> **v1.2 变更留痕（2026-11-12 用户裁决乙 · #45）**：四套旧门控整体退役，**81 项断言一条不删**，载体由旧四套迁移到新 P1 套件（`PLR-*` 承接编号，见 `p1-gate-retirement.md` §3）；「门控全绿」组成同步改写（§3.2 / G1 / G5）。**规格定义合计仍为 143 条**（`62 + 81`）：无一条删除、无一条放宽阈值、无一条把 FAIL 改 NOTE；改的是**载体与判据地位**，不是覆盖面。

### 6.3 K1–K5 覆盖映射核查表（实跑报告必填、必须满格）

| 类别 | `p0-slice-spec.md` §1 要求 | P1 承接编号 | 原断言 | 强度对比 | 满格? |
| --- | --- | --- | --- | --- | --- |
| K1 | 两圈 / 门线 `g.line` / 听音题正确性 / 11 场 ≤180s | `PDCORE-1..5` + `PL-*` 36 项 | S1–S8/S13/A0–A6/U6/U8/H10/T0–T7 | ≥ 原（新增 3D/2D 逐位一致 + 双快照锚定） | ☐ |
| K2 | 跨站单键保真 / C08 白名单 / `rally.unlocked` 并集 | `PS-1..3` + `PL-*` D1–D6 | D1–D6/U10/U11/F11a/F11b/H12 | ≥ 原（新增零新增字段） | ☐ |
| K3 | `window.IPA_DISPLAY` 单一源 / 稳定键（U05/U07） | `PI-1..4` + `PRARITY-2` | F1/F1b/F2/F5/F9a/F9b/B2/B9/D7.4/H11/`D4-A02/A03` | ≥ 原（按 `unit` 主键 48/48 唯一 + `sym` 48/48 唯一 + 零 `displayIpa` 作键；C1 键契约） | ☐ |
| K4 | 83 词全表 + 4 字段名零泄露（H5 口径） | `PQ-1..5` | H5/H6/H8/U8/S11/`D3-Axx`/`F6` | ≥ 原（新增 3D overlay 检测面 + **3D 层零答案域读取 `PQ-5`**） | ☐ |
| K5 | 四项计数归零 / ERR_ABORTED 单列 / 同源真实 0 | `PE-1..2` | U1/U12/F11d/D7.5/H12 | ≥ 原（新增 WebGL 事件分类） | ☐ |

> **任一格空格或未填 → 判 FAIL**（覆盖面缩水），不得以「PASS 数够多」替代。**九族**（含新增 `PVIS` / `PDEG`）新增判据另在报告中按域逐条汇总。

---

## 7. 回归运行纪律（沿用 `hud-qa-plan.md`，按 P1 扩展）

### 7.1 串行顺序（浏览器门控不并行）

```
# 0 静态自检（不启浏览器）：三文件 sha256 双锚定 / 源码层 46 / 产物层 N / 扫描根隔离 / 81 项迁移重放清单核对（退役令 §3 PLR-*）/ #29 D4 JSON 不变式复核
# 1 路线 B 基线：python -B verify_p0_gate.py → 62（继续原样全绿，不退役）
# 2 P1 新门控：python -B verify_p1_gate.py（含 81 项 PLR-* 迁移重放 + K1–K5 + PVIS/PDEG/PQ-5）
# 3 退役四套（verify_cseg_gate / verify_cseg_ui / verify_fresh_gate / verify_c08_gate）：自 2026-11-12 起移出判定链，仅归档可手动跑，exit code 不计入 G1（用户裁决乙）
# 4 两圈实跑：node js/headless_laps.mjs（原路径原命令，11 场 ≤180s）
# 5 纯函数单测：node js/minimap_model.test.mjs（10 项）
# 6 P1 新门控域明细（与 #2 同一脚本）：自起 dev/build 服务，串行跑 PV/PC/PM/PR/PRARITY/PB/PVIS/PDEG/PVB/PE + PLR-* 迁移重放
# 7 人工过眼：375×780 / 320×568 / DPR 2·3 / V1–V17 相关项 / PVIS-3 24px 剪影盲测 / Playtest 30 秒主观签收（G9 上线后观察项 / advisory，不计入 G1）
# 8 发布前 PX-*：待 Phase B #32 通知，本轮不执行
```
> **服务生命周期**：沿用 #20b 可靠方案——由 `verify_p1_gate.py` 用 `subprocess.Popen` 自起 dev(5173)/preview(4173)，`wait_port` 就绪后串行跑，`finally` 显式 `terminate()` + 端口复核。**不得**用后台 `&` 起服务（#20b 首跑实测子进程随 shell 退出被杀）。

### 7.2 `ERR_ABORTED` / `ERR_CONNECTION_REFUSED` 明细区分（不放宽）

逐字沿用 `hud-qa-plan.md` §3 / `p0-qa-spec.md` §5.2 / 附录 A.7：`ERR_ABORTED` 单列披露不计失败；同源非 `ERR_ABORTED` 真实失败**必须 = 0**；外链与 Vite 机制项单列、不得据此豁免任何同源项；`console.error` 按「计数配对 + `ConsoleMessage.location.url` 外部 host 校验」分类（A.7）；**FAIL 改 NOTE 一律禁止**。

### 7.3 已知瞬态事实与处置（不放宽断言、不改脚本、不视为产品缺陷）

- `stage-delivery-2026-11-09.md` §2.1 / `hud-qa-plan.md`：连续同批串行跑 7 脚本时 `verify_hud_spec.py` H12 曾出现 1 次 `fan.mp3 → ERR_CONNECTION_REFUSED`（音频实体存在 9792 B，in-process `ThreadingHTTPServer` 端口回收瞬态），单独重跑 2 次均 12/12、四项计数全 0。
- `p0-qa-report.md` §5：dev Google Fonts `ERR_CONNECTION_CLOSED` 外链事件真实复现过 1 次（run5），同源真实失败仍为 0，按 A.7 单列。
- **处置链**：① 明细逐条打印分类 → ② 单独重跑该脚本 2 次 → ③ 复核实体存在与 sha256 → ④ 端口/服务生命周期复核 → ⑤ 若两次重跑仍 FAIL 则**判真实 FAIL 并上报**，不得豁免 → ⑥ 全程登记为 NOTE/明细，不改任何脚本、不放宽任何阈值。
- **P1 新增 WebGL 上下文丢失事件**按同一纪律：单列披露 + 恢复后「不跳门」硬判定（§4.5-6 / `PDEG-2`），不因「环境项」静默豁免。

### 7.4 flaky 隔离

沿用 `p0-qa-spec.md` §5.4：固定 `wait_for_timeout` 改为 `wait_for_function` 条件等待；时序打点用 `Object.defineProperty` setter 同步捕获（#20b run4 实测 `setInterval` 轮询会 flaky）；短词子串改完整词 + IPA 硬断言（A.5）；**连续两轮 `SUMMARY` 与断言名集合逐条一致**才下结论（#20b run6/run7 口径）。隔离的测试不得污染 CI 信号。`PDEG-*` 的 WebGL 禁用 / contextlost 模拟须用**确定性 API**（启动参数 / `WEBGL_lose_context`），不得靠 `wait_for_timeout` 碰运气。

---

## 8. 登记表模板（实跑时逐表填写）

- **§8.1 四项错误计数表**：dev / build × 2D L0 / 3D 主形态 × 2 视口；列 `pageerror / 硬console_error / bad_status / 同源真实 / ERR_ABORTED / 外链 / Vite 机制 / WebGL 事件`。
- **§8.2 资源按字节校验表**：逐资源列 `路径 / 期望字节 / 实际字节 / magic / sha256[:16] / Content-Type / 是否 text/html / dev / build / 线上`；`BV-0` 先探兜底结果单列。
- **§8.3 3D 可见性证据表**：`视口 / 模式 / webglVersion / vendor / renderer / meshCount / 三车 id / drawCalls / 三车屏占比 / frames / contextLost / odo 时刻 / 像素非空证据`。
- **§8.4 相机参数表**：`机位高 / 俯角 / 水平 FOV / 阻尼时间常数 / 消失点 y / 可见赛道段占比 / 两车道投影间距`；对照 §B.1 区间。
- **§8.5 375px 可玩记录表**：`视口 / 圈数 / 门数 / 选道次数 / #jump / quiz 三题型 / finishTime / scrollWidth vs innerWidth / 顶栏相交数 / DPR 位图尺寸 / 人工签收`。
- **§8.6 CONCERNS / NOTE 登记格式**：沿用 `p0-qa-spec.md` §7.3 —— 每条含 `编号 / 性质 / 影响 / 处置 / 是否需裁决`；**FAIL 改 NOTE 一律禁止**；CONCERNS 不得静默放行。
- **§8.7 判定记录表**：沿用 `p0-qa-report.md` §8，含 K1–K5 映射满格、**九族**逐域汇总、稳定性（连续两轮一致）、质量门判定（PASS / CONCERNS / FAIL）、遗留风险、advisory 声明。
- **§8.8（v1.1 新增）视觉六维阈值表**：`维度 / 期望 / 实测 / 取法（脚本计算或盲测） / 过·不过`；含 `PVIS-5` 的 `lightCount`、柔补光强度、AO 覆盖率，以及 `probe.jsx`/`probe.html` sha256 与 P0 前快照全等复核列。
- **§8.9（v1.1 新增）降级路径表**：`触发方式（WebGL 不可用 / contextlost / 低配）/ 是否白屏 / 2D 三车可玩 / 听音选车道完成 / 完整一局 / finishTime 与 L0 基线逐项一致 / 与 PV 正常路径分表标记`。
- **§8.10（v1.1 新增）D4 教研校验表**：`units.length / unit 唯一 / sym 唯一 / displayIpaForKey / CI 公式逐条 / band 逐条 / forbiddenFields 交集 / distribution 六档 / 档位边界 CI 不倒置 / UR=ɜː θ ð`；按 `D4-Axx` ID 逐行登记。

---

## 9. 回滚点与项目数据声明

- `.workbuddy/backups/` 属**项目数据、不是临时缓存，不得清理**（R3）；现有 `c07b-data-baseline.js` / `baseline-meta.json` / `hud-20261109/` / `p0-pre-20261109/`（374 项 `/ 373 全等`）/ `p0-evidence-20261109/`（384 条 + `qa/` 子目录）全部保留。
- 唯一已知快照差异：`design/3d-adr.md`（#26 路线 B 计划内 ADR 更新），已定性为**文档变更非产品漂移**，见 `qa/qa_postclose_verify.log`。
- **P1 改动前须新建全量快照**（建议 `.workbuddy/backups/p1-pre-<日期>/`），含产品代码 + 五套门控脚本 + `deploy.sh` + `vendor.manifest.json` + **`p1-gameplay-spec.md` / `p1-3d-art-spec.md` / 本规格**；manifest 写明日期、字节、sha256 与可回滚范围；K1 的「双快照锚定」依赖此快照。
- **P0 探针零改动核对点（v1.1）**：`probe.jsx` / `probe.html` 须逐字不动（sha256 与 `p0-pre-20261109` 快照全等），确保 P0 62 项继续原样全绿；`PVIS-5` 的 `lightCount=2` 只作用于 P1 主站场景。
- 回滚按 manifest 相对路径 copy 回源根、逐文件按 sha256 前 16 位复核；回滚后重跑 `node js/headless_laps.mjs` 11 场 + 源码层 46 断言，确认回到 2D L0 基线。
- 项目**无 git 仓库**（C3）；建仓与首次提交属 Phase B #32，需用户单独批准。

---

## 10. 实跑前置：需 #28 / #29 / #30 提供的产物信息（v1.1 更新：#29 / #30 已到位，#28 仍占位）

| # | 来源 | 需要的信息 | 状态 / 影响的判据 |
| --- | --- | --- | --- |
| 1 | **#28 engineering-lead** | P1 只读可观测接口名与字段（类比 `window.__P0_PROBE__`）：meshCount / drawCalls / 三车屏占比或投影坐标 / frames / errors / contextLost | 占位 · `PV-*` |
| 2 | #28 | 相机与玩家 `odo` 的关联可观测性、`fov` / 俯角 / 机位高 / 远裁面、赛道采样点投影序列（远端收敛证据） | 占位 · `PC-*` |
| 3 | #28 | `snapshot()` 键白名单、3D rAF 与 `main.js frame()` 分离形态、localStorage 写入点、源码静态锚点（文件/函数） | 占位 · `PR-*` |
| 4 | #28 | 是否仍 `/index.html`、左右选道 / `#jump` / quiz DOM id 是否沿用、3D canvas `pointer-events`、2D/3D 开关形态 | 占位 · `PM-*` / PF-03/04 |
| 5 | #28 | dev/build 启动方式（vite dev 5173 / preview 4173？）、新增入口、headless 无 WebGL 的降级标识、`RENDER_MODE` 取值 | 占位 · 全部 / §7.1 |
| 6 | #28 | P1 新增文件清单、`vendor.manifest.json` 与 `VENDOR_TAG` / N、是否引入 GLB / 社区模型 | 占位 · `PB-*` / `PVB-*` / C2 |
| 7 | **#29 design-strategist** | ~~D4 权威映射表~~ | **已到位**：`p1-gameplay-spec.md` §2.3（48 全表）/ §2.8（JSON，48 条）/ §2.7（F1–F8）/ §2.10（`D4-A01..A12`）；按 ID 引用、不复述语义。`PRARITY-*`（本轮未落盘独立 `rarity-map.json`，QA 不预设落盘） |
| 8 | #29 | ~~「3D 主形态终点判据」边界与产物路径~~ | **已到位**：产品/体验侧定义、不含 `chk()`；按 `D3-A01..A09` / `D4-A01..A12` / `D6-G01..G13` ID 交叉引用。`D6-G02` 门控口径按主理人裁决 A 已定（§3.2）。**终点定义已由用户拍板**（裁决 B-8） |
| 9 | #29 | ~~听音选车道保真规格~~ | **已到位**：`p1-gameplay-spec.md` §1（`D3-Axx`）/ §1.6 判定链冻结 / §1.7 §9-7 未决；K2 / K4 / `PQ-5`。**§9-7 仍视为未拍板，不写成已决** |
| 10 | **#30 art-director** | ~~社区模型 provenance 清单与资产清单落点~~ | **已到位**：`p1-3d-art-spec.md`（§5 六维 / §4.8 光照 / §6.7 防泄题 / provenance / 参数化精灵）。QA 只登记不判合规结论（§5 C2 / D2 补充验收） |
| 11 | 主理人 | **实跑通知**（本轮不实跑）；G9 上线后观察项（advisory，不阻断）；**G10 L0 退役时点 / 单一形态收敛裁决**（终点定义已拍板） | 待通知 · §4 |
| 12 | **#28（v1.1 新增）** | `PDEG-*` 降级路径可观测点：WebGL 不可用 / `webglcontextlost` 的确定性模拟手段（`WEBGL_lose_context` / 启动参数）、2D L0 切换标识、降级后「三车可玩 / 听音选车道完成」取证接口 | 占位 · `PDEG-1..4` |
| 13 | **#28（v1.1 新增）** | `PVIS-*` 视觉六维可观测点：材质层数与 PBR 参数、光源列表与强度、主体 hex 色值、抖动峰值、细节随距衰减的采样接口；24px 剪影导出方式（盲测用） | 占位 · `PVIS-1..6` |

> 在 **1–6、12–13 未到位前**，规格以语义占位表述，**不预设字段名、不预设文件数、不预设 N**；判据硬要求逐字不变。**#29 / #30 的 7–10 项已到位，占位取消**；仍有 11 项主理人通知与 #28 八项工程输入待齐。

---

## 11. `verify_p1_gate.py` 骨架判据清单（脚本草案，本轮不实跑）

配套落盘 `音标拉力赛/verify_p1_gate.py`（**骨架**：判据清单常量 + `chk()` 框架 + `SPEC_ONLY` 守卫，`python -B` 仅做 AST/清单自检，不启浏览器、不连服务、不写判定结果）。实跑时按 §10 输入补齐字段与实现，编号逐条对齐本规格。

骨架中的 `CHECKS` 清单（域 → 判据名，共 **62 条新增/重定义硬 chk** = 19 + 31 + 6 + 4 + 2，另 `PL_*` 81 项由 `PL_CHECKS` 常量枚举）：

```
PDCORE  5 : 三文件 sha256 双锚定 / 11 场 headless ≤180s / 单测 10 项 / 3D-2D finishTime 逐项一致 / 浏览器判定一致性
PS      3 : C08 白名单重放 / rally.unlocked 并集 / 零写盘·零新增字段
PI      4 : 等价时序 / U11=ɜr + 48 卡面 / unit 主键·sym 稳定键·零 displayIpa 作键 / U05-U07 去重硬证
PQ      5 : H5 零泄露 / 词表 83 守卫 / snapshot 键白名单 / 3D overlay 检测面 / 3D 层零答案域读取
PE      2 : 四项硬归零 / 明细单列披露
PV      5 : WebGL 真创建 / mesh≥3 三车可区分 / drawCalls>0 / 三车屏占比>0 / racing 时刻可见
PC      4 : 跟随 odo 单调 / 远端收敛 / 俯角-FOV 区间·无俯视 / 两车道可辨
PM      7 : 375 完整一局 / 左右选道 / #jump / quiz 三题型 / 零横向溢出 / 顶栏不遮挡 / 320×568 + DPR
PR      6 : 静态 6 项零命中 / setItem 增量0 / snapshot 只读 / rAF 15·144fps 一致 / quiz 冻结 / 上下文恢复不跳门
PRARITY 5 : 禁三字段·不修三字段 / unit 主键·sym 唯一·零 displayIpa 作键 / CI 公式逐条可复算·按 CI 单调不降(禁整类) / 分布 14-12-9-6-4-3·UR=ɜː θ ð·档位边界不倒置 / 六档轮廓一致·牌面零文本
PB      4 : 源码层 46 / 产物层 N / 互不混算六项 / 20 图零裸引用
PVIS    6 : 材质 3-5 层可数 / 主体 S≤45% 可算 / 24px 黑剪影可辨(盲测) / 抖动≤3px / 光源 2 盏+AO(不复用 probe lightCount=1) / 随距衰减三档
PDEG    4 : WebGL 不可用降级不白屏 / contextlost 降级不白屏 / 降级后 2D 三车可玩·听音选车道可完成 / 降级前后判定逐项一致(不作 PF-01 FAIL 证据)
PT      2 : 门控全绿 / 375px 可玩
PL     81 : §3.3 逐条枚举（36+0+15+30）→ 退役后 PLR-* 承接（p1-gate-retirement.md §3）
```

> **SPEC_ONLY 守卫**：骨架在 `__main__` 打印 `P1 门控规格草案 / 实跑待主理人通知（#31）` 并 `exit(2)`，与 #5-PRE 的「HUD 元素未就绪」优雅报错同构；**绝不**在产物未定型时跑出误导性的全绿 SUMMARY。

---

## 12. 边界、Handoff 与质量门声明

- **本轮写入物仅 2 个**：`design/p1-qa-spec.md`（本文件，**v1.2**）、`verify_p1_gate.py`（骨架 v1.1，SPEC_ONLY；`#46` 由主理人本地实跑化，QA 不碰）。**#45 另新建** `design/p1-gate-retirement.md`（退役令 + 81 项承接表）。**未改**产品代码（`js/` / `index.html` / `css/` / 图片 / `data.js` / `ipa-display.js` / `deploy.sh` / 上游管线 / `probe.jsx` / `probe.html`）、**未改五套既有验收脚本**、**未改 `p0-qa-spec.md` / `p0-qa-report.md` / `p1-gameplay-spec.md` / `p1-3d-art-spec.md`**；未部署、未上线、未 commit、未建 git 仓库；**未实跑任何门控**。
- **v1.1 并入内容**：主理人两批 P1 门控口径裁决（A 门控口径 / B-2 光照 / B-3 降级 / B-4 零答案域 / B-5 六维 / B-6 D4 / B-7 边界 / B-8 终点 / C-1 C1 键契约 / C-2 C2 单调 / C-3 PF-01 与降级分开）；design-strategist #29 的 C1/C2/C3 回执与 D4 权威映射表；#30 六维/光照/防泄题锚点。
- **v1.2 并入内容（#45）**：用户 2026-11-12 书面裁决「四套旧门控整体退役」（`p1-legacy-gate-fail-scan.md` §6 乙）；退役的是发布阻断判据地位、不是删断言；81 项逐条迁移到新套件 `PLR-*` 重放（承接表零空白行，见 `design/p1-gate-retirement.md` §3）；门控全绿口径 / G1 / G5 / PF-07 / PF-10 / §7.1 串行顺序同步；**规格定义合计仍 143 条，无一条删除或放宽**。
- **发现的缺陷**：本轮为规格阶段，无产品缺陷可报；已向 #28 / #29 直接索取实跑前置信息（协作规则允许），未越界分派任务。**跨文档口径张力已登记**（§0.6：`p1-gameplay-spec.md` §3.5/§498/§6-6/R3 仍写「终点未拍板」，与主理人裁决 B-8 冲突，已提请 #29 同步，QA 不替其改文件）。
- **待用户/主理人决定**：① G10 L0 退役时点 / 单一 3D 形态收敛 / 保留期（**终点定义已拍板**，此项为达成后的执行裁决）；② G9 上线后观察项（advisory，不阻断，是否补儿童实测由用户决定）；③ C4 SSH 凭据/免密；④ 实跑通知；⑤ 最终放行与发布签字。
- **质量门 advisory**：QA 给判定与阻塞项，**最终放行由用户决定**；CONCERNS / 证据 MISSING 一律不静默放行。

---

*规格 v1.2 · quality-lead 严守真 · 2026-11-10（v1.2 修订 2026-11-12 · #45）· 依据 #31 派单 + 主理人两批补充裁决 + #29 `p1-gameplay-spec.md` + #30 `p1-3d-art-spec.md` + `kart-visibility-diagnosis.md` D1–D6·C1–C6 + `p0-slice-spec.md` 裁决 1–3 + `p0-qa-spec.md` v1.3 + `hud-qa-plan.md` + `stage-delivery` R1–R11 · 五类断言 K1–K5 逐条保留、缺一不可 · 九族 P1 硬判据逐条可验证（新增 PVIS 六维 / PDEG 降级）· C1 键契约 unit 主键 / sym 稳定键 / 零 displayIpa 作键 · C2 逐音素按 CI 单调、禁整类断言 · 失效清单 10 族 + 81 项原样保留逐条枚举 · 规格定义判据 143 条（v1.0 132 + 11 条新增/加严）+ 发布前 C2–C6 5 条 · **2026-11-12 用户裁决乙：四套旧门控整体退役、81 项迁移重放（`PLR-*` 承接表见 `design/p1-gate-retirement.md` §3，零空白行）** · 「门控全绿」= 路线 B 重定义套件 + 81 项迁移重放 + 11 场 headless，≠ 原始 110 项原样全绿 · D6 终点定义「门控全绿 + 375px 可玩」用户已拍板，L0 退役时点待裁决、QA 不替用户决定 · 质量门 advisory，最终放行由用户决定*
