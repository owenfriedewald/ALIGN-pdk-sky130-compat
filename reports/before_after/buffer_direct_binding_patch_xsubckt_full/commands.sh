# One-circuit validation command
scripts/run_one_circuit_validation.sh --open-pdks-root /foss/pdks/sky130A --gds generated_runs/buffer_direct_binding_patch/BUFFER_0.gds --layout-top BUFFER --schematic examples/buffer/buffer.sp --schematic-top buffer --out-dir /work/reports/before_after/buffer_direct_binding_patch_xsubckt_full --expand-nf-stack --scale-wl-to-um --mos-as-subckt --uppercase-nets
# Magic DRC
scripts/run_magic_drc.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/buffer_direct_binding_patch/BUFFER_0.gds --top BUFFER --out-dir /work/reports/before_after/buffer_direct_binding_patch_xsubckt_full
# Magic extraction
scripts/run_magic_extract.sh --open-pdks-root /foss/pdks/sky130A --gds /work/generated_runs/buffer_direct_binding_patch/BUFFER_0.gds --top BUFFER --out-dir /work/reports/before_after/buffer_direct_binding_patch_xsubckt_full
# Netgen LVS
scripts/run_netgen_lvs.sh --open-pdks-root /foss/pdks/sky130A --layout-spice /work/reports/before_after/buffer_direct_binding_patch_xsubckt_full/extracted/BUFFER.extracted.spice --layout-top BUFFER --schematic-spice /work/reports/before_after/buffer_direct_binding_patch_xsubckt_full/normalized/buffer.normalized.sp --schematic-top buffer --out-dir /work/reports/before_after/buffer_direct_binding_patch_xsubckt_full
