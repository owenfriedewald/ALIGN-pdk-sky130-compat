#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_netgen_lvs.sh --open-pdks-root PATH --layout-spice PATH --schematic-spice PATH --top CELL --out-dir DIR

Runs Netgen LVS for one extracted layout SPICE and schematic SPICE pair.
Requires Netgen and an installed open_pdks sky130A tree.
EOF
}

OPEN_PDKS_ROOT=""
LAYOUT_SPICE=""
SCHEMATIC_SPICE=""
TOP=""
OUT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --open-pdks-root) OPEN_PDKS_ROOT="$2"; shift 2 ;;
    --layout-spice) LAYOUT_SPICE="$2"; shift 2 ;;
    --schematic-spice) SCHEMATIC_SPICE="$2"; shift 2 ;;
    --top) TOP="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$OPEN_PDKS_ROOT" || -z "$LAYOUT_SPICE" || -z "$SCHEMATIC_SPICE" || -z "$TOP" || -z "$OUT_DIR" ]]; then
  usage >&2
  exit 2
fi

SETUP_TCL="$OPEN_PDKS_ROOT/libs.tech/netgen/sky130A_setup.tcl"
OUT_DIR="$(realpath -m "$OUT_DIR")"
LOG_DIR="$OUT_DIR/raw_logs"
mkdir -p "$LOG_DIR"

command -v netgen >/dev/null || { echo "ERROR: netgen not found on PATH" >&2; exit 127; }
[[ -f "$SETUP_TCL" ]] || { echo "ERROR: missing Netgen setup: $SETUP_TCL" >&2; exit 2; }
[[ -f "$LAYOUT_SPICE" ]] || { echo "ERROR: missing layout SPICE: $LAYOUT_SPICE" >&2; exit 2; }
[[ -f "$SCHEMATIC_SPICE" ]] || { echo "ERROR: missing schematic SPICE: $SCHEMATIC_SPICE" >&2; exit 2; }
LAYOUT_SPICE="$(realpath "$LAYOUT_SPICE")"
SCHEMATIC_SPICE="$(realpath "$SCHEMATIC_SPICE")"

REPORT="$LOG_DIR/${TOP}.lvs.report"
LOG="$LOG_DIR/${TOP}.netgen_lvs.log"
COMMANDS="$OUT_DIR/commands.sh"
{
  echo "# Netgen LVS"
  printf 'scripts/run_netgen_lvs.sh --open-pdks-root %q --layout-spice %q --schematic-spice %q --top %q --out-dir %q\n' \
    "$OPEN_PDKS_ROOT" "$LAYOUT_SPICE" "$SCHEMATIC_SPICE" "$TOP" "$OUT_DIR"
} >> "$COMMANDS"

netgen -batch lvs \
  "$LAYOUT_SPICE $TOP" \
  "$SCHEMATIC_SPICE $TOP" \
  "$SETUP_TCL" \
  "$REPORT" \
  | tee "$LOG"

echo "Wrote $LOG"
echo "Wrote $REPORT"
