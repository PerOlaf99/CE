#!/usr/bin/env python3
"""refine_on_v3.py - bolt the de-novo refine pass (drop + gap-fill + stutter
merge) onto the v3 per-region CNN reads and re-BLAST.

Hypothesis from the gap decomposition: the BLAST HSP truncates before our
tail because of the "middle" region's and tail's uncertain calls; a
confidence-gated drop plus gap-fill (borrowing the project's own
refine_denovo, which is fully de-novo) may extend the HSP / matched_bp.
"""
import os, sys
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, '/media/per/78B0C7DE1FA7081C/electropherogram/sanger_toolkit')
import extract_v3 as ex
import train_v3 as tv
from extract_training_data import parse_rsd, parse_esd
import tensorflow as tf
from blast_bench import blast_eval

LABELS = 'ACGT'
W = 15


def wall_probs(models, ch, scans, rank_fracs):
    """Region-aware CNN probs for arbitrary scans (batched by region)."""
    n = len(ch)
    Xall = np.zeros((len(scans), 2 * W + 1, 4), np.float32)
    for i, s in enumerate(scans):
        lo, hi = s - W, s + W + 1
        win = ch[max(0, lo):min(n, hi)]
        if lo < 0 or hi > n:
            win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
        Xall[i] = win
    mu = Xall.mean(1, keepdims=True)
    sd = Xall.std(1, keepdims=True) + 1e-8
    Xn = ((Xall - mu) / sd).astype(np.float32)
    rgv = np.array([ex.region_of(float(r)) for r in rank_fracs])
    out = np.zeros((len(scans), 5))
    for rg in sorted(set(rgv)):
        sel = np.where(rgv == rg)[0]
        out[sel] = models[int(rg)].predict(Xn[sel], batch_size=256, verbose=0)
    return out


def refine_lite(models, ch, scans, seq, rankf,
                drop_p=0.50, add_p=0.60, gap_frac=1.25, iters=3, jitter=2):
    scans = list(scans)
    seq = list(seq)
    rankf = list(rankf)
    probs = wall_probs(models, ch, scans, rankf)
    pmax = probs.max(1)
    keep = pmax >= drop_p
    seq = [b for b, k in zip(seq, keep) if k]
    sc_arr = np.asarray([s for s, k in zip(scans, keep) if k])
    rf = np.asarray([r for r, k in zip(rankf, keep) if k])
    for _ in range(iters):
        if len(sc_arr) < 3:
            break
        med = float(np.median(np.diff(sc_arr)))
        added = 0
        # candidate scans: midpoints of wide gaps
        cands = []
        for a, b in zip(sc_arr[:-1], sc_arr[1:]):
            gap = b - a
            if gap < gap_frac * med:
                continue
            need = max(0, int(round(gap / med)) - 1)
            for j in range(1, need + 1):
                c0 = int(a + round(gap * j / (need + 1)))
                cands.extend(range(c0 - jitter, c0 + jitter + 1))
        if not cands:
            break
        uniq = sorted(set(cands))
        # rank fraction for candidates ~ linear between neighbors
        urf = []
        for s in uniq:
            idx = np.searchsorted(sc_arr, s)
            if idx == 0:
                urf.append(0.0)
            elif idx >= len(sc_arr):
                urf.append(1.0)
            else:
                a, b = sc_arr[idx - 1], sc_arr[idx]
                urf.append(rf[idx - 1] + (s - a) / max(1.0, b - a) * (rf[idx] - rf[idx - 1]))
        cp = wall_probs(models, ch, uniq, urf)
        cdict = {}
        for k, s in enumerate(uniq):
            cdict[s] = (cp[k][:4].max(), cp[k][:4].argmax())
        for a, b in zip(sc_arr[:-1], sc_arr[1:]):
            gap = b - a
            if gap < gap_frac * med:
                continue
            need = max(0, int(round(gap / med)) - 1)
            for j in range(1, need + 1):
                c0 = int(a + round(gap * j / (need + 1)))
                opts = [(s, cdict[s]) for s in range(c0 - jitter, c0 + jitter + 1)
                        if s in cdict]
                if not opts:
                    continue
                best_s, (best_p, best_b) = max(opts, key=lambda t: t[1][0])
                if best_p >= add_p:
                    idx = np.searchsorted(sc_arr, best_s)
                    seq.insert(idx, LABELS[best_b])
                    sc_arr = np.insert(sc_arr, idx, best_s)
                    lo_r = rf[idx - 1] if idx > 0 else 0.0
                    hi_r = rf[idx] if idx < len(rf) else 1.0
                    rf = np.insert(rf, idx, (lo_r + hi_r) / 2.0)
                    added += 1
        if added == 0:
            break
    return ''.join(seq)


def call_well_v3(well, models, ref_rc, d):
    ch = parse_rsd(os.path.join(ex.PLATE, well + '.rsd'))[ex.CH_NAMES].values.astype(np.float64)
    esd = parse_esd(os.path.join(ex.GT, well + '.esd'))
    r, why = ex.extract_well(well, ch, esd, ref_rc)
    if r is None:
        return None, why
    n = r['n_usable']
    rank = np.arange(n, dtype=float) / max(1, n - 1)
    region = np.array([ex.region_of(x) for x in rank])
    X = np.array([ex.make_window(ch, int(s)) for s in r['scan']])
    mu = X.mean(1, keepdims=True)
    sd = X.std(1, keepdims=True) + 1e-8
    Xn = ((X - mu) / sd).astype(np.float32)
    called = np.empty(n, dtype='<U1')
    probs = np.zeros((n, 5))
    for rg in sorted(set(region)):
        sel = region == rg
        p = models[int(rg)].predict(Xn[sel], verbose=0)
        probs[sel] = p
        called[sel] = [LABELS[i] for i in p[:, :4].argmax(1)]
    read = ''.join(called)
    return (ch, r['scan'], read, rank), 'ok'


def main():
    d = np.load(os.path.join(ex.__file__.rsplit('/', 1)[0], 'v3_training.npz'),
                allow_pickle=True)
    wells = sorted({w for w, s in zip(d['well'], d['split']) if not s})
    models = {r: tf.keras.models.load_model(
        os.path.join(os.path.dirname(os.path.realpath(__file__)),
                     f'base_caller_model_v3_{tv.REGIONS[r]}.keras'),
        compile=False) for r in range(4)}
    ref_rc = ex.load_clean_ref()
    print(f'{len(wells)} wells')
    import statistics as st
    base, rf1, dll = [], [], []
    for well in wells:
        res, why = call_well_v3(well, models, ref_rc, d)
        if res is None:
            continue
        ch, scans, read, rank = res
        b = blast_eval(read)
        base.append(b['matched'] if b else 0)
        rr = refine_lite(models, ch, list(scans), list(read), list(rank),
                         drop_p=0.50, add_p=0.60, gap_frac=1.25)
        br = blast_eval(rr)
        rf1.append(br['matched'] if br else 0)
        dd = parse_esd(os.path.join(ex.GT, well + '.esd'))['sequence']
        bd = blast_eval(dd)
        dll.append(bd['matched'] if bd else 0)
    print(f'baseline v3 matched : {st.mean(base):.1f}  (n={len(base)})')
    print(f'refine-lite matched  : {st.mean(rf1):.1f}  delta {st.mean(rf1)-st.mean(base):+.1f}')
    print(f'DLL matched          : {st.mean(dll):.1f}')


if __name__ == '__main__':
    main()