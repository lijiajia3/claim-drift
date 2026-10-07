#!/usr/bin/env python3
"""Analyze frozen aggregate literal counts; no text, labels or models are generated."""
from pathlib import Path
from collections import Counter,defaultdict
from dataclasses import dataclass,asdict
import csv,json,math,hashlib
import numpy as np
from literal_features import WORDS,FAMILIES,VIEWS
ROOT=Path(__file__).resolve().parent/'data/literal';REPS=19999;SEED=20261005
FEATURES=tuple(FAMILIES)+WORDS

def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def boot(a,b,reps=REPS,seed=SEED):
    a=np.asarray(a,float);b=np.asarray(b,float);rng=np.random.default_rng(seed);out=[]
    for start in range(0,reps,1000):
        n=min(1000,reps-start);out.extend((a[rng.integers(len(a),size=(n,len(a)))].mean(1)-b[rng.integers(len(b),size=(n,len(b)))].mean(1)).tolist())
    return np.quantile(out,[.025,.975]).tolist()
def contrast(a,b):
    out={'n_negative':len(a),'n_positive':len(b),'mean_negative':float(np.mean(a)) if len(a) else None,'mean_positive':float(np.mean(b)) if len(b) else None}
    if not len(a) or not len(b):return {**out,'estimate':None,'ci95_low':None,'ci95_high':None}
    est=float(np.mean(a)-np.mean(b));out['estimate']=est
    if len(a)<2 or len(b)<2:return {**out,'ci95_low':None,'ci95_high':None,'warning':'fewer than two sources in a group'}
    lo,hi=boot(a,b);out.update(ci95_low=lo,ci95_high=hi)
    if len(set(a))==1 or len(set(b))==1:out['warning']='At least one source group has no observed variation; conditional bootstrap can be degenerate'
    return out
@dataclass(frozen=True)
class Config:
    view:str='full'
    stratum:str='all'
    event_column:str='event_year_journal'
    omit_event_year:bool=False
    window:int=0
    latest:bool=False

def select_and_fit(rows,meta,cfg):
    selected=[r for r in rows if r['text_view']==cfg.view and (cfg.stratum=='all' or r['assertion']==int(cfg.stratum=='positive'))]
    by=defaultdict(list)
    for r in selected:by[r['analysis_claim_id']].append(r)
    fitted=[]
    def pool(rs):
        out=Counter()
        for r in rs:
            for k,v in r.items():
                if isinstance(v,int) and k not in ('year','latest_year','assertion'):out[k]+=v
        return out
    for name,m in sorted(meta.items()):
        rr=by[name];ev=int(m[cfg.event_column]);year=lambda r:r['latest_year'] if cfg.latest else r['year']
        pre=[r for r in rr if year(r)<ev and (not cfg.window or year(r)>=ev-cfg.window)]
        post=[r for r in rr if year(r)>=ev+int(cfg.omit_event_year) and (not cfg.window or year(r)<=ev+cfg.window)]
        total,a,b=pool(rr),pool(pre),pool(post)
        for feature in FEATURES:
            ch='context_'+feature;th='token_'+feature
            item={'analysis_claim_id':name,'source_id':m['source_id'],'project':m['project'],'criterion':m['revised_outcome'],'feature':feature,
                  'n_all':total['n_texts'],'n_pre':a['n_texts'],'n_post':b['n_texts'],'hit_all':total[ch],'hit_pre':a[ch],'hit_post':b[ch],
                  'tokens_all':total['n_tokens'],'tokens_pre':a['n_tokens'],'tokens_post':b['n_tokens'],
                  'occurrences_all':total[th],'occurrences_pre':a[th],'occurrences_post':b[th]}
            if total['n_texts']>=15:
                item['level_incidence']=total[ch]/total['n_texts'];item['level_token_density']=1000*total[th]/total['n_tokens'] if total['n_tokens'] else None
            if min(a['n_texts'],b['n_texts'])>=10:
                item.update(pre_incidence=a[ch]/a['n_texts'],post_incidence=b[ch]/b['n_texts'],event_incidence=b[ch]/b['n_texts']-a[ch]/a['n_texts'])
                if a['n_tokens'] and b['n_tokens']:item['event_token_density']=1000*(b[th]/b['n_tokens']-a[th]/a['n_tokens'])
            fitted.append(item)
    return fitted

def summarize(fits,scenario,endpoints,features):
    out=[]
    for feature in features:
        for endpoint in endpoints:
            rows=[r for r in fits if r['feature']==feature and r.get(endpoint) is not None]
            a=[r[endpoint] for r in rows if r['criterion']=='failed'];b=[r[endpoint] for r in rows if r['criterion']=='successful']
            out.append({'scenario':scenario,'feature':feature,'endpoint':endpoint,**contrast(a,b),
                'sources_with_any_full_history_hit_negative':sum(r['hit_all']>0 for r in rows if r['criterion']=='failed'),
                'sources_with_any_full_history_hit_positive':sum(r['hit_all']>0 for r in rows if r['criterion']=='successful'),
                'full_history_text_units':sum(r['n_all'] for r in rows),
                'sources_with_any_event_period_hit_negative':sum((r['hit_pre']+r['hit_post'])>0 for r in rows if r['criterion']=='failed'),
                'sources_with_any_event_period_hit_positive':sum((r['hit_pre']+r['hit_post'])>0 for r in rows if r['criterion']=='successful'),
                'event_period_text_units':sum(r['n_pre']+r['n_post'] for r in rows),'pre_text_units':sum(r['n_pre'] for r in rows),'post_text_units':sum(r['n_post'] for r in rows)})
    return out

def raw_summaries(rows,meta):
    result=[]
    for view in VIEWS:
        for stratum in ('all','positive','negative'):
            rr=[r for r in rows if r['text_view']==view and (stratum=='all' or r['assertion']==int(stratum=='positive'))]
            for group in ('all','failed','successful'):
                g=[r for r in rr if group=='all' or meta[r['analysis_claim_id']]['revised_outcome']==group]
                for feature in FEATURES:
                    den=sum(r['n_texts'] for r in g);nt=sum(r['n_tokens'] for r in g);hits=sum(r['context_'+feature] for r in g);occ=sum(r['token_'+feature] for r in g)
                    result.append({'text_view':view,'stratum':stratum,'criterion':group,'feature':feature,'n_text_units':den,'n_alphabetic_tokens':nt,'n_texts_with_feature':hits,'n_feature_occurrences':occ,'raw_context_fraction':hits/den if den else None,'occurrences_per1000_tokens':occ/nt*1000 if nt else None,'n_source_papers':len({r['analysis_claim_id'] for r in g}),'n_papers_with_feature':len({r['analysis_claim_id'] for r in g if r['context_'+feature]})})
    return result

def component_intervals(fits,membership,scenario,endpoints=('level_incidence','event_incidence')):
    # The fixed primary105 graph resamples groups of sources sharing exact archived text.
    clusters=defaultdict(list)
    for r in membership:clusters[int(r['component_id'])].append(r['analysis_claim_id'])
    names=list(clusters.values());out=[]
    for feature in FAMILIES:
        for metric in endpoints:
            by={r['analysis_claim_id']:r for r in fits if r['feature']==feature and r.get(metric) is not None};ss=np.zeros((len(names),2));ns=np.zeros_like(ss)
            for j,ids in enumerate(names):
                for name in ids:
                    if name in by:
                        r=by[name];k=int(r['criterion']=='successful');ss[j,k]+=r[metric];ns[j,k]+=1
            rng=np.random.default_rng(SEED);draw=[]
            for start in range(0,REPS,1000):
                inds=rng.integers(len(names),size=(min(1000,REPS-start),len(names)));s=ss[inds].sum(1);n=ns[inds].sum(1);okay=(n>0).all(1);ratio=s[okay]/n[okay];draw.extend((ratio[:,0]-ratio[:,1]).tolist())
            out.append({'scenario':scenario,'feature':feature,'endpoint':metric,'n_components':len(names),'largest_component':max(map(len,names)),'estimate':ss.sum(0)[0]/ns.sum(0)[0]-ss.sum(0)[1]/ns.sum(0)[1],'ci95_low':float(np.quantile(draw,.025)),'ci95_high':float(np.quantile(draw,.975)),'note':'Known shared-text components only; unknown shared citing-paper dependence is not resolved'})
    return out

def main():
    out=ROOT.parents[1]/'results/literal';out.mkdir(exist_ok=True,parents=True);rows=read(ROOT/'inputs/literal_counts_by_source_year.csv');meta={r['analysis_claim_id']:r for r in read(ROOT/'inputs/source_cohort.csv')}
    for r in rows:
        for k in r:
            if k not in ('analysis_claim_id','source_id','text_view'):r[k]=int(r[k])
    assert len(meta)==105 and len([m for m in meta.values() if m['revised_outcome']=='failed'])==57
    raw=raw_summaries(rows,meta);write(out/'raw_counts_all_words_and_families.csv',raw)
    retention=[]
    for view in VIEWS:
        for feature in FEATURES:
            match={r['stratum']:r for r in raw if r['text_view']==view and r['criterion']=='all' and r['feature']==feature}
            a,p,n=[match[x] for x in ('all','positive','negative')]
            assert a['n_texts_with_feature']==p['n_texts_with_feature']+n['n_texts_with_feature']
            retention.append({'text_view':view,'feature':feature,'all_hit_contexts':a['n_texts_with_feature'],'qwen_positive_hit_contexts':p['n_texts_with_feature'],'qwen_negative_hit_contexts':n['n_texts_with_feature'],'positive_retention_fraction':p['n_texts_with_feature']/a['n_texts_with_feature'] if a['n_texts_with_feature'] else None,'n_all':a['n_text_units'],'n_positive':p['n_text_units'],'n_negative':n['n_text_units']})
    write(out/'qwen_retention_by_literal_feature.csv',retention)
    configs={};summary=[];paper=[];fits_by={}
    for stratum in ('all','positive','negative'):
        key='full_'+stratum;cfg=Config(stratum=stratum);fits=select_and_fit(rows,meta,cfg);fits_by[key]=fits;configs[key]=asdict(cfg)
        summary.extend(summarize(fits,key,['level_incidence','event_incidence'],FEATURES));summary.extend(summarize(fits,key,['level_token_density','event_token_density'],FAMILIES));paper.extend({'scenario':key,**r} for r in fits)
    for view in ('first700_complete_tokens','first1200_complete_tokens'):
        for stratum in ('all','positive'):
            key=view+'_'+stratum;cfg=Config(view=view,stratum=stratum);fits=select_and_fit(rows,meta,cfg);configs[key]=asdict(cfg);summary.extend(summarize(fits,key,['level_incidence','event_incidence'],FAMILIES));paper.extend({'scenario':key,**r} for r in fits)
    for timing,kw in [('recorded_manuscript_upload_years',{'event_column':'event_year_first_located_manuscript'}),('omit_event_year',{'omit_event_year':True}),('symmetric5_years_omit_event_year',{'omit_event_year':True,'window':5}),('latest_archived_year',{'latest':True})]:
        for stratum in ('all','positive'):
            key=timing+'_'+stratum;cfg=Config(stratum=stratum,**kw);fits=select_and_fit(rows,meta,cfg);configs[key]=asdict(cfg);summary.extend(summarize(fits,key,['event_incidence'],FAMILIES));paper.extend({'scenario':key,**r} for r in fits)
    write(out/'source_estimates_all_predefined_features.csv',paper);write(out/'source_bootstrap_contrasts.csv',summary)
    paired=[];pairest=[]
    for feature in FAMILIES:
        a={r['analysis_claim_id']:r for r in fits_by['full_all'] if r['feature']==feature and r.get('event_incidence') is not None}
        p={r['analysis_claim_id']:r for r in fits_by['full_positive'] if r['feature']==feature and r.get('event_incidence') is not None};ids=sorted(set(a)&set(p));ss=[]
        for name in ids:
            rr={'analysis_claim_id':name,'criterion':a[name]['criterion'],'feature':feature,'all_event_change':a[name]['event_incidence'],'positive_event_change':p[name]['event_incidence'],'filtered_minus_all_change':p[name]['event_incidence']-a[name]['event_incidence']};ss.append(rr);pairest.append(rr)
        for measure in ('all_event_change','positive_event_change','filtered_minus_all_change'):
            paired.append({'feature':feature,'measure':measure,**contrast([r[measure] for r in ss if r['criterion']=='failed'],[r[measure] for r in ss if r['criterion']=='successful'])})
    write(out/'matched_source_filter_comparison.csv',paired);write(out/'matched_source_filter_estimates.csv',pairest)
    membership=read(ROOT/'inputs/shared_text_component_membership.csv')
    comp=[r for key in ('full_all','full_positive') for r in component_intervals(fits_by[key],membership,key)];write(out/'shared_text_component_sensitivity.csv',comp)
    matched_components=component_intervals(pairest,membership,'matched_filter_shift',('filtered_minus_all_change',))
    write(out/'matched_filter_shared_component_sensitivity.csv',matched_components)
    lopo=[]
    for project in sorted({m['project'] for m in meta.values()}):
        ff=[r for r in fits_by['full_all'] if r['project']!=project];lopo.extend(summarize(ff,'omit_'+project,['level_incidence','event_incidence'],FAMILIES))
    write(out/'leave_project_out.csv',lopo)
    exclusions=[]
    for view in VIEWS:
        rr=[r for r in rows if r['text_view']==view]
        exclusions.append({'text_view':view,'excluded_modal_case':sum(r['excluded_modal_case'] for r in rr),'excluded_may_numeric':sum(r['excluded_may_numeric'] for r in rr),**{f'excluded_case_{w}':sum(r[f'excluded_case_{w}'] for r in rr) for w in ('may','might','could')}})
    write(out/'frozen_exclusion_counts.csv',exclusions)
    (out/'analysis_configurations.json').write_text(json.dumps(configs,indent=2)+'\n')
    (out/'method.json').write_text(json.dumps({'rules_sha256':hashlib.sha256((ROOT/'RULES_FROZEN.json').read_bytes()).hexdigest(),'cohort':json.loads((ROOT/'inputs/preparation_verification.json').read_text()),'bootstrap_replicates':REPS,'seed':SEED,'direction':'criterion-negative minus criterion-positive','primary_unit':'source-paper proportion of text units with at least one literal match','token_density_unit':'matched occurrences per1000 alphabetic tokens, source weighted','no_semantic_classification':True,'no_new_human_labels':True,'known_model_prompt_overlap':True,'all_words_and_predefined_specifications_retained':True},indent=2)+'\n')
    print(json.dumps([r for r in retention if r['text_view']=='full' and r['feature'] in FAMILIES],indent=2))
    print(json.dumps([r for r in summary if r['scenario']=='full_all' and r['endpoint']=='event_incidence' and r['feature'] in FAMILIES],indent=2))
if __name__=='__main__':main()
