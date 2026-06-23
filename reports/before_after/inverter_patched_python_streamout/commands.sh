# One-circuit validation command
scripts/run_one_circuit_validation.sh --open-pdks-root /foss/pdks/sky130A --gds generated_runs/inverter_align_nogds_patch/INVERTER_0.python.gds --layout-top INVERTER --schematic artifacts/inverter_tuple/inverter/input/inverter.sp --schematic-top inverter --out-dir /work/reports/before_after/inverter_patched_python_streamout --expand-nf-stack --scale-wl-to-um
# Magic DRC
scripts/run_magic_drc.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/inverter_align_nogds_patch/INVERTER_0.python.gds --top INVERTER --out-dir /work/reports/before_after/inverter_patched_python_streamout
# Magic extraction
scripts/run_magic_extract.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/inverter_align_nogds_patch/INVERTER_0.python.gds --top INVERTER --out-dir /work/reports/before_after/inverter_patched_python_streamout
# Netgen LVS
scripts/run_netgen_lvs.sh --open-pdks-root /foss/pdks/sky130A --layout-spice /work/reports/before_after/inverter_patched_python_streamout/extracted/INVERTER.extracted.spice --layout-top INVERTER --schematic-spice /work/reports/before_after/inverter_patched_python_streamout/normalized/inverter.normalized.sp --schematic-top inverter --out-dir /work/reports/before_after/inverter_patched_python_streamout
