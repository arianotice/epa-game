// Task #19 / CSEG-P0 · 路线 B 最终配置（据 dev/build 实测定型，方案不预设）
//
// 实测事实（2026-11-09，见 design/p0-impl-report.md §3）：
//  T1  Vite root=音标拉力赛/ 时，index.html 的 ../音标大闯关/... 在浏览器里被规范化为
//      /音标大闯关/...，dev 下命中 SPA fallback → 200 + text/html（伪装，不是资源）。
//      单靠 server.fs.allow 不够：动态拼接的 48 立绘 / 48 卡面 / 83 audio 不是静态引用，
//      Vite 静态分析抓不到，且 vite build 会把 4 个静态 ../ 图片 hash 化到 /assets/。
//  T2  普通同步 script（ipa-display.js）在 dev 与 build 下均被 Vite 原样保留
//      （build 仅警告 "can't be bundled without type=module"）→ 只要资源送达，
//      window.IPA_DISPLAY 仍先于 module 就绪，时序不破。
//  T4  Vite 保留源码里的查询串（改写为绝对路径但 ?v= 仍在）→ 源码层 ?v= 与
//      产物层 content-hash 双命名空间自然并存，互不混算（见 vendor.manifest.json）。
//
// 本文件是 .js，会被 S17 扫描 → 全文禁止出现源码层 tag 字面量（用变量拼接，不写字面量）。
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));   // 音标拉力赛/
const PROJECT = path.resolve(ROOT, "..");                     // 英语音标播客/
const QUEST = path.join(PROJECT, "音标大闯关");
const CROSS_SEG = path.basename(QUEST);                       // 音标大闯关（中文，URL 需 decode）
const VENDOR_TAG = "p0-20261109";

// 补充约束 #19-3（team-lead 转达 quality-lead 扫描根污染风险）：把产物层落点移出
// 两站扫描根（QUEST/RALLY 的 os.walk 范围），指向项目根下的独立目录 .p0-build/dist/。
// Vite build.outDir 支持 root 之外的绝对路径；preview server 仍以该目录为服务根，
// 故 index.html / probe.html / /音标大闯关/... 的 URL 结构与 origin 均不变（T3 不冲突）。
// 注意：node_modules/ 由 npm 依 package.json 位置决定，不由 Vite 配置控制；
// 外置它会把工程根上提到项目根，与「node js/headless_laps.mjs 原路径原命令」及
// dev/build 启动 cwd 冲突，故本轮不硬凑，结论与部署建议见 design/p0-impl-report.md §9。
const OUT_DIR = path.resolve(PROJECT, ".p0-build", "dist");

const MIME = {
  ".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg", ".gif": "image/gif", ".svg": "image/svg+xml",
  ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
  ".mp3": "audio/mpeg", ".wav": "audio/wav", ".ogg": "audio/ogg",
  ".html": "text/html; charset=utf-8", ".ico": "image/x-icon",
};

function safeJoin(base, rel) {
  const p = path.resolve(base, "." + path.sep + rel);
  return p.startsWith(path.resolve(base) + path.sep) ? p : null;
}

// dev：把 /音标大闯关/<rel> 映射到磁盘 ../音标大闯关/<rel>，逐字节送达、不 transform。
// 注册为 pre 中间件（configureServer 不返回函数），确保抢在 Vite SPA fallback 之前。
function crossSiteDev() {
  return {
    name: "p0-cross-site-dev",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        let pathname;
        try { pathname = decodeURIComponent(new URL(req.url, "http://localhost").pathname); }
        catch { return next(); }
        // 兼容 /@fs/ 与直接 /音标大闯关/ 两种前缀；../ 已被浏览器规范化掉
        const marker = "/" + CROSS_SEG + "/";
        const i = pathname.indexOf(marker);
        if (i < 0) return next();
        const rel = pathname.slice(i + marker.length);
        const file = safeJoin(QUEST, rel);
        if (!file || !fs.existsSync(file) || !fs.statSync(file).isFile()) return next();
        const ext = path.extname(file).toLowerCase();
        res.setHeader("Content-Type", MIME[ext] || "application/octet-stream");
        res.setHeader("Cache-Control", "no-cache");
        res.setHeader("X-P0-Cross-Site", VENDOR_TAG);
        res.statusCode = 200;
        fs.createReadStream(file).pipe(res);
      });
    },
  };
}

// build：Vite 只 hash 化 index.html 的 4 个静态 ../ 图片；动态拼接的
// 48 立绘 / 48 卡面 / 83 audio / ipa-display.js / 29 成稿图都不在产物里。
// 逐字节复制到 dist，保持与源码层完全一致的 URL 路径（dist/音标大闯关/...、dist/audio/...）。
// 实测注意（2026-11-09）：Node v22.22.2 / Windows 中文路径下
// fs.cpSync(src,dst,{recursive:true}) 会让进程静默崩溃（exit 127、try/catch 接不住、
// 日志停在调用前），故这里用纯 JS 逐文件 copyFileSync 递归，可捕获、可计数、可校验。
function copyTreeSync(src, dst) {
  let n = 0;
  const st = fs.statSync(src);
  if (st.isDirectory()) {
    fs.mkdirSync(dst, { recursive: true });
    for (const name of fs.readdirSync(src)) {
      n += copyTreeSync(path.join(src, name), path.join(dst, name));
    }
  } else if (st.isFile()) {
    fs.mkdirSync(path.dirname(dst), { recursive: true });
    fs.copyFileSync(src, dst);
    n += 1;
  }
  return n;
}

function crossSiteBuild() {
  return {
    name: "p0-cross-site-build",
    apply: "build",
    closeBundle() {
      const dist = OUT_DIR;
      const copies = [
        [path.join(QUEST, "assets"), path.join(dist, CROSS_SEG, "assets")],
        [path.join(QUEST, "js", "ipa-display.js"), path.join(dist, CROSS_SEG, "js", "ipa-display.js")],
        [path.join(ROOT, "audio"), path.join(dist, "audio")],
        [path.join(ROOT, "vendor.manifest.json"), path.join(dist, "vendor.manifest.json")],
        // Task #28 / P1：主站 3D 默认渲染层的预构建 IIFE。index.html 是动态注入的 script，
        // Vite 静态分析抓不到，故由 closeBundle 逐字节复制；源码层必须已跑过 npm run build:p1。
        [path.join(ROOT, "assets", "p1"), path.join(dist, "assets", "p1")],
      ];
      let n = 0;
      for (const [src, dst] of copies) {
        if (!fs.existsSync(src)) continue;
        n += copyTreeSync(src, dst);
      }
      console.log(`[p0-cross-site-build] copied ${n} file(s) into dist (VENDOR_TAG=${VENDOR_TAG})`);
    },
  };
}

export default defineConfig({
  root: ROOT,
  base: "./",
  plugins: [react(), crossSiteDev(), crossSiteBuild()],
  define: { __P0_VENDOR_TAG__: JSON.stringify(VENDOR_TAG) },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    // 配套项，不是主解：允许 Vite 自身读取 root 外的静态引用；动态拼接 URL 仍靠上面的中间件。
    fs: { allow: [PROJECT] },
  },
  preview: { host: "127.0.0.1", port: 4173, strictPort: true },
  build: {
    outDir: OUT_DIR,
    // Task #28 / P1：产物目录由 crossSiteBuild() 逐字节复制，Vite 会覆盖同名产物。
    // 关闭自动清空，避免在已累积的跨站产物上触发本机批量删除保护（safe-delete shim，
    // threshold=50）；历史 hash 产物不参与入口，需人工定期清理，见 p1-impl-report.md §9。
    emptyOutDir: false,
    // 独立入口：/ 是 2D 主形态（默认），/probe.html 是 opt-in 的 R3F 探针。
    rollupOptions: {
      input: {
        main: path.join(ROOT, "index.html"),
        probe: path.join(ROOT, "probe.html"),
      },
    },
  },
});
