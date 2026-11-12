# -*- coding: utf-8 -*-
"""滚动叙事站验收：GSAP ScrollTrigger 场景动画 + Lenis 平滑滚动 + 路由清理"""
import asyncio
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8765/index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(("  [PASS] " if ok else "  [FAIL] ") + name + ((" -> " + str(detail)) if detail else ""))


async def scroll_to(page, sel, settle=1100):
    await page.evaluate(
        """(sel) => {
          const el = document.querySelector(sel);
          if (!el) return;
          if (window.__lenis) window.__lenis.scrollTo(el, { immediate: true });
          else el.scrollIntoView();
          if (window.ScrollTrigger) ScrollTrigger.update();
        }""",
        sel,
    )
    await page.wait_for_timeout(settle)


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await ctx.new_page()

        errors = []
        page.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        page.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        # ---------- 1. 默认落地页应为叙事站 ----------
        print("\n[1] 默认落地页")
        await page.goto(BASE, wait_until="networkidle")
        await page.wait_for_timeout(1400)
        n_ch = await page.locator(".chapter").count()
        check("默认（空 hash）进入叙事站，共 9 个章节", n_ch == 9, "实际 %d 章" % n_ch)
        has_story_mode = await page.evaluate("document.body.classList.contains('story-mode')")
        check("body 进入 story-mode", has_story_mode)

        # ---------- 2. 动画库加载 ----------
        print("\n[2] 动画库（本地 vendor）")
        libs = await page.evaluate(
            "({gsap: !!window.gsap, st: !!window.ScrollTrigger, lenis: !!window.Lenis, inst: !!window.__lenis})"
        )
        check("GSAP 已加载", libs["gsap"])
        check("ScrollTrigger 已加载", libs["st"])
        check("Lenis 已加载", libs["lenis"])
        check("Lenis 实例已创建（平滑滚动生效）", libs["inst"])
        ready = await page.evaluate("document.documentElement.classList.contains('gsap-ready')")
        check("gsap-ready 初始态已启用", ready)

        # ---------- 3. 背景层 ----------
        print("\n[3] 章节色彩过渡层")
        n_bg = await page.locator("#story-bg .bg-layer").count()
        check("9 层背景（每章一层）", n_bg == 9, "实际 %d 层" % n_bg)
        n_dots = await page.locator(".chapter-dots .cdot").count()
        check("右侧章节导航 9 个点", n_dots == 9, "实际 %d" % n_dots)

        # ---------- 4. 序章入场动画 ----------
        print("\n[4] 序章场景入场")
        op = await page.evaluate(
            """() => {
              const s = document.querySelector('.chapter[data-ch="0"]');
              if (!s) return null;
              return {
                num: getComputedStyle(s.querySelector('.ch-num')).opacity,
                title: getComputedStyle(s.querySelector('.ch-title')).opacity,
                lead: getComputedStyle(s.querySelector('.ch-lead')).opacity,
              };
            }"""
        )
        check("序章编号已淡入", op and float(op["num"]) > 0.05, op)
        check("序章标题已淡入", op and float(op["title"]) > 0.9, op and op["title"])
        check("序章引导语已淡入", op and float(op["lead"]) > 0.9, op and op["lead"])

        # 关键交互元素（播放器）必须落在首屏内
        vis = await page.evaluate(
            """() => {
              const p = document.querySelector('.chapter[data-ch="0"] .story-player');
              if (!p) return null;
              const r = p.getBoundingClientRect();
              return { top: Math.round(r.top), bottom: Math.round(r.bottom), vh: innerHeight };
            }"""
        )
        check("序章音频播放器在首屏可视区内", vis and vis["bottom"] <= vis["vh"] + 2, vis)

        await page.screenshot(path="tmp_shots/s1_prologue.png")

        # ---------- 5. 逐章滚动 + 背景过渡 ----------
        print("\n[5] 滚动逐章揭示")
        for i in (2, 4, 6):
            await scroll_to(page, '.chapter[data-ch="%d"]' % i)
            op = await page.evaluate(
                """(i) => {
                  const s = document.querySelector('.chapter[data-ch="' + i + '"]');
                  const t = s.querySelector('.ch-title') || s.querySelector('.gal-title');
                  return t ? getComputedStyle(t).opacity : null;
                }""",
                i,
            )
            check("第 %d 章标题入场完成" % i, op is not None and float(op) > 0.9, op)

        # 背景层：滚到深处后，靠后的层应已淡入，靠前的层仍保留（叠加）
        bgs = await page.evaluate(
            """() => Array.from(document.querySelectorAll('#story-bg .bg-layer'))
                 .map(e => +getComputedStyle(e).opacity)"""
        )
        check("背景层随滚动交叉淡入（靠后层已点亮）", bgs and bgs[5] > 0.8, bgs)

        # ---------- 6. 钉住章节 ----------
        print("\n[6] 钉住（pin）章节")
        await scroll_to(page, ".chapter--journey", 1200)
        pins = await page.locator(".pin-spacer").count()
        check("旅程全景幕已钉住（pin-spacer 生成）", pins >= 1, "pin-spacer=%d" % pins)
        nodes = await page.locator(".jnode").count()
        check("地图路线含 30 个关卡节点", nodes == 30, "实际 %d" % nodes)
        # 地图应完整可见，不被吸顶顶栏或底部导航裁切
        jf = await page.evaluate(
            """() => {
              const st = document.querySelector('.journey-stage');
              const r = st.getBoundingClientRect();
              const poly = document.querySelector('.route-line');
              return { top: Math.round(r.top), bottom: Math.round(r.bottom),
                       vh: innerHeight, dash: poly ? poly.style.strokeDashoffset : 'n/a' };
            }"""
        )
        check("旅程地图完整落在可视区内", jf["top"] >= -2 and jf["bottom"] <= jf["vh"] + 2, jf)
        await page.screenshot(path="tmp_shots/s2_journey.png")

        # ---------- 7. 48 精灵长廊 ----------
        print("\n[7] 48 音标精灵长廊")
        await scroll_to(page, ".chapter--gallery", 1200)
        cards = await page.locator(".sp-card").count()
        check("横向长廊含 48 张音标卡", cards == 48, "实际 %d" % cards)
        await page.screenshot(path="tmp_shots/s3_gallery.png")

        # ---------- 8. 章节导航点击 ----------
        print("\n[8] 章节导航交互")
        await page.evaluate("window.__lenis && window.__lenis.scrollTo(0, {immediate:true})")
        await page.wait_for_timeout(600)
        before = await page.evaluate("window.scrollY")
        await page.locator('.chapter-dots .cdot[data-i="3"]').click()
        await page.wait_for_timeout(1600)
        after = await page.evaluate("window.scrollY")
        check("点击第 4 章导航点后页面发生滚动", after > before + 300, "%d -> %d" % (before, after))

        # ---------- 9. 终章 CTA ----------
        print("\n[9] 终章 CTA 进入闯关")
        await scroll_to(page, ".chapter[data-ch='8']", 1200)
        cta = page.locator(".finale-cta a.btn.red")
        check("终章显示“开启我的闯关之旅”按钮", await cta.count() == 1)
        await cta.click()
        await page.wait_for_timeout(1200)
        url = page.url
        check("点击后跳转到探险地图 #/map", "#/map" in url, url)

        # ---------- 10. 路由清理 ----------
        print("\n[10] 路由切换清理")
        left_ch = await page.locator(".chapter").count()
        left_bg = await page.locator("#story-bg").count()
        left_dots = await page.locator("#chapter-dots").count()
        n_st = await page.evaluate("window.ScrollTrigger ? ScrollTrigger.getAll().length : -1")
        check("离开故事页后章节 DOM 已移除", left_ch == 0, left_ch)
        check("离开故事页后背景层已移除", left_bg == 0, left_bg)
        check("离开故事页后章节导航已移除", left_dots == 0, left_dots)
        check("离开故事页后 ScrollTrigger 已清空", n_st == 0, "剩 %d 个" % n_st)
        check("离开故事页后 story-mode 类已移除",
              not await page.evaluate("document.body.classList.contains('story-mode')"))

        # ---------- 11. 返回故事页 ----------
        print("\n[11] 返回叙事站")
        await page.goto(BASE + "#/story", wait_until="networkidle")
        await page.wait_for_timeout(1400)
        n_ch = await page.locator(".chapter").count()
        n_bg = await page.locator("#story-bg .bg-layer").count()
        n_st = await page.evaluate("ScrollTrigger.getAll().length")
        check("返回后章节重新渲染", n_ch == 9, n_ch)
        check("返回后背景层重新生成", n_bg == 9, n_bg)
        check("返回后 ScrollTrigger 重新注册", n_st > 0, "%d 个" % n_st)
        nav_active = await page.locator('.nav-btn[data-nav="story"].active').count()
        check("底部导航“探险故事”高亮", nav_active == 1)

        # ---------- 12. 音频可播 ----------
        print("\n[12] 音频资源")
        r = await page.request.get("http://127.0.0.1:8765/assets/audio/ep00.opus")
        check("序章音频 ep00.opus 可访问", r.status == 200, r.status)
        r2 = await page.request.get("http://127.0.0.1:8765/assets/img/cover.webp")
        check("序章配图 cover.webp 可访问", r2.status == 200, r2.status)

        # ---------- 13. 移动端 ----------
        print("\n[13] 移动端")
        m = await browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        mp = await m.new_page()
        merr = []
        mp.on("pageerror", lambda e: merr.append(str(e)))
        await mp.goto(BASE, wait_until="networkidle")
        await mp.wait_for_timeout(1400)
        n_ch = await mp.locator(".chapter").count()
        check("移动端渲染 9 章", n_ch == 9, n_ch)
        await mp.screenshot(path="tmp_shots/s4_mobile_story.png")
        check("移动端无 JS 错误", len(merr) == 0, merr[:3])

        # ---------- 14. 控制台错误 ----------
        print("\n[14] 控制台")
        # 过滤已知的 favicon 等无关错误
        real = [e for e in errors if "favicon" not in e.lower()]
        check("桌面端无 JS / 控制台错误", len(real) == 0, real[:3])

        await browser.close()

    print("\n" + "=" * 56)
    passed = sum(1 for _, ok, _ in results if ok)
    print("结果：%d/%d 通过" % (passed, len(results)))
    failed = [n for n, ok, _ in results if not ok]
    if failed:
        print("未通过：")
        for f in failed:
            print("  - " + f)
    print("=" * 56)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
