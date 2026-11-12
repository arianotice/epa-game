# 音标拉力赛 · 2D HUD 落地最终回归 QA 计划（#5）

> **文档状态**：`#5-PRE` 并行准备产物（`quality-lead` 严守真）。**本文件与 `verify_hud_spec.py` 在 #4 落地前只做静态自检，不执行任何门控。**
> **唯一规格依据**：`design/hud-ux-spec.md` 第 5 节 H1–H12（逐条期望值照抄，不自编）；显隐口径以第 7 节 Q1–Q4 锁定结论 + 主理人「quiz 口径」补充裁决为准；影响面以 `design/hud-impl-plan.md` §D / §F 为准。
> **质量门性质**：advisory（建议性）。我给 PASS / CONCERNS / FAIL 判定与阻塞项，**最终放行由用户决定**；发布签字等高影响动作须人工审批。
> **本阶段边界**：只读源码 + 只新建本文件与 `verify_hud_spec.py`；未改 `js/` / `index.html` / `css/` / 图片 / 四套既有验收脚本 / `data.js` / `ipa-display.js` / 上游管线；未跑门控、未部署、未上线、未 commit。

---

## 0. 前置条件（开跑前逐条确认，缺一不跑）

| # | 前置 | 核对方法 | 未满足时 |
| --- | --- | --- | --- |
| P0 | `#4` 已落地并回传实现报告；`index.html` 已含 `#minimap` / `#minimap-c` / `#minimap-lap` | `rg -n 'minimap' index.html css/game.css js/main.js js/render.js` | 不跑，待主理人通知 |
| P1 | 缓存串已统一 bump 到 **`hud-20261108`** | 静态直方图（见 §5.1）唯一值 = `hud-20261108`，46 处 | 退回 #4 |
| P2 | `config.js:7 CACHE_TAG` = `hud-20261108`；四套脚本 `TAG` 常量 + `verify_cseg_ui.py:26` 死常量 + `headless_laps.mjs:19` 同步 | 逐文件 `rg -n 'cseg-20261107\|hud-20261108'` | 退回 #4（**QA 不代改既有脚本**） |
| P3 | 系统 Chrome 可用：`C:\Program Files\Google\Chrome\Application\chrome.exe` | `Test-Path` / `ls`；本机 Playwright 1.64.1 缺 `chromium-1248`，**所有浏览器脚本必须显式传 `executable_path`** | 修环境，不降级为默认 chromium |
| P4 | Python 3 + `playwright.sync_api`、Node 可用 | 一条 `python -c "import playwright"` / `node -v` | 修环境 |
| P5 | 工作目录干净（未部署、未上线、未 commit），回滚点可用 | 见 §9 | 先恢复再跑 |

> **P2 的易错点**：`hud-impl-plan.md` §D.2(2) 与 §H 明确列出 **6 处** TAG/CACHE_TAG 字符串 + `verify_cseg_gate.py:24` 的 `S18` 判据（判据内含 tag 字面量，**漏改必 FAIL**）。`config.js` 的 `CACHE_TAG` 驱动 `${CACHE_TAG}` 模板，S17 正则抓不到 `${…}`、S18 白名单放行，**改它不改变 46 计数**；这是最易误判的一处。

---

## 1. 最终回归执行顺序与命令清单

**顺序理由**：秒级静态门控先跑（最快抓 tag / 裸引用 / 源码级回归）→ 浏览器门控四套（抓跨站回归）→ `headless_laps.mjs`（最慢 ≈175 s，放中后段，避免早段失败白等）→ 最后 HUD 专项脚本（依赖 DOM 就绪，自带 readiness check）。**任一步 FAIL 即停，先定位再决定是否继续，不带着红灯往下跑。**

工作目录：`C:/Users/86135/WorkBuddy/英语音标播客`

```bash
# ---- 步骤 0：静态自检（不启动浏览器，可先做） ----
cd "C:/Users/86135/WorkBuddy/英语音标播客/音标拉力赛"
python -m py_compile verify_hud_spec.py                 # 仅语法，不执行
python -c "import re,pathlib,collections; \
p=pathlib.Path('.'); \
c=collections.Counter(); \
[c.update(re.findall(r'\?v=([A-Za-z0-9\-]+)', f.read_text(encoding='utf-8'))) \
 for f in list(p.rglob('*.html'))+list(p.rglob('*.js'))+list(p.rglob('*.css'))+ \
          list((p.parent/'音标大闯关').rglob('*.html'))+list((p.parent/'音标大闯关').rglob('*.js'))+ \
          list((p.parent/'音标大闯关').rglob('*.css'))]; \
print('TAGS:', dict(c))"                              # 期望 {'hud-20261108': 46}

# ---- 步骤 1：静态源码门控（38 项） ----
python verify_cseg_gate.py

# ---- 步骤 2：拉力赛 UI 浏览器门控（14 项） ----
python verify_cseg_ui.py

# ---- 步骤 3：姊妹站浏览器门控（21 项 + 37 项） ----
cd "../音标大闯关"
python verify_fresh_gate.py
python verify_c08_gate.py

# ---- 步骤 4：两圈实跑（11 场，无浏览器，最慢 ≈174.57 s ≤ 180 s） ----
cd "../音标拉力赛"
node js/headless_laps.mjs
# 等价写法：cd js && node headless_laps.mjs
# 注：mjs 内为 await import('./config.js?v=TAG')，相对模块自身解析，两种 cwd 均可

# ---- 步骤 5：HUD 专项验收（H1–H12，新脚本，自起 HTTP server） ----
python verify_hud_spec.py
```

> **不要**在 `音标拉力赛/` 根之外运行 `verify_hud_spec.py`：脚本用 `HERE = dirname(__file__)` 推导两站根目录，从别处调用仍可工作，但统一在根目录运行便于日志归档。
> **不要**并行跑多个浏览器门控：四套脚本各自自起 HTTP server / 占用端口，串行执行避免 `requestfailed` 假阳性。

---

## 2. 每项 PASS 判据（逐项表）

| 步骤 | 命令 | 基线 TOTAL | PASS 判据 | 退出码 |
| --- | --- | --- | --- | --- |
| 1 | `python verify_cseg_gate.py` | 38 | `SUMMARY: 38 PASS / 0 FAIL / 38 TOTAL`；且 `S17 tag 唯一恰好 46 处`、`S18 图片 URL 零裸引用`、`S13 "g.lap === lapNow" 字面量锁` 三条逐项 PASS | `0` |
| 2 | `python verify_cseg_ui.py` | 14 | `SUMMARY: 14 PASS / 0 FAIL / 14 TOTAL`；`U1/U12` 错误计数项 PASS | `0` |
| 3a | `python verify_fresh_gate.py` | 21 | `SUMMARY: 21 PASS / 0 FAIL / 21 TOTAL`（脚本带 `CONCERNS/NOTE` 计数，NOTE 须逐条过眼并在报告登记） | `0` |
| 3b | `python verify_c08_gate.py` | 37 | `SUMMARY: 37 PASS / 0 FAIL / 37 TOTAL` | `0` |
| 4 | `node js/headless_laps.mjs` | 11 场 | 11 场 **ALL PASS**；每场两圈完整、`finishTime ≤ 180 s`；门判定 / 跨圈复位无异常 | `0` |
| 5 | `python verify_hud_spec.py` | **12**（H1–H12；H6 为 if/else 双分支字面量，运行期只走一条） | `SUMMARY: 12 PASS / 0 FAIL / 12 TOTAL`；`HUD_NOT_READY` / `NOT_READY_OR_ENV_ERROR` **不得出现**；`CONCERNS/NOTE` 逐条过眼 | `0` |

**合计基线**：四套门控 **110 项**（38+14+21+37）+ 11 场两圈实跑 + HUD 专项 12 项。

**汇总判据**：
- **PASS**：以上 6 项命令全部 `退出码 0` 且 SUMMARY 全绿；四项错误计数按 §3 归零；§5 资源按字节校验通过；§6 人工清单无「阻塞」项；§7 DPR 复核通过。
- **CONCERNS**：全绿但存在 NOTE（外链字体环境失败、`__rally.minimapRect()` / `minimapModel()` 未暴露的降级 NOTE、375×780 人工项仅「建议优化」级），需用户在放行时显式接受。
- **FAIL**：任一命令非零退出、任一 SUMMARY 含 FAIL、四项错误计数中 `pageerror` / `console_error` / `bad_status` / 同源真实网络失败任一 ≠ 0、HUD 路径出现写盘、答案词面/IPA 出现在小地图、quiz 冻结数值变化、tag 不唯一或 ≠46、20 个图片 URL 出现裸引用。

> **TOTAL 变化的处置**：四套既有脚本由 #4 统一 bump，`chk` 数量原则上不变；若运行期 TOTAL 与基线不符，**先查是否 #4 顺带增删了断言**，登记差异后再判 PASS，不得默认放行。

---

## 3. 四项错误计数归零要求（含 `ERR_ABORTED` 严格分类）

四套门控 + 新脚本统一监听 `pageerror` / `console` (type=error) / `requestfailed` / `response.status >= 400`。**历史坑**：Playwright `reload()` / 页面导航会主动取消在途请求，产生 `net::ERR_ABORTED`，此前曾被误判为 FAIL。

| 类别 | 判定 | 是否计入硬失败 | 要求 |
| --- | --- | --- | --- |
| `pageerror` | 页面未捕获异常 | **是** | `= 0` |
| `console_error` | `console.error` 文本 | **是** | `= 0` |
| `bad_status` | HTTP `status >= 400` | **是** | `= 0` |
| `requestfailed` — `net::ERR_ABORTED` | reload / 导航主动取消 | **否**，单列披露 | 允许 > 0；必须打印去重 URL 样例 |
| `requestfailed` — 同源（`127.0.0.1` / `localhost`）非 `ERR_ABORTED` | **真实网络失败** | **是** | `= 0` |
| `requestfailed` — 外链（`fonts.googleapis.com` / `fonts.gstatic.com` 等）非 `ERR_ABORTED` | 环境相关 | **否**，NOTE 披露 | 打印明细；资源送达另由 §5 字节/内容比对覆盖，**不信状态码** |

**PASS 硬条件**（`verify_hud_spec.py` H12 已按此实现）：

```
errs_strict_ok = (pageerror == 0 and console_error == 0
                  and bad_status == 0 and len(REAL) == 0)
fields_ok      = (rally_before == rally_after)      # unlocked / maps / EP02 逐字段
zero_write_ok  = (frozen step(300) 的 setItem 增量 == 0)
```

汇总必须**单列披露**：`requestfailed 明细：总计 N | ERR_ABORTED(主动取消,不计失败) N | 同源真实失败 N | 外链环境失败 N`，并打印 `ERR_ABORTED` 样例 URL、`同源真实失败明细`、`console.error 文本`。**禁止**把 `ERR_ABORTED` 混进 FAIL 计数，也**禁止**把它静默吞掉不披露。

附加：HUD 路径**零写盘**——hook `Storage.prototype.setItem` 后 `step(300)` 增量必须为 0；`rally.unlocked` / `maps` / `EP02` 开赛前后逐字段相等（防两站共享单键 `ipa-quest-v1` 的跨站存档竞态）。

---

## 4. H1–H12 断言映射（复核表，判据照抄 `hud-ux-spec.md` §5）

| # | 断言 | 关键期望值 | 脚本内 `chk` |
| --- | --- | --- | --- |
| H1 | DOM 存在性 + 属性 | `#minimap` / `#minimap-c` / `#minimap-lap` 存在；`aria-hidden="true"`；`pointerEvents==='none'`；底板 `backgroundColor` alpha ≥ .82；`z-index:5`；DOM 顺序在 `#hud` 之后 | `H1 #minimap / #minimap-c / #minimap-lap 存在且属性符合规格` |
| H2 | 显隐矩阵 | `title/teach/results → hidden=true`；`countdown/racing/paused → false`；**`quiz → false`（显示但冻结）** 且冻结前后 `karts[0].odo` / `simTime` 相等；**`boardOpen \|\| shopOpen`（mode 仍 `racing`）→ `true`** | `H2 显隐矩阵逐阶段断言…` |
| H3 | 375px 不溢出 | `375×667`：`left≥0 && right≤375 && top≥0 && bottom<667 && width≤112.5`；`320×568` 同样不溢出；PC `width≤160` | `H3 375×667 / 320×568 / PC 下 #minimap 不溢出且宽度收敛` |
| H4 | 位置不重叠（双视口） | 与 `#hud .hud-row > *`（`#btn-mute`/`#btn-pause`/`#combo`/`#progress`）、`#banner`、`#route-map`（可见时）两两不相交；窄屏 `banner.top ≥ mm.bottom + 12`（含 0.5px 亚像素容差）；`#quiz` 按 **z-index 层叠**（`.panel` z=8 > `#minimap` z=5），**不做几何不相交断言** | `H4 小地图与 #hud 子项/#banner/#route-map 不相交 + 窄屏 banner 下移 + gutter 生效 + quiz 层叠` |
| H5 | 小地图不含答案文本 | 4 门的 `spoken.word` / `other.word` / `left.word` / `right.word` / 各 `ipa` / `displayIpa` 均不出现在 `mm.textContent` + `mm.innerHTML` + 后代 `alt`/`aria-label`/`data-*`；禁用属性 `data-lane/data-correct/data-side/data-answer` | `H5 小地图 textContent/innerHTML/后代属性均不含答案词面/IPA/答案域名/禁用 data-*` |
| H6 | 数据接口无答案键 | `JSON.stringify(minimapModel())` 不含 `spoken/correctLateral/left/right/pairKey/qType/options/displayIpa/answer/correct` 作为**键名**（用 `Object.keys` 递归，避免误伤值）；`nextGate` 键集合精确 `={id,lap,line,distance,secondsTo}` | `H6 minimapModel 数据接口无答案键 + nextGate 键集合精确相等`（未暴露则按规格报 FAIL + NOTE） |
| H7 | 路牌在阈值内出现 | `odo = g.line − (D_preview+50)` → `#signs.hidden=true`；`dist = D_preview−20` 且 `!g.played` → S1 出现、两牌零字母零 `/`；`g.played=true` → S2 含 `word` 与 `/ipa/`。**`D_preview` = follow 1482 / listen 1620 里程**（`span·L + 0.5·preview·speed`，名义常量，不读 `speedNow()`） | `H7 路牌 S0 隐藏 / S1 在 D_preview 内出现 / S2 播音后出现（follow 1482 · listen 1620）` |
| H8 | 对称、无指向性 | S1 两牌 `className` 均不含 `is-long/is-short`、零文本；S2 `rect.width` 相等（±1px）、`opacity` 相等、`className` 不含 `ok/bad/correct/answer`、分别含 `g.left.word` / `g.right.word` 且互异；`#signs.innerHTML` 不含「正确」「答案」及 `correctLateral` 提示 | `H8 S1 零文本且双侧中性对称 / S2 两侧同帧同尺寸且含各自 word 与 /ipa/、无指向性` |
| H9 | quiz 冻结 | `#signs.hidden===true`；`simTime` / `karts[0].odo` 冻结前后及 `step(60)` 后不变；`setItem` 零写入；答完回 `racing` 后 `#signs.hidden` 恢复 `false` 且内容与进 quiz 前一致 | `H9 quiz 冻结数值不变 / #signs.hidden=true / setItem 零写入 / 回 racing 路牌无缝重现` |
| H10 | 两圈不重复/不串位 | `lineT=[0.24,0.68,1.24,1.68]`（容差 `1e-9`）；两圈同 `commitT` 门 `line` 差 = `L`（±1）；`minimapModel().nextGate.lap===1`；`lap===1` 时 `#signs` 子节点 ≤2；第 2 圈门置 `played=true` 后正常出牌；`signKey` 以 `gate.id` 开头含 phase（`data-opened` 不可观测时改以行为断言为主，NOTE 披露） | `H10 两圈同 commitT 不重复（lineT/line 差=L/lap=1/≤2 牌/signKey/第 2 圈正常出牌）` |
| H11 | 缓存串唯一 + 零裸引用 | 全站 `?v=` 字面量集合 = `{hud-20261108}` 且恰好 **46 处**；`config.js CACHE_TAG` 同步；`<img src>` / `<link href>` / `<script src>` / ESM `import` 零裸引用；**20 个图片 URL** 全部带 tag（含 2 处动态拼接型 `level.js:49` / `story.js:307`）；`window.IPA_DISPLAY.U11.displayIpa === 'ɜr'`；本地 HTTP server 资源按字节送达 | `H11 tag 唯一且恰好 46 处 / CACHE_TAG 同步 / 20 个图片 URL 零裸引用 / 资源按字节送达` |
| H12 | 零回归 + 零写盘 | 四项错误计数严格归零（`ERR_ABORTED` 单列）；`step(300)` 期间 `setItem` 增量 0；`rally.unlocked/maps/EP02` 开赛前后逐字段相等 | `H12 四项错误计数归零（ERR_ABORTED 单列） / HUD 路径零写盘 / rally 字段开赛前后不变` |

**单向铁律（贯穿 H5/H6/H8）**：`correctLateral` / `spoken` 只许出现在 `audio.playWord()` 与 `judge()`；HUD 的 `innerHTML` / `fillText` / `data-*` / `alt` / `aria-label` 一律不得接触。`sym` 是英式稳定键，**禁止**用 `displayIpa` 作键。

**优雅报错契约**：`verify_hud_spec.py` 在 `window.__rally` / `#minimap` / `#minimap-c` 任一缺失时打印「**HUD 元素未就绪，请先完成 #4**」+ 检测明细 + 当前 `?v=` 字面量，输出 `SUMMARY: 0 PASS / 0 FAIL / 0 TOTAL | HUD_NOT_READY`，`sys.exit(2)`；顶层 `try/except` 兜底输出 `NOT_READY_OR_ENV_ERROR` 并退 2，**不抛裸 traceback**。`exit(2)` 属「前置未满足」，不计为回归 FAIL。

---

## 5. 资源按字节 / 内容校验方法（防 Caddy 兜底 200 陷阱）

> **陷阱**：线上 Caddy 对不存在的路径可能兜底返回 `index.html` 且 `HTTP 200`。**只信状态码会把「资源没送到」误判为「送达」**。本轮不部署不上线，但发布后复核必须按下述口径；`verify_hud_spec.py` 的 H11 已内置**本地 HTTP server** 的按字节比对，可先在本地把方法跑通。

### 5.1 静态层（本地，秒级）

1. **tag 直方图**：扫两站 `.html` / `.js` / `.css`，`re.findall(r'\?v=([A-Za-z0-9\-]+)', text)` → `Counter`。PASS：`{'hud-20261108': 46}`（唯一值、恰好 46）。基线分布（`hud-impl-plan.md` §D.2）：大闯关 `index.html` 17 / `atlas.js` 6 / `level.js` 1 / `map.js` 3 / `story.js` 2；拉力赛 `index.html` 7 / `main.js` 7 / `race.js` 2 / `render.js` 1 = **46**。
2. **图片 URL 零裸引用**：抽 20 个含 `/` 的 `.webp` / `.png` 字面量，逐个确认带 `?v=hud-20261108` 或 `${CACHE_TAG}`；另查 2 处动态拼接型（`level.js:49`、`story.js:307`）段内也带 tag。
3. **`CACHE_TAG` 同步**：`rg -n 'CACHE_TAG' js/config.js` 值为 `hud-20261108`；`rg -n 'cseg-20261107'` 全仓应为 **0 命中**（含 6 处 TAG/CACHE_TAG 常量与 `headless_laps.mjs:19`）。
4. **`IPA_DISPLAY` 哨兵**：`window.IPA_DISPLAY.U11.displayIpa === 'ɜr'`，确认 `ipa-display.js` 未被误改。

### 5.2 运行时按字节比对（本地 HTTP server，`verify_hud_spec.py` H11 已实现）

脚本自起 `ThreadingHTTPServer`（`Quiet` handler 补 `.mjs → text/javascript`、`.opus → audio/ogg`、`.mp3 → audio/mpeg`、`.webp → image/webp` 的 MIME），对每个待测资源：

```python
url = "http://127.0.0.1:<port>/<relpath>?v=hud-20261108"
with urllib.request.urlopen(url) as r:
    body = r.read()
    ctype = r.headers.get("Content-Type")
disk = open(os.path.join(ROOT, relpath), "rb").read()
ok = (body == disk) and ("text/html" not in ctype)   # 逐字节 + Content-Type 双重
```

PASS：`body == disk`（长度与内容一致）、`Content-Type` 与后缀匹配（`.webp→image/webp`、`.js/.mjs→text/javascript`、`.css→text/css`、`.mp3→audio/mpeg`、`.opus→audio/ogg`）、**且不是 `text/html`**。

### 5.3 发布后复核预案（本阶段不执行）

1. **先探兜底**：请求一个确定不存在的路径，例如 `GET /assets/img/__qa_missing_9f3a.webp?v=hud-20261108`。若返回 `200` 且 body 以 `<!doctype html` / `<html` 开头 → **确认存在兜底**，此后所有资源**状态码一律不可信**，只按 5.2 的字节 / 内容口径判定。
2. **逐资源校验**：对 20 个图片 URL + 全部 `?v=` 引用的 `.js` / `.css` / `.mjs` / 音频，逐个比对
   - `Content-Type` 非 `text/html`；
   - **文件 magic**：WebP `RIFF????WEBP`、PNG `\x89PNG\r\n\x1a\n`、MP3 `ID3` 或 `0xFF 0xFB`、JS/CSS 为可打印 UTF-8 且不含 `<html`；
   - 字节长度与本地磁盘一致；`sha256(body) == sha256(disk)`。
3. **缓存生效验证**：带 `?v=hud-20261108` 请求一次，再改查询串为旧值请求一次，确认服务端返回的是**当前**文件而非缓存旧副本；浏览器侧 Hard Reload + 清空 Cache Storage 后重跑 §1 步骤 5。
4. **两站交叉**：姊妹站 `音标大闯关` 的 `atlas.js` / `level.js` / `map.js` / `story.js` 与拉力赛的 `main.js` / `race.js` / `render.js` 都要覆盖，防只 bump 了一站。

---

## 6. 375×780 人工过眼清单（自动脚本不覆盖此尺寸，必须人工）

> **口径区分**：`verify_hud_spec.py` 自动几何断言用 **375×667** / **320×568** / **1280×800**（规格 §2.1.3 / H3）；**375×780** 是人工过眼尺寸（更高的现代手机视口，验证纵向余量与 `#banner` 下移）。两者不可互相替代。

| # | 检查项 | 判据 | 级别 |
| --- | --- | --- | --- |
| V1 | 右上角小地图位置与完整度 | 375×780 下 `right:10px` / `top:calc(8px + safe-area)`，宽 ≤ `min(96px,26vw)`、高 ≤ `min(64px,17vw)`；四角无裁切、不与状态栏/刘海冲突 | 阻塞 |
| V2 | 半透明底板与可读性 | `background: var(--card)`（羊皮纸 `rgba(255,250,240,.94)`）+ `2px solid var(--line)` + `--shadow`；环线 / 三车点 / `1/2` 圈数在动态赛道背景上对比清晰 | 阻塞 |
| V3 | 与 HUD 不重叠 | `#btn-mute`(42px) / `#btn-pause`(≥72px) / `#combo` / `#progress` 均不与小地图相交；`#hud` gutter（`padding-right:120px`）生效，`.hud-row` 多换 1 行但文字不挤压变形、不截断 | 阻塞 |
| V4 | `#banner` 下移 | 窄屏 `banner.top ≥ mm.bottom + 12px`；顶部提示（如「第 1/2 圈 · 听对 N」）完整显示、不被小地图遮住 | 阻塞 |
| V5 | **`#route-map` 互斥** | 标题页只显示 `#route-map`（176×118，四区大地图入口），**不出现**比赛小地图；进入比赛后只显示小地图，`#route-map` 消失；**不存在三元素叠压**，`#route-map` 未删未移 | 阻塞 |
| V6 | `pointer-events:none` 穿透 | 手指点击小地图覆盖区域应穿透到下层，**不**误触 / 不吞掉 `#btn-pause` / `#btn-mute`；小地图本身零交互（无缩放 / 拖拽 / 点击反馈） | 阻塞 |
| V7 | 状态机显隐 | `countdown`（静态三车+`1/2`）/ `racing` / `paused`（冻结保持）/ `quiz`（显示但冻结）依次过眼；`title` / `teach` / `results` 小地图隐藏 | 阻塞 |
| V8 | **quiz 冻结口径** | `#quiz` 面板（z=8）盖住区域但小地图仍可见且**数值静止**；`#signs` **完全隐藏**（无 IPA 题 `#quiz-prompt` 与两侧词牌同屏）；答题回 `racing` 后路牌按 `played` 无缝重现、无闪烁、不重播 `open` 动画 | 阻塞 |
| V9 | board / shop 打开 | 从 `racing` 打开排行榜 / 商店（`mode` 仍为 `racing`）→ 小地图与路牌同时隐藏；关闭后按当前 `dist` 恢复，不因冻结期未 `step` 而错位 | 阻塞 |
| V10 | 路牌 S1 / S2 | S1 中性几何箭头 `↖ ↗` 成对同形同色、**零文本零 IPA**、不上 `is-long/is-short`；S2 两侧词牌同帧同尺寸、内容互异、**无单侧高亮 / 勾选 / 变色 / 「正确答案」**；路牌飘入右上角时被小地图矩形避让裁剪（`visibility:hidden`） | 阻塞 |
| V11 | 两圈切换 | 跨圈时圈数 `1/2 → 2/2`，`nextGate` 不串圈，路牌不重复 / 不漏显 / 不残留 S1 内容；同一相对 `commitT`（0.24 / 0.68）两圈位置一致 | 阻塞 |
| V12 | 答案不泄露（目视） | 小地图与 HUD 目视无单词 / IPA / 例词 / 左右指向性提示；唯一线索来自听觉 `spoken.word` | 阻塞 |
| V13 | 触摸操作区 | `#touch`（z=7）左/右转向不受小地图影响；底部按钮可点、无遮挡 | 阻塞 |
| V14 | 结果页 / 暂停页 | `#panel-results` / `#panel-pause` 打开时显隐符合矩阵；无小地图残影 / 残帧 | 建议 |
| V15 | `prefers-reduced-motion` | 系统开启减少动效后，小地图无脉动 / 进度弧补间，路牌 `open` 动画降级为直接显示，两侧仍同帧 | 建议 |
| V16 | 横屏短高（375×320）与 320×568 | `--mm-w/-h` 用 `min(px,vw)` 收敛；`mm.bottom < innerHeight`；不与 `#count-num`（120px 字）纵向重叠 | 建议 |
| V17 | 视觉一致性 | 配色沿用 `--paper #f6ead0` / `--ink #4a3520` / `--gold #c9a227` / `--gold-deep #a0720a`，底板沿用 `--card`；与 3D 视觉方向稿的右上角「同位置角色切换」一致 | 建议 |

> 任一项「阻塞」未通过 → 质量门判 **FAIL**，回传 #4 修后重跑 §1。人工过眼结果（通过/不通过/截图路径）登记到 §10 判定记录。

---

## 7. DPR 2 / 3 复核

规格 §2.1.3：内嵌 canvas 按 `dpr = min(2, devicePixelRatio)` 设位图尺寸，绘制前 `ctx.setTransform(dpr,0,0,dpr,0,0)`，与 `main.js:731-737 resize()` 同源。**DPR 3 会被 clamp 到 2**，这是设计意图，不是缺陷。

复核方法（在 `verify_hud_spec.py` 的浏览器 context 之外另开，或人工 DevTools 覆盖）：

```python
for dsf in (1, 2, 3):
    c = browser.new_context(viewport={"width": 375, "height": 780},
                            device_scale_factor=dsf)
    p = c.new_page(); boot(p); into_racing(p)
    d = p.evaluate("""() => {
      const m = document.querySelector('#minimap-c');
      const r = m.getBoundingClientRect();
      const ctx = m.getContext('2d');
      const px = ctx.getImageData(0, 0, m.width, m.height).data;
      let nonBlank = 0; for (let i=3;i<px.length;i+=4) if (px[i]) nonBlank++;
      return {cssW:r.width, cssH:r.height, bmpW:m.width, bmpH:m.height,
              transform: ctx.getTransform().toString(), nonBlank};
    }""")
    # PASS: bmpW == cssW * min(2, dsf)（±1）, bmpH 同理；nonBlank > 0；transform 含该 dpr
    c.close()
```

| # | 检查项 | 判据 |
| --- | --- | --- |
| D1 | 位图尺寸 | `#minimap-c.width/height` == CSS 尺寸 × `min(2, DPR)`（±1px）；DPR 2 与 DPR 3 的位图尺寸**相同**（clamp 生效） |
| D2 | 绘制变换 | `ctx.getTransform()` 为 `dpr` 缩放；绘制坐标仍用 CSS 像素，不出现双倍偏移 / 裁切 |
| D3 | 实际有内容 | `getImageData` 非全透明像素数 > 0（确认不是空白 canvas） |
| D4 | 目视清晰度 | DPR 2 / 3 下环线、车点、`1/2` 文字不模糊、不锯齿、无 1px 断线；与 DPR 1 相比更锐利而非更糊 |
| D5 | 布局不随 DPR 漂移 | `getBoundingClientRect()` 的 CSS 尺寸 / 位置在 1 / 2 / 3 下一致；不触发 resize 抖动或重复绘制 |
| D6 | 截图留证 | 各 DPR 各存一张 375×780 截图到回归证据目录 |

---

## 8. 旧断言失效预判与处置建议（#4 改动引起）

> **总原则**：本阶段 QA **一个字都不改四套既有验收脚本**；若出现下表失效，先判「#4 偏离收尾方案」还是「旧断言需合理演进」，**由主理人裁决**后由对应成员修改，QA 只重跑复核。

| # | 可能失效的旧断言 | 触发条件 | 预判 | 处置建议 |
| --- | --- | --- | --- | --- |
| O1 | `verify_cseg_gate.py:100-113` **S17** `set(tag_counts)=={TAG} and count(TAG)==46`；`verify_fresh_gate.py:162-174` **F8a**；`verify_c08_gate.py:80-92` **S1.7** | #4 新建 `js/hud.js` / `js/minimap.js` 模块并 `import "...?v=NEW"`，或新增 `<script src>` / `<img>` / `<link>` → 计数 47 / 48 | **三处同时 FAIL** | 收尾方案（Q1/Q3：不新建模块、不加 `<src>`，`#minimap` 为无 src 容器）净 +0，**不应触发**。若确需新增：由主理人裁决同步把三处 `== 46` 与描述文案改成新值，且 S18 检查新文件；QA 不改脚本 |
| O2 | `verify_cseg_gate.py` **S18**（图片 URL 零裸引用，判据内含 tag 字面量） | #4 bump 了 46 处却**漏改 S18 判据**里的 `cseg-20261107` | **必 FAIL** | `hud-impl-plan.md` §H 第 4 步点名：`verify_cseg_gate.py:24` 的 `TAG` + S18 判据必须同批改。回退 #4 补齐 |
| O3 | `verify_cseg_gate.py:89` **S13**（以字面量 `"g.lap === lapNow"` 锁死 `visibleGates` 过滤） | #4 改写 `main.js:969-971` 的渲染 / 小地图 lap 过滤表达式 | 源码级 FAIL | 新 HUD 逻辑一律按 `g.lap === lapNow` 消费（§2.2.5 硬约束 3）；若因格式化换行导致字面量不匹配，主理人裁决是保持表达式还是更新断言 |
| O4 | `verify_cseg_gate.py:66-69` **S4/S5**（`player.odo >= g.line` / `before < upcoming.line`） | #4 误改 `race.js` 门判定 / 复活 C 段已弃用相对圈坐标 | 不应触发（#4 明确不动 `race.js` 判定） | 出现即视为实现越界，回退 #4；不得复活 `wrapDelta/hasPassed/crossed/nextLine/commitMark` |
| O5 | `verify_cseg_ui.py` **U 系列显隐 / `#signs` 相关断言**（14 项） | #4 把 `syncSigns()` 改造成 S0–S3 状态机、Q2 增 quiz 隐藏路牌分支；旧 U 断言若假设 `quiz` 仍显示路牌 / `#signs` 恒为 2 个 `.sign` | 可能 FAIL | 以 Q2/Q3 锁定结论为准，**不放松新 HUD 断言去迁就旧 U**；由主理人裁决更新旧 U 断言的期望值（#4 或 engineering-lead 改），QA 重跑 |
| O6 | `verify_fresh_gate.py` **F11c / F11d**、**F8b / F9b**；`verify_c08_gate.py` **D7.1 / D7.2**（tag / 图片 URL / 四项错误全 0） | tag 未跨站同步、或新增 `#minimap` canvas 抛 `console.error` / 资源 404 | 可能 FAIL | 先按 §5.1 确认 9 个文件 46 处全部 bump；再按 §3 看错误计数明细，区分 `ERR_ABORTED` 与真实 404 |
| O7 | `verify_cseg_ui.py` **U1/U12**、`verify_fresh_gate.py` **F11d** 的 `requestfailed` 计数 | reload 产生 `net::ERR_ABORTED` | 历史误判坑 | 四套已按 `ERR_ABORTED` 豁免修好；新脚本按 §3 单列披露。若仍误判，隔离该测试并登记 flaky，**不污染 CI 信号** |
| O8 | `headless_laps.mjs:19` `const TAG` | 未同步为 `hud-20261108` | **功能上不会 FAIL**（`.mjs` 不被扫；Node 对本地 `?v=` 不敏感） | 口径统一建议同步；若 #4 改了 `TUNING` / `DIFFICULTY` 数值（本轮**禁止**）才会影响 11 场结果，那时视为越界 |
| O9 | `render.js` 主画布 `drawMinimap()` 相关断言（若既有脚本有） | Q1=A 把小地图**迁移**到 DOM 内嵌 canvas | 可能 FAIL | `hud-impl-plan.md` §D 未记录针对 `drawMinimap` 的既有断言；若出现，主理人裁决「保留主画布绘制」还是「更新断言」，并补 H1/H4 的 DOM 化断言 |
| O10 | `index.html` DOM 顺序 / 子节点数量类断言 | 新增 `#minimap` 插在 `#hud` 之后 | 可能 FAIL | Q1 明确要求此顺序；以规格为准更新旧断言，QA 不改 |
| O11 | 375px 几何类旧断言 | `#hud { padding-right: var(--mm-right-gutter) }` 收窄 content box（可用宽 351→243px）、`#banner` 窄屏下移 | 可能 FAIL | R2 已判定「`.hud-row` 多换 1 行可接受」；由主理人裁决更新旧断言坐标容差，不回退 gutter |
| O12 | Q4 遗留项相关 | #4 **顺手**统一了 `placeLaneSign` 的 `t`/`odo` 0.02·L 偏差 | 会移动所有既有路牌 → 路牌投影位置类断言 FAIL | Q4 锁定「本轮不改」。出现即视为越界，回退；若用户后续决定修，须 **QA 补一条路牌投影位置回归断言** |

---

## 9. 回滚路径与方法

- **回滚点**：`C:/Users/86135/AppData/Local/Temp/hud_backup_20261108/`（`#3` 阶段建立的 #4 改动前干净基线）。
- **内容**：13 个文件 + `manifest.txt`；`hud-impl-plan.md` §F 收尾复核记录 `FILES=13 / TOTAL_BYTES=214840 / SOURCE_FILES_UNMODIFIED=YES`。覆盖：拉力赛 `js/config.js`、`js/main.js`、`js/race.js`、`js/render.js`、`index.html`、`css/game.css`；两站 `index.html`；`音标大闯关/js/store.js`；四套验收脚本；附加 `js/headless_laps.mjs`。
- **触发条件**：① HUD 专项判 FAIL 且定位为实现缺陷、窗口内无法修；② 四套门控任一出现回归 FAIL 且无法快速定位；③ 资源送达错发（Caddy 兜底 / tag 漏 bump）导致线上资源不对；④ 用户要求撤回本轮 2D HUD。
- **方法**（Git Bash / PowerShell，按 manifest 相对路径 copy 回源根同名路径）：

```bash
# Git Bash（示例，逐文件按 manifest 执行）
BK="/c/Users/86135/AppData/Local/Temp/hud_backup_20261108"
cp -f "$BK/音标拉力赛/js/main.js" "音标拉力赛/js/main.js"
# ... 其余 12 个文件同理
find "$BK" -type f -name manifest.txt -exec cat {} \;   # 复核 sha256 前 16 位
```

```powershell
# PowerShell 等价
$BK = "C:\Users\86135\AppData\Local\Temp\hud_backup_20261108"
Copy-Item -Force "$BK\音标拉力赛\js\main.js" "音标拉力赛\js\main.js"
# 副本可能带只读属性 → 按需清除：
Get-ChildItem "音标拉力赛" -Recurse | Where-Object { $_.IsReadOnly } | ForEach-Object { $_.IsReadOnly = $false }
```

- **复核**：按 `manifest.txt` 的 **sha256 前 16 位**逐文件比对，确认与基线条目一致。
- **回滚后的验证口径（重要）**：回滚会把缓存串还原为 `cseg-20261107`，此时 `verify_hud_spec.py` 的 `TAG = "hud-20261108"` 与 readiness check 必然失败，属**预期**——回滚后**不再跑 HUD 专项**，改为只重跑四套门控确认回到旧基线全绿（110 项）。
- **本 QA 计划的两个交付文件不在回滚范围**：`verify_hud_spec.py` 与 `design/hud-qa-plan.md` 为 #5-PRE 新增、不改产品代码；若要完全撤回，直接删除这两个文件即可（**需用户审批**）。

---

## 10. 判定记录表（#4 落地后由 QA 填写）

| 项 | 结果 | SUMMARY / 证据 | 备注 |
| --- | --- | --- | --- |
| P0–P5 前置 | ☐ 通过 ☐ 未通过 |  |  |
| 步骤 1 `verify_cseg_gate.py` | ☐ PASS ☐ FAIL | `___ PASS / ___ FAIL / ___ TOTAL` |  |
| 步骤 2 `verify_cseg_ui.py` | ☐ PASS ☐ FAIL |  |  |
| 步骤 3a `verify_fresh_gate.py` | ☐ PASS ☐ FAIL | NOTE 数 ___ |  |
| 步骤 3b `verify_c08_gate.py` | ☐ PASS ☐ FAIL |  |  |
| 步骤 4 `headless_laps.mjs` | ☐ PASS ☐ FAIL | 最慢 ___ s |  |
| 步骤 5 `verify_hud_spec.py` | ☐ PASS ☐ FAIL | `___ PASS / ___ FAIL / ___ TOTAL` \| NOTE ___ |  |
| §3 四项错误计数 | ☐ 归零 | pageerror__ console__ bad_status__ REAL__ ABORTED__ EXTERNAL__ |  |
| §5 资源按字节校验 | ☐ 通过 | tag 直方图 / 20 URL / magic / sha256 |  |
| §6 375×780 人工过眼 | ☐ 通过 | V1–V13 阻塞项全过；V14–V17 建议项 ___ |  |
| §7 DPR 2/3 复核 | ☐ 通过 | 截图路径 ___ |  |
| **质量门判定** | ☐ PASS ☐ CONCERNS ☐ FAIL |  | advisory，最终放行由用户决定 |

---

## 11. CONCERNS / 风险登记

| # | 风险 | 影响 | 缓解 / 处置 |
| --- | --- | --- | --- |
| **C1** | **#4 的 DOM id 与规格不一致时断言如何定位** | H1 readiness check 只认 `#minimap` / `#minimap-c` / `#minimap-lap`；若 #4 用了别的 id / 把 canvas 换成 `<svg>`，脚本会走 `HUD_NOT_READY` 优雅退出而非给出精确断言失败 | ① 脚本已打印检测明细（`rally/mm/mmc/mmlap` 布尔 + 当前 `?v=` 字面量），可据此立即定位；② `minimapRect()` 未暴露时**降级用 `getBoundingClientRect()`** 兜底（H1/H4 不受阻）；③ **以规格 §2.1.3 / Q1 为准回传 #4 改名**，QA 不改产品代码、不擅自放宽断言；④ 若主理人裁决保留 #4 命名，则由主理人指定改脚本常量（属 #5 范畴，另行授权） |
| **C2** | **quiz 冻结口径若实现跑偏** | 若 #4 实现成「quiz 时小地图也隐藏」或「`#signs` 冻结保持而非隐藏」，H2 / H9 会硬 FAIL；若 `frame()` 仍在 quiz 推进 `simTime` / `karts[0].odo`，H9 数值断言 FAIL | ① **唯一口径 = 主理人补充裁决**：`quiz → mm.hidden === false` 且冻结前后 `karts[0].odo` / `simTime` 相等；`#signs.hidden === true`；`boardOpen‖shopOpen`（mode 仍 racing）→ `mm.hidden === true`；`title/teach/results → true`；`countdown/racing/paused → false`；② 显隐必须由 `visible = mode∈{countdown,racing,paused,quiz} && !boardOpen && !shopOpen && !!race` **显式控制**，不得依赖 `minimap: mode!=="title"`（R5）；③ **不放松断言迁就实现**，回传 #4 按 Q2 改造 `syncSigns()` 隐藏分支 + `frame()` 冻结；④ 复测 `step(60)` 后仍相等、回 racing 路牌无缝重现 |
| **C3** | **tag 计数若因新增 script 而变化** | `S17` / `F8a` / `S1.7` 三处 `==46` 会**同时 FAIL**；`S18` 判据漏改也会 FAIL | ① 收尾方案（Q1/Q3：不新建模块、不加 `<script src>` / `<img>` / `<link>`，`#minimap` 无 src）净 +0，**46 保持**；② 开跑前先做 §5.1 直方图自检，异常立即定位到具体文件；③ 若确需新增 `?v=` 字面量，由主理人裁决同步改三处 `==46` + 描述文案 + S18 新文件检查，**QA 本阶段绝不改既有验收脚本**；④ 注意 `config.js CACHE_TAG` 改动**不影响** 46 计数（S17 正则抓不到 `${…}`） |
| C4 | `minimapModel()` / `minimapData` 未暴露 | H6 按规格报 FAIL；H10 的 `nextGate.lap===1` 无法取数 | 脚本已做探测 + NOTE 降级（H10 加 `(not key10 or key_ok)` 保底，H6 保留硬 FAIL 以守规格）；处置：#4 按 §1.2 挂只读 getter 或暴露 `view.minimapData`，由主理人裁决 |
| C5 | `signKey` / `data-opened` 载体不可观测 | H10 的「signKey 以 gate.id 开头含 phase」可能误杀 | 已改为 `data-opened` 为空时输出 NOTE 并**以行为断言为主**（`lineT` 容差 `1e-9`、`line` 差 = L、`lap===1`、≤2 牌、第 2 圈正常出牌）；不放宽行为断言 |
| C6 | S1 中性路牌若移除 `.sign` class | 按 `querySelectorAll('.sign')` 统计块数会得 0 → H7/H8 假 FAIL | `Q.signs()` 已改用 `#signs.children.length` 统计，并保留 `signClassCount` 作诊断字段 |
| C7 | 375×780 未纳入自动几何断言 | 自动脚本只覆盖 375×667 / 320×568 / 1280×800；780 高度的纵向余量、`#banner` 下移只能人工 | §6 人工清单 V1–V17 明确列出，判为「阻塞」项须全过才放行；建议后续把 375×780 加入自动 context |
| C8 | Caddy 兜底 200 陷阱 | 只信状态码会把资源未送达误判为送达 | §5.3 发布后预案：先探不存在路径 → 再逐资源按字节 / magic / sha256 校验；本轮不部署不上线 |
| C9 | Playwright 1.64.1 缺 `chromium-1248` | 默认 `chromium.launch()` 必失败 | 四套既有脚本 + `verify_hud_spec.py` 全部显式 `executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe"`；若 Chrome 路径变更，由主理人统一裁决后同批改 |
| C10 | 两站共享 `ipa-quest-v1` 写盘竞态 | HUD 改动若误写 localStorage，会与姊妹站存档互相覆盖 | H9 / H12 hook `Storage.prototype.setItem` 计数，`step(300)` 增量必须为 0；`unlocked/maps/EP02` 开赛前后逐字段相等 |
| C11 | rAF 在断言间「偷跑」导致 flaky | 仿真被墙钟推进，冻结类断言偶发 FAIL | 脚本注入 `window.__qa` 夹具并置 `R._stepping = true` 抑制真实 rAF，全部用 `window.__rally.step(n)` 显式驱动；若仍 flaky，**隔离该用例单独重跑并登记**，不污染 CI 信号、不直接改期望值 |
| C12 | `headless_laps.mjs` ≈175 s 超时 / 环境波动 | 步骤 4 可能被误判超时 | 基线最慢 `174.57 s ≤ 180 s`；单独串行跑，不与浏览器门控并行；超时先查环境负载，不直接放宽 `finishTime` 上限 |
| C13 | Q4 遗留项 `placeLaneSign` 的 `t`/`odo` 差 `0.02·L`（≈385 里程） | 本轮**不修**；若 #4 顺手修了会移动所有既有路牌 | 实现报告须声明「未修」；若后续决定修，QA 补一条**路牌投影位置回归断言**（O12） |
| C14 | 质量门为 advisory | 我给判定，放行权在用户 | 报告只写 PASS / CONCERNS / FAIL 与阻塞项，不代替用户签字；发布签字须人工审批 |

---

## 12. Handoff 与待命

- 本文件 + `verify_hud_spec.py` 为 `#5-PRE` 全部交付物；两者在 #4 落地前**只做静态自检**（`py_compile` / AST / tag 直方图），**未执行任何门控、未跑最终回归**。
- **任务 `#5` 不标记 completed**——最终回归尚未跑。`#4` 落地后由主理人另行通知，按 §1 顺序执行并填写 §10 判定记录表。
- 所有产出经主理人中转；QA 不与其他成员直接 SendMessage。
- 不部署、不上线、不 commit。

---

*QA 计划结束 · 规格依据 `hud-ux-spec.md` §5 H1–H12 / §7 Q1–Q4 · 缓存串 `hud-20261108` · 回滚点 `C:/Users/86135/AppData/Local/Temp/hud_backup_20261108/` · 等待 #4 落地后执行*
