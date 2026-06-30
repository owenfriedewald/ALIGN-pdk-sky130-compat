# One-Circuit Validation Summary

Layout top: `BUFFER`
Schematic top: `buffer`

Raw logs: `/work/reports/before_after/buffer_direct_binding_patch_xsubckt_full/raw_logs`
Verification GDS: `generated_runs/buffer_direct_binding_patch/BUFFER_0.gds`
Normalized schematic: `/work/reports/before_after/buffer_direct_binding_patch_xsubckt_full/normalized/buffer.normalized.sp`
Extracted SPICE: `/work/reports/before_after/buffer_direct_binding_patch_xsubckt_full/extracted/BUFFER.extracted.spice`

Review:
- `/work/reports/before_after/buffer_direct_binding_patch_xsubckt_full/raw_logs/BUFFER.magic_drc.summary.txt`
- `/work/reports/before_after/buffer_direct_binding_patch_xsubckt_full/raw_logs/buffer_vs_BUFFER.netgen_lvs.summary.txt`

DRC:
```text
25: Total DRC errors found: 0
```

LVS:
```text
104: Circuits match uniquely.
42: Netlists match uniquely.
55: Final result: Circuits match uniquely.
```
