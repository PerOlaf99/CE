#!/usr/bin/env python3
"""reproduce_dll.py - 96-well "do we reproduce Cimarron 3.12's own numbers?"
End-to-end BLAST of the closest full-DLL-algorithm Python port vs the DLL-ESD
read, per well: bases called, HSP coverage, %identity, and position-recall of
the DLL's called peaks.

Path A (dll-port):  cache_sep lanes -> ported envelope detector (FUN_1002511d+
  FUN_10024f29, dll_peakdet with 0.05 env floor + region window) -> CNN labels.
Path B (refined):   our production engine + refine (tail 0.70->0.85).
Both BLASTed vs M13 mp18 with the same blastn/megablast as the DLL-ESD.
"""
import os, sys, csv, math, tempfile, subprocess, multiprocessing as mp
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
os.environ['OMP_NUM_THREADS'] = '1'; os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'; os.environ['NUMEXPR_NUM_THREADS'] = '1'
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(HERE, 're_artifacts'))
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))

GT_DIR = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
PLATE = os.path.join(ROOT, 'MB1000_M13_DT')
SEP = os.path.join(ROOT, 'cache_sep')
REF = os.path.join(ROOT, 'sanger_toolkit', 'refs', 'm13_M77815.1.fa')
WELLS = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]
MODELS = None


def ref_seq():
    return ''.join(l.strip() for l in open(REF) if not l.startswith('>'))


def _init():
    global MODELS
    import perfect_basecaller as pb
    MODELS = pb.load_ensemble([os.path.join(HERE, 'base_caller_model*.keras')])


def blast_seq(seq):
    clean = ''.join(c for c in seq if c in 'ACGT')
    if len(clean) < 30:
        return None
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, 'm13.fa'), 'w') as f:
            f.write('>M13mp18\n' + ref_seq() + '\n')
        with open(os.path.join(td, 'q.fa'), 'w') as f:
            f.write('>q\n' + clean + '\n')
        subprocess.run(['makeblastdb', '-in', os.path.join(td, 'm13.fa'),
                        '-dbtype', 'nucl', '-out', os.path.join(td, 'db')],
                       check=True, capture_output=True)
        out = os.path.join(td, 'o.txt')
        subprocess.run(['blastn', '-db', os.path.join(td, 'db'),
                        '-query', os.path.join(td, 'q.fa'), '-task', 'megablast',
                        '-outfmt', '6 qlen qstart qend length pident mismatch gapopen bitscore',
                        '-out', out], check=True, capture_output=True)
        rows = [l.split('\t') for l in open(out) if l.strip()]
        if not rows:
            return None
        r = max(rows, key=lambda x: float(x[7]))
        qlen, qs, qe, ln, pident, mm, gap = (
            int(r[0]), int(r[1]), int(r[2]), int(r[3]), float(r[4]),
            int(r[5]), int(r[6]))
        matched = ln - mm - gap
        return dict(bases=qlen, matched=matched, mm=mm, gap=gap,
                    full_ident=100.0 * matched / qlen,
                    pident=pident, hsp_cov=100.0 * (qe - qs + 1) / qlen)


def port_read(well):
    """Path A: ported envelope detector (separated lanes) + CNN labels
    at the kept positions (CNN evaluated on the RAW 4-dye trace, which is
    what the ensemble was trained on)."""
    import numpy as np
    import perfect_basecaller as pb
    import cimarrontv as cim
    import dll_peakdet as dp
    lanes = np.load(os.path.join(SEP, well + '.npy'))
    pos, seq, inten = dp.dll_peaks(lanes)
    if len(pos) == 0:
        return np.array([], np.int64), ''
    ch, sc = cim.read_rsd(os.path.join(PLATE, well + '.rsd'))
    chw = np.asarray(ch.T, dtype=np.float64)
    probs = pb.cnn_probs(MODELS, chw, pos)
    pred = probs.argmax(1)
    return pos, ''.join(pb.LABELS[i] for i in pred)


def refined_read(well):
    import numpy as np
    import perfect_basecaller as pb
    import cimarrontv as cim
    from perfect_basecaller import refine_denovo_v2
    rsd = os.path.join(PLATE, well + '.rsd')
    ch, sc = cim.read_rsd(rsd)
    chw = ch.T.astype(np.float64)
    eng = pb.build_engine(); res = eng.call(ch, sc)
    pos = np.int64([int(round(p.time)) for p in res.peaks])
    probs = pb.cnn_probs(MODELS, chw, pos)
    pred = probs.argmax(1)
    seq0 = ''.join(pb.LABELS[i] for i in pred)
    conf = [pb.phred(probs[k, i]) for k, i in enumerate(pred)]
    s, _, _ = refine_denovo_v2(MODELS, chw, list(seq0), list(conf), pos,
                               drop_p_hi=0.70, drop_p_lo=0.85, add_p=0.60)
    return s


def _work(well):
    import numpy as np
    import extract_training_data as etd
    esd = os.path.join(GT_DIR, well + '.esd')
    if not (os.path.isfile(os.path.join(SEP, well + '.npy')) and os.path.isfile(esd)):
        return None
    d = etd.parse_esd(esd)
    dll = blast_seq(d['sequence'])
    final = np.array(d['peak_positions'], np.int64)
    ppos, pseq = port_read(well)
    port = blast_seq(pseq)
    # position recall of port peaks vs DLL called peaks (pass-2, tol 6)
    if len(ppos):
        rec = np.mean(np.min(np.abs(final[None, :] - ppos[:, None]), axis=1) <= 6) * 100
    else:
        rec = float('nan')
    ref = blast_seq(refined_read(well))
    return dict(well=well, dll=dll, port=port, ref=ref, recall=rec,
                nppos=len(ppos))


def main():
    import numpy as np
    out = os.path.join(HERE, 'reproduce_dll_rows.csv')
    ctx = mp.get_context('spawn')
    rows = []
    with ctx.Pool(2, initializer=_init) as pool:
        for row in pool.imap_unordered(_work, WELLS):
            if row is None:
                continue
            rows.append(row)
            w = row['well']
            def fm(r):
                return (f"b={r['bases']:4d} cov={r['hsp_cov']:5.1f} "
                        f"id={r['pident']:5.2f} fi={r['full_ident']:5.2f}") if r else 'NO'
            print(f"{w:5s} rec={row['recall']:5.1f}% DLL[{fm(row['dll'])}] "
                  f"PORT[{fm(row['port'])}] REF[{fm(row['ref'])}]", flush=True)
    with open(out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['well', 'recall', 'dll_b', 'dll_cov', 'dll_id', 'dll_fi',
                    'port_b', 'port_cov', 'port_id', 'port_fi',
                    'ref_b', 'ref_cov', 'ref_id', 'ref_fi'])
        for r in rows:
            def g(x, k):
                return (x[k] if x else '')
            w.writerow([r['well'], f"{r['recall']:.1f}",
                        g(r['dll'], 'bases'), g(r['dll'], 'hsp_cov'), g(r['dll'], 'pident'), g(r['dll'], 'full_ident'),
                        g(r['port'], 'bases'), g(r['port'], 'hsp_cov'), g(r['port'], 'pident'), g(r['port'], 'full_ident'),
                        g(r['ref'], 'bases'), g(r['ref'], 'hsp_cov'), g(r['ref'], 'pident'), g(r['ref'], 'full_ident')])
    def mean(k, f):
        v = [f(r[k]) for r in rows]
        v = [x for x in v if x is not None]
        return np.mean(v) if v else float('nan')
    n = len(rows)
    print(f"\n=== {n} wells: reproducing Cimarron 3.12's read (same BLAST pipeline) ===")
    print(f"  DLL-ESD : bases={mean('dll', lambda r: r['bases']):6.1f} "
          f"cov={mean('dll', lambda r: r['hsp_cov']):5.2f} "
          f"id={mean('dll', lambda r: r['pident']):5.2f} "
          f"full_ident={mean('dll', lambda r: r['full_ident']):5.2f}")
    print(f"  PORT    : bases={mean('port', lambda r: r['bases']):6.1f} "
          f"cov={mean('port', lambda r: r['hsp_cov']):5.2f} "
          f"id={mean('port', lambda r: r['pident']):5.2f} "
          f"full_ident={mean('port', lambda r: r['full_ident']):5.2f}  "
          f"recall={np.mean([r['recall'] for r in rows]):.1f}%")
    print(f"  REFINED : bases={mean('ref', lambda r: r['bases']):6.1f} "
          f"cov={mean('ref', lambda r: r['hsp_cov']):5.2f} "
          f"id={mean('ref', lambda r: r['pident']):5.2f} "
          f"full_ident={mean('ref', lambda r: r['full_ident']):5.2f}")


if __name__ == '__main__':
    main()