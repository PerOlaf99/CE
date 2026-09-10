#!/usr/bin/env python3
"""probe_port2.py - does offset-averaged CNN labeling (PORT2) beat single-window
labeling (PORT) at the SAME port positions?  Probe on a few wells, BLASTed vs
M13 mp18 with the same pipeline as reproduce_dll.py.  Also prints the DLL-ESD
reference per well."""
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
WELLS = sys.argv[1:] if len(sys.argv) > 1 else ['A01', 'B04', 'B05', 'C09', 'D12', 'H11']
OFFSETS = [-4, -2, 0, 2, 4]
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
        qlen, qs, qe, ln, pident, mm, gap = (int(r[0]), int(r[1]), int(r[2]),
                                             int(r[3]), float(r[4]), int(r[5]), int(r[6]))
        matched = ln - mm - gap
        return dict(bases=qlen, matched=matched, mm=mm, gap=gap,
                    full_ident=100.0 * matched / qlen,
                    pident=pident, hsp_cov=100.0 * (qe - qs + 1) / qlen)


def label_at(chw, pos, offsets):
    """Label positions via ensemble; average probs across centering offsets.
    One batched cnn_probs call over (pos x offsets) augmented array."""

    import numpy as np
    import perfect_basecaller as pb
    n_pos = len(pos)
    if n_pos == 0:
        return ''
    n = chw.shape[0]
    qs = []
    for p in pos:
        for o in offsets:
            qs.append(min(max(int(p) + o, 15), n - 16))
    qa = np.asarray(qs, np.int64)
    pr_all = pb.cnn_probs(MODELS, chw, qa)
    pr_all = pr_all.reshape(n_pos, len(offsets), 4)
    pr = pr_all.mean(axis=1)
    return ''.join(pb.LABELS[i] for i in pr.argmax(1))


def _work(well):
    import numpy as np
    import perfect_basecaller as pb
    import cimarrontv as cim
    import dll_peakdet as dp
    import extract_training_data as etd
    esd = os.path.join(GT_DIR, well + '.esd')
    if not (os.path.isfile(os.path.join(SEP, well + '.npy')) and os.path.isfile(esd)):
        return None
    d = etd.parse_esd(esd)
    dll = blast_seq(d['sequence'])
    lanes = np.load(os.path.join(SEP, well + '.npy'))
    pos, _, _ = dp.dll_peaks(lanes)
    ch, sc = cim.read_rsd(os.path.join(PLATE, well + '.rsd'))
    chw = np.asarray(ch.T, dtype=np.float64)
    pros = pb.cnn_probs(MODELS, chw, np.asarray(pos, np.int64))
    pred = pros.argmax(1)
    seq_port = ''.join(pb.LABELS[i] for i in pred)
    seq_p2 = label_at(chw, pos, OFFSETS)
    return dict(well=well, dll=dll,
                port=blast_seq(seq_port), port2=blast_seq(seq_p2),
                npos=len(pos))


def main():
    import numpy as np
    ctx = mp.get_context('spawn')
    rows = []
    with ctx.Pool(2, initializer=_init) as pool:
        for row in pool.imap_unordered(_work, WELLS):
            if row is None:
                continue
            rows.append(row)
            w = row['well']

            def fm(r):
                return (f"b={r['bases']:4d} cov={r['hsp_cov']:5.1f} id={r['pident']:5.2f} "
                        f"fi={r['full_ident']:5.2f}") if r else 'NO'
            print(f"""{w:5s} DLL[{fm(row['dll'])}] PORT[{fm(row['port'])}] P2av[{fm(row['port2'])}]""", flush=True)
    print("\n=== probe: offset-averaged labels at same port positions ===", flush=True)
    for k in ['dll', 'port', 'port2']:
        v = [r[k] for r in rows]
        v = [x for x in v if x]
        if not v:
            continue
        print(f"  {k:6s}: bases={np.mean([r['bases'] for r in v]):6.1f} "
              f"cov={np.mean([r['hsp_cov'] for r in v]):5.2f} "
              f"id={np.mean([r['pident'] for r in v]):5.2f} "
              f"full_ident={np.mean([r['full_ident'] for r in v]):5.2f}", flush=True)


if __name__ == '__main__':
    main()