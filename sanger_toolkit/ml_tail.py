#!/usr/bin/env python3
"""CNN (v4 ensemble) re-call of the head/tail problem bases.
Labels = ESD peak positions (same as GUI ml_hybrid), windows = raw 31x4.
Compare CNN vs M13 truth, ESD, and the duplex-composite read, per band."""
import glob, json, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'sanger_toolkit'))
sys.path.insert(0, ROOT)
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
HOME = os.path.join(ROOT, '02_denovo_cnn_ensemble_91.53pct')
sys.path.insert(0, HOME)

from optimize_windows_esd import load_well
from Bio import Align
import tensorflow as tf
import perfect_basecaller as pb

raw, esd_seq, esd_pp = load_well(os.path.join(ROOT, 'MB1000_M13_DT'), 'A01',
                                 'MB1000_M13_DT_Cp312_MD1')
m13 = open(os.path.join(ROOT, 'M13.md')).read().strip().upper()

al = Align.PairwiseAligner(); al.match_score = 2; al.mismatch_score = -1
al.open_gap_score = -2; al.extend_gap_score = -1; al.mode = 'global'
a = al.align(esd_seq, m13)[0]
coord = np.full(len(esd_seq), -1, dtype=int)
ei = mi = -1
for c1, c2 in zip(a[0], a[1]):
    if c2 != '-': mi += 1
    if c1 != '-':
        ei += 1
        if c2 != '-': coord[ei] = mi

# duplex-composite (graft) read
graft = list(esd_seq)
for f in glob.glob(os.path.join(ROOT, 'sanger_toolkit', 'od_whole_m13', '*.json')):
    r = json.load(open(f))
    if r['ok'] and r['called']:
        graft[r['idx']] = r['called'][0]

models = [tf.keras.models.load_model(os.path.join(HOME, f), compile=False)
          for f in ['base_caller_model_v4_clean.keras',
                    'base_caller_model_v4_pos.keras',
                    'base_caller_model_v4_pos_b.keras']]
pos_ids = np.asarray(esd_pp, dtype=np.int64)
X4 = pb._build_window(raw, pos_ids, 15)
s_min, s_max = pos_ids.min(), pos_ids.max()
s_range = max(1.0, float(s_max - s_min))
pos_frac = ((pos_ids - s_min) / s_range).astype(np.float32)
probs = np.zeros((len(pos_ids), 4), dtype=np.float64)
for m in models:
    if m.input_shape[-1] == 5:
        W = X4.shape[1]
        pos_ch = pos_frac[:, None, None] * np.ones((len(X4), W, 1), dtype=np.float32)
        inp = np.concatenate([X4, pos_ch], axis=2)
    else:
        inp = X4
    p = m.predict(inp, verbose=0)[:, :4]
    probs += p
probs /= 3.0
cnn = 'ACGT'
labels = probs.argmax(1)
pmax = probs.max(1)

print(f'CNN ran on {len(pos_ids)} ESD positions')
bands = [(2082, 2400), (2400, 7000), (7000, 8600), (8600, 9400)]
print('\nband       n    ESD   GRAFT  CNN     CNN+drop(.5)  CNN+drop(.7)')
for b0, b1 in bands:
    e = g = c = c5 = c7 = cov = 0
    for i in range(len(esd_seq)):
        if not (b0 <= esd_pp[i] <= b1) or coord[i] < 0: continue
        cov += 1
        tr = m13[coord[i]]
        e += (esd_seq[i] == tr)
        g += (graft[i] == tr)
        c += (cnn[labels[i]] == tr)
        c5 += (cnn[labels[i]] == tr and pmax[i] >= 0.5)
        c7 += (cnn[labels[i]] == tr and pmax[i] >= 0.7)
    print(f'{b0}-{b1:<5d} {cov:4d}  {100*e/cov:5.1f}%  {100*g/cov:5.1f}%  '
          f'{100*c/cov:5.1f}%   {100*c5/cov:5.1f}%     {100*c7/cov:5.1f}%')

# detailed failure list for the tail + head: which bases does graft get wrong,
# what does CNN say there, and the CNN confidence
print('\n--- graft errors vs M13 (worst @ tail) ---')
errs = []
for i in range(len(esd_seq)):
    if coord[i] < 0: continue
    if graft[i] != m13[coord[i]]:
        errs.append((int(esd_pp[i]), esd_pp[i], i, esd_seq[i], graft[i],
                     m13[coord[i]], cnn[labels[i]], round(float(pmax[i]), 3)))
errs.sort(reverse=True)
print('scan     idx esd graft truth cnn  p   band')
for s, _, i, e_, gr, tr, cl, p in errs:
    band = 'HEAD' if s < 2400 else ('TAIL' if s > 8600 else 'MID')
    print(f'{s:5d}  {i:3d}  {e_}→{gr}  {tr}   {cl}   {p:.2f}  {band}')
print(f'total graft errors: {len(errs)}')

np.save('/tmp/opencode/ml_cnn_probs.npy', probs)
np.save('/tmp/opencode/ml_cnn_pmax.npy', pmax)
print('saved probs arrays')