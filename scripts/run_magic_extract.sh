#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  run_magic_extract.sh --open-pdks-root PATH --gds PATH --top CELL --out-dir DIR

Runs Magic extraction/ext2spice for one generated GDS/top cell.
Requires Magic and an installed open_pdks sky130A tree.
EOF
}

OPEN_PDKS_ROOT=""
GDS=""
TOP=""
OUT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --open-pdks-root) OPEN_PDKS_ROOT="$2"; shift 2 ;;
    --gds) GDS="$2"; shift 2 ;;
    --top) TOP="$2"; shift 2 ;;
    --out-dir) OUT_DIR="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

if [[ -z "$OPEN_PDKS_ROOT" || -z "$GDS" || -z "$TOP" || -z "$OUT_DIR" ]]; then
  usage >&2
  exit 2
fi

MAGIC_RC="$OPEN_PDKS_ROOT/libs.tech/magic/sky130A.magicrc"
OUT_DIR="$(realpath -m "$OUT_DIR")"
LOG_DIR="$OUT_DIR/raw_logs"
EXTRACT_DIR="$OUT_DIR/extracted"
WORK_DIR="$OUT_DIR/magic_work"
mkdir -p "$LOG_DIR" "$EXTRACT_DIR" "$WORK_DIR"

command -v magic >/dev/null || { echo "ERROR: magic not found on PATH" >&2; exit 127; }
[[ -f "$MAGIC_RC" ]] || { echo "ERROR: missing Magic rc: $MAGIC_RC" >&2; exit 2; }
[[ -f "$GDS" ]] || { echo "ERROR: missing GDS: $GDS" >&2; exit 2; }
GDS="$(realpath "$GDS")"

LOG="$LOG_DIR/${TOP}.magic_extract.log"
COMMANDS="$OUT_DIR/commands.sh"
{
  echo "# Magic extraction"
  printf 'scripts/run_magic_extract.sh --open-pdks-root %q --gds %q --top %q --out-dir %q\n' \
    "$OPEN_PDKS_ROOT" "$GDS" "$TOP" "$OUT_DIR"
} >> "$COMMANDS"

(
  cd "$WORK_DIR"
  magic -dnull -noconsole -rcfile "$MAGIC_RC" <<EOF | tee "$LOG"
gds read $GDS
load $TOP
extract all
ext2spice lvs
ext2spice cthresh 0
ext2spice rthresh 0
ext2spice
quit -noprompt
EOF
)

if [[ -f "$WORK_DIR/${TOP}.spice" ]]; then
  cp "$WORK_DIR/${TOP}.spice" "$EXTRACT_DIR/${TOP}.extracted.spice"
  echo "Wrote $EXTRACT_DIR/${TOP}.extracted.spice"
else
  echo "WARNING: expected extracted SPICE not found at $WORK_DIR/${TOP}.spice" >&2
fi
echo "Wrote $LOG"
