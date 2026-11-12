# -*- coding: utf-8 -*-
"""A2/A3 合成修正版：几何反推 + 角度配对"""
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
BLUE = (46, 95, 138); DRED = (140, 64, 52); CHIP = (233, 216, 180, 215)

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

def ipa(d, cx, cy, s, size, fill=INK, chipbg=True):
    f = F(FONT_IPA, size)
    b = d.textbbox((0, 0), s, font=f); w, h = b[2]-b[0], b[3]-b[1]
    if chipbg: chip(d, cx, cy, w+size*0.5, h+size*0.45)
    d.text((cx-w/2-b[0], cy-h/2-b[1]), s, font=f, fill=fill)

def find_blobs(arr, rgb, tol=45, min_size=120, region=None, ds=4):
    H, W = arr.shape[:2]
    if region:
        x0, y0, x1, y1 = int(region[0]*W), int(region[1]*H), int(region[2]*W), int(region[3]*H)
        sub = arr[y0:y1, x0:x1]
    else:
        x0 = y0 = 0; sub = arr
    dist = np.abs(sub.astype(int) - np.array(rgb)).sum(axis=2)
    mask = dist < tol
    h, w = mask.shape
    h2, w2 = h//ds, w//ds
    m2 = mask[:h2*ds, :w2*ds].reshape(h2, ds, w2, ds).any(axis=(1, 3))
    lab = np.zeros((h2, w2), dtype=int); blobs = []; cur = 0
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
                    blobs.append((x0+sx/size*ds, y0+sy/size*ds, size*ds*ds))
    return blobs

# ---------------------------------------------------------------- A2
# 绘制版四边形 4+3+2+3 行排列 -> 行主序硬匹配
VOWEL_ROWS = [
    ["/iː/", "/ɪ/", "/uː/", "/ʊ/"],
    ["/e/", "/ɜː/", "/ɔː/"],
    ["/æ/", "/ə/"],
    ["/ʌ/", "/ɑː/", "/ɒ/"],
]
DIPH = ["/eɪ/", "/aɪ/", "/ɔɪ/", "/əʊ/", "/aʊ/", "/ɪə/", "/eə/", "/ʊə/"]

def synth_a2():
    src = Image.open(f"{BASE}/A2-元音城堡分区图.png").convert("RGB")
    im = src.resize((2560, 1600), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    W, H = im.size; sx, sy = W/src.size[0], H/src.size[1]
    arr = np.array(src)
    # 四边形内 12 宝石
    gems = []
    for rgb in (RED, BLUE):
        gems += find_blobs(arr, rgb, region=(0.30, 0.22, 0.70, 0.72), min_size=200)
    # 按 y 分行
    gems.sort(key=lambda g: g[1])
    rows = []
    for g in gems:
        if rows and abs(g[1] - np.mean([r[1] for r in rows[-1]])) < 40:
            rows[-1].append(g)
        else:
            rows.append([g])
    print("  A2 rows:", [len(r) for r in rows])
    names_flat = []
    for r in rows:
        r.sort(key=lambda g: g[0])
    for ri, r in enumerate(rows):
        for g in r:
            names_flat.append(VOWEL_ROWS[ri].pop(0) if ri < len(VOWEL_ROWS) and VOWEL_ROWS[ri] else "?")
    # 四边形范围
    xs = [g[0] for g in gems]; ys = [g[1] for g in gems]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    # 轴标签
    ipa(d, ((x0+x1)/2)*sx, (y0-52)*sy, "高", 30, INK, chipbg=False)
    ipa(d, ((x0+x1)/2)*sx, (y1+52)*sy, "低", 30, INK, chipbg=False)
    ipa(d, (x0-58)*sx, ((y0+y1)/2)*sy, "前", 30, INK, chipbg=False)
    ipa(d, (x1+58)*sx, ((y0+y1)/2)*sy, "后", 30, INK, chipbg=False)
    # 宝石下方贴音标
    for g, nm in zip(gems, names_flat):
        if nm != "?":
            ipa(d, g[0]*sx, g[1]*sy+46, nm, 34, INK)
    # 走廊 8 格：四边形外、城堡内的彩色 blob，按角度聚类
    cx, cy = src.size[0]*0.5, src.size[1]*0.47
    qrad = max(x1-x0, y1-y0)*0.62
    ring = []
    for rgb in (RED, BLUE, GREEN):
        for b in find_blobs(arr, rgb, region=(0.05, 0.08, 0.95, 0.92), min_size=140):
            r = math.hypot(b[0]-cx, b[1]-cy)
            if qrad < r < 430 and not (x0-30 < b[0] < x1+30 and y0-30 < b[1] < y1+30):
                ring.append(b)
    # 按角度聚类(相距25°内合一)
    def ang(b): return math.degrees(math.atan2(-(b[1]-cy), b[0]-cx)) % 360
    ring.sort(key=ang)
    groups = []
    for b in ring:
        if groups and abs(((ang(b)-ang(groups[-1][0]))+180)%360-180) < 25:
            groups[-1].append(b)
        else:
            groups.append([b])
    centers = []
    for gp in groups:
        gx = np.mean([b[0] for b in gp]); gy = np.mean([b[1] for b in gp])
        centers.append((gx, gy, ang((gx, gy))))
    centers.sort(key=lambda c: c[2])
    print("  A2 corridor clusters:", [(round(c[0]), round(c[1]), round(c[2])) for c in centers])
    # 从最接近顶部的簇开始顺时针配对
    if centers:
        start = min(range(len(centers)), key=lambda i: abs(((centers[i][2]-90)+180)%360-180))
        order = [centers[(start+k) % len(centers)] for k in range(len(centers))]
        for k, c in enumerate(order[:8]):
            ipa(d, c[0]*sx, c[1]*sy-56, DIPH[k], 32, BLUE)
    # 标题注释
    txt(d, W*0.5, H*0.035, "元音城堡 · 20 位元音精灵", 46, DRED)
    txt(d, W*0.5, H*0.962, "单元音住四边形宫殿 · 双元音走走廊滑梯", 28, INK, bold=False)
    for t, ny in [("鼻腔", 0.415), ("上颚", 0.475), ("舌面", 0.545), ("舌尖", 0.615)]:
        txt(d, W*0.072, H*ny, t, 22, INK, bold=False, chipbg=False)
    im.save(f"{OUT}/A2-元音城堡分区图_合成.png")
    print("A2 done, monophthongs:", names_flat)

# ---------------------------------------------------------------- A3
COLS = ["双唇", "唇齿", "齿间", "齿龈", "齿龈后·硬腭", "软腭", "声门"]
ROWS = ["爆破", "摩擦", "破擦", "鼻音", "舌侧", "半元音"]
MATRIX = {
    (0,0): ("p","b"), (0,3): ("t","d"), (0,5): ("k","g"),
    (1,1): ("f","v"), (1,2): ("θ","ð"), (1,3): ("s","z"), (1,4): ("ʃ","ʒ"), (1,6): ("h",""),
    (2,4): ("tʃ","dʒ"),
    (3,0): ("m",""), (3,3): ("n",""), (3,5): ("ŋ",""),
    (4,3): ("l","r"),
    (5,0): ("w",""), (5,4): ("j",""),
}

def synth_a3():
    src = Image.open(f"{BASE}/A3-辅音王国分区图.png").convert("RGB")
    im = src.resize((2560, 1600), Image.LANCZOS)
    d = ImageDraw.Draw(im, "RGBA")
    W, H = im.size; sx, sy = W/src.size[0], H/src.size[1]
    arr = np.array(src)
    # 矩阵内宝石格(9个已知格位) -> 反推网格
    gems = []
    for rgb in (RED, BLUE, GREEN):
        gems += find_blobs(arr, rgb, region=(0.24, 0.12, 0.76, 0.78), min_size=140)
    # 只保留成对分裂格与单色格(矩阵内的宝石是菱形/半半分裂)
    print("  A3 raw gem blobs:", len(gems), [(round(g[0]), round(g[1])) for g in gems])
    xs = sorted(g[0] for g in gems); ys = sorted(g[1] for g in gems)
    # x 聚类 -> 列(应有 4 组: col 0,3,4,5)
    def cluster(vals, gap=30):
        out = [[vals[0]]]
        for v in vals[1:]:
            if v - out[-1][-1] <= gap: out[-1].append(v)
            else: out.append([v])
        return [float(np.mean(g)) for g in out]
    xc = cluster(xs); yc = cluster(ys)
    print("  A3 x clusters:", [round(v) for v in xc], " y clusters:", [round(v) for v in yc])
    # 用宝石格位拟合: 已知 col 索引 [0,3,4,5], row 索引 [0,2,3,5](按 y 排序的簇数可能为4)
    # 直接用最小二乘拟合 col_idx->x, row_idx->y
    col_idx = [0, 3, 4, 5][:len(xc)]
    row_idx = [0, 2, 3, 5][:len(yc)]
    if len(xc) >= 2:
        ax, bx = np.polyfit(col_idx, xc, 1)
    else:
        ax, bx = src.size[0]/7, src.size[0]*0.27
    if len(yc) >= 2:
        ay, by = np.polyfit(row_idx, yc, 1)
    else:
        ay, by = src.size[1]/6, src.size[1]*0.15
    print("  A3 fit: ax=%.1f bx=%.1f ay=%.1f by=%.1f" % (ax, bx, ay, by))
    def cell_cx(i): return (ax*i + bx + ax/2) * sx
    def cell_cy(j): return (ay*j + by + ay/2) * sy
    # 轴标签
    for i, c in enumerate(COLS):
        txt(d, cell_cx(i), (by-42)*sy, c, 26, INK, bold=False)
    for j, r in enumerate(ROWS):
        txt(d, (bx-80)*sx, cell_cy(j), r, 26, INK, bold=False)
    # 格内音标(格子上部,避开中央图标)
    for (j, i), (a, b) in MATRIX.items():
        cxm, cym = cell_cx(i), cell_cy(j)
        if b:
            ipa(d, cxm - ax*sx*0.21, cym - ay*sy*0.26, a, 32, RED, chipbg=False)
            ipa(d, cxm + ax*sx*0.21, cym - ay*sy*0.26, b, 32, GREEN, chipbg=False)
        else:
            ipa(d, cxm, cym - ay*sy*0.28, a, 32, INK, chipbg=False)
    # 四兄弟横条(矩阵下方)
    for k, s in enumerate(["/tr/", "/dr/", "/ts/", "/dz/"]):
        ipa(d, cell_cx(k) + (cell_cx(6)-cell_cx(0))/6*0.0, (by + 6*ay + 60)*sy, s, 32, DRED)
    txt(d, W*0.5, H*0.035, "辅音王国 · 28 位辅音精灵", 46, DRED)
    txt(d, W*0.5, H*0.955, "清浊成对：左红右绿 · 中间声带波纹", 28, INK, bold=False)
    im.save(f"{OUT}/A3-辅音王国分区图_合成.png")
    print("A3 done")

if __name__ == "__main__":
    synth_a2()
    synth_a3()
    print("DONE")
