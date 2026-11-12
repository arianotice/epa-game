# -*- coding: utf-8 -*-
"""#20b / P0 路线 B 门控重定义 · 独立实跑（quality-lead，新文件，不改五套既有脚本）。

依据：design/p0-qa-spec.md v1.1（含附录 A 三处判据修订）+ design/p0-impl-report.md §9 十项。
覆盖：K1–K5 五类 / BC 双层缓存 / BV dev+build 资源送达 / BI 等价时序 / BR 探针 / 四项错误计数。
服务生命周期：本脚本自起 dev(5173) 与 preview(4173)，finally 显式 terminate 释放端口（串行纪律）。
证据：全部日志落 .workbuddy/backups/p0-evidence-20261109/qa/（项目内，非 Temp）。
边界：纯验证，零产品改动；不改五套验收脚本；不部署/上线/commit。
用法：python verify_p0_gate.py
"""
import os, sys, io, re, json, time, socket, hashlib, subprocess, threading, urllib.parse, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

HERE = os.path.dirname(os.path.abspath(__file__))          # 音标拉力赛/
ROOT = os.path.dirname(HERE)                              # 英语音标播客/
QUEST = os.path.join(ROOT, "音标大闯关")
DIST = os.path.join(ROOT, ".p0-build", "dist")
SNAP = os.path.join(ROOT, ".workbuddy", "backups", "p0-pre-20261109")
EV = os.path.join(ROOT, ".workbuddy", "backups", "p0-evidence-20261109", "qa")
os.makedirs(EV, exist_ok=True)
NODE = "node"
VITE = os.path.join(HERE, "node_modules", "vite", "bin", "vite.js")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SRC_TAG = "hud-20261108"
VENDOR_TAG = "p0-20261109"
N_EXPECT = 3
BASE = {"dev": "http://127.0.0.1:5173", "build": "http://127.0.0.1:4173"}
SRC_SCAN_FILES = [
    "音标大闯关/index.html", "音标大闯关/js/atlas.js", "音标大闯关/js/level.js",
    "音标大闯关/js/map.js", "音标大闯关/js/story.js",
    "音标拉力赛/index.html", "音标拉力赛/js/main.js",
    "音标拉力赛/js/race.js", "音标拉力赛/js/render.js",
]
CORE_FILES = ["音标拉力赛/js/race.js", "音标拉力赛/js/track.js", "音标拉力赛/js/config.js",
              "音标拉力赛/js/main.js", "音标拉力赛/js/headless_laps.mjs"]
GATE_FILES = ["音标拉力赛/verify_cseg_gate.py", "音标拉力赛/verify_cseg_ui.py",
              "音标拉力赛/verify_hud_spec.py", "音标大闯关/verify_fresh_gate.py",
              "音标大闯关/verify_c08_gate.py"]
EXCLUDE_DIRS = {"node_modules", "dist", "src", ".vite", "coverage", "__pycache__"}

RESULTS, NOTES, CONCERNS = [], [], []
FALLBACK_PROBED = {"dev": False, "build": False}

def chk(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + ("  | " + str(detail) if detail != "" else ""))
    return bool(ok)

def note(name, detail=""):
    NOTES.append((name, detail)); print("  NOTE  " + name + ("  | " + str(detail) if detail else ""))

def concern(name, detail=""):
    CONCERNS.append((name, detail)); print("  CONCERNS  " + name + ("  | " + str(detail) if detail else ""))

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def read(p, enc="utf-8"):
    return open(p, encoding=enc, errors="replace").read()

def rel(path, base=ROOT):
    return os.path.relpath(path, base).replace("\\", "/")

# ---------------------------------------------------------------- 服务生命周期
procs = []
def port_up(port):
    s = socket.socket(); s.settimeout(0.3)
    r = s.connect_ex(("127.0.0.1", port)); s.close(); return r == 0

def wait_port(port, proc, timeout=40):
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            return False, "server exited rc=%s" % proc.returncode
        if port_up(port): return True, "%.1fs" % (time.time() - t0)
        time.sleep(0.25)
    return False, "timeout %ss" % timeout

def start_servers():
    ok_all = True
    devlog = open(os.path.join(EV, "qa_dev_server.log"), "w", encoding="utf-8")
    prevlog = open(os.path.join(EV, "qa_preview_server.log"), "w", encoding="utf-8")
    p1 = subprocess.Popen([NODE, VITE, "--host", "127.0.0.1", "--port", "5173", "--strictPort"],
                          cwd=HERE, stdout=devlog, stderr=subprocess.STDOUT)
    procs.append(p1)
    ok1, d1 = wait_port(5173, p1)
    p2 = subprocess.Popen([NODE, VITE, "preview", "--host", "127.0.0.1", "--port", "4173", "--strictPort"],
                          cwd=HERE, stdout=prevlog, stderr=subprocess.STDOUT)
    procs.append(p2)
    ok2, d2 = wait_port(4173, p2)
    ok_all = ok1 and ok2
    print("SERVER dev=%s(%s) preview=%s(%s)" % (ok1, d1, ok2, d2))
    return ok_all

def stop_servers():
    for p in procs:
        try: p.terminate()
        except Exception: pass
    for p in procs:
        try: p.wait(timeout=8)
        except Exception:
            try: p.kill()
            except Exception: pass
    time.sleep(0.6)
    print("PORTS after stop: 5173=%s 4173=%s" %
          ("IN USE" if port_up(5173) else "FREE", "IN USE" if port_up(4173) else "FREE"))

# ---------------------------------------------------------------- URL / HTTP 工具
def url(mode, path):
    return BASE[mode] + urllib.parse.quote(path, safe="/?=&")

def http_get(mode, path, timeout=12):
    import urllib.request
    u = url(mode, path)
    try:
        with urllib.request.urlopen(u, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read()
    except Exception as e:
        return -1, {}, ("%s: %s" % (type(e).__name__, e)).encode()

MAGIC = {
    ".webp": lambda b: b[:4] == b"RIFF" and b[8:12] == b"WEBP",
    ".png": lambda b: b[:8] == b"\x89PNG\r\n\x1a\n",
    ".mp3": lambda b: b[:3] == b"ID3" or (len(b) > 1 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0),
    ".opus": lambda b: b[:4] == b"OggS",
}
def magic_ok(body, path):
    ext = os.path.splitext(path)[1].lower()
    if ext in MAGIC: return MAGIC[ext](body)
    # JS/CSS/HTML/JSON：可打印且不含 <html（防兜底 HTML 伪装成 JS）
    if ext in (".js", ".mjs", ".css", ".json"):
        return b"<html" not in body[:400].lower() and b"<!doctype html" not in body[:400].lower()
    return True

def ctype_matches(path, ctype):
    ext = os.path.splitext(path)[1].lower()
    want = {".webp": "image/webp", ".png": "image/png", ".mp3": "audio/mpeg",
            ".opus": "audio/ogg", ".js": "javascript", ".mjs": "javascript",
            ".css": "text/css", ".json": "application/json", ".html": "text/html"}.get(ext)
    if not want: return True
    return want in (ctype or "").lower()

# ---------------------------------------------------------------- 静态层
print("=" * 74)
print("=== BD 判定核心确定性（K1）· 静态 sha256 + 原路径实跑 ===")
print("=" * 74)
fh = json.load(open(os.path.join(SNAP, "file-hashes.json"), encoding="utf-8"))
snap_map = {e["path"].replace("\\", "/"): e["sha256"] for e in fh["files"]}

def snap_eq(relp):
    exp = snap_map.get(relp)
    cur = sha(os.path.join(ROOT, relp)) if os.path.exists(os.path.join(ROOT, relp)) else None
    return exp is not None and cur is not None and exp == cur

core_eq = {r: snap_eq(r) for r in CORE_FILES}
chk("BD-1 判定核心 5 文件 sha256 与 P0 前快照逐字全等（逐字不改/不移植TS/不进React state）",
    all(core_eq.values()), {"逐项": core_eq, "快照": "p0-pre-20261109/file-hashes.json",
                            "all_src_equal": fh.get("all_src_equal")})
gate_eq = {r: snap_eq(r) for r in GATE_FILES}
chk("BD-1b 五套既有验收脚本 sha256 与快照全等（零改动）", all(gate_eq.values()), gate_eq)
chk("BD-1c data.js / ipa-display.js 字节全等（K3 权威表未动）",
    snap_eq("音标大闯关/js/data.js") and snap_eq("音标大闯关/js/ipa-display.js"),
    {"data.js": sha(os.path.join(QUEST, "js", "data.js"))[:16],
     "ipa-display.js": sha(os.path.join(QUEST, "js", "ipa-display.js"))[:16]})

r = subprocess.run([NODE, "js/headless_laps.mjs"], cwd=HERE, capture_output=True, text=True, timeout=240)
hl = r.stdout + r.stderr
times = [float(x) for x in re.findall(r"^\s*(?:follow|listen)\s+\S+\s+\S+\s+YES\s+([\d.]+)", hl, re.M)]
chk("BD-2 node js/headless_laps.mjs 原路径原命令 11 场 ALL PASS 且 max(finishTime)<=180s",
    r.returncode == 0 and "ALL PASS" in hl and len(times) == 11 and max(times) <= 180.0,
    {"exit": r.returncode, "场数": len(times), "min": min(times) if times else None,
     "max": max(times) if times else None, "题库": re.search(r"题库:.*", hl).group(0) if "题库:" in hl else "-"})
open(os.path.join(EV, "qa_headless.log"), "w", encoding="utf-8").write(hl)

r2 = subprocess.run([NODE, "js/minimap_model.test.mjs"], cwd=HERE, capture_output=True, text=True, timeout=120)
mm = r2.stdout + r2.stderr
chk("BD-3 minimapModel 纯函数单测 10 项全绿",
    r2.returncode == 0 and "10 PASS / 0 FAIL / 10 TOTAL" in mm,
    re.search(r"SUMMARY:.*", mm).group(0) if "SUMMARY:" in mm else "no summary")
open(os.path.join(EV, "qa_minimap_model.log"), "w", encoding="utf-8").write(mm)

print()
print("=" * 74)
print("=== BC 双层缓存 46 + N（附录 A.1 修订判据）===")
print("=" * 74)
cnt = collections.Counter()
for r0 in SRC_SCAN_FILES:
    cnt.update(re.findall(r"\?v=([A-Za-z0-9\-]+)", read(os.path.join(ROOT, r0))))
chk("BC-1 源码层 9 文件白名单 tag 唯一且恰好 46",
    dict(cnt) == {SRC_TAG: 46} and set(cnt) == {SRC_TAG}, {"直方图": dict(cnt)})

# 产物层：VENDOR_TAG 字面量计数（唯一值、恰好 N）
nvendor = 0; vendor_per = {}; resid = 0; resid_per = {}
for dp, _, fns in os.walk(DIST):
    for fn in fns:
        p = os.path.join(dp, fn)
        try: t = read(p)
        except Exception: continue
        a = t.count(VENDOR_TAG); b = t.count(SRC_TAG)
        if a: vendor_per[rel(p, DIST)] = a
        if b: resid_per[rel(p, DIST)] = b
        nvendor += a; resid += b
# 产物层「唯一值」：dist 内 VENDOR_TAG 是唯一版本标识字面量（不与源码层 tag 混算、无第二种 vendor tag）
chk("BC-2 产物层 VENDOR_TAG 唯一且恰好 N=3（.p0-build/dist 独立扫描根）",
    nvendor == N_EXPECT and len(vendor_per) > 0 and VENDOR_TAG != SRC_TAG,
    {"N": nvendor, "逐文件": vendor_per, "VENDOR_TAG": VENDOR_TAG,
     "唯一值口径": "dist 内仅 VENDOR_TAG 一种构建层标识；源码层 tag 见 BC-3 单列披露"})

# BC-3 修订判据：扫描根物理隔离 + 各层唯一 + 不同值 + 源码层不含产物 tag + 源码层无杂 tag
src_roots = {os.path.join(ROOT, "音标大闯关"), HERE}
dist_root = DIST
isolated = not any(os.path.abspath(dist_root).startswith(os.path.abspath(s) + os.sep) for s in src_roots)
src_no_vendor = all(VENDOR_TAG not in read(os.path.join(ROOT, r0)) for r0 in SRC_SCAN_FILES)
src_single_tag = set(cnt) == {SRC_TAG}
dist_single_tag = True  # nvendor 全部计的是 VENDOR_TAG 字面量本身
different = VENDOR_TAG != SRC_TAG
chk("BC-3 两层互不混算（扫描根隔离 + 各层唯一+不同值+源码层不含产物tag；附录A.1修订）",
    isolated and dict(cnt) == {SRC_TAG: 46} and nvendor == N_EXPECT
    and different and src_no_vendor and src_single_tag and dist_single_tag,
    {"扫描根隔离": isolated, "源码层": dict(cnt), "产物层N": nvendor,
     "VENDOR_TAG!=SRC_TAG": different, "源码层不含VENDOR_TAG": src_no_vendor,
     "产物层残留 hud-20261108（单列披露、不计入N、不作FAIL依据）": resid,
     "残留逐文件": resid_per})

STRLIT = re.compile(r"""["'`]([^"'`\n]*\.(?:webp|png)[^"'`\n]*)["'`]""")
CONCAT = re.compile(r"""["'`]([^"'`\n]*assets/img/)["'`]\s*\+\s*[^,;)\n]{1,60}""")
def bare_in(paths):
    out = []
    for p in paths:
        t = read(p)
        for m in STRLIT.finditer(t):
            u = m.group(1)
            if "/" in u and "?v=" + SRC_TAG not in u and "${CACHE_TAG}" not in u:
                out.append((rel(p), u))
        for m in CONCAT.finditer(t):
            seg = t[m.start():m.end()]
            if "?v=" + SRC_TAG not in seg: out.append((rel(p), "CONCAT " + seg.strip()[:40]))
    return out
wl_bare = bare_in([os.path.join(ROOT, r0) for r0 in SRC_SCAN_FILES])
chk("BC-4 20 个图片 URL 零裸引用（含 assets/img/+变量 拼接型，白名单口径）",
    len(wl_bare) == 0, {"裸引用数": len(wl_bare), "明细": wl_bare[:5]})

# 原口径复现（不排除 node_modules）：全仓裸引用是否全部来自 node_modules（诊断，非 FAIL 依据）
all_bare = []
for base in (QUEST, HERE):
    for dp, dns, fns in os.walk(base):
        for fn in fns:
            if not fn.endswith((".html", ".js", ".css")): continue
            p = os.path.join(dp, fn); r0 = rel(p, base)
            if r0.startswith(("assets/", "docs/", "sprite_gen/")): continue
            t = read(p)
            for m in STRLIT.finditer(t):
                u = m.group(1)
                if "/" in u and "?v=" + SRC_TAG not in u and "${CACHE_TAG}" not in u:
                    all_bare.append((r0, "node_modules" in r0))
nm_flags = [x[1] for x in all_bare]
chk("BC-5 原口径全仓裸引用全部来自 node_modules（诊断披露；白名单口径已 PASS）",
    all(nm_flags) if nm_flags else True,
    {"原口径裸引用总数": len(all_bare), "来自node_modules": sum(nm_flags),
     "非node_modules": sum(1 for x in nm_flags if not x),
     "说明": "原 S17/S18 全仓口径在构建链下失效（F-01/F-02），此处仅复现污染来源"})

vm = json.load(open(os.path.join(HERE, "vendor.manifest.json"), encoding="utf-8"))
pinned = {e["name"]: e["version"] for e in vm["pinned"]}
chk("BC-6 vendor.manifest 版本钉定（three 0.186.1 / VENDOR_TAG / 双命名空间声明）",
    pinned.get("three") == "0.186.1" and vm.get("VENDOR_TAG") == VENDOR_TAG
    and vm["cache_namespaces"]["source_layer"]["count"] == 46
    and vm["cache_namespaces"]["build_layer"]["tag"] == VENDOR_TAG,
    {"three": pinned.get("three"), "VENDOR_TAG": vm.get("VENDOR_TAG"),
     "pinned数": len(pinned), "peer_verified": len(vm.get("peer_upper_bounds_verified", []))})

# ---------------------------------------------------------------- 浏览器层
print()
print("=" * 74)
print("=== BV / BI / BR / BD-4 / BQ / BS / BE 浏览器实跑（dev + build 双模式串行）===")
print("=" * 74)

from playwright.sync_api import sync_playwright

ERR_CATS = ("ERR_ABORTED", "同源真实失败", "外链环境", "Vite机制")
VOCAB = []          # 全局共享：K4 的 allWords() 83 词全表，BQ-1 与 BQ-2 共用，禁止缩小
FIELD_NAMES = ("correctLateral", "spoken", "left", "right")
FORBID_ATTR = re.compile(r"data-(lane|correct|side|answer|left|right|word|ipa|spoken)", re.I)

def scan_surface(surface, html, vocab, attrs, ipas=()):
    """K4 共用检测：词表 = 83 词全表 + 4 字段名（不缩小）；返回子串/完整词/IPA 三类命中。

    - 子串命中 sub：H5 原始口径（最严），用于 2D HUD（检测面短、无引擎注入文本）。
    - 完整词命中 whole：按词边界匹配，用于含 R3F 注入 CSS / 调试状态文本的检测面；
      对把答案词整体写进 DOM 的真泄露同样命中，但排除 `lock`⊂`block` 这类无关碰撞。
    - IPA 斜杠形式：独立硬断言，补规格 §1 K4「+IPA」要求（斜杠形式不与普通英文碰撞）。
    - 检测面 = textContent + 后代所有属性值；innerHTML 仅诊断、不计判定（#5 裁决口径）。
    """
    sl = (surface or "").lower()
    tokens = set(w for w in vocab if w) | set(FIELD_NAMES)
    sub = sorted(t for t in tokens if t and t.lower() in sl)
    whole = sorted(t for t in tokens
                   if t and re.search(r"(?<![a-z0-9])" + re.escape(t.lower()) + r"(?![a-z0-9])", sl))
    ipa_hits = sorted(x for x in set("/" + i + "/" for i in ipas if i) if x.lower() in sl)
    cn = [k for k in ("答案", "正确") if k in sl]
    badn = [n for n, _ in attrs if FORBID_ATTR.search(n)]
    html_sub = sorted(t for t in tokens if t and t.lower() in (html or "").lower())
    return {"sub": sub, "whole": whole, "ipa": ipa_hits, "cn": cn,
            "badn": badn, "html_sub": html_sub, "词表数": len(vocab)}
class Watch:
    def __init__(self, page):
        self.e = {"pageerror": 0, "console_error": 0, "bad_status": 0}
        self.fails = []          # (url, failure)
        self.console_texts = []
        self.console_items = []   # (text, location_url) —— 供外链派生 console.error 做来源配对
        self.bad_urls = []       # (status, url) —— 4xx 明细，便于定位是产品资源还是脚本噪声
        page.on("pageerror", lambda e: self.e.__setitem__("pageerror", self.e["pageerror"] + 1))
        page.on("console", self._console)
        page.on("requestfailed", lambda r: self.fails.append((r.url, r.failure or "None")))
        page.on("response", self._response)
    def _console(self, m):
        if m.type == "error":
            self.e["console_error"] += 1
            self.console_texts.append(m.text[:160])
            try: loc = (m.location or {}).get("url", "") or ""
            except Exception: loc = ""
            self.console_items.append((m.text[:160], loc))
    def _response(self, r):
        if r.status >= 400:
            self.e["bad_status"] += 1
            self.bad_urls.append((r.status, r.url))
    def classify(self):
        aborted = same = external = vite = 0; real = []; ext_urls = []
        for u, f in self.fails:
            if "ERR_ABORTED" in f: aborted += 1; continue
            is_local = ("127.0.0.1" in u) or ("localhost" in u)
            if is_local:
                same += 1; real.append((u, f))
            elif "fonts.googleapis.com" in u or "fonts.gstatic.com" in u or "gstatic" in u:
                external += 1; ext_urls.append((u, f))
            elif any(k in u for k in ("/@vite/client", "/@fs/", "/@id/", ".vite/deps", "ws://", "wss://")):
                vite += 1
            else:
                same += 1; real.append((u, f))
        # K5 分类完备化（附录 A.7）：浏览器会为「外链资源加载失败」自动派生一条
        # console.error("Failed to load resource: ...")。同一事件在 requestfailed 侧按外链
        # 环境项 NOTE 单列，在 console.error 侧也必须一致，但必须【逐条 + URL 级配对证明】：
        #   ① 派生条数 <= 已核实外链失败条数；
        #   ② 每条派生 console.error 的 location.url 必须是外部 host（不得是同源/空同源资源）；
        #   ③ 同源真实失败 == 0（硬条件，绝不被外链项豁免）。
        # 任何不满足配对的 console.error（含页面自身 console.error）仍是硬失败。
        derived_pairs = [(t, u) for t, u in self.console_items if "Failed to load resource" in t]
        hard_console = [t for t, _ in self.console_items if "Failed to load resource" not in t]
        def is_external_loc(u):
            return bool(u) and ("fonts.googleapis.com" in u or "fonts.gstatic.com" in u
                               or "gstatic" in u) and ("127.0.0.1" not in u and "localhost" not in u)
        # ConsoleMessage.location.url 通常指向失败资源；若 Chrome 未给 location（空），
        # 则退化为「计数配对 + 同源真实失败=0 + bad_status=0」三重约束，仍不豁免同源项。
        loc_known = [u for _, u in derived_pairs if u]
        loc_ok = (not loc_known) or all(is_external_loc(u) for u in loc_known)
        paired = (len(derived_pairs) <= len(ext_urls)) and loc_ok
        return {"总计": len(self.fails), "ERR_ABORTED": aborted, "同源真实失败": same,
                "外链环境": external, "Vite机制": vite, "同源真实明细": real[:6],
                "bad_status明细": self.bad_urls[:6],
                "console_error总数": len(self.console_texts),
                "外链派生console_error": [t for t, _ in derived_pairs],
                "派生console_error的location.url": [u for _, u in derived_pairs],
                "location级配对": loc_ok, "硬失败console_error": hard_console,
                "配对成立": paired, "外链失败明细": ext_urls[:6]}

# 资源集：跨目录静态代表（dev 中间件 + build 复制都覆盖）
RES_SET = [
    ("音标大闯关/js/ipa-display.js", "/音标大闯关/js/ipa-display.js"),
    ("音标大闯关/assets/img/a1.webp", "/音标大闯关/assets/img/a1.webp"),
    ("音标大闯关/assets/sprites/U01.webp", "/音标大闯关/assets/sprites/U01.webp"),
    ("音标大闯关/assets/sprites/U02.webp", "/音标大闯关/assets/sprites/U02.webp"),
    ("音标大闯关/assets/sprites/cards/U01.webp", "/音标大闯关/assets/sprites/cards/U01.webp"),
    ("音标拉力赛/audio/fan.mp3", "/audio/fan.mp3"),
]
def build_res_local(mode, path):
    # build 产物内路径
    if path.startswith("音标大闯关/"): return os.path.join(DIST, path)
    return os.path.join(DIST, path.split("/", 1)[1])  # 音标拉力赛/audio/x -> dist/audio/x

def do_bv(mode):
    # BV-0 硬前置：先探兜底（结果登记，不强求「无兜底」）
    st, hd, body = http_get(mode, "/音标大闯关/assets/img/__qa_missing_9f3a.webp?v=__probe__")
    ctype = hd.get("Content-Type", "")
    fallback200 = (st == 200 and ("text/html" in ctype.lower()
                   or body.lstrip()[:15].lower().startswith(b"<!doctype")
                   or body.lstrip()[:6].lower().startswith(b"<html")))
    chk("BV-0[%s] 先探兜底：探测已执行且结果如实登记（此后状态码一律不可信）" % mode,
        isinstance(st, int) and st > 0,
        {"探测路径": "__qa_missing_9f3a.webp", "status": st, "ctype": ctype,
         "存在兜底200HTML": fallback200,
         "口径": "BV-1 起只按 逐字节+magic+sha256+CType非text/html 判定"})
    FALLBACK_PROBED[mode] = True
    passed = 0
    for disk_rel, path in RES_SET:
        disk = os.path.join(ROOT, disk_rel)
        if not os.path.exists(disk):
            chk("BV-1[%s] %s 资源存在" % (mode, disk_rel), False, "磁盘缺失"); continue
        st2, hd2, body2 = http_get(mode, path + "?v=" + SRC_TAG)
        ct = hd2.get("Content-Type", "")
        disk_b = open(disk, "rb").read()
        ok = (FALLBACK_PROBED[mode] and body2 == disk_b and magic_ok(body2, disk_rel)
              and "text/html" not in ct.lower() and ctype_matches(disk_rel, ct)
              and hashlib.sha256(body2).hexdigest() == hashlib.sha256(disk_b).hexdigest())
        passed += 1 if ok else 0
        chk("BV-1[%s] %s 逐字节+magic+sha256+CType非text/html" % (mode, disk_rel), ok,
            {"status": st2, "ctype": ct, "送达字节": len(body2), "本地字节": len(disk_b),
             "byteEqual": body2 == disk_b, "magic": magic_ok(body2, disk_rel),
             "sha256_16": hashlib.sha256(body2).hexdigest()[:16]})
    return passed

def do_bi(mode, page, watch):
    # BI-1 script 形态（等价时序口径：不按 DOM 顺序判）
    d = page.evaluate("""() => {
      const s = [...document.querySelectorAll('script')].find(x => (x.src||'').includes('ipa-display.js'));
      const m = [...document.querySelectorAll('script[type=module]')];
      const D = window.IPA_DISPLAY;
      const ts = window.__P0_IPA_TS__ || null;
      return {scriptFound: !!s, type: s?s.getAttribute('type'):null,
              defer: s?s.hasAttribute('defer'):false, async: s?s.hasAttribute('async'):false,
              moduleCount: m.length, ready: !!D, keys: D?Object.keys(D).length:0,
              u11: D&&D.U11?D.U11.displayIpa:null,
              moduleDone: !!(window.__rally && document.getElementById('minimap')),
              ipaFirstSeenState: ts?ts.state:null, ipaFirstSeenKeys: ts?ts.keys:null,
              domOrder: s&&m.length? (s.compareDocumentPosition(m[0]) & Node.DOCUMENT_POSITION_FOLLOWING ? 'script在module前' : 'script在module后') : null};
    }""")
    chk("BI-1[%s] ipa-display.js 仍为非 module / 无 defer / 无 async" % mode,
        d["scriptFound"] and d["type"] is None and not d["defer"] and not d["async"], d)
    # BI-2 等价时序（附录 A.2）：不按 DOM 字面顺序，验「实际执行时序」——
    # add_init_script 在文档解析最早阶段轮询记录 IPA_DISPLAY 首次可见的 document.readyState；
    # module 默认 defer 到 DOMContentLoaded 前才执行，故 readyState=loading 时已就绪即证明先于 module。
    chk("BI-2[%s] 等价时序：module 执行前 IPA_DISPLAY 已就绪 / U11=ɜr / 48键 / module已完成" % mode,
        d["ready"] and d["keys"] == 48 and d["u11"] == "ɜr" and d["moduleDone"]
        and d["ipaFirstSeenState"] == "loading" and d["ipaFirstSeenKeys"] == 48,
        {"ready": d["ready"], "keys": d["keys"], "u11": d["u11"], "moduleDone": d["moduleDone"],
         "IPA_DISPLAY首次可见的readyState": d["ipaFirstSeenState"],
         "首次可见时键数": d["ipaFirstSeenKeys"], "DOM顺序(仅诊断不计判定)": d["domOrder"],
         "口径": "build 下 module 提到 head、DOM 顺序反了，但执行时序不变；验实际执行时序而非 DOM 字面顺序"})
    # BI-3 结果层：48 卡面美式 + 字节全等
    chk("BI-3[%s] 48 卡面美式 / 无英式符号 / sym 稳定键 / ipa-display.js 字节全等" % mode,
        d["ready"] and snap_eq("音标大闯关/js/ipa-display.js"),
        {"权威表字节": sha(os.path.join(QUEST, "js", "ipa-display.js"))[:16],
         "F1b/F9a 基线": "源码零改动，沿用 #5 已验口径"})

def do_bq(page):
    global VOCAB
    # K4：沿用 H5 口径 textContent + 后代所有属性值，不退回 innerHTML
    # 词表统一用 Node 直接读源码 js/config.js 的 allWords()（83 词全表，权威）。
    # 不用浏览器 import('/js/config.js?v=...')：build 产物无 js/ 源码目录，该请求会命中
    # SPA fallback 返回 200 text/html，制造 console.error / bad_status 假阳性（#20b 首跑实测）。
    vocab = []
    rr = subprocess.run([NODE, "-e",
        "import('./js/config.js').then(c=>console.log(JSON.stringify(c.allWords())))"],
        cwd=HERE, capture_output=True, text=True, timeout=30)
    try: vocab = json.loads(rr.stdout.strip().splitlines()[-1])
    except Exception: vocab = []
    VOCAB = vocab
    vocab_ok = (len(vocab) == 83 and len(set(vocab)) == 83)
    faces = ["correctLateral", "spoken", "left", "right"]
    info = page.evaluate("""() => {
      const mm = document.getElementById('minimap');
      if(!mm) return null;
      const attrs = [];
      [mm, ...mm.querySelectorAll('*')].forEach(el=>{
        for(const a of el.attributes) attrs.push([a.name, a.value]);
      });
      return {text: mm.textContent || '', attrs: attrs,
              html: mm.innerHTML || ''};
    }""")
    if info is None:
        chk("BQ-1 2D HUD 答案零泄露（#minimap 存在）", False, "#minimap 未就绪"); return
    surface = info["text"] + "," + ",".join(v for _, v in info["attrs"])
    ipas = page.evaluate("""() => {
      const D = window.IPA_DISPLAY || {}; const s = new Set();
      for (const k in D) { const o = D[k] || {}; if (o.displayIpa) s.add(o.displayIpa); if (o.sym) s.add(o.sym); }
      return [...s];
    }""")
    r1 = scan_surface(surface, info["html"], vocab, info["attrs"], ipas)
    # BQ-1 沿用 H5 原始【子串】口径（最严）：2D HUD 检测面短、无引擎注入文本
    chk("BQ-1 83 词全表+4 字段名 在 textContent+后代所有属性值零命中（不查 innerHTML）/ 禁用 data-*",
        vocab_ok and not r1["sub"] and not r1["cn"] and not r1["badn"] and not r1["ipa"],
        {"词表数": len(vocab), "恰为83且不重复": vocab_ok, "字段名": list(FIELD_NAMES),
         "子串命中": r1["sub"], "IPA斜杠形式命中": r1["ipa"], "中文答案域命中": r1["cn"],
         "禁用属性": r1["badn"], "检测面字符数": len(surface),
         "IPA token 数": len(ipas),
         "innerHTML假阳性证据(仅诊断不计判定)": r1["html_sub"][:4]})
    chk("BQ-1b 词表完整性守卫（len==83 且 set==83，防缩小词表）", vocab_ok,
        {"len": len(vocab), "set": len(set(vocab))})

def do_bs(mode, page):
    # K2：跨站单键保真 —— 2D 主形态零写盘 + rally 字段守恒
    d = page.evaluate("""() => {
      const KEY='ipa-quest-v1';
      const before = localStorage.getItem(KEY);
      const keysBefore = Object.keys(localStorage).sort();
      let writes=0; const orig = Storage.prototype.setItem;
      Storage.prototype.setItem = function(...a){ writes++; return orig.apply(this,a); };
      if(window.__rally && window.__rally.step) { try{ window.__rally.step(60); }catch(e){} }
      Storage.prototype.setItem = orig;
      const after = localStorage.getItem(KEY);
      return {keys: keysBefore, writes: writes, same: before===after,
              hasRally: !!(before && JSON.parse(before).rally)};
    }""")
    chk("BS-1[%s] 2D 主形态 step(60) 零写盘 / 键集合不变 / rally 字段守恒" % mode,
        d["writes"] == 0 and d["same"], d)

def do_br(mode, pw, ctx_host):
    # BR：探针默认关闭（主站不创建 WebGL 上下文）
    for vp in ((375, 780), (320, 568)):
        c = ctx_host.new_context(viewport={"width": vp[0], "height": vp[1]}, device_scale_factor=2)
        p = c.new_page(); w = Watch(p)
        # add_init_script 必须是「立即执行」语句（不能传未调用的箭头函数，#20b 首跑踩坑）
        p.add_init_script("""
          window.__P0_GLCOUNT__ = 0;
          (function(){
            var orig = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(t){
              if (String(t).indexOf('webgl') === 0) window.__P0_GLCOUNT__++;
              return orig.apply(this, arguments);
            };
          })();
        """)
        p.goto(BASE[mode] + "/index.html", wait_until="domcontentloaded")
        # 条件等待（替代固定 sleep，避免模块首加载抖动造成 flaky）
        try: p.wait_for_function("() => !!window.__rally && !!document.getElementById('minimap')", timeout=12000)
        except Exception: pass
        p.wait_for_timeout(300)   # 留一小段窗口，确认探针默认关闭下不会有任何 WebGL 上下文被创建
        gl = p.evaluate("() => window.__P0_GLCOUNT__")
        rally = p.evaluate("() => !!(window.__rally && document.getElementById('minimap'))")
        chk("BR-1[%s][%dx%d] 默认关闭：主站零 WebGL 上下文 / 2D L0 就绪" % (mode, vp[0], vp[1]),
            gl == 0 and rally,
            {"webgl_getContext次数": gl, "__rally就绪": rally,
             "hook生效": gl is not None,
             "口径": "主站 index.html 完全不加载探针；不打开 /probe.html 即不创建 WebGL 上下文"})
        c.close()
    # BR-2 探针开启：两视口 WebGL 上下文 + 立方体/纸雾/暖光
    for vp in ((375, 780), (320, 568)):
        c = ctx_host.new_context(viewport={"width": vp[0], "height": vp[1]}, device_scale_factor=2)
        p = c.new_page(); w = Watch(p)
        p.goto(BASE[mode] + "/probe.html", wait_until="domcontentloaded")
        p.wait_for_function("() => window.__P0_PROBE__ && window.__P0_PROBE__.frames > 3", timeout=15000)
        s = p.evaluate("""() => {
          const S = window.__P0_PROBE__;
          return {tag:S.tag, webgl:S.webgl, renderer:S.webglRenderer, fogIsExp2:S.fogIsExp2,
                  fogDensity:S.fogDensity, lightCount:S.lightCount, boxCount:S.boxCount,
                  drawCalls:S.drawCalls, frames:S.frames, mounted:S.mounted,
                  contextLost:S.contextLost, errors:S.errors,
                  canvas: !!document.querySelector('#probe-root canvas')};
        }""")
        chk("BR-2[%s][%dx%d] 探针开启：WebGL上下文+立方体+纸雾+暖光可见" % (mode, vp[0], vp[1]),
            s["webgl"] and "WebGL" in (s["renderer"] or "") and s["fogIsExp2"]
            and s["boxCount"] == 1 and s["lightCount"] == 1 and s["frames"] > 3
            and not s["contextLost"] and not s["errors"] and s["canvas"] and s["tag"] == VENDOR_TAG,
            s)
        # BR-3 一键关闭 3D（#probe-toggle 卸载 Canvas）
        p.click("#probe-toggle"); p.wait_for_timeout(500)
        off = p.evaluate("""() => ({mounted: window.__P0_PROBE__.mounted,
                                    canvas: !!document.querySelector('#probe-root canvas'),
                                    pressed: document.getElementById('probe-toggle').getAttribute('aria-pressed')})""")
        chk("BR-3[%s][%dx%d] #probe-toggle 一键关闭 3D（Canvas 卸载 / mounted=false）" % (mode, vp[0], vp[1]),
            off["mounted"] is False and not off["canvas"], off)
        # BR-4 一键关回 2D（#probe-back 返回 index.html）
        # 用条件等待而非固定 sleep：dev 首次加载模块较多，700ms 曾出现 __rally 未挂载的 flaky
        p.click("#probe-back")
        try: p.wait_for_function("() => !!window.__rally && !!document.getElementById('minimap')", timeout=12000)
        except Exception: pass
        back = p.evaluate("""() => ({url: location.href,
                                     rally: !!(window.__rally && document.getElementById('minimap')),
                                     probe: !!(window.__P0_PROBE__ && window.__P0_PROBE__.tag)})""")
        chk("BR-4[%s][%dx%d] #probe-back 关回 2D 主站（URL 正确 / 2D 就绪）" % (mode, vp[0], vp[1]),
            "/index.html" in back["url"] and back["rally"], back)
        c.close()

def do_be(mode, w, label):
    cl = w.classify()
    # K5 硬判据（附录 A.7 分类完备化，非放宽）：
    #   pageerror / bad_status / 同源真实失败 / 非外链派生的硬 console.error —— 四项一律 = 0。
    #   浏览器为「已核实的外链资源失败」自动派生的 "Failed to load resource" console.error，
    #   仅在【逐条配对成立】且【同源真实失败=0】时才按外链环境项 NOTE 单列；
    #   任何凭空出现的派生失败（配对不成立）仍判 FAIL。不得据此豁免任何同源项。
    chk("BE-1[%s][%s] 四项错误计数硬归零（同源真实失败=0 / 硬console_error=0 / 配对成立）" % (mode, label),
        w.e["pageerror"] == 0 and w.e["bad_status"] == 0
        and cl["同源真实失败"] == 0
        and len(cl["硬失败console_error"]) == 0
        and cl["配对成立"],
        {"errs": w.e, "明细": cl, "console.error文本": w.console_texts[:4],
         "口径": "外链派生 console.error 需逐条配对到外链失败 URL；不配对或不来自外链仍为硬失败"})
    if cl["外链环境"] > 0 or cl["外链派生console_error"]:
        note("BE-2[%s][%s] 外链环境项单列（Google Fonts，NOTE 不豁免同源）" % (mode, label),
             "外链 requestfailed=%d 条 / 派生 console.error=%d 条 / 配对成立=%s；"
             "同源真实失败仍须=0（实测=%d）"
             % (cl["外链环境"], len(cl["外链派生console_error"]),
                cl["配对成立"], cl["同源真实失败"]))
    if cl["Vite机制"] > 0 or cl["ERR_ABORTED"] > 0:
        note("BE-3[%s][%s] ERR_ABORTED / Vite 机制项单列" % (mode, label),
             "ERR_ABORTED=%d Vite机制=%d（不计失败、不静默吞）" % (cl["ERR_ABORTED"], cl["Vite机制"]))

def run_browser(pw):
    browser = pw.chromium.launch(headless=True, executable_path=CHROME)
    try:
        for mode in ("dev", "build"):
            print("\n----- MODE = %s -----" % mode)
            do_bv(mode)
            c = browser.new_context(viewport={"width": 1280, "height": 800})
            p = c.new_page(); w = Watch(p)
            # BI-2 等价时序打点：用 Object.defineProperty 拦截 window.IPA_DISPLAY 的赋值，
            # 在「同步 script 执行的那一刻」同步记录 document.readyState 与键数。
            # 不用 setInterval 轮询（解析阶段可能抢不到 tick，实测偶发 None —— 打点自身 flaky）。
            # setter 语义等价普通赋值，不影响产品读取；module 默认 defer 到解析完成后才执行。
            p.add_init_script("""
              window.__P0_IPA_TS__ = {state: null, keys: null};
              (function(){
                var _v;
                Object.defineProperty(window, 'IPA_DISPLAY', {
                  configurable: true,
                  get: function(){ return _v; },
                  set: function(v){
                    _v = v;
                    window.__P0_IPA_TS__.state = document.readyState;
                    window.__P0_IPA_TS__.keys = (v && typeof v === 'object') ? Object.keys(v).length : 0;
                  }
                });
              })();
            """)
            p.goto(BASE[mode] + "/index.html", wait_until="domcontentloaded")
            p.wait_for_function("() => !!window.__rally || !!window.IPA_DISPLAY", timeout=12000)
            p.wait_for_timeout(700)
            # BD-4 2D 主形态可用 + K1 判定一致性
            d = p.evaluate("""() => ({mode: window.__rally? window.__rally.mode : null,
                rally: !!window.__rally, mm: !!document.getElementById('minimap'),
                mmc: !!document.getElementById('minimap-c'),
                canvas: !!document.getElementById('c'),
                title: !!document.getElementById('panel-title'),
                listen: !!document.getElementById('btn-listen')})""")
            chk("BD-4[%s] 2D L0 主形态可用（__rally/mode/#c/#minimap/#minimap-c 就绪）" % mode,
                d["rally"] and d["mode"] == "title" and d["mm"] and d["mmc"] and d["canvas"], d)
            do_bi(mode, p, w)
            do_bq(p)
            do_bs(mode, p)
            do_be(mode, w, "2D主形态")
            # BQ-2 探针页答案零泄露（探针 root 全部后代属性）
            pc = c.new_page(); wp = Watch(pc)
            pc.goto(BASE[mode] + "/probe.html", wait_until="domcontentloaded")
            pc.wait_for_function("() => window.__P0_PROBE__", timeout=12000)
            pc.wait_for_timeout(600)
            surf = pc.evaluate("""() => {
              const roots = ['#probe-root','#probe-ui','#probe-status'];
              let text='', attrs=[];
              for(const sel of roots){ const el=document.querySelector(sel); if(!el) continue;
                text += el.textContent||'';
                [el,...el.querySelectorAll('*')].forEach(x=>{for(const a of x.attributes) attrs.push([a.name,a.value]);});
              }
              return {text, attrs};
            }""")
            s2 = surf["text"] + "," + ",".join(v for _, v in surf["attrs"])
            # K4 铁律：探针 overlay 也是检测面，用与 BQ-1 同一份 83 词全表 + 4 字段名，不缩小。
            # 附录 A.5：探针页含 R3F 注入的内联 CSS（display:block / position:relative）与
            # QA 调试状态文本（frames/drawCalls），短词 lock/me/sit 会作为【无关更长单词的子串】
            # 假阳性（与 #5 的 `<span` 撞 pan 同类）。故判据 = 完整词匹配（对真泄露同样命中、
            # 更精确）+ IPA 斜杠形式硬断言；子串命中逐条单列披露，不静默丢弃、不放宽词表。
            ipas2 = pc.evaluate("""() => {
              const D = window.IPA_DISPLAY || {}; const s = new Set();
              for (const k in D) { const o = D[k] || {}; if (o.displayIpa) s.add(o.displayIpa); if (o.sym) s.add(o.sym); }
              return [...s];
            }""")
            r2 = scan_surface(s2, "", VOCAB, surf["attrs"], ipas2)
            chk("BQ-2[%s] 探针 overlay DOM 83 词全表+4 字段名完整词零命中 / IPA 零命中 / 禁用 data-*" % mode,
                len(VOCAB) == 83 and not r2["whole"] and not r2["ipa"]
                and not r2["cn"] and not r2["badn"],
                {"词表数": len(VOCAB), "字段名": list(FIELD_NAMES), "IPA token 数": len(ipas2),
                 "完整词命中(硬判据)": r2["whole"], "IPA斜杠命中(硬判据)": r2["ipa"],
                 "中文答案域命中": r2["cn"], "禁用属性": r2["badn"],
                 "子串命中(仅诊断,逐条披露)": r2["sub"][:8],
                 "子串命中实证根因": "lock⊂display:block / me⊂frames / sit⊂position:relative（均非答案载体）",
                 "检测面字符数": len(s2),
                 "口径": "完整词边界匹配，对把答案词整体写入 DOM 的真泄露同样命中"})
            do_be(mode, wp, "探针")
            c.close()
            do_br(mode, pw, browser)
    finally:
        browser.close()

# ---------------------------------------------------------------- main
def main():
    t0 = time.time()
    print("P0 GATE  start=%s" % time.strftime("%Y-%m-%d %H:%M:%S"))
    print("ROOT=%s" % ROOT); print("EV=%s" % EV)
    srv_ok = False
    try:
        srv_ok = start_servers()
        chk("P0-0 dev(5173) 与 preview(4173) 服务启动就绪（端口释放后自行起）", srv_ok)
        if not srv_ok:
            concern("服务未就绪，浏览器层跳过", "见 qa_dev_server.log / qa_preview_server.log")
            return
        with sync_playwright() as pw:
            run_browser(pw)
    except Exception as e:
        import traceback
        chk("P0 顶层异常", False, "%s: %s" % (type(e).__name__, e))
        open(os.path.join(EV, "qa_traceback.log"), "w", encoding="utf-8").write(traceback.format_exc())
    finally:
        stop_servers()
        # T3 用户裁决项（不判 PASS、不悄悄放行）
        concern("CN-4 / T3：dist/ 单目录发布时两站不同源、共享 ipa-quest-v1 不成立",
                "按现有 deploy.sh 源码 scp 双站同级 → 同源成立；改 dist/ 单目录发布则 dist 内不含完整大闯关站 "
                "(仅 assets+ipa-display.js)，跨站跳转断、localStorage 共享前提不成立 → 须完整大闯关站同级部署。"
                "已升级用户裁决，本轮不判 PASS、不悄悄放行。")
        print("\n" + "=" * 74)
        p = sum(1 for _, ok, _ in RESULTS if ok); f = len(RESULTS) - p
        print("SUMMARY: %d PASS / %d FAIL / %d TOTAL" % (p, f, len(RESULTS)))
        if f:
            for n, ok, d in RESULTS:
                if not ok: print("  FAILED:", n, "|", d)
        if NOTES:
            print("-- NOTES (%d) --" % len(NOTES))
            for n, d in NOTES: print("  NOTE:", n, "|", d)
        if CONCERNS:
            print("-- CONCERNS (%d) --" % len(CONCERNS))
            for n, d in CONCERNS: print("  CONCERNS:", n, "|", d)
        print("elapsed=%.1fs" % (time.time() - t0))
        print("=" * 74)
        out = {"summary": {"PASS": p, "FAIL": f, "TOTAL": len(RESULTS)},
               "results": [{"name": n, "ok": ok, "detail": str(d)} for n, ok, d in RESULTS],
               "notes": [{"name": n, "detail": str(d)} for n, d in NOTES],
               "concerns": [{"name": n, "detail": str(d)} for n, d in CONCERNS]}
        open(os.path.join(EV, "qa_p0_gate_result.json"), "w", encoding="utf-8").write(
            json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(1 if f else 0)

if __name__ == "__main__":
    main()
