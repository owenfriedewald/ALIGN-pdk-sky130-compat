# Diagnostic Triage

Date: 2026-06-18

Primary report: `context/ALIGN SKY130 Diagnostic Report.md`

Reference used: `upstream/skywater-pdk/docs/rules/gds_layers.csv` and SkyWater periphery rule CSVs under `upstream/skywater-pdk/docs/rules/periphery/`.

No `upstream/open_pdks/` tree, Magic `sky130A.tech`, or Netgen setup file was present in this workspace.

## Triage Table

| Diagnostic section / issue | Failure stage | Affected circuit/artifact | Suspected mismatch type | ALIGN-side file or behavior | official/open_pdks reference file or behavior found | Likely patch location | Risk | Expected verification improvement | Action |
|---|---|---|---|---|---|---|---|---|---|
| 3.1 Poly/V0/Pc GDS conflicts | DRC/LVS/extraction | All generated GDS | Layer mapping | `Poly=66:20`, `V0=66:44`, `Pc=66:20` in `layers.json`; `mos.py` emits pc wire on `Poly` | `poly=66:20`, `licon1=66:44` in SkyWater `gds_layers.csv`; sharing base layer with different datatype is expected | No direct PDK edit yet | Medium | Avoids incorrect layer remap | investigate_more |
| 3.1 M1/V1/M2/V2 conflicts | DRC/LVS/extraction | All routed layouts | Layer naming abstraction | ALIGN abstract `M1=67:20`, `V1=67:44`, `M2=68:20`, `V2=68:44` | SkyWater `li1=67:20`, `mcon=67:44`, `met1=68:20`, `via=68:44` | `scripts/compare_layer_map.py` added | Low for helper, high for direct remap | Gives repeatable evidence before any layer edits | fix_now helper only |
| 3.2 Layer naming offset | DRC/LVS/extraction | All generated layouts | Layer name abstraction vs official naming | ALIGN uses `M1/M2/...` where `M1` corresponds to local interconnect | SkyWater names local interconnect `li1` and metal1 `met1`; GDS pairs match under abstraction | Documentation/tooling first; generator rename unsafe | High | Clarifies that naming is abstract, not necessarily a streamed-GDS error | investigate_more |
| 3.2 Fin layer present | DRC/extraction | MOS generator output | Non-Sky130 template artifact | `Fin=2:0` and MOS grid uses `self.fin` | No planar Sky130 `fin` drawing layer in `gds_layers.csv` | `SKY130_PDK/mos.py`, `layers.json` | High | Could remove unknown-layer warnings only after proving it does not alter MOS generation semantics | unsafe_without_review |
| 3.3 li1 min width mismatch | DRC | Routes on ALIGN `M1` | Rule value/conservatism | `M1 Width=250 nm` | `li.1` official min is 170 nm | `layers.json` | Medium | Reducing width may improve density but can change routing/grid behavior | investigate_more |
| 3.3 li1 spacing/area missing | DRC | Routes on ALIGN `M1` | Missing rule encoding | No explicit spacing/area fields beyond pitch/width | `li.3=170 nm`, `li.6=0.0561 um2` | `layers.json` schema and ALIGN router rule support | Medium | Could catch invalid geometries earlier if schema supports it | investigate_more |
| 3.3 mcon/V0 spacing mismatch | DRC | Contact arrays | Diagnostic layer attribution issue | `V0 SpaceX/Y=170 nm` | If V0 is `licon1`, `licon.2=170 nm`; if mcon, `ct.2=190 nm` | No edit; helper documents V0 as licon1 | Medium | Prevents changing licon spacing to mcon spacing incorrectly | investigate_more |
| 3.3 metal1/M2 width mismatch | DRC/QoR | Routes on ALIGN `M2` | Conservative width | `M2 Width=280 nm` | `m1.1=140 nm` | `layers.json` | Medium | Smaller routes may help QoR but alters routing tracks/design assumptions | investigate_more |
| 3.3 metal spacing/area missing | DRC | All metal | Missing rule categories | `layers.json` encodes pitch/width/end-to-end, not full DRC deck | SkyWater rule CSVs include spacing/area/density details | `layers.json` plus ALIGN rule consumers | High | Early geometry filtering, but only if ALIGN consumes new fields | defer |
| 3.3 via1 width undersized | DRC | ALIGN `V1` | Diagnostic arithmetic likely mixes via cut and enclosure | `V1 WidthX/Y=170 nm` | ALIGN `V1` maps to mcon; `ct.1=170 nm` | No edit | High | Avoids changing mcon cut to a via-footprint number | unsafe_without_review |
| 3.3 via2 width undersized | DRC | ALIGN `V2` | Diagnostic arithmetic likely mixes via cut and enclosure | `V2 WidthX/Y=150 nm` | ALIGN `V2` maps to via; `via.1a=150 nm` outside `areaid.mt` | No edit | High | Avoids invalid cut-width change | unsafe_without_review |
| 3.3 via3 width undersized | DRC | ALIGN `V3` | Diagnostic arithmetic likely mixes via cut and enclosure | `V3 WidthX/Y=200 nm` | ALIGN `V3` maps to via2; `via2.1a=200 nm` | No edit | High | Avoids invalid cut-width change | unsafe_without_review |
| 3.3 via4 width undersized | DRC | ALIGN `V4` | Diagnostic arithmetic likely mixes via cut and enclosure | `V4 WidthX/Y=200 nm` | ALIGN `V4` maps to via3; `via3.1=200 nm` | No edit | High | Avoids invalid cut-width change | unsafe_without_review |
| 3.3 V1 zero enclosure | DRC | ALIGN `V1` mcon | Enclosure | `V1 VencA_L=0`, `VencP_L=0` | For mcon, `ct.4=0`; met1 enclosure handled by metal rule `m1.4=30 nm` and current high-side enclosure values | No edit | Medium | Needs generated geometry before changing asymmetric enclosures | investigate_more |
| 3.4 density/antenna/device-specific rules absent | DRC/signoff | All layouts | Missing rule deck coverage | ALIGN `layers.json` is not a full signoff rule deck | SkyWater docs have many categories not represented in ALIGN | Verification/runbook, not `layers.json` rewrite | High | Use Magic/open_pdks as authoritative checker instead of duplicating full deck | defer |
| 4 LVS failures from layer mapping | LVS/extraction | All layouts | Extraction setup and netlist dialect | Current GDS map appears consistent under abstraction; examples use mixed model aliases | No Netgen/open_pdks setup present; official device names appear in examples and `models.sp` | `scripts/normalize_netlist.py` added | Low for helper | Makes one-circuit LVS experiments easier without altering generator behavior | fix_now |

## Priority Result

The first pass did not find a safe direct edit to `SKY130_PDK/layers.json` from the diagnostic report. The main route/contact GDS pairs match SkyWater docs when interpreted as:

| ALIGN abstract | SkyWater drawing layer |
|---|---|
| `M1` | `li1` |
| `V0` | `licon1` |
| `M2` | `met1` |
| `V1` | `mcon` |
| `M3` | `met2` |
| `V2` | `via` |
| `M4` | `met3` |
| `V3` | `via2` |
| `M5` | `met4` |
| `V4` | `via3` |
| `M6` | `met5` |
| `V5` | `via4` |

The next physical step should be a one-circuit Magic import/extract/LVS run to see whether failures are caused by generated geometry, labels, model names, missing setup files, or the remaining special layers (`Fin`, `Hvt`, MIM helpers), rather than applying the report's broad layer-number edits directly.
