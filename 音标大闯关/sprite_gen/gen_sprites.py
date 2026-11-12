# -*- coding: utf-8 -*-
"""批量调用 Agnes 生图（经 agnes-ai-generation skill 的 agnes_api.py）出 48 张音标精灵白底贴纸。

需要环境变量 AGNES_API_KEY（或 AGNES_API_TOKEN / APIHUB_AGNES_API_KEY）。
断点续传：raw/uXX.png 已存在且非空则跳过。

用法：
  python gen_sprites.py --samples            # 先出 6 张稀有度样板（每档 1 张）给风格确认
  python gen_sprites.py --units U01,U05,U41  # 指定某几张
  python gen_sprites.py --all                 # 出满 48 张
  python gen_sprites.py --samples --force     # 强制重出
"""
import argparse, json, os, sys, re, time, urllib.request, concurrent.futures as cf

HERE = os.path.dirname(os.path.abspath(__file__))
AGNES_API = os.path.abspath(os.path.join(HERE, "..", "..", "agnes-ai-generation-skill", "scripts", "agnes_api.py"))
RAW = os.path.join(HERE, "raw")
os.makedirs(RAW, exist_ok=True)

# 6 档稀有度样板：每档挑一张有辨识度的
SAMPLES = {"P": "U01", "SR": "U21", "SAR": "U13", "HR": "U17", "SSR": "U33", "UR": "U41"}
SAMPLE_ORDER = [SAMPLES[r] for r in ("P", "SR", "SAR", "HR", "SSR", "UR")]


def load_manifest():
    return json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))


def prompt_of(mf, u):
    return mf[u]["prompt"]


import threading
_LAST_CALL = {"t": 0.0}
_THR_LOCK = threading.Lock()


def throttle(min_gap=8.0):
    """全局节流：两次出图调用至少间隔 min_gap 秒，避免撞 429 限流（线程安全）。"""
    with _THR_LOCK:
        wait = _LAST_CALL["t"] + min_gap - time.time()
        if wait > 0:
            time.sleep(wait)
        _LAST_CALL["t"] = time.time()


def call_agnes(unit, prompt, size="1024x1024", retries=5):
    """subprocess 调 agnes_api.py image，返回首个 url。遇 429 限流则指数退避重试。"""
    import subprocess, random
    env = dict(os.environ)
    cmd = [sys.executable, AGNES_API, "image", "--prompt", prompt,
           "--size", size, "--no-translate-prompt", "--raw"]
    for attempt in range(retries):
        throttle()
        p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=240)
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        m = re.search(r"\{.*\}", out, re.DOTALL)
        if p.returncode == 0 and m:
            data = json.loads(m.group(0))
        else:
            # 429 限流：退避重试（15s, 30s, 60s, 90s, 120s）
            if "429" in err or "rate limit" in err.lower():
                backoff = min(120, 15 * (attempt + 1)) + random.uniform(0, 5)
                print(f"  429 [{unit}] 第{attempt+1}次，退避 {backoff:.0f}s ...", flush=True)
                time.sleep(backoff)
                continue
            raise RuntimeError(f"[{unit}] no JSON (rc={p.returncode}):\n{out[:400]}\nSTDERR:{err[:300]}")
        break
    else:
        raise RuntimeError(f"[{unit}] 重试 {retries} 次仍 429 限流，稍后再补")
    # 提取 url
    urls = []
    def grab(o):
        if isinstance(o, dict):
            for k in ("url", "image_url"):
                if isinstance(o.get(k), str):
                    urls.append(o[k])
            for v in o.values():
                grab(v)
        elif isinstance(o, list):
            for v in o:
                grab(v)
    grab(data)
    if not urls:
        raise RuntimeError(f"[{unit}] no url in Agnes response: {str(data)[:300]}")
    return urls[0]


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())


def process_unit(unit, mf, size, force):
    dest = os.path.join(RAW, f"{unit}.png")
    if not force and os.path.exists(dest) and os.path.getsize(dest) > 1000:
        print(f"  skip {unit} (cached)")
        return (unit, "cached")
    prompt = prompt_of(mf, unit)
    url = call_agnes(unit, prompt, size)
    download(url, dest)
    print(f"  ok   {unit} <- {url[:80]}")
    return (unit, "ok", url)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", action="store_true", help="出 6 张稀有度样板")
    ap.add_argument("--units", help="逗号分隔 unit 列表")
    ap.add_argument("--all", action="store_true", help="出满 48 张")
    ap.add_argument("--size", default="1024x1024")
    ap.add_argument("--force", action="store_true", help="忽略缓存强制重出")
    ap.add_argument("--workers", type=int, default=3, help="并发数（默认 3，避免限流）")
    args = ap.parse_args()

    mf = load_manifest()
    if args.samples:
        units = SAMPLE_ORDER
    elif args.units:
        units = [u.strip().upper() for u in args.units.split(",") if u.strip()]
    elif args.all:
        units = [u for u in mf.keys()]
    else:
        units = SAMPLE_ORDER  # 默认 6 样板
        print("（未指定 --all/--samples/--units，默认出 6 张样板）")

    # 校验 key
    if not any(os.environ.get(k) for k in ("AGNES_API_KEY", "AGNES_API_TOKEN", "APIHUB_AGNES_API_KEY")):
        print("ERROR: 未检测到 AGNES_API_KEY。请设置后重试：")
        print("  Windows PowerShell:  $env:AGNES_API_KEY='sk-...'")
        print("  Git Bash:            export AGNES_API_KEY='sk-...'")
        print("（key 在 https://platform.agnes-ai.com 申请）")
        sys.exit(1)

    if "U01" not in units:
        pass
    print(f"准备出 {len(units)} 张精灵: {units}\n")
    t0 = time.time()
    results, fails = [], []
    with cf.ThreadPoolExecutor(max_workers=max(1, args.workers)) as ex:
        futs = {ex.submit(process_unit, u, mf, args.size, args.force): u for u in units}
        for fut in cf.as_completed(futs):
            u = futs[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                print(f"  FAIL {u}: {e}")
                fails.append(u)
    print(f"\n完成 {len(results)}/{len(units)}，耗时 {time.time()-t0:.1f}s。失败: {fails or '无'}")
    open(os.path.join(RAW, "last_batch.json"), "w", encoding="utf-8").write(
        json.dumps({"units": units, "results": results, "fails": fails}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
