#!/usr/bin/env python3
"""diag_v3.py - where do the held-out per-column errors come from?

Loads v3_training.npz val windows, runs the 4 saved v3 region models,
and buckets every (mis)classification by:
  region, true base, predicted base, center-peak intensity, local spacing,
  dominant-channel agreement, center-vs-neighbor contrast.

No BLAST; fast. Print-only.
"""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.realpath(__file__))
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')
sys.path.insert(0, HERE)

import tensorflow as tf
import train_v3 as tv

d = np.load(os.path.join(HERE, 'v3_training.npz'), allow_pickle=True)
X, y = d['X'], d['y'].astype(int)
reg = d['region'].astype(int)
split = d['split'].astype(bool)
scan = d['scan'].astype(int)
well = d['well']
refpos0 = d['refpos0'].astype(int)
labels = [str(x) for x in d['labels']]
labels_a = np.asarray(labels)
labels5 = labels + ['bg']

val = ~split
print(f'val windows: {int(val.sum())}')

# construct bands as in eval_v3: labelled non-M13 columns (also ca. tail insert)
cblo = d['cband_lo'].astype(int)
cbhi = d['cband_hi'].astype(int)
in_band = np.zeros(len(y), bool)
for lo, hi in zip(cblo, cbhi):
    in_band |= (refpos0 >= lo) & (refpos0 <= hi)
print(f'ev-aligned (non-band) val windows: '
      f'{int((val & ~in_band).sum())}  band: {int((val & in_band).sum())}')

rows = dict(k=[])
pred = np.full(len(y), -1)
for r in range(4):
    m = tf.keras.models.load_model(
        os.path.join(HERE, f'base_caller_model_v3_{tv.REGIONS[r]}.keras'))
    sel = val & (reg == r)
    Xte = tv.zscore(X[sel])
    p = m.predict(Xte, batch_size=1024, verbose=0)
    pred[sel] = p.argmax(axis=1)

vv = val.copy()
ok = pred[vv] == y[vv]
tot = int(vv.sum())
print(f'val accuracy: {ok.mean()*100:.2f}% ({int(ok.sum())}/{tot})')

ib = in_band[vv]
ev = ~ib
vN = f'{ok[ev].mean()*100:.2f}%'
print(f'non-band val accuracy: {vN} n={int(ev.sum())}')

true = y[vv]
prd = pred[vv]
rg = reg[vv]
sc = scan[vv]
rp = refpos0[vv]
Xv = X[vv]

evtt = ev & (rg < 3)
print(f'non-band excl tailtail: {ok[evtt].mean()*100:.2f}% n={int(evtt.sum())}')
print(f'band (construct) accuracy: {ok[ib].mean()*100:.2f}% n={int(ib.sum())}')

ACC = 1e-6
c = Xv[:, 15, :] + ACC
h = c.sum(axis=1)
mx = c.max(axis=1)
chi = c.argmax(axis=1)
chan_of = np.array(['A', 'C', 'G', 'T'])
dom_ok = (chan_of[chi] == labels_a[true])

# local spacing proxy: scans to nearest other local max inside the window
def local_geom(win, center=15):
    v = win.sum(axis=1)
    peaks = []
    for i in range(1, len(v) - 1):
        if v[i] >= v[i - 1] and v[i] >= v[i + 1] and v[i] > 0:
            peaks.append(i)
    if not peaks:
        return 0.0, 0.0, 0.0
    cp = min(peaks, key=lambda p: abs(p - center))
    right = min([p for p in peaks if p > cp], default=None)
    left = max([p for p in peaks if p < cp], default=None)
    if right is not None and left is not None:
        sp = (right - left) / 2.0
    elif right is not None:
        sp = float(right - cp)
    elif left is not None:
        sp = float(cp - left)
    else:
        sp = 0.0
    off = abs(cp - center)
    return sp, off, float(v[center])

csum = Xv.sum(axis=(1, 2)) + ACC
center_frac = c / csum[:, None]  # (n,4)
contrast = (c.max(axis=1) / (Xv[:, :, :].mean(axis=(1, 2)) + ACC))

geom = np.array([local_geom(w) for w in Xv])
spacing = geom[:, 0]
offc = geom[:, 1]
peakv = geom[:, 2]

print('\n--- confusion (true rows, pred cols) ---')
CM = np.zeros((5, 5), int)
for t, p in zip(true, prd):
    CM[t, p] += 1
print('    ' + ' '.join(f'{labels5[j]:>4s}' for j in range(5)))
for i in range(5):
    tot_i = CM[i].sum()
    print(f'{labels5[i]:>3s} {tot_i:6d} ' +
          ' '.join(f'{CM[i, j]:4d}' for j in range(5)) +
          (f'  err={100*(1-CM[i,i]/tot_i):5.1f}%' if tot_i else ''))

print('\n--- error rate by region ---')
for r in range(4):
    m_ = rg == r
    if not m_.any():
        continue
    print(f'  {tv.REGIONS[r]:9s} acc={ok[m_].mean()*100:6.2f}% n={int(m_.sum())}')

print('\n--- error rate by center-peak intensity quartile ---')
qs = np.quantile(h, [0.25, 0.5, 0.75])
qb = np.digitize(h, qs)
for q_ in range(4):
    m_ = qb == q_
    if not m_.any():
        continue
    print(f'  q{q_}  h<{str(round(qs[q_-1],1)) if q_>0 else "-":>8s} acc={ok[m_].mean()*100:6.2f}% n={int(m_.sum())}')

print('\n--- error rate by local spacing (scans between neighbor peaks) ---')
sb = np.digitize(spacing, [6, 7.5, 9, 10.5])
for s_ in range(5):
    m_ = sb == s_
    if not m_.any():
        continue
    print(f'  s{s_}  sp<{["6","7.5","9","10.5","inf"][s_]:>4s} acc={ok[m_].mean()*100:6.2f}% n={int(m_.sum())}')

print('\n--- error rate by center-offset (scans window-center to nearest peak) ---')
ob = np.digitize(offc, [0.5, 1.5, 2.5])
for o_ in range(4):
    m_ = ob == o_
    if not m_.any():
        continue
    print(f'  o{o_}  off={["0","0.5","1.5","2.5+"][o_]:>4s} acc={ok[m_].mean()*100:6.2f}% n={int(m_.sum())}')

print('\n--- error rate by dominant-channel agreement (center pixel) ---')
print(f'  center-channel == label channel: acc={ok[dom_ok].mean()*100:6.2f}% n={int(dom_ok.sum())}')
print(f'  center-channel != label channel: acc={ok[~dom_ok].mean()*100:6.2f}% n={int((~dom_ok).sum())}')
if (~dom_ok).any():
    print('  top confusions where center channel is wrong:')
    bad = ~(ok & dom_ok) & ~dom_ok
    for (t, p) in zip(true[bad], prd[bad]):
        pass
    cf = np.zeros((4, 4), int)
    for t, p in zip(true[bad], prd[bad]):
        if t < 4 and p < 4:
            cf[t, p] += 1
    for i in range(4):
        for j in range(4):
            if cf[i][j] > 0:
                print(f'    true={labels_a[i]} pred={labels[j]} n={cf[i][j]}')

print('\n--- error rate by raw peak-position vs ESD scan (argmax of total i-profile) ---')
am = Xv.sum(axis=2).argmax(axis=1)
aoff = np.abs(am - 15)
for lo, hi in [(0, 1), (1, 2), (2, 4), (4, 8), (8, 99)]:
    m_ = (aoff >= lo) & (aoff < hi)
    if not m_.any():
        continue
    print(f'  |rawpeak-ESD| in [{lo},{hi}) acc={ok[m_].mean()*100:6.2f}% n={int(m_.sum())}')
am_ev = np.abs(Xv.sum(axis=2).argmax(axis=1) - 15)
m_ev = ev & (am_ev >= 2)
print(f'  non-band, |rawpeak-ESD|>=2: acc={ok[m_ev].mean()*100:6.2f}% n={int(m_ev.sum())}')
m_ev0 = ev & (am_ev < 2)
print(f'  non-band, |rawpeak-ESD|<2 : acc={ok[m_ev0].mean()*100:6.2f}% n={int(m_ev0.sum())}')

print('\n--- error rate by rank-in-read (region cut is crude; use refpos0 fraction) ---')
rpfrac = (rp - rp.min()) / max(1, rp.max() - rp.min())
for lo, hi in [(0, 0.1), (0.1, 0.5), (0.5, 0.9), (0.9, 1.0)]:
    m_ = (rpfrac >= lo) & (rpfrac < hi)
    if not m_.any():
        continue
    print(f'  rank[{lo:.1f},{hi:.1f}) acc={ok[m_].mean()*100:6.2f}% n={int(m_.sum())}')

print('\n--- per-well val acc (worst 10) ---')
per = {}
for i in range(len(y)):
    if not vv[i]:
        continue
    w = well[i]
    per.setdefault(w, [0, 0])[0] += int(ok[i] if True else 0)
    per[w][1] += 1
for w, (c_, n_) in sorted(per.items(), key=lambda kv: kv[1][0] / kv[1][1])[:10]:
    print(f'  {w} acc={100*c_/n_:6.2f}% n={n_}')