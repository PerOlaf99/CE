# NEXT SESSION — handoff / progress list
(USB workdir: /media/tv/78B0C7DE1FA7081C1/electropherogram/02_denovo_cnn_ensemble_91.53pct)

## Where the session ended (all verified, plate means of 96 wells)
|             | bases | matched_bp | cov% | id%  | fi%  |
|-------------|-------|-----------|------|------|------|
| DLL-ESD     | 867.4 |    753.3   | 87.8 | 96.8 | 86.9 |
| cfg1 .50/.70| 783.5 |    695.7   | 91.6 | 94.3 | 88.8 |
| cfg3 .40/.60| 805.0 |    703.6   | 90.7 | 93.9 | 87.4 |
| REFINED (prod) | 722.4 | 660.2   | 91.6 | 95.8 | 91.4 |

Headline: the MERGE pipeline (full DLL-length register + our CNN confidence)
  - BEATS DLL on identity and coverage (fi 88.8 vs 86.9, cov 91.6 vs 87.8)
  - BEATS our own production REFINED by +36..+44 matched_bp
  - still LOSES the acceptance metric matched_bp (696/704 vs DLL 753)
Gate to 753 = our ~4% in-HSP error, ~94% indels (doublets + tail drift).

## Decisions locked this session
- Route B (pure clone of pass-2) REJECTED as orthogonal; envelope=candidate-
  set-only confirmed by evidence.  Route chosen: length+identity merge.
- Fine-centering / jitter-retrain: DE-PRIORITIZED (probe showed +0.4 fi only).
- Acceptance protocol stays: BLAST matched_bp plus our fi/cov as a secondary
  "we beat DLL on identity+coverage" argument.

## Artifacts (all live on this USB)
- merge_plate.py, merge_plate_rows.csv, merge_plate.log   <- 96-well MERGE result
- merge_probe.py, merge_probe_rows.csv, merge_probe.log   <- 6-well config sweep
- probe_port2.py, probe_port2.log                         <- centering probe
- reproduce_dll.py, reproduce_dll_rows.csv                <- PORT/REFINED/DLL 96w
- blast_v2tail.py, sweep_tail.log                         <- configurable BLAST
- dll_peakdet.py, re_artifacts/{decomp_all.c, classify_fuzzy.py}  <- decoder ring
- perfect_basecaller.py                                   <- CNN + refine_denovo
- SESSION_LOG_perfect_basecaller.md                       <- full narrative

## PROGRESS LIST for next session (in recommended order)
[ ] 1. Sanity: files listed above all present; `python3 -c "import perfect_basecaller"`
        works; rerun nothing yet.
[ ] 2. MEASURE the indel structure of a merged read (cfg1 on A01 once).  Global
        align merged read vs M13 reference; tag every site as match/insert/delete.
        Count: (a) gaps in head+middle vs tail; (b) runs of adjacent insertions
        (doublets) vs isolated.  This tells us if 753 is reachable by cleaning
        vs by keeping-labels-smarter.  (minimap2 or edlib if available offline;
        else brute biopython pairwise2.)
[ ] 3. Attack 1 - kill doublets BEFORE labelling: on the full-register candidate
        list, merge envelope peaks closer than ~0.5*median spacing (dedup exact
        pairs), then CNN-label the cleaned set; rerun cfg1 BLAST on 6 wells.
        Target: matched affects only, fi unchanged.
[ ] 4. Attack 2 - OKN-gate the tail: port classify_fuzzy.py (FUN_10012140) and
        drop tail candidates that the OKN would not keep (shoulder/quiet test)
        instead of our phred-based retain.  Compare vs cfg3 on 6 wells.
[ ] 5. Attack 3 - DLL-exact positions for the tail: use DLL trace 'record' spacing
        in the tail region (> cfg end bgn), label those record centers with our
        CNN.  Tests the hypothesis 'positions, not labels, cap us at ~712'.
[ ] 6. If any attack pushes 6-well mean matched >= 745: run full 96-well merge
        with that pipeline (reuse merge_plate.py skeleton), deliver final table
        DLL vs MERGE-v2 vs our REFINED, and the verdict.
[ ] 7. If NONE crosses ~745: declare and ship the honest result - we match DLL
        length within ~8%, beat identity by ~2% and coverage by ~4%, matched_bp
        -50..-58 due to ~4% indel residue in long-read tails; present with the
        implied-precision argument if acceptable, then STOP.
[ ] 8. Log every step's numbers in SESSION_LOG_perfect_basecaller.md.

## Gotchas (repeat offenders)
- NO pkill -f 'python3...'; it kills the outer bash shell.  Use pgrep -f only.
- Background jobs: setsid bash -c 'exec python3 -u X.py > X.log 2>&1' </dev/null >/dev/null 2>&1 & disown
- CNN ensemble eats the RAW 4-dye trace (cim.read_rsd -> ch.T), never cache_sep lanes.
- spawn workers lose main() globals -> pool initializer must (re)import perfect_basecaller.