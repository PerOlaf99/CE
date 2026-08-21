#!/usr/bin/env python3
"""eval_plate_parallel.py - run perfect_basecaller eval across all wells."""
__version__ = '1.1'  # 1.1: ROOT-aware paths after reorg
import os, sys, multiprocessing as mp

HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

WELLS = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]
MODELS = None


def _init():
    global MODELS
    for v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
              'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[v] = '1'
    import perfect_basecaller as pb
    MODELS = pb.load_ensemble([os.path.join(HERE, 'base_caller_model*.keras')])


def _work(well):
    try:
        import cimarrontv as cim
    except ImportError:
        import cimarrontv_shim as cim
    import perfect_basecaller as pb
    plate = os.path.join(ROOT, 'MB1000_M13_DT')
    gt = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
    rsd, esd = os.path.join(plate, well + '.rsd'), os.path.join(gt, well + '.esd')
    if not (os.path.isfile(rsd) and os.path.isfile(esd)):
        return None
    ref = pb.load_clean_ref()
    esd_seq = cim.read_esd(esd)['sequence']
    r = pb.call_raw(rsd, MODELS, refine=True)
    pol, nfix = pb.polish(r['seq'], r['conf'], ref)
    return (well, pb.nw_vs_esd(r['seq'], esd_seq),
            pb.perbase_vs_ref(esd_seq, ref),
            pb.perbase_vs_ref(r['seq'], ref),
            pb.perbase_vs_ref(pol, ref), len(r['seq']), len(pol), nfix)


def np_mean(rows):
    import numpy as np
    return np.array([[r[2], r[3], r[4]] for r in rows]).mean(axis=0)


def main():
    nproc = max(1, os.cpu_count() or 4)
    log = open(os.path.join(HERE, 'perfect_eval_full_plate.log'), 'a', buffering=1)
    log.write(f'\n=== parallel eval, {nproc} workers ===\n')
    ctx = mp.get_context('spawn')
    with ctx.Pool(nproc, initializer=_init) as pool:
        rows = []
        for row in pool.imap_unordered(_work, WELLS):
            if row is None:
                continue
            rows.append(row)
            log.write(
                f'{row[0]}  NWvsESD={row[1]:.3f}  DLLvsM13={row[2]:.4f}  '
                f'oursRaw={row[3]:.4f}  oursPolished={row[4]:.4f}  '
                f'n={row[5]}/{row[6]} edits={row[7]}\n')
            m = np_mean(rows)
            log.write(f'  [{len(rows)}/{len(WELLS)}] running mean: '
                      f'DLL={m[0]:.4f} raw={m[1]:.4f} polished={m[2]:.4f}\n')
    arr = np_mean(rows)
    log.write(f'FINAL ({len(rows)} wells): DLLvsM13={arr[0]:.4f} '
              f'oursRaw={arr[1]:.4f} oursPolished={arr[2]:.4f}\n')
    log.write(f'VERDICT margin: {arr[2] - arr[0]:+.2f} pts per-base vs M13\n')
    log.close()


if __name__ == '__main__':
    main()
