#!/usr/bin/env python3
"""blast_v2tail.py - BLAST DLL-ESD vs the new v2-tail-tight caller (same pipeline).

Full-read BLAST metric (from plate_blast._blast_seq):
  qlen        detected ACGT bases
  matched_bp  aligned_len - mismatch - gapopen   (bases that match M13)
  full_ident  matched_bp / qlen  (true identity over ALL detected bases)
  pident      matched/aligned within HSP
  hsp_cov     fraction of the read inside the best HSP
"""
import os, sys, csv, tempfile, subprocess, multiprocessing as mp
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
os.environ['OMP_NUM_THREADS'] = '1'; os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'; os.environ['NUMEXPR_NUM_THREADS'] = '1'
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))

REF = os.path.join(ROOT, 'sanger_toolkit', 'refs', 'm13_M77815.1.fa')
GT_DIR = os.path.join(ROOT, 'MB1000_M13_DT', 'MB1000_M13_DT_Cp312_MD1')
PLATE = os.path.join(ROOT, 'MB1000_M13_DT')
WELLS = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]
MODELS = None


def ref_seq():
    return ''.join(l.strip() for l in open(REF) if not l.startswith('>'))


def _init(hi=None, lo=None, add=None):
    global MODELS, DROP_HI, DROP_LO, ADD_P
    if hi is not None:
        DROP_HI = hi
    if lo is not None:
        DROP_LO = lo
    if add is not None:
        ADD_P = add
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
        if qlen <= 0:
            return None
        return dict(bases=qlen, matched=matched,
                    full_ident=100.0 * matched / qlen,
                    pident=pident,
                    hsp_cov=100.0 * (qe - qs + 1) / qlen)


DROP_HI = 0.70
DROP_LO = 0.85
ADD_P = 0.60


def _work(well):
    import numpy as np
    import perfect_basecaller as pb
    import cimarrontv as cim
    from perfect_basecaller import refine_denovo_v2
    rsd = os.path.join(PLATE, well + '.rsd')
    esd = os.path.join(GT_DIR, well + '.esd')
    if not (os.path.isfile(rsd) and os.path.isfile(esd)):
        return None
    import extract_training_data as etd
    d = etd.parse_esd(esd)
    dll = blast_seq(d['sequence'])
    ch, scans = cim.read_rsd(rsd)
    eng = pb.build_engine(); res = eng.call(ch, scans)
    pos = np.int64([int(round(p.time)) for p in res.peaks])
    chw = ch.T.astype(np.float64)
    probs = pb.cnn_probs(MODELS, chw, pos)
    pred = probs.argmax(1)
    seq0 = ''.join(pb.LABELS[i] for i in pred)
    conf0 = np.array([pb.phred(probs[k, i]) for k, i in enumerate(pred)], dtype=np.int32)
    seq, _, _ = refine_denovo_v2(MODELS, chw, list(seq0), list(conf0), pos,
                                 drop_p_hi=DROP_HI, drop_p_lo=DROP_LO, add_p=ADD_P)
    ours = blast_seq(seq)
    return dict(well=well, dll=dll, ours=ours)


def main():
    import numpy as np
    import sys
    argv = list(sys.argv[1:])
    global DROP_HI, DROP_LO, ADD_P
    kv = [a for a in argv if '=' in a and a.split('=')[0] in ('hi', 'lo', 'add')]
    for a in kv:
        k, _, v = a.partition('=')
        if k == 'hi': DROP_HI = float(v)
        if k == 'lo': DROP_LO = float(v)
        if k == 'add': ADD_P = float(v)
    argv = [a for a in argv if a not in kv]
    sel = None
    if '--wells' in argv:
        i = argv.index('--wells')
        sel = [a.upper() for a in argv[i + 1:]]
        argv = argv[:i]
    wells = [w for w in WELLS if (not sel or w in sel)]
    ctx = mp.get_context('spawn')
    results = []
    with ctx.Pool(2, initializer=_init, initargs=(DROP_HI, DROP_LO, ADD_P)) as pool:
        for row in pool.imap_unordered(_work, wells):
            if row is None:
                continue
            results.append(row)
            w = row['well']
            d, o = row['dll'], row['ours']
            def fmt(r):
                return (f"b={r['bases']:4d} m={r['matched']:4d} "
                        f"fi={r['full_ident']:5.2f} pi={r['pident']:5.2f} "
                        f"cov={r['hsp_cov']:5.2f}") if r else 'NO'
            print(f"{w:5s} DLL[{fmt(d)}]  OURS[{fmt(o)}]", flush=True)
    out = os.path.join(HERE, 'blast_v2tail_rows.csv')
    with open(out, 'w', newline='') as f:
        wrow = csv.writer(f)
        wrow.writerow(['well', 'dll_bases', 'dll_match', 'dll_fi', 'dll_pi', 'dll_cov',
                       'ours_bases', 'ours_match', 'ours_fi', 'ours_pi', 'ours_cov'])
        for r in results:
            d, o = r['dll'], r['ours']
            wrow.writerow([r['well']] +
                          ([d['bases'], d['matched'], f"{d['full_ident']:.2f}",
                            f"{d['pident']:.2f}", f"{d['hsp_cov']:.2f}"] if d else [''] * 5) +
                          ([o['bases'], o['matched'], f"{o['full_ident']:.2f}",
                            f"{o['pident']:.2f}", f"{o['hsp_cov']:.2f}"] if o else [''] * 5))
    darr = np.array([[r['dll']['matched'], r['dll']['full_ident']] for r in results if r['dll']], float)
    oarr = np.array([[r['ours']['matched'], r['ours']['full_ident']] for r in results if r['ours']], float)
    n = len(results)
    print(f"\nBLAST FULL-READ METRIC, n={n} wells")
    print(f"  DLL  matched_bp={darr[:,0].mean():6.1f}  full_ident={darr[:,1].mean():5.2f}%"
          f"  (bases {np.mean([r['dll']['bases'] for r in results if r['dll']]):.0f})")
    print(f"  OURS matched_bp={oarr[:,0].mean():6.1f}  full_ident={oarr[:,1].mean():5.2f}%"
          f"  (bases {np.mean([r['ours']['bases'] for r in results if r['ours']]):.0f})")
    db = oarr[:,0].mean() - darr[:,0].mean()
    di = oarr[:,1].mean() - darr[:,1].mean()
    print(f"  delta: matched_bp {db:+.1f}   full_ident {di:+.2f} pts")
    with open(os.path.join(HERE, 'blast_v2tail_final.log'), 'a') as f:
        f.write(f"\n{n} wells: DLL m={darr[:,0].mean():.1f} fi={darr[:,1].mean():.2f} | "
                f"OURS m={oarr[:,0].mean():.1f} fi={oarr[:,1].mean():.2f} "
                f"(dm {db:+.1f}, dfi {di:+.2f})\n")


if __name__ == '__main__':
    main()