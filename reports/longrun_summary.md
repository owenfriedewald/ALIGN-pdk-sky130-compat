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
- Added `SKY130_PDK/openpdks_compat.json` as experimental compatibility metadata for layer maps, special layer notes, model aliases, and LVS parameter policy
- Added official LVT/HVT and MIM capacitor model stubs to `SKY130_PDK/models.sp`
- Updated model alias normalization to preserve LVT/HVT intent where official SkyWater names exist
- Added SPICE and GDS inspection helpers: `scripts/inspect_spice.py`, `scripts/inspect_gds_layers.py`
- Added validation input discovery helper: `scripts/discover_validation_inputs.py`
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

## Tuple Update

After `inverter_tuple.tar.gz` was provided, the local images were:

- `darpaalign/align-public:latest`: ALIGN available, including `schematic2layout.py`.
- `hpretl/iic-osic-tools:latest`: Magic, Netgen, KLayout Python, and open_pdks `/foss/pdks/sky130A` available.

Real inverter validation is now possible and was run. The current branch is no longer only verification prep:

- Corrected `Hvt` from non-SkyWater `970:0` to official `hvtp 78:44`.
- Added GDS sanitizer for helper layers rejected by Magic.
- Added no-PEX default extraction for LVS, with `--pex` opt-in.
- Added explicit `nf/stack` schematic expansion. This changed inverter LVS from raw device-count mismatch to matching `120` devices and `564` nets on both sides, with remaining pin/net mismatch.
- Regenerated inverter with `darpaalign/align-public:latest`; helper layers still stream, proving this needs an ALIGN exporter patch or sanitizer bridge.

## Generation-Time Helper Layer Update

After adding `scripts/patch_align_gds_export.py` and marking helper layers as `NoGDS` in `SKY130_PDK/layers.json`, the patched ALIGN Python stream-out path generated:

- `generated_runs/inverter_align_nogds_patch/INVERTER_0.python.gds`

Layer inspection showed this Python GDS no longer includes `100:5`, `104:0`, or `235:5`. Running the one-circuit flow on this file with `--no-sanitize-gds` succeeded through Magic import, DRC, extraction, and Netgen invocation:

- Magic import: no unknown helper-layer errors.
- Magic DRC: still 60 errors.
- Magic extraction: extracted SPICE produced.
- Netgen LVS with `--expand-nf-stack --scale-wl-to-um`: 120 devices and 564 nets on both sides, but LVS still failed due to pin/net matching.

The default PnR GDS (`INVERTER_0.gds`) still emits `104:0` and `235:5`, so the patched Python stream-out or sanitizer remains the practical verification path for now.

## Branch Risk

This branch is safe to keep as an experimental compatibility branch. It now has real one-circuit Magic/Netgen evidence, including one bounded `drc_clean` and `lvs_clean` inverter result under an explicit RVT compatibility policy.

## No-LVT-Marker / Subckt LVS Update

The earlier 60-error inverter DRC result was traced to official Sky130 LVT rules, not a generic poly-width issue:

```text
LVT PMOS gate length < 0.35um (poly.1b)
```

Because the current ALIGN Sky130 inverter is inherited from a mock-FinFET abstraction and asks for `pmos_lvt` at `L=150e-9`, the branch now treats legacy `*_lvt` aliases as regular 1.8V devices for this compatibility path:

- `SKY130_PDK/layers.json` no longer lists `LVT` in `design_info.vt_type`, preventing `lvtn` marker generation.
- `scripts/normalize_netlist.py --coerce-lvt-to-rvt` maps schematic `nmos_lvt`/`pmos_lvt` aliases to regular RVT Sky130 devices for LVS.
- `--mos-as-subckt --uppercase-nets` normalizes the schematic to Magic's extracted SPICE dialect.

Current best evidence:

- GDS: `generated_runs/inverter_align_no_lvt_marker/INVERTER_0.python.gds`
- Report: `reports/before_after/inverter_no_lvt_marker_xsubckt_full/`
- Magic DRC: `Total DRC errors found: 0`
- Netgen LVS: `Final result: Circuits match uniquely.`

This is not a claim that official Sky130 LVT support is solved. It is a practical compatibility mode for current ALIGN Sky130 aliases and generated geometry.

## Buffer Clean Run And Label Patch

A second MOS-only circuit was generated and validated:

- Source: `examples/buffer/buffer.sp`
- GDS: `generated_runs/buffer_align_label_patch/BUFFER_0.python.gds`
- Report: `reports/before_after/buffer_label_patch_xsubckt_full/`
- Magic DRC: `Total DRC errors found: 0`
- Netgen LVS: `Final result: Circuits match uniquely.`

The first buffer run before the label patch was DRC-clean but LVS failed top-level port matching because the Python stream-out emitted an internal node label as a top-level Magic port. Root cause was in ALIGN `pnr/main.py`:

```python
labels = [i.name for i in hN.blockPins].extend([i.name for i in hN.PowerNets])
```

`list.extend()` returns `None`, so the GDS translator did not receive the intended top-level label allow-list. `scripts/patch_align_gds_export.py` now patches this to list concatenation and also skips `Outline` injection when the PDK marks it `NoGDS`.

## Five-Transistor OTA Clean Run

The same patched Python stream-out and LVS normalization flow was applied to `examples/five_transistor_ota/five_transistor_ota.sp`:

- GDS: `generated_runs/five_transistor_ota_label_patch/FIVE_TRANSISTOR_OTA_0.python.gds`
- Report: `reports/before_after/five_transistor_ota_label_patch_xsubckt_full/`
- Magic DRC: `Total DRC errors found: 0`
- Netgen LVS: `Final result: Circuits match uniquely.`
- LVS scale: 300 device instances and 208 nets on both sides before matching.

This is the first clean modest analog block in the branch. It uses regular `sky130_fd_pr__nfet_01v8` and `sky130_fd_pr__pfet_01v8` models and does not depend on the LVT-to-RVT compatibility policy.

## Current-Mirror OTA DRC-Clean / LVS-Failing Run

The next larger MOS-only circuit, `examples/current_mirror_ota/current_mirror_ota.sp`, was generated and run through the same patched stream-out and normalization flow:

- GDS: `generated_runs/current_mirror_ota_label_patch/CURRENT_MIRROR_OTA_0.python.gds`
- Report: `reports/before_after/current_mirror_ota_label_patch_xsubckt_full/`
- Magic DRC: `Total DRC errors found: 0`
- Netgen LVS: `Final result: Netlists do not match.`
- Mismatch: layout has 192 devices and 106 nets; normalized schematic has 184 devices and 102 nets.
- Device class mismatch: layout extracts 80 PFETs; normalized schematic expects 72 PFETs. NFET count matches.

The mismatch is now tied to generated PMOS grouped primitives with unequal finger counts:

```text
SCM_PMOS_85912433_X1_Y5: M1 NF=6, M2 NF=12, stack=2, formula_units=4.5, emitted unit_cells=5
SCM_PMOS_85912433_X5_Y1: M1 NF=6, M2 NF=12, stack=2, formula_units=4.5, emitted unit_cells=5
```

This is useful negative evidence. The next real PDK/device rewrite target is the grouped MOS array sizing logic, not Magic/Netgen setup.

## Current-Mirror OTA Clean After Grouped-MOS Rewrite

`SKY130_PDK/gen_param.py` and `SKY130_PDK/mos.py` now carry explicit per-device unit counts for unequal-NF grouped MOS primitives. Regenerating `current_mirror_ota` after that rewrite produced:

- GDS: `generated_runs/current_mirror_ota_unit_counts/CURRENT_MIRROR_OTA_0.python.gds`
- Report: `reports/before_after/current_mirror_ota_unit_counts_xsubckt_full/`
- Magic DRC: `Total DRC errors found: 0`
- Netgen LVS: `Final result: Circuits match uniquely.`
- Counts: 184 devices and 102 nets on both sides.

This resolves the first larger ratioed-current-mirror LVS blocker with a real PDK/generator change. It does not validate all ratioed devices, native/default GDS stream-out, true LVT/HVT geometry, capacitors, or resistors.

## Telescopic OTA Clean Run

After the grouped-MOS rewrite, `examples/telescopic_ota/telescopic_ota.sp` was generated and validated:

- GDS: `generated_runs/telescopic_ota_unit_counts/TELESCOPIC_OTA_0.python.gds`
- Report: `reports/before_after/telescopic_ota_unit_counts_xsubckt_full/`
- Magic DRC: `Total DRC errors found: 0`
- Netgen LVS: `Final result: Circuits match uniquely.`
- Counts after Netgen parallel/series merging: 10 devices and 15 nets on both sides.

The telescopic source uses legacy `nmos_lvt`/`pmos_lvt` names, so this result depends on the experimental RVT compatibility policy and does not prove true LVT-compliant geometry.
