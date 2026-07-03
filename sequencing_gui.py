#!/usr/bin/env python3
"""Sequencing basecaller GUI with adjustable preprocessing and real-time plots.

Load RSD + ESD for one well. Tune baseline, smoothing, and matrix parameters
via sliders. 3 plots show the effect of each processing stage in real time.
Save processed data and run ML basecalling.
"""
import sys, os, struct, json, subprocess
import numpy as np
from scipy.ndimage import minimum_filter1d, gaussian_filter1d
from scipy.signal import savgol_filter

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QGroupBox, QGridLayout, QSlider, QTextEdit, QSplitter, QTabWidget,
    QFileDialog, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd

BASE_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"
CHAN_COLORS = ['red', 'green', 'blue', 'orange']
BASE_LETTERS = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}
CHEM_MAP = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}

DEFAULT_SPEC_MATRIX = np.array([
    [0.85, 0.03, 0.05, 0.07],
    [0.02, 0.88, 0.04, 0.06],
    [0.06, 0.04, 0.86, 0.04],
    [0.07, 0.05, 0.05, 0.83],
], dtype=np.float64)

# Off-diagonal pattern from DEFAULT (fraction of bleed to each other channel)
OFF_PATTERN = np.array([
    [0.00, 0.20, 0.33, 0.47],
    [0.17, 0.00, 0.33, 0.50],
    [0.43, 0.29, 0.00, 0.29],
    [0.41, 0.29, 0.29, 0.00],
], dtype=np.float64)


def find_esd_subdirs(base_dir):
    dirs = {}
    for d in sorted(os.listdir(base_dir)):
        dp = os.path.join(base_dir, d)
        if os.path.isdir(dp) and d.endswith('_MD1'):
            name = d.replace('MB1000_M13_DT_', '').replace('_MD1', '')
            dirs[name] = d
    return dirs


def make_matrix_from_diagonals(diag):
    """Build 4x4 mixing matrix from 4 diagonal values.
    Off-diagonals follow DEFAULT pattern scaled to (1-diag) total bleed."""
    mix = np.zeros((4, 4), dtype=np.float64)
    for col in range(4):
        bleed = 1.0 - diag[col]
        pattern = OFF_PATTERN[:, col].copy()
        pattern[col] = 0
        psum = pattern.sum()
        if psum > 0:
            pattern = pattern / psum * bleed
        pattern[col] = diag[col]
        mix[:, col] = pattern
    return mix


class SequencingGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Sequencing Basecaller GUI')
        self.setGeometry(50, 50, 1500, 950)
        self.rsd_raw = None
        self.esd_traces = None
        self.esd_data = None
        self.current_well = None
        self._saved_lims = {}
        self._setup_ui()
        self._populate_wells()

    def _setup_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setContentsMargins(4, 4, 4, 4)

        # -- Top bar: well selector + load --
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
        top.addStretch()

        # -- Sliders panel --
        sliders_w = QWidget()
        sliders_l = QHBoxLayout(sliders_w)
        sliders_l.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(sliders_w)

        # Baseline group
        blg = QGroupBox('Baseline')
        blg_g = QVBoxLayout(blg)
        blg_g.addWidget(QLabel('Rolling Min window:'))
        hl = QHBoxLayout()
        self.bl_slider = QSlider(Qt.Horizontal)
        self.bl_slider.setRange(20, 1000)
        self.bl_slider.setValue(200)
        self.bl_slider.setSingleStep(10)
        self.bl_spin = QSpinBox()
        self.bl_spin.setRange(20, 1000)
        self.bl_spin.setValue(200)
        self.bl_spin.setSingleStep(10)
        self.bl_slider.valueChanged.connect(lambda v: self.bl_spin.setValue(v))
        self.bl_spin.valueChanged.connect(lambda v: self.bl_slider.setValue(v))
        self.bl_spin.valueChanged.connect(self._schedule_update)
        hl.addWidget(self.bl_slider)
        hl.addWidget(self.bl_spin)
        blg_g.addLayout(hl)
        sliders_l.addWidget(blg)

        # Smoothing group
        smg = QGroupBox('Smooth')
        smg_g = QVBoxLayout(smg)
        hl1 = QHBoxLayout()
        hl1.addWidget(QLabel('Window:'))
        sm_win = QSlider(Qt.Horizontal)
        sm_win.setRange(3, 31)
        sm_win.setValue(7)
        sm_win.setSingleStep(2)
        sm_win.setTickPosition(QSlider.TicksBelow)
        self.sm_win_spin = QSpinBox()
        self.sm_win_spin.setRange(3, 31)
        self.sm_win_spin.setValue(7)
        self.sm_win_spin.setSingleStep(2)
        sm_win.valueChanged.connect(lambda v: self.sm_win_spin.setValue(v))
        self.sm_win_spin.valueChanged.connect(lambda v: sm_win.setValue(v))
        self.sm_win_spin.valueChanged.connect(self._schedule_update)
        hl1.addWidget(sm_win)
        hl1.addWidget(self.sm_win_spin)
        smg_g.addLayout(hl1)
        hl2 = QHBoxLayout()
        hl2.addWidget(QLabel('Order:'))
        sm_ord = QSlider(Qt.Horizontal)
        sm_ord.setRange(1, 5)
        sm_ord.setValue(2)
        self.sm_ord_spin = QSpinBox()
        self.sm_ord_spin.setRange(1, 5)
        self.sm_ord_spin.setValue(2)
        sm_ord.valueChanged.connect(lambda v: self.sm_ord_spin.setValue(v))
        self.sm_ord_spin.valueChanged.connect(lambda v: sm_ord.setValue(v))
        self.sm_ord_spin.valueChanged.connect(self._schedule_update)
        hl2.addWidget(sm_ord)
        hl2.addWidget(self.sm_ord_spin)
        smg_g.addLayout(hl2)
        sliders_l.addWidget(smg)

        # Matrix group: 4 diagonal sliders
        mxg = QGroupBox('Matrix (diagonal per base)')
        mxg_g = QGridLayout(mxg)
        self.mx_sliders = []
        self.mx_spins = []
        for i, label in enumerate(['T (Ch0)', 'G (Ch1)', 'C (Ch2)', 'A (Ch3)']):
            mxg_g.addWidget(QLabel(label), i, 0)
            sl = QSlider(Qt.Horizontal)
            sl.setRange(25, 100)
            sl.setValue(85)  # Default ~0.85
            sl.setTickPosition(QSlider.TicksBelow)
            sp = QSpinBox()
            sp.setRange(25, 100)
            sp.setValue(85)
            sp.setSuffix('%')
            sl.valueChanged.connect(lambda v, s=sp: s.setValue(v))
            sp.valueChanged.connect(lambda v, s=sl: s.setValue(v))
            sp.valueChanged.connect(self._schedule_update)
            mxg_g.addWidget(sl, i, 1)
            mxg_g.addWidget(sp, i, 2)
            self.mx_sliders.append(sl)
            self.mx_spins.append(sp)
        # Preset buttons
        preset_l = QHBoxLayout()
        for name, vals in [('Default', [85, 88, 86, 83]),
                           ('Identity', [100, 100, 100, 100]),
                           ('Uniform', [50, 50, 50, 50])]:
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, v=vals: self._set_matrix(v))
            preset_l.addWidget(btn)
        mxg_g.addLayout(preset_l, 4, 0, 1, 3)
        sliders_l.addWidget(mxg)

        # -- 3 plots --
        self.fig = Figure(figsize=(14, 11), dpi=100)
        self.fig.subplots_adjust(hspace=0.08, left=0.05, right=0.98, top=0.97, bottom=0.05)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        layout.addWidget(self.toolbar)
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

    def _set_matrix(self, vals):
        for sl, sp, v in zip(self.mx_sliders, self.mx_spins, vals):
            sl.setValue(v)
            sp.setValue(v)

    def _schedule_update(self):
        self._update_timer.start()

    def _populate_wells(self):
        if os.path.isdir(BASE_DIR):
            wells = sorted(f[:-4] for f in os.listdir(BASE_DIR) if f.endswith('.rsd'))
            self.well_combo.clear()
            self.well_combo.addItems(wells)
            if 'A01' in wells:
                self.well_combo.setCurrentText('A01')
        subdirs = find_esd_subdirs(BASE_DIR)
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
            self.current_well = well
            n_peaks = len(self.esd_data.get('peak_positions', []))
            self.status.setText(f'{well}: RSD {len(self.rsd_raw)} scans, '
                                f'ESD {len(self.esd_traces)} recs, {n_peaks} peaks')
            self._update_plot()
        except Exception as e:
            self.status.setText(f'Error: {e}')
            import traceback
            traceback.print_exc()

    def _load_esd_traces(self, path):
        with open(path, 'rb') as f:
            raw = f.read()
        n_records = len(raw) // 20
        self.esd_traces = np.zeros((n_records, 4), dtype=np.float64)
        for i in range(n_records):
            try:
                ch = struct.unpack('<ffff', raw[i*20+4:(i+1)*20])
                # Filter extreme values (metadata leakage into trace data)
                ch = tuple(0.0 if np.isnan(c) or np.isinf(c) or abs(c) > 1000 else c for c in ch)
                self.esd_traces[i] = ch
            except Exception:
                self.esd_traces[i] = 0.0

    def _process(self):
        if self.rsd_raw is None:
            return None, None, None, None
        raw = self.rsd_raw.copy()

        # Baseline
        bw = self.bl_spin.value()
        bl = np.zeros_like(raw)
        for ch in range(4):
            bl[:, ch] = minimum_filter1d(raw[:, ch], size=bw, mode='reflect')
        corr = np.clip(raw - bl, 0, None)

        # Smooth
        sw = self.sm_win_spin.value()
        so = self.sm_ord_spin.value()
        if sw > so + 1 and sw % 2 == 1:
            sm = corr.copy()
            for ch in range(4):
                sm[:, ch] = savgol_filter(sm[:, ch], sw, so)
        else:
            sm = corr.copy()

        # Matrix separation
        diag = np.array([s.value() / 100.0 for s in self.mx_sliders])
        mix = make_matrix_from_diagonals(diag)
        inv = np.linalg.inv(mix)
        bm = np.median(bl, axis=0)
        gn = sm / (bm[np.newaxis, :] + 1e-10)
        separated = gn @ inv.T
        separated = np.clip(separated, 0, None)

        return raw, bl, corr, sm, separated, mix

    def _save_limits(self):
        """Save current axis limits before redraw."""
        self._saved_lims = {}
        for i, ax in enumerate(self.fig.axes):
            self._saved_lims[i] = {
                'xlim': ax.get_xlim(),
                'ylim': ax.get_ylim(),
                'x_autoscale': ax.get_autoscalex_on(),
                'y_autoscale': ax.get_autoscaley_on(),
            }

    def _restore_limits(self, axes):
        """Restore saved axis limits after redraw."""
        for i, ax in enumerate(axes):
            if i in self._saved_lims:
                lims = self._saved_lims[i]
                if not lims['x_autoscale']:
                    ax.set_xlim(lims['xlim'])
                if not lims['y_autoscale']:
                    ax.set_ylim(lims['ylim'])

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

        # Plot 3: Separated vs ESD
        for ch in range(4):
            ax3.plot(self.x_rsd, separated[:, ch], color=CHAN_COLORS[ch], linewidth=0.5,
                     label=f'Sep {BASE_LETTERS[ch]}')
        for ch in range(4):
            ax3.plot(self.x_esd, self.esd_traces[:, ch], color=CHAN_COLORS[ch], linewidth=0.3,
                     linestyle=':', alpha=0.5)
        ax3.set_ylabel('Separated + ESD (dotted)', fontsize=8)
        ax3.set_xlabel('Scan / Record index', fontsize=8)
        ax3.tick_params(labelsize=7)

        # Add base labels from ESD
        peaks = self.esd_data.get('peak_positions')
        seq = self.esd_data.get('sequence', '')
        if peaks is not None and seq:
            n_esd_recs = len(self.esd_traces)
            for p, base in zip(peaks, seq):
                p = int(p)
                if p >= n_esd_recs:
                    continue
                trace = self.esd_traces[p]
                dom_ch = np.argmax(trace) if np.any(trace > 0) else -1
                if dom_ch < 0:
                    continue
                dom_base = BASE_LETTERS[dom_ch]
                color = 'black' if base == dom_base else 'red'
                ax3.axvline(x=p, color='gray', alpha=0.08, linewidth=0.3)
                ax3.text(p, 0.95, base, fontsize=4, ha='center', va='top',
                         color=color, clip_on=True,
                         bbox=dict(boxstyle='round,pad=0.02', facecolor='white',
                                   alpha=0.6, edgecolor=color))

        # Plot 4: ESD traces with peaks
        for ch in range(4):
            ax4.plot(self.x_esd, self.esd_traces[:, ch], color=CHAN_COLORS[ch], linewidth=0.5)
        ax4.set_ylabel('ESD traces', fontsize=8)
        ax4.set_xlabel('Scan / Record index', fontsize=8)
        ax4.tick_params(labelsize=7)

        if peaks is not None and seq:
            n_esd_recs = len(self.esd_traces)
            for p, base in zip(peaks, seq):
                p = int(p)
                if p >= n_esd_recs:
                    continue
                trace = self.esd_traces[p]
                dom_ch = np.argmax(trace) if np.any(trace > 0) else -1
                if dom_ch < 0:
                    continue
                dom_base = BASE_LETTERS[dom_ch]
                color = 'black' if base == dom_base else 'red'
                ax4.axvline(x=p, color='gray', alpha=0.12, linewidth=0.3)
                ax4.text(p, 0.95, base, fontsize=4, ha='center', va='top',
                         color=color, clip_on=True,
                         bbox=dict(boxstyle='round,pad=0.02', facecolor='white',
                                   alpha=0.6, edgecolor=color))

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
                'diagonals': [s.value() / 100.0 for s in self.mx_sliders],
                'baseline_window': self.bl_spin.value(),
                'smooth_window': self.sm_win_spin.value(),
                'smooth_order': self.sm_ord_spin.value(),
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
        diag = np.array([s.value() / 100.0 for s in self.mx_sliders])

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
        valid_mask = (positions >= 0) & (positions < n_sep)

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
