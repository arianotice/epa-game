# -*- coding: utf-8 -*-
"""《声音探险队》图片文字合成脚本 · 总纲5张
用法: py synthesize_master.py
输出: 图片/成稿/ 下各图 *_合成.png
依赖: Pillow + numpy (py 启动器)
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
from collections import deque

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"
OUT = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/成稿"
FONT_IPA = "C:/Windows/Fonts/ARIALUNI.TTF"   # Arial Unicode MS: 完整 IPA
FONT_ZH = "C:/Windows/Fonts/msyh.ttc"        # 微软雅黑
FONT_ZH_BD = "C:/Windows/Fonts/msyhbd.ttc"   # 微软雅黑 Bold

INK = (35, 54, 78)       # #23364E 墨蓝
RED = (176, 58, 46)      # #B03A2E 石榴红
GREEN = (46, 125, 91)    # #2E7D5B 翡翠绿
BLUE = (46, 95, 138)     # #2E5F8A 蓝宝石
DRED = (140, 64, 52)     # #8C4034 暗红
CHIP = (233, 216, 180, 215)  # 羊皮纸色半透明底片

_fc = {}
def F(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]

def upscale(im, w, h):
    return im.resize((w, h), Image.LANCZOS)

def chip(draw, cx, cy, w, h):
    """半透明羊皮纸圆角底片"""
    draw.rounded_rectangle([cx - w/2, cy - h/2, cx + w/2, cy + h/2],
                           radius=h*0.28, fill=CHIP, outline=INK, width=2)

FALLBACK = set('↔')   # 雅黑缺字符号 → 用 ARIALUNI 回退绘制
def txt(draw, cx, cy, s, size, fill=INK, bold=True, chipbg=True):
    fp = FONT_ZH_BD if bold else FONT_ZH
    f = F(fp, size)
    # 总宽按实际字体分段累加（缺字符号用回退字体的宽度）
    w = sum(draw.textlength(ch, font=F(FONT_IPA if ch in FALLBACK else fp, size)) for ch in s)
    b = draw.textbbox((0, 0), s, font=f)
    h = b[3]-b[1]
    if chipbg:
        chip(draw, cx, cy, w + size*0.7, h + size*0.55)
    x0 = cx - w/2
    y0 = cy - h/2 - b[1]
    # 分段绘制：连续同字体字符为一段
    x = x0; i = 0
    while i < len(s):
        fb = s[i] in FALLBACK
        j = i
        while j < len(s) and (s[j] in FALLBACK) == fb:
            j += 1
        seg = s[i:j]
        if fb:
            fch = F(FONT_IPA, size)
            draw.text((x, cy), seg, font=fch, fill=fill, anchor="lm")
            x += draw.textlength(seg, font=fch)
        else:
            draw.text((x, y0), seg, font=f, fill=fill)
            x += draw.textlength(seg, font=f)
        i = j

def ipa(draw, cx, cy, s, size, fill=INK, chipbg=True, bold=False):
    f = F(FONT_IPA, size)
    b = draw.textbbox((0, 0), s, font=f)
    w, h = b[2]-b[0], b[3]-b[1]
    if chipbg:
        chip(draw, cx, cy, w + size*0.5, h + size*0.45)
    draw.text((cx - w/2 - b[0], cy - h/2 - b[1]), s, font=f, fill=fill)

def mixed(draw, cx, cy, ipa_str, zh_str, size, ipa_fill=INK, zh_fill=INK, chipbg=True):
    """IPA + 中文 混排居中"""
    f1 = F(FONT_IPA, size)
    f2 = F(FONT_ZH_BD, size)
    b1 = draw.textbbox((0, 0), ipa_str, font=f1); w1 = b1[2]-b1[0]
    b2 = draw.textbbox((0, 0), zh_str, font=f2); w2 = b2[2]-b2[0]
    gap = size * 0.35
    total = w1 + gap + w2
    h = max(b1[3]-b1[1], b2[3]-b2[1])
    if chipbg:
        chip(draw, cx, cy, total + size*0.6, h + size*0.5)
    x = cx - total/2
    draw.text((x - b1[0], cy - h/2 - b1[1]), ipa_str, font=f1, fill=ipa_fill)
    draw.text((x + w1 + gap - b2[0], cy - h/2 - b2[1]), zh_str, font=f2, fill=zh_fill)

def find_blobs(arr, rgb, tol=45, min_size=120, region=None, ds=4):
    """颜色blob检测(降采样加速)。region=(x0,y0,x1,y1)归一化。返回 [(cx,cy,size)] 原图坐标"""
    H, W = arr.shape[:2]
    if region:
        x0, y0, x1, y1 = [int(v*(W if i%2==0 else H)) for i, v in enumerate(region)]
        sub = arr[y0:y1, x0:x1]
    else:
        x0, y0 = 0, 0
        sub = arr
    dist = np.abs(sub.astype(int) - np.array(rgb)).sum(axis=2)
    mask = dist < tol
    h, w = mask.shape
    h2, w2 = h//ds, w//ds
    m2 = mask[:h2*ds, :w2*ds].reshape(h2, ds, w2, ds).any(axis=(1, 3))
    lab = np.zeros((h2, w2), dtype=int)
    blobs = []
    cur = 0
    for yy in range(h2):
        for xx in range(w2):
            if m2[yy, xx] and lab[yy, xx] == 0:
                cur += 1
                q = deque([(yy, xx)]); lab[yy, xx] = cur
                size = 0; sx = 0; sy = 0
                while q:
                    cy2, cx2 = q.popleft(); size += 1; sx += cx2; sy += cy2
                    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                        ny, nx = cy2+dy, cx2+dx
                        if 0 <= ny < h2 and 0 <= nx < w2 and m2[ny, nx] and lab[ny, nx] == 0:
                            lab[ny, nx] = cur; q.append((ny, nx))
                if size >= max(4, min_size//(ds*ds)):
                    blobs.append((x0 + sx/size*ds, y0 + sy/size*ds, size*ds*ds))
    return blobs

def nearest_assign(points, anchors):
    """points: [(x,y)]; anchors: [(x,y,name)] -> 每个点的名字(唯一匹配)"""
    used = set()
    result = []
    order = sorted(range(len(points)), key=lambda i: -min(
        (points[i][0]-a[0])**2 + (points[i][1]-a[1])**2 for a in anchors))
    pairs = []
    for i in order:
        best, bd = None, 1e18
        for j, a in enumerate(anchors):
            if j in used: continue
            d = (points[i][0]-a[0])**2 + (points[i][1]-a[1])**2
            if d < bd: bd, best = d, j
        used.add(best)
        pairs.append((i, anchors[best][2], bd**0.5))
    result = [None]*len(points)
    for i, name, d in pairs:
        result[i] = name
    return result

# ============================================================
# A1 英语音标大地图
# ============================================================
def synth_a1():
    im = upscale(Image.open(f"{BASE}/A1-英语音标大地图.png").convert("RGB"), 2560, 1600)
    d = ImageDraw.Draw(im, "RGBA")
    W, H = im.size
    def P(nx, ny): return (W*nx, H*ny)
    # 标题区（顶部中央空白带）
    txt(d, *P(0.50, 0.048), "英语音标大地图", 66, DRED)
    txt(d, *P(0.50, 0.098), "48 个音标精灵 · 四幕探险全图", 30, INK, bold=False, chipbg=False)
    # 四区标注
    txt(d, *P(0.135, 0.575), "出发营地", 30, DRED)
    txt(d, *P(0.365, 0.135), "元音城堡", 30, BLUE)
    txt(d, *P(0.735, 0.125), "辅音王国", 30, GREEN)
    txt(d, *P(0.855, 0.135), "进阶峰", 30, BLUE)
    # 路径标注
    txt(d, *P(0.505, 0.865), "探险路线", 24, INK, bold=False)
    # 图例（底部通栏）
    ly = H*0.955
    lx = W*0.5
    items = [("清音 · 短元音", RED), ("浊音", GREEN), ("长元音 · 双元音滑梯", BLUE)]
    f = F(FONT_ZH, 26)
    widths = []
    for s, c in items:
        b = d.textbbox((0,0), s, font=f); widths.append(b[2]-b[0])
    total = sum(widths) + len(items)*(30+18) + (len(items)-1)*36
    x = lx - total/2
    for (s, c), w in zip(items, widths):
        d.rounded_rectangle([x, ly-13, x+26, ly+13], radius=6, fill=c, outline=INK, width=2)
        d.text((x+38, ly-13), s, font=f, fill=INK)
        x += 26 + 12 + w + 36
    im.save(f"{OUT}/A1-英语音标大地图_合成.png")
    print("A1 done")

# ============================================================
# A2 元音城堡分区图（宝石检测 + 就近匹配）
# ============================================================
VOWEL_ANCHORS = [  # 四边形内标准锚点(归一化 0-1)
    (0.115, 0.045, "/iː/"), (0.300, 0.075, "/ɪ/"),
    (0.130, 0.360, "/e/"),  (0.150, 0.720, "/æ/"),
    (0.480, 0.300, "/ɜː/"), (0.480, 0.640, "/ə/"),
    (0.720, 0.760, "/ʌ/"),  (0.845, 0.900, "/ɑː/"), (0.615, 0.880, "/ɒ/"),
    (0.845, 0.050, "/uː/"), (0.680, 0.100, "/ʊ/"), (0.880, 0.430, "/ɔː/"),
]
DIPH_ORDER = ["/eɪ/", "/aɪ/", "/ɔɪ/", "/əʊ/", "/aʊ/", "/ɪə/", "/eə/", "/ʊə/"]

def synth_a2():
    src = Image.open(f"{BASE}/A2-元音城堡分区图.png").convert("RGB")
    im = upscale(src, 2560, 1600)
    d = ImageDraw.Draw(im, "RGBA")
    W, H = im.size
    arr = np.array(src)
    # 1) 四边形内12宝石(中央大厅区域)
    gems = []
    for rgb in (RED, BLUE):
        gems += find_blobs(arr, rgb, region=(0.30, 0.22, 0.70, 0.72), min_size=200)
    print("  A2 quad gems:", len(gems))
    # 归一化到四边形锚点空间
    xs = [g[0] for g in gems]; ys = [g[1] for g in gems]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    pad = 0.012
    pts = [((g[0]-x0)/(x1-x0+1e-6), (g[1]-y0)/(y1-y0+1e-6)) for g in gems]
    names = nearest_assign(pts, [(a[0], a[1], a[2]) for a in VOWEL_ANCHORS])
    # 四边形像素范围(用于轴标签)
    qx0, qx1 = x0 - (x1-x0)*pad, x1 + (x1-x0)*pad
    qy0, qy1 = y0 - (y1-y0)*pad, y1 + (y1-y0)*pad
    sx = W/src.size[0]; sy = H/src.size[1]
    qx0, qx1, qy0, qy1 = qx0*sx, qx1*sx, qy0*sy, qy1*sy
    # 2) 轴标签
    ipa(d, (qx0+qx1)/2, qy0 - 46, "高", 30, INK, chipbg=False)
    ipa(d, (qx0+qx1)/2, qy1 + 46, "低", 30, INK, chipbg=False)
    ipa(d, qx0 - 52, (qy0+qy1)/2, "前", 30, INK, chipbg=False)
    ipa(d, qx1 + 52, (qy0+qy1)/2, "后", 30, INK, chipbg=False)
    # 3) 每宝石贴音标(贴在宝石下方)
    for g, nm in zip(gems, names):
        if nm:
            ipa(d, g[0]*sx, g[1]*sy + 44, nm, 34, INK)
    # 4) 走廊8双元音:检测大厅外、城堡内的蓝色blob
    cx, cy = src.size[0]*0.5, src.size[1]*0.47
    ring = []
    for rgb in (BLUE, RED, GREEN):
        for b in find_blobs(arr, rgb, region=(0.06, 0.10, 0.94, 0.90), min_size=150):
            r = ((b[0]-cx)**2 + (b[1]-cy)**2) ** 0.5
            if 150 < r < 330:
                ring.append(b)
    print("  A2 ring blobs:", len(ring))
    # 按角度排序(从顶部顺时针)
    def ang(b):
        import math
        return (math.atan2(b[0]-cx, -(b[1]-cy)) + 2*math.pi) % (2*math.pi)
    ring.sort(key=ang)
    # 去除过近的重复
    filtered = []
    for b in ring:
        if all((b[0]-f[0])**2 + (b[1]-f[1])**2 > 60**2 for f in filtered):
            filtered.append(b)
    print("  A2 ring filtered:", len(filtered))
    for i, b in enumerate(filtered[:8]):
        nm = DIPH_ORDER[i] if i < 8 else ""
        if nm:
            ipa(d, b[0]*sx, b[1]*sy - 52, nm, 32, BLUE)
    # 5) 标题与注释
    txt(d, W*0.5, H*0.035, "元音城堡 · 20 位元音精灵", 46, DRED)
    txt(d, W*0.5, H*0.962, "单元音住四边形宫殿 · 双元音走走廊滑梯", 28, INK, bold=False)
    # 侧边剖面标注
    txt(d, W*0.075, H*0.415, "鼻腔", 22, INK, bold=False, chipbg=False)
    txt(d, W*0.065, H*0.475, "上颚", 22, INK, bold=False, chipbg=False)
    txt(d, W*0.075, H*0.545, "舌面", 22, INK, bold=False, chipbg=False)
    txt(d, W*0.075, H*0.615, "舌尖", 22, INK, bold=False, chipbg=False)
    im.save(f"{OUT}/A2-元音城堡分区图_合成.png")
    print("A2 done")

# ============================================================
# A3 辅音王国分区图（网格线检测 + 标准矩阵）
# ============================================================
MATRIX = {  # (row, col) -> ipa字符串 ; row 0-5, col 0-6
    (0,0): ("p","b"), (0,3): ("t","d"), (0,5): ("k","g"),
    (1,1): ("f","v"), (1,2): ("θ","ð"), (1,3): ("s","z"), (1,4): ("ʃ","ʒ"), (1,6): ("h",""),
    (2,4): ("tʃ","dʒ"),
    (3,0): ("m",""), (3,3): ("n",""), (3,5): ("ŋ",""),
    (4,3): ("l","r"),
    (5,0): ("w",""), (5,4): ("j",""),
}
COLS = ["双唇", "唇齿", "齿间", "齿龈", "齿龈后·硬腭", "软腭", "声门"]
ROWS = ["爆破", "摩擦", "破擦", "鼻音", "舌侧", "半元音"]

def detect_grid(arr):
    """检测矩阵网格线, 返回 (vlines, hlines) 像素坐标列表"""
    gray = arr.mean(axis=2)
    dark = gray < 110
    H, W = dark.shape
    # 中央区域
    rx0, rx1, ry0, ry1 = int(W*0.20), int(W*0.80), int(H*0.10), int(H*0.85)
    sub = dark[ry0:ry1, rx0:rx1]
    colsum = sub.sum(axis=0)
    rowsum = sub.sum(axis=1)
    rw = rx1-rx0
    vlines = [rx0+i for i, v in enumerate(colsum) if v > rw*0.45]
    hlines = [ry0+i for i, v in enumerate(rowsum) if v > (rx1-rx0)*0.45]
    def group(lines):
        if not lines: return []
        out = [[lines[0]]]
        for v in lines[1:]:
            if v - out[-1][-1] <= 3: out[-1].append(v)
            else: out.append([v])
        return [int(np.mean(g)) for g in out]
    return group(vlines), group(hlines)

def synth_a3():
    src = Image.open(f"{BASE}/A3-辅音王国分区图.png").convert("RGB")
    im = upscale(src, 2560, 1600)
    d = ImageDraw.Draw(im, "RGBA")
    W, H = im.size
    sx, sy = W/src.size[0], H/src.size[1]
    arr = np.array(src)
    vl, hl = detect_grid(arr)
    print("  A3 vlines:", len(vl), vl)
    print("  A3 hlines:", len(hl), hl)
    if len(vl) >= 8 and len(hl) >= 7:
        # 取最外侧的 7+1 条边界
        vlines = vl[:8] if len(vl) > 8 else vl
        hlines = hl[:7] if len(hl) > 7 else hl
    else:
        print("  A3 grid detection fallback")
        vlines = [src.size[0]*f for f in (0.268, 0.335, 0.402, 0.469, 0.536, 0.603, 0.670, 0.737)]
        hlines = [src.size[1]*f for f in (0.150, 0.243, 0.336, 0.429, 0.522, 0.615, 0.708)]
    # 轴标签
    for i, c in enumerate(COLS):
        cxm = (vlines[i]+vlines[i+1])/2 * sx
        txt(d, cxm, (hlines[0]-40)*sy, c, 26, INK, bold=False)
    for j, r in enumerate(ROWS):
        cym = (hlines[j]+hlines[j+1])/2 * sy
        txt(d, (vlines[0]-72)*sx, cym, r, 26, INK, bold=False)
    # 格内音标
    for (j, i), (a, b) in MATRIX.items():
        cx0, cx1 = vlines[i]*sx, vlines[i+1]*sx
        cy0, cy1 = hlines[j]*sy, hlines[j+1]*sy
        cxm, cym = (cx0+cx1)/2, (cy0+cy1)/2
        if b:
            ipa(d, cx0 + (cx1-cx0)*0.27, cym - (cy1-cy0)*0.22, a, 34, RED, chipbg=False)
            ipa(d, cx1 - (cx1-cx0)*0.27, cym - (cy1-cy0)*0.22, b, 34, GREEN, chipbg=False)
        else:
            ipa(d, cxm, cym - (cy1-cy0)*0.24, a, 34, INK, chipbg=False)
    # 四兄弟横条标签
    strip_y = (hlines[-1] + 95) * sy
    for k, s in enumerate(["/tr/", "/dr/", "/ts/", "/dz/"]):
        cxm = (vlines[k] + vlines[k+1]) / 2 * sx
        ipa(d, cxm, strip_y, s, 32, DRED)
    txt(d, W*0.5, H*0.035, "辅音王国 · 28 位辅音精灵", 46, DRED)
    txt(d, W*0.5, H*0.955, "清浊成对：左红右绿 · 中间声带波纹", 28, INK, bold=False)
    im.save(f"{OUT}/A3-辅音王国分区图_合成.png")
    print("A3 done")

# ============================================================
# F 口腔剖面总图
# ============================================================
def synth_f():
    im = upscale(Image.open(f"{BASE}/F-口腔剖面总图.png").convert("RGB"), 2400, 1600)
    d = ImageDraw.Draw(im, "RGBA")
    W, H = im.size
    txt(d, W*0.5, H*0.04, "发音四要素 · 口腔剖面图", 46, DRED)
    # 四要素小图图注(四角)
    txt(d, W*0.135, H*0.285, "① 唇形：开 ↔ 合", 26, INK, bold=False)
    txt(d, W*0.795, H*0.265, "② 舌位：高↔低 · 前↔后", 26, INK, bold=False)
    txt(d, W*0.135, H*0.875, "③ 气流：肺 → 口腔 → 唇外", 26, INK, bold=False)
    txt(d, W*0.80, H*0.885, "④ 声带：振动(浊) vs 不振动(清)", 26, INK, bold=False)
    # 角色
    txt(d, W*0.135, H*0.945, "波波队长", 24, DRED, bold=False)
    txt(d, W*0.85, H*0.50, "小 Q", 24, DRED, bold=False)
    txt(d, W*0.5, H*0.955, "所有音标的差别，都藏在这四个要素里", 26, INK, bold=False)
    im.save(f"{OUT}/F-口腔剖面总图_合成.png")
    print("F done")

# ============================================================
# 方形封面
# ============================================================
def synth_cover():
    im = upscale(Image.open(f"{BASE}/封面-方形.png").convert("RGB"), 3000, 3000)
    # 1536→3000 近 2 倍放大，轻度锐化补偿线画软化（平坦插画，percent 45 / threshold 3 安全）
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=45, threshold=3))
    d = ImageDraw.Draw(im, "RGBA")
    W, H = im.size
    txt(d, W*0.5, H*0.435, "声音探险队", 123, DRED, chipbg=False)
    txt(d, W*0.5, H*0.525, "48 个音标精灵", 59, INK, chipbg=False)
    txt(d, W*0.5, H*0.575, "小学英语音标启蒙播客", 38, INK, bold=False, chipbg=False)
    im.save(f"{OUT}/封面-方形_合成.png")
    print("cover done")

if __name__ == "__main__":
    synth_a1()
    synth_a2()
    synth_a3()
    synth_f()
    synth_cover()
    print("ALL DONE")
