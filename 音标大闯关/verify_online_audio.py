# -*- coding: utf-8 -*-
"""线上验证（http://192.144.226.216）：音频修复 + 48 音标短音。

针对 Caddy「文件不存在也返回 index.html(200)」的 catch-all 兜底，
48 短音用【本地字节数 vs 线上 Content-Length】逐一比对来判定真实部署，避免 200 假阳性。
另校验线上 audio.js 已含 playPhoneme / _doPlay / .opus 归一化（新版）。
"""
import asyncio, json, os, sys
from playwright.async_api import async_playwright

BASE = "http://192.144.226.216/index.html"
ORIGIN = "http://192.144.226.216"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
PH_DIR = os.path.join(HERE, "assets", "audio", "ph")

STATE = """() => {
  const el = window.AudioMgr ? window.AudioMgr.el : null;
  return {
    cur: window.AudioMgr ? window.AudioMgr.cur : null,
    srcTail: el && el.currentSrc ? el.currentSrc.split('/').pop() : null,
    srcDir:  el && el.currentSrc ? (el.currentSrc.includes('/ph/') ? 'ph/' : 'root/') : null,
    paused:  el ? el.paused : null,
    current: el ? Math.round(el.currentTime * 100) / 100 : null,
    rs:      el ? el.readyState : null,
  };
}"""

# 返回 {unit: expected_size} 与 48 个短音 fetch 的 Content-Length 对比
SIZE_CHECK = """async (expect) => {
  const keys = Object.keys(expect);
  const res = [];
  for (const k of keys) {
    try {
      const r = await fetch('assets/audio/ph/' + k.toLowerCase() + '.opus', {cache: 'no-store'});
      const cl = r.headers.get('content-length');
      res.push({unit: k, status: r.status,
                bytes: (cl !== null) ? parseInt(cl, 10) : -1,
                type: r.headers.get('content-type') || ''});
    } catch (e) {
      res.push({unit: k, status: 0, bytes: -1, type: 'ERR:' + String(e).slice(0, 30)});
    }
  }
  return res;
}"""


def load_local_sizes():
    if not os.path.isdir(PH_DIR):
        print("!! 本地 ph/ 目录不存在:", PH_DIR); return {}
    d = {}
    for f in os.listdir(PH_DIR):
        if f.endswith(".opus"):
            d[f[:-5].upper()] = os.path.getsize(os.path.join(PH_DIR, f))
    return d


async def main():
    local = load_local_sizes()
    print("本地 ph/*.opus 数量:", len(local), "(期望 48)")

    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME,
                                     args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(viewport={"width": 1440, "height": 900})
        await ctx.add_init_script(
            "localStorage.setItem('ipa-quest-v1', JSON.stringify({stars:{EP00:1},collected:[],sound:true,lastEp:'EP00'}));")
        p = await ctx.new_page()
        errs = []
        p.on("pageerror", lambda e: errs.append(str(e)[:200]))
        ok = True

        # ---------- 0) 线上 audio.js 是否为新版 ----------
        await p.goto(BASE, wait_until="domcontentloaded")
        js_text = await p.evaluate("""async () => {
            const r = await fetch(location.origin + '/js/audio.js', {cache:'no-store'});
            return await r.text();
        }""")
        has_pp = "playPhoneme" in js_text
        has_do = "_doPlay" in js_text
        has_norm = r"\.opus" in js_text.replace("\n", " ")   # 匹配源码里的 /\.opus$/i 归一化
        print("0) 线上 audio.js: playPhoneme=" + str(has_pp) + " _doPlay=" + str(has_do)
              + " .opus归一化=" + str(has_norm))
        ok = ok and (has_pp and has_do and has_norm)

        # ---------- ① 首页故事线点音标 = 短音 ph/ ----------
        await p.goto(BASE + "#/story", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(900)
        nchips = await p.evaluate("() => document.querySelectorAll('.sp-chip').length")
        clicked_ph = None
        if nchips > 0:
            await p.locator(".sp-chip").first.click()
            await p.wait_for_timeout(700)
            clicked_ph = await p.evaluate(STATE)
        c1 = (clicked_ph and clicked_ph.get("srcDir") == "ph/")
        ok = ok and c1
        print("① 首页音标 chip:", nchips, "-> 点首个后:", clicked_ph,
              "-> 播短音(ph/)?", "✅" if c1 else "❌")

        # ---------- ② 第01关播客 播放→暂停→恢复 ----------
        await p.goto(BASE + "#/level/EP01", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(500)
        await p.locator(".play-btn").first.click()
        for _ in range(20):
            s = await p.evaluate(STATE)
            if s.get("rs") >= 3 and not s.get("paused"):
                break
            await p.wait_for_timeout(500)
        s_playing = await p.evaluate(STATE)
        await p.locator(".play-btn").first.click()
        await p.wait_for_timeout(300)
        s_paused = await p.evaluate(STATE)
        t_pause = s_paused.get("current") or 0
        await p.locator(".play-btn").first.click()
        await p.wait_for_timeout(2500)
        s_resumed = await p.evaluate(STATE)
        resumed = (not s_resumed.get("paused")) and ((s_resumed.get("current") or 0) > t_pause)
        ok = ok and resumed
        print("② 播客 播放 t=" + str(s_playing.get("current"))
              + " → 暂停 t=" + str(t_pause)
              + " → 恢复后 t=" + str(s_resumed.get("current"))
              + " (rs=" + str(s_resumed.get("rs")) + ") -> 续播?", "✅" if resumed else "❌")

        # ---------- ③ 48 短音：本地字节数 vs 线上 Content-Length ----------
        if not local:
            print("③ 本地 ph/ 为空，无法做字节比对 —— 跳过并判失败")
            ok = False
        else:
            rows = await p.evaluate(SIZE_CHECK, local)
            mismatch = [r for r in rows if (r["status"] != 200
                        or r["type"] and "html" in r["type"]
                        or r["bytes"] != local[r["unit"]])]
            good = sum(1 for r in rows if r["bytes"] == local[r["unit"]])
            print("③ 短音字节比对: " + str(good) + "/" + str(len(local)) + " 与本地一致",
                  "-> " + ("✅ 全部一致(真部署)" if not mismatch else "❌ 有 " + str(len(mismatch)) + " 个不符"))
            for m in mismatch[:8]:
                print("    不符:", m, "期望", local.get(m["unit"]))
            ok = ok and (not mismatch and good == 48)

        await b.close()

    print("\n==== 线上综合判定 ====")
    print("全部通过 ✅" if ok and not errs else "存在失败 ❌", "| JS 错误:", errs or "无")
    sys.exit(0 if ok and not errs else 1)


asyncio.run(main())
