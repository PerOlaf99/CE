"""M13mp18 reference sequence for alignment and evaluation."""
import os
import numpy as np
import edlib

M13_REFERENCE = (
    "tgccaagcttgcatgcctgcaggtcgactctagaggatccccgggtaccgagctcgaattcgta"
    "atcatggtcatagctgtttcctgtgtgaaattgttatccgctcacaattccacacaacatacgag"
    "ccggaagcataaagtgtaaagcctggggtgcctaatgagtgagctaactcacattaattgcgttg"
    "cgctcactgcccgctttccagtcgggaaacctgtcgtgccagctgcattaatgaatcggccaacg"
    "cgcggggagaggcggtttgcgtattgggcgccagggtggtttttcttttcaccagcgagacgggc"
    "aacagctgattgcccttcaccgcctggccctgagagagttgcagcaagcggtccacgctggtttg"
    "ccccagcaggcgaaaatcctgtttgatggtggttccgaaatcggcaaaatcccttataaatcaaa"
    "agaatagcccgagatagggttgagtgttgttccagtttggaacaagagtccactattaaagaacg"
    "tggactccaacgtcaaagggcgaaaaaccgtctatcagggcgatggcccactacgtgaaccatca"
    "cccaaatcaagttttttggggtcgaggtgccgtaaagcactaaatcggaaccctaaagggagccc"
    "ccgatttagagcttgacggggaaagccggcgaacgtggcgagaaaggaagggaagaaagcgaaag"
    "gagcgggcgctagggcgctggcaagtgtagcggtcacgctgcgcgtaaccaccacacccgccgcg"
    "cttaatgcgccgctacagggcgcgtactatggttgctttgac"
).upper()


def save_reference(dir_path):
    path = os.path.join(dir_path, 'm13_reference.txt')
    with open(path, 'w') as f:
        f.write(M13_REFERENCE)
    print(f"Saved M13 reference ({len(M13_REFERENCE)} bp) to {path}")


import re


def align_to_reference(query, ref=None, gap_open=-10, gap_extend=-1, match=2, mismatch=-3):
    """Local alignment to M13 reference using edlib (fast, unit-cost edit distance).

    Uses edlib HW mode to find the best infix match, then parses the CIGAR
    to produce alignment strings.  ~1000x faster than pure-Python SW.

    Returns dict with alignment info.
    """
    if ref is None:
        ref = M13_REFERENCE

    query_clean = ''.join(c for c in query if c in 'ACGT')
    if len(query_clean) < 10:
        return _empty_alignment()

    result = edlib.align(query_clean, ref, mode='HW', task='path')

    if result['editDistance'] is None or result['cigar'] is None:
        return _empty_alignment()

    locations = result['locations'][0]
    ref_start = locations[0]
    ref_end = locations[1]
    cigar = result['cigar']

    # Parse CIGAR: alternating numbers and operations
    parts = re.findall(r'\d+|[MIDNSHP=X]', cigar)

    q_aligned_parts = []
    r_aligned_parts = []
    q_pos = 0
    r_pos = ref_start

    for k in range(0, len(parts), 2):
        length = int(parts[k])
        op = parts[k + 1]
        if op in ('=', 'M', 'X'):
            q_seg = query_clean[q_pos:q_pos + length]
            r_seg = ref[r_pos:r_pos + length]
            q_aligned_parts.append(q_seg)
            r_aligned_parts.append(r_seg)
            q_pos += length
            r_pos += length
        elif op == 'I':
            q_aligned_parts.append(query_clean[q_pos:q_pos + length])
            r_aligned_parts.append('-' * length)
            q_pos += length
        elif op == 'D':
            q_aligned_parts.append('-' * length)
            r_aligned_parts.append(ref[r_pos:r_pos + length])
            r_pos += length

    q_aligned = ''.join(q_aligned_parts)
    r_aligned = ''.join(r_aligned_parts)

    matches = sum(1 for a, b in zip(q_aligned, r_aligned) if a == b)
    identity = matches / len(q_aligned) if q_aligned else 0

    return {
        'query_start': 0,
        'ref_start': ref_start,
        'query_end': q_pos,
        'ref_end': ref_end,
        'aligned_length': len(q_aligned),
        'matches': matches,
        'mismatches': len(q_aligned) - matches,
        'identity': identity,
        'query_aligned': q_aligned,
        'ref_aligned': r_aligned,
        'score': -result['editDistance'],
    }


def _empty_alignment():
    return {'query_start': 0, 'ref_start': 0, 'query_end': 0, 'ref_end': 0,
            'aligned_length': 0, 'matches': 0, 'mismatches': 0, 'identity': 0.0,
            'query_aligned': '', 'ref_aligned': '', 'score': 0}


def print_alignment(align, width=80):
    """Pretty-print alignment."""
    q = align['query_aligned']
    r = align['ref_aligned']
    match_str = ''.join('|' if a == b else ' ' for a, b in zip(q, r))
    
    print(f"Reference: {align['ref_start']}-{align['ref_end']} "
          f"({len(M13_REFERENCE)} bp)")
    print(f"Query:     {align['query_start']}-{align['query_end']} "
          f"(align len={align['aligned_length']})")
    print(f"Identity:  {align['identity']:.4f} ({align['matches']}/{align['aligned_length']})")
    print(f"Score:     {align['score']}")
    print()
    
    for block in range(0, len(q), width):
        end = block + width
        print(f"Query:  {q[block:end]}")
        print(f"        {match_str[block:end]}")
        print(f"Ref:    {r[block:end]}")
        print()


if __name__ == '__main__':
    # Test with a simple example
    save_reference('.')
    
    # Quick test alignment
    query = "TGCCAAGCTTGCATGCCTGCAGGTCGACTCTAGAGGATCCCCGGGTACCGAGCTCGAATTCGTAATCATGGTCAT"
    result = align_to_reference(query)
    print_alignment(result)
