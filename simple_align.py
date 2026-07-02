"""Simple M13 alignment without edlib."""

M13_REFERENCE = (
    "TGCCAAGCTTGCA"
    "TGCCTGCAGGTCGACTCTAGAGGATCCCCGGGTACCGAGCTCGAATTCGTA"
    "ATCATGGTCATAGCTGTTTCCTGTGTGAAATTGTTATCCGCTCACAATTCCACACAACATACGAG"
    "CCGGAAGCATAAGTGTAAAGCCTGGGGTGCCTAATGAGTGAGCTAACTCACATTAATTGCGTTG"
    "CGCTCACTGCCCGCTTTCCAGTCGGGAAACCTGTCGTGCCAGCTGCATTAATGAATCGGCCAACG"
    "CGCGGGGAGAGGCGGTTTGCGTATTGGGCGCCAGGGTGGTTTTTCTTTTCACCAGCGAGACGGGC"
    "AACAGCTGATTGCCCTTCACCGCCTGGCCCTGAGAGAGTTGCAGCAAGCGGTCCACGCTGGTTTG"
    "CCCCAGCAGGCGAAAATCCTGTTTGATGGTGGTTCCGAAATCGGCAAAATCCCTTATAAATCAAA"
    "AGAATAGCCCGAGATAGGGTTGAGTGTTGTTCCAGTTTGGAACAAGAGTCCACTATTAAAGAACG"
    "TGGACTCCAACGTCAAAGGGCGAAAAACCGTCTATCAGGGCGATGGCCCACTACGTGAACCATCA"
    "CCCAAATCAAGTTTTTTGGGGTCGAGGTGCCGTAAAGCACTAAATCGGAACCCTAAAGGGAGCCC"
    "CCGATTTAGAGCTTGACGGGGAAAGCCGGCGAACGTGGCGAGAAAGGAAGGGAAGAAAGCGAAAG"
    "GAGCGGGCGCTAGGGCGCTGGCAAGTGTAGCGGTCACGCTGCGCGTAACCACCACACCCGCCGCG"
    "CTTAATGCGCCGCTACAGGGCGCGTACTATGGTTGCTTTGAC"
).upper()


def _nw_align(q, r, match=1, mismatch=-1, gap=-2):
    """Needleman-Wunsch global alignment, returns (score, matches, length)."""
    m, n = len(q), len(r)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        dp[i][0] = dp[i - 1][0] + gap
    for j in range(1, n + 1):
        dp[0][j] = dp[0][j - 1] + gap
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            diag = dp[i - 1][j - 1] + (match if q[i - 1] == r[j - 1] else mismatch)
            up = dp[i - 1][j] + gap
            left = dp[i][j - 1] + gap
            dp[i][j] = max(diag, up, left)
    # Traceback
    i, j = m, n
    matches = 0
    alen = 0
    while i > 0 or j > 0:
        if i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + (match if q[i - 1] == r[j - 1] else mismatch):
            if q[i - 1] == r[j - 1]:
                matches += 1
            alen += 1
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + gap:
            alen += 1
            i -= 1
        else:
            alen += 1
            j -= 1
    return dp[m][n], matches, alen


def align_to_m13(query, ref=None):
    """Needleman-Wunsch global alignment of query to M13 reference."""
    if ref is None:
        ref = M13_REFERENCE
    q = ''.join(c for c in query if c in 'ACGT')
    if len(q) < 20:
        return None
    score, matches, alen = _nw_align(q, ref)
    return {
        'matches': matches,
        'alignment_length': alen,
        'score': score,
        'identity': matches / alen * 100 if alen > 0 else 0,
        'query_length': len(q),
        'ref_length': len(ref),
    }


def align_sliding(query, ref=None):
    """Sliding window string match - count exact k-mer matches.
    Fast approximation of identity without alignment."""
    if ref is None:
        ref = M13_REFERENCE
    q = ''.join(c for c in query if c in 'ACGT')
    if len(q) < 10:
        return None

    k = 8
    q_kmers = set(q[i:i+k] for i in range(len(q) - k + 1))
    best = 0
    best_pos = 0
    for i in range(len(ref) - len(q)):
        ref_kmers = set(ref[i+j:i+j+k] for j in range(len(q) - k + 1))
        common = len(q_kmers & ref_kmers)
        if common > best:
            best = common
            best_pos = i

    matches = best
    total = len(q) - k + 1
    return {
        'matches': matches,
        'alignment_length': total,
        'identity': matches / total * 100 if total > 0 else 0,
        'ref_position': best_pos,
    }
