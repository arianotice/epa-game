# -*- coding: utf-8 -*-
"""提取 v2：修正标记词匹配，补充序章/进阶关手工数据。"""
import json, re, os

SRC = r"C:/Users/86135/WorkBuddy/英语音标播客/生产管线/脚本"
OUT = r"C:/Users/86135/WorkBuddy/英语音标播客/音标大闯关/content_raw.json"

PHONEMES = [
    ("iː", "微笑小姐", "vowel-long", "EP02", "U01"), ("ɪ", "放松精灵", "vowel-short", "EP02", "U02"),
    ("e", "小口精灵", "vowel-short", "EP03", "U03"), ("æ", "大口精灵", "vowel-short", "EP03", "U04"),
    ("ɑː", "医生精灵", "vowel-long", "EP04", "U05"), ("ʌ", "戳肚子精灵", "vowel-short", "EP04", "U06"),
    ("ɒ", "吹泡泡精灵", "vowel-short", "EP05", "U07"), ("ɔː", "吸果冻精灵", "vowel-long", "EP05", "U08"),
    ("ʊ", "轻轻推精灵", "vowel-short", "EP06", "U09"), ("uː", "吹蜡烛精灵", "vowel-long", "EP06", "U10"),
    ("ɜː", "卷舌弹簧精灵", "vowel-long", "EP07", "U11"), ("ə", "偷懒叹气精灵", "vowel-short", "EP07", "U12"),
    ("eɪ", "滑梯精灵A", "diphthong", "EP08", "U13"), ("aɪ", "滑梯精灵I", "diphthong", "EP08", "U14"),
    ("ɔɪ", "欢呼精灵", "diphthong", "EP09", "U15"), ("əʊ", "含糖精灵", "diphthong", "EP09", "U16"),
    ("aʊ", "惊叹精灵", "diphthong", "EP10", "U17"), ("ɪə", "悄悄话精灵", "diphthong", "EP10", "U18"),
    ("eə", "风吹精灵", "diphthong", "EP11", "U19"), ("ʊə", "旅行精灵", "diphthong", "EP11", "U20"),
    ("p", "纸飞机精灵", "cons-clear", "EP12", "U21"), ("b", "打鼓精灵", "cons-voiced", "EP12", "U22"),
    ("t", "小锤精灵", "cons-clear", "EP13", "U23"), ("d", "响锤精灵", "cons-voiced", "EP13", "U24"),
    ("k", "咳嗽精灵", "cons-clear", "EP14", "U25"), ("g", "打嗝精灵", "cons-voiced", "EP14", "U26"),
    ("f", "咬唇清风精灵", "cons-clear", "EP15", "U27"), ("v", "咬唇振动精灵", "cons-voiced", "EP15", "U28"),
    ("θ", "咬舌清音精灵", "cons-clear", "EP16", "U29"), ("ð", "咬舌浊音精灵", "cons-voiced", "EP16", "U30"),
    ("s", "小蛇精灵", "cons-clear", "EP17", "U31"), ("z", "蜜蜂精灵", "cons-voiced", "EP17", "U32"),
    ("ʃ", "图书馆精灵", "cons-clear", "EP18", "U33"), ("ʒ", "呼噜精灵", "cons-voiced", "EP18", "U34"),
    ("h", "哈气精灵", "cons-clear", "EP19", "U35"), ("r", "小钩子精灵", "cons-voiced", "EP19", "U36"),
    ("tʃ", "火车精灵", "cons-clear", "EP20", "U37"), ("dʒ", "果酱精灵", "cons-voiced", "EP20", "U38"),
    ("m", "哼歌精灵", "nasal", "EP21", "U39"), ("n", "啄米精灵", "nasal", "EP21", "U40"),
    ("ŋ", "打鼾国王精灵", "nasal", "EP22", "U41"),
    ("l", "快乐钩子精灵", "lateral", "EP23", "U42"),
    ("w", "吻唇精灵", "semivowel", "EP24", "U43"), ("j", "短耶精灵", "semivowel", "EP24", "U44"),
    ("tr", "戳精灵", "cons-clear", "EP25", "U45"), ("dr", "啄精灵", "cons-voiced", "EP25", "U46"),
    ("ts", "呲精灵", "cons-clear", "EP25", "U47"), ("dz", "兹精灵", "cons-voiced", "EP25", "U48"),
]

EP_META = {
    "EP00": ("camp", "出发营地", [], "国际音标就是英语的拼音：48 个音标是 48 块乐高积木，所有英语单词都由它们拼成。学会音标，陌生单词也敢开口读，背单词快一倍。"),
    "EP01": ("camp", "出发营地", [], "嘴巴里有支乐队：嘴唇是大门、牙齿是栏杆、舌头是舞者、声带是小鼓、气流是风。元音是乐音，辅音是打击乐。"),
    "EP02": ("vowel", "阳光农场", ["iː", "ɪ"], "微笑音 vs 放松音：嘴角拉到耳边拖长「衣——」是 sheep；嘴巴微张短促「咦」是 ship。"),
    "EP03": ("vowel", "营养早餐", ["e", "æ"], "两档嘴型：/e/ 像咬一口苹果，短促「诶」；/æ/ 像打哈欠，下巴掉下来「哎」。手指横放嘴里量嘴型。"),
    "EP04": ("vowel", "上学路上", ["ɑː", "ʌ"], "医生音 vs 戳肚子音：/ɑː/ 像医生检查喉咙「啊——」又长又开；/ʌ/ 像被轻轻戳一下肚子「啊」，短又松。"),
    "EP05": ("vowel", "运动会", ["ɒ", "ɔː"], "吹泡泡 vs 吸果冻：都撮唇「哦」，短「哦」是 hop 跳，拖长「哦——」是 ball。"),
    "EP06": ("vowel", "睡前故事", ["ʊ", "uː"], "推东西 vs 吹蜡烛：都撮唇「乌」，/ʊ/ 像轻轻推东西「唔」短而松；/uː/ 像吹蜡烛「呜——」长而紧。"),
    "EP07": ("vowel", "动物园与回家路", ["ɜː", "ə"], "卷舌弹簧 vs 偷懒叹气：/ɜː/ 舌头卷成小弹簧停在口腔中部「呃——」；/ə/ 嘴巴懒洋洋叹口气「呃」，最短最放松。"),
    "EP08": ("vowel", "生日派对", ["eɪ", "aɪ"], "滑滑梯音：双元音要从一个音滑到另一个音。从「诶」滑到「衣」是字母 A；看到风筝吓一跳「啊—衣」是字母 I。"),
    "EP09": ("vowel", "玩具箱与感冒", ["ɔɪ", "əʊ"], "欢呼音 vs 含糖音：看到玩具「哦—衣」欢呼；「欧」像含着一颗糖，是字母 O 的名字音。"),
    "EP10": ("vowel", "我的家", ["aʊ", "ɪə"], "惊叹 vs 悄悄话：看到大房子「啊—呜」惊叹；「一—呃」是指着耳朵说悄悄话。"),
    "EP11": ("vowel", "理发店与旅行", ["eə", "ʊə"], "最文静的两个音：头发被风吹「诶—呃」；收拾行李「乌—呃」。单词最少，认识就行。"),
    "EP12": ("cons", "纸飞机大赛", ["p", "b"], "双唇紧闭「噗」地爆破：/p/ 是纸飞机不振动；/b/ 是打鼓要振动（手贴喉咙感受）。"),
    "EP13": ("cons", "动物园：老虎与小狗", ["t", "d"], "舌尖当小锤子敲上齿龈：「特」不振动、「德」振动。"),
    "EP14": ("cons", "公园放风筝", ["k", "g"], "舌根轻轻顶天花板：/k/ 像咳嗽「咔」，/g/ 像打嗝「咕」。"),
    "EP15": ("cons", "花店与早餐", ["f", "v"], "上牙轻咬下唇吹气「夫」；/v/ 是「夫」的振动版。记住：牙齿必须碰嘴唇才是 v，否则就变成了 w。"),
    "EP16": ("cons", "生日蜡烛与家人", ["θ", "ð"], "咬舌双胞胎：舌尖轻轻探出齿缝，送气「斯」是 /θ/，振动「兹」是 /ð/。舌尖别伸太长，碰到就缩回。"),
    "EP17": ("cons", "动物园与蜂场", ["s", "z"], "小蛇「嘶嘶」不振动，蜜蜂「滋滋」要振动：同一张嘴型，声带开关决定清浊。"),
    "EP18": ("cons", "海边与客厅电视", ["ʃ", "ʒ"], "图书馆「嘘——」嘴唇撮圆是 /ʃ/；/ʒ/ 是「嘘」的打呼噜版，汉语里没有，靠手贴喉咙认振动。"),
    "EP19": ("cons", "冬天暖手与农场", ["h", "r"], "「哈」是气流自由冲出、声带不振动；/r/ 是舌尖钩起悬空「rrr」，千万别卷成汉语的「日/热」。"),
    "EP20": ("cons", "教室与早餐桌", ["tʃ", "dʒ"], "火车「哧—吃」：先爆破后摩擦，嘴巴先抵后圆；/dʒ/ 是声带边振动边滑动，像吃果酱「饥吃」。"),
    "EP21": ("cons", "睡前与餐桌", ["m", "n"], "闭眼哼歌「嗯」是 /m/，小鸡啄米点头「嗯」是 /n/。捏住鼻子两个音都发不出来——鼻音验证法。"),
    "EP22": ("cons", "王国与音乐课", ["ŋ"], "舌根堵住喉咙打鼾「嗯」：/n/ 是舌尖干活，/ŋ/ 是舌根干活。sing 读「腥」不读「星」。"),
    "EP23": ("cons", "开灯与水果店", ["l"], "快乐「lll」：舌尖像小钩子钩住上齿龈。词首清晰「了」，词尾模糊「欧」——apple 读「艾泡」不读「艾普」。"),
    "EP24": ("cons", "喝水与画画", ["w", "j"], "/w/ 是吻一下嘴唇再滑开；/j/ 像「耶」但更短，马上接到元音。we 读「呜—衣」快速滑动，不是「威」。"),
    "EP25": ("cons", "火车站与操场", ["tr", "dr", "ts", "dz"], "火车头兄弟：tr「戳」、dr「啄」；尾巴音兄弟：ts「呲」、dz「兹」。名词复数尾巴常是 ts/dz。"),
    "EP26": ("peak", "音节切蛋糕", [], "长单词切蛋糕：ba-na-na 拍手数音节；每一块里必须有一颗元音；开音节开门长、闭音节关门短。"),
    "EP27": ("peak", "重音的秘密", [], "PRESent 礼物 vs preSENT 赠送：双音节词重音位置不同，意思完全不同；实词重读、虚词轻读。"),
    "EP28": ("peak", "连读与失去爆破", [], "not at all 读成 no-ta-tall；good boy 的尾音憋住不炸。说得像 native 的两个秘诀。"),
    "EP29": ("peak", "毕业大作战", [], "六对易混音标终极对决：/iː/-/ɪ/、/æ/-/e/、/θ/-/s/、/v/-/w/、/n/-/ŋ/、/l/-/r/。全图点亮 + 毕业朗读挑战。"),
}

# 序章/进阶关手工数据
HAND = {
    "EP00": {"words": [("cat", "猫"), ("banana", "香蕉"), ("dog", "狗")],
             "mnemonic": "国际音标是英语的拼音，48 个音标就是 48 块乐高积木——任何一个英语单词，都能用它们拼出来！"},
    "EP01": {"words": [("lips", "嘴唇"), ("teeth", "牙齿"), ("tongue", "舌头"), ("vocal cords", "声带"), ("air", "气流")],
             "mnemonic": "嘴唇大门牙齿栏，舌头舞者声带鼓，气流带来一阵风——元音唱歌辅音打鼓！"},
    "EP26": {"words": [("happy", "开心的"), ("table", "桌子"), ("banana", "香蕉"), ("elephant", "大象")],
             "mnemonic": "长单词切蛋糕，拍手数块数；每块必有元音草莓，开门长、关门短！"},
    "EP27": {"words": [("PRESent", "礼物"), ("preSENT", "赠送"), ("REcord", "唱片"), ("reCORD", "录制")],
             "mnemonic": "单词里有盏灯，照到哪块哪块明。名词形容词灯在前，动词常常灯在后。句子里实词重，虚词轻轻往前送！"},
    "EP28": {"words": [("Not at all", "一点也不"), ("An apple", "一个苹果"), ("Good boy", "好孩子")],
             "mnemonic": "词尾碰头就连读，爆破音尾憋住不炸——英语从积木变成滑梯！"},
    "EP29": {"words": [("sheep / ship", "绵羊 / 小船"), ("bed / bad", "床 / 坏的"), ("think / sink", "想 / 下沉"),
                       ("very / wary", "非常 / 小心的"), ("sin / sing", "过错 / 唱歌"), ("light / right", "灯 / 右边")],
             "mnemonic": "拖长的是绵羊，一冒就收是小船；塞半根手指是 bed，塞一整根是 bad；敢探出去的是 think，躲起来的是 sink；牙齿碰唇是 very，撮圆前亲是 wary；舌尖关门是 sin，舌根关门是 sing；贴上去的是 light，悬空的是 right。"},
}

CHAL_SPECIAL = {
    "EP26": {"type": "count", "items": [("window", 2), ("elephant", 3), ("computer", 3)]},
    "EP27": {"type": "stress", "items": [("table", 1), ("begin", 2), ("window", 1)]},
    "EP28": {"type": "phrase", "items": [("Not at all", "3 个词：not / at / all"), ("An apple", "2 个词：an / apple，粘得太紧"), ("Good boy", "憋住了：good 的尾音没炸开，是颗哑弹")]},
}

def load(ep):
    p1 = os.path.join(SRC, ep + ".json")
    p2 = os.path.join(SRC, "单元", ep + ".json")
    return json.load(open(p1 if os.path.exists(p1) else p2, encoding="utf-8"))

def words_of(text):
    return [w for w in re.split(r"[.\s]+", text.strip().rstrip(".")) if re.fullmatch(r"[a-zA-Z]+", w)]

RHYME_MARKS = ["口诀记忆屋", "口诀记住", "口诀背熟", "口诀收好", "进口诀"]
TREASURE_MARKS = ["单词宝藏", "例句宝藏", "宝藏时间", "第一件宝藏"]

def find_marker(segs, marks, start=0):
    for i in range(start, len(segs)):
        if any(m in segs[i]["text"] for m in marks):
            return i
    return None

result = {"phonemes": [], "levels": []}

# ---------- 48 音标 ----------
for sym, name, ptype, ep, unit in PHONEMES:
    d = load(unit)
    segs = d["segments"]
    words, seen = [], set()
    i_tr = find_marker(segs, TREASURE_MARKS)
    i_rh = find_marker(segs, RHYME_MARKS, start=(i_tr or 0))
    if i_tr is not None and i_rh is not None and i_rh > i_tr:
        for s in segs[i_tr:i_rh]:
            if s["lang"] == "en":
                for w in words_of(s["text"]):
                    if w.lower() not in seen:
                        seen.add(w.lower()); words.append(w)
    mnemonic = ""
    if i_rh is not None:
        for s in segs[i_rh + 1:]:
            if s["lang"] == "zh" and len(s["text"]) >= 10:
                mnemonic = s["text"]; break
    key_point = ""
    if i_tr:
        KW = ["舌", "唇", "牙", "声带", "气流", "振动", "嘴角", "喉咙", "嘴型", "嘴唇", "爆破", "摩擦", "鼻音"]
        cands = [s["text"] for s in segs[:i_tr] if s["lang"] == "zh" and len(s["text"]) >= 30]
        good = [c for c in cands if sum(k in c for k in KW) >= 3]
        if good:
            key_point = max(good, key=len)
        elif cands:
            key_point = max(cands, key=len)
    result["phonemes"].append({
        "sym": sym, "name": name, "type": ptype, "ep": ep, "unit": unit,
        "words": words, "key_point": key_point, "mnemonic": mnemonic, "title": d["title"],
    })

# ---------- 30 关 ----------
PAIR_RE = re.compile(r"^([a-zA-Z]+)\.\s*(?:\.\.\.\s*)?([a-zA-Z]+)\.$")
for n in range(30):
    ep = f"EP{n:02d}"
    region, scene, phs, tip = EP_META[ep]
    d = load(ep)
    segs = d["segments"]
    pairs = []
    i_chal = next((i for i, s in enumerate(segs) if "听辨大挑战" in s["text"] or (ep == "EP29" and "擂台" in s["text"])), None)
    if i_chal is not None:
        for s in segs[i_chal:]:
            if s["lang"] != "en":
                continue
            m = PAIR_RE.match(s["text"].strip())
            if m:
                p = [m.group(1), m.group(2)]
                if not pairs or pairs[-1] != p:
                    pairs.append(p)
    words, seen = [], set()
    i_tr = find_marker(segs, TREASURE_MARKS)
    i_rh = find_marker(segs, RHYME_MARKS, start=(i_tr or 0))
    if i_tr is not None and i_rh is not None and i_rh > i_tr:
        for s in segs[i_tr:i_rh]:
            if s["lang"] == "en":
                for w in words_of(s["text"]):
                    if w.lower() not in seen:
                        seen.add(w.lower()); words.append(w)
    mnemonic = ""
    if i_rh is not None:
        for s in segs[i_rh + 1:]:
            if s["lang"] == "zh" and len(s["text"]) >= 10:
                mnemonic = s["text"]; break
    lv = {"ep": ep, "title": d["title"], "region": region, "scene": scene,
          "phonemes": phs, "tip": tip, "words": words, "mnemonic": mnemonic, "pairs": pairs}
    if ep in HAND:
        lv["words"] = HAND[ep]["words"]
        lv["mnemonic"] = HAND[ep]["mnemonic"]
    if ep in CHAL_SPECIAL:
        lv["special"] = CHAL_SPECIAL[ep]
    result["levels"].append(lv)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

print("== 关卡 ==")
for lv in result["levels"]:
    w = lv["words"]
    print(f"{lv['ep']} 词{len(w):2d} 对{len(lv['pairs'])} 口诀{'√' if lv['mnemonic'] else '×'} | {[x[0] if isinstance(x,tuple) else x for x in w][:8]}")
print("\n== 音标（只列异常） ==")
for p in result["phonemes"]:
    if len(p["words"]) < 2 or not p["key_point"] or not p["mnemonic"]:
        print(f"{p['sym']:4s} {p['name']:8s} 词{len(p['words'])} 要点{'√' if p['key_point'] else '×'} 口诀{'√' if p['mnemonic'] else '×'} {p['words']}")
print("（无输出=全部达标）")
