import { DIFFICULTY, KART_TYPE, TUNING, VOWELS, PHONEMES, RACE_MAPS, CHARACTERS, QUIZ_TITLES, allWords, buildGates, poolOf, scoreRace, ROCK_HIT_BAND } from "./config.js?v=fwd-20261121";
import { createTrack } from "./track.js?v=fwd-20261121";
import { createAudio } from "./audio.js?v=fwd-20261121";
import { createRace } from "./race.js?v=fwd-20261121";
import { CARDS } from "./cards.js?v=fwd-20261121";
import { project, render, minimapModel } from "./render.js?v=fwd-20261121";

/* FIX-C03：面向用户的大字一律取美式 displayIpa（按稳定 unit id 查表），表缺项回退英式 sym。 */
const IPA = (card) => (window.IPA_DISPLAY && window.IPA_DISPLAY[card.id] && window.IPA_DISPLAY[card.id].displayIpa) || card.sym;

const KEY = "ipa-quest-v1";
const canvas = document.querySelector("#c");
const ctx = canvas.getContext("2d");
const audio = createAudio();
const track = createTrack(TUNING);
const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const ui = {
  hud: document.querySelector("#hud"),
  place: document.querySelector("#place"),
  gates: document.querySelector("#gates"),
  combo: document.querySelector("#combo"),
  tags: document.querySelector("#tags"),
  board: document.querySelector("#board"),
  kartType: document.querySelector("#kart-type"),
  progress: document.querySelector("#progress > span"),
  /* FWD M3：HUD 影子三角 + Δt 文案（纯刻度，非第 4 辆车，不进 3D 白名单）。 */
  ghost: document.querySelector("#ghost-mark"),
  ghostLabel: document.querySelector("#ghost-label"),
  banner: document.querySelector("#banner"),
  verdict: document.querySelector("#verdict"),
  fork: document.querySelector("#fork-card"),
  forkLeft: document.querySelector("#fork-left"),
  forkRight: document.querySelector("#fork-right"),
  forkCount: document.querySelector("#fork-count"),
  cheer: document.querySelector("#cheer"),
  cheerWord: document.querySelector("#cheer-word"),
  confetti: document.querySelector("#confetti"),
  nitroBar: document.querySelector("#nitro-bar"),
  quiz: document.querySelector("#quiz"),
  quizWhy: document.querySelector("#quiz-why"),
  quizTitle: document.querySelector("#quiz-title"),
  quizPrompt: document.querySelector("#quiz-prompt"),
  quizOptions: document.querySelector("#quiz-options"),
  quizResult: document.querySelector("#quiz-result"),
  quizReplay: document.querySelector("#quiz-replay"),
  boardPanel: document.querySelector("#board-panel"),
  boardBody: document.querySelector("#board-body"),
  gems: document.querySelector("#gems"),
  shields: document.querySelector("#shields"),
  shop: document.querySelector("#shop-panel"),
  shopGems: document.querySelector("#shop-gems"),
  shopList: document.querySelector("#shop-list"),
  touch: document.querySelector("#touch"),
  left: document.querySelector("#steer-left"),
  right: document.querySelector("#steer-right"),
  mid: document.querySelector("#replay"),
  jump: document.querySelector("#jump"),
  mute: document.querySelector("#btn-mute"),
  pause: document.querySelector("#btn-pause"),
  title: document.querySelector("#panel-title"),
  routeMap: document.querySelector("#route-map"),
  how: document.querySelector("#how"),
  teach: document.querySelector("#panel-teach"),
  teachFocus: document.querySelector("#teach-focus"),
  mapPick: document.querySelector("#map-pick"),
  charPick: document.querySelector("#char-pick"),
  count: document.querySelector("#panel-count"),
  countNum: document.querySelector("#count-num"),
  countHint: document.querySelector("#count-hint"),
  pausePanel: document.querySelector("#panel-pause"),
  results: document.querySelector("#panel-results"),
  best: document.querySelector("#best"),
  signs: document.querySelector("#signs"),
  signL: document.querySelector("#sign-l"),
  signR: document.querySelector("#sign-r"),
  live: document.querySelector("#live"),
  minimap: document.querySelector("#minimap"),
  minimapC: document.querySelector("#minimap-c"),
  minimapLap: document.querySelector("#minimap-lap"),
};

// A5：pointer.jump 仅记录触屏按住态；真正的一次跳跃与键盘 Space 共用 jumpEdge。
const pointer = { left: false, right: false, rocket: false, jump: false };
const keys = new Set();
let replayEdge = false;
let jumpEdge = false;
/* IMPL-1B B2：半屏点选转向（触屏优先，与键盘 ArrowLeft/ArrowRight + A/D 并存）。
   window 级 pointerdown 事件委托，不新增物理全屏层、不打乱 z 栈；HIT_EXCLUDE 覆盖
   全部交互层，故点 #jump（位于 #touch 内）不会被半屏逻辑吞掉，jumpEdge 仍由既有
   ui.jump 监听独立触发。本批只做单跳必过：零 260ms 状态机 / 零 jump2 / 零双击效果。 */
let tapSteer = "";
let mode = "title";
let diff = DIFFICULTY.listen;
let race = null;
/* C 段：当前杯赛地图 / 车手。偏好存进共享 rally，跨站由 store.js 白名单保留。 */
let mapId = RACE_MAPS[0].id;
let characterId = CHARACTERS[0].id;
let resultOpen = false;
let boardOpen = false;
let shopOpen = false;
let confettiBits = [];
/* IMPL-1B B1：按 cheer.seq 去重（同词连续触发须重播），初值 -1 表示「未展示」。 */
let cheerShown = -1;
/* 任务2：verdict 按 seq 去重重播（同词连续判定也要弹），初值 -1 表示「未展示」。 */
let verdictShown = -1;
let count = 0;
let lastBeep = 99;
let signKey = "";
let signPhase = "S0";        // CSEG-E1：路牌 S0–S3 当前相位（供 minimapModel / #5 只读断言）
let lastSignState = null;    // CSEG-E1：上一帧 computeSignState() 快照（冻结态沿用，保证「显示但冻结」）
let lastMmModel = null;      // CSEG-E1：最近一帧 minimapModel(view) 快照（window.__rally.minimapModel() 只读）
let mmCtx = null;            // CSEG-E1：内嵌 #minimap-c 的 2d context（惰性取得）
let mmRect = null;           // CSEG-E1：最近一帧 #minimap 的 rect（placeLaneSign 避让裁剪用）
let w = 1;
let h = 1;
let dpr = 1;
const camera = { x: 0, y: 0, h: 0 };
const demo = [
  { t: 0.04, lateral: 0, kind: "player", id: "p", boost: 0, turbo: 0 },
  { t: 0.046, lateral: 0.42, kind: "rival", id: "a", boost: 0, turbo: 0 },
  { t: 0.034, lateral: -0.42, kind: "rival", id: "b", boost: 0, turbo: 0 },
];

const PAINTS = [
  { id: "paint-base", tier: "基础款", cost: 50, body: "#3d8eb8", shine: 0 },
  { id: "paint-plus", tier: "进阶款", cost: 100, body: "#7ad7ff", shine: 1 },
  { id: "paint-rare", tier: "稀有款", cost: 200, body: "#e8fbff", shine: 2 },
];
const TRIMS = [
  { id: "trim-base", tier: "基础款", cost: 50, trim: "#e0b44a", shine: 0 },
  { id: "trim-plus", tier: "进阶款", cost: 100, trim: "#ffe27a", shine: 1 },
  { id: "trim-rare", tier: "稀有款", cost: 200, trim: "#fff6c2", shine: 2 },
];
const SHIELD_COST = 80;

function readPack() {
  const data = readStore();
  const rally = data.rally && typeof data.rally === "object" ? data.rally : {};
  return {
    gems: rally.gems || 0,
    shields: rally.shields || 0,
    paint: rally.paint || "",
    trim: rally.trim || "",
    ownedPaints: Array.isArray(rally.ownedPaints) ? rally.ownedPaints : [],
    ownedTrims: Array.isArray(rally.ownedTrims) ? rally.ownedTrims : [],
    /* FIX-C03：音标卡唯一解锁来源 = 赛事地图 rally.unlocked（按 unit id）。
       collected / stars 两条旧解锁口径彻底退役，不再读取、不保留任何 fallback。 */
    unlocked: Array.isArray(rally.unlocked) ? rally.unlocked : [],
    maps: rally.maps && typeof rally.maps === "object" ? rally.maps : {},
    lastMap: rally.lastMap || "",
    lastChar: rally.lastChar || "",
  };
}

/* ---------- C 段：四区杯赛地图 / 车手选择 ----------------------------------
 * 音标卡唯一解锁来源 = 赛事地图完赛答对的门（见 openResults），宝石不可兑换。
 * 选择偏好写入 rally.lastMap / lastChar，走 commit 避免跨站全量覆写。
 * --------------------------------------------------------------------------- */
function currentMap() {
  return RACE_MAPS.find((m) => m.id === mapId) || RACE_MAPS[0];
}
function currentChar() {
  return CHARACTERS.find((c) => c.id === characterId) || CHARACTERS[0];
}
function renderPickers() {
  const pack = readPack();
  if (RACE_MAPS.some((m) => m.id === pack.lastMap)) mapId = pack.lastMap;
  if (CHARACTERS.some((c) => c.id === pack.lastChar)) characterId = pack.lastChar;
  ui.mapPick.innerHTML = RACE_MAPS.map((m) => {
    const done = pack.maps[m.id] && pack.maps[m.id].wins > 0;
    return `<button type="button" class="seg-btn" data-map="${m.id}" aria-pressed="${m.id === mapId}">${done ? "✓ " : ""}${m.name}<small>${m.zone} · ${m.short}</small></button>`;
  }).join("");
  ui.charPick.innerHTML = CHARACTERS.map((c) =>
    `<button type="button" class="seg-btn" data-char="${c.id}" aria-pressed="${c.id === characterId}">${c.name}<small>${c.blurb}</small></button>`
  ).join("");
  ui.mapPick.querySelectorAll("[data-map]").forEach((btn) => {
    btn.onclick = () => {
      mapId = btn.dataset.map;
      commit((d) => { d.rally.lastMap = mapId; });
      audio.unlock(); audio.click();
      renderPickers();
    };
  });
  ui.charPick.querySelectorAll("[data-char]").forEach((btn) => {
    btn.onclick = () => {
      characterId = btn.dataset.char;
      commit((d) => { d.rally.lastChar = characterId; });
      audio.unlock(); audio.click();
      renderPickers();
    };
  });
}
function patchRally(mut) {
  /* FIX-C08：走 commit，让商店扣款 / 购买基于「写入瞬间最新整对象」的相对变更，
     不再用内存快照全量覆写；同步 HUD 时改用 commit 返回的最新 rally 值。 */
  const d = commit((obj) => mut(obj.rally));
  if (race) {
    race.state.gems = d.rally.gems || 0;
    race.state.shields = d.rally.shields || 0;
  }
}
function playerLook() {
  const pack = readPack();
  const paint = PAINTS.find((item) => item.id === pack.paint);
  const trim = TRIMS.find((item) => item.id === pack.trim);
  return {
    body: paint ? paint.body : null,
    trim: trim ? trim.trim : null,
    bodyShine: paint ? paint.shine : 0,
    trimShine: trim ? trim.shine : 0,
  };
}
function readStore() {
  try { return JSON.parse(localStorage.getItem(KEY)) || {}; }
  catch (e) { return {}; }
}
function writeStore(data) {
  try { localStorage.setItem(KEY, JSON.stringify(data)); }
  catch (e) { /* 隐私模式可能拒绝写入 */ }
}

/* ---------- FIX-C08：跨站共享存档（单键 ipa-quest-v1）------------------------
 * 两站同源、共用单键；rally 是共享嵌套对象。旧写点各自 readStore→writeStore 全量覆写，
 * 与大闯关 store.js 的陈旧快照、race.js 的绝对值写回交错 → 覆盖 / 双花。
 * commit = 写入瞬间重读最新整对象 → 只应用本次最小变更 → 写回。
 *   mutator 只改自己字段，禁止删除 / 覆盖 collected / legacyCollected / stars /
 *   rally.schemaVersion / rally.unlocked（大闯关权威域）；这些字段随「最新整对象」原样保留。
 *   集合域 ownedPaints / ownedTrims 用 unionArr 兜底取并集，防止任何写点用旧快照整体替换丢项。
 *   gems / shields 一律 delta（+拾取 / -消费），禁绝对值覆盖、禁 max/min。
 *   EP02：stars/bestAcc 取 max、played 累加、lastPlace/diff 取最新（见 openResults）。
 *   howSeen：OR（true 优先）；sound / paint / trim / lastEp：单字段 LWW，以本次操作为准。
 * localStorage 无原子 CAS，本方案把竞态窗口压到 read→write 之间，不追求数学零竞态。
 * --------------------------------------------------------------------------- */
function unionArr(a, b) {
  const out = Array.isArray(a) ? a.slice() : [];
  (Array.isArray(b) ? b : []).forEach((x) => { if (x != null && !out.includes(x)) out.push(x); });
  return out;
}
function commit(mutator) {
  let d;
  try { d = JSON.parse(localStorage.getItem(KEY)); } catch (e) { d = {}; }
  if (!d || typeof d !== "object") d = {};
  if (!d.rally || typeof d.rally !== "object") d.rally = {};
  /* 写前快照：供 ownedPaints / ownedTrims 并集兜底。 */
  const beforePaints = Array.isArray(d.rally.ownedPaints) ? d.rally.ownedPaints.slice() : [];
  const beforeTrims = Array.isArray(d.rally.ownedTrims) ? d.rally.ownedTrims.slice() : [];
  mutator(d);
  const paints = unionArr(beforePaints, d.rally.ownedPaints);
  const trims = unionArr(beforeTrims, d.rally.ownedTrims);
  if (paints.length) d.rally.ownedPaints = paints;
  if (trims.length) d.rally.ownedTrims = trims;
  writeStore(d);
  return d;
}

/* ---------- FWD 度量域 rally.fwd + 机制辅助（全部在 frame() 之外）--------------
 * 1 容器 + 9 叶子字段；ring 为定长 12 位纯数字元组 FIFO（无词面 / IPA / 答案）。
 * X1 初始化 → X2 开局 → X3 再跑一场 → X4 完赛 → X5 离开；每局 ≤4 次 setItem。
 * frame() 与 __rally.step(n) 内零写入；window.__rally.fwd 是零写盘只读投影。 */
const M1_ON = new URLSearchParams(location.search).get("m1") === "on";
let fwd = null;          // 内存镜像（X1 建立）
let inRace = false;      // 在赛态：仅内存，不落盘
let shadowBest = 0;      // 当前地图 bestTime 缓存（秒），X1 / X4 更新
const fwdNum = (x) => (Number.isFinite(Number(x)) ? Number(x) : 0);
const isTuple12 = (t) => Array.isArray(t) && t.length === 12 && t.every((n) => Number.isFinite(n));

function fwdWrite(d, patch) {
  /* 写前整对象由 commit() 保证；这里只并列写 fwd 域，绝不碰 EP02/unlocked/maps。 */
  const prev = (d.rally.fwd && typeof d.rally.fwd === "object") ? d.rally.fwd : {};
  const next = {
    v: 1,
    sess: fwd ? fwd.sess : fwdNum(prev.sess) + 1,
    start: fwd ? fwd.start : Date.now(),
    last: fwd ? fwd.last : fwdNum(prev.last),
    starts: fwdNum(prev.starts),
    again: fwdNum(prev.again),
    quits: fwdNum(prev.quits),
    games: fwdNum(prev.games),
    ring: Array.isArray(prev.ring) ? prev.ring.filter(isTuple12).slice(-12) : [],
  };
  Object.assign(next, patch || {});
  next.v = 1;
  if (fwd) { next.sess = fwd.sess; next.start = fwd.start; }
  next.ring = (Array.isArray(next.ring) ? next.ring : []).filter(isTuple12).slice(-12);
  d.rally.fwd = next;
  fwd = Object.assign({}, next);   // 同步内存镜像（ring 元素为浅引用，X3 会先复制）
  return next;
}
function readMapBest() {
  const r = readStore().rally;
  const mp = r && r.maps && r.maps[mapId];
  return mp && Number(mp.bestTime) > 0 ? Number(mp.bestTime) : 0;
}
function fwdInit() {
  /* X1：模块初始化末尾调用；sess 本机自增，不是用户标识。 */
  const saved = readStore().rally;
  const prev = (saved && saved.fwd && typeof saved.fwd === "object") ? saved.fwd : {};
  const ring = Array.isArray(prev.ring) ? prev.ring.filter(isTuple12).slice(-12) : [];
  fwd = {
    v: 1, sess: fwdNum(prev.sess) + 1, start: Date.now(), last: fwdNum(prev.last),
    starts: fwdNum(prev.starts), again: fwdNum(prev.again), quits: fwdNum(prev.quits),
    games: fwdNum(prev.games), ring,
  };
  inRace = false;
  shadowBest = readMapBest();
  commit((d) => { fwdWrite(d, {}); });
}
function fwdStart() {
  /* X2：beginCountdown() 入口；starts+1 落盘，inRace 仅置内存。 */
  inRace = true;
  commit((d) => { fwdWrite(d, { starts: fwdNum((d.rally.fwd || {}).starts) + 1 }); });
}
function fwdAgain() {
  /* X3：#btn-again.onclick；again+1，并把最近一局 ring 末位 againFlag 回填 1。 */
  commit((d) => {
    const prev = d.rally.fwd || {};
    const ring = Array.isArray(prev.ring) ? prev.ring.map((t) => (Array.isArray(t) ? t.slice() : t)) : [];
    if (ring.length && isTuple12(ring[ring.length - 1])) ring[ring.length - 1][11] = 1;
    fwdWrite(d, { again: fwdNum(prev.again) + 1, ring });
  });
}
function fwdTuple(raw) {
  /* 12 位定长数字元组：sess / n / acc100 / place / 用时×10 / judged /
     replays / quizTotal / quizCorrect / rockHits / cheerSeq / againFlag。 */
  const gates = race ? race.state.gates : [];
  return [
    fwd ? fwd.sess : 0,
    fwd ? fwdNum(fwd.games) + 1 : 1,
    raw.total ? Math.round((fwdNum(raw.correct) / raw.total) * 100) : 0,
    fwdNum(raw.place),
    Math.round(fwdNum(raw.time) * 10),
    gates.filter((g) => g.judged).length,
    gates.filter((g) => g.replayed).length,
    fwdNum(raw.quizTotal),
    fwdNum(raw.quizCorrect),
    race ? fwdNum(race.state.rockHits) : 0,
    race ? fwdNum(race.state.cheerSeq) : 0,
    0,
  ];
}
function fwdQuit() {
  /* X5：统一出口；inRace 守卫保证从标题开商店 / 结果页回标题不误计 quits。 */
  const now = Date.now();
  if (inRace) {
    commit((d) => { fwdWrite(d, { quits: fwdNum((d.rally.fwd || {}).quits) + 1, last: now }); });
    inRace = false;
  } else {
    commit((d) => { fwdWrite(d, { last: now }); });
  }
}

/* M1：近失缺口——每局结果页恒 1 条；只读取已有存档 + result()，零新 schema。 */
function nearMissFor(raw, saved) {
  const mp = saved && saved.maps && saved.maps[mapId] ? saved.maps[mapId] : null;
  const bestTime = mp && Number(mp.bestTime) > 0 ? Number(mp.bestTime) : 0;
  const hits = (raw.hits || []).length;
  const total = raw.total || 4;
  const dQ = Math.ceil(0.8 * total) - hits;
  const dPlace = fwdNum(raw.place) - 1;
  const dt = bestTime ? fwdNum(raw.time) - bestTime : null;
  let line = "", goal = "";
  if (!bestTime) {
    line = "第一局已建档，下一局开始追自己";
    goal = "定个目标";
  } else if (raw.place === 3) {
    line = "第 3 名 · 先把车开回前二";           // 败局不假希望「差一题就三星」
    goal = "追回一个名次";
  } else if (dQ === 1) {
    const w = raw.misses && raw.misses[0] && raw.misses[0].spoken && raw.misses[0].spoken.word;
    line = w
      ? `就差 <button type="button" data-word="${w}">▶ ${w}</button> 这一个词，三星就到手`
      : "就差一道题，三星就到手";
    goal = w ? `把 ${w} 开对` : "再答对一题";
  } else if (dPlace === 1) {
    line = "第 2 名，离第 1 名只差一个车身";
    goal = "抢回第 1 名";
  } else if (dQ === 2) {
    line = "再答对两道题，这局的星星就多一颗";
    goal = "多答对两题";
  } else if (dt !== null && Math.abs(dt) <= 3.0) {
    line = dt >= 0 ? `比自己最好慢 ${dt.toFixed(1)} 秒` : `比自己最好快 ${(-dt).toFixed(1)} 秒，稳住`;
    goal = dt > 0 ? `追回 ${dt.toFixed(1)} 秒` : "守住这个节奏";
  } else {
    line = "这局稳住了节奏，下一局接着追自己最好成绩";
    goal = "刷新自己的最好成绩";
  }
  return { line, goal, bestTime, dt };
}

/* M3：成绩卡 R-<base36>，12 位混合基数打包（≤12 字符）；纯本地、零后端。 */
const CARD_BITS = [2, 2, 7, 11, 3, 4, 4, 2];
const CARD_KEYS = ["mapIdx", "stars", "acc100", "time10", "firstListen", "chain", "rescue", "ver"];
function encodeCard(o) {
  let n = 0;
  CARD_BITS.forEach((bits, i) => {
    const cap = (2 ** bits) - 1;
    n = n * (2 ** bits) + Math.max(0, Math.min(cap, Math.round(fwdNum(o[CARD_KEYS[i]]))));
  });
  return "R-" + n.toString(36).toUpperCase();
}
function decodeCard(code) {
  const m = /^R-([0-9A-Z]{1,10})$/.exec(String(code || "").trim().toUpperCase());
  if (!m) return null;
  let n = parseInt(m[1], 36);
  if (!Number.isFinite(n) || n < 0) return null;
  const out = {};
  for (let i = CARD_BITS.length - 1; i >= 0; i--) {
    const mod = 2 ** CARD_BITS[i];
    out[CARD_KEYS[i]] = n % mod;
    n = Math.floor(n / mod);
  }
  if (n !== 0 || out.ver !== 1) return null;
  out.acc100 = Math.min(100, out.acc100);
  return out;
}

function refreshBest() {
  const saved = readStore().rally && readStore().rally.EP02;
  ui.best.hidden = !saved;
  if (!saved) return;
  ui.best.textContent = `本机最好 ${"★".repeat(saved.stars)}${"☆".repeat(3 - saved.stars)} · 听对 ${Math.min(100, Math.round((saved.bestAcc || 0) * 100))}%`;
}

function setMode(next) {
  mode = next;
  ui.title.hidden = next !== "title";
  ui.teach.hidden = next !== "teach";
  ui.count.hidden = next !== "countdown";
  ui.pausePanel.hidden = next !== "paused";
  ui.results.hidden = next !== "results";
  if (ui.quiz) ui.quiz.hidden = next !== "quiz";
  const racingUi = next === "countdown" || next === "racing" || next === "paused" || next === "results" || next === "quiz";
  ui.hud.hidden = !racingUi;
  ui.touch.hidden = !(next === "countdown" || next === "racing");
  if (ui.banner && next !== "racing" && next !== "countdown" && next !== "quiz") ui.banner.hidden = true;
  if (ui.routeMap) ui.routeMap.hidden = next !== "title";
  if (ui.how) {
    ui.how.hidden = next !== "title";
    ui.how.classList.toggle("shut", howSeen());
    if (next === "title" && !ui.how.classList.contains("shut")) ui.title.hidden = true;
  }
  // A2：统一接管排行榜 / 商店面板。只有 racing 期间允许它们保持打开；
  // 切到 quiz / paused / results / countdown / title / teach 一律收起并复位标志，
  // 避免「开榜 → 碰撞开 quiz → 答题回 racing」后 boardOpen 残留导致仿真冻结。
  if (next !== "racing") {
    boardOpen = false;
    shopOpen = false;
  }
  if (ui.boardPanel) ui.boardPanel.hidden = !boardOpen;
  if (ui.shop) ui.shop.hidden = !shopOpen;
  // A2：非 racing 态显式关闭引擎增益，避免卡在最后一次 setTargetAtTime 目标值；
  // 恢复 racing 后由 race.update() 末尾的 audio.engine() 每帧正常驱动。
  if (next !== "racing") audio.engineOff();
}

function bindHold(btn, field) {
  btn.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    btn.setPointerCapture(e.pointerId);
    pointer[field] = true;
  });
  const up = () => { pointer[field] = false; };
  btn.addEventListener("pointerup", up);
  btn.addEventListener("pointercancel", up);
}
bindHold(ui.left, "left");
bindHold(ui.right, "right");
// A5：独立触屏跳跃按钮。一次 pointerdown 置一次 jumpEdge，与键盘 Space 共用
// readInput() 的消费路径（const jump = jumpEdge; jumpEdge = false;），键盘与触屏同源。
ui.jump.addEventListener("pointerdown", (e) => {
  e.preventDefault();
  pointer.jump = true;
  jumpEdge = true;
});
const jumpUp = () => { pointer.jump = false; };
ui.jump.addEventListener("pointerup", jumpUp);
ui.jump.addEventListener("pointercancel", jumpUp);
ui.mid.addEventListener("pointerdown", (e) => {
  e.preventDefault();
  if (mode === "countdown") {
    ui.mid.setPointerCapture(e.pointerId);
    pointer.rocket = true;
  } else if (mode === "racing") replayEdge = true;
});
ui.mid.addEventListener("pointerup", () => { pointer.rocket = false; });
ui.mid.addEventListener("pointercancel", () => { pointer.rocket = false; });

window.addEventListener("keydown", (e) => {
  if (e.repeat) return;
  keys.add(e.code);
  if (["Space", "ArrowLeft", "ArrowRight"].includes(e.code)) e.preventDefault();
  if (e.code === "Space" && mode === "racing") jumpEdge = true;
  if (e.code === "KeyE") replayEdge = true;
  if (e.code === "KeyM") toggleMute();
  if (e.code === "Escape") {
    if (mode === "racing") setMode("paused");
    else if (mode === "paused") setMode("racing");
  }
  if (e.code === "Enter" && mode === "title") openTeach("listen");
});
window.addEventListener("keyup", (e) => keys.delete(e.code));
window.addEventListener("blur", () => { if (mode === "racing") setMode("paused"); });

/* IMPL-1B B2：分叉处「把车开进对应车道」= 点左右半屏 + 键盘 ArrowLeft/ArrowRight
   （及 A/D）并存、触屏优先。window 级 pointerdown 事件委托，不新增物理全屏层，
   因此不打乱 z 栈 / PM-6「零相交、canvas 不吞点击」判据。
   HIT_EXCLUDE 覆盖全部关键交互层：#jump 位于 #touch 内，点击它时本委托直接 return，
   既不设定 tapSteer、也不 preventDefault，故半屏命中绝不吞掉 #jump 的跳跃点击。
   按住式：pointerdown 设方向、pointerup/pointercancel 清除，避免车无限偏向一侧。
   单跳必过口径：不新增 260ms fireJump 状态机 / input.jump2 / jump2 字段 /
   jumpEvents 的 edge:"jump2" 分支；双击与触屏点两下无任何额外效果。 */
const HIT_EXCLUDE = "#hud, #touch, .panel, #confetti, #cheer, #signs, #tags, #minimap, #quiz, #board, #shop";
function onHalfTap(e) {
  if (mode !== "racing") return;
  if (e.target && e.target.closest && e.target.closest(HIT_EXCLUDE)) return;
  tapSteer = e.clientX < window.innerWidth / 2 ? "left" : "right";
}
function clearHalfTap() { tapSteer = ""; }
window.addEventListener("pointerdown", onHalfTap, { passive: true });
window.addEventListener("pointerup", clearHalfTap, { passive: true });
window.addEventListener("pointercancel", clearHalfTap, { passive: true });

/* FIX-C08：别的标签写了 KEY 时刷新在跑比赛的 HUD 余额，避免显示开赛快照。
   只读 e.newValue，不写回、不触发二次迁移、不写 bak。 */
window.addEventListener("storage", (e) => {
  if (e.key !== KEY || !e.newValue || !race) return;
  let d;
  try { d = JSON.parse(e.newValue); } catch (err) { return; }
  const r = d && d.rally && typeof d.rally === "object" ? d.rally : null;
  if (!r) return;
  race.state.gems = r.gems || 0;
  race.state.shields = r.shields || 0;
});

function toggleMute() {
  const on = commit((d) => { d.sound = d.sound === false; }).sound;
  audio.setMuted(!on);
  ui.mute.textContent = on ? "🔊" : "🔇";
  ui.mute.setAttribute("aria-label", on ? "关闭声音" : "打开声音");
}

function readInput() {
  const auto = window.__rally && window.__rally.autopilot && race && mode === "racing";
  /* IMPL-1B B2 / PM-2：键盘 ArrowLeft/KeyA、ArrowRight/KeyD、触屏 #steer、
     半屏点选 tapSteer 四来源投影方向一致；autopilot 分支仍按既有逻辑覆盖。 */
  let left = keys.has("ArrowLeft") || keys.has("KeyA") || pointer.left || tapSteer === "left";
  let right = keys.has("ArrowRight") || keys.has("KeyD") || pointer.right || tapSteer === "right";
  if (auto) {
    const act = race.activeGate();
    const steer = window.__rally.forceMiss ? -1 : 1;
    if (act && act.eta <= diff.fork + 0.15) {
      const dir = Math.sign(act.gate.correctLateral) * steer;
      left = dir < 0;
      right = dir > 0;
    } else { left = false; right = false; }
  }
  const replay = replayEdge;
  replayEdge = false;
  // A5：键盘 Space（keydown）与触屏 #jump（pointerdown）共用同一条边沿。
  const jump = jumpEdge;
  jumpEdge = false;
  return { left, right, replay, rocket: keys.has("Space") || pointer.rocket, jump };
}

function openTeach(id) {
  audio.unlock();
  audio.preload(allWords());
  audio.click();
  diff = DIFFICULTY[id];
  document.querySelector("#teach-diff").textContent = diff.label;
  /* C 段：静态两块仍是基础 /i/ ↔ /ɪ/ 教学（C07 锁定文案不动）；
     这里追加「本场杯赛重点」，让学生知道这张图要听的音素与词对。 */
  const m = currentMap();
  const clusters = m.clusters.map(([a, b]) => {
    const pa = PHONEMES[a], pb = PHONEMES[b];
    return `<b>/${pa.ipa}/ ${pa.label}</b> ↔ <b>/${pb.ipa}/ ${pb.label}</b>`;
  }).join("；");
  const sample = poolOf(m.id).slice(0, 3)
    .map((p) => `${p[0].word} / ${p[1].word}`).join("、");
  ui.teachFocus.innerHTML = `本场 <b>${m.name}</b>（${m.zone} · ${TUNING.laps} 圈）｜重点：${clusters}`
    + `<br>${m.blurb}　例词：${sample}`;
  setMode("teach");
}

function beginCountdown() {
  if (race) race.dispose();
  resultOpen = false;
  verdictShown = -1;                // 任务2：新一局复位 verdict 去重键
  fwdStart();                       // FWD X2：starts+1 落盘，inRace=true（内存）
  signKey = "";
  /* C 段：门按当前杯赛地图的词池生成，车手按选择传入；两者与 openQuiz 同源。 */
  race = createRace({
    track, diff, gates: buildGates(mapId), audio,
    mapId, character: currentChar(),
  });
  const s = track.sample(race.state.player.t);
  camera.x = s.x;
  camera.y = s.y;
  camera.h = Math.atan2(s.fy, s.fx);
  count = 2.999;
  lastBeep = 99;
  audio.click();
  setMode("countdown");
}

function followCamera(dt, snap) {
  const p = race.state.player;
  const s = track.sample(p.t);
  const vis = Math.max(-1, Math.min(1, p.lateral + (p.drift || 0)));
  const tx = s.x + s.fx * 90 + s.rx * vis * track.roadHalf;
  const ty = s.y + s.fy * 90 + s.ry * vis * track.roadHalf;
  const k = snap ? 1 : Math.min(1, dt * 8);
  camera.x += (tx - camera.x) * k;
  camera.y += (ty - camera.y) * k;
  const target = Math.atan2(s.fy, s.fx);
  camera.h = snap ? target : lerpAngle(camera.h, target, Math.min(1, dt * 8));
}

function updateDemo(dt) {
  const pace = reduced ? 0 : dt * 0.01;
  demo.forEach((k, i) => {
    k.t = (k.t + pace) % 1;
    const look = track.sample((k.t + 480 / track.length) % 1);
    k.yaw = Math.atan2(look.fy, look.fx);
  });
  const s = track.sample(demo[0].t);
  camera.x += (s.x - camera.x) * 0.06;
  camera.y += (s.y - camera.y) * 0.06;
  camera.h = lerpAngle(camera.h, Math.atan2(s.fy, s.fx), 0.06);
}

function lerpAngle(a, b, t) {
  const d = Math.atan2(Math.sin(b - a), Math.cos(b - a));
  return a + d * t;
}

function choiceHtml(choice) {
  const long = choice.length === "长";
  return `<img alt="" src="${choice.sprite}"><span class="w" lang="en">${choice.word}</span><span class="ipa">/${choice.ipa}/</span><small>${long ? "紧音" : "松音"}</small>`;
}

function paintLane(el, choice) {
  el.className = "sign on-lane " + (choice.length === "长" ? "is-long" : "is-short");
  el.innerHTML = choiceHtml(choice);
  const img = el.querySelector("img");
  if (img) img.addEventListener("error", () => img.remove(), { once: true });
}

function paintPick(el, choice, keyLabel) {
  el.className = "steer ipa-pick " + (choice.length === "长" ? "is-long" : "is-short");
  el.innerHTML = `<b class="ipa">/${choice.ipa}/</b><small>${keyLabel}</small>`;
}

function plainSteers() {
  ui.left.className = "steer";
  ui.right.className = "steer";
  ui.left.innerHTML = "<b>向左</b><small>A · ←</small>";
  ui.right.innerHTML = "<b>向右</b><small>D · →</small>";
}

/* CSEG-E1：D_preview = span·L + 0.5·preview·speed。复用闲置的 diff.preview 常量，
   用名义 diff.speed（不读 speedNow，避免加速/减速时预告窗口抖动）；
   span·L = f·v：follow 936 / listen 1020；0.5·p·v：546 / 600；合计 1482 / 1620 里程。 */
function previewDistance() {
  return race.state.span * track.length + 0.5 * diff.preview * diff.speed;
}

/* CSEG-E1 / S1：零文本中性预告牌。两块牌同 className / 同内容 / 同帧 / 同尺寸 /
   同不透明度，只有几何符号 ◇；无 word / IPA / label / sprite / is-long / is-short /
   左右色差 / 先后出现差异，绝不接触 spoken / correctLateral 等答案域。 */
function paintForecast(el) {
  el.className = "sign on-lane forecast";
  el.innerHTML = '<span class="fc">◇</span>';
}

/* CSEG-E1：S0–S3 相位的纯判定（零 DOM 副作用）。前置到 render 之前计算，
   使小地图 model 的 phase 与路牌状态机同帧，不滞后一帧。只消费 activeGate()/decide
   返回的唯一门，禁止遍历 state.gates 批量生成；gate.id（含 lap）区分两圈。
   race===null / 非比赛态返回 S0 空态（E6）。 */
function computeSignState() {
  const L = track.length;
  const D_preview = race ? previewDistance() : 0;
  if (!race || (mode !== "racing" && mode !== "paused" && mode !== "quiz")) {
    return { phase: "S0", gate: null, deciding: null, spanEff: 0, D_preview };
  }
  const act = race.activeGate();
  const deciding = race.state.decide;
  const gate = (deciding && deciding.gate) || (act && act.gate) || null;
  const dist = gate ? gate.line - race.state.player.odo : Infinity;
  let phase = "S0";
  if (gate && (gate.judged || gate.unheard)) phase = "S3";
  else if (gate && dist <= D_preview) phase = (gate.played || deciding) ? "S2" : "S1";
  const spanEff = phase === "S1" ? D_preview / L : race.state.span;
  return { phase, gate, deciding, spanEff, D_preview };
}

/* CSEG-E1：组装 minimapModel(view) 的纯数据入参。只取几何域 / 运动学 / 中性元信息，
   绝不带 spoken / other / correctLateral / left / right / pairKey / qType 等答案域。
   speed 用名义 diff.speed（不读 speedNow）；karts 传绝对 odo，t 由纯函数内部 odo 派生。 */
function buildMmView(mmW, mmH, phase) {
  const p = race.state.player;
  return {
    track,
    karts: race.state.karts,
    activeGate: race.activeGate(),
    playerOdo: p.odo,
    startOdo: p.startOdo,
    lap: race.state.lap,
    laps: race.state.laps,
    mapId: race.state.mapId,
    speed: diff.speed,          // 名义速度，不读 speedNow()
    phase,                      // 由 frame() 前置 computeSignState() 传入，与路牌同帧
    reduced,
    mmW, mmH, dpr,
  };
}

/* CSEG-E1：小地图每帧「显式显隐 + 内嵌 canvas 位图尺寸 + 纯模型快照」。
   visible 由 frame() 显式传入（表达式含 quiz、排除 boardOpen/shopOpen），每帧都设置
   hidden，不依赖「frozen 画面就不会变」——render()/syncSigns() 在冻结期每帧仍执行。
   race===null / 隐藏态返回 model=null，渲染层跳过绘制、不抛异常（E6）。 */
function updateMinimap(visible, signState) {
  const mm = ui.minimap, cv = ui.minimapC;
  if (mm) mm.hidden = !visible;
  if (!visible || !mm || !cv || !race) {
    lastMmModel = null;
    mmRect = null;
    return { visible: false, ctx: null, model: null };
  }
  const r = mm.getBoundingClientRect();
  mmRect = r;   // 容器 rect 含 2px border，供 placeLaneSign 外扩 8px 避让（更保守）
  /* 投影 / 位图尺寸用内嵌 canvas 的 CSS 尺寸（容器 content 区，不含 border），
     与 drawMinimap() 的 clearRect / setTransform 坐标系严格一致。 */
  const mmW = Math.round(cv.clientWidth) || Math.round(r.width);
  const mmH = Math.round(cv.clientHeight) || Math.round(r.height);
  if (!mmW || !mmH) {
    lastMmModel = null;
    return { visible: false, ctx: null, model: null };
  }
  /* 内嵌 canvas 位图尺寸按 dpr = min(2, devicePixelRatio) 设置；绘制前由
     drawMinimap() 内部 setTransform(dpr,…)，与 resize() 的 dpr 同源。 */
  const bw = Math.round(mmW * dpr), bh = Math.round(mmH * dpr);
  if (cv.width !== bw || cv.height !== bh || !mmCtx) {
    cv.width = bw;
    cv.height = bh;
    mmCtx = cv.getContext("2d");
  }
  const model = minimapModel(buildMmView(mmW, mmH, signState.phase));
  lastMmModel = model;
  if (ui.minimapLap && ui.minimapLap.textContent !== model.lapText) {
    ui.minimapLap.textContent = model.lapText;   // 极简「1/2」，不重复「听对 N」
  }
  return { visible: true, ctx: mmCtx, model };
}

function syncSigns(matrix, signState) {
  /* CSEG-E1：相位由 frame() 前置的 computeSignState() 统一判定一次，路牌状态机与
     小地图 minimapModel(view).phase 共用同一结果（不再各自算一遍、不再滞后一帧）。 */
  const { phase, gate, deciding, spanEff } = signState;
  /* Q2（quiz）+ E5 / §2.1.6（boardOpen / shopOpen 时 mode 仍是 racing；results 已结束）：
     显式隐藏路牌。刻意不触碰 signKey / dataset.opened / 牌内容 → 回 racing 后按 played
     无缝重现 S2，不重新 audio.playWord、不重播 open 动画、不因冻结期未 step 而错位。 */
  if (mode === "quiz" || mode === "results" || boardOpen || shopOpen) {
    ui.signs.hidden = true;
    ui.touch.classList.remove("hot");
    return;
  }
  /* S0–S3 状态机：phase / gate / deciding / spanEff 全部来自 computeSignState()。
     dist <= D_preview 是距离上限保险（防跨门/跨圈提前显示）；played（beginDecide）/
     judged / unheard 边沿决定相位。只消费 activeGate()/decide 返回的唯一门，
     禁止遍历 state.gates 批量生成 DOM 牌；两圈靠 gate.id 自然区分。 */
  const show = phase === "S1" || phase === "S2";
  ui.signs.hidden = !show;
  ui.touch.classList.toggle("hot", !!(show && mode === "racing"));
  if (!show) {
    if (signKey !== "plain") { signKey = "plain"; plainSteers(); }
    ui.signL.classList.remove("open");
    ui.signR.classList.remove("open");
    ui.signL.classList.remove("on-lane");
    ui.signR.classList.remove("on-lane");
    ui.signL.style.transform = "";
    ui.signR.style.transform = "";
    return;
  }
  /* signKey 纳入 gate.id（含 lap）与 phase → S1→S2 必然换 key 触发重绘 / open 重置。
     禁用 commitT / lineT % 1 / pairKey 作 key（两圈同 commitT 会串）。 */
  const key = `${gate.id}:${phase}:${gate.left.word}:${gate.right.word}`;
  if (key !== signKey) {
    signKey = key;
    /* 任务3：S1 预告阶段就显示真实选项卡片（paintLane 内容），不再用中性◇预告。
       卡片提前静态出现，玩家一眼看清左右两个 IPA + 单词；判定仍只在 state.decide
       可选阶段响应（见 race.js 选道即判），保证先听到词再选。 */
    paintLane(ui.signL, gate.left);
    paintLane(ui.signR, gate.right);
    paintPick(ui.left, gate.left, "A · ←");
    paintPick(ui.right, gate.right, "D · →");
    ui.signL.classList.remove("open");
    ui.signR.classList.remove("open");
    ui.signL.dataset.opened = "";
    ui.signR.dataset.opened = "";
  }
  /* 入场淡入：S1 提前出现 / S2 进入选道各淡入一次，open 类同时加到两块牌（同帧同动画）。
     lane-fade 是纯 opacity 淡入，无 translateY、无掉落位移。 */
  if (ui.signL.dataset.opened !== key) {
    ui.signL.dataset.opened = key;
    ui.signR.dataset.opened = key;
    void ui.signL.offsetWidth;
    ui.signL.classList.add("open");
    ui.signR.classList.add("open");
  }
  /* spanEff 由 computeSignState() 前置给出：S1 = D_preview/L（中性预告牌立在门线前
     0.36·D_preview，≈534/583 里程），S2 保留现状 race.state.span（≈337/367 里程）。 */
  placeLaneSign(ui.signL, matrix, gate, -1, spanEff);
  placeLaneSign(ui.signR, matrix, gate, 1, spanEff);
  syncTags(matrix);
}

function placeLaneSign(el, matrix, gate, side, spanEff) {
  /* CSEG-E1：span 参数化（S1 传 D_preview/L、S2 传 race.state.span）。
     Q4：t0/t1/t 与 odo0/odo1/odo 的 0.02·L 偏差本轮登记遗留项 G12，不改既有位置口径。
     保留 0.66/0.34/0.36 系数、project()、--lane、屏幕裁剪，以及 S12 的绝对 odo 传参。 */
  const span = spanEff;
  const t0 = gate.commitT - span * 0.66;
  const t1 = gate.commitT - span * 0.34;
  const t = gate.commitT - span * 0.36;
  /* C 段：pointAt 用相对 t（track.sample 取 0~1）；branchLateral 已改绝对里程，
     必须传 gate.line 对应的绝对 odo，否则横向偏移永远算成 0、路牌贴中线不动。 */
  const L = track.length;
  const odo0 = gate.line - span * L * 0.66;
  const odo1 = gate.line - span * L * 0.34;
  const odo = gate.line - span * L * 0.36;
  const p0 = race.pointAt(t0, race.branchLateral(gate, odo0, side));
  const p1 = race.pointAt(t1, race.branchLateral(gate, odo1, side));
  const here = race.pointAt(t, race.branchLateral(gate, odo, side));
  const a = project(matrix, p0.x, p0.y, dpr);
  const b = project(matrix, p1.x, p1.y, dpr);
  const c = project(matrix, here.x, here.y, dpr);
  const ang = Math.atan2(b.x - a.x, a.y - b.y);
  /* CSEG-E1：牌中心落入 #minimap rect 外扩 8px 则强制隐藏（防 z=5 小地图盖住 z=4 路牌）。
     mmRect 由 updateMinimap() 每帧缓存；隐藏态为 null，此时路牌本身也已隐藏。 */
  const overMm = !!mmRect &&
    c.x > mmRect.left - 8 && c.x < mmRect.right + 8 &&
    c.y > mmRect.top - 8 && c.y < mmRect.bottom + 8;
  const visible = c.x > -80 && c.x < w + 80 && c.y > -80 && c.y < h - 20 && !overMm;
  el.style.visibility = visible ? "visible" : "hidden";
  el.style.left = `${c.x}px`;
  el.style.top = `${c.y}px`;
  el.style.setProperty("--lane", `${ang}rad`);
}

function syncTags(matrix) {
  if (!race || mode === "title" || mode === "teach") {
    ui.tags.innerHTML = "";
    return;
  }
  ui.tags.innerHTML = race.state.karts.filter((kart) => kart.kind === "player").map((kart) => {
    const vis = Math.max(-1, Math.min(1, kart.lateral + (kart.drift || 0)));
    const p = race.pointAt(kart.t, vis);
    const s = project(matrix, p.x, p.y, dpr);
    if (s.x < -30 || s.x > w + 30 || s.y < 10 || s.y > h - 20) return "";
    return `<div class="kart-tag you" style="left:${s.x}px;top:${s.y}px"><b>You</b><small>${KART_TYPE}</small></div>`;
  }).join("");
}

function placeSign(el, p) {
  const visible = p.x > 8 && p.x < w - 8 && p.y > 8 && p.y < h - 150;
  el.style.visibility = visible ? "visible" : "hidden";
  el.style.left = `${p.x}px`;
  el.style.top = `${p.y}px`;
}

function syncQuizTilt(matrix) {
  if (!ui.quiz) return;
  if (mode !== "quiz" || !race) {
    ui.quiz.style.transform = "";
    return;
  }
  const L = race.state.track.length;
  const t = race.state.player.t;
  const here = race.pointAt(t, 0);
  const ahead = race.pointAt(t + 180 / L, 0);
  const a = project(matrix, here.x, here.y, dpr);
  const b = project(matrix, ahead.x, ahead.y, dpr);
  const ang = Math.atan2(b.x - a.x, a.y - b.y);
  ui.quiz.style.transform = `translate(-50%, -50%) rotate(${ang}rad)`;
}

function syncFork() {
  const d = race && race.state.decide;
  if (ui.fork) ui.fork.hidden = true;
  if (!ui.forkCount) return;
  const show = !!(d && d.phase === "hold");
  ui.forkCount.hidden = !show;
  if (!show) return;
  ui.forkCount.textContent = String(Math.max(1, Math.ceil(d.left)));
}

function burstConfetti() {
  /* IMPL-1B B1：局部小彩带——围绕 #cheer-word 中心生成，不再全屏 90 片。
     本函数只由 syncCheer() 在检测到新的 cheer.seq 时调用；撞墙 / 撞车 / 护身卡抵消
     三分支都不调用 cheer()，因此三分支零弹出。成功跳石与判门命中各自产生独立 seq，
     故每次「恰好一次欢呼 + 恰好一次彩带」，同词连续触发亦重播。 */
  const colors = ["#e0b44a", "#1f618d", "#b03a2e", "#1e7a4f", "#fffaf0", "#6c3483"];
  confettiBits = [];
  const r = ui.cheerWord && ui.cheerWord.getBoundingClientRect
    ? ui.cheerWord.getBoundingClientRect() : null;
  const cx = r && r.width ? r.left + r.width / 2 : window.innerWidth / 2;
  const cy = r && r.height ? r.top + r.height / 2 : window.innerHeight * 0.42;
  const spread = Math.min(r && r.width ? r.width : 120, 160) / 2;
  for (let i = 0; i < 16; i++) {
    const a = (i / 16) * Math.PI * 2 + Math.random() * 0.35;
    confettiBits.push({
      x: cx + (Math.random() - 0.5) * spread,
      y: cy + (Math.random() - 0.5) * 12,
      vx: Math.cos(a) * (70 + Math.random() * 90),
      vy: Math.sin(a) * (70 + Math.random() * 90) - 40,
      color: colors[i % colors.length],
      life: 0.9 + Math.random() * 0.5,
      age: 0,
      w: 4 + Math.random() * 3,
    });
  }
}

function drawConfetti(dt) {
  const canvas = ui.confetti;
  if (!canvas) return;
  const ctx2 = canvas.getContext("2d");
  const w0 = window.innerWidth;
  const h0 = window.innerHeight;
  if (canvas.width !== w0) { canvas.width = w0; canvas.height = h0; }
  ctx2.clearRect(0, 0, w0, h0);
  confettiBits.forEach((p) => {
    p.age += dt;
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.vy += 40 * dt;
    ctx2.globalAlpha = Math.max(0, 1 - p.age / p.life);
    ctx2.fillStyle = p.color;
    ctx2.fillRect(p.x, p.y, p.w, p.w * 0.6);
  });
  ctx2.globalAlpha = 1;
  confettiBits = confettiBits.filter((p) => p.age < p.life);
}

function syncCheer(dt) {
  const c = race && race.state.cheer;
  const on = !!(c && race.state.time < c.until);
  if (!ui.cheer) return;
  ui.cheer.hidden = !on;
  /* IMPL-1B B1：去重键 c.word → c.seq。cheer.seq 由 race.js 全局递增，
     同词连续触发（如连续两次成功跳石或同词判门）seq 必然不同 → 重播欢呼 + 局部彩带；
     判门命中与成功跳石两类触发源各自产生独立 seq，互不吞掉。 */
  const seq = c ? Number(c.seq) || 0 : -1;
  if (on && cheerShown !== seq) {
    cheerShown = seq;
    ui.cheerWord.textContent = c.word;
    burstConfetti();
  }
  if (!on) cheerShown = -1;
  drawConfetti(dt);
}

/* 任务2：即时结果提示。race.js 每次判门（选道即判 / 过门线兜底）产出 state.verdict，
   含递增 seq；表现层按 seq 去重重播，避免同词连续判定被吞。hit=true 绿勾RIGHT，
   hit=false 红叉WRONG。显示窗口约 1.15s（CSS verdict-pop），与 banner 文字并存。 */
function syncVerdict() {
  if (!ui.verdict) return;
  const v = race && race.state.verdict;
  if (!v || !race || race.state.time >= v.until || mode === "title" || mode === "teach") {
    ui.verdict.hidden = true;
    return;
  }
  ui.verdict.hidden = false;
  const seq = Number(v.seq) || 0;
  if (verdictShown !== seq) {
    verdictShown = seq;
    ui.verdict.classList.toggle("ok", !!v.hit);
    ui.verdict.classList.toggle("bad", !v.hit);
    const mark = ui.verdict.querySelector(".vmark");
    const word = ui.verdict.querySelector(".vword");
    if (mark) mark.textContent = v.hit ? "✓" : "✗";
    if (word) word.textContent = v.hit ? "RIGHT" : "WRONG";
    ui.verdict.classList.remove("show");
    void ui.verdict.offsetWidth;   // 强制回流以重播入场动画
    ui.verdict.classList.add("show");
  }
}

function syncHud() {
  if (!race || ui.hud.hidden) return;
  const p = race.state.player;
  const place = race.placeOf(p);
  ui.place.textContent = `第${place}名`;
  ui.kartType.textContent = `车型 ${KART_TYPE}`;
  const laps = race.state.laps || TUNING.laps;
  ui.gates.textContent = `第 ${Math.min(laps, race.state.lap + 1)}/${laps} 圈 · 听对 ${race.state.correct}`;
  if (ui.gems) ui.gems.textContent = `宝石 ${race.state.gems || 0}`;
  if (ui.shields) ui.shields.textContent = `护身 ${race.state.shields || 0}`;
  const dots = [0, 1, 2].map((i) => `<i class="${i < p.combo ? "on" : ""}"></i>`).join("");
  ui.combo.innerHTML = p.turbo > 0 ? "<b>清晰喷</b>" : dots;
  /* C 段：进度条分母随圈数放大，否则第 1 圈就满格、第 2 圈不动。 */
  const frac = Math.max(0, Math.min(1,
    (p.odo - p.startOdo) / (track.length * (race.state.laps || TUNING.laps))));
  ui.progress.style.width = `${frac * 100}%`;
  /* FWD M3：影子是 #progress 上的 HUD 三角刻度（s_ghost=time/bestTime），非第 4 辆车。
     Δt<0.3s 显示并排；首局无 bestTime 隐藏。只读 shadowBest 缓存，frame() 内零写盘。 */
  if (ui.ghost) {
    if (shadowBest > 0) {
      const sGhost = Math.max(0, Math.min(1, race.state.time / shadowBest));
      const dtGhost = frac * shadowBest - race.state.time;
      ui.ghost.hidden = false;
      ui.ghost.style.left = `${Math.min(99, Math.max(0, sGhost * 100))}%`;
      if (ui.ghostLabel) {
        const label = Math.abs(dtGhost) < 0.3 ? "并排"
          : dtGhost > 0 ? `领先影子 ${dtGhost.toFixed(1)}s` : `落后影子 ${(-dtGhost).toFixed(1)}s`;
        ui.ghostLabel.hidden = false;
        if (ui.ghostLabel.textContent !== label) ui.ghostLabel.textContent = label;
      }
    } else {
      ui.ghost.hidden = true;
      if (ui.ghostLabel) { ui.ghostLabel.hidden = true; if (ui.ghostLabel.textContent) ui.ghostLabel.textContent = ""; }
    }
  }
  const showBanner = race.state.banner && race.state.bannerT > 0;
  ui.banner.hidden = !showBanner;
  if (showBanner && ui.banner.textContent !== race.state.banner) {
    ui.banner.textContent = race.state.banner;
    ui.live.textContent = race.state.banner;
  }
  if (mode === "countdown") {
    ui.mid.innerHTML = pointer.rocket || keys.has("Space") ? "<b>起跑就绪</b>" : "<b>按住起跑</b><small>空格</small>";
    const n = count > 0 ? Math.ceil(count) : 0;
    ui.countNum.textContent = n > 0 ? String(n) : "GO";
    ui.countNum.classList.toggle("go", n === 0);
    if (ui.nitroBar) ui.nitroBar.style.width = `${Math.round((race.state.nitro || 0) * 100)}%`;
    ui.countHint.textContent = "长按空格充氮，起步先冲出去";
  } else if (mode === "racing") {
    const act = race.activeGate();
    const canReplay = act && act.gate.played && !act.gate.judged && !act.gate.replayed;
    ui.mid.disabled = !canReplay;
    ui.mid.innerHTML = "<b>再听一次</b><small>E · 打断连击</small>";
  }
}

function openResults() {
  resultOpen = true;
  const raw = race.result();
  // A1：bestAcc / 星星只反映闸门命中率（hits.length / total），额外惩罚题完全不参与。
  const scored = scoreRace(raw.place, raw.hits.length, raw.total);
  /* C 段：音标卡唯一解锁来源 = 赛事地图完赛且答对的门所属 unit。
     宝石不参与兑换。unlocked 是跨站权威域，必须取并集，禁止整体覆盖。 */
  const m = currentMap();
  /* FWD：写前存档快照——bestTime / 上局 firstListen 必须在本次 commit 覆盖前读取。
     只保留必要前置量，commit() 紧跟其后（C08 S1.4 写点收口断言要求 900 字符内）。 */
  const savedRally = readStore().rally || {};
  const prevEar = savedRally.ear && typeof savedRally.ear === "object" ? savedRally.ear : {};
  const prevRecent = Array.isArray(prevEar.recent) ? prevEar.recent.filter((n) => Number.isFinite(n)) : [];
  const near = nearMissFor(raw, savedRally);
  const earned = [...new Set(raw.hits.map((g) => g.spoken.unit).filter(Boolean))];
  let newlyUnlocked = [];
  commit((d) => {
    const prev = d.rally.EP02 || {};
    d.rally.EP02 = {
      stars: Math.max(prev.stars || 0, scored.stars),
      bestAcc: Math.max(prev.bestAcc || 0, scored.acc),
      lastPlace: raw.place,
      played: (prev.played || 0) + 1,
      diff: diff.id,
    };
    const before = Array.isArray(d.rally.unlocked) ? d.rally.unlocked.slice() : [];
    d.rally.unlocked = unionArr(before, earned);
    const fresh = earned.filter((u) => !before.includes(u));
    newlyUnlocked = fresh;
    if (fresh.length) {
      /* unlockLog 是跨站并集域（store.js 按 unit+at 去重），这里只追加、不覆盖。 */
      const log = Array.isArray(d.rally.unlockLog) ? d.rally.unlockLog.slice() : [];
      d.rally.unlockLog = log.concat(fresh.map((u) => ({
        unit: u, at: new Date().toISOString(), meta: `${m.id}#${raw.place}`,
      })));
    }
    if (!d.rally.maps || typeof d.rally.maps !== "object") d.rally.maps = {};
    const mp = d.rally.maps[m.id] || {};
    d.rally.maps[m.id] = {
      wins: (mp.wins || 0) + 1,
      bestStars: Math.max(mp.bestStars || 0, scored.stars),
      bestAcc: Math.max(mp.bestAcc || 0, scored.acc),
      bestTime: mp.bestTime ? Math.min(mp.bestTime, raw.time) : raw.time,
    };
    /* FWD X4：与上方 EP02 / unlocked / unlockLog / maps 四处既有赋值并列追加，
       四处赋值逐字未动。resultOpen 一次性门天然保证 games 不双计。 */
    const fNow = Date.now();
    fwdWrite(d, {
      games: fwdNum((d.rally.fwd || {}).games) + 1,
      ring: ((d.rally.fwd && Array.isArray(d.rally.fwd.ring))
        ? d.rally.fwd.ring.filter(isTuple12) : []).concat([fwdTuple(raw)]).slice(-12),
      last: fNow,
    });
    inRace = false;
    const curEar = (d.rally.ear && typeof d.rally.ear === "object") ? d.rally.ear : prevEar;
    const recent = Array.isArray(curEar.recent) ? curEar.recent.filter((n) => Number.isFinite(n)).slice(-9) : [];
    recent.push(fwdNum(raw.firstListen));
    d.rally.ear = {
      firstListenSum: fwdNum(curEar.firstListenSum) + fwdNum(raw.firstListen),
      cleanChainBest: Math.max(fwdNum(curEar.cleanChainBest), fwdNum(raw.cleanChain)),
      recent,
    };
    d.rally.shadow = {
      bestTime: d.rally.maps[m.id].bestTime,
      lastDt: Math.round((near.dt === null ? 0 : near.dt) * 10) / 10,
    };
    shadowBest = Number(d.rally.maps[m.id].bestTime) || 0;
    return fresh;
  });
  /* FWD：以下纯展示量在 commit 之后计算（写前只需 savedRally / prevRecent / near）。 */
  const firstListen = fwdNum(raw.firstListen);
  const chain = fwdNum(raw.cleanChain);
  const rescue = fwdNum(raw.rescue);
  const dFirst = prevRecent.length ? firstListen - prevRecent[prevRecent.length - 1] : null;
  const m2Line = `这局 ${firstListen}/${raw.total} 一次听准 · ${dFirst === null ? "首次记录" : `比上局 ${dFirst >= 0 ? "+" : ""}${dFirst}`}`;
  const cardCode = encodeCard({
    mapIdx: RACE_MAPS.findIndex((x) => x.id === mapId),
    stars: scored.stars, acc100: Math.round(scored.acc * 100),
    time10: Math.round(fwdNum(raw.time) * 10),
    firstListen, chain, rescue, ver: 1,
  });
  audio.engineOff();
  const star = "★".repeat(scored.stars) + "☆".repeat(3 - scored.stars);
  const miss = raw.misses.map((g) =>
    `<li><button type="button" data-word="${g.spoken.word}">▶ ${g.spoken.word}</button><span class="ipa">/${g.spoken.ipa}/</span> ${g.spoken.hint}</li>`
  ).join("");
  const unlockLine = newlyUnlocked.length
    ? `<p class="fine">🏁 本场解锁 ${newlyUnlocked.length} 张音标卡：${newlyUnlocked.map((u) => (PHONEMES[u] ? `/${PHONEMES[u].ipa}/` : u)).join("、")}　（去图鉴「赛事卡」查看）</p>`
    : `<p class="fine">本场没有新卡。答对分岔门即可解锁对应音标精灵，换个杯赛地图还能遇到别的音。</p>`;
  /* M1 默认中性；仅 ?m1=on 才换带目标文案（默认 off / 显式 on，无 ?m1=off）。 */
  const againLabel = M1_ON ? `再跑一场 · ${near.goal}` : "再跑一场";
  ui.results.innerHTML = `
    <p class="eyebrow">${m.name} · ${m.zone} · ${diff.label} · ${TUNING.laps} 圈</p>
    <h2>第 ${raw.place} 名</h2>
    <p class="stars" aria-label="${scored.stars} 星">${star}</p>
    <p class="near-miss">${near.line}</p>
    <p class="fine">${m2Line}${dFirst === null ? "" : `（救援题 ${rescue} 道 · 最长连听 ${chain} 题）`}</p>
    <p>听对 ${raw.correct} / ${raw.total} · 用时 ${raw.time.toFixed(1)} 秒</p>
    ${unlockLine}
    ${raw.quizTotal ? `<p class="fine">额外听辨 ${raw.quizCorrect} / ${raw.quizTotal} · 惩罚题独立统计，不计入听对率、星星与名次</p>` : ""}
    ${raw.unheard.length ? `<p class="fine">有 ${raw.unheard.length} 个词没来得及听到，未计入答错。</p>` : ""}
    <p class="fine">${scored.stars === 3 ? "听对了至少 80%，而且跑进了前两名。" : "三星需要跑进前两名，并且听对至少 80%。听对会直接加速。"}</p>
    ${miss ? `<ul class="misses">${miss}</ul>` : "<p>这两圈的词都开进了正确车道。</p>"}
    <p class="fine fwd-card">成绩卡 <code id="score-card">${cardCode}</code>
      <button type="button" class="btn ghost" id="btn-copy-card">复制成绩卡</button></p>
    <p class="fine fwd-card"><input id="rival-code" type="text" maxlength="12" placeholder="贴同学码比一比" aria-label="同学成绩码">
      <button type="button" class="btn ghost" id="btn-rival">比一比</button>
      <span id="rival-msg" hidden></span></p>
    <p class="fine">进度记在这台设备的探险队存档里，不改闯关星星。</p>
    <div class="row">
      <button type="button" class="btn" id="btn-again">${againLabel}</button>
      <button type="button" class="btn ghost" id="btn-title">回标题</button>
    </div>`;
  ui.results.hidden = false;
  setMode("results");
  ui.results.querySelector("#btn-again").onclick = () => {
    fwdAgain();                       // FWD X3：again+1 + ring 末位回填（先于 X2）
    beginCountdown();
  };
  ui.results.querySelector("#btn-title").onclick = () => { fwdQuit(); refreshBest(); setMode("title"); };
  ui.results.querySelectorAll("[data-word]").forEach((btn) => {
    btn.onclick = () => { audio.unlock(); audio.playWord(btn.dataset.word); };
  });
  /* M3 成绩卡：复制走 navigator.clipboard，失败退化为可手抄文本；同学码本地对比 ≤5 条。 */
  const copyBtn = ui.results.querySelector("#btn-copy-card");
  const rivalInput = ui.results.querySelector("#rival-code");
  const rivalMsg = ui.results.querySelector("#rival-msg");
  if (copyBtn) copyBtn.onclick = async () => {
    try {
      if (!navigator.clipboard) throw new Error("clipboard unavailable");
      await navigator.clipboard.writeText(cardCode);
      rivalMsg.textContent = "已复制成绩卡";
    } catch (e) {
      rivalMsg.textContent = `复制失败，请手抄：${cardCode}`;
    }
    rivalMsg.hidden = false;
  };
  const rivalBtn = ui.results.querySelector("#btn-rival");
  if (rivalBtn) rivalBtn.onclick = () => {
    const code = rivalInput ? rivalInput.value.trim().toUpperCase() : "";
    const dec = decodeCard(code);
    const me = decodeCard(cardCode);
    if (!dec || !me) { rivalMsg.textContent = "成绩码无效，请检查后重试"; rivalMsg.hidden = false; return; }
    rivalMsg.textContent = `同学 ${dec.acc100}% / ${(dec.time10 / 10).toFixed(1)}s，你 ${me.acc100}% / ${(me.time10 / 10).toFixed(1)}s`;
    rivalMsg.hidden = false;
    commit((d) => {
      const list = Array.isArray(d.rally.rivals) ? d.rally.rivals.slice() : [];
      if (!list.some((r) => r && r.code === code)) {
        list.push({ code, acc: dec.acc100, t: dec.time10, s: dec.stars, fl: dec.firstListen, ch: dec.chain });
      }
      d.rally.rivals = list.slice(-5);
    });
  };
}

function resize() {
  dpr = Math.min(2, window.devicePixelRatio || 1);
  w = window.innerWidth;
  h = window.innerHeight;
  canvas.width = Math.round(w * dpr);
  canvas.height = Math.round(h * dpr);
}
window.addEventListener("resize", resize);
resize();

document.querySelector("#btn-follow").onclick = () => openTeach("follow");
document.querySelector("#btn-listen").onclick = () => openTeach("listen");
document.querySelector("#btn-back-title").onclick = () => { fwdQuit(); setMode("title"); };
document.querySelector("#btn-grid").onclick = () => beginCountdown();
document.querySelectorAll(".play[data-word]").forEach((btn) => {
  btn.onclick = () => { audio.unlock(); audio.playWord(btn.dataset.word); audio.click(); };
});
ui.mute.onclick = () => toggleMute();
ui.pause.onclick = () => { if (mode === "racing") setMode("paused"); else if (mode === "paused") setMode("racing"); };
document.querySelector("#btn-resume").onclick = () => setMode("racing");
document.querySelector("#btn-quit").onclick = () => { fwdQuit(); audio.engineOff(); refreshBest(); setMode("title"); };

const soundOn = readStore().sound !== false;
audio.setMuted(!soundOn);
ui.mute.textContent = soundOn ? "🔊" : "🔇";
refreshBest();
renderPickers();

function openQuizCard() {
  const q = race && race.state.quiz;
  if (!q || mode === "quiz") return;
  setMode("quiz");
  ui.quizWhy.textContent = q.reason === "wall" ? "碰到路沿，车停住了" : q.reason === "rock" ? "碰到石头，车停住了" : "撞到别的车，车停住了";
  ui.quizResult.textContent = "";
  /* C 段：3 种题型共用同一答案键（word === spoken.word），只换题干与选项呈现。
     B7：options 两项互异、spoken 必在其内，由 openQuiz 保证，这里不做数值改动。 */
  const kind = q.qType || "word";
  ui.quizTitle.textContent = QUIZ_TITLES[kind] || QUIZ_TITLES.word;
  /* 题干绝不能泄答案：word 题考「听词辨词」，只提示重听；
     ipa / type 题考的是音值与类别，才把词面写出来作为可访问性提示。 */
  if (kind === "word") {
    ui.quizPrompt.textContent = "没听清可以点喇叭再听一遍，然后选你听到的词。";
  } else {
    ui.quizPrompt.innerHTML = `词：<b>${q.spoken.word}</b>　（点喇叭可再听一遍）`;
  }
  const label = (o) => {
    if (kind === "ipa") return `<span class="ipa">/${o.ipa}/</span>`;
    if (kind === "type") return `<span class="ipa">${o.label}</span>`;
    return `<span class="ipa">/${o.ipa}/</span> ${o.word}`;
  };
  ui.quizOptions.innerHTML = q.options.map((o) =>
    `<button type="button" class="btn ghost quiz-opt" data-word="${o.word}">${label(o)}</button>`
  ).join("");
  ui.quizOptions.querySelectorAll("button").forEach((btn) => {
    btn.onclick = () => pickQuiz(btn.dataset.word);
  });
}

function pickQuiz(word) {
  const res = race.finishQuiz(word);
  if (!res) return;
  ui.quizResult.textContent = res.hit ? `对了 · ${res.spoken.word}` : `错了 · 是 ${res.spoken.word}`;
  ui.quizOptions.querySelectorAll("button").forEach((btn) => {
    btn.disabled = true;
    if (btn.dataset.word === res.spoken.word) btn.classList.add("ok");
    else if (btn.dataset.word === word) btn.classList.add("bad");
  });
  setTimeout(() => { if (mode === "quiz") setMode("racing"); }, 850);
}

function renderBoard() {
  if (!race) return;
  ui.boardBody.innerHTML = race.answerBoard().map((r) => {
    const items = r.answers.length
      ? r.answers.map((a) => `<li class="${a.hit ? "ok" : "bad"}">${a.hit ? "✓" : "✗"} <span class="ipa">/${a.ipa}/</span> ${a.word}</li>`).join("")
      : "<li>还没答过</li>";
    return `<article><h3>${r.name} · ${r.correct}</h3><ul>${items}</ul></article>`;
  }).join("");
}

document.querySelector("#btn-board").onclick = () => {
  if (!race || mode === "title" || mode === "teach") return;
  boardOpen = true;
  audio.engineOff(); // A2：开榜冻结仿真，显式收引擎增益
  renderBoard();
  ui.boardPanel.hidden = false;
};
document.querySelector("#board-close").onclick = () => {
  boardOpen = false;
  ui.boardPanel.hidden = true;
};
function paintShop() {
  const pack = readPack();
  ui.shopGems.textContent = `宝石 ${pack.gems} · 护身卡 ${pack.shields}`;
  /* cards.js 的 card.cost 字段已标记 deprecated：保留但不展示、不参与任何兑换（用户口径①）。 */
  const phonemes = CARDS.map((card) => {
    /* FIX-C03：唯一解锁口径 = 四大杯赛赛事地图写入的 rally.unlocked（unit id）；
       旧 collected / stars 口径已彻底退役，无任何 fallback（30 关全通也不会全卡解锁）。 */
    const open = pack.unlocked.includes(card.id);
    return `<button type="button" class="card${open ? " have" : " locked"}" disabled title="图鉴 ${card.sym}">
      <img src="../音标大闯关/assets/sprites/cards/${card.id}.webp?v=fwd-20261121" alt="${card.sym}">
      <b class="ipa">/${IPA(card)}/</b>
      <small>${card.name}</small>
      <small>${card.rarity} · ${open ? "已解锁 · 四大杯赛" : "待解锁 · 四大杯赛"}</small>
    </button>`;
  }).join("");
  const gear = (list, owned, equipped, kind) => list.map((item) => {
    const have = owned.includes(item.id);
    const on = equipped === item.id;
    const label = have ? (on ? "使用中" : "装备") : `${item.cost} 宝石`;
    return `<button type="button" data-buy="${kind}" data-id="${item.id}">${item.tier}<small>${label}</small></button>`;
  }).join("");
  ui.shopList.innerHTML = `
    <h3>音标卡</h3>
    <p class="fine">按稀有度排列。音标卡只能通过四大杯赛的卡丁车赛事地图解锁，宝石不能兑换音标卡。</p>
    <div class="shop-grid">${phonemes}</div>
    <h3>车身颜色</h3>
    <p class="fine">基础 50，进阶 100，稀有 200。越高等级越亮，并带动态光。</p>
    <div class="shop-row">${gear(PAINTS, pack.ownedPaints, pack.paint, "paint")}</div>
    <h3>车身装饰</h3>
    <div class="shop-row">${gear(TRIMS, pack.ownedTrims, pack.trim, "trim")}</div>
    <h3>功能卡</h3>
    <div class="shop-row"><button type="button" data-buy="shield">护身卡<small>抵消一次石头撞击 · ${SHIELD_COST} 宝石</small></button></div>`;
}
function howSeen() {
  const data = readStore();
  return !!(data.rally && data.rally.howSeen);
}
function markHowSeen() {
  /* FIX-C08：走 commit，避免用陈旧内存快照覆写别站进度。 */
  commit((d) => { d.rally.howSeen = true; });
}
document.querySelector("#how-close").onclick = () => {
  markHowSeen();
  ui.how.classList.add("shut");
  ui.title.hidden = false;
};
document.querySelector("#how-tab").onclick = () => {
  ui.how.classList.remove("shut");
  ui.title.hidden = true;
  shopOpen = false;
  ui.shop.hidden = true;
};
document.querySelector("#how-shop").onclick = () => {
  ui.how.classList.add("shut");
  ui.title.hidden = false;
  shopOpen = true;
  audio.engineOff(); // A2：开店冻结仿真，显式收引擎增益
  paintShop();
  ui.shop.hidden = false;
};
document.querySelector("#shop-close").onclick = () => {
  fwdQuit();
  shopOpen = false;
  ui.shop.hidden = true;
  if (race) race.dispose();
  race = null;
  audio.engineOff();
  refreshBest();
  setMode("title");
};
ui.shopList.addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-buy]");
  if (!btn) return;
  const kind = btn.dataset.buy;
  if (kind === "shield") {
    patchRally((rally) => {
      if ((rally.gems || 0) < SHIELD_COST) return;
      rally.gems -= SHIELD_COST;
      rally.shields = (rally.shields || 0) + 1;
    });
  } else if (kind === "paint" || kind === "trim") {
    const list = kind === "paint" ? PAINTS : TRIMS;
    const item = list.find((entry) => entry.id === btn.dataset.id);
    if (!item) return;
    const ownedKey = kind === "paint" ? "ownedPaints" : "ownedTrims";
    const equipKey = kind === "paint" ? "paint" : "trim";
    patchRally((rally) => {
      const owned = Array.isArray(rally[ownedKey]) ? rally[ownedKey].slice() : [];
      if (!owned.includes(item.id)) {
        if ((rally.gems || 0) < item.cost) return;
        rally.gems -= item.cost;
        owned.push(item.id);
        rally[ownedKey] = owned;
      }
      rally[equipKey] = item.id;
    });
  }
  paintShop();
});
ui.quizReplay.onclick = () => {
  const q = race && race.state.quiz;
  if (q) { audio.unlock(); audio.playWord(q.spoken.word); }
};

/* FWD X5：页面卸载 / 切后台各挂一次监听；fwdQuit 的 inRace 守卫保证不重复计 quits。 */
window.addEventListener("pagehide", () => { fwdQuit(); });
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") fwdQuit();
});

const s0 = track.sample(demo[0].t);
camera.x = s0.x;
camera.y = s0.y;
camera.h = Math.atan2(s0.fy, s0.fx);
fwdInit();                            // FWD X1：v=1 / sess+1 / start，建立内存镜像
setMode("title");

let last = performance.now();
let simTime = 0; // A2：仿真 / 渲染时钟，冻结态不累加
function frame(now) {
  const dt = Math.max(0, Math.min(0.033, (now - last) / 1000));
  last = now;
  // A2：暂停 / 结果 / 答题 / 榜 / 店期间不推进仿真与渲染时钟，
  // 保证 render.js 的 spin = time * 16 在冻结态不转（原来传 now/1000 是真实墙钟）。
  const frozen = mode === "paused" || mode === "results" || mode === "quiz" || boardOpen || shopOpen;
  if (!frozen) simTime += dt;
  const input = readInput();
  if (mode === "title" || mode === "teach") updateDemo(dt);
  else if (mode === "countdown") {
    race.previewSteer(dt, input);
    if (input.rocket) race.state.nitro = Math.min(1, (race.state.nitro || 0) + dt / 2.6);
    count -= dt;
    if (count > 0) {
      const n = Math.ceil(count);
      if (n !== lastBeep) { audio.beep(4 - n); lastBeep = n; }
    } else if (lastBeep !== 0) {
      audio.go();
      lastBeep = 0;
    }
    if (count <= -0.42) {
      race.launch(race.state.nitro || 0);
      setMode("racing");
    }
    followCamera(dt, count > 2.6);
  } else if (mode === "racing") {
    if (!boardOpen && !shopOpen) race.update(dt, input);
    if (race.state.quiz) openQuizCard();
    followCamera(dt, false);
    if (race.state.finished && !resultOpen && race.state.time > race.state.finishTime + 1.05) openResults();
  } else if (mode === "quiz") {
    followCamera(dt, false);
  }
  const karts = (mode === "title" || mode === "teach" || !race) ? demo : race.state.karts;
  /* C 段：两圈的门 commitT 相同，全量交给 render 会把 4 个门重复画在 2 个位置。
     只把当前圈的门交给渲染层；门判定与路牌仍用 race.state.gates 全量。 */
  const lapNow = race ? race.state.lap : 0;
  const visibleGates = race && mode !== "title" && mode !== "teach"
    ? race.state.gates.filter((g) => g.lap === lapNow) : [];
  /* CSEG-E1 / §2.1.6：显式显隐表达式。boardOpen/shopOpen 打开时 mode 仍是 racing，
     必须查软锁；quiz 显示但冻结（不随面板隐藏，靠 z-index 层叠）；
     title / teach / results 隐藏。`&& !!race` 兜底 race===null（E6）。 */
  const visible = (mode === "countdown" || mode === "racing" || mode === "paused" || mode === "quiz")
    && !boardOpen && !shopOpen && !!race;
  /* CSEG-E1：S0–S3 相位前置到 render / updateMinimap / syncSigns 之前一次判定，三方共用
     同一结果（消除滞后一帧）。冻结态沿用上一帧 signState，保证 quiz / paused「显示但冻结」：
     step(60) 后 phase 与 model 逐字段相等（H2 / H9），且不重新 audio.playWord。 */
  const signState = (frozen && lastSignState) ? lastSignState : computeSignState();
  lastSignState = signState;
  signPhase = signState.phase;
  const mm = updateMinimap(visible, signState);
  const matrix = render(ctx, {
    w, h, dpr, track,
    gates: visibleGates,
    span: race ? race.state.span : 0.02,
    /* IMPL-1B B1：与判定层同一常数源（race.state.merge = TUNING.mergeDt = 0.028），
       消除 2D flareAt 收拢窗口与判定层分叉闭合相位漂移；title 态 race 为空时兜底 0.028。 */
    merge: race && race.state ? race.state.merge : 0.028,
    karts,
    time: simTime,
    ribbonT: race && mode !== "title" && mode !== "teach" ? (race.state.ribbonT || 0) : 0,
    camera,
    shake: race && mode === "racing" ? race.state.shake : 0,
    particles: race && mode !== "title" && mode !== "teach" ? race.state.particles : [],
    pickups: race && mode !== "title" && mode !== "teach" ? race.state.pickups : [],
    /* IMPL-1B B4：贴地起跳标线提前量。AIR_COVER = airMax·speed + ROCK_HIT_BAND
       （airMax=0.5s、speed 用名义 diff.speed 260/300、ROCK_HIT_BAND=78 unit）≈208/228 unit；
       除以赛道长 L 归一化成 t 偏移交给 render.js，2D 层零判定常量、零硬编码。 */
    jumpLeadT: (0.5 * diff.speed + ROCK_HIT_BAND) / track.length,
    laneLateral: TUNING.laneLateral,
    reduced,
    look: playerLook(),
    minimap: visible,          // 布尔显式门控（取代旧 mode !== "title"）
    mmCtx: mm.ctx,
    mmModel: mm.model,
    anchor: mode === "title" || mode === "teach" ? 0.24 : 0.52,
  });
  if (race && mode !== "title" && mode !== "teach") { syncSigns(matrix, signState); syncTags(matrix); syncFork(); syncQuizTilt(matrix); }
  else { ui.signs.hidden = true; ui.tags.innerHTML = ""; if (ui.fork) ui.fork.hidden = true; }
  syncCheer(dt);
  syncVerdict();
  syncHud();
  if (!window.__rally._stepping) requestAnimationFrame(frame);
}
/* CSEG-E1：#5 断言所需的只读快照（全部零副作用、不写盘、不改游戏状态）。
   minimapModel() 优先返回当前帧快照；若在未接线帧被调用且 race 存在，则即时构建纯模型，
   保证 H6 / H10 在任何时刻都能拿到不含答案键的模型。minimapRect() 返回纯对象便于 JSON。 */
function currentMmModel() {
  if (lastMmModel) return lastMmModel;
  if (!race) return null;
  return minimapModel(buildMmView(160, 104, signPhase));
}
function currentMmRect() {
  const mm = ui.minimap;
  if (!mm || mm.hidden) return null;
  const r = mm.getBoundingClientRect();
  return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
}

window.__rally = {
  autopilot: false,
  forceMiss: false,
  get mode() { return mode; },
  get race() { return race; },
  get camera() { return camera; },
  get boardOpen() { return boardOpen; },   // A2 验收只读
  get shopOpen() { return shopOpen; },     // A2 验收只读
  get simTime() { return simTime; },       // A2 验收只读（渲染/仿真时钟）
  get signKey() { return signKey; },       // CSEG-E1 / H10 只读：含 gate.id + phase
  get signPhase() { return signPhase; },   // CSEG-E1 只读：当前 S0–S3 相位
  /* IMPL-1B B1：S7 交互断言取证用只读观测点（全部零副作用，仅取 race.state 现值）。 */
  get rockHits() { return race ? race.state.rockHits : 0; },
  get rockBudget() { return race ? race.state.rockBudget : 0; },
  get cheerSeq() { return race ? race.state.cheerSeq : 0; },
  /* FWD 只读投影：返回内存镜像副本，零写盘、零判定副作用。 */
  get fwd() { return fwd ? Object.assign({}, fwd, { ring: fwd.ring.map((t) => t.slice()) }) : null; },
  get pickups() { return race ? race.state.pickups : []; },
  minimapRect() { return currentMmRect(); },      // CSEG-E1 / H1 H3 H4 只读
  minimapModel() { return currentMmModel(); },    // CSEG-E1 / H6 H10 只读
  frame,
  step(n = 1) {
    this._stepping = true;
    if (!this._now) this._now = performance.now();
    for (let i = 0; i < n; i++) frame(this._now += 16.7);
    this._stepping = false;
  },
  vowels: VOWELS,
};

requestAnimationFrame(frame);
