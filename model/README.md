# model

Core simulation. One file (`core.py`), no surprises.

## Decision rule

An agent with altruism $a$ and trust $p$ presses blue when

$$p \cdot (1 + a) \;\geq\; \lambda$$

where $\lambda$ is the loss-aversion coefficient. Equivalently, the trust threshold is

$$t^{\star}(a) \;=\; \frac{\lambda}{a + \lambda}$$

- $\lambda = 1$: textbook expected-value rule. Threshold collapses to $1 / (1 + a)$.
- $\lambda = 2.25$: Kahneman–Tversky 1992 loss aversion. Threshold rises to e.g. 0.89 at $a = 0.28$.

## Outcome

After every agent decides, each one misclicks independently with probability `error_rate`. If the post-error blue fraction is $\geq 0.5$, blue wins and everyone survives. Otherwise blue loses and only the red voters survive.

## Assumptions, stated honestly

- **No communication.** Agents don't see each other's votes, don't poll, don't update beliefs. This is the analytical baseline the dilemma is usually stated under, but it's a simplification — see "Known weak points" in the article.
- **Beta-distributed traits.** `altruism_alpha/beta` and `trust_alpha/beta` shape a population. The sweep script (`scripts/generate_empirics_grid.py`) chooses a fixed concentration of 7 and varies the mean — this trades realism for legibility on a 2D map.
- **Symmetric error rate.** A misclick swaps your intended button. Default is 2%; doubling it shifts results modestly without changing structure.
- **Loss aversion is contestable at high stakes.** $\lambda = 2.25$ is from gambling experiments; the literature is messy when the loss is "your life." The article footnotes this.
