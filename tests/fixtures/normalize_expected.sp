* simple alias normalization fixture
.subckt inv in out vdd vss
mn0 out in vss vss sky130_fd_pr__nfet_01v8_lvt w=1u l=150n nf=2
mp0 out in vdd vdd sky130_fd_pr__pfet_01v8 w=2u l=150n nf=2
.ends inv
