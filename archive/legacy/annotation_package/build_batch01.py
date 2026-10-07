#!/usr/bin/env python3
# 从 core_6000 生成一份可导入 Label Studio 的标注批次(batch01):
#   - 30 条硬金标(注意力题,答案由无歧义信号词判定,不依赖模型)
#   - 12 条盲重复(同句换 task_id,拉开距离,测自我一致性)
#   - 330 条普通句
# 产物写入 batch01_recut/:import CSV(上传用,盲) + KEY CSV(PI 专用) 。
import csv, re, random, os
random.seed(20260715)
BASE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(BASE, "batch01_recut")
os.makedirs(OUT, exist_ok=True)

def load(p):
    with open(os.path.join(BASE, p), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

core = load("core_6000.csv")
key  = {r["id"]: r for r in load("core_6000_KEY.csv")}
for r in core:
    k = key.get(r["id"], {})
    r["model_s"], r["arm"], r["year"] = k.get("model_s",""), k.get("arm",""), k.get("year","")

def ms(r):
    try: return float(r["model_s"])
    except: return None

def usable(r, lo=70, hi=350):
    s = (r["sentence"] or "").strip()
    if not (lo <= len(s) <= hi): return False
    if s.startswith(("…","...")): return False
    if not re.search(r"[.!?]$", s): return False
    if s[0].islower(): return False
    return True

RE_HEDGE = re.compile(r"\b(may|might|could|possibly|perhaps|speculat\w*)\b", re.I)
RE_DEF   = re.compile(r"\b(causes?|caused|causal|proves?|proven|demonstrat\w+|well[- ]established|well[- ]known|unequivocal\w*)\b", re.I)
# 纯方法/范式引用信号(收紧:必须是"用了谁的范式/程序/材料")
RE_NONA  = re.compile(r"\b(we (used|adopted|employed|administered)|using (a |the )?(paradigm|procedure|task|method|scale|materials?|stimuli) (from|of|developed by)|following (the )?(procedure|method|protocol|paradigm) (of|from|described)|adapted from|based on the (paradigm|procedure|task) (of|from)|identical to that (used|described) (in|by))\b", re.I)
# 发现类动词:出现即说明句子在转述结论 → 排除出 non-assert 候选
RE_FIND  = re.compile(r"\b(shown|showed|found|finds?|demonstrat\w+|reported?|reveal\w+|predict\w+|caused?|increas\w+|reduc\w+|decreas\w+|associat\w+|correlat\w+|relat\w+|discover\w+|indicat\w+|suggest\w+|conclud\w+|evidence (that|for)|led to|effect of)\b", re.I)

pool = [r for r in core if usable(r)]
hedge_c = [r for r in pool if RE_HEDGE.search(r["sentence"]) and not RE_DEF.search(r["sentence"]) and (ms(r) is not None and ms(r) <= 0.25)]
def_c   = [r for r in pool if RE_DEF.search(r["sentence"])   and not RE_HEDGE.search(r["sentence"]) and (ms(r) is not None and ms(r) >= 0.90)]
nona_c  = [r for r in pool if RE_NONA.search(r["sentence"])  and not RE_FIND.search(r["sentence"]) and not RE_DEF.search(r["sentence"]) and not RE_HEDGE.search(r["sentence"])]
for lst in (hedge_c, def_c, nona_c): random.shuffle(lst)

# 金标 = 逐条人工审定的显式白名单(2026-07-15 审:剔除引用方自述/假设、撞手册降档规则、
# "This result/finding"开头、分号残句等歧义句)。答案按区间判(见 score_batch01.py):
#   hedged: assert=1 且 certainty≤0.25;definitive: assert=1 且 certainty≥0.75;nonassert: assert=0。
VETTED_HEDGED = ["C0346","C5821","C4892","C5304","C4747","C0103","C2175","C0597"]
VETTED_DEFIN  = ["C0791","C1342","C3429","C0272","C0681","C0524","C3518","C0073","C5579","C1290"]
VETTED_FOILS  = ["A118","A042","A066","A045","A122","A044","A114","A018"]

core_by_id = {r["id"]: r for r in core}
gold = []  # (row, item_type, gold_assert, gold_cert)
for cid in VETTED_HEDGED: gold.append((core_by_id[cid], "gold_hedged",     1, 0.0))
for cid in VETTED_DEFIN:  gold.append((core_by_id[cid], "gold_definitive", 1, 1.0))
sentA = {r["id"]: (r.get("sentence") or "").strip() for r in load("task_A_sentences.csv")}
for fid in VETTED_FOILS:
    s = sentA.get(fid,"")
    if s:
        gold.append(({"id":fid, "sentence":s, "model_s":"", "arm":"", "year":""}, "gold_nonassert", 0, ""))
gold_ids = {r["id"] for r,_,_,_ in gold}

# 按句子文本去重(core_6000 有约50条重复文本),防止计划外的"同句两id"混进批次被误当盲重复
seen_txt = {(r["sentence"] or "").strip() for r,_,_,_ in gold}
ordinary = []
cand = [r for r in pool if r["id"] not in gold_ids]
random.shuffle(cand)
for r in cand:
    t = (r["sentence"] or "").strip()
    if t in seen_txt: continue
    seen_txt.add(t); ordinary.append(r)
    if len(ordinary) == 330: break

# 12 条盲重复:按 model_s 分层挑,覆盖不同确定性
dsrc = sorted(ordinary, key=lambda r: (ms(r) if ms(r) is not None else 0.5))
step = max(1, len(dsrc)//12)
dups = [dsrc[i*step] for i in range(12)]
dup_ids = {r["id"] for r in dups}

# ---- 组装:唯一 task_id;先放唯一句(打乱),再把盲重复插到离原句 >=120 的位置 ----
uniq = [(r, t, ga, gc) for r,t,ga,gc in gold] + [(r, "ordinary", "", "") for r in ordinary]
random.shuffle(uniq)
seq = list(uniq)                      # 360 个唯一任务
pos = {r["id"]: i for i,(r,_,_,_) in enumerate(seq)}
for r in dups:
    src = pos[r["id"]]
    tgt = (src + 180) % (len(seq)+1)
    seq.insert(tgt, (r, "duplicate", "", ""))   # 盲重复占位,item_type=duplicate
# 分配连续 task_id
tasks = []
for i,(r,t,ga,gc) in enumerate(seq, 1):
    tasks.append(dict(task_id=f"T{i:04d}", src_id=r["id"], item_type=t,
                      gold_assert=ga, gold_cert=gc, model_s=r["model_s"],
                      arm=r["arm"], year=r["year"], sentence=(r["sentence"] or "").strip()))

# 校验盲重复间距
byid = {}
for i,tk in enumerate(tasks): byid.setdefault(tk["src_id"], []).append(i)
gaps = [max(v)-min(v) for v in byid.values() if len(v)>1]
print(f"任务总数 {len(tasks)} | 盲重复对 {len(gaps)} | 最小间距 {min(gaps) if gaps else '-'}")
print(f"硬金标 hedged/definitive/nonassert = {sum(1 for t in tasks if t['item_type']=='gold_hedged')}/"
      f"{sum(1 for t in tasks if t['item_type']=='gold_definitive')}/"
      f"{sum(1 for t in tasks if t['item_type']=='gold_nonassert')}")

# ---- 产物1:import CSV(上传用)——只有 task_id + sentence,绝对盲 ----
with open(os.path.join(OUT,"batch01_import.csv"),"w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["task_id","sentence"])
    for t in tasks: w.writerow([t["task_id"], t["sentence"]])

# ---- 产物2:KEY CSV(PI 专用,勿发学生)——含金标答案与重复映射 ----
with open(os.path.join(OUT,"batch01_KEY_PI_ONLY.csv"),"w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["task_id","src_id","item_type","gold_assert","gold_cert","model_s","arm","year","sentence"])
    for t in tasks:
        w.writerow([t["task_id"],t["src_id"],t["item_type"],t["gold_assert"],t["gold_cert"],
                    t["model_s"],t["arm"],t["year"],t["sentence"]])
print("已写:", os.path.join(OUT,"batch01_import.csv"))
print("已写:", os.path.join(OUT,"batch01_KEY_PI_ONLY.csv"))
