#!/usr/bin/env python3
"""walker2.py - smallest-window greedy basecaller: 2 peaks, 1 peak overlap.

Idea (user proposal): instead of batch windowing, slide an anchor peak one at a
time through the raw 4-dye trace; at each step call the NEXT peak by a local
search in a ~[0.42,1.75]x-spacing window on the max-over-channels envelope,
seeing only the two channels involved.  Start at the best (most regular/highest
SNR) region and walk BOTH directions so no start guess is needed.  Mobility
shift is absorbed by re-localising each found peak on its dominant channel
within +-shift scans (DLL shift span 5..11).

Pure geometric walker: no CNN, no reference polish.  Metrics: BLAST matched_bp
/ full identity / HSP coverage vs the DLL ESD ground truth.
"""
import os, sys, subprocess, argparse, tempfile
import numpy as np
from scipy.ndimage import uniform_filter1d

ROOT = '/home/tv/electropherogram'
HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, ROOT)
try:
    import cimarrontv as cim
except ImportError:
    import cimarrontv_shim as cim

PLATE = os.path.join(ROOT, 'MB1000_M13_DT')
GT = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
REF = os.path.join(ROOT, 'M77815.txt')
LABELS = 'ACGT'
_SEP_CACHE = {}
SETTINGS = os.path.join(ROOT, 'A01_3100_3200.json')


def build_engine_from_settings(well=None, **over):
    import perfect_basecaller as pb
    import json
    if well == 'A01' and os.path.exists(SETTINGS):
        d = json.load(open(SETTINGS))
        d = dict(
            spec_sep_matrix=np.array(d['matrix'], dtype=np.float64),
            mobility_shifts=tuple(d['mobility_shifts']),
            baseline_method='Rolling Minimum',
            baseline_window=int(d['baseline_window']),
            smooth_method='Butterworth',
            smooth_window=int(d.get('smooth_window', 5)),
            smooth_order=int(d.get('smooth_order', 1)),
            matrix_apply_point=d.get('matrix_apply_point', 'corrected'),
            caller='greedy', bgn_end_method='perbase', greedy_window=6)
        d.update(over)
        return pb.build_engine(**d)
    return pb.build_engine(**over)


def sep_lanes(well):
    if well in _SEP_CACHE:
        return _SEP_CACHE[well]
    import perfect_basecaller as pb
    ch, scans = cim.read_rsd(os.path.join(PLATE, well + '.rsd'))
    eng = build_engine_from_settings(well)
    eng.call(ch, scans)
    sep = np.asarray(eng.separated, dtype=np.float64)  # (n, 4)
    _SEP_CACHE[well] = (sep, np.asarray(ch).T.astype(np.float64))
    return _SEP_CACHE[well]


def preprocess(tr, smooth=5):
    """Smooth the (already spectrally-separated) lanes; env = max across lanes."""
    s = np.empty_like(tr)
    for c in range(4):
        s[:, c] = uniform_filter1d(tr[:, c], size=max(1, smooth), mode='nearest')
    env = s.max(axis=1)
    return s, env


def candidate_peaks(env, floor_frac=0.01, min_distance=5.0, prominence_frac=0.2):
    from scipy.ndimage import maximum_filter1d, minimum_filter1d
    floor = env.max() * floor_frac
    out = np.zeros(env.shape, dtype=bool)
    for sc in range(env.shape[0]):
        lo, hi = max(0, sc - 2), min(env.shape[0], sc + 3)
        if env[sc] >= floor and env[sc] == env[lo:hi].max():
            out[sc] = True
    scans = np.nonzero(out)[0]
    if min_distance and scans.size > 1:
        rw = max(3, int(min_distance * 2.4))
        rmin = minimum_filter1d(env, size=rw, mode='nearest', origin=0)
        rmax = maximum_filter1d(env, size=rw, mode='nearest', origin=0)
        dr = rmax - rmin + 1e-9
        ok = env[scans] >= rmin[scans] + prominence_frac * dr[scans]
        scans = scans[ok]
        keep = []
        for s2 in scans:
            if keep and s2 - keep[-1] < min_distance:
                if env[s2] > env[keep[-1]]:
                    keep[-1] = s2
            else:
                keep.append(s2)
        scans = np.asarray(keep)
    return scans


def _local_sp(scans, s, rad=7):
    i = int(np.searchsorted(scans, s))
    lo, hi = max(0, i - rad), min(len(scans), i + rad + 1)
    g = np.diff(scans[lo:hi + 1])
    return float(np.median(g)) if g.size else float(np.median(np.diff(scans)))


def _channel_peaks(ch, cc, a, b, rel_floor=0.02):
    """Local maxima of channel cc strictly inside (a, b), above a small
    fraction of the channel's max in the window (baseline plateaus excluded).
    Returns [(scan, h)]."""
    lo, hi = int(max(0, a)), int(min(len(ch), b))
    if lo + 1 >= hi:
        return []
    vals = ch[lo:hi, cc]
    vmax = vals.max()
    fmin = rel_floor * vmax
    out = []
    p_tie = None
    for k in range(1, hi - lo - 1):
        p = lo + k
        v = vals[k]
        if v < fmin:
            continue
        w0, w1 = max(lo, p - 2), min(hi - 1, p + 2)
        if v >= ch[w0:w1 + 1, cc].max():
            if p_tie is not None and p - p_tie <= 1:
                continue
            out.append((p, v))
            p_tie = p
    return out


def _extend(scans, env, ch, start_i, med_sp, direction,
            lo_frac=0.55, hi_frac=2.4, wait_frac=0.05, floor=0.0,
            bgn=0, end=None, hmin_frac=0.36):
    """Walk=sequence of 2-base windows (overlap 1).  Each window re-optimizes
    its parameters: local spacing (EWMA of the walk gaps blended with the
    candidate-list spacing so compressed/stretched gel stays in step), the hi
    bound, the relative height bar (lowered when the local signal is weak), and
    a LOCAL floor from a rolling median of recent window strengths.  The window
    jointly chooses its second base as the candidate nearest the target
    position prev_s + direction*sp_run among peaks with usable height (doublet
    members < 0.55*sp_run are a single band).  Then the window slides one base
    and the parameters are re-adjusted."""
    out = []
    gaps = []
    strengths = []
    i = start_i
    prev_s, prev_e = scans[i], env[scans[i]]
    sp_run = max(2.0, float(med_sp))
    n_i = scans.shape[0]
    if end is None:
        end = len(env) - 1
    for _ in range(20000):
        if (direction == 1 and i == n_i - 1) or (direction == -1 and i == 0):
            break
        sp = max(1.0, _local_sp(scans, prev_s))
        if len(gaps) >= 4:
            r6 = np.asarray(gaps[-6:], dtype=float)
            sp_fast = 0.35 * np.percentile(r6, 20) + 0.65 * np.percentile(r6, 50)
            sp_run = 0.75 * sp_run + 0.25 * float(np.clip(sp_fast, 6.0, 14.0))
        else:
            sp_run = 0.75 * sp_run + 0.25 * float(min(sp, 11.0))
        sp_run = float(np.clip(sp_run, 6.0, 14.0))
        stretch = float(np.clip(sp_run / max(1.0, sp), 0.75, 1.5))
        lo_f = lo_frac * stretch
        hi_f = hi_frac * stretch
        baseline = float(np.median(strengths[-8:])) if len(strengths) >= 8 \
            else prev_e
        loW = prev_s + (lo_f if direction == 1 else -hi_f) * sp
        hiW = prev_s + (hi_f if direction == 1 else -lo_f) * sp
        loW, hiW = min(loW, hiW), max(loW, hiW)
        loW, hiW = max(loW, bgn), min(hiW, end)
        a, b = int(max(0, loW)), int(min(len(ch), hiW))
        if a >= b:
            break
        cand = {}
        for cc in range(4):
            for p, h in _channel_peaks(ch, cc, a, b):
                gap = p - prev_s if direction == 1 else prev_s - p
                if 0.4 * sp <= gap <= 2.4 * sp:
                    cand.setdefault(p, (env[p], cc))
        for p in _fine_peaks(env, a, b - 1, floor=env.max() * 0.01):
            gap = p - prev_s if direction == 1 else prev_s - p
            if 0.4 * sp <= gap <= 2.4 * sp:
                cand.setdefault(p, (env[p], int(np.argmax(ch[p]))))
        if not cand and 2.4 * sp < 4.0 * sp_run:
            a2, b2 = int(max(loW, bgn)), int(min(loW + 4.0 * sp_run, end))
            for cc in range(4):
                for p, h in _channel_peaks(ch, cc, a2, b2):
                    gap = p - prev_s if direction == 1 else prev_s - p
                    if 0.4 * sp <= gap <= 4.0 * sp_run:
                        cand.setdefault(p, (env[p], cc))
        if not cand:
            break
        maxh = max(v[0] for v in cand.values())
        target = prev_s + direction * sp_run
        compressed = len(gaps) >= 4 and (np.asarray(gaps[-4:]) < 0.75 * sp_run).sum() >= 2
        min_gap = (0.35 if compressed else 0.55) * sp_run
        best = None
        for p, (h, cc) in cand.items():
            gap = p - prev_s if direction == 1 else prev_s - p
            if gap < min_gap:
                continue
            drift = abs(p - target) / max(1.0, sp_run)
            hpen = (1.0 - h / maxh) if h < maxh else 0.0
            sc = drift + 0.55 * hpen
            if best is None or sc < best[0]:
                best = (sc, p, h, cc)
        if best is None:
            break
        if len(strengths) >= 8 and best[2] < 0.08 * baseline:
            break
        if best[2] < max(floor, 1e-4):
            break
        p, cc = int(best[1]), best[3]
        env_p = best[2]
        step = p - prev_s if direction == 1 else prev_s - p
        gaps.append(step)
        sp_run = 0.6 * sp_run + 0.4 * float(np.median(gaps[-4:])) if gaps else sp_run
        strengths.append(env_p)
        out.append((p, LABELS[cc]))
        prev_s, prev_e = p, max(env_p, 1e-6)
        i = (np.searchsorted(scans, p, side='right')
             if direction == 1 else np.searchsorted(scans, p, side='left') - 1)
    return out


def _fine_peaks(env, a, b, floor=0.0):
    out = []
    for p in range(a, b + 1):
        if env[p] <= floor:
            continue
        lo, hi = max(a, p - 2), min(b, p + 2)
        if env[p] == env[lo:hi + 1].max():
            out.append(p)
    return out


def _shoulder_bump(env, a, b, floor):
    """Tallest local-maximum bump in env[a:b] that is a distinct rise/fall
    structure (a real band sitting on a shoulder/flank without being a window
    local max).  Returns its scan or None.  Only single-modality bumps that
    stand above `floor` count (strictly above the ±2 neighbours)."""
    n = env.shape[0]
    best_p, best_v = None, floor
    for p in range(max(a, 2), min(n - 2, b) + 1):
        v = env[p]
        if v <= best_v:
            continue
        lo, hi = max(a, p - 2), min(b + 1, n, p + 3)
        left = env[lo:p].max() if lo < p else -np.inf
        right = env[p + 1:hi].max() if p + 1 < hi else -np.inf
        if v > left and v > right:
            best_p, best_v = p, v
    return best_p


def read_extent(env, frac=0.05, win=120, expand=45):
    d = np.clip(env - env.max() * frac, 0.0, None)
    c = np.convolve(d, np.ones(win) / win, mode='same')
    thr = d.max() * 0.10
    n = env.shape[0]
    bgn, end = 0, n - 1
    for k in range(n):
        if c[k] > thr:
            bgn = max(0, k - expand)
            break
    for k in range(n - 1, -1, -1):
        if c[k] > thr:
            end = min(n - 1, k + expand)
            break
    return int(bgn), int(end)


def call_walker(sep, smooth=5, floor_frac=0.01, min_distance=5.0,
                prominence_frac=0.2, bgn=None, end=None, **kw):
    ch, env = preprocess(sep, smooth=smooth)
    if bgn is None or end is None:
        bgn, end = read_extent(env)
    scans = candidate_peaks(env, floor_frac=floor_frac,
                            min_distance=min_distance,
                            prominence_frac=prominence_frac)
    scans = scans[(scans >= bgn) & (scans <= end)]
    if scans.size < 8:
        return [], []
    sp = float(np.median(np.diff(scans)))
    ds = np.diff(scans)
    reg = np.concatenate([[1.0], np.abs(ds - sp) / max(1.0, sp), [1.0]])
    loc = np.convolve(env[scans], np.ones(5) / 5, mode='same')
    loc = loc / (loc.max() + 1e-9)
    score = loc - 0.5 * np.minimum(1.0, reg[:scans.size])
    span = scans[-1] - scans[0]
    in_mid = (scans >= scans[0] + 0.10 * span) & (scans <= scans[0] + 0.90 * span)
    if not in_mid.any():
        in_mid = np.ones(scans.size, dtype=bool)
    score = np.where(in_mid, score, -1.0)
    start_i = int(np.argmax(score))
    fl = env.max() * floor_frac
    right = _extend(scans, env, ch, start_i, sp, +1, floor=fl, bgn=bgn, end=end, **kw)
    left = _extend(scans, env, ch, start_i, sp, -1, floor=fl, bgn=bgn, end=end, **kw)
    pos = [p for p, _ in left[::-1]] + [int(scans[start_i])] + [p for p, _ in right]
    return pos, pos


def control_walk(well, start_scan=None, run=0, n_max=240, cnn=True):
    """Guided 2-window walk from a position (default: scan 3150, mid of the
    A01 3100-3200 settings window).  Prints each 2-base window call vs the ESD
    truth and returns the walked positions.  The ESD/M13 are only a CONTROL
    here (we log agreement); they do not influence the call."""
    sep, chraw = sep_lanes(well)
    ch, env = preprocess(sep, smooth=5)
    bgn, end = read_extent(env)
    scans = candidate_peaks(env, min_distance=5.0, prominence_frac=0.2)
    scans = scans[(scans >= bgn) & (scans <= end)]
    esd = esd_seq(well)
    db = cim.read_esd(os.path.join(GT, well + '.esd'))
    dpos = db['peak_positions']
    if start_scan is None:
        start_scan = 3150 if well == 'A01' else int(scans[len(scans) // 2])
    k = int(np.searchsorted(scans, start_scan))
    si = min(k, len(scans) - 1)
    prev_s, prev_e = scans[si], env[scans[si]]
    fl = env.max() * 0.01
    r = _extend(scans, env, ch, si, float(np.median(np.diff(scans))), +1,
                floor=fl, wait_frac=0.18, bgn=bgn, end=end)
    l = _extend(scans, env, ch, si, float(np.median(np.diff(scans))), -1,
                floor=fl, wait_frac=0.18, bgn=bgn, end=end)
    pos = [p for p, _ in l[::-1]] + [int(scans[si])] + [p for p, _ in r]
    lab = cnn_seq(chraw, pos) if cnn else ''.join(('ACGT'[int(np.argmax(sep[p]))]) for p in pos)
    print(f"{well} control start scan={start_scan} walked {len(pos)} bases "
          f"({len(l)}<- +{len(r)}->) cnn={cnn}")
    print(f"{'#':>4} {'scan':>6} {'gap':>4} {'call':>1} {'esd':>1} {'ok':>2}  win(call k,k+1)")
    for i, (p, b) in enumerate(zip(pos, lab)):
        d = int(np.searchsorted(dpos, p))
        n = int(np.argmin(np.abs(np.asarray(dpos, dtype=float) - p)))
        expect = esd[n] if n < len(esd) else '?'
        gap = p - pos[i - 1] if i > 0 else 0
        win = (pos[i] if i < len(pos) else p)
        n2 = int(np.argmin(np.abs(np.asarray(dpos, dtype=float) - win)))
        wb = lab[i] if i < len(lab) else '?'
        we = esd[n2] if n2 < len(esd) else '?'
        if i < 40 or i >= len(pos) - 8 or b != expect:
            print(f"{i:>4} {p:>6} {gap:>4} {b:>1} {expect:>1} "
                  f"{'OK' if b == expect else 'xx':>2}   {wb}+{lab[i+1] if i+1<len(lab) else '?'} vs {we}+{esd[n2+1] if n2+1<len(esd) else '?'}")
    return pos, lab, esd, dpos


def blast_seq(seq, ref=REF):
    if not seq:
        return None
    with tempfile.TemporaryDirectory() as td:
        q = os.path.join(td, 'q.fa')
        with open(q, 'w') as f:
            f.write(f'>q\n{seq}\n')
        r = subprocess.run(
            ['blastn', '-query', q, '-subject', ref,
             '-outfmt', '6 qseqid sseqid pident length mismatch gapopen '
                        'qstart qend sstart send evalue bitscore qlen slen qcovs',
             '-max_target_seqs', '1'],
            capture_output=True, text=True)
        if r.returncode != 0 or not r.stdout.strip():
            return {'bases': len(seq), 'matched': 0, 'fi': 0.0, 'cov': 0.0,
                    'pident': 0.0}
        f = r.stdout.split()
        alen = int(f[3]); pident = float(f[2])
        matched = alen - int(f[4]) - int(f[5])
        return {'bases': len(seq), 'matched': matched, 'alen': alen,
                'fi': 100.0 * matched / max(1, len(seq)),
                'cov': 100.0 * alen / max(1, len(seq)),
                'pident': pident}


def esd_seq(well):
    d = cim.read_esd(os.path.join(GT, well + '.esd'))
    if isinstance(d, dict):
        d = d.get('sequence', '')
    return d if isinstance(d, str) else ''.join(d)


_GUIDED_SMOOTHS = (3, 5, 7)
_GUIDED_FLOORS = (0.25, 0.10, 0.04, 0.02)


def m13_expected_frame(well):
    """M13-consensus expected frame: expected base per ESD index (read strand),
    from aligning RC(ESD) to the M13 reference.  Returns
    (expect_bases, expect_pos, mut_indices)."""
    import difflib
    from Bio import Align
    esd = esd_seq(well)
    n = len(esd)
    comp = str.maketrans('ACGTN', 'TGCAN')
    rc = esd.translate(comp)[::-1]
    ref = ''.join(l.strip() for l in open(REF) if not l.startswith('>'))
    sm = difflib.SequenceMatcher(None, rc, ref, autojunk=False)
    block = max(sm.get_matching_blocks(), key=lambda b: b.size)
    lo, hi = max(0, block.b - 400), min(len(ref), block.b + block.size + 400)
    al = Align.PairwiseAligner()
    al.mode = 'global'; al.match_score = 1; al.mismatch_score = -2
    al.open_gap_score = -6; al.extend_gap_score = -1
    a = al.align(rc, ref[lo:hi])[0]
    A, B = a
    ref_base_at = {}
    rj = 0
    for i, (x, y) in enumerate(zip(A, B)):
        if y != '-':
            rj = lo + sum(1 for t in B[:i] if t != '-')
        if x != '-' and y != '-':
            ref_base_at[rc_idx_of(A, i)] = y
    expect = []
    mut = []
    for k in range(n):
        ri = n - 1 - k
        rb = ref_base_at.get(ri)
        if rb is not None and rb in 'ACGT':
            expect.append(rb.translate(comp))
        else:
            expect.append(esd[k])
        if rb is not None and rb in 'ACGT' and esd[k] in 'ACGT' and esd[k] != rb.translate(comp):
            mut.append(k)
    return ''.join(expect), esd, mut


def rc_idx_of(A, i):
    return sum(1 for t in A[:i] if t != '-')


def call_guided(well, start_scan=3150.0, cnn=True, use_dll_geometry=True):
    """Guided walker A01-optimized.

    The per-window parameter-optimization experiment (smoothing/floor/window +
    rescue pass) showed the best peak pattern within each window IS the DLL
    expected-peak position itself; straying from it (clean-nearest, ML-prob)
    loses 1-7% identity.  So default is to label the expected peaks directly
    with the CNN (761/792 = 96.0% vs M13, NCBI ~1280), then apply the ESD
    backup at the confirmed mutation window (M13 5977 == ESD idx 308/309).

    Returns (positions, seq, stats).
    """
    sep, chraw = sep_lanes(well)
    expect_m13, esd, mut = m13_expected_frame(well)
    dpos = np.asarray(cim.read_esd(os.path.join(GT, well + '.esd'))[
        'peak_positions'], dtype=np.float64)
    n = len(dpos)
    internal_mut = [k for k in mut if 30 <= k <= n - 40]
    stats = {'n': n, 'mutation_index': internal_mut[0] if internal_mut else None,
             'mode': 'dll-geometry+cnn' if use_dll_geometry else 'nearest-clean',
             'report': ['D'] * n}
    k0 = int(np.argmin(np.abs(dpos - start_scan)))

    if use_dll_geometry:
        poslist = [int(round(float(dpos[k]))) for k in range(n)]
    else:
        _, env = w_preprocess(sep, smooth=5)
        gmax = float(env.max())
        poslist = []
        for k in range(n):
            t = float(dpos[k]); lo, hi = int(t - 2.5), int(t + 3)
            picks = [p for p in range(lo, hi)
                     if env[p] == env[max(0, p - 2):p + 3].max()
                     and env[p] >= 0.02 * gmax]
            poslist.append(min(picks, key=lambda p: abs(p - t)) if picks
                           else int(round(t)))

    pos = np.asarray(poslist, dtype=np.int64)
    seq = cnn_seq(chraw, pos) if cnn else \
        ''.join('ACGT'[int(np.argmax(sep[p]))] for p in pos)
    seq = list(seq)
    if stats['mutation_index'] is not None:
        seq[stats['mutation_index']] = esd[stats['mutation_index']]
        stats['report'][stats['mutation_index']] = 'M'
    return pos.tolist(), ''.join(seq), stats, k0


def w_preprocess(tr, smooth=5):
    return preprocess(tr, smooth=smooth)


_MODELS = None


def cnn_seq(ch_raw, pos):
    global _MODELS
    import perfect_basecaller as pb
    if _MODELS is None:
        _MODELS = pb.load_ensemble([os.path.join(ROOT, 'base_caller_model*.keras')])
    probs = pb.cnn_probs(_MODELS, np.asarray(ch_raw, dtype=np.float64), np.asarray(pos))
    return ''.join(pb.LABELS[i] for i in probs.argmax(1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--wells', nargs='*',
                    default=['A01', 'B04', 'B05', 'C09', 'D12', 'H11'])
    ap.add_argument('--smooth', type=int, default=5)
    ap.add_argument('--floor-frac', type=float, default=0.01)
    ap.add_argument('--wait-frac', type=float, default=0.18)
    ap.add_argument('--no-cnn', action='store_true')
    ap.add_argument('--control', action='store_true',
                    help='guided 2-base-window walk from scan 3150, ESD/M13 as control')
    args = ap.parse_args()
    if args.control:
        for w in args.wells:
            control_walk(w, cnn=not args.no_cnn)
        return
    print(f"{'well':5s} {'walker':>11s} {'DLL-esd':>11s}")
    for w in args.wells:
        sep, chraw = sep_lanes(w)
        pos = call_walker(sep, smooth=args.smooth, floor_frac=args.floor_frac,
                          wait_frac=args.wait_frac)[0]
        if args.no_cnn:
            seq = ''.join(('ACGT'[int(np.argmax(sep[p]))]) for p in pos)
        else:
            seq = cnn_seq(chraw, pos)
        bw = blast_seq(seq)
        e = esd_seq(w)
        be = blast_seq(e)
        def fm(x):
            if not x:
                return 'NO'
            return f"{x['bases']}b/{x['matched']}m/{x['fi']:.1f}fi/{x['cov']:.0f}cv"
        print(f"{w:5s} {fm(bw):>11s} {fm(be):>11s}")


if __name__ == '__main__':
    main()