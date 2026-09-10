#!/usr/bin/env python3
"""attack_merge.py - NEXT_SESSION steps 2 & 3 (and 4 lightly):

  * Step 2 (measure): global-align a MERGE read vs M13 and decompose every
    aligned column as match/insert/delete, then attribute those to read
    region (head/middle/tail) and to contiguity (isolated vs adjacent/doublet
    runs).  Answers: is the ~753 matched_bp gate reachable by *cleaning* the
    candidate set (doublets / tail junk) or is it a *labels* limit?

  * Step 3 / Attack 1: kill doublets BEFORE labelling.  On the FULL DLL
    register candidate list (all envelope rising->falling transitions in the
    CF region incl. the DLL tail), merge envelope peaks closer than
    ~0.5*median spacing (keep the stronger), THEN CNN-label the cleaned set.
    Target: matched_bp up, fi unchanged.

Run on the machine that holds the models + BLAST (TF required):
    python3 -u attack_merge.py --wells A01 B04 B05 C09 D12 H11
    python3 -u attack_merge.py --wells A01 --cfg 0.50/0.70 0.40/0.60
"""
import os, sys, csv, tempfile, subprocess, argparse, multiprocessing as mp
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
os.environ['OMP_NUM_THREADS'] = '1'; os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'; os.environ['NUMEXPR_NUM_THREADS'] = '1'
HERE = os.path.dirname(os.path.realpath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, ROOT)

GT_DIR = os.path.join(ROOT, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
PLATE = os.path.join(ROOT, 'MB1000_M13_DT')
SEP = os.path.join(ROOT, 'cache_sep')
REF = os.path.join(ROOT, 'sanger_toolkit', 'refs', 'm13_M77815.1.fa')

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
                    full_ident=100.0 * matched / qlen, pident=pident,
                    hsp_cov=100.0 * (qe - qs + 1) / qlen)


# ---- candidate generation (identical to merge_probe.py) ----
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


def full_register(well):
    """Full DLL-length candidate positions (env maxima in the CF region),
    incl. the DLL tail, exactly as merge_probe uses them."""
    import numpy as np
    import dll_peakdet as dp
    lanes = np.load(os.path.join(SEP, well + '.npy')).astype(np.float64)
    env = dp.env_max(lanes)
    scans = np.array(transitions(env), np.int64)
    envs = env[scans]
    reg = longest_region(envs, 0.05 * env.max())
    if reg is None:
        return np.array([], np.int64)
    lo, hi = reg
    return scans[lo:hi + 1]


def kill_doublets(scans, envs, frac=0.5):
    """Attack 1: merge envelope peaks closer than frac*median-spacing before
    labelling.  Among a close cluster keep the one with the LARGEST envelope
    (the stronger peak).  Returns deduped (scans, envs) in order."""
    import numpy as np
    if len(scans) < 3:
        return scans, envs
    med = float(np.median(np.diff(scans)))
    keep = []
    i = 0
    n = len(scans)
    while i < n:
        # gather cluster: all consecutive peaks within frac*med of the prev
        j = i + 1
        while j < n and (scans[j] - scans[j - 1]) < frac * med:
            j += 1
        cl = slice(i, j)
        bi = int(np.argmax(envs[cl]))
        keep.append(i + bi)
        i = j
    keep = np.array(sorted(set(keep)), dtype=np.int64)
    return scans[keep], envs[keep]


def _merge(well, cfg, frac=0.5, measure=False):
    """Return BLAST dict for the merge read built with Attack-1 doublet kill
    (frac=0 disables it).  If measure, also return the indel structure dict."""
    import numpy as np
    import cimarrontv as cim
    import perfect_basecaller as pb
    import dll_peakdet as dp
    lanes = np.load(os.path.join(SEP, well + '.npy')).astype(np.float64)
    env = dp.env_max(lanes)
    full = full_register(well)
    if len(full) == 0:
        return None, None
    envs = env[full]
    n_before = len(full)
    if frac > 0:
        full, envs = kill_doublets(full, envs, frac)
    ch, sc = cim.read_rsd(os.path.join(PLATE, well + '.rsd'))
    chw = np.asarray(ch.T, dtype=np.float64)
    probs = pb.cnn_probs(MODELS, chw, full)
    pred = probs.argmax(1)
    seq0 = ''.join(pb.LABELS[i] for i in pred)
    conf = [pb.phred(probs[k, i]) for k, i in enumerate(pred)]
    s, c2, sp = pb.refine_denovo_v2(MODELS, chw, list(seq0), conf, full, **cfg)

    d = blast_seq(s) if s else None
    meas = None
    if measure:
        meas = indel_structure(s) if s else None
        if meas is not None:
            meas['n_cand_before'] = n_before
            meas['n_cand_after'] = len(full)
            meas['n_doublet_killed'] = n_before - len(full)
    return d, meas


def indel_structure(seq):
    """Global-align the read vs reference (read orientation) and tag columns.
    Returns dict of counts split by (a) read region (head/mid/tail) and
    (b) adjacency (isolated vs part of a >=2 run)."""
    import numpy as np
    from extract_m13_clean_training import load_clean_ref, seed_sw_align
    ref = load_clean_ref()
    al = seed_sw_align(seq, ref)
    if al is None:
        return None
    q_al, r_al = al
    # per-read-position tag of the alignment path
    pos_tags = []  # 0 match, 1 insert (q base where r=-), 2 delete (r base where q=-)
    for q, r in zip(q_al, r_al):
        if q == '-':
            pos_tags.append(2)      # deletion: reference base with no query base
        elif r == '-':
            pos_tags.append(1)      # insertion: query base with no ref base
        else:
            pos_tags.append(0)      # match or substitution
    nq = len([q for q in q_al if q != '-'])
    if nq == 0:
        return None

    def region(idx):
        """Region by read position along q_al (non-gap read positions only)."""
        f = (idx + 0.5) / nq
        return 1 if f < 1 / 3 else (2 if f < 2 / 3 else 3)

    def contig(taglist):
        """Return (isolated_count, run_count_total) for tags equal to `v`."""
        runs = []
        cur = 0
        for t in taglist:
            if t in (1, 2):
                cur += 1
            else:
                if cur:
                    runs.append(cur)
                    cur = 0
        if cur:
            runs.append(cur)
        return len([r for r in runs if r == 1]), sum(runs)

    iso_ins, tot_ins = contig(pos_tags)
    iso_del, tot_del = contig(pos_tags)
    mm = sum(1 for q, r in zip(q_al, r_al) if q != '-' and r != '-' and q != r)
    n_match = sum(1 for q, r in zip(q_al, r_al) if q != '-' and r != '-' and q == r)

    by_reg = {1: {}, 2: {}, 3: {}}
    del_by_reg = {1: 0, 2: 0, 3: 0}
    qpos = 0
    for q, r in zip(q_al, r_al):
        if q == '-':
            reg = region(qpos) if qpos > 0 else region(0)
            del_by_reg[reg] += 1
            continue
        reg = region(qpos)
        d = by_reg[reg]
        if r == '-':
            d['ins'] = d.get('ins', 0) + 1
        elif r == q:
            d['match'] = d.get('match', 0) + 1
        else:
            d['mm'] = d.get('mm', 0) + 1
        qpos += 1

    return dict(n_read=nq, n_match=n_match, n_mm=mm, n_ins=tot_ins, n_del=tot_del,
                iso_ins=iso_ins, iso_del=iso_del,
                ins_by_reg=by_reg, del_by_reg=del_by_reg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--wells', nargs='*',
                    default=['A01', 'B04', 'B05', 'C09', 'D12', 'H11'])
    ap.add_argument('--cfg', default='0.50/0.70',
                    help='drop_p_hi/drop_p_lo[/add_p] (default 0.50/0.70/0.60)')
    ap.add_argument('--metrics', action='store_true',
                    help='also print indel-structure decomposition (step 2)')
    ap.add_argument('--wide', action='store_true')
    args = ap.parse_args()
    parts = [float(x) for x in args.cfg.replace(',', '/').split('/')]
    cfg = dict(drop_p_hi=parts[0], drop_p_lo=parts[1], add_p=parts[2] if len(parts) > 2 else 0.60)

    ctx = mp.get_context('spawn')
    with ctx.Pool(2, initializer=_init) as pool:
        for well in args.wells:
            # no-doublet-kill baseline then attack-1, plus deletion counterflow
            d0, _ = _merge(well, cfg, frac=0.0, measure=args.metrics)
            d1, m1 = _merge(well, cfg, frac=0.5, measure=args.metrics)
            d2, m2 = _merge(well, cfg, frac=0.65, measure=args.metrics)

            def fm(x):
                return f"{x['bases']}b/{x['matched']:.0f}m/{x['full_ident']:.1f}fi" if x else 'NO'
            print(f"{well:5s} base[{fm(d0)}] k0.5[{fm(d1)}] k0.65[{fm(d2)}]", flush=True)
            if args.metrics and m1:
                b = m1
                print(f"   -> k0.5 doubled: cand {b['n_cand_before']}->{b['n_cand_after']} "
                      f"(-{b['n_doublet_killed']}); read={b['n_read']} match={b['n_match']} "
                      f"mm={b['n_mm']} ins={b['n_ins']}(iso {b['iso_ins']}) "
                      f"del={b['n_del']}(iso {b['iso_del']})", flush=True)
                print(f"      ins by region { {k: v['ins'] for k, v in b['ins_by_reg'].items()} } "
                      f"del by region {b['del_by_reg']}", flush=True)
            if args.metrics and m2:
                b = m2
                print(f"   -> k0.65 doubled: cand {b['n_cand_before']}->{b['n_cand_after']} "
                      f"(-{b['n_doublet_killed']}); read={b['n_read']} match={b['n_match']} "
                      f"mm={b['n_mm']} ins={b['n_ins']}(iso {b['iso_ins']}) "
                      f"del={b['n_del']}(iso {b['iso_del']})", flush=True)
                print(f"      ins by region { {k: v['ins'] for k, v in b['ins_by_reg'].items()} } "
                      f"del by region {b['del_by_reg']}", flush=True)


if __name__ == '__main__':
    main()
