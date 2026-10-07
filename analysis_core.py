"""Offline estimators, eligibility and conditional uncertainty for source-paper text scores.
All source/project/outcome decisions are supplied by an explicit versioned ledger.
"""
from __future__ import annotations
import csv, hashlib, json, math, random, statistics
from collections import defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
from scipy import stats

BOOT=19999
SEED=20261005
PRIMARY_METRICS=('level','transformed_drift','event_change')

def read_csv(p):
    with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def write_csv(p, rows):
    if not rows:return
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with Path(p).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)

def load_inputs(path):
    cells=read_csv(Path(path)/'numeric_cells.csv');records=[]
    for cell in cells:
        r=dict(cell)
        for k in ('year_earliest','year_latest','n_scored_presentations','n_distinct_years','assertion','assertion_conflict','development_frame_eligible','original_paper_year','matched_record_year','before_original_year','before_matched_record_year'):r[k]=int(r[k])
        for k in ('certainty','luna','deepseek'):r[k]=float(r[k]) if r[k] else None
        records.extend(dict(r) for _ in range(int(cell['frequency'])))
    return records

@dataclass(frozen=True)
class Config:
    label_column:str='revised_outcome'
    included_only:bool=True
    event_column:str='event_year_journal'
    score_column:str='certainty'
    date_rule:str='earliest'
    min_level:int=15
    min_event:int=10
    min_bin:int=8
    event_window:int=0
    omit_event_year:bool=False
    original_year_filter:bool=False
    development_frame_only:bool=False
    omit_project:str=''
    only_project:str=''
    max_year:int=0

    def __post_init__(self):
        if self.date_rule not in ('earliest','latest','drop_conflicts'):
            raise ValueError('date_rule must be earliest, latest or drop_conflicts')
        if self.score_column not in ('certainty','luna','deepseek'):
            raise ValueError('score_column must identify a frozen score component')
        if min(self.min_level,self.min_event,self.min_bin)<1 or self.event_window<0:
            raise ValueError('count thresholds must be positive and event_window nonnegative')


def outcome(r, cfg):
    x=r[cfg.label_column].strip().lower()
    mapping={'refuted':'negative','failed':'negative','not_success':'negative','criterion-negative':'negative','negative':'negative',
             'robust':'positive','successful':'positive','success':'positive','criterion-positive':'positive','positive':'positive','ambiguous':'ambiguous','unresolved':'ambiguous'}
    if x not in mapping:raise ValueError(f'Unknown outcome {x!r} for {r["analysis_claim_id"]}')
    return mapping[x]


def truth(x):return str(x).lower() in ('1','true','yes')


def select(records, ledger, cfg):
    assert len(ledger)==len({r['analysis_claim_id'] for r in ledger})
    meta={r['analysis_claim_id']:r for r in ledger}
    assert set(meta)=={r['analysis_claim_id'] for r in records}
    papers={}
    for name,m in sorted(meta.items()):
        arm=outcome(m,cfg)
        if cfg.included_only and not truth(m['include_primary']):continue
        if arm=='ambiguous':continue
        if cfg.omit_project and m['project']==cfg.omit_project:continue
        if cfg.only_project and m['project']!=cfg.only_project:continue
        event=int(float(m[cfg.event_column]))
        papers[name]={'id':name,'source_id':m['source_id'],'project':m['project'],'arm':arm,'event_year':event,'meta':m,'rows':[]}
    for r in records:
        name=r['analysis_claim_id']
        if name not in papers:continue
        if cfg.date_rule=='drop_conflicts' and r['n_distinct_years']>1:continue
        year=r['year_latest' if cfg.date_rule=='latest' else 'year_earliest']
        if cfg.max_year and year>cfg.max_year:continue
        if cfg.original_year_filter and year<r['original_paper_year']:continue
        if cfg.development_frame_only and not r['development_frame_eligible']:continue
        papers[name]['rows'].append({**r,'year':year,'s':r[cfg.score_column]})
    return papers


def make_bins(rows, min_bin=8):
    by_year=defaultdict(list)
    for r in rows:by_year[r['year']].append(r['s'])
    bins=[]; current=[]
    for year, vals in sorted(by_year.items()):
        current.extend((year,s) for s in vals)
        if len(current)>=min_bin:bins.append(current);current=[]
    if current:
        if bins:bins[-1].extend(current)
        else:bins=[current]
    return [(statistics.mean(y for y,s in b),statistics.mean(s for y,s in b),len(b)) for b in bins]


def slope(x,y,w=None):
    x=np.asarray(x,dtype=float);y=np.asarray(y,dtype=float);w=np.ones(len(x)) if w is None else np.asarray(w,dtype=float)
    mx=np.average(x,weights=w);my=np.average(y,weights=w);den=np.dot(w,(x-mx)**2)
    if den==0:return None
    return float(np.dot(w,(x-mx)*(y-my))/den)


def fit_paper(paper,cfg=Config()):
    rows=paper['rows'];pos=[r for r in rows if r['assertion'] and r['s'] is not None]
    out={'analysis_claim_id':paper['id'],'source_id':paper['source_id'],'project':paper['project'],'outcome':paper['arm'],'event_year':paper['event_year'],
         'n_all':len(rows),'n_positive':len(pos),'level_eligible':False,'drift_eligible':False,'event_eligible':False,
         'assertion_rate':len(pos)/len(rows) if rows else None,'original_paper_year':int(paper['meta']['original_paper_year'])}
    if pos:
        scores=[r['s'] for r in pos]
        out.update(mean_all_positive=statistics.mean(scores),first_year=min(r['year'] for r in pos),last_year=max(r['year'] for r in pos),
                   median_all_positive=statistics.median(scores),usable_positive_fraction=statistics.mean(r['development_frame_eligible'] for r in pos),
                   n_conflicting_date_positive=sum(r['n_distinct_years']>1 for r in pos))
    if len(pos)>=cfg.min_level:
        out.update(level=statistics.mean(r['s'] for r in pos),level_eligible=True,
                   median_score=statistics.median(r['s'] for r in pos),high_score_fraction=statistics.mean(r['s']>=.75 for r in pos),low_score_fraction=statistics.mean(r['s']<=.25 for r in pos))
    else:out['level_exclusion']='fewer than minimum positive texts'
    pts=make_bins(pos,cfg.min_bin)
    out['n_bins']=len(pts)
    if pts:out['binned_year_span']=pts[-1][0]-pts[0][0]
    if len(pos)>=cfg.min_level and len(pts)>=3 and len({round(p[0]) for p in pts})>=3 and pts[-1][0]-pts[0][0]>=4:
        x=[p[0] for p in pts];y=[math.log(1-min(p[1],.999)) for p in pts];w=[p[2] for p in pts]
        gamma=slope(x,y,w)
        if gamma is not None:
            out.update(transformed_drift=1-math.exp(gamma),raw_score_slope=slope(x,[p[1] for p in pts],w),drift_eligible=True,
                       clipped_bins=sum(p[1]>.999 for p in pts))
    if not out['drift_eligible']:out['drift_exclusion']='positive count, number/distinct years of adaptive bins, or binned-year span ineligible'
    event=paper['event_year']
    pre=[r for r in pos if r['year']<event and (not cfg.event_window or r['year']>=event-cfg.event_window)]
    post=[r for r in pos if r['year']>=event+(1 if cfg.omit_event_year else 0) and (not cfg.event_window or r['year']<=event+cfg.event_window)]
    out.update(n_pre=len(pre),n_post=len(post),n_event_year=sum(r['year']==event for r in pos))
    if len(pre)>=cfg.min_event and len(post)>=cfg.min_event:
        a=statistics.mean(r['s'] for r in pre);b=statistics.mean(r['s'] for r in post)
        out.update(pre_mean=a,post_mean=b,event_change=b-a,event_eligible=True,
                   mean_pre_year=statistics.mean(r['year'] for r in pre),mean_post_year=statistics.mean(r['year'] for r in post))
        pp=defaultdict(list)
        for r in pos:
            if -8<=r['year']-event<=-1:pp[r['year']-event].append(r['s'])
        if len(pp)>=3:out['pretrend_raw']=slope(list(pp),[statistics.mean(v) for v in pp.values()])
        ar_pre=[r for r in rows if r['year']<event and (not cfg.event_window or r['year']>=event-cfg.event_window)]
        ar_post=[r for r in rows if r['year']>=event+(1 if cfg.omit_event_year else 0) and (not cfg.event_window or r['year']<=event+cfg.event_window)]
        out['assertion_rate_change']=statistics.mean(r['assertion'] for r in ar_post)-statistics.mean(r['assertion'] for r in ar_pre)
    else:out['event_exclusion']='fewer than minimum positive texts in pre or post interval'
    return out


def bootstrap_difference(a,b,reps=BOOT,seed=SEED):
    a=np.asarray(a,float);b=np.asarray(b,float);rng=np.random.default_rng(seed)
    draws=np.empty(reps)
    for start in range(0,reps,1000):
        n=min(1000,reps-start)
        draws[start:start+n]=a[rng.integers(0,len(a),size=(n,len(a)))].mean(1)-b[rng.integers(0,len(b),size=(n,len(b)))].mean(1)
    return draws


def legacy_bootstrap(a,b,seed,reps=9999):
    rng=random.Random(seed)
    draws=sorted(statistics.mean(rng.choices(a,k=len(a)))-statistics.mean(rng.choices(b,k=len(b))) for _ in range(reps))
    return [draws[int(.025*reps)],draws[int(.975*reps)]],min(1.,2*min(sum(v<=0 for v in draws),sum(v>=0 for v in draws))/reps)


def contrast(a,b,reps=BOOT,seed=SEED,with_bootstrap=True):
    a=np.asarray(a,float);b=np.asarray(b,float)
    out={'n_negative':len(a),'n_positive':len(b),'mean_negative':float(a.mean()) if len(a) else None,'mean_positive':float(b.mean()) if len(b) else None}
    if not len(a) or not len(b):return {**out,'estimate':None,'inference_note':'one outcome group is empty'}
    estimate=float(a.mean()-b.mean());out['estimate']=estimate
    if len(a)<2 or len(b)<2:return {**out,'inference_note':'fewer than two papers in an outcome group; no confidence interval'}
    va=float(a.var(ddof=1)/len(a));vb=float(b.var(ddof=1)/len(b));se=math.sqrt(va+vb)
    df=(va+vb)**2/(va**2/(len(a)-1)+vb**2/(len(b)-1)) if va+vb else None
    out.update(se=se,welch_df=df)
    if min(len(a),len(b))<10:out['inference_note']='exploratory small group; percentile bootstrap can be discrete and poorly calibrated; compare Welch interval'
    if se:
        for lev in (.90,.95):
            q=float(stats.t.ppf((1+lev)/2,df));out[f'welch_ci{int(lev*100)}_low']=estimate-q*se;out[f'welch_ci{int(lev*100)}_high']=estimate+q*se
        out['welch_p']=float(2*stats.t.sf(abs(estimate/se),df))
    if with_bootstrap:
        draws=bootstrap_difference(a,b,reps,seed)
        out.update(bootstrap_ci95_low=float(np.quantile(draws,.025)),bootstrap_ci95_high=float(np.quantile(draws,.975)),bootstrap_reps=reps)
    return out


def evaluate(records,ledger,cfg=Config(),reps=BOOT,with_bootstrap=True):
    papers=select(records,ledger,cfg);fits=[fit_paper(p,cfg) for p in papers.values()]
    metrics={}
    for metric in (*PRIMARY_METRICS,'raw_score_slope','assertion_rate','pretrend_raw','assertion_rate_change','median_score','high_score_fraction','low_score_fraction'):
        groups={g:[r[metric] for r in fits if r['outcome']==g and r.get(metric) is not None] for g in ('negative','positive')}
        metrics[metric]=contrast(groups['negative'],groups['positive'],reps=reps,with_bootstrap=with_bootstrap)
    return {'config':asdict(cfg),'n_papers':len(papers),'n_texts':sum(len(p['rows']) for p in papers.values()),'n_positive_texts':sum(r['assertion'] for p in papers.values() for r in p['rows']),'metrics':metrics},fits,papers


def project_standardized(fits,metric,reps=BOOT,seed=SEED):
    groups=defaultdict(lambda:defaultdict(list))
    for r in fits:
        if r.get(metric) is not None:groups[r['project']][r['outcome']].append(r[metric])
    both={p:v for p,v in groups.items() if len(v['negative'])>=2 and len(v['positive'])>=2}
    total=sum(sum(map(len,v.values())) for v in both.values())
    if not total:return {'estimate':None,'note':'No project has >=2 papers in both groups'}
    w={p:sum(map(len,v.values()))/total for p,v in both.items()}
    estimates={p:statistics.mean(v['negative'])-statistics.mean(v['positive']) for p,v in both.items()}
    est=sum(w[p]*v for p,v in estimates.items())
    draws=np.zeros(reps)
    for i,(p,v) in enumerate(sorted(both.items())):draws+=w[p]*bootstrap_difference(v['negative'],v['positive'],reps,seed+i)
    return {'estimate':est,'bootstrap_ci95_low':float(np.quantile(draws,.025)),'bootstrap_ci95_high':float(np.quantile(draws,.975)),
            'weights':w,'project_contrasts':estimates,'included_projects':list(both),'excluded_projects':sorted(set(groups)-set(both)),
            'weight_rule':'pooled eligible paper fractions in projects with >=2 papers per outcome; held fixed during stratified resampling'}


def precision_diagnostics(c,metric):
    if not c.get('se'):return []
    est,se,df=c['estimate'],c['se'],c['welch_df'];rows=[]
    margins=(.0025,.005,.01,.02) if metric in ('transformed_drift','raw_score_slope','pretrend_raw') else (.005,.01,.02,.03,.05)
    for margin in margins:
        p1=float(stats.t.sf((est+margin)/se,df));p2=float(stats.t.cdf((est-margin)/se,df))
        rows.append({'metric':metric,'illustrative_model_scale_margin':margin,'tost_p':max(p1,p2),'tost_pass_05':max(p1,p2)<.05,
                     'normal_approx_equivalence_power_assuming_true_zero':max(0.,float(2*stats.norm.cdf(margin/se-stats.norm.ppf(.95))-1)),
                     'normal_approx_detect_difference_power':float(stats.norm.sf(stats.norm.ppf(.975)-margin/se)+stats.norm.cdf(-stats.norm.ppf(.975)-margin/se)),
                     'normal_approx_80pct_detectable_difference':float((stats.norm.ppf(.975)+stats.norm.ppf(.8))*se),
                     'normal_approx_margin_for_80pct_equivalence_if_zero':float((stats.norm.ppf(.95)+stats.norm.ppf(.9))*se),
                     'interpretation':'post hoc hypothetical precision diagnostic; not a SESOI, human-scale equivalence, or achieved-power estimate'})
    return rows
