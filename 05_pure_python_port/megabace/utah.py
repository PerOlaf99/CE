"""Faithful Python port of the University-of-Utah 1996 basecaller (the
MegaBACE / Cimarron engine lineage) reconstructed from the patent source in
``/tmp/opencode/rsd/patent_src``.

Stage 1 implements the blind (band-limited) deconvolution front end:
``MB`` static tables (lifter / ww / fbwlut), the cepstral-domain ``blindeconv``
filter, and the NR ``four1`` FFT mapped onto numpy.

FFT convention (verified against compiled C, see PORT_NOTES.md):
    dfourl(data, nn, isign=+1) == np.fft.ifft(z)*nn
    dfourl(data, nn, isign=-1) == np.fft.fft(z)
where z is packed from the interleaved double buffer.
"""

from __future__ import annotations

import math
import numpy as np

NPTS = 2048
INPUTSTEP = 1900
ENDPT = (INPUTSTEP + NPTS) // 2
MAXPASSES = 6
PERCENTILE = 40
OVRLAP = 20
MAXSEG = 6
STATIC_BUF_SZ = NPTS // 2
SMLGAP = 1
BIGGAP = 33
MAXFBW = 100
DBL_EPSILON = 2.220446049250313e-16
TWO_PI = 2.0 * np.pi


# --------------------------------------------------------------------------
# NR four1 mapping helpers
# --------------------------------------------------------------------------

def _fftshift_arr(a: np.ndarray) -> np.ndarray:
    """Swap the two halves of a length-N (even) array.

    Matches the C helper ``fftshift(v, n)`` which swaps v[i] <-> v[n/2+i]
    for i = 1..n/2 on 1-based arrays.
    """
    mid = a.size // 2
    out = np.empty_like(a)
    out[:mid] = a[mid:]
    out[mid:] = a[:mid]
    return out


def f_plus(z: np.ndarray) -> np.ndarray:
    """dfourl(isign=+1) on a complex vector: unnormalized forward DFT with the
    +2*pi*i exponent convention."""
    return np.fft.ifft(z) * z.size


def f_minus(z: np.ndarray) -> np.ndarray:
    """dfourl(isign=-1) on a complex vector."""
    return np.fft.fft(z)


# --------------------------------------------------------------------------
# MB static tables  (mb.cxx)
# --------------------------------------------------------------------------

class MB:
    """Encapsulates the per-fluorophore static filter tables and the cached
    band-pass filter used by ``blindeconv``."""

    def __init__(self, fluor: bool) -> None:
        self.fluor = fluor
        self.last_fbw = 0
        self._build_ww()
        self._build_lifter()
        self._build_fbwlut()
        self.filter = np.zeros(NPTS + 1)  # 1-based layout, index 0 unused

    def _build_ww(self) -> None:
        j = np.arange(NPTS + 1, dtype=np.float64)  # j[1..NPTS] used
        ww = TWO_PI / NPTS * (j - NPTS / 2)
        self.ww = ww * ww  # 1-based layout: ww[0] unused

    def _build_lifter(self) -> None:
        lifter = np.zeros(NPTS + 1)  # 1-based layout
        lifter[1] = 0.0
        lifter[NPTS] = 0.0
        lifter[NPTS // 2 + 1] = 1.0
        if self.fluor:
            bgnpt, endpt = 7.0, 24.0
        else:
            bgnpt, endpt = 13.0, 23.0
        m = np.pi / (endpt - bgnpt)
        b = np.pi / 2.0 - m * endpt
        for sdx in range(2, NPTS // 2 + 1):
            if sdx < bgnpt:
                val = 0.0
            elif sdx <= endpt:
                val = 0.5 * (1.0 + np.sin(m * float(sdx) + b))
            else:
                val = 1.0
            lifter[sdx] = val
            lifter[NPTS - sdx + 2] = val
        self.lifter = lifter

    def _build_fbwlut(self) -> None:
        crossover = 0.23 if self.fluor else 0.20
        k = 2.0 + np.sqrt(np.log(crossover) / -0.5)
        self.fbwlut = np.zeros(BIGGAP + 1)
        for pdx in range(SMLGAP, BIGGAP + 1):
            fbw = int(0.5 + (k / pdx) * NPTS / TWO_PI)
            if fbw > MAXFBW:
                fbw = MAXFBW
            self.fbwlut[pdx] = fbw

    def fbw_for_spacing(self, spacing: int) -> int:
        spacing = int(spacing)
        if spacing < SMLGAP:
            spacing = SMLGAP
        elif spacing > BIGGAP:
            spacing = BIGGAP
        return int(self.fbwlut[spacing])

    def compute_filter(self, fbw: int) -> np.ndarray:
        """(Re)build the Gaussian band-pass ``filter_`` array for ``fbw``.

        filter_[sdx] = c * exp(-ww[sdx] / (4*alpha)) for sdx = 1..NPTS then
        fftshift on the real length-NPTS array.
        """
        if fbw == self.last_fbw:
            return self.filter[1:]
        self.last_fbw = fbw
        fsigma = float((fbw - 1) * 2) * np.pi / NPTS
        alpha = 0.5 * fsigma * fsigma
        c = np.sqrt(np.pi / alpha)
        filt = c * np.exp(-self.ww[1:] / (4 * alpha))
        self.filter[1:] = _fftshift_arr(filt)
        return self.filter[1:]


# --------------------------------------------------------------------------
# blindeconv  (blindeconv.cxx)
# --------------------------------------------------------------------------

def blindeconv_lane(x: np.ndarray, mb: MB, fbw: int) -> np.ndarray:
    """Cepstral (homomorphic) band-limited deconvolution of one lane.

    ``x`` is the real lane signal of length ``NPTS``.  Returns the sharpened
    lane signal of length ``NPTS``.  Faithful to the C pipeline in
    ``SegRead::blindeconv`` lines 138-204.
    """
    n = x.size
    assert n == NPTS

    mb.compute_filter(fbw)  # ensure filter_ cache is current

    # ivec_ = complex signal with imag part zero.
    z = x.astype(np.complex128)

    # fftshift(ivec_, 2*NPTS) on the interleaved buffer == fftshift of the
    # length-N complex array.
    z = _fftshift_arr(z)

    # dfourl(ivec_, NPTS, 1)  -> complex spectrum (unnormalized)
    z = f_plus(z)

    # dCNozeros: where the whole complex value == 0.0 set real part to eps
    zero_mask = (z.real == 0.0) & (z.imag == 0.0)
    z.real[zero_mask] = DBL_EPSILON

    # dCln
    z = np.log(z)

    # save phase (imag) into imag_; take real (log magnitude)
    phase = 1j * z.imag.copy()
    z = z.real.copy()

    # dfourl(..., -1); 1/N -> cepstrum of log-magnitude
    z = f_minus(z)
    z = z / n

    # multiply by lifter (real), only real cepstrum bins are non-zero
    z = z * mb.lifter[1:]

    # dfourl(..., +1): re-estimate log-magnitude spectrum
    z = f_plus(z)
    z = z.real.copy()

    # recombine with saved phase, then exp -> filtered complex spectrum
    z = z + phase
    z = np.exp(z)

    # multiply by the band-pass filter in the frequency domain
    z = z * mb.filter[1:]

    # back to time domain
    z = f_minus(z)
    z = z / n

    # fftshift back, take real part
    z = _fftshift_arr(z)
    return z.real


def blindeconv_matrix(mat: np.ndarray, mb: MB, fbw: int) -> np.ndarray:
    """Apply ``blindeconv_lane`` to each lane column of a (NPTS, 4) matrix.

    The C code loops lanes 1..4 over the windowed ``bdproc`` matrix and writes
    the sharpened result back into the same matrix rows.
    """
    out = mat.astype(np.float64).copy()
    for lane in range(4):
        out[:, lane] = blindeconv_lane(out[:, lane], mb, fbw)
    return out


# ---------------------------------------------------------------------------
# Part 3: envelope, PkDet (bands), peakdet FSM, maxlanecode
#
# Mirrors Wvfm::envelope, PKDET (Pkdet.cxx) and SegRead::peakdet/maxlanecode.
# All scan positions inside these classes are 1-based (C-array semantics);
# convert to 0-based only when slicing numpy arrays.
# ---------------------------------------------------------------------------

MINXBND = 1.0
MAXXBND = 2.0


def envelope(lanes):
    """Wvfm::envelope over a 4-lane matrix already shifted/registered.

    ``lanes``: sequence of 4 length-N arrays (row = lane).  Lane shifts are
    taken as already applied physically (``ShftVect noshift``), so sv.s(l)=0.
    Returns dict with 1-based lists (index 0 unused) of length N:
    pv (max across lanes), pi (argmax lane 1..4), px (xbnd peakiness in
    [MINXBND, MAXXBND]), pb (buzz banding metric).
    """
    lanes = np.asarray(lanes, dtype=np.float64)
    if lanes.ndim == 1:
        lanes = lanes[None, :]
    nl, n = lanes.shape
    assert nl == 4
    pv = [0.0] * (n + 1)
    pi = [0] * (n + 1)
    px = [0.0] * (n + 1)
    pb = [0.0] * (n + 1)
    for scnl in range(1, n + 1):
        v = [lanes[l, scnl - 1] for l in range(nl)]
        i = [1, 2, 3, 4]
        # ascending bubble sort over the 4 lane values (keeps lane ids)
        for a in range(4):
            for b in range(3 - a):
                if v[b] > v[b + 1]:
                    v[b], v[b + 1] = v[b + 1], v[b]
                    i[b], i[b + 1] = i[b + 1], i[b]
        mx = v[3]
        smx = v[2]
        pv[scnl] = mx
        pi[scnl] = i[3]
        lo1 = v[0] if v[0] > 0.0 else 0.0
        lo3 = v[2] if v[2] > 0.0 else 0.0
        pb[scnl] = (lo3 - lo1) / (mx - v[2]) if mx != v[2] else 0.5
        if pb[scnl] > 9.99:
            pb[scnl] = 9.99
        smx = smx if smx >= DBL_EPSILON else DBL_EPSILON
        if mx < 0.1:
            mx = MINXBND + mx / math.sqrt(smx)
        else:
            mx = mx / smx
        if mx > MAXXBND:
            mx = MAXXBND
        elif mx < MINXBND:
            mx = MINXBND
        px[scnl] = mx
    return {'pv': pv, 'pi': pi, 'px': px, 'pb': pb}


def _imedian(sorted_list_1based):
    """Median of a 1-based sorted list (index 0 unused), C PKDET convention."""
    k = len(sorted_list_1based) - 1
    if k < 1:
        return 0
    if k & 1:
        mid = 1 + k // 2
        return sorted_list_1based[mid]
    mid = k // 2
    return (sorted_list_1based[mid] + sorted_list_1based[mid + 1]) // 2


class PkDet:
    """PKDET container: peaks + interleaved troughs define the 'bands'.

    Positions stored 1-based.  ``gap_[i]`` = spacing to previous peak,
    ``gap_[i+1]`` = spacing to next peak (end gaps = medGap).  ``wid_[i]`` =
    trough[i+1] - trough[i] (bracketing troughs).  ``ins_`` insertion flag.
    """

    def __init__(self):
        self.ppk = None
        self.ptr = None
        self.gap = None
        self.wid = None
        self.ins = None
        self.Np = 0
        self.Nt = 0
        self.medGap = 0
        self.medWid = 0

    def set_ppkptr(self, ppk, Np, ptr, Nt):
        P1 = 1
        pxl, pxn = ppk[1], ppk[Np]
        txl, txn = ptr[1], ptr[Nt]
        if pxl < txl:
            P1 += 1
        if pxn > txn:
            Np -= 1
        Np_ = Np - P1 + 1
        Nt_ = Nt
        if (Nt_ < 2) or (Nt_ != (Np_ + 1)):
            return 0
        self.ppk = [0] * (Np_ + 1)
        self.wid = [0] * (Np_ + 1)
        self.ins = [0] * (Np_ + 1)
        self.ptr = [0] * (Nt_ + 1)
        self.gap = [0] * (Nt_ + 1)
        wtmp = [0] * (Np_ + 1)
        gtmp = [0] * (Np_)
        Pl, Tl = P1, 1
        for idx in range(1, Np_ + 1):
            self.ppk[idx] = ppk[Pl]
            Pl += 1
            self.ptr[idx] = ptr[Tl]
            Tl += 1
            self.wid[idx] = ptr[Tl] - ptr[Tl - 1]
            self.ins[idx] = 0
            wtmp[idx] = self.wid[idx]
            if idx < Np_:
                self.gap[1 + idx] = ppk[Pl] - ppk[Pl - 1]
                gtmp[idx] = self.gap[1 + idx]
        self.ptr[Np_ + 1] = ptr[Tl]
        self.medGap = _imedian(sorted(gtmp[1:]))
        self.gap[1] = self.medGap
        self.gap[Np_ + 1] = self.medGap
        self.medWid = _imedian(sorted(wtmp[1:]))
        self.Np = Np_
        self.Nt = Nt_
        return 1

    def set_bands(self, bands):
        """set( Band*, Nb ): bands is a list of (bgn,mid,end,ins) tuples 1-based."""
        Nb = len(bands)
        self.Np = Nb
        self.Nt = Nb + 1
        if self.Nt < 2:
            return 0
        self.ppk = [0] * (Nb + 1)
        self.wid = [0] * (Nb + 1)
        self.ins = [0] * (Nb + 1)
        self.ptr = [0] * (self.Nt + 1)
        self.gap = [0] * (self.Nt + 1)
        wtmp = [0] * (Nb + 1)
        gtmp = [0] * (Nb)
        bl = [list(b) for b in bands]
        for idx in range(1, Nb):
            bn, bnpl = bl[idx - 1], bl[idx]
            if bn[2] != bnpl[0]:
                if bn[2] - bn[0] + 1 > bnpl[2] - bnpl[0] + 1:
                    bl[idx - 1][2] = bnpl[0]
                else:
                    bl[idx][0] = bn[2]
            bn, bnpl = bl[idx - 1], bl[idx]
            self.ppk[idx] = bn[1]
            self.ptr[idx] = bn[0]
            self.wid[idx] = bn[2] - bn[0] + 1
            self.ins[idx] = bn[3]
            wtmp[idx] = self.wid[idx]
            self.gap[1 + idx] = bnpl[1] - bn[1]
            gtmp[idx] = self.gap[1 + idx]
        bn = bl[Nb - 1]
        self.ppk[Nb] = bn[1]
        self.ptr[Nb] = bn[0]
        self.ptr[Nb + 1] = bn[2]
        self.wid[Nb] = self.ptr[Nb + 1] - self.ptr[Nb]
        self.ins[Nb] = bn[3]
        wtmp[Nb] = self.wid[Nb]
        self.medGap = _imedian(sorted(gtmp[1:]))
        self.gap[1] = self.medGap
        self.gap[Nb + 1] = self.medGap
        self.medWid = _imedian(sorted(wtmp[1:]))
        return 1

    def bbgn(self, idx):
        return self.ptr[idx]

    def bmid(self, idx):
        return self.ppk[idx]

    def bend(self, idx):
        return self.ptr[idx + 1]

    def bwid(self, idx):
        return self.wid[idx]

    def lgap(self, idx):
        return self.gap[idx]

    def rgap(self, idx):
        return self.gap[idx + 1]

    def band(self, idx):
        return (self.ptr[idx], self.ppk[idx], self.ptr[idx + 1], self.ins[idx])

    def npk(self):
        return self.Np

    def ntr(self):
        return self.Nt


def peakdet(envv, npts):
    """SegRead::peakdet zero-crossing FSM on the 1-based envelope ``envv``.

    Returns (ppk, Np, ptr, Nt): peak positions (local maxima) and trough
    positions (local minima) of the envelope, as 1-based scan indices.
    """
    MAXSV = 0  # nsv_.maxshft() when aligned with noshift already applied
    ppk = [0] * (npts + 1)
    ptr = [0] * (npts + 1)
    Np = Nt = 0
    vml = envv[MAXSV + 1]
    v = envv[MAXSV + 2]
    st = 0  # ST_UNK
    ST_UNK, ST_UP, ST_DN = 0, 1, 2
    for idx in range(MAXSV + 2, npts + 1):
        if st == ST_UNK:
            if v > vml:
                st = ST_UP
            elif v < vml:
                st = ST_DN
        elif st == ST_UP:
            if v < vml:
                st = ST_DN
                Np += 1
                ppk[Np] = idx - 1
        elif st == ST_DN:
            if v > vml:
                st = ST_UP
                Nt += 1
                ptr[Nt] = idx - 1
        vml = v
        if idx + 1 <= npts:
            v = envv[idx + 1]
    return ppk, Np, ptr, Nt


def maxlanecode(envv, lanes, npts, scanl):
    """SegRead::maxlanecode: per scan, lane id with value >= 0.80*envelope.

    Returns 1-based list of length scanl+1 of codes 0..5 (5 == ambiguous).
    """
    lanes = np.asarray(lanes, dtype=np.float64)
    bcodes = [0] * (scanl + 1)
    MAXSV = 0
    for sdx in range(MAXSV + 1, npts + 1):
        THR = 0.80 * envv[sdx]
        code = 0
        for ldx in range(1, 5):
            if lanes[ldx - 1, sdx - 1] >= THR:
                code = ldx if code == 0 else 5
            if code == 5:
                break
        bcodes[sdx] = code
    return bcodes


# ---------------------------------------------------------------------------
# Part 4: windowed multi-pass front end (nfeeder + nreader schedule)
#
# Mirrors Wvfm::nfeeder/nreader at the signal level: overlapping NPTS windows
# stepped by INPUTSTEP, blindeconv(FBW) per window, envelope + FSM peakdet,
# PkDet bands, spacing = 40th percentile of consecutive band positions
# (fBandSpace over the pass-0 band list), fbwlut monotone-clamped against the
# previous window, second blindeconv at the adapted FBW, bands re-extracted.
# Lane alignment/registration (xtranorm/mcalign) is NOT yet applied (sv=0).
# ---------------------------------------------------------------------------

PERCENTILE = 40
FROMEND = (NPTS - INPUTSTEP) // 10


def fband_space(posns):
    """SegRead::fBandSpace: spacing = 40th percentile of consecutive positions."""
    if len(posns) < 2:
        return None
    diff = sorted(posns[i + 1] - posns[i] for i in range(len(posns) - 1))
    idx = (PERCENTILE * len(diff)) // 100
    return diff[idx]


def fbwlut(spacing, mb=None):
    if spacing < SMLGAP:
        spacing = SMLGAP
    elif spacing > BIGGAP:
        spacing = BIGGAP
    if mb is None:
        mb = MB(fluor=True)
    return int(mb.fbwlut[spacing])


class SegmentBands:
    """Outcome of one nreader window: bands + base calls + per-scan lane codes.

    ``offs`` = absolute start scan of the window (aligned frame, sv applied).
    Positions are kept as *global* 0-based trace indices for downstream use.
    """

    def __init__(self):
        self.bands = []       # list of (mid, bgn, end) global 0-based
        self.seq = []         # base call per band
        self.spacing = None
        self.fbw = None


def _peakband_pass(window_lanes, fbw, mb, pos0):
    """One nreader pass on a (4, NPTS) window: blindeconv -> envelope -> bands.

    Returns (bmid_global_list, seq_list, pk, env).
    """
    w = window_lanes.copy()
    if fbw is not None:
        w = blindeconv_matrix(w.T, mb, fbw).T
    env = envelope(w)
    ppk, Np, ptr, Nt = peakdet(env['pv'], NPTS)
    pk = PkDet()
    if pk.set_ppkptr(ppk, Np, ptr, Nt) != 1 or pk.Np < 1:
        return [], [], pk, env
    bcodes = maxlanecode(env['pv'], w, NPTS, NPTS)
    mids = [pk.bmid(i) for i in range(1, pk.Np + 1)]
    seq = []
    for i in range(1, pk.Np + 1):
        m = pk.bmid(i)
        code = bcodes[m]
        if code == 0:
            code = env['pi'][m]
        seq.append(code)
    global_mids = [pos0 + m - 1 for m in mids]
    return global_mids, seq, pk, env


def front_end(traces, mb=None, max_passes=None, verbose=False):
    """nfeeder-equivalent over a full preprocessed 4-lane trace.

    Returns (bands, seq_list, meta) with global 0-based band mids.  ``seq``
    entries are lane codes 1..4 (or 5 ambiguous).  This is the front end only:
    no mcalign shifts, no omitokn/gapcheck call refinement (nrefine stage 2).
    """
    if mb is None:
        mb = MB(fluor=True)
    n = traces.shape[1]
    if max_passes is None:
        if n < NPTS:
            max_passes = 1
        else:
            max_passes = int(math.ceil(float(n - NPTS) / float(INPUTSTEP))) + 1
            if max_passes > MAXPASSES:
                max_passes = MAXPASSES
    fbw = 82
    prev_spacing = None
    bands_all = []
    seq_all = []
    meta = []
    iSl = 0
    endi = n
    for passNr in range(1, max_passes + 1):
        endpt = iSl + NPTS - 1
        if endpt < endi:
            w = traces[:, iSl:endpt + 1]
        else:
            w = np.zeros((4, NPTS))
            have = endi - iSl
            w[:, :have] = traces[:, iSl:endi]
        mids0, seq0, pk0, env0 = _peakband_pass(w, fbw, mb, iSl)
        sp = fband_space(mids0)
        if sp is None:
            break
        if prev_spacing is not None and sp < prev_spacing:
            sp = prev_spacing
        prev_spacing = sp
        fbw = fbwlut(sp, mb)
        mids1, seq1, pk1, env1 = _peakband_pass(w, fbw, mb, iSl)
        bands_all.extend(mids1)
        seq_all.extend(seq1)
        meta.append((passNr, sp, fbw, len(mids1), iSl))
        newStart = iSl + INPUTSTEP
        if (newStart + NPTS) >= endi:
            newStart = endi - NPTS
            if newStart <= iSl:
                break
        iSl = newStart
    return bands_all, seq_all, meta


# ---------------------------------------------------------------------------
# Part 5: SegRead::nrefine stage 2 (omission / insertion / calling)
# ---------------------------------------------------------------------------

def _centroid(pv, bgn, end):
    """SegRead::centroid of the envelope (pv) over 1-based [bgn, end]."""
    n = end - bgn + 1
    if n < 2:
        return bgn + n // 2
    minv = min(pv[bgn:end + 1])
    numer = 0.0
    denom = 0.0
    for idx in range(bgn + 1, end + 1):
        jdx = idx - 1
        vj = pv[jdx] - minv
        vi = pv[idx] - minv
        numer += vj * (2.0 * jdx + idx) + vi * (jdx + 2.0 * idx)
        denom += (vj + vi)
    if denom <= 0.0:
        return bgn + n // 2
    return int(math.floor(numer / (3.0 * denom) + 0.5))


def nrefine_window(w, fbw, mb, letters='TGCA', force5_concl=()):
    """SegRead::nrefine over one (4, NPTS) window (already blindeconvolved).

    Returns dict with 1-based scan positions in the window:
      mid[], bgn[], end[], ins[], code[] (lane 1..5), ok/n/omit kept flags.
    ``code`` is the bandcode lane (5 two-lane) -> base later via LNORDR
    mapping; ``letters`` maps trace row 0..3 to its base letter (used to count
    GC-richness inside gapcheck).  Returns None on too-few-bands abort.
    """
    from megabace.fuzzy import omitokn, gapcheck, insMetric

    env = envelope(w)
    pv = env['pv']
    ppk, Np, ptr, Nt = peakdet(pv, NPTS)
    raw = PkDet()
    if raw.set_ppkptr(ppk, Np, ptr, Nt) != 1 or raw.Np < 1:
        return None
    bandcode = maxlanecode(pv, w, NPTS, NPTS)
    N = raw.Np
    bmid = [raw.bmid(i) for i in range(1, N + 1)]
    lgap = [raw.lgap(i) for i in range(1, N + 1)]
    rgap = [raw.rgap(i) for i in range(1, N + 1)]
    insSP = insMetric(bmid, lgap)
    if insSP is None:
        return None
    ht = [pv[raw.bmid(i)] for i in range(1, N + 1)]
    lo = [min(pv[raw.bbgn(i)], pv[raw.bend(i)]) for i in range(1, N + 1)]
    xb = [env['px'][raw.bmid(i)] for i in range(1, N + 1)]
    om = omitokn(insSP, ht, lo, lgap, rgap, xb)
    if om is None:
        return None
    seq = []
    bands = []
    for i in range(1, N + 1):
        d = int(round(om[i - 1][0]))
        if d == 3:  # BAND_OMIT -> drop
            continue
        if d in force5_concl:
            bandcode[raw.bmid(i)] = 5
        b = raw.band(i)
        bands.append(list(b))
        pi = env['pi'][raw.bmid(i)]
        seq.append(letters[pi - 1])
    if len(bands) < 1:
        return None
    # refit models on the keepers, then gapcheck for split decisions
    pk = PkDet()
    if pk.set_bands(bands) != 1 or pk.Np < 2:
        return None
    m2 = [pk.bmid(i) for i in range(1, pk.Np + 1)]
    l2 = [pk.lgap(i) for i in range(1, pk.Np + 1)]
    r2 = [pk.rgap(i) for i in range(1, pk.Np + 1)]
    w2 = [pk.bwid(i) for i in range(1, pk.Np + 1)]
    insSP = insMetric(m2, l2)
    insWD = insMetric(m2, w2)
    if insSP is None or insWD is None:
        return None
    om = gapcheck(insSP, insWD, l2, w2, seq)
    if om is None:
        return None
    out = [list(bands[0])]
    jdx = 1
    for idx in range(2, pk.Np + 1):
        if int(round(om[idx - 1][0])) == 2:  # GAP_SPLIT
            m4 = idx - 2
            if insSP[m4] == 0:
                return None
            ratio = r2[m4] / float(insSP[m4])
            numSmallGap = int(0.5 + 0.2 + ratio)
            if numSmallGap == 0:
                return None
            newSP = r2[m4] // numSmallGap
            mid = pk.bmid(m4 + 1)
            for _ndx in range(1, numSmallGap):
                mid += newSP
                bgn = mid - newSP // 2
                end = bgn + newSP - 1
                if bgn < 1:
                    bgn = 1
                if end > NPTS:
                    end = NPTS
                c = _centroid(pv, bgn, end)
                out.append([bgn, c, end, 1])
                jdx += 1
                if jdx >= STATIC_BUF_SZ:
                    return None
        out.append(list(bands[idx - 1]))
        jdx += 1
        if jdx >= STATIC_BUF_SZ:
            return None
    pk = PkDet()
    if pk.set_bands(out) != 1 or pk.Np < 1:
        return None
    # final omitokn pass over the refined list
    m3 = [pk.bmid(i) for i in range(1, pk.Np + 1)]
    l3 = [pk.lgap(i) for i in range(1, pk.Np + 1)]
    r3 = [pk.rgap(i) for i in range(1, pk.Np + 1)]
    insSP = insMetric(m3, l3)
    if insSP is None:
        return None
    ht = [pv[pk.bmid(i)] for i in range(1, pk.Np + 1)]
    lo = [min(pv[pk.bbgn(i)], pv[pk.bend(i)]) for i in range(1, pk.Np + 1)]
    xb = [env['px'][pk.bmid(i)] for i in range(1, pk.Np + 1)]
    om = omitokn(insSP, ht, lo, l3, r3, xb)
    if om is None:
        return None
    final_mid = []
    final_bgn = []
    final_end = []
    final_code = []
    final_ins = []
    for i in range(1, pk.Np + 1):
        d = int(round(om[i - 1][0]))
        if d == 3:
            continue
        if d in force5_concl:
            bandcode[pk.bmid(i)] = 5
        b = pk.band(i)
        final_mid.append(b[1])
        final_bgn.append(b[0])
        final_end.append(b[2])
        final_ins.append(b[3])
        final_code.append(bandcode[b[1]])
    return {
        'mid': final_mid, 'bgn': final_bgn, 'end': final_end,
        'code': final_code, 'ins': final_ins,
    }
