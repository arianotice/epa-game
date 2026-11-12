/* projcard.js — 「项目代表词卡」弹窗
   点单个音标 → 弹出该音标在项目里的一组代表词（boommanpro/phonetic_symbol_web），
   并播放主词真人录音（assets/audio/ph/uXX.opus）。
   入口：首页故事线音标 chip / 画廊卡、关卡页音标学习卡、图鉴「单独听这个音」。
   对外：window.ProjCard.show(phoneme, {autoplay})
*/
(function () {
  /* FIX-C03：面向用户的大字一律取美式 displayIpa（按稳定 unit id 查表），表缺项回退英式 sym。 */
  const IPA = (p) => (window.IPA_DISPLAY && window.IPA_DISPLAY[p.unit] && window.IPA_DISPLAY[p.unit].displayIpa) || p.sym;

  const TYPE_COLOR = {
    "vowel-long": "var(--blue)", "vowel-short": "var(--red)", "diphthong": "var(--purple)",
    "cons-clear": "var(--red)", "cons-voiced": "var(--green)", "nasal": "var(--green)",
    "lateral": "var(--green)", "semivowel": "var(--blue)",
  };
  const TYPE_LABEL = {
    "vowel-long": "紧元音", "vowel-short": "松元音", "diphthong": "双元音",
    "cons-clear": "清辅音", "cons-voiced": "浊辅音", "nasal": "鼻音",
    "lateral": "舌侧音", "semivowel": "半元音",
  };
  const RARITY_CN = { P: "普通", SR: "稀有", SAR: "超凡", HR: "英雄", SSR: "传说", UR: "神话" };

  let current = null;   // 当前卡对应的音标 unit，用于 toggle 播放
  let isPlaying = false;

  function show(p, opts) {
    if (!p || !p.unit) return;
    const { Modal, h, esc, Toast } = window.App;
    const autoplay = opts === undefined ? true : opts.autoplay;
    const main = p.projMain || "";
    const others = p.projWords || [];
    const color = TYPE_COLOR[p.type] || "var(--gold-deep)";

    const playBtn = h("button", { class: "btn projcard-play" }, "🎧 听真人录音");
    function wirePlay() {
      playBtn.onclick = () => {
        AudioMgr.sfx("click");
        AudioMgr.playPhoneme(p.unit, main, {
          onPlay: () => { isPlaying = true; playBtn.textContent = "⏸ 停止"; playBtn.classList.add("on"); },
          onPause: () => { isPlaying = false; playBtn.textContent = "🎧 听真人录音"; playBtn.classList.remove("on"); },
          onEnd: () => { isPlaying = false; playBtn.textContent = "🔁 再听一遍"; playBtn.classList.remove("on"); },
        });
      };
    }
    wirePlay();

    const chips = h("div", { class: "projcard-words" });
    if (main) {
      chips.append(h("button", {
        class: "word-chip main", title: "主录音词 · 点我听真人朗读",
        onclick: () => { AudioMgr.sfx("click"); playBtn.onclick && playBtn.click(); }
      },
        h("span", { class: "ipa" }, esc(main)),
        h("small", null, (others ? "主词" : "")),
        h("em", { class: "rec-tag" }, "🎙 真人")));
    }
    others.forEach((w) => {
      chips.append(h("button", {
        class: "word-chip", title: "点我听真人朗读",
        onclick: () => { AudioMgr.sfx("click"); if (!AudioMgr.speakEn(w.w, 0.9)) Toast.show("当前浏览器不支持语音朗读"); }
      }, h("span", { class: "ipa" }, esc(w.w)), w.zh ? h("small", null, esc(w.zh)) : null));
    });

    const rar = p.rarity ? h("span", { class: "rar-badge rar-" + p.rarity.toLowerCase() }, p.rarity + " " + (RARITY_CN[p.rarity] || "")) : null;

    const body = h("div", { class: "modal projcard" },
      h("button", { class: "close-x", onclick: () => Modal.close() }, "✕"),
      h("div", { class: "projcard-sym" },
        h("span", { class: "ipa", style: "color:" + color, title: `图鉴 ${p.sym}` }, esc(IPA(p))),
        h("span", { class: "projcard-name" }, esc(p.name))),
      h("div", { class: "projcard-tags" },
        h("span", { class: "tag", style: "color:" + color }, TYPE_LABEL[p.type] || ""),
        rar ? rar : null,
        h("span", { class: "projcard-from" }, "来自项目词库")),
      h("div", { class: "projcard-block-t" }, "🎙 项目代表词"),
      chips,
      h("div", { class: "projcard-audio" }, playBtn,
        h("small", { class: "projcard-tip" }, "主词是真人录音，点它或按钮听朗读；其它同音词点一下即听。")),
      h("div", { class: "result-actions" },
        h("button", { class: "btn ghost", onclick: () => { Modal.close(); location.hash = "#/level/" + p.ep; } }, "去 " + (p.ep || "对应") + " 关学这个音"))
    );

    Modal.open(body);
    current = p.unit;
    if (autoplay) playBtn.click();
  }

  window.ProjCard = { show };
})();
