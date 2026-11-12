# -*- coding: utf-8 -*-
"""将 78 个播客成品 MP3 压缩为 Opus 24kbps 单声道，供网站使用。"""
import os, re, subprocess, sys
import imageio_ffmpeg

SRC = r"C:/Users/86135/WorkBuddy/英语音标播客/音频/成片"
DST = r"C:/Users/86135/WorkBuddy/英语音标播客/音标大闯关/assets/audio"
FF = imageio_ffmpeg.get_ffmpeg_exe()

os.makedirs(DST, exist_ok=True)
files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(".mp3"))
print(f"共 {len(files)} 个 MP3")

ok, fail = 0, 0
for f in files:
    m = re.match(r"(EP\d+|U\d+)", f)
    if not m:
        print("跳过(无法识别编号):", f); fail += 1; continue
    out = os.path.join(DST, m.group(1).lower() + ".opus")
    if os.path.exists(out) and os.path.getsize(out) > 10000:
        continue  # 断点续跑
    r = subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", os.path.join(SRC, f),
                        "-ac", "1", "-ar", "24000",
                        "-c:a", "libopus", "-b:a", "24k",
                        out], capture_output=True, text=True)
    if r.returncode != 0:
        print("失败:", f, r.stderr[:200]); fail += 1
    else:
        ok += 1
        if ok % 10 == 0:
            print(f"进度 {ok}/{len(files)}")

total = sum(os.path.getsize(os.path.join(DST, x)) for x in os.listdir(DST) if x.endswith(".opus"))
print(f"完成: 成功 {ok}, 失败 {fail}, 输出 {len(os.listdir(DST))} 个 opus, 合计 {total/1048576:.1f} MB")
