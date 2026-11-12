# -*- coding: utf-8 -*-
"""精确检测 24 张 B 图的气泡（顶边+底边配对）与横幅位置"""
from PIL import Image
import numpy as np
import os

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"

def analyze(path):
    im = np.array(Image.open(path).convert("RGB"))
    bright = im.sum(axis=2) / 3
    H, W = bright.shape
    dark = bright < 150
    # 收集所有长run（>100px）作为边线段
    segs = []  # (yc, xc, ln)
    for y in range(int(0.60*H), int(0.97*H)):
        row = dark[y]; xx = 0
        while xx < W:
            if row[xx]:
                x0 = xx
                while xx < W and row[xx]: xx += 1
                if xx - x0 > 100:
                    segs.append((y, (x0+xx)/2, xx-x0))
            else:
                xx += 1
    # 聚类：相邻行、x中心接近的run归为一组（气泡的一条边）
    groups = []
    for y, xc, ln in segs:
        for g in groups:
            if abs(g["yc"] - y) <= 4 and abs(g["xc"] - xc) < 70 and abs(g["ln"] - ln) < 90:
                g["ys"].append(y); g["xc"] = (g["xc"]*g["n"] + xc)/(g["n"]+1); g["n"] += 1
                g["ln"] = max(g["ln"], ln)
                break
        else:
            groups.append({"yc": y, "xc": xc, "ln": ln, "n": 1, "ys": [y]})
    edges = [(np.mean(g["ys"]), g["xc"], g["ln"]) for g in groups]
    # 气泡：两条边（顶/底），x中心接近、垂直间距50-150
    bubbles = []
    for i in range(len(edges)):
        for j in range(i+1, len(edges)):
            a, b = edges[i], edges[j]
            dy = abs(a[0] - b[0])
            if abs(a[1] - b[1]) < 60 and 50 < dy < 150:
                bubbles.append(((a[1]+b[1])/2, (a[0]+b[0])/2, dy))
    # 去重（中心距>150）
    out = []
    for cx, cy, dy in bubbles:
        if all((cx-ox)**2 + (cy-oy)**2 > 150**2 for ox, oy, _ in out):
            out.append((cx, cy, dy))
    out.sort()
    # 横幅：y>0.80H 的最宽run
    band = [(ln, yc) for yc, xc, ln in edges if yc > 0.80*H]
    band.sort(reverse=True)
    banner_y = band[0][1] if band else None
    return out, banner_y

files = sorted(f for f in os.listdir(BASE) if f.startswith("B") and f.endswith(".png"))
for f in files:
    bs, by = analyze(os.path.join(BASE, f))
    s = "  ".join(f"({int(cx)},{int(cy)},h{int(dy)})" for cx, cy, dy in bs)
    print(f"{f[:26]:28s} bubbles[{len(bs)}]: {s}   bannerY={int(by) if by else '-'}")
