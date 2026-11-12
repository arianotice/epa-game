import { BOOST, COLLIDE, QUIZ_TYPES, ROCKET, SLOW, TUNING, TURBO, forkSpan, hitsLane, pairKeyOf, pickQuizPair, poolOf } from "./config.js?v=hud-20261108";
import { offsetPoint } from "./track.js?v=hud-20261108";

export function createRace({ track, diff, gates, audio, mapId = "camp", character = null }) {
  const L = track.length;
  const charMul = character && character.steerMul ? character.steerMul : 1;
  const charAir = character && character.airMul ? character.airMul : 1;
  const span = forkSpan(diff, L);
  const merge = TUNING.mergeDt;
  const startT = 0.02;
  const mk = (id, name, kind, t, skill, home) => ({
    id, name, kind, skill, home,
    odo: t * track.length,
    startOdo: t * track.length,
    t,
    lateral: home,
    laneTarget: home,
    boost: 0,
    slow: 0,
    turbo: 0,
    combo: 0,
    correct: 0,
    bumpCd: 0,
    air: 0,
    hop: 0,
    jumpCd: 0,
    dashLeft: 0,
    wallCd: 0,
    startBoost: kind === "player" ? 0 : 1.8,
    answers: [],
    yaw: 0,
    drift: 0,
    launchWait: 0,
    choice: {},
    resolved: {},
  });

  const player = mk("you", "You", "player", startT, 1, 0);
  const rivals = [
    mk("a", "A", "rival", startT, 0.28, -0.55),
    mk("b", "B", "rival", startT, 0.42, 0.55),
  ];
  const karts = [player, rivals[0], rivals[1]];
  const startYaw = Math.atan2(track.sample(startT).fy, track.sample(startT).fx);
  karts.forEach((k) => { k.yaw = startYaw; });

  let missTimer = 0;
  const state = {
    track, diff, gates, span, merge,
    karts, player, rivals,
    time: 0,
    finished: false,
    finishTime: 0,
    shake: 0,
    banner: "",
    bannerT: 0,
    flashes: [],
    particles: [],
    correct: 0,
    wrong: 0,
    gateHits: 0,
    quizCorrect: 0,
    quizWrong: 0,
    quizTotal: 0,
    ribbonT: 0,
    lastJudgeAt: -10,
    nitro: 0,
    quiz: null,
    gems: 0,
    cards: [],
    pickups: [],
    /* C 段：mapId / lap / 额外题去重窗口 / 石头预警 */
    mapId,
    lap: 0,
    laps: TUNING.laps,
    recentPairs: [],
    warning: "",
    warningT: 0,
  };

  /* 每圈的门是独立对象（buildGates 已按 lap 拆好），这里把相对位置换成绝对里程，
     所有判定统一用 g.line，不再用 wrapDelta(t, commitT) —— 两圈不会互相抢门。 */
  gates.forEach((g) => { g.line = player.startOdo + g.lineT * L; });

  const STORE_KEY = "ipa-quest-v1";
  function loadWallet() {
    try {
      const data = JSON.parse(localStorage.getItem(STORE_KEY)) || {};
      const rally = data.rally || {};
      state.gems = rally.gems || 0;
      state.shields = rally.shields || 0;
    } catch (e) { /* 读不到就从 0 开始 */ }
  }
  /* FIX-C08：gems / shields 一律 delta，禁止把开赛快照的绝对值写回。
     读写入瞬间最新的整对象 → 相对增量 → 写回；保留其它字段、不写 schemaVersion。
     这样与 main.js 商店扣款 / 大闯关 save() 并发时不会双花或回滚进度。 */
  function applyWalletDelta(dGems, dShields) {
    try {
      const data = JSON.parse(localStorage.getItem(STORE_KEY)) || {};
      if (!data || typeof data !== "object") return;
      if (!data.rally || typeof data.rally !== "object") data.rally = {};
      data.rally.gems = (data.rally.gems || 0) + dGems;
      data.rally.shields = (data.rally.shields || 0) + dShields;
      localStorage.setItem(STORE_KEY, JSON.stringify(data));
      state.gems = data.rally.gems;
      state.shields = data.rally.shields;
    } catch (e) { /* 隐私模式可能拒绝写入 */ }
  }
  loadWallet();

  function buildField() {
    const lanes = [-0.55, 0, 0.55];
    const items = [];
    const blocked = (t) => {
      if (Math.min(Math.abs(t - startT), 1 - Math.abs(t - startT)) < 0.04) return true;
      return gates.some((g) => {
        const d = Math.min(Math.abs(g.commitT - t), 1 - Math.abs(g.commitT - t));
        return d < 0.04;
      });
    };
    const settle = (t) => {
      let mark = t;
      for (let n = 0; n < 8 && blocked(mark); n++) mark += 0.012;
      if (mark > 0.94) mark = 0.9;
      return mark;
    };
    const jitter = () => (Math.random() - 0.5) * 0.1;
    for (let i = 0; i < 8; i++) {
      const t = settle(0.12 + (0.74 * (i + 0.5) / 8) + (Math.random() - 0.5) * 0.012);
      items.push({
        id: `rock-${i}`,
        kind: "rock",
        t,
        lateral: Math.max(-0.66, Math.min(0.66, lanes[i % 3] + jitter())),
        taken: false,
      });
    }
    for (let i = 0; i < 10; i++) {
      const t = settle(0.14 + (0.72 * (i + 0.5) / 10) + 0.035);
      items.push({
        id: `gem-${i}`,
        kind: "gem",
        t,
        lateral: Math.max(-0.66, Math.min(0.66, lanes[(i + 1) % 3] + jitter())),
        taken: false,
      });
    }
    return items;
  }
  state.pickups = buildField();

  function wrapDelta(from, to) {
    let d = to - from;
    if (d < 0) d += 1;
    return d;
  }

  function placeOf(kart) {
    let n = 1;
    for (const other of karts) if (other !== kart && other.odo > kart.odo) n++;
    return n;
  }

  function activeGate() {
    let best = null;
    let bestEta = Infinity;
    for (const g of gates) {
      if (g.judged || g.unheard) continue;
      const dist = g.line - player.odo;
      if (dist < 0) continue;
      const eta = dist / Math.max(40, speedNow(player));
      if (eta < bestEta) { bestEta = eta; best = g; }
    }
    return best ? { gate: best, eta: bestEta } : null;
  }

  function baseMul(kart) {
    if (kart.kind === "player") return 1;
    return kart.id === "a" ? 1.02 : 1.008;
  }

  function speedNow(kart) {
    let mul = baseMul(kart);
    if (kart.turbo > 0) mul *= TURBO.mul;
    else if (kart.boost > 0) mul *= kart.kind === "player" ? BOOST.mul : 1.12;
    if (kart.slow > 0) mul *= SLOW.mul;
    return diff.speed * mul;
  }

  function burst(s, color, n) {
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2;
      const sp = 40 + Math.random() * 160;
      state.particles.push({
        x: s.x, y: s.y,
        vx: Math.cos(a) * sp + s.fx * 80,
        vy: Math.sin(a) * sp + s.fy * 80,
        life: 0.4 + Math.random() * 0.35,
        age: 0,
        color,
      });
    }
  }

  function cheer(combo) {
    const words = ["Good", "Excellent", "Marvellous"];
    const word = words[Math.min(words.length - 1, Math.max(0, (combo || 1) - 1))];
    state.cheer = { word, until: state.time + 3.4 };
    state.banner = `${word} · 对了`;
    state.bannerT = 3.4;
  }

  function judge(gate) {
    gate.judged = true;
    const hit = hitsLane(player.lateral, gate.correctLateral);
    gate.hit = hit;
    player.answers.push({ word: gate.spoken.word, ipa: gate.spoken.ipa, hit });
    state.lastJudgeAt = state.time;
    const s = track.sample(player.t);
    const pos = offsetPoint(s, player.lateral * track.roadHalf);
    if (hit) {
      // A1：只有分岔门命中才计分。state.correct 是 gateHits 的显示镜像，
      // 保证 HUD / 排行榜 / 结果页同源；额外惩罚题不再写这里（见 finishQuiz）。
      state.gateHits++;
      state.correct = state.gateHits;
      player.correct = state.correct;
      player.combo++;
      player.boost = Math.max(player.boost, 2.8);
      player.slow = 0;
      rivals.forEach((r, i) => {
        r.odo = Math.min(r.odo, player.odo - 220 - i * 60);
        r.t = ((r.odo % track.length) + track.length) % track.length / track.length;
        r.boost = 0;
      });
      audio.hit();
      burst(pos, "#e0b44a", 18);
      cheer(player.combo);
      if (player.combo >= 3) {
        player.turbo = TURBO.time;
        player.combo = 0;
        audio.turbo();
        burst(pos, "#f5e6a8", 28);
      }
    } else {
      state.wrong++;
      player.combo = 0;
      player.boost = 0;
      player.turbo = 0;
      player.slow = SLOW.time;
      const passer = rivals.slice().sort((a, b) => b.odo - a.odo)[0];
      passer.odo = player.odo + 320;
      passer.t = (passer.odo / track.length) % 1;
      passer.lateral = player.lateral >= 0 ? -0.7 : 0.7;
      passer.laneTarget = passer.lateral;
      passer.home = passer.lateral;
      passer.boost = 0.9;
      state.shake = 7;
      audio.miss();
      state.banner = `错了 · 是 ${gate.spoken.word}  /${gate.spoken.ipa}/`;
      state.bannerT = 1.35;
    }
  }

  function updateKart(kart, dt) {
    let mul = baseMul(kart);
    if (kart.turbo > 0) mul *= TURBO.mul;
    else if (kart.boost > 0) mul *= kart.kind === "player" ? BOOST.mul : 1.12;
    if (kart.kind !== "player" && kart.startBoost > 0) mul *= 1.45;
    if (kart.slow > 0) mul *= SLOW.mul;
    if (kart.kind !== "player") {
      const gap = (kart.odo - player.odo) / track.length;
      if (gap > 0.12) mul *= 0.94;
    }
    const base = diff.speed;
    kart.boost = Math.max(0, kart.boost - dt);
    kart.slow = Math.max(0, kart.slow - dt);
    kart.turbo = Math.max(0, kart.turbo - dt);
    kart.bumpCd = Math.max(0, kart.bumpCd - dt);
    kart.jumpCd = Math.max(0, (kart.jumpCd || 0) - dt);
    kart.startBoost = Math.max(0, kart.startBoost - dt);
    kart.launchWait = Math.max(0, kart.launchWait - dt);
    if (kart.kind === "player") {
      kart.air = Math.max(0, (kart.air || 0) - dt);
      /* C 段：起跳后的宽容窗口，提前一点起跳也能算「成功规避石头」。 */
      kart.hopWindow = Math.max(0, (kart.hopWindow || 0) - dt);
      // A4：落地（air 归零）才复位段数，杜绝「air 归零后每帧无限重置刷程」。
      if (kart.air === 0) kart.hop = 0;
    }
    const waiting = kart.launchWait > 0;
    if ((!state.finished || kart.kind !== "player") && !waiting) kart.odo += base * mul * dt;
    // A4：二段跳冲刺改为「里程预算 + 冷却」，分摊到若干帧推进，
    // 消除单帧 +=140 瞬移（V5）及其与 blockSplitter 回滚的幽灵拾取。
    if (kart.dashLeft > 0) {
      const d = Math.min(kart.dashLeft, 900 * dt);
      kart.odo += d;
      kart.dashLeft -= d;
    }
    kart.t = (kart.odo / L) % 1;
    const rate = kart.kind === "player" ? diff.steer * charMul : 2.4;
    const step = rate * dt;
    if (kart.lateral < kart.laneTarget) kart.lateral = Math.min(kart.laneTarget, kart.lateral + step);
    else if (kart.lateral > kart.laneTarget) kart.lateral = Math.max(kart.laneTarget, kart.lateral - step);
    kart.lateral = Math.max(-1, Math.min(1, kart.lateral));
    const s = track.sample(kart.t);
    const look = track.sample((kart.t + 480 / track.length) % 1);
    const lookH = Math.atan2(look.fy, look.fx);
    const steer = Math.max(-0.55, Math.min(0.55, (kart.laneTarget - kart.lateral) * 1.1));
    let branch = 0;
    const fork = gates.find((g) => !g.judged && !g.unheard &&
      kart.odo >= g.line - span * L && kart.odo <= g.line + merge * L);
    if (fork && Math.abs(kart.lateral) > 0.18) {
      const side = Math.sign(kart.lateral);
      const aheadOdo = kart.odo + 200;
      const aheadT = (aheadOdo / L) % 1;
      const p0 = offsetPoint(s, branchLateral(fork, kart.odo, side) * track.roadHalf);
      const sAhead = track.sample(aheadT);
      const p1 = offsetPoint(sAhead, branchLateral(fork, aheadOdo, side) * track.roadHalf);
      const laneH = Math.atan2(p1.y - p0.y, p1.x - p0.x);
      branch = Math.atan2(Math.sin(laneH - lookH), Math.cos(laneH - lookH));
    }
    kart.yaw = lerpAngle(kart.yaw, lookH + steer + branch, 1 - Math.pow(0.04, dt));
    const ahead = track.sample(kart.t + 140 / track.length);
    const ah = Math.atan2(ahead.fy, ahead.fx);
    const heading = Math.atan2(s.fy, s.fx);
    const curve = Math.atan2(Math.sin(ah - heading), Math.cos(ah - heading));
    const driftTarget = Math.max(-0.14, Math.min(0.14, -curve * 1.6));
    kart.drift += (driftTarget - kart.drift) * Math.min(1, dt * 4);
  }

  function lerpAngle(a, b, t) {
    const d = Math.atan2(Math.sin(b - a), Math.cos(b - a));
    return a + d * Math.max(0, Math.min(1, t));
  }

  /* C 段：odo 为绝对里程；门线用 g.line，故第 2 圈的门与第 1 圈互不串位。 */
  function branchLateral(gate, odo, side) {
    const spanLen = span * L;
    const start = gate.line - spanLen;
    const full = gate.line - spanLen * 0.42;
    const end = gate.line + merge * L;
    let f = 0;
    if (odo >= start && odo < full) f = (odo - start) / Math.max(0.0001, full - start);
    else if (odo >= full && odo <= gate.line) f = 1;
    else if (odo > gate.line && odo <= end) f = 1 - (odo - gate.line) / Math.max(0.0001, end - gate.line);
    f = Math.max(0, Math.min(1, f));
    const laneHalf = 0.72;
    const island = 0.28 * f;
    const center = TUNING.laneLateral;
    const lerp = (a, b) => a + (b - a) * f;
    if (side < 0) {
      const outer = lerp(-1, -center - laneHalf);
      const inner = lerp(-2 / track.roadHalf, -island);
      return (outer + inner) / 2;
    }
    const inner = lerp(2 / track.roadHalf, island);
    const outer = lerp(1, center + laneHalf);
    return (inner + outer) / 2;
  }

  function splitterHalf(odo) {
    const spanLen = span * L;
    let best = 0;
    for (const g of gates) {
      if (g.judged || g.unheard) continue;
      const start = g.line - spanLen;
      const full = g.line - spanLen * 0.42;
      let f = 0;
      if (odo >= start && odo < full) f = (odo - start) / Math.max(0.0001, full - start);
      else if (odo >= full && odo <= g.line + merge * L) f = 1;
      if (f > best) best = f;
    }
    return best * 0.34;
  }

  function blockSplitter(prevOdo, input) {
    const open = gates.find((g) => g.holdDone && !g.judged && !g.unheard);
    if (!open) return;
    const half = splitterHalf(player.odo);
    if (half < 0.12) return;
    if (Math.abs(player.lateral) >= half) return;
    const left = input && input.left && !(input.right);
    const right = input && input.right && !(input.left);
    if (left) player.lateral = -(half + 0.04);
    else if (right) player.lateral = half + 0.04;
    else {
      player.odo = prevOdo;
      player.t = (player.odo / track.length) % 1;
      player.boost = 0;
      player.turbo = 0;
    }
  }

  function answering() {
    return gates.some((g) => g.played && !g.judged);
  }

  function pressRivals() {
    if (!answering()) return;
    rivals.forEach((r, i) => {
      const behind = player.odo - 260 - i * 80;
      if (r.odo > behind) r.odo = behind;
      r.t = ((r.odo % track.length) + track.length) % track.length / track.length;
      const side = i === 0 ? -0.1 : 0.1;
      r.lateral = side;
      r.laneTarget = side;
    });
  }

  function shoveRival(rival) {
    const side = rival.lateral >= player.lateral ? 1 : -1;
    let lat = player.lateral + side * 0.82;
    if (Math.abs(lat) > 0.9) lat = player.lateral - side * 0.82;
    rival.lateral = Math.max(-0.88, Math.min(0.88, lat));
    rival.laneTarget = rival.lateral;
    rival.home = rival.lateral;
    rival.odo = player.odo - 240;
    rival.t = ((rival.odo % track.length) + track.length) % track.length / track.length;
    rival.drift = 0;
  }

  function beginDecide(act) {
    if (state.decide || state.quiz || !act) return;
    if (act.gate.judged || act.gate.unheard || act.gate.holdDone) return;
    const dist = act.gate.line - player.odo;
    const mouth = span * L * 0.55;
    const lead = mouth + 360 + speedNow(player) * 0.62;
    if (dist > lead) return;
    // A3：lastJudgeAt 只由 judge() 更新（分岔门播音节流），额外惩罚题不再刷新它
    // （见 finishQuiz），高频惩罚题因此不会把门挤成「静默漏播」。
    if (state.time - state.lastJudgeAt < 2.4) {
      // 到期强制放行：临近门线时即使未满间隔也必须开播，保证每个门在 commitT 前 played。
      if (dist > speedNow(player) * 0.55) return;
    }
    if (!act.gate.played) {
      act.gate.played = true;
      audio.playWord(act.gate.spoken.word);
    }
    state.decide = { gate: act.gate, phase: "reveal", arm: 0.55, left: 3 };
  }

  function commitMark(commitT) {
    const L = track.length;
    let mark = commitT % 1;
    if (mark < 0) mark += 1;
    return mark * L;
  }

  function nextLine(prevOdo, commitT) {
    const L = track.length;
    let line = Math.floor(prevOdo / L) * L + commitMark(commitT);
    if (line <= prevOdo) line += L;
    return line;
  }

  function hasPassed(odo, commitT) {
    const L = track.length;
    const mark = commitMark(commitT);
    const base = Math.floor(odo / L) * L;
    const line = base + mark;
    if (line <= odo && odo - line < L * 0.5) return true;
    const earlier = line - L;
    return earlier >= 0 && earlier <= odo && odo - earlier < L * 0.5;
  }

  function crossed(prevOdo, nowOdo, commitT) {
    const line = nextLine(prevOdo, commitT);
    return prevOdo < line && nowOdo >= line;
  }

  function openQuiz(reason) {
    if (state.quiz) return;
    /* C 段：从当前杯赛地图的词池取题，最近 3 对不重复 → 连续同对率 0%。
       同时随机题型，让额外题也覆盖 word / ipa / type 三种。 */
    const pair = pickQuizPair(poolOf(mapId), state.recentPairs);
    const key = pairKeyOf(pair);
    state.recentPairs.push(key);
    if (state.recentPairs.length > 3) state.recentPairs.shift();
    const spoken = Math.random() < 0.5 ? pair[0] : pair[1];
    const other = spoken === pair[0] ? pair[1] : pair[0];
    const options = Math.random() < 0.5 ? [spoken, other] : [other, spoken];
    const qType = QUIZ_TYPES[Math.floor(Math.random() * QUIZ_TYPES.length)];
    state.quiz = { spoken, options, reason, qType, pairKey: key };
    player.boost = 0;
    player.turbo = 0;
    player.slow = 0;
    player.combo = 0;
    audio.playWord(spoken.word);
    state.banner = "";
    state.bannerT = 0;
  }

  function finishQuiz(word) {
    if (!state.quiz) return null;
    const spoken = state.quiz.spoken;
    const hit = word === spoken.word;
    // A1：额外惩罚题独立统计，不进 correct / 听对率 / 星星 / total，
    // 也不改 place / 速度。答案打上 quiz 标记，排行榜按分岔门口径过滤（同源）。
    state.quizTotal++;
    if (hit) state.quizCorrect++;
    else state.quizWrong++;
    player.answers.push({ word: spoken.word, ipa: spoken.ipa, hit, quiz: true });
    if (hit) {
      // 额外惩罚题答对只给正确性反馈；不放欢呼 / 纸屑，
      // 避免「撞石头造成干扰」反向变成小学生故意撞墙看纸屑的娱乐（team-lead 拍板 2）。
      audio.hit();
    } else {
      // 答错只保留减速与提示，不再把对手前推 300（避免额外题放大名次差）。
      player.slow = 1.4;
      audio.miss();
      state.banner = `错了 · 是 ${spoken.word}  /${spoken.ipa}/`;
    }
    state.bannerT = 1.45;
    // A1/A3：不再刷新 lastJudgeAt（那是分岔门时钟）；
    // 不再 shoveRival / 不再给 boost / 不再改 rival.odo：额外题不改变名次与速度。
    state.quiz = null;
    return { hit, spoken };
  }

  function checkWall(dt) {
    player.wallCd = Math.max(0, (player.wallCd || 0) - dt);
    if (state.quiz || player.wallCd > 0) return;
    if (Math.abs(player.lateral) < 0.97) return;
    player.lateral = Math.sign(player.lateral || 1) * 0.78;
    player.laneTarget = player.lateral;
    player.wallCd = 3;
    player.bumpCd = 3;
    state.shake = 8;
    audio.bump();
    openQuiz("wall");
  }

  function resolveContacts() {
    if (answering()) return;
    for (const rival of rivals) {
      let along = Math.abs(player.odo - rival.odo);
      along = Math.min(along, track.length - along);
      const dLat = player.lateral - rival.lateral;
      if (along >= COLLIDE.along || Math.abs(dLat) >= COLLIDE.lateral) continue;
      shoveRival(rival);
      if (player.bumpCd <= 0) {
        player.bumpCd = 8;
        player.boost = 0;
        player.turbo = 0;
        player.combo = 0;
        state.shake = 9;
        audio.bump();
        openQuiz("kart");
      }
    }
  }

  function answerBoard() {
    const rows = karts.map((k) => ({
      id: k.id,
      kind: k.kind,
      name: k.kind === "player" ? "You" : k.id.toUpperCase(),
      correct: k.correct || 0,
      // A1：排行榜只列分岔门答案，额外惩罚题独立统计、不混入此口径。
      answers: (k.answers || []).filter((a) => !a.quiz),
    }));
    rows.sort((a, b) => b.correct - a.correct || b.answers.length - a.answers.length);
    rows.forEach((r, i) => { r.rank = i + 1; });
    return rows;
  }

  function scanPickups() {
    const L = track.length;
    for (const item of state.pickups) {
      if (item.taken) continue;
      let odo = Math.floor(player.odo / L) * L + item.t * L;
      if (odo > player.odo + 90) odo -= L;
      if (Math.abs(player.odo - odo) > 78) continue;
      if (Math.abs(player.lateral - item.lateral) > 0.2) continue;
      item.taken = true;
      if (item.kind === "gem") {
        applyWalletDelta(1, 0);
        audio.hit();
      } else if ((player.air || 0) > 0.05) {
        // A5：成功跳过石头 = 纯规避。只点亮 1s 后轮彩带计时器（纯视觉），
        // 不给宝石 / 加速 / 连击 / 计分 / 名次 / 欢呼或纸屑。
        state.ribbonT = 1.0;
      } else if ((state.shields || 0) > 0) {
        applyWalletDelta(0, -1);
        state.banner = "护身卡抵消了这次撞击";
        state.bannerT = 1.2;
        audio.bump();
      } else {
        // A4：撞石头弹题；quiz 会冻结全车并把 slow 归零，故删掉
        // player.slow=Math.max(...,1.15) 这行死代码。
        state.shake = 6;
        audio.bump();
        openQuiz("rock");
      }
    }
  }

  function update(dt, input) {
    if (state.finished) {
      state.time += dt;
      state.bannerT = Math.max(0, state.bannerT - dt);
      state.shake = Math.max(0, state.shake - dt * 18);
      stepParticles(dt);
      return;
    }
    state.time += dt;
    state.bannerT = Math.max(0, state.bannerT - dt);
    state.shake = Math.max(0, state.shake - dt * 18);

    /* C 段：跨圈复位道具。门本身按 lap 生成了独立对象（buildGates），
       天然不会有「第 2 圈 gates 全部 judged」的问题，只需复位 pickups[].taken。 */
    const lapNow = Math.floor((player.odo - player.startOdo) / L);
    if (lapNow > state.lap && lapNow < state.laps) {
      state.lap = lapNow;
      state.pickups.forEach((it) => { it.taken = false; });
      state.banner = `第 ${lapNow + 1} 圈 · 宝石和石头都刷新啦`;
      state.bannerT = 2.2;
    }

    const prevOdo = player.odo;
    const picking = answering();
    if (input) {
      const left = input.left && !input.right;
      const right = input.right && !input.left;
      const lane = TUNING.laneLateral;
      if (left) player.laneTarget = picking ? -lane : -1;
      else if (right) player.laneTarget = picking ? lane : 1;
      else player.laneTarget = player.lateral;
    }
    const act = activeGate();
    beginDecide(act);
    if (state.decide && state.decide.phase === "hold") {
      state.decide.left -= dt;
      pressRivals();
      if (state.decide.left > 0) {
        stepParticles(dt);
        audio.engine(0, false);
        return;
      }
      state.decide.gate.holdDone = true;
      state.decide = null;
    }
    const holding = state.decide && state.decide.phase === "hold";
    if (input && input.jump && !holding) {
      const up = (player.air || 0) > 0.04;
      if (!up) {
        // A4：地面起跳只在完全落地（hop 已由 updateKart 清零）时允许，
        // 不再每帧重置 air，杜绝「air 归零后无限重置刷程」。二段跳玩法保留。
        if (!player.hop) {
          player.hop = 1;
          player.airMax = 0.5;
          player.air = 0.5;
        }
      } else if (player.hop === 1) {
        player.hop = 2;
        player.airMax = 0.74;
        player.air = 0.74;
        // A4：二段跳冲刺改为「140 里程预算 + 冷却」，由 updateKart 分摊推进，
        // 消除单帧 +=140 瞬移（V5）及与 blockSplitter 回滚的幽灵拾取。
        if ((player.jumpCd || 0) <= 0) {
          player.dashLeft = Math.max(player.dashLeft || 0, 140);
          player.jumpCd = 0.9;
        }
      }
    }
    updateKart(player, dt);
    // A4：先回滚到最终 odo，再扫描拾取，消除「先领后回滚」的幽灵拾取 / 幽灵碰撞。
    blockSplitter(prevOdo, input);
    scanPickups();
    if (state.decide && state.decide.phase === "reveal") {
      state.decide.arm -= dt;
      if (state.decide.arm <= 0) {
        state.decide.phase = "hold";
        state.decide.left = 3;
        player.boost = 0;
        player.turbo = 0;
      }
    }
    if (input && input.replay && act && act.gate.played && !act.gate.judged && !act.gate.replayed) {
      act.gate.replayed = true;
      player.combo = 0;
      audio.playWord(act.gate.spoken.word);
      state.banner = "再听一次 · 连击已断开";
      state.bannerT = 0.9;
    }

    for (const g of gates) {
      if (g.judged || g.unheard) continue;
      const waiting = state.decide && state.decide.gate === g;
      /* C 段：门线是绝对里程 g.line（buildGates 已按 lap 生成独立门对象）。
         旧写法 hasPassed(odo, commitT) 只看相对圈位置，两圈 commitT 相同会让
         第 2 圈的门在第 1 圈就被判掉 / 误标「未听到」，故一律改用 g.line。 */
      const passed = player.odo >= g.line;
      if (!g.played) {
        // A3 兜底：越过门线仍从未播放 → 显式标记「未听到」，不静默算 miss，
        // 结果页据此区分，不把没听过的词列成答错。
        if (passed && !waiting) g.unheard = true;
        continue;
      }
      if (waiting) continue;
      if (passed) judge(g);
    }

    for (const rival of rivals) {
      const upcoming = gates.find((g) => !rival.resolved[g.id]);
      if (upcoming) {
        /* C 段：rival 同样按绝对里程门线判定，弃用 wrapDelta / crossed 的相对圈坐标。 */
        const dist = upcoming.line - rival.odo;
        const eta = dist / Math.max(40, diff.speed);
        if (rival.choice[upcoming.id] == null && eta <= diff.fork) {
          const smart = Math.random() < rival.skill;
          rival.choice[upcoming.id] = smart ? upcoming.correctLateral : -upcoming.correctLateral;
        }
        if (answering()) rival.laneTarget = rival === rivals[0] ? -0.1 : 0.1;
        else rival.laneTarget = rival.home;
        const before = rival.odo;
        updateKart(rival, dt);
        if (!rival.resolved[upcoming.id] && before < upcoming.line && rival.odo >= upcoming.line) {
          rival.resolved[upcoming.id] = true;
          const ok = hitsLane(rival.lateral, upcoming.correctLateral, true);
          rival.answers.push({ word: upcoming.spoken.word, ipa: upcoming.spoken.ipa, hit: ok });
          if (ok) { rival.correct++; rival.boost = 0.75; }
          else rival.slow = 0.45;
          rival.laneTarget = rival.home;
        }
      } else if (!answering()) {
        rival.laneTarget = rival.home;
        updateKart(rival, dt);
      } else {
        rival.laneTarget = rival === rivals[0] ? -0.1 : 0.1;
        updateKart(rival, dt);
      }
    }
    checkWall(dt);
    resolveContacts();
    pressRivals();

    const traveled = player.odo - player.startOdo;
    if (traveled >= state.laps * track.length) {
      state.finished = true;
      state.finishTime = state.time;
      player.odo = player.startOdo + state.laps * track.length;
      player.t = startT;
      state.banner = "抵达终点";
      state.bannerT = 2;
      audio.fanfare();
      const s = track.sample(player.t);
      burst(offsetPoint(s, player.lateral * track.roadHalf), "#e0b44a", 40);
    }

    if (player.boost > 0 || player.turbo > 0) {
      const s = track.sample(player.t);
      const p = offsetPoint(s, player.lateral * track.roadHalf);
      state.particles.push({
        x: p.x - s.fx * 26, y: p.y - s.fy * 26,
        vx: -s.fx * 40 + (Math.random() - 0.5) * 30,
        vy: -s.fy * 40 + (Math.random() - 0.5) * 30,
        life: 0.25, age: 0,
        color: player.turbo > 0 ? "#f3e2ff" : "#ffd36a",
      });
    }
    stepParticles(dt);
    audio.engine(speedNow(player), player.boost > 0 || player.turbo > 0);
  }

  function stepParticles(dt) {
    // A5：1s 彩带淡出。quiz / 暂停等冻结态不调用 update，故此处自然不递减。
    if (state.ribbonT > 0) state.ribbonT = Math.max(0, state.ribbonT - dt);
    for (const p of state.particles) {
      p.age += dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
    }
    state.particles = state.particles.filter((p) => p.age < p.life);
    if (state.particles.length > 240) state.particles.splice(0, state.particles.length - 240);
  }

  function previewSteer(dt, input) {
    const left = input.left && !input.right;
    const right = input.right && !input.left;
    if (left) player.laneTarget = -1;
    else if (right) player.laneTarget = 1;
    else player.laneTarget = player.lateral;
    const step = diff.steer * dt;
    if (player.lateral < player.laneTarget) player.lateral = Math.min(player.laneTarget, player.lateral + step);
    else if (player.lateral > player.laneTarget) player.lateral = Math.max(player.laneTarget, player.lateral - step);
    player.lateral = Math.max(-1, Math.min(1, player.lateral));
    for (const rival of rivals) {
      const d = player.lateral - rival.lateral;
      if (Math.abs(d) < COLLIDE.lateral) {
        const sign = d >= 0 ? 1 : -1;
        player.lateral = Math.max(-1, Math.min(1, rival.lateral + sign * COLLIDE.lateral));
      }
    }
  }

  function launch(amount) {
    const n = Math.max(0, Math.min(1, amount || 0));
    state.nitro = 0;
    if (n < 0.02) return;
    const dash = Math.round(n * 1200);
    player.odo += dash;
    player.t = (player.odo / track.length) % 1;
    player.boost = 0.2 + n * 1.35;
    rivals.forEach((r) => { r.launchWait = 0.2 + n * 1.4; });
  }

  function rocket() {
    player.boost = Math.max(player.boost, ROCKET.time);
    audio.turbo();
  }

  function result() {
    const place = placeOf(player);
    const total = gates.length;
    // A1：correct / total 只读「分岔门命中数 / 门数」，额外惩罚题完全不参与。
    // A3：misses 只列已播放且已判定的门；未判门单独归入 unheard，不列成答错。
    const judged = gates.filter((g) => g.judged);
    const hits = judged.filter((g) => g.hit);
    const misses = judged.filter((g) => !g.hit);
    const unheard = gates.filter((g) => !g.judged);
    return {
      place,
      correct: state.gateHits,
      wrong: misses.length,
      total,
      time: state.finishTime,
      misses,
      hits,
      unheard,
      quizCorrect: state.quizCorrect,
      quizTotal: state.quizTotal,
    };
  }

  return {
    state,
    update,
    previewSteer,
    rocket,
    activeGate,
    placeOf,
    launch,
    branchLateral,
    finishQuiz,
    answerBoard,
    result,
    pointAt(t, lateral) {
      const s = track.sample(t);
      return offsetPoint(s, lateral * track.roadHalf);
    },
    dispose() { clearTimeout(missTimer); },
  };
}
