import sys, glob, os, statistics, numpy as np
warnings = None
import warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/workspace')
from megabace.rsd import RsdFile
from megabace import signal as sigmod, utah
from megabace.spectral import deconvolve

NPTS, INPUTSTEP = 2048, 1900
letters = 'TGCA'
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

def engine(src, argmax_recode):
    n = src.shape[1]
    mb = utah.MB(fluor=True)
    passes = 1 if n < NPTS else min(int(np.ceil((n - NPTS) / INPUTSTEP)) + 1, 6)
    fbw = 82; prev_sp = None; finals = []; iSl = 0
    for p in range(1, passes + 1):
        w = src[:, iSl:iSl + NPTS]
        if w.shape[1] < NPTS:
            ww = np.zeros((4, NPTS)); ww[:, :w.shape[1]] = w; w = ww
        r = utah.nrefine_window(utah.blindeconv_matrix(w.T, mb, fbw).T, fbw, mb, letters)
        if r is None or len(r['mid']) < 2:
            break
        sp = utah.fband_space([iSl + m - 1 for m in r['mid']])
        if sp is None:
            break
        if prev_sp is not None and sp < prev_sp:
            sp = prev_sp
        prev_sp = sp; fbw = utah.fbwlut(sp, mb)
        r = utah.nrefine_window(utah.blindeconv_matrix(w.T, mb, fbw).T, fbw, mb, letters)
        if r is None:
            break
        finals.append((iSl, r))
        newStart = iSl + INPUTSTEP
        if newStart + NPTS >= n:
            newStart = n - NPTS
            if newStart <= iSl:
                break
        iSl = newStart
    mids = []; codes = []
    for iSl, r in finals:
        for m, c in zip(r['mid'], r['code']):
            mids.append(iSl + m - 1); codes.append(c)
    order = np.argsort(mids)
    mids = [mids[i] for i in order]; codes = [codes[i] for i in order]
    um = []; uc = []
    for m, c in zip(mids, codes):
        if um and abs(m - um[-1]) < 3:
            continue
        um.append(m); uc.append(c)
    if argmax_recode:
        uc = [int(np.argmax(src[:, m])) + 1 for m in um]
    return um, uc

def report(um, uc, label, well):
    seq = ''.join(letters[c - 1] if c in (1, 2, 3, 4) else 'N' for c in uc)
    path = sw(seq, refc)
    if path is None:
        print(well, label, len(seq), seq.count('N'), 'NOALIGN')
        return (well, label, len(seq), seq.count('N'), None, None, None, None)
    M = sum(1 for x in path if x[2]); cols = len(path)
    I = sum(1 for x in path if x[0] is not None and x[1] is None)
    D = sum(1 for x in path if x[1] is not None and x[0] is None)
    print(well, label, 'bands', len(seq), 'N', seq.count('N'), 'cols', cols,
          'id', round(M / cols * 100, 1), 'ins', I, 'del', D)
    return (well, label, len(seq), seq.count('N'), round(M / cols * 100, 1), I, D, cols)

if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'keep'
    out = []
    for f in sorted(glob.glob('MB1000_M13_DT/*.rsd')):
        well = os.path.basename(f)[:-4]
        rsd = RsdFile(f)
        tr = rsd.extract_traces()
        base = sigmod.subtract_baseline_multi(tr)
        src = sigmod.normalize_channels(deconvolve(base, None, True))
        um, uc = engine(src, mode == 'argmax')
        out.append(report(um, uc, mode, well))
    ids = [r[4] for r in out if r[4] is not None]
    print('MEAN', mode, round(statistics.mean(ids), 2), 'MEDIAN', round(statistics.median(ids), 2), 'n', len(ids))
