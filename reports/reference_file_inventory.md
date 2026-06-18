# Reference File Inventory

Date: 2026-06-18

Local sources inspected:

- ALIGN Sky130 collateral: `SKY130_PDK/`
- Diagnostic report: `context/ALIGN SKY130 Diagnostic Report.md`
- Official SkyWater reference: `upstream/skywater-pdk/`
- open_pdks reference: not present under `upstream/`

## Inventory

| Item | Expected purpose | Path if found | Source tree | Required for DRC/LVS/PEX | Missing / notes |
|---|---|---|---|---|---|
| `sky130A.tech` | Magic technology file containing Sky130 layer definitions, DRC rules, extraction definitions, and GDS mapping used by Magic. | Not found | Expected in open_pdks install, usually under `sky130A/libs.tech/magic/` | Required for Magic DRC and Magic extraction/PEX | Missing locally. The SkyWater docs are not a substitute for Magic runtime. |
| `.magicrc` / `sky130A.magicrc` | Magic startup file that loads the Sky130 Magic tech and sets search paths/styles. | Not found | Expected in open_pdks install, usually under `sky130A/libs.tech/magic/` | Required or strongly recommended for Magic DRC/extraction | Missing locally. The checklist uses `$OPEN_PDKS_SKY130A/libs.tech/magic/sky130A.magicrc` as placeholder. |
| Netgen setup Tcl | Device equivalence, property tolerances, and LVS setup for Sky130 extraction vs schematic. | Not found | Expected in open_pdks install, usually under `sky130A/libs.tech/netgen/sky130A_setup.tcl` | Required for Netgen LVS | Missing locally. Cannot validate LVS setup until an open_pdks path is supplied. |
| Magic extraction files | Extraction and PEX rules used by Magic, often embedded in `sky130A.tech` plus open_pdks support files. | Not found as runtime files | Expected in open_pdks install | Required for extraction and PEX | SkyWater docs include `docs/verification/pex/magic.rst`, but no executable extraction deck is present. |
| GDS layer maps | Official drawing/purpose to GDS layer/datatype mapping. | `upstream/skywater-pdk/docs/rules/gds_layers.csv` | official SkyWater docs | Required for layer-map comparison; Magic also needs equivalent mapping in tech file | Found as documentation. Used by `scripts/compare_layer_map.py`. |
| SPICE model files | Electrical/device model definitions for simulation and LVS model naming references. | `SKY130_PDK/models.sp` | ALIGN Sky130 | Needed for ALIGN primitive parsing; not sufficient for official LVS | Official SkyWater/open_pdks model `.spice` files were not found locally. |
| Primitive device definitions | Official primitive device names and recognition requirements. | `upstream/skywater-pdk/docs/rules/device-details/**`, `upstream/skywater-pdk/docs/rules/layers/table-f2a-lvs.tsv` | official SkyWater docs | Useful for LVS mapping and device triage | Documentation found. Runtime extraction recognition still requires Magic/open_pdks. |
| LVS layer/device table | Lists device classes, schematic elements, required layers, and layout model names. | `upstream/skywater-pdk/docs/rules/layers/table-f2a-lvs.tsv` | official SkyWater docs | Useful for LVS mismatch triage | Found as documentation. Needs Netgen setup for runtime equivalence. |
| Rule CSVs/docs | Official design-rule values and rule IDs for per-layer comparisons. | `upstream/skywater-pdk/docs/rules/periphery/*.csv`, `upstream/skywater-pdk/docs/rules/summary/*.csv`, `upstream/skywater-pdk/docs/verification/**/*.rst` | official SkyWater docs | Useful for diagnostic comparison; not executable DRC | Found as documentation. Do not duplicate full DRC deck into ALIGN without a narrow reason. |

## High-Value Local Rule References

| Purpose | Path |
|---|---|
| GDS drawing-layer mapping | `upstream/skywater-pdk/docs/rules/gds_layers.csv` |
| LVS device/layer matrix | `upstream/skywater-pdk/docs/rules/layers/table-f2a-lvs.tsv` |
| Layer descriptions | `upstream/skywater-pdk/docs/rules/layers/table-c4b-layer-description.csv` |
| Poly rules | `upstream/skywater-pdk/docs/rules/periphery/p028-poly_dotdash.csv` |
| Licon rules | `upstream/skywater-pdk/docs/rules/periphery/p034-licon_dotdash.csv` |
| Li1 rules | `upstream/skywater-pdk/docs/rules/periphery/p035-li_dotdash_dotdash.csv` |
| Mcon rules | `upstream/skywater-pdk/docs/rules/periphery/p035-ct_dotdash.csv` |
| Metal1 rules | `upstream/skywater-pdk/docs/rules/periphery/p038-m1_dotdash.csv` |
| Via rules | `upstream/skywater-pdk/docs/rules/periphery/p039-via_dotdash.csv` |
| Metal2 rules | `upstream/skywater-pdk/docs/rules/periphery/p040-m2_dotdash.csv` |
| Via2 rules | `upstream/skywater-pdk/docs/rules/periphery/p041-via2_dotdash.csv` |
| Metal3 rules | `upstream/skywater-pdk/docs/rules/periphery/p042-m3_dotdash.csv` |
| Via3 rules | `upstream/skywater-pdk/docs/rules/periphery/p042-via3_dotdash.csv` |
| Metal4/Metal5 rules | `upstream/skywater-pdk/docs/rules/periphery/p044-m4_dotdash.csv`, `upstream/skywater-pdk/docs/rules/periphery/p044-m5_dotdash.csv` |
| Via4 rules | `upstream/skywater-pdk/docs/rules/periphery/p044-via4_dotdash.csv` |
| RCX docs | `upstream/skywater-pdk/docs/rules/rcx/rcx-all.tsv`, `upstream/skywater-pdk/docs/verification/pex/magic.rst` |

## Preflight Command

Run local/reference discovery:

```sh
python3 scripts/check_verification_refs.py
```

Current local outcome: expected failure because Magic tech, Magic rc, Netgen setup Tcl, and Magic extraction runtime files are absent.

Run broader common-path discovery:

```sh
python3 scripts/check_verification_refs.py --search-common
```

Current outcome: `magic`, `netgen`, `schematic2layout.py`, open_pdks runtime files, and generated GDS are missing; `klayout` is available at `/usr/bin/klayout`.

When an open_pdks install is available, run:

```sh
python3 scripts/check_verification_refs.py --open-pdks-root "$OPEN_PDKS_SKY130A"
```

where `OPEN_PDKS_SKY130A` points at the installed `sky130A` directory, for example `/usr/local/share/pdk/sky130A`.
