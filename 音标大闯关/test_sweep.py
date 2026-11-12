# -*- coding: utf-8 -*-
"""全关卡巡检：30 关页面渲染 + 挑战启动 + 首题作答"""
import asyncio, sys
from playwright.async_api import async_playwright

BASE = "http://localhost:8765"
errors = []

async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                                           args=["--no-sandbox"])
        ctx = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await ctx.new_page()
        page.on("pageerror", lambda e: errors.append(f"[pageerror] {e}"))
        page.on("console", lambda m: errors.append(f"[console] {m.text}") if m.type == "error" else None)

        # 种子进度：全部解锁（模拟已通关）
        await page.goto(BASE + "/index.html#/map", wait_until="networkidle")
        await page.evaluate("""() => {
          const stars = {};
          for (let i = 0; i < 30; i++) stars['EP' + String(i).padStart(2,'0')] = 3;
          const syms = window.IPA_DATA.phonemes.map(p => p.sym);
          localStorage.setItem('ipa-quest-v1', JSON.stringify({v:1, stars, collected: syms, sound: true, lastEp: 'EP29'}));
        }""")
        await page.reload(wait_until="networkidle")
        await page.wait_for_timeout(600)

        bad = []
        for i in range(30):
            ep = f"EP{i:02d}"
            await page.goto(f"{BASE}/index.html#/level/{ep}", wait_until="networkidle")
            await page.wait_for_timeout(350)
            has_start = await page.locator("text=听辨大挑战").count()
            img_ok = await page.locator(".level-img").count()
            if not has_start:
                bad.append(f"{ep}: 无挑战按钮"); continue
            await page.click("text=听辨大挑战")
            await page.wait_for_timeout(300)
            q = await page.evaluate("window.__curQ")
            if not q or "answer" not in q:
                bad.append(f"{ep}: 题目异常 {q}"); continue
            opts = await page.locator(".opt").count()
            if opts < 2:
                bad.append(f"{ep}: 选项不足 {opts}"); continue
            # 答对第一题
            await page.locator(".opt").nth(q["answer"]).click()
            await page.wait_for_timeout(250)
            fb = await page.locator(".feedback .ok, .feedback .no").count()
            if not fb:
                bad.append(f"{ep}: 无反馈"); continue
            print(f"{ep} ✅ 题型={q['type']} 选项={opts}")
        await page.screenshot(path=r"C:/Users/86135/WorkBuddy/英语音标播客/音标大闯关/tmp_crops/t11_sweep.png", full_page=True)

        # 毕业证书页
        await page.goto(BASE + "/index.html#/grad", wait_until="networkidle")
        await page.wait_for_timeout(800)
        dip = await page.locator(".diploma").count()
        print(f"毕业证书页: {'✅' if dip else '❌'}")
        await page.screenshot(path=r"C:/Users/86135/WorkBuddy/英语音标播客/音标大闯关/tmp_crops/t12_diploma.png", full_page=True)

        # 地图全点亮
        await page.goto(BASE + "/index.html#/map", wait_until="networkidle")
        await page.wait_for_timeout(600)
        done = await page.locator(".node.done").count()
        stars = await page.locator("#hud-stars").text_content()
        spirits = await page.locator("#hud-spirits").text_content()
        print(f"全通关地图: 点亮节点 {done}/30, HUD ⭐{stars} 💎{spirits}")
        await page.screenshot(path=r"C:/Users/86135/WorkBuddy/英语音标播客/音标大闯关/tmp_crops/t13_map_all.png")
        await browser.close()

    real = [e for e in errors if "favicon" not in e and "fonts.g" not in e]
    if bad or real:
        print("\n问题:", bad[:10], real[:10]); sys.exit(1)
    print("\n=== 30 关巡检全部通过，无 JS 错误 ✅ ===")

asyncio.run(main())
