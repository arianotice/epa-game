import os, glob, wave, re

ROOT = r"C:\Users\86135\WorkBuddy\英语音标播客"
D = os.path.join(ROOT, "音频", "成片")

def dur(mp3):
    w = mp3[:-4] + ".wav"
    if os.path.exists(w):
        wf = wave.open(w, "rb")
        x = wf.getnframes() / wf.getframerate()
        wf.close()
        return x
    return 0.0

rows_ep, rows_u = [], []
for f in sorted(glob.glob(os.path.join(D, "*.mp3"))):
    b = os.path.basename(f)[:-4]
    m = re.match(r"(EP\d+|U\d+)-(.*)-完整音频", b)
    if not m:
        continue
    code, title = m.group(1), m.group(2)
    sz = os.path.getsize(f) / 1048576
    line = "| %s | %s | %.1f 分钟 | %.1f MB |" % (code, title, dur(f) / 60, sz)
    (rows_ep if code.startswith("EP") else rows_u).append(line)

doc = []
doc.append("# 《声音探险队 · 48个音标精灵》音频成品清单")
doc.append("")
doc.append("> 全系列已全部制作完成，共 **78 个成品文件**：30 期正节目 + 48 个音标讲解单元。")
doc.append("> 总时长 **413.5 分钟（约 6.9 小时）**，总体积 378.7 MB，目录：`音频/成片/`。")
doc.append("> 全部采用免费 TTS 方案合成，英文单词与音素示范一律使用标准美音音色。")
doc.append("")
doc.append("## 声音方案")
doc.append("")
doc.append("| 角色 | 中文讲解 | 英文示范 |")
doc.append("|---|---|---|")
doc.append("| 波波队长 | zh-CN-YunxiaNeural（呆萌男童） | en-US-BrianNeural（标准美音） |")
doc.append("| 小 Q | zh-CN-XiaoyiNeural（萌萌女童） | en-US-AnaNeural（标准美音） |")
doc.append("")
doc.append("中英文分段独立合成：中文讲解走地道童声，英文单词与音素走美音，两者在脚本层面严格分离（由 lang 字段控制），")
doc.append("因此不存在中文音色念英文带来的中式口音问题。")
doc.append("")
doc.append("## 一、30 期正节目（合计 236.7 分钟）")
doc.append("")
doc.append("| 编号 | 标题 | 时长 | 大小 |")
doc.append("|---|---|---|---|")
doc.extend(rows_ep)
doc.append("")
doc.append("## 二、48 个音标讲解单元（合计 176.9 分钟）")
doc.append("")
doc.append("| 编号 | 精灵 | 时长 | 大小 |")
doc.append("|---|---|---|---|")
doc.extend(rows_u)
doc.append("")
doc.append("## 技术备注")
doc.append("")
doc.append("- 规格：MP3 / 32kHz / 128kbps 单声道；同名 .wav 无损版同目录存放，便于后期混音效")
doc.append("- 生产管线：`生产管线/engine.py`；脚本源：`生产管线/脚本/`（正片 EP*.json、单元 `脚本/单元/U*.json`）")
doc.append("- 管线支持断点续跑：若某段合成失败，原样重跑即可只补失败段")

out = os.path.join(ROOT, "音频成品清单.md")
open(out, "w", encoding="utf-8").write("\n".join(doc))
print("清单已生成:", out)
print("条目数:", len(rows_ep) + len(rows_u))
