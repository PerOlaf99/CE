#!/usr/bin/env python3
"""Overnight plate-wide ML basecall for MB1000_M13_DT.

Applies the trained CNN basecaller (same patch/normalize/quality logic as the
GUI's _run_ml) to every well, evaluating each call against the ESD (Cp312)
call and the M13 amplicon reference.

Writes into ml_plate_results/:
    progress.log   - one append-only line per finished well (drives the
                     hourly cron health check)
    ml_plate_results.csv - per-well metrics, re-opened in append mode so the
                     run resumes where it stopped if interrupted
    ml_plate_report.txt - summary statistics once the run completes

Run:  nohup python3 ml_plate_run.py >/dev/null 2>&1 &
"""
import os
import sys
import time
import csv
import datetime

import numpy as np

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, 'MB1000_M13_DT')
ESD_SUBDIR = 'MB1000_M13_DT_Cp312_MD1'
OUT_DIR = os.path.join(ROOT, 'ml_plate_results')
WINDOW = 15
QUAL_N = 20

from extract_training_data import parse_rsd, parse_esd      # noqa: E402
from peak_calling import nw_identity                        # noqa: E402


def _m13_reference():
    try:
        from simple_align import M13_REFERENCE
        return M13_REFERENCE
    except Exception:
        from m13_reference import M13_REFERENCE
        return M13_REFERENCE


def _align_to_m13(query, ref):
    """Global Needleman-Wunsch identity vs the M13 amplicon reference
    (matches the GUI's _align_to_m13). Returns (identity%, matches, aligned)."""
    q = ''.join(c for c in query if c in 'ACGT')
    if len(q) < 20:
        return 0.0, 0, 0
    m, n = len(q), len(ref)
    a, b, g = 1, -1, -2
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    dp[:, 0] = np.arange(m + 1) * g
    dp[0, :] = np.arange(n + 1) * g
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            dp[i, j] = max(dp[i - 1, j - 1] + (a if q[i - 1] == ref[j - 1] else b),
                           dp[i - 1, j] + g, dp[i, j - 1] + g)
    i, j = m, n
    matches = aligned = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + (
                a if q[i - 1] == ref[j - 1] else b):
            aligned += 1
            matches += q[i - 1] == ref[j - 1]
            i -= 1
            j -= 1
        elif i > 0 and dp[i, j] == dp[i - 1, j] + g:
            aligned += 1
            i -= 1
        else:
            aligned += 1
            j -= 1
    return (100.0 * matches / aligned if aligned else 0.0), matches, aligned


def process_well(w, model, ref, ml_labels):
    df = parse_rsd(os.path.join(DATA_DIR, f'{w}.rsd'))
    raw = df[['Channel1', 'Channel2', 'Channel3',
              'Channel4']].values.astype(np.float32)
    esd = parse_esd(os.path.join(DATA_DIR, ESD_SUBDIR, f'{w}.esd'))
    positions = esd.get('peak_positions')
    seq = esd.get('sequence', '')
    if positions is None or not seq:
        raise ValueError('no ESD peaks/sequence')

    n_scans = len(raw)
    valid = np.where((positions >= WINDOW) & (positions < n_scans - WINDOW))[0]
    valid_positions = positions[valid]
    esd_valid = ''.join(seq[i] for i in valid if i < len(seq))
    if len(valid_positions) == 0:
        raise ValueError('no valid peak positions')

    X = np.array([raw[int(p) - WINDOW:int(p) + WINDOW + 1]
                  for p in valid_positions], dtype=np.float32)
    X_mean = X.mean(axis=(1,), keepdims=True)
    X_std = X.std(axis=(1,), keepdims=True) + 1e-8
    X = (X - X_mean) / X_std

    preds = model.predict(X, verbose=0)
    pred_classes = preds.argmax(axis=1)
    pred_probs = preds.max(axis=1)

    bases = []
    quals = []
    for cls, prob in zip(pred_classes, pred_probs):
        base = ml_labels[cls]
        qual = int(round(prob * 100))
        if qual < QUAL_N:
            base = 'N'
        bases.append(base)
        quals.append(qual)
    called = ''.join(bases)

    esd_identity = nw_identity(called, esd_valid, max_len=20000)
    q = ''.join(c for c in bases if c in 'ACGT')
    m13_pct, m13_matches, m13_aligned = _align_to_m13(q, ref)

    conf = [p for p, b in zip(pred_probs, bases) if b != 'N']
    avg_conf = float(np.mean(conf)) * 100 if conf else 0.0
    n_n = sum(1 for b in bases if b == 'N')
    return {
        'n_esd': int(len(valid_positions)),
        'n_called': int(len(bases)),
        'n_n': n_n,
        'n_acgt': int(len(q)),
        'vs_esd_pct': float(esd_identity),
        'vs_m13_pct': float(m13_pct),
        'm13_matches': int(m13_matches),
        'm13_aligned': int(m13_aligned),
        'avg_conf': float(avg_conf),
    }


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    from basecaller import _load_ml_model, ML_LABELS
    sys.stderr.write('loading model...\n')
    model = _load_ml_model()
    ref = _m13_reference()
    sys.stderr.write(f'model loaded, M13 ref {len(ref)} bp\n')

    wells = sorted(f[:-4] for f in os.listdir(DATA_DIR)
                   if f.endswith('.rsd'))
    done = set()
    csv_path = os.path.join(OUT_DIR, 'ml_plate_results.csv')
    if os.path.exists(csv_path):
        with open(csv_path, newline='') as fh:
            for row in csv.DictReader(fh):
                done.add(row['well'])

    columns = ['well', 'n_esd', 'n_called', 'n_n', 'n_acgt', 'vs_esd_pct',
               'vs_m13_pct', 'm13_matches', 'm13_aligned', 'avg_conf',
               'took_s']
    new_file = not os.path.exists(csv_path)
    fh_csv = open(csv_path, 'a', newline='')
    writer = csv.DictWriter(fh_csv, fieldnames=columns)
    if new_file:
        writer.writeheader()
        fh_csv.flush()

    progress = os.path.join(OUT_DIR, 'progress.log')
    results = []
    t_start = time.time()
    pending = [w for w in wells if w not in done]
    sys.stderr.write(f'{len(wells)} wells, {len(pending)} pending\n')
    for idx, w in enumerate(pending, start=len(done) + 1):
        t0 = time.time()
        try:
            res = process_well(w, model, ref, ML_LABELS)
        except Exception as e:
            line = (f'{_now()}  {w}  FAILED: {e}')
            print(line, flush=True)
            with open(progress, 'a') as p:
                p.write(line + '\n')
            continue
        took = time.time() - t0
        res.update({'well': w, 'took_s': round(took, 1)})
        writer.writerow(res)
        fh_csv.flush()
        results.append(res)
        line = (f'{_now()}  {w}  done={idx}/{len(wells)}  '
                f'vs_ESD={res["vs_esd_pct"]:.1f}  '
                f'vs_M13={res["vs_m13_pct"]:.1f}  '
                f'{res["n_called"]}bases  {took:.0f}s')
        print(line, flush=True)
        with open(progress, 'a') as p:
            p.write(line + '\n')

    fh_csv.close()
    total = time.time() - t_start

    report = os.path.join(OUT_DIR, 'ml_plate_report.txt')
    with open(report, 'w') as r:
        r.write(f'ML plate run ({datetime.date.today()})\n')
        r.write(f'wells attempted: {len(wells)}   finished: {len(results)}'
                f'   elapsed: {total/60:.1f} min\n\n')
        if results:
            es = np.array([x['vs_esd_pct'] for x in results])
            m13 = np.array([x['vs_m13_pct'] for x in results])
            r.write(f'vs ESD : mean {es.mean():.1f}  median '
                    f'{np.median(es):.1f}  min {es.min():.1f}  '
                    f'max {es.max():.1f}\n')
            r.write(f'vs M13 : mean {m13.mean():.1f}  median '
                    f'{np.median(m13):.1f}  min {m13.min():.1f}  '
                    f'max {m13.max():.1f}\n\n')
            r.write('worst 5 by vs M13:\n')
            for x in sorted(results, key=lambda x: x['vs_m13_pct'])[:5]:
                r.write(f"  {x['well']}: vs_M13 {x['vs_m13_pct']:.1f}  "
                        f"vs_ESD {x['vs_esd_pct']:.1f}\n")
            r.write('best 5 by vs M13:\n')
            for x in sorted(results, key=lambda x: -x['vs_m13_pct'])[:5]:
                r.write(f"  {x['well']}: vs_M13 {x['vs_m13_pct']:.1f}  "
                        f"vs_ESD {x['vs_esd_pct']:.1f}\n")
    sys.stderr.write(f'DONE. {len(results)} wells in {total/60:.1f} min. '
                     f'Report: {report}\n')


def _now():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


if __name__ == '__main__':
    main()