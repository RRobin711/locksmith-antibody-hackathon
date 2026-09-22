# Is the G3 aromatic filter a binding result or a pose-retention result?

`scripts/74_g3_outcome_variable.py`, n = **239** designs with folds, seed 20260922, 10000 resamples. No new compute.

## 1. What aromatic count actually predicts

| outcome | what it measures | Spearman ρ (aromatics →) | p |
|---|---|---|---|
| `dockq` | **pose retention vs the parent crystal** | **-0.414** | 2.6e-11 |
| `ipsae` | self-consistency of the predicted interface | **-0.115** | 0.076 |
| `dg` | PRODIGY ΔG, a contact-count regression | **+0.087** | 0.18 |
| `contacts` | heavy-atom contact count | **+0.225** | 0.00044 |
| `iface_plddt` | interface confidence | **-0.442** | 7.2e-13 |
| `cdr_sasa` | CDR solvent accessibility | **-0.006** | 0.92 |
| `seq_recovery` | similarity to the parent SEQUENCE | +0.130 | 0.045 |
| `cdrh3_identity` | CDR-H3 identity to Keytruda | +0.152 | 0.018 |

## 2. G3's own test — filtered vs an equal-budget random subset (k = 45 of 239)

G3's logic, kept exactly: a filter must beat the SAME rule applied at random with the same retention fraction. Keeping the pool's best design proves nothing — a random subset retaining fraction *f* keeps the maximum with probability exactly *f*.

| outcome | filtered mean | random mean | margin | one-sided p |
|---|---|---|---|---|
| `dockq` | 0.7287 | 0.7050 | +0.0237 | **0.0001** ✅ |
| `ipsae` | 0.7981 | 0.7947 | +0.0034 | **0.2405** |
| `dg` | -12.3546 | -12.1961 | +0.1585 | **0.0641** |
| `contacts` | 99.8159 | 101.6163 | -1.8004 | **0.9884** |
| `iface_plddt` | 91.5243 | 90.3994 | +1.1248 | **0.0001** ✅ |
| `cdr_sasa` | 1519.0587 | 1519.8488 | -0.7901 | **0.5466** |

## 3. Verdict

The filter beats its equal-budget null on **2 of 6** outcomes: ['dockq', 'iface_plddt'].

**Every outcome it beats is a property of the PREDICTOR, not of the interface.** `dockq` here is measured against the parent crystal, so it is pose retention; `iface_plddt` is the model's own confidence in the interface it drew. Both answer *how cleanly does Boltz model this loop*. Meanwhile every quantity that is about the interface itself — contact count, PRODIGY ΔG, CDR SASA — is null or worse.

**`contacts` runs the wrong way and that is the sharpest result here.** Filtered designs have FEWER heavy-atom contacts than a random subset of the same size (one-sided p for 'more contacts' = 0.988, i.e. the reverse test is significant). That is exactly what the chemistry predicts — Tyr and Trp are large and make many contacts — and it is the opposite of what a binding filter should do.

**So G3 does not license a design rule.** It established that CDR-H3s with fewer aromatics are ones Boltz places closer to the parent pose and is more confident about. Neither quantity exists for a de novo target: there is no parent crystal to retain a pose against, and confidence is not affinity (`results/skempi_validity.md`: a mutation that abolishes binding scores ipSAE 0.917 against the wild type's 0.903). Optimising it selects for designs the predictor finds easy, which is the definition of a metric gaming its own scorer.

**The prior it inverts.** Tyr and Trp dominate natural paratopes; selecting for ≤1 aromatic in a 13-residue CDR-H3 selects against them. Our own named winner carries aromatic count **2**, so the filter at its pre-registered threshold would have discarded it.

**What is NOT refuted.** The statistics were sound and the null was the right one for the question asked. Nothing here says the original analysis was sloppy; it says the outcome variable does not support the conclusion that was drawn from it. This is the same error class as `results/metric_validity.md` §on outcome choice.

---

## 4. What downstream rested on this — checked, not assumed

**The shortlist and the named winner did NOT.** `scripts/32_shortlist_and_reseed.py:76`
sorts on `-x["surrogate"]`; aromatic count appears only in a reporting line
(`by aromatic count:` at line 86). The filter was never applied as a selection step, so
refuting it **does not disturb the Challenge 1 selection**. This was verified by reading
the sort key, not inferred from memory — and it is the reason the winner carries aromatic
count 2 despite a pre-registered threshold of ≤1.

**Documents changed in this pass:** `PLAN.md` (G3 status ✅→❌), `README.md` (status
block), `results/pitch_outline.md` (moved from "do not present as validated" to "refuted;
if mentioned, mention it as a finding about the metric"), `results/m3_g3_verdict.md`
(SUPERSEDED banner at the top), `LEARNINGS.md` (entry rewritten with the resolution), and
`scripts/57_build_submission.py` — which carried a **dangling reference to
`results/g3_verdict_reexamined.md`, a file that never existed**. That reference was
written into the shipped `methods_and_limitations.md` last session and would have sent a
grader to a missing file; it is now replaced with the result itself, inline.

*That dangling reference is itself an instance of the night's pattern: the newest claim
carried the error. It was written in the same pass that added the "if a number cannot be
reproduced from the artefact you hand over, you have not handed over the number" language.*
