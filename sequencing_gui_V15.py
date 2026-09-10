#!/usr/bin/env python3
"""Sequencing basecaller GUI V15 — modular version.

Core DSP, basecalling, and alignment logic lives in separate modules
(constants.py, dsp.py, basecall.py, align.py).  This file contains only
the PyQt5 GUI classes, the OptimizerWorker thread, and the ReferenceDialog.
"""
import sys, os, struct, json, subprocess, tempfile
import numpy as np

import multiview_peakdetect as mvpd

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton,
    QGroupBox, QGridLayout, QSlider, QTextEdit, QSplitter, QTabWidget,
    QFileDialog, QProgressBar, QScrollArea, QFrame, QDialog, QLineEdit,
    QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer, QSettings, QThread, pyqtSignal

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_training_data import parse_rsd, parse_esd

try:
    from cimarrontv import cimarron_bgn_end as _cimarron_bgn_end
except Exception:
    _cimarron_bgn_end = None

# ── Import from new modules ────────────────────────────────────────────
from constants import (
    CHAN_COLORS, BASE_LETTERS, CHEM_MAP, IUPAC_CODES,
    DEFAULT_SPEC_MATRIX, _TUNED_SSM, OFF_PATTERN,
    BASELINE_METHODS, SMOOTH_METHODS,
    SMOOTH_PARAM_CONFIG, SMOOTH_TOOLTIPS,
    SMOOTH_PARAM1_TOOLTIPS, SMOOTH_PARAM2_TOOLTIPS,
    BASELINE_PARAM_CONFIG, METRIC_TOOLTIPS,
)
from dsp import (
    find_esd_subdirs, make_matrix_from_diagonals,
    dsp_shift_channel, dsp_apply_mobility_shifts, dsp_full_pipeline,
    dsp_compute_baseline, dsp_smooth_signal, dsp_separate_channels,
    dsp_dominant_periodicities,
)
from basecall import (
    pc_normalize_peaks, pc_normalize_display,
    pc_detect_peaks_4ch, pc_call_bases,
    pc_signal_onset, pc_signal_region,
    pc_call_bases_with_shifts, pc_call_bases_greedy,
    pc_fill_in_combined_peaks, pc_fill_in_shoulders,
    pc_lifetrace_peaks_shape, pc_lifetrace_transform,
    pc_lifetrace_basecall, pc_hybrid_basecall,
    pc_estimate_mobility_shifts,
)
from align import (
    pc_nw_identity, pc_reference_accuracy,
    ref_semiglobal_identity, ref_local_identity, _ref_revcomp,
)

DEFAULT_DATA_DIR = "/media/tv/78B0C7DE1FA7081C/electropherogram/MB1000_M13_DT"
class ReferenceDialog(QDialog):
    """Paste or load a known reference sequence (e.g. M13) and measure how
    accurate both the ESD basecall and the independent caller are against the
    truth, instead of only against each other. The reference is stored in the
    settings JSON so it can be reused for other fragments in future runs."""

    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self.setWindowTitle('Reference DNA comparison')
        self.setMinimumWidth(620)

        lay = QVBoxLayout(self)
        name_row = QHBoxLayout()
        name_row.addWidget(QLabel('Reference name:'))
        self.name_edit = QLineEdit(gui.reference_name)
        name_row.addWidget(self.name_edit, 1)
        lay.addLayout(name_row)

        lay.addWidget(QLabel('Reference sequence (ACGT; FASTA headers allowed):'))
        self.ref_text = QTextEdit()
        self.ref_text.setPlainText(gui.reference_dna)
        self.ref_text.setMaximumHeight(140)
        lay.addWidget(self.ref_text)

        region_row = QHBoxLayout()
        region_row.addWidget(QLabel('Region from'))
        self.from_spin = QSpinBox()
        self.from_spin.setRange(1, 1000000)
        self.from_spin.setValue(gui.reference_start)
        region_row.addWidget(self.from_spin)
        region_row.addWidget(QLabel('to'))
        self.to_spin = QSpinBox()
        self.to_spin.setRange(1, 1000000)
        self.to_spin.setValue(gui.reference_end)
        region_row.addWidget(self.to_spin)
        region_row.addStretch(1)
        self.load_fasta_btn = QPushButton('Load FASTA…')
        self.load_fasta_btn.clicked.connect(self._load_fasta)
        region_row.addWidget(self.load_fasta_btn)
        lay.addLayout(region_row)

        self.compare_btn = QPushButton('Compare basecalls against reference')
        self.compare_btn.clicked.connect(self._compare)
        lay.addWidget(self.compare_btn)

        self.esd_result = QLabel('ESD vs reference: (run Compare)')
        self.ind_result = QLabel('Independent vs reference: (run Compare)')
        lay.addWidget(self.esd_result)
        lay.addWidget(self.ind_result)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def _clean_seq(self):
        text = self.ref_text.toPlainText()
        lines = [l.strip() for l in text.splitlines()
                 if l.strip() and not l.startswith('>')]
        return ''.join(c for c in ''.join(lines) if c in 'ACGTNacgtn').upper()

    def _load_fasta(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Load reference FASTA', '',
            'FASTA files (*.fa *.fasta);;All Files (*)')
        if not path:
            return
        try:
            with open(path) as f:
                lines = f.read().splitlines()
        except Exception as e:
            self.esd_result.setText(f'Could not read FASTA: {e}')
            return
        name = lines[0].lstrip('>').split()[0] if lines and lines[0].startswith('>') \
            else os.path.basename(path)
        seq = ''.join(c for c in ''.join(
            l for l in lines[1:] if not l.startswith('>'))
            if c in 'ACGTNacgtn').upper()
        self.name_edit.setText(name)
        self.ref_text.setPlainText(seq)

    def _compare(self):
        gui = self.gui
        if gui.rsd_raw is None or gui.esd_data is None:
            self.esd_result.setText('Load a well first (needs RSD + ESD data)')
            return
        ref = self._clean_seq()
        lo = max(1, self.from_spin.value())
        hi = self.to_spin.value()
        if not ref or hi < lo:
            self.esd_result.setText('Reference empty or invalid region')
            return
        ref_slice = ref[lo - 1:hi]

        esd_seq = gui.esd_data.get('sequence', '')
        # Use the caller shown in the plot (tolerance + fill-in knobs), not
        # the old standalone pc_call_bases path. _update_plot refreshes it
        # synchronously so the comparison always matches what is on screen.
        gui._update_plot()
        ind_seq = gui._manual_sequence or ''
        if not ind_seq:
            gui._run_independent_peakcall()
            ind_seq = gui._independent_seq or ''

        for label, seq, box in (('ESD', esd_seq, self.esd_result),
                                ('Independent', ind_seq, self.ind_result)):
            if not seq:
                box.setText(f'{label} vs reference: no sequence')
                continue
            fwd = ref_local_identity(seq, ref_slice)
            rev = ref_local_identity(_ref_revcomp(seq), ref_slice)
            (ident, mm, mmis, ind, aligned, score, rlo, rhi,
             qlo, qhi, mism) = (rev if rev[5] >= fwd[5] else fwd)
            orient = 'rev-comp' if rev[5] >= fwd[5] else 'forward'
            errors = mmis + ind
            drop_start = qlo
            drop_end = max(0, len(seq) - 1 - qhi)
            box.setText(
                f'{label} vs reference (BLAST local): {ident:.1f}%\n'
                f'  {mm} matches, {mmis} mismatch, {ind} indel '
                f'= {errors} errors ({aligned} bases aligned)\n'
                f'  {orient} read · best segment ref {lo + rlo}..{lo + rhi}\n'
                f'  {drop_start} bp dropped at read start, '
                f'{drop_end} at read end')

    def accept(self):
        self.gui.reference_name = self.name_edit.text().strip()
        self.gui.reference_dna = self._clean_seq()
        self.gui.reference_start = max(1, self.from_spin.value())
        self.gui.reference_end = max(1, self.to_spin.value())
        super().accept()


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
class SequencingGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Sequencing Basecaller GUI V10')
        self.setGeometry(50, 50, 1500, 950)
        self.rsd_raw = None
        self.esd_traces = None
        self.esd_data = None
        self.esd_offset = 0
        self.current_well = None
        self._saved_lims = {}
        self._smooth_mode = 'Savitzky-Golay'
        self._manual_sequence = ''
        self._shift_lines = {}
        self._drag_channel = None
        self._drag_start_x = 0
        self._last_separated = None
        self._independent_seq = None
        self.reference_name = 'M13 M77815.1'
        self.reference_dna = ''
        self.reference_start = 5300
        self.reference_end = 6300
        self._settings = QSettings('opencode', 'sequencing_gui')
        self.data_dir = str(self._settings.value(
            'data_dir', os.environ.get('SEQUENCING_DATA_DIR', '')))
        if not self.data_dir or not os.path.isdir(self.data_dir):
            self.data_dir = DEFAULT_DATA_DIR
        self._setup_ui()
        self._restore_settings()
        self._populate_wells()
        if not self.reference_dna:
            m13 = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'refs', 'm13_M77815.1.fa')
            if os.path.exists(m13):
                try:
                    with open(m13) as f:
                        lines = f.read().splitlines()
                    seq = ''.join(c for c in ''.join(
                        l for l in lines[1:] if l.strip() and not l.startswith('>'))
                        if c in 'ACGTNacgtn').upper()
                    if seq:
                        self.reference_dna = seq
                        self.reference_name = 'M13 M77815.1'
                except Exception:
                    pass

    def _setup_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setContentsMargins(4, 4, 4, 4)

        # -- Top bar --
        top = QHBoxLayout()
        layout.addLayout(top)
        self.data_dir_btn = QPushButton('Select Data Folder…')
        self.data_dir_btn.setToolTip(
            'Choose the folder that contains the .rsd sequencing files '
            '(and the per-run ESD subfolders like *_MD1).')
        self.data_dir_btn.clicked.connect(self._select_data_folder)
        top.addWidget(self.data_dir_btn)
        self.data_dir_label = QLabel(self.data_dir)
        self.data_dir_label.setToolTip('Current data folder')
        self.data_dir_label.setMaximumWidth(380)
        self.data_dir_label.setStyleSheet('color: #555;')
        top.addWidget(self.data_dir_label)
        top.addSpacing(8)
        top.addWidget(QLabel('Well:'))
        self.well_combo = QComboBox()
        self.well_combo.setEditable(True)
        self.well_combo.setMinimumWidth(80)
        self.well_combo.setToolTip(
            'Select the RSD (raw sequencing data) well to load. Typed '
            'names are matched against the .rsd files in the data folder.')
        top.addWidget(self.well_combo)
        self.load_btn = QPushButton('Load')
        self.load_btn.setToolTip('Load the selected well\'s RSD trace and '
                                 'its matching ESD basecall data and update '
                                 'the plot.')
        self.load_btn.clicked.connect(self._load_data)
        top.addWidget(self.load_btn)
        top.addWidget(QLabel('  ESD variant:'))
        self.esd_combo = QComboBox()
        self.esd_combo.setToolTip(
            'Choose which ESD (basecaller output) variant to compare '
            'against. "Cp312" is the standard alignment. Other entries are '
            'alternate peak-calling variants; use Cp312 for the best '
            'machine-learning match.')
        top.addWidget(self.esd_combo)
        top.addSpacing(4)
        top.addWidget(QLabel('ESD offset:'))
        self.esd_offset_spin = QSpinBox()
        self.esd_offset_spin.setRange(-20000, 40000)
        self.esd_offset_spin.setValue(0)
        self.esd_offset_spin.setSingleStep(10)
        self.esd_offset_spin.setMinimumWidth(90)
        self.esd_offset_spin.setToolTip(
            'Manual horizontal shift applied to the ESD trace (records -> '
            'scans) so the ESD bases sit under our basecall for comparison. '
            'Auto-estimated on load, but you can fine-tune it here and even '
            'use it to compare alternate ESD variants (each may need its own '
            'offset).')
        self.esd_offset_spin.valueChanged.connect(self._schedule_update)
        top.addWidget(self.esd_offset_spin)
        top.addSpacing(12)
        self.save_settings_btn = QPushButton('Save settings…')
        self.save_settings_btn.setToolTip(
            'Write all current settings (baseline, smoothing, matrix, '
            'mobility shifts, calling thresholds, norm window, well and ESD '
            'variant) to a JSON text file so the same basecall can be '
            'reproduced later or on another machine.')
        self.save_settings_btn.clicked.connect(self._save_settings_to_file)
        top.addWidget(self.save_settings_btn)
        self.load_settings_btn = QPushButton('Load settings…')
        self.load_settings_btn.setToolTip(
            'Read a previously saved settings JSON text file, apply it to '
            'the controls and re-run the basecall.')
        self.load_settings_btn.clicked.connect(self._load_settings_from_file)
        top.addWidget(self.load_settings_btn)
        self.reference_btn = QPushButton('Reference DNA…')
        self.reference_btn.setToolTip(
            'Compare the ESD basecall and the independent caller against a '
            'known reference sequence (e.g. M13), to measure how many real '
            'errors each caller has. The reference is stored in the settings '
            'JSON so it can be reused for other fragments later.')
        self.reference_btn.clicked.connect(self._open_reference_dialog)
        top.addWidget(self.reference_btn)

        # -- Figure + canvas + toolbar --
        self.fig = Figure(figsize=(14, 11), dpi=100)
        self.fig.subplots_adjust(hspace=0.08, left=0.14, right=0.98, top=0.97, bottom=0.05)
        # The figure's sizeHint would otherwise be 1400x1100px, and inside the
        # non-collapsible QSplitter that pins the window's minimum width to
        # ~1820px - wider than most screens, so the right edge is pushed
        # off-screen and cannot be grabbed to resize. Allow the canvas to
        # shrink so the window is freely resizable.
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setMinimumSize(200, 200)
        self.canvas.mpl_connect('button_press_event', self._on_canvas_press)
        self.canvas.mpl_connect('motion_notify_event', self._on_canvas_move)
        self.canvas.mpl_connect('button_release_event', self._on_canvas_release)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        top.addWidget(self.toolbar)
        top.addStretch()

        # -- Sliders panel (narrow left sidebar so the plots get more room) --
        sliders_scroll = QScrollArea()
        sliders_scroll.setWidgetResizable(True)
        sliders_scroll.setMinimumWidth(300)
        sliders_scroll.setMaximumWidth(460)
        sliders_scroll.setFrameShape(QFrame.NoFrame)
        sliders_w = QWidget()
        sliders_l = QVBoxLayout(sliders_w)
        sliders_l.setContentsMargins(0, 0, 0, 0)
        sliders_scroll.setWidget(sliders_w)

        # Baseline group
        blg = QGroupBox('Baseline')
        blg.setToolTip(
            'Baseline correction removes the slowly-varying background '
            'drift from each channel before peak detection. Pick a method '
            'below and tune its window and secondary parameter with the '
            'sliders. arPLS and ALS generally give the flattest baseline '
            'with the least distortion.')
        blg_g = QVBoxLayout(blg)
        hl_m = QHBoxLayout()
        hl_m.addWidget(QLabel('Method:'))
        self.baseline_combo = QComboBox()
        self.baseline_combo.addItems(BASELINE_METHODS)
        self.baseline_combo.setToolTip(
            'Baseline method: Rolling Minimum / Rolling Median roll a '
            'window along the trace; ALS / AsyLS / arPLS fit an asymmetric '
            'least-squares baseline; airPLS is an iterative variant; SNIP '
            'erodes the trace; Rubberband fits a convex hull below the '
            'signal; Polynomial Detrend removes a fitted trend. Try arPLS '
            'or ALS for clean, low-drift results.')
        self.baseline_combo.currentTextChanged.connect(self._on_baseline_method_changed)
        hl_m.addWidget(self.baseline_combo)
        blg_g.addLayout(hl_m)
        self.bl_param_label = QLabel('Window:')
        self.bl_param_label.setToolTip(
            'Window (scans) over which the baseline is estimated. Larger '
            'windows follow slow drift only; smaller windows hug faster '
            'changes but risk fitting peaks as baseline.')
        blg_g.addWidget(self.bl_param_label)
        hl = QHBoxLayout()
        self.bl_slider = QSlider(Qt.Horizontal)
        self.bl_slider.setRange(20, 1000)
        self.bl_slider.setValue(200)
        self.bl_slider.setSingleStep(10)
        self.bl_slider.setToolTip('Same as the "Window" spin box, as a slider.')
        self.bl_spin = QSpinBox()
        self.bl_spin.setRange(20, 1000)
        self.bl_spin.setValue(200)
        self.bl_spin.setSingleStep(10)
        self.bl_spin.setMinimumWidth(70)
        self.bl_spin.setToolTip(
            'Baseline window in scans. Larger = only slow background is '
            'removed; smaller = more aggressive, may eat real peaks.')
        self._link_slider_spinbox(self.bl_slider, self.bl_spin)
        hl.addWidget(self.bl_slider)
        hl.addWidget(self.bl_spin)
        blg_g.addLayout(hl)

        # Baseline secondary param (asymmetry p for ALS/AsyLS, max iters for airPLS/arPLS)
        blg_g2 = QHBoxLayout()
        self.bl2_param_label = QLabel('Secondary:')
        self.bl2_slider = QSlider(Qt.Horizontal)
        self.bl2_slider.setToolTip(
            'Second baseline parameter, shown only when the chosen method '
            'uses one. For ALS / AsyLS it is the asymmetry p (label shows '
            'p x100) - higher biases the fit below the signal. For airPLS / '
            'arPLS it is the maximum number of fitting iterations.')
        self.bl2_slider.setRange(1, 100)
        self.bl2_slider.setValue(1)
        self.bl2_slider.setSingleStep(1)
        self.bl2_slider.setTickPosition(QSlider.TicksBelow)
        self.bl2_param_label.setToolTip('Secondary baseline parameter: asymmetry p (ALS/AsyLS) or max iterations (airPLS, arPLS)')
        self.bl2_spin = QSpinBox()
        self.bl2_spin.setRange(1, 100)
        self.bl2_spin.setValue(1)
        self.bl2_spin.setSingleStep(1)
        self.bl2_spin.setMinimumWidth(70)
        self.bl2_spin.setToolTip(
            'Second baseline parameter, shown only when the chosen method '
            'uses one. For ALS / AsyLS it is the asymmetry p (the label '
            'shows p x100) - higher biases the fit below the signal. For '
            'airPLS / arPLS it is the maximum number of fitting '
            'iterations.')
        self._link_slider_spinbox(self.bl2_slider, self.bl2_spin)
        blg_g2.addWidget(self.bl2_param_label)
        blg_g2.addWidget(self.bl2_slider)
        blg_g2.addWidget(self.bl2_spin)
        blg_g.addLayout(blg_g2)
        sliders_l.addWidget(blg)

        # Smoothing group
        smg = QGroupBox('Smooth')
        smg.setToolTip(
            'Smoothing filters noise from the baseline-corrected trace '
            'before peak detection. Choose a method and a window/order. '
            'Savitzky-Golay preserves peak shape well; too large a window '
            'can merge close peaks.')
        smg_g = QVBoxLayout(smg)
        smg_g.setSpacing(2)
        hl_m = QHBoxLayout()
        hl_m.addWidget(QLabel('Method:'))
        self.smooth_combo = QComboBox()
        self.smooth_combo.addItems(SMOOTH_METHODS)
        self.smooth_combo.setToolTip(SMOOTH_TOOLTIPS.get(self.smooth_combo.currentText()))
        self.smooth_combo.currentTextChanged.connect(self._on_smooth_method_changed)
        hl_m.addWidget(self.smooth_combo)
        smg_g.addLayout(hl_m)

        hl1 = QHBoxLayout()
        self.sm_param1_label = QLabel('Window:')
        self.sm_param1_label.setToolTip(SMOOTH_PARAM1_TOOLTIPS.get(self.smooth_combo.currentText()))
        hl1.addWidget(self.sm_param1_label)
        self.sm_win_slider = QSlider(Qt.Horizontal)
        self.sm_win_slider.setRange(3, 51)
        self.sm_win_slider.setValue(7)
        self.sm_win_slider.setSingleStep(2)
        self.sm_win_slider.setTickPosition(QSlider.TicksBelow)
        self.sm_win_slider.setToolTip('Same as the "Window" spin box, as a slider.')
        self.sm_win_spin = QSpinBox()
        self.sm_win_spin.setRange(3, 51)
        self.sm_win_spin.setValue(7)
        self.sm_win_spin.setSingleStep(2)
        self.sm_win_spin.setMinimumWidth(60)
        self.sm_win_spin.setToolTip(SMOOTH_PARAM1_TOOLTIPS.get(self.smooth_combo.currentText()))
        self._link_slider_spinbox(self.sm_win_slider, self.sm_win_spin)
        hl1.addWidget(self.sm_win_slider)
        hl1.addWidget(self.sm_win_spin)
        smg_g.addLayout(hl1)

        hl2 = QHBoxLayout()
        self.sm_param2_label = QLabel('Order:')
        self.sm_param2_label.setToolTip(SMOOTH_PARAM2_TOOLTIPS.get(self.smooth_combo.currentText()))
        hl2.addWidget(self.sm_param2_label)
        self.sm_ord_slider = QSlider(Qt.Horizontal)
        self.sm_ord_slider.setRange(1, 20)
        self.sm_ord_slider.setValue(2)
        self.sm_ord_spin = QSpinBox()
        self.sm_ord_spin.setRange(1, 20)
        self.sm_ord_spin.setValue(2)
        self.sm_ord_spin.setMinimumWidth(60)
        self.sm_ord_slider.setToolTip('Same as the "Order" spin box, as a slider.')
        self.sm_ord_spin.setToolTip(SMOOTH_PARAM2_TOOLTIPS.get(self.smooth_combo.currentText()))
        self._link_slider_spinbox(self.sm_ord_slider, self.sm_ord_spin)
        hl2.addWidget(self.sm_ord_slider)
        hl2.addWidget(self.sm_ord_spin)
        smg_g.addLayout(hl2)
        sliders_l.addWidget(smg)

        # Matrix group: full 4x4 grid
        mxg = QGroupBox('Matrix (row=channel, col=base)')
        mxg.setToolTip(
            'Spectral overlap (crosstalk) matrix. Row = detected channel, '
            'column = fluorophore/base. Entry M[r][c] is how much of base '
            '"c" appears in channel "r". Used for spectral deconvolution '
            '(colour separation) of the raw trace. Diagonal entries should '
            'dominate with small off-diagonal bleed values.')
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
                sp.setRange(0.0, 5.0)
                sp.setSingleStep(0.01)
                sp.setDecimals(3)
                sp.setValue(float(DEFAULT_SPEC_MATRIX[r, c]))
                sp.setMinimumWidth(62)
                sp.setToolTip(
                    f'Crosstalk factor from base {base_labels[c]} into '
                    f'channel Ch{r}. 1.0 = full signal, near 0 = no bleed. '
                    f'May exceed 1.0 when a bleed channel is stronger than '
                    f'the primary channel for a base (e.g. a large blue '
                    f'crosstalk sitting under an A call).')
                if r == c:
                    sp.setStyleSheet('QDoubleSpinBox { font-weight: bold; }')
                sp.valueChanged.connect(self._schedule_update)
                mxg_g.addWidget(sp, r + 1, c + 1)
                self.mx_grid_spins[r][c] = sp
        preset_l = QHBoxLayout()
        for name, m in [('Default', DEFAULT_SPEC_MATRIX),
                        ('Identity', np.eye(4)),
                        ('Uniform', np.full((4, 4), 0.25))]:
            btn = QPushButton(name)
            btn.setToolTip(
                {'Default': 'Load the standard calibration crosstalk matrix.',
                 'Identity': 'No crosstalk - each channel is its own base '
                             '(ignore spectral bleed).',
                 'Uniform': 'Flat 0.25 matrix (worst case, rarely useful).'}[name])
            btn.clicked.connect(lambda checked, mm=m: self._set_matrix(mm))
            preset_l.addWidget(btn)
        mxg_g.addLayout(preset_l, 5, 0, 1, 5)
        sliders_l.addWidget(mxg)

        # Mobility shift group
        msg = QGroupBox('Mobility Shift (scans)')
        msg.setToolTip(
            'Mobility shift: a per-channel constant scan offset applied '
            'after matrix separation. Dye mobilities differ slightly, so '
            'the four base peaks for the same fragment land a few scans '
            'apart. Positive shifts a channel right (to later scans). '
            'Fine-tune by dragging the dashed coloured lines on the '
            'separated plot with "Drag shift lines" active.')
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
            sp.setToolTip(f'{label} mobility shift in scans. Positive moves '
                          f'this channel\'s peaks to later scan positions.')
            sp.valueChanged.connect(self._schedule_update)
            msg_g.addWidget(sp, i, 1)
            self.mobility_spins.append(sp)
        reset_shift_btn = QPushButton('Reset shifts')
        reset_shift_btn.setToolTip('Set all four mobility shifts back to 0.')
        reset_shift_btn.clicked.connect(self._reset_mobility_shifts)
        msg_g.addWidget(reset_shift_btn, 4, 0, 1, 2)
        sliders_l.addWidget(msg)

        # Peak detection group (for independent basecall)
        pdg = QGroupBox('Peak detection')
        pdg.setToolTip(
            'Settings for the independent basecaller (no ESD peak positions '
            'used). Distance is the minimum spacing between detected peaks, '
            'Prom x1000 the minimum prominence threshold, and Ambig % the '
            'IUPAC ambiguity window.')
        pdg_g = QGridLayout(pdg)
        pdg_g.setVerticalSpacing(4)
        self.method_combo = QComboBox()
        self.method_combo.addItems(['Greedy (max-intensity)',
                                    'Per-channel (cluster)',
                                    'Cimarron (tuned)',
                                    'Multiview (per-channel)'])
        self.method_combo.setToolTip(
            'Independent basecall strategy.\n\n'
            'Greedy (max-intensity): repeatedly call the strongest peak of '
            'the per-channel-normalized combined envelope, then excise a '
            'band around it. Most accurate on this data (88% vs 81% mean '
            'identity across the plate, better on all 96 wells). Uses '
            'Distance as the excise window and Prom x1000 as the minimum '
            'remaining-envelope fraction.\n\n'
            'Per-channel (cluster): detect peaks on each channel separately '
            'and merge near-coincident peaks into IUPAC ambiguity codes. '
            'Uses Distance, Prom, Ambig, Tolerance and Fill-in.\n\n'
            'Cimarron (tuned): runs the full cimarrontv.py Cimarron312 '
            'engine (port of the csibq030012.dll pipeline) end-to-end on the '
            'raw RSD channels with the validated tuned DSP: AsyLS baseline, '
            'Butterworth 5/9 smoothing, crosstalk separation, perbase '
            'begin/end detection and the greedy caller. ~95% identity vs the '
            'true M13 reference (DLL ~96%), best result achieved on this '
            'plate. Uses the current Matrix and Mobility Shifts from this '
            'GUI; baseline/smoothing knobs above do not affect this method.\n\n'
            'Multiview (per-channel): every channel gets its own Distance '
            'and Prominence (panel below), plus an optional combined-'
            'envelope view whose discoveries fill positions all four '
            'channels missed. Tune the per-channel numbers against the ESD '
            'with multiview_peakdetect.py and enter the optimized values '
            'here to watch the effect live.')
        pdg_g.addWidget(QLabel('Variant:'), 0, 2)
        pdg_g.addWidget(QLabel('Method:'), 0, 0)
        pdg_g.addWidget(self.method_combo, 0, 1)
        self.method_combo.currentIndexChanged.connect(self._on_method_changed)
        self.distance_spin = QDoubleSpinBox()
        self.distance_spin.setDecimals(2)
        self.distance_spin.setSingleStep(0.5)
        self.distance_spin.setToolTip(
            'Minimum horizontal distance between detected peaks, in scans. '
            'Peaks closer than this in the same channel are treated as one '
            'call. Too small = double-calls on noisy peaks; too large = '
            'misses real close bases. Decimals allowed (e.g. 4.63).')
        self.distance_spin.setRange(0.1, 1000.0)
        self.distance_spin.setValue(5.0)
        self.distance_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Distance:'), 1, 0)
        pdg_g.addWidget(self.distance_spin, 1, 1)
        self.prominence_spin = QSpinBox()
        self.prominence_spin.setToolTip(
            'Minimum prominence for a peak, shown as x1000 of the channel '
            'maximum (so 20 = 2.0% of the channel max). Prominence is how '
            'much a peak stands above its immediate surroundings, not its '
            'absolute height. Raise it to reject small baseline bumps.')
        self.prominence_spin.setRange(1, 10000)
        self.prominence_spin.setValue(20)
        self.prominence_spin.setSingleStep(5)
        self.prominence_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Prom x1000:'), 2, 0)
        pdg_g.addWidget(self.prominence_spin, 2, 1)
        # Ambiguous-window threshold: minimum secondary-peak height (as a %
        # of the dominant peak in a cluster) required for it to be merged
        # into an IUPAC ambiguity code instead of being ignored as noise.
        self.ambig_spin = QSpinBox()
        self.ambig_spin.setToolTip(
            'Ambiguous window: minimum height of a secondary peak, as a '
            'percentage of the dominant peak in the same cluster, needed '
            'for it to be merged into an IUPAC ambiguity code. For '
            'example, at 25% a minor bump reaching 15% of the main peak is '
            'treated as noise (fully unambiguous base), but a bump at 30% '
            'is a real co-eluting fragment (called e.g. M for A+C). Lower '
            '= more sensitive to weak under-peaks; higher = only merges '
            'strong secondary signals. Default 25%.')
        self.ambig_spin.setRange(1, 100)
        self.ambig_spin.setValue(25)
        self.ambig_spin.setSingleStep(5)
        self.ambig_spin.setSuffix(' %')
        self.ambig_spin.setMinimumWidth(70)
        self.ambig_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Ambig %:'), 3, 0)
        pdg_g.addWidget(self.ambig_spin, 3, 1)
        # Rolling local-max normalization window for the per-channel signal
        # (see pc_call_bases_with_shifts: each channel is divided by its
        # rolling local maximum). Sanger CE signals decay with fragment
        # length, so late peaks are systematically weaker; a smaller window
        # follows the decay more closely and equalizes early/late peak
        # heights, a larger window keeps more of the raw scale. This is the
        # "signal normalization for each channel" knob.
        self.norm_window_spin = QSpinBox()
        self.norm_window_spin.setRange(20, 4000)
        self.norm_window_spin.setValue(800)
        self.norm_window_spin.setSingleStep(50)
        self.norm_window_spin.setSuffix(' scans')
        self.norm_window_spin.setToolTip(
            'Rolling local-max window used to normalize each channel '
            'before peak detection. Each channel is divided by the running '
            'maximum over this window, which compensates for the signal '
            'decay across a Sanger run (early peaks stronger, late peaks '
            'weaker). Smaller = tracks the decay more tightly (more '
            'uniform peak heights); larger = closer to the raw signal. '
            'Default 800 scans.')
        self.norm_window_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Norm win:'), 4, 0)
        pdg_g.addWidget(self.norm_window_spin, 4, 1)
        # Cluster-merge tolerance: per-channel peaks within this many scans
        # of a cluster's start are treated as the same base (see
        # pc_call_bases_with_shifts). Too large and two adjacent real bases
        # on different channels (e.g. G~2493 / T~2496, only ~3 scans apart)
        # collapse into one call - the taller base swallows the weaker one.
        # Too small and a single noisy peak over-calls as several bases.
        self.tol_spin = QSpinBox()
        self.tol_spin.setRange(1, 20)
        self.tol_spin.setValue(4)
        self.tol_spin.setToolTip(
            'Cluster-merge tolerance, in scans: how far apart per-channel '
            'peaks must be to count as different bases. Peaks from any '
            'channels within this window are merged into one call and only '
            'the tallest survives (others may form an IUPAC ambiguity code). '
            'Default 4. Try 2-3 to stop closely-spaced cross-channel bases '
            '(like G~2493/T~2496) collapsing into one.')
        self.tol_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Tolerance:'), 5, 0)
        pdg_g.addWidget(self.tol_spin, 5, 1)
        # Fill-in detector: after the per-channel call, re-run peak finding
        # on the combined envelope and add any position clearly separated
        # from existing calls. Reverses the G~2493-type merge without the
        # false-peak flood of naive combined detection.
        self.fillin_check = QCheckBox()
        self.fillin_check.setToolTip(
            'Fill-in detector: re-detect peaks on the combined (max over '
            'shifted channels) envelope and add any position that is at '
            'least "Fill gap" scans from every per-channel call and has a '
            'clean dominant channel. Reverses the cluster-merge that drops '
            'a real base next to a taller one (e.g. G~2493 next to T~2496). '
            'Filled-in bases are drawn in orange.')
        self.fillin_check.setChecked(False)
        self.fillin_check.toggled.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Fill-in:'), 6, 0)
        pdg_g.addWidget(self.fillin_check, 6, 1)
        self.fill_gap_spin = QSpinBox()
        self.fill_gap_spin.setRange(1, 8)
        self.fill_gap_spin.setValue(3)
        self.fill_gap_spin.setToolTip(
            'Fill-in gap, in scans: a combined-envelope peak must sit at '
            'least this far from every existing per-channel call to be '
            'added as a new base. Smaller = more sensitive to the tight '
            'cross-channel pairs the merge drops; larger = fewer candidates. '
            'Default 3.')
        self.fill_gap_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Fill gap:'), 7, 0)
        pdg_g.addWidget(self.fill_gap_spin, 7, 1)
        self.fill_margin_spin = QSpinBox()
        self.fill_margin_spin.setRange(0, 100)
        self.fill_margin_spin.setValue(20)
        self.fill_margin_spin.setSingleStep(5)
        self.fill_margin_spin.setSuffix(' %')
        self.fill_margin_spin.setToolTip(
            'Fill-in margin: minimum dominance of the winning channel at a '
            'fill-in position, as a percentage of the combined-signal peak '
            '(winner minus runner-up, divided by winner). Low = accept '
            'noisier/shoulder positions; high = only add unambiguous bases. '
            'Default 20%.')
        self.fill_margin_spin.valueChanged.connect(self._schedule_update)
        pdg_g.addWidget(QLabel('Fill mrgn:'), 8, 0)
        pdg_g.addWidget(self.fill_margin_spin, 8, 1)
        # -- Multiview group: independent Distance/Prominence per channel
        # for the 'Multiview (per-channel)' method, plus the combined-
        # envelope view. Values are meant to come from
        # multiview_peakdetect.py's ESD optimization.
        mvg = QGroupBox('Multiview params')
        mvg.setToolTip(
            'Per-channel peak detection parameters for the Multiview '
            'method. Each row is one dye channel (A, C, G, T); COMB is '
            'the max-over-channels envelope whose peaks fill positions '
            'every channel missed (gated by Fill gap / Fill mrgn above). '
            'Optimized values: python3 multiview_peakdetect.py.')
        mv_g = QGridLayout(mvg)
        mv_g.setVerticalSpacing(2)
        self.mv_dist_spins = []
        self.mv_prom_spins = []
        mv_g.addWidget(QLabel(''), 0, 0)
        mv_g.addWidget(QLabel('Distance'), 0, 1)
        mv_g.addWidget(QLabel('Prom x1000'), 0, 2)
        labels = ['A', 'C', 'G', 'T']
        for ch in range(4):
            mv_g.addWidget(QLabel(labels[ch]), ch + 1, 0)
            dspin = QDoubleSpinBox()
            dspin.setDecimals(2)
            dspin.setSingleStep(0.5)
            dspin.setRange(0.1, 1000.0)
            dspin.setValue(6.0)
            dspin.valueChanged.connect(self._schedule_update)
            pspin = QSpinBox()
            pspin.setRange(1, 10000)
            pspin.setValue(75)
            pspin.setSingleStep(5)
            pspin.valueChanged.connect(self._schedule_update)
            self.mv_dist_spins.append(dspin)
            self.mv_prom_spins.append(pspin)
            mv_g.addWidget(dspin, ch + 1, 1)
            mv_g.addWidget(pspin, ch + 1, 2)
        mv_g.addWidget(QLabel('COMB'), 5, 0)
        self.mv_comb_check = QCheckBox()
        self.mv_comb_check.setChecked(True)
        self.mv_comb_check.toggled.connect(self._schedule_update)
        self.mv_comb_dist_spin = QDoubleSpinBox()
        self.mv_comb_dist_spin.setDecimals(2)
        self.mv_comb_dist_spin.setSingleStep(0.5)
        self.mv_comb_dist_spin.setRange(0.1, 1000.0)
        self.mv_comb_dist_spin.setValue(8.0)
        self.mv_comb_dist_spin.valueChanged.connect(self._schedule_update)
        self.mv_comb_prom_spin = QSpinBox()
        self.mv_comb_prom_spin.setRange(1, 10000)
        self.mv_comb_prom_spin.setValue(120)
        self.mv_comb_prom_spin.setSingleStep(5)
        self.mv_comb_prom_spin.valueChanged.connect(self._schedule_update)
        mv_g.addWidget(self.mv_comb_check, 5, 1)
        mv_g.addWidget(self.mv_comb_dist_spin, 5, 2)
        mv_g.addWidget(self.mv_comb_prom_spin, 5, 3)
        self.mv_group = mvg
        self._set_multiview_enabled(False)
        sliders_l.addWidget(mvg)
        sliders_l.addWidget(pdg)

        # -- Call-region group -- restrict normalization + basecalling to
        # the scan window that really contains sample signal. Everything
        # before the start is flat baseline, whose noise the rolling
        # normalization otherwise amplifies into false "peaks" in the
        # separated plot and into spurious base calls; everything at/after
        # the stop is the decaying tail. Auto mode derives both edges from
        # the separated trace; untick it to set From/To by hand.
        rg = QGroupBox('Call region')
        rg.setToolTip(
            'Restrict normalization and basecalling to the scan range that '
            'really contains sample signal. Before the start is flat '
            'baseline (its noise is amplified into false peaks by rolling '
            'normalization); at/after the stop is the decaying tail. '
            '"Auto-detect" derives both edges from the separated trace; '
            'untick it to set From/To by hand (0/0 = use the whole file).')
        rg_g = QGridLayout(rg)
        rg_g.setVerticalSpacing(4)
        self.region_auto_check = QCheckBox('Auto-detect start/stop')
        self.region_auto_check.setChecked(True)
        self.region_auto_check.toggled.connect(self._on_region_auto_toggled)
        rg_g.addWidget(self.region_auto_check, 0, 0, 1, 2)
        self.region_hybrid_check = QCheckBox('Hybrid tail (perbase end)')
        self.region_hybrid_check.setChecked(True)
        self.region_hybrid_check.setToolTip(
            'Auto mode: replace the looser legacy tail (10% of in-region max '
            'on the separated trace) with the Cimarron per-base end detector '
            'on the raw trace, trimmed by 120 scans. Cuts the decaying-noise '
            'tail that otherwise over-calls; ~+0.5pp NW on the 96-well plate.')
        self.region_hybrid_check.toggled.connect(self._schedule_update)
        rg_g.addWidget(self.region_hybrid_check, 1, 0, 1, 2)
        self.region_start_spin = QSpinBox()
        self.region_start_spin.setRange(0, 1000000)
        self.region_start_spin.setValue(0)
        self.region_start_spin.setToolTip(
            'First scan of the callable signal window (0 = start of file).')
        self.region_start_spin.valueChanged.connect(self._schedule_update)
        rg_g.addWidget(QLabel('From:'), 2, 0)
        rg_g.addWidget(self.region_start_spin, 2, 1)
        self.region_stop_spin = QSpinBox()
        self.region_stop_spin.setRange(0, 1000000)
        self.region_stop_spin.setValue(0)
        self.region_stop_spin.setToolTip(
            'Last scan of the callable signal window (0 = end of file).')
        self.region_stop_spin.valueChanged.connect(self._schedule_update)
        rg_g.addWidget(QLabel('To:'), 3, 0)
        rg_g.addWidget(self.region_stop_spin, 3, 1)
        sliders_l.addWidget(rg)

        # -- Matrix-stage tick boxes (narrow column left of the plots) --
        # Each graph has a tick box on its left marking the stage where the
        # crosstalk (dye-bleed) separation matrix is applied. The choices are
        # mutually exclusive; when none is ticked, no matrix is applied at all
        # and the raw 4 channels pass straight through to peak calling.
        # Mobility shifts are NOT shown in any graph - they are applied only
        # just before basecalling/peak detection.
        self._stage_cbs = {}
        stage_col = QWidget()
        stage_col.setFixedWidth(118)
        stage_col.setToolTip(
            'Tick the graph at the pipeline stage where the separation '
            'matrix is applied.\n'
            'Noise: pre-1500 noise floor subtracted, then matrix, then the '
            'chosen baseline (2-stage) floating graph only.\n'
            'Raw: raw --matrix--> baseline --smooth--> shift -> call\n'
            'Corrected: raw --baseline--> --matrix--> smooth -> shift -> call\n'
            'Smoothed: raw --baseline--> --smooth--> --matrix--> shift -> call\n'
            'No tick: no matrix applied (raw channels pass straight through).')
        stage_l = QVBoxLayout(stage_col)
        stage_l.setContentsMargins(2, 0, 2, 0)
        stage_l.setSpacing(0)
        stage_l.addWidget(QLabel('Matrix'), alignment=Qt.AlignHCenter)
        for _stage, _label in [('offset', 'on Noise+Mat'),
                               ('raw', 'on Raw'),
                               ('corrected', 'on Corrected'),
                               ('smoothed', 'on Smoothed'),
                               ('shifted', 'on Shifted')]:
            cb = QCheckBox(_label)
            cb.setToolTip(
                f'Apply the separation matrix to the {_label} signal.'
                if _stage != 'shifted' else
                'Apply the matrix AFTER mobility correction (shift each '
                'channel, then separate). Experimental A-B vs "on Smoothed".')
            cb.toggled.connect(lambda ck, s=_stage: self._on_stage_toggled(ck, s))
            self._stage_cbs[_stage] = cb
            stage_l.addWidget(cb, 1)
        stage_l.addWidget(QLabel(''), 1)

        # -- Plots -- (selection sidebar on the left, plot fills the rest),
        # inside a vertical splitter so the FASTA output below can be
        # enlarged/shrunk by dragging the border between plots and FASTA.
        self._h_splitter = QSplitter(Qt.Horizontal)
        self._h_splitter.setChildrenCollapsible(False)
        self._h_splitter.addWidget(sliders_scroll)
        self._h_splitter.addWidget(stage_col)
        self._h_splitter.addWidget(self.canvas)
        self._h_splitter.setStretchFactor(0, 0)
        self._h_splitter.setStretchFactor(1, 0)
        self._h_splitter.setStretchFactor(2, 1)
        self._h_splitter.setSizes([380, 110, 1000])
        self._plots_container = QWidget()
        plots_l = QVBoxLayout(self._plots_container)
        plots_l.setContentsMargins(0, 0, 0, 0)
        plots_l.setSpacing(2)
        plots_l.addWidget(self._h_splitter, 1)
        self._v_splitter = QSplitter(Qt.Vertical)
        self._v_splitter.setChildrenCollapsible(False)
        self._v_splitter.addWidget(self._plots_container)
        layout.addWidget(self._v_splitter)

        # -- Bottom bar --
        bottom = QHBoxLayout()
        self._plots_container.layout().addLayout(bottom)
        self.save_btn = QPushButton('Save processed data...')
        self.save_btn.setToolTip(
            'Export the processed traces (baseline, corrected, smoothed, '
            'separated) for the current well to a .npz file.')
        self.save_btn.clicked.connect(self._save_data)
        bottom.addWidget(self.save_btn)
        self.ml_btn = QPushButton('Run ML basecalling')
        self.ml_btn.setToolTip(
            'Run the trained neural-network basecaller on the separated '
            'trace and report its agreement with the ESD sequence.')
        self.ml_btn.clicked.connect(self._run_ml)
        bottom.addWidget(self.ml_btn)
        self.ml_fasta_btn = QPushButton('Export ML FASTA')
        self.ml_fasta_btn.setToolTip(
            'Write the last ML basecall (at ESD peak positions) to a FASTA '
            'file plus an alignment report vs both the ESD call and the '
            'true M13 reference.')
        self.ml_fasta_btn.clicked.connect(self._export_ml_fasta)
        self.ml_fasta_btn.setEnabled(False)
        bottom.addWidget(self.ml_fasta_btn)
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
            "ordinary sequencing read the channels carry different bases "
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
        self.cancel_opt_btn = QPushButton('Cancel optimization')
        self.cancel_opt_btn.setToolTip('Terminate the running optimization process.')
        self.cancel_opt_btn.clicked.connect(self._cancel_optimizer)
        self.cancel_opt_btn.setVisible(False)
        bottom.addWidget(self.cancel_opt_btn)
        self.overnight_cb = QCheckBox('Run overnight (all wells, deep search)')
        self.overnight_cb.setToolTip(
            'When ticked, the optimizer runs on EVERY well with many more '
            'iterations (it can take hours) so it explores far more of the '
            'parameter space. Leave it running over night / the weekend.')
        bottom.addWidget(self.overnight_cb)
        self.reset_btn = QPushButton('Reset view')
        self.reset_btn.setToolTip('Reset the plot zoom/pan back to the full view.')
        self.reset_btn.clicked.connect(self._reset_view)
        bottom.addWidget(self.reset_btn)
        self.drag_mode_btn = QPushButton('Drag shift lines')
        self.drag_mode_btn.setCheckable(True)
        self.drag_mode_btn.setToolTip(
            'Enable dragging colored vertical lines on the plot to adjust '
            'per-channel mobility shifts. The shift is computed relative to '
            'the current spin-box value and applied immediately.')
        self.drag_mode_btn.toggled.connect(self._on_drag_mode_toggled)
        self.drag_mode_btn.setVisible(False)
        bottom.addWidget(self.drag_mode_btn)
        self.call_btn = QPushButton('Run basecall')
        self.call_btn.setToolTip('Run independent peak-calling with current shifts and matrix')
        self.call_btn.clicked.connect(self._run_basecall)
        bottom.addWidget(self.call_btn)
        self.progress = QProgressBar()
        self.progress.setMaximumWidth(200)
        self.progress.setVisible(False)
        self.progress.setToolTip('Progress of the currently running '
                                 'optimization or batch task.')
        bottom.addWidget(self.progress)
        self.opt_log = QTextEdit()
        self.opt_log.setMaximumHeight(100)
        self.opt_log.hide()
        self.opt_log.setToolTip('Log output of the parameter optimizer.')
        bottom.addWidget(self.opt_log)
        bottom.addStretch()
        self.status = QLabel('Load a well to begin')
        self.status.setStyleSheet('color: gray;')
        bottom.addWidget(self.status)
        self._fasta_box = None  # set up in _build_fasta_section

        faasta = self._build_fasta_section()
        faasta.setMinimumHeight(70)
        self._v_splitter.addWidget(faasta)
        self._v_splitter.setStretchFactor(0, 1)
        self._v_splitter.setStretchFactor(1, 0)
        self._v_splitter.setSizes([700, 150])

        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(50)
        self._update_timer.timeout.connect(self._update_plot)

        # Apply the default method's parameter preset now that the widgets
        # and the update timer exist (Greedy is the default and the best on
        # this data).
        self._on_method_changed(self.method_combo.currentIndex())

        self._opt_worker = None

    def _build_fasta_section(self):
        grp = QGroupBox()
        grp.setFlat(True)
        grp.setToolTip(
            'Result of the independent basecall, shown as FASTA. Bases '
            'printed with IUPAC ambiguity codes (M/R/W/S/Y/K) are positions '
            'where a secondary peak reached the "Ambig %" threshold. Copy '
            'or save with the buttons on the right.')
        outer = QVBoxLayout(grp)
        outer.setContentsMargins(6, 4, 6, 4)
        outer.setSpacing(4)
        # Description and the ESD/Independent metric boxes share one line:
        # the metrics sit on the same row as the description, right after
        # the closing ")" of "(independent peak-call, IUPAC codes)".
        header = QHBoxLayout()
        header.setSpacing(10)
        title = QLabel('FASTA sequence (independent peak-call, IUPAC codes)')
        title.setStyleSheet('font-weight: bold;')
        header.addWidget(title)
        header.addWidget(self._build_metrics_row())
        header.addStretch()
        outer.addLayout(header)
        lay = QHBoxLayout()
        self._fasta_box = QTextEdit()
        self._fasta_box.setMinimumHeight(40)
        self._fasta_box.setReadOnly(True)
        self._fasta_box.setPlaceholderText('Run independent peak-call to see sequence here')
        self._fasta_box.setToolTip(
            'Called sequence with IUPAC ambiguity codes. Highlight and '
            'copy, or use the Copy / Save FASTA buttons.')
        lay.addWidget(self._fasta_box, stretch=1)
        copy_btn = QPushButton('Copy')
        copy_btn.setToolTip('Copy FASTA to clipboard')
        copy_btn.clicked.connect(self._copy_fasta)
        lay.addWidget(copy_btn)
        save_seq_btn = QPushButton('Save FASTA...')
        save_seq_btn.setToolTip('Save FASTA sequence to a file')
        save_seq_btn.clicked.connect(self._save_fasta)
        lay.addWidget(save_seq_btn)
        outer.addLayout(lay)
        return grp

    def _build_metrics_row(self):
        """Two plain-text metric labels (ESD match / Independent bases) shown
        on the same line as the FASTA description, right after its closing
        ")":  FASTA sequence (...)  ESD match: 94.6%  Independent: 81.8%.
        Hover tooltips explain what each metric means."""
        row = QWidget()
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        self._esd_metric_label = QLabel('ESD match: --')
        self._esd_metric_label.setToolTip(METRIC_TOOLTIPS['ESD match'])
        self._esd_metric_label.setStyleSheet(
            'color: #0033cc; font-weight: bold;')
        lay.addWidget(self._esd_metric_label)
        self._indep_metric_label = QLabel('Independent: --')
        self._indep_metric_label.setToolTip(METRIC_TOOLTIPS['Independent'])
        self._indep_metric_label.setStyleSheet(
            'color: #1a7a1a; font-weight: bold;')
        lay.addWidget(self._indep_metric_label)
        lay.addStretch()
        return row

    def _update_fasta_box(self, sequence):
        if not sequence:
            self._fasta_box.setText('')
            return
        well = self.current_well or 'unknown'
        header = f'>{well}_manual'
        wrapped = '\n'.join(sequence[i:i + 80] for i in range(0, len(sequence), 80))
        self._fasta_box.setText(f'{header}\n{wrapped}')
        self._fasta_box.setReadOnly(True)

    def _reference_local_identity(self, sequence):
        """Concordance of a basecall with the true reference sequence.

        BLAST-style local (Smith-Waterman) identity against the stored
        reference slice (reference_dna[reference_start-1:reference_end]),
        best strand chosen automatically. Returns a float percent, or None
        when no reference is configured."""
        ref = getattr(self, 'reference_dna', '')
        lo = getattr(self, 'reference_start', 0)
        hi = getattr(self, 'reference_end', 0)
        if not ref or hi <= lo or not sequence:
            return None
        ref_slice = ref[lo - 1:hi]
        if not ref_slice:
            return None
        fwd = ref_local_identity(sequence, ref_slice)
        rev = ref_local_identity(_ref_revcomp(sequence), ref_slice)
        best = rev if rev[5] >= fwd[5] else fwd
        return float(best[0])

    def _copy_fasta(self):
        if self._fasta_box and self._fasta_box.toPlainText():
            clipboard = QApplication.clipboard()
            clipboard.setText(self._fasta_box.toPlainText())
            self.status.setText('FASTA sequence copied to clipboard')
            QTimer.singleShot(3000, lambda: self.status.setText(
                f'{self.current_well}: ready' if self.rsd_raw else 'Load a well to begin'))

    def _save_fasta(self):
        if not self._manual_sequence:
            return
        from PyQt5.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, 'Save FASTA', '',
                                               'FASTA Files (*.fasta *.fa *.fna);;All Files (*)')
        if not path:
            return
        well = self.current_well or 'unknown'
        header = f'>{well}_manual'
        wrapped = '\n'.join(self._manual_sequence[i:i + 80]
                            for i in range(0, len(self._manual_sequence), 80))
        with open(path, 'w') as f:
            f.write(header + '\n')
            f.write(wrapped + '\n')
        self.status.setText(f'Saved FASTA to {path}')

    def _link_slider_spinbox(self, slider, spinbox):
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
        self._settings.setValue('baseline_window2', self.bl2_spin.value())
        self._settings.setValue('smooth_method', self.smooth_combo.currentText())
        self._settings.setValue('smooth_window', self.sm_win_spin.value())
        self._settings.setValue('smooth_order', self.sm_ord_spin.value())
        self._settings.setValue('matrix_apply_point', self._get_matrix_apply_point())
        self._settings.setValue('min_distance', self.distance_spin.value())
        self._settings.setValue('prominence_frac', self.prominence_spin.value())
        self._settings.setValue('min_signal_frac', self.ambig_spin.value())
        self._settings.setValue('tolerance', self.tol_spin.value())
        self._settings.setValue('fill_in', self.fillin_check.isChecked())
        self._settings.setValue('fill_gap', self.fill_gap_spin.value())
        self._settings.setValue('fill_margin', self.fill_margin_spin.value())
        self._settings.setValue('basecall_method', self.method_combo.currentIndex())
        for ch in range(4):
            self._settings.setValue(f'mv_dist_{ch}',
                                    self.mv_dist_spins[ch].value())
            self._settings.setValue(f'mv_prom_{ch}',
                                    self.mv_prom_spins[ch].value())
        self._settings.setValue('mv_comb_on', self.mv_comb_check.isChecked())
        self._settings.setValue('mv_comb_dist', self.mv_comb_dist_spin.value())
        self._settings.setValue('mv_comb_prom', self.mv_comb_prom_spin.value())
        self._settings.setValue('esd_offset', self.esd_offset_spin.value())
        if hasattr(self, 'esd_combo'):
            self._settings.setValue('esd_variant', self.esd_combo.currentText())
        for r in range(4):
            for c in range(4):
                self._settings.setValue(f'matrix_{r}_{c}',
                                        self.mx_grid_spins[r][c].value())
        for ch in range(4):
            self._settings.setValue(f'mobility_shift_{ch}',
                                    self.mobility_spins[ch].value())
        self._settings.setValue('region_auto', self.region_auto_check.isChecked())
        self._settings.setValue('region_hybrid', self.region_hybrid_check.isChecked())
        self._settings.setValue('region_start', self.region_start_spin.value())
        self._settings.setValue('region_stop', self.region_stop_spin.value())

    def _restore_settings(self):
        def restore_combo(combo, key, default):
            val = self._settings.value(key, default)
            idx = combo.findText(val)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        def restore_spin(spin, key, default):
            spin.setValue(int(self._settings.value(key, default)))
        def restore_dspin(spin, key, default):
            spin.setValue(float(self._settings.value(key, default)))
        restore_combo(self.baseline_combo, 'baseline_method', 'Rolling Minimum')
        restore_spin(self.bl_spin, 'baseline_window', 200)
        restore_spin(self.bl2_spin, 'baseline_window2', 1)
        restore_combo(self.smooth_combo, 'smooth_method', 'Savitzky-Golay')
        restore_spin(self.sm_win_spin, 'smooth_window', 7)
        restore_spin(self.sm_ord_spin, 'smooth_order', 2)
        self._on_smooth_method_changed(self.smooth_combo.currentText())
        _method = self._settings.value('basecall_method', 0)
        try:
            self.method_combo.setCurrentIndex(int(_method))
        except (TypeError, ValueError):
            self.method_combo.setCurrentIndex(0)
        restore_dspin(self.distance_spin, 'min_distance', 5)
        restore_spin(self.prominence_spin, 'prominence_frac', 200)
        restore_spin(self.ambig_spin, 'min_signal_frac', 25)
        restore_spin(self.tol_spin, 'tolerance', 4)
        restore_spin(self.fill_gap_spin, 'fill_gap', 3)
        restore_spin(self.fill_margin_spin, 'fill_margin', 20)
        for ch in range(4):
            restore_dspin(self.mv_dist_spins[ch], f'mv_dist_{ch}', 6.0)
            restore_spin(self.mv_prom_spins[ch], f'mv_prom_{ch}', 75)
        restore_dspin(self.mv_comb_dist_spin, 'mv_comb_dist', 8.0)
        restore_spin(self.mv_comb_prom_spin, 'mv_comb_prom', 120)
        _mvcomb = self._settings.value('mv_comb_on', True)
        self.mv_comb_check.setChecked(
            _mvcomb in (True, 'true', 'True', '1', 1))
        _fillin_val = self._settings.value('fill_in', False)
        self.fillin_check.setChecked(_fillin_val in (True, 'true', 'True', '1', 1))
        mpa = self._settings.value('matrix_apply_point', 'smoothed')
        self._set_matrix_apply_point(mpa)
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
        if hasattr(self, 'esd_offset_spin'):
            restore_spin(self.esd_offset_spin, 'esd_offset', 0)
        _region_auto = self._settings.value('region_auto', True)
        self.region_auto_check.setChecked(
            _region_auto in (True, 'true', 'True', '1', 1))
        _region_hybrid = self._settings.value('region_hybrid', True)
        self.region_hybrid_check.setChecked(
            _region_hybrid in (True, 'true', 'True', '1', 1))
        restore_spin(self.region_start_spin, 'region_start', 0)
        restore_spin(self.region_stop_spin, 'region_stop', 0)
        self._on_region_auto_toggled(self.region_auto_check.isChecked())

    def closeEvent(self, event):
        self._save_settings()
        super().closeEvent(event)

    # ------------------------------------------------------------------
    # Manual shift line dragging
    # ------------------------------------------------------------------

    def _on_drag_mode_toggled(self, checked):
        if checked:
            self.status.setText('Drag mode: click a colored line on the separated plot to adjust')
            self.drag_mode_btn.setText('✓ Drag mode')
        else:
            self.drag_mode_btn.setText('Drag shift lines')
            self.status.setText('Drag mode off')
            if self._drag_channel is not None:
                self._drag_channel = None
                self._schedule_update()

    def _on_canvas_press(self, event):
        if not self.drag_mode_btn.isChecked() or event.button != 1:
            return
        if event.inaxes is None:
            return
        ax = event.inaxes
        # Only allow dragging on ax3 (separated plot, subplot index 3 = 4th)
        axes_list = self.fig.axes
        if ax not in axes_list or axes_list.index(ax) != 2:
            return
        x = event.xdata
        if x is None:
            return
        # Find nearest draggable line (one per channel, drawn as dashed vlines)
        if not hasattr(self, '_shift_lines') or not self._shift_lines:
            self._draw_shift_lines(ax)
        best_ch = -1
        best_dist = 50
        for ch, (line, _) in self._shift_lines.items():
            lx = line.get_xdata()[0]
            dist = abs(lx - x)
            if dist < best_dist:
                best_dist = dist
                best_ch = ch
        if best_ch < 0:
            self._drag_channel = None
            return
        self._drag_channel = best_ch
        self._drag_start_x = x
        self._shift_lines[best_ch][0].set_linewidth(2.0)
        self.canvas.draw()

    def _on_canvas_move(self, event):
        if self._drag_channel is None or event.inaxes is None:
            return
        x = event.xdata
        if x is None:
            return
        line, base_pos = self._shift_lines[self._drag_channel]
        line.set_xdata([x])
        self.canvas.draw_idle()

    def _on_canvas_release(self, event):
        if self._drag_channel is None:
            return
        ch = self._drag_channel
        line, base_pos = self._shift_lines[ch]
        new_x = line.get_xdata()[0]
        delta = int(new_x - base_pos)
        if delta != 0:
            new_val = self.mobility_spins[ch].value() + delta
            new_val = max(self.mobility_spins[ch].minimum(),
                          min(self.mobility_spins[ch].maximum(), new_val))
            self.mobility_spins[ch].blockSignals(True)
            self.mobility_spins[ch].setValue(new_val)
            self.mobility_spins[ch].blockSignals(False)
        self._drag_channel = None
        self._schedule_update()

    def _draw_shift_lines(self, ax):
        """Draw a dashed vertical line for each channel at the position of
        that channel's tallest peak, or at a fixed reference. The line's
        x-position represents the channel's current effective shift."""
        if not hasattr(self, '_shift_lines'):
            self._shift_lines = {}
        for line in self._shift_lines.values():
            line[0].remove()
        self._shift_lines.clear()
        separated = getattr(self, '_last_separated', None)
        shifts = self._effective_shifts()
        for ch in range(4):
            if separated is not None and separated[:, ch].max() > 0:
                ref_pos = int(np.argmax(separated[:, ch]))
            else:
                ref_pos = 100
            line = ax.axvline(x=ref_pos, color=CHAN_COLORS[ch],
                               linestyle='--', linewidth=1.5, alpha=0.8,
                               label=f'{BASE_LETTERS[ch]} shift={shifts[ch]}')
            self._shift_lines[ch] = (line, ref_pos)

    # ------------------------------------------------------------------
    # Automated / explicit basecalling
    # ------------------------------------------------------------------

    def _run_basecall(self):
        """Run the independent peak-call with current settings and update
        the FASTA box, plot, and status. Can be called programmatically:

            gui = SequencingGUI()
            gui._load_data_with_path(rsd_path, esd_path)
            gui._run_basecall()
        """
        if self.rsd_raw is None:
            self.status.setText('Load a well first')
            return
        result = self._process()
        if result is None:
            return
        raw, bl, corr, sm, separated, mix = result
        self._last_separated = separated
        shifts = self._effective_shifts()
        region = self._get_region(separated)
        try:
            # Pass unshifted `separated` - the caller applies the mobility
            # shift itself. See the note in _update_plot for why passing an
            # already-shifted trace here double-applies it.
            pos, seq, groups, ints = self._call_bases(separated, shifts, region)
            self._manual_sequence = seq
            self._update_fasta_box(seq)
            self.status.setText(f'Basecalled {len(seq)} bases with IUPAC codes')
        except Exception as e:
            self.status.setText(f'Basecall error: {e}')
        self._schedule_update()

    def load_settings_from_dict(self, settings_dict):
        """Programmatic API: apply a dict of settings and refresh.
        Keys: baseline_method, baseline_window, smooth_method,
        smooth_window, smooth_order, matrix (4x4 list),
        mobility_shifts (4-list of ints)."""
        if 'baseline_method' in settings_dict:
            idx = self.baseline_combo.findText(settings_dict['baseline_method'])
            if idx >= 0:
                self.baseline_combo.setCurrentIndex(idx)
        if 'baseline_window' in settings_dict:
            self.bl_spin.setValue(int(settings_dict['baseline_window']))
        if 'baseline_window2' in settings_dict:
            self.bl2_spin.setValue(int(settings_dict['baseline_window2']))
        if 'smooth_method' in settings_dict:
            idx = self.smooth_combo.findText(settings_dict['smooth_method'])
            if idx >= 0:
                self.smooth_combo.setCurrentIndex(idx)
        if 'smooth_window' in settings_dict:
            self.sm_win_spin.setValue(int(settings_dict['smooth_window']))
        if 'smooth_order' in settings_dict:
            self.sm_ord_spin.setValue(int(settings_dict['smooth_order']))
        if 'matrix_apply_point' in settings_dict:
            self._set_matrix_apply_point(str(settings_dict['matrix_apply_point']))
        if 'norm_window' in settings_dict:
            self.norm_window_spin.setValue(
                max(1, int(round(float(settings_dict['norm_window'])))))
        if 'min_distance' in settings_dict:
            self.distance_spin.setValue(float(settings_dict['min_distance']))
        if 'basecall_method' in settings_dict:
            idx = int(settings_dict['basecall_method'])
            if 0 <= idx < self.method_combo.count():
                self.method_combo.setCurrentIndex(idx)
        if 'prominence_frac' in settings_dict:
            self.prominence_spin.setValue(int(round(float(settings_dict['prominence_frac']) * 1000.0)))
        if 'min_signal_frac' in settings_dict:
            self.ambig_spin.setValue(int(round(float(settings_dict['min_signal_frac']) * 100.0)))
        if 'tolerance' in settings_dict:
            self.tol_spin.setValue(int(settings_dict['tolerance']))
        if 'fill_in' in settings_dict:
            self.fillin_check.setChecked(bool(settings_dict['fill_in']))
        if 'fill_gap' in settings_dict:
            self.fill_gap_spin.setValue(int(settings_dict['fill_gap']))
        if 'fill_margin' in settings_dict:
            self.fill_margin_spin.setValue(int(round(float(settings_dict['fill_margin']) * 100.0)))
        mv_src = settings_dict.get('multiview') or settings_dict
        if 'ch_params' in mv_src:
            for ch, pair in enumerate(mv_src['ch_params'][:4]):
                self.mv_dist_spins[ch].setValue(float(pair[0]))
                self.mv_prom_spins[ch].setValue(int(pair[1]))
            comb = mv_src.get('comb_params')
            if comb:
                self.mv_comb_dist_spin.setValue(float(comb[0]))
                self.mv_comb_prom_spin.setValue(int(comb[1]))
                self.mv_comb_check.setChecked(True)
            else:
                self.mv_comb_check.setChecked(False)
        if 'matrix' in settings_dict:
            self._set_matrix(np.array(settings_dict['matrix']))
        if 'mobility_shifts' in settings_dict:
            for ch, val in enumerate(settings_dict['mobility_shifts']):
                self.mobility_spins[ch].setValue(int(val))
        if 'esd_offset' in settings_dict:
            self.esd_offset_spin.setValue(int(settings_dict['esd_offset']))
        if 'reference_dna' in settings_dict:
            self.reference_dna = str(settings_dict['reference_dna'])
        if 'reference_name' in settings_dict:
            self.reference_name = str(settings_dict['reference_name'])
        if 'reference_start' in settings_dict:
            self.reference_start = int(settings_dict['reference_start'])
        if 'reference_end' in settings_dict:
            self.reference_end = int(settings_dict['reference_end'])
        if 'basecall_method' not in settings_dict:
            # Legacy settings (no method key): land on the selected method's
            # factory parameter preset instead of the per-channel-tuned
            # values the old files carried, so the new default (Greedy) runs
            # with its validated parameters.
            self._on_method_changed(self.method_combo.currentIndex())
        self._save_settings()
        self._schedule_update()

    def _save_settings_to_file(self):
        """Export all current settings to a human-readable JSON text file so
        the basecall can be reproduced later or on another machine."""
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save settings', 'settings.json',
            'JSON files (*.json);;All Files (*)')
        if not path:
            return
        settings = self.get_settings()
        settings['well'] = self.well_combo.currentText().strip()
        settings['esd_variant'] = self.esd_combo.currentText()
        try:
            with open(path, 'w') as f:
                json.dump(settings, f, indent=2, sort_keys=True)
        except Exception as e:
            self.status.setText(f'Could not save settings: {e}')
            return
        self.status.setText(f'Settings saved to {path}')

    def _load_settings_from_file(self):
        """Read a settings JSON text file and apply it, then reload the well
        it was saved from so the results reproduce exactly."""
        path, _ = QFileDialog.getOpenFileName(
            self, 'Load settings', '',
            'JSON files (*.json);;All Files (*)')
        if not path:
            return
        try:
            with open(path) as f:
                settings = json.load(f)
        except Exception as e:
            self.status.setText(f'Could not read settings: {e}')
            return
        if not isinstance(settings, dict):
            self.status.setText('Not a valid settings file')
            return
        if 'esd_variant' in settings:
            idx = self.esd_combo.findText(str(settings['esd_variant']))
            if idx >= 0:
                self.esd_combo.setCurrentIndex(idx)
        if 'well' in settings:
            self.well_combo.setCurrentText(str(settings['well']))
        self.load_settings_from_dict(settings)
        if self.rsd_raw is None or self.current_well != str(
                settings.get('well', '')).strip():
            self._load_data()
        self.status.setText(f'Settings loaded from {path}')

    def _write_init_json(self):
        """Write current GUI settings to a temp JSON file and return its path
        for passing to optimize_params.py via --init-json."""
        if self.rsd_raw is None:
            return None
        try:
            settings = self.get_settings()
            path = os.path.join(tempfile.mkdtemp(prefix='gui_init_'),
                                'current_settings.json')
            with open(path, 'w') as f:
                json.dump(settings, f)
            return path
        except Exception:
            return None

    def get_settings(self):
        """Return current settings as a dict for automation/saving."""
        return {
            'baseline_method': self.baseline_combo.currentText(),
            'baseline_window': self.bl_spin.value(),
            'baseline_window2': self.bl2_spin.value(),
            'smooth_method': self.smooth_combo.currentText(),
            'smooth_window': self.sm_win_spin.value(),
            'smooth_order': self.sm_ord_spin.value(),
            'norm_window': self.norm_window_spin.value(),
            'matrix_apply_point': self._get_matrix_apply_point(),
            'basecall_method': self.method_combo.currentIndex(),
            'min_distance': self.distance_spin.value(),
            'prominence_frac': self.prominence_spin.value() / 1000.0,
            'min_signal_frac': self.ambig_spin.value() / 100.0,
            'tolerance': self.tol_spin.value(),
            'fill_in': self.fillin_check.isChecked(),
            'fill_gap': self.fill_gap_spin.value(),
            'fill_margin': self.fill_margin_spin.value() / 100.0,
            'multiview': {
                'ch_params': [[self.mv_dist_spins[c].value(),
                               self.mv_prom_spins[c].value()]
                              for c in range(4)],
                'comb_params': [self.mv_comb_dist_spin.value(),
                                self.mv_comb_prom_spin.value()]
                if self.mv_comb_check.isChecked() else None,
            },
            'matrix': self._get_matrix().tolist(),
            'mobility_shifts': self._get_mobility_shifts(),
            'esd_offset': self.esd_offset_spin.value(),
            'reference_name': self.reference_name,
            'reference_start': self.reference_start,
            'reference_end': self.reference_end,
            'reference_dna': self.reference_dna,
        }

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
        self.smooth_combo.setToolTip(SMOOTH_TOOLTIPS.get(method))
        self.sm_param1_label.setToolTip(SMOOTH_PARAM1_TOOLTIPS.get(method))
        self.sm_win_spin.setToolTip(SMOOTH_PARAM1_TOOLTIPS.get(method))
        self.sm_param2_label.setToolTip(SMOOTH_PARAM2_TOOLTIPS.get(method))
        self.sm_ord_spin.setToolTip(SMOOTH_PARAM2_TOOLTIPS.get(method))
        self._schedule_update()

    def _on_baseline_method_changed(self, method):
        cfg = BASELINE_PARAM_CONFIG.get(
            method, ('Window:', (20, 1000), None, None))
        label1, rng1, label2, rng2 = cfg
        self.bl_param_label.setText(label1)
        self.bl_spin.setRange(*rng1)
        self.bl_slider.setRange(*rng1)
        if method == 'None':
            self.bl_spin.setEnabled(False)
            self.bl_slider.setEnabled(False)
            self.bl2_param_label.setVisible(False)
            self.bl2_slider.setVisible(False)
            self.bl2_spin.setVisible(False)
            self._schedule_update()
            return
        self.bl_spin.setEnabled(True)
        self.bl_slider.setEnabled(True)
        self.bl_spin.setValue(int(np.mean(rng1)))
        self.bl_slider.setValue(int(np.mean(rng1)))
        if label2 is not None and rng2 is not None:
            self.bl2_param_label.setText(label2)
            self.bl2_param_label.setVisible(True)
            self.bl2_slider.setVisible(True)
            self.bl2_spin.setVisible(True)
            self.bl2_param_label.setToolTip(f'{label2} for {method}')
            self.bl2_slider.setToolTip(f'{label2} for {method}')
            self.bl2_spin.setToolTip(f'{label2} for {method}')
            self.bl2_slider.setRange(*rng2)
            self.bl2_spin.setRange(*rng2)
            self.bl2_spin.setValue(int(np.mean(rng2)))
            self.bl2_slider.setValue(int(np.mean(rng2)))
        else:
            self.bl2_param_label.setVisible(False)
            self.bl2_slider.setVisible(False)
            self.bl2_spin.setVisible(False)
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

    def _select_data_folder(self):
        """Let the user pick the folder containing .rsd files and the
        per-run ESD subfolders. Repopulates wells and saves the choice."""
        folder = QFileDialog.getExistingDirectory(
            self, 'Select Data Folder', self.data_dir)
        if not folder:
            return
        self.data_dir = folder
        self.data_dir_label.setText(folder)
        self._settings.setValue('data_dir', folder)
        self._populate_wells()
        n = self.well_combo.count()
        if n == 0:
            self.status.setText(
                f'No .rsd files found in {folder}. Pick the folder that '
                'contains the .rsd files (they live in a MB1000_M13_DT '
                'folder, with ESD subfolders like *_MD1 inside).')
        else:
            self.status.setText(
                f'Data folder set to {folder} — {n} wells found')

    def _populate_wells(self):
        if os.path.isdir(self.data_dir):
            wells = sorted(f[:-4] for f in os.listdir(self.data_dir)
                           if f.endswith('.rsd'))
            self.well_combo.clear()
            self.well_combo.addItems(wells)
            if 'A01' in wells:
                self.well_combo.setCurrentText('A01')
        else:
            self.well_combo.clear()
        subdirs = find_esd_subdirs(self.data_dir) if os.path.isdir(self.data_dir) else {}
        self.esd_combo.clear()
        for k in sorted(subdirs):
            self.esd_combo.addItem(k, subdirs[k])
        if self.esd_combo.count() > 0:
            cp312_idx = None
            for i in range(self.esd_combo.count()):
                if self.esd_combo.itemText(i) == 'Cp312':
                    cp312_idx = i
                    break
            if cp312_idx is None:
                cp312_idx = self.esd_combo.findText('Cp312')
            if cp312_idx >= 0:
                self.esd_combo.setCurrentIndex(cp312_idx)
            else:
                self.esd_combo.setCurrentIndex(0)

    def _load_data(self):
        well = self.well_combo.currentText().strip()
        if not well:
            return
        rsd_path = os.path.join(self.data_dir, f'{well}.rsd')
        esd_subdir = self.esd_combo.currentData() or ''
        esd_path = os.path.join(self.data_dir, esd_subdir, f'{well}.esd')
        if not os.path.exists(rsd_path):
            self.status.setText(f'Missing: {rsd_path}')
            return
        if not os.path.exists(esd_path):
            self.status.setText(f'Missing: {esd_path}')
            return
        try:
            df = parse_rsd(rsd_path)
            self.rsd_raw = df[['Channel1', 'Channel2', 'Channel3',
                               'Channel4']].values.astype(np.float64)
            self.x_rsd = np.arange(len(self.rsd_raw))
            self.esd_data = parse_esd(esd_path)
            self._load_esd_traces(esd_path)
            self.x_esd = np.arange(len(self.esd_traces))
            self.esd_offset = self._estimate_esd_offset(
                self.esd_data.get('peak_positions'), self.esd_traces)
            self.esd_offset_spin.blockSignals(True)
            self.esd_offset_spin.setValue(int(self.esd_offset))
            self.esd_offset_spin.blockSignals(False)
            self.current_well = well
            n_peaks = len(self.esd_data.get('peak_positions', []))
            # Sanity-check the chosen ESD variant: peak_positions are supposed
            # to sit on the same (positive-scan) coordinate grid as the RSD
            # trace. A wrong variant (e.g. a calibration or alternate call
            # variant) can put peaks at negative/absurd scans, which swings the
            # estimated offset and visibly misaligns the ESD row under our
            # basecall. Catch that here instead of silently plotting rubbish.
            warning = ''
            n_scans = len(self.rsd_raw)
            pp = self.esd_data.get('peak_positions')
            peak_arr = np.asarray(pp, dtype=np.int64) if pp is not None else np.array([], dtype=np.int64)
            if len(peak_arr) > 0:
                pmin, pmax = int(peak_arr.min()), int(peak_arr.max())
                # Peaks must sit on the positive RSD scan grid and span a
                # plausible region (not all clustered or off-grid).
                if pmin < 0 or pmax - pmin < 10:
                    warning = ('  // MISALIGNED ESD: peak positions out of '
                               'range? Try the "Cp312" ESD variant.')
                elif not (0 <= pmin < n_scans and 0 < pmax <= n_scans + 2000):
                    warning = ('  // MISALIGNED ESD: peaks fall outside the '
                               'RSD scan grid. Check the ESD variant '
                               '(expected ~Cp312).')
            # Offset sanity: with the correct variant the ESD trace aligns
            # somewhere in the body of the RSD trace. An offset at the extreme
            # ends (near 0 or near n_scans) means the alignment degenerated,
            # e.g. a wrong ESD variant driving the offset to the trace edge.
            if not warning:
                if self.esd_offset < 0:
                    warning = ('  // MISALIGNED ESD: negative offset. Check '
                               'the ESD variant (expected ~Cp312).')
                elif n_scans > 0 and self.esd_offset > 0.85 * n_scans:
                    warning = ('  // MISALIGNED ESD: offset at the trace '
                               'edge. Check the ESD variant (expected '
                               '~Cp312).')
            self.status.setText(
                f'{well}: RSD {len(self.rsd_raw)} scans, '
                f'ESD {len(self.esd_traces)} recs, {n_peaks} peaks, '
                f'offset~{self.esd_offset}{warning}')
            self._update_plot()
            self.drag_mode_btn.setVisible(True)
        except Exception as e:
            self.status.setText(f'Error: {e}')
            import traceback
            traceback.print_exc()

    def _estimate_esd_offset(self, peak_positions, esd_traces):
        """Find the constant shift that puts the largest total amplitude
        of the ESD envelope at the ESD-labeled peak positions.

        The ESD basecaller's peak_positions are already on the correct
        coordinate for the RSD trace. But esd_traces (the raw per-record
        amplitude array) starts at record 0 independently, so it doesn't
        line up under those labels. We search for the offset that
        maximizes the average envelope amplitude at the labeled positions."""
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
        best_offset = max(
            range(best_offset - coarse_step, best_offset + coarse_step + 1),
            key=score)
        return int(best_offset)

    def _shift_channel(self, arr, shift):
        """Shift a 1-D channel trace by ``shift`` scans, padding with the
        edge value instead of wrapping (np.roll wraps, smearing the end
        of the trace into the start)."""
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
        """ESD-called peak positions are systematically shifted left of the
        true apex. Search a small window (mostly forward) around the called
        index and return the position of maximum channel intensity.

        Callers with closely-spaced peaks should shrink `fwd`/`back` to
        roughly half the gap to the neighboring peak (see the ax4 label
        loop). Without that, this window can overshoot past the true apex
        in dense regions and lock onto a *neighboring* peak instead -
        which visibly misplaces the label onto the wrong peak."""
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
                ch = tuple(0.0 if (np.isnan(c) or np.isinf(c) or abs(c) > 1000)
                           else max(0.0, c) for c in ch)
                esd_traces[i] = ch
            except Exception:
                esd_traces[i] = 0.0
        max_per_rec = esd_traces.max(axis=1)
        spikes = np.where(max_per_rec > 5)[0]
        if len(spikes) > 0:
            clean_end = spikes[0]
            clean_max = max_per_rec[:clean_end]
            if len(clean_max) > 0:
                limit = float(np.percentile(clean_max, 99.9))
                if 0 < limit < 1000:
                    esd_traces = np.clip(esd_traces, 0, limit)
        non_zero = np.any(esd_traces > 0, axis=1)
        if non_zero.any():
            last_nz = np.where(non_zero)[0][-1]
            self.esd_traces = esd_traces[:last_nz + 50]
        else:
            self.esd_traces = esd_traces

    def _process(self):
        """Thin wrapper around dsp_full_pipeline, reading current widget values.

        Mobility shifts are NOT applied inside the pipeline (so baseline,
        smoothing, and matrix inversion operate on the raw aligned signal).
        Shifts are applied separately to the separated trace for display
        and peak-calling only."""
        if self.rsd_raw is None:
            return None
        return dsp_full_pipeline(
            self.rsd_raw,
            self._effective_shifts(),
            self.baseline_combo.currentText(),
            self.bl_spin.value(),
            self._smooth_mode,
            self.sm_win_spin.value(),
            self.sm_ord_spin.value(),
            self._get_matrix(),
            self.bl2_spin.value() if self.bl2_spin else None,
            self._get_matrix_apply_point(),
        )

    def _on_stage_toggled(self, checked, stage):
        """Keep the matrix-stage tick boxes mutually exclusive while still
        allowing all of them to be unticked ('no matrix')."""
        if checked:
            for s, cb in self._stage_cbs.items():
                if s != stage and cb.isChecked():
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
        self._schedule_update()

    def _get_matrix_apply_point(self):
        """Stage where the separation matrix is applied, from the per-graph
        tick boxes. Returns 'none' when no box is ticked (no matrix)."""
        if not hasattr(self, '_stage_cbs') or not self._stage_cbs:
            return 'smoothed'
        for stage, cb in self._stage_cbs.items():
            if cb.isChecked():
                return stage
        return 'none'

    def _set_matrix_apply_point(self, stage):
        """Set the matrix-application stage from the tick boxes (used when
        loading saved settings). 'none' untics every box."""
        if not hasattr(self, '_stage_cbs') or not self._stage_cbs:
            return
        stage = str(stage) if stage else 'none'
        for s, cb in self._stage_cbs.items():
            cb.setChecked(stage == s)

    def _get_mobility_shifts(self):
        """Read per-channel shifts from the spin boxes."""
        return [sp.value() for sp in self.mobility_spins]

    def _effective_shifts(self):
        """Mobility shifts used for the pipeline and for peak-calling/display.

        In the normal pipeline the matrix is applied *before* mobility
        correction, so the separated trace still needs shifting: this returns
        the spin values. In the experimental 'on Shifted' matrix stage the shift
        is already baked into ``separated`` by ``dsp_full_pipeline``, so we
        return zeros here to avoid shifting the same trace twice."""
        if self._get_matrix_apply_point() == 'shifted':
            return [0, 0, 0, 0]
        return self._get_mobility_shifts()

    def _apply_shifts_to_separated(self, separated, shifts=None):
        """Apply per-channel mobility shifts to the separated trace only.
        Used for display and peak detection — never fed back into the
        baseline/smoothing/matrix pipeline."""
        if shifts is None:
            shifts = self._effective_shifts()
        out = separated.copy()
        for ch in range(4):
            s = int(shifts[ch])
            if s != 0:
                out[:, ch] = dsp_shift_channel(out[:, ch], s)
        return out

    def _on_region_auto_toggled(self, checked):
        """Enable/disable the manual From/To spins when auto-detect is
        toggled. The spins keep displaying the last auto values so manual
        mode starts from a sensible window."""
        auto = bool(checked)
        self.region_start_spin.setEnabled(not auto)
        self.region_stop_spin.setEnabled(not auto)
        self.region_hybrid_check.setEnabled(auto)
        self._schedule_update()

    def _set_multiview_enabled(self, on):
        """Grey out the Multiview parameter panel unless that method is
        selected (the values are meaningless for the other methods)."""
        if not hasattr(self, 'mv_group'):
            return
        self.mv_group.setEnabled(bool(on))

    def _on_method_changed(self, index):
        """Apply the factory parameter preset for the chosen basecall
        method. Fires when the user switches methods (saved settings are
        restored afterwards and take precedence over these defaults)."""
        if index == 0:  # Greedy (max-intensity)
            self.distance_spin.setValue(5)
            self.prominence_spin.setValue(200)     # min_frac 0.20
            self.norm_window_spin.setValue(800)
        elif index == 1:  # Per-channel (cluster)
            self.distance_spin.setValue(5)
            self.prominence_spin.setValue(75)      # prominence_frac 0.075
            self.norm_window_spin.setValue(2000)
        elif index == 3:  # Multiview (per-channel): shared-param starting
            # point; replace with multiview_peakdetect.py output.
            self.distance_spin.setValue(6)
            self.prominence_spin.setValue(75)      # prominence_frac 0.075
            self.norm_window_spin.setValue(800)
        # index 2 = Cimarron (tuned): DSP settings are fixed inside the
        # engine; the peak-call spins are unused so leave them untouched.
        self._set_multiview_enabled(index == 3)

    def _call_bases(self, separated, shifts, region):
        """Run the independent basecall with the currently selected method,
        returning (positions, sequence, base_groups, intensities)."""
        idx = self.method_combo.currentIndex()
        if idx == 2:
            return self._call_bases_cimarron()
        if idx == 3:
            return mvpd.detect_multiview(
                separated, shifts,
                ch_params=[(self.mv_dist_spins[c].value(),
                            self.mv_prom_spins[c].value())
                           for c in range(4)],
                comb_params=(self.mv_comb_dist_spin.value(),
                             self.mv_comb_prom_spin.value())
                if self.mv_comb_check.isChecked() else None,
                tolerance=max(1, self.tol_spin.value()),
                norm_window=max(1, self.norm_window_spin.value()),
                min_signal_frac=self.ambig_spin.value() / 100.0,
                fill_gap=max(1, self.fill_gap_spin.value()),
                fill_margin_pct=float(self.fill_margin_spin.value()),
                region=region,
            )
        if idx == 0:
            return pc_call_bases_greedy(
                separated, shifts,
                window=max(1, self.distance_spin.value()),
                min_frac=self.prominence_spin.value() / 1000.0,
                norm_window=max(1, self.norm_window_spin.value()),
                region=region,
            )
        return pc_call_bases_with_shifts(
            separated, shifts,
            min_distance=max(1, self.distance_spin.value()),
            prominence_frac=self.prominence_spin.value() / 1000.0,
            tolerance=max(1, self.tol_spin.value()),
            min_signal_frac=self.ambig_spin.value() / 100.0,
            norm_window=max(1, self.norm_window_spin.value()),
            region=region,
        )

    def _call_bases_cimarron(self):
        """Run the tuned cimarrontv Cimarron312 engine on the raw RSD
        channels. Returns the GUI (positions, sequence, base_groups,
        intensities) contract using the engine's peak positions, sequence,
        and per-peak heights, so the existing plot overlay keeps working.

        Uses the validated tuned configuration (A01_settings.json bleed
        matrix, mobility shifts 5/11/10/10, AsyLS baseline, Butterworth 5/9,
        'smoothed' matrix apply point, perbase begin/end, greedy caller) by
        default, but honors the GUI's matrix/shift spin boxes whenever the
        user has customized them away from the factory defaults."""
        import cimarrontv as _cim
        if self.rsd_raw is None:
            return (np.array([], dtype=np.int64), '', [], [])
        raw = np.asarray(self.rsd_raw, dtype=np.float64)   # (N,4)
        tuned = dict(baseline_method="AsyLS",
                     baseline_window=50010,
                     smooth_method="Butterworth",
                     smooth_window=5,
                     smooth_order=9,
                     matrix_apply_point="smoothed",
                     caller="greedy",
                     bgn_end_method="perbase",
                     greedy_window=6)
        # Always run the validated tuned configuration so the method is
        # reproducible. The GUI matrix/shift knobs above the plot drive the
        # other two basecall methods; this one is intentionally fixed.
        tuned['spec_sep_matrix'] = _TUNED_SSM
        tuned['mobility_shifts'] = (5, 11, 10, 10)
        eng = _cim.Cimarron312(variant="3.12", **tuned)
        res = eng.call(raw)
        seq = res.sequence
        positions = np.array([p.idx for p in res.peaks], dtype=np.int64)
        letters = [p.base for p in res.peaks]
        base_groups = [frozenset([l]) for l in letters]
        intensities = [{l: float(p.height)} for p, l in
                       zip(res.peaks, letters)]
        return positions, seq, base_groups, intensities

    def _get_region(self, separated):
        """Return the (start, stop) scan window that confines
        normalization + basecalling to the real signal.

        In auto mode the window is derived from the separated trace via
        pc_signal_region and written back into the (read-only) spin boxes.
        In manual mode the spin values are used verbatim; 0/0 means "whole
        file" and returns None. Returns None also when there is no signal
        to detect."""
        if separated is None or len(separated) == 0:
            return None
        if self.region_auto_check.isChecked():
            start, stop = pc_signal_region(separated)
            if (self.region_hybrid_check.isChecked()
                    and _cimarron_bgn_end is not None
                    and getattr(self, 'rsd_raw', None) is not None):
                try:
                    _, pend = _cimarron_bgn_end(
                        np.asarray(self.rsd_raw, dtype=np.float64),
                        method='perbase')
                    stop = min(len(separated), max(start, int(pend) - 120))
                except Exception:
                    pass
            self.region_start_spin.blockSignals(True)
            self.region_stop_spin.blockSignals(True)
            self.region_start_spin.setValue(int(start))
            self.region_stop_spin.setValue(int(stop))
            self.region_start_spin.blockSignals(False)
            self.region_stop_spin.blockSignals(False)
            return int(start), int(stop)
        r0 = int(self.region_start_spin.value())
        r1 = int(self.region_stop_spin.value())
        n = len(separated)
        if r0 <= 0 and r1 <= 0:
            return None
        r0 = max(0, r0)
        if r1 <= 0 or r1 > n:
            r1 = n
        if r1 <= r0:
            r1 = n
        return r0, r1

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
        self._save_limits()

        raw, bl, corr, sm, separated, mix = result
        self._last_separated = separated
        self.fig.clear()
        ax1 = self.fig.add_subplot(4, 1, 1)
        ax2 = self.fig.add_subplot(4, 1, 2, sharex=ax1)
        ax3 = self.fig.add_subplot(4, 1, 3, sharex=ax1)
        ax4 = self.fig.add_subplot(4, 1, 4, sharex=ax1)
        apply_point = self._get_matrix_apply_point()
        # Panels keep their stage meaning on every matrix-stage switch, but
        # the separated panel's y-scale changes ('none' passes raw counts
        # through, else 0-1 normalized), so reset saved limits on stage
        # changes to avoid a "blank" or "jumping" plot.
        if apply_point != getattr(self, '_last_apply_point', None):
            self._saved_lims = {}
        self._last_apply_point = apply_point

        # Mobility shifts are applied only just before basecalling/peak
        # detection - never on the raw/corrected graphs (1 and 2). The
        # separated graph (3) IS the just-before-calling stage, so it shows
        # the shifted trace, and the base labels below sit at the called
        # (shifted) positions, exactly matching the basecall output. Per-
        # channel display normalization: each channel is divided by its own
        # rolling max so the four channels share the same 0-1 scale and the
        # separated plot looks like the ESD reference (uniform ~0-1 peaks)
        # instead of peaks ranging 0-2.5 at the edges to 0-7.5 in the middle.
        shifts = self._effective_shifts()
        separated_shifted = self._apply_shifts_to_separated(separated, shifts)
        region = self._get_region(separated)
        display_window = max(int(self.norm_window_spin.value()), 3)
        sep_disp = pc_normalize_display(separated_shifted, window=display_window,
                                        region=region)

        # Plot 1: raw + baseline. This graph never shows the matrix output -
        # the tick box on its left marks whether the matrix is applied at the
        # raw stage.
        for ch in range(4):
            ax1.plot(self.x_rsd, raw[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.3, alpha=0.6)
            ax1.plot(self.x_rsd, bl[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.5, linestyle='--', alpha=0.5)
        ax1.set_ylabel('Raw + baseline', fontsize=8)
        ax1.legend(['Ch0(T)', 'Ch1(G)', 'Ch2(C)', 'Ch3(A)'],
                   fontsize=5, ncol=4, loc='upper right')
        ax1.tick_params(labelbottom=False, labelsize=7)

        # Plot 2: corrected + smoothed. Same rule as Plot 1 - the matrix is
        # never drawn here; its application point is the tick box on the left.
        for ch in range(4):
            ax2.plot(self.x_rsd, corr[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.2, alpha=0.3)
            ax2.plot(self.x_rsd, sm[:, ch], color=CHAN_COLORS[ch], linewidth=0.5)
        ax2.set_ylabel('Corrected + smoothed', fontsize=8)
        ax2.tick_params(labelbottom=False, labelsize=7)

        # Plot 3: Separated (normalized, mobility-corrected - shifts are
        # applied just before basecalling and are shown here, since this is
        # the final pre-call stage). ESD is intentionally NOT drawn here -
        # see ax4 ("MegaBACE plot") for MegaBACE's own ESD reference.
        for ch in range(4):
            ax3.plot(self.x_rsd, sep_disp[:, ch], color=CHAN_COLORS[ch],
                     linewidth=0.5, label=f'Sep {BASE_LETTERS[ch]}')
        ax3.set_ylabel('Separated (normalized)', fontsize=8)
        ax3.set_ylim(0, 1.05)
        ax3.tick_params(labelbottom=False, labelsize=7)
        if region is not None and region[1] > region[0]:
            ax3.axvline(region[0], color='gray', linestyle=':', linewidth=1)
            ax3.axvline(region[1], color='gray', linestyle=':', linewidth=1)
            ax3.text(region[0] + 2, 0.97, 'start', fontsize=6, color='gray',
                     va='top')
            ax3.text(region[1] - 2, 0.97, 'stop', fontsize=6, color='gray',
                     va='top', ha='right')

        # ESD peak positions/sequence are still read here (needed for the
        # ESD-match% comparison text below and for ax4), just not drawn as
        # a trace/labels on this subplot anymore.
        peaks = self.esd_data.get('peak_positions')
        seq = self.esd_data.get('sequence', '')

        # Plot 4: ESD traces with peaks - this is the only plot that shows
        # MegaBACE's own ESD data. The offset is manually adjustable via
        # the "ESD offset" spin box (auto-populated on load), so alternate
        # ESD variants that need a different shift can be compared too.
        esd_offset = self.esd_offset_spin.value()
        x_esd_aligned = self.x_esd + esd_offset
        for ch in range(4):
            ax4.plot(x_esd_aligned, self.esd_traces[:, ch],
                     color=CHAN_COLORS[ch], linewidth=0.5,
                     label=f'ESD {BASE_LETTERS[ch]}')
        ax4.set_ylabel('ESD traces (MegaBACE)', fontsize=8)
        ax4.set_xlabel('Scan / Record index (aligned)', fontsize=8)
        ax4.tick_params(labelsize=7)
        ax4.legend(fontsize=5, ncol=4, loc='upper right')
        if esd_offset:
            ax4.text(0.01, 0.95,
                     f'ESD trace shifted +{esd_offset} to align under labels',
                     transform=ax4.transAxes, fontsize=6, ha='left', va='top',
                     color='gray')

        if peaks is not None:
            n_esd_recs = len(self.esd_traces)
            esd_max = self.esd_traces.max(axis=0)
            # Draw every MegaBACE ESD base letter in a single flat row near
            # the top of the plot, pinned in axes-fraction so it stays put
            # through zoom/pan - far easier to read as a continuous sequence
            # than labels riding up and down on each peak's own height.
            # Rendering is also batched (one vlines call + one text loop)
            # instead of a separate axvline per base, which was ~840 Line2D
            # artists re-created on every redraw and made the GUI sluggish.
            band_y = 0.93
            tick_y = 0.98
            zero_frac = max(esd_max.max(), 1e-9)
            vx, vcol = [], []
            tick_segs, tick_cols = [], []
            peaks_arr = np.asarray(peaks, dtype=np.int64)
            n_dropped = 0
            for idx in range(len(peaks_arr)):
                p = int(peaks_arr[idx])
                native_guess = p - esd_offset
                # Clamp rather than skip: a peak that lands just outside
                # [0, n_esd_recs) after offset correction (typically the
                # first/last couple of calls) still gets a label at the
                # nearest valid record, instead of silently vanishing -
                # this used to make the row look like it was missing bases
                # even though ESD had called them.
                if n_esd_recs <= 0:
                    n_dropped += 1
                    continue
                native_guess = int(np.clip(native_guess, 0, n_esd_recs - 1))

                # Bound the apex search by half the gap to each neighboring
                # ESD-called peak, so in densely-spaced regions the search
                # can't overshoot the true apex and lock onto the
                # neighbor's peak instead (see _snap_to_peak_apex).
                gap_next = int(peaks_arr[idx + 1]) - p if idx + 1 < len(peaks_arr) else 999
                gap_prev = p - int(peaks_arr[idx - 1]) if idx > 0 else 999
                fwd = max(2, min(15, gap_next // 2)) if gap_next > 0 else 2
                back = max(1, min(2, gap_prev // 2)) if gap_prev > 0 else 1

                p_apex_native = self._snap_to_peak_apex(
                    self.esd_traces, native_guess, n_esd_recs, back=back, fwd=fwd)
                trace = self.esd_traces[p_apex_native]
                if np.any(trace > 0):
                    dom_ch = int(np.argmax(trace))
                    color = CHAN_COLORS[dom_ch]
                    base = BASE_LETTERS[dom_ch]
                else:
                    # Genuinely all-zero window (rare) - still draw a
                    # placeholder rather than dropping the base, so the
                    # displayed count always matches ESD's own count.
                    dom_ch = -1
                    color = 'gray'
                    base = '?'
                x_disp = p_apex_native + esd_offset
                # short hairline under its letter, colored by winning channel
                vx.append(x_disp)
                vcol.append(color)
                ax4.text(x_disp, band_y, base, transform=ax4.get_xaxis_transform(),
                         fontsize=6, ha='center', va='center', color='black',
                         fontweight='bold', clip_on=True,
                         bbox=dict(facecolor=color, alpha=0.35, pad=0.2,
                                   edgecolor='none'))
                # tiny quality tick pinned above: flat = confident call
                if dom_ch >= 0 and trace[dom_ch] > 0:
                    conf = float(np.clip(
                        (trace[dom_ch] - np.sort(trace)[-2]) / trace[dom_ch], 0, 1)) \
                        if len(trace) > 1 else 1.0
                    wob = (1.0 - conf) * 0.02
                    xr = np.array([x_disp - 2, x_disp - 1, x_disp,
                                   x_disp + 1, x_disp + 2], dtype=float)
                    tick_segs.append(np.column_stack(
                        [xr, tick_y + wob * np.array([0, 1, -1, 1, 0])]))
                    tick_cols.append(color)
            if vx:
                ax4.vlines(vx, 0.97 * zero_frac, 0.995 * zero_frac,
                           colors=vcol, linewidths=[0.4] * len(vx),
                           alpha=0.15)
                if tick_segs:
                    lc = LineCollection(tick_segs,
                                        transform=ax4.get_xaxis_transform(),
                                        colors=tick_cols, linewidths=0.6,
                                        alpha=0.8, capstyle='round')
                    ax4.add_collection(lc)
            if n_dropped:
                self.status.setText(
                    f'{n_dropped} of {len(peaks_arr)} ESD base labels could '
                    'not be placed (no valid trace records) and were skipped')

        # Matrix condition + where the matrix is currently applied
        cond = np.linalg.cond(mix)
        stage_names = {'raw': 'raw data',
                       'corrected': 'baseline-corrected',
                       'smoothed': 'corrected + smoothed',
                       'none': 'no matrix (raw channels)'}
        ax3.text(0.99, 0.01,
                 f'matrix on {stage_names.get(apply_point, apply_point)}'
                 f' · cond={cond:.2f}',
                 transform=ax3.transAxes, fontsize=7, ha='right',
                 va='bottom', color='gray',
                 bbox=dict(facecolor='white', alpha=0.7, pad=1))

        # ESD / M13 accuracy is computed below (once the independent call is
        # available) as matched-bases / reference-length via
        # pc_reference_accuracy - not by sampling at ESD's own peak positions.

        # Independent peak-calling on the mobility-corrected separated
        # trace, with IUPAC ambiguity codes and a per-base quality tick.
        esd_txt = None
        m13_txt = None
        if self.rsd_raw is not None:
            try:
                # IMPORTANT: pass the *unshifted* `separated` here, not
                # separated_shifted. The caller applies the mobility shift
                # itself; passing an already-shifted trace here used to
                # double-apply the shift, which is why called bases landed
                # roughly one peak-spacing away from the true peak apex
                # instead of on it.
                pos, iupac_seq, base_groups, intens = self._call_bases(
                    separated, shifts, region)
                # Fill-in: re-run peak detection on the combined envelope and
                # add clean positions the per-channel merge dropped (e.g. the
                # G next to a taller T only 3 scans away), or - for the
                # greedy caller - recover shoulder bases whose apex the
                # +/-Distance excision blanked (e.g. a clean C hiding on a
                # taller neighbor's flank). Drawn in orange so you can see
                # exactly which bases the fill-in added.
                fillin_pos = []
                fillin_add = None
                if self.fillin_check.isChecked():
                    if self.method_combo.currentIndex() == 1:
                        fillin_add = pc_fill_in_combined_peaks(
                            separated, shifts,
                            positions=[int(p) for p in pos],
                            min_distance=max(1, self.distance_spin.value()),
                            prominence_frac=self.prominence_spin.value() / 1000.0,
                            norm_window=max(1, self.norm_window_spin.value()),
                            fill_gap=max(1, self.fill_gap_spin.value()),
                            fill_margin=self.fill_margin_spin.value() / 100.0,
                            region=region,
                        )
                    elif self.method_combo.currentIndex() == 0:
                        fillin_add = pc_fill_in_shoulders(
                            separated, shifts,
                            positions=[int(p) for p in pos],
                            norm_window=max(1, self.norm_window_spin.value()),
                            fill_gap=max(1, self.fill_gap_spin.value()),
                            fill_margin=self.fill_margin_spin.value() / 100.0,
                            region=region,
                        )
                    if fillin_add:
                        merged = sorted(
                            [(int(p), letter) for p, letter in zip(pos, iupac_seq)]
                            + list(fillin_add), key=lambda t: t[0])
                        pos = np.array([t[0] for t in merged], dtype=np.int64)
                        iupac_seq = ''.join(t[1] for t in merged)
                        fillin_pos = [int(t[0]) for t in fillin_add]
                fillin_set = set(fillin_pos)
                # Bases sit in one flat row near the top of the plot,
                # rather than riding up and down with each peak's own
                # height - easier to read as a continuous sequence.
                # y is in axes-fraction (0-1), x stays in data coordinates,
                # so the row stays pinned to the top of the visible area
                # through zoom/pan.
                trans = ax3.get_xaxis_transform()
                band_y = 0.96
                tick_y = 0.99
                tick_amp = 0.035  # max vertical wobble for a fully ambiguous call
                half_w = max(1.0, self.distance_spin.value() / 3.0)
                # Batching: one vlines call for all hairlines + one
                # LineCollection for all quality ticks, instead of ~2 plots
                # per base. This cut redraw time dramatically (hundreds of
                # Line2D artists were being recreated on every slider move).
                hv_x, hv_col = [], []
                tick_segs, tick_cols = [], []
                for p, letter in zip(pos, iupac_seq):
                    if not (0 <= p < len(separated_shifted)):
                        continue
                    vals = separated_shifted[p]
                    dom_ch = int(np.argmax(vals))
                    color = CHAN_COLORS[dom_ch]
                    face = ('orange' if int(p) in fillin_set else 'yellow')
                    # The separated graph shows the SHIFTED trace (shifts are
                    # applied just before basecalling), and `p` is the called
                    # position in those shifted coordinates - so labels sit on
                    # the peaks that are drawn and match the basecall output.
                    x_disp = int(p)
                    ax3.text(x_disp, band_y, letter, transform=trans, fontsize=5,
                             ha='center', va='center', color='black',
                             fontweight='bold', clip_on=True,
                             bbox=dict(facecolor=face, alpha=0.6, pad=0.3,
                                       edgecolor='none'))
                    hv_x.append(x_disp)
                    hv_col.append(color)

                    # Quality tick above the base: how clearly the winning
                    # channel beats the runner-up at this position. A
                    # confident call (winner >> runner-up) draws a flat
                    # horizontal line; an ambiguous call (winner ~= runner-
                    # up, e.g. a heterozygous/IUPAC position) draws a
                    # visibly wobbling one - straighter is better.
                    top, second = np.sort(vals)[-1], np.sort(vals)[-2]
                    confidence = float(np.clip((top - second) / top, 0, 1)) if top > 0 else 0.0
                    wobble = (1.0 - confidence) * tick_amp
                    xs = np.array([x_disp - half_w, x_disp - half_w / 2, x_disp,
                                   x_disp + half_w / 2, x_disp + half_w])
                    ys = tick_y + wobble * np.array([0.0, 1.0, -1.0, 1.0, 0.0])
                    tick_segs.append(np.column_stack([xs, ys]))
                    tick_cols.append(color)
                if hv_x:
                    ax3.vlines(hv_x, tick_y, band_y, transform=trans,
                               colors=hv_col, linewidths=[0.3] * len(hv_x),
                               alpha=0.15)
                if tick_segs:
                    lc = LineCollection(tick_segs, transform=trans,
                                        colors=tick_cols, linewidths=0.8,
                                        alpha=0.85, capstyle='round')
                    ax3.add_collection(lc)

                if iupac_seq and len(iupac_seq) > 10:
                    n_fill = len(fillin_pos)
                    # Matched-bases / reference-length accuracy (the "match
                    # bases / total bases" metric) against the ESD sequence.
                    esd_m, esd_t, esd_pct = pc_reference_accuracy(iupac_seq, seq)
                    # Same against the M13 reference slice (the headline target).
                    ref = getattr(self, 'reference_dna', '')
                    lo = getattr(self, 'reference_start', 0)
                    hi = getattr(self, 'reference_end', 0)
                    ref_slice = ref[lo - 1:hi] if (ref and hi > lo) else ''
                    if ref_slice:
                        m13_m, m13_t, m13_pct = pc_reference_accuracy(
                            iupac_seq, ref_slice)
                        name = getattr(self, 'reference_name', '') or 'M13'
                        m13_txt = (f'{name}: {m13_m}/{m13_t} bases '
                                   f'({m13_pct:.1f}%)')
                    else:
                        m13_txt = 'M13: no reference set'
                    esd_txt = f'ESD: {esd_m}/{esd_t} bases ({esd_pct:.1f}%)'
                    if n_fill:
                        esd_txt += f' · {n_fill} filled-in'
                    self._manual_sequence = iupac_seq
                    self._update_fasta_box(iupac_seq)
            except Exception as e:
                self._manual_sequence = ''
                self._fasta_box.setText('')
                self.status.setText(f'Independent basecall error: {e}')

        # Comparison metrics as two Qt boxes at the top of the FASTA section
        # (see _build_metrics_row), matching the surrounding widget font size.
        # Both now report matched-bases / reference-length (see
        # pc_reference_accuracy).
        self.fig.subplots_adjust(hspace=0.08, left=0.14, right=0.98,
                                 top=0.97, bottom=0.08)
        if esd_txt is not None:
            self._esd_metric_label.setText(esd_txt)
            self._esd_metric_label.setVisible(True)
        else:
            self._esd_metric_label.setVisible(False)
        if m13_txt is not None:
            self._indep_metric_label.setText(m13_txt)
            self._indep_metric_label.setVisible(True)
        else:
            self._indep_metric_label.setVisible(False)
        self._restore_limits([ax1, ax2, ax3, ax4])
        for ax in [ax1, ax2, ax3]:
            ax.set_xlabel('')
        ax4.set_xlabel('Scan / Record index (aligned)', fontsize=8)
        if self.drag_mode_btn.isChecked():
            self._draw_shift_lines(ax3)
            self.drag_mode_btn.setVisible(True)
        else:
            self._shift_lines.clear()
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
                'baseline_window2': self.bl2_spin.value(),
                'smooth_window': self.sm_win_spin.value(),
'smooth_order': self.sm_ord_spin.value(),
            'min_distance': self.distance_spin.value(),
            'prominence_frac': self.prominence_spin.value() / 1000.0,
            'min_signal_frac': self.ambig_spin.value() / 100.0,
                'mobility_shifts': [sp.value() for sp in self.mobility_spins],
                'condition': float(np.linalg.cond(mix)),
            }, f, indent=2)
        self.status.setText(f'Saved to {dir_path}')

    def _run_ml(self):
        """ML basecalling: feeds raw (unseparated) RSD trace patches centered
        at ESD peak positions through the trained CNN model.

        The model was trained on raw 4-channel patches at ESD-aligned peaks,
        so it implicitly handles spectral unmixing — no baseline correction,
        smoothing, or matrix inversion needed. This is why it achieves
        ~98% vs ESD (vs ~30% for naive argmax on separated traces).

        Also evaluates against the M13 reference (the true ground truth),
        since ESD itself only matches M13 at ~92%."""
        if self.current_well is None:
            self.status.setText('Load a well first')
            return
        self.progress.setVisible(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status.setText('Running ML basecalling...')
        QApplication.processEvents()

        from basecaller import _load_ml_model, ML_LABELS
        model = _load_ml_model()
        window = 15

        # Read raw RSD trace (NOT the processed/separated trace)
        well = self.current_well
        rsd_path = os.path.join(self.data_dir, f'{well}.rsd')
        df = parse_rsd(rsd_path)
        raw = df[['Channel1', 'Channel2', 'Channel3',
                  'Channel4']].values.astype(np.float32)

        # ESD data for evaluation
        esd_path = os.path.join(self.data_dir,
                                self.esd_combo.currentData() or '',
                                f'{well}.esd')
        esd_data = parse_esd(esd_path)
        positions = esd_data.get('peak_positions')
        seq = esd_data.get('sequence', '')
        if positions is None or not seq:
            self.status.setText('No ESD peaks to evaluate')
            self.progress.setVisible(False)
            return

        n_scans = len(raw)
        # Clamp positions to valid range for patch extraction
        valid = np.where((positions >= window) &
                         (positions < n_scans - window))[0]
        valid_positions = positions[valid]

        self.progress.setValue(20)
        QApplication.processEvents()

        # Build batch of normalized patches
        X = np.array([raw[int(p) - window:int(p) + window + 1]
                      for p in valid_positions], dtype=np.float32)
        X_mean = X.mean(axis=(1,), keepdims=True)
        X_std = X.std(axis=(1,), keepdims=True) + 1e-8
        X = (X - X_mean) / X_std

        self.progress.setValue(40)
        QApplication.processEvents()

        preds = model.predict(X, verbose=0)
        pred_classes = preds.argmax(axis=1)
        pred_probs = preds.max(axis=1)

        self.progress.setValue(70)
        QApplication.processEvents()

        # Assemble called sequence at ESD positions
        esd_seq_valid = ''.join(seq[i] for i in valid if i < len(seq))
        bases = []
        quals = []
        for cls, prob in zip(pred_classes, pred_probs):
            base = ML_LABELS[cls]
            qual = int(round(prob * 100))
            if qual < 20:
                base = 'N'
            bases.append(base)
            quals.append(qual)
        called = ''.join(bases)
        self._ml_called = called
        self._ml_quals = np.array(quals, dtype=np.int32)
        self._ml_positions = valid_positions
        self._ml_raw_seq = esd_seq_valid

        # Identity vs ESD: full global (Needleman-Wunsch) alignment instead of
        # the circular position-indexed match so known small ESD base errors
        # don't drag the score down - the fair comparison against a second
        # caller is alignment identity, same as the M13 metric. N bases are
        # kept (they are real mismatches to ESD, unlike align_to_m13 which
        # strips them).
        from peak_calling import nw_identity as _nw_esd
        esd_identity = _nw_esd(called, esd_seq_valid, max_len=20000)

        # Identity vs M13 (true ground truth)
        from simple_align import M13_REFERENCE
        q = ''.join(c for c in bases if c in 'ACGT')
        m13_result = self._align_to_m13(q)
        m13_identity = m13_result.get('identity', 0) if m13_result else 0

        # Quality distribution
        conf_called = [p for b, p in zip(bases, pred_probs) if b != 'N']
        if conf_called:
            avg_conf = np.mean(conf_called) * 100
        else:
            avg_conf = 0

        non_n = sum(1 for b in bases if b != 'N')
        self.progress.setValue(100)
        self._ml_esd_identity = esd_identity
        self._ml_m13_identity = m13_identity
        self.status.setText(
            f'ML basecall: {non_n}/{len(bases)} called (avg conf {avg_conf:.0f}%). '
            f'vs ESD={esd_identity:.1f}%, vs M13={m13_identity:.1f}%'
            f' - use "Export ML FASTA" to save it')
        self.ml_fasta_btn.setEnabled(True)
        QTimer.singleShot(4000, lambda: self.progress.setVisible(False))

    def _export_ml_fasta(self):
        """Write the stored ML basecall to a FASTA file plus a comparison
        report against both the ESD call and the true M13 reference.

        Only the confidently-called positions are FASTA bases; low-confidence
        calls are written as N so the record stays length-identical with the
        ESD call for easy columnwise diffing (ESD has a few known errors, so
        seeing both strings side by side makes disagreements visible)."""
        well = self.current_well
        if well is None or not hasattr(self, '_ml_called') or not self._ml_called:
            self.status.setText('Run ML basecalling first')
            return
        called = self._ml_called
        quals = self._ml_quals
        esd_seq = self._ml_raw_seq
        esd_ident = getattr(self, '_ml_esd_identity', 0.0)
        m13_ident = getattr(self, '_ml_m13_identity', 0.0)

        dir_path = QFileDialog.getExistingDirectory(
            self, 'Select save directory',
            os.path.join(self.data_dir, self.current_well or ''))
        if not dir_path:
            return

        # FASTA header carries the compare metrics so it is self-describing
        # without opening the report file.
        header = (f'>{well} ml-basecall conf~{int(np.mean(quals[quals >= 20])) if (quals >= 20).any() else 0} '
                  f'vs_ESD={esd_ident:.1f}% vs_M13={m13_ident:.1f}% '
                  f'esdlen={len(esd_seq)}')
        fasta_path = os.path.join(dir_path, f'{well}_ml.fasta')
        report_path = os.path.join(dir_path, f'{well}_ml_report.txt')
        with open(fasta_path, 'w') as f:
            f.write(header + '\n')
            for i in range(0, len(called), 80):
                f.write(called[i:i + 80] + '\n')

        # Alignment report: three-letter rows for the full ML call vs M13 (the
        # true reference) and ML vs ESD, so disagreements are visible.
        q13 = ''.join(c for c in called if c in 'ACGT')
        m13_result = self._align_to_m13(q13)
        with open(report_path, 'w') as f:
            f.write(f'{well} ML basecall comparison report\n')
            f.write(f'called bases: {len(called)} (ESD len {len(esd_seq)}) '
                    f'avg conf: {int(np.mean(quals[quals >= 20])) if (quals >= 20).any() else 0}\n'
                    f'vs ESD NW identity: {esd_ident:.1f}%\n')
            f.write(f'vs M13 NW identity: {m13_ident:.1f}%\n')
            if m13_result:
                f.write(f'M13 aligned: matches={m13_result["matches"]} '
                        f'len={m13_result["alignment_length"]}\n')
            f.write('\nML call quality (position|base|conf):\n')
            for i in range(len(called)):
                f.write(f'{i + 1}\t{called[i]}\t{quals[i]}\n')
        self.status.setText(
            f'Exported ML FASTA: {fasta_path} (+ report {report_path})')

    @staticmethod
    def _align_to_m13(query, ref=None):
        """Needleman-Wunsch alignment of query string to M13 reference."""
        from simple_align import M13_REFERENCE
        if ref is None:
            ref = M13_REFERENCE
        q = ''.join(c for c in query if c in 'ACGT')
        if len(q) < 20:
            return None
        m, n = len(q), len(ref)
        dp = np.zeros((m + 1, n + 1), dtype=np.int32)
        dp[:, 0] = np.arange(m + 1) * -2
        dp[0, :] = np.arange(n + 1) * -2
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                diag = dp[i - 1, j - 1] + (1 if q[i - 1] == ref[j - 1] else -1)
                up = dp[i - 1, j] + -2
                left = dp[i, j - 1] + -2
                dp[i, j] = max(diag, up, left)
        i, j = m, n
        matches = 0
        aligned = 0
        while i > 0 or j > 0:
            if i > 0 and j > 0 and dp[i, j] == dp[i - 1, j - 1] + \
                    (1 if q[i - 1] == ref[j - 1] else -1):
                aligned += 1
                if q[i - 1] == ref[j - 1]:
                    matches += 1
                i -= 1
                j -= 1
            elif i > 0 and dp[i, j] == dp[i - 1, j] + -2:
                aligned += 1
                i -= 1
            else:
                aligned += 1
                j -= 1
        return {
            'matches': matches,
            'alignment_length': aligned,
            'identity': matches / aligned * 100 if aligned else 0,
        } if aligned else None

    def _nw_identity(self, q, r, match=1, mismatch=-1, gap=-2):
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
        matches = 0
        aligned = 0
        while i > 0 or j > 0:
            if i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + \
                    (match if q[i-1] == r[j-1] else mismatch):
                aligned += 1
                if q[i-1] == r[j-1]:
                    matches += 1
                i -= 1
                j -= 1
            elif i > 0 and dp[i][j] == dp[i-1][j] + gap:
                aligned += 1
                i -= 1
            else:
                aligned += 1
                j -= 1
        return 100.0 * matches / aligned if aligned else 0.0

    def _run_independent_peakcall(self):
        """Run a real peak detector on the shifted separated trace (no ESD peak
        positions involved) and align the result against the ESD sequence.
        This is the number to trust over the plot's 'ESD match %', which
        only samples the trace at positions ESD already told it were peaks."""
        if self.rsd_raw is None or self.esd_data is None:
            self.status.setText('Load a well first')
            return
        result = self._process()
        if result is None:
            return
        _, _, _, _, separated, _ = result
        shifts = self._effective_shifts()
        sep_shifted = self._apply_shifts_to_separated(separated, shifts)
        esd_seq = self.esd_data.get('sequence', '')
        if not esd_seq:
            self.status.setText('No ESD sequence to compare against')
            return
        positions, called_seq, heights = pc_call_bases(sep_shifted)
        self._independent_seq = called_seq
        identity = pc_nw_identity(called_seq, esd_seq, max_len=20000)
        self.status.setText(
            f'Independent peak-call: {len(called_seq)} bases called '
            f'(ESD has {len(esd_seq)}) - alignment identity vs ESD: '
            f'{identity:.1f}%')

    def _open_reference_dialog(self):
        ReferenceDialog(self).exec_()

    def _run_auto_mobility(self):
        """Peak-coincidence mobility shift estimate (see
        pc_estimate_mobility_shifts). Only meaningful on calibration-standard
        data where all four dye channels share peak positions; on a real read
        the confidence gate rejects the spurious lags envelope correlation
        used to return (e.g. -38 on Ch1 of an ordinary M13 read)."""
        if self.rsd_raw is None:
            self.status.setText('Load a well first')
            return
        shifts, conf = pc_estimate_mobility_shifts(self.rsd_raw, ref_channel=3)
        for ch, sp in enumerate(self.mobility_spins):
            sp.blockSignals(True)
            sp.setValue(int(np.clip(shifts[ch], sp.minimum(), sp.maximum())))
            sp.blockSignals(False)
        self._schedule_update()
        low = [BASE_LETTERS[ch] for ch in range(4) if conf[ch] < 0.55]
        if low:
            self.status.setText(
                f'Auto mobility: {list(map(int, shifts))} — no clear '
                f'peak-coincidence signal on {"".join(low) or "?"}, '
                f'not calibration-run data? Treat shifts as unverified.')
        else:
            self.status.setText(
                f'Auto mobility shift (calibration-run estimate): '
                f'{list(map(int, shifts))}')

    def _run_optimizer(self):
        """Shell out to optimize_params.py in a background thread so the
        GUI stays responsive (the optimization can take 1-30 minutes
        depending on well count and maxiter)."""
        if self.current_well is None:
            self.status.setText('Load a well first')
            return
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'optimize_params.py')
        if not os.path.exists(script):
            self.status.setText('optimize_params.py not found next to this script')
            return
        esd_subdir = self.esd_combo.currentData() or ''
        out_path = os.path.join(tempfile.mkdtemp(prefix='optimize_'),
                                'best_params.json')
        self.status.setText(
            f'Optimizing parameters for well {self.current_well} ...')
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.progress.setValue(-1)
        self.opt_log.clear()
        self.opt_log.show()
        self.cancel_opt_btn.setVisible(True)
        self._disable_controls()

        overnight = self.overnight_cb.isChecked()
        if overnight:
            wells_arg = 'all'
            maxiter = 400
            popsize = 25
            workers = 4
            self.status.setText(
                'Overnight optimization: all wells, deep search (this will take '
                'a long time - leave it running)...')
        else:
            wells_arg = self.current_well
            maxiter = 30
            popsize = 10
            workers = 1
        cmd = [sys.executable, '-u', script, '--base-dir', self.data_dir,
               '--wells', wells_arg, '--maxiter', str(maxiter),
               '--popsize', str(popsize), '--workers', str(workers),
               '--out', out_path,
               '--min-distance', str(self.distance_spin.value()),
               '--prominence-frac', f'{self.prominence_spin.value() / 1000.0:.6f}',
               '--ambig-frac', f'{self.ambig_spin.value() / 100.0:.6f}']
        if esd_subdir:
            subdirs = find_esd_subdirs(self.data_dir)
            for name, d in subdirs.items():
                if d == esd_subdir:
                    cmd += ['--esd-subdir', name]
                    break
        init_json = self._write_init_json()
        if init_json:
            cmd += ['--init-json', init_json]
            self.status.setText(
                f'Optimizing from current settings ...')
        else:
            self.status.setText(
                f'Optimizing parameters for well {self.current_well} ...')

        worker = OptimizerWorker(cmd, out_path, self)
        worker.finished.connect(self._on_optimizer_finished)
        worker.stdout_line.connect(self._on_optimizer_stdout)
        worker.start()
        self._opt_worker = worker

    def _cancel_optimizer(self):
        if self._opt_worker and self._opt_worker.isRunning():
            self._opt_worker.cancel()
            self.status.setText('Cancelling optimizer...')
        self.cancel_opt_btn.setVisible(False)

    def _on_optimizer_stdout(self, line):
        """Stream optimizer progress lines to the log window."""
        self.opt_log.append(line)
        vs = self.opt_log.verticalScrollBar()
        if vs:
            vs.setValue(vs.maximum())

    def _disable_controls(self):
        for w in [self.well_combo, self.esd_combo, self.load_btn,
                  self.save_btn, self.ml_btn, self.peakcall_btn,
                  self.mobility_btn, self.optimize_btn]:
            w.setEnabled(False)

    def _enable_controls(self):
        for w in [self.well_combo, self.esd_combo, self.load_btn,
                  self.save_btn, self.ml_btn, self.peakcall_btn,
                  self.mobility_btn, self.optimize_btn]:
            w.setEnabled(True)

    def _on_optimizer_finished(self, result):
        """Handle the OptimizerWorker.finished signal."""
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        self.cancel_opt_btn.setVisible(False)
        self.opt_log.hide()
        self._enable_controls()

        if result.startswith('ERROR:'):
            self.status.setText(result)
            return

        out_path = result
        try:
            with open(out_path) as f:
                best = json.load(f)
        except Exception as e:
            self.status.setText(f'Could not read optimizer output: {e}')
            return

        idx = self.baseline_combo.findText(best['baseline_method'])
        if idx >= 0:
            self.baseline_combo.setCurrentIndex(idx)
        self.bl_spin.setValue(int(round(best['baseline_window'])))
        if 'baseline_window2' in best:
            self.bl2_spin.setValue(int(round(best['baseline_window2'])))
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
        self._save_best_to_settings_file(best)
        self.status.setText(
            f"Optimizer found {best.get('base_identity_pct', 0.0):.1f}% identity vs ESD "
            f"with {best['baseline_method']}/{best['smooth_method']} - loaded into "
            f"controls and written to A01_settings.json")

    def _save_best_to_settings_file(self, best):
        """Merge the optimizer's best baseline/smoothing/shift/matrix into the
        A01_settings.json next to this script so the user can load and try it
        via 'Load settings'. Only the parameters the optimizer searched are
        overwritten; the user's other settings (esd_variant, well, caller
        knobs, matrix stage) are preserved."""
        import os as _os
        path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                             'A01_settings.json')
        try:
            if _os.path.exists(path):
                with open(path) as f:
                    cur = json.load(f)
            else:
                cur = {}
            cur.update({
                'baseline_method': best['baseline_method'],
                'baseline_window': int(round(best['baseline_window'])),
                'baseline_window2': int(round(best.get('baseline_window2',
                                                       cur.get('baseline_window2', 0)))),
                'smooth_method': best['smooth_method'],
                'smooth_window': int(round(best['smooth_window'])),
                'smooth_order': int(round(best['smooth_order'])),
                'mobility_shifts': [int(s) for s in best['mobility_shifts']],
                'matrix': np.asarray(best['matrix']).tolist(),
            })
            with open(path, 'w') as f:
                json.dump(cur, f, indent=2)
            self.opt_log.append(f'Best settings saved to {path}')
        except Exception as e:
            self.opt_log.append(f'Could not save best settings: {e}')

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
