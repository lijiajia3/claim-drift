# -*- coding: utf-8 -*-
"""fill_numbers.py — 跑批落地后运行:从 out_runall_v2/summary.json 读出 main.tex 每个 [TODO] 应填的值。
只打印对照清单,不自动改 tex(数字进正文前必须人眼过一遍)。"""
import json, os, statistics, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "out_runall_v2", "summary.json")))
seeds = [r for r in d["seeds"] if r.get("beta") is not None]
st = [r for r in seeds if r["arm"] == "stable"]
rv = [r for r in seeds if r["arm"] == "reversed"]
agg = d.get("aggregate", {})

def mean(xs): return statistics.mean(xs) if xs else float("nan")
bs, br = mean([r["beta"] for r in st]), mean([r["beta"] for r in rv])

print("=" * 60)
print("main.tex TODO 对照清单(逐条人工核对后填入)")
print("=" * 60)
print(f"[摘要] N landmark findings        -> {len(d['seeds'])} 个种子(可拟合 {len(seeds)})")
print(f"[摘要] robust findings harden     -> β̄ = {bs:+.3f} (n={len(st)})")
print(f"[摘要] refuted no hardening       -> β̄ = {br:+.3f} (n={len(rv)}) [现文写 -0.003,核对]")
print(f"[摘要] hotness 句是否保留          -> corr = {agg.get('hotness_corr')} (>0 且稳才保留)")
print(f"[Results] refuted n / β̄          -> n={len(rv)}, β̄={br:+.3f}")
print(f"[Results] robust n / β̄ / 倍数     -> n={len(st)}, β̄={bs:+.3f}, 对比={'∞' if abs(br)<1e-9 else f'{bs/abs(br):.0f}×'}")
print(f"[Results] hotness r               -> {agg.get('hotness_corr')}")
for nm in ("h_pylori", "smoking_cancer"):
    r = next((x for x in seeds if x["name"] == nm), None)
    if r: print(f"[Results 案例] {nm:15} -> β={r['beta']:+.4f}, R²={r.get('r2')}, mean_s={r.get('mean_s')}, span={r.get('year_span')}")
print(f"[Discussion] refuted 符号确认       -> β̄={br:+.4f} ({'flat/负,成立' if br <= 0.005 else '⚠️ 为正,措辞要改'})")
print("-" * 60)
print("质量门(不过就别填,回去改架构):")
ok_st = [r for r in st if r.get("year_span") and r["year_span"][1] - r["year_span"][0] >= 6]
print(f"  健康稳定种子(跨度≥6年): {len(ok_st)} 个 -> β̄={mean([r['beta'] for r in ok_st]):+.4f}")
print(f"  判定: {'✅ 好——继续写论文' if ok_st and mean([r['beta'] for r in ok_st]) > 0.01 and br < 0.01 else '❌ 不行——改架构再跑'}")
print("=" * 60)
for r in sorted(seeds, key=lambda x: (x['arm'], x['beta'])):
    print(f"  {r['name']:18} {r['arm']:9} β={r['beta']:+.4f} R²={r.get('r2')} span={r.get('year_span')} assert%={r.get('assert_rate')}")
