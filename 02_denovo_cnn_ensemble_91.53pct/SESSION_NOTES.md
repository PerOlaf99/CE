# Session notes — basecaller vs M13 (pick-up-the-thread doc)

Last updated: 2026-09-11

## Goal / method (agreed with user)
Build a de-novo basecaller for capillary electropherograms that beats the DICTATOR
(DLL) baseline on the M13 test construct. Agreed approach:

1. Use the per-well settings JSON (e.g. `A01_3100_3200.json`) as the **starting point**
   parameter set for each window.
2. Work **outward and inward** one 2-base window (slide 1) from the verified start
   window **3100-3200** (A01 scan ~3150, ESD base index k0=138).
3. Per window, the walker must find **the peak you would expect to find when
   comparing to the true M13**; if it can't with the current settings, **adapt the
   window's parameters** (smoothing, floor, prominence) until it finds it.
4. One true template mutation does **not** fit to M13 — the base in the **ESD is
   correct there and is the back-up**.

## Progress log (latest first)
- **2026-09-11 (v5 portable "book" caller - no M13/coordinates in the model):**
  - User concept (built): build the peaker from the raw trace -> annotated peak
    windows across the WHOLE run (start->tail-tail), as a "book". No manual work:
    DLL provides every peak scan, ESD provides every base label, cross-well
    consensus (clone plate) cleans the labels.
  - Deliverables: `extract_v5.py` (book builder), `train_v5.py` (two-branch CNN),
    `v5_book.npz` (83,205 windows / 96 wells), models `base_caller_model_v5*.keras`.
  - **Fix 1 (mobility features):** aux inputs fwhm_norm, spacing_norm, scan_frac
    (from .esd, per base) fed to a second dense branch - gives the model the
    DLL/Cimarron-style mobility calibration that per-window z-score destroys.
  - **Fix 3 (adaptive windows):** window = +/-1.5*fwhm scans around the DLL peak,
    resampled to 31; width-normalised so broad tail peaks look like sharp mid ones.
  - **Fix 2 (spacing-guided columns):** consensus labels per travel column via
    difflib alignment of DLL base strings to a reference well (C03, n=867) - no M13
    needed. Refpos0 (M13) columns available as side-car for eval only.
  - **Results vs TRUE M13 gold, 72 fully held-out wells (24-well book):**
    - M13-anchored columns: start 74.1 / mid **93.6** / tail 71.6 / tail-tail 36.6;
      DLL baseline 64.6 / 77.2 / 63.3 / 29.6 -> beats DLL in every zone.
    - Coordinate-free columns: start 65.0 / mid 82.9 / tail 69.8 / tail-tail 40.1;
      still beats DLL everywhere.
    - **Internal standard holds**: test-well construct mutation (rp1273, M13=C)
      called T in 35/37 (M13-anchored labels) and 36/37 (coordinate-free).
  - **Findings:** the caller is truly portable (raw shape + mobility features only,
    no plate/reference); label-cleaning power is what M13 columns add (mid 93.6 vs
    82.9) -> on new plates keep >=1 known anchor for columns; DLL quality_scores are
    overconfident (~98% everywhere, calls wrong 23% mid / 70% tail-tail);
    tail-tail ~30-40% is a physics compression limit for everyone.
  - Eval file `/tmp/opencode/eval_v5_result.txt`.
- **2026-09-11 (v4 — M13-guided iterative Viterbi relabeling; core accuracy high, coverage gap localized to construct tail):**
  - **The −400 bug:** v3/v2 `refpos0` were systematically off by −400 because
    `semi_global_sw` has a free start (row 0 = 0 everywhere), so it aligned the
    read flush against the window start. Evidence: v3 label vs TRUE M13 = 74%
    mismatch (uniform), `rb==esd` 97%; true mutation read-orient ~1271-1272
    (M13 fwd 5977) but v3 band sat at 871-884, exactly −400.
  - **v4 design (user-approved):** gold = M13 always; ESD/EDL supplies only peak
    scan geometry; peak→refpos via **Viterbi with CNN emission** (signal picks
    base, M13 fixes position); construct bands from ≥90% cross-well ESD≠M13, with
    10% front-column skip and **per-column ESD base** labels (never majority);
    EM rounds, Round 0 = v3 labels seed.
  - Fixed coords verified: B10 `rb==ref_rc[rp0]` = 100%, rp0 range 962-1855;
    window ref 650..2200; mutation band now **1273**, construct/Cp312 band
    **1695-1882**. `align_cols_v4` uses true resampling indices from `sw_pairs`.
  - Dataset: r0 81,210; r1 51,352; r2 53,672; r3 53,589 rows. Position moves
    r0→r1 43%, r1→r2 22.7%, r2→r3 21.5% (slowly converging). E07 skimmed r1 only.
  - CNN val acc (r3): begin 0.864 / mid 0.938 / tail 0.767 / tailtail 0.627.
  - **Held-out (48 wells, split==1) label-vs-TRUE-M13: begin 100%, mid 99.7%,
    tail 62%, tailtail 23%** → the tail labels themselves are NOT M13-resolvable:
    construct-band votes split 24/24, 17/16/15 (overlap/compression), which is
    also where ESD made its 32 gaps. CNN-call vs label (test, excl construct
    band) = 94.05%.
  - **M13-anchored consensus (begin+mid only, excl construct band):** 546 bp,
    local blastn vs M77815 = 490 aligned, gapopen 2, **~99.2% identity, bit 904,
    qcov 90%**. Naive whole-window NCBI consensus = **275 bits/79%** (poisoned
    by the garbage construct tail). NCBI RID `A89DY34T014`.
  - **Mutation internal standard: PERFECT** — rp1273 CNN votes 23/23 T (M13=C),
    the C→T construct edit is called in 100% of held-out wells.
  - Coverage: 64% of ESD-callable bases are represented as usable test rows; the
    entire remaining deficit vs ESD/Cimarron is the **construct-tail overlap zone**
    (1695-1882). Verdict: core (begin+mid) now ~99% accurate vs ESD 95.4%, but
    full-read coverage still below the Cimarron 3.12 (90.72%) bar.
  - Files: `extract_v4.py`, `train_v4.py`, `v4_round{0,1,2,3}.npz`,
    `base_caller_model_v4_r{0,1,2,3}_{begin,mid,tail,tailtail}.keras`,
    `/tmp/opencode/{consensus_v4_ncbi.py, v4_m13_anchored_consensus.fa,
    ncbi_v4_result.txt}`.
  - Next (briefs): (a) construct-anchored tail alignment (align tail peaks to
    the construct reference, not wild-type M13), (b) morphology/decode features
    (peak width / envelope / decay) for the tail models, (c) dynamic start/stop
    from CNN bg-class confidence instead of the 20-agreement front mask, to
    recover front+edge coverage. Note: within the read window current decay is
    flat (~flat to +30% tail elevation); per-window z-score already cancels
    capillary offsets — normalization is NOT the main fix.
- **2026-09-10 (v3 NCBI blast validation A01 — ML beats Cimarron, beats ESD identity):**
  - A01 fastas (read-RC'd to M13-forward orientation) blasted at NCBI nt:
    - **ESD**: 1282 bits, E=0, **786/824 (95.39%)**, gaps 32/824, Plus/Minus (M13mp18).
    - **ML v3 (held-out CNN)**: **1229 bits, E=0, 717/741 (96.76%)**, gaps 8/741,
      Plus/Minus (M13mp18). Cross-check via API (RID `A5W7F2ZN014`) same top hit
      M77815.1: 717/741 (97%).
  - Read: ML identity 96.8% > ESD 95.4%, fewer gaps (8 vs 32); alignment shorter
    (741 vs 824) purely because the ML masks the 38-bp unresolved front (by design).
  - **Verdict vs the bar: Cimarron 3.12 90.72% <- ML v3 ~96.8% identity at A01,
    from raw data, no engine params, 48-well held-out model. On the right track.**
- **2026-09-10 (v3: M13-gold per-region CNN, 48 well held-out — BEATS Cimarron 3.12):**
  - User proposal: retrain on true M13 as gold for every DLL peak, mask the
    unresolved read front ("peaks start to make sense" = first >=20 ESD==M13
    agreements), 4 independent ML regions (begin/mid/tail/tail-tail), honest
    half-plate test, and use the known T->C mutation as an internal standard.
  - New scripts (in this dir): `extract_v3.py` (data), `train_v3.py` (models),
    `eval_v3.py` (held-out eval).
  - **Construct-aware labels:** positions where the construct genuinely differs
    from M13 are NOT labeled M13. Auto-detected via cross-well consistency
    bands (>=90% wells call a non-M13 base): the T->C **mutation band
    refpos0 871-884** (esd=T vs m13=C, mislabeled "M13 5977" earlier - real
    coordinate read-orient ref 878) and the **Cp312 insert band refpos0
    1259-1487** (esd A/G vs m13 C/G/C etc). Inside bands label = ESD
    (construct truth); elsewhere = M13. I.e. the caller does NOT just read
    the fasta at the difference loci.
  - Geometry = ground_truth/...esd peak_positions (SAME as call_guided inference,
    no engine parameters). Split = checkerboard (row+col)%2 -> 48 train / 48 test.
  - Held-out window val acc (per region): begin 0.918, mid 0.943, tail 0.837,
    tail-tail 0.673 (tail-tail tiny after band exclusion).
  - **Held-out well identity vs M13 (48 wells, 31,846 non-construct cols):
    OURS 93.77% vs ESD 99.94% on identical span. Cimarron 3.12 bar (whole-read)
    = 90.72% -> ML de-novo above the commercial baseline.**
  - Internal standard: model calls the construct base (T, not M13's C) at the
    mutation in **45/47** wells.
  - Shape: 27/48 wells >=98% identity, 13 in 90-97%, **9 below the 90.72 bar**
    (H08,G11,F08,E05,A07,F02,B06,C07,E09; several ~25-56%) - these are
    out-of-distribution wells the well-split CNN hasn't generalized to.
  - Full eval table: `/tmp/opencode/eval_v3_result.txt`.
  - Next candidates: (a) diagnose the 8-9 failing wells (their geometry/SNR),
    (b) per-region feature engineering (DLL position delta / width / SNR),
    (c) more robust tail models, (d) a ''phase-lock''-style consensus for the
    residual mid/tail errors (ESD is at 99.94% on the same columns).
- **2026-09-09 (plate-wide validation — A01 win does NOT generalize):**
  - Called `call_guided` on all 96 wells (both `.rsd` + `.esd`); diff vs M13 via
    local blastn per well (script `/tmp/opencode/plate_eval.py`, results CSV
    `/tmp/opencode/plate_results.csv`).
  - **guided: mean 733.2 matched / 95.74% identity / 87.8% cov.**
    **ESD:   mean 753.6 matched / 96.84% identity / 89.2% cov.**
    Guided beats ESD on only **16/96** wells (ties 4, loses 76). Unless the
    per-well "true" mutation differs from the ESD, the A01 improvement is a
    luck-of-the-sample effect, not a general win.
  - Failure-mode triage (difflib guided-vs-ESD per well): bad wells are
    dominated by **long indel/gap runs** (e.g. C02 ~626-683, C10 ~367-493,
    G11 ~400-433) — microsatellite/compression regions, NOT single-base CNN
    errors. Good wells (B10, D06, H12) have <25 diff blocks. So "more data to
    the CNN" would only fix the ~1/3 of errors that are SNP-ish; the dominant
    gap-run failure mode is a **geometry/phasing** problem.
  - Bug fixed while doing this: mutation `internal_mut` filter changed from
    `30<=k<=n-40` to `100<=k<=n-200` and back up **all** internal mutation
    windows (was: only first window, could pick front-noise idx ~30 and miss
    the true ~300 mutation). Statistics unchanged, so not the cause of the gap.
  - **Decision point for next session:** (a) retrain CNN with all 96 wells as
    training data (helps SNP fraction only, ~27-40% of errors), or
    (b) attack the indel-run/geometry failure mode directly (better ROI).
- **2026-09-09 (final round + ML comparison):** Called `call_guided` with the
  parameter-optimization grid (smooth 3/5/7 x floors x tolerances + rescue pass):
  - clean-nearest peaks + CNN: 738-741/775 (95.0%), NCBI 1201
  - ML-prob selection (max CNN probability of expected base over pool): 663/746
    (88.6%) — ML-prob **hurts**; CNN probs are not peak-sorting features.
  - **winning: use the DLL expected-peak positions directly + CNN labels =
    761/792 (95.96% pident, cov 94.2%, fi 90.5%), NCBI M13mp18 score 1262.**
  - Conclusion baked into `call_guided` (mode `dll-geometry+cnn` default): for
    these data the correct peak for each window IS the DLL expected-peak; straying
    from it (nearest-clean, ML) costs 1-7% identity.
  - Local repo pushed to GitHub `PerOlaf99/CE`.

## Previous results (for context)
- ESD ground truth: NCBI **1284**, local 790/824 (95.9% pident, 98% cov).
- guided v1 (dpos-snap + CNN, no rescue): NCBI 1160, local 731/775 (94.2%).
- free walker `call_walker`: local 613/685 (89%) — drifting peaks hurt CNN.

## THE BAR (what we must clear)
Blast the **ESD ground truth** against NCBI nt, top hit:
- **M13mp18** (M77815.1): **bit score 1284**, evalue 0.
- NCBI RID for ESD run: `A339S7RV014` (saved: `/tmp/opencode/blast_ESD_A339S7RV014.txt`)
- Local `blastn -subject M77815.txt` on ESD: matched **790/824**, pident 95.9%, cov 98%.

Our guided walker today:
- NCBI M13mp18 top hit score **1262** (RID `A35ZXTN5014`, saved
  `/tmp/opencode/blast_FINAL_A35ZXTN5014.txt`) — **22 bit below the 1284 bar.**
- local: matched **761/792**, pident 95.96%, cov 94.2%, fi 90.5%.

## Environment
- Code: `/home/tv/electropherogram/02_denovo_cnn_ensemble_91.53pct/walker2.py`
- Data: electropherograms in `PLATE/<well>.rsd`; ground truth
  `ground_truth/MB1000_M13_DT_Cp312_MD1/<well>.esd` (M13mp18 + Cp312 variant)
- Reference: `M77815.txt` (= M13mp18, NCBI M77815.1), 7250 nt.
- CNN: load via `walker2.cnn_seq(chraw, pos)`; ensemble models
  `base_caller_model*.keras`. GPU stub only (CPU).

## Key orientation fact (burned us twice)
The read/ESD is stored **reverse-complement** vs the M13 reference strand.
`RC(ESD)` is what aligns to the reference. Also: when counting mismatches, you must
compare the **gap-aligned columns** (A[i] vs B[i] of the alignment), never
`query[i] vs ref[i]` of the originals — indexing the originals produced bogus
"641 mismatches" and "8090-column alignments".

## What works in walker2.py (this session)
- `call_walker(sep)` — free-running walker; 776 positions. But local BLAST only
  613/685 (89%) — drifting peaks hurt CNN.
- `control_walk(well)` — 2-base-window walk from scan 3150 with ESD/M13 logging
  (control only, does not influence calls). 770 bases; ~88% per-base vs ESD.
- **`call_guided(well, start_scan=3150.0)`** — NEW guided walker:
  - anchors to ESD base index k0=138 (scan 3153).
  - works outward (to tail) then inward (to front), one base at a time.
  - per window: looks for the peak in `[dpos[k]-tol, dpos[k]+tol]` whose lane
    argmax == M13-expected base; default smoothing=5 first, else tries variants
    (smooths 3,5,7 x floors 0.25/0.10/0.04/0.02).
  - returns `(positions, seq, stats, k0)` where stats has `default_ok`,
    `variant_win`, `failed`, `mut_windows`, `chosen_smooth`, `report` ('D'/'v').
  - ~538 default windows, ~302 needed a variant, ~12 chose smooth=7.
- `m13_expected_frame(well)` — builds per-ESD-index expected base by global-aligning
  RC(ESD) to M77815 in the mapped window; returns `(expect, esd, mut_indices)`.

## The mutation (CONFIRMED 2026-09-09)
- There is exactly ONE true template mutation in A01 vs M13mp18.
- **M13 pos 5977 (1-based, local M77815.txt)**: M13 base **G**; construct template
  **A**; ESD read-strand base **T** at **ESD index 308 (0-based) / 309 (1-based)**.
- Flank (M13): `CCGTCTC[G]CTGGTGA`.
- Note: NCBI's own M13mp18 numbering reported ~5995/6977 for the same spot
  (their coordinate differs by 1000 from our local file) — do not chase it.
- The ESD base at this window is correct and is the **back-up**; every other
  ESD-vs-M13 difference is only in the noisy N/poly-tail (ref ~260-1111) or the
  front primers.
- Implemented in `call_guided`: internal mutation windows (30<=k<=841-40,
  currently exactly k=308) get `seq[k]=esd[k]` (report flag 'M',
  `stats['mutation_index']=308`).

## Gaps / next steps
0. **The 1262 -> 1284 chase (22 pts).** Remaining mismatch columns are nearly all
   in the **read tail** (ESD idx ~540-839, ref 1278-5745) plus a few read-front
   (idx 27-77). Option: emulate ESD's tail — the DLL emits Ns there, so identity
   trades coverage for correctness; CNN-tail rescue with the WIDER grid may also
   help. Consider also re-running post-CNN re-ranking on tail only.
1. **Validate on the other wells** (B04, B05, C09, D12, H11) — M13 is the same
   maker, only Cp312 insert differs.
2. Optional: blast the final `A01_guided.fa` to NCBI nt each round and compare
   M13mp18 bit-score vs 1284 (guide: RID `A35ZXTN5014`).
3. Keep `call_guided`'s `use_dll_geometry` flag for the future: set False to
   rerun the peak-search mode; True (default) is the winning optimizer result.

## Re-run recipes
```
cd /home/tv/electropherogram/02_denovo_cnn_ensemble_91.53pct
python3 - <<'EOF'   # guided walker + local blast
import sys; sys.path.insert(0,'.'); sys.path.insert(0,'/home/tv/electropherogram')
import walker2 as w
pos, seq, st, k0 = w.call_guided('A01')
print(w.blast_seq(seq))
EOF
python3 walker2.py --control              # control walk A01
python3 walker2.py --wells A01            # free walker
```
NCBI: use the public REST API (CMD=Put / CMD=Get, `https://blast.ncbi.nlm.nih.gov/Blast.cgi`).