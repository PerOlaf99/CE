"""Plate analysis for rs1695 genotyping.
Usage: python analyze_plate.py T5  # or T1, T2, etc.
"""
import sys, os, numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_widths, savgol_filter
from extract_training_data import parse_rsd
from genotyping_analysis import deconvolve_peaks, compute_mutant_fraction

SCAN_START = 2000
SCAN_END = 2950
N_IS_PEAKS = 4
IS_MATCH_MIN = 5   # sample peak min scans before IS
IS_MATCH_MAX = 25  # sample peak max scans before IS
FWHM_LIMIT = 10    # default, adjusted by assess_plate_quality()


def assess_plate_quality(plate_dir, n_sample=6):
    """Sample wells to estimate plate resolution.
    Returns (quality, fwhm_max, metrics_dict).
    quality: 'GOOD'|'FAIR'|'POOR'|'FAILED'
    """
    import random
    all_rsd = [f for f in os.listdir(plate_dir) if f.endswith('.rsd')]
    if len(all_rsd) < 3:
        return 'FAILED', 10, {'reason': 'too few files'}
    sample = random.sample(all_rsd, min(n_sample, len(all_rsd)))
    is_fwhms = []
    samp_narrow_fwhms = []
    is_counts = []
    for f in sample:
        try:
            df = parse_rsd(os.path.join(plate_dir, f))
        except Exception:
            continue
        ch3 = df['Channel3'].values.astype(float)[SCAN_START:SCAN_END]
        ch2 = df['Channel2'].values.astype(float)[SCAN_START:SCAN_END]
        is_p, _ = find_peaks(ch3, height=500, distance=25, prominence=300)
        is_counts.append(len(is_p))
        for p in is_p:
            half = ch3[p] / 2
            l = p
            while l > 0 and ch3[l] > half:
                l -= 1
            r = p
            while r < len(ch3) - 1 and ch3[r] > half:
                r += 1
            is_fwhms.append(r - l)
        # Sample narrow peaks only (likely genotyping signal)
        samp_p, _ = find_peaks(ch2, height=2000, distance=10)
        for p in samp_p:
            half = ch2[p] / 2
            l = p
            while l > 0 and ch2[l] > half:
                l -= 1
            r = p
            while r < len(ch2) - 1 and ch2[r] > half:
                r += 1
            fw = r - l
            if fw < 30:  # Only consider narrow peaks for quality
                samp_narrow_fwhms.append(fw)
    if not is_fwhms:
        return 'FAILED', 10, {'is_median_fwhm': 0, 'reason': 'no IS peaks'}
    m_is = np.median(is_fwhms)
    m_samp = np.median(samp_narrow_fwhms) if samp_narrow_fwhms else 99
    avg_is_count = np.mean(is_counts)
    metrics = {'is_median_fwhm': float(m_is), 'samp_median_fwhm': float(m_samp),
               'avg_is_per_well': float(avg_is_count), 'n_sampled': len(sample)}
    if avg_is_count < 2.5:
        return 'FAILED', 10, {**metrics, 'reason': f'IS count too low ({avg_is_count:.1f}/well)'}
    if m_is < 10 and m_samp < 12:
        return 'GOOD', 10, metrics
    if m_is < 15 and m_samp < 18:
        return 'FAIR', 15, metrics
    return 'POOR', 25, metrics


def find_is_peaks(ch3):
    region = ch3[SCAN_START:SCAN_END]
    idx, props = find_peaks(region, height=500, distance=25, prominence=300)
    if len(idx) == 0:
        return [], []
    scans = idx + SCAN_START
    heights = props['peak_heights']
    # Filter out electronic spikes (FWHM < 3)
    real = []
    for s, h in zip(scans, heights):
        y = ch3[max(0, s - 20):min(len(ch3), s + 20)]
        pi = np.argmax(y)
        w, _, _, _ = peak_widths(y, np.array([pi]), rel_height=0.5)
        if w[0] >= 2.5:
            real.append((s, h))
    if not real:
        return [], []
    scans, heights = zip(*real)
    order = np.argsort(heights)[::-1][:N_IS_PEAKS]
    is_scans = sorted([int(scans[o]) for o in order])
    is_areas = []
    for s in is_scans:
        l = max(SCAN_START, s - 5)
        r = min(SCAN_END, s + 6)
        is_areas.append(float(np.trapz(ch3[l:r])))
    return is_scans, is_areas


def find_sample_peaks(ch2):
    region = ch2[SCAN_START:SCAN_END]
    baseline = np.median(region[:min(100, len(region))])
    peak_range = region.max() - baseline
    if peak_range < 50:
        return []
    thresh = baseline + peak_range * 0.15
    above = np.where(region > thresh)[0] + SCAN_START
    if len(above) == 0:
        return []
    # Use wider gap (diff > 15) since broad peaks may elevate adjacent scans
    groups = np.split(above, np.where(np.diff(above) > 15)[0] + 1)
    peaks = []
    for g in groups:
        if len(g) < 2:
            continue
        # If group spans > 20 scans, may contain multiple merged peaks
        if g[-1] - g[0] > 20:
            seg_start = g[0] - SCAN_START
            seg_end = g[-1] - SCAN_START + 1
            seg = region[seg_start:seg_end]
            local_max, _ = find_peaks(seg, distance=10,
                                      prominence=peak_range * 0.03)
            if len(local_max) > 0:
                for lm in local_max:
                    mi = lm + g[0]
                    l = max(0, mi - 8)
                    r = min(len(ch2), mi + 9)
                    peaks.append({'scan': int(mi), 'height': float(ch2[mi]),
                                  'area': float(ch2[l:r].sum())})
                continue
        # Default: single peak per group
        mi = g[np.argmax(region[g - SCAN_START])]
        l = max(0, mi - 8)
        r = min(len(ch2), mi + 9)
        peaks.append({'scan': int(mi), 'height': float(ch2[mi]),
                      'area': float(ch2[l:r].sum())})
    peaks.sort(key=lambda p: p['scan'])
    return peaks


def filter_peaks(peaks, ch2, is_scans):
    if not peaks:
        return []
    # 1. Remove primer (first peak if gap > 30 to next)
    if len(peaks) > 1 and (peaks[1]['scan'] - peaks[0]['scan']) > 30:
        peaks = peaks[1:]
    if not peaks:
        return []
    # 2. FWHM filter
    fwhm_keep = []
    for p in peaks:
        ps = p['scan']
        y = ch2[max(0, ps - 30):min(len(ch2), ps + 30)]
        pi = np.argmax(y)
        w, _, _, _ = peak_widths(y, np.array([pi]), rel_height=0.5)
        if 2.5 < w[0] < FWHM_LIMIT:
            fwhm_keep.append(p)
    if not fwhm_keep:
        return []
    # 3. IS matching: keep one peak per IS (5-25 scans before)
    if len(is_scans) < 2:
        return fwhm_keep
    matched = []
    used = set()
    for is_s in is_scans:
        best = None
        best_dist = 999
        for pi, p in enumerate(fwhm_keep):
            if pi in used:
                continue
            d = is_s - p['scan']
            if IS_MATCH_MIN <= d <= IS_MATCH_MAX:
                if d < best_dist:
                    best_dist = d
                    best = (pi, p)
        if best is not None:
            matched.append(best[1])
            used.add(best[0])
    # Fallback: if matching gave too few, use FWHM-filtered
    if len(matched) < 2:
        return fwhm_keep
    matched.sort(key=lambda p: p['scan'])
    return matched


def analyze_well(path):
    df = parse_rsd(path)
    ch2 = df['Channel2'].values.astype(float)
    ch3 = df['Channel3'].values.astype(float)
    actual_end = min(SCAN_END, len(ch2))
    if actual_end <= SCAN_START:
        return None
    is_scans, is_areas = find_is_peaks(ch3)
    raw = find_sample_peaks(ch2)
    filtered = filter_peaks(raw, ch2, is_scans)
    if not filtered:
        return {'well': os.path.basename(path)[:3], 'n': 0, 'scans': [], 'norms': [], 'mf': 0, 'label': 'no peaks'}
    smooth = savgol_filter(ch2[SCAN_START:actual_end], 7, 2)
    fitted = deconvolve_peaks(
        np.concatenate([ch2[:SCAN_START], smooth, ch2[actual_end:]]),
        filtered, scan_start=SCAN_START, scan_end=actual_end)
    mf, label = compute_mutant_fraction(fitted)
    norms = []
    for p in fitted:
        if is_scans:
            ni = np.argmin(np.abs(p['scan'] - np.array(is_scans)))
            norms.append(p['area'] / max(is_areas[ni], 1))
        else:
            norms.append(0)
    return {
        'well': os.path.basename(path)[:3],
        'n': len(fitted),
        'scans': [f'{p["scan"]:.0f}' for p in fitted],
        'norms': [f'{n:.2f}' for n in norms],
        'mf': mf,
        'label': label,
        'is_count': len(is_scans),
    }


def main():
    if len(sys.argv) < 2:
        runs = ['T1', 'T2', 'T3', 'T3b', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10']
        print("Usage: python analyze_plate.py <run> [--export <path>]")
        print(f"Available: {', '.join(runs)}")
        return
    run = sys.argv[1]
    base = '/media/per/Disk 2/electropherogram/RS1695'
    folder_map = {
        'T1': 'OY_rs1695_T1_230910Run02',
        'T2': 'OY_rs1695_T2_240910Run01',
        'T3': 'OY_rs1695_T3_160910Run01',
        'T3b': 'OY_rs1695_T3_160910Run02',
        'T4': 'OY_rs1695_T4_160910Run01',
        'T5': 'OY_rs1695_T5_270910Run01',
        'T6': 'OY_rs1695_T6_270910Run01',
        'T7': 'OY_rs1695_T7_270910Run01',
        'T8': 'OY_rs1695_T8_270910Run01',
        'T9': 'OY_rs1695_T9_270910Run01',
        'T10': 'OY_rs1695_T10_280910Run01',
    }
    folder = folder_map.get(run)
    if folder is None:
        print(f"Unknown run: {run}")
        return
    plate_dir = os.path.join(base, folder)
    if not os.path.isdir(plate_dir):
        print(f"Directory not found: {plate_dir}")
        return
    # Assess plate quality
    qual, fwhm_max, qm = assess_plate_quality(plate_dir)
    global FWHM_LIMIT
    FWHM_LIMIT = fwhm_max
    print(f'Plate quality: {qual}')
    if qm:
        print(f'  IS median FWHM={qm.get("is_median_fwhm","?"):}  sample median FWHM={qm.get("samp_median_fwhm","?"):}  avg IS/well={qm.get("avg_is_per_well","?"):.1f}')
        if 'reason' in qm:
            print(f'  Reason: {qm["reason"]}')
    print(f'  Using FWHM_MAX={fwhm_max}')
    wells = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]
    rows = []
    print(f"{'Well':5s} {'PK':3s} {'Scans':30s} {'Norm areas':35s} {'MF':6s} {'Status'}")
    print('-' * 90)
    for w in wells:
        path = os.path.join(plate_dir, f'{w}.rsd')
        if not os.path.exists(path):
            continue
        r = analyze_well(path)
        if r is None:
            print(f'{w:5s}  --  error')
            continue
        rows.append(r)
        scans = ','.join(r['scans'])
        norms = ','.join(r['norms'])
        print(f'{w:5s}  {r["n"]:2d}  {scans:30s}  {norms:35s}  {r["mf"]:6.3f}  {r["label"]}')
    homo = sum(1 for r in rows if r['n'] == 1)
    het4 = sum(1 for r in rows if r['n'] == 4)
    other = sum(1 for r in rows if r['n'] not in (1, 4))
    print(f'\nSummary: {homo} homozygous, {het4} het (4pk), {other} other/ambiguous')
    # Export CSV
    import csv as csvmod
    export_path = None
    if '--export' in sys.argv:
        ei = sys.argv.index('--export')
        if ei + 1 < len(sys.argv):
            export_path = sys.argv[ei + 1]
    if export_path:
        with open(export_path, 'w', newline='') as f:
            wr = csvmod.writer(f)
            wr.writerow(['# Plate', run, 'Quality', qual, 'FWHM_MAX', fwhm_max])
            if qm:
                wr.writerow(['# IS_median_FWHM', qm.get('is_median_fwhm', ''),
                             'Samp_median_FWHM', qm.get('samp_median_fwhm', ''),
                             'IS_per_well', f'{qm.get("avg_is_per_well", ""):.1f}'])
            wr.writerow(['Well', 'N_Peaks', 'MF', 'Status', 'Scans', 'Norm_Areas'])
            for r in rows:
                mf_str = f'{r["mf"]:.4f}'
                wr.writerow([r['well'], r['n'], mf_str, r['label'],
                             ';'.join(r['scans']), ';'.join(r['norms'])])
        print(f'Exported to {export_path}')


if __name__ == '__main__':
    main()
