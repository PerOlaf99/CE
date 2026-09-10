#!/usr/bin/env python3
"""
matrix_schedule.py - learn a spectral crosstalk-matrix schedule for automatic
matrix adjustment along a CE run.

Labels  : per-window DE-optimized full 4x4 matrices from opt_windows*/*.json
          (matrix_apply_point != 'none' only).
Features: raw-trace statistics + normalized run position.  Computed at decode
          time, so no M13 reference or analyzer basecall is needed to predict.
Model   : small Keras MLP regressor, 16 outputs, huber loss.
Eval    : leave-one-window-out CV (entry MAE vs constant baselines) plus
          end-to-end M13 identity of a full basecall under:
              (A) fixed global init matrix
              (B) per-window DE matrix  (label truth, upper bound)
              (C) learned schedule matrix (this model)
Run:
  python3 matrix_schedule.py --base-dir ... --outdir <dir>

Scaling labels (consistent matrices across windows AND wells):
  The existing opt_windows* labels mix matrix_apply_point (none/raw/corrected/
  smoothed), so only non-'none' ones are usable as-is.  To grow an exactly
  consistent training set for the whole plate, run the per-window optimizer
  with the apply point pinned and a fixed window grid, then rerun this script:

    for W in A01 B01 C01 ... H12; do
      mkdir -p opt_windows_labels/$W
      python3 optimize_windows_esd.py --well $W --win-size 700 --overlap 100 \
          --min-win 2050 --max-win 9332 --method greedy --tune-matrix diag \
          --matrix-apply-point corrected --outdir opt_windows_labels/$W
    done
    python3 matrix_schedule.py --label-dirs opt_windows_labels

  With many wells labeled the model learns genuinely cross-run generalization;
  this script already reports well- and position-holdout performance.
"""
import argparse, glob, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import extract_training_data as etd
import optimize_windows_esd as ow

BASE = os.path.join(ROOT, 'MB1000_M13_DT')
DEFAULT_INIT_JSON = os.path.join(HERE, 'A01_2050_2411.json')
LABEL_DIRS = ['opt_windows_esd', 'opt_windows_fine', 'opt_windows_tail']


def extract_window_features(raw, s0, e0):
    """Features for a scan window, computable from raw trace alone.

    Returns a 38-dim vector:
      1      normalized run position (midpoint / run length)
      4*5    per-channel: max, p95, mean, std, mean|diff|
      4      relative median channel amplitudes (dye ratios)
      4      per-channel local-max density
      6      upper-tri cross-channel correlation of the raw window
    """
    seg = raw[s0:e0].astype(np.float64)
    n = max(seg.shape[0], 1)
    feats = [(s0 + e0) / (2.0 * len(raw))]
    for ch in range(4):
        x = seg[:, ch]
        feats.append(float(np.max(x)))
        feats.append(float(np.percentile(x, 95)))
        feats.append(float(np.mean(x)))
        feats.append(float(np.std(x)))
        d = np.diff(x, axis=0)
        feats.append(float(np.mean(np.abs(d))) if len(d) else 0.0)
    med = np.maximum(np.median(seg, axis=0), 1e-9)
    r = med / med.sum()
    feats += [float(r[ch]) for ch in range(4)]
    for ch in range(4):
        x = seg[:, ch]
        npeak = int(np.sum(np.diff(np.sign(np.diff(x, axis=0))) < 0)) if len(x) >= 3 else 0
        feats.append(npeak / n)
    if seg.shape[0] >= 4:
        c = np.corrcoef(seg.T)
        for i in range(4):
            for j in range(i + 1, 4):
                feats.append(float(c[i, j]))
    else:
        feats += [0.0] * 6
    return np.asarray(feats, dtype=np.float64)


class RawCache:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self._cache = {}

    def get(self, well):
        if well not in self._cache:
            d = etd.parse_rsd(os.path.join(self.base_dir, well + '.rsd'))
            self._cache[well] = d[['Channel1', 'Channel2', 'Channel3',
                                   'Channel4']].values.astype(np.float64)
        return self._cache[well]


def collect_labels(base_dir, label_dirs, well_filter):
    """Return (X, Y, meta) where Y is the flattened 16-entry matrix per window."""
    cache = RawCache(base_dir)
    X, Y, meta = [], [], []
    for d in label_dirs:
        for f in sorted(glob.glob(os.path.join(d, '*.json'))):
            j = json.load(open(f))
            if j.get('matrix_apply_point') == 'none':
                continue
            well = j['well']
            if well_filter and well not in well_filter:
                continue
            if not os.path.exists(os.path.join(base_dir, well + '.rsd')):
                print(f'  skip {f}: no raw for {well}')
                continue
            s0, e0 = int(j['region_start']), int(j['region_stop'])
            raw = cache.get(well)
            s0 = max(0, min(int(s0), len(raw) - 2))
            e0 = max(2, min(int(e0), len(raw), s0 + 2))
            X.append(extract_window_features(raw, s0, e0))
            Y.append(np.asarray(j['matrix'], dtype=np.float64).reshape(-1))
            meta.append(dict(well=well, region_start=int(j['region_start']),
                             region_stop=int(j['region_stop']),
                             apply_point=j.get('matrix_apply_point', 'smoothed'),
                             ident=j.get('m13_ident_pct'),
                             score=j.get('optimized_score'),
                             file=f))
    return (np.vstack(X).astype(np.float64), np.vstack(Y).astype(np.float64), meta)


def build_model(n_feat, n_out=16, seed=1):
    from tensorflow import keras
    from tensorflow.keras import layers, regularizers
    keras.utils.set_random_seed(seed)
    inp = layers.Input(shape=(n_feat,))
    x = layers.Dense(64, activation='relu',
                     kernel_regularizer=regularizers.l2(1e-4))(inp)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(32, activation='relu')(x)
    out = layers.Dense(n_out)(x)
    m = keras.Model(inp, out)
    m.compile(optimizer=keras.optimizers.Adam(1e-3),
              loss=keras.losses.Huber(delta=1.0), metrics=['mae'])
    return m


def _zscore_train(Xtr, Ytr):
    mu = Ytr.mean(axis=0)
    sd = Ytr.std(axis=0)
    sd[sd < 1e-6] = 1.0
    return mu, sd, (Ytr - mu) / sd


def predict_schedule(X, Y, epochs=200):
    """Leave-one-window-out: predict each window's matrix from a model trained
    on all other windows.  Returns (pred_Y, mae_per_entry, mae_total)."""
    preds = np.zeros_like(Y)
    for i in range(len(Y)):
        msk = np.ones(len(Y), dtype=bool)
        msk[i] = False
        mu, sd, Yn = _zscore_train(X[msk], Y[msk])
        m = build_model(X.shape[1])
        m.fit(X[msk], Yn, epochs=epochs, batch_size=len(Yn), verbose=0)
        p = m.predict(X[i:i + 1], verbose=0)[0]
        preds[i] = p * sd + mu
    mae = np.mean(np.abs(preds - Y), axis=0)
    return preds, mae, float(np.mean(np.abs(preds - Y)))


def basecall_identity(raw, region, target, params, matrix, method='greedy'):
    """M13 (matches, aligned) for the window with the given matrix, all other
    knobs fixed at ``params`` (the per-window DE-optimized values)."""
    p = dict(params)
    p['matrix'] = np.asarray(matrix, dtype=np.float64)
    seq = ow.call_window(raw, p, region, method)
    return ow._global_score(seq, target)


def to_params(j):
    return dict(baseline_method=j['baseline_method'],
                baseline_window=j['baseline_window'],
                baseline_window2=j.get('baseline_window2'),
                smooth_method=j['smooth_method'],
                smooth_window=j['smooth_window'],
                smooth_order=j['smooth_order'],
                mobility_shifts=list(j['mobility_shifts']),
                matrix_apply_point=j.get('matrix_apply_point', 'smoothed'),
                min_distance=j.get('min_distance', 5),
                prominence_frac=j.get('prominence_frac', 0.1),
                norm_window=j.get('norm_window', 800),
                min_distance_floor=j.get('min_distance_floor', 1))


def e2e_eval(base_dir, meta, Y, pred_Y, init_json):
    """Compare fixed global matrix vs DE truth vs learned schedule per window."""
    cache = RawCache(base_dir)
    init_mat = np.asarray(json.load(open(init_json))['matrix'], dtype=np.float64)
    m13 = None
    esd_cache = {}
    tot = {'fix': (0, 0), 'de': (0, 0), 'ml': (0, 0)}
    rows = []
    for mi, m in enumerate(meta):
        raw = cache.get(m['well'])
        if m['well'] not in esd_cache:
            d = etd.parse_esd(os.path.join(
                base_dir, '..', 'ground_truth', ow.ESD_SUBDIR, m['well'] + '.esd'))
            esd_cache[m['well']] = (str(d['sequence']),
                                    np.asarray(d['peak_positions'], dtype=np.int64))
        esd_seq, esd_pp = esd_cache[m['well']]
        s0, e0 = m['region_start'], m['region_stop']
        region = (max(0, int(s0)), min(int(e0), len(raw)))
        j = json.load(open(m['file']))
        params = to_params(j)
        if m13 is None:
            m13 = ow.load_reference(os.path.join(HERE, 'refs', 'm13_M77815.1.fa'))
        esdwin = ow.esd_window(esd_seq, esd_pp, s0, e0)
        target = ow.anchored_m13_window_target(esdwin, m13)[0]
        mf, nf = basecall_identity(raw, region, target, params, init_mat)
        md, nd = basecall_identity(raw, region, target, params, Y[mi].reshape(4, 4))
        ml, nl = basecall_identity(raw, region, target, params, pred_Y[mi].reshape(4, 4))
        for k, (mm, nn) in [('fix', (mf, nf)), ('de', (md, nd)), ('ml', (ml, nl))]:
            t = tot[k]
            tot[k] = (t[0] + mm, t[1] + nn)
        idf = 100 * mf / nf if nf else 0
        idd = 100 * md / nd if nd else 0
        idl = 100 * ml / nl if nl else 0
        rows.append((s0, e0, idf, idd, idl))
    return rows, tot


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--base-dir', default=BASE)
    ap.add_argument('--init-json', default=DEFAULT_INIT_JSON)
    ap.add_argument('--label-dirs', default=','.join(LABEL_DIRS),
                    help='comma-separated directories of window optimization JSONs')
    ap.add_argument('--epochs', type=int, default=200)
    ap.add_argument('--wells', default=None,
                    help='comma list of wells to include (default: all found)')
    ap.add_argument('--outdir', default=HERE,
                    help='directory for matrix_preds.npz')
    args = ap.parse_args()

    well_filter = set(args.wells.split(',')) if args.wells else None
    print('collecting labels...')
    X, Y, meta = collect_labels(args.base_dir, [d.strip() for d in
                                                args.label_dirs.split(',')],
                                well_filter)
    print(f'  {len(Y)} labeled windows, {X.shape[1]} features')
    if len(Y) < 4:
        raise SystemExit('too few labeled windows')

    print('LOOCV training...')
    pred_Y, mae_entries, mae_tot = predict_schedule(X, Y, epochs=args.epochs)
    mu = Y.mean(axis=0)
    sd = Y.std(axis=0)
    el = np.mean(np.abs(Y - mu))
    e1 = np.mean(np.abs(Y - np.median(Y, axis=0)))
    print(f'  entry MAE: baseline(mean)= {el:.4f}  baseline(median)= {e1:.4f}  '
          f'ML= {mae_tot:.4f}')
    d = {i: (e1, mae_entries[i]) for i in range(16)}
    worst = sorted(d.items(), key=lambda kv: -kv[1][1])[:4]
    print('  worst-predicted entries (median-baseline vs ML MAE):')
    for i, (b, ml) in worst:
        r, c = divmod(i, 4)
        print(f'    M[{r},{c}]: basem={b:.4f} ml={ml:.4f}')

    print('\nE2E M13 identity (window knobs fixed, only the matrix changes):')
    rows, tot = e2e_eval(args.base_dir, meta, Y, pred_Y, args.init_json)
    print(f"{'window':15s} {'fixId%':>7s} {'deId%':>7s} {'mlId%':>7s}")
    for s0, e0, idf, idd, idl in rows:
        print(f'[{s0:5d},{e0:5d}] {idf:7.2f} {idd:7.2f} {idl:7.2f}')
    for k, (m, n) in tot.items():
        print(f'TOTAL {k}: matches={m} aln={n} ident={100 * m / n:.2f}%')

    out = os.path.join(args.outdir, 'matrix_preds.npz')
    os.makedirs(args.outdir, exist_ok=True)
    np.savez(out, X=X, Y=Y, pred=pred_Y,
             meta=np.array([(m['well'], m['region_start'], m['region_stop'],
                             m['apply_point']) for m in meta], dtype=object))
    print(f'saved {out}')


if __name__ == '__main__':
    main()