"""Command line interface for the MegaBACE RSD basecaller."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from . import __version__
from .basecall import BaseCaller
from .rsd import RSDError, RsdFile, extract_traces
from .simulate import random_sequence, simulate_traces, write_rsd


def _read_matrix(path: str) -> np.ndarray:
    p = Path(path)
    if p.suffix.lower() in (".npy", ".npz"):
        m = np.load(p)
        if isinstance(m, np.lib.npyio.NpzFile):
            arr = None
            for key in m.files:
                arr = m[key]
                break
            m = arr
    else:
        m = np.loadtxt(p)
    m = np.asarray(m, dtype=np.float64)
    if m.ndim != 2 or m.shape[0] != m.shape[1]:
        raise SystemExit(f"matrix {path} must be square")
    return m


def cmd_inspect(args) -> int:
    try:
        rsd = RsdFile(args.file)
    except RSDError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(rsd.summary())
    if args.hex:
        print()
        print("first 256 bytes (hex):")
        data = rsd.data[:256]
        for i in range(0, len(data), 16):
            chunk = data[i:i + 16]
            hx = " ".join(f"{b:02x}" for b in chunk)
            asc = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            print(f"{i:06x}  {hx:<47}  {asc}")
    return 0


def cmd_basecall(args) -> int:
    try:
        rsd = RsdFile(args.file)
    except RSDError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    matrix = _read_matrix(args.matrix) if args.matrix else None
    channel_order = args.channel_order
    if args.channel_order == "AUTO" or args.channel_order is None:
        channel_order = rsd.metadata.channel_order
    caller = BaseCaller(
        channel_order=channel_order,
        matrix=matrix,
        estimate_matrix=not args.fixed_matrix,
        quality_scale=args.quality_scale,
        trim=not args.no_trim,
    )

    lanes = args.lane or [1]

    out = sys.stdout if not args.output else open(args.output, "w", encoding="utf-8")
    try:
        for lane in lanes:
            try:
                traces = extract_traces(rsd)
            except RSDError as exc:
                print(
                    f"lane {lane}: extraction failed: {exc}", file=sys.stderr
                )
                continue
            if traces.shape[1] < 32:
                print(
                    f"lane {lane}: too few data points ({traces.shape[1]}), skipping",
                    file=sys.stderr,
                )
                continue
            call = caller.call(traces)
            name = f"{Path(args.file).stem}_lane{lane}"
            if args.fastq:
                out.write(call.fastq_record(name) + "\n")
            else:
                out.write(f">{name}\n")
                for i in range(0, len(call.bases), 60):
                    out.write(call.bases[i:i + 60] + "\n")
    finally:
        if out is not sys.stdout:
            out.close()
    return 0


def cmd_simulate(args) -> int:
    seq = random_sequence(args.length, seed=args.seed)
    traces, pos = simulate_traces(
        seq,
        spacing_start=args.spacing_start,
        spacing_end=args.spacing_end,
        noise_sigma=args.noise,
        seed=args.seed,
    )
    write_rsd(args.output, traces, sequence=seq, lane=1)
    truth = Path(args.output).with_suffix(".seq")
    truth.write_text(f">{Path(args.output).stem}\n{seq}\n", encoding="utf-8")
    print(f"wrote {args.output} ({traces.shape[1]} points, {len(seq)} bases)")
    print(f"true sequence: {truth}")
    return 0


def cmd_compare(args) -> int:
    true = _first_seq(args.reference)
    calls = _first_seq(args.calls)
    n = min(len(true), len(calls))
    if n == 0:
        print("no overlap")
        return 1
    match = sum(a == b for a, b in zip(true[:n], calls[:n]))
    acc = match / n * 100.0
    print(
        f"compared {n} bases: {match} exact matches, accuracy={acc:.2f}%"
    )
    return 0


def _first_seq(path: str) -> str:
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    out = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith(">"):
            continue
        if line.startswith("+"):
            break
        out.append(line)
    return "".join(out).upper()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="rsdbasecall",
        description="Basecall MegaBACE 1000 RSD files (v" + __version__ + ")",
    )
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("inspect", help="dump RSD record structure")
    sp.add_argument("file")
    sp.add_argument("--hex", action="store_true", help="also dump first bytes")
    sp.set_defaults(func=cmd_inspect)

    sp = sub.add_parser("basecall", help="basecall an RSD file")
    sp.add_argument("file")
    sp.add_argument("-o", "--output", help="output file (default stdout)")
    sp.add_argument("--fastq", action="store_true", help="emit FASTQ instead of FASTA")
    sp.add_argument("--matrix", help="mixing matrix (npy or text file)")
    sp.add_argument("--fixed-matrix", action="store_true",
                    help="do not estimate the matrix automatically")
    sp.add_argument("--channel-order", default="AUTO",
                    help="channel to base mapping (AUTO reads it from the file, "
                         "default AUTO)")
    sp.add_argument("--quality-scale", type=float, default=1.5)
    sp.add_argument("--no-trim", action="store_true")
    sp.add_argument("--lane", type=int, action="append", help="lane(s) to call")
    sp.set_defaults(func=cmd_basecall)

    sp = sub.add_parser("simulate", help="generate a synthetic RSD file")
    sp.add_argument("length", type=int, help="number of bases")
    sp.add_argument("output", help="output .rsd path")
    sp.add_argument("--seed", type=int, default=0)
    sp.add_argument("--spacing-start", type=float, default=18.0)
    sp.add_argument("--spacing-end", type=float, default=7.0)
    sp.add_argument("--noise", type=float, default=120.0)
    sp.set_defaults(func=cmd_simulate)

    sp = sub.add_parser("compare", help="compare two FASTA files (accuracy)")
    sp.add_argument("reference")
    sp.add_argument("calls")
    sp.set_defaults(func=cmd_compare)

    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
