# Remaining Blockers

Date: 2026-06-18

## Resolved Runtime Blockers For Inverter Tuple

The tuple plus Docker images removed the original hard runtime blockers for one inverter:

- generated GDS available under `artifacts/` and regenerated under `generated_runs/`,
- Magic/Netgen/open_pdks available in `hpretl/iic-osic-tools:latest`,
- ALIGN generation available in `darpaalign/align-public:latest`.

Current bounded best results:

```text
reports/before_after/inverter_no_lvt_marker_xsubckt_full/
Magic DRC: Total DRC errors found: 0
Netgen LVS: Final result: Circuits match uniquely.

reports/before_after/buffer_label_patch_xsubckt_full/
Magic DRC: Total DRC errors found: 0
Netgen LVS: Final result: Circuits match uniquely.

reports/before_after/five_transistor_ota_label_patch_xsubckt_full/
Magic DRC: Total DRC errors found: 0
Netgen LVS: Final result: Circuits match uniquely.
```

The inverter result depends on the experimental no-LVT-marker RVT compatibility policy and schematic subckt normalization. The buffer and five-transistor OTA results use regular 1.8V model aliases and additionally validate the top-level-label patch in the ALIGN runtime patcher.

## Remaining Runtime Blockers Outside Docker / Outside Inverter

| Blocker | Impact | Next action |
|---|---|---|
| No host open_pdks `sky130A` install path found | Host cannot run without Docker | Use `/foss/pdks/sky130A` inside `hpretl/iic-osic-tools:latest`, or install/point host to open_pdks. |
| `magic` not found on host PATH | Host cannot run DRC/extraction directly | Use Docker image or install Magic on host. |
| `netgen` not found on host PATH | Host cannot run LVS directly | Use Docker image or install Netgen on host. |
| Host `schematic2layout.py` not found on PATH | Host cannot generate new ALIGN layout directly | Use local Docker image `darpaalign/align-public:latest` or install ALIGN locally. |

## Compatibility Questions Waiting For Evidence

| Question | Why evidence is needed |
|---|---|
| Does `Fin` stream into GDS and trigger Magic unknown-layer or extraction issues? | The generator uses `Fin`; removing it without GDS evidence risks changing layout semantics. |
| Do Magic pin labels land on recognized Sky130 pin/text layers? | LVS pin mismatches depend on generated GDS labels and Magic extraction behavior. |
| Does Netgen require dropping/renaming parameters beyond `stack`? | Extracted SPICE is needed to see property names and values. |
| Does Magic extraction preserve LVT/HVT model names from marker layers? | The normalizer now preserves official LVT/HVT names, but extracted model naming depends on real Magic extraction. |
| Do ALIGN MIM capacitor layouts extract as official `cap_mim` models? | Official parser stubs were added, but capacitor geometry/model equivalence requires a generated cap layout and LVS. |
| Are reported via-width issues real cut-size violations or enclosure-footprint confusion? | SkyWater docs suggest the diagnostic report mixes cut width and enclosure for several vias. Magic DRC evidence is required. |
| Are metal width differences harmful or just conservative routing choices? | DRC may pass despite conservative widths; changing widths would alter layout generation/QoR. |

## Risky Changes Deferred

- Broad layer renaming from ALIGN abstract names to official SkyWater names.
- Via width edits from the diagnostic report.
- Metal width/pitch changes.
- Removing or remapping `Fin`.
- Adding full density/antenna/device-specific signoff rules into `layers.json`.
- Filtering or waiving DRC/LVS output.

## Updated Blockers From Inverter Tuple

| Blocker | Evidence | Next action |
|---|---|---|
| Helper layers still stream from default PnR GDS | The patched Python stream-out path now removes helper layers, but default `INVERTER_0.gds` still emits `104:0` and `235:5` from downstream PnR result writing. | Use patched `.python.gds` or sanitizer for verification; next patch target is the downstream PnR GDS writer. |
| MOS generator is still mock-FinFET-derived | Inverter schematic has 2 MOS with `nf=20 stack=3`; Magic extracts 120 MOS devices. | Redesign MOS schematic/generator contract for planar Sky130, or make LVS netlists physically expanded before comparison. |
| Default/native PnR GDS writer still emits helper boundary records | The patched Python stream-out path removes helper layers, but default native `*.gds` still emits non-Sky130 boundary records such as `235:5`. | Patch downstream native GDS writer or keep using `.python.gds`/sanitizer for verification. |
| Official LVT support is not solved | The clean inverter path suppresses LVT marker generation and coerces schematic aliases to RVT. | Either generate official-compliant LVT geometry or reject/remap invalid LVT requests intentionally. |
| Larger/mixed-device circuits are unvalidated | Inverter, buffer, and five-transistor OTA have clean Magic/Netgen runs; current mirror OTA, telescopic OTA, MIM caps, resistors, HVT, and true LVT are not validated. | Repeat the same flow on the next small or mixed-device circuit before changing broad rules. |
| MOS generator is still mock-FinFET-derived | Inverter schematic has 2 MOS with `nf=20 stack=3`; Magic extracts 120 MOS devices. | Keep LVS physical expansion for verification or redesign the schematic/generator contract for planar Sky130. |
| Broader ratioed grouped MOS coverage is still limited | The specific `current_mirror_ota` 6/12 PMOS grouped case is now clean after explicit `unit_counts`, but other unequal-ratio grouped devices have not been swept. | Use `scripts/analyze_mos_array_units.py` on each new generated run and validate representative ratioed NMOS/PMOS groups. |

## Current Practical Verification Path

Use `scripts/patch_align_gds_export.py` inside the ALIGN runtime before generation, generate `.python.gds`, then verify with:

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

For regular RVT MOS-only examples such as buffer, omit `--coerce-lvt-to-rvt` and use the same `--mos-as-subckt --uppercase-nets --expand-nf-stack --scale-wl-to-um` LVS normalization. The Python stream-out patch is still required to avoid internal labels becoming top-level Magic pins.
