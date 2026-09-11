#!/usr/bin/env python3
"""Test current-driven frame hypothesis.

For each well: match de-novo detector candidates (cache_sep) to esd peaks,
measure offset = esd_pos - cand_pos per peak, group by position/current, and
compute correlation of local offset with current at that scan.  Supports block
level (res->scan mapping changes gradually with falling current)."""
import sys, os
import numpy as np
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
import dll_peakdet as dp
from extract_training_data import parse_esd, parse_rsd

SEP = os.path.join(ROOT, 'cache_sep')
GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
PLATE = os.path.join(ROOT, 'MB1000_M13_DT')


def main():
    d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
    wells = sorted(set(w.decode() if isinstance(w, bytes) else w for w in d['well']))
    all_d, all_cur, all_pos = [], [], []
    wells_d = []
    for well in wells:
        sep = np.load(os.path.join(SEP, well + '.npy'))
        pos, _, _ = dp.dll_peaks(sep, env_floor_frac=None, region_window=False)
        E = parse_esd(os.path.join(GT, well + '.esd'))
        pp = np.array([int(p) for p in E['peak_positions']])
        cur = parse_rsd(os.path.join(PLATE, well + '.rsd'))['Current'].values.astype(float)
        # match: for each esd peak find nearest candidate within 8
        resid = np.full(len(pp), np.nan)
        cand = pos
        cc = 0
        for i, p in enumerate(pp):
            im = np.argmin(np.abs(cand - p))
            if abs(cand[im] - p) <= 8:
                resid[i] = p - cand[im]  # esd - candidate
                cc += 1
        if cc < 50:
            continue
        wells_d.append((well, np.nanmedian(np.abs(resid)), np.nanmedian(resid)))
        m = ~np.isnan(resid)
        # current at each esd peak scan
        po = pp[m]
        res = resid[m]
        ci = cur[po]
        all_d.append(res); all_cur.append(ci); all_pos.append(po)
        r = np.corrcoef(res, ci)[0, 1]
        rr = np.corrcoef(res, po)[0, 1]
        print(f'{well}: match={cc}/{len(pp)} |esd-cand| med={np.nanmedian(np.abs(res)):.1f} '
              f'scans, resid vs current r={r:+.3f}, vs pos r={rr:+.3f}')

    D = np.concatenate(all_d); C = np.concatenate(all_cur); P = np.concatenate(all_pos)
    print(f'\nALL wells ({len(D)} matched peaks)')
    print(f'  resid |.| med = {np.median(np.abs(D)):.2f} scans, signed med = {np.median(D):+.2f}')
    print(f'  resid ~ current  r = {np.corrcoef(D, C)[0,1]:+.3f}')
    print(f'  resid ~ scans    r = {np.corrcoef(D, P)[0,1]:+.3f}')
    # resid in current-decile buckets
    order = np.argsort(C)
    Db, Cb = D[order], C[order]
    Nb = 10
    for b in range(Nb):
        sl = slice(b * len(Db) // Nb, (b + 1) * len(Db) // Nb)
        print(f'  cur [{Cb[sl].mean():5.1f}] resid med={np.median(Db[sl]):+6.2f} '
              f'|.|med={np.median(np.abs(Db[sl])):5.2f}')
    # resid in scan-decile buckets (time along run)
    order = np.argsort(P)
    Db, Pb = D[order], P[order]
    for b in range(Nb):
        sl = slice(b * len(Db) // Nb, (b + 1) * len(Db) // Nb)
        print(f'  scans[{Pb[sl].mean():5.0f}] resid med={np.median(Db[sl]):+6.2f} '
              f'|.|med={np.median(np.abs(Db[sl])):5.2f}')


if __name__ == '__main__':
    main()