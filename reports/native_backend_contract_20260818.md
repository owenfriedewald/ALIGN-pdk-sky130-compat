# Native Backend Contract and Mixed-Stack Generator Guard

Date: 2026-08-18

## Issue

The AnalogDSL compatibility campaign produced normal current-mirror GDS files
while ALIGN also emitted two internal open errors. Magic/Netgen subsequently
extracted 10 devices and 10 nets from a 12-device, 12-net schematic. Separately,
the historical verification wrapper defaulted to a sanitized GDS copy, and the
compatibility PDK still contains an import-time ALIGN source patch.

## Source diagnostic

The generated `SCM_PMOS_78583499` primitive contains `M1` with `STACK=1` and
`M2` with `STACK=2`. `MOSGenerator` accepts only one `stack` value for the
whole primitive. `gen_param.py` previously selected the first member's value,
so the second member's series topology was not represented.

## ALIGN-side file

- `SKY130_PDK/gen_param.py`
- `SKY130_PDK/mos.py`
- upstream grouping behavior in ALIGN's compiler primitive matcher
- ALIGN exporter files currently bridged by `SKY130_PDK/align_compat.py`

## official/open_pdks reference

The executable verifier is OpenPDKs Sky130A version
`54435919abffb937387ec956209f9cf5fd2dfbee`, Magic `8.3.603`.
The checked `sky130A.tech` SHA-256 is
`17731b09e2b1c4b35f057b202bf241a798224380dc33ad81125807a6b1b2ca81`.
The source rule reference is the SkyWater PDK rule tree at commit
`7198cf647113f56041e02abf3eb623692820c5e1`.

## Patch made

- Reject a grouped MOS primitive when a generator-wide integer parameter such
  as `STACK` differs across members.
- Extend `analyze_mos_array_units.py` to calculate per-member stack expansion
  and flag `unsupported_heterogeneous_stack`.
- Make native ALIGN GDS the verification-wrapper default. Sanitization is now
  opt-in and labeled `postprocessed_diagnostic_only`.
- Make Magic emit `drc listall why` so every violation rule is preserved.
- Add `gds_json_source: python` as an explicit PDK policy and recognize native
  exporter support from ALIGN commit `482c9fa3`
  (`sky130-native-streamout-current`), forward-ported onto upstream master
  `e392ae47`.
  Publication mode can set `ALIGN_SKY130_REQUIRE_NATIVE_EXPORT=1` to prohibit
  fallback to the legacy runtime source patch.

## Commands run

```text
.venv/bin/python -m pytest pdks/align-sky130-compat/tests -q
.venv/bin/python pdks/align-sky130-compat/scripts/analyze_mos_array_units.py <preserved mirror primitives JSON>
bash -n pdks/align-sky130-compat/scripts/run_magic_drc.sh pdks/align-sky130-compat/scripts/run_one_circuit_validation.sh
```

## Before result

The mixed-stack group was accepted, one stack value was used, ALIGN wrote a
GDS alongside open errors, and LVS failed with the exact missing-device/net
count. Verification tooling could still treat the process/GDS pair as backend
completion.

## After result

The preserved primitive is statically classified with four risky concrete
shape variants. New generation will fail before geometry emission instead of
silently producing that structure. Four focused PDK contract tests pass. No
new ALIGN or physical-verification run has been performed yet.

## Remaining problems

1. Confirm that the identical baseline/A4 `DoNotIdentify` input-safety controls
   in AnalogDSL's `backend_native_gds_v2` package prevent the unsupported
   mixed-stack current-mirror grouping in a complete ALIGN run.
2. Rebuild the Hellbender image from ALIGN commit `482c9fa3`; the source fix is
   focused-test verified but has not yet been exercised in the Slurm environment.
3. Run detailed native-GDS Magic diagnostics for the buffer's one shared DRC
   violation and change only the responsible generator/rule abstraction.
4. Execute outcome-paired baseline/A4 regressions under identical revisions.
