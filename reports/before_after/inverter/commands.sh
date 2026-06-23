# One-circuit validation command
scripts/run_one_circuit_validation.sh --open-pdks-root /foss/pdks/sky130A --gds /tuple/generated/inverter.gds --schematic /tuple/input/inverter.sp --top inverter --out-dir /work/reports/before_after/inverter --drop-param stack
# Magic DRC
scripts/run_magic_drc.sh --open-pdks-root /foss/pdks/sky130A --gds /tuple/generated/inverter.gds --top inverter --out-dir /work/reports/before_after/inverter
# Magic extraction
scripts/run_magic_extract.sh --open-pdks-root /foss/pdks/sky130A --gds /tuple/generated/inverter.gds --top inverter --out-dir /work/reports/before_after/inverter
# One-circuit validation command
scripts/run_one_circuit_validation.sh --open-pdks-root /foss/pdks/sky130A --gds /tuple/generated/inverter.gds --layout-top INVERTER_0 --schematic /tuple/input/inverter.sp --schematic-top inverter --out-dir /work/reports/before_after/inverter --drop-param stack
# Magic DRC
scripts/run_magic_drc.sh --open-pdks-root /foss/pdks/sky130A --gds /work/reports/before_after/inverter/normalized/INVERTER_0.magic_sanitized.gds --top INVERTER_0 --out-dir /work/reports/before_after/inverter
# Magic extraction
scripts/run_magic_extract.sh --open-pdks-root /foss/pdks/sky130A --gds /work/reports/before_after/inverter/normalized/INVERTER_0.magic_sanitized.gds --top INVERTER_0 --out-dir /work/reports/before_after/inverter
# Netgen LVS
scripts/run_netgen_lvs.sh --open-pdks-root /foss/pdks/sky130A --layout-spice /work/reports/before_after/inverter/extracted/INVERTER_0.extracted.spice --layout-top INVERTER_0 --schematic-spice /work/reports/before_after/inverter/normalized/inverter.normalized.sp --schematic-top inverter --out-dir /work/reports/before_after/inverter
