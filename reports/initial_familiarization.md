# Initial Familiarization

Date: 2026-06-18

## Repository Purpose

This workspace is a compatibility bridge around the ALIGN Sky130 PDK collateral. The practical goal is to make ALIGN-generated Sky130 layouts easier to verify with official/open_pdks-style Sky130 Magic/Netgen flows, while preserving provenance and avoiding broad PDK rewrites.

Most tracked project collateral outside `context/` and `upstream/` appears to be ALIGN-side Sky130 collateral: a compact `SKY130_PDK/` directory plus a few example SPICE inputs.

## Important Directories

| Path | Role |
|---|---|
| `SKY130_PDK/` | ALIGN Sky130 PDK collateral: generator Python, `layers.json`, and `models.sp`. |
| `examples/` | Small ALIGN input circuits including inverter, buffer, OTAs, and a UMich test case. |
| `context/` | Diagnostic report source. The existing filename is `context/ALIGN SKY130 Diagnostic Report.md`; the user-requested path used different capitalization. |
| `upstream/skywater-pdk/` | Official SkyWater PDK source/docs reference. Present and treated read-only. |
| `reports/` | Added for this compatibility effort. |
| `scripts/` | Added lightweight compatibility/debug helpers. |
| `tests/fixtures/` | Added tiny fixture for netlist normalization smoke testing. |

## Upstream/Reference Directories Found

| Reference | Status | Notes |
|---|---|---|
| `upstream/skywater-pdk/` | Found | Contains official SkyWater docs and rule CSVs, including `docs/rules/gds_layers.csv` and periphery rule CSVs. |
| `upstream/open_pdks/` | Not found | No open_pdks install tree, Magic `sky130A.tech`, or Netgen setup was found in this repo. |

## Diagnostic Report Sections

The diagnostic report contains:

| Section | Main claim |
|---|---|
| 1 Executive Summary | DRC/LVS failures are attributed to layer-number conflicts, layer naming offset, and rule mismatches. |
| 2 Methodology | Compares ALIGN `SKY130_PDK/layers.json` against a volare/open_pdks `sky130A.tech`. |
| 3.1 GDS Layer Number Conflicts | Claims GDS conflicts among Poly/V0/Pc and route/via layers. |
| 3.2 Layer Naming Offset | Claims ALIGN `M1` is Sky130 `li1`, `M2` is `met1`, etc. |
| 3.3 Numeric Rule Value Comparison | Lists width, spacing, enclosure, and area mismatches. |
| 3.4 Missing Rule Categories | Notes spacing, area, density, antenna, and device-specific rules missing from ALIGN encoding. |
| 4 LVS Issue Attribution | Attributes LVS failures to geometry/layer identification problems. |
| 5 Summary of Confirmed Mismatches | Summarizes critical/high/medium mismatch classes. |
| 6 Recommended Next Steps | Recommends layer assignment/name fixes, via widths, missing rules, and DRC/LVS reruns. |

## Likely Patch Targets

| Target | Why it matters | Current assessment |
|---|---|---|
| `SKY130_PDK/layers.json` | Central ALIGN layer/rule encoding. | Do not patch broadly yet. A repeatable comparison against `gds_layers.csv` shows the main routing/contact GDS mapping is consistent if ALIGN `M1` is treated as SkyWater `li1`. |
| `SKY130_PDK/models.sp` | Model aliases used by ALIGN primitive parsing. | Useful for generator input, but not enough for Netgen LVS by itself. |
| LVS netlist normalization wrapper | Can bridge schematic model aliases to official model names for tests. | Low-risk wrapper added as `scripts/normalize_netlist.py`. |
| Layer-map comparison helper | Needed to separate confirmed mapping bugs from naming-abstraction issues. | Added as `scripts/compare_layer_map.py`. |
| Magic/Netgen run scripts | Needed for one-circuit verification. | Deferred because no open_pdks Magic/Netgen setup is present. A runbook was added. |

## Available Scripts Or Missing Scripts

Before this pass, the repo had no DRC/LVS/PEX scripts. Added:

| Script | Purpose |
|---|---|
| `scripts/compare_layer_map.py` | Compares ALIGN `layers.json` GDS pairs against SkyWater `docs/rules/gds_layers.csv` under the documented ALIGN abstraction. |
| `scripts/normalize_netlist.py` | Rewrites simple MOS model aliases such as `nmos_lvt`/`pmos_rvt` to official Sky130 model names for LVS experiments. |

Still missing:

| Missing helper | Blocker |
|---|---|
| `scripts/run_magic_drc.sh` | Requires known Magic/open_pdks install path and test GDS. |
| `scripts/run_netgen_lvs.sh` | Requires known Netgen setup Tcl and extracted/schematic netlist conventions. |
| `scripts/run_pex.sh` | Requires Magic/open_pdks extraction setup and target layout. |

## Immediate Risks

| Risk | Why |
|---|---|
| Diagnostic report overstates GDS conflicts | GDS layer and datatype pairs can share a base layer number; this is normal in Sky130. The main ALIGN route/contact stack matches SkyWater docs under the `M1 == li1` abstraction. |
| Via-width recommendations appear to mix cut width with metal enclosure footprint | SkyWater CSVs list via cut widths of 0.150/0.200/0.200/0.800 um for via/via2/via3/via4, while the report recommends larger cut sizes by adding enclosure. |
| No open_pdks verification deck in repo | Magic/Netgen commands cannot be validated locally from repo-only context. |
| `Fin` remains a template artifact | It is used by the MOS generator grid, so removing/remapping it without generator review is unsafe. |
| HVT layer has a nonstandard GDS number | `Hvt` is `970:0` in ALIGN collateral; impact unclear without generated layouts and LVS/extraction evidence. |
