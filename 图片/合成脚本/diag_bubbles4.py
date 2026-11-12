# -*- coding: utf-8 -*-
"""V4 气泡检测：连通域分析（描边围合的孤立内部区域）"""
from PIL import Image
import numpy as np
from collections import deque
import os

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"

def bubble_interiors(path, y0f=0.60, y1f=0.90, thr=168):
    im = np.array(Image.open(path).convert("RGB"))
    bright = im.sum(axis=2) / 3
    H, W = bright.shape
    y0, y1 = int(y0f*H), int(y1f*H)
    free = bright[y0:y1, :] >= thr          # 非暗 = 可通过
    h, w = free.shape
    lab = np.zeros((h, w), dtype=int)
    comps = []
    cur = 0
    for yy in range(h):
        for xx in range(w):
            if free[yy, xx] and lab[yy, xx] == 0:
                cur += 1
                q = deque([(yy, xx)]); lab[yy, xx] = cur
                size = 0; x0 = x1 = xx; ytop = ybot = yy
                while q:
                    cy, cx = q.popleft(); size += 1
                    x0 = min(x0, cx); x1 = max(x1, cx)
                    ytop = min(ytop, cy); ybot = max(ybot, cy)
                    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny, nx = cy+dy, cx+dx
                        if 0 <= ny < h and 0 <= nx < w and free[ny, nx] and lab[ny, nx] == 0:
                            lab[ny, nx] = cur; q.append((ny, nx))
                bw, bh = x1-x0+1, ybot-ytop+1
                comps.append((x0, ytop+y0, bw, bh, size))
    # 气泡：宽170-340、高55-125、填充率>0.68
    out = []
    for x0, yt, bw, bh, size in comps:
        if 165 <= bw <= 345 and 50 <= bh <= 130 and size / (bw*bh) > 0.68:
            out.append((x0 + bw/2, yt + bh/2, bw, bh))
    out.sort()
    return out

files = sorted(f for f in os.listdir(BASE) if f.startswith("B") and f.endswith(".png"))
for f in files:
    bs = bubble_interiors(os.path.join(BASE, f))
    s = "  ".join(f"({int(cx)},{int(cy)} {bw}x{bh})" for cx, cy, bw, bh in bs)
    print(f"{f[:26]:28s} [{len(bs)}] {s}")
