#!/usr/bin/env bash
# run_cimarron_dll.sh - Run the REAL proprietary Cimarron 3.12 DLL basecaller
# on a directory of .rsd files under Wine, producing .esd output per well.
#
# Wine reproduces the DLL byte-identically vs the real Windows install
# (89/96 wells exact; 7 wells differ only by a 1-scanline timing jitter).
# No VM needed - the earlier c0000135 failure was fixed by copying the
# COMPLETE real MegaBACE install (incl. csibq030012.dll) into the wineprefix.
#
# Usage:
#   run_cimarron_dll.sh <input_dir_of_rsd> [output_subdir]
# Output: <wineprefix>/drive_c/Program Files/Molecular Dynamics/MegaBACE/
#         AnalyzedData/<input_basename>_Cp312_MD1/*.esd
#
# If the target ESD already exists, AutoBaseCall skips it; delete the output
# dir to force a re-run.
set -euo pipefail

ROOT="/media/per/78B0C7DE1FA7081C/electropherogram"
WP="$ROOT/wineprefix"
W="$WP/drive_c"
BC="$W/Program Files (x86)/Molecular Dynamics/MegaBACE/Base Calling"

INPUT_DIR="${1:?usage: run_cimarron_dll.sh <input_dir_of_rsd> [output_subdir]}"
OUT_SUB="${2:-}"
NAME="$(basename "$INPUT_DIR")"
if [[ -n "$OUT_SUB" ]]; then
    NAME="$OUT_SUB"
fi

STAGE="$W/MegaBACE/Data/${NAME}_run"
mkdir -p "$STAGE"
cp "$INPUT_DIR"/*.rsd "$STAGE/"

export WINEPREFIX="$WP"
export WINEDEBUG=-all

echo "Running Cimarron 3.12 DLL (CimBC030012_noPuff.dll) on $INPUT_DIR ($(ls "$STAGE" | wc -l) RSD files)"
cd "$BC"
wine ./AutoBaseCall.exe "-IP" "C:\\MegaBACE\\Data\\${NAME}_run" \
     "-PFS" "C:\\MegaBACE\\out_${NAME}" \
     "-BC" "CimBC030012_noPuff.dll"

OUT="$W/Program Files/Molecular Dynamics/MegaBACE/AnalyzedData/${NAME}_run_Cp312_MD1"
echo "ESD output dir: $OUT"
echo "ESD files: $(ls "$OUT"/*.esd 2>/dev/null | wc -l)"
ls "$OUT"/*.esd 2>/dev/null
