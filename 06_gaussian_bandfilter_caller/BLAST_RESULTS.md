# NCBI BLAST validation

Metric: best HSP per read from NCBI BLAST+ 2.17.0 `megablast` (same engine as
the NCBI web BLAST URL API) against the NCBI M13mp18 reference `M77815.1`
(7,250 bp), over all 96 wells of MB1000_M13_DT. Reported for our denovo caller
and for the Cimarron 3.12 ESD calls.

## Result

| metric | ours | Cimarron 3.12 | delta |
|---|---|---|---|
| identical bases | **73,462** | 72,286 | **+1,176 (+1.6%)** |
| aligned length | **77,136** | 74,726 | **+2,410** |
| coverage of reference (mean) | **11.08%** | 10.74% | **+0.35 pp** |
| total bit score | 120,047 | **122,831** | -2,784 |
| mean bit score | 1,250.5 | **1,279.5** | -29.0 |
| mean % identity | 95.30% | **96.76%** | -1.46 |
| coverage of read (mean) | 87.25% | **89.18%** | -1.93 pp |
| longest error-free stretch (mean) | 250.0 | **285.7** | -35.7 |
| longest error-free stretch (median) | 244 | **288.5** | -44.5 |
| mean read length | **920.9** | 873.0 | +47.9 |
| total gaps | 2,226 | **1,967** | +259 |

## Reading the result

This is a genuine trade-off, not a clean sweep:

- **We call more data.** More identical bases (+1,176), longer alignments
  (+2,410) and more of the reference covered (11.08% vs 10.74%). This is the
  "total correctly-called bases" objective.
- **Cimarron is more accurate per base.** Better bit score, higher %ID,
  higher fraction of each read that aligns, and a longer error-free stretch
  (285.7 vs 250.0 bases on average). Shorter reads make longer perfect runs
  easier, but the gap is large relative to the read-length difference.
- `longest error-free stretch` = longest run of consecutive matching columns
  (gaps break the run) within the best HSP.

## Configuration

Final `WIN_CONFIG`: `use_gaussian_reconstruction=True`,
`gaussian_recon_segment_size=384`, `use_combined_channel_score=True`,
`window_frac=(0.75,1.25)`, `local_norm_window=1800`, `channel_peak_bonus=1.6`,
`pullback_weight=0.019`, `ema_alpha=0.10`.

## Reproduce

```bash
python call_plate.py                 # writes basecalls/*.fasta
BLAST_DIR=/path/to/ncbi-blast-*/bin python blast_eval.py   # -> report_blast.json
python eval_plate.py                 # canonical ratio -> report.json
```

`blast_eval.py` downloads `M77815.1` from NCBI, builds its own BLAST database,
and reports identical bases, aligned length, %ID, bit score, coverage (vs
reference and vs read) and longest error-free stretch for both callers.
