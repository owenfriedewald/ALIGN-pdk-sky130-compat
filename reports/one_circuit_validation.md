# One-Circuit Validation

Date: 2026-06-18

Status: `diagnostic_only`

## Selected Circuit

Target: inverter

| Item | Value |
|---|---|
| Schematic SPICE | `examples/inverter/inverter.sp` |
| Top cell | `inverter` |
| Generated GDS | Not found |
| open_pdks `sky130A` path | Not found |
| Magic executable | Not found |
| Netgen executable | Not found |

## Why Inverter

The inverter is the smallest local circuit and has simple MOS instances:

```spice
mn0 out in vss vss nmos_lvt w=10.5e-7 L=150e-9 nf=20 stack=3
mp0 out in vdd vdd pmos_lvt w=10.5e-7 L=150e-9 nf=20 stack=3
```

The model aliases can be normalized to official Sky130 names. The ALIGN-only `stack` parameter can be dropped explicitly for an LVS dialect experiment using `--drop-param stack`.

## Prepared Command

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root "$OPEN_PDKS_SKY130A" \
  --gds "$LAYOUT_GDS" \
  --schematic examples/inverter/inverter.sp \
  --top inverter \
  --out-dir reports/before_after/inverter \
  --drop-param stack
```

Expected output structure:

```text
reports/before_after/inverter/
  summary.md
  commands.sh
  raw_logs/
  normalized/
  extracted/
  magic_work/
```

## Static Normalization Evidence

Command run:

```sh
python3 scripts/normalize_netlist.py examples/inverter/inverter.sp --drop-param stack -o /tmp/inverter.normalized.sp
```

Observed normalized MOS lines after the experimental LVT-aware mapping:

```spice
mn0 out in vss vss sky130_fd_pr__nfet_01v8_lvt w=10.5e-7 L=150e-9 nf=20
mp0 out in vdd vdd sky130_fd_pr__pfet_01v8_lvt w=10.5e-7 L=150e-9 nf=20
```

This is an opt-in LVS dialect normalization, not a claim that LVS will pass.

## Runtime Result

Initial static pass had no Magic/Netgen run because required runtime inputs were missing:

- generated inverter GDS,
- open_pdks `sky130A` install,
- Magic executable,
- Netgen executable.

## Tuple Runtime Result

Status: `diagnostic_only`

Tuple used:

- GDS: `artifacts/inverter_tuple/inverter/generated/inverter.gds`
- Schematic: `artifacts/inverter_tuple/inverter/input/inverter.sp`
- Layout top: `INVERTER_0`
- Schematic top: `inverter`
- open_pdks path inside Docker: `/foss/pdks/sky130A`
- Magic/Netgen image: `hpretl/iic-osic-tools:latest`
- ALIGN image found later: `darpaalign/align-public:latest`

The wrapper now sanitizes a verification copy of the GDS, dropping `100:5`, `104:0`, and `235:5` helper layers. It keeps `69:5` because SkyWater documents it as `met2,label`.

Results:

- Magic DRC loaded the real `INVERTER_0` top and reported `60` DRC errors.
- Magic extraction produced `reports/before_after/inverter_nopex/extracted/INVERTER_0.extracted.spice`.
- LVS with normal model/parameter normalization failed with `120` extracted MOS devices versus `2` schematic MOS devices.
- LVS with `--expand-nf-stack --scale-wl-to-um` matched device and net counts at `120` devices and `564` nets on both sides, but still failed top-level pin/net matching.

Best current command:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root "$OPEN_PDKS_SKY130A" \
  --gds "$LAYOUT_GDS" \
  --layout-top INVERTER_0 \
  --schematic "$SCHEMATIC_SPICE" \
  --schematic-top inverter \
  --out-dir reports/before_after/inverter_expanded \
  --expand-nf-stack \
  --scale-wl-to-um
```

Interpretation:
The dominant LVS mismatch is no longer model naming. It is the inherited mock-FinFET MOS abstraction: ALIGN encodes physical multiplicity as `nf/stack`, while Magic extracts every planar poly/diff crossing as an individual device. Expansion confirms the count mismatch, and remaining failures point to pin/connectivity semantics.

## Patched Python Stream-Out Result

Status: `diagnostic_only`

The ALIGN runtime was patched inside `darpaalign/align-public:latest` with:

```sh
python3 scripts/patch_align_gds_export.py
```

and `SKY130_PDK/layers.json` now marks helper layers `Bbox`, `Boundary`, `Rboundary`, `Cboundary`, and `Outline` as `NoGDS`.

Regenerated artifact:

- `generated_runs/inverter_align_nogds_patch/INVERTER_0.python.gds`
- Layout top in that GDS: `INVERTER`

Layer inspection with KLayout Python showed no `100:5`, `104:0`, or `235:5` records in the patched Python stream-out. The default PnR GDS still has `104:0` and `235:5`, so use `.python.gds` or the sanitizer until the downstream writer is patched.

No-sanitizer validation command:

```sh
scripts/run_one_circuit_validation.sh \
  --open-pdks-root /foss/pdks/sky130A \
  --gds generated_runs/inverter_align_nogds_patch/INVERTER_0.python.gds \
  --layout-top INVERTER \
  --schematic artifacts/inverter_tuple/inverter/input/inverter.sp \
  --schematic-top inverter \
  --out-dir reports/before_after/inverter_patched_python_streamout \
  --no-sanitize-gds \
  --expand-nf-stack \
  --scale-wl-to-um
```

Results:

- Magic import had no unknown helper-layer errors.
- Magic DRC still reported `60` errors.
- Magic extraction produced `reports/before_after/inverter_patched_python_streamout/extracted/INVERTER.extracted.spice`.
- Netgen LVS still failed, but reached `120` devices and `564` nets on both sides.

Current best next command is the no-sanitizer patched Python stream-out command above. The next actual PDK/generator work is DRC classification and pin/connectivity semantics.
