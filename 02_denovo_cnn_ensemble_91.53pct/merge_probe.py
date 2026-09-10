#!/usr/bin/env python3
"""merge_probe.py - Option 1 "merge length+identity": call the FULL DLL register
(all envelope rising->falling transitions, CF region ~ bgn..end) with OUR CNN
labels and keep/drop by OUR confidence (refine_denovo_v2 config sweep), BLAST
vs M13 and compare to the DLL-ESD on probe wells.  Goal: bases ~DLL length at
our identity -> matched_bp above the DLL."""
import os, sys, csv, tempfile, subprocess, multiprocessing as mp
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
CONFIGS = [dict(drop_p_hi=0.55, drop_p_lo=0.85, add_p=0.60),
           dict(drop_p_hi=0.50, drop_p_lo=0.70, add_p=0.60),
           dict(drop_p_hi=0.60, drop_p_lo=0.99, add_p=0.60),
           dict(drop_p_hi=0.40, drop_p_lo=0.60, add_p=0.60),
           dict(drop_p_hi=0.35, drop_p_lo=0.50, add_p=0.60)]
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


def transitions(env, start=2):
    n = len(env)
    state = 0
    maxima = []
    prev = float(env[start])
    for c in range(start + 1, n):
        cur = float(env[c])
        if state == 0:
            if cur > prev:
                state = 1
            elif cur < prev:
                state = 2
        elif state == 1:
            if cur < prev:
                state = 2
                maxima.append(c - 1)
        elif state == 2:
            if cur > prev:
                state = 1
        prev = cur
    return maxima


def longest_region(envs, above):
    import numpy as np
    n = len(envs)
    sig = envs > above
    best_lo, best_hi, best_len = 0, -1, 0
    cur_lo, quiet = 0, 0
    for i in range(n):
        if sig[i]:
            quiet = 0
        else:
            quiet += 1
            if quiet > 10:
                hi = i - quiet
                if hi - cur_lo + 1 > best_len:
                    best_len, best_lo, best_hi = hi - cur_lo + 1, cur_lo, hi
                cur_lo = i
    if sig.any() and n - cur_lo > best_len:
        best_lo, best_hi = cur_lo, n - 1
    if best_hi < best_lo:
        return None
    return best_lo, best_hi


def merge_read(well, cfg):
    import numpy as np
    import perfect_basecaller as pb
    import cimarrontv as cim
    import dll_peakdet as dp
    lanes = np.load(os.path.join(SEP, well + '.npy')).astype(np.float64)
    env = dp.env_max(lanes)
    scans = np.array(transitions(env), np.int64)
    envs = env[scans]
    reg = longest_region(envs, 0.05 * env.max())
    if reg is None:
        return ''
    lo, hi = reg
    scans = scans[lo:hi + 1]
    ch, sc = cim.read_rsd(os.path.join(PLATE, well + '.rsd'))
    chw = np.asarray(ch.T, dtype=np.float64)
    probs = pb.cnn_probs(MODELS, chw, scans)
    pred = probs.argmax(1)
    seq0 = ''.join(pb.LABELS[i] for i in pred)
    conf = [pb.phred(probs[k, i]) for k, i in enumerate(pred)]
    s, _, _ = pb.refine_denovo_v2(MODELS, chw, list(seq0), conf, scans, **cfg)
    return s


def _work(well):
    import numpy as np
    import extract_training_data as etd
    esd = os.path.join(GT_DIR, well + '.esd')
    if not (os.path.isfile(os.path.join(SEP, well + '.npy')) and os.path.isfile(esd)):
        return None
    d = etd.parse_esd(esd)
    dll = blast_seq(d['sequence'])
    row = dict(well=well, dll=dll)
    for i, cfg in enumerate(CONFIGS):
        s = merge_read(well, cfg)
        row[f'cfg{i}'] = blast_seq(s)
        row[f'n{i}'] = sum(c in 'ACGT' for c in s)
    return row


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
                return (f"{r['bases']}b/{r['matched']:.0f}m/{r['full_ident']:.1f}fi" if r else 'NO')
            line = f"{w:5s} "
            for i in range(len(CONFIGS)):
                line += f" cfg{i}[{fm(row['cfg' + str(i)])}] n={row['n' + str(i)]}"
            line += f" DLL[{fm(row['dll'])}]"
            print(line, flush=True)
    with open(os.path.join(HERE, 'merge_probe_rows.csv'), 'w', newline='') as f:
        w2 = csv.writer(f)
        hdr = ['well', 'dll_b', 'dll_matched', 'dll_fi']
        for i in range(len(CONFIGS)):
            hdr += [f'cfg{i}_b', f'cfg{i}_m', f'cfg{i}_fi', f'cfg{i}_n']
        w2.writerow(hdr)
        for r in rows:
            def g(x, k):
                return (x[k] if x else '')
            rec = [r['well'], g(r['dll'], 'bases'), g(r['dll'], 'matched'), g(r['dll'], 'full_ident')]
            for i in range(len(CONFIGS)):
                rec += [g(r['cfg' + str(i)], 'bases'), g(r['cfg' + str(i)], 'matched'),
                        g(r['cfg' + str(i)], 'full_ident'), r['n' + str(i)]]
            w2.writerow(rec)
    print("\n=== probe: merge length+identity (full register, our confidence) ===", flush=True)

    def mx(k):
        v = [r[k] for r in rows]
        v = [x for x in v if x]
        return np.mean([x['matched'] for x in v]) if v else float('nan')
    for label, key in [('dll  ', 'dll')] + [(f'cfg{i} ', f'cfg{i}') for i in range(len(CONFIGS))]:
        v = [r[key] for r in rows]
        v = [x for x in v if x]
        if not v:
            print(f"  {label}: NO", flush=True)
            continue
        print(f"  {label}: bases={np.mean([x['bases'] for x in v]):6.1f} "
              f"matched_bp={np.mean([x['matched'] for x in v]):6.1f} "
              f"cov={np.mean([x['hsp_cov'] for x in v]):5.2f} "
              f"fi={np.mean([x['full_ident'] for x in v]):5.2f}", flush=True)


if __name__ == '__main__':
    main()