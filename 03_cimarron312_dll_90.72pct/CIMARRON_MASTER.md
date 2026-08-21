# Cimarron 3.12 Reverse Engineering — Master Document

**Last updated**: 2026-08-17  
**Goal**: Build an independent Python basecaller that reproduces Cimarron 3.12 DLL results exactly, without Wine or Windows XP.

---

## 1. Current Results Summary

| Approach | 96-well mean NW | Median | Min | A01 NW | Status |
|---|---|---|---|---|---|
| **DLL (CimBC030012_noPuff.dll)** | 100% (ground truth) | 100% | 100% | 100% | Perfect reference |
| **cimarrontv.py** (Python Cimarron) | 89.98% | 90.26% | 85.01% | 88.24% | Best Python result |
| **cimarrontv.py + hybrid region** | 90.48% | 90.75% | 85.01% | — | +0.50pp improvement |
| **mbsa_rebuild.py** (faithful DLL port) | ~64% | — | — | — | Incomplete: 4x FFT upsampling not decoded |
| **V15 GUI greedy** (V10 preproc) | 88.9% | 89.2% | 84.1% | 91.9% | Visual approximation, NOT Cimarron |
| **V15 GUI greedy** (V8 preproc) | 88.3% | 88.6% | 83.0% | 87.1% | Earlier version |

**The ~10% gap** between cimarrontv.py (89.98%) and DLL (100%) is the core unsolved problem.

---

## 2. DLL Architecture (from reverse engineering)

### Binary Components
| Binary | Role | Exports |
|---|---|---|
| `AutoBaseCall.exe` | GUI (MFC42) | — |
| `CimBC030012_noPuff.dll` | Procedural dispatcher (3.12) | 110 |
| `CimBC030012_beautify.dll` | 3.12a "aligned" variant | 110 |
| `CimBC030012_printify.dll` | 3.12e "even spacing" variant | 110 |
| `csibq030012.dll` | **Core engine** (217 KB) | 450 |
| `core.dll` | Trace I/O + GUI primitives | 284 |
| `MATH.dll` | C math runtime | 225 |
| `GTAL.dll` | Matrix lib (MDdb*) | 100 |
| `basecall.dll` | Older/alternative Cimarron engine | 308KB |
| `csibq153.dll` | Cimarron 1.53 quality scoring | 327KB |
| `MDRegistry.dll` | Windows registry access | 28KB |
| `DataFiles.dll` | COM registration only | 90KB |
| `Abd.dll` | Unknown | 49KB |

### Cimarron 1.53 (csibq153.dll + CimBc010053_*.dll)
- **No Annotate class** (simpler than 3.12)
- **Has `equalizer`, `phredify`, `truvelAdjust`** not in 3.12
- Variants: `CimBc010053_beautify.dll` (Phat/Aligned), `CimBc010053_phredify_noPuff.dll` (Slim Phredify)

### Molecular Dynamics (Sqcr.dll + GTAL.dll + MATH.dll)
- **Interface**: `Sqcr.dll` (221KB, 20 exports)
- **Core**: `GTAL.dll` (100 exports) — `MDWell`, `MDPeak`, `MDTrace` classes
- **Math**: `MATH.dll` (225 exports) — matrices, FFT, Legendre polynomials, curve fitting
- Different approach: peak fitting (Gaussian), FFT-based filtering, spectral separation via `MDWell::specSep`

### Procedural API (30 C-linkage exports)
**Lifecycle**: `CleanUp`, `GetCodeVersion`, `GetBaseCallerCod`  
**Dispatch**: `ExecuteProcedure`, `GetNumOfProcedures`, `GetProcedureAbbreviation`  
**Input**: `SetRawData`, `SetNumSamples`, `SetSignalRange`, `setSigRange`  
**Params**: `SetSpecSepMatrix`, `SetApproxiamatePeakWidth` (note typo), `SetIfAnnotate`, `SetMobilShiftCurve`  
**Reports**: `ReportSequence`, `ReportSignalToNoise`, `ReportSignalRangeForRawData`, `ReportSpecSepDepth`, `ReportSpecSepQual`, `ReportSpecSeparatnMatrixUsed` (typo), `ReportTrueStartStopPoints`, `ReportFWHMSpacing`, `ReportMobShiftUsed`, `ReportNumCurrFix`, `ReportProblem`, `PeekProcessedTrace`

### OOP Core Classes (in csibq030012.dll)
`Wvfm(61)` `BandStat(39)` `BandStatArray(44)` `Annotate(35)` `CSIBQWrap(33)`  
`ObsInpSpec(27)` `RdrOut(20)` `SW(14)` `SSNODE(12)` `QualCtrl(12)` `Mobility(9)`  
`ShftVect(4)` `LMConvert(4)` `AboutBQ(5)`

---

## 3. DLL Algorithm Stages (9 stages)

### Stage 1: Baseline + Smoothing
- **Wvfm::sc_la** / `savitzkyGolay` / `smooth3`
- Savitzky-Golay window=11, polyorder=3 (verified)
- Baseline correction before smoothing

### Stage 2: SSM Crosstalk Correction
- **ObsInpSpec::xtalk** / `ratio`; Wvfm::ssm setter
- 4×4 Spectral Separation Matrix, LU decomposition
- Matrix is loaded at runtime from Basecall.ini/run settings
- Inverts crosstalk: `separated = raw @ M_final.T` (where `M_final = inv(M)` then column-normalized)

### Stage 3: Peak Detection
- **Wvfm::putativePks** → peak detect
- SNR threshold = **3.0** (double 3.0012 in csibq030012 .data)
- Noise fraction = **0.0587** (== 3/51)
- Per-lane peak-width-ratio table: grows 1.12 → 1.92 along lane (band broadening), floor at 1.875

### Stage 4: Band Statistics (14 fields per peak)
```
bbgn, bend     band begin/end scan index
hght           peak height above baseline
lowv           local minimum (valley) under the peak
xbnd           cross-talk boundary residual
buzz           noise under the peak (BandStat `Buzz`)
shap           peak shape / symmetry
widt           FWHM / band width
lgap, sgap     left/right gap to neighbours
snr            signal-to-noise ratio
qual           phred quality
ntnr, insr     noise estimates
awid           average width
```

### Stage 5: Mobility Search
- **Mobility::search** — 70-entry struct array, 0x24-byte stride, size float at offset 0x20
- Lower-bound match (outer loop `i < 0x46 = 70`)
- Tries offsets [-5..+5] per channel, picks best

### Stage 6: SW Self-Alignment
- **SW** class: `sw_`/`swwalk_`/`concensus`; SSNODE start/stop
- Template region identification

### Stage 7: Shift/Indel Realign
- **ShftVect** — per-base indel realignment

### Stage 8: Quality Scoring
- **QualCtrl::StadenQual** / `bspc`
- Weighted: dominance + SNR + amplitude
- Phred quality mapping

### Stage 9: Output
- **RdrOut** → sequence / Edit / Beautify / closesTo / pickcuts
- `Beautify` (aligned variant), `phredify` (Phred scores)

---

## 4. Band Stage (THE MISSING PIECE — 4x FFT Upsampling)

This is the critical unsolved component that accounts for most of the ~10% gap.

### Decoded from csibq030012.dll
The DLL has a **4× FFT upsampling** block that runs BEFORE peak detection. This is the key difference between the DLL and cimarrontv.py.

### Band Table Structure (0x10698)
- Fixed head: 1/151/401/901/1401/1901
- Channel 0: 150/400/900/1400/1900/2400
- Then every 0x2EE (750) scans
- Table records: `[pos, ch0, ch1, ch2, ch3]`

### Band Refinement (0x10270)
1. Build band table from trace
2. Apply per-channel gains (0x108cb): `gain[ch] = 0.25 * sum(p95) / p95[ch]` (95th percentile)
3. Coarse-to-fine B-spline peak-shape search (0x10b2e):
   - Coarse: radius=15, step=2
   - Fine: radius=3, step=1
   - Spline prefix: `out4 = (i+j+k, j+k, k, 0)`
4. Dead-scan carving (0x10ca7/0x10d6d):
   - For each peak, insert dead gaps to separate overlapping peaks
   - Per-channel: shift data right by vec[c], zero vec[c] scans at peak start

### Band Correction (0x10d6d)
- Per-band baseline (min-channel subtraction + cumulative diff)
- Carve vec-scan dead gaps at each record's peak end
- Divisor = maxv / 10.0 (used to find signal decay point)

### Post-Stage (0x4889) — NOT YET DECODED
- Consumes the band table after refinement
- This is the final peak-calling stage in the DLL
- Without it, the faithful port only achieves ~64% NW

### What's Decoded vs Not
| Component | Status | Offset |
|---|---|---|
| Band table build | Decoded | 0x10698 |
| B-spline peak search | Decoded | 0x10b2e |
| Spline prefix-sum kernel | Decoded | 0x10a4e |
| Dead-scan carving | Decoded | 0x10ca7/0x10d6d |
| Per-channel gains | Decoded | 0x108cb |
| Band correction | Decoded | 0x10d6d |
| 4x FFT upsampling | **NOT decoded** | — |
| Post-stage peak calling | **NOT decoded** | 0x4889 |
| Record-list peak detector | **NOT decoded** | 0x19ef2 |

---

## 5. Verified Constants

| Constant | Value | Source |
|---|---|---|
| SNR call threshold | **3.0** | double 3.0012 in csibq030012 .data |
| Noise fraction | **0.0587** (== 3/51) | csibq .rdata/.data, paired with 0.0592 |
| Savitzky-Golay window | **11** | csibq .rdata |
| Savitzky-Golay polyorder | **3** | csibq .rdata |
| Width ratio table | **1.12 → 1.92** (20 entries, floor 1.875) | csibq .rdata |
| Mobility table | **70 entries**, 0x24-byte stride, size at +0x20 | csibq disassembly |
| Build dates | basecall.dll (3.0) 1998-09-08; CimBC030012 (3.12) 2001-10-18 | PE headers |

---

## 6. MegaBACE Data Format

### RSD Format (Raw Signal Data)
- Binary: 5 × uint32 per record (20 bytes)
- Fields: `[Current, Channel1, Channel2, Channel3, Channel4]`
- Channel order: 0=FAM(T), 1=JOE(G), 2=TAMRA(C), 3=CY5(A)
- Boundary: records >200000 in any channel = metadata (not data)
- A01.rsd: 9647 records, 194180 bytes, MD5 `7286b225211ab284b39f2e829788f73e`

### ESD Format (Electronic Signal Data)
- Binary with tagged records
- SEQUENCE tag: type 0x06 (2-byte length) or 0x05 (1-byte length)
- Contains: sequence, base_positions, quality_scores, etc.
- DLL output goes to nested path: `out_Cp312_MD1/out_Cp312_MD1/<name>.esd`

### Ground Truth Reference Files
- `MB1000_M13_DT/{WELL}.rsd` — raw traces (96 wells)
- `MB1000_M13_DT/MB1000_M13_DT_Cp312_MD1/{WELL}.esd` — DLL ESD output (ground truth)
- A01.rsd = Raw_data.rsd (identical files, MD5 `7286b225211ab284b39f2e829788f73e`)
- MB4000_DEMO_DATA A01.rsd is a DIFFERENT file (MD5 `c42bfb65d537edddf0fb1a78e6d8e395`, 9965 records)

---

## 7. Crosstalk / Bleed Matrices

### MegaBACE ET-dye Matrix (from xtalk.tdb)
```
[[1.0,    0.1644, 0.3058, 0.2374],
 [0.0765, 1.0,    0.001,  0.0061],
 [0.0801, 0.0204, 1.0,    1.0924],
 [0.0017, 0.0203, 0.1894, 1.0]]
```
- Channel order: T, G, C, A
- Diagonal = 1.0 (no self-attenuation)
- Some values >1 (e.g., 1.0924 at C→A) may be normalization artifacts

### V10 Matrix (user-tuned, best Python result)
```
[[1.0,  1.0,   0.26,  0.46],
 [0.07, 1.0,   0.075, 0.006],
 [0.38, 0.33,  1.0,   1.52],
 [0.27, 0.26,  0.189, 1.0]]
```

### V8 Matrix (earlier version)
```
[[0.8,  0.55,  0.04,  0   ],
 [0,    0.8,   0,     0   ],
 [0,    0.5,   0.75,  1   ],
 [0.18, 0.06,  0.04,  0.585]]
```

### MegaBACE vs V8 Matrix Comparison
| Entry | MegaBACE | V8 | Diff |
|---|---|---|---|
| [0,1] T→G | 0.1644 | 1.0 | −0.8356 |
| [2,0] C→T | 0.0801 | 0.3500 | −0.2699 |
| [2,1] C→G | 0.0204 | 0.3000 | −0.2796 |
| [2,3] C→A | 1.0924 | 1.5000 | −0.4076 |
| [3,0] A→T | 0.0017 | 0.3000 | −0.2983 |
| [3,1] A→G | 0.0203 | 0.2000 | −0.1797 |
| [0,2] T→C | 0.3058 ≈ 0.306 | ≈0 | |
| [0,3] T→A | 0.2374 ≈ 0.237 | ≈0 | |
| [1,0] G→T | 0.0765 ≈ 0.07 | ≈0 | |
| [1,3] G→A | 0.0061 ≈ 0.006 | ≈0 | |
| [3,2] A→C | 0.1894 ≈ 0.189 | ≈0 | |

---

## 8. Python Pipeline Settings

### V10 Settings (Best — 88.9% mean plate via GUI)
```json
{
  "basecall_method": 0,
  "baseline_method": "AsyLS",
  "baseline_window": 50010,
  "baseline_window2": 1,
  "esd_offset": 2008,
  "esd_variant": "Cp312",
  "fill_gap": 3,
  "fill_in": true,
  "fill_margin": 1.0,
  "matrix": [[1.0, 1.0, 0.26, 0.46], [0.07, 1.0, 0.075, 0.006], [0.38, 0.33, 1.0, 1.52], [0.27, 0.26, 0.189, 1.0]],
  "matrix_apply_point": "corrected",
  "min_distance": 5,
  "min_signal_frac": 1.0,
  "mobility_shifts": [5, 11, 10, 10],
  "norm_window": 300,
  "prominence_frac": 0.135,
  "smooth_method": "Butterworth",
  "smooth_order": 9,
  "smooth_window": 5,
  "tolerance": 3
}
```

### V8 Settings (Previous best — 88.3% mean plate)
```
AsyLS 50000/1, Butterworth 7/6, matrix apply corrected, esd_offset 1998, mobility [5,10,10,10]
```

### Key Parameters
- `CHEM_MAP`/`BASE_LETTERS` = {0:T, 1:G, 2:C, 3:A}
- GUI greedy defaults: distance_spin=5 (=window), prominence_spin=200 (=min_frac 0.20), norm_window=800
- `prominence_frac = prominence_spin/1000`
- ESD peak spacing percentiles: p25=7, p50=9, p75=10 scans
- NW identity uses match=1, mismatch=-1, gap=-2 (see `pc_nw_identity`)

### V10 Preprocessing Comparison
| config | mean | median | min |
|---|---|---|---|
| V8 preproc, w5 mf.20 n800 | 88.3% | 88.6% | 83.0% |
| V10 preproc, w5 p0.135 n300 (V10-stored) | 88.9% | 89.1% | 82.0% |
| **V10 preproc, w5 p0.20 n800 mob[5,11,10,10]** | **88.9%** | **89.2%** | **84.1%** |

---

## 9. What Was Tried and Failed

### Failed Approaches to Close the ~10% Gap
1. **Same-letter + shallow-valley merge**: 89.6% → 86.2% (removes real homopolymer pairs)
2. **Dominant-channel FWHM-adaptive excise** (cap 10/12/16): 89.6% → 82–84%
3. **Plateau-fraction excise** (cuts at 0.90/0.95/0.97 of apex): → 88.3–88.7%
4. **Rolling-MEAN / rolling-MEDIAN normalization**: → 73–77% / 15% (max-filter essential)
5. **Dominant-channel apex refinement** (±2/3/4 scans): no gain
6. **Fill-in after greedy**: no gain (deletions sit inside excise windows)
7. **Adaptive local threshold** (rolling 200/400/800): no gain
8. **Running greedy on ESD's own mobility-corrected traces**: worse (85.5 vs 88.6)
9. **Greedy window sweep**: win=4→81.9%, win=5→88.6%, win=6→86.8% (5 is optimal)

### Root Cause: Position Error, Not Amplitude Error
- Letters are ~99% correct when position is right
- Position error is SCATTER, not bias (no systematic mobility drift)
- Late-read peak decay makes envelope maxima poorly defined
- Rolling-max normalization flattens both single broad peaks AND genuine adjacent pairs → indistinguishable

### The 4x FFT Upsampling Block is the Key
- `mbsa_rebuild.py` (faithful DLL port) only gets 64% NW without it
- The upsampling block (0x10270/0x10d6d/0x4889) is NOT yet fully decoded
- This block compensates for raw-trace noise that the Python pipeline cannot handle
- **This is the single most important piece to decode for closing the gap**

---

## 10. Region/Tail Detector Improvement

### Hybrid Region (implemented, verified)
- New `bgn_end_method="hybrid"` in Cimarron312: legacy onset start + perbase end trimmed by `hybrid_tail_trim` (default 120)
- Per-well analysis: perbase end NEVER cuts real bases (mean +186 scans past last ref peak, max +262)
- Official 96-well eval: **hybrid 90.48% mean / 90.75 median / max 93.59** vs baseline legacy 89.98% mean → +0.50pp
- Reproduction: `python3 eval_ground_truth.py --bgnend hybrid`

### Second-Phase Peak Detection Candidates
| candidate | 96-well mean NW | verdict |
|---|---|---|
| 3.12 legacy (baseline) | 89.74% | reference |
| 3.12 hybrid region | **90.27%** | +0.53pp, keep |
| 3.12a SW realign + quality-gated trim | 79.01% | -10.7pp, reject |
| 3.12a hybrid | 72.81% | -16.9pp, reject |

### GUI V15 Hybrid Region
- Added "Hybrid tail (perbase end)" checkbox in Region group (default ON, persisted as `region_hybrid`)
- Full 96-well: hybrid **88.89% mean / 89.35 med** vs legacy 88.67% / 89.11 (+0.22pp mean)
- A01: 88.41 → 91.39

---

## 11. Wine DLL Basecalling (Workaround)

### Working Command
```bash
cd /path/to/wineprefix
wineserver -k 2>/dev/null; sleep 1
WINEDEBUG=-all xvfb-run -a wine cmd /c \
  'cd /d "C:\MegaBACE\Sequence Analyzer" && \
   AutoBaseCall.exe -IF C:\MegaBACE\out\{WELL}.rsd \
   -OD C:\MegaBACE\out\out_Cp312_MD1 \
   -BC CimBC030012_noPuff.dll'
```

### Critical Notes
- **Must use `xvfb-run -a wine cmd /c`** — bare `wine AutoBaseCall.exe` hangs silently
- **DLL ESD output goes to nested path**: `out_Cp312_MD1/out_Cp312_MD1/<name>.esd`
- **`csibq030012.dll` (patched with cave hooks, 267776 bytes) must NOT be in Sequence Analyzer folder** — it causes hangs. Must use original `csibq030012.dll.orig` (265728 bytes)
- **A13.rsd (MB4000) cannot be basecalled via DLL** — Wine hangs even with `wine cmd /c`

---

## 12. Key Files Inventory

### Core Implementation
| File | Description |
|---|---|
| `cimarrontv.py` (2577 lines) | Python Cimarron 3.12 reimplementation (best: 89.98% NW) |
| `cimarrontv_V1.py` (635 lines) | Older version (broken: only 37 bases) |
| `mbsa_rebuild.py` (474 lines) | Faithful DLL port attempt (64% NW, incomplete) |
| `sequencing_gui_V15.py` (210KB) | GUI with greedy caller (visual approximation) |

### Settings
| File | Description |
|---|---|
| `settingsV10.json` | Best Python settings (88.9% mean plate via GUI) |
| `settingsV8.json` | Previous best (88.3% mean plate) |
| `A01_settings.json` | A01-specific settings |
| `A01_matrix.json` | A01 crosstalk matrix |

### Evaluation
| File | Description |
|---|---|
| `eval_ground_truth.py` | Batch evaluation against DLL ESDs |
| `eval_ground_truth.json` | 96-well results (89.98% mean NW) |
| `extract_training_data.py` | RSD/ESD parser for training data |

### Analysis Scripts
| File | Description |
|---|---|
| `basecall_scripts/gui_greedy_fullplate_v10.py` | V10 96-well evaluation |
| `basecall_scripts/greedy_v10_sweep.py` | V10 parameter sweep |
| `basecall_scripts/greedy_sweep.py` | Original parameter sweep |
| `basecall_scripts/balance_diag.py` | Channel balance diagnosis |
| `basecall_scripts/greedy_fill.py` | Fill-in testing |
| `basecall_scripts/greedy_fullplate.py` | Full plate evaluation |
| `basecall_scripts/greedy_refine.py` | Refinement testing |
| `basecall_scripts/greedy_merge.py` | Merge testing |

### Data
| Path | Description |
|---|---|
| `MB1000_M13_DT/{WELL}.rsd` | Raw traces (96 wells) |
| `MB1000_M13_DT/MB1000_M13_DT_Cp312_MD1/{WELL}.esd` | DLL ground truth ESDs |
| `MB4000_DEMO_DATA/A01.rsd` | Different instrument (MB4000) |
| `wineprefix/drive_c/MegaBACE/` | Wine installation with DLLs |

### Wine/DLL Setup
| Path | Description |
|---|---|
| `wineprefix/drive_c/MegaBACE/Sequence Analyzer/csibq030012.dll.orig` | Original DLL (265728 bytes) |
| `wineprefix/drive_c/MegaBACE/Sequence Analyzer/CimBC030012_noPuff.dll` | Wrapper DLL |
| `wineprefix/drive_c/MegaBACE/out/out_Cp312_MD1/Raw_data.esd` | DLL output |

---

## 13. Environment Notes

- Home PC system pip may be blocked (PEP 668). Biopython 1.88 is installed ONLY in `/tmp/opencode/benv` venv (which has NO PyQt5). `electropherogram` is NOT on PyPI.
- Data has no `.ab1` files — only `.rsd`/`.esd`.
- Windows XP MegaBACE files on USB `KINGSTON`: `MegaBACE/` (base DLLs, demo data), `DataSystem/` (xtalk.tdb, mapping sets), `CE/` (related docs). NOT Windows XP compatible.
- The MegaBACE `Base Calling` DLLs (`basecall.dll`, `CimBC030012_*.dll`, etc.) are Windows XP binaries — not directly runnable on modern OS without emulation.

### How to Reproduce/Verify (headless)
- 96-well V10+greedy: `/tmp/opencode/gui_greedy_fullplate_v10.py` (expect 88.9/89.2/84.1)
- 8-well V10 sweep: `/tmp/opencode/greedy_v10_sweep.py`
- 96-well V8 baseline: `/tmp/opencode/gui_greedy_fullplate.py` (88.3/88.6/83.0)
- Parameter sweep: `/tmp/opencode/greedy_sweep.py`
- Fill-in test: `greedy_fill.py`
- Balance diagnosis: `balance_diag.py`

---

## 14. Open Problems / Next Steps

### Critical: Decode the 4x FFT Upsampling Block
- Address: `csibq030012.dll` offsets 0x10270, 0x10d6d, 0x4889
- This is the single most important piece to decode
- Without it, faithful port only achieves 64% NW
- With it, the gap should close from ~10% to near-zero

### Secondary: Decode Post-Stage (0x4889)
- Consumes band table after refinement
- Final peak-calling stage in the DLL
- Not yet decoded

### Tertiary: Per-Channel Peak Shape Modeling
- Greedy caller is at structural ceiling for broad peaks
- Need per-channel peak-shape fitting to distinguish single broad peaks from genuine adjacent pairs

### Open Decisions
- **A. Apply V10 preprocessing + best greedy config** as new GUI defaults (recommended immediate step)
- **B. Test MegaBACE bleed matrix** in greedy framework (may yield ~1–2 points)
- **C. Different caller for residual gap** (peak-shape fitting, larger effort)
- **D. Reconsider ESD as position oracle only** (previously rejected)

---

## 15. Derived Tools

### MegaBACE Sequence Analyzer GUI
- `cimarron_analyzer/sequence_analyzer.py` — GUI with DLL basecalling via Wine
- `cimarron_analyzer/analyze_rsd.py` — CLI tool (Python-based, less accurate)
- `cimarron_analyzer/cimarrontv.py` — Python Cimarron engine (experimental)
- `cimarron_analyzer/extract_training_data.py` — ESD parser
- `cimarron_analyzer/peak_detector.py` — Peak detection utilities
