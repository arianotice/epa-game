/* Task #28 / P1 · 3D 卡丁车主形态（R3F 场景 + 命令式 three 内容）
 *
 * 边界（p0-slice-spec.md 裁决 1 / 3d-adr.md ADR-2 / p1-gameplay-spec.md §1.4）：
 *  - 本文件是主站默认 3D 渲染层；2D render() 保留为 L0 应急降级层，且**始终在跑**，
 *    因此「降级」= 卸载本层 overlay，2D 立即可见、不白屏。
 *  - 只读：唯一接触判定域的入口是 scene3d-model.mjs:snapshot3d() 的白名单投影；
 *    只读 window.__rally 的 mode / race.state，绝不写回 odo / lateral / 门线；
 *    不写 localStorage；不调用 race.update()；不进 main.js 的 frame() 判定主循环。
 *  - 独立视觉循环：R3F useFrame 是 R3F 内部 loop；本文件另起一条 rAF 只做「何时挂载」
 *    的决策，与 main.js frame() 零共享。
 *  - 答案域零进入：本文件与 scene3d-model.mjs 都不出现任何答案域字段名/词面；
 *    几何、材质、路牌、门一律中性，不承载任何可推导答案的信息。
 *  - 延迟挂载：title / teach 不创建 WebGL 上下文（保住 P0 BR-1）；
 *    countdown / racing / paused / quiz 才挂载，用户「点开始后车显现」由此满足。
 *  - 降级：WebGL 不可用 / webglcontextlost / 一键回退 → 自动回 2D L0，有可观测标识。
 *  - 不引 GLB / 社区模型 / CDN / postprocessing；只用已钉定的 react + three + r3f。
 *  - 全文不含源码层缓存 tag 字面量，也不含任何图片 URL 字面量（S17 / S18 不污染）。
 */
import React, { useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import {
  P1_TAG, FOG_COLOR, FOG_DENSITY, NEAR_CLIP, FAR_CLIP,
  CAMERA_PRESET, LIGHT_PRESET, KART_STYLE,
  SNAPSHOT_KEYS, KART_KEYS, GATE_KEYS,
  snapshot3d, buildSceneFrame,
} from "./scene3d-model.mjs";

/* ---- QA 只读可观测接口（quality-lead #31 的 ①–⑤ 输入，类比 __P0_PROBE__） ----
 * 纯数值 / 纯字符串，可直接 JSON 序列化；不是「Canvas 存在」这类伪证据。
 */
const STATE = window.__P1_SCENE__ = {
  tag: P1_TAG,
  renderMode: "3d",            // 3d（主形态）| 2d（一键回退 / 降级）
  mounted: false,              // R3F Canvas 当前是否已挂载
  webgl: false,
  webglVersion: "",
  webglVendor: "",
  webglRenderer: "",
  meshCount: 0,                // scene 内 isMesh 总数（每 6 帧刷新）
  kartMeshCount: 0,             // 三车 group 内 mesh 总数
  kartIds: [],                  // 三车 id，可区分
  drawCalls: 0,                 // gl.info.render.calls，上一帧真实值
  kartScreenRatio: {},          // 三车真实投影包围盒面积 / 视口面积
  kartProjected: {},            // 三车真实 NDC 包围盒
  frames: 0,
  cameraOdoEstM: 0,             // 跟随单调的可观测量（由 lap + t 派生，非判定域 odo）
  camera: {},
  convergence: {},
  fog: { isExp2: false, density: null },
  light: { count: 0, main: 0, fill: 0 },
  lap: 0, laps: 2, progress: 0,
  snapshotKeys: [...SNAPSHOT_KEYS],
  kartKeys: [...KART_KEYS],
  gateKeys: [...GATE_KEYS],
  snapshot3dSource: "js/scene3d-model.mjs:snapshot3d()",
  rafSource: "r3f useFrame + 独立 mount-decision rAF（与 main.js frame() 分离）",
  storageWrites: 0,            // 本层零 Storage 写入点；QA 静态扫描 + 运行时 hook 双重验证
  contextLost: false,
  degraded: false,
  degradeReason: "",
  forced2d: false,
  mirrorZ: 1,
  errors: [],
};

const ACTIVE_MODES = ["countdown", "racing", "paused", "quiz"];

function queryForced2d() {
  try {
    const q = new URLSearchParams(window.location.search);
    return q.get("p1") === "off" || q.get("render") === "2d";
  } catch { return false; }
}

/* 唯一读取判定域的函数：白名单投影 → 纯几何场景帧。不复制 state、不写回。 */
function readFrame() {
  const r = window.__rally;
  if (!r || !r.race || !r.race.state) return null;
  const st = r.race.state;
  const snap = snapshot3d(st);
  if (!snap) return null;
  return buildSceneFrame(snap, {
    track: st.track,
    viewW: window.innerWidth,
    viewH: window.innerHeight,
    mirrorZ: STATE.mirrorZ,
  });
}

/* ---- 共享几何 / 材质（控 draw call，零外部资源） ---- */
const GEO = {
  box: new THREE.BoxGeometry(1, 1, 1),
  cyl: new THREE.CylinderGeometry(0.21, 0.21, 0.16, 12),
  hub: new THREE.CylinderGeometry(0.07, 0.07, 0.165, 12),
  head: new THREE.SphereGeometry(0.16, 16, 12),
  lamp: new THREE.SphereGeometry(0.08, 10, 8),
  octa: new THREE.OctahedronGeometry(0.12),
  disc: new THREE.CylinderGeometry(0.26, 0.26, 0.04, 16),
  spare: new THREE.CylinderGeometry(0.24, 0.24, 0.10, 14),
  fin: new THREE.TorusGeometry(0.24, 0.035, 8, 16, Math.PI),
  post: new THREE.BoxGeometry(1, 1, 1),
};
const MAT = {
  chassis: new THREE.MeshStandardMaterial({ color: "#3a332c", roughness: 0.90, metalness: 0 }),
  wheel:   new THREE.MeshStandardMaterial({ color: "#6e655b", roughness: 0.95, metalness: 0 }),
  gold:    new THREE.MeshStandardMaterial({ color: "#c9a227", roughness: 0.35, metalness: 0.78 }),
  cream:   new THREE.MeshStandardMaterial({ color: "#f6ead0", roughness: 0.85, metalness: 0 }),
  head:    new THREE.MeshStandardMaterial({ color: "#e8c9a0", roughness: 0.90, metalness: 0 }),
  lamp:    new THREE.MeshStandardMaterial({ color: "#b03a2e", roughness: 0.55, metalness: 0 }),
  ink:     new THREE.MeshStandardMaterial({ color: "#23364E", roughness: 0.92, metalness: 0 }),
  road:    new THREE.MeshStandardMaterial({ color: "#C9AE82", roughness: 0.90, metalness: 0, side: THREE.DoubleSide }),
  dash:    new THREE.MeshStandardMaterial({ color: "#f6ead0", roughness: 0.90, metalness: 0 }),
  gate:    new THREE.MeshStandardMaterial({ color: "#f6ead0", roughness: 0.88, metalness: 0 }),
  gateTrim:new THREE.MeshStandardMaterial({ color: "#b99b6b", roughness: 0.70, metalness: 0 }),
};

/* art-spec §3.1 的 16 部件表；表以「车头 +Z」书写，本局部系前向为 -z，
   故整组套一层 rotation.y=PI 的 body group（只翻渲染层，绝不动判定域 lateral）。 */
const PROFILE = {
  player: { bodyH: 0.42, rollY: 0.92, headY: 0.98, shoulderY: 0.80, wingY: 0.92 },
  a:      { bodyH: 0.30, rollY: 0.52, headY: 0.58, shoulderY: 0.48, wingY: 0.64 },
  b:      { bodyH: 0.38, rollY: 0.74, headY: 0.86, shoulderY: 0.70, wingY: 0.82 },
};
function mesh(geo, mat, scale, pos) {
  const m = new THREE.Mesh(geo, mat);
  m.scale.set(scale[0], scale[1], scale[2]);
  m.position.set(pos[0], pos[1], pos[2]);
  return m;
}
function createKart(id) {
  const p = PROFILE[id] || PROFILE.a;
  const style = KART_STYLE[id] || KART_STYLE.a;
  const bodyMat = new THREE.MeshStandardMaterial({ color: style.color, roughness: 0.80, metalness: 0 });
  const trimMat = new THREE.MeshStandardMaterial({ color: style.trim, roughness: 0.85, metalness: 0 });
  const outer = new THREE.Group();
  const body = new THREE.Group();
  body.rotation.y = Math.PI;
  outer.add(body);
  const add = (m) => { body.add(m); return m; };

  add(mesh(GEO.box, MAT.chassis, [1.00, 0.18, 1.60], [0, 0.28, 0]));            // 1 chassis
  add(mesh(GEO.box, bodyMat, [0.92, p.bodyH, 1.40], [0, 0.48, 0.05]));           // 2 body
  add(mesh(GEO.box, bodyMat, [0.70, 0.22, 0.42], [0, 0.40, 0.86]));              // 3 nose
  add(mesh(GEO.box, MAT.cream, [0.60, 0.30, 0.55], [0, 0.68, -0.12]));          // 4 seat
  add(mesh(GEO.box, trimMat, [0.66, 0.34, 0.10], [0, p.rollY, -0.40]));          // 5 roll_bar
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {                         // 6–9 wheels
    const w = add(mesh(GEO.cyl, MAT.wheel, [1, 1, 1], [sx * 0.56, 0.21, sz * 0.52]));
    w.rotation.z = Math.PI / 2;
    const h = add(mesh(GEO.hub, MAT.gold, [1, 1, 1], [sx * 0.565, 0.21, sz * 0.52])); // 10 hub cap
    h.rotation.z = Math.PI / 2;
  }
  add(mesh(GEO.box, MAT.cream, [0.34, 0.20, 0.02], [0, 0.52, -0.79]));           // 12 空白编号牌（无字母）
  for (const sx of [-1, 1]) add(mesh(GEO.octa, trimMat, [1, 1, 1], [sx * 0.47, 0.50, 0.10])); // 13 空白徽章位
  add(mesh(GEO.head, MAT.head, [1, 1, 1], [0, p.headY, -0.10]));                 // 14 head
  add(mesh(GEO.box, bodyMat, [0.42, 0.20, 0.24], [0, p.shoulderY, -0.10]));       // 15 shoulder
  if (id === "player") {                                                          // 16 玩家专属：最高剪影
    add(mesh(GEO.disc, MAT.gold, [1, 1, 1], [0, 1.12, -0.20]));                    // 罗盘盘 / 行李架
    const spare = add(mesh(GEO.spare, MAT.wheel, [1, 1, 1], [0, 0.55, -0.86]));    // 后置备胎
    spare.rotation.x = Math.PI / 2;
    add(mesh(GEO.box, trimMat, [0.90, 0.06, 0.18], [0, p.wingY, -0.72]));         // 高尾翼
  } else if (id === "a") {                                                            // NPC A：最矮、翘尾翼、双圆尾灯
    const wing = add(mesh(GEO.box, trimMat, [0.66, 0.05, 0.20], [0, p.wingY, -0.76]));
    wing.rotation.x = -0.28;
    for (const sx of [-1, 1]) add(mesh(GEO.lamp, MAT.lamp, [1, 1, 1], [sx * 0.30, 0.60, -0.78]));
  } else {                                                                            // NPC B：中高、弧形尾鳍、对称双灯
    const fin = add(mesh(GEO.fin, trimMat, [1, 1, 1], [0, p.wingY, -0.72]));
    fin.rotation.y = Math.PI / 2;
    for (const sx of [-1, 1]) add(mesh(GEO.lamp, MAT.cream, [1, 1, 1], [sx * 0.30, 0.62, -0.78]));
  }
  outer.name = "p1-kart-" + id;
  outer.userData.kartId = id;
  return { group: outer, count: body.children.length };
}

function createGateSlot(scene) {
  const g = new THREE.Group();
  for (const sx of [-1, 1]) {
    g.add(mesh(GEO.post, MAT.gate, [0.16, 2.3, 0.16], [sx * 3.9, 1.15, 0]));
    g.add(mesh(GEO.post, MAT.gateTrim, [0.24, 0.16, 0.24], [sx * 3.9, 2.32, 0]));
  }
  g.add(mesh(GEO.post, MAT.gate, [8.0, 0.18, 0.18], [0, 2.34, 0]));   // 横梁
  g.add(mesh(GEO.post, MAT.cream, [1.5, 0.7, 0.06], [0, 1.95, 0.1])); // 空白牌位（无文字）
  g.visible = false;
  scene.add(g);
  return g;
}

function createWorld(scene) {
  scene.background = new THREE.Color(FOG_COLOR);
  scene.fog = new THREE.FogExp2(FOG_COLOR, FOG_DENSITY);
  const main = new THREE.DirectionalLight(LIGHT_PRESET.main.color, LIGHT_PRESET.main.intensity);
  main.position.set(LIGHT_PRESET.main.position[0], LIGHT_PRESET.main.position[1], LIGHT_PRESET.main.position[2]);
  const fill = new THREE.AmbientLight(LIGHT_PRESET.fill.color, LIGHT_PRESET.fill.intensity);
  scene.add(main, fill);

  const SEG = 48;
  const roadGeo = new THREE.BufferGeometry();
  roadGeo.setAttribute("position", new THREE.BufferAttribute(new Float32Array((SEG + 1) * 2 * 3), 3));
  const idx = [];
  for (let i = 0; i < SEG; i++) {
    const a = i * 2, b = a + 1, c = a + 2, d = a + 3;
    idx.push(a, b, c, b, d, c);
  }
  roadGeo.setIndex(idx);
  const road = new THREE.Mesh(roadGeo, MAT.road);
  road.frustumCulled = false;
  scene.add(road);
  const dashes = new THREE.InstancedMesh(new THREE.BoxGeometry(0.14, 0.012, 0.85), MAT.dash, 40);
  dashes.frustumCulled = false;
  scene.add(dashes);

  const karts = {};
  let kartMeshCount = 0;
  for (const id of ["you", "a", "b"]) {
    const k = createKart(id === "you" ? "player" : id);
    karts[id] = k;
    kartMeshCount += k.count;
    scene.add(k.group);
  }
  const gates = [createGateSlot(scene), createGateSlot(scene), createGateSlot(scene), createGateSlot(scene)];
  const startFinish = createGateSlot(scene);
  const dummy = new THREE.Object3D();

  return {
    lightCount: 2,
    kartMeshCount,
    karts,
    update(f) {
      const pos = roadGeo.attributes.position;
      const n = Math.min(f.road.length, SEG + 1);
      for (let i = 0; i < n; i++) {
        const r = f.road[i], w = r.w;
        pos.setXYZ(i * 2, r.x - r.nx * w, 0, r.z - r.nz * w);
        pos.setXYZ(i * 2 + 1, r.x + r.nx * w, 0, r.z + r.nz * w);
      }
      pos.needsUpdate = true;
      roadGeo.computeBoundingSphere();
      MAT.road.color.set(f.meta.zoneColor.road);
      MAT.gateTrim.color.set(f.meta.zoneColor.curb);
      let nd = 0;
      for (let i = 0; i < n && nd < 40; i += 2) {
        const r = f.road[i];
        dummy.position.set(r.x, 0.014, r.z);
        dummy.rotation.set(0, Math.atan2(-r.nz, -r.nx), 0);
        dummy.scale.set(1, 1, 1);
        dummy.updateMatrix();
        dashes.setMatrixAt(nd++, dummy.matrix);
      }
      dashes.count = nd;
      dashes.instanceMatrix.needsUpdate = true;
      for (const k of f.karts) {
        const obj = karts[k.id];
        if (!obj) continue;
        obj.group.visible = k.visible;
        obj.group.position.set(k.x, k.lift || 0, k.z);
        obj.group.rotation.y = Math.atan2(k.dirX, -k.dirZ);
      }
      gates.forEach((slot, i) => {
        const g = f.gates[i];
        slot.visible = !!g;
        if (g) slot.position.set(g.x, 0, g.z);
      });
      startFinish.visible = !!f.startFinish;
      if (f.startFinish) startFinish.position.set(f.startFinish.x, 0, f.startFinish.z);
    },
    dispose() {
      /* 场景卸载时移除本层对象；共享几何/材质是模块级单例，交给 GC/页面生命周期。 */
      scene.remove(road, dashes, main, fill, startFinish, ...gates, ...Object.values(karts).map((k) => k.group));
      scene.fog = null;
      scene.background = null;
      roadGeo.dispose();
    },
  };
}

/* ---- 每帧把真实 WebGL 状态发布到 STATE（不是硬编码假值） ---- */
function publish(f, world, gl, camera, scene) {
  STATE.frames += 1;
  STATE.drawCalls = gl.info.render.calls;
  gl.info.reset();
  if (STATE.frames % 6 === 0) {
    let n = 0;
    scene.traverse((o) => { if (o.isMesh) n += 1; });
    STATE.meshCount = n;
  }
  STATE.kartMeshCount = world.kartMeshCount;
  STATE.kartIds = f.karts.map((k) => k.id);
  const ratio = {};
  for (const k of f.karts) {
    const obj = world.karts[k.id];
    if (!obj || !obj.group.visible) {
      ratio[k.id] = 0;
      STATE.kartProjected[k.id] = null;
      continue;
    }
    const bb = new THREE.Box3().setFromObject(obj.group);
    const pts = [];
    for (const x of [bb.min.x, bb.max.x]) for (const y of [bb.min.y, bb.max.y]) for (const z of [bb.min.z, bb.max.z]) {
      pts.push(new THREE.Vector3(x, y, z).project(camera));
    }
    const x0 = Math.min(...pts.map((p) => p.x)), x1 = Math.max(...pts.map((p) => p.x));
    const y0 = Math.min(...pts.map((p) => p.y)), y1 = Math.max(...pts.map((p) => p.y));
    ratio[k.id] = +(((x1 - x0) * (y1 - y0)) / 4).toFixed(6);
    STATE.kartProjected[k.id] = {
      x0: +x0.toFixed(4), y0: +y0.toFixed(4), x1: +x1.toFixed(4), y1: +y1.toFixed(4),
    };
  }
  STATE.kartScreenRatio = ratio;
  STATE.cameraOdoEstM = +f.camera.odoEstM.toFixed(3);
  STATE.camera = {
    x: f.camera.x, y: f.camera.y, z: f.camera.z,
    lookX: f.camera.lookX, lookY: f.camera.lookY, lookZ: f.camera.lookZ,
    pitchDeg: f.camera.pitchDeg, fov: f.camera.fov, fovIsVertical: f.camera.fovIsVertical,
    near: f.camera.near, far: f.camera.far,
    heightM: f.camera.heightM, distanceM: f.camera.distanceM, lookAheadM: f.camera.lookAheadM,
  };
  STATE.convergence = {
    seesWholeLoop: f.convergence.seesWholeLoop,
    visibleRangeM: +f.convergence.visibleRangeM.toFixed(3),
    lapLengthM: +f.convergence.lapLengthM.toFixed(3),
    farClipM: f.convergence.farClipM,
    vanishingPointY: f.convergence.vanishingPointY,
    centerlineProjectedY: f.convergence.centerlineProjectedY,
    roadDzM: f.convergence.roadDzM,
  };
  STATE.fog = {
    isExp2: !!(scene.fog && scene.fog.isFogExp2 === true),   // 布尔判据，不用类名 / constructor.name
    density: scene.fog ? scene.fog.density : null,
  };
  STATE.light = { count: 2, main: LIGHT_PRESET.main.intensity, fill: LIGHT_PRESET.fill.intensity };
  STATE.lap = f.lap;
  STATE.laps = f.laps;
  STATE.progress = +f.progress.toFixed(4);
}

/* ---- 错误边界：WebGL 创建失败 → 自动降级 2D L0，不白屏 ---- */
class Boundary extends React.Component {
  constructor(props) { super(props); this.state = { failed: false }; }
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(err) { degrade("webgl-create-failed: " + String(err && err.message)); }
  render() { return this.state.failed ? null : this.props.children; }
}

function onCreated({ gl, scene }) {
  const ctx = gl.getContext();
  STATE.webgl = !!ctx;
  if (ctx) {
    STATE.webglVersion = String(ctx.getParameter(ctx.VERSION) || "");
    STATE.webglVendor = String(ctx.getParameter(ctx.VENDOR) || "");
    STATE.webglRenderer = String(ctx.getParameter(ctx.RENDERER) || "");
  }
  gl.info.autoReset = false;
  const canvas = gl.domElement;
  canvas.style.pointerEvents = "none";
  canvas.addEventListener("webglcontextlost", (ev) => {
    ev.preventDefault();
    STATE.contextLost = true;
    degrade("webglcontextlost");
  });
  canvas.addEventListener("webglcontextrestored", () => { STATE.contextLost = false; });
  const lose = ctx && ctx.getExtension("WEBGL_lose_context");
  STATE.simulateContextLoss = () => {
    if (lose) lose.loseContext();
    else degrade("webgl-lose-context-unavailable");
  };
  STATE.fog = {
    isExp2: !!(scene.fog && scene.fog.isFogExp2 === true),
    density: scene.fog ? scene.fog.density : null,
  };
}

function SceneContent() {
  const { gl, scene, camera, size } = useThree();
  const worldRef = useRef(null);
  useEffect(() => {
    const world = createWorld(scene);
    worldRef.current = world;
    return () => { world.dispose(); worldRef.current = null; };
  }, [scene]);
  useFrame(() => {
    const f = readFrame();
    if (!f || !worldRef.current) return;
    camera.fov = f.camera.fov;
    camera.aspect = Math.max(0.1, size.width / Math.max(1, size.height));
    camera.near = f.camera.near;
    camera.far = f.camera.far;
    camera.position.set(f.camera.x, f.camera.y, f.camera.z);
    camera.lookAt(f.camera.lookX, f.camera.lookY, f.camera.lookZ);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld(true);
    worldRef.current.update(f);
    publish(f, worldRef.current, gl, camera, scene);
  });
  return null;
}

function P1Canvas() {
  return (
    <Boundary>
      <Canvas
        dpr={[1, 1.75]}
        gl={{ antialias: false, alpha: false, powerPreference: "low-power" }}
        camera={{
          fov: CAMERA_PRESET.fov375, near: NEAR_CLIP, far: FAR_CLIP,
          position: [0, CAMERA_PRESET.heightM, CAMERA_PRESET.distanceM],
        }}
        onCreated={onCreated}
        style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }}
      >
        <SceneContent />
      </Canvas>
    </Boundary>
  );
}

/* ---- 挂载宿主：fixed 全屏、z=3（盖住 #c，低于 #signs/#tags/#hud/#minimap/#route-map），
   pointer-events:none 保证不吞掉 steer / jump / quiz / pause 的触屏点击。 ---- */
function ensureHost() {
  let host = document.getElementById("p1-stage");
  if (host) return host;
  host = document.createElement("div");
  host.id = "p1-stage";
  host.setAttribute("aria-hidden", "true");
  host.style.cssText = "position:fixed;inset:0;z-index:3;pointer-events:none;overflow:hidden;";
  const c = document.getElementById("c");
  if (c && c.nextSibling) document.body.insertBefore(host, c.nextSibling);
  else document.body.appendChild(host);
  return host;
}

const root = createRoot(ensureHost());
let mounted = false;

/* 一键回退（?p1=off / ?render=2d）：bundle 仍加载以暴露降级标识，但全程不挂载 3D。 */
if (queryForced2d() || window.__P1_OFF__ === true) {
  STATE.forced2d = true;
  STATE.renderMode = "2d";
  STATE.degradeReason = "forced-2d-via-query";
}

/* WebGL 可用性的确定性探测：只在「准备挂载」那一帧执行一次，title/teach 下绝不触发，
   因此 P0 BR-1（主站零 WebGL 上下文）不受影响。探测上下文随即 loseContext 释放，
   不残留、不计入场景上下文。headless 无 WebGL 时由此给出可观测降级标识，不白屏。 */
function webglProbe() {
  try {
    const c = document.createElement("canvas");
    const gl = c.getContext("webgl2") || c.getContext("webgl");
    if (!gl) return false;
    const ext = gl.getExtension("WEBGL_lose_context");
    if (ext) ext.loseContext();
    return true;
  } catch { return false; }
}

function degrade(reason) {
  if (STATE.degraded) return;
  STATE.degraded = true;
  STATE.degradeReason = reason;
  STATE.renderMode = "2d";
  STATE.mounted = false;
  mounted = false;
  try { root.render(null); } catch (e) { STATE.errors.push(String(e && e.message)); }
}

STATE.setRenderMode = (m) => {
  if (m === "2d") {
    STATE.forced2d = true;
    degrade("manual-2d");
  } else if (m === "3d") {
    STATE.forced2d = false;
    STATE.degraded = false;
    STATE.degradeReason = "";
    STATE.renderMode = "3d";
  }
};

/* 独立视觉决策 rAF：只判断「何时挂载」，不驱动判定、不写状态、不读答案域。
   title / teach 下不挂载 → 不创建任何 WebGL 上下文（P0 BR-1 保持不变）。 */
function shouldMount() {
  if (STATE.forced2d || queryForced2d() || STATE.degraded) return false;
  const r = window.__rally;
  return !!r && !!r.race && ACTIVE_MODES.indexOf(r.mode) >= 0;
}
function decisionLoop() {
  const want = shouldMount();
  if (want !== mounted) {
    if (want && !webglProbe()) {
      degrade("webgl-unavailable");
    } else {
      mounted = want;
      STATE.mounted = want;
      STATE.renderMode = want ? "3d" : "2d";
      try { root.render(want ? <P1Canvas /> : null); }
      catch (e) { STATE.errors.push(String(e && e.message)); degrade("react-render-failed"); }
    }
  }
  requestAnimationFrame(decisionLoop);
}
requestAnimationFrame(decisionLoop);
