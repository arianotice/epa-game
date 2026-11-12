# -*- coding: utf-8 -*-
"""诊断：A3 网格线轮廓 + A2 宝石分行"""
import numpy as np
from PIL import Image

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"

# ---- A3 网格诊断 ----
src = Image.open(f"{BASE}/A3-辅音王国分区图.png").convert("RGB")
arr = np.array(src)
gray = arr.mean(axis=2)
dark = gray < 130
H, W = dark.shape
print("A3 size:", W, H)
rx0, rx1, ry0, ry1 = int(W*0.24), int(W*0.76), int(H*0.10), int(H*0.85)
sub = dark[ry0:ry1, rx0:rx1]
colsum = sub.sum(axis=0); rowsum = sub.sum(axis=1)
rw = rx1 - rx0
print("== A3 垂直暗线候选(colsum > 0.20*rw) ==")
vs = [(rx0+i, int(v)) for i, v in enumerate(colsum) if v > rw*0.20]
print(vs)
print("== A3 水平暗线候选(rowsum > 0.20*rw) ==")
hs = [(ry0+i, int(v)) for i, v in enumerate(rowsum) if v > rw*0.20]
print(hs)

# ---- A2 宝石分行诊断 ----
from collections import deque
src2 = Image.open(f"{BASE}/A2-元音城堡分区图.png").convert("RGB")
arr2 = np.array(src2)
RED = (176, 58, 46); BLUE = (46, 95, 138); GREEN = (46, 125, 91)
def blobs(arr, rgb, tol=45, min_size=200, region=None, ds=4):
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

gems = []
for rgb in (RED, BLUE):
    gems += blobs(arr2, rgb, region=(0.30, 0.22, 0.70, 0.72), min_size=200)
gems.sort(key=lambda g: (g[1], g[0]))
print("== A2 quad gems (x,y,size) ==")
for g in gems:
    print("   (%d, %d, %d)" % g)
