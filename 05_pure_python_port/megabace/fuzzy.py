"""Fuzzy omission/insertion logic of the Utah 1996 basecaller.

Faithful Python port of the recovered patent sources:
  * fomitokn.c    -> omitokn   (keep / N / OMIT decision per detected band)
  * fgapcheck.c   -> gapcheck  (NORMAL / SPLIT decision on large gaps)
  * nrefine.cxx   -> insMetric (quadratic insertion-spacing model)

The fuzzy memberships are piecewise-linear.  Hedges act on membership
values: NOHEDGE=identity, VERY=square, SOMEWHAT=sqrt, CONTINT=(y>=0.5)?
sqrt(y):y*y.  AND=min, OR=max, NOT=1-x.  Disjunction of rules is a pointwise
max envelope; the crisp conclusion is the centroid of that envelope over the
conclusion domain, and rule compatibility is the peak envelope height.
"""

import math

import numpy as np

AND = min
OR = max


def NOT(x):
    return 1.0 - x


def _contint(y):
    return math.sqrt(y) if y >= 0.5 else y * y


def _contdeint(y):
    return y * y if y >= math.sqrt(0.5) else math.sqrt(y)


HEDGE_PH = {
    'none': (lambda y: y),
    'very': (lambda y: y * y),
    'somewhat': (lambda y: math.sqrt(y)),
    'contint': _contint,
}
HEDGE_UNPH = {
    'none': (lambda y: y),
    'very': (lambda y: math.sqrt(y)),
    'somewhat': (lambda y: y * y),
    'contint': _contdeint,
}


class CFuzzySet:
    """Piecewise-linear membership over sorted breakpoints x[0..n-1].

    ``membership(pt)`` interpolates the stored (raw) y and then applies the
    hedge; outside the breakpoint range the membership is flat at the nearest
    end value.  ``scale`` and ``negate`` operate on the raw y values.
    """

    def __init__(self, xpts, ypts, hedge='none'):
        self.x = [float(v) for v in xpts]
        self.y = [float(v) for v in ypts]
        self.n = len(self.x)
        self.ph = HEDGE_PH[hedge]
        self.unph = HEDGE_UNPH[hedge]

    def membership(self, pt):
        if self.n == 0:
            return 0.0
        if pt <= self.x[0]:
            return self.ph(self.y[0])
        if pt >= self.x[self.n - 1]:
            return self.ph(self.y[self.n - 1])
        lo, hi = 0, self.n - 1
        while True:
            mid = (lo + hi) // 2
            if mid == lo:
                break
            if self.x[mid] < pt:
                lo = mid
            else:
                hi = mid
        yh = self.y[hi]
        yhml = self.y[hi - 1]
        frac = (pt - self.x[hi - 1]) / (self.x[hi] - self.x[hi - 1])
        yy = yhml + frac * (yh - yhml)
        return self.ph(yy)

    def scale(self, fac):
        self.y = [v * fac for v in self.y]

    def negate(self):
        self.y = [1.0 - v for v in self.y]

    def compat_index(self):
        return self.ph(max(self.y))

    def centroid(self, xmin=None, xmax=None, dx=1e-3):
        """Centroid of the hedged membership envelope over [xmin, xmax]."""
        if xmin is None:
            xmin = self.x[0]
        if xmax is None:
            xmax = self.x[self.n - 1]
        n = int(math.ceil((xmax - xmin) / dx))
        if n < 2:
            return 0.0
        xs = [xmin + i * dx for i in range(n + 1)]
        ys = [self.membership(x) for x in xs]
        numer = 0.0
        denom = 0.0
        for i in range(n):
            x1, x2 = xs[i], xs[i + 1]
            y1, y2 = ys[i], ys[i + 1]
            denom += (y1 + y2) * (x2 - x1) / 2.0
            numer += (y1 * (2 * x1 + x2) + y2 * (x1 + 2 * x2)) * (x2 - x1) / 6.0
        if abs(denom) < 1e-20:
            return 0.0
        return numer / denom


def _max_envelope(sets, xmin, xmax, dx=1e-3):
    n = int(math.ceil((xmax - xmin) / dx))
    xs = [xmin + i * dx for i in range(n + 1)]
    env = [0.0] * len(xs)
    for s in sets:
        for j, x in enumerate(xs):
            m = s.membership(x)
            if m > env[j]:
                env[j] = m
    return xs, env


def _envelope_centroid(sets, xmin, xmax, dx=1e-3):
    """Vectorized centroid + peak height of the max envelope of the rules.

    Rule sets are always NOHEDGE here, and ``np.interp`` reproduces the flat
    extension of ``membership`` outside the breakpoints exactly, so the result
    matches the C piecewise-vertex computation on a fine grid.
    """
    grid = np.arange(xmin, xmax + 0.5 * dx, dx)
    env = np.zeros_like(grid)
    for s in sets:
        vals = np.interp(grid, np.asarray(s.x), np.asarray(s.y))
        np.maximum(env, vals, out=env)
    dxg = np.diff(grid)
    y0 = env[:-1]
    y1 = env[1:]
    x0 = grid[:-1]
    x1 = grid[1:]
    denom = 0.5 * np.sum((y0 + y1) * dxg)
    if abs(denom) < 1e-20:
        return 0.0, 0.0
    numer = np.sum((y0 * (2.0 * x0 + x1) + y1 * (x0 + 2.0 * x1)) * dxg) / 6.0
    return float(numer / denom), float(env.max())


# ---------------------------------------------------------------------------
# omitokn  (fomitokn.c)
# ---------------------------------------------------------------------------

_OKSP_X = [0.2, 0.5, 0.8]
_OKSP_Y = [1.0, 0.0, 1.0]
_ABSP_X = [0.2, 0.4, 0.6, 0.8]
_ABSP_Y = [0.0, 1.0, 1.0, 0.0]
_TIXB_X = [1.0, 1.4, 1.8]
_TIXB_Y = [1.0, 0.5, 0.0]
_OKXB_X = [1.2, 1.4]
_OKXB_Y = [0.0, 1.0]
_CONCL_X = [0.4596, 3.5540]
_OK_X = [0.4596, 1.3797, 1.6864]
_OK_Y = [1.0, 1.0, 0.0]
_N_X = [1.3797, 1.6864, 2.2998, 2.6065]
_N_Y = [0.0, 1.0, 1.0, 0.0]
_OMIT_X = [2.2998, 2.6065, 3.5540]
_OMIT_Y = [0.0, 1.0, 1.0]
_DX = 1e-3


def omitokn(pinS, pht, plo, pLsp, pRsp, pxb):
    """Per-band OK/N/OMIT decision.

    Inputs are 0-based sequences of length NPK:
      pinS - model insertion spacing, pht - peak height (envv at bmid),
      plo  - valley height (min(envv at band ends)), pLsp/pRsp - spacing to
      the left/right neighbouring peak, pxb - xbanding peakiness.
    Returns list of (concl, cmpti).  Decision (nrefine): int(round(concl))
      -> 1 BAND_OK, 2 BAND_N, 3 BAND_OMIT.
    """
    npk = len(pinS)
    mean_plo = sum(plo) / float(npk) if npk else 0.0
    tiHt = CFuzzySet([0.4 * mean_plo, 1.1 * mean_plo], [1.00, 0.00], 'none')
    okHt = CFuzzySet([0.5 * mean_plo, 1.5 * mean_plo], [0.00, 1.00], 'somewhat')
    okSP = CFuzzySet(_OKSP_X, _OKSP_Y, 'none')
    abSP = CFuzzySet(_ABSP_X, _ABSP_Y, 'very')
    tiXb = CFuzzySet(_TIXB_X, _TIXB_Y, 'none')
    okXb = CFuzzySet(_OKXB_X, _OKXB_Y, 'none')
    out = []
    for idx in range(npk):
        insp = pinS[idx]
        if insp == 0.0:
            return None
        if pLsp[idx] < (insp / 2.0):
            modLsp = insp / 2.0
        else:
            modLsp = math.fmod(pLsp[idx], insp)
        if pRsp[idx] < (insp / 2.0):
            modRsp = insp / 2.0
        else:
            modRsp = math.fmod(pRsp[idx], insp)
        modLsp /= insp
        modRsp /= insp
        okLsp = okSP.membership(modLsp)
        okRsp = okSP.membership(modRsp)
        abLsp = abSP.membership(modLsp)
        abRsp = abSP.membership(modRsp)
        oksp = OR(okLsp, okRsp)
        absp = OR(abLsp, abRsp)
        tixb = tiXb.membership(pxb[idx])
        okxb = okXb.membership(pxb[idx])
        tiht = tiHt.membership(pht[idx])
        okht = okHt.membership(pht[idx])
        rule_ok = CFuzzySet(_OK_X, _OK_Y, 'none')
        rule_n = CFuzzySet(_N_X, _N_Y, 'none')
        rule_om = CFuzzySet(_OMIT_X, _OMIT_Y, 'none')
        rule_ok.scale(AND(okxb, OR(okht, oksp)))
        rule_n.scale(AND(tixb, OR(okht, AND(oksp, tiht))))
        rule_om.scale(AND(tiht, absp))
        concl, cmpti = _envelope_centroid(
            [rule_ok, rule_n, rule_om], _CONCL_X[0], _CONCL_X[1], _DX)
        out.append((concl, cmpti))
    return out


# ---------------------------------------------------------------------------
# gapcheck  (fgapcheck.c)
# ---------------------------------------------------------------------------

_NPREV = 5
_A = 0.5079
_B = 1.5002
_C = 1.5069
_D = 2.5063


def _weight(n, gs, cs):
    return 1.0 - math.sqrt((float((n - gs) * (n - gs) + (n - cs) * (n - cs))
                            / (2.0 * float(n * n))))


def _gcness(n, gs, cs, mx, my):
    lh = (n + 1) // 2
    sh = n - lh
    if mx == 0:
        mx = lh
    if my == 0:
        my = sh
    normalize = _weight(n, mx, my)
    rv = _weight(n, gs, cs) / normalize
    if rv > 1.0:
        rv = 1.0
    return rv * rv


def gapcheck(pis, piw, ps, pw, pseq):
    """Per-band NORMAL/SPLIT decision on possibly missed bases.

    0-based inputs of length nbands:
      pis - model insertion spacing, piw - model insertion width,
      ps - real spacing to previous peak (lgap), pw - real band width (bwid),
      pseq - called base letters per band.
    Returns list of (concl, cmpti).  Decision (nrefine): int(round(concl))
      -> 1 GAP_NORMAL, 2 GAP_SPLIT.
    """
    nbands = len(pis)
    ciBgWD = CFuzzySet([0.0, 1.0], [0.0, 1.0], 'contint')
    ciBgGP = CFuzzySet([0.42, 0.6, 1.0], [0.0, 1.0, 1.0], 'very')
    ciMdGP = CFuzzySet([0.25, 0.3, 0.45, 0.57], [0.0, 1.0, 1.0, 0.0], 'none')
    ciSmGP = CFuzzySet([-1.0, -0.5, 0.0], [1.0, 1.0, 0.0], 'contint')
    gc = [0.0] * nbands
    gs = [0] * nbands
    cs = [0] * nbands
    out = []
    # gc[] pass: composition + spacing compression over previous bands
    for idx in range(nbands):
        bgnj = idx - _NPREV if idx > _NPREV else 0
        prvgaps = 0.0
        for jdx in range(bgnj, idx):
            prvgaps += ps[jdx]
            ch = pseq[jdx]
            if ch == 'G':
                gs[idx] += 1
            elif ch == 'C':
                cs[idx] += 1
        expgaps = piw[idx] * (idx - bgnj)
        if expgaps == 0.0 or prvgaps < expgaps:
            prvgaps = 1.0
            expgaps = 1.0
        gc[idx] = (expgaps / prvgaps) * _gcness(
            _NPREV, gs[idx], cs[idx], _NPREV // 2, _NPREV // 2)
    for idx in range(nbands):
        if pis[idx] == 0.0 or piw[idx] == 0.0:
            return None
        rawgap_cur = (ps[idx] / pis[idx]) - 1.0
        rawgap_prev = 0.0 if idx == 0 else (ps[idx - 1] / pis[idx]) - 1.0
        rawwid_cur = (pw[idx] / piw[idx]) - 1.0
        rawwid_prev = 0.0 if idx == 0 else (pw[idx - 1] / piw[idx]) - 1.0
        bg_cur = ciBgGP.membership(rawgap_cur)
        bg_prev = ciBgGP.membership(rawgap_prev)
        md_cur = ciMdGP.membership(rawgap_cur)
        md_prev = ciMdGP.membership(rawgap_prev)
        sm_cur = ciSmGP.membership(rawgap_cur)
        sm_prev = ciSmGP.membership(rawgap_prev)
        bw_cur = ciBgWD.membership(rawwid_cur)
        bw_prev = ciBgWD.membership(rawwid_prev)
        gcrich = gc[idx]
        conj1 = AND(bg_cur, gcrich)
        conj2 = AND(bg_cur, sm_prev)
        conj2 = AND(conj2, NOT(bw_cur))
        conj2 = AND(conj2, NOT(bw_prev))
        rule_norm = CFuzzySet([_A, _B, _C], [1.0, 1.0, 0.0], 'none')
        rule_norm.scale(OR(NOT(bg_cur), OR(conj1, conj2)))
        conj1 = AND(bg_cur, OR(bw_prev, bw_cur))
        conj2 = AND(bg_cur, AND(NOT(sm_prev), NOT(gcrich)))
        rule_split = CFuzzySet([_B, _C, _D], [0.0, 1.0, 1.0], 'none')
        rule_split.scale(OR(conj1, conj2))
        concl, cmpti = _envelope_centroid(
            [rule_norm, rule_split], _A, _D, _DX)
        out.append((concl, cmpti))
    return out


# ---------------------------------------------------------------------------
# insMetric / quadratic fit  (nrefine.cxx)
# ---------------------------------------------------------------------------

def quadratic_fit(xs, ys):
    """Least-squares quadratic coef = [a, b, c, residual_variance]."""
    n = len(xs)
    if n < 3:
        return None
    sx = sum(xs)
    sx2 = sum(v * v for v in xs)
    sx3 = sum(v * v * v for v in xs)
    sx4 = sum(v ** 4 for v in xs)
    sy = sum(ys)
    sxy = sum(x * y for x, y in zip(xs, ys))
    sx2y = sum(x * x * y for x, y in zip(xs, ys))
    a = [[n, sx, sx2], [sx, sx2, sx3], [sx2, sx3, sx4]]
    bvec = [sy, sxy, sx2y]
    # Gaussian elimination with partial pivoting
    for col in range(3):
        piv = max(range(col, 3), key=lambda r: abs(a[r][col]))
        if abs(a[piv][col]) < 1e-14:
            return None
        a[col], a[piv] = a[piv], a[col]
        bvec[col], bvec[piv] = bvec[piv], bvec[col]
        for r in range(col + 1, 3):
            f = a[r][col] / a[col][col]
            for c in range(col, 3):
                a[r][c] -= f * a[col][c]
            bvec[r] -= f * bvec[col]
    coef = [0.0, 0.0, 0.0]
    for r in (2, 1, 0):
        coef[r] = bvec[r]
        for c in range(r + 1, 3):
            coef[r] -= a[r][c] * coef[c]
        coef[r] /= a[r][r]
    var = 0.0
    for x, y in zip(xs, ys):
        r = y - (coef[0] + x * coef[1] + x * x * coef[2])
        var += r * r
    var /= float(n)
    return [coef[0], coef[1], coef[2], var]


def _nint(x):
    return int(math.floor(x + 0.5))


def insMetric(px, py):
    """insMetric: quadratic model of spacing (or width) vs scan position.

    0-based int sequences of length N.  Returns the model int array (or None
    if a robust fit is impossible).  Mirrors the outlier-trim/refit/flatten
    behaviour of the C code.
    """
    n = len(px)
    if n < 4:
        return None
    coef = quadratic_fit(px, py)
    if coef is None:
        return None
    std = math.sqrt(coef[3]) if coef[3] > 0 else 0.0
    good_x = []
    good_y = []
    for x, y in zip(px, py):
        pred = coef[0] + x * coef[1] + x * x * coef[2]
        if abs(pred - y) < std:
            good_x.append(x)
            good_y.append(int(round(pred)))
    if len(good_x) >= 4:
        coef2 = quadratic_fit(good_x, good_y)
        if coef2 is not None:
            coef = coef2
    ytmp = [int(coef[0] + x * coef[1] + x * x * coef[2]) for x in px]
    if coef[2] != 0.0:
        ipt = _nint(-coef[1] / (2.0 * coef[2]))
        if 1 <= ipt <= n:
            k = ytmp[ipt - 1]
            if coef[2] > 0.0:
                for i in range(ipt - 1):
                    ytmp[i] = k
            else:
                for i in range(ipt, n):
                    ytmp[i] = k
    return ytmp
