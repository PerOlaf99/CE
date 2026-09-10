"""
Phase A port: Cimarron 3.12 fuzzy-logic engine (PATH 2).

Faithful port of the CFuzzySet primitives decompiled from csibq030012.dll:
  FUN_10012ad0  constructor (x[]/y[] as SEPARATE contiguous double arrays)
  FUN_10012c6c  membership  = piecewise-linear interp (flat ends), out through transform[0xc]
  FUN_10012dbd  max_val     = max(y[]), out through transform[0xc]
  FUN_10012e31  is_empty    = n == 0
  FUN_10012ec6  complement  = 1 - y
  FUN_10012f4d  union       = merged-sorted-x set, pointwise max (param_3==0) or min
  FUN_10013818  centroid    = defuzzifier I0/(3*I1), guard |I1| > 6.1e-21

Mode transforms (constructor [0xc]/[0xd], applied to membership OUT and to inputs):
  mode 0: identity / identity
  mode 1: sqrt / square
  mode 2: square / sqrt
  mode 3: piecewise(sqrt,square) / piecewise(square,sqrt)  @ threshold 0.5

Offsets in the 0x38-byte object: [0..7] vtable, [8]=n(0x20), [9]=x(0x24),
[10]=y(0x28), [0xb]=mode, [0xc]=transform_out(0x30), [0xd]=transform_in(0x34).

UNCONFIRMED / FLAGGED (to pin in Phase B, do NOT ship):
  __CENTROID_K : decomp shows _DAT_10038928 (0x4415AF1D78B58C40 ~ 5.7e20) used as a
                 numerator weight. This is almost certainly an x87 long-double
                 decompiler artifact; the true centroid divisor is 3.0 and K is
                 EXPECTED to be 3.0. Kept as a parameter; verify against asm and
                 DLL output before trusting.
"""

import math
import struct


# ---- constants decoded from .rdata -----------------------------------------
C_ONE          = 1.0          # _DAT_10038900
C_THRESH_0_5   = 0.5          # _DAT_10038938 (mode-3 piecewise threshold)
C_CENTROID_K     = 2.0        # _DAT_10038928 (numerator weight, from asm fldl 0x10038928)
C_CENTROID_SCALE = 3.0        # _DAT_10038930 (denominator divisor)
C_CENTROID_EPS   = 6.1e-21    # _DAT_10038910 (guard on |I1|)


class CFuzzySet:
    """A piecewise-linear fuzzy set with a mode (input/output transform)."""

    def __init__(self, x, y, mode=0, _centroid_k=None):
        # x and y are SEPARATE arrays (offsets 0x24 / 0x28), each n doubles.
        assert len(x) == len(y) > 0, "CFuzzySet requires >=1 point"
        self.n = len(x)
        self.x = list(x)
        self.y = list(y)
        self.mode = mode
        self._centroid_k = C_CENTROID_K if _centroid_k is None else _centroid_k

    # ---- mode transforms (port of FUN_10013991/999/a4/b9/f4) --------------
    @staticmethod
    def _t_out(kind, v):
        if kind == 'sq':
            return v * v
        if kind == 'sqrt':
            return math.sqrt(v)
        if kind == 'sqrt_sq':
            return math.sqrt(v) if v < C_THRESH_0_5 else v * v
        if kind == 'sq_sqrt':
            return v * v if v < C_THRESH_0_5 else math.sqrt(v)
        return v  # identity

    @staticmethod
    def _transform_kind(mode, which):
        pair = {
            0: ('id', 'id'),
            1: ('sqrt', 'sq'),
            2: ('sq', 'sqrt'),
            3: ('sqrt_sq', 'sq_sqrt'),
        }[mode]
        return pair[0] if which == 'out' else pair[1]

    def _out(self, v):
        return self._t_out(self._transform_kind(self.mode, 'out'), v)

    # ---- membership (FUN_10012c6c): interp y over sorted x, flat ends ----
    def membership(self, val):
        if self.n == 0:
            return 0.0
        x, y = self.x, self.y
        if val < x[0]:
            m = y[0]
        elif val >= x[-1]:
            m = y[-1]
        else:
            # binary search for right index
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

    # ---- max_val (FUN_10012dbd) -------------------------------------------
    def max_val(self):
        m = max(self.y)
        return self._out(m)

    # ---- is_empty (FUN_10012e31) ------------------------------------------
    def is_empty(self):
        return self.n == 0

    # ---- complement / fuzzy NOT (FUN_10012ec6): y -> 1 - y ----------------
    def complement(self):
        self.y = [C_ONE - v for v in self.y]

    # ---- scale (FUN_10012f0b): y -> y*param_2 -----------------------------
    def scale(self, k):
        self.y = [v * k for v in self.y]

    # ---- centroid / defuzzifier (FUN_10013818) ------------------------------
    def centroid(self):
        """I0/I1 weighted-mass centroid; guard on |I1|; scale 3.0."""
        if self.n < 2:
            return None
        K = self._centroid_k
        I0 = 0.0
        I1 = 0.0
        for i in range(1, self.n):
            dx = self.x[i] - self.x[i - 1]
            f1 = self._out(self.y[i])
            f0 = self._out(self.y[i - 1])
            # I0 numerator mirrors decomp: (K*x_i + x_{i-1})*f1 + (K*x_{i-1}+x_i)*f0
            I0 += dx * ((K * self.x[i] + self.x[i - 1]) * f1 +
                        (K * self.x[i - 1] + self.x[i]) * f0)
            I1 += (f1 + f0) * dx
        if abs(I1) > C_CENTROID_EPS:
            return I0 / (C_CENTROID_SCALE * I1)
        return None

    # ---- union / merge (FUN_10012f4d): merged-sorted-x, max|min merge ----
    def union(self, other, use_min=False):
        """Returns a new CFuzzySet = fuzzy merge of self and other.
        param_3==0 -> max (union/OR); param_3!=0 -> min (intersection/AND)."""
        if self.is_empty():
            return other
        if other.is_empty():
            return self
        n = self.n + other.n
        xs = sorted(set(self.x) | set(other.x))
        ys = []
        for xv in xs:
            sv = self.membership_raw(xv)
            ov = other.membership_raw(xv)
            ys.append(min(sv, ov) if use_min else max(sv, ov))
        return CFuzzySet(xs, ys, mode=self.mode)

    def membership_raw(self, val):
        """interp WITHOUT the output transform (used internally by union)."""
        if self.n == 0:
            return 0.0
        x, y = self.x, self.y
        if val < x[0]:
            return y[0]
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
