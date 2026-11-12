# 持久化验收基线重建报告 · Task #18 / CSEG-BASE-REBUILD

> **用户拍板**：「重建证据链并持久化」——不是降低门槛，是把验收从易失的系统 Temp 依赖里根治出来，并给 #4 的改动补回可回退能力。
> **本轮写入物清单（唯一）**：`.workbuddy/backups/`（新目录及全部内容）+ `音标大闯关/verify_fresh_gate.py` + `音标大闯关/verify_c08_gate.py` + 本报告。**未修改任何游戏产品代码**（`js/` 下的游戏逻辑、`index.html`、`css/`、图片资产一律零改动）。
> **边界**：不部署、不上线、不 commit。项目无 git 仓库、无提交。
> **作者**：engineering-lead（程基岩） · **执行日期** 2026-11-09 · **优先级** P0（插队，先于 #14 技术预研完成）

---

## §1 结论（先看这里）

| 判据（主理人 §三） | 结果 |
|---|---|
| `verify_fresh_gate.py` 21/21 且 F3/F6 转 PASS、CONCERNS 归 0 | ✅ **21 PASS / 0 FAIL / 21 TOTAL**，F3 / F6a / F6b / F6c 全 PASS，**CONCERNS/NOTE: 0** |
| 四套门控合计 ≥110 项全绿 | ✅ **110/110**（38 + 37 + 21 + 14），另 `verify_hud_spec.py` 12/12 |
| 四项错误计数全 0 | ✅ 四套脚本均 `pageerror / console_error / requestfailed / bad_status = 0` |
| `hud-20261108` 46 处唯一 | ✅ 直方图 `{'hud-20261108': 46}`，唯一 |
| `node js/headless_laps.mjs` | ✅ 11 场 **ALL PASS**，最慢 174.57s ≤ 180s |
| `node js/minimap_model.test.mjs` | ✅ 10 PASS / 0 FAIL / 10 TOTAL |
| `python verify_hud_spec.py` | ✅ 12 PASS / 0 FAIL / 12 TOTAL（2 条预存的口径 NOTE，不计失败） |
| Temp 运行时依赖残余 | ✅ **0 处**（`os.environ.get("TEMP")` 全仓验收脚本 0 命中） |
| 13 文件快照作为后续改动的回退点 | ✅ 已落盘，逐字节校验 src==dst |

---

## §2 新旧基线对照（问题的根因与裁决）

### 2.1 采信的主理人事实（已独立核实，不再复查）

- 五个 Temp 回滚点**全部不存在**：`c07b-backup-20261106`、`c08_resume_backup_20261107`、`cseg_backup_20261107`、`hud_backup_20261108`、`rally_b2_published_backup`。项目无 git 仓库 / 无提交；`C:/Users/86135/WorkBuddy` 与 Temp 下 5 层递归零 c07b 副本 → **原样恢复不可行**。
- 唯一残留 `音标大闯关/js/data.js.bak`：11-03 / 5039 行 / 118089 B；当前 `data.js`：11-07 / **7684 行 / 174527 B**。**行数不等、不是 C07-B 前基线**，不能满足 F6a 的 `len(old_lines)==len(cur_lines)`，**不可替代**。
- `verify_fresh_gate.py:33` 原 `C07B = os.path.join(os.environ.get("TEMP","/tmp"), "c07b-backup-20261106")`；`:113` F3 缺失得 `eɪ_old=-1` → 1 FAIL；`:139-160` F6a/F6b/F6c 整段包在 `if os.path.exists(base_data)`，缺失走 else → 1 FAIL。**合计正好 2 FAIL**。
- F6a 原判据 `len(dirty)==0 and 100 <= len(diff) <= 250 and len(old_lines)==len(cur_lines)`：基线换成「当前已验收态」后 `diff` 恒为 0，**必须改写**，否则仍红。

### 2.2 新基线：为什么是「当前已验收 data.js」

| 维度 | 旧基线（已永久丢失） | 新基线（本次建立） |
|---|---|---|
| 位置 | `%TEMP%/c07b-backup-20261106/音标大闯关/js/data.js`（易失） | `<项目根>/.workbuddy/backups/c07b-data-baseline.js`（**项目数据，不是临时缓存，不得删除**） |
| 内容 | C07-B 改动**前**的 data.js | **当前已验收 data.js 的逐字节副本**，174527 B / 7684 行 |
| mtime 语义 | 早于 C07-B | 2026-11-07 08:42:49，**早于 #4 的 11-08** |
| sha256 | 不可考 | `25784ee12bd0f637794f46e37acad604155cb946902e115858f1a69663892d1f` |
| 断言语义 | 「相对历史基线 diff 落在 100–250 行文案行」 | **「与持久化已验收基线逐字一致（不回退）+ sha256 全等锁定」** |
| 强度 | 依赖易失外部文件，实际已降级为 2 FAIL | **不降**：F3 判定式逐字不变、F6a 由「允许 100–250 行 diff」收紧为「diff 必须为 0」、新增 sha256 全等、F6b/F6c 逐字不动、else 分支保留且缺失仍判 FAIL |

**为何可用当前 data.js**：它是 11-07 已验收态，mtime 早于 #4（11-08），且 F4（25 组镜像逐字一致）/ F5（逻辑枚举键 + D01–D05 文案）/ F6b（img/audio/eɪ 计数）/ F6c（content_raw 10-30、data.js.bak 11-03 的 mtime 均早于 data.js）等**独立断言**证明本轮未改动它。这些独立断言不依赖 C07B，是「未改动」的独立证据。

### 2.3 语义变化必须诚实登记

> ⚠️ **C07-B 前 / C08 resume 前的历史 diff 能力已永久丧失，不可恢复。** 新基线提供的保证是「**不回退**」（当前已验收态被逐字节锁定，任何后续改动都会被 F6a 的 `diff==0` 与 `sha256` 全等断言捕获），而**不是**「能重放 C07-B 那次文案修订的完整 diff」。这是能力替换，不是能力保留；本轮已把断言强度从「允许 100–250 行 diff」收紧到「diff 必须为 0」，属**增强**而非放宽。

---

## §3 持久化目录与 13 文件快照

### 3.1 目录结构

```
C:/Users/86135/WorkBuddy/英语音标播客/
└── .workbuddy/                        ← 项目数据目录（已存在，非临时缓存，不得删除）
    └── backups/                       ← 本次新建（持久化根）
        ├── c07b-data-baseline.js       ← 当前已验收 data.js 逐字节副本（174527 B）
        ├── baseline-meta.json          ← 来源 / 复制时间 / 字节 / sha256 全值 / 为何替代 / 消费方
        └── hud-20261109/              ← #4 之后的已验收状态快照
            ├── manifest.txt           ← 13 项：relative_path / bytes / sha256_16 / 源 mtime
            └── (13 个文件，按原相对路径组织)
```

**关键安全性**：四套门控的 `os.walk` 扫描根**仅** `QUEST`（`音标大闯关/`）与 `RALLY`（`音标拉力赛/`），并排除 `assets/ / docs/ / sprite_gen/`。`.workbuddy/backups/` 位于**项目根**，不在两站目录内 → 13 个含 `?v=hud-20261108` 的快照副本**不会污染 S17/F8a/H11 的 46 处计数**。实测直方图 `{'hud-20261108': 46}` 已确认。

### 3.2 `manifest.txt` 头部声明（逐字）

```
# 持久化回滚点 · hud-20261109
# 状态声明：这是 #4 改动「之后」的已验收状态快照，**不是 #4 之前**。
# 原 #4 前快照位于系统 Temp（hud_backup_20261108/），随系统 Temp 清理永久丢失、不可恢复。
# 本快照的作用：作为后续改动的回退点；【不能】用于回滚到 #4 之前。
# FILES = 13   TOTAL_BYTES = 232451
# SOURCE_FILES_UNMODIFIED = YES（逐字节复制后已校验 src==dst）
# 副本已置只读属性；回退时按相对路径 copy 回源根同名路径，并按需清除只读。
```

> **重要**：这是 **#4 之后**的快照，**不是 #4 之前**。原 #4 前基线永久丢失，本快照**不能**回滚到 #4 前；它的作用是给**后续所有改动**提供回退点。副本已置只读，防止被误改。

### 3.3 13 文件清单（relative_path / bytes / sha256_16 / 源 mtime）

| # | relative_path | bytes | sha256_16 | 源 mtime |
|---|---|---:|---|---|
| 1 | `音标拉力赛/js/config.js` | 12076 | `0dfe653c7552aab3` | 2026-11-08 16:38:48 |
| 2 | `音标拉力赛/js/main.js` | 53361 | `2db27bd0c1010faf` | 2026-11-08 16:38:48 |
| 3 | `音标拉力赛/js/race.js` | 31068 | `e9a17cf03dabcada` | 2026-11-08 16:38:48 |
| 4 | `音标拉力赛/js/render.js` | 20357 | `7b65bafa994de5cc` | 2026-11-08 16:38:48 |
| 5 | `音标拉力赛/index.html` | 7839 | `c5bc92ab614336f4` | 2026-11-08 16:38:48 |
| 6 | `音标拉力赛/css/game.css` | 17466 | `2d1b8c453c002f75` | 2026-11-08 16:14:23 |
| 7 | `音标大闯关/index.html` | 3514 | `76be623cd369b82a` | 2026-11-08 16:38:48 |
| 8 | `音标大闯关/js/store.js` | 12981 | `35cd51332a55c7c2` | 2026-11-08 11:06:36 |
| 9 | `音标拉力赛/verify_cseg_gate.py` | 14021 | `7657d300432a6859` | 2026-11-08 16:38:48 |
| 10 | `音标拉力赛/verify_cseg_ui.py` | 12883 | `04234ff10db8dba8` | 2026-11-08 16:38:48 |
| 11 | `音标大闯关/verify_fresh_gate.py` | 18863 | `6c898d82fa6afe43` | 2026-11-08 16:38:48 |
| 12 | `音标大闯关/verify_c08_gate.py` | 20623 | `b620efceafbebc99` | 2026-11-08 16:38:48 |
| 13 | `音标拉力赛/js/headless_laps.mjs` | 7399 | `41443f3fe153b8f9` | 2026-11-08 16:38:48 |
| | **合计** | **232451** | | |

> 清单照 `design/hud-impl-plan.md` §F 的 13 项（含附加的 `headless_laps.mjs` 回归链入口）。原 Temp manifest 已丢失，本清单按 §F 逐项列全并补齐 sha256 与源 mtime。注意 sha256_16 与 §F 旧值不同是**预期的**——本快照是 #4 **之后**的状态，#4 已修改其中 5 个产品文件并 bump 缓存串。

---

## §4 脚本逐行改动 diff（只列改了哪几行及理由）

**仅 2 个验收脚本被修改**，其余 11 个文件（含全部游戏产品代码）与快照**逐字节全等**（`_baseline_verify.py` 实测：13 文件中变化 = 2）。

### 4.1 `音标大闯关/verify_fresh_gate.py`（改 6 处）

| # | 行（改后） | 改动 | 理由 |
|---|---|---|---|
| 1 | `:19-22` docstring 末尾 | 新增 1 行 | 主理人指定头部注释：`2026-11-09 基线迁移：原 Temp 基线随系统清理丢失，经用户批准改为项目内持久化基线；断言强度不降` |
| 2 | `:35-39` | `C07B = os.path.join(os.environ.get("TEMP","/tmp"), "c07b-backup-20261106")` → `BASELINE = os.path.join(ROOT, ".workbuddy", "backups", "c07b-data-baseline.js")` + 4 行说明 | 基线路由改为项目内持久化路径，**不使用 TEMP 环境变量推导** |
| 3 | `:117` | `base_data = os.path.join(C07B, "音标大闯关","js","data.js")` → `base_data = BASELINE` | 同上；**F3 判定式 `eɪ_now == eɪ_old` 逐字未改**，只是 `eɪ_old` 从持久化基线算，语义变为「eɪ 计数相对已验收基线稳定」 |
| 4 | `:148-159` | **F6a 改写**：判定式 `len(dirty)==0 and 100<=len(diff)<=250 and len(old_lines)==len(cur_lines)` → `len(diff)==0 and len(dirty)==0 and len(old_lines)==len(cur_lines) and sha_equal`；新增 `sha_cur / sha_base / sha_equal` 三行；`chk` 名称改为「与持久化已验收基线逐字一致（不回退）」；detail 增加 `sha256 全等` / `sha256_16` | 基线换成当前已验收态后 `diff` 恒 0，原 `100<=diff<=250` 会误红；改为**等价不回退断言 + sha256 全等锁定**，名称与描述同步更新「不要留旧名字骗人」 |
| 5 | `:171-173` else | `chk("F6 基线缺失（c07b-backup-20261106）", False, base_data)` → `chk("F6 持久化基线缺失（.workbuddy/backups/c07b-data-baseline.js）", False, base_data)` + 1 行注释 | **保留 else 分支**，改成指向持久化基线的明确报错；若持久化基线也缺失**仍判 FAIL，不静默放行** |
| 6 | — | **未动**：F1 / F1b / F2 / F4 / F5 / F6b / F6c / F7 / F8a / F8b / F9a / F9b / F9c / F10a / F10b / F11a–F11d 全部逐字保留 | 遵守「禁止删除/跳过/降级任何其它 chk；禁止改 F1/F2/F4/F5/F7/F8a/F8b/F9/F10/F11 任何逻辑；禁止放宽阈值」 |

> **F6a 项数说明**：主理人判据要求 `verify_fresh_gate.py` **21/21**（项数不变），因此「新增一条 sha256 全等断言」实现为 **F6a 判定式内的新增合取条件 `and sha_equal` + detail 输出**，而非新增独立 `chk`（否则会变成 22 项，与 21/21 冲突）。断言强度不降：F6a 仍是一条独立 chk，且判定式从 3 个条件增至 4 个。

### 4.2 `音标大闯关/verify_c08_gate.py`（改 1 处）

| 行（改后） | 改动 | 理由 |
|---|---|---|
| `:289-291` | `bak_data = os.path.join(os.environ.get("TEMP","/tmp"), "c08_resume_backup_20261107", "音标大闯关__js__data.js")` → `bak_data = os.path.join(ROOT, ".workbuddy", "backups", "c07b-data-baseline.js")` + 2 行注释 | 主理人 §二.5「清扫其它 Temp 依赖」：全仓 grep 发现这是四套脚本里**唯一另一处**真实 Temp 路径依赖（D9.2 真双元音 13 行比对）。**只改路径常量，断言代码逐字不动** |

**附带效果（已实测）**：原 `c08_resume_backup_20261107` 不存在时，`if os.path.exists(bak_data)` 为假，**D9.2 整段被跳过**（不计 chk）。指向持久化基线后 D9.2 **实际执行并 PASS**，c08_gate 的覆盖从「跳过」变为「验证」——**断言覆盖不降反升**，且仍为 37 项（D9.2 原本就在计数内时是条件跳过，现转为有效验证；实测 SUMMARY 37 PASS / 0 FAIL）。

### 4.3 全仓 Temp 依赖清扫结果

grep 关键词：`TEMP` / `AppData\/Local\/Temp` / `c07b` / `c08_resume` / `cseg_backup` / `hud_backup` / `rally_b2_published`，范围 = 四套验收脚本 + `verify_hud_spec.py`。

- **迁移前真实运行时依赖 2 处**：`verify_fresh_gate.py:33`（C07B 常量）+ `verify_c08_gate.py:289`（bak_data）→ **均已迁移**。
- **迁移后运行时依赖 `os.environ.get("TEMP")` = 0 处**（`_baseline_verify.py` 正则实测）。
- 残余命中均为**注释/说明文字**，不是路径依赖：`verify_cseg_gate.py:5` 的 `C:/Users/86135/AppData/Local/Programs/Python/Python313/python.exe`（用法说明里的 Python 解释器路径，非 Temp）、本报告 §2 与各脚本 2026-11-09 迁移注释中的「Temp / c07b」字样。`agent-sprite-forge/` 下的 `TEMPLATE` / `TEMPORAL_KEEP` / `TEMPORARY` 是无关变量名，且不属于四套验收脚本，不在范围。
- **0 处需要额外迁移**（除上述 2 处外）。

---

## §5 全量复跑结果（串行，未并发）

执行顺序（严格串行，避免 #4 已披露的 in-process `ThreadingHTTPServer` 并发抖动）：

| # | 命令 | 结果 | 四项错误计数 |
|---|---|---|---|
| 1 | `python verify_fresh_gate.py`（音标大闯关/） | **21 PASS / 0 FAIL / 21 TOTAL**，CONCERNS/NOTE **0** | `pageerror 0 / console_error 0 / requestfailed 0 / bad_status 0` |
| 2 | `python verify_cseg_gate.py`（音标拉力赛/） | **38 PASS / 0 FAIL / 38 TOTAL** | 全 0 |
| 3 | `python verify_c08_gate.py`（音标大闯关/） | **37 PASS / 0 FAIL / 37 TOTAL**（D9.1/D9.2/D9.3 全 PASS） | 全 0 |
| 4 | `python verify_cseg_ui.py`（音标拉力赛/） | **14 PASS / 0 FAIL / 14 TOTAL** | 全 0 |
| 5 | `python verify_hud_spec.py`（音标拉力赛/） | **12 PASS / 0 FAIL / 12 TOTAL**（2 条预存口径 NOTE，不计失败） | 全 0 |
| 6 | `node js/headless_laps.mjs` | **ALL PASS**，11 场，最慢 174.57s ≤ 180s | — |
| 7 | `node js/minimap_model.test.mjs` | **10 PASS / 0 FAIL / 10 TOTAL** | — |

**四套门控合计 = 38 + 37 + 21 + 14 = 110 / 110 全绿 ✅**（判据为 ≥110）。
**加第 5 套 HUD 验收 12 项 → 122 / 122 全绿。**
`verify_hud_spec.py` 的 2 条 NOTE 是该脚本既有的口径披露（H10 signKey 不可观测 / H4 #quiz 层叠口径），**非本轮基线迁移引入**，且按脚本约定不计入 PASS/FAIL，不影响「CONCERNS 归 0」判据（该判据指 `verify_fresh_gate.py`，实测 0）。

**关键断言明细**：

- F3：`{'/e/ 命中': 0, 'eɪ 当前': 5, 'eɪ 基线': 5}` → PASS
- F6a：`{'基线行数': 7684, '当前行数': 7684, 'diff 行数': 0, '逻辑键改动': [], 'sha256 全等': True, 'sha256_16': '25784ee12bd0f637'}` → PASS
- F6c：`content_raw 10-30 11:05 < data.js 11-07 08:42`、`data.js.bak 11-03 07:45 < data.js` → PASS（上游管线未重跑）
- F8a / S17：`{'hud-20261108': 46}` → 唯一且恰好 46
- 未触发 `ERR_CONNECTION_REFUSED` / `ERR_ABORTED` 抖动，**未放宽任何断言**

---

## §6 完整性校验（独立复核）

| 项 | 结果 |
|---|---|
| 13 文件快照 src == dst（逐字节） | ✅ 复制时已逐项断言；副本置只读 |
| 快照 vs 当前源：变化文件数 | ✅ **2**（仅 `verify_fresh_gate.py` / `verify_c08_gate.py`；**其余 11 个含全部游戏产品代码逐字节未动**） |
| `python -m py_compile` 两个脚本 | ✅ OK |
| `BASELINE` 与当前 `data.js` 逐字节全等 | ✅ 174527 B，sha256 `25784ee1…` |
| `baseline-meta.json` | ✅ 含来源路径 / 复制时间 / 字节 / sha256 全值 / 为何替代 / 消费方 |
| tag 直方图（复刻四套脚本扫描口径） | ✅ `{'hud-20261108': 46}`，唯一 |
| 备份根不在 `QUEST`/`RALLY` 扫描根内 | ✅ 确认（不会污染 46 计数） |
| TEMP 运行时依赖残余 | ✅ 0 处 |
| 未修改游戏产品代码 / 图片 / 其它验收脚本断言 | ✅ 实测 |

---

## §7 遗留风险与必须诚实登记的事项

1. **⚠️ C07-B 前 / C08 resume 前的历史 diff 能力已永久丧失，不可恢复。** 新基线只提供「**与当前已验收态逐字一致（不回退）+ sha256 全等锁定**」的持续保证，**不能**重放 C07-B 那次文案修订的完整 diff，也**不能**证明「C07-B 当时只改了 100–250 行文案行」。这是能力替换而非能力保留；已通过收紧 F6a（diff 从「允许 100–250」改为「必须 0」）+ 新增 sha256 全等补强，但历史审计链本身缺失。**建议**：若未来需要历史审计，应尽早建立 git 仓库并做首次提交（需用户单独批准，本轮不 commit）。
2. **⚠️ `hud-20261109/` 是 #4 之后的快照，不能回滚到 #4 之前。** 原 #4 前 Temp 快照永久丢失；本快照只对**后续改动**提供回退能力。manifest 头部已逐字写明，避免误用。
3. **`.workbuddy/backups/` 必须作为项目数据长期保留、不得删除、不得当作临时缓存清理。** 一旦删除，F3/F6 会回到 2 FAIL，D9.2 会退回「跳过」，且 else 分支明确判 FAIL、不会静默放行。建议纳入版本控制或部署清单（需用户批准）。
4. **基线是「当前已验收态」的静态副本，需显式更新流程。** 未来若 `data.js` 因正当需求变更，必须**同步更新** `c07b-data-baseline.js` 与 `baseline-meta.json`，并重新跑四套门控；否则 F6a 会以「不回退」为由判红。这是**设计意图**（任何改动都必须被看见），不是缺陷，但需要写进后续维护约定。
5. **`verify_hud_spec.py` 的 2 条 NOTE 属预存口径披露，本轮未处理**（不在 #18 授权范围内；它是 #5 / quality-lead 的脚本）。建议由主理人转 quality-lead 决定是否收敛。
6. **`data.js.bak`（11-03 / 5039 行）仍在站内**，F6c 用它做 mtime 断言。它**不是** C07-B 前基线，不应被误当作基线使用；本轮未改动它。
7. **四套门控必须串行跑**。#4 已披露并发启动 Playwright / in-process server 会出现 `ERR_CONNECTION_REFUSED` / `ERR_ABORTED` 瞬态抖动；本轮串行一次通过，未触发。
8. **两个脚本的迁移注释中出现「Temp / c07b」字样**，属说明文字；全仓 grep 时会被命中，但**不是路径依赖**。后续若做自动化「零 Temp 依赖」扫描，应按 `os.environ.get("TEMP")` 等运行时模式判定，避免把注释误判为残留。

---

## §8 边界复核

- ✅ 只改 `verify_fresh_gate.py`（逻辑 + 路径）与 `verify_c08_gate.py`（仅路径常量）；其余 11 个产品/脚本文件逐字节未动。
- ✅ 未修改 `index.html` / `css/` / `js/` 下的游戏逻辑 / 图片资产 / 上游构建管线 / `data.js` / `ipa-display.js`。
- ✅ 未删除/跳过/降级任何 chk；F1/F2/F4/F5/F7/F8a/F8b/F9/F10/F11 逐字保留；未放宽任何阈值。
- ✅ 未部署、未上线、未 commit。
- ✅ 禁止与其他成员直连（本报告与结论经主理人中转）。

---

*本报告为 Task #18 / CSEG-BASE-REBUILD 的交付主体。完成后按主理人指令继续 #14 3D 技术预研（含并入 config.js A/B 分组键陷阱与 ADR 集）。*
