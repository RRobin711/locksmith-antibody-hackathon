# Chapter 11 — Study plan: how to actually learn this

## What this chapter teaches

The other chapters explain the campaign. This one is about getting the material
into your head, which is a different problem. It gives a reading order, a
prerequisite curriculum for the gaps, a set of exercises whose answers are
checkable against the repository, and a longer track for rebuilding the system
yourself.

The organising principle: **you do not understand a measurement until you can
say what it would look like if it were lying to you.** Every exercise below is
built to produce that reflex, because it is the one skill this project actually
demonstrates.

---

## 1. Reading orders

Pick the one that matches why you are here.

### 1.1 The nine-hour pass — "I want to understand what happened"

Read in this order, roughly one hour each:

1. [[00-orientation|Orientation]] — the four questions
2. [[07-the-campaign|The campaign]] — the nine days as narrative
3. [[01-the-biological-problem|The biological problem]]
4. [[02-the-engineering-problem|The engineering problem]]
5. [[04-measurement-theory|Measurement theory]]
6. [[05-experiment-design|Experiment design]]
7. [[06-allocation-and-selection|Allocation and selection]]
8. [[08-what-broke|What broke]]
9. [[09-critique|The critique]]

Skip [[03-the-toolchain|the toolchain]] on a first pass and return when you need
to actually install something.

### 1.2 The transferable pass — "I do not care about antibodies"

This is the honest recommendation for most readers. The measurement theory here
is field-independent: it applies to A/B testing, model evaluation, benchmark
design, hiring, or any setting where you rank noisy candidates and pick the best.

1. [[00-orientation|Orientation]] §1.3 and §2 only
2. [[04-measurement-theory|Measurement theory]] — all of it
3. [[05-experiment-design|Experiment design]] — all of it
4. [[06-allocation-and-selection|Allocation and selection]] — all of it
5. [[09-critique|The critique]] §2 and §6

That is four to five hours and it is where the compounding knowledge lives.

### 1.3 The practitioner pass — "I am going to build something like this"

Add [[03-the-toolchain|the toolchain]] and [[08-what-broke|what broke]] to the
transferable pass, then work the Track B exercises in §4. Read
[[02-the-engineering-problem|the engineering problem]] with `config/metrics.yaml`
open beside it.

---

## 2. Prerequisite curriculum

Eight tiers, ordered by leverage. You do not need all of them, and the ordering
is deliberately not the conventional one — the statistics comes early because it
is what most people are missing and what pays back fastest.

**Tier 1 — Measurement theory (highest leverage; start here).** Classical test
theory: `observed = true + error`. Reliability as a variance ratio. The
[[04-measurement-theory#2. The intraclass correlation, and metrics that turn out to be constants|intraclass correlation]]. [[04-measurement-theory#3. Spearman–Brown: what averaging buys|Spearman–Brown]]. Attenuation. Range restriction. If you
learn only one tier, learn this one; it is what
[[04-measurement-theory|Chapter 04]] teaches and it is what the project spent
five sessions discovering the hard way.

**Tier 2 — Inference and power.** Confidence intervals, the Fisher-z
transformation, statistical power, and above all the **detectable-effect
standard**: a null result is meaningless unless you state the effect you could
have detected. Partial correlation. Resampling and permutation tests.

**Tier 3 — Scientific software practice.** Version control from the first line.
Invariant testing. Mutation testing. Configuration as data. Determinism and
resumability. This tier is cheap and the project's own record shows what skipping
it costs.

**Tier 4 — Protein structure basics.** Amino acids, the peptide backbone, the PDB
format, chains, residue numbering, RMSD, solvent-accessible surface area,
interfaces. Enough to read a structure file and know what you are looking at.

**Tier 5 — Antibody architecture.** Heavy and light chains, Fv/Fab/IgG, the six
CDRs, framework regions, V(D)J recombination and why CDR-H3 is special, IMGT
numbering.

**Tier 6 — Structure prediction.** What a folding model does. MSAs and
co-evolution. pLDDT, PAE, ipTM, [[03-the-toolchain#4.3 ipSAE — interface confidence from the PAE|ipSAE]] and what each is a statement *about*.
Recycling and diffusion sampling. Training cutoffs and memorisation.

**Tier 7 — Design tools.** [[03-the-toolchain#2.1 ProteinMPNN|ProteinMPNN]], [[03-the-toolchain#2.2 RFdiffusion via RFantibody|RFdiffusion]], and their limits — notably
that ProteinMPNN optimises sequence recovery given a backbone, which is not the
same objective as anything you care about.

**Tier 8 — Developability.** Glycosylation sequons, [[01-the-biological-problem#6.2 The NG deamidation motif in Challenge 1's CDR-H2|deamidation]] motifs,
isoelectric point, aggregation propensity, immunogenicity. Deferrable until you
have a design worth criticising.

---

## 3. Self-test questions

Answer these from memory before checking. If you cannot, reread the named
chapter. Answers are all recoverable from the repository.

**On measurement** ([[04-measurement-theory|Ch 04]])

1. A metric has an intraclass correlation of 0.003 across random seeds. What does
   that tell you about using it to rank designs, and what does it tell you about
   the *designs*?
2. Two noisy measurements each with [[04-measurement-theory#1.3 Reliability|reliability]] 0.75 have a true correlation of
   0.80. What correlation will you observe? Why must you never report the
   corrected value as if it were observed?
3. You measure reliability 0.965 on a panel spanning a wide quality range, then
   apply it to a shortlist spanning one tenth the range, with identical noise.
   What happens, and why is this not a noise problem?
4. Why is "shortlisting destroys reliability" a statement about the *selection
   step* rather than about the measurement?

**On inference** ([[05-experiment-design|Ch 05]])

5. You measure a correlation of −0.168 with p = 0.69 at n = 8 and conclude the
   effect is absent. State precisely what is wrong with that conclusion, and what
   you should have written instead.
6. A filter improves a pool's mean quality with p < 0.0001 but does not move the
   maximum, and the p-value for the maximum *rises monotonically* with retention
   fraction. What is that pattern the signature of?
7. Your filter beats an [[05-experiment-design#6. Equal-budget resampling, and varying the outcome|equal-budget]] random null on the outcome you chose. What
   should you do before believing it, and what did doing so reveal here?
8. Why is a null built from uniformly-drawn residues a strawman when testing
   whether a designed interface lands on a target epitope? What is the right null
   and what is still wrong with it?

**On allocation** ([[06-allocation-and-selection|Ch 06]])

9. The error of a mean falls as `1/√k`. What law governs the error of a *spread*,
   and why does that invert the depth-versus-breadth answer?
10. You pick the highest-scoring candidate from a noisy pool. In what direction is
    its score biased, by how much, and what is the correction?
11. Why can a single fresh measurement never validate a shrinkage correction,
    however closely it lands?
12. A monotone relabelling of a banded sub-score cannot change which of two
    designs scores higher — true or false? Justify carefully.

**On engineering** ([[02-the-engineering-problem|Ch 02]], [[08-what-broke|Ch 08]])

13. Name four distinct ways a structure-prediction run can exit with status 0
    having produced nothing usable.
14. A resume mechanism checks whether an output row exists before re-running.
    What is the failure mode, and what should it key on instead?
15. Why does merging a CUDA-using stage and a multiprocessing stage into one
    script kill every worker on Linux, and what is the one-line fix?
16. A config file and a module constant encode the same convention. The config is
    the declared source of truth. What actually happened here, and what did it
    cost?

**On the science** ([[01-the-biological-problem|Ch 01]])

17. A handbook lists `N→Q` and `S→A` as interchangeable fixes for a glycosylation
    sequon. What single free calculation tells you which one is safe, and what was
    the measured difference?
18. Why is whole-chain sequence identity useless as a novelty screen for
    antibodies, and what do you use instead?
19. An anti-lysozyme antibody passes every gate in a PD-1 binding pipeline. What
    does this establish, and what does it not?

---

## 4. Exercises

### Track A — analysis only, no GPU

Everything here runs on a laptop against files already in the repository.

**A1 — Reproduce the ICC table.** Take the multi-seed scores in `runs/` and
compute the intraclass correlation for each of the eight metrics. Confirm that
`contacts` and `cdr_sasa` are indistinguishable from zero and that five of eight
metrics are effectively constant across the pool. *This is the single highest-value
hour in the whole course, because it is the calculation that would have
redesigned the campaign had it been run on day 5 instead of day 7.*

**A2 — Build the equal-budget null.** Implement the resampling test: draw random
subsets of the same size the filter retains, and compare the filter's mean and
maximum against those distributions. Reproduce the result that the filter wins on
the mean and not the maximum. Then re-run it with each of the six scored metrics
as the outcome and reproduce the six-row table that refutes the filter.

**A3 — Verify the band-relabelling counterexample.** The composite depends only
on the multiset of the six binding bands plus two more, so there are 252 distinct
designs on the grid. Enumerate them with exact rational arithmetic and find the
ordering reversals between the midpoint and top band mappings. Confirm there are
39, and explain in one sentence why "monotone" was not sufficient.

**A4 — Settle the Spearman–Brown inconsistency.** Reconcile the 7-seed-mean
reliability of 0.629 against the single-seed figures of 0.276 and 0.296. Show
that 0.629 reproduces as `1 − 0.176²/0.290²`, then show that the two remain
mutually inconsistent, and quantify by how much. This is a real open item in the
project, not a made-up exercise.

**A5 — Audit a claim you choose.** Pick any numeric claim in any `results/*.md`
file. Find its provenance, its n, and its estimand. Decide whether it is stated
at the right resolution. The project's own auditors found errors at roughly one
per twenty claims; see whether you can match that rate.

### Track B — with compute

**B1 — The eight-fold negative control.** Fold a known-wrong antibody against
your target and score it through your gates. Eight folds. If it passes, you have
learned more than a hundred folds of ranking would have taught you.

**B2 — Vary one inherited parameter.** Pick any setting you copied from somewhere
else and run a two-level arm. Six folds. Compare against the effort you were
about to spend assuming it was fine.

**B3 — The diffusion-sample envelope.** Fold the same input with one sample and
with five. Fifty-four extra seconds. Report the range rather than the point
estimate, forever afterwards.

**B4 — The decoy-patch control.** This is the experiment the project never ran
and still needs: condition backbone generation on hotspots on the *opposite face*
of the target and compare epitope coverage. It is the only design that separates
"conditioning steers the interface" from "the geometry would have gone there
anyway." A few GPU-hours and a few dollars.

### Track C — rebuild it

Work through [[02-the-engineering-problem|Chapter 02]] and implement the pipeline
yourself, in this order — which is deliberately *not* the order the project used:

1. Encode the rubric as data, with every unspecified convention as an explicit switch.
2. Write the five invariant tests. `git init` first.
3. Calibrate against a known-good complex and a deliberate decoy that must fail.
4. Run a twenty-design baseline.
5. **Compute the ICC and dynamic range of every metric on that baseline.**
6. Run the negative control.
7. *Only now* size a campaign.

Steps 5 and 6 are the ones the project did in the wrong place, and doing them in
the right place is the entire lesson.

---

## 5. A checklist to keep

Pin this somewhere. Every line is paid for by an incident in the record.

**Before you measure anything**
- [ ] Does this metric vary across my candidates at all? (ICC, dynamic range)
- [ ] Does it respond to the thing I care about? (knockout or ablation control)
- [ ] What does a known-wrong input score?

**Before you believe a number**
- [ ] What is its n?
- [ ] What is its estimand — single observation, k-replicate mean, pool mean?
- [ ] What effect could I have detected at this n?
- [ ] Which script and which run directory produced it?

**Before you believe a null**
- [ ] State it as "no effect larger than x." If you cannot name x, do not report it.

**Before you believe a filter or a rule**
- [ ] Does it beat the *same rule applied at random* at equal budget?
- [ ] Does it survive when I change the outcome variable?
- [ ] Does my null match the *geometry* of the thing it is a null for?

**Before you trust a parameter**
- [ ] Did it cross a task boundary? If so it is an untested hypothesis — vary it once.

**Before you trust a passing control**
- [ ] Which confound does it eliminate? What is it silent about?

**Before you ship**
- [ ] Does the validator re-derive every number from the delivered files alone?
- [ ] Does the headline lead with what I actually believe?

---

## What to take away

The project's own closing lesson is an ordering rule, and it is the thing to
practise:

> **Establish that your measurement carries signal before spending anything on
> its precision. Run the cheap falsifying experiment first, because it is the one
> that can make all the expensive work unnecessary.**

Almost everything this campaign took nine days to learn was learnable in two. The
negative control cost eight folds. The metric reliability table cost nothing at
all. The chapter that explains why they came last is [[09-critique|the critique]];
the chapters that explain why they matter are
[[04-measurement-theory|measurement theory]],
[[05-experiment-design|experiment design]] and
[[06-allocation-and-selection|allocation and selection]].
