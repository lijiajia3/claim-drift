# -*- coding: utf-8 -*-
"""make_figures_v3.py — v3 全套 18 图(4 主图 + 14 补充图),矢量 PDF + 预览 PNG。
数据:../out_runall_v3/summary.json、../seeds_data/scored2_v3_*.jsonl、../v3_seeds/seeds_v3.csv。
容错:缺哪块数据就跳过对应图并打印原因。跑批落地后:python3.13 make_figures_v3.py
"""
import json, math, os, csv, statistics, glob
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "figs_v3"); os.makedirs(OUT, exist_ok=True)
BLUE, VERM, INK, MUTED, GRID = "#0072B2", "#D55E00", "#1a1a1a", "#555555", "#d9d9d9"
plt.rcParams.update({"font.family": "Helvetica", "font.size": 7.5, "axes.linewidth": 0.6,
                     "pdf.fonttype": 42})

def style(ax, x=True):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x" if x else "y", color=GRID, lw=0.4, alpha=0.7); ax.set_axisbelow(True)

def save(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + "_p.png"), dpi=130); plt.close(fig); print("✓", name)

def col(r): return BLUE if r["arm"] == "robust" else VERM

S = json.load(open(os.path.join(ROOT, "out_runall_v3", "summary.json")))["seeds"] \
    if os.path.exists(os.path.join(ROOT, "out_runall_v3", "summary.json")) else []
OK = [r for r in S if r.get("beta") is not None]
CSVROWS = {("v3_" + r["name"]): r for r in csv.DictReader(open(os.path.join(ROOT, "v3_seeds", "seeds_v3.csv")))}
for r in OK: r["csv"] = CSVROWS.get(r["name"], {})
ROB = [r for r in OK if r["arm"] == "robust"]; REF = [r for r in OK if r["arm"] == "refuted"]
print(f"fitted: {len(OK)} (robust {len(ROB)} / refuted {len(REF)})")

def scored(name):
    p = os.path.join(ROOT, "seeds_data", f"scored2_{name}.jsonl"); rows = []
    if os.path.exists(p):
        for L in open(p):
            try:
                o = json.loads(L)
                if o.get("year") and o.get("assert") == 1 and o.get("s") is not None:
                    rows.append((o["year"], o["s"]))
            except Exception: pass
    return sorted(rows)

def bins(rows, mb=8):
    by = {}; out = []; cur = []
    for y, s in rows: by.setdefault(y, []).append(s)
    for y in sorted(by):
        cur.extend((y, v) for v in by[y])
        if len(cur) >= mb: out.append(cur); cur = []
    if cur and out: out[-1] += cur
    elif cur: out = [cur]
    return [(statistics.mean(y for y, _ in b), statistics.mean(v for _, v in b), len(b)) for b in out]

def wfit(pts, birth):
    xs = [p[0] - birth for p in pts]; ws = [p[2] for p in pts]
    ys = [math.log(1 - min(p[1], .999)) for p in pts]
    W = sum(ws); mx = sum(w*x for w, x in zip(ws, xs))/W; my = sum(w*y for w, y in zip(ws, ys))/W
    den = sum(w*(x-mx)**2 for w, x in zip(ws, xs))
    if den == 0: return None
    sl = sum(w*(x-mx)*(y-my) for w, x, y in zip(ws, xs, ys))/den
    return 1 - math.exp(sl)

# ---------- F1 定律曲线 ----------
def F1():
    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    ends = []
    for b, c in zip((.01, .03, .06, .12), ["#b3cde3", "#6baed6", "#2171b5", "#08306b"]):
        s = [1-(1-.4)*(1-b)**g for g in range(61)]
        ax.plot(range(61), s, color=c, lw=1.6); ends.append([b, s[-1]])
    ends.sort(key=lambda e: e[1])
    for i in range(1, len(ends)):
        if ends[i][1]-ends[i-1][1] < .055: ends[i][1] = ends[i-1][1]+.055
    for b, y in ends: ax.text(62, y, f"$\\beta$={b}", fontsize=7, va="center")
    ax.set_xlim(0, 76); ax.set_xlabel("Citation generation $g$"); ax.set_ylabel("$\\mathbb{E}[s_g]$")
    style(ax, x=False); save(fig, "F1_law")

# ---------- F2 β 森林图 ----------
def F2():
    if not OK: return print("skip F2")
    o = sorted(REF, key=lambda r: r["beta"]) + sorted(ROB, key=lambda r: r["beta"])
    fig, ax = plt.subplots(figsize=(4.8, .05*len(o)+1.1))
    ax.axvline(0, color=GRID, lw=.8)
    for i, r in enumerate(o):
        ax.scatter(r["beta"], i, s=14, marker="o" if r["arm"] == "robust" else "D",
                   color=col(r), edgecolors="white", linewidths=.3, zorder=3)
    for grp, c, lo in ((REF, VERM, 0), (ROB, BLUE, len(REF))):
        if grp:
            m = statistics.mean(r["beta"] for r in grp)
            ax.vlines(m, lo-.4, lo+len(grp)-.6, color=c, lw=2, alpha=.85)
    ax.axhline(len(REF)-.5, color=GRID, lw=.6, ls=":")
    ax.set_yticks([]); ax.set_xlabel("Hardening rate $\\beta$ (per year)")
    ax.legend(handles=[Line2D([0],[0],marker="o",ls="",color=BLUE,label=f"Robust (n={len(ROB)})",markersize=5),
                       Line2D([0],[0],marker="D",ls="",color=VERM,label=f"Refuted (n={len(REF)})",markersize=4.5)],
              frameon=False, fontsize=6.5, loc="lower right")
    ax.spines["left"].set_visible(False); style(ax); save(fig, "F2_forest")

# ---------- F3 mean_s 水平 ----------
def F3():
    ok = [r for r in OK if r.get("mean_s") is not None]
    if not ok: return print("skip F3")
    fig, ax = plt.subplots(figsize=(2.8, 2.6))
    for j, (grp, c) in enumerate(((REF, VERM), (ROB, BLUE))):
        vs = [r["mean_s"] for r in grp if r.get("mean_s") is not None]
        x = [j + (hash(str(v)+str(i)) % 100 - 50)/450 for i, v in enumerate(vs)]
        ax.scatter(x, vs, s=12, color=c, alpha=.65, edgecolors="none")
        ax.hlines(statistics.mean(vs), j-.25, j+.25, color=c, lw=2)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Refuted", "Robust"])
    ax.set_ylabel("Mean stated certainty $\\bar{s}$"); style(ax, x=False); save(fig, "F3_levels")

# ---------- F4 热度散点 ----------
def F4():
    ok = [r for r in OK if r.get("citationCount")]
    if len(ok) < 5: return print("skip F4")
    fig, ax = plt.subplots(figsize=(3.2, 2.6))
    for r in ok:
        ax.scatter(math.log10(r["citationCount"]), r["beta"], s=14,
                   marker="o" if r["arm"] == "robust" else "D", color=col(r), alpha=.7, edgecolors="none")
    ax.axhline(0, color=GRID, lw=.8)
    ax.set_xlabel("log$_{10}$ citations"); ax.set_ylabel("$\\beta$"); style(ax, x=False); save(fig, "F4_hotness")

# ---------- S 系列 ----------
def S1():  # 项目分层
    if not OK: return print("skip S1")
    fig, ax = plt.subplots(figsize=(3.6, 2.6))
    js = {"AER": "EERP", "QJE": "EERP", "Science": "SSRP", "Nature": "SSRP"}
    def proj(r):
        j = str(r["csv"].get("journal", ""))
        for k, v in js.items():
            if k.lower() in j.lower(): return v
        return "RPP"
    ps = ["RPP", "EERP", "SSRP"]
    for pi, p in enumerate(ps):
        for j, (arm, c, d) in enumerate((("refuted", VERM, -.15), ("robust", BLUE, .15))):
            vs = [r["beta"] for r in OK if proj(r) == p and r["arm"] == arm]
            if vs:
                ax.scatter([pi+d]*len(vs), vs, s=10, color=c, alpha=.6, edgecolors="none")
                ax.hlines(statistics.mean(vs), pi+d-.1, pi+d+.1, color=c, lw=2)
    ax.axhline(0, color=GRID, lw=.8); ax.set_xticks(range(len(ps))); ax.set_xticklabels(ps)
    ax.set_ylabel("$\\beta$"); style(ax, x=False); save(fig, "S1_project")

def S2():  # 学科分层
    if not OK: return print("skip S2")
    ds = sorted({str(r["csv"].get("discipline", "?")) for r in OK})
    fig, ax = plt.subplots(figsize=(3.6, 2.6))
    for di, dname in enumerate(ds):
        for arm, c, dd in (("refuted", VERM, -.15), ("robust", BLUE, .15)):
            vs = [r["beta"] for r in OK if str(r["csv"].get("discipline")) == dname and r["arm"] == arm]
            if vs:
                ax.scatter([di+dd]*len(vs), vs, s=10, color=c, alpha=.6, edgecolors="none")
                ax.hlines(statistics.mean(vs), di+dd-.1, di+dd+.1, color=c, lw=2)
    ax.axhline(0, color=GRID, lw=.8); ax.set_xticks(range(len(ds))); ax.set_xticklabels(ds, fontsize=6.5)
    ax.set_ylabel("$\\beta$"); style(ax, x=False); save(fig, "S2_discipline")

def S3():
    ok = [r for r in OK if r.get("implied_s0") is not None]
    if not ok: return print("skip S3")
    fig, ax = plt.subplots(figsize=(3, 2.6))
    for r in ok: ax.scatter(r["implied_s0"], r["beta"], s=12, color=col(r), alpha=.7, edgecolors="none")
    ax.axhline(0, color=GRID, lw=.8); ax.set_xlabel("Implied $s_0$"); ax.set_ylabel("$\\beta$")
    style(ax, x=False); save(fig, "S3_s0_beta")

def S4():
    ok = [r for r in S if r.get("n_assert") and r.get("n_all")]
    if not ok: return print("skip S4")
    fig, ax = plt.subplots(figsize=(3, 2.4))
    for j, (arm, c) in enumerate((("refuted", VERM), ("robust", BLUE))):
        vs = [r["n_assert"]/r["n_all"] for r in ok if r["arm"] == arm]
        if vs:
            ax.hist(vs, bins=12, alpha=.55, color=c, label=arm)
    ax.set_xlabel("Assertion-sentence rate"); ax.set_ylabel("Claims"); ax.legend(frameon=False, fontsize=6.5)
    style(ax, x=False); save(fig, "S4_assert_rate")

def S5():
    ok = [r for r in OK if r.get("g_range")]
    if not ok: return print("skip S5")
    o = sorted(ok, key=lambda r: r["g_range"][0])
    fig, ax = plt.subplots(figsize=(4.2, .07*len(o)+1))
    for i, r in enumerate(o):
        ax.hlines(i, r["g_range"][0], r["g_range"][1], color=col(r), lw=1.2, alpha=.75)
    ax.set_yticks([]); ax.set_xlabel("Observed generations $g$ (years since publication)")
    ax.spines["left"].set_visible(False); style(ax); save(fig, "S5_windows")

def S6():  # 分桶敏感性
    if not OK: return print("skip S6")
    fig, ax = plt.subplots(figsize=(3.2, 2.6))
    mks = (6, 8, 12); rob_m, ref_m = [], []
    for mb in mks:
        bs_r, bs_f = [], []
        for r in OK:
            rows = scored(r["name"]); birth = r.get("birth")
            if not rows or not birth: continue
            pts = bins(rows, mb)
            if len(pts) < 3 or (pts[-1][0]-pts[0][0]) < 4: continue
            b = wfit(pts, birth)
            if b is None: continue
            (bs_r if r["arm"] == "robust" else bs_f).append(b)
        rob_m.append(statistics.mean(bs_r) if bs_r else float("nan"))
        ref_m.append(statistics.mean(bs_f) if bs_f else float("nan"))
    ax.plot(mks, rob_m, "o-", color=BLUE, label="Robust"); ax.plot(mks, ref_m, "D-", color=VERM, label="Refuted")
    ax.axhline(0, color=GRID, lw=.8); ax.set_xlabel("Min sentences per bin"); ax.set_ylabel("Group mean $\\beta$")
    ax.legend(frameon=False, fontsize=6.5); style(ax, x=False); save(fig, "S6_binning")

def S7():
    ok = [r for r in OK if r.get("r2") is not None]
    if not ok: return print("skip S7")
    fig, ax = plt.subplots(figsize=(3, 2.6))
    for r in ok: ax.scatter(r["n_assert"], r["r2"], s=12, color=col(r), alpha=.7, edgecolors="none")
    ax.set_xlabel("Assertion sentences $n$"); ax.set_ylabel("Fit $R^2$"); style(ax, x=False); save(fig, "S7_n_r2")

def S8():  # 六个示例轨迹
    cand = sorted(OK, key=lambda r: -(r.get("r2") or 0))[:6]
    if not cand: return print("skip S8")
    fig, axes = plt.subplots(2, 3, figsize=(7, 4.2))
    for ax, r in zip(axes.flat, cand):
        rows = scored(r["name"]); pts = bins(rows)
        ax.scatter([p[0] for p in pts], [p[1] for p in pts], s=[max(6, min(30, p[2])) for p in pts],
                   color=col(r), edgecolors="white", linewidths=.4, zorder=3)
        b = r["beta"]; y0 = pts[0][0]; m0 = min(pts[0][1], .95)
        fx = [y0+t*(pts[-1][0]-y0)/60 for t in range(61)]
        ax.plot(fx, [1-(1-m0)*(1-b)**(x-y0) for x in fx], color=INK, lw=1)
        ax.set_title(r["name"][3:28].replace("_", " "), fontsize=6, color=MUTED)
        ax.tick_params(labelsize=6); style(ax, x=False)
    save(fig, "S8_trajectories")

def S9():
    pooled = {"robust": [], "refuted": []}
    for r in OK:
        rows = scored(r["name"])
        if not rows: continue
        med = rows[len(rows)//2][0]
        for y, s in rows: pooled[r["arm"]].append(("early" if y < med else "late", s))
    fig, axes = plt.subplots(1, 2, figsize=(5.6, 2.3), sharey=True)
    for ax, arm, c in zip(axes, ("refuted", "robust"), (VERM, BLUE)):
        for k, ls in (("early", ":"), ("late", "-")):
            vs = [s for kk, s in pooled[arm] if kk == k]
            if vs: ax.hist(vs, bins=20, histtype="step", ls=ls, color=c, label=k, density=True)
        ax.set_title(arm, fontsize=7); ax.legend(frameon=False, fontsize=6); style(ax, x=False)
    axes[0].set_ylabel("Density"); save(fig, "S9_s_dist")

def S10():
    ok = [r for r in OK if r.get("citationCount")]
    if not ok: return print("skip S10")
    fig, ax = plt.subplots(figsize=(3, 2.4))
    for arm, c in (("refuted", VERM), ("robust", BLUE)):
        vs = [math.log10(r["citationCount"]) for r in ok if r["arm"] == arm]
        if vs: ax.hist(vs, bins=12, alpha=.55, color=c, label=arm)
    ax.set_xlabel("log$_{10}$ citations"); ax.set_ylabel("Claims"); ax.legend(frameon=False, fontsize=6.5)
    style(ax, x=False); save(fig, "S10_cites")

def S11():
    ok = [r for r in OK if r.get("mean_s") is not None]
    if not ok: return print("skip S11")
    fig, ax = plt.subplots(figsize=(3.2, 2.8))
    for r in ok: ax.scatter(r["mean_s"], r["beta"], s=12, color=col(r), alpha=.7, edgecolors="none")
    ax.axhline(0, color=GRID, lw=.8); ax.axvline(statistics.median([r["mean_s"] for r in ok]), color=GRID, lw=.8, ls=":")
    ax.set_xlabel("Level $\\bar{s}$"); ax.set_ylabel("Slope $\\beta$"); style(ax, x=False); save(fig, "S11_level_slope")

def S12():
    ok = [r for r in OK if r["csv"].get("p_rep") not in (None, "", "nan")]
    pts = []
    for r in ok:
        try: pts.append((float(r["csv"]["p_rep"]), r["beta"]))
        except Exception: pass
    if len(pts) < 5: return print("skip S12")
    fig, ax = plt.subplots(figsize=(3.2, 2.6))
    ax.scatter([min(p, 1) for p, _ in pts], [b for _, b in pts], s=12, color=INK, alpha=.6, edgecolors="none")
    ax.axhline(0, color=GRID, lw=.8); ax.axvline(.05, color=VERM, lw=.8, ls=":")
    ax.set_xlabel("Replication $p$-value"); ax.set_ylabel("$\\beta$"); style(ax, x=False); save(fig, "S12_dose")

def S13():
    hi = [r for r in OK if (r.get("r2") or 0) >= .1]
    if not hi: return print("skip S13")
    fig, ax = plt.subplots(figsize=(2.8, 2.5))
    for j, (arm, c) in enumerate((("refuted", VERM), ("robust", BLUE))):
        vs = [r["beta"] for r in hi if r["arm"] == arm]
        if vs:
            ax.scatter([j]*len(vs), vs, s=12, color=c, alpha=.65, edgecolors="none")
            ax.hlines(statistics.mean(vs), j-.2, j+.2, color=c, lw=2)
    ax.axhline(0, color=GRID, lw=.8); ax.set_xticks([0, 1]); ax.set_xticklabels(["Refuted", "Robust"])
    ax.set_ylabel("$\\beta$ ($R^2\\geq0.1$)"); style(ax, x=False); save(fig, "S13_hiR2")

def S14():
    ok = [r for r in OK if r.get("birth")]
    if not ok: return print("skip S14")
    fig, ax = plt.subplots(figsize=(3, 2.5))
    for r in ok: ax.scatter(r["birth"], r["beta"], s=12, color=col(r), alpha=.7, edgecolors="none")
    ax.axhline(0, color=GRID, lw=.8); ax.set_xlabel("Publication year"); ax.set_ylabel("$\\beta$")
    style(ax, x=False); save(fig, "S14_birthyear")

if __name__ == "__main__":
    for f in (F1, F2, F3, F4, S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14):
        try: f()
        except Exception as e: print("✗", f.__name__, type(e).__name__, str(e)[:80])
