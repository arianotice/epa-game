# -*- coding: utf-8 -*-
"""诊断2：A2 三色全检 + A3 宽区网格线"""
import numpy as np
from PIL import Image
from collections import deque

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"
RED = (176, 58, 46); BLUE = (46, 95, 138); GREEN = (46, 125, 91)

def blobs(arr, rgb, tol=45, min_size=150, region=None, ds=4):
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
                    out.append((round(x0+sx/size*ds), round(y0+sy/size*ds), size*ds*ds))
    return out

# A2 全色检测
arr2 = np.array(Image.open(f"{BASE}/A2-元音城堡分区图.png").convert("RGB"))
allg = []
for c, nm in [(RED, "R"), (BLUE, "B"), (GREEN, "G")]:
    for b in blobs(arr2, c, region=(0.28, 0.20, 0.72, 0.74), min_size=150):
        allg.append((b[0], b[1], nm, b[2]))
allg.sort(key=lambda g: (g[1], g[0]))
print("== A2 quad all-color blobs (%d) ==" % len(allg))
for g in allg:
    print("   (%d, %d) %s size=%d" % g)

# A3 宽区垂直线
arr3 = np.array(Image.open(f"{BASE}/A3-辅音王国分区图.png").convert("RGB"))
gray = arr3.mean(axis=2); dark = gray < 130
H, W = dark.shape
rx0, rx1, ry0, ry1 = int(W*0.08), int(W*0.92), int(H*0.18), int(H*0.80)
sub = dark[ry0:ry1, rx0:rx1]
colsum = sub.sum(axis=0); rw = rx1-rx0
# 连续峰合并
peaks = []
i = 0
cols = colsum
while i < len(cols):
    if cols[i] > rw*0.35:
        j = i
        while j < len(cols) and cols[j] > rw*0.35: j += 1
        seg = cols[i:j]
        pk = i + int(np.argmax(seg))
        peaks.append((rx0+pk, int(seg.max())))
        i = j
    else:
        i += 1
print("== A3 vline peaks (wide region) ==")
print(peaks)
rowsum = sub.sum(axis=1)
peaks2 = []
i = 0
while i < len(rowsum):
    if rowsum[i] > rw*0.35:
        j = i
        while j < len(rowsum) and rowsum[j] > rw*0.35: j += 1
        seg = rowsum[i:j]
        pk = i + int(np.argmax(seg))
        peaks2.append((ry0+pk, int(seg.max())))
        i = j
    else:
        i += 1
print("== A3 hline peaks (wide region) ==")
print(peaks2)
