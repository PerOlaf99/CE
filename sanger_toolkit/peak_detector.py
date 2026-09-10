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

# Basecalling dye chemistry: channel -> base mapping for ET Terminators
# Channel 1 = T, Channel 2 = G, Channel 3 = C, Channel 4 = A
CHEMISTRY_MAP = {0: "T", 1: "G", 2: "C", 3: "A"}

# Dye mobility offsets (scans): each dye label shifts migration speed
# Ch1(T) moves fastest → detected earlier → offset -3
# Ch2(G) slightly faster → offset -1
# Ch3(C) slightly slower → offset +1
# Ch4(A) slowest → offset +3
MOBILITY_OFFSET = [-3, -1, 1, 3]

# Default basecalling peak detection parameters
DEFAULT_HEIGHT = 15
DEFAULT_PROMINENCE = 10
DEFAULT_DISTANCE = 5
DEFAULT_NMS_DISTANCE = 5


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

    def detect_basecalling(self, df, scan, height=DEFAULT_HEIGHT,
                           prominence=DEFAULT_PROMINENCE,
                           per_channel_distance=DEFAULT_DISTANCE,
                           nms_distance=DEFAULT_NMS_DISTANCE):
        """Basecalling-specific peak detection with mobility correction.

        Detects peaks per-channel, applies dye-specific mobility offsets,
        then merges nearby peaks using non-maximum suppression (NMS).

        This accounts for different fluorophore migration rates between
        channels — essential for accurate base calling.

        Returns same dict as detect() with 'peaks' and 'peak_channels'.
        """
        scan_values = scan.values
        n_scans = len(df)
        ch_data = df[PEAK_CHANNEL_NAMES].values.astype(np.float64)

        # Per-channel baseline correction and smoothing
        candidates = []
        for i, ch_name in enumerate(PEAK_CHANNEL_NAMES):
            y_raw = ch_data[:, i]
            y_corrected, _ = self.correct_baseline(y_raw)
            try:
                y_smooth = savgol_filter(y_corrected, SAVGOL_WINDOW, SAVGOL_ORDER)
            except Exception:
                y_smooth = y_corrected

            peaks, props = find_peaks(
                y_smooth, height=height, prominence=prominence,
                distance=per_channel_distance,
            )

            if self.limit_range:
                mask = ((scan_values[peaks] >= self.scan_start) &
                        (scan_values[peaks] <= self.scan_end))
                peaks = peaks[mask]
                if 'peak_heights' in props:
                    props['peak_heights'] = props['peak_heights'][mask]

            for j, p in enumerate(peaks):
                corr = p + MOBILITY_OFFSET[i]
                if 0 <= corr < n_scans:
                    h = props['peak_heights'][j] if 'peak_heights' in props else y_smooth[p]
                    candidates.append((corr, h))

        if not candidates:
            return {
                'peaks': np.array([], dtype=int),
                'peak_channels': [],
                'peak_lefts': np.array([]),
                'peak_rights': np.array([]),
                'channel_data': {},
                'channel_baselines': {},
                'noise_levels': {},
                'scan': scan,
                'scan_values': scan_values,
            }

        # Sort by height descending, greedy NMS
        candidates.sort(key=lambda x: -x[1])
        selected = []
        for pos, h in candidates:
            if all(abs(pos - s_pos) > nms_distance for s_pos, _ in selected):
                selected.append((pos, h))

        selected.sort(key=lambda x: x[0])
        peaks_arr = np.array([p for p, _ in selected], dtype=int)
        # Assign each peak to a channel based on the original candidate's source
        peak_channels = []
        for pos, _ in selected:
            # Find which channel contributed this position
            best_ch = 'Current'
            best_d = nms_distance + 1
            for i in range(4):
                # Check if this channel had a peak that maps to this position
                for p in range(int(pos - nms_distance), int(pos + nms_distance + 1)):
                    if 0 <= p < n_scans:
                        corr = p + MOBILITY_OFFSET[i]
                        if abs(corr - pos) <= 2:
                            best_ch = PEAK_CHANNEL_NAMES[i]
                            break
            peak_channels.append(best_ch)

        return {
            'peaks': peaks_arr,
            'peak_channels': peak_channels,
            'peak_lefts': np.full_like(peaks_arr, 0.0),
            'peak_rights': np.full_like(peaks_arr, 0.0),
            'channel_data': {},
            'channel_baselines': {},
            'noise_levels': {},
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
