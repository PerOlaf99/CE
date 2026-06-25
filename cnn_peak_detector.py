import os
import sys
import numpy as np
from scipy.interpolate import interp1d
from scipy.integrate import simpson


def _init_tf():
    import tensorflow as tf
    _dl_src = os.path.join(os.path.dirname(__file__), "deep-learning-peak-detection-main", "src")
    if _dl_src not in sys.path:
        sys.path.insert(0, _dl_src)
    from cnn.models import ConvNet
    from cnn.preprocessing import LabelEncoder
    return tf, ConvNet, LabelEncoder


WEIGHTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "deep-learning-peak-detection-main",
    "notebooks", "output", "weights", "cnn_weights.h5"
)
INPUT_SIZE = 8192
NUM_WINDOWS = 256
PEAK_CHANNEL_NAMES = ["Channel1", "Channel2", "Channel3", "Channel4"]
PEAK_WIDTH_HALF = 5


class CnnPeakDetector:
    def __init__(self):
        tf, ConvNet, LabelEncoder = _init_tf()
        self.model = ConvNet(
            filters=[64, 128, 128, 256, 256],
            kernel_sizes=[9, 9, 9, 9, 9],
            dropout=0.0,
            pool_type="max",
            pool_sizes=[2, 2, 2, 2, 2],
            conv_block_size=1,
            input_shape=(INPUT_SIZE, 1),
            output_shape=(NUM_WINDOWS, 3),
            residual=False,
        )
        self.model.load_weights(WEIGHTS_PATH)
        self.label_encoder = LabelEncoder(NUM_WINDOWS)

        self.min_height = 0
        self.prominence = 0
        self.distance = 0
        self.min_width = 0
        self.baseline_method = "None"
        self.baseline_param = 0
        self.group_stutter = False
        self.stutter_window = 0
        self.limit_range = False
        self.scan_start = 0
        self.scan_end = 50000
        self.active_channels = {
            "Channel1": False,
            "Channel2": True,
            "Channel3": False,
            "Channel4": False,
            "Current": False,
        }

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
            y = df[ch].values
            channel_data[ch] = y
            channel_baselines[ch] = np.zeros_like(y)
            noise_levels[ch] = 1.0

            if len(y) < 2:
                continue

            y_interp, scan_interp = self._resample(y, scan_values)
            max_val = y_interp.max()
            if max_val <= 0:
                continue
            y_norm = y_interp[None, :, None] / max_val

            preds = self.model(y_norm, training=False)[0].numpy()
            probs, locs_norm, areas = self.label_encoder.decode(preds, threshold=0.5)

            if len(locs_norm) == 0:
                continue

            scan_peaks = locs_norm * (len(y) - 1)

            for sp, prob, area in zip(scan_peaks, probs, areas):
                idx = int(round(sp))
                idx = max(0, min(idx, len(y) - 1))
                all_peaks.append(idx)
                all_channels.append(ch)
                all_lefts.append(max(0, idx - PEAK_WIDTH_HALF))
                all_rights.append(min(len(y) - 1, idx + PEAK_WIDTH_HALF))

        if not any_active:
            return {
                "peaks": np.array([], dtype=int),
                "peak_channels": [],
                "peak_lefts": np.array([]),
                "peak_rights": np.array([]),
                "channel_data": channel_data,
                "channel_baselines": channel_baselines,
                "noise_levels": noise_levels,
                "scan": scan,
                "scan_values": scan_values,
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
            "peaks": peaks,
            "peak_channels": peak_channels,
            "peak_lefts": peak_lefts,
            "peak_rights": peak_rights,
            "channel_data": channel_data,
            "channel_baselines": channel_baselines,
            "noise_levels": noise_levels,
            "scan": scan,
            "scan_values": scan_values,
        }

    def build_peak_rows(self, well, wd):
        rows = []
        peaks = wd["peaks"]
        if len(peaks) == 0:
            return rows
        scan_values = wd["scan_values"]
        channel_data = wd["channel_data"]
        channel_baselines = wd["channel_baselines"]
        noise_levels = wd["noise_levels"]
        peak_channels = wd["peak_channels"]
        peak_lefts = wd["peak_lefts"]
        peak_rights = wd["peak_rights"]

        for p, pc, left, right in zip(peaks, peak_channels, peak_lefts, peak_rights):
            y = channel_data.get(pc)
            if y is None:
                continue
            l = max(0, int(round(left)))
            r = min(len(y) - 1, int(round(right)))
            area = simpson(y[l:r + 1], x=scan_values[l:r + 1])
            bl_val = channel_baselines.get(pc, np.zeros_like(y))[p]
            rows.append({
                "well": well, "channel": pc, "scan": scan_values[p],
                "height": y[p], "width": r - l, "baseline": bl_val,
                "area": area, "noise": noise_levels.get(pc, 1),
            })
        return rows

    def _resample(self, y, scan_values):
        n = len(y)
        f = interp1d(np.arange(n), y, bounds_error=False, fill_value=0.0)
        x_new = np.linspace(0, n - 1, INPUT_SIZE)
        y_new = f(x_new)

        f_scan = interp1d(np.arange(n), scan_values, bounds_error=False, fill_value=scan_values[-1])
        scan_new = f_scan(x_new)
        return y_new, scan_new
