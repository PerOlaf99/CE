#!/usr/bin/env bash
# basecall.sh - dispatcher for all basecalling approaches.
#   ./basecall.sh denovo   A01.rsd              # our CNN ensemble, de-novo (91.53%)
#   ./basecall.sh denovo   --refine A01.rsd     # + de-novo gap-fill refinement pass
#   ./basecall.sh polished A01.rsd              # reference-guided polish (100%)
#   ./basecall.sh polished --eval --wells A01 B02 C03 D04
#   ./basecall.sh cimarron  A01.rsd             # commercial DLL baseline (90.72%)
set -e
R="$(cd "$(dirname "$0")" && pwd)"
cmd="${1:-}"; shift || true
case "$cmd" in
  denovo)          exec python3 "$R/02_denovo_cnn_ensemble_91.53pct/perfect_basecaller.py" "$@" ;;
  polished|polish) exec python3 "$R/01_polished_100.00pct/run_polish.py" "$@" ;;
  cimarron)        exec python3 "$R/03_cimarron312_dll_90.72pct/call_cimarron.py" "$@" ;;
  *) sed -n '2,9p' "$0"; exit 1 ;;
esac
