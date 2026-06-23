# One-circuit validation command
scripts/run_one_circuit_validation.sh --open-pdks-root /foss/pdks/sky130A --gds generated_runs/five_transistor_ota_label_patch/FIVE_TRANSISTOR_OTA_0.python.gds --layout-top FIVE_TRANSISTOR_OTA --schematic examples/five_transistor_ota/five_transistor_ota.sp --schematic-top five_transistor_ota --out-dir /work/reports/before_after/five_transistor_ota_label_patch_xsubckt_full --expand-nf-stack --scale-wl-to-um --mos-as-subckt --uppercase-nets
# Magic DRC
scripts/run_magic_drc.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/five_transistor_ota_label_patch/FIVE_TRANSISTOR_OTA_0.python.gds --top FIVE_TRANSISTOR_OTA --out-dir /work/reports/before_after/five_transistor_ota_label_patch_xsubckt_full
# Magic extraction
scripts/run_magic_extract.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/five_transistor_ota_label_patch/FIVE_TRANSISTOR_OTA_0.python.gds --top FIVE_TRANSISTOR_OTA --out-dir /work/reports/before_after/five_transistor_ota_label_patch_xsubckt_full
# Netgen LVS
scripts/run_netgen_lvs.sh --open-pdks-root /foss/pdks/sky130A --layout-spice /work/reports/before_after/five_transistor_ota_label_patch_xsubckt_full/extracted/FIVE_TRANSISTOR_OTA.extracted.spice --layout-top FIVE_TRANSISTOR_OTA --schematic-spice /work/reports/before_after/five_transistor_ota_label_patch_xsubckt_full/normalized/five_transistor_ota.normalized.sp --schematic-top five_transistor_ota --out-dir /work/reports/before_after/five_transistor_ota_label_patch_xsubckt_full
