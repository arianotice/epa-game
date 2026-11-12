# -*- coding: utf-8 -*-
"""把 _phrepo/phonetic_words.json 的项目代表词族注入 js/data.js。

为每个音标追加两个字段：
  projMain : 主录音词（= build_phoneme_from_repo.py 的 M 映射，ph/uXX.opus 里实际播的那个词）
  projWords: 该音标在项目里的同音词族列表 [{w, zh}]（不含 projMain 本身）

前端用这两个字段渲染"项目代表词卡"。
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)  # 工作区根
PHJSON = os.path.join(ROOT, "_phrepo", "phonetic_words.json")
DATAJS = os.path.join(HERE, "js", "data.js")

# U -> 主录音词（与 build_phoneme_from_repo.py 的 M 一致）
M = {
    1: "bee", 2: "little", 3: "bed", 4: "ant", 5: "mark", 6: "cup", 7: "dog",
    8: "caught", 9: "book", 10: "cool", 11: "bird", 12: "center",
    13: "wait", 14: "my", 15: "point", 16: "pose", 17: "mouse", 18: "beer",
    19: "bear", 20: "poor",
    21: "sip", 22: "bread", 23: "tomorrow", 24: "dog", 25: "cat", 26: "egg",
    27: "fish", 28: "very", 29: "path", 30: "they", 31: "nice", 32: "seize",
    33: "ship", 34: "decision", 35: "hut", 36: "read", 37: "chick", 38: "jam",
    39: "smart", 40: "no", 41: "spring", 42: "line", 43: "work", 44: "yell",
    45: "track", 46: "dress", 47: "eats", 48: "beds",
}

# U -> 项目 phonetic_words.json 里的 key 编号
# （通过"主词属于哪组"人工确认）
U_TO_KEY = {
    1:1, 2:6, 3:7, 4:8, 5:3, 6:10, 7:11, 8:4, 9:12, 10:5,
    11:2, 12:9, 13:13, 14:14, 15:15, 16:17, 17:16, 18:18, 19:19, 20:20,
    21:21, 22:32, 23:22, 24:33, 25:23, 26:34, 27:24, 28:35, 29:27, 30:38,
    31:25, 32:36, 33:26, 34:37, 35:28, 36:39, 37:29, 38:40,
    39:43, 40:44, 41:45, 42:46, 43:47, 44:48, 45:31, 46:42, 47:30, 48:41,
}

# 项目词 → 中文释义（用于 projWords 渲染）
ZH = {
    "bee":"蜜蜂", "we":"我们", "read":"阅读",
    "little":"小的", "sit":"坐", "fish":"鱼",
    "bed":"床", "red":"红色", "egg":"鸡蛋",
    "ant":"蚂蚁", "lamb":"小羊",
    "mark":"标记", "shark":"鲨鱼", "father":"爸爸",
    "cup":"杯子", "bus":"公共汽车", "sun":"太阳",
    "dog":"狗", "box":"盒子", "stop":"停止",
    "caught":"抓到", "walk":"走路", "board":"木板",
    "book":"书", "good":"好的", "full":"满的",
    "cool":"酷的", "rude":"粗鲁的", "tooth":"牙齿",
    "bird":"鸟", "word":"单词", "work":"工作",
    "center":"中心", "panda":"熊猫", "actor":"演员",
    "wait":"等待", "late":"迟的", "hate":"讨厌",
    "my":"我的", "why":"为什么", "write":"写",
    "point":"点", "oil":"油",
    "mouse":"老鼠", "town":"城镇", "cloud":"云",
    "pose":"姿势", "mode":"模式", "know":"知道",
    "beer":"啤酒", "mere":"小的湖", "deer":"鹿",
    "bear":"熊", "wear":"穿", "fare":"车费",
    "poor":"贫穷的", "tour":"旅行", "pure":"纯净的",
    "sip":"啜饮", "put":"放",
    "bread":"面包", "club":"俱乐部", "lab":"实验室",
    "tomorrow":"明天", "today":"今天", "top":"顶部",
    "card":"卡片",
    "cat":"猫",
    "dig":"挖", "gate":"大门",
    "free":"自由", "floor":"地板",
    "very":"非常", "dove":"鸽子", "ever":"曾经",
    "path":"小路", "think":"想", "math":"数学",
    "they":"他们", "those":"那些", "other":"其他",
    "nice":"好的",
    "zero":"零", "size":"尺寸",
    "ship":"小船", "shirt":"衬衫",
    "decision":"决定", "television":"电视", "leisure":"空闲",
    "hut":"小屋", "hello":"你好", "home":"家",
    "grass":"草",
    "chick":"小鸡", "coach":"教练", "rich":"富有的",
    "jam":"果酱", "bridge":"桥", "July":"七月",
    "smart":"聪明的", "move":"移动", "mud":"泥",
    "no":"不", "hunt":"打猎", "find":"找到",
    "spring":"春天", "sing":"唱歌", "ink":"墨水",
    "line":"线", "pool":"池塘", "alive":"活着的",
    "wood":"木头", "what":"什么",
    "yell":"喊叫", "yak":"牦牛", "youth":"青春",
    "track":"轨道", "tree":"大树", "trill":"颤音",
    "dress":"连衣裙", "drink":"喝", "dream":"梦",
    "eats":"吃（三单）", "cats":"猫（复数）", "gifts":"礼物（复数）",
    "beds":"床（复数）", "adds":"加（三单）", "friends":"朋友（复数）",
}

def word_zh(w):
    return ZH.get(w, "")


def main():
    # 读项目词表
    raw = json.load(open(PHJSON, encoding="utf-8"))
    # key -> [semantic_name, word1, word2, ...]（标签与词混排；arr[1:] 并剔除含下划线的语义标签）
    proj_words = {}
    for k, arr in raw.items():
        words = [w for w in arr[1:] if w and "_" not in w and w not in ("mass",)]
        proj_words[int(k)] = words

    # 读 data.js
    txt = open(DATAJS, encoding="utf-8").read()
    marker = "window.IPA_DATA = "
    idx = txt.find(marker)
    assert idx != -1, "data.js 里找不到 window.IPA_DATA = "
    json_body = txt[idx + len(marker):].rstrip().rstrip(";")
    data = json.loads(json_body)

    patched = 0
    for p in data["phonemes"]:
        unit = p.get("unit", "")
        u_num = int(unit[1:]) if unit.startswith("U") else 0
        if u_num not in M:
            continue
        main_w = M[u_num]
        k = U_TO_KEY[u_num]
        others = [w for w in proj_words.get(k, []) if w.lower() != main_w.lower()]
        p["projMain"] = main_w
        p["projWords"] = [{"w": w, "zh": word_zh(w)} for w in others]
        patched += 1

    # 同步 levels 里的内嵌 phonemes（关卡页用到的那份）
    lv_patched = 0
    for lv in data["levels"]:
        for p in lv.get("phonemes", []):
            unit = p.get("unit", "")
            u_num = int(unit[1:]) if unit.startswith("U") else 0
            if u_num in M:
                main_w = M[u_num]
                k = U_TO_KEY[u_num]
                others = [w for w in proj_words.get(k, []) if w.lower() != main_w.lower()]
                p["projMain"] = main_w
                p["projWords"] = [{"w": w, "zh": word_zh(w)} for w in others]
                lv_patched += 1

    # 写回
    with open(DATAJS, "w", encoding="utf-8") as f:
        f.write("// 由 build_data.py + build_proj_inject.py 自动生成\n")
        f.write("window.IPA_DATA = ")
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write(";\n")

    print(f"顶层 phonemes 注入 {patched}/48; levels 内嵌注入 {lv_patched}")
    print(f"sample: U01 projMain={data['phonemes'][0].get('projMain')}, projWords={data['phonemes'][0].get('projWords')}")


if __name__ == "__main__":
    main()
