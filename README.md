# red button / blue button

A population-scale simulation behind the essay **[Which button?](https://aesv.io/etc/which-button)**.

> Everyone in the world privately presses a red or blue button. If more than half press blue, everyone lives. Otherwise only the people who pressed red live.

Red is the safe button: you live either way. Blue saves everyone if it clears a majority and kills you if it doesn't. The essay argues about what people *would* do; this repo estimates it from real national data and keeps the numbers reproducible.

## The model

Each agent has a **trust** `p` (its belief that others will press blue, drawn around its nation's social-trust level) and an **altruism** `a` (the weight it puts on a stranger's life). It presses blue iff

```
trust × (1 + altruism) ≥ 1
```

the risk-neutral expected-value rule, equivalently when trust clears the threshold `1 / (1 + a)`. Traits are Beta-distributed around each nation's mean (concentration 7); altruism is fixed at `a = 0.28`, the dictator-game mean (Engel 2011) used as a generous ceiling. There is no misclick, no communication, no coordination.

The rule is **global**: blue wins only if more than half of *everyone* presses it. With no noise the per-country blue (= death) fraction is a closed form, evaluated by quadrature and confirmed by a Monte-Carlo run at the real world population (~7 billion agents); the two agree to 0.0004 percentage points.

## What it finds

- **Blue never wins** — not in any surveyed country, not in the world. The global blue fraction is about 5%, against the 50% it needs.
- **Deaths climb with trust.** The more a country trusts, the more of it presses blue and dies when blue loses. Denmark, the most trusting nation measured, loses about 42%; the least trusting lose a rounding error.
- **The world figure is China-dominated.** At China's (contested) 64% trust, China alone is about 89% of the global toll; take China out and the world death rate falls below the US.

Full write-up, with the figures: **https://aesv.io/etc/which-button**

## Reproduce

```bash
pip install -r requirements.txt

python -m scripts.model              # exact results + sensitivity -> data/canonical_results.json
python -m scripts.model --confirm    # also the ~7e9-agent Monte-Carlo confirmation (slow)
python -m scripts.plot_death_curve   # -> figures/death-curve.svg
python -m scripts.plot_toll_bars     # -> figures/toll-bars.svg
python -m unittest tests.test_model  # pin the published numbers
```

## Layout

```
scripts/model.py             the model: decision rule, exact blue_fraction, global world game
scripts/plot_death_curve.py  death-rate-vs-trust curve (transparent SVG, page colors)
scripts/plot_toll_bars.py    per-country death toll, blue deaths vs red survivors
data/countries.json          inputs: per-nation trust, altruism, population, with sources
data/canonical_results.json  the outputs the essay cites
figures/                     the generated charts
tests/                       pin the published numbers against the model
```

## Data

`data/countries.json` carries every input with its source in the `_meta` block: trust from the World Values Survey Wave 7 (Denmark from the European Values Study 2017, merged into the same series), altruism from Engel's 2011 dictator-game meta-analysis, populations from UN World Population Prospects 2022. Trust values are approximate (WVS percentages move 1–3 points between releases) and China's 64% is contested; the essay treats both as such.
