/* Task #28 / P1 · 3D 场景可复现预构建（esbuild → 自包含 IIFE）
 *
 * 为什么需要预构建：五套既有门控自起 ThreadingHTTPServer 服务**纯静态源码**，不走 Vite；
 * .jsx + bare import 在静态源码形态下浏览器无法执行。故把 scene3d.jsx + 依赖打成
 * 单个 IIFE bundle，落 assets/p1/（S17 / S18 的 os.walk 排除 assets/，不污染 46 处 tag）。
 *
 * 运行： node js/build-p1.mjs     （package.json: npm run build:p1）
 * 产物： assets/p1/scene3d.js     （index.html 动态注入加载，不带任何 ?v= 字面量）
 */
import { build } from "esbuild";
import { readFileSync, statSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "..");
const OUT_DIR = path.join(ROOT, "assets", "p1");
const OUT = path.join(OUT_DIR, "scene3d.js");
mkdirSync(OUT_DIR, { recursive: true });

await build({
  entryPoints: [path.join(HERE, "scene3d.jsx")],
  outfile: OUT,
  bundle: true,
  format: "iife",
  platform: "browser",
  target: ["es2020"],
  loader: { ".jsx": "jsx" },
  jsx: "automatic",
  define: { "process.env.NODE_ENV": JSON.stringify("production") },
  minify: true,
  legalComments: "none",
  logLevel: "silent",
});

const src = readFileSync(OUT, "utf8");
const bytes = statSync(OUT).size;
/* 产物层静态护栏：源码层 tag / 产物层 tag / 图片 URL / 禁用判据关键字一律零命中。 */
const AUDIT = {
  "源码层 tag": (src.match(/hud-20261108/g) || []).length,
  "P0 产物层 tag": (src.match(/p0-20261109/g) || []).length,
  "未替换的 process.env": (src.match(/process\.env/g) || []).length,
  "fogType 字符串": (src.match(/fogType/g) || []).length,
  "Storage 写入 API": (src.match(/\.setItem\s*\(/g) || []).length,
  "图片 URL 裸引用": (src.match(/assets\/img\/|\.webp|\.png/g) || []).length,
};
const bad = Object.entries(AUDIT).filter(([, n]) => n !== 0);
console.log("[build-p1] " + path.relative(ROOT, OUT) + "  " + bytes + " bytes");
for (const [k, n] of Object.entries(AUDIT)) console.log("  " + (n === 0 ? "OK  " : "FAIL") + "  " + k + " = " + n);
if (bad.length) {
  console.error("[build-p1] 产物静态护栏未通过：", bad);
  process.exit(1);
}
console.log("[build-p1] DONE (IIFE / 零外部运行时依赖 / 静态源码形态可执行)");
