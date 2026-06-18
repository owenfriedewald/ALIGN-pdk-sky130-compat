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

Observed normalized MOS lines:

```spice
mn0 out in vss vss sky130_fd_pr__nfet_01v8 w=10.5e-7 L=150e-9 nf=20
mp0 out in vdd vdd sky130_fd_pr__pfet_01v8 w=10.5e-7 L=150e-9 nf=20
```

This is an opt-in LVS dialect normalization, not a claim that LVS will pass.

## Runtime Result

No Magic/Netgen run was performed. Required runtime inputs are missing:

- generated inverter GDS,
- open_pdks `sky130A` install,
- Magic executable,
- Netgen executable.
