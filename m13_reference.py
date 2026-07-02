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
    """Smith-Waterman local alignment of query to M13 reference using edlib.
    
    Returns dict with alignment info.
    """
    if ref is None:
        ref = M13_REFERENCE
    
    # Use edlib for fast alignment
    # edlib uses NW/SW: task='path' gives CIGAR
    # Set mode='NW' for global, 'HW' for infix, 'SH' for prefix/suffix
    query_clean = ''.join(c for c in query if c in 'ACGT')
    
    result = edlib.align(query_clean, ref, mode='HW', task='path')
    
    if result['editDistance'] is None or result['locations'] is None:
        return {
            'query_start': 0, 'ref_start': 0,
            'query_end': 0, 'ref_end': 0,
            'aligned_length': 0, 'matches': 0,
            'identity': 0.0,
            'query_aligned': '', 'ref_aligned': '',
            'score': 0,
        }
    
    # Get alignment details from CIGAR-like format
    locations = result['locations'][0]
    ref_start = locations[0]
    ref_end = locations[1]
    
    # Build aligned sequences from edlib result
    # edlib gives us the CIGAR string - decode it
    cigar = result['cigar']
    
    q_aligned_parts = []
    r_aligned_parts = []
    q_pos = 0
    r_pos = ref_start
    
    # Parse CIGAR: each entry is (length, type) where type is
    # 0=match, 1=insertion, 2=deletion
    cig_types = []
    cig_lengths = []
    
    i = 0
    while i < len(cigar):
        # Each element is a tuple (length, type)
        length, typ = cigar[i]
        if typ == 0:  # match/mismatch
            q_aligned_parts.append(query_clean[q_pos:q_pos + length])
            r_aligned_parts.append(ref[r_pos:r_pos + length])
            q_pos += length
            r_pos += length
        elif typ == 1:  # insertion (gap in ref)
            q_aligned_parts.append(query_clean[q_pos:q_pos + length])
            r_aligned_parts.append('-' * length)
            q_pos += length
        else:  # deletion (gap in query)
            q_aligned_parts.append('-' * length)
            r_aligned_parts.append(ref[r_pos:r_pos + length])
            r_pos += length
        i += 1
    
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
        'identity': identity,
        'query_aligned': q_aligned,
        'ref_aligned': r_aligned,
        'score': -result['editDistance'],
    }


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
