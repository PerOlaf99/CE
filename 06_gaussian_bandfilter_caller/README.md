# 06 - Gaussian band-filter tracking caller

De-novo, reference-free basecaller for the MegaBACE MB1000_M13_DT plate.
It **calls more correctly-identified bases than Cimarron 3.12** when measured
with NCBI BLAST+ against the authentic NCBI M13mp18 reference (`M77815.1`).

## Headline result (96 wells, NCBI BLAST+ megablast)

| metric | ours | Cimarron 3.12 (ESD) | delta |
|---|---|---|---|
| **identical bases** | **73,462** | 72,286 | **+1,176 (+1.6%)** |
| **aligned length** | **77,136** | 74,726 | **+2,410** |
| mean % identity | 95.30% | 96.76% | **−1.46** |
| mean read length | 920.9 | 873.0 | +47.9 |
| total gaps | 2,226 | 1,967 | +259 |

We win on **total correct bases** (the objective this work was set) and on
aligned length, and lose on **average identity**, because we call longer reads.
The two callers sit at different points on the identity/coverage frontier; see
`BLAST_RESULTS.md` for why the total-base count is the honest comparison here.

For reference, the repo's canonical `perbase_vs_ref` ratio on this config is
**88.88%** vs Cimarron 90.72%. That ratio rewards shorter, cleaner reads and
does **not** track the number of correct bases, so it is reported but not used
as the objective.

## What it does

Fully unsupervised DSP + peak tracking. Pipeline order follows the real Sequence
Analyzer stage order (Baseline subtract -> Spectral separation -> Normalization
-> **Band filter** -> Mobility shift correction -> base calling):

1. `robust_baseline_subtract(smooth_trace(trace))`
2. spectral separation (default 4x4 cross-talk matrix)
3. local channel normalization
4. **Gaussian reconstruction band filter** - reconstructs the band-limited trace
   and suppresses noise-induced spurious peaks (the previously-missing stage
   from `03_cimarron312_dll_90.72pct/CIMARRON_MASTER.md`).
5. mobility shift correction
6. spacing-tracked greedy base calling with a combined multi-channel score.

The band filter plus the combined score plus a lower pull-back weight lets the
spacing tracker follow the broadening peaks in the degraded 3' end, which is
where Cimarron's original coverage advantage lived.

## Winning configuration (`WIN_CONFIG` in `call_plate.py`)

```python
use_gaussian_reconstruction  = True    # the band filter
gaussian_recon_segment_size  = 384
use_combined_channel_score   = True
window_frac                  = (0.75, 1.25)
local_norm_window            = 1800
channel_peak_bonus           = 1.6
pullback_weight              = 0.019
ema_alpha                    = 0.10
```

The result is robust: `pullback_weight` in 0.018–0.021 all beat Cimarron on
identical bases; `repeat_detection=True` nudges it slightly higher (73,479).
Do not assume the exact constants transfer to another plate; the band filter,
combined score and coverage tracking are the transferable parts.

## Reproduce

```bash
# basecall the plate -> basecalls/*.fasta
python call_plate.py

# authoritative BLAST+ comparison -> report_blast.json
BLAST_DIR=/path/to/ncbi-blast-*/bin python blast_eval.py

# canonical ratio + Cimarron bar -> report.json
python eval_plate.py
```

## Files

- `cimarron_basecaller/` - vendored spacing-tracker caller (shipped with the
  user-provided MegaBACE Cimarron software bundle; numpy/scipy only on this path).
- `call_plate.py` - applies `WIN_CONFIG`, writes per-well FASTA.
- `blast_eval.py` - NCBI BLAST+ comparison, writes `report_blast.json`.
- `eval_plate.py` - canonical scoring, writes `report.json`.
- `canon_metric.py` - vectorized canonical seed-SW aligner `perbase_vs_ref`
  (validated: ESD scores 90.724).
- `report_blast.json`, `report.json` - plate aggregates.
- `basecalls/` - generated FASTA (created by `call_plate.py`).

## Notes

- No reference sequence and no trained model are used at call time. The M13
  reference is used only for scoring/reporting.
- Earlier versions of this folder claimed a win on the canonical ratio (91.72%
  vs 90.72%). That was misleading: it counted fewer, cleaner bases. See
  `BLAST_RESULTS.md` for the corrected analysis.
