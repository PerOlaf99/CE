"""A5: unit tests for Phase A fuzzy engine (fuzzy_engine.py)."""
import math
import random
import sys

sys.path.insert(0, '.')
from fuzzy_engine import CFuzzySet, CFuzzySet as F, C_CENTROID_SCALE

failures = 0

def check(name, cond, got=None):
    global failures
    if not cond:
        failures += 1
        print(f"FAIL {name}  got={got}")
    else:
        print(f"ok   {name}")

# --- triangular membership interp (flat ends, mode 0) ---
tri = F([0, 1, 2, 3], [0, 1, 0, 0], mode=0)
check("tri peak", tri.membership(1.0) == 1.0, tri.membership(1.0))
check("tri left-ramp", abs(tri.membership(0.5) - 0.5) < 1e-12, tri.membership(0.5))
check("tri right-ramp", abs(tri.membership(1.5) - 0.5) < 1e-12, tri.membership(1.5))
check("tri below flat", tri.membership(-0.5) == 0.0, tri.membership(-0.5))
check("tri above flat", tri.membership(9.0) == 0.0, tri.membership(9.0))

# --- half-triangle: left boundary -> y[0] flat -----------------------------
half = F([1.0, 2.0], [1.0, 0.0], mode=0)
check("half below flat=1", half.membership(0.0) == 1.0, half.membership(0.0))
check("half mid", abs(half.membership(1.5) - 0.5) < 1e-12, half.membership(1.5))
check("half above flat=0", half.membership(3.0) == 0.0, half.membership(3.0))

# --- max_val ---
check("max val", tri.max_val() == 1.0, tri.max_val())
const = F([0, 1, 2], [0.4, 0.4, 0.4], mode=0)
check("max const", abs(const.max_val() - 0.4) < 1e-12, const.max_val())

# --- is_empty ----
check("empty", F([0, 1], [0, 1]).is_empty() is False)
# n==0 can't be built via __init__ (assert), emulate via scaled-to-zero? skip

# --- union (max) vs intersection (min) ---
a = F([0, 1, 2], [0, 1, 0], mode=0)
b = F([0.5, 1.5, 2.5], [0, 1, 0], mode=0)
u = a.union(b, use_min=False)
i = a.union(b, use_min=True)
check("union at 1.0 == 1", abs(u.membership(1.0) - 1.0) < 1e-9, u.membership(1.0))
# b at x=2.0 = interp(1.5->1, 2.5->0) = 0.5 ; a at 2.0 = 0 ; max=0.5
check("union at 2.0 == 0.5", abs(u.membership(2.0) - 0.5) < 1e-9, u.membership(2.0))
# intersection of two unit triangles that only overlap where both raised
check("inter at 1.0 (a=1,b small) >0", i.membership(1.0) > 0.0, i.membership(1.0))
check("inter at 3.0 == 0", abs(i.membership(3.0) - 0.0) < 1e-9, i.membership(3.0))
check("union at 3.0 == 0", abs(u.membership(3.0) - 0.0) < 1e-9, u.membership(3.0))

# --- centroid: port faithfully; symmetric triangle => exact 1.0 with K=2.0 ----
# Resolved from asm: _DAT_10038928=2.0 (K), _DAT_10038930=3.0 (divisor). For the
# symmetric triangle [0,1,2]->[0,1,0] this yields exactly 1.0 (true COM) --
# which validates the numerator/denominator + constants end to end.
ctr = F([0, 1, 2], [0, 1, 0], mode=0)
c = ctr.centroid()
check("centroid has value", c is not None, c)
check("centroid finite positive", c is not None and math.isfinite(c) and c > 0, c)
check("centroid K=2 -> 1.0", c is not None and abs(c - 1.0) < 1e-9, c)

# --- modes: square / sqrt transforms ---
m1 = F([2, 4], [1, 0], mode=1)   # out = sqrt(y); y ramps 1->0
check("mode1 out sqrt(1)=1", abs(m1.membership(2.0) - 1.0) < 1e-9, m1.membership(2.0))
# membership at x=3 is 0.5 -> out = sqrt(0.5) = 0.7071
check("mode1 out sqrt(0.5)=0.7071", abs(m1.membership(3.0) - math.sqrt(0.5)) < 1e-6, m1.membership(3.0))
m2 = F([2, 4], [1, 0], mode=2)   # out = y^2
check("mode2 out sq(0.5)=0.25", abs(m2.membership(3.0) - 0.25) < 1e-6, m2.membership(3.0))
m0 = F([2, 4], [1, 0], mode=0)
check("mode0 out id(0.5)=0.5", abs(m0.membership(3.0) - 0.5) < 1e-9, m0.membership(3.0))

# --- complement (1-y) ---
cmp = F([0, 1], [1, 0], mode=0)
cmp.complement()
check("complement max -> 0", abs(cmp.membership(0.0)) < 1e-9, cmp.membership(0.0))
check("complement min -> 1", abs(cmp.membership(1.0) - 1.0) < 1e-9, cmp.membership(1.0))

# --- random interp consistency (monotonic x, membership in [lo,hi]) --------
random.seed(7)
ok = True
for _ in range(500):
    n = random.randint(2, 8)
    xs = sorted(random.uniform(-2, 2) for _ in range(n))
    ys = [random.uniform(0, 1) for _ in range(n)]
    f = CFuzzySet(xs, ys)
    for _ in range(20):
        v = random.uniform(-3, 3)
        m = f.membership(v)
        if not (-1e-6 <= m <= 1.000001):
            ok = False
            break
    if not ok:
        break
check("random interp bounded", ok)

print()
print("FAILURES:", failures)
sys.exit(1 if failures else 0)
