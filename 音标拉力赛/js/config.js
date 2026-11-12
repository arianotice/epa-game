/* 声音拉力赛 · 四区杯赛题库与赛道参数
   音值只取 window.IPA_DISPLAY[unit].displayIpa（Vocabulary.com 美式口径）。
   每个词按稳定 unit id 绑定；sym / alias 只作角标，displayIpa 禁止做键（U05/U07 同为 ɑ）。
   C07 锁定的 length:"长"/"短" 与两条 hint 原文本表保留；length 在新簇里仅作
   A/B 两侧的视觉分组键（is-long / is-short），不再承载长短音语义。 */

export const CACHE_TAG = "hud-20261108";

export const TUNING = {
  straight: 6800,
  radius: 900,
  roadHalf: 520,
  laneLateral: 0.55,
  /* C 段：两圈制。commits 是「每一圈」的门位，总门数 = laps × commits.length。 */
  laps: 2,
  commits: [0.24, 0.68],
  mergeDt: 0.028,
};

export const KART_TYPE = "探险卡丁";

/** 撞车：沿赛道和横向都靠得很近才算。减速数秒，并插入一题。 */
export const COLLIDE = {
  along: 130,
  lateral: 0.22,
  slow: 2.2,
  think: 2.7,
};

/* C 段提速：2 圈理论上限 148.1s / 128.4s，给减速与答题留出 ≥ 30s 缓冲。 */
export const DIFFICULTY = {
  follow: {
    id: "follow",
    label: "跟读档",
    blurb: "车更慢，车道更宽，听到之后有更长时间转向",
    speed: 260,
    steer: 3.5,
    preview: 4.2,
    fork: 3.6,
    wide: true,
  },
  listen: {
    id: "listen",
    label: "听辨档",
    blurb: "常速。听对就加速，连续听对打出清晰喷",
    speed: 300,
    steer: 3.1,
    preview: 4.0,
    fork: 3.4,
    wide: false,
  },
};

/* 角色轻版：只影响转向速率 / 起跳滞空 / 默认车色，不动计分与解锁口径。 */
export const CHARACTERS = [
  { id: "bobo", name: "波波队长", blurb: "稳重，转向温和", steerMul: 0.90, airMul: 1.00, body: "#3d8eb8" },
  { id: "q", name: "小 Q", blurb: "灵活，跳得更高", steerMul: 1.15, airMul: 1.20, body: "#e0b44a" },
  { id: "mimi", name: "咪咪", blurb: "均衡，好上手", steerMul: 1.00, airMul: 1.10, body: "#1e7a4f" },
];

/* C07 锁定的基础两项：逐字不动（display 字段与 sprite tag 为 C 段新增）。 */
export const VOWELS = {
  i: {
    ipa: "i",
    alias: "iː",
    length: "长",
    guide: ["feet", "seat", "me"],
    hint: "嘴角拉开，肌肉绷紧",
    sprite: `../音标大闯关/assets/sprites/U01.webp?v=${CACHE_TAG}`,
    color: "#1f618d",
  },
  "ɪ": {
    ipa: "ɪ",
    alias: "ɪ",
    length: "短",
    guide: ["sit", "gym"],
    hint: "嘴放松，轻轻一收",
    sprite: `../音标大闯关/assets/sprites/U02.webp?v=${CACHE_TAG}`,
    color: "#b03a2e",
  },
};

/* 18 个音素，四个杯赛地图共用。ipa 与 IPA_DISPLAY[unit].displayIpa 逐字相等。
   label 用于「看词选发音类别」题型；tone 只驱动 is-long / is-short 配色。
   同一对的两个 label 必须互异，否则 type 题会失去区分度（B7 断言）。 */
const A_COLOR = "#1f618d";
const B_COLOR = "#b03a2e";
function ph(unit, ipa, alias, label, length, tone, hint) {
  return {
    unit, ipa, alias, label, length, tone, hint,
    color: tone === "long" ? A_COLOR : B_COLOR,
    sprite: `../音标大闯关/assets/sprites/${unit}.webp?v=${CACHE_TAG}`,
  };
}

export const PHONEMES = {
  U01: ph("U01", "i", "iː", "紧音", "长", "long", "嘴角拉开，肌肉绷紧"),
  U02: ph("U02", "ɪ", "ɪ", "松音", "短", "short", "嘴放松，轻轻一收"),
  U03: ph("U03", "ɛ", "e", "小口音", "长", "long", "嘴角微开，下巴放低一点"),
  U04: ph("U04", "æ", "æ", "大口音", "短", "short", "嘴巴张大，像轻轻咬一口苹果"),
  U06: ph("U06", "ʌ", "ʌ", "中央音", "长", "long", "嘴放松，声音从嗓子中间轻轻弹出"),
  U07: ph("U07", "ɑ", "ɒ", "开口音", "短", "short", "下巴全放下，嘴巴张到最大"),
  U09: ph("U09", "ʊ", "ʊ", "短圆唇", "长", "long", "嘴唇拢圆，声音短促放松"),
  U10: ph("U10", "u", "uː", "长圆唇", "短", "short", "嘴唇撅成小圆，声音往前送"),
  U11: ph("U11", "ɜr", "ɜː", "卷舌中央", "长", "long", "舌头往后收、两边轻轻卷起，带 r 的尾音"),
  U19: ph("U19", "ɛr", "eə", "卷舌开口", "短", "short", "先发 ɛ，再轻轻带出 r 的尾音"),
  U21: ph("U21", "p", "p", "清音", "长", "long", "双唇轻轻一弹，声带不振动"),
  U22: ph("U22", "b", "b", "浊音", "短", "short", "双唇一弹，同时让声带振动"),
  U27: ph("U27", "f", "f", "清音", "长", "long", "上牙轻碰下唇，只送气不振动"),
  U28: ph("U28", "v", "v", "浊音", "短", "short", "上牙轻碰下唇，声带一起振动"),
  U31: ph("U31", "s", "s", "清音", "长", "long", "舌尖靠近上齿龈，送一条细气流"),
  U32: ph("U32", "z", "z", "浊音", "短", "short", "同样是细气流，加上声带振动"),
  U40: ph("U40", "n", "n", "前鼻音", "长", "long", "舌尖抵上齿龈，声音从鼻子出来"),
  U41: ph("U41", "ŋ", "ŋ", "后鼻音", "短", "short", "舌根抬起抵软腭，声音从鼻子深处出来"),
};

function side(unit, word, display) {
  const p = PHONEMES[unit];
  return {
    unit, word, display: display || word,
    ipa: p.ipa, alias: p.alias, label: p.label, length: p.length, tone: p.tone,
    hint: p.hint, sprite: p.sprite, color: p.color,
  };
}
const P = (a, wa, b, wb, db) => [side(a, wa), side(b, wb, db)];

/* 37 对最小对立，四区各一池。全部为真实词、同一辅音框架下的音值对立；
   rhotic 簇（U11/U19）例词均带 r 色彩；不含 ɒ/ɑː→ɑ 合并音互相对立。 */
export const PAIRS_BY_MAP = {
  camp: [
    P("U01", "seat", "U02", "sit"),
    P("U01", "sheep", "U02", "ship"),
    P("U01", "feet", "U02", "fit"),
    P("U01", "leave", "U02", "live"),
    P("U03", "bed", "U04", "bad"),
    P("U03", "pen", "U04", "pan"),
    P("U03", "men", "U04", "man"),
    P("U03", "said", "U04", "sad"),
  ],
  castle: [
    P("U06", "cut", "U07", "cot"),
    P("U06", "luck", "U07", "lock"),
    P("U06", "duck", "U07", "dock"),
    P("U06", "cup", "U07", "cop"),
    /* 扩池：单局取 4 对，池 >= 10 时任一对出现率理论上限 0.40，
       远低于 B5 的 0.60 阈值（原 7 对上限 0.571 会随机越线）。 */
    P("U06", "hut", "U07", "hot"),
    P("U06", "pup", "U07", "pop"),
    P("U06", "dull", "U07", "doll"),
    P("U09", "pull", "U10", "pool"),
    P("U09", "full", "U10", "fool"),
    P("U09", "look", "U10", "luke", "Luke"),
  ],
  kingdom: [
    P("U21", "pat", "U22", "bat"),
    P("U21", "pig", "U22", "big"),
    P("U21", "cap", "U22", "cab"),
    P("U21", "pear", "U22", "bear"),
    P("U27", "fan", "U28", "van"),
    P("U27", "fine", "U28", "vine"),
    P("U27", "leaf", "U28", "leave"),
    P("U27", "safe", "U28", "save"),
  ],
  peak: [
    P("U31", "sip", "U32", "zip"),
    P("U31", "sue", "U32", "zoo"),
    P("U31", "bus", "U32", "buzz"),
    P("U31", "rice", "U32", "rise"),
    P("U40", "sin", "U41", "sing"),
    P("U40", "win", "U41", "wing"),
    P("U40", "ban", "U41", "bang"),
    P("U40", "thin", "U41", "thing"),
    P("U11", "her", "U19", "hair"),
    P("U11", "fir", "U19", "fair"),
    P("U11", "stir", "U19", "stair"),
  ],
};

export const RACE_MAPS = [
  {
    id: "camp", zone: "出发营地", name: "出发营地杯", short: "紧松元音",
    blurb: "先分清 i / ɪ 的紧松，再听 ɛ / æ 的口型大小。",
    clusters: [["U01", "U02"], ["U03", "U04"]],
    unlock: ["U01", "U02", "U03", "U04"],
  },
  {
    id: "castle", zone: "元音城堡", name: "元音城堡杯", short: "后元音与圆唇",
    blurb: "ʌ / ɑ 的开口大小，ʊ / u 的短长圆唇。",
    clusters: [["U06", "U07"], ["U09", "U10"]],
    unlock: ["U06", "U07", "U09", "U10"],
  },
  {
    id: "kingdom", zone: "辅音王国", name: "辅音王国杯", short: "清浊辅音",
    blurb: "p / b、f / v：同一口型，只差声带振不振动。",
    clusters: [["U21", "U22"], ["U27", "U28"]],
    unlock: ["U21", "U22", "U27", "U28"],
  },
  {
    id: "peak", zone: "进阶峰", name: "进阶峰杯", short: "摩擦·鼻音·卷舌",
    blurb: "s / z 的细气流、n / ŋ 的前后鼻、ɜr / ɛr 的卷舌尾音。",
    clusters: [["U31", "U32"], ["U40", "U41"], ["U11", "U19"]],
    unlock: ["U31", "U32", "U40", "U41", "U11", "U19"],
  },
];

export const QUIZ_TYPES = ["word", "ipa", "type"];
export const QUIZ_TITLES = {
  word: "选出听到的词",
  ipa: "选出它的音标",
  type: "选出它的发音类别",
};

/* C07 兼容导出：原 7 对 /i/ ↔ /ɪ/ 逐字保留，旧断言与教学面板仍可用。 */
export const PAIRS = [
  [side("U01", "seat"), side("U02", "sit")],
  [side("U01", "sheep"), side("U02", "ship")],
  [side("U01", "feet"), side("U02", "fit")],
  [side("U01", "beat"), side("U02", "bit")],
  [side("U01", "sleep"), side("U02", "slip")],
  [side("U01", "green"), side("U02", "grin")],
  [side("U01", "cheek"), side("U02", "chick")],
];

export const BOOST = { mul: 1.48, time: 1.4 };
export const TURBO = { mul: 1.92, time: 0.75 };
export const SLOW = { mul: 0.54, time: 0.85 };
export const ROCKET = { mul: 1.55, time: 0.9 };

export function pairKeyOf(pair) {
  return [pair[0].word, pair[1].word].sort().join("/");
}

export function poolOf(mapId) {
  return PAIRS_BY_MAP[mapId] || PAIRS_BY_MAP[RACE_MAPS[0].id];
}

export function allWords() {
  const set = new Set();
  for (const v of Object.values(VOWELS)) v.guide.forEach((w) => set.add(w));
  for (const pairs of [PAIRS, ...Object.values(PAIRS_BY_MAP)]) {
    for (const [a, b] of pairs) { set.add(a.word); set.add(b.word); }
  }
  return [...set];
}

function shuffle(list, rand) {
  const a = list.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rand() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

/* 额外题选对：去重窗口 3，最近 3 对不再出现 → 连续同对率 0%。 */
export function pickQuizPair(pool, recent = [], rand = Math.random) {
  const fresh = pool.filter((p) => !recent.includes(pairKeyOf(p)));
  const from = fresh.length ? fresh : pool;
  return from[Math.floor(rand() * from.length)];
}

/* C 段：为每圈生成独立门对象（lap + lineT），不用跨圈重置 judged / played，
   天然做到第 2 圈仍有题；单局四门词对全局互不重复，题型至少 2 种。 */
export function buildGates(mapId = RACE_MAPS[0].id, rand = Math.random) {
  const pool = poolOf(mapId);
  const need = TUNING.laps * TUNING.commits.length;
  const picked = shuffle(pool, rand).slice(0, need);
  /* 前 3 门是三种题型的随机排列 → 单局必现 3 种，且顺序不固定。 */
  const forcedTypes = shuffle(QUIZ_TYPES, rand);
  const out = [];
  for (let lap = 0; lap < TUNING.laps; lap++) {
    TUNING.commits.forEach((commitT, ci) => {
      const i = lap * TUNING.commits.length + ci;
      const pair = picked[i % picked.length];
      const sayFirst = rand() < 0.5;
      const spoken = sayFirst ? pair[0] : pair[1];
      const other = sayFirst ? pair[1] : pair[0];
      const onRight = rand() < 0.5;
      out.push({
        id: i,
        lap,
        commitT,
        lineT: lap + commitT,
        pairKey: pairKeyOf(pair),
        qType: i < forcedTypes.length ? forcedTypes[i] : QUIZ_TYPES[Math.floor(rand() * QUIZ_TYPES.length)],
        spoken,
        other,
        left: onRight ? other : spoken,
        right: onRight ? spoken : other,
        correctLateral: onRight ? TUNING.laneLateral : -TUNING.laneLateral,
        played: false,
        replayed: false,
        judged: false,
        hit: false,
      });
    });
  }
  return out;
}

export function forkSpan(diff, length) {
  return (diff.fork * diff.speed) / length;
}

export function hitsLane(lateral, correctLateral) {
  if (Math.abs(lateral) < 0.2) return false;
  return Math.sign(lateral) === Math.sign(correctLateral);
}

export function scoreRace(place, correct, total) {
  const acc = total ? Math.min(1, correct / total) : 0;
  let stars = 1;
  if ((place <= 2 && acc >= 0.4) || acc >= 0.6) stars = 2;
  if (place <= 2 && acc >= 0.8) stars = 3;
  return { stars, acc };
}
