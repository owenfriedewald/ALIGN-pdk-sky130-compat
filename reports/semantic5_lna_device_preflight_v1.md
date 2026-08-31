# Semantic-five LNA fixed-device preflight v1

Date: 2026-08-30

Status: **four fixed macros are byte-frozen and official-Magic DRC-clean;
full-LNA closure remains an execution gate**

## Scope

This preflight closes the device classes that the reconstructed semantic-five
LNA cannot obtain from the compatibility PDK's parameterized MOS/CAP/RES
generators.  It uses ALIGN's native `--blackbox_dir` primitive-input path; it
does not rewrite a placed or routed GDS.  Each committed macro is produced from
an official Magic Sky130 PCell reference.  The builder changes only the cell
name and the known port-label strings, verifies that non-text geometry is
unchanged, and emits GDS with timestamps disabled for byte reproducibility.

The verification tuple is:

- container: `hpretl/iic-osic-tools:latest`, digest
  `sha256:ae380e2b0b96bd57b91f5864623ed488d00f78eaf58caf7f7d9d3754d315df38`;
- OpenPDKs Sky130A: `54435919abffb937387ec956209f9cf5fd2dfbee`;
- Magic: 8.3 revision 603, Sky130A technology version
  `1.0.571-1-g5443591`; and
- Netgen: 1.5.316.

## Source-level resistor correction

The official `sky130_fd_pr__res_high_po_0p35` PCell generated one `rpm.1`
violation under this same official deck.  `rpm_generate` is derived from the
resistor poly/contact geometry, so widening only the raw RPM marker did not and
could not close the rule.  That diagnostic edit was discarded.

The Sky130 PCell declares the 0.35, 0.69, 1.41, 2.85, and 5.73 um high-poly
variants compatible.  The first compatible width whose derived region passes
the 1.27 um `rpm.1` minimum is 1.41 um.  The pre-layout source therefore uses:

- `w=1.41 um, l=60.43 um` for the original `15/0.35` L/W target; and
- `w=1.41 um, l=32.23 um` for the original `8/0.35` L/W target.

The respective L/W errors are below 0.005%.  This preserves the intended
high-poly resistance ratios while changing the physical device variant; the
substitution is disclosed in the operational and LVS netlists.  It is not a
claim of identical parasitics.

## Observed device evidence

| Committed macro | SHA-256 | Magic DRC | Extracted device identity | Standalone LVS |
|---|---|---:|---|---|
| `SKY130_FD_PR__RES_HIGH_PO_0P35_MGFMH8.gds` | `a90a5417...fda44e5` | 0 | `res_high_po_1p41 l=60.43` | unique match |
| `SKY130_FD_PR__RES_HIGH_PO_0P35_V3QVRN.gds` | `b2877f1b...2655a9c` | 0 | `res_high_po_1p41 l=32.23` | unique match |
| `SKY130_FD_PR__CAP_MIM_M3_2_LJ5JLG.gds` | `0049779a...3a60361` | 0 | `cap_mim_m3_2 l=30 w=30` | deferred to full LNA |
| `SKY130_FD_PR__DIODE_PD2NW_05V5_WW7YB9.gds` | `45a55692...693d23` | 0 | `diode_pd2nw_05v5 perim=8e6 area=4e12` | deferred to full LNA |

Magic emits isolated two-terminal cap/diode tops as a top-level `.end` network
rather than a named `.subckt`, so the generic standalone LVS wrapper cannot
perform a meaningful pin-name match for those two macros.  Their device model,
terminal nets, and parameters were extracted exactly, but unique cap/diode LVS
is deliberately not claimed here.  The unchanged native final LNA GDS must
pass unique Netgen LVS against the separately frozen device-aware schematic.

All four macros passed a repeat build with byte-identical SHA-256 values.  A
local ALIGN frontend run through `2_primitives` recognized all four exact GDS
macros through `--blackbox_dir`, generated the true-LVT and RVT MOS primitives,
and completed.  This is a parser/topology/primitive-generation preflight, not
layout completion.

## Remaining gate

Before publication classification, a paired baseline/A4 LNA run must use one
pinned ALIGN image and this exact PDK commit, consume these exact macro bytes,
produce normal native final GDS with no nonempty `*.errors`, and pass official
Magic DRC zero plus unique Netgen LVS.  Complete-RC extraction and any PEX/QoR
work remain downstream of that full-circuit pair gate.
