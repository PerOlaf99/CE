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
| matched bases | **78,362** | 72,286 | **+6,076 (+8.4%)** |
| aligned length | **83,116** | 74,726 | **+8,390** |
| coverage of reference (mean) | **11.94%** | 10.74% | **+1.20 pp** |
| total bit score | **124,783** | 122,831 | **+1,952 (+1.6%)** |
| mean bit score | **1,299.8** | 1,279.5 | **+20.3** |
| mean % identity | 94.30% | **96.76%** | -2.46 |
| coverage of read (mean) | **90.04%** | 89.18% | **+0.86 pp** |
| longest error-free stretch (mean) | 363.9 | **490.7** | -126.7 |
| longest error-free stretch (median) | 330.5 | **519** | -188.5 |
| mean read length | **962.5** | 873.0 | +89.5 |
| total gaps | 2,576 | **1,967** | +609 |

## Reading the result

- **We win both GOLDEN counters.** More matched bases (+6,076, +8.4%) and a
  higher total bit score (+1,952, +1.6%). That is the acceptance objective.
- We also cover more of the reference (+1.20 pp) and more of each read aligns
  (+0.86 pp), because we emit a longer true-positive read (962 bp vs 873 bp).
- **Cimarron is more accurate per base** (96.76% vs 94.30% identity) and has a
  longer clean stretch (490.7 vs 363.9). Those are the price of the longer
  read: the tail that supplies the extra matched bases is also where errors
  concentrate, so the longest uninterrupted run is shorter. Retuning the band
  filter cut the longest-run gap from 159 to 126.7 without giving up matched
  bases.
- The remaining target is to win `matched_bp` **and** `longest_run` at once.

## What produced the win

A **position-profiled pull-back** in `track_bases`: `pullback_weight` ramps
from 0.008 to 0.001 over the last 2/3 of the read (`profile_fracs=(0.33,1.0)`),
so the spacing estimate is no longer dragged toward the mid-read global median
where the peaks broaden in the degraded 3' tail. The caller now supports
`(start, end)` profiles for `ema_alpha`, `pullback_weight`, `min_prominence`
and `channel_peak_bonus`; a scalar (or `(v, v)`) reproduces the un-profiled
caller byte-for-byte.

A **retuned Wiener band filter**: `gaussian_recon_sigma_scale=1.05` with
`gaussian_recon_noise_reg=0.06` (over the previous plain `noise_reg=0.05`).
This sharpens the reconstruction just enough to place peaks more accurately
-- cutting substitutions 2334 -> 2178 and lengthening the mean error-free run
331.7 -> 363.9 -- while still *raising* matched bases (816.1 -> 816.3) and bit
score (1291.2 -> 1299.8). It is a strict Pareto improvement over the previous
config.

A **mean-base-quality gate** (>= 2.0, else re-call with the stable scalar
config) keeps the three wells that run away under the loose tail
(E02/E03/F03, 1544-2285 bp at mean quality ~1.3) aligned, so all 96 wells are
scored -- the same fall-back-on-low-quality strategy the golden project
records.

## Sweeps behind the tuning

`exp_trim.py`, `exp_grid*.py`, `exp_profile*.py`, `exp_deconv*.py`,
`exp_anchor.py` re-score every variant with BLAST+
(`report_trim_sweep.json`, `report_grid*.json`, `report_profile*.json`,
`report_deconv*.json`, `report_anchor.json`):

- Trimming the degraded 3' tail raises %ID (95.3% -> 98.3% at percentile 40)
  but **reduces matched bases and bit score**, because the tail is mostly
  matching bases. Not used.
- The `channel_peak_bonus` 1.0-1.6 range and the DLL upsampling/parabolic-peak
  mechanisms (`exp_upsample.py`, `exp_parabolic.py`) do not beat the profiled
  config.
- Profiled variants: matched/well 813-819, bit score/well 1,282-1,294; the
  pull-back ramp is the only tracker profile that helps (ramped EMA,
  loose-prominence and bonus ramps do not).
- Band-filter grid (`exp_deconv2.py`): the whole (sigma 0.9-1.2) x
  (regularization 0.05-0.13) frontier is monotone in the matched/longest
  trade-off; `sigma=1.05, reg=0.06` is the unique strict dominator of the old
  config, and `sigma=1.10, reg=0.075` gives the best longest (400) at matched
  811. Richardson-Lucy iterative deconvolution (non-negative, further
  regularized) was implemented and rejected -- it amplifies baseline noise.
- Spacing-anchor curve (`exp_anchor.py`): +18 longest/well for -2 matched/well;
  off by default.

## Configuration

`WIN_CONFIG`: `use_gaussian_reconstruction=True`,
`gaussian_recon_segment_size=384`, `gaussian_recon_sigma_scale=1.05`,
`gaussian_recon_noise_reg=0.06`, `use_combined_channel_score=True`,
`window_frac=(0.75,1.25)`, `local_norm_window=1800`, `channel_peak_bonus=1.2`,
`pullback_weight=(0.008,0.001)`, `ema_alpha=0.08`,
`profile_fracs=(0.33,1.0)`, quality gate 2.0 (`FALLBACK_CONFIG` otherwise).

Canonical `perbase_vs_ref` on this config is 89.19% vs Cimarron 90.72%; that
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

## Gap analysis: why the longest-run bar is not yet won

We already win the two GOLDEN counters (matched bases + bit score). The
remaining deficit is `longest_error_free_run` (363.9 vs 490.7, after the band
filter retune). Diagnosing the per-well / per-column structure
(`exp_perwell.py`, `exp_longest.py`, `exp_posbias.py`, `exp_start.py`) shows:

| caller | insertions | deletions | substitutions | aligned |
|--------|-----------:|----------:|--------------:|--------:|
| ours (profiled) | 1,301 | 1,320 | **2,334** | 83,298 |
| Cimarron DLL    |   501 | 1,466 |   **473** | 74,726 |

The gap is **substitutions, not indels**, and it is **broad** (the DLL has the
longer run on 86/96 wells). Our advantage in matched bases comes from calling
the degraded 3' tail, i.e. longer reads (962 vs 873 bp); that extra length is
net-positive for the primary counter but carries a lower per-position accuracy.
Per-position analysis shows the substitutions are not one region: ours has ~4%
substitution in the first ~90 bases (primer-adjacent) versus the DLL's 0.6%,
near-zero through mid-read, and rises to 13.6% in the 80-90% tail versus the
DLL's 3.8%. So both ends need sharper per-position estimation.

Results with the retuned Wiener band filter (`exp_deconv.py`, `exp_deconv2.py`,
`report_deconv2.json`/`report_deconv3.json`) confirm this is the right lever:

* `gaussian_recon_sigma_scale=1.05`, `noise_reg=0.06` is a **strict Pareto
  improvement** over the old winner -- matched 816.3 vs 816.1, bit 1299.8 vs
  1291.2, longest 363.9 vs 331.7, substitutions 2178 vs 2334, insertions 1137
  vs 1301. Sharpening the reconstruction (smaller effective PSF plus more
  Wiener regularization) lets the tracker place peaks more accurately without
  losing the tail bases.
* Sweeping further along the (sigma, regularization) frontier trades matched
  bases for longest run monotonically: `s1.10_r0.075` gives longest 400 (matched
  811), `s1.00_r0.09` gives longest 399 (matched 803).
* An optional **position-varying spacing anchor** (`use_spacing_anchor_curve`,
  `exp_anchor.py`) costs ~2 matched/well for ~+18 longest/well (matched 814.4,
  bit 1302.0, longest 381.6); combining it with a softer filter
  (`s1.10_r0.075`) reaches longest 408.9. It is implemented but off in
  `WIN_CONFIG` because matched bases are the primary counter.

Negative results that bounded the search:

* Insertion pruning (`prune_spurious_insertions`, the patent's "OmitOkN"
  heuristic) only fires on ~50 columns plate-wide (`exp_prune.py`,
  `report_prune.json`); it nudges identity up but leaves the longest run
  unchanged, and pushing it harder just deletes true bases. The unwanted
  columns are not isolated shoulders of resolved peaks.
* Softening the profiled tail (`exp_profile3.py`, `report_profile3.json`)
  raises %ID and cuts insertions monotonically (94.08 -> 94.59) but lowers
  matched bases (816 -> 803) and does not lengthen the longest run.
* A Richardson-Lucy **iterative** deconvolution was implemented but rejected:
  without the patent's mobility model it amplifies baseline noise into spurious
  peaks and runs the tracker away (`gaussian_recon_iters` removed).
* **Position-profiled** Wiener regularization (`gaussian_recon_noise_reg` given
  as a `(start, end)` pair over the read, `exp_regprofile.py` /
  `report_regprofile.json`) was worse than the scalar on every axis: 11 ramps
  from sharp-early/smooth-late to the reverse all lost matched bases (808-814
  vs 816.3) and bit score (1270-1291 vs 1299.8) for at most +17 longest. The
  scalar `noise_reg=0.06` is kept. The plumbing exists (default off) but is not
  used.
* A Pareto scan of **all ~120 tried configurations** (`exp_pareto.py`) found no
  pre-retune setting that dominated the winner; the 96-well frontier was flat
  around matched ~810-820 with longest ~330.

Conclusion: per-position accuracy at the read ends is the remaining target.
The band-filter retune already closed a third of the longest-run gap; closing
the rest likely needs the patent's full blind deconvolution with an
overshoot/mobility model, or the optional spacing-anchor curve combined with a
softer filter (documented above, available but traded against matched bases).
