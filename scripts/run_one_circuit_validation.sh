#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_one_circuit_validation.sh --open-pdks-root PATH --gds PATH --schematic PATH --top CELL --out-dir DIR [--drop-param NAME ...]
  run_one_circuit_validation.sh --open-pdks-root PATH --gds PATH --layout-top CELL --schematic PATH --schematic-top CELL --out-dir DIR [--drop-param NAME ...] [--expand-nf-stack] [--scale-wl-to-um]

Runs the prepared one-circuit flow:
  reference preflight -> static layer/model checks -> schematic normalization ->
  Magic DRC -> Magic extraction/ext2spice -> Netgen LVS -> log summaries.

This script does not waive or filter errors. Raw logs are preserved under OUT_DIR/raw_logs.
By default it writes a sanitized verification GDS under OUT_DIR/normalized that drops
known ALIGN helper layers rejected by Magic; use --no-sanitize-gds to disable this.
EOF
}

OPEN_PDKS_ROOT=""
GDS=""
SCHEMATIC=""
TOP=""
LAYOUT_TOP=""
SCHEMATIC_TOP=""
OUT_DIR=""
DROP_PARAMS=()
SANITIZE_GDS=1
EXPAND_NF_STACK=0
SCALE_WL_TO_UM=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --open-pdks-root) OPEN_PDKS_ROOT="$2"; shift 2 ;;
    --gds) GDS="$2"; shift 2 ;;
    --schematic) SCHEMATIC="$2"; shift 2 ;;
    --top) TOP="$2"; shift 2 ;;
    --layout-top) LAYOUT_TOP="$2"; shift 2 ;;
    --schematic-top) SCHEMATIC_TOP="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    --drop-param) DROP_PARAMS+=("$2"); shift 2 ;;
    --no-sanitize-gds) SANITIZE_GDS=0; shift ;;
    --expand-nf-stack) EXPAND_NF_STACK=1; shift ;;
    --scale-wl-to-um) SCALE_WL_TO_UM=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -n "$TOP" ]]; then
  LAYOUT_TOP="${LAYOUT_TOP:-$TOP}"
  SCHEMATIC_TOP="${SCHEMATIC_TOP:-$TOP}"
fi

if [[ -z "$OPEN_PDKS_ROOT" || -z "$GDS" || -z "$SCHEMATIC" || -z "$LAYOUT_TOP" || -z "$SCHEMATIC_TOP" || -z "$OUT_DIR" ]]; then
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
  printf 'scripts/run_one_circuit_validation.sh --open-pdks-root %q --gds %q --layout-top %q --schematic %q --schematic-top %q --out-dir %q' \
    "$OPEN_PDKS_ROOT" "$GDS" "$LAYOUT_TOP" "$SCHEMATIC" "$SCHEMATIC_TOP" "$OUT_DIR"
  for param in "${DROP_PARAMS[@]}"; do
    printf ' --drop-param %q' "$param"
  done
  if [[ "$EXPAND_NF_STACK" -eq 1 ]]; then
    printf ' --expand-nf-stack'
  fi
  if [[ "$SCALE_WL_TO_UM" -eq 1 ]]; then
    printf ' --scale-wl-to-um'
  fi
  printf '\n'
} >> "$COMMANDS"

python3 scripts/check_verification_refs.py --open-pdks-root "$OPEN_PDKS_ROOT" \
  | tee "$RAW_LOGS/${SCHEMATIC_TOP}.reference_preflight.log"
python3 scripts/compare_layer_map.py \
  | tee "$RAW_LOGS/${SCHEMATIC_TOP}.layer_map_check.log"
python3 scripts/compare_model_names.py \
  | tee "$RAW_LOGS/${SCHEMATIC_TOP}.model_name_check.log"

VERIFY_GDS="$GDS"
if [[ "$SANITIZE_GDS" -eq 1 ]]; then
  VERIFY_GDS="$NORMALIZED/${LAYOUT_TOP}.magic_sanitized.gds"
  python3 scripts/sanitize_gds_for_magic.py "$GDS" -o "$VERIFY_GDS" \
    | tee "$RAW_LOGS/${LAYOUT_TOP}.sanitize_gds.log"
fi

NORMALIZE_ARGS=()
for param in "${DROP_PARAMS[@]}"; do
  NORMALIZE_ARGS+=(--drop-param "$param")
done
if [[ "$EXPAND_NF_STACK" -eq 1 ]]; then
  NORMALIZE_ARGS+=(--expand-nf-stack)
fi
if [[ "$SCALE_WL_TO_UM" -eq 1 ]]; then
  NORMALIZE_ARGS+=(--scale-wl-to-um)
fi
python3 scripts/normalize_netlist.py "$SCHEMATIC" "${NORMALIZE_ARGS[@]}" \
  -o "$NORMALIZED/${SCHEMATIC_TOP}.normalized.sp"

scripts/run_magic_drc.sh \
  --open-pdks-root "$OPEN_PDKS_ROOT" \
  --gds "$VERIFY_GDS" \
  --top "$LAYOUT_TOP" \
  --out-dir "$OUT_DIR"

scripts/run_magic_extract.sh \
  --open-pdks-root "$OPEN_PDKS_ROOT" \
  --gds "$VERIFY_GDS" \
  --top "$LAYOUT_TOP" \
  --out-dir "$OUT_DIR"

LAYOUT_SPICE="$EXTRACTED/${LAYOUT_TOP}.extracted.spice"
scripts/run_netgen_lvs.sh \
  --open-pdks-root "$OPEN_PDKS_ROOT" \
  --layout-spice "$LAYOUT_SPICE" \
  --layout-top "$LAYOUT_TOP" \
  --schematic-spice "$NORMALIZED/${SCHEMATIC_TOP}.normalized.sp" \
  --schematic-top "$SCHEMATIC_TOP" \
  --out-dir "$OUT_DIR"

python3 scripts/summarize_drc_log.py "$RAW_LOGS/${LAYOUT_TOP}.magic_drc.log" \
  | tee "$RAW_LOGS/${LAYOUT_TOP}.magic_drc.summary.txt"
python3 scripts/summarize_lvs_log.py "$RAW_LOGS/${SCHEMATIC_TOP}_vs_${LAYOUT_TOP}.netgen_lvs.log" "$RAW_LOGS/${SCHEMATIC_TOP}_vs_${LAYOUT_TOP}.lvs.report" \
  | tee "$RAW_LOGS/${SCHEMATIC_TOP}_vs_${LAYOUT_TOP}.netgen_lvs.summary.txt"

cat > "$OUT_DIR/summary.md" <<EOF
# One-Circuit Validation Summary

Layout top: \`$LAYOUT_TOP\`
Schematic top: \`$SCHEMATIC_TOP\`

Raw logs: \`$RAW_LOGS\`
Verification GDS: \`$VERIFY_GDS\`
Normalized schematic: \`$NORMALIZED/${SCHEMATIC_TOP}.normalized.sp\`
Extracted SPICE: \`$LAYOUT_SPICE\`

Review:
- \`$RAW_LOGS/${LAYOUT_TOP}.magic_drc.summary.txt\`
- \`$RAW_LOGS/${SCHEMATIC_TOP}_vs_${LAYOUT_TOP}.netgen_lvs.summary.txt\`
EOF

echo "Wrote $OUT_DIR/summary.md"
