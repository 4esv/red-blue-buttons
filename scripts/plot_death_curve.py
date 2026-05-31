"""Render the death-vs-trust curve as a standalone SVG, straight from the model.

The curve is the exact death rate of a population at trust t (a uniform world
at that trust): deaths = blue_fraction(t) while that is below 0.5 (blue loses,
every blue presser dies), then a cliff to zero at the critical trust where blue
crosses 50% and everyone survives. Every surveyed country sits exactly on the
curve, because each country is modelled as a population at its own trust, so its
death rate IS curve(its trust). Flags mark where each nation lands.

    python -m scripts.plot_death_curve            # -> figures/death-curve.svg

Transparent background, aesv.io page colors (ink / brick / sage), mono labels.
Country markers are Unicode flag emoji (degrade to two-letter codes on platforms
without flag glyphs, e.g. Windows). Output is inline-pasteable into the article.
"""

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.model import blue_fraction, critical_trust, ALTRUISM, LAMBDA

# aesv.io foundation.css tokens
INK = "#1a1a1a"
INK_MUTE = "#5c5650"
BRICK = "#a84a3c"
SAGE = "#6b8576"
LAVENDER = "#6e6291"
GRID = "#e8dfc8"
INK_FAINT = "#bdb6a8"
# Birdie is the site display/body face, loaded via @font-face in foundation.css.
# It only resolves when the SVG is inlined in the page (an <img>-loaded SVG can't
# reach the page's fonts), so this figure is meant to be pasted inline, not linked.
FONT = "'Birdie', system-ui, sans-serif"

W, H = 760, 400
L, R, T, B = 66, 20, 22, 46
X0, X1 = L, W - R
Y0, Y1 = T, H - B
Y_MAX = 0.50  # top of the y-axis = 50% deaths


def xmap(t):
    return X0 + t * (X1 - X0)


def ymap(d):
    return Y1 - (d / Y_MAX) * (Y1 - Y0)


def flag(iso2):
    return "".join(chr(0x1F1E6 + ord(c) - ord("a")) for c in iso2.lower())


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg():
    data = json.loads((REPO / "data" / "countries.json").read_text())
    countries = data["countries"]
    entries = countries + [data["rest_of_world"]]
    ct = critical_trust()  # ~0.776

    # Curve samples on the doomed (rising) side, up to the cliff.
    ts = np.linspace(0.0, ct, 160)
    rising = [(xmap(t), ymap(blue_fraction(float(t)))) for t in ts]

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'style="display:block;width:100%;height:auto" '
        f'font-family="{FONT}" role="img" '
        f'aria-label="Death rate versus trust. Deaths climb with trust to nearly half '
        f'the population just below 77.6 percent trust, then drop to zero once a '
        f'population crosses the blue-wins majority. Every surveyed country sits on the '
        f'rising side; none reach the safe zone.">'
    )

    # Safe zone past the cliff: blue clears the majority, nobody dies.
    xc_zone = xmap(ct)
    parts.append(
        f'<rect x="{xc_zone:.1f}" y="{Y0}" width="{X1 - xc_zone:.1f}" '
        f'height="{Y1 - Y0}" fill="{LAVENDER}" opacity="0.12"/>'
    )
    parts.append(
        f'<text x="{(xc_zone + X1) / 2:.1f}" y="{(Y0 + Y1) / 2:.0f}" fill="{LAVENDER}" '
        f'font-size="15" text-anchor="middle">Blue &gt;50%</text>'
    )

    # Gridlines + axis ticks.
    for gx in [0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        x = xmap(gx)
        parts.append(f'<line x1="{x:.1f}" y1="{Y0}" x2="{x:.1f}" y2="{Y1}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(
            f'<text x="{x:.1f}" y="{Y1 + 16}" fill="{INK_MUTE}" font-size="11" '
            f'text-anchor="middle">{int(gx * 100)}%</text>'
        )
    for gy in [0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        y = ymap(gy)
        parts.append(f'<line x1="{X0}" y1="{y:.1f}" x2="{X1}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        parts.append(
            f'<text x="{X0 - 8}" y="{y + 3:.1f}" fill="{INK_MUTE}" font-size="11" '
            f'text-anchor="end">{int(gy * 100)}%</text>'
        )

    # Axes.
    parts.append(f'<line x1="{X0}" y1="{Y1}" x2="{X1}" y2="{Y1}" stroke="{INK}" stroke-width="1.5"/>')
    parts.append(f'<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1}" stroke="{INK}" stroke-width="1.5"/>')

    # The cliff: vertical drop at critical trust to zero deaths.
    xc = xmap(ct)
    parts.append(
        f'<line x1="{xc:.1f}" y1="{ymap(0.5):.1f}" x2="{xc:.1f}" y2="{ymap(0):.1f}" '
        f'stroke="{BRICK}" stroke-width="2" stroke-dasharray="4 3"/>'
    )

    # Rising death curve.
    d = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in rising)
    parts.append(f'<path d="{d}" fill="none" stroke="{BRICK}" stroke-width="2.5"/>')

    # Cliff annotation.
    parts.append(
        f'<text x="{xc - 6:.1f}" y="{Y0 + 12}" fill="{INK_MUTE}" font-size="11" '
        f'text-anchor="end">{ct * 100:.1f}%</text>'
    )

    # Country flags, exactly on the curve. Nudge known exact-trust collisions apart.
    nudges = {"CAN": -13, "TUR": -13}  # Canada vs Germany; Turkey vs Mexico
    for c in countries:
        t = c["trust"]
        d_ = blue_fraction(t)
        cx, cy = xmap(t), ymap(d_)
        parts.append(
            f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx:.1f}" y2="{Y1}" '
            f'stroke="{INK_FAINT}" stroke-width="1" stroke-dasharray="1 3"/>'
        )
        fy = cy + nudges.get(c["code"], 0)
        parts.append(
            f'<text x="{cx:.1f}" y="{fy - 7:.1f}" font-size="17" text-anchor="middle">'
            f'{flag(c["iso2"])}</text>'
        )

    # World: the population-weighted aggregate. It sits ABOVE the curve:
    # mixing trust levels kills more than the average trust alone would, since
    # the high-trust tail still presses blue. 🌍 marks the real (trust, rate).
    tot = sum(e["population"] for e in entries)
    w_trust = sum(e["trust"] * e["population"] for e in entries) / tot
    w_rate = sum(blue_fraction(e["trust"]) * e["population"] for e in entries) / tot
    wx, wy = xmap(w_trust), ymap(w_rate)
    parts.append(
        f'<line x1="{wx:.1f}" y1="{wy:.1f}" x2="{wx:.1f}" y2="{Y1}" '
        f'stroke="{INK_FAINT}" stroke-width="1" stroke-dasharray="1 3"/>'
    )
    parts.append(
        f'<text x="{wx:.1f}" y="{wy - 7:.1f}" font-size="17" text-anchor="middle">🌍</text>'
    )

    # Axis titles.
    parts.append(
        f'<text x="{(X0 + X1) / 2:.0f}" y="{H - 6}" fill="{INK}" font-size="12" '
        f'text-anchor="middle">← trust →</text>'
    )
    parts.append(
        f'<text x="14" y="{(Y0 + Y1) / 2:.0f}" fill="{INK}" font-size="12" '
        f'text-anchor="middle" transform="rotate(-90 14 {(Y0 + Y1) / 2:.0f})">'
        f'death toll</text>'
    )

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    svg = build_svg()
    out = REPO / "figures" / "death-curve.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)
    print(f"saved {out}  ({len(svg):,} bytes)")
    print(f"critical trust (cliff): {critical_trust() * 100:.1f}%  "
          f"(altruism={ALTRUISM}, lambda={LAMBDA})")
