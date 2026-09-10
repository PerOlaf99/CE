#!/usr/bin/env python3
"""stutter_merge_test.py v2 - stutter-merge grid (fixed summary loop) plus
forensics on WHERE our residual insertion errors actually are.

Caches per-well de-novo(+refine) calls to calls_cache.npz so re-runs skip
the expensive CNN passes."""
import os
import sys

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import numpy as np
import perfect_basecaller as pb
from error_budget import WELLS, PLATE

CACHE = os.path.join(HERE, 'calls_cache.npz')
REF = pb.load_clean_ref()


def pmax_from_conf(conf):
    c = np.asarray(conf, dtype=np.float64)
    return 1.0 - np.power(10.0, -c / 10.0)


def stutter_merge(seq, scans, conf, gap_frac=0.55, p_t=0.60):
    seq = list(seq)
    scans = [int(s) for s in scans]
    conf = [int(c) for c in conf]
    med = float(np.median(np.diff(scans))) if len(scans) > 2 else 10.0
    out_s, out_p, out_c, dropped = [], [], [], 0
    k = 0
    while k < len(seq):
        if k + 1 < len(seq) and seq[k + 1] == seq[k] and \
                (scans[k + 1] - scans[k]) < gap_frac * med:
            a, b = k, k + 1
            strong, weak = (a, b) if conf[a] >= conf[b] else (b, a)
            if pmax_from_conf([conf[weak]])[0] < p_t:
                out_s.append(seq[strong])
                out_p.append(scans[strong])
                out_c.append(conf[strong])
                dropped += 1
                k += 2
                continue
        out_s.append(seq[k])
        out_p.append(scans[k])
        out_c.append(conf[k])
        k += 1
    return ''.join(out_s), out_p, out_c, dropped


def align_errors(query, ref):
    """Return (mm_idx, ins_idx, del_idx) as indices into the ALIGNED query /
    reference strings, plus the aligned pair lists."""
    al = pb.seed_sw_align(query, REF)
    q, r = al
    mm, ins, dele = [], [], []
    qi = 0
    for i, (a, b) in enumerate(zip(q, r)):
        if a != '-':
            if b == '-':
                ins.append((i, qi))
            elif a != b:
                mm.append((i, qi))
            qi += 1
        elif b != '-':
            dele.append(i)
    return mm, ins, dele, q, r


GRID = [(gf, pt) for gf in (0.45, 0.55, 0.65) for pt in (0.50, 0.60, 0.70)]


def load_or_call(models):
    if os.path.exists(CACHE):
        z = np.load(CACHE, allow_pickle=True)
        print(f'loaded cache {CACHE} ({len(z["wells"])} wells)', flush=True)
        return {str(w): (str(z['seq'][k]), z['scans'][k], z['conf'][k])
                for k, w in enumerate(z['wells'])}
    out = {}
    for w in WELLS:
        r = pb.call_raw(os.path.join(PLATE, f'{w}.rsd'),
                        models=models, refine=True)
        out[w] = (''.join(r['seq']),
                  np.asarray(r['scans'], dtype=np.int64),
                  np.asarray(r['conf'], dtype=np.int32))
        acc = 100.0 * sum(1 for a, b in zip(*pb.seed_sw_align(r['seq'], REF))
                          if a == b and a != '-') / max(1, len(r['seq']))
        print(f'{w}: called {len(r["seq"])} acc={acc:.2f}%', flush=True)
    np.savez(CACHE,
             wells=np.array(list(out.keys())),
             seq=np.array([v[0] for v in out.values()], dtype=object),
             scans=np.array([v[1] for v in out.values()], dtype=object),
             conf=np.array([v[2] for v in out.values()], dtype=object))
    print(f'saved cache {CACHE}', flush=True)
    return out


def main():
    models = None
    if not os.path.exists(CACHE):
        models = pb.load_ensemble([os.path.join(
            HERE, 'base_caller_model*.keras')])
    calls = load_or_call(models)

    base_accs = {}
    print('\n== stutter-merge grid (per-well mean over wells) ==', flush=True)
    agg = {v: dict(acc=[], drop=0, mm=0, ins=0, dele=0) for v in GRID}
    ins_stats = []
    for w, (seq, scans, conf) in calls.items():
        ro = None
        al = pb.seed_sw_align(seq, REF)
        q, r = al
        n = max(1, len(q))
        acc = 100.0 * sum(1 for a, b in zip(q, r)
                          if a == b and a != '-') / n
        base_accs[w] = acc
        mm_i, ins_i, del_i, _, _ = align_errors(seq, REF)
        for _, qi in ins_i:
            prev_gap = (np.diff(scans)[qi - 1] if 0 < qi < len(scans) else -1)
            quart = min(4, 4 * qi // max(1, len(seq) - 1) + 1)
            ins_stats.append((w, seq[qi], int(prev_gap), int(conf[qi]),
                              quart))
        for gf, pt in GRID:
            seq2, _, _, ndrop = stutter_merge(seq, scans, conf,
                                              gap_frac=gf, p_t=pt)
            al2 = pb.seed_sw_align(seq2, REF)
            q2, r2 = al2
            acc2 = 100.0 * sum(1 for a, b in zip(q2, r2)
                               if a == b and a != '-') / max(1, len(q2))
            a = agg[(gf, pt)]
            a['acc'].append(acc2)
            a['drop'] += ndrop
            a['mm'] += sum(1 for x, y in zip(q2, r2)
                           if x != '-' and y != '-' and x != y)
            a['ins'] += sum(1 for x in q2 if x == '-')
            a['dele'] += sum(1 for y in r2 if y == '-')
    nb = float(np.mean(list(base_accs.values())))
    print(f'baseline mean acc: {nb:.3f}%')
    rows = sorted(GRID, key=lambda v: -np.mean(agg[v]['acc']))
    for gf, pt in rows:
        a = agg[(gf, pt)]
        ma = float(np.mean(a['acc']))
        print(f'g={gf:.2f} p<{pt:.2f}: acc={ma:.3f}% '
              f'({ma - nb:+.3f})  drops={a["drop"]}  '
              f'tot_mm={a["mm"]} tot_ins={a["ins"]} tot_del={a["dele"]}',
              flush=True)

    print('\n== insertion forensics (baseline calls) ==', flush=True)
    if ins_stats:
        arr_g = np.array([s[2] for s in ins_stats])
        arr_c = np.array([s[3] for s in ins_stats])
        arr_q = np.array([s[4] for s in ins_stats])
        letters = {}
        for s in ins_stats:
            letters[s[1]] = letters.get(s[1], 0) + 1
        print(f'n_insertions={len(ins_stats)} over {len(calls)} wells')
        print('letter hist:', dict(sorted(letters.items())))
        print('quartile hist:',
              {q: int((arr_q == q).sum()) for q in range(1, 5)})
        print('gap-to-prev-peak: median', np.median(arr_g),
              'p25', np.percentile(arr_g, 25),
              'p75', np.percentile(arr_g, 75),
              'frac<0.45*11:', float((arr_g < 5).mean()))
        pm = pmax_from_conf(arr_c)
        print('ins pmax: median %.3f  frac>=0.7: %.3f'
              % (np.median(pm), float((pm >= 0.7).mean())))


if __name__ == '__main__':
    main()
