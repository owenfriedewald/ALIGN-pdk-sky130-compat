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

The current import-time ALIGN streamout patch is transitional. The target
journal flow uses a pinned, rebuilt ALIGN source revision containing the
equivalent exporter fixes natively.

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
