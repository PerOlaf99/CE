import sys
sys.path.insert(0, '/workspace')
import os, glob
import numpy as np
from megabace.rsd import RsdFile
from megabace.basecall import BaseCaller, _noise_level
from megabace import signal as sigmod
from megabace.spectral import deconvolve

ref = open('/tmp/opencode/rsd/m13mp18.fasta').read().split('\n', 1)[1].replace('\n', '').upper()
refRC = ref.translate(str.maketrans('ACGT', 'TGCA'))[::-1]
refc = refRC + refRC
GAP = -5

def sw(a, b):
    na, nb = len(a), len(b)
    H = np.zeros((na + 1, nb + 1), dtype=np.int32)
    ar = np.frombuffer(a.encode(), dtype=np.uint8)
    br = np.frombuffer(b.encode(), dtype=np.uint8)
    for i in range(1, na + 1):
        sc = np.where(ar[i - 1] == br, 2, -3)
        C = np.maximum(np.maximum(H[i - 1, 1:] + GAP, H[i - 1, :-1] + sc), 0)
        run = np.maximum.accumulate(np.concatenate(([0], C - GAP * np.arange(1, nb + 1))))
        H[i] = run + GAP * np.arange(nb + 1)
    flat = int(H.argmax()); i = flat // (nb + 1); j = flat % (nb + 1)
    if H[i, j] == 0:
        return None
    path = []
    while i > 0 and j > 0 and H[i, j] > 0:
        if H[i, j] == H[i - 1, j - 1] + (2 if a[i - 1] == b[j - 1] else -3):
            path.append((i - 1, j - 1, a[i - 1] == b[j - 1])); i -= 1; j -= 1
        elif H[i, j] == H[i - 1, j] + GAP:
            path.append((i - 1, None, False)); i -= 1
        elif H[i, j] == H[i, j - 1] + GAP:
            path.append((None, j - 1, False)); j -= 1
        else:
            break
    path.reverse()
    return path

def deletion_positions(path):
    dels = []
    i = 0
    while i < len(path):
        if path[i][0] is None and path[i][1] is not None:
            j = i
            while j + 1 < len(path) and path[j + 1][0] is None and path[j + 1][1] is not None:
                j += 1
            # map to read positions between flanking aligned calls
            lc = path[a - 1][0] if i > 0 else -1
            rc = path[b + 1][0] if j + 1 < len(path) else -1
            dels.append((lc, rc, refc[path[i][1]]))
            i = j + 1
        else:
            i += 1
    return dels

def run_experiment(lo_ratio, hi_ratio, height_frac, dom_thr, min_sep_frac):
    """For each well, for gaps in [lo_ratio, hi_ratio)*expected, find candidate peaks.
    Returns: recoverable deletions fixed, spurious insertions caused (by checking if
    inserting the base improves the SW identity)."""
    tot_fixed = 0; tot_spurious = 0; tot_cand = 0
    wells = sorted(glob.glob('/tmp/opencode/rsd/MB1000_M13_DT/*.rsd'))
    per_well = {}
    for w in wells:
        name = os.path.basename(w).replace('.rsd', '')
        rsd = RsdFile(w); tr = rsd.extract_traces()
        order = rsd.metadata.channel_order
        bc = BaseCaller(channel_order=order, trim=True)
        call = bc.call(tr)
        if call.bases.count('N') > len(call.bases) * 0.5:
            continue
        base = sigmod.subtract_baseline_multi(tr)
        sep = deconvolve(base, None, True)
        norm = sigmod.normalize_channels(sep)
        path = sw(call.bases, refc)
        if path is None:
            continue
        gaps = np.diff(call.positions.astype(float))
        med = float(np.median(gaps))
        k = 21
        exp = np.asarray([np.median(gaps[max(0, i - k):min(gaps.size, i + k + 1)]) for i in range(gaps.size)])
        exp = np.clip(exp, 0.5 * med, 2.0 * med)
        ratio = gaps / exp
        fixed = 0; spurious = 0; cands = 0
        # deletion gaps (by flanking aligned calls)
        delmap = {}
        i = 0
        while i < len(path):
            if path[i][0] is None and path[i][1] is not None:
                j = i
                while j + 1 < len(path) and path[j + 1][0] is None and path[j + 1][1] is not None:
                    j += 1
                lc = path[i - 1][0] if i > 0 else None
                rc = path[j + 1][0] if j + 1 < len(path) else None
                if lc is not None and rc is not None:
                    delmap[(int(call.positions[lc]), int(call.positions[rc]))] = True
                i = j + 1
            else:
                i += 1
        n_pts = norm.shape[1]
        for gi in range(gaps.size):
            r = ratio[gi]
            if not (lo_ratio <= r < hi_ratio):
                continue
            lo = int(call.positions[gi]); hi = int(call.positions[gi + 1])
            if hi - lo < 3:
                continue
            best = None
            for c in range(4):
                ch = sigmod.smooth(norm[c], window=3)
                noise = _noise_level(ch)
                seg = ch[lo + 1:hi]
                if seg.size < 1:
                    continue
                pk, props = sigmod.detect_peaks(seg, min_distance=1, min_prominence=max(0.0005, 1.0 * noise))
                if pk.size == 0:
                    continue
                for p0, prom in zip(pk, props['prominences']):
                    p = int(p0) + lo + 1
                    hl = ch[lo]; hr = ch[hi] if hi < n_pts else hl
                    h = ch[p]
                    if h < height_frac * max(hl, hr, 1e-6):
                        continue
                    # dominance radius 1
                    dom_c = norm[c, max(0, p - 1):p + 2].max()
                    dom_all = norm[:, max(0, p - 1):p + 2].max()
                    if dom_all <= 0 or dom_c < dom_thr * dom_all:
                        continue
                    # spacing check: both sides
                    gL = p - lo; gR = hi - p
                    e = exp[gi]
                    if gL < min_sep_frac * e or gR < min_sep_frac * e:
                        continue
                    cand = (p, c, float(h))
                    if best is None or cand[2] > best[2]:
                        best = cand
            if best is None:
                continue
            cands += 1
            # classify: is this gap a deletion gap AND candidate channel matches deleted base?
            is_del = (lo, hi) in delmap
            if is_del:
                fixed += 1
            else:
                spurious += 1
        tot_fixed += fixed; tot_spurious += spurious; tot_cand += cands
        per_well[name] = (fixed, spurious, cands)
    return tot_fixed, tot_spurious, tot_cand, per_well

if __name__ == '__main__':
    import itertools
    print('lo_ratio hi_ratio height_frac dom_thr min_sep_frac | fixed spurious cands')
    for (lo, hi, hf, dom, ms) in [
        (1.05, 1.8, 0.5, 0.9, 0.45),
        (1.05, 1.8, 0.6, 0.9, 0.45),
        (1.05, 1.8, 0.7, 0.9, 0.45),
        (1.05, 1.8, 0.5, 0.95, 0.45),
        (1.05, 1.8, 0.6, 0.95, 0.45),
        (1.05, 1.8, 0.5, 0.9, 0.5),
        (1.2, 1.8, 0.5, 0.9, 0.45),
        (1.2, 1.8, 0.6, 0.95, 0.45),
        (1.1, 1.8, 0.6, 0.95, 0.5),
        (1.0, 1.8, 0.6, 0.95, 0.5),
        (1.1, 1.9, 0.5, 0.9, 0.5),
    ]:
        f, s, c, _ = run_experiment(lo, hi, hf, dom, ms)
        print(f'{lo:5.2f} {hi:5.2f} {hf:11.1f} {dom:5.2f} {ms:11.2f} | {f:5d} {s:8d} {c:6d}')
