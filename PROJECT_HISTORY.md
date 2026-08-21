# PROJECT HISTORY — MegaBACE Basecalling
*Merged master document: continuous development record of the electropherogram project.*
*Supersedes `SESSION_LOG_perfect_basecaller.md` + `PROGRESS_REPORT.md` (both archived in `99_archive/`).*
*Deep-dive companion: `03_cimarron312_dll_90.72pct/CIMARRON_MASTER.md` (DLL reverse engineering).*

**Last updated:** 2026-08-21 · **Workspace:** `/media/tv/78B0C7DE1FA7081C/electropherogram` (USB stick, NTFS)

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

---

## 5. Metrics — read this before comparing numbers

- **Old figures (96.5% DLL, 92% RF)** were seed-SW matched/aligned accuracy at
  ORACLE (DLL) peak positions — not comparable to full-read numbers.
- **Current standard**: per-base accuracy of the FULL called read vs the M13
  reference via seed-SW alignment (`extract_m13_clean_training.load_clean_ref /
  seed_sw_align`; read orientation = revcomp of settingsV10 reference_dna).
  Both callers scored identically → comparisons hold.
- NW identity vs the DLL ESDs runs ~87–90% (matches the cimarrontv engine).
- Polished 100% is the expected ceiling for clonal M13 (sample == reference).

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
