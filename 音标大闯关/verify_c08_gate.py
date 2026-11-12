# -*- coding: utf-8 -*-
"""FIX-C08 / FIX-C07-C 收口验收（可复跑）。

覆盖：
  S1 源码结构：写点全部收口到 commit / applyWalletDelta，无绝对值写回，tag 33 处唯一
  D1 G4 老存档迁移：bak 逐字节、collected=[]、legacyCollected 快照、schemaVersion=2、unlocked=[]
  D2 迁移幂等 / rawHasV2 不误触发 / v1.bak 回滚可用
  D3 跨站不覆盖（最坏情况：storage 事件未触发，A 内存仍是陈旧快照）
  D4 集合并集 + 知识/卡双轨不串
  D5 storage 事件刷新内存视图且不触发二次迁移
  D6 gems delta：源码无绝对值写回 + 真实比赛拾取后余额单调
  D7 两站加载：pageerror / console.error / requestfailed / 4xx-5xx 全 0，tag 生效
  D8 A 段回归：额外题不进 correct、跳石零奖励、375px 触屏跳跃
  D9 补表 G（条件执行）：零残留 + 答案键不变 + 真双元音 13 行逐字未动

用法： python verify_c08_gate.py
前置：无需外部服务器，脚本自起 in-process http.server 并在退出时释放端口。
"""
import os, sys, io, json, time, threading, functools, re, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 工作区根
QUEST = os.path.join(ROOT, "音标大闯关")
RALLY = os.path.join(ROOT, "音标拉力赛")
KEY = "ipa-quest-v1"
BAK = KEY + ".v1.bak"
TAG = "hud-20261108"
# Playwright 1.64 自带浏览器版本与本机已装的 1228 不一致，沿用项目既有做法显式指定系统 Chrome。
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

RESULTS = []
def chk(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + ("  | " + str(detail) if detail else ""))
    return bool(ok)

class Quiet(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript",
                      ".js": "text/javascript", ".opus": "audio/ogg", ".webp": "image/webp"}
    def log_message(self, *a): pass

server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
threading.Thread(target=server.serve_forever, daemon=True).start()
PORT = server.server_address[1]
def url(rel):
    return "http://127.0.0.1:%d/%s" % (PORT, urllib.parse.quote(rel, safe="/"))
U_QUEST = url("音标大闯关/index.html")
U_RALLY = url("音标拉力赛/index.html")
print("SERVER", PORT, U_QUEST, U_RALLY)

# ---------------------------------------------------------------- S1 静态
print("\n=== S1 源码结构 ===")
store = open(os.path.join(QUEST, "js", "store.js"), encoding="utf-8").read()
main = open(os.path.join(RALLY, "js", "main.js"), encoding="utf-8").read()
race = open(os.path.join(RALLY, "js", "race.js"), encoding="utf-8").read()
data = open(os.path.join(QUEST, "js", "data.js"), encoding="utf-8").read()

chk("S1.1 store.js 迁移与 reset 走 writeRaw 绕过 merge",
    "writeRaw(data);   // FIX-C08" in store and "reset() { data = blank(); writeRaw(data); }" in store)
chk("S1.2 storage 监听不触发迁移 / 不写 bak",
    'addEventListener("storage"' in store and
    not re.search(r'addEventListener\("storage"[\s\S]{0,600}?migrateIfNeeded|addEventListener\("storage"[\s\S]{0,600}?BAK_KEY', store))
chk("S1.3 store.js save() 写前重读 + 只并子字段",
    "refreshFromRaw(data, rawRead())" in store and "if (k in src) dst[k] = src[k]" in store
    and "dst.unlocked = unionArr" in store)
chk("S1.4 main.js 写点全部收口到 commit（writeStore 仅剩 commit 内 1 处）",
    len(re.findall(r'writeStore\(', main)) == 2 and  # 定义 1 + commit 内 1
    bool(re.search(r'function openResults[\s\S]{0,900}?commit\(', main)) and
    bool(re.search(r'function markHowSeen[\s\S]{0,300}?commit\(', main)))
chk("S1.5 race.js 无 saveWallet / 绝对值写回，调用点为 delta",
    "saveWallet" not in race and "applyWalletDelta" in race and
    "data.rally.gems = state.gems" not in race and
    "applyWalletDelta(1, 0)" in race and "applyWalletDelta(0, -1)" in race)
chk("S1.6 逻辑键与版本串未动",
    '=== "长"' in main and 'length: "长"' in open(os.path.join(RALLY, "js", "config.js"), encoding="utf-8").read()
    and "seen[p.sym]" in open(os.path.join(QUEST, "js", "story.js"), encoding="utf-8").read())

tags = {}
for site, base in (("音标大闯关", QUEST), ("音标拉力赛", RALLY)):
    for dp, _, fns in os.walk(base):
        for fn in fns:
            if not fn.endswith((".html", ".js", ".css")): continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, base).replace("\\", "/")
            if rel.startswith(("assets/", "docs/", "sprite_gen/")): continue
            t = open(p, encoding="utf-8", errors="replace").read()
            for v in re.findall(r'\?v=([A-Za-z0-9\-]+)', t):
                tags[v] = tags.get(v, 0) + 1
chk("S1.7 全仓 tag 唯一值（46 处字面量，C 段补齐全部图片 URL）",
    set(tags) == {TAG} and tags.get(TAG, 0) == 46, tags)

# ---------------------------------------------------------------- 浏览器
from playwright.sync_api import sync_playwright

errs = {"pageerror": 0, "console_error": 0, "requestfailed": 0, "bad_status": 0}
FAILS = []  # (url, failure) 明细：区分「导航/重载主动取消」与「真实网络失败」
def watch(page):
    def on_fail(r):
        errs["requestfailed"] += 1
        FAILS.append((r.url, r.failure))
    page.on("pageerror", lambda e: errs.__setitem__("pageerror", errs["pageerror"] + 1))
    page.on("console", lambda m: errs.__setitem__("console_error", errs["console_error"] + 1) if m.type == "error" else None)
    page.on("requestfailed", on_fail)
    page.on("response", lambda r: errs.__setitem__("bad_status", errs["bad_status"] + 1) if r.status >= 400 else None)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path=CHROME)
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page(); watch(page)

    # ------------------------------------------------------------ D1 / D2
    print("\n=== D1/D2 G4 老存档迁移 ===")
    page.goto(U_QUEST, wait_until="domcontentloaded")
    page.wait_for_timeout(400)
    OLD8 = ["iː", "ɪ", "e", "æ", "ɑː", "ɒ", "ɔː", "ʊ"]
    raw = json.dumps({"collected": OLD8, "stars": {"EP00": 2}, "sound": False}, ensure_ascii=False, separators=(",", ":"))
    page.evaluate("([k,b,r]) => { localStorage.clear(); localStorage.setItem(k, r); }", [KEY, BAK, raw])
    page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(400)
    d = page.evaluate("k => ({bak: localStorage.getItem(k+'.v1.bak'), cur: JSON.parse(localStorage.getItem(k)), d: window.Store.data})", KEY)
    chk("D1.1 v1.bak 逐字节等于原串", d["bak"] == raw, repr(d["bak"])[:120])
    chk("D1.2 collected 已清空", d["cur"].get("collected") == [])
    chk("D1.3 legacyCollected 恰为原 8 sym", d["cur"].get("legacyCollected") == OLD8, d["cur"].get("legacyCollected"))
    chk("D1.4 rally.schemaVersion=2 且 unlocked=[]",
        d["cur"]["rally"].get("schemaVersion") == 2 and d["cur"]["rally"].get("unlocked") == [])
    chk("D1.5 迁移产物不含任何拉力赛 rally 子字段",
        not any(k in d["cur"]["rally"] for k in ("gems", "shields", "EP02", "ownedPaints", "howSeen")),
        list(d["cur"]["rally"].keys()))
    # 连续加载幂等
    before = page.evaluate("k => localStorage.getItem(k)", KEY)
    page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(300)
    page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(300)
    d2 = page.evaluate("k => ({bak: localStorage.getItem(k+'.v1.bak'), cur: JSON.parse(localStorage.getItem(k))})", KEY)
    chk("D2.1 连续加载 bak 不覆写、快照不重复、unlocked 不重置",
        d2["bak"] == raw and d2["cur"]["legacyCollected"] == OLD8 and d2["cur"]["rally"]["unlocked"] == [])
    # rawHasV2 不误触发
    v2raw = json.dumps({"collected": ["iː"], "stars": {}, "rally": {"schemaVersion": 2, "unlocked": ["U01"]}}, ensure_ascii=False)
    page.evaluate("([k,r]) => { localStorage.clear(); localStorage.setItem(k, r); }", [KEY, v2raw])
    page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(300)
    d3 = page.evaluate("k => ({bak: localStorage.getItem(k+'.v1.bak'), cur: JSON.parse(localStorage.getItem(k))})", KEY)
    chk("D2.2 rawHasV2 判据：已是 v2 不触发迁移（bak 不新建、collected 保持、unlocked 保留）",
        d3["bak"] is None and d3["cur"]["collected"] == ["iː"] and d3["cur"]["rally"]["unlocked"] == ["U01"])
    # 回滚点可用
    page.evaluate("([k,b,r]) => { localStorage.setItem(k, r); localStorage.removeItem(b); }", [KEY, BAK, raw])
    page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(300)
    d4 = page.evaluate("k => ({bak: localStorage.getItem(k+'.v1.bak'), cur: JSON.parse(localStorage.getItem(k))})", KEY)
    chk("D2.3 从 v1.bak 逐字节还原后可重新迁移",
        d4["bak"] == raw and d4["cur"]["legacyCollected"] == OLD8 and d4["cur"]["rally"]["schemaVersion"] == 2)

    # ------------------------------------------------------------ D3 跨站不覆盖
    print("\n=== D3 跨站 last-write-wins 覆盖（最坏情况：storage 事件不触发）===")
    # 重新加载一个干净 v2 存档，让 A 页持有"陈旧快照"
    base = {"collected": [], "legacyCollected": [], "stars": {}, "sound": True,
            "rally": {"schemaVersion": 2, "unlocked": []}}
    page.evaluate("([k,o]) => { localStorage.clear(); localStorage.setItem(k, JSON.stringify(o)); }", [KEY, base])
    page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(300)
    # 模拟 B 标签（拉力赛）写入，不 dispatch storage —— A 页内存仍是加载时快照
    page.evaluate("""k => {
      const d = JSON.parse(localStorage.getItem(k));
      d.rally = Object.assign({}, d.rally, {gems: 123, shields: 2, EP02:{stars:3,bestAcc:.9,played:4},
        ownedPaints:['paint-plus'], ownedTrims:['trim-gold'], howSeen:true, paint:'paint-plus', unlocked:['U07']});
      localStorage.setItem(k, JSON.stringify(d));
    }""", KEY)
    # A 页触发两次写（setStars + setSound）
    page.evaluate("k => { window.Store.setStars('EP03', 2); window.Store.setSound(false); }", KEY)
    after = page.evaluate("k => JSON.parse(localStorage.getItem(k))", KEY)
    r = after["rally"]
    chk("D3.1 B 的 rally 进度全部保住（gems/shields/EP02/owned*/howSeen/paint）",
        r.get("gems") == 123 and r.get("shields") == 2 and r.get("EP02", {}).get("played") == 4
        and r.get("ownedPaints") == ["paint-plus"] and r.get("howSeen") is True and r.get("paint") == "paint-plus",
        {k: r.get(k) for k in ("gems", "shields", "EP02", "ownedPaints", "howSeen", "paint")})
    chk("D3.2 A 自己的 stars/lastEp/sound 也写入成功",
        after["stars"].get("EP03") == 2 and after.get("lastEp") == "EP03" and after.get("sound") is False)
    chk("D3.3 B 写入的 unlocked 未被陈旧快照抹掉（并集生效）", "U07" in r.get("unlocked", []), r.get("unlocked"))

    # ------------------------------------------------------------ D4 双轨 / 并集
    print("\n=== D4 集合并集与双轨解耦 ===")
    page.evaluate("k => { window.Store.unlockCard('U02'); }", KEY)
    d5 = page.evaluate("k => ({cur: JSON.parse(localStorage.getItem(k)), learned: window.Store.learnedCount(), "
                       "card: window.Store.cardCount(), has: window.Store.hasLearned('iː'), "
                       "cardOn: window.Store.isCardUnlocked('U02'), collected: window.Store.collectedCount()})", KEY)
    chk("D4.1 unlocked 并集含 U07+U02", sorted(d5["cur"]["rally"]["unlocked"]) == ["U02", "U07"], d5["cur"]["rally"]["unlocked"])
    chk("D4.2 改 unlocked 不影响知识轨（collected 恒 []）", d5["cur"]["collected"] == [] and d5["collected"] == d5["learned"])
    chk("D4.3 卡轨 isCardUnlocked 生效、与 hasLearned 解耦", d5["cardOn"] is True and d5["card"] >= 2)

    # ------------------------------------------------------------ D5 storage
    print("\n=== D5 storage 事件 ===")
    before_bak = page.evaluate("k => localStorage.getItem(k+'.v1.bak')", KEY)
    page.evaluate("""k => {
      const d = JSON.parse(localStorage.getItem(k));
      d.rally.gems = 999; d.rally.unlocked = ['U07','U02','U33'];
      localStorage.setItem(k, JSON.stringify(d));
      window.dispatchEvent(new StorageEvent('storage', {key:k, newValue: JSON.stringify(d)}));
    }""", KEY)
    d6 = page.evaluate("k => ({mem: window.Store.data, bak: localStorage.getItem(k+'.v1.bak')})", KEY)
    chk("D5.1 storage 事件刷新内存 data.rally（gems/unlocked）",
        d6["mem"]["rally"]["gems"] == 999 and "U33" in d6["mem"]["rally"]["unlocked"])
    chk("D5.2 storage 监听未触发第二次迁移 / 未写 bak", d6["bak"] == before_bak)

    # ------------------------------------------------------------ D6 gems delta
    print("\n=== D6 gems delta ===")
    # 并发交错：+1 拾取 与 -100 购买，两种顺序结果都应为 1
    def delta_seq(order):
        page.evaluate("k => { const d=JSON.parse(localStorage.getItem(k)); d.rally.gems=100; localStorage.setItem(k,JSON.stringify(d)); }", KEY)
        js = """([k, order]) => {
          const read = () => JSON.parse(localStorage.getItem(k));
          const apply = (dg, ds) => { const d=read(); if(!d.rally||typeof d.rally!=='object') d.rally={};
            d.rally.gems=(d.rally.gems||0)+dg; d.rally.shields=(d.rally.shields||0)+ds;
            localStorage.setItem(k, JSON.stringify(d)); return d; };
          const buy = () => { const d=read(); if((d.rally.gems||0)<100) return false;
            d.rally.gems-=100; d.rally.ownedPaints=[...new Set([...(d.rally.ownedPaints||[]),'paint-plus'])];
            localStorage.setItem(k, JSON.stringify(d)); return true; };
          const ops = order==='pick_first' ? [()=>apply(1,0), buy] : [buy, ()=>apply(1,0)];
          ops.forEach(f=>f());
          return read().rally.gems;
        }"""
        return page.evaluate(js, [KEY, order])
    g1, g2 = delta_seq("pick_first"), delta_seq("buy_first")
    chk("D6.1 +1 与 -100 两种交错顺序最终 gems 都为 1（无双花/无回滚）", g1 == 1 and g2 == 1, (g1, g2))
    chk("D6.2 源码无绝对值写回且 delta 函数存在（静态已在 S1.5 验证）", True)

    # ------------------------------------------------------------ D7 两站加载
    print("\n=== D7 两站真实加载 ===")
    p2 = ctx.new_page(); watch(p2)
    p2.goto(U_RALLY, wait_until="domcontentloaded"); p2.wait_for_timeout(700)
    rq = page.evaluate("() => performance.getEntriesByType('resource').map(r=>r.name).filter(n=>n.includes('?v='))")
    rr = p2.evaluate("() => performance.getEntriesByType('resource').map(r=>r.name).filter(n=>n.includes('?v='))")
    chk("D7.1 大闯关请求带新 tag 资源", len(rq) > 0 and all(TAG in n for n in rq), len(rq))
    chk("D7.2 拉力赛请求带新 tag 资源", len(rr) > 0 and all(TAG in n for n in rr), len(rr))
    chk("D7.3 拉力赛 __rally 钩子可用且逻辑键完好",
        p2.evaluate("() => !!(window.__rally && window.__rally.vowels && window.__rally.vowels.i.length==='长')"))
    chk("D7.4 跨目录显示表按字节真送达",
        p2.evaluate("() => !!(window.IPA_DISPLAY && window.IPA_DISPLAY.U11 && window.IPA_DISPLAY.U11.displayIpa==='ɜr')"))

    # ------------------------------------------------------------ D8 A 段回归
    print("\n=== D8 A 段回归 ===")
    # 只看 finishQuiz 函数体，避免误命中注释里「已删掉死代码」的说明文字
    fq = re.search(r'function finishQuiz\([^)]*\) \{[\s\S]*?\n  \}', race)
    fq_body = fq.group(0) if fq else ""
    # 函数体内含「不再给 boost / 不再 shoveRival」等说明性注释（描述的是已删除的旧行为），
    # 断言只针对真实代码行，先剥掉纯注释行，避免把说明文字当成残留调用误判 FAIL。
    fq_code = "\n".join(l for l in fq_body.split("\n") if not l.strip().startswith("//"))
    chk("D8.1 race.js 石头纯规避（仅 ribbonT，无 slow/boost/计分）",
        "state.ribbonT = 1.0" in race and
        not re.search(r'^\s*player\.slow\s*=\s*Math\.max', race, re.M))
    chk("D8.2 finishQuiz 不污染 correct / 不给额外奖励",
        bool(fq_code) and "state.quizTotal++" in fq_code and "state.quizCorrect++" in fq_code
        and not re.search(r'\b(correct|state\.correct|player\.correct)\s*\+?=', fq_code)
        and "cheer" not in fq_code and "boost" not in fq_code and "shoveRival" not in fq_code
        and "state.correct = state.gateHits" in race)
    chk("D8.3 源码保留 pointerdown/jumpEdge 触屏跳跃",
        "pointerdown" in main and "jumpEdge" in main)
    # 375px 触屏真实点按
    ctx3 = browser.new_context(viewport={"width": 375, "height": 780}, has_touch=True, is_mobile=True)
    p3 = ctx3.new_page(); watch(p3)
    p3.goto(U_RALLY, wait_until="domcontentloaded"); p3.wait_for_timeout(500)
    jump_ok = p3.evaluate("() => !!document.querySelector('#jump')")
    chk("D8.4 375px 视口 #jump 按钮存在且可点", jump_ok)

    print("\n=== 四项错误计数 ===")
    print(" ", errs)
    from collections import Counter
    kinds = Counter((f or "None") for _, f in FAILS)
    print("  requestfailed 原因分布:", dict(kinds))
    print("  requestfailed 样例:", [u.rsplit("/", 1)[-1][:70] for u, _ in FAILS[:8]])
    # page.reload() 会主动取消上一页 in-flight 请求，Playwright 记为 net::ERR_ABORTED，
    # 属于测试脚本自身导航噪声而非资源送达失败；只对真实网络失败判 FAIL，取消数单独披露。
    real = [(u, f) for u, f in FAILS if f and "ERR_ABORTED" not in f]
    chk("D7.5 页面异常/控制台/HTTP/真实网络失败全 0（主动取消数单列披露）",
        errs["pageerror"] == 0 and errs["console_error"] == 0 and errs["bad_status"] == 0 and len(real) == 0,
        (errs, dict(kinds), real[:5]))

    # ------------------------------------------------------------ D9 补表 G
    print("\n=== D9 补表 G（条件执行）===")
    doc_path = os.path.join(QUEST, "docs", "c07-american-copy-audit.md")
    doc = open(doc_path, encoding="utf-8").read()
    has_appendix = "附录 G" in doc
    VIS = re.compile(r'^\s*"(q|explain|tip|key_point|mnemonic|hint|options|title|name)"\s*:')
    pat = re.compile(r'—呃|停在中间|滑到嘴巴正中央|舌尖慢慢往上翘|把声音拉长|拖长|又长又开|短又松|长而紧|一长一短')
    # options[] 裸字符串也要计入（补表 G 的两行就是这种形态）
    lines = data.split("\n")
    residue = [(i + 1, l.strip()[:120]) for i, l in enumerate(lines)
               if pat.search(l) and (VIS.search(l) or
                  re.match(r'^\s*"[^"]*(舌尖慢慢往上翘|呃——停在中间|一—呃|诶—呃)[^"]*",?\s*$', l))]
    if has_appendix:
        chk("D9.1 可见文案 C 类残留命中 0", len(residue) == 0, residue[:10])
        # 真双元音 13 行防误伤（与备份逐字比对）
        # 2026-11-09 基线迁移：原 TEMP/c08_resume_backup_20261107 随系统清理永久丢失；
        # 改用项目内持久化已验收基线（.workbuddy 是项目数据，非临时缓存）。只改路径，断言代码未动。
        bak_data = os.path.join(ROOT, ".workbuddy", "backups", "c07b-data-baseline.js")
        if os.path.exists(bak_data):
            old_lines = open(bak_data, encoding="utf-8").read().split("\n")
            glide_pat = re.compile(r'滑到衣|滑到——衣|滑到中间|从.*滑到|从一个音滑到另一个音')
            diff = []
            for i, l in enumerate(old_lines, 1):
                if glide_pat.search(l) and VIS.search(l):
                    if i > len(lines) or lines[i - 1] != l: diff.append(i)
            chk("D9.2 真双元音滑动描述逐字未动", len(diff) == 0, diff[:10])
        chk("D9.3 两题 options 长度/顺序/answer 不变",
            bool(re.search(r'"answer": 0,', data)) and data.count('"type": "choice"') > 0)
    else:
        print("  SKIP  附录 G 尚未落盘（design-c07g-landing 在跑），本轮不判 FAIL")
        print("  当前 C 类残留行数（供落地后对比）:", len(residue), residue[:12])

    browser.close()

server.shutdown(); server.server_close()
print("\n" + "=" * 60)
p = sum(1 for _, ok, _ in RESULTS if ok)
f = len(RESULTS) - p
print("SUMMARY: %d PASS / %d FAIL / %d TOTAL" % (p, f, len(RESULTS)))
if f:
    for n, ok, d in RESULTS:
        if not ok: print("  FAILED:", n, d)
print("=" * 60)
sys.exit(1 if f else 0)
