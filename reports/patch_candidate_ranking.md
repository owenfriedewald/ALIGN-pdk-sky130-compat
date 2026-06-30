# Patch Candidate Ranking

Date: 2026-06-18

No medium/high-risk patches were applied. Rankings below separate verification-only preparation from generator/PDK semantic changes.

| Rank | Candidate fix | Confidence | Expected impact | Risk | Runtime GDS required? | Changes generation or only verification? | Fair for baseline ALIGN and AnalogDSL? | Action |
|---:|---|---|---|---|---|---|---|---|
| 1 | Keep and use `scripts/check_verification_refs.py` preflight | High | High: immediately identifies missing Magic/Netgen files before a validation run | Low | No | Verification only | Yes | Already added |
| 2 | Keep and use `scripts/compare_layer_map.py` before any layer patch | High | High: prevents incorrect GDS remaps based on base-layer-only conflicts | Low | No | Verification only | Yes | Already added |
| 3 | Use `scripts/normalize_netlist.py` as optional LVS schematic input | Medium-high | Medium: removes simple model alias mismatch from first LVS experiment | Low | No for preparation; yes for proving LVS impact | Verification wrapper only | Yes, if applied equally to baseline and AnalogDSL schematics | Already added |
| 4 | Use `scripts/compare_model_names.py` to inventory model aliases and parameters | High | Medium: makes model-name and parameter dialect visible before LVS | Low | No | Verification only | Yes | Already added |
| 5 | Add thin `run_magic_drc.sh` / `run_netgen_lvs.sh` wrappers around checklist commands | High | Medium: reduces command transcription errors | Low; wrappers require explicit paths and preserve raw logs | No to write; yes to validate | Verification only | Yes | Added |
| 6 | Add LVS/DRC report summarizer scripts | High | Medium: helps classify mismatch classes repeatedly | Low | No; fixture logs added | Verification only | Yes | Added |
| 7 | Document ALIGN abstract routing names as `M1=li1`, `M2=met1`, etc. | High | High: avoids repeating the report's layer-offset ambiguity | Low | No | Documentation only | Yes | Done in reports; consider README addition after review |
| 8 | Treat `Fin` as an export artifact only if it appears in generated GDS | Medium | Medium: could remove unknown-layer warnings | High without GDS | Yes | Could change generation/export | Yes only if applied to all outputs | Unsafe now |
| 9 | Patch `Hvt` GDS number `970:0` | Low-medium | Unknown: may affect HVT marker recognition | Medium/high | Yes | Generation/export | Yes only after evidence | Investigate after generated GDS and official marker reference |
| 10 | Change via widths from diagnostic report recommendations | Low | Potentially high if report were correct, but current docs suggest recommendations mix cut size and enclosure | High | Yes | Generation geometry | Yes only after evidence | Do not apply now |
| 11 | Reduce metal widths to official minimums | Medium for numeric mismatch, low for safety | Could improve density/QoR but changes router behavior | High | Yes | Generation geometry | Fair only if applied globally, but invalidates baseline comparison continuity | Defer |
| 12 | Add missing full signoff spacing/area/density/antenna rules to `layers.json` | Low as a direct patch | Unknown; ALIGN may not consume fields consistently | High | Yes | Generation/rule semantics | Maybe, but large rewrite risk | Defer |
| 13 | Rename ALIGN layers from abstract names to official SkyWater names | Low | Could reduce human confusion but likely breaks generator assumptions | High | Yes | Generation and collateral semantics | Risky for all flows | Do not apply without design review |
| 14 | Edit generated GDS/layouts to pass DRC/LVS | Not applicable | Not reusable | High | Yes | Generated artifact only | No | Not allowed except labeled one-off diagnosis |

## Current Recommended Next Patch After Runtime Evidence

The verification wrappers now exist. The first likely safe runtime-driven patch after a real run is a narrowly scoped netlist/setup normalization change based on the extracted SPICE and Netgen report. Geometry changes remain deferred until Magic DRC provides concrete evidence.

## Review Points Before Any Generator Patch

- Confirm whether Owen wants ALIGN abstract `M1` documented permanently as SkyWater `li1`.
- Confirm whether official/open_pdks generated extracted SPICE uses model names that simple normalization can bridge.
- Confirm whether `Fin` and special VT/helper layers actually appear in streamed GDS.
- Confirm whether failures are reproducible on both unconstrained ALIGN baseline and AnalogDSL-constrained output under the same setup.

## Updated Ranking After Inverter Evidence

Date: 2026-06-23

| Rank | Candidate fix | Confidence | Expected impact | Risk | Runtime GDS required? | Changes generation or only verification? | Fair for baseline ALIGN and AnalogDSL? | Action |
|---:|---|---|---|---|---|---|---|---|
| 1 | Suppress LVT marker generation for legacy ALIGN `*_lvt` aliases until official LVT geometry exists | High for current inverter | High: removed all 60 Magic `poly.1b` DRC errors on the regenerated inverter | Medium: changes VT semantics; must be documented as RVT compatibility, not true LVT | Yes to prove | Generation metadata and LVS normalization | Yes if applied to all ALIGN-generated Sky130 outputs | Applied experimentally |
| 2 | Normalize LVS schematic to Magic extracted subckt dialect (`--mos-as-subckt --uppercase-nets`) | High for current inverter | High: changed equal-count LVS failure into unique match | Low/medium: verification-only but may mask schematic dialect issues if overused | Yes to prove | Verification only | Yes if both baseline and AnalogDSL use the same normalizer | Applied as opt-in |
| 3 | Keep `--expand-nf-stack --scale-wl-to-um` for mock-FinFET-derived MOS schematics | High for current inverter | High: maps 2 schematic MOS with `nf=20 stack=3` to 120 physical devices | Medium: verification normalization reflects generated topology, not original schematic abstraction | Yes to prove | Verification only | Yes if applied equally | Applied as opt-in |
| 4 | Patch downstream/default PnR GDS writer to honor `NoGDS` for `Outline`/boundary artifacts | Medium | Medium: would remove need for `.python.gds` or sanitizer path | Medium: writer path needs targeted source evidence | Yes | Generation/export only | Yes | Next useful patch |
| 5 | Add official LVT geometry support or reject invalid LVT lengths | Medium | High for real LVT support | High: changes transistor generator semantics and sizing constraints | Yes | Generation geometry/device policy | Yes, but affects all comparisons | Defer until transistor policy review |
| 6 | Broaden DRC/LVS validation to buffer/current mirror/OTA | Medium | High: determines whether inverter fix generalizes | Low for running checks, high for broad edits | Yes | Verification first | Yes | Next validation phase |
| 7 | Global poly pitch/width widening | Low after experiment | Negative on inverter: increased DRC errors and worsened LVS | High: large geometry/topology blast radius | Yes | Generation geometry | Yes but harmful | Deferred; keep as negative evidence |

## Updated Ranking After Buffer Evidence

Date: 2026-06-23

| Rank | Candidate fix | Confidence | Expected impact | Risk | Runtime GDS required? | Changes generation or only verification? | Fair for baseline ALIGN and AnalogDSL? | Action |
|---:|---|---|---|---|---|---|---|---|
| 1 | Patch ALIGN Python stream-out top-level label allow-list | High | High: changes buffer from port-mismatch LVS fail to clean LVS | Low/medium: export-label behavior only, but must be applied before generation | Yes | Generation/export only | Yes | Applied in runtime patcher |
| 2 | Keep Python stream-out `.python.gds` as primary verification artifact | High | High: avoids helper-layer import failures and now has correct top-level labels | Low | Yes | Export path selection | Yes | Continue |
| 3 | Patch native/default PnR GDS helper-boundary records | Medium | Medium: would make default `*.gds` usable without sanitizer | Medium/high: writer source path still needs tighter evidence | Yes | Generation/export only | Yes | Investigate later |

## Updated Ranking After Five-Transistor OTA Evidence

Date: 2026-06-23

| Rank | Candidate fix | Confidence | Expected impact | Risk | Runtime GDS required? | Changes generation or only verification? | Fair for baseline ALIGN and AnalogDSL? | Action |
|---:|---|---|---|---|---|---|---|---|
| 1 | Keep current patched Python stream-out + LVS normalization flow for MOS-only RVT circuits | High | High: clean inverter, buffer, and five-transistor OTA evidence | Low/medium: experimental but now repeatable | Yes | Export + verification | Yes | Use as current baseline |
| 2 | Validate next mixed/more complex circuit before changing geometry | High | High: prevents unnecessary PDK rewrites | Low for validation | Yes | Verification only | Yes | Next |
| 3 | True LVT support via geometry/policy | Medium | High, but separate from current clean RVT path | High | Yes | Device-generation semantics | Yes | Defer pending review |

## Updated Ranking After Current-Mirror OTA Evidence

Date: 2026-06-23

| Rank | Candidate fix | Confidence | Expected impact | Risk | Runtime GDS required? | Changes generation or only verification? | Fair for baseline ALIGN and AnalogDSL? | Action |
|---:|---|---|---|---|---|---|---|---|
| 1 | Fix grouped MOS array sizing for unequal-NF pairs | High that it is the current LVS blocker | High: current_mirror_ota is DRC-clean but fails LVS by exactly 8 extra PFETs | High: changes MOS primitive generation semantics | Yes | Generation/device topology | Yes if applied globally | Investigate with a targeted primitive-level rewrite |
| 2 | Add/read `scripts/analyze_mos_array_units.py` before validating larger grouped-MOS circuits | High | Medium/high: predicts LVS count risk from generated primitives before Magic/Netgen | Low | No after generation; yes to correlate with LVS | Verification/diagnostic only | Yes | Added |
| 3 | Force schematic normalizer to match rounded-up grouped arrays | Low | Could make current LVS pass artificially | High: would hide real layout-vs-schematic topology mismatch | Yes | Verification only, but unsafe | No | Do not apply |
| 4 | Continue validating circuits with equal-NF grouped MOS arrays | High | Medium: clean five-transistor OTA shows equal-NF groups are currently usable | Low | Yes | Verification only | Yes | Continue as regression coverage |

## Updated Ranking After Unit-Count Rewrite

Date: 2026-06-30

| Rank | Candidate fix | Confidence | Expected impact | Risk | Runtime GDS required? | Changes generation or only verification? | Fair for baseline ALIGN and AnalogDSL? | Action |
|---:|---|---|---|---|---|---|---|---|
| 1 | Keep explicit `unit_counts` for unequal-NF SCM MOS groups | High for current_mirror_ota | High: changed current_mirror_ota from DRC-clean/LVS-failing to DRC-clean/LVS-clean | Medium/high: generator topology change, but targeted | Yes | Generation/device topology | Yes | Applied experimentally |
| 2 | Sweep analyzer across all generated MOS primitives before each LVS run | High | Medium: catches future ratioed-group count risks early | Low | No after generation | Diagnostic only | Yes | Use as run preflight |
| 3 | Validate telescopic OTA or another ratioed grouped circuit | Medium | High: checks generality beyond one PMOS 6/12 case | Low for validation, medium for follow-up patches | Yes | Verification first | Yes | Next |
