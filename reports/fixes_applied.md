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

## 6. Experimental open_pdks Compatibility Metadata

Issue:
Layer/model compatibility knowledge was spread across reports and scripts, making it harder to audit future wrapper behavior against the PDK collateral.

Source diagnostic:
Layer naming and model-name mismatch classes from the diagnostic report and follow-up triage.

Files changed:
`SKY130_PDK/openpdks_compat.json`
`scripts/compare_layer_map.py`
`scripts/compare_model_names.py`
`scripts/normalize_netlist.py`

Before behavior:
The layer-map and model alias decisions were hardcoded in scripts.

Patch made:
Added `SKY130_PDK/openpdks_compat.json` with the experimental ALIGN-to-SkyWater layer map, special-layer notes, model aliases, and recommended LVS parameter drops. Updated helper scripts to read this metadata.

Why the patch is safe:
The file is metadata only. ALIGN generation does not consume it unless a wrapper or diagnostic script opts into it.

How to verify:

```sh
python3 scripts/compare_layer_map.py
python3 scripts/compare_model_names.py
```

Remaining limitations:
This is static compatibility metadata, not physical verification evidence.

## 7. Official LVT/HVT Model Alias Support

Issue:
The previous netlist normalizer collapsed `nmos_lvt` and `pmos_lvt` aliases to generic 1.8 V FET models, losing VT intent before LVS.

Source diagnostic:
Official SkyWater docs list `sky130_fd_pr__nfet_01v8_lvt`, `sky130_fd_pr__pfet_01v8_lvt`, and `sky130_fd_pr__pfet_01v8_hvt`.

Files changed:
`SKY130_PDK/models.sp`
`SKY130_PDK/openpdks_compat.json`
`scripts/normalize_netlist.py`
`tests/fixtures/normalize_expected.sp`

Before behavior:
ALIGN aliases normalized to generic `sky130_fd_pr__nfet_01v8` / `sky130_fd_pr__pfet_01v8`.

Patch made:
Mapped `nmos_lvt` to `sky130_fd_pr__nfet_01v8_lvt`, `pmos_lvt` to `sky130_fd_pr__pfet_01v8_lvt`, and `pmos_hvt` to `sky130_fd_pr__pfet_01v8_hvt`. Added official LVT/HVT model stubs to `models.sp` so schematics using official variant names can be parsed by the ALIGN-side model parser.

Also added official MIM capacitor parser stubs for `sky130_fd_pr__cap_mim_m3_2`, `sky130_fd_pr__cap_mim_m4`, and `sky130_fd_pr__model__cap_mim`, while keeping the existing ALIGN `sky130_fd_pr__cap_mim_m3_1` stub.

Why the patch is safe:
This affects model naming/parsing and optional LVS normalization only; it does not change layout geometry.

How to verify:

```sh
python3 scripts/normalize_netlist.py examples/inverter/inverter.sp --drop-param stack -o /tmp/inverter.normalized.sp
```

Remaining limitations:
Whether Magic extraction emits these exact variant model names depends on generated geometry/marker layers and the open_pdks Magic extraction setup.

Whether ALIGN-generated MIM capacitor geometry matches official/open_pdks extraction still requires a generated capacitor layout and Magic/Netgen evidence.

## 8. SPICE And GDS Inspection Helpers

Issue:
Once generated artifacts are provided, we need quick pre-Magic/pre-Netgen visibility into schematic top cells, pins, model usage, parameters, and streamed GDS layer/datatype usage.

Source diagnostic:
Pin/port, layer-map, and model/parameter mismatch classes.

Files changed:
`scripts/inspect_spice.py`
`scripts/inspect_gds_layers.py`

Before behavior:
Top-cell/pin/model inspection required ad hoc `rg` commands, and there was no prepared GDS layer dump helper.

Patch made:
Added `inspect_spice.py` for subcircuits, pins, instance counts, model references, and parameter names. Added `inspect_gds_layers.py` to read a GDS with KLayout Python and compare used layer/datatype pairs against `SKY130_PDK/openpdks_compat.json`.

Why the patch is safe:
Read-only diagnostics only.

How to verify:

```sh
python3 scripts/inspect_spice.py examples/inverter/inverter.sp
python3 scripts/inspect_gds_layers.py --help
```

Remaining limitations:
`inspect_gds_layers.py` requires a KLayout Python module and a real GDS file.

## 9. Validation Input Discovery Helper

Issue:
When generated artifacts are later added somewhere in the workspace or common PDK directories, manually finding the right GDS/SPICE/open_pdks tuple is error-prone.

Source diagnostic:
Long-run environment discovery requirements.

Files changed:
`scripts/discover_validation_inputs.py`

Before behavior:
Discovery used ad hoc `find` commands.

Patch made:
Added a helper that reports tool availability, scans roots for GDS/SPICE/open_pdks `sky130A` candidates, infers SPICE top cells, ranks real examples ahead of fixtures/PDK models, and prints a `run_one_circuit_validation.sh` command when it finds a complete tuple.

Why the patch is safe:
Read-only discovery only.

How to verify:

```sh
python3 scripts/discover_validation_inputs.py --root . --limit 12
```

Remaining limitations:
No complete validation tuple is currently present because GDS and open_pdks are missing.

## 10. Tuple-Backed Magic/Netgen Flow Fixes

Issue:
The provided inverter tuple showed that a single `--top inverter` value caused Magic to load a new empty cell while the GDS top cell was actually `INVERTER_0`.

Source diagnostic:
Real run on `artifacts/inverter_tuple/inverter/generated/inverter.gds`.

Files changed:
`scripts/run_magic_drc.sh`
`scripts/run_magic_extract.sh`
`scripts/run_netgen_lvs.sh`
`scripts/run_one_circuit_validation.sh`
`scripts/sanitize_gds_for_magic.py`
`SKY130_PDK/openpdks_compat.json`

Before result:
Magic reported unknown helper layers and then created an empty `inverter` cell. The apparent DRC count of zero was invalid.

Patch made:
Added separate layout/schematic top support, hard failure on Magic empty-cell/load failures, and a KLayout-based verification GDS sanitizer that drops known ALIGN helper layers rejected by Magic: `100:5`, `104:0`, and `235:5`. Preserved official `69:5` met2 label shapes.

Why the patch is safe:
The source GDS is not modified. The sanitized GDS is a derived verification artifact, and every dropped layer is logged.

After result:
Magic loaded `INVERTER_0`, reported 60 DRC errors, produced extracted SPICE, and Netgen ran. This advanced the state from setup failure to real DRC/LVS mismatch evidence.

Remaining problems:
Helper-layer dropping is still a wrapper/export bridge. A direct PDK-only removal attempt using `NoGDS` failed because ALIGN's installed `gen_gds_json.py` hard-codes `Bbox['GdsLayerNo']`.

## 11. HVT GDS Mapping Correction

Issue:
`SKY130_PDK/layers.json` encoded `Hvt` as `970:0`, which is not a SkyWater GDS layer.

Source diagnostic:
SkyWater `upstream/skywater-pdk/docs/rules/gds_layers.csv` lists `hvtp,drawing,78:44`.

Files changed:
`SKY130_PDK/layers.json`
`SKY130_PDK/openpdks_compat.json`
`scripts/compare_layer_map.py`

Before result:
`compare_layer_map.py` classified `Hvt` as a skipped nonstandard layer.

Patch made:
Changed `Hvt` to official `hvtp` GDS `78:44` and added it to the static layer comparison map.

Why the patch is safe:
This is an upstream-backed name/layer correction. The inverter tuple uses LVT, so no inverter geometry changed from this patch.

How to verify:

```sh
python3 scripts/compare_layer_map.py
```

Remaining problems:
PMOS HVT extraction still needs an HVT layout test.

## 12. LVS nf/stack Physical Expansion Experiment

Issue:
ALIGN Sky130 schematics describe a MOS as one device with `nf=20 stack=3`, but Magic/open_pdks extracts the generated planar layout as 60 physical MOS segments per device. This is inherited from the mock FinFET-style abstraction.

Source diagnostic:
Inverter tuple LVS before expansion: layout had 60 NFET + 60 PFET instances; normalized schematic had 1 NFET + 1 PFET.

Files changed:
`scripts/normalize_netlist.py`
`scripts/run_one_circuit_validation.sh`

Patch made:
Added opt-in `--expand-nf-stack` and `--scale-wl-to-um` normalizer modes. The one-circuit wrapper can now pass these options through.

Why the patch is safe:
This is an explicit LVS experiment mode, not default behavior and not a DRC waiver.

After result:
Against no-PEX extracted inverter SPICE, expanded schematic LVS reached matching top-level counts:

```text
Circuit 1 contains 120 devices, Circuit 2 contains 120 devices.
Circuit 1 contains 564 nets,    Circuit 2 contains 564 nets.
```

Remaining problems:
Netgen still failed top-level pin/net matching. The next PDK/generator fix is connectivity/pin semantics, not just model naming or raw device count.

## 13. Generation-Time Helper Layer Suppression

Issue:
ALIGN-generated Sky130 GDS includes helper/boundary layers rejected by open_pdks Magic. Post-generation sanitization works, but it is better to stop non-fabric helper layers from streaming where possible.

Source diagnostic:
Magic import rejected helper layer-purpose pairs `100:5`, `104:0`, and `235:5`. A first PDK-only `NoGDS` experiment failed because ALIGN's installed Python GDS exporter always accessed `Bbox['GdsLayerNo']`.

Files changed:
`SKY130_PDK/layers.json`
`scripts/patch_align_gds_export.py`

Patch made:
Marked `Bbox`, `Boundary`, `Rboundary`, `Cboundary`, and `Outline` as `"NoGDS": true` in `layers.json`. Added an opt-in runtime patcher for ALIGN's installed `align/cell_fabric/gen_gds_json.py` so the Python exporter skips `NoGDS` layers and does not unconditionally append `Bbox`.

Why the patch is safe:
The PDK metadata change applies only to non-fabric helper layers. The runtime patcher creates a backup and only changes exporter stream-out behavior for layers explicitly marked `NoGDS`; it does not change placement, routing, transistor geometry, or electrical layers.

After result:
Regenerated inverter with `darpaalign/align-public:latest` after applying the patcher. The Python stream-out GDS no longer contains helper layers:

```text
GDS: generated_runs/inverter_align_nogds_patch/INVERTER_0.python.gds
Used layers include official SkyWater layers and met2 labels/pins only.
No 100:5, 104:0, or 235:5 records were present.
```

Then ran the one-circuit flow without the GDS sanitizer:

```text
Magic loaded INVERTER without unknown-layer errors.
Magic DRC still reported 60 errors.
Magic extraction produced extracted SPICE.
Expanded LVS reached 120 devices and 564 nets on both sides, but netlists still did not match.
```

Remaining problems:
The default non-Python PnR GDS (`INVERTER_0.gds`) still contains `104:0` and `235:5`, apparently from downstream PnR result JSON/GDS writer behavior. For open_pdks verification, use patched `.python.gds` or the sanitizer until that writer path is patched too.

## 14. No-LVT-Marker RVT Compatibility Mode

Issue:
The inverter example uses ALIGN mock-FinFET-era model names `nmos_lvt` and `pmos_lvt` with `L=150e-9`. When streamed with the official Sky130 `lvtn` marker, Magic DRC reports the official `poly.1b` LVT PMOS gate-length rule because `pfet_01v8_lvt` requires a longer channel than the ALIGN inverter supplies.

Source diagnostic:
`reports/before_after/inverter_patched_python_streamout/raw_logs/INVERTER.magic_drc.find_why.txt` classified all remaining DRC feedback as:

```text
LVT PMOS gate length < 0.35um (poly.1b)
```

Files changed:
`SKY130_PDK/layers.json`
`scripts/normalize_netlist.py`
`scripts/run_one_circuit_validation.sh`

Patch made:
Removed `LVT` from `design_info.vt_type`, leaving `["HVT", "RVT"]`, so the ALIGN generator does not place the `lvtn` marker for these mock-FinFET-style `*_lvt` aliases. Added opt-in schematic normalization `--coerce-lvt-to-rvt` so LVS compares the resulting no-marker layout against regular `sky130_fd_pr__nfet_01v8` and `sky130_fd_pr__pfet_01v8` device names.

Why the patch is safe:
This is a narrow compatibility policy for the current ALIGN Sky130 fork: treat legacy `nmos_lvt`/`pmos_lvt` aliases as regular 1.8V devices unless and until the generator can create official LVT-compliant geometry. It does not claim LVT physical correctness.

Before result:
Patched Python stream-out without helper layers imported cleanly into Magic, but DRC reported 60 `poly.1b` LVT PMOS gate-length violations.

After result:
Regenerated inverter:

```text
generated_runs/inverter_align_no_lvt_marker/INVERTER_0.python.gds
```

Magic DRC result:

```text
Total DRC errors found: 0
```

Remaining problems:
This mode intentionally drops LVT semantics for the tested inverter. Official LVT support still requires geometry changes to produce the longer LVT channel or a generator/model policy that refuses invalid LVT requests.

## 15. Magic-Extracted Subckt LVS Dialect

Issue:
After no-LVT-marker generation, Magic extracted each MOS as an `X... sky130_fd_pr__*` subckt-style instance, while the normalized schematic still used SPICE `M... sky130_fd_pr__*` primitive MOS syntax and lower-case top-level pins. Netgen reached equal model classes/device counts but still failed matching.

Source diagnostic:
`reports/before_after/inverter_no_lvt_marker_rvt_full/raw_logs/inverter_vs_INVERTER.netgen_lvs.summary.txt` showed:

```text
Circuit 1 contains 120 devices, Circuit 2 contains 120 devices.
Circuit 1 contains 564 nets,    Circuit 2 contains 564 nets.
```

but the final comparison did not match.

Files changed:
`scripts/normalize_netlist.py`
`scripts/run_one_circuit_validation.sh`

Patch made:
Added opt-in normalizer flags:

- `--mos-as-subckt`: emits expanded schematic MOS instances as `X... model` subckt calls, matching Magic extraction.
- `--uppercase-nets`: uppercases MOS node names and `.subckt` ports, matching Magic's extracted top-pin style.

Why the patch is safe:
These are explicit LVS normalization modes. They do not modify generated GDS, hide DRC/LVS errors, or change ALIGN generation.

After result:
Full one-circuit validation:

```text
reports/before_after/inverter_no_lvt_marker_xsubckt_full/
```

Result:

```text
Total DRC errors found: 0
Circuit 1 contains 120 devices, Circuit 2 contains 120 devices.
Circuit 1 contains 84 nets,    Circuit 2 contains 84 nets.
Final result: Circuits match uniquely.
```

Remaining problems:
The no-LVT-marker policy is experimental. The default PnR GDS writer still emits some helper layers, so the current clean path uses patched Python stream-out or a sanitizer. Larger circuits still need validation.

## 16. Top-Level Label Filtering In ALIGN Python Stream-Out

Issue:
The buffer layout was DRC-clean and topology-equivalent, but Magic extracted the internal net `OUT1` as a top-level port. Netgen reported `Netlists match uniquely with port errors` and failed top-level pin matching.

Source diagnostic:
`reports/before_after/buffer_xsubckt_full/raw_logs/buffer_vs_BUFFER.lvs.report` showed:

```text
X_MN0_MN1_MP0_MP1/VM | (no pin, node is OUT1)
Final result: Top level cell failed pin matching.
```

ALIGN-side file:
Runtime patch target: installed `align/pnr/main.py`.

Files changed:
`scripts/patch_align_gds_export.py`

Patch made:
Extended the runtime patcher to fix ALIGN's top-level `reqLabels` construction:

```python
labels = [i.name for i in hN.blockPins] + [i.name for i in hN.PowerNets]
```

instead of using `list.extend()`, which returns `None` and caused all pin terminals to be labeled. The patcher also prevents `pnr/main.py` from injecting top-level `Outline` when the PDK marks `Outline` as `NoGDS`.

Why the patch is safe:
This changes only Python stream-out labeling/filtering in the patched ALIGN runtime. It does not modify placement, routing, or electrical geometry. It removes internal labels from Magic extraction rather than waiving LVS.

After result:
Regenerated and validated buffer:

```text
GDS: generated_runs/buffer_align_label_patch/BUFFER_0.python.gds
Report: reports/before_after/buffer_label_patch_xsubckt_full/
Magic DRC: Total DRC errors found: 0
Netgen LVS: Final result: Circuits match uniquely.
```

Remaining problems:
The default native PnR GDS path still contains non-Sky130 helper boundary records. The verified path remains patched Python stream-out or sanitized verification GDS.

## 17. Unequal-NF Grouped MOS Unit Counts

Issue:
`current_mirror_ota` was DRC-clean but LVS-failing. Magic extracted 80 PFET devices while the normalized schematic expected 72 PFET devices. NFET counts matched, so the remaining mismatch was a real generated PMOS topology/count problem rather than a model-name, pin-name, or Netgen setup issue.

Source diagnostic:
`reports/before_after/current_mirror_ota_label_patch_xsubckt_full/summary.md` showed:

```text
Total DRC errors found: 0
Circuit 1 contains 192 devices, Circuit 2 contains 184 devices. *** MISMATCH ***
Circuit 1 contains 106 nets,    Circuit 2 contains 102 nets. *** MISMATCH ***
```

`scripts/analyze_mos_array_units.py` identified the two generated PMOS grouped primitives:

```text
SCM_PMOS_85912433_X1_Y5: M1 NF=6, M2 NF=12, stack=2, formula_units=4.5
SCM_PMOS_85912433_X5_Y1: M1 NF=6, M2 NF=12, stack=2, formula_units=4.5
```

ALIGN-side file:
`SKY130_PDK/gen_param.py`
`SKY130_PDK/mos.py`

Patch made:
`gen_param.py` now records explicit per-device `unit_counts` for unequal-NF SCM MOS groups. `mos.py` consumes that map and emits only the requested physical MOS unit count instead of drawing the rounded surplus device cell introduced by ALIGN's two-device primitive `x_cells` doubling. The helper `scripts/analyze_mos_array_units.py` now reports corrected explicit-unit cases as notes and still fails when an unequal fractional group has no explicit unit-count metadata.

Why the patch is safe:
This is a targeted generator-topology change for grouped MOS primitives whose source devices have unequal `NF*M`. Equal-NF groups continue down the prior path. The patch removes physically generated surplus PFETs; it does not hide LVS errors or alter Netgen output.

After result:
Regenerated and validated current-mirror OTA:

```text
GDS: generated_runs/current_mirror_ota_unit_counts/CURRENT_MIRROR_OTA_0.python.gds
Report: reports/before_after/current_mirror_ota_unit_counts_xsubckt_full/
Magic DRC: Total DRC errors found: 0
Netgen LVS: Final result: Circuits match uniquely.
```

Device and net counts after the patch:

```text
Circuit 1 contains 184 devices, Circuit 2 contains 184 devices.
Circuit 1 contains 102 nets,    Circuit 2 contains 102 nets.
```

Remaining problems:
This validates the 6/12 PMOS grouped-current-mirror case and leaves more complex ratioed devices, true LVT/HVT geometry, capacitors, resistors, and default native GDS stream-out as separate targets.
