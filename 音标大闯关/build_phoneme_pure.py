# -*- coding: utf-8 -*-
"""生成 48 个「纯音标读法」短音（edge-tts 念纯音标提示词 → ogg/opus 24k 单声道）。

覆盖 build_phoneme_clips.py 产出的"单词版"（assets/audio/ph/uXX.opus），
让点音标时只听到"该音标的读法"而非代表词。前端 AudioMgr.playPhoneme 无需改动。
"""
import asyncio, json, os, subprocess, sys
import edge_tts
import imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "assets", "audio", "ph")
PLAN = os.path.join(HERE, "sprite_gen", "phoneme_pure.json")
os.makedirs(DST, exist_ok=True)

plan = json.load(open(PLAN, encoding="utf-8"))
print(f"生成 {len(plan)} 个纯音标短音 -> {DST}")


async def synth(row, mp3):
    for attempt in range(3):
        try:
            await edge_tts.Communicate(row["prompt"], row.get("voice", "en-US-AriaNeural"),
                                       rate=row.get("rate", "+0%")).save(mp3)
            if os.path.exists(mp3) and os.path.getsize(mp3) > 400:
                return True
        except Exception as e:
            print(f"  synth {row['unit']} attempt{attempt+1}: {str(e)[:120]}")
        await asyncio.sleep(1.5 * (attempt + 1))
    return False


def to_opus(mp3, out):
    return subprocess.run([FF, "-y", "-hide_banner", "-loglevel", "error",
                           "-i", mp3, "-ac", "1", "-ar", "24000",
                           "-c:a", "libopus", "-b:a", "24k", out],
                          capture_output=True, text=True).returncode == 0


async def main():
    ok = fail = 0
    for row in plan:
        out = os.path.join(DST, row["unit"].lower() + ".opus")
        mp3 = os.path.join(DST, row["unit"].lower() + ".tmp.mp3")
        # 强制重生成（覆盖单词版）：不跳过已存在的 out
        if not await synth(row, mp3):
            fail += 1
            print(f"  [FAIL] {row['unit']} {row['prompt']!r} 合成失败")
            continue
        if not to_opus(mp3, out):
            fail += 1
            print(f"  [FAIL] {row['unit']} opus 转码失败")
            continue
        try: os.remove(mp3)
        except OSError: pass
        ok += 1
        print(f"  [OK] {row['unit']} {row['sym']:<5} TTS={row['prompt']:<8} -> {os.path.getsize(out)}B")
        if ok % 10 == 0:
            print(f"  进度 {ok}/{len(plan)}")

    total = sum(os.path.getsize(os.path.join(DST, f)) for f in os.listdir(DST) if f.endswith(".opus"))
    print(f"\n完成: 成功 {ok} 失败 {fail}; ph/ 现有 {len([f for f in os.listdir(DST) if f.endswith('.opus')])} 个 opus, 合计 {total/1048576:.2f} MB")
    sys.exit(0 if fail == 0 and ok == 48 else 1)


asyncio.run(main())
