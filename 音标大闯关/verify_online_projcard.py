# -*- coding: utf-8 -*-
"""线上验收（http://192.144.226.216）：项目代表词卡 + 48 真人录音短音。

针对 Caddy「文件不存在也返回 index.html(200)」的 catch-all 兜底：
- 新增/改动的 js/css 用「内容特征 + 字节数 ≠ index.html」判定真实部署；
- 48 短音用「本地字节数 vs 线上 Content-Length」逐一比对。
再用 headless Chrome 验证三入口行为：首页 chip / 关卡页主词 chip / 图鉴按钮 → 弹词卡 + 播 ph/ 真人录音。
"""
import asyncio, os, sys
from playwright.async_api import async_playwright

BASE = "http://192.144.226.216/"
ORIGIN = "http://192.144.226.216"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(HERE, "assets", "audio", "ph")


def local_ph_size():
    d = {}
    for f in os.listdir(PH):
        if f.endswith(".opus"):
            d[f[:-5].upper()] = os.path.getsize(os.path.join(PH, f))
    return d


# 线上资源探测：返回每个 path 的 {bytes, head, hit}
RES_CHECK = r"""async (paths) => {
  const out = {};
  for (const p of paths) {
    try {
      const r = await fetch(p, {cache: 'no-store'});
      const t = await r.text();
      const cl = r.headers.get('content-length');
      out[p] = {
        status: r.status,
        bytes: (cl !== null) ? parseInt(cl,10) : t.length,
        len: t.length,
        head: t.slice(0, 60),
        body: t,
      };
    } catch (e) { out[p] = {status: 0, bytes: -1, len: 0, head: 'ERR:'+String(e).slice(0,30), body: ''}; }
  }
  return out;
}"""


async def main():
    ph = local_ph_size()
    print("本地 ph/*.opus 数量:", len(ph), "(期望 48)")

    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME,
                                     args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(viewport={"width": 1440, "height": 900})
        await ctx.add_init_script(
            "localStorage.setItem('ipa-quest-v1', JSON.stringify({stars:{EP00:1,EP01:1,EP02:1},collected:[],sound:true,lastEp:'EP02'}));")
        p = await ctx.new_page()
        errs = []
        p.on("pageerror", lambda e: errs.append(str(e)[:200]))
        ok = True

        await p.goto(BASE, wait_until="domcontentloaded")

        # ---------- 0) 新增/改动文件是否真上线（防 Caddy 兜底） ----------
        paths = ["index.html", "js/projcard.js", "js/data.js", "js/story.js",
                 "js/level.js", "js/atlas.js", "css/style.css"]
        res = await p.evaluate(RES_CHECK, paths)
        idx_len = res["index.html"]["len"]
        checks = [
            ("index.html 引用 projcard.js", "js/projcard.js" in res["index.html"]["body"]),
            ("projcard.js 是真实新文件", "window.ProjCard" in res["js/projcard.js"]["body"]
                 and res["js/projcard.js"]["len"] > 1000),
            ("data.js 含 projMain/projWords", "projMain" in res["js/data.js"]["body"]
                 and "projWords" in res["js/data.js"]["body"]),
            ("story.js 接入 ProjCard.show", "ProjCard.show" in res["js/story.js"]["body"]),
            ("level.js 接入真人主词 chip", "rec-tag" in res["js/level.js"]["body"]),
            ("atlas.js 接入 ProjCard.show", "ProjCard.show" in res["js/atlas.js"]["body"]),
            ("style.css 含 .projcard 样式", ".projcard" in res["css/style.css"]["body"]),
        ]
        print("\n0) 线上文件落地检查（index.html 字节=" + str(idx_len) + "，防御 Caddy 兜底）")
        for name, good in checks:
            print("   ", "✅" if good else "❌", name)
            ok = ok and good
        # projcard.js 若为兜底 html 会与 index.html 等长
        if res["js/projcard.js"]["len"] == idx_len and idx_len > 0:
            print("    ❌ projcard.js 疑似 Caddy 兜底(与 index.html 等长)")
            ok = False

        # ---------- ① 首页故事线 chip → 弹词卡 + 播 ph/ ----------
        await p.goto(BASE + "#/story", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(800)
        await p.locator(".sp-chip").first.click()
        await p.wait_for_timeout(700)
        s1 = await p.evaluate("""() => {
          const m = document.querySelector('.projcard');
          const a = window.AudioMgr.el;
          return {
            modal: !!m,
            name: m ? (m.querySelector('.projcard-name')?.textContent || '') : '',
            mainChip: m ? (m.querySelector('.word-chip.main .ipa')?.textContent || '') : '',
            from: m ? (m.querySelector('.projcard-from')?.textContent || '') : '',
            srcTail: a ? (a.currentSrc.split('/').pop() || '') : '',
            srcDir: a && a.currentSrc ? (a.currentSrc.includes('/ph/') ? 'ph/' : 'root/') : null,
            paused: a ? a.paused : null, rs: a ? a.readyState : null,
          };
        }""")
        c1 = s1["modal"] and s1["mainChip"] == "bee" and s1["srcDir"] == "ph/" and (s1["rs"] or 0) >= 1
        ok = ok and c1
        print("\n① 首页 chip ->", s1, "-> 弹词卡+播ph/?", "✅" if c1 else "❌")

        await p.evaluate("document.querySelector('.modal-layer .close-x')?.click()")
        await p.evaluate("var l=document.querySelector('#modal-layer'); if(l){l.hidden=true;l.innerHTML='';}")
        await p.wait_for_timeout(200)

        # ---------- ② 关卡页 EP02 真人主词 chip ----------
        await p.goto(BASE + "#/level/EP02", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(500)
        mainN = await p.evaluate("() => document.querySelectorAll('.word-chip.main').length")
        mainTxt = await p.evaluate("() => document.querySelector('.word-chip.main .ipa')?.textContent || ''")
        if mainN:
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

        # ---------- ③ 图鉴弹层「听真人代表词」→ 弹词卡 ----------
        await p.goto(BASE + "#/atlas", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(600)
        await p.evaluate("() => { document.querySelector('.ph-tile')?.click(); }")
        await p.wait_for_timeout(400)
        btns = await p.evaluate("""() => Array.from(document.querySelectorAll('.modal .btn'))
          .map(b => b.textContent.trim())""")
        await p.evaluate("""() => {
          const bs = Array.from(document.querySelectorAll('.modal .btn'));
          const t = bs.find(b => /真人|代表词/.test(b.textContent));
          if (t) t.click();
        }""")
        await p.wait_for_timeout(600)
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

        # ---------- ④ 48 真人录音：本地字节 vs 线上 Content-Length ----------
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
        good = 48 - len(bad)
        print("\n④ 48 真人录音字节比对: " + str(good) + "/48 与本地一致",
              "✅ 全部一致(真部署)" if not bad else "❌ 有 " + str(len(bad)) + " 个不符")
        for m in bad[:5]:
            print("    不符:", m, "期望", ph.get(m["unit"]))
        ok = ok and (not bad and good == 48)

        # ---------- ⑤ 嗅探 u01.opus 头部=OggS（非 html 兜底） ----------
        sniff = await p.evaluate("""async () => {
          const r = await fetch('assets/audio/ph/u01.opus', {cache:'no-store'});
          const b = await r.arrayBuffer();
          const u = new Uint8Array(b.slice(0,4));
          return Array.from(u).map(x=>x.toString(16).padStart(2,'0')).join(' ');
        }""")
        c5 = sniff == "4f 67 67 53"
        ok = ok and c5
        print("⑤ u01.opus 头部:", sniff, "(应为 4f 67 67 53 = OggS)", "✅" if c5 else "❌")

        await b.close()

    print("\n==== 线上综合判定 ====")
    print("全部通过 ✅" if ok and not errs else "存在失败 ❌", "| JS 错误:", errs or "无")
    sys.exit(0 if ok and not errs else 1)


asyncio.run(main())
