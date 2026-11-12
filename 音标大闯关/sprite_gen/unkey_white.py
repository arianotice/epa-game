# -*- coding: utf-8 -*-
"""把 Agnes 出的白底精灵贴纸 -> 透明 PNG。

核心：浅色精灵（米白/奶油色）跟纯白背景同色，按“白色阈值”会误删本体。
改用 **连通域 flood-fill**：只有「与图片边缘连通的近白区域」判为背景并透明化；
精灵内部（被光晕/轮廓围住的独立连通块）即使很浅也整体保留。

依赖 scipy.ndimage（已装）。纯 Python，不碰 ffmpeg。

用法：
  python unkey_white.py                     # 处理 raw/U*.png -> sprites/
  python unkey_white.py --only U01,U05      # 指定
  python unkey_white.py --canvas 768        # 统一画布
  python unkey_white.py --white-lum 248 --white-sat 14 --feather 2
"""
import argparse, os, glob
from PIL import Image, ImageFilter
import numpy as np
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "sprites")


def key_white_flood(arr, white_lum, white_sat, feather):
    """返回 alpha (H,W)：与边缘连通的近白区域=0（透明），其余=255。"""
    r, g, b = arr[..., 0].astype(np.int32), arr[..., 1].astype(np.int32), arr[..., 2].astype(np.int32)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    sat = np.minimum.reduce([np.abs(r - g), np.abs(g - b), np.abs(r - b)])
    white = (lum > white_lum) & (sat < white_sat)          # “非常白”
    labels, _ = ndimage.label(white)                        # 近白连通块
    H, W = white.shape
    border = set(labels[0, :].tolist()) | set(labels[-1, :].tolist()) \
             | set(labels[:, 0].tolist()) | set(labels[:, -1].tolist())
    border.discard(0)
    bg = np.zeros((H, W), dtype=bool)
    if border:
        bg[np.isin(labels, list(border))] = True            # 只边缘连通的白 -> 背景
    alpha = np.where(bg, 0, 255).astype(np.uint8)
    if feather > 0:
        alpha = np.array(Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(feather)))
    return alpha


def crop_to_content(rgba, pad=12):
    a = np.array(rgba)[..., 3]
    ys, xs = np.where(a > 12)
    if len(xs) == 0:
        return rgba
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(a.shape[1] - 1, x1 + pad), min(a.shape[0] - 1, y1 + pad)
    return rgba.crop((x0, y0, x1 + 1, y1 + 1))


def center_on_canvas(img, canvas, fill=0.94):
    C = canvas
    im = img.convert("RGBA")
    scale = int(C * fill)
    iw, ih = im.size
    r = scale / max(iw, ih)
    if r < 1:
        im = im.resize((max(1, int(iw * r)), max(1, int(ih * r))), Image.LANCZOS)
    bg = Image.new("RGBA", (C, C), (0, 0, 0, 0))
    bg.paste(im, ((C - im.size[0]) // 2, (C - im.size[1]) // 2), im)
    return bg


def process(path, canvas, white_lum, white_sat, feather, fill):
    im = Image.open(path).convert("RGB")
    arr = np.array(im, dtype=np.int32)
    alpha = key_white_flood(arr, white_lum, white_sat, feather)
    rgba = im.convert("RGBA")
    rgba.putalpha(Image.fromarray(alpha, "L"))
    rgba = crop_to_content(rgba, pad=12)
    return center_on_canvas(rgba, canvas, fill)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="逗号分隔 unit，如 U01,U05")
    ap.add_argument("--canvas", type=int, default=768)
    ap.add_argument("--white-lum", type=int, default=248, help="背景白度判定（亮度下限）")
    ap.add_argument("--white-sat", type=int, default=14, help="背景白度判定（饱和度上限）")
    ap.add_argument("--feather", type=int, default=2)
    ap.add_argument("--fill", type=float, default=0.94, help="内容占画布比例")
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)
    if args.only:
        names = [f"{u.strip().upper()}.png" for u in args.only.split(",")]
        files = [os.path.join(RAW, n) for n in names if os.path.exists(os.path.join(RAW, n))]
        miss = [n for n in names if not os.path.exists(os.path.join(RAW, n))]
        if miss:
            print("缺少 raw:", miss)
    else:
        files = sorted(glob.glob(os.path.join(RAW, "U*.png")))
    print(f"处理 {len(files)} 张 -> {OUT} (canvas={args.canvas} lum={args.white_lum} sat={args.white_sat} feather={args.feather})")
    for f in files:
        base = os.path.basename(f)
        rgba = process(f, args.canvas, args.white_lum, args.white_sat, args.feather, args.fill)
        rgba.save(os.path.join(OUT, base))
        a = np.array(rgba)[..., 3]
        print(f"  {base}: opaque={float((a > 128).mean())*100:.1f}%")
    print(f"\n完成 {len(files)} 张透明精灵。")


if __name__ == "__main__":
    main()
