# GOLDEN STANDARD — how we measure a basecalled read (ALWAYS use this)

> **THE golden standard is NCBI BLAST of the called read against M13mp18
> (M77815.1).** Every result, experiment, iteration, and "did we win?" decision
> is judged by the numbers produced by `blast_eval()` in
> `sanger_toolkit/blast_bench.py`, applied to BOTH the DLL/ESD read and OUR read
> with the *identical* pipeline so they are directly comparable.
>
> **Do not substitute** span identity, CNN val-accuracy, "agreement %", or any
> local diff for the BLAST bar.  Those are diagnostics.  The match that counts
> is NCBI-BLAST's `matched_bp` (matched = aligned − mismatches − gaps).
>
> Two acceptance bars, both on the SAME blastn HSP:
>   1. **`matched_bp`** — how many reference base pairs the read gets right
>      (THE metric; reward for emitting real bases, esp. the tail).
>   2. **`longest_error_free_run`** — the longest consecutive stretch of
>      error-free columns (reward for a CLEAN read).  The known template mutation
>      (M13 fwd 5977) is excluded as NEUTRAL: the called T there neither counts
>      nor breaks the run, so a clean read crossing the mutation site is not
>      penalized (this is the "longest error-free read, SNP not counted" bar).
>
> Reference: `sanger_toolkit/refs/m13_M77815.1.fa` (M13mp18, 7250 nt).
> Commands: `blastn -task megablast` against `makeblastdb` of that reference.

---

## The five headline numbers (all from the SAME blastn HSP)

| metric | symbol | meaning | why it matters |
|---|---|---|---|
| **bases called** | `bases_detected` / `qlen` | number of bases in the read we hand to BLAST | how much we emit (recall) |
| **aligned** | `aligned` | length of the single best HSP (platform) | how much of our read lines up |
| **coverage** | `coverage` | `(qend−qstart+1)/qlen` × 100 | fraction of OUR read inside the HSP |
| **identity** | `pident` (BLAST) | `matched/aligned`; gaps-free matches vs the aligned platform | BLAST's own quality number |
| **matched_bp** | `matched` | `aligned − mismatches − gaps` | **THE acceptance metric** |
| **longest error-free run** | `longest_run` | longest consecutive run of matching columns on the same HSP, **M13 fwd 5977 excluded as neutral** | clean-stretch bar; read must be right for LONG, not just for MANY |

Longest-run rule (2026-09-16): use the gapped HSP columns
(`blastn -outfmt "6 ... qseq sseq"`, best-bitscore HSP), not a re-alignment;
a column is a match iff `qseq[c]==sseq[c]` and neither is a gap; the known SNP
column (the one whose forward coordinate == 5977) is skipped so it neither
counts nor breaks the run.

Plus ancillary from the same record:
- `full_identity` = `matched / bases_detected` × 100 (matched_true / everything we emitted).
- `bitscore`, `mismatch`, `gapopen` — secondary diagnostics.
- `m13_start`–`m13_end` — where on M13 our read landed (orientation: reads are
  stored reverse-complement, so the reader may appear as Minus strand).

**Priority when reading results:** (1) `matched_bp` (THE bar), (2) `coverage`,
(3) `identity`, (4) `bases_detected`, (5) `longest_run` (clean-stretch bar).

---

## A01 walk-through (concrete, from `blast_eval()` on 2026-09-14)

Caller = **Cimarron 3.12 DLL** (the `ground_truth/.../A01.esd` read) — this is
the goal we chase.

```
DLL A01  bases=839  matched=790  full_id=94.16%  (pident=95.39)  cov=95.35%
        (M13 5471-6286)  bitscore=1282  aligned=824  mismatch=6  gaps=28
```

How to read this exact record:

- `bases=839` — the ESD read has 841 bases total but 2 are N (beyond the callable
  region), so 839 non-N bases are handed to blastn.  **catalogued = 841,
  blastable = 839.**
- `aligned=824` — the best HSP spans 824 columns on M13 (5471→6286).
- `coverage=95.35%` — 800 of our 839 emitted bases fall inside that HSP
  (`805−6+1=800`; the read's first ~5 bases and last ~34 are unaligned, they are
  front-primer / dead-tail).
- `identity=95.39%` — BLAST counts `790/824` aligned columns equal (6 mismatches,
  28 insertion gaps: `cow aligned − mismatch − gapopen=790`).
- **`matched=790`** — this IS the DLL target number.  Every experiment must be
  quoted vs **790 on A01** and vs the 48-well mean (DLL 754.8).
- `full_id=94.16%` — 790 matched out of 839 emitted (the strictest, penalizes
  unaligned tail).
- `longest_error_free_run` **= 506** (fwd 5719→6226 on the same HSP).  The two
  flanking runs on either side of the mutation site (fwd 5977) merge into one
  506-base clean stretch once the SNP column is excluded; without exclusion the
  raw run is 257 (the read's own T at 5977 is a mismatch vs the RC-of-G C).

### Our best de-novo A01 for contrast (the gap we are closing)

| caller | bases | aligned | coverage | identity | **matched** |
|---|---|---|---|---|---|
| **DLL 3.12 (goal)** | 839 | 824 | 95.35% | 95.39% | **790** |
| v8 corrector ceiling (DLL positions) | — | — | — | — | **710.8** (48-well mean) |
| v9 weekend de-novo (adaptive-window CNN) | 848 | — | — | 91.6 | **609.6** (48-well mean) |
| v9 + corr (48-well mean, finished 09-14) | 848 | — | — | 92.0 | **613.6** |
| DLL-position ceiling (v8, 48-well mean) | — | — | — | — | **710.8** vs DLL 754.8 |

**Summary of the mountain:** 1 base pair = 1 unit.  A01: DLL 790, our current
de-novo pipeline lands ~625-650 (v6+region+v8/corr), v9 weekend regressed to
609.6 (adaptive-width CNN needs the corrector).  The whole project is judged by
these `matched` numbers from the SAME blastn path, well by well.

---

## The 48-well acceptance statement (how we declare "WIN" / "FAIL")

- Run `blast_eval()` on the DLL ESD read AND on OUR de-novo read for all 48
  held-out wells (the `v3_training.npz` `split==0` wells).
- Compute the mean `matched_bp` for each.
- **Accept = our 48-well mean `matched_bp` ≥ DLL 48-well mean (754.8).**
- NEVER average CNN probabilities or identities across wells as a proxy —
  average the per-well `matched` values.

Current status (recorded here so it never gets lost):

```
DLL 3.12 (48 wells) ........ mean matched = 754.8
OUR v8 corrector ceiling ... mean matched = 710.8   (DLL positions + corrector)
OUR v9 weekend (de-novo) ... mean matched = 609.6   (regression — needs corr)
OUR v9 + corr (de-novo) .... mean matched = 613.6   (+4, still below v8)
v3 CNN (48-wells, 2026-09-11) mean matched = 701.3
ESD (span: the reference for per-column) ... 99.94% identity on same columns

WEB 2026-09-15 (external "best_basecaller", de-novo DSP, NO model)
     mean matched = 767.98  (48 wells, >= 754.8 -> PASSES the bar; beats DLL 32/48)
     mean bases = 918.6, mean fullid = 83.60% (DLL 869.7 / 86.79%)
     calls in 02_denovo_cnn_ensemble_91.53pct/bestweb_calls/ (whole 96-well plate
     also done: 73,523 matched total, 765.9 mean, 0 unaligned).
     Why: it emits a LONGER read whose tail is real M13 (+14 matched) at the
     cost of identity (fullid 83.6 vs 86.8).  Same lesson as the tail-zone null.

TUNED 2026-09-15 (quality-gated pullback sweep, tuned_basecaller.py): pullback
     0.019 -> 0.012 extends the tail match further (+26/piece) but collapses a
     few wells into low-quality tracks; gated by mean base qual (fall back to
     0.019) -> 96/96 wells aligned, no oracle:
       held-out 48 ... mean matched = 793.42  (fi 83.25, pident 94.55)
       whole 96 ....... mean matched = 792.62  (fi 83.10, pident 94.44)
       DLL bar ........ 754.81 held / 753.28 plate  -> beats DLL ~39 mean.
     A01 = 801 matched (947 bp) > DLL 790.  Best de-novo result to date.
     (release-pack "track_bases" config, cp_bonus=1.1/baseline 201/adaptive
      spectral, reproduces 765/801 on A01, is WORSE under this bar: held 756.)

TUNED-FINETUNE 2026-09-15 (bitscore-objective sweep, mb1k_window_sweep.py):
     New objective: BLAST bitscore (rewards length AND identity; the earlier
     matched-only sweep picked longer-but-dirtier reads that trailed bitscore).
     Config: pb 0.008 / ema 0.08 / channel_peak_bonus 1.4, gate 2.4.
       held-out 48 ... bits = 1282.58  matched = 796.77  id = 94.75%
       other 48 ..... bits = 1275.54  matched = 787.31  id = 94.95%
       whole 96 ..... bits = 1279.06  matched = 792.04  id = 94.85%
       old tuned .... bits = 1262.41  matched = 792.62  id = 94.44%
       DLL (held) ... bits = 1282.00  matched = 754.81  id = 96.81%
       -> bits tied DLL (+0.6), matched +42, id -2.1 (caps at mutants).
     Gate 2.4 catches G03's long-but-messy read (1093bp, q=2.25, bits 1079) and
     falls back to the base read (1012bp, bits 1081, matched 842) - same as DLL.
     Only pullback/ema/bonus move bitscore; window_frac/local_norm flat.

POSITION-PROFILE 2026-09-15 (track_bases pos_profile, mb1k_posprofile_sweep.py):
     Honest replacement for the abandoned windowed tail splice: parameters are
     now a function of read position (linear interp of ema/pullback/min-prom/
     bonus vs scan-fraction; byte-identical to scalar config when flat).
     Error localization -> tail third carries 63% of errors; the killer was
     NOT error-rate but tail SPACING divergence from the mid-read global
     median - pulling back toward it there loses tail bases.  Profile: loosen
     pullback 0.008 -> 0.001 across the last 2/3 of the read (frac 0.33).
       held-out 48 ... bits = 1290.54  matched = 818.60  id = 94.00%
       other 48 ..... bits = 1277.12  matched = 813.58  id = 93.87%
       whole 96 ..... bits = 1283.83  matched = 816.09  id = 93.94%
       flat (pre) ... bits = 1279.06  matched = 792.04  id = 94.85%
       DLL (held) ... bits = 1282.00  matched = 754.81  id = 96.81%
       DLL (plate) .. bits = 1278.3   matched = 753.3   id = 96.8%
       -> beats DLL on BOTH metrics on BOTH splits: held bits +8.5,
          matched +64/well; plate bits +5.5, matched +63/well.
Fast-EMA tails, loose-prominence, and bonus ramps all lost; only the
        pullback ramp helped.  Tail error-rate unchanged (~8.4%) - gains are
        recovered tail length, not cleaner bases.

COMBINED 2026-09-16 (track_bases pos_profile + refine_denovo_v2 add-only):
     Full 96-well plate on the golden bar.  Tested four fusion styles on 6
     worst/first wells + full plate:
       - greedy + tuned refine_v2 .......... 648.8 mean   (CNN gap-fill from
         engine greedy start; tail recovery poor -> LOSES to DLL)
       - track_bases alone (tuned_calls) ... 816.09 plate mean (91/96 > DLL)
       - track_bases + refine_v2 add-only ... 816.65 plate mean (+53 matched,
         30 wells gain, 0 wells loss)  <- BEST
       - track_bases + CNN re-label ........ destroy (CNN was trained on
         greedy-engine peaks; DSP band positions score low -> -100..-200)
     => The CNN ensemble cannot re-label DSP-positioned bands (hurts).  Its
        only safe use on top of track_bases is the no-drop gap-INSERTION pass
        (+0.07% matched, no losses).  SHIP: tuned_calls/.
        Calls: 02_denovo_cnn_ensemble_91.53pct/golden_plate_calls_trackBrefine/
     Final plate standings: track_bases 816.09 / trackB+add-only 816.65 /
     DLL 753.28.  Margin over DLL ~ +63 matched/well (+8.4%).
     Mutation internal standard survives BOTH outputs in all 96 wells (T at
     fwd 5977); the add-only refine inserts a few spurious homopolymer bases
     around the motif in some wells but the T residue is always present.

LONGEST ERROR-FREE RUN 2026-09-16 (SNP-neutral, same-HSP columns, 96-well
     plate; metric defined above):
       DLL ................ mean 398.1  med 375.5  min 228 max 626  (>500: 33w)
       track_bases ........ mean 286.5  med 280.5  min 114 max 590  (>500: 5w)
       trackB+add-only .... mean 213.6  med 210.0  min  93 max 335  (>500: 0w)
     Story: the two bars are complementary and DLL still leads ONE of them.
     matched_bp = total real bases recovered (trackB +63/well: longer tail).
     longest_run   = CLEANEST consecutive stretch (DLL +112/well: fewer
     scattered errors).  track_bases trades a few points of clean-stretch for
     a much longer true-positive read; the tail that wins matched_bp is
     precisely where its errors concentrate (~8.4% tail error rate), so its
     clean run is shorter.  A WIN against the DLL on BOTH bars simultaneously
     (matched_bp AND longest_run) is the eventual acceptance target.
```

---

## The mutation internal standard (independent of BLAST, always check it)

- Exactly ONE true template mutation.  Coordinates CONFIRMED 2026-09-16 by
  reference search + BLAST mapping (previous 5977-only note was imprecise):
  - **M13 forward pos 5977 (1-based, `m13_M77815.1.fa`) : reference base G.
    Sequence flank (fwd): `CCGTCTC[G]CTGGTGA` (G at 5977).**
  - The read-wildtype motif `CACCAGCGAGACGGG` STARTS at M13 fwd **5983** (the
    G flank continues into it); the sequencing/ESD read carries **T** at that
    site: read motif `CACCAG[T]GAGACGGG` (T is the 7th base, fwd 5977).
  - ESD read-strand base at **ESD index 308 (0-based, A01) = T** (M13 read-
    orient = C).  In the read it is a **C→T** transition (G→A on the forward /
    reference strand).
- A caller that reads the wild-type C here is WRONG about the construct.
- Track as "mutation called T in N/wells" (v3: 45/47; v4: 100%; v5: 36/37;
  track_bases pos_profile 2026-09-16: **96/96 — the T is preserved in every
  well**).

---

## Orientation & gotchas that have burned us (keep here forever)

1. **Reads are stored REVERSE-COMPLEMENT vs the M13 forward strand.**  `RC(read)`
   is what aligns; BLAST reports Plus/Minus strand.  Never compare
   `query[i] vs ref[i]` of the originals — must compare gap-aligned columns.
2. **BLAST identity (`pident`) is `matched/aligned` and IGNORES unaligned tail.**
   Coverage hides that.  `matched_bp` and `full_identity` do not.  Use all three
   together; never cheer a high `pident` while `coverage` is low.
3. **`blast_eval(sequence, task='megablast')` — the 2nd argument is the TASK,
   not a reference.**  Passing the ESD sequence there crashed blastn
   (CalledProcessError) when I first wired it.  Good call is `blast_eval(gui_seq)`.
4. **Length tricks don't win**: adding base runs (insertion columns, unmasked
   front, etc.) that don't match M13 *lower* `matched`.  Long read ≠ win.
5. **`matched` counts base pairs actually equal to M13.**  Over-detection
   (our lenient candidate set = 1217 vs DLL 841) destroys it (51.4% full_id).
6. **Clean Ns before BLAST** (DLL's own 841 rds → 839 blastable).  `blast_eval`
   strips non-ACGT internally; `bases_detected` reflects post-strip length.

---

## Reproduce

```
cd /media/per/78B0C7DE1FA7081C/electropherogram/sanger_toolkit
python3 blast_bench.py --wells A01 --no-cnn            # DLL ESD + independent caller
python3 blast_bench.py --wells A01                      # DLL ESD + CNN ensemble read
python3 eval_v8_esdpos.py                               # DLL-pos ceiling, 48 wells
python3 eval_v9_weekend.py --prefix base_caller_model_v9 --corr  # full v9 de-novo
```

Alternate (any single read): `python3 -c "import sys; sys.path.insert(0,'sanger_toolkit'); from blast_bench import blast_eval; print(blast_eval(open('reads.fa').read().splitlines(keepends=True)[1].strip()))`

Last refreshed: **2026-09-14** (Sep 11 weekend v9 run inspected, corr stage finished 09-11 16:xx).