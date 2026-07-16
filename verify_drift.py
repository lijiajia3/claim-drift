# -*- coding: utf-8 -*-
"""
verify_drift.py — 最小验证:科学 claim 在跨代引用中是否"硬化"(丢限定、变确定)。
自动复刻 Greenberg(2009, BMJ)手工 citation-distortion 的核心信号,但用本地模型在规模上跑。

管线:
  1) 取一个种子论文(DOI/paperId)——其原始 claim 通常是"有限定/有对照"的。
  2) S2 Graph API 拉它的引用上下文(citing sentence + 引用年份),带指数退避应对 429。
  3) 本地 Qwen 对每条 citing sentence 判"确定性等级"(hedged/neutral/definitive)+ 是否因果断言。
  4) 检验:definitive 占比是否随引用年份上升(= claim 随代际硬化 = 传播失真)。
本机、离线分类;仅 API 拉数据。不预设结论,definitive 不升就是诚实 null。
"""
import os, sys, json, re, time, urllib.request, urllib.parse, argparse
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")

API = "https://api.semanticscholar.org/graph/v1"

def _get(url, tries=6):
    for t in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "claim-drift-probe/0.1"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 5 * (t + 1) + 5
                print(f"  [429] backoff {wait}s ({t+1}/{tries})"); time.sleep(wait); continue
            raise
        except Exception as e:
            print(f"  [err] {e}; retry"); time.sleep(3)
    raise RuntimeError("API failed after retries")

def resolve_seed(seed):
    pid = seed if "/" not in seed and len(seed) == 40 else f"DOI:{seed}"
    d = _get(f"{API}/paper/{urllib.parse.quote(pid, safe=':')}?fields=title,year,abstract,citationCount")
    return d

def pull_contexts(pid, want=250):
    out, offset = [], 0
    while len(out) < want:
        url = (f"{API}/paper/{pid}/citations?fields=contexts,intents,isInfluential,"
               f"citingPaper.year,citingPaper.title&limit=100&offset={offset}")
        d = _get(url)
        data = d.get("data", [])
        if not data: break
        for it in data:
            yr = (it.get("citingPaper") or {}).get("year")
            for ctx in (it.get("contexts") or []):
                if yr and len(ctx) > 40:
                    out.append({"year": yr, "ctx": ctx.strip()})
        offset += 100
        if "next" not in d: break
        time.sleep(4.0)
    return out[:want]

CLS_SYS = ("You classify how a citing sentence states a scientific finding. Output ONLY JSON "
           "{\"certainty\":\"hedged|neutral|definitive\",\"causal\":true|false}. "
           "hedged = uses may/might/suggests/associated/could; definitive = states as established "
           "fact/causes/proves/demonstrates; neutral otherwise.")

def build_clf():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    name = "Qwen/Qwen2.5-1.5B-Instruct"
    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(name)
    model = AutoModelForCausalLM.from_pretrained(
        name, torch_dtype=torch.float16 if dev == "mps" else torch.float32).to(dev).eval()
    def clf(sent):
        msgs = [{"role": "system", "content": CLS_SYS}, {"role": "user", "content": sent[:600]}]
        text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inp = tok(text, return_tensors="pt").to(dev)
        with torch.no_grad():
            out = model.generate(**inp, max_new_tokens=40, do_sample=False, pad_token_id=tok.eos_token_id)
        raw = tok.decode(out[0][inp["input_ids"].shape[1]:], skip_special_tokens=True)
        m = re.search(r"\{.*\}", raw, re.S)
        try:
            o = json.loads(m.group(0)); return o.get("certainty", "neutral"), bool(o.get("causal"))
        except Exception:
            return "neutral", False
    return clf

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", default="10.1177/0956797610383437",
                    help="DOI or 40-char S2 paperId (default: Carney 2010 power-posing)")
    ap.add_argument("--want", type=int, default=200)
    a = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    print("[seed] resolving", a.seed)
    s = resolve_seed(a.seed)
    print(f"  title: {s.get('title')}  year={s.get('year')}  citations={s.get('citationCount')}")
    pid = s["paperId"]
    print("[pull] citation contexts ...")
    ctxs = pull_contexts(pid, a.want)
    print(f"  got {len(ctxs)} dated contexts")
    if len(ctxs) < 30:
        print("  too few contexts; try another seed");
    json.dump({"seed": s, "contexts": ctxs}, open(os.path.join(here, "contexts.json"), "w"),
              ensure_ascii=False, indent=2)

    clf = build_clf()
    for i, c in enumerate(ctxs):
        cert, caus = clf(c["ctx"])
        c["certainty"], c["causal"] = cert, caus
        if i % 25 == 0: print(f"  clf {i}/{len(ctxs)}")

    # 按年份分早/晚半，看 definitive 占比是否上升
    yrs = sorted(set(c["year"] for c in ctxs))
    if len(ctxs) >= 20 and len(yrs) >= 3:
        med = sorted(c["year"] for c in ctxs)[len(ctxs)//2]
        early = [c for c in ctxs if c["year"] < med]
        late = [c for c in ctxs if c["year"] >= med]
        def defrac(g): return sum(c["certainty"] == "definitive" for c in g)/len(g) if g else float("nan")
        def caus(g): return sum(c["causal"] for c in g)/len(g) if g else float("nan")
        res = {"seed_title": s.get("title"), "n": len(ctxs), "year_split": med,
               "early_n": len(early), "late_n": len(late),
               "definitive_frac_early": round(defrac(early), 3),
               "definitive_frac_late": round(defrac(late), 3),
               "causal_frac_early": round(caus(early), 3),
               "causal_frac_late": round(caus(late), 3),
               "hardening_delta": round(defrac(late) - defrac(early), 3)}
    else:
        res = {"note": "insufficient contexts/years", "n": len(ctxs)}
    json.dump({"summary": res, "contexts": ctxs}, open(os.path.join(here, "drift_result.json"), "w"),
              ensure_ascii=False, indent=2)
    print("\n=== RESULT ===")
    print(json.dumps(res, ensure_ascii=False, indent=2))
    if "hardening_delta" in res:
        d = res["hardening_delta"]
        print(f"\n解读:definitive(把有限定的原始 claim 说成既定事实)占比 "
              f"早期 {res['definitive_frac_early']} → 晚期 {res['definitive_frac_late']} "
              f"(Δ={d:+.3f})。")
        print("  Δ>0 = claim 随引用代际硬化(传播失真信号成立);Δ≤0 = 本种子上未显现(诚实 null)。")

if __name__ == "__main__":
    main()
