# red button / blue button

Code and figures behind **[Red Button, Blue Button](https://aesv.io/feed/red-button-blue-button)**.

> Red is safe. Blue saves everyone if more than half the world presses it — otherwise it kills the people who pressed it.

The article is the thing to read. This repo holds the simulation it cites and the figures it embeds, so the numbers stay reproducible.

## Layout

```
model/      decision rule, simulate_once, simulate_many
data/       empirics_grid.json (41×41 sweep), countries.json (WVS Wave 7 trust)
scripts/    generate_empirics_grid.py — regenerate the sweep
charts/     standalone HTML/SVG figures
tests/      sanity checks
```

## Reproduce

```bash
python3 -m pytest tests/ -q
python3 -m scripts.generate_empirics_grid    # a few minutes
python3 -m http.server 8000 && open http://localhost:8000/charts/
```

No build step, no dependencies. Charts use `system-ui` standalone; on aesv.io they inherit Birdie.

## The model in one line

An agent presses blue iff $p \cdot (1 + a) \geq \lambda$ — i.e. iff their trust clears $\lambda / (a + \lambda)$, where $\lambda$ is loss aversion (1 = textbook, 2.25 = Kahneman–Tversky). Blue wins if the post-error blue fraction clears 50%. Full derivation in [`model/README.md`](model/README.md).

## Data provenance

`countries.json` uses approximate WVS Wave 7 trust values and the global dictator-game altruism mean (Engel 2011). Metadata in the file documents sources and caveats. Verify against the WVS release before citing in anything load-bearing.
