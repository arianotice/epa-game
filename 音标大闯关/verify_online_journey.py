# -*- coding: utf-8 -*-
"""线上验证（192.144.226.216）：①第六幕藏宝行进图  ②48 纯音标短音（字节级比对）。

针对 Caddy「不存在资源也返回 index.html(200)」的 catch-all，短音用
【本地字节数 vs 线上 Content-Length】比对判定真实部署，避免 200 假阳性。
"""
import asyncio, os, sys
from playwright.async_api import async_playwright

ORIGIN = "http://192.144.226.216"
BASE = ORIGIN + "/index.html"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
PH_DIR = os.path.join(HERE, "assets", "audio", "ph")

JOURNEY = """() => {
  const nodes = [...document.querySelectorAll('.jnode')];
  return {
    total: nodes.length,
    withGem: nodes.filter(n => n.querySelector('.gem')).length,
    withX:   nodes.filter(n => n.querySelector('.xmark')).length,
    lit: document.querySelectorAll('.jnode.lit').length,
  };
}"""

SIZE_CHECK = """async (expect) => {
  const keys = Object.keys(expect);
  const res = [];
  for (const k of keys) {
    try {
      const r = await fetch('assets/audio/ph/' + k.toLowerCase() + '.opus', {cache: 'no-store'});
      const cl = r.headers.get('content-length');
      res.push({unit: k, status: r.status,
                bytes: (cl !== null) ? parseInt(cl, 10) : -1,
                type: r.headers.get('content-type') || ''});
    } catch (e) { res.push({unit: k, status: 0, bytes: -1, type: 'ERR:' + String(e).slice(0,30)}); }
  }
  return res;
}"""


def load_local_sizes():
    d = {}
    for f in os.listdir(PH_DIR):
        if f.endswith(".opus"):
            d[f[:-5].upper()] = os.path.getsize(os.path.join(PH_DIR, f))
    return d


async def main():
    local = load_local_sizes()
    print("本地纯音标短音数量:", len(local), "(期望 48)")

    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME,
                                     args=["--no-sandbox", "--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(viewport={"width": 1440, "height": 900})
        p = await ctx.new_page()
        errs = []
        p.on("pageerror", lambda e: errs.append(str(e)[:200]))
        ok = True

        # ---------- ① 第六幕藏宝行进图 ----------
        await p.goto(BASE + "#/story", wait_until="networkidle", timeout=40000)
        await p.wait_for_timeout(1000)
        off = await p.evaluate(JOURNEY)
        print("① 藏宝行进图（未点亮）:", off)
        await p.locator("#journey-play").click()
        await p.wait_for_timeout(3200)
        on = await p.evaluate(JOURNEY)
        print("   点亮后:", on)
        c1 = (off["total"] == 30 and off["withGem"] == 30 and off["withX"] == 30
              and on["lit"] == 30)
        ok = ok and c1
        print("   判定：30 节点全带宝石+✕、点亮 30/30 ->", "✅" if c1 else "❌")

        # ---------- ② 48 纯音标短音：本地字节 vs 线上 Content-Length ----------
        if not local:
            print("② 本地 ph/ 为空，无法比对"); ok = False
        else:
            rows = await p.evaluate(SIZE_CHECK, local)
            good = sum(1 for r in rows if r["bytes"] == local[r["unit"]])
            mismatch = [r for r in rows if r["bytes"] != local[r["unit"]]]
            print("② 纯音标短音字节比对: " + str(good) + "/" + str(len(local)),
                  "-> " + ("✅ 全部一致(真部署)" if not mismatch else "❌ " + str(len(mismatch)) + " 个不符"))
            for m in mismatch[:8]:
                print("   不符:", m, "期望", local.get(m["unit"]))
            ok = ok and (good == 48 and not mismatch)

        # ---------- ③ 抽 1 个纯音标短音内容嗅探（防 Caddy 兜底）----------
        sniff = await p.evaluate("""async () => {
            const r = await fetch('assets/audio/ph/u29.opus', {cache:'no-store'});
            const b = await r.arrayBuffer();
            const head = new Uint8Array(b).slice(0, 4);
            const hex = [...head].map(x => x.toString(16).padStart(2,'0')).join(' ');
            return {bytes: b.byteLength, head: hex, isHtml: head[0]===0x3c && head[1]===0x21};
        }""")
        print("③ 嗅探 u29.opus 头部:", sniff, "->", "真 opus(非html)" if not sniff.get("isHtml") else "Caddy 兜底❌")
        ok = ok and not sniff.get("isHtml")

        await b.close()

    print("\n==== 线上综合判定 ====")
    print("全部通过 ✅" if ok and not errs else "存在失败 ❌", "| JS 错误:", errs or "无")
    sys.exit(0 if ok and not errs else 1)


asyncio.run(main())
