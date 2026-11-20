# -*- coding: utf-8 -*-
"""S7 · PN-* 真实交互断言（最终回归第 8 步，独立脚本）。

边界：
  - **不挂进 verify_p1_gate.py 的 SUITES**（保持 121 项断言名集合连续两轮一致）。
  - 只读产品代码，零产品改动；不改 result.json / 121 计数；禁止 commit / push / 部署。
  - 作废项（用户 2026-11-14「只做单跳必过」拍板）一律**不写成待实现要求**：
    二段跳 / 260ms 双沿状态机 / input.jump2 / hop===2 / airMax 0.74 / 双击跳更高 /
    两级 lift / 0.9× / Amazing / 随机三选一 / 连击偏向词 / R-2 二选一张力。
  - 词表唯一 Good / Excellent / Marvellous。
  - 人工观感项列 NOT_COVERED，不冒充 PASS。

取证方式：
  - Node 真实模块重放（内联 --input-type=module -e，零新增 .mjs 文件）：
    ① ≥1000 seed 单跳必过（锁定第一颗 rock 车道、标准时机单次 input.jump、滞空见证 cleared）；
    ② 整局自动驾驶观测 rockHits / rock 条目配额 / quizReasons.wall / NPC 速度下限 / finishTime。
  - 静态源码字面量（剥离注释后检查「实现」，注释里的作废字段留痕不作命中）
    + headless_laps.mjs 原路径实跑。

用法： py -3.13 verify_p1_interaction.py
"""
import os
import re
import io
import json
import sys
import subprocess

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
NODE = "node"
LOGDIR = os.path.join(HERE, "gate-logs")
os.makedirs(LOGDIR, exist_ok=True)

RESULTS = []
NOT_COVERED = []


def chk(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("  PASS  " if ok else "  FAIL  ") + name + ("  | " + str(detail) if detail != "" else ""))
    return bool(ok)


def read(rel):
    return open(os.path.join(ROOT, rel), encoding="utf-8", errors="replace").read()


def strip_comments(js):
    """剥离 JS 块注释 / 行注释，仅留可执行代码用于「实现是否存在」检查。

    race.js 的 IMPL-1A 留痕注释里逐字写了「不做 input.jump2 / hop===2」「删 dashLeft /
    hopWindow / jumpCd」等作废字段名，属历史留痕非实现；本函数避免把它们误判为实现命中。
    """
    js = re.sub(r"/\*[\s\S]*?\*/", " ", js)
    js = re.sub(r"//[^\n]*", " ", js)
    return js


# ---------------------------------------------------------------------------
# Node 真实重放取证（内联；顶层 await 由 --input-type=module 提供）
# ---------------------------------------------------------------------------
NODE_PROBE = r'''
const TAG = "fwd-20261120";
const cfg = await import('./js/config.js?v=' + TAG);
const { createTrack } = await import('./js/track.js?v=' + TAG);
const { createRace } = await import('./js/race.js?v=' + TAG);
const { TUNING, DIFFICULTY, buildGates, ROCK_HIT_BAND, ROCK_QUOTA,
        ROCK_HITS_MAX, NPC_MIN_SPEED_RATIO, BOOST, TURBO, SLOW } = cfg;

const audio = new Proxy({}, { get: (_t, k) => (k === "then" ? undefined : () => {}) });
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => mem.set(String(k), String(v)),
  removeItem: (k) => mem.delete(k),
};
mem.set("ipa-quest-v1", JSON.stringify({ rally: { gems: 0, shields: 0 } }));

function seeded(seed) {
  let s = seed >>> 0;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}
const L = createTrack(TUNING).length;
const DT = 1 / 60;
const MAX = 60 * 400;

function rockOdo(item, po) {
  let o = Math.floor(po / L) * L + item.t * L;
  if (o > po + 90) o -= L;
  return o;
}

/* 同源复算 speedNow(player)：baseMul(player)===1（race.js:198），
   与 updateKart(rival):315 的 floor 读取同一时点的 player 状态。 */
function playerSpeedNow(st, diff) {
  const p = st.player;
  let mul = 1;
  if (p.turbo > 0) mul *= TURBO.mul;
  else if (p.boost > 0) mul *= BOOST.mul;
  if (p.slow > 0) mul *= SLOW.mul;
  return diff.speed * mul;
}

/* 场景 A：唯一 P0 单跳必过 —— 锁定第一颗 rock 的车道，标准时机单次 jump，
   跑到该 rock 首次定案，验证 cleared（滞空见证规避）而非撞击。 */
function jumpOne(seed, diffId) {
  const rand = seeded(seed); const real = Math.random; Math.random = rand;
  try {
    const track = createTrack(TUNING);
    const diff = DIFFICULTY[diffId];
    const gates = buildGates("camp", rand);
    const race = createRace({ track, diff, gates, audio, mapId: "camp" });
    const st = race.state;
    const target = st.pickups.filter((p) => p.kind === "rock")[0];
    const lane = target.lateral;
    let steps = 0, jumpFrames = 0;
    while (steps < MAX && !target.taken) {
      st.player.lateral = lane; st.player.laneTarget = lane;
      const d = rockOdo(target, st.player.odo) - st.player.odo;
      const input = {};
      if (d > ROCK_HIT_BAND && d <= ROCK_HIT_BAND + 0.35 * diff.speed) {
        input.jump = true; jumpFrames++;
      }
      race.update(DT, input);
      if (st.quiz) race.finishQuiz(st.quiz.spoken.word);
      steps++;
    }
    return { taken: target.taken, cleared: !!target.cleared,
             hits: st.rockHits, jumpFrames, steps };
  } finally { Math.random = real; }
}

/* 场景 B：整局自动驾驶（不跳），观测撞石封顶 / 条目配额 / 零撞墙题 / NPC 速度下限。
   速度下限只取「连续推进帧」：judge()/pressRivals() 的 `r.odo = ...` 是合法 odo 位置
   钳制（可能令 ΔrivalOdo<=0），属位置修正而非速度，须显式排除，避免假 FAIL。 */
function raceOne(seed, diffId, mapId) {
  const rand = seeded(seed); const real = Math.random; Math.random = rand;
  try {
    const track = createTrack(TUNING);
    const diff = DIFFICULTY[diffId];
    const gates = buildGates(mapId, rand);
    const race = createRace({ track, diff, gates, audio, mapId });
    const st = race.state;
    const rocks = st.pickups.filter((p) => p.kind === "rock");
    let steps = 0, quizRock = 0, quizWall = 0, minRatio = Infinity, minRatioRaw = Infinity;
    let sampleCount = 0, belowCount = 0;
    let floorViolations = 0, floorSamples = 0, minFloorMargin = Infinity;
    let prevP = st.player.odo, prevR = st.rivals.map((r) => r.odo);
    while (!st.finished && steps < MAX) {
      const act = race.activeGate();
      const answering = st.gates.some((g) => g.played && !g.judged);
      let input = {};
      if (act && answering) {
        const t = act.gate.correctLateral;
        const lat = st.player.lateral;
        if (lat < t - 0.04) input = { right: true };
        else if (lat > t + 0.04) input = { left: true };
      }
      race.update(DT, input);
      if (st.quiz) {
        const reason = st.quiz.reason || "?";
        if (reason === "rock") quizRock++;
        if (reason === "wall") quizWall++;
        race.finishQuiz(st.quiz.spoken.word);
      }
      const dP = st.player.odo - prevP;
      const vPlayer = playerSpeedNow(st, diff);
      const floorDt = NPC_MIN_SPEED_RATIO * vPlayer * DT;
      for (let i = 0; i < st.rivals.length; i++) {
        const dR = st.rivals[i].odo - prevR[i];
        if (dP > 0) {
          const ratio = dR / dP;
          if (ratio < minRatioRaw) minRatioRaw = ratio;   // 含合法位置钳制帧，仅诊断
        }
        if (dR > 0) {                                     // rival 本帧确实推进
          if (dP > 0) {
            const ratio = dR / dP;
            if (ratio < minRatio) minRatio = ratio;      // Δodo 瞬时比值（诊断）
            sampleCount++;
            if (ratio < 0.94 - 1e-9) belowCount++;
          }
          // 主判据：逐帧同源 floor 不等式 v_i >= 0.94·v_player_now（race.js:315-316 原式）
          const margin = dR - floorDt;
          if (margin < minFloorMargin) minFloorMargin = margin;
          floorSamples++;
          if (margin < -1e-9) floorViolations++;
        }
      }
      prevP = st.player.odo; prevR = st.rivals.map((r) => r.odo);
      steps++;
    }
    return { finished: st.finished, finishTime: +st.finishTime.toFixed(2),
             rockItems: rocks.length, rockHits: st.rockHits, rockBudget: st.rockBudget,
             quizRock, quizWall, minRatio, minRatioRaw, sampleCount, belowCount,
             floorViolations, floorSamples, minFloorMargin, steps };
  } finally { Math.random = real; }
}

const JUMP_SEEDS = 1000;
const jump = { seeds: JUMP_SEEDS, cleared: 0, hit: 0, notTaken: 0, maxHits: 0, maxSteps: 0, pass: false };
for (let s = 1; s <= JUMP_SEEDS; s++) {
  const r = jumpOne(s, (s % 2) ? "follow" : "listen");
  if (r.cleared) jump.cleared++; else jump.hit++;
  if (!r.taken) jump.notTaken++;
  if (r.hits > jump.maxHits) jump.maxHits = r.hits;
  if (r.steps > jump.maxSteps) jump.maxSteps = r.steps;
}
jump.pass = (jump.cleared === JUMP_SEEDS && jump.hit === 0 &&
             jump.notTaken === 0 && jump.maxHits === 0);

const races = [];
for (const diffId of ["follow", "listen"]) {
  for (const mapId of ["camp", "castle", "kingdom", "peak"]) {
    races.push(raceOne(7, diffId, mapId));
  }
}
for (const seed of [11, 23, 31]) races.push(raceOne(seed, "follow", "camp"));

const raceSummary = {
  count: races.length,
  allFinished: races.every((r) => r.finished),
  maxFinishTime: Math.max(...races.map((r) => r.finishTime)),
  rockItemsSet: [...new Set(races.map((r) => r.rockItems))],
  maxRockHits: Math.max(...races.map((r) => r.rockHits)),
  rockBudget: races[0].rockBudget,
  quizRockTotal: races.reduce((n, r) => n + r.quizRock, 0),
  wallTotal: races.reduce((n, r) => n + r.quizWall, 0),
  minRivalRatio: Math.min(...races.map((r) => r.minRatio)),
  minRivalRatioRaw: Math.min(...races.map((r) => r.minRatioRaw)),
  belowCount: races.reduce((n, r) => n + r.belowCount, 0),
  sampleCount: races.reduce((n, r) => n + r.sampleCount, 0),
  floorViolations: races.reduce((n, r) => n + r.floorViolations, 0),
  floorSamples: races.reduce((n, r) => n + r.floorSamples, 0),
  minFloorMargin: Math.min(...races.map((r) => r.minFloorMargin)),
  constants: { ROCK_QUOTA, ROCK_HITS_MAX, NPC_MIN_SPEED_RATIO, ROCK_HIT_BAND },
};
console.log(JSON.stringify({ jump, races: raceSummary, L: +L.toFixed(2) }));
'''


def run_node_probe():
    r = subprocess.run([NODE, "--input-type=module", "-e", NODE_PROBE],
                       cwd=HERE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    if r.returncode != 0 or not (r.stdout or "").strip():
        chk("S7 Node 取证脚本可执行（真实模块重放）", False,
            {"rc": r.returncode, "stderr": (r.stderr or "")[-600:],
             "stdout": (r.stdout or "")[-200:]})
        return None
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e:
        chk("S7 Node 取证输出为可解析 JSON", False,
            {"err": repr(e), "tail": (r.stdout or "")[-300:]})
        return None


# ---------------------------------------------------------------------------
# 断言
# ---------------------------------------------------------------------------
def main():
    print("=" * 78)
    print("S7 · verify_p1_interaction.py · PN-* 真实交互断言（独立第 8 步）")
    print("=" * 78)

    probe = run_node_probe()
    if probe is None:
        _finish()
        return

    jump = probe["jump"]
    races = probe["races"]

    RACE = read("音标拉力赛/js/race.js")
    TRACK = read("音标拉力赛/js/track.js")
    CONFIG = read("音标拉力赛/js/config.js")
    HEADLESS = read("音标拉力赛/js/headless_laps.mjs")
    MODEL = read("音标拉力赛/js/scene3d-model.mjs")
    RENDER = read("音标拉力赛/js/render.js")
    MAIN = read("音标拉力赛/js/main.js")
    QA = read("音标拉力赛/design/p1-interaction-qa.md")
    IMPL = read("音标拉力赛/design/p1-interaction-impl.md")
    REMAP = read("音标拉力赛/design/p1-interaction-remap.md")
    CSEG = read("音标拉力赛/verify_cseg_gate.py")
    RACE_CODE = strip_comments(RACE)
    MAIN_CODE = strip_comments(MAIN)

    # PN-JUMP-00：唯一 P0 单跳必过（≥1000 seed 可复现、二段跳非前提）
    no_double = all(t not in RACE_CODE and t not in MAIN_CODE for t in
                    ["input.jump2", "hop === 2", "hop===2", "airMax = 0.74",
                     "Amazing", "0.9倍"])
    single = "player.hop = 1" in RACE and "player.airMax = 0.5" in RACE and "player.air = 0.5" in RACE
    chk("PN-JUMP-00 唯一 P0 单跳必过（≥1000 seed 可复现 / 二段跳非前提）",
        jump["pass"] and no_double and single,
        {"seeds": jump["seeds"], "cleared": jump["cleared"], "hit": jump["hit"],
         "notTaken": jump["notTaken"], "maxRockHits(单跳场景)": jump["maxHits"],
         "二段跳实现零命中(剥离注释)": no_double, "单级airMax=0.5": single})

    # PN-JUMP-01：首击立即起跳 / 无原生 dblclick 延迟（非二段跳要求）
    nodbl = not re.search(r"dblclick|e\.detail\s*===\s*2", MAIN_CODE)
    chk("PN-JUMP-01 首击立即起跳（air 即时置位）/ 无原生 dblclick 探测",
        nodbl and "player.air = 0.5" in RACE,
        {"dblclick零命中": nodbl, "口径": "仅指原生 dblclick 探测，非二段跳要求"})

    # PN-JUMP-03：删 dashLeft/hopWindow/jumpCd 后 odo 只按 base*mul*dt 单调推进
    dead = all(t not in RACE_CODE for t in ["dashLeft", "hopWindow", "jumpCd", "input.jump2"])
    chk("PN-JUMP-03 删 dashLeft/hopWindow/jumpCd 后 odo 只按 base*mul*dt 单调、零额外推进",
        dead and "kart.odo += base * mul * dt" in RACE,
        {"死字段实现零命中(剥离注释)": dead, "护栏例外": "blockSplitter 合法回滚由产品逻辑自身承接"})

    # PN-ROCK-04：撞石 ≤2 整数硬上限
    cap_static = ("ROCK_HITS_MAX = 2" in CONFIG
                  and "rockBudget: ROCK_HITS_MAX" in RACE
                  and "if (state.rockHits >= state.rockBudget) return;" in RACE)
    chk("PN-ROCK-04 撞石 ≤2 整数硬上限（跨圈累计 / 不复位）",
        cap_static and races["maxRockHits"] <= 2 and races["rockBudget"] == 2,
        {"maxRockHits(整局实跑)": races["maxRockHits"], "rockBudget": races["rockBudget"],
         "ROCK_HITS_MAX": races["constants"]["ROCK_HITS_MAX"]})

    # PN-ROCK-05a：state.pickups 中 rock 条目配额 ≤2（非整局出现次数，跨圈重现不判 FAIL）
    quota = ("ROCK_QUOTA = 2" in CONFIG
             and "for (let i = 0; i < ROCK_QUOTA; i++)" in RACE
             and "state.pickups = buildField();" in RACE)
    chk("PN-ROCK-05a state.pickups 中 rock 条目配额 ≤2（跨圈重现为既定语义、不判 FAIL）",
        quota and len(races["rockItemsSet"]) == 1 and races["rockItemsSet"][0] <= 2,
        {"rock条目集合": races["rockItemsSet"], "ROCK_QUOTA": races["constants"]["ROCK_QUOTA"],
         "口径": "条目配额 ≤2，不是整局出现 / 交互次数 ≤2"})

    # PN-ROCK-05b：碰撞计数封顶（达 2 后不再 openQuiz(rock) / 不再计 quizReasons.rock）
    cap_logic = ("if (state.rockHits >= state.rockBudget) return;" in RACE
                 and 'openQuiz("rock")' in RACE
                 and "state.rockHits += 1" in RACE)
    rockquiz_ok = races["quizRockTotal"] <= 2 * races["count"]
    chk("PN-ROCK-05b 碰撞计数封顶（达 2 后静默越过、不再 openQuiz(rock) / 不计 quizReasons.rock）",
        cap_logic and rockquiz_ok and races["maxRockHits"] <= 2,
        {"quizRockTotal": races["quizRockTotal"], "maxRockHits": races["maxRockHits"],
         "封顶静态逻辑": cap_logic})

    # PN-ROCK-06：改动前超标留痕 FAIL 原样保留、禁止改绿（当前新代码作修复后对照）
    hist = ("PN-ROCK-06" in QA and "0 / 5 / 3 / 6" in QA and "全部 > 2" in QA
            and "不悄悄改绿" in QA and "rock=7/4" in REMAP and "0/5/3/6" in REMAP
            and "PN-ROCK-06" in IMPL)
    chk("PN-ROCK-06 改动前超标留痕 FAIL 原样保留（禁止改绿；当前 rockHits<=2 为修复后对照）",
        hist and races["maxRockHits"] <= 2,
        {"历史证据(qa/impl/remap)完好": hist, "当前maxRockHits": races["maxRockHits"],
         "口径": "验证历史 FAIL 证据未被改绿，不是把旧 FAIL 判成 PASS"})

    # PN-ROCK-01/02/03：提前可见 / 存在跳跃窗 / 无「生成即碰撞」
    vis = ("ROCK_HIT_BAND = 78" in CONFIG
           and "pickups" in MODEL
           and "PICKUP_KEYS" in MODEL
           and "const d = player.odo - odo;" in RACE
           and "Math.abs(d) <= ROCK_HIT_BAND" in RACE)
    chk("PN-ROCK-01/02/03 石头提前可见 / 存在可跳窗 / 无生成即碰撞（|Δodo|>78 才定案）",
        vis and races["constants"]["ROCK_HIT_BAND"] == 78,
        {"ROCK_HIT_BAND": races["constants"]["ROCK_HIT_BAND"],
         "只读pickups投影": "PICKUP_KEYS" in MODEL})

    # PN-NPC-01：速度下限 0.94·v_player_now 不得放宽
    floor_static = ("NPC_MIN_SPEED_RATIO = 0.94" in CONFIG
                    and "const floor = NPC_MIN_SPEED_RATIO * (speedNow(player) / diff.speed);" in RACE
                    and "if (mul < floor) mul = floor;" in RACE)
    chk("PN-NPC-01 rival 速度下限 0.94·v_player_now 不得放宽（0.9× 作废）",
        floor_static and races["floorViolations"] == 0 and races["floorSamples"] > 0,
        {"同源floor不等式违反帧": races["floorViolations"],
         "floor采样帧": races["floorSamples"],
         "最小余量(dR-0.94·v_player_now·dt)": round(races["minFloorMargin"], 9),
         "minRivalRatio(诊断,Δodo比值)": round(races["minRivalRatio"], 6),
         "低于0.94的Δodo帧占比(诊断)": "%d/%d" % (races["belowCount"], races["sampleCount"]),
         "NPC_MIN_SPEED_RATIO": races["constants"]["NPC_MIN_SPEED_RATIO"], "阈值": 0.94,
         "口径": "主判据=逐帧同源 floor 不等式 v_i>=0.94·v_player_now（race.js:315-316 原式，零排除帧、阈值0.94不变）；"
                 "Δodo 瞬时比值 0.68 系判门 reveal→hold 帧 player.boost/turbo 清零发生在 updateKart(player) 之后、"
                 "rival 之前，致 dP 含 boost 而 floor 不含，属合法瞬态、非下限放宽，故改以同源 floor 不等式为判据"})

    # PN-SPEED-04：VISUAL_FLOW_GAIN 零进判定四文件 + DIFFICULTY.speed 260/300 逐字不动
    judge4 = {"race.js": RACE, "track.js": TRACK, "config.js": CONFIG, "headless_laps.mjs": HEADLESS}
    zero = all("VISUAL_FLOW_GAIN" not in t for t in judge4.values())
    speed_ok = "speed: 260" in CONFIG and "speed: 300" in CONFIG
    chk("PN-SPEED-04 VISUAL_FLOW_GAIN 零进判定四文件且 DIFFICULTY.speed 260/300 逐字不动",
        zero and speed_ok,
        {"判定四文件零命中": zero, "逐文件": {k: ("VISUAL_FLOW_GAIN" in v) for k, v in judge4.items()},
         "speed260/300": speed_ok})

    # PN-SPEED-05：VISUAL_FLOW_GAIN 只作用渲染层（两个落点都要覆盖）
    m_exp = re.search(r"export const VISUAL_FLOW_GAIN\s*=\s*([\d.]+)", MODEL)
    r_const = re.search(r"const VISUAL_FLOW_GAIN\s*=\s*([\d.]+)", RENDER)
    two_sites = bool(m_exp) and bool(r_const) and m_exp.group(1) == r_const.group(1) == "1.6"
    linephase = "lineDashOffset" in RENDER and RENDER.count("VISUAL_FLOW_GAIN") >= 2
    no_write = not re.search(r"(odo|lateral|g\.line|diff\.speed)\s*=.*VISUAL_FLOW_GAIN", MODEL + RENDER)
    chk("PN-SPEED-05 VISUAL_FLOW_GAIN 只作用渲染层（scene3d-model.mjs:34 export + render.js:8 const 双落点）",
        two_sites and linephase and no_write,
        {"落点1(scene3d-model.mjs export)": m_exp.group(1) if m_exp else None,
         "落点2(render.js const)": r_const.group(1) if r_const else None,
         "仅lineDashOffset相位": linephase, "零写回判定域": no_write})

    # PN-SPEED-06：forkSpan 依赖登记（speed 260/300 未变则窗口维持）
    chk("PN-SPEED-06 forkSpan = fork*speed/L 依赖登记（260/300 未变则窗口维持）",
        "return (diff.fork * diff.speed) / length;" in CONFIG,
        {"公式": "diff.fork * diff.speed / length"})

    # PN-FORK-01/02：石头生成按 g.line 绝对里程排除分叉窗口（里程互斥）
    fork = ("line0 - span * L - ROCK_MARGIN" in RACE
            and "line0 = g.line - (g.lap || 0) * L" in RACE
            and "ROCK_MARGIN = 60" in CONFIG)
    chk("PN-FORK-01/02 石头按 g.line 绝对里程排除分叉窗口（贴地起跳标线与选道态互斥）",
        fork, {"ROCK_MARGIN": 60, "口径": "blocked() 按绝对里程折叠回第一圈基准"})

    # PN-QUIZ-03：词表 Good/Excellent/Marvellous 逐字锁定（无 Amazing / 不要求随机三选一）
    wm = re.search(r"const words\s*=\s*\[([^\]]+)\]", RACE)
    words = [x.strip().strip('"\'') for x in wm.group(1).split(",")] if wm else []
    chk("PN-QUIZ-03 词表 Good/Excellent/Marvellous 逐字锁定（Amazing / 随机三选一 / 连击偏向词作废）",
        words == ["Good", "Excellent", "Marvellous"] and "Amazing" not in RACE_CODE,
        {"词表": words, "Amazing零命中": "Amazing" not in RACE_CODE})

    # PN-QUIZ-05：两类触发源共用 c.seq 全局序号去重（同词连播仍重播）
    seq = ("state.cheerSeq += 1" in RACE and "seq: state.cheerSeq" in RACE
           and "cheerShown !== seq" in MAIN and "cheerShown = seq" in MAIN
           and "cheer(1)" in RACE)
    chk("PN-QUIZ-05 判门/跳石两类触发源共用 c.seq 全局序号去重（同词连播仍重播）",
        seq, {"去重键": "cheerShown !== c.seq（非按词内容）"})

    # PN-QUIZ-04：quizReasons.wall === 0（整局零撞墙题）
    chk("PN-QUIZ-04 quizReasons.wall === 0（整局零撞墙题）",
        races["wallTotal"] == 0 and "quizReasons.wall" in HEADLESS,
        {"wallTotal(整局实跑)": races["wallTotal"], "场数": races["count"]})

    # PN-SPEED-01：headless_laps.mjs 原路径原命令 11 场 ALL PASS 且 max<=180s（如实报新值）
    r = subprocess.run([NODE, "js/headless_laps.mjs"], cwd=HERE, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", timeout=300)
    hl = (r.stdout or "") + (r.stderr or "")
    times = [float(x) for x in re.findall(
        r"^\s*(?:follow|listen)\s+\S+\s+\S+\s+YES\s+([\d.]+)", hl, re.M)]
    chk("PN-SPEED-01 node js/headless_laps.mjs 11 场 ALL PASS 且 max(finishTime)<=180s",
        r.returncode == 0 and "ALL PASS" in hl and len(times) == 11 and max(times) <= 180.0,
        {"exit": r.returncode, "场数": len(times),
         "min": min(times) if times else None, "max": max(times) if times else None,
         "重放场景maxFinishTime": races["maxFinishTime"]})

    # PN-GUARD-01/02：PLR-CSEG-S2/A6 的 speed 260/300 期望值维持原值 + 双锚定重锚就位
    guard = ('"speed: 260"' in CSEG and '"speed: 300"' in CSEG
             and "speed: 260" in CONFIG and "speed: 300" in CONFIG)
    snap_ok = (os.path.isfile(os.path.join(ROOT, ".workbuddy", "backups", "fwd-tag-20261120", "file-hashes.json"))
               and os.path.isfile(os.path.join(ROOT, ".workbuddy", "backups", "fwd-tag-20261120", "manifest.txt")))
    chk("PN-GUARD-01/02 PLR-CSEG-S2/A6 speed 260/300 维持原值 + fwd-tag-20261120 双快照重锚就位",
        guard and snap_ok,
        {"S2/A6期望值不变": guard, "新快照双文件": snap_ok})

    _finish()
    return


def _finish():
    NOT_COVERED.extend([
        "NPC「像真人驾车」主观观感（不龟速/不扎堆的体感）— 人工签收，不冒充 PASS",
        "分叉「真实可见」五阶段可读性 / 贴地起跳标线可预期性 — 人工签收",
        "石头可见性（3D 屏占比 / 提前可见观感）、L2 与 L1 一眼可分 — 人工签收",
        "欢呼 Good/Excellent/Marvellous 文案 + 局部小彩带 / 同词连播观感 — 人工签收",
        "单跳手感触屏实机（首击无延迟 / 单跳必过体感）— 人工签收",
    ])
    print("\n-- S7 NOT_COVERED（人工过眼，不进 PASS 计数）--")
    for x in NOT_COVERED:
        print("  NOT_COVERED  " + x)
    p = sum(1 for _, ok, _ in RESULTS if ok)
    f = len(RESULTS) - p
    print("\n" + "=" * 78)
    print("S7 PN-* SUMMARY: %d PASS / %d FAIL / %d TOTAL" % (p, f, len(RESULTS)))
    if f:
        for n, ok, d in RESULTS:
            if not ok:
                print("  FAILED:", n, "|", d)
    print("=" * 78)
    out = {
        "suite": "S7 / verify_p1_interaction.py",
        "summary": {"PASS": p, "FAIL": f, "TOTAL": len(RESULTS)},
        "results": [{"name": n, "ok": ok, "detail": str(d)} for n, ok, d in RESULTS],
        "not_covered": NOT_COVERED,
    }
    with open(os.path.join(LOGDIR, "S7.log"), "w", encoding="utf-8") as fp:
        json.dump(out, fp, ensure_ascii=False, indent=2)
    print("S7_LOG -> " + os.path.join(LOGDIR, "S7.log"))
    sys.exit(1 if f else 0)


if __name__ == "__main__":
    main()
