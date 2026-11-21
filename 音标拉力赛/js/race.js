import { BOOST, COLLIDE, QUIZ_TYPES, ROCKET, SLOW, TUNING, TURBO, forkSpan, hitsLane, pairKeyOf, pickQuizPair, poolOf, ROCK_QUOTA, ROCK_HITS_MAX, ROCK_HIT_BAND, ROCK_LAT_BAND, ROCK_MARGIN, NPC_MIN_SPEED_RATIO, PACE_MUL } from "./config.js?v=fwd-20261121";
import { offsetPoint } from "./track.js?v=fwd-20261121";

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
  /* IMPL-1A A6：错峰起跑里程，两车各错开 ±Δ（> COLLIDE.along=130 碰撞带），
     一前一后 + 横向 a 左 / b 右，杜绝三车同里程扎堆与开局贴身连环碰撞。 */
  const rivals = [
    mk("a", "A", "rival", startT - 0.022, 0.28, -0.55),
    mk("b", "B", "rival", startT + 0.020, 0.42, 0.55),
  ];
  /* 软跟随目标里程差（相对 player.odo），只用速度倍率渐进收敛、不改 odo。 */
  rivals[0].gapTarget = -0.022 * L;
  rivals[1].gapTarget = 0.020 * L;
  /* 任务4：NPC 拟人——每局给两车固定的反应延迟系数与个体相位，使"听见词→决定选边"
     的时机像真人快慢不同（0.62~1.12×diff.fork），且走线相位两车错开、不可预测。 */
  rivals.forEach((r, i) => {
    r.reactK = 0.62 + Math.random() * 0.5;   // 选边反应快慢
    r.weavePhase = i === 0 ? 0 : 2.3;         // 走线个体相位差
  });
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
    /* IMPL-1A：撞石硬上限（整局累计、跨圈不复位）/ 欢呼全局递增序号。
       rockHits 达 rockBudget 后静默越过，不再 openQuiz("rock")、不再计 quizReasons.rock。 */
    rockHits: 0,
    rockBudget: ROCK_HITS_MAX,
    cheerSeq: 0,
    /* 选道即判：每次判门（含过门线兜底）递增，供表现层按 seq 去重重播 RIGHT/WRONG。 */
    verdictSeq: 0,
    verdict: null,
    /* FWD 纯统计（只读展示）：整局累计、跨圈不复位；不参与任何判定 / 计分 / 名次 / 速度。 */
    firstListen: 0,
    cleanChain: 0,
    cleanChainBest: 0,
    rockCleared: 0,
    rockSeen: 0,
    rockSinceGate: 0,
    rescue: 0,
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
    /* IMPL-1A A1：按 g.line 绝对里程排除真实分叉窗口
       [g.line - span*L - margin, g.line + merge*L + margin]，不再用旧的相对 commitT ±0.04L。
       门线 g.line = startOdo + (lap + commitT)*L（:83）；pickups 的 t 每圈复用
       （跨圈仅复位 taken，:614），故把每个门窗口按 lap 折叠回第一圈基准再判定，
       两圈的分叉「张开→选择→闭合」窗口都与石头互斥（hold 冻结不再吞跳 / 触屏手势不打架）。 */
    const blocked = (t) => {
      if (Math.min(Math.abs(t - startT), 1 - Math.abs(t - startT)) < 0.04) return true;
      const odo = player.startOdo + t * L;
      return gates.some((g) => {
        const line0 = g.line - (g.lap || 0) * L; // = startOdo + commitT*L，与 odo 同基准
        return odo >= line0 - span * L - ROCK_MARGIN && odo <= line0 + merge * L + ROCK_MARGIN;
      });
    };
    const settle = (t) => {
      let mark = t;
      for (let n = 0; n < 12 && blocked(mark); n++) mark += 0.012;
      if (mark > 0.94) mark = 0.9;
      return mark;
    };
    const jitter = () => (Math.random() - 0.5) * 0.1;
    /* IMPL-1A A1：整局石头总数 = ROCK_QUOTA(2)，取代「每圈 8 颗 × 2 圈 = 16 颗」。
       两颗基准里程落在单车道直道段，settle() 兜底避让分叉窗口。
       armed / cleared 是滞空见证式（scanPickups）的单调累积字段，出窗/落地才定案。 */
    const rockBases = [0.4, 0.82];
    for (let i = 0; i < ROCK_QUOTA; i++) {
      const t = settle(rockBases[i % rockBases.length] + (Math.random() - 0.5) * 0.012);
      items.push({
        id: `rock-${i}`,
        kind: "rock",
        t,
        lateral: Math.max(-0.66, Math.min(0.66, lanes[i % 3] + jitter())),
        taken: false,
        armed: false,
        cleared: false,
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
    /* IMPL-1A A6：微速差 + 缓慢正弦起伏（非恒定倍率），两车相位错开，
       避免长期同速贴固定相对位置。区间约 0.96–1.06；
       判定层 DIFFICULTY.speed 260/300 逐字不动（方案 B）。 */
    const phase = kart.id === "a" ? 0 : 1.7;
    const wobble = 0.035 * Math.sin(state.time * 0.6 + phase);
    return (kart.id === "a" ? 1.015 : 0.995) + wobble;
  }

  function speedNow(kart) {
    let mul = baseMul(kart);
    if (kart.turbo > 0) mul *= TURBO.mul;
    else if (kart.boost > 0) mul *= kart.kind === "player" ? BOOST.mul : 1.12;
    if (kart.slow > 0) mul *= SLOW.mul;
    /* speedNow 保持"相对速度查询"语义：不乘 PACE_MUL。
       提速只在实际推进 base（updateKart 的 diff.speed * PACE_MUL）生效；
       floor = 0.94·speedNow(player)/diff.speed 依赖此式=0.94·mul_player，
       探针同源复算与之逐字一致，不得把节奏乘数混进来破坏 NPC 下限判据。 */
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
    /* IMPL-1A A5：全局递增 seq，判门命中与成功跳石共用同一计数器。
       表现层（IMPL-1B）按 seq 去重而非按 word，保证同词连续触发仍重播。 */
    state.cheerSeq += 1;
    state.cheer = { word, seq: state.cheerSeq, until: state.time + 3.4 };
    state.banner = `${word} · 对了`;
    state.bannerT = 3.4;
  }

  /* 选道即判：sideOverride 为玩家所选方向（±1），命中只取选择符号，不再等车身开过门线。
     过门线兜底（玩家全程未选）不传参，仍按 player.lateral 判，口径逐字保留。 */
  function judge(gate, sideOverride) {
    gate.judged = true;
    const hit = hitsLane(sideOverride != null ? sideOverride : player.lateral, gate.correctLateral);
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
      /* IMPL-1A A6：删除「硬压到玩家后方固定负里程」（扎堆 / 贴固定相对位置根源）。
         改为软跟随：只在领先超过上限时轻收，防止 odo 拉开近一整圈导致 wrap 误碰撞。 */
      const leadCap = 0.12 * L;
      rivals.forEach((r, i) => {
        if (r.odo > player.odo + leadCap + i * 60) {
          r.odo = player.odo + leadCap + i * 60;
          r.t = ((r.odo % track.length) + track.length) % track.length / track.length;
        }
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
    /* FWD 纯统计：一次听准 = 命中 ∧ 未重听；连听遇错 / 重听 / 本门间撞石即断。
       放在判定分支之后，逐字不改上方任何判定数值与 cheer / openQuiz 触发链。 */
    if (hit && !gate.replayed) {
      state.firstListen += 1;
      state.cleanChain = state.rockSinceGate === 0 ? state.cleanChain + 1 : 0;
    } else {
      state.cleanChain = 0;
    }
    state.rockSinceGate = 0;
    state.cleanChainBest = Math.max(state.cleanChainBest, state.cleanChain);
    /* 任务2：即时结果供表现层按 seq 去重重播（绿勾RIGHT / 红叉WRONG），与 banner 文字并存。
       until 用 race 时钟；hold 冻结期 race.state.time 仍推进，故展示窗口会自然到期。 */
    state.verdictSeq += 1;
    state.verdict = {
      hit, seq: state.verdictSeq,
      word: gate.spoken.word, ipa: gate.spoken.ipa,
      until: state.time + 1.15,
    };
  }

  function updateKart(kart, dt) {
    let mul = baseMul(kart);
    if (kart.turbo > 0) mul *= TURBO.mul;
    else if (kart.boost > 0) mul *= kart.kind === "player" ? BOOST.mul : 1.12;
    if (kart.kind !== "player" && kart.startBoost > 0) mul *= 1.45;
    if (kart.slow > 0) mul *= SLOW.mul;
    if (kart.kind !== "player") {
      /* IMPL-1A A6：软跟随。删除了 pressRivals 的 odo 硬拉回，改用「速度倍率微调」
         把 rival 锚定在 gapTarget（±约 400 unit，> COLLIDE.along=130 碰撞带）附近：
         只调 mul、绝不改 odo，故 odo 单调推进、零瞬移、零冻结，也不会连环 kart 碰撞。 */
      const err = (kart.odo - player.odo) - (kart.gapTarget || 0);
      const corr = Math.max(-0.05, Math.min(0.05, -err / (0.04 * track.length)));
      mul *= 1 + corr;
      const gap = (kart.odo - player.odo) / track.length;
      if (gap > 0.12) mul *= 0.94;
      /* 任务4：偶尔犹豫——低频噪声短时微调速度倍率（±2.5%、两车相位不同）。
         放在 floor 兜底之前，确保 NPC_MIN_SPEED_RATIO 下限不被破坏；软跟随 / collide 全保留。 */
      const hesitate = 0.025 * Math.sin(state.time * 0.37 + (kart.weavePhase || 0) + 0.6);
      mul *= 1 + hesitate;
      /* A6 速度下限 v_i >= 0.94 · v_player_now（team-lead 终裁）。
         玩家本帧有效 mul = speedNow(player)/diff.speed，与玩家同源；放在所有降速之后，
         保证 gap 降速 / 软跟随 / startBoost 衰减 / rival.slow 都不会把对手压成龟速。 */
      const floor = NPC_MIN_SPEED_RATIO * (speedNow(player) / diff.speed);
      if (mul < floor) mul = floor;
    }
    /* 任务5：base 与 speedNow 同源乘 PACE_MUL，玩家/rival 推进速度一致放大。 */
    const base = diff.speed * PACE_MUL;
    kart.boost = Math.max(0, kart.boost - dt);
    kart.slow = Math.max(0, kart.slow - dt);
    kart.turbo = Math.max(0, kart.turbo - dt);
    kart.bumpCd = Math.max(0, kart.bumpCd - dt);
    kart.startBoost = Math.max(0, kart.startBoost - dt);
    kart.launchWait = Math.max(0, kart.launchWait - dt);
    if (kart.kind === "player") {
      /* IMPL-1A：删 hopWindow 死字段（全项目零赋值零读取）与 jumpCd 冷却；
         air 逐帧 -dt，落地（air 归零）才复位 hop。 */
      kart.air = Math.max(0, (kart.air || 0) - dt);
      if (kart.air === 0) kart.hop = 0;
    }
    const waiting = kart.launchWait > 0;
    /* IMPL-1A A3：删 dashLeft 二段跳冲刺的额外 odo 分摊；
       odo 只按 base*mul*dt 单调推进，跳跃只改垂直 air、不动水平速度。 */
    if ((!state.finished || kart.kind !== "player") && !waiting) kart.odo += base * mul * dt;
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

  /* 任务4：NPC 拟人走线。三频叠加——低频大漂移(0.12) + 中频修正(0.08) + 个体微摆(0.05)，
     幅度合计 ≤0.25、两车相位错开，轨迹非周期、不可预测但仍平滑；base 基准车道不变。
     临近门且已选边时朝所选侧靠，选边阈值带个体 reactK 抖动（真人反应快慢不同）。
     只产出 laneTarget，lateral 一律由 updateKart 逐帧按 rate*dt 收敛（零瞬切）。 */
  function npcLaneTarget(rival, idx, upcoming) {
    const base = idx === 0 ? -0.42 : 0.42;
    const p = rival.weavePhase != null ? rival.weavePhase : idx * 2.3;
    const phase = state.time;
    const weave = 0.12 * Math.sin(phase * 0.23 + p)
      + 0.08 * Math.sin(phase * 0.61 + p * 1.6 + 1.1)
      + 0.05 * Math.sin(phase * 1.17 + p * 2.4);
    let target = base + weave;
    if (upcoming && rival.choice[upcoming.id] != null) {
      const eta = (upcoming.line - rival.odo) / Math.max(40, diff.speed);
      if (eta <= diff.fork * (rival.reactK || 1)) target = rival.choice[upcoming.id];
    }
    return Math.max(-0.9, Math.min(0.9, target));
  }

  function pressRivals() {
    if (!answering()) return;
    /* IMPL-1A A6：删除「r.odo>behind → r.odo=behind」硬拉回到固定负里程
       与「r.lateral=±0.1」瞬切同侧（扎堆 / 龟速 / 贴固定相对位置根源）。
       改为：仅在领先接近 wrap 误判区时软收 + 各自 laneTarget（错峰换道）。 */
    const leadCap = 0.12 * L;
    rivals.forEach((r, i) => {
      if (r.odo > player.odo + leadCap + i * 60) {
        r.odo = player.odo + leadCap + i * 60;
        r.t = ((r.odo % track.length) + track.length) % track.length / track.length;
      }
      r.laneTarget = npcLaneTarget(r, i, gates.find((g) => !r.resolved[g.id]));
    });
  }

  function shoveRival(rival) {
    const side = rival.lateral >= player.lateral ? 1 : -1;
    let lat = player.lateral + side * 0.82;
    if (Math.abs(lat) > 0.9) lat = player.lateral - side * 0.82;
    /* IMPL-1A A6：保留碰撞横向推离，但删除 rival.odo=player.odo-240 的瞬时里程回拉
       （瞬移 / 名次失真）；home 不再被瞬切覆盖，后续由走线逻辑自然回归。 */
    rival.lateral = Math.max(-0.88, Math.min(0.88, lat));
    rival.laneTarget = rival.lateral;
    rival.drift = 0;
  }

  function beginDecide(act) {
    if (state.decide || state.quiz || !act) return;
    if (act.gate.judged || act.gate.unheard || act.gate.holdDone) return;
    const dist = act.gate.line - player.odo;
    /* 任务C：lead 放宽到与卡片 S1 预告窗口（main.js previewDistance）严格同式——
       span·L + 0.5·preview·speed，用 diff.speed 不含 PACE_MUL，两窗口对齐。
       这样卡片一出现即建立 decide、播音、可选、可判，选道即判链立即生效。 */
    const lead = span * L + 0.5 * diff.preview * diff.speed;
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
    /* 任务1：hold 展示窗口 3s→1.2s；选道即判后还会 min(left,0.9) 进一步缩短。 */
    state.decide = { gate: act.gate, phase: "reveal", arm: 0.55, left: 1.2, picked: null };
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
    /* FWD 纯统计：救援题答对续链 +1（断链时不复活），不碰 combo / 名次 / 速度。 */
    if (hit) {
      state.rescue += 1;
      if (state.cleanChain > 0) {
        state.cleanChain += 1;
        state.cleanChainBest = Math.max(state.cleanChainBest, state.cleanChain);
      }
    }
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

  /* IMPL-1A A4/A5：石头定案。cleared → 恰好一次欢呼（词表不变、seq 全局递增）
     + 1s 后轮彩带；撞击 → 计数并封顶，rockHits 达 rockBudget 后静默越过
     （不 shake / 不 bump / 不 openQuiz，故不进 quizReasons.rock）。 */
  function settleRock(item) {
    /* FWD C-12：唯一计数落点，与「定案事件」1:1；cleared / 封顶 / 撞击三路径全覆盖。 */
    state.rockSeen += 1;
    if (item.cleared) state.rockCleared += 1;
    if (item.cleared) {
      state.ribbonT = 1.0;
      cheer(1);
      return;
    }
    if (state.rockHits >= state.rockBudget) return;
    state.rockHits += 1;
    state.rockSinceGate += 1;   // FWD 纯统计：本门与下一门之间撞过石 → 连听断开
    if ((state.shields || 0) > 0) {
      applyWalletDelta(0, -1);
      state.banner = "护身卡抵消了这次撞击";
      state.bannerT = 1.2;
      audio.bump();
    } else {
      state.shake = 6;
      audio.bump();
      openQuiz("rock");
    }
  }

  function scanPickups() {
    const L = track.length;
    for (const item of state.pickups) {
      if (item.taken) continue;
      /* :570-571 的 odo 换算逐字保留：把「前方 >90 unit」的石头折算到后方，
         使 d 在 [-78,+78] 窗口内连续、无 wrap 跳变。定案不得用单向 d>78 判越过。 */
      let odo = Math.floor(player.odo / L) * L + item.t * L;
      if (odo > player.odo + 90) odo -= L;
      const d = player.odo - odo;
      const inBand = Math.abs(d) <= ROCK_HIT_BAND;
      const sameLane = Math.abs(player.lateral - item.lateral) <= ROCK_LAT_BAND;
      if (item.kind === "gem") {
        // gem 即时拾取语义逐字不变
        if (!inBand || !sameLane) continue;
        item.taken = true;
        applyWalletDelta(1, 0);
        audio.hit();
        continue;
      }
      /* IMPL-1A A2：滞空见证式。进过同车道窗口即 armed，窗内任一帧 air>0 即 cleared；
         出窗 / 落地 / 已见证时定案一次。armed/cleared 单调累积、不因 blockSplitter
         回滚清除，item.taken 一旦 true 幂等不再处理。air>0.05 → air>0 放宽。 */
      if (inBand && sameLane) {
        item.armed = true;
        if ((player.air || 0) > 0) item.cleared = true;
      }
      const settle = item.armed && (item.cleared || (player.air || 0) === 0 || !inBand);
      if (settle) {
        item.taken = true;
        settleRock(item);
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
      /* IMPL-1A：滞空见证字段随 taken 一起复位，避免第 2 圈沿用上一圈的
         armed/cleared 残留导致错误定案；rockHits 是整局累计，跨圈不复位。 */
      state.pickups.forEach((it) => { it.taken = false; it.armed = false; it.cleared = false; });
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
      /* 任务1 选道即判：decide 可选阶段第一次按左/右即按「选择方向」判，不等车开过门线。
         picked 记录所选方向，天然只判一次；judge 内 gate.judged=true，过门线循环的
         `if (g.judged) continue` 不会再判。玩家全程不按则维持原 reveal→hold→过门线兜底。 */
      if (state.decide && state.decide.picked == null && (left || right)) {
        const pickedGate = state.decide.gate;
        if (!pickedGate.judged && !pickedGate.unheard) {
          const side = left ? -1 : 1;
          state.decide.picked = side;
          judge(pickedGate, side);
          /* 判定后只保留很短的展示窗口（≤0.9s），随后放行，不再冻结到 3 秒。 */
          state.decide.phase = "hold";
          state.decide.left = Math.min(state.decide.left, 0.9);
        }
      }
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
    /* IMPL-1A：只做「单跳必过」，取消二段跳 —— 不做 260ms 状态机、不做 input.jump2、
       不做双击加高、不做两级 lift、不做 hop===2 追加抬升。单次 jump 边沿起跳一次；
       滞空期间（air>0，hop 尚未由 updateKart 落地复位）再次按被 !player.hop 挡住，
       故双击无额外效果。airMax 保持 0.5s（E1 选项甲，不延 airMax）。 */
    if (input && input.jump && !holding && (player.air || 0) <= 0 && !player.hop) {
      player.hop = 1;
      player.airMax = 0.5;
      player.air = 0.5;
    }
    updateKart(player, dt);
    // A4：先回滚到最终 odo，再扫描拾取，消除「先领后回滚」的幽灵拾取 / 幽灵碰撞。
    blockSplitter(prevOdo, input);
    scanPickups();
    if (state.decide && state.decide.phase === "reveal") {
      state.decide.arm -= dt;
      if (state.decide.arm <= 0) {
        state.decide.phase = "hold";
        state.decide.left = 1.2;   // 任务1：3s→1.2s，未选兜底也不再长时间冻结
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
      const idx = rival === rivals[0] ? 0 : 1;
      const upcoming = gates.find((g) => !rival.resolved[g.id]);
      if (upcoming) {
        /* C 段：rival 同样按绝对里程门线判定，弃用 wrapDelta / crossed 的相对圈坐标。 */
        const dist = upcoming.line - rival.odo;
        const eta = dist / Math.max(40, diff.speed);
        /* 任务4：选边时机带个体 reactK 抖动——不同 rival 在 eta<=fork*reactK 时才决定，
           像真人反应快慢不同（0.62~1.12×）。不改 smart 概率与判定口径。 */
        if (rival.choice[upcoming.id] == null && eta <= diff.fork * (rival.reactK || 1)) {
          const smart = Math.random() < rival.skill;
          rival.choice[upcoming.id] = smart ? upcoming.correctLateral : -upcoming.correctLateral;
        }
      }
      /* IMPL-1A A6：不再 answering() 期强设同侧 ±0.1 / 非 answering 固定 home；
         统一走 npcLaneTarget（各自基准 + 换道 + 临门选边），lateral 由 updateKart
         逐帧按 rate*dt 收敛，零瞬切、不长期贴固定相对位置。 */
      rival.laneTarget = npcLaneTarget(rival, idx, upcoming);
      const before = rival.odo;
      updateKart(rival, dt);
      if (upcoming && !rival.resolved[upcoming.id] && before < upcoming.line && rival.odo >= upcoming.line) {
        rival.resolved[upcoming.id] = true;
        const ok = hitsLane(rival.lateral, upcoming.correctLateral, true);
        rival.answers.push({ word: upcoming.spoken.word, ipa: upcoming.spoken.ipa, hit: ok });
        if (ok) { rival.correct++; rival.boost = 0.75; }
        else rival.slow = 0.45;
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
      /* FWD 纯统计：仅供展示 / 埋点交叉校验，不进 acc / stars / place / 速度 / combo。 */
      firstListen: state.firstListen,
      cleanChain: state.cleanChainBest,
      rescue: state.rescue,
      rockCleared: state.rockCleared,
      rockSeen: state.rockSeen,
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
