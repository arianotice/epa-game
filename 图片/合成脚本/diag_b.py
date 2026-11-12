# -*- coding: utf-8 -*-
"""B 系列合成前诊断：1) B02 徽章宝石点检测 2) B25 中央菱形区放大"""
from PIL import Image
import numpy as np
from collections import deque

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"
INK = (35, 54, 78); RED = (176, 58, 46); GREEN = (46, 125, 91); BLUE = (46, 95, 138)

def blobs(arr, rgb, tol=60, min_size=40, region=None, ds=3):
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
                    out.append((x0+sx/size*ds, y0+sy/size*ds, size*ds*ds))
    return out

# --- B02 宝石检测（1536x864）---
a2 = np.array(Image.open(f"{BASE}/B02-阳光农场_iː-vs-ɪ.png").convert("RGB"))
print("B02 size:", a2.shape)
gems = []
for rgb, nm in ((RED,"红"), (BLUE,"蓝"), (GREEN,"绿")):
    for b in blobs(a2, rgb, region=(0.12, 0.14, 0.88, 0.46), min_size=60):
        gems.append((nm, round(b[0]), round(b[1]), b[2]))
for g in sorted(gems, key=lambda t: (t[2], t[1])):
    print("  gem", g)

# --- B25 中央菱形区放大（top-center diamond + surroundings）---
b25 = Image.open(f"{BASE}/B25-火车站_四宫格特例.png").convert("RGB")
print("B25 size:", b25.size)
# 上排中央菱形区: x 0.30-0.56W, y 0.18-0.34H
c1 = b25.crop((int(0.30*1536), int(0.18*864), int(0.56*1536), int(0.34*864))).resize((900, 500), Image.LANCZOS)
# 上排左剖面上方（候选徽章位）: x 0.10-0.30W, y 0.20-0.32H
c2 = b25.crop((int(0.10*1536), int(0.20*864), int(0.30*1536), int(0.32*864))).resize((600, 360), Image.LANCZOS)
sheet = Image.new("RGB", (900, 880), (255, 255, 255))
sheet.paste(c1, (0, 0)); sheet.paste(c2, (0, 500))
sheet.save(r"C:/Users/86135/WorkBuddy/英语音标播客/图片/合成脚本/diag_b25.png")
print("diag_b25 saved")
