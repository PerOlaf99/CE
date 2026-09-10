# 05 — Pure-Python MegaBACE basecaller port + Cimarron 3.12 ground-truth analysis

This folder is the *pure-Python* port of the Cimarron-style basecalling pipeline
(`megabace/` package) plus the ground-truth (Cimarron 3.12 `.abd`) analysis and
progress reports produced while validating it against the commercial caller on
the `MB1000_M13_DT` plate.

It is additive: nothing in `01_..`–`04_..` or the repo root was modified.

## Contents

| path | what |
|---|---|
| `megabace/` | the port: `rsd.py`, `signal.py`, `spectral.py`, `basecall.py`, `fuzzy.py`, `utah.py`, `simulate.py`, `cli.py` |
| `tests/` | `pytest` round-trip tests (`pytest` must stay green) |
| `pyproject.toml` | package metadata / `rsdbasecall` entry point |
| `PORT_NOTES.md` | **main running progress log** (every experiment, metric, finding, dead end) |
| `reference/` | `m13mp18.fasta` reference + small per-well fasta used in alignments |
| `analysis/` | diagnostic / experiment scripts (`gt_eval.py`, `regen.py`, `diag_*`, `exp_*`, `sweep_*`, …) and small C probes |
| `reports/` | `validation_report.csv`, `cimarron_gt_report.csv`, tuning sweeps (`*.out`, `*.log`) |
| `cimarron_calls/` | per-well Cimarron 3.12 ground-truth FASTA extracted from the `.abd` files |
| `basecalls/` | the port's per-well FASTA output at the time of these reports |

Large raw instrument data (`*.rsd`, `.abd`, `.esd`) is intentionally not
duplicated here — it is already in `MB1000_M13_DT/` and `ground_truth/`, and is
covered by `.gitignore`.

## Goal

Reproduce Cimarron 3.12 basecalling in pure Python and match/beat it on the
M13 `MB1000_M13_DT` plate, validated against Cimarron's own output (`SVER`
tag = `Cimarron 3.12`, `PDMF` = `ET Terminators`).

## Status (see `PORT_NOTES.md` for the full record)

Metric = full-read identity vs the M13mp18 reference via the shared seed-SW
alignment used everywhere in this repo.

| set | Cimarron 3.12 (GT) | this port (baseline) |
|---|---|---|
| 43 wells A01–D07 (available `.abd`) | mean 96.84%, median 97.11%, mean read 873 bp | mean 94.03% (same metric) |
| full 63-well set | — | mean 93.90 / median 93.82, mean ~706 calls |
| A01 control | 841 bp, 95.39% | 694 calls, 93.2% |

Gap anatomy: the port is ~2.8 points behind on the 43-well GT set. Errors are
deletion-dominated; the read starts ~60 bp late at the 5' end and, more
importantly, stops ~190 bp early at the 3' end (aligned reference span ~248 bp
shorter than Cimarron).

## Key ground-truth findings (round `diag_tail5`, see `PORT_NOTES.md`)

- The port's `.rsd` raw channels are **point-identical** to the ABD raw DATA
  channels (corr 1.000): TGCA → ABD `DATA` T=4, G=3, C=1, A=2. Same data as
  Cimarron used, tail included.
- Cimarron GT is effectively **perfect** (0 substitutions in every sampled
  well; errors are ~24 indels/read only), so the far 3' tail is cleanly
  callable in the data.
- The port's ~169 "junk" tail peaks are **not noise**: ~70% fall within ±5
  scans of Cimarron-predicted positions at template density; ~1/3 of GT tail
  bases are missed; letters there are only ~63% correct.
- Dead ends confirmed: shrinking the baseline window (+15 bp only),
  `tail_extension` (garbage), `mobility_correct` (catastrophic: A01 97.6→74.4%).
- `DATA(9..12)` are Cimarron's separated dye signals indexed by `PLOC`
  (per-base row order `C,A,G,T`), and `MTRX.1 == MTRX.101` is the stored 4×4
  matrix — useful for replicating Cimarron's colour separation exactly.

## Next steps

1. Use the ABD `MTRX` matrix and `DATA(9..12)`/`PLOC` separation as a
   reference to correct the port's `spectral.py` deconvolution, especially in
   the 3' tail.
2. Recover the missing ~1/3 of tail bases and their positions.
3. Then tackle the 5' start lag (~60 bp).
4. Re-run `analysis/regen.py` and refresh `basecalls/` + `validation_report.csv`
   after any change; keep `pytest` green.
