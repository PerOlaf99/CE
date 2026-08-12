# HANDOFF — Basecaller task (continue at home PC)

Copy this folder (`electropherogram/`) to the home PC along with this file. Everything needed
is on this USB stick. Re-run the verification scripts below to confirm the state.

## Goal
Make the **independent basecaller** (no ESD dependency) reproduce ESD-quality basecalls.
ESD will eventually be unavailable, so the caller must not use ESD peak positions.
GUIDED / ESD-position basecalling was **rejected** by the user — keep it independent.

## Current state (DONE — do not redo)
- A Biopython-style **greedy max-intensity caller** was benchmarked and is now **integrated into
  the GUI**: `sequencing_gui_V15.py`.
- Algorithm (`pc_call_bases_greedy`, ~line 1031): per-channel rolling-normalize (norm_window=800),
  combine envelope = max across channels, repeatedly take global max, call argmax channel,
  excise ±window (5), stop when remaining max < min_frac (0.20) × region max.
- GUI has a **method selector** "Greedy (max-intensity) / Per-channel (cluster)" at the top of the
  Peak detection group (rows shifted +1). Presets: Greedy → dist 5, prom 200, norm 800;
  Per-channel → dist 5, prom 75, norm 2000. Dispatch in `_call_bases()`; routed through
  `_run_basecall` (~2977) and `_update_plot` (~3842). Fill-in (`pc_fill_in_combined_peaks`) runs
  ONLY for the per-channel method.
- Method is persisted as `basecall_method` in settings; legacy settings without the key get the
  greedy factory preset (migration). `load_settings_from_dict` / `get_settings` handle it.
- Headless verification passed; full 96-well plate via GUI code path verified.

### Results (greedy w5 mf.20)
| metric | greedy (new) | current per-channel |
|---|---|---|
| 96-well mean NW | **88.3%** | 81.1% |
| 96-well median | 88.6% | 81.6% |
| 96-well min | 83.0% | 70.3% |
| better on | **96/96 wells** | — |
| A01 | 87.1% (n=862) | 81.8% |

A01 error taxonomy (greedy w5 mf.20): match=771, sub=47, ins=23, del=44 (aligned=885).
ESD-position letter ceiling (argmax at ESD positions) = 95.1% → the caller is ~7 points below
what perfect positions would give.

## Why the remaining ~12% gap is NOT fixable by simple tuning (all tried)
1. **Channel balance — NOT the issue.** Raw A is healthy (raw medians at ESD positions:
   A=205, G=125, C=304, T=183). Substitutions are position errors, not amplitude errors.
2. **Letters are ~99% correct when position is right.** Position error is the entire gap.
3. **Position error is SCATTER, not bias.** Late-read per-channel medians stay ~0±1 scans
   (T worst late: 59% off >3, but not systematically shifted). → No mobility drift to correct;
   a linear/adaptive mobility model will NOT help.
4. **Root cause: late-read peak decay.** Envelope maxima become poorly defined. Greedy positions
   are within 2 scans of ESD 80% of the time, 84% within 3; late read: 34% off >3.
5. Tried and gave NO gain: dominant-channel apex refinement (±2/3/4), fill-in after greedy
   (deletions sit inside excise windows), adaptive local threshold (rolling 200/400/800),
   running greedy on ESD's own mobility-corrected traces (worse: 85.5 vs 88.6).
6. Greedy window sweep: win=4 → 81.9%, win=5 → 88.6%, win=6 → 86.8%. Window 5 is optimal.
   ESD peak spacing is p25=7 / p50=9 / p75=10 scans, so window 5 (excise 11) is NOT the limiter.

## Next steps / open decision (pick ONE)
- **A. Stop here** — greedy is integrated, 88.3% mean is a solid independent result. Set greedy as
  default method in GUI.
- **B. Attack late-read peak decay** — Gaussian/fit-based position refinement on the dominant
  channel in the decayed late read (larger effort, uncertain payoff; verify on 8-well + 96-well).
- **C. Reconsider ESD as position oracle only** (ESD positions + our letters). Previously rejected
  as ESD-dependent; only do this if the user relaxes that constraint.

## How to reproduce / verify (headless)
Requires PyQt5 (system python has it). Scripts live in `/tmp/opencode` on this PC — copy them.
- 8-well sweep/checker: `greedy_refine.py` (window/min_frac variants)
- 96-well verifier via GUI code path: `/tmp/opencode/gui_greedy_fullplate.py`
  (expect mean 88.3%, median 88.6%, min 83.0%)
- Standalone 96-well: `/tmp/opencode/greedy_fullplate.py`
- Parameter sweep: `/tmp/opencode/greedy_sweep.py` (NOTE: had a pick-order sort bug — fixed;
  calls must be sorted by position before NW)
- A01 taxonomy / offset analysis: inline scripts (offset pctiles, per-channel drift by read third)

## Critical context / numbers
- `CHEM_MAP`/`BASE_LETTERS` = {0:T, 1:G, 2:C, 3:A}
- Real bleed matrix: `[[0.8,0.55,0.04,0],[0,0.8,0,0],[0,0.5,0.75,1],[0.18,0.06,0.04,0.585]]`
- Best pipeline settings in `settingsV8.json`: AsyLS 50000/1, Butterworth 7/6, matrix apply
  corrected, esd_offset 1998, mobility [5,10,10,10]
- GUI greedy defaults: distance_spin=5 (=window), prominence_spin=200 (=min_frac 0.20),
  norm_window=800; `prominence_frac = prominence_spin/1000`
- ESD peak spacing percentiles: p25=7, p50=9, p75=10 scans
- NW identity uses match=1, mismatch=-1, gap=-2 (see `pc_nw_identity`)

## Environment gotchas
- Home PC system pip may be blocked (PEP 668). Biopython 1.88 is installed ONLY in
  `/tmp/opencode/benv` venv (which has NO PyQt5). `electropherogram` is NOT on PyPI.
  Data has no `.ab1` files — only `.rsd`/`.esd`.
- Data paths: `MB1000_M13_DT/{WELL}.rsd` and `MB1000_M13_DT/MB1000_M13_DT_Cp312_MD1/{WELL}.esd`

## Key files
- `sequencing_gui_V15.py` — active GUI with greedy caller integrated
- `settingsV8.json` — best pipeline settings
- `/tmp/opencode/gui_greedy_fullplate.py`, `greedy_fullplate.py`, `greedy_sweep.py`,
  `greedy_refine.py`, `greedy_fill.py`, `balance_diag.py` — verification/analysis scripts
