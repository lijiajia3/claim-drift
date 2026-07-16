# -*- coding: utf-8 -*-
"""rescore_multi.py — 多模型稳健性打分器(rescore_deepseek.py 的泛化版)。
用多个不同厂商的大模型,用与 Qwen 完全相同的 prompt,重打全部 v3 句子;
每个模型独立输出到 seeds_data/scored_<tag>_*.jsonl(互不覆盖、逐句断点续跑),
跑完对【每个模型分别】验证:与 Qwen 的一致性 + 是否独立复现组间 null(refuted≈robust)。

运行:  python3 rescore_multi.py            # 跑 MODELS 里所有模型 + 出报告
       python3 rescore_multi.py --report  # 只重算报告,不调 API
需要:  SiliconFlow key(环境变量 SILICONFLOW_API_KEY 或 ~/.siliconflow_key)

⚠️ 下方 MODELS 的 slug 请到 SiliconFlow 模型列表核对确切名称再跑,写错会整轮 404。
   "DeepSeek V4 Flash" / LongCat 的确切 slug 我无法替你确认,占位在此,核对后填入。
"""
import os, re, json, glob, time, statistics, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.abspath(__file__))
WORKERS = int(os.environ.get("WORKERS", "8"))

# 每个 provider 一套端点 + key 来源(环境变量优先,否则读本地文件)
PROVIDERS = {
    "siliconflow": dict(base_url="https://api.siliconflow.cn/v1",   key_env="SILICONFLOW_API_KEY", key_file="~/.siliconflow_key"),
    "longcat":     dict(base_url="https://api.longcat.chat/openai/v1", key_env="LONGCAT_API_KEY", key_file="~/.longcat_key"),
}
# tag(输出命名,勿含空格) : provider + 模型名
MODELS = {
    "ds":      dict(provider="siliconflow", model="deepseek-ai/DeepSeek-V3"),        # DeepSeek-V3:对齐论文已写的第二打分器,勿删
    "dsv4":    dict(provider="siliconflow", model="deepseek-ai/DeepSeek-V4-Flash"),  # DeepSeek-V4-Flash:最新代,堵"模型过时"质疑
    # LongCat-2.0 是推理模型,必须关思考(否则思考token吃光输出→返回空);关后与其他模型一样是"直接判断",可比
    "longcat": dict(provider="longcat",     model="LongCat-2.0", max_tokens=64,
                    extra_body={"chat_template_kwargs": {"enable_thinking": False}}),  # 美团 LongCat-2.0:跨厂独立性
    # "glm":   dict(provider="siliconflow", model="THUDM/glm-4-9b-chat"),            # 备选:再加一个不同厂
}

SYS = (
  "You analyse ONE sentence that cites a specific prior finding. Do TWO things, output ONLY compact JSON.\n"
  "1) \"assert\": 1 if the sentence RESTATES or PARAPHRASES the finding's CLAIM (what was found / what causes what), "
  "0 if it only cites the work as a method/tool/paradigm/dataset/example or as generic background WITHOUT restating the claim.\n"
  "2) \"s\": if assert=1, rate how CERTAIN/UNIVERSAL the claim is stated, 0..1 "
  "(0.0 fully hedged 'may be associated'; 0.5 neutral; 1.0 definitive/causal 'X causes Y'/'it is established that'). "
  "If assert=0, set s to null.\n"
  "Judge rhetoric, not truth. Output: {\"assert\":0|1,\"s\":<float 0..1 or null>}."
)

def client(provider):
    import openai
    p = PROVIDERS[provider]
    key = os.environ.get(p["key_env"], "")
    if not key:
        kf = os.path.expanduser(p["key_file"])
        if os.path.exists(kf): key = open(kf).read().strip()
    if not key:
        raise RuntimeError(f"缺少 {provider} 的 key:设 {p['key_env']} 或写入 {p['key_file']}")
    return openai.OpenAI(api_key=key, base_url=p["base_url"], timeout=120)

def make_scorer(cl, model, extra_body=None, max_tokens=48):
    def score(text):
        for a in range(5):
            try:
                kw = dict(model=model,
                    messages=[{"role": "system", "content": SYS}, {"role": "user", "content": text[:700]}],
                    temperature=0.0, max_tokens=max_tokens)
                if extra_body: kw["extra_body"] = extra_body
                r = cl.chat.completions.create(**kw)
                raw = r.choices[0].message.content or ""
                am = re.search(r'"assert"\s*:\s*([01])', raw)
                sm = re.search(r'"s"\s*:\s*([01](?:\.\d+)?)', raw)
                if am:
                    a1 = int(am.group(1))
                    s1 = max(0.0, min(1.0, float(sm.group(1)))) if (a1 and sm) else None
                    return a1, s1
            except Exception:
                time.sleep(6 * (a + 1))
        return None, None
    return score

def score_model(tag, cfg):
    model = cfg["model"]
    cl = client(cfg["provider"])
    score = make_scorer(cl, model, cfg.get("extra_body"), cfg.get("max_tokens", 48))
    files = sorted(glob.glob(os.path.join(ROOT, "seeds_data/scored2_v3_*.jsonl")))
    print(f"[{tag}] {len(files)} seeds, model={model}", flush=True)
    for fi, f in enumerate(files):
        name = os.path.basename(f)[8:-6]
        out = os.path.join(ROOT, "seeds_data", f"scored_{tag}_{name}.jsonl")
        done = set()
        if os.path.exists(out):
            for L in open(out):
                try: done.add(json.loads(L)["ctx"][:90])
                except Exception: pass
        todo = []
        for L in open(f):
            try:
                o = json.loads(L)
                if o.get("ctx") and o["ctx"][:90] not in done: todo.append(o)
            except Exception: pass
        if todo:
            fh = open(out, "a", encoding="utf-8")
            with ThreadPoolExecutor(max_workers=WORKERS) as ex:
                futs = {ex.submit(score, o["ctx"]): o for o in todo}
                for fut in as_completed(futs):
                    o = futs[fut]; a1, s1 = fut.result()
                    if a1 is None: continue
                    fh.write(json.dumps({"year": o.get("year"), "assert": a1, "s": s1,
                                         "ctx": o["ctx"]}, ensure_ascii=False) + "\n"); fh.flush()
            fh.close()
        print(f"  [{tag} {fi+1}/{len(files)}] {name} (+{len(todo)})", flush=True)

def pearson(ps):
    if len(ps) < 3: return None
    xs=[p[0] for p in ps]; ys=[p[1] for p in ps]
    mx=statistics.mean(xs); my=statistics.mean(ys)
    dx=(sum((x-mx)**2 for x in xs))**.5; dy=(sum((y-my)**2 for y in ys))**.5
    return sum((x-mx)*(y-my) for x,y in zip(xs,ys))/(dx*dy) if dx and dy else None

def report():
    import csv
    seedcsv = os.path.join(ROOT, 'v3_seeds/seeds_v3.csv')
    ARM = {}
    if os.path.exists(seedcsv):
        ARM = {('v3_'+r['name']): r.get('arm','') for r in csv.DictReader(open(seedcsv))}
    files = sorted(glob.glob(os.path.join(ROOT, "seeds_data/scored2_v3_*.jsonl")))
    out = {"baseline": "Qwen2.5-72B (scored2)", "models": {}}
    for tag in MODELS:
        agree=[0,0]; pairs=[]; lv={'robust':[],'refuted':[]}
        for f in files:
            name = os.path.basename(f)[8:-6]
            fm = os.path.join(ROOT, "seeds_data", f"scored_{tag}_{name}.jsonl")
            if not os.path.exists(fm): continue
            q={}; m={}
            for L in open(f):
                try: o=json.loads(L); q[o["ctx"][:90]]=o
                except Exception: pass
            for L in open(fm):
                try: o=json.loads(L); m[o["ctx"][:90]]=o
                except Exception: pass
            ss=[]
            for k,oq in q.items():
                om=m.get(k)
                if not om: continue
                agree[0]+=int(oq.get("assert")==om.get("assert")); agree[1]+=1
                if oq.get("assert")==1 and om.get("assert")==1 and oq.get("s") is not None and om.get("s") is not None:
                    pairs.append((oq["s"], om["s"]))
                if om.get("assert")==1 and om.get("s") is not None: ss.append(om["s"])
            arm = ARM.get(name,"")
            if arm in lv and len(ss)>=15: lv[arm].append(statistics.mean(ss))
        r = pearson(pairs)
        ref = statistics.mean(lv['refuted']) if lv['refuted'] else None
        rob = statistics.mean(lv['robust']) if lv['robust'] else None
        out["models"][tag] = {
            "model": MODELS[tag]["model"],
            "n_covered": agree[1],
            "assert_agreement_vs_qwen": round(agree[0]/agree[1],4) if agree[1] else None,
            "s_pearson_vs_qwen": round(r,4) if r is not None else None,
            "level_refuted": round(ref,4) if ref is not None else None,
            "level_robust": round(rob,4) if rob is not None else None,
            "null_gap_refuted_minus_robust": round(ref-rob,4) if (ref is not None and rob is not None) else None,
            "n_claims": {k:len(v) for k,v in lv.items()},
        }
    json.dump(out, open(os.path.join(ROOT,"out_runall_v3/multi_scorer_result.json"),"w"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print("\n每个模型的 null_gap 越接近 0,越说明'组间无差异'不是单模型产物。MULTI_REPORT_DONE", flush=True)

def main():
    # --only=dsv4,longcat 只跑指定模型;--no-report 跳过末尾报告(并行时用,最后手动 --report 汇总)
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--only="): only = set(a.split("=",1)[1].split(","))
    tags = [t for t in MODELS if (only is None or t in only)]
    if "--report" not in sys.argv:
        for tag in tags:
            try: score_model(tag, MODELS[tag])
            except Exception as e: print(f"[{tag}] 打分中断: {e}", flush=True)
    if "--no-report" not in sys.argv:
        report()

if __name__ == "__main__":
    main()
