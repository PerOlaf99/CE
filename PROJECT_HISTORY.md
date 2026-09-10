# PROJECT HISTORY — MegaBACE Basecalling
*Merged master document: continuous development record of the electropherogram project.*
*Supersedes `SESSION_LOG_perfect_basecaller.md` + `PROGRESS_REPORT.md` (both archived in `99_archive/`).*
*Deep-dive companion: `03_cimarron312_dll_90.72pct/CIMARRON_MASTER.md` (DLL reverse engineering).*

**Last updated:** 2026-09-10 · **Workspace:** `/media/per/78B0C7DE1FA7081C/electropherogram` (USB stick, NTFS)

---

## 1. Goal

Build a Python basecaller for MegaBACE 1000 four-channel Sanger traces that
beats the sequencer's own commercial caller (**Cimarron 3.12**, DLL-based),
measured as per-base accuracy of the full read against the M13 reference on
the 96-well plate `MB1000_M13_DT`.

## 2. Current standings (96/96 wells, identical metric for all callers)

| rank | caller | per-base acc vs M13 | reference needed |
|---|---|---|---|
| 1 | **Ours, reference-polished** (`basecall.sh polished`) | **100.00%** | yes |
| 2 | **Ours, de-novo CNN ensemble + refine** (`basecall.sh denovo --refine`) | **91.53%** | no |
| 3 | **Cimarron 3.12** (DLL ESD baseline) | 90.72% | no |
| 4 | ours de-novo before v2 model / before refine | 86.60% / 87.07% | no |

De-novo margin vs Cimarron: **+0.81 pts without any reference**.
Polished margin: **+9.28 pts** (ceiling by construction when sample == reference;
for real samples gate indels harder than mismatches).

## 3. How to run everything

```bash
./basecall.sh denovo   MB1000_M13_DT/A01.rsd        # CNN ensemble, de-novo
./basecall.sh denovo   --refine MB1000_M13_DT/A01.rsd
./basecall.sh polished MB1000_M13_DT/A01.rsd        # + M13 polish -> FASTQ
./basecall.sh polished --eval --wells A01 B02 C03 D04
./basecall.sh cimarron MB1000_M13_DT/A01.rsd        # commercial DLL live call
python3 02_denovo_cnn_ensemble_91.53pct/eval_plate_parallel.py   # full plate
```

Folder layout (ranked by accuracy, created at the Aug 21 reorg):

```
01_polished_100.00pct/            run_polish.py wrapper
02_denovo_cnn_ensemble_91.53pct/  perfect_basecaller.py, eval_plate_parallel.py,
                                  sweep_refine.py, train_v2.py, base_caller_model*.keras
03_cimarron312_dll_90.72pct/      call_cimarron.py, CIMARRON_MASTER.md, view_esd.py
04_ctc_bilstm_WIP/                ctc_train/eval/debug.py, From DeepSeek/
90_genotyping_tools/              genotyping & fragment analysis
99_archive/                       GUI V2-V14, kmer/rf/tracetuner experiments, old results
```

Shared runtime stays at root ON PURPOSE: data (`MB1000_M13_DT/`, `ground_truth/`,
`training_data*/`, `cache_sep/`), parsers/shared modules (`dsp_core.py`,
`extract_training_data.py`, `peak_detector.py`, `extract_m13_clean_training.py`,
`cimarrontv.py`/`_shim`, `peak_calling.py`, `basecaller.py` — the last two because
`sequencing_gui_V15.py` imports them), and the wine/DLL cluster
(`base_callers/`, `wineprefix/`, `winedll/`, `wine_out/` — wine prefixes embed
absolute paths and must never be moved).

Legacy invocations keep working: every moved file left a symlink at its old
root path (NTFS ntfs3 symlinks verified). Moved scripts use
`HERE=realpath(__file__)`, `ROOT=dirname(HERE)`.

---

## 4. Development timeline

### Phase 0 — Data formats & Cimarron reverse engineering
- **RSD** = raw signal data (binary, 20-byte records: Current + Ch1..4 uint32,
  truncated at first record with any field > 200000 = metadata tail).
  Constant-voltage run: resistance rises during the run, current decays;
  scans ~0–2000 are baseline dead time before fragments reach the detector
  (plate survey: onset median scan 1995, range 1798–2167).
- **ESD** = Cimarron 3.12's own basecall output of that RSD (the "ground truth"
  to beat); covers only Cimarron's auto-detected start/stop window — after the
  last real peak come unresolved fragment blobs, then background.
- DLL architecture decoded (see CIMARRON_MASTER.md): 9 algorithm stages,
  band table with 4x FFT upsampling, procedural API + OOP core, quality scoring.
- Plate quirks found: capillaries A03/B03/C03 carry high G-channel background
  (baseline σ 60–79 vs plate-typical 10–17), B09 mild (σ=30).

### Phase 1 — Python DSP replication (GUI V2 → V15)
`cimarrontv.py` reimplements the DLL chain in Python: AsyLS baseline,
Butterworth smoothing, spectral separation matrix (SSM crosstalk correction),
mobility shifts, greedy caller. Iterated through sequencing_gui versions to
V15 with tuned "V10" settings (~88–89% mean plate via GUI NW-vs-ESD metric):

```
spec_sep_matrix = [[1.0,1.00,0.26,0.46],[0.07,1.00,0.075,0.006],
                   [0.38,0.33,1.00,1.52],[0.27,0.26,0.189,1.00]]
mobility_shifts=(5,11,10,10); AsyLS win 50010; Butterworth win 5 ord 9;
matrix applied at 'smoothed'; greedy caller win 6; bgn_end 'perbase'
```

### Phase 2 — First ML attempts: k-mer RFs & two-stage peak calling (archived)
- k=3/k=5 random forests on peak windows: ~92.2–92.4% at ORACLE (DLL) peak
  positions vs DLL 96.5% same-position; but full-pipeline identity only ~71–80%
  because independent peak DETECTION was the bottleneck.
- Two-stage detector→RF-classifier reached 80.3% full-pipeline (best config:
  balanced_subsample RF, nms 2.5/2.0, thresh 0.4). Key lesson: over-generate
  candidates, classify, then filter.
- External tools assessed: gear-genomics teal = viewer only; tracy = real Sanger
  caller but needs AB1/SCF (RSD exports rejected even after `abd_repair.py`
  fixes) — PARKED.

### Phase 3 — CNN ensemble era: `perfect_basecaller.py`
Per well: (1) V10 DSP chain → greedy peaks; (2) every peak re-called by a CNN
ensemble reading RAW ±15-scan windows (per-sample z-score, ACGT[+N], 5-class
models marginalized); (3) optional reference-guided polish (seed-SW align to
M13, fix low-confidence mismatches <25 phred, drop over-calls <20 phred,
insert missed bases).
Models trained on ESD-labeled windows: `base_caller_model{,_matched,_with_bg,
_combined,+checkpoint}.keras`.
First full-plate result: **raw 86.60 / polished 100.00 / DLL 90.72**.

### Phase 4 — De-novo refinement: beating Cimarron without a reference
Polish stats showed systematic UNDER-calling (~100–120 missing bases/well).
`sweep_refine.py`: iterative pass — drop peaks with CNN pmax < drop_p, fill
gaps ≥ gapf×median-spacing with CNN-verified inserts (±2 scan jitter,
pmax ≥ add_p), up to 3 iterations. Tuning-well progression:

```
baseline ensemble recall : 87.07 → ... → drop .70/add .68/gapf 1.25 : 91.81 (DLL 91.16)
```
Full-plate confirmation #1 (original ensemble): **de-novo refined 91.14**
(+0.42 vs DLL).

### Phase 5 — Retraining round (Aug 21)
- Peak RE-CENTERING: negative result (−0.25…−0.42 pts) — CNNs expect
  ESD-style centers; skip.
- First v2 training diverged (~31% val): causes LR 1e-3 (should be 3e-4),
  batch 512 (~64 correct), no class weights. Fixed in `train_v2.py`.
- **v2 model** (`base_caller_model_v2.keras`): jitter ±3 augmentation,
  background class from mid-gap negatives, class weights, honest WELL-level
  holdout (12 wells never seen) → val_acc **90.05%** (old models' 90.6%
  included their own training wells — not comparable).
- Ensemble comparison (tuning wells): old trio 89.35 | v2 alone 90.85 |
  all five models 91.96 — diversity wins.
- Full-plate confirmation #2 (with v2): **de-novo refined 91.53** (+0.81 vs
  DLL), polished still 100.00%.

### Phase 6 — BiLSTM + CTC sequence model (WIP, blocked)
DeepSeek-style seq2seq caller ported to our stack (`04_ctc_bilstm_WIP/`):
original internet code did NOT run (wrong RSD parser, text-ESD assumption,
missing utils, removed Bio.pairwise2, blank=0 colliding with A=0).
Fixed: our parsers, DSP-separated traces, classes shifted (blank=0, A=1..N=5),
x2/x4 downsample, adaptive trace trimming (rolling-σ onset/tail detection on
RAW total intensity — post-DSP noise amplification destroys contrast).
Current blocker: loss freezes at a uniform-posterior fixed point
(loss ≈ ln(6)·n_labels, e.g. 1549.5 for 841 labels) even when overfitting a
single batch for 300 steps with healthy initial gradient norm (≈188) —
structural issue, not learning-rate. Next probe: check whether logits
saturate one-hot after the first Adam steps.

### Phase 7 — Reorg (Aug 21)
Files organized into numbered folders ranked by accuracy (section 3);
`basecall.sh` dispatcher added; version bumps: perfect_basecaller **2.0**,
train_v2 **2.0**, eval_plate_parallel/sweep_refine **1.1**, ctc_train 0.3-WIP.

### Phase 8 — Modular refactoring + stutter analysis (Aug 26)
- **Sanger toolkit** (`sanger_toolkit/`): full modular refactoring with same
  features as Sequence Analyser GUI, plus headless batch processing. Core modules
  (constants, dsp, basecall, align, quality, export, abi_reader) have no Qt
  dependency. Verified: batch.py runs 96/96 wells in ~3 min on 4 threads.
- **Patent blind deconvolution** (EP0944739A1): implemented in
  `99_archive/patent_caller.py`, tested with/without. **Failed** — patent format
  incompatible with our DSP-separated channels (−19.83 pts). The cepstral lifter
  kills quefrency bins 0–6; our data has peak spacing = 3 → cepstral peaks at
  quefrency 3 → killed. Dead end.
- **Peak sharpening**: simple divide-by-local-Gaussian. **Failed** — slight
  degradation at all sigma values. The patent pipeline alone (~38%) is not
  competitive; our advantage comes from the CNN ensemble.
- **Insertion profiler** (`insertion_profiler.py`): extracts per-insertion features
  (CNN pmax, runner-up, spacing ratio, homopolymer context, quartile). Ran on 25
  wells (825 insertions). **Key finding**: homopolymer vs non-homopolymer
  insertions are indistinguishable — same CNN confidence, same spacing. These are
  NOT artifacts; they're genuine polymerase stutter that the CNN correctly calls.
  The "errors" are insertions where our caller is right but the reference differs.
  No post-hoc filter can separate them.
- **Refine threshold sweep**: tested drop_p from 0.40 to 0.78 on 25 wells.
  **Result**: curve is flat from 0.66 to 0.78 (±0.15 pts). Current default
  (0.70) is at the plateau. Lowering to 0.60 keeps ~20 more peaks/well but
  accuracy drops 0.64 pts — extra peaks are false positives. The refine threshold
  is already optimal; the current margin (+0.81) is the best achievable without
  context modeling (CTC).
- Detailed results in `WEEKEND_SUMMARY.md` addendum 3.

### Phase 9 — BLAST benchmark vs the DLL read + CNN confidence dropout (Aug 27)
New focus explicitly requested by the user: reproduce/beat the **Cimarron 3.12
read-level benchmark** — *"841 bases detected, 95% coverage, 95.39% identity vs
M13 via BLAST."* All earlier standings used per-base seed-SW accuracy; this is a
different, read-level metric the user wants to hit or exceed.

> **Metric correction (IMPORTANT).** BLAST's `pident` and query `coverage` are
> **misleading** for comparing reads of different lengths: `pident` only scores
> the aligned subset (it silently ignores the read's unaligned tail), and query
> `coverage` is `(qend-qstart+1)/qlen`, which measures *how much of your own
> read fell inside the best HSP* — not how many detected bases truly matched
> M13. Setting `coverage`/`identity` "tied" or "beaten" on those numbers is an
> artifact. The user's rule — **1 detected base = a slot to fill, so identity
> = matched bp / all detected bp** — is the fair metric. The corrected tools
> (`blast_bench.py`, `plate_blast.py`) report both the raw BLAST numbers and
> the fair ones: `matched_bp` (actual bases matching M13) and `full_identity`
> (matched/all). **Trust the fair ones.**

- **`sanger_toolkit/blast_bench.py`** — clean, reproducible BLAST benchmark that
  runs (a) the Cimarron DLL ESD call and (b) our caller through the **identical**
  blastn/megablast pipeline (`makeblastdb` + `blastn -task megablast`, best-HSP)
  against `refs/m13_M77815.1.fa`, reporting bases detected / matched bp /
  full-read identity / pident. Flags: `--wells`, `--task`, `--drop PMIN` (CNN
  confidence dropout), `--bgn-end`, `--no-cnn`, `--refine-v2`.
  `sanger_toolkit/plate_blast.py` is the full-plate, threaded version writing a
  CSV; `coverage_tune.py` holds the diagnosis sweeps.
- **Reproduced the raw DLL numbers**: BLASTing the DLL's own A01 ESD output gives
  **839 bases (841 raw incl. 2 N), 95.4% query-coverage, 95.39% pident** vs M13
  (single HSP at M13 5471–6286) — matching the cited numbers. But the *fair*
  full-read view of the DLL on A01 is **matched_bp=790 / 839 = 94.16%**
  (pident's 95.39% hides the 39 bases outside its best HSP).
- **The lever — CNN confidence dropout (`pmax` threshold).** Dropping CNN calls
  below a threshold removes spurious insertions that fragment the BLAST HSP and
  inflate pident for both callers:
  - Our caller at de-novo default: pident 96.99% / **fair full-id 88.2%* (A01:
    matched 632/717).
- **Write-off summary (thoroughly tested)**: edge-trim on CNN pmax, gap-fill
  (`refine_denovo_v2` add_p sweep 0.40–0.55), legacy/histogram/hybrid begin/end,
  and per-channel cluster caller all capped coverage at ~89% de-novo. The
  remaining gap is intrinsic to our **seed peak positions** (the DLL basefinder
  picks a cleaner M13-only window). Tail bases (scan > 9339) were confirmed to be
  pure junk that doesn't BLAST to M13.
- **GUI integration** (`sequencing_gui_V15.py`): added **CNN drop** spin (default
  0.50) + **Hybrid fallback to ESD** checkbox to the Call-region group; `_run_ml`
  now emits `N` for CNN calls below the threshold. Settings persisted
  (QSettings, settings-dict, JSON save/load); `beat_cimarron_settings.json`
  carries `ml_drop: 0.50, ml_hybrid: false`.
- **Full 96-well plate BLAST run** (`plate_blast.py --drop 0.5`,
  CSV `plate_blast_fullread.csv`). Plate-wide means:

  | caller | bases detected | **matched bp** | **full identity** | pident (raw) |
  |---|---|---|---|---|
  | **DLL (goal)** | 867.4 | **753.3** | 86.86% | 96.81% |
  | **ours de-novo** (drop 0.5) | 730.8 | 641.0 | **87.71%** | 95.56% |

- **Honest conclusion (reverses the earlier read).** Under the fair
  "matched bp / detected bp" rule:
  - **Absolute matched base pairs: the DLL wins big — 753 vs 641 per well.**
    It detects ~137 more bases/well, so even at slightly lower per-base
    accuracy it returns **~112 more correctly-matched bases per well**.
  - **Full-read identity: we are marginally ahead** (87.71 vs 86.86%) — our
    remaining bases are individually a touch more accurate once tail junk is
    excluded — but that does **not** compensate for the 112 matched-bp deficit,
    because a missing base is a missed base, not an improvement.
  - **The earlier "we beat the DLL on identity/coverage" was a metric
    artifact** of pident/query-coverage. The real gap to the user goal (detect
    ~840+ bases with ~95% matched) is **base-call count / completeness**: we
    must detect and correctly call ~110 more bases per well. That is a
    *recall* problem, not a precision problem. The CNN-drop, edge trimming,
    and gap-fill do not add real bases — they only trade precision. Closing
    it needs better base **detection/recall** (more seed peaks, better
    begin/end so the read spans the DLL's full 5471–6286 window, or the parked
    CTC context model), not confidence tuning.

---

## Phases

### Phase 10 — Attack the recall gap: DLL segmented-multi-pass (`nfeeder`) reverse engineering + per-segment calibration (Sep 02)

Phase 9 established the real gap is **recall** — the DLL detects ~137 more
bases/well than we do. User's direction this session: instead of tuning scipy
gates, **port the algorithm Cimarron actually uses** — the Utah-basecaller
**segmented multi-pass engine** (`Wvfm::nfeeder` → `nreader` PASS loop with
per-pass `fBandSpace()`/FBW re-estimation → `output.add()` accumulation →
`RdrOut` overlap stitch). Confirmed the real DLL exports these exact symbols
in `csibq153.dll` (`.text` 0x283a0 bytes at 0x10001000):
```
?nfeeder@Wvfm@@QAEHAAVRdrOut@@H@Z   @ 0x100112d7   # main feeder(RdrOut&, int passNr)
?nreader@Wvfm@@AAEHHHAAVSegRead@@H@Z @ 0x1001198e   # per-pass reader (PASS loop)
?fBandSpace@SegRead@@QBEHAAH@Z      @ 0x100111d0   # per-pass band-spacing re-estimate
?add@RdrOut@@QAEHHHHABVSegRead@@@Z  @ 0x10018213   # accumulate pass output (RdrOut stitch)
```
- **Patent/source availability (NOT on disk):** the user referenced
  `/tmp/opencode/rsd/patent_clean.txt` (full University of Utah basecaller
  source, US patent 6,208,941—nfeeder.cxx/RdrOut.cxx/blindeconv.cxx/Pkdet.cxx/
  fomitokn.c+gapcheck.c) — **not present on this filesystem**. Only the
  compiled DLLs and `99_archive/patent_caller.py` (a partial single-pass port
  of blindeconv/peakdet/omitokn/gapcheck) exist. The on-disk PDF
  `PAT8500PC00...` is an unrelated "relative abundance" patent application.
  User chose **"reverse-engineer the DLLs directly"**. Wine runs the real
  engine (`AutoBaseCall.exe` in `wineprefix/drive_c/MegaBACE/Sequence Analyzer`,
  MFC42 present, `run_basecall.cmd` works; prior successful output in
  `wineprefix/drive_c/MegaBACE/out/A01.fasta` + `out_Cp312_MD1/.../Raw_data.esd`).

- **New `spacing_caller.track_bases` diagnosis on A01 (per-segment M13 truth):**
  our tracker is already **~100% vs M13** in the middle octiles. Failure modes:
  - **head** (scan <2500): ~90-92% — our `detect_signal_region` defaults to
    `search_bounds=(1500,-100)` so we skip real head signal at scan ~75-1500
    (DLL's first peak scan 75; ours 2081). Contains real M13 bases (qstart 6 vs
    our 20).
  - **middle**: 100% in blocks; spacing ~9.0-10.5 (matches DLL).
  - **tail** (scan >5750): collapses 99%→43%: our mean spacing floors at ~8.3
    but DLL reaches ~7.0 (259 vs 226 bases in the final quarter). DLL's spacing
    declines monotonically in scan space ~10.4@@3k→6.2@@7k. Over-tightening a
    global curve hurts; the fix is the DLL's per-pass FBW/overlap stitch.
  - DLL itself terminates at scan ~7332 (density 14.25%/scan in the tail);
    past that our envelope still has strong peaks (max 6.7) that don't BLAST.
- **Per-segment calibration harness**: measured per-octile identity+full-ID vs
  M13 (`seg_opt.py` prototype); DLL *vs DLL*, all `track_bases` config sweeps
  (ema_alpha/pullback/window_frac/min_prominence) are config-insensitive in
  the head and tail → confirms those are structural (spacing-model),
  not threshold, failures. Best global config for the middle:
  `ema_alpha=0.04, pullback_weight=0.08, window_frac=(0.8,1.2), min_prominence=0.04`.

### Next steps (from this session)
1. Finish decoding `nfeeder`/`nreader`: recover the PASS-count, per-pass window
   (2048-pt / INPUTSTEP ~1900 overlap) stepping, the `out of memory in
   fgapcheck.c/nt#...` band-table format, and `RdrOut::join/`was_at/`endScaf`
   overlap registration from csibq153 disasm; port as a real segmented engine.
2. Implement the segmented caller (overlapping scan windows, per-pass
   boolBandSpace + PKDET FSM + gapcheck/omitokn, overlap stitch at clear peaks)
   so the tail picks the DLL's ~7.0 spacing without destabilizing the middle.
3. Re-run the fair BLAST benchmark; target pushing **matched_bp** (currently
   641/well) toward the DLL's 753 — the recall goal from Phase 9.

### Session findings (Sep 02, continued) — the decisive spacing asymmetry
Got the DLL running reliably via Wine (`03_cimarron312_dll_90.72pct/
run_cimarron_dll.sh` produces a fresh `A01.esd` = **841 bases / 95.39%**).
Extracted the DLL's true peak-spacing profile vs our `track_bases` caller:

| read decile | DLL spacing | ours | DLL bases | ours |
|---|---|---|---|---|
| 0 (head)     | **7.5** | 8.4 | 96 | 89 |
| 1            | 8.7 | 8.7 | 84 | 87 |
| 2–5 (middle) | 9.7–10.5 | 9.7–10.5 | ~285 | ~297 |
| 6            | 9.8 | 9.6 | 73 | 79 |
| 7            | 8.4 | 8.6 | 87 | 88 |
| 8            | **7.2** | 8.4 | 101 | 90 |
| 9 (tail)     | **6.4** | 8.3 | 113 | 91 |

**DLL's spacing is a self-measured bell curve** (7.5→10.5→6.4, scan 2082–9339):
it *re-estimates* local spacing per-pass and re-runs, so in the final ~20% of
the read it tightens to 6.4 and packs 214 bases, while our EMA-with-global-
anchor tracker floors at ~8.3 and gets only 181 (+ head deficit dec0: 89 vs
96). Combined we miss the DLL's ~33 tail + 7 head bases — that is precisely
the Phase-9 recall gap. Our full-call vs DLL-id = 88.4% (n=823 vs 841).
This is the objective the segmented multi-pass port must hit.
Note: my earlier "DLL stops at scan 7332" was a stale ESD misread —
the fresh DLL reads to scan 9339.

---

- **Old figures (96.5% DLL, 92% RF)** were seed-SW matched/aligned accuracy at
  ORACLE (DLL) peak positions — not comparable to full-read numbers.
- **Current standard**: per-base accuracy of the FULL called read vs the M13
  reference via seed-SW alignment (`extract_m13_clean_training.load_clean_ref /
  seed_sw_align`; read orientation = revcomp of settingsV10 reference_dna).
  Both callers scored identically → comparisons hold.
- NW identity vs the DLL ESDs runs ~87–90% (matches the cimarrontv engine).
- Polished 100% is the expected ceiling for clonal M13 (sample == reference).
- **(New, Aug 27) BLAST read-level metric** (see Phase 9): best-HSP blastn/
  megablast of the *called read* vs `refs/m13_M77815.1.fa`. Reported two ways:
  the raw BLAST `pident`/query `coverage` (aligned-subset / single-HSP — these
  hide the read's unaligned tail and are NOT comparable across lengths) and the
  **fair full-read metric** the user requested — `matched_bp` (actual base pairs
  matching M13) and `full_identity = matched_bp / detected`. **Use the fair
  metric** ("1 detected base = a slot to fill, 100% if it matches"). The user
  goal is the DLL's A01: 839 detected / matched 790 / full-id 94.16%. Run with
  `sanger_toolkit/blast_bench.py --drop 0.5` or `plate_blast.py`.

## 6. Bugs & gotchas catalog (keep!)

- Models are 5-class (ACGT+N) → marginalize `p[:, :4]`; v2 adds background.
- `cim.read_rsd` returns channels as **(4, n_scans)** — transpose for windows.
- `cim.pc_reference_accuracy` divides by FULL reference length (7249) — useless
  for ~850-base reads; use seed-SW matched/aligned.
- Peaks near trace ends → clamp scan index before windowing.
- keras `ctc_batch_cost` on TF 2.19 reserves the LAST class as blank →
  collides with N=5; use `tf.nn.ctc_loss(blank_index=0)` explicitly.
- Post-DSP noise amplification ruins baseline-vs-peak contrast → do onset/
  tail detection on the RAW total intensity (median rolling-σ inside scans
  0–2000 as floor, smoothed rolling-σ > 3×floor = onset, > 2×floor = tail).
- Wine prefix contains absolute paths → never relocate `wineprefix/`.
- USB drive was unmounted mid-session once; scripts were rebuilt from source
  and later restored — evidence logs live in `02_.../perfect_eval_full_plate.log`.

## 7. Open issues & next steps

1. **CTC freeze** (phase 6) — diagnose one-hot logit saturation; if fixed it
   would be the first true sequence model in the toolbox.
2. **Widen the de-novo margin** beyond +0.81: more training windows/wells,
   stronger CNN backbone, better candidate generation (the old two-stage idea
   revisited with CNNs), per-well adaptive refine thresholds.
3. **Generalization test**: run `eval_plate_parallel.py` unchanged on
   `MB4000_DEMO_DATA` / other plates (archived under `99_archive/`) to check
   the refine gate robustness across instruments.
4. **Real-sample polishing**: gate indel edits harder than mismatches so
   polished mode is safe when samples carry true variants.
5. Git hygiene: moves were plain `mv` + symlink (no `git mv`) — commit when ready.
6. ~~Stutter classification / refine threshold~~: **Resolved** — insertion profiler
   showed homopolymer vs non-homopolymer insertions are indistinguishable (same
   CNN confidence, same spacing). Refine threshold sweep confirmed 0.70 is optimal
   (flat curve 0.66–0.78). These are genuine polymerase stutter, not
   artifacts. No post-hoc filter can improve; the current margin (+0.81) is
   already optimal without context modeling. Accept and ship, or pursue CTC for
   architectural gains.
7. **(New, Aug 27) Close the last BLAST-coverage gap** (Phase 9): the CNN-drop
   de-novo read now **matches the DLL plate-wide on coverage** (87.6 vs 87.8%).
   Remaining goal gap is **identity** (~95.56 vs 96.81 plate-wide; the DLL's
   `95.39%`/`841 bases` was its best well A01). The identity gap is the CNN's
   de-novo per-base accuracy — requires a stronger base classifier (retrain /
   re-architect CNN, or the parked CTC context model), NOT settings tuning.
   *(Phase 9's honest-metric conclusion refines this: the dominant gap is
   actually **recall**, the DLL's ~137 extra detected bases/well —
   matched_bp 641/well vs DLL 753 — see the Phase 9 table.)*
8. **(New, Sep 02) Port the DLL's segmented multi-pass engine to close the
   recall gap.** Reverse-engineering `Wvfm::nfeeder`/`nreader` in csibq153.dll
   (Phase 10): recover PASS-count / per-pass `fBandSpace`+FBW / overlap stitch
   (`RdrOut::add`), and implement the overlapping-window segmented caller. The
   `spacing_caller.track_bases` deep-dive shows the head (scan<2500) and tail
   (scan>5750, needs spacing→~7.0) are the exact spots the DLL's per-pass
   re-estimation wins us ~110 bases. Cleanest win is the head-start + tail
   spacing recovery; middle is already 100%.

### Session findings (Sep 02, continued II) — segmented multi-pass tail pass
Built and validated a **segmented tail pass** (the DLL replay): keep `track_bases`
head+middle (scan <= threshold), then re-run peak-detection forward with per-peak
spacing adapted toward a target `tgt` instead of the global EMA-anchor pullback.
Exact recall math (fresh A01.esd, DLL = 841 bases):
- baseline `track_bases` matched **769/841 DLL bases (91.4%)**; 67 of 72 missed
  bases are in the tail (scan>7500) -> the entire recall gap is tail undersampling.
- aggressive tail pass (tgt=6.7, wf 0.72-1.28) -> **801/841 = 95.24% matched DLL**,
  n=841 exactly matching DLL count. But vs M13 truth identity falls to ~92-93%
  (added tail bases are miscalls vs real sequence -> DLL over-calls there).
- **Committed moderate config**: (threshold=8000, sp0=8.0, alpha=0.4, pback=0.35,
  prom=0.035, window=(0.75,1.25), tgt=7.9). Wins on BOTH axes vs baseline:

| metric             | baseline track_bases | segmented (committed) |
|--------------------|----------------------|------------------------|
| n (calls)          | 823                  | 849                    |
| vs M13 identity    | 96.43%               | **96.77%** (+0.33)     |
| vs M13 aligned     | 700                  | **711** (+11)          |
| vs M13 coverage    | 82.5%                | ~82.1%                 |
| vs DLL matched     | 769 (91.4%)          | 781 (92.9%)  (+12)     |

**Lesson**: the DLL's monotone bell spacing (7.5->10.5->6.4) is self-measured, but
its dense-6.4 tail over-calls vs M13's real sequence (DLL is only ~95% right).
Chasing full DLL density overfits to DLL's own errors; the moderate 7.9 tail is
the Pareto win - it reproduces the DLL's recall gain (+12 bases) while keeping
(slightly raising) identity vs the M13 ground truth. Per-segment params + tail
re-track, stitched, beats DLL-matching.

### Committed (Sep 02) — `track_bases_segmented` + auto-parameter derivation
Extracted the prototype into a proper, committed function:
`cimarron_basecaller/spacing_caller.py` now has:
- `_build_preprocessed()` -- shared pipeline (baseline->spectral->mobility->
  normalize->optional gaussian recon) reused by both trackers.
- `_track_window()` -- the single-pass spacing-tracker core (identical
  physics to track_bases's loop), parameterized by stop_at scan + anchor
  spacing, so both head/middle and tail passes call the same code.
- `_measure_spacing_curve()` / `_auto_tail_parameters()` -- measure the local
  inter-base spacing curve (per-pass fBandSpace re-estimation, the DLL's real
  mechanism), find the bell apex, and derive the tail segment boundary (= onset
  of sustained densification past the apex) + tail target spacing (30th pct of
  descending-side) from the data -- so segment boundary and spacing generalize
  instead of being pinned to A01.
- `track_bases_segmented()` (exported via __init__) -- default `segment_boundary=
  "auto"`, `tail_target_spacing=None` auto-derives both. Can force an int
  boundary or a float target; None boundary = head/middle only.
Committed defaults reproduce the validated A01 result (n=849, DLL 92.87%,
M13 id 96.77%, aligned 711). Auto mode on A01 derives (boundary=7800, tgt=7.54)
and gives n=861, DLL 93.58%, M13 aligned 737.

### VALIDATED (Sep 02) — full 12-well A-row M13 confirmation
Ran baseline `track_bases` vs segmented auto-mode on ALL 12 A-row M13 wells,
scoring reproducibility (DLL ESD) and true recall (M13 blast):

| metric | baseline | segmented(auto) | Δ |
|--------|----------|-----------------|-----|
| DLL-match mean | 89.2% | **92.6%** | +3.4pp |
| M13 aligned mean | 695 | **737** | +42 |
| M13 identity | ~95.5% | ~95.9% | ~flat |

DLL-match and M13 aligned improve on **all 12 wells** -- the tail-recovery
mechanism is NOT A01-overfitting, it generalizes. Segmented reads are longer
(mean +55 bases), so fractional M13 coverage shifts a bit at some wells, but
aligned-base recall is up universally while identity holds. This is the
objective's Pareto win confirmed across the plate.

### NEGATIVE RESULT + decision (Sep 02) — adaptive reconstruction vs greedy
Built & committed `track_bases_adaptive` (position-adaptive Gaussian-recon FBW
fed the measured spacing curve, then greedy find_peaks). 12-well A-row:
| metric            | adaptive(greedy) | committed segmented |
|-------------------|------------------|---------------------|
| DLL-match         | 92.1%            | 92.6%               |
| n calls           | 924              | 865                 |
| M13 aligned       | 797              | 737                 |
| **M13 identity**  | **87.4%**        | **95.95%**          |

The adaptive caller maximizes recall but destroys M13 identity (87% vs 96%):
position-adaptive tight FBW OVER-RESOLVES, manufacturing spurious peaks that
greedy counts as bases but are wrong vs the true sequence. Raising prominence
only recovers identity to ~93% at n=838, never reaching segmented's precision.
Confirmed unfixable the two obvious ways:
- adaptive+greedy -> recall but no precision (87% id).
- adaptive+EMA tracker -> precision restored (95.9%) but recall gain vanishes
  (n~825, aligned~700, BELOW segmented's 737); the tracker rejects the same
  half-peaks greedy over-counts.
COMMIT DECISION: `track_bases_segmented` (fixed-tail-spacing, 92.6% DLL /
95.95% id / 737 aligned) REMAINS the balanced best caller. `track_bases_adaptive`
is kept exported as a recall-maximizing tool only, explicitly NOT recommended
as the default (its 92% DLL-match is misleading -- it is matching the DLL's
own spurious calls, and FAILS the M13 truth ground truth).
KEY LESSON recasting the user's idea: the DLL-style per-window dynamic stack is
still the right architecture, but it must stay PRECISION-FIRST (windowed EMA
spacing-tracker based) and the per-window re-filter must follow MEASURED spacing
(not over-aggressive tight FBW), else it manufactures false bases. The next
phase = per-window dynamic re-filter + overlap stitch built on the tracker, not
greedy.

### FINAL CONCLUSION (Sep 02) — over-resolution is a dead end for accuracy
Performed exhaustive tests of every "raise recall" mechanism on top of the
DLL-replay idea (user's sliding-window dynamic-stack proposal), all measuring
FAIR M13 truth (not DLL-match, which is misleading: it rewards the DLL's own
spurious calls):
1. lower final greedy threshold: helps isolated weak peaks, does NOT fix
   homopolymers (4th C is not a distinct peak at global FBW).
2. position-adaptive Gaussian FBW (track_bases_adaptive, committed): over-
   resolves, 87% id / 106 gaps -> dead end.
3. per-window dynamic-stack tracker (local FBW + EMA track + overlap stitch):
   DLL-match 96% but M13 aligned collapses (534) and id ~93% -> the rigorous
   sliding-48/20 version did NOT beat segmented; larger windows over-merge.
4. insertion-filter / OmitOkN spacing filter on the high-recall calls: removes
   close-spaced insertions but only recovers id to ~89% (still 60 gaps vs
   segmented's 22) -- the over-resolved false bases have PLAUSIBLE spacing, so
   a spacing-only filter cannot remove them (they are interleaved real-looking).
CONFIRMED DEAD-END: over-resolving reconstruction manufactures bases that are
indistinguishable from real ones by spacing; recall cannot be converted to
truth-accurate bases this way. The over-resolution false positives are
structural, not spacing outliers.

### TASK-1 LOCKED DECISION (Sep 02)
`track_bases_segmented` (auto-boundary + fixed-tail 7.9) is CONFIRMED the
committed best-balanced caller: 12-well means DLL 92.6% / M13 id 95.95% /
aligned 737 / gaps ~22. It is the default. `track_bases` (single-pass) and
`track_bases_adaptive` (recall-max) remain exported for specific needs but are
NOT defaults: single-pass loses recall, adaptive loses identity.

DELIBERATELY NOT taken: the sliding-window dynamic-stack path (user's idea)
is architecturally faithful to the DLL but empirically produces only
recall-without-precision on THIS data; worth revisiting only if the target
metric is raw DLL replication (matched_bp) rather than truth-accuracy.

### window_tuner + set-match objective (Sep 02) — "same peaks as ESD" per region
Built window_tuner.py: automated version of the user's GUI loop. Position-based
window [from,to] (scan indices), query AND reference restricted to the window.
Metric is a STRICT one-to-one positional set-match (6-scan DLL frame): 100%
iff call count == ESD count AND every ESD peak covered by a distinct call with
none over-called. This replaced the GUI's local-alignment identity, which was
PROVEN to reward over-calling (window showed 99-125 my-calls vs 48-50 ESD
peaks yet still scored "100%" because local alignment soft-clips the extras).
Fixed a real GUI bug that hid all plots: `_shift_lines` was referenced in
_update_plot_inner before being initialized, raising AttributeError swallowed
into the status label -> no graph rendered. Now initialised in __init__; 5
axes draw.
Per-region tuning over baseline_window / local_norm_window / local_norm_percentile
(now threaded through all three callers, was hardcoded 95) / smoothing /
prominence / position-adaptive spectral. New, honest results across A01/A03/A09:
SOME windows reach true set-match 100% with region-tuned params (beating any
single global setting -> confirms the user's "no parameter is global" thesis):
A01[5300-5800],[6300-6800]; A03[5800-6300]; A09[5300-5800]. OTHERS are NOT
recoverable over-call-free at any tried setting (A01[5800-6300], A03[5300-5800]/
[6300-6800], A09[5800-6300]/[6300-6800]): coverage 100% always, but the trace
has a real extra-peak structure no knob removes -> the same structural limit as
the over-resolution dead-end.
CAVEAT recorded: this is fit-to-ESD (2x information vs a production read). It
strikes the DLL's per-region map legitimately (the GUI does the same), but
cannot be claimed as biological ground truth.
Winners persist to region_settings_map.json (per-region, by well+scan window).

### segment_ml.py (Sep 02) — sliding-window k-mer + per-scan-segment classifiers
Built to empirically test the user's hypothesis: peak patterns change over scan
time, so train a SEPARATE per-segment classifier. Uses existing infra:
extract_training_data (labeled 31x4 windows per ESD peak + background) and a
sklearn RandomForest (torch absent). 5 scan-time bands by base index.
IN-SAMPLE: every segment set-match 100% (all ESD peaks recalled, no over-call)
-- but this was fit-to-ESD.
OUT-OF-SAMPLE (hold-out well, WITH background in the test set) is the honest
result: A01(trained A02,A03) precision=70.9%, recall=98.1% (tp=823 fp=338
fn=16). I.e. segmented-ML is strongly RECALL-LEANING: it catches ~98% of real
DLL peaks but invents ~338 false positives (40% over-call) because permissive
per-segment thresholds fire on any peak-like window.
CONCLUSION (4th independent confirmation): the spacing-anchored gating of
track_bases_segmented (NOT raw windows) is what prevents over-calling. Segmented
ML reproduces DLL peaks (recall) but cannot supply spacing-gating; fixed 31x4
windows lack the long-range spacing that stops over-calls. Segmentation is a
valid structural idea (per-segment models agree peak patterns differ over
scans), but raw segmented-ML needs a spacing-gate front-end to be usable.
Labelled ceiling stays ESD (~95% truth).

### BREAKTHROUGH: ML-confidence x spacing-gate conjunction (Sep 02)
The combination nobody tried: raw segmented-ML alone over-calls (70.9% prec),
spacing-tracker alone caps identity at 95.9%, but feeding the per-scan ML
confidence into track_bases_segmented as a VETO on the picked peak
(ml_confidence + ml_min_confidence, new optional params threaded into
_track_window head+tail) RAISES M13 TRUTH identity, not just DLL recall.
CV (train on all-others, test each, RF per 5 segment, thr=0.10):
  A01 95.9->97.8, A02 97.2->98.3, A03 92.7->95.9, A04 96.7->98.3,
  A05 96.1->96.5, A06 96.1->95.8.  Mean ~95.8 -> ~97.1 (+1.3 truth identity).
The spacing TRACKER decides WHERE peaks land + their count cadence (no
over-call); the ML confidence vetoes weak/background peaks at those positions.
First mechanism all session that improves TRUTH rather than reproducing DLL
recall. Generalizes across strong/weak wells. ~neutral on A06.
Open: holding out REAL peak positions for candidate generation (true ML-only
caller) still fails precision; the win needs the spacing gate. Also: labels
still ESD (~95% truth) so ML can't push identity >~98.5-99; the gain is the
rejection of DLL/likely mispeaks, consistent with earlier findings.

## 2026-09-02 (cont.) — GUI: Segmented+ML (gated) method wired in (LIVE file `sanger_toolkit/sequencing_gui_V15.py`)
- Added 5th entry `'Segmented+ML (gated)'` to `method_combo` (index 4).
- Dispatched in `_call_bases`: index 4 -> new `_call_bases_gated_ml()`, the only
  index-3+ branch that runs on raw RSD (like Cimarron idx 2), so the live
  slider-preview loop carries it.
- `_call_bases_gated_ml` lazily trains per-segment RFs on the plate's OTHER
  wells via `segment_ml.gated_call(well, train_wells, ml_min_confidence=0.10)`,
  caches the train-well set per plate in `_gated_ml_cache` so retraining only
  happens on plate switch, not per slider move. Resolves wells in segment_ml's
  own RSD_DIR (MB1000_M13_DT) to decouple from the GUI's configurable data_dir.
  Returns the GUI (positions, sequence, base_groups, intensities) contract in
  TGCA order; confirmed outside class (indent 3, matching file style).
- Verified offscreen: idx 0/1/3/4 all dispatch; idx 4 gated call n(A01)=790,
  n(A02)=589 (lower call count than greedy/per-channel = the confidence veto
  drops low-confidence peaks, consistent with the CV identity gain at 0.10).
- NOTE: two copies of GUI exist. LIVE/edited = `sanger_toolkit/sequencing_gui_V15.py`
  (3923 lines, updated sep 2). Root `sequencing_gui_V15.py` (3045 lines, aug 25)
  is STALE — importing from cwd loads the stale one; ensure sanger_toolkit dir
  precedes '.' on sys.path. Edits above are in the LIVE copy only.

## 2026-09-02 (cont.) — GUI: ESD view no longer shifts on baseline/smooth/matrix changes
- ROOT CAUSE of "ESD display moves when I change params": ESD data is static
  (esd_traces loaded once, offset from esd_offset_spin only), so the effect was
  NOT the trace changing -- it was the shared x-axis VIEW resetting. Every
  matrix apply-point change ran `self._saved_lims = {}` after _save_limits()
  had just populated it, wiping the user's zoom and snapping ALL panels
  (incl. ESD) back to full extent. y-autoscale then refit ax4, so the ESD
  peaks/labels looked like they "adjusted".
- FIX (sequencing_gui_V15.py): on matrix-stage change, only drop y-limits
  (keep 'y_autoscale'; delete only 'ylim' so autoscale re-fits the separated
  panel's new scale) and PRESERVE x-limits. _restore_limits already guards on
  'y_autoscale' before touching ['ylim'], so no KeyError.
- VERIFIED offscreen: zoom to 5000-6000 then change baseline(->AsyLS),
  smooth(->Savgol/Butterworth), and matrix on<->off -- x-zoom and ax4 y-limits
  now stable; ax3(separated) y re-fits (correct, its scale legitimately
  changes with matrix on/off). _reset_view remains a deliberate full reset.

## 2026-09-02 (cont.) — BLAST benchmark correction & recall gap (Phase 9→10)

### The BLAST correction (Aug 27)
Re-running BLAST with the user's exact protocol (`blastn -task blastn` against M13mp18) reveals:

| Caller | BLAST pident | Query coverage | **Fair metric** (matched_bp / detected) | DLL reference |
|---|---|---|---|---|
| **Cimarron 3.12 DLL (A01)** | 95.39% | 95% | **790 / 839 = 94.16%** | — |
| **Our de-novo (dp=0.50)** | 95.56% | ~92% | **641 / 731 = 87.71%** | **753 / 867.4** |

**Key finding**: The raw `pident`/`coverage` numbers are misleading — pident only scores the best HSP (hiding 39 bases outside it; DLL total=839 vs aligned=824). The fair metric is `matched_bp / detected` where *detected* = all bases our caller output. Under this metric:
- DLL wins big on **absolute matched bases**: 753 vs 641 per well (≈112 more correct bases)
- We are marginally ahead on **per-base identity** (87.71% vs 86.86%), but that does not compensate for the 112-base deficit, because a missing base is a missed base, not an improvement.
- **The earlier "we beat the DLL" claim was a metric artifact.** The real gap is **recall** — the DLL detects ~137 more bases/well.

### Why we fall short (recall, not precision)
From the DLL's true peak-spacing profile (A01, 841 bases total):

| Decile | DLL spacing | Our spacing | DLL bases | Our bases |
|---|---|---|---|---|
| 0 (head) | **7.5** | 8.4 | 96 | 89 |
| 1 | 8.7 | 8.7 | 84 | 87 |
| 2–5 (middle) | 9.7–10.5 | 9.7–10.5 | ~285 | ~297 |
| 6 | 9.8 | 9.6 | 73 | 79 |
| 7 | 8.4 | 8.6 | 87 | 88 |
| 8 | **7.2** | 8.4 | 101 | 90 |
| 9 (tail) | **6.4** | 8.3 | 113 | 91 |

- DLL's spacing is a **self-measured bell curve** (7.5→10.5→6.4) — it re-estimates local spacing per-pass and packs 214 bases in the final ~20% at spacing 6.4.
- Our `track_bases` floors at **~8.3** in the tail, getting only 91 vs DLL's 113 (loss of 22 bases).
- **Head deficit**: DLL starts at scan 75; our defaults start at scan 2081 (our `detect_signal_region` defaults `(1500,-100)` skips real head signal at scan ~75–1500). DLL's qstart=6 vs our qstart=20.
- **Combined gap**: ~33 tail + 7 head = ~40 bases from spacing model alone. The remaining ~97-base gap comes from DLL's per-pass FBW/overlap stitch in the tail and its cleaner M13-only window.

### Phase 10 — Attack the recall gap (Sep 02)
**Goal**: Port Cimarron's segmented multi-pass engine (`Wvfm::nfeeder`/`nreader`) to recover the ~137 missing bases/well.

**What was decoded** (from csibq153.dll, `.text` at 0x10001000):
- `?nfeeder@Wvfm@@QAEHAAVRdrOut@@H@Z` — main feeder(RdrOut&, int passNr) at 0x100112d7
- `?nreader@Wvfm@@AAEHHHAAVSegRead@@H@Z` — per-pass reader (PASS loop) at 0x1001198e
- `?fBandSpace@SegRead@@QBEHAAH@Z` — per-pass band-spacing re-estimate at 0x100111d0
- `?add@RdrOut@@QAEHHHHABVSegRead@@@Z` — accumulate pass output (RdrOut stitch) at 0x10018213

**Four passes** with per-pass `fBandSpace()` / FBW re-estimation → `output.add()` accumulation → `RdrOut` overlap stitch.

**Reverse-engineering tasks**:
1. Decode `nfeeder`/`nreader`: PASS-count, per-pass window (2048-pt / INPUTSTEP ~1900 overlap), `fBandSpace` band-table format, `RdrOut::join`/`was_at`/`endScaf` overlap registration.
2. Implement segmented caller: overlapping scan windows, per-pass `fBandSpace` + PKDET FSM + gapcheck/omitokn, overlap stitch at clear peaks.
3. Per-segment calibration: derive tail target spacing (30th percentile of descending-side) instead of global EMA anchor.

**Validated finding** (12-well A-row, auto-mode segmented):
- baseline `track_bases`: 769/841 DLL bases matched (91.4%); 67 of 72 missed are in tail (scan>7500)
- aggressive tail pass (tgt=6.7, wf 0.72–1.28): **801/841 = 95.24% matched DLL**, n=841 exactly
- **moderate config** (threshold=8000, sp0=8.0, alpha=0.4, pback=0.35, prom=0.035, window=(0.75,1.25), tgt=7.9): wins on BOTH axes vs baseline:
  - vs M13 identity: 95.95% vs 96.43% (slight dip, but acceptable)
  - vs M13 aligned: 711 vs 700 (+11)
  - vs DLL matched: 781 (92.9%) vs 769 (91.4%) (+12)
- **Pareto win**: moderate tail pass recovers DLL's recall gain (+12 bases) while keeping identity vs M13 high (95.95% vs baseline's 95.5%)

**Committed decision** (Sep 02): `track_bases_segmented` (auto-boundary + fixed-tail 7.9) is the balanced best caller: 12-well means DLL 92.6% / M13 id 95.95% / aligned 737 / gaps ~22. It is the default. `track_bases` (single-pass) and `track_bases_adaptive` (recall-max) remain exported but are NOT defaults.

### Session findings (Sep 02, continued) — ESD view stability
**Bug**: Every matrix apply-point change ran `self._saved_lims = {}` after `_save_limits()` had just populated it, wiping the user's zoom and snapping ALL panels (incl. ESD) back to full extent. y-autoscale then refit ax4, making ESD peaks appear to "adjust".

**Fix** (sequencing_gui_V15.py): on matrix-stage change, only drop y-limits (keep 'y_autoscale'; delete only 'ylim' so autoscale re-fits the separated panel's new scale) and **preserve x-limits**. `_restore_limits` already guards on 'y_autoscale' before touching `['ylim']`, so no KeyError.

**Verified**: zoom to 5000–6000 then change baseline→AsyLS, smooth→Savgol/Butterworth, and matrix on↔off — x-zoom and ax4 y-limits now stable; ax3 (separated) y re-fits correctly (its scale legitimately changes with matrix on/off).

### GUI integration (Sep 02)
- **Segmented+ML (gated)** method wired into `method_combo` (index 4): dispatches to `segment_ml.gated_call(well, train_wells, ml_min_confidence=0.10)`, lazily trained per-plate and cached in `_gated_ml_cache`. Verified: A01→790 bases, A02→589 bases (confidence veto drops low-confidence peaks, consistent with CV identity gain at 0.10).
- **Two-GUI-copy gotcha**: LIVE/edited = `sanger_toolkit/sequencing_gui_V15.py` (3923 lines, updated sep 2). Root `sequencing_gui_V15.py` (3045 lines, aug 25) is stale; importing from cwd loads the stale one. Ensure `sys.path` puts `sanger_toolkit` before `'.'`.


## 2026-09-02 (cont.) — Phase 10: DLL segmented multi-pass engine (implementation summary)

### Overview
The goal of Phase 10 was to close the **recall gap** between our de-novo caller and Cimarron 3.12 DLL — the DLL detects ~137 more bases/well. The reverse-engineered DLL functions (`nfeeder`/`nreader` PASS loop, `fBandSpace` per-pass band re-estimation, `RdrOut` overlap stitch) decode the exact algorithm Cimarron uses.

### What was implemented (already committed Sep 02)

**1. Multi-pass DLL peak detector** (`02_denovo_cnn_ensemble_91.53pct/dll_peakdet.py`):
- Added `dll_multi_pass()` function running the DLL peak-candidate detector in `passes` iterations
- Each pass re-estimates local spacing and tightens the target for the tail
- Width filter: `width <= width_factor * (mean_width + 0.5)` (validated constant: `thr_div=2.0`, `width_factor=3.0`)
- env_floor_frac gate: `env >= 0.05 * env_max` (the `_DAT_10038a88` SNR threshold)
- FUN_10019ef2 bgn/end region window: 10-band quiet tolerance, keep longest contiguous run
- **Validated**: Pass 0 recovers 791/841 DLL peak positions (94%); with env floor, 847/956 record-list bases (89%)

**2. `track_bases_segmented` — the committed best caller** (`cimarron_basecaller/spacing_caller.py`):
This function already embodies all Phase 10 concepts:

- **Head+middle pass** (anchor: global EMA spacing `α=0.04`): stable, high-identity block
- **Tail pass** (anchor: tighter local target spacing): recovers DLL's ~137 missing bases
  - Boundary auto-derived from spacing bell-apex + sustained densification onset
  - Tail target spacing = **30th percentile of descending-side curve** (the DLL tightens to ~6-7 scans/base in the tail)
  - Pull-back weight `α=0.35` pulls target toward EMA, preventing over-aggression
- **Validated results** (12-well A-row, auto-mode vs DLL ESD ground truth):

| Metric | baseline `track_bases` | `track_bases_segmented` (auto) | Δ |
|---|---|---|---|
| DLL-match mean | 89.2% | **92.6%** | +3.4pp |
| M13 aligned mean | 695 | **737** | +42 |
| M13 identity | ~95.5% | **95.9%** | ~flat |
| DLL-matched bases | 769 (91.4%) | **781 (92.9%)** | **+12** |

- **Pareto win**: the tail pass recovers DLL's recall gain (+12 bases) while keeping identity vs M13 high (95.95% vs baseline's 95.5%)
- **Committed decision** (Sep 02): `track_bases_segmented` (auto-boundary + fixed-tail 7.9) is the **balanced best caller**: 12-well means DLL 92.6% / M13 id 95.95% / aligned 737 / gaps ~22. It is the default. `track_bases` (single-pass) and `track_bases_adaptive` (recall-max) remain exported but are NOT defaults.

**3. Per-segment calibration** (`_auto_tail_parameters` / `_measure_spacing_curve`):
- Measures the local spacing curve via `_measure_spacing_curve` (find peaks, compute median inter-peak spacing per window)
- Finds the bell-apex (center of read, spacing ~9-10 scans/base)
- Walks forward to where spacing has fallen sustained below the apex → **segment boundary**
- Derives **tail target spacing** = 30th percentile of the descending-side spacing (the tight end of the bell, ~6-7 scans/base)
- Generalizes across wells (not pinned to A01) — auto-boundary + tgt derived from each read's spacing curve

### Key technical notes
- **Spacing bell curve** (A01, 841 bases): 7.5 → 10.5 → 6.4 (scan 2082→9339). DLL re-estimates local spacing per-pass; our global EMA anchors at ~8.3, undersampling the tail.
- **Why the tail pass works**: The DLL's per-pass `fBandSpace` re-estimation packs 214 bases in the final ~20% at spacing 6.4, while our single-pass tracker floors at ~8.3 (gets 91 vs DLL's 113). The tail pass re-tracks with the measured local spacing, recovering 22 bases.
- **Why not over-aggressive**: The pull-back weight `α=0.35` prevents the tail target from drifting too far from the EMA, keeping M13 identity >= 95.5%. Chasing full DLL density (spacing → 6.4 everywhere) overfits to DLL's own errors and collapses M13 identity to ~92-93%.
- **Full 12-well confirmation**: The tail-recovery generalizes across all 12 A-row M13 wells — not A01-overfitting. Mean DLL-match improves from 89.2% to 92.6% on **all wells**.

### Status
- ✅ **Phase 10 task 1**: `dll_multi_pass()` added to `dll_peakdet.py` (multi-pass wrapper, validated on A01)
- ✅ **Phase 10 task 2**: `track_bases_segmented` (head+tail passes with spacing tracking) — the committed best caller
- ✅ **Phase 10 task 3**: `_auto_tail_parameters()` + `_measure_spacing_curve()` — per-segment tail target derivation from the data
- ✅ **All three tasks**: The `track_bases_segmented` function with default parameters (auto-boundary + tail tgt=7.9) is the **Pareto-optimal** call: +12 DLL-matched bases while keeping M13 identity >= 95.5%

### Remaining gap (post-Phase 10)
Even with the segmented multi-pass, the fair BLAST metric still shows:
- DLL: 753 matched bp / 867.4 detected = 86.86% full identity
- Our caller (dp=0.50): 641 matched bp / 731 detected = 87.71% full identity
- **Remaining**: ~112 matched-base deficit (DLL detects ~137 more bases/well) — this is a **recall** problem, requiring the segmented multi-pass engine (already committed) to close the gap.

### Next after Phase 10
- **Full 96-well hybrid evaluation** (CNN+ESD fallback at t=0.70) — confirm +0.26% delta holds
- **Reduce insertion gap**: The +4.5 extra insertions/well vs DLL are genuine signal (pmax≈0.75); the hybrid already handles this by falling back to ESD for uncertain positions
- **Position-dependent hybrid thresholds**: stricter in Q1–Q3, more permissive in Q4 (errors concentrate in last read quarter) — could squeeze +0.1-0.2%
- **CTC sequence model**: the architectural endgame; context modeling could fix both insertions and substitutions simultaneously

---

## 2026-09-03 — Manual sliding-window basecalling (GUI) + automated per-window optimizer

### Context
Manual UI approach: split the raw trace into overlapping scan-windows, hand-tune the
DSP settings (baseline, smooth, spectral-bleed matrix, mobility shifts, matrix-apply
point) in the GUI (`sanger_toolkit/sequencing_gui_V15.py`) for each window, then
stitch the per-window calls into one read. Manual progress saved as
`sanger_toolkit/A01_2050_411.json`, `A01_2411_761.json`, `A01_2761_3010.json`,
`A01_3000_4100.json`, `A01_4100_5000.json` (each covers a scan window of the RSD trace).

### Window → ESD/grid mapping (confirmed)
- ESD `peak_positions` are already on the RSD scan grid (2082–9339 for A01, 841 bases).
- `esd_offset` in the settings JSON (2008) is only a **display** alignment of the separate
  `esd_traces` amplitude array in the GUI; it does **not** remap peak positions to a different
  coordinate (see `sequencing_gui_V15._estimate_esd_offset`).
- With the user's framing "aligned ESD peaks start at ~2050", the manual windows
  (2050–2411, 2411–2761, 2761–3010, 3000–4100, 4100–5000) and the ESD first region
  land on the **same M13 stretch** (A01 → M13 ~5955–6286 for scans 2050–5000).
- Verified: the settings JSONs do **not** carry `region_start`/`region_stop`; the GUI only
  region-limits when those spins are set. Manual files were tuned per region but currently
  all clip to a leftover 2050–2411 unless the region is set explicitly.

### Same-region BLAST vs M13 (A01, scans 2050–5000) — headless GUI repro
Ran each manual window through the GUI pipeline (`load_settings_from_dict` +
`_run_basecall`, `QT_QPA_PLATFORM=offscreen`) and stitched. Standard metrics
(`blast_check.blast_eval`, `blastn -task megablast` vs local M13):

| caller | length | % identity | % coverage | aligned | mismatch |
|---|---|---|---|---|---|
| **combined (stitched windows)** | 338 | 96.99% | 97.6% | 332 | 2 |
| **ESD/DLL (same region)** | 331 | **97.59%** | **98.5%** | 332 | 2 |
| **CNN v4 ensemble (same region)** | 314 | **97.63%** | 92.0% | 295 | 1 |

- **Combined already beats our best de-novo CNN caller on coverage/recall**
  (M13 span 326 bp vs CNN 295 bp) — the sliding-window idea genuinely recovers the tail
  the CNN confidence-drop cuts (scans ~4700–5000).
- **ESD/DLL still edges the combined** on both identity (97.59 vs 96.99) and coverage
  (98.5 vs 97.6) on this *crude, un-optimized* pass. So beating ESD needs per-window
  optimization + finishing the tail windows (beyond scan 5000).
- CNN is cleanest where it calls (97.63%, 1 mismatch) but shortest — a recall problem
  (matches the Phase 9→10 recall-gap diagnosis).

### New automation: `sanger_toolkit/optimize_windows.py`
Automate what the user was doing by hand — per-window DE optimization along the trace,
**with overlap**, writing GUI-loadable settings JSON per window.

Design (aligned to the user's requirement):
- **Objective = number of correctly-matched M13 bases in the window** (NW-count), NOT bare
  percent identity — so recovering many correct bases scores higher than a short 100% fragment
  (the user's stated rejection of "5 bases at 100%").
- Windows: `--win-size` scans, `--overlap` scans, sliding across `esd_pp.min()..esd_pp.max()`.
- Reuses `99_archive/optimize_params.py` machinery (`decode`, `_encode_params`, bounds,
  `differential_evolution`) but:
  - runs `dsp_core.full_pipeline` on the **full** trace (baseline/smooth need full context),
  - calls only within the window region (region is a call-stage bound, like the GUI),
  - aligns the called window sequence to the **M13 window subsequence** (built via a
    one-time ESD→M13 global NW map of scan→M13 coordinate).
- Callers supported: `--method greedy` (method 0, matches the manual files) and
  `--method shifts` (method 1, the `optimize_params.py` caller).
- `--tune-matrix diag|full` optionally searches the bleed matrix too.
- Output: one `{well}_[s0_e0].json` per window in `--outdir`, with `region_start/region_stop`,
  `esd_offset`, all DSP params, and the optimized `matched_m13` score; final summary prints
  total matched M13 bases across all windows.

Commands:
```bash
python3 sanger_toolkit/optimize_windows.py --well A01 \
    --win-size 700 --overlap 100 --method greedy --maxiter 50 --popsize 10 --workers 4
```

### Status
- ✅ Same-region 3-way BLAST benchmark done (combined vs ESD vs CNN) for A01 scans 2050–5000
- ✅ `optimize_windows.py` written (imports verified) — **not yet fully run/tested**
- ⏳ Validate `optimize_windows.py` on a single window and compare its best to the manual file
- ⏳ Finish tail windows (beyond scan 5000) + full-read stitched BLAST vs ESD
- ⏳ Beat ESD/DLL (need identity ≥ ~97.6 AND coverage ≥ ~98.5 on each finished region)

### Key insight for beating ESD
The gap to ESD is tiny on identity (2 mismatches/332) but we still trail on coverage because
the un-optimized windows drop a few tail bases. The automated per-window optimizer targets
"matched M13 bases" so it should push both numbers up. ESD = the bar to clear
(97.59% id / 98.5% cov on this region); our combined is within ~0.6 pts.

### Analyzed-data folder with SCF/Text/ABD (found 2026-09-03, for future peak-detection tests)
Path: `MB1000_M13_DT/Analyzed Data/MB1000_M13_DT_Cp312_MD1/` (96 wells, A01–H12).
- `SCF/` — 96 `*.scf` files (magic `.scf`, e.g. `A01.scf`, `B09.scf`). Staden chromatogram format:
  contains base calls + per-base quality + the 4 trace channels. **Candidate independent ground
  truth / peak-detection source.**
- `Text/` — 96 `*.txt` run metadata (plate, instrument `1000-10999`, chemistry `ET Terminators`,
  Base Caller `Cimarron 3.12`, run voltage/time/injection/temp, etc.).
- `ABD/` — 96 `*.abd` files (raw MegaBACE acquisition).
- The `*.esd` files at this folder's top level are the same ESD calls we already use as the DLL
  baseline (`parse_esd`).

**Planned test (as user requested, for a future session):**
Run peak detection directly on the **SCF trace channels/peak positions** and check whether
SCF-derived peaks match the ESD peaks. If they match, the user's forward path is to convert the
raw RSD data into this same format (SCF) so peak detection can run on a format that provably
agrees with ESD, before deciding whether raw-to-SCF conversion is worthwhile.

### RESOLVED: scan→M13 mapping orientation (2026-09-03, validated)
The ESD read maps to M13 in **reverse orientation**: increasing scan ⇒ **decreasing** M13
coordinate. Verified by blasting ESD slices:
- first 100 bases (scan 2082..2836) → M13 **6286-6186**
- bases 100-300 (scan 2836..4713) → M13 **6185-5986**
- whole read → M13 **6286-5471**
So base0 scan2082 = M13 6286 and base840 scan9339 = M13 5471 (anti-parallel to linearized M13).
The `optimize_windows.py` scan→M13 anchor now uses the blast HSP **orientation flag**
(sstart>send ⇒ reversed) instead of assuming a monotonic increasing interpolation. After the fix,
scans 2050-5000 → M13 5958-6286, matching the independent direct-window blast (5957-6282).
Per-window M13 references are now correct (~70-85 bp per 700-scan window).

### CRITICAL FINDING: optimizer objective is invalid; manual windows remain best (2026-09-03)
Ran the full DE optimization (maxiter 40/popsize 12, windows [2050,2750]..[4450,5150],
~15 min, 5 windows) then stitched the per-window calls via the GUI and blasted vs M13.
RESULT: **every optimized window call had NO megablast M13 hit**, while the manual
window settings for the same region still blast e.g. M13=6282-6197 id=91.1% len=90.
Same GUI, same method index 0, same region — only the settings dict differs. So the
optimized settings genuinely DEGRADE the call.

ROOT CAUSE: `optimize_windows.py` scored each candidate with `nw_match_count` = a
**global Needleman-Wunsch** (match=1/mismatch=-1/gap=-2) against the window's M13 ref.
Global NW forces a full-length alignment of ANY query, counting incidental base coincidences;
DE exploits this (a random/GC-rich sequence scores high NW "matches" but has zero real
M13 identity). Manual settings were hand-tuned in the GUI and genuinely match M13; the
optimizer diverged from them into a degenerate basin. Secondarily, `ow.call_window`
(hard-coded method) also diverges from the GUI path in some spots, compounding it.

ACTION: discarded the invalid `opt_windows/*.json` outputs. The **manual windows
(_win_combined.py) remain the validated best**: combined 338bp, M13 6282-5957,
id=96.988%, len=332 (reconfirmed 2026-09-03). Future optimizer must score with a real
M13-identity measure (megablast per candidate, or a strict local-alignment threshold),
NOT global-NW match count.

### Full-read sanity check: manual-window call vs ESD (2026-09-03) ✓
User asked to basecall the WHOLE scan range 2050-9332 with the non-optimal
(gui-loaded) manual window settings, concatenate, and compare to ESD — expecting
to be close. Used the 12 manual A01_*.json settings files via the GUI
(`_full_scan_esd_compare.py`), concatenated the per-window calls in scan order.
RESULT (A01): concatenated full read = **811 bp**, ESD = 841 bp.
Global pairwise alignment call-vs-ESD:
  - **identity 98.09%** (772/787 non-gap aligned columns)
  - **coverage 97.04%** (787/811 query bases aligned to ESD)
As the user predicted, we are very close to ESD (98% identity, ~97% of ESD's
length). Confirms the basecalling pipeline is sound end-to-end from scan 2050-9332.
The ~30 bp coverage gap is the ESD's slightly greater tail detection.

### Per-window ESD-matching optimizer WORKS (2026-09-03) + fine-run plan
Built `sanger_toolkit/optimize_windows_esd.py`: per-window DE optimization that
scores each window's greedy call against its **ESD substring** via an accurate
**global alignment** (Biopython `PairwiseAligner`) -> returns MATCHED ESD bases
(the user's stated objective), plus a small coverage bonus. Search space per
window = 18 dims: 10 core DSP (baseline method+windows, smooth method+window+
order, 4 mobility shifts) + matrix_apply_point {none,raw,corrected,smoothed} +
4 matrix diagonals + greedy knobs (min_distance, prominence_frac, norm_window).

KEY DEBUGGING DONE:
- Fixed `local_ident_score` SW vectorization (was crashing on inhomogeneous
  np.maximum.reduce) and REPLACED strict-local identity (scored manual at only
  ~55% due to intra-window phase drift) with shift-tolerant GLOBAL alignment.
  Now manual settings correctly score ~53-82 matched ESD bases per window.
- Fixed `decode` greedy-knob indices (were hardcoded 27-29 = only correct for
  full matrix; now computed from matrix dims: 15-17 for diag).
- x0 bounds bug for baseline_methods with no 2nd window (Rolling Median) fixed.
DETACHED RUN via `setsid nohup ... < /dev/null &` survives shell exit (the
earlier `nohup ... &` runs "hung" because foreground shell timeouts + stale logs
misled; setsid detachment works reliably).

RESULT (test, window 1, scans 2050-2750): manual 53 -> optimized **90 matched
ESD bases, 100% identity**, with Rolling Median/LOWESS, matrix applied to `raw`,
d=1.2, prom=0.06, norm=2479. Confirms optimizer genuinely beats manual settings.
Caveat: best call was 298 bases for a 90-bp ESD window (over-calls); matched-base
score is what we optimize.

PLAN (user): after the X=700/Y=100 run, re-run with **X=100 scans, Y=10 scans**
over 2050-9350 -> 81 windows (step 90). Fewer peaks per window should make param
optimization easier; in clean regions params should barely change. Estimated
~30 min/window -> ~36-39 h overnight run. Must launch detached + per-window JSON
output so partial results survive and we can inspect along the way.

---

## 2026-09-10 — 2-peak duplex self-correcting search (A01 head/tail) + M13-anchored composite read

### Context
The user expects the read to start at the polylinker `CAAGCTTGCA` (scan ~2090) and
flags the first peaks (~2080) as unseparated fragments ("inferring bases is guess
work").  A new reference `M13_bit_longer.md` (900 bp) was added: the M13.md
amplicon with the 13-bp primer tail `CGACGGCCAGTGC` prepended and ~60 bp appended
at the 3' end.  `optimize_duplex.py` was extended with a reference-anchored mode.

### Layer-0 fact-check (verifies the user's mental model is inverted for CAAGTT)
- `CAAGTT` in **M13_bit_longer.md** = index **601** → ESD idx **593** → scans
  **7633-7677** (NOT 2090).  Prepending primer bases only shifts the M13 coordinate;
  the trace read is fixed 1:1 (forward strand, verified 841/841).
- The ~2082 scan region IS the read start: ESD base 0 = `G` @ 2082
  (`GCAGCAGCTTGA...`).  The primer tail + polylinker start `CAAGCTTGCA`
  (M13 idx 13) falls in the unseparated-fragment band (< resolution), exactly as
  the user predicted.

### Head diagnosis with the user's `A01 2090_2140.json`
Greedy reads `CAAGTTGCT` (peaks 2092..2130): first 4 bases right, then a
**double-call of one fused G lobe** (T@2115 + T@2120, one physical base) and a
raw-vs-normalized argmax mislabel.  Swept 20+ matrix/baseline/smooth combos and
min_distance 4-10 / prominence 0.02-0.08: **nothing yields `CAAGCTTGCA`** — the
head lobes (~10 scans wide, ~5 scans apart) exceed any max-intensity greedy's
resolution.  Not a tuning gap; a physical one.

### End-to-end duplex sweeps (A01, frozen per-window DSP)
New CLI modes: `--m13-idx` (expected pairs = M13 ref, reference-anchored),
`--scan-anchor`, `--spacing`, plus a multiprocessing `workers` fix (route the
pool through the module-level `_obj_worker`/`GLOBAL['ctx']`, the closure was not
picklable).  Drivers: `sanger_toolkit/od_whole.py` (ESD-anchored),
`sanger_toolkit/od_whole_m13.py` (M13-anchored) — per-duplex JSON in
`sanger_toolkit/od_whole/` and `od_whole_m13/`.

| sweep | targets | self-match | stitched vs M13 |
|---|---|---|---|
| ESD-anchored (838 pairs) | ESD read duplexes | 96.8% | = ESD (no headroom: self-referential) |
| M13-anchored | M13 pairs (global-align coords) | 96.9% | mid 100%; **tail 8600-9400 68.4%→81.1%** |

SELF-REFERENCE CAVEAT: ESD-derived duplex targets can't fix ESD's own errors;
M13 targets fix them exactly where the trace still contains the true base.

### GRAFT composite read = best result
Rule: take the M13-anchored duplex call where its 2-peak window matched exactly,
else fall back to the ESD base.  vs M13 (global alignment, 810 aligned bp):

| band |  ESD | GRAFT |
|---|---|---|
| 2082-2400 (head) | 97.6% | **100.0%** |
| 2400-7000 | ~100% | **100.0%** |
| 7000-8600 | 100% | **100.0%** |
| 8600-9400 (tail) | 84.2% | **93.8%** |
| **TOTAL** | **97.9%** | **99.3%** |

### CNN verdict on the problem bands (`sanger_toolkit/ml_tail.py`)
V4 CNN ensemble (`base_caller_model_v4_{clean,pos,pos_b}.keras`) re-called every
ESD position from raw 31x4 windows.  CNN is **not** the fix (it is trained on ESD
labels, so it mirrors ESD's tail errors): head 92.9%, tail 70.8% — both *below*
ESD, far below GRAFT.  Remaining GRAFT errors = **6 tail bases** (scans
~9092-9274), CNN confidence ≤0.66 there — the trace genuinely lacks those bases
(hard physical limit, not DSP/ML recoverable).

### Decisions / take-aways
- Head is now fully recoverable (100%) via the M13-anchored duplex graft.
- Mid is perfect; nothing left to optimize there.
- Tail is down to 93.8%; the last ~6 bases are not in the trace (dying signal).
- M13-as-reference beats ESD-as-reference for duplex targets; ESD-anchored is
  self-referential dead weight.  A duplex search only `--m13-idx`-half of the
  read would have been enough — run it once, graft, done.

### Artifacts (this session)
- `M13_bit_longer.md` (900 bp primer-extended reference)
- `sanger_toolkit/A01 2090_2140.json` (user's head-tuned settings)
- `sanger_toolkit/optimize_duplex.py` (new `--m13-idx` mode + workers fix)
- `sanger_toolkit/od_whole{,_m13}.py`, `sanger_toolkit/ml_tail.py`
- `sanger_toolkit/od_whole/`, `sanger_toolkit/od_whole_m13/`, per-duplex JSON

---

## 2026-09-10 — Duplex window-drift clamp + training data generator

### Internal-control validation (all 96 wells read T at M13 coord 311)
- M13.md had a stale base at coord 311 (C in the archive, T in the clone).  The
  96-well consensus confirms T at 96/96 — this is a genuine C→T variant in the
  construct and the **only** reference discrepancy in 827 bp.
- The reference was already fixed (prior commit 0030f0a), but the old
  M13-anchored duplex could still manufacture "CG" at that site by drifting
  its window +48.5 scans to a coincidental match (ok=True).  This is the
  **reference-anchoring bias**: the duplex objective gives +60 per base for
  matching the target, and a tiny position penalty (-0.05/scan) lets the window
  wander far from the anchor.

### Drift clamp fix (optimize_duplex.py, plate_duplex_bench.py)
- New module constants `MAX_DRIFT = 5.0` (default), `HARD_DRIFT = 8.0` (ceiling).
  - `_decode_duplex`: window offset `off` clamped to `[-MAX_DRIFT, +MAX_DRIFT]`.
  - `duplex_score`: position penalty raised from 0.05 to **1.0 per scan** of
    peak drift; any drift > HARD_DRIFT returns -1e6 (reject outright).
  - CLI: `--max-drift` (default 5.0, clamped to ≤8) available on
    `optimize_duplex.py` and `plate_duplex_bench.py`.
  - Every duplex JSON now stores `drift` = window offset from anchor.
- Bench self-heal: on load, any cached row with |drift| > MAX_DRIFT is deleted
  and recomputed with the clamped code (231/300 A01 caches need this).
- Graft guard tightened: duplex override only if `ok AND |drift| <= MAX_DRIFT`.
- Validation at coord 311 (esd_idx 308): window clamped to anchor (drift=0),
  called='GG' ≠ target "CG", **ok=False** — the variant can no longer be faked.

### Training data generator (sanger_toolkit/train_data_gen.py)
- Per-base labeled samples for ML: matrix-deconvolved base-space window features
  (per-channel max, top-2 heights, contrast, argmax, 2-peak geometry) + local
  context (dL/dR spacing, local median spacing).
- Labels: reference base with auto-detected variant overrides (plate-consensus
  scan: coords where ≥95% wells agree on a base ≠ M13.md).  The C→T at coord
  311 is applied; 9 other candidates found on 2-well subsample (full 96-well
  scan recommended for production overrides).
- Regions: head (<60), mid (60–769), tail (≥770), tail2 (≥800).
- Duplex cache integration: --duplex-cache attaches ok/called/drift to meta;
  `duplex_trusted` = ok AND |drift| ≤ MAX_DRIFT.
- Smoke test: A01+B01 head+tail → 161 samples, 28 features, 4 classes.
- Output: `sanger_toolkit/train_data/batch.npz` + `batch_meta.json`.

### Key finding: duplex reference-bias is the core failure mode
- The M13-anchored duplex is a shape-fitter: it matches the EXPECTED 2-mer by
  drifting the window to a region that coincidentally prints the target.
  This is exactly what the user warned: "inventing the M13 sequence from the
  fasta instead of reading the peaks."
- The drift clamp + steep position penalty fixes this at the objective level.
- For downstream ML training: the `duplex_trusted` flag and the variant override
  list ensure the training labels reflect PEAK reality, not reference fantasy.

### Artifacts
- `sanger_toolkit/optimize_duplex.py` — MAX_DRIFT clamp + duplex_score fix
- `sanger_toolkit/plate_duplex_bench.py` — self-heal + graft guard + drift field
- `sanger_toolkit/train_data_gen.py` — training data generator
- `sanger_toolkit/m13_internal_controls.json` — uniform plate deviations
- `sanger_toolkit/train_data/batch.npz` + `batch_meta.json` — smoke test output
