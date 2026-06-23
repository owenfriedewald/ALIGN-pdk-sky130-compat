# One-Circuit Validation Summary

Layout top: `INVERTER`
Schematic top: `inverter`

Raw logs: `/work/reports/before_after/inverter_no_lvt_marker_xsubckt_full/raw_logs`
Verification GDS: `generated_runs/inverter_align_no_lvt_marker/INVERTER_0.python.gds`
Normalized schematic: `/work/reports/before_after/inverter_no_lvt_marker_xsubckt_full/normalized/inverter.normalized.sp`
Extracted SPICE: `/work/reports/before_after/inverter_no_lvt_marker_xsubckt_full/extracted/INVERTER.extracted.spice`

Review:
- `/work/reports/before_after/inverter_no_lvt_marker_xsubckt_full/raw_logs/INVERTER.magic_drc.summary.txt`
- `/work/reports/before_after/inverter_no_lvt_marker_xsubckt_full/raw_logs/inverter_vs_INVERTER.netgen_lvs.summary.txt`

DRC:
```text
25: Total DRC errors found: 0
```

LVS:
```text
90: Circuits match uniquely.
43: Netlists match with 10 symmetries.
56: Final result: Circuits match uniquely.
```
