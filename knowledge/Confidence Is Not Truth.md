---
date: 2026-09-15
tags: [project, idea, AI, pattern, learning]
status: living
---

Tags: [[Idea|ideas worth keeping]] · [[AI, ML|AI and ML]] · [[Pattern|patterns worth reusing]] · [[Learning|things I'm learning]]

# Confidence Is Not Truth

**Why this note exists:** this is the intellectual centre of the project. Everything else is
machinery; this is the reason the machinery is arranged the way it is.

---

## 1. The structural problem

Six of the eight scored metrics are computed from files **we generate ourselves** — our
predicted structure and our predicted confidence matrix. The organisers do not re-fold
anything. Only two metrics come from the sequence.

So most of the score is a function of a structure we produced, judged by a confidence measure
we also produced.

And [[How Structure Prediction Works|as covered elsewhere]], confidence measures describe the
model's opinion of its own output. They never touch reality — they *cannot*, because for a
molecule that has never been synthesised there is no truth to compare against.

**Therefore a confidently wrong answer scores well.**

## 2. "Any team can hill-climb ipSAE"

**Hill-climbing** is the simplest optimisation there is: make a small random change, keep it if
the score went up, discard it if not, repeat. No gradients, no theory. Works on any score you
can evaluate repeatedly.

ipSAE is cheap to evaluate — our folds take 34 seconds. So:

```
seq = starting_design
for _ in range(1000):
    candidate = mutate_one_CDR_residue(seq)
    if ipSAE(fold(candidate)) > ipSAE(fold(seq)):
        seq = candidate
```

About fifteen lines, and roughly a day of laptop GPU time. It will absolutely find sequences
the model is very confident about.

**Why that's bad:** this is **Goodhart's law** — *when a measure becomes a target, it ceases
to be a good measure.*

The mechanism here is specific. A folding model is confident when its input resembles cases in
its training data where the answer was unambiguous. So hill-climbing ipSAE does not push
sequences toward *binds PD-1 well*; it pushes them toward *looks like a textbook complex to
this particular model*. Those correlate — which is exactly why ipSAE is useful at all — but
optimisation pressure eats the correlation. Push hard enough and you are constructing
**adversarial examples for the folding model**.

The analogy I keep coming back to: **ipSAE asks the witness "how sure are you?" instead of
checking the alibi.** You can coach a witness into confidence. It tells you nothing about
whether the story is true.

## 3. The uncomfortable part: we do this accidentally

It would be comfortable to treat the above as a warning about other people. It isn't.

**Selection is optimisation.** Our pipeline generates ~10,000 candidates, folds the survivors,
and picks the best-scoring one. That *is* a hill-climb — executed in one parallel step instead
of a thousand sequential ones. We don't have to intend anything for the mechanism to operate.

The statistical name is the **winner's curse**. If every measured score is `true value +
noise`, and you take the maximum over N samples, your winner is disproportionately likely to be
one whose *noise* happened to be favourable. The inflation grows with N. So **the score we
report for our chosen design is systematically optimistic, and the harder we screen, the worse
it gets.**

This flips the whole validation programme from an ethics argument into a self-interested one.

**The concrete mitigation:** whatever design we name "best", we re-predict it with **fresh
random seeds** and re-score. That estimate is unbiased, because the design was not selected
using it. If the score drops materially, the gap *is* the curse, and the runner-up may be the
better molecule. We record both numbers and quote the clean one.

## 4. What actually constitutes evidence

If confidence isn't proof, what is? Four independent lines, none of which can be produced by
hill-climbing a single model's confidence.

### Cross-predictor consensus

Fold the same design with **different models** — Boltz, AlphaFold, Chai — and check whether
they agree on the pose.

*Why it works:* a confidently-wrong answer is usually confidently wrong in **one model's
idiom**. Different architectures, trained differently, have different blind spots. Agreement
between them is evidence that survived the selection process rather than evidence manufactured
by it.

### Specificity controls

Predict our designed antibody against **unrelated targets** — lysozyme, or PD-L1 itself.
Confidence should **collapse**.

*Why it works:* a binder that "binds" everything has learned the predictor, not the target.
This is the single cheapest test for the failure mode we most fear, and almost nobody runs it.

### Hotspot ablation

Identify the two or three residues contributing most to the interface, mutate them to alanine
(the smallest useful amino acid — effectively deleting a side chain), and re-score. Binding
should **collapse**.

*Why it works:* a real interface has structure — specific residues doing specific work. If
removing the load-bearing contacts changes nothing, then what the tool liked was diffuse noise
that happened to accumulate, not an interaction.

### Epitope overlap

Measure what fraction of PD-L1's binding site our antibody actually covers, against
pembrolizumab's measured **58%**.

*Why it works:* this is the only check in the entire project that asks whether the molecule
would **function as a drug**. [[The Eight Metrics|Nothing in the rubric asks this]] — ipSAE and
ΔG do not know what a checkpoint is. A design could score 90 and bind the wrong face of PD-1.

## 5. Why this is the actual deliverable

We are not submitting to the competition. The point is to produce something a computational
biology lab would find genuinely good.

Given that, **hitting the numbers is not the achievement — anyone willing to hill-climb can hit
the numbers.** Demonstrating that the numbers correspond to something real is the achievement,
and it is the part most teams skip because the rubric doesn't reward it.

There is also a fit argument. Locksmith Bio's science is
[[Intrinsically Disordered Proteins|intrinsically disordered proteins]] — molecules with no
single fixed structure, properly described as *ensembles* rather than single shapes. A lab
whose founding insight is "the average is the wrong statistic" is not going to be impressed by
a high confidence score. They are going to ask how you know it means anything.

## 6. The ensemble bridge — offered carefully

There is a genuine connection between our problem and their science, and it is worth stating
without overclaiming.

[[Antibody Architecture|CDR-H3]] is the most conformationally variable element in an antibody —
that is precisely why it determines specificity and why it is hard to design. Representing it
as a single set of coordinates plus one confidence number is exactly the modelling failure the
IDP field exists to correct.

So: characterise CDR-H3 as a **distribution**. Sample across seeds and predictors, report the
spread, and show whether the designed interface is supported by a *converged* loop or by one
lucky sample.

This is cheap — it falls out of the multi-seed folding we do for consensus anyway — and it is
a stronger claim than ipSAE can make. It is one line of evidence among several, not a
headline. Worth doing; not worth overselling.

---

**Related:** [[Build the Judge Before the Contestant|validating the scoring first]] ·
[[How Structure Prediction Works|where confidence numbers come from]] ·
[[Intrinsically Disordered Proteins|why ensembles beat point estimates]]
