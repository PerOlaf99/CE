"""Canonical plate metric: perbase_vs_ref vs the clean M13 read-orientation reference.

This is the repository's canonical semi-global seed-SW aligner
(extract_m13_clean_training.load_clean_ref / seed_sw_align / semi_global_sw,
MATCH=2, MISMATCH=-3, GAP=-4), reimplemented here in a vectorized NumPy form that
is bit-identical to the reference DP (validated on MB1000_M13_DT A01). Cimarron
3.12 DLL (ESD) scores 90.72 on this metric for the plate.
"""
import os
import sys
import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from extract_m13_clean_training import load_clean_ref  # noqa: E402

INF = -10 ** 9
MATCH, MIS, GAP = 2, -3, -4

_REF = None


def get_ref():
    global _REF
    if _REF is None:
        _REF = load_clean_ref()
    return _REF


def semi_global_sw_fast(query, ref):
    n, m = len(query), len(ref)
    if n == 0 or m == 0:
        return "", ""
    q = np.frombuffer(query.encode(), dtype=np.uint8)
    r = np.frombuffer(ref.encode(), dtype=np.uint8)
    H = np.zeros((n + 1, m + 1), dtype=np.int64)
    H[1:, 0] = INF
    jj = np.arange(1, m + 1)
    for i in range(1, n + 1):
        sc = np.where(r == q[i - 1], MATCH, MIS)
        diag = H[i - 1, :-1] + sc
        up = H[i - 1, 1:] + GAP
        W = np.maximum(diag, up)
        V = np.empty(m + 1, dtype=np.int64)
        V[0] = 0
        V[1:] = W - GAP * jj
        np.maximum.accumulate(V, out=V)
        H[i, 1:] = V[1:] + GAP * jj
    bj = int(np.argmax(H[n, 1:])) + 1
    i, j = n, bj
    a_, b_ = [], []
    while i > 0:
        if j == 0:
            a_.append(query[i - 1]); b_.append("-"); i -= 1; continue
        cur = H[i, j]
        d = H[i - 1, j - 1] + (MATCH if query[i - 1] == ref[j - 1] else MIS)
        if cur == d and d >= H[i - 1, j] + GAP and d >= H[i, j - 1] + GAP:
            a_.append(query[i - 1]); b_.append(ref[j - 1]); i -= 1; j -= 1
        elif H[i - 1, j] + GAP >= H[i, j - 1] + GAP:
            a_.append(query[i - 1]); b_.append("-"); i -= 1
        else:
            a_.append("-"); b_.append(ref[j - 1]); j -= 1
    al = "".join(reversed(a_)); bl = "".join(reversed(b_))
    i0 = len(bl) - len(bl.lstrip("-"))
    return al[i0:], bl[i0:]


def seed_sw_align_fast(query, ref_rc):
    if len(query) < 60:
        return None
    K = 15
    qset = {query[i:i + K]: i for i in range(len(query) - K + 1)}
    offs = [j - qset[ref_rc[j:j + K]] for j in range(len(ref_rc) - K + 1)
            if ref_rc[j:j + K] in qset]
    if len(offs) < 3:
        return None
    med = int(np.median(offs))
    start = max(0, med - 400)
    win = ref_rc[start:med + 2 * len(query)]
    return semi_global_sw_fast(query, win)


def score(seq, ref=None):
    """Return (percent_identity, n_match, n_del, n_ins, n_sub, n_cols) or None."""
    if ref is None:
        ref = get_ref()
    al = seed_sw_align_fast(seq, ref)
    if al is None:
        return None
    a, b = al
    M = sum(1 for x, y in zip(a, b) if x == y)
    D = sum(1 for x, y in zip(a, b) if x == "-" and y != "-")
    I = sum(1 for x, y in zip(a, b) if y == "-" and x != "-")
    S = sum(1 for x, y in zip(a, b) if x != "-" and y != "-" and x != y)
    return 100.0 * M / max(1, len(a)), M, D, I, S, len(a)


def perbase_vs_ref(seq, ref=None):
    r = score(seq, ref)
    return None if r is None else r[0]
