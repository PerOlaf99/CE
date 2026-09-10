"""
Faithful port of Cimarron 3.12 base-calling fuzzy classifier FUN_10012140
(+ the CFuzzySet engine FUN_10012ad0/c6c/dbd/f4d/13818) -- PATH 2, B3.

Decoded from csibq030012.dll assembly (fun_10012140.asm) + .rdata tables.

FUNCTION ARGS (thiscall, asm ebp offsets, count N = 0x20):
  0x08 int[]  Y[i]    per-band integer feature
  0x0c float[] sb[i]  signal fed to the dynamic floor ramps
  0x10 float[] envAll mean-env source over the well (for the floor)
  0x14 int[]  D[i]    flank feature -> ratio r1
  0x18 int[]  E[i]    flank feature -> ratio r2
  0x1c float[] s2[i]  signal fed to descending(desc) / rising(rise) sets
  0x20 int    N
  0x24 out rec[i]     {val,qual} (float at +4,+8)

RETURNS (eax): 0 on abort (bad alloc / sentinel), 1 on success (per well).

The engine + rule is fully transcribed below; see DLL_FUNCTION_MAP.md §B3-DETAIL.
"""

import math


# --------------------------------------------------------------------------
# CFuzzySet engine (port of FUN_10012ad0 + primitives)
# --------------------------------------------------------------------------
C_THRESH_0_5 = 0.5      # _DAT_10038938
C_ONE        = 1.0      # _DAT_10038900
K_CENTROID   = 2.0      # _DAT_10038928
SCALE_CENTROID = 3.0    # _DAT_10038930
EPS_CENTROID = 6.1e-21  # _DAT_10038910


def _t(kind, v):
    if kind == 'sq':
        return v * v
    if kind == 'sqrt':
        return math.sqrt(v)
    if kind == 'sqrt_sq':
        return math.sqrt(v) if v < C_THRESH_0_5 else v * v
    if kind == 'sq_sqrt':
        return v * v if v < C_THRESH_0_5 else math.sqrt(v)
    return v


class FSet:
    """x[], y[] SEPARATE arrays (CFuzzySet obj: x@0x24, y@0x28)."""

    _PAIR = {
        0: ('id', 'id'),
        1: ('sqrt', 'sq'),
        2: ('sq', 'sqrt'),
        3: ('sqrt_sq', 'sq_sqrt'),
    }

    def __init__(self, x, y, mode=0):
        self.x = list(x)
        self.y = list(y)
        self.n = len(x)
        self.mode = mode
        self._out_kind, _ = self._PAIR[mode]

    def _out(self, v):
        return _t(self._out_kind, v)

    def membership(self, val):
        if self.n == 0:
            return 0.0
        x, y = self.x, self.y
        if val < x[0]:
            m = y[0]
        elif val >= x[-1]:
            m = y[-1]
        else:
            lo, hi = 0, self.n - 1
            while lo < hi:
                mid = (lo + hi) // 2
                if x[mid] < val:
                    lo = mid + 1
                else:
                    hi = mid
            i = lo
            if x[i] == val or i == 0:
                m = y[i]
            else:
                t = (val - x[i - 1]) / (x[i] - x[i - 1])
                m = y[i - 1] + (y[i] - y[i - 1]) * t
        return self._out(m)

    def scaled(self, k):
        return FSet(self.x, [v * k for v in self.y], self.mode)

    def union(self, other):
        xs = sorted(set(self.x) | set(other.x))
        ys = [max(self._interp_raw(z), other._interp_raw(z)) for z in xs]
        return FSet(xs, ys, self.mode)

    def _interp_raw(self, val):
        x, y = self.x, self.y
        if self.n == 0 or val < x[0]:
            return 0.0 if self.n == 0 else y[0]
        if val >= x[-1]:
            return y[-1]
        lo, hi = 0, self.n - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if x[mid] < val:
                lo = mid + 1
            else:
                hi = mid
        i = lo
        if x[i] == val or i == 0:
            return y[i]
        t = (val - x[i - 1]) / (x[i] - x[i - 1])
        return y[i - 1] + (y[i] - y[i - 1]) * t

    def max_val(self):
        return self._out(max(self.y))

    def centroid(self):
        if self.n < 2:
            return None
        I0 = 0.0
        I1 = 0.0
        for i in range(1, self.n):
            dx = self.x[i] - self.x[i - 1]
            f1 = self._out(self.y[i])
            f0 = self._out(self.y[i - 1])
            I0 += dx * ((K_CENTROID * self.x[i] + self.x[i - 1]) * f1 +
                        (K_CENTROID * self.x[i - 1] + self.x[i]) * f0)
            I1 += (f1 + f0) * dx
        if abs(I1) > EPS_CENTROID:
            return I0 / (SCALE_CENTROID * I1)
        return None


# --------------------------------------------------------------------------
# Static outer / inner sets (decoded from .rdata @0x10038750..0x100388c0)
# --------------------------------------------------------------------------
def _static_sets(floor, T):
    # outer
    sV = FSet([0.2, 0.5, 0.8], [1.0, 0.0, 1.0], mode=0)          # -0x30 local_34
    sT = FSet([0.2, 0.4, 0.6, 0.8], [0.0, 1.0, 1.0, 0.0], mode=2)  # -0x2c local_30
    sDesc = FSet([1.0, 1.4, 1.8], [1.0, 0.5, 0.0], mode=0)        # -0x34 local_38
    sRise = FSet([1.2, 1.4], [0.0, 1.0], mode=0)                  # -0x4c local_50
    # dynamic floor ramps
    sRampA = FSet([floor, T], [0.0, 1.0], mode=0)                 # -0x38 local_3c
    sRampB = FSet([floor, T], [0.0, 1.0], mode=1)                 # -0x60 puVar1
    # inner windows (mode 0), scaled per band then max-union
    zero = FSet([0.4596, 3.554], [0.0, 0.0], mode=0)              # -0x6c puVar2
    sLow = FSet([0.4596, 1.3797, 1.6864], [1.0, 1.0, 0.0], mode=0)  # -0xf0 puVar3
    sMid = FSet([1.3797, 1.6864, 2.2998, 2.6065], [0.0, 1.0, 1.0, 0.0], mode=0)  # -0xd4 puVar4
    sHigh = FSet([2.2998, 2.6065, 3.554], [0.0, 1.0, 1.0], mode=0)  # -0xb0 puVar5
    return sV, sT, sDesc, sRise, sRampA, sRampB, zero, sLow, sMid, sHigh


# --------------------------------------------------------------------------
# FUN_10012140  (over a set of bands; returns 0 if any abort, else 1)
# --------------------------------------------------------------------------
def classify(Y_int, sb, envAll, D_int, E_int, s2, N):
    # per-well floor (+1.24 factor)
    if N <= 0:
        return 1
    s = 0.0
    for i in range(N):
        s += float(envAll[i])
    floor = s / N
    if floor > 0.05:                       # _DAT_100388d0 clamp (min(mean,0.05))
        floor = 0.05
    T = 0.93 * floor * 1.3333333333333333  # local_10 ~1.24*floor

    (sV, sT, sDesc, sRise, sRampA, sRampB,
     _zero, sLow, sMid, sHigh) = _static_sets(floor, T)

    out = [None] * N
    for i in range(N):
        Y = float(Y_int[i])

        # modulo ratios r1,r2 (decomp guard: if Y/2<=v<=Y then fmod(v,Y);
        # FUN_10012c6c feeds v mod Y to the V/trapezoid sets). Normal D~=Y
        # -> ratio ~0 -> V==1 (LOW fires); half-gap D~=Y/2 -> 0.5 -> V=0.
        def ratio(Vint):
            v = float(Vint)
            Yf = Y if Y != 0 else 1.0
            if 0.0 < Yf:
                mv = math.fmod(v, Yf)
            else:
                mv = 0.0
            return mv / Yf

        r1 = ratio(D_int[i])
        r2 = ratio(E_int[i])

        # outer set memberships (max over the two ratios)
        m_V = max(sV.membership(r1), sV.membership(r2))
        m_T = max(sT.membership(r1), sT.membership(r2))

        # float-array fuzzy evals
        dVal = sDesc.membership(s2[i])     # descending set
        rVal = sRise.membership(s2[i])     # rising set
        ramp = sRampA.membership(sb[i])    # dynamic ramp A
        pv = sRampB.membership(sb[i])      # dynamic ramp B (mode1 sqrt)

        # rule weights (Mamdani min-aggregation)
        wLow = min(rVal, pv, m_V)          # scale for LOW set
        wMid = min(dVal, pv)               # scale for MID set
        wHigh = ramp                       # scale for HIGH set

        # fuzzy inference: scale inner windows, max-union into zero set
        combined = (_zero
                    .union(sLow.scaled(wLow))
                    .union(sMid.scaled(wMid))
                    .union(sHigh.scaled(wHigh)))

        cval = combined.centroid()
        cval = 0.0 if cval is None else cval
        cqual = combined.max_val()

        if cval == 0.0 and cqual == 0.0:
            cval, cqual = 1.0, 0.5         # sentinel

        out[i] = (float(cval), float(cqual))
    return out
