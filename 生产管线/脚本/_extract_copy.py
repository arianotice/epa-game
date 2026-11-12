# -*- coding: utf-8 -*-
"""Extract teaching copy (words, mnemonics,精灵名) from EP02-EP25 scripts for image copy deck."""
import json, os, re

base = r"C:/Users/86135/WorkBuddy/英语音标播客/生产管线/脚本"
out = {}
for ep in [f"EP{n:02d}" for n in range(2, 26)]:
    p = os.path.join(base, f"{ep}.json")
    with open(p, encoding="utf-8") as f:
        data = json.load(f)
    segs = data["segments"]
    title = data["title"]
    # find word groups: zh segment mentioning 第X组, then following en segment(s)
    groups = []
    for i, s in enumerate(segs):
        if s["lang"] == "zh" and re.search(r"第[一二三]组", s["text"]):
            words = []
            for j in range(i + 1, min(i + 5, len(segs))):
                if segs[j]["lang"] == "en":
                    words.append(segs[j]["text"])
                elif segs[j]["lang"] == "zh" and words:
                    break
            groups.append(words)
    # find mnemonic: zh segment right after the one containing 口诀记忆屋
    mnemonic = ""
    for i, s in enumerate(segs):
        if "口诀" in s["text"] and "记忆屋" in s["text"]:
            # next zh long segment is the mnemonic
            for j in range(i + 1, min(i + 4, len(segs))):
                if segs[j]["lang"] == "zh" and len(segs[j]["text"]) > 15 and "拍手" not in segs[j]["text"]:
                    mnemonic = segs[j]["text"]
                    break
            break
    # find精灵名 mentions (小姐/精灵/国王 etc in bobo zh segments)
    sprites = set()
    for s in segs:
        if s["lang"] == "zh":
            for m in re.findall(r"[一-龥]{1,4}(?:小姐|精灵|国王|队长)", s["text"]):
                sprites.add(m)
    # find IPA-ish references: 符号不出现在text；找「衣」「咦」等 sound nicknames near quotes
    nicknames = set()
    for s in segs:
        if s["lang"] == "zh":
            for m in re.findall(r"—\s*([一-龥]{1,3})\s*[。！？,，]", s["text"]):
                nicknames.add(m)
    out[ep] = {"title": title, "groups": groups, "mnemonic": mnemonic,
               "sprites": sorted(sprites), "nicknames": sorted(nicknames)}

with open(os.path.join(base, "_image_copy_source.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

for ep, d in out.items():
    print(f"== {ep} {d['title']}")
    for g in d["groups"]:
        print("   words:", g)
    print("   口诀:", d["mnemonic"][:120])
    print("   精灵:", d["sprites"], "昵称:", d["nicknames"])
