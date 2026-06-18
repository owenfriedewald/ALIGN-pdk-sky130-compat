#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_one_circuit_validation.sh --open-pdks-root PATH --gds PATH --schematic PATH --top CELL --out-dir DIR [--drop-param NAME ...]

Runs the prepared one-circuit flow:
  reference preflight -> static layer/model checks -> schematic normalization ->
  Magic DRC -> Magic extraction/ext2spice -> Netgen LVS -> log summaries.

This script does not waive or filter errors. Raw logs are preserved under OUT_DIR/raw_logs.
EOF
}

OPEN_PDKS_ROOT=""
GDS=""
SCHEMATIC=""
TOP=""
OUT_DIR=""
DROP_PARAMS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --open-pdks-root) OPEN_PDKS_ROOT="$2"; shift 2 ;;
    --gds) GDS="$2"; shift 2 ;;
    --schematic) SCHEMATIC="$2"; shift 2 ;;
    --top) TOP="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --drop-param) DROP_PARAMS+=("$2"); shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$OPEN_PDKS_ROOT" || -z "$GDS" || -z "$SCHEMATIC" || -z "$TOP" || -z "$OUT_DIR" ]]; then
  usage >&2
  exit 2
fi

OUT_DIR="$(realpath -m "$OUT_DIR")"
RAW_LOGS="$OUT_DIR/raw_logs"
NORMALIZED="$OUT_DIR/normalized"
EXTRACTED="$OUT_DIR/extracted"
mkdir -p "$RAW_LOGS" "$NORMALIZED" "$EXTRACTED"

COMMANDS="$OUT_DIR/commands.sh"
{
  echo "# One-circuit validation command"
  printf 'scripts/run_one_circuit_validation.sh --open-pdks-root %q --gds %q --schematic %q --top %q --out-dir %q' \
    "$OPEN_PDKS_ROOT" "$GDS" "$SCHEMATIC" "$TOP" "$OUT_DIR"
  for param in "${DROP_PARAMS[@]}"; do
    printf ' --drop-param %q' "$param"
  done
  printf '\n'
} >> "$COMMANDS"

python3 scripts/check_verification_refs.py --open-pdks-root "$OPEN_PDKS_ROOT" \
  | tee "$RAW_LOGS/${TOP}.reference_preflight.log"
python3 scripts/compare_layer_map.py \
  | tee "$RAW_LOGS/${TOP}.layer_map_check.log"
python3 scripts/compare_model_names.py \
  | tee "$RAW_LOGS/${TOP}.model_name_check.log"

NORMALIZE_ARGS=()
for param in "${DROP_PARAMS[@]}"; do
  NORMALIZE_ARGS+=(--drop-param "$param")
done
python3 scripts/normalize_netlist.py "$SCHEMATIC" "${NORMALIZE_ARGS[@]}" \
  -o "$NORMALIZED/${TOP}.normalized.sp"

scripts/run_magic_drc.sh \
  --open-pdks-root "$OPEN_PDKS_ROOT" \
  --gds "$GDS" \
  --top "$TOP" \
  --out-dir "$OUT_DIR"

scripts/run_magic_extract.sh \
  --open-pdks-root "$OPEN_PDKS_ROOT" \
  --gds "$GDS" \
  --top "$TOP" \
  --out-dir "$OUT_DIR"

LAYOUT_SPICE="$EXTRACTED/${TOP}.extracted.spice"
scripts/run_netgen_lvs.sh \
  --open-pdks-root "$OPEN_PDKS_ROOT" \
  --layout-spice "$LAYOUT_SPICE" \
  --schematic-spice "$NORMALIZED/${TOP}.normalized.sp" \
  --top "$TOP" \
  --out-dir "$OUT_DIR"

python3 scripts/summarize_drc_log.py "$RAW_LOGS/${TOP}.magic_drc.log" \
  | tee "$RAW_LOGS/${TOP}.magic_drc.summary.txt"
python3 scripts/summarize_lvs_log.py "$RAW_LOGS/${TOP}.netgen_lvs.log" "$RAW_LOGS/${TOP}.lvs.report" \
  | tee "$RAW_LOGS/${TOP}.netgen_lvs.summary.txt"

cat > "$OUT_DIR/summary.md" <<EOF
# One-Circuit Validation Summary

Top: \`$TOP\`

Raw logs: \`$RAW_LOGS\`
Normalized schematic: \`$NORMALIZED/${TOP}.normalized.sp\`
Extracted SPICE: \`$LAYOUT_SPICE\`

Review:
- \`$RAW_LOGS/${TOP}.magic_drc.summary.txt\`
- \`$RAW_LOGS/${TOP}.netgen_lvs.summary.txt\`
EOF

echo "Wrote $OUT_DIR/summary.md"
