"""Sequence alignment and reference comparison.

Pure functions extracted from sequencing_gui_V15.py.  No Qt, no widgets.
"""
import numpy as np


# ── Needleman-Wunsch (global) ──────────────────────────────────────────

def pc_nw_identity(query, reference, match=1, mismatch=-1, gap=-2, max_len=6000):
    """Global (Needleman-Wunsch) alignment identity between two base-letter
    strings, in percent."""
    q = query[:max_len]
    r = reference[:max_len]
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0.0
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    dp[:, 0] = np.arange(m + 1) * gap
    dp[0, :] = np.arange(n + 1) * gap
    r_int = np.frombuffer(r.encode('ascii'), dtype=np.uint8).astype(np.int64)
    js = np.arange(1, n + 1, dtype=np.int64)
    gapj = gap * js
    for i in range(1, m + 1):
        qi = ord(q[i - 1])
        prev = dp[i - 1]
        diag = prev[:-1] + np.where(r_int == qi, match, mismatch)
        up = prev[1:] + gap
        pref = np.maximum.accumulate(np.maximum(diag, up) - gapj)
        dp[i, 0] = prev[0] + gap
        dp[i, 1:] = pref + gapj
    i, j = m, n
    matches = 0
    aligned = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + \
                (match if q[i - 1] == r[j - 1] else mismatch):
            aligned += 1
            if q[i - 1] == r[j - 1]:
                matches += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i, j] == dp[i - 1, j] + gap:
            aligned += 1
            i -= 1
        else:
            aligned += 1
            j -= 1
    return 100.0 * matches / aligned if aligned else 0.0


def pc_reference_accuracy(query, reference, match=1, mismatch=-1, gap=-2,
                          max_len=6000):
    """Matched-bases / reference-length accuracy.  Returns
    ``(matched, total_ref, pct)``."""
    q = query[:max_len]
    r = reference[:max_len]
    m, n = len(q), len(r)
    total_ref = n
    if m == 0 or n == 0:
        return 0, total_ref, 0.0
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    dp[:, 0] = np.arange(m + 1) * gap
    dp[0, :] = np.arange(n + 1) * gap
    r_int = np.frombuffer(r.encode('ascii'), dtype=np.uint8).astype(np.int64)
    js = np.arange(1, n + 1, dtype=np.int64)
    gapj = gap * js
    for i in range(1, m + 1):
        qi = ord(q[i - 1])
        prev = dp[i - 1]
        diag = prev[:-1] + np.where(r_int == qi, match, mismatch)
        up = prev[1:] + gap
        pref = np.maximum.accumulate(np.maximum(diag, up) - gapj)
        dp[i, 0] = prev[0] + gap
        dp[i, 1:] = pref + gapj
    i, j = m, n
    matched = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + \
                (match if q[i - 1] == r[j - 1] else mismatch):
            if q[i - 1] == r[j - 1]:
                matched += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i, j] == dp[i - 1, j] + gap:
            i -= 1
        else:
            j -= 1
    pct = 100.0 * matched / total_ref if total_ref else 0.0
    return matched, total_ref, pct


# ── Semi-global alignment (free end gaps) ──────────────────────────────

def _ref_revcomp(seq):
    comp = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G', 'N': 'N'}
    return ''.join(comp.get(b, 'N') for b in seq[::-1])


def ref_semiglobal_identity(query, reference):
    """Free-end-gap Needleman-Wunsch identity against a reference. Terminal
    overhangs are free (not counted as errors).  Returns
    (identity_pct, matches, mismatches, indels)."""
    q, r = query, reference
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0.0, 0, 0, 0
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    tb = np.zeros((m + 1, n + 1), dtype=np.int8)
    for i in range(1, m + 1):
        qi = q[i - 1]
        prev = dp[i - 1]
        row = dp[i]
        tbrow = tb[i]
        for j in range(1, n + 1):
            diag = prev[j - 1] + (1 if qi == r[j - 1] else -1)
            up = prev[j] - 2
            left = row[j - 1] - 2
            if diag >= up and diag >= left:
                row[j], tbrow[j] = diag, 0
            elif up >= left:
                row[j], tbrow[j] = up, 1
            else:
                row[j], tbrow[j] = left, 2
    i, j = m, int(np.argmax(dp[m, :]))
    if dp[i, j] < dp[int(np.argmax(dp[:, n])), n]:
        i, j = int(np.argmax(dp[:, n])), n
    matches = mismatches = indels = 0
    while i > 0 and j > 0:
        d = tb[i, j]
        if d == 0:
            if q[i - 1] == r[j - 1]:
                matches += 1
            else:
                mismatches += 1
            i -= 1
            j -= 1
        elif d == 1:
            indels += 1
            i -= 1
        else:
            indels += 1
            j -= 1
    total = matches + mismatches + indels
    ident = 100.0 * matches / total if total else 0.0
    return ident, matches, mismatches, indels


# ── Local alignment (Smith-Waterman, affine gap) ───────────────────────

def ref_local_identity(query, reference):
    """BLAST-style local (Smith-Waterman, affine-gap) identity against a
    reference slice.

    Returns (identity_pct, matches, mismatches, indels, aligned_len, score,
     ref_start0, ref_end0, read_start0, read_end0, mismatch_list)."""
    q, r = query, reference
    m, n = len(q), len(r)
    if m == 0 or n == 0:
        return 0.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, []
    NEG = -10**9
    match, mismatch, gopen, gext = 2, -3, 11, 2
    Mp = [0] * (n + 1)
    Xp = [NEG] * (n + 1)
    Yp = [NEG] * (n + 1)
    TB, V = [], []
    best = (0, 0, 0)
    for i in range(1, m + 1):
        qi = q[i - 1]
        Mrow = [0] * (n + 1)
        Xrow = [NEG] * (n + 1)
        Yrow = [NEG] * (n + 1)
        trow = [0] * (n + 1)
        vrow = [0] * (n + 1)
        for j in range(1, n + 1):
            base = Mp[j - 1]
            if Xp[j - 1] > base:
                base = Xp[j - 1]
            if Yp[j - 1] > base:
                base = Yp[j - 1]
            Mrow[j] = (base if base > 0 else 0) + \
                (match if qi == r[j - 1] else mismatch)
            xa = Mp[j] - gopen
            xb = Xp[j] - gext
            Xrow[j] = xa if xa > xb else xb
            ya = Mrow[j - 1] - gopen
            yb = Yrow[j - 1] - gext
            Yrow[j] = ya if ya > yb else yb
            v = Mrow[j]
            if Xrow[j] > v:
                v = Xrow[j]
            if Yrow[j] > v:
                v = Yrow[j]
            vrow[j] = v
            trow[j] = 0 if v == Mrow[j] else (1 if v == Xrow[j] else 2)
            if v > best[0]:
                best = (v, i, j)
        TB.append(trow)
        V.append(vrow)
        Mp, Xp, Yp = Mrow, Xrow, Yrow
    _, i, j = best
    matches = mismatches = indels = 0
    mism = []
    ref_hits = []
    read_hits = []
    while i > 0 and j > 0:
        v = V[i - 1][j]
        if v <= 0:
            break
        d = TB[i - 1][j]
        if d == 0:
            qb, rb = q[i - 1], r[j - 1]
            read_hits.append(i - 1)
            ref_hits.append(j - 1)
            if qb == rb:
                matches += 1
            else:
                mismatches += 1
                mism.append((i - 1, qb, rb, j - 1))
            i -= 1
            j -= 1
        elif d == 1:
            indels += 1
            read_hits.append(i - 1)
            i -= 1
        else:
            indels += 1
            ref_hits.append(j - 1)
            j -= 1
    aligned = matches + mismatches + indels
    ident = 100.0 * matches / aligned if aligned else 0.0
    rlo = min(ref_hits) if ref_hits else 0
    rhi = max(ref_hits) if ref_hits else 0
    qlo = min(read_hits) if read_hits else 0
    qhi = max(read_hits) if read_hits else len(q) - 1
    return ident, matches, mismatches, indels, aligned, best[0], \
        rlo, rhi, qlo, qhi, mism
