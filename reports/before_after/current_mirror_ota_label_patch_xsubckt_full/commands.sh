# One-circuit validation command
scripts/run_one_circuit_validation.sh --open-pdks-root /foss/pdks/sky130A --gds generated_runs/current_mirror_ota_label_patch/CURRENT_MIRROR_OTA_0.python.gds --layout-top CURRENT_MIRROR_OTA --schematic examples/current_mirror_ota/current_mirror_ota.sp --schematic-top current_mirror_ota --out-dir /work/reports/before_after/current_mirror_ota_label_patch_xsubckt_full --expand-nf-stack --scale-wl-to-um --mos-as-subckt --uppercase-nets
# Magic DRC
scripts/run_magic_drc.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/current_mirror_ota_label_patch/CURRENT_MIRROR_OTA_0.python.gds --top CURRENT_MIRROR_OTA --out-dir /work/reports/before_after/current_mirror_ota_label_patch_xsubckt_full
# Magic extraction
scripts/run_magic_extract.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/current_mirror_ota_label_patch/CURRENT_MIRROR_OTA_0.python.gds --top CURRENT_MIRROR_OTA --out-dir /work/reports/before_after/current_mirror_ota_label_patch_xsubckt_full
# Netgen LVS
scripts/run_netgen_lvs.sh --open-pdks-root /foss/pdks/sky130A --layout-spice /work/reports/before_after/current_mirror_ota_label_patch_xsubckt_full/extracted/CURRENT_MIRROR_OTA.extracted.spice --layout-top CURRENT_MIRROR_OTA --schematic-spice /work/reports/before_after/current_mirror_ota_label_patch_xsubckt_full/normalized/current_mirror_ota.normalized.sp --schematic-top current_mirror_ota --out-dir /work/reports/before_after/current_mirror_ota_label_patch_xsubckt_full
