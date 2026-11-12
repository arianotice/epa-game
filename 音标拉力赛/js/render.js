import { offsetPoint } from "./track.js?v=hud-20261108";

const paperCache = { c: null, w: 0, h: 0 };

function paper(w, h) {
  if (paperCache.c && paperCache.w === w && paperCache.h === h) return paperCache.c;
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const g = c.getContext("2d");
  g.fillStyle = "#e7d3a8";
  g.fillRect(0, 0, w, h);
  const grd = g.createRadialGradient(w * 0.2, h * 0.1, 40, w * 0.5, h * 0.5, w * 0.7);
  grd.addColorStop(0, "rgba(255,250,235,.65)");
  grd.addColorStop(1, "rgba(196,164,106,.25)");
  g.fillStyle = grd;
  g.fillRect(0, 0, w, h);
  g.strokeStyle = "rgba(120,80,30,.045)";
  for (let i = 0; i < 1400; i++) {
    g.beginPath();
    const x = Math.random() * w;
    const y = Math.random() * h;
    g.moveTo(x, y);
    g.lineTo(x + Math.random() * 36 - 18, y + Math.random() * 8 - 4);
    g.stroke();
  }
  paperCache.c = c;
  paperCache.w = w;
  paperCache.h = h;
  return c;
}

function mix(hex, amount) {
  const n = parseInt(hex.slice(1), 16);
  const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255;
  const t = amount;
  const rr = Math.round(107 + (r - 107) * t);
  const gg = Math.round(74 + (g - 74) * t);
  const bb = Math.round(50 + (b - 50) * t);
  return `rgb(${rr},${gg},${bb})`;
}

function flareAt(t, gates, span, merge) {
  let best = 0;
  let gate = null;
  for (const g of gates) {
    const start = g.commitT - span;
    const full = g.commitT - span * 0.42;
    const end = g.commitT + merge;
    let f = 0;
    if (t >= start && t < full) f = (t - start) / (full - start);
    else if (t >= full && t <= g.commitT) f = 1;
    else if (t > g.commitT && t <= end) f = 1 - (t - g.commitT) / merge;
    if (f > best) { best = f; gate = g; }
  }
  return { flare: Math.max(0, Math.min(1, best)), gate };
}

function edges(sample, flare, laneLateral, H) {
  const laneHalf = H * 0.72;
  const island = H * 0.28 * flare;
  const center = laneLateral * H;
  const lerp = (a, b) => a + (b - a) * flare;
  const leftOuter = lerp(-H, -center - laneHalf);
  const leftInner = lerp(-2, -island);
  const rightInner = lerp(2, island);
  const rightOuter = lerp(H, center + laneHalf);
  return {
    ll: offsetPoint(sample, leftOuter),
    lr: offsetPoint(sample, leftInner),
    rl: offsetPoint(sample, rightInner),
    rr: offsetPoint(sample, rightOuter),
    flare,
  };
}

function quad(ctx, a, b, c, d) {
  ctx.beginPath();
  ctx.moveTo(a.x, a.y);
  ctx.lineTo(b.x, b.y);
  ctx.lineTo(c.x, c.y);
  ctx.lineTo(d.x, d.y);
  ctx.closePath();
  ctx.fill();
}

function drawKart(ctx, s, lateral, H, style, time, boosting, yaw, ribbon) {
  const p = offsetPoint(s, lateral * H);
  ctx.save();
  ctx.translate(p.x, p.y);
  ctx.rotate(typeof yaw === "number" ? yaw : Math.atan2(s.fy, s.fx));
  ctx.scale(1.7, 1.7);
  ctx.fillStyle = "rgba(40,28,12,.3)";
  ctx.beginPath();
  ctx.ellipse(6, 16, 46, 18, 0, 0, Math.PI * 2);
  ctx.fill();
  const max = style.airMax || 0.5;
  const peak = (style.hop || 1) >= 2 ? 78 : 46;
  const hop = style.air > 0 ? Math.sin(Math.min(1, style.air / max) * Math.PI) * peak : 0;
  if (hop) ctx.translate(hop, 0);
  const spin = time * 16;
  for (const [wx, wy] of [[-24, 30], [-24, -30], [34, 28], [34, -28]]) {
    ctx.save();
    ctx.translate(wx, wy);
    ctx.fillStyle = "#120e0b";
    ctx.beginPath();
    ctx.ellipse(0, 5, 12, 18, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "#2a221b";
    ctx.beginPath();
    ctx.ellipse(0, 0, 12, 18, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = style.trim;
    ctx.beginPath();
    ctx.ellipse(0, 0, 5, 8, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = "#efe6d2";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, 0);
    ctx.lineTo(Math.sin(spin) * 4, Math.cos(spin) * 7);
    ctx.stroke();
    ctx.restore();
  }
  if (boosting) {
    const flame = 16 + Math.random() * 14;
    ctx.fillStyle = style.turbo ? "rgba(214,186,255,.95)" : "rgba(255,176,64,.95)";
    ctx.beginPath();
    ctx.moveTo(-34, -8);
    ctx.lineTo(-34 - flame, 0);
    ctx.lineTo(-34, 8);
    ctx.fill();
  }
  ctx.fillStyle = style.trim;
  roundRect(ctx, -6, -26, 40, 12, 5);
  ctx.fill();
  roundRect(ctx, -6, 14, 40, 12, 5);
  ctx.fill();
  ctx.fillStyle = style.body;
  roundRect(ctx, -36, -18, 78, 36, 12);
  ctx.fill();
  ctx.strokeStyle = style.trim;
  ctx.lineWidth = 3;
  ctx.stroke();
  gloss(ctx, style.bodyShine || 0, time, -36, -18, 78, 36);
  ctx.beginPath();
  ctx.moveTo(42, -12);
  ctx.lineTo(68, 0);
  ctx.lineTo(42, 12);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.fillStyle = "#241c16";
  roundRect(ctx, -4, -10, 20, 20, 5);
  ctx.fill();
  ctx.fillStyle = style.trim;
  ctx.fillRect(-42, -24, 10, 48);
  ctx.fillRect(-40, -28, 16, 6);
  ctx.fillRect(-40, 22, 16, 6);
  gloss(ctx, style.trimShine || 0, time, -42, -28, 18, 56);
  ctx.fillStyle = "#f6ead0";
  roundRect(ctx, 24, -8, 16, 16, 3);
  ctx.fill();
  // A5：成功躲避石头后的 1s 后轮彩带（纯视觉反馈，不触碰任何数值 / 奖励）。
  if (ribbon > 0) drawRibbon(ctx, ribbon);
  ctx.restore();
}

// A5：后轮胎周围的轻量彩带 / 纸屑，1s 内线性淡出。只消费传入的计时器，
// 不读也不写 gems / boost / combo / correct / place / confetti 等任何游戏状态。
function drawRibbon(ctx, t) {
  const a = Math.max(0, Math.min(1, t));
  const colors = ["#e0b44a", "#1f618d", "#b03a2e", "#1e7a4f", "#6c3483", "#fffaf0"];
  const spread = (1 - a) * 26;
  ctx.save();
  ctx.globalAlpha = a * 0.9;
  for (let i = 0; i < 12; i++) {
    const side = i % 2 === 0 ? -1 : 1;
    const k = (i % 6) / 6;
    const x = -24 - spread * (0.35 + k) - (i % 3) * 2;
    const y = side * (30 + spread * (0.25 + k * 0.6));
    ctx.fillStyle = colors[i % colors.length];
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(i * 1.31 + (1 - a) * 2.4);
    ctx.fillRect(-6, -1.8, 12, 3.6);
    ctx.restore();
  }
  ctx.restore();
}

function gloss(ctx, shine, time, x, y, w, h) {
  if (!shine) return;
  ctx.save();
  const pulse = 0.5 + 0.5 * Math.sin(time * (shine >= 2 ? 7 : 3.2));
  ctx.globalAlpha = shine >= 2 ? 0.28 + 0.42 * pulse : 0.1 + 0.2 * pulse;
  ctx.fillStyle = "#fffaf0";
  roundRect(ctx, x, y, w, h, 8);
  ctx.fill();
  if (shine >= 2) {
    const sweep = ((time * 56) % (w + 28)) - 14;
    ctx.globalAlpha = 0.75;
    ctx.fillRect(x + sweep, y, 10, h);
  }
  ctx.restore();
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

export function render(ctx, view) {
  const { w, h, dpr, track, gates, span, merge, karts, time, camera, shake, reduced } = view;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);
  ctx.drawImage(paper(w, h), 0, 0, w, h);

  const forkW = track.roadHalf * 2.7;
  const zoom = Math.max(0.2, Math.min((w * 0.64) / forkW, (h * 0.86) / (track.roadHalf * 3.4), 0.9));
  const heading = camera.h;
  const anchor = view.anchor || 0.62;
  ctx.save();
  ctx.translate(w / 2 + (reduced ? 0 : (Math.random() - 0.5) * shake), h * anchor + (reduced ? 0 : (Math.random() - 0.5) * shake));
  ctx.rotate(-heading - Math.PI / 2);
  ctx.scale(zoom, zoom);
  ctx.translate(-camera.x, -camera.y);
  const matrix = ctx.getTransform();

  const H = track.roadHalf;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.beginPath();
  track.samples.forEach((s, i) => (i ? ctx.lineTo(s.x, s.y) : ctx.moveTo(s.x, s.y)));
  ctx.closePath();
  ctx.strokeStyle = "#8d9a68";
  ctx.lineWidth = H * 2.55;
  ctx.stroke();
  ctx.strokeStyle = "#d9c79a";
  ctx.lineWidth = H * 2.15;
  ctx.stroke();
  ctx.strokeStyle = "#e0b44a";
  ctx.lineWidth = H * 2 + 22;
  ctx.stroke();

  const samples = track.samples;
  for (let i = 0; i < samples.length; i++) {
    const a = samples[i];
    const b = samples[(i + 1) % samples.length];
    const fa = flareAt(a.t, gates, span, merge);
    const fb = flareAt(b.t, gates, span, merge);
    const ea = edges(a, fa.flare, view.laneLateral, H);
    const eb = edges(b, fb.flare, view.laneLateral, H);
    const gate = fa.gate || fb.gate;
    const flare = Math.max(fa.flare, fb.flare);
    const leftColor = gate ? mix(gate.left.color, 0.72 * flare) : "#6b4a32";
    const rightColor = gate ? mix(gate.right.color, 0.72 * flare) : "#6b4a32";
    ctx.fillStyle = flare < 0.12 ? "#6b4a32" : leftColor;
    quad(ctx, ea.ll, ea.lr, eb.lr, eb.ll);
    ctx.fillStyle = flare < 0.12 ? "#6b4a32" : rightColor;
    quad(ctx, ea.rl, ea.rr, eb.rr, eb.rl);
    if (flare > 0.08) {
      const liftA = { x: ea.lr.x - a.fx * 14 + a.rx * 8, y: ea.lr.y - a.fy * 14 + a.ry * 8 };
      const liftB = { x: eb.lr.x - b.fx * 14 + b.rx * 8, y: eb.lr.y - b.fy * 14 + b.ry * 8 };
      const liftC = { x: eb.rl.x - b.fx * 14 + b.rx * 8, y: eb.rl.y - b.fy * 14 + b.ry * 8 };
      const liftD = { x: ea.rl.x - a.fx * 14 + a.rx * 8, y: ea.rl.y - a.fy * 14 + a.ry * 8 };
      ctx.fillStyle = "rgba(90,60,24,.35)";
      quad(ctx, ea.lr, ea.rl, eb.rl, eb.lr);
      ctx.fillStyle = "#e7d3a4";
      quad(ctx, liftA, liftD, liftC, liftB);
      ctx.fillStyle = "#c4a15a";
      quad(ctx, ea.lr, liftA, liftB, eb.lr);
      if (flare > 0.45 && i % 7 === 0) {
        const mid = {
          x: (liftA.x + liftD.x) * 0.5 + a.fx * 18,
          y: (liftA.y + liftD.y) * 0.5 + a.fy * 18,
        };
        ctx.fillStyle = "#fff8e8";
        ctx.beginPath();
        ctx.moveTo(mid.x + a.fx * 26, mid.y + a.fy * 26);
        ctx.lineTo(mid.x - a.fx * 16 + a.rx * 18, mid.y - a.fy * 16 + a.ry * 18);
        ctx.lineTo(mid.x - a.fx * 16 - a.rx * 18, mid.y - a.fy * 16 - a.ry * 18);
        ctx.closePath();
        ctx.fill();
      }
    }
  }

  ctx.setLineDash([22, 18]);
  ctx.beginPath();
  let pen = false;
  for (const s of samples) {
    const f = gates.length ? flareAt(s.t, gates, span, merge).flare : 0;
    const p = offsetPoint(s, 0);
    if (f > 0.25) { pen = false; continue; }
    if (!pen) { ctx.moveTo(p.x, p.y); pen = true; }
    else ctx.lineTo(p.x, p.y);
  }
  ctx.strokeStyle = "rgba(246,234,208,.55)";
  ctx.lineWidth = 4;
  ctx.stroke();
  ctx.setLineDash([]);

  for (const g of gates) {
    const s = track.sample(g.commitT);
    const f = flareAt(g.commitT, gates, span, merge).flare;
    if (f < 0.4) continue;
    const edge = edges(s, 1, view.laneLateral, H);
    ctx.lineWidth = 8;
    ctx.strokeStyle = g.left.color;
    ctx.beginPath();
    ctx.moveTo(edge.ll.x, edge.ll.y);
    ctx.lineTo(edge.lr.x, edge.lr.y);
    ctx.stroke();
    ctx.strokeStyle = g.right.color;
    ctx.beginPath();
    ctx.moveTo(edge.rl.x, edge.rl.y);
    ctx.lineTo(edge.rr.x, edge.rr.y);
    ctx.stroke();
  }

  const finish = track.sample(0.012);
  ctx.fillStyle = "#f6ead0";
  ctx.strokeStyle = "#a0720a";
  ctx.lineWidth = 6;
  ctx.beginPath();
  const fl = offsetPoint(finish, -H);
  const fr = offsetPoint(finish, H);
  ctx.moveTo(fl.x, fl.y);
  ctx.lineTo(fr.x, fr.y);
  ctx.stroke();

  for (const p of view.particles) {
    const k = 1 - p.age / p.life;
    ctx.globalAlpha = Math.max(0, k);
    ctx.fillStyle = p.color;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 6 * k + 2, 0, Math.PI * 2);
    ctx.fill();
    ctx.globalAlpha = 1;
  }

  for (const item of view.pickups || []) {
    if (item.taken) continue;
    const s = track.sample(item.t);
    const p = offsetPoint(s, item.lateral * H);
    ctx.save();
    ctx.translate(p.x, p.y);
    if (item.kind === "gem") {
      ctx.fillStyle = "#7fd4ff";
      ctx.strokeStyle = "#1d6f99";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(0, -18);
      ctx.lineTo(14, 0);
      ctx.lineTo(0, 20);
      ctx.lineTo(-14, 0);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    } else {
      ctx.fillStyle = "#6e655b";
      ctx.strokeStyle = "#3a332c";
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.ellipse(0, 4, 18, 12, 0.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#8a8176";
      ctx.beginPath();
      ctx.ellipse(-4, -2, 10, 7, -0.4, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }

  const styles = {
    player: { body: "#2f6f8f", trim: "#e0b44a", mark: "Q" },
    a: { body: "#a33b3b", trim: "#f0d0c8", mark: "A" },
    b: { body: "#3d6b45", trim: "#d5ead8", mark: "B" },
  };
  const order = karts.slice().sort((a, b) => a.kind === "player" ? 1 : -1);
  for (const kart of order) {
    const s = track.sample(kart.t);
    const style = styles[kart.kind === "player" ? "player" : kart.id];
    const vis = Math.max(-1, Math.min(1, kart.lateral + (kart.drift || 0)));
    const look = view.look || {};
    const dressed = kart.kind === "player";
    drawKart(ctx, s, vis, H, {
      ...style,
      body: dressed && look.body ? look.body : style.body,
      trim: dressed && look.trim ? look.trim : style.trim,
      bodyShine: dressed ? look.bodyShine || 0 : 0,
      trimShine: dressed ? look.trimShine || 0 : 0,
      turbo: kart.turbo > 0,
      air: kart.air || 0,
      airMax: kart.airMax || 0.5,
      hop: kart.hop || 1,
    }, time, kart.boost > 0 || kart.turbo > 0, kart.yaw,
    kart.kind === "player" ? (view.ribbonT || 0) : 0);
  }

  ctx.restore();

  const vig = ctx.createRadialGradient(w / 2, h / 2, h * 0.2, w / 2, h / 2, h * 0.72);
  vig.addColorStop(0, "rgba(0,0,0,0)");
  vig.addColorStop(1, "rgba(90,60,20,.28)");
  ctx.fillStyle = vig;
  ctx.fillRect(0, 0, w, h);

  /* CSEG-E1：小地图已 DOM 化，绘制迁入 #minimap 的内嵌 canvas。
     显隐由 main.js 的 visible 表达式显式控制（view.minimap 为布尔），不再依赖
     「frozen 画面就不会变」；底板由 CSS 提供，主画布 #c 不再承载小地图。 */
  if (view.minimap && view.mmCtx && view.mmModel) drawMinimap(view.mmCtx, view.mmModel);
  return matrix;
}

/* ---- CSEG-E1：小地图数据模型（纯函数 · Node 可单测）------------------------
 * 只消费几何域 / 状态域 / 中性元信息；字段白名单见 design/hud-ux-spec.md §1.2。
 * 输出键名刻意避开 spoken / other / correctLateral / left / right / pairKey /
 * qType / options / displayIpa / sym / hit / answer / correct / word / ipa / label，
 * nextGate 严格 5 键 {id,lap,line,distance,secondsTo}，绝不指向正确侧。
 * 唯一跨轮坐标 = 绝对里程 odo；t 只由 odo 派生：t_i = (odo_i / L) % 1。
 * --------------------------------------------------------------------------- */
const MM_ZONES = {
  camp: "出发营地",
  castle: "元音城堡",
  kingdom: "辅音王国",
  peak: "进阶峰",
};

function mmProjector(track, mmW, mmH) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const s of track.samples) {
    if (s.x < minX) minX = s.x;
    if (s.y < minY) minY = s.y;
    if (s.x > maxX) maxX = s.x;
    if (s.y > maxY) maxY = s.y;
  }
  const pad = 10;
  const innerW = Math.max(1, mmW - pad * 2);
  const innerH = Math.max(1, mmH - pad * 2);
  const spanX = Math.max(1e-6, maxX - minX);
  const spanY = Math.max(1e-6, maxY - minY);
  const sc = Math.min(innerW / spanX, innerH / spanY);
  const ox = pad - minX * sc + (innerW - spanX * sc) / 2;
  const oy = pad - minY * sc + (innerH - spanY * sc) / 2;
  return (x, y) => ({ x: ox + x * sc, y: oy + y * sc });
}

export function minimapModel(view) {
  const track = view.track;
  const L = track.length || 1;
  const laps = Math.max(1, view.laps || 1);
  const lap = Math.max(0, view.lap || 0);
  const mmW = view.mmW || 160;
  const mmH = view.mmH || 104;
  const dpr = view.dpr || 1;
  const proj = mmProjector(track, mmW, mmH);

  /* 赛道环线：沿用既有 min/max→ox/oy/sc 等比投影，不用 project(matrix,…)。 */
  const trackPath = track.samples.map((s) => proj(s.x, s.y));

  /* 三车点：t 只由绝对 odo 派生（两圈不会串位），绝不读 commitT / lineT%1。 */
  const karts = (view.karts || []).map((k) => {
    const odo = Number.isFinite(k.odo) ? k.odo : (k.t || 0) * L;
    const t = ((odo / L) % 1 + 1) % 1;
    const s = track.sample(t);
    const p = proj(s.x, s.y);
    const isPlayer = k.kind === "player";
    return {
      id: k.id, kind: k.kind, x: p.x, y: p.y,
      color: isPlayer ? "#2f6f8f" : (k.id === "a" ? "#a33b3b" : "#3d6b45"),
      r: isPlayer ? (mmW <= 120 ? 3.5 : 4.5) : (mmW <= 120 ? 2.6 : 3.2),
    };
  });

  /* 起终点：与 render.js 主画面的 finish = track.sample(0.012) 同源，中性单色。 */
  const startSample = track.sample(0.012);
  const startAt = proj(startSample.x, startSample.y);

  /* nextGate：只认当前 lap 的未判定门（E9 unheard / judged 跳过），严格 5 键。
     菱形坐标同样由 (line / L) % 1 从绝对里程派生。 */
  const ag = view.activeGate && view.activeGate.gate ? view.activeGate.gate : null;
  const act = (ag && !ag.judged && !ag.unheard && ag.lap === lap && Number.isFinite(ag.line)) ? ag : null;
  let nextGate = null;
  let nextGateAt = null;
  if (act) {
    const distance = Math.max(0, act.line - (view.playerOdo || 0));
    const speed = Math.max(1, view.speed || 1);
    nextGate = { id: act.id, lap: act.lap, line: act.line, distance, secondsTo: distance / speed };
    const t = ((act.line / L) % 1 + 1) % 1;
    const gs = track.sample(t);
    nextGateAt = proj(gs.x, gs.y);
  }

  /* 进度 = odo/(laps·L)，双端 clamp，不用 t（两圈 t 会重复）。 */
  const startOdo = view.startOdo || 0;
  const playerOdo = view.playerOdo || 0;
  const progress = Math.min(1, Math.max(0, (playerOdo - startOdo) / (laps * L)));
  const mapId = view.mapId || "camp";

  return {
    trackPath, karts, startAt, nextGateAt, nextGate,
    length: L, startOdo, lap, laps,
    lapText: `${Math.min(laps, lap + 1)}/${laps}`,
    progress,
    zone: MM_ZONES[mapId] || MM_ZONES.camp,
    mapId,
    phase: view.phase || "S0",
    reduced: !!view.reduced,
    mmW, mmH, dpr,
  };
}

function drawDiamond(ctx, x, y, r, fill, stroke) {
  ctx.beginPath();
  ctx.moveTo(x, y - r);
  ctx.lineTo(x + r, y);
  ctx.lineTo(x, y + r);
  ctx.lineTo(x - r, y);
  ctx.closePath();
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = 1.5; ctx.stroke(); }
}

/* CSEG-E1：drawMinimap 迁入内嵌 canvas（不是另起一套、不是停用）。
   逻辑沿用既有「赛道环线 + 三车点」，补进度弧 / 起终点 / 中性 nextGate 菱形；
   圈数由 DOM #minimap-lap 承载。全部坐标来自 minimapModel(view)，
   不使用 project(matrix,…)（那是主相机），也不消费任何答案域。 */
function drawMinimap(mmCtx, model) {
  const { mmW, mmH, dpr } = model;
  mmCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
  mmCtx.clearRect(0, 0, mmW, mmH);
  mmCtx.lineJoin = "round";
  mmCtx.lineCap = "round";

  const path = model.trackPath;
  if (!path.length) return;

  mmCtx.beginPath();
  path.forEach((p, i) => { if (i) mmCtx.lineTo(p.x, p.y); else mmCtx.moveTo(p.x, p.y); });
  mmCtx.closePath();
  mmCtx.strokeStyle = "#6b4a32";
  mmCtx.lineWidth = 3;
  mmCtx.stroke();

  /* 进度弧：长度 = progress，沿环线静态描金；无补间 / 无脉动（reduced 天然满足）。 */
  const end = Math.max(1, Math.floor(model.progress * (path.length - 1)));
  if (end > 1) {
    mmCtx.beginPath();
    for (let i = 0; i <= end; i++) {
      const p = path[i];
      if (i) mmCtx.lineTo(p.x, p.y); else mmCtx.moveTo(p.x, p.y);
    }
    mmCtx.strokeStyle = "#c9a227";
    mmCtx.lineWidth = 3;
    mmCtx.stroke();
  }

  /* 起终点：中性单色菱形，恒定显示，白描边与 nextGate 区分。 */
  drawDiamond(mmCtx, model.startAt.x, model.startAt.y, 4, "#a0720a", "#fffaf0");

  /* nextGate：中性单色菱形；S1 点亮 / S2 保持 / S3 或无门熄灭；
     无左右指向、无箭头、无高亮侧、无单侧放大。 */
  if (model.nextGateAt && (model.phase === "S1" || model.phase === "S2")) {
    drawDiamond(mmCtx, model.nextGateAt.x, model.nextGateAt.y, 5.5, "#a0720a", null);
  }

  for (const k of model.karts) {
    mmCtx.fillStyle = k.color;
    mmCtx.beginPath();
    mmCtx.arc(k.x, k.y, k.r, 0, Math.PI * 2);
    mmCtx.fill();
  }
}

export function project(matrix, x, y, dpr) {
  const p = new DOMPoint(x, y).matrixTransform(matrix);
  return { x: p.x / dpr, y: p.y / dpr };
}
