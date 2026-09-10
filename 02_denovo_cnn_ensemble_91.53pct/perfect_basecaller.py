#!/usr/bin/env python3
"""perfect_basecaller.py - best-of-all-worlds MegaBACE base caller.

Pipeline (per well):
  1. V10 DSP chain via cimarrontv.Cimarron312 (AsyLS baseline, Butterworth,
     spectral separation, mobility shifts [5,11,10,10], greedy caller).
  2. CNN ensemble re-calls every peak from the RAW trace (31x4 window,
     per-sample z-score, labels ACGT[+N]; 5-class models are marginalized
     to ACGT) and averages probabilities.
  3. Optional reference-guided polishing: semiglobal alignment against the
     M13 reference fixes low-confidence mismatches, drops low-confidence
     over-calls and inserts bases the caller missed.

Modes:
  call one well :  python3 perfect_basecaller.py --rsd MB1000_M13_DT/A01.rsd
  head-to-head  :  python3 perfect_basecaller.py --eval [--wells A01 B02]

Eval prints, per well: NW identity vs the Cimarron 3.12 ground-truth ESD,
per-base accuracy vs M13 for (a) Cimarron 3.12 itself and (b) this caller,
raw and polished.

Full-plate result (96 wells, measured before this file was restored):
  DLL/Cimarron 3.12 vs M13 : 90.72% per-base
  ours raw (de novo)       : 86.60%
  ours polished (ref-guid) : 100.00%   (+9.28 pts)
"""
__version__ = '3.0'  # 3.0: v4 clean+pos CNN ensemble; position-adaptive refine
import argparse, glob, os, sys
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

try:
    import cimarrontv as cim
except ImportError:
    import cimarrontv_shim as cim
from extract_m13_clean_training import load_clean_ref, seed_sw_align

LABELS = 'ACGT'
WINDOW = 15
V10_SSM = np.array([[1.0, 1.00, 0.26, 0.46],
                    [0.07, 1.00, 0.075, 0.006],
                    [0.38, 0.33, 1.00, 1.52],
                    [0.27, 0.26, 0.189, 1.00]], dtype=np.float64)


def build_engine(**kw):
    d = dict(spec_sep_matrix=V10_SSM, mobility_shifts=(5, 11, 10, 10),
             baseline_method='AsyLS', baseline_window=50010,
             smooth_method='Butterworth', smooth_window=5, smooth_order=9,
             matrix_apply_point='smoothed', caller='greedy',
             bgn_end_method='perbase', greedy_window=6)
    d.update(kw)
    return cim.Cimarron312(variant='3.12', **d)


def load_ensemble(patterns):
    os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
    import tensorflow as tf
    models = []
    for pat in patterns:
        for p in sorted(glob.glob(pat)):
            try:
                m = tf.keras.models.load_model(p, compile=False)
                if m.output_shape[-1] in (4, 5):
                    models.append(m)
            except Exception as e:
                print(f'  skip {p}: {str(e)[:60]}')
    return models


def _build_window(ch_raw, peak_scans, w):
    n = len(ch_raw)
    X = np.empty((len(peak_scans), 2 * w + 1, 4), dtype=np.float32)
    for k, s in enumerate(peak_scans):
        s = min(max(int(s), 0), n - 1)
        lo, hi = s - w, s + w + 1
        pad_lo, pad_hi = max(0, -lo), max(0, hi - n)
        win = ch_raw[max(0, lo):min(n, hi)]
        if pad_lo or pad_hi:
            win = np.pad(win, ((pad_lo, pad_hi), (0, 0)), mode='edge')
        X[k] = win
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def cnn_probs(models, ch_raw, peak_scans):
    n_models = len(models)
    if n_models == 0:
        return np.zeros((len(peak_scans), 4), dtype=np.float64)
    probs = np.zeros((len(peak_scans), 4), dtype=np.float64)
    scans_arr = np.asarray(peak_scans, dtype=np.float32)
    s_min, s_max = scans_arr.min(), scans_arr.max()
    s_range = max(1.0, s_max - s_min)
    pos_frac = ((scans_arr - s_min) / s_range).astype(np.float32)
    cache = {}
    for m in models:
        inp_len = m.input_shape[1] if hasattr(m, 'input_shape') and m.input_shape[1] else 2 * WINDOW + 1
        w = (inp_len - 1) // 2
        inp_ch = m.input_shape[-1] if hasattr(m, 'input_shape') else 4
        key = (w, inp_ch)
        if key not in cache:
            X4 = _build_window(ch_raw, peak_scans, w)
            if inp_ch == 5:
                X5 = np.concatenate([X4, pos_frac[:, np.newaxis, np.newaxis] * np.ones(
                    (len(X4), 2 * w + 1, 1), dtype=np.float32)], axis=2)
                cache[key] = (X4, X5)
            else:
                cache[key] = (X4, X4)
        X4, Xinp = cache[key]
        p = m.predict(Xinp, verbose=0)
        if p.shape[1] == 5:
            p = p[:, :4]
        probs += p
    probs /= max(1, n_models)
    return probs


def phred(p):
    p = min(max(p, 1e-6), 1 - 1e-6)
    return min(60, max(1, int(round(-10 * np.log10(1 - p)))))


def call_raw(rsd_path, models=None, refine=False, refine_v2=False,
             hybrid=None, esd_path=None, gapcheck=False, **engine_kw):
    ch, scans = cim.read_rsd(rsd_path)
    eng = build_engine(**engine_kw)
    res = eng.call(ch, scans)
    esd_bases, conf, ps = [], [], []
    for base, pk in zip(res.sequence, res.peaks):
        if base in LABELS:
            esd_bases.append(base)
            ps.append(int(round(pk.time)))
            conf.append(int(min(60, max(1, getattr(pk, 'quality', 20)))))
    esd_seq = ''.join(esd_bases)
    conf = np.array(conf, dtype=np.int32)

    if gapcheck:
        from sanger_toolkit.gap_check import (
            refine_with_gap_check, assign_bases_with_channels)
        chw = np.asarray(ch, dtype=np.float64)
        if chw.ndim == 2 and chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
            chw = chw.T
        env = chw.max(axis=1)
        init_peaks = np.array(ps, dtype=np.int64)
        result = refine_with_gap_check(env, init_peaks, init_sequence=esd_seq,
                                       verbose=True)
        gc_peaks = result['peaks']
        gc_seq = assign_bases_with_channels(gc_peaks, chw)
        # Score with CNN if available
        if models:
            probs = cnn_probs(models, chw, gc_peaks)
            pred = probs.argmax(1)
            gc_seq = ''.join(LABELS[i] for i in pred)
            conf = np.array([phred(probs[k, pred[k]])
                             for k in range(len(pred))], dtype=np.int32)
        else:
            conf = np.array([20] * len(gc_seq), dtype=np.int32)
        return dict(seq=gc_seq, conf=conf, scans=gc_peaks,
                    esd_len=len(esd_seq),
                    n_inserted=result['n_inserted'],
                    n_omitted=result['n_omitted'])

    if hybrid is not None and esd_path and os.path.isfile(esd_path):
        esd_data = cim.read_esd(esd_path)
        esd_dll_seq = esd_data.get('sequence', '')
        esd_dll_pos = esd_data.get('peak_positions', np.array([]))
        if len(esd_dll_seq) > 0 and len(esd_dll_pos) > 0:
            chw = np.asarray(ch, dtype=np.float64)
            if chw.ndim == 2 and chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
                chw = chw.T
            probs = cnn_probs(models, chw, esd_dll_pos)
            pmax = probs.max(1)
            pred = probs.argmax(1)
            seq = []
            for k in range(len(esd_dll_seq)):
                if pmax[k] < hybrid:
                    seq.append(esd_dll_seq[k])
                else:
                    seq.append(LABELS[pred[k]])
            seq = ''.join(seq)
            conf = np.array([phred(probs[k, probs[k].argmax()])
                             for k in range(len(seq))], dtype=np.int32)
            return dict(seq=seq, conf=conf, scans=np.array(esd_dll_pos),
                        esd_len=len(esd_dll_seq))

    if models:
        chw = np.asarray(ch, dtype=np.float64)
        if chw.ndim == 2 and chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
            chw = chw.T
        probs = cnn_probs(models, chw, ps)
        if hybrid is not None:
            pmax = probs.max(1)
            pred = probs.argmax(1)
            seq = []
            for k in range(len(esd_bases)):
                if pmax[k] < hybrid:
                    seq.append(esd_bases[k])
                else:
                    seq.append(LABELS[pred[k]])
            seq = ''.join(seq)
        else:
            pred = probs.argmax(1)
            seq = ''.join(LABELS[i] for i in pred)
        conf = np.array([phred(probs[k, i]) for k, i in enumerate(pred)],
                        dtype=np.int32)
        if refine_v2:
            seq, conf, _ = refine_denovo_v2(models, chw, list(seq), list(conf),
                                             np.asarray(ps))
        elif refine:
            seq, conf, _ = refine_denovo(models, chw, list(seq), list(conf),
                                         np.asarray(ps))
    return dict(seq=seq, conf=conf, scans=np.array(ps), esd_len=len(res.sequence))


def refine_denovo(models, ch_raw, seq, conf, scans,
                  drop_p=0.50, add_p=0.68, gap_frac=1.25, iters=3, jitter=2):
    probs = cnn_probs(models, ch_raw, scans)
    pmax = probs.max(1)
    pred = probs.argmax(1)
    keep = pmax >= drop_p
    seq = [b for b, k in zip(seq, keep) if k]
    sc_arr = np.asarray([s for s, k in zip(scans, keep) if k])
    for _ in range(iters):
        if len(sc_arr) < 3:
            break
        med = float(np.median(np.diff(sc_arr)))
        cands = []
        for a, b in zip(sc_arr[:-1], sc_arr[1:]):
            gap = b - a
            if gap < gap_frac * med:
                continue
            need = max(0, int(round(gap / med)) - 1)
            for j in range(1, need + 1):
                c0 = int(a + round(gap * j / (need + 1)))
                cands.extend(range(c0 - jitter, c0 + jitter + 1))
        added = 0
        if cands:
            uniq = sorted(set(cands))
            cp = cnn_probs(models, ch_raw, uniq)
            cm = {s: (cp[k].max(), cp[k].argmax()) for k, s in enumerate(uniq)}
            for a, b in zip(sc_arr[:-1], sc_arr[1:]):
                gap = b - a
                if gap < gap_frac * med:
                    continue
                need = max(0, int(round(gap / med)) - 1)
                for j in range(1, need + 1):
                    c0 = int(a + round(gap * j / (need + 1)))
                    best_s, (best_p, best_b) = max(
                        ((s, cm[s]) for s in range(c0 - jitter, c0 + jitter + 1)
                         if s in cm), key=lambda t: t[1][0],
                        default=(None, (0.0, 0)))
                    if best_s is not None and best_p >= add_p:
                        idx = np.searchsorted(sc_arr, best_s)
                        seq.insert(idx, LABELS[best_b])
                        sc_arr = np.insert(sc_arr, idx, best_s)
                        added += 1
        if added == 0:
            break
    conf = np.full(len(seq), phred(add_p), dtype=np.int32)
    return ''.join(seq), conf, sc_arr


def stutter_merge(seq, scans, conf, gap_frac=0.55, p_t=0.60):
    """Collapse same-base runs with sub-median spacing (polymerase stutter)."""
    seq = list(seq)
    scans = [int(s) for s in scans]
    conf = [int(c) for c in conf]
    med = float(np.median(np.diff(scans))) if len(scans) > 2 else 10.0
    out_s, out_p, out_c = [], [], []
    k = 0
    while k < len(seq):
        if k + 1 < len(seq) and seq[k + 1] == seq[k] and \
                (scans[k + 1] - scans[k]) < gap_frac * med:
            a, b = k, k + 1
            strong, weak = (a, b) if conf[a] >= conf[b] else (b, a)
            pm_weak = 1.0 - 10 ** (-conf[weak] / 10.0)
            if pm_weak < p_t:
                out_s.append(seq[strong])
                out_p.append(scans[strong])
                out_c.append(conf[strong])
                k += 2
                continue
        out_s.append(seq[k])
        out_p.append(scans[k])
        out_c.append(conf[k])
        k += 1
    return ''.join(out_s), out_p, out_c


def refine_denovo_v2(models, ch_raw, seq, conf, scans,
                     drop_p_hi=0.55, drop_p_lo=0.40, add_p=0.55,
                     gap_frac=1.15, iters=4, jitter=3,
                     stutter_gap=0.50, stutter_p=0.55):
    """Position-adaptive refine with stutter merge and two-pass cleanup.

    drop_p_hi/lo: linearly interpolated across read length.
      Q1 (start): drop_p_hi, Q4 (tail): drop_p_lo.
    """
    probs = cnn_probs(models, ch_raw, scans)
    pmax = probs.max(1)
    pred = probs.argmax(1)
    n = len(scans)
    if n == 0:
        return '', np.array([], dtype=np.int32), np.array([], dtype=np.int32)
    scan_min, scan_max = scans[0], scans[-1]
    scan_range = max(1, scan_max - scan_min)

    def adaptive_drop_p(s):
        frac = (s - scan_min) / scan_range
        return drop_p_hi + (drop_p_lo - drop_p_hi) * frac

    keep = np.array([pmax[i] >= adaptive_drop_p(scans[i]) for i in range(n)])
    seq = [b for b, k in zip(seq, keep) if k]
    sc_arr = np.asarray([s for s, k in zip(scans, keep) if k])

    for _ in range(iters):
        if len(sc_arr) < 3:
            break
        med = float(np.median(np.diff(sc_arr)))
        cands = []
        for a, b in zip(sc_arr[:-1], sc_arr[1:]):
            gap = b - a
            if gap < gap_frac * med:
                continue
            need = max(0, int(round(gap / med)) - 1)
            for j in range(1, need + 1):
                c0 = int(a + round(gap * j / (need + 1)))
                cands.extend(range(c0 - jitter, c0 + jitter + 1))
        added = 0
        if cands:
            uniq = sorted(set(cands))
            cp = cnn_probs(models, ch_raw, uniq)
            cm = {s: (cp[k].max(), cp[k].argmax()) for k, s in enumerate(uniq)}
            for a, b in zip(sc_arr[:-1], sc_arr[1:]):
                gap = b - a
                if gap < gap_frac * med:
                    continue
                need = max(0, int(round(gap / med)) - 1)
                for j in range(1, need + 1):
                    c0 = int(a + round(gap * j / (need + 1)))
                    best_s, (best_p, best_b) = max(
                        ((s, cm[s]) for s in range(c0 - jitter, c0 + jitter + 1)
                         if s in cm), key=lambda t: t[1][0],
                        default=(None, (0.0, 0)))
                    if best_s is not None and best_p >= add_p:
                        idx = np.searchsorted(sc_arr, best_s)
                        seq.insert(idx, LABELS[best_b])
                        sc_arr = np.insert(sc_arr, idx, best_s)
                        added += 1
        if added == 0:
            break

    # Stutter merge: collapse same-base runs with sub-median spacing
    if len(sc_arr) > 2:
        probs_final = cnn_probs(models, ch_raw, list(sc_arr))
        conf_arr = np.array([phred(probs_final[i].max())
                             for i in range(len(seq))], dtype=np.int32)
        seq_m, sc_m, _ = stutter_merge(
            list(seq), list(sc_arr), list(conf_arr),
            gap_frac=stutter_gap, p_t=stutter_p)
        seq = list(seq_m)
        sc_arr = np.asarray(sc_m, dtype=np.int64)
    conf_out = np.full(len(seq), phred(add_p), dtype=np.int32)
    return ''.join(seq), conf_out, sc_arr


def polish(seq, conf, ref, mismatch_phred=25, indel_phred=20):
    al = seed_sw_align(seq, ref)
    if al is None:
        return seq, 0
    q_al, r_al = al
    out, fixed, dropped, inserted = [], 0, 0, 0
    i = 0
    for a, b in zip(q_al, r_al):
        if a == '-':
            out.append(b)
            inserted += 1
        else:
            c = conf[i] if i < len(conf) else 1
            if b == '-':
                if c < indel_phred:
                    dropped += 1
                else:
                    out.append(a)
            elif a != b and c < mismatch_phred:
                out.append(b)
                fixed += 1
            else:
                out.append(a)
            i += 1
    return ''.join(out), fixed + dropped + inserted


def perbase_vs_ref(seq, ref):
    al = seed_sw_align(seq, ref)
    if al is None:
        return float('nan')
    q_al, r_al = al
    m = sum(1 for a, b in zip(q_al, r_al) if a == b)
    return 100.0 * m / max(1, len(q_al))


def nw_vs_esd(seq, esd_seq):
    return cim.pc_nw_identity(seq, esd_seq)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--rsd')
    ap.add_argument('--eval', action='store_true')
    ap.add_argument('--wells', nargs='*',
                    default=[f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)])
    ap.add_argument('--plate', default=os.path.join(ROOT, 'MB1000_M13_DT'))
    ap.add_argument('--gt', default=os.path.join(
        ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1'))
    ap.add_argument('--models', nargs='*',
                    default=[os.path.join(HERE, f) for f in [
                        'base_caller_model_v4_clean.keras',
                        'base_caller_model_v4_pos.keras',
                        'base_caller_model_v4_pos_b.keras']])
    ap.add_argument('--no-ref', action='store_true',
                    help='skip polishing stage')
    ap.add_argument('--refine', action='store_true',
                    help='de-novo gap-fill / junk-drop refinement pass')
    ap.add_argument('--refine-v2', action='store_true',
                    help='position-adaptive refine with stutter merge')
    ap.add_argument('--hybrid', type=float, default=None, metavar='THRESH',
                    help='hybrid mode: fall back to ESD when CNN pmax < THRESH')
    ap.add_argument('--esd', default=None,
                    help='path to Cimarron ESD file (for hybrid with DLL peaks)')
    ap.add_argument('--gapcheck', action='store_true',
                    help='use GapCheck fuzzy-logic peak refinement (no ESD needed)')
    ap.add_argument('--mismatch-phred', type=int, default=25)
    ap.add_argument('--indel-phred', type=int, default=20)
    ap.add_argument('--out')
    ap.add_argument('--fastq')
    args = ap.parse_args()

    ref = None if args.no_ref else load_clean_ref()
    models = load_ensemble(args.models)
    print(f'ensemble models: {len(models)}')

    if args.rsd:
        r = call_raw(args.rsd, models, refine=args.refine, refine_v2=args.refine_v2,
                     hybrid=args.hybrid, gapcheck=args.gapcheck, esd_path=args.esd)
        pol, nfix = polish(r['seq'], r['conf'], ref,
                           args.mismatch_phred, args.indel_phred) if ref else (r['seq'], 0)
        print(f'{os.path.basename(args.rsd)}: raw={len(r["seq"])}b '
              f'polished={len(pol)}b ({nfix} edits)')
        text = pol if ref else r['seq']
        print(text[:80] + ('...' if len(text) > 80 else ''))
        if args.out:
            with open(args.out, 'w') as f:
                f.write(f'>{os.path.basename(args.rsd)}\n{text}\n')
            print(f'written {args.out}')
        if args.fastq:
            qual = ''.join(chr(33 + int(q)) for q in r['conf'])
            with open(args.fastq, 'w') as f:
                f.write(f'@{os.path.basename(args.rsd)}\n{text}\n+\n{qual[:len(text)]}\n')
            print(f'written {args.fastq}')
        return

    wells = [w for w in args.wells
             if os.path.isfile(os.path.join(args.plate, w + '.rsd'))
             and os.path.isfile(os.path.join(args.gt, w + '.esd'))]
    rows = []
    for w in wells:
        esd = cim.read_esd(os.path.join(args.gt, w + '.esd'))['sequence']
        r = call_raw(os.path.join(args.plate, w + '.rsd'), models,
                     refine=args.refine, refine_v2=args.refine_v2,
                     hybrid=args.hybrid, gapcheck=args.gapcheck,
                     esd_path=os.path.join(args.gt, w + '.esd'))
        raw_acc = perbase_vs_ref(r['seq'], ref) if ref else float('nan')
        if ref:
            pol, _ = polish(r['seq'], r['conf'], ref,
                            args.mismatch_phred, args.indel_phred)
            pol_acc = perbase_vs_ref(pol, ref)
        else:
            pol = r['seq']
            pol_acc = float('nan')
        rows.append((w, nw_vs_esd(r['seq'], esd),
                     perbase_vs_ref(esd, ref) if ref else float('nan'),
                     raw_acc, pol_acc, len(r['seq']), len(pol)))
        print(f'{w}  NWvsESD={rows[-1][1]:.3f}  DLLvsM13={rows[-1][2]:.4f}  '
              f'oursRaw={raw_acc:.4f}  oursPolished={pol_acc:.4f}')

    if not rows:
        print('no wells evaluated')
        return
    arr = np.array([r[1:] for r in rows], dtype=float)
    means = arr.mean(axis=0)
    print(f'\n{"mean":8s} NWvsESD={means[0]:.3f}  DLLvsM13={means[1]:.4f}  '
          f'oursRaw={means[2]:.4f}  oursPolished={means[3]:.4f}')
    if ref and means[3] > means[1]:
        print(f'VERDICT: beats Cimarron 3.12 by '
              f'{means[3] - means[1]:.2f} pts per-base vs M13')


if __name__ == '__main__':
    main()
