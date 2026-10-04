#!/usr/bin/env python3
"""What effect could the depth sweep's heterogeneity null actually have DETECTED?

THE CLAIM THIS PRICES. `results/depth_sweep.md` concluded "No stratum C. No rental." on
the strength of one null: 18 backbones x 8 sequences, 12 clears, Pearson dispersion
X^2 = 22.91 on 17 df (p = 0.152) and a beta-binomial LRT of 0.696 (fitted rho = 0.0446,
p = 0.202). From that it wrote: "These 18 backbones are exchangeable: there are no good or
bad ones in this pool, only draws", and therefore "generate more backbones" and "draw more
sequences" are the same experiment at different prices.

WHY IT NEEDED PRICING. A null is only meaningful as "no effect larger than x", and x was
never stated. `docs/lecture/08-what-broke.md:512` records "a small-n null read as evidence
of absence" as this project's most repeated error -- >=6 instances, four corrected in a
single day. The depth sweep itself withdraws two claims for that exact shape, then rests
its spending decision on a third null of the same kind. Its own conclusion hedges with
"this pipeline's ceiling ON THESE BACKBONES", which is the loophole stated by the file
that closes the question.

THE CONTROL COMES FIRST. Before any power number, the implementation must reproduce the
recorded statistics from the recorded per-backbone counts (10 zeros, 5 ones, 2 twos, one
three). It does, to 3 dp on all four quantities. Without that the power curve would be
measuring some other test.

CALIBRATION, AND WHY ASYMPTOTICS ARE NOT ASSUMED. At p = 0.083 and k = 8 the chi-square
approximation is suspect, so critical values are simulated under rho = 0 rather than read
from a table. The asymptotic chi2_17 cutoff turns out to be mildly conservative (real
type-I 0.0405, not 0.050) and the simulation-calibrated p for the observed 22.909 is
0.132 rather than 0.152 -- the conclusion is unchanged either way, which is worth knowing.

TWO PARAMETERISATIONS, because rho is not a quantity anyone can act on. Part A reports
power against the intra-backbone correlation rho. Part B reports it against mixture worlds
-- "g of 18 backbones clear at p_good, the rest at p_bad" -- holding the pool mean near the
observed 8.3%, which is the form the campaign decision actually takes: is there a backbone
worth generating more of?

STATED PLAINLY. This prices the EXISTING null. It does not run anything, fold anything, or
re-examine whether the 18 backbones were a representative sample in the first place -- that
is the separate range-restriction question in `results/unconditioned_baseline.md`.

    uv run python scripts/110_heterogeneity_power.py
"""
from __future__ import annotations

import numpy as np
from scipy import optimize, special, stats

SEED = 20260924
N, K = 18, 8
CLEARS = 12
MU = CLEARS / (N * K)
OBS = np.array([0] * 10 + [1] * 5 + [2] * 2 + [3])
RECORDED = {"x2": 22.91, "x2_p": 0.152, "lr": 0.696, "rho": 0.0446, "lr_p": 0.202}


def pearson_disp(x: np.ndarray, k: int) -> float:
    """Pearson dispersion statistic; chi-square on len(x)-1 df under a shared rate."""
    p = x.sum() / (len(x) * k)
    if p <= 0 or p >= 1:
        return 0.0
    return float(((x - k * p) ** 2).sum() / (k * p * (1 - p)))


def _bb_nll(params, x, k):
    mu = special.expit(params[0])
    s = np.exp(params[1])
    a, b = mu * s, (1 - mu) * s
    return -float(np.sum(special.betaln(x + a, k - x + b) - special.betaln(a, b)))


def _bin_nll(x, k):
    p = x.sum() / (len(x) * k)
    if p <= 0 or p >= 1:
        return 0.0
    return -float(np.sum(x * np.log(p) + (k - x) * np.log(1 - p)))


def bb_lrt(x: np.ndarray, k: int) -> tuple[float, float]:
    """Beta-binomial vs binomial LR statistic, and the fitted rho = 1/(s+1)."""
    best = None
    p0 = special.logit(max(x.sum() / (len(x) * k), 1e-3))
    for s0 in (0.0, 2.0, 4.0, 6.0):
        r = optimize.minimize(_bb_nll, [p0, s0], args=(x, k), method="Nelder-Mead",
                              options={"xatol": 1e-8, "fatol": 1e-10, "maxiter": 4000})
        if best is None or r.fun < best.fun:
            best = r
    return max(2 * (_bin_nll(x, k) - best.fun), 0.0), 1.0 / (np.exp(best.x[1]) + 1.0)


def draw(n, k, mu, rho, rng):
    if rho <= 1e-9:
        return rng.binomial(k, mu, size=n)
    s = (1 - rho) / rho
    return rng.binomial(k, rng.beta(mu * s, (1 - mu) * s, size=n))


def crit(n, k, mu, rng, nsim=20000):
    v = np.array([pearson_disp(rng.binomial(k, mu, size=n), k) for _ in range(nsim)])
    return float(np.quantile(v, 0.95))


def main() -> int:
    rng = np.random.default_rng(SEED)

    print("CONTROL -- reproduce the recorded statistics from the recorded counts")
    x2 = pearson_disp(OBS, K)
    lr, rho = bb_lrt(OBS, K)
    got = {"x2": x2, "x2_p": stats.chi2.sf(x2, N - 1), "lr": lr, "rho": rho,
           "lr_p": 0.5 * stats.chi2.sf(lr, 1)}
    ok = True
    for key, want in RECORDED.items():
        hit = abs(got[key] - want) < 0.005
        ok &= hit
        print(f"  {key:6s} recorded {want:8.4f}  computed {got[key]:8.4f}  "
              f"{'OK' if hit else 'MISMATCH'}")
    if not ok:
        print("\nCONTROL FAILED -- the power curve below would measure a different test.")
        return 1

    c = crit(N, K, MU, rng)
    print(f"\nCALIBRATION  (p={MU:.4f}, k={K}: asymptotics not assumed)")
    print(f"  simulated 95th pct under rho=0 : {c:.3f}")
    print(f"  asymptotic chi2_17 95th pct    : {stats.chi2.ppf(0.95, 17):.3f}")
    print(f"  that cutoff's REAL type-I rate : "
          f"{np.mean([pearson_disp(rng.binomial(K, MU, size=N), K) > stats.chi2.ppf(0.95,17) for _ in range(20000)]):.4f}")

    print(f"\nA. POWER vs intra-backbone correlation rho  (n={N}, k={K}, alpha=0.05 calibrated)")
    print(f"{'rho':>7} {'sd(rate)':>9} {'10-90 pct of rates':>22} {'power':>7}")
    for r in (0.0, 0.0446, 0.10, 0.15, 0.20, 0.24, 0.30, 0.40, 0.50):
        pw = np.mean([pearson_disp(draw(N, K, MU, r, rng), K) > c for _ in range(6000)])
        if r > 1e-9:
            s = (1 - r) / r
            lo, hi = stats.beta.ppf([0.10, 0.90], MU * s, (1 - MU) * s)
        else:
            lo = hi = MU
        flag = "  <- fitted" if abs(r - RECORDED["rho"]) < 1e-6 else ""
        print(f"{r:7.3f} {np.sqrt(r*MU*(1-MU)):9.4f} "
              f"{lo*100:8.1f}% -{hi*100:7.1f}% {pw:7.3f}{flag}")

    print(f"\nB. POWER vs mixture worlds  (pool mean held near {MU:.1%})")
    print(f"{'good bb':>8} {'p_good':>7} {'p_bad':>7} {'pool mean':>10} {'power':>7}")
    for ng, pg, pb in [(3, 0.20, 0.060), (2, 0.25, 0.063), (3, 0.25, 0.050),
                       (1, 0.40, 0.063), (4, 0.25, 0.036), (6, 0.20, 0.025),
                       (2, 0.40, 0.042), (3, 0.35, 0.030), (1, 0.60, 0.050)]:
        p = np.r_[np.full(ng, pg), np.full(N - ng, pb)]
        pw = np.mean([pearson_disp(rng.binomial(K, p), K) > c for _ in range(6000)])
        print(f"{ng:8d} {pg:7.0%} {pb:7.1%} {(ng*pg+(N-ng)*pb)/N:10.1%} {pw:7.3f}")

    print(f"\nC. WHAT DESIGN WOULD DETECT rho = 0.10 / 0.15 at 80%?")
    print(f"{'n bb':>5} {'k seq':>6} {'folds':>6} {'new folds':>10} {'pw(0.10)':>9} {'pw(0.15)':>9}")
    for n, k in [(18, 8), (18, 16), (36, 8), (18, 32), (36, 16), (54, 8)]:
        cc = crit(n, k, MU, rng, nsim=8000)
        p10 = np.mean([pearson_disp(draw(n, k, MU, 0.10, rng), k) > cc for _ in range(4000)])
        p15 = np.mean([pearson_disp(draw(n, k, MU, 0.15, rng), k) > cc for _ in range(4000)])
        print(f"{n:5d} {k:6d} {n*k:6d} {n*k-144:10d} {p10:9.3f} {p15:9.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
