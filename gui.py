import sys
import os
import csv
import struct

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
from basecaller import basecall, basecall_ml, CHEMISTRY_MAP


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
        self.setWindowTitle("Base Calling Results")
        self.resize(700, 500)
        layout = QVBoxLayout(self)

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
        btn_save = QPushButton("Save FASTA")
        btn_save.clicked.connect(lambda: self._save_fasta(well_results))
        btn_row.addWidget(btn_save)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _save_fasta(self, well_results):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save FASTA", "", "FASTA (*.seq *.fasta);;All Files (*)"
        )
        if not path:
            return
        with open(path, "w") as f:
            for well, result in well_results.items():
                f.write(f">{well}\n")
                seq = result["sequence"]
                for i in range(0, len(seq), 80):
                    f.write(seq[i:i+80] + "\n")


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
        self._undo_manager = UndoManager()
        self._spectral_matrix = DEFAULT_SPECTRAL_MATRIX.copy()

        self.training_data = []
        self._figure_labels = []
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

        self.init_ui()

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
        export_btn = QPushButton("Export ML Data")
        export_btn.setToolTip("Export labeled peak data as CSV for ML training")
        export_btn.clicked.connect(self.export_training_data)
        ml_layout.addWidget(export_btn)
        train_btn = QPushButton("Train RF")
        train_btn.setToolTip("Train a Random Forest classifier using exported peak labels")
        train_btn.clicked.connect(self.train_random_forest)
        ml_layout.addWidget(train_btn)
        export_sel_btn = QPushButton("Export Selected")
        export_sel_btn.setToolTip("Export peaks and areas for selected wells as CSV")
        export_sel_btn.clicked.connect(self.export_selected_wells)
        ml_layout.addWidget(export_sel_btn)
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
        layout.addLayout(params_layout)

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
        self.start_spin.setRange(0, 100000)
        self.start_spin.setValue(0)
        self.start_spin.setEnabled(False)
        self.start_spin.valueChanged.connect(self._mark_dirty_and_update)
        range_layout.addWidget(self.start_spin)
        range_layout.addWidget(QLabel("End:"))
        self.end_spin = QSpinBox()
        self.end_spin.setToolTip("End scan number for range-limited detection")
        self.end_spin.setRange(0, 100000)
        self.end_spin.setValue(50000)
        self.end_spin.setEnabled(False)
        self.end_spin.valueChanged.connect(self._mark_dirty_and_update)
        range_layout.addWidget(self.end_spin)
        layout.addLayout(range_layout)

        self.status_label = QLabel("No data loaded")
        layout.addWidget(self.status_label)

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

        QShortcut(QKeySequence(Qt.Key_Delete), self, self._delete_nearest_peak)
        QShortcut(QKeySequence(Qt.Key_Backspace), self, self._delete_nearest_peak)
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

        QShortcut(QKeySequence(Qt.Key_Left), self, self._prev_well_single)
        QShortcut(QKeySequence(Qt.Key_Right), self, self._next_well_single)

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

        # Find end of data: metadata starts when any field exceeds 5000
        # (ASCII text labels read as uint32 produce values > 10^6)
        MAX_CHANNEL_VALUE = 5000
        boundary = len(records)
        for i, rec in enumerate(records):
            if any(v > MAX_CHANNEL_VALUE for v in rec):
                boundary = i
                break

        data = records[:boundary]
        df = pd.DataFrame(data, columns=['Current', 'Channel1', 'Channel2', 'Channel3', 'Channel4'])
        df['Scan'] = np.arange(len(df))
        return df[['Scan', 'Channel1', 'Channel2', 'Channel3', 'Channel4', 'Current']]

    def load_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
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
            self._update_well_styles()
            self._highlight_well(first)
            self.update_plot()

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
        if chemistry == "ML Base Caller":
            try:
                from basecaller import _load_ml_model
                ml_model = _load_ml_model()
            except (FileNotFoundError, Exception) as e:
                QMessageBox.critical(
                    self, "ML Base Caller",
                    f"Cannot load ML model:\n{e}\n\n"
                    f"Train it first with: python train_model.py"
                )
                return
        for well in sorted(self.selected_wells):
            if well not in self.all_data:
                continue
            df = self.all_data[well]
            self._sync_detector_params()
            wd = self.detector.detect(df, df["Scan"])
            if len(wd["peaks"]) == 0:
                continue
            if chemistry == "ML Base Caller":
                bc = basecall_ml(
                    data=df,
                    peaks=wd["peaks"],
                    peak_channels=wd["peak_channels"],
                    scan_values=wd["scan_values"],
                    model=ml_model,
                    min_quality=10,
                )
            else:
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
        """Filter peaks in all wells based on IS selection.

        - In the IS channel: keep only the top N peaks by height (N = IS Peak #).
        - In sample channels: keep only peaks whose scan falls within an IS peak's
          scan window (left_ips – tolerance … right_ips + tolerance).
        - Within each channel, limit total peaks to N.
        - IS peak positions are matched between wells by ordering by scan (i.e. the
          earliest-eluting canonical IS peak is peak #1 in every well).
        """
        ch = self._is_channel
        if not ch:
            return
        n_is = self._is_peak_num
        if n_is is None or n_is < 1:
            return

        tolerance = 30  # scan points around each IS peak

        # ---- Step 1: for each well, identify the top-N IS channel peaks ----
        is_info = {}  # well -> {positions, lefts, rights, indices}
        for well, wd in self._well_data.items():
            if well not in self.all_data:
                continue
            peaks = wd['peaks']
            pchs = wd['peak_channels']
            sv = wd['scan_values']

            is_idx = [i for i, pc in enumerate(pchs) if pc == ch]
            if not is_idx:
                continue

            ch_data = wd['channel_data'].get(ch)
            if ch_data is None:
                continue
            heights = [ch_data[peaks[i]] for i in is_idx]
            top = sorted(is_idx, key=lambda i: heights[is_idx.index(i)], reverse=True)[:n_is]
            top = sorted(top, key=lambda i: sv[peaks[i]])

            is_info[well] = {
                'positions': [sv[peaks[i]] for i in top],
                'lefts': [wd['peak_lefts'][i] for i in top],
                'rights': [wd['peak_rights'][i] for i in top],
                'indices': set(top),
            }

        if not is_info:
            return

        # ---- Step 2: build median IS peak positions across wells ----
        n = min(len(v['positions']) for v in is_info.values())
        if n == 0:
            return

        median_positions = []
        median_lefts = []
        median_rights = []
        ref_wells = [w for w, v in is_info.items() if len(v['positions']) >= n]
        for i in range(n):
            median_positions.append(np.median([is_info[w]['positions'][i] for w in ref_wells]))
            median_lefts.append(np.median([is_info[w]['lefts'][i] for w in ref_wells]))
            median_rights.append(np.median([is_info[w]['rights'][i] for w in ref_wells]))

        # ---- Step 3: filter every well's peak list ----
        for well, wd in self._well_data.items():
            if well not in is_info:
                continue
            peaks = wd['peaks']
            pchs = wd['peak_channels']
            sv = wd['scan_values']
            info = is_info[well]

            new_peaks = []
            new_channels = []
            new_lefts = []
            new_rights = []

            for pc in sorted(set(pchs), key=lambda x: int(x.replace('Channel', '') or '0')):
                mask = np.array([c == pc for c in pchs])
                pc_peaks = peaks[mask]
                pc_indices = np.where(mask)[0]
                pc_lefts = wd['peak_lefts'][mask]
                pc_rights = wd['peak_rights'][mask]

                keep = []
                for idx_in_pc, (p, orig_i) in enumerate(zip(pc_peaks, pc_indices)):
                    scan_val = sv[p]
                    if pc == ch:
                        keep.append(orig_i in info['indices'])
                    else:
                        inside = False
                        for j in range(min(n, len(info['positions']))):
                            l = info['lefts'][j] - tolerance
                            r = info['rights'][j] + tolerance
                            if l <= scan_val <= r:
                                inside = True
                                break
                        keep.append(inside)

                if not any(keep):
                    continue

                keep_idx = [i for i, k in enumerate(keep) if k]

                # Limit per channel to top N by height
                if len(keep_idx) > n_is:
                    ch_heights = [wd['channel_data'].get(pc, np.zeros_like(sv))[pc_peaks[i]] for i in keep_idx]
                    keep_idx = [keep_idx[i] for i in np.argsort(ch_heights)[-n_is:]]
                    keep_idx.sort()

                for i in keep_idx:
                    new_peaks.append(pc_peaks[i])
                    new_channels.append(pc)
                    new_lefts.append(pc_lefts[i])
                    new_rights.append(pc_rights[i])

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

        self._apply_is_filter()
        self._draw_peak_markers()
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
                key=lambda x: int(x.replace('Channel', '') or '0')
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
                self.bl_spin.setRange(10, 5000)
                self.bl_spin.setValue(500)
            elif method == "ALS":
                self.bl_label.setText("Lambda (10^x):")
                self.bl_spin.setRange(2, 9)
                self.bl_spin.setValue(5)
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
        self.status_label.setText("Data cleared")

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
