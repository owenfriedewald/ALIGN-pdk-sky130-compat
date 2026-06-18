# One-Circuit Validation Checklist

Date: 2026-06-18

Use this when a generated GDS, schematic SPICE, top cell, and open_pdks Sky130A path are available.

Verification levels start as `diagnostic_only`. Promote only with evidence:

- `drc_clean`: Magic DRC reports zero errors under the stated deck/setup.
- `lvs_clean`: Netgen reports matching circuits under the stated setup.
- `pex_available`: Magic extraction/PEX output is produced.

## Inputs

- [ ] Set `OPEN_PDKS_SKY130A` to the installed open_pdks `sky130A` directory.
- [ ] Set `LAYOUT_GDS` to the generated ALIGN GDS.
- [ ] Set `SCHEMATIC_SPICE` to the source schematic SPICE.
- [ ] Set `TOP` to the GDS/schematic top cell name.
- [ ] Confirm output directories exist.

```sh
export OPEN_PDKS_SKY130A=/path/to/share/pdk/sky130A
export LAYOUT_GDS=/path/to/generated/top.gds
export SCHEMATIC_SPICE=/path/to/source/top.sp
export TOP=top_cell_name
mkdir -p reports/before_after reports/logs
```

## Static Preflight

- [ ] Run the full prepared wrapper if all inputs are available:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root "$OPEN_PDKS_SKY130A" \
  --gds "$LAYOUT_GDS" \
  --schematic "$SCHEMATIC_SPICE" \
  --top "$TOP" \
  --out-dir "reports/before_after/${TOP}" \
  --drop-param stack
```

- [ ] If the full wrapper fails, continue with the individual commands below to isolate the missing input or failing stage.

- [ ] Check required reference files.

```sh
python3 scripts/check_verification_refs.py --open-pdks-root "$OPEN_PDKS_SKY130A" \
  | tee reports/logs/${TOP}.reference_preflight.log
```

- [ ] Check ALIGN layer mapping against SkyWater docs.

```sh
python3 scripts/compare_layer_map.py \
  | tee reports/logs/${TOP}.layer_map_check.log
```

- [ ] Check local model aliases and example parameter conventions.

```sh
python3 scripts/compare_model_names.py \
  | tee reports/logs/${TOP}.model_name_check.log
```

- [ ] Create an optional normalized schematic for Netgen experiments.

```sh
python3 scripts/normalize_netlist.py "$SCHEMATIC_SPICE" \
  -o reports/before_after/${TOP}.normalized.sp
```

## Magic DRC

- [ ] Run Magic DRC on the generated GDS.

```sh
magic -dnull -noconsole \
  -rcfile "$OPEN_PDKS_SKY130A/libs.tech/magic/sky130A.magicrc" <<EOF \
  | tee reports/logs/${TOP}.magic_drc.log
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

- [ ] Record whether result is `drc_clean` or still `diagnostic_only`.
- [ ] Do not filter violations. Classify them by layer/rule in a follow-up report.

## Magic Extraction

- [ ] Run Magic extraction and extracted SPICE generation.

```sh
magic -dnull -noconsole \
  -rcfile "$OPEN_PDKS_SKY130A/libs.tech/magic/sky130A.magicrc" <<EOF \
  | tee reports/logs/${TOP}.magic_extract.log
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

- [ ] Locate the extracted SPICE file.

```sh
find . -maxdepth 2 -type f \( -name "${TOP}.spice" -o -name "${TOP}.sp" \) -print \
  | tee reports/logs/${TOP}.extracted_spice_paths.log
```

- [ ] Preserve the extracted SPICE under `reports/before_after/`.

```sh
cp "${TOP}.spice" "reports/before_after/${TOP}.extracted.spice"
```

Adjust the source path if Magic emits a different filename.

## Netgen LVS

- [ ] Run LVS against the normalized schematic first.

```sh
netgen -batch lvs \
  "reports/before_after/${TOP}.extracted.spice $TOP" \
  "reports/before_after/${TOP}.normalized.sp $TOP" \
  "$OPEN_PDKS_SKY130A/libs.tech/netgen/sky130A_setup.tcl" \
  "reports/logs/${TOP}.lvs.report" \
  | tee reports/logs/${TOP}.netgen_lvs.log
```

- [ ] If normalization is suspected to hide useful evidence, rerun against the original schematic too.

```sh
netgen -batch lvs \
  "reports/before_after/${TOP}.extracted.spice $TOP" \
  "$SCHEMATIC_SPICE $TOP" \
  "$OPEN_PDKS_SKY130A/libs.tech/netgen/sky130A_setup.tcl" \
  "reports/logs/${TOP}.lvs.original_schematic.report" \
  | tee reports/logs/${TOP}.netgen_lvs.original_schematic.log
```

- [ ] Record whether result is `lvs_clean` or still `diagnostic_only`.
- [ ] Do not waive or filter mismatches. Classify each mismatch source.

## Optional PEX

- [ ] If DRC/LVS are sufficiently understood, produce parasitic extraction output.

```sh
magic -dnull -noconsole \
  -rcfile "$OPEN_PDKS_SKY130A/libs.tech/magic/sky130A.magicrc" <<EOF \
  | tee reports/logs/${TOP}.magic_pex.log
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

- [ ] Record `pex_available` only if an extracted SPICE/PEX file is produced and preserved.

## Report Summarization

- [ ] Summarize DRC counts.

```sh
rg -n "error|drc|count|why|Total" reports/logs/${TOP}.magic_drc.log \
  | tee reports/logs/${TOP}.magic_drc.summary.txt
```

- [ ] Summarize LVS outcome.

```sh
rg -n "match|mismatch|Netlists do not match|Circuits match|Property|Device|Net" \
  reports/logs/${TOP}.netgen_lvs.log reports/logs/${TOP}.lvs.report \
  | tee reports/logs/${TOP}.netgen_lvs.summary.txt
```

- [ ] Create or update a before/after note with:

```text
Issue:
Source diagnostic:
ALIGN-side file:
official/open_pdks reference:
Command run:
Before result:
After result:
Remaining problems:
Verification label:
```
