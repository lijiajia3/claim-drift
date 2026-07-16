# -*- coding: utf-8 -*-
"""run_all_v3.py — v3 架构:复现项目 135 种子(seeds_v3.csv,客观组别)。
  解析 = 精确标题匹配 + 年份校验(±2)兜底最高被引;拉取 = 中引直拉/高引分层;
  打分 = 与 v2 同一模型同一 prompt(Qwen72B 两步);拟合 = 锚定出生年的 β + 水平 mean_s。
模式:PULL_ONLY=1 只拉不打分(免费,夜磨);默认全流程。断点续跑同 v2。
用法: PULL_ONLY=1 python3.13 run_all_v3.py
"""
import os, csv, json, math, time, statistics
from run_all import DATADIR, API, s2_get
import urllib.parse
from run_all_v2 import pull_layered, make_scorer, score_seed, HICITE

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "out_runall_v3"); os.makedirs(OUTDIR, exist_ok=True)
SEEDCSV = os.path.join(HERE, "v3_seeds", "seeds_v3.csv")
WANT = int(os.environ.get("WANT", "300"))
NSEED = int(os.environ.get("NSEED", "0"))
PULL_ONLY = os.environ.get("PULL_ONLY", "") == "1"
MINBIN = int(os.environ.get("MINBIN", "8"))

def resolve(title, year, mincite=int(os.environ.get("RESOLVE_MINCITE", "20"))):
    """match+search 双路取候选,年份±2 过滤,取被引最高;低于 mincite 视为解析失败(宁缺勿错)。"""
    q = urllib.parse.quote(str(title)[:200])
    fields = "title,year,citationCount"
    cand = []
    d = s2_get(f"{API}/paper/search/match?query={q}&fields={fields}")
    if d and d.get("data"): cand += d["data"]
    d = s2_get(f"{API}/paper/search?query={q}&fields={fields}&limit=10")
    if d and d.get("data"): cand += d["data"]
    ok = [c for c in cand if c.get("year") and abs(int(c["year"]) - int(year)) <= 2
          and c.get("paperId")]
    if not ok: return None
    best = max(ok, key=lambda c: c.get("citationCount") or 0)
    if (best.get("citationCount") or 0) < mincite:
        return None   # 全是低引候选 = 十有八九是错配,宁可弃种
    return best

def fit_v3(scored, birth):
    rows = [r for r in scored if r.get("year") and r.get("assert") == 1 and r.get("s") is not None
            and birth and r["year"] >= birth]
    n_all = len([r for r in scored if r.get("year")])
    if len(rows) < 15: return {"beta": None, "note": "few_assert", "n_assert": len(rows), "n_all": n_all}
    by = {}
    for r in rows: by.setdefault(r["year"], []).append(r["s"])
    bins, cur = [], []
    for yr in sorted(by):
        cur.extend((yr, s) for s in by[yr])
        if len(cur) >= MINBIN: bins.append(cur); cur = []
    if cur:
        if bins: bins[-1] += cur
        else: bins = [cur]
    pts = [(statistics.mean(y for y, _ in b), statistics.mean(s for _, s in b), len(b)) for b in bins]
    span = (pts[-1][0] - pts[0][0]) if pts else 0
    mean_s = round(statistics.mean(r["s"] for r in rows), 3)
    if len(pts) < 3 or len(set(round(p[0]) for p in pts)) < 3 or span < 4:
        return {"beta": None, "note": "narrow", "n_assert": len(rows), "n_all": n_all,
                "mean_s": mean_s, "bins": len(pts)}
    xs = [p[0] - birth for p in pts]; ws = [p[2] for p in pts]
    ys = [math.log(1 - min(p[1], 0.999)) for p in pts]
    W = sum(ws); mx = sum(w*x for w, x in zip(ws, xs))/W; my = sum(w*y for w, y in zip(ws, ys))/W
    den = sum(w*(x-mx)**2 for w, x in zip(ws, xs))
    if den == 0: return {"beta": None, "note": "degenerate", "n_assert": len(rows), "mean_s": mean_s}
    slope = sum(w*(x-mx)*(y-my) for w, x, y in zip(ws, xs, ys))/den
    inter = my - slope*mx
    ss_t = sum(w*(y-my)**2 for w, y in zip(ws, ys))
    ss_r = sum(w*(y-(inter+slope*x))**2 for w, x, y in zip(ws, xs, ys))
    return {"beta": round(1 - math.exp(slope), 4), "implied_s0": round(1 - math.exp(inter), 3),
            "r2": round(1 - ss_r/ss_t, 3) if ss_t > 0 else None, "mean_s": mean_s,
            "n_assert": len(rows), "n_all": n_all, "bins": len(pts),
            "g_range": [int(pts[0][0] - birth), int(pts[-1][0] - birth)]}

def main():
    seeds = list(csv.DictReader(open(SEEDCSV, encoding="utf-8")))
    if NSEED: seeds = seeds[:NSEED]
    scorer = None if PULL_ONLY else make_scorer()
    results, t0 = [], time.time()
    for i, sd in enumerate(seeds):
        name, arm = "v3_" + sd["name"], sd["arm"]
        birth = int(float(sd["year"]))
        ctx_p = os.path.join(DATADIR, f"contexts_{name}.json")
        meta_p = os.path.join(DATADIR, f"meta_{name}.json")
        print(f"\n[{i+1}/{len(seeds)}] [{arm}] {name}", flush=True)
        if os.path.exists(ctx_p):
            contexts = json.load(open(ctx_p))
            meta = json.load(open(meta_p)) if os.path.exists(meta_p) else {}
            print(f"  [cache] {len(contexts)}", flush=True)
        elif os.environ.get("SKIP_MISSING", "") == "1":
            print("  [skip] no cache (SKIP_MISSING)", flush=True)
            results.append({"name": name, "arm": arm, "error": "no_cache"}); continue
        else:
            info = resolve(sd["title"], birth)
            if not info:
                print("  [skip] resolve failed", flush=True)
                results.append({"name": name, "arm": arm, "error": "resolve"}); continue
            meta = {"title": info.get("title"), "year": info.get("year"),
                    "citationCount": info.get("citationCount"), "birth": birth}
            contexts = pull_layered(info["paperId"], WANT, meta.get("citationCount"))
            json.dump(contexts, open(ctx_p, "w"), ensure_ascii=False)
            json.dump(meta, open(meta_p, "w"), ensure_ascii=False)
            print(f"  pulled {len(contexts)} (cites={meta.get('citationCount')})", flush=True)
            time.sleep(3)
        if PULL_ONLY or not contexts:
            results.append({"name": name, "arm": arm, "n_ctx": len(contexts)}); continue
        scored = score_seed(name, contexts, scorer)
        fit = fit_v3(scored, birth)
        results.append({"name": name, "arm": arm, "citationCount": meta.get("citationCount"),
                        "birth": birth, **fit})
        print(f"  -> beta={fit.get('beta')} mean_s={fit.get('mean_s')} n_assert={fit.get('n_assert')}", flush=True)

    out = {"seeds": results}
    if not PULL_ONLY:
        ok = [r for r in results if r.get("beta") is not None]
        rob = [r["beta"] for r in ok if r["arm"] == "robust"]
        ref = [r["beta"] for r in ok if r["arm"] == "refuted"]
        ms_rob = [r["mean_s"] for r in ok if r["arm"] == "robust"]
        ms_ref = [r["mean_s"] for r in ok if r["arm"] == "refuted"]
        out["aggregate"] = {
            "n_ok": len(ok), "n_robust": len(rob), "n_refuted": len(ref),
            "beta_robust_mean": round(statistics.mean(rob), 4) if rob else None,
            "beta_refuted_mean": round(statistics.mean(ref), 4) if ref else None,
            "means_robust_mean_s": round(statistics.mean(ms_rob), 3) if ms_rob else None,
            "means_refuted_mean_s": round(statistics.mean(ms_ref), 3) if ms_ref else None,
        }
        print("\n" + json.dumps(out["aggregate"], indent=1))
    json.dump(out, open(os.path.join(OUTDIR, "summary.json"), "w"), ensure_ascii=False, indent=1)
    print(f"\n[done] {round(time.time()-t0,1)}s -> out_runall_v3/summary.json", flush=True)
    print("V3_STAGE_DONE", flush=True)

if __name__ == "__main__":
    main()
