# -*- coding: utf-8 -*-
"""FWD-VIS-1 · 用户三条硬要求的真实浏览器视觉取证（fresh eyes，只读产品代码）。

唯一新建交付文件；证据 PNG 落 .workbuddy/evidence/。不改产品代码 / 既有门控 / design。
  A 3D 卡丁车立体车体   B 闸门真实分叉左右车道张开   C 石头在赛道上提前可见
真实 Chromium + SwiftShader 软件 WebGL；截图均为 Canvas 真帧，非 2D 降级冒充。
B/C 按「门 eta / 石头前方距离」在近处窗口截候选帧，供人工过眼挑选最佳。
"""
import io
import os
import sys
import json
import functools
import threading
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EVID = os.path.join(HERE, ".workbuddy", "evidence")
CAND = os.path.join(EVID, "_cand")
os.makedirs(CAND, exist_ok=True)
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]


class Quiet(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      ".mjs": "text/javascript", ".js": "text/javascript",
                      ".opus": "audio/ogg", ".webp": "image/webp"}
    def log_message(self, *a):
        pass


class Srv(ThreadingHTTPServer):
    request_queue_size = 128
    daemon_threads = True
    allow_reuse_address = True


server = Srv(("127.0.0.1", 0), functools.partial(Quiet, directory=ROOT))
threading.Thread(target=server.serve_forever, daemon=True).start()
PORT = server.server_address[1]


def rally_url():
    return "http://127.0.0.1:%d/%s" % (PORT, urllib.parse.quote("音标拉力赛/index.html", safe="/"))


STATE_JS = """() => {
  const s = window.__P1_SCENE__, r = window.__rally;
  if (!s) return null;
  const o = { renderMode:s.renderMode, mounted:s.mounted, webgl:s.webgl, degraded:s.degraded,
    degradeReason:s.degradeReason, webglRenderer:s.webglRenderer, webglVersion:s.webglVersion,
    drawCalls:s.drawCalls, meshCount:s.meshCount, kartMeshCount:s.kartMeshCount, frames:s.frames,
    kartScreenRatio:s.kartScreenRatio, forkFlareMax:s.forkFlareMax, rockVisible:s.rockVisible,
    gemVisible:s.gemVisible, markVisible:s.markVisible, hRock:s.hRock, progress:s.progress,
    mode:(r?r.mode:null), finished:(r&&r.race&&r.race.state.finished)||false };
  o.lapLengthM = s.convergence ? s.convergence.lapLengthM : null;
  try {
    if (r && r.race) {
      const act = r.race.activeGate();
      o.gateEta = act ? +act.eta.toFixed(3) : null;
      o.gateLine = act ? +act.gate.line.toFixed(0) : null;
      o.odo = +r.race.state.player.odo.toFixed(0);
      // 最近一颗未拾取石头的前方距离（米）
      const L = o.lapLengthM || 19254.5;
      const ps = r.pickups.filter(p=>p.kind==='rock'&&!p.taken);
      let best = 1e9;
      for (const p of ps) {
        let dt = p.t - r.race.state.player.t; if (dt < -0.02) dt += 1;
        const dz = dt * L;
        if (dz >= 0 && dz < best) best = dz;
      }
      o.rockDzM = best < 1e8 ? +best.toFixed(1) : null;
    }
  } catch (e) { o.rockDzM = null; o._readErr = String(e && e.message); }
  return o;
}"""


def read_state(page):
    return page.evaluate(STATE_JS)


def enter_racing(page):
    page.wait_for_function("() => !!window.__rally", timeout=20000)
    page.wait_for_timeout(500)
    page.evaluate("() => { const b = document.querySelector('#how-close'); if (b) b.click(); }")
    page.wait_for_timeout(150)
    page.click("#btn-listen")
    page.wait_for_timeout(200)
    page.click("#btn-grid")
    page.wait_for_timeout(250)
    page.evaluate("() => { window.__rally.autopilot = true; window.__rally.step(300); }")
    page.wait_for_timeout(1800)
    # 等 3D 稳定过 meshCount 刷新点（每 6 帧）
    page.evaluate("() => window.__rally.step(60)")
    page.wait_for_timeout(400)
    return page.evaluate("() => window.__rally.mode")


def advance(page, frames):
    """推进 n 帧，自动作答 quiz（避免 hold 冻结），返回末帧状态。"""
    return page.evaluate("""(n) => { const r = window.__rally;
      for (let k = 0; k < n; k++) {
        r.step(1);
        if (r.race && r.race.state.quiz) r.race.finishQuiz(r.race.state.quiz.spoken.word);
      }
      return null; }""", frames)


TITLE = {}
RACING = {}
SHOTS = {}
ERRORS = {}
VERDICT = {}


def mark(key, ok, concerns, evidence):
    level = "PASS" if ok and not concerns else ("CONCERNS" if concerns else "FAIL")
    VERDICT[key] = {"verdict": level, "evidence": evidence}
    print("\n=== %s : %s ===" % (key, level))
    print("  " + json.dumps(evidence, ensure_ascii=False))


from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path=CHROME, args=ARGS)
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()
    errs = {"pageerror": 0, "console_error": 0, "requestfailed": 0, "bad_status": 0}
    details = []
    page.on("pageerror", lambda e: (errs.__setitem__("pageerror", errs["pageerror"] + 1),
                                    details.append("pageerror: " + str(e))))
    page.on("console", lambda m: (errs.__setitem__("console_error", errs["console_error"] + 1),
                                  details.append("console: " + m.text)) if m.type == "error" else None)
    page.on("requestfailed", lambda r: errs.__setitem__("requestfailed", errs["requestfailed"] + 1))
    page.on("response", lambda r: (errs.__setitem__("bad_status", errs["bad_status"] + 1),
                                   details.append("bad_status: %s %s" % (r.status, r.url))) if r.status >= 400 else None)

    print("=" * 76)
    print("FWD-VIS-1 · 真实浏览器三条硬要求视觉取证")
    print("ARGS=" + json.dumps(ARGS) + "  EVID=" + EVID)
    print("=" * 76)

    page.goto(rally_url(), wait_until="domcontentloaded")
    page.wait_for_function("() => !!window.__P1_SCENE__", timeout=25000)
    page.wait_for_timeout(700)
    TITLE = read_state(page)
    print("[标题页] renderMode=%s webgl=%s degradeReason=%s" %
          (TITLE.get("renderMode"), TITLE.get("webgl"), TITLE.get("degradeReason")))

    mode = enter_racing(page)
    s = read_state(page)
    RACING = s
    print("[racing] mode=%s renderMode=%s mounted=%s webgl=%s degraded=%s" %
          (mode, s.get("renderMode"), s.get("mounted"), s.get("webgl"), s.get("degraded")))
    print("  drawCalls=%s meshCount=%s kartMeshCount=%s frames=%s renderer=%s" %
          (s.get("drawCalls"), s.get("meshCount"), s.get("kartMeshCount"),
           s.get("frames"), s.get("webglRenderer")))
    print("  kartScreenRatio=%s" % json.dumps(s.get("kartScreenRatio"), ensure_ascii=False))
    is3d = (TITLE.get("renderMode") == "3d" and s.get("mode") == "racing"
            and s.get("renderMode") == "3d" and s.get("mounted") is True
            and s.get("webgl") is True and s.get("degraded") is False
            and (s.get("drawCalls") or 0) > 0 and (s.get("kartMeshCount") or 0) > 0)
    shot_a = os.path.join(EVID, "FWD_A_3d_kart.png")
    page.screenshot(path=shot_a)
    SHOTS["A"] = shot_a
    mark("A_3D卡丁车", is3d, [] if is3d else ["3D 门槛未达，截图可能为 2D 降级"], {
        "titleRenderMode": TITLE.get("renderMode"), "racingRenderMode": s.get("renderMode"),
        "mode": s.get("mode"), "mounted": s.get("mounted"), "webgl": s.get("webgl"),
        "degraded": s.get("degraded"), "degradeReason": s.get("degradeReason"),
        "drawCalls": s.get("drawCalls"), "meshCount": s.get("meshCount"),
        "kartMeshCount": s.get("kartMeshCount"), "kartScreenRatio": s.get("kartScreenRatio"),
        "webglRenderer": s.get("webglRenderer"), "webglVersion": s.get("webglVersion"),
        "png": shot_a, "人工过眼": "看立体车体/车轮/阴影/透视赛道",
    })

    # 扫描：按近处窗口截候选帧
    b_cands, c_cands = [], []
    last_b = last_c = -99
    for i in range(200):
        advance(page, 15)
        cs = read_state(page)
        if cs.get("mode") != "racing" or cs.get("finished"):
            break
        eta = cs.get("gateEta")
        # B：门在近处（eta 0.05~0.9s，分叉张开且未贴脸），flare>0.3
        if (is3d and eta is not None and 0.05 <= eta <= 0.9
                and (cs.get("forkFlareMax") or 0) > 0.3 and i - last_b >= 4
                and len(b_cands) < 8):
            p = os.path.join(CAND, "B_%03d.png" % i)
            page.screenshot(path=p)
            b_cands.append({"i": i, "eta": eta, "flare": cs.get("forkFlareMax"),
                            "png": p, "state": cs})
            last_b = i
        # C：石头在玩家前方 15~130m（提前可见，非拾取瞬间）
        dz = cs.get("rockDzM")
        if (is3d and dz is not None and 15 <= dz <= 130
                and (cs.get("rockVisible") or 0) >= 1 and i - last_c >= 4
                and len(c_cands) < 8):
            p = os.path.join(CAND, "C_%03d.png" % i)
            page.screenshot(path=p)
            c_cands.append({"i": i, "rockDzM": dz, "rockVisible": cs.get("rockVisible"),
                            "markVisible": cs.get("markVisible"), "png": p, "state": cs})
            last_c = i
        if i % 40 == 0:
            print("  扫描 i=%d prog=%s eta=%s rockDz=%s flare=%s rock=%s" %
                  (i, cs.get("progress"), eta, dz, cs.get("forkFlareMax"), cs.get("rockVisible")))
    print("候选帧: B=%d C=%d" % (len(b_cands), len(c_cands)))
    for tag, arr in (("B", b_cands), ("C", c_cands)):
        for c in arr:
            key = "eta" if tag == "B" else "rockDzM"
            print("  %s i=%d %s=%s png=%s" % (tag, c["i"], key, c[key], os.path.basename(c["png"])))

    SHOTS["B_candidates"] = b_cands
    SHOTS["C_candidates"] = c_cands
    ERRORS = {"counts": dict(errs), "details": details[:8]}
    print("\n[四项错误计数] %s" % json.dumps(errs, ensure_ascii=False))
    browser.close()

server.shutdown()

mark("B_真实分叉", is3d and len(b_cands) > 0,
     ([] if (is3d and b_cands) else ["未捕获到近处分叉张开候选帧"]),
     {"候选数": len(b_cands), "人工过眼": "从候选挑左右车道张开、车在车道上、非卡片从天而降的一帧",
      "candidates": [{"eta": c["eta"], "flare": c["flare"], "png": c["png"]} for c in b_cands]})
mark("C_石头提前可见", is3d and len(c_cands) > 0,
     ([] if (is3d and c_cands) else ["未捕获到近处可见石头候选帧"]),
     {"候选数": len(c_cands), "人工过眼": "从候选挑石头在赛道上、前方提前可见、含贴地起跳标线的一帧",
      "candidates": [{"rockDzM": c["rockDzM"], "rockVisible": c["rockVisible"],
                      "markVisible": c["markVisible"], "png": c["png"]} for c in c_cands]})

print("\n" + "=" * 76)
for k, v in VERDICT.items():
    print("%-14s %s" % (k, v["verdict"]))
print("=" * 76)
out = os.path.join(EVID, "FWD_VIS_result.json")
with open(out, "w", encoding="utf-8") as fp:
    json.dump({"verdict": VERDICT, "title": TITLE, "racing": RACING,
               "shots": SHOTS, "errors": ERRORS}, fp, ensure_ascii=False, indent=2)
print("RESULT_JSON -> " + out)
print("A_PNG -> %s (exists=%s)" % (SHOTS["A"], os.path.isfile(SHOTS["A"])))
