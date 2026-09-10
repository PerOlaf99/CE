import sys, warnings
import numpy as np
warnings.filterwarnings('ignore')
sys.path.insert(0, '/workspace')
from megabace.rsd import RsdFile
from megabace import signal as sigmod, utah
from megabace.spectral import deconvolve

NPTS, INPUTSTEP, MAXPASSES, MAXFBW = 2048, 1900, 6, 100
ref = open('/tmp/opencode/rsd/m13mp18.fasta').read().split('\n', 1)[1].replace('\n', '').upper()
refRC = ref.translate(str.maketrans('ACGT', 'TGCA'))[::-1]
refc = refRC + refRC
GAP = -5
import numpy as _np
def sw(a, b):
    na, nb = len(a), len(b)
    H = _np.zeros((na + 1, nb + 1), dtype=_np.int32)
    ar = _np.frombuffer(a.encode(), dtype=_np.uint8)
    br = _np.frombuffer(b.encode(), dtype=_np.uint8)
    for i in range(1, na + 1):
        sc = _np.where(ar[i - 1] == br, 2, -3)
        C = _np.maximum(_np.maximum(H[i - 1, 1:] + GAP, H[i - 1, :-1] + sc), 0)
        run = _np.maximum.accumulate(_np.concatenate(([0], C - GAP * _np.arange(1, nb + 1))))
        H[i] = run + GAP * _np.arange(nb + 1)
    flat = int(H.argmax()); i = flat // (nb + 1); j = flat % (nb + 1)
    if H[i, j] == 0: return None
    path = []
    while i > 0 and j > 0 and H[i, j] > 0:
        if H[i, j] == H[i - 1, j - 1] + (2 if a[i - 1] == b[j - 1] else -3):
            path.append((i - 1, j - 1, a[i - 1] == b[j - 1])); i -= 1; j -= 1
        elif H[i, j] == H[i - 1, j] + GAP: path.append((i - 1, None, False)); i -= 1
        elif H[i, j] == H[i, j - 1] + GAP: path.append((None, j - 1, False)); j -= 1
        else: break
    path.reverse(); return path

def run(well, src_label):
    rsd = RsdFile(f'/tmp/opencode/rsd/MB1000_M13_DT/{well}.rsd')
    tr = rsd.extract_traces()
    base = sigmod.subtract_baseline_multi(tr)
    if src_label == 'sep':
        src = sigmod.normalize_channels(deconvolve(base, None, True))
    else:
        src = base
    mb = utah.MB(fluor=True)
    n = src.shape[1]
    letters = 'TGCA'
    # two full passes to mimic nfeeder spacing adaptation per window
    passes = 1 if n < NPTS else min(int(_np.ceil((n - NPTS) / INPUTSTEP)) + 1, MAXPASSES)
    fbw = 82
    prev_sp = None
    finals = []
    meta = []
    iSl = 0
    for p in range(1, passes + 1):
        w = src[:, iSl:iSl + NPTS]
        if w.shape[1] < NPTS:
            ww = _np.zeros((4, NPTS)); ww[:, :w.shape[1]] = w; w = ww
        r = utah.nrefine_window(utah.blindeconv_matrix(w.T, mb, fbw).T, fbw, mb, letters)
        if r is None or len(r['mid']) < 2:
            break
        sp = utah.fband_space([iSl + m - 1 for m in r['mid']])
        if sp is None:
            break
        if prev_sp is not None and sp < prev_sp:
            sp = prev_sp
        prev_sp = sp
        fbw = utah.fbwlut(sp, mb)
        r = utah.nrefine_window(utah.blindeconv_matrix(w.T, mb, fbw).T, fbw, mb, letters)
        if r is None:
            break
        finals.append((iSl, r))
        meta.append((p, sp, fbw, len(r['mid']), iSl))
        newStart = iSl + INPUTSTEP
        if newStart + NPTS >= n:
            newStart = n - NPTS
            if newStart <= iSl:
                break
        iSl = newStart
    mids, codes, ins = [], [], []
    for iSl, r in finals:
        for m, c in zip(r['mid'], r['code']):
            mids.append(iSl + m - 1)
            codes.append(c)
    order = _np.argsort(mids)
    mids = [mids[i] for i in order]; codes = [codes[i] for i in order]
    # collapse duplicates from overlapping windows (keep first)
    uniq_m = []; uniq_c = []
    for m, c in zip(mids, codes):
        if uniq_m and abs(m - uniq_m[-1]) < 3:
            continue
        uniq_m.append(m); uniq_c.append(c)
    seq = ''.join(letters[c - 1] if c in (1, 2, 3, 4) else 'N' for c in uniq_c)
    path = sw(seq, refc)
    print(well, src_label, 'meta', [(a, b, c, d) for a, b, c, d, _e in meta])
    print('  bands', len(seq), 'N', seq.count('N'), 'codes', _np.bincount([c for c in uniq_c], minlength=6).tolist())
    if path is None:
        print('  no alignment'); return
    M = sum(1 for x in path if x[2]); cols = len(path)
    print('  aligned cols', cols, 'matches', M, 'identity', round(M / cols * 100, 1))

if __name__ == '__main__':
    run('A01', 'base')
    run('A01', 'sep')
