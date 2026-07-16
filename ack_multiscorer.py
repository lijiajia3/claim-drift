# -*- coding: utf-8 -*-
"""ack_multiscorer.py — Task B (acknowledgment) multi-model robustness.

Labels the same 150 post-refutation sentences (annotation_package/task_B_sentences.csv)
with four independent LLMs under ONE identical acknowledgment prompt, then reports each
model's acknowledgment rate + inter-model agreement + agreement with the paper's primary
labels (out_runall_v3/ack_rate_modelB.json). Resumable: per-model cache in out_runall_v3/.

Run:  python3 ack_multiscorer.py            # score with APIs + report
      python3 ack_multiscorer.py --report   # recompute report only, no API calls
Needs: ~/.siliconflow_key and ~/.longcat_key (same as rescore_multi.py).
"""
import os, re, json, csv, time, statistics, sys
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "out_runall_v3")
WORKERS = int(os.environ.get("WORKERS", "6"))

PROVIDERS = {
    "siliconflow": dict(base_url="https://api.siliconflow.cn/v1",     key_env="SILICONFLOW_API_KEY", key_file="~/.siliconflow_key"),
    "longcat":     dict(base_url="https://api.longcat.chat/openai/v1", key_env="LONGCAT_API_KEY",     key_file="~/.longcat_key"),
}
# tag : provider + model.  qwen = the paper's PRIMARY scorer (cross-check vs existing labels).
MODELS = {
    "qwen":    dict(provider="siliconflow", model="Qwen/Qwen2.5-72B-Instruct"),
    "ds":      dict(provider="siliconflow", model="deepseek-ai/DeepSeek-V3"),
    "dsv4":    dict(provider="siliconflow", model="deepseek-ai/DeepSeek-V4-Flash"),
    "longcat": dict(provider="longcat",     model="LongCat-2.0", max_tokens=64,
                    extra_body={"chat_template_kwargs": {"enable_thinking": False}}),
}

# Faithful to the paper's Task B definition (Materials and Methods, "Acknowledgment rate"):
# mention of the replication failure, mixed/inconsistent evidence, or any controversy.
SYS = (
  "You read ONE sentence from a scientific paper that cites a specific prior finding. "
  "Output ONLY compact JSON: {\"ack\":0|1}.\n"
  "Set ack=1 if the sentence MENTIONS that the cited finding FAILED TO REPLICATE, has "
  "MIXED / INCONSISTENT / CONFLICTING evidence, is DISPUTED, QUESTIONED, or CONTROVERSIAL, "
  "or otherwise flags doubt about the finding's validity.\n"
  "Set ack=0 otherwise, including when the sentence simply states the finding, even hedged "
  "wording like 'may' or 'suggests'. Cautious phrasing WITHOUT reference to contrary evidence "
  "is NOT acknowledgment. Judge only what the sentence says."
)

def client(provider):
    import openai
    p = PROVIDERS[provider]
    key = os.environ.get(p["key_env"], "")
    if not key:
        kf = os.path.expanduser(p["key_file"])
        if os.path.exists(kf): key = open(kf).read().strip()
    if not key:
        raise RuntimeError(f"missing key for {provider}: set {p['key_env']} or write {p['key_file']}")
    return openai.OpenAI(api_key=key, base_url=p["base_url"], timeout=120)

def make_scorer(cl, model, extra_body=None, max_tokens=32):
    def score(text):
        for a in range(5):
            try:
                kw = dict(model=model,
                    messages=[{"role": "system", "content": SYS}, {"role": "user", "content": text[:700]}],
                    temperature=0.0, max_tokens=max_tokens)
                if extra_body: kw["extra_body"] = extra_body
                r = cl.chat.completions.create(**kw)
                raw = r.choices[0].message.content or ""
                m = re.search(r'"ack"\s*:\s*([01])', raw)
                if m: return int(m.group(1))
            except Exception:
                time.sleep(6 * (a + 1))
        return None
    return score

def load_sentences():
    path = os.path.join(ROOT, "annotation_package", "task_B_sentences.csv")
    rows = []
    for r in csv.DictReader(open(path, encoding="utf-8-sig")):
        rid = (r.get("id") or "").strip()
        sent = (r.get("sentence") or "").strip()
        if rid and sent: rows.append((rid, sent))
    return rows

def score_model(tag, cfg, rows):
    out = os.path.join(OUT, f"ackB_{tag}.json")
    done = json.load(open(out)) if os.path.exists(out) else {}
    todo = [(rid, s) for rid, s in rows if rid not in done]
    if todo:
        cl = client(cfg["provider"])
        sc = make_scorer(cl, cfg["model"], cfg.get("extra_body"), cfg.get("max_tokens", 32))
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futs = {ex.submit(sc, s): rid for rid, s in todo}
            for fut in as_completed(futs):
                rid = futs[fut]; v = fut.result()
                if v is not None: done[rid] = v
        json.dump(done, open(out, "w"), indent=1)
    print(f"  [{tag}] {cfg['model']}: labeled {len(done)}/{len(rows)}", flush=True)
    return done

def primary_labels():
    p = os.path.join(OUT, "ack_rate_modelB.json")
    if not os.path.exists(p): return {}
    return {rid: int(v) for rid, v in json.load(open(p))}

def report(rows):
    ids = [rid for rid, _ in rows]
    labels = {}
    for tag in MODELS:
        p = os.path.join(OUT, f"ackB_{tag}.json")
        if os.path.exists(p): labels[tag] = json.load(open(p))
    prim = primary_labels()
    print("\n" + "=" * 64)
    print(f"Task B acknowledgment — {len(ids)} sentences, one identical prompt\n")
    print(f"{'model':<26}{'n':>5}{'ack=1':>7}{'rate':>8}")
    for tag in MODELS:
        L = labels.get(tag, {})
        vals = [L[i] for i in ids if i in L]
        pos = sum(vals)
        print(f"{MODELS[tag]['model']:<26}{len(vals):>5}{pos:>7}{pos/len(vals)*100:>7.1f}%" if vals else f"{tag}: no labels")
    if prim:
        pos = sum(prim.get(i, 0) for i in ids)
        print(f"{'[paper primary labels]':<26}{len(prim):>5}{pos:>7}{pos/len(prim)*100:>7.1f}%")
    # pairwise agreement across the 4 fresh models
    tags = [t for t in MODELS if t in labels]
    print("\npairwise agreement (fraction of sentences with identical 0/1):")
    for i, a in enumerate(tags):
        for b in tags[i+1:]:
            common = [x for x in ids if x in labels[a] and x in labels[b]]
            agr = sum(labels[a][x] == labels[b][x] for x in common) / len(common)
            print(f"  {a:<9} vs {b:<9}: {agr*100:.1f}%  (n={len(common)})")
    # agreement of fresh Qwen with paper's stored primary labels (prompt-fidelity check)
    if "qwen" in labels and prim:
        common = [x for x in ids if x in labels["qwen"] and x in prim]
        agr = sum(labels["qwen"][x] == prim[x] for x in common) / len(common)
        print(f"\nfresh Qwen vs paper's stored primary labels: {agr*100:.1f}% agree (n={len(common)})")
    # majority vote over the 4 models
    maj = []
    for x in ids:
        vs = [labels[t][x] for t in tags if x in labels[t]]
        if vs: maj.append(1 if sum(vs) * 2 > len(vs) else 0)
    print(f"\n4-model majority-vote acknowledgment: {sum(maj)}/{len(maj)} = {sum(maj)/len(maj)*100:.1f}%")
    json.dump({"per_model": {MODELS[t]['model']: sum(labels[t][i] for i in ids if i in labels[t]) for t in tags},
               "n": len(ids), "majority_pos": sum(maj)},
              open(os.path.join(OUT, "ackB_multiscorer_result.json"), "w"), indent=1)
    print("ACK_MULTI_DONE", flush=True)

def main():
    rows = load_sentences()
    print(f"loaded {len(rows)} Task B sentences", flush=True)
    if "--report" not in sys.argv:
        for tag in MODELS:
            try: score_model(tag, MODELS[tag], rows)
            except Exception as e: print(f"  [{tag}] interrupted: {e}", flush=True)
    report(rows)

if __name__ == "__main__":
    main()
