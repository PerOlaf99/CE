# Utah 1996 engine port — working notes

Goal: reach Cimarron 3.12-level basecalling on the 63-well MegaBACE1000 M13mp18
set (user reference: 841 bp read, 95% coverage, 95.39% identity via BLAST) by a
faithful Python port of the recovered University-of-Utah 1996 basecaller patent
source in `/tmp/opencode/rsd/patent_src/`.

## Adopted baseline (current heuristic caller, A-insertion gate r=0.55/hmax=0.35)
63-well mean 93.90%, median 93.82%; A01 = 694 calls, cols=487, id=93.2% (M/cols).
pytest 6 passed.

## dfourl / NR four1 convention (RESOLVED 2026-09-03)
The patent `dfourl` is a standard NR radix-2 `four1` but the OCR'd twiddle line
is ambiguous. We validated by compiling a clean C `four1` whose twiddle advance is
a TRUE COMPLEX ROTATION (multiply by e^{iθ} each m step):

    wtemp = sin(0.5*theta); wpr = -2*wtemp*wtemp; wpi = sin(theta);
    wr=1, wi=0;
    for each m: butterfly; then  wtemp=wr; wr=wr+wr*wpr-wi*wpi; wi=wi+wi*wpr+wtemp*wpi;

This variant (called "variantR" in experiments) passes roundtrip
four1(x,+1); four1(x,-1) == n*x for ALL POWER-OF-TWO nn (2,4,8; the nn=6 failure
is expected because nn must be a power of two). The original OCR form
`wr=(wtemp=wr)*wpr-wi*wpi` FAILS roundtrip at nn>=4, so the OCR mangled the line;
the rotation form is the real code.

Sign/order mapping vs numpy (verified with 8-sample unitstep, max abs err ~5e-7):
  dfourl(data, nn, isign=+1)  == np.fft.ifft(z)*n     (i.e. forward DFT with +2πi
      exponent, unnormalized) after packing complex z from interleaved doubles.
  dfourl(data, nn, isign=-1)  == np.fft.fft(z)
So in the port: wherever C calls dfourl(x,n,+1) use ifft-based forward; wherever
it calls dfourl(x,n,-1) with trailing dRkCmul(1/n) use fft-based inverse, or
equivalently keep np.fft.fft / np.fft.ifft paired consistently per call site.
IMPORTANT: blindeconv.cxx literally calls dfourl(...,1) as its "forward" step and
dfourl(...,-1) as its "back" step (plus a 1/N rescale after each -1 call).  We
translate dfourl(isign=+1) := F_plus = np.fft.ifft(z)*N and dfourl(isign=-1) :=
F_minus = np.fft.fft(z).  Because these are inverses up to the explicit 1/N, the
natural numpy pairing fft/ifft with the explicit divide reproduces the C result.

Key interleaving facts used by blindeconv:
  * data arrays are Complex stored as interleaved doubles, 1-based index, length 2*n.
  * fftshift(v, n) with n=2*NPTS swaps v[i] <-> v[mid+i] for i=1..mid (real doubles)
    = a half-array rotation on the FULL interleaved buffer.
  * dCln/dCexp = complex ln/exp elementwise on interleaved buffer.
  * dGetComponent: real -> keep odd (re) positions, zero even; imag -> keep even, zero odd.
  * dRCmul multiplies complex by real array; dRkCmul by a real scalar.
  * dCNozeros: if z[idx]==0.0 set real = DBL_EPSILON.

## Engine constants (from patent files)
NPTS=2048, INPUTSTEP=1900, ENDPT=(INPUTSTEP+NPTS)/2, MAXPASSES=6, PERCENTILE=40,
OVRLAP=20, MAXSEG=6, MAXFBW=100, SMLGAP=1, BIGGAP=33, STATIC_BUF_SZ=NPTS/2.
fbwlut (fluor CROSSOVER=0.23, else 0.20): K=2+sqrt(log(CROSSOVER)/-0.5);
fbw[pdx] = int(0.5+(K/pdx)*NPTS/(2π)), capped at MAXFBW, pdx in SMLGAP..BIGGAP.
MB::bdStatics(fluor): lifter_[1]=lifter_[NPTS]=0, lifter_[NPTS/2+1]=1;
  fluor: bgnpt=7,endpt=24 ; nonfluor: BGNLFTR=13,ENDLFTR=23;
  m=π/(endpt-bgnpt); b=π/2 - m*endpt;
  for sdx in 2..NPTS/2: if sdx<bgnpt lifter=0 elif sdx<=endpt
      lifter=0.5*(1+sin(m*sdx+b)) else 1; mirror lifter_[NPTS-sdx+2]=lifter_[sdx].
  ww_[j] = (2π/NPTS*(j - NPTS/2))^2 for j=1..NPTS  (then squared).
blindeconv filter (recomputed when FBW changes):
  fsigma = (FBW-1)*2π/NPTS; alpha=0.5*fsigma^2; c=sqrt(π/alpha);
  filter_[sdx]=c*exp(-ww_[sdx]/(4*alpha)); then fftshift(filter_,NPTS).
Per-lane cepstral deconvolution pipeline (from blindeconv.cxx lines 138-204):
  build ivec_ complex = lane data (imag 0) length NPTS; fftshift(ivec_,2*NPTS);
  dfourl(ivec,NPTS,+1); dCNozeros; dCln; save imag phase into imag_; take real
    log-magnitude into ivec_; dfourl(ivec,NPTS,-1); dRkCmul(1/NPTS) -> cepstrum;
  multiply by lifter_ (real); dfourl(ivec,NPTS,+1); take real;
  dCadd(ivec, imag_) [recombine filtered log-mag with saved phase];
  dCexp; dRCmul by filter_; dfourl(ivec,NPTS,-1); dRkCmul(1/NPTS);
  fftshift(ivec_,2*NPTS); write back real part (odd doubles) to lane.

## nreader windowing (nreader.cxx)
SegRead seg built over rows = NPTS (windowed), each lane reads from Wvfm sc_la.
Padded tail: randPadd random [0,1) scaled by ht (q95-q5 robust range); first 10
  samples of the tail window are cosine-blended from the last real sample.
have = actual samples present (iSN-ptl+1 when padded).

## nfeeder segmentation (nfeeder.cxx)
PASSES = 1 if rawpts<NPTS else ceil((rawpts-NPTS)/INPUTSTEP)+1 capped at 6.
Pass loop: nreader(fbw,0) -> fBandSpace -> clamp spacing monotone vs previous
  pass bspac -> fbwlut(spacing) sets fbw -> nreader(fbw,1) -> output.add().
New segment start = iSl+INPUTSTEP; if newStart+NPTS>=endi then = endi-NPTS.
startTimer/stopTimer only for timing.

## nrefine flow (SegRead::nrefine) - from nrefine.cxx + SegRead.cxx
peakdet -> xbndara -> maxlanecode -> omitokn -> (refit?) -> gapcheck ->
omitokn -> setBandStats. insMetric fits quadratic spacing model coef[4],
std=sqrt(coef[3]), trim >1std, refit, vertex Ipt=-coef[1]/(2 coef[2]), flatten
far side to K. gapcheck GAP_SPLIT splits a band using fuzzy gcness.

## PKDET geometry (fmt_Pkdet.cxx) - RESOLVED 2026-09-04
set(ppk,Np,ptr,Nt): drop first peak if pxl<txl (P1++), drop last if pxn>txn
(Np--), require Nt==Np+1.  ppk_[i]=peak, ptr_[i]=trough[i] (band bgn),
ptr_[i+1]=trough[i+1] (band end).  wid_[i]=ptr[t+1]-ptr[t] = spacing between
the TWO troughs bracketing peak i (independent of peak).  gap_[1+i]=peak[i+1]
-peak[i]; gap_[1]=gap_[N+1]=medGap.  medGap = median of internal gaps:
 K=Np-1; if K odd medGap=gtmp[1+K//2] else (gtmp[K//2]+gtmp[1+K//2])/2.
medWid same recipe over wid values: (Np&1)? wtmp[1+Np//2] :
 (wtmp[Np//2]+wtmp[1+Np//2])/2.  ins_=0 (or Pb.ins()).
set(Band* Pb,Nb): build from bands; if bn.end()!=bnp.bgn() and bn.wid()>
 bnp.wid() then Pb[idx].end(bnp.bgn()) else Pb[idx+1].bgn(bn.end()).

## Wvfm::envelope + peakdet + maxlanecode (Wvfm.cxx 811+, SegRead.cxx)
envelope(noshift) computes over ALIGNED matrix (shifts physically applied;
ShftVect noshift => sv.s=0, maxshft=0). Per scan col: ascending bubble sort of
the 4 lane values tracking lane ids -> mx=v[3], smx=v[2], mi=id of v[3].
 pv[scnl]=mx  (the ENVELOPE used by peakdet / maxlanecode THR)
 pi[scnl]=mi  (argmax lane; used for base call: LNORDR[envi(bmid)-1])
 px[scnl]=xbnd: smx=max(smx,DBL_EPSILON); if mx<0.1 mx=1.0+mx/sqrt(smx)
   else mx/=smx; clamp [1.0,2.0]  (peak/2nd-peak 'peakiness')
 pb[scnl]=buzz: (max(0,v0) clipped.. ) = (v[2]c-v[0]c)/(mx-v[2]) or 0.5 if
   equal; clamp >9.99  (v[0],v[2] clamped >=0)
peakdet(npts): 1-based envv; MAXSV=0. FSM on (envv[idx],envv[idx-1]):
 vml=envv(1), v=envv(2); for idx=2..npts compare v vs vml (UP/DN/UNK); UP->DN
 records peak at idx-1; DN->UP records trough at idx-1; then vml=v, v=envv(idx+1)
 (the idx=npts tail read is 1-past and UNUSED - guard in python).
 NOTE envv() in centroid/peakdet/lo-height code = pv (max-lane envelope), NOT px.
PkDet.set then enforces interior bracketing => genuinely drops first/last peak
 when not bracketed by troughs (validated synthetically on gaussian lane data:
 23 raw peaks -> 21 kept, medGap=medWid=32=spacing, err=+1 (1-based pos)).
maxlanecode(have,bcodes): per scan 1..have: THR=0.80*envv(sdx); code=lane idx
 whose sc_la(sdx,ldx)>=THR, or 5 if a second lane also >= THR.

## xtranorm (xtranorm.cxx)
unstop(): remove "band-lite" artifact scans via product/sum criteria loops;
pass1 calls mcalign (Monte-Carlo 3-cube lane-shift hill-climb, ShftVects NCUBES=6),
lane-gain normalization dmscanlprod/dmscanlsum; pass2 skips mcalign.

## Channel-order note
RSD metadata channel_order is "TGCA".  Patent lane numbering is order of the
4 lanes as stored; lane -> base mapping uses maxlanecode with lane order from
sc_la columns; we must map patent lane (1..4) to trace rows using channel_order.

## nfeeder/nreader schedule (fmt_nfeeder.cxx) - RESOLVED 2026-09-04
fbw starts 82; PASSES = rawpts<NPTS ? 1 : ceil((rawpts-NPTS)/INPUTSTEP)+1 cap 6.
Each pass: nreader(fbw,pass2=0) -> segrd.fBandSpace(spacing) -> monotone clamp
 spacing >= ospace=bspac(previous pass) -> fbwlut(spacing) (SMLGAP..BIGGAP clamp)
 -> nreader(fbw,pass2=1) -> output.add(). Next window: iSl+=INPUTSTEP; if
 newStart+NPTS>=endi newStart=endi-NPTS.
fBandSpace: spacing = diff[(40*len)/100] of sorted consecutive band posn diffs.
fbwlut(spacing) = pmb->fbwlut[spacing] (clamped table lookup).
Implemented in megabace/utah.py part 4 (front_end / _peakband_pass / fband_space
 / fbwlut). Stage-2 has NO mcalign/xtranorm yet (sv=0) and NO omitokn/gapcheck.
Smoke test A01 baseline-only: spacing 13 -> fbw 93, ~147 bands/window, 731 total
 (vs 694 calls for tuned current caller; patent trims further via pickcuts).
Input feeding note: feeding baseline-only beats our normalize_channels output
 (180/window, spacing 12) => real engine expects its OWN gain normalization
 (xtranorm dmscanlprod/dmscanlsum) not ours; use baseline-subtracted input.

## Remaining pieces to port (in priority order)
1. omitokn + gapcheck fuzzy omit/insert logic + insMetric refits (nrefine stage2;
   files nrefine.cxx/omitokn?/gapcheck via fmt_dfourl/fgapcheck).
2. maxlanecode -> LNORDR base mapping + 0.8*env THR (have), then setBandStats
   pass2 shape/quality fields (lfit? shap cc via PATTCOEF pattern corr).
3. xtranorm + mcalign lane registration & per-lane gain normalization.
4. RdrOut OVRLAP-20 stitching of per-window SegRead results, MaxInterpeat,
   pickcuts trim, bandqual + StadenQual=98*q+1.
5. preproc: truvelAdjust gamma, sliding-min baseline(N), bgnEnd bgni/endi,
   noZeros, rawPks RatioBin (MDYN only?), fbbls best-baseline path.


## Session: stage-2 chain bring-up on A01 (sep input resolves lane coding)

Findings (all A01, M13, same SW metric as regen.py):
- `nrefine_window` lanes/codes on RAW baseline-subtracted input are useless: spectral bleed makes
  maxlanecode ambiguous/wrong (773 bands, 282 N, alignment fails, ~55-59% at-position vs baseline).
- Feeding deconvolved+normalized channels (`sep`) fixes lane coding: at-position agreement 87.9%
  vs baseline letters; confusion nearly diagonal (C/G/T clean). So the C engine's envelope/maxlanecode
  expects color-separated, per-lane-normalized lanes (MegaBACE does color separation pre-Cimarron).
- Engine result on sep: 964 bands, N 184, SW cols 547, identity 83.7%, ins 6 del 27 (baseline A01:
  694 calls, N 20, cols 487, id 93.2%).
- Extra bands come from (a) ringing doublets: ~100 positions have two bands 4-6 scans apart
  (codes mostly [X,5]); (b) ~180 spurious bands in unaligned leader/tail.
  Merging doublets thr=5 => 924 bands, id 87.3% but cols drop; thr=7 kills real bases (del 46).
- N calls concentrate at A-truth positions (57/75 code5-at-matched are A-truth); at those A peaks the
  2nd lane is 0.78 of max (A not decisive), and argmax picks right only 60%. Residual A/T separation
  problem (baseline survives it via per-channel peak detection + a_bleed_fix).
- Threshold sweep of the 0.80*env ambiguity rule on sep bands: thr 0.8 id 83.2 -> 1.0 (argmax) id 85.6,
  cols 616, del up to 40. Argmax caps ~85.6% => ceiling set by A separation + doublets, not by rule.
- Mobility correction (align_channels) before the engine destroys lane geometry (matched 285, id ~crap);
  do NOT apply to engine input.

Interpretation: the faithful port currently tops ~85% on A01, below the 93.2% heuristic baseline,
purely because our color-separation leaves A/T ambiguous at A bases and deconv ringing creates doublet
bands. Patent assumes better-separated lanes. Next lever is replication of proper color separation
(A-bleed removal / matrix calibration / xtranorm-style lane gains) so maxlanecode sees decisive lanes.

utah.nrefine_window gained `force5_concl=()` param (conclusions that force bandcode 5; default none =
keep maxlanecode code, so only genuinely two-lane -> code 5 -> 'N'). OK/N branch semantics remain
provisional (see earlier note) but barely matter for identity because bandcode dominates.

## Session 2: 63-well engine vs baseline error anatomy (decision-grade evidence)
- Engine port on all 63 wells (sep input): mean 81.7% / median 81.9 (bandcode-kept); argmax-recode:
  mean 86.2% / median 87.1. Baseline: 93.9/93.8. Port is NOT competitive on this dataset without a
  large color-separation investment; treating it as research, not a replacement.
- Baseline error anatomy across 63 wells (cols 33056, id 93.9): substitutions ~366 cols, insertions 59,
  deletions 1591. So DELETIONS drive the metric, not mismatches.
- Deletion sites are ~99% boundary artifact: interior (12.5%-87.5% of aligned ref span) identity is
  98.98% mean / 99.23% median. Caller is at data limit in the interior.
- Boundary deletions cluster at template positions shared by most reads (refc 1060 in 52/63 wells,
  1505/1515 in 49/63) = reads' noisy start/tail regions (sparse calls -> SW gap columns), not fixable
  per-base. Read trimming 15..45 calls/side changes nothing (SW block unchanged); trimming ~150/side
  lifts mean to 95.5, ~200/side to 96.6. Amplitude- and quality-based end-trim DO NOT reproduce that
  (quality model uncalibrated ~Q5-10 everywhere; amplitude edges not separable).
- Consequence: to reach the reported ~95.39% would need trimming conventions/quality recalibration that
  define the "reliable read", not further basecalling logic. Interior calling would then score ~95-99.

## Session: Cimarron 3.12 ground truth located & quantified
- User supplied Drive folder; gdown downloaded MB1000_M13_DT_Cp312_MD1/ABD/*.abd for wells A01..D07 (43 of 63). Google Drive public-link quota exhausted; .esd/.txt (96 each) and remaining .abd (D08..F03, 20 wells) still blocked. Retry loop (retry_drive.sh) no growth across passes.
- The .abd files are ABI/ABIF-format MegaBACE Sequence Analyser exports. Directory entries at END of file (28-byte entries). PBAS num1 = basecall, PLOC num1 = per-base scan positions. A01: 841 bases, SW identity 95.39% vs refRCc -> matches user's 95.39%/841bp reference exactly => these ARE the Cimarron 3.12 output (ground truth).
- Extractor: gt_eval.py -> cimarron_gt_report.csv + cimarron_calls/<well>.fasta (identical SW + metric as validation_report.csv).
- Ground truth over 43 wells (same metric as our baseline): mean id 96.84%, median 97.11%, mean readlen 873. Ours: mean 94.03%, mean calls 729. Per-well delta ours->GT mostly +2..+6 pts (worst B01/D06 +6.4; only A06 -0.3, B07 -1.1, A11 0.0 where ours >= GT).
- Template span deficit: our aligned refRC span ~248 bp shorter than Cimarron's on average: we start ~median 63 bp late (5') and end ~median 192 bp early (3'). cols ours ~530 vs GT ~760.
- The last ~150-240 template bp Cimarron calls (beyond our refRC_end) are essentially MISSING from our read: SW of that window vs our raw call gives only ~12-29 aligned cols at 75-93% id. Our tail calls (~200/read, non-aligning garbage) do NOT contain that sequence. Our caller stops making valid calls ~150-200 bp before the real 3' template end and emits spurious calls instead; Cimarron continues calling real peaks to the reaction end.
- PLOC indexed to ABD processed DATA (cnt 7389; PLOC<=7332), not comparable to .rsd raw scan coords directly. .rsd extract raw ~9646 pts.

## Session 2026-09-09 (diag_tail5): tail gap root-cause analysis — results

Established facts (validated, not speculation):
- Our `.rsd` raw traces are POINTWISE IDENTICAL to ABD raw DATA channels (corr 1.000):
  channel order TGCA -> ABD DATA: T=4, G=3, C=1, A=2. Same run data, same length (~9646/9647).
- Cimarron GT is effectively PERFECT: every aligned GT base == M13mp18 refRC exactly (0 substitutions
  in all sampled wells A01,B01,B02,D06,A06,B07; errors are ~24 indels/read only). Ref span ~964..1780.
  Cimarron reads the tail (last ref windows) at 100% match -> tail IS cleanly callable in the data.
- Our full untrimmed caller (default params) calls ~751 peaks to scan ~9645, but only ~465 align to
  ref 1040..1522; ~169 "junk tail peaks" beyond pos ~7329 (ref 1522) with median spacing ~13.
- Those junk tail peaks are NOT noise: 168/239 GT-tail predicted positions have a junk peak within
  ±5 scans (median |dx| ~3.2); ~1/3 of GT tail bases are undetected; extra junk extends past GT end.
- Letters at the 146/239 position-matched junk peaks: 63% correct vs GT (G under-called -> bleeds to
  A/C/T; T->G). Real signal present but degraded in our separated space.
- Previous "tail is A-dominated" diagnostics were MAPPING ARTIFACTS (proc->raw extrapolation broke);
  the real tail signature is ~63% letters + missing ~1/3 peaks + position offsets, not pure A-bleed.

Tested fixes that FAIL:
- Smaller morphological baseline windows (200/128/80/48): recover only ~15 bp (refspan 1522->1537).
- tail_extension=True: adds garbage (earlier).
- mobility_correct=True: catastrophic (A01 97.6%->74.4%, B07 99.2%->82%); align_channels harmful here.
- Cimarron processed DATA(9..12) is not argmax-decodable (48%) -> cannot cheaply clone its decode.

Conclusion: matching Cimarron's tail (~250 bp beyond our aligned end at ~100% accuracy) requires
essentially reproducing Cimarron's mobility-corrected shape/spacing basecalling. Our architecture
(per-channel detect + dominance + fixed/spa matrix) can only reach ~63% letters in the tail.
Open decisions for the user: (a) keep iterating on tail letter recovery, (b) focus on 5' start lag
(~60 bp) as the next achievable gain, (c) accept current state and finalize deliverables.
