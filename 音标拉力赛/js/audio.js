/* 例词用预生成的美式人声（en-US-AriaNeural，自然语速）。
   音效与引擎声用 WebAudio，避免盖过单词。 */

export function createAudio() {
  let ctx = null;
  let master = null;
  let engineGain = null;
  let engineFilter = null;
  let noiseSrc = null;
  let muted = false;
  const cache = new Map();
  let current = null;
  let speaking = false;

  function ensure() {
    if (ctx) return;
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return;
    ctx = new AC();
    master = ctx.createGain();
    master.gain.value = 0.85;
    master.connect(ctx.destination);

    const bufferSize = 2 * ctx.sampleRate;
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = buffer.getChannelData(0);
    let last = 0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      last = (last + 0.02 * white) / 1.02;
      data[i] = last * 3.5;
    }
    noiseSrc = ctx.createBufferSource();
    noiseSrc.buffer = buffer;
    noiseSrc.loop = true;
    engineFilter = ctx.createBiquadFilter();
    engineFilter.type = "lowpass";
    engineFilter.frequency.value = 240;
    engineGain = ctx.createGain();
    engineGain.gain.value = 0;
    noiseSrc.connect(engineFilter);
    engineFilter.connect(engineGain);
    engineGain.connect(master);
    noiseSrc.start();
  }

  function resume() {
    ensure();
    if (ctx && ctx.state === "suspended") ctx.resume();
  }

  function tone(freq, dur, type, gain, delay = 0) {
    if (!ctx || muted) return;
    const t0 = ctx.currentTime + delay;
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, t0);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(gain, t0 + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    osc.connect(g);
    g.connect(master);
    osc.start(t0);
    osc.stop(t0 + dur + 0.02);
  }

  function playWord(name) {
    resume();
    stopWord();
    let el = cache.get(name);
    if (!el) {
      el = new Audio(`audio/${name}.mp3`);
      el.preload = "auto";
      cache.set(name, el);
    }
    speaking = true;
    el.onended = () => { if (current === el) speaking = false; };
    el.onerror = () => fallbackSpeak(name);
    el.volume = muted ? 0 : 1;
    current = el;
    try { el.currentTime = 0; } catch (e) { /* 尚未就绪时从 0 播 */ }
    el.play().catch(() => fallbackSpeak(name));
  }

  function fallbackSpeak(name) {
    if (!window.speechSynthesis || muted) { speaking = false; return; }
    const u = new SpeechSynthesisUtterance(name);
    u.lang = "en-US";
    u.rate = 1;
    u.onend = () => { speaking = false; };
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }

  function stopWord() {
    if (current) {
      current.pause();
      current = null;
    }
    speaking = false;
    if (window.speechSynthesis) window.speechSynthesis.cancel();
  }

  function preload(words) {
    for (const w of words) {
      if (cache.has(w)) continue;
      const el = new Audio(`audio/${w}.mp3`);
      el.preload = "auto";
      cache.set(w, el);
    }
  }

  return {
    unlock: resume,
    preload,
    playWord,
    stopWord,
    get speaking() { return speaking; },
    setMuted(v) {
      muted = !!v;
      if (current) current.volume = muted ? 0 : 1;
      if (master) master.gain.value = muted ? 0 : 0.85;
    },
    get muted() { return muted; },
    click() { resume(); tone(660, 0.07, "triangle", 0.08); },
    beep(n) { resume(); tone(520 + n * 80, 0.12, "square", 0.06); },
    go() { resume(); tone(523, 0.12, "square", 0.07); tone(784, 0.18, "square", 0.07, 0.1); },
    hit() { resume(); tone(660, 0.08, "triangle", 0.09); tone(880, 0.14, "triangle", 0.08, 0.07); },
    miss() { resume(); tone(196, 0.18, "sine", 0.07); },
    bump() { resume(); tone(140, 0.12, "square", 0.06); tone(90, 0.2, "sine", 0.08, 0.04); },
    turbo() { resume(); tone(440, 0.2, "sawtooth", 0.04); tone(660, 0.22, "sawtooth", 0.04, 0.08); },
    fanfare() {
      resume();
      [523, 659, 784, 1046].forEach((f, i) => tone(f, 0.22, "triangle", 0.07, i * 0.12));
    },
    engine(speed, boosting) {
      if (!ctx || !engineGain || muted) return;
      const target = Math.min(0.045, 0.012 + speed / 9000) * (boosting ? 1.4 : 1);
      engineGain.gain.setTargetAtTime(speaking ? target * 0.25 : target, ctx.currentTime, 0.08);
      engineFilter.frequency.setTargetAtTime(180 + speed * 0.6, ctx.currentTime, 0.1);
    },
    engineOff() {
      if (ctx && engineGain) engineGain.gain.setTargetAtTime(0.0001, ctx.currentTime, 0.05);
    },
  };
}
