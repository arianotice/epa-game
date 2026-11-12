# -*- coding: utf-8 -*-
"""生成 48 个音标短音（edge-tts 念代表词 → ogg/opus 24k 单声道）。

用途：首页故事线/图鉴点音标时播放"准确的音标读音"（1-2 秒代表词），
替代原先 3-8 分钟的整期播客（uXX.opus）。

管线与 build_audio.py 一致（imageio_ffmpeg → ogg/opus 24k mono），离线可部署。
输出：assets/audio/ph/u01.opus ... u48.opus
"""
import asyncio, json, os, re, subprocess, sys

import edge_tts
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
DST = os.path.join(os.path.dirname(__file__), "assets", "audio", "ph")
MANIFEST = os.path.join(os.path.dirname(__file__), "sprite_gen", "phoneme_words.json")
VOICE = "en-US-AriaNeural"
RATE = "-10%"          # 略放慢，元音/辅音更清晰
os.makedirs(DST, exist_ok=True)

rows = json.load(open(MANIFEST, encoding="utf-8"))
print(f"edge-tts 生成 {len(rows)} 个音标短音 -> {DST}  (voice={VOICE})")


async def synth(row, mp3_path):
    async def run():
        tts = edge_tts.Communicate(row["word"], VOICE, rate=RATE)
        await tts.save(mp3_path)
    for attempt in range(3):
        try:
            await run()
            if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 500:
                return True
        except Exception as e:
            print(f"  synth {row['unit']} attempt{attempt+1} err: {str(e)[:120]}")
        await asyncio.sleep(1.5 * (attempt + 1))
    return False


def to_opus(mp3_path, out_path):
    r = subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                        "-i", mp3_path,
                        "-ac", "1", "-ar", "24000",
                        "-c:a", "libopus", "-b:a", "24k", out_path],
                       capture_output=True, text=True)
    return r.returncode == 0


async def main():
    ok, fail = 0, 0
    for row in rows:
        out = os.path.join(DST, row["unit"].lower() + ".opus")
        if os.path.exists(out) and os.path.getsize(out) > 1000:
            continue  # 断点续跑
        mp3 = os.path.join(DST, row["unit"].lower() + ".mp3")
        need = True
        if os.path.exists(mp3) and os.path.getsize(mp3) > 500:
            need = False
        if need:
            if not await synth(row, mp3):
                fail += 1
                print(f"  [FAIL] {row['unit']} {row['word']!r} 网络/合成失败，跳过")
                continue
        if not to_opus(mp3, out):
            fail += 1
            print(f"  [FAIL] {row['unit']} opus 转码失败")
            continue
        try:
            os.remove(mp3)
        except OSError:
            pass
        ok += 1
        print(f"  [OK] {row['unit']} {row['word']:<12} ({row['sym']}) -> {os.path.getsize(out)}B")
        if ok % 10 == 0:
            print(f"  进度 {ok}/{len(rows)}")

    total = sum(os.path.getsize(os.path.join(DST, f)) for f in os.listdir(DST)
                if f.endswith(".opus"))
    n = len([f for f in os.listdir(DST) if f.endswith(".opus")])
    print(f"\n完成: 本次成功 {ok}, 失败 {fail}; ph/ 目录现有 {n} 个 opus, 合计 {total/1048576:.2f} MB")
    sys.exit(0 if fail == 0 and n == 48 else 1)


asyncio.run(main())
