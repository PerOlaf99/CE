# MegaBACE ET basecaller (unified)

One Python engine (`cimarron_basecaller.spacing_caller.track_bases`) with
**instrument × mode** configs — not four separate codebases.

| Preset | Instrument | Mode | Intent |
|--------|------------|------|--------|
| `mb1000_accuracy` | MegaBACE 1000 | accuracy | Longest error-free run, high ID |
| `mb1000_length` | MegaBACE 1000 | length | Longest usable read at ID ≥ 95% |
| `mb4000_accuracy` | MegaBACE 4000 | accuracy | Same goals + MB4000 spectral CHM |
| `mb4000_length` | MegaBACE 4000 | length | Length mode + MB4000 CHM |

Evaluation gate for both modes: **identity ≥ 95%** vs reference (e.g. M13 M77815.1).

## Quick start

```bash
pip install -r requirements.txt

# MB1000 accuracy (default)
python run_basecall.py example_data/A01.rsd --instrument mb1000 --mode accuracy -o out.fasta

# MB4000 length mode
python run_basecall.py /path/to/well.rsd --preset mb4000_length -o out.fasta

# Show resolved knobs
python run_basecall.py well.rsd --preset mb4000_accuracy --describe
```

## CLI

```
--instrument {mb1000,mb4000}
--mode       {accuracy,length}
--preset     mb1000_accuracy | mb1000_length | mb4000_accuracy | mb4000_length
--config     legacy: pos_bonus07 | pos_profile | any preset name
-o           output FASTA
```

## Layout

```
configs.py                 # resolve_config(instrument, mode)
run_basecall.py            # CLI
assets/MB4000_CHM.npz      # supervised spectral matrix for 4000
cimarron_basecaller/       # shared library
```

## Notes

- Dye order for these ET plates: **TGCA** (handled in `to_acgt_trace`).
- MB4000 uses `assets/MB4000_CHM.npz` (`supervised`); MB1000 uses built-in `DEFAULT_CHM`.
- `accuracy` ≈ former `pos_bonus07`; `length` ≈ former `pos_profile` + mild mid hard-zone.
- Mobility default: `[-2, -1, -2, 2]` for A,C,G,T on both instruments.

## Experimental: mid-zone A/C HP-split head (Phase A)

```bash
python run_basecall.py well.rsd --preset mb4000_accuracy --hp-split
```

- Module: `cimarron_basecaller/hp_split_head.py`
- Model: `assets/hp_split_ac_mid.npz` (logistic, ESD-supervised partner search)
- Default threshold **0.90**, max 2 inserts — lower thresholds **hurt longest_run** on MB4000 holdout

**Status:** research only. ESD partner labels over-fire; matched_bp stable but longest_error_free drops when inserts increase. Classical `accuracy`/`length` modes remain the production path.

## Accuracy mode ≈ MonkeyCode precision

`mb*_accuracy` now uses:
- `gaussian_recon_noise_reg = 0.128` (stronger Wiener; plate-optimal ~0.12–0.13)
- `trim_quality_percentile = 38` (deep quality trim)

On a 96-well MB1000 M13 plate, that lineage reported ~98.2% mean ID and ~473 bp mean longest error-free run (vs Cimarron ~96.8% / ~491). Matched-base count drops because of trimming — use `length` mode when total span matters more than pure error-free length.
