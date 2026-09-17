"""Batch processing dialog for the sequencing GUI.

Displays a 96-well plate grid, starts batch processing, and shows
per-well progress.  Exports FASTQ/FASTA when done.
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QProgressBar, QTextEdit, QFileDialog,
    QGroupBox, QGridLayout, QCheckBox, QSplitter, QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from plate_view import PlateView
from batch import BatchProcessor


class BatchWorker(QThread):
    """Background thread running the batch processor."""
    progress = pyqtSignal(str, int, int)   # well, done, total
    finished = pyqtSignal(dict)            # results dict
    error = pyqtSignal(str)

    def __init__(self, processor):
        super().__init__()
        self.processor = processor

    def run(self):
        try:
            self.processor.run(progress_callback=self._cb)
            self.finished.emit(self.processor.results)
        except Exception as e:
            self.error.emit(str(e))

    def _cb(self, well, done, total):
        self.progress.emit(well, done, total)

    def cancel(self):
        self.processor.cancel()


class BatchDialog(QDialog):
    """Full-featured batch processing dialog.

    Call with:
        dlg = BatchDialog(data_dir, parent=self)
        dlg.exec_()
    """

    well_selected = pyqtSignal(str)  # emit well name when user clicks plate

    def __init__(self, data_dir, esd_subdir=None, shifts=None,
                 method=0, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Batch Process Plate')
        self.setMinimumSize(900, 650)
        self.data_dir = data_dir
        self.esd_subdir = esd_subdir
        self.shifts = shifts or [5, 11, 10, 10]
        self.method = method
        self._worker = None
        self._results = {}
        self._init_ui()
        self._scan_wells()

    def _init_ui(self):
        main = QVBoxLayout(self)
        # ── Top bar: settings ──
        top = QHBoxLayout()
        top.addWidget(QLabel('Threads:'))
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 16)
        self.threads_spin.setValue(4)
        top.addWidget(self.threads_spin)
        top.addWidget(QLabel('Method:'))
        self.method_combo = QComboBox()
        self.method_combo.addItems(['Greedy', 'Cluster', 'Cimarron+CNN'])
        self.method_combo.setCurrentIndex(self.method)
        top.addWidget(self.method_combo)
        top.addStretch()
        self.run_btn = QPushButton('▶ Run Batch')
        self.run_btn.clicked.connect(self._start_batch)
        top.addWidget(self.run_btn)
        self.cancel_btn = QPushButton('■ Cancel')
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._cancel_batch)
        top.addWidget(self.cancel_btn)
        main.addLayout(top)
        # ── Progress ──
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        main.addWidget(self.progress)
        self.status_label = QLabel('Ready')
        main.addWidget(self.status_label)
        # ── Splitter: plate view + log ──
        splitter = QSplitter(Qt.Horizontal)
        # Plate view
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        self.plate = PlateView()
        self.plate.well_clicked.connect(self._on_well_clicked)
        ll.addWidget(self.plate)
        # Summary stats below plate
        self.summary_label = QLabel('')
        self.summary_label.setStyleSheet('font-size: 11px; color: #444;')
        ll.addWidget(self.summary_label)
        splitter.addWidget(left)
        # Log
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(QLabel('Log'))
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setFontFamily('Monospace')
        self.log.setFontPointSize(9)
        rl.addWidget(self.log)
        # Export buttons
        exp = QHBoxLayout()
        self.fastq_btn = QPushButton('Export FASTQ')
        self.fastq_btn.setEnabled(False)
        self.fastq_btn.clicked.connect(self._export_fastq)
        exp.addWidget(self.fastq_btn)
        self.fasta_btn = QPushButton('Export FASTA')
        self.fasta_btn.setEnabled(False)
        self.fasta_btn.clicked.connect(self._export_fasta)
        exp.addWidget(self.fasta_btn)
        self.per_well_btn = QPushButton('Export per-well')
        self.per_well_btn.setEnabled(False)
        self.per_well_btn.clicked.connect(self._export_per_well)
        exp.addWidget(self.per_well_btn)
        rl.addLayout(exp)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        main.addWidget(splitter)

    def _scan_wells(self):
        """Count .rsd files in data_dir."""
        if not os.path.isdir(self.data_dir):
            self.status_label.setText(f'Folder not found: {self.data_dir}')
            return
        wells = [f[:-4] for f in os.listdir(self.data_dir) if f.endswith('.rsd')]
        self.status_label.setText(f'{len(wells)} wells found in {self.data_dir}')
        self.plate.set_status({w: 'pending' for w in wells})

    def _start_batch(self):
        self.run_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.fastq_btn.setEnabled(False)
        self.fasta_btn.setEnabled(False)
        self.per_well_btn.setEnabled(False)
        self.log.clear()
        self.progress.setValue(0)
        self.status_label.setText('Processing...')
        method = self.method_combo.currentIndex()
        processor = BatchProcessor(
            self.data_dir, esd_subdir=self.esd_subdir,
            shifts=self.shifts, method=method,
        )
        self._worker = BatchWorker(processor)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _cancel_batch(self):
        if self._worker:
            self._worker.cancel()
            self.log.append('** Cancelled **')
            self.status_label.setText('Cancelled')
            self.run_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)

    def _on_progress(self, well, done, total):
        self.progress.setMaximum(total)
        self.progress.setValue(done)
        r = self._worker.processor.results.get(well)
        if r and r.success:
            self.plate.set_well(well, q_score=r.mean_q, status='done')
            self.log.append(f'{well}: {r.total_bases} bases  Q={r.mean_q:.1f}  '
                          f'{r.elapsed:.1f}s')
        elif r:
            self.plate.set_well(well, status='error')
            self.log.append(f'{well}: ERROR {r.error}')
        self.status_label.setText(f'[{done}/{total}] {well}')

    def _on_finished(self, results):
        self._results = results
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.fastq_btn.setEnabled(True)
        self.fasta_btn.setEnabled(True)
        self.per_well_btn.setEnabled(True)
        stats = self._worker.processor.summary_stats()
        self.summary_label.setText(
            f'{stats["success"]}/{stats["total_wells"]} wells  |  '
            f'mean {stats.get("mean_bases", 0)} bases  |  '
            f'Q20 {stats.get("mean_q20", 0)}%  |  '
            f'Q30 {stats.get("mean_q30", 0)}%  |  '
            f'{stats.get("mean_time", 0)}s/well'
        )
        self.log.append(f'\n=== Done: {stats["success"]}/{stats["total_wells"]} wells ===')
        self.status_label.setText(f'Complete: {stats["success"]}/{stats["total_wells"]} wells')

    def _on_error(self, msg):
        self.log.append(f'FATAL: {msg}')
        self.status_label.setText('Error')
        self.run_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

    def _on_well_clicked(self, well):
        self.well_selected.emit(well)

    def _export_fastq(self):
        path = QFileDialog.getExistingDirectory(self, 'Output directory')
        if not path:
            return
        self._worker.processor.export_fastq(path)
        self.log.append(f'FASTQ exported to {path}')

    def _export_fasta(self):
        path = QFileDialog.getExistingDirectory(self, 'Output directory')
        if not path:
            return
        self._worker.processor.export_fasta(path)
        self.log.append(f'FASTA exported to {path}')

    def _export_per_well(self):
        path = QFileDialog.getExistingDirectory(self, 'Output directory')
        if not path:
            return
        self._worker.processor.export_per_well(path)
        self.log.append(f'Per-well FASTQ exported to {path}')

    def get_results(self):
        return self._results
