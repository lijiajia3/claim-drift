# -*- coding: utf-8 -*-
"""
rule_classify.py — 透明·可复现的确定性/因果框架分类(替换不可靠的 1.5B)。
基于 Hyland(2005)学术 hedging/booster 词表 + 因果 vs 关联动词表。
两条轴:
  (1) certainty: hedge 命中 h vs booster 命中 b → hedged / definitive / neutral
  (2) framing:  causal 命中 vs associational 命中 → causal / associational / neutral
用法: python3 rule_classify.py contexts.json  [标签]
"""
import sys, json, re
from collections import Counter

HEDGES = [r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bsuggest", r"\bindicat", r"\bpossib",
          r"\bpotential", r"\bappear", r"\bseem", r"\blikely\b", r"\bperhaps\b", r"\bprobabl",
          r"\btend to\b", r"\bpropos", r"\bassum", r"\bspeculat", r"\bhypothes",
          r"\brelatively\b", r"\bsomewhat\b", r"\bpartially\b", r"\bwould\b",
          r"\bassociat", r"\bcorrelat", r"\blinked\b", r"\brelated to\b",
          r"\bconsistent with\b", r"\braise the possibility", r"\bputativ"]
BOOSTERS = [r"\bdemonstrat", r"\bprov(e|es|en|ing)\b", r"\bshow(s|ed|n)? that\b", r"\bestablish",
            r"\bconfirm", r"\bclearly\b", r"\bdefinit", r"\bundoubted", r"\bevident",
            r"\bconclusiv", r"\bwell[- ]establish", r"\bin fact\b", r"\bindeed\b",
            r"\balways\b", r"\bnecessarily\b", r"\brobust", r"\bstrong evidence\b",
            r"\bunequivocal", r"\bcertain(ly)?\b"]
CAUSAL = [r"\bcaus", r"\blead(s|ing)? to\b", r"\bresult(s|ed|ing)? in\b", r"\bproduc",
          r"\binduc", r"\bdriv(e|es|ing)\b", r"\bresponsible for\b", r"\bdetermin",
          r"\beffect of\b", r"\bimpact of\b", r"\binfluenc", r"\benhanc", r"\bincreas",
          r"\bdecreas", r"\breduc", r"\bimprov", r"\bboost"]
ASSOC = [r"\bassociat", r"\bcorrelat", r"\blinked\b", r"\brelated to\b", r"\brelationship\b",
         r"\bconnection\b", r"\bco-occur", r"\baccompan"]

def hits(text, pats):
    t = text.lower()
    return sum(1 for p in pats if re.search(p, t))

def certainty(text):
    h, b = hits(text, HEDGES), hits(text, BOOSTERS)
    if b > h and b > 0: return "definitive"
    if h > b and h > 0: return "hedged"
    return "neutral"

def framing(text):
    c, a = hits(text, CAUSAL), hits(text, ASSOC)
    if c > a and c > 0: return "causal"
    if a > c and a > 0: return "associational"
    return "neutral"

def analyze(path, label=None):
    cs = json.load(open(path, encoding="utf-8"))
    for c in cs:
        c["cert"] = certainty(c["ctx"]); c["frame"] = framing(c["ctx"])
    ys = sorted(c["year"] for c in cs)
    med = ys[len(ys)//2]
    def frac(g, key, val):
        g = [x for x in g if x["year"]]
        return round(sum(x[key] == val for x in g)/len(g), 3) if g else float("nan")
    early = [c for c in cs if c["year"] < med]; late = [c for c in cs if c["year"] >= med]
    # 年份线性斜率(definitive & causal 占比 vs 年)
    import statistics
    yrs = sorted(set(c["year"] for c in cs))
    def yearfrac(key, val):
        xs, ws = [], []
        for y in yrs:
            g = [c for c in cs if c["year"] == y]
            if len(g) >= 5:
                xs.append((y, sum(c[key] == val for c in g)/len(g), len(g)))
        return xs
    def slope(series):
        if len(series) < 3: return None
        xs = [s[0] for s in series]; ny = [s[1] for s in series]
        mx = sum(xs)/len(xs); my = sum(ny)/len(ny)
        den = sum((x-mx)**2 for x in xs)
        return round(sum((x-mx)*(y-my) for x, y in zip(xs, ny))/den, 5) if den else None
    res = {"label": label or path, "n": len(cs), "median_year": med,
           "definitive_early": frac(early, "cert", "definitive"),
           "definitive_late": frac(late, "cert", "definitive"),
           "definitive_delta": round(frac(late, "cert", "definitive") - frac(early, "cert", "definitive"), 3),
           "causal_early": frac(early, "frame", "causal"),
           "causal_late": frac(late, "frame", "causal"),
           "causal_delta": round(frac(late, "frame", "causal") - frac(early, "frame", "causal"), 3),
           "definitive_slope_per_yr": slope(yearfrac("cert", "definitive")),
           "causal_slope_per_yr": slope(yearfrac("frame", "causal")),
           "cert_dist": dict(Counter(c["cert"] for c in cs)),
           "frame_dist": dict(Counter(c["frame"] for c in cs))}
    return res, cs

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "contexts.json"
    label = sys.argv[2] if len(sys.argv) > 2 else None
    res, _ = analyze(path, label)
    print(json.dumps(res, ensure_ascii=False, indent=2))
