"""M13mp18 reference sequence for alignment and evaluation."""
import os
import numpy as np

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
    """Smith-Waterman local alignment of query to M13 reference.
    
    Returns dict with alignment info.
    """
    if ref is None:
        ref = M13_REFERENCE
    
    m, n = len(query), len(ref)
    score = np.zeros((m + 1, n + 1), dtype=np.int32)
    
    # Traceback: 0=stop, 1=diag, 2=up, 3=left
    trace = np.zeros((m + 1, n + 1), dtype=np.uint8)
    
    max_score = 0
    max_i, max_j = 0, 0
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            match_score = match if query[i-1] == ref[j-1] else mismatch
            
            diag = score[i-1, j-1] + match_score
            up = score[i-1, j] + (gap_extend if trace[i-1, j] == 2 else gap_open)
            left = score[i, j-1] + (gap_extend if trace[i, j-1] == 3 else gap_open)
            
            scores = [0, diag, up, left]
            best = np.argmax(scores)
            score[i, j] = scores[best]
            trace[i, j] = best
            
            if score[i, j] > max_score:
                max_score = score[i, j]
                max_i, max_j = i, j
    
    # Traceback
    q_aligned, r_aligned = [], []
    i, j = max_i, max_j
    while trace[i, j] != 0 and score[i, j] > 0:
        if trace[i, j] == 1:  # diag
            q_aligned.append(query[i-1])
            r_aligned.append(ref[j-1])
            i -= 1
            j -= 1
        elif trace[i, j] == 2:  # up (gap in ref)
            q_aligned.append(query[i-1])
            r_aligned.append('-')
            i -= 1
        else:  # left (gap in query)
            q_aligned.append('-')
            r_aligned.append(ref[j-1])
            j -= 1
    
    q_aligned = ''.join(reversed(q_aligned))
    r_aligned = ''.join(reversed(r_aligned))
    
    # Compute identity
    matches = sum(1 for a, b in zip(q_aligned, r_aligned) if a == b)
    identity = matches / len(q_aligned) if q_aligned else 0
    
    return {
        'query_start': i,
        'ref_start': j,
        'query_end': max_i,
        'ref_end': max_j,
        'aligned_length': len(q_aligned),
        'matches': matches,
        'identity': identity,
        'query_aligned': q_aligned,
        'ref_aligned': r_aligned,
        'score': max_score,
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
