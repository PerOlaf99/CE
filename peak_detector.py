import numpy as np
import pandas as pd
from scipy.signal import find_peaks, peak_widths, savgol_filter
from scipy.integrate import simpson
from scipy import sparse
from scipy.sparse.linalg import spsolve


SAVGOL_WINDOW = 11
SAVGOL_ORDER = 2
PEAK_WIDTH_REL_HEIGHT = 0.95
NOISE_WINDOW = 200
ALS_P = 0.01
ALS_NITER = 10
PEAK_CHANNEL_NAMES = ['Channel1', 'Channel2', 'Channel3', 'Channel4']


class PeakDetector:
    def __init__(self, params=None):
        if params is None:
            params = {}
        self.min_height = params.get('min_height', 100)
        self.prominence = params.get('prominence', 50)
        self.distance = params.get('distance', 5)
        self.min_width = params.get('min_width', 1)
        self.baseline_method = params.get('baseline_method', 'None')
        self.baseline_param = params.get('baseline_param', 500)
        self.group_stutter = params.get('group_stutter', False)
        self.stutter_window = params.get('stutter_window', 5)
        self.limit_range = params.get('limit_range', False)
        self.scan_start = params.get('scan_start', 0)
        self.scan_end = params.get('scan_end', 50000)
        self.active_channels = params.get('active_channels', {
            'Channel1': False,
            'Channel2': True,
            'Channel3': False,
            'Channel4': False,
            'Current': False,
        })

    def correct_baseline(self, y):
        method = self.baseline_method
        if method == 'None':
            return y, np.zeros_like(y)
        elif method == 'First 200':
            n = min(NOISE_WINDOW, len(y))
            bl_val = np.median(y[:n])
            baseline = np.full_like(y, bl_val)
            return y - baseline, baseline
        elif method == 'Rolling Min':
            window = self.baseline_param
            baseline = pd.Series(y).rolling(window, center=True, min_periods=1).min().values
            baseline = np.nan_to_num(baseline)
            return y - baseline, baseline
        elif method == 'ALS':
            lam = self.baseline_param
            L = len(y)
            D = sparse.diags([1, -2, 1], [0, -1, -2], shape=(L, L - 2))
            w = np.ones(L)
            for _ in range(ALS_NITER):
                W = sparse.spdiags(w, 0, L, L)
                Z = W + lam * D.dot(D.T)
                z = spsolve(Z, w * y)
                w = ALS_P * (y > z) + (1 - ALS_P) * (y < z)
            return y - z, z

    def group_stutter_peaks(self, peaks, left_ips, right_ips, scan_values, y):
        order = np.argsort(scan_values[peaks])
        sorted_peaks = peaks[order]
        sorted_left = left_ips[order]
        sorted_right = right_ips[order]

        groups = []
        display_peaks = []
        display_lefts = []
        display_rights = []
        n_merged = []

        current_group = [sorted_peaks[0]]
        current_left = sorted_left[0]
        current_right = sorted_right[0]

        for i in range(1, len(sorted_peaks)):
            gap = scan_values[sorted_peaks[i]] - scan_values[sorted_peaks[i - 1]]
            if gap <= self.stutter_window:
                current_group.append(sorted_peaks[i])
                current_left = min(current_left, sorted_left[i])
                current_right = max(current_right, sorted_right[i])
            else:
                heights = y[current_group]
                main_idx = current_group[np.argmax(heights)]
                groups.append(current_group)
                display_peaks.append(main_idx)
                display_lefts.append(current_left)
                display_rights.append(current_right)
                n_merged.append(len(current_group))
                current_group = [sorted_peaks[i]]
                current_left = sorted_left[i]
                current_right = sorted_right[i]

        heights = y[current_group]
        main_idx = current_group[np.argmax(heights)]
        groups.append(current_group)
        display_peaks.append(main_idx)
        display_lefts.append(current_left)
        display_rights.append(current_right)
        n_merged.append(len(current_group))

        return (groups, np.array(display_peaks), np.array(display_lefts),
                np.array(display_rights), n_merged)

    def detect(self, df, scan):
        scan_values = scan.values
        all_peaks = []
        all_channels = []
        all_lefts = []
        all_rights = []
        channel_data = {}
        channel_baselines = {}
        noise_levels = {}
        any_active = False

        for ch in PEAK_CHANNEL_NAMES:
            if ch not in df.columns or not self.active_channels.get(ch, False):
                continue
            any_active = True
            y_raw = df[ch].values
            y_corrected, baseline = self.correct_baseline(y_raw)
            channel_data[ch] = y_corrected
            channel_baselines[ch] = baseline

            n_noise = min(NOISE_WINDOW, len(y_corrected))
            noise_levels[ch] = max(np.std(y_corrected[:n_noise]), 1e-10)

            try:
                y_smooth = savgol_filter(y_corrected, SAVGOL_WINDOW, SAVGOL_ORDER)
            except Exception:
                y_smooth = y_corrected

            peaks, _props = find_peaks(
                y_smooth,
                height=self.min_height,
                prominence=self.prominence,
                distance=self.distance,
                width=self.min_width,
            )

            if self.limit_range:
                mask = (scan_values[peaks] >= self.scan_start) & (scan_values[peaks] <= self.scan_end)
                peaks = peaks[mask]

            if len(peaks) == 0:
                continue

            _widths, _, left_ips, right_ips = peak_widths(
                y_smooth, peaks, rel_height=PEAK_WIDTH_REL_HEIGHT
            )

            if self.group_stutter and len(peaks) > 1:
                _, disp_peaks, disp_lefts, disp_rights, _ = self.group_stutter_peaks(
                    peaks, left_ips, right_ips, scan_values, y_corrected
                )
                for p, l, r in zip(disp_peaks, disp_lefts, disp_rights):
                    all_peaks.append(p)
                    all_channels.append(ch)
                    all_lefts.append(l)
                    all_rights.append(r)
            else:
                for p, l, r in zip(peaks, left_ips, right_ips):
                    all_peaks.append(p)
                    all_channels.append(ch)
                    all_lefts.append(l)
                    all_rights.append(r)

        if not any_active:
            return {
                'peaks': np.array([], dtype=int),
                'peak_channels': [],
                'peak_lefts': np.array([]),
                'peak_rights': np.array([]),
                'channel_data': channel_data,
                'channel_baselines': channel_baselines,
                'noise_levels': noise_levels,
                'scan': scan,
                'scan_values': scan_values,
            }

        if all_peaks:
            sort_idx = np.argsort(all_peaks)
            peaks = np.array(all_peaks)[sort_idx]
            peak_channels = [all_channels[i] for i in sort_idx]
            peak_lefts = np.array(all_lefts)[sort_idx]
            peak_rights = np.array(all_rights)[sort_idx]
        else:
            peaks = np.array([], dtype=int)
            peak_channels = []
            peak_lefts = np.array([])
            peak_rights = np.array([])

        return {
            'peaks': peaks,
            'peak_channels': peak_channels,
            'peak_lefts': peak_lefts,
            'peak_rights': peak_rights,
            'channel_data': channel_data,
            'channel_baselines': channel_baselines,
            'noise_levels': noise_levels,
            'scan': scan,
            'scan_values': scan_values,
        }

    def build_peak_rows(self, well, wd):
        rows = []
        peaks = wd['peaks']
        if len(peaks) == 0:
            return rows
        scan_values = wd['scan_values']
        channel_data = wd['channel_data']
        channel_baselines = wd['channel_baselines']
        noise_levels = wd['noise_levels']
        peak_channels = wd['peak_channels']
        peak_lefts = wd['peak_lefts']
        peak_rights = wd['peak_rights']

        for p, pc, left, right in zip(peaks, peak_channels, peak_lefts, peak_rights):
            y = channel_data.get(pc)
            if y is None:
                continue
            l = max(0, int(round(left)))
            r = min(len(y) - 1, int(round(right)))
            area = simpson(y[l:r + 1], x=scan_values[l:r + 1])
            bl_val = channel_baselines.get(pc, np.zeros_like(y))[p]
            rows.append({
                'well': well, 'channel': pc, 'scan': scan_values[p],
                'height': y[p], 'width': r - l, 'baseline': bl_val,
                'area': area, 'noise': noise_levels.get(pc, 1),
            })
        return rows
