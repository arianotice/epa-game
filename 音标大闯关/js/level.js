/* level.js — 关卡页（期配图/播客音频/学习卡）+ 听辨大挑战引擎 */
(function () {
  const { $, $$, h, esc, fmtTime, Toast, Modal, confetti } = window.App;
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
  const REGION_ICON = { camp: "🏕️", vowel: "🏰", cons: "🏛️", peak: "⛰️" };

  function levelOf(ep) {
    return window.IPA_DATA.levels.find((l) => l.ep === ep);
  }

  /* ================= 关卡主页面 ================= */
  function render(view, ep) {
    const lv = levelOf(ep);
    if (!lv) { location.hash = "#/map"; return; }
    if (!Store.isUnlocked(ep)) {
      Toast.show("🔒 这一关还没解锁，先完成上一关吧！");
      location.hash = "#/map"; return;
    }
    AudioMgr.stop();

    /* 头部 */
    view.append(h("div", { class: "level-head" },
      h("a", { class: "back", href: "#/map" }, "← 返回地图"),
      h("div", null,
        h("div", { class: "level-title" }, `${REGION_ICON[lv.region]} ${lv.ep.replace("EP", "第 ")}关 · ${esc(lv.title)}`),
        h("div", { class: "level-scene" }, `${lv.regionName} · 场景：${esc(lv.scene)}`)
      ),
      h("div", { style: "margin-left:auto;font-size:15px;color:var(--gold-deep);font-weight:700" },
        Store.starsOf(ep) > 0 ? "⭐".repeat(Store.starsOf(ep)) + " 已通关" : "未通关")
      )
    );

    const grid = h("div", { class: "level-grid" });

    /* 左：期配图 */
    const imgCard = h("div", { class: "card" },
      h("img", { class: "level-img", src: "assets/img/" + lv.img + "?v=hud-20261108", alt: lv.title + " 配图", loading: "lazy" }),
      h("div", { class: "img-cap" }, `《${esc(lv.title)}》探险配图`)
    );
    grid.append(imgCard);

    /* 右：音频 + 学习卡 */
    const side = h("div");

    /* 播客播放器 */
    const bar = h("i");
    const tCur = h("span", null, "0:00"), tDur = h("span", null, "0:00");
    const playBtn = h("button", { class: "play-btn", "aria-label": "播放本期完整节目" }, "▶");
    const playerCard = h("div", { class: "card" },
      h("div", { class: "card-title" }, "🎧 听波波队长讲故事"),
      h("div", { class: "player" },
        playBtn,
        h("div", { class: "track" },
          h("div", { class: "bar" }, bar),
          h("div", { class: "time" }, tCur, tDur)
        )
      ),
      h("div", { style: "font-size:13px;color:var(--ink-soft);margin-top:6px" },
        "完整探险旅程版（约 5–11 分钟）：情境 → 发音实验室 → 单词宝藏 → 口诀 → 听辨挑战")
    );
    const onTick = (el) => {
      bar.style.width = (el.duration ? (el.currentTime / el.duration) * 100 : 0) + "%";
      tCur.textContent = fmtTime(el.currentTime);
      tDur.textContent = fmtTime(el.duration);
    };
    playBtn.addEventListener("click", () => {
      AudioMgr.sfx("click");
      AudioMgr.play(lv.audio, lv.title, {
        onTick,
        onPlay: () => { playBtn.textContent = "⏸"; },
        onPause: () => { playBtn.textContent = "▶"; },
        onEnd: () => { playBtn.textContent = "▶"; bar.style.width = "0%"; tCur.textContent = "0:00"; },
      });
    });
    side.append(playerCard);

    /* 学习卡（每个音标一张） */
    lv.phonemes.forEach((p) => {
      const symCls = TYPE_CLASS[p.type] || "";
      const wordChips = h("div", { class: "ph-words" });
      /* 项目主词（真人录音）排最前；再列播客单词 */
      if (p.projMain) {
        const mainW = p.projMain;
        const projZh = (p.projWords || []).find((x) => x.w.toLowerCase() === mainW.toLowerCase());
        wordChips.append(h("button", {
          class: "word-chip main", title: "真人录音 · 点击朗读",
          onclick: () => {
            AudioMgr.sfx("click");
            AudioMgr.playPhoneme(p.unit, mainW, {
              onPlay: () => Toast.show("🎙 真人朗读：" + mainW),
            });
          }
        },
          h("span", { class: "ipa" }, esc(mainW)),
          projZh ? h("small", null, esc(projZh.zh || "")) : null,
          h("em", { class: "rec-tag" }, "🎙"))
        );
      }
      p.words.forEach((w) => {
        if (p.projMain && w.w.toLowerCase() === p.projMain.toLowerCase()) return;
        wordChips.append(h("button", {
          class: "word-chip", title: "点击朗读",
          onclick: () => { AudioMgr.sfx("click"); if (!AudioMgr.speakEn(w.w)) Toast.show("当前浏览器不支持语音朗读"); }
        }, h("span", { class: "ipa" }, esc(w.w)), h("small", null, esc(w.zh))));
      });
      side.append(h("div", { class: "card ph-card" },
        h("div", { class: "ph-top" },
          h("div", { class: "ph-sym " + symCls, title: `图鉴 ${p.sym}` }, esc(IPA(p))),
          h("div", null,
            h("div", { class: "ph-name" }, `✨ ${esc(p.name)}`),
            h("span", { class: "tag t-" + (symCls.replace("c-", "")) }, TYPE_LABEL[p.type] || "")
          )
        ),
        h("div", { class: "ph-key" }, esc(p.key_point)),
        wordChips,
        h("div", { class: "mnemonic" }, h("b", null, "📢 口诀"), esc(p.mnemonic))
      ));
    });

    /* 本关单词宝藏总表 */
    if (lv.words.length) {
      const wc = h("div", { class: "ph-words" });
      lv.words.forEach((w) => {
        wc.append(h("button", {
          class: "word-chip", title: "点击朗读",
          onclick: () => { AudioMgr.sfx("click"); if (!AudioMgr.speakEn(w.w)) Toast.show("当前浏览器不支持语音朗读"); }
        }, h("span", { class: "ipa" }, esc(w.w)), h("small", null, esc(w.zh))));
      });
      side.append(h("div", { class: "card ph-card" },
        h("div", { class: "card-title" }, "💎 本关单词宝藏"),
        h("div", { class: "ph-key", style: "margin:0" }, "点单词听发音，跟着念三遍："),
        wc
      ));
    }

    /* 记忆小窍门 + 闯关入口 */
    const tipCard = h("div", { class: "card ph-card" },
      h("div", { class: "card-title" }, "🧭 记忆小窍门"),
      h("div", { class: "tip-box" }, esc(lv.tip))
    );
    side.append(tipCard);

    const startBtn = h("button", { class: "btn red", style: "width:100%;margin-top:14px;font-size:22px" },
      Store.starsOf(ep) > 0 ? "🔁 重考听辨大挑战" : "⚔️ 开始听辨大挑战");
    startBtn.addEventListener("click", () => { AudioMgr.sfx("click"); startQuiz(view, lv); });
    side.append(startBtn);

    grid.append(side);
    view.append(grid);
  }

  /* ================= 挑战引擎 ================= */
  function shuffle(a) {
    a = a.slice();
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }
  function normOpt(o) {
    if (typeof o === "string") return { w: o };
    return { w: o && o.w, zh: o && o.zh };
  }

  function startQuiz(view, lv) {
    // 每关题库已扩充；每次随机抽取 5 题，保证不同用户/次数题目不同，且都来自本关所学
    const quiz = shuffle(lv.quiz).slice(0, 5).map((q) => prepareQ(q, lv));
    const state = { i: 0, correct: 0, spoke: null };

    view.innerHTML = "";
    view.append(h("div", { class: "level-head" },
      h("a", { class: "back", href: "#/level/" + lv.ep }, "← 返回学习"),
      h("div", { class: "level-title" }, `⚔️ 听辨大挑战 · ${lv.ep.replace("EP", "第 ")}关`),
      h("div", { style: "margin-left:auto;font-size:14px;color:var(--ink-soft)" }, "答对 3 题即可通关")
    ));

    const dots = h("div", { class: "quiz-progress" });
    const card = h("div", { class: "card quiz-card" });
    view.append(dots, card);

    function paintDots() {
      dots.innerHTML = "";
      quiz.forEach((q, idx) => {
        const cls = "qdot" + (idx < state.i ? (q._ok ? " ok" : " bad") : "") + (idx === state.i ? " now" : "");
        dots.append(h("i", { class: cls }));
      });
    }

    function showQ() {
      const q = quiz[state.i];
      window.__curQ = q; // 测试/调试钩子
      paintDots();
      card.innerHTML = "";
      card.append(h("div", { class: "quiz-q" }, esc(q.q)));

      if (q.type === "listen") {
        const btn = h("button", { class: "listen-btn", "aria-label": "播放单词" }, "🔊");
        btn.addEventListener("click", () => {
          btn.classList.add("playing");
          AudioMgr.speakEn(q.spoke, 0.8);
          setTimeout(() => btn.classList.remove("playing"), 900);
        });
        card.append(btn, h("div", { style: "font-size:13.5px;color:var(--ink-soft)" }, "点喇叭再听一遍"));
        setTimeout(() => btn.click(), 350);
      } else if (q.type === "count" || q.type === "stress" || q.type === "phrase") {
        const btn = h("button", { class: "listen-btn", "aria-label": "播放" }, "🔊");
        btn.addEventListener("click", () => {
          btn.classList.add("playing");
          AudioMgr.speakEn(q.speak, q.type === "phrase" ? 0.75 : 0.8);
          setTimeout(() => btn.classList.remove("playing"), 1100);
        });
        card.append(btn, h("div", { style: "font-size:13.5px;color:var(--ink-soft)" }, "点喇叭听题目"));
        setTimeout(() => btn.click(), 350);
      }

      const optWrap = h("div", { class: "quiz-opts" + (q.options.length === 3 ? " three" : (q.options.length === 2 ? "" : " one")) });
      const fb = h("div", { class: "feedback" });
      const nextBtn = h("button", { class: "btn", style: "display:none" }, state.i === quiz.length - 1 ? "查看成绩 🏆" : "下一题 ▶");

      q.options.forEach((opt, idx) => {
        const o = normOpt(opt);
        const ob = h("button", { class: "opt" }, h("span", { class: "ipa" }, esc(o.w || "")), o.zh ? h("small", null, esc(o.zh)) : null);
        ob.addEventListener("click", () => {
          if (fb.dataset.done) return;
          fb.dataset.done = "1";
          const ok = idx === q.answer;
          q._ok = ok;
          if (ok) { state.correct++; AudioMgr.sfx("correct"); }
          else AudioMgr.sfx("wrong");
          $$(".opt", optWrap).forEach((b, j) => {
            b.disabled = true;
            if (j === q.answer) b.classList.add("correct");
            if (j === idx && !ok) b.classList.add("wrong");
          });
          fb.append(
            h("div", { class: ok ? "ok" : "no" }, ok ? "🎉 答对啦！" : "💡 答错啦，记住它！"),
            h("div", { class: "why" }, esc(q.explain || ""))
          );
          nextBtn.style.display = "";
          nextBtn.focus();
        });
        optWrap.append(ob);
      });

      nextBtn.addEventListener("click", () => {
        AudioMgr.sfx("click");
        state.i++;
        if (state.i < quiz.length) showQ();
        else finish();
      });

      card.append(optWrap, fb, nextBtn);
    }

    function finish() {
      paintDots();
      const n = state.correct;
      const stars = n >= 5 ? 3 : n >= 4 ? 2 : n >= 3 ? 1 : 0;
      const prev = Store.starsOf(lv.ep);
      Store.setStars(lv.ep, stars);
      /* FIX-B01：退役 collected，闯关只写 stars；音标卡改由赛事地图比赛结果解锁 */

      card.innerHTML = "";
      card.append(
        h("div", { class: "quiz-q" }, stars > 0 ? "🎉 通关成功！" : "😢 差一点点，再来一次！"),
        h("div", { class: "result-stars" },
          ...Array.from({ length: 3 }, (_, i) => h("span", { class: stars > i ? "" : "off" }, "⭐"))
        ),
        h("div", { class: "result-info" }, `答对 ${n} / 5 题` + (stars > prev ? " · 新纪录！" : ""))
      );

      if (lv.phonemes.length) {
        /* FIX-B01：结算只给「学习反馈」，不提图鉴 / 收集 / 卡 */
        card.append(h("div", { style: "font-size:14px;color:var(--ink-soft)" },
          stars > 0
            ? `本关学会了 ${lv.phonemes.length} 个音标，发音要点和口诀随时可回看 📖`
            : `本关遇到 ${lv.phonemes.length} 个音标，再听一遍故事就记住啦`));
        const row = h("div", { class: "collected-row" });
        lv.phonemes.forEach((p) => {
          row.append(h("div", { class: "collected-chip" },
            h("span", { class: "ipa", title: `图鉴 ${p.sym}` }, esc(IPA(p))),
            h("span", null, esc(p.name) + (Store.hasLearned(p.unit) ? " 已学会 ✨" : " 再学一遍"))
          ));
        });
        card.append(row);
      }

      /* 逐颗点亮星星 */
      const starEls = $$(".result-stars span", card);
      starEls.forEach((s, i) => {
        if (i < stars) setTimeout(() => { AudioMgr.sfx("star"); }, 350 + i * 420);
      });
      if (stars > 0) setTimeout(() => { confetti(); AudioMgr.sfx(stars === 3 ? "fanfare" : "levelup"); }, 350 + stars * 420);

      const nextEp = nextLevelEp(lv.ep);
      const acts = h("div", { class: "result-actions" });
      if (stars > 0 && nextEp) {
        acts.append(h("button", { class: "btn green", onclick: () => { location.hash = "#/level/" + nextEp; } }, "下一关 ▶"));
      }
      if (stars === 0) {
        acts.append(h("button", { class: "btn red", onclick: () => startQuiz(view, lv) }, "🔁 再考一次"));
      } else {
        acts.append(h("button", { class: "btn ghost", onclick: () => startQuiz(view, lv) }, "🔁 重考"));
      }
      acts.append(h("button", { class: "btn ghost", onclick: () => { location.hash = "#/map"; } }, "🗺️ 回地图"));
      card.append(acts);
      App.renderHud();
    }

    showQ();
  }

  function prepareQ(q, lv) {
    const out = Object.assign({}, q);
    if (q.type === "listen") {
      // 随机决定读哪个词；选项 = 该词 + 本关其它词作干扰项，凑成 3 个
      const spoke = q.pair.length > 1 ? q.pair[Math.floor(Math.random() * q.pair.length)] : q.pair[0];
      out.spoke = spoke;
      const opts = q.pair.slice();
      const pool = ((lv && lv.words) ? lv.words.map((w) => w.w) : []).filter((w) => !opts.includes(w));
      const distractors = (q.distractors || []).concat(pool);
      while (opts.length < 3 && distractors.length) {
        const d = distractors.splice(Math.floor(Math.random() * distractors.length), 1)[0];
        if (d && !opts.includes(d)) opts.push(d);
      }
      out.options = shuffle(opts).map((w) => ({ w, zh: wordZh(w) }));
      out.answer = out.options.findIndex((o) => o.w === spoke);
      out.explain = out.explain || "这两个词只差一个音，耳朵要多练！";
    } else {
      // choice / count / stress / phrase：选项可能是字符串或对象，统一规范化后洗牌
      const opts = (q.options || []).map(normOpt);
      const correctW = normOpt(q.options[q.answer]).w;
      out.options = shuffle(opts);
      out.answer = out.options.findIndex((o) => o.w === correctW);
    }
    if (!out.explain) out.explain = "";
    return out;
  }

  function wordZh(w) {
    const hit = window.IPA_DATA.levels
      .flatMap((l) => l.words)
      .find((x) => x.w.toLowerCase() === w.toLowerCase());
    return hit ? hit.zh : "";
  }

  function nextLevelEp(ep) {
    const idx = window.IPA_DATA.levels.findIndex((l) => l.ep === ep);
    if (idx < 0 || idx >= 29) return null;
    return window.IPA_DATA.levels[idx + 1].ep;
  }

  window.LevelView = { render };
})();
