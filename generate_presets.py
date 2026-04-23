#!/usr/bin/env python3
"""Preset generator / data exporter for Celestial Sim.

Two modes:

  python3 generate_presets.py export [--out presets.json]
      Dump the canonical preset table (matches PRESETS in sim.js) as JSON.

  python3 generate_presets.py random [--count N] [--seed S]
      Generate a new "stable cluster" preset — a heavy central body with
      N satellites on circular orbits, each with v = sqrt(G * M / r).
      Prints a JS-ready preset literal and a JSON representation.

The CLI banner ("Celestial Mechanics …") is pulled from strings.json so the
Python tool uses the same copy as the web UI.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STRINGS_PATH = HERE / "strings.json"

# Mirror of PRESETS in sim.js — keep in sync by hand, or regenerate via export.
CANONICAL_PRESETS = {
    "binary": {
        "bodies": [
            {"pos": [-1.0, 0.0], "vel": [0.0, -0.5], "mass": 1.0},
            {"pos": [ 1.0, 0.0], "vel": [0.0,  0.5], "mass": 1.0},
        ],
        "colors": ["#f6c667", "#ff7ab6"],
    },
    "figure8": {
        "bodies": [
            {"pos": [-0.97000436,  0.24308753], "vel": [ 0.466203685,  0.43236573], "mass": 1.0},
            {"pos": [ 0.97000436, -0.24308753], "vel": [ 0.466203685,  0.43236573], "mass": 1.0},
            {"pos": [ 0.0,         0.0        ], "vel": [-0.93240737,  -0.86473146], "mass": 1.0},
        ],
        "colors": ["#89c9ff", "#f6c667", "#ff7ab6"],
    },
    "solar": {
        "bodies": [
            {"pos": [ 0.0, 0.0], "vel": [ 0.0,    0.0   ], "mass": 20.0},
            {"pos": [ 1.5, 0.0], "vel": [ 0.0,    3.651 ], "mass":  0.3},
            {"pos": [-2.5, 0.0], "vel": [ 0.0,   -2.828 ], "mass":  0.6},
            {"pos": [ 0.0, 4.0], "vel": [-2.236,  0.0   ], "mass":  0.2},
        ],
        "colors": ["#f6c667", "#6be1c7", "#ff7ab6", "#c89bf5"],
    },
    "cluster": {
        "bodies": [
            {"pos": [-1.5, -0.8], "vel": [ 0.2,  0.4], "mass": 1.2},
            {"pos": [ 1.2,  0.9], "vel": [-0.3, -0.3], "mass": 0.9},
            {"pos": [ 0.3, -1.4], "vel": [-0.1,  0.2], "mass": 1.0},
            {"pos": [-0.8,  1.3], "vel": [ 0.4, -0.1], "mass": 0.7},
            {"pos": [ 1.8, -0.2], "vel": [-0.2,  0.1], "mass": 1.3},
        ],
        "colors": ["#89c9ff", "#f6c667", "#ff7ab6", "#80e0a3", "#c89bf5"],
    },
    "chaos": {
        "bodies": [
            {"pos": [-1.0,  0.5], "vel": [ 0.0,  0.3], "mass": 1.0},
            {"pos": [ 1.0,  0.0], "vel": [ 0.3, -0.2], "mass": 1.5},
            {"pos": [ 0.0, -1.0], "vel": [-0.4,  0.1], "mass": 0.8},
        ],
        "colors": ["#89c9ff", "#f6c667", "#ff7ab6"],
    },
}

PALETTE = ["#f6c667", "#89c9ff", "#ff7ab6", "#6be1c7", "#c89bf5", "#80e0a3"]


def load_strings() -> dict:
    try:
        return json.loads(STRINGS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def banner(strings: dict) -> None:
    brand = strings.get("app", {}).get("brand", "Celestial Sim")
    tagline = strings.get("app", {}).get("tagline", "")
    print(brand)
    if tagline:
        print(tagline)


def cmd_export(args: argparse.Namespace) -> int:
    args.out.write_text(json.dumps(CANONICAL_PRESETS, indent=2), encoding="utf-8")
    print(f"wrote {len(CANONICAL_PRESETS)} presets -> {args.out}")
    return 0


def circular_orbit_preset(count: int, rng: random.Random) -> dict:
    """Heavy central body + count satellites on circular orbits.

    For a circular orbit around a dominant central mass M at radius r:
        v = sqrt(G * M / r)    (G = 1 in sim units)
    """
    central_mass = rng.uniform(15.0, 25.0)
    bodies = [{
        "pos": [0.0, 0.0],
        "vel": [0.0, 0.0],
        "mass": round(central_mass, 3),
    }]
    for i in range(count):
        radius = 1.2 + i * 0.9 + rng.uniform(-0.1, 0.1)
        phase = rng.uniform(0.0, 2.0 * math.pi)
        speed = math.sqrt(central_mass / radius)
        # Velocity perpendicular to radius vector (counter-clockwise).
        bodies.append({
            "pos": [round(radius * math.cos(phase), 4),
                    round(radius * math.sin(phase), 4)],
            "vel": [round(-speed * math.sin(phase), 4),
                    round( speed * math.cos(phase), 4)],
            "mass": round(rng.uniform(0.15, 0.9), 3),
        })
    colors = [PALETTE[i % len(PALETTE)] for i in range(len(bodies))]
    return {"bodies": bodies, "colors": colors}


def cmd_random(args: argparse.Namespace) -> int:
    rng = random.Random(args.seed)
    preset = circular_orbit_preset(args.count, rng)
    print("# JSON")
    print(json.dumps(preset, indent=2))
    print()
    print("# JS literal (paste into sim.js PRESETS)")
    print("generated: {")
    print("  bodies: [")
    for b in preset["bodies"]:
        print(f"    {{ pos: [{b['pos'][0]:>8}, {b['pos'][1]:>8}], "
              f"vel: [{b['vel'][0]:>8}, {b['vel'][1]:>8}], "
              f"mass: {b['mass']} }},")
    print("  ],")
    print("  colors: [" + ", ".join(f"'{c}'" for c in preset["colors"]) + "],")
    print("},")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_export = sub.add_parser("export", help="dump canonical presets as JSON")
    p_export.add_argument("--out", type=Path, default=HERE / "presets.json")
    p_export.set_defaults(func=cmd_export)

    p_random = sub.add_parser("random", help="generate a random stable-orbit preset")
    p_random.add_argument("--count", type=int, default=4, help="satellites around the central body")
    p_random.add_argument("--seed", type=int, default=None)
    p_random.set_defaults(func=cmd_random)

    args = parser.parse_args()
    banner(load_strings())
    print()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
