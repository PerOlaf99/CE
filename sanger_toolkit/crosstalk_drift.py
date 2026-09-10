#!/usr/bin/env python3
import numpy as np
from scipy.linalg import lstsq, svd
from scipy.interpolate import interp1d
from collections import defaultdict


class CrosstalkDrift:
    def __init__(self, window_size=800, step=200, ridge_lambda=1e-3, min_peaks=10):
        self.window_size = window_size
        self.step = step
        self.ridge_lambda = ridge_lambda
        self.min_peaks = min_peaks
        self.window_centers = []
        self.matrices = []
        self.condition_numbers = []
        self.purities = []

    def estimate_from_peaks(self, traces, peaks, bases, scan_indices=None):
        if scan_indices is None:
            scan_indices = np.arange(traces.shape[1])
        base_to_ch = {'T': 0, 'G': 1, 'C': 2, 'A': 3}
        chans = np.array([base_to_ch[b] for b in bases])
        peak_positions = np.array(peaks)
        order = np.argsort(peak_positions)
        peak_positions = peak_positions[order]
        chans = chans[order]
        N = traces.shape[1]
        window_starts = list(range(0, N - self.window_size + 1, self.step))
        if (N - self.window_size) % self.step != 0:
            window_starts.append(N - self.window_size)
        self.window_centers = [start + self.window_size // 2 for start in window_starts]
        for start in window_starts:
            end = start + self.window_size
            mask = (peak_positions >= start) & (peak_positions < end)
            if np.sum(mask) < self.min_peaks:
                self.matrices.append(None)
                self.condition_numbers.append(np.nan)
                self.purities.append(np.full(4, np.nan))
                continue
            Y = traces[:, peak_positions[mask]].T
            X = np.zeros((len(Y), 4))
            X[np.arange(len(Y)), chans[mask]] = 1.0
            M, _, _, _ = lstsq(X, Y, lapack_driver='gelsd')
            M = np.maximum(M, 0)
            col_sums = M.sum(axis=0)
            M = M / (col_sums + 1e-12)
            self.matrices.append(M)
            self.condition_numbers.append(np.linalg.cond(M))
            self.purities.append(np.diag(M))
        self._interpolate_matrices()
        return self

    def _interpolate_matrices(self):
        centers = np.array(self.window_centers)
        valid = [i for i, M in enumerate(self.matrices) if M is not None]
        if len(valid) < 2:
            return
        valid_centers = centers[valid]
        M_stack = np.array([self.matrices[i] for i in valid])
        new_matrices = []
        for idx, center in enumerate(centers):
            if self.matrices[idx] is not None:
                new_matrices.append(self.matrices[idx])
            else:
                M_interp = np.zeros((4, 4))
                for i in range(4):
                    for j in range(4):
                        vals = M_stack[:, i, j]
                        f = interp1d(valid_centers, vals, kind='linear',
                                     bounds_error=False, fill_value=(vals[0], vals[-1]))
                        M_interp[i, j] = f(center)
                new_matrices.append(M_interp)
        self.matrices = new_matrices

    def get_matrix(self, scan_index):
        centers = np.array(self.window_centers)
        if len(centers) == 0:
            return np.eye(4)
        if scan_index <= centers[0]:
            return self.matrices[0]
        if scan_index >= centers[-1]:
            return self.matrices[-1]
        idx = np.searchsorted(centers, scan_index) - 1
        if idx < 0:
            return self.matrices[0]
        if idx >= len(centers) - 1:
            return self.matrices[-1]
        c1, c2 = centers[idx], centers[idx + 1]
        M1, M2 = self.matrices[idx], self.matrices[idx + 1]
        if M1 is None or M2 is None:
            return M1 if M1 is not None else M2
        alpha = (scan_index - c1) / (c2 - c1)
        return (1 - alpha) * M1 + alpha * M2

    def unmix(self, y, scan_index=None, use_ridge=False):
        if scan_index is not None:
            M = self.get_matrix(scan_index)
        else:
            M = self.matrices[0] if len(self.matrices) > 0 else np.eye(4)
        if use_ridge or self.ridge_lambda > 0:
            MtM = M.T @ M + self.ridge_lambda * np.eye(4)
            MtY = M.T @ y
            x = np.linalg.solve(MtM, MtY)
        else:
            x, _, _, _ = lstsq(M, y, lapack_driver='gelsd')
        x = np.maximum(x, 0)
        return x

    def unmix_traces(self, traces, use_ridge=False):
        N = traces.shape[1]
        unmixed = np.zeros_like(traces)
        for i in range(N):
            y = traces[:, i]
            x = self.unmix(y, scan_index=i, use_ridge=use_ridge)
            unmixed[:, i] = x
        return unmixed

    def diagnose(self):
        print("Window centers:", self.window_centers)
        print("Condition numbers:", self.condition_numbers)
        print("Purities (diagonal) per window:")
        for i, pur in enumerate(self.purities):
            print(f"  window {i}: T={pur[0]:.2f}, G={pur[1]:.2f}, C={pur[2]:.2f}, A={pur[3]:.2f}")
