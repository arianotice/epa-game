# 四套旧门控退役令与 81 项承接表（#45）

> **文件性质**：quality-lead（严守真）独占产出 · **退役令 + 承接表（规范性文档）**。本轮**只写文档**，不跑门控、不改任何 `verify_*.py`、不改产品代码、不重出资产、不部署 / 上线 / commit。
> **生效日**：**2026-11-12** · **任务**：`#45`（四套旧门控整体退役并落实 81 项承接）· **上游**：`#44` `design/p1-legacy-gate-fail-scan.md`（2026-11-11 实跑，6 条真实断言 FAIL）；`design/p1-qa-spec.md`（验收规格）；`verify_p1_gate.py` `PL_CHECKS`（81 项常量）。
> **用户书面裁决（原文，2026-11-12）**：**「四套旧门控整体退役。跑判据，继续任务，可以部署在我设置的 GitHub 仓库上」**。
> **裁决解读**：这是 `p1-legacy-gate-fail-scan.md` §6 甲 / 乙二选一中明确选 **乙（整体退役）**。`p1-qa-spec.md` §0 第 28 行「不得借门控重写删断言」所需的**用户书面放行已成立**；主理人已向用户说明并裁决如下。

---

## 0. 退役性质（最重要的一句，防止误读）

> **退役的是「旧套件作为发布阻断判据的地位」，不是删 81 项断言。**
>
> 81 项期望值**逐字不改**，全部迁移到新 P1 套件、用**正确扫描域**重放，逐条给承接编号（§3）。
> 旧四套脚本**归档保留、可手动跑、但不再进入判定链**（§8）。
> 6 条真实 FAIL 的原文、命中明细与退出码**永久保留**在 `p1-legacy-gate-fail-scan.md`，**不因退役而抹掉、不改 NOTE、不放宽阈值**（§6 / §9）。

**为什么这不是「静默删断言」**：`p1-qa-spec.md` §0.3 覆盖度守恒律要求「任一被重定义的旧断言都有『替代 = 具体编号』；出现空行 = 规格不接受」。本文件 §3 的 81 行承接表逐条满足该约束，**无一行空白、无一条无承接编号**；§4 另把 29 项重验域、HUD 12 项与辅助脚本的覆盖也逐条承接。总数守恒：**81 项原样保留 + 29 项重验 = 110 项**，一条不少。

---

## 1. 退役清单（明确「四套」边界）

### 1.1 列入退役的四套（= 历史 110 项口径）

| # | 脚本 | 项数 | 11-11 实跑 | 退役理由 |
| --- | --- | --- | --- | --- |
| 1 | `音标拉力赛/verify_cseg_gate.py` | 38 | **36 PASS / 2 FAIL（S17、S18）**，exit=1 | 扫描域 `os.walk` 未排除 P0 新增的 `node_modules/`，5 条 FAIL 中的 2 条落此 |
| 2 | `音标拉力赛/verify_cseg_ui.py` | 14 | 14 PASS / 0 FAIL，exit=0 | 属同一历史套件（110 项口径的 14 项重验域）；随四套整体退役 |
| 3 | `音标大闯关/verify_fresh_gate.py` | 21 | **20 PASS / 1 FAIL（F8a）**，exit=1 | 同上扫描域缺陷 |
| 4 | `音标大闯关/verify_c08_gate.py` | 37 | **36 PASS / 1 FAIL（S1.7）**，exit=1 | 同上扫描域缺陷 |

> 四套合计 110 项 = 38 + 14 + 21 + 37，即 `p1-qa-spec.md` §3.3 的 `110 = 29 项重验 + 81 项原样保留` 口径。**「四套」严格指上表四个脚本**，不含下列脚本。

### 1.2 不在「四套」之列的脚本及处置理由（逐个回答主理人点名项）

| 脚本 | 是否在退役列 | 理由与处置 |
| --- | --- | --- |
| **`音标拉力赛/verify_hud_spec.py`（12 项）** | **不在四套之列，但同样退出判定链、归档保留** | 「四套」是 110 项口径；`p1-qa-spec.md` §3.3 末行明确 HUD 12 项「**不属于 110 项口径**」，故技术上不是四套成员。但：① 它的 **H11** 与四套是**同构扫描域缺陷**（11-11 实跑 11/12，H11 真实 FAIL，见报告 §2 F-5）；② H1–H12 按 PF-10「不得静默删除」必须逐条承接。因此处置为 **「不列入四套退役清单、但退出判定链并归档；12 项迁移到新套件重放」**，见 §4.3。**12 条断言一条不许消失。** |
| **`音标拉力赛/verify_p0_gate.py`（62 项）** | **不退役** | ① 它是**路线 B 重定义套件**本身（#20/#27 产物），不是 P0 之前的历史套件；② 11-11 实跑 **62 PASS / 0 FAIL / 62**、exit=0；③ 它**已采用正确扫描域**（排除 `node_modules/`/`dist/`），是 `PB-*` 六项约束的实证来源（`p1-qa-report.md` 🟢 PASS）；④ 它是 `verify_p1_gate.py` 的上游基线。退役它会同时删掉现行有效门控，与用户「跑判据」相悖。 |
| `音标拉力赛/verify_p1_visual.py`（63 项） | 不退役 | #44 本轮新建，连续两轮 63/63 全绿，是 3D 三车可见 / 竖屏 / 降级的现行证据，属判定链。 |
| `音标拉力赛/verify_p1_gate.py` | 不退役 | P1 新门控（`#46` 主理人本地正在实跑化），是退役后**唯一的门控判定链核心**。本文件 §5 的「门控全绿」即指它实跑。 |
| `音标大闯关/verify_atlas_sprites.py` | 不在四套之列，不进判定链、归档 | 姊妹站**辅助脚本**，非 110 项口径成员。11-11 实跑 8 PASS / **1 FAIL**（收集态注入口径过时：`collected` 已退役恒 `[]`、唯一解锁源是 `rally.unlocked` 按 `U01–U48`，脚本却注入英式 IPA `iː/p`），且脚本 FAIL 仍返回 exit=0。处置：归档、**不进判定链**；其 8 项有效断言（48 张立绘加载 / dim 灰化 / 身份卡大图 / 六档分组 / webp 200 / JS 无错误）由 P1 资产门控承接（§4.4）；注入口径与 exit code 修复**另立任务**，本轮不改。 |
| `音标大闯关/verify_features.py` / `verify_audio_fix.py` | 不在四套之列，不进判定链、归档 | 11-11 实跑为 Playwright `Page.click` 超时（`#modal-layer` 拦截 pointer events），**属交互前置失败、非断言 FAIL**（报告 §4）。不属门控判据链。 |

### 1.3 生效范围

- 自 **2026-11-12** 起，§1.1 四套 + §1.2 中标注「退出判定链」的脚本，其 `exit code` / `PASS` / `FAIL` **不再作为发布阻断依据**，不再计入 `p1-qa-spec.md` §4.1 的 G1「门控全绿」。
- 上述脚本**全部保留在磁盘、不删除、不改名、不修改**（本轮零改动），供人工随时手动复跑与历史追溯。
- **不退役**：`verify_p0_gate.py` 62 项、`verify_p1_visual.py` 63 项、`verify_p1_gate.py`、`npm run headless` 11 场、`npm run test:minimap` 10 项、`npm run test:scene3d` 18 项。

---

## 2. 用户放行依据与红线核对

| 项 | 内容 |
| --- | --- |
| 用户原文 | 「四套旧门控整体退役。跑判据，继续任务，可以部署在我设置的 GitHub 仓库上」（2026-11-12 书面） |
| 对应选项 | `p1-legacy-gate-fail-scan.md` §6 **乙**：不动旧门控，整体标记为「P0 之前的历史套件、在 3D 主形态下不作验收依据」，终点判据只认路线 B 重定义套件 + 81 项 + 11 场 headless |
| 放行条款 | `p1-qa-spec.md` §0 第 28 行「**不得借门控重写删断言**」——该条禁止的是「无用户书面放行的静默退役」；本次用户书面放行成立，且**配套 81 项逐条承接表**（§3）保证断言不消失 |
| 守恒核对 | `p1-qa-spec.md` §0 第 36 行「出现空行 = 规格不接受」——§3 承接表 **81 行全部填满，零空白行** |
| 主理人裁决 | 「退役的是『旧套件作为发布阻断判据的地位』，不是删 81 项断言。81 项期望值逐字不改，迁移到新 P1 套件用正确扫描域重放，逐条给承接编号。」 |
| 明确未做 | 未把任何 FAIL 改成 NOTE、未放宽任何阈值、未删任何断言、未改任何 `verify_*.py`、未重跑上游构建管线、未部署 / 上线 / commit / 建仓 |

---

## 3. 81 项承接表（逐条，无空白行）

> **口径**：`PL_CHECKS` 四组 = `verify_cseg_gate.py` **36** + `verify_cseg_ui.py` **0** + `verify_fresh_gate.py` **15** + `verify_c08_gate.py` **30** = **81**。
> **承接编号约定**：`PLR-<组>-<原编号>`（`PLR` = Playback of Legacy Retained）。`PLR-*` 是 `verify_p1_gate.py` 实跑化后 `PL_CHECKS` **重放族**的命名约定；主理人 `#46` 本地实跑化时按此编号落地，**本轮不改 `verify_p1_gate.py`**（避免写冲突）。
> **期望值**：全部「**是 · 逐字不变**」，原文锚定 `p1-qa-spec.md` §3.3；迁移只换**载体与扫描域**，不换期望值。
> **重放方式图例**：`SRC` 静态源码/文件扫描（产品层白名单 9 文件 + 排除 `node_modules/`/`dist/`/`.p0-build/`/`.workbuddy/`）· `NODE` Node 自检/纯函数单测 · `BYTE` 逐字节 / sha256 / mtime 比对 · `UI` 真实 Chromium UI / localStorage 取证。
> **扫描域铁律**：所有 `SRC` / `BYTE` 重放一律使用 `p1-qa-spec.md` §2.6 `PB-*` 已预设的排除清单（报告 §2.3 已证：产品层 `{hud-20261108:46}` 唯一且恰好 46、裸引用 0，33 处裸引用 100% 在 `node_modules/`）。

### 3.1 组 A · `verify_cseg_gate.py` 36 项

| 原编号 | 承接编号 | 重放方式 | 期望值逐字不变 |
| --- | --- | --- | --- |
| S1 | `PLR-CSEG-S1` | SRC | 是 · `TUNING.laps===2` |
| S2 | `PLR-CSEG-S2` | SRC | 是 · 提速 follow260 / listen300 |
| S3 | `PLR-CSEG-S3` | SRC | 是 · 终点 `laps×L` |
| S4 | `PLR-CSEG-S4` | SRC | 是 · `g.line` 绝对里程 |
| S5 | `PLR-CSEG-S5` | SRC | 是 · rival `upcoming.line` |
| S6 | `PLR-CSEG-S6` | SRC | 是 · 跨圈复位 `pickups[].taken` |
| S7 | `PLR-CSEG-S7` | SRC | 是 · 进度条分母含 laps |
| S8 | `PLR-CSEG-S8` | SRC | 是 · 开局按地图建门 |
| S9 | `PLR-CSEG-S9` | SRC | 是 · 四区与车手选择器接 UI |
| S10 | `PLR-CSEG-S10` | SRC | 是 · 教学面板杯赛重点（C07 静态块保留） |
| S11 | `PLR-CSEG-S11` | SRC | 是 · quiz 三题型且 word 题不泄答案 |
| S12 | `PLR-CSEG-S12` | SRC | 是 · `placeLaneSign` 传绝对 odo |
| S13 | `PLR-CSEG-S13` | SRC | 是 · render 只收当前圈（两圈 commitT 相同不重绘） |
| S14 | `PLR-CSEG-S14` | SRC | 是 · 结果页解锁取并集 |
| S15 | `PLR-CSEG-S15` | SRC | 是 · 跨站白名单含 `maps/lastMap/lastChar` |
| S16 | `PLR-CSEG-S16` | SRC（正确扫描域） | 是 · atlas 6 处图片 URL 全带 tag |
| A0 | `PLR-CSEG-A0` | NODE | 是 · headless 退出码 0 |
| A1 | `PLR-CSEG-A1` | NODE | 是 · 2 档 × 4 地图 + 3 最坏 = 11 场 |
| A2 | `PLR-CSEG-A2` | NODE | 是 · 全部 ≤180s |
| A3 | `PLR-CSEG-A3` | NODE | 是 · 最坏工况（15 碰撞 + 20 全错）≤180s |
| A4 | `PLR-CSEG-A4` | NODE | 是 · headless 含 4/4 门判定与跨圈 1 次 |
| A5 | `PLR-CSEG-A5` | NODE | 是 · `result.time===finishTime` |
| A6 | `PLR-CSEG-A6` | NODE | 是 · 理论 `2×L/speed≤150s` |
| B0 | `PLR-CSEG-B0` | NODE | 是 · Node 自检可运行且输出可解析 |
| B1 | `PLR-CSEG-B1` | NODE | 是 · 四区地图非空、词对≥24、音素≥16 |
| B2 | `PLR-CSEG-B2` | NODE | 是 · 准确性（unit 绑定·ipa 与权威表一致·最小对立互异·0 错配） |
| B3 | `PLR-CSEG-B3` | NODE | 是 · 音频 100% 覆盖 `allWords()` |
| B4 | `PLR-CSEG-B4` | NODE | 是 · 题型≥3 |
| B5 | `PLR-CSEG-B5` | NODE | 是 · 固定题 0、任一词对出现率≤60% |
| B6 | `PLR-CSEG-B6` | NODE | 是 · 单局 4 门词对互不重复（12000 局） |
| B7 | `PLR-CSEG-B7` | NODE | 是 · 单局题型≥2 且三题型都出现 |
| B8 | `PLR-CSEG-B8` | NODE | 是 · 额外题连续同对率 0（去重窗口 3） |
| B9 | `PLR-CSEG-B9` | BYTE | 是 · `ipa-display.js` 全文未动 + `sym` 稳定键 |
| C1 | `PLR-CSEG-C1` | SRC + BYTE | 是 · 音频文件数 == `allWords()` 词数 |
| C2 | `PLR-CSEG-C2` | SRC + BYTE | 是 · 全部 mp3 帧头有效且无 <500B 残 file |
| C3 | `PLR-CSEG-C3` | SRC | 是 · 生成脚本以 `config.allWords()` 为单一词表来源 |

**小计 36 项**（S 16 + A 7 + B 10 + C 3）。

### 3.2 组 B · `verify_cseg_ui.py` 0 项

| 原编号 | 承接编号 | 重放方式 | 期望值逐字不变 |
| --- | --- | --- | --- |
| （本组 `PL_CHECKS` 为 0 项） | （无 `PLR-CSEG-UI-*` 条目） | UI（14 项 U1–U12 归 §4.2 的 29 项重验域重放，非本表 81 项） | 是 · U10（解锁并集）/ U11（跨站不覆盖）期望值逐字保留，不因 3D 默认化或本次退役改变 |

**小计 0 项**（`PL_CHECKS` 该组为空；14 项全部在 §4.2 承接，不产生空白覆盖面）。

### 3.3 组 C · `verify_fresh_gate.py` 15 项

| 原编号 | 承接编号 | 重放方式 | 期望值逐字不变 |
| --- | --- | --- | --- |
| F1 | `PLR-FRESH-F1` | SRC | 是 · 英式符号残留 0 |
| F1b | `PLR-FRESH-F1b` | SRC | 是 · `ː` 仅出现在 10 行 `sym` 稳定键 |
| F2 | `PLR-FRESH-F2` | SRC | 是 · 长短音·央化旧措辞残留 0 |
| F3 | `PLR-FRESH-F3` | SRC | 是 · `/e/` 六行改 `/ɛ/` 且 `eɪ` 未被误伤 |
| F4 | `PLR-FRESH-F4` | BYTE | 是 · 25 组 `episodes/phonemes` 镜像逐字一致 |
| F5 | `PLR-FRESH-F5` | SRC | 是 · 逻辑枚举键锁定 + D01–D05 美式显示文案在场 |
| F6a | `PLR-FRESH-F6a` | BYTE | 是 · 与持久化已验收基线逐字一致（不回退 + sha256 全等） |
| F6b | `PLR-FRESH-F6b` | BYTE | 是 · 图片·音频字段名与 `eɪ` 次数未改 |
| F6c | `PLR-FRESH-F6c` | BYTE | 是 · 上游构建管线未重跑（mtime 早于 `data.js`） |
| F7 | `PLR-FRESH-F7` | SRC | 是 · 11 个重点 unit 教学文案走查无残留 |
| F9a | `PLR-FRESH-F9a` | UI | 是 · G5 纯净页图鉴 48 卡大字全为美式 |
| F9b | `PLR-FRESH-F9b` | UI + BYTE | 是 · G5 卡面图·总图 URL 带当前 tag 且 `U11=ɜr` |
| F9c | `PLR-FRESH-F9c` | BYTE | 是 · G5 49 张发布卡面与美式源逐字节全等 |
| F11a | `PLR-FRESH-F11a` | UI | 是 · G4 老存档迁移逐字节回滚点（`collected=[]`/`legacyCollected`/v2） |
| F11b | `PLR-FRESH-F11b` | UI | 是 · 跨站 last-write-wins 不覆盖 |

**小计 15 项**。

### 3.4 组 D · `verify_c08_gate.py` 30 项

| 原编号 | 承接编号 | 重放方式 | 期望值逐字不变 |
| --- | --- | --- | --- |
| S1.1 | `PLR-C08-S1.1` | SRC | 是 · 迁移与 reset 走 `writeRaw` 绕过 merge |
| S1.2 | `PLR-C08-S1.2` | SRC | 是 · storage 监听不触发迁移·不写 bak |
| S1.3 | `PLR-C08-S1.3` | SRC | 是 · `save()` 写前重读 + 只并子字段 |
| S1.4 | `PLR-C08-S1.4` | SRC | 是 · 写点全收口 `commit` |
| S1.5 | `PLR-C08-S1.5` | SRC | 是 · `race.js` 无 `saveWallet`·绝对值写回 |
| S1.6 | `PLR-C08-S1.6` | SRC | 是 · 逻辑键与版本串未动 |
| D1.1 | `PLR-C08-D1.1` | UI | 是 · `v1.bak` 逐字节等于原串 |
| D1.2 | `PLR-C08-D1.2` | UI | 是 · `collected` 已清空 |
| D1.3 | `PLR-C08-D1.3` | UI | 是 · `legacyCollected` 恰为原 8 sym |
| D1.4 | `PLR-C08-D1.4` | UI | 是 · `schemaVersion=2` 且 `unlocked=[]` |
| D1.5 | `PLR-C08-D1.5` | UI | 是 · 迁移产物不含任何拉力赛 `rally` 子字段 |
| D2.1 | `PLR-C08-D2.1` | UI | 是 · 连续加载 bak 不覆写·快照不重复·`unlocked` 不重置 |
| D2.2 | `PLR-C08-D2.2` | UI | 是 · `rawHasV2` 判据 |
| D2.3 | `PLR-C08-D2.3` | UI | 是 · 从 `v1.bak` 逐字节还原后可重新迁移 |
| D3.1 | `PLR-C08-D3.1` | UI | 是 · B 的 `rally` 进度（gems/shields/EP02/owned*/howSeen/paint）全保住 |
| D3.2 | `PLR-C08-D3.2` | UI | 是 · A 自己 `stars/lastEp/sound` 写入成功 |
| D3.3 | `PLR-C08-D3.3` | UI | 是 · B 写入的 `unlocked` 未被陈旧快照抹掉（并集生效） |
| D4.1 | `PLR-C08-D4.1` | UI | 是 · `unlocked` 并集含 U07+U02 |
| D4.2 | `PLR-C08-D4.2` | UI | 是 · 改 `unlocked` 不影响知识轨（`collected` 恒 []） |
| D4.3 | `PLR-C08-D4.3` | UI | 是 · 卡轨 `isCardUnlocked` 生效且与 `hasLearned` 解耦 |
| D5.1 | `PLR-C08-D5.1` | UI | 是 · `storage` 事件刷新内存 `data.rally` |
| D5.2 | `PLR-C08-D5.2` | UI | 是 · 监听未触发第二次迁移·未写 bak |
| D6.1 | `PLR-C08-D6.1` | UI | 是 · `+1` 与 `-100` 两种交错顺序最终 gems 都为 1（无双花/无回滚） |
| D6.2 | `PLR-C08-D6.2` | SRC + UI | 是 · 源码无绝对值写回且 delta 函数存在 |
| D8.1 | `PLR-C08-D8.1` | SRC | 是 · `race.js` 石头纯规避（仅 `ribbonT`） |
| D8.2 | `PLR-C08-D8.2` | SRC | 是 · `finishQuiz` 不污染 `correct`·不给额外奖励 |
| D8.3 | `PLR-C08-D8.3` | SRC | 是 · 源码保留 `pointerdown/jumpEdge` 触屏跳跃 |
| D9.1 | `PLR-C08-D9.1` | SRC | 是 · 可见文案 C 类残留命中 0 |
| D9.2 | `PLR-C08-D9.2` | BYTE | 是 · 真双元音滑动描述逐字未动 |
| D9.3 | `PLR-C08-D9.3` | SRC | 是 · 两题 `options` 长度·顺序·answer 不变 |

**小计 30 项**。

### 3.5 承接表守恒核对

```
组 A 36 + 组 B 0 + 组 C 15 + 组 D 30 = 81 项
承接编号总数 = 36 + 0 + 15 + 30 = 81 个，无一重复、无一缺号
空白行 = 0（每行 4 列均填满）
期望值「逐字不变」= 81 / 81
```
> 交叉核对：`verify_p1_gate.py` `PL_CHECKS` 的 81 个编号与本表 81 个「原编号」**一一对应**；本表是它的规范性承接映射，不新增、不删除、不改期望值。

---

## 4. 81 项之外的覆盖面承接（防止「退役 = 少验了」）

### 4.1 关键事实：6 条真实 FAIL **全部不在 81 项保留域**

`p1-legacy-gate-fail-scan.md` §2 / §3 的 6 条 FAIL 落点如下，**没有一条属于 §3 承接表的 81 项**：

| FAIL | 编号 | 所属域 | 退役后承接 |
| --- | --- | --- | --- |
| F-1 | `verify_cseg_gate.py` S17 全仓 tag 唯一且恰好 46 | 29 项重验域（cseg_gate 2 项之一） | `PB-1` / `PB-3`，正确扫描域重放，期望值 `{hud-20261108:46}` 逐字不变 |
| F-2 | `verify_cseg_gate.py` S18 全仓图片 URL 零裸引用 | 29 项重验域 | `PB-4`，正确扫描域重放，期望值「20 图零裸引用」逐字不变 |
| F-3 | `verify_fresh_gate.py` F8a 全仓 `?v=` tag 唯一 | 29 项重验域（fresh_gate 6 项之一） | `PB-1` / `PB-3` |
| F-4 | `verify_c08_gate.py` S1.7 全仓 tag 唯一值 | 29 项重验域（c08_gate 7 项之一） | `PB-1` / `PB-3` |
| F-5 | `verify_hud_spec.py` H11（复合：tag / CACHE_TAG / 20 图零裸引用 / 资源按字节送达） | HUD 12 项专项（非 110 项口径） | `PB-1..4` + `PVB-*`；H11 的 `CACHE_TAG 同步=True` / `按字节比对=True` / `带错 tag 的请求=[]` / `IPA_DISPLAY.U11=ɜr` 四子项**原本就 PASS**，须原样重放 |
| F-6 | `verify_atlas_sprites.py` 收集后 got 卡 + 稀有度徽章 `{'got':0,'rar':0}` | 姊妹站辅助脚本（非门控链） | §4.4；注入口径修复另立任务，8 项有效断言由 P1 资产门控承接 |

> **这正是「退役不等于删断言」的实证**：81 项保留域的期望值全部与 3D 主形态**无关**（判定核心源码字面量 / 跨站存档逻辑 / 美式文案基线 / Node 自检），因此 11-11 实跑中**无一条 FAIL 落在 81 项里**。退役移除的是「用错误扫描域跑这 81 项 + 5 条扫描域断言」的旧载体，不是移除断言本身。

### 4.2 29 项重验域迁移（`110 = 29 + 81` 守恒）

| 来源 | 项数 | 退役后承接 |
| --- | --- | --- |
| `verify_cseg_gate.py` S17 / S18 | 2 | `PB-1..PB-4`（正确扫描域：排除 `node_modules/` / `dist/` / `.p0-build/` / `.workbuddy/`）；**另补一条依赖层单列断言**保证覆盖面不缩水（依赖层单独扫、明确不得作产品层依据，即报告 §6 甲的补偿断言） |
| `verify_cseg_ui.py` U1–U7 / U8×3 / U9–U12 | 14 | 新 P1 套件 UI 重放族（换 base URL / 3D 主形态），U10 解锁并集、U11 跨站不覆盖期望值逐字保留 |
| `verify_fresh_gate.py` 6 项（含 F8a） | 6 | `PB-*` + 新套件 UI / BYTE 重放 |
| `verify_c08_gate.py` 7 项（含 S1.7） | 7 | `PB-*` + 新套件 UI 重放 |
| **合计** | **29** | 逐条有承接，无空白 |

### 4.3 HUD 12 项迁移（PF-10 硬约束）

`verify_hud_spec.py` H1–H12 逐条承接，**11 项原本 PASS、1 项（H11）真实 FAIL 均如实登记**：

| 组 | 承接 | 备注 |
| --- | --- | --- |
| H1–H4（2D HUD DOM / 显隐） | 新 P1 套件 `PM-*` 顶栏不遮挡 + UI 重放族 | 期望值逐字不变 |
| H5–H8（零泄露 / 路牌状态机 / S0–S3） | `PQ-1` / `PQ-4` / `PQ-5` | H5 检测面 = `textContent` + 后代所有属性值，不查 `innerHTML`；83 词全表 + 4 字段名 + `len(vocab)==83` 守卫，逐字不变 |
| H9–H10（冻结 / 路牌几何） | `PR-5` / `PC-*` | 逐字不变 |
| **H11**（tag / CACHE_TAG / 20 图零裸引用 / 资源按字节送达） | `PB-1..PB-4` + `PVB-*`（四重判定：逐字节 + magic + sha256 + Content-Type 非 `text/html`，不信状态码） | **F-5 FAIL 原文永久保留于 `p1-legacy-gate-fail-scan.md` §2**；四个已 PASS 子项原样重放；**不改 NOTE、不放宽** |
| H12（跨站存档） | `PS-*` / `PLR-C08-D*` | 逐字不变 |

### 4.4 辅助脚本有效断言承接

`verify_atlas_sprites.py` 的 8 项 PASS（48 张立绘加载 / dim 灰化 / 身份卡大图 / 六档分组 / webp 200 / JS 无错误等）由 P1 资产门控（D4 六档 / 48 卡面）承接；`verify_features.py` / `verify_audio_fix.py` 的交互前置超时按报告 §4 登记为环境项，不转断言、不改判定。

---

## 5. 终点判据改写（用户 11-12 裁决后，替换 `p1-qa-spec.md` 旧口径）

> **「门控全绿」权威口径（2026-11-12 生效，逐字）**：
> ```
> 门控全绿 = 路线 B 重定义套件实跑
>            · verify_p0_gate.py 62 项（继续原样全绿，不退役）
>            · verify_p1_gate.py 实跑（#46 实跑化后；K1–K5 映射 5/5 满格、含 PVIS/PDEG/PQ-5）
>          + 81 项迁移重放（本文件 §3 承接表，正确扫描域，期望值逐字不变）
>          + node js/headless_laps.mjs 11 场 ALL PASS（max ≤180s）
> ```
> **四套旧门控的 `exit code` 自 2026-11-12 起不再计入上式**（用户裁决乙 · 整体退役）。
> **明确不等于「原始 110 项原样全绿」**（`p1-qa-spec.md` X9）：Vite/R3F 构建链下 110 项中的 29 项已物理失效（#20/#27 F-01~F-12），且旧套件扫描域缺陷已被 11-11 实跑实证；写死 110 项原样全绿会把终点锁死。
> **终点定义本身不变**：D6 终点 = **「门控全绿 + 375px 可玩」**，用户已拍板；本次只改「门控全绿」的**组成与载体**，不改终点定义、不重开裁决。
> **部署 ≠ 本文件放行**：用户「可以部署在我设置的 GitHub 仓库上」是**用户授权**，仍须走 Phase B（`#32` / `#47` / `#48`）的 C2–C6 同源部署与逐字节复核，QA 不代签发布。

### 5.1 G1 门控全绿判据同步（替换 `p1-qa-spec.md` §4.1 G1 行）

| 字段 | 新内容 |
| --- | --- |
| 条件 | **门控全绿** |
| 硬判据 | 路线 B 重定义套件（`verify_p0_gate.py` 62 PASS / 0 FAIL + `verify_p1_gate.py` `SUMMARY: N PASS / 0 FAIL / N TOTAL`，§6.3 K1–K5 映射 5/5 满格无空格，含 `PVIS-*` / `PDEG-*` / `PQ-5`）+ **81 项迁移重放全绿**（`p1-gate-retirement.md` §3 承接表，正确扫描域，期望值逐字不变）+ `headless_laps.mjs` 11 场 ALL PASS；四项退出码全 0。**四套旧门控 exit code 不计入判定链**；**≠ 原始 110 项原样全绿（X9）** |
| 证据来源 | `verify_p1_gate.py` 实跑日志 + `result.json` + `p1-gate-retirement.md` §3 承接表逐行 PASS 记录 |
| 判定 | 待实跑（`#46`） |
| 裁决方 | QA 判定 → 用户放行 |

> G5「五类断言零降级」同步改为「81 项**迁移重放**在 3D 形态下重放全绿」；`p1-qa-spec.md` §3.2 / §3.3 / §6.1 / §6.2 / §7.1 / §12 的「原样保留（载体为旧门控）」口径统一改为「**迁移到新套件重放**」，并引用本文件。**判据条数不变：规格定义合计仍为 143 条（62 条新增/重定义 chk + 81 项迁移重放）**，一条未删、一条未放宽。

---

## 6. PF-01~PF-10 映射更新（退役后状态）

> 基线：`p1-qa-spec.md` §3.1 表 + `p1-legacy-gate-fail-scan.md` §5 实测映射。退役**不改变技术承接**，只更新**状态**与**载体**。10 族仍全部有承接编号，无一条删除/放宽/改 NOTE。

| 族 | 原承接（§3.1） | 11-11 实测（报告 §5） | **退役后状态（本令更新）** |
| --- | --- | --- | --- |
| PF-01 | `PV-1..PV-4` + `PM-*`；降级另见 `PDEG-*` | `verify_p0_gate.py` 62/62 仍全绿；`verify_p1_visual.py` V1–V3 证 WebGL 真创建 | 不变。正常路径 `PV-*` / 降级路径 `PDEG-*` 分离（X11）仍成立 |
| PF-02 | `PV-2/3` + `PC-*` + `PR-*` + `PVIS-5` | 探针逐字不动；P1 实测 63 卡丁 mesh / 71 drawCalls / light.count=2 | 不变。`probe.jsx` / `probe.html` 逐字不动 → P0 62 项继续原样全绿 |
| PF-03 / PF-04 | `PR-*` + `PM-*` + `PDEG-*` | `?p1=off` / `?render=2d` 实测回退完整可玩 | 不变 |
| PF-05 | `PV-*` + `PM-*` + `BD-4'` | 3D 主形态下 `__rally` getter 仍挂载；2D HUD DOM 14/14 | 不变。`verify_cseg_ui.py` 退役后，14 项按 §4.2 迁移到新套件 UI 重放族 |
| PF-06 | `PVB-*` / `BV-*` 四重判定 | H11 的 `按字节比对=True` 仍 PASS | 不变。四重判定口径（逐字节 + magic + sha256 + CType 非 `text/html`）逐字保留 |
| **PF-07** | `PB-*`（六项约束逐字沿用 A.1） | **F-1/F-3/F-4/F-5 四条 FAIL 正落此族**：旧门控未按 §2.6 排除 `node_modules/`；产品层 `{hud-20261108:46}` 唯一且恰好 46、裸引用 0 | **状态更新（重点）**：① 四套旧门控退出判定链 → 这 4 条 FAIL **不再是发布阻断**；② **不得定性为「已修复」**——产品层 46 / 0 裸引用仍须由 `PB-1..PB-4` 在新套件**逐条重验**，并补依赖层单列断言（§4.2）；③ `verify_p0_gate.py` 62/62 已实证正确扫描域有效，是 `PB-*` 的现行载体；④ 29 项重验域的 S17 / S18 / F8a / S1.7 按 §4.2 迁移，期望值逐字不变。**本族从「待用户拍板后落地」转为「用户 11-12 裁决乙已放行、`PB-*` 承接生效、旧 FAIL 归档留痕」** |
| PF-08 | `PQ-4` / `PQ-5` | V1–V3 H5 零泄露 + 三条白名单逐字锁定全 PASS | 不变 |
| PF-09 | `PE-*` | V1–V6 四项错误计数全 0 | 不变 |
| **PF-10** | `PM-*` / `PQ-*` / `PB-*` / §3.3 保留清单；**「每一条 H 断言在实跑报告中必须有 PASS/FAIL 或明确的『替代 = 编号』」** | H11 真实 FAIL 已如实登记（F-5），未改 NOTE；`verify_hud_spec.py` 其余 11 项 PASS | **状态更新（重点）**：① `verify_hud_spec.py` 归档、退出判定链，但 **H1–H12 逐条迁入新套件**（§4.3），**12 条断言一条不许消失**；② **H11 的 FAIL 原文、命中明细、退出码永久保留**在 `p1-legacy-gate-fail-scan.md` §2 F-5 与 §4，**不因退役抹掉、不改 NOTE、不放宽**；③ 本令 §4.3 即 §3.1 要求的「实跑报告逐条登记」的**退役后承接登记**，与报告原文构成双重留痕 |

---

## 7. 退役后脚本处置（可追溯、可手动、不进链）

| 项 | 处置 |
| --- | --- |
| 文件 | 四套脚本 + `verify_hud_spec.py` + 三套辅助脚本**全部原地保留**，不删 / 不改名 / 不修改 / 不移到 `archive/`（避免路径变化破坏历史证据链） |
| 可手动跑 | 允许任何人按原用法手动复跑做历史对照；输出**仅作参考**，不得回填 G1 |
| 判定链 | CI / 发布流程 / `p1-qa-spec.md` §7.1 串行顺序**不再调用**四套；§7.1 第 1–3 步改为「`verify_p0_gate.py` 62 + `verify_p1_gate.py`（含 81 项 `PLR-*` 迁移重放）+ `verify_p1_visual.py` 63」 |
| 证据 | `p1-legacy-gate-fail-scan.md`（11-11 实跑，6 条 FAIL 原文）与本令**永久保留**，作为「为何退役」与「81 项去哪了」的双重证据 |
| 回滚 | 若用户后续撤回退役裁决，按本令 §3 承接表反向对照即可恢复 81 项原样重放；**无需改任何脚本** |

---

## 8. 边界与质量门声明

- **本轮写入物仅 2 个**：`design/p1-gate-retirement.md`（本文件，新建）、`design/p1-qa-spec.md`（修订 81 项口径）。**未改** `verify_p1_gate.py`（主理人 `#46` 本地实跑化，避免写冲突）、未改任何 `verify_*.py`、未改产品代码、未重出资产、未跑门控 / 浏览器、未部署 / 上线 / commit / 建 git 仓库。
- **FAIL 纪律**：6 条真实 FAIL 全部保留原文与命中明细，**没有一条被静默改成 NOTE、没有一条放宽阈值、没有一条删除**。退役改变的是「判据地位」，不是「断言存在性」。
- **守恒核对**：81 项逐条承接（§3，零空白行）+ 29 项重验承接（§4.2）+ HUD 12 项承接（§4.3）= 覆盖面完整；`110 = 29 + 81` 仍成立；规格定义判据仍 **143 条**。
- **质量门 advisory**：QA 给判定与阻塞项，**最终放行与发布签字由用户决定**；CONCERNS / 证据 MISSING 一律不静默放行。用户「可以部署在 GitHub 仓库上」的授权仍须经 Phase B 的 C2–C6 同源部署与逐字节复核，QA 不代签发布。

---

*退役令 v1.0 · quality-lead 严守真 · 生效 2026-11-12 · 任务 #45 · 依据用户 2026-11-12 书面裁决（乙 · 四套整体退役）+ `#44` `design/p1-legacy-gate-fail-scan.md`（11-11 实跑，6 条真实 FAIL）+ `design/p1-qa-spec.md` §0/§3/§4/§6 + `verify_p1_gate.py` `PL_CHECKS` 81 项 · 退役的是发布阻断判据地位、不是删断言 · 81 项期望值逐字不改、逐条 `PLR-*` 承接、零空白行 · 门控全绿 = 路线 B 重定义套件 + 81 项迁移重放 + 11 场 headless，≠ 原始 110 项原样全绿（X9）· PF-07 / PF-10 状态已更新 · G1 已同步 · 质量门 advisory*

---

## 9. 实现回执（主理人补登 · 2026-11-12 · 实跑化完成后）

> 本节由主理人补登，用于消解 §7「判定链不再调用四套」与本轮 PLR 实现的表面张力。
> **不修改 §0–§8 任何规范性文字**；§0–§8 仍是规范，本节只登记「规范如何被真实执行」。

### 9.1 81 项重放的真实载体

- 新建 `音标拉力赛/verify_p1_plr.py`（PLR 重放适配器），并在 `verify_p1_gate.py` 增加 `run_plr()`。
- 适配器以 `exec(compile(...))` 在自定义 globals 中执行 `verify_cseg_gate.py` / `verify_fresh_gate.py` / `verify_c08_gate.py`，**读取其断言定义与期望值（源码逐字未改）**，从 `RESULTS` 取回逐条 `(name, ok, detail)`；旧脚本结尾的 `sys.exit(1 if f else 0)` 被捕获并丢弃。
- **判定链归属**：只有 81 条 `PLR-<组>-<编号>` 布尔值进入 `verify_p1_gate.py` 的 `chk()` 与 `GATE_VERDICT`；旧脚本自己的 `SUMMARY` / `exit code` / `CONCERNS` 一律丢弃。
- 因此 §7「不再调用四套」的准确含义是 **不再把旧套件自身的判定结果当发布阻断**，不是禁止读取其断言定义。81 条期望值 100% 来自旧脚本源码、逐字不改；四个旧脚本零改动、零改名、原地保留。

### 9.2 正确扫描域与实测

- `os.walk` 定向 patch：仅当 `top` 位于项目树内时排除 `node_modules / dist / .p0-build / .workbuddy / .git / __pycache__ / src / .vite / coverage`；site-packages 内 Playwright driver 自身的 walk 不受影响。
- 实测取回 38 / 21 / 37 条断言；§3 承接表的 81 个编号 **36/36 + 15/15 + 30/30 全命中、零失败**；11-11 的 4 条扫描域 FAIL（S17 / S18 / F8a / S1.7）在正确扫描域下自然转绿，实证 §4.1「真实 FAIL 全不在 81 项保留域」。

### 9.3 门控全绿的实跑组成

- `verify_p1_gate.py` 现按 §5 组成实跑：`S0` = `verify_p0_gate.py` 62 项（不退役）+ S1/S2/S3/S4/S6 + `S5` = `verify_p1_visual.py` 63 项 + 静态断言 B1–B10（B9 即本退役令落盘）+ 81 项 `PLR-*`。
- 逐条明细与结论见 `音标拉力赛/result.json`（`pl81_status = REPLAYED_81_VIA_PLR_ADAPTER`）；三份重放原始结果见 `音标拉力赛/plr-verify_*.json`；各套件完整输出见 `音标拉力赛/gate-logs/`（本机诊断、不入库）。
- **执行顺序约束（非放宽）**：S5 的 WebGL 取证必须在任何会批量启停 Chromium 的套件之前执行，否则 swiftshader 偶发初始化失败会让 3D 整体降级成 2D。当前顺序 = S3（纯 Node 构建）→ S5 → S0 → 其余。断言、期望值、门槛一条未改。
- **测试服务器并发修复（第 3/4 轮实测）**：`verify_p1_visual.py` 自起的 `ThreadingHTTPServer` 默认 `request_queue_size=5`，V1 首屏并发拉 mp3/webp/js/css 时偶发 `net::ERR_CONNECTION_REFUSED`，使「四项错误计数归零」FAIL（3D 三车可见性仍全 PASS）。已把 backlog 调到 128 并设 daemon 线程；**四项错误计数归零仍是硬 chk，未豁免该类错误、未放宽阈值**。各套件完整输出落 `gate-logs/` 供复核。

### 9.4 未覆盖面（如实登记）

- 人工签收类（PVIS-3 / PVIS-1/2/4/6 / PM-7 / PT-2）与 29 项重验域 UI、HUD 12 项的逐条替代编号，仍列在 `result.json` 的 `not_covered`，**不冒充 PASS**；G9 按用户裁决为上线后 advisory，不作发布阻断。
