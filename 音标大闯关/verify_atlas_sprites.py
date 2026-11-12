# -*- coding: utf-8 -*-
"""验收图鉴新接入：精灵立绘 / 详情身份卡 / 稀有度进阶图鉴页。"""
import asyncio
from playwright.async_api import async_playwright

BASE = "http://localhost:8765/index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


async def main():
    out = []
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME,
                                     args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        p = await b.new_page(viewport={"width": 1440, "height": 900})
        errs = []
        p.on("pageerror", lambda e: errs.append(str(e)[:200]))

        # ---------- 1) 图鉴卡片：精灵立绘 img + 稀有度 ----------
        await p.goto(BASE + "#/atlas", wait_until="networkidle", timeout=30000)
        await p.wait_for_timeout(1000)
        tiles = await p.evaluate("""() => {
            const ts=[...document.querySelectorAll('.ph-tile')];
            const withImg=ts.filter(t=>t.querySelector('.ph-sprite img')).length;
            const dim=ts.filter(t=>t.querySelector('.ph-sprite.dim')).length;
            const imgs=[...document.querySelectorAll('.ph-sprite img')];
            const loaded=imgs.filter(i=>i.naturalWidth>0).length;
            return {tiles:ts.length, withImg, dim, imgs:imgs.length, loaded};
        }""")
        out.append(("图鉴卡片精灵立绘(48张且已加载)", tiles["withImg"] >= 48 and tiles["loaded"] >= 48, tiles))
        # 未收集=灰模糊
        out.append(("未收集卡精灵灰化(dim)", tiles["dim"] > 0, tiles))

        # 模拟收集 2 个再验证（Store 的 localStorage key 是 ipa-quest-v1）
        await p.evaluate("() => { const o={stars:{},collected:['iː','p'],sound:true,lastEp:'EP00'}; localStorage.setItem('ipa-quest-v1', JSON.stringify(o)); }")
        await p.reload(wait_until="networkidle")
        await p.wait_for_timeout(800)
        got = await p.evaluate("""() => {
            const got=document.querySelectorAll('.ph-tile.got').length;
            const rar=document.querySelectorAll('.ph-tile .rar-badge').length;
            return {got, rar};
        }""")
        out.append(("收集后 got 卡 + 稀有度徽章", got["got"] >= 2 and got["rar"] >= 2, got))

        # ---------- 2) 详情弹层：身份卡大图 ----------
        await p.locator(".ph-tile").first.click()
        await p.wait_for_timeout(700)
        modal = await p.evaluate("""() => {
            const m=document.querySelector('.modal');
            if(!m) return {found:false};
            const img=m.querySelector('.ph-card-art img');
            return {found:true,
                   cardArt:!!m.querySelector('.ph-card-art'),
                   imgOk: img? img.naturalWidth>0:false,
                   src:(img&&img.src||'').split('/').pop()};
        }""")
        out.append(("详情弹层含身份卡大图", modal.get("cardArt") and modal.get("imgOk"), modal))
        await p.keyboard.press("Escape")
        await p.wait_for_timeout(300)

        # ---------- 3) 稀有度进阶图鉴页 ----------
        await p.goto(BASE + "#/atlas/rarity", wait_until="networkidle", timeout=30000)
        await p.wait_for_timeout(1000)
        rar = await p.evaluate("""() => {
            const prog=document.querySelector('.atlas-progress img');
            const sec=[...document.querySelectorAll('.rar-section')];
            const sprites=document.querySelectorAll('.rar-grid .ph-sprite img').length;
            const secNames=sec.map(s=>s.querySelector('.rar-badge')?s.querySelector('.rar-badge').textContent:'');
            return {progress: prog?prog.naturalWidth>0:false, sections:sec.length, secNames, sprites};
        }""")
        out.append(("稀有度页：进阶总图加载", rar["progress"], rar))
        out.append(("稀有度页：6 个稀有度分组", rar["sections"] == 6, rar["secNames"]))
        out.append(("稀有度页：分组内精灵立绘(48)", rar["sprites"] >= 48, rar["sprites"]))

        # ---------- 资源可达（抽样 webp）----------
        net = await p.evaluate("""() => fetch('assets/sprites/rarity_progress.webp').then(r=>r.status)
            .then(s=>fetch('assets/sprites/cards/U01.webp').then(r2=>r2.status).then(s2=>({prog:s,card:s2})))""")
        out.append(("稀有度总图+身份卡 webp 可达200", net.get("prog")==200 and net.get("card")==200, net))

        await b.close()

    print("=== 图鉴新接入验收 ===")
    ok = True
    for name, passed, detail in out:
        print(("  [PASS] " if passed else "  [FAIL] ") + name + "  -> " + str(detail))
        ok = ok and passed
    print("页面 JS 错误:", errs or "无")
    print("总体:", ("全部通过 ✅（JS 无错误）" if ok and not errs else "存在失败 ❌"))


asyncio.run(main())
