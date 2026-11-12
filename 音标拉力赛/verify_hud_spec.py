# -*- coding: utf-8 -*-
"""HUD 验收脚本（#5 用；纯验证，零产品改动）。

落地 design/hud-ux-spec.md 第 5 节 H1–H12 断言，对齐 verify_cseg_ui.py 的写法：
自起 in-process ThreadingHTTPServer + sync_playwright + chk(name, ok, detail)
+ page.evaluate + window.__rally.step(n) + 汇总 SUMMARY: N PASS / N FAIL / N TOTAL。

  H1  DOM 存在性 / aria-hidden / pointer-events / 底板 alpha / z-index
  H2  显隐矩阵（title/teach/countdown/racing/paused/quiz/boardOpen/shopOpen/results）
  H3  375×667 / 320×568 不溢出
  H4  PC + 375px 位置不重叠（#hud 子项 / #banner / #route-map；#quiz 按 z-index 层叠）
  H5  小地图不含答案文本（allWords() 83 词全表 / 字段名 / IPA / 禁用 data-* 属性）
      检测面 = mm.textContent + 后代元素所有属性值（alt/aria-label/title/data-* 等）；
      【#5 主理人裁决】不含 mm.innerHTML 源码字面量（`<span` 标签名会与 pen/pan 的 "pan" 假阳性）。
      83 词全表与 correctLateral/spoken/left/right 字段名一个不少，硬 chk 断言，不降级为 warn。
  H6  minimapModel 数据接口无答案键 + nextGate 键集合精确相等
  H7  路牌 S0/S1/S2 在 D_preview 阈值内出现（follow 1482 / listen 1620 里程）
  H8  S1 零文本 / S2 两侧对称、无指向性
  H9  quiz 冻结（#signs.hidden / simTime / karts[0].odo / setItem 零写入 / 回 racing 复原）
  H10 两圈同 commitT 不重复（lineT / line 差 = L / 圈号 / signKey / 第 2 圈正常出牌）
  H11 缓存串唯一 46 处 + 20 个图片 URL 零裸引用 + 资源按字节/内容送达
  H12 四项错误计数归零 + HUD 路径零写盘 + 跨站 rally 字段开赛前后不变

【四项错误计数口径】pageerror / console_error / requestfailed / bad_status 全部按明细判定：
  * net::ERR_ABORTED —— Playwright reload / 导航主动取消在途请求，属正常现象，单列披露、不计失败；
  * 同源（127.0.0.1）非 ERR_ABORTED 的 requestfailed —— 真实网络失败，必须为 0；
  * 外链字体（fonts.googleapis.com / fonts.gstatic.com）非 ERR_ABORTED 失败 —— 环境相关，
    以 NOTE 披露、不计入硬失败（资源送达另由「按字节/内容比对」覆盖，不信状态码）。
  * pageerror / console_error / bad_status —— 一律硬失败必须为 0。

【优雅报错】#4 未落地（#minimap 未出现 / __rally 未就绪 / tag 未 bump）时，
打印「HUD 元素未就绪，请先完成 #4」并以退出码 2 干净退出，不抛裸 traceback。

【硬约束】本脚本只读源码、只驱动浏览器，不修改任何产品文件 / 既有验收脚本；
不部署、不上线、不 commit。Playwright 1.64.1 缺 chromium-1248，必须显式指定系统 Chrome。

用法： python verify_hud_spec.py
前置：#4 已落地。无需外部服务器，脚本自起 HTTP server 并在退出时释放端口。
"""
import os
import sys
import io
import re
import json
import threading
import functools
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
QUEST = os.path.join(ROOT, "音标大闯关")
RALLY = HERE
KEY = "ipa-quest-v1"
TAG = "hud-20261108"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
L_EXPECT = 19254.5
D_PREVIEW = {"follow": 1482.0, "listen": 1620.0}   # span*L + 0.5*preview*speed（里程）
LEAD = {"follow": 1036.0, "listen": 1107.0}        # beginDecide 播音阈值（里程）

RESULTS = []
NOTES = []


def chk(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + ("  | " + str(detail) if detail else ""))
    return bool(ok)


def note(name, detail=""):
    """CONCERNS / 观测不到但不应误判为 FAIL 的事项，单列披露、不计入 PASS/FAIL。"""
    NOTES.append((name, detail))
    print("  NOTE  " + name + ("  | " + str(detail) if detail else ""))


def read(p):
    with open(p, encoding="utf-8", errors="replace", newline="") as f:
        return f.read()


class Quiet(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".mjs": "text/javascript", ".js": "text/javascript",
        ".opus": "audio/ogg", ".mp3": "audio/mpeg", ".webp": "image/webp",
    }

    def log_message(self, *a):
        pass

    def handle(self):
        # 导航/重载会取消在途资源请求，客户端断连属正常现象，不打到 stderr
        try:
            super().handle()
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError, OSError):
            pass


# ---------------------------------------------------------------------------
# 浏览器侧测试夹具：注入一次即可。
#  * __qa.step 持有 __rally._stepping=true 抑制 rAF 自动步进 —— 所有帧推进只由脚本
#    显式驱动，避免墙钟/真实 rAF 在断言间偷偷推进仿真（verify_cseg_ui.py 的 step()
#    会在收尾把 _stepping 置回 false，故这里每次 step 后重新置位）。
#  * __qa.setGate 把 player.odo 直接摆到指定门前距离，并把拾取物标记 taken、
#    清空 quiz/decide、把对手挪开，隔离出纯粹的 S0/S1/S2 状态机观测窗口。
# ---------------------------------------------------------------------------
QA_JS = r"""
(() => {
  const R = window.__rally;
  const Q = window.__qa = {};
  Q.setItemCount = 0;
  const orig = Storage.prototype.setItem;
  Storage.prototype.setItem = function (...a) { Q.setItemCount++; return orig.apply(this, a); };
  Q.step = (n) => { R.step(n == null ? 1 : n); R._stepping = true; };
  R._stepping = true;
  Q.snap = () => {
    const mm = document.querySelector('#minimap');
    const sg = document.querySelector('#signs');
    const s = R.race ? R.race.state : null;
    return {
      mode: R.mode, boardOpen: R.boardOpen, shopOpen: R.shopOpen, race: !!R.race,
      simTime: R.simTime, odo: (s && s.player) ? s.player.odo : null, lap: s ? s.lap : null,
      mmHidden: mm ? mm.hidden : null, signsHidden: sg ? sg.hidden : null,
      setItemCount: Q.setItemCount
    };
  };
  Q.model = () => {
    try {
      if (typeof R.minimapModel === 'function') return {src:'__rally.minimapModel()', data: R.minimapModel()};
      if (R.minimapData !== undefined)          return {src:'__rally.minimapData',    data: R.minimapData};
      if (typeof window.minimapModel === 'function') return {src:'window.minimapModel()', data: window.minimapModel()};
    } catch (e) { return {src:'error', data:null, error:String(e)}; }
    return {src:null, data:null};
  };
  Q.minimapRect = () => {
    try { return (typeof R.minimapRect === 'function') ? R.minimapRect() : null; }
    catch (e) { return {__error:String(e)}; }
  };
  Q.mmInfo = () => {
    const m = document.querySelector('#minimap');
    if (!m) return null;
    const c = m.querySelector('#minimap-c') || m.querySelector('canvas');
    const lap = m.querySelector('#minimap-lap');
    const cs = getComputedStyle(m);
    const attrs = [];
    const walk = (e) => {
      for (const a of (e.attributes || [])) attrs.push([a.name, a.value]);
      for (const ch of (e.children || [])) walk(ch);
    };
    walk(m);
    return {
      exists:true, canvas: !!c, canvasId: c ? c.id : null, lap: !!lap,
      aria: m.getAttribute('aria-hidden'), pe: cs.pointerEvents, bg: cs.backgroundColor,
      z: cs.zIndex, position: cs.position, hidden: m.hidden,
      text: m.textContent, html: m.innerHTML, attrs: attrs,
      canvasW: c ? c.width : null, canvasH: c ? c.height : null,
      dpr: window.devicePixelRatio || 1
    };
  };
  Q.gateFaces = () => {
    const s = R.race ? R.race.state : null;
    if (!s) return [];
    const disp = window.IPA_DISPLAY || {};
    return s.gates.map(g => {
      const parts = [g.spoken, g.other, g.left, g.right].filter(Boolean);
      return {
        id:g.id, lap:g.lap, lineT:g.lineT, line:g.line,
        words: parts.map(p => p.word).filter(Boolean),
        ipas:  parts.map(p => p.ipa).filter(Boolean),
        disps: parts.map(p => (disp[p.unit] ? disp[p.unit].displayIpa : null)).filter(Boolean)
      };
    });
  };
  Q.geom = (sel) => {
    const e = document.querySelector(sel);
    if (!e) return null;
    const r = e.getBoundingClientRect(), cs = getComputedStyle(e);
    return {left:r.left, top:r.top, right:r.right, bottom:r.bottom,
            width:r.width, height:r.height, hidden:e.hidden,
            pe:cs.pointerEvents, z:cs.zIndex, padRight:cs.paddingRight};
  };
  Q.hudChildren = () => {
    const out = [];
    document.querySelectorAll('#hud .hud-row > *').forEach(e => {
      const r = e.getBoundingClientRect();
      out.push({id:e.id || e.className || e.tagName,
                left:r.left, top:r.top, right:r.right, bottom:r.bottom});
    });
    return out;
  };
  Q.signs = () => {
    const sg = document.querySelector('#signs');
    const l = document.querySelector('#sign-l'), r = document.querySelector('#sign-r');
    const info = (e) => {
      if (!e) return null;
      const b = e.getBoundingClientRect(), cs = getComputedStyle(e);
      return {text:(e.textContent||'').trim(), className:e.className||'', html:e.innerHTML,
              opened:(e.dataset ? (e.dataset.opened||'') : ''), width:b.width, opacity:cs.opacity};
    };
    return {hidden: sg ? sg.hidden : null, inner: sg ? sg.innerHTML : '',
            count: sg ? sg.children.length : -1,
            signClassCount: sg ? sg.querySelectorAll('.sign').length : -1,
            l:info(l), r:info(r)};
  };
  Q.setGate = (played, dist, lapIndex) => {
    const s = R.race ? R.race.state : null;
    if (!s) return null;
    s.pickups.forEach(p => { p.taken = true; });
    s.quiz = null; s.decide = null;
    const gi = (lapIndex || 0) * 2;   // 每圈 2 门：lap0 -> gates[0]，lap1 -> gates[2]
    const g = s.gates[gi];
    s.gates.forEach((x, i) => { if (i < gi) { x.played = true; x.judged = true; x.hit = true; } });
    g.played = !!played; g.judged = false; g.hit = false;
    g.unheard = false; g.replayed = false; g.holdDone = false;
    s.player.odo = g.line - dist;
    s.player.t = ((s.player.odo % s.track.length) + s.track.length) % s.track.length / s.track.length;
    s.player.lateral = 0; s.player.laneTarget = 0;
    s.lap = lapIndex || 0;
    s.finished = false;
    s.rivals.forEach((rv, i) => {
      rv.odo = s.player.odo - 800 - i*300;
      rv.lateral = i ? 0.55 : -0.55; rv.laneTarget = rv.lateral;
    });
    return {id:g.id, lap:g.lap, line:g.line, dist:g.line - s.player.odo,
            leftWord:g.left.word, rightWord:g.right.word,
            leftIpa:g.left.ipa, rightIpa:g.right.ipa};
  };
  Q.quizInject = () => {
    const s = R.race.state, g = s.gates[0];
    s.quiz = {spoken:g.spoken, options:[g.spoken, g.other], reason:'wall',
              qType:'word', pairKey:g.pairKey};
    return {word:g.spoken.word};
  };
  Q.finish = () => {
    const s = R.race.state;
    s.gates.forEach(g => { g.played = true; g.judged = true; g.hit = true; });
    s.gateHits = s.gates.length;
    s.finished = true;
    s.finishTime = Math.max(0, s.time - 1.2);
  };
  Q.showBanner = (on) => { const b = document.querySelector('#banner'); if (b) b.hidden = !on; };
  return true;
})()
"""


def install_qa(page):
    return page.evaluate(QA_JS)


def boot(page, url_rally, diff_id=None):
    """导航到拉力赛、关掉首次「玩法」说明、装夹具、可选定档，返回是否到达 title。"""
    page.goto(url_rally, wait_until="domcontentloaded")
    page.wait_for_function("!!window.__rally", timeout=15000)
    page.wait_for_timeout(400)
    page.evaluate("() => { const b = document.querySelector('#how-close'); if (b) b.click(); }")
    page.wait_for_timeout(120)
    install_qa(page)
    if diff_id:
        page.click("#btn-" + diff_id)
        page.evaluate("() => window.__qa.step(1)")
    return True


def into_racing(page, frames=260):
    # 辅助 context 从 title 起：先经 #btn-<diff> 进 teach，#btn-grid 才可见；
    # 若 boot() 已定档（mode=teach），跳过这一步直接进 countdown。
    if page.evaluate("() => window.__rally.mode") == "title":
        page.click("#btn-listen")
        page.evaluate("() => window.__qa.step(1)")
    page.click("#btn-grid")
    page.evaluate("() => window.__qa.step(1)")
    page.evaluate("(n) => window.__qa.step(n)", frames)
    return page.evaluate("() => window.__qa.snap()")


def snap(page):
    return page.evaluate("() => window.__qa.snap()")


def alpha_of(color):
    """从 rgb()/rgba() 解析 alpha；rgb() 视为 1.0。"""
    if not color:
        return None
    m = re.search(r"rgba?\(([^)]+)\)", color)
    if not m:
        return None
    parts = [x.strip() for x in m.group(1).split(",")]
    if len(parts) >= 4:
        try:
            return float(parts[3])
        except ValueError:
            return None
    return 1.0


def collect_keys(obj, acc):
    if isinstance(obj, dict):
        for k, v in obj.items():
            acc.append(k)
            collect_keys(v, acc)
    elif isinstance(obj, list):
        for v in obj:
            collect_keys(v, acc)


def intersects(a, b):
    if not a or not b:
        return False
    return not (a["right"] <= b["left"] or b["right"] <= a["left"]
                or a["bottom"] <= b["top"] or b["bottom"] <= a["top"])


# ---------------------------------------------------------------------------
def main():
    server = ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    PORT = server.server_address[1]

    def url(rel):
        return "http://127.0.0.1:%d/%s" % (PORT, urllib.parse.quote(rel, safe="/"))

    U_RALLY = url("音标拉力赛/index.html")
    U_QUEST = url("音标大闯关/index.html")
    print("SERVER", PORT)

    from playwright.sync_api import sync_playwright

    errs = {"pageerror": 0, "console_error": 0, "requestfailed": 0, "bad_status": 0}
    FAILS = []          # (url, failure) 全量明细
    CONSOLE_ERRS = []   # console.error 文本明细
    ABORTED = []        # ERR_ABORTED（reload/导航主动取消）
    REAL = []           # 同源真实网络失败
    EXTERNAL = []       # 外链字体等非产品失败

    def watch(page):
        def on_fail(r):
            f = str(r.failure)
            errs["requestfailed"] += 1
            FAILS.append((r.url, f))
            if "ERR_ABORTED" in f:
                ABORTED.append(r.url)
            elif "127.0.0.1" in r.url or "localhost" in r.url:
                REAL.append((r.url, f))
            else:
                EXTERNAL.append((r.url, f))
        page.on("pageerror", lambda e: errs.__setitem__("pageerror", errs["pageerror"] + 1))
        page.on("console", lambda m: (errs.__setitem__("console_error", errs["console_error"] + 1),
                                      CONSOLE_ERRS.append(m.text)) if m.type == "error" else None)
        page.on("requestfailed", on_fail)
        page.on("response", lambda r: errs.__setitem__("bad_status", errs["bad_status"] + 1)
                if r.status >= 400 else None)

    H2_OBS = []
    H12_OBS = {}

    def h2(label, expect_hidden, s, precond=True, precond_detail=""):
        ok = (s.get("mmHidden") == expect_hidden) and bool(precond)
        H2_OBS.append((label, ok, {
            "mode": s.get("mode"), "boardOpen": s.get("boardOpen"),
            "shopOpen": s.get("shopOpen"), "mmHidden": s.get("mmHidden"),
            "期望 hidden": expect_hidden, "前置条件": precond_detail or precond,
        }))
        return ok

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=CHROME)
        ctx = browser.new_context(viewport={"width": 1280, "height": 800})
        page = ctx.new_page()
        watch(page)
        boot(page, U_RALLY)

        # ------------------------------------------------------------ 优雅报错前置
        ready = page.evaluate("""() => ({
          rally: !!window.__rally,
          mm: !!document.querySelector('#minimap'),
          mmc: !!document.querySelector('#minimap-c'),
          mmlap: !!document.querySelector('#minimap-lap'),
          rect: typeof (window.__rally && window.__rally.minimapRect) === 'function',
          model: typeof (window.__rally && window.__rally.minimapModel) === 'function',
          tagInHtml: (document.documentElement.outerHTML.match(/\\?v=([A-Za-z0-9\\-]+)/) || [])[1] || null
        })""")
        static_tag_now = re.findall(r"\?v=([A-Za-z0-9\-]+)",
                                    read(os.path.join(RALLY, "index.html")))
        if not (ready["rally"] and ready["mm"] and ready["mmc"]):
            print("\n" + "=" * 60)
            print("HUD 元素未就绪，请先完成 #4")
            print("  检测：window.__rally=%s / #minimap=%s / #minimap-c=%s / #minimap-lap=%s"
                  % (ready["rally"], ready["mm"], ready["mmc"], ready["mmlap"]))
            print("  当前 index.html 的 ?v= 字面量：%s（期望 %s）"
                  % (sorted(set(static_tag_now)) or "无", TAG))
            print("  本脚本用于 #4 落地后的 HUD 验收；当前 DOM/钩子尚未提供，已跳过全部断言。")
            print("SUMMARY: 0 PASS / 0 FAIL / 0 TOTAL  | HUD_NOT_READY")
            print("=" * 60)
            server.shutdown()
            server.server_close()
            sys.exit(2)
        if not ready["rect"]:
            note("H1/H4 __rally.minimapRect() 未暴露",
                 "脚本改用 getBoundingClientRect() 取矩形；若 #4 计划提供该 getter 请补挂")
        if not ready["model"]:
            note("H6/H10 __rally.minimapModel() 未暴露",
                 "H6 将按规格报 FAIL；可选解法：挂到 __rally / 暴露 minimapData / 改用 view.minimapData")
        print("  READY  #minimap 已就绪 | tag(html)=%s | rect=%s model=%s"
              % (ready["tagInHtml"], ready["rect"], ready["model"]))

        # H12 真·开赛前基线：title 态取 rally 三字段，稍后在 racing（results 写盘之前）复取
        H12_OBS["rally_before"] = page.evaluate(
            "k => { const d = JSON.parse(localStorage.getItem(k)||'{}').rally || {}; "
            "return {unlocked:d.unlocked||null, maps:d.maps||null, EP02:d.EP02||null}; }", KEY)

        # ------------------------------------------------------------ H1
        print("\n=== H1 DOM 存在性与属性 ===")
        mm = page.evaluate("() => window.__qa.mmInfo()")
        a = alpha_of(mm["bg"])
        chk("H1 #minimap / #minimap-c / #minimap-lap 存在且属性符合规格",
            mm["exists"] and mm["canvas"] and mm["canvasId"] == "minimap-c" and mm["lap"]
            and mm["aria"] == "true" and mm["pe"] == "none"
            and mm["position"] == "fixed" and mm["z"] == "5"
            and a is not None and a >= 0.82,
            {"canvasId": mm["canvasId"], "lap": mm["lap"], "aria": mm["aria"],
             "pointerEvents": mm["pe"], "bg": mm["bg"], "alpha": a,
             "zIndex": mm["z"], "position": mm["position"],
             "canvasBitmap": [mm["canvasW"], mm["canvasH"]], "dpr": mm["dpr"]})

        # ------------------------------------------------------------ H11 运行时 + 静态
        print("\n=== H11 缓存串 / 图片 URL / 资源送达 ===")
        resnames = page.evaluate("() => performance.getEntriesByType('resource').map(r => r.name)")
        tagged = [n for n in resnames if "?v=" in n]
        tagged_bad = [n for n in tagged
                      if re.search(r"\.(js|css|webp|png)(\?|$)", n) and TAG not in n]
        ipa_ok = page.evaluate("() => !!(window.IPA_DISPLAY && window.IPA_DISPLAY.U11 && window.IPA_DISPLAY.U11.displayIpa === 'ɜr')")
        byte_ok, byte_detail = True, {}
        for rel in ("音标拉力赛/index.html", "音标拉力赛/js/main.js",
                    "音标大闯关/js/ipa-display.js"):
            try:
                got = urllib.request.urlopen(url(rel), timeout=8).read()
                local = open(os.path.join(ROOT, rel), "rb").read()
                same = got == local
                byte_ok = byte_ok and same
                byte_detail[rel] = {"字节相等": same, "送达字节": len(got), "本地字节": len(local)}
            except Exception as e:
                byte_ok = False
                byte_detail[rel] = str(e)

        tags, img_urls, bare = {}, [], []
        strlit = re.compile(r"""["'`]([^"'`\n]*\.(?:webp|png)[^"'`\n]*)["'`]""")
        concat = re.compile(r"""["'`]([^"'`\n]*assets/img/)["'`]\s*\+\s*[^,;)\n]{1,60}""")
        for base in (QUEST, RALLY):
            for dp, _, fns in os.walk(base):
                for fn in fns:
                    if not fn.endswith((".html", ".js", ".css")):
                        continue
                    p = os.path.join(dp, fn)
                    rel = os.path.relpath(p, base).replace("\\", "/")
                    if rel.startswith(("assets/", "docs/", "sprite_gen/")):
                        continue
                    t = read(p)
                    for v in re.findall(r"\?v=([A-Za-z0-9\-]+)", t):
                        tags[v] = tags.get(v, 0) + 1
                    for m in strlit.finditer(t):
                        u = m.group(1)
                        if "/" not in u:
                            continue
                        img_urls.append((rel, u))
                        if ("?v=" + TAG) not in u and "${CACHE_TAG}" not in u:
                            bare.append((rel, "LITERAL " + u))
                    for m in concat.finditer(t):
                        seg = t[m.start():m.end()]
                        if ("?v=" + TAG) not in seg:
                            bare.append((rel, "CONCAT " + seg.strip()))
        cfg = read(os.path.join(RALLY, "js", "config.js"))
        cache_tag_ok = ('CACHE_TAG = "%s"' % TAG) in cfg
        # 所有 <img src>/<link href>/<script src>/ESM import 的本地静态资源必须带 ?v=
        bare_src = []
        for base in (QUEST, RALLY):
            for dp, _, fns in os.walk(base):
                for fn in fns:
                    if not fn.endswith((".html", ".js")):
                        continue
                    p = os.path.join(dp, fn)
                    rel = os.path.relpath(p, base).replace("\\", "/")
                    if rel.startswith(("assets/", "docs/", "sprite_gen/")):
                        continue
                    t = read(p)
                    for u in re.findall(r"""(?:src|href)\s*=\s*["']([^"']+\.(?:js|css|webp|png))["']""", t):
                        if "?v=" not in u:
                            bare_src.append((rel, u))
                    for u in re.findall(r"""from\s+["']([^"']+\.js)["']""", t):
                        if "?v=" not in u:
                            bare_src.append((rel, u))
        chk("H11 tag 唯一且恰好 46 处 / CACHE_TAG 同步 / 20 个图片 URL 零裸引用 / 资源按字节送达",
            set(tags) == {TAG} and tags.get(TAG, 0) == 46
            and cache_tag_ok and len(img_urls) == 20 and not bare and not bare_src
            and not tagged_bad and ipa_ok and byte_ok,
            {"tag 直方图": tags, "CACHE_TAG 同步": cache_tag_ok,
             "图片 URL 字面量": len(img_urls), "裸引用": bare[:5], "裸 src/import": bare_src[:5],
             "带 tag 请求数": len(tagged), "带错 tag 的请求": tagged_bad[:5],
             "IPA_DISPLAY.U11=ɜr": ipa_ok, "按字节比对": byte_ok,
             "字节明细": byte_detail})

        # ------------------------------------------------------------ H2 显隐矩阵（部分 1）
        print("\n=== H2 显隐矩阵 ===")
        h2("title", True, snap(page), precond=(snap(page)["mode"] == "title"),
           precond_detail="mode==='title'")
        page.click("#btn-listen")
        page.evaluate("() => window.__qa.step(1)")
        h2("teach", True, snap(page), precond=(snap(page)["mode"] == "teach"),
           precond_detail="mode==='teach'")
        page.click("#btn-grid")
        page.evaluate("() => window.__qa.step(1)")
        h2("countdown", False, snap(page), precond=(snap(page)["mode"] == "countdown"),
           precond_detail="mode==='countdown'")
        s_racing = page.evaluate("(n) => { window.__qa.step(n); return window.__qa.snap(); }", 260)
        h2("racing", False, s_racing, precond=(s_racing["mode"] == "racing"),
           precond_detail="mode==='racing'")

        # ------------------------------------------------------------ H5 / H6
        print("\n=== H5 小地图不含答案文本 / H6 数据接口无答案键 ===")
        # 【#5 主理人裁决 · H5 假阳性修正】
        #   检测面 = 用户可见文本(mm.textContent) + 后代元素的所有属性值
        #            (含 alt / aria-label / title / data-*；遍历全量属性，不缩小)
        #   不含 mm.innerHTML 源码字面量 —— `<span id="minimap-lap">` 标签名中的
        #   "span" 会让 83 词全表里的 "pan"（pen/pan 对）假阳性。这是测试脚本假阳性，
        #   不是产品缺陷；Q1 的 DOM 契约（含 #minimap-lap）保持不动。
        #   词表 = allWords() 83 词全表 + 4 个答案域名 + 4 门 IPA/displayIpa（保留）。
        #   【防放宽铁律】83 词全表与字段名一个不少、不缩小词表、不降级为 warn，
        #   仍是硬 chk；并把「词表恰为 83 且不重复」本身也写成判据。
        vocab = []
        try:
            vocab = page.evaluate("""async (tag) => {
              const cfg = await import('/音标拉力赛/js/config.js?v=' + tag);
              return cfg.allWords();
            }""", TAG) or []
        except Exception as e:
            note("H5 allWords() 动态取词失败", "%s: %s" % (type(e).__name__, e))
        faces = page.evaluate("() => window.__qa.gateFaces()")
        mm2 = page.evaluate("() => window.__qa.mmInfo()")
        attr_pairs = mm2.get("attrs") or []
        surface = ",".join([mm2.get("text") or ""] + [str(v) for _, v in attr_pairs])
        surface_l = surface.lower()
        FIELD_NAMES = ("correctLateral", "spoken", "left", "right")
        tokens = set(w for w in vocab if w)             # 83 词全表，不过滤短词
        tokens.update(FIELD_NAMES)                      # 4 个答案域名
        for g in faces:                                  # 4 门 IPA / displayIpa（保留原检测）
            for w in g["words"]:
                if len(w) >= 2:
                    tokens.add(w)
            for ipa in (g["ipas"] + g["disps"]):
                tokens.add("/" + ipa + "/")              # 可见斜杠形式，避免单字母 IPA 误伤
        bad_hits = sorted(t for t in tokens if t and t.lower() in surface_l)
        FORBID_KEYS = {"correctLateral", "spoken", "left", "right", "pairKey", "qType",
                       "displayIpa", "answer", "correct", "options", "other", "hit",
                       "word", "ipa", "label", "sym"}
        FORBID_ATTR = re.compile(r"data-(lane|correct|side|answer|left|right|word|ipa|spoken)", re.I)
        bad_cn = [k for k in ("答案", "正确") if k in surface_l]
        bad_attrs = [name for name, _ in attr_pairs if FORBID_ATTR.search(name)]
        # 诊断项（不计判定）：证明 innerHTML 里的 <span> 确实是假阳性来源
        html_l = (mm2.get("html") or "").lower()
        html_fp = sorted(t for t in tokens if t and t.lower() in html_l)
        vocab_ok = (len(vocab) == 83 and len(set(vocab)) == 83)
        chk("H5 83 词全表+4 字段名+IPA 在可见文本/属性值零命中（不含 innerHTML 源码字面量）/ 禁用 data-*",
            vocab_ok and len(faces) == 4 and not bad_hits and not bad_cn and not bad_attrs,
            {"检测面口径": "mm.textContent + 后代所有属性值；已排除 mm.innerHTML（#5 裁决，避 `<span` 撞 pan）",
             "allWords() 词表数": len(vocab), "词表恰为 83 且不重复": vocab_ok,
             "字段名": list(FIELD_NAMES), "扫描 token 总数": len(tokens),
             "门数": len(faces), "检测面字符数": len(surface),
             "命中答案词面/字段名/IPA": bad_hits[:8], "命中中文答案域关键字": bad_cn,
             "禁用属性名": bad_attrs, "mm.textContent": (mm2.get("text") or "")[:60],
             "innerHTML 仅诊断不计判定": True,
             "innerHTML 假阳性命中(证据)": html_fp[:8],
             "检测面属性值明细": attr_pairs})

        model = page.evaluate("() => window.__qa.model()")
        if model["data"] is None:
            chk("H6 minimapModel 数据接口无答案键 + nextGate 键集合精确相等", False,
                {"原因": "minimapModel()/minimapData 均未在 window.__rally 暴露，无法按 H6 扫描键名",
                 "探测到的入口": model["src"], "error": model.get("error"),
                 "处置建议": "请 #4 补挂只读 minimapModel()；或改用 view.minimapData 后同步调整 H6"})
            h6_ok = False
        else:
            keys = []
            collect_keys(model["data"], keys)
            bad_keys = sorted({k for k in keys if k in FORBID_KEYS})
            ng = model["data"].get("nextGate") if isinstance(model["data"], dict) else None
            expect_ng = {"id", "lap", "line", "distance", "secondsTo"}
            ng_keys_ok = (ng is None) or (isinstance(ng, dict) and set(ng.keys()) == expect_ng)
            h6_ok = not bad_keys and ng_keys_ok
            chk("H6 minimapModel 数据接口无答案键 + nextGate 键集合精确相等", h6_ok,
                {"入口": model["src"], "键总数": len(keys), "命中禁用键": bad_keys,
                 "nextGate": ng, "nextGate 键集合正确": ng_keys_ok})
            if ng is None:
                note("H6 nextGate 当前为 null", "无临近门时允许为 null；H10 会在 D_preview 内复测 lap===1")

        # ------------------------------------------------------------ H7 / H8 状态机（listen）
        print("\n=== H7 路牌 D_preview 阈值 / H8 S1 零文本与 S2 对称（listen 1620 里程）===")
        h7, h8 = {}, {}

        def walk_states(pg, diff_id):
            dp = D_PREVIEW[diff_id]
            out = {}
            # S0：dist > D_preview
            gate = pg.evaluate("([p,d]) => window.__qa.setGate(p,d,0)", [False, dp + 50])
            pg.evaluate("() => window.__qa.step(1)")
            out["S0"] = {"gate": gate, "signs": pg.evaluate("() => window.__qa.signs()")}
            # S1：dist = D_preview - 20 且 !played
            gate = pg.evaluate("([p,d]) => window.__qa.setGate(p,d,0)", [False, dp - 20])
            pg.evaluate("() => window.__qa.step(1)")
            out["S1"] = {"gate": gate, "signs": pg.evaluate("() => window.__qa.signs()")}
            # S2：dist = D_preview - 20 且 played
            gate = pg.evaluate("([p,d]) => window.__qa.setGate(p,d,0)", [True, dp - 20])
            pg.evaluate("() => window.__qa.step(1)")
            out["S2"] = {"gate": gate, "signs": pg.evaluate("() => window.__qa.signs()")}
            return out

        h7["listen"] = walk_states(page, "listen")

        # 清理：把门拨回未播放，避免后续 H9/H10 残留
        page.evaluate("() => { const s=window.__rally.race.state; "
                      "s.gates.forEach(g=>{g.played=false;g.judged=false;g.hit=false;}); }")

        def s_ok(v, diff_id):
            dp = D_PREVIEW[diff_id]
            g0, g1, g2 = v["S0"]["gate"], v["S1"]["gate"], v["S2"]["gate"]
            return {
                "S0 隐藏": v["S0"]["signs"]["hidden"] is True and g0["dist"] > dp,
                "S1 显示": v["S1"]["signs"]["hidden"] is False and g1["dist"] <= dp,
                "S2 显示": v["S2"]["signs"]["hidden"] is False and g2["dist"] <= dp,
                "两牌恒 2 块": all(v[k]["signs"]["count"] == 2 for k in ("S0", "S1", "S2")),
                "阈值里程": [g0["dist"], g1["dist"], g2["dist"]],
            }

        def s_sym(v):
            s1, s2 = v["S1"]["signs"], v["S2"]["signs"]
            l1, r1, l2, r2 = s1["l"], s1["r"], s2["l"], s2["r"]
            no_letters = lambda t: not re.search(r"[A-Za-z/]", t or "")
            s1_zero = (l1 and r1 and no_letters(l1["text"]) and no_letters(r1["text"]))
            s1_neutral = (l1 and r1 and not re.search(r"is-long|is-short", l1["className"])
                          and not re.search(r"is-long|is-short", r1["className"]))
            s1_sym = (l1 and r1 and abs(l1["width"] - r1["width"]) <= 1
                      and l1["opacity"] == r1["opacity"] and l1["className"] == r1["className"])
            g = v["S2"]["gate"]
            s2_words = (l2 and r2 and g["leftWord"] in l2["text"] and g["rightWord"] in r2["text"]
                        and ("/" + g["leftIpa"] + "/") in l2["text"]
                        and ("/" + g["rightIpa"] + "/") in r2["text"]
                        and l2["text"] != r2["text"])
            s2_sym = (l2 and r2 and abs(l2["width"] - r2["width"]) <= 1
                      and l2["opacity"] == r2["opacity"])
            no_hint = (l2 and r2
                       and not re.search(r"ok|bad|correct|answer", l2["className"] + " " + r2["className"])
                       and not re.search(r"正确|答案|correctLateral", s2["inner"]))
            return {"S1 零文本": s1_zero, "S1 中性无长短音着色": s1_neutral, "S1 双侧对称": s1_sym,
                    "S2 含两侧 word 与 /ipa/ 且互异": s2_words, "S2 双侧同宽同不透明度": s2_sym,
                    "S2 无单侧高亮/答案字样": no_hint,
                    "S1 文本": [l1["text"] if l1 else None, r1["text"] if r1 else None],
                    "S2 文本": [l2["text"] if l2 else None, r2["text"] if r2 else None]}

        h8["listen"] = s_sym(h7["listen"])

        # ------------------------------------------------------------ H9 quiz 冻结
        print("\n=== H9 quiz 冻结（#signs.hidden / simTime / odo / 零写盘 / 回 racing 复原）===")
        # 先摆出可见的 S2，作为「进 quiz 前」的对照
        gate_before = page.evaluate("([p,d]) => window.__qa.setGate(p,d,0)",
                                    [True, D_PREVIEW["listen"] - 20])
        page.evaluate("() => window.__qa.step(1)")
        signs_before = page.evaluate("() => window.__qa.signs()")
        pre = snap(page)
        page.evaluate("() => window.__qa.quizInject()")
        page.evaluate("() => window.__qa.step(1)")
        in_quiz = snap(page)
        signs_quiz = page.evaluate("() => window.__qa.signs()")
        c0 = in_quiz["setItemCount"]
        page.evaluate("() => window.__qa.step(60)")
        post = snap(page)
        c1 = post["setItemCount"]
        h2("quiz", False, in_quiz,
           precond=(in_quiz["mode"] == "quiz" and signs_quiz["hidden"] is True
                    and post["simTime"] == in_quiz["simTime"]
                    and post["odo"] == in_quiz["odo"]),
           precond_detail="mode==='quiz' 且路牌隐藏且冻结前后数值相等")
        freeze_ok = (in_quiz["mode"] == "quiz"
                     and signs_quiz["hidden"] is True
                     and in_quiz["mmHidden"] is False
                     and post["simTime"] == in_quiz["simTime"]
                     and post["odo"] == in_quiz["odo"]
                     and post["mmHidden"] is False
                     and (c1 - c0) == 0)
        # 答完回 racing（pickQuiz 用 850ms setTimeout 切回 racing）
        page.locator("#quiz-options button").first.click()
        page.wait_for_timeout(1000)
        page.evaluate("() => window.__qa.step(1)")
        after = snap(page)
        signs_after = page.evaluate("() => window.__qa.signs()")
        restore_ok = (after["mode"] == "racing" and signs_after["hidden"] is False
                      and signs_after["l"] and signs_before["l"]
                      and signs_after["l"]["text"] == signs_before["l"]["text"]
                      and signs_after["r"]["text"] == signs_before["r"]["text"])
        chk("H9 quiz 冻结数值不变 / #signs.hidden=true / setItem 零写入 / 回 racing 路牌无缝重现",
            freeze_ok and restore_ok,
            {"进 quiz 前": {"mode": pre["mode"], "simTime": pre["simTime"], "odo": pre["odo"],
                          "signsHidden": signs_before["hidden"]},
             "quiz 中": {"mode": in_quiz["mode"], "mmHidden": in_quiz["mmHidden"],
                       "signsHidden": signs_quiz["hidden"], "simTime": in_quiz["simTime"],
                       "odo": in_quiz["odo"]},
             "step(60) 后": {"simTime": post["simTime"], "odo": post["odo"],
                           "mmHidden": post["mmHidden"]},
             "setItem 增量": c1 - c0, "冻结判定": freeze_ok,
             "回 racing": {"mode": after["mode"], "signsHidden": signs_after["hidden"]},
             "路牌文本复原": [signs_after["l"]["text"] if signs_after["l"] else None,
                          signs_after["r"]["text"] if signs_after["r"] else None],
             "复原判定": restore_ok})

        # ------------------------------------------------------------ H2 面板特例 + paused 零写盘
        page.click("#btn-pause")
        page.evaluate("() => window.__qa.step(1)")
        s_paused = snap(page)
        h2("paused", False, s_paused, precond=(s_paused["mode"] == "paused"),
           precond_detail="mode==='paused'")
        z0 = s_paused["setItemCount"]
        page.evaluate("() => window.__qa.step(300)")
        z1 = snap(page)["setItemCount"]
        H12_OBS["frozen_write_delta"] = z1 - z0
        page.click("#btn-resume")
        page.evaluate("() => window.__qa.step(1)")

        # 清理 quiz 残留状态（pickQuiz 已置空，但保险起见）
        page.evaluate("() => { const s=window.__rally.race.state; s.quiz=null; s.decide=null; }")

        page.evaluate("() => document.querySelector('#btn-board').click()")
        page.evaluate("() => window.__qa.step(1)")
        s_board = snap(page)
        h2("boardOpen（mode 仍 racing）", True, s_board,
           precond=(s_board["mode"] == "racing" and s_board["boardOpen"] is True),
           precond_detail="mode==='racing' && boardOpen===true")
        page.evaluate("() => document.querySelector('#board-close').click()")
        page.evaluate("() => window.__qa.step(1)")

        # #how 在 racing 下被 setMode 隐藏，故用 DOM .click() 触发既有 onclick（不校验可见性）
        page.evaluate("() => document.querySelector('#how-shop').click()")
        page.evaluate("() => window.__qa.step(1)")
        s_shop = snap(page)
        h2("shopOpen（mode 仍 racing）", True, s_shop,
           precond=(s_shop["mode"] == "racing" and s_shop["shopOpen"] is True),
           precond_detail="mode==='racing' && shopOpen===true")
        page.evaluate("() => document.querySelector('#how-tab').click()")
        page.evaluate("() => window.__qa.step(1)")

        # H12 开赛后 rally 字段（须在 results 写盘之前取）
        H12_OBS["rally_after"] = page.evaluate(
            "k => { const d = JSON.parse(localStorage.getItem(k)||'{}').rally || {}; "
            "return {unlocked:d.unlocked||null, maps:d.maps||null, EP02:d.EP02||null}; }", KEY)

        # ------------------------------------------------------------ H10 两圈
        print("\n=== H10 两圈同 commitT 不重复 ===")
        g10 = page.evaluate("([p,d]) => window.__qa.setGate(p,d,1)",
                            [True, D_PREVIEW["listen"] - 20])
        page.evaluate("() => window.__qa.step(1)")
        sg10 = page.evaluate("() => window.__qa.signs()")
        s10 = snap(page)
        lines = page.evaluate("() => window.__rally.race.state.gates.map(g=>({id:g.id,lap:g.lap,lineT:g.lineT,line:g.line}))")
        lineT_ok = all(abs(g["lineT"] - e) < 1e-9
                       for g, e in zip(lines, [0.24, 0.68, 1.24, 1.68]))
        diff_ok = (abs((lines[2]["line"] - lines[0]["line"]) - L_EXPECT) <= 1
                   and abs((lines[3]["line"] - lines[1]["line"]) - L_EXPECT) <= 1)
        m10 = page.evaluate("() => window.__qa.model()")
        ng10 = m10["data"].get("nextGate") if isinstance(m10.get("data"), dict) else None
        ng_lap_ok = (ng10 is None) or (ng10.get("lap") == 1)
        if ng10 is None:
            note("H10 nextGate 为 null", "无法核对 lap===1；若 #4 的 minimapModel 只在 D_preview 内给 nextGate，请复核本条")
        key10 = (sg10["l"]["opened"] if sg10["l"] else "") or (sg10["r"]["opened"] if sg10["r"] else "")
        key_ok = (not key10) or (key10.startswith(str(g10["id"]) + ":") and ":" in key10[len(str(g10["id"]) + ":"):])
        if not key10:
            note("H10 signKey 不可观测",
                 "#sign-l/#sign-r 的 data-opened 为空（#4 可能改了键载体）；已改以行为断言为主")
        h10 = (s10["lap"] == 1 and sg10["count"] <= 2 and sg10["hidden"] is False
               and lineT_ok and diff_ok and ng_lap_ok
               and g10["lap"] == 1 and g10["id"] == 2
               and (not key10 or key_ok))
        chk("H10 两圈同 commitT 不重复（lineT/line 差=L/lap=1/≤2 牌/signKey/第 2 圈正常出牌）",
            h10,
            {"state.lap": s10["lap"], "lineT": [g["lineT"] for g in lines], "lineT 正确": lineT_ok,
             "line 差=L": [round(lines[2]["line"] - lines[0]["line"], 2),
                         round(lines[3]["line"] - lines[1]["line"], 2)], "line 差正确": diff_ok,
             "当前门": {"id": g10["id"], "lap": g10["lap"]}, ".sign 块数": sg10["count"],
             "#signs.hidden": sg10["hidden"], "nextGate.lap": (ng10 or {}).get("lap"),
             "nextGate.lap 正确": ng_lap_ok, "signKey(data-opened)": key10, "signKey 形状": key_ok})

        # ------------------------------------------------------------ H2 results
        page.evaluate("() => window.__qa.finish()")
        page.evaluate("() => window.__qa.step(1)")
        s_res = snap(page)
        h2("results", True, s_res, precond=(s_res["mode"] == "results"),
           precond_detail="mode==='results'")

        chk("H2 显隐矩阵逐阶段断言（含 quiz 显示但冻结 / boardOpen·shopOpen 时 mode 仍 racing）",
            all(ok for _, ok, _ in H2_OBS),
            {label: {"ok": ok, **d} for label, ok, d in H2_OBS})

        # ------------------------------------------------------------ H7/H8 follow 档（另一 context）
        print("\n=== H7/H8 follow 档（1482 里程）复核 ===")
        ctx_f = browser.new_context(viewport={"width": 1280, "height": 800})
        p_f = ctx_f.new_page()
        watch(p_f)
        boot(p_f, U_RALLY, diff_id="follow")
        s_f = into_racing(p_f, 260)
        if s_f["mode"] != "racing":
            note("follow 档未能进入 racing", s_f)
        h7["follow"] = walk_states(p_f, "follow")
        h8["follow"] = s_sym(h7["follow"])
        ctx_f.close()

        h7_res = {k: s_ok(v, k) for k, v in h7.items()}
        h7_ok = all(all(x for key, x in d.items() if isinstance(x, bool)) for d in h7_res.values())
        chk("H7 路牌 S0 隐藏 / S1 在 D_preview 内出现 / S2 播音后出现（follow 1482 · listen 1620）",
            h7_ok, {"follow": h7_res["follow"], "listen": h7_res["listen"],
                    "阈值公式": "D_preview = fork*speed + 0.5*preview*speed（名义速度，非 speedNow）"})
        h8_ok = all(all(x for key, x in d.items() if isinstance(x, bool)) for d in h8.values())
        chk("H8 S1 零文本且双侧中性对称 / S2 两侧同帧同尺寸且含各自 word 与 /ipa/、无指向性",
            h8_ok, {"follow": h8["follow"], "listen": h8["listen"]})

        # ------------------------------------------------------------ H3 / H4 多视口
        print("\n=== H3 不溢出 / H4 位置不重叠（PC + 375 + 320）===")
        viewports = [("PC 1280×800", 1280, 800), ("触屏 375×667", 375, 667),
                     ("极窄 320×568", 320, 568)]
        geom_all = {}
        for label, wv, hv in viewports:
            c = browser.new_context(viewport={"width": wv, "height": hv})
            p = c.new_page()
            watch(p)
            boot(p, U_RALLY)
            s_v = into_racing(p, 260)
            g = p.evaluate("""() => {
              const Q = window.__qa;
              Q.showBanner(true);   // 临时显形以便量测；量完立即还原
              const out = {
                mm: Q.geom('#minimap'), hud: Q.geom('#hud'),
                banner: Q.geom('#banner'), route: Q.geom('#route-map'),
                quiz: Q.geom('#quiz'), children: Q.hudChildren(),
                padRight: Q.geom('#hud') ? Q.geom('#hud').padRight : null,
                rect: Q.minimapRect()
              };
              Q.showBanner(false);
              return out;
            }""")
            geom_all[label] = {"mode": s_v["mode"], "g": g}
            c.close()

        h3_res = {}
        for label, wv, hv in viewports:
            d = geom_all[label]
            r = d["g"]["mm"]
            limit_w = 112.5 if wv == 375 else (0.30 * wv if wv <= 640 else 160)
            ok = (d["mode"] == "racing" and r and r["hidden"] is False
                  and r["left"] >= 0 and r["right"] <= wv and r["top"] >= 0
                  and r["bottom"] < hv and r["width"] <= limit_w + 0.5)
            h3_res[label] = {"ok": ok, "rect": r, "width 上限": limit_w,
                             "viewport": [wv, hv]}
        chk("H3 375×667 / 320×568 / PC 下 #minimap 不溢出且宽度收敛",
            all(v["ok"] for v in h3_res.values()), h3_res)

        def overlap_view(label, wv):
            d = geom_all[label]["g"]
            mmr, ban, route, children = d["mm"], d["banner"], d["route"], d["children"]
            bad = []
            for c in children:
                if c["right"] > c["left"] and c["bottom"] > c["top"] and intersects(mmr, c):
                    bad.append("hud:" + str(c["id"]))
            if ban and ban["right"] > ban["left"] and intersects(mmr, ban):
                bad.append("#banner")
            if route and route["hidden"] is False and intersects(mmr, route):
                bad.append("#route-map")
            banner_gap = None
            if wv <= 640 and ban:
                banner_gap = ban["top"] - mmr["bottom"]
                # 规格要求 >= 12px；留 0.5px 亚像素容差，仍能拦住现状的 6px 间隙
                if banner_gap < 11.5:
                    bad.append("#banner 与 mm 的垂直间距 < 12px")
            # #quiz 按规格是 z-index 层叠（.panel z=8 > #minimap z=5），不做几何不相交断言
            z_mm = int(mmr["z"]) if mmr and str(mmr["z"]).lstrip("-").isdigit() else None
            z_quiz = int(d["quiz"]["z"]) if d["quiz"] and str(d["quiz"]["z"]).lstrip("-").isdigit() else None
            z_ok = (z_mm is not None and z_quiz is not None and z_quiz > z_mm)
            gutter_ok = True
            if wv <= 640 and d["padRight"]:
                try:
                    gutter_ok = float(d["padRight"].replace("px", "")) >= 100
                except ValueError:
                    gutter_ok = False
            return {"重叠项": bad, "banner 垂直间距": banner_gap,
                    "mm.z": z_mm, "quiz.z": z_quiz, "quiz 层叠正确": z_ok,
                    "hud padding-right": d["padRight"], "gutter 生效": gutter_ok,
                    "ok": not bad and z_ok and gutter_ok}

        h4_res = {"PC 1280×800": overlap_view("PC 1280×800", 1280),
                  "触屏 375×667": overlap_view("触屏 375×667", 375),
                  "极窄 320×568": overlap_view("极窄 320×568", 320)}
        note("H4 #quiz 口径",
             "spec §2.1.4/§2.1.6：quiz 时小地图显示但冻结，由 .panel(z=8) 覆盖 #minimap(z=5)，"
             "属 z-index 层叠而非几何不相交；故此处断言层叠顺序 + pointer-events:none，不断言矩形不相交")
        chk("H4 小地图与 #hud 子项/#banner/#route-map 不相交 + 窄屏 banner 下移 + gutter 生效 + quiz 层叠",
            all(v["ok"] for v in h4_res.values()), h4_res)

        # ------------------------------------------------------------ H12 汇总
        print("\n=== H12 四项错误计数 / 零写盘 / 跨站字段 ===")
        # 第二站也加载一次，确保「两站累计」四项错误计数
        p2 = ctx.new_page()
        watch(p2)
        p2.goto(U_QUEST, wait_until="domcontentloaded")
        p2.wait_for_timeout(400)

        errs_strict_ok = (errs["pageerror"] == 0 and errs["console_error"] == 0
                          and errs["bad_status"] == 0 and len(REAL) == 0)
        fields_ok = (H12_OBS.get("rally_before") == H12_OBS.get("rally_after"))
        zero_write_ok = (H12_OBS.get("frozen_write_delta") == 0)
        chk("H12 四项错误计数归零（ERR_ABORTED 单列） / HUD 路径零写盘 / rally 字段开赛前后不变",
            errs_strict_ok and fields_ok and zero_write_ok,
            {"四项错误计数": dict(errs),
             "requestfailed 明细分类": {"总计": len(FAILS), "ERR_ABORTED 主动取消": len(ABORTED),
                                    "同源真实失败": len(REAL), "外链环境失败": len(EXTERNAL)},
             "同源真实失败明细": REAL[:4], "外链失败明细": EXTERNAL[:4],
             "console.error 文本": CONSOLE_ERRS[:4],
             "frozen step(300) setItem 增量": H12_OBS.get("frozen_write_delta"),
             "rally 开赛前": H12_OBS.get("rally_before"), "rally 开赛后": H12_OBS.get("rally_after"),
             "字段逐字段相等": fields_ok, "四项严格归零": errs_strict_ok})

        print("\n=== 四项错误计数明细（严格区分 reload 主动取消）===")
        print("  pageerror=%d  console_error=%d  requestfailed=%d  bad_status=%d"
              % (errs["pageerror"], errs["console_error"], errs["requestfailed"], errs["bad_status"]))
        print("  requestfailed 明细：总计 %d | ERR_ABORTED(主动取消,不计失败) %d | 同源真实失败 %d | 外链环境失败 %d"
              % (len(FAILS), len(ABORTED), len(REAL), len(EXTERNAL)))
        if ABORTED:
            print("  ERR_ABORTED 样例 URL(去重前 5)：", sorted(set(ABORTED))[:5])
        if REAL:
            print("  !! 同源真实失败明细：", REAL[:5])
        if EXTERNAL:
            print("  外链失败(环境相关,NOTE)：", EXTERNAL[:5])
        if CONSOLE_ERRS:
            print("  !! console.error 文本：", CONSOLE_ERRS[:5])

        browser.close()

    server.shutdown()
    server.server_close()

    print("\n" + "=" * 60)
    p = sum(1 for _, ok, _ in RESULTS if ok)
    f = len(RESULTS) - p
    print("SUMMARY: %d PASS / %d FAIL / %d TOTAL  |  CONCERNS/NOTE: %d"
          % (p, f, len(RESULTS), len(NOTES)))
    for n, ok, d in RESULTS:
        if not ok:
            print("  FAILED:", n, "|", d)
    if NOTES:
        for n, d in NOTES:
            print("  NOTE:", n, "|", d)
    print("=" * 60)
    return 1 if f else 0


if __name__ == "__main__":
    try:
        code = main()
    except SystemExit:
        raise
    except Exception as e:
        print("\n" + "=" * 60)
        print("HUD 元素未就绪，请先完成 #4（或脚本运行环境异常）")
        print("  中断原因：%s: %s" % (type(e).__name__, e))
        print("  常见原因：#4 尚未落地导致 #minimap / __rally 钩子缺失、系统 Chrome 不可启动、端口占用。")
        print("  本脚本不抛裸 traceback；请完成 #4 后重跑。")
        print("SUMMARY: 0 PASS / 0 FAIL / 0 TOTAL  | NOT_READY_OR_ENV_ERROR")
        print("=" * 60)
        code = 2
    sys.exit(code)
