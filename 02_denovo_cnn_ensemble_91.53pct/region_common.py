#!/usr/bin/env python3
"""region_common.py - overlapping per-region basecalling + stitch helpers.

Shared by train_region_split.py (train one region CNN per region for ANY
split) and eval_region_stitch.py (BLAST acceptance with overlap margins).

Model naming: region_split<N>_r<r>.keras for an N-region split, r in 0..N-1.
The 4-region config is special-cased to the existing v3 models
(base_caller_model_v3_{begin,mid,tail,tailtail}.keras).
"""
import os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

import extract_v3 as ex

LABELS = 'ACGT'
REGION_NAMES4 = ['begin', 'mid', 'tail', 'tailtail']

# candidate splits for the "how many regions" sweep.
# cuts = region upper boundaries in rank fraction; n_regions = len(cuts)+1.
SPLITS = {
    2: {'cuts': [0.30]},
    3: {'cuts': [0.20, 0.70]},
    4: {'cuts': [0.15, 0.65, 0.90]},
    5: {'cuts': [0.12, 0.35, 0.62, 0.85]},
    6: {'cuts': [0.10, 0.27, 0.47, 0.67, 0.85]},
    7: {'cuts': [0.10, 0.30, 0.50, 0.70, 0.82, 0.92]},
    8: {'cuts': [0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90]},
    9: {'cuts': [0.05, 0.15, 0.30, 0.45, 0.60, 0.70, 0.80, 0.94]},
}

# how each split chooses its model files: default tag 's' (region_splitN),
# '4' previously trained under the v3 names; keep them by default.
SPLIT_TAGS = {4: 'v3'}

SPLIT_JSON = os.path.join(HERE, 'region_splits.json')


def region_of(frac, cuts):
    r = 0
    for c in cuts:
        if frac >= c:
            r += 1
        else:
            break
    return r


def region_bounds(cuts):
    """Interval [lo, hi] per region index (0..n_regions-1)."""
    n = len(cuts) + 1
    lo = [0.0] * n
    for r in range(1, n):
        lo[r] = cuts[r - 1]
    hi = cuts + [1.0]
    return [(lo[r], hi[r]) for r in range(n)]


def covering_regions(frac, cuts, margin=0.0):
    """Region indices whose domain [+- margin in rank] covers frac."""
    out = [r for r, (lo, hi) in enumerate(region_bounds(cuts))
           if lo - margin <= frac <= hi + margin]
    return out or [region_of(frac, cuts)]


def stitch_call(P_all, covering, method):
    """Given probs dict {region_idx: (5,) prob vector} covering a base,
    return the called base index (0..3).

    methods:
      none   - use the single covering region (baseline == v3 at margin 0)
      conf   - choose the covering model with highest max-class prob
      vote   - elementwise mean of class probs over covering models
      wmax   - elementwise max of class probs over covering models
    """
    idx = sorted(covering)
    P = np.stack([P_all[r][:4] for r in idx])
    if method == 'none':
        return int(P_all[idx[0]][:4].argmax())
    if method == 'conf':
        best = idx[0]
        for r in idx:
            if P_all[r][:4].max() > P_all[best][:4].max():
                best = r
        return int(P_all[best][:4].argmax())
    if method == 'vote':
        return int(P.mean(0).argmax())
    if method == 'wmax':
        return int(P.max(0).argmax())
    raise ValueError(f'unknown stitch {method}')


def split_name(n):
    return f'region_split{n}'


def model_path(n, r, tag):
    if tag == 'v3':
        if n != 4:
            raise ValueError('v3 model set only exists for n=4')
        return os.path.join(HERE, f'base_caller_model_v3_{REGION_NAMES4[r]}.keras')
    if tag in (None, '', 's'):
        return os.path.join(HERE, f'{split_name(n)}_r{r}.keras')
    return os.path.join(HERE, f'{split_name(n)}_{tag}_r{r}.keras')


def load_models(n, tag):
    import tensorflow as tf
    mm = {}
    for r in range(n):
        p = model_path(n, r, tag)
        if not os.path.isfile(p):
            return None, [f'missing {p}']
        mm[r] = tf.keras.models.load_model(p, compile=False)
    return mm, None


def predict_all_models(models, Xn, n_regions):
    """xn: normalized (N, win, 4). Return dict r -> probs (N,5)."""
    out = {}
    for r in range(n_regions):
        out[r] = models[r].predict(Xn, batch_size=256, verbose=0)
    return out


def build_windows(ch, scans, w=ex.WINDOW):
    n = len(ch)
    X = np.zeros((len(scans), 2 * w + 1, 4), np.float32)
    for i, s in enumerate(scans):
        lo, hi = s - w, s + w + 1
        win = ch[max(0, lo):min(n, hi)]
        if lo < 0 or hi > n:
            win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)),
                         mode='edge')
        X[i] = win
    return X


def zscore(X):
    mu = X.mean(1, keepdims=True)
    sd = X.std(1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def save_splits_json():
    data = {str(k): dict(v, tag=SPLIT_TAGS.get(k, 's'))
            for k, v in SPLITS.items()}
    with open(SPLIT_JSON, 'w') as f:
        json.dump(data, f, indent=1)


if __name__ == '__main__':
    save_splits_json()
    print(f"wrote {SPLIT_JSON}: { {k: SPLITS[k]['cuts'] for k in SPLITS} }")