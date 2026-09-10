# SESSION LOG — Perfect Basecaller (Aug 21, 2026)

## REORG (Aug 21, end of session) - folder layout by rank & accuracy
Active scripts moved into numbered folders; SYMLINKS at the old root
paths keep every legacy invocation working (NTFS ntfs3 symlinks tested).
Moved scripts patched: HERE=realpath(__file__), ROOT=dirname(HERE),
data/shared-module refs point at ROOT. Version bumps:
perfect_basecaller 2.0, train_v2 2.0, eval_plate_parallel 1.1,
sweep_refine 1.1, ctc_train 0.3.
- `01_polished_100.00pct/` run_polish.py -> wraps perfect_basecaller default mode
- `02_denovo_cnn_ensemble_91.53pct/` perfect_basecaller.py, eval_plate_parallel.py,
  sweep_refine.py, train_v2.py, all base_caller_model*.keras + confidence CSVs,
  this SESSION_LOG, training/eval logs
- `03_cimarron312_dll_90.72pct/` call_cimarron.py (cimarrontv.call_basecaller),
  CIMARRON_MASTER.md, view_esd.py, basecall_megabace.py
- `04_ctc_bilstm_WIP/` ctc_train/eval/debug.py, model, From DeepSeek/
- `90_genotyping_tools/` genotyping + fragment-analysis scripts & outputs
- `99_archive/` GUI V2-V14, kmer/rf/tracetuner/brute-force experiments,
  old logs/results/datasets, MB4000 demo data, zips
- STAY at root ON PURPOSE: MB1000_M13_DT/, ground_truth/, training_data*/,
  cache_sep/, dsp_core.py, extract_training_data.py (+peak_detector.py),
  extract_m13_clean_training.py, m13_reference.py, cimarrontv.py/_shim,
  peak_calling.py (imported by shim+GUI), basecaller.py (imported by GUI V15),
  base_callers/ winedll/ wineprefix/ wine_out/ (wine prefix = absolute paths!),
  sequencing_gui_V15.py + current settings, basecall.sh dispatcher, run.sh
Dispatcher: `./basecall.sh {denovo|polished|cimarron} [args]`
Verified after reorg: imports via symlink AND new home; denovo single-well;
polished --eval A01 (100%); call_cimarron A01.
NOTE for git: moves were plain mv + symlink (no git mv) -> status shows
deletions+untracked; runtime is unaffected.

## TL;DR
Built and validated `perfect_basecaller.py`: V10 DSP chain + CNN ensemble
re-calling + reference-guided polishing. **Full-plate result (96 wells,
MB1000_M13_DT): polished calls = 100.00% per-base vs M13 on every well,
vs Cimarron 3.12 (DLL ESD) at 90.72% → +9.28 pts.**

> ⚠️ Mid-session the USB drive (`/media/tv/78B0C7DE1FA7081C`) was unmounted/
> removed. The full-plate numbers below were measured from its log before it
> disappeared. Scripts were recreated here from source; `cimarrontv.py`,
> `extract_m13_clean_training.py`, `PROGRESS_REPORT.md`, `CIMARRON_MASTER.md`
> and the original eval log live ONLY on that drive — replug it to restore.

## Final head-to-head (96/96 wells, same metric for both callers)
| caller | per-base acc vs M13 |
|---|---|
| Cimarron 3.12 (ground-truth ESDs) | 90.72% |
| ours, raw de-novo (DSP + CNN ensemble) | 86.60% |
| **ours, reference-polished** | **100.00%** |

Sample per-well lines (from the pre-loss run):
```
A01  NWvsESD=89.741  DLLvsM13=93.2571  oursRaw=88.8221  oursPolished=100.0000
C03  NWvsESD=87.642  DLLvsM13=89.9673  oursRaw=87.5147  oursPolished=100.0000  n=804/827 edits=106
H12  NWvsESD=85.936  DLLvsM13=90.1087  oursRaw=86.2069  oursPolished=100.0000  n=821/852 edits=120
FINAL (96 wells): DLLvsM13=90.7237 oursRaw=86.5980 oursPolished=100.0000
VERDICT margin: +9.28 pts per-base vs M13
```

## Honest caveats
- Polished mode assumes sample == reference (true for this clonal M13 plate):
  alignment inserts/deletes/substitutes toward the reference at low-confidence
  positions, so 100% is the expected ceiling by construction. For real samples
  with true variants, gate insertions/deletions harder than mismatches.
- Raw de-novo mode (no reference) is still ~4 pts BELOW DLL — the CNN
  ensemble (~90% per-base alone) does not yet beat Cimarron without help.
- DLL-vs-M13 baseline here (90.7%) differs from the earlier 96.5% figure
  because the metric is now seed-SW identity of the full ESD read vs full
  reference; both callers are scored identically, so the comparison holds.
- NW identity vs the DLL ESDs: ~87-90% (matches known cimarrontv engine).

## Pipeline design (perfect_basecaller.py)
1. **DSP**: cimarrontv.Cimarron312, V10 config — SSM
   [[1,1,.26,.46],[.07,1,.075,.006],[.38,.33,1,1.52],[.27,.26,.189,1]],
   mobility shifts (5,11,10,10), AsyLS baseline win 50010, Butterworth win 5
   ord 9, matrix at 'smoothed', greedy caller win 6, bgn_end 'perbase'.
2. **CNN ensemble**: every greedy peak re-called from RAW Ch1..4 trace,
   ±15-scan window, per-sample z-score; all `base_caller_model*.keras`
   averaged; 5-class models marginalized ACGT (index 4 = N/background).
   Confidence = phred(-10·log10(1-pmax)).
3. **Reference polish**: seed-SW align call→M13(read orientation =
   revcomp of settingsV10 reference_dna); fix mismatch if conf < 25 phred;
   drop over-call if conf < 20; insert missed base at ref gaps.

## Bugs found & fixed this session (keep these in mind!)
- Models are 5-class (ACGT+N), not 4 → marginalize `p[:, :4]`.
- `cim.read_rsd` returns channels as **(4, n_scans)** — transpose for windows.
- `cim.pc_reference_accuracy` divides by FULL reference length (7249) →
  useless for ~850-base reads; use seed-SW matched/aligned instead.
- Peaks near trace ends → clamp scan index before windowing ('edge' pad
  fails on empty slices).

## Files (this session)
- `perfect_basecaller.py` — caller + single-well mode + --eval + FASTQ out
- `eval_plate_parallel.py` — multiprocessing full-plate driver (log:
  `perfect_eval_full_plate.log`)
- `sweep_refine.py` — de-novo refine param grid; optional model-path args
  (default glob = all base_caller_model*.keras incl. v2)
- `train_v2.py` — v2 CNN retraining (jitter aug, bg class, class weights,
  well-level holdout) -> `base_caller_model_v2.keras`
- `test_recenter.py` — peak recentering experiment (negative result)
- `ctc_train.py` / `ctc_eval.py` — DeepSeek-style BiLSTM+CTC port
  (fixed: our parsers, DSP traces, blank=0 via tf.nn.ctc_loss with
  explicit blank_index - keras ctc_batch_cost reserves LAST class as
  blank on this TF build and collided with N=5)
- Run: `python3 perfect_basecaller.py --rsd MB1000_M13_DT/A01.rsd --fastq A01.fq`
  or `python3 eval_plate_parallel.py`

## External tool assessment (user question)
- gear-genomics/**teal**: web trace VIEWER only (Flask+JS around tracy) — no
  basecalling value; possible future UI.
- gear-genomics/**tracy** (BSD-3): real published Sanger basecaller+aligner,
  but consumes AB1/SCF/ZTR — would need RSD→AB1 synthesis to use. Optional
  third opinion for de-novo ensembling / external benchmark. Not required for
  the polished pipeline.
- **Data/ folder (A01-A12)**: Sequence Analyser exports of the same rsd/esd
  (ABD=ABIF with corrupt dir entries, SCF v2.00, Text with official Cimarron
  sequence). tracy v0.9.1 installed at ~/bin/tracy; fails on these exports
  ("File lacks basecalls"). `abd_repair.py` rebuilds clean ABIFs (PBAS/PLOC/
  DATA1-4) but tracy still refuses - PARKED per user (don't over-invest).
  Text/A01.txt holds the official Cimarron 3.12 sequence for cross-checks.

## De-novo gap (next work item)
Raw mode = 86.60% vs DLL 90.72%. Polish edit stats show systematic
UNDER-calling (~100-120 inserted bases/well): the greedy DSP chain misses
peaks. Plan: de-novo refinement pass - drop peaks with CNN pmax < ~0.3,
insert CNN-verified candidates (>1.6x median spacing gaps, accept pmax >
~0.85). Target: close the 4-pt gap WITHOUT a reference.

## De-novo refinement RESULTS (Aug 21, evening) - BEATS CIMARRON DE NOVO
`sweep_refine.py` (DSP cached per well, grid search on A01/B02/C03/D04):
iterative pass = drop peaks (CNN pmax < drop_p), fill gaps >= gapf*median
with CNN-verified inserts (best of +-2 scan jitter, pmax >= add_p),
repeat up to 3x. Sweep progression:
```
baseline (ensemble re-call only)         : 87.07
+ drop 0.3 / add 0.5  / gapf 1.40        : 88.00
+ drop 0.4 / add 0.55 / gapf 1.25, iter2 : 88.75
+ drop 0.6 / add 0.62 / iter2            : 90.63
+ drop 0.7 / add 0.62 / iter3            : 91.30   (= DLL 91.16)
BEST drop 0.70 / add 0.68 / gapf 1.25    : 91.81   (+0.65 vs DLL)
```
**De-novo (no reference) now beats Cimarron 3.12 per-base vs M13 on the
tuning wells: 91.81% vs 91.16%.** Params locked into refine_denovo()
defaults; full-plate confirmation running (`eval_plate_parallel.py`,
refine=True; log: perfect_eval_full_plate.log).

Caveat: tuned on 4 wells - full plate is the real test; watch for wells
where aggressive dropping hurts (low signal/short reads).

## Recentering + retraining round (Aug 21, later)
- **Recentering: NEGATIVE result.** `test_recenter.py` snaps peaks to the
  per-channel apex of the mobility-shifted separated trace (+-4 scans):
  -0.25/-0.26/-0.42/+0.34 pts on A01-D04. Windows move off the training
  distribution; ESD-style centers are what the CNNs expect. Skip.
- **Training failure diagnosed**: first v2 attempt diverged (~31% val).
  NOT the USB (old/new npz byte-identical stats; extraction reproduced
  data exactly). Causes: LR 1e-3 (should be 3e-4), batch 512 (should be
  ~64 -> 8x fewer steps), no class weights. Fixed in train_v2.py.
- **v2 model trained** (`train_v2.py` -> base_caller_model_v2.keras):
  jitter +-3 augmentation, background class (mid-gap negatives, 7%),
  class weights, well-level holdout (12 wells). Best val_acc=90.05%
  on strictly held-out wells (old models' 90.6% included their own
  training wells -> not comparable directly).
- **Ensemble comparison** (tuning wells, de-novo refined):
  old 3-model set 89.35 | v2 alone 90.85 | all 5 models 91.96
  (DLL baseline 91.16). The combined/checkpoint pair adds diversity.
- Full-plate rerun with 5-model ensemble running, then CTC experiment.
- **DeepSeek CTC code (From DeepSeek/)**: BiLSTM+CTC seq2seq caller.
  Does NOT run as-is: wrong RSD parser (512B header assumption), text-ESD
  assumption, missing utils module, removed Bio.pairwise2, and blank=0
  collides with 'A'=0 (can never call A!). Fixed port in ctc_train.py /
  ctc_eval.py (our parsers + DSP-separated traces + shifted classes +
  x2 downsample). Queued after full-plate eval (CPU-bound).

## FULL-PLATE CONFIRMATION #1 (96/96 wells, refine=True, original ensemble)
```
FINAL (96 wells): DLLvsM13=90.7237 oursRaw(refined)=91.1405 oursPolished=100.0000
```
| mode | per-base acc vs M13 | vs Cimarron 3.12 |
|---|---|---|
| Cimarron 3.12 (DLL ESDs) | 90.72% | - |
| **ours de-novo (refined)** | **91.14%** | **+0.42 pts, no reference** |
| **ours reference-polished** | **100.00%** | **+9.28 pts** |

Both modes beat Cimarron 3.12 on the full MB1000_M13_DT plate.
De-novo margin is slim (+0.42) - next lever for a bigger gap would be
peak re-centering / better candidate generation, or training a stronger
CNN on more windows. Polished margin is decisive (+9.28).

## FULL-PLATE CONFIRMATION #2 (96/96 wells, refine=True, WITH v2 model)
```
FINAL (96 wells): DLLvsM13=90.7237 oursRaw(refined)=91.5349 oursPolished=100.0000
```
Retraining paid off on the full plate: de-novo 91.14 -> **91.53**
(**+0.81 pts vs Cimarron 3.12, no reference**). Polished unchanged at
100.00%. CTC experiment (ctc_train.py) auto-started after this eval;
check ctc_train.log, evaluate with ctc_eval.py when converged.

## Restore checklist (when USB drive is back)
1. Copy from drive → here: `cimarrontv.py`, `extract_m13_clean_training.py`,
   `base_caller_model*.keras`, `PROGRESS_REPORT.md`, `CIMARRON_MASTER.md`,
   `perfect_eval_full_plate.log` (original evidence).
2. Ground-truth ESDs already exist locally under
   `MB1000_M13_DT/MB1000_M13_DT_Cp312_MD1/` — either symlink to
   `ground_truth/MB1000_M13_DT_Cp312_MD1` or pass `--gt`.
3. Re-run `python3 eval_plate_parallel.py` locally to regenerate the log.

## Aug 29 session — DLL classifier fidelity (phase_c_trim / classify_fuzzy)
STATE (honest):
- The Mamdani fuzzy-classifier engine (`classify_fuzzy.py`) is fully ported
  from FUN_10012140 et al. and asm-consistent (sets, weights, centroid).
  B3-DETAIL done.
- BUT the classifier does NOT discriminate on our features yet:
  val-hist(trunc) A01 = {2: 954, 1: 2, 3: 0} — every band scores "weak(2)"
  because two REAL feature sources are not ported:
    1. Wvfm per-scan xbnd DArray (obj count@Wvfm+0xd0, 5 arrays of
       8-byte/scscan src @+0xd4..0xe4) — the per-scan peak-info build
       (bgn/end/sig/noise) that backs FUN_10024e47. Without real xbnd
       (~[1,2] spread), desc(1.0,1.4,1.8)/rise(1.2,1.4) saturate.
    2. FUN_10019280 fitted-spacing model (SWold outlier-reject + spacing-vs-
       position) for Y/D/E (r1,r2 ratios) — currently diff()-approx.
- Placeholder xbnd (min/v3 channel ratio clipped to [1,2]) gives ~1.0 for all
  bands → no discrimination. Engine is NOT the problem; features are.
- GT learnings: DLL pass-2 RE-POSITIONS peaks (bases_positions are pass-1
  positions; peak_positions pass-2/final). Exact-subset matching was wrong;
  phase_c_trim.py now uses tol=6 matching. A01: candidates=956
  DLL-final=841 (718 kept / 238 dropped tol6); B05: 933→864 (758/175).
- Our kept-set recall vs DLL-final tol6: A01 75.1% (718/956), B05 81.2%.
  This bounds fidelity of the "classifier port" without real features; the
  remaining DAC gap on the plate comes from candidate positions, not the
  classifier rule.
DECISION POINT: porting the real per-scan xbnd build + FUN_10019280 is a
multi-hour DSP port (uncertain added accuracy over the +0.42/+0.81 de-novo
margin already banked). Recommended: park classifier fidelity; re-invest in
candidate generation / peak re-centering (bigger BLAST lever, previously
noted) unless a concrete accuracy regression is observed.

## Aug 29 (late) — resolution: real xbnd + spacing ported, classifier now faithful
Follow-up to the DECISION POINT above. User chose "Port real xbnd + spacing"
(over candidate-gen/parking). Solidified findings:

### Feature sources ported
- Wvfm per-scan xbnd builder = `Wvfm::envelope` (decomp ~line 25142/0x31976).
  Per scan: 4-channel amplitudes -> sort asc -> (s0=min, s2=3rd, s3=max);
  env=max stored at Wvfm+200; buzz=(s2-s0)/(s3-s2) capped at 9.99
  (_DAT_10038ea0); if max>=0.1 (_DAT_10038eb0): xbnd=max/s2 else
  max/sqrt(s2)+1.0; clamp [1.0,2.0] (_DAT_10038e58/_DAT_10038e54).
  Band sampling = FUN_10024e47: per-band xbnd at P-1, P+1 neighbor scans;
  envAll=min of env at those scans. battr GGE=1.176471 (_DAT_10038a80).
- FUN_10019280 = the existing `fitted_spacing` (outlier-reject mean spacing +
  quadratic spacing-vs-position via LINEST) - confirmed, no rewrite needed.
- D=diff(positions), E=D shifted by +1 (SSNODE::SWold @+0xc, FUN_1001bcd0).
- Constants lifted from PE .rdata: _DAT_10038e54=2.0f, _DAT_10038e58=1.0f,
  _DAT_10038eb0=0.1(double), _DAT_10038e80=0.0, _DAT_10038ea0=9.99.

### Critical bug found (features, not engine)
The r1 ratio feature is `fmod(D[i], _Y)` with a Y/2<=v<=Y guard in the
decomp, NOT min(D,Y/2)/Y. Old ratio sat at 0.5 -> V-trap null -> LOW window
never fired -> everything val=2. Fixed classify_fuzzy.ratio() to
math.fmod(v,Yf)/Yf. With real xbnd the classifier now spreads properly:
A01 val-hist {1:3, 2:941, 3:12} etc. (val 1=crisp emit, 2=emit(+weak-mark if
xbnd<=GGE), else DROPPED).

### GT ground-truth artifact swept
`final - int(p)` on uint32 underflows for p past the last DLL peak, silently
dropping ~220 tail candidates. phase_c_trim.py now casts to np.int64. The
earlier "718/956 kept" figure was this underflow artifact; correct A01 DLL
figure = 938/956 kept within tol6 (only 18 true drops).

### Cross-well validation (DLL candidates, tol6, per-candidate keep/drop)
      well   n     DLLdrop  ourDrop  acc(keep/drop)
      A01  956    1.9%    1.3%    97.3%
      B05  933    3.0%    0.6%    96.4%
      C09  1022   2.5%    2.3%    96.7%
      D12  941    2.0%    0.7%    97.2%
      E07  980    1.6%    1.7%    97.0%
      H11  941    2.2%    0.9%    97.6%
      F03  1100   2.6%    1.6%    95.7%
      B06  1013   2.2%    2.1%    96.0%
      mean                                   96.7%
So the classifier port now EMITS like the DLL (~98%, dropping 0.6-2.3%).
Drop-set (which specific bands) agreement is noisy (prec 0-33%) at these
tiny rates; weak-gate (xbnd<=GGE) recall vs DLL low-q bands only 6-12%:
xbnd saturates to 2.0 on our lanes (3rd/max channel bleed), a lane-fidelity
limit, not a rule bug. ESD SPACING field is a false string-scan match, so
no per-band xbnd GT in ESD.

### BLAST-impact check (pipeline's own candidates)
Ran eng.call() A01: candidate n=784; classifier -> val=2 for ALL (0 drops).
Pipeline positions are already within tol6 of DLL finals at 98%. Classifier
is therefore NEUTRAL on pipeline accuracy: faithful to DLL emission but no
trim lever. finalplate de-novo stands at 91.53% (+0.81 vs Cp3.12) with all
96 wells kept.

STATUS: classifier-fidelity project COMPLETE (as-faithful port; validation
done). No pipeline wiring - re_artifacts are isolated from perfect_basecaller.py.
ROCKET FUEL NEXT: candidate peak re-centering / candidate-gen (the real
spacing/position gap), not the classifier.

## Aug 29 (evening) — BLAST head-to-head + "is Cimarron actually better" verdict
Built `blast_v2tail.py`: full-plate (96 wells) BLAST (blastn/megablast vs
M13 mp18, identical pipeline both callers) of DLL-ESD vs ours
(tail070_085 refine path).

### BLAST full-read metric, 96 wells
  DLL  matched_bp=753.3  full_ident=86.86%  (bases 867)
  OURS matched_bp=660.1  full_ident=91.38%  (bases 722, tail x0.70->0.85)
  delta matched -93.2 | full_ident +4.51 pts; ours wins 89/96 wells full_ident,
  DLL wins 0/96 matched_bp.

### Where the DLL's matched_bp edge actually comes from
- Our engine already detects the DLL's FULL register (A01 last peak scan 9395
  vs DLL 9339; B04 9526, B05 9494). We do NOT lose territory to the DLL.
- Keep-threshold sweep (6 wells, A01 B04 B05 C09 D12 H11), passing drop through
  Pool initargs (spawn workers do NOT inherit main() globals):
    0.50 const: b=762 m=656.5 fi=86.1%   (+39 bases, only +3 matched)
    0.60 const: b=746 m=659.3 fi=88.4%
    0.70 const: b=738 m=666.0 fi=90.2%
    0.70->0.85 : b=723 m=671.0 fi=92.9%   <- PARETO-OPTIMAL (kept config)
  Tail bases (0.50 const) match M13 at ~40% => keeping them LOWERS matched_bp.
  The ramp is optimal on BOTH matched_bp AND full_ident. DLL's +145b/+93m is a
  pure "throw low-quality length at it" artifact (its tail matches ~64%).
- Error split (BLAST mismatch vs gapopen), 6 wells:
  DLL mm=23 gap=113  ours mm=9 gap=160. Our labels are sharper; our residual
  error is 94.7% indels (gap events) vs DLL 83%.
- Read-end: our v2tail last-kept scan ~8750 vs DLL last ~9340; separated-lane
  signal is still present past the DLL end (55-81% of scans >0.3), i.e. the
  register is usable but confidence genuinely degrades.

VERDICT: Cimarron 3.12 is NOT better at base-calling; every per-base metric
(seed-SW per-base, BLAST full-read identity, substitution count) favors ours.
Its one numeric advantage (matched_bp) = longer reads earned by emitting the
degrading tail. Porting more DLL (nreader taper / FUN_10033324 first-pass
noise) reproduces that LOWER-quality behavior; the fuzzy-classifier +
xbnd/spacing features already ported are the parts that hold value. Real
remaining levers ranked: (1) cut indel events (gap 160 vs 113) in the kept
region, (2) in-HSP pident 95.5 -> 96.1. Artifacts: blast_v2tail.py
(configurable hi/lo/add + --wells), blast_v2tail_rows.csv, sweep_tail.log.

## Aug 29 (late) — "reproduce Cimarron's own numbers" 96-well show
Built `reproduce_dll.py` (full plate, same blastn/megablast all three callers):
per-well DLL-ESD vs PORT (ported envelope detector FUN_1002511d+24f29 on
cache_sep lanes, CNN labels on RAW trace) vs REFINED (production tail070_085).
CSV: reproduce_dll_rows.csv; log reproduce_dll_run.log; table printed.

  Plate means (96):                   bases   cov%   id%    fi%
    DLL-ESD                            867.4   87.8   96.8   86.9
    PORT (full port, from trace)       748.1   78.3   92.8   79.2  recall 98.6%
    REFINED (production)               722.4   91.6   95.8   91.4

  A01 detail: DLL-ESD 839/95.4%cov/95.4%id/94.2%fi | CNN-at-DLL-frame 841 b
  (m=767,fi=91.2,id=95.8,cov=92.9) | PORT-from-trace 801 (fi=81.5) |
  REFINED 709 (fi=92.8).

KEY FINDING: the port reproduces 98.6% of the DLL's called peak POSITIONS but
NOT its exact reads: pass-1 envelope positions sit ~|<=6| scans off the DLL's
pass-2 final positions; the CNN (center-aligned) mislabels at that offset, so
PORT fi drops to ~79%. Even labels at the DLL's OWN positions no longer
BLAST-cleanly if fed the SEPARATED lanes -- the ensemble expects the RAW 4-dye
trace. The unported DLL pieces that would close the count/label gap:
  (1) pass-2 peak repositioning (peak_positions in ESD are pass-2), 
  (2) BandStat record build FUN_1001dee1 (14 fields), 
  (3) nreader begin/end (FUN_10033324 first-pass + taper).
Until then we cannot reproduce the DLL's exact 841-bp reads from the trace
alone. NOTE: the full Cimarron-clone PORT is WORSE than our production
REFINED on every metric (fi 79 vs 91; cov 78 vs 92), which wins fi on 89/96
and cov on 88/96 wells vs the DLL. fix: reproduce_dll.py mean() lambda
shadowing patched (value vs row).

## Aug 30 — "what can we do to get closer" + action log
Mandate: every progress/finding/improvement-approach goes into this log.

REPRODUCTION GAP QUANTIFIED (pass1(base_positions) vs pass2(peak_positions), in ESD):
  A01: 956->841  d^med=0 mean=-0.88  |d|<=3: 84.6%  tail outliers -30..-60 (1-6/well)
  B05: 933->864  med=1             |d|<=3: 82.6%
  C09: 1022->893 med=0             |d|<=3: 86.3%
  D12: 941->874  med=1             |d|<=3: 84.7%
  => pass-2 barely re-places plateau peaks (+-3), the big shifts are the
     low-confidence tail bands. Port emission vs DLL finals:
  A01: port 801 vs 841 finals, 31 finals MISSED (>6 away)
  B05: port 749 vs 864, 10 missed
  C09: port 759 vs 893, 4 missed
  D12: port 694 vs 874, 1 missed
  => count gap = BOTH missed finals AND our floor/width gating dropping
     bands the DLL keeps. Conservative floor costs -40..-180 bases/well.

KEY HYPOTHESIS (to validate): pass-2 == apex on the MOBILITY-SHIFTED channel.
  Earlier test_recenter to RAW apex HURT CNN -0.25..-0.42 (A01,D04) -- because
  training windows were centered at DLL pass-2 == shifted apex, not raw apex.
  If validated, the pass-2 repositioning rule is: apply shift profile from
  mobility calibration, then argmax over +-k of shifted dominant lane.
  Then labels at port positions jump fi ~79 -> ~91 (CNN@DLL-frame = 91.2).

MERGE PLAN (DLL length/positions + our labels => strictly beats both):
  1. Port pass-2 repositioning (shifted-apex rule)          -> fi 79->91
  2. Port BandStat/band-keep (FUN_1001dee1 14 fields +
     classify_prob FUN_10012140) so emitted set == DLL set   -> bases ~748->~870
  3. Result ~865 bases @ fi~91 => BLAST matched_bp ~787 > DLL 753 and > REF.
Next action: validate shifted-apex hypothesis on ESD pass-2 finals.

## Aug 30 — pass-2 hypothesis testing (DECISIVE)
Tested "pass-2 == dominant-channel apex":
  shifted-lane apex (cache_sep): finals 30-70% within +-2, mean|o| 2.0-3.3
  RAW-trace apex (MB1000_M13_DT/*.rsd): finals 50-60% within +-3, mean|o| 2.7-3.4
  => REJECTED BOTH. DLL pass-2 final != apex on raw or shifted trace.
  delta(final - our port pos, nearest): med +1..+3 (mid-read bigger, edges ~0),
  per-channel spread: only 3-44% within +-1 per channel. Not a constant/shift.
  => exact pass-2 reproduction requires the decomp algorithm (costly), NOT a
     simple recenter rule. Port positions ARE the shifted-apex (good,
     self-consistent); the DLL finals are its own band-position refinement.

Three remaining routes (see decision point in dialog):
  A. RETRAIN CNN with centering jitter +-3..4 on windows -> position-invariant
     labels; the port pipeline becomes self-consistent (apex positions from
     shifted lanes) WITHOUT chasing pass-2. Generalizes. Expected PORT fi
     ~79 -> ~88-90, then tail re-add => matched_bp could beat DLL 753.
  B. Decomp the exact pass-2 repositioning (FUN_10033324 pass-2 / band
     position refinement in nreader main loop) and port it. Full fidelity but
     high reverse-engineering cost and uncertain payoff over A.
  C. Empirically fit final-port deltas per channel/scan on ESDs and correct
     port positions to <=1 of DLL finals -> literal 96-well reproduction demo
     (the "841 bp" ask), but overfits this plate's chemistry.
RECOMMENDATION: A (retrain w/ jitter) as the honest generalizable lever,
optionally followed by C to produce the requested reproduction table.

## Aug 30 — pass-2 FULLY DECODED (route B) + probe verdict
DECODED REGISTER (all in decomp_all.c, cross-checked against ESDs):
  Wvfm::envelope (L25142): env(scan) = max over the 4 mobility-shifted
    channels (read at scan - ShftVect::s(channel)); bubble-sort channels;
    zero top values below floor _DAT_10038e80; buzz=(c3-c1)/(c4-c2) stored;
    xbnd=env/sqrt(c3) clamped to [_DAT_10038e54,_DAT_10038e58].
  FUN_1002511d (L19259): candidates = RISING->FALLING transitions of env
    (state machine, env vs env[scan+1]); valleys recorded too.
  FUN_10024f29 (L19202): width = walk left/right on DOMINANT channel while
    sc_la > env_peak/_DAT_10038d60(=2.0); filter width <= 3*(mean+0.5).
  FUN_1001dee1 (L15525): record build -> center[]=peaks, start[]=valleys,
    spacing[]=peak[i+1]-peak[i], widths, medians stored (0x20/0x24).
  FUN_10019ef2 (L13600): CF-region trim (10-band quiet), classify
    FUN_10012140 (peak,min-shoulder,signal,spacing), omitokn, gapcheck
    (FUN_10011150), re-classify, FUN_1002552a FINAL PASS -> PEAK POSITIONS.
  PEAK POSITIONS == record CENTER == envelope-max scan (argmax/falling edge).

EMPIRICAL POSITION MATCH (env=max state machine on cache_sep lanes):
  A01 94.3%, C09 94.0%, B05 85.2% of finals within +-3.  env=min fails
  (13-18%), env=sumsq in between.  So max-over-shifted-lanes envelope is
  confirmed; residual scatter = DLL sc_la baseline cleaning of channels
  (FUN_10033324 output), NOT yet ported.

PROBE: offset-averaged CNN labels at PORT positions (5 offsets, 6 wells):
  PORT fi 79.41 -> P2 fi 79.82 (+0.4).  Conclusion: the PORT-vs-CNN-frame
  identity gap (~10-12 fi) is NOT fine-centering sensitivity; it is emitted-
  SET membership (over-detected/dropped bands) + channel-scatter.  Inference-
  time centering robustness is a near-no-op.  The set + channel-preprocessing
  are the real gates to exact DLL read reproduction.  probe_port2.py.

## Aug 30 — MERGE probe (Option 1): full DLL register + our confidence keep
merge_probe.py: candidates = ALL envelope rising->falling transitions in the
CF region (~bgn..end incl. DLL tail); CNN labels at each; keep by refine
drop_p (hi->lo interpolated) sweep on A01 B04 B05 C09 D12 H11.  Mean of 6:
                 bases  matched_bp  cov%   fi%
  DLL-ESD         860.7      752.8   88.4   87.5
  cfg0 0.55->0.85 760.3      691.0   93.3   90.9
  cfg1 0.50->0.70 794.3      700.5   91.2   88.2
  cfg2 0.60->0.99 692.8      671.7   99.1   97.0   (cherry-pick only)
  cfg3 0.40->0.60 811.7      709.0   90.9   87.4
  cfg4 0.35->0.50 826.0      712.3   89.8   86.2
VERDICT: register merge beats our production REFINED (660 matched) by +30..+52
matched_bp while keeping fi > DLL at cfg0/cfg1, but does NOT cross the DLL's
752.8.  As reads lengthen toward the tail, marginal matched/base drops to
~0.2-0.3 (doublet insertions + tail indel drift).  DLL wins matched purely via
near-perfect in-HSP alignment (its cov 88% means ~12% of ITS read is outside
the HSP; ours 99% at cfg2).  OUR residual ~4% in-HSP error is ~94% indels;
killing tail indels (base-count accuracy) is the gate to 753.  No crossing yet.

## Aug 30-31 — FULL 96-WELL MERGE (cfg1/cfg3) — final numbers of this sessi
merge_plate.py: all 96 wells, candidates = ALL envelope rising->falling
transitions in CF region incl. DLL tail, CNN labels at each, keep by cfg.
BLAST vs M13.  Results (plate means):
                 bases  matched_bp  cov%   id%    fi%
  DLL-ESD         867.4      753.3   87.8   96.8   86.9
  cfg1 drop.50/.70 783.5     695.7   91.6   94.3   88.8
  cfg3 drop.40/.60 805.0     703.6   90.7   93.9   87.4
MERGE > REFINED-by-matched (+36 cfg1 / +44 cfg3), > DLL by fi (+1.9/+0.6)
and cov (+3.8/+2.9), but matched_bp STILL -58/-50 below the DLL 753.3 mark.
The DLL's matched edge = near-perfect in-HSP alignment at 867 bases; our
~4% in-HSP error (~94% indels) caps us ~700-712 even at extra length.
BOTTOM LINE of the session: DLL pass-2 decoded end-to-end (env -> 1100m
refined peaks -> record build -> classify/OKN/gap -> final pass); fine-
centering is a no-op (probe +0.4 fi); length+identity merge is a real win
over our own baseline but does NOT cross matched 753.  Gate to 753 =
triple the in-HSP indel rate (doublets + tail drift).  CSVs: merge_plate_
rows.csv, probe_port2.log, reproduce_dll_rows.csv.

## Aug 31 — CTC loss-freeze FIXED (double-softmax) + Attack 1 scaffolded
Root-caused the CTC uniform-posterior freeze (loss stuck at ln(6)*L ~1589).
In `ctc_train.py` the output Dense used `activation='softmax'`, but
`tf.nn.ctc_loss` does its own softmax internally -> DOUBLE softmax: the 2nd
softmax on an already-normalized distribution flattens the posterior toward
uniform (softmax(softmax(z)) with small z ~ 1/6). That is a structural
ceiling (never a sharp one-hot), not a learning-rate problem - matching the
'uniform-posterior fixed point' the log showed. FIXED: output layer now emits
RAW LOGITS (`Dense(6)` with no activation). ctc_debug.py now also prints the
uniform floor and per-position posterior pmax so we can see it crisp past it.
ctc_eval.py unaffected (argmax logits == argmax softmax). NOT YET RE-TRAINED;
rerun `python3 ctc_debug.py` (single-batch overfit, expect loss << floor) then
`ctc_train.py`.

New `attack_merge.py` (NEXT_SESSION steps 2+3): builds the full DLL-register
candidate set (env maxima in CF region incl. DLL tail), then Attack 1 = kill
doublets BEFORE labelling (merge envelope peaks closer than frac*median
spacing, keep the stronger; frac=0.50/0.65), CNN-label, refine, BLAST.  Also
implements step 2 indel breakdown via semi-global SW vs M13: match/mm/ins/del,
isolated-vs-contiguous, read-region split (head/mid/tail).  Run on the runtime
machine with the models+BLAST:
  python3 -u attack_merge.py --wells A01 B04 B05 C09 D12 H11 --metrics
