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


def align_to_reference(query, ref=None, gap_open=-10, gap_extend=-1, match=2, mismatch=-3):
    """Smith-Waterman local alignment using swalign (affine gaps, fast).

    Returns dict with alignment info.
    """
    if ref is None:
        ref = M13_REFERENCE

    query_clean = ''.join(c for c in query if c in 'ACGT')
    if len(query_clean) < 10:
        return _empty_alignment()

    import swalign
    matrix = swalign.NucleotideScoringMatrix(match=match, mismatch=mismatch)
    sw = swalign.LocalAlignment(matrix, gap_penalty=gap_open,
                                gap_extension_penalty=gap_extend)
    try:
        align = sw.align(query_clean, ref)
    except:
        return _empty_alignment()

    if align.score == 0:
        return _empty_alignment()

    # Build aligned sequences from CIGAR
    cigar = align.cigar
    q_aligned_parts, r_aligned_parts = [], []
    q_pos, r_pos = 0, 0

    for length, op in cigar:
        if op == 'M':
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

    return {
        'query_start': align.q_pos, 'ref_start': align.r_pos,
        'query_end': align.q_end, 'ref_end': align.r_end,
        'aligned_length': len(q_aligned),
        'matches': align.matches,
        'mismatches': align.mismatches,
        'identity': align.identity,
        'query_aligned': q_aligned,
        'ref_aligned': r_aligned,
        'score': align.score,
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
