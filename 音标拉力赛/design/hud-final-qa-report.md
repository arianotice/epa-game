# 音标拉力赛 · 2D HUD 最终回归 QA 报告（#5）

> **执行者**：quality-lead（严守真） · **首轮回归**：2026-11-08 · **收口复核**：2026-11-09 · **任务**：`#5` 四套门控全量回归 + HUD 断言 → 收口复核关闭 CONCERNS
> **依据**：`design/hud-qa-plan.md` 六步顺序；`design/hud-ux-spec.md` §5 H1–H12；主理人 `#5` 启动消息的三项裁决（H5 语义口径 / P1 旧 tag 范围 / P2 `minimap_model.test.mjs` 保留现位）；`#5` 收口复核消息（`#18` 重建持久化基线后独立复跑并给最终判定）。
> **独立声明**：首轮与收口复核两批数字均为本机**独立实跑**所得，未复述 engineering-lead 自测（首轮自报 110/110 + 27/27 + 13/13；收口复核自报 110/110 + HUD 12/12 + headless 11 场 + 单测 10/10）。两批证据日志分列于 `qa5/`（首轮）与 `qa5b/`（收口复核）。
> **质量门性质**：advisory。我给判定与阻塞项，**最终放行由用户决定**；发布签字须人工审批。
> **边界遵守（两轮）**：未改任何产品代码（`js/` / `index.html` / `css/` / 图片 / `data.js` / `ipa-display.js`）、未改其他三套门控脚本、未部署、未上线、未 commit。首轮仅按主理人授权修改 `verify_hud_spec.py` 的 H5 检测面并新建本报告；**收口复核为只读复跑，未改任何验收脚本（含 `verify_hud_spec.py`）与产品代码，仅更新本报告**。
> **收口复核触发**：首轮唯一阻塞 C1（TEMP 基线 `c07b-backup-20261106` 被清理导致 F3/F6 FAIL、`c08` D9.2 条件跳过）由 `#18` 按用户拍板「重建证据链并持久化」修复；经本轮独立复跑验证，§6 **C1 已 CLOSED**，质量门改判 **PASS**。

---

## 0. 质量门判定（结论先行）

> # 🟢 PASS

| 维度 | 结果 |
| --- | --- |
| **HUD 功能本体** | ✅ **全绿** —— H1–H12 12/12、独立抽查 7 项、人工清单 8 项、DPR 2/3、8 项资源字节校验、四项错误计数全 0、tag 46 唯一、20 图零裸引用 |
| **四套门控（收口复核独立实跑）** | ✅ **110 / 110 全绿、0 FAIL** —— `cseg_gate` 38 + `cseg_ui` 14 + `fresh_gate` **21（F3/F6 转 PASS）** + `c08_gate` **37（D9.2 实际执行且 PASS）**；四个退出码全 0 |
| **专项** | ✅ `verify_hud_spec.py` 12/12（NOTE 2 条为 H10/H4 既有可解释登记，非阻塞）；`headless_laps.mjs` 11 场 ALL PASS（最慢 174.57 s ≤ 180 s）；`minimap_model.test.mjs` 10/10 |
| **证据链** | ✅ 持久化基线三方 sha256 全等（174527 B）；`.workbuddy/backups/` 不污染 46 处 tag 统计 / 20 图零裸引用 / 运行时资源清单（0 命中） |
| **判定** | **PASS** —— 首轮唯一阻塞 **C1 已 CLOSED**（见 §6）：`#18` 重建持久化基线后，本轮独立复跑逐项满足全部形式判据（≥110 全绿 / `fresh_gate` 21/21 且 F3/F6 PASS / 四项错误计数全 0 / `hud-20261108` 46 唯一 + 20 图零裸引用 / 阻塞性 CONCERNS 归 0） |
| **遗留风险（不阻塞放行）** | 见 §6 R1 / R2：① C07-B 前 / C08 resume 前历史 diff 能力永久丧失，改由「不回退 + sha256 全等」保证；② `hud-20261109` 为 `#4` 之后状态，只能回滚后续改动，回不到 `#4` 之前 |

**放行建议**：全部实质判据与形式判据均已满足，**QA 判 PASS**。质量门为 advisory，最终放行与发布签字仍由用户/主理人决定；建议放行前确认 §6 两条遗留风险可接受，并确认 `.workbuddy/backups/` 作为项目数据保留、不得当缓存清理。

---

## 1. 收口复核独立实跑总表（2026-11-09）

> 本表为**收口复核**本机独立串行实跑结果（四套门控串行 + HUD + headless + 单测），未复述工程侧自测数字。首轮（2026-11-08，CONCERNS 判定）的对应数字见 §1.2 修复前对照。

| 步骤 | 命令 | 退出码 | SUMMARY / 结果 | 判定 |
| --- | --- | --- | --- | --- |
| 1a | `python verify_cseg_gate.py` | `0` | `38 PASS / 0 FAIL / 38 TOTAL`（S17 `{hud-20261108:46}`、S18 零裸引用、A0–A4 headless 11 场 ≤180s） | ✅ PASS |
| 1b | `python verify_cseg_ui.py` | `0` | `14 PASS / 0 FAIL / 14 TOTAL`（U1/U12 四项计数全 0） | ✅ PASS |
| 1c | `python verify_fresh_gate.py` | `0` | `21 PASS / 0 FAIL / 21 TOTAL \| CONCERNS/NOTE: 0`（**F3、F6a、F6b、F6c 全 PASS**） | ✅ PASS |
| 1d | `python verify_c08_gate.py` | `0` | `37 PASS / 0 FAIL / 37 TOTAL`（**D9.2 实际执行且 PASS**） | ✅ PASS |
| 2a | `node js/headless_laps.mjs` | `0` | **11 场 ALL PASS**，最慢 `174.57 s ≤ 180 s` | ✅ PASS |
| 2b | `node js/minimap_model.test.mjs` | `0` | `10 PASS / 0 FAIL / 10 TOTAL`（T0–T7） | ✅ PASS |
| 3 | `python -B verify_hud_spec.py` | `0` | `12 PASS / 0 FAIL / 12 TOTAL`（H1–H12），NOTE 2 条（H10/H4，既有登记） | ✅ PASS |

**收口复核独立实跑合计**：四套门控 **110 / 110 全绿、0 FAIL、四个退出码全 0**（≥110 判据满足）；`verify_hud_spec.py` 12 项；`minimap_model.test.mjs` 10 项 —— **合计 132 项断言全绿 + `headless` 11 场两圈实跑全过**，另加 §1.1 三项静态重点审查与 sha256 三方比对。四项错误计数五处全 0；全日志 **0 条 FAIL 行**；`hud-20261108` 46 处唯一；20 图零裸引用。

**证据日志**（系统临时目录，非产品目录）：`C:/Users/86135/AppData/Local/Temp/qa5b/`
`1a_cseg_gate.log` · `1b_cseg_ui.log` · `1c_fresh_gate.log` · `1d_c08_gate.log` · `3_hud_spec.log` · `2a_headless.log` · `2b_minimap_model.log`

### 1.1 三项重点审查（收口复核点名项）

#### ① `verify_fresh_gate.py` 改动只在基线路由 + F6a —— AST 逐条核对 PASS

以 `#18` 之前的权威改前副本 `.workbuddy/backups/hud-20261109/音标大闯关/verify_fresh_gate.py`（用 `C07B = os.environ["TEMP"]/c07b-backup-20261106`、旧 F6a「与 C07-B 前基线 diff 只落在文案行」）与当前版本做 `diff -u` + `ast` 逐条 `chk(...)` 配对：

- 改前 / 改后**各 22 个 `chk(...)`**（含 `if/else` 两分支，运行时择一，故实际 21 项），**数量一致、无删除、无跳过、无降级为 `note`、无阈值放宽**。
- **仅 2 处差异，均为预期内**：
  - `F6a`：判定式由 `len(dirty)==0 and 100 <= len(diff) <= 250 and len(old_lines)==len(cur_lines)` **收紧**为 `len(diff)==0 and len(dirty)==0 and len(old_lines)==len(cur_lines) and sha_equal`（新增 `hashlib.sha256` 全等锁），名称相应改为「与持久化已验收基线逐字一致（不回退）」；
  - `else` 分支文案：`F6 基线缺失（c07b-backup-20261106）` → `F6 持久化基线缺失（.workbuddy/backups/c07b-data-baseline.js）`，**判定值仍为 `False`（基线再缺失仍判 FAIL，不静默放行）**。
- **`F3` 判定式逐字一致**（`len(f3_slash_e)==0 and eɪ_now>0 and eɪ_now==eɪ_old`）；`F1/F1b/F2/F4/F5/F6b/F6c/F7/F8a/F8b/F9a/F9b/F9c/F10a/F10b/F11a/F11b/F11c/F11d` 名称与判定式**全部逐字未动**。
- 其余改动仅为 docstring 说明、`C07B`→`BASELINE` 常量路由（指向项目内 `.workbuddy/backups/c07b-data-baseline.js`）、`base_data = BASELINE` 一处赋值；全仓**无运行时 `TEMP` 依赖**（0 处）。
- 实跑佐证：`F3 | {'/e/ 命中': 0, 'eɪ 当前': 5, 'eɪ 基线': 5}`；`F6a | {'基线行数': 7684, '当前行数': 7684, 'diff 行数': 0, '逻辑键改动': [], 'sha256 全等': True, 'sha256_16': '25784ee12bd0f637'}`。

#### ② `verify_c08_gate.py` D9.2 真执行且 PASS —— 实跑证据

`diff -u` 确认 `c08_gate` 改前→改后**仅 1 处**：`bak_data` 路径常量由 `TEMP/c08_resume_backup_20261107/音标大闯关__js__data.js` 改为项目内 `.workbuddy/backups/c07b-data-baseline.js`，**D9.1/D9.2/D9.3 断言代码逐字未动**。首轮因该 TEMP 基线不存在，`D9.2` 被 `if os.path.exists(bak_data)` 条件跳过（36 vs 37）；本轮基线存在，日志实证：

```
=== D9 补表 G（条件执行）===
  PASS  D9.1 可见文案 C 类残留命中 0
  PASS  D9.2 真双元音滑动描述逐字未动        ← 实际执行且 PASS
  PASS  D9.3 两题 options 长度/顺序/answer 不变
SUMMARY: 37 PASS / 0 FAIL / 37 TOTAL            ← 回到 37 项基线
```

#### ③ `.workbuddy/backups/` 不污染 46 处 tag 扫描 / 20 图零裸引用 —— 静态 + 实跑双证

- **扫描根**：五套脚本的 `?v=` / 图片 URL 扫描均为 `for base in (QUEST, RALLY)` 下的 `os.walk`，`QUEST = ROOT/音标大闯关`、`RALLY = ROOT/音标拉力赛`；`.workbuddy` 位于 `ROOT` 下、与两站**平级**，两处 `os.walk` 均不进入 → 天然隔离。五套脚本中 `.workbuddy` 字面仅出现在 `fresh_gate` / `c08_gate` 的**基线路径常量**（非扫描根），运行时 `os.environ["TEMP"]` 依赖 **0 处**。
- **基线文件本身**：`c07b-data-baseline.js` 内 `?v=` 出现 **0 次**，不可能贡献 tag 计数；含 30 处 `.webp/.png` 文件名字符串，但因不在扫描根内，**不参与 S18 裸引用判定**，也未被误当产品资源。
- **按脚本原逻辑独立复现**：`S17` tag 直方图 `{'hud-20261108': 46}`（唯一且 46 = True）；`S18` 裸引用命中 **0**。
- **实跑三方一致**：`cseg_gate` S17 `{'hud-20261108': 46}` / S18 PASS；`fresh_gate` F8a `{'hud-20261108': 46}`；`hud_spec` H11 `{'hud-20261108': 46}` + `图片 URL 字面量 20 / 裸引用 [] / 裸 src/import []` + `CACHE_TAG 同步 True`。
- **运行时清单**：`qa5b/` 全部日志检索 `.workbuddy` / `c07b-data-baseline` / `hud-20261109` **0 命中**（`fresh_gate` 资源总数 19 / 带 tag 18、`F11c` 14/13、`H11` 带 tag 请求 12 中均无备份文件）；全日志 **0 条 FAIL 行**。

#### ④ 持久化基线三方 sha256 全等

| 对象 | sha256 | 字节 |
| --- | --- | --- |
| `baseline-meta.json` 声明 | `25784ee12bd0f637794f46e37acad604155cb946902e115858f1a69663892d1f` | 174527 |
| `.workbuddy/backups/c07b-data-baseline.js` 实测 | 同上（全等） | 174527 |
| `音标大闯关/js/data.js` 实测 | 同上（全等） | 174527 |

`meta == baseline == data.js == True`；`baseline == data.js` 逐字节相等。这正是 F6a 收紧后 `diff 行数=0` 且 `sha_equal=True` 的根据，也说明**当前 `data.js` 处于已验收态、无回退**。

### 1.2 修复前对照（首轮 #5 回归，2026-11-08，判 CONCERNS）

| 步骤 | 首轮结果 | 收口复核结果 |
| --- | --- | --- |
| 1c `fresh_gate` | `17 PASS / 2 FAIL / 19 TOTAL`，exit **1**（F3 `eɪ 基线=-1`、F6「基线缺失」） | `21 / 0 / 21`，exit 0（F3/F6 全 PASS） |
| 1d `c08_gate` | `36 / 0 / 36`（D9.2 条件跳过） | `37 / 0 / 37`（D9.2 执行且 PASS） |
| 四套合计 | **107 执行 / 105 PASS / 2 FAIL** | **110 / 110 / 0** |
| 质量门 | 🟡 CONCERNS（C1 证据 MISSING） | 🟢 PASS（C1 CLOSED） |

根因与独立佐证（首轮）：TEMP 基线 `c07b-backup-20261106` 与 `c08_resume_backup_20261107` 被系统清理；`data.js` mtime `2026-11-07 08:42:49` 早于 `#4`（`2026-11-08`），证明与 HUD 无关。首轮证据日志：`C:/Users/86135/AppData/Local/Temp/qa5/`。

---

## 2. H1–H12 逐项判定（`verify_hud_spec.py`，两轮均 12/12 PASS）

> 表内数字取自首轮详单；收口复核以同一脚本复跑 12/12 一致，本轮逐项明细见 `qa5b/3_hud_spec.log`（`simTime` 等运行时期望值的微小差异属 `step()` 推进波动，均在断言容差内）。

| # | 断言 | 结果 | 关键实测证据 |
| --- | --- | --- | --- |
| H1 | DOM 存在性与属性 | ✅ PASS | `#minimap` / `#minimap-c` / `#minimap-lap` 齐备；`aria-hidden=true`、`pointerEvents=none`、`zIndex=5`、`position=fixed`、底板 `rgba(255,250,240,0.94)`（alpha .94 ≥ .82） |
| H2 | 显隐矩阵（9 阶段） | ✅ PASS | `title/teach/results → hidden=true`；`countdown/racing/paused/quiz → false`；**`boardOpen` 与 `shopOpen` 时 `mode` 仍 `racing` 但 `hidden=true`**；quiz 冻结前后数值相等 |
| H3 | 375px 不溢出（三视口） | ✅ PASS | 375×667 `96×63.75`（≤112.5）；320×568 `83.19×54.39`；PC `160×104`；三者 `left≥0 / right≤W / top≥0 / bottom<H` |
| H4 | 位置不重叠 + 层叠 | ✅ PASS | 三视口 `重叠项=[]`；窄屏 banner 间距 `12.0px`；`hud padding-right` PC `184px` / 触屏 `120px`；quiz 层叠 `z=8 > mm z=5` |
| H5 | **小地图不含答案文本** | ✅ PASS | 见 §3（主理人裁决口径落地） |
| H6 | `minimapModel` 字段白名单 | ✅ PASS | 入口 `__rally.minimapModel()`；递归键总数 **1085**，禁用键 `[]`；`nextGate` 恰 5 键 `{id,lap,line,distance,secondsTo}` |
| H7 | 路牌 `D_preview` 阈值 | ✅ PASS | follow 1482 / listen 1620 里程；两档 S0 隐藏 → S1 显示 → S2 显示；两牌恒 2 块；名义速度常量 |
| H8 | S1 零文本 / S2 对称 | ✅ PASS | S1 文本 `['◇','◇']`，无 `is-long/is-short`；S2 双侧同宽同不透明度、含各自 word 与 `/ipa/` 且互异、无单侧高亮 |
| H9 | quiz 冻结 | ✅ PASS | `simTime` / `odo` 在 `step(60)` 前后逐值不变；`#signs.hidden=true`；`setItem 增量 0`；回 racing 路牌文本无缝复原 |
| H10 | 两圈同 `commitT` 不重复 | ✅ PASS | `lineT=[0.24,0.68,1.24,1.68]`（容差 1e-9）；两圈 `line 差 = 19254.5 = L`；`state.lap=1`；`nextGate.lap=1`；`.sign` 块数 2；第 2 圈正常出牌 |
| H11 | 缓存串 + 资源送达 | ✅ PASS | tag 直方图 `{'hud-20261108':46}`；`CACHE_TAG` 同步；20 个图片 URL 零裸引用、零裸 `src/import`；`IPA_DISPLAY.U11=ɜr`；按字节比对全等 |
| H12 | 零回归 + 零写盘 | ✅ PASS | 四项错误计数全 0；`frozen step(300)` 的 `setItem 增量 0`；`rally.unlocked/maps/EP02` 开赛前后逐字段相等 |

**2 条 NOTE（均不影响判定，已登记）**：
1. `H10 signKey 不可观测` —— `#sign-l/#sign-r` 的 `data-opened` 为空（`#4` 改了键载体，`__rally.signKey` / `signPhase` 已暴露）；已改以行为断言为主（`lineT` / `line 差` / `lap` / 块数 / 第 2 圈出牌）。
2. `H4 #quiz 口径` —— 按规格 §2.1.4/§2.1.6，quiz 时小地图显示但冻结，由 `.panel(z=8)` 覆盖 `#minimap(z=5)`，属 z-index 层叠而非几何不相交；故断言层叠顺序 + `pointer-events:none`，不做矩形不相交断言。

---

## 3. H5 主理人裁决落地（假阳性修正）

**裁决**：检测面 = 用户可见文本与可访问性属性，**不含 `mm.innerHTML` 源码字面量**；词表 = `allWords()` **83 词全表** + `correctLateral/spoken/left/right` 四字段名，零命中断言；**不得缩小词表、不得只查部分词、不得降级为 warn**；Q1 DOM 契约（含 `<span id="minimap-lap">`）不动。

**脚本改动**（仅 `verify_hud_spec.py`，977 行，AST 自检通过；**收口复核未再改动此脚本**）：
- 检测面改为 `mm.textContent + 遍历后代所有属性值`（`attrs` 全量 `[name, value]` 的值），`mm.innerHTML` **仅作诊断证据、不计判定**。
- 词表改为浏览器内 `await import('/音标拉力赛/js/config.js?v=hud-20261108')` → `cfg.allWords()`（产品本体，83 词，不缩小、不过滤短词），叠加 4 字段名与 4 门 IPA/displayIpa，共 **91 个 token**。
- **防放宽铁律落地**：把「`len(vocab)==83` 且 `len(set(vocab))==83`」本身写成 `vocab_ok` 硬判据；仍是 `chk()` 硬断言（非 warn）；字段名 4 个一个不少。

**实跑结果（两轮均 PASS）**：

```
检测面字符数 53 | 词表 83（恰为 83 且不重复: True）| token 总数 91 | 门数 4
命中答案词面/字段名/IPA: []   命中中文答案域关键字: []   禁用属性名: []
mm.textContent: '\n  \n  1/2\n'
检测面属性值: [['id','minimap'],['aria-hidden','true'],['id','minimap-c'],
              ['width','156'],['height','100'],['id','minimap-lap']]
innerHTML 假阳性命中(证据): ['pan']     ← 精确复现工程侧报告的 `<span` 撞 pen/pan
```

**结论**：`<span id="minimap-lap">` 标签名中的 "span" 含 `pan`（pen/pan 词对，83 词全表内），确系**测试脚本假阳性**；新检测面下 83 词全表零命中。**产品零缺陷，DOM 契约未改，断言未放宽。**

---

## 4. 独立抽查（首轮，不复述工程侧自测，直接读实现状态）

> 抽查脚本**不 import 验收脚本、不复用 `window.__qa` 夹具**，直接消费 `window.__rally` 与原生 DOM，主理人点名的 3 处全部覆盖。本节为**首轮 #5 回归**证据；收口复核为只读复跑，未重复人工抽查（范围见 §8），结论未被推翻。

| # | 抽查点 | 实测 | 判定 |
| --- | --- | --- | --- |
| 1 | **quiz 冻结**：`mm.hidden===false` 且 `karts[0].odo`/`simTime` 不变 | 冻结前 `{odo:690.5800685732153, sim:4.901303999999207, mode:'quiz', mmHidden:false, signsHidden:true}`；`step(60)` 后**逐值完全相等**，`mmHidden` 仍 false | ✅ PASS |
| 2 | **S1 零文本** | 干净 racing 态、`activeGate()`、`dist=1452.1` → `phase='S1'`；两牌文本 `◇`/`◇`（无字母无斜杠）；class `sign on-lane forecast`；块数 2；无 `is-long/is-short` | ✅ PASS |
| 3 | **boardOpen**：mode 仍 racing 但小地图隐藏 | 真实点击 `#btn-board` → `{mode:'racing', boardOpen:true, shopOpen:false, mmHidden:true}` | ✅ PASS |
| 4 | 375×780 几何 | `rect 269,8→365,71.75`（96×63.75）、`overlaps=[]`、`pe=none`、`z=5`、`hudPad=120px`、banner 间距 **12px** | ✅ PASS |
| 5 | 320×568 几何 | `rect 226.81,8→310,62.39`（83.19×54.39）、`overlaps=[]`、banner 间距 **12px** | ✅ PASS |
| 6 | DPR 2 | `css 92×59.75 → bmp 184×120`（×2）、`matrix(2,0,0,2,0,0)`、非空像素 2192 | ✅ PASS |
| 7 | DPR 3 | `css 92×59.75 → bmp 184×120`（**clamp 到 2**，符合 `dpr=min(2,devicePixelRatio)`）、非空像素 2192 | ✅ PASS |

**过程记录（透明披露，不计为缺陷）**：首轮独立抽查 v1 曾报 4 项 FAIL，逐一查证为**抽查脚本自身前置错误** —— ① S1/boardOpen 沿用 quiz 未复原的页面（`mode` 仍 quiz、`decide` 未清）；② 两视口的 `#banner` 未 `unhide`，`getBoundingClientRect()` 全 0 导致间距为负。与 H5 假阳性同类，属测试脚本 bug。修正前置（每场景新开干净 page、清 `quiz/decide`、`unhide banner`）后 v2 全绿（4/4），叠加 quiz 冻结与 DPR 2/3 共 **7 项独立复核全绿**。

**HUD 内部 chip 精确测量（澄清 375×780 截图里的淡字疑点）**：375×780 与 320×568 下，`#hud .hud-row > *` 全部 10 个 chip 的**彼此重叠对 = []、文字裁切（`scrollWidth>clientWidth`）= []、与小地图相交 = []**；`hud clientWidth` 375/320。截图中的淡字是半透明 UI 元素（`#combo` 占位圆点 / `#gems`），非遮挡、非截断，符合规格 R2「`.hud-row` 多换 1 行可接受」。

---

## 5. 人工清单 V1–V17 / DPR / 资源校验结果

> **证据归属说明**：本节 V1–V17、DPR 2/3 截图、8 项资源按字节校验均为**首轮 #5 回归（2026-11-08）**独立实跑证据；收口复核（2026-11-09）任务范围为四套门控 + `verify_hud_spec.py` + headless + 单测 + 三项重点审查，**未重复人工过眼与截图**（只读复跑边界，见 §8）。本轮 `verify_hud_spec.py` 的 H11 覆盖了其中「资源按字节送达」子集（`index.html` 7839 B / `main.js` 53361 B / `ipa-display.js` 3822 B 三项全等），H12 覆盖四项错误计数；§5.3 的 8 项资源与 §5.2 的 DPR 结论沿用首轮、未被本轮改动推翻。两轮之间产品与验收脚本仅发生 `#18` 的基线路由改动，不影响这些断言。

### 5.1 人工清单（自动化可判定项 + 截图过眼）

| # | 项 | 结果 | 证据 |
| --- | --- | --- | --- |
| V1 | 右上角位置与完整度 | ✅ PASS | 375×780 `right:10 / top:8`，96×63.75，四角无裁切；DPR2/3 截图目视完整 |
| V2 | 半透明底板与可读性 | ✅ PASS | `rgba(255,250,240,.94)` + 2px 描边 + shadow；截图环线/车点/`1/2` 清晰 |
| V3 | 与 HUD 不重叠 | ✅ PASS | `overlaps=[]`；chip 彼此重叠 `[]`；`hud padding-right=120px` 生效 |
| V4 | `#banner` 下移 | ✅ PASS | 375×780 与 320×568 间距均 **12px**（`banner.top = mm.bottom + 12`） |
| V5 | `#route-map` 互斥 | ✅ PASS | title：`routeHidden=false, mmHidden=true`；racing：`routeHidden=true, mmHidden=false`；无三元素叠压，未删未移 |
| V6 | `pointer-events:none` 穿透 | ✅ PASS | `elementFromPoint(mm 中心)` → `hud`，`insideMinimap=false`（不吃暂停/静音触屏事件） |
| V7 | 状态机显隐（countdown/racing/paused/quiz/title/teach/results） | ✅ PASS | H2 九阶段矩阵全绿 |
| V8 | quiz 冻结口径 | ✅ PASS | H9 + 独立抽查 1（小地图显示但冻结、路牌隐藏、答题后无缝复原） |
| V9 | board / shop 打开 | ✅ PASS | H2 + 独立抽查 3（`mode` 不变但显式隐藏） |
| V10 | 路牌 S1 / S2 | ✅ PASS | H7/H8 + 独立抽查 2（S1 `◇◇` 中性、S2 对称无指向性） |
| V11 | 两圈切换 | ✅ PASS | H10（`line 差 = L`、`lap=1`、`nextGate.lap=1`） |
| V12 | 答案不泄露（目视） | ✅ PASS | H5（83 词零命中）/ H6（1085 键零禁用键）+ 截图目视无单词/IPA |
| V13 | 触摸操作区 | ✅ PASS | `#touch` 矩形 `0,670→375,780`，与小地图 `269,8→365,71.75` 不相交 |
| V14 | 结果页 / 暂停页显隐 | ✅ PASS | H2 `results → hidden=true`、`paused → false`（冻结保持） |
| V15 | `prefers-reduced-motion` | ✅ PASS | `mq=true`、`mmAnim=none`、两牌 `signAnims=['none','none']` |
| V16 | 375×320 横屏短高 / 320×568 | ✅ PASS | 375×320 `mm.bottom=71.75 < 320` 不溢出；320×568 见 §4 |
| V17 | 视觉一致性 | ✅ PASS | `--paper #f6ead0` / `--ink #4a3520` / `--gold #c9a227` / `--card rgba(255,250,240,.94)`；DPR2/3 截图配色一致 |

**截图留证**：`qa5/dpr2_375x780.png`、`dpr3_375x780.png`、`375x780.png`、`320x568.png`。DPR2 与 DPR3 视觉一致（DPR3 按规格 clamp 到 2），环线无锯齿、圈数 `1/2` 可辨、底板与赛道对比充分。

### 5.2 DPR 2 / 3 复核

| DPR | CSS 尺寸 | 位图尺寸 | `getTransform()` | 非空像素 | 判定 |
| --- | --- | --- | --- | --- | --- |
| 2 | 92×59.75 | 184×120 | `matrix(2,0,0,2,0,0)` | 2192 | ✅ PASS |
| 3 | 92×59.75 | **184×120** | `matrix(2,0,0,2,0,0)` | 2192 | ✅ PASS（clamp 到 2，符合 `min(2,dpr)`） |

布局不随 DPR 漂移（CSS rect 不变），无重复绘制 / resize 抖动。

### 5.3 8 项资源按字节 / magic / sha256 校验（防 Caddy 兜底 200）

| # | 资源 | 字节 | `byteEqual` | sha256[:16] | magic | Content-Type |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 拉力赛 `index.html` | 7839 | ✅ | `c5bc92ab614336f4` | — | `text/html` |
| 2 | 拉力赛 `css/game.css` | 17466 | ✅ | `2d1b8c453c002f75` | — | `text/css` |
| 3 | 拉力赛 `js/main.js` | 53361 | ✅ | `2db27bd0c1010faf` | — | `text/javascript` |
| 4 | 拉力赛 `js/render.js` | 20357 | ✅ | `7b65bafa994de5cc` | — | `text/javascript` |
| 5 | 拉力赛 `js/config.js` | 12076 | ✅ | `0dfe653c7552aab3` | — | `text/javascript` |
| 6 | 大闯关 `js/ipa-display.js` | 3822 | ✅ | `0ce76227903f0fd5` | — | `text/javascript` |
| 7 | 大闯关 `assets/img/a1.webp` | 355002 | ✅ | `25532a2616ef1a87` | `RIFF....WEBP` ✅ | `image/webp` |
| 8 | 大闯关 `assets/sprites/U01.webp` | 64670 | ✅ | `c27427191d2c709b` | `RIFF....WEBP` ✅ | `image/webp` |

**8/8 PASS**。兜底 200 陷阱探测：请求确定不存在的 `assets/img/__qa_missing_9f3a.webp?v=hud-20261108` → 本地 server 正确返回 **404**，无兜底；即便线上有兜底，本校验按**逐字节 + magic + sha256 + Content-Type 非 text/html** 四重判定，状态码不参与结论，防陷阱口径有效。收口复核本轮 `H11` 按字节送达子集（1/3/6 三项）复验全等。

### 5.4 四项错误计数（严格区分 `ERR_ABORTED`，收口复核本轮全 0）

| 脚本 | pageerror | console_error | requestfailed | bad_status | ERR_ABORTED 单列 | 真实失败 |
| --- | --- | --- | --- | --- | --- | --- |
| `verify_cseg_ui.py` U1/U12 | 0 | 0 | 0 | 0 | 0 | 0 |
| `verify_fresh_gate.py` F11d | 0 | 0 | 0 | 0 | 0（原因分布 `{}`） | 0 |
| `verify_c08_gate.py` D7.5 | 0 | 0 | 0 | 0 | 0（原因分布 `{}`） | 0 |
| `verify_hud_spec.py` H12 | 0 | 0 | 0 | 0 | **总计 0 / 主动取消 0 / 同源真实失败 0 / 外链环境失败 0** | 0 |
| `verify_cseg_gate.py` | — | — | — | — | 纯静态门控，无浏览器 | — |

**全 0，PASS**。HUD 脚本按主理人要求单列披露 `ERR_ABORTED`（本轮恰为 0），未把主动取消混入 FAIL，也未静默吞掉。收口复核 `qa5b/` 全日志 **0 条 FAIL 行**。

### 5.5 缓存串 / 图片 URL / 旧 tag 范围（P1）/ 测试资产（P2）

| 项 | 结果 |
| --- | --- |
| `?v=` 直方图 | `{'hud-20261108': 46}` —— 唯一值、恰好 46 处（9 个文件分布不变）；收口复核三处实跑（S17/F8a/H11）+ 独立复现一致 |
| `config.js CACHE_TAG` | `hud-20261108`，与 46 处字面量一致；`headless_laps.mjs:19` 与四套脚本 `TAG` 常量均同步 |
| 20 个图片 URL | 独立复核 **20 个字面量 / 0 裸引用**；动态拼接型 2 处段内亦带 tag |
| **P1** 产品/脚本旧 tag | 扫描 29 个产品 + 验收脚本文件，**0 命中 → PASS** |
| **P1b** design/docs 旧 tag | 6 文件 25 次，`hud-impl-plan.md`(8)、`hud-impl-report.md`(8)、`hud-qa-plan.md`(4)、`hud-ux-spec.md`(2)、`visual-direction-3d.md`(1)、`音标大闯关/docs/c-segment-acceptance.md`(2) —— **均为历史叙述文档，按裁决不算残留**，此处逐项列出备查 |
| **P2** `js/minimap_model.test.mjs` | 保留现位（8247 B）；全仓 `<script src>` / ESM import / 发布清单 **零引用**；页面 `performance.getEntriesByType('resource')` 共 96 条，**测试文件请求 `[]`** → 未带入运行时；`.mjs` 不进 tag 扫描。✅ PASS |

---

## 6. CONCERNS 清单与缓解（收口复核后）

> **状态总览**：首轮共 10 项 CONCERNS（C1–C10）。收口复核后，**唯一阻塞 C1 已 CLOSED**、C2/C4/C5 随 `#18` 消除、C3/C6/C7/C8/C9/C10 维持原性质（均为非阻塞、已解释或属流程/发布后事项）。**阻塞性 CONCERNS 归 0，质量门判 PASS**。下表保留全部条目以便追溯，新增两条**必须保留的遗留风险 R1 / R2**。

| # | CONCERNS | 性质 | 收口复核后状态 | 缓解 / 处置 |
| --- | --- | --- | --- | --- |
| **C1** | ~~`verify_fresh_gate.py` F3/F6 两项 FAIL（退出码 1）、TEMP 基线目录被清理~~ | 测试环境基线缺失，非产品缺陷 | ✅ **CLOSED**（唯一阻塞已消除） | 见下方「C1 关闭依据」：`#18` 按用户拍板重建项目内持久化基线，本轮独立复跑 `fresh_gate` 21/21 且 F3/F6 全 PASS、`c08` D9.2 执行且 PASS、四套 110/110。 |
| **C2** | ~~回滚点 `Temp/hud_backup_20261108/` 不存在~~ | 环境（TEMP 清理） | ✅ **已缓解**（附 **R2** 限制） | `#18` 已在 `.workbuddy/backups/hud-20261109/` 落盘 13 产品文件 + `manifest.txt`（232451 B，`SOURCE_FILES_UNMODIFIED=YES`），作为**持久化回滚点**。但 manifest 头部如实声明该快照是 `#4` **之后**状态，见 R2。 |
| **C3** | `verify_hud_spec.py` 两条 NOTE | 可解释，不影响判定 | 维持（非阻塞） | ① H10 `signKey` 不可观测：以行为断言为主；② H4 `#quiz` 层叠口径：不做几何不相交断言。§2 已登记，本轮 12/12 复跑 NOTE 仍为同样 2 条。 |
| **C4** | ~~门控 TOTAL 与基线不一致：`fresh 19 vs 21`、`c08 36 vs 37`（合计 107 vs 110）~~ | 条件分支跳过 | ✅ **CLOSED** | 基线恢复后 `fresh_gate` 回到 21（F6a/F6b/F6c 进入 `if` 分支）、`c08_gate` 回到 37（D9.2 实际执行），合计 **110/110**，与基线完全一致。 |
| **C5** | 工程侧自测口径与 QA 独立实跑口径差异 | 口径差异 | 维持（无产品影响） | 两轮 QA 均**独立实跑、未复述自测数字**：首轮 107 执行 / 105 PASS / 2 FAIL；收口复核 110/110。建议以本报告两批实跑日志（`qa5/` / `qa5b/`）为准。 |
| **C6** | 工程侧提示 `F10a` 偶发 `ERR_CONNECTION_REFUSED` | 未复现 | 维持（非阻塞） | 首轮两跑、收口复核一跑，F10a 均 PASS（`stale_hits=0, pageerror=0, console_error=0`）。按既有 `ERR_ABORTED` 明细区分口径处理，**未放宽任何断言**；本轮未复现。 |
| **C7** | 独立抽查 v1 的 4 项假阳性 | 抽查脚本前置错误 | 维持（非阻塞） | 已定位（quiz 态未复原 / banner 未 unhide），v2 修正前置后 4/4 全绿，过程透明登记。 |
| **C8** | Q4 遗留项 `placeLaneSign` 的 `t`/`odo` 差 `0.02·L`（≈385 里程） | 已登记遗留项 | 维持（本轮不修） | 按 §7 Q4 锁定「本轮不改」；若后续决定修，QA 需补一条路牌投影位置回归断言。 |
| **C9** | 线上 Caddy 兜底 200 陷阱 | 本轮不部署，发布后风险 | 维持（当前无影响） | 发布后须按 §5.3 口径（逐字节 + magic + sha256 + Content-Type 非 `text/html`）复核，先探不存在路径确认是否有兜底，**不信状态码**。 |
| **C10** | 质量门为 advisory | 流程 | 维持 | QA 给 PASS 判定，**最终放行由用户决定**；发布签字须人工审批。 |

### C1 关闭依据（用户拍板「重建证据链并持久化」→ `#18` 落地 → QA 独立复跑验证）

1. **证据链重建**：`.workbuddy/backups/` 落盘 `c07b-data-baseline.js`（174527 B，当前已验收 `data.js` 的逐字节副本）、`baseline-meta.json`（sha256 全值 + `semantics_change` 说明）、`hud-20261109/`（13 产品文件 + `manifest.txt`，232451 B）。
2. **断言强度不降**：`verify_fresh_gate.py` 仅改基线路由（`C07B`→项目内 `BASELINE`）与 F6a（**收紧**为 `diff==0 and dirty==0 and 行数相等 and sha256 全等`），F3 判定式逐字未动、其余 19 项 `chk` 逐字未动、`else` 分支基线缺失仍判 FAIL；`verify_c08_gate.py` 仅改 `bak_data` 路径常量、D9.2 断言代码逐字未动。**QA 未改任何验收脚本，未放宽任何断言**（§1.1 ① 逐条核对）。
3. **实跑验证**：收口复核四套门控 **110/110 全绿**，`fresh_gate` **21/21 且 F3/F6 PASS**（`sha256 全等 True`、`diff 行数 0`）、`CONCERNS/NOTE: 0`，`c08_gate` **37/37 且 D9.2 执行且 PASS**，`verify_hud_spec.py` 12/12，四项错误计数全 0，`hud-20261108` 46 唯一，20 图零裸引用，`.workbuddy/backups/` 未污染任何统计/运行时清单（§1.1 ②③④）。
4. **判定**：首轮 C1 的「2 项证据 MISSING」已由持久化基线 + 不回退 + sha256 全等重新覆盖，形式判据全部满足 → **C1 CLOSED，质量门 PASS**。

### 必须保留的遗留风险（不阻塞本轮放行，但须登记）

| # | 风险 | 影响 | 约束 |
| --- | --- | --- | --- |
| **R1** | **C07-B 前 / C08 resume 前的历史 diff 能力已永久丧失** | 原 TEMP 基线 `c07b-backup-20261106`（C07-B 改动前 `data.js`）与 `c08_resume_backup_20261107`（C08 resume 前）随系统 Temp 清理**不可恢复**，`hud_backup_20261108`（`#4` 前快照）同样丢失。F6a / D9.2 不再能与「改动前历史态」做逐字 diff | 现改由 **「不回退 + sha256 全等」** 保证：持久化基线 = 当前已验收态逐字节副本；`F6a` 断言 `diff==0 + sha_equal`、`D9.2` 断言真双元音行逐字未动；`baseline-meta.json` 的 `semantics_change` 已如实登记。**断言强度不降，但「相对历史态的 diff」不再可得**；后续若需审计历史文案变更，只能依赖 `data.js.bak` / `content_raw.json` 等次级证据 |
| **R2** | **`hud-20261109` 是 `#4` 之后状态，只能回滚后续改动** | `manifest.txt` 头部如实声明：该快照是 `#4` 改动**之后**的已验收状态，**不是 `#4` 之前**；原 `#4` 前快照 `Temp/hud_backup_20261108/` 已永久丢失 | 该回滚点**仅能**用于回滚 `#4` 之后发生的后续改动，**回不到 `#4` 之前**。任何「撤销本轮 2D HUD」的诉求不可通过此快照实现，须另行走代码级回退 |

### 项目数据声明（须随本报告一并遵守）

- **`.workbuddy/backups/` 属项目数据，不是临时缓存，不得当缓存清理**。本轮复现的 46 处 tag 扫描 / 20 图零裸引用断言均以 `QUEST` / `RALLY` 为扫描根，该目录在 `ROOT` 下与两站平级、天然不被纳入；删除它不会改变任何断言结果，但会**直接摧毁 F3/F6a/F6b/D9.2 的证据链**（回到首轮 C1 的 MISSING 状态）。
- **`data.js` 后续若发生任何变更，必须同步更新 `.workbuddy/backups/c07b-data-baseline.js` 与 `baseline-meta.json` 的 sha256/bytes**，否则 `F6a` 的 `diff==0 + sha_equal` 会立即判 FAIL（这是**预期的防回退 / 防漂移行为**，不是误报）。变更须经用户/主理人批准，并由 QA 重新复跑四套门控确认。

---

## 7. 判定记录表（收口复核实跑填写，2026-11-09）

| 项 | 结果 | SUMMARY / 证据 |
| --- | --- | --- |
| P0–P5 前置（`#4` 落地 / tag bump / 脚本 TAG 同步 / 系统 Chrome / 环境 / 干净工作区） | ✅ 通过 | `hud-20261108` 46 处唯一；`CACHE_TAG` 与四套脚本 `TAG` + `headless_laps.mjs:19` 全同步；Chrome `executable_path` 全链可用（`CHROME_OK`）；Python 3.13.14 / Node v22.22.2 |
| 步骤 1a `verify_cseg_gate.py` | ✅ PASS | `38 / 0 / 38`，exit 0（S17 `{hud-20261108:46}`、S18 零裸引用、A0–A4 headless 11 场 ≤180s） |
| 步骤 1b `verify_cseg_ui.py` | ✅ PASS | `14 / 0 / 14`，exit 0（U1/U12 四项计数全 0） |
| 步骤 1c `verify_fresh_gate.py` | ✅ PASS | `21 / 0 / 21`，exit 0，**F3/F6a/F6b/F6c 全 PASS**，`CONCERNS/NOTE: 0` |
| 步骤 1d `verify_c08_gate.py` | ✅ PASS | `37 / 0 / 37`，exit 0，**D9.2 实际执行且 PASS** |
| 步骤 2a `headless_laps.mjs` | ✅ PASS | 11 场 ALL PASS，最慢 `174.57 s ≤ 180 s` |
| 步骤 2b `minimap_model.test.mjs` | ✅ PASS | `10 / 0 / 10`（T0–T7） |
| 步骤 3 `verify_hud_spec.py` | ✅ PASS | `12 / 0 / 12`，NOTE 2（H10/H4，首轮既有登记） |
| §1.1① `fresh_gate` 改动只在基线路由 + F6a | ✅ PASS | AST 逐条配对 22/22 `chk`，仅 2 处预期差异（F6a 收紧 / else 文案），F3 及 19 项判定式逐字未动 |
| §1.1② `c08` D9.2 真执行 | ✅ PASS | 日志 `PASS  D9.2 真双元音滑动描述逐字未动`，TOTAL 回到 37 |
| §1.1③ 备份目录不污染扫描 | ✅ PASS | 扫描根 `(QUEST,RALLY)`；复现 S17 `{hud-20261108:46}` / S18 `0`；全日志 `.workbuddy` 0 命中 |
| §1.1④ 三方 sha256 全等 | ✅ PASS | meta = baseline = data.js = `25784ee…`，174527 B |
| 四项错误计数 | ✅ 归零 | `cseg_ui` / `fresh_gate` F11d / `c08` D7.5 / `hud_spec` H12 全 `0/0/0/0`；ERR_ABORTED 单列 0；全日志 0 条 FAIL 行 |
| tag / 图片 URL / P1 / P2 | ✅ 通过 | 46 唯一（三处实跑一致）/ 20 零裸引用 / 产品脚本旧 tag 0 命中 / 测试资产未入运行时 |
| 资源按字节校验 | ✅ 通过 | 首轮 §5.3 8/8；本轮 H11 三项按字节送达全等（子集复核） |
| 独立抽查 / 人工清单 / DPR | ✅ 通过（首轮证据） | 首轮 §4 抽查 7 项 + §5.1 V1–V17 + §5.2 DPR2/3；本轮未重复人工过眼（只读复跑边界），未被推翻 |
| **质量门判定** | 🟢 **PASS** | 四套 110/110 全绿、C1 CLOSED、阻塞性 CONCERNS 归 0、四项错误计数全 0；遗留 R1/R2 不阻塞 |

---

## 8. 边界与 Handoff

**首轮（2026-11-08）**
- 未改产品代码：`js/` / `index.html` / `css/` / 图片 / `data.js` / `ipa-display.js` / 上游管线一律未动；四套既有门控脚本一个字未改（`verify_fresh_gate.py` 的 FAIL 仅如实上报，未做任何修补）。
- 唯一脚本改动：`verify_hud_spec.py` 的 H5 检测面（主理人 `#5` 消息明确授权「按上述 H5 口径修正后跑」），改后 977 行、AST 自检通过、H1–H12 覆盖不变。
- 未部署、未上线、未 commit。

**收口复核（2026-11-09）**
- **只读复跑**：未改产品代码、未改任何验收脚本（含 `verify_hud_spec.py`）、未部署 / 未上线 / 未 commit；仅**更新本报告**（`design/hud-final-qa-report.md`）。
- 实跑范围：四套门控串行 + `verify_hud_spec.py` + `node js/headless_laps.mjs` + `node js/minimap_model.test.mjs`，另加三项重点静态审查与 sha256 三方比对；证据落 `qa5b/`。
- 未发现产品缺陷，无需回派 engineering-lead。
- 所有产出经主理人中转；QA 未与其他成员直接通信。
- **待用户/主理人决定**：最终放行与发布签字（质量门 advisory）；放行前请确认 §6 R1 / R2 可接受，并确认 `.workbuddy/backups/` 作为项目数据保留。

---

*报告结束 · 质量门 🟢 PASS（收口复核 2026-11-09）· 四套门控 110/110 全绿 · 唯一阻塞 C1 CLOSED · 遗留风险 R1（历史 diff 能力永久丧失，改由不回退 + sha256 全等保证）/ R2（`hud-20261109` 仅能回滚 `#4` 之后）· 最终放行由用户决定*
