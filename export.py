"""Sequence export: FASTA and FASTQ with quality scores.

Standard Sanger sequencing output formats.
"""
import os
import numpy as np


def write_fasta(path, header, sequence, line_width=80):
    """Write a single FASTA record."""
    with open(path, 'w') as f:
        f.write(f'>{header}\n')
        for i in range(0, len(sequence), line_width):
            f.write(sequence[i:i + line_width] + '\n')


def write_fasta_multi(path, records, line_width=80):
    """Write multiple FASTA records.  records = [(header, sequence), ...]"""
    with open(path, 'w') as f:
        for header, sequence in records:
            f.write(f'>{header}\n')
            for i in range(0, len(sequence), line_width):
                f.write(sequence[i:i + line_width] + '\n')


def _phred_to_ascii(phred_scores, offset=33):
    """Convert Phred integer scores to FASTQ ASCII encoding.

    offset=33 is standard Sanger/Illumina 1.8+ encoding.
    Q_char = chr(Q + offset), clamped to printable range.
    """
    q = np.asarray(phred_scores, dtype=np.int32)
    q = np.clip(q, 0, 93)
    return ''.join(chr(int(v) + offset) for v in q)


def write_fastq(path, header, sequence, phred_scores, description=''):
    """Write a single FASTQ record.

    header:    sequence identifier (without @)
    sequence:  base string
    phred_scores: array of int Phred Q-scores
    description: optional text after the header on line 1
    """
    h = f'@{header}'
    if description:
        h += f' {description}'
    qual_str = _phred_to_ascii(phred_scores)
    with open(path, 'w') as f:
        f.write(f'{h}\n{sequence}\n+\n{qual_str}\n')


def write_fastq_multi(path, records):
    """Write multiple FASTQ records.  records = [(header, seq, quals), ...]"""
    with open(path, 'w') as f:
        for header, sequence, phred_scores in records:
            h = f'@{header}'
            qual_str = _phred_to_ascii(phred_scores)
            f.write(f'{h}\n{sequence}\n+\n{qual_str}\n')


def write_fastq_append(path, header, sequence, phred_scores, description=''):
    """Append a FASTQ record to an existing file."""
    h = f'@{header}'
    if description:
        h += f' {description}'
    qual_str = _phred_to_ascii(phred_scores)
    with open(path, 'a') as f:
        f.write(f'{h}\n{sequence}\n+\n{qual_str}\n')


def write_phred_table(path, positions, bases, phred_scores):
    """Write a per-position quality table (tab-separated).
    Useful for inspection / downstream tools that don't read FASTQ."""
    with open(path, 'w') as f:
        f.write('position\tbase\tphred\tquality_char\n')
        for pos, base, q in zip(positions, bases, phred_scores):
            qc = chr(int(q) + 33) if 0 <= q <= 93 else '?'
            f.write(f'{pos}\t{base}\t{q}\t{qc}\n')
