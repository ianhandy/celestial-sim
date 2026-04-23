#!/usr/bin/env python3
"""Generate a JSON file of initial celestial bodies for the sim.

All user-facing text is sourced from strings.json so the CLI messages stay
consistent with the web UI. Keys used: `app.title`, `app.tagline`,
`errors.stringsLoadFailed`.

Usage:
    python3 generate_bodies.py [--count N] [--out bodies.json] [--seed S]
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
DEFAULT_OUT = HERE / "bodies.json"

G = 1.0
STAR_MASS = 20_000.0
CENTER = (450.0, 300.0)


def load_strings() -> dict:
    try:
        with STRINGS_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as err:
        print(f"[warn] could not read {STRINGS_PATH.name}: {err}", file=sys.stderr)
        return {
            "app": {"title": "Celestial Sim", "tagline": ""},
            "errors": {"stringsLoadFailed": "Failed to load strings.json."},
        }


def t(strings: dict, dotted: str, fallback: str = "") -> str:
    node = strings
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node:
            return fallback
        node = node[key]
    return node if isinstance(node, str) else fallback


def circular_orbit(radius: float, phase: float, mass: float, color: str) -> dict:
    cx, cy = CENTER
    speed = math.sqrt(G * STAR_MASS / radius)
    return {
        "x": cx + radius * math.cos(phase),
        "y": cy + radius * math.sin(phase),
        "vx": -speed * math.sin(phase),
        "vy":  speed * math.cos(phase),
        "m": mass,
        "r": max(2.0, mass ** (1 / 3) * 0.9),
        "color": color,
    }


def generate(count: int, rng: random.Random) -> list[dict]:
    palette = ["#9fd3ff", "#c5a0ff", "#7fe0a6", "#ff9f9f", "#ffd27a", "#b0b9ff"]
    bodies = [{
        "x": CENTER[0], "y": CENTER[1],
        "vx": 0.0, "vy": 0.0,
        "m": STAR_MASS, "r": 14.0,
        "color": "#ffd27a",
    }]
    for i in range(count):
        radius = 70 + i * 45 + rng.uniform(-10, 10)
        phase = rng.uniform(0, 2 * math.pi)
        mass = rng.uniform(5, 40)
        color = palette[i % len(palette)]
        bodies.append(circular_orbit(radius, phase, mass, color))
    return bodies


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate initial bodies for Celestial Sim.")
    parser.add_argument("--count", type=int, default=5, help="number of orbiting bodies")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output JSON path")
    parser.add_argument("--seed", type=int, default=None, help="random seed for reproducibility")
    args = parser.parse_args()

    strings = load_strings()
    print(t(strings, "app.title", "Celestial Sim"))
    tagline = t(strings, "app.tagline")
    if tagline:
        print(tagline)

    rng = random.Random(args.seed)
    bodies = generate(args.count, rng)

    args.out.write_text(json.dumps(bodies, indent=2), encoding="utf-8")
    print(f"wrote {len(bodies)} bodies -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
