/* app.js — 路由、HUD、通用工具 */
(function () {
  const $ = (sel, root) => (root || document).querySelector(sel);
  const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));

  function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach((k) => {
      if (k === "class") el.className = attrs[k];
      else if (k === "html") el.innerHTML = attrs[k];
      else if (k.startsWith("on") && typeof attrs[k] === "function") el.addEventListener(k.slice(2), attrs[k]);
      else if (attrs[k] !== null && attrs[k] !== undefined) el.setAttribute(k, attrs[k]);
    });
    kids.flat().forEach((c) => {
      if (c === null || c === undefined || c === false) return;
      el.append(c.nodeType ? c : document.createTextNode(String(c)));
    });
    return el;
  }
  function esc(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  function fmtTime(s) {
    if (!isFinite(s)) return "0:00";
    s = Math.max(0, Math.floor(s));
    return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
  }

  /* ---------- Toast ---------- */
  let toastTimer = null;
  const Toast = {
    show(msg, ms) {
      const t = $("#toast");
      t.textContent = msg; t.classList.add("show");
      clearTimeout(toastTimer);
      toastTimer = setTimeout(() => t.classList.remove("show"), ms || 2200);
    },
  };

  /* ---------- 弹层 ---------- */
  const Modal = {
    open(contentNode) {
      const layer = $("#modal-layer");
      layer.innerHTML = "";
      layer.append(contentNode);
      layer.hidden = false;
      layer.onclick = (e) => { if (e.target === layer) Modal.close(); };
      document.addEventListener("keydown", Modal._esc = (e) => { if (e.key === "Escape") Modal.close(); });
    },
    close() {
      const layer = $("#modal-layer");
      layer.hidden = true; layer.innerHTML = "";
      if (Modal._esc) document.removeEventListener("keydown", Modal._esc);
    },
  };

  /* ---------- 彩带 ---------- */
  function confetti() {
    const old = document.getElementById("confetti");
    if (old) old.remove();
    const cv = h("canvas", { id: "confetti" });
    document.body.append(cv);
    const ctx = cv.getContext("2d");
    cv.width = innerWidth; cv.height = innerHeight;
    const colors = ["#e9b949", "#b03a2e", "#1e7a4f", "#1f618d", "#6c3483", "#ffefc4"];
    const ps = Array.from({ length: 140 }, () => ({
      x: Math.random() * cv.width, y: -20 - Math.random() * cv.height * .5,
      w: 6 + Math.random() * 7, vy: 2.2 + Math.random() * 3.2, vx: -1.6 + Math.random() * 3.2,
      c: colors[(Math.random() * colors.length) | 0], r: Math.random() * Math.PI, vr: -.14 + Math.random() * .28,
    }));
    let frames = 0;
    (function tick() {
      ctx.clearRect(0, 0, cv.width, cv.height);
      ps.forEach((p) => {
        p.x += p.vx; p.y += p.vy; p.r += p.vr;
        ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.r);
        ctx.fillStyle = p.c; ctx.fillRect(-p.w / 2, -p.w / 4, p.w, p.w / 2);
        ctx.restore();
      });
      if (++frames < 170) requestAnimationFrame(tick);
      else cv.remove();
    })();
  }

  /* ---------- HUD ---------- */
  function renderHud() {
    $("#hud-stars").textContent = Store.totalStars();
    const spirits = $("#hud-spirits");
    spirits.textContent = Store.learnedCount();
    /* FIX-B01：HUD 由「已收集 X / 48」改为「已学 X / 48」，避免老玩家归零惊吓。
       index.html 不在本轮改动范围，故用幂等 DOM 变换改写标签（dataset 保证只做一次）。 */
    const hudItem = spirits.closest(".hud-item");
    if (hudItem && !hudItem.dataset.learnedHud) {
      hudItem.dataset.learnedHud = "1";
      hudItem.setAttribute("title", "已学会的音标 · 音标卡请参加四大杯赛解锁");
      const icon = hudItem.querySelector(".hud-icon");
      if (icon) icon.textContent = "📖";
      const wrap = spirits.parentElement;
      if (wrap) wrap.replaceChildren(document.createTextNode("已学 "), spirits, document.createTextNode(" / 48"));
    }
    $("#btn-sound").textContent = Store.soundOn() ? "🔊" : "🔇";
  }

  /* ---------- 路由 ---------- */
  function route() {
    AudioMgr.stop();
    /* 离开上一视图时清理其 ScrollTrigger / 背景层，避免钉住残留 */
    if (window.StoryView) StoryView.destroy();
    const hash = location.hash || "#/story";
    const view = $("#view");
    view.innerHTML = "";
    $$(".nav-btn").forEach((b) => b.classList.remove("active"));
    if (window.StoryView) StoryView.scrollTop();
    else window.scrollTo({ top: 0 });

    let m;
    if ((m = hash.match(/^#\/level\/(EP\d+)$/i))) {
      const ep = m[1].toUpperCase();
      if (window.LevelView) LevelView.render(view, ep); else view.append(h("p", null, "关卡页加载中…"));
      $$('[data-nav="map"]').forEach((b) => b.classList.add("active"));
    } else if (hash.startsWith("#/atlas")) {
      if (window.AtlasView) AtlasView.render(view, hash); else view.append(h("p", null, "图鉴加载中…"));
      $$('[data-nav="atlas"]').forEach((b) => b.classList.add("active"));
    } else if (hash === "#/grad") {
      if (window.MapView) MapView.renderDiploma(view); else view.append(h("p", null, "加载中…"));
    } else if (hash === "#/story") {
      if (window.StoryView) StoryView.render(view); else view.append(h("p", null, "故事加载中…"));
      $$('[data-nav="story"]').forEach((b) => b.classList.add("active"));
    } else {
      if (window.MapView) MapView.render(view); else view.append(h("p", null, "地图加载中…"));
      $$('[data-nav="map"]').forEach((b) => b.classList.add("active"));
    }
    renderHud();
  }

  /* ---------- 顶栏高度变量：叙事屏据此按「可视区高度」排版，避免被吸顶栏裁切 ---------- */
  function syncTopbarVar() {
    const tb = $(".topbar");
    if (tb) document.documentElement.style.setProperty("--topbar-h", tb.offsetHeight + "px");
  }

  /* ---------- 启动 ---------- */
  document.addEventListener("DOMContentLoaded", () => {
    syncTopbarVar();
    window.addEventListener("resize", syncTopbarVar);
    $("#btn-sound").addEventListener("click", () => {
      Store.setSound(!Store.soundOn());
      renderHud();
      Toast.show(Store.soundOn() ? "声音已开启 🔊" : "声音已关闭 🔇");
      if (Store.soundOn()) AudioMgr.sfx("click");
    });
    $("#btn-atlas").addEventListener("click", () => { location.hash = "#/atlas"; });
    /* 启用 Lenis 平滑滚动（与 ScrollTrigger 同步，全站生效） */
    if (window.StoryView) StoryView.initSmooth();
    window.addEventListener("hashchange", route);
    route();
  });

  window.App = { $, $$, h, esc, fmtTime, Toast, Modal, confetti, renderHud };
})();
