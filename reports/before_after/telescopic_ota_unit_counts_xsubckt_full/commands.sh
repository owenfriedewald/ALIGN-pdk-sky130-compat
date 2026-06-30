# One-circuit validation command
scripts/run_one_circuit_validation.sh --open-pdks-root /foss/pdks/sky130A --gds generated_runs/telescopic_ota_unit_counts/TELESCOPIC_OTA_0.python.gds --layout-top TELESCOPIC_OTA --schematic examples/telescopic_ota/telescopic_ota.sp --schematic-top telescopic_ota --out-dir /work/reports/before_after/telescopic_ota_unit_counts_xsubckt_full --expand-nf-stack --scale-wl-to-um --coerce-lvt-to-rvt --mos-as-subckt --uppercase-nets
# Magic DRC
scripts/run_magic_drc.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/telescopic_ota_unit_counts/TELESCOPIC_OTA_0.python.gds --top TELESCOPIC_OTA --out-dir /work/reports/before_after/telescopic_ota_unit_counts_xsubckt_full
# Magic extraction
scripts/run_magic_extract.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/telescopic_ota_unit_counts/TELESCOPIC_OTA_0.python.gds --top TELESCOPIC_OTA --out-dir /work/reports/before_after/telescopic_ota_unit_counts_xsubckt_full
# Netgen LVS
scripts/run_netgen_lvs.sh --open-pdks-root /foss/pdks/sky130A --layout-spice /work/reports/before_after/telescopic_ota_unit_counts_xsubckt_full/extracted/TELESCOPIC_OTA.extracted.spice --layout-top TELESCOPIC_OTA --schematic-spice /work/reports/before_after/telescopic_ota_unit_counts_xsubckt_full/normalized/telescopic_ota.normalized.sp --schematic-top telescopic_ota --out-dir /work/reports/before_after/telescopic_ota_unit_counts_xsubckt_full
