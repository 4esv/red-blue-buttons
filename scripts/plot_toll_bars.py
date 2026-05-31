"""Per-country death-toll bars. Each bar is one country (full width = its whole
population), split into the share that DIES (blue / lavender, the blue-pressers)
and the share that SURVIVES (red / brick, the red-pressers), the same colors as
the button pictograms. Sorted by death rate, least to most, with the absolute
death toll labelled in blue at the end of each bar.

No bar's blue reaches the 50% line: a country whose blue share crossed it would
win the majority and lose nobody.

    python -m scripts.plot_toll_bars            # -> figures/toll-bars.svg

Transparent background, aesv.io tokens, Birdie (resolves when inlined in page).
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.model import blue_fraction

INK = "#1a1a1a"
INK_MUTE = "#5c5650"
DIE = "#6e6291"        # --lavender, the blue button: blue-pressers who die
SURVIVE = "#a84a3c"    # --brick, the red button: red-pressers who live
INK_FAINT = "#bdb6a8"
FONT = "'Birdie', system-ui, sans-serif"

W = 540            # compact viewBox so the dense chart stays legible at the
ROW_H = 21         # graph's width and downscales gently on a phone
TOP = 30
BOT = 14
BAR_X0 = 152       # left edge of bars (after flag + name + rate)
BAR_W = 316        # full-width bar = 100% of population
LABEL_X = BAR_X0 + BAR_W + 8


def flag(iso2):
    return "".join(chr(0x1F1E6 + ord(c) - ord("a")) for c in iso2.lower())


def human(x):
    if x >= 1e9:
        return f"{x / 1e9:.2f}B"
    if x >= 1e7:
        return f"{x / 1e6:.0f}M"
    if x >= 1e6:
        return f"{x / 1e6:.1f}M"
    if x >= 1e4:
        return f"{x / 1e3:.0f}k"
    if x >= 1e3:
        return f"{x / 1e3:.1f}k"
    return f"{x:.0f}"


def rate_label(r):
    pct = r * 100
    if pct >= 1:
        return f"{pct:.0f}%"
    if pct >= 0.1:
        return f"{pct:.1f}%"
    return "&lt;0.1%"  # escaped: written straight into SVG text


def build_svg():
    data = json.loads((REPO / "data" / "countries.json").read_text())
    cs = data["countries"]
    entries = cs + [data["rest_of_world"]]
    rows = []
    for c in cs:
        r = blue_fraction(c["trust"])
        rows.append({"name": c["name"], "glyph": flag(c["iso2"]), "rate": r,
                     "pop": c["population"], "deaths": r * c["population"]})
    # World: the population-weighted aggregate (includes the rest-of-world bucket).
    tot = sum(e["population"] for e in entries)
    w_rate = sum(blue_fraction(e["trust"]) * e["population"] for e in entries) / tot
    rows.append({"name": "World", "glyph": "🌍", "rate": w_rate,
                 "pop": tot, "deaths": w_rate * tot})
    rows.sort(key=lambda x: x["deaths"])  # least total loss at top

    H = TOP + ROW_H * len(rows) + BOT
    x50 = BAR_X0 + BAR_W * 0.5
    p = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'style="display:block;width:100%;height:auto" font-family="{FONT}" role="img" '
        f'aria-label="Per-country death toll. Each bar is one country; the blue share '
        f'are the blue-pressers who die, the red share are the red-pressers who survive. '
        f'Sorted by total deaths, fewest (Colombia) to most (the world total). Blue '
        f'deaths are labelled to the left of each bar and red survivors to the right. '
        f'No bar’s blue reaches the 50 percent line.">'
    )

    # Legend (top-left): die = blue, survive = red.
    p.append(f'<rect x="{BAR_X0}" y="10" width="11" height="11" fill="{DIE}"/>')
    p.append(f'<text x="{BAR_X0 + 16}" y="19" fill="{INK_MUTE}" font-size="11">die</text>')
    p.append(f'<rect x="{BAR_X0 + 44}" y="10" width="11" height="11" fill="{SURVIVE}"/>')
    p.append(f'<text x="{BAR_X0 + 60}" y="19" fill="{INK_MUTE}" font-size="11">survive</text>')

    # 50% reference line (the blue-wins majority; no bar's blue can reach it).
    p.append(f'<line x1="{x50:.1f}" y1="{TOP - 4}" x2="{x50:.1f}" y2="{H - BOT + 2}" '
             f'stroke="{INK_FAINT}" stroke-width="1" stroke-dasharray="3 3"/>')
    p.append(f'<text x="{x50:.1f}" y="19" fill="{INK_MUTE}" font-size="11" '
             f'text-anchor="middle">50%</text>')

    for i, row in enumerate(rows):
        yc = TOP + i * ROW_H + ROW_H / 2
        bar_y = yc - 5.5
        p.append(f'<text x="10" y="{yc + 4:.1f}" font-size="14">{row["glyph"]}</text>')
        p.append(f'<text x="34" y="{yc + 4:.1f}" fill="{INK}" font-size="12">{row["name"]}</text>')
        # blue deaths, right-aligned just left of the bar
        p.append(f'<text x="{BAR_X0 - 8}" y="{yc + 4:.1f}" fill="{DIE}" font-size="11" '
                 f'font-weight="bold" text-anchor="end">{human(row["deaths"])}</text>')
        # whole bar = survive (red); die (blue) overlaid from the left
        p.append(f'<rect x="{BAR_X0}" y="{bar_y:.1f}" width="{BAR_W}" height="11" fill="{SURVIVE}"/>')
        dw = BAR_W * row["rate"]
        if dw > 0.6:
            p.append(f'<rect x="{BAR_X0}" y="{bar_y:.1f}" width="{dw:.1f}" height="11" fill="{DIE}"/>')
        # red survivors (the living), hugging the right end of the bar
        p.append(f'<text x="{LABEL_X}" y="{yc + 4:.1f}" fill="{SURVIVE}" font-size="11" '
                 f'font-weight="bold">{human(row["pop"] - row["deaths"])}</text>')

    p.append("</svg>")
    return "\n".join(p)


if __name__ == "__main__":
    svg = build_svg()
    out = REPO / "figures" / "toll-bars.svg"
    out.parent.mkdir(exist_ok=True)
    out.write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + svg)
    print(f"saved {out}  ({len(svg):,} bytes)")
