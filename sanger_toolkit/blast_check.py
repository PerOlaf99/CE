#!/usr/bin/env python3
"""blast_check.py - BLAST-based quality eval for the M13 caller.

The real-world benchmark for this project is NOT the internal ESD comparison
but whether the called sequence aligns to the M13 reference in a single clean
HSP (like the commercial Cimarron 3.12 DLL does: A01 = 95.39% id, 95% coverage).

Requires NCBI blast+ (`blastn` + `makeblastdb` on PATH) and an M13 reference.
"""
import os, sys, subprocess, tempfile

REF = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'refs', 'm13_M77815.1.fa')

def _ref2fa():
    seq = ''.join(l.strip() for l in open(REF) if not l.startswith('>'))
    return '>M13mp18\n' + seq + '\n'

def blast_eval(sequence, task='megablast'):
    """Run real blastn(sequence vs M13) and return the best HSP metrics.

    Returns None if no alignment, else dict with qlen, qstart, qend, coverage,
    pident, bitscore, evalue, aligned, mismatch, gaps.""" 
    seq = ''.join(c for c in sequence if c in 'ACGT')
    if len(seq) < 30:
        return None
    with tempfile.TemporaryDirectory() as td:
        m13 = os.path.join(td, 'm13.fa')
        with open(m13, 'w') as f:
            f.write(_ref2fa())
        q = os.path.join(td, 'q.fa')
        with open(q, 'w') as f:
            f.write('>q\n' + seq + '\n')
        subprocess.run(['makeblastdb', '-in', m13, '-dbtype', 'nucl', '-out',
                        os.path.join(td, 'm13db')], check=True, capture_output=True)
        out = os.path.join(td, 'o.txt')
        subprocess.run(['blastn', '-db', os.path.join(td, 'm13db'), '-query', q,
                        '-task', task, '-outfmt',
                        '6 qlen qstart qend pident bitscore evalue length mismatch gapopen',
                        '-out', out], check=True, capture_output=True)
        rows = [l.split('\t') for l in open(out) if l.strip()]
        if not rows:
            return None
        # pick best by bitscore
        r = max(rows, key=lambda x: float(x[4]))
        qlen, qstart, qend, pident, bitscore, evalue, ln, mm, gaps = (
            int(r[0]), int(r[1]), int(r[2]), float(r[3]), float(r[4]),
            float(r[5]), int(r[6]), int(r[7]), int(r[8]))
        return {
            'qlen': qlen, 'qstart': qstart, 'qend': qend,
            'coverage': 100.0 * (qend - qstart + 1) / qlen,
            'pident': pident, 'bitscore': bitscore, 'evalue': evalue,
            'aligned': ln, 'mismatch': mm, 'gaps': gaps,
        }


if __name__ == '__main__':
    fasta = sys.argv[1] if len(sys.argv) > 1 else '/dev/stdin'
    seq = ''.join(l.strip() for l in open(fasta) if not l.startswith('>'))
    for task in ('megablast', 'blastn'):
        r = blast_eval(seq, task)
        if r:
            print(f'[{task}] ' + ', '.join(f'{k}={v:.2f}' if isinstance(v, float)
                                            else f'{k}={v}' for k, v in r.items()))
        else:
            print(f'[{task}] NO ALIGNMENT')
