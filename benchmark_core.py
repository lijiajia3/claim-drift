#!/usr/bin/env python3
"""Finite-corpus retention reference models. No network or model inference."""
from __future__ import annotations
import csv
from collections import defaultdict
from pathlib import Path
import numpy as np

FAMILIES = ['epistemic_adverb_tokens', 'replication_word_tokens', 'lowercase_modal_tokens']
SCHEMES = ['volume', 'volume_year', 'volume_year_length']
BITS = np.array([[(p >> j) & 1 for j in range(3)] for p in range(8)], dtype=np.int64)
SEED = 2026100602
DRAWS = 19999



def write_csv(path, rows):
    with Path(path).open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def length_band(n):
    return int(np.searchsorted([70, 351, 701, 1201], n, side='right'))


def moments(colors, k):
    colors = np.asarray(colors, dtype=np.int64)
    n = int(colors.sum())
    assert n > 0 and 0 <= k <= n
    h = colors @ BITS
    p = h / n
    mean = k * p
    if n == 1 or k == 0 or k == n:
        variance = np.zeros(3)
    else:
        variance = k * p * (1 - p) * (n - k) / (n - 1)
    return mean, variance


def sample_hits(colors, k, rng, draws):
    colors = np.asarray(colors, dtype=np.int64)
    if k == 0:
        return np.zeros((draws, 3), dtype=np.int64)
    if k == colors.sum():
        return np.broadcast_to(colors @ BITS, (draws, 3)).copy()
    return rng.multivariate_hypergeometric(colors, k, size=draws) @ BITS



def analyze(rows, source_rows, group, weights, n, k, h, all_inc, observed_inc, d, observed, out):
    rng = np.random.default_rng(SEED)
    result_rows, support_rows, source_outputs, project_rows = [], [], [], []
    strata_outputs, mc_checks = [], []
    baseline = -(weights @ (all_inc[:, 1] - all_inc[:, 0]))
    coefficients = weights[:, None] * np.array([-1, 1])[None, :] / k
    for scheme in SCHEMES:
        strata = defaultdict(lambda: {'colors': np.zeros(8, dtype=np.int64), 'k': 0})
        for r in rows:
            key = (r['source_index'], r['period'])
            if scheme != 'volume':
                key += (r['year'],)
            if scheme == 'volume_year_length':
                key += (r['length_band'],)
            strata[key]['colors'][r['marker_pattern']] += 1
            strata[key]['k'] += r['assertion']
        sim = np.broadcast_to(baseline, (DRAWS, 3)).copy()
        exp_h = np.zeros_like(h, dtype=float)
        var_d = np.zeros(3)
        random_n = random_k = random_strata = 0
        random_hits = np.zeros(3, dtype=np.int64)
        variable_strata = np.zeros(3, dtype=np.int64)
        recovered_n = np.zeros_like(n)
        recovered_k = np.zeros_like(k)
        for key, value in sorted(strata.items()):
            i, t = key[:2]
            colors, ks = value['colors'], value['k']
            ns, hs = int(colors.sum()), colors @ BITS
            recovered_n[i, t] += ns
            recovered_k[i, t] += ks
            mean, variance = moments(colors, ks)
            exp_h[i, t] += mean
            var_d += coefficients[i, t] ** 2 * variance
            sim += coefficients[i, t] * sample_hits(colors, ks, rng, DRAWS)
            randomizable = 0 < ks < ns
            if randomizable:
                random_strata += 1
                random_n += ns
                random_k += ks
                random_hits += hs
                variable_strata += (hs > 0) & (hs < ns)
            strata_outputs.append({'scheme': scheme, 'source_index': i, 'period': t,
                                   'year': key[2] if len(key) > 2 else '',
                                   'length_band': key[3] if len(key) > 3 else '',
                                   'n': ns, 'k': ks,
                                   **{f'pattern_{j}': int(v) for j, v in enumerate(colors)}})
        assert np.array_equal(recovered_n, n) and np.array_equal(recovered_k, k)
        expected_inc = exp_h / k[..., None]
        expected_gap = expected_inc - all_inc
        expected_d = expected_gap[:, 1] - expected_gap[:, 0]
        expected = weights @ expected_d
        if scheme == 'volume':
            assert np.max(np.abs(expected)) < 1e-13
        for j, family in enumerate(FAMILIES):
            lo, hi = np.quantile(sim[:, j], [0.025, 0.975])
            se = np.sqrt(var_d[j] / DRAWS)
            error = float(sim[:, j].mean() - expected[j])
            z = error / se if se > 0 else 0.
            assert abs(z) < 6, ('unexpected Monte Carlo mean error', scheme, family, z)
            result_rows.append({'scheme': scheme, 'feature': family,
                                'observed': observed[j], 'reference_expectation': expected[j],
                                'observed_minus_expected': observed[j] - expected[j],
                                'reference_q025': lo, 'reference_q975': hi,
                                'reference_sd_simulated': sim[:, j].std(ddof=1),
                                'reference_sd_analytic': np.sqrt(var_d[j]),
                                'observed_outside_reference_envelope': bool(observed[j] < lo or observed[j] > hi)})
            support_rows.append({'scheme': scheme, 'feature': family,
                                 'n_strata': len(strata), 'randomizable_strata': random_strata,
                                 'marker_variable_strata': variable_strata[j],
                                 'all_texts': int(n.sum()), 'retained_texts': int(k.sum()),
                                 'all_hits': int(h[..., j].sum()),
                                 'randomizable_texts': random_n, 'randomizable_retained_texts': random_k,
                                 'randomizable_family_hits': random_hits[j],
                                 'fraction_texts_randomizable': random_n / n.sum(),
                                 'fraction_retained_randomizable': random_k / k.sum(),
                                 'fraction_family_hits_randomizable': random_hits[j] / h[..., j].sum() if h[..., j].sum() else ''})
            mc_checks.append({'scheme': scheme, 'feature': family, 'mean_error': error,
                              'mean_monte_carlo_se': se, 'mean_error_z': z})
        for i, m in enumerate(source_rows):
            for j, family in enumerate(FAMILIES):
                source_outputs.append({**m, 'scheme': scheme, 'feature': family,
                                       'n_pre': n[i, 0], 'n_post': n[i, 1],
                                       'k_pre': k[i, 0], 'k_post': k[i, 1],
                                       'all_pre': all_inc[i, 0, j], 'all_post': all_inc[i, 1, j],
                                       'observed_pre': observed_inc[i, 0, j], 'observed_post': observed_inc[i, 1, j],
                                       'expected_pre': expected_inc[i, 0, j], 'expected_post': expected_inc[i, 1, j],
                                       'observed_filter_shift': d[i, j],
                                       'expected_filter_shift': expected_d[i, j],
                                       'residual': d[i, j] - expected_d[i, j]})
        if scheme == 'volume_year_length':
            projects = np.array([r['project'] for r in source_rows])
            residuals = d - expected_d
            for project in sorted(set(projects)):
                for mode in ['within_project', 'leave_project_out']:
                    mask = projects == project if mode == 'within_project' else projects != project
                    neg, pos = mask & group, mask & ~group
                    for j, family in enumerate(FAMILIES):
                        project_rows.append({'project': project, 'mode': mode, 'feature': family,
                                             'n_negative': int(neg.sum()), 'n_positive': int(pos.sum()),
                                             'observed': float(d[neg, j].mean() - d[pos, j].mean()),
                                             'expected': float(expected_d[neg, j].mean() - expected_d[pos, j].mean()),
                                             'residual': float(residuals[neg, j].mean() - residuals[pos, j].mean())})
        np.save(out / f'{scheme}_reference_draws.npy', sim)
    for name, values in [('benchmark_results', result_rows), ('benchmark_support', support_rows),
                         ('source_results', source_outputs), ('project_concentration', project_rows),
                         ('strata_pattern_counts', strata_outputs), ('monte_carlo_checks', mc_checks)]:
        write_csv(out / f'{name}.csv', values)

