#!/usr/bin/env python3
"""Separate pre-declared scope sensitivity: add the archived Staunton target only.
The conservative105-source main analysis and frozen literal rules stay unchanged.
"""
from pathlib import Path
import csv,hashlib,json,sys,importlib.util
from dataclasses import asdict
from collections import defaultdict,Counter
ROOT=Path(__file__).resolve().parent/'data/literal';BASE=ROOT.parent/'core'
sys.path.insert(0,str(Path(__file__).resolve().parent))
import analysis_core as ac
from literal_features import features,FAMILIES,VIEWS
from analyze_literal_counts import select_and_fit,summarize,Config,write,read

def main():
    source=BASE/'inputs/analysis_ledger.csv'
    meta=read(source);added=next(r for r in meta if r['source_id']=='rpp.73');claim=added['analysis_claim_id']
    definition={'name':'106-source archived-Staunton-selected-target sensitivity','primary_cohort_remains':105,'additional_source_id':'rpp.73',
       'rule':'Archived selected Staunton contrast: predicted-direction nominal significance by Pearson chi-square goodness-of-fit against local Democratic/Republican voter proportions .30/.70; no source-wide aggregation is imposed.',
       'n':120,'democratic_count':25,'republican_count':95,'chi_square':4.801587301587,'pearson_p':.0284335289139828,'signed_phi':.2000330660,
       'important_distinction':'The unrounded Pearson p is not an exact-binomial p. Broader multi-site scope remains an inclusion choice; this row is not silently promoted into the105-source main analysis.',
       'source_cohort_sha256':json.loads((BASE/'inputs/cohort_version.json').read_text())['source_cohort_sha256'],'sources':{'report':'https://osf.io/download/2jwi6/','count_workbook':'https://osf.io/download/ftzbj/','selection_script':'https://osf.io/download/hau4p/','registered_protocol':'https://osf.io/download/n6m5d/','registration':'https://osf.io/hctz9/'}}
    out=ROOT.parents[1]/'results/literal';(out/'staunton_sensitivity_definition.json').write_text(json.dumps(definition,indent=2)+'\n')
    # Frozen-model three endpoints, using the original numerical estimator.
    records=ac.load_inputs(BASE/'inputs');ledger=ac.read_csv(BASE/'inputs/analysis_ledger.csv');changed=[]
    for r in ledger:
        z=dict(r)
        if z['source_id']=='rpp.73':z['revised_outcome']='successful';z['include_primary']='True'
        changed.append(z)
    result,fits,_=ac.evaluate(records,changed,ac.Config())
    assert result['n_papers']==106 and result['n_texts']==15302 and result['n_positive_texts']==8443
    model={k:result['metrics'][k] for k in ac.PRIMARY_METRICS}
    (out/'staunton106_frozen_model_sensitivity.json').write_text(json.dumps({'definition':definition,'n_papers':106,'n_texts':15302,'n_positive_texts':8443,'primary_event_convention':'journal publication year','metrics':model},indent=2)+'\n')
    # Only the newly admitted source text is processed; the frozen105 aggregates are retained.
    rows=read(ROOT/'inputs/literal_counts_by_source_year.csv')
    for r in rows:
        for k in r:
            if k not in ('analysis_claim_id','source_id','text_view'):r[k]=int(r[k])
    extra=read(ROOT/'inputs/staunton_added_source_counts.csv')
    for r in extra:
        for k in r:
            if k not in ('analysis_claim_id','source_id','text_view'):r[k]=int(r[k])
    assert sum(r['n_texts'] for r in extra if r['text_view']=='full')==22
    assert sum(r['n_texts']*r['assertion'] for r in extra if r['text_view']=='full')==16
    meta105={r['analysis_claim_id']:r for r in read(ROOT/'inputs/source_cohort.csv')};meta106={**meta105,claim:{**added,'revised_outcome':'successful','include_primary':'True'}}
    contrasts=[];support=[]
    for stratum in ('all','positive'):
        fits=select_and_fit(rows+extra,meta106,Config(stratum=stratum));contrasts.extend(summarize(fits,'staunton106_'+stratum,['level_incidence','event_incidence'],FAMILIES))
        support.extend({'stratum':stratum,**r} for r in fits if r['analysis_claim_id']==claim)
    write(out/'staunton106_literal_sensitivity.csv',contrasts);write(out/'staunton106_added_source_support.csv',support)
    counts=[]
    for f in FAMILIES:
        for st in ('all','positive','negative'):
            xx=[r for r in extra if r['text_view']=='full' and (st=='all' or r['assertion']==int(st=='positive'))]
            counts.append({'stratum':st,'feature':f,'added_text_units':sum(r['n_texts'] for r in xx),'added_hit_contexts':sum(r['context_'+f] for r in xx),'added_occurrences':sum(r['token_'+f] for r in xx)})
    write(out/'staunton106_added_literal_counts.csv',counts)
    print(json.dumps({'frozen_model':model,'added_literal_counts':counts},indent=2))
if __name__=='__main__':main()
