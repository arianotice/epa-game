# -*- coding: utf-8 -*-
"""无头浏览器验收 v3：顺序闯关 EP00→EP01→EP02，验证解锁/星星/收集/图鉴/移动端"""
import asyncio, sys
from playwright.async_api import async_playwright

BASE = "http://localhost:8765"
OUT = r"C:/Users/86135/WorkBuddy/英语音标播客/音标大闯关/tmp_crops"
errors = []

async def clear_quiz(page):
    await page.click("text=开始听辨大挑战")
    await page.wait_for_timeout(400)
    for i in range(5):
        q = await page.evaluate("window.__curQ")
        await page.locator(".opt").nth(q["answer"]).click()
        await page.wait_for_timeout(200)
        await page.locator(".quiz-card button.btn").last.click()
        await page.wait_for_timeout(250)
    await page.wait_for_timeout(1400)

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                                           args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        page = await browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("console", lambda m: errors.append(f"[console.{m.type}] {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"[pageerror] {e}"))

        # 1. 地图
        await page.goto(BASE + "/index.html#/map", wait_until="networkidle")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{OUT}/t1_map.png")
        n = await page.locator(".node").count()
        print(f"1. 地图节点: {n} (期望30) {'✅' if n == 30 else '❌'}")

        # 2. 顺序闯 EP00 → EP01 → EP02
        for step, expect in enumerate(["EP00", "EP01", "EP02"]):
            await page.click(".map-head button.btn.red")   # 继续探险
            await page.wait_for_timeout(500)
            url_ep = page.url.split("#/level/")[-1]
            ok = url_ep == expect
            print(f"2.{step+1} 继续探险 → {url_ep} (期望 {expect}) {'✅' if ok else '❌'}")
            await page.screenshot(path=f"{OUT}/t2_level_{expect}.png", full_page=True)
            await clear_quiz(page)
            prog = await page.evaluate("JSON.parse(localStorage.getItem('ipa-quest-v1'))")
            print(f"     stars={prog['stars']}")
            await page.goto(BASE + "/index.html#/map", wait_until="networkidle")
            await page.wait_for_timeout(500)

        prog = await page.evaluate("JSON.parse(localStorage.getItem('ipa-quest-v1'))")
        print(f"3. 三关后: stars={prog['stars']} collected={prog['collected']}")
        assert prog["stars"].get("EP02") == 3, "EP02 应得 3 星"
        assert set(prog["collected"]) == {"iː", "ɪ"}, "应收集 iː/ɪ"
        print("   星星与收集 ✅")

        # 4. 地图进度展示
        await page.screenshot(path=f"{OUT}/t4_map_progress.png")
        done_nodes = await page.locator(".node.done").count()
        print(f"4. 已点亮节点: {done_nodes} (期望3) {'✅' if done_nodes == 3 else '❌'}")

        # 5. EP02 关卡页完整内容
        await page.goto(BASE + "/index.html#/level/EP02", wait_until="networkidle")
        await page.wait_for_timeout(700)
        ph = await page.locator(".ph-card").count()
        chips = await page.locator(".word-chip").count()
        print(f"5. EP02 学习卡: {ph} (期望3), 单词按钮: {chips} {'✅' if ph == 3 and chips >= 12 else '❌'}")

        # 6. 图鉴
        await page.goto(BASE + "/index.html#/atlas", wait_until="networkidle")
        await page.wait_for_timeout(700)
        tiles = await page.locator(".ph-tile").count()
        got = await page.locator(".ph-tile:not(.locked)").count()
        print(f"6. 图鉴卡片: {tiles} (期望48), 已解锁: {got} (期望2) {'✅' if tiles == 48 and got == 2 else '❌'}")
        await page.locator(".ph-tile:not(.locked)").first.click()
        await page.wait_for_timeout(400)
        modal_txt = await page.locator(".modal h2").inner_text()
        print(f"   音标弹层标题: {modal_txt}")
        await page.screenshot(path=f"{OUT}/t6_modal.png")
        await page.keyboard.press("Escape")

        # 7. 知识图谱
        await page.goto(BASE + "/index.html#/atlas/maps", wait_until="networkidle")
        await page.wait_for_timeout(700)
        maps = await page.locator(".atlas-map-card").count()
        imgs = await page.locator(".atlas-map-card img").count()
        print(f"7. 知识图谱: {maps} 卡 / {imgs} 图 {'✅' if maps == 4 else '❌'}")

        # 8. 移动端
        mp = await browser.new_page(viewport={"width": 390, "height": 844})
        await mp.goto(BASE + "/index.html#/map", wait_until="networkidle")
        await mp.wait_for_timeout(700)
        await mp.screenshot(path=f"{OUT}/t8_mobile_map.png")
        await mp.goto(BASE + "/index.html#/level/EP02", wait_until="networkidle")
        await mp.wait_for_timeout(700)
        await mp.screenshot(path=f"{OUT}/t9_mobile_level.png", full_page=True)
        print("8. 移动端截图完成 ✅")

        await browser.close()

    real = [e for e in errors if "favicon" not in e and "fonts.g" not in e]
    print("\n=== JS 错误 ===")
    if real:
        for e in real[:10]: print(" ", e)
        sys.exit(1)
    print("（无）✅")

asyncio.run(main())
