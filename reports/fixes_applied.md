# Fixes Applied

Date: 2026-06-18

## 1. Repeatable ALIGN-to-SkyWater Layer Map Comparison

Issue:
The diagnostic report classifies several route/contact GDS pairs as conflicts, but SkyWater uses the same base GDS layer number with different datatypes for related drawing layers.

Source diagnostic:
Sections 3.1 and 3.2 of `context/ALIGN SKY130 Diagnostic Report.md`.

Files changed:
`scripts/compare_layer_map.py`

Before behavior:
Layer-map review was manual and easy to conflate with layer base-number comparisons.

Patch made:
Added a script that compares `SKY130_PDK/layers.json` against `upstream/skywater-pdk/docs/rules/gds_layers.csv` using the explicit abstraction that ALIGN `M1` is SkyWater `li1`, ALIGN `M2` is SkyWater `met1`, and so on.

Why the patch is safe:
It is diagnostic-only and does not alter PDK generation semantics.

How to verify:

```sh
python3 scripts/compare_layer_map.py
```

Current result:
The main route/contact stack reports `ok`. Special/helper layers such as `Fin`, `Pc`, and boundary layers are reported as `skip` with notes.

Remaining limitations:
This does not validate generated GDS geometry, labels, Magic extraction behavior, or Netgen device matching.

## 2. SPICE Model Alias Normalization Helper

Issue:
Example schematics use a mixture of ALIGN aliases such as `nmos_lvt`/`pmos_rvt` and official-style model names such as `sky130_fd_pr__nfet_01v8`. LVS experiments often need schematic model names to match extraction/setup expectations.

Source diagnostic:
Section 4 attributes LVS failures to extraction/layer issues; model aliasing is a related low-risk LVS dialect bridge visible in local examples and `SKY130_PDK/models.sp`.

Files changed:
`scripts/normalize_netlist.py`
`tests/fixtures/normalize_input.sp`
`tests/fixtures/normalize_expected.sp`

Before behavior:
No local helper existed to normalize simple MOS model aliases before a Netgen experiment.

Patch made:
Added a small SPICE line normalizer for MOS instance model tokens. It maps common ALIGN aliases to `sky130_fd_pr__nfet_01v8` or `sky130_fd_pr__pfet_01v8` and leaves unrecognized lines unchanged.

Why the patch is safe:
It is opt-in and writes to stdout unless an output path is supplied. It does not modify examples or PDK collateral in place.

How to verify:

```sh
python3 scripts/normalize_netlist.py tests/fixtures/normalize_input.sp -o /tmp/align_sky130_normalized_fixture.sp
diff -u tests/fixtures/normalize_expected.sp /tmp/align_sky130_normalized_fixture.sp
```

Remaining limitations:
This is not a full SPICE parser. It intentionally handles simple MOS instance model normalization only. Netgen setup may still require property tolerances, device class mapping, subcircuit flattening choices, and pin normalization.

## 3. One-Circuit Magic/Netgen Wrapper Scripts

Issue:
The repository had no runnable wrapper for the first one-circuit Magic DRC, Magic extraction, extracted SPICE, Netgen LVS, or report summarization pass.

Source diagnostic:
The diagnostic report recommends rerunning DRC/LVS after mapping/setup issues are clarified. `reports/reference_file_inventory.md` shows the runtime decks and tools are missing locally, so wrappers need explicit path checks and should preserve raw logs.

Files changed:
`scripts/run_magic_drc.sh`
`scripts/run_magic_extract.sh`
`scripts/run_netgen_lvs.sh`
`scripts/run_one_circuit_validation.sh`
`scripts/summarize_drc_log.py`
`scripts/summarize_lvs_log.py`

Before behavior:
The runbook documented commands, but there was no executable, repeatable wrapper.

Patch made:
Added explicit shell wrappers for Magic DRC, Magic extraction/ext2spice, Netgen LVS, and a one-command orchestration script. Added Python summarizers for Magic DRC and Netgen LVS logs.

Why the patch is safe:
The scripts are opt-in, preserve raw logs, do not filter errors, and do not modify PDK collateral or generated GDS. They fail fast if required tools or open_pdks files are missing.

How to verify:

```sh
bash -n scripts/run_magic_drc.sh scripts/run_magic_extract.sh scripts/run_netgen_lvs.sh scripts/run_one_circuit_validation.sh
scripts/run_one_circuit_validation.sh --help
python3 scripts/summarize_drc_log.py tests/fixtures/magic_drc_sample.log
python3 scripts/summarize_lvs_log.py tests/fixtures/netgen_lvs_sample.log
```

Remaining limitations:
No real Magic/Netgen validation was possible because this environment lacks generated GDS, Magic, Netgen, and an open_pdks `sky130A` install.

## 4. Extended Netlist Normalization Options

Issue:
The inverter example contains ALIGN-only `stack=3` MOS parameters. Netgen LVS may compare against extracted devices that do not carry this schematic-only parameter.

Source diagnostic:
LVS dialect/model mismatch category from the diagnostic report and `reports/mismatch_to_file_map.md`.

Files changed:
`scripts/normalize_netlist.py`

Before behavior:
The normalizer only replaced model aliases.

Patch made:
Added explicit opt-in `--drop-param NAME` and `--rename-param OLD=NEW` options for MOS instance parameters.

Why the patch is safe:
Default behavior remains model alias normalization only. Parameter dropping/renaming must be requested explicitly in the command and is recorded by the wrapper.

How to verify:

```sh
python3 scripts/normalize_netlist.py examples/inverter/inverter.sp --drop-param stack -o /tmp/inverter.normalized.sp
```

Remaining limitations:
This is still a lightweight line-oriented normalizer, not a general SPICE parser.

## 5. Reference Preflight Environment Detection

Issue:
The workspace needed a quick way to distinguish missing local runtime files from available documentation references.

Source diagnostic:
Reference-file inventory and long-run environment discovery.

Files changed:
`scripts/check_verification_refs.py`

Before behavior:
The script searched the repo and optional open_pdks root, but did not report tool executables or common PDK search roots.

Patch made:
Added executable reporting for `magic`, `netgen`, `klayout`, and `schematic2layout.py`, plus `--search-common` for common local PDK directories.

Why the patch is safe:
Read-only discovery only.

How to verify:

```sh
python3 scripts/check_verification_refs.py --search-common
```

Remaining limitations:
The current environment still lacks Magic, Netgen, ALIGN CLI, open_pdks runtime files, and generated GDS.
