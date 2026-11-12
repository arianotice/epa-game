/* C 段多圈实跑验证（Node，无浏览器）。
   直接 import 真实模块、按固定 dt 步进跑完整场，输出 finishTime / 门判定 / 跨圈复位。
   用法：node headless_laps.mjs
   注意：race.js 依赖 localStorage 与 audio，这里用最小 mock；仿真时钟只在
   race.update() 里累加，与浏览器 frame() 的冻结行为一致。 */

/* 最小 localStorage mock，让 loadWallet / applyWalletDelta 走真实分支。 */
const mem = new Map();
globalThis.localStorage = {
  getItem: (k) => (mem.has(k) ? mem.get(k) : null),
  setItem: (k, v) => mem.set(k, String(v)),
  removeItem: (k) => mem.delete(k),
};
mem.set("ipa-quest-v1", JSON.stringify({ rally: { gems: 0, shields: 3 } }));

/* audio 是纯副作用对象，全部空实现即可。 */
const audio = new Proxy({}, { get: (_t, k) => (k === "then" ? undefined : () => {}) });

const TAG = "hud-20261108";
const { TUNING, DIFFICULTY, buildGates, RACE_MAPS, PAIRS_BY_MAP, allWords, QUIZ_TYPES } =
  await import(`./config.js?v=${TAG}`);
const { createTrack } = await import(`./track.js?v=${TAG}`);
const { createRace } = await import(`./race.js?v=${TAG}`);

const L = createTrack(TUNING).length;
const DT = 1 / 60;
const MAX_STEPS = 60 * 400; // 400s 保护上限

/* 让 Math.random 可复现，方便对比工况。 */
function seeded(seed) {
  let s = seed >>> 0;
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; };
}

function run({ diffId = "follow", mapId = "camp", worst = false, seed = 7, forceCollide = false } = {}) {
  const rand = seeded(seed);
  const realRandom = Math.random;
  Math.random = rand;
  try {
    const track = createTrack(TUNING);
    const diff = DIFFICULTY[diffId];
    const gates = buildGates(mapId, rand);
    const race = createRace({ track, diff, gates, audio, mapId });
    const st = race.state;

    let steps = 0, lapChanges = 0, lastLap = 0;
    let quizAuto = 0, quizWrongAuto = 0, collisions = 0;
    const quizReasons = {};
    while (!st.finished && steps < MAX_STEPS) {
      /* A4 规格要求「至少 2 次碰撞」：把对手挪到玩家身边，走真实的
         resolveContacts() 路径触发 shoveRival + SLOW + bumpCd=8s 冷却，
         不直接改 speed / slow，保证是产品代码在起作用。 */
      if (forceCollide && steps % 600 === 300 && st.player.bumpCd <= 0) {
        const r = st.rivals[0];
        r.odo = st.player.odo - 40;
        r.t = (r.odo / L) % 1;
        r.lateral = st.player.lateral;
        r.laneTarget = r.lateral;
        collisions++;
      }
      const act = race.activeGate();
      let input = {};
      /* 真实玩家在「听到词 → 判定」期间按住选边，把车收敛到目标车道
         (±laneLateral)；判定后松手让车稳定在该车道。绝不能一路按到底，
         否则 lateral 冲到 ±1 会持续撞墙，凭空刷出几十道额外惩罚题。
         answering() 与 race.js 内部同源：gates.some(g => g.played && !g.judged)。 */
      const answering = st.gates.some((g) => g.played && !g.judged);
      if (act && answering) {
        const target = (worst ? -1 : 1) * act.gate.correctLateral;
        const lat = st.player.lateral;
        if (lat < target - 0.04) input = { right: true };
        else if (lat > target + 0.04) input = { left: true };
      }
      race.update(DT, input);
      /* 浏览器里 mode==="quiz" 会冻结仿真，答题不占 state.time；
         这里立即结算（最坏工况故意答错以触发 SLOW 1.4s），等价近似。 */
      if (st.quiz) {
        quizAuto++;
        const r = st.quiz.reason || "?";
        quizReasons[r] = (quizReasons[r] || 0) + 1;
        if (worst) { race.finishQuiz("__wrong__"); quizWrongAuto++; }
        else race.finishQuiz(st.quiz.spoken.word);
      }
      if (st.lap !== lastLap) { lapChanges++; lastLap = st.lap; }
      steps++;
    }
    const res = race.result();
    return {
      diffId, mapId, worst,
      finished: st.finished,
      finishTime: +st.finishTime.toFixed(2),
      time: +st.time.toFixed(2),
      traveled: +(st.player.odo - st.player.startOdo).toFixed(1),
      need: +(st.laps * L).toFixed(1),
      lapChanges,
      judged: gates.filter((g) => g.judged).length,
      unheard: gates.filter((g) => g.unheard).length,
      gateHits: st.gateHits,
      total: res.total,
      quizAuto, quizWrongAuto, collisions,
      pickupsReset: st.pickups.some((p) => !p.taken),
      resultTime: +res.time.toFixed(2),
      quizReasons,
      steps,
    };
  } finally {
    Math.random = realRandom;
  }
}

const results = [];
for (const diffId of Object.keys(DIFFICULTY)) {
  for (const m of RACE_MAPS) {
    results.push(run({ diffId, mapId: m.id }));
  }
}
/* 最坏工况：连续答错 + 额外题全答错（触发 SLOW 1.4s）+ 强制 2 次碰撞。 */
results.push(run({ diffId: "follow", mapId: "camp", worst: true, seed: 11, forceCollide: true }));
results.push(run({ diffId: "follow", mapId: "peak", worst: true, seed: 23, forceCollide: true }));
results.push(run({ diffId: "listen", mapId: "kingdom", worst: true, seed: 31, forceCollide: true }));

const pad = (s, n) => String(s).padEnd(n);
console.log("track.length =", L.toFixed(2), "| laps =", TUNING.laps,
  "| need =", (TUNING.laps * L).toFixed(1), "| DT =", DT.toFixed(4));
console.log(pad("档位", 8), pad("地图", 9), pad("工况", 7), pad("完赛", 6),
  pad("用时s", 8), pad("判门", 6), pad("未听", 6), pad("跨圈", 6), pad("result.time", 12));
for (const r of results) {
  console.log(pad(r.diffId, 8), pad(r.mapId, 9), pad(r.worst ? "worst" : "normal", 7),
    pad(r.finished ? "YES" : "NO", 6), pad(r.finishTime, 8),
    pad(`${r.judged}/${r.total}`, 6), pad(r.unheard, 6), pad(r.lapChanges, 6),
    pad(r.resultTime, 12), "额外题", r.quizAuto, JSON.stringify(r.quizReasons));
}

const fails = [];
for (const r of results) {
  if (!r.finished) fails.push(`${r.diffId}/${r.mapId}/${r.worst} 未完赛`);
  if (r.finishTime > 180) fails.push(`${r.diffId}/${r.mapId}/${r.worst} finishTime=${r.finishTime}>180`);
  if (r.judged !== r.total) fails.push(`${r.diffId}/${r.mapId}/${r.worst} 判门 ${r.judged}/${r.total}`);
  if (r.lapChanges !== TUNING.laps - 1) fails.push(`${r.diffId}/${r.mapId}/${r.worst} 跨圈次数 ${r.lapChanges}`);
  if (r.resultTime !== r.finishTime) fails.push(`${r.diffId}/${r.mapId}/${r.worst} result.time 不同源`);
  if (Math.abs(r.traveled - r.need) > 1) fails.push(`${r.diffId}/${r.mapId}/${r.worst} 里程 ${r.traveled}/${r.need}`);
  if (r.worst && r.quizAuto === 0) fails.push(`${r.diffId}/${r.mapId} 最坏工况未触发额外题（不构成惩罚）`);
  if (r.quizReasons.wall) fails.push(`${r.diffId}/${r.mapId}/${r.worst} 出现撞墙题（驾驶模型失真）`);
}
/* A4：至少一场最坏工况命中 >= 2 次真实碰撞。 */
const maxCollide = Math.max(...results.map((r) => r.collisions));
console.log("强制碰撞注入最大命中次数:", maxCollide);
if (maxCollide < 2) fails.push(`A4 最坏工况碰撞命中 ${maxCollide} < 2`);
console.log("\n=== 断言 ===");
console.log(fails.length ? "FAIL:\n - " + fails.join("\n - ") : "ALL PASS");
console.log("题库: 地图", Object.keys(PAIRS_BY_MAP).length,
  "词对", Object.values(PAIRS_BY_MAP).reduce((n, p) => n + p.length, 0),
  "词", allWords().length, "题型", QUIZ_TYPES.length);
process.exit(fails.length ? 1 : 0);
