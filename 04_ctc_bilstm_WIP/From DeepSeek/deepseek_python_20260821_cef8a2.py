from sklearn.metrics import accuracy_score
# alignment of sequences might be needed; we can use global alignment (Bio.pairwise2)

def compare_sequences(pred, truth):
    # Use Needleman-Wunsch alignment to handle indels
    from Bio import pairwise2
    aln = pairwise2.align.globalms(pred, truth, 1, -1, -1, -1)[0]  # simple scoring
    # count matches
    matches = sum(1 for a, b in zip(aln[0], aln[1]) if a == b and a != '-')
    return matches / len(aln[2])  # accuracy over aligned length