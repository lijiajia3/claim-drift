# -*- coding: utf-8 -*-
"""
run_all.py — paper6「claim 传播硬化」端到端一键跑:
  种子篮子(稳定组 vs 翻车组) → 拉引用上下文 → 连续强度打分 s∈[0,1] → 拟合 β → 两组对比 + 热度相关。

理论(见 THEORY.md):转述信道 E[s'|s]=s+β(1-s),几何硬化 E[s_g]=1-(1-s0)(1-β)^g。
  代际 g 用 (引用年 - 种子年) 作 proxy。对每个种子线性拟合 ln(1-mean_s_g)=ln(1-s0)+g·ln(1-β) → β=1-exp(斜率)。
  预测1:稳定组 β>0 且单调;预测2:被引越热(citationCount 越大)硬化越快;稳定组 β 显著 > 翻车组。

依赖:openai(打分)。其余全用标准库。务必用装了 openai 的解释器:  python3.13 run_all.py
只需 SiliconFlow key(~/.siliconflow_key)。所有路径相对本脚本所在目录,不联网除了 S2 拉数据 + 打分 API。

一键:            python3.13 run_all.py
只重算不重拉:     SKIP_PULL=1 python3.13 run_all.py
先跑前 4 个种子:  NSEED=4 python3.13 run_all.py
每种子多拉点:     WANT=500 python3.13 run_all.py

【重要】拉 S2 数据前先申请免费 API key(否则限流 429 跑不动 20 个种子):
  https://www.semanticscholar.org/product/api  → 存到 ~/.s2_key(或 export S2_API_KEY=...)
  已拉过的种子会缓存到 seeds_data/,断点续跑不重拉;打分也断点续跑。
"""
import os, re, json, time, math, statistics, urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------- 路径:全部相对本脚本所在目录 ----------
HERE   = os.path.dirname(os.path.abspath(__file__))
DATADIR= os.path.join(HERE, "seeds_data")     # 每个种子的 contexts_<name>.json / scored_<name>.jsonl
OUTDIR = os.path.join(HERE, "out_runall")      # 汇总结果
os.makedirs(DATADIR, exist_ok=True); os.makedirs(OUTDIR, exist_ok=True)

# ---------- 可编辑的种子篮子 ----------
# arm: "stable"=未被推翻(预期硬化 β>0);"reversed"=已翻车/自我修正(对照,预期 β≈0 或变软)。
# 组别是【假设】不是真值;DOI 若解析失败该种子会被跳过并记录,不影响其余。你可自由增删。
SEEDS = [
    # —— 翻车 / 自我修正组(对照,预期 β≈0)——
    {"name":"power_posing",   "arm":"reversed", "title":"Power posing: brief nonverbal displays affect neuroendocrine levels and risk tolerance"},  # Carney 2010
    {"name":"ego_depletion",  "arm":"reversed", "title":"Ego depletion: is the active self a limited resource?"},                                  # Baumeister 1998
    {"name":"facial_feedback","arm":"reversed", "title":"Inhibiting and facilitating conditions of the human smile: a nonobtrusive test of the facial feedback hypothesis"}, # Strack 1988
    {"name":"bem_precognition","arm":"reversed","title":"Feeling the future: experimental evidence for anomalous retroactive influences on cognition and affect"},          # Bem 2011
    {"name":"elderly_priming","arm":"reversed", "title":"Automaticity of social behavior: Direct effects of trait construct and stereotype activation on action"},          # Bargh 1996
    {"name":"money_priming",  "arm":"reversed", "title":"The Psychological Consequences of Money"},                                # Vohs 2006
    {"name":"glucose_willpower","arm":"reversed","title":"Self-control relies on glucose as a limited energy source: Willpower is more than a metaphor"},                   # Gailliot 2007
    {"name":"oxytocin_trust", "arm":"reversed", "title":"Oxytocin increases trust in humans"},                                     # Kosfeld 2005
    {"name":"marshmallow",    "arm":"reversed", "title":"Predicting adolescent cognitive and self-regulatory competencies from preschool delay of gratification"},          # Shoda&Mischel 1990
    {"name":"stereotype_threat","arm":"reversed","title":"Stereotype threat and the intellectual test performance of African Americans"},                                   # Steele&Aronson 1995
    {"name":"mozart_effect",  "arm":"reversed", "title":"Music and spatial task performance"},                                     # Rauscher 1993
    {"name":"stanford_prison","arm":"reversed", "title":"Interpersonal dynamics in a simulated prison"},                           # Haney&Zimbardo 1973
    # —— 稳定 / 未翻车组(预期硬化 β>0)——
    {"name":"prospect_theory","arm":"stable",   "title":"Prospect Theory: An Analysis of Decision under Risk"},                    # Kahneman&Tversky 1979
    {"name":"cognitive_diss", "arm":"stable",   "title":"Cognitive consequences of forced compliance"},                           # Festinger&Carlsmith 1959
    {"name":"stroop",         "arm":"stable",   "title":"Studies of interference in serial verbal reactions"},                     # Stroop 1935
    {"name":"testing_effect", "arm":"stable",   "title":"Test-enhanced learning: Taking memory tests improves long-term retention"}, # Roediger&Karpicke 2006
    {"name":"anchoring",      "arm":"stable",   "title":"Judgment under Uncertainty: Heuristics and Biases"},                      # Tversky&Kahneman 1974
    {"name":"framing",        "arm":"stable",   "title":"The framing of decisions and the psychology of choice"},                  # T&K 1981
    {"name":"serial_position","arm":"stable",   "title":"The serial position effect of free recall"},                              # Murdock 1962
    {"name":"spacing_effect", "arm":"stable",   "title":"Distributed practice in verbal recall tasks: A review and quantitative synthesis"}, # Cepeda 2006
    {"name":"endowment",      "arm":"stable",   "title":"Experimental Tests of the Endowment Effect and the Coase Theorem"},       # Kahneman-Knetsch-Thaler 1990
    {"name":"smoking_cancer", "arm":"stable",   "title":"Smoking and Carcinoma of the Lung"},                                      # Doll&Hill 1950
    {"name":"h_pylori",       "arm":"stable",   "title":"Unidentified curved bacilli in the stomach of patients with gastritis and peptic ulceration"},                     # Marshall&Warren 1984
    {"name":"flynn_effect",   "arm":"stable",   "title":"Massive IQ gains in 14 nations: What IQ tests really measure"},           # Flynn 1987
]
# 注:用 title-match 解析种子(比 DOI 稳,S2 对一些老经典的 DOI/年份不可靠)。种子年份仅作元数据,
# β 拟合用【引用年】自身当横轴(见 fit_beta),所以即便 S2 把老论文标成重印年,β 也不受影响。

API   = "https://api.semanticscholar.org/graph/v1"
# 可选 S2 API key(强烈建议):无 key 时共享池限流很凶(429),20 个种子几乎跑不动。
# 免费申请 https://www.semanticscholar.org/product/api,放到 ~/.s2_key 或 export S2_API_KEY=...
S2_KEY = os.environ.get("S2_API_KEY","") or (
    open(os.path.expanduser("~/.s2_key")).read().strip() if os.path.exists(os.path.expanduser("~/.s2_key")) else "")
WANT  = int(os.environ.get("WANT", "300"))     # 每种子想要的上下文数
NSEED = int(os.environ.get("NSEED", "0"))      # 0=全部
MODEL = os.environ.get("MODEL", "Qwen/Qwen2.5-72B-Instruct")
WORKERS = int(os.environ.get("WORKERS", "8"))
SKIP_PULL = os.environ.get("SKIP_PULL", "") == "1"

# ---------- S2 拉取(带退避) ----------
def s2_get(url, tries=int(os.environ.get("S2_TRIES","14")), wait=int(os.environ.get("S2_WAIT","35"))):
    hdr = {"User-Agent":"claim-drift/1.0"}
    if S2_KEY: hdr["x-api-key"] = S2_KEY
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers=hdr)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"    [429] wait {wait}s ({t+1}/{tries})", flush=True); time.sleep(wait); continue
            if e.code == 404:
                return None
            # 其它 4xx/5xx(含 400 offset 越界)不抛异常,返回 None 让调用方跳过该页,别崩整个跑批
            print(f"    [HTTP {e.code}] skip page", flush=True)
            return None
        except Exception as e:
            print(f"    [err] {e}; wait 10s", flush=True); time.sleep(10)
    return None

def resolve_seed(sd):
    """优先 title-match(对老经典比 DOI 稳);没 title 再退回 DOI。返回含 paperId 的 dict 或 None。"""
    fields = "title,year,citationCount,externalIds"
    if sd.get("title"):
        q = urllib.parse.quote(sd["title"])
        d = s2_get(f"{API}/paper/search/match?query={q}&fields={fields}")
        if d and d.get("data"):
            return d["data"][0]
    if sd.get("doi"):
        pid = urllib.parse.quote(f"DOI:{sd['doi']}", safe=':')
        d = s2_get(f"{API}/paper/{pid}?fields={fields}")
        if d and d.get("paperId"):
            return d
    return None

def pull_contexts(pid, want):
    out, offset = [], 0
    while len(out) < want:
        url = (f"{API}/paper/{pid}/citations?fields=contexts,citingPaper.year"
               f"&limit=100&offset={offset}")
        d = s2_get(url)
        if not d: break
        data = d.get("data", [])
        if not data: break
        for it in data:
            yr = (it.get("citingPaper") or {}).get("year")
            for ctx in (it.get("contexts") or []):
                if yr and len(ctx) > 40:
                    out.append({"year": yr, "ctx": ctx.strip()})
        offset += 100
        if len(data) < 100: break
        time.sleep(float(os.environ.get("S2_PAGE_SLEEP","7")))   # keyless 共享池:翻页间隔放缓,少触发 429
    return out[:want]

# ---------- 连续强度打分 ----------
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

def make_scorer():
    import openai
    key = os.environ.get("SILICONFLOW_API_KEY","") or open(os.path.expanduser("~/.siliconflow_key")).read().strip()
    cl = openai.OpenAI(api_key=key, base_url="https://api.siliconflow.cn/v1", timeout=120)
    kw = {"extra_body":{"enable_thinking":False}} if "Qwen3" in MODEL else {}
    def score(text):
        for a in range(5):
            try:
                r = cl.chat.completions.create(
                    model=MODEL,
                    messages=[{"role":"system","content":SYS},{"role":"user","content":text[:700]}],
                    temperature=0.0, max_tokens=32, **kw)
                raw = r.choices[0].message.content or ""
                m = re.search(r'"s"\s*:\s*([01](?:\.\d+)?)', raw)
                if m: return max(0.0, min(1.0, float(m.group(1))))
            except Exception:
                time.sleep(4*(a+1))
        return None
    return score

def score_seed(name, contexts, scorer):
    """对一个种子的上下文打分,断点续跑到 scored_<name>.jsonl。"""
    jsonl = os.path.join(DATADIR, f"scored_{name}.jsonl")
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
                c = futs[f]; s = f.result()
                if s is None: continue
                rec = {"year": c["year"], "s": s, "ctx": c["ctx"]}
                fh.write(json.dumps(rec, ensure_ascii=False)+"\n"); fh.flush()
                done[c["ctx"]] = rec
                if i % 50 == 0: print(f"    scored {i}/{len(todo)}", flush=True)
        fh.close()
    return [v for v in done.values() if v.get("year")]

# ---------- 拟合 β ----------
def fit_beta(scored):
    """横轴用【引用年】自身(不减种子年):x=引用年, 加权线性拟合 ln(1-mean_s_year)=a+b·x,
       β_per_year=1-exp(b)。这样即便 S2 把老论文标成重印年/缺年,β 也不受影响(只是横轴平移)。
       返回 β_per_year, R², n, 早/晚 mean_s。"""
    rows = [r for r in scored if r.get("year")]
    if len(rows) < 20: return {"beta":None, "note":"too few contexts", "n":len(rows)}
    by_y = {}
    for r in rows:
        by_y.setdefault(r["year"], []).append(r["s"])
    pts = [(y, statistics.mean(ss), len(ss)) for y, ss in sorted(by_y.items()) if len(ss) >= 5]
    if len(pts) < 3:
        return {"beta":None, "note":"<3 usable year-bins", "n":len(rows), "yearbins":len(pts)}
    # 加权最小二乘:x=year(去均值以稳数值), y=ln(1-mean_s), w=n
    y0 = pts[0][0]
    xs, ys, ws = [], [], []
    for yr, ms, n in pts:
        ms = min(ms, 0.999)
        xs.append(yr - y0); ys.append(math.log(1-ms)); ws.append(n)
    W = sum(ws); mx = sum(w*x for w,x in zip(ws,xs))/W; my = sum(w*y for w,y in zip(ws,ys))/W
    den = sum(w*(x-mx)**2 for w,x in zip(ws,xs))
    if den == 0: return {"beta":None, "note":"degenerate years", "n":len(rows)}
    slope = sum(w*(x-mx)*(y-my) for w,x,y in zip(ws,xs,ys))/den
    intercept = my - slope*mx
    ss_tot = sum(w*(y-my)**2 for w,y in zip(ws,ys))
    ss_res = sum(w*(y-(intercept+slope*x))**2 for w,x,y in zip(ws,xs,ys))
    r2 = round(1 - ss_res/ss_tot, 3) if ss_tot > 0 else None
    beta = 1 - math.exp(slope)          # slope<0(s 随年份升)→ β>0 硬化
    med = sorted(r["year"] for r in rows)[len(rows)//2]
    early=[r["s"] for r in rows if r["year"]<med]; late=[r["s"] for r in rows if r["year"]>=med]
    return {"beta":round(beta,4), "r2":r2, "n":len(rows), "yearbins":len(pts),
            "year_range":[pts[0][0], pts[-1][0]],
            "mean_s_early":round(statistics.mean(early),3) if early else None,
            "mean_s_late":round(statistics.mean(late),3) if late else None}

# ---------- 汇总统计 ----------
def pearson(xs, ys):
    if len(xs) < 3: return None
    mx=sum(xs)/len(xs); my=sum(ys)/len(ys)
    num=sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    dx=math.sqrt(sum((x-mx)**2 for x in xs)); dy=math.sqrt(sum((y-my)**2 for y in ys))
    return round(num/(dx*dy),3) if dx>0 and dy>0 else None

def main():
    seeds = SEEDS[:NSEED] if NSEED else SEEDS
    scorer = make_scorer()
    results = []
    for sd in seeds:
        name, arm = sd["name"], sd["arm"]
        ref = sd.get("title") or sd.get("doi") or ""
        print(f"\n=== [{arm}] {name}  ({ref[:50]}) ===", flush=True)
        ctx_path = os.path.join(DATADIR, f"contexts_{name}.json")
        meta_path= os.path.join(DATADIR, f"meta_{name}.json")
        # 1) 拉上下文(缓存)
        if os.path.exists(ctx_path) and (SKIP_PULL or True):
            contexts = json.load(open(ctx_path, encoding="utf-8"))
            meta = json.load(open(meta_path, encoding="utf-8")) if os.path.exists(meta_path) else {}
            print(f"  [cache] {len(contexts)} contexts", flush=True)
        else:
            contexts, meta = [], {}
        if not contexts and not SKIP_PULL:
            info = resolve_seed(sd)
            if not info or "paperId" not in info:
                print(f"  [skip] 种子解析失败,跳过", flush=True)
                results.append({"name":name,"arm":arm,"error":"resolve_failed"}); continue
            meta = {"title":info.get("title"), "year":info.get("year"),
                    "citationCount":info.get("citationCount")}
            print(f"  {meta['title']}  year={meta['year']}  cites={meta['citationCount']}", flush=True)
            contexts = pull_contexts(info["paperId"], WANT)
            print(f"  pulled {len(contexts)} contexts", flush=True)
            json.dump(contexts, open(ctx_path,"w"), ensure_ascii=False, indent=1)
            json.dump(meta, open(meta_path,"w"), ensure_ascii=False, indent=1)
            time.sleep(5)
        if not contexts:
            results.append({"name":name,"arm":arm,"error":"no_contexts"}); continue
        # 2) 打分
        scored = score_seed(name, contexts, scorer)
        # 3) 拟合 β
        fit = fit_beta(scored)
        row = {"name":name, "arm":arm, "seed_year":meta.get("year"),
               "citationCount":meta.get("citationCount"), "n_scored":len(scored), **fit}
        results.append(row)
        print(f"  -> beta={fit.get('beta')}  R2={fit.get('r2')}  "
              f"(n={fit.get('n')}, yearbins={fit.get('yearbins')})", flush=True)

    # 4) 两组对比 + 热度相关
    ok = [r for r in results if r.get("beta") is not None]
    stable = [r["beta"] for r in ok if r["arm"]=="stable"]
    revsd  = [r["beta"] for r in ok if r["arm"]=="reversed"]
    hot_x = [math.log10(r["citationCount"]) for r in ok if r.get("citationCount")]
    hot_y = [r["beta"] for r in ok if r.get("citationCount")]
    agg = {
        "n_seeds_ok": len(ok),
        "beta_stable_mean": round(statistics.mean(stable),4) if stable else None,
        "beta_reversed_mean": round(statistics.mean(revsd),4) if revsd else None,
        "stable_minus_reversed": round(statistics.mean(stable)-statistics.mean(revsd),4) if stable and revsd else None,
        "hotness_corr_logcites_vs_beta": pearson(hot_x, hot_y),
        "prediction1_stable_hardens": (statistics.mean(stable)>0) if stable else None,
        "prediction2_hot_hardens_faster": (pearson(hot_x,hot_y) or 0) > 0 if len(hot_x)>=3 else None,
    }
    out = {"model":MODEL, "seeds":results, "aggregate":agg}
    json.dump(out, open(os.path.join(OUTDIR,"summary.json"),"w"), ensure_ascii=False, indent=2)

    # ---------- 打印表 ----------
    print("\n" + "="*72)
    print(f"{'seed':<18}{'arm':<10}{'β':>9}{'R²':>7}{'cites':>8}{'n':>6}")
    print("-"*72)
    for r in results:
        b = r.get("beta"); b = f"{b:+.3f}" if isinstance(b,float) else (r.get("error") or "—")
        print(f"{r['name']:<18}{r['arm']:<10}{b:>9}{str(r.get('r2','—')):>7}"
              f"{str(r.get('citationCount','—')):>8}{str(r.get('n_scored','—')):>6}")
    print("="*72)
    print(json.dumps(agg, ensure_ascii=False, indent=2))
    print(f"\n[done] -> {os.path.join(OUTDIR,'summary.json')}")
    if agg["stable_minus_reversed"] is not None:
        print("\n解读:")
        print(f"  稳定组 β̄={agg['beta_stable_mean']}  vs  翻车组 β̄={agg['beta_reversed_mean']}"
              f"  (差={agg['stable_minus_reversed']:+})")
        print(f"  预测1(稳定组硬化 β>0):{agg['prediction1_stable_hardens']}")
        print(f"  预测2(越热硬化越快,corr>0):{agg['prediction2_hot_hardens_faster']} "
              f"(r={agg['hotness_corr_logcites_vs_beta']})")
        print("  稳定组 β 明显>翻车组 且两条预测都成立 → 往大子刊方向写;否则如实收成中档 null。")

if __name__ == "__main__":
    main()
