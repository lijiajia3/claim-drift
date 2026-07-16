# -*- coding: utf-8 -*-
"""pull_stable.py — 只拉不打分:把稳定组还缺 contexts 缓存的种子先拉齐(keyless S2,不花打分钱)。
余额恢复后 run_all_v2 直接走缓存进打分。"""
import os, json, time
from run_all_v2 import resolve_seed, pull_layered, HICITE
from run_all import SEEDS, DATADIR

WANT = int(os.environ.get("WANT", "500"))
for sd in [s for s in SEEDS if s["arm"] == "stable"]:
    name = sd["name"]
    ctx_path = os.path.join(DATADIR, f"contexts_{name}.json")
    meta_path = os.path.join(DATADIR, f"meta_{name}.json")
    if os.path.exists(ctx_path):
        try:
            n = len(json.load(open(ctx_path)))
        except Exception:
            n = 0
        if n >= 100:
            print(f"[skip] {name}: cached {n}", flush=True); continue
    info = resolve_seed(sd)
    if not info or "paperId" not in info:
        print(f"[fail] {name}: resolve failed", flush=True); continue
    meta = {"title": info.get("title"), "year": info.get("year"),
            "citationCount": info.get("citationCount")}
    print(f"[pull] {name}: {str(meta['title'])[:50]} cites={meta['citationCount']}", flush=True)
    ctxs = pull_layered(info["paperId"], WANT, meta.get("citationCount"))
    if ctxs:
        json.dump(ctxs, open(ctx_path, "w"), ensure_ascii=False, indent=1)
        json.dump(meta, open(meta_path, "w"), ensure_ascii=False)
        print(f"[done] {name}: {len(ctxs)} contexts", flush=True)
    else:
        print(f"[empty] {name}", flush=True)
    time.sleep(5)
print("PULL_STABLE_FINISHED", flush=True)
