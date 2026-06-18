# Long-Run Summary

Date: 2026-06-18

## Branch And Starting Point

Starting commit: `0f04c647bf6767c79fb8f7eab1ac64306888b4db`

Working branch: `sky130-compat-longrun`

The branch was created after an initial sandbox failure writing `.git` refs; the successful branch creation used escalation and is recorded in `reports/verification_log.md`.

## Environment Discovery

Found:

- Python: `/usr/bin/python3`
- KLayout: `/usr/bin/klayout`
- ALIGN-side collateral: `SKY130_PDK/`
- Source schematic SPICE examples: `examples/*/*.sp`
- First recommended schematic target: `examples/inverter/inverter.sp`, top cell `inverter`
- SkyWater reference docs/rules: `upstream/skywater-pdk/docs/`
- GDS layer map: `upstream/skywater-pdk/docs/rules/gds_layers.csv`

Not found:

- Generated ALIGN Sky130 GDS files
- `magic` executable
- `netgen` executable
- `schematic2layout.py`
- open_pdks `sky130A` install path
- `sky130A.tech`
- `sky130A.magicrc` / `.magicrc`
- `sky130A_setup.tcl`
- Magic runtime extraction files

`scripts/check_verification_refs.py --search-common` currently reports missing runtime verification files and tools.

## Real One-Circuit Run Status

A real `GDS -> Magic DRC -> Magic extraction -> extracted SPICE -> Netgen LVS` run was not possible in this environment because no generated GDS, open_pdks runtime deck, Magic executable, or Netgen executable was available.

The workspace is now prepared so that the first real run can be launched with one command once those inputs are provided.

## Fixes Applied

Verification and LVS-prep improvements:

- Added Magic DRC wrapper: `scripts/run_magic_drc.sh`
- Added Magic extraction/ext2spice wrapper: `scripts/run_magic_extract.sh`
- Added Netgen LVS wrapper: `scripts/run_netgen_lvs.sh`
- Added one-command flow wrapper: `scripts/run_one_circuit_validation.sh`
- Added DRC log summarizer: `scripts/summarize_drc_log.py`
- Added LVS log summarizer: `scripts/summarize_lvs_log.py`
- Enhanced `scripts/check_verification_refs.py` to report tools and scan common PDK locations with `--search-common`
- Enhanced `scripts/normalize_netlist.py` with explicit opt-in MOS parameter dropping and renaming
- Added fixture logs for summarizer smoke tests

No `SKY130_PDK/layers.json` geometry/rule changes were applied. Current static comparison still indicates the main ALIGN abstract stack matches SkyWater GDS pairs when interpreted as `M1=li1`, `M2=met1`, etc.

## Current First Circuit

Use the inverter first:

- Schematic: `examples/inverter/inverter.sp`
- Top cell: `inverter`
- Recommended normalization: `--drop-param stack`

Reason: it is the smallest local schematic and includes simple MOS devices with ALIGN-only `stack` parameters.

## Exact Next Command

Once a generated inverter GDS and open_pdks `sky130A` install path are available:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root /path/to/share/pdk/sky130A \
  --gds /path/to/generated/inverter.gds \
  --schematic examples/inverter/inverter.sp \
  --top inverter \
  --out-dir reports/before_after/inverter \
  --drop-param stack
```

Before that, verify the open_pdks path:

```sh
python3 scripts/check_verification_refs.py --open-pdks-root /path/to/share/pdk/sky130A
```

## Branch Risk

This branch is safe to keep as a compatibility-prep branch. It should still be treated as experimental until a real one-circuit Magic/Netgen run is completed, because no physical DRC/LVS claims have been validated.
