#!/usr/bin/env python3
"""Phase C trim runner: reproduce the DLL's FUN_10019ef2 keep/drop stage.

Pipeline (all from decomp of csibq030012.dll):
  1. candidates P[]        = FUN_100250d0 region (bgn/end) applied elsewhere;
     here passed in (or from dll_peakdet raw).
  2. Y[] = fitted spacing  = FUN_10019280 (robust quadratic spacing-vs-position):
        z-outlier reject |z|>1.5 -> iquadratic fit -> residual-std re-reject
        -> refit -> per-band eval -> edge stabilization -> min-clamp >=1.
  3. D[] = SWold           = actual inter-candidate spacing P[i+1]-P[i].
  4. E[] = FUN_1001bcd0    = spacing array shifted (neighbour spacing).
  5. sb[] = envv(P[i])     = envelope at the candidate scan.
  6. envAll[i] = min(envv(left flank), envv(right flank)).
  7. s2[] = xbnd           = per-scan Wvfm::xbnd (approximated here).
  8. classify_fuzzy (FUN_10012140) -> out[i].val,out[i].qual.
  9. keep/weak/drop: q=trunc(val); 1->keep, 2->weak(emit, mark if xbnd<=1.176471),
     else drop.
Validated against the DLL-ESD: candidate=956 (bases_positions), final=841
(peak_positions) on A01.
"""
import os, sys, math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import classify_fuzzy as cf

ROOT = "/media/tv/78B0C7DE1FA7081C1/electropherogram"
GTD = os.path.join(ROOT, "ground_truth/MB1000_M13_DT_Cp312_MD1")
SEP = os.path.join(ROOT, "cache_sep")

# -- gates (.rdata) -----------------------------------------------------
Z_OR = 1.5                # _DAT_10038aa0  spacing z-outlier
XB_GATE = 1.176471        # _DAT_10038a80  xbnd weak gate (20/17)
ENV_FLOOR = 0.05          # _DAT_10038a88  env floor clamp
WIDTH_DIV = 2.0           # _DAT_10038d60


def iquadratic(x, y):
    """Port of iquadratic (0x351a8): least-squares quadratic y=a x^2+b x+c.
    Returns (c,b,a,resid_var) or None if n<4 / zero residual."""
    n = len(x)
    if n < 4:
        return None
    X, Y = np.asarray(x, np.float64), np.asarray(y, np.float64)
    ybar = Y.mean()
    local_10 = ((Y - ybar) ** 2).sum() / (n - 1.0)
    if local_10 == 0.0:
        return None
    m0 = n / local_10
    m1 = X.sum() / local_10
    m2 = (X * X).sum() / local_10
    m3 = (X * X * X).sum() / local_10
    m4 = (X * X * X * X).sum() / local_10
    v0 = Y.sum() / local_10
    v1 = (X * Y).sum() / local_10
    v2 = (X * X * Y).sum() / local_10
    A = np.array([[m0, m1, m2],
                  [m1, m2, m3],
                  [m2, m3, m4]], np.float64)
    bvec = np.array([v0, v1, v2], np.float64)
    try:
        sol = np.linalg.solve(A, bvec)
    except np.linalg.LinAlgError:
        return None
    c, b, a = float(sol[0]), float(sol[1]), float(sol[2])
    fit = a * X * X + b * X + c
    resid = float(((fit - Y) ** 2).sum() / (n - 3.0))
    return c, b, a, resid


def fitted_spacing(positions, spacings):
    """Port of FUN_10019280. positions/spacings: equal-length lists.
    Returns int[] fitted spacing per band or None on failure."""
    N = len(positions)
    if N < 4:
        return None
    p = np.asarray(positions, np.float64)
    s = np.asarray(spacings, np.float64)
    mean = s.mean()
    var = (s * s).mean() - mean * mean
    std = math.sqrt(max(var, 0.0))
    if std == 0.0:
        return None
    # pass 1: z-reject
    z = np.abs(s - mean) / std
    keep = np.where(z <= Z_OR)[0]
    if len(keep) < 4:
        # fall back to no rejection (keeps the fit alive like the DLL's ivector)
        keep = np.arange(N)
    q = iquadratic(p[keep], s[keep])
    if q is None:
        return None
    c, b, a, resid_var = q
    resid_std = math.sqrt(max(resid_var, 0.0))

    def at(xx):
        return int(math.trunc(a * xx * xx + b * xx + c))

    # pass 2: residual-std re-reject, then refit if enough survivors
    surv = [(float(p[i]), float(at(p[i]))) for i in range(N)
            if abs(at(p[i]) - s[i]) < resid_std]
    if len(surv) > 3:
        q2 = iquadratic([x for x, y in surv], [y for x, y in surv])
        if q2 is not None:
            c, b, a, resid_var = q2
            del at
            def at(xx):
                return int(math.trunc(a * xx * xx + b * xx + c))

    out = [at(float(pp)) for pp in p]
    # edge stabilization (13336-13352)
    if a != 0.0:
        v1 = at(float(p[0]))
        if p[0] <= v1 <= p[-1]:
            l74 = 0
            while l74 < N and p[l74] < v1:
                l74 += 1
            if l74 < N:
                base = out[l74]
                if a <= 0.0:
                    for i in range(l74 + 1, N):
                        out[i] = base
                else:
                    for i in range(0, l74):
                        out[i] = base
    # min-clamp >= 1
    local = 10 ** 7
    any_neg = False
    for v in out:
        if v < 1:
            any_neg = True
        elif v < local:
            local = v
    if any_neg:
        if local < 1:
            local = 1
        out = [local if v < local else v for v in out]
    return out


def envi_base(lanes, pos):
    """FUN_10025431: first/only channel >= envv*0.8 (k). ch>=2 -> 5.
    Returns per-scan channel code (0 none, 1-4, 5 ambig)."""
    env = lanes.max(axis=1)
    codes = np.zeros(len(lanes), dtype=np.int8)
    for c in range(4):
        above = lanes[:, c] >= 0.8 * env
        codes[above] = np.where(codes[above] == 0, c + 1, 5)
    return codes


def xbnd_array(lanes):
    """Wvfm::envelope port (0x31976): per-scan xbnd = cross-channel ratio
    max/3rd, branch max/sqrt(3rd)+1 below 0.1, clamped to [1,2].
    (buzz = (3rd-1st)/(max-3rd) at this scan is not consumed by the classifier.)
    """
    n = len(lanes)
    xb = np.empty(n)
    for i in range(n):
        v = np.sort(lanes[i])
        lo = float(v[0])          # local_44 (1st/store #1)
        xm = float(v[2])          # local_54 = 3rd highest
        mx = float(v[3])          # dVar7 = max
        lo = 0.0 if lo < 0.0 else lo
        xm = 0.0 if xm < 0.0 else xm
        if xm < 2.220446049250313e-16:
            xm = 2.220446049250313e-16
        if mx >= 0.1:             # _DAT_10038eb0 (double 0.1)
            val = mx / xm
        else:
            val = mx / math.sqrt(xm) + 1.0   # +_DAT_10038e58 (1.0f)
        if val > 2.0:             # _DAT_10038e54
            val = 2.0
        elif val < 1.0:           # _DAT_10038e58
            val = 1.0
        xb[i] = val
    return xb


def build_features(lanes, P, env, DYE_NONE=None):
    """Y (fitted spacing), D (SWold), E (SWold shifted +1), sb, envAll,
    s2 (per-scan xbnd sampled at band positions)."""
    P = np.asarray(P, np.int64)
    N = len(P)
    D = np.zeros(N)
    for i in range(N - 1):
        D[i] = P[i + 1] - P[i]
    if N > 1:
        D[N - 1] = D[N - 2]
    Y = fitted_spacing(P, D)
    if Y is None:
        Y = [int(round(float(np.median(D))))] * N
    E = np.empty(N)
    for i in range(N - 1):
        E[i] = D[i + 1]
    if N > 1:
        E[N - 1] = D[N - 1]
    sb = env[P]
    # envAll = min(envv(left-neighbour band), envv(right-neighbour band))
    eA = np.empty(N)
    left = np.clip(P - D, 0, len(env) - 1).astype(int)
    right = np.clip(np.concatenate((P[1:], P[-1:])), 0, len(env) - 1).astype(int)
    eA = np.minimum(env[left], env[right])
    xb = xbnd_array(lanes)[P]
    return Y, D, E, sb, eA, xb


def classify_trim(lanes, P):
    """Returns (kept_indices, weak_flag_per_kept, out_vals)."""
    env = lanes.max(axis=1)
    Y, D, E, sb, eA, xb = build_features(lanes, P, env)
    N = len(P)
    out = cf.classify(Y, sb, eA, D, E, xb, N)
    kept = []
    weak = []
    for i in range(N):
        val = math.trunc(out[i][0])
        if val == 1:
            kept.append(i); weak.append(False)
        elif val == 2:
            kept.append(i); weak.append(xb[i] <= XB_GATE)
    return np.array(kept, dtype=int), np.array(weak, dtype=bool), out


def dump(feature_vals, N, out):
    pass


def main():
    try:
        import extract_training_data as etd
    except ImportError:
        sys.path.insert(0, ROOT)
        import extract_training_data as etd
    well = sys.argv[1] if len(sys.argv) > 1 else "A01"
    lanes = np.load(os.path.join(SEP, well + ".npy"))
    d = etd.parse_esd(os.path.join(GTD, well + ".esd"))
    rec = np.asarray(d["bases_positions"], np.int64)   # pass-1 candidate positions
    final = np.asarray(d["peak_positions"], np.int64)  # pass-2 final (repositioned)
    tol = 6                                            # DLL re-positions peaks in pass 2
    kept_mask = np.array([int(np.min(np.abs(final - int(p)))) <= tol for p in rec])

    P = rec
    env = lanes.max(axis=1)
    Y, D, E, sb, eA, xb = build_features(lanes, P, env)
    N = len(P)
    print(f"{well}: candidates={N}  DLL-final={len(final)} "
          f"({int(kept_mask.sum())} kept / {N - int(kept_mask.sum())} dropped)")

    out = cf.classify(Y, sb, eA, D, E, xb, N)
    vals = np.array([math.trunc(o[0]) for o in out])
    print(f"classify: val-hist(trunc)=", {v: int((vals == v).sum()) for v in range(-1, 6)})

    pred_keep = vals == 1
    pred_weak = vals == 2
    pred_keep = pred_keep | pred_weak
    gt = kept_mask
    tp = int((pred_keep & gt).sum()); fp = int((pred_keep & ~gt).sum())
    tn = int((~pred_keep & ~gt).sum()); fn = int((~pred_keep & gt).sum())
    print(f"keep/drop vs ground truth: TP={tp} FP={fp} TN={tn} FN={fn}")
    print(f"  precision={100*tp/max(tp+fp,1):.1f}%  recall(kept)={100*tp/max(tp+fn,1):.1f}%")
    print(f"  our kept set recall vs DLL positions (tol={tol}): "
          f"{100*np.mean(np.min(np.abs(final[None, :] - P[pred_keep, None]), axis=1) <= tol):.1f}%"
          f" ({(np.min(np.abs(final[None, :] - P[pred_keep, None]), axis=1) <= tol).sum()}/{int(pred_keep.sum())})")

    # and the position-metric on the raw predicted kept set
    det = set(P[pred_keep].tolist())
    hit = sum(1 for g in final if any(abs(int(g) - x) <= 3 for x in det))
    print(f"  our kept({len(det)}) recall vs DLL-final(841) tol3={100*hit/len(final):.1f}% "
          f"({hit}/{len(final)})")


if __name__ == "__main__":
    main()