# -*- coding: utf-8 -*-
"""A2/A3 终版合成：A3 程序化标准矩阵面板 + A2 轴标签/走廊双元音"""
import math
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from collections import deque

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"
OUT = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/成稿"
FONT_IPA = "C:/Windows/Fonts/ARIALUNI.TTF"
FONT_ZH = "C:/Windows/Fonts/msyh.ttc"
FONT_ZH_BD = "C:/Windows/Fonts/msyhbd.ttc"
INK = (35, 54, 78); RED = (176, 58, 46); GREEN = (46, 125, 91)
BLUE = (46, 95, 138); DRED = (140, 64, 52); PARCH = (233, 216, 180)
CHIP = (233, 216, 180, 220)

_fc = {}
def F(p, s):
    if (p, s) not in _fc: _fc[(p, s)] = ImageFont.truetype(p, s)
    return _fc[(p, s)]

def chip(d, cx, cy, w, h):
    d.rounded_rectangle([cx-w/2, cy-h/2, cx+w/2, cy+h/2], radius=h*0.28,
                        fill=CHIP, outline=INK, width=2)

def txt(d, cx, cy, s, size, fill=INK, bold=True, chipbg=True):
    f = F(FONT_ZH_BD if bold else FONT_ZH, size)
    b = d.textbbox((0, 0), s, font=f); w, h = b[2]-b[0], b[3]-b[1]
    if chipbg: chip(d, cx, cy, w+size*0.7, h+size*0.55)
    d.text((cx-w/2-b[0], cy-h/2-b[1]), s, font=f, fill=fill)

def ipa(d, cx, cy, s, size, fill=INK, chipbg=False):
    f = F(FONT_IPA, size)
    b = d.textbbox((0, 0), s, font=f); w, h = b[2]-b[0], b[3]-b[1]
    if chipbg: chip(d, cx, cy, w+size*0.5, h+size*0.45)
    d.text((cx-w/2-b[0], cy-h/2-b[1]), s, font=f, fill=fill)

def diamond(d, cx, cy, r, color, outline=INK):
    d.polygon([(cx, cy-r), (cx+r*0.78, cy), (cx, cy+r), (cx-r*0.78, cy)],
              fill=color, outline=outline)

def diamond_split(d, cx, cy, r):
    """左红右绿菱形 + 中间声带波纹"""
    d.polygon([(cx, cy-r), (cx, cy+r), (cx-r*0.78, cy)], fill=RED, outline=INK)
    d.polygon([(cx, cy-r), (cx, cy+r), (cx+r*0.78, cy)], fill=GREEN, outline=INK)
    pts = []
    for i in range(0, 21):
        t = i/20
        x = cx - r*0.78 + t*r*1.56
        y = cy + math.sin(t*math.pi*3)*r*0.16
        pts.append((x, y))
    d.line(pts, fill=INK, width=3)

# ---------------------------------------------------------------- A2
DIPH = ["/eɪ/", "/aɪ/", "/ɔɪ/", "/əʊ/", "/aʊ/", "/ɪə/", "/eə/", "/ʊə/"]
RED = (176, 58, 46); BLUE = (46, 95, 138); GREEN = (46, 125, 91)

def blobs(arr, rgb, tol=45, min_size=140, region=None, ds=4):
    Hh, Ww = arr.shape[:2]
    if region:
        x0, y0 = int(region[0]*Ww), int(region[1]*Hh)
        sub = arr[int(region[1]*Hh):int(region[3]*Hh), int(region[0]*Ww):int(region[2]*Ww)]
    else:
        x0 = y0 = 0; sub = arr
    dist = np.abs(sub.astype(int) - np.array(rgb)).sum(axis=2)
    mask = dist < tol
    h, w = mask.shape; h2, w2 = h//ds, w//ds
    m2 = mask[:h2*ds, :w2*ds].reshape(h2, ds, w2, ds).any(axis=(1, 3))
    lab = np.zeros((h2, w2), dtype=int); out = []; cur = 0
    for yy in range(h2):
        for xx in range(w2):
            if m2[yy, xx] and lab[yy, xx] == 0:
                cur += 1; q = deque([(yy, xx)]); lab[yy, xx] = cur
                size = 0; sx = 0; sy = 0
                while q:
                    cy2, cx2 = q.popleft(); size += 1; sx += cx2; sy += cy2
                    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
                        ny, nx = cy2+dy, cx2+dx
                        if 0 <= ny < h2 and 0 <= nx < w2 and m2[ny, nx] and lab[ny, nx] == 0:
                            lab[ny, nx] = cur; q.append((ny, nx))
                if size >= max(4, min_size//(ds*ds)):
                    out.append((x0+sx/size*ds, y0+sy/size*ds))
    return out

def synth_a2():
    src = Image.open(f"{BASE}/A2-元音城堡分区图.png").convert("RGB")
    S = 2560/src.size[0]
    im = src.resize((2560, 1600), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    arr = np.array(src)
    # 走廊8格检测
    cx, cy = 768, 482
    ring = []
    for rgb in (RED, BLUE, GREEN):
        for b in blobs(arr, rgb, region=(0.05, 0.08, 0.95, 0.92)):
            r = math.hypot(b[0]-cx, b[1]-cy)
            if 250 < r < 430:
                ring.append(b)
    def ang(b): return math.degrees(math.atan2(-(b[1]-cy), b[0]-cx)) % 360
    ring.sort(key=ang)
    groups = []
    for b in ring:
        if groups and abs(((ang(b)-ang(groups[-1][0]))+180)%360-180) < 25:
            groups[-1].append(b)
        else:
            groups.append([b])
    centers = [(float(np.mean([b[0] for b in g])), float(np.mean([b[1] for b in g])))
               for g in groups]
    centers.sort(key=lambda c: ang(c))
    print("  A2 corridor cells:", len(centers))
    if len(centers) == 8:
        start = min(range(8), key=lambda i: abs(((ang(centers[i])-90)+180)%360-180))
        for k in range(8):
            c = centers[(start+k) % 8]
            ipa(d, c[0]*S, c[1]*S-92, DIPH[k], 40, BLUE, chipbg=True)
    else:
        print("  !! corridor count != 8, skip diphthong labels")
    # 轴标签(四边形四边)
    ipa(d, 760*S, 338*S, "高", 40, INK, chipbg=True)
    ipa(d, 760*S, 686*S, "低", 40, INK, chipbg=True)
    ipa(d, 578*S, 511*S, "前", 40, INK, chipbg=True)
    ipa(d, 942*S, 511*S, "后", 40, INK, chipbg=True)
    # 标题注释
    txt(d, 1280, 56, "元音城堡 · 20 位元音精灵", 72, DRED)
    txt(d, 1280, 1546, "单元音住四边形宫殿 · 双元音走走廊滑梯", 44, INK, bold=False)
    for t, ny in [("鼻腔", 0.415), ("上颚", 0.475), ("舌面", 0.545), ("舌尖", 0.615)]:
        txt(d, 2560*0.072, 1600*ny, t, 36, INK, bold=False, chipbg=False)
    im.save(f"{OUT}/A2-元音城堡分区图_合成.png")
    print("A2 done")

# ---------------------------------------------------------------- A3
COLS = ["双唇", "唇齿", "齿间", "齿龈", "齿龈后·硬腭", "软腭", "声门"]
ROWS = ["爆破", "摩擦", "破擦", "鼻音", "舌侧", "半元音"]
# (row, col) -> ("ipa_left", "ipa_right", kind)  kind: split/single
MATRIX = {
    (0,0): ("p", "b", "split"), (0,3): ("t", "d", "split"), (0,5): ("k", "g", "split"),
    (1,1): ("f", "v", "split"), (1,2): ("θ", "ð", "split"), (1,3): ("s", "z", "split"),
    (1,4): ("ʃ", "ʒ", "split"), (1,6): ("h", "", "single_clear"),
    (2,4): ("tʃ", "dʒ", "split"),
    (3,0): ("m", "", "single_voiced"), (3,3): ("n", "", "single_voiced"), (3,5): ("ŋ", "", "single_voiced"),
    (4,3): ("l", "r", "pair_voiced"),
    (5,0): ("w", "", "single_voiced"), (5,4): ("j", "", "single_voiced"),
}

def synth_a3():
    src = Image.open(f"{BASE}/A3-辅音王国分区图.png").convert("RGB")
    S = 2560/src.size[0]
    im = src.resize((2560, 1600), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    # 标准矩阵面板(源坐标 345-1195 × 196-830)
    px0, py0, px1, py1 = 345*S, 196*S, 1195*S, 830*S
    d.rounded_rectangle([px0, py0, px1, py1], radius=14, fill=(233, 216, 180, 242),
                        outline=INK, width=5)
    cw = (px1-px0)/7; rh = (py1-py0)/6
    for i in range(1, 7):
        d.line([(px0+cw*i, py0), (px0+cw*i, py1)], fill=INK, width=3)
    for j in range(1, 6):
        d.line([(px0, py0+rh*j), (px1, py0+rh*j)], fill=INK, width=3)
    # 轴标签
    for i, c in enumerate(COLS):
        txt(d, px0+cw*(i+0.5), py0-52, c, 40, INK, bold=False)
    for j, r in enumerate(ROWS):
        txt(d, px0-140, py0+rh*(j+0.5), r, 40, INK, bold=False)
    # 格内容
    for (j, i), (a, b, kind) in MATRIX.items():
        ccx = px0+cw*(i+0.5); ccy = py0+rh*(j+0.5)
        if kind == "split":
            ipa(d, ccx-cw*0.20, ccy-rh*0.24, a, 44, RED)
            ipa(d, ccx+cw*0.20, ccy-rh*0.24, b, 44, GREEN)
            diamond_split(d, ccx, ccy+rh*0.16, 34)
        elif kind == "pair_voiced":
            ipa(d, ccx-cw*0.20, ccy-rh*0.24, a, 44, GREEN)
            ipa(d, ccx+cw*0.20, ccy-rh*0.24, b, 44, GREEN)
            diamond(d, ccx, ccy+rh*0.16, 32, GREEN)
        else:
            color = RED if kind == "single_clear" else GREEN
            ipa(d, ccx, ccy-rh*0.24, a, 44, color)
            diamond(d, ccx, ccy+rh*0.16, 32, color)
    # 四兄弟横条标签
    strip_cy = 880*S
    for k, s in enumerate(["/tr/", "/dr/", "/ts/", "/dz/"]):
        ipa(d, (345+119*(k+0.5))*S, strip_cy, s, 42, DRED)
    txt(d, 1280, 56, "辅音王国 · 28 位辅音精灵", 72, DRED)
    txt(d, 1280, 1546, "清浊成对：左红右绿 · 中间声带波纹", 44, INK, bold=False)
    im.save(f"{OUT}/A3-辅音王国分区图_合成.png")
    print("A3 done")

if __name__ == "__main__":
    synth_a2()
    synth_a3()
    print("DONE")
