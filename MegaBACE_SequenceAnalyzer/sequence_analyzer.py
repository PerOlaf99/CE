#!/usr/bin/env python3
"""
MegaBACE Sequence Analyzer (Python)
====================================
Desktop UI matching the Molecular Dynamics MegaBACE Sequence Analyzer
User's Guide v2.0 feature set:

  • Navigation pane (loaded plate folders) + Sample-status pane
    (plate ID · well · sample ID · run ID · base-call/export status)
  • Display pane with three tabs: Electropherogram, Sequence, Wrap
  • Main toolbar (Load Plates, Print, Base Call, Export FASTA/SCF/Text/ABD,
    Stop, About) and Display toolbar (Raw/Processed Trace, Remove Trace(s),
    Remove All, rows-per-screen buttons, Zoom in/out along x and y,
    Joint Scrolling)
  • Base Caller list box (Cimarron 1.53 Slim Phredify / Phat / 1.31,
    Molecular Dynamics incremental) and Left Cut Off list box
  • Incremental base-calling stages via the Data menu: Baseline Subtraction,
    Spectral Separation, Normalization, Band Filter, Mobility Shift,
    Quality Assessment
  • Quality profile (blue-green: good, brown: poor) per base 0–100
  • Export: FASTA (.seq), SCF, ABD, text; Print; Data-storage settings

Requires: Python 3.10+ with tkinter, numpy, scipy, matplotlib
  Linux:   sudo apt install python3-tk

Run:
  python sequence_analyzer.py
  python sequence_analyzer.py --folder /path/to/rsd_dir
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import List, Optional

import numpy as np

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from analyzer_core import (
    AnalysisSettings,
    BASE_COLORS,
    INTERNAL_CALLER_TO_GUILD,
    MANUAL_BASECALLERS,
    TraceDocument,
    discover_rsd,
    discover_esd,
    load_rsd,
    load_esd,
    run_basecall,
    display_trace,
    stage_document,
    assess_quality,
    INCREMENTAL_STAGES,
    export_fasta,
    export_scf,
    export_abd,
    export_text,
)

BASE_LETTERS_ORDER = "ACGT"       # trace column order
BASE_ORDER_LETTERS = ["A", "C", "G", "T"]

CHANNEL_COLORS = {"A": "#00AA00", "C": "#0000DD", "G": "#111111", "T": "#DD0000"}
QUALITY_GOOD = "#2E8B57"          # blue-green: good-quality section
QUALITY_POOR = "#8B4513"          # brown: poor-quality section
QUALITY_CURVE = "#B8860B"         # dark goldenrod line

TRACE_THEMES = {
    "Classic": {"A": "#00AA00", "C": "#0000DD", "G": "#111111", "T": "#DD0000"},
    "Chromas": {"A": "#00AA00", "C": "#1E90FF", "G": "#444444", "T": "#FF0000"},
    "High-contrast": {"A": "#2E8B57", "C": "#1F4FC0", "G": "#000000", "T": "#E03030"},
    "Monochrome": {"A": "#777777", "C": "#555555", "G": "#333333", "T": "#888888"},
}

DATA_STORAGE_FILE = Path(__file__).with_name("seq_analyzer_storage.json")


def _load_storage_settings() -> dict:
    try:
        return json.loads(DATA_STORAGE_FILE.read_text())
    except Exception:
        return {}


def _save_storage_settings(d: dict) -> None:
    try:
        DATA_STORAGE_FILE.write_text(json.dumps(d, indent=2))
    except Exception:
        pass


class DataStorageDialog(tk.Toplevel):
    """Options > Data storage: default raw / analyzed locations."""

    def __init__(self, parent, raw_path: str, analyzed_path: str, callback):
        super().__init__(parent)
        self.title("Data Storage")
        self.resizable(False, False)
        self.callback = callback
        f = ttk.Frame(self, padding=10)
        f.grid()
        ttk.Label(f, text="Default Raw Data").grid(row=0, column=0, sticky="w")
        self.raw_var = tk.StringVar(value=raw_path)
        e1 = ttk.Entry(f, textvariable=self.raw_var, width=52)
        e1.grid(row=0, column=1, padx=4)
        ttk.Button(f, text="Browse…",
                   command=lambda: self._browse(self.raw_var)).grid(row=0, column=2)
        ttk.Label(f, text="Default Analyzed Data").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.ana_var = tk.StringVar(value=analyzed_path)
        e2 = ttk.Entry(f, textvariable=self.ana_var, width=52)
        e2.grid(row=1, column=1, padx=4, pady=(6, 0))
        ttk.Button(f, text="Browse…",
                   command=lambda: self._browse(self.ana_var)).grid(row=1, column=2, pady=(6, 0))
        ttk.Button(f, text="OK", command=self._ok).grid(row=2, column=1, sticky="e", pady=(10, 0))

    def _browse(self, var: tk.StringVar):
        d = filedialog.askdirectory(title="Select folder")
        if d:
            var.set(d)

    def _ok(self):
        self.callback(self.raw_var.get(), self.ana_var.get())
        self.destroy()


class ExportOptionsDialog(tk.Toplevel):
    """FASTA export options (folder, file name, individual/appended, high-Q only)."""

    def __init__(self, parent, default_dir: str, on_export):
        super().__init__(parent)
        self.title("Export FASTA Options")
        self.resizable(False, False)
        self.on_export = on_export
        f = ttk.Frame(self, padding=10)
        f.grid()
        ttk.Label(f, text="Output folder").grid(row=0, column=0, sticky="w")
        self.dir_var = tk.StringVar(value=default_dir)
        ttk.Entry(f, textvariable=self.dir_var, width=44).grid(row=0, column=1, padx=4)
        ttk.Button(f, text="Browse…", command=self._browse).grid(row=0, column=2)
        ttk.Label(f, text="File name (optional)").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.name_var = tk.StringVar(value="all_reads.fasta")
        ttk.Entry(f, textvariable=self.name_var, width=44).grid(row=1, column=1, padx=4, pady=(6, 0))
        self.single_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Individual files per sample",
                        variable=self.single_var).grid(row=2, column=1, sticky="w", pady=(6, 0))
        self.hiq_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(f, text="Export only high-quality regions (Q ≥ 30)",
                        variable=self.hiq_var).grid(row=3, column=1, sticky="w")
        ttk.Button(f, text="Export", command=self._go).grid(row=4, column=1, sticky="e", pady=(10, 0))

    def _browse(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self.dir_var.set(d)

    def _go(self):
        try:
            self.on_export(Path(self.dir_var.get()), self.name_var.get(),
                           self.single_var.get(), self.hiq_var.get())
        except Exception as e:
            messagebox.showerror("Export error", str(e))
        self.destroy()


class SequenceAnalyzerApp(tk.Tk):
    def __init__(self, initial_folders: Optional[List[Path]] = None):
        super().__init__()
        self.title("MegaBACE Sequence Analyzer")
        self.geometry("1560x960")
        self.minsize(1120, 760)

        storage = _load_storage_settings()
        self.raw_storage = storage.get("raw", "")
        self.analyzed_storage = storage.get("analyzed", "")

        self.folders: List[Path] = list(initial_folders or [])
        self.files: List[Path] = []
        self.docs: dict[str, TraceDocument] = {}
        self.selected: List[Path] = []
        self.settings = AnalysisSettings()
        self.n_graphs = tk.IntVar(value=2)
        self.rows_wrap = tk.IntVar(value=4)
        self.view_mode = tk.StringVar(value="processed")
        self.basecaller = tk.StringVar(value="pos_bonus07")
        self.left_cutoff = tk.IntVar(value=0)
        self.status_var = tk.StringVar(value="Ready — add a data folder to begin")
        self.joint_scroll = tk.BooleanVar(value=True)
        self.no_empty_abds = tk.BooleanVar(value=False)

        # Visualization state
        self.chan_show = [tk.BooleanVar(value=True) for _ in BASE_LETTERS_ORDER]
        self.show_letters = tk.BooleanVar(value=True)
        self.show_qnum = tk.BooleanVar(value=False)
        self.show_qcurve = tk.BooleanVar(value=True)
        self.theme = tk.StringVar(value="Classic")

        self._zoom = {"x": (None, None), "y": (None, None)}
        self._current_tab = "electropherogram"

        self._build_menu()
        self._build_layout()
        self._bind_shortcuts()
        if self.folders:
            for p in self.folders:
                self.folder_list.insert(tk.END, str(p))
            self.refresh_file_list()
            self.folder_list.selection_set(0)
        self.after(120, self.try_auto_load_plate)

    # ------------------------------------------------------------------ UI
    def _bind_shortcuts(self):
        self.bind_all("<Control-l>", lambda e: self.add_folder())
        self.bind_all("<Control-a>", lambda e: self.select_all())
        self.bind_all("<Control-p>", lambda e: self.print_current())
        self.bind_all("<Control-f>", lambda e: self.export_fasta())
        self.bind_all("<Control-s>", lambda e: self.export_scf())
        self.bind_all("<Control-t>", lambda e: self.export_text())
        self.bind_all("<Control-b>", lambda e: self.export_abd())
        self.bind_all("<Control-F6>", lambda e: self.basecall_selected())
        self.bind_all("<F1>", lambda e: self.run_single_stage("baseline"))
        self.bind_all("<F2>", lambda e: self.run_single_stage("spectral"))
        self.bind_all("<F3>", lambda e: self.run_single_stage("normalize"))
        self.bind_all("<F4>", lambda e: self.run_single_stage("band"))
        self.bind_all("<F5>", lambda e: self.run_single_stage("mobility"))
        self.bind_all("<Escape>", lambda e: self.stop_processing())

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_m = tk.Menu(menubar, tearoff=0)
        file_m.add_command(label="Load plates from folder…  Ctrl+L", command=self.add_folder)
        file_m.add_command(label="Export to ABD  Ctrl+B", command=self.export_abd)
        file_m.add_command(label="Export to SCF  Ctrl+S", command=self.export_scf)
        file_m.add_command(label="Export to FASTA  Ctrl+F", command=self.export_fasta)
        file_m.add_command(label="Export to text  Ctrl+T", command=self.export_text)
        file_m.add_separator()
        file_m.add_command(label="Print  Ctrl+P", command=self.print_current)
        file_m.add_separator()
        file_m.add_command(label="Exit  Ctrl+Q", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_m)

        edit_m = tk.Menu(menubar, tearoff=0)
        edit_m.add_command(label="Select All Samples  Ctrl+A", command=self.select_all)
        menubar.add_cascade(label="Edit", menu=edit_m)

        opt_m = tk.Menu(menubar, tearoff=0)
        opt_m.add_command(label="Data storage…", command=self.data_storage_dialog)
        caller_m = tk.Menu(opt_m, tearoff=0)
        for name in MANUAL_BASECALLERS:
            internal = INTERNAL_CALLER_TO_GUILD.get(name, name)
            caller_m.add_radiobutton(
                label=name, variable=self.basecaller, value=internal,
                command=self._on_basecaller_change)
        opt_m.add_cascade(label="Base caller", menu=caller_m)
        opt_m.add_checkbutton(label="No 'empty' ABDs",
                              variable=self.no_empty_abds)
        menubar.add_cascade(label="Options", menu=opt_m)

        data_m = tk.Menu(menubar, tearoff=0)
        data_m.add_command(label="Perform base calling  Ctrl+F6", command=self.basecall_selected)
        data_m.add_command(label="Baseline subtraction  Ctrl+F1",
                           command=lambda: self.run_single_stage("baseline"))
        data_m.add_command(label="Spectral separation  Ctrl+F2",
                           command=lambda: self.run_single_stage("spectral"))
        data_m.add_command(label="Normalization  Ctrl+F3",
                           command=lambda: self.run_single_stage("normalize"))
        data_m.add_command(label="Band filter  Ctrl+F4",
                           command=lambda: self.run_single_stage("band"))
        data_m.add_command(label="Mobility shift  Ctrl+F5",
                           command=lambda: self.run_single_stage("mobility"))
        data_m.add_command(label="Quality assessment",
                           command=self.run_quality_assessment)
        data_m.add_separator()
        data_m.add_command(label="Stop processing  Esc", command=self.stop_processing)
        menubar.add_cascade(label="Data", menu=data_m)

        help_m = tk.Menu(menubar, tearoff=0)
        help_m.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_m)
        self.config(menu=menubar)

    def _build_layout(self):
        # Status bar
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(
            side=tk.BOTTOM, fill=tk.X)

        # Toolbars
        self._build_toolbars()

        # Paned windows: nav/sample-status | display
        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(body, width=330)
        body.add(left, weight=1)
        self._build_nav_pane(left)

        center = ttk.Frame(body)
        body.add(center, weight=6)
        self._build_display_pane(center)

        right = ttk.Frame(body, width=270)
        body.add(right, weight=1)
        self._build_right_pane(right)

    def _build_toolbars(self):
        bar = ttk.Frame(self)
        bar.pack(side=tk.TOP, fill=tk.X, padx=4, pady=2)

        # Main toolbar
        self._tb_btn(bar, "Load Plates", self.add_folder)
        self._tb_btn(bar, "Print", self.print_current)
        self._tb_btn(bar, "Base Call", self.basecall_selected)
        self._tb_btn(bar, "FASTA", self.export_fasta)
        self._tb_btn(bar, "SCF", self.export_scf)
        self._tb_btn(bar, "Text", self.export_text)
        self._tb_btn(bar, "ABD", self.export_abd)
        self._tb_btn(bar, "Stop", self.stop_processing)
        self._tb_btn(bar, "About", self.show_about)

        # Display toolbar (second row)
        bar2 = ttk.Frame(self)
        bar2.pack(side=tk.TOP, fill=tk.X, padx=4, pady=(0, 2))
        ttk.Label(bar2, text="Display:").pack(side=tk.LEFT)
        self._tb_btn(bar2, "Raw Trace", lambda: self.set_view("raw"))
        self._tb_btn(bar2, "Processed Trace", lambda: self.set_view("processed"))
        self._tb_btn(bar2, "Remove Trace(s)", self.remove_traces)
        self._tb_btn(bar2, "Remove All", self.remove_all)
        ttk.Separator(bar2, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=4)
        ttk.Label(bar2, text="Rows:").pack(side=tk.LEFT)
        for n in (1, 2, 3, 4):
            self._tb_btn(bar2, str(n), lambda n=n: self.set_rows(n))
        ttk.Separator(bar2, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=4)
        self._tb_btn(bar2, "Zoom X+", lambda: self.zoom("x", 0.8))
        self._tb_btn(bar2, "Zoom X-", lambda: self.zoom("x", 1.25))
        self._tb_btn(bar2, "Zoom Y+", lambda: self.zoom("y", 0.8))
        self._tb_btn(bar2, "Zoom Y-", lambda: self.zoom("y", 1.25))
        ttk.Checkbutton(bar2, text="Joint Scrolling", variable=self.joint_scroll).pack(side=tk.LEFT, padx=6)

    def _tb_btn(self, parent, text, cmd):
        b = ttk.Button(parent, text=text, command=cmd)
        b.pack(side=tk.LEFT, padx=2)
        return b

    def _build_nav_pane(self, parent: ttk.Frame):
        ttk.Label(parent, text="Navigation: plate folders",
                  font=("", 10, "bold")).pack(anchor="w", padx=4, pady=(4, 0))
        self.folder_list = tk.Listbox(parent, height=5, exportselection=False)
        self.folder_list.pack(fill=tk.X, padx=4, pady=2)
        self.folder_list.bind("<Double-Button-1>", lambda e: self.load_plate())
        fb = ttk.Frame(parent)
        fb.pack(fill=tk.X, padx=4)
        ttk.Button(fb, text="Add folder…", command=self.add_folder).pack(side=tk.LEFT)
        ttk.Button(fb, text="Load plate", command=self.load_plate).pack(side=tk.LEFT, padx=4)
        ttk.Button(fb, text="Remove", command=self.remove_folder).pack(side=tk.LEFT, padx=4)

        ttk.Label(parent, text="Sample status",
                  font=("", 10, "bold")).pack(anchor="w", padx=4, pady=(8, 0))
        cols = ("plate", "well", "sample", "run", "basecall", "export")
        widths = (100, 44, 80, 60, 44, 44)
        tree = ttk.Treeview(parent, columns=cols, show="headings", height=18,
                            selectmode="extended")
        for c, w in zip(cols, widths):
            tree.heading(c, text={"plate": "Plate ID", "well": "Well",
                                  "sample": "Sample ID", "run": "Run ID",
                                  "basecall": "Base call", "export": "Export"}[c],
                         anchor="center")
            tree.column(c, width=w, anchor="center", stretch=(c == "plate" or c == "sample"))
        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=2)
        vsb.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=2)
        self.sample_tree = tree
        tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        tree.bind("<Double-Button-1>", lambda e: self.basecall_selected())
        tree.bind("<Return>", lambda e: self.basecall_selected())

        # Graph count
        gb = ttk.Frame(parent)
        gb.pack(fill=tk.X, padx=4, pady=4)
        ttk.Label(gb, text="Graphs to show").pack(side=tk.LEFT)
        ttk.Spinbox(gb, from_=1, to=8, textvariable=self.n_graphs, width=4,
                    command=self.redraw).pack(side=tk.LEFT, padx=4)

    def _build_display_pane(self, parent: ttk.Frame):
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self.electropherogram_tab = ttk.Frame(self.notebook)
        self.sequence_tab = ttk.Frame(self.notebook)
        self.wrap_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.electropherogram_tab, text="Electropherogram")
        self.notebook.add(self.sequence_tab, text="Sequence")
        self.notebook.add(self.wrap_tab, text="Wrap")

        # --- Electropherogram tab ---
        chan_bar = ttk.Frame(self.electropherogram_tab)
        chan_bar.pack(fill=tk.X, padx=4, pady=(4, 0))
        ttk.Label(chan_bar, text="Trace channels:").pack(side=tk.LEFT)
        for i, base in enumerate(BASE_LETTERS_ORDER):
            cb = tk.Checkbutton(
                chan_bar, text=f"  {base}  ", variable=self.chan_show[i],
                command=self.redraw, fg=CHANNEL_COLORS[base],
                activeforeground=CHANNEL_COLORS[base], selectcolor="white")
            cb.pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(chan_bar, text="Base letters", variable=self.show_letters,
                        command=self.redraw).pack(side=tk.LEFT, padx=6)
        ttk.Checkbutton(chan_bar, text="Q numbers", variable=self.show_qnum,
                        command=self.redraw).pack(side=tk.LEFT, padx=2)
        ttk.Checkbutton(chan_bar, text="Q curve", variable=self.show_qcurve,
                        command=self.redraw).pack(side=tk.LEFT, padx=2)
        theme_lbl = ttk.Label(chan_bar, text="Theme:")
        theme_lbl.pack(side=tk.LEFT, padx=(10, 2))
        theme_cb = ttk.Combobox(chan_bar, textvariable=self.theme, state="readonly",
                                width=12, values=list(TRACE_THEMES))
        theme_cb.pack(side=tk.LEFT)
        theme_cb.bind("<<ComboboxSelected>>", lambda e: self.redraw())

        # Left Cut Off list box
        coco = ttk.Frame(self.electropherogram_tab)
        coco.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(coco, text="Left Cut Off:").pack(side=tk.LEFT)
        cut_vals = [0, 500, 1000, 1500, 2000, 2500, 3000, 3500]
        self.left_cut_combo = ttk.Combobox(
            coco, textvariable=self.left_cutoff, values=cut_vals, width=8)
        self.left_cut_combo.set(0)
        self.left_cut_combo.pack(side=tk.LEFT, padx=4)
        self.left_cut_combo.bind("<<ComboboxSelected>>", lambda e: self.redraw())

        self.fig = Figure(figsize=(11, 7.5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.electropherogram_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4)
        self.canvas.mpl_connect("scroll_event", self._on_scroll_wheel)
        self.canvas.mpl_connect("button_press_event", self._on_press)
        self.canvas.mpl_connect("button_release_event", self._on_release)
        tb = NavigationToolbar2Tk(self.canvas, self.electropherogram_tab)
        tb.update()

        # --- Sequence tab ---
        st = ttk.Frame(self.sequence_tab)
        st.pack(fill=tk.BOTH, expand=True)
        qbox = ttk.LabelFrame(st, text="Quality")
        qbox.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)
        ttk.Label(qbox, text="Quality profile:  ").pack(side=tk.LEFT)
        tk.Label(qbox, text="▓▓▓▓  good (blue-green)", fg=QUALITY_GOOD, bg="white").pack(side=tk.LEFT)
        tk.Label(qbox, text="  ▓▓▓▓  poor (brown)", fg=QUALITY_POOR, bg="white").pack(side=tk.LEFT)
        self.seq_text = scrolledtext.ScrolledText(
            st, wrap=tk.NONE, font=("Courier", 10), width=120, height=26)
        self.seq_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # --- Wrap tab ---
        rowb = ttk.Frame(self.wrap_tab)
        rowb.pack(fill=tk.X, padx=4, pady=2)
        ttk.Label(rowb, text="Rows per screen:").pack(side=tk.LEFT)
        for n in (2, 3, 4, 5):
            ttk.Button(rowb, text=str(n),
                       command=lambda n=n: self.set_wrap_rows(n)).pack(side=tk.LEFT, padx=2)
        self.wrap_fig = Figure(figsize=(11, 7.5), dpi=100)
        self.wrap_canvas = FigureCanvasTkAgg(self.wrap_fig, master=self.wrap_tab)
        self.wrap_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=4)
        ttk.Button(self.wrap_tab, text="Redraw wrap", command=self.redraw_wrap).pack(pady=2)

    def _build_right_pane(self, parent: ttk.Frame):
        canvas = tk.Canvas(parent, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor=tk.NW)
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        def section(title: str) -> ttk.LabelFrame:
            f = ttk.LabelFrame(inner, text=title, padding=4)
            f.pack(fill=tk.X, padx=4, pady=4)
            return f

        # Base Caller list box
        f = section("Base Caller")
        self.basecaller_listbox = tk.Listbox(f, height=len(MANUAL_BASECALLERS),
                                             exportselection=False)
        for name in MANUAL_BASECALLERS:
            self.basecaller_listbox.insert(tk.END, name)
        self.basecaller_listbox.selection_set(0)
        self.basecaller_listbox.bind(
            "<<ListboxSelect>>",
            lambda e: self._set_caller_from_listbox())
        self.basecaller_listbox.pack(fill=tk.X)

        # Dye order
        f = section("Dye / channel")
        self.base_order_var = tk.StringVar(value=self.settings.base_order)
        ttk.Label(f, text="Base order (instrument)").pack(anchor="w")
        ttk.Combobox(
            f, textvariable=self.base_order_var, values=["TGCA", "ACGT", "GATC", "CTAG"],
            width=12).pack(anchor="w")

        # Baseline
        f = section("Baseline")
        self.bl_enable = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Enable baseline", variable=self.bl_enable).pack(anchor="w")
        self.bl_win = tk.IntVar(value=self.settings.baseline_window)
        ttk.Label(f, text="Window").pack(anchor="w")
        ttk.Scale(f, from_=51, to=401, variable=self.bl_win, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Spectral / mobility
        f = section("Spectral & mobility")
        self.spec_en = tk.BooleanVar(value=True)
        self.spec_adapt = tk.BooleanVar(value=True)
        self.mob_en = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Spectral separation", variable=self.spec_en).pack(anchor="w")
        ttk.Checkbutton(f, text="Position-adaptive matrix", variable=self.spec_adapt).pack(anchor="w")
        ttk.Checkbutton(f, text="Mobility correction", variable=self.mob_en).pack(anchor="w")

        # Band filter
        f = section("Band filter (deconv)")
        self.gauss_en = tk.BooleanVar(value=True)
        self.gauss_seg = tk.IntVar(value=384)
        self.gauss_reg = tk.DoubleVar(value=0.05)
        ttk.Checkbutton(f, text="Gaussian reconstruction", variable=self.gauss_en).pack(anchor="w")
        ttk.Label(f, text="Segment size").pack(anchor="w")
        ttk.Scale(f, from_=128, to=1024, variable=self.gauss_seg, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(f, text="Noise reg").pack(anchor="w")
        ttk.Scale(f, from_=0.01, to=0.2, variable=self.gauss_reg, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Spacing tracker
        f = section("Spacing tracker")
        self.bonus = tk.DoubleVar(value=0.7)
        self.pullback = tk.DoubleVar(value=0.008)
        self.ema = tk.DoubleVar(value=0.08)
        self.wlo = tk.DoubleVar(value=0.70)
        self.whi = tk.DoubleVar(value=1.30)
        ttk.Label(f, text="Channel peak bonus").pack(anchor="w")
        ttk.Scale(f, from_=0.0, to=1.5, variable=self.bonus, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(f, text="Pullback weight").pack(anchor="w")
        ttk.Scale(f, from_=0.0, to=0.03, variable=self.pullback, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(f, text="EMA alpha").pack(anchor="w")
        ttk.Scale(f, from_=0.02, to=0.25, variable=self.ema, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Scan region
        f = section("Scan region (display)")
        self.scan_start = tk.IntVar(value=0)
        self.scan_end = tk.IntVar(value=0)
        ttk.Label(f, text="Start (0=auto)").pack(anchor="w")
        ttk.Entry(f, textvariable=self.scan_start, width=10).pack(anchor="w")
        ttk.Label(f, text="End (0=full)").pack(anchor="w")
        ttk.Entry(f, textvariable=self.scan_end, width=10).pack(anchor="w")

        bf = ttk.Frame(inner)
        bf.pack(fill=tk.X, padx=4, pady=8)
        ttk.Button(bf, text="Apply knobs + redraw", command=self.apply_knobs_redraw).pack(fill=tk.X, pady=2)
        ttk.Button(bf, text="Basecall with knobs", command=self.basecall_selected).pack(fill=tk.X, pady=2)

    def _set_caller_from_listbox(self):
        sel = self.basecaller_listbox.curselection()
        if sel:
            name = MANUAL_BASECALLERS[sel[0]]
            self.basecaller.set(INTERNAL_CALLER_TO_GUILD.get(name, name))
            self.status_var.set(f"Base caller: {name}")

    def _on_basecaller_change(self):
        internal = self.basecaller.get()
        name = INTERNAL_CALLER_TO_GUILD.get(internal, internal)
        for i, n in enumerate(MANUAL_BASECALLERS):
            if n == name:
                self.basecaller_listbox.selection_clear(0, tk.END)
                self.basecaller_listbox.selection_set(i)
                break

    # ------------------------------------------------------------------ data
    def add_folder(self):
        d = filedialog.askdirectory(title="Select folder containing .rsd / .esd files")
        if not d:
            return
        p = Path(d)
        if p not in self.folders:
            self.folders.append(p)
            self.folder_list.insert(tk.END, str(p))
        self.refresh_file_list()

    def load_plate(self):
        sel = self.folder_list.curselection()
        if not sel:
            messagebox.showinfo("Load plate", "Choose a plate folder in the navigation pane.")
            return
        self.container_dir = Path(self.folder_list.get(sel[0]))
        self.refresh_file_list()

    def remove_folder(self):
        sel = list(self.folder_list.curselection())
        if not sel:
            return
        for i in reversed(sel):
            path = Path(self.folder_list.get(i))
            self.folder_list.delete(i)
            if path in self.folders:
                self.folders.remove(path)
        self.refresh_file_list()

    def clear_folders(self):
        self.folders.clear()
        self.folder_list.delete(0, tk.END)
        self.refresh_file_list()

    def try_auto_load_plate(self):
        if not self.folders:
            return
        example = self._find_example_plate_folder()
        if example is not None:
            self.container_dir = example
            self.refresh_file_list()
            self.status_var.set(f"Loaded plate folder: {example}")

    def _find_example_plate_folder(self) -> Optional[Path]:
        """Pick the container dir: a folder holding *.rsd directly, else a
        plate-root subfolder (e.g. MB1000_M13_DT/Cp312_MD1)."""
        for folder in self.folders:
            if list(folder.glob("*.rsd")):
                return folder
            try:
                subs = sorted([p for p in folder.iterdir() if p.is_dir()])
            except Exception:
                subs = []
            for sub in subs:
                if list(sub.glob("*.rsd")):
                    return sub
        return None

    def refresh_file_list(self):
        self.files = discover_rsd(self.folders)
        self._populate_status_tree(self.files)
        self.status_var.set(
            f"{len(self.files)} .rsd wells · {len(self.folders)} folder(s)")

    def _populate_status_tree(self, files: List[Path]):
        tree = self.sample_tree
        for item in tree.get_children():
            tree.delete(item)
        for f in files:
            well = f.stem
            plate = f.parent.name
            tree.insert("", "end", values=(
                plate, well, well, "", "", ""))
        if files:
            first = files[0]
            plate = first.parent.name
            self.status_var.set(f"Plate '{plate}': {len(files)} wells loaded. "
                                f"Select wells and press ENTER / Base Call.")

    def on_tree_select(self, _evt=None):
        ids = self.sample_tree.selection()
        self.selected = []
        platemap = {}
        for f in self.files:
            platemap[(f.parent.name, f.stem)] = f
        for iid in ids:
            vals = self.sample_tree.item(iid)["values"]
            if vals:
                self.selected.append(platemap.get((vals[0], vals[1])))
        self.selected = [p for p in self.selected if p is not None]
        self.redraw()

    def select_all(self):
        for item in self.sample_tree.get_children():
            self.sample_tree.selection_add(item)
        self.on_tree_select()
        self.status_var.set(f"Selected all {len(self.selected)} samples")

    # ------------------------------------------------------------------ analysis
    def set_view(self, mode: str | None = None):
        if mode is not None:
            self.view_mode.set(mode)
        self.reset_zoom()
        self.redraw()

    def reset_zoom(self):
        self._zoom = {"x": (None, None), "y": (None, None)}

    def set_rows(self, n: int):
        self.n_graphs.set(n)
        self.redraw()

    def set_wrap_rows(self, n: int):
        self.rows_wrap.set(n)
        self.redraw_wrap()

    def zoom(self, axis: str, factor: float):
        x0, x1 = self._zoom["x"]
        if x0 is None:
            for ax in self.fig.axes:
                if axis == "x":
                    x0, x1 = ax.get_xlim()
        for ax in self.fig.axes:
            if axis == "x":
                x0, x1 = self._zoom["x"] if self._zoom["x"][0] is not None else ax.get_xlim()
                mid = (x0 + x1) / 2
                w = (x1 - x0) * factor
                ax.set_xlim(mid - w / 2, mid + w / 2)
                self._zoom["x"] = ax.get_xlim()
            else:
                y0, y1 = ax.get_ylim()
                mid = (y0 + y1) / 2
                w = (y1 - y0) * factor
                ax.set_ylim(mid - w / 2, mid + w / 2)
                if self._zoom["y"][0] is None:
                    self._zoom["y"] = ax.get_ylim()
        self.canvas.draw_idle()

    def _on_scroll_wheel(self, event):
        """Scroll to left/right; with joint scrolling all panes move together."""
        if event.inaxes is None:
            return
        scale = 1.1 if event.step > 0 else 0.9
        ax = event.inaxes
        x0, x1 = ax.get_xlim()
        w = x1 - x0
        target = event.xdata
        if self.joint_scroll.get():
            for a in self.fig.axes:
                a.set_xlim(target - (target - x0) * scale,
                           target + (x1 - target) * scale)
        else:
            ax.set_xlim(target - (target - x0) * scale,
                        target + (x1 - target) * scale)
        self.canvas.draw_idle()

    def _on_press(self, event):
        if event.button != 1:
            return
        self._press_xy = (event.x, event.y)
        self._press_xdata = event.xdata

    def _on_release(self, event):
        if getattr(self, "_press_xy", None) is None:
            return
        if event.button != 1 or event.inaxes is None:
            self._press_xy = None
            return
        dx = event.x - self._press_xy[0]
        if abs(dx) > 20 and self._press_xdata is not None:
            # drag to zoom along x
            w0 = self._press_xdata
            w1 = event.xdata or w0
            a = event.inaxes
            for ax in self.fig.axes:
                if self.joint_scroll.get() or ax is a:
                    ax.set_xlim(min(w0, w1), max(w0, w1))
        self._press_xy = None
        self.canvas.draw_idle()

    def remove_traces(self):
        """Remove selected trace(s) from display only (files retained)."""
        self.selected = []
        self.sample_tree.selection_remove(*(self.sample_tree.selection()))
        self.redraw()
        self.status_var.set("Removed selected trace(s) from display (files retained).")

    def remove_all(self):
        self.selected = []
        self.sample_tree.selection_remove(*(self.sample_tree.get_children()))
        self.redraw()
        self.status_var.set("Removed all samples from display (files retained in plate folder).")

    def _settings_from_ui(self) -> AnalysisSettings:
        s = AnalysisSettings(
            basecaller=self.basecaller.get(),
            base_order=self.base_order_var.get(),
            baseline_window=int(self.bl_win.get()),
            spectral_enable=self.spec_en.get(),
            position_adaptive_spectral=self.spec_adapt.get(),
            mobility_enable=self.mob_en.get(),
            use_gaussian_reconstruction=self.gauss_en.get(),
            gaussian_recon_segment_size=int(self.gauss_seg.get()),
            gaussian_recon_noise_reg=float(self.gauss_reg.get()),
            channel_peak_bonus=float(self.bonus.get()),
            pullback_weight=float(self.pullback.get()),
            ema_alpha=float(self.ema.get()),
            window_frac_lo=float(self.wlo.get()),
            window_frac_hi=float(self.whi.get()),
            view_mode=self.view_mode.get(),
            signal_start=int(self.scan_start.get()),
            signal_end=int(self.scan_end.get()),
        )
        return s

    def apply_knobs_redraw(self):
        self.settings = self._settings_from_ui()
        self.redraw()
        self.status_var.set("Knobs applied.")

    def _ensure_doc(self, path: Path) -> TraceDocument:
        key = str(path.resolve())
        if key not in self.docs:
            self.status_var.set(f"Loading {path.name}…")
            self.update_idletasks()
            self.docs[key] = load_rsd(path, base_order=self.base_order_var.get())
        return self.docs[key]

    def basecall_selected(self):
        if not self.selected:
            messagebox.showinfo("Basecall", "Select one or more wells in the list.")
            return
        self.settings = self._settings_from_ui()
        self.status_var.set(f"Base calling {len(self.selected)} well(s)…")
        self.update_idletasks()
        try:
            for path in self.selected:
                key = str(path.resolve())
                if key not in self.docs:
                    self.docs[key] = load_rsd(path, base_order=self.settings.base_order)
                doc = self.docs[key]
                self.update_idletasks()
                run_basecall(doc, self.settings)
                self._mark_status(path, "called", "✓")
            # quality assessment after all calls
            for path in self.selected:
                doc = self.docs[str(path.resolve())]
                q, idx = assess_quality(doc, self.settings)
                doc.qualities = q[: len(doc.sequence)] if len(q) else []
                doc.quality_index = idx if q else 0.0
        except Exception as ex:
            messagebox.showerror("Basecall error", str(ex))
            return
        self.status_var.set("Base calling complete.")
        self.redraw()
        self._show_sequence()
        self.notebook.select(self.electropherogram_tab)

    def basecall_all(self):
        if not self.files:
            return
        self.selected = list(self.files)
        self.basecall_selected()

    def run_single_stage(self, stage: str):
        """Data-menu incremental processing stage."""
        if not self.selected:
            messagebox.showinfo("Stage", "Select samples first.")
            return
        self.settings = self._settings_from_ui()
        label = dict(INCREMENTAL_STAGES).get(stage, stage)
        self.status_var.set(f"{label}…")
        self.update_idletasks()
        try:
            for path in self.selected:
                doc = self._ensure_doc(path)
                stage_document(doc, self.settings, stage)
        except Exception as ex:
            messagebox.showerror("Stage error", str(ex))
            return
        self.view_mode.set(stage)
        self.reset_zoom()
        self.redraw()
        self.status_var.set(f"{label} complete.")

    def run_quality_assessment(self):
        if not self.selected:
            messagebox.showinfo("Quality", "Select samples first.")
            return
        self.settings = self._settings_from_ui()
        total_idx = []
        for path in self.selected:
            doc = self._ensure_doc(path)
            if not doc.sequence:
                run_basecall(doc, self.settings)
            q, idx = assess_quality(doc, self.settings)
            doc.qualities = q[: len(doc.sequence)] if len(q) else []
            doc.quality_index = idx if q else 0.0
            total_idx.append(idx)
        self.redraw()
        self._show_sequence()
        self.status_var.set(
            f"Quality assessed. index mean={np.mean(total_idx):.1f} "
            f"(blue-green ≥ 30 = good, brown < 30 = poor).")

    def stop_processing(self):
        self.status_var.set("Processing stopped.")
        self.update_idletasks()

    # ------------------------------------------------------------------ plot
    def _theme_colors(self) -> dict:
        return dict(TRACE_THEMES.get(self.theme.get(), "Classic"))

    def _on_tab_changed(self, _evt=None):
        self._current_tab = self.notebook.tab(self.notebook.select(), "text")
        if self._current_tab == "Wrap":
            self.redraw_wrap()

    def _well_stats(self, doc) -> str:
        """One-line stats for a basecalled well."""
        seq, q = doc.sequence, doc.qualities
        n = len(seq)
        qi = getattr(doc, "quality_index", 0.0)
        if n == 0:
            return "not basecalled"
        qa = np.asarray(q[:n], dtype=float) if q else np.array([], dtype=float)
        qmean = float(qa.mean()) if qa.size else 0.0
        nN = seq.count("N")
        gc = 100.0 * (seq.count("G") + seq.count("C")) / n if n else 0.0
        pos = np.asarray(doc.peak_positions[:n], dtype=float)
        sp = float(np.median(np.diff(pos))) if pos.size > 1 else 0.0
        return (f"len={n} Qmean={qmean:.0f} Qindex={qi:.0f} "
                f"GC={gc:.0f}% N={nN} sp={sp:.1f} scans")

    def _signal_bounds(self, doc, settings):
        s0 = max(0, settings.signal_start)
        s1 = settings.signal_end if settings.signal_end > 0 else doc.acgt.shape[0]
        s1 = min(doc.acgt.shape[0], s1)
        cut = int(self.left_cutoff.get() or 0)
        s0 = max(s0, cut)
        return s0, s1

    def redraw(self):
        self.fig.clear()
        colors = self._theme_colors()
        n = max(1, min(8, self.n_graphs.get()))
        paths = self.selected[:n] if self.selected else []
        if not paths:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "Select wells in the Sample-status pane (ENTER = base call)",
                    ha="center", va="center")
            ax.set_axis_off()
            self.canvas.draw_idle()
            return

        settings = self._settings_from_ui()
        for i, path in enumerate(paths):
            ax = self.fig.add_subplot(len(paths), 1, i + 1)
            try:
                doc = self._ensure_doc(path)
            except Exception as e:
                ax.text(0.5, 0.5, f"Load error: {e}", ha="center", transform=ax.transAxes)
                continue
            tr = display_trace(doc, settings)
            s0, s1 = self._signal_bounds(doc, settings)
            if s1 <= s0:
                s1 = tr.shape[0]
            x = np.arange(s0, s1)
            plotted = False
            for ci, base in enumerate(BASE_LETTERS_ORDER):
                if not self.chan_show[ci].get():
                    continue
                ax.plot(x, tr[s0:s1, ci], color=colors[base], lw=0.7, label=base)
                plotted = True
            if not plotted:
                ax.text(0.5, 0.5, "(all channels hidden)",
                        ha="center", va="center", transform=ax.transAxes, color="#888")
            # quality profile on twin axis (blue-green = good, brown = poor)
            qd = getattr(doc, "quality", None)
            pos_peaks = np.asarray(doc.peak_positions, dtype=float)
            qq = np.asarray(doc.qualities[: len(pos_peaks)], dtype=float) \
                if doc.qualities else np.array([])
            if (self.show_qcurve.get() and len(qq) == len(pos_peaks) and qq.size
                    and settings.view_mode not in ("raw",)):
                ax2 = ax.twinx()
                good_c = qq >= 30.0
                if good_c.any():
                    ax2.scatter(pos_peaks[good_c], qq[good_c], s=4, color=QUALITY_GOOD, zorder=6)
                if (~good_c).any():
                    ax2.scatter(pos_peaks[~good_c], qq[~good_c], s=4, color=QUALITY_POOR, zorder=6)
                ax2.set_ylabel("quality", fontsize=7, color="#666")
                ax2.tick_params(axis="y", labelsize=7)
                ax2.set_ylim(0, 100)
                ax2.yaxis.set_label_position("right")

            ax.set_ylabel(doc.well, fontsize=8)
            ax.tick_params(labelsize=7)
            if i == 0 and plotted:
                ax.legend(loc="upper right", fontsize=7, ncol=4)
            if i == len(paths) - 1:
                ax.set_xlabel("Scan")
            else:
                ax.set_xlabel("")

            if doc.sequence and settings.view_mode in ("called", "baseline",
                                                       "spectral", "normalize",
                                                       "band", "mobility") and doc.peak_positions:
                seq = doc.sequence
                q = np.asarray(doc.qualities[: len(seq)], dtype=float) if doc.qualities else np.array([])
                pos = np.asarray(doc.peak_positions[: len(seq)], dtype=float)
                med_sp = float(np.median(np.diff(pos))) if pos.size > 1 else 0.0
                ytop = float(np.nanmax(tr[s0:s1])) if tr[s0:s1].size else 1.0
                if ytop <= 0:
                    ytop = 1.0
                tight = (s1 - s0) > 1400
                draw_let = (not tight) or med_sp >= 10
                draw_q = self.show_qnum.get() and med_sp >= 16
                for pi, let in enumerate(seq):
                    if pi >= len(pos) or let not in colors:
                        continue
                    p = int(pos[pi])
                    if not (s0 <= p < s1):
                        continue
                    ax.axvline(p, color=colors[let], alpha=0.20, lw=0.5, zorder=1)
                    if draw_let:
                        ax.text(p, ytop + 0.01 * ytop, let, color=colors[let],
                                ha="center", va="bottom", fontsize=7, zorder=5, clip_on=True)
                    if draw_q and pi < len(q):
                        ax.text(p, -0.02 * ytop, f"{q[pi]:.0f}", color="#B8860B",
                                ha="center", va="top", fontsize=6, zorder=5, clip_on=True)
                if not draw_let:
                    ax.text(0.01, 1.02, "bases too dense — zoom to show letters",
                            transform=ax.transAxes, fontsize=6, color="#888")
            if self._zoom["x"][0] is not None:
                ax.set_xlim(*self._zoom["x"])
            if self._zoom["y"][0] is not None:
                ax.set_ylim(*self._zoom["y"])
        self.fig.tight_layout()
        self.canvas.draw_idle()
        self._show_sequence()

    def _show_sequence(self):
        self.seq_text.delete("1.0", tk.END)
        for path in self.selected[: self.n_graphs.get()]:
            key = str(path.resolve())
            doc = self.docs.get(key)
            if not doc or not doc.sequence:
                continue
            self.seq_text.insert(tk.END, f">{doc.well} {self._well_stats(doc)}\n")
            seq = doc.sequence
            for i in range(0, len(seq), 50):
                chunk = seq[i:i + 50]
                self.seq_text.insert(tk.END, f"{i + 1:5d}  {chunk}\n")
            self.seq_text.insert(tk.END, "\n")

    def redraw_wrap(self):
        self.wrap_fig.clear()
        colors = self._theme_colors()
        if not self.selected:
            ax = self.wrap_fig.add_subplot(111)
            ax.text(0.5, 0.5, "Select one sample for the Wrap tab", ha="center", va="center")
            ax.set_axis_off()
            self.wrap_canvas.draw_idle()
            return
        path = self.selected[0]
        settings = self._settings_from_ui()
        try:
            doc = self._ensure_doc(path)
        except Exception as e:
            ax = self.wrap_fig.add_subplot(111)
            ax.text(0.5, 0.5, f"Load error: {e}", ha="center", transform=ax.transAxes)
            self.wrap_canvas.draw_idle()
            return
        tr = display_trace(doc, settings)
        rows = max(2, min(5, self.rows_wrap.get()))
        per = int(np.ceil(tr.shape[0] / rows))
        s0 = max(0, int(self.left_cutoff.get() or 0))
        for r in range(rows):
            ax = self.wrap_fig.add_subplot(rows, 1, r + 1)
            a = s0 + r * per
            b = min(tr.shape[0], a + per)
            if b <= a:
                ax.axis("off")
                continue
            x = np.arange(a, b)
            for ci, base in enumerate(BASE_LETTERS_ORDER):
                if not self.chan_show[ci].get():
                    continue
                ax.plot(x, tr[a:b, ci], color=colors[base], lw=0.7)
            ax.set_xlim(a, b)
            ax.set_ylabel(doc.well, fontsize=8)
            ax.tick_params(labelsize=6)
        self.wrap_fig.tight_layout()
        self.wrap_canvas.draw_idle()

    # ------------------------------------------------------------------ I/O
    def _mark_status(self, path: Path, which: str, value: str):
        for item in self.sample_tree.get_children():
            vals = self.sample_tree.item(item)["values"]
            if vals and vals[1] == path.stem and vals[0] == path.parent.name:
                cur = list(vals)
                cur[4 if which == "basecall" else 5] = value
                self.sample_tree.item(item, values=tuple(cur))
                return

    def _export_dir(self, suffix: str = "") -> Path:
        base = self.raw_storage or (self.container_dir if hasattr(self, "container_dir") else "")
        if not base:
            base = str(Path.cwd())
        return Path(base)

    def export_fasta(self):
        if not self.selected:
            messagebox.showinfo("Export", "Select basecalled wells first.")
            return
        default_dir = str(self._export_dir())
        ExportOptionsDialog(self, default_dir, self._do_export_fasta)

    def _do_export_fasta(self, folder: Path, fname: str, individual: bool,
                         hiq: bool):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        n = 0
        for p in self.selected:
            doc = self.docs.get(str(p.resolve()))
            if not doc or not doc.sequence:
                continue
            if individual:
                export_fasta(doc, folder / f"{doc.well}.seq", hiq)
            else:
                target = folder / (fname or "all_reads.seq")
                lines = []
                if target.exists():
                    lines = target.read_text().splitlines()
                fasta = f">{doc.well} len={len(doc.sequence)} plate={doc.path.parent.name}\n" \
                    f"{doc.sequence}\n"
                with target.open("a") as fh:
                    fh.write(fasta)
            self._mark_status(p, "export", "FASTA")
            n += 1
        self.status_var.set(f"Exported {n} well(s) to {folder}")

    def export_scf(self):
        if not self.selected:
            messagebox.showinfo("Export", "Select basecalled wells first.")
            return
        folder = self._export_dir("scf")
        d = filedialog.askdirectory(title="Select SCF output folder",
                                    initialdir=str(folder))
        if not d:
            return
        out = Path(d)
        n = 0
        for p in self.selected:
            doc = self.docs.get(str(p.resolve()))
            if not doc or not doc.sequence:
                continue
            export_scf(doc, out / f"{doc.well}.scf")
            self._mark_status(p, "export", "SCF")
            n += 1
        self.status_var.set(f"Exported {n} SCF file(s) to {out}")

    def export_abd(self):
        if not self.selected:
            messagebox.showinfo("Export", "Select basecalled wells first.")
            return
        d = filedialog.askdirectory(title="Select ABD output folder",
                                    initialdir=str(self._export_dir("abd")))
        if not d:
            return
        out = Path(d)
        n = 0
        for p in self.selected:
            doc = self.docs.get(str(p.resolve()))
            if not doc or not doc.sequence:
                if self.no_empty_abds.get():
                    continue
                doc = self._ensure_doc(p)
            export_abd(doc, out / f"{doc.well}.abd")
            self._mark_status(p, "export", "ABD")
            n += 1
        self.status_var.set(f"Exported {n} ABD file(s) to {out}")

    def export_text(self):
        if not self.selected:
            messagebox.showinfo("Export", "Select samples first.")
            return
        d = filedialog.askdirectory(title="Select text output folder",
                                    initialdir=str(self._export_dir("txt")))
        if not d:
            return
        out = Path(d)
        n = 0
        for p in self.selected:
            doc = self._ensure_doc(p)
            export_text(doc, out / f"{doc.well}.txt")
            self._mark_status(p, "export", "text")
            n += 1
        self.status_var.set(f"Exported {n} text file(s) to {out}")

    def print_current(self):
        """Send the current Electropherogram (or Wrap) figure to the printer."""
        fig = self.wrap_fig if self._current_tab == "Wrap" else self.fig
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            fig.savefig(tmp.name, dpi=150)
        except Exception as e:
            messagebox.showerror("Print", f"Could not render: {e}")
            return
        cmd = None
        if sys.platform.startswith("linux"):
            cmd = ["lp", tmp.name]
        elif sys.platform == "darwin":
            cmd = ["lp", tmp.name]
        elif os.name == "nt":
            import os as _os
            _os.startfile(tmp.name, "print")  # type: ignore
            return
        if cmd:
            try:
                subprocess.run(cmd, check=False)
                self.status_var.set(f"Sent {tmp.name} to the printer.")
            except Exception as e:
                messagebox.showinfo("Print",
                                    f"Printed to PDF (no printer command): {tmp.name}\n{e}")

    def data_storage_dialog(self):
        DataStorageDialog(self, self.raw_storage, self.analyzed_storage,
                          self._apply_storage)

    def _apply_storage(self, raw: str, analyzed: str):
        self.raw_storage = raw
        self.analyzed_storage = analyzed
        _save_storage_settings({"raw": raw, "analyzed": analyzed})
        self.status_var.set("Data storage locations updated.")

    def save_settings(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                            filetypes=[("JSON", "*.json")])
        if not path:
            return
        s = self._settings_from_ui()
        Path(path).write_text(json.dumps(s.__dict__, indent=2))
        self.status_var.set(f"Saved settings to {path}")

    def load_settings(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        data = json.loads(Path(path).read_text())
        for k, v in data.items():
            if hasattr(self.settings, k):
                setattr(self.settings, k, v)
        self.basecaller.set(data.get("basecaller", "pos_bonus07"))
        self.base_order_var.set(data.get("base_order", "TGCA"))
        self.bonus.set(data.get("channel_peak_bonus", 0.7))
        self.pullback.set(data.get("pullback_weight", 0.008))
        self.status_var.set(f"Loaded settings from {path}")

    def show_about(self):
        messagebox.showinfo(
            "About",
            "MegaBACE Sequence Analyzer (Python)\n\n"
            "Match to the Sequence Analyzer User's Guide v2.0:\n"
            "• Navigation + Sample-status panes\n"
            "• Electropherogram / Sequence / Wrap tabs\n"
            "• Cimarron 1.53 Slim Phredify / Phat / 1.31, Molecular Dynamics\n"
            "• Incremental stages: baseline, spectral, normalize, band, mobility\n"
            "• Quality profile (good = blue-green, poor = brown) 0–100\n"
            "• Export FASTA (with high-Q option), SCF, ABD, text\n"
            "• Print, data storage, joint scrolling, zoom X/Y, rows-per-screen\n\n"
            "Reads .rsd (raw) and .esd (analyzed) via best_basecaller release.",
        )


def main():
    ap = argparse.ArgumentParser(description="MegaBACE Sequence Analyzer")
    ap.add_argument("--folder", action="append", type=Path,
                    help="Data folder (repeatable)")
    args = ap.parse_args()
    app = SequenceAnalyzerApp(initial_folders=args.folder)
    app.mainloop()


if __name__ == "__main__":
    main()