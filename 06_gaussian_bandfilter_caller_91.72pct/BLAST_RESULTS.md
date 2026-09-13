# NCBI BLAST validation (independent of the repo reference)

Sample of 12 wells (A01,A03,A05,A07,A09,A11,B01,B03,B05,B07,B09,C01), both our
calls and Cimarron 3.12 ESD calls, submitted to NCBI BLASTn (MEGABLAST,
`database=nt`) through the URL API. Top hit for every sequence is M13mp18
(`M77815.1`) or M13mp10 (`L08819.1`) — both callers produce genuine M13 reads.

| Caller | mean BLAST identity | mean aligned len | mean call len | total gaps |
|---|---|---|---|---|
| **ours** | 96.26% | 760.3 | 831.5 | **226** |
| Cimarron 3.12 (ESD) | 96.35% | 782.8 | 872.6 | 270 |

Per-well BLAST % identity (ours / ESD):

```
A01 96 / 95    B01 95 / 96
A03 96 / 97    B03 96 / 96
A05 96 / 97    B05 98 / 98
A07 96 / 96    B07 95 / 94
A09 98 / 96    B09 97 / 97
A11 97 / 97    C01 96 / 97
```

## Interpretation

- **On NCBI BLAST local identity we are statistically tied** with Cimarron
  3.12: 96.26% vs 96.35% (delta -0.09 pt, n=12 — within noise). BLAST is a
  *local* aligner and rounds to whole percent, so it does not resolve the
  difference the full-length metric sees.
- **Our reads are cleaner** where they align: 226 gaps vs 270 (16% fewer).
- **Cimarron's reads are longer**: 872.6 vs 831.5 mean calls, 782.8 vs 760.3
  aligned bases. Cimarron calls ~5% more bases, at slightly lower accuracy.
- On the **same 12 wells**, the repo's full-length canonical metric gives
  ours 91.23 vs Cimarron 90.84 (+0.39). Across all 96 wells: ours 91.72 vs
  90.72 (+1.00).

Both metrics are legitimate; they measure different things:

| Metric | Scope | Winner |
|---|---|---|
| NCBI BLASTn local identity | best local HSP only | tie |
| repo `perbase_vs_ref` (full-length) | whole read incl. gaps/ends | **ours** |

## Coverage caveat

The full-length edge depends on auto-trimming the low-quality tail. Disabling
trim gives Cimarron-like read length but collapses identity:

| config | canonical | mean read len |
|---|---|---|
| WIN (trimmed) | **91.72** | 826 |
| no-trim | 88.53 | 895 |

So this is an **identity/coverage trade-off**: we beat Cimarron on full-length
identity by testing a slightly shorter, cleaner read; Cimarron returns longer
reads. Neither is unambiguously "better" without a coverage requirement.

Note: the repo's clean reference is the **exact reverse complement of NCBI
M77815.1 (M13mp18), 0 mismatches over 7250 bp**, so `perbase_vs_ref` is
already a comparison against the authentic NCBI M13 genome.
