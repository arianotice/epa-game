/* Task #19 / CSEG-P0 · R3F 探针（独立入口 / opt-in）
 *
 * 边界（p0-slice-spec.md §1 裁决 1 / §2 做 2）：
 *  - 本文件是 probe.html 的独立渲染层。主站 index.html 不加载它，2D 是默认且唯一的 L0 主形态。
 *  - 不 import js/main.js、不读 race.state、不订阅 requestAnimationFrame(frame)、
 *    不写 localStorage、不消费任何判定结果。判定核心（race.js / track.js / config.js）
 *    保持独立原生 JS ESM，逐字不改。
 *  - 本探针自己的 Canvas 渲染循环是隔离的视觉循环，与判定主循环零共享；
 *    P1 起若要渲染赛道，只能通过 race.snapshot() 只读字段白名单（沿用 minimapModel(view)
 *    的几何域），绝不写回 odo / lateral / g.line。
 *  - 不引 Rapier / GLB / Polyspoon / CDN；只用已钉定的 react + three + @react-three/fiber。
 *  - 全文不含源码层缓存 tag 字面量，避免污染 S17 的 46 处计数。
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

const VENDOR_TAG = typeof __P0_VENDOR_TAG__ === "string" ? __P0_VENDOR_TAG__ : "p0-20261109";

/* 浏览器实测可观测状态（Go/No-Go「3D 探针可用」判据）。 */
const STATE = window.__P0_PROBE__ = {
  tag: VENDOR_TAG,
  mounted: false,
  webgl: false,
  webglVendor: "",
  webglRenderer: "",
  fogType: "",
  fogIsExp2: false,
  fogDensity: null,
  lightCount: null,
  boxCount: null,
  drawCalls: null,
  frames: 0,
  contextLost: false,
  errors: [],
};

/* 场景内向 STATE 汇报一次真实 three 状态（不是硬编码的假值）。 */
function ProbeScene() {
  const { gl, scene } = useThree();
  const meshRef = useRef(null);

  useEffect(() => {
    try {
      const ctx = gl.getContext();
      STATE.webgl = !!ctx && typeof ctx.getParameter === "function";
      STATE.webglRenderer = String(gl.capabilities && gl.capabilities.isWebGL2 ? "WebGL2" : "WebGL1");
      if (ctx && ctx.getParameter) {
        const ext = ctx.getExtension("WEBGL_debug_renderer_info");
        STATE.webglVendor = ext ? String(ctx.getParameter(ext.UNMASKED_RENDERER_WEBGL)) : String(ctx.getParameter(ctx.RENDERER));
      }
      // 类名在 build minify 后会变成 K_ / _FogExp2，故用 three 的 isFogExp2 布尔标记判定
      STATE.fogType = scene.fog ? scene.fog.constructor.name : "none";
      STATE.fogIsExp2 = !!(scene.fog && scene.fog.isFogExp2);
      STATE.fogDensity = scene.fog && typeof scene.fog.density === "number" ? scene.fog.density : null;
      STATE.lightCount = scene.children.filter((o) => o && o.isLight).length;
      STATE.boxCount = scene.children.filter((o) => o && o.isMesh && o.geometry && o.geometry.type === "BoxGeometry").length;
      const canvas = gl.domElement;
      canvas.addEventListener("webglcontextlost", (e) => { e.preventDefault(); STATE.contextLost = true; });
    } catch (err) {
      STATE.errors.push(String(err && err.message ? err.message : err));
    }
  }, [gl, scene]);

  useFrame(() => {
    STATE.frames += 1;
    if (STATE.frames === 3) STATE.drawCalls = gl.info && gl.info.render ? gl.info.render.calls : null;
    if (meshRef.current) {
      meshRef.current.rotation.y += 0.006;
      meshRef.current.rotation.x += 0.003;
    }
  });

  return (
    <>
      {/* 甲 · 立体书：纸雾收敛（FogExp2），不使用 postprocessing / 全屏 bloom */}
      <fogExp2 attach="fog" args={["#efe6d3", 0.045]} />
      {/* 单一暖主光：不加第二光源、不加硬高光点 */}
      <directionalLight color="#ffd6a0" intensity={2.1} position={[3.2, 4.5, 5]} />
      <mesh ref={meshRef}>
        <boxGeometry args={[1.5, 1.5, 1.5]} />
        <meshStandardMaterial color="#d98f5b" roughness={0.82} metalness={0.02} />
      </mesh>
    </>
  );
}

function ProbeApp({ onReady }) {
  const [on, setOn] = useState(true);

  useEffect(() => {
    STATE.mounted = true;
    if (typeof onReady === "function") onReady(setOn);
  }, [onReady]);

  useEffect(() => { STATE.mounted = !!on; }, [on]);

  return (
    <>
      {on && (
        <Canvas
          dpr={[1, 2]}
          gl={{ antialias: true, alpha: false, powerPreference: "low-power" }}
          camera={{ position: [0, 0, 4.2], fov: 50 }}
          onCreated={({ gl }) => {
            try { gl.setClearColor("#efe6d3"); } catch (_) { /* noop */ }
          }}
          style={{ width: "100%", height: "100%", display: "block" }}
        >
          <ProbeScene />
        </Canvas>
      )}
    </>
  );
}

const rootEl = document.getElementById("probe-root");
const statusEl = document.getElementById("probe-status");
const toggleEl = document.getElementById("probe-toggle");

function renderStatus() {
  if (!statusEl) return;
  statusEl.textContent = [
    `VENDOR_TAG=${STATE.tag}`,
    `webgl=${STATE.webgl}`,
    `renderer=${STATE.webglRenderer || "-"}`,
    `fog=${STATE.fogType || "-"}@${STATE.fogDensity === null ? "-" : STATE.fogDensity}`,
    `lights=${STATE.lightCount === null ? "-" : STATE.lightCount}`,
    `boxes=${STATE.boxCount === null ? "-" : STATE.boxCount}`,
    `frames=${STATE.frames}`,
    `drawCalls=${STATE.drawCalls === null ? "-" : STATE.drawCalls}`,
    `mounted=${STATE.mounted}`,
    `contextLost=${STATE.contextLost}`,
  ].join(" | ");
}

let root = null;
function mount() {
  if (root) return;
  root = createRoot(rootEl);
  root.render(<ProbeApp onReady={(setOn) => {
    if (toggleEl) {
      toggleEl.addEventListener("click", () => {
        setOn((v) => !v);
        STATE.mounted = toggleEl.getAttribute("aria-pressed") === "true" ? false : true;
        const next = toggleEl.getAttribute("aria-pressed") !== "true";
        toggleEl.setAttribute("aria-pressed", String(next));
        toggleEl.textContent = next ? "关闭 3D 探针" : "开启 3D 探针";
      });
    }
  }} />);
}

try {
  mount();
} catch (err) {
  STATE.errors.push(String(err && err.message ? err.message : err));
  if (statusEl) statusEl.textContent = "PROBE FAILED: " + STATE.errors.join("; ");
}

/* 状态轮询：只更新文本，不驱动 3D、不进判定主循环。 */
const timer = setInterval(renderStatus, 250);
window.addEventListener("beforeunload", () => clearInterval(timer), { once: true });
