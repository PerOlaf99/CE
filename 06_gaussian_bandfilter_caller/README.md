# 06 - Gaussian band-filter tracking caller

De-novo, reference-free basecaller for the MegaBACE MB1000_M13_DT plate.
It **calls more correctly-identified bases than Cimarron 3.12** when measured
with NCBI BLAST+ against the authentic NCBI M13mp18 reference (`M77815.1`).

## Headline result (96 wells, NCBI BLAST+ megablast, best HSP per read)

| metric | ours | Cimarron 3.12 (ESD) | delta |
|---|---|---|---|
| **matched bases** | **78,362** | 72,286 | **+6,076 (+8.4%)** |
| **aligned length** | **83,116** | 74,726 | **+8,390** |
| **coverage of reference (mean)** | **11.94%** | 10.74% | **+1.20 pp** |
| **total bit score** | **124,783** | 122,831 | **+1,952 (+1.6%)** |
| **mean bit score** | **1,299.8** | 1,279.5 | **+20.3** |
| mean % identity | 94.30% | **96.76%** | -2.46 |
| **coverage of read (mean)** | **90.04%** | 89.18% | **+0.86 pp** |
| longest error-free stretch (mean) | 363.9 | **490.7** | -126.7 |
| mean read length | **962.5** | 873.0 | +89.5 |
| total gaps | 2,576 | **1,967** | +609 |

We win on the **two GOLDEN counters -- matched bases and bit score** -- as well
as aligned length, both coverages and read length; Cimarron keeps the higher
per-base **identity** (it calls shorter reads) and the longer **error-free
stretch**. The remaining target is to win the longest-run bar too.

## Precision mode: longest error-free run / %ID

`call_plate.py --mode precision` (config `WIN_CONFIG_PRECISION`) is the opposite
corner of the frontier. The operator prioritised the **longest error-free run
and per-base identity**, accepting a shorter read and fewer matched bases to get
there. It keeps the same reconstruction and peak tracker as `WIN_CONFIG` but

- raises the Wiener regularization `gaussian_recon_noise_reg` 0.06 -> **0.128**
  (sharper-smoothed peaks place more bands exactly right),
- enables the **spacing-anchor curve** (`use_spacing_anchor_curve`) to stabilise
  the local spacing estimate, and
- applies a deep **38th-percentile quality trim** that discards the degraded
  read ends where nearly all residual errors live.

The regularization and trim depth were swept jointly (`exp_prectrimN.py`): the
longest run peaks sharply at reg ~0.128 / pct 38 and collapses past reg 0.14.

| metric | golden mode | **precision mode** | Cimarron 3.12 |
|---|---|---|---|
| matched bases | **78,362** | 59,403 | 72,286 |
| total bit score | **124,783** | 104,920 | 122,831 |
| mean % identity | 94.30% | **98.19%** | 96.76% |
| longest error-free run (mean) | 363.9 | **473.1** | 490.7 |
| longest error-free run (median) | 330.5 | **500** | 519 |
| mean read length | **962.5** | 627.4 | 873.0 |
| total gaps | 2,576 | **787** | 1,967 |
| canonical `perbase_vs_ref` | 89.19% | **97.81%** | 90.72% |

Precision mode **wins % identity by +1.43 pp over Cimarron** (98.19 vs 96.76)
and cuts total gaps by 60%, closing the longest-run gap from -126.7 to -17.6 bp
(3.6%). It cannot win the longest bar outright: a reference-free per-well
choice between the golden and precision calls would reach an oracle mean of
486.9 (vs Cimarron 490.7), but every quality-based proxy tested (`exp_select.py`,
`report_select.json`) picks worse than pure precision, so no such selector ships.

Two changes get us here. The **position-profiled pull-back** ramps
`pullback_weight` 0.008 -> 0.001 across the last 2/3 of the read
(`profile_fracs=(0.33, 1.0)`), so the spacing estimate stops being dragged back
toward the mid-read global median exactly where the peaks broaden in the
degraded 3' tail; this recovered the tail (matched 793 -> 816/well). Then
**retuning the Wiener band filter** (`gaussian_recon_sigma_scale=1.05`,
`gaussian_recon_noise_reg=0.06`) sharpens the reconstruction just enough to cut
substitutions and lengthen the error-free runs (331.7 -> 363.9) while still
*raising* matched bases (816.1 -> 816.3) and bit score (1291.2 -> 1299.8) -- a
strict Pareto improvement over the previous config. A mean-base-quality gate
(>= 2.0) keeps the three wells that run away under the loose tail (E02/E03/F03,
1544-2285 bp at mean quality ~1.3) on the stable scalar config, so all 96 wells
still align.

Earlier experiments that did **not** ship: trimming the degraded 3' tail
(`exp_trim.py`) raises %ID but lowers matched bases and bit score, because the
tail is mostly matching bases; insertion pruning (`prune_spurious_insertions`,
the patent's OmitOkN) and tail-softening profiles (`exp_profile3.py`) raise
identity but do not move the longest run; a full Richardson-Lucy iterative
deconvolution was implemented and rejected because it amplifies baseline noise
into spurious peaks and runs the tracker away; the `channel_peak_bonus` sweep
(`exp_grid*.py`) and the DLL's upsampling / parabolic-peak mechanisms
(`exp_upsample.py`, `exp_parabolic.py`) did not beat the profiled config. An
optional position-varying spacing anchor (`use_spacing_anchor_curve`) trims ~2
matched/well for ~+18 longest-run/well and is available but off in
`WIN_CONFIG`; see `exp_anchor.py`.

For reference, the repo's canonical `perbase_vs_ref` ratio on this config is
**88.94%** vs Cimarron 90.72%. That ratio penalizes gaps and rewards shorter,
cleaner reads and does **not** track the number of correct bases, so it is
reported but not used as the objective (the project GOLDEN STANDARD ranks
matched bases first, bit score next).

## What it does

Fully unsupervised DSP + peak tracking. Pipeline order follows the real Sequence
Analyzer stage order (Baseline subtract -> Spectral separation -> Normalization
-> **Band filter** -> Mobility shift correction -> base calling):

1. `robust_baseline_subtract(smooth_trace(trace))`
2. spectral separation (default 4x4 cross-talk matrix)
3. local channel normalization
4. **Gaussian reconstruction band filter** - reconstructs the band-limited trace
   and suppresses noise-induced spurious peaks (the previously-missing stage
   from `03_cimarron312_dll_90.72pct/CIMARRON_MASTER.md`).
5. mobility shift correction
6. spacing-tracked greedy base calling with a combined multi-channel score and
   a position-profiled spacing pull-back.

The band filter, the combined score and the falling pull-back weight let the
spacing tracker follow the broadening peaks in the degraded 3' end, which is
where Cimarron's original coverage advantage lived.

## Winning configuration (`WIN_CONFIG` in `call_plate.py`)

```python
use_gaussian_reconstruction  = True    # the band filter
gaussian_recon_segment_size  = 384
use_combined_channel_score   = True
window_frac                  = (0.75, 1.25)
local_norm_window            = 1800
channel_peak_bonus           = 1.2
pullback_weight              = (0.008, 0.001)   # position-profiled
ema_alpha                    = 0.08
profile_fracs                = (0.33, 1.0)
# quality gate: mean base quality >= 2.0, else FALLBACK_CONFIG
```

The result is robust around the profile: ramp start 0.25-0.50 all beat Cimarron
on matched bases and bit score; the ramp end 0.000-0.002 is flat; only the
pull-back ramp helps (ramped EMA, loose-prominence and bonus ramps do not).
Do not assume the exact constants transfer to another plate; the band filter,
combined score, position-profiled pull-back and the quality gate are the
transferable parts.

## Reproduce

```bash
# basecall the plate -> basecalls/*.fasta (golden: matched-bases / bit optimum)
python call_plate.py

# longest-run / %ID optimum -> basecalls_precision/*.fasta
python call_plate.py --mode precision

# authoritative BLAST+ comparison -> report_blast.json
BLAST_DIR=/path/to/ncbi-blast-*/bin python blast_eval.py

# precision-mode scoreboard -> report_precision_mode.json
BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_scoreprec.py

# canonical ratio + Cimarron bar -> report.json
python eval_plate.py
```

## Files

- `cimarron_basecaller/` - vendored spacing-tracker caller (shipped with the
  user-provided MegaBACE Cimarron software bundle; numpy/scipy only on this path).
- `call_plate.py` - applies `WIN_CONFIG` (default) or `WIN_CONFIG_PRECISION`
  (`--mode precision`), writes per-well FASTA.
- `blast_eval.py` - NCBI BLAST+ comparison, writes `report_blast.json`.
- `eval_plate.py` - canonical scoring, writes `report.json`.
- `canon_metric.py` - vectorized canonical seed-SW aligner `perbase_vs_ref`
  (validated: ESD scores 90.724).
- `exp_trim.py`, `exp_grid*.py`, `exp_profile*.py` - sweeps behind the tuning
  decisions (reports in `report_trim_sweep.json`, `report_grid*.json`,
  `report_profile*.json`).
- `report_blast.json`, `report.json` - plate aggregates.
- `basecalls/` - generated FASTA (created by `call_plate.py`).

## Notes

- No reference sequence and no trained model are used at call time. The M13
  reference is used only for scoring/reporting.
- Earlier versions of this folder claimed a win on the canonical ratio (91.72%
  vs 90.72%). That was misleading: it counted fewer, cleaner bases. See
  `BLAST_RESULTS.md` for the corrected analysis.
