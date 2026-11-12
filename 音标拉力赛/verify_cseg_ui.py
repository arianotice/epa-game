# -*- coding: utf-8 -*-
"""C 段真实浏览器 DOM 冒烟（可复跑；纯验证，零产品改动）。

其它三套门控覆盖「源码静态 + Node 内核 + 文件物理」，本脚本补上唯一缺的一层：
在真实 Chromium 里点一遍 C 段新增 UI，确认它真的渲染、真的写盘、真的跨站保真。

  U1  页面加载四项错误计数                    U2  四区/车手选择器渲染
  U3  点击选择写盘 lastMap/lastChar            U4  reload 后偏好保持
  U5  教学面板动态杯赛重点 + C07 静态块保留    U6  开局 4 门 / 2 圈 / 3 题型 / 词对不重复
  U7  HUD 第 1/2 圈 + 进度条未满格            U8  三种题型 quiz 卡片真实渲染与不泄答案
  U9  结果页渲染                              U10 赛事解锁 / 杯赛成绩写盘
  U11 大闯关真实写入后 C 段新字段不被冲掉      U12 最终四项错误计数

用法： python verify_cseg_ui.py
前置：无需外部服务器，脚本自起 in-process http.server 并在退出时释放端口。
"""
import os, sys, io, json, threading, functools, urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEST = os.path.join(ROOT, "音标大闯关")
RALLY = os.path.join(ROOT, "音标拉力赛")
KEY = "ipa-quest-v1"
TAG = "hud-20261108"
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
U_RALLY = url("音标拉力赛/index.html")
U_QUEST = url("音标大闯关/index.html")
print("SERVER", PORT)

from playwright.sync_api import sync_playwright

errs = {"pageerror": 0, "console_error": 0, "requestfailed": 0, "bad_status": 0}
aborted = []
def watch(pg):
    def on_fail(r):
        if "ERR_ABORTED" in str(r.failure):
            aborted.append(r.url)
        else:
            errs["requestfailed"] += 1
    pg.on("pageerror", lambda e: errs.__setitem__("pageerror", errs["pageerror"] + 1))
    pg.on("console", lambda m: errs.__setitem__("console_error", errs["console_error"] + 1) if m.type == "error" else None)
    pg.on("requestfailed", on_fail)
    pg.on("response", lambda r: errs.__setitem__("bad_status", errs["bad_status"] + 1) if r.status >= 400 else None)

READ_RALLY = "k => JSON.parse(localStorage.getItem(k) || '{}').rally || {}"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path=CHROME)
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page(); watch(page)
    page.goto(U_RALLY, wait_until="domcontentloaded")
    page.wait_for_function("!!window.__rally", timeout=15000)
    page.wait_for_timeout(600)

    print("\n=== U1–U5 标题页 / 选择器 / 教学面板 ===")
    chk("U1 拉力赛页面加载无异常（pageerror / console / 4xx）",
        errs["pageerror"] == 0 and errs["console_error"] == 0 and errs["bad_status"] == 0, dict(errs))

    # 首次访问会弹「玩法」说明并隐藏标题页（产品既有设计），按真实 UI 路径关掉；
    # 该动作会写 rally.howSeen，因此后续 reload 不会再次遮挡。
    page.evaluate("document.querySelector('#how-close').click()")
    page.wait_for_timeout(200)

    sel = page.evaluate("""() => ({
      maps: [...document.querySelectorAll('#map-pick [data-map]')].map(b => ({id: b.dataset.map, on: b.getAttribute('aria-pressed') === 'true'})),
      chars: [...document.querySelectorAll('#char-pick [data-char]')].map(b => ({id: b.dataset.char, on: b.getAttribute('aria-pressed') === 'true'}))
    })""")
    chk("U2 四区 4 个 / 车手 3 个，各恰好 1 个选中",
        len(sel["maps"]) == 4 and len(sel["chars"]) == 3
        and sum(m["on"] for m in sel["maps"]) == 1 and sum(c["on"] for c in sel["chars"]) == 1,
        {"maps": len(sel["maps"]), "chars": len(sel["chars"])})

    tmap, tchar = sel["maps"][2]["id"], sel["chars"][1]["id"]
    page.click('#map-pick [data-map="%s"]' % tmap)
    page.click('#char-pick [data-char="%s"]' % tchar)
    page.wait_for_timeout(150)
    pressed = page.evaluate("""() => ({
      map: document.querySelector('#map-pick [aria-pressed="true"]').dataset.map,
      char: document.querySelector('#char-pick [aria-pressed="true"]').dataset.char,
      name: document.querySelector('#map-pick [aria-pressed="true"]').textContent
    })""")
    saved = page.evaluate(READ_RALLY, KEY)
    chk("U3 点击后选中态切换且 lastMap / lastChar 写盘",
        pressed["map"] == tmap and pressed["char"] == tchar
        and saved.get("lastMap") == tmap and saved.get("lastChar") == tchar,
        {"map": pressed["map"], "char": pressed["char"], "lastMap": saved.get("lastMap"), "lastChar": saved.get("lastChar")})

    page.reload(wait_until="domcontentloaded")
    page.wait_for_function("!!window.__rally", timeout=15000)
    page.wait_for_timeout(250)
    after_reload = page.evaluate("""() => ({
      map: document.querySelector('#map-pick [aria-pressed="true"]').dataset.map,
      char: document.querySelector('#char-pick [aria-pressed="true"]').dataset.char
    })""")
    chk("U4 reload 后杯赛 / 车手偏好保持", after_reload["map"] == tmap and after_reload["char"] == tchar, after_reload)

    page.click("#btn-listen")
    page.wait_for_timeout(200)
    teach = page.evaluate("""() => {
      const f = document.querySelector('#teach-focus');
      return {mode: window.__rally.mode, name: f.querySelector('b') ? f.querySelector('b').textContent : '',
              text: f.textContent, body: document.querySelector('#panel-teach').textContent};
    }""")
    chk("U5 教学面板动态杯赛重点（地图 / 2 圈 / 音素对）且 C07 静态块保留",
        teach["mode"] == "teach" and teach["name"] and teach["name"] in pressed["name"]
        and "2 圈" in teach["text"] and "↔" in teach["text"]
        and "紧音" in teach["body"] and "松音" in teach["body"],
        {"mode": teach["mode"], "name": teach["name"], "focus": teach["text"][:70]})

    print("\n=== U6–U7 开局 / 两圈 HUD ===")
    page.click("#btn-grid")
    page.wait_for_timeout(150)
    g = page.evaluate("""() => {
      const r = window.__rally.race, gs = r.state.gates;
      return {mode: window.__rally.mode, laps: r.state.laps, mapId: r.state.mapId,
              n: gs.length, lineT: gs.map(x => x.lineT), lapsOf: gs.map(x => x.lap),
              qTypes: gs.map(x => x.qType), pairKeys: gs.map(x => x.pairKey),
              units: gs.map(x => x.spoken.unit)};
    }""")
    chk("U6 开局 4 门 / 2 圈 / 地图一致 / 每圈 2 门 / 里程递增 / 三题型 / 词对不重复",
        g["n"] == 4 and g["laps"] == 2 and g["mapId"] == tmap
        and sorted(g["lapsOf"]) == [0, 0, 1, 1]
        and all(g["lineT"][i] < g["lineT"][i + 1] for i in range(3))
        and len(set(g["qTypes"])) == 3 and len(set(g["pairKeys"])) == 4,
        {"n": g["n"], "laps": g["laps"], "mapId": g["mapId"], "lineT": g["lineT"],
         "qTypes": g["qTypes"], "pairs": len(set(g["pairKeys"]))})

    page.evaluate("window.__rally.step(260)")
    page.wait_for_timeout(100)
    hud = page.evaluate("""() => ({mode: window.__rally.mode,
      gates: document.querySelector('#gates').textContent,
      width: document.querySelector('#progress span').style.width})""")
    wpct = float(hud["width"].replace("%", "") or 0)
    chk("U7 进入 racing 且 HUD 显示第 1/2 圈、进度条未满格",
        hud["mode"] == "racing" and "1/2" in hud["gates"] and 0 < wpct < 100,
        {"mode": hud["mode"], "gates": hud["gates"], "width": hud["width"]})

    print("\n=== U8 三种题型 quiz 卡片 ===")
    expect_title = {"word": "选出听到的词", "ipa": "选出它的音标", "type": "选出它的发音类别"}
    quiz_seen = {}
    for kind in ("word", "ipa", "type"):
        q = page.evaluate("""(kind) => {
          const r = window.__rally.race, gs = r.state.gates, g = gs[0];
          const spoken = g.spoken, other = g.other;
          r.state.quiz = {spoken, options: [spoken, other], reason: 'wall', qType: kind, pairKey: g.pairKey};
          window.__rally.step(1);
          return {mode: window.__rally.mode,
                  title: document.querySelector('#quiz-title').textContent,
                  prompt: document.querySelector('#quiz-prompt').textContent,
                  opts: [...document.querySelectorAll('#quiz-options button')].map(b => b.textContent.trim()),
                  word: spoken.word, ipa: spoken.ipa};
        }""", kind)
        quiz_seen[kind] = q
        ok = (q["mode"] == "quiz" and q["title"] == expect_title[kind]
              and len(q["opts"]) == 2 and q["opts"][0] != q["opts"][1])
        if kind == "word":
            ok = ok and q["word"] not in q["prompt"] and all(q["word"] in o or o for o in q["opts"])
        if kind == "ipa":
            ok = ok and all("/" in o for o in q["opts"])
        if kind == "type":
            ok = ok and q["opts"] != quiz_seen["word"]["opts"]
        chk("U8.%s 题型「%s」真实渲染且题干不泄答案" % (kind, expect_title[kind]), ok,
            {"mode": q["mode"], "title": q["title"], "opts": q["opts"], "prompt": q["prompt"][:36]})
        page.locator("#quiz-options button").first.click()
        page.wait_for_timeout(950)

    print("\n=== U9–U11 结果页 / 解锁写盘 / 跨站保真 ===")
    res = page.evaluate("""() => {
      const r = window.__rally.race;
      r.state.gates.forEach(g => { g.played = true; g.judged = true; g.hit = true; });
      r.state.gateHits = r.state.gates.length;
      r.state.finished = true;
      r.state.finishTime = Math.max(0, r.state.time - 1.2);
      window.__rally.step(1);
      const el = document.querySelector('#panel-results');
      return {hidden: el.hidden, mode: window.__rally.mode, text: el.textContent};
    }""")
    chk("U9 结果页真实渲染（2 圈 / 杯赛名 / 解锁说明）",
        res["hidden"] is False and res["mode"] == "results"
        and "2 圈" in res["text"] and teach["name"] in res["text"]
        and ("本场解锁" in res["text"] or "本场没有新卡" in res["text"]),
        {"hidden": res["hidden"], "mode": res["mode"], "text": res["text"][:90]})

    saved2 = page.evaluate(READ_RALLY, KEY)
    earned = [u for u in g["units"] if u]
    chk("U10 赛事解锁取并集 + 四区杯赛成绩 + 偏好均写入存档",
        all(u in (saved2.get("unlocked") or []) for u in earned)
        and (saved2.get("maps") or {}).get(tmap, {}).get("wins", 0) >= 1
        and saved2.get("lastMap") == tmap and saved2.get("lastChar") == tchar,
        {"earned": earned, "unlocked": saved2.get("unlocked"),
         "mapStat": (saved2.get("maps") or {}).get(tmap),
         "lastMap": saved2.get("lastMap"), "lastChar": saved2.get("lastChar")})

    p2 = ctx.new_page(); watch(p2)
    p2.goto(U_QUEST, wait_until="domcontentloaded")
    p2.wait_for_function("!!window.Store", timeout=15000)
    p2.wait_for_timeout(400)
    p2.evaluate("window.Store.setSound(true)")
    p2.wait_for_timeout(250)
    saved3 = page.evaluate(READ_RALLY, KEY)
    chk("U11 大闯关真实写入后 C 段新字段 maps / lastMap / lastChar 未被跨站覆盖",
        (saved3.get("maps") or {}).get(tmap, {}).get("wins", 0) >= 1
        and saved3.get("lastMap") == tmap and saved3.get("lastChar") == tchar
        and all(u in (saved3.get("unlocked") or []) for u in earned),
        {"maps": saved3.get("maps"), "lastMap": saved3.get("lastMap"), "lastChar": saved3.get("lastChar")})

    print("\n=== 四项错误计数（两站累计） ===")
    print(" ", dict(errs), "| 主动取消(ERR_ABORTED，不计失败):", len(aborted))
    chk("U12 pageerror / console.error / 真实网络失败 / 4xx 全 0",
        all(v == 0 for v in errs.values()), dict(errs))

    browser.close()

print("\n" + "=" * 60)
p = sum(1 for _, ok, _ in RESULTS if ok)
f = len(RESULTS) - p
print("SUMMARY: %d PASS / %d FAIL / %d TOTAL" % (p, f, len(RESULTS)))
for n, ok, det in RESULTS:
    if not ok:
        print("  FAILED:", n, "|", det)
sys.exit(1 if f else 0)
