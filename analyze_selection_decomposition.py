#!/usr/bin/env python3
"""Exact descriptive accounting on previously frozen literal citation-text counts."""
from pathlib import Path
import csv, json, hashlib, platform
from collections import defaultdict
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent/'data/selection'
INPUT=ROOT/'inputs' if (ROOT/'inputs').is_dir() else ROOT.parent/'scientometrics_analysis/lexical/inputs'
OLD=ROOT/'previous' if (ROOT/'previous').is_dir() else ROOT.parent/'scientometrics_analysis/lexical/outputs'
OUT=ROOT.parents[1]/'results/selection'
FEATURES=('epistemic_adverb_tokens','replication_word_tokens','lowercase_modal_tokens')
SEED=20261006
B=19999
PROTOCOL_HASH='167f2ce696b06d0f0608b94040a85a22ecb0d2113bd99294db7956e60b42863e'
METRICS=('filter_shift','retention_component','stratum_distribution_component','account_retained_weight','account_excluded_incidence')
CONFIGS={
 'journal':dict(event='event_year_journal',year='year',omit=False,window=0),
 'recorded_manuscript_upload_years':dict(event='event_year_first_located_manuscript',year='year',omit=False,window=0),
 'omit_event_year':dict(event='event_year_journal',year='year',omit=True,window=0),
 'symmetric5_years_omit_event_year':dict(event='event_year_journal',year='year',omit=True,window=5),
 'latest_archived_year':dict(event='event_year_journal',year='latest_year',omit=False,window=0),
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,rows):
    pd.DataFrame(rows).to_csv(OUT/name,index=False,float_format='%.17g')
def fit_source(d,meta,cfg):
    results=[]
    for name,m in sorted(meta.items()):
        dd=d[d.analysis_claim_id==name]
        ev=int(m[cfg['event']]);years=dd[cfg['year']]
        pre=(years<ev)
        post=(years>=ev+int(cfg['omit']))
        if cfg['window']:
            pre &= years>=ev-cfg['window'];post &= years<=ev+cfg['window']
        periods={}
        for label,mask in [('pre',pre),('post',post)]:
            z=dd[mask]
            periods[label]={a:z[z.assertion==a] for a in (0,1)}
        counts={label:{a:int(z.n_texts.sum()) for a,z in vals.items()} for label,vals in periods.items()}
        if min(counts['pre'][1],counts['post'][1])<10:continue
        for f in FEATURES:
            r={'analysis_claim_id':name,'source_id':m['source_id'],'project':m['project'],'criterion':m['revised_outcome'],'feature':f}
            for t in ('pre','post'):
                np_,nn=counts[t][1],counts[t][0];na=np_+nn
                hp=int(periods[t][1]['context_'+f].sum());hn=int(periods[t][0]['context_'+f].sum())
                assert 0<=hp<=np_ and 0<=hn<=nn
                pp=hp/np_;pn=hn/nn if nn else np.nan;pa=(hp+hn)/na;q=nn/na
                r.update({f'{t}_n_positive':np_,f'{t}_n_negative':nn,f'{t}_hit_positive':hp,f'{t}_hit_negative':hn,
                  f'{t}_positive_incidence':pp,f'{t}_negative_incidence':pn,f'{t}_all_incidence':pa,
                  f'{t}_excluded_share':q,f'{t}_filter_gap':pp-pa,f'{t}_weighted_retained_incidence':q*pp,
                  f'{t}_excluded_incidence_all_denominator':hn/na})
                assert abs((pp-pa)-(q*pp-hn/na))<1e-12
                if nn: assert abs((pp-pa)-q*(pp-pn))<1e-12
            r['all_event_change']=r['post_all_incidence']-r['pre_all_incidence']
            r['positive_event_change']=r['post_positive_incidence']-r['pre_positive_incidence']
            r['filter_shift']=r['post_filter_gap']-r['pre_filter_gap']
            assert abs(r['filter_shift']-(r['positive_event_change']-r['all_event_change']))<1e-12
            r['account_retained_weight']=r['post_weighted_retained_incidence']-r['pre_weighted_retained_incidence']
            r['account_excluded_incidence']=-(r['post_excluded_incidence_all_denominator']-r['pre_excluded_incidence_all_denominator'])
            assert abs(r['filter_shift']-r['account_retained_weight']-r['account_excluded_incidence'])<1e-12
            r['decomposition_eligible']=min(r['pre_n_negative'],r['post_n_negative'])>=1
            r['negative10_eligible']=min(r['pre_n_negative'],r['post_n_negative'])>=10
            if r['decomposition_eligible']:
                qp,qq=r['pre_excluded_share'],r['post_excluded_share']
                dp=r['pre_positive_incidence']-r['pre_negative_incidence'];dq=r['post_positive_incidence']-r['post_negative_incidence']
                r['retention_component']=(qq-qp)*(dq+dp)/2
                r['stratum_distribution_component']=(dq-dp)*(qq+qp)/2
                assert abs(r['filter_shift']-r['retention_component']-r['stratum_distribution_component'])<1e-12
            else:
                r['retention_component']=np.nan;r['stratum_distribution_component']=np.nan
            results.append(r)
    return pd.DataFrame(results)

def summarize(z,metrics,cohort,mode='source'):
    groups=[z[z.criterion==c].sort_values('analysis_claim_id') for c in ('failed','successful')]
    ns=[len(x) for x in groups]
    if not min(ns):return []
    arrays=[x[list(metrics)].to_numpy(float) for x in groups]
    assert all(np.isfinite(x).all() for x in arrays)
    means=[x.mean(0) for x in arrays];point=means[0]-means[1]
    rng=np.random.default_rng(SEED);draw=[]
    for start in range(0,B,1000):
        n=min(1000,B-start)
        vals=[a[rng.integers(len(a),size=(n,len(a)))].mean(1) for a in arrays]
        draw.append(vals[0]-vals[1])
    draws=np.concatenate(draw);lo,hi=np.quantile(draws,[.025,.975],axis=0)
    return [{'feature':z.feature.iloc[0],'cohort':cohort,'resampling':mode,'metric':k,'n_negative':ns[0],'n_positive':ns[1],
        'mean_negative':means[0][j],'mean_positive':means[1][j],'estimate':point[j],
        'ci95_low':lo[j] if min(ns)>=2 else np.nan,'ci95_high':hi[j] if min(ns)>=2 else np.nan,
        'n_draws':B if min(ns)>=2 else 0} for j,k in enumerate(metrics)]

def component_summarize(z,metrics,cohort,members):
    component_ids=sorted(members.component_id.unique());index={k:i for i,k in enumerate(component_ids)}
    membermap=dict(zip(members.analysis_claim_id,members.component_id))
    sums=np.zeros((len(component_ids),2,len(metrics)));counts=np.zeros((len(component_ids),2))
    for r in z.to_dict('records'):
        i=index[membermap[r['analysis_claim_id']]];g=int(r['criterion']=='successful')
        sums[i,g]+=np.array([r[k] for k in metrics]);counts[i,g]+=1
    means=sums.sum(0)/counts.sum(0)[:,None];point=means[0]-means[1]
    rng=np.random.default_rng(SEED);draw=[];dropped=0
    for start in range(0,B,500):
        inds=rng.integers(len(component_ids),size=(min(500,B-start),len(component_ids)))
        s=sums[inds].sum(1);n=counts[inds].sum(1);ok=(n>0).all(1);dropped+=sum(~ok)
        rat=s[ok]/n[ok,:,None];draw.append(rat[:,0]-rat[:,1])
    draws=np.concatenate(draw);lo,hi=np.quantile(draws,[.025,.975],axis=0)
    return [{'feature':z.feature.iloc[0],'cohort':cohort,'resampling':'frozen_shared_text_component','metric':k,
        'n_negative':int(counts.sum(0)[0]),'n_positive':int(counts.sum(0)[1]),'mean_negative':means[0,j],'mean_positive':means[1,j],
        'estimate':point[j],'ci95_low':lo[j],'ci95_high':hi[j],'n_draws':len(draws),'dropped_draws':int(dropped),
        'n_components_in_fixed_graph':len(component_ids),'n_components_with_eligible_source':int((counts.sum(1)>0).sum())} for j,k in enumerate(metrics)]

def standardized(z,projects,weight_mode):
    weights={p:(1/len(projects) if weight_mode=='equal_project' else (z.project==p).mean()) for p in projects}
    cells={(p,g):z[(z.project==p)&(z.criterion==g)].filter_shift.to_numpy(float) for p in projects for g in ('failed','successful')}
    if any(len(a)==0 for a in cells.values()):return {'feature':z.feature.iloc[0],'weight_mode':weight_mode,'status':'unsupported_empty_project_criterion_cell'}
    means={g:sum(weights[p]*cells[(p,g)].mean() for p in projects) for g in ('failed','successful')}
    rng=np.random.default_rng(SEED);draw=[]
    for start in range(0,B,1000):
        n=min(1000,B-start);diff=np.zeros(n)
        for p in projects:
            for g,sign in [('failed',1),('successful',-1)]:
                a=cells[(p,g)];diff+=sign*weights[p]*a[rng.integers(len(a),size=(n,len(a)))].mean(1)
        draw.extend(diff)
    lo,hi=np.quantile(draw,[.025,.975])
    small={f'{p}:{g}':len(a) for (p,g),a in cells.items() if len(a)<2}
    return {'feature':z.feature.iloc[0],'weight_mode':weight_mode,'status':'descriptive_fixed_project_standardization',
       'estimate':means['failed']-means['successful'],'mean_negative':means['failed'],'mean_positive':means['successful'],
       'ci95_low':lo if not small else np.nan,'ci95_high':hi if not small else np.nan,
       'audit_conditional_ci95_low':lo,'audit_conditional_ci95_high':hi,
       'interval_warning':'Manuscript interval suppressed: singleton project-criterion cell has unestimated within-cell variability' if small else '',
       'singleton_cells_json':json.dumps(small,sort_keys=True),'weights_json':json.dumps(weights,sort_keys=True),
       'cell_counts_json':json.dumps({p:{g:len(cells[(p,g)]) for g in ('failed','successful')} for p in projects},sort_keys=True)}

def main():
    OUT.mkdir(exist_ok=True,parents=True)
    protocol=ROOT/'SELECTION_DECOMPOSITION_PROTOCOL.md';assert sha(protocol)==PROTOCOL_HASH
    paths=[INPUT/'literal_counts_by_source_year.csv',INPUT/'source_cohort.csv',INPUT/'shared_text_component_membership.csv',OLD/'matched_source_filter_estimates.csv',OLD/'matched_source_filter_comparison.csv']
    d=pd.read_csv(paths[0]);d=d[d.text_view=='full'].copy()
    meta={r['analysis_claim_id']:r for r in pd.read_csv(paths[1]).to_dict('records')}
    assert len(meta)==105 and int(d.n_texts.sum())==15280 and int(d[d.assertion==1].n_texts.sum())==8427
    members=pd.read_csv(paths[2]);old=pd.read_csv(paths[3])
    configs={k:fit_source(d,meta,v) for k,v in CONFIGS.items()}
    mainfit=configs['journal'];assert len(mainfit)==72*3
    checks=[]
    for f in FEATURES:
        a=mainfit[mainfit.feature==f].set_index('analysis_claim_id');o=old[old.feature==f].set_index('analysis_claim_id')
        assert set(a.index)==set(o.index)
        for new,prev in [('filter_shift','filtered_minus_all_change'),('all_event_change','all_event_change'),('positive_event_change','positive_event_change')]:
            err=float(np.max(np.abs(a[new]-o.loc[a.index,prev])));assert err<1e-12
            checks.append({'feature':f,'metric':new,'max_absolute_difference_from_previous':err})
    write('source_period_decomposition.csv',mainfit)
    summaries=[];components=[];lopo=[];loco=[];project=[];standard=[];timing=[];support=[]
    projects=sorted({r['project'] for r in meta.values()})
    for f in FEATURES:
        z=mainfit[mainfit.feature==f].copy()
        for label,sel,metrics in [('full72',z,('filter_shift','account_retained_weight','account_excluded_incidence')),
             ('nonempty_negative_each_period',z[z.decomposition_eligible],METRICS),
             ('negative10_each_period',z[z.negative10_eligible],METRICS)]:
            summaries.extend(summarize(sel,metrics,label));components.extend(component_summarize(sel,metrics,label,members))
            support.append({'feature':f,'cohort':label,'n_sources':len(sel),'n_negative':sum(sel.criterion=='failed'),'n_positive':sum(sel.criterion=='successful'),
              'pre_texts':int((sel.pre_n_positive+sel.pre_n_negative).sum()),'post_texts':int((sel.post_n_positive+sel.post_n_negative).sum())})
        full=z[z.criterion=='failed'].filter_shift.mean()-z[z.criterion=='successful'].filter_shift.mean()
        for p in projects:
            zz=z[z.project!=p]
            for r in summarize(zz,['filter_shift'],'omit_'+p):lopo.append({'omitted_project':p,**r})
            pp=z[z.project==p]
            for r in summarize(pp,['filter_shift'],'project_'+p):project.append({'project':p,**r})
        for r in z.to_dict('records'):
            zz=z[z.analysis_claim_id!=r['analysis_claim_id']]
            estimate=zz[zz.criterion=='failed'].filter_shift.mean()-zz[zz.criterion=='successful'].filter_shift.mean()
            n=sum(z.criterion==r['criterion']);contribution=(1 if r['criterion']=='failed' else -1)*r['filter_shift']/n
            loco.append({k:r[k] for k in ('feature','analysis_claim_id','source_id','project','criterion')}|{
                'source_filter_shift':r['filter_shift'],'signed_contribution_to_full_contrast':contribution,
                'estimate_omitting_source':estimate,'change_from_full_estimate':estimate-full})
        for mode in ('equal_project','pooled_source_project_weights'):standard.append(standardized(z,projects,mode))
        base_ids=set(z.analysis_claim_id)
        for name,allfit in configs.items():
            sel=allfit[allfit.feature==f]
            for r in summarize(sel,['filter_shift'],name):timing.append(r|{'n_sources_also_in_primary72':len(set(sel.analysis_claim_id)&base_ids),'n_sources_not_in_primary72':len(set(sel.analysis_claim_id)-base_ids)})
    write('source_bootstrap_components.csv',summaries);write('shared_component_bootstrap.csv',components)
    write('source_support.csv',support);write('leave_project_out.csv',lopo);write('within_project.csv',project);write('project_standardized.csv',standard)
    write('leave_source_out.csv',loco);write('timing_filter_shift.csv',timing)
    write('nondecomposable_sources.csv',mainfit[~mainfit.decomposition_eligible])
    write('all_timing_source_estimates.csv',pd.concat([v.assign(timing=k) for k,v in configs.items()],ignore_index=True))
    influence=[]
    for f in FEATURES:
        ff=[r for r in loco if r['feature']==f]
        influence.append({'feature':f,'minimum_source_deletion_estimate':min(r['estimate_omitting_source'] for r in ff),'maximum_source_deletion_estimate':max(r['estimate_omitting_source'] for r in ff),
           'maximum_absolute_source_deletion_change':max(abs(r['change_from_full_estimate']) for r in ff),
           'top_five_absolute_signed_contributions':sorted(ff,key=lambda r:abs(r['signed_contribution_to_full_contrast']),reverse=True)[:5]})
    (OUT/'influence_summary.json').write_text(json.dumps(influence,indent=2)+'\n')
    method={'protocol_sha256':PROTOCOL_HASH,'input_sha256':{str(p.relative_to(ROOT.parent)):sha(p) for p in paths},
      'script_sha256':sha(Path(__file__)),'bootstrap_replicates':B,'seed':SEED,'features':FEATURES,'configs':CONFIGS,
      'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'archive_identity_checks':checks,
      'interpretation':'Post hoc descriptive algebra and sensitivity; no semantic ground truth, causal effect, or claim-level response validation.'}
    (OUT/'method.json').write_text(json.dumps(method,indent=2)+'\n')
    print(pd.DataFrame(summaries).query("feature=='replication_word_tokens'").to_string(index=False))
    print('\nLOPO\n',pd.DataFrame(lopo).query("feature=='replication_word_tokens'").to_string(index=False))
    print('\nTIMING\n',pd.DataFrame(timing).query("feature=='replication_word_tokens'").to_string(index=False))
    print('\nPROJECT\n',pd.DataFrame(project).query("feature=='replication_word_tokens'").to_string(index=False))
    print('\nSTANDARDIZED\n',pd.DataFrame(standard).query("feature=='replication_word_tokens'").to_string(index=False))
    print('\nINFLUENCE\n',json.dumps(influence[1],indent=2))

if __name__=='__main__': main()
