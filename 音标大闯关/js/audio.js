/* audio.js — 播客音频播放 + 浏览器语音合成 + WebAudio 音效 */
(function () {
  const A = {
    el: new Audio(),
    cur: null,           // 当前播放的音频 key
    onTick: null, onEnd: null, onPlay: null, onPause: null,
    _enVoice: null,
  };

  /* ---------- 音频播放（单例 <audio>：播客整期 / 音标短音共用一条轨道） ---------- */
  A._src = null;   // 当前已加载的音频 URL，用于 播放/暂停/恢复 的切换判定
  A.el.preload = "auto";

  function _wire(cb) {
    A.onTick = cb && cb.onTick; A.onEnd = cb && cb.onEnd;
    A.onPlay = cb && cb.onPlay; A.onPause = cb && cb.onPause;
  }

  /* 可靠地把 <audio> 推入播放态：
     若媒体尚未就绪（readyState<1 / 上次 play 被打断 / 未缓冲到），
     el.play() 会静默 reject 而不触发 "play" —— 这正是「暂停后点恢复不播」的根因。
     这里挂一次性 canplay，数据到位后自动续播，修复该 bug。 */
  function _doPlay() {
    const p = A.el.play();
    if (p && p.catch) {
      p.catch((err) => {
        if (err && (err.name === "NotSupportedError" || err.name === "AbortError" || err.name === "InvalidStateError" || err.name === "NotAllowedError")) {
          const onCan = () => { A.el.removeEventListener("canplay", onCan); A.el.play().catch(() => {}); };
          A.el.addEventListener("canplay", onCan, { once: true });
        } else if (window.Toast) {
          Toast.show("音频加载失败，请检查网络后重试");
        }
      });
    }
  }

  /* 播放/暂停 切换（针对同一音源）：
     - 该源正在播放 → 暂停（保留 currentTime）
     - 该源已暂停   → 恢复（从暂停处续播）
     - 切到新音源   → 从头播放 */
  A.toggle = function (src, label, cb) {
    _wire(cb);
    if (A._src === src) {
      if (!A.el.paused) { A.el.pause(); return; }
      _doPlay();   // 已暂停 → 恢复
      return;
    }
    A._src = src; A.el.src = src; _doPlay();   // 新音源 → 从头播
  };

  /* 兼容旧接口：按 key（ep01 / ep01.opus / u01）播放整期音频（toggle 语义）。
     数据里的 audio 字段本身带 ".opus"，这里先归一化，避免拼成 "xx.opus.opus" */
  A.play = function (key, label, cb) {
    const k = String(key || "").replace(/\.opus$/i, "");
    A.cur = k;
    A.toggle("assets/audio/" + k + ".opus", label, cb);
  };

  /* 播放 48 音标“短音”（准确读音，assets/audio/ph/uXX.opus），
     用于点音标 chip / 图鉴“听这个音”，替代 3–8 分钟的整期播客 */
  A.playPhoneme = function (unit, label, cb) {
    const k = String(unit || "").toLowerCase().replace(/\.opus$/, "");
    if (!k) return;
    A.cur = "ph/" + k;
    A.toggle("assets/audio/ph/" + k + ".opus", label, cb);
  };

  A.pause = function () { A.el.pause(); };
  A.stop = function () {
    A.el.pause();
    try { A.el.removeAttribute("src"); A.el.load(); } catch (e) {}
    A._src = null; A.cur = null;
  };

  A.el.addEventListener("timeupdate", () => { if (A.onTick) A.onTick(A.el); });
  A.el.addEventListener("play", () => { if (A.onPlay) A.onPlay(A.el); });
  A.el.addEventListener("pause", () => { if (A.onPause) A.onPause(A.el); });
  A.el.addEventListener("ended", () => {
    if (A.onEnd) A.onEnd(A.el);
    A.cur = null; A._src = null;   // 播完归位：再点同键＝从头重播
  });

  /* ---------- 语音合成（单词/题干朗读） ---------- */
  function pickVoice() {
    if (!window.speechSynthesis) return null;
    const vs = speechSynthesis.getVoices();
    if (!vs.length) return null;
    return vs.find((v) => /en[-_]US/i.test(v.lang) && /female|ana|zira|samantha|aria|jenny/i.test(v.name))
        || vs.find((v) => /en[-_]US/i.test(v.lang))
        || vs.find((v) => /^en/i.test(v.lang)) || null;
  }
  if (window.speechSynthesis) {
    speechSynthesis.getVoices();
    speechSynthesis.onvoiceschanged = () => { A._enVoice = pickVoice(); };
  }

  A.speakEn = function (text, rate) {
    if (!window.speechSynthesis) return false;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "en-US"; u.rate = rate || 0.85; u.pitch = 1.05;
    if (!A._enVoice) A._enVoice = pickVoice();
    if (A._enVoice) u.voice = A._enVoice;
    speechSynthesis.speak(u);
    return true;
  };
  A.speakZh = function (text) {
    if (!window.speechSynthesis) return;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = "zh-CN"; u.rate = 0.95;
    speechSynthesis.speak(u);
  };
  A.ttsReady = function () {
    return !!window.speechSynthesis && !!pickVoice();
  };

  /* ---------- WebAudio 合成音效 ---------- */
  let ctx = null;
  function ac() {
    if (!ctx) { const C = window.AudioContext || window.webkitAudioContext; if (C) ctx = new C(); }
    if (ctx && ctx.state === "suspended") ctx.resume();
    return ctx;
  }
  function tone(freq, t0, dur, type, vol) {
    const c = ac(); if (!c) return;
    const o = c.createOscillator(), g = c.createGain();
    o.type = type || "sine"; o.frequency.value = freq;
    const t = c.currentTime + t0;
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(vol || 0.18, t + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g); g.connect(c.destination);
    o.start(t); o.stop(t + dur + 0.05);
  }
  A.sfx = function (name) {
    if (!Store.soundOn()) return;
    try {
      if (name === "click") tone(880, 0, .07, "triangle", .10);
      else if (name === "correct") { tone(659, 0, .12, "sine", .16); tone(988, .1, .22, "sine", .16); }
      else if (name === "wrong") { tone(220, 0, .18, "sawtooth", .10); tone(165, .12, .26, "sawtooth", .10); }
      else if (name === "star") { tone(1319, 0, .1, "sine", .14); tone(1760, .08, .3, "sine", .12); }
      else if (name === "fanfare") { [523, 659, 784, 1047, 1319].forEach((f, i) => tone(f, i * .13, .3, "triangle", .15)); }
      else if (name === "levelup") { tone(392, 0, .15, "triangle", .16); tone(523, .12, .15, "triangle", .16); tone(659, .24, .3, "triangle", .16); }
    } catch (e) {}
  };

  window.AudioMgr = A;
})();
