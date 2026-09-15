# track_bases results (MB1000_M13_DT)

Unsupervised MegaBACE basecaller (`track_bases` from best_basecaller / cimarron_basecaller).
No ESD or reference used at call time. Gold standard for comparison: NCBI BLAST vs M13mp18 (M77815.1).

## Files

| File | Description |
|------|-------------|
| `A01_track_bases.fasta` | A01 call (903 bp) for NCBI BLASTN |
| `A01_track_bases.txt` | Same sequence, plain text |
| `plate_caller_compare.csv` | All 96 wells: MD, Cimarron 1.53, Cimarron 3.12 (ESD), track_bases (RSD) vs M13 proxy metrics |

## How to run track_bases

```bash
# from best_basecaller package
python3 basecall.py --input A01.rsd --out calls
# or plate directory of *.rsd
python3 basecall.py --input /path/to/MB1000_M13_DT --out calls
```

Python API:

```python
from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller.spacing_caller import track_bases

trace, order = to_acgt_trace(read_rsd("A01.rsd"), base_order="TGCA")
seq, quals, bands = track_bases(
    trace, base_order=order,
    use_gaussian_reconstruction=True,
    gaussian_recon_segment_size=384,
    use_combined_channel_score=True,
    window_frac=(0.75, 1.25),
    local_norm_window=1800,
    channel_peak_bonus=1.1,
    pullback_weight=0.019,
    ema_alpha=0.10,
    baseline_window=201,
    position_adaptive_spectral=True,
)
```

## Plate summary (eqM13 = matching bases vs M13 reference, proxy for BLAST identical bases)

| Caller | sum eqM13 | mean eq | mean length |
|--------|----------:|--------:|------------:|
| MD (Molecular Dynamics) | 68,283 | 711 | 735 |
| Cimarron 1.53 | 76,479 | 797 | 859 |
| Cimarron 3.12 | 78,293 | 816 | 867 |
| track_bases | **79,158** | **825** | **909** |

CSV columns: `well`, `MD_n/sm/eq`, `Cp153_n/sm/eq`, `Cp312_n/sm/eq`, `TB_n/sm/eq`.

## NCBI BLAST

Paste `A01_track_bases.fasta` into:
https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastn&PAGE_TYPE=BlastSearch

Subject/accession: M77815.1 (M13mp18). Compare coverage, % identity, and aligned length to Cimarron ESD results.
