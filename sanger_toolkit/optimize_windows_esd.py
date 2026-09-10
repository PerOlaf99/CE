#!/usr/bin/env python3
"""
Per-window automated optimizer for A01.

v2.0 changes:
A) PIPELINE PARITY - candidates run through the SAME pipeline the GUI uses:
   sanger_toolkit.dsp.dsp_full_pipeline, including the correct GUI apply points
   {none, offset, raw, corrected, smoothed, shifted}. Previously this script
   called the older dsp_core.full_pipeline, which diverged from what the GUI
   actually produces (no 'offset' point, different 'raw' semantics).
B) M13 TARGET - the objective no longer scores against the analyzer's OWN ESD
   basecall (that just reproduces the manual settings).  The ESD trace's peak
   positions are aligned once to the M13 reference (trying both strands), and
   each window is scored against the corresponding M13 substring.  DE now
   optimizes agreement with the true reference.
C) ROBUSTNESS - after the pipeline runs at norm_window, the call is repeated at
   norm_window*1.5 and norm_window/1.5.  The objective is the WORST of the three
   scores (plus a small length-variance penalty), so norm-fragile settings that
   flip CC<->G etc. when the trace normalization window shifts are rejected.
D) SEEDED REDUCED-DIM SEARCH - --freeze {baseline,smooth,matrix,greedy,all}
   pins whole parameter groups at the --init-json settings (default
   A01_2050_2411.json, the established good manual settings), so DE only
   searches the dims you actually want to retune.  x0 is seeded from the JSON.
E) REPORTING - identity is reported vs BOTH the M13 target and the ESD window,
   with an explicit mismatch list, and stored in the output JSON.

Search space per window (CLI-gated):
  10 core dims  - baseline_method, baseline_window(01), baseline_window2(01),
                  smooth_method, smooth_window(01), smooth_order(01),
                  4 mobility shifts
  4 mobility shifts
  10 matrix_apply_point  - discrete {none, offset, raw, corrected, smoothed, shifted}
                            (pinnable with --matrix-apply-point for labels that are
                            comparable across windows/wells)
  11+ matrix      - 'diag' (4 entries) or 'full' (16 entries) or fixed
  greedy knobs  - min_distance(window), prominence_frac, norm_window
Run:
  python3 optimize_windows_esd.py --well A01 --win-size 700 --overlap 100 \
      --method greedy --tune-matrix diag --maxiter 40 --popsize 12 --workers 8
"""
import argparse, json, os, sys, time
import numpy as np
from scipy.optimize import differential_evolution

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, '99_archive'))
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import dsp
import dsp_core
from basecall import pc_call_bases_greedy, pc_call_bases_with_shifts
from optimize_params import BASELINE_METHODS, SMOOTH_METHODS
import extract_training_data as etd

ESD_SUBDIR = 'MB1000_M13_DT_Cp312_MD1'
APPLY_POINTS = ['none', 'offset', 'raw', 'corrected', 'smoothed', 'shifted']
MOBILITY_MAX_SHIFT = 10
MATRIX_ENTRY_MAX = 5.0
# Per extra base emitted beyond the expected ESD length, subtract OVER_PENALTY from
# the objective. Discourages the DE from over-calling (blowing past ESD density)
# even after the min_distance_floor knob bottoms out.
OVER_PENALTY = 0.15
# Tolerance: only penalise once len(seq) exceeds expected*OVER_TOL.
OVER_TOL = 1.10


def load_well(base_dir, well, esd_subdir):
    d = etd.parse_esd(os.path.join(base_dir, esd_subdir, well + '.esd'))
    seq = d['sequence']
    pp = np.asarray(d['peak_positions'], dtype=np.int64)
    raw = etd.parse_rsd(os.path.join(base_dir, well + '.rsd'))
    raw = raw[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.astype(np.float64)
    return raw, seq, pp


def _map01(u, lo, hi):
    return lo + float(np.clip(u, 0.0, 1.0)) * (hi - lo)


def decode(x, tune_matrix, greedy, pinned_ap=None):
    """Full per-window params from the DE vector x (0-1 normalized)."""
    bl_idx = int(np.clip(np.floor(x[0]), 0, len(BASELINE_METHODS) - 1))
    bl_method = BASELINE_METHODS[bl_idx]
    _, bl_range, _, bl2_range = dsp_core.BASELINE_PARAM_CONFIG[bl_method]
    bl_window = _map01(x[1], *bl_range)
    bl_window2 = _map01(x[2], *bl2_range) if bl2_range is not None else None

    sm_idx = int(np.clip(np.floor(x[3]), 0, len(SMOOTH_METHODS) - 1))
    sm_method = SMOOTH_METHODS[sm_idx]
    _, r1, _, r2 = dsp_core.SMOOTH_PARAM_CONFIG[sm_method]
    sm_window = _map01(x[4], *r1)
    sm_order = _map01(x[5], *r2)
    if sm_method in ('Savitzky-Golay', 'Moving Avg', 'Median'):
        sm_window = int(round(sm_window))
        if sm_window % 2 == 0:
            sm_window += 1
    else:
        sm_window = sm_window if sm_method == 'Whittaker' else int(round(sm_window))
    sm_order = int(round(sm_order))

    shifts = np.round([_map01(x[6 + ch], -MOBILITY_MAX_SHIFT, MOBILITY_MAX_SHIFT)
                       for ch in range(4)]).astype(np.int64).tolist()

    if pinned_ap is None:
        ap_idx = int(np.clip(np.floor(x[10]), 0, len(APPLY_POINTS) - 1))
        matrix_apply_point = APPLY_POINTS[ap_idx]
    else:
        matrix_apply_point = pinned_ap

    if tune_matrix == 'full':
        matrix = np.array([_map01(v, 0.0, MATRIX_ENTRY_MAX)
                           for v in x[11:27]]).reshape(4, 4)
    elif tune_matrix == 'diag':
        diag = np.array([_map01(x[11 + i], 0.20, 0.99) for i in range(4)])
        matrix = dsp_core.make_matrix_from_diagonals(diag)
    else:
        matrix = dsp_core.DEFAULT_SPEC_MATRIX

    if greedy:
        g0 = 11 + (4 if tune_matrix == 'diag' else 16 if tune_matrix == 'full' else 0)
        min_distance = max(1.0, _map01(x[g0], 1.0, 12.0))
        prominence_frac = _map01(x[g0 + 1], 0.01, 0.60)
        norm_window = max(20.0, _map01(x[g0 + 2], 20, 4000))
        min_distance_floor = max(1.0, _map01(x[g0 + 3], 2.0, 7.0))
    else:
        min_distance, prominence_frac, norm_window = 4.0, 0.1, 200.0
        min_distance_floor = 1.0

    return dict(baseline_method=bl_method, baseline_window=bl_window,
                baseline_window2=bl_window2, smooth_method=sm_method,
                smooth_window=sm_window, smooth_order=sm_order,
                mobility_shifts=shifts, matrix=np.asarray(matrix, dtype=np.float64),
                matrix_apply_point=matrix_apply_point,
                min_distance=min_distance, prominence_frac=prominence_frac,
                norm_window=norm_window, min_distance_floor=min_distance_floor)


def n_dims(tune_matrix, greedy):
    base = 11 + (4 if tune_matrix == 'diag' else 16 if tune_matrix == 'full' else 0)
    return base + (4 if greedy else 0)


def x0_from(params, tune_matrix, greedy):
    x = [float(BASELINE_METHODS.index(params['baseline_method'])) + 0.5]
    _, br, _, br2 = dsp_core.BASELINE_PARAM_CONFIG[params['baseline_method']]
    x.append((params['baseline_window'] - br[0]) / (br[1] - br[0]))
    if br2 is None:
        x.append(0.0)  # placeholder, ignored by decode
    else:
        bw2 = params.get('baseline_window2', br2[0])
        x.append(float(np.clip((bw2 - br2[0]) / (br2[1] - br2[0]), 0.0, 1.0)))
    x.append(float(SMOOTH_METHODS.index(params['smooth_method'])) + 0.5)
    _, r1, _, r2 = dsp_core.SMOOTH_PARAM_CONFIG[params['smooth_method']]
    x.append((params['smooth_window'] - r1[0]) / (r1[1] - r1[0]))
    x.append((params['smooth_order'] - r2[0]) / (r2[1] - r2[0]))
    for ch in range(4):
        x.append((params['mobility_shifts'][ch] + MOBILITY_MAX_SHIFT) / (2 * MOBILITY_MAX_SHIFT))
    ap = params.get('matrix_apply_point', 'smoothed')
    x.append(APPLY_POINTS.index(ap) if ap in APPLY_POINTS else 3)
    mat = np.array(params['matrix'], dtype=np.float64)
    if tune_matrix == 'full':
        for i in range(16):
            x.append(float(np.clip(mat.reshape(-1)[i] / MATRIX_ENTRY_MAX, 0, 1)))
    elif tune_matrix == 'diag':
        for i in range(4):
            lo, hi = 0.20, 0.99
            x.append(float(np.clip((np.diag(mat)[i] - lo) / (hi - lo), 0, 1)))
    if greedy:
        x.append((params.get('min_distance', 5.0) - 1.0) / 11.0)
        x.append((params.get('prominence_frac', 0.1) - 0.01) / 0.59)
        x.append((params.get('norm_window', 200) - 20.0) / 3980.0)
        x.append(float(np.clip((params.get('min_distance_floor', 4.0) - 2.0) / 5.0, 0, 1)))
    return x


def call_window_pairs(raw, params, region, method):
    """Same pipeline as the GUI (dsp_full_pipeline / dsp.py).  Mobility shifts
    are passed through exactly like the GUI does; for every apply point except
    'shifted' they are ignored by the pipeline and used by the caller below.
    Returns (positions, call_sequence)."""
    _, _, _, _, separated, _ = dsp.dsp_full_pipeline(
        raw, list(params['mobility_shifts']), params['baseline_method'],
        params['baseline_window'], params['smooth_method'], params['smooth_window'],
        params['smooth_order'], params['matrix'],
        baseline_window2=params.get('baseline_window2'),
        matrix_apply_point=params.get('matrix_apply_point', 'smoothed'))
    shifts = list(params['mobility_shifts'])
    if method == 'greedy':
        pos, seq, _, _ = pc_call_bases_greedy(
            separated, shifts, window=max(1, int(round(params.get('min_distance', 5)))),
            min_frac=params.get('prominence_frac', 0.1),
            norm_window=max(1, int(round(params.get('norm_window', 800)))),
            region=region, min_distance_floor=params.get('min_distance_floor', 1))
    else:
        pos, seq, _, _ = pc_call_bases_with_shifts(
            separated, shifts, min_distance=max(1, int(round(params.get('min_distance', 4)))),
            prominence_frac=params.get('prominence_frac', 0.05),
            norm_window=max(1, int(round(params.get('norm_window', 800)))),
            region=region)
    seq = ''.join(b for b in seq if b in 'ACGT')
    return pos, seq


def call_window(raw, params, region, method):
    _, seq = call_window_pairs(raw, params, region, method)
    return seq


def local_ident_score(seq, target, floor=0.85):
    """Strict LOCAL Smith-Waterman of seq vs target (the ESD window). Returns
    (matches, aln_len, identity). Only counts when identity >= floor, otherwise
    returns tiny score so DE cannot exploit random matches."""
    q, r = seq, target
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0, 0, 0.0
    match, mismatch, gap = 2, -1, -2
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    best = 0
    best_i = best_j = 0
    for i in range(1, m + 1):
        qi = q[i - 1]
        for j in range(1, n + 1):
            diag = dp[i - 1, j - 1] + (match if qi == r[j - 1] else mismatch)
            up = dp[i - 1, j] + gap
            left = dp[i, j - 1] + gap
            v = max(0, diag, up, left)
            dp[i, j] = v
            if v > best:
                best = v; best_i = i; best_j = j
    # backtrack from best (local)
    i, j = best_i, best_j
    matches = aligned = 0
    while i > 0 and j > 0 and dp[i, j] > 0:
        if dp[i - 1, j - 1] + (match if q[i - 1] == r[j - 1] else mismatch) == dp[i, j]:
            aligned += 1
            if q[i - 1] == r[j - 1]:
                matches += 1
            i -= 1; j -= 1
        elif dp[i - 1, j] + gap == dp[i, j]:
            aligned += 1; i -= 1
        elif dp[i, j - 1] + gap == dp[i, j]:
            aligned += 1; j -= 1
        else:
            i -= 1; j -= 1
    identity = matches / aligned if aligned else 0.0
    if identity >= floor:
        return matches, aligned, identity
    return 0, aligned, identity


def esd_window(esd_seq, esd_pp, s0, e0):
    """ESD substring whose peak scans fall in [s0,e0]."""
    m = (esd_pp >= s0) & (esd_pp <= e0)
    idx = np.where(m)[0]
    if len(idx) == 0:
        # nearest peak for context
        i = int(np.argmin(np.abs(esd_pp - (s0 + e0) / 2)))
        return esd_seq[max(0, i - 40): i + 80]
    a, b = int(idx.min()), int(idx.max())
    return esd_seq[max(0, a - 10): b + 1]


def anchored_m13_window_target(esdwin, m13, margin=20):
    """Reliable M13 target for an ESD window substring.

    build_m13_map()'s full-read local alignment is unreliable on these reads
    (diffuse, ~25%), which makes make_m13_window_target() return a corrupt
    target.  Instead we local-align the (short, trustworthy) ESD window against
    M13 in both orientations and cut the M13 slice covering it, in read
    orientation, padded by ``margin`` on each side.

    Returns (target, rev, coords):
      target - M13 string in read orientation (scorable against the call), or
               ``esdwin`` itself when no alignment is good enough
      rev    - True when the read runs reverse-strand to stored M13
      coords - (sstart, send) 1-based stored-M13 coordinates of the aligned
               region (may be descending when rev), or (0, 0) on fallback
    """
    from Bio import Align
    from Bio.Seq import Seq as BioSeq
    al = Align.PairwiseAligner()
    al.mode = 'local'
    al.match_score = 2
    al.mismatch_score = -1
    al.open_gap_score = -2
    al.extend_gap_score = -1
    m13u = m13.upper()
    cand = []
    for s_or, rev in ((m13u, False),
                      (str(BioSeq(m13u).reverse_complement()), True)):
        a = al.align(esdwin, s_or)[0]
        if len(a.aligned) == 0:
            continue
        try:
            s_range = a.aligned[1][0]
        except (IndexError, TypeError):
            continue
        s, e = int(s_range[0]), int(s_range[1]) - 1   # subject start,end
        if (e - s + 1) < max(10, 0.7 * len(esdwin)):
            continue
        ident = a.score / (2 * (e - s + 1)) if e >= s else 0.0
        cand.append((a.score, ident, rev, s_or, s, e))
    if not cand:
        return esdwin, False, (0, 0)
    _, ident, rev, s_or, s, e = max(cand, key=lambda t: (t[0], t[1]))
    L = len(s_or)
    lo, hi = max(0, s - margin), min(L, e + margin + 1)
    target = s_or[lo:hi]
    if rev:
        n = len(m13u)
        coords = (n - hi + 1, n - lo)   # stored 1-based, descending when rev
    else:
        coords = (lo + 1, hi)
    return target, rev, coords


def _global_score(seq, target):
    """Global alignment of the window call vs its ESD window substring (the same
    shift-tolerant global alignment that gave ~98% on the full read). Returns
    (matches, aligned_len)."""
    from Bio import Align
    al = Align.PairwiseAligner()
    al.mode = 'global'
    al.match_score = 2
    al.mismatch_score = -1
    al.open_gap_score = -2
    al.extend_gap_score = -1
    a, b = al.align(seq, target)[0]
    matches = sum(1 for x, y in zip(a, b) if x == y and x != '-')
    non_gap = sum(1 for x, y in zip(a, b) if x != '-' and y != '-')
    return matches, non_gap


def load_reference(ref_fa_path):
    """Return the M13 reference sequence (uppercase) from a FASTA file."""
    from Bio import SeqIO
    for rec in SeqIO.parse(ref_fa_path, 'fasta'):
        return str(rec.seq).upper()
    raise SystemExit(f'reference fasta empty or missing: {ref_fa_path}')


def build_m13_map(esd_seq, m13):
    """Local-align the analyzer basecall (read order) against M13, trying both
    strands.  Returns (s_or, rev, m13_pos) where s_or is M13 in the orientation
    the read covers (read scan index increases with s_or index), rev=True when
    the read runs reverse-strand to the stored M13, and m13_pos[i] is the 0-based
    s_or coordinate of ESD base i.  LOCAL alignment is essential: the read sits
    on a contiguous ~1:1 stretch of M13, and a global alignment stretches the
    short read across the whole reference with fake end clusters."""
    from Bio import Align
    from Bio.Seq import Seq as BioSeq
    al = Align.PairwiseAligner()
    al.mode = 'local'
    al.match_score = 2
    al.mismatch_score = -1
    al.open_gap_score = -2
    al.extend_gap_score = -1
    m13u = m13.upper()
    cand = []
    for s_or, rev in ((m13u, False),
                      (str(BioSeq(m13u).reverse_complement()), True)):
        a = al.align(esd_seq, s_or)[0]
        cand.append((a.score, s_or, rev, a))
    cand.sort(key=lambda t: -t[0])
    score, s_or, rev, a = cand[0]
    m13_pos = np.full(len(esd_seq), -1, dtype=np.int64)
    mi = ei = -1
    for c1, c2 in zip(a[0], a[1]):
        if c2 != '-':
            mi += 1
        if c1 != '-':
            ei += 1
            if c2 != '-':
                m13_pos[ei] = mi
    valid = np.where(m13_pos >= 0)[0]
    if len(valid):
        m13_pos[:valid[0]] = m13_pos[valid[0]]
        for i in range(valid[0] + 1, len(m13_pos)):
            if m13_pos[i] < 0:
                m13_pos[i] = m13_pos[i - 1]
    elif len(m13_pos):
        m13_pos[:] = 0
    return s_or, rev, m13_pos


def make_m13_window_target(esd_seq, esd_pp, s0, e0, m13_pos, s_or):
    """M13 substring corresponding to the ESD peaks in scan window [s0,e0],
    with the same +/-10-base context that esd_window() used."""
    m = (esd_pp >= s0) & (esd_pp <= e0)
    idx = np.where(m)[0]
    L = len(m13_pos)
    if len(idx) == 0:
        i = int(np.argmin(np.abs(esd_pp - (s0 + e0) / 2)))
        a = max(0, min(L - 1, i - 40))
        b = max(0, min(L - 1, i + 80))
        return s_or[m13_pos[a]: m13_pos[b] + 1]
    a = max(0, int(idx.min()) - 10)
    b = min(L - 1, int(idx.max()))
    return s_or[m13_pos[a]: m13_pos[b] + 1]


def mismatch_list(seq, target, top=60):
    """Call positions (0-based) where seq disagrees with the M13 target."""
    from Bio import Align
    al = Align.PairwiseAligner()
    al.mode = 'global'
    al.match_score = 2
    al.mismatch_score = -1
    al.open_gap_score = -2
    al.extend_gap_score = -1
    a, b = al.align(seq, target)[0]
    out, ci = [], 0
    for x, y in zip(a, b):
        if x != '-' and y != '-' and x != y:
            out.append((ci, x, y))
        if x != '-':
            ci += 1
    return out[:top]


def refine_objective(params, raw, region, target, method, robust=True):
    """Score a candidate call against the M13 target.  When robust, also
    re-call at norm_window*1.5 and norm_window/1.5 and take the WORST score of
    the three (plus a small length-variance penalty): a setting whose call
    collapses when the normalization window changes by ~a few hundred scans is
    rejected, which is what kills the norm-fragile CC<->G flips."""
    base = dict(params)
    n = float(params.get('norm_window', 200))
    norms = [n]
    if robust:
        for f in (1.5, 1.0 / 1.5):
            v = float(np.clip(n * f, 20, 4000))
            if v not in norms:
                norms.append(v)
    scores, lens = [], []
    for nd in norms:
        p2 = dict(base)
        p2['norm_window'] = nd
        seq = call_window(raw, p2, region, method)
        if len(seq) < 5:
            scores.append(0.0)
            lens.append(0)
            continue
        matches, non_gap = _global_score(seq, target)
        cov = non_gap / len(target) if target else 0.0
        expected = len(target)
        overlen = max(0, len(seq) - int(expected * OVER_TOL))
        scores.append(float(matches) + 2.0 * cov - OVER_PENALTY * overlen)
        lens.append(len(seq))
    final = min(scores)
    if robust and len(lens) >= 2:
        final -= 0.02 * (max(lens) - min(lens))
    return max(final, 0.0)


def _objective(x, ctx):
    raw, region, target, method, tune_matrix, greedy, robust, pinned_ap = ctx
    params = decode(x, tune_matrix, greedy, pinned_ap)
    return -refine_objective(params, raw, region, target, method, robust)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--well', default='A01')
    ap.add_argument('--base-dir', default=os.path.join(ROOT, 'MB1000_M13_DT'))
    ap.add_argument('--esd-subdir', default=ESD_SUBDIR)
    ap.add_argument('--ref', default=os.path.join(HERE, 'refs', 'm13_M77815.1.fa'),
                    help='M13 reference FASTA used as the scoring target')
    ap.add_argument('--init-json', default=None,
                    help='seed settings JSON (default A01_2050_2411.json)')
    ap.add_argument('--freeze', choices=['none', 'baseline', 'smooth', 'matrix', 'greedy', 'all'],
                    default='none', help='pin parameter group(s) at the init-json values (reduced-dim search)')
    ap.add_argument('--no-robust', action='store_true',
                    help='disable +/-50% norm_window robustness checks (saves 3x pipeline calls)')
    ap.add_argument('--win-size', type=int, default=700)
    ap.add_argument('--overlap', type=int, default=100)
    ap.add_argument('--min-win', type=int, default=2050)
    ap.add_argument('--max-win', type=int, default=9332)
    ap.add_argument('--method', choices=['greedy', 'shifts'], default='greedy')
    ap.add_argument('--tune-matrix', nargs='?', const='diag', choices=['diag', 'full'], default=None)
    ap.add_argument('--matrix-apply-point', dest='pin_ap', choices=APPLY_POINTS, default=None,
                    help='pin matrix_apply_point during the search (produces matrix '
                         'labels that are comparable across windows/wells, e.g. "corrected")')
    ap.add_argument('--no-greedy-knobs', action='store_true', help='keep greedy knobs fixed at defaults')
    ap.add_argument('--maxiter', type=int, default=40)
    ap.add_argument('--popsize', type=int, default=12)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--outdir', default=os.path.join(HERE, 'opt_windows_esd'))
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--win', type=int, default=None, help='only optimize window index (1-based); omit to run all windows')
    args = ap.parse_args()

    greedy = not args.no_greedy_knobs
    robust = not args.no_robust
    raw, esd_seq, esd_pp = load_well(args.base_dir, args.well, args.esd_subdir)
    n = len(raw) - 2008
    print(f'{args.well}: raw len={len(raw)}, esd len={len(esd_seq)}, esd peaks {esd_pp.min()}-{esd_pp.max()}')

    init_path = args.init_json or os.path.join(HERE, 'A01_2050_2411.json')
    if not os.path.exists(init_path):
        raise SystemExit(f'--init-json not found: {init_path}')
    init = json.load(open(init_path))
    init_params = dict(
        baseline_method=init['baseline_method'], baseline_window=init['baseline_window'],
        baseline_window2=init.get('baseline_window2'),
        smooth_method=init['smooth_method'], smooth_window=init['smooth_window'],
        smooth_order=init['smooth_order'], mobility_shifts=list(init['mobility_shifts']),
        matrix=np.array(init['matrix']), matrix_apply_point=args.pin_ap or init.get('matrix_apply_point', 'smoothed'),
        min_distance=init.get('min_distance', 5.0), prominence_frac=init.get('prominence_frac', 0.1),
        norm_window=init.get('norm_window', 200),
    )

    # --- M13 reference map, built once for the whole read ---
    m13_ref = load_reference(args.ref)
    s_or, rev, m13_pos = build_m13_map(esd_seq, m13_ref)
    print(f'M13 ref {os.path.basename(args.ref)} len={len(m13_ref)}: read runs '
          f'{"reverse strand (stored M13 revcomp)" if rev else "forward strand"} of M13')

    lo, hi = args.min_win, args.max_win
    step = args.win_size - args.overlap
    windows = []
    s = lo
    while s < hi:
        e = min(len(raw), s + args.win_size)
        windows.append((s, e))
        s += step
        if e >= hi:
            break
    print(f'{len(windows)} windows (size={args.win_size}, overlap={args.overlap}):')
    for s, e in windows:
        print(f'  [{s}, {e}]')

    D = n_dims(args.tune_matrix, greedy)
    bounds = [(0, len(BASELINE_METHODS) - 1e-6), (0, 1), (0, 1),
              (0, len(SMOOTH_METHODS) - 1e-6), (0, 1), (0, 1),
              (0, 1), (0, 1), (0, 1), (0, 1), (0, len(APPLY_POINTS) - 1e-6)]
    if args.tune_matrix == 'full':
        bounds += [(0, 1)] * 16
    elif args.tune_matrix == 'diag':
        bounds += [(0, 1)] * 4
    if greedy:
        bounds += [(0, 1)] * 4
    x0 = x0_from(init_params, args.tune_matrix, greedy)

    # --- reduced-dim search: pin frozen groups at their init positions ---
    def _pin_list(group):
        base_end = n_dims(args.tune_matrix, False)
        if group == 'baseline':
            return [0, 1, 2]
        if group == 'smooth':
            return [3, 4, 5]
        if group == 'matrix':
            return [10] + list(range(11, base_end))  # apply point + matrix entries
        if group == 'greedy':
            return list(range(base_end, base_end + (4 if greedy else 0)))
        if group == 'all':
            idx = [0, 1, 2, 3, 4, 5, 10] + list(range(11, base_end))
            idx += list(range(base_end, base_end + (4 if greedy else 0)))
            return sorted({i for i in idx if i < D})
        return []

    pinned = set()
    for g in ('baseline', 'smooth', 'matrix', 'greedy'):
        if args.freeze in (g, 'all'):
            pinned |= {i for i in _pin_list(g) if 0 <= i < D}
    for i in pinned:
        lo_i, hi_i = bounds[i]
        v = float(min(max(x0[i], lo_i), hi_i))
        bounds[i] = (v - 1e-9, v + 1e-9)
    if args.pin_ap:
        idx = APPLY_POINTS.index(args.pin_ap)
        bounds[10] = (float(idx), float(idx) + 1e-9)
    print(f'dims={D}, tune_matrix={args.tune_matrix}, greedy_knobs={greedy}, '
          f'robust={robust}, freeze={args.freeze} '
          f'({D - len(pinned)} free / {len(pinned)} pinned dims)')

    os.makedirs(args.outdir, exist_ok=True)
    summary = []
    for wi, (s0, e0) in enumerate(windows, start=1):
        if args.win and wi != args.win:
            print(f'skipping window {wi} (--win {args.win})')
            continue
        esdwin = esd_window(esd_seq, esd_pp, s0, e0)
        target, tgt_rev, tgt_coords = anchored_m13_window_target(esdwin, m13_ref)
        region = (max(0, s0), min(len(raw), e0))
        ctx = (raw, region, target, args.method, args.tune_matrix, greedy, robust, args.pin_ap)
        t0 = time.time()
        print(f'\n--- window {wi}/{len(windows)} [{s0},{e0}] '
              f'(m13 target {len(target)} bp, esd win {len(esdwin)} bp) ---')
        res = differential_evolution(
            _objective, bounds, maxiter=args.maxiter, popsize=args.popsize,
            seed=args.seed + wi, workers=args.workers, polish=False, tol=0.0,
            mutation=(0.5, 1.5), recombination=0.7, x0=x0,
            updating='deferred' if args.workers != 1 else 'immediate',
            args=(ctx,))
        best = decode(res.x, args.tune_matrix, greedy)
        seq = call_window(raw, best, region, args.method)
        m13m, m13aln = _global_score(seq, target)
        esdm, esdaln = _global_score(seq, esdwin)
        seq0 = call_window(raw, init_params, region, args.method)
        m13m0, m13aln0 = _global_score(seq0, target)
        id13 = m13m / m13aln if m13aln else 0.0
        id13_0 = m13m0 / m13aln0 if m13aln0 else 0.0
        ide = esdm / esdaln if esdaln else 0.0
        dt = time.time() - t0
        print(f'  INIT : matches={m13m0} aln={m13aln0} id={100*id13_0:.1f}%  len={len(seq0)}')
        print(f'  BEST : matches={m13m} aln={m13aln} id={100*id13:.1f}%  len={len(seq)} '
              f'in {dt:.0f}s | {best["baseline_method"]}/{best["smooth_method"]} '
              f'apply={best["matrix_apply_point"]} d={best["min_distance"]:.1f} '
              f'prom={best["prominence_frac"]:.2f} norm={best["norm_window"]:.0f} '
              f'shifts={[int(s) for s in best["mobility_shifts"]]}')
        print(f'  ESD id={100*ide:.1f}% vs the analyzer window ({esdm}/{esdaln})')
        mis = mismatch_list(seq, target)
        if mis:
            print('  M13 mismatches (call_pos: call->target):')
            for pi, x, y in mis:
                print(f'    {pi}: {x}->{y}')
        out = {
            'well': args.well, 'region_start': int(s0), 'region_stop': int(e0),
            'baseline_method': best['baseline_method'],
            'baseline_window': int(best['baseline_window']),
            'baseline_window2': int(best.get('baseline_window2') or 0),
            'smooth_method': best['smooth_method'],
            'smooth_window': int(best['smooth_window']),
            'smooth_order': int(best['smooth_order']),
            'matrix_apply_point': best['matrix_apply_point'],
            'mobility_shifts': [int(s) for s in best['mobility_shifts']],
            'matrix': np.asarray(best['matrix']).tolist(),
            'esd_offset': 2008, 'esd_variant': 'Cp312', 'basecall_method': 0,
            'min_distance': float(best['min_distance']),
            'prominence_frac': float(best['prominence_frac']),
            'norm_window': int(best['norm_window']),
            'min_distance_floor': float(best.get('min_distance_floor', 1)),
            'fill_gap': init.get('fill_gap', 4), 'fill_margin': init.get('fill_margin', 0.2),
            'fill_in': True, 'band_low': 0, 'band_high': 0, 'band_order': 2,
            'm13_matches': int(m13m), 'm13_aln': int(m13aln),
            'm13_ident_pct': round(100 * id13, 2),
            'm13_ref': os.path.splitext(os.path.basename(args.ref))[0],
            'esd_matches': int(esdm), 'esd_aln': int(esdaln),
            'esd_ident_pct': round(100 * ide, 2),
            'optimized_score': float(m13m),
            'pinned_ap': args.pin_ap,
            'freeze': args.freeze, 'init_json': os.path.basename(init_path),
        }
        fn = os.path.join(args.outdir, f'{args.well}_[{s0}_{e0}].json')
        with open(fn, 'w') as f:
            json.dump(out, f, indent=2)
        summary.append((s0, e0, m13m0, id13_0, m13m, id13, ide, fn))
        print(f'  saved {fn}')

    print('\n=== summary (init vs optimized, vs M13 target) ===')
    print(f'{"window":18s} {"initM":>5s} {"initId%":>7s} {"bestM":>5s} {"bestId%":>7s} {"esdId%":>7s}')
    for s0, e0, m0, id0, m, idv, ide, fn in summary:
        print(f'[{s0},{e0:5d}]: {m0:5d} {100*id0:7.1f} {m:5d} {100*idv:7.1f} {100*ide:7.1f}')
    if summary:
        t0 = sum(x[2] for x in summary); tb = sum(x[4] for x in summary)
        print(f'\nTOTAL M13 matched: init={t0} optimized={tb}')


if __name__ == '__main__':
    main()
