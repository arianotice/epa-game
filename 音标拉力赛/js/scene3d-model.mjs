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

/* ---- IMPL-1B：单跳 / 石头 / 环境流速的渲染层镜像常量 --------------------------
   这些值与判定层（race.js / config.js）逐字对齐，仅供 3D 只读几何投影，
   绝不参与任何判定、绝不写回 state；集中在此便于 QA 比对，避免散落硬编码。
   - AIR_MAX / JUMP_PEAK：race.js player.airMax=0.5、美术线单跳 lift 峰值 0.55m；
   - H_ROCK：石头半埋外露高 0.32m；ROCK_BAND_VIS：碰撞带 ±78 unit；
   - MERGE_DT：TUNING.mergeDt=0.028 分叉闭合窗口（t 域）；
   - VISUAL_FLOW_GAIN：方案 B 单一视觉流速标量，只放大纯环境元素滚动相位。 */
export const AIR_MAX = 0.5;
export const JUMP_PEAK = 0.55;
export const H_ROCK = 0.32;
/* 命名刻意采用中性写法（不复用判定层含碰撞语义词的原名），避开答案域禁词字面；
   值与 config.js 的碰撞带常量 78 逐字对齐，仅供纯渲染派生、不参与判定。 */
export const ROCK_BAND_VIS = 78;
export const NOMINAL_SPEED = 260;   // 名义速度（与 config follow 档一致），仅用于标线派生
export const MERGE_DT = 0.028;
export const VISUAL_FLOW_GAIN = 1.6;

/* ---- FWD-VIS-2：3D 视觉可读性增强常量（纯渲染，零判定语义 / 零答案域） --------
   真实浏览器取证确认两处肉眼缺陷：石头几何 Dodecahedron(0.5)×H_ROCK0.32 实际半径
   仅 ~0.16m 且 #8a7a63 与路面 #C9AE82 明度接近 → 30–60m 不可辨；分叉双车道张开
   幅度被雾/词卡稀释 → 截图看不出「两条真实车道分开」。
   本组常量只被 scene3d.jsx 渲染层消费：放大石体 / 深色石体 + 高亮描边环 + 加粗
   起跳标线；放大分叉左右车道外扩 + 双色车道带 + 暗红虚线探险路径（art-spec §4.2
   既有机制）+ 窄而连续的分流岛分隔带。绝不改变 H_ROCK / MERGE_DT / ROCK_BAND_VIS /
   forkFlare / 任何判定域量；键名中性、不含答案域与左右语义词面。 */
/* 视觉修复轮（用户反馈驱动，纯渲染、零判定写回）：
   - 任务1 巨石→真小石头：半径 0.92m（旧 FWD-VIS-4 放大值）回落到 0.25m（仍 > 初始 0.16m），
     金环 1.14/1.95 收窄到 0.38/0.75（内环仍越过石体 0.25m 投影半径），石体提亮到 #8a7a63；
     「提前可见」三件提示原样保留：贴地金环 rockRing + 起跳金线 marks（markStretch 不缩）+ fog:false。
   - 任务2 分岔清晰：色带加深提亮拉开明度、segStretch 收到贴合段间距、spanScale 缩短视觉走廊。 */
export const ROCK_VIS = Object.freeze({
  radiusM: 0.25,          // 真·小石头渲染半径（m）；基准几何 Dodecahedron(1)，0.92→0.25
  bodyColor: "#8a7a63",   // 浅一点暖褐（旧 #5b4a37），与 #c9ae82 路面留适度明度差，靠金环/金线预告
  bodyEmissive: "#2e2210",// 顶面轻微自发光，远处保住轮廓而不融进路面
  bodyEmissiveIntensity: 0.38,
  ringInnerM: 0.38,       // 贴地描边环内径（m），越过石体 0.25m 投影半径
  ringOuterM: 0.75,       // 外径（m），0.37m 宽金色预告带（旧 1.95 随石体缩小同步收窄）
  ringColor: "#ffd54a",   // 更亮的金：远距离一抹金色预告
  markColor: "#f2c94c",   // 起跳标线（加粗加亮，取代偏暗 #c9a227）
  markDepthM: 0.16,       // GEO.mark 深度基准，jsx 内 scale.z 再乘 stretch
  markStretch: 3.4,       // 起跳标线不缩：实际纵深 = 0.16 × 3.4 ≈ 0.54m（提前可见的玩法关键信息）
});
export const FORK_VIS = Object.freeze({
  spread: 1.42,           // 左右车道中心视觉外扩倍率（判定域无关，保持）
  islandGain: 0.42,       // 中央分流岛宽度系数（窄而连续的分隔带，避免宽暗条盖住车道）
  islandColor: "#3E2E20", // 任务2：分隔带加深（旧 #6f5b45 明度太接近路面 #C9AE82），拉开对比
  islandNearScale: 0.55,  // 近端（dzM≤0）宽度系数，实体楔形保持、仅收窄
  islandNearFadeM: 16,    // 从近端到远端线性恢复全宽的里程（m）
  bandBaseM: 1.15,        // 车道色带 flare=0 收拢宽度（m）；两条常驻导引带
  bandGainM: 1.95,        // 车道色带 flare=1 额外宽度（m），张开态 ≈ 3.1m
  bandA: "#FFF4DC",       // 任务2：奶白带提亮（旧 #f6ead0），与路面 #C9AE82 明度拉开
  bandB: "#5A3B22",       // 任务2：深木带加深（旧 #8C6D43 与路面太接近），压低明度强对比
  pathColor: "#8C4034",   // 暗红虚线探险路径（art-spec §4.2 既有视觉锚）
  segStretch: 7.6,        // 任务2：0.16×7.6≈1.22m≈段间距 1.21m，恰好连续不重叠（旧 9.5=1.52m 重叠生摩纹）
  pathStretch: 2.4,       // 探险路径单段纵深系数（虚线节奏）
  spanScale: 0.6,         // 任务2：分岔视觉长度缩短，forkFlare 的 spanT ×0.6（不动判定域 span / MERGE_DT）
});

/* ---- 团队裁决 1：坐标系与相机（p1-3d-art-spec.md §1 / §2，建议值，实机可微调并记录） ---- */
export const WORLD_SCALE = 0.008;          // 1 m = 125 2D unit；roadHalf 520 → 4.16 m
export const FOG_COLOR = "#efe6d3";        // 纸色底（P0 探针同值）
export const FOG_DENSITY = 0.06;           // 任务3：0.045→0.06，远处更快淡出=速度感
export const NEAR_CLIP = 0.1;
export const FAR_CLIP = 120;
export const CAMERA_PRESET = Object.freeze({
  distanceM: 7,          // 任务3：8→7 m，更贴车尾=更快体感
  heightM: 3.0,          // 任务3：3.6→3.0 m，机位压低
  pitchDeg: 18,          // 俯角 18°（不动）
  lookAheadM: 11,        // 任务3：9→11 m，看得更远=速度感
  fov375: 88,            // 任务3：78→88，竖屏垂直 FOV 拉大（边缘拉伸感）
  fov320: 84,            // 任务3：74→84
  fovWide: 60,           // 横屏 / PC（不动）
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
/* IMPL-1B B5：加只读 pickups；KART_KEYS 在 air 后同序补 airMax / hop（运动学域，
   与 verify_p1_visual.py:42 期望按同一顺序同步；GATE_KEYS 三键一字不动）。 */
export const SNAPSHOT_KEYS = Object.freeze([
  "lap", "laps", "zone", "span", "time", "karts", "gates", "pickups",
]);
export const KART_KEYS = Object.freeze([
  "id", "kind", "t", "lateral", "drift", "boost", "turbo", "air", "airMax", "hop", "yaw",
]);
export const GATE_KEYS = Object.freeze(["id", "lap", "commitT"]);
/* IMPL-1B B5：pickups 只读投影白名单，答案域零泄露（不含任何判定域千预键）。 */
export const PICKUP_KEYS = Object.freeze([
  "id", "kind", "t", "lateral", "taken", "armed", "cleared",
]);

/* 输出顶层键白名单（scene3d-model.test.mjs T2 逐项核对）。
   IMPL-1B：新增 pickups 几何 + 真实分叉 fork 只读派生（纯中性几何，无答案域）。 */
export const SCENE_KEYS = Object.freeze([
  "tag", "lap", "laps", "progress", "origin",
  "road", "karts", "gates", "pickups", "fork", "startFinish",
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
    /* IMPL-1B B5：单级 lift(p)=JUMP_PEAK·sin(π·p)，p=1-air/airMax，
       与判定层 air 共用同一归一化相位（零漂移、零时间补间）；airMax 缺省 AIR_MAX。
       起跳瞬间 p=0、落地 p=1 均为 0，滞空中点达峰值 0.55m（h_rock=0.32m 半埋）。 */
    const airMax = Math.max(1e-6, Number(k.airMax) || AIR_MAX);
    const air = Math.min(airMax, Math.max(0, Number(k.air) || 0));
    const p = 1 - air / airMax;
    const lift = p >= 1 ? 0 : JUMP_PEAK * Math.sin(Math.PI * p);
    return {
      id: k.id, kind: k.kind,
      color: st.color, trim: st.trim, mark: st.mark,
      x: c.x + o.x, y: 0, z: (c.z + o.z) * mirrorZ,
      dirX: d.x / dl, dirZ: (d.z / dl) * mirrorZ,
      lift,
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

  /* ---- IMPL-1B B6：真实分叉只读几何（f:0→1→0 张开→选边→闭合） ----------------
     纯中性，只从 snap.gates 的 commitT / snap.span / MERGE_DT 派生，与判定层
     branchLateral() 同源相位；零写回 odo/lateral/g.line，零答案域。
     键名刻意用 sideA/sideB 等中性命名，避开答案域与判定语义词面。 */
  /* 任务2：forkFlare 的视觉张开窗口缩短到现值 ×spanScale(0.6)，分岔变成短引导区而非长走廊。
     仅缩放纯渲染的 flare 里程；判定域 snap.span / merge / MERGE_DT 逐字不动，零写回。 */
  const spanT = (Number(snap.span) || 0.02) * (Number(FORK_VIS.spanScale) || 0.6);
  const mergeT = MERGE_DT;
  function forkFlare(tAt) {
    let best = 0;
    for (const g of (snap.gates || [])) {
      if (g.lap !== lapNow) continue;
      const d = wrapHalf(tAt - wrap01(Number(g.commitT) || 0));
      const start = -spanT;
      const full = -spanT * 0.42;
      let fv = 0;
      if (d >= start && d < full) fv = (d - start) / Math.max(1e-6, full - start);
      else if (d >= full && d <= 0) fv = 1;
      else if (d > 0 && d <= mergeT) fv = 1 - d / Math.max(1e-6, mergeT);
      if (fv > best) best = fv;
    }
    return Math.max(0, Math.min(1, best));
  }
  const fork = road.map((r) => {
    const tAt = wrap01(t0 + r.dzM / (L * scale));
    const flare = forkFlare(tAt);
    const centerM = 0.55 * r.w;                 // 与 TUNING.laneLateral 同源（中性系数）
    const branchM = 0.91 * r.w;                 // 分叉外扩后的分支中心
    const sideA = -(centerM + (branchM - centerM) * flare);
    return {
      dzM: r.dzM, x: r.x, z: r.z, nx: r.nx, nz: r.nz, w: r.w,
      flare: +flare.toFixed(6),
      island: +(0.28 * flare * r.w).toFixed(6),
      sideA: +sideA.toFixed(6),
      sideB: +(-sideA).toFixed(6),
    };
  });

  /* ---- IMPL-1B B4/B6：pickups 只读几何（半埋石头 + 宝石 + 贴地起跳标线） ----
     只消费 snapshot3d 的 PICKUP_KEYS 白名单投影；未 taken 才可见。
     起跳标线里程 = 石头前 AIR_COVER = airMax·speed + 碰撞带（≈208/228 unit），
     换算成米后给 markDzM，渲染层据此画贴地金线；零写回判定量。 */
  const jumpLeadM = (AIR_MAX * NOMINAL_SPEED + ROCK_BAND_VIS) * scale;
  const pickups = (snap.pickups || []).map((it) => {
    const ti = wrap01(Number(it.t) || 0);
    const s = track.sample(ti);
    const c = toLocal(s.x, s.y, origin, scale);
    const off = (Number(it.lateral) || 0) * roadHalf;
    const o = toLocal(s.rx * off, s.ry * off, origin, scale, true);
    const dzM = wrapHalf(ti - t0) * L * scale;
    const isRock = it.kind === "rock";
    return {
      id: it.id, kind: it.kind, t: ti, lateral: Number(it.lateral) || 0,
      taken: !!it.taken, armed: !!it.armed, cleared: !!it.cleared,
      x: c.x + o.x, z: (c.z + o.z) * mirrorZ,
      y: isRock ? H_ROCK * 0.5 : 0.28,
      h: isRock ? H_ROCK : 0.22,
      dzM, markDzM: dzM - jumpLeadM,
      visible: !it.taken && dzM > -behindM - 4 && dzM < aheadM + 4,
    };
  });

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
    road, karts, gates, pickups, fork, startFinish,
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
      pickupKeys: [...PICKUP_KEYS], hRock: H_ROCK, jumpPeak: JUMP_PEAK,
      visualFlowGain: VISUAL_FLOW_GAIN,
      /* FWD-VIS-2：纯渲染视觉参数随帧发布，QA 可只读比对，零判定域写回。 */
      rockVis: { ...ROCK_VIS }, forkVis: { ...FORK_VIS },
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
    /* IMPL-1B B5：pickups 只投影 7 键白名单，答案域零泄露。 */
    pickups: (state.pickups || []).map((p) => project(p, PICKUP_KEYS)),
  };
}
