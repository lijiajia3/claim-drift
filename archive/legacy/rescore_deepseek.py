# -*- coding: utf-8 -*-
"""rescore_deepseek.py — 第二打分模型稳健性:用 DeepSeek 重打全部 v3 句子(与 Qwen 同一 prompt),
逐句断点续跑到 scored3_v3_*.jsonl;跑完自动出对照分析 second_scorer_result.json。
运行:python3.13 rescore_deepseek.py    (环境变量 MODEL 可换 deepseek-v4-pro)
"""
import os, re, json, glob, time, statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import openai

ROOT = os.path.dirname(os.path.abspath(__file__))
MODEL = os.environ.get("MODEL", "deepseek-ai/DeepSeek-V3")
WORKERS = int(os.environ.get("WORKERS", "8"))

SYS = (
  "You analyse ONE sentence that cites a specific prior finding. Do TWO things, output ONLY compact JSON.\n"
  "1) \"assert\": 1 if the sentence RESTATES or PARAPHRASES the finding's CLAIM (what was found / what causes what), "
  "0 if it only cites the work as a method/tool/paradigm/dataset/example or as generic background WITHOUT restating the claim.\n"
  "2) \"s\": if assert=1, rate how CERTAIN/UNIVERSAL the claim is stated, 0..1 "
  "(0.0 fully hedged 'may be associated'; 0.5 neutral; 1.0 definitive/causal 'X causes Y'/'it is established that'). "
  "If assert=0, set s to null.\n"
  "Judge rhetoric, not truth. Output: {\"assert\":0|1,\"s\":<float 0..1 or null>}."
)

def client():
    key = os.environ.get("SILICONFLOW_API_KEY", "") or open(os.path.expanduser("~/.siliconflow_key")).read().strip()
    return openai.OpenAI(api_key=key, base_url="https://api.siliconflow.cn/v1", timeout=120)

cl = client()
def score(text):
    for a in range(5):
        try:
            r = cl.chat.completions.create(model=MODEL,
                messages=[{"role": "system", "content": SYS}, {"role": "user", "content": text[:700]}],
                temperature=0.0, max_tokens=48)
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

def main():
    t0 = time.time()
    files = sorted(glob.glob(os.path.join(ROOT, "seeds_data/scored2_v3_*.jsonl")))
    print(f"[ds] {len(files)} seeds, model={MODEL}", flush=True)
    for fi, f in enumerate(files):
        name = os.path.basename(f)[8:-6]
        out = os.path.join(ROOT, "seeds_data", f"scored3_{name}.jsonl")
        done = set()
        if os.path.exists(out):
            for L in open(out):
                try: done.add(json.loads(L)["ctx"][:90])
                except Exception: pass
        todo = []
        for L in open(f):
            try:
                o = json.loads(L)
                if o.get("ctx") and o["ctx"][:90] not in done:
                    todo.append(o)
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
        print(f"  [{fi+1}/{len(files)}] {name} done ({len(todo)} new)", flush=True)

    # ---- 对照分析 ----
    import csv
    CSV = {('v3_' + r['name']): r for r in csv.DictReader(open(os.path.join(ROOT, 'v3_seeds/seeds_v3.csv')))}
    pairs = []           # (qwen_s, ds_s) on sentences both call assertion
    agree = [0, 0]       # assert agreement
    lv = {'robust': [], 'refuted': []}   # ds per-claim mean_s
    for f in files:
        name = os.path.basename(f)[8:-6]
        f3 = os.path.join(ROOT, "seeds_data", f"scored3_{name}.jsonl")
        if not os.path.exists(f3): continue
        q = {}; d = {}
        for L in open(f):
            try:
                o = json.loads(L); q[o["ctx"][:90]] = o
            except Exception: pass
        for L in open(f3):
            try:
                o = json.loads(L); d[o["ctx"][:90]] = o
            except Exception: pass
        ss = []
        for k, oq in q.items():
            od = d.get(k)
            if not od: continue
            agree[0] += int(oq.get("assert") == od.get("assert")); agree[1] += 1
            if oq.get("assert") == 1 and od.get("assert") == 1 and oq.get("s") is not None and od.get("s") is not None:
                pairs.append((oq["s"], od["s"]))
            if od.get("assert") == 1 and od.get("s") is not None:
                ss.append(od["s"])
        meta = CSV.get(name)
        if meta and len(ss) >= 15:
            lv[meta['arm']].append(statistics.mean(ss))
    def pear(ps):
        xs = [p[0] for p in ps]; ys = [p[1] for p in ps]
        mx = statistics.mean(xs); my = statistics.mean(ys)
        num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
        dx = (sum((x - mx) ** 2 for x in xs)) ** .5; dy = (sum((y - my) ** 2 for y in ys)) ** .5
        return num / (dx * dy) if dx and dy else None
    res = {"model": MODEL, "n_sentence_pairs": len(pairs),
           "assert_agreement": round(agree[0] / agree[1], 4) if agree[1] else None,
           "s_pearson": round(pear(pairs), 4) if len(pairs) > 30 else None,
           "level_refuted_ds": round(statistics.mean(lv['refuted']), 4) if lv['refuted'] else None,
           "level_robust_ds": round(statistics.mean(lv['robust']), 4) if lv['robust'] else None,
           "n_claims": {k: len(v) for k, v in lv.items()},
           "seconds": round(time.time() - t0, 1)}
    json.dump(res, open(os.path.join(ROOT, "out_runall_v3/second_scorer_result.json"), "w"), indent=1)
    print(json.dumps(res, indent=1)); print("DS_RESCORE_DONE", flush=True)

if __name__ == "__main__":
    main()
