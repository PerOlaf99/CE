#!/usr/bin/env python3
"""merge_plate.py - full 96-well run of the MERGE reads (DLL register + our
confidence), configs cfg1 and cfg3 from merge_probe, BLAST vs M13, saved to
merge_plate_rows.csv.  Answers 'show me for all 96 samples' with the merged
length+identity pipeline."""
import os, sys, csv, multiprocessing as mp
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import merge_probe as mpb

WELLS = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]
CFG_IDS = {0: 'cfg0', 1: 'cfg1', 3: 'cfg3'}


def _work(well):
    esd = os.path.join(mpb.GT_DIR, well + '.esd')
    if not (os.path.isfile(os.path.join(mpb.SEP, well + '.npy')) and os.path.isfile(esd)):
        return None
    import extract_training_data as etd
    d = etd.parse_esd(esd)
    dll = mpb.blast_seq(d['sequence'])
    row = dict(well=well, dll=dll)
    for i in [1, 3]:
        s = mpb.merge_read(well, mpb.CONFIGS[i])
        row[CFG_IDS[i]] = mpb.blast_seq(s)
    return row


def main():
    import numpy as np
    ctx = mp.get_context('spawn')
    out = os.path.join(mpb.HERE, 'merge_plate_rows.csv')
    rows = []
    with ctx.Pool(2, initializer=mpb._init) as pool:
        for row in pool.imap_unordered(_work, WELLS):
            if row is None:
                continue
            rows.append(row)
            w = row['well']

            def fm(r):
                return (f"{r['bases']}b/{r['matched']}m/{r['full_ident']:.1f}fi" if r else 'NO')
            print(f"{w:5s} cfg1[{fm(row['cfg1'])}] cfg3[{fm(row['cfg3'])}] "
                  f"DLL[{fm(row['dll'])}]", flush=True)
    with open(out, 'w', newline='') as f:
        w2 = csv.writer(f)
        w2.writerow(['well', 'dll_b', 'dll_matched', 'dll_fi',
                     'cfg1_b', 'cfg1_m', 'cfg1_fi',
                     'cfg3_b', 'cfg3_m', 'cfg3_fi'])
        for r in rows:
            def g(x, k):
                return (x[k] if x else '')
            w2.writerow([r['well'], g(r['dll'], 'bases'), g(r['dll'], 'matched'),
                         g(r['dll'], 'full_ident'),
                         g(r['cfg1'], 'bases'), g(r['cfg1'], 'matched'), g(r['cfg1'], 'full_ident'),
                         g(r['cfg3'], 'bases'), g(r['cfg3'], 'matched'), g(r['cfg3'], 'full_ident')])
    print(f"\n=== {len(rows)} wells: MERGE cfg1/cfg3 vs DLL ===", flush=True)

    def mkv(k, field):
        v = [r[k][field] for r in rows if r[k]]
        return np.mean(v) if v else float('nan')
    for key in ['dll', 'cfg1', 'cfg3']:
        print(f"  {key:5s}: bases={mkv(key, 'bases'):6.1f} matched_bp={mkv(key, 'matched'):6.1f} "
              f"cov={mkv(key, 'hsp_cov'):5.2f} id={mkv(key, 'pident'):5.2f} "
              f"fi={mkv(key, 'full_ident'):5.2f}", flush=True)


if __name__ == '__main__':
    main()