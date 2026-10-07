#!/usr/bin/env python3
"""Reproduce descriptive counts from eight selected article labels and twelve gate flags."""
from pathlib import Path
from collections import defaultdict
import csv,json,hashlib
P=Path(__file__).resolve().parent/'data/external'
read=lambda p:list(csv.DictReader(p.open(encoding='utf-8-sig')))
labels=read(P/'inputs/selected_article_labels.csv'); contexts=read(P/'inputs/selected_context_gate_inputs.csv'); pairs=read(P/'reported_results/article_case_audit.csv');ledger=read(P/'reported_results/source_recovery_ledger.csv');summary=read(P/'reported_results/case_valence_summary.csv')
assert len(labels)==len(pairs)==8 and len(contexts)==12
assert len({r['doi'] for r in pairs})==7 and sum(int(r['gate_retained']) for r in contexts)==11
assert len(ledger)==12 and len({r['doi'] for r in ledger})==10
assert sum(r['recovery_state']=='recovered' for r in ledger)==10
assert len({r['doi'] for r in ledger if r['recovery_state']=='recovered'})==8
assert sum(int(r['eligible_linked_contexts']) for r in ledger if r['eligible_linked_contexts'])==12
assert sum(int(r['recovered_target_paragraph_case_units']) for r in ledger if r['recovered_target_paragraph_case_units'])==21
assert sum(int(r['linked_target_paragraph_case_units']) for r in ledger if r['linked_target_paragraph_case_units'])==11
original={(r['doi'],r['case']):r for r in labels}; grouped=defaultdict(list)
for r in contexts:grouped[r['doi'],r['case']].append(r)
for r in pairs:
 key=r['doi'],r['case']; old=original[key]; assert old['excluded'].strip().casefold()=='false';v=old['citationClassificationAgreed'].strip().casefold(); v={'favourable':'favorable','unfavourable':'unfavorable'}.get(v,v);assert v==r['adjudicated_article_valence'];cc=grouped[key];assert len(cc)==int(r['eligible_archived_contexts']);assert sum(int(x['gate_retained']) for x in cc)==int(r['gate_retained_contexts'])
for r in summary:
 pp=[p for p in pairs if p['case']==r['case'] and p['adjudicated_article_valence']==r['article_valence']];n=sum(int(p['eligible_archived_contexts']) for p in pp);ret=sum(int(p['gate_retained_contexts']) for p in pp)
 for col,value in [('article_case_pairs',len(pp)),('distinct_citing_dois',len({p['doi'] for p in pp})),('eligible_archived_contexts',n),('gate_retained_contexts',ret),('gate_excluded_contexts',n-ret)]: assert int(r[col])==value
 if n:assert abs(float(r['pooled_context_retention_fraction'])-ret/n)<1e-12;assert abs(float(r['article_balanced_retention_fraction'])-sum(int(p['gate_retained_contexts'])/int(p['eligible_archived_contexts']) for p in pp)/len(pp))<1e-12
 else:assert r['pooled_context_retention_fraction']==r['article_balanced_retention_fraction']==''
print('PASS: all eight case-by-valence rows, eight article-case joins, twelve gate inputs and the complete twelve-row recovery ledger reproduce.')
print('No unfavorable or unclassifiable examples; differential coverage of criticism is not estimable. No inference or certainty validation is performed.')
