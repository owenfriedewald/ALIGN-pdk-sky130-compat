# Generate flattened official-Magic reference cells for the two Sky130 device
# classes required by the semantic-five LNA physical benchmark.  These outputs
# are geometry/extraction oracles for generator development, not campaign GDS.

if {![info exists ::env(REFERENCE_OUT_DIR)]} {
    puts stderr "REFERENCE_OUT_DIR is required"
    exit 2
}

set outdir $::env(REFERENCE_OUT_DIR)
file mkdir $outdir

proc generate_reference {cell_name device parameters outdir} {
    load $cell_name -quiet
    select top cell
    erase *
    box values 0 0 0 0

    set defaults_proc ${device}_defaults
    set check_proc ${device}_check
    set draw_proc ${device}_draw
    set defaults [$defaults_proc]
    set checked [$check_proc [dict merge $defaults $parameters]]
    $draw_proc $checked

    property FIXED_BBOX [box values]
    save $cell_name
    gds write [file join $outdir ${cell_name}.gds]
    puts stdout "reference_cell=$cell_name"
    puts stdout "reference_device=$device"
    puts stdout "reference_parameters=$checked"
    puts stdout "reference_bbox=[box values]"
    flush stdout
}

drc off
snap internal

generate_reference \
    SKY130_RES_HIGH_PO_1P41_R15EQ_REFERENCE \
    sky130::sky130_fd_pr__res_high_po_1p41 \
    [dict create l 60.43 w 1.41 m 1 nx 1 guard 1 doports 1] \
    $outdir

generate_reference \
    SKY130_RES_HIGH_PO_1P41_R8EQ_REFERENCE \
    sky130::sky130_fd_pr__res_high_po_1p41 \
    [dict create l 32.23 w 1.41 m 1 nx 1 guard 1 doports 1] \
    $outdir

generate_reference \
    SKY130_DIODE_PD2NW_05V5_A4_REFERENCE \
    sky130::sky130_fd_pr__diode_pd2nw_05v5 \
    [dict create l 2.0 w 2.0 area 4.0 peri 8.0 nx 1 ny 1 guard 1 doports 1] \
    $outdir

generate_reference \
    SKY130_CAP_MIM_M3_2_L30W30_REFERENCE \
    sky130::sky130_fd_pr__cap_mim_m3_2 \
    [dict create l 30.0 w 30.0 m 1 nx 1 ny 1 doports 1] \
    $outdir

quit -noprompt
