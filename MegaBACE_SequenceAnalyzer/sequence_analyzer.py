#!/usr/bin/env python3
"""
MegaBACE Sequence Analyzer (Python)
====================================
Desktop UI inspired by Molecular Dynamics MegaBACE Sequence Analyzer:

  • Multi-folder project load
  • File list of .rsd wells
  • 1–8 electropherogram panes
  • Raw / processed / base-called views
  • Basecaller versions (pos_bonus07, pos_profile, hz_soften, raw_peaks)
  • Analysis knobs: baseline, spectral, mobility, band-filter, spacing tracker

Requires: Python 3.10+ with tkinter, numpy, matplotlib
  Windows/macOS: tkinter usually included
  Linux: sudo apt install python3-tk

Run:
  python sequence_analyzer.py
  python sequence_analyzer.py --folder /path/to/rsd_dir
"""
from __future__ import annotations

import argparse
import json
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from typing import List, Optional

import numpy as np

# matplotlib embedded
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from analyzer_core import (
    AnalysisSettings,
    BASECALLER_VERSIONS,
    TraceDocument,
    discover_rsd,
    load_rsd,
    run_basecall,
    display_trace,
)

# Dye colours (classic chromatogram look)
CHANNEL_COLORS = {"A": "#00AA00", "C": "#0000DD", "G": "#111111", "T": "#DD0000"}
CHANNEL_ORDER = "ACGT"
QUALITY_COLOR = "#FF8C00"

TRACE_THEMES = {
    "Classic": {"A": "#00AA00", "C": "#0000DD", "G": "#111111", "T": "#DD0000"},
    "Chromas": {"A": "#00AA00", "C": "#1E90FF", "G": "#444444", "T": "#FF0000"},
    "High-contrast": {"A": "#2E8B57", "C": "#1F4FC0", "G": "#000000", "T": "#E03030"},
    "Monochrome": {"A": "#777777", "C": "#555555", "G": "#333333", "T": "#888888"},
}


class SequenceAnalyzerApp(tk.Tk):
    def __init__(self, initial_folders: Optional[List[Path]] = None):
        super().__init__()
        self.title("MegaBACE Sequence Analyzer")
        self.geometry("1400x900")
        self.minsize(1000, 700)

        self.folders: List[Path] = list(initial_folders or [])
        self.files: List[Path] = []
        self.docs: dict[str, TraceDocument] = {}  # path str → doc
        self.selected: List[Path] = []
        self.settings = AnalysisSettings()
        self.n_graphs = tk.IntVar(value=1)
        self.view_mode = tk.StringVar(value="processed")
        self.basecaller = tk.StringVar(value="pos_bonus07")
        self.status_var = tk.StringVar(value="Ready — add a data folder to begin")

        # Visualization state
        self.chan_show = [tk.BooleanVar(value=True) for _ in CHANNEL_ORDER]
        self.show_letters = tk.BooleanVar(value=True)
        self.show_qnum = tk.BooleanVar(value=False)
        self.show_qcurve = tk.BooleanVar(value=True)
        self.theme = tk.StringVar(value="Classic")

        self._build_menu()
        self._build_layout()
        if self.folders:
            self.refresh_file_list()

    # ------------------------------------------------------------------ UI
    def _build_menu(self):
        menubar = tk.Menu(self)
        file_m = tk.Menu(menubar, tearoff=0)
        file_m.add_command(label="Add data folder…", command=self.add_folder)
        file_m.add_command(label="Clear folders", command=self.clear_folders)
        file_m.add_separator()
        file_m.add_command(label="Export sequence (FASTA)…", command=self.export_fasta)
        file_m.add_command(label="Export peak table (CSV)…", command=self.export_peaks)
        file_m.add_command(label="Save settings JSON…", command=self.save_settings)
        file_m.add_command(label="Load settings JSON…", command=self.load_settings)
        file_m.add_separator()
        file_m.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_m)

        view_m = tk.Menu(menubar, tearoff=0)
        for mode, label in [
            ("raw", "Raw traces"),
            ("processed", "Processed (ACGT)"),
            ("called", "Base-called (with peaks)"),
        ]:
            view_m.add_radiobutton(
                label=label, variable=self.view_mode, value=mode, command=self.redraw
            )
        view_m.add_separator()
        view_m.add_checkbutton(
            label="Show base letters on peaks", variable=self.show_letters,
            command=self.redraw)
        view_m.add_checkbutton(
            label="Show quality numbers (zoomed)", variable=self.show_qnum,
            command=self.redraw)
        view_m.add_checkbutton(
            label="Show quality curve (orange)", variable=self.show_qcurve,
            command=self.redraw)
        view_m.add_separator()

        chan_m = tk.Menu(view_m, tearoff=0)
        for i, base in enumerate(CHANNEL_ORDER):
            chan_m.add_checkbutton(
                label=f"Channel {base}", variable=self.chan_show[i],
                command=self.redraw)
        view_m.add_cascade(label="Channels", menu=chan_m)

        theme_m = tk.Menu(view_m, tearoff=0)
        for name in TRACE_THEMES:
            theme_m.add_radiobutton(
                label=name, variable=self.theme, value=name, command=self.redraw)
        view_m.add_cascade(label="Trace colors", menu=theme_m)
        menubar.add_cascade(label="View", menu=view_m)

        analysis_m = tk.Menu(menubar, tearoff=0)
        analysis_m.add_command(label="Basecall selected", command=self.basecall_selected)
        analysis_m.add_command(label="Basecall all in list", command=self.basecall_all)
        menubar.add_cascade(label="Analysis", menu=analysis_m)

        help_m = tk.Menu(menubar, tearoff=0)
        help_m.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_m)
        self.config(menu=menubar)

    def _build_layout(self):
        # Status bar
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(
            side=tk.BOTTOM, fill=tk.X
        )

        body = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        body.pack(fill=tk.BOTH, expand=True)

        # ----- Left: folders + files -----
        left = ttk.Frame(body, width=260)
        body.add(left, weight=1)

        ttk.Label(left, text="Data folders", font=("", 10, "bold")).pack(anchor=tk.W, padx=4, pady=(4, 0))
        self.folder_list = tk.Listbox(left, height=4, exportselection=False)
        self.folder_list.pack(fill=tk.X, padx=4, pady=2)
        fb = ttk.Frame(left)
        fb.pack(fill=tk.X, padx=4)
        ttk.Button(fb, text="Add folder…", command=self.add_folder).pack(side=tk.LEFT)
        ttk.Button(fb, text="Remove", command=self.remove_folder).pack(side=tk.LEFT, padx=4)

        ttk.Label(left, text="Wells (.rsd)", font=("", 10, "bold")).pack(anchor=tk.W, padx=4, pady=(8, 0))
        self.file_list = tk.Listbox(left, selectmode=tk.EXTENDED, exportselection=False)
        self.file_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
        self.file_list.bind("<<ListboxSelect>>", self.on_file_select)

        ttk.Label(left, text="Graphs to show").pack(anchor=tk.W, padx=4)
        ttk.Spinbox(
            left, from_=1, to=8, textvariable=self.n_graphs, width=5, command=self.redraw
        ).pack(anchor=tk.W, padx=4)

        # ----- Center: plots -----
        center = ttk.Frame(body)
        body.add(center, weight=5)

        chan_bar = ttk.Frame(center)
        chan_bar.pack(fill=tk.X, padx=4, pady=(4, 0))
        ttk.Label(chan_bar, text="Channels:").pack(side=tk.LEFT)
        for i, base in enumerate(CHANNEL_ORDER):
            cb = tk.Checkbutton(
                chan_bar, text=f"  {base}  ", variable=self.chan_show[i],
                command=self.redraw,
                fg=CHANNEL_COLORS[base], activeforeground=CHANNEL_COLORS[base],
                selectcolor="white")
            cb.pack(side=tk.LEFT, padx=2)

        self.fig = Figure(figsize=(9, 7), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=center)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, center)
        toolbar.update()

        # Sequence readout
        ttk.Label(center, text="Called sequence").pack(anchor=tk.W, padx=4)
        self.seq_text = scrolledtext.ScrolledText(center, height=4, wrap=tk.CHAR, font=("Courier", 9))
        self.seq_text.pack(fill=tk.X, padx=4, pady=2)

        # ----- Right: knobs -----
        right = ttk.Frame(body, width=300)
        body.add(right, weight=1)
        self._build_knobs(right)

    def _build_knobs(self, parent: ttk.Frame):
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

        # Basecaller
        f = section("Basecaller version")
        for key, desc in BASECALLER_VERSIONS.items():
            ttk.Radiobutton(
                f, text=f"{key}", variable=self.basecaller, value=key
            ).pack(anchor=tk.W)
            ttk.Label(f, text=f"  {desc}", foreground="#555").pack(anchor=tk.W)

        # Dye order
        f = section("Dye / channel")
        self.base_order_var = tk.StringVar(value=self.settings.base_order)
        ttk.Label(f, text="Base order (instrument)").pack(anchor=tk.W)
        ttk.Combobox(
            f, textvariable=self.base_order_var, values=["TGCA", "ACGT", "GATC", "CTAG"], width=12
        ).pack(anchor=tk.W)

        # Baseline
        f = section("Baseline")
        self.bl_enable = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Enable baseline", variable=self.bl_enable).pack(anchor=tk.W)
        self.bl_win = tk.IntVar(value=self.settings.baseline_window)
        ttk.Label(f, text="Window").pack(anchor=tk.W)
        ttk.Scale(f, from_=51, to=401, variable=self.bl_win, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Spectral / mobility
        f = section("Spectral & mobility")
        self.spec_en = tk.BooleanVar(value=True)
        self.spec_adapt = tk.BooleanVar(value=True)
        self.mob_en = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text="Spectral separation", variable=self.spec_en).pack(anchor=tk.W)
        ttk.Checkbutton(f, text="Position-adaptive matrix", variable=self.spec_adapt).pack(anchor=tk.W)
        ttk.Checkbutton(f, text="Mobility correction", variable=self.mob_en).pack(anchor=tk.W)

        # Band filter
        f = section("Band filter (deconv)")
        self.gauss_en = tk.BooleanVar(value=True)
        self.mp_wiener = tk.BooleanVar(value=False)
        self.gauss_seg = tk.IntVar(value=384)
        self.gauss_reg = tk.DoubleVar(value=0.05)
        ttk.Checkbutton(f, text="Gaussian reconstruction", variable=self.gauss_en).pack(anchor=tk.W)
        ttk.Checkbutton(f, text="Multi-pass Wiener (2048/1900)", variable=self.mp_wiener).pack(anchor=tk.W)
        ttk.Label(f, text="Segment size").pack(anchor=tk.W)
        ttk.Scale(f, from_=128, to=1024, variable=self.gauss_seg, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(f, text="Noise reg").pack(anchor=tk.W)
        ttk.Scale(f, from_=0.01, to=0.2, variable=self.gauss_reg, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Spacing tracker
        f = section("Spacing tracker")
        self.bonus = tk.DoubleVar(value=0.7)
        self.pullback = tk.DoubleVar(value=0.008)
        self.ema = tk.DoubleVar(value=0.08)
        self.wlo = tk.DoubleVar(value=0.70)
        self.whi = tk.DoubleVar(value=1.30)
        ttk.Label(f, text="Channel peak bonus").pack(anchor=tk.W)
        ttk.Scale(f, from_=0.0, to=1.5, variable=self.bonus, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(f, text="Pullback weight").pack(anchor=tk.W)
        ttk.Scale(f, from_=0.0, to=0.03, variable=self.pullback, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(f, text="EMA alpha").pack(anchor=tk.W)
        ttk.Scale(f, from_=0.02, to=0.25, variable=self.ema, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Label(f, text="Window frac lo / hi").pack(anchor=tk.W)
        ttk.Scale(f, from_=0.5, to=0.95, variable=self.wlo, orient=tk.HORIZONTAL).pack(fill=tk.X)
        ttk.Scale(f, from_=1.05, to=1.6, variable=self.whi, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # Signal region
        f = section("Scan region (display)")
        self.scan_start = tk.IntVar(value=0)
        self.scan_end = tk.IntVar(value=0)
        ttk.Label(f, text="Start (0=auto)").pack(anchor=tk.W)
        ttk.Entry(f, textvariable=self.scan_start, width=10).pack(anchor=tk.W)
        ttk.Label(f, text="End (0=full)").pack(anchor=tk.W)
        ttk.Entry(f, textvariable=self.scan_end, width=10).pack(anchor=tk.W)

        # Apply
        bf = ttk.Frame(inner)
        bf.pack(fill=tk.X, padx=4, pady=8)
        ttk.Button(bf, text="Apply knobs + redraw", command=self.apply_knobs_redraw).pack(fill=tk.X, pady=2)
        ttk.Button(bf, text="Basecall with knobs", command=self.basecall_selected).pack(fill=tk.X, pady=2)

    # ------------------------------------------------------------------ data
    def add_folder(self):
        d = filedialog.askdirectory(title="Select folder containing .rsd files")
        if not d:
            return
        p = Path(d)
        if p not in self.folders:
            self.folders.append(p)
            self.folder_list.insert(tk.END, str(p))
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

    def refresh_file_list(self):
        self.files = discover_rsd(self.folders)
        self.file_list.delete(0, tk.END)
        for f in self.files:
            self.file_list.insert(tk.END, f"{f.parent.name}/{f.name}")
        self.status_var.set(f"{len(self.files)} .rsd files in {len(self.folders)} folder(s)")

    def on_file_select(self, _evt=None):
        idxs = self.file_list.curselection()
        self.selected = [self.files[i] for i in idxs if i < len(self.files)]
        self.redraw()

    def _settings_from_ui(self) -> AnalysisSettings:
        s = AnalysisSettings(
            basecaller=self.basecaller.get(),
            base_order=self.base_order_var.get(),
            baseline_window=int(self.bl_win.get()),
            spectral_enable=self.spec_en.get(),
            position_adaptive_spectral=self.spec_adapt.get(),
            mobility_enable=self.mob_en.get(),
            use_gaussian_reconstruction=self.gauss_en.get(),
            use_multipass_wiener=self.mp_wiener.get(),
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

    def _ensure_doc(self, path: Path) -> TraceDocument:
        key = str(path.resolve())
        if key not in self.docs:
            self.status_var.set(f"Loading {path.name}…")
            self.update_idletasks()
            self.docs[key] = load_rsd(path, base_order=self.base_order_var.get())
        return self.docs[key]

    # ------------------------------------------------------------------ analysis
    def basecall_selected(self):
        if not self.selected:
            messagebox.showinfo("Basecall", "Select one or more wells in the list.")
            return
        self.settings = self._settings_from_ui()
        for path in self.selected:
            try:
                doc = self._ensure_doc(path)
                self.status_var.set(f"Basecalling {path.name} ({self.settings.basecaller})…")
                self.update_idletasks()
                run_basecall(doc, self.settings)
            except Exception as e:
                messagebox.showerror("Basecall error", f"{path.name}:\n{e}")
                return
        self.status_var.set(f"Basecalled {len(self.selected)} well(s)")
        self.redraw()
        self._show_sequence()

    def basecall_all(self):
        if not self.files:
            return
        self.selected = list(self.files)
        self.basecall_selected()

    def _show_sequence(self):
        self.seq_text.delete("1.0", tk.END)
        for path in self.selected[: self.n_graphs.get()]:
            key = str(path.resolve())
            doc = self.docs.get(key)
            if not doc or not doc.sequence:
                continue
            self.seq_text.insert(
                tk.END,
                f">{doc.well} {self._well_stats(doc)}\n{doc.sequence}\n\n")

    # ------------------------------------------------------------------ plot
    def _theme_colors(self) -> dict:
        return dict(TRACE_THEMES.get(self.theme.get(), "Classic"))

    def _well_stats(self, doc) -> str:
        """One-line stats for a basecalled well (length, Q, GC, spacing)."""
        import textwrap
        seq, q = doc.sequence, doc.qualities
        n = len(seq)
        if n == 0:
            return "not basecalled"
        qa = np.asarray(q[:n], dtype=float) if q else np.array([], dtype=float)
        qmean = float(qa.mean()) if qa.size else 0.0
        qmin = float(qa.min()) if qa.size else 0.0
        nN = seq.count("N")
        gc = 100.0 * (seq.count("G") + seq.count("C")) / n if n else 0.0
        pos = np.asarray(doc.peak_positions[:n], dtype=float)
        sp = float(np.median(np.diff(pos))) if pos.size > 1 else 0.0
        return (f"len={n} Qmean={qmean:.1f} Qmin={qmin:.1f} "
                f"GC={gc:.1f}% N={nN} sp={sp:.2f} scans")

    def redraw(self):
        self.fig.clear()
        colors = self._theme_colors()
        n = max(1, min(8, self.n_graphs.get()))
        paths = self.selected[:n] if self.selected else []
        if not paths:
            ax = self.fig.add_subplot(111)
            ax.text(0.5, 0.5, "Select wells from the list", ha="center", va="center")
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
            s0 = max(0, settings.signal_start)
            s1 = settings.signal_end if settings.signal_end > 0 else tr.shape[0]
            s1 = min(tr.shape[0], s1)
            x = np.arange(s0, s1)
            plotted = False
            for ci, base in enumerate(CHANNEL_ORDER):
                if not self.chan_show[ci].get():
                    continue
                ax.plot(x, tr[s0:s1, ci], color=colors[base], lw=0.7, label=base)
                plotted = True
            if not plotted:
                ax.text(0.5, 0.5, "(all channels hidden)",
                        ha="center", va="center", transform=ax.transAxes, color="#888")
            ax.set_ylabel(doc.well, fontsize=8)
            ax.tick_params(labelsize=7)
            if i == 0 and plotted:
                ax.legend(loc="upper right", fontsize=7, ncol=4)
            if i == len(paths) - 1:
                ax.set_xlabel("Scan")

            if doc.sequence and settings.view_mode == "called" and doc.peak_positions:
                # base letters + quality numbers above peaks
                seq = doc.sequence
                q = doc.qualities or []
                pos = np.asarray(doc.peak_positions, dtype=float)
                med_sp = float(np.median(np.diff(pos))) if pos.size > 1 else 0.0
                ytop = float(np.nanmax(tr[s0:s1])) if tr[s0:s1].size else 1.0
                tight = (s1 - s0) > 1400
                draw_let = (not tight) or med_sp >= 10
                draw_q = self.show_qnum.get() and med_sp >= 16
                for pi, base_ in enumerate(seq):
                    if pi >= len(pos) or base_ not in colors:
                        continue
                    p = int(pos[pi])
                    if not (s0 <= p < s1):
                        continue
                    ax.axvline(p, color=colors[base_], alpha=0.20, lw=0.5, zorder=1)
                    if draw_let:
                        ax.text(p, ytop + 0.01 * ytop, base_, color=colors[base_],
                                ha="center", va="bottom", fontsize=7,
                                zorder=5, clip_on=True)
                    if draw_q and pi < len(q):
                        ax.text(p, -0.02 * ytop, f"{q[pi]:.2f}", color=QUALITY_COLOR,
                                ha="center", va="top", fontsize=6,
                                zorder=5, clip_on=True)
                if not draw_let:
                    ax.text(0.01, 1.02, "bases too dense — zoom to show letters",
                            transform=ax.transAxes, fontsize=6, color="#888")

            if (self.show_qcurve.get() and doc.sequence and doc.qualities
                    and settings.view_mode != "raw"):
                # quality curve on a twin axis (band heights at peak scans)
                pos = np.asarray(doc.peak_positions, dtype=float)
                q = np.asarray(doc.qualities[: len(pos)], dtype=float)
                m = (pos >= s0) & (pos < s1)
                if m.any():
                    ax2 = ax.twinx()
                    ax2.plot(pos[m], q[m], color=QUALITY_COLOR, lw=1.2, alpha=0.85)
                    ax2.set_ylabel("quality", color=QUALITY_COLOR, fontsize=7)
                    ax2.tick_params(axis="y", labelcolor=QUALITY_COLOR, labelsize=7)
        self.fig.tight_layout()
        self.canvas.draw_idle()
        self._show_sequence()

    # ------------------------------------------------------------------ I/O
    def export_fasta(self):
        if not self.selected:
            messagebox.showinfo("Export", "Select basecalled wells first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".fasta", filetypes=[("FASTA", "*.fasta")])
        if not path:
            return
        lines = []
        for p in self.selected:
            doc = self.docs.get(str(p.resolve()))
            if doc and doc.sequence:
                lines.append(f">{doc.well} len={len(doc.sequence)}\n{doc.sequence}")
        Path(path).write_text("\n".join(lines) + "\n")
        self.status_var.set(f"Wrote {path}")

    def export_peaks(self):
        """Export basecalled peaks to CSV: well, base, scan position, quality."""
        import csv
        if not self.selected:
            messagebox.showinfo("Export", "Select basecalled wells first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["well", "index", "base", "scan", "quality"])
            for p in self.selected:
                doc = self.docs.get(str(p.resolve()))
                if not doc or not doc.sequence:
                    continue
                for i, (b, pos, q) in enumerate(zip(
                        doc.sequence, doc.peak_positions, doc.qualities or [])):
                    w.writerow([doc.well, i, b, int(pos), float(q)])
        self.status_var.set(f"Wrote {path}")

    def save_settings(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        s = self._settings_from_ui()
        Path(path).write_text(json.dumps(s.__dict__, indent=2))

    def load_settings(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        data = json.loads(Path(path).read_text())
        for k, v in data.items():
            if hasattr(self.settings, k):
                setattr(self.settings, k, v)
        # push to UI (subset)
        self.basecaller.set(data.get("basecaller", "pos_bonus07"))
        self.base_order_var.set(data.get("base_order", "TGCA"))
        self.bonus.set(data.get("channel_peak_bonus", 0.7))
        self.pullback.set(data.get("pullback_weight", 0.008))
        self.status_var.set(f"Loaded settings from {path}")

    def show_about(self):
        messagebox.showinfo(
            "About",
            "MegaBACE Sequence Analyzer (Python)\n\n"
            "Views: raw / processed / base-called\n"
            "Basecallers: pos_bonus07, pos_profile, hz_soften, raw_peaks\n"
            "Multi-folder .rsd load, multi-graph, analysis knobs\n\n"
            "Uses BEST_BASECALLER_RELEASE spacing tracker.",
        )


def main():
    ap = argparse.ArgumentParser(description="MegaBACE Sequence Analyzer")
    ap.add_argument("--folder", action="append", type=Path, help="Data folder (repeatable)")
    args = ap.parse_args()
    app = SequenceAnalyzerApp(initial_folders=args.folder)
    app.mainloop()


if __name__ == "__main__":
    main()
