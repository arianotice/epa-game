# -*- coding: utf-8 -*-
"""V3 气泡检测：垂直边框线配对（左右描边 → 气泡）"""
from PIL import Image
import numpy as np
import os

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"

def vsegments(path):
    im = np.array(Image.open(path).convert("RGB"))
    bright = im.sum(axis=2) / 3
    H, W = bright.shape
    dark = bright < 150
    y0, y1 = int(0.62*H), int(0.93*H)   # 气泡/横幅带
    segs = []  # (xc, ytop, ybot)
    for x in range(int(0.04*W), int(0.96*W)):
        col = dark[y0:y1, x]
        yy = 0; best = (0, 0, 0)
        while yy < len(col):
            if col[yy]:
                s = yy
                while yy < len(col) and col[yy]: yy += 1
                if yy - s > best[0]: best = (yy - s, s, yy)
            else:
                yy += 1
        if best[0] > 55:
            segs.append((x, y0 + best[1], y0 + best[2]))
    # 聚类相邻列为一条竖线
    lines = []
    for x, yt, yb in segs:
        for L in lines:
            if x - L["x"][-1] <= 3 and abs(yt - L["yt"]) < 25 and abs(yb - L["yb"]) < 25:
                L["x"].append(x); L["yt"] = min(L["yt"], yt); L["yb"] = max(L["yb"], yb)
                break
        else:
            lines.append({"x": [x], "yt": yt, "yb": yb})
    out = [(int(np.mean(L["x"])), L["yt"], L["yb"]) for L in lines]
    # 配对：左右竖线，水平距170-330，纵向范围重叠>60%
    bubbles = []
    for i in range(len(out)):
        for j in range(i+1, len(out)):
            a, b = out[i], out[j]
            dx = abs(a[0] - b[0])
            ov = min(a[2], b[2]) - max(a[1], b[1])
            hmin = min(a[2]-a[1], b[2]-b[1])
            if 170 < dx < 330 and ov > 0.6 * hmin and hmin > 55:
                bubbles.append(((a[0]+b[0])/2, (max(a[1], b[1]) + min(a[2], b[2]))/2, hmin))
    bubbles.sort()
    return bubbles

files = sorted(f for f in os.listdir(BASE) if f.startswith("B") and f.endswith(".png"))
for f in files:
    bs = vsegments(os.path.join(BASE, f))
    s = "  ".join(f"({int(cx)},{int(cy)},h{int(h)})" for cx, cy, h in bs)
    print(f"{f[:26]:28s} [{len(bs)}] {s}")
