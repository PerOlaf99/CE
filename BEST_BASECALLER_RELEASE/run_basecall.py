#!/usr/bin/env python3
"""
Unified MegaBACE ET basecaller — one engine, instrument × mode configs.

Examples:
  python run_basecall.py well.rsd --instrument mb1000 --mode accuracy
  python run_basecall.py well.rsd --instrument mb4000 --mode length -o out.fasta
  python run_basecall.py well.rsd --preset mb4000_accuracy
  python run_basecall.py well.rsd --config pos_bonus07   # legacy alias
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
from cimarron_basecaller.spacing_caller import track_bases
from configs import CONFIGS, PRESETS, describe, resolve_config


def call_one(rsd_path: Path, cfg: dict) -> tuple[str, list]:
    rsd = read_rsd(str(rsd_path))
    base_order = cfg.pop("base_order", "TGCA")
    # track_bases does not take base_order from cfg as dye map for rsd — use to_acgt_trace
    trace, order = to_acgt_trace(rsd, base_order=base_order)
    # spectral matrix: string "default" -> leave for track_bases DEFAULT_CHM
    ssm = cfg.get("spectral_separation_matrix")
    if isinstance(ssm, str) and ssm == "default":
        cfg = dict(cfg)
        cfg.pop("spectral_separation_matrix", None)
    seq, quals, bands = track_bases(trace, base_order=order, **cfg)
    return seq, bands


def main() -> None:
    p = argparse.ArgumentParser(description="MegaBACE ET basecaller (instrument × mode)")
    p.add_argument("rsd", type=Path, help="Input .rsd file")
    p.add_argument("-o", "--output", type=Path, default=None, help="Output FASTA (default: stdout)")
    p.add_argument(
        "--instrument",
        choices=("mb1000", "mb4000"),
        default=None,
        help="Instrument profile (spectral matrix + defaults)",
    )
    p.add_argument(
        "--mode",
        choices=("accuracy", "length"),
        default=None,
        help="accuracy = longest error-free; length = longest ID>=95%% read",
    )
    p.add_argument(
        "--preset",
        choices=PRESETS,
        default=None,
        help="Shortcut: mb1000_accuracy | mb1000_length | mb4000_accuracy | mb4000_length",
    )
    p.add_argument(
        "--config",
        default=None,
        help="Legacy config name (pos_bonus07, pos_profile, or a preset name)",
    )
    p.add_argument("--describe", action="store_true", help="Print resolved config and exit")
    p.add_argument("--hp-split", action="store_true",
                   help="Experimental mid-zone A/C supervised peak-split head")
    p.add_argument("--hp-split-threshold", type=float, default=0.90,
                   help="Probability threshold for HP split inserts (default 0.90)")

    args = p.parse_args()

    if args.preset:
        instrument, mode = args.preset.split("_", 1)
    elif args.config:
        if args.config in CONFIGS:
            # resolve via name for describe
            if args.config.startswith("mb"):
                instrument, mode = args.config.split("_", 1)
            elif args.config == "pos_profile":
                instrument, mode = "mb1000", "length"
            else:
                instrument, mode = "mb1000", "accuracy"
            cfg = dict(CONFIGS[args.config])
        else:
            sys.exit(f"Unknown --config {args.config}")
            return
    else:
        instrument = args.instrument or "mb1000"
        mode = args.mode or "accuracy"

    if args.describe:
        print(describe(instrument, mode))
        return

    if not args.preset and not args.config:
        cfg = resolve_config(instrument, mode)
    elif args.preset:
        cfg = resolve_config(instrument, mode)
    else:
        cfg = dict(CONFIGS[args.config])
        # still need base_order
        cfg.setdefault("base_order", "TGCA")

    # re-bind instrument/mode for header after legacy path
    if args.preset:
        pass
    elif args.config and args.config in ("pos_bonus07", "pos_profile"):
        instrument, mode = ("mb1000", "length" if args.config == "pos_profile" else "accuracy")

    if not args.rsd.is_file():
        sys.exit(f"File not found: {args.rsd}")

    print(describe(instrument, mode), file=sys.stderr)
    seq, bands = call_one(args.rsd, dict(cfg))
    if args.hp_split:
        try:
            from cimarron_basecaller.hp_split_head import apply_splits, bands_to_sequence, load_model
            from cimarron_basecaller.spacing_caller import (
                DEFAULT_MOBILITY_SHIFTS, DEFAULT_CHM, apply_spectral_separation,
                detect_signal_region, estimate_global_spacing,
            )
            from cimarron_basecaller.simple_caller import (
                robust_baseline_subtract, apply_mobility_correction, normalize_channels_local,
            )
            from cimarron_basecaller.rsd_io import read_rsd, to_acgt_trace
            model_path = ROOT / "assets" / "hp_split_ac_mid.npz"
            if model_path.is_file():
                model = load_model(model_path)
                rsd = read_rsd(str(args.rsd))
                tr, order = to_acgt_trace(rsd, base_order="TGCA")
                M = cfg.get("spectral_separation_matrix", DEFAULT_CHM)
                if isinstance(M, str):
                    M = DEFAULT_CHM
                x = robust_baseline_subtract(tr, 151)
                x = apply_spectral_separation(np.clip(x, 0, None), M)
                x = apply_mobility_correction(x, tuple(DEFAULT_MOBILITY_SHIFTS))
                x = normalize_channels_local(np.clip(x, 0, None), window=1800)
                sp = estimate_global_spacing(x.max(axis=1), *detect_signal_region(x))
                n0 = len(bands)
                bands = apply_splits(bands, np.clip(x, 0, None), model, float(sp),
                                     threshold=args.hp_split_threshold, max_inserts=2)
                seq = bands_to_sequence(bands, order)
                print(f"HP-split: +{len(bands)-n0} peaks (thr={args.hp_split_threshold})", file=sys.stderr)
            else:
                print("HP-split model missing; skipped", file=sys.stderr)
        except Exception as e:
            print(f"HP-split failed: {e}", file=sys.stderr)
    header = f"{args.rsd.stem}|{instrument}_{mode}|len={len(seq)}"
    fasta = f">{header}\n{seq}\n"
    if args.output:
        args.output.write_text(fasta)
        print(f"Wrote {args.output} ({len(seq)} bp, {len(bands)} peaks)", file=sys.stderr)
    else:
        sys.stdout.write(fasta)


if __name__ == "__main__":
    main()
