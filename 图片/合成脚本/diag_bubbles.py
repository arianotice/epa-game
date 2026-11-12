# -*- coding: utf-8 -*-
"""检测 24 张 B 图的气泡位置（长水平墨线配对）"""
import numpy as np
from PIL import Image
import os

BASE = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/定稿"
INK = np.array([35, 54, 78])

def detect_bubbles(path):
    arr = np.array(Image.open(path).convert("RGB"))
    H, W = arr.shape[:2]
    y_lo, y_hi = int(0.60*H), int(0.93*H)
    x_lo, x_hi = int(0.05*W), int(0.95*W)
    band = arr[y_lo:y_hi, x_lo:x_hi]
    dark = np.abs(band.astype(int) - INK).sum(axis=2) < 170
    edges = []
    for yy in range(dark.shape[0]):
        row = dark[yy]; xx = 0; rw = len(row)
        while xx < rw:
            if row[xx]:
                x0 = xx
                while xx < rw and row[xx]: xx += 1
                ln = xx - x0
                if 180 <= ln <= 450:
                    edges.append((x0+x_lo, yy+y_lo, ln))
            else:
                xx += 1
    pairs = []
    for i in range(len(edges)):
        for j in range(i+1, len(edges)):
            a, b = edges[i], edges[j]
            cxa, cxb = a[0]+a[2]/2, b[0]+b[2]/2
            dy = abs(a[1]-b[1])
            if abs(cxa-cxb) < 60 and 50 < dy < 130:
                pairs.append(((cxa+cxb)/2, (a[1]+b[1])/2))
    # 聚类去重
    out = []
    for cx, cy in pairs:
        if all((cx-ox)**2 + (cy-oy)**2 > 120**2 for ox, oy in out):
            out.append((cx, cy))
    out.sort()
    return out

files = sorted(f for f in os.listdir(BASE) if f.startswith("B") and f.endswith(".png"))
for f in files:
    bs = detect_bubbles(os.path.join(BASE, f))
    print(f"{f[:28]:30s} -> " + "  ".join(f"({int(cx)},{int(cy)})" for cx, cy in bs))
