#!/usr/bin/env python3
"""Interactive RSD+ESD trace explorer with synchronized zoom.

Stacked view: RSD raw -> RSD baseline-corrected -> RSD separated -> ESD traces
All subplots share the same x-axis zoom for direct comparison.
"""
import sys, os, struct
import numpy as np
from scipy.ndimage import minimum_filter1d
from scipy.signal import savgol_filter

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QCheckBox, QPushButton, QGroupBox,
    QGridLayout, QTextEdit
)
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd

BASE_DIR = os.path.join(os.path.dirname(__file__), 'MB1000_M13_DT')
CHAN_NAMES_RSD = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
CHAN_COLORS = ['red', 'green', 'blue', 'orange']
BASE_LETTERS = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}

DEFAULT_SPEC_MATRIX = np.array([
    [0.85, 0.03, 0.05, 0.07],
    [0.02, 0.88, 0.04, 0.06],
    [0.06, 0.04, 0.86, 0.04],
    [0.07, 0.05, 0.05, 0.83],
], dtype=np.float64)


def find_esd_subdirs(base_dir):
    dirs = {}
    for d in sorted(os.listdir(base_dir)):
        dp = os.path.join(base_dir, d)
        if os.path.isdir(dp) and d.endswith('_MD1'):
            name = d.replace('MB1000_M13_DT_', '').replace('_MD1', '')
            dirs[name] = d
    return dirs


class TraceExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('RSD + ESD Trace Explorer')
        self.setGeometry(100, 100, 1400, 900)
        self.rsd_data = None
        self.esd_data = None
        self.esd_traces = None
        self.current_well = None
        self._axes = []
        self._x_rsd = None
        self._x_esd = None
        self._init_ui()
        self._populate_wells()

    def _init_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setContentsMargins(4, 4, 4, 4)

        ctrl = QHBoxLayout()
        layout.addLayout(ctrl)
        ctrl.addWidget(QLabel('Well:'))
        self.well_combo = QComboBox()
        self.well_combo.setEditable(True)
        ctrl.addWidget(self.well_combo)
        self.load_btn = QPushButton('Load')
        self.load_btn.clicked.connect(self._load_data)
        ctrl.addWidget(self.load_btn)
        ctrl.addWidget(QLabel('  ESD:'))
        self.esd_combo = QComboBox()
        ctrl.addWidget(self.esd_combo)
        ctrl.addStretch()

        proc = QHBoxLayout()
        layout.addLayout(proc)

        blg = QGroupBox('Baseline')
        blg_grid = QGridLayout(blg)
        self.bl_check = QCheckBox('On')
        self.bl_check.setChecked(True)
        self.bl_check.stateChanged.connect(self._update_plot)
        blg_grid.addWidget(self.bl_check, 0, 0)
        blg_grid.addWidget(QLabel('Window:'), 0, 1)
        self.bl_window = QSpinBox()
        self.bl_window.setRange(10, 1000)
        self.bl_window.setValue(200)
        self.bl_window.setSingleStep(10)
        self.bl_window.valueChanged.connect(self._update_plot)
        blg_grid.addWidget(self.bl_window, 0, 2)
        proc.addWidget(blg)

        smg = QGroupBox('Smooth')
        smg_grid = QGridLayout(smg)
        self.sm_check = QCheckBox('On')
        self.sm_check.setChecked(True)
        self.sm_check.stateChanged.connect(self._update_plot)
        smg_grid.addWidget(self.sm_check, 0, 0)
        smg_grid.addWidget(QLabel('Win:'), 0, 1)
        self.sm_window = QSpinBox()
        self.sm_window.setRange(3, 31)
        self.sm_window.setValue(7)
        self.sm_window.setSingleStep(2)
        self.sm_window.valueChanged.connect(self._update_plot)
        smg_grid.addWidget(self.sm_window, 0, 2)
        smg_grid.addWidget(QLabel('Ord:'), 0, 3)
        self.sm_order = QSpinBox()
        self.sm_order.setRange(1, 5)
        self.sm_order.setValue(2)
        self.sm_order.valueChanged.connect(self._update_plot)
        smg_grid.addWidget(self.sm_order, 0, 4)
        proc.addWidget(smg)

        mxg = QGroupBox('Matrix')
        mxg_grid = QGridLayout(mxg)
        self.mx_check = QCheckBox('On')
        self.mx_check.setChecked(True)
        self.mx_check.stateChanged.connect(self._update_plot)
        mxg_grid.addWidget(self.mx_check, 0, 0)
        self.mx_combo = QComboBox()
        self.mx_combo.addItems(['Default', 'Identity', 'From data'])
        self.mx_combo.currentIndexChanged.connect(self._update_plot)
        mxg_grid.addWidget(self.mx_combo, 0, 1)
        self.gain_check = QCheckBox('Gain norm')
        self.gain_check.setChecked(True)
        self.gain_check.stateChanged.connect(self._update_plot)
        mxg_grid.addWidget(self.gain_check, 0, 2)
        proc.addWidget(mxg)

        dpg = QGroupBox('Show')
        dpg_grid = QGridLayout(dpg)
        self.show_raw = QCheckBox('RSD raw')
        self.show_raw.setChecked(True)
        self.show_raw.stateChanged.connect(self._update_plot)
        dpg_grid.addWidget(self.show_raw, 0, 0)
        self.show_corr = QCheckBox('RSD corr')
        self.show_corr.setChecked(True)
        self.show_corr.stateChanged.connect(self._update_plot)
        dpg_grid.addWidget(self.show_corr, 0, 1)
        self.show_sep = QCheckBox('RSD sep')
        self.show_sep.setChecked(True)
        self.show_sep.stateChanged.connect(self._update_plot)
        dpg_grid.addWidget(self.show_sep, 1, 0)
        self.show_esd = QCheckBox('ESD')
        self.show_esd.setChecked(True)
        self.show_esd.stateChanged.connect(self._update_plot)
        dpg_grid.addWidget(self.show_esd, 1, 1)
        self.show_bases = QCheckBox('Bases')
        self.show_bases.setChecked(True)
        dpg_grid.addWidget(self.show_bases, 0, 2, 2, 1, Qt.AlignCenter)
        self.show_bases.stateChanged.connect(self._update_plot)
        proc.addWidget(dpg)

        self.fig = Figure(figsize=(14, 8), dpi=100)
        self.fig.subplots_adjust(hspace=0.05, left=0.05, right=0.98, top=0.97, bottom=0.06)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        self.status = QTextEdit()
        self.status.setMaximumHeight(60)
        self.status.setReadOnly(True)
        layout.addWidget(self.status)

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
            self.rsd_data = parse_rsd(rsd_path)[CHAN_NAMES_RSD].values.astype(np.float64)
            self.esd_data = parse_esd(esd_path)
            self._load_esd_traces(esd_path)
            self.current_well = well
            self._x_rsd = np.arange(len(self.rsd_data))
            self._x_esd = np.arange(len(self.esd_traces))
            n_peaks = len(self.esd_data.get('peak_positions', []))
            self.status.setText(f'{well}: RSD {len(self.rsd_data)} scans, '
                                f'ESD {len(self.esd_traces)} recs, {n_peaks} peaks')
            self._update_plot()
        except Exception as e:
            self.status.setText(f'Error: {e}')
            import traceback
            traceback.print_exc()

    def _load_esd_traces(self, path):
        with open(path, 'rb') as f:
            raw = f.read()
        data_end = 8754
        self.esd_traces = np.zeros((data_end, 4), dtype=np.float64)
        for i in range(data_end):
            self.esd_traces[i] = struct.unpack('<ffff', raw[i*20+4:(i+1)*20])

    def _process_rsd(self):
        if self.rsd_data is None:
            return None, None, None
        raw = self.rsd_data.copy()
        if self.bl_check.isChecked():
            bl = np.zeros_like(raw)
            w = self.bl_window.value()
            for ch in range(4):
                bl[:, ch] = minimum_filter1d(raw[:, ch], size=w, mode='reflect')
            corr = np.clip(raw - bl, 0, None)
        else:
            corr = raw.copy()
        if self.sm_check.isChecked():
            w = self.sm_window.value()
            o = self.sm_order.value()
            if w > o + 1 and w % 2 == 1:
                for ch in range(4):
                    corr[:, ch] = savgol_filter(corr[:, ch], w, o)
        if self.mx_check.isChecked():
            preset = self.mx_combo.currentText()
            if preset == 'Identity':
                mix = np.eye(4)
            elif preset == 'From data':
                mix = self._derive_matrix()
            else:
                mix = DEFAULT_SPEC_MATRIX
            bl = minimum_filter1d(self.rsd_data, size=self.bl_window.value(), mode='reflect')
            bm = np.median(bl, axis=0)
            gn = corr / (bm[np.newaxis, :] + 1e-10) if self.gain_check.isChecked() and bm.min() > 0 else corr
            sep_mat = np.linalg.inv(mix)
            separated = gn @ sep_mat.T
        else:
            separated = corr.copy()
        return raw, corr, separated

    def _derive_matrix(self):
        if self.rsd_data is None or self.esd_data is None:
            return DEFAULT_SPEC_MATRIX
        peaks = self.esd_data.get('peak_positions')
        seq = self.esd_data.get('sequence', '')
        if peaks is None:
            return DEFAULT_SPEC_MATRIX
        bl = np.zeros_like(self.rsd_data)
        w = self.bl_window.value()
        for ch in range(4):
            bl[:, ch] = minimum_filter1d(self.rsd_data[:, ch], size=w, mode='reflect')
        corr = np.clip(self.rsd_data - bl, 0, None)
        bm = np.median(bl, axis=0)
        gn = corr / (bm[np.newaxis, :] + 1e-10) if self.gain_check.isChecked() and bm.min() > 0 else corr
        pd = {b: [] for b in 'ACGT'}
        for p, base in zip(peaks, seq):
            p = int(p)
            if base not in 'ACGT' or p < 5 or p >= len(gn) - 5:
                continue
            sig = gn[p]
            if sig.sum() > 0.01:
                pd[base].append(sig)
        mix = np.zeros((4, 4))
        for i, base in enumerate(['A', 'C', 'G', 'T']):
            arr = np.array(pd[base])
            if len(arr) < 10:
                continue
            med = np.median(arr, axis=0)
            nz = med / (med.sum() + 1e-10)
            mix[:, i] = nz
        if mix.sum() < 0.01:
            return DEFAULT_SPEC_MATRIX
        return mix

    def _update_plot(self):
        if self.rsd_data is None or self.esd_traces is None:
            return
        raw, corr, separated = self._process_rsd()
        n_show = [self.show_raw.isChecked(), self.show_corr.isChecked(),
                  self.show_sep.isChecked(), self.show_esd.isChecked()]
        n_plots = sum(n_show)
        if n_plots == 0:
            return

        self.fig.clear()
        self._axes = []
        ax_idx = 0

        def share_x(ax):
            if self._axes:
                ax.sharex(self._axes[0])
            self._axes.append(ax)

        if n_show[0]:
            ax_idx += 1
            ax = self.fig.add_subplot(n_plots, 1, ax_idx)
            share_x(ax)
            for ch in range(4):
                ax.plot(self._x_rsd, raw[:, ch], color=CHAN_COLORS[ch], linewidth=0.4, label=CHAN_LABELS_RSD[ch])
            ax.set_ylabel('Raw RSD', fontsize=8)
            ax.legend(fontsize=5, ncol=4, loc='upper right')
            ax.tick_params(labelbottom=False, labelsize=7)

        if n_show[1]:
            ax_idx += 1
            ax = self.fig.add_subplot(n_plots, 1, ax_idx, sharex=self._axes[0] if self._axes else None)
            share_x(ax)
            for ch in range(4):
                ax.plot(self._x_rsd, corr[:, ch], color=CHAN_COLORS[ch], linewidth=0.4)
            ax.set_ylabel('Corrected RSD', fontsize=8)
            ax.tick_params(labelbottom=False, labelsize=7)

        if n_show[2]:
            ax_idx += 1
            ax = self.fig.add_subplot(n_plots, 1, ax_idx, sharex=self._axes[0] if self._axes else None)
            share_x(ax)
            for ch in range(4):
                ax.plot(self._x_rsd, separated[:, ch], color=CHAN_COLORS[ch], linewidth=0.4, label=BASE_LETTERS[ch])
            ax.set_ylabel('RSD sep', fontsize=8)
            ax.legend(fontsize=5, ncol=4, loc='upper right')
            ax.tick_params(labelbottom=False, labelsize=7)

        if n_show[3]:
            ax_idx += 1
            ax = self.fig.add_subplot(n_plots, 1, ax_idx, sharex=self._axes[0] if self._axes else None)
            share_x(ax)
            for ch in range(4):
                ax.plot(self._x_esd, self.esd_traces[:, ch], color=CHAN_COLORS[ch], linewidth=0.4, label=BASE_LETTERS[ch])
            ax.set_ylabel('ESD traces', fontsize=8)
            ax.set_xlabel('Record index', fontsize=8)
            ax.legend(fontsize=5, ncol=4, loc='upper right')
            ax.tick_params(labelsize=7)

            if self.show_bases.isChecked() and self.esd_data:
                peaks = self.esd_data.get('peak_positions')
                seq = self.esd_data.get('sequence', '')
                if peaks is not None:
                    for p, base in zip(peaks, seq):
                        p = int(p)
                        if p >= len(self.esd_traces):
                            continue
                        trace = self.esd_traces[p]
                        dom_ch = np.argmax(trace)
                        dom_base = BASE_LETTERS[dom_ch]
                        color = 'black' if base == dom_base else 'red'
                        ax.axvline(x=p, color='gray', alpha=0.12, linewidth=0.3)
                        ax.text(p, 0.95, base, fontsize=5, ha='center', va='top',
                                color=color, clip_on=True,
                                bbox=dict(boxstyle='round,pad=0.05', facecolor='white',
                                          alpha=0.7, edgecolor=color))

        self.fig.subplots_adjust(hspace=0.05, left=0.05, right=0.98, top=0.97, bottom=0.06)
        self.canvas.draw()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self._reset_view()
        elif event.key() == Qt.Key_L:
            self._load_data()

    def _reset_view(self):
        if self._axes:
            for ax in self._axes:
                if self._x_rsd is not None:
                    ax.set_xlim(self._x_rsd[0], self._x_rsd[-1])
            self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TraceExplorer()
    window.show()
    sys.exit(app.exec_())
