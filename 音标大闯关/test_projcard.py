# -*- coding: utf-8 -*-
"""端到端验证「项目代表词卡」三入口：首页 chip / 关卡页主词 / 图鉴按钮。"""
import asyncio, os, sys
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:8767/"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(HERE, "assets", "audio", "ph")

ERRS = []

def local_ph_size():
    d = {}
    for f in os.listdir(PH):
        if f.endswith(".opus"):
            d[f[:-5].upper()] = os.path.getsize(os.path.join(PH, f))
    return d


async def main():
    ph = local_ph_size()
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME,
                                     args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(viewport={"width": 1440, "height": 900})
        await ctx.add_init_script(
            "localStorage.setItem('ipa-quest-v1', JSON.stringify({stars:{EP00:1,EP01:1,EP02:1},collected:[],sound:true,lastEp:'EP02'}));")
        p = await ctx.new_page()
        p.on("pageerror", lambda e: ERRS.append(str(e)[:200]))
        ok = True

        # ---------- ① 首页故事线 chip ----------
        await p.goto(BASE + "#/story", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(800)
        await p.locator(".sp-chip").first.click()
        await p.wait_for_timeout(700)
        s1 = await p.evaluate("""() => {
          const m = document.querySelector('.projcard');
          const a = window.AudioMgr.el;
          return {
            modal: !!m,
            title: m ? (m.querySelector('.projcard-name')?.textContent || '') : '',
            mainChip: m ? (m.querySelector('.word-chip.main .ipa')?.textContent || '') : '',
            from: m ? (m.querySelector('.projcard-from')?.textContent || '') : '',
            srcTail: a ? (a.currentSrc.split('/').pop() || '') : '',
            srcDir: a && a.currentSrc ? (a.currentSrc.includes('/ph/') ? 'ph/' : 'root/') : null,
            paused: a ? a.paused : null, rs: a ? a.readyState : null,
          };
        }""")
        c1 = s1["modal"] and s1["srcDir"] == "ph/" and (s1["rs"] or 0) >= 1
        ok = ok and c1
        print("① 首页 chip ->", s1, "-> 弹词卡+播ph/?", "✅" if c1 else "❌")

        # 关闭当前弹窗（点弹窗自带的 close-x）
        await p.evaluate("document.querySelector('.modal-layer .close-x')?.click()")
        await p.evaluate("document.querySelector('#modal-layer').hidden=true; document.querySelector('#modal-layer').innerHTML=''")
        await p.wait_for_timeout(200)

        # ---------- ② 关卡页 EP02 主词 chip ----------
        await p.goto(BASE + "#/level/EP02", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(500)
        mainN = await p.evaluate("() => document.querySelectorAll('.word-chip.main').length")
        mainTxt = await p.evaluate("() => document.querySelector('.word-chip.main .ipa')?.textContent || ''")
        await p.locator(".word-chip.main").first.click()
        await p.wait_for_timeout(800)
        s2 = await p.evaluate("""() => {
          const a = window.AudioMgr.el;
          return {
            srcTail: a ? (a.currentSrc.split('/').pop() || '') : '',
            srcDir: a && a.currentSrc ? (a.currentSrc.includes('/ph/') ? 'ph/' : 'root/') : null,
            rs: a ? a.readyState : null,
          };
        }""")
        c2 = mainN >= 1 and s2["srcDir"] == "ph/" and (s2["rs"] or 0) >= 1
        ok = ok and c2
        print("② 关卡页 EP02: 主词 chip 数=" + str(mainN) + " 首主词=" + mainTxt,
              "-> 点主词:", s2, "-> 播ph/真人录音?", "✅" if c2 else "❌")

        # ---------- ③ 图鉴弹层「听真人代表词」按钮 ----------
        await p.goto(BASE + "#/atlas", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(600)
        # 图鉴卡片点第一张 -> 弹层 -> 找「听真人代表词」按钮
        await p.evaluate("() => { document.querySelector('.ph-tile')?.click(); }")
        await p.wait_for_timeout(400)
        btns = await p.evaluate("""() => Array.from(document.querySelectorAll('.modal .btn'))
          .map(b => b.textContent.trim())""")
        await p.evaluate("""() => {
          const bs = Array.from(document.querySelectorAll('.modal .btn'));
          const t = bs.find(b => /真人|代表词/.test(b.textContent));
          if (t) t.click();
        }""")
        await p.wait_for_timeout(500)
        s3 = await p.evaluate("""() => {
          const m = document.querySelector('.projcard');
          const a = window.AudioMgr.el;
          return {
            modal: !!m,
            srcTail: a ? (a.currentSrc.split('/').pop() || '') : '',
            srcDir: a && a.currentSrc ? (a.currentSrc.includes('/ph/') ? 'ph/' : 'root/') : null,
            rs: a ? a.readyState : null,
          };
        }""")
        c3 = s3["modal"] and s3["srcDir"] == "ph/"
        ok = ok and c3
        print("③ 图鉴弹层 按钮=" + str(btns), "->", s3, "-> 弹词卡?", "✅" if c3 else "❌")

        # ---------- ④ 48 真人录音字节 vs 本地 ----------
        rows = await p.evaluate("""async (expect) => {
          const res = [];
          for (const k of Object.keys(expect)) {
            try {
              const r = await fetch('assets/audio/ph/' + k.toLowerCase() + '.opus', {cache: 'no-store'});
              const cl = r.headers.get('content-length');
              res.push({unit: k, bytes: cl !== null ? parseInt(cl,10) : -1,
                         type: r.headers.get('content-type') || ''});
            } catch (e) { res.push({unit: k, bytes: -1, type: 'ERR:' + String(e).slice(0,20)}); }
          }
          return res;
        }""", ph)
        bad = [r for r in rows if r["bytes"] != ph[r["unit"]]]
        print("④ 48 真人录音字节: " + str(48 - len(bad)) + "/48 与本地一致"
              + (" ✅" if not bad else " ❌ 不符: " + str(bad[:3])))
        ok = ok and (not bad)

        await b.close()

    print("\n==== 判定 ====")
    print("全部通过 ✅" if ok and not ERRS else "存在失败 ❌", "| JS 错误:", ERRS or "无")
    sys.exit(0 if ok and not ERRS else 1)


asyncio.run(main())
