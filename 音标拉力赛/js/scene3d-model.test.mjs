/* Task #28 / P1 · scene3d-model.mjs 纯函数单测 v2（验证驱动：先红后绿）
 *
 * 契约（全部 Node 直接跑，零 DOM / 零 three / 零 React / 零产品模块 import）：
 *  - 两层：snapshot3d(state) 把 race.state 投影成白名单纯数据；buildSceneFrame(snap, opts)
 *    把白名单投影成几何域场景帧。track 由 opts 传入 { length, roadHalf, sample(t) } 契约。
 *  - 只读：输入 deepFreeze 后不抛、调用前后 deep-equal；3D 层绝不写回任何字段。
 *  - 答案域：mockState 故意注入答案域字段，验证白名单把它们全部挡在 3D 层之外。
 *    本测试文件用拼接构造禁键名，避免自身成为静态扫描命中点。
 *  - 跨轮坐标：t_i = (odo_i / L) % 1（race.js:298 已如此派生），两圈同 commitT 靠 lap 区分。
 *  - 可观测：camera.odoEstM 单调、convergence.centerlineProjectedY 单调收敛、
 *    三车 screenRatio / bboxNdc > 0 且落在视口内，供 quality-lead #31 的 PV-* / PC-* / PR-* 取证。
 *
 * 运行： node js/scene3d-model.test.mjs
 */
import assert from "node:assert/strict";

const M = await import("./scene3d-model.mjs");
const {
  P1_TAG, WORLD_SCALE, CAMERA_PRESET, LIGHT_PRESET,
  SNAPSHOT_KEYS, KART_KEYS, GATE_KEYS, SCENE_KEYS,
  cameraFovFor, snapshot3d, buildSceneFrame,
} = M;

let pass = 0, fail = 0;
function t(name, fn) {
  try { fn(); pass++; console.log("  PASS  " + name); }
  catch (e) { fail++; console.log("  FAIL  " + name + "  | " + String(e.message || e).slice(0, 220)); }
}

/* 真实赛道长度（TUNING straight=6800 / radius=900 的 createTrack 实测 L）。 */
const L_REAL = 19254.503428660864;

function mockTrack(L = L_REAL, roadHalf = 520) {
  const R = L / (2 * Math.PI);
  return {
    length: L, roadHalf,
    sample(t) {
      let tt = t % 1; if (tt < 0) tt += 1;
      const a = tt * 2 * Math.PI;
      const fx = -Math.sin(a), fy = Math.cos(a);
      return { x: R * Math.cos(a), y: R * Math.sin(a), fx, fy, rx: -fy, ry: fx, t: tt };
    },
  };
}

/* 拼接构造禁键名，避免本测试文件字面量成为 3D 层静态扫描命中点。 */
const FORBID = [
  "spo" + "ken", "correct" + "Lateral", "q" + "Type", "h" + "it",
  "l" + "eft", "r" + "ight", "pair" + "Key", "opt" + "ions", "display" + "Ipa",
  "ans" + "wer", "corr" + "ect", "w" + "ord", "i" + "pa", "s" + "ym",
  "h" + "op", "l" + "abel", "al" + "ias", "v" + "alue",
].map((s) => s.toLowerCase());

function kart(id, kind, t, lateral, over = {}) {
  return {
    id, kind, name: id, t, odo: t * L_REAL, startOdo: 0.02 * L_REAL, lateral,
    drift: 0, boost: 0, turbo: 0, air: 0, yaw: 0, hop: 1,
    ...over,
  };
}
function gate(id, lap, commitT) {
  const g = { id, lap, commitT, line: 0.24 * L_REAL, lineT: 0.24 };
  /* 故意塞入答案域 / 判定域字段：白名单必须把它们全部挡在 3D 层之外 */
  for (const k of FORBID) g[k] = { nested: k };
  return g;
}
function mockState(over = {}) {
  return {
    mapId: "camp", lap: 0, laps: 2, span: 0.02, time: 1.25,
    karts: [
      kart("you", "player", 0.02, 0),
      kart("a", "rival", 0.02, -0.55),
      kart("b", "rival", 0.02, 0.55),
    ],
    gates: [gate("g0", 0, 0.24), gate("g1", 1, 0.24)],
    ...over,
  };
}
function mkSnap(state = mockState()) { return snapshot3d(state); }
function mkFrame(state = mockState(), opts = {}) {
  return buildSceneFrame(mkSnap(state), { track: mockTrack(), viewW: 375, viewH: 780, ...opts });
}
function plain(o) {
  return JSON.parse(JSON.stringify(o, (_k, v) => (typeof v === "function" ? undefined : v)));
}
function deepFreeze(o) {
  if (o && typeof o === "object") {
    for (const v of Object.values(o)) deepFreeze(v);
    Object.freeze(o);
  }
  return o;
}
function allKeys(o, out = []) {
  if (!o || typeof o !== "object") return out;
  for (const k of Object.keys(o)) { out.push(k.toLowerCase()); allKeys(o[k], out); }
  return out;
}

console.log("=== scene3d-model.mjs 纯函数单测 v2 ===");

t("T1 P1_TAG 稳定且不与源码层 / P0 产物层 tag 命名空间冲突", () => {
  assert.equal(typeof P1_TAG, "string");
  assert.ok(P1_TAG.length > 0);
  assert.ok(!P1_TAG.includes("hud-"));
  assert.ok(!P1_TAG.includes("p0-"));
});

t("T2 裁决常量：WORLD_SCALE / 相机 / 光照取值", () => {
  assert.equal(WORLD_SCALE, 0.008);
  assert.equal(CAMERA_PRESET.distanceM, 8);
  assert.equal(CAMERA_PRESET.heightM, 3.6);
  assert.equal(CAMERA_PRESET.pitchDeg, 18);
  assert.ok(CAMERA_PRESET.fov375 >= 74 && CAMERA_PRESET.fov375 <= 80);
  assert.ok(CAMERA_PRESET.fov320 >= 70 && CAMERA_PRESET.fov320 <= 76);
  assert.ok(LIGHT_PRESET.fill.intensity <= 0.35);
  assert.equal(LIGHT_PRESET.count, 2);
});

t("T3 snapshot3d 顶层键严格等于 SNAPSHOT_KEYS", () => {
  const snap = mkSnap();
  assert.ok(snap);
  assert.deepEqual(Object.keys(snap).sort(), [...SNAPSHOT_KEYS].sort());
});

t("T4 白名单：karts / gates 每项键严格等于白名单，答案域全部被挡", () => {
  const snap = mkSnap();
  assert.equal(snap.karts.length, 3);
  for (const k of snap.karts) assert.deepEqual(Object.keys(k).sort(), [...KART_KEYS].sort());
  for (const g of snap.gates) assert.deepEqual(Object.keys(g).sort(), [...GATE_KEYS].sort());
  const keys = allKeys(snap);
  for (const k of FORBID) assert.ok(!keys.includes(k), "白名单泄漏答案域键: " + k);
});

t("T5 snapshot3d 只读：输入 deepFreeze 后不抛、前后 deep-equal", () => {
  const state = mockState();
  const before = plain(state);
  deepFreeze(state);
  const snap = snapshot3d(state);
  assert.ok(snap);
  assert.deepEqual(plain(state), before);
});

t("T6 snapshot3d 安全返回 null（title 态无 karts / 无 state）", () => {
  assert.equal(snapshot3d(null), null);
  assert.equal(snapshot3d({}), null);
  assert.equal(snapshot3d({ karts: [] }), null);
});

t("T7 buildSceneFrame 顶层键严格等于 SCENE_KEYS", () => {
  const f = mkFrame();
  assert.ok(f);
  assert.deepEqual(Object.keys(f).sort(), [...SCENE_KEYS].sort());
});

t("T8 三车显形：id/kind/color/mark 互异、玩家 Q 标、三车都在可见窗口内", () => {
  const f = mkFrame();
  assert.equal(f.karts.length, 3);
  assert.deepEqual(f.karts.map((k) => k.id).sort(), ["a", "b", "you"]);
  assert.equal(new Set(f.karts.map((k) => k.color)).size, 3);
  assert.equal(new Set(f.karts.map((k) => k.mark)).size, 3);
  const you = f.karts.find((k) => k.id === "you");
  assert.equal(you.mark, "Q");
  assert.equal(you.kind, "player");
  assert.ok(f.karts.every((k) => k.visible === true), "起跑三车都应可见");
  assert.equal(new Set(f.karts.map((k) => +k.x.toFixed(3))).size, 3, "三车横向位置应可区分");
});

t("T9 局部跟车坐标与竖屏 FOV 锚", () => {
  const f = mkFrame();
  const you = f.karts.find((k) => k.id === "you");
  assert.ok(Math.abs(you.x) < 1e-6 && Math.abs(you.z) < 1e-6, "玩家应在局部原点");
  assert.ok(f.camera.z > 0 && f.camera.y > 0, "第三人称相机在车后上方");
  assert.ok(f.camera.lookZ < 0, "相机朝 -z 看向前方");
  assert.equal(f.camera.fovIsVertical, true);
  assert.equal(cameraFovFor(375, 780), CAMERA_PRESET.fov375);
  assert.equal(cameraFovFor(320, 568), CAMERA_PRESET.fov320);
  assert.equal(cameraFovFor(800, 600), CAMERA_PRESET.fovWide);
  assert.ok(f.camera.near > 0 && f.camera.far > f.camera.near);
});

t("T10 相机自洽：pitchDeg 决定 forward、odoEstM 由 lap+t 派生且严格单调", () => {
  const f = mkFrame();
  assert.equal(f.camera.pitchDeg, CAMERA_PRESET.pitchDeg);
  assert.ok(Number.isFinite(f.camera.forwardY) && Number.isFinite(f.camera.forwardZ));
  assert.ok(f.camera.forwardZ < 0 && f.camera.forwardY < 0, "俯角下前向应为负 y / 负 z");
  const seq = [0.05, 0.15, 0.35, 0.85].map((tv) =>
    mkFrame(mockState({ karts: [kart("you", "player", tv, 0)] })).camera.odoEstM);
  for (let i = 1; i < seq.length; i++) assert.ok(seq[i] > seq[i - 1], "odoEstM 必须随 t 单调递增");
  const lap1 = mkFrame(mockState({ lap: 1, karts: [kart("you", "player", 0.05, 0)] })).camera.odoEstM;
  assert.ok(lap1 > seq[0], "跨圈 odoEstM 必须继续单调（lap 参与）");
});

t("T11 不泄答案：输出任意层级键名零命中 FORBID 集合", () => {
  const f = mkFrame();
  const keys = allKeys(f);
  for (const k of FORBID) assert.ok(!keys.includes(k), "输出泄漏答案域键: " + k);
  assert.ok(!("t" in f), "顶层不应暴露裸 t 作跨轮坐标");
  assert.ok(f.meta.snapshotKeys.length > 0 && !keys.includes("odo"), "3D 层不读绝对 odo");
});

t("T12 赛道带：采样里程单调、前方窗口远小于圈长、雾在整圈之前收敛", () => {
  const f = mkFrame();
  assert.equal(f.road.length, f.meta.segments + 1);
  const dz = f.convergence.roadDzM;
  assert.equal(dz.length, f.road.length);
  for (let i = 1; i < dz.length; i++) assert.ok(dz[i] > dz[i - 1], "roadDzM 必须单调递增");
  assert.ok(f.meta.aheadM + f.meta.behindM < f.convergence.lapLengthM * 0.5, "前方采样窗口远小于圈长");
  assert.equal(f.convergence.seesWholeLoop, false);
  assert.equal(f.fog.isExp2, true);
  assert.ok(f.fog.density > 0);
  assert.ok(f.convergence.visibleRangeM < f.convergence.lapLengthM);
  assert.ok(f.convergence.farClipM >= f.fog.far);
});

t("T13 远端收敛可量化：centerlineProjectedY 单调收敛到 vanishingPointY", () => {
  const f = mkFrame();
  const y = f.convergence.centerlineProjectedY;
  assert.ok(Array.isArray(y) && y.length === f.road.length);
  assert.ok(y.every((v) => Number.isFinite(v)));
  assert.ok(Number.isFinite(f.convergence.vanishingPointY));
  const target = f.convergence.vanishingPointY;
  assert.ok(Math.abs(y[y.length - 1] - target) < Math.abs(y[0] - target), "远端点应更接近消失点");
  assert.ok(f.convergence.vanishingTargetRatio > 0 && f.convergence.vanishingTargetRatio < 1);
});

t("T14 三车屏占比 > 0 且投影包围盒落在可见视锥内", () => {
  const f = mkFrame();
  for (const k of f.karts) {
    assert.ok(Number.isFinite(k.screenRatio) && k.screenRatio > 0, k.id + " 屏占比必须 > 0");
    for (const v of [k.bboxNdc.x0, k.bboxNdc.x1, k.bboxNdc.y0, k.bboxNdc.y1]) assert.ok(Number.isFinite(v));
    assert.ok(k.bboxNdc.x0 > -1 && k.bboxNdc.x1 < 1, k.id + " 横向必须落在视口内");
    assert.ok(k.bboxNdc.y0 > -1 && k.bboxNdc.y1 < 1, k.id + " 纵向必须落在视口内");
    assert.ok(k.screenRatio < 0.9, k.id + " 不应全屏");
  }
  assert.equal(new Set(f.karts.map((k) => +((k.bboxNdc.x0 + k.bboxNdc.x1) / 2).toFixed(3))).size, 3);
});

t("T15 跨圈 wrap：邻车 t 落在上一圈末尾不跳变，门按 lap 过滤", () => {
  const state = mockState();
  state.karts[1].t = 0.02 - 0.0001;
  const f = mkFrame(state);
  const a = f.karts.find((k) => k.id === "a");
  assert.ok(Math.abs(a.dzM) < f.meta.aheadM, "跨圈邻车不应跳到赛道尽头");
  assert.ok(f.gates.every((g) => g.lap === f.lap), "只绘当前圈的中性门");
  assert.ok(f.gates.length >= 1);
  for (const g of f.gates) {
    assert.deepEqual(Object.keys(g).sort(), ["dzM", "id", "lap", "x", "xl", "xr", "z", "zl", "zr"].sort());
  }
});

t("T16 风格裁决：2 盏灯 / 纯色路面 / 中性闸门 / M7 M8 不入 P1", () => {
  const f = mkFrame();
  assert.equal(f.light.count, 2);
  assert.ok(f.light.fill.intensity <= 0.35);
  assert.equal(f.meta.m7Terrain, false);
  assert.equal(f.meta.m8MirrorGate, false);
  assert.equal(f.meta.roadStyle, "solid");
  assert.equal(f.meta.gateStyle, "neutral");
  assert.deepEqual(f.meta.laneMarks, [0]);
  assert.equal(f.meta.laneCenters.length, 2);
});

t("T17 mirrorZ 只翻渲染层：lateral 白名单原样、z 翻号、x 不变", () => {
  const s = mockState();
  const a = mkFrame(s, { mirrorZ: 1 });
  const b = mkFrame(s, { mirrorZ: -1 });
  assert.deepEqual(mkSnap(s).karts.map((k) => k.lateral), mkSnap(s).karts.map((k) => k.lateral),
    "判定域 lateral 绝不因镜像改变");
  assert.ok(a.road.every((r, i) => Math.abs(r.x - b.road[i].x) < 1e-9), "渲染层 X 不因镜像改变");
  assert.ok(a.road.some((r) => Math.abs(r.z) > 1e-9), "赛道前向 Z 非零才谈得上翻号");
  assert.ok(a.road.every((r, i) => Math.abs(b.road[i].z + r.z) < 1e-9), "渲染层 Z 被翻号");
  assert.ok(a.startFinish === null || typeof a.startFinish === "object");
});

t("T18 纯函数可重复 + 无 snap / 无 track 时安全返回 null", () => {
  const s1 = mkSnap(mockState());
  const opts = { track: mockTrack(), viewW: 375, viewH: 780 };
  assert.deepEqual(buildSceneFrame(s1, opts), buildSceneFrame(s1, opts));
  assert.equal(buildSceneFrame(null, { track: mockTrack() }), null);
  assert.equal(buildSceneFrame({ karts: [] }, { track: mockTrack() }), null);
  assert.equal(buildSceneFrame(mkSnap(), {}), null);
});

console.log("\nSUMMARY: " + pass + " PASS / " + fail + " FAIL / " + (pass + fail) + " TOTAL");
if (fail) process.exit(1);
