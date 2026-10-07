#!/usr/bin/env python3
"""Frozen literal-token observables. No semantic classifications or model calls."""
from __future__ import annotations
import re
import unicodedata
from collections import Counter
ADVERBS=('possibly','perhaps','probably')
REPLICATION=('replicate','replicates','replicated','replicating','replication','replications')
MODALS=('may','might','could')
WORDS=ADVERBS+REPLICATION+MODALS
FAMILIES={'epistemic_adverb_tokens':ADVERBS,'replication_word_tokens':REPLICATION,'lowercase_modal_tokens':MODALS}
def token_spans(text):
    # Consume maximal candidates first, so an invalid suffix cannot backtrack
    # into a false bare-token hit. Combining marks stay with their candidate.
    def wordchar(ch):
        return ch.isalnum() or ch=='_' or unicodedata.category(ch).startswith('M')
    i=0
    while i<len(text):
        if not wordchar(text[i]):
            i+=1;continue
        start=i
        while i<len(text) and wordchar(text[i]):i+=1
        while i+1<len(text) and text[i] in ("'",'’') and wordchar(text[i+1]):
            i+=1
            while i<len(text) and wordchar(text[i]):i+=1
        original=text[start:i];parts=re.split("['’]",original)
        if len(parts)<=2 and all(part.isalpha() for part in parts):
            yield start,i,original
RIGHT_NUMBER=re.compile(r'^[\s,./-]+[0-9]{1,4}(?!\w)')
LEFT_NUMBER=re.compile(r'(?<!\w)[0-9]{1,4}[\s,./-]+$')
VIEWS={'full':None,'first700_complete_tokens':700,'first1200_complete_tokens':1200}

def numeric_adjacent(text,start,end):
    return bool(RIGHT_NUMBER.search(text[end:]) or LEFT_NUMBER.search(text[:start]))

def features(text,limit=None):
    count=Counter();excluded_case=Counter();excluded_number=Counter();n_tokens=0
    for start,end,original in token_spans(text):
        if limit is not None and end>limit:continue
        n_tokens+=1;tok=original.replace('’',"'").casefold()
        if tok in ADVERBS:count[tok]+=1
        rep=tok[:-2] if tok.endswith("'s") else tok
        if rep in REPLICATION:count[rep]+=1
        if tok in MODALS:
            if original not in MODALS:excluded_case[tok]+=1
            elif tok=='may' and numeric_adjacent(text,start,end):excluded_number[tok]+=1
            else:count[tok]+=1
    out={'n_tokens':n_tokens,'n_characters':len(text) if limit is None else min(len(text),limit)}
    for word in WORDS:out[f'token_{word}']=count[word];out[f'context_{word}']=int(count[word]>0)
    for family,words in FAMILIES.items():out[f'token_{family}']=sum(count[w] for w in words);out[f'context_{family}']=int(any(count[w] for w in words))
    out['excluded_modal_case']=sum(excluded_case.values());out['excluded_may_numeric']=excluded_number['may']
    for word in MODALS:out[f'excluded_case_{word}']=excluded_case[word]
    return out
