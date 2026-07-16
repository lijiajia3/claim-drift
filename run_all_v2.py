# -*- coding: utf-8 -*-
"""
run_all_v2.py — paper6 硬化实验 v2,修掉 v1 夜跑暴露的 4 个设计问题。复用 run_all 的 SEEDS 与路径。
  修1 分层拉取:高被引种子按 offset 分层采样(不再只拿最新两年),拓宽年份窗口。
  修2 主张过滤:两步打分——先判"这句是否在转述该主张本身"(剔除方法学/背景引用),再对转述句打 s。
  修3 消歧:标题搜前若干候选,取【被引最高】的原始版(避免命中重印本)。
  修4 自适应分桶拟合:年份贪心合并成 >=MINBIN 的桶,>=3 桶即可拟合;报饱和水平 mean_s。
另存:seeds_data/scored2_<name>.jsonl、out_runall_v2/summary.json,不覆盖 v1。
运行:  python3.13 run_all_v2.py       重拉高被引种子:  REPULL=1 python3.13 run_all_v2.py
"""
import os, re, json, time, math, statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request, urllib.error, urllib.parse
from run_all import SEEDS, DATADIR, API, S2_KEY, s2_get   # 复用种子与限流拉取

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_runall_v2")
os.makedirs(OUTDIR, exist_ok=True)
WANT    = int(os.environ.get("WANT", "500"))
NSEED   = int(os.environ.get("NSEED", "0"))
MODEL   = os.environ.get("MODEL", "Qwen/Qwen2.5-72B-Instruct")
WORKERS = int(os.environ.get("WORKERS", "8"))
REPULL  = os.environ.get("REPULL", "") == "1"     # 强制重拉(分层)高被引种子
MINBIN  = int(os.environ.get("MINBIN", "8"))
HICITE  = int(os.environ.get("HICITE", "1500"))   # 超过则用分层拉取

# ---------- 修3:消歧解析(取被引最高) ----------
def resolve_seed(sd):
    fields = "title,year,citationCount,externalIds"
    if sd.get("title"):
        q = urllib.parse.quote(sd["title"])
        d = s2_get(f"{API}/paper/search?query={q}&fields={fields}&limit=8")
        if d and d.get("data"):
            cand = [c for c in d["data"] if c.get("citationCount") is not None]
            if cand:
                return max(cand, key=lambda c: c["citationCount"])   # 被引最高 = 原始版
            return d["data"][0]
    return None

# ---------- 修1:分层拉取 ----------
def pull_layered(pid, want, citecount):
    pages = max(1, math.ceil(want/100))
    if citecount and citecount > HICITE and citecount > want*1.5:
        maxoff = min(int(citecount)-100, 9000)                       # S2 硬上限 offset+limit<=10000,留余量到 9000
        offs = sorted(set(int(round(i*maxoff/(pages-1))) for i in range(pages))) if pages>1 else [0]
    else:
        offs = [i*100 for i in range(pages)]
    out = []
    for off in offs:
        d = s2_get(f"{API}/paper/{pid}/citations?fields=contexts,citingPaper.year&limit=100&offset={off}")
        if not d: continue
        for it in d.get("data", []):
            yr = (it.get("citingPaper") or {}).get("year")
            for ctx in (it.get("contexts") or []):
                if yr and len(ctx) > 40:
                    out.append({"year": yr, "ctx": ctx.strip()})
        time.sleep(float(os.environ.get("S2_PAGE_SLEEP","7")))
    # 去重
    seen=set(); uniq=[]
    for c in out:
        k=(c["year"], c["ctx"][:80])
        if k not in seen: seen.add(k); uniq.append(c)
    return uniq

# ---------- 修2:两步打分(主张判定 + 强度) ----------
SYS = (
  "You analyse ONE sentence that cites a specific prior finding. Do TWO things, output ONLY compact JSON.\n"
  "1) \"assert\": 1 if the sentence RESTATES or PARAPHRASES the finding's CLAIM (what was found / what causes what), "
  "0 if it only cites the work as a method/tool/paradigm/dataset/example or as generic background WITHOUT restating the claim.\n"
  "2) \"s\": if assert=1, rate how CERTAIN/UNIVERSAL the claim is stated, 0..1 "
  "(0.0 fully hedged 'may be associated'; 0.5 neutral; 1.0 definitive/causal 'X causes Y'/'it is established that'). "
  "If assert=0, set s to null.\n"
  "Judge rhetoric, not truth. Output: {\"assert\":0|1,\"s\":<float 0..1 or null>}."
)

def make_scorer():
    import openai
    key = os.environ.get("SILICONFLOW_API_KEY","") or open(os.path.expanduser("~/.siliconflow_key")).read().strip()
    cl = openai.OpenAI(api_key=key, base_url="https://api.siliconflow.cn/v1", timeout=120)
    kw = {"extra_body":{"enable_thinking":False}} if "Qwen3" in MODEL else {}
    def score(text):
        for a in range(5):
            try:
                r = cl.chat.completions.create(model=MODEL,
                    messages=[{"role":"system","content":SYS},{"role":"user","content":text[:700]}],
                    temperature=0.0, max_tokens=32, **kw)
                raw = r.choices[0].message.content or ""
                asrt = re.search(r'"assert"\s*:\s*([01])', raw)
                sv   = re.search(r'"s"\s*:\s*([01](?:\.\d+)?)', raw)
                if asrt:
                    a1 = int(asrt.group(1))
                    s1 = max(0.0,min(1.0,float(sv.group(1)))) if (a1 and sv) else None
                    return a1, s1
            except Exception:
                time.sleep(4*(a+1))
        return None, None
    return score

def score_seed(name, contexts, scorer):
    jsonl = os.path.join(DATADIR, f"scored2_{name}.jsonl")
    done = {}
    if os.path.exists(jsonl):
        for line in open(jsonl, encoding="utf-8"):
            try: o=json.loads(line); done[o["ctx"]]=o
            except Exception: pass
    todo = [c for c in contexts if c["ctx"] not in done]
    if todo:
        fh = open(jsonl, "a", encoding="utf-8")
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(scorer, c["ctx"]): c for c in todo}
            for i, f in enumerate(as_completed(futs)):
                c = futs[f]; a1, s1 = f.result()
                if a1 is None: continue
                rec = {"year": c["year"], "assert": a1, "s": s1, "ctx": c["ctx"]}
                fh.write(json.dumps(rec, ensure_ascii=False)+"\n"); fh.flush()
                done[c["ctx"]] = rec
                if i % 50 == 0: print(f"    scored {i}/{len(todo)}", flush=True)
        fh.close()
    return [v for v in done.values() if v.get("year")]

# ---------- 修4:自适应分桶 + 只用主张句拟合 β ----------
def fit_beta(scored):
    rows = [r for r in scored if r.get("year") and r.get("assert")==1 and r.get("s") is not None]
    n_all = len([r for r in scored if r.get("year")])
    if len(rows) < 15:
        return {"beta":None, "note":"too few assertion sentences", "n_assert":len(rows), "n_all":n_all}
    # 按【年份】合并:相邻年份并入同一桶,直到该桶 >=MINBIN 句(不是按句数硬切,避免同年凑出假桶)
    by_year = {}
    for r in rows: by_year.setdefault(r["year"], []).append(r["s"])
    bins, cur = [], []
    for yr in sorted(by_year):
        cur.extend((yr, s) for s in by_year[yr])
        if len(cur) >= MINBIN: bins.append(cur); cur=[]
    if cur:
        if bins: bins[-1] += cur
        else: bins = [cur]
    pts = [(statistics.mean(y for y,_ in b), statistics.mean(s for _,s in b), len(b)) for b in bins]
    # 去掉同年退化桶:要求桶中心年份至少 3 个不同值,跨度 >=4 年
    yrs_distinct = len(set(round(p[0]) for p in pts))
    span_yrs = (pts[-1][0]-pts[0][0]) if pts else 0
    if len(pts) < 3 or yrs_distinct < 3 or span_yrs < 4:
        return {"beta":None, "note":"window too narrow", "n_assert":len(rows), "n_all":n_all,
                "bins":len(pts), "year_span":[int(pts[0][0]), int(pts[-1][0])] if pts else None}
    y0 = pts[0][0]
    xs, ys, ws = [], [], []
    for yr, ms, n in pts:
        ms = min(ms, 0.999)
        xs.append(yr-y0); ys.append(math.log(1-ms)); ws.append(n)
    W=sum(ws); mx=sum(w*x for w,x in zip(ws,xs))/W; my=sum(w*y for w,y in zip(ws,ys))/W
    den=sum(w*(x-mx)**2 for w,x in zip(ws,xs))
    if den==0: return {"beta":None, "note":"degenerate", "n_assert":len(rows)}
    slope=sum(w*(x-mx)*(y-my) for w,x,y in zip(ws,xs,ys))/den
    intercept=my-slope*mx
    ss_tot=sum(w*(y-my)**2 for w,y in zip(ws,ys)); ss_res=sum(w*(y-(intercept+slope*x))**2 for w,x,y in zip(ws,xs,ys))
    r2=round(1-ss_res/ss_tot,3) if ss_tot>0 else None
    beta=1-math.exp(slope)
    return {"beta":round(beta,4), "r2":r2, "n_assert":len(rows), "n_all":n_all,
            "assert_rate":round(len(rows)/n_all,2), "bins":len(pts),
            "mean_s":round(statistics.mean(r["s"] for r in rows),3),
            "year_span":[int(pts[0][0]), int(pts[-1][0])]}

def pearson(xs, ys):
    if len(xs)<3: return None
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
    num=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    dx=math.sqrt(sum((x-mx)**2 for x in xs)); dy=math.sqrt(sum((y-my)**2 for y in ys))
    return round(num/(dx*dy),3) if dx>0 and dy>0 else None

def main():
    seeds = SEEDS[:NSEED] if NSEED else SEEDS
    arm_only = os.environ.get("ARM","")
    if arm_only:
        seeds = [s for s in seeds if s["arm"]==arm_only]
    scorer = make_scorer()
    results=[]
    for sd in seeds:
        name, arm = sd["name"], sd["arm"]
        print(f"\n=== [{arm}] {name} ===", flush=True)
        ctx_path = os.path.join(DATADIR, f"contexts_{name}.json")
        meta_path= os.path.join(DATADIR, f"meta_{name}.json")
        meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
        contexts = json.load(open(ctx_path)) if os.path.exists(ctx_path) else []
        # 修1/修3:高被引种子在 REPULL 下重拉(分层),或没缓存时拉取
        need_repull = REPULL and meta.get("citationCount",0) and meta["citationCount"] > HICITE
        if not contexts or need_repull:
            info = resolve_seed(sd)
            if not info or "paperId" not in info:
                print("  [skip] 解析失败"); results.append({"name":name,"arm":arm,"error":"resolve_failed"}); continue
            meta = {"title":info.get("title"),"year":info.get("year"),"citationCount":info.get("citationCount")}
            print(f"  {meta['title'][:55]}  yr={meta['year']}  cites={meta['citationCount']}", flush=True)
            contexts = pull_layered(info["paperId"], WANT, meta.get("citationCount"))
            print(f"  pulled {len(contexts)} (layered={need_repull or (meta.get('citationCount',0)>HICITE)})", flush=True)
            json.dump(contexts, open(ctx_path,"w"), ensure_ascii=False, indent=1)
            json.dump(meta, open(meta_path,"w"), ensure_ascii=False)
            time.sleep(3)
        else:
            print(f"  [cache] {len(contexts)} contexts", flush=True)
        if not contexts: results.append({"name":name,"arm":arm,"error":"no_contexts"}); continue
        scored = score_seed(name, contexts, scorer)
        fit = fit_beta(scored)
        row = {"name":name,"arm":arm,"citationCount":meta.get("citationCount"), **fit}
        results.append(row)
        print(f"  -> beta={fit.get('beta')} R2={fit.get('r2')} assert%={fit.get('assert_rate')} "
              f"bins={fit.get('bins')} span={fit.get('year_span')}", flush=True)

    # 汇总(只用能拟合的)
    ok=[r for r in results if r.get("beta") is not None]
    st=[r["beta"] for r in ok if r["arm"]=="stable"]; rv=[r["beta"] for r in ok if r["arm"]=="reversed"]
    hx=[math.log10(r["citationCount"]) for r in ok if r.get("citationCount")]; hy=[r["beta"] for r in ok if r.get("citationCount")]
    agg={"n_ok":len(ok),
         "beta_stable_mean":round(statistics.mean(st),4) if st else None,
         "beta_stable_median":round(statistics.median(st),4) if st else None,
         "beta_reversed_mean":round(statistics.mean(rv),4) if rv else None,
         "beta_reversed_median":round(statistics.median(rv),4) if rv else None,
         "stable_minus_reversed":round(statistics.mean(st)-statistics.mean(rv),4) if st and rv else None,
         "hotness_corr":pearson(hx,hy)}
    json.dump({"model":MODEL,"seeds":results,"aggregate":agg}, open(os.path.join(OUTDIR,"summary.json"),"w"),
              ensure_ascii=False, indent=2)
    print("\n"+"="*74)
    print(f"{'seed':18}{'arm':9}{'β':>8}{'R²':>7}{'assrt':>6}{'bins':>5}{'span':>12}")
    print("-"*74)
    for r in results:
        b=r.get("beta"); b=f"{b:+.3f}" if isinstance(b,float) else (r.get("error") or r.get("note","—"))[:10]
        sp=r.get("year_span"); sp=f"{sp[0]}-{sp[1]}" if sp else "—"
        print(f"{r['name']:18}{r['arm']:9}{b:>8}{str(r.get('r2','—')):>7}{str(r.get('assert_rate','—')):>6}{str(r.get('bins','—')):>5}{sp:>12}")
    print("="*74)
    print(json.dumps(agg, ensure_ascii=False, indent=2))
    print(f"\n[done] -> {os.path.join(OUTDIR,'summary.json')}")

if __name__ == "__main__":
    main()
