# One-circuit validation command
scripts/run_one_circuit_validation.sh --open-pdks-root /foss/pdks/sky130A --gds generated_runs/inverter_align_no_lvt_marker/INVERTER_0.python.gds --layout-top INVERTER --schematic artifacts/inverter_tuple/inverter/input/inverter.sp --schematic-top inverter --out-dir /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full --expand-nf-stack --scale-wl-to-um --coerce-lvt-to-rvt --mos-as-subckt --uppercase-nets
# Magic DRC
scripts/run_magic_drc.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/inverter_align_no_lvt_marker/INVERTER_0.python.gds --top INVERTER --out-dir /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full
# Magic extraction
scripts/run_magic_extract.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/inverter_align_no_lvt_marker/INVERTER_0.python.gds --top INVERTER --out-dir /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full
# Netgen LVS
scripts/run_netgen_lvs.sh --open-pdks-root /foss/pdks/sky130A --layout-spice /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full/extracted/INVERTER.extracted.spice --layout-top INVERTER --schematic-spice /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full/normalized/inverter.normalized.sp --schematic-top inverter --out-dir /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full
# One-circuit validation command
scripts/run_one_circuit_validation.sh --open-pdks-root /foss/pdks/sky130A --gds generated_runs/inverter_align_no_lvt_marker/INVERTER_0.python.gds --layout-top INVERTER --schematic artifacts/inverter_tuple/inverter/input/inverter.sp --schematic-top inverter --out-dir /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full --expand-nf-stack --scale-wl-to-um --coerce-lvt-to-rvt --mos-as-subckt --uppercase-nets
# Magic DRC
scripts/run_magic_drc.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/inverter_align_no_lvt_marker/INVERTER_0.python.gds --top INVERTER --out-dir /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full
# Magic extraction
scripts/run_magic_extract.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/inverter_align_no_lvt_marker/INVERTER_0.python.gds --top INVERTER --out-dir /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full
# Netgen LVS
scripts/run_netgen_lvs.sh --open-pdks-root /foss/pdks/sky130A --layout-spice /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full/extracted/INVERTER.extracted.spice --layout-top INVERTER --schematic-spice /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full/normalized/inverter.normalized.sp --schematic-top inverter --out-dir /work/reports/before_after/inverter_no_lvt_marker_xsubckt_full
