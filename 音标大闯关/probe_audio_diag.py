# -*- coding: utf-8 -*-
"""严格诊断：Chrome 对 ogg/opus 的解码能力 + 用"小体积短音"测 play→pause→resume 状态机。"""
import asyncio
from playwright.async_api import async_playwright

BASE = "http://localhost:8765/index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

DECODE = """() => {
  const a = new Audio();
  return {
    ogg_opus: a.canPlayType('audio/ogg; codecs=opus'),
    ogg: a.canPlayType('audio/ogg'),
    webm: a.canPlayType('audio/webm'),
    mp3: a.canPlayType('audio/mpeg'),
    hasAudio: 'play' in a,
  };
}"""

# 用小体积短音 ph/u01.opus（~1.7s）做可靠的 播放/暂停/恢复 状态机测试
STATE = """() => {
  const el = window.AudioMgr ? window.AudioMgr.el : null;
  return {
    paused: el ? el.paused : null,
    current: el ? Math.round(el.currentTime * 100) / 100 : null,
    readyState: el ? el.readyState : null,
    canplay: el ? el.canPlayType('audio/ogg; codecs=opus') : null,
    srcTail: el && el.currentSrc ? el.currentSrc.split('/').pop() : null,
  };
}"""


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME,
                                     args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(viewport={"width": 1440, "height": 900})
        p = await ctx.new_page()
        errs = []
        p.on("pageerror", lambda e: errs.append(str(e)[:200]))

        print("Chrome 解码能力:", await p.evaluate(DECODE))

        # 直接驱动 AudioMgr 对"短音"做 play→pause→resume，源是 ph/u01.opus（小、秒级 buffer）
        await p.goto(BASE, wait_until="networkidle")
        seq = []
        # 1) play 短音
        await p.evaluate("() => { AudioMgr.stop(); AudioMgr.playPhoneme('U01','t'); }")
        await p.wait_for_timeout(900)          # 1.7s 短音，给它播一会儿
        s1 = await p.evaluate(STATE)
        seq.append(("play", s1))
        # 2) 主动暂停
        await p.evaluate("() => { AudioMgr.pause(); }")
        await p.wait_for_timeout(200)
        s2 = await p.evaluate(STATE)
        t_at_pause = s2["current"]
        seq.append(("pause", s2))
        # 3) 恢复（关键！）
        await p.evaluate("() => { AudioMgr.toggle('assets/audio/ph/u01.opus','t'); }")
        await p.wait_for_timeout(900)
        s3 = await p.evaluate(STATE)
        seq.append(("resume", s3))

        for tag, s in seq:
            print(f"{tag:>7}: paused={s['paused']} t={s['current']} rs={s['readyState']} src={s['srcTail']}")

        print("\n---- 判定（短音）----")
        print(f"暂停时刻 t={t_at_pause}, 恢复后 t={s3['current']}")
        resumed = (not s3["paused"]) and ((s3["current"] or 0) > (t_at_pause or 0))
        print("恢复后仍在播放且 currentTime 前进:", "YES ✅" if resumed else "NO ❌")
        print("readyState(能否解码 ogg/opus):", s3["readyState"], "(>0 说明能解码)")
        print("JS 错误:", errs or "无")
        await b.close()


asyncio.run(main())
