# -*- coding: utf-8 -*-
"""生成 48 个「纯音标本身 + 真人代表词」拼接短音，覆盖 assets/audio/ph/uXX.opus。

每个音标点按 → 先听到"该音标本身代表的音"（edge-tts 纯音素，来自 phoneme_pure.json），
停顿 0.35s 后，再听到真人录音的代表词（来自 _phrepo/words-voice/word-<词>.mp3）。
文件名不变（ph/uXX.opus）→ 前端 AudioMgr.playPhoneme 无需改动。

管线：edge-tts -> mp3(纯音素) ；repo mp3(真人词)；ffmpeg 归一化 24k mono + apad 停顿 + concat -> libopus。
"""
import asyncio, json, os, subprocess, sys
import edge_tts
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = os.path.dirname(os.path.abspath(__file__))
PHONEME_PURE = os.path.join(ROOT, "音标大闯关", "sprite_gen", "phoneme_pure.json")
REPO_WORDS = os.path.join(ROOT, "_phrepo", "words-voice")
DST = os.path.join(ROOT, "音标大闯关", "assets", "audio", "ph")
TMP = os.path.join(ROOT, "_ph_combined_tmp")
os.makedirs(DST, exist_ok=True)
os.makedirs(TMP, exist_ok=True)

# U -> 项目代表词（按 IPA 音标语义映射，已 48/48 校验存在于 words-voice）
M = {
    1: "bee", 2: "little", 3: "bed", 4: "ant", 5: "mark", 6: "cup", 7: "dog",
    8: "caught", 9: "book", 10: "cool", 11: "bird", 12: "center",
    13: "wait", 14: "my", 15: "point", 16: "pose", 17: "mouse", 18: "beer",
    19: "bear", 20: "poor",
    21: "sip", 22: "bread", 23: "tomorrow", 24: "dog", 25: "cat", 26: "egg",
    27: "fish", 28: "very", 29: "path", 30: "they", 31: "nice", 32: "seize",
    33: "ship", 34: "decision", 35: "hut", 36: "read", 37: "chick", 38: "jam",
    39: "smart", 40: "no", 41: "spring", 42: "line", 43: "work", 44: "yell",
    45: "track", 46: "dress", 47: "eats", 48: "beds",
}


def find_repo_mp3(word):
    low = word.lower()
    for f in os.listdir(REPO_WORDS):
        if f.startswith("word-") and f.endswith(".mp3") and f[5:-4].lower() == low:
            return os.path.join(REPO_WORDS, f)
    return None


async def synth_pure(row, out_mp3):
    for a in range(3):
        try:
            await edge_tts.Communicate(row["prompt"], row.get("voice", "en-US-AriaNeural"),
                                       rate=row.get("rate", "+0%")).save(out_mp3)
            if os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 300:
                return True
        except Exception as e:
            print(f"    synth {row['unit']} attempt{a+1}: {str(e)[:100]}")
        await asyncio.sleep(1.5 * (a + 1))
    return False


def combine(pure_mp3, word_mp3, out_opus, gap=0.35):
    # 纯音素 + gap 停顿 + 真人词，统一 24k mono 后拼接，编码 ogg/opus
    cmd = [FF, "-y", "-hide_banner", "-loglevel", "error",
           "-i", pure_mp3, "-i", word_mp3,
           "-filter_complex",
           f"[0:a]aresample=24000,aformat=channel_layouts=mono[a];"
           f"[1:a]aresample=24000,aformat=channel_layouts=mono[b];"
           f"[a]apad=pad_dur={gap}[c];[c][b]concat=n=2:v=0:a=1[out]",
           "-map", "[out]", "-ac", "1", "-ar", "24000",
           "-c:a", "libopus", "-b:a", "24k", out_opus]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0 and os.path.exists(out_opus)


async def main():
    plan = {r["unit"]: r for r in json.load(open(PHONEME_PURE, encoding="utf-8"))}
    ok = fail = 0
    for u in range(1, 49):
        row = plan.get("U%02d" % u)
        if not row:
            fail += 1; print(f"  [SKIP] U{u:02d} 无纯音标规划"); continue
        word = M[u]
        wmp3 = find_repo_mp3(word)
        if not wmp3:
            fail += 1; print(f"  [MISS] U{u:02d} 真人词 {word!r} 未找到"); continue
        pmp3 = os.path.join(TMP, "U%02d.pure.mp3" % u)
        out = os.path.join(DST, "u%02d.opus" % u)
        if not await synth_pure(row, pmp3):
            fail += 1; print(f"  [FAIL] U{u:02d} 纯音素合成失败"); continue
        if not combine(pmp3, wmp3, out):
            fail += 1; print(f"  [FAIL] U{u:02d} 拼接/编码失败"); continue
        ok += 1
        print(f"  [OK] U{u:02d} {row['sym']:<5} [{row['prompt']} + {word}] -> {os.path.getsize(out)}B")
        if ok % 10 == 0:
            print(f"    进度 {ok}/{48}")

    total = sum(os.path.getsize(os.path.join(DST, f)) for f in os.listdir(DST) if f.endswith(".opus"))
    n = len([f for f in os.listdir(DST) if f.endswith(".opus")])
    print(f"\n完成: 成功 {ok} 失败 {fail}; ph/ 现有 {n} 个 opus, 合计 {total/1048576:.2f} MB")
    sys.exit(0 if fail == 0 and ok == 48 else 1)


asyncio.run(main())
