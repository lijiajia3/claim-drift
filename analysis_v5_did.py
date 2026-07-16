# -*- coding: utf-8 -*-
"""analysis_v5_did.py — v5 判决分析:失败复现是否在修辞上留痕。
句子级 DiD:s_ic = α_c + λ·post_t + δ·(post × refuted) + ε,主张固定效应(组内去均值),
δ 的显著性用按主张聚类的 bootstrap(1999 次重抽主张)。附事件研究(相对复现年的逐年 s̄)。
输出:out_runall_v3/did_result.json + 终端报告。跑完打分后运行:python3.13 analysis_v5_did.py
"""
import json, glob, csv, os, random, statistics

ROOT = os.path.dirname(os.path.abspath(__file__))
CSV = {('v3_' + r['name']): r for r in csv.DictReader(open(os.path.join(ROOT, 'v3_seeds/seeds_v3.csv')))}

def repyear(meta):
    j = str(meta.get('journal', '')).lower()
    if 'economic' in j or 'qje' in j: return 2016
    if 'science' in j or 'nature' in j: return 2018
    return 2015

# ---- 组装句子级面板 ----
claims = {}   # name -> dict(arm, ry, rows=[(year, s)])
for f in glob.glob(os.path.join(ROOT, 'seeds_data/scored2_v3_*.jsonl')):
    name = os.path.basename(f)[8:-6]
    meta = CSV.get(name)
    if not meta: continue
    rows = []
    for L in open(f):
        try:
            o = json.loads(L)
            if o.get('assert') == 1 and o.get('s') is not None and o.get('year'):
                rows.append((int(o['year']), float(o['s'])))
        except Exception: pass
    pre = [s for y, s in rows if y < repyear(meta)]
    post = [s for y, s in rows if y >= repyear(meta)]
    if len(pre) >= 10 and len(post) >= 10:      # 预注册式准入:两侧都要有句子
        claims[name] = {'arm': meta['arm'], 'ry': repyear(meta), 'rows': rows}

def did_delta(cl):
    """点估计:句子级 FE-DiD 的 δ = mean_c∈refuted(Δ_c) − mean_c∈robust(Δ_c),
       Δ_c = post 均值 − pre 均值(主张内去均值即 FE;等权主张,避免大主张主导)。"""
    dR, dB = [], []
    for c in cl.values():
        pre = [s for y, s in c['rows'] if y < c['ry']]
        post = [s for y, s in c['rows'] if y >= c['ry']]
        d = statistics.mean(post) - statistics.mean(pre)
        (dR if c['arm'] == 'refuted' else dB).append(d)
    if not dR or not dB: return None, None, None
    return statistics.mean(dR) - statistics.mean(dB), statistics.mean(dR), statistics.mean(dB)

delta, dR, dB = did_delta(claims)
names = list(claims)
R = [n for n in names if claims[n]['arm'] == 'refuted']
B = [n for n in names if claims[n]['arm'] == 'robust']
print(f"claims 准入: {len(names)} (refuted {len(R)} / robust {len(B)})")
print(f"Δ_refuted={dR:+.4f}  Δ_robust={dB:+.4f}  DiD δ={delta:+.4f}")

# ---- 聚类 bootstrap(重抽主张)----
random.seed(7)
BOOT = 1999; bs = []
for _ in range(BOOT):
    samp = {f"r{i}": claims[random.choice(R)] for i in range(len(R))}
    samp.update({f"b{i}": claims[random.choice(B)] for i in range(len(B))})
    d, _, _ = did_delta(samp)
    if d is not None: bs.append(d)
bs.sort()
lo, hi = bs[int(.025 * len(bs))], bs[int(.975 * len(bs))]
p = 2 * min(sum(1 for x in bs if x <= 0), sum(1 for x in bs if x >= 0)) / len(bs)
print(f"95% CI [{lo:+.4f}, {hi:+.4f}]   bootstrap 双侧 p≈{p:.4f}")

# ---- 事件研究:相对复现年的逐年 s̄(按组,主张内去均值后合并)----
ev = {'refuted': {}, 'robust': {}}
for c in claims.values():
    base = statistics.mean(s for _, s in c['rows'])
    for y, s in c['rows']:
        t = y - c['ry']
        if -8 <= t <= 8:
            ev[c['arm']].setdefault(t, []).append(s - base)
series = {arm: {t: (round(statistics.mean(v), 4), len(v)) for t, v in sorted(d.items()) if len(v) >= 30}
          for arm, d in ev.items()}
for arm in ('refuted', 'robust'):
    print(f"\n事件研究 {arm}: " + "  ".join(f"t{t:+d}:{m:+.3f}(n={n})" for t, (m, n) in series[arm].items()))

json.dump({'n_claims': len(names), 'n_refuted': len(R), 'n_robust': len(B),
           'delta_refuted': dR, 'delta_robust': dB, 'did': delta,
           'ci95': [lo, hi], 'p_boot': p, 'event_study': series},
          open(os.path.join(ROOT, 'out_runall_v3/did_result.json'), 'w'), indent=1)
print(f"\n判定: {'✅ 显著——v4 框架成立,重构论文' if p < 0.05 else ('△ 边缘(p<0.15)——看事件研究形状再定' if p < 0.15 else '❌ 不显著——进 v6 或诚实 null')}")
