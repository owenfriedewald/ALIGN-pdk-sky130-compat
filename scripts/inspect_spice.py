#!/usr/bin/env python3
"""Inspect SPICE subcircuits, pins, instance models, and parameters."""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from pathlib import Path


SUBCKT_RE = re.compile(r"^\s*\.subckt\s+(\S+)(?P<pins>.*)$", re.IGNORECASE)
ENDS_RE = re.compile(r"^\s*\.ends\b", re.IGNORECASE)
MOS_RE = re.compile(r"^\s*[mM]\S*\s+\S+\s+\S+\s+\S+\s+\S+\s+(?P<model>\S+)(?P<params>.*)$")
CAP_RE = re.compile(r"^\s*[cC]\S*\s+\S+\s+\S+\s+(?P<value>\S+)(?P<params>.*)$")
X_RE = re.compile(r"^\s*[xX]\S+(?P<body>.*)$")
PARAM_RE = re.compile(r"(?<!\S)([A-Za-z_][A-Za-z0-9_]*)\s*=")


def inspect(path: Path) -> dict:
    subckts: dict[str, list[str]] = {}
    current: str | None = None
    instance_counts: Counter[str] = Counter()
    models: Counter[str] = Counter()
    params: dict[str, Counter[str]] = defaultdict(Counter)

    for raw in path.read_text(errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("*"):
            continue
        subckt = SUBCKT_RE.match(line)
        if subckt:
            current = subckt.group(1)
            subckts[current] = subckt.group("pins").split()
            continue
        if ENDS_RE.match(line):
            current = None
            continue

        prefix = line[0].lower()
        if prefix in {"m", "c", "x", "r", "l", "d", "q"}:
            instance_counts[prefix] += 1

        mos = MOS_RE.match(line)
        if mos:
            model = mos.group("model")
            models[model] += 1
            params["mos"].update(name.lower() for name in PARAM_RE.findall(mos.group("params")))
            continue

        cap = CAP_RE.match(line)
        if cap:
            params["cap"].update(name.lower() for name in PARAM_RE.findall(cap.group("params")))
            continue

        xinst = X_RE.match(line)
        if xinst:
            body = xinst.group("body").split()
            if body:
                models[body[-1]] += 1

    return {
        "subckts": subckts,
        "instance_counts": instance_counts,
        "models": models,
        "params": params,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spice", type=Path)
    args = parser.parse_args()

    data = inspect(args.spice)
    print(f"SPICE: {args.spice}")
    print("Subcircuits:")
    for name, pins in data["subckts"].items():
        print(f"  - {name}: pins={' '.join(pins) if pins else '<none>'}")
    print("Instance counts:")
    for kind, count in sorted(data["instance_counts"].items()):
        print(f"  - {kind}: {count}")
    print("Models/subckt references:")
    for model, count in sorted(data["models"].items()):
        print(f"  - {model}: {count}")
    print("Parameters:")
    for group, counter in sorted(data["params"].items()):
        values = ", ".join(f"{name}({count})" for name, count in sorted(counter.items()))
        print(f"  - {group}: {values}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
