# -*- coding: utf-8 -*-
"""将 29 张成稿 PNG 转为 WebP，并生成 favicon。"""
import os
from PIL import Image

SRC = r"C:/Users/86135/WorkBuddy/英语音标播客/图片/成稿"
DST = r"C:/Users/86135/WorkBuddy/英语音标播客/音标大闯关/assets/img"
os.makedirs(DST, exist_ok=True)

# 文件名 -> (输出名, 目标宽度)
PLAN = {"A1": ("a1", 1920), "A2": ("a2", 1920), "A3": ("a3", 1920), "F": ("f", 1600), "封面": ("cover", 1200)}

def save_webp(im, path, q=82):
    im.save(path, "WEBP", quality=q, method=6)

total_in = total_out = 0
for f in sorted(os.listdir(SRC)):
    if not f.endswith(".png"):
        continue
    key = f.split("-")[0]
    if key.startswith("B"):
        out_name, w = f.split("-")[0].lower(), 1600
    elif key in PLAN:
        out_name, w = PLAN[key]
    else:
        print("跳过:", f); continue
    src = os.path.join(SRC, f)
    im = Image.open(src).convert("RGB")
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    out = os.path.join(DST, out_name + ".webp")
    save_webp(im, out)
    si, so = os.path.getsize(src), os.path.getsize(out)
    total_in += si; total_out += so
    print(f"{out_name}.webp  {im.width}x{im.height}  {si/1048576:.2f}MB -> {so/1024:.0f}KB")

# favicon：由方形封面缩放到 256 PNG
cover = Image.open(os.path.join(SRC, "封面-方形_合成.png")).convert("RGB").resize((256, 256), Image.LANCZOS)
cover.save(os.path.join(DST, "favicon.png"), "PNG")
print("favicon.png 256x256 完成")
print(f"总计: {total_in/1048576:.1f}MB -> {total_out/1048576:.1f}MB")
