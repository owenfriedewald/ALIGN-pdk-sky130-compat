# Mismatch-To-File Map

Date: 2026-06-18

This maps diagnostic mismatch classes to local ALIGN files and official/reference files. It is intentionally preparation-focused: no generated GDS, Magic run, Netgen run, or broad PDK rewrite is required.

| Mismatch class | ALIGN-side candidate files / behavior | Official/open_pdks reference files | Comparison method | Likely patch type | Can address without generated GDS? | Requires runtime verification? |
|---|---|---|---|---|---|---|
| GDS layer number conflicts | `SKY130_PDK/layers.json`; generator use in `SKY130_PDK/mos.py`, `cap.py`, `res.py` | `upstream/skywater-pdk/docs/rules/gds_layers.csv`; eventually `sky130A.tech` | Run `python3 scripts/compare_layer_map.py`; compare layer/datatype pairs, not base layer numbers only | Documentation, translation table, or narrow layer-map patch if proven wrong | Partly. Static mapping can be compared now | Yes. Must verify generated GDS imports and labels/extraction in Magic |
| Layer naming offset | ALIGN abstract names `M1`, `V0`, `M2`, etc. in `layers.json` and generators | `gds_layers.csv`; Magic tech when available | Map ALIGN abstract stack to official SkyWater stack (`M1=li1`, `M2=met1`, etc.) | Usually documentation/wrapper naming, not generation rename | Yes for static mapping | Yes for extraction/LVS behavior |
| Fin layer present | `layers.json` `Fin`; `mos.py` fin grid/wires | SkyWater planar docs have no `fin` drawing layer | Search generated terminal/GDS once available; inspect `mos.py` dependency | Unsafe generator refactor or export filtering only if proven artifact reaches GDS | No safe patch now; can document risk | Yes. Need generated GDS to see if `Fin` streams out and affects Magic |
| Pc/Poly overlap | `layers.json` `Pc=66:20`; `mos.py` creates `self.pc` on `Poly` layer while using `Pc` width/ext config | `gds_layers.csv` `poly=66:20`; licon/npc docs for poly contacts | Code inspection plus generated GDS/layer dump later | Documentation or generator cleanup if `Pc` is only config | Can document now | Yes. Need geometry to validate poly-contact extraction |
| Mcon/licon spacing attribution | `V0`, `V1` entries in `layers.json` | `p034-licon_dotdash.csv`, `p035-ct_dotdash.csv`, `gds_layers.csv` | Confirm whether ALIGN via abstraction maps to licon or mcon, then compare correct rule | Rule value patch only if mapped rule is wrong | Static comparison now; patch not safe yet | Yes. Contact arrays need DRC evidence |
| Via width recommendations | `V1` to `V5` width fields in `layers.json` | `p039-via_dotdash.csv`, `p041-via2_dotdash.csv`, `p042-via3_dotdash.csv`, `p044-via4_dotdash.csv` | Compare cut width separately from enclosure footprint | Do not patch cut widths from enclosure arithmetic; possible enclosure patch after evidence | Can classify now | Yes. Need DRC and generated geometry |
| Via/metal enclosure | `VencA_*`, `VencP_*` fields in `layers.json`; generator via placement | Per-layer via and metal enclosure CSVs; Magic DRC output later | Compare low/high enclosure fields against official adjacent-side rules | Narrow rule field change if violation is systematic | Partly | Yes. Enclosure depends on geometry orientation and generated shapes |
| Metal widths too conservative | `M1`-`M6` widths/pitches in `layers.json` | `p035-li`, `p038-m1`, `p040-m2`, `p042-m3`, `p044-m4/m5` CSVs | Compare official minimums to ALIGN routing grid rules | Generation/routing QoR change, not verification bridge | No safe patch now | Yes. Changes layout semantics and fair baseline behavior |
| Missing spacing/area rules | `layers.json` lacks many explicit signoff rule categories | Rule CSVs and Magic/open_pdks DRC deck | Static gap analysis, then let Magic enforce signoff | Add helper checks only if narrow and consumed by ALIGN; otherwise runbook | Documentation/checklist yes | Yes for physical evidence |
| Density/antenna/device-specific rules absent | No full signoff deck in ALIGN collateral | SkyWater docs and open_pdks Magic/KLayout decks | Inventory only | Do not duplicate full signoff into ALIGN | Documentation only | Yes. Requires signoff deck/runtime reports |
| LVS device recognition | `mos.py`, `cap.py`, `res.py`; layer labels/pins in `layers.json` | `table-f2a-lvs.tsv`; Netgen setup Tcl when available; Magic extraction | Compare required recognition layers and model names; generated extraction later | Netlist normalization or setup wrapper first, generator patch only with evidence | Partly | Yes. Needs Magic extraction and Netgen LVS |
| LVS model-name dialect | `SKY130_PDK/models.sp`; example netlists use `nmos_lvt`, `pmos_rvt`, official names | SkyWater docs model names; open_pdks model files/setup later | Run `python3 scripts/compare_model_names.py`; optional `normalize_netlist.py` | Opt-in netlist normalization wrapper | Yes | Yes. Netgen setup may need property equivalences too |
| Parameter-name dialect | Example MOS params `w`, `l`, `nf`, `m`, `stack`; ALIGN models include `nfin`, `parallel` | Netgen setup Tcl and extracted SPICE conventions when available | Compare schematic params vs extracted params after Magic extraction | Normalizer or Netgen property tolerance config | Can inventory now | Yes. Requires extracted SPICE |
| Pin/port label recognition | `layers.json` `Pin`/`Label` datatypes; generator terminal emission | Magic tech and periphery label/pin rules; generated GDS | Inspect generated GDS labels and Magic extraction logs | Export/label wrapper or generator fix | No | Yes. Need generated GDS and Magic labels/extraction |
| PEX setup | No local PEX scripts; `cap.py`/`res.py` approximations | open_pdks Magic extraction/PEX setup; `rcx-all.tsv` docs | Inventory then run Magic extraction when available | Runbook/script wrapper | Checklist yes | Yes. Needs Magic/open_pdks and layout |

## Immediate No-GDS Work Completed

- Static layer-map comparison: `scripts/compare_layer_map.py`
- Static reference preflight: `scripts/check_verification_refs.py`
- Static model/parameter comparison: `scripts/compare_model_names.py`
- Opt-in schematic model normalization: `scripts/normalize_netlist.py`

## Work Explicitly Waiting On Runtime Inputs

- Whether `Fin` reaches streamed GDS and causes Magic warnings/errors.
- Whether Magic extracts MOS devices from ALIGN geometry.
- Whether pin labels land on recognized layers/purposes.
- Whether Netgen model/property differences remain after simple alias normalization.
- Whether DRC failures are caused by true geometry versus setup/mapping assumptions.
