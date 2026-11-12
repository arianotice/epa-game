# -*- coding: utf-8 -*-
"""V5 气泡检测：闭运算封缝 + 连通域（不设容量上限，泄漏区自然变大被滤除）"""
from PIL import Image
import numpy as np
from collections import deque
import os

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"

def bubble_interiors(path, y0f=0.58, y1f=0.92, thr=170):
    im = np.array(Image.open(path).convert("RGB"))
    bright = im.sum(axis=2) / 3
    H, W = bright.shape
    y0, y1 = int(y0f*H), int(y1f*H)
    wall = bright[y0:y1, :] < thr
    # 闭运算：膨胀1再腐蚀1（封1-2px缝隙）
    def dilate(m):
        r = m.copy()
        r[1:, :] |= m[:-1, :]; r[:-1, :] |= m[1:, :]
        r[:, 1:] |= m[:, :-1]; r[:, :-1] |= m[:, 1:]
        return r
    def erode(m):
        r = m.copy()
        r[1:, :] &= m[:-1, :]; r[:-1, :] &= m[1:, :]
        r[:, 1:] &= m[:, :-1]; r[:, :-1] &= m[:, 1:]
        return r
    wall = erode(dilate(wall))
    free = ~wall
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
                    if cx < x0: x0 = cx
                    if cx > x1: x1 = cx
                    if cy < ytop: ytop = cy
                    if cy > ybot: ybot = cy
                    for dy, dx in ((1,0),(-1,0),(0,1),(0,-1)):
                        ny, nx = cy+dy, cx+dx
                        if 0 <= ny < h and 0 <= nx < w and free[ny, nx] and lab[ny, nx] == 0:
                            lab[ny, nx] = cur; q.append((ny, nx))
                bw, bh = x1-x0+1, ybot-ytop+1
                comps.append((x0, ytop+y0, bw, bh, size))
    out = []
    for x0, yt, bw, bh, size in comps:
        if 160 <= bw <= 350 and 45 <= bh <= 140 and 8000 <= size <= 48000 and size/(bw*bh) > 0.6:
            out.append((x0 + bw/2, yt + bh/2, bw, bh))
    # 去重
    ded = []
    for c in sorted(out):
        if all((c[0]-d[0])**2 + (c[1]-d[1])**2 > 90**2 for d in ded):
            ded.append(c)
    ded.sort()
    return ded

files = sorted(f for f in os.listdir(BASE) if f.startswith("B") and f.endswith(".png"))
for f in files:
    bs = bubble_interiors(os.path.join(BASE, f))
    s = "  ".join(f"({int(cx)},{int(cy)} {bw}x{bh})" for cx, cy, bw, bh in bs)
    print(f"{f[:26]:28s} [{len(bs)}] {s}")
