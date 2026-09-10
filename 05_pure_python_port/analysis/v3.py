import numpy as np
from scipy import ndimage
import scipy.signal as sps

def smooth(x, window=3):
    if window < 2 or x.size < window: return x.copy()
    return np.convolve(x, np.ones(window)/window, mode="same")

def detect_envelope(norm, min_distance=2):
    env = smooth(norm.max(axis=0), 3)
    pks = sps.find_peaks(env, distance=min_distance, prominence=0.0)[0]
    return pks, env

def assign_channels(norm, peaks, win=1):
    n = norm.shape[1]
    n_dyes = norm.shape[0]
    chans = np.empty(peaks.size, dtype=int)
    domv = np.empty(peaks.size)
    cross = np.empty(peaks.size)
    for j, p in enumerate(peaks):
        lo, hi = max(0, p-win), min(n, p+win+1)
        v = norm[:, lo:hi].max(axis=1)
        c = int(v.argmax())
        chans[j] = c; domv[j] = v[c]
        v2 = np.delete(v, c)
        cross[j] = v2.max()/max(v[c], 1e-9)
    return chans, domv, cross

def expected_spacing(peaks):
    if peaks.size < 3:
        return np.full(peaks.size, 8.0)
    sp = np.diff(peaks).astype(float)
    # robust: fit quadratic to spacing vs peak index (midpoints)
    x = np.arange(peaks.size-1, dtype=float) + 0.5
    # remove outliers (spacing beyond 2x median)
    med = np.median(sp)
    mask = (sp > 0.2*med) & (sp < 4*med)
    if mask.sum() < 3:
        return np.full(peaks.size, med)
    coeffs = np.polyfit(x[mask], sp[mask], 2)
    s = np.polyval(coeffs, np.arange(peaks.size-1, dtype=float) + 0.5)
    s = np.clip(s, 1.5, 40)
    # expected spacing per peak = avg of adjacent gaps
    out = np.empty(peaks.size)
    out[0] = s[0]; out[-1] = s[-1]
    out[1:-1] = 0.5*(s[:-1]+s[1:])
    return out

def cull_and_insert(norm, peaks, min_dist_frac=0.45, insert_frac=1.5, max_iter=6):
    """Remove spurious peaks (too close) and insert missing peaks (too far)."""
    peaks = peaks.copy()
    for _ in range(max_iter):
        if peaks.size < 3: break
        s = expected_spacing(peaks)
        removed = False; inserted = False
        new = []
        i = 0
        while i < peaks.size:
            new.append(peaks[i])
            if i+1 < peaks.size:
                g = peaks[i+1] - peaks[i]
                se = 0.5*(s[i]+s[i+1])
                if g < min_dist_frac*se:
                    # spurious: remove weaker of the two
                    v = norm[:, peaks[i]:peaks[i]+1].max()
                    v2 = norm[:, peaks[i+1]:peaks[i+1]+1].max()
                    if v2 >= v:
                        new.pop()  # remove current
                    # else keep current and skip next
                    if v2 < v:
                        i += 1  # skip next
                elif g > insert_frac*se:
                    n_ins = int(round(g/se)) - 1
                    if n_ins > 0 and g < 12*se:
                        for k in range(1, n_ins+1):
                            pos = peaks[i] + int(round(g*k/(n_ins+1)))
                            new.append(pos)
                        inserted = True
            i += 1
        peaks = np.array(sorted(set(new)), dtype=int)
        if not removed and not inserted: break
    return peaks

def call_v3(norm, min_distance=2):
    pks, env = detect_envelope(norm, min_distance)
    pks = cull_and_insert(norm, pks)
    chans, domv, cross = assign_channels(norm, pks)
    return pks, chans, domv, cross, env
