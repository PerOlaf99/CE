"""Simple M13 alignment without edlib."""
import re, difflib

M13_REFERENCE = (
    "TGCCAAGCTTGCA" + 
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


def align_to_m13(query):
    """Simple alignment of query to M13 reference.
    Uses longest contiguous match, then extends.
    """
    q = ''.join(c for c in query if c in 'ACGT')
    if len(q) < 20:
        return None

    # Find best match location using longest common substring
    sm = difflib.SequenceMatcher(None, q, M13_REFERENCE, autojunk=False)
    match = sm.find_longest_match(0, len(q), 0, len(M13_REFERENCE))

    if match.size < 20:
        return None

    q_start, ref_start, length = match
    q_matched = q[q_start:q_start + length]
    ref_matched = M13_REFERENCE[ref_start:ref_start + length]

    matches = sum(1 for a, b in zip(q_matched, ref_matched) if a == b)

    return {
        'matches': matches,
        'alignment_length': length,
        'query_start': q_start,
        'ref_start': ref_start,
        'identity': matches / length * 100 if length > 0 else 0,
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
