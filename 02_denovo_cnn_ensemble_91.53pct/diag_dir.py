#!/usr/bin/env python3
"""Test if color-separation (direction) features explain the CNN's ~7% gap.

DLL hypothesis: a single base peak is a 4D direction (dye emission). If we
decompose each window center-column into [baseline + height*direction], and
classify by nearest class-mean direction, we mimic the DLL's calibrated
decision without any CNN. Compare val accuracy on the SAME non-band columns.

Prints: class directions (train), and val accuracy of
  (a) raw direction classifier
  (b) baseline-subtracted direction classifier (10th pct per channel)
  (c) direction classifier on domain-compressed windows (center + immediate)
Also reports coverage of the tail/head regions to see where direction-alone fails.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, HERE)
d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
X, y = d['X'], d['y'].astype(int)
reg = d['region'].astype(int)
split = d['split'].astype(bool)
scan = d['scan'].astype(int)
refpos0 = d['refpos0'].astype(int)
labels = [str(x) for x in d['labels']]
labels_a = np.asarray(labels)

cblo = d['cband_lo'].astype(int)
cbhi = d['cband_hi'].astype(int)
in_band = np.zeros(len(y), bool)
for lo, hi in zip(cblo, cbhi):
    in_band |= (refpos0 >= lo) & (refpos0 <= hi)

tr = split & ~in_band
va = ~split & ~in_band
print(f'train-col {tr.sum()}  val-nonband {va.sum()}  '
      f'val-nonband notailtail {(va & (reg < 3)).sum()}')

def dir_features(Xw):
    c = Xw[:, 15, :] + 1e-6
    # baseline per channel = min over left/right thirds (shoulder background)
    b = np.concatenate([Xw[:, :5, :], Xw[:, 26:, :]], axis=1).min(axis=1) + 1e-6
    s = c - b
    s = s / (np.linalg.norm(s, axis=1, keepdims=True) + 1e-9)
    return s

for name, use_b in [('raw-mean', False), ('baseline-sub', True)]:
    if use_b:
        Ftr = dir_features(X[tr])
        Fva = dir_features(X[va])
    else:
        Ftr = (X[tr][:, 15, :] + 1e-6)
        Ftr = Ftr / (np.linalg.norm(Ftr, axis=1, keepdims=True) + 1e-9)
        Fva = (X[va][:, 15, :] + 1e-6) / (np.linalg.norm(X[va][:, 15, :], axis=1, keepdims=True) + 1e-9)
    means = np.zeros((4, 4))
    for b in range(4):
        m_ = (y[tr] == b)
        means[b] = Ftr[m_].mean(axis=0)
        means[b] /= (np.linalg.norm(means[b]) + 1e-9)
    score = Fva @ means.T
    pred = score.argmax(axis=1)
    okv = (pred == y[va])
    print(f'\n[{name}] val non-band acc {okv.mean()*100:.2f}% n={len(okv)}')
    for lo, hi in [(0, 3), (3, 0)]:
        pass
    for r in range(4):
        m_ = reg[va] == r
        if m_.any():
            print(f'   region {r} acc {okv[m_].mean()*100:.2f}% n={int(m_.sum())}')
    # by rank
    rp = refpos0[va]
    fr = (rp - rp.min()) / max(1, rp.max() - rp.min())
    for lo, hi in [(0, .1), (.1, .5), (.5, .9), (.9, 1.0)]:
        m_ = (fr >= lo) & (fr < hi)
        if m_.any():
            print(f'   rank[{lo:.1f},{hi:.1f}) acc {okv[m_].mean()*100:.2f}% n={int(m_.sum())}')
    CM = np.zeros((4, 4), int)
    for t, p in zip(y[va], pred):
        if t < 4 and p < 4:
            CM[t, p] += 1
    print('   confusion (true rows):')
    for i in range(4):
        print('   ' + ' '.join(f'{labels[i]}:{CM[i, j]:6d}' for j in range(4)) + f'  err {100*(1-CM[i,i]/max(1,CM[i].sum())):.1f}%')
    # direction classifier confidence -> how much does a CNN agree when direction strong?
    srt = score.max(axis=1)