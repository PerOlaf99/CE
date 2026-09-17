"""CNN ensemble confidence scoring for Sanger basecalling.

Wraps the trained TensorFlow CNN models to produce per-base softmax
probabilities (pmax) at peak positions, which map to Phred Q-scores.

The CNN takes a 31x4 window centered on each peak scan position from
the raw trace, applies per-sample z-score normalization, and outputs
a 5-class softmax (A/C/G/T/N).  Multiple models are averaged (ensemble).

Usage:
    from cnn_confidence import CNNEstimator
    est = CNNEstimator()          # loads models once (~2s)
    pmax = est.predict_pmax(raw_traces, peak_scans)
    q_scores = est.phred(pmax)
"""
import os
import glob
import numpy as np

os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '3')

WINDOW = 15  # half-window → 31 samples total
LABELS = 'ACGT'
DEFAULT_MODEL_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', '02_denovo_cnn_ensemble_91.53pct')

_singleton = None


V4_MODELS = [
    'base_caller_model_v4_clean.keras',
    'base_caller_model_v4_pos.keras',
    'base_caller_model_v4_pos_b.keras',
]


def _load_models(model_dir=None):
    """Load v4 ensemble models, falling back to all models if v4 missing."""
    import tensorflow as tf
    if model_dir is None:
        model_dir = DEFAULT_MODEL_DIR
    models = []
    v4_paths = [os.path.join(model_dir, f) for f in V4_MODELS]
    glob_paths = sorted(glob.glob(os.path.join(model_dir, 'base_caller_model*.keras')))
    candidates = v4_paths if all(os.path.exists(p) for p in v4_paths) else glob_paths
    for p in candidates:
        try:
            m = tf.keras.models.load_model(p, compile=False)
            if m.output_shape[-1] in (4, 5):
                models.append(m)
        except Exception:
            pass
    return models


def _build_windows(ch_raw, scans, window=WINDOW):
    """Extract 2*window+1 x 4 windows centered on each scan position.

    ch_raw: (N, 4) float64 raw trace
    scans: array of int scan positions

    Returns: (len(scans), 2*window+1, 4) float32, z-score normalized per-sample.
    """
    n = len(ch_raw)
    w = window
    scans = np.asarray(scans, dtype=np.int64)
    X = np.empty((len(scans), 2 * w + 1, 4), dtype=np.float32)
    for k, s in enumerate(scans):
        s = int(np.clip(s, 0, n - 1))
        lo, hi = s - w, s + w + 1
        pad_lo, pad_hi = max(0, -lo), max(0, hi - n)
        win = ch_raw[max(0, lo):min(n, hi)]
        if pad_lo or pad_hi:
            win = np.pad(win, ((pad_lo, pad_hi), (0, 0)), mode='edge')
        X[k] = win
    mu = X.mean(axis=1, keepdims=True)
    sd = X.std(axis=1, keepdims=True) + 1e-8
    X = ((X - mu) / sd).astype(np.float32)
    return X


def _add_position_channel(X4, scans):
    """Append a 5th position-fraction channel to 4-channel windows.

    X4: (N, W, 4) float32
    scans: array of scan positions (same length as N)

    Returns: (N, W, 5) float32 with position channel.
    """
    scans_arr = np.asarray(scans, dtype=np.float32)
    s_min, s_max = scans_arr.min(), scans_arr.max()
    s_range = max(1.0, s_max - s_min)
    pos_frac = ((scans_arr - s_min) / s_range).astype(np.float32)
    W = X4.shape[1]
    pos_ch = pos_frac[:, np.newaxis, np.newaxis] * np.ones((len(X4), W, 1), dtype=np.float32)
    return np.concatenate([X4, pos_ch], axis=2)


def _prepare_model_input(models, X4, scans):
    """Build per-model inputs, adding position channel where needed.

    Returns list of (model, input_array) pairs.
    """
    out = []
    for m in models:
        inp_ch = m.input_shape[-1] if m.input_shape[-1] else 4
        if inp_ch == 5:
            inp = _add_position_channel(X4, scans)
        else:
            inp = X4
        out.append((m, inp))
    return out


def _ensemble_predict(models, X, scans=None):
    """Run ensemble averaging over loaded models.

    X: (N, W, 4) float32 4-channel windows
    scans: scan positions (required if any model needs position channel)

    Returns (N, 4) float64 probabilities for ACGT.
    """
    has_pos = any(m.input_shape[-1] == 5 for m in models)
    if has_pos and scans is not None:
        pairs = _prepare_model_input(models, X, scans)
    else:
        pairs = [(m, X) for m in models]
    probs = np.zeros((len(X), 4), dtype=np.float64)
    for m, inp in pairs:
        p = m.predict(inp, verbose=0)
        if p.shape[1] == 5:
            p = p[:, :4]
        probs += p
    probs /= max(1, len(models))
    return probs


class CNNEstimator:
    """Singleton-friendly CNN confidence estimator.

    Loads the model ensemble once and caches it for all subsequent calls.
    """
    _instance = None

    def __new__(cls, model_dir=None):
        if cls._instance is not None:
            return cls._instance
        inst = super().__new__(cls)
        inst._loaded = False
        inst.models = []
        inst.model_dir = model_dir
        cls._instance = inst
        return inst

    def load(self, model_dir=None):
        if self._loaded:
            return
        if model_dir:
            self.model_dir = model_dir
        self.models = _load_models(self.model_dir)
        self._loaded = True

    def predict_probs(self, ch_raw, scans):
        """Return (N, 4) ACGT probabilities from the ensemble.

        ch_raw: (N, 4) raw trace
        scans: array of scan positions (int)
        """
        if not self._loaded:
            self.load()
        if not self.models:
            raise RuntimeError('No CNN models loaded')
        X = _build_windows(ch_raw, scans)
        return _ensemble_predict(self.models, X, scans)

    def predict_pmax(self, ch_raw, scans):
        """Return per-base maximum softmax probability (pmax).

        Returns (N,) float64 array.
        """
        probs = self.predict_probs(ch_raw, scans)
        return probs.max(axis=1)

    def predict_labels(self, ch_raw, scans):
        """Return predicted base labels and their pmax.

        Returns (labels_str, pmax_array).
        """
        probs = self.predict_probs(ch_raw, scans)
        pred = probs.argmax(axis=1)
        pmax = probs.max(axis=1)
        labels = ''.join(LABELS[i] for i in pred)
        return labels, pmax

    def phred(self, pmax):
        """Convert pmax to Phred Q-scores (int8, 0-93)."""
        p = np.asarray(pmax, dtype=np.float64)
        p_err = np.clip(1.0 - p, 1e-15, 1.0)
        q = -10.0 * np.log10(p_err)
        return np.clip(np.round(q), 0, 93).astype(np.int8)

    @classmethod
    def clear(cls):
        """Release models to free memory."""
        if cls._instance is not None:
            cls._instance.models = []
            cls._instance._loaded = False
            cls._instance = None


def get_estimator(model_dir=None):
    """Get or create the singleton CNNEstimator."""
    return CNNEstimator(model_dir)
