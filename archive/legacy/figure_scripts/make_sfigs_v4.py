# -*- coding: utf-8 -*-
"""make_sfigs_v4.py — 15 张补充图重绘(与主图同一 v4 视觉系统)。
S15 升级为四模型稳健性(Qwen + DeepSeek-V3 + DeepSeek-V4-Flash + LongCat-2.0)。
文件名与旧版一致,main.tex 无需改动。运行: python3.13 make_sfigs_v4.py
"""
import json, math, os, statistics, random
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import make_figures_v4 as V

HERE, ROOT = V.HERE, V.ROOT
S, OK, CSV, ARM = V.S, V.OK, V.CSV, V.ARM
VERM, BLUE, INK, MUTED, FAINT, GRID = V.VERM, V.BLUE, V.INK, V.MUTED, V.FAINT, V.GRID
style, panel, save = V.style, V.panel, V.save
half_violin, mean_bar = V.half_violin, V.mean_bar
scored, bins, wfit, proj = V.scored, V.bins, V.wfit, V.proj
for r in OK: r["csv"] = CSV.get(r["name"], {})

def strip_means(ax, groups, ylim=(-.062, .062), jit=.10, seed=1):
    """groups: [(x_center, arm, values)]"""
    random.seed(seed)
    for x0, arm, vs in groups:
        A = ARM[arm]
        ax.scatter([x0 + random.uniform(-jit, jit) for _ in vs], vs, s=10,
                   marker=A["mk"], color=A["c"], alpha=.55, edgecolors="none", zorder=3)
        if vs: mean_bar(ax, x0, statistics.mean(vs), A["c"], half=jit + .06)
    ax.axhline(0, color=INK, lw=.6, ls=(0, (1, 2))); ax.set_ylim(*ylim)

def legend_arms(ax, loc="upper right", fs=6.0):
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker=ARM[a]["mk"], color=ARM[a]["c"], ls="", ms=4.5,
                label=a.capitalize()) for a in ("refuted", "robust")]
    ax.legend(handles=h, frameon=False, fontsize=fs, loc=loc, handlelength=1.2)

# ---------- S1 分项目 ----------
def S1():
    fig, ax = plt.subplots(figsize=(3.8, 2.7)); fig.subplots_adjust(left=.17, right=.97, top=.92, bottom=.15)
    ps = ["RPP", "EERP", "SSRP"]
    gs = []
    for pi, p in enumerate(ps):
        for arm, d in (("refuted", -.17), ("robust", .17)):
            gs.append((pi + d, arm, [r["beta"] for r in OK if proj(r["name"]) == p and r["arm"] == arm]))
    strip_means(ax, gs, jit=.08, seed=11)
    ax.set_xticks(range(len(ps))); ax.set_xticklabels(["Psychology\n(RPP)", "Economics\n(EERP)", "Social sci.\n(SSRP)"], fontsize=6.2)
    ax.set_ylabel("Certainty drift $\\beta$ (per year)"); legend_arms(ax); style(ax)
    save(fig, "S1_project")

# ---------- S2 分学科 ----------
def S2():
    ds = sorted({str(r["csv"].get("discipline", "?")) for r in OK})
    fig, ax = plt.subplots(figsize=(4.2, 2.7)); fig.subplots_adjust(left=.15, right=.97, top=.92, bottom=.17)
    gs = []
    for di, dn in enumerate(ds):
        for arm, d in (("refuted", -.17), ("robust", .17)):
            gs.append((di + d, arm, [r["beta"] for r in OK if str(r["csv"].get("discipline")) == dn and r["arm"] == arm]))
    strip_means(ax, gs, jit=.08, seed=12)
    ax.set_xticks(range(len(ds))); ax.set_xticklabels(ds, fontsize=6.2)
    ax.set_ylabel("Certainty drift $\\beta$ (per year)"); legend_arms(ax); style(ax)
    save(fig, "S2_discipline")

# ---------- S3 s0 vs beta ----------
def S3():
    ok = [r for r in OK if r.get("implied_s0") is not None]
    fig, ax = plt.subplots(figsize=(3.4, 2.8)); fig.subplots_adjust(left=.18, right=.96, top=.92, bottom=.16)
    for r in ok:
        A = ARM[r["arm"]]
        ax.scatter(r["implied_s0"], r["beta"], s=13, marker=A["mk"], color=A["c"], alpha=.6, edgecolors="none")
    ax.axhline(0, color=INK, lw=.6, ls=(0, (1, 2)))
    ax.set_xlabel("Fitted initial certainty $s_0$"); ax.set_ylabel("Certainty drift $\\beta$")
    ax.set_ylim(-.062, .062); legend_arms(ax, loc="upper left"); style(ax)
    save(fig, "S3_s0_beta")

# ---------- S4 断言率 ----------
def S4():
    ok = [r for r in S if r.get("n_assert") and r.get("n_all")]
    fig, ax = plt.subplots(figsize=(3.4, 2.6)); fig.subplots_adjust(left=.15, right=.96, top=.92, bottom=.17)
    for arm in ("refuted", "robust"):
        A = ARM[arm]
        vs = [r["n_assert"] / r["n_all"] for r in ok if r["arm"] == arm]
        ax.hist(vs, bins=12, alpha=.45, color=A["c"], label=arm.capitalize())
    ax.set_xlabel("Assertion-sentence rate per claim"); ax.set_ylabel("Claims")
    ax.legend(frameon=False, fontsize=6.2, handlelength=1.4); style(ax)
    save(fig, "S4_assert_rate")

# ---------- S5 观察窗 ----------
def S5():
    ok = sorted([r for r in OK if r.get("g_range")], key=lambda r: r["g_range"][0])
    fig, ax = plt.subplots(figsize=(4.6, .065 * len(ok) + 1.1))
    fig.subplots_adjust(left=.06, right=.97, top=.94, bottom=.6 / (.065 * len(ok) + 1.1))
    for i, r in enumerate(ok):
        A = ARM[r["arm"]]
        ax.hlines(i, r["g_range"][0], r["g_range"][1], color=A["c"], lw=1.3, alpha=.7)
    ax.set_yticks([]); ax.set_xlabel("Observed span (years since original publication)")
    ax.spines[["left", "top", "right"]].set_visible(False); ax.spines["bottom"].set_color(FAINT)
    ax.grid(axis="x", color=GRID, lw=.5); ax.set_axisbelow(True); ax.tick_params(colors=MUTED)
    legend_arms(ax, loc="lower right", fs=6.4)
    save(fig, "S5_windows")

# ---------- S6 分桶敏感性 ----------
def S6():
    fig, ax = plt.subplots(figsize=(3.4, 2.7)); fig.subplots_adjust(left=.17, right=.96, top=.92, bottom=.16)
    for arm in ("refuted", "robust"):
        A = ARM[arm]; ms = []
        for mb in (6, 8, 12):
            bs = []
            for r in OK:
                b = wfit(bins(scored(r["name"]), mb), r.get("birth") or 2010)
                if b is not None and r["arm"] == arm: bs.append(b)
            ms.append(statistics.mean(bs) if bs else float("nan"))
        ax.plot((6, 8, 12), ms, marker=A["mk"], color=A["c"], lw=1.4, markersize=4.4,
                markeredgecolor="white", markeredgewidth=.5, label=arm.capitalize())
    ax.axhline(0, color=INK, lw=.6, ls=(0, (1, 2)))
    ax.set_xticks((6, 8, 12)); ax.set_ylim(-.03, .03)
    ax.set_xlabel("Minimum sentences per year bin"); ax.set_ylabel("Group mean $\\beta$")
    ax.legend(frameon=False, fontsize=6.2, handlelength=1.4); style(ax)
    save(fig, "S6_binning")

# ---------- S7 n vs R2 ----------
def S7():
    ok = [r for r in OK if r.get("r2") is not None]
    fig, ax = plt.subplots(figsize=(3.4, 2.8)); fig.subplots_adjust(left=.15, right=.96, top=.92, bottom=.16)
    for r in ok:
        A = ARM[r["arm"]]
        ax.scatter(r["n_assert"], r["r2"], s=13, marker=A["mk"], color=A["c"], alpha=.6, edgecolors="none")
    ax.set_xlabel("Assertion sentences per claim $n$"); ax.set_ylabel("Trajectory fit $R^2$")
    ax.set_xscale("log"); legend_arms(ax); style(ax)
    save(fig, "S7_n_r2")

# ---------- S8 最佳拟合轨迹 ----------
def S8():
    cand = sorted(OK, key=lambda r: -(r.get("r2") or 0))[:6]
    fig, axes = plt.subplots(2, 3, figsize=(7.0, 4.2), sharey=True)
    fig.subplots_adjust(left=.07, right=.98, top=.92, bottom=.10, hspace=.45, wspace=.12)
    for ax, r in zip(axes.flat, cand):
        A = ARM[r["arm"]]
        pts = bins(scored(r["name"]), 8)
        ax.scatter([p[0] for p in pts], [p[1] for p in pts],
                   s=[max(7, min(30, p[2] * .8)) for p in pts],
                   color=A["c"], edgecolors="white", linewidths=.5, zorder=3)
        b = r["beta"]; y0 = pts[0][0]; m0 = min(pts[0][1], .95)
        fx = [y0 + t * (pts[-1][0] - y0) / 60 for t in range(61)]
        ax.plot(fx, [1 - (1 - m0) * (1 - b) ** (x - y0) for x in fx], color=INK, lw=.9, alpha=.8, zorder=2)
        t = CSV.get(r["name"], {}).get("title", r["name"][3:])[:34]
        ax.set_title(t + "…", fontsize=5.6, color=A["c"], fontweight="bold", pad=4)
        ax.text(.03, .06, f"$\\beta$={b:+.3f}   $R^2$={r.get('r2', 0):.2f}",
                transform=ax.transAxes, fontsize=5.6, color=MUTED)
        ax.tick_params(labelsize=5.6); style(ax)
        from matplotlib.ticker import MaxNLocator
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=4))
    axes[0][0].set_ylabel("Mean $s$ per bin", fontsize=6.4)
    axes[1][0].set_ylabel("Mean $s$ per bin", fontsize=6.4)
    fig.text(.5, .015, "Year of citing paper  (marker size $\\propto$ sentences per bin; line: fitted saturating drift)",
             ha="center", fontsize=6.6, color=MUTED)
    save(fig, "S8_trajectories")

# ---------- S9 早/晚分布 ----------
def S9():
    pooled = {"robust": [], "refuted": []}
    for r in OK:
        rows = scored(r["name"])
        if not rows: continue
        med = rows[len(rows) // 2][0]
        for y, s in rows: pooled[r["arm"]].append(("early" if y < med else "late", s))
    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.5), sharey=True)
    fig.subplots_adjust(left=.10, right=.97, top=.87, bottom=.19, wspace=.12)
    for ax, arm in zip(axes, ("refuted", "robust")):
        A = ARM[arm]
        for k, ls, alpha in (("early", (0, (3, 2)), .8), ("late", "-", 1)):
            vs = [s for kk, s in pooled[arm] if kk == k]
            ax.hist(vs, bins=20, histtype="step", ls=ls, color=A["c"], lw=1.3,
                    alpha=alpha, label=f"{k} half", density=True)
        ax.set_title(arm.capitalize(), fontsize=7.2, color=A["c"], fontweight="bold")
        ax.set_xlabel("Stated certainty $s$")
        ax.legend(frameon=False, fontsize=6.0, handlelength=1.6); style(ax)
    axes[0].set_ylabel("Density")
    save(fig, "S9_s_dist")

# ---------- S10 引用量 ----------
def S10():
    ok = [r for r in OK if r.get("citationCount")]
    fig, ax = plt.subplots(figsize=(3.4, 2.6)); fig.subplots_adjust(left=.15, right=.96, top=.92, bottom=.17)
    for arm in ("refuted", "robust"):
        A = ARM[arm]
        vs = [math.log10(r["citationCount"]) for r in ok if r["arm"] == arm]
        ax.hist(vs, bins=12, alpha=.45, color=A["c"], label=arm.capitalize())
    ax.set_xlabel("Original paper citations ($\\log_{10}$)"); ax.set_ylabel("Claims")
    ax.legend(frameon=False, fontsize=6.2, handlelength=1.4); style(ax)
    save(fig, "S10_cites")

# ---------- S11 水平 vs 斜率 ----------
def S11():
    ok = [r for r in OK if r.get("mean_s") is not None]
    fig, ax = plt.subplots(figsize=(3.5, 2.9)); fig.subplots_adjust(left=.18, right=.96, top=.92, bottom=.15)
    for r in ok:
        A = ARM[r["arm"]]
        ax.scatter(r["mean_s"], r["beta"], s=13, marker=A["mk"], color=A["c"], alpha=.6, edgecolors="none")
    ax.axhline(0, color=INK, lw=.6, ls=(0, (1, 2)))
    ax.axvline(statistics.median([r["mean_s"] for r in ok]), color=FAINT, lw=.7, ls=":")
    ax.set_xlabel("Mean stated certainty $\\bar{s}$"); ax.set_ylabel("Certainty drift $\\beta$")
    ax.set_ylim(-.062, .062); legend_arms(ax, loc="upper left"); style(ax)
    save(fig, "S11_level_slope")

# ---------- S12 剂量-响应(全体) ----------
def S12():
    pts = []
    for r in OK:
        pr = r["csv"].get("p_rep")
        try: pts.append((float(pr), r["beta"], r["arm"]))
        except Exception: pass
    fig, ax = plt.subplots(figsize=(3.5, 2.8)); fig.subplots_adjust(left=.17, right=.96, top=.92, bottom=.16)
    for p, b, arm in pts:
        A = ARM[arm]
        ax.scatter(min(p, 1), b, s=13, marker=A["mk"], color=A["c"], alpha=.6, edgecolors="none")
    ax.axhline(0, color=INK, lw=.6, ls=(0, (1, 2))); ax.axvline(.05, color=INK, lw=.7, ls=":")
    ax.text(.08, .052, "replication\n$p=0.05$", fontsize=5.8, color=MUTED, va="top", linespacing=1.25)
    ax.set_xlabel("Replication $p$-value"); ax.set_ylabel("Certainty drift $\\beta$")
    ax.set_ylim(-.062, .062); style(ax)
    save(fig, "S12_dose")

# ---------- S13 高R²子集 ----------
def S13():
    hi = [r for r in OK if (r.get("r2") or 0) >= .1]
    fig, ax = plt.subplots(figsize=(3.0, 2.7)); fig.subplots_adjust(left=.20, right=.95, top=.92, bottom=.14)
    gs = [(j, arm, [r["beta"] for r in hi if r["arm"] == arm]) for j, arm in enumerate(("refuted", "robust"))]
    strip_means(ax, gs, jit=.11, seed=13)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Refuted", "Robust"]); ax.set_xlim(-.55, 1.55)
    ax.set_ylabel("Certainty drift $\\beta$,  $R^2\\geq0.1$ subset"); style(ax)
    save(fig, "S13_hiR2")

# ---------- S14 发表年 ----------
def S14():
    ok = [r for r in OK if r.get("birth")]
    fig, ax = plt.subplots(figsize=(3.4, 2.7)); fig.subplots_adjust(left=.17, right=.96, top=.92, bottom=.16)
    for r in ok:
        A = ARM[r["arm"]]
        ax.scatter(r["birth"], r["beta"], s=13, marker=A["mk"], color=A["c"], alpha=.6, edgecolors="none")
    ax.axhline(0, color=INK, lw=.6, ls=(0, (1, 2)))
    ax.set_xlabel("Original paper publication year"); ax.set_ylabel("Certainty drift $\\beta$")
    ax.set_ylim(-.062, .062); legend_arms(ax, loc="upper left"); style(ax)
    save(fig, "S14_birthyear")

# ---------- S15 四模型稳健性 ----------
def S15():
    pairs = json.load(open(os.path.join(ROOT, "out_runall_v3", "scorer_pairs.json")))
    M = json.load(open(os.path.join(ROOT, "out_runall_v3", "multi_scorer_result.json")))["models"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.9), gridspec_kw={"width_ratios": [1.05, 1.25]})
    fig.subplots_adjust(left=.08, right=.975, top=.86, bottom=.17, wspace=.34)
    panel(a1, "A", -.16)
    a1.scatter([p[0] for p in pairs], [p[1] for p in pairs], s=3, color=INK, alpha=.04, edgecolors="none")
    a1.plot([0, 1], [0, 1], ls="--", lw=1, color=VERM)
    a1.text(.03, .97, "Spearman $\\rho$ = 0.54\nassertion agreement 86%", transform=a1.transAxes,
            fontsize=6.2, va="top", linespacing=1.35, color=MUTED)
    a1.set_xlabel("Primary scorer (Qwen2.5-72B) $s$"); a1.set_ylabel("DeepSeek-V3 $s$")
    a1.set_xlim(-.05, 1.05); a1.set_ylim(-.05, 1.05); style(a1, grid_axis=None)
    # B 四模型哑铃
    panel(a2, "B", -.14)
    rows = [("Qwen2.5-72B\n(primary, Alibaba)", .568, .564),
            ("LongCat-2.0\n(Meituan)", M["longcat"]["level_refuted"], M["longcat"]["level_robust"]),
            ("DeepSeek-V4-Flash", M["dsv4"]["level_refuted"], M["dsv4"]["level_robust"]),
            ("DeepSeek-V3", M["ds"]["level_refuted"], M["ds"]["level_robust"])]
    for i, (lab, ref, rob) in enumerate(rows):
        a2.plot([rob, ref], [i, i], color=FAINT, lw=1.6, zorder=2)
        a2.scatter(ref, i, s=34, marker="D", color=VERM, zorder=3, edgecolors="white", linewidths=.5)
        a2.scatter(rob, i, s=34, marker="o", color=BLUE, zorder=3, edgecolors="white", linewidths=.5)
        gap = ref - rob
        a2.text(max(ref, rob) + .022, i, f"$\\Delta$={gap:+.4f}", va="center", fontsize=6.0, color=MUTED)
    a2.set_yticks(range(len(rows))); a2.set_yticklabels([r[0] for r in rows], fontsize=6.2)
    a2.set_xlabel("Group mean stated certainty")
    a2.set_xlim(.53, .80)
    from matplotlib.lines import Line2D
    a2.legend(handles=[Line2D([], [], marker="D", color=VERM, ls="", ms=4.5, label="Refuted"),
                       Line2D([], [], marker="o", color=BLUE, ls="", ms=4.5, label="Robust")],
              frameon=False, fontsize=6.0, loc="lower right", handlelength=1.2)
    style(a2, grid_axis="x")
    save(fig, "S15_secondscorer")

if __name__ == "__main__":
    for f in (S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15):
        try: f()
        except Exception:
            import traceback; traceback.print_exc()
