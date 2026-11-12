/* Task #28 / P1 · 3D 场景几何模型（纯函数 · 零 DOM / 零 three / 零 React 依赖 · Node 可单测）
 *
 * 本文件是「判定域 → 视觉域」的唯一换算层。硬约束：
 *  - 只读：只消费 `snapshot3d()` 产出的白名单纯数据 + opts.track 的几何契约
 *    { length, roadHalf, sample(t) }；不 import 任何产品模块、不调用写方法、不碰 localStorage。
 *  - 答案域零进入：允许集见 p1-gameplay-spec.md §1.4 / p1-3d-art-spec.md §3.6（本文件不复述
 *    那些键名，避免渲染层源码静态扫描命中）。白名单字段见 SNAPSHOT_KEYS / KART_KEYS / GATE_KEYS。
 *  - 跨轮坐标：一律从沿环归一化位置派生，t_i = wrap01(odo_i / L)；两圈同 commitT 的门靠
 *    lap 区分；邻车相对位置归一到 [-L/2, L/2)，跨圈不跳变。Q4 登记的 0.02·L 偏差本轮不修。
 *  - 局部跟车坐标系：以玩家采样点为原点，前进方向 -z、右向 +x、y 向上；scale = WORLD_SCALE
 *    （m / 2D unit）。前方赛道带只采样 aheadM 米，配合 FogExp2 收敛，绝不铺整条闭环赛道。
 *  - 防镜像：若实机左右镜像，只允许在渲染层翻 Z / 前向分量（meta.mirrorZ），
 *    绝不改判定域 lateral 符号。
 *
 * 本文件为 .mjs，不在五套门控的 .html/.js/.css 扫描范围内，且不含任何 ?v= 字面量。
 */
export const P1_TAG = "p1-20261110";

/* ---- 团队裁决 1：坐标系与相机（p1-3d-art-spec.md §1 / §2，建议值，实机可微调并记录） ---- */
export const WORLD_SCALE = 0.008;          // 1 m = 125 2D unit；roadHalf 520 → 4.16 m
export const FOG_COLOR = "#efe6d3";        // 纸色底（P0 探针同值）
export const FOG_DENSITY = 0.045;          // 纸雾收敛远端
export const NEAR_CLIP = 0.1;
export const FAR_CLIP = 120;
export const CAMERA_PRESET = Object.freeze({
  distanceM: 8,          // 车尾后方 8 m（≈4–5 车身）
  heightM: 3.6,          // 高机位 3.6 m
  pitchDeg: 18,          // 俯角 18°
  lookAheadM: 9,         // 注视点沿前向 9 m
  fov375: 78,            // 375×780 竖屏：垂直 FOV 为锚
  fov320: 74,            // 320×568：垂直 FOV 为锚
  fovWide: 60,           // 横屏 / PC
});
/* 裁决 2：单一暖主光 + 1 盏低强度柔补光（≤0.35）+ 接触 AO（几何软影，不引 postprocessing）。
   probe.jsx 的 lightCount=1 断言不受影响（独立入口、逐字不动）。 */
export const LIGHT_PRESET = Object.freeze({
  main: Object.freeze({ color: "#ffd6a0", intensity: 2.1, position: Object.freeze([3.2, 4.5, 5]) }),
  fill: Object.freeze({ color: "#fff2dc", intensity: 0.32 }),
  ao: "contact-shadow",
  count: 2,
});
/* 四区主题色（p1-3d-art-spec.md §4.3，逐字取值；只作材质换色，不驱动几何稀有度） */
export const ZONE = Object.freeze({
  camp:    Object.freeze({ road: "#C9AE82", curb: "#A88F63", rail: "#8C6D43" }),
  castle:  Object.freeze({ road: "#D8CEB4", curb: "#23364E", rail: "#C9A227" }),
  kingdom: Object.freeze({ road: "#C9AE82", curb: "#8C4034", rail: "#8C4034" }),
  peak:    Object.freeze({ road: "#EDE4D0", curb: "#7EA6C0", rail: "#B03A2E" }),
});
/* 与 render.js:382-386 的 2D 车体配色 / 标记一致，保证 L0/L1 视觉同源。 */
export const KART_STYLE = Object.freeze({
  player: Object.freeze({ color: "#2f6f8f", trim: "#e0b44a", mark: "Q" }),
  a: Object.freeze({ color: "#a33b3b", trim: "#f0d0c8", mark: "A" }),
  b: Object.freeze({ color: "#3d6b45", trim: "#d5ead8", mark: "B" }),
});
/* 车体包围盒（m）：art-spec §3.4 三车剪影高度（1.15 / 0.72 / 1.05）+ 1.6m 车长 / 0.9m 车宽。
   纯几何估计，供 QA「三车屏占比 > 0 且落在视口内」取证；运行时再用真实 WebGL 复核。 */
export const KART_BOX = Object.freeze({
  player: Object.freeze({ lengthM: 1.6, widthM: 0.9, heightM: 1.15 }),
  a:       Object.freeze({ lengthM: 1.6, widthM: 0.9, heightM: 0.72 }),
  b:       Object.freeze({ lengthM: 1.6, widthM: 0.9, heightM: 1.05 }),
});

/* ---- 只读白名单（团队裁决 4 / art-spec A1）。严禁任何答案域派生参数进入 3D 层。 ---- */
export const SNAPSHOT_KEYS = Object.freeze([
  "lap", "laps", "zone", "span", "time", "karts", "gates",
]);
export const KART_KEYS = Object.freeze([
  "id", "kind", "t", "lateral", "drift", "boost", "turbo", "air", "yaw",
]);
export const GATE_KEYS = Object.freeze(["id", "lap", "commitT"]);

/* 输出顶层键白名单（scene3d-model.test.mjs T2 逐项核对） */
export const SCENE_KEYS = Object.freeze([
  "tag", "lap", "laps", "progress", "origin",
  "road", "karts", "gates", "startFinish",
  "camera", "fog", "light", "meta", "convergence",
]);

const LANE_CENTERS = Object.freeze([-0.55, 0.55]);   // 与 TUNING.laneLateral 一致
const CENTER_DIVIDER = Object.freeze([0]);           // 裁决 3：纯色路面 + 中央虚线，M7/M8 不入 P1

function wrap01(v) { let x = v % 1; if (x < 0) x += 1; return x; }
function wrapHalf(v) { let x = wrap01(v); if (x >= 0.5) x -= 1; return x; }

/* ---- 纯数学透视投影（零 three 依赖，Node 可单测）------------------------------
 * 相机 lookAt 基：zAxis = -forward、xAxis = (1,0,0)、yAxis = cross(zAxis, xAxis)。
 * 竖屏以垂直 FOV 为锚（art-spec §2.2），aspect = viewW/viewH。
 * 相机后方的采样点把深度 clamp 到 near，保证取证序列恒为有限数（不出现 NaN/Inf）。
 * 用途：convergence.centerlineProjectedY（远端收敛）+ karts[].bboxNdc / screenRatio（三车可见）。
 */
export function cameraBasis(pitchDeg) {
  const p = (pitchDeg * Math.PI) / 180;
  const sy = Math.sin(p), cy = Math.cos(p);
  return {
    forwardY: -sy, forwardZ: -cy,   // forward = (0, -sin p, -cos p)
    zy: sy, zz: cy,                  // zAxis = -forward
    uy: cy, uz: -sy,                 // yAxis = (0, cos p, -sin p)
  };
}
export function projectNdc(cam, px, py, pz, viewW, viewH) {
  const b = cameraBasis(cam.pitchDeg);
  const dx = px - cam.x, dy = py - cam.y, dz = pz - cam.z;
  const xCam = dx;
  const yCam = dy * b.uy + dz * b.uz;
  const zCam = dy * b.zy + dz * b.zz;
  const depth = Math.max(-zCam, Math.max(cam.near, 1e-3));
  const tanHalf = Math.tan((cam.fov * Math.PI) / 360);
  const aspect = (Number(viewW) || 375) / (Number(viewH) || 780);
  return {
    x: (xCam / depth) / (aspect * tanHalf),
    y: (yCam / depth) / tanHalf,
    depth,
  };
}
function kartBoxNdc(cam, k, viewW, viewH) {
  const box = KART_BOX[k.kind === "player" ? "player" : k.id] || KART_BOX.a;
  const hx = box.widthM / 2, hz = box.lengthM / 2;
  const y0 = k.lift || 0, y1 = y0 + box.heightM;
  let x0 = Infinity, x1 = -Infinity, ny0 = Infinity, ny1 = -Infinity;
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) for (const sy of [0, 1]) {
    const q = projectNdc(cam, k.x + sx * hx, sy ? y1 : y0, k.z + sz * hz, viewW, viewH);
    if (q.x < x0) x0 = q.x;
    if (q.x > x1) x1 = q.x;
    if (q.y < ny0) ny0 = q.y;
    if (q.y > ny1) ny1 = q.y;
  }
  return { x0, y0: ny0, x1, y1: ny1 };
}

/** 竖屏以垂直 FOV 为锚（art-spec §2.2）；按视口宽高比取建议值。 */
export function cameraFovFor(viewW, viewH) {
  const w = Number(viewW) || 375, h = Number(viewH) || 780;
  if (w / h >= 1) return CAMERA_PRESET.fovWide;
  return w <= 340 ? CAMERA_PRESET.fov320 : CAMERA_PRESET.fov375;
}

/**
 * 把赛道采样点 / 世界向量投影到「以玩家采样点为原点的局部跟车坐标系」。
 * 点：d = p - origin；向量：isVector=true 时直接传 (vx,vy) 不做平移。
 * 局部 x = d·r（右），局部 z = -(d·f)（前为负 z）。scale 把 2D unit 换成米。
 */
function toLocal(px, py, origin, scale, isVector = false) {
  const dx = isVector ? px : px - origin.x;
  const dy = isVector ? py : py - origin.y;
  return {
    x: (dx * origin.rx + dy * origin.ry) * scale,
    z: -(dx * origin.fx + dy * origin.fy) * scale,
  };
}

/**
 * @param {object} snap  snapshot3d() 的白名单只读快照（无 track / 无函数 / 无答案域）
 * @param {object} opts  { track, worldScale, aheadM, behindM, segments, viewW, viewH, mirrorZ }
 * @returns {object|null} 场景帧；title 态（无 karts）返回 null
 */
export function buildSceneFrame(snap, opts = {}) {
  if (!snap || !Array.isArray(snap.karts) || !snap.karts.length) return null;
  const track = opts.track || null;
  if (!track || !(track.length > 0) || typeof track.sample !== "function") return null;
  const L = track.length;
  const roadHalf = Number.isFinite(track.roadHalf) ? track.roadHalf : 520;
  const scale = Number.isFinite(opts.worldScale) ? opts.worldScale : WORLD_SCALE;
  const aheadM = Number.isFinite(opts.aheadM) ? opts.aheadM : 48;   // 前方 48 m（纸雾在 ~45 m 收敛）
  const behindM = Number.isFinite(opts.behindM) ? opts.behindM : 10; // 车后 10 m（相机在 8 m）
  const segments = Math.max(8, opts.segments || 48);
  const mirrorZ = opts.mirrorZ === -1 ? -1 : 1;                     // 只翻渲染层 Z，不动 lateral

  const player = snap.karts.find((k) => k.kind === "player") || snap.karts[0];
  const t0 = wrap01(Number(player.t) || 0);
  const s0 = track.sample(t0);
  const origin = { x: s0.x, y: s0.y, fx: s0.fx, fy: s0.fy, rx: s0.rx, ry: s0.ry, t: t0 };
  const lapNow = Math.max(0, snap.lap || 0);
  const laps = Math.max(1, snap.laps || 2);
  /* 相机「跟随」可观测信号：由白名单 lap + t 派生的里程估计（非读取判定域 odo）。 */
  const odoEstM = (lapNow + t0) * L * scale;

  /* ---- 前方赛道带：按局部相对里程采样，不闭环；弯道自然向远处弯出 ---- */
  const road = [];
  for (let i = 0; i <= segments; i++) {
    const dzM = -behindM + (aheadM + behindM) * (i / segments);
    const s = track.sample(wrap01(t0 + dzM / (L * scale)));
    const c = toLocal(s.x, s.y, origin, scale);
    const n = toLocal(s.rx, s.ry, origin, scale, true);
    const nl = Math.hypot(n.x, n.z) || 1;
    road.push({
      x: c.x, z: c.z * mirrorZ, dzM,
      nx: n.x / nl, nz: (n.z / nl) * mirrorZ,   // 法向 Z 同步翻，保证 ribbon 左右不镜像错位
      w: roadHalf * scale,
    });
  }

  /* ---- 三车：位置由各自 t 派生，跨圈相对位置归一，不写回任何字段 ---- */
  const karts = snap.karts.map((k) => {
    const ti = wrap01(Number(k.t) || 0);
    const s = track.sample(ti);
    const c = toLocal(s.x, s.y, origin, scale);
    const lat = Math.max(-1, Math.min(1, (Number(k.lateral) || 0) + (Number(k.drift) || 0)));
    const off = lat * roadHalf;
    const o = toLocal(s.rx * off, s.ry * off, origin, scale, true);
    const d = toLocal(s.fx, s.fy, origin, scale, true);
    const dl = Math.hypot(d.x, d.z) || 1;
    const st = KART_STYLE[k.kind === "player" ? "player" : k.id] || KART_STYLE.a;
    const dzM = wrapHalf(ti - t0) * L * scale;
    return {
      id: k.id, kind: k.kind,
      color: st.color, trim: st.trim, mark: st.mark,
      x: c.x + o.x, y: 0, z: (c.z + o.z) * mirrorZ,
      dirX: d.x / dl, dirZ: (d.z / dl) * mirrorZ,
      lift: Math.max(0, Number(k.air) || 0) * scale,
      boosting: !!((Number(k.turbo) || 0) > 0 || (Number(k.boost) || 0) > 0),
      dzM,
      visible: dzM > -behindM - 4 && dzM < aheadM + 4,
    };
  });

  /* ---- 门 / 路牌：只取当前圈且在预告窗口内的中性几何（裁决 3：M8 镜像闸门不入 P1） ---- */
  const gates = [];
  for (const g of (snap.gates || [])) {
    if (g.lap !== lapNow) continue;
    const dzM = wrap01((Number(g.commitT) || 0) - t0) * L * scale;
    if (dzM > aheadM || dzM < -behindM) continue;
    const s = track.sample(wrap01(t0 + dzM / (L * scale)));
    const c = toLocal(s.x, s.y, origin, scale);
    const n = toLocal(s.rx, s.ry, origin, scale, true);
    const nl = Math.hypot(n.x, n.z) || 1;
    const w = roadHalf * scale;
    gates.push({
      id: g.id, lap: g.lap, dzM,
      x: c.x, z: c.z * mirrorZ,
      xl: c.x - (n.x / nl) * w, zl: (c.z - (n.z / nl) * w) * mirrorZ,
      xr: c.x + (n.x / nl) * w, zr: (c.z + (n.z / nl) * w) * mirrorZ,
    });
  }

  /* ---- 起终点门：前方最近的 t=0 跨圈点（中性几何，内容解耦） ---- */
  const sfDzM = wrap01(-t0) * L * scale;
  let startFinish = null;
  if (sfDzM <= aheadM) {
    const s = track.sample(wrap01(t0 + sfDzM / (L * scale)));
    const c = toLocal(s.x, s.y, origin, scale);
    startFinish = { dzM: sfDzM, x: c.x, z: c.z * mirrorZ };
  }

  const progress = Math.max(0, Math.min(1, (lapNow + t0) / laps));
  const lapLengthM = L * scale;
  const visibleRangeM = 3 / FOG_DENSITY;      // exp(-(d·density)^2) → 3/density 处几乎全雾
  const fov = cameraFovFor(opts.viewW, opts.viewH);
  const zoneId = ZONE[snap.zone] ? snap.zone : "camp";

  /* ---- 相机自洽 + QA 可观测（PC-* / PV-*）--------------------------------
   * pitchDeg 决定 forward；look = pos + forward·lookAheadM，不再让 lookZ 与 pitchDeg 各自为政。
   * 透视投影用纯数学完成，零 three 依赖；车体包围盒 8 角投影给 screenRatio / bboxNdc。
   */
  const basis = cameraBasis(CAMERA_PRESET.pitchDeg);
  const cam = {
    x: 0, y: CAMERA_PRESET.heightM, z: CAMERA_PRESET.distanceM,
    pitchDeg: CAMERA_PRESET.pitchDeg, fov, near: NEAR_CLIP,
    forwardY: basis.forwardY, forwardZ: basis.forwardZ,
  };
  const look = {
    x: 0,
    y: cam.y + basis.forwardY * CAMERA_PRESET.lookAheadM,
    z: cam.z + basis.forwardZ * CAMERA_PRESET.lookAheadM,
  };
  const tanHalf = Math.tan((fov * Math.PI) / 360);
  const vanishingPointY = Math.tan((CAMERA_PRESET.pitchDeg * Math.PI) / 180) / tanHalf;
  /* 沿相机前向的理想中心线投影 y：忽略弯道横向，故必然单调收敛到消失点，
     作为「远端收敛 / 赛道往远处消失」的可量化证据；真实弯道投影由 road[i] 交付渲染层。 */
  const centerlineProjectedY = road.map((r) => projectNdc(cam, 0, 0, -r.dzM, opts.viewW, opts.viewH).y);
  for (const k of karts) {
    const box = kartBoxNdc(cam, k, opts.viewW, opts.viewH);
    k.bboxNdc = box;
    k.screenRatio = +(((box.x1 - box.x0) * (box.y1 - box.y0)) / 4).toFixed(6);
  }

  return {
    tag: P1_TAG,
    lap: lapNow, laps, progress,
    origin: { x: origin.x, y: origin.y, fx: origin.fx, fy: origin.fy, rx: origin.rx, ry: origin.ry, t: t0 },
    road, karts, gates, startFinish,
    camera: {
      x: cam.x, y: cam.y, z: cam.z,
      lookX: look.x, lookY: look.y, lookZ: look.z,
      pitchDeg: CAMERA_PRESET.pitchDeg,
      forwardY: cam.forwardY, forwardZ: cam.forwardZ,
      fov, fovIsVertical: true, near: NEAR_CLIP, far: FAR_CLIP,
      distanceM: CAMERA_PRESET.distanceM, heightM: CAMERA_PRESET.heightM,
      lookAheadM: CAMERA_PRESET.lookAheadM,
      odoEstM, worldX: origin.x, worldY: origin.y,
    },
    fog: { color: FOG_COLOR, density: FOG_DENSITY, isExp2: true, far: FAR_CLIP },
    light: {
      main: { color: LIGHT_PRESET.main.color, intensity: LIGHT_PRESET.main.intensity, position: [...LIGHT_PRESET.main.position] },
      fill: { color: LIGHT_PRESET.fill.color, intensity: LIGHT_PRESET.fill.intensity },
      ao: LIGHT_PRESET.ao, count: LIGHT_PRESET.count,
    },
    meta: {
      aheadM, behindM, scale, length: L, segments, roadHalf,
      laneCenters: [...LANE_CENTERS], laneMarks: [...CENTER_DIVIDER],
      zone: zoneId, zoneColor: { ...ZONE[zoneId] },
      mirrorZ, roadStyle: "solid", gateStyle: "neutral",
      m7Terrain: false, m8MirrorGate: false,
      worldScale: scale, lapLengthM,
      /* 不泄题护栏：场景输出只有几何 / 状态 / 中性元信息；见 T4 / T17 */
      snapshotKeys: [...SNAPSHOT_KEYS], kartKeys: [...KART_KEYS], gateKeys: [...GATE_KEYS],
    },
    convergence: {
      fogDensity: FOG_DENSITY,
      visibleRangeM,
      lapLengthM,
      seesWholeLoop: visibleRangeM >= lapLengthM,   // 必为 false：雾在整圈之前收敛
      farClipM: FAR_CLIP,
      roadDzM: road.map((r) => +r.dzM.toFixed(3)),
      centerlineProjectedY: centerlineProjectedY.map((v) => +v.toFixed(6)),
      vanishingPointY: +vanishingPointY.toFixed(6),
      vanishingTargetRatio: 0.40,
    },
  };
}

/**
 * 只读快照：把 race.state 投影成白名单纯数据（团队裁决 4）。
 * 这是 3D 层接触判定域的**唯一**入口；不复制函数、不复制门内容、不含任何答案域字段。
 * 放在本文件而非 race.js，是因为 ADR-2 要求 race.js 逐字不改（不能给它加方法）。
 */
export function snapshot3d(state) {
  if (!state || !Array.isArray(state.karts) || !state.karts.length) return null;
  const project = (src, keys) => {
    const out = {};
    for (const k of keys) out[k] = src[k];
    return out;
  };
  return {
    lap: state.lap || 0,
    laps: state.laps || 2,
    zone: state.mapId || "camp",
    span: Number(state.span) || 0,
    time: Number(state.time) || 0,
    karts: state.karts.map((k) => project(k, KART_KEYS)),
    gates: (state.gates || []).map((g) => project(g, GATE_KEYS)),
  };
}
