"""Per-channel multi-view peak detection and ESD-driven parameter tuning.

detect_multiview() generalizes pc_call_bases_with_shifts so every channel
gets its own (distance, prominence) pair, plus an optional combined-envelope
view with its own parameters whose discoveries fill positions all channels
missed (the existing fill-in idea, generalized).

The command-line interface optimizes those ten numbers against the Cimarron
ESD peak tables (F1 match within +-tolerance scans) by coordinate descent
over a plate sample, writing a JSON the GUI values can be typed from.
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.ndimage import maximum_filter1d
from scipy.signal import find_peaks

BASE_LETTERS = 'ACGT'
IUPAC_CODES = {
    frozenset('A'): 'A', frozenset('C'): 'C', frozenset('G'): 'G',
    frozenset('T'): 'T',
    frozenset('AG'): 'R', frozenset('CT'): 'Y', frozenset('CG'): 'S',
    frozenset('AT'): 'W', frozenset('GT'): 'K', frozenset('AC'): 'M',
    frozenset('CGT'): 'B', frozenset('AGT'): 'D', frozenset('ACT'): 'H',
    frozenset('ACG'): 'V', frozenset('ACGT'): 'N',
}


def _shift_channel(arr, shift):
    s = int(shift)
    out = np.zeros_like(arr)
    if s == 0:
        return arr.copy()
    if abs(s) >= len(arr):
        return out
    if s > 0:
        out[:-s] = arr[s:]
    else:
        out[-s:] = arr[:s]
    return out


def detect_multiview(separated, shifts=None,
                     ch_params=None, comb_params=None,
                     tolerance=4, norm_window=800,
                     min_signal_frac=0.25, min_height_ratio=2.0,
                     fill_gap=3, fill_margin_pct=20, region=None):
    """Basecall with independent per-channel peak parameters plus an
    optional combined-envelope view.

    ch_params    : list of 4 (distance, prom_x1000) pairs, one per channel
                   (A, C, G, T order).
    comb_params  : (distance, prom_x1000) for find_peaks on the max over
                   normalized shifted channels, or None to disable.
    fill_gap     : a combined-view peak must sit at least this many scans
                   from every per-channel call to be added as a base.
    fill_margin_pct : minimum dominance (%) of the winning channel at a
                   fill-in position (winner - runner-up) / winner.

    Returns (positions, sequence, base_groups, intensities) — same contract
    as pc_call_bases_with_shifts."""
    from scipy.signal import find_peaks as _fp

    sep = np.asarray(separated, dtype=np.float64)
    n = len(sep)
    if shifts is None:
        shifts = [0, 0, 0, 0]
    if ch_params is None:
        ch_params = [(6.0, 75)] * 4
    shifted_all = [_shift_channel(sep[:, ch], int(shifts[ch]))
                   for ch in range(4)]

    lead_n = max(int(n * 0.05), 1)
    ch_floor = [float(np.percentile(np.clip(shifted_all[ch][:lead_n], 0, None),
                                    90)) for ch in range(4)]

    norms = []
    for ch in range(4):
        rolled = maximum_filter1d(np.clip(shifted_all[ch], 0, None),
                                  size=max(3, int(norm_window)),
                                  mode='nearest')
        rolled = np.where(rolled > 0, rolled, 1.0)
        norms.append(shifted_all[ch] / rolled)

    start, stop = 0, n
    if region is not None and int(region[1]) > int(region[0]):
        start = max(0, int(region[0]))
        stop = min(n, int(region[1]))

    channels = []
    for ch in range(4):
        dist, prom_x = ch_params[ch]
        scale = np.percentile(np.clip(norms[ch], 0, None), 99.5)
        prom = max(scale * (prom_x / 1000.0), 1e-9) if scale > 0 else 1e-9
        peaks, _ = _fp(norms[ch], distance=max(1.0, float(dist)),
                       prominence=prom)
        floor_ch = ch_floor[ch] * max(float(min_height_ratio), 0.0)
        for p in peaks:
            if start <= p < stop and shifted_all[ch][p] >= floor_ch:
                channels.append((int(p), ch, float(shifted_all[ch][p])))

    channels.sort(key=lambda c: c[0])
    positions, base_groups, intensities = [], [], []
    i = 0
    while i < len(channels):
        j = i
        cluster = [channels[i]]
        cluster_start = channels[i][0]
        while j + 1 < len(channels) and \
                channels[j + 1][0] - cluster_start <= tolerance:
            j += 1
            cluster.append(channels[j])
        max_signal = max(c[2] for c in cluster)
        min_signal = max_signal * min_signal_frac
        valid = [c for c in cluster if c[2] >= min_signal]
        bases = frozenset(BASE_LETTERS[c[1]] for c in valid)
        best = max(valid, key=lambda c: c[2])
        positions.append(best[0])
        base_groups.append(bases)
        intensities.append({BASE_LETTERS[c]: h for _, c, h in valid})
        i = j + 1

    if comb_params is not None:
        env = np.max(np.stack([np.clip(x, 0, None) for x in norms]), axis=0)
        dist, prom_x = comb_params
        scale = np.percentile(env, 99.5)
        prom = max(scale * (prom_x / 1000.0), 1e-9) if scale > 0 else 1e-9
        peaks, _ = _fp(env, distance=max(1.0, float(dist)), prominence=prom)
        margin = float(fill_margin_pct) / 100.0
        gap = max(1, int(fill_gap))
        added = []
        for p in peaks:
            if not (start <= p < stop):
                continue
            if any(abs(p - q) < gap for q in positions):
                continue
            window = slice(max(0, p - 2), min(n, p + 3))
            vals = [shifted_all[c][window].max() for c in range(4)]
            order = np.argsort(vals)[::-1]
            win, run = vals[order[0]], vals[order[1]]
            if win <= 0 or (win - run) / win < margin:
                continue
            floor_ok = any(shifted_all[c][p] >=
                           ch_floor[c] * max(float(min_height_ratio), 0.0)
                           for c in range(4))
            if not floor_ok:
                continue
            added.append((int(p), int(order[0])))
        for p, ch in sorted(added):
            positions.append(p)
            base_groups.append(frozenset([BASE_LETTERS[ch]]))
            intensities.append({BASE_LETTERS[ch]: float(shifted_all[ch][p])})

    order = np.argsort(positions)
    positions = np.array(positions, dtype=np.int64)[order]
    base_groups = [base_groups[k] for k in order]
    intensities = [intensities[k] for k in order]
    sequence = ''.join(IUPAC_CODES.get(b, 'N') for b in base_groups)
    return positions, sequence, base_groups, intensities


def prf_vs_esd(det_positions, esd_positions, tol=3):
    """Precision/recall/F1 of detected peak positions against the ESD peak
    table, matching within +-tol scans (greedy nearest pairing)."""
    det = np.asarray(sorted(det_positions), dtype=np.int64)
    ref = np.asarray(sorted(esd_positions), dtype=np.int64)
    if len(det) == 0 or len(ref) == 0:
        return 0.0, 0.0, 0.0
    used_ref = np.zeros(len(ref), dtype=bool)
    hits = 0
    j0 = 0
    for d in det:
        while j0 < len(ref) and ref[j0] < d - tol:
            j0 += 1
        for j in range(j0, len(ref)):
            if ref[j] > d + tol:
                break
            if not used_ref[j]:
                used_ref[j] = True
                hits += 1
                break
    prec = hits / len(det)
    rec = hits / len(ref)
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    return prec, rec, f1


def load_well(plate_dir, well, esd_variant='Cp312'):
    """Return (separated, esd_positions) for one well using the V10 tuned
    DSP (AsyLS 50010, Butterworth 5/9, tuned SSM at 'smoothed', no shifts)."""
    from sequencing_gui_V15 import _TUNED_SSM, dsp_full_pipeline
    rsd_path = os.path.join(plate_dir, f'{well}.rsd')
    esd_path = os.path.join(plate_dir, f'{plate_dir.split("/")[-1]}_'
                            f'{esd_variant}_MD1', f'{well}.esd')
    if not (os.path.exists(rsd_path) and os.path.exists(esd_path)):
        return None, None
    import cimarrontv as cim
    data = cim.read_rsd(rsd_path)
    raw = np.asarray(data[0], dtype=np.float64)
    if raw.shape[0] == 4:
        raw = raw.T
    _, _, _, _, separated, _ = dsp_full_pipeline(
        raw, (0, 0, 0, 0),
        baseline_method='AsyLS', baseline_window=50010,
        smooth_method='Butterworth', smooth_window=5, smooth_order=9,
        matrix=_TUNED_SSM, matrix_apply_point='smoothed')
    from extract_training_data import parse_esd
    d = parse_esd(esd_path)
    esd_pos = d.get('peak_positions', d.get('base_positions'))
    if esd_pos is None:
        return separated, None
    return separated, np.asarray(sorted(esd_pos), dtype=np.int64)


DEFAULT_CH_PARAMS = [(6.0, 75)] * 4
DIST_GRID = list(range(2, 13))
PROM_GRID = list(range(20, 320, 20))


def eval_params(wells_data, ch_params, comb_params, tol_esd=3, **kw):
    precs, recs, f1s = [], [], []
    for sep, esd in wells_data:
        if sep is None or esd is None or len(esd) == 0:
            continue
        pos, _, _, _ = detect_multiview(sep, shifts=None,
                                        ch_params=list(ch_params),
                                        comb_params=comb_params, **kw)
        p, r, f = prf_vs_esd(pos, esd, tol=tol_esd)
        precs.append(p)
        recs.append(r)
        f1s.append(f)
    if not f1s:
        return 0.0, 0.0, 0.0
    return float(np.mean(precs)), float(np.mean(recs)), float(np.mean(f1s))


def optimize(wells_data, tol_esd=3, passes=2, verbose=True, **kw):
    ch = [list(p) for p in DEFAULT_CH_PARAMS]
    comb = None
    base_p, base_r, base_f = eval_params(wells_data, ch, None, tol_esd, **kw)
    if verbose:
        print(f'baseline (shared 6.0/75, no comb): P={base_p:.4f} '
              f'R={base_r:.4f} F1={base_f:.4f}')
    best_f = base_f
    for pas in range(passes):
        for ci in range(4):
            bd, bp, bf = ch[ci][0], ch[ci][1], best_f
            for d in DIST_GRID:
                for px in PROM_GRID:
                    trial = [list(x) for x in ch]
                    trial[ci] = [float(d), float(px)]
                    _, _, f = eval_params(wells_data, trial, comb, tol_esd, **kw)
                    if f > bf:
                        bf, bd, bp = f, float(d), float(px)
            ch[ci] = [bd, bp]
            best_f = bf
            if verbose:
                print(f'  pass{pas} ch{ci} ({BASE_LETTERS[ci]}): '
                      f'dist={bd} prom={bp} -> F1={bf:.4f}')
        if comb is None:
            cbd, cbp, cbf = 8.0, 120.0, best_f
            found = False
            for d in range(5, 15):
                for px in (60, 80, 100, 120, 150, 180, 220):
                    _, _, f = eval_params(wells_data, ch, [float(d), float(px)],
                                          tol_esd, **kw)
                    if f > cbf + 1e-6:
                        cbf, cbd, cbp, found = f, float(d), float(px), True
            if found:
                comb = [cbd, cbp]
                best_f = cbf
                if verbose:
                    print(f'  pass{pas} comb enabled: dist={cbd} '
                          f'prom={cbp} -> F1={cbf:.4f}')
            elif verbose:
                print(f'  pass{pas} comb: no improvement, left disabled')
        else:
            cbd, cbp = comb
            cbf = best_f
            for d in range(max(2, int(cbd) - 2), int(cbd) + 3):
                for px in range(max(20, int(cbp) - 40), int(cbp) + 41, 20):
                    _, _, f = eval_params(wells_data, ch, [float(d), float(px)],
                                          tol_esd, **kw)
                    if f > cbf:
                        cbf, cbd, cbp = f, float(d), float(px)
            comb = [float(cbd), float(cbp)]
            best_f = cbf
            if verbose:
                print(f'  pass{pas} comb refine: dist={cbd} prom={cbp} '
                      f'-> F1={cbf:.4f}')
    return ch, comb, (base_p, base_r, base_f), \
        eval_params(wells_data, ch, comb, tol_esd, **kw)


def main():
    ap = argparse.ArgumentParser(
        description='Optimize per-channel peak detection vs ESD peak tables.')
    ap.add_argument('--plate', default='MB1000_M13_DT')
    ap.add_argument('--wells', type=int, default=24,
                    help='number of wells sampled evenly across the plate')
    ap.add_argument('--esd-tol', type=int, default=3)
    ap.add_argument('--passes', type=int, default=2)
    ap.add_argument('--out', default='perchannel_params.json')
    args = ap.parse_args()

    plate_dir = args.plate if os.path.isdir(args.plate) else \
        os.path.join(os.path.dirname(os.path.abspath(__file__)), args.plate)

    letters = 'ABCDEFGH'
    rows = range(1, 13)
    all_wells = [f'{lt}{r:02d}' for lt in letters for r in rows]
    step = max(1, len(all_wells) // args.wells)
    picked = all_wells[::step][:args.wells]

    wells_data = []
    for w in picked:
        sep, esd = load_well(plate_dir, w)
        if sep is None or esd is None or len(esd) == 0:
            print(f'  skip {w}')
            continue
        wells_data.append((sep, esd))
        print(f'loaded {w}: {len(esd)} esd peaks')
    if not wells_data:
        sys.exit('no wells loaded')

    ch, comb, base, opt = optimize(wells_data, tol_esd=args.esd_tol,
                                   passes=args.passes)
    print('\n=== RESULT ===')
    print(f'baseline: P={base[0]:.4f} R={base[1]:.4f} F1={base[2]:.4f}')
    print(f'optimized: P={opt[0]:.4f} R={opt[1]:.4f} F1={opt[2]:.4f}')
    for i, (d, p) in enumerate(ch):
        print(f'  ch{BASE_LETTERS[i]}: distance={d:.2f} prom_x1000={p:.0f}')
    if comb:
        print(f'  COMB: distance={comb[0]:.2f} prom_x1000={comb[1]:.0f}')
    else:
        print('  COMB: disabled')
    with open(args.out, 'w') as fh:
        json.dump({'ch_params': ch, 'comb_params': comb,
                   'esd_tol': args.esd_tol,
                   'f1_baseline': base[2],
                   'precision': opt[0], 'recall': opt[1],
                   'f1_optimized': opt[2],
                   'wells': [w for w in picked]},
                  fh, indent=2)
    print(f'saved {args.out}')


if __name__ == '__main__':
    main()
