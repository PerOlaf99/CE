#!/usr/bin/env python3
"""view_esd.py - minimal ESD viewer + FASTA export.

Loads an .esd basecall (DLL ground truth) from the chosen ESD folder and
draws it on the 4-channel RSD trace (when an RSD is found). The base letters
are placed at their true peak scans, like the DLL produced them. Use the
matplotlib toolbar to zoom/pan; "Copy FASTA" / "Save FASTA..." give the ESD
sequence for BLAST comparison against your own basecalls.

Usage: python3 view_esd.py [data_dir]
"""
import json, os, sys
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QSpinBox, QFileDialog,
)
from PyQt5.QtGui import QFont

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_esd, parse_rsd

DEFAULT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ESD = os.path.join(DEFAULT_DIR, 'ground_truth', 'MB1000_M13_DT_Cp312_MD1')
BASE_OF_DYE = ("T", "G", "C", "A")
CHAN_COLORS = ['#d62728', '#2ca02c', '#1f77b4', '#ff7f0e']


class EsdViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESD basecall viewer")
        self.rsd_raw = None
        self.esd = None
        self.esd_path = None
        self.build_ui()
        self.is_gui_active = True

    # ------------------------------------------------------------------ UI
    def build_ui(self):
        central = QWidget()
        v = QVBoxLayout(central)

        top = QVBoxLayout()
        row_rsd = QHBoxLayout()
        row_rsd.addWidget(QLabel("Data folder (RSD):"))
        self.dir_label = QLabel(DEFAULT_DIR)
        row_rsd.addWidget(self.dir_label, 1)
        btn_dir = QPushButton("Browse...")
        btn_dir.clicked.connect(self._browse_dir)
        row_rsd.addWidget(btn_dir)
        top.addLayout(row_rsd)

        row_esd = QHBoxLayout()
        row_esd.addWidget(QLabel("ESD folder:"))
        self.esd_label = QLabel(DEFAULT_ESD)
        row_esd.addWidget(self.esd_label, 1)
        btn_esd = QPushButton("Browse...")
        btn_esd.clicked.connect(self._browse_esd)
        row_esd.addWidget(btn_esd)
        top.addLayout(row_esd)

        row_ctl = QHBoxLayout()
        row_ctl.addWidget(QLabel("Well:"))
        self.well_combo = QComboBox()
        self.well_combo.currentIndexChanged.connect(self._load_well)
        row_ctl.addWidget(self.well_combo)
        btn_go = QPushButton("Run")
        btn_go.clicked.connect(self._load_well)
        row_ctl.addWidget(btn_go)
        row_ctl.addStretch(1)
        top.addLayout(row_ctl)
        v.addLayout(top)

        navrow = QHBoxLayout()
        navrow.addWidget(QLabel("Bgn:"))
        self.bgn_spin = QSpinBox()
        self.bgn_spin.setRange(0, 20000)
        navrow.addWidget(self.bgn_spin)
        navrow.addWidget(QLabel("End:"))
        self.end_spin = QSpinBox()
        self.end_spin.setRange(0, 20000)
        navrow.addWidget(self.end_spin)
        btn_bgn = QPushButton("Jump bgn")
        btn_bgn.clicked.connect(lambda: self._zoom_to(self.bgn_spin.value()))
        navrow.addWidget(btn_bgn)
        btn_end = QPushButton("Jump end")
        btn_end.clicked.connect(lambda: self._zoom_to(self.end_spin.value()))
        navrow.addWidget(btn_end)
        btn_copy = QPushButton("Copy FASTA")
        btn_copy.clicked.connect(self._copy_fasta)
        navrow.addWidget(btn_copy)
        btn_save = QPushButton("Save FASTA...")
        btn_save.clicked.connect(self._save_fasta)
        navrow.addWidget(btn_save)
        self.note = QLabel('')
        navrow.addWidget(self.note, 1)
        v.addLayout(navrow)

        self.fig = Figure(figsize=(12, 6), constrained_layout=True)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        v.addWidget(self.toolbar)
        v.addWidget(self.canvas)
        self.setCentralWidget(central)
        self.resize(1200, 700)
        self._populate_wells()

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select data folder", DEFAULT_DIR)
        if d:
            self.dir_label.setText(d)
            self._populate_wells()

    def _browse_esd(self):
        d = QFileDialog.getExistingDirectory(self, "Select ESD folder",
                                             self.esd_label.text() or DEFAULT_DIR)
        if d:
            self.esd_label.setText(d)
            self._populate_wells()

    def _populate_wells(self):
        d = self.esd_label.text()
        wells = []
        if os.path.isdir(d):
            wells = sorted(f[:-4] for f in os.listdir(d)
                           if f.endswith('.esd'))
        self.well_combo.blockSignals(True)
        self.well_combo.clear()
        self.well_combo.addItems(wells)
        self.well_combo.blockSignals(False)
        if wells:
            self._load_well()

    # ------------------------------------------------------------ loading
    def _load_well(self):
        well = self.well_combo.currentText()
        if not well:
            return
        esd_path = os.path.join(self.esd_label.text(), well + '.esd')
        if not os.path.isfile(esd_path):
            self.note.setText(f'missing {esd_path}')
            return
        try:
            d = parse_esd(esd_path)
            self.esd = d
            self.esd_path = esd_path
        except Exception as e:
            self.note.setText(f'ESD error: {e}')
            return
        self.rsd_raw = None
        rsd_path = os.path.join(self.dir_label.text(), well + '.rsd')
        if not os.path.isfile(rsd_path):
            cand = os.path.join(self.dir_label.text(), os.path.basename(well))
            if os.path.isfile(cand):
                rsd_path = cand
        if os.path.isfile(rsd_path):
            try:
                df = parse_rsd(rsd_path)
                self.rsd_raw = np.asarray([df['Channel1'], df['Channel2'],
                                           df['Channel3'], df['Channel4']],
                                          dtype=float)
            except Exception as e:
                self.note.setText(f'RSD error: {e}')
        self._draw()

    # -------------------------------------------------------------- plot
    def _esd_rows(self):
        """Return list of (scan, base) from the ESD at its true peak scans,
        skipping trailing noise the way the DLL does."""
        if self.esd is None:
            return []
        pk = self.esd.get('peak_positions')
        if pk is None:
            pk = self.esd.get('bases_positions')
        seg = self.esd.get('sequence', '')
        if pk is None or len(pk) == 0:
            return []
        rows = [(int(pk[i]), b) for i, b in enumerate(seg)
                if i < len(pk) and b in 'TGCA']
        return rows

    def _fasta(self):
        if self.esd is None:
            return None
        seq = self.esd.get('sequence', '')
        name = f"{self.well_combo.currentText()} ESD (DLL)"
        wrapped = '\n'.join(seq[i:i + 80] for i in range(0, len(seq), 80))
        return f">esd_{name}\n{wrapped}\n"

    def _copy_fasta(self):
        fa = self._fasta()
        if fa is None:
            self.note.setText('no ESD loaded')
            return
        QApplication.clipboard().setText(fa)
        seq_len = sum(len(line) for line in fa.splitlines()[1:])
        self.note.setText(f'copied {seq_len}bp ESD FASTA to clipboard')

    def _save_fasta(self):
        fa = self._fasta()
        if fa is None:
            self.note.setText('no ESD loaded')
            return
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save FASTA', os.path.join(DEFAULT_DIR,
                                             self.well_combo.currentText() + '.esd.fasta'),
            'FASTA (*.fasta);;All files (*)')
        if path:
            with open(path, 'w') as f:
                f.write(fa)
            self.note.setText(f'saved {path}')

    def _draw(self):
        self.fig.clear()
        ax = self.fig.add_subplot(1, 1, 1)
        rows = self._esd_rows()
        if rows:
            self.bgn_spin.setValue(rows[0][0])
            self.end_spin.setValue(rows[-1][0])
        if self.rsd_raw is not None:
            raw = self.rsd_raw.T
            x = np.arange(len(raw))
            for ch_ in range(4):
                cmax = max(float(np.max(raw[:, ch_])), 1e-9)
                ax.plot(x, raw[:, ch_] / cmax, color=CHAN_COLORS[ch_],
                        linewidth=0.7, alpha=0.85,
                        label=f'{BASE_OF_DYE[ch_]} (raw Ch{ch_ + 1})')
            ax.legend(loc='upper right', fontsize=6, ncol=4)
            ax.set_xlim(x[0], x[-1])
            ax.set_ylim(0, 1.2)
        for scan, base in rows:
            if self.rsd_raw is not None and 0 <= scan < len(self.rsd_raw.T):
                ch = 'TGCA'.index(base)
                ax.text(scan, 1.06, base, ha='center', va='center', fontsize=6,
                        color='black', fontweight='bold',
                        bbox=dict(facecolor=CHAN_COLORS[ch], alpha=0.6,
                                  pad=0.2, edgecolor='none'))
            else:
                ax.text(scan, 1.06, base, ha='center', va='center', fontsize=6,
                        color='navy', fontweight='bold',
                        bbox=dict(facecolor='#dcdcff', alpha=0.6,
                                  pad=0.2, edgecolor='none'))
        ax.set_yticks([])
        nseq = len(self.esd.get('sequence', '')) if self.esd else 0
        meta = ''
        if self.esd and self.esd.get('sample_name'):
            meta = f"  {self.esd['sample_name'].strip()}"
        ax.set_title(f"ESD {self.well_combo.currentText()}: {len(rows)} peak-positioned bases"
                     f" / {nseq} letters{meta}")
        ax.set_xlabel('scan index')
        self.canvas.draw()

    def _zoom_to(self, scan):
        ax = self.fig.axes[0]
        x0, x1 = ax.get_xlim()
        half = (x1 - x0) / 2
        ax.set_xlim(scan - half, scan + half)
        self.canvas.draw()


def main():
    app = QApplication.instance() or QApplication([])
    win = EsdViewer()
    win.show()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())