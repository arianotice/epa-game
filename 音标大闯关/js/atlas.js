/* atlas.js — 音标图鉴（48 精灵卡 + U 音频）与知识图谱（A1/A2/A3/F）
 * FIX-B01：双轨解耦
 *   知识轨 hasLearned(p.unit)  —— key_point / mnemonic / words / ▶ 讲解 / 知识图谱，永不锁
 *   卡轨   isCardUnlocked(p.unit) —— 卡面大图、got/locked 视觉、稀有度徽章、拉力赛可用卡
 */
(function () {
  const { $, $$, h, esc, Toast, Modal } = window.App;
  /* FIX-C03：面向用户的大字一律取美式 displayIpa（按稳定 unit id 查表），表缺项回退英式 sym。 */
  const IPA = (p) => (window.IPA_DISPLAY && window.IPA_DISPLAY[p.unit] && window.IPA_DISPLAY[p.unit].displayIpa) || p.sym;

  const TYPE_CLASS = {
    "vowel-long": "c-long", "vowel-short": "c-short", "diphthong": "c-dip",
    "cons-clear": "c-clear", "cons-voiced": "c-voi", "nasal": "c-nas",
    "lateral": "c-lat", "semivowel": "c-semi",
  };
  const TYPE_LABEL = {
    "vowel-long": "紧元音", "vowel-short": "松元音", "diphthong": "双元音",
    "cons-clear": "清辅音", "cons-voiced": "浊辅音", "nasal": "鼻音",
    "lateral": "舌侧音", "semivowel": "半元音",
  };
  const TYPE_COLOR = {
    "vowel-long": "var(--blue)", "vowel-short": "var(--red)", "diphthong": "var(--purple)",
    "cons-clear": "var(--red)", "cons-voiced": "var(--green)", "nasal": "var(--green)",
    "lateral": "var(--green)", "semivowel": "var(--blue)",
  };

  const MAPS = [
    { key: "a1", title: "A1 · 英语音标大地图", desc: "48 个音标精灵的全景知识图谱：出发营地 → 元音城堡 → 辅音王国 → 进阶峰，路线连线就是学习顺序。每个宝藏格 = 音标符号 + 代表单词 + 小图标。" },
    { key: "a2", title: "A2 · 元音城堡分区图", desc: "20 个元音的专业「元音四边形」舌位图：横轴看嘴张开程度，纵轴看舌头前后；8 个双元音画成滑梯，标注滑动方向。" },
    { key: "a3", title: "A3 · 辅音王国分区图", desc: "28 个辅音的家族树：横轴 = 发音部位（双唇→唇齿→齿间→齿龈→硬腭→软腭→声门），纵轴 = 发音方法（爆破/摩擦/破擦/鼻音/舌侧/半元音）。" },
    { key: "f", title: "F · 口腔剖面总图", desc: "发音器官剖面图：嘴唇（大门）、牙齿（栏杆）、舌头（舞者）、声带（小鼓）、气流（风）——发音实验室的总指挥图。" },
  ];

  function render(view, hash) {
    const data = window.IPA_DATA;
    const tab = hash.includes("maps") ? "maps" : (hash.includes("rarity") ? "rarity" : "cards");

    view.append(h("div", { class: "atlas-tabs" },
      h("button", { class: "atlas-tab" + (tab === "cards" ? " active" : ""), onclick: () => { location.hash = "#/atlas"; } }, "💎 48 个音标精灵"),
      h("button", { class: "atlas-tab" + (tab === "rarity" ? " active" : ""), onclick: () => { location.hash = "#/atlas/rarity"; } }, "🌟 稀有度进阶图鉴"),
      h("button", { class: "atlas-tab" + (tab === "maps" ? " active" : ""), onclick: () => { location.hash = "#/atlas/maps"; } }, "🗺️ 知识图谱大图")
    ));

    if (tab === "cards") renderCards(view, data);
    else if (tab === "rarity") renderRarity(view, data);
    else renderMaps(view, data);
  }

  /* ---------- 48 音标卡 ---------- */
  function renderCards(view, data) {
    const filters = [
      { id: "all", name: "全部 48" },
      { id: "vowel", name: "元音 20" },
      { id: "cons", name: "辅音 28" },
      { id: "learned", name: "✅ 已学会" },
      { id: "racecards", name: "🏁 赛事卡" },
    ];
    let active = "all";
    const grid = h("div", { class: "ph-grid" });
    const filterRow = h("div", { class: "filter-row" });

    function paint() {
      filterRow.innerHTML = "";
      filters.forEach((f) => {
        const b = h("button", { class: "filter-chip" + (active === f.id ? " active" : "") }, f.name);
        b.addEventListener("click", () => { active = f.id; AudioMgr.sfx("click"); paint(); });
        filterRow.append(b);
      });
      grid.innerHTML = "";
      data.phonemes.forEach((p) => {
        if (active === "vowel" && p.type.indexOf("vowel") !== 0 && p.type !== "diphthong") return;
        if (active === "cons" && (p.type === "vowel-long" || p.type === "vowel-short" || p.type === "diphthong")) return;
        /* FIX-B01：知识（已学会）与卡面（赛事卡）各自独立判定 */
        const learned = Store.hasLearned(p.unit);
        const cardGot = Store.isCardUnlocked(p.unit);
        if (active === "learned" && !learned) return;
        if (active === "racecards" && !cardGot) return;
        const rar = p.rarity;
        const tile = h("div", {
          class: "ph-tile" + (cardGot ? " got" : " locked"),
          "data-rar": cardGot ? rar : "",
          onclick: (e) => {
            if (e.target.closest(".u-play")) return;
            openPhModal(p);
          }
        },
          h("button", {
            class: "u-play", title: learned ? "播放这个音的讲解" : "学会这个音后即可播放讲解",
            onclick: (e) => {
              e.stopPropagation();
              AudioMgr.sfx("click");
              if (learned) { AudioMgr.play(p.audio, p.name, {}); Toast.show(`🎧 正在播放：${p.name}（${IPA(p)}）`); }
              else Toast.show("🔒 先在关卡里学会这个音，就能听它的讲解啦！");
            }
          }, "▶"),
          h("div", { class: "ph-sprite" + (cardGot ? "" : " dim") },
            h("img", { src: `assets/sprites/${p.unit}.webp?v=hud-20261108`, alt: p.name, loading: "lazy" })
          ),
          h("div", { class: "sym", style: `color:${TYPE_COLOR[p.type]}`, title: `图鉴 ${p.sym}` }, esc(IPA(p))),
          h("div", { class: "nm" }, esc(p.name)),
          h("div", { class: "wds", style: learned ? "filter:none;opacity:1" : "" },
            learned ? p.words.map((w) => esc(w.w)).join(" · ") : "学会后可见单词"),
          cardGot && rar ? h("span", { class: "rar-badge rar-" + rar.toLowerCase(), title: "稀有度 " + rar }, rar) : null,
          !cardGot ? h("span", { class: "lock-tag" }, "🔒 待赛事解锁") : null,
          learned && !cardGot ? h("span", { class: "learned-tag", style: "position:absolute;left:8px;bottom:8px;z-index:3;font-size:11px;font-weight:700;color:#fff;background:rgba(30,122,79,.92);padding:2px 7px;border-radius:999px" }, "✅ 已学会") : null
        );
        grid.append(tile);
      });
      if (!grid.children.length) {
        const emptyMsg = active === "learned"
          ? "还没有学会音标，去地图听故事、完成听辨大挑战就学会啦！"
          : active === "racecards"
            ? "还没有赛事卡，参加四大杯赛的卡丁车比赛就能解锁音标卡！"
            : "这里还没有音标，换个筛选看看～";
        grid.append(h("div", { style: "grid-column:1/-1;text-align:center;color:var(--ink-soft);padding:30px" },
          emptyMsg));
      }
    }

    view.append(h("div", { class: "card", style: "margin-bottom:14px" },
      h("div", { class: "card-title" }, "💎 音标精灵图鉴"),
      h("div", { style: "font-size:13.5px;color:var(--ink-soft)" },
        `已学会 ${Store.learnedCount()} / 48 · 赛事卡 ${Store.cardCount()} / 48。学过的发音要点、口诀、单词与讲解永久可见；音标卡面需参加四大杯赛的卡丁车比赛解锁。点卡片看发音要点，点 ▶ 单独听这个音的讲解。`)
    ));
    view.append(filterRow, grid);
    paint();
  }

  /* ---------- 音标详情弹层 ---------- */
  function openPhModal(p) {
    /* FIX-B01：卡面（赛事卡）与知识（已学会）双轨独立判定 */
    const cardGot = Store.isCardUnlocked(p.unit);
    const learned = Store.hasLearned(p.unit);
    const lv = window.IPA_DATA.levels.find((l) => l.ep === p.ep);
    const body = h("div", { class: "modal" },
      h("button", { class: "close-x", onclick: () => Modal.close() }, "✕"),
      cardGot ? h("div", { class: "ph-card-art" },
        h("img", { src: `assets/sprites/cards/${p.unit}.webp?v=hud-20261108`, alt: p.name })
      ) : h("div", { class: "ph-card-art ph-card-art--locked" },
        h("img", { src: `assets/sprites/cards/${p.unit}.webp?v=hud-20261108`, alt: p.name }),
        h("div", { class: "ph-card-art-veil" }, h("span", null, "🔒 参加四大杯赛解锁卡面"), h("small", null, "稀有度 " + (p.rarity || "—")))),
      h("h2", null, h("span", { class: "ipa", style: `color:${TYPE_COLOR[p.type]}`, title: `图鉴 ${p.sym}` }, esc(IPA(p))), " " + esc(p.name)),
      h("div", { style: "margin-bottom:8px" }, h("span", { class: "tag", style: `color:${TYPE_COLOR[p.type]}` }, TYPE_LABEL[p.type]),
        " ", h("span", { style: "font-size:13px;color:var(--ink-soft)" },
          (learned ? "✅ 已学会" : "尚未学会") + (cardGot ? " · 赛事卡已解锁" : " · 卡面待赛事解锁"))),
      h("div", { class: "ph-key", style: "font-size:15px" }, learned ? esc(p.key_point) : "先去对应关卡学一学，就能看到它的完整档案啦！"),
      learned ? h("div", { class: "mnemonic" }, h("b", null, "📢 口诀"), esc(p.mnemonic)) : null,
      learned ? h("div", { class: "ph-words" }, p.words.map((w) =>
        h("button", { class: "word-chip", onclick: () => AudioMgr.speakEn(w.w) },
          h("span", { class: "ipa" }, esc(w.w)), h("small", null, esc(w.zh)))
      )) : null,
      h("div", { class: "result-actions" },
        h("button", { class: "btn", onclick: () => { Modal.close(); if (window.ProjCard) ProjCard.show(p); else { AudioMgr.playPhoneme(p.unit, p.name); Toast.show(`🎧 正在播放：${p.name}`); } } }, "🎙 听真人代表词"),
        learned ? h("button", { class: "btn ghost", onclick: () => { AudioMgr.play(p.audio, p.name, {}); Toast.show(`🎧 正在播放：${p.name} 的发音讲解`); } }, "▶ 听发音讲解") : null,
        h("button", { class: "btn ghost", onclick: () => { Modal.close(); location.hash = "#/level/" + p.ep; } }, `去 ${p.ep} 关`)
      ),
      lv ? h("div", { style: "font-size:13px;color:var(--ink-soft);margin-top:10px;text-align:center" }, `出现在《${esc(lv.title)}》）`) : null
    );
    Modal.open(body);
  }

  /* ---------- 稀有度进阶图鉴 ---------- */
  const RARITY_ORDER = ["P", "SR", "SAR", "HR", "SSR", "UR"];
  const RARITY_CN = { P: "普通", SR: "稀有", SAR: "超凡", HR: "英雄", SSR: "传说", UR: "神话" };

  function renderRarity(view, data) {
    view.append(h("div", { class: "card", style: "margin-bottom:14px" },
      h("div", { class: "card-title" }, "🌟 稀有度进阶图鉴"),
      h("div", { style: "font-size:13.5px;color:var(--ink-soft)" },
        "48 只音标精灵分六档稀有度：从 P 到 UR，越难辨的音越稀有。参加四大杯赛的卡丁车比赛解锁卡面，集齐 48 张赛事卡点亮完整图鉴。")
    ));
    // 进阶总图
    view.append(h("div", { class: "card atlas-progress" },
      h("img", { src: "assets/sprites/rarity_progress.webp?v=hud-20261108", alt: "稀有度进阶图鉴" })));

    // 六档分组
    const groups = RARITY_ORDER.map((r) => data.phonemes.filter((p) => p.rarity === r));
    RARITY_ORDER.forEach((r, gi) => {
      const list = groups[gi];
      if (!list.length) return;
      const got = list.filter((p) => Store.isCardUnlocked(p.unit)).length;
      const sec = h("div", { class: "rar-section rar-" + r.toLowerCase() },
        h("div", { class: "rar-section-hd" },
          h("span", { class: "rar-badge rar-" + r.toLowerCase() }, r),
          h("b", null, RARITY_CN[r]),
          h("span", { class: "rar-count" }, `${got} / ${list.length} 已解锁`)),
        h("div", { class: "ph-grid rar-grid" }));
      list.forEach((p) => {
        const isGot = Store.isCardUnlocked(p.unit);
        sec.lastElementChild.append(h("div", {
          class: "ph-tile" + (isGot ? " got" : " locked"), "data-rar": isGot ? r : "",
          onclick: () => openPhModal(p)
        },
          h("div", { class: "ph-sprite" + (isGot ? "" : " dim") },
            h("img", { src: `assets/sprites/${p.unit}.webp?v=hud-20261108`, alt: p.name, loading: "lazy" })),
          h("div", { class: "sym", style: `color:${TYPE_COLOR[p.type]}`, title: `图鉴 ${p.sym}` }, esc(IPA(p))),
          h("div", { class: "nm" }, esc(p.name)),
          isGot ? null : h("span", { class: "lock-tag" }, "🔒"))
        );
      });
      view.append(sec);
    });
  }

  /* ---------- 知识图谱大图 ---------- */
  function renderMaps(view, data) {
    const wrap = h("div", { class: "atlas-maps" });
    MAPS.forEach((m) => {
      wrap.append(h("div", { class: "card atlas-map-card" },
        h("img", { src: `assets/img/${m.key}.webp?v=hud-20261108`, alt: m.title, loading: "lazy" }),
        h("h3", null, m.title),
        h("p", null, m.desc)
      ));
    });
    view.append(h("div", { class: "card", style: "margin-bottom:14px" },
      h("div", { class: "card-title" }, "🗺️ 动画知识图谱"),
      h("div", { style: "font-size:13.5px;color:var(--ink-soft)" }, "四张总纲大图：大地图定路线、城堡与王国定分类、口腔剖面定原理。闯关时它们会一直陪着你。")
    ));
    view.append(wrap);
  }

  window.AtlasView = { render };
})();
