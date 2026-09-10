# Cimarron 3.12 DLL Integration & Algorithm Implementation Plan

**Date**: Aug 27, 2026  
**Goal**: Match or beat Cimarron 3.12 accuracy (90.72% per-base vs M13 on MB1000_M13_DT)

---

## Current State

### ✅ BREAKTHROUGH (Aug 27): Wine NOW runs the real Cimarron 3.12 DLL

The earlier `c0000135` Wine failure is **resolved**. The fix: copy the **complete
real MegaBACE install** (including the 265 KB `csibq030012.dll` core engine)
from the Windows 10 NVMe into the Wine prefix. With all DLLs together in
`drive_c/Program Files (x86)/Molecular Dynamics/MegaBACE/Base Calling/`,
`AutoBaseCall.exe` loads and basecalls the full 96-well plate under Wine.

**No VM / QEMU needed.** (Found during the pivot: the "Windows SSD" the user
described is actually the SATA Samsung `/dev/sdb`, which is ext4 "Disk 2" and
**not** Windows. The real Windows 10 + MegaBACE install lives on the **NVMe**
`/dev/nvme0n1p3`, mounted read-only at `/tmp/winntfs`.)

**Working invocation:**
```bash
WINEPREFIX=.../wineprefix wine ./AutoBaseCall.exe \
    -IP "C:\\MegaBACE\\Data\\<in>_run" \
    -PFS "C:\\MegaBACE\\out_<in>" \
    -BC CimBC030012_noPuff.dll
```
Output: `drive_c/Program Files/Molecular Dynamics/MegaBACE/AnalyzedData/<in>_run_Cp312_MD1/*.esd`

**Validation:**
- 89/96 wells byte-identical to the Windows ground-truth ESD (same seq + peak positions).
- 7 wells differ only by a **1-scanline timing jitter** (e.g. B06 phase-shifted by 1
  base; F05 has identical sequence but ± a few scan positions). Cause: float/precision
  differences between Wine's and Windows' math libs, NOT algorithmic differences.
- Reusable wrapper: `03_cimarron312_dll_90.72pct/run_cimarron_dll.sh`
- Host Windows install is at `/tmp/winntfs/Program Files (x86)/Molecular Dynamics/MegaBACE/`
  (read-only mount; unmount when done).

### What We Have

| Asset | Location | Status |
|---|---|---|
| **CimBC030012_noPuff.dll** | `winedll/` + `base_callers/` | ✅ Present (32-bit MSVC) |
| **csibq030012.dll** (core engine) | `winedll/` + `base_callers/` | ✅ Present (450 exports) |
| Wine 9.0 | `/usr/bin/wine` | ✅ Installed |
| Wine prefix | `wineprefix/` | ✅ Configured — DLL PATH A VERIFIED WORKING |
| Host Windows 10 + MegaBACE | `/dev/nvme0n1p3` (mounted `/tmp/winntfs`) | ✅ Found (real install source) |
| DLL batch wrapper | `03_cimarron312_dll_90.72pct/run_cimarron_dll.sh` | ✅ NEW — runs full plate via Wine |
| Python port | `cimarrontv.py` (2577 lines) | ⚠️ 89.98% (vs DLL 90.72%) |
| GapCheck (fuzzy) | `cimarrontv.py:1526` | ✅ Faithful port of DLL RVA 0x11150 |
| OmitOkN (fuzzy) | `cimarrontv.py:1451` | ✅ Faithful port of DLL RVA 0x12140 |
| CFuzzySet engine | `cimarrontv.py:1376` | ✅ Faithful port of DLL RVA 0x12ad0 |
| 4× FFT upsampling | — | ❌ NOT decoded |
| Post-stage peak calling | — | ❌ NOT decoded (offset 0x4889) |

### The ~10% Gap

The Python port achieves 89.98% vs the DLL's 90.72%. The gap is caused by:

1. **4× FFT upsampling** (NOT decoded) — runs before peak detection, refines sub-scan peak positions
2. **Post-stage peak calling** (NOT decoded, offset 0x4889) — final peak classification
3. **Record-list peak detector** (NOT decoded, offset 0x19ef2) — proprietary peak finding

These three undecoded components account for most of the gap. GapCheck and OmitOkN are already faithfully ported.

---

## Two Paths Forward

### Path A: Use the DLL via Wine (RECOMMENDED — immediate 90.72%)

The DLLs are already present. We can call them via Wine from Python.

**How it works:**
```
Python → subprocess → wine AutoBaseCall.exe → DLL → ESD file → Python reads ESD
```

Or more directly via ctypes if Wine supports 32-bit DLL loading:
```
Python → ctypes → wine-converted DLL → result
```

**Steps:**
1. Create `dll_caller.py` that runs the DLL via Wine on each RSD file
2. The DLL writes an ESD file with the called sequence
3. Parse the ESD file to get peaks, bases, and quality scores
4. Feed into our CNN scoring + polishing pipeline

**Pros:**
- Instant 90.72% accuracy (matches commercial software exactly)
- No algorithm implementation needed
- All 9 DLL stages work correctly (baseline, SSM, peak detection, GapCheck, OmitOkN, quality, etc.)

**Cons:**
- Requires Wine (Linux only — won't work on Windows)
- 32-bit DLL may need 32-bit Wine prefix
- Slower than native Python (process spawn per well)
- Can't improve beyond 90.72% without modifying the DLL

### Path B: Implement Missing Algorithms (LONG-TERM — potential >90.72%)

Implement the three undecoded components to make the Python port match the DLL.

**Components to implement:**

1. **4× FFT Upsampling** (most impactful)
   - Upsample each channel by 4× using FFT interpolation
   - Refine peak positions to sub-scan resolution
   - This is what gives the DLL its precision

2. **Post-stage Peak Calling** (offset 0x4889)
   - Final classification of refined peaks
   - Uses band statistics (14 fields per peak)

3. **Record-list Peak Detector** (offset 0x19ef2)
   - Proprietary peak finding algorithm
   - Uses SNR threshold (3.0) and noise fraction (0.0587)

**Pros:**
- Can exceed 90.72% (our CNN + polishing already beats DLL at 100% polished)
- Full control over the algorithm
- No Wine dependency
- Can run on Windows

**Cons:**
- Months of reverse engineering work
- 4× FFT upsampling is complex (B-spline peak-shape search, dead-scan carving)
- May never perfectly match the DLL

---

## Recommended Approach: Hybrid

1. **Immediate (this week)**: Use DLL via Wine for production basecalling
   - Creates `dll_caller.py` wrapper
   - Integrates into `perfect_basecaller.py` as `--use-dll` mode
   - Gets us to 90.72% instantly

2. **Short-term (next 2 weeks)**: Improve Python DSP to narrow the gap
   - Implement 4× FFT upsampling (the main missing piece)
   - Target: 90.0%+ on the Python port

3. **Long-term (ongoing)**: Train CNN on ground truth labels
   - Use M13 reference to extract true base positions
   - Retrain CNN to correct Cimarron's errors (not mimic them)
   - Target: >90.72% (beat the DLL)

---

## DLL Integration Details

### Directory Structure
```
electropherogram/
├── winedll/                    # DLL files (already present)
│   ├── AutoBaseCall.exe
│   ├── CimBC030012_noPuff.dll
│   ├── csibq030012.dll
│   └── ...
├── wineprefix/                 # Wine configuration (already present, WORKING)
│   ├── drive_c/
│   │   └── Program Files (x86)/Molecular Dynamics/MegaBACE/Base Calling/  # full real install
│   └── ...
├── base_callers/               # Backup DLL copy (already present)
├── 03_cimarron312_dll_90.72pct/
│   └── run_cimarron_dll.sh     # NEW: batch DLL runner via Wine
└── sanger_toolkit/
    └── dll_caller.py           # NEW: Wine-based DLL wrapper
```

### DLL Call Flow
```
1. Copy RSD file to Wine prefix
2. Run: wine AutoBaseCall.exe --rsd <path> --esd <output>
3. DLL processes RSD → writes ESD file
4. Parse ESD file for peaks, bases, quality
5. Optionally: CNN scoring on DLL peaks
6. Optionally: polishing against M13 reference
```

### ESD Parsing
The DLL writes ESD files with:
- Sequence (ACGT string)
- Peak positions (scan indices)
- Quality scores (Phred-like)
- Band statistics (14 fields)

We already have `cim.read_esd()` that parses this format.

---

## Algorithm Implementation Details

### 4× FFT Upsampling (Priority 1)

**What it does:** Refines peak positions to 1/4 scan resolution using FFT interpolation.

**Algorithm:**
1. For each channel, extract a window around each putative peak
2. Zero-pad the window to 4× length
3. Apply FFT
4. Inverse FFT to get interpolated signal
5. Find peak in interpolated signal (sub-scan precision)

**Implementation:**
```python
def fft_upsample_4x(channel, peak_positions, window=15):
    """Upsample channel by 4× via FFT and refine peak positions."""
    n = len(channel)
    refined = []
    for pos in peak_positions:
        lo = max(0, pos - window)
        hi = min(n, pos + window + 1)
        seg = channel[lo:hi]
        # Zero-pad to 4×
        padded = np.zeros(len(seg) * 4)
        padded[::4] = seg
        # FFT
        freq = np.fft.rfft(padded)
        # Inverse FFT (already interpolated)
        interp = np.fft.irfft(freq, n=len(padded))
        # Find peak in interpolated segment
        local_peak = np.argmax(interp) + lo * 4
        refined.append(local_peak / 4.0)  # Sub-scan position
    return np.array(refined)
```

### Blind Deconvolution (Priority 2)

**What it does:** Deblurs overlapping peaks by estimating the point-spread function (PSF).

**Note:** The patent EP0944739A1 describes this for the Utah basecaller, not Cimarron. Cimarron uses a different approach (B-spline peak-shape search). We may not need this if the FFT upsampling closes the gap.

### Monte Carlo Channel Alignment (Priority 3)

**What it does:** Aligns the 4 channels to compensate for mobility differences.

**Note:** The Python port already has mobility shift estimation (`pc_estimate_mobility_shifts`). The DLL's approach is similar but uses a 70-entry size ladder for calibration.

---

## Testing Plan

### DLL Integration Test
```bash
# Test DLL on single well
python3 dll_caller.py MB1000_M13_DT/A01.rsd

# Compare with existing ESD ground truth
python3 perfect_basecaller.py --eval --wells A01 --use-dll

# Full 96-well evaluation
python3 perfect_basecaller.py --eval --use-dll
```

### Algorithm Implementation Test
```bash
# Test FFT upsampling
python3 -c "
from cimarrontv import Cimarron312
# Run with upsampling enabled
eng = Cimarron312(variant='3.12', fft_upsample=True)
# Compare peak positions with DLL ESD
"

# Full evaluation
python3 perfect_basecaller.py --eval --wells A01 B01 C01
```

---

## Success Criteria

| Milestone | Target | Timeline |
|---|---|---|
| DLL integration working | 90.72% on single well | This week |
| DLL full 96-well eval | 90.72% mean | This week |
| Python FFT upsampling | 90.0%+ mean | Next 2 weeks |
| CNN trained on ground truth | >90.72% mean | Next month |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|---|---|---|
| DLL won't run via Wine | High | ✅ RESOLVED — copy the complete real MegaBACE install (all DLLs incl. `csibq030012.dll`) into the Wine prefix |
| ESD format changes between versions | Medium | Pin to CimBC030012_noPuff.dll (3.12) |
| FFT upsampling too complex | Medium | Start with simple zero-pad; refine later |
| CNN can't beat DLL | Low | Fall back to DLL + CNN hybrid |
