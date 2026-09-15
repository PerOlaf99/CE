# Cimarron DLL decode notes (part B)

Goal: find the DLL's "4x FFT upsample" stage and see whether replicating it
gives a real algorithmic improvement over our pure-Python caller.

Analysis target: `MegaBACE/Base Calling/csibq030012.dll` (PE32, x86, native
MSVC, 450 exports, no symbols). Tools: `objdump` disassembly + PE parsing
(import/export/IAT) + reading `.rdata`/`.data` constants. All DLLs here are
native; none are .NET.

## What was found

### 1. The FFT is Numerical Recipes `four1`

Export `?dfour1@@YAXQANKH@Z` = `void dfour1(double*, unsigned long, int)` at
`0x10034340`. Disassembly shows the exact NR `four1` structure: bit-reversal
loop, then Danielson-Lanczos with `mmax` starting at 2 and doubling,
`theta = isign * (2*pi)/mmax`, `wtemp = sin(0.5*theta)`,
`wpr = -2*wtemp*wtemp`, `wi = sin(theta)`. Constants read from `.rdata`:
`2.0`, `0.5`, `-2.0`. It is a plain complex DFT with the NR sign convention,
so `numpy.fft` is numerically equivalent.

### 2. There is no "4x FFT upsample"

`dfour1` is called from 18 sites, in these functions:
- `psd@Wvfm` (`0x10020380`) - power spectral density.
- `cutoff@RdrOut` (`0x10022325`) - designs a length-2N complex frequency
  response (table `0x10038bd8` = half-widths {7,9,11,13,15} per mode, fills a
  passband and zeroes the high frequencies), i.e. a frequency-domain low-pass.
- `pickcuts@RdrOut` (`0x100228b8`), `flatten_@RdrOut` (`0x10023166`) - spectral
  baseline flattening / cutoff selection.
- two internal functions (`0x1000b7a0`, `0x10030505`).

None of these interpolate or upsample the trace. The FFT is used for spectral
analysis and frequency-domain filtering only.

### 3. Rate conversion is cubic-spline, not Fourier

- `rawRateCnvrt@Wvfm` (`0x100207b0`) calls NR `spline` (`0x10036070`) and
  `splint` (`0x10036302`) four times - cubic-spline resampling of the trace.
- `doSmplRateCnvrt@CSIBQWrap` (`0x1000cbbc`) orchestrates it.
- `smplRate@Wvfm` (`0x100017c0`) sets an `INTERPOLATE_BY` mode.

### 4. `upSmpl` only scales band coordinates

`upSmpl@BandStatArray(int factor)` (`0x10015f59`) loops over band-stat elements
(stride `0x50`) and multiplies three integer coordinate fields by `factor`.
`resize@RdrOut` (`0x1002358a`) picks `upSmpl` (mode 1) or `dnSmpl` (mode 2)
based on the run's rate-conversion mode. It is coordinate scaling, not
signal interpolation.

### 5. Sub-sample peak positions come from quadratic fits

`BandStat` stores quadratic coefficients (`squad@BandStat` / `gquad@BandStat`)
and there are integer/double quadratic interpolators `iquadratic`
(`0x100351a8`) and `dquadratic` (`0x10035606`). So the DLL refines each band's
peak position sub-sample with a parabola.

## Empirical test: do these help our caller?

Both DLL-inspired mechanisms were ported and scored on all 96 wells with the
same NCBI BLAST+ megablast metric (identical bases vs `M77815.1`), with
sample-rate-dependent windows scaled:

| variant | identical bases |
|---|---|
| current caller (control) | **73,462** |
| 2x spline upsample | 42,816 |
| 2x Fourier upsample | 42,059 |
| 4x spline upsample | 8,990 |
| 4x Fourier upsample | 8,226 |
| parabolic sub-sample peaks (integer pos) | 70,175 |
| parabolic sub-sample peaks (float pos) | 68,865 |

Trace upsampling is catastrophic (most reads become unalignable), and
sub-sample parabolic peak positioning is also slightly worse. The parabolic
variant was verified to reproduce the control exactly when the refinement is
disabled, so the comparison is fair.

## Conclusion

The originally-hypothesised "4x FFT upsample" does not exist in
`csibq030012.dll`. The DLL upsamples trace data with cubic splines and refines
peak positions with quadratic fits; its FFT (`dfour1` = NR `four1`) is used only
for spectral filters (PSD, cutoff, flatten).

Neither mechanism improves our caller: naive upsampling destroys alignment, and
parabolic sub-sample peaks reduce the identical-base count. Our raw-resolution
DSP + spacing-tracking pipeline is already at a better operating point, which is
consistent with it already beating Cimarron 3.12 on total correct bases
(73,462 vs 72,286). No change is made to the shipped caller.
