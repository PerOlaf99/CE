# v5raw / v5rawnorm — 2-input inference wiring & read-level findings

Status: tested on MB1000_M13_DT (96-well plate) · 2026-09-13

## What was wired

`perfect_basecaller.py` now supports the v5-family dual-input models
(raw/gain-normalized adaptive window `(N,31,4)` + 4-value velocity aux):

- `_raw_profiles()` — FWHM + peak-cadence profiles measured on the raw trace.
- `_velocity_features()` — aux columns in exact training order
  `(fwhm_ratio, spacing_ratio, scan_frac, current_ratio)`, clipped as in the
  extractor (`0.5–4.0`, current `0.5–1.5`).
- `_gain_norm_rows()` — bit-exact copy of `extract_v5rawnorm.gain_normalize`
  (p99 block envelope) + `adaptive_window` (`+/-1.5·fwhm`, clamped 8–48,
  resampled to 31, global z-score).
- `cnn_probs(..., cur_arr=..., gain_norm=...)` — dispatches 1-input
  (v3/v4 fixed-window) vs 2-input (v5, aux) models; threads current trace and
  gain-norm through `call_raw`, `refine_denovo[_v2]` and the `--gain-norm` CLI.

**Preprocessing was verified bit-exact** against the training book
(`v5rawnorm_book.npz`, well A01 scan 2082): max abs diff `0.0`, and the
production path reproduces book predictions exactly (same-call frac 1.0).

## Critical bug found & fixed (this is the headline)

Extraction already z-scores each window (`adaptive_window`), and the trainer
also calls `zscore(X)` before fitting and evaluating (`train_v5raw.py`).  The
live-run path built the book-equal (single-z) windows but the model was trained
on double-z windows.  Result: on exact training anchors the model scored
**30.3%** single-z vs **86.1%** double-z; the wired read was complete garbage
(plate NW identity ~35, most wells unalignable).

Fix: `cnn_probs` re-applies the per-window z-score (`_zscore_rows`) on the
gain-norm path, mirroring the trainer.  After the fix the same plate run reads
coherently.

## Results

### 1. Controlled window-level accuracy (identical 62,475 held-out windows)

Labels = ESD (the training target); `TRUTH` = ESD==M13 subset (26,137 rows).

| model | overall | TRUTH | tailtail (reg 3) |
|---|---|---|---|
| v5  (3-aux, raw adaptive)   | 62.6% | 82.0% | 42.7% |
| v5raw (4-aux, raw adaptive) | 61.7% | 79.4% | 49.0% |
| v5rawnorm (4-aux + gain)    | 61.7% | 79.2% | **51.4%** |

### 2. Full-plate read accuracy, production path (`call_raw`)

| config | NWvsESD | oursRaw (de novo vs M13) | oursPolished |
|---|---|---|---|
| v4 fixed-window ensemble (16 reg models) | **86.20%** | **86.37%** | 100.0% |
| v5rawnorm (2-input, gain-norm) | 73.74% | 74.33% (90/96 wells) | 100.0% |

Per-position (double-z) agreement of v5rawnorm vs nearest ESD base: A01 84.3%,
A02 74.4% — uniform in anchor offset (±1, ±2 scans identical), so the residual
gap is label quality, not anchor placement.

## Verdict

- The v5-family inference path is now correctly implemented and *validated*; the
  missing double z-score was a real latent bug that would have shipped garbage.
- v5rawnorm's genuine, repeatable gain is **tailtail (end-of-read) classification
  (+8.7pp over v5)**, which is where v4/v3 models are weakest.
- It is nonetheless a **read-level regression today**: gains are confined to the
  tail while the body performs worse than v4 (overall/window and on-plate raw
  accuracy 74% vs 86%), and 6/96 wells fail alignment.  The de-novo bar stays
  the v4 fixed-window ensemble; polished output still reaches 100% either way.

## Next steps if the tailtail gain is wanted in production

- Keep v4 family for the read; use v5rawnorm only as a tailtail-side re-call /
  confidence veto at `scan_frac > 0.85` (its validated region of strength).
- or retrain on engine-anchored windows (candidates from `call_raw`, not ESD)
  so training and inference peak sets match exactly.