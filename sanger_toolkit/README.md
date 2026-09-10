# Sanger Toolkit — Modular Basecalling GUI

## Quick Start
```bash
cd sanger_toolkit
python3 sequencing_gui_V15.py
```

## Features

### Basecalling
- **De-novo CNN ensemble**: 91.53% accuracy (vs Cimarron 90.72%)
- **Polished mode**: 100% (with M13 reference)
- **CNN confidence dropout** (`Analyze → Run ML Basecalling`, "CNN drop" in the
  Call-region group): drops low-confidence CNN calls (pmax < threshold, default
  0.50) as `N`, removing spurious insertions that otherwise fragment the BLAST
  hit and inflate its aligned-subset `pident`.
- 5 basecalling methods: Greedy, Per-channel, Cimarron, Multiview, LifeTrace/Hybrid
- IUPAC ambiguity codes for heterozygous positions
- Fill-in detector for swallowed bases

### GUI Features
- 4-panel chromatogram view (raw, corrected, separated, ESD) with shared x-axis
- **Per-base Q-score color bar** (5th subplot) — red < Q20, yellow Q20-30, green > Q30
- **Reverse complement view** toggle for inspecting reverse reads
- **ABI/SCF import** — analyze data from any Sanger sequencer (not just MegaBACE)
- Interactive parameter tuning with live update (50ms debounce)
- Drag-to-adjust mobility shift lines
- Reference comparison dialog (local alignment, both strands)
- Settings save/load (JSON + QSettings persistence)
- Parameter optimizer (differential evolution)
- 96-well batch processing with plate grid view

### Keyboard Shortcuts
| Key | Action |
|---|---|
| `R` | Reset view |
| `L` | Load well |
| `Space` | Next well |
| `Backspace` | Previous well |
| `Left/Right` | Scroll 100 scans |
| `Up/Down` | Scroll 20 scans |
| `Ctrl+F` | Fit to window |
| `Ctrl+S` | Save FASTA |
| `Ctrl+O` | Load settings |
| `Ctrl+C` | Copy FASTA |
| `Ctrl+E` | Export data |
| `G` | Toggle rev-comp view |
| `Q` | Toggle Q-score bar |

## File Map

### Core modules (no Qt dependency — usable headlessly)
| File | Lines | Purpose |
|---|---|---|
| `constants.py` | 193 | Matrices, base codes, method lists, parameter ranges, tooltips |
| `dsp.py` | 456 | Signal processing: 13 baselines, 9 smoothers, crosstalk separation, full pipeline |
| `basecall.py` | 612 | Peak detection + 5 basecallers (Greedy, Per-channel, Cimarron, Multiview, LifeTrace/Hybrid) |
| `align.py` | 237 | Needleman-Wunsch, Smith-Waterman, semi-global alignment, reference accuracy |
| `quality.py` | 121 | Phred Q-score estimation from confidence, quality statistics |
| `trim.py` | 102 | Sliding-window and trailing quality-based auto-trimming |
| `export.py` | 79 | FASTA and FASTQ export with quality scores |
| `abi_reader.py` | ~300 | ABI (.ab1) and SCF file format reader for Sanger chromatograms |

### CNN confidence (optional — needs TensorFlow)
| File | Lines | Purpose |
|---|---|---|
| `cnn_confidence.py` | 168 | Loads trained CNN ensemble, per-base softmax → Phred Q-scores |

### Batch processing (no Qt dependency)
| File | Lines | Purpose |
|---|---|---|
| `batch.py` | 480 | Headless plate processor: threaded 96-well pipeline, FASTQ/FASTA export, summary stats |

### Benchmark / tuning (no Qt dependency)
| File | Purpose |
|---|---|
| `blast_bench.py` | **BLAST read-level benchmark** vs the Cimarron 3.12 DLL goal. BLASTs (a) the DLL ESD call and (b) our caller through the identical blastn/megablast best-HSP pipeline against `refs/m13_M77815.1.fa`, reporting bases / matched bp / full-read identity / pident. Flags: `--wells`, `--task`, `--drop PMIN`, `--bgn-end`, `--no-cnn`, `--refine-v2`. |
| `plate_blast.py` | Full-plate version of `blast_bench.py`. Loads the CNN ensemble once, runs all/selected wells in parallel, prints per-well table + plate-wide means (matched bp + full-read identity), writes a CSV (`--out`). Flags: `--wells`, `--drop` (default 0.50), `--bgn-end`, `--threads`. |
| `coverage_tune.py` | Engine-knob sweep (bgn-end, greedy_min_frac, cluster prominence, CNN-drop) used to diagnose the coverage/recall gap. |

## BLAST benchmark
Measure the called read against M13 exactly like the commercial DLL.

**Metric note.** BLAST `pident` (over the aligned subset only) and single-HSP
query `coverage` do **not** fairly compare reads of different lengths — they
ignore the read's unaligned tail. Use the **full-read metric** these tools
report: `matched_bp` (actual base pairs matching M13) and `full_identity =
matched / detected` ("1 detected base = a slot to fill; 100% only if it
matches M13").

```bash
# Compare DLL vs our default call (shows both raw + full-read metrics)
python3 blast_bench.py --wells A01 --drop 0.5
# Across several wells
python3 blast_bench.py --wells A01 B01 C01 --drop 0.5
```
Requires NCBI blast+ (`blastn`, `makeblastdb`) and TensorFlow (for the CNN path;
add `--no-cnn` for the pure independent caller). The CNN drop below `pmax 0.50`
removes spurious insertions, improving the aligned-subset `pident` of the
remaining bases. See `PROJECT_HISTORY.md` Phase 9.

### Full plate
```bash
python3 plate_blast.py --drop 0.5 --out plate_blast_fullread.csv   # all 96 wells
```
Plate-wide (96 wells, drop 0.5) — **full-read metric**:

| caller | bases detected | matched bp | full identity |
|---|---|---|---|
| **DLL (goal)** | 867.4 | **753.3** | 86.86% |
| **ours de-novo** | 730.8 | 641.0 | **87.71%** |

Honest read: our remaining bases are slightly more accurate individually, but the
DLL **detects ~137 more bases/well and matches ~112 more base pairs/well**. The
gap to the user goal (841 bases / ~95% matched on A01) is **recall** — detecting
and correctly calling more bases — not precision. CNN-drop/edge-trim/gap-fill
only trade precision; closing the gap needs better base detection (more seed
peaks, begin/end spanning the DLL's full M13 window, or a CTC context model).



### GUI
| File | Lines | Purpose |
|---|---|---|
| `sequencing_gui_V15.py` | ~3200 | PyQt5 GUI — imports from core modules, includes CNN Q-score display, Q-score bar, rev-comp toggle |
| `plate_view.py` | 185 | Interactive 96-well plate grid widget (color-coded by Q-score/status) |
| `batch_dialog.py` | 238 | Batch processing dialog with plate grid, progress, export buttons |

### Runtime dependencies (copied from parent project)
| File | Purpose |
|---|---|
| `multiview_peakdetect.py` | Multiview per-channel detection optimizer |
| `extract_training_data.py` | RSD/ESD file parsers |
| `peak_detector.py` | Peak detection helper (used by extract_training_data) |
| `cimarrontv.py` | Cimarron 3.12 DLL engine (Python port) |
| `simple_align.py` | M13 reference sequence + alignment helpers |
| `refs/m13_M77815.1.fa` | M13 bacteriophage reference FASTA |

## Architecture
```
sequencing_gui_V15.py  (GUI — PyQt5 widgets, plot, event handlers)
    ├── constants.py        (shared data)
    ├── dsp.py              (signal processing)
    ├── basecall.py         (basecalling algorithms)
    ├── align.py            (sequence alignment)
    ├── quality.py          (Phred Q-scores)
    ├── trim.py             (quality trimming)
    ├── export.py           (FASTA/FASTQ export)
    ├── abi_reader.py       (ABI/SCF file import)
    ├── cnn_confidence.py   (CNN ensemble → pmax → Q-scores)
    ├── batch_dialog.py     (batch processing dialog)
    │   └── plate_view.py   (96-well grid widget)
    └── batch.py            (headless plate processor)
```

## Headless usage (no GUI)
```python
from batch import BatchProcessor, METHOD_CIMARRON_CNN

bp = BatchProcessor('/path/to/MB1000_M13_DT', method=METHOD_CIMARRON_CNN)
bp.run(max_workers=4, progress_callback=lambda w, d, t: print(f'{w}: {d}/{t}'))
bp.export_fastq('output/', prefix='plate')
bp.export_fasta('output/', prefix='plate')
print(bp.summary_stats())
```

Or via CLI:
```bash
python3 batch.py /path/to/MB1000_M13_DT --out output/ --threads 4 --method 2
```

## ABI/SCF Import
```python
from abi_reader import read_chromatogram, abi_to_rsd_traces

chrom = read_chromatogram('sample.ab1')
traces, x, channel_order = abi_to_rsd_traces(chrom)
print(f'{chrom["n_scans"]} scans, {len(chrom["sequence"])} bases')
```

## Q-scores
- **Method 2 (Cimarron+CNN)**: Uses the Cimarron312 engine for peak detection, then
  scores each peak with the trained CNN ensemble. Q = -10*log10(1 - pmax).
- **Methods 0-1 (Greedy/Cluster)**: Uses the independent peak caller with CNN
  scoring at detected positions.
- The CNN gives honest Q-scores (~Q8 mean for 91.5% accuracy). These are
  well-calibrated: Q8 means ~84% accuracy, matching the model's real performance.
- For higher Q-scores, the CNN model needs more training data or calibration.

## Insertion Profiler
```bash
python3 insertion_profiler.py --wells A01 B02 C03 --out profile.csv
python3 insertion_profiler.py --out profile.csv   # all 96 wells
```

Profiles insertion errors vs M13 reference, extracting per-insertion features:
CNN pmax, runner-up probability, peak height, spacing ratio vs local median,
homopolymer context (base, run length), quartile position.

Key finding (25 wells, 825 insertions): homopolymer vs non-homopolymer
insertions are **indistinguishable** — same CNN confidence, same spacing.
These are genuine polymerase stutter, not artifacts. No post-hoc filter can
separate them. Refine threshold sweep confirmed drop_p=0.70 is optimal
(flat curve 0.66–0.78). See `WEEKEND_SUMMARY.md` addendum 3 for details.
