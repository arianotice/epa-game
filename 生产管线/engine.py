#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Universal free-TTS production engine for 声音探险队 podcast.

Voice routing (scheme B - Chinese native + American English):
  波波队长  zh -> zh-CN-YunxiaNeural (呆萌男童)   en -> en-US-BrianNeural (美音男 · approachable)
  小 Q      zh -> zh-CN-XiaoyiNeural (萌萌女童)   en -> en-US-AnaNeural   (美音女 · cute/cartoon)

Usage:
  python3 engine.py synth  <script.json>   # generate segments (resumable)
  python3 engine.py concat <script.json>   # concat into one long MP3 + WAV
  python3 engine.py all    <script.json>   # both
"""
import asyncio, json, os, sys, wave
import miniaudio

SR = 32000
WORK = r"C:\Users\86135\WorkBuddy\英语音标播客\音频"

VOICES = {
    ("bobo", "zh"): "zh-CN-YunxiaNeural",
    ("bobo", "en"): "en-US-BrianNeural",
    ("xq",   "zh"): "zh-CN-XiaoyiNeural",
    ("xq",   "en"): "en-US-AnaNeural",
}

def seg_dir(ep):
    d = os.path.join(WORK, "合成段", ep)
    os.makedirs(d, exist_ok=True)
    return d

def rate(speed):
    return "%+d%%" % round((speed - 1.0) * 100)

async def _synth_one(seg, path, sem):
    import edge_tts
    voice = VOICES[(seg["role"], seg.get("lang", "zh"))]
    comm = edge_tts.Communicate(seg["text"], voice, rate=rate(seg.get("speed", 0.85)))
    async with sem:
        with open(path, "wb") as f:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])

def verify(path):
    """decode via miniaudio to confirm the file is real audio; return duration."""
    with open(path, "rb") as f:
        raw = f.read()
    if len(raw) < 200:
        return 0.0
    info = miniaudio.decode(raw, output_format=miniaudio.SampleFormat.SIGNED16,
                            nchannels=1, sample_rate=SR)
    return info.num_frames / SR

async def cmd_synth(script):
    ep = script["ep"]
    d = seg_dir(ep)
    segs = script["segments"]
    sem = asyncio.Semaphore(4)
    todo, done = [], 0
    for s in segs:
        p = os.path.join(d, "seg_%s.mp3" % s["id"])
        dur = verify(p) if os.path.exists(p) else 0.0
        if dur > 0.1:
            done += 1
            continue
        todo.append(s)
    print("[%s] %d segments, %d already done, %d to synthesize" % (ep, len(segs), done, len(todo)))
    fails = []
    for s in todo:
        p = os.path.join(d, "seg_%s.mp3" % s["id"])
        ok = False
        for attempt in range(4):
            try:
                await _synth_one(s, p, sem)
                if verify(p) > 0.1:
                    ok = True
                    break
            except Exception as e:
                print("  [%s] try%d %s" % (s["id"], attempt + 1, str(e)[:70]))
            await asyncio.sleep(2)
        if ok:
            print("  ok %-7s %-4s %-2s %.1fs" % (s["id"], s["role"], s.get("lang", "zh"), verify(p)))
        else:
            fails.append(s["id"])
            if os.path.exists(p):
                os.remove(p)
            print("  FAIL %s" % s["id"])
        await asyncio.sleep(0.3)
    print("[%s] done=%d/%d fails=%s" % (ep, len(segs) - len(fails), len(segs), fails or "none"))
    return 1 if fails else 0

def cmd_concat(script):
    ep = script["ep"]
    d = seg_dir(ep)
    out_dir = os.path.join(WORK, "成片")
    os.makedirs(out_dir, exist_ok=True)
    gaps = script.get("gaps", {})
    default_gap = script.get("default_gap", 0.3)
    pcm = bytearray()
    total = 0
    for i, s in enumerate(script["segments"]):
        p = os.path.join(d, "seg_%s.mp3" % s["id"])
        if not os.path.exists(p):
            print("MISSING %s" % s["id"])
            return 2
        with open(p, "rb") as f:
            info = miniaudio.decode(f.read(), output_format=miniaudio.SampleFormat.SIGNED16,
                                    nchannels=1, sample_rate=SR)
        pcm += bytes(info.samples)
        total += info.num_frames
        if i < len(script["segments"]) - 1:
            gf = int(round(gaps.get(s["id"], default_gap) * SR))
            pcm += b"\x00" * (gf * 2)
            total += gf
    name = "%s-%s-完整音频" % (ep, script["title"])
    wav = os.path.join(out_dir, name + ".wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(bytes(pcm))
    mp3 = os.path.join(out_dir, name + ".mp3")
    import lameenc
    src = wave.open(wav, "rb")
    enc = lameenc.Encoder()
    enc.set_bit_rate(128); enc.set_in_sample_rate(SR); enc.set_channels(1); enc.set_quality(2)
    with open(mp3, "wb") as out:
        while True:
            chunk = src.readframes(576000)
            if not chunk:
                break
            out.write(enc.encode(chunk))
        out.write(enc.flush())
    src.close()
    dur = total / SR
    print("FINAL %s" % mp3)
    print("duration=%.1fs (%.2f min) mp3=%.1fMB" % (dur, dur / 60, os.path.getsize(mp3) / 1048576))
    return 0

async def main():
    cmd = sys.argv[1]
    script = json.load(open(sys.argv[2], encoding="utf-8"))
    if cmd in ("synth", "all"):
        rc = await cmd_synth(script)
        if rc and cmd == "all":
            return rc
    if cmd in ("concat", "all"):
        return cmd_concat(script)
    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
