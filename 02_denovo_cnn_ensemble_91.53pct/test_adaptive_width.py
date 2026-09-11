#!/usr/bin/env python3
"""Test adaptive window width at DLL positions vs fixed W=15, W=20, W=30.
Physics: head peaks ~6 wide, tail peaks ~34 wide.
CNN trained on W=15 windows, so wider windows feed cropped/zeroed context
but should capture the full peak at tail."""
import sys, os, numpy as np
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'sanger_toolkit'))
import tensorflow as tf, dll_peakdet as dp
from extract_training_data import parse_esd
from bandstat import band_features

SEP = '../cache_sep'
GT = '../ground_truth/MB1000_M13_DT_Cp312_MD1'
CUTS8 = (0.05, 0.15, 0.35, 0.50, 0.65, 0.80, 0.90)


def region_of(f):
    r = 0
    for c in CUTS8:
        if f >= c: r += 1
        else: break
    return r


def zscore(X):
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    return ((X - mu) / sd).astype(np.float32)


def window_var(lanes, s, L):
    """Return a fixed 31-length window; if L>15 the extra width is cropped
    via edge-pad (window wider than trained 15 is not batchable)."""
    n = len(lanes)
    lo, hi = s - L, s + L + 1
    win = lanes[max(0, lo):min(n, hi)]
    if lo < 0 or hi > n:
        win = np.pad(win, ((max(0, -lo), max(0, hi - n)), (0, 0)), mode='edge')
    # crop to central 31
    L31 = 15
    c = win.shape[0]
    s0 = max(0, (c // 2) - L31)
    win = win[s0:s0 + 31]
    if win.shape[0] < 31:
        win = np.pad(win, ((0, 31 - win.shape[0]), (0, 0)), mode='edge')
    return win.astype(np.float32)


models = [tf.keras.models.load_model(
    f'base_caller_model_v6_cal8_r{r}.keras', compile=False) for r in range(8)]

wells = ['A01', 'E05', 'G11', 'H08', 'F02', 'B06', 'A07', 'G09',
         'C03', 'C07', 'D04', 'D06']

results = {}
for w in wells:
    E = parse_esd(f'{GT}/{w}.esd')
    pp = np.array([int(p) for p in E['peak_positions']])
    seq = np.array(list(E['sequence']))
    labels = np.array(['ACGT'.index(b) if b in 'ACGT' else -1 for b in seq])
    sep = np.load(f'{SEP}/{w}.npy')
    n = len(sep)

    # get per-position width from band_features
    bf = band_features(sep, pp)
    widths = bf[:, 3]

    # fractions for region assignment
    fr = np.arange(len(pp)) / max(1, len(pp) - 1)
    regs = np.array([region_of(f) for f in fr])

    row = {}
    for mode in ['fix15', 'fix20', 'fix30', 'w1.0x', 'w1.2x', 'wvar']:
        Xs = []
        for i, p in enumerate(pp):
            if mode == 'fix15':
                L = 15
            elif mode == 'fix20':
                L = 20
            elif mode == 'fix30':
                L = 30
            elif mode == 'w1.0x':
                L = int(np.clip(widths[i], 10, 40))
            elif mode == 'w1.2x':
                L = int(np.clip(1.2 * widths[i], 12, 40))
            elif mode == 'wvar':
                # 2x width capped between 14 and 40
                L = int(np.clip(2.0 * widths[i], 14, 40))
            Xs.append(window_var(sep, int(p), L))
        X = np.array(Xs)
        P = np.zeros((len(pp), 5))
        for r in range(8):
            sel = regs == r
            if sel.sum():
                P[sel] = models[r].predict(zscore(X[sel]), batch_size=256, verbose=0)
        acc = (P[:, :4].argmax(1) == labels).mean()
        row[mode] = acc

    results[w] = row
    print(f'  {w}', ' '.join(f'{k}={v:.3f}' for k, v in row.items()),
          f' widths min={widths.min():.0f} max={widths.max():.0f} p50={np.median(widths):.0f}')

print('\nmeans:')
for mode in ['fix15', 'fix20', 'fix30', 'w1.0x', 'w1.2x', 'wvar']:
    vals = [results[w][mode] for w in results]
    print(f'  {mode} {np.mean(vals):.4f}  (range {min(vals):.3f}..{max(vals):.3f})')

# tail accuracy only (region >=5)
print('\nregion>=5 (tail) accuracy:')
for mode in ['fix15', 'fix20', 'fix30', 'w1.0x', 'w1.2x', 'wvar']:
    tails = []
    for w in wells:
        E = parse_esd(f'{GT}/{w}.esd')
        pp = np.array([int(p) for p in E['peak_positions']])
        seq = np.array(list(E['sequence']))
        labels = np.array(['ACGT'.index(b) if b in 'ACGT' else -1 for b in seq])
        fr = np.arange(len(pp)) / max(1, len(pp) - 1)
        tail = fr >= 0.65
        sep = np.load(f'{SEP}/{w}.npy')
        bf = band_features(sep, pp)
        widths = bf[:, 3]
        regs = np.array([region_of(f) for f in fr])
        Xs = []
        for i, p in enumerate(pp):
            if mode == 'fix15': L = 15
            elif mode == 'fix20': L = 20
            elif mode == 'fix30': L = 30
            elif mode == 'w1.0x': L = int(np.clip(widths[i], 10, 40))
            elif mode == 'w1.2x': L = int(np.clip(1.2 * widths[i], 12, 40))
            else: L = int(np.clip(2.0 * widths[i], 14, 40))
            Xs.append(window_var(sep, int(p), L))
        X = np.array(Xs)
        P = np.zeros((len(pp), 5))
        for r in range(8):
            sel = regs == r
            if sel.sum():
                P[sel] = models[r].predict(zscore(X[sel]), batch_size=256, verbose=0)
        ta = (P[tail, :4].argmax(1) == labels[tail]).mean()
        tails.append(ta)
    print(f'  {mode} {np.mean(tails):.4f}')
