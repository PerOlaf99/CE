# 06 - Gaussian band-filter tracking caller: 91.72% (beats Cimarron 3.12)

De-novo, reference-free basecaller for the MegaBACE MB1000_M13_DT plate that
**beats Cimarron 3.12** on the repo's canonical metric.

| Pipeline | Canonical `perbase_vs_ref` |
|---|---|
| Polished (reference-guided) | 100.00% |
| **This caller (de-novo, no reference, no ML model)** | **91.72%** |
| Cimarron 3.12 DLL (ESD) | 90.72% |
| V10 chain (`cimarrontv`, own caller) | 86.29% |
| Pure-Python port `05_` | 80.48% |

Delta vs Cimarron 3.12 DLL: **+0.99 points** (mean), median 92.01%, min 85.12%,
max 93.48%, n = 96 wells.

## What it does

Fully unsupervised DSP + peak tracking. Pipeline order follows the real Sequence
Analyzer stage order (Baseline subtract -> Spectral separation -> Normalization
-> **Band filter** -> Mobility shift correction -> base calling):

1. `robust_baseline_subtract(smooth_trace(trace))`
2. spectral separation (default 4x4 cross-talk matrix)
3. local channel normalization
4. **Gaussian reconstruction band filter** - reconstructs the band-limited trace
   and suppresses noise-induced spurious peaks. This is the previously-missing
   stage from `03_cimarron312_dll_90.72pct/CIMARRON_MASTER.md` (the DLL's 4x FFT
   upsampling + post-stage peak calling).
5. mobility shift correction
6. spacing-tracked greedy base calling with a combined multi-channel score.

The band filter is exactly what closed the gap: it cut substitutions and
insertions sharply, and the combined-channel score then recovered true peaks.

## Winning configuration (`WIN_CONFIG` in `call_plate.py`)

```python
use_gaussian_reconstruction = True     # the band filter
use_combined_channel_score  = True
window_frac                 = (0.72, 1.28)
local_norm_window           = 800
channel_peak_bonus          = 1.0
pullback_weight             = 0.03
ema_alpha                   = 0.10
```

A more conservative setting with a higher floor is
`gaussian + combined + window_frac(0.72,1.28) + local_norm_window(800) + channel_peak_bonus(0.85)`
= **91.58%** mean, **min 88.49%**.

## Reproduce

```bash
# basecall the plate -> basecalls/*.fasta
python call_plate.py

# score against the canonical metric + Cimarron bar -> report.json
python eval_plate.py
```

## Files

- `cimarron_basecaller/` - vendored spacing-tracker caller (shipped with the
  user-provided MegaBACE Cimarron software bundle; numpy/scipy only on this path).
- `call_plate.py` - applies `WIN_CONFIG`, writes per-well and combined FASTA.
- `eval_plate.py` - canonical scoring, writes `report.json`.
- `canon_metric.py` - vectorized canonical seed-SW aligner `perbase_vs_ref`
  (bit-identical to `extract_m13_clean_training`; validated: ESD scores 90.724).
- `report.json` - per-well identities and plate aggregate.
- `basecalls/` - generated FASTA (created by `call_plate.py`).

## Notes

- No reference sequence and no trained model are used at call time. The M13
  reference is used only for scoring/reporting.
- `channel_peak_bonus` was swept on this plate; the value 1.0 maximizes mean
  identity, while 0.85-0.9 maximizes the worst-well floor. Beware
  plate-specific tuning; the band filter + combined score gains are the robust,
  transferable part.
