# Current-Mirror OTA LVS Mismatch Notes

Date: 2026-06-23

Status: `drc_clean`, `lvs_mismatch`.

## Result

Magic DRC completed with no reported DRC errors:

```text
Total DRC errors found: 0
```

Netgen LVS did not match:

```text
Circuit 1 contains 192 devices, Circuit 2 contains 184 devices. *** MISMATCH ***
Circuit 1 contains 106 nets,    Circuit 2 contains 102 nets. *** MISMATCH ***
sky130_fd_pr__pfet_01v8 (80) | sky130_fd_pr__pfet_01v8 (72) **Mismatch**
Final result: Netlists do not match.
```

NFET device counts match. The mismatch is concentrated in PFET extraction: Magic extracts 8 more PFET subdevices than the normalized schematic expects.

## Extra Extracted PFET Instances

The unmatched layout-side PFET instances reported by Netgen are:

```text
X177 a_200_1764# a_3412_1974# a_4874_840# VDD sky130_fd_pr__pfet_01v8
X178 a_2122_840# a_372_561# VDD VDD sky130_fd_pr__pfet_01v8
X181 VDD a_372_561# a_1950_840# VDD sky130_fd_pr__pfet_01v8
X184 a_5046_840# a_3412_1974# a_200_1764# VDD sky130_fd_pr__pfet_01v8
X186 a_372_561# a_372_561# a_402_840# VDD sky130_fd_pr__pfet_01v8
X187 a_2466_840# a_372_561# VDD VDD sky130_fd_pr__pfet_01v8
X189 VOUT a_372_561# a_746_840# VDD sky130_fd_pr__pfet_01v8
X190 VDD a_3412_1974# a_5390_840# VDD sky130_fd_pr__pfet_01v8
```

These are not unknown models or parameter-name differences. They are real extracted PFET devices connected to the PMOS mirror/output nets.

## Generator Evidence

`scripts/analyze_mos_array_units.py` flags the two generated PMOS grouped primitives:

```text
SCM_PMOS_85912433_X1_Y5, 5, 4.500, 36, 2, M1=6;M2=12, fractional_unit_rounding,unequal_nf_group,high_lvs_count_risk
SCM_PMOS_85912433_X5_Y1, 5, 4.500, 36, 2, M1=6;M2=12, fractional_unit_rounding,unequal_nf_group,high_lvs_count_risk
```

The source PMOS mirror groups are 6-finger and 12-finger devices with `stack=2`, so the normalized schematic expects `(6 + 12) * 2 = 36` PFET subdevices per grouped primitive. The current ALIGN Sky130 generator computes a fractional unit-cell count of `4.5` and emits `5` unit cells. Across two PMOS grouped primitives, that aligns with the observed `+8` extracted PFET count.

## Next Patch Target

The next PDK rewrite target is the MOS grouped-array sizing policy in `SKY130_PDK/gen_param.py` and/or the grouped MOS array implementation in `SKY130_PDK/mos.py`.

Do not fix this by filtering the LVS report or by forcing the schematic normalizer to invent extra devices. The layout is physically generating/extracting additional PFETs compared with the source schematic.
