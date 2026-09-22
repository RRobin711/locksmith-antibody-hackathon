---
date: 2026-09-15
tags: [project, protein-design, structure-prediction, resource, learning]
status: living
---

Tags: [[Protein Design|protein design]] · [[Structure Prediction|structure prediction]] · [[Resource|reference material]] · [[Learning|things I'm learning]]

# The Eight Metrics

**Why this note exists:** with no lab, "does this antibody work?" is answered entirely by
these eight numbers. They are the definition of success, so understanding what each one
actually measures — and what it *fails* to measure — is the difference between designing a
molecule and gaming a scoreboard.

Background: [[How Structure Prediction Works|what a folding model produces]].

---

## 1. How the scoring works

Each metric produces a raw value, which is mapped into one of three bands — **good**, **medium**
or **poor** — and converted to a sub-score out of 10. The sub-scores are grouped into three
categories and combined:

```
Final score (0–100) = [ 0.60 × Binding + 0.20 × Developability + 0.20 × Novelty ] × 10
```

**Binding** averages six metrics. **Developability** is one metric. **Novelty** is one metric.

Two consequences fall straight out of that arithmetic, and they shaped our whole approach:

- Because binding is an *average of six*, improving one binding metric moves the final score by
  only a sixth of its weight. Novelty and developability are single metrics carrying the same
  weight each — so **one point of novelty is worth about twice one point of any binding
  metric.** And both are computable from sequence alone, in milliseconds, before any structure
  exists.
- Because binding is an average, it is dragged down by its **worst** member. Optimise the
  minimum, not the mean.

## 2. The hard cutoffs

Separately from the bands, each metric has a **hard cutoff**. Fail any single one and the
design is marked **non-viable** and ranked below every design that passed. It is a gate, not a
penalty.

Eight independent gates, all of which must pass.

| Metric | Good | Cutoff (fail = non-viable) |
|---|---|---|
| ipSAE | ≥ 0.80 | ≥ 0.60 |
| DockQ *(Challenge 1 only)* | ≥ 0.80 | ≥ 0.23 |
| ΔG (kcal/mol) | ≤ −12 | ≤ −6 |
| Interface contacts | > 25 | ≥ 10 |
| Interface pLDDT | > 80 | ≥ 65 |
| CDR SASA (Å²) | > 600 | > 250 |
| NetSolP | ≥ 0.70 | ≥ 0.50 |
| CDR-H3 identity | < 70% | < 95% |

---

## 3. The binding metrics (60% of the score)

### ipSAE — interface confidence

**What it is:** a number from 0 to 1 distilled from the folding model's
[[How Structure Prediction Works|PAE matrix]] — specifically the inter-chain block, which
describes how confident the model is about where one protein sits relative to the other.

**Intuition:** *does the model believe its own answer about how these two things fit together?*

**Why it's in the rubric:** for a designed molecule there is nothing to compare against, so
the model's own confidence is the only available signal about whether the binding pose is
meaningful.

**What it does not measure:** truth. It cannot — see [[Confidence Is Not Truth|the note on exactly this]]. A confidently wrong pose scores well.

**Calibrated:** we measured **0.841 on a pose we independently verified as correct.** Since the
good band starts at 0.80, a genuinely correct interface sits only just inside it. Anything much
above 0.85 on a *designed* molecule should raise an eyebrow, not a cheer.

### DockQ — does the pose match the real one *(Challenge 1 only)*

**What it is:** a 0–1 score comparing your predicted complex to a reference structure, mapped
onto the **CAPRI** quality classes used in the docking field: High ≥0.80, Medium 0.49–0.80,
Acceptable 0.23–0.49, Incorrect below that.

**Intuition:** *did you keep binding the same way the original did?*

**Why it exists:** Challenge 1 is a redesign of a known molecule, so there *is* a right answer
and we can check against it. Challenge 2 has no reference, which is why DockQ doesn't apply
there — and why Challenge 2 is so much riskier.

**Calibrated:** two copies of the *same* complex in the *same* crystal score **0.867** against
each other, not 1.000 — the scale below which "different pose" and "different crystal packing"
cannot be told apart. Not a ceiling; a prediction can exceed it. Ours scored **0.820**.

### ΔG — predicted binding energy

**What it is:** the free energy of binding, in kilocalories per mole. **More negative means
tighter binding.** Computed by a tool called PRODIGY.

**Intuition:** *how hard would it be to pull these two apart?*

**How PRODIGY works, and why that matters:** it is a linear regression over the *composition of
contacts* at the interface — how many are polar, charged, hydrophobic — plus properties of the
non-contacting surface. It is not a physics simulation.

**Treat it as ordinal, not cardinal.** Its published error is around 1.5–2 kcal/mol, and
roughly 1.4 kcal/mol corresponds to a *tenfold* change in binding strength. So it can rank two
designs usefully; it cannot tell you an affinity.

We learned this the honest way. PRODIGY predicted Kd = 34 pM for pembrolizumab against a
measured 29 pM, and I initially wrote that up as validation. It isn't — that agreement is well
inside the tool's noise. It was luck. What it genuinely validates is *plumbing*: the tool ran
on the right interface.

Note also that PRODIGY's ΔG is essentially a function of its own contact count, so **ΔG and
contacts are not independent evidence** despite occupying two of six binding slots.

### Interface contacts

**What it is:** the count of atom pairs, one from each protein, close enough to be touching.

**Intuition:** *how much of the two surfaces is actually in contact?*

**Calibrated:** pembrolizumab's real interface has **102**. The "good" band starts at 25. Any
genuine antibody–antigen interface clears this comfortably — it is close to a free metric, and
mostly useful for catching designs that aren't really binding at all.

### Interface pLDDT

**What it is:** the model's per-residue confidence, averaged over just the residues at the
binding interface.

**Intuition:** *is the model sure about the shape of the bit that matters?*

**Why interface-only:** a model can be confident about two proteins individually and clueless
about the contact between them. Averaging over the whole structure would hide that.

**Undefined on experimental structures** — a crystal has no pLDDT, and the field it would
occupy holds something else entirely ([[Eight Silent Failures|trap #1]]). We measured **94.4**.

### CDR SASA — is the binding surface exposed

**What it is:** *Solvent Accessible Surface Area* of the CDR loops, in square ångströms.
Conceptually: roll a water-molecule-sized ball over the protein and measure how much of the
loops it can touch.

**Intuition:** *are the grabbing loops out where they can grab, or buried inside the protein?*

**A convention the rules never specify:** is this measured on the complex (where the target
buries part of the paratope) or on the antibody alone? The two differ by hundreds of Å². We
computed both and found it **doesn't matter** — 1564 Å² bound versus 2460 Å² unbound, and the
"good" threshold is 600. Both are far above it. An ambiguity that looked dangerous turned out
to be moot, which we only know because we measured instead of arguing.

**A useful failure:** we built a deliberate decoy — pembrolizumab paired with a copy of PD-1 it
does *not* touch — and it **passed** CDR SASA at 2460 Å², because with nothing bound the loops
are maximally exposed. **CDR SASA alone cannot detect a non-interface.** That is the concrete
case for judging designs on the *minimum* of the binding metrics rather than the average.

---

## 4. Developability (20%)

### NetSolP — will it dissolve

**What it is:** a machine-learning model that predicts, from sequence alone, whether a protein
will express and stay dissolved rather than clumping together.

**Intuition:** *can this actually be manufactured?*

**Why 20% of the score for one number:** because this is where real drugs die. A molecule that
binds perfectly but aggregates in the vial is worthless. Solubility problems account for
roughly 30% of candidate failures in manufacturing development. The competition's whole framing
— *"antibodies that don't just bind, but look like real drugs"* — is aimed at this.

**A caveat worth stating:** NetSolP predicts solubility **in E. coli**, a bacterium.
Therapeutic antibodies are made in mammalian cells. So it is a proxy being applied slightly
outside its training domain. The organisers chose it, so we use it — but we note the mismatch
rather than pretending it isn't there.

**Status:** downloaded, not yet wired in. Until it runs, our harness reports viability as
*unknown* rather than *true* — it refuses to claim a design passes all eight gates when it has
only measured seven.

---

## 5. Novelty (20%)

### CDR-H3 identity

**What it is:** percent sequence identity between your CDR-H3 loop and a reference
(pembrolizumab's for Challenge 1, human germline for Challenge 2). **Lower is better.**

**Intuition:** *did you design something, or copy something?*

**Why it exists:** without it you could submit the original drug with one change and claim
credit. See [[Antibody Architecture|why CDR-H3 specifically]].

**The arithmetic, exactly:** pembrolizumab's CDR-H3 is 13 residues, so identity moves in steps
of 7.7%. One substitution (92.3%) clears the gate; **four substitutions (69.2%) earn full
marks.**

**A pleasing sanity check:** when we ran our harness on native pembrolizumab, it *failed* the
novelty gate at 100% identity. That is the metric working correctly — pembrolizumab *is* the
thing you're not allowed to copy. We initially wrote the test expecting it to pass everything,
and had to correct the test rather than the code. See [[Build the Judge Before the Contestant|the calibration note]].

---

## 6. What the metrics collectively miss

Nothing in this list asks whether the molecule would **work as a drug**.

ipSAE and ΔG do not know what a checkpoint is. A design that binds the back of PD-1 tightly and
confidently scores identically to one that blocks PD-L1. You could score 90 and have designed
something therapeutically useless.

That is why we added a check the rubric doesn't make: the fraction of the PD-L1 binding site
our antibody covers, with **58%** — pembrolizumab's own coverage — as the target. See
[[PD-1 and Checkpoint Blockade|the target note]] and [[Confidence Is Not Truth|the validation note]].
