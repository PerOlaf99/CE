#!/usr/bin/env python3
"""Sequencing basecaller GUI with adjustable preprocessing and real-time plots.

Load RSD + ESD for one well. Tune baseline, smoothing, and matrix parameters
via sliders. 3 plots show the effect of each processing stage in real time.
Save processed data and run ML basecalling.
"""
import sys, os, struct, json, subprocess, tempfile
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QGroupBox, QGridLayout, QSlider, QTextEdit, QSplitter, QTabWidget,
    QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, QSettings

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd

import dsp_core
import peak_calling
from dsp_core import (
    CHAN_COLORS, BASE_LETTERS, CHEM_MAP, DEFAULT_SPEC_MATRIX, OFF_PATTERN,
    make_matrix_from_diagonals, BASELINE_PARAM_CONFIG, SMOOTH_PARAM_CONFIG,
)

BASE_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"


def find_esd_subdirs(base_dir):
    dirs = {}
    for d in sorted(os.listdir(base_dir)):
        dp = os.path.join(base_dir, d)
        if os.path.isdir(dp) and d.endswith('_MD1'):
            name = d.replace('MB1000_M13_DT_', '').replace('_MD1', '')
            dirs[name] = d
    return dirs


class SequencingGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Sequencing Basecaller GUI')
        self.setGeometry(50, 50, 1500, 950)
        self.rsd_raw = None
        self.esd_traces = None
        self.esd_data = None
        self.esd_offset = 0
        self.current_well = None
        self._saved_lims = {}
        self._smooth_mode = 'Savitzky-Golay'
        self._settings = QSettings('opencode', 'sequencing_gui')
        self._setup_ui()
        self._restore_settings()
        self._populate_wells()

    def _setup_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setContentsMargins(4, 4, 4, 4)

        # -- Top bar: well selector + load + toolbar --
        top = QHBoxLayout()
        layout.addLayout(top)
        top.addWidget(QLabel('Well:'))
        self.well_combo = QComboBox()
        self.well_combo.setEditable(True)
        self.well_combo.setMinimumWidth(80)
        top.addWidget(self.well_combo)
        self.load_btn = QPushButton('Load')
        self.load_btn.clicked.connect(self._load_data)
        top.addWidget(self.load_btn)
        top.addWidget(QLabel('  ESD variant:'))
        self.esd_combo = QComboBox()
        top.addWidget(self.esd_combo)

        # -- Toolbar (moved up to save vertical space) --
        self.fig = Figure(figsize=(14, 11), dpi=100)
        self.fig.subplots_adjust(hspace=0.08, left=0.05, right=0.98, top=0.97, bottom=0.05)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        top.addWidget(self.toolbar)
        top.addStretch()

        # -- Sliders panel --
        sliders_w = QWidget()
        sliders_w.setMinimumHeight(260)
        sliders_l = QHBoxLayout(sliders_w)
        sliders_l.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(sliders_w)

        # Baseline group
        blg = QGroupBox('Baseline')
        blg_g = QVBoxLayout(blg)
        hl_m = QHBoxLayout()
        hl_m.addWidget(QLabel('Method:'))
        self.baseline_combo = QComboBox()
        self.baseline_combo.addItems(['Rolling Minimum', 'Rolling Median', 'ALS',
                                      'airPLS', 'SNIP', 'Morphological (Top-hat)',
                                      'Polynomial Detrend'])
        self.baseline_combo.currentTextChanged.connect(self._on_baseline_method_changed)
        hl_m.addWidget(self.baseline_combo)
        blg_g.addLayout(hl_m)
        self.bl_param_label = QLabel('Window:')
        blg_g.addWidget(self.bl_param_label)
        hl = QHBoxLayout()
        self.bl_slider = QSlider(Qt.Horizontal)
        self.bl_slider.setRange(20, 1000)
        self.bl_slider.setValue(200)
        self.bl_slider.setSingleStep(10)
        self.bl_spin = QSpinBox()
        self.bl_spin.setRange(20, 1000)
        self.bl_spin.setValue(200)
        self.bl_spin.setSingleStep(10)
        self.bl_spin.setMinimumWidth(70)
        self._link_slider_spinbox(self.bl_slider, self.bl_spin)
        hl.addWidget(self.bl_slider)
        hl.addWidget(self.bl_spin)
        blg_g.addLayout(hl)
        sliders_l.addWidget(blg)

        # Smoothing group
        smg = QGroupBox('Smooth')
        smg_g = QVBoxLayout(smg)
        smg_g.setSpacing(2)

        hl_m = QHBoxLayout()
        hl_m.addWidget(QLabel('Method:'))
        self.smooth_combo = QComboBox()
        self.smooth_combo.addItems(['Savitzky-Golay', 'Gaussian', 'Moving Avg',
                                    'Median', 'Whittaker', 'Butterworth',
                                    'Wavelet', 'LOWESS', 'FFT Lowpass'])
        self.smooth_combo.currentTextChanged.connect(self._on_smooth_method_changed)
        hl_m.addWidget(self.smooth_combo)
        smg_g.addLayout(hl_m)

        hl1 = QHBoxLayout()
        self.sm_param1_label = QLabel('Window:')
        hl1.addWidget(self.sm_param1_label)
        self.sm_win_slider = QSlider(Qt.Horizontal)
        self.sm_win_slider.setRange(3, 51)
        self.sm_win_slider.setValue(7)
        self.sm_win_slider.setSingleStep(2)
        self.sm_win_slider.setTickPosition(QSlider.TicksBelow)
        self.sm_win_spin = QSpinBox()
        self.sm_win_spin.setRange(3, 51)
        self.sm_win_spin.setValue(7)
        self.sm_win_spin.setSingleStep(2)
        self.sm_win_spin.setMinimumWidth(60)
        self._link_slider_spinbox(self.sm_win_slider, self.sm_win_spin)
        hl1.addWidget(self.sm_win_slider)
        hl1.addWidget(self.sm_win_spin)
        smg_g.addLayout(hl1)

        hl2 = QHBoxLayout()
        self.sm_param2_label = QLabel('Order:')
        hl2.addWidget(self.sm_param2_label)
        self.sm_ord_slider = QSlider(Qt.Horizontal)
        self.sm_ord_slider.setRange(1, 20)
        self.sm_ord_slider.setValue(2)
        self.sm_ord_spin = QSpinBox()
        self.sm_ord_spin.setRange(1, 20)
        self.sm_ord_spin.setValue(2)
        self.sm_ord_spin.setMinimumWidth(60)
        self._link_slider_spinbox(self.sm_ord_slider, self.sm_ord_spin)
        hl2.addWidget(self.sm_ord_slider)
        hl2.addWidget(self.sm_ord_spin)
        smg_g.addLayout(hl2)

        sliders_l.addWidget(smg)

        # Matrix group: full 4x4 mixing-matrix grid (row = measured channel, col = true base)
        mxg = QGroupBox('Matrix (row=channel, col=base)')
        mxg_g = QGridLayout(mxg)
        mxg_g.setVerticalSpacing(3)
        mxg_g.setHorizontalSpacing(3)
        base_labels = ['T', 'G', 'C', 'A']
        base_colors = ['red', 'green', 'blue', 'orange']
        mxg_g.addWidget(QLabel(''), 0, 0)
        for c in range(4):
            lbl = QLabel(base_labels[c])
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f'color: {base_colors[c]}; font-weight: bold;')
            mxg_g.addWidget(lbl, 0, c + 1)
        self.mx_grid_spins = [[None] * 4 for _ in range(4)]
        for r in range(4):
            row_lbl = QLabel(f'Ch{r}')
            row_lbl.setStyleSheet(f'color: {base_colors[r]}; font-weight: bold;')
            mxg_g.addWidget(row_lbl, r + 1, 0)
            for c in range(4):
                sp = QDoubleSpinBox()
                sp.setRange(0.0, 1.0)
                sp.setSingleStep(0.01)
                sp.setDecimals(3)
                sp.setValue(float(DEFAULT_SPEC_MATRIX[r, c]))
                sp.setMinimumWidth(62)
                if r == c:
                    sp.setStyleSheet('QDoubleSpinBox { font-weight: bold; }')
                sp.valueChanged.connect(self._schedule_update)
                mxg_g.addWidget(sp, r + 1, c + 1)
                self.mx_grid_spins[r][c] = sp
        # Preset buttons
        preset_l = QHBoxLayout()
        for name, m in [('Default', DEFAULT_SPEC_MATRIX),
                        ('Identity', np.eye(4)),
                        ('Uniform', np.full((4, 4), 0.25))]:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, mm=m: self._set_matrix(mm))
            preset_l.addWidget(btn)
        mxg_g.addLayout(preset_l, 5, 0, 1, 5)
        sliders_l.addWidget(mxg)

        # Mobility shift group: per-channel scan shift (dye mobility correction)
        msg = QGroupBox('Mobility Shift (scans)')
        msg_g = QGridLayout(msg)
        msg_g.setVerticalSpacing(4)
        msg_g.setHorizontalSpacing(4)
        self.mobility_spins = []
        for i, (label, color) in enumerate(zip(['T (Ch0)', 'G (Ch1)', 'C (Ch2)', 'A (Ch3)'],
                                                  CHAN_COLORS)):
            lbl = QLabel(label)
            lbl.setStyleSheet(f'color: {color}; font-weight: bold;')
            msg_g.addWidget(lbl, i, 0)
            sp = QSpinBox()
            sp.setRange(-500, 500)
            sp.setValue(0)
            sp.setSingleStep(1)
            sp.setMinimumWidth(70)
            sp.setStyleSheet(f'QSpinBox {{ color: {color}; font-weight: bold; }}')
            sp.valueChanged.connect(self._schedule_update)
            msg_g.addWidget(sp, i, 1)
            self.mobility_spins.append(sp)
        reset_shift_btn = QPushButton('Reset shifts')
        reset_shift_btn.clicked.connect(self._reset_mobility_shifts)
        msg_g.addWidget(reset_shift_btn, 4, 0, 1, 2)
        sliders_l.addWidget(msg)

        # -- 3 plots --
        # -- Plots --
        layout.addWidget(self.canvas)

        # -- Bottom: save + ml + status --
        bottom = QHBoxLayout()
        layout.addLayout(bottom)
        self.save_btn = QPushButton('Save processed data...')
        self.save_btn.clicked.connect(self._save_data)
        bottom.addWidget(self.save_btn)
        self.ml_btn = QPushButton('Run ML basecalling')
        self.ml_btn.clicked.connect(self._run_ml)
        bottom.addWidget(self.ml_btn)
        self.peakcall_btn = QPushButton('Independent peak-call vs ESD')
        self.peakcall_btn.setToolTip(
            'Detects peaks on the separated trace itself (no ESD peak '
            'positions used as input) and aligns the result against the '
            "ESD sequence. This is the fair accuracy number - the plot's "
            "'ESD match %' samples the trace at ESD's own peak positions, "
            "which is circular.")
        self.peakcall_btn.clicked.connect(self._run_independent_peakcall)
        bottom.addWidget(self.peakcall_btn)
        self.mobility_btn = QPushButton('Auto mobility shift (calib. run)')
        self.mobility_btn.setToolTip(
            'Cross-correlates channels to estimate a constant per-channel '
            'lag. Only meaningful on a mobility/matrix calibration '
            'standard, where all 4 dyes label the same fragments - on an '
            'ordinary sequencing read the channels carry different bases '
            "at different times and don't share peak timing to correlate.")
        self.mobility_btn.clicked.connect(self._run_auto_mobility)
        bottom.addWidget(self.mobility_btn)
        self.optimize_btn = QPushButton('Optimize parameters...')
        self.optimize_btn.setToolTip(
            'Runs optimize_params.py (differential evolution) against the '
            'currently loaded well, scoring candidates by independent '
            'peak-call identity vs the ESD sequence, then loads the best '
            'settings found into these controls.')
        self.optimize_btn.clicked.connect(self._run_optimizer)
        bottom.addWidget(self.optimize_btn)
        self.reset_btn = QPushButton('Reset view')
        self.reset_btn.clicked.connect(self._reset_view)
        bottom.addWidget(self.reset_btn)
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(200)
        self.progress.setVisible(False)
        bottom.addWidget(self.progress)
        bottom.addStretch()
        self.status = QLabel('Load a well to begin')
        self.status.setStyleSheet('color: gray;')
        bottom.addWidget(self.status)

        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(50)
        self._update_timer.timeout.connect(self._update_plot)

    def _link_slider_spinbox(self, slider, spinbox):
        """Bidirectional connection with blockSignals to prevent infinite loops."""
        def on_slider(v):
            spinbox.blockSignals(True)
            spinbox.setValue(v)
            spinbox.blockSignals(False)
            self._schedule_update()
        def on_spinbox(v):
            slider.blockSignals(True)
            slider.setValue(v)
            slider.blockSignals(False)
            self._schedule_update()
        slider.valueChanged.connect(on_slider)
        spinbox.valueChanged.connect(on_spinbox)

    def _reset_mobility_shifts(self):
        for sp in self.mobility_spins:
            sp.blockSignals(True)
            sp.setValue(0)
            sp.blockSignals(False)
        self._schedule_update()

    def _save_settings(self):
        self._settings.setValue('baseline_method', self.baseline_combo.currentText())
        self._settings.setValue('baseline_window', self.bl_spin.value())
        self._settings.setValue('smooth_method', self.smooth_combo.currentText())
        self._settings.setValue('smooth_window', self.sm_win_spin.value())
        self._settings.setValue('smooth_order', self.sm_ord_spin.value())
        for r in range(4):
            for c in range(4):
                self._settings.setValue(f'matrix_{r}_{c}', self.mx_grid_spins[r][c].value())
        for ch in range(4):
            self._settings.setValue(f'mobility_shift_{ch}', self.mobility_spins[ch].value())

    def _restore_settings(self):
        def restore_combo(combo, key, default):
            val = self._settings.value(key, default)
            idx = combo.findText(val)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        def restore_spin(spin, key, default):
            spin.setValue(int(self._settings.value(key, default)))
        restore_combo(self.baseline_combo, 'baseline_method', 'Rolling Minimum')
        restore_spin(self.bl_spin, 'baseline_window', 200)
        restore_combo(self.smooth_combo, 'smooth_method', 'Savitzky-Golay')
        restore_spin(self.sm_win_spin, 'smooth_window', 7)
        restore_spin(self.sm_ord_spin, 'smooth_order', 2)
        # Force combo signal to update labels/ranges
        self._on_smooth_method_changed(self.smooth_combo.currentText())
        for r in range(4):
            for c in range(4):
                default = float(DEFAULT_SPEC_MATRIX[r, c])
                val = float(self._settings.value(f'matrix_{r}_{c}', default))
                sp = self.mx_grid_spins[r][c]
                sp.blockSignals(True)
                sp.setValue(val)
                sp.blockSignals(False)
        for ch in range(4):
            val = int(self._settings.value(f'mobility_shift_{ch}', 0))
            sp = self.mobility_spins[ch]
            sp.blockSignals(True)
            sp.setValue(val)
            sp.blockSignals(False)

    def closeEvent(self, event):
        self._save_settings()
        super().closeEvent(event)

    def _on_smooth_method_changed(self, method):
        self._smooth_mode = method
        label1, range1, label2, range2 = SMOOTH_PARAM_CONFIG.get(
            method, ('Window:', (3, 51), 'Order:', (1, 20)))
        self.sm_param1_label.setText(label1)
        self.sm_param2_label.setText(label2)
        self.sm_win_slider.setRange(*range1)
        self.sm_win_spin.setRange(*range1)
        self.sm_ord_slider.setRange(*range2)
        self.sm_ord_spin.setRange(*range2)
        self._schedule_update()

    def _on_baseline_method_changed(self, method):
        label, rng = BASELINE_PARAM_CONFIG.get(method, ('Window:', (20, 1000)))
        self.bl_param_label.setText(label)
        self.bl_spin.setRange(*rng)
        self.bl_slider.setRange(*rng)
        self._schedule_update()

    def _set_matrix(self, mat):
        mat = np.asarray(mat, dtype=np.float64)
        for r in range(4):
            for c in range(4):
                sp = self.mx_grid_spins[r][c]
                sp.blockSignals(True)
                sp.setValue(float(mat[r, c]))
                sp.blockSignals(False)
        self._schedule_update()

    def _get_matrix(self):
        mat = np.zeros((4, 4), dtype=np.float64)
        for r in range(4):
            for c in range(4):
                mat[r, c] = self.mx_grid_spins[r][c].value()
        return mat

    def _schedule_update(self):
        self._update_timer.start()

    def _populate_wells(self):
        if os.path.isdir(BASE_DIR):
            wells = sorted(f[:-4] for f in os.listdir(BASE_DIR) if f.endswith('.rsd'))
            self.well_combo.clear()
            self.well_combo.addItems(wells)
            if 'A01' in wells:
                self.well_combo.setCurrentText('A01')
        subdirs = find_esd_subdirs(BASE_DIR) if os.path.isdir(BASE_DIR) else {}
        self.esd_combo.clear()
        for k in sorted(subdirs):
            self.esd_combo.addItem(k, subdirs[k])

    def _load_data(self):
        well = self.well_combo.currentText().strip()
        if not well:
            return
        rsd_path = os.path.join(BASE_DIR, f'{well}.rsd')
        esd_subdir = self.esd_combo.currentData() or ''
        esd_path = os.path.join(BASE_DIR, esd_subdir, f'{well}.esd')
        if not os.path.exists(rsd_path):
            self.status.setText(f'Missing: {rsd_path}')
            return
        if not os.path.exists(esd_path):
            self.status.setText(f'Missing: {esd_path}')
            return
        try:
            df = parse_rsd(rsd_path)
            self.rsd_raw = df[['Channel1', 'Channel2', 'Channel3', 'Channel4']].values.astype(np.float64)
            self.x_rsd = np.arange(len(self.rsd_raw))
            self.esd_data = parse_esd(esd_path)
            self._load_esd_traces(esd_path)
            self.x_esd = np.arange(len(self.esd_traces))
            self.esd_offset = self._estimate_esd_offset(
                self.esd_data.get('peak_positions'), self.esd_traces)
            self.current_well = well
            n_peaks = len(self.esd_data.get('peak_positions', []))
            self.status.setText(f'{well}: RSD {len(self.rsd_raw)} scans, '
                                f'ESD {len(self.esd_traces)} recs, {n_peaks} peaks, '
                                f'offset~{self.esd_offset}')
            self._update_plot()
        except Exception as e:
            self.status.setText(f'Error: {e}')
            import traceback
            traceback.print_exc()

    def _estimate_esd_offset(self, peak_positions, esd_traces):
        """The base-letter positions (peak_positions from the ESD basecaller)
        are already on the correct coordinate - that's why the letters land in
        the right place. But esd_traces, the raw per-record amplitude array
        read straight off disk, is indexed independently starting at record 0,
        so its curve doesn't line up under those letters. Find the constant
        shift such that esd_traces[i] belongs at display position (i + offset)
        by directly searching for the offset that puts the largest total
        amplitude at the labeled positions."""
        if peak_positions is None or esd_traces is None:
            return 0
        peak_positions = np.asarray(peak_positions, dtype=np.int64)
        peak_positions = peak_positions[peak_positions >= 0]
        if len(peak_positions) == 0:
            return 0
        n_e = len(esd_traces)
        envelope = esd_traces.max(axis=1).astype(np.float64)
        max_pos = int(peak_positions.max())

        def score(offset):
            idx = peak_positions - offset
            m = (idx >= 0) & (idx < n_e)
            if not np.any(m):
                return -np.inf
            return float(envelope[idx[m]].sum()) / max(1, int(m.sum()))

        lo, hi = -n_e, max_pos + 1
        if hi <= lo:
            return 0
        coarse_step = max(1, (hi - lo) // 400)
        best_offset = max(range(lo, hi, coarse_step), key=score)
        best_offset = max(range(best_offset - coarse_step, best_offset + coarse_step + 1),
                           key=score)
        return int(best_offset)

    def _shift_channel(self, arr, shift):
        """Shift a 1-D channel trace by `shift` scans, padding with the edge
        value instead of wrapping around (np.roll would wrap, smearing the
        end of the trace into the start)."""
        n = len(arr)
        shift = int(np.clip(shift, -(n - 1), n - 1))
        if shift == 0:
            return arr
        out = np.empty_like(arr)
        if shift > 0:
            out[:shift] = arr[0]
            out[shift:] = arr[:-shift]
        else:
            k = -shift
            out[-k:] = arr[-1]
            out[:-k] = arr[k:]
        return out

    def _snap_to_peak_apex(self, traces, p, n_recs, back=2, fwd=15):
        """ESD-called peak positions are systematically shifted left of the true
        apex. Search a small window (mostly forward) around the called index
        and return the position of maximum channel intensity within it."""
        lo = max(0, p - back)
        hi = min(n_recs, p + fwd + 1)
        if hi <= lo:
            return p
        seg_height = traces[lo:hi].max(axis=1)
        return lo + int(np.argmax(seg_height))

    def _load_esd_traces(self, path):
        with open(path, 'rb') as f:
            raw = f.read()
        n_records = len(raw) // 20
        esd_traces = np.zeros((n_records, 4), dtype=np.float64)
        for i in range(n_records):
            try:
                ch = struct.unpack('<ffff', raw[i*20+4:(i+1)*20])
                ch = tuple(0.0 if np.isnan(c) or np.isinf(c) or abs(c) > 1000
                           else max(0.0, c) for c in ch)
                esd_traces[i] = ch
            except Exception:
                esd_traces[i] = 0.0
        # Clip spike records (metadata leakage): find the first record where
        # any channel exceeds 5, use the preceding clean region's P99.9 as cap.
        max_per_rec = esd_traces.max(axis=1)
        spikes = np.where(max_per_rec > 5)[0]
        if len(spikes) > 0:
            clean_end = spikes[0]
            clean_max = max_per_rec[:clean_end]
            limit = float(np.percentile(clean_max, 99.9))
            if 0 < limit < 1000:
                esd_traces = np.clip(esd_traces, 0, limit)
        # Trim trailing all-zero region
        non_zero = np.any(esd_traces > 0, axis=1)
        if non_zero.any():
            last_nz = np.where(non_zero)[0][-1]
            self.esd_traces = esd_traces[:last_nz + 50]
        else:
            self.esd_traces = esd_traces

    def _process(self):
        """Thin wrapper around dsp_core.full_pipeline, reading current
        widget values. The math lives in dsp_core so the exact same code
        path can be driven headlessly by optimize_params.py - if you tune
        a well there and punch the winning numbers into these sliders,
        you get identical output, because it's literally the same
        function underneath."""
        if self.rsd_raw is None:
            return None
        mobility_shifts = [sp.value() for sp in self.mobility_spins]
        return dsp_core.full_pipeline(
            self.rsd_raw,
            mobility_shifts,
            self.baseline_combo.currentText(),
            self.bl_spin.value(),
            self._smooth_mode,
            self.sm_win_spin.value(),
            self.sm_ord_spin.value(),
            self._get_matrix(),
        )

    def _save_limits(self):
        self._saved_lims = {}
        for i, ax in enumerate(self.fig.axes):
            self._saved_lims[i] = {
                'xlim': ax.get_xlim(),
                'ylim': ax.get_ylim(),
                'x_autoscale': ax.get_autoscalex_on(),
                'y_autoscale': ax.get_autoscaley_on(),
            }

    def _restore_limits(self, axes):
        for i, ax in enumerate(axes):
            if i in self._saved_lims:
                lims = self._saved_lims[i]
                if lims['y_autoscale']:
                    ax.autoscale(True, axis='y')
                else:
                    ax.autoscale(False, axis='y')
                    ax.set_ylim(lims['ylim'])
                if not lims['x_autoscale']:
                    ax.set_xlim(lims['xlim'])

    def _update_plot(self):
        if self.rsd_raw is None or self.esd_traces is None:
            return
        result = self._process()
        if result is None:
            return

        # Save current zoom state before clearing
        self._save_limits()

        raw, bl, corr, sm, separated, mix = result

        self.fig.clear()
        ax1 = self.fig.add_subplot(4, 1, 1)
        ax2 = self.fig.add_subplot(4, 1, 2, sharex=ax1)
        ax3 = self.fig.add_subplot(4, 1, 3, sharex=ax1)
        ax4 = self.fig.add_subplot(4, 1, 4, sharex=ax1)
        for ch in range(4):
            ax1.plot(self.x_rsd, raw[:, ch], color=CHAN_COLORS[ch], linewidth=0.3, alpha=0.6)
            ax1.plot(self.x_rsd, bl[:, ch], color=CHAN_COLORS[ch], linewidth=0.5,
                     linestyle='--', alpha=0.5)
        ax1.set_ylabel('Raw + baseline', fontsize=8)
        ax1.tick_params(labelbottom=False, labelsize=7)
        ax1.legend(['Ch0(T)', 'Ch1(G)', 'Ch2(C)', 'Ch3(A)'], fontsize=5, ncol=4, loc='upper right')

        # Plot 2: Corrected + smoothed
        for ch in range(4):
            ax2.plot(self.x_rsd, corr[:, ch], color=CHAN_COLORS[ch], linewidth=0.2, alpha=0.3)
            ax2.plot(self.x_rsd, sm[:, ch], color=CHAN_COLORS[ch], linewidth=0.5)
        ax2.set_ylabel('Corrected + smoothed', fontsize=8)
        ax2.tick_params(labelbottom=False, labelsize=7)

        # Plot 3: Separated vs ESD (ESD rescaled per-channel for shape comparison)
        esd_offset = getattr(self, 'esd_offset', 0)
        x_esd_aligned = self.x_esd + esd_offset
        for ch in range(4):
            ax3.plot(self.x_rsd, separated[:, ch], color=CHAN_COLORS[ch], linewidth=0.5,
                     label=f'Sep {BASE_LETTERS[ch]}')
        # Scale ESD traces to match separated range per channel
        esd_plot = self.esd_traces.copy()
        for ch in range(4):
            s_max = separated[:, ch].max()
            e_max = esd_plot[:, ch].max()
            if e_max > 0 and s_max > 0:
                esd_plot[:, ch] *= s_max / e_max
        for ch in range(4):
            ax3.plot(x_esd_aligned, esd_plot[:, ch], color=CHAN_COLORS[ch], linewidth=0.3,
                     linestyle=':', alpha=0.5)
        ax3.set_ylabel('Separated (+ ESD scaled)', fontsize=8)
        ax3.tick_params(labelbottom=False, labelsize=7)
        if esd_offset:
            ax3.text(0.01, 0.95, f'ESD trace shifted +{esd_offset} to align under labels',
                     transform=ax3.transAxes, fontsize=6, ha='left', va='top',
                     color='gray')

        # Add base labels: letter is always derived from the dominant channel
        # at the peak, so it matches its color by construction
        peaks = self.esd_data.get('peak_positions')
        seq = self.esd_data.get('sequence', '')
        if peaks is not None:
            n_esd_recs = len(self.esd_traces)
            sep_max = separated.max(axis=0)
            for p in peaks:
                p = int(p)
                native_guess = p - esd_offset
                if native_guess < 0 or native_guess >= n_esd_recs:
                    continue
                p_apex_native = self._snap_to_peak_apex(self.esd_traces, native_guess, n_esd_recs)
                trace = self.esd_traces[p_apex_native]
                dom_ch = np.argmax(trace) if np.any(trace > 0) else -1
                if dom_ch < 0:
                    continue
                color = CHAN_COLORS[dom_ch]
                base = BASE_LETTERS[dom_ch]
                x_disp = p_apex_native + esd_offset
                if 0 <= x_disp < len(separated) and sep_max[dom_ch] > 0:
                    y_disp = separated[x_disp, dom_ch] + 0.05 * sep_max[dom_ch]
                    ax3.text(x_disp, y_disp, base, fontsize=6, ha='center', va='bottom',
                             color=color, clip_on=True, fontweight='bold')
                else:
                    ax3.text(x_disp, 0.94, base, transform=ax3.get_xaxis_transform(),
                             fontsize=6, ha='center', va='top',
                             color=color, clip_on=True, fontweight='bold')
                ax3.axvline(x=x_disp, color=color, alpha=0.08, linewidth=0.3)

        # Plot 4: ESD traces with peaks (standalone, autoscaled y-axis)
        for ch in range(4):
            ax4.plot(x_esd_aligned, self.esd_traces[:, ch], color=CHAN_COLORS[ch], linewidth=0.5,
                     label=f'ESD {BASE_LETTERS[ch]}')
        ax4.set_ylabel('ESD traces', fontsize=8)
        ax4.set_xlabel('Scan / Record index (aligned)', fontsize=8)
        ax4.tick_params(labelsize=7)
        ax4.legend(fontsize=5, ncol=4, loc='upper right')

        if peaks is not None:
            n_esd_recs = len(self.esd_traces)
            esd_max = self.esd_traces.max(axis=0)
            for p in peaks:
                p = int(p)
                native_guess = p - esd_offset
                if native_guess < 0 or native_guess >= n_esd_recs:
                    continue
                p_apex_native = self._snap_to_peak_apex(self.esd_traces, native_guess, n_esd_recs)
                trace = self.esd_traces[p_apex_native]
                dom_ch = np.argmax(trace) if np.any(trace > 0) else -1
                if dom_ch < 0:
                    continue
                color = CHAN_COLORS[dom_ch]
                base = BASE_LETTERS[dom_ch]
                x_disp = p_apex_native + esd_offset
                y_disp = trace[dom_ch] + 0.05 * max(esd_max[dom_ch], 1e-9)
                ax4.axvline(x=x_disp, color=color, alpha=0.12, linewidth=0.3)
                ax4.text(x_disp, y_disp, base, fontsize=6, ha='center', va='bottom',
                         color=color, clip_on=True, fontweight='bold')

        # Show matrix info
        cond = np.linalg.cond(mix)
        ax3.text(0.99, 0.01, f'cond={cond:.2f}', transform=ax3.transAxes,
                fontsize=7, ha='right', va='bottom', color='gray',
                bbox=dict(facecolor='white', alpha=0.7, pad=1))

        # Show ESD match percentage
        if peaks is not None and seq:
            n = min(len(seq), len(peaks))
            called = []
            for i in range(n):
                p = int(peaks[i])
                if 0 <= p < len(separated):
                    ch = np.argmax(separated[p])
                    called.append(CHEM_MAP[ch])
                else:
                    called.append('N')
            matches = sum(1 for a, b in zip(called, seq) if a == b)
            pct = matches / n * 100 if n > 0 else 0
            ax3.text(0.99, 0.07, f'ESD match: {pct:.1f}%', transform=ax3.transAxes,
                    fontsize=7, ha='right', va='bottom', color='blue',
                    bbox=dict(facecolor='white', alpha=0.7, pad=1))

        self.fig.subplots_adjust(hspace=0.08, left=0.05, right=0.98, top=0.97, bottom=0.05)

        # Restore zoom state from before the redraw
        self._restore_limits([ax1, ax2, ax3, ax4])

        # Label x-axis only on bottom-most plot
        for ax in [ax1, ax2, ax3]:
            ax.set_xlabel('')
        ax4.set_xlabel('Scan / Record index (aligned)', fontsize=8)

        self.canvas.draw()

    def _save_data(self):
        if self.rsd_raw is None:
            return
        result = self._process()
        if result is None:
            return
        raw, bl, corr, sm, separated, mix = result
        dir_path = QFileDialog.getExistingDirectory(self, 'Select save directory')
        if not dir_path:
            return
        well = self.current_well or 'unknown'
        np.savez(os.path.join(dir_path, f'{well}_processed.npz'),
                 raw=raw, baseline=bl, corrected=corr, smoothed=sm,
                 separated=separated, mixing_matrix=mix,
                 esd_traces=self.esd_traces)
        with open(os.path.join(dir_path, f'{well}_matrix.json'), 'w') as f:
            json.dump({
                'well': well,
                'matrix': mix.tolist(),
                'diagonals': np.diag(mix).tolist(),
                'baseline_window': self.bl_spin.value(),
                'smooth_window': self.sm_win_spin.value(),
                'smooth_order': self.sm_ord_spin.value(),
                'mobility_shifts': [sp.value() for sp in self.mobility_spins],
                'condition': float(np.linalg.cond(mix)),
            }, f, indent=2)
        self.status.setText(f'Saved to {dir_path}')

    def _run_ml(self):
        if self.current_well is None:
            self.status.setText('Load a well first')
            return
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status.setText('Running ML basecalling...')
        QApplication.processEvents()

        import tempfile
        tmp = tempfile.mkdtemp(prefix='seq_gui_')
        result = self._process()
        if result is None:
            return
        raw, bl, corr, sm, separated, mix = result

        # Save processed data for ML
        well = self.current_well
        data_path = os.path.join(tmp, f'{well}_processed.npz')
        np.savez(data_path, raw=raw, corrected=corr, smoothed=sm,
                 separated=separated, matrix=mix,
                 esd_traces=self.esd_traces,
                 esd_peaks=self.esd_data.get('peak_positions', []),
                 esd_sequence=self.esd_data.get('sequence', ''))

        # Get ESD positions and run simple argmax basecalling
        esd_path = os.path.join(BASE_DIR,
                                self.esd_combo.currentData() or '',
                                f'{well}.esd')
        esd_data = parse_esd(esd_path)
        positions = esd_data.get('peak_positions')
        seq = esd_data.get('sequence', '')
        if positions is None or not seq:
            self.status.setText('No ESD peaks to evaluate')
            self.progress.setVisible(False)
            return

        # Clamp positions to valid range
        n_sep = len(separated)
        valid = np.where((positions >= 0) & (positions < n_sep))[0]
        positions = positions[valid]
        seq_list = list(seq)
        seq = ''.join(seq_list[i] for i in valid if i < len(seq_list))

        # Argmax basecalling on separated data
        n = min(len(seq), len(positions))
        called = []
        for i in range(n):
            p = int(positions[i])
            if 0 <= p < len(separated):
                ch = np.argmax(separated[p])
                called.append(CHEM_MAP[ch])
            else:
                called.append('N')
        called = ''.join(called)
        seq = seq[:n]

        # Evaluate vs ESD
        matches = sum(1 for a, b in zip(called, seq) if a == b)
        esd_identity = matches / n * 100 if n > 0 else 0

        # Evaluate vs M13
        from simple_align import M13_REFERENCE
        q = ''.join(c for c in called if c in 'ACGT')
        m13_identity = 0
        if len(q) >= 20:
            q_al, r_al = self._nw_align(q, M13_REFERENCE)
            m13_match = sum(1 for a, b in zip(q_al, r_al) if a == b)
            m13_identity = m13_match / len(q_al) * 100 if q_al else 0

        self.progress.setValue(100)
        self.status.setText(f'Argmax: vs ESD={esd_identity:.1f}%, vs M13={m13_identity:.2f}%')
        QTimer.singleShot(2000, lambda: self.progress.setVisible(False))

    def _run_independent_peakcall(self):
        """Run a real peak detector on the separated trace (no ESD peak
        positions involved) and align the result against ESD's sequence.
        This is the number to trust over the plot's 'ESD match %', which
        only samples the trace at positions ESD already told it were
        peaks."""
        if self.rsd_raw is None or self.esd_data is None:
            self.status.setText('Load a well first')
            return
        result = self._process()
        if result is None:
            return
        _, _, _, _, separated, _ = result
        esd_seq = self.esd_data.get('sequence', '')
        if not esd_seq:
            self.status.setText('No ESD sequence to compare against')
            return
        positions, called_seq, heights = peak_calling.call_bases(separated)
        identity = peak_calling.nw_identity(called_seq, esd_seq, max_len=20000)
        self.status.setText(
            f'Independent peak-call: {len(called_seq)} bases called '
            f'(ESD has {len(esd_seq)}) - alignment identity vs ESD: '
            f'{identity:.1f}%')

    def _run_auto_mobility(self):
        """Cross-correlation-based mobility shift estimate. Only reliable
        on a calibration/mobility-standard run - see the button tooltip
        and peak_calling.estimate_mobility_shifts's docstring for why an
        ordinary sequencing read doesn't give this a fair signal to lock
        onto."""
        if self.rsd_raw is None:
            self.status.setText('Load a well first')
            return
        shifts = peak_calling.estimate_mobility_shifts(self.rsd_raw, ref_channel=3)
        for ch, sp in enumerate(self.mobility_spins):
            sp.blockSignals(True)
            sp.setValue(int(np.clip(shifts[ch], sp.minimum(), sp.maximum())))
            sp.blockSignals(False)
        self._schedule_update()
        self.status.setText(
            f'Auto mobility shift (calibration-run estimate): {list(shifts)} '
            '- verify against a known standard before trusting on real reads')

    def _run_optimizer(self):
        """Shell out to optimize_params.py for the current well only (a
        quick, single-well search - point the standalone script at more
        wells from the command line for a search that generalizes better)
        and load the winning settings into the controls."""
        if self.current_well is None:
            self.status.setText('Load a well first')
            return
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'optimize_params.py')
        if not os.path.exists(script):
            self.status.setText('optimize_params.py not found next to this script')
            return
        esd_subdir = self.esd_combo.currentData() or ''
        out_path = os.path.join(tempfile.mkdtemp(prefix='optimize_'), 'best_params.json')
        self.status.setText(f'Optimizing parameters for well {self.current_well} '
                             '(this can take a minute)...')
        self.progress.setVisible(True)
        self.progress.setValue(0)
        QApplication.processEvents()
        cmd = [sys.executable, script, '--base-dir', BASE_DIR,
               '--wells', self.current_well, '--maxiter', '40',
               '--popsize', '12', '--out', out_path]
        if esd_subdir:
            subdirs = find_esd_subdirs(BASE_DIR)
            for name, d in subdirs.items():
                if d == esd_subdir:
                    cmd += ['--esd-subdir', name]
                    break
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800)
        except subprocess.CalledProcessError as e:
            self.progress.setVisible(False)
            self.status.setText(f'Optimizer failed: {e.stderr[-300:] if e.stderr else e}')
            return
        except subprocess.TimeoutExpired:
            self.progress.setVisible(False)
            self.status.setText('Optimizer timed out after 30 minutes')
            return
        self.progress.setValue(100)
        try:
            with open(out_path) as f:
                best = json.load(f)
        except Exception as e:
            self.progress.setVisible(False)
            self.status.setText(f'Could not read optimizer output: {e}')
            return

        idx = self.baseline_combo.findText(best['baseline_method'])
        if idx >= 0:
            self.baseline_combo.setCurrentIndex(idx)
        self.bl_spin.setValue(int(round(best['baseline_window'])))
        idx = self.smooth_combo.findText(best['smooth_method'])
        if idx >= 0:
            self.smooth_combo.setCurrentIndex(idx)
        self.sm_win_spin.setValue(int(round(best['smooth_window'])))
        self.sm_ord_spin.setValue(int(round(best['smooth_order'])))
        for ch, sp in enumerate(self.mobility_spins):
            sp.blockSignals(True)
            sp.setValue(int(best['mobility_shifts'][ch]))
            sp.blockSignals(False)
        self._set_matrix(np.array(best['matrix']))
        QTimer.singleShot(1500, lambda: self.progress.setVisible(False))
        self.status.setText(
            f"Optimizer found {best['best_identity_pct']:.1f}% identity vs ESD "
            f"with {best['baseline_method']}/{best['smooth_method']} - loaded into controls")

    def _nw_align(self, q, r, match=1, mismatch=-1, gap=-2):
        m, n = len(q), len(r)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(1, m + 1):
            dp[i][0] = dp[i-1][0] + gap
        for j in range(1, n + 1):
            dp[0][j] = dp[0][j-1] + gap
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                diag = dp[i-1][j-1] + (match if q[i-1] == r[j-1] else mismatch)
                up = dp[i-1][j] + gap
                left = dp[i][j-1] + gap
                dp[i][j] = max(diag, up, left)
        i, j = m, n
        q_al, r_al = [], []
        while i > 0 or j > 0:
            if i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + (match if q[i-1] == r[j-1] else mismatch):
                q_al.append(q[i-1]); r_al.append(r[j-1]); i -= 1; j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + gap:
                q_al.append(q[i-1]); r_al.append('-'); i -= 1
            else:
                q_al.append('-'); r_al.append(r[j-1]); j -= 1
        return ''.join(reversed(q_al)), ''.join(reversed(r_al))


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self._reset_view()
        elif event.key() == Qt.Key_L:
            self._load_data()

    def _reset_view(self):
        self._saved_lims = {}
        for ax in self.fig.axes:
            ax.autoscale(True)
        self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = SequencingGUI()
    window.show()
    sys.exit(app.exec_())
