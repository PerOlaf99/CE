# track_bases release pack (MegaBACE MB1000_M13_DT)

## Contents

### `track_bases_results/`
- `A01_track_bases.fasta` — A01 call for NCBI BLASTN (vs M77815.1)
- `A01_track_bases.txt` — plain sequence
- `plate_caller_compare.csv` — 96 wells: MD, Cimarron 1.53, Cimarron 3.12, track_bases
- `README_track_bases.md` — metrics summary and usage notes

### `best_basecaller_min/`
Minimal Python package to re-run the unsupervised caller on any `.rsd`:
```bash
cd best_basecaller_min
pip install numpy scipy
python3 basecall.py --input /path/to/A01.rsd --out calls
```

## NCBI BLAST
1. Open https://blast.ncbi.nlm.nih.gov/Blast.cgi?PROGRAM=blastn&PAGE_TYPE=BlastSearch
2. Paste `track_bases_results/A01_track_bases.fasta`
3. Subject: M77815.1 (or search nr for M13mp18)

## Plate totals (eqM13 ≈ identical bases vs M13)
| Caller | sum eq | mean len |
|--------|-------:|---------:|
| MD | 68,283 | 735 |
| Cimarron 1.53 | 76,479 | 859 |
| Cimarron 3.12 | 78,293 | 867 |
| track_bases | 79,158 | 909 |

Push `track_bases_results/` into your CE git repo when ready.
