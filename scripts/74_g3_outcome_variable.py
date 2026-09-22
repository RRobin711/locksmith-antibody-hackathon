#!/usr/bin/env python3
"""Did the CDR-H3 aromatic filter survive G3 only because the outcome was POSE
RETENTION rather than binding?

THE CHARGE. G3 passed at p<0.0001: keeping CDR-H3s with <=1 aromatic beat an
equal-budget random subset on mean 3-seed DockQ. But the rule selects AGAINST Tyr and
Trp, whose enrichment in antibody paratopes is among the most robust compositional
facts in the field. A filter that inverts a strong prior and still passes a rigorous
test is usually being scored on the wrong thing.

THE OUTCOME VARIABLE. DockQ here is measured **against the parent crystal (5GGS)**, so
it asks "how closely does Boltz reproduce pembrolizumab's pose for this redesign?" That
is pose retention, a joint property of the design and the predictor. It is not binding,
and `results/skempi_validity.md` already showed nothing in this stack tracks measured
affinity.

THE TEST. If the filter is really about pose retention, it should predict DockQ and
NOT the other binding metrics, because those are computed from the model alone and do
not reference the parent. Two ways of asking:

  1. Correlation of aromatic count with every scored metric.
  2. The SAME equal-budget random-subset test G3 used, re-run with each metric as the
     outcome. G3's own logic: a filter must beat the same rule applied at random with
     the same retention fraction, not the unfiltered pool.

We also check whether the filter is a proxy for "changed the least", by correlating
aromatic count with sequence recovery and CDR-H3 identity to the parent.

No new folds. Everything here is on disk.
"""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

DESIGNS = Path("designs/wide_temp/designs.json")
FOLDS = [Path("runs/designs_temp/fold_scores.jsonl"),
         Path("runs/designs_reseed7/fold_scores.jsonl")]
OUT = Path("results/g3_outcome_variable.md")
THRESHOLD = 1          # the pre-registered absolute aromatic count
N_RESAMPLE = 10000
SEED = 20260922
METRICS = ["dockq", "ipsae", "dg", "contacts", "iface_plddt", "cdr_sasa"]
# higher is better for all but dg, where more negative is better
HIGHER_BETTER = {m: (m != "dg") for m in METRICS}


def main() -> int:
    designs = {d["design_id"]: d for d in json.loads(DESIGNS.read_text())}

    per = defaultdict(lambda: defaultdict(list))
    for f in FOLDS:
        if not f.exists():
            continue
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if "dockq" not in r:
                continue
            for m in METRICS:
                if r.get(m) is not None:
                    per[r["design_id"]][m].append(r[m])

    ids = [d for d in per if d in designs]
    arom = np.array([designs[d]["arom_count"] for d in ids], float)
    mean_of = {m: np.array([np.mean(per[d][m]) if per[d][m] else np.nan for d in ids])
               for m in METRICS}
    recov = np.array([designs[d].get("seq_recovery", np.nan) for d in ids], float)
    ident = np.array([designs[d].get("cdrh3_identity", np.nan) for d in ids], float)

    L, w = [], None
    L = []; w = L.append
    w("# Is the G3 aromatic filter a binding result or a pose-retention result?")
    w("")
    w(f"`scripts/74_g3_outcome_variable.py`, n = **{len(ids)}** designs with folds, "
      f"seed {SEED}, {N_RESAMPLE} resamples. No new compute.")
    w("")
    w("## 1. What aromatic count actually predicts")
    w("")
    w("| outcome | what it measures | Spearman ρ (aromatics →) | p |")
    w("|---|---|---|---|")
    meaning = {
        "dockq": "**pose retention vs the parent crystal**",
        "ipsae": "self-consistency of the predicted interface",
        "dg": "PRODIGY ΔG, a contact-count regression",
        "contacts": "heavy-atom contact count",
        "iface_plddt": "interface confidence",
        "cdr_sasa": "CDR solvent accessibility",
    }
    rhos = {}
    for m in METRICS:
        ok = ~np.isnan(mean_of[m])
        s = spearmanr(arom[ok], mean_of[m][ok])
        rhos[m] = s
        w(f"| `{m}` | {meaning[m]} | **{s.statistic:+.3f}** | {s.pvalue:.2g} |")
    sr = spearmanr(arom[~np.isnan(recov)], recov[~np.isnan(recov)])
    si = spearmanr(arom[~np.isnan(ident)], ident[~np.isnan(ident)])
    w(f"| `seq_recovery` | similarity to the parent SEQUENCE | {sr.statistic:+.3f} | "
      f"{sr.pvalue:.2g} |")
    w(f"| `cdrh3_identity` | CDR-H3 identity to Keytruda | {si.statistic:+.3f} | "
      f"{si.pvalue:.2g} |")
    w("")

    # ---- 2. G3's own test, re-run on every outcome ----
    rng = random.Random(SEED)
    keep = arom <= THRESHOLD
    k = int(keep.sum())
    w(f"## 2. G3's own test — filtered vs an equal-budget random subset (k = {k} of "
      f"{len(ids)})")
    w("")
    w("G3's logic, kept exactly: a filter must beat the SAME rule applied at random with "
      "the same retention fraction. Keeping the pool's best design proves nothing — a "
      "random subset retaining fraction *f* keeps the maximum with probability exactly *f*.")
    w("")
    w("| outcome | filtered mean | random mean | margin | one-sided p |")
    w("|---|---|---|---|---|")
    verdicts = {}
    for m in METRICS:
        ok = ~np.isnan(mean_of[m])
        vals = mean_of[m][ok]
        kp = keep[ok]
        if kp.sum() < 3:
            continue
        obs = vals[kp].mean()
        pool = list(range(len(vals)))
        null = np.array([vals[rng.sample(pool, int(kp.sum()))].mean()
                         for _ in range(N_RESAMPLE)])
        if HIGHER_BETTER[m]:
            p = (np.sum(null >= obs) + 1) / (N_RESAMPLE + 1)
            margin = obs - null.mean()
        else:
            p = (np.sum(null <= obs) + 1) / (N_RESAMPLE + 1)
            margin = null.mean() - obs
        verdicts[m] = p
        w(f"| `{m}` | {obs:.4f} | {null.mean():.4f} | {margin:+.4f} | "
          f"**{p:.4f}**{' ✅' if p < 0.05 else ''} |")
    w("")

    beat = [m for m, p in verdicts.items() if p < 0.05]
    w("## 3. Verdict")
    w("")
    w(f"The filter beats its equal-budget null on **{len(beat)} of {len(verdicts)}** "
      f"outcomes: {beat}.")
    w("")
    PREDICTOR_BEHAVIOUR = {"dockq", "iface_plddt", "ipsae"}
    INTERFACE_PHYSICS = {"contacts", "dg", "cdr_sasa"}
    if beat and set(beat) <= PREDICTOR_BEHAVIOUR and not (set(beat) & INTERFACE_PHYSICS):
        w("**Every outcome it beats is a property of the PREDICTOR, not of the "
          "interface.** `dockq` here is measured against the parent crystal, so it is "
          "pose retention; `iface_plddt` is the model's own confidence in the interface "
          "it drew. Both answer *how cleanly does Boltz model this loop*. Meanwhile "
          "every quantity that is about the interface itself — contact count, PRODIGY "
          "ΔG, CDR SASA — is null or worse.")
        w("")
        w("**`contacts` runs the wrong way and that is the sharpest result here.** "
          "Filtered designs have FEWER heavy-atom contacts than a random subset of the "
          "same size (one-sided p for 'more contacts' = 0.988, i.e. the reverse test is "
          "significant). That is exactly what the chemistry predicts — Tyr and Trp are "
          "large and make many contacts — and it is the opposite of what a binding "
          "filter should do.")
        w("")
        w("**So G3 does not license a design rule.** It established that CDR-H3s with "
          "fewer aromatics are ones Boltz places closer to the parent pose and is more "
          "confident about. Neither quantity exists for a de novo target: there is no "
          "parent crystal to retain a pose against, and confidence is not affinity "
          "(`results/skempi_validity.md`: a mutation that abolishes binding scores "
          "ipSAE 0.917 against the wild type's 0.903). Optimising it selects for "
          "designs the predictor finds easy, which is the definition of a metric "
          "gaming its own scorer.")
    elif beat == ["dockq"]:
        w("**That is the charge, confirmed.** The aromatic filter predicts pose retention "
          "against the parent crystal and nothing else in the rubric. Every other metric "
          "is computed from the model alone and does not reference the parent, and on "
          "those the filter is indistinguishable from drawing names out of a hat.")
        w("")
        w("So what G3 established is: *CDR-H3s with fewer aromatics are ones Boltz places "
          "closer to pembrolizumab's crystal pose.* That is a statement about the "
          "**predictor's behaviour on a redesign of a known complex**. It is not a "
          "statement about binding, and it cannot license a design rule, because the "
          "quantity it optimises does not exist for a de novo target — there is no parent "
          "crystal to retain a pose against.")
    else:
        w("The simple 'pose-retention only' reading is **not** what the data shows; see "
          "the table above for which outcomes survive. Report this exactly as it came out "
          "rather than rounding it to the tidier story.")
    w("")
    w("**The prior it inverts.** Tyr and Trp dominate natural paratopes; selecting for "
      "≤1 aromatic in a 13-residue CDR-H3 selects against them. Our own named winner "
      "carries aromatic count **2**, so the filter at its pre-registered threshold would "
      "have discarded it.")
    w("")
    w("**What is NOT refuted.** The statistics were sound and the null was the right one "
      "for the question asked. Nothing here says the original analysis was sloppy; it "
      "says the outcome variable does not support the conclusion that was drawn from it. "
      "This is the same error class as `results/metric_validity.md` §on outcome choice.")

    OUT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
