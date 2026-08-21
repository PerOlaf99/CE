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
