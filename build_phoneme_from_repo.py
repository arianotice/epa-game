# -*- coding: utf-8 -*-
"""从开源项目 boommanpro/phonetic_symbol_web 的 words-voice 里，
为 48 个音标一一映射真人录音，转 ogg/opus 24k 单声道，覆盖 assets/audio/ph/uXX.opus。

源：_phrepo/words-voice/word-<word>.mp3（真人朗读该音标代表词）
映射：按 IPA 音标语义，把我们 U01–U48 对应到项目 48 键 phonetic_words.json 的代表词。
前端 AudioMgr.playPhoneme 文件名不变，无需改动。
"""
import os, shutil, subprocess
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
REPO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_phrepo", "words-voice")
HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "音标大闯关", "assets", "audio", "ph")
os.makedirs(DST, exist_ok=True)

# U 号 -> words-voice 里的代表词（按 IPA 音标语义精确映射，已 48/48 校验存在）
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


def find_mp3(word):
    # 文件名可能带大小写（word-July.mp3），用大小写不敏感匹配
    low = word.lower()
    for f in os.listdir(REPO):
        if f.startswith("word-") and f.endswith(".mp3") and f[5:-4].lower() == low:
            return os.path.join(REPO, f)
    return None


def to_opus(mp3, out):
    r = subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", mp3, "-ac", "1", "-ar", "24000",
                        "-c:a", "libopus", "-b:a", "24k", out],
                       capture_output=True, text=True)
    return r.returncode == 0


def main():
    ok = fail = 0
    for u in range(1, 49):
        word = M[u]
        src = find_mp3(word)
        out = os.path.join(DST, "u%02d.opus" % u)
        if not src:
            fail += 1
            print(f"  [MISS] U{u:02d} {word!r} 源 mp3 未找到")
            continue
        if not to_opus(src, out) or not os.path.exists(out):
            fail += 1
            print(f"  [FAIL] U{u:02d} {word!r} 转码失败")
            continue
        ok += 1
        print(f"  [OK] U{u:02d} {word:<9} <- {os.path.basename(src):>16} -> {os.path.getsize(out)}B")
    total = sum(os.path.getsize(os.path.join(DST, f)) for f in os.listdir(DST) if f.endswith(".opus"))
    n = len([f for f in os.listdir(DST) if f.endswith(".opus")])
    print(f"\n完成: 成功 {ok} 失败 {fail}; ph/ 现有 {n} 个 opus, 合计 {total/1048576:.2f} MB")
    import sys
    sys.exit(0 if fail == 0 and ok == 48 else 1)


if __name__ == "__main__":
    main()
