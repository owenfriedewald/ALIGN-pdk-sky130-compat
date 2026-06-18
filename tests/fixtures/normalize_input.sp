* simple alias normalization fixture
.subckt inv in out vdd vss
mn0 out in vss vss nmos_lvt w=1u l=150n nf=2
mp0 out in vdd vdd pmos_rvt w=2u l=150n nf=2
.ends inv
