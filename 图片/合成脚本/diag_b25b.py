# -*- coding: utf-8 -*-
"""B25 精确定位：舌位色块检测 + 候选徽章区放大"""
from PIL import Image
import numpy as np
from collections import deque

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"
RED = (176, 58, 46); GREEN = (46, 125, 91); BLUE = (46, 95, 138)

def blobs(arr, rgb, tol=55, min_size=200, ds=3):
    dist = np.abs(arr.astype(int) - np.array(rgb)).sum(axis=2)
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
                if size >= max(8, min_size//(ds*ds)):
                    out.append((round(sx/size*ds), round(sy/size*ds), size*ds*ds))
    return out

b25 = np.array(Image.open(f"{BASE}/B25-火车站_四宫格特例.png").convert("RGB"))
print("== B25 舌位色块（面积>600）==")
for rgb, nm in ((RED,"红"), (GREEN,"绿"), (BLUE,"蓝")):
    for b in blobs(b25, rgb, min_size=600):
        print(f"  {nm} ({b[0]},{b[1]}) area={b[2]}")

# 四个候选徽章区放大拼图
im = Image.open(f"{BASE}/B25-火车站_四宫格特例.png").convert("RGB")
crops = {
    "TL": (int(0.10*1536), int(0.20*1536 and 0.22*864), int(0.32*1536), int(0.34*864)),
    "TR": (int(0.56*1536), int(0.22*864), int(0.80*1536), int(0.34*864)),
    "BL": (int(0.10*1536), int(0.50*864), int(0.32*1536), int(0.62*864)),
    "BR": (int(0.56*1536), int(0.50*864), int(0.80*1536), int(0.62*864)),
}
sheet = Image.new("RGB", (680, 760), (255, 255, 255))
pos = [(0,0),(340,0),(0,380),(340,380)]
for (k, box), p in zip(crops.items(), pos):
    c = im.crop(box).resize((340, 380), Image.LANCZOS)
    sheet.paste(c, p)
sheet.save(r"C:/Users/86135/WorkBuddy/英语音标播客/图片/合成脚本/diag_b25b.png")
print("diag_b25b saved")
