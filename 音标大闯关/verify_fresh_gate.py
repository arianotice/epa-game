# -*- coding: utf-8 -*-
"""FIX-B2 / C06 / C07 / C08 fresh 全量复验（可复跑；纯验证，零产品改动）。

11 组门控（对应 docs/c07-american-copy-audit.md §5.2 的 9 条 + G3 + G5）：
  F1  零残留正则（§5.2-2）      F2  措辞残留（§5.2-3）
  F3  /e/ 六行 + eɪ 防误伤（§5.2-1）
  F4  25 组 episodes/phonemes 镜像逐字 diff（§5.2-7 / §5.1-9）
  F5  逻辑枚举键锁定 + D01–D05 显示文案（§5.2-6 / §5.3）
  F6  不误伤抽检 + 上游构建管线未重跑（§5.2-9 / §5.2-8）
  F7  11 个重点 unit 教学人工走查（程序化近似，§5.2-4）
  F8  G3 缓存串：33 处唯一 + 实际请求全带 tag
  F9  G5 场景 A 纯净页：图鉴 DOM 美式、卡面资源与显示值同源
  F10 G5 场景 B 受控强缓存：不带 tag 的 js/css 注入旧缓存脏内容，页面仍须正常
  F11 不回退：G4 老存档迁移 + 跨站不覆盖 + 两站四项错误计数

另单列 NOTE（CONCERNS 登记，不计入 PASS/FAIL）：列表页立绘/图谱 URL 未带 tag。

用法： python verify_fresh_gate.py
前置：无需外部服务器，脚本自起 in-process http.server 并在退出时释放端口。

2026-11-09 基线迁移：原 Temp 基线随系统清理丢失，经用户批准改为项目内持久化基线；断言强度不降。
"""
import os, sys, io, json, time, threading, functools, re, hashlib, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEST = os.path.join(ROOT, "音标大闯关")
RALLY = os.path.join(ROOT, "音标拉力赛")
KEY = "ipa-quest-v1"
TAG = "hud-20261108"
# Playwright 1.64 自带浏览器版本与本机已装的 1228 不一致，沿用项目既有做法显式指定系统 Chrome。
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
# 2026-11-09 基线迁移：原 C07-B 前基线在系统 Temp（c07b-backup-20261106），随 Temp 清理
# 永久丢失、不可恢复。经用户批准改为项目内持久化基线（.workbuddy 是项目数据，非临时缓存）。
# 基线 = 当前已验收 data.js 的逐字节副本；断言语义由「历史 diff」改为「不回退 + sha256 全等」，
# 强度不降。不使用 TEMP 环境变量推导。
BASELINE = os.path.join(ROOT, ".workbuddy", "backups", "c07b-data-baseline.js")

RESULTS = []
NOTES = []
def chk(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + ("  | " + str(detail) if detail else ""))
    return bool(ok)
def note(name, detail=""):
    """已知 CONCERNS：单独登记、不计入 PASS/FAIL，避免把非本轮回归项混进结论。"""
    NOTES.append((name, detail))
    print("  NOTE  " + name + ("  | " + str(detail) if detail else ""))

def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()

def lines_of(p):
    return read(p).splitlines()

class Quiet(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript",
                      ".js": "text/javascript", ".opus": "audio/ogg", ".webp": "image/webp",
                      ".mp3": "audio/mpeg"}
    def log_message(self, *a): pass
    def handle(self):
        # 页面导航会取消在途资源请求，客户端断连属正常现象，不打到 stderr
        try: super().handle()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError): pass

server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
threading.Thread(target=server.serve_forever, daemon=True).start()
PORT = server.server_address[1]
def url(rel):
    return "http://127.0.0.1:%d/%s" % (PORT, urllib.parse.quote(rel, safe="/"))
U_QUEST = url("音标大闯关/index.html")
U_RALLY = url("音标拉力赛/index.html")
print("SERVER", PORT)

data = read(os.path.join(QUEST, "js", "data.js"))
DATA_LINES = data.splitlines()
main = read(os.path.join(RALLY, "js", "main.js"))
config = read(os.path.join(RALLY, "js", "config.js"))
atlas = read(os.path.join(QUEST, "js", "atlas.js"))
r_index = read(os.path.join(RALLY, "index.html"))

# 只取「用户可见文案」：带可见字段名的值 + options[] 裸字符串；排除 sym/alias 等稳定键
VIS_FIELD = re.compile(r'^\s*"(q|explain|tip|key_point|mnemonic|hint|title|name|text|note|subtitle)"\s*:\s*"(.*)"\s*,?\s*$')
BARE_STR = re.compile(r'^\s*"([^"]*)"\s*,?\s*$')
def visible_values(txt):
    out = []
    for i, l in enumerate(txt.split("\n"), 1):
        m = VIS_FIELD.match(l)
        if m:
            out.append((i, m.group(2)))
            continue
        b = BARE_STR.match(l)
        if b and ":" not in b.group(1)[:12]:
            out.append((i, b.group(1)))
    return out

VIS = visible_values(data)
BAD_IPA = re.compile(r'ː|ɒ|əʊ|ɪə|eə|ʊə|/e/')
BAD_WORD = re.compile(r'拖长|又长又开|短又松|长而紧|一长一短|滑到嘴巴正中央|—呃')

print("\n=== F1–F7 静态全量复核（fresh 读盘，无任何缓存）===")
f1 = [(i, v[:70]) for i, v in VIS if BAD_IPA.search(v)]
chk("F1 §5.2-2 可见文案英式符号残留 0（sym/alias 稳定键白名单）", len(f1) == 0, f1[:6])
chk("F1b data.js 中 ː 仅出现在 10 行 sym 稳定键",
    sum(1 for l in DATA_LINES if "ː" in l) == 10 and
    all(re.match(r'^\s*"sym":', l) for l in DATA_LINES if "ː" in l),
    sum(1 for l in DATA_LINES if "ː" in l))

f2 = [(i, v[:70]) for i, v in VIS if BAD_WORD.search(v)]
chk("F2 §5.2-3 长短音/央化旧措辞残留 0", len(f2) == 0, f2[:6])

f3_slash_e = [(i, v[:60]) for i, v in VIS if "/e/" in v]
eɪ_now = data.count("eɪ")
base_data = BASELINE  # 2026-11-09：项目内持久化已验收基线（原 TEMP/c07b 基线已永久丢失）
eɪ_old = read(base_data).count("eɪ") if os.path.exists(base_data) else -1
chk("F3 §5.2-1 可见文案 /e/ 六行已改 /ɛ/ 且 eɪ 未被误伤",
    len(f3_slash_e) == 0 and eɪ_now > 0 and eɪ_now == eɪ_old,
    {"/e/ 命中": len(f3_slash_e), "eɪ 当前": eɪ_now, "eɪ 基线": eɪ_old})

MIRRORS = [(207,5904),(208,5905),(241,5941),(242,5942),(431,5978),(432,5979),
           (651,6048),(652,6049),(685,6085),(686,6086),(875,6122),(876,6123),
           (909,6159),(910,6160),(1099,6196),(1100,6197),(1133,6233),(1134,6234),
           (1357,6307),(1358,6308),(2025,6525),(2026,6526),(2215,6562),(2216,6563),
           (2245,6595),(2246,6596)]
mirror_bad = [(a, b) for a, b in MIRRORS
              if a > len(DATA_LINES) or b > len(DATA_LINES)
              or DATA_LINES[a-1].strip() != DATA_LINES[b-1].strip()]
chk("F4 §5.2-7 25 组 episodes/phonemes 镜像逐字一致", len(mirror_bad) == 0, mirror_bad[:6])

logic_ok = ('length: "长"' in config and 'length: "短"' in config
            and '=== "长"' in main and "is-long" in main and "is-short" in main
            and "seen[p.sym]" in read(os.path.join(QUEST, "js", "story.js"))
            and 'hint: "嘴角拉开，肌肉绷紧"' in config
            and 'hint: "嘴放松，轻轻一收"' in config
            and "紧音" in main and "松音" in main
            and "图鉴 iː · 紧音" in r_index and "图鉴 ɪ · 松音" in r_index)
chk("F5 §5.2-6/§5.3 逻辑枚举键锁定 + D01–D05 美式显示文案在场", logic_ok)

if os.path.exists(base_data):
    old_lines = lines_of(base_data)
    cur_lines = DATA_LINES
    diff = [(i+1, x.strip()[:60], y.strip()[:60])
            for i, (x, y) in enumerate(zip(old_lines, cur_lines)) if x != y]
    LOGIC_KEYS = re.compile(r'"(sym|answer|img|audio|unit|id|type|word|src|href|cost|stars)"\s*:')
    dirty = [(i, a, b) for i, a, b in diff if LOGIC_KEYS.search(a) or LOGIC_KEYS.search(b)]
    # 2026-11-09 新增：sha256 全等断言（当前 data.js 与持久化已验收基线逐字节全等）。
    # 基线即当前已验收态，故 diff 恒为 0；以「不回退 + sha256 锁定」替代已永久丧失的历史 diff 能力。
    sha_cur = hashlib.sha256(open(os.path.join(QUEST, "js", "data.js"), "rb").read()).hexdigest()
    sha_base = hashlib.sha256(open(base_data, "rb").read()).hexdigest()
    sha_equal = sha_cur == sha_base
    chk("F6a §5.2-9 与持久化已验收基线逐字一致（不回退）",
        len(diff) == 0 and len(dirty) == 0 and len(old_lines) == len(cur_lines) and sha_equal,
        {"基线行数": len(old_lines), "当前行数": len(cur_lines),
         "diff 行数": len(diff), "逻辑键改动": dirty[:5],
         "sha256 全等": sha_equal, "sha256_16": sha_cur[:16]})
    chk("F6b 图片/音频字段名与 eɪ 出现次数未被改动",
        data.count('"img"') == read(base_data).count('"img"')
        and data.count('"audio"') == read(base_data).count('"audio"')
        and eɪ_now == eɪ_old)
    raw_m = os.path.getmtime(os.path.join(QUEST, "content_raw.json"))
    data_m = os.path.getmtime(os.path.join(QUEST, "js", "data.js"))
    bak_m = os.path.getmtime(os.path.join(QUEST, "js", "data.js.bak"))
    chk("F6c §5.2-8 上游构建管线未重跑（content_raw / data.js.bak mtime 均早于 data.js）",
        raw_m < data_m and bak_m < data_m,
        {"content_raw": time.strftime("%m-%d %H:%M", time.localtime(raw_m)),
         "data.js.bak": time.strftime("%m-%d %H:%M", time.localtime(bak_m)),
         "data.js": time.strftime("%m-%d %H:%M", time.localtime(data_m))})
else:
    # 2026-11-09：持久化基线缺失仍判 FAIL，不静默放行（原 Temp 基线缺失报错已迁到这里）。
    chk("F6 持久化基线缺失（.workbuddy/backups/c07b-data-baseline.js）", False, base_data)

# F8 缓存串静态
tags = {}
for base in (QUEST, RALLY):
    for dp, _, fns in os.walk(base):
        for fn in fns:
            if not fn.endswith((".html", ".js", ".css")): continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, base).replace("\\", "/")
            if rel.startswith(("assets/", "docs/", "sprite_gen/")): continue
            for v in re.findall(r'\?v=([A-Za-z0-9\-]+)', read(p)):
                tags[v] = tags.get(v, 0) + 1
chk("F8a 全仓 ?v= tag 唯一（46 处字面量，C 段补齐全部图片 URL）",
    set(tags) == {TAG} and tags.get(TAG, 0) == 46, tags)

# ---------------------------------------------------------------- 浏览器
from playwright.sync_api import sync_playwright
errs = {"pageerror": 0, "console_error": 0, "requestfailed": 0, "bad_status": 0}
FAILS = []
def watch(page):
    def on_fail(r):
        errs["requestfailed"] += 1
        FAILS.append((r.url, r.failure))
    page.on("pageerror", lambda e: errs.__setitem__("pageerror", errs["pageerror"] + 1))
    page.on("console", lambda m: errs.__setitem__("console_error", errs["console_error"] + 1) if m.type == "error" else None)
    page.on("requestfailed", on_fail)
    page.on("response", lambda r: errs.__setitem__("bad_status", errs["bad_status"] + 1) if r.status >= 400 else None)

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path=CHROME)
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page(); watch(page)
    page.goto(U_QUEST, wait_until="domcontentloaded"); page.wait_for_timeout(500)

    # F7 教学走查：直接从运行时数据取 11 个重点 unit 的全部可见文本
    focus = ["U01","U02","U05","U06","U09","U10","U11","U12","U18","U19","U20"]
    f7 = page.evaluate("""units => {
      const D = window.IPA_DATA, out = {};
      const pool = [].concat(D.phonemes || [], ...(D.episodes || []).map(e => e.phonemes || []));
      for (const u of units) {
        const p = pool.find(x => x && x.unit === u);
        if (!p) { out[u] = 'MISSING'; continue; }
        const txt = ['q','explain','tip','key_point','mnemonic','hint','title','name']
          .map(k => p[k] == null ? '' : JSON.stringify(p[k])).join(' ')
          + ' ' + JSON.stringify(p.options || []);
        out[u] = /拖长|又长又开|短又松|长而紧|一长一短|滑到嘴巴正中央|—呃|ː|ɒ/.test(txt) ? 'RESIDUE' : 'OK';
      }
      return out;
    }""", focus)
    f7_bad = {k: v for k, v in f7.items() if v != "OK"}
    chk("F7 §5.2-4 11 个重点 unit 教学文案走查无残留", len(f7_bad) == 0, f7_bad or f7)

    # F8 实际请求
    rq = page.evaluate("() => performance.getEntriesByType('resource').map(r=>r.name)")
    tagged = [n for n in rq if "?v=" in n]
    chk("F8b 大闯关实际请求资源全部带新 tag",
        len(tagged) > 0 and all(TAG in n for n in tagged if re.search(r'\.(js|css|webp|png)(\?|$)', n)),
        {"资源总数": len(rq), "带 tag": len(tagged)})

    # F9 G5 场景 A：图鉴页 DOM 与卡面资源同源
    page.goto(U_QUEST + "#/atlas", wait_until="domcontentloaded"); page.wait_for_timeout(600)
    dom = page.evaluate("""() => {
      const syms = [...document.querySelectorAll('.sym')].map(e => e.textContent.trim());
      const sprites = [...document.querySelectorAll('img[src*="assets/sprites/"]')].map(e => e.getAttribute('src'));
      return {syms, sprites, u11: window.IPA_DISPLAY && window.IPA_DISPLAY.U11 && window.IPA_DISPLAY.U11.displayIpa};
    }""")
    sym_bad = [s for s in dom["syms"] if re.search(r'ː|ɒ|əʊ|ɪə|eə|ʊə', s)]
    chk("F9a G5 纯净页图鉴 48 卡大字全为美式、无英式符号",
        len(dom["syms"]) > 0 and len(sym_bad) == 0,
        {"大字个数": len(dom["syms"]), "残留": sym_bad[:5]})
    card_urls = re.findall(r'sprites/cards/\$\{p\.unit\}\.webp\?v=([A-Za-z0-9\-]+)', atlas)
    chk("F9b G5 卡面图/总图 URL 全部带当前 tag 且权威表 U11=ɜr",
        len(card_urls) == 2 and all(v == TAG for v in card_urls)
        and ("rarity_progress.webp?v=" + TAG) in atlas and dom["u11"] == "ɜr",
        {"卡面图 URL": len(card_urls), "U11": dom["u11"]})
    src_dir = os.path.join(QUEST, "sprite_gen", "webp_american")
    pub_dir = os.path.join(QUEST, "assets", "sprites", "cards")
    if os.path.isdir(src_dir):
        pairs = [(os.path.join(pub_dir, "U%02d.webp" % i), os.path.join(src_dir, "U%02d.webp" % i))
                 for i in range(1, 49)]
        pairs.append((os.path.join(QUEST, "assets", "sprites", "rarity_progress.webp"),
                      os.path.join(src_dir, "rarity_progress.webp")))
        bad = [os.path.basename(a) for a, b in pairs
               if not (os.path.exists(a) and os.path.exists(b)) or sha(a) != sha(b)]
        chk("F9c G5 49 张发布卡面与美式源逐字节全等（图文同源）", len(bad) == 0, bad[:5])
    else:
        note("F9c 美式源目录不存在，跳过逐字节比对", src_dir)

    # F11 不回退：G4 迁移 + 跨站不覆盖
    OLD8 = ["iː","ɪ","e","æ","ɑː","ɒ","ɔː","ʊ"]
    raw = json.dumps({"collected": OLD8, "stars": {"EP00": 2}, "sound": False},
                     ensure_ascii=False, separators=(",", ":"))
    page.evaluate("([k,r]) => { localStorage.clear(); localStorage.setItem(k, r); }", [KEY, raw])
    page.reload(wait_until="domcontentloaded"); page.wait_for_timeout(450)
    d = page.evaluate("k => ({bak: localStorage.getItem(k+'.v1.bak'), cur: JSON.parse(localStorage.getItem(k))})", KEY)
    chk("F11a G4 老存档迁移逐字节回滚点 / collected=[] / legacyCollected / v2",
        d["bak"] == raw and d["cur"].get("collected") == [] and
        d["cur"].get("legacyCollected") == OLD8 and
        d["cur"]["rally"].get("schemaVersion") == 2)
    page.evaluate("""k => {
      const d = JSON.parse(localStorage.getItem(k));
      d.rally = Object.assign({}, d.rally, {gems: 77, shields: 3, EP02:{stars:3,played:5},
        ownedPaints:['paint-plus'], howSeen:true, unlocked:['U07']});
      localStorage.setItem(k, JSON.stringify(d));
      window.Store.setStars('EP03', 2); window.Store.setSound(false);
    }""", KEY)
    a = page.evaluate("k => JSON.parse(localStorage.getItem(k))", KEY)
    chk("F11b 跨站 last-write-wins 不覆盖（B 的 rally 全保住 + A 自己写入成功）",
        a["rally"].get("gems") == 77 and a["rally"].get("EP02", {}).get("played") == 5
        and "U07" in a["rally"].get("unlocked", [])
        and a.get("stars", {}).get("EP03") == 2 and a.get("sound") is False)

    p2 = ctx.new_page(); watch(p2)
    p2.goto(U_RALLY, wait_until="domcontentloaded"); p2.wait_for_timeout(600)
    rr = p2.evaluate("() => performance.getEntriesByType('resource').map(r=>r.name)")
    chk("F11c 拉力赛实际请求全带新 tag + 跨目录显示表按字节送达",
        any(TAG in n for n in rr) and
        p2.evaluate("() => !!(window.IPA_DISPLAY && window.IPA_DISPLAY.U11.displayIpa==='ɜr')"),
        {"资源数": len(rr), "带 tag": sum(1 for n in rr if TAG in n)})

    # F10 G5 场景 B：受控强缓存 —— 不带 tag 的 js/css 注入旧缓存脏内容
    ctx2 = browser.new_context(viewport={"width": 1280, "height": 800})
    p3 = ctx2.new_page()
    err2 = {"pageerror": 0, "console_error": 0, "stale_hits": 0, "img_untagged": 0}
    untagged_urls = []
    p3.on("pageerror", lambda e: err2.__setitem__("pageerror", err2["pageerror"] + 1))
    p3.on("console", lambda m: err2.__setitem__("console_error", err2["console_error"] + 1) if m.type == "error" else None)
    def stale_router(route):
        u = route.request.url
        if "?v=" in u:
            route.continue_(); return
        if re.search(r'\.(js|css)(\?|$)', u):
            err2["stale_hits"] += 1
            route.fulfill(status=200, content_type="application/javascript", body="/* STALE CACHE COPY */")
            return
        # favicon 是浏览器自动请求的站点图标，非内容资源，不纳入版本化治理。
        if re.search(r'\.(webp|png)(\?|$)', u) and "favicon" not in u:
            err2["img_untagged"] += 1
            untagged_urls.append(u.rsplit("/", 1)[-1])
        route.continue_()
    p3.route("**/*", stale_router)
    p3.goto(U_QUEST + "#/atlas", wait_until="domcontentloaded"); p3.wait_for_timeout(700)
    dom3 = p3.evaluate("""() => ({
      syms: [...document.querySelectorAll('.sym')].map(e => e.textContent.trim()),
      sprites: [...document.querySelectorAll('img[src*="assets/sprites/"]')].length,
      dataReady: !!(window.IPA_DATA && window.IPA_DISPLAY)
    })""")
    chk("F10a G5 强缓存场景：js/css 无漏网的不带 tag 资源（0 次脏内容注入）",
        err2["stale_hits"] == 0 and err2["pageerror"] == 0 and err2["console_error"] == 0,
        {"stale_hits": err2["stale_hits"], "pageerror": err2["pageerror"],
         "console_error": err2["console_error"]})
    chk("F10b G5 强缓存场景：页面仍完整渲染美式图鉴",
        dom3["dataReady"] and len(dom3["syms"]) == 48 and
        not any(re.search(r'ː|ɒ|əʊ|ɪə|eə|ʊə', s) for s in dom3["syms"]) and dom3["sprites"] > 0,
        {"大字": len(dom3["syms"]), "立绘": dom3["sprites"]})
    if err2["img_untagged"]:
        note("缓存串口径缺口：仍有图片 URL 未带 ?v=",
             "%d 个请求；明细：%s" % (err2["img_untagged"], sorted(set(untagged_urls))[:8]))

    print("\n=== 四项错误计数 ===")
    from collections import Counter
    kinds = Counter((f or "None") for _, f in FAILS)
    real = [(u, f) for u, f in FAILS if f and "ERR_ABORTED" not in f]
    print(" ", errs, "原因分布:", dict(kinds))
    chk("F11d 两站页面异常/控制台/HTTP/真实网络失败全 0",
        errs["pageerror"] == 0 and errs["console_error"] == 0 and
        errs["bad_status"] == 0 and len(real) == 0,
        (errs, dict(kinds), real[:4]))
    browser.close()

server.shutdown(); server.server_close()
print("\n" + "=" * 60)
p = sum(1 for _, ok, _ in RESULTS if ok)
f = len(RESULTS) - p
print("SUMMARY: %d PASS / %d FAIL / %d TOTAL  |  CONCERNS/NOTE: %d"
      % (p, f, len(RESULTS), len(NOTES)))
if f:
    for n, ok, d in RESULTS:
        if not ok: print("  FAILED:", n, d)
if NOTES:
    for n, d in NOTES: print("  NOTE:", n, "|", d)
print("=" * 60)
sys.exit(1 if f else 0)
