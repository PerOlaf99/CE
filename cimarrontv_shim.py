#!/usr/bin/env python3
"""cimarrontv_shim.py - minimal stand-in for the lost cimarrontv.py engine.

Rebuilds the API surface perfect_basecaller needs from local modules:
  read_rsd / parse_esd   <- extract_training_data
  DSP chain              <- dsp_core.full_pipeline (AsyLS, Butterworth,
                            spectral separation, mobility shifts)
  candidate peaks        <- peak_calling.detect_peaks_4ch + BASE_LETTERS
  pc_nw_identity         <- peak_calling.nw_identity

NOTE: the greedy caller here is simpler than the original Cimarron 3.12
port (no SNR trim, no bgn/end trimming), so raw de-novo accuracy is lower.
This does NOT matter for the perfect_basecaller pipeline: the CNN ensemble
re-calls every peak and polishing fixes indels - only peak POSITIONS matter.
"""
import struct
import numpy as np

import dsp_core
import peak_calling
from extract_training_data import parse_rsd, parse_esd

BASE_LETTERS = peak_calling.BASE_LETTERS

V10_SSM = np.array([[1.0, 1.00, 0.26, 0.46],
                    [0.07, 1.00, 0.075, 0.006],
                    [0.38, 0.33, 1.00, 1.52],
                    [0.27, 0.26, 0.189, 1.00]], dtype=np.float64)


def read_rsd(path: str):
    df = parse_rsd(path)
    ch = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.astype(np.float64)
    return ch.T.copy(), df['Scan'].values.astype(np.int64)


def read_esd(path: str):
    return parse_esd(path)


def pc_nw_identity(query: str, reference: str) -> float:
    return peak_calling.nw_identity(query, reference)


class Peak:
    def __init__(self, idx, time, channel, base, height, quality=30):
        self.idx = idx
        self.time = float(time)
        self.channel = int(channel)
        self.base = base
        self.height = float(height)
        self.quality = int(quality)


class CallResult:
    def __init__(self, sequence, peaks):
        self.sequence = sequence
        self.peaks = peaks
        self.quality = ''.join(chr(33 + p.quality) for p in peaks)


class Cimarron312:
    def __init__(self, variant='3.12', spec_sep_matrix=None,
                 snr_threshold=3.0, base_letters=None, min_distance=6,
                 baseline_method='AsyLS', baseline_window=50010,
                 baseline_window2=None, smooth_method='Butterworth',
                 smooth_window=5, smooth_order=9,
                 matrix_apply_point='smoothed',
                 mobility_shifts=(5, 11, 10, 10), caller='greedy',
                 greedy_window=6, **kw):
        self.ssm = np.asarray(spec_sep_matrix if spec_sep_matrix is not None
                              else V10_SSM.copy(), dtype=float)
        self.mobility_shifts = tuple(mobility_shifts)
        self.baseline_method = baseline_method
        self.baseline_window = baseline_window
        self.baseline_window2 = baseline_window2
        self.smooth_method = smooth_method
        self.smooth_window = smooth_window
        self.smooth_order = smooth_order
        self.matrix_apply_point = matrix_apply_point
        self.min_distance = min_distance

    def call(self, channels, scans=None):
        ch = np.asarray(channels, dtype=np.float64)
        if ch.ndim == 2 and ch.shape[0] == 4 and ch.shape[0] <= ch.shape[1]:
            ch = ch.T
        _, _, _, _, separated, _ = dsp_core.full_pipeline(
            ch, self.mobility_shifts, self.baseline_method,
            self.baseline_window, self.smooth_method, self.smooth_window,
            self.smooth_order, self.ssm,
            baseline_window2=self.baseline_window2,
            matrix_apply_point=self.matrix_apply_point)
        shifted = dsp_core.apply_mobility_shifts(separated, self.mobility_shifts)
        self.separated = separated
        self.shifted = shifted
        norm = peak_calling.normalize_peaks(shifted, mode='total_signal')
        merged = peak_calling.detect_peaks_4ch(
            norm, min_distance=self.min_distance, prominence_frac=0.02)
        peaks, seq = [], []
        for k, (pos, chan, height) in enumerate(merged):
            base = BASE_LETTERS[chan]
            seq.append(base)
            peaks.append(Peak(idx=k, time=pos, channel=chan, base=base,
                              height=height))
        return CallResult(''.join(seq), peaks)
