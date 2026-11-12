# -*- coding: utf-8 -*-
"""48 音标精灵：形象锚点 + 6 档稀有度光晕 + 统一风格基座 + 提示词生成。

设计原则（对齐项目硬约束）：
- 精灵本体 **不画任何文字 / 音标 / 中文 / 数字**（Agnes 直渲易乱码），文字一律后期 Pillow 合成。
- 每张精灵形象「暗合」该音标的发音动作（取自 data.js 的 name + key_point + mnemonic）。
- 稀有度靠「光晕颜色 + 星星数」区分（P/SR/SAR/HR/SSR/UR 六档）。
- 出图要求纯白底（贴纸风），后期 unkey_white.py 去白底 -> 透明 PNG。
"""
import json, os

HERE = os.path.dirname(__file__)

# --- 统一风格基座（每张都含） ---
STYLE_BASE = (
    "A single cute chibi mascot sound-spirit creature, warm parchment-and-adventure "
    "cartoon sticker style, soft 2.5D rendering, clean gentle shading, thick soft rounded "
    "outlines, cozy warm color palette, with tiny floating sound-wave rings and a few small "
    "sparkles around it. Playful, whimsical and friendly, NOT babyish or toddler-like. "
    "Full upper body, centered, perfectly symmetric front-facing view."
)
WHITE_BG = (
    " The creature stands centered on a completely flat pure solid white background, "
    "single clean white color only, with no floor, no drop shadow, no gradient, no pattern, "
    "no text, no letters, no numbers, no symbols, no watermark, no border. "
    "The white background must be perfectly even and uniform."
)

# --- 6 档稀有度光晕 ---
RARITY_AURA = {
    "P":   "Around the creature is a soft cool silver-blue light aura, plain and simple, no stars.",
    "SR":  "Around the creature is an emerald green glowing aura with one small star sparkle.",
    "SAR": "Around the creature is a golden amber glowing aura with two small star sparkles.",
    "HR":  "Around the creature is a bold ruby-red radiant aura with three small star sparkles.",
    "SSR": "Around the creature is a royal purple magical aura with a small crown halo and four small star sparkles.",
    "UR":  "Around the creature is an intense prismatic rainbow radiant aura with a radiant crown and five small star sparkles.",
}

# --- 48 形象锚点（英文，贴合发音动作，不出现文字） ---
PROFILES = {
    "U01": "a smiling little smile-lady spirit with a big toothy grin and rosy cheeks",
    "U02": "a very relaxed, slouched spirit with half-closed lazy eyes and a small relaxed mouth",
    "U03": "a spirit making a small pouty eh mouth with its lips barely open",
    "U04": "a spirit with a wide open aah mouth and a big joyful grin",
    "U05": "a cheerful little doctor spirit wearing a tiny stethoscope, mouth open, kind face",
    "U06": "a round-bellied spirit poking its own tummy with one finger, making a soft uhh sound",
    "U07": "a spirit blowing one big round soap bubble, cheeks puffed",
    "U08": "a spirit sucking on a wiggly jelly cup with round pouty lips",
    "U09": "a spirit gently nudging a small ball with a soft friendly gesture",
    "U10": "a spirit with round pursed lips blowing out a birthday candle flame",
    "U11": "a bouncy springy spirit with a coiled spring motif and a curling tongue",
    "U12": "a drowsy sighing spirit leaning back, half asleep, letting out a tired sigh",
    "U13": "a spirit sliding down a tiny playground slide with both arms raised",
    "U14": "a spirit riding a little toy airplane that glides down, both wings up",
    "U15": "a cheering spirit with both arms raised in the air, mouth open in a cheer",
    "U16": "a sweet little spirit holding up a small sugar cube, happy face",
    "U17": "a wide-eyed surprised spirit with a big open ooh-whoa mouth",
    "U18": "a spirit leaning close and whispering, cupping one hand to its mouth",
    "U19": "a wind-blown spirit with flowing ribbons and hair, a soft breeze around it",
    "U20": "a little traveler spirit carrying a tiny backpack, ready for a journey",
    "U21": "a small paper-plane spirit puffing out a clean little burst of air",
    "U22": "a spirit drumming on a tiny drum with drumsticks",
    "U23": "a spirit holding a small hammer, tapping it gently",
    "U24": "a spirit striking a small golden bell, a ring of sound",
    "U25": "a spirit with a hand on its mouth giving a soft kh cough",
    "U26": "a surprised spirit mid-hiccup, one eye winking",
    "U27": "a spirit with its top teeth gently on its lip, blowing a cool fff breeze",
    "U28": "a spirit with buzzing lips and a tiny telephone receiver motif",
    "U29": "a spirit with its tongue tip poking between its teeth, a clean thorn emblem, gentle and clear",
    "U30": "a spirit with its tongue between its teeth, a low soft buzz, a small thorn emblem",
    "U31": "a playful little snake spirit making a soft sss hissing shape",
    "U32": "a happy buzzing bee spirit with stripes and small wings",
    "U33": "a hushing librarian spirit pressing one finger to its lips, a tiny book motif, quiet shh",
    "U34": "a spirit with a coiled hissing shape and a small treasure chest motif",
    "U35": "a spirit puffing out a warm round hff breath, cheeks puffed",
    "U36": "a spirit with a curling tongue and a small hook motif, a playful rrr",
    "U37": "a spirit in a little steam-train costume with a tiny puff of smoke, chchch",
    "U38": "a spirit holding a small jam jar with a spoon, jaja, cozy",
    "U39": "a humming spirit with its nose closed and a floating music note, mmm",
    "U40": "a bird-like spirit pecking at tiny grains of rice, nnn",
    "U41": "a snoring little king spirit wearing a small crown, eyes closed, zzz snore",
    "U42": "a cheerful spirit making a happy tongue curl with a small hook motif",
    "U43": "a spirit with very round ooh-wah pouty lips and a little heart",
    "U44": "a quick-gesture spirit with a small yee hand wave, lively",
    "U45": "a spirit giving a tr-tr tap with a small train whistle motif",
    "U46": "a spirit with a dr-dr pecking beak-like gesture",
    "U47": "a spirit hissing ts like a kettle, a tiny spark",
    "U48": "a spirit with a dz-buzz shape and a small gear motif",
}

def load_phonemes():
    txt = open(os.path.join(HERE, "..", "js", "data.js"), encoding="utf-8").read()
    i = txt.index("window.IPA_DATA = ")
    d = json.loads(txt[i + len("window.IPA_DATA = "):].rstrip().rstrip(";"))
    return d["phonemes"]

def load_ipa_display():
    """全站唯一显示值来源：js/ipa-display.js（美式 displayIpa + 英式角标 alias）。
    sym 仍以 data.js 为准，作跨站稳定键，绝不被显示值替换。
    该文件 48 行表是严格 JSON 字面量（全键双引号），与 :91-95 同款纯 json.loads；
    表后另追加 window.IPA_DISPLAY_META（溯源元数据），截取到该赋值之前即可。"""
    txt = open(os.path.join(HERE, "..", "js", "ipa-display.js"), encoding="utf-8").read()
    i = txt.index("window.IPA_DISPLAY = ")
    body = txt[i + len("window.IPA_DISPLAY = "):]
    j = body.find("window.IPA_DISPLAY_META")
    if j != -1:
        body = body[:j]
    return json.loads(body.rstrip().rstrip(";"))

def prompt_for(unit, prof_text, aura_text):
    return f"{STYLE_BASE} Subject: {prof_text}. {aura_text}{WHITE_BG}"

def build_manifest():
    ph = load_phonemes()
    disp = load_ipa_display()
    missing = [p["unit"] for p in ph if p["unit"] not in disp]
    if missing:
        raise KeyError(f"ipa-display.js 缺少 unit: {missing}")
    manifest = {}
    for p in ph:
        u = p["unit"]
        rar = p.get("rarity", "SR")
        manifest[u] = {
            # sym 保持英式原样，作跨站稳定键；显示值只增不改
            "sym": p["sym"],
            "displayIpa": disp[u]["displayIpa"], "alias": disp[u]["alias"],
            "name": p["name"], "rarity": rar,
            "type": p.get("typeName", ""), "audio": p.get("audio", ""),
            "words": [w["w"] for w in p.get("words", [])],
            "prompt": prompt_for(u, PROFILES[u], RARITY_AURA[rar]),
        }
    return manifest

def make_prompts():
    os.makedirs(os.path.join(HERE, "prompts"), exist_ok=True)
    mf = build_manifest()
    for u, m in mf.items():
        open(os.path.join(HERE, "prompts", f"{u}.txt"), "w", encoding="utf-8").write(m["prompt"])
    open(os.path.join(HERE, "manifest.json"), "w", encoding="utf-8").write(
        json.dumps(mf, ensure_ascii=False, indent=2))
    print(f"manifest.json + {len(mf)} prompt txt files written to {HERE}/prompts/")
    # 稀有度分布
    dist = {}
    for m in mf.values():
        dist[m["rarity"]] = dist.get(m["rarity"], 0) + 1
    print("rarity distribution:", dict(sorted(dist.items())))

if __name__ == "__main__":
    make_prompts()
