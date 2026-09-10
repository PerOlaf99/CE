#!/usr/bin/env python3
"""coverage_tune.py - find engine seed config that maximizes BLAST coverage.

Goal: beat Cimarron 3.12 (841 bases / 95% coverage / 95.39% identity).
Our CNN already beats identity (~97%).  We need MORE peaks (bases detected)
and HIGHER coverage.  The seed peak detector (Cimarron engine) is the
bottleneck: it misses ~35 bases that the DLL finds.  This script sweeps
engine knobs and reports BLAST metrics for the CNN re-called sequence.
"""
import os, sys, glob, argparse
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

import perfect_basecaller as pb
from perfect_basecaller import LABELS, phred


def get_seq(well, models, engine_kw, use_cnn=True):
    ch, scans = pb.cim.read_rsd(os.path.join(ROOT, 'MB1000_M13_DT', well + '.rsd'))
    eng = pb.build_engine(**engine_kw)
    res = eng.call(ch, scans)
    ps = [int(round(pk.time)) for pk in res.peaks]
    if not use_cnn:
        seq = ''.join(b for b, pk in zip(res.sequence, res.peaks) if b in LABELS)
        return seq, ps
    chw = np.asarray(ch, dtype=np.float64)
    if chw.ndim == 2 and chw.shape[0] == 4 and chw.shape[0] <= chw.shape[1]:
        chw = chw.T
    if len(ps):
        probs = pb.cnn_probs(models, chw, ps)
        pred = probs.argmax(1)
        seq = ''.join(LABELS[i] for i in pred)
    else:
        seq = ''
    return seq, ps


def blast_metrics(seq):
    import subprocess, tempfile
    clean = ''.join(c for c in seq if c in 'ACGT')
    if len(clean) < 30:
        return None
    seqr = ''.join(l.strip() for l in open(os.path.join(HERE, 'refs', 'm13_M77815.1.fa'))
                   if not l.startswith('>'))
    with tempfile.TemporaryDirectory() as td:
        open(os.path.join(td, 'm13.fa'), 'w').write('>M13\n' + seqr + '\n')
        open(os.path.join(td, 'q.fa'), 'w').write('>q\n' + clean + '\n')
        subprocess.run(['makeblastdb', '-in', os.path.join(td, 'm13.fa'),
                        '-dbtype', 'nucl', '-out', os.path.join(td, 'db')],
                       check=True, capture_output=True)
        out = os.path.join(td, 'o.txt')
        subprocess.run(['blastn', '-db', os.path.join(td, 'db'),
                        '-query', os.path.join(td, 'q.fa'), '-task', 'megablast',
                        '-outfmt', '6 qlen qstart qend sstart send pident bitscore',
                        '-out', out], check=True, capture_output=True)
        rows = [l.split('\t') for l in open(out) if l.strip()]
        if not rows:
            return None
        r = max(rows, key=lambda x: float(x[5]))
        qlen, qstart, qend, sstart, send, pident, bs = (
            int(r[0]), int(r[1]), int(r[2]), int(r[3]), int(r[4]),
            float(r[5]), float(r[6]))
        return dict(bases=qlen, cov=100.0*(qend-qstart+1)/qlen, ident=pident,
                    m13=(min(sstart, send), max(sstart, send)), bs=bs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--well', default='A01')
    ap.add_argument('--models', nargs='*', default=[
        os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct', f) for f in [
            'base_caller_model_v4_clean.keras']])
    args = ap.parse_args()
    models = pb.load_ensemble(args.models)
    if not models:
        print('no models'); return

    def report(name, e):
        seq, ps = get_seq(args.well, models, e)
        m = blast_metrics(seq)
        if m:
            print(f'{name:55s} bases={m["bases"]:4d} cov={m["cov"]:5.1f}% id={m["ident"]:5.2f}% M13={m["m13"][0]}-{m["m13"][1]} ps={len(ps)}')
        else:
            print(f'{name:55s} NO-ALIGN ps={len(ps)}')

    print('baseline perbase / greedy / min_frac defaults:')
    report('DLL goal (839/95.4/95.39)', {})

    # Sweep bgn_end_method
    for bem in ['perbase', 'histogram', 'legacy', 'hybrid']:
        report(f'bgn_end={bem}', dict(bgn_end_method=bem))

    # Sweep greedy_min_frac (lower = more peaks but more noise)
    for gmf in [0.03, 0.02, 0.01, 0.005]:
        report(f'greedy_min_frac={gmf}', dict(greedy_min_frac=gmf))

    # cluster caller with different prominence
    for cpf in [0.026, 0.01, 0.005, 0.002]:
        report(f'cluster prom={cpf}', dict(caller='cluster', cluster_prominence_frac=cpf))


if __name__ == '__main__':
    main()
