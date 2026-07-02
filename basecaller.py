import numpy as np
import os
import csv

# Channel-to-base mappings per chemistry (Chemistry.ini)
# Key: channel_index (0-3) -> base letter
CHEMISTRY_MAP = {
    "ET Terminators":          {0: "T", 1: "G", 2: "C", 3: "A"},
    "ET Primers":              {0: "A", 1: "C", 2: "T", 3: "G"},
    "TSII-Version 2 Terminators": {0: "A", 1: "G", 2: "C", 3: "T"},
    "SNuPe Terminators":       {0: "A", 1: "G", 2: "C", 3: "T"},
    "ML Base Caller":          {},  # Trained CNN on ESD-centered positions
    "ML Scan Caller":          {},  # Brute-force per-scan CNN with background class
    "Cimarron 3.12 (Python)":  {0: "T", 1: "G", 2: "C", 3: "A"},  # Spectral separation + classic peak detection
}

BASE_QUAL_CHANNELS = ["Channel1", "Channel2", "Channel3", "Channel4"]
ML_LABELS = ['A', 'C', 'G', 'T']
ML_LABELS_WITH_N = ['A', 'C', 'G', 'T', 'N']

# Path to the trained model (relative to this file)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "base_caller_model.keras")
MODEL_PATH_WITH_BG = os.path.join(os.path.dirname(__file__), "base_caller_model_with_bg.keras")
CONFIDENCE_CURVE_PATH = MODEL_PATH.replace('.keras', '_confidence.csv')

# Dye mobility adjustments (relative spacing in scans)
# These correct for different migration speeds of each dye label
# Values are approximate — varies with run conditions
MOBILITY_OFFSET = {
    "ET Terminators":          {0: -3, 1: -1, 2: 1, 3: 3},
    "ET Primers":              {0: 0, 1: 0, 2: 0, 3: 0},
    "TSII-Version 2 Terminators": {0: -2, 1: 0, 2: 1, 3: 3},
    "SNuPe Terminators":       {0: -2, 1: -1, 2: 2, 3: 3},
}

# ESD subdirectory name -> human-readable caller name mapping
# Maps the subdirectory names found in the MB4000/MB1000 folders to
# human-readable base caller names from Basecall.ini
ESD_CALLER_NAME_MAP = {
    # Cimarron 3.12 variants
    'Cp312': 'Cimarron 3.12',
    'Cimarron 3.12': 'Cimarron 3.12',
    # Cimarron 3.12 Aligned (beautify — aligns to reference)
    'Cp312_a': 'Cimarron 3.12 Aligned',
    'Cp312 Aligned': 'Cimarron 3.12 Aligned',
    # Cimarron 3.12 Even Spacing (printify — enforces uniform spacing)
    'Cp312_es': 'Cimarron 3.12 Even Spacing',
    'Cp312 Even Spacing': 'Cimarron 3.12 Even Spacing',
    # Cimarron 1.53 (beautify)
    'Cp1_530': 'Cimarron 1.53',
    'Cimarron 1.53': 'Cimarron 1.53',
    # Cimarron 1.53 Slim Phredify (phredify_noPuff)
    'Cp1_530_sl_ph': 'Cimarron 1.53 Slim Phredify',
    'Cimarron 1.53 Slim Phredify': 'Cimarron 1.53 Slim Phredify',
    # Molecular Dynamics (SQCR)
    'M': 'Molecular Dynamics',
    'Molecular Dynamics': 'Molecular Dynamics',
    # Fallback for full folder names like MB4000_M13_DT_Cp312_MD1
    'MB4000_M13_DT_Cp312_MD1': 'Cimarron 3.12',
    'MB4000_M13_DT_Cp312_a_MD1': 'Cimarron 3.12 Aligned',
    'MB4000_M13_DT_Cp312_es_MD1': 'Cimarron 3.12 Even Spacing',
    'MB4000_M13_DT_Cp1_530_MD1': 'Cimarron 1.53',
    'MB4000_M13_DT_Cp1_530_sl_ph_MD1': 'Cimarron 1.53 Slim Phredify',
    'MB4000_M13_DT_M_MD1': 'Molecular Dynamics',
    # MB1000 variants
    'MB1000_M13_DT_Cp312_MD1': 'Cimarron 3.12',
    'MB1000_M13_DT_Cp312_a_MD1': 'Cimarron 3.12 Aligned',
    'MB1000_M13_DT_Cp312_es_MD1': 'Cimarron 3.12 Even Spacing',
    'MB1000_M13_DT_Cp1_530_MD1': 'Cimarron 1.53',
    'MB1000_M13_DT_Cp1_530_sl_ph_MD1': 'Cimarron 1.53 Slim Phredify',
    'MB1000_M13_DT_M_MD1': 'Molecular Dynamics',
}


def esd_caller_display_name(subdir_name):
    """Convert an ESD subdirectory name to a human-readable caller name."""
    if subdir_name in ESD_CALLER_NAME_MAP:
        return ESD_CALLER_NAME_MAP[subdir_name]
    # Try to extract short name from full folder names
    parts = subdir_name.split('_')
    for i, p in enumerate(parts):
        if p in ('Cp312', 'Cp1', 'M') and i + 1 < len(parts):
            for j in range(i, len(parts)):
                candidate = '_'.join(parts[i:j + 1])
                if candidate in ESD_CALLER_NAME_MAP:
                    return ESD_CALLER_NAME_MAP[candidate]
        elif p == 'Cp1' and i + 2 < len(parts) and parts[i+1] == '530':
            for j in range(i, len(parts)):
                candidate = '_'.join(parts[i:j + 1])
                if candidate in ESD_CALLER_NAME_MAP:
                    return ESD_CALLER_NAME_MAP[candidate]
    return subdir_name


# ET terminators spectral separation matrix (approximate inverse)
# Rows = raw channels, columns = dye emissions
# [T, G, C, A] dye emission profiles
# Based on Cimarron 3.12 analysis
DEFAULT_SPEC_MATRIX = np.array([
    [0.85, 0.03, 0.05, 0.07],  # Ch1 (mainly T)
    [0.02, 0.88, 0.04, 0.06],  # Ch2 (mainly G)
    [0.06, 0.04, 0.86, 0.04],  # Ch3 (mainly C)
    [0.07, 0.05, 0.05, 0.83],  # Ch4 (mainly A)
], dtype=np.float64)



def _load_ml_model(path=None):
    import tensorflow as tf
    if path is None:
        path = MODEL_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"ML model not found at {path}. "
            f"Train it first with train_model.py"
        )
    return tf.keras.models.load_model(path)

def _load_confidence_curve():
    """Load confidence threshold vs accuracy data from training."""
    if not os.path.exists(CONFIDENCE_CURVE_PATH):
        return None
    results = []
    with open(CONFIDENCE_CURVE_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'threshold': float(row['threshold']),
                'accuracy': float(row['accuracy']),
                'coverage': float(row['coverage']),
                'n_calls': int(row['n_calls']),
            })
    return results

def _find_optimal_threshold(target_accuracy=0.98):
    """Find the lowest confidence threshold achieving target accuracy."""
    curve = _load_confidence_curve()
    if curve is None:
        return 0.5  # fallback default
    best = None
    for r in curve:
        if r['accuracy'] >= target_accuracy and r['coverage'] > 0:
            if best is None or r['threshold'] < best['threshold']:
                best = r
    if best is None:
        return 0.95  # fallback high threshold
    return best['threshold']


def basecall_ml(
    data,
    peaks,
    peak_channels,
    scan_values,
    chemistry="ML Base Caller",
    min_quality=10,
    model=None,
    auto_threshold=True,
    target_accuracy=0.98,
):
    if model is None:
        model = _load_ml_model()

    if auto_threshold:
        min_prob = _find_optimal_threshold(target_accuracy)
        # Use min_prob as the effective confidence threshold, mapping to quality 0-100
        min_quality = max(min_quality, int(round(min_prob * 100)))

    if len(peaks) == 0:
        return [], ""

    sorted_idx = np.argsort(peaks)
    peaks_sorted = peaks[sorted_idx]
    channels_sorted = [peak_channels[i] for i in sorted_idx]

    ch = data[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values
    n_scans = len(ch)
    window = 15

    bases = []
    qual_scores = []
    positions = []
    probabilities = []
    X_batch = []

    for peak_idx in peaks_sorted:
        if peak_idx < window or peak_idx >= n_scans - window:
            bases.append("N")
            qual_scores.append(0)
            positions.append(scan_values[peak_idx] if scan_values is not None else float(peak_idx))
            probabilities.append(0.0)
            continue
        window_data = ch[peak_idx - window:peak_idx + window + 1, :]
        X_batch.append(window_data)

    if X_batch:
        X_batch = np.array(X_batch, dtype=np.float32)
        X_mean = X_batch.mean(axis=(1,), keepdims=True)
        X_std = X_batch.std(axis=(1,), keepdims=True) + 1e-8
        X_batch = (X_batch - X_mean) / X_std

        preds = model.predict(X_batch, verbose=0)
        pred_classes = preds.argmax(axis=1)
        pred_probs = preds.max(axis=1)

        batch_idx = 0
        for peak_idx in peaks_sorted:
            if peak_idx < window or peak_idx >= n_scans - window:
                continue
            cls = pred_classes[batch_idx]
            prob = pred_probs[batch_idx]
            base = ML_LABELS[cls] if cls < 4 else "N"
            qual = int(round(prob * 100))
            if qual < min_quality:
                base = "N"
                qual = min_quality
            bases.append(base)
            qual_scores.append(qual)
            probabilities.append(float(prob))
            positions.append(
                scan_values[peak_idx] if scan_values is not None else float(peak_idx)
            )
            batch_idx += 1

    seq_lines = _format_sequence(positions, bases, qual_scores)

    return {
        "bases": bases,
        "qualities": qual_scores,
        "positions": positions,
        "probabilities": probabilities,
        "sequence_lines": seq_lines,
        "sequence": "".join(bases),
        "chemistry": "ML Base Caller",
        "avg_quality": int(np.mean(qual_scores)) if qual_scores else 0,
        "n_count": sum(1 for b in bases if b == "N"),
        "total_calls": len(bases),
        "auto_threshold": min_quality / 100.0,
    }


def basecall(
    data,
    peaks,
    peak_channels,
    scan_values,
    chemistry="ET Terminators",
    min_quality=10,
):
    ch_map = CHEMISTRY_MAP.get(chemistry, CHEMISTRY_MAP["ET Terminators"])
    mob = MOBILITY_OFFSET.get(chemistry, MOBILITY_OFFSET["ET Terminators"])

    if len(peaks) == 0:
        return [], ""

    sorted_idx = np.argsort(peaks)
    peaks_sorted = peaks[sorted_idx]
    channels_sorted = [peak_channels[i] for i in sorted_idx]

    bases = []
    qual_scores = []
    positions = []

    for peak_idx, ch_name in zip(peaks_sorted, channels_sorted):
        if ch_name not in BASE_QUAL_CHANNELS:
            continue
        ch_i = BASE_QUAL_CHANNELS.index(ch_name)
        base = ch_map.get(ch_i, "N")
        scan = scan_values[peak_idx] if scan_values is not None else float(peak_idx)

        # Build 4-channel intensity vector at this peak
        intensities = []
        for ch in BASE_QUAL_CHANNELS:
            if ch in data.columns:
                intensities.append(data[ch].iloc[peak_idx])
            else:
                intensities.append(0.0)
        intensities = np.array(intensities, dtype=np.float64)
        total = intensities.sum()
        if total <= 0:
            qual = 0
        else:
            # Peak channel fraction of total signal
            frac = intensities[ch_i] / total
            qual = _compute_quality(frac, data, ch_i, peak_idx)

        if qual >= min_quality:
            bases.append(base)
        else:
            bases.append("N")
        qual_scores.append(qual)
        positions.append(scan)

    # Build padded sequence text
    seq_lines = _format_sequence(positions, bases, qual_scores)

    return {
        "bases": bases,
        "qualities": qual_scores,
        "positions": positions,
        "sequence_lines": seq_lines,
        "sequence": "".join(bases),
        "chemistry": chemistry,
        "avg_quality": int(np.mean(qual_scores)) if qual_scores else 0,
        "n_count": sum(1 for b in bases if b == "N"),
        "total_calls": len(bases),
    }


def _estimate_noise(trace, n_first=200):
    """Estimate noise level from first N scans of a 4-channel trace."""
    region = trace[:min(n_first, len(trace))]
    return np.std(region, axis=0) + 1e-8


def _integrate_peak(clean, peak_idx, half_width=3):
    """Integrate spectral unmixed signal over a window around the peak."""
    start = max(0, peak_idx - half_width)
    end = min(len(clean), peak_idx + half_width + 1)
    window = clean[start:end]
    return window.sum(axis=0)


def _attenuate_outliers(signal, threshold=5.0, window=51):
    """Attenuate outlier spikes (Cimarron's AttenOutliers).
    
    Clips values deviating more than `threshold` * local MAD from median.
    """
    half = window // 2
    result = signal.copy().astype(np.float64)
    for i in range(len(signal)):
        start = max(0, i - half)
        end = min(len(signal), i + half + 1)
        seg = signal[start:end]
        med = np.median(seg)
        mad = np.median(np.abs(seg - med)) + 1e-8
        upper = med + threshold * mad
        lower = med - threshold * mad
        result[i] = np.clip(result[i], lower, upper)
    return result


def _validate_spectral_matrix(matrix):
    """Cimarron's spec separation validation (diagonal >= 0.7, cross-talk check)."""
    diag = np.diag(matrix)
    if np.any(diag < 0.7):
        return False, list(np.where(diag < 0.7)[0])
    # Cross-talk: off-diagonal elements should not exceed diagonal
    for i in range(4):
        row_max_off = np.max(np.delete(matrix[i], i))
        if row_max_off > diag[i] * 0.5:
            return False, [i]
    return True, []


def _mobility_search(clean, peak_idx, mob_candidates, half_width=2):
    """Cimarron's Mobility::search — find best mobility offset.
    
    Tries each mobility offset and picks the one giving the most
    dominant single-channel unmixed signal.
    """
    n_scans = len(clean)
    best_score = -1
    best_intensities = None
    best_offset = 0
    for offset in mob_candidates:
        idx = int(np.clip(peak_idx + offset, half_width, n_scans - 1 - half_width))
        intensities = _integrate_peak(clean, idx, half_width)
        total = intensities.sum()
        if total <= 0:
            continue
        frac = intensities.max() / total
        score = frac
        if score > best_score:
            best_score = score
            best_intensities = intensities
            best_offset = offset
    if best_intensities is None:
        idx = int(np.clip(peak_idx, half_width, n_scans - 1 - half_width))
        best_intensities = _integrate_peak(clean, idx, half_width)
    return best_intensities, best_offset


def _gap_check(peak_positions, max_gap_factor=3.0, min_gap=2):
    """Check for abnormal gaps in peak spacing (Cimarron's gapcheck).
    
    Returns indices of peaks where the gap to the next peak is
    more than max_gap_factor times the local median spacing.
    """
    if len(peak_positions) < 3:
        return []
    gaps = np.diff(peak_positions)
    if len(gaps) == 0:
        return []
    median_gap = np.median(gaps)
    if median_gap < 1:
        return []
    abnormal = []
    for i, g in enumerate(gaps):
        if g > median_gap * max_gap_factor and g > min_gap:
            abnormal.append(i)
    return abnormal


def basecall_cimarron(
    data,
    peaks,
    peak_channels,
    scan_values,
    chemistry="Cimarron 3.12 (Python)",
    min_quality=10,
    spectral_matrix=None,
    variant=None,
):
    """Cimarron-like base caller using spectral separation + peak picking.

    Applies spectral separation inverse matrix to unmix channels,
    then calls bases from the dominant channel at each peak position.
    Incorporates mobility shift correction, peak-width integration,
    and SNR-based quality scoring inspired by Cimarron 3.12 DLL analysis.

    Variants (matching the Cimarron 3.12 DLL post-processing modes):
      None (default)     — standard (CimBC030012_noPuff)
      'aligned'          — align peaks to reference grid (CimBC030012_beautify)
      'even_spacing'     — enforce even spacing (CimBC030012_printify)
      'phredify'         — Cimarron 1.53 slim phredify
    """
    if spectral_matrix is None:
        spectral_matrix = DEFAULT_SPEC_MATRIX

    # Validate spectral matrix (Cimarron checks diag >= 0.7)
    valid, bad_cols = _validate_spectral_matrix(spectral_matrix)
    if not valid:
        raise ValueError(
            f"Spectral separation matrix validation failed: "
            f"diagonal element(s) below 0.7 at indices {bad_cols}. "
            f"{'Cross-talk exceeds 50% of diagonal.' if not valid else ''}"
        )

    ch_map = CHEMISTRY_MAP.get("ET Terminators", {0: "T", 1: "G", 2: "C", 3: "A"})

    if len(peaks) == 0:
        return {
            "bases": [], "qualities": [], "positions": [],
            "sequence_lines": [], "sequence": "",
            "chemistry": chemistry,
            "avg_quality": 0, "n_count": 0, "total_calls": 0,
        }

    # Preprocess: attenuate outliers in each channel (Cimarron's AttenOutliers)
    ch_cols = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
    raw = data[ch_cols].values.astype(np.float64)
    for i in range(4):
        raw[:, i] = _attenuate_outliers(raw[:, i])

    # Apply spectral separation
    inv_mat = np.linalg.inv(spectral_matrix)
    clean = raw @ inv_mat.T
    clean = np.maximum(clean, 0.0)

    # Estimate noise per dye channel
    noise = _estimate_noise(clean)

    sorted_idx = np.argsort(peaks)
    peaks_sorted = peaks[sorted_idx]
    channels_sorted = [peak_channels[i] for i in sorted_idx]

    # Mobility offset search ranges (Cimarron's Mobility::search)
    # Each channel has a different mobility. We try a range and pick best.
    mob_candidates = {
        0: [-5, -4, -3, -2, -1],  # Channel1 (T) — fastest
        1: [-3, -2, -1, 0, 1],     # Channel2 (G)
        2: [-1, 0, 1, 2, 3],       # Channel3 (C)
        3: [1, 2, 3, 4, 5],        # Channel4 (A) — slowest
    }

    bases = []
    qual_scores = []
    positions = []
    all_intensities = []

    for peak_idx, ch_name in zip(peaks_sorted, channels_sorted):
        if ch_name not in BASE_QUAL_CHANNELS:
            continue
        ch_i = BASE_QUAL_CHANNELS.index(ch_name)

        # Adaptive mobility search
        candidates = mob_candidates.get(ch_i, [-3, -1, 0, 1, 3])
        intensities, best_offset = _mobility_search(clean, peak_idx, candidates)
        total = intensities.sum()

        if total <= 0:
            qual = 0
            dominant = ch_i
        else:
            dominant = np.argmax(intensities)
            frac = intensities[dominant] / total
            peak_signal = intensities[dominant]
            snr = peak_signal / noise[dominant]
            # BandStat-inspired quality: dominance + SNR + signal strength relative to noise
            dom_score = frac * 100
            snr_score = min(snr * 5, 100)
            # Signal strength relative to baseline noise
            amp_score = min((peak_signal / noise[dominant]) * 10, 100)
            qual = int(round(0.5 * dom_score + 0.3 * snr_score + 0.2 * amp_score))
            qual = min(qual, 100)

        base = ch_map.get(dominant, "N")
        if qual < min_quality:
            base = "N"

        scan = scan_values[peak_idx] if scan_values is not None else float(peak_idx)
        bases.append(base)
        qual_scores.append(qual)
        positions.append(scan)
        all_intensities.append(intensities)

    # Gap check: detect abnormal peak spacing (Cimarron's gapcheck/omitokn)
    gap_flags = _gap_check(positions)
    for i in gap_flags:
        if i < len(qual_scores):
            qual_scores[i] = max(qual_scores[i] // 2, 0)
            if qual_scores[i] < min_quality:
                bases[i] = "N"

    # Variant-specific post-processing
    positions_arr = np.array(positions, dtype=float)
    if variant == 'aligned':
        # CimBC030012_beautify: align dominant peaks to nearest integer positions
        for i in range(len(positions)):
            if bases[i] != 'N' and qual_scores[i] >= 30:
                positions[i] = round(positions[i])
    elif variant == 'even_spacing':
        # CimBC030012_printify: enforce minimum spacing
        filtered_pos = []
        filtered_bases = []
        filtered_qual = []
        last_pos = -float('inf')
        min_spacing = max(2, int(np.median(np.diff(sorted(positions)))) // 2)
        for i in np.argsort(positions):
            p = positions[i]
            if p - last_pos >= min_spacing:
                filtered_pos.append(p)
                filtered_bases.append(bases[i])
                filtered_qual.append(qual_scores[i])
                last_pos = p
        positions = filtered_pos
        bases = filtered_bases
        qual_scores = filtered_qual

    seq_lines = _format_sequence(positions, bases, qual_scores)
    return {
        "bases": bases,
        "qualities": qual_scores,
        "positions": positions,
        "sequence_lines": seq_lines,
        "sequence": "".join(bases),
        "chemistry": chemistry,
        "avg_quality": int(np.mean(qual_scores)) if qual_scores else 0,
        "n_count": sum(1 for b in bases if b == "N"),
        "total_calls": len(bases),
        "variant": variant,
    }


def _compute_quality(frac, data, ch_i, peak_idx):
    base_qual = int(round(min(frac * 100, 100)))
    if base_qual < 10:
        base_qual = 0
    return base_qual


def export_bases_csv(results, path):
    """Export base calling results to CSV.
    
    results: dict of well -> basecall result dict
    """
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Well', 'Position', 'Base', 'Quality', 'Probability'])
        for well in sorted(results.keys()):
            r = results[well]
            probs = r.get('probabilities', [None] * len(r['bases']))
            for pos, base, qual, prob in zip(
                r['positions'], r['bases'], r['qualities'], probs
            ):
                prob_str = f"{prob:.4f}" if prob is not None else ""
                writer.writerow([well, int(pos), base, qual, prob_str])


def export_bases_fasta(results, path):
    """Export base calling results to FASTA."""
    with open(path, 'w') as f:
        for well in sorted(results.keys()):
            r = results[well]
            f.write(f">{well} chemistry={r['chemistry']} avg_qual={r['avg_quality']}\n")
            seq = r['sequence']
            for i in range(0, len(seq), 80):
                f.write(seq[i:i+80] + "\n")


def export_bases_summary(results, path):
    """Export a summary table of base calling stats."""
    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Well', 'Chemistry', 'Total Calls', 'N Count',
                         'N Rate (%)', 'Avg Quality', 'Sequence Length'])
        for well in sorted(results.keys()):
            r = results[well]
            n_rate = r['n_count'] / r['total_calls'] * 100 if r['total_calls'] > 0 else 0
            writer.writerow([
                well, r['chemistry'], r['total_calls'], r['n_count'],
                f"{n_rate:.1f}", r['avg_quality'], len(r['sequence']),
            ])


def basecall_ml_scan(
    data,
    scan_values,
    chemistry="ML Scan Caller",
    min_confidence=0.8,
    min_spacing=3,
    model=None,
):
    """Brute-force base calling by scanning every position with the ML model.

    Runs the model on every scan position, filters by confidence,
    then decodes runs of consecutive same-base predictions into
    individual base calls (taking the highest-confidence position
    in each run). No explicit peak detection needed.

    The model must have been trained with background (N) class so
    it learns to output low confidence / N class at non-peak positions.

    Returns: same dict format as basecall_ml()
    """
    if model is None:
        path = MODEL_PATH_WITH_BG
        import tensorflow as tf
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Model with background class not found at {path}. "
                f"Train it first with: python train_model.py --include-background"
            )
        model = tf.keras.models.load_model(path)

    ch = data[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values
    n_scans = len(ch)
    window = 15

    if n_scans < window * 2 + 1:
        return {
            "bases": [], "qualities": [], "positions": [],
            "sequence_lines": [], "sequence": "",
            "chemistry": chemistry,
            "avg_quality": 0, "n_count": 0, "total_calls": 0,
        }

    # Batch predict on all valid scan positions
    valid_positions = np.arange(window, n_scans - window)
    X = np.array([ch[p - window:p + window + 1] for p in valid_positions], dtype=np.float32)
    mu = X.mean(axis=(1,), keepdims=True)
    X = (X - mu) / (X.std(axis=(1,), keepdims=True) + 1e-8)
    preds = model.predict(X, verbose=0)
    classes = preds.argmax(axis=1)
    confs = preds.max(axis=1)

    # Filter: keep only non-N predictions above confidence threshold
    is_base = (classes < 4) & (confs >= min_confidence)

    # Decode runs: consecutive same-base predictions → one base call
    bases = []
    qual_scores = []
    positions = []

    i = 0
    while i < len(valid_positions):
        if not is_base[i]:
            i += 1
            continue

        # Start of a run
        base_cls = classes[i]
        run_start = i

        # Find end of this run (different base, N, or low confidence)
        j = i
        while j < len(valid_positions) and is_base[j] and classes[j] == base_cls:
            j += 1
        run_end = j - 1

        # Find the position with highest confidence in this run
        run_confs = confs[run_start:run_end + 1]
        best_idx = run_start + run_confs.argmax()
        best_pos = valid_positions[best_idx]
        best_conf = run_confs.max()
        best_base = ML_LABELS[base_cls]

        # Record the base call
        bases.append(best_base)
        qual_scores.append(int(round(best_conf * 100)))
        positions.append(
            scan_values[best_pos] if scan_values is not None else float(best_pos)
        )

        # Enforce minimum spacing: skip ahead
        # Calculate position in scan indices to enforce spacing
        next_scan = best_pos + min_spacing
        # Find the next valid position index >= next_scan
        i = np.searchsorted(valid_positions, next_scan)

    seq_lines = _format_sequence(positions, bases, qual_scores)
    n_count = sum(1 for b in bases if b == 'N')

    return {
        "bases": bases,
        "qualities": qual_scores,
        "positions": positions,
        "sequence_lines": seq_lines,
        "sequence": "".join(bases),
        "chemistry": chemistry,
        "avg_quality": int(np.mean(qual_scores)) if qual_scores else 0,
        "n_count": n_count,
        "total_calls": len(bases),
    }


def _format_sequence(positions, bases, qual_scores):
    lines = []
    n = len(bases)
    for i in range(0, n, 60):
        chunk = "".join(bases[i:i + 60])
        qual_chunk = "".join(str(min(q // 10, 9)) for q in qual_scores[i:i + 60])
        pos_start = int(positions[i]) if positions else 0
        pos_end = int(positions[min(i + 59, n - 1)]) if positions else 0
        lines.append(f"{pos_start:6d}  {chunk}")
        lines.append(f"{'':6s}  {qual_chunk}")
    return lines
