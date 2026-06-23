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
    r"^(?P<indent>\s*)(?P<name>[mM]\S*)\s+(?P<d>\S+)\s+(?P<g>\S+)\s+(?P<s>\S+)\s+(?P<b>\S+)\s+(?P<model>\S+)(?P<suffix>(?:\s+.*)?$)"
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


def params_to_dict(suffix: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for token in suffix.split():
        match = PARAM_RE.fullmatch(token)
        if match:
            values[match.group("name").lower()] = match.group("value")
    return values


def parse_number(value: str) -> float | None:
    suffixes = {
        "f": 1e-15,
        "p": 1e-12,
        "n": 1e-9,
        "u": 1e-6,
        "m": 1e-3,
        "k": 1e3,
        "meg": 1e6,
        "g": 1e9,
    }
    lowered = value.strip().lower()
    for suffix, scale in sorted(suffixes.items(), key=lambda item: -len(item[0])):
        if lowered.endswith(suffix):
            try:
                return float(lowered[: -len(suffix)]) * scale
            except ValueError:
                return None
    try:
        return float(lowered)
    except ValueError:
        return None


def format_um(value: str) -> str:
    number = parse_number(value)
    if number is None:
        return value
    # ALIGN examples use SI meters; Magic extraction reports micron-valued w/l.
    if abs(number) < 0.01:
        number *= 1e6
    return f"{number:.12g}"


def normalize_wl_units(suffix: str) -> str:
    tokens: list[str] = []
    for token in suffix.split():
        match = PARAM_RE.fullmatch(token)
        if not match:
            tokens.append(token)
            continue
        name = match.group("name")
        value = match.group("value")
        if name.lower() in {"w", "l"}:
            value = format_um(value)
        tokens.append(f"{name}={value}")
    return (" " + " ".join(tokens)) if tokens else ""


def expand_mos_instance(match: re.Match[str], model: str, suffix: str) -> str | None:
    params = params_to_dict(suffix)
    try:
        nf = int(float(params.get("nf", "1")))
        stack = int(float(params.get("stack", "1")))
    except ValueError:
        return None
    if nf <= 1 and stack <= 1:
        return None

    kept_suffix = normalize_params(suffix, {"nf", "stack"}, {})
    kept_suffix = normalize_wl_units(kept_suffix)
    lines: list[str] = []
    for finger in range(nf):
        previous = match.group("d")
        for segment in range(stack):
            next_node = match.group("s") if segment == stack - 1 else f"{match.group('name')}_nf{finger}_s{segment}"
            lines.append(
                f"{match.group('indent')}{match.group('name')}_nf{finger}_stk{segment} "
                f"{previous} {match.group('g')} {next_node} {match.group('b')} {model}{kept_suffix}\n"
            )
            previous = next_node
    return "".join(lines)


def normalize_line(
    line: str,
    model_aliases: dict[str, str],
    drop_params: set[str],
    rename_params: dict[str, str],
    expand_nf_stack: bool,
    scale_wl_to_um: bool,
) -> str:
    if not line.strip() or line.lstrip().startswith(("*", ".", "+")):
        return line
    match = MOS_RE.match(line.rstrip("\n"))
    if not match:
        return line
    model = match.group("model")
    replacement = model_aliases.get(model.lower())
    suffix = normalize_params(match.group("suffix"), drop_params, rename_params)
    if scale_wl_to_um:
        suffix = normalize_wl_units(suffix)
    if expand_nf_stack:
        expanded = expand_mos_instance(match, replacement or model, suffix)
        if expanded is not None:
            return expanded
    if not replacement and suffix == match.group("suffix"):
        return line
    return (
        f"{match.group('indent')}{match.group('name')} {match.group('d')} {match.group('g')} "
        f"{match.group('s')} {match.group('b')} {replacement or model}{suffix}\n"
    )


def normalize_text(
    text: str,
    model_aliases: dict[str, str] | None = None,
    drop_params: set[str] | None = None,
    rename_params: dict[str, str] | None = None,
    expand_nf_stack: bool = False,
    scale_wl_to_um: bool = False,
) -> str:
    model_aliases = model_aliases or MODEL_ALIASES
    drop_params = drop_params or set()
    rename_params = rename_params or {}
    return "".join(
        normalize_line(line, model_aliases, drop_params, rename_params, expand_nf_stack, scale_wl_to_um)
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
    parser.add_argument(
        "--expand-nf-stack",
        action="store_true",
        help="Expand MOS nf/stack parameters into explicit physical series devices for LVS experiments.",
    )
    parser.add_argument(
        "--scale-wl-to-um",
        action="store_true",
        help="Convert small SI-meter w/l values to micron-valued w/l to match Magic extraction style.",
    )
    args = parser.parse_args()

    rename_params = parse_rename(args.rename_param)
    model_aliases = load_model_aliases(args.compat_map if args.compat_map.exists() else None)
    normalized = normalize_text(
        args.input.read_text(),
        model_aliases=model_aliases,
        drop_params={name.lower() for name in args.drop_param},
        rename_params=rename_params,
        expand_nf_stack=args.expand_nf_stack,
        scale_wl_to_um=args.scale_wl_to_um,
    )
    if args.output:
        args.output.write_text(normalized)
    else:
        sys.stdout.write(normalized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
