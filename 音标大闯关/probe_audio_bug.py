# -*- coding: utf-8 -*-
"""复现关卡页「听波波队长讲故事」播放/暂停/恢复 状态机行为。"""
import asyncio
from playwright.async_api import async_playwright

BASE = "http://localhost:8765/index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

STATE = """() => {
    const btn=[...document.querySelectorAll('.play-btn')][0];
    const el=window.AudioMgr?window.AudioMgr.el:null;
    return {
        btnText: btn? btn.textContent : '(no .play-btn)',
        nPlayBtns: document.querySelectorAll('.play-btn').length,
        paused: el? el.paused : null,
        current: el? Math.round(el.currentTime*10)/10 : null,
        duration: el? Math.round((el.duration||0)*10)/10 : null,
        cur: window.AudioMgr? window.AudioMgr.cur : null,
        readyState: el? el.readyState : null
    };
}"""


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME,
                                     args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(viewport={"width": 1440, "height": 900})
        # 在页面脚本运行前写好存档，解锁 EP01
        await ctx.add_init_script("""
            localStorage.setItem('ipa-quest-v1', JSON.stringify({stars:{EP00:1},collected:[],sound:true,lastEp:'EP00'}));
        """)
        p = await ctx.new_page()
        errs = []
        p.on("pageerror", lambda e: errs.append(str(e)[:200]))

        async def snap(tag):
            s = await p.evaluate(STATE)
            s["tag"] = tag
            return s

        await p.goto(BASE + "#/level/EP01", wait_until="networkidle", timeout=30000)
        await p.wait_for_timeout(900)
        print("0 初始:", await snap("init"))

        await p.locator(".play-btn").first.click()
        await p.wait_for_timeout(1800)
        s1 = await snap("play")
        print("1 播放后1.8s:", s1)

        await p.locator(".play-btn").first.click()
        await p.wait_for_timeout(500)
        s2 = await snap("pause")
        print("2 暂停后0.5s:", s2, " t@pause=", s2.get("current"))

        await p.locator(".play-btn").first.click()
        await p.wait_for_timeout(1800)
        s3 = await snap("resume")
        print("3 恢复后1.8s:", s3)

        await p.locator(".play-btn").first.click()
        await p.wait_for_timeout(500)
        s4 = await snap("pause2")
        print("4 再暂停后:", s4)

        await b.close()

    print("\n---- 判定 ----")
    print("JS 错误:", errs or "无")
    # 自动判定
    print("STEP1 播放中: paused=" + str(s1.get("paused")) + " cur=" + str(s1.get("current")))
    print("STEP3 恢复后 currentTime 是否前进: " + ("YES ✅" if (s3.get("current") or 0) > (s2.get("current") or 0) + 0.5 else "NO ❌") )
    print("STEP3 恢复后 paused: " + str(s3.get("paused")))


asyncio.run(main())
