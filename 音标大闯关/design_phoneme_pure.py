# -*- coding: utf-8 -*-
"""48 音标「纯音读法」生成规划（走 edge-tts 音频生产管线）。

设计原则：点每个音标 → 只播"该音标本身的读音"（元音拉长 / 辅音爆破或摩擦的
最简音节），而不播代表词。提示词用最贴近该音标的英文书写形式，配合语速微调，
让 edge-tts 尽量发出"单音素"。

输出：sprite_gen/phoneme_pure.json（unit/sym/name/prompt/rate/note）
生成器：build_phoneme_pure.py -> assets/audio/ph/uXX.ogg(opus)（覆盖单词版）
"""
import json, os

# 48 音标：unit, sym, name -> (prompt, rate%, note)
# rate: edge-tts 语速字符串（"-15%" 更慢、更利于元音拖长 / 摩擦音持续）
P = {
    # ---- 20 元音 ----
    "U01": ("ee",     "ee",         -5),   # iː  长元音
    "U02": ("ih",     "ih",         0),    # ɪ
    "U03": ("eh",     "eh",         0),    # e
    "U04": ("a",      "a",          -5),   # æ  大口
    "U05": ("aaah",   "aaah",      -20),   # ɑː  长 a
    "U06": ("uh",     "uh",         0),    # ʌ
    "U07": ("o",      "o",          -5),   # ɒ  短 o
    "U08": ("or",     "or",        -10),   # ɔː  长 o
    "U09": ("oo",     "oo",         0),    # ʊ   短 u
    "U10": ("oooh",   "oooh",      -20),   # uː  长 u
    "U11": ("err",    "air",       -10),   # ɜː  卷舌
    "U12": ("er",     "uh",         0),    # ə   央元音
    "U13": ("ay",     "ay",         0),    # eɪ
    "U14": ("eye",    "eye",        0),    # aɪ
    "U15": ("oy",     "oy",         0),    # ɔɪ
    "U16": ("oh",     "oh",         0),    # əʊ
    "U17": ("ow",     "ow",         0),    # aʊ
    "U18": ("ear",    "ear",        0),    # ɪə
    "U19": ("air",    "air",        0),    # eə
    "U20": ("oor",    "oor",        0),    # ʊə
    # ---- 28 辅音 ----
    "U21": ("puh",    "pff",        0),   # p
    "U22": ("buh",    "b",          0),   # b
    "U23": ("tu",     "tss",        0),   # t
    "U24": ("du",     "duh",        0),   # d
    "U25": ("kuh",    "k",          0),   # k
    "U26": ("guh",    "g",          0),   # g
    "U27": ("fff",    "fff",       -10),   # f  持续摩擦
    "U28": ("vvv",    "vvv",       -10),   # v
    "U29": ("thuh",   "thf",        0),   # θ  清
    "U30": ("this",   "this",       0),   # ð  浊
    "U31": ("sss",    "sss",       -10),   # s
    "U32": ("zzz",    "zzz",       -10),   # z
    "U33": ("shh",    "shh",       -10),   # ʃ
    "U34": ("zzh",    "buzz",       0),   # ʒ
    "U35": ("huh",    "h",          0),   # h
    "U36": ("rrr",    "rrr",       -10),   # r
    "U37": ("chuh",   "ch",         0),   # tʃ
    "U38": ("juh",    "j",          0),   # dʒ
    "U39": ("mmm",    "mmm",       -10),   # m  鼻音
    "U40": ("nnn",    "nnn",       -10),   # n
    "U41": ("nguh",   "ng",         0),   # ŋ
    "U42": ("lll",    "ll",        -10),   # l  舌侧
    "U43": ("wuh",    "oooh",       0),   # w
    "U44": ("yuh",    "yay",        0),   # j
    "U45": ("truh",   "tr",         0),   # tr
    "U46": ("druh",   "dr",         0),   # dr
    "U47": ("ts",     "ts",         0),   # ts
    "U48": ("dz",     "dz",         0),   # dz
}

VOICE = "en-US-AriaNeural"          # 美音女声，元音/摩擦最清晰（与播客 Bobo/XQ 区分，用于"纯音素"）


def build():
    # 复用 48 音标的 unit/sym/name（单一数据源）
    words = json.load(open(os.path.join(os.path.dirname(__file__),
                                        "sprite_gen", "phoneme_words.json"), encoding="utf-8"))
    rows = []
    for w in words:
        u = w["unit"]
        if u not in P:
            continue
        tts_prompt, note, rate = P[u]
        rows.append({
            "unit": u, "sym": w["sym"], "name": w["name"],
            "prompt": tts_prompt, "rate": "%+d%%" % rate,
            "voice": VOICE, "note": note,
        })
    out = os.path.join(os.path.dirname(__file__), "sprite_gen", "phoneme_pure.json")
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("已写入", out, "，共", len(rows), "条")
    # 打印校验
    for r in rows:
        print(f"  {r['unit']} {r['sym']:<5} -> TTS:{r['prompt']!r:<10} rate:{r['rate']:>6}")


if __name__ == "__main__":
    build()
