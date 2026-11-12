# -*- coding: utf-8 -*-
"""P1 3D 卡丁车主形态 · 真实 Chromium 可见性 / 竖屏 / 降级门控（只读，零产品改动）。

与既有门控的分工：
  verify_cseg_gate.py / verify_cseg_ui.py / verify_fresh_gate.py / verify_c08_gate.py
    —— 静态源码 + 2D 判定核心 + DOM，均不证明 3D 三车「真的画出来」。
  本脚本补上唯一缺的一层：比赛态下用 gl.info.render.calls、mesh 计数、
  三车真实投影包围盒面积 / 视口面积（kartScreenRatio）证明玩家车 + 2 NPC 可见且可区分。

判定口径（quality-lead #31 G4）：禁止以「Canvas 存在 / 对象存在」冒充可见。

  V1 1280×800 桌面 3D 主形态     V2 375×780 竖屏 D6 终点     V3 320×568 小屏兼容
  V4 ?p1=off 一键回退 2D L0     V5 ?render=2d 回退          V6 无 WebGL 自动降级不白屏
  V7 跟车相机单调 / 不泄答案 / 零 Storage 写入 / 四项错误计数

用法： py -3.13 verify_p1_visual.py
前置：脚本自起 in-process http.server（根目录为项目根，保证跨目录 ../音标大闯关/ 可达），退出释放端口。
"""
import io
import json
import os
import sys
import functools
import threading
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
LAUNCH_ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]

# 注意：不放裸词 "key" —— STATE 的三个 QA 诊断字段 snapshotKeys / kartKeys / gateKeys
# 名字本身含 "Keys"，用裸词会假阳性。改用具体答案域键名；并另加 §白名单逐字断言
# （下方 EXPECTED_*），使这三份数组即便被塞入答案域字段也必然 FAIL，整体比裸词更严。
FORBID = ("correct", "answer", "spoken", "left", "right", "pairkey", "qtype",
          "options", "hit", "correctlateral", "which", "answerkey", "correctkey",
          "correctlateral", "spokenword")

EXPECTED_SNAPSHOT_KEYS = ["lap", "laps", "zone", "span", "time", "karts", "gates"]
EXPECTED_KART_KEYS = ["id", "kind", "t", "lateral", "drift", "boost", "turbo", "air", "yaw"]
EXPECTED_GATE_KEYS = ["id", "lap", "commitT"]

RESULTS = []
EVIDENCE = {}


def chk(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + ("  | " + str(detail) if detail else ""))
    return bool(ok)


class Quiet(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      ".mjs": "text/javascript", ".js": "text/javascript",
                      ".opus": "audio/ogg", ".webp": "image/webp"}

    def log_message(self, *a):
        pass


class LocalServer(ThreadingHTTPServer):
    """修测试服务器自身的并发能力，不放宽任何断言。

    ThreadingHTTPServer 默认 request_queue_size=5。V1 首屏会并发拉取 mp3 /
    webp / js / css，系统负载高时 listen backlog 溢出会直接拒绝连接，浏览器
    报 net::ERR_CONNECTION_REFUSED，使「四项错误计数归零」偶发 FAIL（2026-11-12
    门控第 3/4 轮实测）。调大 backlog 后该竞态消失，四项错误计数仍是硬断言。
    """
    request_queue_size = 128
    daemon_threads = True
    allow_reuse_address = True


server = LocalServer(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
threading.Thread(target=server.serve_forever, daemon=True).start()
PORT = server.server_address[1]


def rally_url(query=""):
    rel = urllib.parse.quote("音标拉力赛/index.html", safe="/")
    return "http://127.0.0.1:%d/%s%s" % (PORT, rel, query)


NO_WEBGL_INIT = """(() => {
  const orig = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (t) {
    if (typeof t === 'string' && /webgl/i.test(t)) return null;
    return orig.apply(this, arguments);
  };
})()"""

RECURSIVE_LEAK = """(v) => {
  const bad = [];
  const walk = (x, path) => {
    if (x === null || x === undefined) return;
    if (Array.isArray(x)) { x.forEach((e, i) => walk(e, path + '[' + i + ']')); return; }
    if (typeof x === 'object') { for (const k in x) {
      if (FORBID_LOCAL.some(w => k.toLowerCase().includes(w))) bad.push(path + '.' + k);
      walk(x[k], path + '.' + k);
    } return; }
    if (typeof x === 'string' && FORBID_LOCAL.some(w => x.toLowerCase().includes(w))) bad.push(path + '=' + x);
  };
  const FORBID_LOCAL = %s;
  walk(v, 'STATE');
  return bad;
}""" % json.dumps(list(FORBID))


def enter_racing(page):
    """按真实 UI 路径：关玩法遮罩 → 听辨档 → 上赛道 → 确定性步进到 racing。"""
    page.wait_for_function("() => !!window.__rally", timeout=20000)
    page.wait_for_timeout(500)
    page.evaluate("() => { const b = document.querySelector('#how-close'); if (b) b.click(); }")
    page.wait_for_timeout(150)
    page.click("#btn-listen")
    page.wait_for_timeout(200)
    page.click("#btn-grid")
    page.wait_for_timeout(250)
    page.evaluate("() => window.__rally.step(300)")
    page.wait_for_timeout(1600)
    return page.evaluate("() => window.__rally.mode")


def run_case(browser, name, viewport, query="", no_webgl=False, want3d=True):
    print("\n=== %s  viewport=%s  query=%s  no_webgl=%s ===" % (name, viewport, query or "(none)", no_webgl))
    ctx = browser.new_context(viewport=viewport)
    page = ctx.new_page()
    errs = {"pageerror": 0, "console_error": 0, "requestfailed": 0, "bad_status": 0}
    aborted, details = [], []
    page.on("pageerror", lambda e: (errs.__setitem__("pageerror", errs["pageerror"] + 1),
                                    details.append("pageerror: " + str(e))))
    page.on("console", lambda m: (errs.__setitem__("console_error", errs["console_error"] + 1),
                                  details.append("console: " + m.text)) if m.type == "error" else None)
    page.on("requestfailed", lambda r: aborted.append(r.url + " " + str(r.failure))
            if "ERR_ABORTED" in str(r.failure)
            else (errs.__setitem__("requestfailed", errs["requestfailed"] + 1),
                  details.append("requestfailed: " + r.url + " " + str(r.failure))))
    page.on("response", lambda r: (errs.__setitem__("bad_status", errs["bad_status"] + 1),
                                   details.append("bad_status: %s %s" % (r.status, r.url)))
            if r.status >= 400 else None)
    if no_webgl:
        page.add_init_script(NO_WEBGL_INIT)

    page.goto(rally_url(query), wait_until="domcontentloaded")
    mode = enter_racing(page)
    state = page.evaluate("() => window.__P1_SCENE__ ? ({...window.__P1_SCENE__}) : null")
    overflow = page.evaluate("() => ({sw: document.documentElement.scrollWidth, iw: window.innerWidth})")
    EVIDENCE[name] = {"mode": mode, "state": state, "errs": dict(errs), "overflow": overflow}

    chk("%s 进入 racing 且 __P1_SCENE__ 可观测" % name, mode == "racing" and state is not None,
        {"mode": mode, "hasState": state is not None})
    if state is None:
        ctx.close()
        return

    if want3d:
        chk("%s renderMode=3d / mounted / WebGL 就绪" % name,
            state["renderMode"] == "3d" and state["mounted"] and state["webgl"] and not state["degraded"],
            {"renderMode": state["renderMode"], "mounted": state["mounted"],
             "webgl": state["webgl"], "webglVersion": state["webglVersion"],
             "degradeReason": state["degradeReason"]})
        ids = state["kartIds"]
        chk("%s 三车 id 互异且含玩家 you" % name,
            len(ids) == 3 and len(set(ids)) == 3 and "you" in ids, ids)
        chk("%s 三车 mesh 与真实 drawCalls > 0" % name,
            state["kartMeshCount"] > 0 and state["drawCalls"] > 0 and state["frames"] > 0,
            {"kartMeshCount": state["kartMeshCount"], "drawCalls": state["drawCalls"],
             "meshCount": state["meshCount"], "frames": state["frames"]})
        ratios = state["kartScreenRatio"]
        chk("%s 三车真实投影屏占比 > 0（G4 硬判据，非 Canvas 存在）" % name,
            len(ratios) == 3 and all(isinstance(v, (int, float)) and 0 < v < 1 for v in ratios.values()),
            ratios)
        boxes = state["kartProjected"]
        inbox = {k: all(-1 <= v <= 1 for v in (b["x0"], b["y0"], b["x1"], b["y1"]))
                 and b["x1"] > b["x0"] and b["y1"] > b["y0"] for k, b in boxes.items()}
        chk("%s 三车投影包围盒在可见视锥内且面积为正" % name,
            len(inbox) == 3 and all(inbox.values()), inbox)
        chk("%s FogExp2 + 双灯（主光 + 柔补光）" % name,
            state["fog"]["isExp2"] and state["fog"]["density"] > 0 and state["light"]["count"] == 2,
            {"fog": state["fog"], "light": state["light"]})
        conv = state["convergence"]
        chk("%s 第三人称跟车：看不到整圈、可见里程 < 圈长" % name,
            conv.get("seesWholeLoop") is False and 0 < conv.get("visibleRangeM", 0) < conv.get("lapLengthM", 0),
            {"seesWholeLoop": conv.get("seesWholeLoop"), "visibleRangeM": conv.get("visibleRangeM"),
             "lapLengthM": conv.get("lapLengthM")})
        cam = state["camera"]
        chk("%s 竖屏以垂直 FOV 为锚、高机位俯角跟车" % name,
            cam.get("fovIsVertical") is True and 60 <= cam.get("fov", 0) <= 90
            and cam.get("heightM", 0) > 0 and cam.get("distanceM", 0) > 0,
            {k: cam.get(k) for k in ("fov", "fovIsVertical", "heightM", "distanceM", "pitchDeg")})
        leak = page.evaluate(RECURSIVE_LEAK, state)
        chk("%s H5 零泄露：STATE 任意层级键名/字符串不命中答案域" % name, len(leak) == 0, leak[:5])
        # 三条白名单逐字断言：三份 QA 诊断数组必须严格等于 Node 单测 T3/T4 的只读白名单，
        # 防止往「白名单」里夹带答案域字段后靠上面的词表蒙混过关。
        chk("%s 只读白名单逐字锁定（snapshot/kart/gate）" % name,
            state["snapshotKeys"] == EXPECTED_SNAPSHOT_KEYS
            and state["kartKeys"] == EXPECTED_KART_KEYS
            and state["gateKeys"] == EXPECTED_GATE_KEYS,
            {"snapshotKeys": state["snapshotKeys"], "kartKeys": state["kartKeys"],
             "gateKeys": state["gateKeys"]})
        chk("%s 3D 层零 Storage 写入 / 零内部错误" % name,
            state["storageWrites"] == 0 and len(state["errors"]) == 0,
            {"storageWrites": state["storageWrites"], "errors": state["errors"][:3]})
        before = state["cameraOdoEstM"]
        page.evaluate("() => window.__rally.step(180)")
        page.wait_for_timeout(900)
        after = page.evaluate("() => window.__P1_SCENE__.cameraOdoEstM")
        chk("%s 跟车相机随里程单调前移" % name, after > before, {"before": before, "after": after})
    else:
        chk("%s 一键/自动降级：renderMode=2d、未挂载 3D" % name,
            state["renderMode"] == "2d" and not state["mounted"],
            {"renderMode": state["renderMode"], "mounted": state["mounted"],
             "forced2d": state["forced2d"], "degraded": state["degraded"],
             "degradeReason": state["degradeReason"]})
        if no_webgl:
            chk("%s 无 WebGL 自动降级（非白屏）" % name,
                state["degraded"] and "webgl" in state["degradeReason"],
                {"degraded": state["degraded"], "reason": state["degradeReason"]})
        else:
            chk("%s 回退标识来自 query 而非崩溃" % name,
                state["forced2d"] and state["degradeReason"] == "forced-2d-via-query",
                {"forced2d": state["forced2d"], "reason": state["degradeReason"]})
        canvas = page.evaluate("""() => { const c = document.querySelector('#c');
          const r = c.getBoundingClientRect(); return {w: Math.round(r.width), h: Math.round(r.height), cw: c.width, ch: c.height}; }""")
        chk("%s 2D L0 仍完整可玩（racing + #c 画布有效）" % name,
            mode == "racing" and canvas["w"] > 0 and canvas["h"] > 0 and canvas["cw"] > 0,
            canvas)

    chk("%s 无横向溢出（竖屏可玩）" % name, overflow["sw"] <= overflow["iw"] + 1, overflow)
    chk("%s 四项错误计数归零" % name,
        all(v == 0 for v in errs.values()),
        {"counts": dict(errs), "details": details[:6], "aborted(ERR_ABORTED,不计)": aborted[:4]})
    ctx.close()


from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path=CHROME, args=LAUNCH_ARGS)
    run_case(browser, "V1-桌面1280", {"width": 1280, "height": 800})
    run_case(browser, "V2-竖屏375", {"width": 375, "height": 780})
    run_case(browser, "V3-小屏320", {"width": 320, "height": 568})
    run_case(browser, "V4-p1off", {"width": 375, "height": 780}, query="?p1=off", want3d=False)
    run_case(browser, "V5-render2d", {"width": 375, "height": 780}, query="?render=2d", want3d=False)
    run_case(browser, "V6-noWebGL", {"width": 375, "height": 780}, no_webgl=True, want3d=False)
    browser.close()

fails = [(n, d) for n, ok, d in RESULTS if not ok]
print("\n" + "=" * 68)
print("SUMMARY  PASS=%d  FAIL=%d  TOTAL=%d" % (len(RESULTS) - len(fails), len(fails), len(RESULTS)))
for n, d in fails:
    print("  FAIL  %s | %s" % (n, d))
print("EVIDENCE_JSON " + json.dumps({
    k: {"mode": v["mode"], "renderMode": v["state"]["renderMode"] if v["state"] else None,
        "mounted": v["state"]["mounted"] if v["state"] else None,
        "kartMeshCount": v["state"]["kartMeshCount"] if v["state"] else None,
        "drawCalls": v["state"]["drawCalls"] if v["state"] else None,
        "kartIds": v["state"]["kartIds"] if v["state"] else None,
        "kartScreenRatio": v["state"]["kartScreenRatio"] if v["state"] else None,
        "degradeReason": v["state"]["degradeReason"] if v["state"] else None,
        "errs": v["errs"], "overflow": v["overflow"]}
    for k, v in EVIDENCE.items()
}, ensure_ascii=False))
server.shutdown()
sys.exit(0 if not fails else 1)
