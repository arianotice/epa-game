# -*- coding: utf-8 -*-
"""augment_data.py — 给音标大闯关数据注入「稀有度」并扩充每关题库。

- 给每个 phoneme（全局 + 关卡内）加 rarity 字段：SR / SAR / SSR / HR / UR / P
- 每关 quiz 扩充：保留原有题，按该关 phonemes/words 生成对应题（听辨 + 选择，三选项 + 解析）
- 写回 js/data.js，保留头部注释与 `window.IPA_DATA =` 前缀
"""
import re, json, random

SRC = "js/data.js"

# ---- 稀有度分级（基于中国小学生常见易混/难度，越靠后越稀有）----
RARITY = {
    # 最基础、最熟悉：P（普通）
    "iː": "P", "ɪ": "P", "e": "P", "æ": "P", "ə": "P",
    # SR：常见元音/爆破/鼻音
    "ɑː": "SR", "ʌ": "SR", "ɒ": "SR", "ʊ": "SR", "uː": "SR",
    "p": "SR", "b": "SR", "t": "SR", "d": "SR", "k": "SR", "g": "SR",
    "f": "SR", "v": "SR", "m": "SR", "n": "SR", "w": "SR", "s": "SR",
    # SAR：双元音 / 半元音 / 清擦音
    "eɪ": "SAR", "aɪ": "SAR", "ɔɪ": "SAR", "əʊ": "SAR", "h": "SAR",
    "j": "SAR", "z": "SAR", "r": "SAR", "l": "SAR", "ɜː": "SAR",
    # HR：部分双元音 / 破擦
    "ɪə": "HR", "eə": "HR", "ʊə": "HR", "aʊ": "HR",
    "tr": "HR", "dr": "HR", "ts": "HR", "dz": "HR",
    # SSR：较难辅音（摩擦/破擦/卷舌）
    "ʃ": "SSR", "ʒ": "SSR", "tʃ": "SSR", "dʒ": "SSR",
    # UR：中国学生最难（咬舌/鼻音后接/浊擦）
    "θ": "UR", "ð": "UR", "ŋ": "UR", "ɔː": "UR",
}

# 这些关已有完善题库，不额外生成（避免与进阶概念冲突）
SKIP_GENERATE = {"EP00", "EP26", "EP27", "EP28"}


def first_clause(s):
    s = re.sub(r"^四句话记牢[:：]?", "", s or "")
    for sep in ["；", ";", "。", "，", ","]:
        if sep in s:
            s = s.split(sep)[0]
            break
    return s.strip()[:18]


def expand_quiz(lv):
    phons = lv.get("phonemes", [])
    if not phons or lv["ep"] in SKIP_GENERATE:
        return lv["quiz"]
    all_words = [w["w"] for w in lv.get("words", [])]
    new = []
    for p in phons:
        pwords = [w["w"] for w in p.get("words", [])]
        others = [w for w in all_words if w not in pwords]
        sym, name = p["sym"], p["name"]
        # 1) 哪个词里藏着 /sym/
        if pwords and len(others) >= 2:
            correct = pwords[0]
            dc = random.sample(others, 2)
            new.append({
                "type": "choice",
                "q": "下面哪个词里藏着 %s /%s/ ？" % (name, sym),
                "options": [correct] + dc,
                "answer": 0,
                "explain": "「%s」里就住着 %s /%s/ ！" % (correct, name, sym),
            })
        # 2) 发 /sym/ 时嘴巴/舌头怎么做
        action = first_clause(p.get("key_point", ""))
        oth_actions = [first_clause(o.get("key_point", ""))
                       for o in phons if o["sym"] != sym and first_clause(o.get("key_point", ""))]
        if action and oth_actions:
            dc = random.sample(oth_actions, min(2, len(oth_actions)))
            new.append({
                "type": "choice",
                "q": "发 /%s/ 的时候，嘴唇和舌头要怎么做？" % sym,
                "options": [action] + dc,
                "answer": 0,
                "explain": (p.get("mnemonic", "") or "")[:40],
            })
        # 3) 听辨：播放该关单词，选出听到的词（运行时配 distractors 凑 3 项）
        if len(all_words) >= 3 and pwords:
            spoke = random.choice(pwords)
            dc = [w for w in all_words if w != spoke]
            dc = random.sample(dc, 2) if len(dc) >= 2 else dc
            new.append({
                "type": "listen",
                "pair": [spoke],
                "distractors": dc,
                "q": "仔细听，你听到的是哪个词？",
            })
    # 合并：原有 + 生成，洗牌后保留（运行时再随机抽 5）
    merged = list(lv["quiz"]) + new
    random.shuffle(merged)
    return merged


def main():
    src = open(SRC, encoding="utf-8").read()
    m = re.search(r"window\.IPA_DATA\s*=\s*(\{.*\})\s*;", src, re.S)
    if not m:
        raise SystemExit("找不到 window.IPA_DATA")
    data = json.loads(m.group(1))

    # 注入稀有度
    for p in data["phonemes"]:
        if "rarity" not in p:
            p["rarity"] = RARITY.get(p["sym"], "SR")
    for lv in data["levels"]:
        for p in lv.get("phonemes", []):
            if "rarity" not in p:
                p["rarity"] = RARITY.get(p["sym"], "SR")

    # 扩充题库
    for lv in data["levels"]:
        lv["quiz"] = expand_quiz(lv)

    out_json = json.dumps(data, ensure_ascii=False, indent=1)
    header = ("// 由 build_data.py 自动生成：30 关 + 48 音标 + 闯关题（augment_data.py 已注入稀有度并扩充题库）\n"
              "window.IPA_DATA = ")
    open(SRC, "w", encoding="utf-8").write(header + out_json + ";\n")

    # 校验
    with open(SRC, encoding="utf-8") as f:
        re.search(r"window\.IPA_DATA\s*=\s*(\{.*\})\s*;", f.read(), re.S).group(1)
    print("OK: 写入完成")
    print("稀有度分布：", {r: sum(1 for p in data["phonemes"] if p["rarity"] == r)
                          for r in ["P", "SR", "SAR", "HR", "SSR", "UR"]})
    for lv in data["levels"][:3] + data["levels"][-1:]:
        print(lv["ep"], "题库题数 =", len(lv["quiz"]))


if __name__ == "__main__":
    random.seed(20261103)
    main()
