# Pre-registration — Challenge 2 production run
**Written 2026-09-21, BEFORE any production score exists.** Settles audit items 10.1 and 10.2.

## The problem this exists to solve

The handbook allows **one design per challenge**. We will hold ~N x 4 candidates and must
pick one. Every metric that would normally order them has been measured not to:
PRODIGY dG and contacts are blind to interface destruction (0.9x seed noise vs 64x for
interface pLDDT); ipSAE and interface pLDDT detect gross destruction but mis-rank SKEMPI
point mutants **with the wrong sign**; nothing tracks measured affinity; and Challenge 2
has no DockQ. Choosing on the composite is therefore not available -- we have proven the
composite does not order things.

## 10.1 — Establishing whether `interaction_pae` can select

`interaction_pae` (RF2's PAE restricted to inter-chain pairs) is the only RF2 output that
moved across the four designs we have: **14.42 / 14.70 / 15.84 / 14.61**, range 1.42,
against `pred_lddt` flat at 0.91-0.92 and useless. But **all four share one dock**, so that
is *within-backbone* spread. A selection rule needs **between-dock** separation, which is
unmeasured.

### The cheapest way to measure it: the pod's first hour

Three options costed:

| route | design | wall-clock | cash |
|---|---|---|---|
| existing artefacts | — | — | **impossible**: we have exactly 1 backbone |
| CPU | 8 backbones x 2 seqs | 8x19.5 + 16x7.1 = **4.5 h** | £0, machine tied up |
| **pod, first hour** | **10 backbones x 3 seqs** | 10x~3 + 30x~0.75 = **~55 min** | **~$0.25** |

**The pod block wins by ~5x on wall-clock and costs pennies — and it is not extra work.**
It doubles as the per-backbone timing measurement that must happen before N is fixed
(the 5-8 min/backbone figure is a bracket, and the last bracketed figure — RF2 at 4 min —
measured 7.1, **1.75x off**). One block, two answers.

### The statistic, and the effect it can detect

One-way variance decomposition of `interaction_pae` by backbone:

```
ICC = var_between_backbone / (var_between_backbone + var_within_backbone)
```

At **k = 10 backbones, m = 3 sequences** (n = 30), the between-backbone F-test has
df = (9, 20) and F_crit(0.05) = 2.39, which corresponds to **ICC ≈ 0.32**.

> **Stated before the run, per the standing rule: this block can detect ICC ≥ ~0.32.
> An ICC below that is indistinguishable from zero at this n and must NOT be reported
> as "no between-dock signal" — only as "no signal larger than 0.32 detectable at k=10."**

### The selection rule, pre-registered

- **If ICC ≥ 0.32** → primary key is **`interaction_pae`, lower is better**, computed as the
  per-backbone mean over its sequences (not the per-design minimum, which selects on noise).
- **If ICC < 0.32** → fall back to **hotspot contact count** from `pod/check_backbone.py`
  — the only quantity measured to be both deterministic and meaningful. Tie-break on
  `frac_iface_on_epitope`.
- **In both cases** the gates are applied first (ipSAE ≥ 0.60, dG ≤ -6, NetSolP ≥ 0.50,
  germline CDR-H3 identity < 95%); selection operates only on gate-clearing designs.
- **Not permitted as a selection key:** the rubric composite, PRODIGY dG, contacts.
  Reasons above; all three are measured blind or mis-ordered.

**Backbone ID is stamped into every design row at generation time.** It cannot be
reconstructed after aggregation, and every variance and rate figure below depends on it.

## 10.2 — N

**Default N = 30, not 100.** The endorsement of 100 rested on a pass-rate confidence
interval, and a pass rate is a property of the *pipeline*, not of the molecule we submit.
Combined with 10.1, a larger pool we cannot rank is worse than a smaller one: it widens
the selection problem without improving the answer.

**Two conditions could revise it upward, and both are measured by the same pilot block:**

1. **If ICC ≥ 0.32**, selection has real signal, and best-of-N genuinely improves with N.
   Then N = 60-100 buys something.
2. **If the gate pass rate is very low** (< ~10% of backbones yielding any gate-clearing
   design), N = 30 risks returning **zero** successes and teaching nothing. At a 5% rate,
   N = 30 has a 21% chance of zero.

So N is set **after** the pilot block, from two numbers it produces. The block's 10
backbones are the first tranche of whichever N is chosen, not a separate cost.

### Rate definition — which one is quoted

**Backbone-level.** A backbone passes if **any** of its sequences clears all gates.
Design-level rates over N x 4 treat four sequences sharing one dock as independent; they
are not, and a CI computed that way is **falsely narrow by up to ~2x**. If a design-level
rate is reported at all it carries a clustered CI and says so.

## What would make this run uninformative

Declared in advance:

- **Zero backbones clear the gates.** Reportable as a characterised negative, but only if
  the conditioning check confirms the docks were on-epitope — otherwise it is a plumbing
  failure, not a result.
- **All backbones score identically** on both candidate keys, i.e. ICC < 0.32 *and*
  hotspot contact count is constant. Then no selection rule exists, we submit the design
  with the highest hotspot contact count, and we say plainly that the choice is arbitrary
  among gate-clearing candidates.
- **The unconditioned arm is indistinguishable from the conditioned arm** on
  `frac_iface_on_epitope`. That would mean the hotspot conditioning is doing nothing and
  the whole run is unconditioned generation wearing a target's name. Detectable effect for
  that comparison to be stated before that arm runs, per the same rule as above.

## What this run does NOT establish

- **The hotspot contact check tests conditioning, not binding** (audit 10.6). It answers
  "did RFdiffusion aim where it was told", never "does this bind".
- **RF2 agreement is not validation** (audit 10.5). It is a different model from Boltz,
  which is better than self-consistency, but both are trained on overlapping PDB data and
  correlated errors are exactly what one would expect. One sentence in the docs, not a
  claim.
- **No binding evidence of any kind exists** for anything this run produces.
