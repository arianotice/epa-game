# -*- coding: utf-8 -*-
"""B 系列 24 张文字合成：徽章（IPA+汉字 hint+精灵名牌）+ 单词气泡 + 口诀横幅
版面数据来源：连通域检测 + 逐张底带核验（diag_bubbles5 / diag_band1-4）"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"
OUT = r"C:/Users/86135/英语音标播客/图片/成稿"
OUT = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/成稿"
FONT_IPA = "C:/Windows/Fonts/ARIALUNI.TTF"
FONT_ZH = "C:/Windows/Fonts/msyh.ttc"
FONT_ZH_BD = "C:/Windows/Fonts/msyhbd.ttc"
INK = (35, 54, 78); RED = (176, 58, 46); GREEN = (46, 125, 91); BLUE = (46, 95, 138)
PARCH = (233, 216, 180); WHITE = (255, 255, 255)
OW, OH = 2400, 1350
S = OW / 1536.0

_fc = {}
def F(p, s):
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]

def light(c, f=0.42):
    return tuple(int(v + (255 - v) * f) for v in c)

# ---------------------------------------------------------------- 元素绘制
def badge(d, cx, cy, color, ipa, hint, name=None, r=112, label=None):
    """菱形徽章（IPA+hint）+ 下方同名牌；B25 用 label 模式"""
    pts = [(cx, cy - r), (cx + r * 0.78, cy), (cx, cy + r), (cx - r * 0.78, cy)]
    d.polygon(pts, fill=color)
    d.line(pts + [pts[0]], fill=INK, width=5, joint="curve")
    g = light(color)
    for gx, gy in pts:
        d.ellipse([gx - 11, gy - 11, gx + 11, gy + 11], fill=g, outline=INK, width=2)
    if label:  # B25：IPA + 名称行
        d.text((cx, cy - 30), ipa, font=F(FONT_IPA, 60), fill=WHITE, anchor="mm")
        d.text((cx, cy + 32), label, font=F(FONT_ZH_BD, 24), fill=WHITE, anchor="mm")
        return
    d.text((cx, cy - 44), ipa, font=F(FONT_IPA, 72), fill=WHITE, anchor="mm")
    d.text((cx, cy + 28), hint, font=F(FONT_ZH_BD, 25), fill=WHITE, anchor="mm")
    if name:
        f = F(FONT_ZH_BD, 27)
        w = d.textlength(name, font=f)
        pw, ph = w + 42, 52
        py = cy + r + ph / 2 - 12
        d.rounded_rectangle([cx - pw / 2, py - ph / 2, cx + pw / 2, py + ph / 2],
                            radius=13, fill=color, outline=INK, width=3)
        d.text((cx, py), name, font=f, fill=WHITE, anchor="mm")

def bubble(d, cx, cy, bw, bh, words=None, contrast=None, plain=None):
    """气泡内文字：words=[(en,zh,color)] / contrast=(kwL,kwR,cL,cR) / plain=[(text,color)]"""
    cx, cy, bw, bh = cx * S, cy * S, bw * S, bh * S
    maxw, maxh = bw - 34, bh - 18
    if words:
        n = len(words)
        for size in range(31, 12, -1):
            lh = size + 9
            if lh * n > maxh:
                continue
            ok = True
            for en, zh, c in words:
                w = d.textlength(en + "  ", font=F(FONT_ZH_BD, size)) + \
                    d.textlength(zh, font=F(FONT_ZH, size))
                if w > maxw:
                    ok = False; break
            if ok:
                break
        lh = size + 9
        y0 = cy - (n - 1) * lh / 2
        for i, (en, zh, c) in enumerate(words):
            fe = F(FONT_ZH_BD, size); fz = F(FONT_ZH, size)
            we = d.textlength(en + "  ", font=fe)
            wz = d.textlength(zh, font=fz)
            x = cx - (we + wz) / 2
            d.text((x, y0 + i * lh), en, font=fe, fill=c, anchor="lm")
            d.text((x + we, y0 + i * lh), zh, font=fz, fill=INK, anchor="lm")
    elif contrast:
        kwL, kwR, cL, cR = contrast
        for size in range(30, 13, -1):
            fL = F(FONT_ZH_BD, size); fA = F(FONT_IPA, size); fR = F(FONT_ZH_BD, size)
            wL = d.textlength(kwL, font=fL)
            wA = d.textlength(" ↔ ", font=fA)
            wR = d.textlength(kwR, font=fR)
            if wL + wA + wR <= maxw and size <= maxh:
                break
            size -= 1
        x = cx - (wL + wA + wR) / 2
        d.text((x, cy), kwL, font=fL, fill=cL, anchor="lm")
        d.text((x + wL, cy), "↔", font=fA, fill=INK, anchor="lm")
        d.text((x + wL + wA, cy), kwR, font=fR, fill=cR, anchor="lm")
    elif plain:
        n = len(plain)
        for size in range(29, 12, -1):
            lh = size + 8
            if lh * n > maxh:
                continue
            if all(d.textlength(t, font=F(FONT_ZH_BD, size)) <= maxw for t, c in plain):
                break
        lh = size + 8
        y0 = cy - (n - 1) * lh / 2
        for i, (t, c) in enumerate(plain):
            d.text((cx, y0 + i * lh), t, font=F(FONT_ZH_BD, size), fill=c, anchor="mm")

def banner_zone(bright, bubble_bot):
    """返回 (text_center, zone_top, zone_bot, fold_row)。
    结构：上褶皱线 → 净主体 → 下褶皱实线 → 波浪花边。
    中央区(25%-75%)逐行暗计数 + 平滑；下褶皱=[0.86H,0.965H]平滑峰值行；
    上褶皱=从下褶皱向上扫，主体(count<=300)之上第一行 >300 的线。"""
    H, W = bright.shape
    cen = bright[:, int(0.25 * W):int(0.75 * W)]
    ccnt = np.array([(cen[y] < 150).sum() for y in range(H)], dtype=float)
    sm = np.convolve(ccnt, np.ones(5) / 5, mode="same")
    # 下褶皱实线
    lo, hi = int(0.86 * H), int(0.965 * H)
    fold = lo + int(np.argmax(sm[lo:hi]))
    fold_top = fold - 6
    # 上褶皱：跳过下褶皱带 → 主体 → 第一行 >300
    y = fold - 6
    while y > int(0.60 * H) and sm[y] > 250:
        y -= 1
    while y > int(0.60 * H) and sm[y] <= 300:
        y -= 1
    top_fold_bot = y + 1
    body_top = max(top_fold_bot + 2, int(0.60 * H))
    # 可用区：避开气泡与上下褶皱
    zone_top = max(bubble_bot + 4, body_top + 4)
    zone_bot = fold_top - 2
    base = fold - 76                      # 经验基准（B02 验收位标定）
    bh2 = 24                              # 两行文字块半高（源图px）
    if zone_top + bh2 <= zone_bot - bh2:
        c = min(max(base, zone_top + bh2), zone_bot - bh2)
    else:                                 # 紧凑：居中于可用区
        c = (zone_top + zone_bot) / 2
    return c, zone_top, zone_bot, fold

def draw_banner(d, cx, cy, lines, zone_h=None):
    """两行/三行口诀；宽度自适应 1680px，高度不足时缩小字号。
    墨高估算：n 行时 ink ≈ (n-1)*(size+11) + 2*0.45*size + size*0.45（首行上半）"""
    size = 33 if len(lines) <= 2 else 26
    while size > 19 and any(d.textlength(l, font=F(FONT_ZH_BD, size)) > 1680 for l in lines):
        size -= 2
    if zone_h:
        maxh = zone_h * S - 4           # 可用高度（合成px，留 2px 余量）
        while size > 18:
            ink = (len(lines) - 1) * (size + 11) + 0.9 * size + 2
            if ink <= maxh:
                break
            size -= 2
    lh = size + 11
    y0 = cy - (len(lines) - 1) * lh / 2
    for i, l in enumerate(lines):
        d.text((cx, y0 + i * lh), l, font=F(FONT_ZH_BD, size), fill=INK, anchor="mm")
    return size

# ---------------------------------------------------------------- 数据
# 气泡: (cx, cy, w, h, kind, content)  kind: W=单词 C=对比 P=纯文本
D = []
def add(file, L, R, bubbles, banner, badges=None):
    D.append(dict(file=file, L=L, R=R, bubbles=bubbles, banner=banner, badges=badges))

add("B02-阳光农场_iː-vs-ɪ",
    ("/iː/", "衣——", "微笑小姐", BLUE), ("/ɪ/", "咦", "放松精灵", RED),
    [(307,675,259,118,"W",[("sheep","绵羊",BLUE),("tree","大树",BLUE),("green","绿色",BLUE)]),
     (769,677,255,112,"C",("拖长","短促",BLUE,RED)),
     (1214,678,253,115,"W",[("ship","小船",RED),("fish","鱼",RED),("big","大大的",RED)])],
    ["嘴角微笑拉耳边，拖长音，是 sheep；嘴巴微张松又轻，短促咦，是 ship；",
     "一只 sheep 游啊游，游成了小船 ship！"])
add("B03-早餐桌_e-vs-æ",
    ("/e/", "诶", "小口精灵", RED), ("/æ/", "哎", "大口精灵", BLUE),
    [(310,618,200,81,"W",[("egg","鸡蛋",RED),("bed","床",RED)]),
     (370,708,200,75,"W",[("red","红色",RED),("pen","钢笔",RED)]),
     (825,665,200,110,"C",("小口","大口",RED,BLUE)),
     (1265,659,210,110,"W",[("apple","苹果",BLUE),("hand","手",BLUE)])],
    ["一小口，短促诶，鸡蛋 egg 床上睡；打哈欠，下巴掉，苹果 apple 手中抱。",
     "手指一量就知道，小口大口差一档！"])
add("B04-上学路_ɑː-vs-ʌ",
    ("/ɑː/", "啊——", "医生精灵", BLUE), ("/ʌ/", "啊", "戳肚子精灵", RED),
    [(275,673,250,92,"W",[("car","小汽车",BLUE),("park","公园",BLUE),("star","星星",BLUE)]),
     (756,672,288,91,"C",("长开","短松",BLUE,RED)),
     (1251,669,270,105,"W",[("bus","公交",RED),("cup","杯子",RED),("duck","鸭子",RED)])],
    ["医生查喉咙，啊——又长又开，小汽车 car 开进 park；戳一下肚子，啊，短又松，",
     "鸭子 duck 跳上 bus。长的是医生，短的是戳肚，一长一短分清楚！"])
add("B05-运动会_ɒ-vs-ɔː",
    ("/ɒ/", "哦", "吹泡泡精灵", RED), ("/ɔː/", "哦——", "吸果冻精灵", BLUE),
    [(256,656,213,132,"W",[("hot","热",RED),("dog","狗",RED),("box","盒子",RED)]),
     (1287,652,210,124,"W",[("ball","球",BLUE),("horse","小马",BLUE),("door","门",BLUE)])],
    ["嘴巴撮圆像小鱼，吹泡泡，哦，短又快，小狗 dog 守着 box；吸果冻，哦——长又圆，",
     "小马 horse 顶着 ball。快的吹泡，慢的吸冻，一快一慢记心间！"])
add("B06-睡前卧室_ʊ-vs-uː",
    ("/ʊ/", "唔", "轻轻推精灵", RED), ("/uː/", "呜——", "吹蜡烛精灵", BLUE),
    [(272,653,255,108,"W",[("book","书",RED),("foot","脚",RED)]),
     (587,667,252,101,"W",[("good","好",RED)]),
     (942,659,258,109,"W",[("food","食物",BLUE),("moon","月亮",BLUE)]),
     (1261,650,256,109,"W",[("blue","蓝色",BLUE)])],
    ["嘴巴圆成小圆圈，轻轻推，唔，短又松，故事 book 放在 foot 边；吹蜡烛，呜——长又紧，",
     "月亮 moon 照着 blue。松的是推，紧的是吹，一松一紧要分明！"])
add("B07-动物园回家_ɜː-vs-ə",
    ("/ɜː/", "呃——", "卷舌弹簧精灵", BLUE), ("/ə/", "呃", "偷懒叹气精灵", RED),
    [(254,671,168,98,"W",[("bird","小鸟",BLUE),("girl","女孩",BLUE),("nurse","护士",BLUE)]),
     (761,667,169,81,"C",("卷舌","懒叹",BLUE,RED)),
     (1273,668,170,89,"W",[("banana","香蕉",RED),("panda","熊猫",RED),("teacher","老师",RED)])],
    ["舌头卷成小弹簧，呃——停在正中央，小鸟 bird，女孩 girl，护士 nurse 忙又忙；",
     "嘴巴偷懒叹口气，呃，短得几乎听不见，香蕉 banana，熊猫 panda，老师 teacher。卷的是弹簧，懒的是叹气！"])
add("B08-生日派对_eɪ-vs-aɪ",
    ("/eɪ/", "诶→衣", "滑滑梯哥哥", BLUE), ("/aɪ/", "啊→衣", "滑滑梯弟弟", BLUE),
    [(304,649,230,60,"W",[("cake","蛋糕",BLUE)]),
     (587,650,230,60,"W",[("name","名字",BLUE)]),
     (941,650,230,60,"W",[("rain","雨",BLUE)]),
     (1228,650,230,60,"P",[("诶→衣",BLUE)]),
     (319,714,200,55,"W",[("bike","自行车",BLUE)]),
     (556,714,210,55,"W",[("kite","风筝",BLUE)]),
     (965,715,210,55,"W",[("five","五",BLUE)]),
     (1205,714,205,55,"P",[("啊→衣",BLUE)])],
    ["滑滑梯，溜两段，诶滑到衣，是字母 A，蛋糕 cake、名字 name、窗外 rain；",
     "啊滑到衣，是字母 I，自行车 bike、风筝 kite、蜡烛 five。起点不同路线变，一高一低记心间！"])
add("B09-玩具箱感冒_ɔɪ-vs-əʊ",
    ("/ɔɪ/", "哦→衣", "欢呼精灵", BLUE), ("/əʊ/", "欧→呜", "含糖精灵", BLUE),
    [(460,690,300,100,"W",[("toy","玩具",BLUE),("boy","男孩",BLUE),("noise","吵闹",BLUE)]),
     (764,684,202,76,"C",("欢呼","含糖",BLUE,BLUE)),
     (1300,690,240,100,"W",[("nose","鼻子",BLUE),("home","家",BLUE),("boat","小船",BLUE)])],
    ["打开箱子，哦—衣，toy 和 boy 吵闹 noise；含颗糖，欧——，nose 通，",
     "回 home 的路上划着 boat。欢呼滑两格，含糖圆一颗！"])
add("B10-我的家_aʊ-vs-ɪə",
    ("/aʊ/", "啊→呜", "惊叹精灵", BLUE), ("/ɪə/", "衣→呃", "悄悄话精灵", BLUE),
    [(274,654,235,95,"W",[("house","房子",BLUE),("mouth","嘴",BLUE)]),
     (597,670,191,64,"W",[("cow","奶牛",BLUE)]),
     (933,670,223,65,"W",[("ear","耳朵",BLUE),("near","近",BLUE)]),
     (1263,668,211,95,"W",[("deer","鹿",BLUE)])],
    ["大房子，啊——呜，house 大，mouth 张，奶牛 cow 站在草地上；",
     "贴耳朵，一——呃，ear 朵，在 near 处，小 deer 轻轻走过来。一个往外张，一个往里收！"])
add("B11-理发店旅行_eə-vs-ʊə",
    ("/eə/", "诶→呃", "头发文静精灵", BLUE), ("/ʊə/", "乌→呃", "行李文静精灵", BLUE),
    [(258,678,189,101,"W",[("hair","头发",BLUE),("bear","熊",BLUE),("chair","椅子",BLUE)]),
     (765,694,192,89,"C",("诶→呃","乌→呃",BLUE,BLUE)),
     (1265,682,202,100,"W",[("tour","旅行",BLUE),("sure","确信",BLUE)])],
    ["风吹头发诶到呃，扁嘴轻滑不拖拉；收拾行李乌到呃，圆唇放松去旅行。",
     "两个声音最文静，单词虽少认得清！"])
add("B12-纸飞机_p-vs-b",
    ("/p/", "噗", "纸飞机兄弟", RED), ("/b/", "卜", "打鼓兄弟", GREEN),
    [(385,650,300,100,"W",[("pack","书包",RED),("pig","猪",RED)]),
     (725,675,120,55,"W",[("cap","帽子",RED)]),
     (1135,650,300,100,"W",[("back","背",GREEN),("big","大",GREEN)]),
     (1420,650,110,55,"W",[("cab","出租车",GREEN)])],
    ["双唇紧闭先关门，突然打开气流喷；纸飞机音不振动，打鼓声音喉咙震。",
     "嘴型相同开关换，手贴喉咙马上辨！"])
add("B13-动物园_t-vs-d",
    ("/t/", "特", "轻锤「特」", RED), ("/d/", "德", "响锤「德」", GREEN),
    [(210,647,194,118,"W",[("tie","领带",RED),("town","城镇",RED),("coat","外套",RED)]),
     (933,673,178,84,"C",("不振动","振动",RED,GREEN)),
     (1298,655,220,131,"W",[("die","死",GREEN),("down","下",GREEN),("code","代码",GREEN)])],
    ["舌尖抬起贴齿龈，突然弹开气流喷；轻锤一声「特」不麻，响锤一声「德」嗡嗡。",
     "同一把小锤子，声带开关定清浊！"])
add("B14-放风筝_k-vs-g",
    ("/k/", "咔", "咳嗽「咔」", RED), ("/g/", "咕", "打嗝「咕」", GREEN),
    [(233,675,177,99,"W",[("cap","帽子",RED),("class","班级",RED)]),
     (583,666,177,96,"W",[("pick","捡",RED)]),
     (915,672,179,93,"W",[("gap","缺口",GREEN),("glass","玻璃",GREEN)]),
     (1284,666,196,106,"W",[("pig","猪",GREEN)])],
    ["舌根抬起顶软腭，突然松开气流冲；咳嗽一声「咔」不麻，打嗝一声「咕」嗡嗡。",
     "同一块舌根肉，声带开关定清浊！"])
add("B15-花店早餐_f-vs-v",
    ("/f/", "夫", "咬唇哥哥", RED), ("/v/", "V", "咬唇弟弟", GREEN),
    [(589,685,231,108,"W",[("fine","好",RED),("safe","安全",RED),("fan","迷",RED)]),
     (923,699,148,100,"C",("不振动","振动",RED,GREEN)),
     (1272,673,226,133,"W",[("vine","藤",GREEN),("save","救",GREEN),("van","厢式货车",GREEN)])],
    ["上牙轻轻搭下唇，气流挤出小缝走；哥哥吹气不振动，弟弟振动嗡嗡抖。",
     "牙齿不碰就变味，背心一晃变西方！"])
add("B16-生日蜡烛_θ-vs-ð",
    ("/θ/", "斯·咬舌", "咬舌哥哥", RED), ("/ð/", "兹·咬舌", "咬舌弟弟", GREEN),
    [(290,666,229,77,"W",[("think","想",RED),("thin","瘦",RED)]),
     (598,666,234,77,"W",[("three","三",RED)]),
     (929,667,236,76,"W",[("then","那时",GREEN),("than","比",GREEN)]),
     (1243,669,231,80,"W",[("weather","天气",GREEN)])],
    ["舌尖探出小门缝，轻轻送气别伸太长；哥哥安静吐气斯，弟弟嗡嗡振动兹。",
     "碰到牙齿往回缩，汉语里可没这一双！"])
add("B17-蛇与蜂巢_s-vs-z",
    ("/s/", "斯", "小蛇精灵", RED), ("/z/", "兹", "蜜蜂精灵", GREEN),
    [(276,672,190,110,"W",[("sip","小口喝",RED),("bus","公交",RED),("rice","米",RED)]),
     (772,665,187,92,"C",("不振动","振动",RED,GREEN)),
     (1268,667,191,100,"W",[("zip","拉链",GREEN),("buzz","嗡嗡",GREEN),("rise","升起",GREEN)])],
    ["牙齿合上留条缝，气流挤过嘶嘶响；喉咙不动是小蛇，声带一开蜜蜂忙。",
     "同一嘴型换开关，手贴喉咙马上辨！"])
add("B18-海边电视_ʃ-vs-ʒ",
    ("/ʃ/", "嘘", "海边「嘘」", RED), ("/ʒ/", "呼噜", "电视「呼噜」", GREEN),
    [(258,673,240,83,"W",[("fish","鱼",RED),("sheep","绵羊",RED),("ship","船",RED)]),
     (761,674,260,82,"C",("不振动","振动",RED,GREEN)),
     (1273,674,243,83,"W",[("measure","测量",GREEN),("treasure","宝藏",GREEN),("usually","通常",GREEN)])],
    ["嘴唇撮圆轻轻嘘，图书馆里清又静；同一嘴型声带开，嘘声打起小呼噜。",
     "汉语里面没有它，手贴喉咙捉住它！"])
add("B19-暖手兔子_h-vs-r",
    ("/h/", "哈", "哈气精灵", RED), ("/r/", "若", "钩子精灵", GREEN),
    [(365,690,270,90,"W",[("hat","帽子",RED),("happy","开心",RED)]),
     (720,690,270,90,"W",[("hand","手",RED)]),
     (1120,690,270,90,"W",[("rabbit","兔子",GREEN),("run","跑",GREEN)]),
     (1390,690,200,90,"W",[("rice","米",GREEN)])],
    ["冬天冷，哈——，气流冲出声带静；舌尖钩，悬半空，别念日也别念热；",
     "兔子跑，米饭香，钩子精灵记心上！"])
add("B20-教室果酱_tʃ-vs-dʒ",
    ("/tʃ/", "吃", "火车精灵", RED), ("/dʒ/", "只", "果酱精灵", GREEN),
    [(232,628,166,99,"W",[("chair","椅子",RED),("cheese","奶酪",RED),("teacher","老师",RED)]),
     (760,643,171,81,"C",("不振动","振动",RED,GREEN)),
     (1292,630,168,95,"W",[("juice","果汁",GREEN),("jeans","牛仔裤",GREEN),("jam","果酱",GREEN)])],
    ["小火车，哧——吃——，先堵住，再摩擦；挖果酱，黏又稠，喉咙嗡嗡跟着走；",
     "嘴巴先抵后撮圆，破擦两音记心间！"])
add("B21-睡前餐桌_m-vs-n",
    ("/m/", "嗯·闭嘴", "哼歌嗯", RED), ("/n/", "嗯·舌尖", "点头嗯", BLUE),
    [(594,673,208,96,"W",[("moon","月亮",RED),("mom","妈妈",RED),("milk","牛奶",RED)]),
     (910,670,221,100,"W",[("nose","鼻子",BLUE),("pen","钢笔",BLUE),("dinner","晚餐",BLUE)]),
     (1300,656,225,149,"C",("闭嘴","舌尖",RED,BLUE))],
    ["闭嘴哼歌嗯嗯嗯，月亮妈妈和牛奶；舌尖点头嗯嗯嗯，鼻子钢笔吃晚餐。",
     "捏住鼻子全哑掉，一松手呀全回来！"])
add("B22-打鼾国王_ŋ-vs-n",
    ("/n/", "嗯·舌尖", "点头嗯", RED), ("/ŋ/", "嗯·舌根", "打鼾嗯", BLUE),
    [(234,659,215,113,"W",[("sin","罪",RED),("win","赢",RED)]),
     (608,689,176,72,"W",[("ran","跑",RED)]),
     (907,689,176,73,"W",[("sing","唱",BLUE),("wing","翅膀",BLUE)]),
     (1297,658,222,109,"W",[("rang","响",BLUE)])],
    ["舌尖点头嗯嗯嗯，舌根打鼾嗯嗯嗯；一个在前一个后，唱歌 sing 别唱错。",
     "嘴唇舌尖加舌根，三个鼻音全到齐！"])
add("B23-开关水果_l首l尾",
    ("/l/", "了·清晰", "钩子精灵·词首", RED), ("/l/", "欧·模糊", "钩子精灵·词尾", BLUE),
    [(230,663,191,83,"W",[("light","灯",RED),("night","夜",RED)]),
     (580,684,175,73,"W",[("right","右",RED)]),
     (939,681,181,73,"W",[("apple","苹果",BLUE)]),
     (1301,655,200,90,"W",[("blue","蓝色",BLUE)])],
    ["舌尖小钩钩住埂，两边漏气快乐了；跑到词尾别松口，闷出一个小欧欧。",
     "苹果要读艾泡泡，吞掉尾巴就漏了！"])
add("B24-喝水画画_w-vs-j",
    ("/w/", "呜→衣", "喝水「呜」", RED), ("/j/", "耶", "闪电「耶」", BLUE),
    [(303,667,221,98,"W",[("water","水",RED),("window","窗",RED)]),
     (601,672,209,89,"W",[("west","西",RED)]),
     (920,675,213,88,"W",[("yellow","黄",BLUE),("yogurt","酸奶",BLUE)]),
     (1223,663,220,105,"W",[("vest","背心",BLUE)])],
    ["嘴唇撮圆亲一下，呜地滑走不停留；we 要读呜加衣，千万别读一个威。",
     "耶要短得像闪电，耶完立刻接元音！"])

# B25 四宫格特例
B25 = dict(
    file="B25-火车站_四宫格特例",
    badges=[("/tr/", "戳·火车头", RED, 254, 320), ("/dr/", "啄·啄木鸟", GREEN, 902, 320),
            ("/ts/", "呲·漏气", RED, 254, 510), ("/dz/", "兹·蜜蜂", GREEN, 902, 510)],
    bubbles=[(335,720,281,75,"W",[("tree","树",RED),("train","火车",RED),("cats","猫",RED),("students","学生",RED)]),
             (756,715,300,61,"P",[("名词复数尾巴音",INK),("先听前面抖不抖",INK)]),
             (1179,717,290,68,"W",[("dress","连衣裙",GREEN),("drink","喝",GREEN),("beds","床",GREEN),("friends","朋友",GREEN)])],
    banner=["火车头，戳和啄，戳不动来啄要抖；戳是树 tree，啄是裙 dress。",
            "尾巴音，呲和兹，呲像漏气兹像蜜蜂；呲是猫 cats，兹是床 beds。名词复数加尾巴，先看前面抖不抖！"])

# ---------------------------------------------------------------- 执行
BL = (476, 259); BR = (1060, 259)   # 标准模板徽章位（源图坐标）
for e in D:
    src = Image.open(f"{BASE}/{e['file']}.png").convert("RGB")
    im = src.resize((OW, OH), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    bright = np.array(src).sum(axis=2) / 3
    bubble_bot = max(cy + bh / 2 for cx, cy, bw, bh, k, c in e["bubbles"])
    bcy, zt, zb, fold = banner_zone(bright, bubble_bot)
    # 徽章 + 名牌
    badge(d, BL[0]*S, BL[1]*S, e["L"][3], e["L"][0], e["L"][1], e["L"][2])
    badge(d, BR[0]*S, BR[1]*S, e["R"][3], e["R"][0], e["R"][1], e["R"][2])
    # 气泡
    for cx, cy, bw, bh, kind, content in e["bubbles"]:
        if kind == "W":
            bubble(d, cx, cy, bw, bh, words=content)
        elif kind == "C":
            bubble(d, cx, cy, bw, bh, contrast=content)
        else:
            bubble(d, cx, cy, bw, bh, plain=content)
    # 横幅口诀（高度自适应）
    sz = draw_banner(d, OW/2, bcy*S, e["banner"], zone_h=zb - zt)
    im.save(f"{OUT}/{e['file']}_合成.png")
    print(f"OK {e['file']}  bannerY={bcy:.0f} zone={zt:.0f}-{zb:.0f} fold={fold} size={sz}")

# B25
src = Image.open(f"{BASE}/{B25['file']}.png").convert("RGB")
im = src.resize((OW, OH), Image.LANCZOS)
d = ImageDraw.Draw(im, "RGBA")
bright = np.array(src).sum(axis=2) / 3
bubble_bot = max(cy + bh / 2 for cx, cy, bw, bh, k, c in B25["bubbles"])
bcy, zt, zb, fold = banner_zone(bright, bubble_bot)
for ipa, label, color, bx, by in B25["badges"]:
    badge(d, bx*S, by*S, color, ipa, None, label=label, r=106)
for cx, cy, bw, bh, kind, content in B25["bubbles"]:
    if kind == "W":
        bubble(d, cx, cy, bw, bh, words=content)
    else:
        bubble(d, cx, cy, bw, bh, plain=content)
sz = draw_banner(d, OW/2, bcy*S, B25["banner"], zone_h=zb - zt)
im.save(f"{OUT}/{B25['file']}_合成.png")
print(f"OK {B25['file']}  bannerY={bcy:.0f} zone={zt:.0f}-{zb:.0f} fold={fold} size={sz}")
print("ALL DONE")
