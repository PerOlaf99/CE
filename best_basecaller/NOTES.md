# Notes and validation

## What the caller is

De-novo, reference-free basecalling: DSP (baseline, spectral separation,
normalization, Gaussian band-filter reconstruction, mobility-shift correction)
plus spacing-tracked peak calling with a combined multi-channel score. The M13
reference is used only to score results, never to call bases.

## Plate result (96 wells, MB1000_M13_DT)

Scored with NCBI BLAST+ 2.17.0 `megablast` against NCBI M13mp18 (`M77815.1`),
best hit per read:

| metric | this caller | Cimarron 3.12 (ESD) | delta |
|---|---|---|---|
| identical bases | 73,462 | 72,286 | +1,176 (+1.6%) |
| aligned length | 77,136 | 74,726 | +2,410 |
| mean % identity | 95.30% | 96.76% | -1.46 |
| mean read length | 920.9 | 873.0 | +47.9 |
| total gaps | 2,226 | 1,967 | +259 |

The caller wins on **total correctly-called bases** and aligned length and
loses on **average identity**, because it calls longer reads. The two callers
sit at different points on the identity/coverage frontier.

For completeness, the repo's canonical per-base ratio on this configuration is
88.88% vs Cimarron 90.72%. That ratio favours shorter, cleaner reads and does
not track the number of correct bases.

## Configuration

`WIN_CONFIG` in `basecall.py`:

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

- `pullback_weight` (default 0.08) controls how strongly the running spacing
  estimate is pulled toward the global median. Lowering it to ~0.019 lets the
  tracker follow the broadening peak spacing in the degraded 3' end, which is
  where the extra coverage comes from. Values 0.018-0.021 all beat Cimarron.
- `channel_peak_bonus` (default 0.5) adds corroboration from independent
  per-channel peak detection. 1.6 works best on this plate.
- `repeat_detection=True` nudges the identical-base count slightly higher
  (73,479); left off by default.

Re-tune these two knobs for a different plate; the band filter and combined
score are the parts that transfer.

## Reproduce

```bash
python3 -m pip install -r requirements.txt
python3 test_smoke.py                      # runs a synthetic trace, no data needed
python3 basecall.py --input /path/to/rsd_dir --out calls
```

Then align `calls/*.fasta` to M13 (`M77815.1`) with megablast.
