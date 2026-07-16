#!/usr/bin/env python3
# 建 IAA 训练子集:从 core_6000 按 model_s 分层抽 hedged/neutral/definitive 各 14 条
# (覆盖全确定性档,与 batch01 不重复),让三名标注者【全标这一份】→ α 才有 range 可测。
# 内嵌 6 条金标(2/档)供质控。产物:iaa_train_import.csv(上传,盲) + iaa_train_KEY.csv(PI)。
import csv, re, random, os
random.seed(424242)
BASE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(BASE,"iaa_train")
os.makedirs(OUT,exist_ok=True)
def load(p):
    with open(os.path.join(BASE,p),encoding="utf-8-sig") as f: return list(csv.DictReader(f))
core=load("core_6000.csv"); key={r["id"]:r for r in load("core_6000_KEY.csv")}
used=set()
for f in ("batch01_recut/batch01_KEY_PI_ONLY.csv",):
    for r in load(f): used.add((r.get("sentence") or "").strip())
def ms(r):
    try: return float(key[r["id"]]["model_s"])
    except: return None
def usable(r):
    s=(r["sentence"] or "").strip()
    return 70<=len(s)<=240 and not s.startswith(("…","...")) and re.search(r"[.!?]$",s) and s[0].isupper() and s not in used
RE_H=re.compile(r"\b(may|might|could|possibly|suggests?|appears? to|seems? to)\b",re.I)
RE_D=re.compile(r"\b(shows?|demonstrat\w+|causes?|proves?|well[- ]establish\w+|well[- ]known)\b",re.I)
pool=[r for r in core if usable(r)]
hedged=[r for r in pool if ms(r) is not None and ms(r)<=0.25 and RE_H.search(r["sentence"])]
neutral=[r for r in pool if ms(r) is not None and 0.45<=ms(r)<=0.55]
defin=[r for r in pool if ms(r) is not None and ms(r)>=0.8]  # 高分即定性,不再强制信号词(否则池太小)
for L in (hedged,neutral,defin): random.shuffle(L)
print(f"候选池 hedged {len(hedged)} / neutral {len(neutral)} / definitive {len(defin)}")

# 每档取 14,前 2 条标为金标(答案由档位定,PI 复核)
sel=[]
for band,lst,gc in [("hedged",hedged,0.0),("neutral",neutral,0.5),("definitive",defin,1.0)]:
    for i,r in enumerate(lst[:14]):
        it = f"gold_{band}" if i<2 else "ordinary"
        sel.append((r,band,it,gc))
random.shuffle(sel)
rows=[]
for i,(r,band,it,gc) in enumerate(sel,1):
    rows.append(dict(task_id=f"R{i:03d}",src_id=r["id"],band=band,item_type=it,
                     gold_cert=(gc if it.startswith("gold") else ""),model_s=key[r["id"]]["model_s"],
                     sentence=(r["sentence"] or "").strip()))
with open(os.path.join(OUT,"iaa_train_import.csv"),"w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["task_id","sentence"])
    for r in rows: w.writerow([r["task_id"],r["sentence"]])
with open(os.path.join(OUT,"iaa_train_KEY.csv"),"w",newline="",encoding="utf-8-sig") as f:
    w=csv.writer(f); w.writerow(["task_id","src_id","band","item_type","gold_cert","model_s","sentence"])
    for r in rows: w.writerow([r["task_id"],r["src_id"],r["band"],r["item_type"],r["gold_cert"],r["model_s"],r["sentence"]])
from collections import Counter
print(f"生成 {len(rows)} 条: 档分布 {dict(Counter(r['band'] for r in rows))}")
print(f"金标 {sum(1 for r in rows if r['item_type'].startswith('gold'))} 条")
print("已写 iaa_train/iaa_train_import.csv + iaa_train_KEY.csv")
