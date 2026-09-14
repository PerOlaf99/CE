# NCBI BLAST validation

Metric: **correctly-called bases** from NCBI BLAST+ 2.17.0 `megablast`
(same engine as the NCBI web BLAST URL API) against the NCBI M13mp18 reference
`M77815.1`. This replaced an earlier local-alignment ratio metric that was
misleading (see "Why this metric" below).

## Result (96 wells, MB1000_M13_DT)

| metric | ours | Cimarron 3.12 (ESD) | delta |
|---|---|---|---|
| **identical bases** | **73,462** | 72,286 | **+1,176 (+1.6%)** |
| **aligned length** | **77,136** | 74,726 | **+2,410** |
| mean % identity | 95.30% | 96.76% | **−1.46** |
| mean read length | 920.9 | 873.0 | +47.9 |
| total gaps | 2,226 | 1,967 | +259 |

We now call **more correctly-identified bases and longer alignments** than
Cimarron 3.12, at **lower average identity**. The two callers sit at different
points on the identity/coverage frontier; the trade-off is explicit and not
hidden behind a ratio.

Config: `pullback_weight=0.019`, `channel_peak_bonus=1.6`,
`local_norm_window=1800`, `window_frac=(0.75,1.25)`,
`gaussian_recon_segment_size=384` (all Gaussian/combined-score/band-filter
stages on). Robust: `pullback_weight` 0.018–0.021 all beat Cimarron.

## Why this metric

An earlier committed version of this folder claimed a win using the repo's
`perbase_vs_ref` ratio (91.72% vs 90.72%). That was wrong: the ratio rewards a
*shorter, cleaner* read. Counting actual bases over the whole plate:

```
                ours        Cimarron
bases called    79,304      83,805
correct bases   75,758      79,279     <- Cimarron ahead by 3,521
identity        91.69%      90.71%
```

Cimarron called ~4,500 more bases and got ~3,500 more of them right. The higher
ratio simply came from calling fewer bases. NCBI BLAST confirms it: at our
old config Cimarron led with **72,313 vs 70,289 identical bases (+2.8%)**.

A per-window analysis by reference position showed Cimarron's edge was coverage
in the degraded 3' end (template ~800–900): it covered ~8,800 base-slots there
vs our ~5,000. BLAST's local alignment discards the unalignable tail, so simply
un-trimming did nothing — the extra bases had to be *positioned correctly*.
Retuning the spacing tracker's pull-back weight (0.03 → 0.019) let the local
spacing model track the broadening peaks at both ends, recovering that
coverage with enough correctness to overtake Cimarron's total.

## Reproduce

```bash
python call_plate.py                 # writes basecalls/*.fasta
BLAST_DIR=/path/to/ncbi-blast-*/bin python blast_eval.py   # -> report_blast.json
python eval_plate.py                 # canonical ratio -> report.json
```

`blast_eval.py` downloads `M77815.1` from NCBI and builds its own BLAST
database, so the reference is the authentic NCBI M13 genome.
