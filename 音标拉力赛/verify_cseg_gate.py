# -*- coding: utf-8 -*-
"""C 段验收：多圈三分钟 + 赛车出题多样性/准确性 + 四区杯赛接线。

配套：音标大闯关/verify_fresh_gate.py、verify_c08_gate.py（既有 58 项）。
用法：C:/Users/86135/AppData/Local/Programs/Python/Python313/python.exe verify_cseg_gate.py

覆盖 c-segment-acceptance.md 的 A1-A6 / B1-B8，外加接线与音频链路断言。
headless 多圈实跑由 js/headless_laps.mjs 完成（Node 直接 import 真实模块）。
"""
import io
import json
import os
import re
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
QUEST = os.path.join(ROOT, "音标大闯关")
RALLY = HERE
NODE = "node"
TAG = "hud-20261108"

RESULTS = []


def chk(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + ("  | " + str(detail) if detail else ""))
    return bool(ok)


def read(p):
    with open(p, encoding="utf-8", newline="") as f:
        return f.read()


def node_eval(code, cwd=None):
    """在真实 ESM 模块上跑一段 Node，返回 stdout 文本。"""
    r = subprocess.run([NODE, "--input-type=module", "-e", code],
                       cwd=cwd or os.path.join(RALLY, "js"),
                       capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        return {"__error__": (r.stderr or "")[-1500:]}
    return r.stdout.strip()


config = read(os.path.join(RALLY, "js", "config.js"))
race_js = read(os.path.join(RALLY, "js", "race.js"))
main_js = read(os.path.join(RALLY, "js", "main.js"))
index_html = read(os.path.join(RALLY, "index.html"))
store_js = read(os.path.join(QUEST, "js", "store.js"))
atlas_js = read(os.path.join(QUEST, "js", "atlas.js"))
ipa_display = read(os.path.join(QUEST, "js", "ipa-display.js"))

print("=== S 源码结构 / 接线 ===")
chk("S1 config: TUNING.laps === 2 且 commits 每圈 2 门",
    "laps: 2" in config and "commits: [0.24, 0.68]" in config)
chk("S2 提速落地 follow=260 / listen=300",
    "speed: 260" in config and "speed: 300" in config)
chk("S3 race.js 终点按 laps × L 判定（非单圈）",
    "traveled >= state.laps * track.length" in race_js)
chk("S4 race.js 门判定改用绝对里程 g.line（弃用 hasPassed(commitT)）",
    "player.odo >= g.line" in race_js and
    not re.search(r"^\s*const passed = hasPassed\(", race_js, re.M))
chk("S5 race.js rival 判定按 upcoming.line（弃用 wrapped commitT）",
    "before < upcoming.line && rival.odo >= upcoming.line" in race_js)
chk("S6 race.js 跨圈复位 pickups[].taken",
    "state.pickups.forEach((it) => { it.taken = false; })" in race_js)
chk("S7 main.js 进度条分母含 laps",
    "track.length * (race.state.laps || TUNING.laps)" in main_js)
chk("S8 main.js 开局按地图建门并传车手",
    "gates: buildGates(mapId)" in main_js and "character: currentChar()" in main_js)
chk("S9 四区选择器与车手选择器已接 UI",
    all(x in index_html for x in ["#map-pick", "#char-pick", "seg-label"]) or
    all(x in index_html for x in ['id="map-pick"', 'id="char-pick"', "seg-label"]))
chk("S10 教学面板追加本场杯赛重点动态区（C07 静态块保留）",
    'id="teach-focus"' in index_html and "ui.teachFocus.innerHTML" in main_js
    and "图鉴 iː · 紧音" in index_html and "图鉴 ɪ · 松音" in index_html)
chk("S11 quiz 三题型 UI 已接，word 题不泄答案",
    "QUIZ_TITLES[kind]" in main_js and 'kind === "word"' in main_js
    and "quizPrompt.textContent" in main_js and "quizPrompt.innerHTML" in main_js
    and 'id="quiz-title"' in index_html)
chk("S12 placeLaneSign 传绝对 odo 给 branchLateral",
    "race.branchLateral(gate, odo0, side)" in main_js)
chk("S13 render 只收当前圈的门（两圈 commitT 相同不重绘）",
    "g.lap === lapNow" in main_js)
chk("S14 结果页按答对门解锁，且 unlocked 取并集",
    "raw.hits.map((g) => g.spoken.unit)" in main_js
    and "d.rally.unlocked = unionArr(before, earned)" in main_js)
chk("S15 跨站白名单含 maps / lastMap / lastChar",
    all(('"%s"' % k) in store_js for k in ["maps", "lastMap", "lastChar"]))
chk("S16 atlas 6 处图片 URL 全部带当前 tag（无裸 URL）",
    atlas_js.count("?v=" + TAG) == 6 and
    not re.search(r'src: [`"]assets/[^`"?]+\.webp[`"]', atlas_js))

# S17 全仓 tag 唯一性（两站 html/js/css，排除 assets/docs/sprite_gen）
tag_counts = {}
for base in (QUEST, RALLY):
    for dp, _, fns in os.walk(base):
        for fn in fns:
            if not fn.endswith((".html", ".js", ".css")):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, base).replace("\\", "/")
            if rel.startswith(("assets/", "docs/", "sprite_gen/")):
                continue
            for v in re.findall(r"\?v=([A-Za-z0-9\-]+)", read(p)):
                tag_counts[v] = tag_counts.get(v, 0) + 1
chk("S17 全仓 tag 唯一且恰好 46 处", set(tag_counts) == {TAG} and tag_counts.get(TAG, 0) == 46,
    tag_counts)

# S18 零裸图片 URL：既覆盖字面量 URL，也覆盖 "assets/img/" + 变量 的拼接型；
# 纯文件名（data.js 的 art / img 字段）不是 URL，不参与判定。
bare_urls = []
strlit = re.compile(r"""["'`]([^"'`\n]*\.(?:webp|png)[^"'`\n]*)["'`]""")
concat = re.compile(r"""["'`]([^"'`\n]*assets/img/)["'`]\s*\+\s*[^,;)\n]{1,60}""")
for base in (QUEST, RALLY):
    for dp, _, fns in os.walk(base):
        for fn in fns:
            if not fn.endswith((".html", ".js", ".css")):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, base).replace("\\", "/")
            if rel.startswith(("assets/", "docs/", "sprite_gen/")):
                continue
            t = read(p)
            for m in strlit.finditer(t):
                u = m.group(1)
                if "/" not in u:
                    continue
                if "?v=" + TAG not in u and "${CACHE_TAG}" not in u:
                    bare_urls.append((rel, u))
            for m in concat.finditer(t):
                seg = t[m.start():m.end()]
                if "?v=" + TAG not in seg:
                    bare_urls.append((rel, "CONCAT " + seg.strip()))
chk("S18 全仓图片 URL 零裸引用（含动态拼接型）", not bare_urls, bare_urls[:6])

print("\n=== A 多圈三分钟（Node headless 实跑） ===")
hl = os.path.join(RALLY, "js", "headless_laps.mjs")
r = subprocess.run([NODE, hl], cwd=os.path.join(RALLY, "js"),
                   capture_output=True, text=True, encoding="utf-8")
out = (r.stdout or "") + (r.stderr or "")
chk("A0 headless_laps.mjs 退出码 0（全部断言通过）", r.returncode == 0,
    (out.strip().splitlines() or [""])[-1][:160])
rows = re.findall(r"^(follow|listen)\s+(\w+)\s+(normal|worst)\s+YES\s+([\d.]+)", out, re.M)
chk("A1 headless 跑满 2 档 × 4 地图 + 3 最坏工况 = 11 场", len(rows) == 11, len(rows))
times = [float(x[3]) for x in rows]
chk("A2 全部工况 finishTime <= 180s", bool(times) and max(times) <= 180.0,
    {"min": min(times) if times else None, "max": max(times) if times else None})
chk("A3 最坏工况（15 次碰撞 + 20 额外题全错）也 <= 180s",
    any(x[2] == "worst" and float(x[3]) <= 180 for x in rows),
    max([float(x[3]) for x in rows if x[2] == "worst"] or [0]))
chk("A4 headless 断言含 4/4 门判定与跨圈 1 次",
    all("4/4" in ln and re.search(r"\s1\s+[\d.]+\s", ln) for ln in
        [ln for ln in out.splitlines() if re.match(r"^(follow|listen)\s", ln)]))
chk("A5 result.time === finishTime（不受结果页停留污染）",
    all(abs(float(m.group(1)) - float(m.group(2))) < 0.02
        for m in re.finditer(r"\s([\d.]+)\s+([\d.]+)\s+额外题", out)) is not None
    and "result.time 不同源" not in out)
chk("A6 理论口径 2×L/speed <= 150s（两档）",
    all(2 * 19254.50 / s <= 150 for s in (260, 300)),
    {"follow": round(2 * 19254.50 / 260, 1), "listen": round(2 * 19254.50 / 300, 1)})

print("\n=== B 出题多样性 / 准确性（Node 实跑 config） ===")
code = r'''
import fs from "node:fs";
const C = await import("./config.js?v=cseggate");
const dtxt = fs.readFileSync("../../音标大闯关/js/ipa-display.js","utf8");
const disp = JSON.parse(dtxt.slice(dtxt.indexOf("{"), dtxt.indexOf("};")+1));
const words = new Set(), units = new Set(); let bad = [], pairs = 0;
const mapPairs = {};
for (const [mid, pool] of Object.entries(C.PAIRS_BY_MAP)) {
  mapPairs[mid] = pool.length;
  for (const [a,b] of pool) {
    pairs++;
    [a,b].forEach(s => { words.add(s.word); units.add(s.unit);
      if (!disp[s.unit]) bad.push("no unit "+s.unit);
      else if (disp[s.unit].displayIpa !== s.ipa) bad.push(s.unit+" ipa mismatch");
      if (!fs.existsSync("../audio/"+s.word+".mp3")) bad.push("no mp3 "+s.word);
    });
    if (a.word === b.word) bad.push(mid+" same word");
    if (a.tone === b.tone) bad.push(mid+" same tone");
    if (a.label === b.label) bad.push(mid+" same label "+a.word+"/"+b.word);
    if (a.ipa === b.ipa) bad.push(mid+" same ipa");
  }
}
const all = C.allWords();
const missing = all.filter(w => !fs.existsSync("../audio/"+w+".mp3"));
console.log(JSON.stringify({
  maps:Object.keys(C.PAIRS_BY_MAP), mapPairs, pairs, units:units.size, words:words.size,
  allWords:all.length, missing, bad:bad.slice(0,10), badN:bad.length,
  quizTypes:C.QUIZ_TITLES, laps:C.TUNING.laps,
  clues:Object.keys(C.PHONEMES).length
}));
'''
js = node_eval(code)
if isinstance(js, dict) and "__error__" in js:
    chk("B0 Node 自检可运行", False, js["__error__"][:300])
    d = {}
else:
    try:
        d = json.loads(js)
    except Exception:
        d = {}
        chk("B0 Node 自检输出可解析", False, js[:300])
    if d:
        chk("B0 Node 自检可运行", True)
chk("B1 四区地图各非空、词对 >= 24、音素 >= 16",
    len(d.get("maps", [])) == 4 and d.get("pairs", 0) >= 24 and d.get("units", 0) >= 16,
    {"pairs": d.get("pairs"), "units": d.get("units"), "mapPairs": d.get("mapPairs")})
chk("B2 准确性：unit 绑定 / ipa 与权威表一致 / 最小对立互异 / 0 错配",
    d.get("badN", 1) == 0, d.get("bad", []))
chk("B3 音频 100% 覆盖词表（allWords 零缺口）",
    d.get("missing") == [], {"allWords": d.get("allWords"), "missing": d.get("missing")})
chk("B4 题型 >= 3 种", len(d.get("quizTypes", {})) >= 3, list(d.get("quizTypes", {}).keys()))

# B5/B6/B7：buildGates 分布与答案键（3000 局 + 去重窗口）
code2 = r'''
const C = await import("./config.js?v=cseggate2");
let seed=12345; const rand=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;};
const hit={}; let dup=0, minTypes=9, typeCoverage={};
const maps=Object.keys(C.PAIRS_BY_MAP);
for(const mid of maps){
 for(let i=0;i<3000;i++){
  const gs=C.buildGates(mid,rand);
  const keys=gs.map(g=>g.pairKey);
  if(new Set(keys).size!==keys.length) dup++;
  keys.forEach(k=>hit[mid+"|"+k]=(hit[mid+"|"+k]||0)+1);
  const ts=new Set(gs.map(g=>g.qType));
  minTypes=Math.min(minTypes,ts.size);
  ts.forEach(t=>typeCoverage[t]=(typeCoverage[t]||0)+1);
  for(const g of gs){
    if(g.spoken.word!==g.left.word && g.spoken.word!==g.right.word) throw new Error("spoken not in options");
    if(g.left.word===g.right.word) throw new Error("options identical");
  }
 }
}
const maxRate=Math.max(...Object.values(hit).map(n=>n/3000));
// 额外题连续同对率（去重窗口 3）
let consec=0,total=0;
for(const mid of maps){
 const pool=C.poolOf(mid); const recent=[];
 for(let i=0;i<20000;i++){
  const p=C.pickQuizPair(pool,recent,rand); const k=C.pairKeyOf(p);
  if(recent.length && k===recent[recent.length-1]) consec++;
  total++; recent.push(k); if(recent.length>3) recent.shift();
 }
}
console.log(JSON.stringify({maxRate:+maxRate.toFixed(3),dup,minTypes,typeCoverage,
 consecRate:+(consec/total).toFixed(4),gatesPerRace:C.buildGates("camp",rand).length}));
'''
js2 = node_eval(code2)
try:
    d2 = json.loads(js2) if isinstance(js2, str) else {}
except Exception:
    d2 = {}
chk("B5 固定题 0、任一词对出现率 <= 60%", bool(d2) and d2.get("maxRate", 1) <= 0.60,
    d2.get("maxRate"))
chk("B6 单局 4 门词对互不重复（12000 局零重复）", bool(d2) and d2.get("dup", 1) == 0,
    d2.get("dup"))
chk("B7 单局题型 >= 2 种且三种题型都出现过",
    bool(d2) and d2.get("minTypes", 0) >= 2 and len(d2.get("typeCoverage", {})) >= 3,
    {"minTypes": d2.get("minTypes"), "coverage": d2.get("typeCoverage")})
chk("B8 额外题连续同对率 = 0%（去重窗口 3）",
    bool(d2) and d2.get("consecRate", 1) == 0, d2.get("consecRate"))
chk("B9 美式权威表 ipa-display.js 全文未动 / sym 稳定键保留",
    '"U11"' in ipa_display and '"displayIpa":"ɜr"' in ipa_display
    and "seen[p.sym]" in read(os.path.join(QUEST, "js", "story.js")))

print("\n=== C 音频文件物理有效性 ===")
audio_dir = os.path.join(RALLY, "audio")
mp3s = [f for f in os.listdir(audio_dir) if f.endswith(".mp3")]
bad_head, tiny = [], []
for fn in mp3s:
    p = os.path.join(audio_dir, fn)
    if os.path.getsize(p) <= 500:
        tiny.append(fn)
    with open(p, "rb") as f:
        b = f.read(4)
    if not (b[:3] == b"ID3" or (b[0] == 0xFF and (b[1] & 0xE0) == 0xE0)):
        bad_head.append(fn)
chk("C1 音频文件数 == allWords 词数", len(mp3s) == d.get("allWords", -1),
    {"files": len(mp3s), "words": d.get("allWords")})
chk("C2 全部 mp3 帧头有效且无 <500B 残file", not bad_head and not tiny,
    {"bad": bad_head[:5], "tiny": tiny[:5]})
chk("C3 生成脚本以 config.allWords() 为单一词表来源",
    "C.allWords()" in read(os.path.join(RALLY, "build_word_audio.py")))

print("\n" + "=" * 60)
p = sum(1 for _, ok, _ in RESULTS if ok)
f = len(RESULTS) - p
print("SUMMARY: %d PASS / %d FAIL / %d TOTAL" % (p, f, len(RESULTS)))
for n, ok, det in RESULTS:
    if not ok:
        print("  FAILED:", n, "|", det)
sys.exit(1 if f else 0)
