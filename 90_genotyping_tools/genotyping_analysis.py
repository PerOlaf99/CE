"""Genotyping / heteroduplex analysis for fragment analysis .rsd data.

Chemistry: GT DyeSet2 (ROX=FAM=NED=HEX)
  Ch1 = ROX (size standard)
  Ch2 = FAM (sample)
  Ch3 = NED (IS)
  Ch4 = HEX (overlap)
"""
import sys, os, argparse
import numpy as np
import pandas as pd
from extract_training_data import parse_rsd
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks, savgol_filter
from scipy.optimize import curve_fit

# ── Peak detection ──────────────────────────────────────────────────

def find_peaks_in_region(trace, scan_start=1500, scan_end=1900,
                          height_ratio=0.15, min_gap=6, broad_split=True):
    """Find peaks via threshold grouping, optionally splitting broad groups.

    1. Group consecutive scans above adaptive threshold.
    2. Split any group wider than 50 scans using fine-scale peak detection
       (to resolve peaks on elevated tails, e.g. A02).
    """
    scan_end = min(scan_end, len(trace))
    if scan_end <= scan_start:
        return []
    region = trace[scan_start:scan_end].astype(float)

    noise_floor = np.median(region[:min(100, len(region))])
    peak_valley = region.max() - noise_floor
    if peak_valley < 1:
        return []
    threshold = noise_floor + peak_valley * height_ratio

    above = np.where(region > threshold)[0] + scan_start
    if len(above) == 0:
        return []

    groups = np.split(above, np.where(np.diff(above) > min_gap)[0] + 1)
    result = []

    for g in groups:
        if len(g) < 2:
            continue
        width = g[-1] - g[0]
        if not broad_split or width <= 50:
            # Compact group → single peak
            max_idx = g[trace[g].argmax()]
            area = float(trace[g].sum())
            result.append({
                'scan': int(max_idx),
                'height': float(trace[max_idx]),
                'area': area,
                'left': int(g[0]),
                'right': int(g[-1]),
                'n_points': len(g),
            })
        else:
            # Broad group → split via prominence-based find_peaks
            sub_region = region[g[0]-scan_start:g[-1]-scan_start+1]
            sub_range = sub_region.max() - sub_region.min()
            sub_peaks_idx, _ = find_peaks(sub_region, distance=min_gap * 2,
                                           prominence=sub_range * 0.05,
                                           height=sub_region.max() * 0.15)

            if len(sub_peaks_idx) < 2:
                # Single dominant peak → keep as one
                max_idx = g[trace[g].argmax()]
                area = float(trace[g].sum())
                result.append({
                    'scan': int(max_idx),
                    'height': float(trace[max_idx]),
                    'area': area,
                    'left': int(g[0]),
                    'right': int(g[-1]),
                    'n_points': len(g),
                })
            else:
                for idx in sub_peaks_idx:
                    p = g[0] + idx
                    h = trace[p]
                    tleft = max(0, idx - 8)
                    tright = min(len(sub_region), idx + 9)
                    area = float(np.trapz(sub_region[tleft:tright]))
                    result.append({
                        'scan': int(p),
                        'height': float(h),
                        'area': area,
                        'left': g[0] + tleft,
                        'right': g[0] + tright - 1,
                        'n_points': tright - tleft,
                    })

    result.sort(key=lambda p: p['scan'])
    return result


def refine_peaks(peaks, trace, min_rel_height=0.15, merge_dist=3):
    """Refine peak list: merge Taq-A doublets and remove noise.

    - Merges peaks within merge_dist scans, keeping the taller one
      and summing areas.
    - Removes peaks with height < min_rel_height * max_height.
    """
    if not peaks:
        return []

    peaks = sorted(peaks, key=lambda p: p['scan'])

    # Merge nearby doublets
    merged = []
    current = peaks[0].copy()
    for p in peaks[1:]:
        if p['scan'] - current['scan'] <= merge_dist:
            # Merge: keep taller peak's scan, sum areas
            if p['height'] > current['height']:
                current['scan'] = p['scan']
                current['height'] = p['height']
            current['area'] += p['area']
            current['right'] = max(current['right'], p['right'])
            current['n_points'] += p['n_points']
        else:
            merged.append(current)
            current = p.copy()
    merged.append(current)

    # Filter small noise
    max_h = max(p['height'] for p in merged)
    return [p for p in merged if p['height'] >= min_rel_height * max_h]

def gaussian(x, amp, mu, sigma):
    return amp * np.exp(-0.5 * ((x - mu) / sigma) ** 2)


def deconvolve_peaks(trace, peaks, sigma_guess=3.0,
                      scan_start=1500, scan_end=1900):
    """Fit Gaussian mixture to overlapping peaks."""
    scan_end = min(scan_end, len(trace))
    if scan_end <= scan_start:
        return peaks
    x = np.arange(scan_start, scan_end)
    y = trace[x]

    n = len(peaks)
    if n == 0:
        return []

    # Initial params: amplitude, mu, sigma for each peak
    bounds_low = []
    bounds_high = []
    p0 = []
    for p in peaks:
        p0.extend([p['height'], p['scan'], sigma_guess])
        bounds_low.extend([0, scan_start, 0.5])
        bounds_high.extend([y.max() * 2, scan_end, 10])

    try:
        popt, _ = curve_fit(
            lambda x, *p: sum(gaussian(x, p[i*3], p[i*3+1], p[i*3+2]) for i in range(n)),
            x, y, p0=p0,
            bounds=(bounds_low, bounds_high),
            maxfev=5000,
        )

        fitted = []
        for i in range(n):
            amp = popt[i*3]
            mu = popt[i*3+1]
            sigma = abs(popt[i*3+2])
            area = amp * sigma * np.sqrt(2 * np.pi)
            fitted.append({
                'scan': mu,
                'height': amp,
                'area': area,
                'sigma': sigma,
                'fwhm': 2.355 * sigma,
            })
        return sorted(fitted, key=lambda p: p['scan'])
    except Exception:
        return peaks


# ── Mutant fraction ──────────────────────────────────────────────────

def compute_mutant_fraction(peaks_fitted):
    """Compute mutant fraction from 1, 3, or 4 peak pattern.

    For rs1695 heteroduplex analysis:
      - 1 peak → homozygous (MF=0 or MF=1)
      - 3 peaks → heterozygous with imbalance (MF<0.5)
      - 4 peaks → balanced heterozygous (MF~0.5)

    Peak order (by elution):
      Typically: homo-WT, homo-Mut, hetero-1, hetero-2
    But this depends on the specific mutation.

    Model: After denaturation and random reannealing of WT and Mut strands
    at proportion p (WT) and 1-p (Mut):
      - WT/WT homoduplex: p²
      - Mut/Mut homoduplex: (1-p)²
      - WT/Mut + Mut/WT heteroduplexes: 2p(1-p)
    
    For 4 peaks (assuming equal detectability):
      - Let a0 = first peak area (assigned to WT/WT homo)
      - Let a3 = last peak area (assigned to Mut/Mut homo)
      - Let a1, a2 = middle peaks (heteroduplexes)
      - MF = sqrt(a3/total)  [since a3/total = (1-p)²]
      - or MF = 1 - sqrt(a0/total)
    For simplicity: MF ~ sum of last 3 / total (approximation)
    """
    n = len(peaks_fitted)
    total_area = sum(p['area'] for p in peaks_fitted)
    if total_area <= 0:
        return 0.0, "no signal"

    if n == 0:
        return 0.0, "no peaks"

    if n == 1:
        return 0.0, "homozygous (1 peak)"

    if n == 2:
        # Two peaks could be:
        # - Homozygous with peak splitting → MF ≈ 0
        # - Near-homozygous with tiny hetero peak → MF ≈ 0
        # Check if one peak is much smaller
        small_ratio = min(p['area'] for p in peaks_fitted) / total_area
        if small_ratio < 0.2:
            return 0.0, f"homozygous (2 peaks, noise)"
        else:
            return small_ratio, f"het-like (2 peaks)"

    if n == 3:
        # 3 peaks: low mutant fraction
        # The smallest peak is likely the Mut/Mut homo or one hetero is missing
        # MF ≈ (total - largest_peak) / total
        areas = sorted([p['area'] for p in peaks_fitted], reverse=True)
        mf = (areas[1] + areas[2]) / total_area
        return min(mf, 1.0), "low MF (3 peaks)"

    if n >= 4:
        # 4+ peaks: take top 4 by height, rest is noise
        sorted_p = sorted(peaks_fitted, key=lambda p: p['height'], reverse=True)[:4]
        sorted_p.sort(key=lambda p: p['scan'])
        total = sum(p['area'] for p in sorted_p)
        if total <= 0:
            return 0.0, "no signal"
        # In elution order: [WT(-A), WT(+A), MUT(-A), MUT(+A)]
        # or: [MUT(-A), MUT(+A), WT(-A), WT(+A)] — orientation unknown
        # MF = smaller pair / total  (which pair is the variant)
        wt = sorted_p[0]['area'] + sorted_p[1]['area']
        mut = sorted_p[2]['area'] + sorted_p[3]['area']
        # The variant is whichever pair has smaller total area (minor allele)
        mf = min(wt, mut) / total
        return mf, f"het ({n} peaks)"
    
    return 0.0, "unknown"


# ── Main analysis ───────────────────────────────────────────────────

def analyze_well(base_dir, well, scan_start=1500, scan_end=1900):
    """Analyze a single well and return results."""
    path = os.path.join(base_dir, f"{well}.rsd")
    if not os.path.exists(path):
        return None

    df = parse_rsd(path)
    ch2 = df['Channel2'].values  # FAM = sample
    ch3 = df['Channel3'].values  # NED = IS
    ch1 = df['Channel1'].values  # ROX = size standard

    scan_end = min(scan_end, len(ch2))
    if scan_end <= scan_start:
        return None

    # Find IS peak(s) in Ch3 (NED) — use lower threshold for consistent IS area
    is_peaks = find_peaks_in_region(ch3, scan_start=scan_start, scan_end=scan_end,
                                     height_ratio=0.08, broad_split=False)
    is_peaks = refine_peaks(is_peaks, ch3, min_rel_height=0.1)
    is_area = is_peaks[0]['area'] if is_peaks else 0

    # Find sample peaks in Ch2 (FAM)
    raw_peaks = find_peaks_in_region(ch2, scan_start=scan_start, scan_end=scan_end)

    raw_peaks = refine_peaks(raw_peaks, ch2, min_rel_height=0.15)

    if not raw_peaks:
        return {
            'well': well, 'n_scans': len(df),
            'n_peaks_raw': 0, 'n_peaks_fitted': 0,
            'is_area': is_area, 'is_scan': is_peaks[0]['scan'] if is_peaks else 0,
            'peak_scans': [], 'peak_areas_raw': [], 'peak_areas_fitted': [],
            'peak_heights': [],
            'mf': 0, 'mf_label': "no peaks",
            'norm_area': [], 'error': None,
        }

    # Smooth and deconvolve
    actual_end = min(scan_end, len(ch2))
    smooth = savgol_filter(ch2[scan_start:actual_end], window_length=7, polyorder=2)
    fitted = deconvolve_peaks(np.concatenate([ch2[:scan_start], smooth, ch2[actual_end:]]),
                               raw_peaks, scan_start=scan_start, scan_end=actual_end)

    mf, label = compute_mutant_fraction(fitted)

    # Normalize to IS
    norm_areas = [p['area'] / is_area if is_area > 0 else 0 for p in fitted]

    return {
        'well': well,
        'n_scans': len(df),
        'n_peaks_raw': len(raw_peaks),
        'n_peaks_fitted': len(fitted),
        'is_area': is_area,
        'is_scan': is_peaks[0]['scan'] if is_peaks else 0,
        'peak_scans': [float(p['scan']) for p in fitted],
        'peak_areas_raw': [p['area'] for p in raw_peaks],
        'peak_areas_fitted': [p['area'] for p in fitted],
        'peak_heights': [p['height'] for p in fitted],
        'mf': mf,
        'mf_label': label,
        'norm_area': norm_areas,
        'raw_peaks': raw_peaks,
        'fitted_peaks': fitted,
    }


def analyze_plate(base_dir, scan_start=1500, scan_end=1900):
    """Analyze all 96 wells in a plate."""
    wells = [f'{r}{c:02d}' for r in 'ABCDEFGH' for c in range(1, 13)]
    results = []
    for well in wells:
        r = analyze_well(base_dir, well, scan_start, scan_end)
        if r:
            results.append(r)
    return results


def print_results(results):
    """Print analysis results table."""
    print(f"{'Well':5s} | {'Scans':5s} | {'#Pk':3s} | {'IS area':8s} | "
          f"{'Peak scans':30s} | {'Areas (norm)':40s} | {'MF':6s} | {'Status'}")
    print("-" * 110)
    for r in results:
        scans_fmt = ','.join([f'{s:.0f}' for s in r['peak_scans'][:6]])
        areas_fmt = ','.join([f'{a:.2f}' for a in r['norm_area'][:6]])
        print(f"{r['well']:5s} | {r['n_scans']:5d} | {r['n_peaks_fitted']:3d} | "
              f"{r['is_area']:8.0f} | {scans_fmt:30s} | {areas_fmt:40s} | "
              f"{r['mf']:.3f} | {r['mf_label']}")


def export_results(results, path):
    """Export results to CSV."""
    rows = []
    for r in results:
        rows.append({
            'well': r['well'],
            'n_scans': r['n_scans'],
            'n_peaks': r['n_peaks_fitted'],
            'is_area': r['is_area'],
            'is_scan': r['is_scan'],
            'peak_scans': ';'.join(str(round(s, 1)) for s in r['peak_scans']),
            'peak_areas_raw': ';'.join(str(round(a, 1)) for a in r['peak_areas_raw']),
            'peak_areas_fitted': ';'.join(str(round(a, 1)) for a in r['peak_areas_fitted']),
            'peak_heights': ';'.join(str(round(h, 1)) for h in r['peak_heights']),
            'norm_areas': ';'.join(str(round(a, 4)) for a in r['norm_area']),
            'mutant_fraction': r['mf'],
            'status': r['mf_label'],
        })
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    print(f"\nExported {len(rows)} rows to {path}")


# ── CLI ──────────────────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Genotyping/heteroduplex analysis')
    parser.add_argument('--dir', required=True, help='Directory with .rsd files')
    parser.add_argument('--start', type=int, default=1500, help='Scan start (default: 1500)')
    parser.add_argument('--end', type=int, default=1900, help='Scan end (default: 1900)')
    parser.add_argument('--export', help='Export CSV path')
    parser.add_argument('--wells', nargs='+', help='Specific wells (e.g., A01 B03)')
    args = parser.parse_args()

    if args.wells:
        results = []
        for w in args.wells:
            r = analyze_well(args.dir, w, args.start, args.end)
            if r:
                results.append(r)
    else:
        results = analyze_plate(args.dir, args.start, args.end)

    print_results(results)
    if args.export:
        export_results(results, args.export)
