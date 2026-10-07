# -*- coding: utf-8 -*-
"""assertion_filter_check.py — 审稿硬伤#2:断言过滤器是否系统性地在 refuted 组
更多地剔除"谨慎/加限定"式改写,从而机械地制造零效应。

核心检验:如果对被推翻主张的谨慎改写更容易被判 assert=0(当作背景陈述过滤掉),
那么(a)refuted 组的整体断言率应显著低于 robust 组;(b)更关键——refuted 组的
断言率应在复现事件之后下降(谨慎语言被吸收进 non-assert),而 robust 组不应。
若两条都不成立,则"选择性删除谨慎语言"这一竞争性解释被数据否定。

用与主 DiD 完全相同的打分文件(scored2_v3_*)与事件年(repyear)。
输出:out_runall_v3/assertion_filter_check.json
"""
import json, glob, os, csv, random, statistics

ROOT = os.path.dirname(os.path.abspath(__file__))
CSV = {('v3_' + r['name']): r for r in csv.DictReader(open(os.path.join(ROOT, 'v3_seeds/seeds_v3.csv')))}

def repyear(meta):
    j = str(meta.get('journal', '')).lower()
    if 'economic' in j or 'qje' in j: return 2016
    if 'science' in j or 'nature' in j: return 2018
    return 2015

# claim -> arm, ry, sentences=[(year, assert01)]
claims = {}
for f in glob.glob(os.path.join(ROOT, 'seeds_data/scored2_v3_*.jsonl')):
    name = os.path.basename(f)[8:-6]
    meta = CSV.get(name)
    if not meta:
        continue
    rows = []
    for L in open(f):
        try:
            o = json.loads(L)
            a = o.get('assert')
            y = o.get('year')
            if a in (0, 1) and y:
                rows.append((int(y), int(a)))
        except Exception:
            pass
    if len(rows) >= 20:
        claims[name] = {'arm': meta['arm'], 'ry': repyear(meta), 'rows': rows}

R = [n for n in claims if claims[n]['arm'] == 'refuted']
B = [n for n in claims if claims[n]['arm'] == 'robust']

def rate(names, period=None):
    """断言率 = mean over claims of (assert=1 fraction);等权主张。period='pre'/'post'/None"""
    per = []
    for n in names:
        c = claims[n]
        rows = c['rows']
        if period == 'pre':
            rows = [(y, a) for y, a in rows if y < c['ry']]
        elif period == 'post':
            rows = [(y, a) for y, a in rows if y >= c['ry']]
        if len(rows) >= 5:
            per.append(statistics.mean(a for _, a in rows))
    return statistics.mean(per), len(per)

# (a) 组间整体断言率
aR, nR = rate(R)
aB, nB = rate(B)

# (b) 断言率的 pre/post 变化(每组内),等权主张,聚类 bootstrap 求 Δ(refuted)-Δ(robust)
def delta_assert(names):
    ds = []
    for n in names:
        c = names[n] if isinstance(names, dict) else claims[n]
        c = claims[n]
        pre = [a for y, a in c['rows'] if y < c['ry']]
        post = [a for y, a in c['rows'] if y >= c['ry']]
        if len(pre) >= 5 and len(post) >= 5:
            ds.append((n, statistics.mean(post) - statistics.mean(pre)))
    return ds

dR = delta_assert(R)
dB = delta_assert(B)
mdR = statistics.mean(d for _, d in dR)
mdB = statistics.mean(d for _, d in dB)
did_assert = mdR - mdB

# 聚类 bootstrap 的双侧 p(H0: did_assert=0)
random.seed(11)
rnames = [n for n, _ in dR]
bnames = [n for n, _ in dB]
dmap = dict(dR + dB)
BOOT = 1999
bs = []
for _ in range(BOOT):
    sr = statistics.mean(dmap[random.choice(rnames)] for _ in rnames)
    sb = statistics.mean(dmap[random.choice(bnames)] for _ in bnames)
    bs.append(sr - sb)
bs.sort()
lo, hi = bs[int(0.025 * BOOT)], bs[int(0.975 * BOOT)]
p = 2 * min(sum(1 for x in bs if x >= 0), sum(1 for x in bs if x <= 0)) / BOOT

out = {
    "n_refuted_claims": len(R),
    "n_robust_claims": len(B),
    "assert_rate_refuted": round(aR, 4),
    "assert_rate_robust": round(aB, 4),
    "assert_rate_gap_refuted_minus_robust": round(aR - aB, 4),
    "delta_assert_refuted_post_minus_pre": round(mdR, 4),
    "delta_assert_robust_post_minus_pre": round(mdB, 4),
    "did_assert_rate": round(did_assert, 4),
    "did_assert_ci95": [round(lo, 4), round(hi, 4)],
    "did_assert_p_boot": round(p, 4),
    "interpretation": (
        "If cautious restatements of refuted claims were being selectively dropped by the "
        "assertion filter, refuted claims would show a LOWER assertion rate and a POST-event "
        "DROP in assertion rate relative to robust claims. Observed direction/magnitude below."
    ),
}
os.makedirs(os.path.join(ROOT, 'out_runall_v3'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'out_runall_v3/assertion_filter_check.json'), 'w'),
          ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
