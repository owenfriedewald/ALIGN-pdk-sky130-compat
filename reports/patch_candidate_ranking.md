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
