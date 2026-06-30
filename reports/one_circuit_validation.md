# One-Circuit Validation

Date: 2026-06-18

Status: `diagnostic_only`

## Selected Circuit

Target: inverter

| Item | Value |
|---|---|
| Schematic SPICE | `examples/inverter/inverter.sp` |
| Top cell | `inverter` |
| Generated GDS | Not found |
| open_pdks `sky130A` path | Not found |
| Magic executable | Not found |
| Netgen executable | Not found |

## Why Inverter

The inverter is the smallest local circuit and has simple MOS instances:

```spice
mn0 out in vss vss nmos_lvt w=10.5e-7 L=150e-9 nf=20 stack=3
mp0 out in vdd vdd pmos_lvt w=10.5e-7 L=150e-9 nf=20 stack=3
```

The model aliases can be normalized to official Sky130 names. The ALIGN-only `stack` parameter can be dropped explicitly for an LVS dialect experiment using `--drop-param stack`.

## Prepared Command

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root "$OPEN_PDKS_SKY130A" \
  --gds "$LAYOUT_GDS" \
  --schematic examples/inverter/inverter.sp \
  --top inverter \
  --out-dir reports/before_after/inverter \
  --drop-param stack
```

Expected output structure:

```text
reports/before_after/inverter/
  summary.md
  commands.sh
  raw_logs/
  normalized/
  extracted/
  magic_work/
```

## Static Normalization Evidence

Command run:

```sh
python3 scripts/normalize_netlist.py examples/inverter/inverter.sp --drop-param stack -o /tmp/inverter.normalized.sp
```

Observed normalized MOS lines after the experimental LVT-aware mapping:

```spice
mn0 out in vss vss sky130_fd_pr__nfet_01v8_lvt w=10.5e-7 L=150e-9 nf=20
mp0 out in vdd vdd sky130_fd_pr__pfet_01v8_lvt w=10.5e-7 L=150e-9 nf=20
```

This is an opt-in LVS dialect normalization, not a claim that LVS will pass.

## Runtime Result

Initial static pass had no Magic/Netgen run because required runtime inputs were missing:

- generated inverter GDS,
- open_pdks `sky130A` install,
- Magic executable,
- Netgen executable.

## Tuple Runtime Result

Status: `diagnostic_only`

Tuple used:

- GDS: `artifacts/inverter_tuple/inverter/generated/inverter.gds`
- Schematic: `artifacts/inverter_tuple/inverter/input/inverter.sp`
- Layout top: `INVERTER_0`
- Schematic top: `inverter`
- open_pdks path inside Docker: `/foss/pdks/sky130A`
- Magic/Netgen image: `hpretl/iic-osic-tools:latest`
- ALIGN image found later: `darpaalign/align-public:latest`

The wrapper now sanitizes a verification copy of the GDS, dropping `100:5`, `104:0`, and `235:5` helper layers. It keeps `69:5` because SkyWater documents it as `met2,label`.

Results:

- Magic DRC loaded the real `INVERTER_0` top and reported `60` DRC errors.
- Magic extraction produced `reports/before_after/inverter_nopex/extracted/INVERTER_0.extracted.spice`.
- LVS with normal model/parameter normalization failed with `120` extracted MOS devices versus `2` schematic MOS devices.
- LVS with `--expand-nf-stack --scale-wl-to-um` matched device and net counts at `120` devices and `564` nets on both sides, but still failed top-level pin/net matching.

Best current command:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root "$OPEN_PDKS_SKY130A" \
  --gds "$LAYOUT_GDS" \
  --layout-top INVERTER_0 \
  --schematic "$SCHEMATIC_SPICE" \
  --schematic-top inverter \
  --out-dir reports/before_after/inverter_expanded \
  --expand-nf-stack \
  --scale-wl-to-um
```

Interpretation:
The dominant LVS mismatch is no longer model naming. It is the inherited mock-FinFET MOS abstraction: ALIGN encodes physical multiplicity as `nf/stack`, while Magic extracts every planar poly/diff crossing as an individual device. Expansion confirms the count mismatch, and remaining failures point to pin/connectivity semantics.

## Patched Python Stream-Out Result

Status: `diagnostic_only`

The ALIGN runtime was patched inside `darpaalign/align-public:latest` with:

```sh
python3 scripts/patch_align_gds_export.py
```

and `SKY130_PDK/layers.json` now marks helper layers `Bbox`, `Boundary`, `Rboundary`, `Cboundary`, and `Outline` as `NoGDS`.

Regenerated artifact:

- `generated_runs/inverter_align_nogds_patch/INVERTER_0.python.gds`
- Layout top in that GDS: `INVERTER`

Layer inspection with KLayout Python showed no `100:5`, `104:0`, or `235:5` records in the patched Python stream-out. The default PnR GDS still has `104:0` and `235:5`, so use `.python.gds` or the sanitizer until the downstream writer is patched.

No-sanitizer validation command:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root /foss/pdks/sky130A \
  --gds generated_runs/inverter_align_nogds_patch/INVERTER_0.python.gds \
  --layout-top INVERTER \
  --schematic artifacts/inverter_tuple/inverter/input/inverter.sp \
  --schematic-top inverter \
  --out-dir reports/before_after/inverter_patched_python_streamout \
  --no-sanitize-gds \
  --expand-nf-stack \
  --scale-wl-to-um
```

Results:

- Magic import had no unknown helper-layer errors.
- Magic DRC still reported `60` errors.
- Magic extraction produced `reports/before_after/inverter_patched_python_streamout/extracted/INVERTER.extracted.spice`.
- Netgen LVS still failed, but reached `120` devices and `564` nets on both sides.

## DRC-Clean / LVS-Clean Inverter Result

Status: `drc_clean`, `lvs_clean` for this bounded inverter experiment.

The 60 DRC errors in the patched Python stream-out run were all classified as official Sky130 LVT PMOS gate-length violations. The current compatibility path suppresses LVT marker generation for legacy ALIGN `*_lvt` aliases and compares the schematic as regular 1.8V devices.

Full command used inside `hpretl/iic-osic-tools:latest`:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root /foss/pdks/sky130A \
  --gds generated_runs/inverter_align_no_lvt_marker/INVERTER_0.python.gds \
  --layout-top INVERTER \
  --schematic artifacts/inverter_tuple/inverter/input/inverter.sp \
  --schematic-top inverter \
  --out-dir reports/before_after/inverter_no_lvt_marker_xsubckt_full \
  --no-sanitize-gds \
  --expand-nf-stack \
  --scale-wl-to-um \
  --coerce-lvt-to-rvt \
  --mos-as-subckt \
  --uppercase-nets
```

Results:

```text
Total DRC errors found: 0
Circuit 1 contains 120 devices, Circuit 2 contains 120 devices.
Circuit 1 contains 84 nets,    Circuit 2 contains 84 nets.
Final result: Circuits match uniquely.
```

Evidence directory:

```text
reports/before_after/inverter_no_lvt_marker_xsubckt_full/
```

Interpretation:
The tested inverter is now clean through `GDS -> Magic DRC -> Magic extraction -> extracted SPICE -> Netgen LVS` when using patched Python stream-out and explicit RVT/subckt schematic normalization. This does not validate official LVT geometry, other devices, capacitors, resistors, or larger circuits.

## Buffer Validation After Label Patch

Status: `drc_clean`, `lvs_clean` for a second MOS-only circuit.

The buffer initially reached DRC clean and topology-equivalent LVS, but failed top-level pin matching because an internal node was labeled as a Magic top-level port. Extending `scripts/patch_align_gds_export.py` to patch ALIGN `pnr/main.py` fixed the label filter bug.

Full command used inside `hpretl/iic-osic-tools:latest`:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root /foss/pdks/sky130A \
  --gds generated_runs/buffer_align_label_patch/BUFFER_0.python.gds \
  --layout-top BUFFER \
  --schematic examples/buffer/buffer.sp \
  --schematic-top buffer \
  --out-dir reports/before_after/buffer_label_patch_xsubckt_full \
  --no-sanitize-gds \
  --expand-nf-stack \
  --scale-wl-to-um \
  --mos-as-subckt \
  --uppercase-nets
```

Results:

```text
Total DRC errors found: 0
Circuit 1 contains 4 devices, Circuit 2 contains 4 devices.
Circuit 1 contains 5 nets,    Circuit 2 contains 5 nets.
Final result: Circuits match uniquely.
```

Evidence directory:

```text
reports/before_after/buffer_label_patch_xsubckt_full/
```

Interpretation:
The compatibility flow now has two clean MOS-only examples: inverter under the explicit RVT compatibility policy and buffer under regular RVT aliases. The buffer result validates the top-level-label patch independently of the LVT marker policy.

## Five-Transistor OTA Validation

Status: `drc_clean`, `lvs_clean` for a modest MOS-only analog block.

Full command used inside `hpretl/iic-osic-tools:latest`:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root /foss/pdks/sky130A \
  --gds generated_runs/five_transistor_ota_label_patch/FIVE_TRANSISTOR_OTA_0.python.gds \
  --layout-top FIVE_TRANSISTOR_OTA \
  --schematic examples/five_transistor_ota/five_transistor_ota.sp \
  --schematic-top five_transistor_ota \
  --out-dir reports/before_after/five_transistor_ota_label_patch_xsubckt_full \
  --no-sanitize-gds \
  --expand-nf-stack \
  --scale-wl-to-um \
  --mos-as-subckt \
  --uppercase-nets
```

Results:

```text
Total DRC errors found: 0
Circuit 1 contains 300 devices, Circuit 2 contains 300 devices.
Circuit 1 contains 208 nets,    Circuit 2 contains 208 nets.
Final result: Circuits match uniquely.
```

Evidence directory:

```text
reports/before_after/five_transistor_ota_label_patch_xsubckt_full/
```

Interpretation:
This extends the clean flow beyond toy inverter/buffer cases to a small analog block. It still covers only MOS-only regular 1.8V devices; capacitor, resistor, HVT/LVT, and larger OTA/current mirror behavior remain separate validation targets.

## Current-Mirror OTA Validation

Status: `drc_clean`, `lvs_mismatch`.

Full command used inside `hpretl/iic-osic-tools:latest`:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root /foss/pdks/sky130A \
  --gds generated_runs/current_mirror_ota_label_patch/CURRENT_MIRROR_OTA_0.python.gds \
  --layout-top CURRENT_MIRROR_OTA \
  --schematic examples/current_mirror_ota/current_mirror_ota.sp \
  --schematic-top current_mirror_ota \
  --out-dir reports/before_after/current_mirror_ota_label_patch_xsubckt_full \
  --no-sanitize-gds \
  --expand-nf-stack \
  --scale-wl-to-um \
  --mos-as-subckt \
  --uppercase-nets
```

Results:

```text
Total DRC errors found: 0
Circuit 1 contains 192 devices, Circuit 2 contains 184 devices. *** MISMATCH ***
Circuit 1 contains 106 nets,    Circuit 2 contains 102 nets. *** MISMATCH ***
sky130_fd_pr__pfet_01v8 (80) | sky130_fd_pr__pfet_01v8 (72) **Mismatch**
Final result: Netlists do not match.
```

Evidence directory:

```text
reports/before_after/current_mirror_ota_label_patch_xsubckt_full/
```

Interpretation:
The same patched stream-out and LVS normalization path gets this larger current-mirror OTA to a clean Magic DRC run, but LVS exposes a real PFET count mismatch. `scripts/analyze_mos_array_units.py` flags the two generated PMOS grouped primitives as `fractional_unit_rounding,unequal_nf_group,high_lvs_count_risk`: the source PMOS mirror pair has `NF=6` and `NF=12` with `stack=2`, while the current generator rounds a `4.5` unit-cell calculation up to `5`. This is now the highest-priority device-generation mismatch; it should not be papered over in Netgen.

## Current-Mirror OTA Validation After Unit-Count Rewrite

Status: `drc_clean`, `lvs_clean`.

Full command used inside `hpretl/iic-osic-tools:latest`:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root /foss/pdks/sky130A \
  --gds generated_runs/current_mirror_ota_unit_counts/CURRENT_MIRROR_OTA_0.python.gds \
  --layout-top CURRENT_MIRROR_OTA \
  --schematic examples/current_mirror_ota/current_mirror_ota.sp \
  --schematic-top current_mirror_ota \
  --out-dir reports/before_after/current_mirror_ota_unit_counts_xsubckt_full \
  --no-sanitize-gds \
  --expand-nf-stack \
  --scale-wl-to-um \
  --mos-as-subckt \
  --uppercase-nets
```

Results:

```text
Total DRC errors found: 0
Circuit 1 contains 184 devices, Circuit 2 contains 184 devices.
Circuit 1 contains 102 nets,    Circuit 2 contains 102 nets.
Final result: Circuits match uniquely.
```

Evidence directory:

```text
reports/before_after/current_mirror_ota_unit_counts_xsubckt_full/
```

Interpretation:
The grouped-MOS unit-count rewrite fixed the +8 PFET over-generation without LVS filtering. The new generated PMOS primitives carry explicit `unit_counts` metadata, and `scripts/analyze_mos_array_units.py` reports `risk_count: 0` for the regenerated current-mirror OTA.

## Telescopic OTA Validation

Status: `drc_clean`, `lvs_clean`.

Full command used inside `hpretl/iic-osic-tools:latest`:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root /foss/pdks/sky130A \
  --gds generated_runs/telescopic_ota_unit_counts/TELESCOPIC_OTA_0.python.gds \
  --layout-top TELESCOPIC_OTA \
  --schematic examples/telescopic_ota/telescopic_ota.sp \
  --schematic-top telescopic_ota \
  --out-dir reports/before_after/telescopic_ota_unit_counts_xsubckt_full \
  --no-sanitize-gds \
  --expand-nf-stack \
  --scale-wl-to-um \
  --coerce-lvt-to-rvt \
  --mos-as-subckt \
  --uppercase-nets
```

Results:

```text
Total DRC errors found: 0
Circuit 1 contains 10 devices, Circuit 2 contains 10 devices.
Circuit 1 contains 15 nets,    Circuit 2 contains 15 nets.
Final result: Circuits match uniquely.
```

Evidence directory:

```text
reports/before_after/telescopic_ota_unit_counts_xsubckt_full/
```

Interpretation:
This is another MOS-only analog block validated after the grouped-MOS unit-count rewrite. It uses legacy `nmos_lvt`/`pmos_lvt` aliases, so the clean result depends on the documented RVT compatibility policy (`--coerce-lvt-to-rvt`) and is not true official LVT support.
