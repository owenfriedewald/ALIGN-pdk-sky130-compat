# One-circuit validation command
scripts/run_one_circuit_validation.sh --open-pdks-root /foss/pdks/sky130A --gds /tuple/generated/inverter.gds --layout-top INVERTER_0 --schematic /tuple/input/inverter.sp --schematic-top inverter --out-dir /work/reports/before_after/inverter_nopex --drop-param stack
# Magic DRC
scripts/run_magic_drc.sh --open-pdks-root /foss/pdks/sky130A --gds /work/reports/before_after/inverter_nopex/normalized/INVERTER_0.magic_sanitized.gds --top INVERTER_0 --out-dir /work/reports/before_after/inverter_nopex
# Magic extraction
scripts/run_magic_extract.sh --open-pdks-root /foss/pdks/sky130A --gds /work/reports/before_after/inverter_nopex/normalized/INVERTER_0.magic_sanitized.gds --top INVERTER_0 --out-dir /work/reports/before_after/inverter_nopex
# Netgen LVS
scripts/run_netgen_lvs.sh --open-pdks-root /foss/pdks/sky130A --layout-spice /work/reports/before_after/inverter_nopex/extracted/INVERTER_0.extracted.spice --layout-top INVERTER_0 --schematic-spice /work/reports/before_after/inverter_nopex/normalized/inverter.normalized.sp --schematic-top inverter --out-dir /work/reports/before_after/inverter_nopex
