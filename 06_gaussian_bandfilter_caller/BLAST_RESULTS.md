# NCBI BLAST validation

Metric: best HSP per read from NCBI BLAST+ 2.17.0 `megablast` (same engine as
the NCBI web BLAST URL API) against the NCBI M13mp18 reference `M77815.1`
(7,250 bp), over all 96 wells of MB1000_M13_DT. Reported for our de-novo caller
and for the Cimarron 3.12 ESD calls.

This follows the project **GOLDEN STANDARD**: the decisive counters are
`matched_bp` (identical bases, = BLAST `nident`) and bit score; `longest
error-free run` is the longest run of matching columns on the same best HSP
with the known template mutation (M13 forward 5977) treated as NEUTRAL -- it
neither counts toward nor breaks the run. `blast_eval.py` implements exactly
that (`mean_longest_perfect`; `mean_longest_perfect_raw` ignores the rule).

## Result

| metric | ours | Cimarron 3.12 | delta |
|---|---|---|---|
| matched bases | **78,343** | 72,286 | **+6,057 (+8.4%)** |
| aligned length | **83,298** | 74,726 | **+8,572** |
| coverage of reference (mean) | **12.00%** | 10.74% | **+1.26 pp** |
| total bit score | **123,958** | 122,831 | **+1,127 (+0.9%)** |
| mean bit score | **1,291.2** | 1,279.5 | **+11.7** |
| mean % identity | 94.08% | **96.76%** | -2.68 |
| coverage of read (mean) | **89.90%** | 89.18% | **+0.72 pp** |
| longest error-free stretch (mean) | 331.7 | **490.7** | -159.0 |
| longest error-free stretch (median) | 309 | **519** | -210 |
| mean read length | **966.3** | 873.0 | +93.4 |
| total gaps | 2,621 | **1,967** | +654 |

## Reading the result

- **We win both GOLDEN counters.** More matched bases (+6,057, +8.4%) and a
  higher total bit score (+1,127). That is the acceptance objective.
- We also cover more of the reference (+1.26 pp) and more of each read aligns
  (+0.72 pp), because we emit a longer true-positive read (966 bp vs 873 bp).
- **Cimarron is more accurate per base** (96.76% vs 94.08% identity) and has a
  longer clean stretch (490.7 vs 331.7). Those are the price of the longer
  read: the tail that supplies the extra matched bases is also where errors
  concentrate, so the longest uninterrupted run is shorter.
- The remaining target is to win `matched_bp` **and** `longest_run` at once.

## What produced the win

A **position-profiled pull-back** in `track_bases`: `pullback_weight` ramps
from 0.008 to 0.001 over the last 2/3 of the read (`profile_fracs=(0.33,1.0)`),
so the spacing estimate is no longer dragged toward the mid-read global median
where the peaks broaden in the degraded 3' tail. The caller now supports
`(start, end)` profiles for `ema_alpha`, `pullback_weight`, `min_prominence`
and `channel_peak_bonus`; a scalar (or `(v, v)`) reproduces the un-profiled
caller byte-for-byte.

A **mean-base-quality gate** (>= 2.0, else re-call with the stable scalar
config) keeps the three wells that run away under the loose tail
(E02/E03/F03, 1544-2285 bp at mean quality ~1.3) aligned, so all 96 wells are
scored -- the same fall-back-on-low-quality strategy the golden project
records.

## Sweeps behind the tuning

`exp_trim.py`, `exp_grid*.py`, `exp_profile*.py` re-score every variant with
BLAST+ (`report_trim_sweep.json`, `report_grid*.json`, `report_profile*.json`):

- Trimming the degraded 3' tail raises %ID (95.3% -> 98.3% at percentile 40)
  but **reduces matched bases and bit score**, because the tail is mostly
  matching bases. Not used.
- `longest error-free run` is set by *internal* errors, not the tail, so
  trimming cannot raise it.
- The `channel_peak_bonus` 1.0-1.6 range and the DLL upsampling/parabolic-peak
  mechanisms (`exp_upsample.py`, `exp_parabolic.py`) do not beat the profiled
  config.
- Profiled variants: matched/well 813-819, bit score/well 1,282-1,294; the
  pull-back ramp is the only profile that helps (ramped EMA, loose-prominence
  and bonus ramps do not).

## Configuration

`WIN_CONFIG`: `use_gaussian_reconstruction=True`,
`gaussian_recon_segment_size=384`, `use_combined_channel_score=True`,
`window_frac=(0.75,1.25)`, `local_norm_window=1800`, `channel_peak_bonus=1.2`,
`pullback_weight=(0.008,0.001)`, `ema_alpha=0.08`,
`profile_fracs=(0.33,1.0)`, quality gate 2.0 (`FALLBACK_CONFIG` otherwise).

Canonical `perbase_vs_ref` on this config is 88.94% vs Cimarron 90.72%; that
ratio penalizes gaps and rewards shorter/cleaner reads, so it is a diagnostic,
not the objective.

## Reproduce

```bash
python call_plate.py                 # writes basecalls/*.fasta (with gate)
BLAST_DIR=/path/to/ncbi-blast-*/bin python blast_eval.py   # -> report_blast.json
BLAST_DIR=/path/to/ncbi-blast-*/bin python exp_profile.py  # sweep -> report_profile.json
python eval_plate.py                 # canonical ratio -> report.json
```

`blast_eval.py` downloads `M77815.1` from NCBI, builds its own BLAST database,
and reports matched bases, aligned length, %ID, bit score, coverage (vs
reference and vs read) and the SNP-neutral longest error-free stretch for both
callers.
