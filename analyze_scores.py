#!/usr/bin/env python3
"""Reproduce the revised descriptive analysis and fixed, labelled sensitivities."""
from __future__ import annotations
import argparse, itertools, hashlib, json, shutil, sys
from collections import Counter,defaultdict
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from scipy import stats
from analysis_core import *



def flat_results(name,result):
    return [{'scenario':name,'metric':k,'n_papers':result['n_papers'],'n_texts':result['n_texts'],'n_positive_texts':result['n_positive_texts'],**v} for k,v in result['metrics'].items()]


def archived_replay(records,ledger,out,inputs):
    cfg=Config(label_column='original_outcome',included_only=False,event_column='archived_event_year')
    result,fits,_=evaluate(records,ledger,cfg,with_bootstrap=False)
    archived={r['name']:r for r in json.loads((inputs/'archived_claim_results.json').read_text())}
    errors=[]
    for r in fits:
        a=archived[r['analysis_claim_id']]
        for k,old in [('level','mean_s'),('transformed_drift','beta')]:
            if r.get(k) is not None:errors.append(abs(r[k]-a[old]))
        assert r['n_positive']==a['n_assert'] and r['n_all']==a['n_all']
    assert max(errors)<1e-12
    output=[]
    for metric,seed in [('level',94205),('transformed_drift',94207),('event_change',94206)]:
        a=[r[metric] for r in fits if r['outcome']=='negative' and r.get(metric) is not None]
        b=[r[metric] for r in fits if r['outcome']=='positive' and r.get(metric) is not None]
        ci,p=legacy_bootstrap(a,b,seed)
        output.append({'metric':metric,**result['metrics'][metric],'archived_percentile_ci95_low':ci[0],'archived_percentile_ci95_high':ci[1],'archived_bootstrap_tail_mass_p':p})
    ev=json.loads((inputs/'archived_event_result.json').read_text())
    assert abs(output[2]['estimate']-ev['did'])<1e-12
    assert max(abs(output[2][f'archived_percentile_ci95_{k}']-ev['ci95'][i]) for i,k in enumerate(('low','high')))<1e-12
    write_csv(out/'archived_replay.csv',output)
    (out/'archived_replay_verification.json').write_text(json.dumps({'all_paper_means_and_transformed_slopes_match':True,'maximum_absolute_estimator_error':max(errors),'event_estimate_and_legacy_ci_match':True,'original_source_and_score_files_unchanged':True},indent=2)+'\n')


def event_trajectory(papers,fits,out,reps):
    """Equal-paper, not equal-sentence, trajectory; baseline mean fixed per paper."""
    eligible={r['analysis_claim_id'] for r in fits if r['event_eligible']}
    subject_rows=[]
    for name,p in papers.items():
        if name not in eligible:continue
        by_t=defaultdict(list)
        for r in p['rows']:
            if r['assertion']:by_t[r['year']-p['event_year']].append(r['s'])
        baseline=[s for t,ss in by_t.items() if -5<=t<=-1 for s in ss]
        if not baseline:continue
        for t,ss in sorted(by_t.items()):
            if -8<=t<=8:subject_rows.append({'analysis_claim_id':name,'project':p['project'],'outcome':p['arm'],'event_time':t,
                'n_texts':len(ss),'score_mean':float(np.mean(ss)),'baseline_mean':float(np.mean(baseline)),'change_from_pre5_mean':float(np.mean(ss)-np.mean(baseline))})
    write_csv(out/'event_paper_years.csv',subject_rows)
    summaries=[]
    for t in range(-8,9):
        group={a:[r['change_from_pre5_mean'] for r in subject_rows if r['outcome']==a and r['event_time']==t] for a in ('negative','positive')}
        r=contrast(group['negative'],group['positive'],reps)
        r.update(event_time=t,n_texts=sum(r['n_texts'] for r in subject_rows if r['event_time']==t),
                 baseline='Each paper positive-text mean at event times -5 through -1; paper-year mean then equal paper weights')
        summaries.append(r)
    write_csv(out/'event_equal_paper_trajectory.csv',summaries)
    return subject_rows,summaries


def label_uncertainty(records,ledger,out,reps):
    unresolved=[r['analysis_claim_id'] for r in ledger if r['revised_outcome']=='ambiguous']
    rows=[]
    for bits in itertools.product(('failed','successful'),repeat=len(unresolved)):
        allocation=dict(zip(unresolved,bits)); changed=[{**r,'revised_outcome':allocation.get(r['analysis_claim_id'],r['revised_outcome']),'include_primary':'True'} for r in ledger]
        result,_,_=evaluate(records,changed,Config(included_only=False),reps=reps)
        assignment=';'.join(f'{r["source_id"]}={allocation[r["analysis_claim_id"]]}' for r in ledger if r['analysis_claim_id'] in allocation)
        for metric in PRIMARY_METRICS:rows.append({'assignment':assignment,'metric':metric,**result['metrics'][metric]})
    write_csv(out/'ambiguous_label_all_assignments.csv',rows)
    summary=[]
    for metric in PRIMARY_METRICS:
        rs=[r for r in rows if r['metric']==metric];low=min(rs,key=lambda r:r['estimate']);high=max(rs,key=lambda r:r['estimate'])
        summary.append({'metric':metric,'n_assignments':len(rs),'n_unique_estimates':len({round(r['estimate'],14) for r in rs}),'estimate_min':low['estimate'],'estimate_max':high['estimate'],
                        'assignment_at_min':low['assignment'],'assignment_at_max':high['assignment'],
                        'conditional_ci_envelope_low':min(r['bootstrap_ci95_low'] for r in rs),'conditional_ci_envelope_high':max(r['bootstrap_ci95_high'] for r in rs),
                        'interpretation':'range across all allocations; CI envelope is sensitivity union, not a single calibrated 95% interval'})
    write_csv(out/'ambiguous_label_ranges.csv',summary)


def overlap_clusters(records, fits,out,reps):
    names=sorted(r['analysis_claim_id'] for r in fits);parent={n:n for n in names}
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    def union(a,b):parent[find(a)]=find(b)
    by_group=defaultdict(set)
    input_path=Path(__file__).resolve().parent/'data/core/inputs/shared_source_groups.csv'
    for r in read_csv(input_path):
        if r['analysis_claim_id'] in parent:by_group[r['sharing_group']].add(r['analysis_claim_id'])
    for members in by_group.values():
        ns=sorted(members)
        for a,b in zip(ns,ns[1:]):union(a,b)
    cluster=defaultdict(list)
    for name in names:cluster[find(name)].append(name)
    cs=list(cluster.values());rng=np.random.default_rng(SEED);summaries=[]
    for metric in PRIMARY_METRICS:
        sums=np.zeros((len(cs),2));counts=np.zeros((len(cs),2));lookup={r['analysis_claim_id']:r for r in fits}
        for i,c in enumerate(cs):
            for name in c:
                r=lookup[name]
                if r.get(metric) is not None:
                    arm=0 if r['outcome']=='negative' else 1;sums[i,arm]+=r[metric];counts[i,arm]+=1
        draws=[]
        for start in range(0,reps,1000):
            ids=rng.integers(0,len(cs),(min(1000,reps-start),len(cs)));ss=sums[ids].sum(1);ns=counts[ids].sum(1)
            valid=(ns>0).all(1);v=ss[valid]/ns[valid];draws.extend((v[:,0]-v[:,1]).tolist())
        summaries.append({'metric':metric,'n_source_papers':len(names),'n_connected_components':len(cs),'largest_component':max(map(len,cs)),
                          'estimate':float(sums.sum(0)[0]/counts.sum(0)[0]-sums.sum(0)[1]/counts.sum(0)[1]),
                          'bootstrap_ci95_low':float(np.quantile(draws,.025)),'bootstrap_ci95_high':float(np.quantile(draws,.975)),
                          'note':'Connected components share archived exact text; unobserved common citing articles remain unidentified. Unstratified component bootstrap allows group counts to vary.'})
    write_csv(out/'shared_text_component_bootstrap.csv',summaries)
    write_csv(out/'shared_text_component_membership.csv',[{'analysis_claim_id':name,'component_id':i,'component_size':len(c)} for i,c in enumerate(cs,1) for name in c])


def main():
    root=Path(__file__).resolve().parent/'data/core'
    ap=argparse.ArgumentParser();ap.add_argument('--inputs',type=Path,default=root/'inputs');ap.add_argument('--output',type=Path,default=root.parents[1]/'results/scores');ap.add_argument('--bootstrap',type=int,default=BOOT);ap.add_argument('--skip-label-grid',action='store_true');a=ap.parse_args();a.output.mkdir(exist_ok=True,parents=True)
    records=load_inputs(a.inputs)
    ledger=read_csv(a.inputs/'analysis_ledger.csv')
    archived_replay(records,ledger,a.output,a.inputs)
    result,fits,papers=evaluate(records,ledger,reps=a.bootstrap)
    write_csv(a.output/'primary_paper_estimates.csv',fits);write_csv(a.output/'primary_contrasts.csv',flat_results('conservative_source_baseline',result))
    (a.output/'primary_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('n_papers','n_texts','n_positive_texts')},indent=2));print(json.dumps({k:result['metrics'][k] for k in PRIMARY_METRICS},indent=2),flush=True)
    counts=[]
    for project in sorted({r['project'] for r in fits}):
        for arm in ('negative','positive'):
            rs=[r for r in fits if r['project']==project and r['outcome']==arm]
            counts.append({'project':project,'outcome':arm,'n_papers':len(rs),'n_texts':sum(r['n_all'] for r in rs),'n_positive_texts':sum(r['n_positive'] for r in rs),
                           'n_level':sum(r['level_eligible'] for r in rs),'n_drift':sum(r['drift_eligible'] for r in rs),'n_event':sum(r['event_eligible'] for r in rs)})
    write_csv(a.output/'cohort_counts.csv',counts)
    precision=[row for m,c in result['metrics'].items() if m in PRIMARY_METRICS for row in precision_diagnostics(c,m)];write_csv(a.output/'precision_and_tost_grid.csv',precision)
    configs={'original_labels_corrected_projects_and_dates':Config(label_column='original_outcome',included_only=False),
             'source_based_labels_all108_unresolved_archived':Config(label_column='source_mechanical_outcome',included_only=False),
             'known_earlier_individual_publication_only':Config(event_column='event_year_known_individual_if_earlier'),
             'recorded_manuscript_upload_years':Config(event_column='event_year_first_located_manuscript'),'omit_event_year':Config(omit_event_year=True),
             'latest_conflicting_dates':Config(date_rule='latest'),'drop_conflicting_dates':Config(date_rule='drop_conflicts'),
             'exclude_pre_original_year_flags_diagnostic_only':Config(original_year_filter=True),
             'development_text_frame_only':Config(development_frame_only=True),
             'omit_partial_retrieval_year_2026':Config(max_year=2025),
             'luna_component':Config(score_column='luna'),'deepseek_component':Config(score_column='deepseek')}
    for window in (3,5,8):configs[f'symmetric_{window}yr_excluding_event_year']=Config(event_window=window,omit_event_year=True)
    for threshold in (5,15,20):configs[f'min_event_{threshold}']=Config(min_event=threshold)
    for threshold in (10,20,30):configs[f'min_level_{threshold}']=Config(min_level=threshold)
    for project in sorted({r['project'] for r in ledger}):
        configs[f'omit_{project}']=Config(omit_project=project);configs[f'only_{project}']=Config(only_project=project)
    grid=flat_results('conservative_source_baseline',result)
    for name,cfg in configs.items():
        r,_,_=evaluate(records,ledger,cfg,reps=a.bootstrap);grid.extend(flat_results(name,r));print('sensitivity',name,flush=True)
    write_csv(a.output/'sensitivity_grid.csv',grid)
    (a.output/'sensitivity_definitions.json').write_text(json.dumps({k:asdict(v) for k,v in configs.items()},indent=2)+'\n')
    standardized={m:project_standardized(fits,m,a.bootstrap) for m in PRIMARY_METRICS}
    (a.output/'project_standardization.json').write_text(json.dumps(standardized,indent=2)+'\n')
    event_trajectory(papers,fits,a.output,a.bootstrap)
    overlap_clusters(records,fits,a.output,a.bootstrap)
    if not a.skip_label_grid:label_uncertainty(records,ledger,a.output,a.bootstrap)
    (a.output/'method.json').write_text(json.dumps({'bootstrap_replicates':a.bootstrap,'seed':SEED,'unit':'source paper; outcomes/scoring/corpus held fixed',
        'group_order':'criterion-negative minus criterion-positive','numpy_version':np.__version__,'python_version':sys.version.split()[0],'primary_config':asdict(Config()),
        'cohort':json.loads((a.inputs/'cohort_version.json').read_text()),'no_causal_identification':True,'no_independent_measurement_test':True,'post_hoc_revision':True},indent=2)+'\n')

if __name__=='__main__':main()
