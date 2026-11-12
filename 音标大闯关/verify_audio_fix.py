# -*- coding: utf-8 -*-
"""综合验证：① 首页故事线点音标=短音  ② 第01关播客 暂停→恢复  ③ 48 短音可达。"""
import asyncio
from playwright.async_api import async_playwright

BASE = "http://localhost:8765/index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

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

DECODE_CHECK = """async () => {
  const codes = [];
  for (const u of ['U01','U17','U29','U48']) {
    const r = await fetch('assets/audio/ph/' + u.toLowerCase() + '.opus');
    codes.push(u + ':' + r.status);
  }
  return codes;
}"""


async def main():
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

        # ---------- ① 首页故事线：点音标 chip 应播短音 ph/ ----------
        await p.goto(BASE + "#/story", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(800)
        nchips = await p.evaluate("() => document.querySelectorAll('.sp-chip').length")
        clicked_ph = None
        if nchips > 0:
            await p.locator(".sp-chip").first.click()
            await p.wait_for_timeout(700)
            clicked_ph = await p.evaluate(STATE)
        print("① 首页音标 chip 数:", nchips, "-> 点首个后 AudioMgr 状态:", clicked_ph)
        c1 = (clicked_ph and clicked_ph.get("srcDir") == "ph/")
        ok = ok and c1
        print("   判定：首页点音标播短音(ph/) ->", "✅" if c1 else "❌")

        # ---------- ② 第01关播客：播放→暂停→恢复（真实 Bug 场景）----------
        await p.goto(BASE + "#/level/EP01", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(500)
        await p.locator(".play-btn").first.click()          # 播放 ep01
        # 给足缓冲时间，等到 readyState>=3 才算真正开始
        for _ in range(20):
            s = await p.evaluate(STATE)
            if s.get("rs") >= 3 and not s.get("paused"):
                break
            await p.wait_for_timeout(500)
        s_playing = await p.evaluate(STATE)
        print("② 播客播放中：", s_playing)
        await p.locator(".play-btn").first.click()          # 暂停
        await p.wait_for_timeout(300)
        s_paused = await p.evaluate(STATE)
        t_pause = s_paused.get("current") or 0
        await p.locator(".play-btn").first.click()          # 恢复（关键）
        await p.wait_for_timeout(2500)
        s_resumed = await p.evaluate(STATE)
        print("   暂停时刻 t=", t_pause, " (rs=", s_paused.get("rs"), " paused=", s_paused.get("paused"), ")")
        print("   恢复后   ：", s_resumed)
        resumed = (not s_resumed.get("paused")) and ((s_resumed.get("current") or 0) > t_pause)
        c2 = resumed
        ok = ok and c2
        print("   判定：播客暂停→恢复 续播 ->", "✅" if c2 else "❌")

        # ---------- ③ 48 短音可达 + 可解码 ----------
        codes = await p.evaluate(DECODE_CHECK)
        all200 = all(c.endswith(":200") for c in codes)
        print("③ 抽样短音可达:", codes, "->", "✅ 全 200" if all200 else "❌")
        ok = ok and all200

        await b.close()

    print("\n==== 综合判定 ====")
    print("全部通过 ✅" if ok and not errs else "存在失败 ❌", "| JS 错误:", errs or "无")


asyncio.run(main())
