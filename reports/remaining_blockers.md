# Remaining Blockers

Date: 2026-06-18

## Hard Runtime Blockers

| Blocker | Impact | Next action |
|---|---|---|
| No generated ALIGN Sky130 GDS found | Cannot run Magic DRC/import/extraction | Provide or generate one small GDS, preferably inverter. |
| No open_pdks `sky130A` install path found | No runtime `sky130A.tech`, Magic rc, or Netgen setup | Install or point to open_pdks `sky130A`; then run `scripts/check_verification_refs.py --open-pdks-root`. |
| `magic` not found on PATH | Cannot run DRC/extraction | Install Magic or activate environment containing Magic. |
| `netgen` not found on PATH | Cannot run LVS | Install Netgen or activate environment containing Netgen. |
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
| Helper layers still stream from generated GDS | Regenerated inverter still emits `100:5`, `104:0`, `235:5`; Magic rejects them. Removing GDS mapping from `Bbox` breaks ALIGN `gen_gds_json.py`. | Patch or vendor ALIGN GDS exporter to suppress helper layers, or keep sanitizer as bridge. |
| MOS generator is still mock-FinFET-derived | Inverter schematic has 2 MOS with `nf=20 stack=3`; Magic extracts 120 MOS devices. | Redesign MOS schematic/generator contract for planar Sky130, or make LVS netlists physically expanded before comparison. |
| Top-level pins are not LVS-clean | Expanded LVS matched 120 devices and 564 nets on both sides but failed pin/net matching. | Fix pin label/export/extraction semantics and net naming/case policy. |
| DRC remains nonzero | Magic reports 60 DRC errors on sanitized inverter GDS. | Obtain/classify detailed DRC feedback; then patch actual geometry/rules, not waivers. |
