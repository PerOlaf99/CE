# Clean-stretch gap vs Cimarron 3.12 DLL — findings (2026-09-17)

## Question
Production caller beats DLL on bitscore (1290.5 vs 1282.0) and matched bp
(818.6 vs 754.8) but loses badly on longest-clean-stretch (449.6 vs 577.3).
What is the DLL "magic" that yields 120 bp more error-free stretch at equal
bit score?

## Conclusion (short)
1. **Not** read length, not phantom-base suppression, not wholesale DSP.
2. It is **base-call identity in ref `[5600,5800)`**: ours 10.1% error there vs
   DLL 5.2%. Both callers are equally bad in `[5400,5600)` (29.4% vs 32.9%)
   and equally good in `[5800,6200)` (0.1% vs 1.5%).
3. Every DLL-wins position in `[5600,5800)` is a *substitution* at a base both
   reads reach. There are **no** positions where the DLL reads further into
   that clean window than we do.
4. Trimming our read to DLL length does not move clean (449.6 -> 449.6).

## Evidence

### Error density by 200-bp ref bin (held-48, ours vs DLL)
| ref bin   | ours %err | dll %err |
|-----------|-----------|----------|
| 5400-5600 | 29.4      | 32.9     |
| 5600-5800 | 10.1      | **5.2**  |
| 5800-6000 | 0.2       | 1.5      |
| 6000-6200 | 0.1       | 1.1      |

### Phantom suppression (option 3) is a dead end
- Production reads have **no true insertions**: windowed affine NW finds 0.
- Deleting the 20-70 spurious full-reference "insertion" columns from the
  linear `sw_align` DESTROYS clean/bits (449 -> 327, 1290 -> 1209) -- those
  columns are alignment artifacts, not phantom bases.
- The clean metric breaks the run at every gap column, so phantom-free reads
  get no boost.

### BLAST ground truth (NCBI RID AJ3GUSX1014, A01 baseline-tuned read len=947)
- Score 1286 bits (696), Identities 801/849 (94%), Gaps 17/849 (2%).
- 48 errors total = **31 mismatches + 9 insertions + 8 deletions**.
- In ref window 5597-5745: 9 errors = 5 mismatches + 2 insertions + 2 deletions.

### Affine (BLAST-faithful) longest-clean, ours vs DLL
| well | ours_aff | dll_aff |
|------|----------|---------|
| A01  | 459      | 699-714 |
| B04  | 369      | 725     |
| G07  | 345      | 668     |
| held-48 mean | 476.4    | 696.5   |

Affine alignment does not close the gap either; DLL is *even* cleaner when
measured BLAST-faithfully.

## Next move if this is revisited
- The only lever left in `[5600,5800)` is single-base call accuracy. Compare
  DLL/ours base letters column-by-column at the ~29 DLL-wins substitutions to
  look for a systematic pattern (dye bias / spacing / phase in that window).
- dll_peakdet.py (faithful DLL peak-detector port, validated on A01: 791/841
  peak positions) remains an unexplored trace-level lever.