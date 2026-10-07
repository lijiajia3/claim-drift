#!/usr/bin/env python3
"""Reproduce all reference estimates from portable text-free inputs."""
import argparse
import csv
import hashlib
from pathlib import Path
import numpy as np
from benchmark_core import BITS, FAMILIES, analyze

def read(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def main():
    base = Path(__file__).resolve().parent / 'data/retention'
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=base.parents[1] / 'results/retention')
    parser.add_argument('--strict-bytes', action='store_true',
                        help='Also require original CSV byte identity (runtime dependent).')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rows, sources = read(base / 'inputs/contexts_text_free.csv'), read(base / 'inputs/sources.csv')
    for r in rows:
        for field in ['year','assertion','n_characters','length_band','marker_pattern','source_index','period'] + FAMILIES:
            r[field] = int(r[field])
    for r in sources:
        r['event_year'] = int(r['event_year'])
    group = np.array([r['criterion'] == 'failed' for r in sources])
    assert len(sources) == 72 and group.sum() == 40
    weights = np.where(group, 1 / group.sum(), -1 / (~group).sum())
    n = np.zeros((72, 2), dtype=np.int64)
    k = n.copy()
    h = np.zeros((72, 2, 3), dtype=np.int64)
    actual_h = h.copy()
    for r in rows:
        i, t = r['source_index'], r['period']
        assert sources[i]['analysis_claim_id'] == r['analysis_claim_id']
        n[i, t] += 1
        k[i, t] += r['assertion']
        h[i, t] += BITS[r['marker_pattern']]
        actual_h[i, t] += r['assertion'] * BITS[r['marker_pattern']]
    assert n.sum() == 11999 and k.sum() == 6650 and np.all(k >= 10)
    all_inc, actual_inc = h / n[..., None], actual_h / k[..., None]
    gaps = actual_inc - all_inc
    d = gaps[:, 1] - gaps[:, 0]
    actual = weights @ d
    analyze(rows, sources, group, weights, n, k, h, all_inc, actual_inc, d, actual, args.out)
    for name in ['benchmark_results.csv','benchmark_support.csv','source_results.csv','project_concentration.csv','strata_pattern_counts.csv','monte_carlo_checks.csv']:
        expected = (base / 'reported_results' / name).read_bytes()
        reproduced = (args.out / name).read_bytes()
        from verify_results import check_csv
        check_csv(base / 'reported_results' / name, args.out / name)
        if args.strict_bytes:
            assert expected == reproduced, f'Output differs from reference: {name}'
        label = 'Byte-identical' if expected == reproduced else 'Numerically matched'
        print(f'{label}: {name} {hashlib.sha256(reproduced).hexdigest()}')
    print('All six analysis tables matched. Artificial selection envelopes are not population-effect confidence intervals.')

if __name__ == '__main__':
    main()
