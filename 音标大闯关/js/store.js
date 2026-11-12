/* store.js — 本地进度存档（localStorage）
 * FIX-B01：collected 退役（保留键、清空值），新增 rally 解锁状态，知识 / 卡双轨解耦。
 *   legacyCollected : 老存档 collected 的只读快照（sym 数组），供 hasLearned 派生「已学」知识
 *   rally.unlocked  : 按 unit id（U01–U48）存赛事地图解锁的音标卡，唯一解锁来源
 *   幂等首次加载迁移：以「原始存档」是否已含 v2 rally 判定，避免 blank() 默认值遮蔽老存档
 */
(function () {
  const KEY = "ipa-quest-v1";
  const BAK_KEY = KEY + ".v1.bak";
  const blank = () => ({
    stars: {},
    collected: [],          // 退役字段：键保留、值恒为空（旧页面调用 isCollected 不抛错）
    legacyCollected: [],    // 老存档只读快照
    rally: { schemaVersion: 2, unlocked: [] },
    sound: true,
    lastEp: "EP00"
  });
  let data = blank();

  /* ---------- FIX-C08：跨站共享存档（单键 ipa-quest-v1）------------------------
   * 两站同源部署、共用同一个 localStorage 单键；rally 是共享嵌套对象：
   *   大闯关权威域：stars / collected / legacyCollected / sound / lastEp
   *                 + rally.schemaVersion / rally.collectRetiredAt / rally.unlocked / rally.unlockLog
   *   拉力赛权威域：rally.gems / shields / paint / trim / ownedPaints / ownedTrims / EP02 / howSeen
   * 旧实现是「内存单例快照全量覆盖」：load() 只在模块加载时读一次，此后任何写都把那一刻的
   * data 整体写回，抹掉同期别站写入。修复 = 写前重读最新整对象 → 只把别站权威域并入本次
   * 内存快照 → 写回；并用 storage 事件刷新内存视图。localStorage 无原子 CAS，本方案把竞态
   * 窗口从「整个页面生命周期」压到 rawRead()→writeRaw() 之间，不追求数学零竞态。
   *
   * 字段级 merge 规则（落地准则）：
   *   collected                 恒 []，不合并、不从别站并回非空
   *   legacyCollected           只读快照，不取并集、不被覆盖
   *   rally.schemaVersion       固定 2，不动（rawHasV2 判据）
   *   rally.collectRetiredAt    保留首次值（prev ||）
   *   rally.unlocked / unlockLog / ownedPaints / ownedTrims   取并集
   *        （unlocked / unlockLog 由本文件 unionArr 落地；ownedPaints / ownedTrims
   *          由拉力赛 main.js commit() 落地并集，本文件只做 LWW 透传、绝不覆盖别站最新值）
   *   rally.gems / rally.shields    delta（+拾取 / -消费），禁绝对值覆盖、禁 max/min
   *        （由拉力赛 race.js applyWalletDelta() 与 main.js 购买 mut 落地）
   *   rally.EP02                  stars/bestAcc 取 max、played 累加、lastPlace/diff 取最新
   *        （由拉力赛 main.js openResults() 落地）
   *   rally.howSeen               OR（true 优先）
   *   rally.maps                  C 段四区杯赛成绩，拉力赛权威；整对象 LWW
   *   rally.lastMap / lastChar    C 段地图 / 车手偏好，拉力赛权威；单字段 LWW
   *   sound / paint / trim / lastEp   单字段 LWW，以本次操作为准
   * --------------------------------------------------------------------------- */
  const RALLY_FOREIGN = ["gems", "shields", "paint", "trim", "ownedPaints", "ownedTrims", "EP02", "howSeen",
    "maps", "lastMap", "lastChar"];

  /* 数组去重并集，保序，a 优先；keyOf 给定时按其结果去重（unlockLog 用 unit+at）。 */
  function unionArr(a, b, keyOf) {
    const out = [];
    const seen = new Set();
    (Array.isArray(a) ? a : []).concat(Array.isArray(b) ? b : []).forEach((x) => {
      if (x == null) return;
      const k = keyOf ? keyOf(x) : x;
      if (seen.has(k)) return;
      seen.add(k);
      out.push(x);
    });
    return out;
  }

  /* 只读最新原始整对象：不迁移、不写 bak、失败返回 null。 */
  function rawRead() {
    try {
      const raw = localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (e) { return null; }
  }

  /* 原始全量写回（不带任何 merge）；迁移 / reset 专用，保证迁移产物逐字节等价。 */
  function writeRaw(obj) {
    try { localStorage.setItem(KEY, JSON.stringify(obj)); } catch (e) {}
  }

  /* save() 与 storage 监听共用的唯一一份 merge 逻辑：把 source 里属于别站权威域的
     rally 子字段并入 target 的内存视图。只并子字段，绝不整体替换 rally（浅合并会抹数据）。 */
  function refreshFromRaw(target, source) {
    if (!source || typeof source !== "object") return target;
    const src = source.rally;
    if (!src || typeof src !== "object") return target;
    if (!target.rally || typeof target.rally !== "object") target.rally = { schemaVersion: 2, unlocked: [] };
    const dst = target.rally;
    /* 拉力赛专属子字段：大闯关从不写，取最新值（LWW 透传）即可，不覆盖别站。 */
    RALLY_FOREIGN.forEach((k) => { if (k in src) dst[k] = src[k]; });
    /* unlocked / unlockLog 大闯关自身也写（unlockCard），必须取并集。 */
    dst.unlocked = unionArr(dst.unlocked, src.unlocked);
    const log = unionArr(dst.unlockLog, src.unlockLog,
      (e) => String(e && e.unit) + "|" + String(e && e.at));
    if (log.length) dst.unlockLog = log;
    /* 大闯关权威域（stars/collected/legacyCollected/rally.schemaVersion/
       rally.collectRetiredAt/sound/lastEp）一律不动，绝不从 source 并回。 */
    return target;
  }

  function save() {
    /* 写前重读 → 只并入别站权威域 → 全量写回（竞态窗口压到最小）。 */
    refreshFromRaw(data, rawRead());
    writeRaw(data);
  }

  /* 幂等迁移：仅当「原始存档字符串」里没有 v2 rally 时执行。
     判定必须用 parsed 而非 Object.assign 后的 data —— blank() 自带 rally.schemaVersion=2，
     若用 data 判定会把老存档误判为「已迁移」，导致 collected 不清空、legacyCollected 不快照。 */
  function migrateIfNeeded(rawString, parsed) {
    const rawHasV2 = !!(parsed && parsed.rally && parsed.rally.schemaVersion === 2);
    if (rawHasV2) return;   // 已是 v2：不重复追加 / 不覆写 bak / 不重置 unlocked

    /* 回滚点：只在首次写入迁移前的原始字符串 */
    try {
      if (rawString != null && localStorage.getItem(BAK_KEY) === null) {
        localStorage.setItem(BAK_KEY, rawString);
      }
    } catch (e) {}

    /* legacyCollected：只读快照，幂等（已建立则不再覆写 / 追加） */
    if (!Array.isArray(data.legacyCollected) || data.legacyCollected.length === 0) {
      data.legacyCollected = Array.isArray(data.collected) ? data.collected.slice() : [];
    }
    /* collected 退役：保留键、清空值 */
    data.collected = [];
    /* rally v2：保留已有 unlocked（不重置），补 schemaVersion / collectRetiredAt */
    const prev = (data.rally && typeof data.rally === "object") ? data.rally : {};
    data.rally = Object.assign({}, prev, {
      schemaVersion: 2,
      unlocked: Array.isArray(prev.unlocked) ? prev.unlocked.slice() : [],
      collectRetiredAt: prev.collectRetiredAt || new Date().toISOString()
    });
    writeRaw(data);   // FIX-C08：迁移必须绕过 merge，产物与改动前逐字节等价
  }

  function load() {
    let rawString = null, parsed = null;
    try {
      rawString = localStorage.getItem(KEY);
      parsed = rawString ? JSON.parse(rawString) : null;
      data = Object.assign(blank(), parsed || {});
    } catch (e) { data = blank(); parsed = null; rawString = null; }
    migrateIfNeeded(rawString, parsed);
    return data;
  }
  load();

  /* FIX-C08：同域别的标签写入 KEY 时刷新内存视图，避免长期开着的标签持有陈旧快照。
     只改内存、绝不写回（避免 storage 事件风暴）；绝不调用 load() / migrateIfNeeded() /
     写 BAK_KEY —— 迁移只允许在模块加载时（上面的 load()）跑一次。 */
  window.addEventListener("storage", (e) => {
    if (e.key !== KEY || !e.newValue) return;
    let incoming;
    try { incoming = JSON.parse(e.newValue); } catch (err) { return; }
    refreshFromRaw(data, incoming);
  });

  /* ---------- 双轨派生 ---------- */
  /* 已学集合 = legacyCollected（老存档快照，英式 sym）+ stars（已通关关卡里的 phoneme）。
     同时索引 sym 与 unit 两种键：后续美式显示迁移后按 unit 调用依然命中，避免 ɒ/ɑː 撞键。 */
  function learnedSet() {
    const s = new Set();
    const D = window.IPA_DATA || {};
    const P = D.phonemes || [];
    const bySym = {};
    P.forEach((p) => { if (p && p.sym) bySym[p.sym] = p; });
    (Array.isArray(data.legacyCollected) ? data.legacyCollected : []).forEach((sym) => {
      if (!sym) return;
      s.add(sym);
      const p = bySym[sym];
      if (p) { if (p.sym) s.add(p.sym); if (p.unit) s.add(p.unit); }
    });
    (D.levels || []).forEach((l) => {
      if ((data.stars[l.ep] || 0) >= 1) {
        (l.phonemes || []).forEach((p) => {
          if (!p) return;
          if (p.sym) s.add(p.sym);
          if (p.unit) s.add(p.unit);
        });
      }
    });
    return s;
  }
  function learnedCount() {
    const s = learnedSet();
    return ((window.IPA_DATA && window.IPA_DATA.phonemes) || [])
      .filter((p) => s.has(p.unit) || s.has(p.sym)).length;
  }

  const Store = {
    get data() { return data; },

    starsOf(ep) { return data.stars[ep] || 0; },
    setStars(ep, n) {
      if (n > (data.stars[ep] || 0)) data.stars[ep] = n;
      data.lastEp = ep; save();
    },
    totalStars() {
      return Object.values(data.stars).reduce((a, b) => a + b, 0);
    },

    /* 知识轨计数：已学数（HUD 用，永不归零） */
    learnedCount: learnedCount,
    /** 兼容旧名：语义改为「已学数」，避免 HUD 归零惊吓 */
    collectedCount() { return learnedCount(); },
    /** 卡轨计数：已解锁赛事卡数（后续 B2 用） */
    cardCount() { return Store.unlockedCards().length; },

    /* 知识轨：永不锁 key_point / mnemonic / words / ▶ 讲解 / 知识图谱。
       参数可为 sym 或 unit id，内部两种键均可命中。 */
    hasLearned(key) { return !!key && learnedSet().has(key); },
    /** 兼容旧名（已废弃）：指向知识轨，仅供残留旧调用不抛错 */
    isCollected(key) { return Store.hasLearned(key); },

    /* 卡轨：唯一解锁来源 = 赛事地图 × 卡丁车比赛结果，按 unit id */
    isCardUnlocked(unitId) {
      return !!(unitId && data.rally && Array.isArray(data.rally.unlocked)
        && data.rally.unlocked.includes(unitId));
    },
    unlockedCards() {
      return (data.rally && Array.isArray(data.rally.unlocked))
        ? data.rally.unlocked.slice() : [];
    },
    /** 解锁一张卡（供后续 B2 赛事地图调用；本轮只提供 API，不接 UI）。
        meta 可选：来源杯赛 / 名次等，仅记入 rally.unlockLog，不影响 unlocked 判定。幂等去重。 */
    unlockCard(unitId, meta) {
      if (!unitId) return false;
      if (!data.rally || typeof data.rally !== "object") data.rally = { schemaVersion: 2, unlocked: [] };
      if (!Array.isArray(data.rally.unlocked)) data.rally.unlocked = [];
      if (data.rally.unlocked.includes(unitId)) return false;
      data.rally.unlocked.push(unitId);
      if (meta) {
        if (!Array.isArray(data.rally.unlockLog)) data.rally.unlockLog = [];
        data.rally.unlockLog.push({ unit: unitId, at: new Date().toISOString(), meta: meta });
      }
      save();
      return true;
    },
    /** 退役：保留导出以免旧调用抛错，no-op */
    collect() { return false; },

    /** 解锁规则：EP00 永远开放；第 n 关需第 n-1 关拿到至少 1 星（关卡解锁不属本轮，保持不变） */
    isUnlocked(ep) {
      const idx = LEVEL_INDEX[ep];
      if (idx === undefined) return false;
      if (idx === 0) return true;
      const prev = "EP" + String(idx - 1).padStart(2, "0");
      return Store.starsOf(prev) >= 1;
    },
    /** 当前应挑战的关卡（第一颗星都没拿到的已解锁关） */
    currentEp() {
      for (let i = 0; i < 30; i++) {
        const ep = "EP" + String(i).padStart(2, "0");
        if (Store.starsOf(ep) < 1 && Store.isUnlocked(ep)) return ep;
      }
      return null; // 全部通关
    },
    allCleared() {
      for (let i = 0; i < 30; i++) {
        if (Store.starsOf("EP" + String(i).padStart(2, "0")) < 1) return false;
      }
      return true;
    },
    setSound(on) { data.sound = !!on; save(); },
    soundOn() { return data.sound !== false; },
    reset() { data = blank(); writeRaw(data); },   // FIX-C08：reset 同样绕过 merge
  };

  const LEVEL_INDEX = {};
  (window.IPA_DATA.levels || []).forEach((l, i) => { LEVEL_INDEX[l.ep] = i; });

  window.Store = Store;
})();
