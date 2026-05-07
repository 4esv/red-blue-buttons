// Red Button / Blue Button — shared chart utilities (static charts).
// No dependencies. ES module. Used by logic.html and empirics.html.

// ----- Coordinate helpers --------------------------------------------------

// (a, p) live in [0, 1]. We map them to a plot box {x0, y0, x1, y1} in SVG
// user units. SVG y grows downward, so we flip p so p=1 sits at the top.
export function makeScales({ x0, y0, x1, y1, aMin = 0, aMax = 1, pMin = 0, pMax = 1 } = {}) {
  const w = x1 - x0;
  const h = y1 - y0;
  return {
    x: (a) => x0 + ((a - aMin) / (aMax - aMin)) * w,
    y: (p) => y1 - ((p - pMin) / (pMax - pMin)) * h,
    box: { x0, y0, x1, y1, w, h, aMin, aMax, pMin, pMax },
  };
}

export function clamp(v, lo, hi) {
  return Math.max(lo, Math.min(hi, v));
}

// ----- Color scales --------------------------------------------------------

function lerpHex(c0, c1, t) {
  const a = parseInt(c0.slice(1), 16);
  const b = parseInt(c1.slice(1), 16);
  const r0 = (a >> 16) & 255, g0 = (a >> 8) & 255, b0 = a & 255;
  const r1 = (b >> 16) & 255, g1 = (b >> 8) & 255, b1c = b & 255;
  const r = Math.round(r0 + (r1 - r0) * t);
  const g = Math.round(g0 + (g1 - g0) * t);
  const bb = Math.round(b0 + (b1c - b0) * t);
  return `rgb(${r},${g},${bb})`;
}

// P(blue wins): cream -> lavender. "This region commits to blue."
export function colorPBlue(v) {
  return lerpHex("#f4ecd8", "#8579a0", clamp(v, 0, 1));
}

// Share of population pressing blue: cream -> lavender. The visible range
// over our 22 countries is roughly 0.05..0.35, so we stretch a 0..0.5
// input range across the full gradient for visible contrast.
export function colorBlueFraction(v) {
  const t = clamp(v / 0.5, 0, 1);
  return lerpHex("#f4ecd8", "#8579a0", t);
}

// Survival: brick -> cream -> sage. Bad -> neutral -> good. Anchor the
// midpoint at 0.75 so the visible range (~0.5..1.0) stretches across.
export function colorSurvival(v) {
  const c = clamp(v, 0, 1);
  const mid = 0.75;
  if (c <= mid) return lerpHex("#a84a3c", "#f4ecd8", c / mid);
  return lerpHex("#f4ecd8", "#6b8576", (c - mid) / (1 - mid));
}

// ----- Grid lookup ---------------------------------------------------------

export function nearestIndex(axis, value) {
  let best = 0, bestDist = Infinity;
  for (let i = 0; i < axis.length; i++) {
    const d = Math.abs(axis[i] - value);
    if (d < bestDist) { bestDist = d; best = i; }
  }
  return best;
}

export function lookupCell(grid, a, p) {
  const i = nearestIndex(grid.altruism_axis, a);
  const j = nearestIndex(grid.trust_axis, p);
  // blue_fraction lives only on the flat `cells` array, not on a 2D grid.
  const flat = grid.cells?.[i * grid.grid_size + j];
  return {
    a: grid.altruism_axis[i],
    p: grid.trust_axis[j],
    p_blue_wins: grid.p_blue_wins_grid[i][j],
    survival: grid.survival_grid[i][j],
    blue_fraction: flat ? flat.blue_fraction : null,
  };
}

// ----- Formatters ---------------------------------------------------------

export const fmtPct = (v) => `${(v * 100).toFixed(0)}%`;
export const fmt2 = (v) => v.toFixed(2);
