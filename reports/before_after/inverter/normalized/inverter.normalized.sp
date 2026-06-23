.subckt inverter vss vdd in out
mn0 out in vss vss sky130_fd_pr__nfet_01v8_lvt w=10.5e-7 L=150e-9 nf=20
mp0 out in vdd vdd sky130_fd_pr__pfet_01v8_lvt w=10.5e-7 L=150e-9 nf=20
.ends inverter
