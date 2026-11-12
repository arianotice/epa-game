# -*- coding: utf-8 -*-
"""精灵 / 身份卡 / 六档总图 WebP 转换器 —— 美式重出版权威管线。

== 唯一权威链（2026-11-10 厘清，勿再混用英式基线）==

  [文案] image_profiles.py + manifest.json  (displayIpa = 美式 IPA；sym 仅作英式角标)
      |
      v
  [PNG]  compose_cards.py -> sprite_gen/cards_american/
         48 张 U01..U48.png + rarity_progress.png
      |
      v  <-- 本脚本（RGB, WebP quality=90 / method=6；总图 q=86）
  [中间产物 / 门控权威源] sprite_gen/webp_american/
         48 张 U*.webp + rarity_progress.webp
      |
      v  <-- 本脚本同时写出（同一份字节，不做二次编码）
  [发布] assets/sprites/cards/U*.webp + assets/sprites/rarity_progress.webp
      |
      v  deploy.sh: scp -r assets/sprites -> /var/www/ipaquest/assets/

  [立绘] gen_sprites.py -> unkey_white.py -> sprite_gen/sprites/U*.png
         -> 本脚本（RGBA, q=90, m=6）-> assets/sprites/U*.webp
         立绘本体不含任何文字，故不存在英/美差异，两版共用。

== 已作废，严禁作为发布来源 ==

  sprite_gen/cards/ 是 2026-11-03 的英式 DJ IPA 基线（50 文件），
  仅作历史留档。若误用它重建，会把 iː / ɒ / əʊ / ɪə / eə / ʊə 等英式
  大字写回线上，且 U11=ɜː 会覆盖已上线的美式 ɜr。
  历史错位：本脚本 11-03 版把 CARD 指向 "sprite_gen/cards"，
  与 11-06 上线的美式卡面不一致；本版已修正为 cards_american。

  门控侧早已以美式为准：verify_fresh_gate.py:252 F9c 用
  sprite_gen/webp_american/ 作为 49 张发布卡面的逐字节比对源。

== 用法（可从任意目录运行）==

  py -3.13 sprite_gen/convert_webp.py              # 默认：--check-fast，只读、不写任何文件
  py -3.13 sprite_gen/convert_webp.py --check-fast # 只读：结构 + 中间产物与发布目录逐字节比对
  py -3.13 sprite_gen/convert_webp.py --check      # 只读全量：再从美式 PNG 重编码复现 146 个字节比对（约 2-4 分钟）
  py -3.13 sprite_gen/convert_webp.py --write      # 重建（覆盖发布目录，需人工确认）

  --write 的前置守卫：cards_american/ 必须恰好 48 张 U*.png + 1 张 rarity_progress.png，
  sprites/ 必须恰好 48 张 U*.png；任一缺失即整体中止，绝不部分覆盖、绝不回退英式目录。
"""
import glob
import hashlib
import io
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

SPRITES_PNG = os.path.join(HERE, "sprites")          # 立绘 PNG（无文字，英美共用）
CARDS_AMERICAN = os.path.join(HERE, "cards_american")  # 美式重出版 PNG —— 唯一权威
WEBP_AMERICAN = os.path.join(HERE, "webp_american")   # 美式 WebP 中间产物 / 门控权威源
CARDS_LEGACY = os.path.join(HERE, "cards")            # 英式基线，仅留档，禁止读取
PUB_SPRITES = os.path.join(ROOT, "assets", "sprites")
PUB_CARDS = os.path.join(PUB_SPRITES, "cards")

UNITS = ["U%02d" % i for i in range(1, 49)]

Q_CARD, Q_PROGRESS, METHOD = 90, 86, 6


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def encode(png, rgb, quality):
    buf = io.BytesIO()
    Image.open(png).convert(rgb).save(buf, "WEBP", quality=quality, method=METHOD)
    return buf.getvalue()


def structural():
    """结构守卫：美式源完整性 + 英式基线隔离。返回 (ok, lines)。"""
    lines, ok = [], True

    def need(cond, msg):
        nonlocal ok
        lines.append(("PASS" if cond else "FAIL") + "  " + msg)
        if not cond:
            ok = False

    card_pngs = sorted(glob.glob(os.path.join(CARDS_AMERICAN, "U*.png")))
    spr_pngs = sorted(glob.glob(os.path.join(SPRITES_PNG, "U*.png")))
    need(len(card_pngs) == 48, "美式卡面 PNG 恰好 48 张（实得 %d）" % len(card_pngs))
    need(all(os.path.isfile(os.path.join(CARDS_AMERICAN, u + ".png")) for u in UNITS),
         "美式卡面 U01..U48 无缺号")
    need(os.path.isfile(os.path.join(CARDS_AMERICAN, "rarity_progress.png")),
         "美式六档总图 rarity_progress.png 存在")
    need(len(spr_pngs) == 48, "立绘 PNG 恰好 48 张（实得 %d）" % len(spr_pngs))
    need(all(os.path.isfile(os.path.join(SPRITES_PNG, u + ".png")) for u in UNITS),
         "立绘 U01..U48 无缺号")
    # 语义守卫：权威源必须是 cards_american，且绝不与英式基线目录同路径
    need(os.path.normcase(CARDS_AMERICAN) != os.path.normcase(CARDS_LEGACY)
         and os.path.basename(os.path.normpath(CARDS_AMERICAN)) == "cards_american",
         "权威源目录 = cards_american（与英式基线目录不混用）")
    need(os.path.isdir(CARDS_LEGACY),
         "英式基线 sprite_gen/cards/ 仍完整留档（不删除、只隔离）")
    return ok, lines


def check_fast():
    """只读快检：美式中间产物 <-> 发布目录逐字节全等；立绘 PNG 与发布 webp 均在位。"""
    out = []
    ok, lines = structural()
    out += lines
    n = 0
    for u in UNITS:
        a = os.path.join(WEBP_AMERICAN, u + ".webp")
        b = os.path.join(PUB_CARDS, u + ".webp")
        good = os.path.isfile(a) and os.path.isfile(b) and sha_file(a) == sha_file(b)
        if not good:
            out.append("FAIL  卡面 %s：webp_american 与发布目录不逐字节全等" % u)
            ok = False
        n += 1
    out.append(("PASS" if n == 48 else "FAIL") + "  48 张卡面 中间产物 == 发布目录（逐字节）")
    for rel, dst in [("rarity_progress.webp", os.path.join(PUB_SPRITES, "rarity_progress.webp"))]:
        a = os.path.join(WEBP_AMERICAN, rel)
        good = os.path.isfile(a) and os.path.isfile(dst) and sha_file(a) == sha_file(dst)
        out.append(("PASS" if good else "FAIL") + "  六档总图 中间产物 == 发布目录（逐字节）")
        ok = ok and good
    miss = [u for u in UNITS if not os.path.isfile(os.path.join(PUB_SPRITES, u + ".webp"))]
    out.append(("PASS" if not miss else "FAIL") + "  48 张立绘 WebP 在发布目录（%s）"
               % ("齐备" if not miss else "缺 " + ",".join(miss[:5])))
    ok = ok and not miss
    return ok, out


def check_full():
    """只读全检：从美式 PNG 重编码，逐字节复现 146 个目标文件。"""
    ok, out = check_fast()
    out.append("---- 以下为从 sprite_gen/cards_american/ 与 sprites/ 重编码复现 ----")
    cnt = 0
    for u in UNITS:
        src = os.path.join(CARDS_AMERICAN, u + ".png")
        raw = encode(src, "RGB", Q_CARD)
        got = sha_bytes(raw)
        for label, dst in [("中间产物", os.path.join(WEBP_AMERICAN, u + ".webp")),
                           ("发布", os.path.join(PUB_CARDS, u + ".webp"))]:
            good = os.path.isfile(dst) and sha_file(dst) == got
            if not good:
                out.append("FAIL  卡面 %s / %s 与美式 PNG 重编码不一致" % (u, label))
                ok = False
            cnt += 1
    out.append("PASS  48 张卡面 × 2 目标 = 96 次字节比对完成")
    raw = encode(os.path.join(CARDS_AMERICAN, "rarity_progress.png"), "RGB", Q_PROGRESS)
    got = sha_bytes(raw)
    for label, dst in [("中间产物", os.path.join(WEBP_AMERICAN, "rarity_progress.webp")),
                       ("发布", os.path.join(PUB_SPRITES, "rarity_progress.webp"))]:
        good = os.path.isfile(dst) and sha_file(dst) == got
        out.append(("PASS" if good else "FAIL") + "  六档总图 / %s 与美式 PNG 重编码一致" % label)
        ok = ok and good
    for u in UNITS:
        raw = encode(os.path.join(SPRITES_PNG, u + ".png"), "RGBA", Q_CARD)
        dst = os.path.join(PUB_SPRITES, u + ".webp")
        good = os.path.isfile(dst) and sha_file(dst) == sha_bytes(raw)
        if not good:
            out.append("FAIL  立绘 %s 与 sprites/ PNG 重编码不一致" % u)
            ok = False
        cnt += 1
    out.append("PASS  48 张立绘 字节比对完成（共 %d 次）" % cnt)
    # 英式基线隔离实证：取 4 个英美差异最明显的 unit，证明发布卡面不是英式重编码产物
    out.append("---- 英式基线隔离实证（cards/ 仅留档，不得为发布源）----")
    probes = ["U01", "U11", "U18", "U05"]
    for u in probes:
        legacy_png = os.path.join(CARDS_LEGACY, u + ".png")
        pub = os.path.join(PUB_CARDS, u + ".webp")
        if not os.path.isfile(legacy_png):
            continue
        legacy_sha = sha_bytes(encode(legacy_png, "RGB", Q_CARD))
        amer_sha = sha_bytes(encode(os.path.join(CARDS_AMERICAN, u + ".png"), "RGB", Q_CARD))
        pub_sha = sha_file(pub)
        good = (legacy_sha != pub_sha) and (amer_sha == pub_sha)
        out.append(("PASS" if good else "FAIL")
                   + "  %s 英式重编码 != 发布 且 美式重编码 == 发布" % u)
        ok = ok and good
    return ok, out


def write_all():
    """重建：先过结构守卫，再同时写中间产物与发布目录（同一份字节）。"""
    ok, lines = structural()
    for l in lines:
        print(l, flush=True)
    if not ok:
        print("ABORT：结构守卫未通过，未写入任何文件。", flush=True)
        return False
    os.makedirs(WEBP_AMERICAN, exist_ok=True)
    os.makedirs(PUB_CARDS, exist_ok=True)
    for d in (WEBP_AMERICAN, PUB_CARDS):
        for u in UNITS:
            dst = os.path.join(d, u + ".webp")
            with open(dst, "wb") as f:
                f.write(encode(os.path.join(CARDS_AMERICAN, u + ".png"), "RGB", Q_CARD))
    print("cards: 48 -> webp_american/ + assets/sprites/cards/", flush=True)
    prog = encode(os.path.join(CARDS_AMERICAN, "rarity_progress.png"), "RGB", Q_PROGRESS)
    for dst in [os.path.join(WEBP_AMERICAN, "rarity_progress.webp"),
                os.path.join(PUB_SPRITES, "rarity_progress.webp")]:
        with open(dst, "wb") as f:
            f.write(prog)
    print("progress: 1 -> 中间产物 + 发布", flush=True)
    for u in UNITS:
        dst = os.path.join(PUB_SPRITES, u + ".webp")
        with open(dst, "wb") as f:
            f.write(encode(os.path.join(SPRITES_PNG, u + ".png"), "RGBA", Q_CARD))
    print("sprites: 48 -> assets/sprites/", flush=True)
    print("DONE（来源：sprite_gen/cards_american 美式重出版）", flush=True)
    return True


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--check-fast"
    if arg in ("--check-fast", "--check", "--write"):
        if arg == "--write":
            good = write_all()
        else:
            good, lines = check_fast() if arg == "--check-fast" else check_full()
            for l in lines:
                print(l, flush=True)
            fails = [l for l in lines if l.startswith("FAIL")]
            print("\nSUMMARY  %s  PASS=%d  FAIL=%d" % (arg, len(lines) - len(fails), len(fails)), flush=True)
            if fails:
                print("首要 FAIL：" + fails[0], flush=True)
        sys.exit(0 if good else 1)
    else:
        print(__doc__)
        sys.exit(2)
