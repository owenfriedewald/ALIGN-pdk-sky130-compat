# Verification Log

Date: 2026-06-18

| Command | Outcome |
|---|---|
| `pwd && rg --files -g '!*~' \| sed -n '1,200p'` | Passed. Confirmed repo root and top-level tracked/untracked files. |
| `find . -maxdepth 3 -type d \| sort \| sed -n '1,200p'` | Passed. Found `SKY130_PDK`, `context`, `examples`, and `upstream/skywater-pdk`. |
| `git status --short` | Passed. Pre-existing untracked `.gitignore`, `ALIGN SKY130 Diagnostic Report.md:Zone.Identifier`, and `upstream/` observed. |
| `find context -maxdepth 2 -type f -print` | Passed. Found `context/ALIGN SKY130 Diagnostic Report.md`. |
| `sed -n '1,260p' 'context/ALIGN Sky130 Diagnostic Report.md'` | Failed. Requested capitalization did not match existing filename. |
| `find SKY130_PDK -maxdepth 2 -type f -print \| sort` | Passed. Listed ALIGN-side PDK files. |
| `find upstream -maxdepth 2 -type d -print \| sort` | Passed. Found `upstream/skywater-pdk`; no `upstream/open_pdks`. |
| `sed -n '1,260p' 'context/ALIGN SKY130 Diagnostic Report.md'` | Passed. Read first part of diagnostic report. |
| `sed -n '261,560p' 'context/ALIGN SKY130 Diagnostic Report.md'` | Passed. Read remainder of diagnostic report. |
| `sed -n '1,220p' README.md` | Passed. Confirmed ALIGN-pdk-sky130 usage instructions. |
| `sed -n '1,220p' SKY130_PDK/layers.json` | Passed. Inspected primary layer/rule encoding. |
| `sed -n '221,520p' SKY130_PDK/layers.json` | Passed. Inspected remaining layers and helper entries. |
| `sed -n '1,240p' SKY130_PDK/models.sp` | Passed. Inspected model aliases. |
| `sed -n '1,240p' SKY130_PDK/mos.py` | Passed. Inspected MOS generator layer usage. |
| `sed -n '1,220p' SKY130_PDK/Align_primitives.py` | Passed. Inspected primitive generation entrypoint. |
| `find upstream -path '*sky130A.tech' -print` | Passed with no output. No Magic tech file found under `upstream/`. |
| `find upstream -path '*setup.tcl' -o -path '*sky130A_setup.tcl' -o -path '*sky130A.magicrc' ...` | Passed with no output. No Netgen/Magic setup files found. |
| `find upstream/skywater-pdk/libraries ...` | Passed with no output for shallow search. This SkyWater clone has docs but no obvious open_pdks-ready tech setup. |
| `rg -n 'gds\|GDS\|li1\|mcon\|via1...' upstream/skywater-pdk/docs/rules ...` | Passed. Produced large output; relevant rule CSVs identified. |
| `rg -n ... examples SKY130_PDK -g '*.sp' -g '*.py'` | Passed. Found mixed schematic model aliases and official Sky130 model names. |
| `sed -n '1,80p' upstream/skywater-pdk/docs/rules/layers/table-c4b-layer-description.csv` | Passed. Inspected layer descriptions and GDS references. |
| `sed -n '1,80p' ... p035-ct_dotdash.csv ... p038-m1_dotdash.csv ... p040-m2_dotdash.csv` | Passed. Confirmed mcon/met1/met2 rule values from SkyWater docs. |
| `sed -n '1,80p' ... p039-via_dotdash.csv ... p041-via2_dotdash.csv ... p043-via4_dotdash.csv` | Partially failed. `p043-via4_dotdash.csv` does not exist; via/via2 sections read. |
| `sed -n '1,80p' ... p042-via3_dotdash.csv` | Passed. Confirmed via3 cut/enclosure/spacing values. |
| `sed -n '1,80p' ... p044-via4_dotdash.csv` | Passed. Confirmed via4 cut/enclosure/spacing values. |
| `sed -n '1,80p' ... p035-li_dotdash_dotdash.csv` | Passed. Confirmed li1 width/spacing/area values. |
| `rg -n 'met5\|via4\|via3...' ... gds_layers.csv ...` | Passed. Located official GDS mapping lines. |
| `sed -n '1,45p' upstream/skywater-pdk/docs/rules/gds_layers.csv` | Passed. Confirmed official drawing-layer GDS pairs. |
| `find . -maxdepth 3 -type f \( -name '*.sh' -o -name '*.py' ... \)` | Passed. Confirmed no existing DRC/LVS/PEX scripts. |
| `find upstream -maxdepth 2 -type d -name 'open_pdks' -print` | Passed with no output. No open_pdks tree present. |
| `git ls-files` | Passed. Listed tracked project files. |
| `mkdir -p reports scripts tests/fixtures` | Passed. Created report/script/test directories. |
| `python3 scripts/compare_layer_map.py` | Passed. Main route/contact stack matched SkyWater GDS docs under ALIGN abstraction; helper layers skipped with notes. |
| `python3 scripts/normalize_netlist.py tests/fixtures/normalize_input.sp` | Passed. Printed expected normalized fixture to stdout. |
| `python3 -m py_compile scripts/compare_layer_map.py scripts/normalize_netlist.py` | Passed. Python syntax check clean. |
| `chmod +x scripts/compare_layer_map.py scripts/normalize_netlist.py` | Passed. Made helper scripts executable. |
| `python3 scripts/normalize_netlist.py tests/fixtures/normalize_input.sp -o /tmp/align_sky130_normalized_fixture.sp` | Passed. Wrote normalized fixture. |
| `diff -u tests/fixtures/normalize_expected.sp /tmp/align_sky130_normalized_fixture.sp` | Failed once because it was run in parallel before the output file existed. |
| `ls -l /tmp/align_sky130_normalized_fixture.sp` | Passed after rerun. Confirmed output file exists. |
| `diff -u tests/fixtures/normalize_expected.sp /tmp/align_sky130_normalized_fixture.sp` | Passed after sequential rerun. Fixture output matches expected. |
| `git diff --stat` | Passed with no output because all new files are currently untracked. |
| `git status --short` | Passed. New `scripts/`, `tests/`, and pre-existing untracked files reported. |
| `python3 scripts/compare_layer_map.py` | Passed in final verification. Main route/contact stack matched SkyWater GDS docs under ALIGN abstraction. |
| `python3 -m py_compile scripts/compare_layer_map.py scripts/normalize_netlist.py` | Passed in final verification. Generated `scripts/__pycache__`, later removed. |
| `python3 scripts/normalize_netlist.py tests/fixtures/normalize_input.sp -o /tmp/align_sky130_normalized_fixture.sp` | Passed in final verification. |
| `git diff --check` | Passed. Note: new files are untracked, so this only checks tracked diffs. |
| `diff -u tests/fixtures/normalize_expected.sp /tmp/align_sky130_normalized_fixture.sp` | Passed in final verification. |
| `find reports scripts tests -type f -print \| sort` | Passed. Revealed generated `scripts/__pycache__` files from `py_compile`. |
| `rm -rf scripts/__pycache__` | Passed with approval. Removed generated bytecode cache from verification. |
| `find upstream SKY130_PDK context examples -type f (...)` | Passed. Only `SKY130_PDK/models.sp` and `upstream/skywater-pdk/docs/rules/gds_layers.csv` matched exact runtime/reference filename patterns; no Magic tech/rc or Netgen setup found. |
| `find upstream/skywater-pdk -type f (...) \| rg ...` | Passed. Located relevant SkyWater verification docs, layer tables, rule CSVs, and device-detail docs. |
| `rg -n "sky130_fd_pr__\|\\.model\|\\.subckt..." SKY130_PDK examples upstream/skywater-pdk/docs ...` | Passed. Found ALIGN model definitions, example model usage, and official-looking SkyWater model names in docs. |
| `find upstream -maxdepth 3 -type d -iname '*open*' -o -iname '*pdks*'` | Passed with no output. No local `upstream/open_pdks` tree found. |
| `python3 scripts/check_verification_refs.py` | Expected failure. Reported missing Magic tech, Magic rc, Netgen setup Tcl, and Magic extraction runtime files; found SkyWater `gds_layers.csv`, docs, and local SPICE files. |
| `python3 scripts/compare_model_names.py` | Passed. Found 13 ALIGN `.model` definitions, 6 MOS model names used by examples, 10 ALIGN aliases not seen as official SkyWater names, and no example MOS models missing from `SKY130_PDK/models.sp`. |
| `python3 scripts/check_verification_refs.py --help && python3 scripts/compare_model_names.py --help && python3 scripts/normalize_netlist.py --help` | Passed. Help output available for new and existing helpers. |
| `chmod +x scripts/check_verification_refs.py scripts/compare_model_names.py` | Passed. Made new helper scripts executable. |
| `python3 scripts/check_verification_refs.py --help && python3 scripts/compare_model_names.py --help && python3 scripts/compare_layer_map.py --help && python3 scripts/normalize_netlist.py --help` | Passed. All helper scripts expose `--help`. |
| `python3 scripts/check_verification_refs.py` | Expected failure in final validation for missing required runtime files. |
| `python3 scripts/compare_model_names.py` | Passed in final validation. |
| `python3 -m py_compile scripts/check_verification_refs.py scripts/compare_model_names.py scripts/compare_layer_map.py scripts/normalize_netlist.py` | Passed. Generated `scripts/__pycache__`, later removed. |
| `python3 scripts/compare_layer_map.py` | Passed in final validation. Main route/contact stack matched SkyWater docs under ALIGN abstraction. |
| `python3 scripts/normalize_netlist.py tests/fixtures/normalize_input.sp -o /tmp/align_sky130_normalized_fixture.sp` | Passed in final validation. |
| `git diff --check` | Passed. Note: most current work is untracked, so this does not inspect untracked file content. |
| `find scripts -type d -name __pycache__ -print` | Found generated `scripts/__pycache__` after `py_compile`. |
| `rm -rf scripts/__pycache__` | Passed with approval. Removed generated bytecode cache. |
| `diff -u tests/fixtures/normalize_expected.sp /tmp/align_sky130_normalized_fixture.sp` | Passed. Normalizer fixture output matches expected output. |
| `find scripts -type d -name __pycache__ -print` | Passed with no output after cleanup. |
| `git status --short` | Passed at long-run start. Worktree had untracked prior reports/scripts/tests/upstream and `.gitignore`. |
| `git rev-parse HEAD` | Passed at long-run start. Starting commit: `0f04c647bf6767c79fb8f7eab1ac64306888b4db`. |
| `git branch --show-current` | Passed at long-run start. Initial branch before switch: `sky130-openpdks-verification-compat`. |
| `git switch -c sky130-compat-longrun` | Failed inside sandbox because `.git` ref writes were read-only. |
| `git switch -c sky130-compat-longrun` with escalation | Passed. Working branch for long run: `sky130-compat-longrun`. |
| `find . upstream reports examples outputs results SKY130_PDK -type f (...)` | Passed. No generated GDS/MAG files found; local SPICE examples and `SKY130_PDK/models.sp` found. |
| `find ~/data ~/share/pdk ~/data/pdk ~/data/open_pdks ~/pdks /usr/local/share/pdk /usr/share/pdk -maxdepth 5 -type f (...)` | Passed with no output. No common-path `sky130A.tech`, Magic rc, Netgen setup, GDS, or SPICE runtime files found. |
| `find ~/data ~/share/pdk ~/data/pdk ~/data/open_pdks ~/pdks /usr/local/share/pdk /usr/share/pdk -maxdepth 4 -type d (...)` | Passed with no output. No common-path open_pdks/sky130A install directory found. |
| `command -v magic; command -v netgen; command -v schematic2layout.py; command -v klayout; command -v python3` | Passed. Found `/usr/bin/klayout` and `/usr/bin/python3`; Magic, Netgen, and ALIGN CLI missing. |
| `python3 scripts/check_verification_refs.py --search-common` | Expected failure. Reported missing Magic, Netgen, ALIGN CLI, open_pdks runtime files, and generated GDS; found SkyWater docs/layer map and local SPICE files. |
| `chmod +x scripts/run_magic_drc.sh scripts/run_magic_extract.sh scripts/run_netgen_lvs.sh scripts/summarize_drc_log.py scripts/summarize_lvs_log.py ...` | Passed. Made helper scripts executable. |
| `bash -n scripts/run_magic_drc.sh scripts/run_magic_extract.sh scripts/run_netgen_lvs.sh` | Passed. Shell syntax clean. |
| `python3 -m py_compile scripts/check_verification_refs.py scripts/compare_layer_map.py scripts/compare_model_names.py scripts/normalize_netlist.py scripts/summarize_drc_log.py scripts/summarize_lvs_log.py` | Passed. Generated `scripts/__pycache__`, later removed. |
| `scripts/run_magic_drc.sh --help && scripts/run_magic_extract.sh --help && scripts/run_netgen_lvs.sh --help && scripts/summarize_drc_log.py --help && scripts/summarize_lvs_log.py --help` | Passed. New helpers expose usage/help. |
| `python3 scripts/normalize_netlist.py tests/fixtures/normalize_input.sp -o /tmp/align_sky130_normalized_fixture.sp && diff -u tests/fixtures/normalize_expected.sp /tmp/align_sky130_normalized_fixture.sp` | Passed. Default normalizer behavior preserved. |
| `python3 scripts/normalize_netlist.py examples/inverter/inverter.sp --drop-param stack -o /tmp/inverter.normalized.sp && sed -n '1,20p' /tmp/inverter.normalized.sp` | Passed. Inverter aliases normalized and `stack` dropped only when explicitly requested. |
| `python3 scripts/summarize_drc_log.py tests/fixtures/magic_drc_sample.log` | Passed. DRC summarizer reports count candidate and key rule lines from fixture. |
| `python3 scripts/summarize_lvs_log.py tests/fixtures/netgen_lvs_sample.log` | Passed. LVS summarizer reports key mismatch/property lines from fixture. |
| `chmod +x scripts/run_one_circuit_validation.sh && bash -n scripts/run_one_circuit_validation.sh` | Passed. One-command validation wrapper shell syntax clean. |
| `scripts/run_one_circuit_validation.sh --help` | Passed. Wrapper usage/help is available. |
| `bash -n scripts/run_magic_drc.sh scripts/run_magic_extract.sh scripts/run_netgen_lvs.sh scripts/run_one_circuit_validation.sh` | Passed in final validation. |
| `python3 -m py_compile scripts/check_verification_refs.py scripts/compare_layer_map.py scripts/compare_model_names.py scripts/normalize_netlist.py scripts/summarize_drc_log.py scripts/summarize_lvs_log.py` | Passed in final validation. Generated `scripts/__pycache__`, later removed. |
| `scripts/run_one_circuit_validation.sh --help && scripts/run_magic_drc.sh --help && scripts/run_magic_extract.sh --help && scripts/run_netgen_lvs.sh --help && python3 scripts/check_verification_refs.py --help && python3 scripts/normalize_netlist.py --help` | Passed in final validation. |
| `python3 scripts/check_verification_refs.py --search-common` | Expected failure in final validation because runtime tools/files are missing; found only docs/layer map/local SPICE files. |
| `python3 scripts/normalize_netlist.py tests/fixtures/normalize_input.sp -o /tmp/align_sky130_normalized_fixture.sp && diff -u tests/fixtures/normalize_expected.sp /tmp/align_sky130_normalized_fixture.sp` | Passed in final validation. |
| `python3 scripts/summarize_drc_log.py tests/fixtures/magic_drc_sample.log ... && python3 scripts/summarize_lvs_log.py tests/fixtures/netgen_lvs_sample.log ...` | Passed in final validation. |
| `git diff --check` | Passed in final validation. Note: new files are untracked, so this does not check untracked file content. |
| `find scripts -type d -name __pycache__ -print` | Found generated `scripts/__pycache__` after final `py_compile`. |
| `rm -rf scripts/__pycache__` | Passed with approval. Removed generated bytecode cache. |
| `rg -n "nfet_01v8_lvt\|pfet_01v8_lvt\|pfet_01v8_hvt\|nfet_01v8" upstream/skywater-pdk/docs/rules/device-details upstream/skywater-pdk/docs/contents -g '*.rst'` | Passed. Confirmed official LVT/HVT model names in SkyWater docs. |
| `sed -n ... nfet_01v8_lvt/index.rst ... pfet_01v8_lvt/index.rst ... pfet_01v8_hvt/index.rst` | Passed. Inspected official variant model documentation. |
| `python3 scripts/compare_layer_map.py && python3 scripts/compare_model_names.py` | Passed after adding `SKY130_PDK/openpdks_compat.json` and official model stubs. |
| `python3 scripts/normalize_netlist.py examples/inverter/inverter.sp --drop-param stack -o /tmp/inverter.normalized.sp` | Passed. Inverter now normalizes to official LVT FET model names and drops `stack` only when requested. |
| `rg -n "cap_mim_m3_1\|cap_mim_m3_2\|model__cap_mim\|cap_mim" upstream/skywater-pdk/docs SKY130_PDK examples ...` | Passed. Confirmed official MIM cap names in SkyWater docs and existing ALIGN cap stub. |
| `python3 -m json.tool SKY130_PDK/openpdks_compat.json` | Passed. Compatibility metadata JSON is valid. |
| `python3 -m py_compile ...` | Passed after compatibility metadata/model-normalizer updates. |
| `python3 scripts/inspect_spice.py examples/inverter/inverter.sp` | Passed. Reported inverter pins, two MOS instances, LVT aliases, and MOS params `l/nf/stack/w`. |
| `python3 scripts/inspect_spice.py examples/umich_test_case/umich_test_case.sp` | Passed. Reported hierarchical subckts, MOS/cap/X instance counts, and model references. |
| `python3 scripts/inspect_gds_layers.py --help && python3 scripts/inspect_spice.py --help` | Passed. Inspectors expose help text. |
| `python3 -m py_compile scripts/inspect_spice.py scripts/inspect_gds_layers.py` | Passed. |
| `python3 scripts/discover_validation_inputs.py --root . --limit 12` | Passed. Found example SPICE candidates and no GDS/open_pdks candidates; reported missing Magic/Netgen/ALIGN CLI. |
| `python3 scripts/discover_validation_inputs.py --help` | Passed. Discovery helper exposes help text. |
| `python3 -m py_compile scripts/discover_validation_inputs.py` | Passed. |
| `docker image ls --format ... \| rg -i 'align\|daarp\|layout\|iic\|osic\|sky130'` | Passed with escalation. Found `darpaalign/align-public:latest` and `hpretl/iic-osic-tools:latest`. |
| `docker run ... darpaalign/align-public:latest ... import align ... schematic2layout.py` | Passed. Confirmed ALIGN Python package and `schematic2layout.py` are available in Docker. |
| `docker run ... hpretl/iic-osic-tools:latest ... run_one_circuit_validation.sh ... --layout-top INVERTER_0 --schematic-top inverter` | Passed. Magic loaded real top, DRC reported 60 errors, extraction produced SPICE, Netgen ran and failed LVS. |
| `docker run ... inspect_gds_layers.py /tuple/generated/inverter.gds` | Passed. Confirmed `69:5` is an official met2 label and helper layers `100:5`, `104:0`, `235:5` are drop candidates. |
| `python3 scripts/compare_layer_map.py` | Passed after HVT patch. `Hvt` now maps to official `hvtp 78:44`. |
| `docker run ... schematic2layout.py ... generated_runs/inverter_input` | Passed. Regenerated inverter with `darpaalign/align-public:latest` and workspace `SKY130_PDK`. |
| `docker run ... inspect_gds_layers.py generated_runs/inverter_align/INVERTER_0.gds` | Passed. Regenerated GDS still emits helper layers, proving sanitizer/exporter fix is still needed. |
| `docker run ... schematic2layout.py ... after NoGDS helper-layer experiment` | Failed as useful evidence. ALIGN `gen_gds_json.py` requires `Bbox['GdsLayerNo']`; PDK-only removal of Bbox GDS mapping breaks generation. Reverted. |
| `docker run ... run_one_circuit_validation.sh ... inverter_nopex` | Passed. No-PEX LVS extraction removed parasitic capacitor count mismatch; layout had 120 MOS devices versus schematic 2 MOS devices. |
| `python3 scripts/normalize_netlist.py ... --expand-nf-stack --scale-wl-to-um` | Passed. Expanded inverter schematic to 120 physical MOS devices. |
| `docker run ... run_netgen_lvs.sh ... inverter.expanded.sp` | Passed. Netgen matched 120 devices and 564 nets on both sides, but top-level pin matching still failed. |
| `docker image ls` | Passed. Confirmed local `darpaalign/align-public:latest` and `hpretl/iic-osic-tools:latest` images. |
| `docker run ... python3 ... inspect align package path` | Passed. Installed ALIGN source path is `/usr/local/lib/python3.10/dist-packages/align`; `schematic2layout.py` is `/usr/local/bin/schematic2layout.py`. |
| `docker run ... nl -ba /usr/local/lib/python3.10/dist-packages/align/cell_fabric/gen_gds_json.py` | Passed. Confirmed Python GDS exporter unconditionally appended `Bbox` and streamed all terminal layers by `GdsLayerNo`. |
| `python3 -m py_compile scripts/patch_align_gds_export.py ...` | Passed. New ALIGN exporter patch helper compiles. |
| `python3 scripts/patch_align_gds_export.py --help` | Passed. Help output available. |
| `docker run ... scripts/patch_align_gds_export.py ... schematic2layout.py ...` | First attempt failed because ALIGN requires the working directory to exist. Useful setup evidence. |
| `docker run ... scripts/patch_align_gds_export.py ... mkdir -p generated_runs/inverter_align_nogds_patch ... schematic2layout.py ...` | Passed through generation. Inspection inside ALIGN image failed only because KLayout Python is unavailable in that image. |
| `docker run ... hpretl/iic-osic-tools ... inspect_gds_layers.py generated_runs/inverter_align_nogds_patch/INVERTER_0.gds` | Passed. Default PnR GDS still contains `104:0` and `235:5`, but no longer contains `100:5`. |
| `python3 JSON walker on generated_runs/inverter_align_nogds_patch/**/*.gds.json` | Passed. Remaining `104:0` and `235:5` occur in `3_pnr/Results/*.gds.json`, not primitive Python stream-out. |
| `docker run ... grep ALIGN runtime for Outline/boundary` | Passed. Found `align/pnr/main.py` explicitly inserts top-level `Outline`; no Python text source for `235` found, suggesting downstream writer behavior. |
| `docker run ... inspect_gds_layers.py generated_runs/inverter_align_nogds_patch/INVERTER_0.python.gds` | Passed. Patched Python stream-out contains no `100:5`, `104:0`, or `235:5`; it contains official SkyWater electrical layers plus met2 label/pin layers. |
| `docker run ... run_one_circuit_validation.sh --gds generated_runs/inverter_align_nogds_patch/INVERTER_0.python.gds --layout-top INVERTER --schematic ... --no-sanitize-gds --expand-nf-stack --scale-wl-to-um` | Passed. Magic import had no unknown helper-layer errors, DRC reported 60 errors, extraction produced SPICE, Netgen matched 120 devices/564 nets on both sides but LVS still failed. |
| `docker run ... schematic2layout.py ... generated_runs/inverter_align_no_lvt_marker` | Passed. Regenerated inverter after removing `LVT` from `design_info.vt_type`; output includes `generated_runs/inverter_align_no_lvt_marker/INVERTER_0.python.gds`. |
| `docker run ... run_one_circuit_validation.sh ... inverter_no_lvt_marker --no-sanitize-gds --expand-nf-stack --scale-wl-to-um` | Passed. Magic DRC reported `Total DRC errors found: 0`; extraction produced SPICE; LVS still failed because schematic model classes remained LVT while layout extracted regular 1.8V FETs. |
| `docker run ... normalize_netlist.py ... --coerce-lvt-to-rvt ... run_netgen_lvs.sh ... inverter_no_lvt_marker_rvt_lvs` | Passed. Netgen reached 120 devices on both sides and equivalent RVT model classes, but LVS still failed due to schematic primitive MOS syntax versus Magic extracted subckt syntax. |
| `docker run ... normalize_netlist.py ... --coerce-lvt-to-rvt --mos-as-subckt --uppercase-nets ... run_netgen_lvs.sh ... inverter_no_lvt_marker_xsubckt_lvs` | Passed. LVS-only experiment matched uniquely: 120 devices, 84 nets, `Final result: Circuits match uniquely.` |
| `docker run ... run_one_circuit_validation.sh ... inverter_no_lvt_marker_xsubckt_full --no-sanitize-gds --expand-nf-stack --scale-wl-to-um --coerce-lvt-to-rvt --mos-as-subckt --uppercase-nets` | Passed. Full flow is clean for bounded inverter experiment: Magic DRC `Total DRC errors found: 0`; Netgen LVS `Final result: Circuits match uniquely.` |
| `docker run ... schematic2layout.py ... generated_runs/buffer_align_no_lvt_marker` | Passed. Generated buffer `.python.gds` with clean official electrical/pin/label layers. |
| `docker run ... run_one_circuit_validation.sh ... buffer_xsubckt_full --no-sanitize-gds --expand-nf-stack --scale-wl-to-um --mos-as-subckt --uppercase-nets` | Passed with useful LVS failure. Magic DRC reported zero errors and topology matched, but Netgen failed top-level pin matching because an internal `OUT1` node was extracted as a top-level port. |
| `docker run ... inspect ALIGN pnr/main.py and Pdk API` | Passed. Found `labels = [i.name for i in hN.blockPins].extend(...)` bug and confirmed `Pdk` is dict-like via `.items()` but has no `.get()`. |
| `python3 -m py_compile scripts/patch_align_gds_export.py` | Passed after extending the runtime patcher to patch `pnr/main.py`. |
| `docker run ... schematic2layout.py ... generated_runs/buffer_align_label_patch` | Passed. Regenerated buffer after runtime patcher fixed top-level label filtering. |
| `docker run ... run_one_circuit_validation.sh ... buffer_label_patch_xsubckt_full --no-sanitize-gds --expand-nf-stack --scale-wl-to-um --mos-as-subckt --uppercase-nets` | Passed. Full flow is clean for buffer: Magic DRC `Total DRC errors found: 0`; Netgen LVS `Final result: Circuits match uniquely.` |
