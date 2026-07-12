#!/usr/bin/env bash
# SKELETOME — end-to-end scoring + aggregation.
#
#   ./run.sh              # MOCK by default: fully offline, no API key, no data DL.
#   ./run.sh --full       # REAL AlphaGenome (needs ALPHAGENOME_API_KEY) + optional
#                         # ChromBPNet (needs the isolated env + model H5 env vars).
#
# Reads/writes the CANONICAL RESULTS TSV at every stage. Idempotent; each stage
# writes a distinct file so you can inspect intermediates.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK="${SKELETOME_WORK:-$HERE/../work}"
mkdir -p "$WORK"

MODE="mock"
CBP="off"
for arg in "$@"; do
  case "$arg" in
    --full) MODE="full" ;;
    --with-chrombpnet) CBP="on" ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

PY="${PYTHON:-python}"
IN="${SKELETOME_INPUT:-$WORK/00_input.tsv}"

echo "=== SKELETOME scoring pipeline (mode=$MODE, chrombpnet=$CBP) ==="

# --- Stage 0: input (real runs supply P1/P2 output; demo generates a fixture) ---
if [[ ! -f "$IN" ]]; then
  echo "[run] no input TSV at $IN — generating demo fixture (controls + random HARs)."
  "$PY" "$HERE/make_demo_input.py" --out "$IN"
fi

FULL_FLAG=""
[[ "$MODE" == "full" ]] && FULL_FLAG="--full"

# --- Stage 1: AlphaGenome (PRIMARY) ---
"$PY" "$HERE/score_alphagenome.py" --in "$IN" --out "$WORK/10_alphagenome.tsv" $FULL_FLAG

CUR="$WORK/10_alphagenome.tsv"

# --- Stage 2: ChromBPNet (OPTIONAL; no-ops cleanly if env absent) ---
if [[ "$CBP" == "on" ]]; then
  "$PY" "$HERE/score_chrombpnet.py" --in "$CUR" --out "$WORK/20_chrombpnet.tsv" || {
    echo "[run] ChromBPNet stage failed; continuing with AlphaGenome only." >&2
    cp "$CUR" "$WORK/20_chrombpnet.tsv"; }
  CUR="$WORK/20_chrombpnet.tsv"
fi

# --- Stage 3: neural comparator + skeletal_specific ---
"$PY" "$HERE/comparator.py" --in "$CUR" --out "$WORK/30_comparator.tsv" $FULL_FLAG
CUR="$WORK/30_comparator.tsv"

# --- Stage 4: aggregate + permutation null + BH-FDR + BLIND GDF5 validation ---
NPERM="${SKELETOME_NPERM:-10000}"
"$PY" "$HERE/aggregate.py" --in "$CUR" --out "$WORK/40_results.tsv" --n-perm "$NPERM"

echo "=== done. final canonical TSV: $WORK/40_results.tsv ==="
