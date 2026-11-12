/* CSEG-E1 / Task#4 · minimapModel(view) 纯函数 Node 单测（验证驱动：先于实现）
 * 覆盖 #4 规格 §五 点名的四类断言：坐标范围 / lap 过滤 / 四区映射 / odo/(laps·L) 进度，
 * 外加字段白名单（不泄答案）、nextGate 精确 5 键、圈数文本、两圈同 commitT 不串位。
 *
 * 运行： node js/minimap_model.test.mjs     （cwd 无关，相对 import 基于本文件目录）
 * 性质： 纯 Node 验证脚本，不被浏览器加载；.mjs 后缀不在四套门控
 *        (verify_*.py 只扫 .html/.js/.css) 的扫描范围内，不产生 ?v= 字面量 → 46 计数不变。
 */
import assert from "node:assert/strict";
import { createTrack } from "./track.js";
import { TUNING } from "./config.js";

/* 动态 import：实现前 render.js 尚未 export minimapModel，测试据此明确报 FAIL（红），
 * 实现后自动转绿；静态 import 会在加载期直接抛 SyntaxError，不利于观察红→绿。 */
const renderMod = await import("./render.js");
const minimapModel = renderMod.minimapModel;

const track = createTrack(TUNING);
const L = track.length;
let pass = 0, fail = 0;
const t = (name, fn) => {
  try { fn(); pass++; console.log("  PASS  " + name); }
  catch (e) { fail++; console.log("  FAIL  " + name + " | " + (e && e.message ? e.message : e)); }
};

/* 基准 view：全部为纯数据（无 DOM / 无 race 方法 / 无答案域），与 #1 §1.2 白名单契约一致。 */
function baseView(over = {}) {
  return {
    track,                                   // { samples:[{x,y,...}], length }
    karts: [
      { id: "you", kind: "player", odo: 385.09, lateral: 0 },
      { id: "a", kind: "rival", odo: 400, lateral: -0.55 },
      { id: "b", kind: "rival", odo: 410, lateral: 0.55 },
    ],
    activeGate: null,                        // { gate:{id,lap,line,...} } | null
    playerOdo: 385.09, startOdo: 385.09,
    lap: 0, laps: 2,
    mapId: "camp", zone: "出发营地",
    speed: 300, phase: "S0", reduced: false,
    mmW: 160, mmH: 104,                      // 内嵌 canvas 的 CSS 尺寸
    ...over,
  };
}
const baseModel = (over) => minimapModel(baseView(over));
function collectKeys(o, acc = []) {
  if (Array.isArray(o)) { o.forEach((x) => collectKeys(x, acc)); return acc; }
  if (o && typeof o === "object") {
    for (const k of Object.keys(o)) { acc.push(k); collectKeys(o[k], acc); }
  }
  return acc;
}

console.log("=== minimapModel(view) Node 单测（CSEG-E1 / TDD）===");
console.log("  track.length = " + L.toFixed(2) + "  laps = " + TUNING.laps);

/* ---- 0. 契约存在性（实现前必红） ---- */
t("T0 minimapModel 已导出为纯函数", () => {
  assert.equal(typeof minimapModel, "function", "render.js 尚未 export minimapModel");
  const a = JSON.stringify(baseModel());
  const b = JSON.stringify(baseModel());
  assert.equal(a, b, "相同输入必须产生相同输出（零副作用 / 零随机）");
});

/* ---- 1. 坐标范围（min/max→ox/oy/sc 投影落在 mm 局部坐标盒内） ---- */
t("T1 坐标范围：trackPath / karts / startAt / nextGateAt 全部落在 [0,mmW]×[0,mmH]", () => {
  const m = baseModel({ activeGate: { gate: { id: 0, lap: 0, line: 385.09 + L * 0.24 } } });
  const eps = 0.5;
  const inBox = (p) => p && Number.isFinite(p.x) && Number.isFinite(p.y) &&
    p.x >= -eps && p.x <= m.mmW + eps && p.y >= -eps && p.y <= m.mmH + eps;
  assert.ok(m.trackPath.length > 100, "trackPath 应覆盖整条环线采样");
  assert.ok(m.trackPath.every(inBox), "trackPath 存在越界点");
  assert.equal(m.karts.length, 3, "karts 数量应与输入一致");
  assert.ok(m.karts.every(inBox), "karts 存在越界点");
  assert.ok(inBox(m.startAt), "起终点越界");
  assert.ok(m.nextGateAt && inBox(m.nextGateAt), "nextGate 菱形坐标越界");
});

/* ---- 2. lap 过滤（nextGate 只认当前圈的门；两圈同 commitT 不串） ---- */
t("T2a lap 过滤：activeGate.lap !== lap → nextGate === null", () => {
  const m = baseModel({ lap: 1, activeGate: { gate: { id: 0, lap: 0, line: 385.09 + L * 0.24 } } });
  assert.equal(m.nextGate, null, "跨圈的门不得进 nextGate");
});
t("T2b lap 过滤：activeGate.lap === lap → nextGate.lap === lap 且恰好 5 键", () => {
  const line = 385.09 + L * 1.24;
  const m = baseModel({ lap: 1, playerOdo: 385.09 + L * 1.0, activeGate: { gate: { id: 2, lap: 1, line } } });
  assert.ok(m.nextGate, "当前圈门应产出 nextGate");
  assert.equal(m.nextGate.lap, 1);
  assert.deepEqual(Object.keys(m.nextGate).sort(), ["distance", "id", "lap", "line", "secondsTo"],
    "nextGate 键集合必须精确等于 {id,lap,line,distance,secondsTo}");
  assert.equal(m.nextGate.id, 2);
  assert.equal(m.nextGate.line, line);
  assert.ok(Math.abs(m.nextGate.distance - (line - (385.09 + L * 1.0))) < 1e-6);
  assert.ok(Math.abs(m.nextGate.secondsTo - m.nextGate.distance / 300) < 1e-6);
});
t("T2c 两圈同 commitT：line 相差恰好 L 时，nextGateAt 的 (line/L)%1 投影一致", () => {
  const a = baseModel({ lap: 0, activeGate: { gate: { id: 0, lap: 0, line: 385.09 + L * 0.24 } } });
  const b = baseModel({ lap: 1, activeGate: { gate: { id: 2, lap: 1, line: 385.09 + L * 1.24 } } });
  assert.ok(a.nextGateAt && b.nextGateAt);
  assert.ok(Math.abs(a.nextGateAt.x - b.nextGateAt.x) < 1e-6, "跨圈 x 不一致 → 用了 t 而非 odo 派生");
  assert.ok(Math.abs(a.nextGateAt.y - b.nextGateAt.y) < 1e-6, "跨圈 y 不一致 → 用了 t 而非 odo 派生");
});

/* ---- 3. 四区映射（mapId → 中性 zone 标签互异） ---- */
t("T3 四区映射：camp / castle / kingdom / peak → 4 个互异且非空的 zone", () => {
  const zones = ["camp", "castle", "kingdom", "peak"].map((id) => baseModel({ mapId: id }).zone);
  assert.equal(new Set(zones).size, 4, "四个 mapId 必须映射到四个不同 zone");
  assert.ok(zones.every((z) => typeof z === "string" && z.length > 0), "zone 不得为空");
});

/* ---- 4. progress = clamp((playerOdo - startOdo) / (laps·L), 0, 1)，不用 t ---- */
t("T4 进度：odo/(laps·L) 线性 + 双端 clamp + 两圈不重复", () => {
  const startOdo = 385.09, laps = 2;
  const p = (odo) => baseModel({ playerOdo: odo, startOdo, laps }).progress;
  assert.equal(p(startOdo), 0, "起点应为 0");
  assert.ok(Math.abs(p(startOdo + laps * L * 0.25) - 0.25) < 1e-9, "1/4 场应为 0.25");
  assert.ok(Math.abs(p(startOdo + laps * L * 0.5) - 0.5) < 1e-9, "半场应为 0.5");
  assert.equal(p(startOdo + laps * L), 1, "终点应为 1");
  assert.equal(p(startOdo + laps * L * 1.8), 1, "超界须 clamp 到 1");
  assert.equal(p(startOdo - 500), 0, "负向须 clamp 到 0");
});

/* ---- 5. 不泄答案：字段白名单（逐键扫描，贴合 #5 H6） ---- */
t("T5 字段白名单：model 递归键名不含任何禁词，且 nextGate 无答案域", () => {
  const m = baseModel({ activeGate: { gate: { id: 0, lap: 0, line: 385.09 + L * 0.24 } } });
  const banned = ["spoken", "other", "correctLateral", "left", "right", "pairKey", "qType",
    "options", "displayIpa", "sym", "hit", "answer", "correct", "word", "ipa", "label"];
  const keys = collectKeys(m);
  for (const b of banned) assert.ok(!keys.includes(b), "禁用键泄漏: " + b);
  assert.deepEqual(Object.keys(m.nextGate).sort(), ["distance", "id", "lap", "line", "secondsTo"]);
});

/* ---- 6. 圈数文本（极简 1/2 → 2/2，不重复「听对 N」） ---- */
t("T6 圈数文本：1/2 → 2/2，且不含「听对」", () => {
  assert.equal(baseModel({ lap: 0, laps: 2 }).lapText, "1/2");
  assert.equal(baseModel({ lap: 1, laps: 2 }).lapText, "2/2");
  assert.ok(!baseModel({ lap: 1, laps: 2 }).lapText.includes("听对"));
});

/* ---- 7. 纯函数：不改动输入 view（只读） ---- */
t("T7 纯函数：不修改传入 view / track.samples", () => {
  const v = baseView();
  const before = JSON.stringify({ v, n: v.track.samples.length, s0: v.track.samples[0] });
  minimapModel(v);
  assert.equal(JSON.stringify({ v, n: v.track.samples.length, s0: v.track.samples[0] }), before,
    "minimapModel 不得写回输入");
});

console.log("\n" + "=".repeat(56));
console.log("SUMMARY: " + pass + " PASS / " + fail + " FAIL / " + (pass + fail) + " TOTAL");
process.exit(fail ? 1 : 0);
