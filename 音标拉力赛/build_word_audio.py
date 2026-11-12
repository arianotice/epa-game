# -*- coding: utf-8 -*-
"""C 段例词音频补生成（edge-tts，en-US-AriaNeural 自然语速）。

词表不写死：直接向 config.js 的 allWords() 取，保证「题库 → 音频」单一来源。
只生成缺失的 <word>.mp3，支持断点续跑；已存在的 18 个旧词音频逐字不动。
输出目录：音标拉力赛/audio/

用法：C:/Users/86135/AppData/Local/Programs/Python/Python313/python.exe build_word_audio.py
"""
import asyncio
import json
import os
import subprocess
import sys

import edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
JS = os.path.join(HERE, "js")
DST = os.path.join(HERE, "audio")
VOICE = "en-US-AriaNeural"
# 专有名词按正常大小写念，文件名仍用小写（与题库 word 一致）
PRONOUNCE = {"luke": "Luke"}

os.makedirs(DST, exist_ok=True)


def word_list():
    code = ('import fs from "node:fs";'
            'const C = await import("./js/config.js");'
            'process.stdout.write(JSON.stringify(C.allWords()));')
    r = subprocess.run(["node", "--input-type=module", "-e", code],
                       cwd=HERE, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print("读取 config.js 词表失败：", r.stderr[-800:])
        sys.exit(2)
    return json.loads(r.stdout)


async def synth(word, path):
    text = PRONOUNCE.get(word, word)
    for attempt in range(3):
        try:
            tts = edge_tts.Communicate(text, VOICE)
            await tts.save(path)
            if os.path.exists(path) and os.path.getsize(path) > 500:
                return True
        except Exception as e:
            print("  retry %s #%d: %s" % (word, attempt + 1, str(e)[:100]), flush=True)
        await asyncio.sleep(1.2 * (attempt + 1))
    return False


async def main():
    words = word_list()
    todo = [w for w in words if not (os.path.exists(os.path.join(DST, w + ".mp3"))
                                     and os.path.getsize(os.path.join(DST, w + ".mp3")) > 500)]
    print("词表 %d 个 / 待生成 %d 个 / 输出 %s" % (len(words), len(todo), DST), flush=True)
    ok, fail = 0, []
    for i, w in enumerate(todo, 1):
        p = os.path.join(DST, w + ".mp3")
        if await synth(w, p):
            ok += 1
        else:
            fail.append(w)
            if os.path.exists(p):
                os.remove(p)
        if i % 10 == 0 or i == len(todo):
            print("  进度 %d/%d (ok=%d fail=%d)" % (i, len(todo), ok, len(fail)), flush=True)
        await asyncio.sleep(0.12)

    present = [f for f in os.listdir(DST) if f.endswith(".mp3")]
    missing = [w for w in words if w + ".mp3" not in present]
    total = sum(os.path.getsize(os.path.join(DST, f)) for f in present)
    print("\n完成：本次成功 %d，失败 %d；audio/ 共 %d 个 mp3 / %.2f MB"
          % (ok, len(fail), len(present), total / 1048576), flush=True)
    print("词表覆盖缺口：", missing, flush=True)
    sys.exit(0 if not fail and not missing else 1)


asyncio.run(main())
