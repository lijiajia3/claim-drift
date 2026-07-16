# -*- coding: utf-8 -*-
"""rescore_strength.py — 诊断跑:用强模型给已抽到的 citing 上下文打【连续】确定性强度 s∈[0,1]
(替换 rule/1.5B 的三分桶),检验 pilot 的 flat null 到底是【仪器地板效应】还是【种子本身】。

理论对齐:s=0 完全限定(hedged),s=1 完全确定/普适(definitive)。见 THEORY.md 的 E[s'|s]=s+β(1-s)。
只需 SiliconFlow key(~/.siliconflow_key)。数据用已存在的 contexts.json,不再联网拉引用。

用法:
  python3 rescore_strength.py               # 全部 397 条,Qwen2.5-72B
  N=50 python3 rescore_strength.py          # 先跑 50 条冒烟
输出:
  strength_scored.jsonl   每条 {year, s, ctx}(可断点续跑)
  strength_result.json    按年 mean s + 线性斜率 + 早/晚对比 + 三分桶对照(看地板效应)
"""
import os, re, json, time, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import openai

HERE = os.path.dirname(os.path.abspath(__file__))
CTX  = os.path.join(HERE, "contexts.json")
JSONL= os.path.join(HERE, "strength_scored.jsonl")
OUT  = os.path.join(HERE, "strength_result.json")
MODEL= os.environ.get("MODEL", "Qwen/Qwen2.5-72B-Instruct")
NLIM = int(os.environ.get("N", "0"))          # 0 = all
WORKERS = int(os.environ.get("WORKERS", "8"))

SYS = (
  "You rate how CERTAIN and UNIVERSAL a citing sentence makes a scientific claim sound, "
  "on a continuous 0..1 scale. Anchor points:\n"
  "0.0 = fully hedged/conditional ('may be associated with', 'could suggest', 'under condition X').\n"
  "0.5 = neutral report, no strong stance ('X was measured', 'X and Y were compared').\n"
  "1.0 = fully definitive/universal/causal, stated as established fact ('X causes Y', 'X proves', "
  "'it is well established that X').\n"
  "Judge the RHETORICAL strength of how the finding is stated, not whether it is true. "
  "Output ONLY compact JSON: {\"s\": <float 0..1>}."
)

def client():
    key = os.environ.get("SILICONFLOW_API_KEY","") or open(os.path.expanduser("~/.siliconflow_key")).read().strip()
    return openai.OpenAI(api_key=key, base_url="https://api.siliconflow.cn/v1", timeout=120)

def score(cl, text):
    kw = {"extra_body":{"enable_thinking":False}} if "Qwen3" in MODEL else {}
    for a in range(5):
        try:
            r = cl.chat.completions.create(
                model=MODEL,
                messages=[{"role":"system","content":SYS},{"role":"user","content":text[:700]}],
                temperature=0.0, max_tokens=32, **kw)
            raw = r.choices[0].message.content or ""
            m = re.search(r'"s"\s*:\s*([01](?:\.\d+)?)', raw)
            if m:
                v = float(m.group(1));  return max(0.0, min(1.0, v))
        except Exception:
            time.sleep(4*(a+1))
    return None

def main():
    raw = json.load(open(CTX, encoding="utf-8"))
    ctxs = raw["contexts"] if isinstance(raw, dict) and "contexts" in raw else raw
    if NLIM: ctxs = ctxs[:NLIM]
    # 断点续跑:已打分的 ctx 文本集合
    done = {}
    if os.path.exists(JSONL):
        for line in open(JSONL, encoding="utf-8"):
            try:
                o = json.loads(line); done[o["ctx"]] = o
            except Exception: pass
    todo = [c for c in ctxs if c["ctx"] not in done]
    print(f"[rescore] model={MODEL}  total={len(ctxs)}  already={len(done)}  todo={len(todo)}", flush=True)

    cl = client()
    t0 = time.time()
    fh = open(JSONL, "a", encoding="utf-8")
    lock_done = dict(done)
    def work(c):
        s = score(cl, c["ctx"])
        return c, s
    n_ok = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(work, c) for c in todo]
        for i, f in enumerate(as_completed(futs)):
            c, s = f.result()
            if s is None:  continue
            rec = {"year": c["year"], "s": s, "ctx": c["ctx"]}
            fh.write(json.dumps(rec, ensure_ascii=False)+"\n"); fh.flush()
            lock_done[c["ctx"]] = rec; n_ok += 1
            if i % 25 == 0: print(f"  {i}/{len(todo)}  s={s:.2f}", flush=True)
    fh.close()

    rows = list(lock_done.values())
    rows = [r for r in rows if r.get("year")]
    # 按年 mean s
    import statistics
    yrs = sorted(set(r["year"] for r in rows))
    per_year = []
    for y in yrs:
        g = [r["s"] for r in rows if r["year"]==y]
        if len(g)>=5: per_year.append({"year":y, "n":len(g), "mean_s":round(statistics.mean(g),3)})
    # 线性斜率 mean_s vs year(仅用 n>=5 的年)
    def slope(series):
        if len(series)<3: return None
        xs=[p["year"] for p in series]; ys=[p["mean_s"] for p in series]
        mx=sum(xs)/len(xs); my=sum(ys)/len(ys); den=sum((x-mx)**2 for x in xs)
        return round(sum((x-mx)*(y-my) for x,y in zip(xs,ys))/den,5) if den else None
    med = sorted(r["year"] for r in rows)[len(rows)//2]
    early=[r["s"] for r in rows if r["year"]<med]; late=[r["s"] for r in rows if r["year"]>=med]
    # 三分桶对照:s>0.66 当作旧口径 "definitive",看地板效应
    def defrac(g): return round(sum(1 for s in g if s>0.66)/len(g),3) if g else None
    summary = {
        "model": MODEL, "n": len(rows), "median_year": med,
        "mean_s_early": round(statistics.mean(early),3) if early else None,
        "mean_s_late":  round(statistics.mean(late),3)  if late else None,
        "mean_s_delta": round((statistics.mean(late)-statistics.mean(early)),3) if early and late else None,
        "mean_s_slope_per_yr": slope(per_year),
        "definitive_frac_early(>0.66)": defrac(early),
        "definitive_frac_late(>0.66)":  defrac(late),
        "per_year": per_year,
    }
    json.dump({"summary":summary,"scored":rows}, open(OUT,"w"), ensure_ascii=False, indent=2)
    print("\n=== RESULT ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n[done] {n_ok} newly scored, {round(time.time()-t0,1)}s -> {OUT}")
    d = summary["mean_s_delta"]
    if d is not None:
        print(f"\n解读: 连续强度 mean s  早 {summary['mean_s_early']} -> 晚 {summary['mean_s_late']} (Δ={d:+.3f}).")
        print("  Δ>0 且斜率>0 = 连续仪器测出了三分桶漏掉的硬化(pilot 的 flat 是地板效应).")
        print("  Δ≈0/<0 = 硬化在此种子上确实不显著 -> 是【种子问题】(Power Posing 是被证伪/自我修正案例),该换 seed 篮子.")

if __name__ == "__main__":
    main()
