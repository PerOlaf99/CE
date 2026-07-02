# DLL Reverse Engineering Analysis

## Overview
The `base_callers/` directory contains 15 Windows PE32 DLLs from the original Cimarron/Molecular Dynamics base calling software (circa 2001, Visual C++ 6.0). These implement the 6 base calling variants used to generate the `.esd` reference files.

## Architecture

### Cimarron 3.12 (`csibq030012.dll` + `CimBC030012_*.dll`)
- **Main engine**: `csibq030012.dll` (265KB, 450 exports)
- **Wrapper**: `CimBC030012_noPuff.dll` (32KB, thin wrapper)
- **Variants**:
  - `CimBC030012_noPuff.dll` → Standard
  - `CimBC030012_beautify.dll` → Aligned (calls `RdrOut::Beautify`)
  - `CimBC030012_printify.dll` → Even Spacing

### Cimarron 1.53 (`csibq153.dll` + `CimBc010053_*.dll`)
- **Main engine**: `csibq153.dll` (327KB, 330 exports)
- **No Annotate class** (simpler than 3.12)
- **Has `equalizer`, `phredify`, `truvelAdjust`** not in 3.12
- **Variants**:
  - `CimBc010053_beautify.dll` → Phat/Aligned
  - `CimBc010053_phredify_noPuff.dll` → Slim Phredify

### Molecular Dynamics (`Sqcr.dll` + `GTAL.dll` + `MATH.dll`)
- **Interface**: `Sqcr.dll` (221KB, 20 exports)
- **Core**: `GTAL.dll` (100 exports) — `MDWell`, `MDPeak`, `MDTrace` classes
- **Math**: `MATH.dll` (225 exports) — matrices, FFT, Legendre polynomials, curve fitting
- **Different approach**: peak fitting (Gaussian), FFT-based filtering, spectral separation via `MDWell::specSep`

### Support DLLs
- `basecall.dll` (308KB) — Older/alternative Cimarron engine (same API as csibq030012)
- `csibq153.dll` (327KB) — Cimarron 1.53 quality scoring
- `csibq030012.dll` (265KB) — Cimarron 3.12 quality scoring
- `MATH.dll` (65KB) — MD math library (matrices, vectors, FFT, Legendre polynomials)
- `GTAL.dll` (40KB) — MD trace/peak/well classes
- `core.dll` (99KB) — TIFF I/O, MFC UI dialogs, memory management
- `MDRegistry.dll` (28KB) — Windows registry access
- `DataFiles.dll` (90KB) — COM registration only
- `Abd.dll` (49KB) — Unknown

## Key Algorithms Discovered

### Cimarron Pipeline (csibq030012)
1. **Input**: `Wvfm` (waveform) — 4 channels
2. **Preprocessing**: `Wvfm::preproc` — outlier attenuation, baseline correction (`Wvfm::baseline`, `Wvfm::bestBaseline_`), Savitzky-Golay smoothing (`Wvfm::savitzkyGolay`, window=11)
3. **Spectral Separation**: `Wvfm::specSep` — matrix inversion, cross-talk correction via `ObsInpSpec::setCFTblEntry`
4. **Peak Detection**: `Wvfm::decimateP`, peak finding
5. **Mobility Correction**: `Mobility::search` — tries offsets [-5..+5] per channel, picks best
6. **Band Stats**: `BandStatArray` — position, height, width, spacing, signal/noise, quality
7. **Quality Scoring**: `RdrOut::bandqual` → `BandStat::qual` — weighted: dominance + SNR + amplitude
8. **Gap Checking**: `RdrOut::cutoff` → gap detection
9. **Post-processing**: `RdrOut::Beautify` (align), `RdrOut::phredify` (Phred scores)
10. **Smith-Waterman**: `SW` class for alignment, consensus calling

### Molecular Dynamics Pipeline (Sqcr.dll + GTAL.dll)
1. **Input**: `SetRawData` → `MDWell` with 4-channel traces
2. **Preprocessing**: `MDTrace::trippleMexicanHatFilter`, `MDWell::cleaning`, `MDWell::deSinglePntDip`
3. **Spectral Separation**: `MDWell::specSep(Matrix)` — matrix-based unmixing
4. **Peak Detection**: `MDPeak` — Gaussian fitting, `MDPeak::split`
5. **Mobility**: Various shift calculations
6. **Quality**: `ReportSequence`, `ReportMobShiftUsed`, `ReportSpecSeparatnMatrixUsed`

## Key Differences Between Python Reimplementation and DLLs

### What Python Gets Right
- Spectral separation via matrix inverse ✓
- Savitzky-Golay filter (window=11) ✓
- Mobility search with offset candidates ✓
- Quality scoring from dominance + SNR + amplitude ✓
- Gap checking ✓

### What Python May Be Missing
- **Cimarron 3.12**: `Annotate` class with `getCFData`, `getSpecSepQual`, `setSpecSepDepth` — cross-talk correction tables
- **Cimarron 3.12**: SST pattern matching (`setSSTPattern`, `hasSSTPattern`)
- **Cimarron 3.12**: `ObsInpSpec` with full CF table setup
- **Cimarron 1.53**: `equalizer` — channel equalization not in Python
- **MD**: Completely different peak fitting approach (Gaussian + splitting)
- **MD**: Mexican hat filter for baseline/noise
- **MD**: FFT-based processing (`MDdbSpectra::FFTforward`, `FFTinverse`)

## Mysterious Parameters to Investigate
- `csibq030012`: `?polfit@@YAHPBM00HHW4PFWGHT@@QAMAAM@Z` — polynomial fit with weights
- `csibq030012`: `?savgol@@YAHQAMHHHHH@Z` — standalone Savgol function (maybe different params?)
- `csibq030012`: `?dfour1@@YAXQANKH@Z` — FFT routine
- `csibq153`: `?equalizer@Wvfm@@AAEXPAPAMHH@Z` — channel equalization
- `csibq153`: `?phredify@RdrOut@@AAEXXZ` — Phred quality conversion
- `GTAL.dll`: `?measureSSM@MDWell@@MBE_NAAVMDdbMatrix@@HHNN@Z` — spectral separation matrix measurement
