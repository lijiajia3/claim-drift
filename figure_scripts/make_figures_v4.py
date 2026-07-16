# -*- coding: utf-8 -*-
"""make_figures_v4.py — 8 张 SciAdv 主图重绘(出版级视觉系统)。
文件名与 v3 相同,main.tex 无需改动。设计系统:
  · Okabe-Ito 色盲安全双色(refuted 朱红 / robust 蓝) + 冗余编码(marker: D vs o)
  · 半小提琴(KDE 轮廓)衬于 strip 之后,分布可见
  · 确定性量尺 Blues 渐变贯穿 Fig1 B/C,视觉线索统一
  · 统一 ink/muted/grid 灰阶,hairline 轴线,panel 标签同一坐标系
运行: python3.13 make_figures_v4.py
"""
import json, math, os, csv, glob, statistics, random, textwrap
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.ticker import MaxNLocator, MultipleLocator

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "figs_v3")

# ---------- 设计系统 ----------
VERM, BLUE = "#D55E00", "#0072B2"           # Okabe-Ito
VERM_L, BLUE_L = "#F4C7A8", "#B7D8EC"        # 浅色填充
INK, MUTED, FAINT = "#16161d", "#6e7480", "#a7adb5"
GRID, PANEL_BG = "#e7e9ec", "#f7f8fa"
CMAP = plt.cm.Blues                           # 确定性量尺
plt.rcParams.update({
    "font.family": "Helvetica Neue", "font.size": 7,
    "axes.linewidth": .5, "axes.edgecolor": INK,
    "xtick.color": INK, "ytick.color": INK,
    "xtick.labelsize": 6.4, "ytick.labelsize": 6.4,
    "axes.labelsize": 7.2, "axes.labelcolor": INK,
    "xtick.major.size": 2.4, "ytick.major.size": 2.4,
    "xtick.major.width": .5, "ytick.major.width": .5,
    "pdf.fonttype": 42, "svg.fonttype": "none",
})

S = json.load(open(os.path.join(ROOT, "out_runall_v3/summary.json")))["seeds"]
D = json.load(open(os.path.join(ROOT, "out_runall_v3/did_result.json")))
CSV = {('v3_' + r['name']): r for r in csv.DictReader(open(os.path.join(ROOT, 'v3_seeds/seeds_v3.csv')))}
OK = [r for r in S if r.get("beta") is not None]
LV = [r for r in S if r.get("mean_s") is not None]

def proj(name):
    j = str(CSV.get(name, {}).get('journal', '')).lower()
    return 'EERP' if ('economic' in j or 'qje' in j) else ('SSRP' if ('science' in j or 'nature' in j) else 'RPP')

_SENT = None
def sentences():
    global _SENT
    if _SENT is None:
        _SENT = []
        for f in glob.glob(os.path.join(ROOT, "seeds_data/scored2_v3_*.jsonl")):
            name = os.path.basename(f)[8:-6]; meta = CSV.get(name)
            if not meta: continue
            for L in open(f):
                try:
                    o = json.loads(L)
                    if o.get("assert") == 1 and o.get("s") is not None:
                        _SENT.append((meta["arm"], o.get("year"), o["s"]))
                except Exception: pass
    return _SENT

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

def bins(rows, mb):
    by = {}; out = []; cur = []
    for y, s in rows: by.setdefault(y, []).append(s)
    for y in sorted(by):
        cur.extend((y, v) for v in by[y])
        if len(cur) >= mb: out.append(cur); cur = []
    if cur and out: out[-1] += cur
    elif cur: out = [cur]
    return [(statistics.mean(y for y, _ in b), statistics.mean(v for _, v in b), len(b)) for b in out]

def wfit(pts, birth):
    if len(pts) < 3 or (pts[-1][0] - pts[0][0]) < 4: return None
    xs = [p[0] - birth for p in pts]; ws = [p[2] for p in pts]
    ys = [math.log(1 - min(p[1], .999)) for p in pts]
    W = sum(ws); mx = sum(w * x for w, x in zip(ws, xs)) / W; my = sum(w * y for w, y in zip(ws, ys)) / W
    den = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
    if den == 0: return None
    return 1 - math.exp(sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys)) / den)

# ---------- 通用元件 ----------
def style(ax, grid_axis="y"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(FAINT)
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, lw=.5, alpha=1); ax.set_axisbelow(True)
    ax.tick_params(colors=MUTED)

def panel(ax, letter, dx=0.0):
    ax.text(dx, 1.06, letter, transform=ax.transAxes, fontweight="bold",
            fontsize=10.5, color=INK, va="bottom", ha="left")

def kde(vals, grid):
    n = len(vals); sd = statistics.pstdev(vals) or .05
    h = 1.06 * sd * n ** (-.2) or .05
    return [sum(math.exp(-((g - v) / h) ** 2 / 2) for v in vals) / (n * h * math.sqrt(2 * math.pi)) for g in grid]

def half_violin(ax, x0, vals, color, side=1, width=.30, vertical=True, lo=None, hi=None):
    """在 x0 处画半侧 KDE 轮廓(vertical=True 时值在 y 轴)。"""
    vmin = min(vals) if lo is None else lo; vmax = max(vals) if hi is None else hi
    pad = (vmax - vmin) * .08 + 1e-9
    grid = [vmin - pad + i * (vmax - vmin + 2 * pad) / 120 for i in range(121)]
    dens = kde(vals, grid); mx = max(dens) or 1
    off = [side * width * d / mx for d in dens]
    if vertical:
        ax.fill_betweenx(grid, [x0] * len(grid), [x0 + o for o in off], color=color, alpha=.16, lw=0, zorder=1)
        ax.plot([x0 + o for o in off], grid, color=color, lw=.6, alpha=.45, zorder=1)
    else:
        ax.fill_between(grid, [x0] * len(grid), [x0 + o for o in off], color=color, alpha=.16, lw=0, zorder=1)
        ax.plot(grid, [x0 + o for o in off], color=color, lw=.6, alpha=.45, zorder=1)

def mean_bar(ax, x0, m, color, half=.24, vertical=True, label=None, label_dx=.30, fmt="{:.3f}"):
    if vertical:
        ax.hlines(m, x0 - half, x0 + half, color="white", lw=3.4, zorder=4)
        ax.hlines(m, x0 - half, x0 + half, color=color, lw=1.9, zorder=5)
        if label: ax.text(x0 + label_dx, m, fmt.format(m), va="center", fontsize=6.4,
                          color=color, fontweight="bold", zorder=6)
    else:
        ax.vlines(m, x0 - half, x0 + half, color="white", lw=3.4, zorder=4)
        ax.vlines(m, x0 - half, x0 + half, color=color, lw=1.9, zorder=5)

def boot_ci(vals, n=1999, seed=3):
    rng = random.Random(seed); ms = []
    for _ in range(n): ms.append(statistics.mean(rng.choices(vals, k=len(vals))))
    ms.sort(); return ms[int(.025 * n)], ms[int(.975 * n)]

def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf"))
    fig.savefig(os.path.join(OUT, name + "_p.png"), dpi=200, facecolor="white")
    plt.close(fig); print("v4 ✓", name)

ARM = {"refuted": dict(c=VERM, cl=VERM_L, mk="D"), "robust": dict(c=BLUE, cl=BLUE_L, mk="o")}

# ================= Fig 1 : 设计 + 量尺 + 修辞面貌 =================
def fig1():
    fig = plt.figure(figsize=(7.2, 3.0))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.02, 1.52, 1.12], wspace=.40,
                          left=.035, right=.975, top=.86, bottom=.15)
    # ---- A 队列漏斗 ----
    ax = fig.add_subplot(gs[0]); panel(ax, "A", -0.02)
    steps = [("135 original studies", "3 registered replication projects"),
             ("110 claims resolved", "68 refuted / 42 robust"),
             ("15,467 citing sentences", "dated, 1993–2026"),
             ("8,598 assertion sentences", "restate the claim itself"),
             ("85 / 73 claims analyzed", "trend / event analysis")]
    for i, (t1, t2) in enumerate(steps):
        y = 1 - i * .205
        ax.add_patch(FancyBboxPatch((.06, y - .125), .90, .148,
                                    boxstyle="round,pad=0.012,rounding_size=0.02",
                                    fc=PANEL_BG, ec="#d4d8dd", lw=.6))
        ax.add_patch(Rectangle((.06, y - .125), .016, .148, fc=INK if i < 2 else (VERM if i in (2, 3) else BLUE), lw=0))
        ax.text(.53, y - .030, t1, ha="center", fontsize=7.0, fontweight="bold", color=INK)
        ax.text(.53, y - .096, t2, ha="center", fontsize=5.6, color=MUTED)
        if i < 4:
            ax.annotate("", xy=(.51, y - .152), xytext=(.51, y - .126),
                        arrowprops=dict(arrowstyle="-|>", lw=.7, color=FAINT))
    ax.set_xlim(0, 1); ax.set_ylim(-.06, 1.04); ax.axis("off")
    # ---- B 量尺 + 例句 ----
    ax = fig.add_subplot(gs[1]); panel(ax, "B", -0.02)
    ax.text(.5, 1.66, "Stated certainty $s$", ha="center", fontsize=7.6, color=INK, fontweight="bold")
    # 渐变量尺
    for i in range(160):
        ax.axvspan(i / 160, (i + 1) / 160, ymin=.545, ymax=.615, color=CMAP(.18 + .68 * i / 159), lw=0)
    for x, lab in ((0, "0\nfully hedged"), (.5, "0.5\nneutral"), (1, "1\ndefinitive / causal")):
        ax.text(x, .40, lab, ha="center", va="top", fontsize=6.3, color=INK, linespacing=1.25)
        ax.plot([x, x], [.52, .56], color=INK, lw=.7)
    exs = [(0.0, "People might feel farther away from future events with potential negative than positive implications.", -.52),
           (0.5, "Recalling failures versus achievements has been shown to alter subjective distance to earlier selves.", .82),
           (1.0, "People who expect to own a good in the future exhibit signs of psychological ownership for it.", -.52)]
    for s0, txt, ty in exs:
        ax.scatter(s0, .655, s=34, color=INK, zorder=5, marker="v")
        w = "\n".join(textwrap.wrap("“" + txt + "”", 40 if ty > 0 else 36))
        ax.annotate(w, xy=(s0, .63 if ty < 0 else .72), xytext=(s0, ty),
                    ha="center", va="top" if ty < 0 else "bottom",
                    fontsize=5.5, color=MUTED, style="italic", linespacing=1.3,
                    arrowprops=dict(arrowstyle="-", lw=.5, color=FAINT))
    ax.set_xlim(-.10, 1.10); ax.set_ylim(-1.55, 1.80); ax.axis("off")
    # ---- C 修辞面貌:渐变直方图 ----
    ax = fig.add_subplot(gs[2]); panel(ax, "C", -0.06)
    allS = [s for _, _, s in sentences()]; n = len(allS)
    nb = 21; edges = [i / nb for i in range(nb + 1)]
    cnt = [0] * nb
    for s in allS:
        cnt[min(int(s * nb), nb - 1)] += 1
    for i in range(nb):
        cc = CMAP(.18 + .68 * ((edges[i] + edges[i + 1]) / 2))
        ax.bar((edges[i] + edges[i + 1]) / 2, cnt[i], width=1 / nb * .92, color=cc, lw=0)
    top = max(cnt)
    ax.axvline(.75, color=FAINT, lw=.6, ls=(0, (4, 3))); ax.axvline(.25, color=FAINT, lw=.6, ls=(0, (4, 3)))
    ax.text(.875, top * 1.03, f"definitive\n{sum(1 for s in allS if s>=.75)/n*100:.0f}%",
            ha="center", va="bottom", fontsize=6.3, color=INK, fontweight="bold", linespacing=1.2)
    ax.text(.115, top * 1.03, f"cautious\n{sum(1 for s in allS if s<=.25)/n*100:.0f}%",
            ha="center", va="bottom", fontsize=6.3, color=MUTED, linespacing=1.2)
    ax.set_ylim(0, top * 1.30)
    ax.set_xlabel("Stated certainty $s$"); ax.set_ylabel("Sentences")
    ax.set_xticks([0, .25, .5, .75, 1]); style(ax)
    save(fig, "fig1_design")

# ================= Fig 2 : 水平 null =================
def fig2():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.7), gridspec_kw={'width_ratios': [1, 1.22]})
    fig.subplots_adjust(left=.09, right=.985, top=.86, bottom=.17, wspace=.34)
    panel(a1, "A", -.16); random.seed(5)
    for j, arm in enumerate(("refuted", "robust")):
        A = ARM[arm]; vs = [r["mean_s"] for r in LV if r["arm"] == arm]
        half_violin(a1, j - .02, vs, A["c"], side=-1, width=.30, lo=.33, hi=.87)
        xs = [j + .10 + random.uniform(-.075, .075) for _ in vs]
        a1.scatter(xs, vs, s=11, color=A["c"], alpha=.55, edgecolors="none", zorder=3)
        m = statistics.mean(vs)
        lo, hi = boot_ci(vs, seed=3)                       # 聚类 bootstrap 95% CI
        a1.plot([j + .08, j + .08], [lo, hi], color=A["c"], lw=1.0, zorder=3,
                solid_capstyle="round")
        a1.plot([j + .055, j + .105], [lo, lo], color=A["c"], lw=.8, zorder=3)
        a1.plot([j + .055, j + .105], [hi, hi], color=A["c"], lw=.8, zorder=3)
        mean_bar(a1, j + .08, m, A["c"], half=.20, label=True, label_dx=.27)
    a1.text(.5, .035, "difference $+$0.004   95% CI [$-$0.011, $+$0.019]",
            transform=a1.transAxes, ha="center", fontsize=6.0, color=MUTED)
    a1.set_xticks([0, 1]); a1.set_xticklabels(["Refuted\nclaims (n=60)", "Robust\nclaims (n=39)"])
    a1.set_ylabel("Mean stated certainty per claim")
    a1.set_xlim(-.62, 1.72); a1.set_ylim(.33, .87); style(a1)
    # ---- B CDF ----
    panel(a2, "B", -.13)
    curves = {}
    for arm in ("refuted", "robust"):
        A = ARM[arm]
        vs = sorted(s for a, _, s in sentences() if a == arm)
        ys = [i / len(vs) for i in range(len(vs))]
        curves[arm] = (vs, ys)
        a2.plot(vs, ys, color=A["c"], ls="-" if arm == "refuted" else (0, (4, 2)),
                lw=1.6, label=f"{arm.capitalize()}  ({len(vs):,} sentences)", zorder=3)
    # 最大间隙标注
    gaps = []
    for q in [i / 200 for i in range(1, 200)]:
        f = sum(1 for v in curves["refuted"][0] if v <= q) / len(curves["refuted"][0])
        g = sum(1 for v in curves["robust"][0] if v <= q) / len(curves["robust"][0])
        gaps.append((abs(f - g), q, f, g))
    mg, mq, mf, mgr = max(gaps)
    a2.annotate(f"largest vertical gap = {mg:.03f}", xy=(mq, (mf + mgr) / 2), xytext=(.30, .78),
                fontsize=6.0, color=MUTED,
                arrowprops=dict(arrowstyle="-", lw=.5, color=FAINT))
    a2.set_xlabel("Stated certainty $s$"); a2.set_ylabel("Cumulative fraction of sentences")
    a2.set_xlim(0, 1); a2.set_ylim(0, 1.02)
    a2.legend(frameon=False, fontsize=6.3, loc="upper left", handlelength=1.8); style(a2)
    save(fig, "fig2_levels")

# ================= Fig 3 : 漂移 null =================
def fig3():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.6, 2.7), gridspec_kw={'width_ratios': [1.22, 1]})
    fig.subplots_adjust(left=.10, right=.98, top=.86, bottom=.17, wspace=.32)
    panel(a1, "A", -.13); random.seed(6)
    for j, arm in enumerate(("refuted", "robust")):
        A = ARM[arm]; vs = [r["beta"] for r in OK if r["arm"] == arm]
        half_violin(a1, j + .04, vs, A["c"], side=1, width=.30, vertical=False, lo=-.055, hi=.055)
        ys = [j - .09 + random.uniform(-.065, .065) for _ in vs]
        a1.scatter(vs, ys, s=11, marker=A["mk"], color=A["c"], alpha=.55, edgecolors="none", zorder=3)
        m = statistics.mean(vs)
        mean_bar(a1, j - .08, m, A["c"], half=.17, vertical=False)
        a1.text(m + .008, j + .42, f"{m:+.4f}", ha="left", fontsize=6.2, color=A["c"], fontweight="bold")
    a1.axvline(0, color=INK, lw=.7, ls=(0, (1, 2)))
    a1.set_yticks([0, 1]); a1.set_yticklabels(["Refuted\n(n=51)", "Robust\n(n=34)"])
    a1.set_xlabel("Certainty drift $\\beta$ (per year)")
    a1.set_xlim(-.062, .062); a1.set_ylim(-.55, 1.80)
    a1.text(.985, .97, "group difference $+$0.003\n95% CI [$-$0.004, $+$0.010]",
            transform=a1.transAxes, fontsize=6.0, va="top", ha="right", color=MUTED, linespacing=1.35)
    style(a1, grid_axis="x")
    # ---- B 剂量-响应 ----
    panel(a2, "B", -.16)
    for r in OK:
        pr = CSV.get(r["name"], {}).get("p_rep")
        try: pr = float(pr)
        except Exception: continue
        A = ARM[r["arm"]]
        a2.scatter(min(pr, 1), r["beta"], s=12, marker=A["mk"], color=A["c"],
                   alpha=.6, edgecolors="none", zorder=3)
    a2.axhline(0, color=INK, lw=.7, ls=(0, (1, 2)))
    a2.axvline(.05, color=INK, lw=.7, ls=":")
    a2.text(.085, .050, "replication\n$p=0.05$", fontsize=5.8, color=MUTED, linespacing=1.25, va="top")
    a2.set_xlabel("Replication $p$-value"); a2.set_ylabel("Certainty drift $\\beta$")
    a2.set_xlim(-.04, 1.04); a2.set_ylim(-.062, .062); style(a2)
    save(fig, "fig3_drift")

# ================= Fig 4 : 事件研究 =================
def fig4():
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.0, 2.8), gridspec_kw={'width_ratios': [1.62, 1]})
    fig.subplots_adjust(left=.085, right=.975, top=.86, bottom=.17, wspace=.30)
    panel(a1, "A", -.10)
    a1.axvspan(0, 8.6, color="#f3f4f6", zorder=0)
    a1.text(4.2, .092, "post-publication window", ha="center", fontsize=5.9, color=FAINT)
    for arm in ("refuted", "robust"):
        A = ARM[arm]
        pts = sorted((int(t), v[0], v[1]) for t, v in D["event_study"][arm].items())
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        se = [.28 / math.sqrt(p[2]) for p in pts]
        a1.fill_between(xs, [y - 1.96 * e for y, e in zip(ys, se)],
                        [y + 1.96 * e for y, e in zip(ys, se)], color=A["c"], alpha=.13, lw=0, zorder=1)
        a1.plot(xs, ys, color=A["c"], lw=1.6, marker=A["mk"], markersize=3.6,
                markeredgecolor="white", markeredgewidth=.5,
                label=f"{arm.capitalize()} claims", zorder=3)
    a1.axvline(0, color=INK, lw=.9, ls="--", zorder=2)
    a1.text(-.25, .098, "replication published", fontsize=6.0, color=INK,
            ha="right", va="top", fontweight="bold")
    a1.axhline(0, color=GRID, lw=.8)
    a1.set_ylim(-.10, .105); a1.set_xlim(-8.6, 8.6)
    a1.xaxis.set_major_locator(MultipleLocator(2))
    a1.set_xlabel("Years relative to replication publication")
    a1.set_ylabel("Stated certainty (claim-demeaned)")
    a1.legend(frameon=False, fontsize=6.3, loc="lower left"); style(a1)
    # ---- B 森林图 ----
    panel(a2, "B", -.24)
    def ry_of(m):
        return {'EERP': 2016, 'SSRP': 2018, 'RPP': 2015}[
            'EERP' if ('economic' in str(m.get('journal','')).lower() or 'qje' in str(m.get('journal','')).lower())
            else ('SSRP' if ('science' in str(m.get('journal','')).lower() or 'nature' in str(m.get('journal','')).lower()) else 'RPP')]
    cl = {}
    for f in glob.glob(os.path.join(ROOT, "seeds_data/scored2_v3_*.jsonl")):
        name = os.path.basename(f)[8:-6]; m = CSV.get(name)
        if not m: continue
        ry = ry_of(m); pre, post = [], []
        for L in open(f):
            try:
                o = json.loads(L)
                if o.get("assert") == 1 and o.get("s") is not None and o.get("year"):
                    (pre if o["year"] < ry else post).append(o["s"])
            except Exception: pass
        if len(pre) >= 10 and len(post) >= 10:
            cl[name] = (m["arm"], proj(name), statistics.mean(post) - statistics.mean(pre))
    def did(names):
        dR = [cl[n][2] for n in names if cl[n][0] == "refuted"]
        dB = [cl[n][2] for n in names if cl[n][0] == "robust"]
        return statistics.mean(dR) - statistics.mean(dB) if dR and dB else None
    random.seed(11); rows = []
    for lab, pool in (("Pooled", list(cl)), ("Psychology", [n for n in cl if cl[n][1] == "RPP"]),
                      ("Economics", [n for n in cl if cl[n][1] == "EERP"])):
        R = [n for n in pool if cl[n][0] == "refuted"]; B = [n for n in pool if cl[n][0] == "robust"]
        if len(R) < 3 or len(B) < 3: continue
        bs = []
        for _ in range(999):
            samp = random.choices(R, k=len(R)) + random.choices(B, k=len(B))
            v = did(samp)
            if v is not None: bs.append(v)
        bs.sort(); rows.append((lab, did(pool), bs[int(.025 * len(bs))], bs[int(.975 * len(bs))],
                                len(R), len(B)))
    a2.axvline(0, color=INK, lw=.7, ls=(0, (1, 2)))
    for i, (lab, m, lo, hi, nR, nB) in enumerate(rows):
        y = len(rows) - 1 - i
        a2.plot([lo, hi], [y, y], color=INK, lw=1.2, solid_capstyle="round", zorder=3)
        a2.plot([lo, lo], [y - .07, y + .07], color=INK, lw=1.0)
        a2.plot([hi, hi], [y - .07, y + .07], color=INK, lw=1.0)
        a2.scatter(m, y, s=34, color=INK, zorder=4, marker="s")
        a2.text(-.152, y + .12, lab, ha="left", va="bottom", fontsize=6.6, color=INK, fontweight="bold")
        a2.text(-.152, y - .13, f"{nR} refuted / {nB} robust", ha="left", va="top", fontsize=5.5, color=MUTED)
        a2.text(.148, y, f"{m:+.3f}", ha="right", va="center", fontsize=6.0, color=MUTED)
    a2.set_yticks([]); a2.set_xlim(-.155, .155); a2.set_ylim(-.55, len(rows) - .30)
    a2.set_xlabel("Difference-in-differences (95% CI)")
    a2.spines[["top", "right", "left"]].set_visible(False)
    a2.spines["bottom"].set_color(FAINT)
    a2.grid(axis="x", color=GRID, lw=.5); a2.set_axisbelow(True)
    a2.tick_params(colors=MUTED)
    save(fig, "fig4_event")

# ================= Fig 5 : 沉默 =================
def fig5():
    ack = json.load(open(os.path.join(ROOT, "out_runall_v3/ack_rate_modelB.json")))
    n = len(ack); k = sum(a for _, a in ack); rate = k / n
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(6.0, 2.6), gridspec_kw={'width_ratios': [1, 1.08]})
    fig.subplots_adjust(left=.105, right=.98, top=.85, bottom=.19, wspace=.42)
    panel(a1, "A", -.10)
    # waffle 点阵:150 个句子=150 个点(7 个承认失败,朱红;其余灰),沉默直接可见
    lo = rate - 1.96 * math.sqrt(rate * (1 - rate) / n); hi = rate + 1.96 * math.sqrt(rate * (1 - rate) / n)
    COLS, ROWS = 15, 10
    for i in range(n):
        r_, c_ = divmod(i, COLS)
        ack_dot = i >= n - k                     # 最后 k 个为承认句
        a1.scatter(c_, ROWS - 1 - r_, s=26, marker="o",
                   color=VERM if ack_dot else "#b9bfc6",
                   edgecolors="white", linewidths=.5, zorder=3)
    a1.annotate(f"mention the failure:\n{k} of {n}  ({rate*100:.1f}%,  95% CI {max(lo,0)*100:.1f}–{hi*100:.1f}%)",
                xy=(COLS - 1.6, 0.4), xytext=(COLS - 6.4, -2.2),
                fontsize=6.2, color=VERM, ha="center", linespacing=1.35,
                arrowprops=dict(arrowstyle="-|>", lw=.7, color=VERM))
    a1.text((COLS - 1) / 2, ROWS + .6,
            f"cited as valid, failure unmentioned:  {n-k} of {n}  ({(1-rate)*100:.1f}%)",
            ha="center", fontsize=6.4, color="#5b6169", fontweight="bold")
    a1.set_xlim(-.8, COLS - .2); a1.set_ylim(-3.1, ROWS + 1.3)
    a1.set_xticks([]); a1.set_yticks([])
    for sp in a1.spines.values(): sp.set_visible(False)
    a1.text((COLS - 1) / 2, -3.0, f"each dot = one post-refutation restating sentence (n={n})",
            ha="center", fontsize=5.8, color=MUTED, style="italic")
    # ---- B 承认 vs 沉默的确定性 ----
    panel(a2, "B", -.20)
    rows = list(csv.reader(open(os.path.join(ROOT, 'annotation_package/task_B_sentences.csv'), encoding='utf-8-sig')))[1:]
    keyB = {r[0]: r[1] for r in rows}
    s_of = {}
    for f in glob.glob(os.path.join(ROOT, "seeds_data/scored2_v3_*.jsonl")):
        for L in open(f):
            try:
                o = json.loads(L)
                if o.get("s") is not None: s_of[o["ctx"][:80]] = o["s"]
            except Exception: pass
    grp = {0: [], 1: []}
    for rid, a in ack:
        v = s_of.get(keyB.get(rid, "")[:80])
        if v is not None: grp[a].append(v)
    random.seed(8)
    for j, (g, c) in enumerate(((grp[0], "#5b6169"), (grp[1], VERM))):
        if len(g) >= 10:                       # 小样本组不画分布轮廓,只列点
            half_violin(a2, j - .03, g, c, side=-1, width=.26, lo=0, hi=1)
            xs = [j + .09 + random.uniform(-.06, .06) for _ in g]
        else:
            xs = [j + random.uniform(-.10, .10) for _ in g]
        a2.scatter(xs, g, s=15 if len(g) < 10 else 13, color=c, alpha=.7 if len(g) < 10 else .6,
                   edgecolors="white", linewidths=.4, zorder=3)
        m = statistics.mean(g)
        mean_bar(a2, j + (.07 if len(g) >= 10 else 0), m, c, half=.18, label=True, label_dx=.26, fmt="{:.2f}")
    a2.set_xticks([0, 1])
    a2.set_xticklabels([f"Failure\nunmentioned (n={len(grp[0])})", f"Failure\nmentioned (n={len(grp[1])})"], fontsize=6.2)
    a2.set_ylabel("Stated certainty $s$")
    a2.set_xlim(-.55, 1.75); a2.set_ylim(-.03, 1.06); style(a2)
    save(fig, "fig5_silence")

# ================= Fig 6 : 稳健性四联 =================
def fig6():
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.45))
    fig.subplots_adjust(left=.065, right=.985, top=.84, bottom=.19, wspace=.42)
    (aA, aB, aC, aD) = axes
    for ax, L in zip(axes, "ABCD"): panel(ax, L, -.28)
    # A 分项目
    random.seed(9)
    for pi, p in enumerate(("RPP", "EERP")):
        for arm, d in (("refuted", -.19), ("robust", .19)):
            A = ARM[arm]
            vs = [r["beta"] for r in OK if proj(r["name"]) == p and r["arm"] == arm]
            if not vs: continue
            aA.scatter([pi + d + random.uniform(-.06, .06) for _ in vs], vs, s=8,
                       marker=A["mk"], color=A["c"], alpha=.5, edgecolors="none", zorder=3)
            mean_bar(aA, pi + d, statistics.mean(vs), A["c"], half=.12)
    aA.axhline(0, color=INK, lw=.6, ls=(0, (1, 2)))
    aA.set_xticks([0, 1]); aA.set_xticklabels(["Psychology", "Economics"])
    aA.set_ylabel("$\\beta$ (per year)"); aA.set_ylim(-.062, .062); style(aA)
    # B 分桶敏感性
    for arm in ("refuted", "robust"):
        A = ARM[arm]; ms = []
        for mb in (6, 8, 12):
            bs = []
            for r in OK:
                if r["arm"] != arm: continue
                b = wfit(bins(scored(r["name"]), mb), r.get("birth") or 2010)
                if b is not None: bs.append(b)
            ms.append(statistics.mean(bs) if bs else float("nan"))
        aB.plot((6, 8, 12), ms, marker=A["mk"], color=A["c"], lw=1.4, markersize=4.2,
                markeredgecolor="white", markeredgewidth=.5, label=arm.capitalize())
    aB.axhline(0, color=INK, lw=.6, ls=(0, (1, 2)))
    aB.set_xticks((6, 8, 12)); aB.set_ylim(-.05, .05)
    aB.set_xlabel("Min sentences per bin"); aB.set_ylabel("Group mean $\\beta$")
    aB.legend(frameon=False, fontsize=5.9, loc="upper right", handlelength=1.4); style(aB)
    # C 高 R² 子集
    random.seed(10)
    hi = [r for r in OK if (r.get("r2") or 0) >= .1]
    for j, arm in enumerate(("refuted", "robust")):
        A = ARM[arm]; vs = [r["beta"] for r in hi if r["arm"] == arm]
        aC.scatter([j + random.uniform(-.10, .10) for _ in vs], vs, s=9,
                   marker=A["mk"], color=A["c"], alpha=.55, edgecolors="none", zorder=3)
        if vs: mean_bar(aC, j, statistics.mean(vs), A["c"], half=.20)
    aC.axhline(0, color=INK, lw=.6, ls=(0, (1, 2)))
    aC.set_xticks([0, 1]); aC.set_xticklabels(["Refuted", "Robust"])
    aC.set_ylabel("$\\beta$, $R^2\\geq0.1$ subset"); aC.set_xlim(-.55, 1.55); aC.set_ylim(-.062, .062); style(aC)
    # D 断言率
    for arm in ("refuted", "robust"):
        A = ARM[arm]
        vs = [r["n_assert"] / r["n_all"] for r in S if r.get("n_assert") and r.get("n_all") and r["arm"] == arm]
        aD.hist(vs, bins=12, alpha=.45, color=A["c"], label=arm.capitalize())
    aD.set_xlabel("Assertion-sentence rate"); aD.set_ylabel("Claims")
    aD.legend(frameon=False, fontsize=5.9, loc="upper left", handlelength=1.4); style(aD)
    save(fig, "fig6_robust")

# ================= Fig 7 : 轨迹画廊 =================
def fig7():
    def ry(name): return {'EERP': 2016, 'SSRP': 2018, 'RPP': 2015}[proj(name)]
    cand = sorted([r for r in OK if (r.get("n_assert") or 0) >= 60], key=lambda r: -(r.get("n_assert") or 0))
    ref = [r for r in cand if r["arm"] == "refuted"][:4]
    rob = [r for r in cand if r["arm"] == "robust"][:4]
    fig, axes = plt.subplots(2, 4, figsize=(7.2, 3.9), sharey=True)
    fig.subplots_adjust(left=.07, right=.985, top=.93, bottom=.12, hspace=.46, wspace=.10)
    for ax, r in zip(axes.flat, ref + rob):
        A = ARM[r["arm"]]
        pts = bins(scored(r["name"]), 8)
        ax.scatter([p[0] for p in pts], [p[1] for p in pts],
                   s=[max(7, min(30, p[2] * .8)) for p in pts],
                   color=A["c"], edgecolors="white", linewidths=.5, zorder=3)
        b = r["beta"]; y0 = pts[0][0]; m0 = min(pts[0][1], .95)
        fx = [y0 + t * (pts[-1][0] - y0) / 50 for t in range(51)]
        ax.plot(fx, [1 - (1 - m0) * (1 - b) ** (x - y0) for x in fx], color=INK, lw=.9, alpha=.8, zorder=2)
        ax.axvline(ry(r["name"]), color=INK, lw=.8, ls="--", alpha=.55, zorder=1)
        t = CSV.get(r["name"], {}).get("title", r["name"])
        t = t[:36] + ("…" if len(t) > 36 else "")
        ax.set_title(t, fontsize=5.5, color=A["c"], pad=5, fontweight="bold")
        ax.tick_params(labelsize=5.4)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=4))
        style(ax); ax.set_ylim(.25, .95)
    axes[0][0].set_ylabel("Refuted\nmean $s$ per bin", fontsize=6.4, color=VERM)
    axes[1][0].set_ylabel("Robust\nmean $s$ per bin", fontsize=6.4, color=BLUE)
    fig.text(.5, .015, "Year of citing paper   (dashed line: replication published;  marker size $\\propto$ sentences per bin)",
             ha="center", fontsize=6.8, color=MUTED)
    save(fig, "fig7_gallery")

# ================= Fig 8 : 没有发生的纠正 =================
def fig8():
    pts = sorted((int(t), v[0], v[1]) for t, v in D["event_study"]["refuted"].items())
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    se = [.28 / math.sqrt(p[2]) for p in pts]
    fig, ax = plt.subplots(figsize=(4.8, 3.0))
    fig.subplots_adjust(left=.13, right=.90, top=.90, bottom=.155)
    ax.axvspan(0, xs[-1] + 1.8, color="#f3f4f6", zorder=0)
    ax.fill_between(xs, [y - 1.96 * e for y, e in zip(ys, se)],
                    [y + 1.96 * e for y, e in zip(ys, se)], color=VERM, alpha=.15, lw=0, zorder=2)
    ax.plot(xs, ys, color=VERM, lw=1.8, marker="D", markersize=3.8,
            markeredgecolor="white", markeredgewidth=.5, label="Refuted claims, observed", zorder=5)
    for drop, g in ((-.05, "#5b6169"), (-.10, "#8b9199"), (-.20, "#b9bec5")):
        hy = [0 if x < 0 else drop * (1 - math.exp(-x / 2.0)) for x in xs]
        ax.plot(xs, hy, color=g, lw=1.15, ls=(0, (5, 2.6)), zorder=3)
        ax.text(xs[-1] + .32, hy[-1], f"{drop:+.2f}", fontsize=6.1, color=g,
                va="center", fontweight="bold")
    ax.axvline(0, color=INK, lw=.85, ls=":", zorder=4)
    ax.text(-.35, .088, "replication\npublished", fontsize=6.0, color=INK, ha="right", linespacing=1.25)
    ax.text(4.5, -.208, "hypothetical corrections (illustrative)", fontsize=6.0,
            color="#8b9199", ha="center", style="italic")
    ax.axhline(0, color=GRID, lw=.8)
    ax.set_ylim(-.245, .12); ax.set_xlim(xs[0] - .5, xs[-1] + 1.8)
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.set_xlabel("Years relative to replication publication")
    ax.set_ylabel("Stated certainty (claim-demeaned)")
    ax.legend(frameon=False, fontsize=6.3, loc="lower left"); style(ax)
    save(fig, "fig8_counterfactual")

if __name__ == "__main__":
    for f in (fig1, fig2, fig3, fig4, fig5, fig6, fig7, fig8):
        try: f()
        except Exception:
            import traceback; traceback.print_exc()
