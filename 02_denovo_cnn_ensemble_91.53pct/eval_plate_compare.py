#!/usr/bin/env python3
"""eval_plate_compare.py - one plate pass; v1-refine vs v2-tail_tight per well."""
import os, sys, multiprocessing as mp
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

WELLS = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]
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
    eng = pb.build_engine()
    res = eng.call(ch, scans)
    pos = np.int64([int(round(p.time)) for p in res.peaks])
    chw = ch.T.astype(np.float64)
    probs = pb.cnn_probs(MODELS, chw, pos)
    pred = probs.argmax(1)
    seq0 = ''.join(pb.LABELS[i] for i in pred)
    conf0 = np.array([pb.phred(probs[k, i]) for k, i in enumerate(pred)], dtype=np.int32)
    s1, c1, p1 = refine_denovo(MODELS, chw, list(seq0), list(conf0), pos)
    s2, c2, p2 = refine_denovo_v2(
        MODELS, chw, list(seq0), list(conf0), pos,
        drop_p_hi=0.45, drop_p_lo=0.60, add_p=0.60)
    return (well,
            pb.perbase_vs_ref(esd_seq, ref),
            pb.perbase_vs_ref(''.join(s1), ref),
            pb.perbase_vs_ref(''.join(s2), ref),
            len(s1), len(s2))


def main():
    import numpy as np
    nproc = 2
    log = open(os.path.join(HERE, 'perfect_eval_compare.log'), 'a', buffering=1)
    log.write(f'\n=== compare run (nproc={nproc}) ===\n')
    ctx = mp.get_context('spawn')
    with ctx.Pool(nproc, initializer=_init) as pool:
        rows = []
        for row in pool.imap_unordered(_work, WELLS):
            if row is None:
                continue
            rows.append(row)
            dll = np.mean([r[1] for r in rows])
            v1 = np.mean([r[2] for r in rows])
            v2 = np.mean([r[3] for r in rows])
            log.write(f'{row[0]}  DLL={row[1]:.4f} v1={row[2]:.4f} '
                      f'v2tail={row[3]:.4f} n1={row[4]} n2={row[5]}\n')
            log.write(f'  [{len(rows)}] dll={dll:.4f} v1={v1:.4f} v2tail={v2:.4f}\n')
    arr = np.array([r[1:] for r in rows])
    log.write(f'FINAL ({len(rows)}): DLL={arr[:,0].mean():.4f} '
              f'v1refine={arr[:,1].mean():.4f} v2tailtight={arr[:,2].mean():.4f}\n')
    log.close()


if __name__ == '__main__':
    main()