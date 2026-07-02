import sys
import os
import csv
import struct
import glob

import numpy as np
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QFileDialog, QLabel, QSplitter,
    QToolButton, QTableWidget, QTableWidgetItem, QComboBox, QMessageBox,
    QShortcut, QSpinBox, QDoubleSpinBox, QCheckBox, QMenu, QInputDialog,
    QProgressDialog, QScrollArea, QDialog, QGroupBox, QDialogButtonBox,
    QPlainTextEdit, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence, QCursor, QFont
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbarBase
)
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

from peak_detector import PeakDetector, PEAK_CHANNEL_NAMES
from cnn_peak_detector import CnnPeakDetector
from basecaller import (
    basecall, basecall_ml, basecall_cimarron,
    export_bases_csv, export_bases_fasta, export_bases_summary,
    CHEMISTRY_MAP, esd_caller_display_name,
)


CLICK_TOLERANCE = 10
MAX_WELLS_PER_PAGE = 6
LEFT_PANEL_MIN_WIDTH = 520
IS_NONE_OPTION = "— None —"


class PeakNavigationToolbar(NavigationToolbarBase):
    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)
        self._app = parent

    def pan(self, *args):
        super().pan(*args)
        btn = getattr(self._app, '_select_peaks_btn', None)
        if btn:
            btn.setChecked(False)

    def zoom(self, *args):
        super().zoom(*args)
        btn = getattr(self._app, '_select_peaks_btn', None)
        if btn:
            btn.setChecked(False)


class UndoManager:
    def __init__(self):
        self._undo_stack = []
        self._redo_stack = []

    def push(self, action):
        self._undo_stack.append(action)
        self._redo_stack.clear()

    def undo(self):
        if not self._undo_stack:
            return None
        action = self._undo_stack.pop()
        self._redo_stack.append(action)
        return action

    def redo(self):
        if not self._redo_stack:
            return None
        action = self._redo_stack.pop()
        self._undo_stack.append(action)
        return action

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()


DEFAULT_SPECTRAL_MATRIX = np.array([
    [0.90, 0.01, 0.04, 0.05],   # Ch1 response from ROX, FAM, NED, HEX
    [0.01, 0.92, 0.02, 0.05],   # Ch2
    [0.05, 0.02, 0.90, 0.03],   # Ch3
    [0.04, 0.05, 0.04, 0.87],   # Ch4
], dtype=np.float64)

MATRIX_LABELS = ["ET-ROX", "FAM", "NED", "HEX"]
CHANNEL_LABELS = ["Ch1", "Ch2", "Ch3", "Ch4"]


class MatrixEditorDialog(QDialog):
    def __init__(self, matrix, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Spectral Separation Matrix")
        self.setModal(True)
        self.spins = [[None] * 4 for _ in range(4)]

        layout = QVBoxLayout(self)

        instr = QLabel(
            "Columns are dye emission profiles (how each dye appears in each channel).\n"
            "Rows are raw channels.  M[i,j] = response of channel i to dye j.\n"
            "The inverse matrix is used to unmix: clean = inv(M) @ raw."
        )
        instr.setWordWrap(True)
        layout.addWidget(instr)

        grid = QGridLayout()
        grid.addWidget(QLabel(""), 0, 0)
        for j, dye in enumerate(MATRIX_LABELS):
            lbl = QLabel(dye)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-weight: bold; font-size: 10px;")
            grid.addWidget(lbl, 0, j + 1)
        for i, ch in enumerate(CHANNEL_LABELS):
            lbl = QLabel(ch)
            lbl.setStyleSheet("font-weight: bold; font-size: 10px;")
            grid.addWidget(lbl, i + 1, 0)
            for j in range(4):
                sp = QDoubleSpinBox()
                sp.setRange(0.0, 1.0)
                sp.setSingleStep(0.01)
                sp.setDecimals(3)
                sp.setValue(matrix[i, j])
                grid.addWidget(sp, i + 1, j + 1)
                self.spins[i][j] = sp

        layout.addLayout(grid)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
        self.resize(520, 260)

    def get_matrix(self):
        m = np.zeros((4, 4), dtype=np.float64)
        for i in range(4):
            for j in range(4):
                m[i, j] = self.spins[i][j].value()
        return m


class SequenceDialog(QDialog):
    def __init__(self, well_results, parent=None):
        super().__init__(parent)
        self.well_results = well_results
        self.setWindowTitle("Base Calling Results")
        self.resize(800, 600)
        layout = QVBoxLayout(self)

        # Summary bar
        total_bases = sum(r['total_calls'] for r in well_results.values())
        total_n = sum(r['n_count'] for r in well_results.values())
        avg_q = int(np.mean([r['avg_quality'] for r in well_results.values()]))
        summary = QLabel(
            f"Wells: {len(well_results)}  |  "
            f"Total bases: {total_bases}  |  "
            f"N's: {total_n} ({total_n/max(total_bases,1)*100:.1f}%)  |  "
            f"Avg quality: {avg_q}"
        )
        summary.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(summary)

        # Auto-threshold info if ML
        first = next(iter(well_results.values()))
        if first.get('auto_threshold'):
            thresh = first['auto_threshold']
            info = QLabel(f"ML auto-threshold: p ≥ {thresh:.2f}  "
                          f"(target 98% accuracy)")
            info.setStyleSheet("color: #666; font-size: 11px; padding: 2px 4px;")
            layout.addWidget(info)

        tab_widget = QTabWidget()
        for well, result in well_results.items():
            text = "\n".join(result["sequence_lines"])
            seq = result["sequence"]
            chem = result["chemistry"]
            avg_q = result["avg_quality"]
            n_cnt = result["n_count"]
            total = result["total_calls"]

            header = (
                f"Well: {well}  |  Chemistry: {chem}  |  "
                f"Avg Qual: {avg_q}  |  N's: {n_cnt}/{total}\n"
                f"{'=' * 78}\n"
            )
            content = header + text

            text_edit = QPlainTextEdit()
            text_edit.setPlainText(content)
            text_edit.setFont(QFont("Courier", 10))
            text_edit.setReadOnly(True)
            tab_widget.addTab(text_edit, well)

        layout.addWidget(tab_widget)

        btn_row = QHBoxLayout()
        btn_fasta = QPushButton("Save FASTA")
        btn_fasta.clicked.connect(lambda: self._save_fasta())
        btn_row.addWidget(btn_fasta)
        btn_csv = QPushButton("Save CSV")
        btn_csv.clicked.connect(lambda: self._save_csv())
        btn_row.addWidget(btn_csv)
        btn_summary = QPushButton("Save Summary")
        btn_summary.clicked.connect(lambda: self._save_summary())
        btn_row.addWidget(btn_summary)
        btn_row.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _save_fasta(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save FASTA", "", "FASTA (*.seq *.fasta);;All Files (*)"
        )
        if path:
            export_bases_fasta(self.well_results, path)

    def _save_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV", "", "CSV (*.csv);;All Files (*)"
        )
        if path:
            export_bases_csv(self.well_results, path)

    def _save_summary(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Summary", "", "CSV (*.csv);;All Files (*)"
        )
        if path:
            export_bases_summary(self.well_results, path)


class ElectropherogramApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Electropherogram Analyzer")
        self.resize(1400, 850)

        self.all_data = {}
        self.well_list = [f"{r}{c:02d}" for r in "ABCDEFGH" for c in range(1, 13)]
        self.selected_wells = set()

        self.detector = PeakDetector()
        self._well_data = {}
        self._dirty_wells = set()
        self._deleted_peaks = {}
        self._manual_peaks = {}
        self._peak_marker_lines = []
        self._page_start = 0
        self._current_page_wells = []
        self._active_well = None
        self.auto_scale_x = True
        self.auto_scale_y = True
        self._saved_xlim = None
        self._saved_ylims = []
        self._saved_ylims2 = []
        self._esd_data = {}  # well -> {caller_name: esd_dict}
        self._esd_callers = []  # list of (caller_name, subdir_path)
        self._esd_caller_combo = None
        self._undo_manager = UndoManager()
        self._spectral_matrix = DEFAULT_SPECTRAL_MATRIX.copy()
        self._is_ref_scans = []
        self._is_ref_tolerance = 30

        self.training_data = []
        self._figure_labels = []
        self._current_folder = None
        self._file_header = {}
        self._original_all_data = None
        self._is_channel = None
        self._is_peak_num = None
        self._prev_is_peak_num = None

        self.channel_colors = {
            'Channel1': {'active': '#0072B2', 'inactive': '#cce5f2'},
            'Channel2': {'active': '#E69F00', 'inactive': '#fae5cc'},
            'Channel3': {'active': '#CC79A7', 'inactive': '#f0dae5'},
            'Channel4': {'active': '#009E73', 'inactive': '#cce5de'},
            'Current': {'active': '#555555', 'inactive': '#e0e0e0'},
        }

        self._config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gui_settings.json')
        self._load_settings()

        # Restore window geometry
        s = self._settings
        self.resize(s.get('window_w', 1400), s.get('window_h', 850))
        self.move(s.get('window_x', 100), s.get('window_y', 100))

        self.init_ui()
        self._apply_settings()

    def closeEvent(self, event):
        self._save_settings()
        if self._current_folder:
            self._save_peak_data(self._current_folder)
        super().closeEvent(event)

    def _load_settings(self):
        import json
        defaults = {
            'height': 100, 'prominence': 50, 'distance': 5, 'min_width': 1,
            'stutter': False, 'stutter_window': 5,
            'baseline': 0, 'baseline_param': 500,
            'scan_limit': False, 'scan_start': 0, 'scan_end': 50000,
            'is_n': 4,
            'detection': 0,
            'channels': {'Channel2': True},
            'window_x': 100, 'window_y': 100, 'window_w': 1400, 'window_h': 850,
        }
        try:
            with open(self._config_path) as f:
                loaded = json.load(f)
            for k, v in defaults.items():
                if k not in loaded:
                    loaded[k] = v
            self._settings = loaded
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            self._settings = defaults

    def _save_settings(self):
        import json
        s = self._settings
        s['height'] = self.height_spin.value()
        s['prominence'] = self.prominence_spin.value()
        s['distance'] = self.distance_spin.value()
        s['min_width'] = self.min_width_spin.value()
        s['stutter'] = self.stutter_cb.isChecked()
        s['stutter_window'] = self.stutter_spin.value()
        s['baseline'] = self.baseline_combo.currentIndex()
        s['baseline_param'] = self.bl_spin.value()
        s['scan_limit'] = self.range_cb.isChecked()
        s['scan_start'] = self.start_spin.value()
        s['scan_end'] = self.end_spin.value()
        s['is_n'] = self.is_n_spin.value()
        s['detection'] = self.detection_combo.currentIndex()
        s['channels'] = {ch: btn.isChecked() for ch, btn in self.channel_buttons.items()}
        geo = self.geometry()
        s['window_x'] = geo.x()
        s['window_y'] = geo.y()
        s['window_w'] = geo.width()
        s['window_h'] = geo.height()
        try:
            with open(self._config_path, 'w') as f:
                json.dump(s, f, indent=2)
        except (OSError, PermissionError):
            pass

    def _peak_data_path(self, folder):
        base = os.path.basename(folder)
        return os.path.join(os.path.dirname(folder), f'.peak_data_{base}.json')

    def _save_peak_data(self, folder):
        import json
        data = {
            'manual_peaks': {w: [[int(s), ch] for s, ch in peaks]
                             for w, peaks in self._manual_peaks.items()},
            'deleted_peaks': {w: [int(x) for x in del_set]
                              for w, del_set in self._deleted_peaks.items()},
        }
        for w in self._well_data:
            if w not in data:
                data[w] = {}
            if 'peaks' in self._well_data[w]:
                p = self._well_data[w]['peaks']
                data[w]['peaks'] = [int(x) for x in p] if p is not None else None
            if 'peak_channels' in self._well_data[w]:
                data[w]['peak_channels'] = list(self._well_data[w]['peak_channels'])
        try:
            with open(self._peak_data_path(folder), 'w') as f:
                json.dump(data, f, indent=2)
        except (OSError, PermissionError):
            pass

    def _load_peak_data(self, folder):
        import json
        path = self._peak_data_path(folder)
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, FileNotFoundError, json.JSONDecodeError):
            return
        self._manual_peaks = {}
        for w, lst in data.get('manual_peaks', {}).items():
            parsed = []
            for s, ch in lst:
                try:
                    parsed.append((int(s), int(ch)))
                except (ValueError, TypeError):
                    parsed.append((int(s), str(ch)))
            self._manual_peaks[w] = parsed
        self._deleted_peaks = {}
        for w, lst in data.get('deleted_peaks', {}).items():
            self._deleted_peaks[w] = set(int(x) for x in lst)
        for w in self._well_data:
            if w not in data:
                continue
            if 'peaks' in data[w] and data[w]['peaks'] is not None:
                self._well_data[w]['peaks'] = np.array(data[w]['peaks'], dtype=np.float64)
            if 'peak_channels' in data[w]:
                self._well_data[w]['peak_channels'] = list(data[w]['peak_channels'])
        self.status_label.setText(f"Restored saved peak data ({len(self._manual_peaks)} wells with edits)")

    def _apply_settings(self):
        s = self._settings
        self.height_spin.setValue(s.get('height', 100))
        self.prominence_spin.setValue(s.get('prominence', 50))
        self.distance_spin.setValue(s.get('distance', 5))
        self.min_width_spin.setValue(s.get('min_width', 1))
        self.stutter_cb.setChecked(s.get('stutter', False))
        self.stutter_spin.setValue(s.get('stutter_window', 5))
        self.baseline_combo.setCurrentIndex(s.get('baseline', 0))
        self.bl_spin.setValue(s.get('baseline_param', 500))
        self.is_n_spin.setValue(s.get('is_n', 4))
        self.detection_combo.setCurrentIndex(s.get('detection', 0))

        scan_limit = s.get('scan_limit', False)
        self.range_cb.setChecked(scan_limit)
        self.start_spin.setValue(s.get('scan_start', 0))
        self.start_spin.setEnabled(scan_limit)
        self.end_spin.setValue(s.get('scan_end', 50000))
        self.end_spin.setEnabled(scan_limit)

        ch_settings = s.get('channels', {'Channel2': True})
        for ch, checked in ch_settings.items():
            if ch in self.channel_buttons:
                self.channel_buttons[ch].setChecked(checked)
                self._update_channel_style(ch)

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def init_ui(self):
        splitter = QSplitter(Qt.Horizontal)

        left = self._build_left_panel()
        center = self._build_center_panel()

        splitter.addWidget(left)
        splitter.addWidget(center)
        splitter.setSizes([LEFT_PANEL_MIN_WIDTH, 840])

        self.setCentralWidget(splitter)
        self._apply_style()

    def _build_left_panel(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumWidth(LEFT_PANEL_MIN_WIDTH)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)

        load_btn = QPushButton("Load Folder")
        load_btn.setToolTip("Load a folder containing .rsd or .txt electropherogram files")
        load_btn.clicked.connect(self.load_folder)
        layout.addWidget(load_btn)

        # Action row
        action_row = QHBoxLayout()
        clear_btn = QPushButton("Clear Data")
        clear_btn.setToolTip("Clear all loaded data and reset the application")
        clear_btn.clicked.connect(self.clear_data)
        action_row.addWidget(clear_btn)
        save_all_btn = QPushButton("Save All")
        save_all_btn.setToolTip("Save peak data from all loaded wells to a CSV file")
        save_all_btn.clicked.connect(self.save_all_data)
        action_row.addWidget(save_all_btn)
        select_btn = QPushButton("Select Peaks")
        select_btn.setToolTip(
            "Toggle peak selection on/off. When active, clicks add/remove "
            "peaks instead of zooming/panning."
        )
        select_btn.setCheckable(True)
        select_btn.clicked.connect(self._activate_peak_select)
        action_row.addWidget(select_btn)
        self._select_peaks_btn = select_btn
        layout.addLayout(action_row)

        # Navigation row
        nav = QHBoxLayout()
        prev_btn = QPushButton("\u2190 Prev")
        prev_btn.setToolTip("Navigate to the previous loaded well")
        next_btn = QPushButton("Next \u2192")
        next_btn.setToolTip("Navigate to the next loaded well")
        prev_btn.clicked.connect(self.prev_well)
        next_btn.clicked.connect(self.next_well)
        nav.addWidget(prev_btn)
        nav.addWidget(next_btn)
        layout.addLayout(nav)

        # Well grid
        grid = QGridLayout()
        grid.setSpacing(1)
        self.well_buttons = {}
        corner = QLabel("Well")
        corner.setAlignment(Qt.AlignCenter)
        corner.setFixedSize(28, 14)
        corner.setStyleSheet("font-size: 8px; color: #888;")
        grid.addWidget(corner, 0, 0)

        for c in range(12):
            lbl = QLabel(f"{c+1:02d}")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedSize(38, 14)
            lbl.setStyleSheet("font-size: 9px; color: #888;")
            lbl.setToolTip(f"Column {c+1}")
            grid.addWidget(lbl, 0, c + 1)

        for r in range(8):
            lbl = QLabel(f"  {chr(65+r)}")
            lbl.setFixedSize(28, 28)
            lbl.setStyleSheet("font-size: 10px; color: #888;")
            lbl.setToolTip(f"Row {chr(65+r)}")
            grid.addWidget(lbl, r + 1, 0)

        for i, well in enumerate(self.well_list):
            btn = QPushButton(well)
            btn.setToolTip(f"Load well {well}")
            btn.setFixedSize(38, 28)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 10px; padding: 0px;
                    border: 1px solid #d2d2d7; border-radius: 3px;
                    background-color: #ffffff;
                }
                QPushButton:hover { background-color: #e8e8ed; }
            """)
            btn.clicked.connect(lambda checked, w=well: self._on_well_clicked(w))
            grid.addWidget(btn, (i // 12) + 1, (i % 12) + 1)
            self.well_buttons[well] = btn
            btn.setContextMenuPolicy(Qt.CustomContextMenu)
            btn.customContextMenuRequested.connect(
                lambda pos, w=well: self._toggle_well_selection(w)
            )

        layout.addLayout(grid)

        hint = QLabel("Click=load  Ctrl+click=select")
        hint.setStyleSheet("font-size: 9px; color: #999;")
        layout.addWidget(hint)

        # Row selection buttons
        row_sel = QHBoxLayout()
        row_sel.setSpacing(3)
        row_sel.addWidget(QLabel("Row:"))
        sel_all = QPushButton("All")
        sel_all.setFixedSize(30, 22)
        sel_all.setToolTip("Select all wells")
        sel_all.clicked.connect(lambda: self._select_wells(set(self.well_list)))
        row_sel.addWidget(sel_all)
        sel_clr = QPushButton("Clr")
        sel_clr.setFixedSize(30, 22)
        sel_clr.setToolTip("Clear selection")
        sel_clr.clicked.connect(lambda: self._select_wells(set()))
        row_sel.addWidget(sel_clr)
        for row_label in "ABCDEFGH":
            rb = QPushButton(row_label)
            rb.setFixedSize(30, 22)
            rb.setToolTip(f"Select all wells in row {row_label}")
            wells_in_row = [f"{row_label}{c:02d}" for c in range(1, 13)]
            rb.clicked.connect(
                lambda checked, r=row_label, wl=wells_in_row: self._select_wells(set(wl))
            )
            row_sel.addWidget(rb)
        layout.addLayout(row_sel)

        # Export / ML row
        ml_layout = QHBoxLayout()
        train_cnn_btn = QPushButton("Train CNN")
        train_cnn_btn.setToolTip("Retrain the ML base caller CNN model using extracted training data")
        train_cnn_btn.clicked.connect(self._train_cnn_model)
        ml_layout.addWidget(train_cnn_btn)
        export_sel_btn = QPushButton("Export Selected")
        export_sel_btn.setToolTip("Export peaks and areas for selected wells as CSV")
        export_sel_btn.clicked.connect(self.export_selected_wells)
        ml_layout.addWidget(export_sel_btn)
        export_btn = QPushButton("Export ML Data")
        export_btn.setToolTip("Export labeled peak data as CSV for ML training")
        export_btn.clicked.connect(self.export_training_data)
        ml_layout.addWidget(export_btn)
        pred_btn = QPushButton("Predict Genotypes")
        pred_btn.setToolTip("Predict genotyping calls (0/1/2/4) using trained ML model")
        pred_btn.clicked.connect(self.predict_genotypes)
        ml_layout.addWidget(pred_btn)
        layout.addLayout(ml_layout)

        # Stutter controls
        stutter_layout = QHBoxLayout()
        self.stutter_cb = QCheckBox("Group Stutter")
        self.stutter_cb.setToolTip("Group nearby peaks into stutter groups, keeping only the tallest")
        self.stutter_cb.stateChanged.connect(self._mark_dirty_and_update)
        stutter_layout.addWidget(self.stutter_cb)
        stutter_layout.addWidget(QLabel("Window:"))
        self.stutter_spin = QSpinBox()
        self.stutter_spin.setToolTip("Maximum scan distance between peaks in a stutter group")
        self.stutter_spin.setRange(1, 50)
        self.stutter_spin.setValue(5)
        self.stutter_spin.valueChanged.connect(self._mark_dirty_and_update)
        stutter_layout.addWidget(self.stutter_spin)
        layout.addLayout(stutter_layout)

        # Peak detection params
        params_layout = QHBoxLayout()
        params_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setToolTip("Minimum peak height. Peaks below this value are ignored.")
        self.height_spin.setRange(0, 10000)
        self.height_spin.setValue(100)
        self.height_spin.valueChanged.connect(self._mark_dirty_and_update)
        params_layout.addWidget(self.height_spin)

        params_layout.addWidget(QLabel("Prominence:"))
        self.prominence_spin = QSpinBox()
        self.prominence_spin.setToolTip("Minimum prominence (vertical distance to baseline)")
        self.prominence_spin.setRange(0, 10000)
        self.prominence_spin.setValue(50)
        self.prominence_spin.valueChanged.connect(self._mark_dirty_and_update)
        params_layout.addWidget(self.prominence_spin)

        params_layout.addWidget(QLabel("Distance:"))
        self.distance_spin = QSpinBox()
        self.distance_spin.setToolTip("Minimum horizontal distance between detected peaks (scan points)")
        self.distance_spin.setRange(1, 1000)
        self.distance_spin.setValue(5)
        self.distance_spin.valueChanged.connect(self._mark_dirty_and_update)
        params_layout.addWidget(self.distance_spin)

        params_layout.addWidget(QLabel("Min Width:"))
        self.min_width_spin = QSpinBox()
        self.min_width_spin.setToolTip("Minimum peak width in scan points")
        self.min_width_spin.setRange(0, 100)
        self.min_width_spin.setValue(1)
        self.min_width_spin.valueChanged.connect(self._mark_dirty_and_update)
        params_layout.addWidget(self.min_width_spin)
        clear_peaks_btn = QPushButton("Clear Peaks")
        clear_peaks_btn.setToolTip("Remove all detected peaks in current well")
        clear_peaks_btn.clicked.connect(self._clear_all_peaks)
        params_layout.addWidget(clear_peaks_btn)
        layout.addLayout(params_layout)

        # IS reference row
        is_ref_layout = QHBoxLayout()
        self.save_is_btn = QPushButton("Save IS Ref.")
        self.save_is_btn.setToolTip("Save manually-added peaks in Ch3 as IS reference positions")
        self.save_is_btn.clicked.connect(self._save_is_reference)
        is_ref_layout.addWidget(self.save_is_btn)
        self.find_is_btn = QPushButton("Find IS Peaks")
        self.find_is_btn.setToolTip("Find IS peaks in all wells using saved reference")
        self.find_is_btn.clicked.connect(self._find_is_peaks)
        is_ref_layout.addWidget(self.find_is_btn)
        is_ref_layout.addWidget(QLabel("N:"))
        self.is_n_spin = QSpinBox()
        self.is_n_spin.setToolTip("Number of IS peaks to find per well")
        self.is_n_spin.setRange(1, 20)
        self.is_n_spin.setValue(4)
        is_ref_layout.addWidget(self.is_n_spin)
        self.save_is_model_btn = QPushButton("Save Model")
        self.save_is_model_btn.setToolTip("Save trained IS model to file")
        self.save_is_model_btn.clicked.connect(self._save_is_model)
        is_ref_layout.addWidget(self.save_is_model_btn)
        self.batch_is_btn = QPushButton("Batch IS")
        self.batch_is_btn.setToolTip("Run IS detection on all matching fragment folders in OY/")
        self.batch_is_btn.clicked.connect(self._batch_is_detect)
        is_ref_layout.addWidget(self.batch_is_btn)
        self.load_is_btn = QPushButton("Load IS CSV")
        self.load_is_btn.setToolTip("Load saved IS peaks CSV and display on plot")
        self.load_is_btn.clicked.connect(self._load_is_peaks)
        is_ref_layout.addWidget(self.load_is_btn)
        self.export_is_btn = QPushButton("Export IS CSV")
        self.export_is_btn.setToolTip("Export all wells' IS peaks to CSV for ML training")
        self.export_is_btn.clicked.connect(self._export_is_peaks_csv)
        is_ref_layout.addWidget(self.export_is_btn)
        self.is_ref_label = QLabel("ref: none")
        self.is_ref_label.setStyleSheet("color: #888; font-size: 10px;")
        is_ref_layout.addWidget(self.is_ref_label)
        layout.addLayout(is_ref_layout)

        # Training buttons row
        train_layout = QHBoxLayout()
        self.train_geno_btn = QPushButton("Train Genotyping")
        self.train_geno_btn.setToolTip("Train genotyping model using Genotyping.xlsx ground truth")
        self.train_geno_btn.clicked.connect(self._train_genotyping)
        train_layout.addWidget(self.train_geno_btn)
        self.train_is_btn = QPushButton("Train IS")
        self.train_is_btn.setToolTip("Train using IS peaks CSV (corrected peaks, no Genotyping.xlsx needed)")
        self.train_is_btn.clicked.connect(self._train_is_only)
        train_layout.addWidget(self.train_is_btn)
        layout.addLayout(train_layout)

        # Baseline controls
        bl_layout = QHBoxLayout()
        bl_layout.addWidget(QLabel("Baseline:"))
        self.baseline_combo = QComboBox()
        self.baseline_combo.setToolTip(
            "Baseline correction method.\n"
            "None: raw signal.\n"
            "First 200: constant baseline = median of first 200 scans.\n"
            "Rolling Min: rolling window minimum.\n"
            "ALS: Asymmetric Least Squares (lambda = 10^x)."
        )
        self.baseline_combo.addItems(["None", "First 200", "Rolling Min", "ALS"])
        self.baseline_combo.currentIndexChanged.connect(self.on_baseline_changed)
        bl_layout.addWidget(self.baseline_combo)
        self.bl_label = QLabel("Window:")
        bl_layout.addWidget(self.bl_label)
        self.bl_spin = QSpinBox()
        self.bl_spin.setToolTip(
            "Rolling Min: window size in scan points.\n"
            "ALS: log10 of lambda (smoothness parameter, higher = smoother)."
        )
        self.bl_spin.setRange(10, 5000)
        self.bl_spin.setValue(500)
        self.bl_spin.valueChanged.connect(self._mark_dirty_and_update)
        bl_layout.addWidget(self.bl_spin)
        layout.addLayout(bl_layout)

        # Range limit
        range_layout = QHBoxLayout()
        self.range_cb = QCheckBox("Limit Scan Range")
        self.range_cb.setToolTip("Restrict peak detection to a specific scan range")
        self.range_cb.stateChanged.connect(self._on_range_toggle)
        self.range_cb.stateChanged.connect(self._mark_dirty_and_update)
        range_layout.addWidget(self.range_cb)
        range_layout.addWidget(QLabel("Start:"))
        self.start_spin = QSpinBox()
        self.start_spin.setToolTip("Start scan number for range-limited detection")
        self.start_spin.setRange(0, 500000)
        self.start_spin.setValue(0)
        self.start_spin.setEnabled(False)
        self.start_spin.valueChanged.connect(self._mark_dirty_and_update)
        range_layout.addWidget(self.start_spin)
        range_layout.addWidget(QLabel("End:"))
        self.end_spin = QSpinBox()
        self.end_spin.setToolTip("End scan number for range-limited detection")
        self.end_spin.setRange(0, 500000)
        self.end_spin.setValue(50000)
        self.end_spin.setEnabled(False)
        self.end_spin.valueChanged.connect(self._mark_dirty_and_update)
        range_layout.addWidget(self.end_spin)
        layout.addLayout(range_layout)

        self.status_label = QLabel("No data loaded")
        layout.addWidget(self.status_label)
        self.folder_label = QLabel("")
        self.folder_label.setStyleSheet("font-size: 10px; color: #888;")
        layout.addWidget(self.folder_label)

        # File header info
        self.header_group = QGroupBox("File Header")
        self.header_group.setVisible(False)
        header_layout = QVBoxLayout(self.header_group)
        self.header_table = QTableWidget()
        self.header_table.setColumnCount(2)
        self.header_table.setHorizontalHeaderLabels(['Field', 'Value'])
        self.header_table.horizontalHeader().setStretchLastSection(True)
        self.header_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.header_table.setSelectionMode(QTableWidget.NoSelection)
        self.header_table.setMaximumHeight(200)
        self.header_table.verticalHeader().setVisible(False)
        header_layout.addWidget(self.header_table)
        layout.addWidget(self.header_group)

        # Detection method
        det_layout = QHBoxLayout()
        det_layout.addWidget(QLabel("Detection:"))
        self.detection_combo = QComboBox()
        self.detection_combo.addItems(["Classic", "Deep Learning"])
        self.detection_combo.currentIndexChanged.connect(self._on_detection_changed)
        det_layout.addWidget(self.detection_combo)
        layout.addLayout(det_layout)

        # Internal Standard
        is_layout = QVBoxLayout()
        is_row = QHBoxLayout()
        is_row.addWidget(QLabel("IS Channel:"))
        self.is_channel_combo = QComboBox()
        self.is_channel_combo.currentIndexChanged.connect(self._on_is_channel_changed)
        is_row.addWidget(self.is_channel_combo)
        is_row.addWidget(QLabel("IS Peak #:"))
        self.is_peak_combo = QComboBox()
        self.is_peak_combo.currentIndexChanged.connect(self._on_is_peak_changed)
        is_row.addWidget(self.is_peak_combo)
        is_layout.addLayout(is_row)
        self.summary_label = QLabel("IS Area: -    Sample Area: -    Area/IS: -")
        is_layout.addWidget(self.summary_label)
        layout.addLayout(is_layout)

        # SNR
        snr_layout = QHBoxLayout()
        self.snr_label = QLabel("Noise: -    Best SNR: -")
        snr_layout.addWidget(self.snr_label)
        layout.addLayout(snr_layout)

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _build_center_panel(self):
        center = QWidget()
        center_layout = QVBoxLayout(center)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = PeakNavigationToolbar(self.canvas, self)
        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.setFocusPolicy(Qt.ClickFocus)
        self.canvas.setFocus()

        QShortcut(QKeySequence(Qt.Key_Delete), self, self._delete_selected_or_nearest_peak)
        QShortcut(QKeySequence(Qt.Key_Backspace), self, self._delete_selected_or_nearest_peak)
        QShortcut(QKeySequence('Ctrl+Z'), self, self._undo)
        QShortcut(QKeySequence('Ctrl+Shift+Z'), self, self._redo)

        center_layout.addWidget(self.toolbar)

        # Channel buttons in the toolbar
        self.channel_buttons = {}
        channel_names = [
            ('Channel1', 'Ch1'),
            ('Channel2', 'Ch2'),
            ('Channel3', 'Ch3'),
            ('Channel4', 'Ch4'),
            ('Current', '\u00b5A'),
        ]
        self.toolbar.addSeparator()
        for ch_key, label in channel_names:
            btn = QPushButton(label)
            btn.setToolTip(f"Toggle display of {ch_key}")
            btn.setCheckable(True)
            btn.setChecked(False)
            btn.setFixedSize(36, 36)
            btn.setStyleSheet("""
                QPushButton {
                    border-radius: 18px;
                    font-size: 10px; font-weight: bold;
                    padding: 0px;
                }
                QPushButton:checked {
                    border: 2px solid #333;
                }
            """)
            btn.clicked.connect(self.toggle_channel)
            self.channel_buttons[ch_key] = btn
            self._update_channel_style(ch_key)
            self.toolbar.addWidget(btn)
        self.channel_buttons['Channel2'].setChecked(True)
        self._update_channel_style('Channel2')

        self.toolbar.addSeparator()
        self.norm_btn = QPushButton("Norm")
        self.norm_btn.setToolTip("Scale scan axis by current ratio")
        self.norm_btn.setCheckable(True)
        self.norm_btn.setChecked(False)
        self.norm_btn.setFixedSize(44, 36)
        self.norm_btn.setStyleSheet("""
            QPushButton {
                border-radius: 6px; font-size: 10px; font-weight: bold;
                padding: 0px 4px;
            }
            QPushButton:checked { border: 2px solid #0071e3; color: #0071e3; }
        """)
        self.norm_btn.clicked.connect(self.toggle_normalize)
        self.toolbar.addWidget(self.norm_btn)

        self.align_btn = QPushButton("Align")
        self.align_btn.setToolTip("Align wells by the front edge of the highest peak")
        self.align_btn.setCheckable(True)
        self.align_btn.setChecked(False)
        self.align_btn.setFixedSize(44, 36)
        self.align_btn.setStyleSheet("""
            QPushButton {
                border-radius: 6px; font-size: 10px; font-weight: bold;
                padding: 0px 4px;
            }
            QPushButton:checked { border: 2px solid #0071e3; color: #0071e3; }
        """)
        self.align_btn.clicked.connect(self.toggle_align)
        self.toolbar.addWidget(self.align_btn)

        self.toolbar.addSeparator()
        self.spectral_btn = QPushButton("SpecSep")
        self.spectral_btn.setToolTip("Apply spectral separation (dye crosstalk correction)")
        self.spectral_btn.setCheckable(True)
        self.spectral_btn.setChecked(False)
        self.spectral_btn.setFixedSize(60, 36)
        self.spectral_btn.setStyleSheet("""
            QPushButton {
                border-radius: 6px; font-size: 9px; font-weight: bold;
                padding: 0px 4px;
            }
            QPushButton:checked { border: 2px solid #0071e3; color: #0071e3; }
        """)
        self.spectral_btn.clicked.connect(self.toggle_spectral)
        self.toolbar.addWidget(self.spectral_btn)

        self.matrix_btn = QPushButton("Mat\u2026")
        self.matrix_btn.setToolTip("Edit the spectral separation matrix")
        self.matrix_btn.setFixedSize(36, 36)
        self.matrix_btn.setStyleSheet("""
            QPushButton {
                border-radius: 6px; font-size: 9px; font-weight: bold;
                padding: 0px 4px;
            }
        """)
        self.matrix_btn.clicked.connect(self._edit_spectral_matrix)
        self.toolbar.addWidget(self.matrix_btn)

        self.toolbar.addSeparator()
        self.chemistry_combo = QComboBox()
        self.chemistry_combo.addItems(list(CHEMISTRY_MAP.keys()))
        self.chemistry_combo.setToolTip("Chemistry type for base calling")
        self.chemistry_combo.setFixedWidth(160)
        self.toolbar.addWidget(self.chemistry_combo)

        self.call_bases_btn = QPushButton("Call Bases")
        self.call_bases_btn.setToolTip("Run base calling on selected wells")
        self.call_bases_btn.setFixedSize(80, 36)
        self.call_bases_btn.setStyleSheet("""
            QPushButton {
                border-radius: 6px; font-size: 9px; font-weight: bold;
                padding: 0px 4px;
            }
        """)
        self.call_bases_btn.clicked.connect(self._call_bases)
        self.toolbar.addWidget(self.call_bases_btn)

        self.toolbar.addSeparator()
        self._esd_caller_combo = QComboBox()
        self._esd_caller_combo.setToolTip("Select ESD base caller to overlay on trace")
        self._esd_caller_combo.setFixedWidth(140)
        self._esd_caller_combo.addItem("Base Calls: None")
        self._esd_caller_combo.currentTextChanged.connect(self.update_plot)
        self.toolbar.addWidget(self._esd_caller_combo)

        center_layout.addWidget(self.canvas, stretch=5)

        self.subplots = []
        for i in range(6):
            if i == 0:
                ax = self.figure.add_subplot(6, 1, i + 1)
            else:
                ax = self.figure.add_subplot(6, 1, i + 1, sharex=self.subplots[0]['ax'])
            ax2 = ax.twinx()
            ax.set_visible(False)
            ax2.set_visible(False)
            self.subplots.append({'ax': ax, 'ax2': ax2, 'well': None})

        self.click_hint = QLabel(
            "Click on plot to add/remove peaks  |  "
            "Edit table cells directly  |  "
            "Ctrl+Z: undo  |  Ctrl+Shift+Z: redo"
        )
        self.click_hint.setStyleSheet("color: gray; font-size: 10px;")
        center_layout.addWidget(self.click_hint)

        self.peak_table = QTableWidget()
        self.peak_table.setColumnCount(8)
        self.peak_table.setHorizontalHeaderLabels([
            'Well', 'Channel', 'Peak', 'Scan', 'Height', 'Width', 'Baseline', 'Area'
        ])
        self.peak_table.setEditTriggers(QTableWidget.DoubleClicked)
        self.peak_table.itemChanged.connect(self._on_table_edited)
        self.peak_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.peak_table.customContextMenuRequested.connect(self._table_context_menu)
        center_layout.addWidget(self.peak_table, stretch=1)

        self._esd_seq_label = QLabel()
        self._esd_seq_label.setWordWrap(True)
        self._esd_seq_label.setFont(QFont('monospace', 9))
        self._esd_seq_label.setStyleSheet(
            "QLabel { background: #fafafa; border: 1px solid #ddd; "
            "padding: 4px; margin: 2px 0px; }"
        )
        self._esd_seq_label.setVisible(False)
        center_layout.addWidget(self._esd_seq_label)

        QShortcut(QKeySequence(Qt.Key_Left), self, self._prev_well_single)
        QShortcut(QKeySequence(Qt.Key_Right), self, self._next_well_single)

        # Replace Home/Back/Forward with Auto X/Y checkboxes
        for act in self.toolbar.actions():
            txt = act.text()
            if txt in ('Home', 'Back', 'Forward'):
                act.setVisible(False)
        # Find position after the separator following Forward
        actions = self.toolbar.actions()
        insert_idx = None
        for i, act in enumerate(actions):
            if act.isSeparator() and i > 0 and not actions[i-1].isVisible():
                insert_idx = i + 1
                break
        if insert_idx is None:
            insert_idx = 0
        self._auto_x_btn = QCheckBox("Auto X")
        self._auto_x_btn.setChecked(True)
        self._auto_x_btn.setToolTip("Auto-scale X axis when navigating wells")
        self._auto_x_btn.toggled.connect(lambda on: setattr(self, 'auto_scale_x', on))
        self._auto_x_btn.setStyleSheet(
            "QCheckBox::indicator:checked { background-color: #aaddff; border-radius: 2px; }"
        )
        self.toolbar.insertWidget(actions[insert_idx], self._auto_x_btn)
        self._auto_y_btn = QCheckBox("Auto Y")
        self._auto_y_btn.setChecked(True)
        self._auto_y_btn.setToolTip("Auto-scale Y axis when navigating wells")
        self._auto_y_btn.toggled.connect(lambda on: setattr(self, 'auto_scale_y', on))
        self._auto_y_btn.setStyleSheet(
            "QCheckBox::indicator:checked { background-color: #aaddff; border-radius: 2px; }"
        )
        self.toolbar.insertWidget(actions[insert_idx], self._auto_y_btn)

        return center

    # ------------------------------------------------------------------
    # Style
    # ------------------------------------------------------------------

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f7; }
            QWidget {
                font-family: -apple-system, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
                font-size: 14px; color: #1d1d1f;
            }
            QSplitter::handle { background-color: #d2d2d7; width: 1px; }
            QPushButton {
                background-color: #ffffff; border: 1px solid #d2d2d7;
                border-radius: 6px; padding: 6px 14px;
                font-size: 12px; color: #1d1d1f;
            }
            QPushButton:hover { background-color: #e8e8ed; border-color: #c7c7cc; }
            QPushButton:pressed { background-color: #d2d2d7; }
            QPushButton:checked {
                background-color: #007AFF; border-color: #007AFF; color: #ffffff;
            }
            QToolButton {
                background-color: #ffffff; border: 1px solid #d2d2d7;
                border-radius: 6px; padding: 6px 10px;
                font-size: 12px; color: #1d1d1f;
            }
            QToolButton:hover { background-color: #e8e8ed; }
            QCheckBox { spacing: 6px; font-size: 12px; }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 1px solid #c7c7cc; border-radius: 4px;
                background-color: #ffffff;
            }
            QCheckBox::indicator:checked {
                background-color: #0071e3; border-color: #0071e3;
            }
            QSpinBox, QComboBox {
                background-color: #ffffff; border: 1px solid #d2d2d7;
                border-radius: 5px; padding: 4px 6px;
                font-size: 12px; min-height: 20px; color: #1d1d1f;
            }
            QSpinBox:focus, QComboBox:focus { border-color: #0071e3; }
            QSpinBox::up-button, QSpinBox::down-button { width: 22px; }

            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background-color: #ffffff; border: 1px solid #d2d2d7;
                border-radius: 5px; selection-background-color: #0071e3;
                selection-color: #ffffff;
            }
            QLabel { font-size: 12px; color: #1d1d1f; }
            QTableWidget {
                background-color: #ffffff; border: 1px solid #d2d2d7;
                border-radius: 6px; gridline-color: #e8e8ed;
                font-size: 13px; color: #1d1d1f;
            }
            QTableWidget::item { padding: 4px 8px; }
            QTableWidget::item:selected {
                background-color: #e8f0fe; color: #1d1d1f;
            }
            QHeaderView::section {
                background-color: #f5f5f7; border: none;
                border-bottom: 1px solid #d2d2d7; padding: 6px 8px;
                font-weight: 600; font-size: 12px; color: #6e6e73;
            }
            QScrollBar:vertical {
                background-color: #f5f5f7; width: 10px;
                border: none; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #c7c7cc; border-radius: 5px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background-color: #a1a1a6; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

    # ------------------------------------------------------------------
    # Detector parameter sync
    # ------------------------------------------------------------------

    def _sync_detector_params(self):
        self.detector.min_height = self.height_spin.value()
        self.detector.prominence = self.prominence_spin.value()
        self.detector.distance = self.distance_spin.value()
        self.detector.min_width = self.min_width_spin.value()
        self.detector.baseline_method = self.baseline_combo.currentText()
        bl_method = self.detector.baseline_method
        if bl_method == "Rolling Min":
            self.detector.baseline_param = self.bl_spin.value()
        elif bl_method == "ALS":
            self.detector.baseline_param = 10 ** self.bl_spin.value()
        self.detector.limit_range = self.range_cb.isChecked()
        self.detector.scan_start = self.start_spin.value()
        self.detector.scan_end = self.end_spin.value()
        self.detector.group_stutter = self.stutter_cb.isChecked()
        self.detector.stutter_window = self.stutter_spin.value()
        active = {}
        for ch, btn in self.channel_buttons.items():
            active[ch] = btn.isChecked()
        # Force-activate the IS channel so its peaks are always available for filtering
        if self._is_channel:
            active[self._is_channel] = True
        self.detector.active_channels = active

    def _mark_dirty_and_update(self):
        self._dirty_wells.update(self._well_data.keys())
        self.update_plot()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _find_data_start(self, path):
        with open(path, 'r', encoding='iso-8859-1') as f:
            for i, line in enumerate(f):
                if line.startswith('Scan') and 'Channel' in line:
                    return i
        return None

    @staticmethod
    def _parse_rsd(path):
        """Parse a binary .rsd file into a DataFrame matching .txt column layout."""
        with open(path, 'rb') as f:
            raw = f.read()
        records = []
        for i in range(0, len(raw) - 19, 20):
            v = struct.unpack('<IIIII', raw[i:i+20])
            records.append(v)

        # Find the \x05-tagged metadata to know where data ends
        meta_pos = len(raw)
        for anchor in [b'\x05\tBAR CODE\x00', b'\x05\x0cBASE CALLER\x00']:
            idx = raw.find(anchor)
            if idx >= 0:
                meta_pos = idx
                break
        meta_record = meta_pos // 20

        data = records[:meta_record]
        df = pd.DataFrame(data, columns=['Current', 'Channel1', 'Channel2', 'Channel3', 'Channel4'])
        df['Scan'] = np.arange(len(df))
        return df[['Scan', 'Channel1', 'Channel2', 'Channel3', 'Channel4', 'Current']]

    @staticmethod
    def _parse_rsd_header(path):
        """Extract metadata header fields from an .rsd binary file.

        Returns a flat dict with keys like 'MACHINE ID', 'CHANNEL1_DYE', etc.
        """
        with open(path, 'rb') as f:
            raw = f.read()
        meta = {}
        # Find the metadata section by locating a known anchor tag.
        anchor = b'\x05\tBAR CODE\x00'
        aidx = raw.find(anchor)
        if aidx < 0:
            return meta

        # The metadata section is a sequence of \x05-tagged records.
        # Format: \x05 <length> <length bytes of content (includes trailing \x00)>
        # The content string ends with \x00. Tags alternate between key/value pairs.
        # Some keys have binary values (the value is not a \x05-tagged string).
        KEY_TAGS = {
            'BAR CODE', 'BASE CALLER', 'CHEMISTRY', 'APPLICATION',
            'BEAMSPLITTER A', 'BEAMSPLITTER B',
            'CHANNEL1', 'CHANNEL2', 'CHANNEL3', 'CHANNEL4',
            'LASER MODE', 'NAME', 'COMMENT', 'MACHINE ID',
            'PLATE ID', 'SAMPLE NAME', 'WELL ID',
            'BASE', 'DYE', 'FILTER',
        }
        # Parse all tags into a flat list of (content_without_null, raw_bytes)
        tags = []
        i = aidx
        while i < len(raw) - 3:
            if raw[i] == 0x05:
                length = raw[i + 1]
                if i + 2 + length > len(raw):
                    break
                tag_raw = raw[i + 2:i + 2 + length]
                # Content is null-terminated within the length bytes
                null_pos = tag_raw.find(b'\x00')
                content = tag_raw[:null_pos].decode('latin-1', errors='replace') if null_pos >= 0 else ''
                tags.append(content)
                i += 2 + length
            else:
                i += 1
            # Safety limit
            if len(tags) > 200:
                break

        # Now extract key-value pairs from the alternating tag list
        current_channel = None
        i = 0
        while i < len(tags):
            tag = tags[i]
            if not tag:
                i += 1
                continue
            if tag.startswith('CHANNEL'):
                current_channel = tag
                i += 1
                while i < len(tags) and not tags[i].startswith('CHANNEL'):
                    child = tags[i]
                    # Stop at top-level KEY_TAGS that are not CHANNEL children
                    if child in KEY_TAGS and child not in ('DYE', 'FILTER', 'BASE'):
                        break
                    if child in ('DYE', 'FILTER'):
                        if i + 1 < len(tags):
                            meta[f'{current_channel}_{child}'] = tags[i + 1]
                            i += 1
                    i += 1
            elif tag in KEY_TAGS:
                # Simple key-value pair: next tag is the value
                if i + 1 < len(tags) and tags[i + 1] not in KEY_TAGS:
                    meta[tag] = tags[i + 1]
                    i += 2
                else:
                    meta[tag] = ''
                    i += 1
            else:
                i += 1

        return meta

    @staticmethod
    def _parse_txt_header(path):
        """Extract metadata header lines from a .txt electropherogram file."""
        meta = {}
        with open(path, 'r', encoding='iso-8859-1') as f:
            for line in f:
                line = line.rstrip()
                if line.startswith('Scan') and 'Channel' in line:
                    break
                if ':' in line:
                    key, _, val = line.partition(':')
                    meta[key.strip()] = val.strip()
                elif line.strip():
                    meta.setdefault('Info', []).append(line.strip())
        return meta

    def load_folder(self):
        default_dir = os.path.dirname(os.path.abspath(__file__))
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", default_dir)
        if not folder:
            return

        # Prefer .rsd over .txt (choose whichever exists in the folder)
        rsd_files = [f for f in os.listdir(folder) if f.lower().endswith(".rsd")]
        txt_files = [f for f in os.listdir(folder) if f.lower().endswith(".txt")]
        if rsd_files:
            files = sorted(rsd_files)
            is_rsd = True
        elif txt_files:
            files = sorted(txt_files)
            is_rsd = False
        else:
            QMessageBox.information(
                self, "Load Folder",
                "No .rsd or .txt files found in the selected folder."
            )
            return

        progress = QProgressDialog("Loading files...", "Cancel", 0, len(files), self)
        progress.setWindowTitle("Loading")
        progress.setWindowModality(Qt.WindowModal)

        loaded = 0
        for idx, fname in enumerate(files):
            if progress.wasCanceled():
                break
            progress.setValue(idx)

            well = os.path.splitext(fname)[0]
            if well not in self.well_list:
                continue

            path = os.path.join(folder, fname)
            try:
                if is_rsd:
                    df = self._parse_rsd(path)
                else:
                    header_line = self._find_data_start(path)
                    if header_line is None:
                        continue
                    df = pd.read_csv(
                        path, sep=r"\s+", skiprows=header_line,
                        encoding="iso-8859-1", engine="python",
                        skip_blank_lines=True,
                    )
                    df = df.dropna(how="all")
                    df = df.apply(pd.to_numeric, errors="coerce")
                    df = df.dropna(subset=["Scan"])
                    df = df.reset_index(drop=True)

                self.all_data[well] = df
                loaded += 1
            except Exception:
                pass

        progress.close()
        self._update_well_styles()
        self.status_label.setText(f"Loaded {loaded} wells")
        self._original_all_data = None
        for btn in [self.norm_btn, self.align_btn, self.spectral_btn]:
            if btn.isChecked():
                btn.setChecked(False)
        if loaded > 0:
            first = sorted(self.all_data.keys())[0]
            self.selected_wells = set(self.all_data.keys())
            self._dirty_wells.update(self.all_data.keys())
            self._load_peak_data(folder)

            # Scan for ESD subdirectories
            self._esd_data = {}
            self._esd_callers = []
            self._esd_raw_to_display = {}
            self._esd_display_to_raw = {}
            from extract_training_data import parse_esd
            esd_subdirs = []
            for entry in sorted(os.listdir(folder)):
                subdir = os.path.join(folder, entry)
                if not os.path.isdir(subdir):
                    continue
                esd_files = [f for f in os.listdir(subdir) if f.lower().endswith('.esd')]
                if not esd_files:
                    continue
                esd_subdirs.append((entry, subdir))

            if esd_subdirs:
                total_esd = sum(len(ef) for _, ef in
                                [(s, [f for f in os.listdir(s) if f.lower().endswith('.esd')])
                                 for _, s in esd_subdirs])
                esd_progress = QProgressDialog("Loading ESD base calls...", "Cancel", 0, max(total_esd, 1), self)
                esd_progress.setWindowTitle("Loading ESD")
                esd_progress.setWindowModality(Qt.WindowModal)
                esd_count = 0
                for raw_name, subdir in esd_subdirs:
                    display_name = esd_caller_display_name(raw_name)
                    self._esd_callers.append((raw_name, subdir))
                    self._esd_display_to_raw[display_name] = raw_name
                    self._esd_raw_to_display[raw_name] = display_name
                    for fname in sorted(os.listdir(subdir)):
                        if not fname.lower().endswith('.esd'):
                            continue
                        if esd_progress.wasCanceled():
                            break
                        esd_progress.setValue(min(esd_count, total_esd)); esd_count += 1
                        well = os.path.splitext(fname)[0]
                        if well not in self.all_data:
                            continue
                        try:
                            esd = parse_esd(os.path.join(subdir, fname))
                            self._esd_data.setdefault(well, {})[raw_name] = esd
                        except Exception:
                            pass
                esd_progress.close()
            self._update_esd_caller_combo()

            self._update_well_styles()
            self._highlight_well(first)
            self.update_plot()
        self._current_folder = folder
        self.folder_label.setText(os.path.basename(folder))
        self._populate_file_header()

    def _populate_file_header(self):
        """Parse and display user comments from the loaded folder's .rsd files."""
        if not self._current_folder:
            self.header_group.setVisible(False)
            return
        first_file = None
        for fname in sorted(os.listdir(self._current_folder)):
            if fname.lower().endswith('.rsd'):
                first_file = os.path.join(self._current_folder, fname)
                break
        if first_file is None:
            self.header_group.setVisible(False)
            return

        meta = self._parse_rsd_header(first_file)
        comment = meta.get('COMMENT', '')
        SYSTEM_DEFAULTS = {'Genotyping Default', 'Sequencing Default',
                           'Fragment Default', 'HID Default', ''}

        rows = []
        if comment and comment not in SYSTEM_DEFAULTS:
            rows.append(('Comments', comment))
        elif comment:
            rows.append(('Comments', f'{comment} (default)'))

        self._file_header = dict(rows)
        self.header_table.setRowCount(len(rows))
        for i, (field, value) in enumerate(rows):
            self.header_table.setItem(i, 0, QTableWidgetItem(field))
            val_item = QTableWidgetItem(str(value)[:120])
            val_item.setToolTip(str(value))
            self.header_table.setItem(i, 1, val_item)
        self.header_table.resizeColumnToContents(0)
        self.header_group.setVisible(len(rows) > 0)

    # ------------------------------------------------------------------
    # Well selection / navigation
    # ------------------------------------------------------------------

    def load_well(self, well):
        if well not in self.all_data:
            return
        self.selected_wells = {well}
        self._update_well_styles()
        self._highlight_well(well)
        self._sync_page_start(well)
        self.update_plot()

    def _sync_page_start(self, well):
        all_wells = sorted(self.all_data.keys())
        if well in all_wells:
            self._page_start = (all_wells.index(well) // MAX_WELLS_PER_PAGE) * MAX_WELLS_PER_PAGE

    def _select_wells(self, wells):
        self.selected_wells = set(wells) & set(self.all_data.keys())
        if self.selected_wells:
            first = sorted(self.selected_wells)[0]
            self._sync_page_start(first)
            self._highlight_well(first)
        else:
            self._page_start = 0
            self._highlight_well(None)
        self._update_well_styles()
        self.update_plot()

    def _toggle_well_selection(self, well):
        if well in self.selected_wells:
            self.selected_wells.discard(well)
        elif well in self.all_data:
            self.selected_wells.add(well)
        else:
            return
        if self.selected_wells:
            first = sorted(self.selected_wells)[0]
            self._sync_page_start(first)
        else:
            self._page_start = 0
        self._update_well_styles()

    def _on_well_clicked(self, well):
        if QApplication.keyboardModifiers() == Qt.ControlModifier:
            self._toggle_well_selection(well)
            if self.selected_wells:
                first = sorted(self.selected_wells)[0]
                self._highlight_well(first)
                self.update_plot()
        else:
            self.load_well(well)

    def prev_well(self):
        """Move backward by the number of selected wells."""
        all_wells = sorted(self.all_data.keys())
        if not all_wells or not self.selected_wells:
            return
        step = min(len(self.selected_wells), MAX_WELLS_PER_PAGE)
        indices = sorted(all_wells.index(w) for w in self.selected_wells)
        target = indices[0] - step
        if target < 0:
            return
        self._select_wells([all_wells[i] for i in range(target, target + step)])

    def next_well(self):
        """Move forward by the number of selected wells."""
        all_wells = sorted(self.all_data.keys())
        if not all_wells or not self.selected_wells:
            return
        step = min(len(self.selected_wells), MAX_WELLS_PER_PAGE)
        indices = sorted(all_wells.index(w) for w in self.selected_wells)
        target = indices[-1] + 1
        if target >= len(all_wells):
            return
        end = min(target + step, len(all_wells))
        self._select_wells([all_wells[i] for i in range(target, end)])

    def _prev_well_single(self):
        """Keyboard shortcut: move one well left in the grid."""
        if not self._active_well:
            return
        all_wells = sorted(self.all_data.keys())
        idx = all_wells.index(self._active_well)
        if idx > 0:
            self.load_well(all_wells[idx - 1])

    def _next_well_single(self):
        """Keyboard shortcut: move one well right in the grid."""
        if not self._active_well:
            return
        all_wells = sorted(self.all_data.keys())
        idx = all_wells.index(self._active_well)
        if idx < len(all_wells) - 1:
            self.load_well(all_wells[idx + 1])

    # ------------------------------------------------------------------
    # Well button styling
    # ------------------------------------------------------------------

    def _update_well_styles(self):
        base = """
            QPushButton {
                font-size: 10px; padding: 0px;
                border-radius: 3px;
            }
        """
        for w, btn in self.well_buttons.items():
            if w in self.all_data:
                if w in self.selected_wells:
                    btn.setStyleSheet(base + """ QPushButton {
                        background-color: #BBDEFB; border: 2px solid #64B5F6;
                        font-weight: bold;
                    } QPushButton:hover { background-color: #90CAF9; }""")
                else:
                    btn.setStyleSheet(base + """ QPushButton {
                        background-color: #ffffff; border: 1px solid #d2d2d7;
                    } QPushButton:hover { background-color: #e8e8ed; }""")
            else:
                btn.setStyleSheet(base + """ QPushButton {
                    background-color: #ffffff; border: 1px solid #d2d2d7;
                } QPushButton:hover { background-color: #e8e8ed; }""")

    def _highlight_well(self, well):
        self._update_well_styles()
        btn = self.well_buttons.get(well)
        if btn:
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 10px; padding: 0px;
                    border-radius: 3px;
                    background-color: #6495ed; border: 1px solid #4169e1;
                    color: white; font-weight: bold;
                }
                QPushButton:hover { background-color: #4169e1; }
            """)

    # ------------------------------------------------------------------
    # Channel toggling
    # ------------------------------------------------------------------

    def _on_range_toggle(self):
        enabled = self.range_cb.isChecked()
        self.start_spin.setEnabled(enabled)
        self.end_spin.setEnabled(enabled)

    def _restore_and_apply_transforms(self):
        """Restore data from originals and re-apply enabled transforms."""
        if not self.all_data:
            return
        if self._original_all_data is None:
            return
        self.all_data = {w: df.copy() for w, df in self._original_all_data.items()}

        any_on = False
        if self.norm_btn.isChecked():
            any_on = True
            well_means = {}
            for well, df in self.all_data.items():
                if "Current" in df.columns:
                    well_means[well] = df["Current"].mean()
            if well_means:
                overall_mean = sum(well_means.values()) / len(well_means)
                for well, df in self.all_data.items():
                    wm = well_means.get(well)
                    if wm is None or wm == 0:
                        continue
                    df["Scan"] = df["Scan"] * (wm / overall_mean)

        if self.align_btn.isChecked():
            any_on = True
            self._sync_detector_params()
            all_wells = sorted(self.all_data.keys())
            well_lefts = {}
            for well in all_wells:
                df = self.all_data[well]
                wd = self.detector.detect(df, df["Scan"])
                if len(wd["peaks"]) == 0:
                    continue
                heights = np.array([
                    wd["channel_data"][ch][p]
                    for p, ch in zip(wd["peaks"], wd["peak_channels"])
                ])
                idx = heights.argmax()
                left_scan = np.interp(
                    wd["peak_lefts"][idx], np.arange(len(df)), df["Scan"]
                )
                well_lefts[well] = {"left_scan": left_scan, "wd": wd, "peak_idx": idx}

            if well_lefts:
                target = np.median([v["left_scan"] for v in well_lefts.values()])
                for well, v in well_lefts.items():
                    shift = target - v["left_scan"]
                    self.all_data[well]["Scan"] = self.all_data[well]["Scan"] + shift

        if self.spectral_btn.isChecked():
            any_on = True
            inv_mat = np.linalg.inv(self._spectral_matrix)
            for df in self.all_data.values():
                ch_cols = ["Channel1", "Channel2", "Channel3", "Channel4"]
                present = [c for c in ch_cols if c in df.columns]
                if len(present) < 4:
                    continue
                raw = df[present].values.astype(np.float64)
                clean = raw @ inv_mat.T
                for i, col in enumerate(present):
                    df[col] = np.maximum(clean[:, i], 0.0)

        if not any_on:
            self._original_all_data = None

        self._mark_dirty_and_update()

    def toggle_normalize(self):
        if not self.all_data:
            self.norm_btn.setChecked(False)
            return
        if self._original_all_data is None:
            self._original_all_data = {
                w: df.copy() for w, df in self.all_data.items()
            }
        self._restore_and_apply_transforms()

    def toggle_align(self):
        if not self.all_data:
            self.align_btn.setChecked(False)
            return
        if self._original_all_data is None:
            self._original_all_data = {
                w: df.copy() for w, df in self.all_data.items()
            }
        self._restore_and_apply_transforms()

    def toggle_spectral(self):
        if not self.all_data:
            self.spectral_btn.setChecked(False)
            return
        if self._original_all_data is None:
            self._original_all_data = {
                w: df.copy() for w, df in self.all_data.items()
            }
        self._restore_and_apply_transforms()

    def _call_bases(self):
        if not self.selected_wells:
            QMessageBox.information(self, "Base Calling", "Select at least one well.")
            return
        chemistry = self.chemistry_combo.currentText()
        results = {}
        ml_model = None
        if chemistry in ("ML Base Caller", "ML Scan Caller"):
            try:
                from basecaller import _load_ml_model, MODEL_PATH, MODEL_PATH_WITH_BG
                model_path = MODEL_PATH_WITH_BG if chemistry == "ML Scan Caller" else MODEL_PATH
                ml_model = _load_ml_model(model_path)
            except (FileNotFoundError, Exception) as e:
                model_type = "background-trained" if chemistry == "ML Scan Caller" else ""
                QMessageBox.critical(
                    self, chemistry,
                    f"Cannot load {model_type} ML model:\n{e}\n\n"
                    f"Train it first with:\n"
                    f"  python train_model.py{ ' --include-background' if chemistry == 'ML Scan Caller' else ''}"
                )
                return
        for well in sorted(self.selected_wells):
            if well not in self.all_data:
                continue
            df = self.all_data[well]
            self._sync_detector_params()
            if chemistry == "ML Base Caller":
                wd = self.detector.detect_basecalling(df, df["Scan"])
                if len(wd["peaks"]) == 0:
                    continue
                bc = basecall_ml(
                    data=df,
                    peaks=wd["peaks"],
                    peak_channels=wd["peak_channels"],
                    scan_values=wd["scan_values"],
                    model=ml_model,
                    min_quality=10,
                    auto_threshold=True,
                )
            elif chemistry == "ML Scan Caller":
                from basecaller import basecall_ml_scan
                bc = basecall_ml_scan(
                    data=df,
                    scan_values=df["Scan"],
                    model=ml_model,
                    min_confidence=0.8,
                )
            elif chemistry == "Cimarron 3.12 (Python)":
                wd = self.detector.detect_basecalling(df, df["Scan"])
                if len(wd["peaks"]) == 0:
                    continue
                bc = basecall_cimarron(
                    data=df,
                    peaks=wd["peaks"],
                    peak_channels=wd["peak_channels"],
                    scan_values=wd["scan_values"],
                    min_quality=10,
                    spectral_matrix=self._spectral_matrix,
                    variant=None,
                )
            else:
                wd = self.detector.detect_basecalling(df, df["Scan"])
                if len(wd["peaks"]) == 0:
                    continue
                bc = basecall(
                    data=df,
                    peaks=wd["peaks"],
                    peak_channels=wd["peak_channels"],
                    scan_values=wd["scan_values"],
                    chemistry=chemistry,
                    min_quality=10,
                )
            results[well] = bc

        if not results:
            QMessageBox.information(
                self, "Base Calling", "No bases called. Check peak detection."
            )
            return
        dlg = SequenceDialog(results, self)
        dlg.exec()

    def _edit_spectral_matrix(self):
        if self.spectral_btn.isChecked():
            QMessageBox.information(
                self, "Spectral Separation",
                "Turn off SpecSep before editing the matrix."
            )
            return
        dlg = MatrixEditorDialog(self._spectral_matrix, self)
        if dlg.exec():
            self._spectral_matrix = dlg.get_matrix()
            self.status_label.setText(
                f"Spectral matrix updated  |  {''.ljust(40)}"
            )

    def toggle_channel(self):
        for ch, btn in self.channel_buttons.items():
            self._update_channel_style(ch)
        self._mark_dirty_and_update()

    def _update_channel_style(self, ch):
        btn = self.channel_buttons[ch]
        colors = self.channel_colors.get(ch)
        if not colors:
            return
        if btn.isChecked():
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['active']};
                    color: white;
                    border: 2px solid {colors['active']};
                    border-radius: 20px;
                    font-size: 11px; font-weight: bold;
                    padding: 0px;
                }}
                QPushButton:hover {{ background-color: {colors['active']}; }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {colors['inactive']};
                    color: #8e8e93;
                    border: 1px solid {colors['inactive']};
                    border-radius: 20px;
                    font-size: 11px; font-weight: bold;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {colors['inactive']};
                    border-color: #c7c7cc;
                }}
            """)

    # ------------------------------------------------------------------
    # Peak detection helpers
    # ------------------------------------------------------------------

    def _ensure_well_detected(self, well):
        """Run detection if the well is dirty or not cached."""
        if well not in self.all_data:
            return
        if well in self._well_data and well not in self._dirty_wells:
            return
        df = self.all_data[well]
        scan = df["Scan"]
        wd = self.detector.detect(df, scan)
        self._apply_manual_edits(well, wd)
        self._well_data[well] = wd
        self._dirty_wells.discard(well)

    def _apply_manual_edits(self, well, wd):
        """Apply deleted/manual peak overrides to a detection result."""
        # Remove deleted peaks (by index into scan array)
        deleted = self._deleted_peaks.get(well, set())
        if deleted and len(wd['peaks']) > 0:
            keep_mask = np.array([p not in deleted for p in wd['peaks']])
            wd['peaks'] = wd['peaks'][keep_mask]
            wd['peak_channels'] = [wd['peak_channels'][i] for i in range(len(wd['peak_channels'])) if keep_mask[i]]
            wd['peak_lefts'] = wd['peak_lefts'][keep_mask]
            wd['peak_rights'] = wd['peak_rights'][keep_mask]

        # Add manually added peaks
        manual = self._manual_peaks.get(well, [])
        for idx, ch in manual:
            if not np.any(wd['peaks'] == idx):
                wd['peaks'] = np.append(wd['peaks'], idx)
                wd['peak_channels'].append(ch)
                wd['peak_lefts'] = np.append(wd['peak_lefts'], max(0, idx - 2))
                wd['peak_rights'] = np.append(wd['peak_rights'], idx + 2)

        if len(wd['peaks']) > 0:
            sort_idx = np.argsort(wd['peaks'])
            wd['peaks'] = wd['peaks'][sort_idx]
            wd['peak_channels'] = [wd['peak_channels'][i] for i in sort_idx]
            wd['peak_lefts'] = wd['peak_lefts'][sort_idx]
            wd['peak_rights'] = wd['peak_rights'][sort_idx]

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def _export_peak_rows(self, wells):
        """Build a list of peak-data dicts for the given wells."""
        rows = []
        for well in wells:
            if well not in self.all_data:
                continue
            self._sync_detector_params()
            df = self.all_data[well]
            scan = df["Scan"]
            wd = self.detector.detect(df, scan)
            self._apply_manual_edits(well, wd)
            rows.extend(self.detector.build_peak_rows(well, wd))
        return rows

    # ------------------------------------------------------------------
    # IS filtering
    # ------------------------------------------------------------------

    def _apply_is_filter(self):
        """Keep only the selected IS peak(s) in the IS channel.
        Sample channels are unaffected — IS is only for area normalisation."""
        ch = self._is_channel
        if not ch:
            return
        n_is = self._is_peak_num
        if n_is is None or n_is < 1:
            return

        for well, wd in self._well_data.items():
            if well not in self.all_data:
                continue
            peaks = wd['peaks']
            pchs = wd['peak_channels']

            is_idx = [i for i, pc in enumerate(pchs) if pc == ch]
            if not is_idx:
                continue

            ch_data = wd['channel_data'].get(ch)
            if ch_data is None:
                continue
            heights = [ch_data[peaks[i]] for i in is_idx]
            top = sorted(is_idx, key=lambda i: heights[is_idx.index(i)], reverse=True)[:n_is]
            top = set(top)

            new_peaks = []
            new_channels = []
            new_lefts = []
            new_rights = []

            for i, pc in enumerate(pchs):
                if pc == ch:
                    if i not in top:
                        continue  # drop this IS peak
                new_peaks.append(peaks[i])
                new_channels.append(pc)
                new_lefts.append(wd['peak_lefts'][i])
                new_rights.append(wd['peak_rights'][i])

            if new_peaks:
                order = np.argsort(new_peaks)
                wd['peaks'] = np.array(new_peaks)[order]
                wd['peak_channels'] = [new_channels[i] for i in order]
                wd['peak_lefts'] = np.array(new_lefts)[order]
                wd['peak_rights'] = np.array(new_rights)[order]
            else:
                wd['peaks'] = np.array([], dtype=int)
                wd['peak_channels'] = []
                wd['peak_lefts'] = np.array([])
                wd['peak_rights'] = np.array([])

    # ------------------------------------------------------------------
    # Plot
    # ------------------------------------------------------------------

    def update_plot(self):
        all_wells = sorted(self.all_data.keys())
        if not all_wells:
            return
        page_wells = sorted(self.selected_wells)[:MAX_WELLS_PER_PAGE] if self.selected_wells else all_wells[:MAX_WELLS_PER_PAGE]

        self._sync_detector_params()

        # Remove old figure-level labels
        for label in self._figure_labels:
            try:
                label.remove()
            except Exception:
                pass
        self._figure_labels = []
        self._peak_marker_lines.clear()

        # Save axis limits before clearing (for auto-scale toggle)
        if self.subplots:
            self._saved_xlim = self.subplots[0]['ax'].get_xlim()
            self._saved_ylims = [sp['ax'].get_ylim() for sp in self.subplots]
            self._saved_ylims2 = [sp['ax2'].get_ylim() for sp in self.subplots]
        else:
            self._saved_xlim = None
            self._saved_ylims = []
            self._saved_ylims2 = []

        # Recreate subplots fresh for the right number
        self.figure.clf()
        self.subplots.clear()

        n = len(page_wells)
        for i in range(n):
            if i == 0:
                ax = self.figure.add_subplot(n, 1, i + 1)
            else:
                ax = self.figure.add_subplot(n, 1, i + 1, sharex=self.subplots[0]['ax'])
            ax2 = ax.twinx()
            self.subplots.append({'ax': ax, 'ax2': ax2, 'well': None})

        self._current_page_wells = page_wells

        has_any_signal = False
        has_any_current = False

        for i, well in enumerate(page_wells):
            if well not in self.all_data:
                continue
            sp = self.subplots[i]
            sp['well'] = well
            sp['ax'].set_visible(True)

            df = self.all_data[well]
            scan = df["Scan"]

            self._ensure_well_detected(well)

            has_signal = False
            has_current = False
            for ch in self.channel_buttons:
                if not self.channel_buttons[ch].isChecked():
                    continue
                if ch not in df.columns:
                    continue
                y = df[ch]
                color = self.channel_colors.get(ch, {}).get('active')
                if ch == "Current":
                    sp['ax2'].plot(scan, y / 10, linestyle="-", linewidth=0.5, label=ch, color=color)
                    has_current = True
                else:
                    sp['ax'].plot(scan, y, linewidth=0.5, label=ch, color=color)
                    has_signal = True

            has_any_signal = has_any_signal or has_signal
            has_any_current = has_any_current or has_current

            sp['ax'].set_visible(True)
            sp['ax2'].set_visible(has_current)
            sp['ax'].yaxis.set_visible(has_signal)

            sp['ax'].text(
                0.02, 0.95, well, transform=sp['ax'].transAxes,
                fontsize=8, va='top', ha='left',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.7)
            )

            # X-axis — ticks and label on the bottom subplot only
            if i < len(page_wells) - 1:
                sp['ax'].xaxis.set_tick_params(labelbottom=False)
            else:
                sp['ax'].xaxis.set_tick_params(labelbottom=True)
                sp['ax'].set_xlabel("Scan")
                sp['ax'].xaxis.set_major_locator(MaxNLocator(nbins=5))

        # Figure-level y-axis labels centered on the plot area
        if self.subplots:
            first = self.subplots[0]['ax'].get_position()
            last = self.subplots[-1]['ax'].get_position()
            center_y = (first.y1 + last.y0) / 2
            left = first.x0
            right = first.x1
        else:
            center_y = 0.5
            left = 0.125
            right = 0.88
        if has_any_signal:
            lbl = self.figure.text(
                left / 2, center_y, "Signal (V)",
                rotation='vertical', va='center', ha='center', fontsize=12
            )
            self._figure_labels.append(lbl)
        if has_any_current:
            lbl = self.figure.text(
                right + (1 - right) / 2, center_y, "Current (\u00b5A)",
                rotation='vertical', va='center', ha='center', fontsize=12
            )
            self._figure_labels.append(lbl)

        if page_wells:
            self._active_well = page_wells[0]
        else:
            self._active_well = None

        # Restore saved limits if auto-scale is off
        if not self.auto_scale_x and self._saved_xlim is not None:
            for sp in self.subplots:
                sp['ax'].set_xlim(self._saved_xlim)
        if not self.auto_scale_y and self._saved_ylims:
            for i, sp in enumerate(self.subplots):
                if i < len(self._saved_ylims):
                    sp['ax'].set_ylim(self._saved_ylims[i])
                if i < len(self._saved_ylims2):
                    sp['ax2'].set_ylim(self._saved_ylims2[i])

        self._apply_is_filter()
        self._draw_peak_markers()
        self._draw_esd_calls()
        self._populate_table_and_is()

        self.canvas.draw()

        try:
            self.toolbar._nav_stack = [(self.toolbar._views(), self.toolbar._positions())]
        except Exception:
            pass

        if page_wells:
            self._highlight_well(page_wells[0])

        self.status_label.setText(f"Displaying {', '.join(page_wells)}")

    def _redraw_peaks_only(self, clicked_well):
        self._ensure_well_detected(clicked_well)
        self._apply_is_filter()
        self._draw_peak_markers()
        self._populate_table_and_is()
        self.canvas.draw()

    def _update_esd_caller_combo(self):
        self._esd_caller_combo.blockSignals(True)
        self._esd_caller_combo.clear()
        self._esd_caller_combo.addItem("Base Calls: None")
        for name, subdir in self._esd_callers:
            display = esd_caller_display_name(name)
            self._esd_caller_combo.addItem(display)
        self._esd_caller_combo.blockSignals(False)

    def _draw_esd_calls(self):
        display_caller = self._esd_caller_combo.currentText()
        if not display_caller or display_caller == "Base Calls: None":
            self._esd_seq_label.setVisible(False)
            return
        self._esd_seq_label.setVisible(True)
        # Resolve display name to raw subdirectory key
        raw_caller = self._esd_display_to_raw.get(display_caller, display_caller)
        for sp in self.subplots:
            well = sp['well']
            if well is None:
                continue
            by_caller = self._esd_data.get(well, {})
            esd = by_caller.get(raw_caller)
            if esd is None:
                continue
            seq = esd.get('sequence', '')
            positions = esd.get('peak_positions')
            quality = esd.get('quality_scores')
            if not seq or positions is None:
                continue
            n = min(len(seq), len(positions))
            if quality is not None:
                n = min(n, len(quality))
            ax = sp['ax']
            ylim = ax.get_ylim()
            y_range = ylim[1] - ylim[0]
            y_pos = ylim[1] - 0.05 * y_range  # near top
            for i in range(n):
                pos = int(positions[i])
                base = seq[i]
                q = quality[i] if quality is not None else 0
                if q >= 60:
                    color = '#1a8a1a'
                elif q >= 20:
                    color = '#b0a000'
                else:
                    color = '#cc3333'
                ax.text(pos, y_pos, base, fontsize=6, color=color,
                        ha='center', va='top', fontfamily='monospace',
                        weight='bold')
            # Update sequence display
            self._update_esd_sequence(seq, positions, quality)

    def _update_esd_sequence(self, seq, positions, quality):
        if not hasattr(self, '_esd_seq_label') or self._esd_seq_label is None:
            return
        lines = []
        n = len(seq) if quality is None else min(len(seq), len(quality))
        chunk_size = 100
        for start in range(0, n, chunk_size):
            end = min(start + chunk_size, n)
            chunk_seq = seq[start:end]
            if quality is not None:
                chunk_qual = quality[start:end]
                qual_str = ''.join(
                    ' ' if q is None else ('*' if q >= 60 else (':' if q >= 20 else '.'))
                    for q in chunk_qual
                )
                lines.append(f"{start+1:4d}  {chunk_seq}")
                lines.append(f"        {qual_str}")
            else:
                lines.append(f"{start+1:4d}  {chunk_seq}")
        self._esd_seq_label.setText('\n'.join(lines))

    def _draw_peak_markers(self):
        for line in self._peak_marker_lines:
            try:
                line.remove()
            except Exception:
                pass
        self._peak_marker_lines = []

        for sp in self.subplots:
            well = sp['well']
            if well is None:
                continue
            wd = self._well_data.get(well)
            if wd is None:
                continue
            peaks = wd['peaks']
            if len(peaks) == 0:
                continue
            scan_values = wd['scan_values']
            channel_data = wd['channel_data']
            peak_channels = wd['peak_channels']

            for ch in sorted(
                set(peak_channels),
                key=lambda x: int(str(x).replace('Channel', '') or '0')
            ):
                mask = [pc == ch for pc in peak_channels]
                ch_peaks = peaks[mask]
                if ch in channel_data:
                    y = channel_data[ch]
                    y_range = y.max() - y.min()
                    offset = y_range * 0.03 if y_range > 0 else 1
                    color = self.channel_colors.get(ch, {}).get('active')
                    line, = sp['ax'].plot(
                        scan_values[ch_peaks], y[ch_peaks] + offset,
                        'o', markersize=3, color=color
                    )
                    self._peak_marker_lines.append(line)

    # ------------------------------------------------------------------
    # Table / IS / Summary
    # ------------------------------------------------------------------

    def _populate_table_and_is(self):
        all_rows = []
        for well, wd in self._well_data.items():
            if well not in self.all_data:
                continue
            all_rows.extend(self.detector.build_peak_rows(well, wd))

        self.peak_table.blockSignals(True)
        self.peak_table.setRowCount(len(all_rows))
        best_snr = 0
        noise_display = 0
        for i, row in enumerate(all_rows):
            self.peak_table.setItem(i, 0, QTableWidgetItem(row['well']))
            self.peak_table.setItem(i, 1, QTableWidgetItem(row['channel']))
            self.peak_table.setItem(i, 2, QTableWidgetItem(str(i + 1)))
            self.peak_table.setItem(i, 3, QTableWidgetItem(f'{row["scan"]:.0f}'))
            self.peak_table.setItem(i, 4, QTableWidgetItem(f'{row["height"]:.0f}'))
            self.peak_table.setItem(i, 5, QTableWidgetItem(f'{row["width"]:.1f}'))
            self.peak_table.setItem(i, 6, QTableWidgetItem(f'{row["baseline"]:.0f}'))
            self.peak_table.setItem(i, 7, QTableWidgetItem(f'{row["area"]:.0f}'))
            snr = row['height'] / row['noise']
            if snr > best_snr:
                best_snr = snr
                noise_display = row['noise']

        self.peak_table.blockSignals(False)

        if best_snr > 0:
            self.snr_label.setText(f"Noise: {noise_display:.1f}    Best SNR: {best_snr:.1f}")
        else:
            self.snr_label.setText("Noise: -    Best SNR: -")

        # IS combo boxes (always show all channels so user can pick the IS channel)
        self.is_channel_combo.blockSignals(True)
        self.is_peak_combo.blockSignals(True)
        self.is_channel_combo.clear()
        self.is_peak_combo.clear()
        self.is_channel_combo.addItem(IS_NONE_OPTION)
        for ch in PEAK_CHANNEL_NAMES:
            self.is_channel_combo.addItem(ch)
        if self._is_channel:
            self.is_channel_combo.setCurrentText(self._is_channel)
        else:
            self.is_channel_combo.setCurrentText('Channel3')
            self._is_channel = 'Channel3'
        ch = self.is_channel_combo.currentText()
        if ch and ch != IS_NONE_OPTION:
            count = sum(1 for row in all_rows if row['channel'] == ch)
            count = min(count, 30)
            for i in range(1, count + 1):
                self.is_peak_combo.addItem(str(i))
            prev = getattr(self, '_prev_is_peak_num', None)
            if self._is_peak_num is not None and self._is_peak_num <= count:
                self.is_peak_combo.setCurrentText(str(self._is_peak_num))
            elif prev is not None and prev <= count:
                self.is_peak_combo.setCurrentText(str(prev))
            else:
                default_peak = min(4, count)
                self.is_peak_combo.setCurrentText(str(default_peak))
        self.is_channel_combo.blockSignals(False)
        self.is_peak_combo.blockSignals(False)
        if self._is_peak_num is None and self.is_peak_combo.count() > 0:
            self._is_peak_num = int(self.is_peak_combo.currentText())
            self._mark_dirty_and_update()
            return
        self._sync_is_values()

    def _find_is_area(self):
        """Find IS area by scanning table rows for the selected channel/peak."""
        ch = self.is_channel_combo.currentText() if self.is_channel_combo.count() > 0 else None
        if ch is None or ch == IS_NONE_OPTION:
            return None
        peak_num = self.is_peak_combo.currentText() if self.is_peak_combo.count() > 0 else None
        if peak_num is None:
            return None
        target = int(peak_num)
        nth = 0
        for i in range(self.peak_table.rowCount()):
            item_ch = self.peak_table.item(i, 1)
            if item_ch is not None and item_ch.text() == ch:
                nth += 1
                if nth == target:
                    item_area = self.peak_table.item(i, 7)
                    if item_area is not None:
                        try:
                            return float(item_area.text())
                        except ValueError:
                            return None
        return None

    def _sync_is_values(self):
        ch = self.is_channel_combo.currentText() if self.is_channel_combo.count() > 0 else None
        pk = self.is_peak_combo.currentText() if self.is_peak_combo.count() > 0 else None
        self._update_summary()

    def _on_detection_changed(self):
        mode = self.detection_combo.currentText()
        if mode == "Deep Learning" and not isinstance(self.detector, CnnPeakDetector):
            self.detector = CnnPeakDetector()
            self._mark_dirty_and_update()
        elif mode == "Classic" and not isinstance(self.detector, PeakDetector):
            self.detector = PeakDetector()
            self._mark_dirty_and_update()

    def _on_is_channel_changed(self):
        self._prev_is_peak_num = self._is_peak_num
        text = self.is_channel_combo.currentText()
        self._is_channel = text if text and text != IS_NONE_OPTION else None
        self._is_peak_num = None
        self._mark_dirty_and_update()
        # _populate_table_and_is handles combo population including prev_peak_num restoration

    def _on_is_peak_changed(self):
        new_val = int(self.is_peak_combo.currentText()) if self.is_peak_combo.count() > 0 else None
        if new_val == self._is_peak_num:
            return
        self._is_peak_num = new_val
        self._sync_is_values()
        self._mark_dirty_and_update()

    def _update_summary(self):
        is_area = self._find_is_area()
        if is_area is None:
            is_area = 0
        sample_area = 0
        for i in range(self.peak_table.rowCount()):
            item = self.peak_table.item(i, 7)
            if item is not None:
                try:
                    sample_area += float(item.text())
                except ValueError:
                    pass
        ratio = sample_area / is_area if is_area != 0 else 0
        self.summary_label.setText(
            f"IS Area: {is_area:.0f}    "
            f"Sample Area: {sample_area:.0f}    "
            f"Area/IS: {ratio:.3f}"
        )

    def _on_table_edited(self):
        self._update_summary()

    # ------------------------------------------------------------------
    # Click and peak editing
    # ------------------------------------------------------------------

    def on_click(self, event):
        if event.inaxes is None:
            return
        if not self._select_peaks_btn.isChecked() and self.toolbar.mode != '':
            return

        clicked_well = None
        for sp in self.subplots:
            if sp['ax'] == event.inaxes or sp['ax2'] == event.inaxes:
                clicked_well = sp['well']
                break
        if clicked_well is None:
            return

        wd = self._well_data.get(clicked_well)
        if wd is None:
            return

        scan_values = wd['scan_values']
        channel_data = wd['channel_data']
        peaks = wd['peaks']

        x = event.xdata
        idx = int(np.argmin(np.abs(scan_values - x)))

        # Try to delete nearest peak
        if len(peaks) > 0:
            distances = np.abs(peaks.astype(float) - idx)
            closest_peak_pos = int(np.argmin(distances))
            if distances[closest_peak_pos] < CLICK_TOLERANCE:
                peak_idx_to_delete = int(peaks[closest_peak_pos])
                deleted = self._deleted_peaks.setdefault(clicked_well, set())
                if peak_idx_to_delete not in deleted:
                    self._undo_manager.push(('delete_peak', clicked_well, peak_idx_to_delete))
                deleted.add(peak_idx_to_delete)
                self._well_data[clicked_well] = None  # force re-detect
                self._dirty_wells.add(clicked_well)
                self._redraw_peaks_only(clicked_well)
                return

        # Add new peak
        if not np.any(peaks == idx):
            best_ch = None
            best_y = -np.inf
            for ch, y in channel_data.items():
                if self.channel_buttons[ch].isChecked():
                    if y[idx] > best_y:
                        best_y = y[idx]
                        best_ch = ch
            if best_ch is not None:
                manual = self._manual_peaks.setdefault(clicked_well, [])
                if not any(m[0] == idx for m in manual):
                    self._undo_manager.push(('add_peak', clicked_well, idx, best_ch))
                manual.append((idx, best_ch))
                self._well_data[clicked_well] = None
                self._dirty_wells.add(clicked_well)
                self._redraw_peaks_only(clicked_well)

    def _delete_selected_or_nearest_peak(self):
        """Delete selected table row, or fall back to nearest peak on plot."""
        sel = self.peak_table.selectedItems()
        if sel:
            row = sel[0].row()
            self._delete_peak_from_table(row)
        else:
            self._delete_nearest_peak()

    def _delete_nearest_peak(self):
        if not self._active_well:
            return
        wd = self._well_data.get(self._active_well)
        if wd is None or len(wd['peaks']) == 0:
            return

        scan_values = wd['scan_values']
        peaks = wd['peaks']

        try:
            widget_pos = self.canvas.mapFromGlobal(QCursor.pos())
            h = self.canvas.height()
            fig_pt = (widget_pos.x(), h - widget_pos.y())
        except Exception:
            return

        target_well = None
        for sp in self.subplots:
            well = sp['well']
            if well is None:
                continue
            bbox = sp['ax'].get_window_extent()
            if bbox.contains(widget_pos.x(), widget_pos.y()):
                target_well = well
                break

        if target_well is None:
            return

        wd = self._well_data.get(target_well)
        if wd is None or len(wd['peaks']) == 0:
            return

        inv = None
        for sp in self.subplots:
            if sp['well'] == target_well:
                inv = sp['ax']
                break
        if inv is None:
            return
        try:
            inv_t = inv.transData.inverted()
            data_pt = inv_t.transform(fig_pt)
            x = data_pt[0]
        except Exception:
            return

        scan_values = wd['scan_values']
        peaks = wd['peaks']
        distances = np.abs(scan_values[peaks.astype(int)] - x)
        closest = int(np.argmin(distances))
        if distances[closest] < CLICK_TOLERANCE:
            peak_idx_to_delete = int(peaks[closest])
            deleted = self._deleted_peaks.setdefault(target_well, set())
            if peak_idx_to_delete not in deleted:
                self._undo_manager.push(('delete_peak', target_well, peak_idx_to_delete))
            deleted.add(peak_idx_to_delete)
            self._well_data[target_well] = None
            self._dirty_wells.add(target_well)
            self.update_plot()

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------

    def _undo(self):
        action = self._undo_manager.undo()
        if action is None:
            return
        self._apply_undo_action(action)
        self.update_plot()

    def _redo(self):
        action = self._undo_manager.redo()
        if action is None:
            return
        self._apply_redo_action(action)
        self.update_plot()

    def _apply_undo_action(self, action):
        kind = action[0]
        well = action[1]
        if kind == 'delete_peak':
            peak_idx = action[2]
            deleted = self._deleted_peaks.get(well, set())
            deleted.discard(peak_idx)
        elif kind == 'add_peak':
            idx = action[2]
            _ch = action[3]
            manual = self._manual_peaks.get(well, [])
            self._manual_peaks[well] = [m for m in manual if m[0] != idx]
        self._well_data[well] = None
        self._dirty_wells.add(well)

    def _apply_redo_action(self, action):
        kind = action[0]
        well = action[1]
        if kind == 'delete_peak':
            peak_idx = action[2]
            self._deleted_peaks.setdefault(well, set()).add(peak_idx)
        elif kind == 'add_peak':
            idx = action[2]
            ch = action[3]
            self._manual_peaks.setdefault(well, []).append((idx, ch))
        self._well_data[well] = None
        self._dirty_wells.add(well)

    # ------------------------------------------------------------------
    # Table context menu
    # ------------------------------------------------------------------

    def _table_context_menu(self, pos):
        menu = QMenu()
        delete_action = menu.addAction("Delete Peak")
        add_action = menu.addAction("Add Peak")
        label_action = menu.addAction("Label Peak")
        action = menu.exec_(self.peak_table.viewport().mapToGlobal(pos))
        if action == delete_action:
            row = self.peak_table.rowAt(pos.y())
            if row >= 0:
                self._delete_peak_from_table(row)
        elif action == add_action:
            self._add_peak_dialog()
        elif action == label_action:
            row = self.peak_table.rowAt(pos.y())
            if row >= 0:
                self._label_peak_from_table(row)

    def _delete_peak_from_table(self, row):
        if row < 0:
            return
        well_item = self.peak_table.item(row, 0)
        scan_item = self.peak_table.item(row, 3)
        if well_item is None or scan_item is None:
            return
        well = well_item.text()
        scan_val = int(float(scan_item.text()))
        wd = self._well_data.get(well)
        if wd is None:
            return
        peaks = wd['peaks']
        scan_values = wd['scan_values']
        for p in peaks:
            if abs(scan_values[p] - scan_val) < 2:
                deleted = self._deleted_peaks.setdefault(well, set())
                if p not in deleted:
                    self._undo_manager.push(('delete_peak', well, int(p)))
                deleted.add(int(p))
                self._well_data[well] = None
                self._dirty_wells.add(well)
                self.update_plot()
                return

    def _add_peak_dialog(self):
        if self._active_well is None:
            return
        wd = self._well_data.get(self._active_well)
        if wd is None:
            return
        scan_values = wd['scan_values']
        default_scan = int(scan_values[len(scan_values) // 2])
        scan, ok = QInputDialog.getInt(
            self, "Add Peak", "Enter scan number:",
            default_scan, 0, int(scan_values[-1])
        )
        if not ok:
            return
        idx = int(np.argmin(np.abs(scan_values - scan)))
        if np.any(wd['peaks'] == idx):
            return
        best_ch = None
        best_y = -np.inf
        for ch, y in wd['channel_data'].items():
            if self.channel_buttons[ch].isChecked():
                if y[idx] > best_y:
                    best_y = y[idx]
                    best_ch = ch
        if best_ch is None:
            return
        self._undo_manager.push(('add_peak', self._active_well, idx, best_ch))
        self._manual_peaks.setdefault(self._active_well, []).append((idx, best_ch))
        self._well_data[self._active_well] = None
        self._dirty_wells.add(self._active_well)
        self.update_plot()

    def _label_peak_from_table(self, row):
        """Prompt user for a label and store it in training_data."""
        if row < 0:
            return
        table = self.peak_table
        well_item = table.item(row, 0)
        channel_item = table.item(row, 1)
        peak_item = table.item(row, 2)
        scan_item = table.item(row, 3)
        height_item = table.item(row, 4)
        width_item = table.item(row, 5)
        area_item = table.item(row, 7)
        if any(x is None for x in [well_item, channel_item, peak_item, scan_item,
                                    height_item, width_item, area_item]):
            return

        label, ok = QInputDialog.getText(self, "Label Peak", "Enter label:")
        if not ok or not label.strip():
            return

        peak_data = {
            "well": well_item.text(),
            "channel": channel_item.text(),
            "peak": peak_item.text(),
            "scan": scan_item.text(),
            "height": height_item.text(),
            "width": width_item.text(),
            "area": area_item.text(),
            "label": label.strip(),
        }
        self.training_data.append(peak_data)

    # ------------------------------------------------------------------
    # Baseline
    # ------------------------------------------------------------------

    def on_baseline_changed(self):
        method = self.baseline_combo.currentText()
        if method in ("None", "First 200"):
            self.bl_spin.setEnabled(False)
            self.bl_label.setEnabled(False)
        else:
            self.bl_spin.setEnabled(True)
            self.bl_label.setEnabled(True)
            self.bl_spin.blockSignals(True)
            if method == "Rolling Min":
                self.bl_label.setText("Window:")
                old = self.bl_spin.value()
                self.bl_spin.setRange(10, 5000)
                if old < 10 or old > 5000:
                    self.bl_spin.setValue(500)
                else:
                    self.bl_spin.setValue(old)
            elif method == "ALS":
                self.bl_label.setText("Lambda (10^x):")
                old = self.bl_spin.value()
                self.bl_spin.setRange(2, 9)
                if old < 2 or old > 9:
                    self.bl_spin.setValue(5)
                else:
                    self.bl_spin.setValue(old)
            self.bl_spin.blockSignals(False)
        self._mark_dirty_and_update()

    def _activate_peak_select(self):
        if self._select_peaks_btn.isChecked():
            if self.toolbar.mode == 'pan/zoom':
                self.toolbar.pan()
            elif self.toolbar.mode == 'zoom rect':
                self.toolbar.zoom()
        self.canvas.setFocus()

    # ------------------------------------------------------------------
    # IS reference & peak clearing
    # ------------------------------------------------------------------

    def _clear_all_peaks(self):
        """Remove all detected peaks for the active well."""
        well = self._active_well
        if well is None:
            return
        # Delete all auto-detected peaks in this well
        wd = self._well_data.get(well)
        if wd is None:
            return
        n_peaks = len(wd.get('peaks', []))
        if n_peaks == 0:
            QMessageBox.information(self, "Clear Peaks", "No peaks to clear.")
            return

        # Mark all current scan indices as deleted
        deleted = self._deleted_peaks.setdefault(well, set())
        for idx in range(n_peaks):
            deleted.add(idx)
        # Also clear manual peaks for this well
        self._manual_peaks[well] = []
        self.update_plot()

    def _save_is_reference(self):
        """Save IS reference positions for the whole plate to is_ref_positions.json.

        Tries inter-well consistency across all wells first (accurate per-plate).
        Falls back to the current well's Ch3 peaks.
        """
        from run_is_genotyping import find_consistent_is_refs

        ref_positions = None
        folder_path = self._current_folder
        if folder_path and os.path.isdir(folder_path):
            refs = find_consistent_is_refs(folder_path)
            if refs is not None:
                ref_positions = [r[0] for r in refs]

        if ref_positions is None:
            # Fallback: current well's Ch3 peaks
            well = self._active_well
            if well is None:
                QMessageBox.warning(self, "Save IS Ref.", "No active well and no consistent refs found.")
                return
            manual = self._manual_peaks.get(well, [])
            auto_peaks = []
            wd = self._well_data.get(well)
            if wd is not None:
                for i, scan in enumerate(wd.get('peaks', [])):
                    ch = wd.get('peak_channels', [''])[i] if i < len(wd.get('peak_channels', [])) else ''
                    if scan not in {m[0] for m in manual}:
                        auto_peaks.append((scan, ch))
            deleted = self._deleted_peaks.get(well, set())
            auto_peaks = [(s, c) for s, c in auto_peaks if s not in deleted]
            ch3_peaks = []
            for scan, ch in manual:
                if ch == 2 or ch == 'Channel3':
                    ch3_peaks.append(scan)
            for scan, ch in auto_peaks:
                if ch == 2 or ch == 'Channel3':
                    ch3_peaks.append(scan)
            if len(ch3_peaks) < 1:
                QMessageBox.warning(self, "Save IS Ref.",
                                    "No Channel3 (IS) peaks found.\n"
                                    "Add IS peaks on Ch3 first.")
                return
            ref_positions = sorted(ch3_peaks)

        # Save to is_ref_positions.json keyed by gene name
        folder_name = os.path.basename(folder_path) if folder_path else ''
        gene_key = folder_name
        # Try to extract a concise gene key (e.g. "ABCC2" from "OY_ABCC2_N1_160910Run01")
        for prefix in ('OY_', 'oy_'):
            if gene_key.startswith(prefix):
                parts = gene_key[len(prefix):].split('_')
                if parts:
                    gene_key = parts[0]
                    break

        refs_json_path = os.path.join(os.path.dirname(__file__), 'is_ref_positions.json')
        import json as _json
        existing = {}
        if os.path.exists(refs_json_path):
            with open(refs_json_path) as _f:
                existing = _json.load(_f)
        existing[gene_key] = ref_positions
        with open(refs_json_path, 'w') as _f:
            _json.dump(existing, _f, indent=2)

        self._is_ref_scans = ref_positions
        self.is_ref_label.setText(f"IS ref: {len(ref_positions)} peaks at "
                                   f"{','.join(str(s) for s in ref_positions)}")
        QMessageBox.information(self, "Save IS Ref.",
                                f"Saved {len(ref_positions)} IS ref positions\n"
                                f"({', '.join(str(s) for s in ref_positions)})\n"
                                f"to is_ref_positions.json for gene '{gene_key}'.")

    def _train_is_classifier(self):
        """Train a Random Forest classifier using ALL user-marked Ch3 peaks across wells."""
        n_expected = self.is_n_spin.value()

        # Collect training data from all wells with exactly n_expected manual Ch3 peaks
        X_train, y_train = [], []
        n_pos_wells = 0
        training_wells = []

        for well in self._get_all_wells():
            wd = self._well_data.get(well)
            if wd is None:
                continue
            df = self._get_well_trace(well)
            if df is None:
                continue
            ch3 = df['Channel3'].values.astype(float)
            ch2 = df['Channel2'].values.astype(float)
            noise = np.std(ch3[:200]) if len(ch3) > 200 else 1.0

            # Get manual Ch3 peaks for this well
            manual = self._manual_peaks.get(well, [])
            manual_ch3 = sorted([m[0] for m in manual if m[1] == 2 or m[1] == 'Channel3'])

            # Also include peaks from well_data that are Ch3 and not deleted
            auto_ch3 = []
            if wd.get('peaks') is not None:
                deleted = self._deleted_peaks.get(well, set())
                for i, s in enumerate(wd['peaks']):
                    ch_name = wd.get('peak_channels', [''])[i] if i < len(wd.get('peak_channels', [])) else ''
                    if (ch_name == 2 or ch_name == 'Channel3') and i not in deleted:
                        auto_ch3.append(int(s))

            all_ch3 = sorted(set(manual_ch3 + auto_ch3))

            if len(all_ch3) != n_expected:
                continue

            training_wells.append(well)
            for p in all_ch3:
                feats = self._is_peak_features(p, ch3, ch2, noise)
                X_train.append(feats)
                y_train.append(1)
            n_pos_wells += 1

            # Negative: non-IS local maxima in this well
            all_peaks = self._find_ch3_local_maxima(ch3, noise * 3)
            neg_count = 0
            pos_set = set(all_ch3)
            for p in all_peaks:
                if p in pos_set:
                    continue
                if neg_count >= n_expected * 2:
                    break
                feats = self._is_peak_features(p, ch3, ch2, noise)
                X_train.append(feats)
                y_train.append(0)
                neg_count += 1

        if n_pos_wells < 1 or len(X_train) < 10:
            QMessageBox.warning(self, "Train IS Model",
                                f"Need at least 1 well with exactly {n_expected}"
                                f" Ch3 peaks marked.\n"
                                f"Found {n_pos_wells} suitable wells.")
            return None, 0

        try:
            from sklearn.ensemble import RandomForestClassifier
        except ImportError:
            return None, 0

        clf = RandomForestClassifier(n_estimators=300, max_depth=8,
                                      class_weight='balanced', random_state=42)
        clf.fit(np.array(X_train), np.array(y_train))
        return clf, n_pos_wells

    def _is_peak_features(self, p, ch3, ch2, noise):
        """Feature vector for IS peak classification at scan position p."""
        w = 8
        start = max(0, p - w)
        end = min(len(ch3), p + w + 1)
        window = ch3[start:end]
        window_ch2 = ch2[start:end]

        peak_h = ch3[p]
        ch2_h = ch2[p]
        ratio = peak_h / (ch2_h + 1.0)
        local_min = window.min()
        prominence = peak_h - local_min
        local_std = window.std()
        local_max_ch2 = window_ch2.max()

        # Window samples at fixed offsets from peak
        offsets = [-7, -5, -3, -1, 0, 1, 3, 5, 7]
        samples = [ch3[max(0, min(len(ch3)-1, p+o))] for o in offsets]

        return np.array([
            peak_h / (noise + 1.0),        # SNR
            ratio,                          # Ch3/Ch2 ratio
            prominence / (noise + 1.0),     # prominence / noise
            local_std / (noise + 1.0),      # local std / noise
            peak_h / (local_max_ch2 + 1.0), # peak / max Ch2 in window
            *[s / (noise + 1.0) for s in samples],  # signal at offsets
        ])

    def _find_ch3_local_maxima(self, ch3, threshold):
        """Find all local maxima in Ch3 above threshold."""
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(ch3, height=threshold, distance=3, width=1)
        return peaks

    def _find_is_peaks(self, silent=False):
        """Find IS peaks in all loaded wells using saved manual refs or ML.

        Args:
            silent: If True, suppress success message box.
        """
        wells = self._get_all_wells()
        if not wells:
            QMessageBox.warning(self, "Find IS Peaks", "No wells loaded.")
            return

        from run_is_genotyping import find_is_peaks_for_well, find_consistent_is_refs

        # Try per-plate inter-well consistency FIRST (IS peak positions vary between plates)
        manual_refs = None
        folder_path = self._current_folder
        if folder_path and os.path.isdir(folder_path):
            refs = find_consistent_is_refs(folder_path)
            if refs is not None:
                manual_refs = [r[0] for r in refs]

        if manual_refs is None:
            # Fallback: saved manual ref positions
            refs_json_path = os.path.join(os.path.dirname(__file__), 'is_ref_positions.json')
            folder_name = os.path.basename(folder_path) if folder_path else ''
            if os.path.exists(refs_json_path):
                import json as _json
                with open(refs_json_path) as _f:
                    _all_refs = _json.load(_f)
                for key in sorted(_all_refs.keys(), key=len, reverse=True):
                    if key in folder_name or folder_name in key:
                        manual_refs = _all_refs[key]
                        break

        if manual_refs is not None:
            # Force re-detect all wells with current settings (scan range, height, etc.)
            self._sync_detector_params()
            self._dirty_wells.update(self._well_data.keys())
            from scipy.signal import find_peaks as _find_ch3_peaks
            n_found = 0
            progress = QProgressDialog("Finding IS peaks...", "Cancel", 0, len(wells), self)
            progress.setWindowTitle("Find IS Peaks")
            progress.setWindowModality(Qt.WindowModal)
            for wi, well in enumerate(wells):
                if progress.wasCanceled():
                    break
                progress.setValue(wi)
                QApplication.processEvents()
                self._ensure_well_detected(well)
                wd = self._well_data.get(well)
                if wd is None or not isinstance(wd, dict):
                    continue
                df = self._get_well_trace(well)
                if df is None:
                    continue
                ch3 = df['Channel3'].values.astype(float)
                noise = np.std(ch3[:200]) if len(ch3) > 200 else max(np.std(ch3), 1e-10)
                # Detect peaks on raw Ch3 (no Savgol) to find IS peaks detector may have merged
                raw_ch3_peaks, _ = _find_ch3_peaks(ch3, height=max(50, 3 * noise),
                                                    prominence=noise, distance=3, width=1)
                raw_ch3_peaks = set(int(p) for p in raw_ch3_peaks)
                # Combine with detector's Ch3 peaks
                pchs = wd.get('peak_channels', [])
                existing = set(int(p) for p, pc in zip(wd.get('peaks', []), pchs) if pc == 'Channel3')
                all_ch3 = raw_ch3_peaks | existing
                if not all_ch3:
                    continue
                assigned = set()
                for rp in manual_refs:
                    # Greedy: find nearest unmatched peak within 150 scans
                    best_pos = None
                    best_dist = 151
                    for ap in all_ch3:
                        if ap in assigned:
                            continue
                        d = abs(ap - rp)
                        if d < best_dist:
                            best_dist = d
                            best_pos = ap
                    if best_pos is None:
                        continue
                    assigned.add(best_pos)
                    if best_pos not in existing:
                        wd['peaks'] = np.append(wd['peaks'], best_pos)
                        wd.setdefault('peak_channels', []).append('Channel3')
                        wd.setdefault('peak_heights', []).append(float(ch3[best_pos]) if ch3 is not None else 0)
                        wd['peak_lefts'] = np.append(wd.get('peak_lefts', np.array([])), max(0, best_pos - 2))
                        wd['peak_rights'] = np.append(wd.get('peak_rights', np.array([])), best_pos + 2)
                n_found += 1
            progress.close()
            self.update_plot()
            QApplication.processEvents()
            self.status_label.setText("")
            if not silent:
                QMessageBox.information(self, "Find IS Peaks",
                                        f"Found/matched IS peaks in {n_found}/{len(wells)} wells\n"
                                        f"using saved reference positions {manual_refs}.")
            return

        # Fall back to ML trained on manual marks
        self.status_label.setText("Training IS classifier...")
        QApplication.processEvents()
        clf, n_train_wells = self._train_is_classifier()
        if clf is None:
            self.status_label.setText("")
            return

        n_expected = self.is_n_spin.value()
        # Compute reference spacing from the first well that has exactly n_expected peaks
        ref_spacing = [50]
        for well in self._get_all_wells():
            manual = self._manual_peaks.get(well, [])
            ch3_peaks = sorted([m[0] for m in manual if m[1] == 2 or m[1] == 'Channel3'])
            if len(ch3_peaks) >= n_expected:
                ref_spacing = np.diff(ch3_peaks[:n_expected])
                break
        n_found = 0

        for well in wells:
            df = self._get_well_trace(well)
            if df is None:
                continue
            ch3 = df['Channel3'].values.astype(float)
            ch2 = df['Channel2'].values.astype(float)
            noise = np.std(ch3[:200]) if len(ch3) > 200 else 1.0

            wd = self._well_data.get(well)
            if wd is None or not isinstance(wd, dict):
                self._well_data[well] = None
                self._dirty_wells.add(well)
                self._ensure_well_detected(well)
                wd = self._well_data.get(well)
                if wd is None or not isinstance(wd, dict):
                    continue

            # Score every candidate peak with the classifier
            candidates = self._find_ch3_local_maxima(ch3, noise * 3)
            if len(candidates) == 0:
                continue

            X_cand = np.array([self._is_peak_features(p, ch3, ch2, noise)
                                for p in candidates])
            scores = clf.predict_proba(X_cand)
            if scores.shape[1] < 2:
                continue
            pos_scores = scores[:, 1]

            # Pick best N peaks matching expected pattern
            scored = sorted(zip(candidates, pos_scores), key=lambda x: -x[1])

            # Use pattern matching: find the best set of n_expected peaks
            # that have similar spacing to reference
            best_set = self._match_is_pattern(scored, n_expected, ref_spacing, ch3, noise)

            if not best_set:
                continue

            existing_peaks = set(wd.get('peaks', []))
            n_added = 0
            for s in best_set:
                if s not in existing_peaks:
                    wd['peaks'] = np.append(wd['peaks'], s)
                    wd.setdefault('peak_channels', []).append('Channel3')
                    wd.setdefault('peak_heights', []).append(float(ch3[s]))
                    wd['peak_lefts'] = np.append(wd['peak_lefts'], max(0, s - 2))
                    wd['peak_rights'] = np.append(wd['peak_rights'], s + 2)
                    n_added += 1
            if n_added > 0:
                n_found += 1

        self.update_plot()
        self.status_label.setText("")
        if not silent:
            QMessageBox.information(self, "Find IS Peaks",
                                    f"ML trained on {n_expected} IS peaks from {n_train_wells} wells.\n"
                                    f"Found IS peaks in {n_found}/{len(wells)} wells.")

    def _save_is_model(self):
        """Train and save the IS RF model + manual peak positions + reference spacing.
        
        Accumulates training data across multiple plates: loads existing saved peaks,
        merges with current plate's peaks, then retrains.
        """
        if not self._get_all_wells():
            QMessageBox.warning(self, "Save IS Model", "No wells loaded.")
            return

        import joblib, json
        base = os.path.join(os.path.dirname(__file__), 'is_model')
        current_folder = os.path.basename(self._current_folder) if self._current_folder else ''
        n_expected = self.is_n_spin.value()

        # --- Load existing accumulated peak data ---
        all_peaks = {}  # (folder, well) -> [scan_positions]
        csv_path = base + '_peaks.csv'
        if os.path.exists(csv_path):
            try:
                old_df = pd.read_csv(csv_path)
                cols = [c for c in old_df.columns if c.endswith('_scan')]
                for _, row in old_df.iterrows():
                    folder = row.get('folder', '')
                    well = row['well']
                    scans = sorted(int(row[c]) for c in cols if pd.notna(row[c]))
                    if scans:
                        all_peaks[(folder, well)] = scans
            except Exception:
                pass

        # --- Add current plate's peaks ---
        peak_data = {}
        for well in self._get_all_wells():
            manual = self._manual_peaks.get(well, [])
            ch3 = sorted([m[0] for m in manual if m[1] == 2 or m[1] == 'Channel3'])
            wd = self._well_data.get(well)
            if wd is not None and wd.get('peaks') is not None and len(wd['peaks']) > 0:
                deleted = self._deleted_peaks.get(well, set())
                for i, s in enumerate(wd['peaks']):
                    ch = wd.get('peak_channels', [''])[i] if i < len(wd.get('peak_channels', [])) else ''
                    if (ch == 2 or ch == 'Channel3') and i not in deleted:
                        s_val = int(s)
                        if s_val not in ch3:
                            ch3.append(s_val)
            ch3 = sorted(set(ch3))
            if len(ch3) > 0:
                peak_data[well] = ch3
                all_peaks[(current_folder, well)] = ch3

        if not all_peaks:
            QMessageBox.warning(self, "Save IS Model", "No IS peaks found.")
            return

        # --- Retrain on ALL accumulated wells ---
        X_train, y_train = [], []
        n_pos_wells = 0
        ref_spacing = [50]

        for (folder, well), scans in sorted(all_peaks.items()):
            # Try to find the .rsd file — prefer OY/{folder}/, then current folder, then scan OY/
            df = None
            if folder:
                folder_path = os.path.join(os.path.dirname(__file__), 'OY', folder)
                rsd_path = os.path.join(folder_path, f"{well}.rsd")
                txt_path = os.path.join(folder_path, f"{well}.txt")
                if os.path.exists(rsd_path):
                    from train_genotyping import parse_rsd
                    df = parse_rsd(rsd_path)
                elif os.path.exists(txt_path):
                    from peak_detector import load_trace_file
                    df = load_trace_file(txt_path)
            if df is None:
                # Search OY subdirs for this well's .rsd
                oy_dir = os.path.join(os.path.dirname(__file__), 'OY')
                if os.path.isdir(oy_dir):
                    for d in os.listdir(oy_dir):
                        dp = os.path.join(oy_dir, d)
                        if not os.path.isdir(dp):
                            continue
                        rp = os.path.join(dp, f"{well}.rsd")
                        if os.path.exists(rp):
                            from train_genotyping import parse_rsd
                            df = parse_rsd(rp)
                            break
            if df is None:
                continue

            ch3 = df['Channel3'].values.astype(float)
            ch2 = df['Channel2'].values.astype(float)
            noise = np.std(ch3[:200]) if len(ch3) > 200 else 1.0
            scans_sorted = sorted(scans)

            if len(scans_sorted) >= n_expected:
                # Compute reference spacing from first well with enough peaks
                if len(ref_spacing) == 1 and ref_spacing[0] == 50:
                    ref_spacing = [float(x) for x in np.diff(scans_sorted[:n_expected])]

            if len(scans_sorted) < int(n_expected * 0.5):
                continue

            # Positive examples
            for p in scans_sorted:
                feats = self._is_peak_features(p, ch3, ch2, noise)
                X_train.append(feats)
                y_train.append(1)
            n_pos_wells += 1

            # Negative examples
            all_peaks_pos = self._find_ch3_local_maxima(ch3, noise * 3)
            neg_count = 0
            pos_set = set(scans_sorted)
            for p in all_peaks_pos:
                if p in pos_set:
                    continue
                if neg_count >= n_expected * 2:
                    break
                feats = self._is_peak_features(p, ch3, ch2, noise)
                X_train.append(feats)
                y_train.append(0)
                neg_count += 1

        if n_pos_wells < 1 or len(X_train) < 10:
            QMessageBox.warning(self, "Save IS Model",
                                f"Could not retrain: only {n_pos_wells} usable wells, {len(X_train)} samples.")
            return

        try:
            from sklearn.ensemble import RandomForestClassifier
        except ImportError:
            QMessageBox.warning(self, "Save IS Model", "scikit-learn not available.")
            return
        clf = RandomForestClassifier(n_estimators=300, max_depth=8,
                                      class_weight='balanced', random_state=42)
        clf.fit(np.array(X_train), np.array(y_train))
        joblib.dump(clf, base + '.pkl')

        # --- Save accumulated peak CSV with folder column ---
        csv_rows = []
        for (folder, well), scans in sorted(all_peaks.items()):
            row = {'folder': folder, 'well': well}
            for i, s in enumerate(scans[:n_expected]):
                row[f'is_peak_{i+1}_scan'] = s
            csv_rows.append(row)
        if csv_rows:
            pd.DataFrame(csv_rows).to_csv(csv_path, index=False)

        # --- Save meta: all folders + ref spacing ---
        folders_used = sorted(set(f for (f, _) in all_peaks))
        meta = {
            'n_expected': n_expected,
            'ref_spacing': [float(x) for x in ref_spacing],
            'n_train_wells': n_pos_wells,
            'folders': folders_used,
            'n_total_wells': len(all_peaks),
        }
        with open(base + '_meta.json', 'w') as f:
            json.dump(meta, f, indent=2)

        QMessageBox.information(self, "Save IS Model",
                                f"IS model retrained on {n_pos_wells} wells from {len(folders_used)} plate(s).\n"
                                f"{n_expected} IS peaks expected, {len(all_peaks)} total wells saved.\n"
                                f"Peak data → {csv_path}")

    def _batch_is_detect(self):
        """Run IS detection on all matching fragment folders using inter-well consistency."""
        if not self._current_folder:
            QMessageBox.warning(self, "Batch IS",
                                "Load a folder first so we can derive the fragment prefix.")
            return
        base_name = os.path.basename(self._current_folder)
        prefix = '_'.join(base_name.split('_')[:4]) if base_name.startswith('OY_') else base_name.split('_Run')[0]

        oy_dir = os.path.join(os.path.dirname(__file__), 'OY')
        if not os.path.isdir(oy_dir):
            QMessageBox.warning(self, "Batch IS", f"OY folder not found at {oy_dir}")
            return
        matching = sorted(d for d in os.listdir(oy_dir)
                         if d.startswith(prefix) and os.path.isdir(os.path.join(oy_dir, d)))
        if not matching:
            QMessageBox.warning(self, "Batch IS",
                                f"No folders matching '{prefix}*' found in OY/")
            return
        reply = QMessageBox.question(self, "Batch IS",
                                     f"Process {len(matching)} folders matching '{prefix}*'?\n"
                                     + '\n'.join(matching[:10])
                                     + ('\n...' if len(matching) > 10 else ''),
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        from run_is_genotyping import find_consistent_is_refs, find_is_peaks_for_well

        # Try loading saved manual ref positions
        import json as _json
        manual_refs = None
        refs_json_path = os.path.join(os.path.dirname(__file__), 'is_ref_positions.json')
        if os.path.exists(refs_json_path):
            with open(refs_json_path) as _f:
                _all_refs = _json.load(_f)
            for key in sorted(_all_refs.keys(), key=len, reverse=True):
                if key in prefix or prefix in key:
                    manual_refs = _all_refs[key]
                    break

        self.status_label.setText("Batch IS detection running...")
        QApplication.processEvents()
        results = {}
        n_ok = 0
        for folder_name in matching:
            folder_path = os.path.join(oy_dir, folder_name)
            if manual_refs:
                ref_positions = manual_refs
            else:
                refs = find_consistent_is_refs(folder_path)
                if refs is None:
                    continue
                ref_positions = [r[0] for r in refs]
            rsd_files = sorted(glob.glob(os.path.join(folder_path, '*.rsd')))
            for rsd_path in rsd_files:
                well = os.path.splitext(os.path.basename(rsd_path))[0]
                try:
                    res = find_is_peaks_for_well(rsd_path, ref_positions)
                    if res:
                        results.setdefault(folder_name, {})[well] = [int(r[0]) if r else None for r in res]
                        n_ok += 1
                except Exception:
                    continue
            self.status_label.setText(f"Batch IS: {folder_name} done ({n_ok} wells matched)")
            QApplication.processEvents()

        out_path = os.path.join(os.path.dirname(__file__), f'is_peaks_{prefix}.csv')
        rows = []
        for folder_name, wells in sorted(results.items()):
            for well, scans in sorted(wells.items()):
                for i, s in enumerate(scans):
                    if s is not None:
                        rows.append({'folder': folder_name, 'well': well,
                                     f'is_peak_{i+1}_scan': s})
        if rows:
            pd.DataFrame(rows).to_csv(out_path, index=False)
            n_wells = sum(len(w) for w in results.values())
            QMessageBox.information(self, "Batch IS",
                                    f"Processed {len(matching)} folders.\n"
                                    f"Found IS peaks in {n_wells} wells.\n"
                                    f"Results saved to {out_path}")
        else:
            QMessageBox.warning(self, "Batch IS", "No IS peaks found in any folder.")
        self.status_label.setText("")

    def _train_genotyping(self):
        """Train genotyping model using Genotyping.xlsx ground truth."""
        import importlib, sys
        try:
            from train_genotyping import main as train_main
            self.status_label.setText("Training genotyping model...")
            QApplication.processEvents()
            train_main()
            self.status_label.setText("Genotyping model training complete.")
            QMessageBox.information(self, "Train Genotyping",
                                    "Genotyping model trained and saved to genotyping_model.pkl")
        except Exception as e:
            self.status_label.setText("")
            QMessageBox.critical(self, "Train Genotyping", f"Training failed:\n{e}")

    def _extract_simple_features(self, df, is_peaks):
        """Extract a compact feature set (30 features instead of 175)."""
        import numpy as np
        from scipy.stats import skew, kurtosis
        from scipy.signal import find_peaks

        feats = {}
        ch3 = df['Channel3'].values.astype(float)
        noise_ch3 = np.std(ch3[:200]) if len(ch3) > 200 else max(np.std(ch3), 1e-10)

        # IS peak features
        if is_peaks and len(is_peaks) >= 2:
            scans = sorted([s for s, _ in is_peaks])
            heights = [float(ch3[s]) if s < len(ch3) else 0.0 for s in scans]
            for i in range(min(4, len(scans))):
                feats[f'IS_{i+1}_scan'] = scans[i]
                feats[f'IS_{i+1}_hgt'] = heights[i]
            for i in range(len(scans), 4):
                feats[f'IS_{i+1}_scan'] = 0
                feats[f'IS_{i+1}_hgt'] = 0.0
            feats['IS_n'] = len(scans)
            feats['IS_spread'] = scans[-1] - scans[0]
            feats['IS_mean_hgt'] = float(np.mean(heights))
        else:
            for i in range(1, 5):
                feats[f'IS_{i}_scan'] = 0
                feats[f'IS_{i}_hgt'] = 0.0
            feats['IS_n'] = 0
            feats['IS_spread'] = 0
            feats['IS_mean_hgt'] = 0.0

        # Ch1 and Ch2 trace stats + strongest peak
        for ch_name in ('Channel1', 'Channel2'):
            y = df[ch_name].values.astype(float)
            feats[f'{ch_name}_mean'] = float(np.mean(y))
            feats[f'{ch_name}_std'] = float(np.std(y))
            feats[f'{ch_name}_max'] = float(np.max(y))
            feats[f'{ch_name}_min'] = float(np.min(y))
            feats[f'{ch_name}_energy'] = float(np.sum(y ** 2))

            noise = np.std(y[:200]) if len(y) > 200 else max(np.std(y), 1e-10)
            threshold = max(50, 3 * noise)
            try:
                p, props = find_peaks(y, height=threshold, prominence=threshold * 0.5,
                                      distance=5, width=1)
                if len(p) > 0:
                    h = props['peak_heights']
                    idx = int(p[np.argmax(h)])
                    feats[f'{ch_name}_max_peak_scan'] = idx
                    feats[f'{ch_name}_max_peak_hgt'] = float(np.max(h))
                    feats[f'{ch_name}_n_peaks'] = len(p)
                else:
                    feats[f'{ch_name}_max_peak_scan'] = 0
                    feats[f'{ch_name}_max_peak_hgt'] = 0.0
                    feats[f'{ch_name}_n_peaks'] = 0
            except Exception:
                feats[f'{ch_name}_max_peak_scan'] = 0
                feats[f'{ch_name}_max_peak_hgt'] = 0.0
                feats[f'{ch_name}_n_peaks'] = 0

        # Ch3 (IS) basic stats
        feats['Channel3_mean'] = float(np.mean(ch3))
        feats['Channel3_std'] = float(np.std(ch3))
        feats['Channel3_noise'] = float(noise_ch3)

        # IS/ch2 ratio features
        if is_peaks and len(is_peaks) >= 2:
            ch2 = df['Channel2'].values.astype(float)
            ratios = []
            for s, _ in is_peaks:
                si = int(s)
                if si < len(ch3) and si < len(ch2) and ch2[si] > 10:
                    ratios.append(ch3[si] / ch2[si])
            if ratios:
                feats['IS_Ch2_ratio_mean'] = float(np.mean(ratios))
                feats['IS_Ch2_ratio_min'] = float(np.min(ratios))
            else:
                feats['IS_Ch2_ratio_mean'] = 0.0
                feats['IS_Ch2_ratio_min'] = 0.0
        else:
            feats['IS_Ch2_ratio_mean'] = 0.0
            feats['IS_Ch2_ratio_min'] = 0.0

        return feats

    def _train_is_only(self):
        """Train using corrected IS peaks + Genotyping.xlsx ground truth.
        Uses compact features (~30) to avoid overfitting."""
        import joblib, os
        import numpy as np
        import pandas as pd
        from run_is_genotyping import parse_rsd
        from train_genotyping import SCRIPT_DIR, parse_genotyping_xlsx, normalize_plate_name

        folder = self._current_folder
        if not folder:
            QMessageBox.warning(self, "Train IS", "No folder loaded.")
            return
        folder_name = os.path.basename(folder)
        plate_name = normalize_plate_name(folder_name)

        xlsx_path = os.path.join(SCRIPT_DIR, 'Genotyping.xlsx')
        if os.path.exists(xlsx_path):
            all_plates = parse_genotyping_xlsx(xlsx_path)
        else:
            alt = '/media/tv/Data (ScanDisk)/Genotyping.xlsx'
            all_plates = parse_genotyping_xlsx(alt) if os.path.exists(alt) else {}
        plate_gt = all_plates.get(plate_name, {})
        if plate_gt:
            print(f"Train IS: loaded {len(plate_gt)} genotypes from Genotyping.xlsx for {plate_name}")

        X_list, y_list = [], []
        feature_cols = None

        for well in self._get_all_wells():
            wd = self._well_data.get(well)
            if wd is None:
                continue
            peaks = wd.get('peaks')
            pchs = wd.get('peak_channels', [])
            if peaks is None or len(peaks) < 2:
                continue
            ch3_scans = []
            for i, s in enumerate(peaks):
                ch = pchs[i] if i < len(pchs) else ''
                if ch == 'Channel3' or ch == 2:
                    ch3_scans.append(int(s))
            if len(ch3_scans) < 2:
                continue
            ch3_scans.sort()

            rsd_path = os.path.join(folder, f"{well}.rsd")
            if not os.path.exists(rsd_path):
                continue
            df = parse_rsd(rsd_path)
            if len(df) < 50:
                continue

            ch3 = df['Channel3'].values.astype(float)
            ispk = [(s, float(ch3[s])) for s in ch3_scans if s < len(ch3)]
            feats = self._extract_simple_features(df, is_peaks=ispk)
            if feature_cols is None:
                feature_cols = sorted(feats.keys())
            row = [feats.get(f, 0.0) for f in feature_cols]

            gt = self._well_data.get(well, {}).get('genotype')
            if gt is None:
                gt = plate_gt.get(well)
            if gt is not None:
                try:
                    y_list.append(int(gt))
                    X_list.append(row)
                except (ValueError, TypeError):
                    pass

        if len(X_list) < 5:
            reply = QMessageBox.question(
                self, "Train IS",
                f"Only {len(X_list)} wells have genotypes from Genotyping.xlsx.\n"
                "Assuming all wells are het (4) for this plate?\n"
                "(Click Yes to label all IS-corrected wells as het and train)",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                for well in self._get_all_wells():
                    wd = self._well_data.get(well)
                    if wd is None:
                        continue
                    peaks = wd.get('peaks')
                    pchs = wd.get('peak_channels', [])
                    if peaks is None or len(peaks) < 2:
                        continue
                    ch3_scans = []
                    for i, s in enumerate(peaks):
                        ch = pchs[i] if i < len(pchs) else ''
                        if ch == 'Channel3' or ch == 2:
                            ch3_scans.append(int(s))
                    if len(ch3_scans) < 2:
                        continue
                    rsd_path = os.path.join(folder, f"{well}.rsd")
                    if not os.path.exists(rsd_path):
                        continue
                    df = parse_rsd(rsd_path)
                    if len(df) < 50:
                        continue
                    ch3 = df['Channel3'].values.astype(float)
                    ispk = [(s, float(ch3[s])) for s in ch3_scans if s < len(ch3)]
                    feats = self._extract_simple_features(df, is_peaks=ispk)
                    row = [feats.get(f, 0.0) for f in feature_cols]
                    X_list.append(row)
                    y_list.append(4)
            else:
                QMessageBox.warning(self, "Train IS", "Not enough labeled wells. Train cancelled.")
                return

        X = np.array(X_list)
        y = np.array(y_list)

        from sklearn.ensemble import RandomForestClassifier
        clf = RandomForestClassifier(n_estimators=200, max_depth=8, min_samples_leaf=5,
                                     class_weight='balanced', random_state=42, n_jobs=-1)
        clf.fit(X, y)

        model_path = os.path.join(SCRIPT_DIR, 'genotyping_model.pkl')
        joblib.dump(clf, model_path)
        pd.DataFrame({'feature': feature_cols}).to_csv(
            model_path.replace('.pkl', '_features.csv'), index=False)

        y_pred = clf.predict(X)
        correct = (y_pred == y).sum()
        QMessageBox.information(self, "Train IS",
                                f"Trained on {len(X)} wells, {correct}/{len(X)} correct.\n"
                                f"Model saved to genotyping_model.pkl")

    def _export_is_peaks_csv(self):
        """Export all wells' IS peaks (scan + height) to CSV for ML training."""
        wells = self._get_all_wells()
        if not wells:
            QMessageBox.warning(self, "Export IS CSV", "No wells loaded.")
            return

        folder_name = os.path.basename(self._current_folder) if self._current_folder else ''
        rows = []
        for well in wells:
            wd = self._well_data.get(well)
            if wd is None:
                continue
            peaks = wd.get('peaks', [])
            pchs = wd.get('peak_channels', [])
            phgts = wd.get('peak_heights', [])
            ch3_peaks = []
            for i, s in enumerate(peaks):
                ch = pchs[i] if i < len(pchs) else ''
                if ch == 2 or ch == 'Channel3':
                    h = phgts[i] if i < len(phgts) else 0.0
                    ch3_peaks.append((int(s), float(h)))
            ch3_peaks.sort(key=lambda x: x[0])
            if not ch3_peaks:
                continue
            row = {'folder': folder_name, 'well': well}
            for i, (s, h) in enumerate(ch3_peaks[:4]):
                row[f'is_peak_{i+1}_scan'] = s
                row[f'is_peak_{i+1}_height'] = h
            rows.append(row)

        if not rows:
            QMessageBox.warning(self, "Export IS CSV", "No IS peaks found in any well.")
            return

        default_name = f'is_peaks_{folder_name}.csv' if folder_name else 'is_peaks.csv'
        csv_path, _ = QFileDialog.getSaveFileName(
            self, "Export IS Peaks CSV", os.path.join(os.path.dirname(__file__), default_name),
            "CSV Files (*.csv);;All Files (*)")
        if not csv_path:
            return
        pd.DataFrame(rows).to_csv(csv_path, index=False)
        QMessageBox.information(self, "Export IS CSV",
                                f"Exported IS peaks for {len(rows)} wells to\n{csv_path}")

    def _load_is_peaks(self):
        """Load saved IS peaks CSV and populate well_data for the current folder."""
        from run_is_genotyping import parse_rsd
        csv_path, _ = QFileDialog.getOpenFileName(
            self, "Load IS Peaks CSV", os.path.dirname(__file__),
            "IS Peaks CSV (is_peaks_*.csv);;CSV Files (*.csv);;All Files (*)")
        if not csv_path:
            return
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            QMessageBox.warning(self, "Load IS Peaks", f"Error reading CSV: {e}")
            return

        folder_name = os.path.basename(self._current_folder) if self._current_folder else ''
        folder_df = df[df['folder'] == folder_name]
        if len(folder_df) == 0:
            QMessageBox.warning(self, "Load IS Peaks",
                                f"No entries for current folder '{folder_name}' in CSV.")
            return

        self._sync_detector_params()
        loaded = 0
        for well in folder_df['well'].unique():
            well_df = folder_df[folder_df['well'] == well]
            is_peaks = []
            for col in ['is_peak_1_scan', 'is_peak_2_scan', 'is_peak_3_scan', 'is_peak_4_scan']:
                vals = well_df[col].dropna().values
                if len(vals) > 0:
                    try:
                        is_peaks.append(int(float(vals[0])))
                    except (ValueError, TypeError):
                        continue
            if len(is_peaks) < 2:
                continue
            rsd_path = os.path.join(self._current_folder, f"{well}.rsd")
            if not os.path.exists(rsd_path):
                continue
            try:
                trace = parse_rsd(rsd_path)
                scan = trace["Scan"]
                wd = self.detector.detect(trace, scan)
                wd['scan'] = scan
                wd['scan_values'] = scan
                wd['channel_data'] = {
                    'Channel1': trace['Channel1'].values.astype(float),
                    'Channel2': trace['Channel2'].values.astype(float),
                    'Channel3': trace['Channel3'].values.astype(float),
                    'Channel4': trace['Channel4'].values.astype(float),
                    'Current': trace['Current'].values.astype(float),
                }
                # Override peaks with loaded IS peaks
                ch3 = wd['channel_data']['Channel3']
                wd['peaks'] = np.array(sorted(is_peaks))
                wd['peak_channels'] = ['Channel3'] * len(is_peaks)
                wd['peak_lefts'] = np.array([max(0, p - 2) for p in is_peaks])
                wd['peak_rights'] = np.array([p + 2 for p in is_peaks])
                wd['peak_heights'] = [float(ch3[p]) if p < len(ch3) else 0.0 for p in is_peaks]
                self._well_data[well] = wd
                loaded += 1
            except Exception:
                continue

        if loaded > 0:
            self.update_plot()
            QMessageBox.information(self, "Load IS Peaks",
                                    f"Loaded IS peaks for {loaded} wells.")
        else:
            QMessageBox.warning(self, "Load IS Peaks",
                                "No wells with valid IS peaks found in CSV.")

    def _match_is_pattern(self, scored_candidates, n_expected, ref_spacing, ch3, noise):
        """Find the best set of n_expected peaks matching the reference spacing pattern.

        Uses a greedy nearest-neighbor approach starting from each top candidate.
        """
        if len(scored_candidates) < n_expected:
            return []

        # Sort by scan position for the pattern matching logic
        by_scan = sorted(scored_candidates, key=lambda x: x[0])
        scan_positions = [s for s, _ in by_scan]

        best_score = -1
        best_set = []

        # Try each top-20 candidate (by classifier score) as the anchor point
        for anchor_idx in range(min(20, len(scored_candidates))):
            anchor_scan, anchor_score = scored_candidates[anchor_idx]
            candidate_set = [int(anchor_scan)]
            cumulative_score = anchor_score

            # Find anchor's position in scan-sorted list
            try:
                scan_idx = scan_positions.index(anchor_scan)
            except ValueError:
                continue

            # Walk forward in scan order, matching reference spacing
            for spacing in ref_spacing:
                expected = candidate_set[-1] + spacing
                best_dist = self._is_ref_tolerance
                best_match = None
                best_match_score = 0
                best_j = scan_idx
                for j in range(scan_idx + 1, len(by_scan)):
                    s, sc = by_scan[j]
                    if s > expected + best_dist:
                        break
                    dist = abs(s - expected)
                    if dist < best_dist and s > candidate_set[-1]:
                        best_dist = dist
                        best_match = int(s)
                        best_match_score = sc
                        best_j = j
                if best_match is not None:
                    candidate_set.append(best_match)
                    cumulative_score += best_match_score
                    scan_idx = best_j
                else:
                    break

            if len(candidate_set) >= n_expected * 0.7:
                spacing_penalty = 0
                for i in range(min(len(ref_spacing), len(candidate_set) - 1)):
                    actual_spacing = candidate_set[i + 1] - candidate_set[i]
                    spacing_penalty += abs(actual_spacing - ref_spacing[i])
                total = cumulative_score - spacing_penalty * 0.01
                if total > best_score:
                    best_score = total
                    best_set = candidate_set[:n_expected]

        return best_set

    # ------------------------------------------------------------------
    # Clear / Reset
    # ------------------------------------------------------------------

    def clear_data(self):
        self.all_data.clear()
        self._well_data.clear()
        self._dirty_wells.clear()
        self._deleted_peaks.clear()
        self._manual_peaks.clear()
        self.selected_wells.clear()
        self._page_start = 0
        self._active_well = None
        self._undo_manager.clear()
        self.peak_table.setRowCount(0)
        self.is_channel_combo.clear()
        self.is_peak_combo.clear()
        self.snr_label.setText("Noise: -    Best SNR: -")
        self.summary_label.setText("IS Area: -    Sample Area: -    Area/IS: -")
        self._update_well_styles()
        self._highlight_well(None)
        self.training_data.clear()
        self._figure_labels = []
        self._original_all_data = None
        for btn in [self.norm_btn, self.align_btn, self.spectral_btn]:
            if btn.isChecked():
                btn.setChecked(False)
        for sp in self.subplots:
            sp['ax'].clear()
            sp['ax2'].clear()
            sp['ax'].set_visible(False)
            sp['ax2'].set_visible(False)
            sp['well'] = None
        self.canvas.draw()
        self.header_group.setVisible(False)
        self._current_folder = None
        self._file_header = {}
        self.status_label.setText("Data cleared")
        self.folder_label.setText("")

    # ------------------------------------------------------------------
    # Save / Export
    # ------------------------------------------------------------------

    def save_all_data(self):
        wells = sorted(self.all_data.keys())
        if not wells:
            QMessageBox.information(self, "Save All", "No data loaded.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save All Data", "", "CSV Files (*.csv)"
        )
        if not filename:
            return

        rows = self._export_peak_rows(wells)
        if not rows:
            QMessageBox.information(self, "Save All", "No peaks found.")
            return

        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        QMessageBox.information(
            self, "Save All", f"Saved {len(rows)} peaks from {len(wells)} wells."
        )

    def export_selected_wells(self):
        wells = sorted(self.selected_wells)
        if not wells:
            QMessageBox.information(
                self, "Export", "No wells selected. Ctrl+click wells to select them first."
            )
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Selected Wells", "", "CSV Files (*.csv)"
        )
        if not filename:
            return

        rows = self._export_peak_rows(wells)
        if not rows:
            QMessageBox.information(self, "Export", "No peaks found in selected wells.")
            return

        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

        QMessageBox.information(
            self, "Export", f"Saved {len(rows)} peaks from {len(wells)} wells."
        )

    def export_training_data(self):
        if not self.training_data:
            QMessageBox.information(self, "Export", "No labeled peaks available. Right-click a peak in the table and choose 'Label Peak'.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Training Data", "", "CSV Files (*.csv)"
        )
        if not filename:
            return

        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(self.training_data[0].keys()))
            writer.writeheader()
            writer.writerows(self.training_data)

        QMessageBox.information(
            self, "Export", f"Saved {len(self.training_data)} labeled peaks."
        )

    # ------------------------------------------------------------------
    # Machine Learning
    # ------------------------------------------------------------------

    def train_random_forest(self):
        if not self.training_data:
            QMessageBox.information(
                self, "Train RF",
                "No labeled data available. Right-click peaks in the table "
                "and choose 'Label Peak' first, then export to CSV."
            )
            return

        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.model_selection import train_test_split, cross_val_score
            from sklearn.preprocessing import LabelEncoder
        except ImportError:
            QMessageBox.critical(
                self, "Train RF",
                "scikit-learn is not installed.\n"
                "Install it with: pip install scikit-learn"
            )
            return

        df = pd.DataFrame(self.training_data)
        numeric_cols = ['scan', 'height', 'width', 'area']
        try:
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df = df.dropna(subset=numeric_cols + ['label'])
        except Exception:
            QMessageBox.warning(self, "Train RF", "Could not parse numeric columns.")
            return

        if len(df) < 10:
            QMessageBox.warning(
                self, "Train RF",
                f"Only {len(df)} labeled peaks. Need at least 10 for meaningful training."
            )
            return

        X = df[numeric_cols].values
        le = LabelEncoder()
        y = le.fit_transform(df['label'].values)

        scores = cross_val_score(RandomForestClassifier(n_estimators=100, random_state=42), X, y, cv=min(5, len(le.classes_)))
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        clf = RandomForestClassifier(n_estimators=100, random_state=42)
        clf.fit(X_train, y_train)
        accuracy = clf.score(X_test, y_test)

        msg = (
            f"Random Forest trained on {len(df)} samples.\n"
            f"Classes: {list(le.classes_)}\n"
            f"Cross-val accuracy: {scores.mean():.2f} (+/-{scores.std():.2f})\n"
            f"Test accuracy: {accuracy:.2f}"
        )
        QMessageBox.information(self, "Train RF", msg)

    def _train_cnn_model(self):
        """Train the CNN base caller model from within the GUI."""
        reply = QMessageBox.question(
            self, "Train CNN",
            "This will retrain the ML base caller CNN model using\n"
            "the extracted training data in training_data/.\n\n"
            "The training process may take several minutes.\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        import subprocess
        script = os.path.join(os.path.dirname(__file__), 'train_model.py')
        if not os.path.exists(script):
            QMessageBox.critical(self, "Train CNN", f"train_model.py not found at {script}")
            return

        self.status_label.setText("Training CNN model... (see terminal output)")
        QApplication.processEvents()

        try:
            proc = subprocess.Popen(
                [sys.executable, script],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            # Show output in a dialog
            output = []
            for line in proc.stdout:
                output.append(line.rstrip())
            proc.wait()

            if proc.returncode == 0:
                QMessageBox.information(
                    self, "Train CNN",
                    "Training completed successfully.\n\n"
                    + "\n".join(output[-10:])
                )
            else:
                QMessageBox.critical(
                    self, "Train CNN",
                    f"Training failed (exit code {proc.returncode}).\n\n"
                    + "\n".join(output[-5:])
                )
        except Exception as e:
            QMessageBox.critical(self, "Train CNN", f"Error launching training:\n{e}")

        self.status_label.setText("CNN training finished" if proc.returncode == 0
                                  else "CNN training failed")

    # ------------------------------------------------------------------
    # Genotyping prediction
    # ------------------------------------------------------------------

    def predict_genotypes(self):
        """Predict genotyping calls (0/1/2/4) using the trained ML model."""
        if not hasattr(self, 'all_data') or not self.all_data:
            QMessageBox.information(self, "Predict Genotypes",
                                    "No data loaded. Load a folder of .rsd files first.")
            return

        model_path = os.path.join(os.path.dirname(__file__), 'genotyping_model.pkl')
        features_path = model_path.replace('.pkl', '_features.csv')
        if not os.path.exists(model_path):
            QMessageBox.warning(self, "Predict Genotypes",
                                f"Trained model not found at {model_path}.\n"
                                f"Run `python3 train_genotyping.py` first.")
            return

        try:
            import joblib
            from sklearn.ensemble import RandomForestClassifier
        except ImportError:
            QMessageBox.critical(self, "Predict Genotypes",
                                 "scikit-learn/joblib not installed.\n"
                                 "Install with: pip install scikit-learn joblib")
            return

        model = joblib.load(model_path)
        ref_features = pd.read_csv(features_path)['feature'].tolist()

        folder_path = self._current_folder
        if not folder_path or not os.path.isdir(folder_path):
            QMessageBox.warning(self, "Predict Genotypes",
                                "No valid folder loaded. Load a folder of .rsd files first.")
            return

        # Step 1: Use existing Ch3 peaks from well_data (detector + manual edits).
        # The user runs the default peak finder, corrects ~10% manually, then predicts.
        self._sync_detector_params()
        is_peaks_by_well = {}
        wells_with_ch3 = 0
        for well in self._get_all_wells():
            if well not in self.all_data:
                continue
            df = self._get_well_trace(well)
            if df is None or len(df) < 50:
                continue
            ch3 = df['Channel3'].values.astype(float)
            wd = self._well_data.get(well)
            if wd is None:
                continue
            peaks = wd.get('peaks', [])
            pchs = wd.get('peak_channels', [])
            phgts = wd.get('peak_heights', [])
            ch3_peaks = []
            for i, s in enumerate(peaks):
                ch = pchs[i] if i < len(pchs) else ''
                if ch == 2 or ch == 'Channel3':
                    h = phgts[i] if i < len(phgts) else float(ch3[int(s)]) if int(s) < len(ch3) else 0.0
                    ch3_peaks.append((int(s), float(h)))
            if len(ch3_peaks) >= 2:
                ch3_peaks.sort(key=lambda x: x[0])
                is_peaks_by_well[well] = ch3_peaks[:4]
                wells_with_ch3 += 1

        if wells_with_ch3 < max(4, len(self._get_all_wells()) * 0.5):
            # Not enough wells have Ch3 peaks — try finding refs automatically
            from run_is_genotyping import find_consistent_is_refs
            self.status_label.setText("Finding IS peaks (inter-well consistency)...")
            QApplication.processEvents()
            refs = find_consistent_is_refs(folder_path)
            ref_positions = [r[0] for r in refs] if refs else None
            if ref_positions is None:
                refs_json_path = os.path.join(os.path.dirname(__file__), 'is_ref_positions.json')
                if os.path.exists(refs_json_path):
                    import json as _json
                    with open(refs_json_path) as _f:
                        _all_refs = _json.load(_f)
                    folder_name = os.path.basename(folder_path)
                    for key in sorted(_all_refs.keys(), key=len, reverse=True):
                        if key in folder_name or folder_name in key:
                            ref_positions = _all_refs[key]
                            break
            if ref_positions is not None:
                # Fallback: raw-trace argmax around refs
                for well in self._get_all_wells():
                    if well in is_peaks_by_well or well not in self.all_data:
                        continue
                    df = self._get_well_trace(well)
                    if df is None or len(df) < 50:
                        continue
                    ch3 = df['Channel3'].values.astype(float)
                    noise = np.std(ch3[:200]) if len(ch3) > 200 else max(np.std(ch3), 1e-10)
                    min_is_height = max(100, 5 * noise)
                    pairs = []
                    for ri, rp in enumerate(ref_positions):
                        lo = max(0, int(rp) - 150)
                        hi = min(len(ch3), int(rp) + 150)
                        if hi - lo < 3:
                            continue
                        pos = lo + int(np.argmax(ch3[lo:hi]))
                        h = float(ch3[pos])
                        if h < min_is_height:
                            continue
                        pairs.append((abs(pos - rp), ri, pos, h))
                    if not pairs:
                        continue
                    pairs.sort(key=lambda x: x[0])
                    assigned_peaks = set()
                    assigned_refs = set()
                    is_list = []
                    for dist, ri, pos, h in pairs:
                        if ri in assigned_refs or pos in assigned_peaks:
                            continue
                        assigned_refs.add(ri)
                        assigned_peaks.add(pos)
                        is_list.append((pos, h))
                    if is_list:
                        is_peaks_by_well[well] = sorted(is_list, key=lambda x: x[0])

        # Extract features using the found IS peaks
        self.status_label.setText("Extracting features...")
        QApplication.processEvents()
        all_wells_sorted = self._get_all_wells()
        X_list, well_ids = [], []
        peak_info_list = []  # per-well IS/sample peak info for table

        for well in all_wells_sorted:
            df = self._get_well_trace(well)
            if df is None or len(df) < 50:
                continue

            from train_genotyping import extract_features_from_trace
            try:
                isp = is_peaks_by_well.get(well)
                feats = extract_features_from_trace(df, is_peaks=isp)
            except Exception:
                continue

            # Extract IS peak scan/height info for display
            is_scans = [int(feats.get(f'IS_peak_{i}_scan', 0))
                        for i in range(1, 5)]
            is_heights = [float(feats.get(f'IS_peak_{i}_height', 0.0))
                          for i in range(1, 5)]

            # Find sample peaks: highest Ch1 and Ch2 peaks
            from scipy.signal import find_peaks
            ch1_max_scan, ch1_max_hgt = 0, 0.0
            ch2_max_scan, ch2_max_hgt = 0, 0.0
            try:
                y1 = df['Channel1'].values.astype(float)
                noise1 = np.std(y1[:200]) if len(y1) > 200 else np.std(y1)
                p1, props1 = find_peaks(y1, height=max(50, 3*noise1),
                                         prominence=1.5*noise1, distance=5)
                if len(p1) > 0:
                    h1 = props1['peak_heights']
                    idx = np.argmax(h1)
                    ch1_max_scan = int(p1[idx])
                    ch1_max_hgt = float(h1[idx])

                y2 = df['Channel2'].values.astype(float)
                noise2 = np.std(y2[:200]) if len(y2) > 200 else np.std(y2)
                p2, props2 = find_peaks(y2, height=max(50, 3*noise2),
                                         prominence=1.5*noise2, distance=5)
                if len(p2) > 0:
                    h2 = props2['peak_heights']
                    idx = np.argmax(h2)
                    ch2_max_scan = int(p2[idx])
                    ch2_max_hgt = float(h2[idx])
            except Exception:
                pass

            # Align to reference feature set
            row = []
            for f in ref_features:
                row.append(feats.get(f, 0.0))
            X_list.append(row)
            well_ids.append(well)
            peak_info_list.append({
                'is_scans': is_scans,
                'is_heights': is_heights,
                'ch1_scan': ch1_max_scan,
                'ch1_hgt': ch1_max_hgt,
                'ch2_scan': ch2_max_scan,
                'ch2_hgt': ch2_max_hgt,
            })

        if len(X_list) == 0:
            QMessageBox.warning(self, "Predict Genotypes",
                                "Could not extract features from any loaded wells.")
            return

        X_raw = np.array(X_list)
        from train_genotyping import LABEL_UNMAP

        # Per-plate normalization
        median = np.median(X_raw, axis=0)
        p75 = np.percentile(X_raw, 75, axis=0)
        p25 = np.percentile(X_raw, 25, axis=0)
        iqr = np.maximum(p75 - p25, 1e-8)
        X = (X_raw - median) / iqr

        y_prob = model.predict_proba(X)
        y_pred = model.predict(X)

        # Show results in a dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Genotype Predictions")
        dialog.resize(600, 500)

        layout = QVBoxLayout(dialog)

        # Summary stats
        from collections import Counter
        counts = Counter(y_pred)
        summary_items = []
        for k in sorted(counts):
            name = LABEL_UNMAP.get(k, f"Label {k}")
            summary_items.append(f"{name} ({k}): {counts[k]}")
        layout.addWidget(QLabel(f"Prediction Summary:  {' | '.join(summary_items)}"))

        # Table
        headers = ['Well', 'Prediction', 'Confidence',
                    'P(Fail)', 'P(Hom1)', 'P(Hom2)', 'P(Het)',
                    'Ch1_max_scan', 'Ch1_max_hgt',
                    'Ch2_max_scan', 'Ch2_max_hgt',
                    'IS_1_scan', 'IS_1_hgt',
                    'IS_2_scan', 'IS_2_hgt',
                    'IS_3_scan', 'IS_3_hgt',
                    'IS_4_scan', 'IS_4_hgt']
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(well_ids))

        for i, well in enumerate(well_ids):
            col = 0
            table.setItem(i, col, QTableWidgetItem(well))
            col += 1
            pred_int = int(y_pred[i])
            pred_name = LABEL_UNMAP.get(pred_int, str(pred_int))
            table.setItem(i, col, QTableWidgetItem(f"{pred_name} ({pred_int})"))
            col += 1

            if y_prob.shape[1] >= 4:
                conf = float(np.max(y_prob[i])) * 100
                table.setItem(i, col, QTableWidgetItem(f"{conf:.1f}%"))
                col += 1
                for j, orig_lbl in enumerate([0, 1, 2, 4]):
                    cidx = list(model.classes_).index(orig_lbl) if orig_lbl in model.classes_ else -1
                    if cidx >= 0:
                        pct = float(y_prob[i][cidx]) * 100
                        table.setItem(i, col, QTableWidgetItem(f"{pct:.1f}%"))
                    col += 1
            else:
                col += 5  # skip prob columns if not available

            # Peak info columns
            pi = peak_info_list[i]
            table.setItem(i, col, QTableWidgetItem(str(pi['ch1_scan']))); col += 1
            table.setItem(i, col, QTableWidgetItem(f"{pi['ch1_hgt']:.0f}")); col += 1
            table.setItem(i, col, QTableWidgetItem(str(pi['ch2_scan']))); col += 1
            table.setItem(i, col, QTableWidgetItem(f"{pi['ch2_hgt']:.0f}")); col += 1
            for s, h in zip(pi['is_scans'], pi['is_heights']):
                table.setItem(i, col, QTableWidgetItem(str(s) if s > 0 else '')); col += 1
                table.setItem(i, col, QTableWidgetItem(f"{h:.0f}" if h > 0 else '')); col += 1

        table.resizeColumnsToContents()
        layout.addWidget(table)

        btn_layout = QHBoxLayout()
        copy_btn = QPushButton("Copy Table")
        def _copy_table():
            import csv, io
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow([table.horizontalHeaderItem(c).text() for c in range(table.columnCount())])
            for r in range(table.rowCount()):
                w.writerow(table.item(r, c).text() if table.item(r, c) else ''
                           for c in range(table.columnCount()))
            QApplication.clipboard().setText(buf.getvalue())
        copy_btn.clicked.connect(_copy_table)
        btn_layout.addWidget(copy_btn)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        dialog.exec_()

    def _get_well_trace(self, well):
        """Get the parsed trace DataFrame for a well, from cache or by parsing."""
        if hasattr(self, 'all_data') and well in self.all_data:
            return self.all_data[well]
        if hasattr(self, '_original_all_data') and well in self._original_all_data:
            return self._original_all_data[well]
        # Try parsing the .rsd file directly
        folder = getattr(self, '_current_folder', None)
        if folder is None:
            return None
        rsd_path = os.path.join(folder, f"{well}.rsd")
        txt_path = os.path.join(folder, f"{well}.txt")
        if os.path.exists(rsd_path):
            from train_genotyping import parse_rsd
            return parse_rsd(rsd_path)
        elif os.path.exists(txt_path):
            from peak_detector import load_trace_file
            return load_trace_file(txt_path)
        return None

    def _get_all_wells(self):
        """Get sorted list of all wells from loaded data."""
        if hasattr(self, 'all_data') and self.all_data:
            wells = sorted(self.all_data.keys(), key=self._well_sort_key)
            if wells:
                return wells
        folder = getattr(self, '_current_folder', None)
        if folder is not None and os.path.isdir(folder):
            rsd_files = sorted(glob.glob(os.path.join(folder, '*.rsd')))
            return sorted(set(os.path.splitext(os.path.basename(f))[0]
                             for f in rsd_files), key=self._well_sort_key)
        return []

    def _well_sort_key(self, w):
        row = w[0] if w else 'A'
        try:
            col = int(w[1:]) if len(w) > 1 else 0
        except ValueError:
            col = 0
        return (row, col)

    # ------------------------------------------------------------------
    # Legacy compat stubs
    # ------------------------------------------------------------------

    @property
    def _scan(self):
        wd = self._well_data.get(self._active_well)
        return wd['scan'] if wd else None

    @_scan.setter
    def _scan(self, val):
        pass

    @property
    def _scan_values(self):
        wd = self._well_data.get(self._active_well)
        return wd['scan_values'] if wd else None

    @_scan_values.setter
    def _scan_values(self, val):
        pass

    @property
    def _channel_data(self):
        wd = self._well_data.get(self._active_well)
        return wd['channel_data'] if wd else {}

    @_channel_data.setter
    def _channel_data(self, val):
        pass

    @property
    def peaks(self):
        wd = self._well_data.get(self._active_well)
        return wd['peaks'] if wd else np.array([], dtype=int)

    @peaks.setter
    def peaks(self, val):
        pass

    @property
    def peak_channels(self):
        wd = self._well_data.get(self._active_well)
        return wd['peak_channels'] if wd else []

    @peak_channels.setter
    def peak_channels(self, val):
        pass

    @property
    def areas(self):
        areas = []
        for i in range(self.peak_table.rowCount()):
            item = self.peak_table.item(i, 7)
            if item is not None:
                try:
                    areas.append(float(item.text()))
                except ValueError:
                    pass
        return areas

    @areas.setter
    def areas(self, val):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ElectropherogramApp()
    window.show()
    sys.exit(app.exec_())
