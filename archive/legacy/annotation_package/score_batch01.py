#!/usr/bin/env python3
# batch01 质控与验证打分器(纯 Python,无需第三方库)。
# 用法: python3 score_batch01.py 学生A.csv 学生B.csv [学生C.csv ...]
#   - 每份是 Label Studio 导出(需含列: task_id, assert, certainty;可选 lead_time, note)
#   - 自动读 batch01_recut/batch01_KEY_PI_ONLY.csv 做金标/重复比对
# 输出: 每人三道质控闸(耗时/金标/盲重复) + 通过者的 IAA(κ,α) 与人-模型 ρ。
import csv, sys, os, math
from collections import defaultdict, Counter

BASE = os.path.dirname(os.path.abspath(__file__))
KEY  = os.path.join(BASE, "batch01_recut", "batch01_KEY_PI_ONLY.csv")

# ---------- 统计原语(纯 Python) ----------
def rankdata(a):
    order = sorted(range(len(a)), key=lambda i: a[i])
    ranks = [0.0]*len(a); i=0
    while i < len(a):
        j=i
        while j+1<len(a) and a[order[j+1]]==a[order[i]]: j+=1
        r=(i+j)/2.0+1
        for k in range(i,j+1): ranks[order[k]]=r
        i=j+1
    return ranks

def pearson(x,y):
    n=len(x); mx=sum(x)/n; my=sum(y)/n
    sx=sum((v-mx)**2 for v in x); sy=sum((v-my)**2 for v in y)
    if sx==0 or sy==0: return float('nan')
    return sum((x[i]-mx)*(y[i]-my) for i in range(n))/math.sqrt(sx*sy)

def spearman(x,y): return pearson(rankdata(x),rankdata(y))

def cohen_kappa(a,b):
    cats=sorted(set(a)|set(b)); n=len(a)
    po=sum(1 for i in range(n) if a[i]==b[i])/n
    ca=Counter(a); cb=Counter(b)
    pe=sum((ca[c]/n)*(cb[c]/n) for c in cats)
    return (po-pe)/(1-pe) if pe!=1 else float('nan')

def fleiss_kappa(item_ratings):
    cats=sorted({c for d in item_ratings for c in d})
    N=len(item_ratings)
    if N==0: return float('nan')
    n=sum(item_ratings[0].values())
    if n<2: return float('nan')
    p=[sum(d.get(c,0) for d in item_ratings)/(N*n) for c in cats]
    Pe=sum(pj*pj for pj in p)
    Pi=[(sum(d.get(c,0)**2 for c in cats)-n)/(n*(n-1)) for d in item_ratings]
    Pbar=sum(Pi)/N
    return (Pbar-Pe)/(1-Pe) if Pe!=1 else float('nan')

def krippendorff_ordinal(units):
    # units: list,每元素是一个单元收到的有序类别值(至少 2 个)。
    vals=sorted({v for u in units for v in u})
    idx={v:i for i,v in enumerate(vals)}
    ncat=len(vals)
    o=defaultdict(float)
    for u in units:
        m=len(u)
        if m<2: continue
        for i in range(m):
            for j in range(m):
                if i!=j: o[(idx[u[i]],idx[u[j]])]+=1.0/(m-1)
    n_c=[sum(o[(c,k)] for k in range(ncat)) for c in range(ncat)]
    n=sum(n_c)
    if n<2 or ncat<2: return float('nan')
    def delta2(c,k):
        lo,hi=min(c,k),max(c,k)
        s=sum(n_c[g] for g in range(lo,hi+1))-(n_c[c]+n_c[k])/2.0
        return s*s
    Do=sum(o[(c,k)]*delta2(c,k) for c in range(ncat) for k in range(ncat))/n
    De=sum(n_c[c]*n_c[k]*delta2(c,k) for c in range(ncat) for k in range(ncat))/(n*(n-1))
    return 1-Do/De if De!=0 else float('nan')

# ---------- 读取 ----------
def norm(v): return (v or '').strip()
def get(row,*names):
    low={k.lower():k for k in row}
    for nm in names:
        if nm.lower() in low: return norm(row[low[nm.lower()]])
    return ''
def read_key():
    with open(KEY,encoding='utf-8-sig') as f: return {r['task_id']:r for r in csv.DictReader(f)}
def read_export(path):
    with open(path,encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    out=[]
    for r in rows:
        a=get(r,'assert','是否在转述结论(1/0)','是否在转述结论').split('｜')[0].split('|')[0].strip()
        c=get(r,'certainty','确定性打分(0/0.25/0.5/0.75/1)','确定性打分').split('｜')[0].split('|')[0].strip()
        out.append(dict(task_id=get(r,'task_id'), assert_=a, certainty=c, lead_time=get(r,'lead_time')))
    return out
def float_eq(a,b):
    try: return abs(float(a)-float(b))<1e-6
    except: return False

# ---------- 质控 ----------
def qc_one(name, recs, key):
    by={r['task_id']:r for r in recs}
    lts=[float(r['lead_time']) for r in recs if r['lead_time'] and r['lead_time'].replace('.','',1).isdigit()]
    med=sorted(lts)[len(lts)//2] if lts else None
    under5=(sum(1 for x in lts if x<5)/len(lts)) if lts else None
    gate1=(med is not None and med>=8 and under5 is not None and under5<0.30)
    gp=gf=0
    for tid,k in key.items():
        it=k['item_type']
        if it not in ('gold_hedged','gold_definitive','gold_nonassert'): continue
        r=by.get(tid)
        if not r: continue
        gp+=1
        # 区间判:邻档不算错(suggested…may 答 0 或 0.25 均对),划水者仍过不了
        try: cv=float(r['certainty'])
        except: cv=None
        if it=='gold_nonassert':   ok=(r['assert_']=='0')
        elif it=='gold_hedged':    ok=(r['assert_']=='1' and cv is not None and cv<=0.25)
        else:                      ok=(r['assert_']=='1' and cv is not None and cv>=0.75)
        if ok: gf+=1
    goldrate=gf/gp if gp else None
    gate2=(goldrate is not None and goldrate>=0.80)
    dup=defaultdict(list)
    for tid,k in key.items(): dup[k['src_id']].append(tid)
    pairs=[v for v in dup.values() if len(v)>1]
    consist=ntot=0
    for tids in pairs:
        rs=[by.get(t) for t in tids if by.get(t)]
        if len(rs)<2: continue
        ntot+=1
        a_same=rs[0]['assert_']==rs[1]['assert_']
        c_close=True
        if rs[0]['assert_']=='1' and rs[1]['assert_']=='1':
            try: c_close=abs(float(rs[0]['certainty'])-float(rs[1]['certainty']))<=0.25
            except: c_close=False
        if a_same and c_close: consist+=1
    selfc=consist/ntot if ntot else None
    gate3=(selfc is not None and selfc>=0.75)
    print(f"\n===== {name} =====")
    print(f"  闸1 耗时:   中位 {med}s, <5s占比 {under5:.0%} → {'通过' if gate1 else '❌不通过'}" if med is not None else "  闸1 耗时: 无 lead_time 列(需人工核)")
    print(f"  闸2 金标:   {gf}/{gp} = {goldrate:.0%} → {'通过' if gate2 else '❌不通过'}" if goldrate is not None else "  闸2 金标: 无匹配")
    print(f"  闸3 盲重复: {consist}/{ntot} = {selfc:.0%} → {'通过' if gate3 else '❌不通过'}" if selfc is not None else "  闸3 盲重复: 无匹配")
    passed=gate1 and gate2 and gate3
    print(f"  → 结论: {'✅ 可入 IAA' if passed else '⛔ 数据作废,重标'}")
    return passed, by

def main():
    if len(sys.argv)<2:
        print("用法: python3 score_batch01.py 学生A.csv [学生B.csv ...]"); return
    key=read_key(); raters=[]
    for p in sys.argv[1:]:
        ok,by=qc_one(os.path.basename(p),read_export(p),key)
        if ok: raters.append((os.path.basename(p),by))
    if len(raters)<2:
        print("\n<2 名合格标注者,暂不算 IAA。修复后重跑。"); return
    common=set(raters[0][1])
    for _,by in raters[1:]: common&=set(by)
    item_ratings=[]
    for t in common:
        d=Counter(by[t]['assert_'] for _,by in raters)
        if sum(d.values())==len(raters): item_ratings.append(dict(d))
    kap=fleiss_kappa(item_ratings) if len(raters)>2 else cohen_kappa(
        [raters[0][1][t]['assert_'] for t in common],[raters[1][1][t]['assert_'] for t in common])
    units=[]
    for t in common:
        cs=[]; good=True
        for _,by in raters:
            if by[t]['assert_']=='1':
                try: cs.append(float(by[t]['certainty']))
                except: good=False
            else: good=False
        if good and len(cs)>=2: units.append(cs)
    alpha=krippendorff_ordinal(units)
    hx=[]; mx=[]
    for t in common:
        k=key[t]
        if not k['model_s']: continue
        cs=[]
        for _,by in raters:
            if by[t]['assert_']=='1':
                try: cs.append(float(by[t]['certainty']))
                except: pass
        if cs: hx.append(sum(cs)/len(cs)); mx.append(float(k['model_s']))
    rho=spearman(mx,hx) if len(hx)>2 else float('nan')
    print("\n========== 汇总(合格标注者) ==========")
    print(f"  合格人数: {len(raters)}  共同任务: {len(common)}")
    print(f"  断言一致性 κ (Fleiss/Cohen) = {kap:.3f}   门槛 ≥0.60 → {'✅' if kap>=0.6 else '❌'}")
    print(f"  确定性 Krippendorff α (序数) = {alpha:.3f}   门槛 ≥0.60 → {'✅' if alpha>=0.6 else '❌'}")
    print(f"  人-模型 Spearman ρ (n={len(hx)}) = {rho:.3f}   门槛 ≥0.60 → {'✅' if rho>=0.6 else '❌'}")
    print("\n  三个数都 ✅ → 闸门开,可填正文 TODO 并投稿。")

if __name__=="__main__":
    main()
