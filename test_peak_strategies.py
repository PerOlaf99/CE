#!/usr/bin/env python3
"""Test different peak detection strategies against M13 reference."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from extract_training_data import parse_rsd, parse_esd
from scipy.signal import find_peaks, savgol_filter
from m13_reference import M13_REFERENCE, align_to_reference
from basecaller import _load_ml_model, ML_LABELS

df = parse_rsd('/media/per/Disk 2/electropherogram/MB1000_M13_DT/A01.rsd')
ch = df[['Channel1','Channel2','Channel3','Channel4']].values.astype(np.float32)
total = ch.sum(axis=1)
n_scans = len(ch)
window = 15
model = _load_ml_model()

esd = parse_esd('/media/per/Disk 2/electropherogram/MB1000_M13_DT/MB1000_M13_DT_Cp312_MD1/A01.esd')
seq_s = esd.get('sequence','')
pp = esd.get('peak_positions')
if pp is None: pp = esd.get('bases_positions')
esd_pos = np.asarray(pp[:len(seq_s)]).astype(int)

def eval_peaks(peaks, label):
    peaks = np.array(peaks)
    valid = (peaks >= window) & (peaks < n_scans - window)
    peaks = peaks[valid]
    if len(peaks) == 0:
        print(f'{label}: 0 peaks')
        return
    X = np.array([ch[p-window:p+window+1] for p in peaks], dtype=np.float32)
    X = (X - X.mean(axis=(1,), keepdims=True)) / (X.std(axis=(1,), keepdims=True) + 1e-8)
    preds = model.predict(X, verbose=0)
    y = [ML_LABELS[c] if c < 4 else 'N' for c in preds.argmax(axis=1)]
    align = align_to_reference(''.join(y), M13_REFERENCE)
    print(f'{label}: {len(peaks)} peaks, {align["identity"]:.4f} ({align["matches"]}/{align["aligned_length"]})')

print('=== Reference accuracy by peak detection strategy ===')
print()

eval_peaks(esd_pos, 'ESD positions (golden)')

peaks_t7, _ = find_peaks(savgol_filter(total, 7, 2), height=20, prominence=10, distance=3)
eval_peaks(peaks_t7, 'Total w=7')

peaks_t5, _ = find_peaks(savgol_filter(total, 5, 2), height=10, prominence=5, distance=2)
eval_peaks(peaks_t5, 'Total w=5 permissive')

peaks_c3, _ = find_peaks(savgol_filter(ch[:,2], 7, 2), height=20, prominence=10, distance=3)
eval_peaks(peaks_c3, 'Ch3 only')

# ALSO: test Ch1+Ch3 (most informative channels individually)
peaks_c1, _ = find_peaks(savgol_filter(ch[:,0], 7, 2), height=15, prominence=8, distance=3)
eval_peaks(peaks_c1, 'Ch1 only')
