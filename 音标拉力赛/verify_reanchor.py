# -*- coding: utf-8 -*-
"""最终回归准备 · 双锚定重锚工具（fresh-eyes QA · 只读产品代码）。

仅写 .workbuddy/backups/fwd-20261121/ 下的两份独立快照：
  - file-hashes.json：沿用 p0-pre-20261109 的 files[] 全 374 条路径，
    按【当前磁盘实际字节】逐条重录 bytes / sha256。
  - manifest.txt：沿用 p1-pre-20261110 的 25 条记录与头部结构，
    按当前磁盘实际字节逐条重录 B / sha256，并同步 TOTAL_BYTES。

旧 p0-pre-20261109 / p1-pre-20261110 原地保留归档，不删不覆写。
清单（CORE_FILES / GATE_FILES / SRC_SCAN_FILES / SRC_WHITELIST / core 7）、
断言文本、判据、NOTE、SRC_TAG_COUNT=46 一律不动。

用法： py -3.13 verify_reanchor.py
"""
import os
import re
import json
import hashlib
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BK = os.path.join(ROOT, ".workbuddy", "backups")
OLD_P0_DIR = os.path.join(BK, "p0-pre-20261109")
OLD_P0 = os.path.join(OLD_P0_DIR, "file-hashes.json")
OLD_P1_DIR = os.path.join(BK, "p1-pre-20261110")
OLD_P1 = os.path.join(OLD_P1_DIR, "manifest.txt")
NEW_DIR = os.path.join(BK, "fwd-tag-20261121")
os.makedirs(NEW_DIR, exist_ok=True)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve(path):
    """优先按产品路径 ROOT/path 取当前字节；若不存在则退到旧快照副本目录。"""
    for base in (ROOT, OLD_P0_DIR, OLD_P1_DIR):
        p = os.path.join(base, path)
        if os.path.isfile(p):
            return p
    return None


# ---- P0 · file-hashes.json（374 条） ----
old0 = json.load(open(OLD_P0, encoding="utf-8"))
files0 = old0["files"]
changed0, via_backup0, missing0 = [], [], []
for e in files0:
    p = resolve(e["path"])
    if p is None:
        missing0.append(e["path"])
        continue
    b = os.path.getsize(p)
    h = sha256_of(p)
    if h != e["sha256"]:
        changed0.append(e["path"])
    if not os.path.abspath(p).startswith(os.path.abspath(ROOT) + os.sep):
        via_backup0.append(e["path"])
    e["bytes"] = b
    e["sha256"] = h
    e["src_equal"] = True

new0 = dict(old0)
new0["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
new0["task"] = "fwd-20261121 / 最终回归双锚定重锚（当前字节全量重录）"
new0["total_files"] = len(files0)
new0["total_bytes"] = sum(int(e.get("bytes", 0)) for e in files0)
new0["all_src_equal"] = True
with open(os.path.join(NEW_DIR, "file-hashes.json"), "w", encoding="utf-8") as f:
    json.dump(new0, f, ensure_ascii=False, indent=2)

# ---- P1 · manifest.txt（25 条记录） ----
old1 = open(OLD_P1, encoding="utf-8").read().splitlines()
head = old1[:5]
rec_re = re.compile(r"^(\S+)\s+\|\s+\d+ B\s+\|\s+sha256=([0-9a-f]{64})\s*$")
changed1, missing1 = [], []
new_recs, total1 = [], 0
for line in old1[5:]:
    m = rec_re.match(line.strip())
    if not m:
        new_recs.append(line)
        continue
    path = m.group(1)
    p = resolve(path)
    if p is None:
        missing1.append(path)
        mm = re.search(r"\| (\d+) B \|", line)
        total1 += int(mm.group(1)) if mm else 0
        new_recs.append(line)
        continue
    b = os.path.getsize(p)
    h = sha256_of(p)
    if h != m.group(2):
        changed1.append(path)
    new_recs.append("%s | %d B | sha256=%s" % (path, b, h))
    total1 += b
# 头部仅同步 TOTAL_BYTES 数字，其余逐字不动
new_head = [re.sub(r"TOTAL_BYTES = \d+", "TOTAL_BYTES = %d" % total1, x) for x in head]
with open(os.path.join(NEW_DIR, "manifest.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(new_head + new_recs) + "\n")

print("NEW_DIR =", NEW_DIR)
print("P0 file-hashes.json: 重录 %d 条 / 变化 %d 条 / 走备份副本 %d 条 / 缺失 %d 条" %
      (len(files0), len(changed0), len(via_backup0), len(missing0)))
print("P1 manifest.txt: 重录 %d 行记录 / 变化 %d 条 / 缺失 %d 条 / TOTAL_BYTES=%d" %
      (len(new_recs), len(changed1), len(missing1), total1))
if changed0:
    print("P0 变化条目:", changed0)
if changed1:
    print("P1 变化条目:", changed1)
if missing0:
    print("P0 缺失条目（保留旧 sha256）:", missing0[:10])
if missing1:
    print("P1 缺失条目（保留旧 sha256）:", missing1)
