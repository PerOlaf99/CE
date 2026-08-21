#!/usr/bin/env python3
"""sweep_refine.py - tune refine_denovo params without re-running the DSP.

Loads each well once (DSP + ensemble probs at greedy peaks), then evaluates
a grid of (drop_p, add_p, gap_frac) combos against the M13 reference.
"""
import os, sys, itertools
import numpy as np

__version__ = '1.1'  # 1.1: optional model-path args; ROOT-aware paths
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

try:
    import cimarrontv as cim
except ImportError:
    import cimarrontv_shim as cim
import perfect_basecaller as pb

WELLS = ['A01', 'B02', 'C03', 'D04']
DROP = [0.65, 0.7, 0.75]
ADD = [0.56, 0.62, 0.68]
GAPF = [1.25, 1.3]
ITER = 3
JITTER = 2


def main():
    ref = pb.load_clean_ref()
    pats = sys.argv[1:] or [os.path.join(HERE, 'base_caller_model*.keras')]
    models = pb.load_ensemble(pats)
    cache = {}
    for w in WELLS:
        rsd = os.path.join(HERE, 'MB1000_M13_DT', w + '.rsd')
        ch, scans = cim.read_rsd(rsd)
        eng = pb.build_engine()
        res = eng.call(ch, scans)
        chw = np.asarray(ch, dtype=np.float64)
        if chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
            chw = chw.T
        seq0, conf0, ps0 = [], [], []
        for base, pk in zip(res.sequence, res.peaks):
            if base in pb.LABELS:
                seq0.append(base)
                ps0.append(int(round(pk.time)))
                conf0.append(30)
        base_probs = pb.cnn_probs(models, chw, ps0)
        print(f'{w}: {len(ps0)} peaks', flush=True)
        cache[w] = (chw, np.asarray(ps0), base_probs)

    def apply(w, drop_p, add_p, gapf):
        chw, sc_arr, probs = cache[w]
        pmax = probs.max(1)
        pred = probs.argmax(1)
        keep = pmax >= max(drop_p, 1e-9)
        seq = [pb.LABELS[i] for i, k in zip(pred, keep) if k]
        sc2 = sc_arr[keep]
        for _ in range(ITER):
            if len(sc2) < 3:
                break
            med = float(np.median(np.diff(sc2)))
            cands = []
            for a, b in zip(sc2[:-1], sc2[1:]):
                gap = b - a
                if gap < gapf * med:
                    continue
                need = max(0, int(round(gap / med)) - 1)
                for j in range(1, need + 1):
                    c0 = a + round(gap * j / (need + 1))
                    cands.extend(range(c0 - JITTER, c0 + JITTER + 1))
            added = 0
            if cands:
                cp = pb.cnn_probs(models, chw, sorted(set(cands)))
                cm = {s: (cp[k].max(), cp[k].argmax())
                      for k, s in enumerate(sorted(set(cands)))}
                for a, b in zip(sc2[:-1], sc2[1:]):
                    gap = b - a
                    if gap < gapf * med:
                        continue
                    need = max(0, int(round(gap / med)) - 1)
                    for j in range(1, need + 1):
                        c0 = int(a + round(gap * j / (need + 1)))
                        best_s, (best_p, best_b) = max(
                            ((s, cm[s]) for s in range(c0 - JITTER, c0 + JITTER + 1)
                             if s in cm), key=lambda t: t[1][0],
                            default=(None, (0.0, 0)))
                        if best_s is not None and best_p >= add_p:
                            idx = np.searchsorted(sc2, best_s)
                            seq.insert(idx, pb.LABELS[best_b])
                            sc2 = np.insert(sc2, idx, best_s)
                            added += 1
            if added == 0:
                break
        return ''.join(seq)

    results = {}
    for d, a, g in itertools.product(DROP, ADD, GAPF):
        accs = []
        for w in WELLS:
            s = apply(w, d, a, g)
            accs.append(pb.perbase_vs_ref(s, ref))
        m = float(np.mean(accs))
        results[(d, a, g)] = m
        print(f'drop={d:.2f} add={a:.2f} gapf={g:.2f} -> {m:.4f}', flush=True)

    best = max(results, key=results.get)
    print(f'\nBEST: drop={best[0]} add={best[1]} gapf={best[2]} '
          f'-> {results[best]:.4f}')
    base = np.mean([pb.perbase_vs_ref(
        ''.join(pb.LABELS[i] for i in cache[w][2].argmax(1)), ref)
        for w in WELLS])
    print(f'baseline (no refine): {base:.4f}')


if __name__ == '__main__':
    main()
