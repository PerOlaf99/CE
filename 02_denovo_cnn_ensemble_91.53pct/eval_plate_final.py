#!/usr/bin/env python3
"""eval_plate_final.py - full plate, per-well CSV: v1 vs aggressive tail configs."""
import os, sys, csv, multiprocessing as mp
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
os.environ['OMP_NUM_THREADS'] = '1'; os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'; os.environ['NUMEXPR_NUM_THREADS'] = '1'
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)

WELLS = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]
CONFIGS = [
    ('v1', 'v1'),
    ('tail055_070', {'drop_p_hi': 0.55, 'drop_p_lo': 0.70, 'add_p': 0.60}),
    ('tail070_085', {'drop_p_hi': 0.70, 'drop_p_lo': 0.85, 'add_p': 0.60}),
]
OUT_CSV = os.path.join(HERE, 'final_plate_rows.csv')
MODELS = None


def _init():
    global MODELS
    import perfect_basecaller as pb
    MODELS = pb.load_ensemble([os.path.join(HERE, 'base_caller_model*.keras')])


def _work(well):
    import numpy as np
    import perfect_basecaller as pb
    import cimarrontv as cim
    from perfect_basecaller import refine_denovo, refine_denovo_v2
    plate = os.path.join(ROOT, 'MB1000_M13_DT')
    gt = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
    rsd, esd = os.path.join(plate, well + '.rsd'), os.path.join(gt, well + '.esd')
    if not (os.path.isfile(rsd) and os.path.isfile(esd)):
        return None
    ref = pb.load_clean_ref()
    esd_seq = cim.read_esd(esd)['sequence']
    ch, scans = cim.read_rsd(rsd)
    eng = pb.build_engine(); res = eng.call(ch, scans)
    pos = np.int64([int(round(p.time)) for p in res.peaks])
    chw = ch.T.astype(np.float64)
    probs = pb.cnn_probs(MODELS, chw, pos)
    pred = probs.argmax(1)
    seq0 = ''.join(pb.LABELS[i] for i in pred)
    conf0 = np.array([pb.phred(probs[k, i]) for k, i in enumerate(pred)], dtype=np.int32)
    row = {'well': well, 'dll': pb.perbase_vs_ref(esd_seq, ref)}
    for name, kw in CONFIGS:
        if kw == 'v1':
            s, _, _ = refine_denovo(MODELS, chw, list(seq0), list(conf0), pos)
        else:
            s, _, _ = refine_denovo_v2(MODELS, chw, list(seq0), list(conf0), pos, **kw)
        row[name] = pb.perbase_vs_ref(''.join(s), ref)
        row[name + '_n'] = len(s)
    return row


def main():
    import numpy as np
    first = True
    ctx = mp.get_context('spawn')
    with ctx.Pool(2, initializer=_init) as pool:
        for row in pool.imap_unordered(_work, WELLS):
            if row is None:
                continue
            nom, f = os.path.split(OUT_CSV)
            with open(OUT_CSV, 'a', newline='') as fobj:
                w = csv.DictWriter(fobj, fieldnames=list(row.keys()))
                if first:
                    w.writeheader(); first = False
                w.writerow(row)
            t = list(csv.DictReader(open(OUT_CSV)))
            ns = len(t)
            means = {k: np.mean([float(r[k]) for r in t]) for k in ('dll',) + tuple(c[0] for c in CONFIGS)}
            print(f"{row['well']:5s} [{ns}/{len(WELLS)}] dll={means['dll']:.4f} " +
                  ' '.join(f"{c[0]}={means[c[0]]:.4f}" for c in CONFIGS), flush=True)
    t = list(csv.DictReader(open(OUT_CSV)))
    means = {k: np.mean([float(r[k]) for r in t]) for k in ('dll',) + tuple(c[0] for c in CONFIGS)}
    print(f"\nFINAL ({len(t)} wells): dll={means['dll']:.4f} " +
          ' '.join(f"{c[0]}={means[c[0]]:.4f}" for c in CONFIGS))
    with open(os.path.join(HERE, 'perfect_eval_final.log'), 'a') as f:
        f.write(f"\nFINAL ({len(t)}): dll={means['dll']:.4f}" +
                ''.join(f'  {c[0]}={means[c[0]]:.4f}' for c in CONFIGS) + '\n')


if __name__ == '__main__':
    main()