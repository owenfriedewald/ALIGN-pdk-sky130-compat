# Next Verification Runbook

Date: 2026-06-18

Verification status after this pass: `diagnostic_only`

This repo does not currently include an open_pdks install tree, Magic `sky130A.tech`, Netgen setup Tcl, generated GDS, or extracted SPICE. The next validation should be a one-circuit before/after test using the smallest available ALIGN-generated layout, preferably `examples/inverter` or `examples/buffer`.

## Required Inputs

| Input | Example variable |
|---|---|
| open_pdks Sky130A root containing `libs.tech/magic/sky130A.tech` and `libs.tech/netgen/sky130A_setup.tcl` | `OPEN_PDKS_SKY130A=/path/to/sky130A` |
| Generated ALIGN layout GDS for one circuit | `LAYOUT_GDS=/path/to/inverter.gds` |
| Top cell name in the GDS | `TOP=inverter` |
| Original schematic SPICE | `SCHEMATIC=examples/inverter/inverter.sp` |

## Diagnostic Precheck

Run from repo root:

```sh
python3 scripts/compare_layer_map.py
python3 scripts/normalize_netlist.py "$SCHEMATIC" -o reports/before_after/${TOP}.normalized.sp
```

Expected:
`compare_layer_map.py` should show `ok` for the main route/contact stack. The normalized SPICE should replace simple MOS aliases with official `sky130_fd_pr__nfet_01v8` / `sky130_fd_pr__pfet_01v8` names.

## Magic DRC Sketch

Create `reports/before_after/` before running:

```sh
mkdir -p reports/before_after reports/logs
magic -dnull -noconsole -rcfile "$OPEN_PDKS_SKY130A/libs.tech/magic/sky130A.magicrc" <<EOF | tee reports/logs/${TOP}.magic_drc.log
gds read $LAYOUT_GDS
load $TOP
drc style drc(full)
drc check
drc catchup
drc count total
drc why
quit -noprompt
EOF
```

Record result as `drc_clean` only if Magic reports zero DRC errors under the stated deck/setup.

## Magic Extraction Sketch

```sh
magic -dnull -noconsole -rcfile "$OPEN_PDKS_SKY130A/libs.tech/magic/sky130A.magicrc" <<EOF | tee reports/logs/${TOP}.magic_extract.log
gds read $LAYOUT_GDS
load $TOP
extract all
ext2spice lvs
ext2spice cthresh 0
ext2spice rthresh 0
ext2spice
quit -noprompt
EOF
```

Expected output is usually `${TOP}.spice` in the working directory unless Magic is configured otherwise. Move or copy that file into `reports/before_after/` with the exact command recorded.

## Netgen LVS Sketch

```sh
netgen -batch lvs \
  "$TOP.spice $TOP" \
  "reports/before_after/${TOP}.normalized.sp $TOP" \
  "$OPEN_PDKS_SKY130A/libs.tech/netgen/sky130A_setup.tcl" \
  reports/logs/${TOP}.lvs.report \
  | tee reports/logs/${TOP}.netgen_lvs.log
```

Record result as `lvs_clean` only if Netgen reports the circuits match and any property differences are understood under the active setup.

## Before/After Evidence To Preserve

For each one-circuit test, keep:

| File | Contents |
|---|---|
| `reports/logs/${TOP}.magic_drc.log` | Full Magic DRC command output. |
| `reports/logs/${TOP}.magic_extract.log` | Full extraction command output. |
| `reports/logs/${TOP}.netgen_lvs.log` | Netgen console output. |
| `reports/logs/${TOP}.lvs.report` | Netgen LVS report. |
| `reports/before_after/${TOP}.normalized.sp` | Schematic after optional alias normalization. |

## Current Expected First Failure

Given this pass, the first likely failures to inspect are:

| Area | Why |
|---|---|
| Labels/pins | `layers.json` uses `Pin=16` and `Label=5`; Magic/OpenLane conventions may need pin text placement checks. |
| Device extraction | MOS geometry may depend on helper layers such as `Fin`, `Lvt`, and `Hvt`; generated GDS evidence is needed. |
| Model/property matching | `normalize_netlist.py` handles only simple model aliases; Netgen may still need property tolerances and canonical parameter names. |
| Missing open_pdks setup | This repo currently does not include the Magic/Netgen setup required to make validation plug-and-play. |
