"""Score the de-novo plate against the canonical metric and the Cimarron 3.12 bar.

    python eval_plate.py

Writes report.json with per-well identity and plate aggregates, and prints the
comparison to Cimarron 3.12 DLL (ESD) and the repo's V10 chain.
"""
import glob
import json
import os
import statistics

import canon_metric as cm
from call_plate import basecall_well, WIN_CONFIG

_HERE = os.path.dirname(os.path.abspath(__file__))
RSD_DIR = os.path.join(_HERE, "..", "MB1000_M13_DT")
ESD_DIR = os.path.join(_HERE, "..", "ground_truth", "MB1000_M13_DT_Cp312_MD1")
ref = cm.get_ref()


def _esd_seq(path):
    raw = open(path, "rb").read()
    idx = -1
    while True:
        idx = raw.find(b"SEQUENCE", idx + 1)
        if idx < 0:
            return None
        np_ = idx + 8
        if np_ + 3 >= len(raw) or raw[np_] != 0:
            continue
        tb, lo, hi = raw[np_ + 1], raw[np_ + 2], raw[np_ + 3]
        if tb == 0x06 and 100 < (lo + (hi << 8)) < 5000:
            length, ds = lo + (hi << 8), np_ + 4
        elif tb == 0x05 and 100 < lo < 1000:
            length, ds = lo, np_ + 3
        else:
            continue
        return "".join(c for c in raw[ds:ds + length].decode("ascii", "replace")
                       if c in "ACGTNacgtn").upper()


def main():
    wells = sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(RSD_DIR, "*.rsd")))
    per_well = {}
    ids = []
    for w in wells:
        seq, quals = basecall_well(os.path.join(RSD_DIR, w + ".rsd"))
        r = cm.score(seq, ref)
        ident = r[0] if r else None
        per_well[w] = {"len": len(seq), "identity": ident}
        if ident is not None:
            ids.append(ident)
    esd_ids = []
    for w in wells:
        p = os.path.join(ESD_DIR, w + ".esd")
        if not os.path.exists(p):
            continue
        s = _esd_seq(p)
        if s:
            v = cm.perbase_vs_ref(s, ref)
            if v is not None:
                esd_ids.append(v)
    result = {
        "pipeline": "gaussian_bandfilter + combined channel tracking (track_bases)",
        "config": {k: (list(v) if isinstance(v, tuple) else v) for k, v in WIN_CONFIG.items()},
        "n_wells": len(ids),
        "mean_identity": statistics.mean(ids),
        "median_identity": statistics.median(ids),
        "min_identity": min(ids),
        "max_identity": max(ids),
        "cimarron312_dll_esd_mean": statistics.mean(esd_ids) if esd_ids else None,
        "delta_vs_cimarron": statistics.mean(ids) - statistics.mean(esd_ids) if esd_ids else None,
        "per_well": per_well,
    }
    with open(os.path.join(_HERE, "report.json"), "w") as fh:
        json.dump(result, fh, indent=2)
    print(json.dumps({k: result[k] for k in result if k != "per_well"}, indent=2))


if __name__ == "__main__":
    main()
