#!/usr/bin/env python3
"""Normalize simple ALIGN Sky130 SPICE dialect differences for LVS experiments."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


MODEL_ALIASES = {
    "nmos_rvt": "sky130_fd_pr__nfet_01v8",
    "nmos_lvt": "sky130_fd_pr__nfet_01v8_lvt",
    "nmos_hvt": "sky130_fd_pr__nfet_01v8",
    "nfet": "sky130_fd_pr__nfet_01v8",
    "pmos_rvt": "sky130_fd_pr__pfet_01v8",
    "pmos_lvt": "sky130_fd_pr__pfet_01v8_lvt",
    "pmos_hvt": "sky130_fd_pr__pfet_01v8_hvt",
    "pfet": "sky130_fd_pr__pfet_01v8",
    "sky130_fd_pr__cap_mim_m3_1": "sky130_fd_pr__cap_mim_m3_1",
}

MOS_RE = re.compile(
    r"^(?P<prefix>\s*[mM]\S*\s+\S+\s+\S+\s+\S+\s+\S+\s+)(?P<model>\S+)(?P<suffix>(?:\s+.*)?$)"
)
PARAM_RE = re.compile(r"(?<!\S)(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>[^ \t]+)")


def parse_rename(values: list[str]) -> dict[str, str]:
    renames: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise argparse.ArgumentTypeError(f"Expected OLD=NEW, got {value!r}")
        old, new = value.split("=", 1)
        renames[old.lower()] = new
    return renames


def load_model_aliases(path: Path | None) -> dict[str, str]:
    if path is None:
        return MODEL_ALIASES
    data = json.loads(path.read_text())
    aliases = data.get("model_aliases")
    if not isinstance(aliases, dict):
        raise ValueError(f"No model_aliases object found in {path}")
    return {str(key).lower(): str(value) for key, value in aliases.items()}


def normalize_params(suffix: str, drop: set[str], rename: dict[str, str]) -> str:
    if not suffix.strip() or (not drop and not rename):
        return suffix

    tokens = suffix.split()
    kept: list[str] = []
    for token in tokens:
        match = PARAM_RE.fullmatch(token)
        if not match:
            kept.append(token)
            continue
        name = match.group("name")
        value = match.group("value")
        lowered = name.lower()
        if lowered in drop:
            continue
        kept.append(f"{rename.get(lowered, name)}={value}")
    return (" " + " ".join(kept)) if kept else ""


def normalize_line(
    line: str,
    model_aliases: dict[str, str],
    drop_params: set[str],
    rename_params: dict[str, str],
) -> str:
    if not line.strip() or line.lstrip().startswith(("*", ".", "+")):
        return line
    match = MOS_RE.match(line.rstrip("\n"))
    if not match:
        return line
    model = match.group("model")
    replacement = model_aliases.get(model.lower())
    suffix = normalize_params(match.group("suffix"), drop_params, rename_params)
    if not replacement and suffix == match.group("suffix"):
        return line
    return f"{match.group('prefix')}{replacement or model}{suffix}\n"


def normalize_text(
    text: str,
    model_aliases: dict[str, str] | None = None,
    drop_params: set[str] | None = None,
    rename_params: dict[str, str] | None = None,
) -> str:
    model_aliases = model_aliases or MODEL_ALIASES
    drop_params = drop_params or set()
    rename_params = rename_params or {}
    return "".join(
        normalize_line(line, model_aliases, drop_params, rename_params)
        for line in text.splitlines(keepends=True)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Input SPICE netlist")
    parser.add_argument("-o", "--output", type=Path, help="Output path; defaults to stdout")
    parser.add_argument(
        "--compat-map",
        type=Path,
        default=Path("SKY130_PDK/openpdks_compat.json"),
        help="Compatibility metadata JSON containing model_aliases.",
    )
    parser.add_argument(
        "--drop-param",
        action="append",
        default=[],
        help="Drop a MOS instance parameter by name. Repeatable. Example: --drop-param stack",
    )
    parser.add_argument(
        "--rename-param",
        action="append",
        default=[],
        help="Rename a MOS instance parameter as OLD=NEW. Repeatable.",
    )
    args = parser.parse_args()

    rename_params = parse_rename(args.rename_param)
    model_aliases = load_model_aliases(args.compat_map if args.compat_map.exists() else None)
    normalized = normalize_text(
        args.input.read_text(),
        model_aliases=model_aliases,
        drop_params={name.lower() for name in args.drop_param},
        rename_params=rename_params,
    )
    if args.output:
        args.output.write_text(normalized)
    else:
        sys.stdout.write(normalized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
