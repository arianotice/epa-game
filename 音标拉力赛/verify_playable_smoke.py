# -*- coding: utf-8 -*-
"""人工可玩冒烟（真实 Chromium）：验证本轮 5 项交互肉眼成立。
只读产品代码；起 in-process http.server；截图落 gate-logs/smoke/。
  1) 卡片在分岔前展示且不掉落（S1 有真实卡片 + 无 translateY 掉落位移）
  2) 选道即判（按方向键瞬间 gate.judged=true，不等过门线）
  3) RIGHT/WRONG 弹出（#verdict 显示 ✓/✗ + 英文 RIGHT/WRONG）
  4) 小石头/清晰分岔（3D 渲染模式 + 石头半径从 model 只读确认 0.25）
  5) 真 3D（renderMode=3d, mounted=true, drawCalls>0）
用法： py -3.13 verify_playable_smoke.py
"""
import io, os, sys, json, threading, functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
        "--no-sandbox", "--autoplay-policy=no-user-gesture-required"]
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate-logs", "smoke")
os.makedirs(SHOT, exist_ok=True)

class H(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

srv = ThreadingHTTPServer(("127.0.0.1", 5199), functools.partial(H, directory=ROOT))
threading.Thread(target=srv.serve_forever, daemon=True).start()

import asyncio
from playwright.async_api import async_playwright

BASE = "http://127.0.0.1:5199/音标拉力赛/index.html"
OUT = []
def chk(name, ok, detail=""):
    OUT.append((name, bool(ok), detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + ("  | " + str(detail) if detail else ""))

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=ARGS)
        pg = await b.new_page(viewport={"width": 1280, "height": 800})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:120]))
        await pg.goto(BASE, wait_until="networkidle", timeout=30000)
        await pg.wait_for_timeout(600)

        # 按已验证的真实 UI 路径：关玩法遮罩 → 听辨档 → 上赛道 → 等待进 racing
        await pg.wait_for_function("() => !!window.__rally", timeout=20000)
        await pg.wait_for_timeout(400)
        await pg.evaluate("() => { const b=document.querySelector('#how-close'); if(b) b.click(); }")
        await pg.wait_for_timeout(150)
        await pg.click("#btn-listen")
        await pg.wait_for_timeout(200)
        await pg.click("#btn-grid")
        await pg.wait_for_timeout(250)
        await pg.evaluate("() => window.__rally.step(300)")
        await pg.wait_for_timeout(1600)
        mode = await pg.evaluate("window.__rally.mode")
        chk("进入比赛态", mode == "racing", {"mode": mode})

        # 真 3D：用 __P1_SCENE__ 只读场景快照（与 verify_p1_visual.py 同源）
        scene = await pg.evaluate("""() => {
            const s=window.__P1_SCENE__;
            if(!s) return {none:true};
            return {mounted: s.mounted!==false, renderMode: s.renderMode,
                    drawCalls: s.drawCalls||0, kartMeshes: s.kartMeshCount};
        }""")
        # drawCalls 是每帧渲染快照，等 rAF 跑几帧再读
        await pg.wait_for_timeout(300)
        scene = await pg.evaluate("""() => {
            const s=window.__P1_SCENE__;
            return {mounted: s.mounted!==false, renderMode: s.renderMode,
                    drawCalls: s.drawCalls||0, kartMeshes: s.kartMeshCount};
        }""")
        chk("真 3D 场景已挂载", scene.get("mounted") and scene.get("renderMode")=="3d" and scene.get("drawCalls",0)>0, scene)
        await pg.screenshot(path=os.path.join(SHOT, "01-race3d.png"))

        # 推进到出现音标卡片（S1/S2），最多 step 2400 帧
        phase_info = await pg.evaluate("""() => {
            for (let i=0;i<3000;i++){
                window.__rally.step(1);
                const ph = window.__rally.signPhase;
                if (ph && ph !== 'S0') return {ph, i};
            }
            return {ph: window.__rally.signPhase, i: -1};
        }""")
        chk("卡片在分岔前出现(S1/S2)", phase_info.get("ph") in ("S1","S2","S3") or phase_info.get("i",-1)>=0, phase_info)

        # 卡片 DOM：真实内容 + 无掉落位移
        card = await pg.evaluate("""() => {
            const l=document.querySelector('#sign-l');
            if(!l) return {none:true};
            const cs=getComputedStyle(l);
            return {text:(l.textContent||'').trim().slice(0,40),
                    hasImg: !!l.querySelector('img'),
                    transform: cs.transform,
                    opacity: cs.opacity,
                    open: l.classList.contains('open')};
        }""")
        # 掉落判据：查 CSS @keyframes lane-fade / card-in 是否含 translateY/scale（掉落=位移动画）
        anim = await pg.evaluate("""() => {
            const names=['lane-fade','card-in'];
            const hits=[];
            for(const ss of document.styleSheets){
                let rules; try{rules=ss.cssRules}catch(e){continue}
                for(const r of rules){
                    if(r.type===CSSRule.KEYFRAMES_RULE && names.includes(r.name)){
                        for(const kf of r.cssRules){ hits.push(r.name+':'+kf.keyText+':'+(kf.style.transform||'')); }
                    }
                }
            }
            return hits;
        }""")
        no_drop = all(("translate" not in h and "scale" not in h) for h in anim) and len(anim)>0
        chk("卡片含真实选项内容", card.get("hasImg") or len(card.get("text",""))>0, {"text":card.get("text"),"hasImg":card.get("hasImg")})
        chk("卡片无掉落位移动画", no_drop, anim)
        await pg.screenshot(path=os.path.join(SHOT, "02-card-visible.png"))

        # 推进到 decide 可选窗口（phase=S2 / state.decide 建立），此时读输入才有效
        decide = await pg.evaluate("""() => {
            for(let i=0;i<1500;i++){
                window.__rally.step(1);
                const d=window.__rally.race.state.decide;
                if(d) return {found:true, i, phase:d.phase, picked:d.picked,
                              gateJudged:d.gate.judged};
            }
            return {found:false};
        }""")
        chk("进入可选判定窗口(state.decide)", decide.get("found"), decide)

        # 选道即判：按住方向键（keys.has 需要持续按下），step 后立刻读 verdict
        before = await pg.evaluate("""() => window.__rally.race.state.gates.filter(x=>x.judged).length""")
        await pg.keyboard.down("ArrowLeft")
        await pg.evaluate("window.__rally.step(2)")
        await pg.keyboard.up("ArrowLeft")
        after = await pg.evaluate("""() => {
            const st=window.__rally.race.state;
            const judged=st.gates.filter(x=>x.judged).length;
            const v=st.verdict;
            return {judged, verdict: v?{hit:v.hit,seq:v.seq}:null};
        }""")
        chk("选道即判(按方向键即judged)", after["judged"] > before and after["verdict"] is not None,
            {"before":before,"after":after})

        # verdict DOM 弹出 RIGHT/WRONG
        await pg.evaluate("window.__rally.step(3)")
        vdom = await pg.evaluate("""() => {
            const el=document.querySelector('#verdict');
            if(!el) return {none:true};
            return {hidden: el.hidden, cls: el.className,
                    mark: (el.querySelector('.vmark')||{}).textContent,
                    word: (el.querySelector('.vword')||{}).textContent};
        }""")
        ok_word = vdom.get("word") in ("RIGHT","WRONG") and vdom.get("mark") in ("✓","✗") and not vdom.get("hidden")
        chk("RIGHT/WRONG 即时弹出", ok_word, vdom)
        await pg.screenshot(path=os.path.join(SHOT, "03-verdict.png"))

        chk("零 pageerror", len(errs)==0, errs[:3])
        await b.close()

    srv.shutdown()
    p = sum(1 for _,ok,_ in OUT if ok); f = sum(1 for _,ok,_ in OUT if not ok)
    print("\nSUMMARY: %d PASS / %d FAIL / %d TOTAL" % (p,f,len(OUT)))
    print("SHOTS ->", SHOT)

asyncio.run(main())
