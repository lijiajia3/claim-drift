#!/usr/bin/env python3
"""Finite-cohort hypothetical sensitivity of Welch tests to stipulated differences.
Centered empirical source-paper distributions supply nuisance variance only.
This is not achieved power and cannot account for provenance/measurement error.
"""
from pathlib import Path
import json,sys
import numpy as np
from scipy import stats
from analysis_core import *

def simulate(fits,metric,reps=100000,seed=642024):
    a=np.array([r[metric] for r in fits if r['outcome']=='negative' and r.get(metric) is not None]);b=np.array([r[metric] for r in fits if r['outcome']=='positive' and r.get(metric) is not None])
    a=a-a.mean();b=b-b.mean();rng=np.random.default_rng(seed)
    diffs=np.empty(reps);ses=np.empty(reps);dfs=np.empty(reps)
    # Restore unbiased empirical variance: ordinary resampling from n observations has population variance (n-1)/n times sample variance.
    a=a*np.sqrt(len(a)/(len(a)-1));b=b*np.sqrt(len(b)/(len(b)-1))
    for start in range(0,reps,1000):
        n=min(1000,reps-start);aa=a[rng.integers(len(a),size=(n,len(a)))];bb=b[rng.integers(len(b),size=(n,len(b)))]
        d=aa.mean(1)-bb.mean(1);va=aa.var(1,ddof=1)/len(a);vb=bb.var(1,ddof=1)/len(b);se=np.sqrt(va+vb);df=(va+vb)**2/(va**2/(len(a)-1)+vb**2/(len(b)-1))
        diffs[start:start+n]=d;ses[start:start+n]=se;dfs[start:start+n]=df
    rows=[]
    margins=(.0025,.005,.01,.02) if metric=='transformed_drift' else (.005,.01,.02,.03,.05)
    for margin in margins:
        # Detection probability under a stipulated true negative-minus-positive difference = margin.
        detected=np.abs((diffs+margin)/ses)>stats.t.ppf(.975,dfs)
        # Equivalence probability under stipulated true difference =0, using fixed ±margin.
        equivalent=(diffs-stats.t.ppf(.95,dfs)*ses>-margin)&(diffs+stats.t.ppf(.95,dfs)*ses<margin)
        for purpose,vals in [('detect_stipulated_difference_equal_to_margin',detected),('equivalence_stipulating_true_difference_zero',equivalent)]:
            p=float(vals.mean());mc=np.sqrt(p*(1-p)/reps)
            rows.append({'metric':metric,'n_negative':len(a),'n_positive':len(b),'margin':margin,'purpose':purpose,
                         'simulated_probability':p,'monte_carlo_standard_error':float(mc),'repetitions':reps,
                         'assumption':'centered, variance-restored empirical distributions; independent sources; labels, corpus and model fixed; alpha=.05'})
    return rows

def main():
    root=Path(__file__).resolve().parent/'data/core'
    rec=load_inputs(root/'inputs');led=read_csv(root/'inputs/analysis_ledger.csv');_,fits,_=evaluate(rec,led,with_bootstrap=False)
    rows=[r for m in PRIMARY_METRICS for r in simulate(fits,m)]
    write_csv(root.parents[1]/'results/scores/hypothetical_precision_simulation.csv',rows)
    print(json.dumps([r for r in rows if r['metric']=='event_change' and r['margin']==.02],indent=2))
if __name__=='__main__':main()
