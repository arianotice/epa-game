# -*- coding: utf-8 -*-
"""build_data.py v1：合并 content_raw.json + 手工题库 + 地图节点 → js/data.js"""
import json, os

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/音标大闯关"
raw = json.load(open(os.path.join(BASE, "content_raw.json"), encoding="utf-8"))
PH = {p["sym"]: p for p in raw["phonemes"]}
LV = {l["ep"]: l for l in raw["levels"]}

# ---------- 地图节点（依据 A1 大地图实测：%，左上原点） ----------
GEM_X = [23, 30.5, 38, 45.5]          # 元音城堡宝石 4 列
GEM_Y = [24, 34, 44]                  # 取 5 行中的 3 行节点
KING_X = [55, 65, 75, 85, 93]         # 辅音王国房屋 5 列
KING_Y = [44, 54, 64]                 # 前 3 行
NODES = {"EP00": (12, 68), "EP01": (26, 80)}
for i in range(10):
    NODES[f"EP{i+2:02d}"] = (GEM_X[i % 4], GEM_Y[i // 4])
for i in range(14):
    NODES[f"EP{i+12:02d}"] = (KING_X[i % 5], KING_Y[i // 5])
NODES.update({"EP26": (68, 26), "EP27": (71, 20), "EP28": (73.5, 14), "EP29": (75, 8)})

IMG = {"EP00": "cover.webp", "EP01": "f.webp", "EP26": "a1.webp", "EP27": "a1.webp", "EP28": "a1.webp", "EP29": "cover.webp"}
for n in range(2, 26):
    IMG[f"EP{n:02d}"] = f"b{n:02d}.webp"

REGION_NAME = {"camp": "出发营地", "vowel": "元音城堡", "cons": "辅音王国", "peak": "进阶峰"}

# ---------- 题库：choice 类（知识题） ----------
Q = {}  # ep -> [questions]

def ch(q, options, answer, explain):
    return {"type": "choice", "q": q, "options": options, "answer": answer, "explain": explain}

Q["EP00"] = [
    ch("国际音标对英语来说，就像什么对汉字？", ["拼音", "笔画", "偏旁"], 0, "音标就是英语的拼音，看到任何单词都能自己读出来！"),
    ch("声音探险队一共要抓多少个音标精灵？", ["48 个", "24 个", "12 个"], 0, "20 个元音 + 28 个辅音 = 48 个音标精灵！"),
    {"type": "listen", "pair": ["dog", "cat"], "q": "仔细听，波波队长拼出的是哪个词？"},
    ch("学会音标最大的好处是什么？", ["看到陌生单词也敢开口读", "不用写作业了", "睡觉能梦见英语"], 0, "48 个音标是 48 块乐高积木，会拼就会读！"),
    ch("下面哪个不是声音探险队的目的地？", ["元音城堡", "辅音王国", "糖果乐园"], 2, "我们的目的地是：出发营地→元音城堡→辅音王国→进阶峰！"),
]
Q["EP01"] = [
    ch("手贴住喉咙，感觉麻麻发震，说明声带在？", ["振动（浊音）", "休息", "唱歌"], 0, "手贴喉咙测振动，是分清浊音的随身小工具！"),
    ch("元音精灵的声音更像什么？", ["唱歌（乐音）", "打鼓（打击乐）", "吹口哨"], 0, "元音气流畅通、声音又亮又长，像唱歌；辅音像打鼓。"),
    ch("舌头在嘴巴乐队里扮演谁？", ["舞者", "大门", "栏杆"], 0, "嘴唇是大门、牙齿是栏杆、舌头是舞者、声带是小鼓！"),
    ch("辅音精灵喜欢在嘴巴里做什么？", ["设置障碍", "睡大觉", "变颜色"], 0, "辅音有的噗地爆破、有的嘶嘶摩擦，像打击乐。"),
    {"type": "listen", "pair": ["teeth", "tongue"], "q": "仔细听，你听到的是哪个词？"},
]

def pair_qs(ep):
    """前 3 题：用该关脚本里的听辨对"""
    return [{"type": "listen", "pair": p, "q": "仔细听，你听到的是哪个词？"} for p in LV[ep]["pairs"][:3]]

def pick_q(ep, sym, distract_from):
    """哪个词里藏着某音：答案=该音的词，干扰项=另一个音的词"""
    words = LV[ep]["words"]
    ans_words = [w for w in words[:3]]
    dis_words = [w for w in words[3:6]]
    if not dis_words:
        dis_words = [w for w in words[3:]]
    opts = [ans_words[0]] + dis_words[:3]
    return ch(f"哪个词里藏着 {sym} ？", opts, 0, f"{ans_words[0]} 里就住着 {sym} ！")

Q["EP02"] = pair_qs("EP02") + [
    pick_q("EP02", "微笑小姐 /iː/", None),
    ch("发 /iː/ 的时候，嘴角要怎么做？", ["向两边咧开，拉到耳边", "嘴巴微张，全身放松", "嘴唇撮圆往前亲"], 0, "嘴角微笑拉耳边，拖长音——衣——！"),
]
Q["EP03"] = pair_qs("EP03") + [
    pick_q("EP03", "大口精灵 /æ/", None),
    ch("小口精灵 /e/ 的嘴巴，像在做什么？", ["咬一口苹果", "打哈欠下巴掉", "吹蜡烛"], 0, "/e/ 像咬一口苹果短促「诶」；/æ/ 才是打哈欠「哎」。"),
]
Q["EP04"] = pair_qs("EP04") + [
    pick_q("EP04", "医生精灵 /ɑː/", None),
    ch("戳肚子音 /ʌ/ 的感觉像？", ["被轻轻戳一下肚子", "医生检查喉咙", "吹蜡烛"], 0, "/ʌ/ 短又松，像被戳一下肚子「啊」。"),
]
Q["EP05"] = pair_qs("EP05") + [
    pick_q("EP05", "吸果冻精灵 /ɔː/", None),
    ch("吹泡泡音 /ɒ/ 和吸果冻音 /ɔː/ 的嘴巴都要？", ["撮唇（撮成圆形）", "咧开微笑", "咬住舌头"], 0, "都撮唇「哦」，一个短一个长。"),
]
Q["EP06"] = pair_qs("EP06") + [
    pick_q("EP06", "吹蜡烛精灵 /uː/", None),
    ch("吹蜡烛音 /uː/ 像做什么动作？", ["吹蜡烛", "轻轻推东西", "打哈欠"], 0, "撮唇「呜——」又长又紧，像吹蜡烛。"),
]
Q["EP07"] = pair_qs("EP07") + [
    pick_q("EP07", "卷舌弹簧精灵 /ɜː/", None),
    ch("偷懒叹气音 /ə/ 最大的特点是？", ["最短最放松", "又长又亮", "要卷舌头"], 0, "/ə/ 嘴巴懒洋洋叹口气，一闪就没。"),
]
Q["EP08"] = pair_qs("EP08") + [
    pick_q("EP08", "滑梯精灵 I /aɪ/", None),
    ch("双元音的发音要诀是？", ["从一个音滑到另一个音", "又短又促一口气收", "捏住鼻子发音"], 0, "双元音要滑动：从「诶」滑到「衣」，中间不许停！"),
]
Q["EP09"] = pair_qs("EP09") + [
    pick_q("EP09", "含糖精灵 /əʊ/", None),
    ch("含糖音「欧——」是哪个字母的名字音？", ["字母 O", "字母 A", "字母 I"], 0, "/əʊ/ 像含着一颗糖，正是字母 O 的名字音。"),
]
Q["EP10"] = pair_qs("EP10") + [
    pick_q("EP10", "悄悄话精灵 /ɪə/", None),
    ch("惊叹音 /aʊ/ 的感觉像？", ["看到大房子「哇——」", "捂着耳朵说悄悄话", "打哈欠"], 0, "嘴巴先张到最大再收圆：「啊—呜」！"),
]
Q["EP11"] = pair_qs("EP11") + [
    pick_q("EP11", "旅行精灵 /ʊə/", None),
    ch("/eə/ 和 /ʊə/ 被称为什么音？", ["最文静的两个音", "最爱吵闹的两个音", "最长的两个音"], 0, "它们单词最少，认识就行——风吹头发「诶—呃」，收拾行李「乌—呃」。"),
]
Q["EP12"] = pair_qs("EP12") + [
    pick_q("EP12", "打鼓精灵 /b/", None),
    ch("分清浊音最可靠的办法是？", ["手贴喉咙摸振动", "捏住鼻子", "看嘴型大小"], 0, "喉咙麻的是浊音，安安静静的是清音。"),
]
Q["EP13"] = pair_qs("EP13") + [
    pick_q("EP13", "响锤精灵 /d/", None),
    ch("/t/ 和 /d/ 是谁在干活？", ["舌尖当小锤子敲上齿龈", "双唇紧闭", "舌根顶天花板"], 0, "「特」不振动，「德」振动。"),
]
Q["EP14"] = pair_qs("EP14") + [
    pick_q("EP14", "打嗝精灵 /g/", None),
    ch("咳嗽音 /k/ 是哪个部位在顶天花板？", ["舌根", "舌尖", "嘴唇"], 0, "舌根轻轻顶天花板：/k/ 像咳嗽「咔」。"),
]
Q["EP15"] = pair_qs("EP15") + [
    pick_q("EP15", "咬唇振动精灵 /v/", None),
    ch("/v/ 和 /w/ 的关键区别是？", ["牙齿必须碰嘴唇", "嘴唇要撮圆", "舌头要卷起来"], 0, "上牙碰下唇才是 v，只撮圆就变成 w 啦！"),
]
Q["EP16"] = pair_qs("EP16") + [
    pick_q("EP16", "咬舌浊音精灵 /ð/", None),
    ch("咬舌音的要诀是？", ["舌尖轻探齿缝，碰到就缩回", "舌尖躲到牙齿后面", "舌根顶住喉咙"], 0, "舌尖别伸太长，碰到牙齿就往回缩！"),
]
Q["EP17"] = pair_qs("EP17") + [
    pick_q("EP17", "蜜蜂精灵 /z/", None),
    ch("/s/ 和 /z/ 嘴巴一样，差别在？", ["声带振不振动", "舌位高低", "嘴唇圆不圆"], 0, "同一张嘴型，声带开关决定清浊：嘶嘶不振动，滋滋要振动。"),
]
Q["EP18"] = pair_qs("EP18") + [
    pick_q("EP18", "呼噜精灵 /ʒ/", None),
    ch("图书馆「嘘」音 /ʃ/ 的嘴唇要？", ["往前撮圆", "向两边咧开", "上下咬住"], 0, "嘴唇撮圆「嘘——」，/ʒ/ 是它的打呼噜版。"),
]
Q["EP19"] = pair_qs("EP19") + [
    pick_q("EP19", "小钩子精灵 /r/", None),
    ch("/r/ 的舌尖要怎么做？", ["钩起悬空，不碰任何地方", "躲到牙齿后面", "平放嘴里"], 0, "舌尖悬半空「rrr」，千万别卷成汉语的「日」。"),
]
Q["EP20"] = pair_qs("EP20") + [
    pick_q("EP20", "果酱精灵 /dʒ/", None),
    ch("火车音 /tʃ/ 的发音过程是？", ["先爆破，后摩擦", "只摩擦不爆破", "只爆破不摩擦"], 0, "嘴巴先抵后圆：哧—吃，两步合成一个音。"),
]
Q["EP21"] = pair_qs("EP21") + [
    pick_q("EP21", "啄米精灵 /n/", None),
    ch("验证鼻音的好办法是？", ["捏住鼻子发不出", "手贴喉咙", "看舌头尖"], 0, "捏住鼻子，/m/ /n/ /ŋ/ 全都发不出来——鼻音验证法！"),
]
Q["EP22"] = pair_qs("EP22") + [
    ch("sing 正确的读法接近哪个音？", ["腥", "星", "新"], 0, "sing 读「腥」不读「星」，尾巴是舌根打鼾的 ŋ。"),
    ch("打鼾鼻音 /ŋ/ 是哪个部位在干活？", ["舌根", "舌尖", "嘴唇"], 0, "/n/ 舌尖干活，/ŋ/ 舌根干活。"),
]
Q["EP23"] = pair_qs("EP23") + [
    ch("apple 词尾的 l 读起来像？", ["欧", "普", "了"], 0, "词首清晰「了」，词尾模糊「欧」——apple 读「艾泡」。"),
    ch("快乐 /l/ 的舌尖像什么？", ["小钩子钩住上齿龈", "小锤子敲天花板", "小蛇吐信子"], 0, "舌尖像小钩子，气流从舌头两边漏下去。"),
]
Q["EP24"] = pair_qs("EP24") + [
    pick_q("EP24", "短耶精灵 /j/", None),
    ch("吻唇音 /w/ 的动作像？", ["吻一下嘴唇再滑开", "打一声招呼", "咬一口苹果"], 0, "we 读「呜—衣」快速滑动，不是「威」。"),
]
Q["EP25"] = pair_qs("EP25") + [
    ch("名词复数 cats 的尾巴音是？", ["ts（呲）", "dz（兹）", "tr（戳）"], 0, "cats 结尾清音读 ts；beds 结尾振动读 dz。"),
    ch("火车头兄弟 tr 和 dr 的差别在？", ["声带振不振动", "舌头位置", "嘴唇圆不圆"], 0, "戳不动，啄要抖——tr 清、dr 浊。"),
]
Q["EP26"] = [
    {"type": "count", "speak": "window", "q": "拍手数一数：这个单词有几块蛋糕？", "options": ["2 块", "3 块", "4 块"], "answer": 0, "explain": "win-dow，两块蛋糕！"},
    {"type": "count", "speak": "elephant", "q": "拍手数一数：这个单词有几块蛋糕？", "options": ["2 块", "3 块", "4 块"], "answer": 1, "explain": "el-e-phant，三块！你多拍的那一下是手滑了。"},
    {"type": "count", "speak": "computer", "q": "拍手数一数：这个单词有几块蛋糕？", "options": ["2 块", "3 块", "4 块"], "answer": 2, "explain": "com-pu-ter，三块蛋糕。"},
    ch("每一块「蛋糕」里必须有什么？", ["一颗元音", "一个辅音", "一个字母 s"], 0, "每块音节里必须住着一颗元音草莓！"),
    ch("闭音节的元音读起来？", ["短", "长", "不读"], 0, "关门短，开门长——闭音节元音又短又促。"),
]
Q["EP27"] = [
    {"type": "stress", "speak": "table", "q": "仔细听：重音落在第几块？", "options": ["第一块", "第二块"], "answer": 0, "explain": "TA-ble，名词灯在前！"},
    {"type": "stress", "speak": "begin", "q": "仔细听：重音落在第几块？", "options": ["第一块", "第二块"], "answer": 1, "explain": "be-GIN，动词常常灯在后！"},
    {"type": "stress", "speak": "window", "q": "仔细听：重音落在第几块？", "options": ["第一块", "第二块"], "answer": 0, "explain": "WIN-dow，窗户是东西，灯在前。"},
    ch("PRESent（礼物）和 preSENT（赠送）意思不同，因为？", ["重音位置不同", "字母不同", "读得长短不同"], 0, "重音放前面还是后面，意思完全不一样！"),
    ch("句子里通常读得重、读得长的是？", ["名词、动词等实词", "代词、冠词等虚词", "每个词一样重"], 0, "实词干活读得响，虚词打杂轻轻送。"),
]
Q["EP28"] = [
    {"type": "phrase", "speak": "Not at all", "q": "这句话连起来读，其实是几个词？", "options": ["1 个词", "2 个词", "3 个词"], "answer": 2, "explain": "not / at / all 三个词，连起来像 no-ta-tall。"},
    {"type": "phrase", "speak": "An apple", "q": "这句话连起来读，其实是几个词？", "options": ["1 个词", "2 个词", "3 个词"], "answer": 1, "explain": "an + apple 两个词，粘得太紧骗过了耳朵！"},
    {"type": "phrase", "speak": "Good boy", "q": "good 的尾音是炸开了，还是憋住了？", "options": ["炸开了", "憋住了（哑弹）", "多了一个音"], "answer": 1, "explain": "d 碰到 b 就憋住不炸，中间还空半拍！"},
    ch("「失去爆破」指的是？", ["爆破音的尾音憋住不炸", "声音突然变大", "多读一个音"], 0, "该炸的时候憋住，就是失去爆破。"),
    ch("not at all 连读之后，听起来最像？", ["no-ta-tall", "还是 not-at-all 一样", "no-ta-al"], 0, "t 撞上 a 就连读，整句变成滑溜溜的一串。"),
]
Q["EP29"] = [
    {"type": "listen", "pair": ["sheep", "ship"], "q": "第一座擂台：你听到的是哪个词？"},
    {"type": "listen", "pair": ["think", "sink"], "q": "第二座擂台：你听到的是哪个词？"},
    {"type": "listen", "pair": ["light", "right"], "q": "第三座擂台：你听到的是哪个词？"},
    ch("very 和 wary 的区别是？", ["上牙碰唇 vs 撮圆前亲", "一个长一个短", "一个清一个浊"], 0, "very 开头要咬，wary 开头要吻——牙齿不许碰唇！"),
    ch("sin 和 sing 的结尾区别是？", ["舌尖顶住 vs 舌根抬起来", "一个振动一个不振动", "嘴唇圆不圆"], 0, "舌尖在最前面关门，舌根在最后面关门。"),
]

# ---------- 单词中文释义（依据策划案单词实例列） ----------
ZH = {
    "sheep": "绵羊", "tree": "大树", "green": "绿色", "ship": "小船", "fish": "鱼", "big": "大大的",
    "egg": "鸡蛋", "bed": "床", "red": "红色", "pen": "钢笔", "apple": "苹果", "hand": "手",
    "car": "小汽车", "park": "公园", "star": "星星", "bus": "公共汽车", "cup": "杯子", "duck": "鸭子",
    "hot": "热狗", "dog": "狗", "box": "盒子", "ball": "球", "horse": "马", "door": "门",
    "book": "书", "foot": "脚", "good": "好的", "food": "食物", "moon": "月亮", "blue": "蓝色",
    "bird": "鸟", "girl": "女孩", "nurse": "护士", "banana": "香蕉", "panda": "熊猫", "teacher": "老师",
    "cake": "蛋糕", "name": "名字", "rain": "下雨", "bike": "自行车", "kite": "风筝", "five": "五",
    "toy": "玩具", "boy": "男孩", "noise": "吵闹", "nose": "鼻子", "home": "家", "boat": "小船",
    "house": "房子", "mouth": "嘴", "cow": "奶牛", "ear": "耳朵", "near": "近的", "deer": "鹿",
    "hair": "头发", "chair": "椅子", "bear": "熊", "pear": "梨", "tour": "旅行", "sure": "确定",
    "pig": "猪", "paper": "纸", "baby": "婴儿", "tiger": "老虎", "table": "桌子", "cat": "猫",
    "key": "钥匙", "flower": "花", "phone": "电话", "van": "厢式车", "vegetable": "蔬菜",
    "three": "三", "thank": "谢谢", "birthday": "生日", "this": "这个", "mother": "妈妈", "brother": "兄弟",
    "sun": "太阳", "snake": "蛇", "zoo": "动物园", "lazy": "懒的", "television": "电视", "usually": "通常", "treasure": "宝藏",
    "hat": "帽子", "rabbit": "兔子", "happy": "开心", "rice": "米饭", "run": "跑",
    "juice": "果汁", "lunch": "午餐", "jam": "果酱", "jump": "跳", "mom": "妈妈", "milk": "牛奶", "dinner": "晚餐",
    "king": "国王", "song": "歌", "sing": "唱歌", "morning": "早晨", "strong": "强壮的",
    "light": "灯", "lemon": "柠檬", "lion": "狮子", "look": "看", "water": "水", "window": "窗户",
    "yes": "是的", "yellow": "黄色", "year": "年", "yogurt": "酸奶", "dress": "连衣裙", "cats": "猫（复数）",
    "beds": "床（复数）", "train": "火车", "drink": "喝", "students": "学生", "friends": "朋友",
    "lips": "嘴唇", "teeth": "牙齿", "tongue": "舌头", "vocal cords": "声带", "air": "气流",
    "pure": "纯净的", "seat": "座位", "sit": "坐下", "sleep": "睡觉", "slip": "滑倒",
}

def word_zh(w):
    return ZH.get(w.lower().strip(), "")

# 个别音标要点的人工润色（提取结果开头突兀处）
KEY_POINT_FIX = {
    "iː": "嘴角用力往两边咧开，露出大大的微笑；舌头前半截抬高靠近上颚，中间留一条小缝；气流从小缝慢慢挤出去；声音又亮又长——衣——。",
    "v": "上牙轻咬下唇，气流从唇齿之间的缝里吹出来「夫」；声带要振动，嗡嗡响——和 /f/ 同一位置，只差一个声带开关。",
    "j": "嘴型像快速的「耶」，舌面抬高靠近上腭，马上滑接到后面的元音；声带振动，又短又急。",
    "k": "舌根抬起顶住上腭堵住气流，突然放开，像咳嗽「咔」；声带不振动，安安静静。",
    "f": "上牙轻咬下唇，气流从缝里吹出来「夫」；声带不振动，只有风没有鼓声。",
    "w": "嘴唇撮圆往前亲一下再滑开；声带振动——we 读「呜—衣」快速滑动，不是「威」。",
    "tʃ": "舌尖先抵住上齿龈堵住气流（爆破），再滑到硬腭附近摩擦着出去（摩擦），两步合成一个音；声带不振动。",
    "θ": "舌尖轻轻探出齿缝，碰到牙齿就缩回，别伸太长；气流从缝里送出来「斯」；声带不振动。",
    "dr": "和 tr 同一张嘴型：舌尖先抵住上齿龈再滑开；声带要振动，喉咙发麻——啄。",
    "dz": "和 ts 同一个尾巴音：舌尖抵住上齿龈送气；声带要振动——兹。名词复数 lives、cows 结尾常读 dz。",
}

# ---------- 组装 levels ----------
levels = []
for n in range(30):
    ep = f"EP{n:02d}"
    lv = LV[ep]
    region = lv["region"]
    phonemes = []
    for sym in lv["phonemes"]:
        p = PH[sym]
        kp = KEY_POINT_FIX.get(sym, p["key_point"])
        phonemes.append({"sym": p["sym"], "name": p["name"], "type": p["type"],
                         "words": [{"w": w, "zh": word_zh(w)} for w in p["words"]],
                         "key_point": kp, "mnemonic": p["mnemonic"],
                         "unit": p["unit"]})
    x, y = NODES[ep]
    levels.append({
        "ep": ep, "title": lv["title"], "region": region, "regionName": REGION_NAME[region],
        "scene": lv["scene"], "tip": lv["tip"], "mnemonic": lv["mnemonic"],
        "phonemes": phonemes,
        "words": [{"w": w, "zh": word_zh(w)} if isinstance(w, str) else {"w": w[0], "zh": w[1]} for w in lv["words"]],
        "img": IMG[ep], "audio": ep.lower() + ".opus",
        "node": {"x": x, "y": y}, "quiz": Q[ep],
    })

# ---------- 组装 phonemes（图鉴用） ----------
TYPE_NAME = {"vowel-long": "长元音", "vowel-short": "短元音", "diphthong": "双元音",
             "cons-clear": "清辅音", "cons-voiced": "浊辅音", "nasal": "鼻音",
             "lateral": "舌侧音", "semivowel": "半元音"}
phonemes = []
for p in raw["phonemes"]:
    kp = KEY_POINT_FIX.get(p["sym"], p["key_point"])
    phonemes.append({
        "sym": p["sym"], "name": p["name"], "type": p["type"], "typeName": TYPE_NAME[p["type"]],
        "words": [{"w": w, "zh": word_zh(w)} for w in p["words"]],
        "key_point": kp, "mnemonic": p["mnemonic"],
        "ep": p["ep"], "unit": p["unit"], "audio": p["unit"].lower() + ".opus",
    })

data = {
    "levels": levels,
    "phonemes": phonemes,
    "regions": [
        {"id": "camp", "name": "出发营地", "sub": "建立概念 · 2 站", "badge": {"x": 12, "y": 53}},
        {"id": "vowel", "name": "元音城堡", "sub": "20 个元音 · 10 关", "badge": {"x": 20, "y": 10}},
        {"id": "cons", "name": "辅音王国", "sub": "28 个辅音 · 14 关", "badge": {"x": 65, "y": 12}},
        {"id": "peak", "name": "进阶峰", "sub": "毕业挑战 · 4 站", "badge": {"x": 80, "y": 31}},
    ],
}

out = os.path.join(BASE, "js", "data.js")
with open(out, "w", encoding="utf-8") as f:
    f.write("// 由 build_data.py 自动生成：30 关 + 48 音标 + 150 道闯关题\n")
    f.write("window.IPA_DATA = ")
    json.dump(data, f, ensure_ascii=False, indent=1)
    f.write(";\n")

# 校验
nq = sum(len(l["quiz"]) for l in levels)
print(f"levels={len(levels)}, phonemes={len(phonemes)}, 题目总数={nq}")
for l in levels:
    assert len(l["quiz"]) == 5, l["ep"]
    assert all("q" in x for x in l["quiz"]), l["ep"]
print("校验通过：每关 5 题")
print("输出:", out, f"{os.path.getsize(out)/1024:.0f} KB")
