# -*- coding: utf-8 -*-
"""音标精灵身份卡合成器（Pillow 精确合成文字，防 AI 乱码）。

- 每张卡：稀有度彩色边框 + 稀有度徽章 + 顶部美式 IPA 大字 + 英式小字角标 + 中央精灵立绘 + 底部名称/样例词
- 精灵本体不画文字；IPA 与中文一律这里精确合成
- 大字取 manifest 的 displayIpa（美式）；sym（英式）降级为 alias 小字角标（字号 34 <= 主符号 1/3）
- 六档总图小字统一取 displayIpa、不加角标（总图偏装饰，角标会挤版）
- alias 自带「图鉴 」前缀；「· 长音/短音」后缀由教学页渲染时另拼，不写进 alias
- 字体：IPA / 角标用 ARIALUNI（覆盖 ɛ ɑ ɔ ʊ ər 及「图鉴」等 CJK）；中文名用微软雅黑
"""
import json, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(HERE, "sprites")
# 美式重出专用输出目录：旧 cards/ 的 49 张英式基线保持原样不动，待主理人验收后原子替换。
OUT = os.path.join(HERE, "cards_american")
os.makedirs(OUT, exist_ok=True)

F = "C:/Windows/Fonts/"
def ft(name, size):
    return ImageFont.truetype(F + name, size)

def ipa_font(size):
    return ImageFont.truetype(F + "ARIALUNI.TTF", size)

RAR_META = {
    "P":   ("P",  "普通",    (0, 0, 0, 0), (150, 175, 205), (224, 236, 250)),
    "SR":  ("SR", "稀有",    (0, 0, 0, 0), (70, 160, 95),  (222, 244, 230)),
    "SAR": ("SAR","超凡",    (0, 0, 0, 0), (196, 154, 40), (255, 240, 200)),
    "HR":  ("HR", "英雄",    (0, 0, 0, 0), (200, 55, 55),  (252, 222, 222)),
    "SSR": ("SSR","传说",    (0, 0, 0, 0), (130, 66, 175), (238, 222, 255)),
    "UR":  ("UR", "神话",    (0, 0, 0, 0), (230, 150, 30), (255, 246, 224)),
}


def text_w(draw, txt, font):
    b = draw.textbbox((0, 0), txt, font=font)
    return b[2] - b[0]


def centered(draw, txt, font, cx, y, fill):
    w = text_w(draw, txt, font)
    draw.text((cx - w / 2, y), txt, font=font, fill=fill)


def draw_card(canvas, m, sprite, cw, ch, pad):
    rar = m["rarity"]
    _, cn, _, accent, tint = RAR_META[rar]
    d = ImageDraw.Draw(canvas)
    # 外框（稀有度色）+ 内衬
    d.rounded_rectangle([pad, pad, pad + cw - pad, pad + ch - pad], radius=22,
                        fill=tint, outline=accent, width=6)
    d.rounded_rectangle([pad + 10, pad + 10, pad + cw - pad - 10, pad + ch - pad - 10],
                       radius=16, outline=accent, width=2)
    x0, x1 = pad + 18, pad + cw - pad - 18
    y = pad + 26
    # 稀有度徽章（左上）
    bf = ft("arialbd.ttf", 26)
    bw = text_w(d, rar, bf) + 30
    d.rounded_rectangle([x0, y, x0 + bw, y + 40], 10, fill=accent)
    d.text((x0 + 15, y + 8), rar, font=bf, fill=(255, 255, 255))
    # 稀有度中文名（右上）
    nf = ft("msyhbd.ttc", 24)
    nw = text_w(d, cn + "精灵", nf)
    d.text((x1 - nw, y + 8), cn + "精灵", font=nf, fill=accent)
    y += 56
    # 顶部 IPA 符号（大字，美式 displayIpa，稀有度色）
    sym = m["displayIpa"]
    # 视觉一致性判定（美式重出）：15 个多字符 displayIpa 在 128 号下最宽仅 142px，
    # 远小于卡片可用宽 376px，两档缩放已无防溢出意义；且 112/128 的 ascender 差
    # 17px 会让同一 y 下大字基线跳动。故统一 128 号，基线随同字号天然对齐。
    sf = ipa_font(128)
    cx = x0 + (x1 - x0) / 2
    centered(d, sym, sf, cx, y, accent)
    # 英式小字角标：大字右下，字号 34 <= 主符号 1/3（128/3 = 42.7）
    # alias 自带「图鉴 」前缀（长音/短音后缀由教学页渲染时另拼，不写进 alias）
    alias = m["alias"]
    af = ipa_font(34)
    aw = text_w(d, alias, af)
    ax = min(x1 - aw, cx + text_w(d, sym, sf) / 2 + 12)
    d.text((ax, y + 78), alias, font=af, fill=(120, 105, 88))
    y += 122
    # 精灵立绘（中央）
    spr = Image.open(sprite).convert("RGBA")
    area_h = int(ch * 0.46)
    box_w = int(cw * 0.62)
    r = min(box_w, area_h) / max(spr.size)
    sp = spr.resize((max(1, int(spr.size[0] * r)), max(1, int(spr.size[1] * r))),
                    Image.LANCZOS)
    sx = x0 + ((x1 - x0) - sp.size[0]) // 2
    canvas.alpha_composite(sp, (sx, y + (area_h - sp.size[1]) // 2))
    y += area_h + 10
    # 名称（中文）
    name = m["name"]
    nnf = ft("msyhbd.ttc", 40)
    nw2 = text_w(d, name, nnf)
    centered(d, name, nnf, x0 + (x1 - x0) / 2, y, (45, 35, 25))
    y += 56
    # 样例词（最多 3 个）
    wds = "  ·  ".join(m["words"][:3])
    wf = ft("arial.ttf", 22)
    centered(d, wds, wf, x0 + (x1 - x0) / 2, y, (110, 95, 75))
    return canvas


def make_overview(units, cw=460, ch=640, cols=2, pad=24, gap=30):
    """多张卡拼网格总览，输出 PNG。"""
    mf = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))
    rows = (len(units) + cols - 1) // cols
    W = cols * cw + (cols + 1) * gap
    H = rows * ch + (rows + 1) * gap
    canvas = Image.new("RGBA", (W, H), (245, 240, 230, 255))
    for i, u in enumerate(units):
        r, c = divmod(i, cols)
        ox, oy = gap + c * (cw + gap), gap + r * (ch + gap)
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        draw_card(card, mf[u], os.path.join(SPR, f"{u}.png"), cw, ch, pad)
        canvas.alpha_composite(card, (ox, oy))
    p = os.path.join(OUT, "sample_overview.png")
    canvas.convert("RGB").save(p, "PNG")
    return p


def make_all_cards(cw=460, ch=640):
    """出满 48 张单卡（供图鉴逐张展示），输出 cards_american/U01.png ..."""
    mf = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))
    done = 0
    for u in mf:
        spr = os.path.join(SPR, f"{u}.png")
        if not os.path.exists(spr):
            continue
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        draw_card(card, mf[u], spr, cw, ch, 24)
        card.convert("RGB").save(os.path.join(OUT, f"{u}.png"), "PNG")
        done += 1
    print(f"all cards: {done}/48 -> {OUT}")
    return done


def make_progress():
    """六档稀有度进阶总览图：P→SR→SAR→HR→SSR→UR 从左到右，体现赛事解锁进阶。"""
    mf = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))
    tiers = ["P", "SR", "SAR", "HR", "SSR", "UR"]
    per = {}
    for u, m in mf.items():
        per.setdefault(m["rarity"], []).append(u)

    row_pad, gap, tier_w, tier_h = 40, 28, 420, 300
    W = row_pad * 2 + 6 * tier_w + 5 * gap
    title_h = 120
    H = title_h + tier_h + 70
    canvas = Image.new("RGBA", (W, H), (250, 246, 238, 255))
    d = ImageDraw.Draw(canvas)
    # 标题
    tf = ft("msyhbd.ttc", 40)
    centered(d, "音标精灵 · 稀有度进阶图鉴", tf, W // 2, 34, (60, 45, 30))
    # 22 号字形底 = y+27；y=85 时与上方 40 号标题、下方档卡顶(y=120)各留约 8px，避免贴边
    centered(d, "从 P 到 UR · 在不同赛事地图的卡丁车比赛中解锁全部 48 只音标精灵 →",
             ft("msyh.ttc", 22), W // 2, 85, (120, 105, 85))
    for i, t in enumerate(tiers):
        _, cn, _, accent, tint = RAR_META[t]
        x = row_pad + i * (tier_w + gap)
        y = title_h
        # 档卡背景
        d.rounded_rectangle([x, y, x + tier_w, y + tier_h], 18, fill=tint, outline=accent, width=5)
        # 档徽章 + 数量
        bf = ft("arialbd.ttf", 34)
        d.rounded_rectangle([x + 18, y + 18, x + 18 + text_w(d, t, bf) + 26, y + 62], 10, fill=accent)
        d.text((x + 31, y + 24), t, font=bf, fill=(255, 255, 255))
        cntf = ft("msyhbd.ttc", 26)
        cnt = f"{cn} · {len(per[t])}只"
        d.text((x + tier_w - 18 - text_w(d, cnt, cntf), y + 30), cnt, font=cntf, fill=accent)
        # 该档前 3 只精灵立绘横排（缺图则跳过该位，48 到齐后自动补全）
        reps = [u for u in per[t][:3] if os.path.exists(os.path.join(SPR, f"{u}.png"))]
        slot_u = [u for u in per[t][:3] if not os.path.exists(os.path.join(SPR, f"{u}.png"))]
        spr_w = int((tier_w - 60) / max(3, len(reps) + len(slot_u)))
        for j, u in enumerate(reps + slot_u):
            spath = os.path.join(SPR, f"{u}.png")
            if not os.path.exists(spath):
                bx = x + 30 + j * spr_w
                d.ellipse([bx + 4, y + 110 + spr_w - 4 - 30, bx + spr_w - 4, y + 110 + spr_w - 4],
                          outline=(200, 190, 175), width=2)  # 预留虚位（未生成）
                centered(d, "?", ipa_font(34), bx + spr_w // 2, y + 110 + spr_w // 2 - 24, (200, 190, 175))
                continue
            sp = Image.open(spath).convert("RGBA")
            r = (spr_w - 6) / max(sp.size)
            sp = sp.resize((max(1, int(sp.size[0] * r)), max(1, int(sp.size[1] * r))), Image.LANCZOS)
            bx = x + 30 + j * spr_w
            canvas.alpha_composite(sp, (bx, y + 84 + (spr_w - sp.size[1])))
            # 音标符号（六档总图：统一美式小字 displayIpa，不加英式角标）
            sf = ipa_font(30)
            centered(d, mf[u]["displayIpa"], sf, bx + sp.size[0] // 2, y + 74, accent)
        # 满档提示（固定在档卡底部，避免被精灵光环遮住）
        more = len(per[t]) - len(reps)
        if more > 0:
            centered(d, f"该档共 {len(per[t])} 只 · 展示前 3", ft("msyh.ttc", 18),
                     x + tier_w // 2, y + tier_h - 72, (150, 138, 120))
        # 档位描述
        desc = {"P": "基础音·易解锁", "SR": "常见辅元音", "SAR": "进阶长音",
                "HR": "英雄音·少出现", "SSR": "传说音·难辨", "UR": "神话音·最稀有"}[t]
        d.text((x + 18, y + tier_h - 44), desc, font=ft("msyh.ttc", 20), fill=(90, 78, 62))
        # 箭头
        if i < 5:
            ay = y + tier_h // 2
            d.polygon([(x + tier_w + 4, ay - 14), (x + tier_w + 4, ay + 14),
                       (x + tier_w + gap - 4, ay)], fill=(150, 135, 115))
    p = os.path.join(OUT, "rarity_progress.png")
    canvas.convert("RGB").save(p, "PNG")
    print("progress ->", p)
    return p


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "overview"
    if cmd == "overview":
        units = sys.argv[2].split(",") if len(sys.argv) > 2 else "U01,U21,U13,U17,U33,U41".split(",")
        print("overview ->", make_overview(units))
    elif cmd == "all":
        make_all_cards()
    elif cmd == "progress":
        make_progress()
    else:
        print("usage: compose_cards.py [overview U01,U05|all|progress]")
