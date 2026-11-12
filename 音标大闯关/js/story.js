/* story.js — 滚动叙事首页：序章 → 终章
   技术栈：Lenis 平滑滚动 + GSAP ScrollTrigger 场景化入场 + 逐章色彩过渡 */
(function () {
  const { h, esc, fmtTime, Toast } = window.App;
  const SVGNS = "http://www.w3.org/2000/svg";
  /* FIX-C03：面向用户的大字一律取美式 displayIpa（按稳定 unit id 查表），表缺项回退英式 sym。
     注意：chapterPhonemes() 的 seen[p.sym] 去重键是英式稳定键，绝不改成显示值（美式合并会串数据）。 */
  const IPA = (p) => (window.IPA_DISPLAY && window.IPA_DISPLAY[p.unit] && window.IPA_DISPLAY[p.unit].displayIpa) || p.sym;

  /* ============================================================
     章节剧本（内容取自 30 期播客脚本，非虚构）
     ============================================================ */
  const CHAPTERS = [
    {
      num: "序章", kicker: "出发营地",
      title: "欢迎加入\n声音探险队",
      lead: "你有没有过这样的时刻——看到一个陌生的英语单词，想读却不敢开口？",
      paras: [
        "其实，英语也有一套“拼音”，它叫国际音标。",
        "48 个音标，就是 48 块乐高积木。不管多长多难的词，都能用它们拼出来。学会音标，陌生单词你也敢开口，背单词还能快一倍。",
      ],
      quote: "国际音标是英语的拼音，48 个音标就是 48 块乐高积木——任何一个英语单词，都能用它们拼出来！",
      art: "cover.webp", artCaption: "声音探险队 · 全员集合",
      audio: "ep00", audioLabel: "第 00 集 · 欢迎加入声音探险队",
      eps: ["EP00"],
      bg: "linear-gradient(165deg,#fdf5e2 0%,#f0d095 100%)", accent: "#b8860b",
    },
    {
      num: "第一幕", kicker: "出发营地 · 认识乐器",
      title: "嘴巴里的\n一支乐队",
      lead: "出发之前，先认识一下你的“乐器”——嘴巴。",
      paras: [
        "嘴唇是大门，牙齿是栏杆，舌头是舞者，声带是小鼓，气流是一阵风。",
        "元音气流畅通、又亮又饱满，像在唱歌；辅音有的“噗”地爆破、有的“嘶嘶”摩擦，像在打鼓。",
        "把手贴在喉咙上，发一个长长的“zzz”——感觉到麻麻的震动了吗？那就是声带在打鼓。",
      ],
      quote: "嘴唇大门牙齿栏，舌头舞者声带鼓，气流带来一阵风——元音唱歌辅音打鼓！",
      art: "f.webp", artCaption: "发音实验室 · 口腔剖面图（舌位 / 唇形 / 气流 / 声带）",
      audio: "ep01", audioLabel: "第 01 集 · 嘴巴里的乐队",
      eps: ["EP01"],
      bg: "linear-gradient(165deg,#eaf8f2 0%,#bfe4d5 100%)", accent: "#1e7a4f",
    },
    {
      num: "第二幕", kicker: "元音城堡 · 单元音",
      title: "12 位\n一站到底歌手",
      lead: "元音城堡里住着 20 位元音精灵，它们最爱唱歌。",
      paras: [
        "单元音的秘诀是：嘴型从头到尾保持不变，一站到底。",
        "紧元音要绷住——嘴角拉开“衣——”；松元音要放松、轻轻一收“咦”。差别就在绷不绷、松不松。",
        "最经典的一对：嘴角拉到耳边、肌肉绷紧，是 sheep 绵羊；嘴巴微张、松又轻、轻轻一收，是 ship 小船。",
      ],
      quote: "嘴角微笑拉耳边，绷得紧，是 sheep；嘴巴微张松又轻，轻轻一收，是 ship。",
      art: "a2.webp", artCaption: "元音城堡 · 舌位四边形与 8 条双元音滑梯",
      audio: "ep02", audioLabel: "第 02 集 · 阳光农场的绵羊与小船",
      eps: ["EP02", "EP03", "EP04", "EP05", "EP06", "EP07"],
      bg: "linear-gradient(165deg,#eaf1fc 0%,#bcd6f2 100%)", accent: "#1f618d",
    },
    {
      num: "第三幕", kicker: "元音城堡 · 双元音",
      title: "8 条\n声音滑滑梯",
      lead: "城堡顶层还住着 8 位“滑滑梯精灵”，它们叫双元音。",
      paras: [
        "双元音要从第一个音滑到第二个音，中间不能停：“诶→衣”是字母 A，“啊→衣”是字母 I。",
        "滑梯要滑两段：前重后轻、前长后短。",
        "蛋糕 cake、名字 name、自行车 bike、风筝 kite——每一个都在滑滑梯。",
      ],
      quote: "滑滑梯，溜两段，诶滑到衣，是字母 A；啊滑到衣，是字母 I。起点不同路线变！",
      art: "b08.webp", artCaption: "生日派对 · 双元音滑滑梯",
      audio: "ep08", audioLabel: "第 08 集 · 生日派对上的滑滑梯",
      eps: ["EP08", "EP09", "EP10", "EP11"],
      bg: "linear-gradient(165deg,#f4edfb 0%,#dbc8f3 100%)", accent: "#6c3483",
    },
    {
      num: "第四幕", kicker: "辅音王国 · 清浊成对",
      title: "18 对\n双胞胎鼓手",
      lead: "辅音王国住着 28 位“障碍音”精灵，气流要冲破它们才能出门。",
      paras: [
        "它们大多是成双成对的双胞胎：/p/ 和 /b/、/t/ 和 /d/、/k/ 和 /g/、/f/ 和 /v/……",
        "怎么分辨？手贴喉咙——不麻的是清辅音（像纸飞机“噗”），嗡嗡发麻的是浊辅音（像打鼓）。",
        "最特别的一对：上牙必须碰到下唇才是 /v/，不然就变成 /w/——背心会变成西方！",
      ],
      quote: "嘴型相同开关换，手贴喉咙马上辨！",
      art: "a3.webp", artCaption: "辅音王国 · 发音部位 × 发音方法矩阵",
      audio: "ep12", audioLabel: "第 12 集 · 纸飞机王国的第一声鼓点",
      eps: ["EP12", "EP13", "EP14", "EP15", "EP16", "EP17", "EP18", "EP19", "EP20"],
      bg: "linear-gradient(165deg,#fdeeea 0%,#f1c7bd 100%)", accent: "#b03a2e",
    },
    {
      num: "第五幕", kicker: "辅音王国 · 特殊居民",
      title: "几位\n独行侠邻居",
      lead: "除了双胞胎，辅音王国还住着几位脾气特别的“独行侠”。",
      paras: [
        "鼻音三兄弟 /m/ /n/ /ŋ/：捏住鼻子，它们统统哑掉——一松手又全都回来了。",
        "舌侧音 /l/：舌尖像小钩子钩住上齿龈；跑到词尾要闷出一个“小欧欧”。",
        "还有半元音 /w/ /j/ 和破擦四兄弟 /tr/ /dr/ /ts/ /dz/，各有各的拿手好戏。",
      ],
      quote: "捏住鼻子全哑掉，一松手呀全回来！",
      art: "b21.webp", artCaption: "床头与餐桌 · 鼻音双胞胎",
      audio: "ep21", audioLabel: "第 21 集 · 床头与餐桌上的两个鼻音",
      eps: ["EP21", "EP22", "EP23", "EP24", "EP25"],
      bg: "linear-gradient(165deg,#fdf4e3 0%,#f0d9a6 100%)", accent: "#a0720a",
    },
    {
      type: "journey",
      num: "第六幕", kicker: "旅程全景",
      title: "30 站，\n串成一条光",
      lead: "从出发营地到进阶峰，30 个关卡连成一条探险路线。继续向下滚动，看它一段段被点亮。",
      eps: [],
      bg: "linear-gradient(165deg,#2b3352 0%,#141b30 100%)", accent: "#ffd766", dark: true,
    },
    {
      type: "gallery",
      num: "第七幕", kicker: "48 位音标精灵",
      title: "和 48 位\n精灵打个招呼",
      lead: "每一个音标，都是一位有名字、有性格的小精灵。继续向下滚动，一一认识它们。",
      eps: [],
      bg: "linear-gradient(165deg,#1f2646 0%,#101529 100%)", accent: "#8fd3ff", dark: true,
    },
    {
      num: "终章", kicker: "进阶峰 · 毕业",
      title: "积木，\n变成滑梯",
      lead: "最后一站是进阶峰——在这里，英语从积木变成滑梯。",
      paras: [
        "长单词切蛋糕（音节）、重音的秘密、连读与失去爆破：这是让英语“活”起来的三个魔法。",
        "然后是毕业大作战——六对最容易混淆的音标终极对决，全部点亮就毕业！",
        "故事讲到这里，真正的探险才刚开始。你，准备好了吗？",
      ],
      quote: "词尾碰头就连读，爆破音尾憋住不炸——英语从积木变成滑梯！",
      art: "cover.webp", artCaption: "毕业典礼 · 声音探险队",
      audio: "ep29", audioLabel: "第 29 集 · 毕业大作战",
      eps: ["EP26", "EP27", "EP28", "EP29"],
      bg: "linear-gradient(165deg,#fdf6dc 0%,#f2d078 100%)", accent: "#a0720a",
      finale: true,
    },
  ];

  const REGION_ACCENT = { camp: "#b8860b", vowel: "#1f618d", cons: "#b03a2e", peak: "#6c3483" };
  const TYPE_CLASS = {
    "vowel-long": "c-long", "vowel-short": "c-short", "diphthong": "c-dip",
    "cons-clear": "c-clear", "cons-voiced": "c-voi", "nasal": "c-nas",
    "lateral": "c-lat", "semivowel": "c-semi",
  };

  /* ============================================================
     Lenis 平滑滚动（全局单例，与 ScrollTrigger 同步）
     ============================================================ */
  let lenis = null;
  let ctx = null;

  function reduced() {
    return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  function initSmooth() {
    if (lenis || !window.Lenis || !window.gsap || !window.ScrollTrigger) return;
    if (reduced()) return;
    lenis = new Lenis({
      duration: 1.15,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      smoothWheel: true,
      wheelMultiplier: 1,
      touchMultiplier: 1.7,
    });
    window.__lenis = lenis;
    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add((time) => { lenis.raf(time * 1000); });
    gsap.ticker.lagSmoothing(0);
  }

  function smoothTo(target) {
    if (lenis) { lenis.scrollTo(target, { duration: 1.2 }); return; }
    if (target && target.scrollIntoView) target.scrollIntoView({ behavior: "smooth" });
  }

  function scrollTop() {
    if (lenis) { lenis.scrollTo(0, { immediate: true }); return; }
    window.scrollTo(0, 0);
  }

  function destroy() {
    if (ctx) { ctx.revert(); ctx = null; }
    ["story-bg", "story-progress", "chapter-dots", "story-cta", "story-vignette"]
      .forEach((id) => { const el = document.getElementById(id); if (el) el.remove(); });
    document.body.classList.remove("story-mode");
    if (lenis) lenis.start();
  }

  /* ============================================================
     工具
     ============================================================ */
  function titleNode(t) {
    const lines = String(t).split("\n");
    const out = [];
    lines.forEach((ln, i) => {
      if (i) out.push(h("br"));
      out.push(document.createTextNode(ln));
    });
    return out;
  }

  function chapterPhonemes(eps, L) {
    const out = [], seen = {};
    eps.forEach((ep) => {
      const lv = L[ep];
      if (!lv) return;
      lv.phonemes.forEach((p) => { if (!seen[p.sym]) { seen[p.sym] = 1; out.push(p); } });
    });
    return out;
  }

  /* ---------- 播客播放器卡片 ---------- */
  function makePlayer(audioKey, label) {
    const bar = h("i");
    const tCur = h("span", null, "0:00"), tDur = h("span", null, "0:00");
    const btn = h("button", { class: "play-btn", "aria-label": "播放本期节目" }, "▶");
    btn.addEventListener("click", () => {
      AudioMgr.sfx("click");
      AudioMgr.play(audioKey, label, {
        onTick: (el) => {
          bar.style.width = (el.duration ? (el.currentTime / el.duration) * 100 : 0) + "%";
          tCur.textContent = fmtTime(el.currentTime);
          tDur.textContent = fmtTime(el.duration);
        },
        onPlay: () => { btn.textContent = "⏸"; btn.classList.add("playing"); },
        onPause: () => { btn.textContent = "▶"; btn.classList.remove("playing"); },
        onEnd: () => { btn.textContent = "▶"; btn.classList.remove("playing"); bar.style.width = "0%"; tCur.textContent = "0:00"; },
      });
    });
    return h("div", { class: "card story-player js-anim" },
      h("div", { class: "card-title" }, "🎧 听波波队长讲故事"),
      h("div", { class: "player" }, btn, h("div", { class: "track" },
        h("div", { class: "bar" }, bar),
        h("div", { class: "time" }, tCur, tDur))),
      h("div", { class: "story-player-label" }, esc(label))
    );
  }

  /* ============================================================
     构建：普通章节
     ============================================================ */
  function buildChapter(c, i, L, data) {
    const dark = !!c.dark;
    const style = "--accent:" + c.accent +
      (dark ? ";--ink:#fdf3e0;--ink-soft:#cdbd9b;--card:rgba(255,255,255,.09);--line:rgba(255,255,255,.24)" : "");

    const sec = h("section", {
      class: "chapter" + (i % 2 ? " chapter--flip" : "") + (dark ? " chapter--dark" : ""),
      style: style, "data-ch": i,
    });

    /* 文字区 */
    const text = h("div", { class: "ch-text" });
    text.append(h("div", { class: "ch-num js-anim" }, esc(c.num)));
    text.append(h("div", { class: "ch-kicker js-anim" }, esc(c.kicker)));
    text.append(h("h2", { class: "ch-title js-anim" }, titleNode(c.title)));
    text.append(h("div", { class: "ch-rule js-anim" }));
    text.append(h("p", { class: "ch-lead js-anim" }, esc(c.lead)));
    (c.paras || []).forEach((p) => text.append(h("p", { class: "ch-p js-anim" }, esc(p))));
    if (c.quote) {
      text.append(h("div", { class: "ch-quote js-anim" },
        h("span", { class: "ch-quote-tag" }, "✨ 口诀"),
        h("div", null, esc(c.quote))));
    }

    /* 本幕关卡 */
    const eps = (c.eps || []).filter((ep) => L[ep]);
    if (eps.length) {
      const pills = h("div", { class: "ch-levels js-anim" });
      eps.forEach((ep) => {
        const lv = L[ep];
        const unlocked = Store.isUnlocked(ep);
        const st = Store.starsOf(ep);
        pills.append(h("button", {
          class: "lv-pill" + (unlocked ? "" : " locked") + (st > 0 ? " done" : ""),
          onclick: () => {
            AudioMgr.sfx("click");
            if (unlocked) location.hash = "#/level/" + ep;
            else Toast.show("🔒 这一关还没解锁，先完成上一关吧！");
          },
        }, (unlocked ? "" : "🔒 ") + esc(lv.title)));
      });
      text.append(pills);
    }

    /* 音标精灵小签 */
    const phs = chapterPhonemes(c.eps || [], L);
    if (phs.length) {
      const chips = h("div", { class: "ch-chips" });
      phs.forEach((p) => {
        chips.append(h("button", {
          class: "sp-chip js-anim", title: "点击看「" + p.name + "」的项目代表词卡并听真人朗读",
          onclick: () => { AudioMgr.sfx("click"); if (window.ProjCard) ProjCard.show(p); else AudioMgr.playPhoneme(p.unit, p.name); },
        },
          h("span", { class: "sp-chip-sym ipa " + (TYPE_CLASS[p.type] || ""), title: `图鉴 ${p.sym}` }, esc(IPA(p))),
          h("span", { class: "sp-chip-name" }, esc(p.name)),
          h("span", { class: "sp-chip-play", "aria-hidden": "true" }, "🔊")));
      });
      text.append(chips);
    }

    /* 播放器 */
    if (c.audio) text.append(makePlayer(c.audio, c.audioLabel || ""));

    /* 配图区 */
    const art = h("div", { class: "ch-art" },
      h("figure", { class: "art-frame js-anim" },
        h("img", { class: "art-img", src: "assets/img/" + c.art + "?v=hud-20261108", alt: esc(c.artCaption || ""), loading: "lazy" })),
      h("figcaption", { class: "art-cap" }, esc(c.artCaption || ""))
    );

    const inner = h("div", { class: "ch-inner" }, text, art);
    sec.append(inner);

    /* 终章：大 CTA */
    if (c.finale) {
      sec.append(h("div", { class: "finale-cta js-anim" },
        h("a", { class: "btn red", href: "#/map" }, "🎮 开启我的闯关之旅"),
        h("a", { class: "btn", href: "#/atlas" }, "💎 先看看音标图鉴")));
    }

    return sec;
  }

  /* ============================================================
     构建：第六幕 · 旅程全景（钉住 + 路线绘制）
     ============================================================ */
  /* 藏宝行进图：未点亮 = 藏宝图「X」标记；点亮 = 弹出对应区域色切面钻石宝石 + 微光 */
  const GEM_COLORS = {
    camp:  { fill: "#e9b949", mid: "#f6dd93", hi: "#fff3d0", line: "#8a5a00" },
    vowel: { fill: "#3f7fb5", mid: "#7fb0d8", hi: "#d7ecfb", line: "#1f4f74" },
    cons:  { fill: "#c0392b", mid: "#e07a6a", hi: "#f6d0c8", line: "#7d1f14" },
    peak:  { fill: "#8a4fb0", mid: "#b585d0", hi: "#e8d4f2", line: "#4d2a63" },
  };

  function gemNode(region) {
    const c = GEM_COLORS[region] || GEM_COLORS.camp;
    return (
      '<svg viewBox="0 0 40 40" aria-hidden="true">' +
      '<g class="xmark" stroke="#8a3524" stroke-width="3.2" stroke-linecap="round">' +
      '<line x1="11" y1="11" x2="29" y2="29"/><line x1="29" y1="11" x2="11" y2="29"/></g>' +
      '<g class="gem">' +
      '<polygon points="20,5 33,20 20,35 7,20" fill="' + c.fill + '" stroke="' + c.line + '" stroke-width="1.6" stroke-linejoin="round"/>' +
      '<polygon points="20,5 26,20 20,35 14,20" fill="' + c.mid + '" stroke="' + c.line + '" stroke-width=".7" opacity=".92"/>' +
      '<line x1="7" y1="20" x2="33" y2="20" stroke="' + c.line + '" stroke-width=".7" opacity=".6"/>' +
      '<line x1="20" y1="5" x2="20" y2="35" stroke="' + c.line + '" stroke-width=".7" opacity=".6"/>' +
      '<polygon points="20,11 24,20 20,29 16,20" fill="' + c.hi + '" opacity=".95"/>' +
      '</g>' +
      '<g class="gem-sparkle" fill="#fff8dc">' +
      '<path d="M20,1 L22,14 L20,12 L18,14 Z"/>' +
      '<path d="M20,39 L22,26 L20,28 L18,26 Z"/>' +
      '<path d="M1,20 L14,22 L12,20 L14,18 Z"/>' +
      '<path d="M39,20 L26,22 L28,20 L26,18 Z"/>' +
      '</g>' +
      '</svg>'
    );
  }

  function buildJourney(c, i) {
    const data = window.IPA_DATA;
    const levels = data.levels;
    const pts = levels.map((l) => l.node.x + "," + l.node.y).join(" ");

    /* 按连续区域分组，用于篇章字幕 */
    const groups = [];
    levels.forEach((l, idx) => {
      const last = groups[groups.length - 1];
      if (last && last.id === l.region) last.end = idx;
      else groups.push({ id: l.region, name: l.regionName, start: idx, end: idx });
    });
    const N = levels.length;

    const svg = document.createElementNS(SVGNS, "svg");
    svg.setAttribute("class", "journey-route");
    svg.setAttribute("viewBox", "0 0 100 100");
    svg.setAttribute("preserveAspectRatio", "none");
    svg.setAttribute("aria-hidden", "true");
    const poly = document.createElementNS(SVGNS, "polyline");
    poly.setAttribute("class", "route-line");
    poly.setAttribute("points", pts);
    poly.setAttribute("fill", "none");
    poly.setAttribute("vector-effect", "non-scaling-stroke");
    svg.append(poly);

    const nodes = h("div", { class: "journey-nodes" });
    levels.forEach((l) => {
      const n = h("span", {
        class: "jnode", style: "left:" + l.node.x + "%;top:" + l.node.y + "%",
        title: l.ep.replace("EP", "第 ") + "关 · " + l.title,
      });
      n.innerHTML = gemNode(l.region);
      nodes.append(n);
    });

    const caps = h("div", { class: "journey-caption" });
    groups.forEach((g) => {
      caps.append(h("div", {
        class: "jcap",
        "data-a": (g.start / (N - 1)).toFixed(4),
        "data-b": (g.end / (N - 1)).toFixed(4),
      },
        h("div", { class: "jcap-t", style: "color:" + (REGION_ACCENT[g.id] || c.accent) }, esc(g.name)),
        h("div", { class: "jcap-s" }, esc(g.start + 1 === g.end + 1
          ? "第 " + (g.start + 1) + " 关"
          : "第 " + (g.start + 1) + "–" + (g.end + 1) + " 关"))));
    });

    const sec = h("section", {
      class: "chapter chapter--journey chapter--dark",
      style: "--accent:" + c.accent + ";--ink:#fdf3e0;--ink-soft:#cdbd9b;--card:rgba(255,255,255,.09);--line:rgba(255,255,255,.24)",
      "data-ch": i,
    },
      h("div", { class: "journey-inner" },
        h("div", { class: "gal-head" },
          h("div", { class: "ch-kicker js-anim" }, esc(c.num + " · " + c.kicker)),
          h("div", { class: "gal-title js-anim" }, esc(String(c.title).replace(/\n/g, " "))),
          h("div", { class: "gal-sub js-anim" }, esc(c.lead))),
        h("div", { class: "journey-stage" },
          h("img", { class: "journey-map", src: "assets/img/a1.webp?v=hud-20261108", alt: "英语音标大地图", loading: "lazy" }),
          svg, nodes, caps
        ),
        h("div", { class: "journey-actions" },
          h("button", { class: "btn journey-play", id: "journey-play" },
            "✨ 点击点亮：从第一关走到最后一关"))
      )
    );
    return sec;
  }

  /* ============================================================
     构建：第七幕 · 48 精灵横向长廊
     ============================================================ */
  function buildGallery(c, i) {
    const data = window.IPA_DATA;
    const track = h("div", { class: "gal-track" });
    data.phonemes.forEach((p) => {
      const w0 = p.words && p.words[0] ? p.words[0].w + " " + p.words[0].zh : "";
      const w1 = p.words && p.words[1] ? " · " + p.words[1].w + " " + p.words[1].zh : "";
      track.append(h("button", {
        class: "sp-card", title: "点击看「" + p.name + "」的项目代表词卡并听真人朗读",
        onclick: () => { AudioMgr.sfx("click"); if (window.ProjCard) ProjCard.show(p); else AudioMgr.playPhoneme(p.unit, p.name); },
      },
        h("div", { class: "sp-card-sym " + (TYPE_CLASS[p.type] || ""), title: `图鉴 ${p.sym}` }, esc(IPA(p))),
        h("div", { class: "sp-card-name" }, esc(p.name)),
        h("div", { class: "sp-card-type" }, esc(p.typeName || "")),
        h("div", { class: "sp-card-w" }, esc(w0 + w1))));
    });

    const sec = h("section", {
      class: "chapter chapter--gallery chapter--dark",
      style: "--accent:" + c.accent + ";--ink:#fdf3e0;--ink-soft:#cdbd9b;--card:rgba(255,255,255,.09);--line:rgba(255,255,255,.24)",
      "data-ch": i,
    },
      h("div", { class: "gal-pin" },
        h("div", { class: "gal-head" },
          h("div", { class: "ch-kicker js-anim" }, esc(c.kicker)),
          h("div", { class: "gal-title js-anim" }, esc(String(c.title).replace(/\n/g, ""))),
          h("div", { class: "gal-sub js-anim" }, esc(c.lead))),
        h("div", { class: "gal-viewport" }, track),
        h("div", { class: "gal-hint js-anim" }, "继续向下滚动 →")
      )
    );
    return sec;
  }

  /* ============================================================
     动画装配
     ============================================================ */
  function buildJourneyTimeline(sec) {
    const poly = sec.querySelector(".route-line");
    const nodes = Array.from(sec.querySelectorAll(".jnode"));
    const caps = Array.from(sec.querySelectorAll(".jcap"));
    const playBtn = sec.querySelector("#journey-play");
    if (!poly) return;

    let len = 0;
    try { len = poly.getTotalLength() || 0; } catch (e) { len = 0; }
    if (len) {
      poly.style.strokeDasharray = len;
      poly.style.strokeDashoffset = len;
    }
    /* 藏宝行进图：✕ 标记常驻（低调），宝石默认隐藏；点亮 = 沿路线逐站「X→宝石」 */
    gsap.set(nodes, { opacity: 1 });
    gsap.set(caps, { opacity: 0, y: 26 });

    let playing = false;
    function playJourney() {
      if (playing) return;
      playing = true;
      if (playBtn) { playBtn.disabled = true; playBtn.textContent = "🚀 探险队出发中…"; }
      /* 重播时先复位：路线收回、所有点位还原为 ✕ 标记 */
      if (len) poly.style.strokeDashoffset = len;
      nodes.forEach((n) => n.classList.remove("lit"));
      const tl = gsap.timeline({
        onComplete: () => {
          playing = false;
          if (playBtn) { playBtn.disabled = false; playBtn.textContent = "🔁 再看一遍路线"; }
        },
      });
      if (len) tl.to(poly, { strokeDashoffset: 0, ease: "none", duration: 2.4 }, 0);
      if (nodes.length > 1) {
        nodes.forEach((n, i) => {
          const at = 0.1 + (i / (nodes.length - 1)) * 2.2;
          tl.add(() => { n.classList.add("lit"); AudioMgr.sfx("star"); }, at);
        });
      }
      caps.forEach((cap) => {
        const a = parseFloat(cap.dataset.a) || 0, b = parseFloat(cap.dataset.b) || 1;
        const at = 0.1 + a * 2.2;
        tl.fromTo(cap, { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.4 }, at);
        if (b < 0.999) tl.to(cap, { opacity: 0, y: -26, duration: 0.4 }, 0.1 + b * 2.2);
      });
    }
    if (playBtn) playBtn.addEventListener("click", () => { AudioMgr.sfx("click"); playJourney(); });

    /* 标题入场 */
    const head = sec.querySelector(".gal-head");
    if (head) {
      gsap.fromTo(head.querySelectorAll(".js-anim"), { y: 30, opacity: 0 }, {
        y: 0, opacity: 1, duration: .7, stagger: .12, ease: "power3.out",
        scrollTrigger: { trigger: sec, start: "top 80%", once: true },
      });
    }
  }

  /* 无 GSAP 时的兜底：路线全显、所有点位直接点亮成宝石 */
  function journeyFallback(sec) {
    const poly = sec.querySelector(".route-line");
    if (poly) { poly.style.strokeDashoffset = 0; }
    sec.querySelectorAll(".jnode").forEach((n) => { n.classList.add("lit"); });
    sec.querySelectorAll(".jcap").forEach((c) => { c.style.opacity = 1; c.style.transform = "none"; });
    const b = sec.querySelector("#journey-play");
    if (b) b.style.display = "none";
  }

  function buildGalleryTimeline(sec) {
    const track = sec.querySelector(".gal-track");
    if (!track) return;
    const getDist = () => Math.max(0, track.scrollWidth - window.innerWidth + 140);
    gsap.to(track, {
      x: () => -getDist(),
      ease: "none",
      scrollTrigger: {
        trigger: sec, start: "top top",
        end: () => "+=" + (getDist() + window.innerHeight * 0.5),
        pin: true, scrub: 0.8, anticipatePin: 1, invalidateOnRefresh: true,
      },
    });
    const head = sec.querySelector(".gal-head");
    if (head) {
      gsap.fromTo(head.querySelectorAll(".js-anim"), { y: 30, opacity: 0 }, {
        y: 0, opacity: 1, duration: .7, stagger: .12, ease: "power3.out",
        scrollTrigger: { trigger: sec, start: "top 80%", once: true },
      });
    }
  }

  function initAnimations(wrap) {
    const secs = Array.from(wrap.querySelectorAll(".chapter"));
    const layers = Array.from(document.querySelectorAll("#story-bg .bg-layer"));
    const bar = document.querySelector("#story-progress i");

    ctx = gsap.context(() => {
      /* 全局进度条 */
      ScrollTrigger.create({
        start: 0, end: "max",
        onUpdate: (self) => { if (bar) bar.style.transform = "scaleX(" + self.progress + ")"; },
      });

      secs.forEach((sec, i) => {
        /* 背景色交叉淡入 —— 形成章节间的流畅色彩过渡 */
        if (i > 0 && layers[i]) {
          gsap.fromTo(layers[i], { opacity: 0 }, {
            opacity: 1, ease: "none",
            scrollTrigger: { trigger: sec, start: "top 88%", end: "top 38%", scrub: true },
          });
        }

        /* 右侧导航高亮 */
        const dot = document.querySelector('.chapter-dots .cdot[data-i="' + i + '"]');
        if (dot) {
          ScrollTrigger.create({
            trigger: sec, start: "top center", end: "bottom center",
            onToggle: (self) => dot.classList.toggle("active", self.isActive),
          });
        }

        /* 特殊章节 */
        if (sec.classList.contains("chapter--journey")) { buildJourneyTimeline(sec); return; }
        if (sec.classList.contains("chapter--gallery")) { buildGalleryTimeline(sec); return; }

        const q = (sel) => sec.querySelector(sel);
        const qa = (sel) => Array.from(sec.querySelectorAll(sel));

        const num = q(".ch-num"), kicker = q(".ch-kicker"), title = q(".ch-title"),
          rule = q(".ch-rule"), lead = q(".ch-lead"),
          paras = qa(".ch-p"), quote = q(".ch-quote"),
          frame = q(".art-frame"), img = q(".art-img"),
          player = q(".story-player"), chips = qa(".sp-chip"),
          levels = q(".ch-levels"), finale = q(".finale-cta");

        const tl = gsap.timeline({
          scrollTrigger: { trigger: sec, start: "top 78%", once: true },
        });

        /* 场景化入场：编号 → 标签 → 标题 → 分割线 → 引导 → 正文 → 口诀 → 关卡 → 播放器 → 精灵签 */
        if (num) tl.fromTo(num, { y: 46, opacity: 0, scale: .84 }, { y: 0, opacity: .18, scale: 1, duration: .75, ease: "power3.out" }, 0);
        if (kicker) tl.fromTo(kicker, { y: 18, opacity: 0 }, { y: 0, opacity: 1, duration: .5, ease: "power2.out" }, .05);
        if (title) tl.fromTo(title, { y: 58, opacity: 0 }, { y: 0, opacity: 1, duration: .85, ease: "power3.out" }, .12);
        if (rule) tl.fromTo(rule, { scaleX: 0, opacity: 0 }, { scaleX: 1, opacity: 1, duration: .6, ease: "power2.out" }, .3);
        if (lead) tl.fromTo(lead, { y: 26, opacity: 0 }, { y: 0, opacity: 1, duration: .6, ease: "power2.out" }, .38);
        if (paras.length) tl.fromTo(paras, { y: 24, opacity: 0 }, { y: 0, opacity: 1, duration: .55, stagger: .13, ease: "power2.out" }, .5);
        if (quote) tl.fromTo(quote, { x: -22, opacity: 0 }, { x: 0, opacity: 1, duration: .6, ease: "power2.out" }, .62);
        if (levels) tl.fromTo(levels, { y: 18, opacity: 0 }, { y: 0, opacity: 1, duration: .5, ease: "power2.out" }, .68);
        if (player) tl.fromTo(player, { y: 26, opacity: 0 }, { y: 0, opacity: 1, duration: .6, ease: "power2.out" }, .72);
        if (finale) tl.fromTo(finale, { y: 24, opacity: 0, scale: .96 }, { y: 0, opacity: 1, scale: 1, duration: .7, ease: "back.out(1.6)" }, .8);
        if (chips.length) tl.fromTo(chips, { scale: .5, opacity: 0 }, { scale: 1, opacity: 1, duration: .42, stagger: .04, ease: "back.out(2.2)" }, .78);

        /* 配图：画框揭示 + 视差 */
        if (frame) {
          tl.fromTo(frame, { opacity: 0 }, { opacity: 1, duration: .5, ease: "power1.out" }, .1);
          gsap.fromTo(frame, { y: 34 }, {
            y: -34, ease: "none",
            scrollTrigger: { trigger: sec, start: "top bottom", end: "bottom top", scrub: true },
          });
        }
        if (img) tl.fromTo(img, { yPercent: 100, scale: 1.14 }, { yPercent: 0, scale: 1, duration: 1.15, ease: "power3.out" }, .1);
      });
    }, wrap);

    /* 图片加载完成后刷新 ScrollTrigger（高度会变化） */
    Array.from(wrap.querySelectorAll("img")).forEach((im) => {
      if (!im.complete) im.addEventListener("load", () => ScrollTrigger.refresh(), { once: true });
    });
    setTimeout(() => ScrollTrigger.refresh(), 300);
  }

  /* ============================================================
     渲染入口
     ============================================================ */
  function render(view) {
    const data = window.IPA_DATA;
    const L = {};
    data.levels.forEach((l) => { L[l.ep] = l; });

    destroy(); // 幂等：确保不残留上一视图的 ScrollTrigger / 背景层
    document.body.classList.add("story-mode");
    scrollTop();

    /* 背景层：一章一层 */
    const bg = h("div", { class: "story-bg", id: "story-bg" });
    CHAPTERS.forEach((c) => bg.append(h("div", { class: "bg-layer", style: "background:" + c.bg })));
    document.body.prepend(bg);

    /* 暗角 */
    document.body.append(h("div", { class: "story-vignette", id: "story-vignette" }));

    /* 顶部进度条 */
    document.body.append(h("div", { class: "story-progress", id: "story-progress" }, h("i")));

    /* 章节正文 */
    const wrap = h("div", { class: "story-wrap" });
    CHAPTERS.forEach((c, i) => {
      if (c.type === "journey") wrap.append(buildJourney(c, i));
      else if (c.type === "gallery") wrap.append(buildGallery(c, i));
      else wrap.append(buildChapter(c, i, L, data));
    });
    view.append(wrap);

    /* 右侧章节导航 */
    const dots = h("nav", { class: "chapter-dots", id: "chapter-dots", "aria-label": "章节导航" });
    CHAPTERS.forEach((c, i) => {
      const b = h("button", {
        class: "cdot", "data-i": i, title: c.num + " · " + c.kicker,
        onclick: () => {
          AudioMgr.sfx("click");
          const sec = wrap.querySelector('.chapter[data-ch="' + i + '"]');
          if (sec) smoothTo(sec);
        },
      },
        h("span", { class: "cdot-label" }, esc(c.num + " " + c.kicker)),
        h("span", { class: "cdot-dot" }));
      dots.append(b);
    });
    document.body.append(dots);

    /* 悬浮 CTA */
    document.body.append(h("a", { class: "story-cta", id: "story-cta", href: "#/map" },
      "⚡ 跳过故事，直接闯关 →"));

    if (window.gsap && window.ScrollTrigger) initAnimations(wrap);
    else {
      document.documentElement.classList.remove("gsap-ready");
      wrap.querySelectorAll(".chapter--journey").forEach((s) => journeyFallback(s));
    }

    App.renderHud();
  }

  window.StoryView = { render, destroy, initSmooth, scrollTop };
})();
