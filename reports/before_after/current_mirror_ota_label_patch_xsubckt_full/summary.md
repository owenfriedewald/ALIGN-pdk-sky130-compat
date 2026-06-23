# One-Circuit Validation Summary

Layout top: `CURRENT_MIRROR_OTA`
Schematic top: `current_mirror_ota`

Raw logs: `/work/reports/before_after/current_mirror_ota_label_patch_xsubckt_full/raw_logs`
Verification GDS: `generated_runs/current_mirror_ota_label_patch/CURRENT_MIRROR_OTA_0.python.gds`
Normalized schematic: `/work/reports/before_after/current_mirror_ota_label_patch_xsubckt_full/normalized/current_mirror_ota.normalized.sp`
Extracted SPICE: `/work/reports/before_after/current_mirror_ota_label_patch_xsubckt_full/extracted/CURRENT_MIRROR_OTA.extracted.spice`

Review:
- `/work/reports/before_after/current_mirror_ota_label_patch_xsubckt_full/raw_logs/CURRENT_MIRROR_OTA.magic_drc.summary.txt`
- `/work/reports/before_after/current_mirror_ota_label_patch_xsubckt_full/raw_logs/current_mirror_ota_vs_CURRENT_MIRROR_OTA.netgen_lvs.summary.txt`

DRC:
```text
25: Total DRC errors found: 0
```

LVS:
```text
85: Circuit 1 contains 192 devices, Circuit 2 contains 184 devices. *** MISMATCH ***
86: Circuit 1 contains 106 nets,    Circuit 2 contains 102 nets. *** MISMATCH ***
612: Final result: Netlists do not match.
```
