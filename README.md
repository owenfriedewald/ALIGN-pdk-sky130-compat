# ALIGN-pdk-sky130
## We are working to support [SKY130](https://github.com/google/skywater-pdk) with [ALIGN](https://github.com/ALIGN-analoglayout/ALIGN-public)

## Verification contract for this compatibility branch

Publication-grade checks use the normal final GDS emitted by ALIGN without
post-generation layer deletion, remapping, or geometry rewriting. The
verification wrapper now defaults to that native artifact. Its optional
`--sanitize-gds-diagnostic-only` mode exists only to localize legacy streamout
problems and must not be reported as physical evidence.

The MOS generator also rejects grouped primitives whose members have different
`STACK` values. One generated primitive has one stack geometry; silently using
the first member's value produces a structurally incorrect layout. The proper
upstream response is to prevent that unsupported grouping while retaining safe
homogeneous groups.

Concrete MOS aspect-ratio variants are limited by the official 15 um
diffusion-to-body-tap latch-up distance. Because the current generator places
the body contact on one outer edge of an array, and one MOS row is 28 fins at a
210 nm pitch, only one- and two-row variants are legal. Taller variants are
excluded before placement rather than repaired in the emitted GDS.

PMOS primitive bounding boxes include a grid-aligned placement halo derived
from the official `1.27 um` N-well spacing rule. ALIGN placement LEF excludes
N-well because it is not a routing layer; without this halo, separately placed
PMOS primitives can leave a legal-looking one-track gap that fails Magic rule
`nwell.2a`. The halo changes placement abstraction before layout generation and
does not rewrite or sanitize the emitted GDS. The Magic wrapper expands the
loaded hierarchy before listing violations so preserved logs include rule names
and bounding boxes for subcell errors.

The current import-time ALIGN streamout patch is transitional. The target
journal flow uses a pinned, rebuilt ALIGN source revision containing the
equivalent exporter fixes natively. Set
`ALIGN_SKY130_REQUIRE_NATIVE_EXPORT=1` in that flow: an older ALIGN build then
fails immediately instead of falling back to runtime source mutation.

The MIM-capacitor primitive carries the official CAPM recognition layer and
its dedicated contact into native streamout.  Its abstract macro also exposes
the official CAPM-to-unrelated-metal3 clearance as legal-width, grid-aligned
routing-only M4 obstructions, while explicit M3/V3 access points keep both
formal terminals reachable.  These obstructions remain in LEF for routing but
require an ALIGN exporter that omits `netType=blockage` rectangles from
physical GDS.
The LVS normalizer can reclassify a specifically named ideal capacitor as the
Sky130 MIM subcircuit with `--mim-cap-instance`; this opt-in conversion never
changes unrelated ideal capacitors.

The primitive's formal-terminal contract follows the official extraction
order: ALIGN `PLUS` (the first source capacitor node) reaches the contacted
CAPM top plate, while `MINUS` reaches the broad M4 bottom plate.  Static
contract tests reject a reversed plate assignment before layout.

## Getting started

### Step 1: Install ALIGN
Install ALIGN following instructions on [ALIGN GitHub Repository](https://github.com/ALIGN-analoglayout/ALIGN-public)

### Step 2: Clone the ALIGN PDK Sky130 source code to your local environment
```console
$ git clone https://github.com/ALIGN-analoglayout/ALIGN-pdk-sky130
```

### Step 3: Run ALIGN with Sky130
You may run the align tool using a simple command line tool named `schematic2layout.py`
For most common cases, you will simply run:
```console
$ schematic2layout.py <NETLIST_DIR> -p <PDK_DIR> 
```

For instance, to build the layout for five_transistor_ota. First make a directory in ALIGN-public (in this example `work`), thereafter, use `schematic2layout.py`: 
```console
$ cd ALIGN-public
$ mkdir work && cd work
$ schematic2layout.py ../ALIGN-pdk-sky130/examples/five_transistor_ota -p ../ALIGN-pdk-sky130/SKY130_PDK/
```
