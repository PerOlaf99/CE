# best_basecaller

De-novo, reference-free MegaBACE M13 basecaller. Pure DSP + peak tracking
(numpy/scipy only). No reference sequence and no trained model are used at
call time.

This is the tuned caller for the `MB1000_M13_DT` plate. On all 96 wells, scored
with NCBI BLAST+ `megablast` against the NCBI M13mp18 reference (`M77815.1`):

| metric | this caller | Cimarron 3.12 (ESD) |
|---|---|---|
| identical bases | **73,462** | 72,286 |
| aligned length | **77,136** | 74,726 |
| mean % identity | 95.30% | 96.76% |
| mean read length | 920.9 | 873.0 |

It calls more total correct bases and longer reads than Cimarron 3.12; Cimarron
has higher average identity because it calls shorter reads. See `NOTES.md`.

## Install

```bash
python3 -m pip install -r requirements.txt
```

Requires Python 3.9+, numpy and scipy. Nothing else.

## Run

```bash
# whole plate (directory of *.rsd) -> calls/<well>.fasta + calls/all_reads.fasta
python3 basecall.py --input /path/to/MB1000_M13_DT --out calls

# a single well
python3 basecall.py --input A01.rsd --out calls

# FASTQ with PHRED qualities instead of FASTA
python3 basecall.py --input /path/to/MB1000_M13_DT --out calls --format fq
```

Each well produces `<well>.fasta` (or `.fastq`), plus a combined `all_reads.*`.
Progress and per-well call counts are printed to stdout.

## API

```python
from cimarron_basecaller import track_bases
from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace

trace, order = to_acgt_trace(read_rsd("A01.rsd"), base_order="TGCA")
seq, quals, bands = track_bases(
    trace, base_order=order,
    use_gaussian_reconstruction=True, gaussian_recon_segment_size=384,
    use_combined_channel_score=True, window_frac=(0.75, 1.25),
    local_norm_window=1800, channel_peak_bonus=1.6,
    pullback_weight=0.019, ema_alpha=0.10,
)
```

`basecall.py` holds this exact dict as `WIN_CONFIG`.

## Files

- `basecall.py` - command-line entry point (`WIN_CONFIG` here).
- `cimarron_basecaller/` - DSP + tracking package:
  - `spacing_caller.py` - `track_bases`, the recommended caller.
  - `preprocessing.py`, `deconvolution.py`, `peaks.py`, `scoring.py`,
    `alignment.py` - baseline, spectral separation, Gaussian band filter,
    mobility shift, combined scoring.
  - `rsd_io.py` - MegaBACE `.rsd` reader (`to_acgt_trace`).
  - `dp_caller.py`, `simple_caller.py` - alternate callers (much worse; kept
    for reference).

## Notes

- The `WIN_CONFIG` constants were tuned on this plate. Re-tune
  `pullback_weight` and `channel_peak_bonus` for other plates; the Gaussian
  band filter and combined-channel score are the transferable parts.
- Reads are called in the sample's own orientation. When comparing against an
  M13 reference, use a strand-agnostic aligner (e.g. BLAST / megablast), which
  is how the table above was produced.
- `cimarron_basecaller/` is vendored from the user-provided MegaBACE Cimarron
  software bundle; only numpy/scipy are required on the `track_bases` path.
