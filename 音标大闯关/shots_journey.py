# -*- coding: utf-8 -*-
"""第六幕藏宝行进图 视觉验收：✕标记态 / 点亮宝石态 各截一张。"""
import asyncio
from playwright.async_api import async_playwright

BASE = "http://localhost:8765/index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT = r"C:\Users\86135\WorkBuddy\英语音标播客\音标大闯关\tmp_journey.png"


async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME,
                                     args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        p = await b.new_page(viewport={"width": 1440, "height": 900})
        errs = []
        p.on("pageerror", lambda e: errs.append(str(e)[:200]))

        await p.goto(BASE + "#/story", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(1000)

        # 定位第六幕旅程 section
        stage = p.locator(".chapter--journey .journey-stage")
        await stage.scroll_into_view_if_needed()
        await p.wait_for_timeout(800)

        # ① 未点亮（✕ 标记）态截图
        await stage.screenshot(path=OUT.replace("tmp_journey.png", "tmp_journey_off.png"))
        print("未点亮态已截图 -> tmp_journey_off.png")

        # ② 点击「点亮」按钮，等宝石铺满后截图
        btn = p.locator("#journey-play")
        await btn.click()
        await p.wait_for_timeout(3000)  # 时间线 2.4s + 余量
        lit = await p.evaluate("() => document.querySelectorAll('.jnode.lit').length")
        await stage.screenshot(path=OUT)
        print("点亮后 .jnode.lit =", lit, "/ 30 -> 已截图 tmp_journey.png")

        # ③ 宝石/标记结构检查
        st = await p.evaluate("""() => {
            const nodes=[...document.querySelectorAll('.jnode')];
            return {
                total: nodes.length,
                withGem: nodes.filter(n=>n.querySelector('.gem')).length,
                withX:   nodes.filter(n=>n.querySelector('.xmark')).length,
                regions: [...new Set([...document.querySelectorAll('.jnode')].map(n=>n.title))].length,
            };
        }""")
        print("结构:", st)
        print("JS 错误:", errs or "无")

        await b.close()


asyncio.run(main())
