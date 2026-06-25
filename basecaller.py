import numpy as np
import os

# Channel-to-base mappings per chemistry (Chemistry.ini)
# Key: channel_index (0-3) -> base letter
CHEMISTRY_MAP = {
    "ET Terminators":          {0: "T", 1: "G", 2: "C", 3: "A"},
    "ET Primers":              {0: "A", 1: "C", 2: "T", 3: "G"},
    "TSII-Version 2 Terminators": {0: "A", 1: "G", 2: "C", 3: "T"},
    "SNuPe Terminators":       {0: "A", 1: "G", 2: "C", 3: "T"},
    "ML Base Caller":          {},  # Uses trained CNN instead of channel mapping
}

BASE_QUAL_CHANNELS = ["Channel1", "Channel2", "Channel3", "Channel4"]
ML_LABELS = ['A', 'C', 'G', 'T']

# Path to the trained model (relative to this file)
MODEL_PATH = os.path.join(os.path.dirname(__file__), "base_caller_model.keras")

# Dye mobility adjustments (relative spacing in scans)
# These correct for different migration speeds of each dye label
# Values are approximate — varies with run conditions
MOBILITY_OFFSET = {
    "ET Terminators":          {0: -3, 1: -1, 2: 1, 3: 3},
    "ET Primers":              {0: 0, 1: 0, 2: 0, 3: 0},
    "TSII-Version 2 Terminators": {0: -2, 1: 0, 2: 1, 3: 3},
    "SNuPe Terminators":       {0: -2, 1: -1, 2: 2, 3: 3},
}



def _load_ml_model():
    import tensorflow as tf
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"ML model not found at {MODEL_PATH}. "
            f"Train it first with train_model.py"
        )
    return tf.keras.models.load_model(MODEL_PATH)


def basecall_ml(
    data,
    peaks,
    peak_channels,
    scan_values,
    chemistry="ML Base Caller",
    min_quality=10,
    model=None,
):
    if model is None:
        model = _load_ml_model()

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
    X_batch = []

    for peak_idx in peaks_sorted:
        if peak_idx < window or peak_idx >= n_scans - window:
            bases.append("N")
            qual_scores.append(0)
            positions.append(scan_values[peak_idx] if scan_values is not None else float(peak_idx))
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
            bases.append(base)
            qual_scores.append(qual)
            positions.append(
                scan_values[peak_idx] if scan_values is not None else float(peak_idx)
            )
            batch_idx += 1

    seq_lines = _format_sequence(positions, bases, qual_scores)

    return {
        "bases": bases,
        "qualities": qual_scores,
        "positions": positions,
        "sequence_lines": seq_lines,
        "sequence": "".join(bases),
        "chemistry": "ML Base Caller",
        "avg_quality": int(np.mean(qual_scores)) if qual_scores else 0,
        "n_count": sum(1 for b in bases if b == "N"),
        "total_calls": len(bases),
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


def _compute_quality(frac, data, ch_i, peak_idx):
    base_qual = int(round(min(frac * 100, 100)))
    if base_qual < 10:
        base_qual = 0
    return base_qual


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
