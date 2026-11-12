# -*- coding: utf-8 -*-
"""
verify_p1_plr.py · 81 项 PLR-* 迁移重放适配器（#46 / 2026-11-12）

规范依据：design/p1-gate-retirement.md §3（81 行承接表）与 §5（门控全绿口径）。

做什么：
  把四套【已退役】旧门控里 81 条保留断言，用【正确扫描域】在新 P1 判定链中
  逐条重放；导出 (name, ok, detail) 供 verify_p1_gate.py 以 PLR-<组>-<编号>
  归属计入 PASS / FAIL。

纪律（逐条对应退役令 §0 / §2 / §7）：
  1. 只读取旧脚本的【断言定义与期望值】，源码逐字不改、不改名、不删除；
  2. 丢弃旧脚本的 SUMMARY 与 exit code —— 它们自 2026-11-12 起不进判定链；
  3. 扫描域按 PB-* 排除清单修正（node_modules / dist / .p0-build / .workbuddy
     / .git / __pycache__ / src / .vite / coverage），且只作用于项目树内的 walk，
     不干扰 site-packages 内 Playwright driver 自身的 walk；
  4. 缺失断言 = FAIL，绝不静默补空、绝不改 NOTE、绝不放宽阈值；
  5. 6 条历史真实 FAIL 的原文仍永久留在 p1-legacy-gate-fail-scan.md。

用法：
  py -3.13 verify_p1_plr.py --only verify_cseg_gate.py --out <json>
  不传 --only 时一次重放全部三套（cseg_ui 的 PL_CHECKS 为 0 项，不在此列）。
"""
import os
import sys
import io
import json
import tempfile
import argparse
import traceback

# PB-* 正确扫描域（p1-qa-spec.md §2.6 / p1-gate-retirement.md §3 扫描域铁律）
EXCLUDE = {
    "node_modules", "dist", ".p0-build", ".workbuddy", "__pycache__",
    ".git", "src", ".vite", "coverage",
}

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
QUEST = os.path.join(ROOT, "音标大闯关")

SCRIPTS = {
    "verify_cseg_gate.py": os.path.join(HERE, "verify_cseg_gate.py"),
    "verify_fresh_gate.py": os.path.join(QUEST, "verify_fresh_gate.py"),
    "verify_c08_gate.py": os.path.join(QUEST, "verify_c08_gate.py"),
}

_ORIG_WALK = os.walk
_PROJ = os.path.abspath(ROOT)


def _in_project(p):
    try:
        p = os.path.abspath(p)
    except Exception:
        return False
    return p == _PROJ or p.startswith(_PROJ + os.sep)


def _walk(top, topdown=True, onerror=None, followlinks=False):
    """只修正项目树内的扫描域；站点包 / 系统目录原样放行。"""
    limit = _in_project(top)
    for dp, dns, fns in _ORIG_WALK(top, topdown=topdown,
                                   onerror=onerror, followlinks=followlinks):
        if limit and topdown:
            dns[:] = [d for d in dns if d not in EXCLUDE]
        yield dp, dns, fns


def _safe(d):
    try:
        json.dumps(d, ensure_ascii=False)
        return d
    except Exception:
        return repr(d)


class _StdoutProxy:
    """旧脚本开头会 `io.TextIOWrapper(sys.stdout.buffer, ...)` 二次包装 stdout。

    若把 sys.stdout 直接换成包着单一 raw file 的 TextIOWrapper，旧 wrapper 被 GC
    时会连底层 fd 一起关掉，新 wrapper 随即 `ValueError: I/O operation on closed
    file`。这里让每次访问 .buffer 都返回一份独立打开的文件句柄，彼此不影响。
    """

    def __init__(self, path):
        self._path = path
        self._fp = open(path, "wb", buffering=0)
        self.encoding = "utf-8"
        self.errors = "replace"

    @property
    def buffer(self):
        return io.BufferedWriter(open(self._path, "ab", buffering=0))

    def write(self, s):
        try:
            self._fp.write(s.encode("utf-8", "replace"))
        except Exception:
            pass
        return len(s)

    def flush(self):
        try:
            self._fp.flush()
        except Exception:
            pass

    def close(self):
        try:
            self._fp.close()
        except Exception:
            pass

    def isatty(self):
        return False

    def writable(self):
        return True

    def readable(self):
        return False

    def seekable(self):
        return False

    def fileno(self):
        return self._fp.fileno()


def replay(path, logpath):
    src = open(path, encoding="utf-8").read()
    g = {
        "__name__": "__main__",
        "__file__": os.path.abspath(path),
        "__builtins__": __builtins__,
    }
    saved_walk, saved_out = os.walk, sys.stdout
    proxy = _StdoutProxy(logpath)
    err = None
    try:
        sys.stdout = proxy
        os.walk = _walk
        try:
            exec(compile(src, path, "exec"), g)
        except SystemExit:
            pass                      # 旧脚本结尾 sys.exit(1 if f else 0)：丢弃
        except BaseException:
            err = traceback.format_exc()
    finally:
        os.walk = saved_walk
        sys.stdout = saved_out
        proxy.close()

    rows = []
    for item in g.get("RESULTS", []):
        try:
            rows.append({
                "name": str(item[0]),
                "ok": bool(item[1]),
                "detail": _safe(item[2]) if len(item) > 2 else None,
            })
        except Exception:
            continue
    return {"ok": err is None and bool(rows), "error": err,
            "count": len(rows), "results": rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, choices=sorted(SCRIPTS))
    ap.add_argument("--log-dir", default=None)
    a = ap.parse_args()

    logdir = a.log_dir or tempfile.mkdtemp(prefix="p1-plr-")
    os.makedirs(logdir, exist_ok=True)
    targets = ([a.only] if a.only else sorted(SCRIPTS))

    out = {"mode": "PLR_REPLAY", "exclude_dirs": sorted(EXCLUDE), "scripts": {}}
    for name in targets:
        path = SCRIPTS[name]
        print("[PLR] replay %s ..." % name, flush=True)
        r = replay(path, os.path.join(logdir, name + ".log"))
        r["path"] = path
        r["log"] = os.path.join(logdir, name + ".log")
        out["scripts"][name] = r
        print("[PLR]   -> %d checks | error=%s" %
              (r["count"], "YES" if r["error"] else "no"), flush=True)

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("[PLR] RESULT_JSON -> " + a.out, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
