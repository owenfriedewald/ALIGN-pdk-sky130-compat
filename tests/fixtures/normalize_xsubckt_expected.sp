* simple alias normalization fixture
.subckt inv IN OUT VDD VSS
Xmn0_nf0_stk0 OUT IN VSS VSS sky130_fd_pr__nfet_01v8 w=1 l=0.15
Xmn0_nf1_stk0 OUT IN VSS VSS sky130_fd_pr__nfet_01v8 w=1 l=0.15
Xmp0_nf0_stk0 OUT IN VDD VDD sky130_fd_pr__pfet_01v8 w=2 l=0.15
Xmp0_nf1_stk0 OUT IN VDD VDD sky130_fd_pr__pfet_01v8 w=2 l=0.15
.ends inv
