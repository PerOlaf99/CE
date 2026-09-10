"""simple_align compatibility module.

The GUI (sequencing_gui_V15.py) and several scripts import
`from simple_align import M13_REFERENCE` / `align_to_m13`.  This root module
re-exports the canonical 821 bp M13 amplicon reference from m13_reference.py
so those imports work from the project root.

Note: the self-contained sanger_toolkit/simple_align.py carries an 820 bp
copy that differs by one base at position 141 (extra 'A'); the 821 bp
reference here is the one used by the plate-wide ML run.
"""
import numpy as np

from m13_reference import M13_REFERENCE, align_to_reference  # noqa: F401


def align_to_m13(query, ref=None):
    """Needleman-Wunsch global alignment of query to the M13 reference.

    Matches the final helper in sanger_toolkit/simple_align.py so archived
    scripts keep working against the root reference.
    """
    if ref is None:
        ref = M13_REFERENCE
    q = ''.join(c for c in query if c in 'ACGT')
    if len(q) < 20:
        return None
    m, n = len(q), len(ref)
    dp = np.zeros((m + 1, n + 1), dtype=np.int32)
    dp[:, 0] = np.arange(m + 1) * -2
    dp[0, :] = np.arange(n + 1) * -2
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            diag = dp[i - 1, j - 1] + (1 if q[i - 1] == ref[j - 1] else -1)
            dp[i, j] = max(diag, dp[i - 1, j] - 2, dp[i, j - 1] - 2)
    i, j = m, n
    matches = 0
    alen = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + (
                1 if q[i - 1] == ref[j - 1] else -1):
            matches += q[i - 1] == ref[j - 1]
            alen += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i, j] == dp[i - 1, j] - 2:
            alen += 1
            i -= 1
        else:
            alen += 1
            j -= 1
    return {
        'matches': int(matches),
        'alignment_length': alen,
        'score': int(dp[m, n]),
        'identity': 100.0 * matches / alen if alen else 0.0,
        'query_length': len(q),
        'ref_length': len(ref),
    }