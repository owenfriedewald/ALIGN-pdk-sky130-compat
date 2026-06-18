#!/usr/bin/env python3
"""Compare ALIGN Sky130 model aliases, example usage, and SkyWater doc names."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


MODEL_DEF_RE = re.compile(r"^\s*\.model\s+(\S+)\s+(\S+)", re.IGNORECASE)
MOS_INSTANCE_RE = re.compile(r"^\s*[mM]\S*\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)(?P<params>.*)$")
PARAM_RE = re.compile(r"(?<!\S)([A-Za-z_][A-Za-z0-9_]*)\s*=")
OFFICIAL_MODEL_RE = re.compile(r"sky130_fd_pr__[A-Za-z0-9_]+")


def align_models(path: Path) -> dict[str, str]:
    models: dict[str, str] = {}
    for line in path.read_text(errors="ignore").splitlines():
        match = MODEL_DEF_RE.match(line)
        if match:
            models[match.group(1)] = match.group(2)
    return models


def example_usage(paths: list[Path]) -> tuple[set[str], set[str]]:
    models: set[str] = set()
    params: set[str] = set()
    for path in paths:
        for line in path.read_text(errors="ignore").splitlines():
            match = MOS_INSTANCE_RE.match(line)
            if not match:
                continue
            models.add(match.group(1))
            params.update(name.lower() for name in PARAM_RE.findall(match.group("params")))
    return models, params


def official_names(paths: list[Path]) -> set[str]:
    names: set[str] = set()
    for path in paths:
        names.update(OFFICIAL_MODEL_RE.findall(path.read_text(errors="ignore")))
    return names


def load_alias_targets(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    aliases = data.get("model_aliases", {})
    if not isinstance(aliases, dict):
        return {}
    return {str(key): str(value) for key, value in aliases.items()}


def print_set(label: str, values: set[str]) -> None:
    print(f"{label} ({len(values)}):")
    for value in sorted(values):
        print(f"  - {value}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", type=Path, default=Path("SKY130_PDK/models.sp"))
    parser.add_argument(
        "--compat-map",
        type=Path,
        default=Path("SKY130_PDK/openpdks_compat.json"),
        help="Compatibility metadata JSON containing model_aliases.",
    )
    parser.add_argument("--examples", type=Path, default=Path("examples"), help="Directory of example SPICE files")
    parser.add_argument(
        "--official-docs",
        type=Path,
        default=Path("upstream/skywater-pdk/docs"),
        help="SkyWater docs directory to scan for official model-like names",
    )
    args = parser.parse_args()

    models = align_models(args.models)
    example_paths = sorted(args.examples.glob("**/*.sp")) if args.examples.exists() else []
    doc_paths = sorted(args.official_docs.glob("**/*")) if args.official_docs.exists() else []
    doc_paths = [path for path in doc_paths if path.is_file() and path.suffix in {".rst", ".csv", ".tsv"}]

    used_models, used_params = example_usage(example_paths)
    official = official_names(doc_paths)
    alias_targets = load_alias_targets(args.compat_map)

    print(f"ALIGN model file: {args.models}")
    print_set("ALIGN .model definitions", set(models))
    print_set("MOS models used by examples", used_models)
    print_set("Official-looking model names in SkyWater docs", official)
    print_set("MOS parameter names used by examples", used_params)

    aliases = {name for name in models if name not in official and not name.startswith("sky130_fd_pr__")}
    missing_defs = {name for name in used_models if name not in models}
    print_set("ALIGN aliases not seen as official SkyWater names", aliases)
    print("Compatibility alias targets:")
    for alias in sorted(aliases):
        print(f"  - {alias} -> {alias_targets.get(alias, '<no target>')}")
    print()
    print_set("Example MOS models missing from ALIGN models.sp", missing_defs)

    return 1 if missing_defs else 0


if __name__ == "__main__":
    raise SystemExit(main())
