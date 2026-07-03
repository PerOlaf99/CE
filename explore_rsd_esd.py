#!/usr/bin/env python3
"""Interactive RSD+ESD trace explorer.

Stacked view: RSD raw → RSD baseline-corrected → RSD separated → ESD traces
with adjustable preprocessing and ESD base labels.
"""
import sys, os, struct, json
import numpy as np
import pandas as pd
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import savgol_filter

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QCheckBox, QPushButton, QGroupBox,
    QGridLayout, QSlider, QFileDialog, QSplitter, QTextEdit,
    QDoubleSpinBox, QTabWidget
)
from PyQt5.QtCore import Qt

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd

BASE_DIR = os.path.join(os.path.dirname(__file__), 'MB1000_M13_DT')
ESD_SUBDIRS = {
    'Cp312': 'MB1000_M13_DT_Cp312_MD1',
}

CHAN_NAMES_RSD = ['Channel1', 'Channel2', 'Channel3', 'Channel4']
CHAN_LABELS_RSD = ['Ch0 (T)', 'Ch1 (G)', 'Ch2 (C)', 'Ch3 (A)']
CHAN_COLORS = ['red', 'green', 'blue', 'orange']
BASE_LETTERS = {0: 'T', 1: 'G', 2: 'C', 3: 'A'}

DEFAULT_SPEC_MATRIX = np.array([
    [0.85, 0.03, 0.05, 0.07],
    [0.02, 0.88, 0.04, 0.06],
    [0.06, 0.04, 0.86, 0.04],
    [0.07, 0.05, 0.05, 0.83],
], dtype=np.float64)
SEP_DEFAULT = np.linalg.inv(DEFAULT_SPEC_MATRIX)


class TraceExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('RSD + ESD Trace Explorer')
        self.setGeometry(100, 100, 1400, 900)
        self.rsd_data = None
        self.esd_data = None
        self.esd_traces = None
        self.current_well = None
        self._init_ui()
        self._populate_wells()

    def _init_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)

        # Top controls
        ctrl = QHBoxLayout()
        layout.addLayout(ctrl)

        ctrl.addWidget(QLabel('Well:'))
        self.well_combo = QComboBox()
        self.well_combo.setEditable(True)
        self.well_combo.currentTextChanged.connect(self._on_well_changed)
        ctrl.addWidget(self.well_combo)

        self.load_btn = QPushButton('Load')
        self.load_btn.clicked.connect(self._load_data)
        ctrl.addWidget(self.load_btn)

        ctrl.addWidget(QLabel('  ESD variant:'))
        self.esd_combo = QComboBox()
        for k in ESD_SUBDIRS:
            self.esd_combo.addItem(k)
        ctrl.addWidget(self.esd_combo)

        ctrl.addStretch()

        # Processing controls
        proc = QHBoxLayout()
        layout.addLayout(proc)

        bl_group = QGroupBox('Baseline')
        bl_grid = QGridLayout(bl_group)
        self.bl_check = QCheckBox('Enable')
        self.bl_check.setChecked(True)
        self.bl_check.stateChanged.connect(self._update_plot)
        bl_grid.addWidget(self.bl_check, 0, 0, 1, 2)
        bl_grid.addWidget(QLabel('Window:'), 1, 0)
        self.bl_window = QSpinBox()
        self.bl_window.setRange(10, 1000)
        self.bl_window.setValue(200)
        self.bl_window.setSingleStep(10)
        self.bl_window.valueChanged.connect(self._update_plot)
        bl_grid.addWidget(self.bl_window, 1, 1)
        proc.addWidget(bl_group)

        sm_group = QGroupBox('Smoothing')
        sm_grid = QGridLayout(sm_group)
        self.sm_check = QCheckBox('Enable')
        self.sm_check.setChecked(True)
        self.sm_check.stateChanged.connect(self._update_plot)
        sm_grid.addWidget(self.sm_check, 0, 0, 1, 2)
        sm_grid.addWidget(QLabel('Window:'), 1, 0)
        self.sm_window = QSpinBox()
        self.sm_window.setRange(3, 31)
        self.sm_window.setValue(7)
        self.sm_window.setSingleStep(2)
        self.sm_window.valueChanged.connect(self._update_plot)
        sm_grid.addWidget(self.sm_window, 1, 1)
        sm_grid.addWidget(QLabel('Order:'), 2, 0)
        self.sm_order = QSpinBox()
        self.sm_order.setRange(1, 5)
        self.sm_order.setValue(2)
        self.sm_order.valueChanged.connect(self._update_plot)
        sm_grid.addWidget(self.sm_order, 2, 1)
        proc.addWidget(sm_group)

        mx_group = QGroupBox('Matrix')
        mx_grid = QGridLayout(mx_group)
        self.mx_check = QCheckBox('Enable')
        self.mx_check.setChecked(True)
        self.mx_check.stateChanged.connect(self._update_plot)
        mx_grid.addWidget(self.mx_check, 0, 0, 1, 2)
        mx_grid.addWidget(QLabel('Preset:'), 1, 0)
        self.mx_combo = QComboBox()
        self.mx_combo.addItems(['Default (basecaller.py)', 'Identity', 'Derived from data'])
        self.mx_combo.currentIndexChanged.connect(self._update_plot)
        mx_grid.addWidget(self.mx_combo, 1, 1)
        mx_grid.addWidget(QLabel('Gain norm:'), 2, 0)
        self.gain_check = QCheckBox()
        self.gain_check.setChecked(True)
        self.gain_check.stateChanged.connect(self._update_plot)
        mx_grid.addWidget(self.gain_check, 2, 1)
        proc.addWidget(mx_group)

        disp_group = QGroupBox('Display')
        disp_grid = QGridLayout(disp_group)
        self.show_raw = QCheckBox('RSD raw')
        self.show_raw.setChecked(True)
        self.show_raw.stateChanged.connect(self._update_plot)
        disp_grid.addWidget(self.show_raw, 0, 0)
        self.show_corr = QCheckBox('RSD corrected')
        self.show_corr.setChecked(True)
        self.show_corr.stateChanged.connect(self._update_plot)
        disp_grid.addWidget(self.show_corr, 0, 1)
        self.show_sep = QCheckBox('RSD separated')
        self.show_sep.setChecked(True)
        self.show_sep.stateChanged.connect(self._update_plot)
        disp_grid.addWidget(self.show_sep, 1, 0)
        self.show_esd = QCheckBox('ESD traces')
        self.show_esd.setChecked(True)
        self.show_esd.stateChanged.connect(self._update_plot)
        disp_grid.addWidget(self.show_esd, 1, 1)
        self.show_bases = QCheckBox('Base labels')
        self.show_bases.setChecked(True)
        self.show_bases.stateChanged.connect(self._update_plot)
        disp_grid.addWidget(self.show_bases, 2, 0, 1, 2)
        proc.addWidget(disp_group)

        # Figure
        self.fig = Figure(figsize=(14, 8), dpi=100)
        self.fig.subplots_adjust(hspace=0.08, left=0.06, right=0.98, top=0.95, bottom=0.06)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

        # Status
        self.status = QTextEdit()
        self.status.setMaximumHeight(80)
        self.status.setReadOnly(True)
        layout.addWidget(self.status)

    def _populate_wells(self):
        wells = []
        if os.path.isdir(BASE_DIR):
            for f in sorted(os.listdir(BASE_DIR)):
                if f.endswith('.rsd'):
                    wells.append(f[:-4])
        self.well_combo.clear()
        self.well_combo.addItems(wells)
        if 'A01' in wells:
            self.well_combo.setCurrentText('A01')

    def _on_well_changed(self, text):
        pass

    def _load_data(self):
        well = self.well_combo.currentText().strip()
        if not well:
            return
        rsd_path = os.path.join(BASE_DIR, f'{well}.rsd')
        esd_key = self.esd_combo.currentText()
        esd_dir = ESD_SUBDIRS.get(esd_key, '')
        esd_path = os.path.join(BASE_DIR, esd_dir, f'{well}.esd')
        if not os.path.exists(rsd_path):
            self.status.setText(f'RSD not found: {rsd_path}')
            return
        if not os.path.exists(esd_path):
            self.status.setText(f'ESD not found: {esd_path}')
            return
        try:
            df = parse_rsd(rsd_path)
            self.rsd_data = df[CHAN_NAMES_RSD].values.astype(np.float64)
            esd = parse_esd(esd_path)
            self.esd_data = esd
            self._load_esd_traces(esd_path)
            self.current_well = well
            self.status.setText(f'Loaded {well}: RSD {len(self.rsd_data)} scans, '
                                f'ESD {len(self.esd_traces)} records, '
                                f'{len(esd.get(\"peak_positions\", []))} peaks')
            self._update_plot()
        except Exception as e:
            self.status.setText(f'Error: {e}')
            import traceback
            traceback.print_exc()

    def _load_esd_traces(self, path):
        with open(path, 'rb') as f:
            raw = f.read()
        data_end = 8754
        traces = np.zeros((data_end, 4), dtype=np.float64)
        for i in range(data_end):
            chs = struct.unpack('<ffff', raw[i*20+4:(i+1)*20])
            traces[i] = chs
        self.esd_traces = traces

    def _get_mixing_matrix(self):
        preset = self.mx_combo.currentText()
        if preset == 'Identity':
            return np.eye(4)
        elif preset == 'Default (basecaller.py)':
            return DEFAULT_SPEC_MATRIX
        elif preset == 'Derived from data':
            return self._derive_matrix()
        return DEFAULT_SPEC_MATRIX

    def _derive_matrix(self):
        if self.rsd_data is None or self.esd_data is None:
            return DEFAULT_SPEC_MATRIX
        peaks = self.esd_data.get('peak_positions')
        seq = self.esd_data.get('sequence', '')
        if peaks is None:
            return DEFAULT_SPEC_MATRIX
        # Compute gain-normalized baseline-corrected RSD at ESD peak positions
        bl = np.zeros_like(self.rsd_data)
        for ch in range(4):
            bl[:, ch] = minimum_filter1d(self.rsd_data[:, ch], size=self.bl_window.value(), mode='reflect')
        corr = np.clip(self.rsd_data - bl, 0, None)
        bl_med = np.median(bl, axis=0)
        if self.gain_check.isChecked() and bl_med.min() > 0:
            gn = corr / bl_med[np.newaxis, :]
        else:
            gn = corr
        peak_data = {b: [] for b in 'ACGT'}
        for p, base in zip(peaks, seq):
            p = int(p)
            if base not in 'ACGT' or p < 5 or p >= len(gn) - 5:
                continue
            sig = gn[p]
            if sig.sum() > 0.01:
                peak_data[base].append(sig)
        mix = np.zeros((4, 4))
        for i, base in enumerate(['A', 'C', 'G', 'T']):
            arr = np.array(peak_data[base])
            if len(arr) < 10:
                continue
            med = np.median(arr, axis=0)
            nz = med / (med.sum() + 1e-10)
            mix[:, i] = nz
        if mix.sum() < 0.01:
            return DEFAULT_SPEC_MATRIX
        return mix

    def _process_rsd(self):
        if self.rsd_data is None:
            return None, None, None
        raw = self.rsd_data.copy()
        # Baseline correction
        if self.bl_check.isChecked():
            bl = np.zeros_like(raw)
            for ch in range(4):
                bl[:, ch] = minimum_filter1d(raw[:, ch], size=self.bl_window.value(), mode='reflect')
            corr = np.clip(raw - bl, 0, None)
        else:
            corr = raw.copy()
        # Smoothing
        if self.sm_check.isChecked():
            w = self.sm_window.value()
            o = self.sm_order.value()
            if w > o + 1 and w % 2 == 1:
                for ch in range(4):
                    corr[:, ch] = savgol_filter(corr[:, ch], w, o)
        # Spectral separation
        if self.mx_check.isChecked():
            mix = self._get_mixing_matrix()
            bl_med = np.median(minimum_filter1d(self.rsd_data, size=self.bl_window.value(), mode='reflect'), axis=0)
            if self.gain_check.isChecked() and bl_med.min() > 0:
                gn = corr / bl_med[np.newaxis, :]
            else:
                gn = corr
            sep = np.linalg.inv(mix)
            separated = gn @ sep.T
        else:
            separated = corr.copy()
        return raw, corr, separated

    def _update_plot(self):
        if self.rsd_data is None or self.esd_traces is None:
            return
        raw, corr, separated = self._process_rsd()
        self.fig.clear()
        n_plots = sum([self.show_raw.isChecked(), self.show_corr.isChecked(),
                       self.show_sep.isChecked(), self.show_esd.isChecked()])
        if n_plots == 0:
            return
        ax_idx = 0
        x_rsd = np.arange(len(self.rsd_data))
        x_esd = np.arange(len(self.esd_traces))

        if self.show_raw.isChecked():
            ax_idx += 1
            ax = self.fig.add_subplot(n_plots, 1, ax_idx)
            for ch in range(4):
                ax.plot(x_rsd, raw[:, ch], color=CHAN_COLORS[ch], linewidth=0.4, label=CHAN_LABELS_RSD[ch])
            ax.set_ylabel('Raw RSD')
            ax.legend(fontsize=6, ncol=4, loc='upper right')
            ax.tick_params(labelbottom=False)
            ax.set_xlim(x_rsd[0], x_rsd[-1])

        if self.show_corr.isChecked():
            ax_idx += 1
            ax = self.fig.add_subplot(n_plots, 1, ax_idx)
            for ch in range(4):
                ax.plot(x_rsd, corr[:, ch], color=CHAN_COLORS[ch], linewidth=0.4)
            ax.set_ylabel('Corrected RSD')
            ax.tick_params(labelbottom=False)
            ax.set_xlim(x_rsd[0], x_rsd[-1])

        if self.show_sep.isChecked():
            ax_idx += 1
            ax = self.fig.add_subplot(n_plots, 1, ax_idx)
            for ch in range(4):
                ax.plot(x_rsd, separated[:, ch], color=CHAN_COLORS[ch], linewidth=0.4,
                        label=BASE_LETTERS[ch])
            ax.set_ylabel('RSD separated')
            ax.legend(fontsize=6, ncol=4, loc='upper right')
            ax.tick_params(labelbottom=False)
            ax.set_xlim(x_rsd[0], x_rsd[-1])

        if self.show_esd.isChecked():
            ax_idx += 1
            ax = self.fig.add_subplot(n_plots, 1, ax_idx)
            for ch in range(4):
                ax.plot(x_esd, self.esd_traces[:, ch], color=CHAN_COLORS[ch], linewidth=0.4,
                        label=BASE_LETTERS[ch])
            ax.set_ylabel('ESD traces')
            ax.set_xlabel('Record index')
            ax.legend(fontsize=6, ncol=4, loc='upper right')

            # Overlay ESD peak positions and base labels
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
                        if base == dom_base:
                            color = 'black'
                        else:
                            color = 'red'
                        ax.axvline(x=p, color='gray', alpha=0.15, linewidth=0.3)
                        y_top = 0.95
                        ax.text(p, y_top, base, fontsize=5, ha='center', va='top',
                                color=color,
                                bbox=dict(boxstyle='round,pad=0.05',
                                          facecolor='white', alpha=0.6, edgecolor=color))
            ax.set_xlim(x_esd[0], x_esd[-1])

        self.fig.subplots_adjust(hspace=0.08, left=0.06, right=0.98, top=0.97, bottom=0.06)
        self.canvas.draw()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_R:
            self._update_plot()
        elif event.key() == Qt.Key_L:
            self._load_data()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TraceExplorer()
    window.show()
    sys.exit(app.exec_())
