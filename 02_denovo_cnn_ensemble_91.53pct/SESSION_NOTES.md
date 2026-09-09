# Session notes — basecaller vs M13 (pick-up-the-thread doc)

Last updated: 2026-09-09

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