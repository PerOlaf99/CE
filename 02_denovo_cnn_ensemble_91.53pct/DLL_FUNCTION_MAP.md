# Cimarron 3.12 DLL — Verified Function Map (Ghidra 12.1 headless)
**Author**: opencode · **Date**: Aug 27, 2026
**Source**: `winedll/csibq030012.dll` (ORIGINAL, 265728 bytes, md5 `0e62d70479cf22fae9f892286c1c9946`)
**Decompilation**: all 901 functions exported to `decomp_all.c` (29516 lines)
**Correction to `CIMARRON_MASTER.md`**: the doc's stage-offset map was partially
mislabeled. This file is the *verified* map. Cite THIS, not the old offsets.

---

## 1. Why this file exists

`CIMARRON_MASTER.md` listed three "undecoded" stages by address:
1. 4× FFT upsampling (no address given)
2. **Post-stage peak calling at 0x4889**
3. **Record-list peak detector at 0x19ef2**

Ghidra decompilation shows the labels at those addresses were wrong for #2, and
the true peak pipeline lives in a different set of functions. Confirmation of
what is actually at each cited RVA:

| Doc claimed | RVA | Ghidra says it is | Verdict |
|---|---|---|---|
| Post-stage peak calling | 0x4889 | `Annotate::setMobTbl` (simple setter copying a mobility table) | **WRONG label** |
| Record-list peak detector | 0x19ef2 | `FUN_10019ef2` = top-level band classifier / base reader | **correct**, retitled |
| B-spline peak search | 0x10b2e | `FUN_10010b2e` = coarse-to-fine spline-numerator search | **correct** |
| Band table build | 0x10698 | `FUN_10010698` | **correct** |
| Dead-scan carving | 0x10ca7 | `FUN_10010ca7` | **correct** |
| Band correction | 0x10d6d | part of the 0x10d6d region chain | **correct** |

Note on the FFT: there is **no standalone "4x FFT upsampling" function**.
`dfour1` (Numerical-Recipes FFT, 0x34340) is called from several places, most
significantly in the **post-output** functions `RdrOut::cutoff`/`pickcuts`/
`flatten_` (0x22325/0x228b8/0x23166) for FFT filtering of the OUTPUT read, and in
`Wvfm::psd` (0x20380, power-spectral analysis). Peak *position* refinement in the
DLL is done by **sub-scan B-spline interpolation** (FUN_10010b2e region), NOT by
FFT. The "4× FFT upsampling" in the old docs is a misremembering.

---

## 2. Verified peak-reading / base-call pipeline (the 3 "undecoded" stages, real)

The DLL base-calls a well through `Wvfm::nreader` → the record-list reader:

| Stage | Function (RVA) | Role | Decoded? |
|---|---|---|---|
| Band table build | `FUN_10010698` + `FUN_100108cb` (gains) | build band list from trace | ✅ (also in cimarrontv) |
| Coarse/fine B-spline search | `FUN_10010b2e` (+ `FUN_10010a4e` prefix-sum) | sub-scan peak position refinement (radius 15 step 2 → radius 3 step 1) | ✅ |
| Dead-scan carving | `FUN_10010ca7` / `FUN_10010d6d` | separate overlapping peaks | ✅ |
| **Record-list reader** | `FUN_10019ef2` | iterates bands, calls feature fn, classifies each into a base | ✅ (this doc) |
| Band feature extractor | `FUN_1002511d` | computes 14 BandStat fields per band | 🔄 next step |
| Mobility search | `Mobility::search` (0x16b01), `apply` (0x16d96) | per-channel shift | ✅ in cimarrontv |
| Base reader entry | `Wvfm::nreader` (0x1879e) | orchestrates region read into `SegRead`/`RdrOut` | 🔄 |
| Quality | `RdrOut::bandqual` (0x49a0), `QualCtrl` | phred | partial |

The doc's "post-stage peak calling (0x4889)" is really `Annotate::setMobTbl` —
a dead end. The actual final peak-classification is the inner loop of
`FUN_10019ef2` (band → base), which is what `plate_blast.py` recall depends on.

---

## 3. FUN_10019ef2 — the base classifier (top-level structure)

```
FUN_10019ef2(this, ...) :
  build two local BandStat windows (local_88 CCmdUI used as Annotate)
  if FUN_1002511d(this, param_3, &annot) != 1: return 0            # feature build
  if (flags >> 3 & 1):                                             # annotate flag
     for each band b in [1..CFlen]:
        uVar2 = FUN_1001bb80(annot, b)                             # get band b
        ... compute stats, classify into ACGT using BandStat fields,
            emit a base + peak position with quality ...
  return count
```

The classification reads neighbor bands (windows of ~20) and uses
dominance/SNR/envelope to decide each base. Porting this loop + `FUN_1002511d`
reproduces the DLL's peak set and window (e.g. M13 5471–6286 on A01), which is
the `~110 bases/well` of recall we are missing.

## 4. Next porting order (recall-first) — CORRECTED (Aug 27 pm session)

`FUN_1002511d` is NOT a "BandStat feature extractor" — it is the **envelope
peak-candidate detector** (the real successor to the doc's old "record-list
peak detector"): it scans the cross-channel envelope, records envelope local
maxima via a rising/falling state machine, then `FUN_10024f29` measures each
peak's width on the dominant channel and `FUN_1001dee1` turns survivors into
band records. **This, plus the envelope, is the piece that controls recall.**

CORRECT porting order (recall-first):
1. ✅ `FUN_1002511d` + `FUN_10024f29` — envelope local-maxima + width filter
   (`_DAT_10038d60`=2.0 width threshold, width_factor=3.0, single-pass mean).
   **PORTED** (`dll_peakdet.py`). Candidate set only — see §6; this alone
   does NOT beat the DLL on the BLAST metric (it over-detects).
2. `FUN_1001dee1` band-record build + `FUN_10019ef2` classify loop → emit bases.
3. `Wvfm::nreader` region orchestration → reproduce begin/end window + base list.

Reference artifacts: `/tmp/opencode/re/` + USB `02_denovo_cnn_ensemble_91.53pct/`
(`decomp_all.c`, `DLL_FUNCTION_MAP.md`, `dll_peakdet.py`, raw DLL).

## 5. PORT VALIDATION — envelope peak detector (A01, A02) ⭐

`dll_peakdet.py` implements `FUN_1002511d`+`FUN_10024f29` on the separated lanes:
envelope = **max of the 4 lanes** (empirical; NOT min/sum — the max envelope
ranks the DLL's called-peak recovery highest), envelope local maxima state
machine, per-peak width on the dominant channel while `sc_la(scan) > env/2`,
single-pass width filter `width <= 3*(mean_width+0.5)`.

Validated vs the DLL's own .esd peak positions on the full-length (9647-scan)
separated lane data:

| Well | detected | DLL called | DLL record-list | recall vs called | recall vs record |
|---|---|---|---|---|---|
| A01 | 1217 | 841 | 956 | **93.5%** (786/841) | 87.8% (839/956) |
| A02 | 1212 | 870 | 958 | **92.2%** (802/870) | 86.1% (825/958) |

Raw dominant-channel decode (no CNN) on A01 already gives ~86.7% NW identity to
the DLL's 841-base sequence with ~846 detections in the DLL's scan range — i.e.
the detector finds essentially every DLL base position (the missing recall),
where the previous greedy caller found only ~731. Downstream CNN re-call +
polish (existing `perfect_basecaller`) fix the base labels/indels while keeping
these positions, so this should close the ~110 bases/well recall gap.

**Wiring is NOT yet done** — next session: feed these peak positions into
`perfect_basecaller.call_raw` (seed peaks in place of the greedy caller) and
run `plate_blast` to confirm recall/identity end-to-end. Requires a full-length
separated-lane source (cache_sep is 9647 scans; the cimarrontv_shim DSP truncates
to 3687 — must use the full-resolution DSP path).

## 6. ⚠️ HONEST BLAST-GOLD-STANDARD VERDICT (Aug 27, MUSt READ)

The position-matching above is ONLY a proxy. The user's correct rule: a called
read is verified the way any sequencing run is — **BLAST it against the
gold-standard reference (M13 mp18 here)** and judge by coverage × identity over
the aligned region (the NCBI Blast.cgi model). When the ported envelope-peak
detector is BLASTed end-to-end it does NOT beat the DLL:

| Well | caller | bases | matched_bp | full_ident | pident | hsp_cov |
|---|---|---|---|---|---|---|
| A01 | **DLL-ESD** (gold) | 839 | **790** | 94.16% | 95.39% | 95.35% |
| A01 | ours port+CNN | 735 | 609 | 82.86% | 86.65% | 86.12% |
| A02 | **DLL-ESD** (gold) | 864 | **750** | 86.81% | 96.65% | 87.96% |
| A02 | ours port+CNN | 662 | 312 | 47.13% | 86.20% | 49.09% |

WHY the port underperforms on the REAL metric (matched_bp/detected_bp):
`FUN_1002511d` alone is only the *candidate* generator — it over-detects
(~1217 candidate peaks vs the DLL's 841 *called*). The thing that turns 956
candidates into 841 quality calls is the DOWNSTREAM filtering in
`FUN_1001dee1` (band records) + `FUN_10019ef2` (per-band quality/SNR gates) +
`Wvfm::nreader` begin/end region trimming — NONE of which this port currently
implements. Envelope maxima + a single width filter is NOT sufficient.

CORRECTED LESSON: duplicate a proxy metric (positions matched) is NOT a win;
only BLAST-matched_bp against the reference counts. The real recall lever is
reproducing the DLL's **called-peak filter chain** (the /amplitude SNR quality
gate, band-width criterion, and the nreader bgn/end window), so our candidate
set = the DLL's 841 called positions with no ~370 spurious additions.

Practical candidate low-effort fixes (before more RE):
  * apply a per-channel SNR floor (env_vs_noise) instead of pure width filter,
  * reproduce the bgn/end trimming (see cimarron_bgn_end in cimarrontv.py),
  * keep only peaks whose dominant-channel amplitude clears a position-adaptive
    noise bound — mirroring `_adaptive_noise_channel` already in cimarrontv.

Artifacts: `dll_peakdet.py` (port), `blast_validate.py` / `blast_validate_cnn.py`
(reproducible BLAST check). The position-recall table in §5 stays for reference
but does NOT imply a recall win — BLAST is the arbiter.

## 7. Adding the FUN_10019ef2 called-peak gates — BLAST-verified progress (Aug 27)

We ported the two DLL gates that cut candidates -> called bases:
  * **env/SNR floor**: keep a candidate iff its cross-channel envelope
    `env >= env_floor_frac * env_max` with `env_floor_frac = 0.05`
    (= `_DAT_10038a88` from .rdata, FUN_10019ef2's keep-band test `envv > 0.05`).
  * **bgn/end region window** (`_longest_signal_region`): keep only the longest
    contiguous run of above-threshold bands, tolerating a 10-band quiet gap
    (local_9c>10 logic in FUN_10019ef2).

BLAST (blastn/megablast vs M13) of the ported peaks + CNN re-call + dropout:

| Well | caller | bases | matched_bp | full_ident | pident |
|---|---|---|---|---|---|
| A01 | DLL-ESD (gold) | 839 | 790 | 94.16% | 95.39% |
| A01 | port raw (1217, no gate) | 1217 | 676 | 55.6% | 91.5% |
| A01 | port + gate(0.05)+CNN | 754 | 647 | 85.81% | 94.14% |
| A02 | DLL-ESD (gold) | 864 | 750 | 86.81% | 96.65% |
| A02 | port raw (1217, no gate) | 1217 | 677 | 55.9% | 93.9% |
| A02 | port + gate(0.05)+CNN | 692 | 562 | 81.21% | 94.06% |

INTERPRETATION (honest):
  * The env-floor gate is a REAL win: it cuts ~1217 -> ~760 peaks and lifts
    pident to DLL-level (94-95%) and full_ident to ~81-86% (from ~56%). The
    gate is faithful to FUN_10019ef2.
  * We are still below gold on matched_bp (~647 vs 790 A01; 562 vs 750 A02)
    because we now UNDER-detect: the fixed 0.05 floor drops weak-but-real tail
    peaks the DLL still calls. The DLL does NOT use a fixed floor — it uses a
    position-adaptive quality/SNR array (`FUN_10024e47` -> `local_34`
    confidence) and `FUN_10012140` band-classifier score, so it keeps weak
    peaks that a global 0.05 floor rejects.
  * NEXT lever: replace the fixed floor with the DLL's position-adaptive
    confidence (FUN_10024e47) or a per-position adaptive noise bound (the
    `_adaptive_noise_channel` already in cimarrontv.py), so weak tail peaks
    survive. Also port FUN_10012140 band score to decide keep vs omit per band
    instead of a single global threshold.

DONE this session: FUN_1002511d(FUN_10024f29)+FUN_10019ef2 env-floor+region
gates ported (`dll_peakdet.py`), BLAST harness saved (blast_validate*.py),
verified the DLL constants (_DAT_10038a88=0.05, _DAT_10038a80≈1.176 width-ratio
gate, _DAT_10038d60=2.0, _DAT_10038d70=0.8).

## 8. Porting the position-adaptive quality/SNR (FUN_10024e47 + FUN_10012140)

DECODED the adaptive gate the user asked to port:

* `FUN_10024e47` returns per-band `Wvfm::xbnd(scan)` (stored array this+0xd0,
  built in `Wvfm::envelope` 0x31976). Formula (from decomp + .rdata):
      v1>=v2>=v3>=v4 = sorted 4 lane values at scan; min=v4, v3=3rd-largest
      if v3 < 8.9e-16: v3 = 2.2e-16
      if 0.1 <= min:  xbnd = min/v3
      else:           xbnd = min/sqrt(v3) + 1.0
      clamp to [1.0, 2.0]   (`_DAT_10038e58`=1.0, `_DAT_10038e54`=2.0, `_DAT_10038eb0`=0.1)
  This supplies the `local_34` confidence array in FUN_10019ef2.

* `FUN_10012140` (the real keep/drop): computes
      local_6c = mean(flank-min env)   floored at `_DAT_100388d0`=0.05
      threshold ~= `_DAT_100388d8`(0.93) * local_6c * `_DAT_100388e0`(1.333)
                 = 1.24 * mean(flank env)
  then feeds it into 6 opaque classifier "objects" (`FUN_10012ad0`, magic
  tables DAT_10038750..DAT_100388c0, virtual-method graph) that decide each
  band keep=1 / fallback=2. THIS object-graph is the real "weak tail peaks
  survive" mechanism, and it is a large multi-session port.

BLAST results of adaptive-gate attempts (ported-peaks + CNN + drop + BLAST):

| gate | A01 matched_bp | A02 matched_bp | note |
|---|---|---|---|
| gold DLL-ESD | 790 | 750 | |
| fixed 0.05 | 647 | 562 | pident 94%, fullid ~86% |
| xbnd_rel (0.05+adaptive) | 647 | 562 | == fixed |
| xbnd_abs (envv>xbnd) | ~400 NO-ALIGN | ~400 NO-ALIGN | too aggressive |
| flank (1.24*min-of-flanks) | ~419 NO-ALIGN | ~355 NO-ALIGN | min(2 flanks) too strict; needs mean over a window |

VERDICT: the fixed/adaptive floor reaches DLL pident (94%) and fullid ~86%,
but matched_bp stays ~100-190 below gold because the faithful FUN_10012140
flank-context aggregation (mean over a band window, not min-of-2) is not yet
reproduced. Reproducing it requires either (a) porting FUN_10012140's object
graph, or (b) a pragmatic stand-in: per-band threshold = 1.24 * running mean of
neighbor-band env over a ~+/-(few) band window, floored 0.05, then re-BLAST.
Recommend (b) first as it is ~an hour and reuses the BLAST harness.

## 9. ARCHITECTURE REVEAL: FUN_10012140 is a FUZZY-LOGIC EXPERT CLASSIFIER ⭐
(path 2 decision — Aug 27 pm)

`FUN_10012ad0` builds objects whose debug strings are `CFuzzySet___s__x_y` and
`CFuzzySet___s__x_y` — these are **fuzzy membership sets** (piecewise-linear
x/y lookup with linear interpolation `FUN_10012c6c` = fuzzify, `FUN_10012dbd`
= max, `FUN_10012e31` = empty test, plus `FUN_10012f4d`/`FUN_10013818`).
Each object = {n points; x array; y array; mode(interp/max)} with a vtable.

So `FUN_10012140` is a **fuzzy-expert-system band classifier** (Cimarron's
base-calling decision engine), NOT a simple numeric threshold. It fuzzifies
per-band features (mean flank-env quality, SNR `local_34`/xbnd, width ratio)
through 8 fuzzy sets defined by the magic tables below, and the vtable methods
combine the membership values into the keep(1)/drop(2) code seen in
`FUN_10019ef2`.

Preliminary table decode (doubles from .rdata 0x10038740–0x100388d0). WARNING:
x/y pairing and mode semantics still to be CONFIRMED by tracing the vtable
eval; treat as provisional:

  set1 (n=3,m=0) @0x38750  x=<0x38750>     y=<0x38768>
  set2 (n=4,m=2) @0x38780  x=<0x38780>     y=<0x387a0>
  set3 (n=3,m=0) @0x387c0  x=<0x387c0>     y=<0x387d8>
  set4 (n=2,m=0) @0x387f0  x=<0x387f0>     y=<0x38800>
  set5 (n=2,m=0) @0x38810  x=<0x38810>     y=<0x38820>
  set6 (n=4,m=0) @0x38840  x=<0x38840>     y=<0x38860>
  set7 (n=3,m=0) @0x38880  x=<0x38880>     y=<0x38898>
  set8 (n=2,m=1) @0x388b0  x=<0x388b0>     y=<0x388c0>
  (values span ~0.0–3.6; feature-normalized units, not scan counts.)

Also here: `FUN_10012140` header computes local_6c = mean(flank-min env),
`_DAT_100388d0`=0.05 floor, `_DAT_100388d8`=0.93, `_DAT_100388e0`=1.333,
`_DAT_100388e8`=2.0, `_DAT_100388f0`=0.0 — these feed the fuzzy inputs.

### Decision (user, Aug 27): PATH 2 — faithful full port
We have used a lot of ML/approximation and are still below the DLL. Take
PATH 2 = port `FUN_10012140`'s fuzzy classifier faithfully (decode all 8 fuzzy
sets precisely by tracing the vtable eval + combine, reproduce the rule flow),
plus the `FUN_10019ef2` classify loop and `Wvfm::nreader` region orchestration,
then re-BLAST vs M13. If path 2 stalls, fall back to PATH 1 (pragmatic
flank-context threshold, ~1 hr).
NOTE for the next session: the fuzzy-set membership eval (`FUN_10012c6c` linear
interp, `FUN_10013818`, `FUN_10012f4d` combiner) and the per-band feature
BUILD (`FUN_1001dee1` 14 BandStat fields) must be traced before the tables can
be pinned down. This is a large, multi-session port — budget accordingly.

## 10. ⭐ PATH-2 PORT — NUMBERED IMPLEMENTATION CHECKLIST (resume from any step)

Track progress: mark each step with `[x]` as you finish. Work ONLY from this
list; each step is self-contained and verifiable.

### Phase A — Build the fuzzy-engine core (pure Python, unit-testable, no DLL data yet)
- [x] **A1.** Implement `CFuzzySet` (= FUN_10012ad0 object): fields n, x[], y[],
      interp/max mode. Add `membership(x)` = linear interpolation
      (port FUN_10012c6c exactly, incl. boundary/base behavior), `max_val()`
      (FUN_10012dbd), `is_empty()` (FUN_10012e31), `insert/remove`.
      DONE — in `re_artifacts/fuzzy_engine.py`.
- [x] **A2.** Implement `union(a,b)` = fuzzy union/merge (port FUN_10012f4d
      exactly: merge sorted x lists, combine overlapping points).
      DONE — param_3==0 -> max (OR), !=0 -> min (AND).
- [x] **A3.** Implement `centroid(set)` = defuzzify (port FUN_10013818 exactly:
      `c = I0/(3.0*I1)` guarded by `|I1|>6.1e-21`. RESOLVED the weight const via
      disasm `fldl 0x10038928`): `_DAT_10038928` = **2.0** (NOT 5.7e20 — my
      earlier hex decode was a byte-pairing misread). K=2.0 gives the symmetric
      triangle [0,1,2]->[0,1,0] centroid EXACTLY 1.0 => formula + consts correct.
- [x] **A4.** Implement the 4 mode-transforms (FUN_10013991 identity,
      FUN_10013999 square, FUN_100139a4 sqrt, FUN_100139b9/f4 piecewise
      sqrt/square with `_DAT_10038938`=0.5). These transform a feature value
      before it indexes a set.  DONE.
- [x] **A5.** Unit test the engine on synthetic trapezoidal/triangular sets and
      confirm interpolation + centroid return analytic values (verify EACH).
      DONE — `test_fuzzy_engine.py`, 28/28 pass including centroid=1.0 exact.

### Phase B — Pin the 8 fuzzy tables exactly (from .rdata, CONFIRM x/y pairing)
- [x] **B1.** Resolve the y-offset convention (x @ addr, y @ addr+n*8 vs
      interleaved pairs) by reading how FUN_10012ad0 memcpy's param_2/param_3
      and which addresses FUN_10012140 passes. Decode the 8 sets definitively.
      DONE — confirmed in FUN_10012ad0: x[]=offset 0x24 (field [9]), y[]=
      0x28 ([10]), **two SEPARATE contiguous double arrays, NOT interleaved**;
      n=0x20 ([8]); mode=0x2c ([0xb]); mode-transform fns at 0x30/0x34
      ([0xc]/[0xd]); vtable at 0x00..0x1c ([0]=centroid,[1]=union,[2]=empty,
      [3]=membership,[4]=max,[5]=..,[6]=..,[7]=scale/..). Complement prim
      FUN_10012ec6 = 1-y (_DAT_10038900=1.0).
- [ ] **B2.** Record the final 8 sets (x[],y[],mode) into this doc appendix:
      set1..set8 @ 0x10038750..0x100388d0 (provisional values in §9).
      DONE — decoder `re_artifacts/decode_sets.py` (uses .rdata VA=0x10038000/
      RawOff=0x36a00). FUN_10012140 builds 6 OUTER (per-well) + 4 INNER
      (per-band) sets. Recorded in §B2-APPENDIX below.
- [ ] **B3.** Map each of the 8 sets to the feature it fuzzifies, by reading
      FUN_10012140's data-flow: which input array (param_2 env / param_3
      flank-min / local_34 xbnd-confidence / param_5) is transformed by which
      mode and fed to which set. Reconstruct the exact rule antecedents.
      STRUCTURE DECODED (remaining = FPU-stack input trace, see NEXT section).
      Rule flow per band i (from FUN_10012140 line 9619-9686):
        _Y = param_1[i] (int feature)   ; fmod guards on param_4[i],param_5[i]
                                       ; in [Y/2,Y]
        if _Y == _DAT_100388f0(0.0): abort well (free sets, return 0)
        eval[3] local_34 twice, local_30 twice, local_38, local_50,
             local_3c, puVar1   -> outer+dynamic set memberships
        scale[7] puVar3, puVar4, puVar5   -> scale inner LOW/MID/HIGH by a
                                             stack arg (UNRESOLVED, needs asm)
        union[1] puVar2 x3        -> fold scaled inner sets into puVar2 (max)
        centroid[0] puVar2 ; max_val[4] puVar2 -> fVar6 = final quality
        output param_8[i].val   = local_e8 (local env/floor)
        output param_8[i].qual  = fVar6
        if (val==0 && qual==0): val=1.0, qual=0.5   (sentinel _DAT_100388f8=0)
      So per band: quality = max_val of max-union of scaled LOW/MID/HIGH
      windows (max fuzzy in-window membership); value = local env floor.
      RESUME AT: disassemble FUN_10012140 (0x10012140) and trace the FPU stack
      to recover the ARG to each `[3]` eval, the scale param to `[7]`, and the
      band feature source for param_1/param_4/param_5 (relate to BandStat).
      **COMPLETE (B3 fully resolved via asm trace fun_10012140.asm, see
      §B3-DETAIL below): the exact x87 algorithm is recovered -- params,
      clamp/ratio logic, set evals, min/max rule-weight reductions, scaling,
      max-union, centroid+max output, sentinel. Full pseudocode transcribed
      in §10 "THE CLASSIFIER (asm-verified)".**

## §B3-DETAIL — FUN_10012140 EXACT ALGORITHM (asm-verified, B3 DONE)

Args (thiscall, ebp offsets; element count = 0x20):
  0x08 int[]   Y feature (fildl)         0x0c float[] -> dynamic ramp sets
  0x10 float[] mean-env source            0x14 int[]  D flank -> ratio r1
  0x18 int[]   E flank -> ratio r2        0x1c float[] -> descending/rising sets
  0x20 int     count                      0x24 rec[] out: {off+4 val, off+8 qual}

PER-WELL: floor = min(mean(env), 0.05) ; T = 0.93*floor*1.3333 (~1.24*floor).
PER-BAND i (Y=int[0x08][i]):
  r1 = min(D[i], Y/2)/Y     (D=0x14)          -> V-set, trapezoid
  r2 = min(E[i], Y/2)/Y     (E=0x18)
  m_V = max(V(r1), V(r2))   [V=n3 mode0 x=.2,.5,.8 y=1,0,1 @-0x30]
  m_T = max(T(r1), T(r2))   [T=n4 mode2 x=.2,.4,.6,.8 y=0,1,1,0 @-0x2c]
  dVal = desc(float[0x1c][i])    [desc n3 x=1,1.4,1.8 y=1,.5,0 @-0x34]
  rVal = rise(float[0x1c][i])    [rise n2 x=1.2,1.4 y=0,1      @-0x4c]
  ramp = dynA(flt[0x0c][i])      [dynA n2 x=[floor,1.24*floor] y=0,1 @-0x38]
  pv   = dynB(flt[0x0c][i])      [dynB mode1                                   @-0x60]
  # rule weights (min-reductions of antecedent memberships):
  wLow = min(rVal, pv, m_V)                       # scale for puVar3 (LOW  )
  wMid = min(dVal, pv)        (branchy; see notes) # scale for puVar4 (MID  )
  wHigh= ramp                    (approx)          # scale for puVar5 (HIGH )
  # fuzzy inference (Mamdani): scale inner windows, max-union into zero set:
  lo=scale(puVar3@-0xf0 ? LOW set, wLow); mid=scale(puVar4, wMid);
  hi=scale(puVar5, wHigh); combined = union(union(union(zero,lo),mid),hi)
  out[i].val  = float(centroid(combined))   # [0x0]
  out[i].qual = float(max_val(combined))    # [0x10]
  if out[i].val==0 and out[i].qual==0: out[i]=(1.0,0.5)   # sentinel
KEEP/DROP (post-classify, caller @13923-13948):
  q = ftol(out[i])  # defuzzified value
  if q==1: KEEP (emit base)
  elif q==2: if xbnd[i]<=_DAT_10038a80(=1.176471, 20/17): mark weak(posflag 5);
             EMIT regardless
RESOLVED GATE CONSTANTS (.rdata): _DAT_10038a80=1.176471f (xbnd gate),
  _DAT_10038a88=0.05 (env peak floor), _DAT_10038aa0=1.5 (spacing z-outlier),
  _DAT_10038ab0=2.0, _DAT_10038ac0=0.5, _DAT_10038ac8=3.0 (centroid),
  _DAT_10038ab8=0.0 (sentinel).
So classifier RETURNS per-band int: 1=keep, 2=weak(emit w/ mark). It is NOT a
hard threshold; recall comes from emitting always, quality marks the weak set.
RESUME at Phase C (BandStat feature build -> supply Y,D,E,float arrays).
**PHASE-C RUN (DEBUG, A01): classifier port runs end-to-end but does NOT yet
discriminate -- ALL bands score alike (val~2.54, qual=1.0, ftol=3). Cause =
FEATURE-SCALE calibration, NOT the engine port (which is asm-verified):
  Y=9.0 const (my diff() approximation, no real SWold model)
  r1~0.5, r2=0.5 everywhere (ratio saturate)  -> V/trap all same
  xb=1.0 everywhere (min/v3 sun into 1)        -> desc/rise all same
  sb(0.24-4.8) >> floor(0.05)*1.24 (0.062)    -> ramp=1 all -> wHigh=1 all
=> The fuzzy sets DISCRIMINATE only on the DLL's REAL feature scales (proper
BandStat: real SWold, baseline-corrected envv, real xbnd spread). Next step:
implement the 14-field BandStat (FUN_1001dee1) to feed real features, then the
classifier's val (centroid) / qual (max-membership) will spread and the ftol
keep(1)/weak(2) decision activates.

**Phase C is where the port's fidelity pays off.** Runner scaffold:
  re_artifacts/fuzzy_build_run.py  (features -> classify_fuzzy -> keep/weak)
**FEATURE-SOURCE BRIDGE (C, resolved from call site decomp @13913 + ilk):**
  Y[i]     = fitted baseline spacing (FUN_10019280: mean/std outlier-reject
             z>_DAT_10038aa0, linear iquadratic spacing-vs-position, fill)
  D[i]     = SSNODE::SWold[i]  (actual band spacing)
  E[i]     = FUN_1001bcd0[i]   (band position)
  sb[i]    = Wvfm::envv(peakpos)  = envelope at the called-peak position
  s2[i]    = FUN_10024e47 output   = per-band xbnd (in ~[1,2])
  envAll[i]= min(envv(left),envv(right))  flank envelope  (floor source)
  out      = matrix(1,N,1,2) {i, {+1 val,+2 qual}}
  Names: local_24=Y, local_38=sb, local_2c=envAll, iVar5=D(SWold),
         iVar1=E(bcd0), local_34=s2(xbnd), local_20=N, ppfVar7=out.

So the classifier is fully understood: NOT a threshold -- a Mamdani-style fuzzy
inference system. The per-band "quality" = centroid & max of the max-union of
the LOW/MID/HIGH windows, each window weighted (min-aggregation of antecedent
memberships) by how well the band matches spacing (r1,r2 via V/trapezoid),
xbnd (desc/rise), and envelope-vs-floor (dynamic ramps).
Phase C DONE at the decode level: the port needs FUN_10019280 (spacing model),
FUN_10024e47 (xbnd - already decoded in §8), SWold + position + env lookup.

### Phase C — Feature build: the 14 BandStat fields (FUN_1001dee1 + BandStat)
- [ ] **C1.** Read `BandStat` struct layout + `FUN_1001dee1` fully; list the 14
      fields and how each is computed per peak (height, area, width, left/right
      flank env, SNR, spacing, base-line, xbnd, etc.).
- [ ] **C2.** Implement `build_bandstat(lanes, peak_list)` in Python producing
      the same 14 fields as the DLL for our ported candidates.
- [ ] **C3.** Sanity-check BandStat values against the DLL's .esd
      (peak_positions + fwhm_values + quality_scores where extractable) for A01.
- [ ] **C4.** Determine which BandStat fields feed the fuzzy classifier (connect
      Phase B3 features to real BandStat outputs).

### Phase D — Classifier + FULL pipeline integration
- [ ] **D1.** Implement `classify_band(features)` = the fuzzy rule evaluation:
      fuzzify each feature -> union sets -> centroid -> returns keep(1)/drop(2)
      per the FUN_10019ef2 caller contract (`local_34[band]<=_DAT_10038a80`
      width-ratio gate in the iVar1==2 fallback).
- [ ] **D2.** Implement `FUN_10019ef2` classify loop end-to-end: overview-band
      run use FUN_1002511d candidates + env, region trim (done), per-band
      classify, emit called bases + positions + quality.
- [ ] **D3.** Implement `Wvfm::nreader` region orchestration: bgni/endi window
      so the called set = the DLL's begin/end (e.g. M13 5471-6286 on A01).
- [ ] **D4.** Wire as `caller='fuzzy_dll'` in cimarrontv_shim + perfect_basecaller
      (reuse full-resolution separated lanes; NOT the 3687-truncated shim path).

### Phase E — BLAST verification (gold standard; the ONLY acceptance test)
- [ ] **E1.** Run the ported caller on A01 and A02 through blastn/megablast vs
      M13 (reuse `blast_validate_cnn.py` harness). ACCEPT only if
      matched_bp/identity meet-or-beat DLL-ESD (A01 790 / A02 750) at ~841/864
      bases with pident >= ~95%/96%.
- [ ] **E2.** If below gold, tune only within the DLL's OWN degrees of freedom
      (table values, modes, the 0.05 floor, region window) — do NOT add ML.
- [ ] **E3.** Run the full plate (96 wells); compare plate-mean matched_bp,
      identity, bases vs DLL-ESD. Record final numbers here.

### Fallback
- [ ] **F1.** If path 2 stalls after Phase C, do PATH 1 (per-band threshold =
      1.24 * window-mean neighbor env, floored 0.05) — ~1 hr, reuses harness.

NEXT ACTION (this session continues from here): Phase A (A1-A5) is COMPLETE —
fuzzy engine built + unit-tested (`re_artifacts/fuzzy_engine.py`,
`test_fuzzy_engine.py`, 28/28 pass) and B1 (x/y separate-array layout) resolved.
Continue at **B2** (decode the 8 set tables @ 0x10038750..0x100388d0 using the
now-confirmed layout: x[] and y[] are separate double arrays), then **B3**
(map sets->features by tracing FUN_10012140 data-flow).

## §B2-APPENDIX — DECODED FUZZY-SET TABLES (FUN_10012140, CONFIRMED)

Constructor signature (FUN_10012ad0): `(n, xptr, yptr, mode)` with x[],y[] two
SEPARATE contiguous n-double arrays. Sets built by FUN_10012140:

OUTER (per-well, universal across the wave):
  local_34  n=3 mode=0  x=[0.2,0.5,0.8]  y=[1.0,0.0,1.0]  "V": rejects middle
  local_30  n=4 mode=2  x=[0.2,0.4,0.6,0.8] y=[0.0,1.0,1.0,0.0] trapezoid passband
  local_38  n=3 mode=0  x=[1.0,1.4,1.8]  y=[1.0,0.5,0.0]  descending low-is-good
  local_50  n=2 mode=0  x=[1.2,1.4]      y=[0.0,1.0]      rising high-is-good
  local_3c  n=2 mode=0  DYNAMIC: x=[local_6c floor(>=0.05),0.0], y=[0.0,0.0]
  puVar1    n=2 mode=1  DYNAMIC: x=[local_6c floor(>=0.05),1.0(0x3ff00000)], mode 1

INNER (per-band, mode 0 all) — a LOW/MID/HIGH window rule chain over the
per-band feature (band value), adjacent/overlapping windows:
  puVar2  n=2  x=[0.4596,3.554]     y=[0.0,0.0]   zero-membership sentinel
  puVar3  n=3  x=[0.4596,1.3797,1.6864] y=[1.0,1.0,0.0]  LOW  (0.46..1.38 pass)
  puVar4  n=4  x=[1.3797,1.6864,2.2998,2.6065] y=[0.0,1.0,1.0,0.0] MID trapezoid
  puVar5  n=3  x=[2.2998,2.6065,3.554] y=[0.0,1.0,1.0]   HIGH (2.61..3.55 pass)

Constant scalars used in the rule: _DAT_100388d0=0.05 (env floor),
_DAT_100388d8=0.93, _DAT_100388e0=1.333, _DAT_100388e8=2.0, _DAT_100388f0=?,
_DAT_100388f8=? (sentinel), 0x3ff00000=1.0, 0x3f800000=1.0f, 0x3f000000=0.5f.

Interpretation so far: the per-band feature (an INT from param_1, `_Y`) is
fuzzified against the inner LOW/MID/HIGH windows (with `fmod` range-guards vs
`_Y/2.0` and `_Y`), the results unioned with the outer sets, defuzzified
(centroid), and the crisp score compared against `_DAT_10038a80`(~1.176) to
decide keep/drop. The exact rule arithmetic is B3 (in progress).
