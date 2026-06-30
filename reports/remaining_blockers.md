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

reports/before_after/buffer_direct_binding_patch_xsubckt_full/
Magic DRC: Total DRC errors found: 0
Netgen LVS: Final result: Circuits match uniquely.
```

The inverter result depends on the experimental no-LVT-marker RVT compatibility policy and schematic subckt normalization. The buffer and five-transistor OTA results use regular 1.8V model aliases. The `buffer_direct_binding_patch` result additionally validates that a normal `schematic2layout.py -p SKY130_PDK ...` run can produce a default `BUFFER_0.gds` that Magic imports without helper-layer errors.

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
| MOS generator is still mock-FinFET-derived | Inverter schematic has 2 MOS with `nf=20 stack=3`; Magic extracts 120 MOS devices. | Redesign MOS schematic/generator contract for planar Sky130, or make LVS netlists physically expanded before comparison. |
| Default GDS stream-out is only validated through the PDK import hook | `generated_runs/buffer_direct_binding_patch/BUFFER_0.gds` is clean, but earlier default-GDS attempts before refreshing `align.main.generate_pnr` still emitted helper layers. | Keep this behavior in `SKY130_PDK/align_compat.py`; long-term, move equivalent fixes into the ALIGN fork rather than relying on runtime source patching. |
| Official LVT support is not solved | The clean inverter path suppresses LVT marker generation and coerces schematic aliases to RVT. | Either generate official-compliant LVT geometry or reject/remap invalid LVT requests intentionally. |
| Larger/mixed-device circuits are unvalidated | Inverter, buffer, five-transistor OTA, current-mirror OTA, and telescopic OTA have clean Magic/Netgen runs under stated compatibility policies; MIM caps, resistors, HVT, and true LVT are not validated. | Repeat the same flow on the next small mixed-device circuit before changing broad rules. |
| MOS generator is still mock-FinFET-derived | Inverter schematic has 2 MOS with `nf=20 stack=3`; Magic extracts 120 MOS devices. | Keep LVS physical expansion for verification or redesign the schematic/generator contract for planar Sky130. |
| Broader ratioed grouped MOS coverage is still limited | The specific `current_mirror_ota` 6/12 PMOS grouped case is now clean after explicit `unit_counts`, but other unequal-ratio grouped devices have not been swept. | Use `scripts/analyze_mos_array_units.py` on each new generated run and validate representative ratioed NMOS/PMOS groups. |

## Current Practical Verification Path

For a regular MOS-only direct run, generate normally and validate the default GDS:

```sh
schematic2layout.py -p SKY130_PDK \
  -w generated_runs/buffer_direct_binding_patch \
  -s buffer -n 1 -e 0 \
  --router_mode top_down --router astar --placer python \
  generated_runs/buffer_input_direct_binding_patch

scripts/run_one_circuit_validation.sh \
  --open-pdks-root /foss/pdks/sky130A \
  --gds generated_runs/buffer_direct_binding_patch/BUFFER_0.gds \
  --layout-top BUFFER \
  --schematic examples/buffer/buffer.sp \
  --schematic-top buffer \
  --out-dir reports/before_after/buffer_direct_binding_patch_xsubckt_full \
  --no-sanitize-gds \
  --expand-nf-stack \
  --scale-wl-to-um \
  --mos-as-subckt \
  --uppercase-nets
```

For legacy LVT-alias examples, add `--coerce-lvt-to-rvt` until true LVT-compliant geometry is implemented. LVS normalization is still required because ALIGN source schematics and Magic extracted SPICE use different MOS netlist dialects.
