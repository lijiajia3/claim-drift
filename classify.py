# -*- coding: utf-8 -*-
"""classify.py — 离线:读 contexts.json,本地 Qwen 判每条 citing sentence 的确定性,
按年份分箱看 definitive 占比走势(claim 硬化/自我修正的信号)。无网络。"""
import os, sys, json, re
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

CLS_SYS = ("You judge how a citing sentence frames a scientific finding. Output ONLY JSON "
           "{\"certainty\":\"hedged|neutral|definitive\",\"causal\":true|false}. "
           "hedged=may/might/suggests/associated/could/potential; "
           "definitive=states as established fact/causes/proves/demonstrates/shows that; "
           "neutral=reports without strong stance.")

def main():
    cs = json.load(open("contexts.json", encoding="utf-8"))
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

    for i, c in enumerate(cs):
        c["certainty"], c["causal"] = clf(c["ctx"])
        if i % 50 == 0: print(f"  {i}/{len(cs)}", flush=True)

    def frac(g, key, val=True):
        g = [x for x in g if x.get("certainty") is not None]
        if not g: return float("nan")
        if key == "definitive":
            return round(sum(x["certainty"] == "definitive" for x in g) / len(g), 3)
        return round(sum(x["causal"] for x in g) / len(g), 3)

    bins = [("2011-2015", 2011, 2015), ("2016-2020", 2016, 2020), ("2021-2026", 2021, 2026)]
    binrows = []
    for lab, lo, hi in bins:
        g = [c for c in cs if lo <= c["year"] <= hi]
        binrows.append({"bin": lab, "n": len(g),
                        "definitive_frac": frac(g, "definitive"),
                        "causal_frac": frac(g, "causal")})
    med = sorted(c["year"] for c in cs)[len(cs)//2]
    early = [c for c in cs if c["year"] < med]; late = [c for c in cs if c["year"] >= med]
    summary = {"seed": "Power Posing (Carney 2010)", "n": len(cs), "year_median": med,
               "definitive_early": frac(early, "definitive"),
               "definitive_late": frac(late, "definitive"),
               "hardening_delta": round(frac(late, "definitive") - frac(early, "definitive"), 3),
               "bins": binrows}
    json.dump({"summary": summary, "contexts": cs}, open("drift_result.json", "w"),
              ensure_ascii=False, indent=2)
    print("\n=== RESULT ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
