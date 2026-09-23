# Chapter 09 — Critique: a rigorous project, badly ordered

## What this chapter teaches

Every preceding chapter explains what was done and why it worked. This one asks
whether it should have been done that way at all. The verdict, argued below and
supported by numbers recoverable from the repository, is that the campaign was
**methodologically rigorous and strategically mis-sequenced**: it asked its
questions in almost exactly the reverse of cost order, spending the expensive
non-falsifying effort first and the cheap decisive effort last.

That is not a criticism of care. It is a criticism of *scheduling*, and
scheduling is the thing most easily transferred to the next project. Read this
chapter as a description of a failure mode you will have too, not as an audit of
one person's nine days.

A note on standing. Three of the findings below were produced in this session
and appear nowhere in the project's own record. Two of them contradict
statements written in files the project treats as authoritative. Where that is
so, I say it plainly and show the check, because a critique that asks for
verifiable claims must make verifiable claims.

---

## 1. What was genuinely excellent

Criticism is worthless without a baseline, and the baseline here is high. Five
things in this project are better than professional practice, not merely
adequate for a hackathon.

**Building the judge before the contestant.** `PLAN.md` §3 puts the scoring
harness and its ground-truth calibration on day one, and gates everything behind
G0: *the harness reproduces ground truth; pembrolizumab passes every binding gate
and fails novelty; the decoy is rejected.* This ordering bought two results that
would have been invisible otherwise. Pembrolizumab itself scores **76.0 and is
non-viable**, failing the novelty gate at 100% CDR-H3 identity — a harness that
scored the parent as viable would have been silently wrong about the one molecule
whose answer is known in advance. And **20 of 20** baseline ProteinMPNN designs at
defaults clear all eight gates, which establishes that the gates do not bite on
fixed-backbone redesign. Without that baseline, *"our funnel produced twenty
viable designs"* would have read as an achievement rather than as a measurement
of the gates' inertness.

**Pre-registration that cost something.** Eleven pre-registration documents exist
and at least three fired against the author's interest. `results/specificity.md`
records the pre-declared failure condition triggering on TIM-3 in 2 of 3 seeds,
and notes explicitly that *the arm mean would have passed* — the rule was written
per-seed before the data existed and was applied as written. The design ships
carrying a cross-reactivity caveat that a post-hoc analysis choice would have
removed. Rarer still,
`results/prereg_2026-09-22_calibration_and_negative_control.md` contains a
section headed *"Honest disclosure of what was already seen"*, naming a complex
whose numbers were visible before the pre-registration was written and explaining
why that weakens the instrument. Most people who pre-register do not also
document the contamination of their own pre-registration.

**Nulls with matched geometry.** The epitope knockout in `results/validity.md` §1
carries a matched off-interface alanine control, a fresh MSA for every mutant so
the alignment cannot leak native residues back, and a dose–response across 0, 349
and 527 deleted antigen contacts. It yields a falsifiable partition: ipSAE moves
**17.1×** its own seed standard deviation, interface pLDDT **64.0×**, while
PRODIGY ΔG moves **0.9×** and contacts **1.2×** — the last two are blind. The
composition-matched CDR-H3 scramble holds length, composition, aromatic count and
charge constant, so every cheap sequence feature the project used as a predictor
is controlled by construction.

**Withdrawing published claims, with replacement numbers.** Twenty-four
substantive withdrawals in nine days, each carrying the corrected value rather
than a deletion. The habit is real and it is rare.

**Asking the therapeutic question nobody asked.** `results/pdl1_competition.md`
opens: *"Every metric in the rubric asks whether the antibody binds PD-1. None
asks whether it does the job."* Both designs occlude the PD-L1 footprint (16/18
and 17/18 residues), and the write-up correctly labels the result conditional.

---

## 2. The ordering error, which is the whole critique

### 2.1 Precision before validity

The project spent five sessions building increasingly sophisticated theory about
**how precisely it was measuring**: Spearman–Brown, disattenuation, range
restriction, optimal allocation, winner's-curse shrinkage. Every one of those is
an answer to *"how noisy is my ruler?"* None of them touches *"is my ruler
measuring the thing I care about?"*

When validity was finally measured, on day 7, the answer was severe.
`results/metric_validity.md` — whose own opening line notes it was written *after
an independent audit pointed out that six days had been spent on ranking
precision and none on whether the ranked quantities carry design information* —
found `contacts` at **ICC 0.003** and `cdr_sasa` at **ICC 0.000**: pure sampler
noise. **Five of the eight rubric metrics are constants across the pool.** The
eight-metric harness ranks on three. And of those three, `results/validity.md`
shows that PRODIGY ΔG is **blind to the epitope** — 0.9× its own seed standard
deviation against a 527-contact deletion — while carrying the largest single
share of the ranking variance.

The timing is the indictment. The 239-design campaign ran 2026-09-18 to
2026-09-19. The validity work ran 2026-09-20. So the campaign, the 20×7 reseed,
the shortlist-depth simulation, the winner's-curse estimator and the allocation
study were all executed against a ranking whose largest contributor cannot see
the interface and whose nominal eight dimensions were actually three.

An ICC table is arithmetic over folds already on disk. It costs **zero new
folds**. Computed after the 20-design baseline on day 5, it would have redesigned
the campaign. The correct order is: build the harness, run a baseline, **measure
each metric's ICC and dynamic range on that baseline**, then size a campaign. The
project did steps one, two, four, three.

### 2.2 The fold ledger

Recovered from `pae_*.npz` modification times:

| day | 09-14 | 09-15 | 09-16 | 09-17 | 09-18 | 09-19 | 09-20 | 09-21 | 09-22 |
|---|---|---|---|---|---|---|---|---|---|
| Boltz folds | 0 | 2 | 18 | 49 | 120 | 375 | 507 | 0 | 195 |

Total 1,266. **564 of them — 45% — were spent before the first validity
experiment existed** (`scripts/48_epitope_knockout.py`, 2026-09-20 11:53), and
most of that day's 507 ran concurrently with it rather than informed by it.

Set that against the cost of the experiments that actually bound what the project
can claim. The negative control cost **eight folds**, and
`results/negative_control.md:9` says it plainly: *"It costs eight folds and
nobody ran it for a week."* The metric ICCs cost nothing. The light-chain
refutation cost nothing. The diffusion-sample envelope cost **54 seconds** —
five samples take 2m54s against roughly 2m for one, because the MSA, trunk and
recycling are shared and only the diffusion head reruns.

### 2.3 Inherited parameters — seven, not one

The project names this failure once, about `recycling_steps=3`. It is a pattern
with at least seven members:

| inherited setting | from | examined | consequence |
|---|---|---|---|
| `recycling_steps=3` | Challenge 1 | day 9 | published 0/30 withdrawn; ipSAE 0.263 → 0.864 |
| `diffusion_samples=1` | Boltz default | day 9 | every pose number ever reported is an **argmax** |
| 113-residue PD-1 construct | 5GGS | day 9 | the construct folded is not the construct submitted |
| NetSolP on Fab | unrecorded | day 7 | inverts which chain limits `min(VH, VL)` |
| DockQ `interface_agg` | code default | day 9 | one full band |
| antibody chains with no MSA | Challenge 1 | **never** | still open |
| Fv vs Fab for Challenge 2 | a Challenge 1 result | day 9 | exonerated by a control that was itself blind |

The general rule is stronger than the project's own phrasing: **a parameter that
crossed a task boundary is an untested hypothesis, and must be varied before any
unanimous result is interpreted.** For Challenge 2 that is roughly six folds
against the thirty spent producing a wrong answer.

### 2.4 The control that was blind

The sharpest instance deserves isolating. A positive control was built
specifically to catch the class of error that `recycling_steps` represents. It
**ran at recycling 3 itself**, passed, correctly exonerated the Fv construct
(Fab 0.776, Fv 0.842) — and printed a verdict about the Challenge 2 pool that was
wrong within the hour.

> A control eliminates the confound you thought of and is silent on the one you
> did not. A passing control reads as general reassurance and is nothing of the
> kind.

---

## 3. Three findings from this session

These are new. Each contradicts something written in the project's own files.

### 3.1 The rubric's monotonicity claim is false

`config/metrics.yaml` justifies defaulting `band_value` to `top` with this
reassurance: *"The choice is a uniform monotone relabelling, so it moves the
headline number and never the ranking."* The same claim is repeated in
`results/handbook_conformance.md`.

It is false as stated, and the reason is a clean piece of mathematics worth
teaching. The relabelling maps midpoint sub-scores to top-of-band sub-scores:
2.5 → 5, 7.0 → 8, 9.5 → 10. That map is monotone. It is **not affine**: fitting a
straight line through the two lower anchors gives a slope of 0.6667, which
predicts 9.667 at the Good anchor rather than 10.

The composite is a *weighted mean* of eight sub-scores. Applying a monotone but
non-affine transform componentwise to the arguments of a weighted mean can change
the ordering of the results. Enumerating the full band grid — the composite
depends only on the multiset of the six binding bands plus the developability and
novelty bands, so there are 252 distinct designs — and comparing with exact
rational arithmetic gives **39 strict ordering reversals**, with margins up to a
full composite point. One instance: a design with binding bands
(Poor, Poor, Poor, Poor, Poor, Good), developability Good, novelty Good scores
**60.000** under midpoint against a competitor's **61.000**, and **75.000** under
top against that competitor's **74.000**. The order flips.

What the project actually observed is that no such flip occurred *in its own
239-design pool*. That is a contingent fact about where those designs sat on the
grid, not a theorem. The config states it as a theorem. This matters because the
claim was used to dismiss the band choice as presentationally significant but
methodologically inert, and it is not inert.

This is the project's signature error — **two places encoding one fact, never
reconciled** — appearing in the config file the entire rubric hangs from.

### 3.2 `STATE.md` is stale on a headline number, in the flattering direction

`STATE.md` opens by declaring itself *"the single place to find out where the
project is"* and presents a headline table giving Challenge 2 a score of
**96.0**. But `README.md:34` and the shipped
`submission/LOCKSMITH_DEV/LOCKSMITH_DEV_Challenge2/metrics/scores.md:18` both
record **91.2**, because the design that actually shipped is the S→A
sequon-fixed variant — 4.8 composite points paid deliberately to remove two
glycosylation sequons from the paratope. The substitutions are physically present
in the packaged FASTA.

A stale headline is minor. A stale headline in the designated source of truth,
biased upward, inside a project whose thesis is that flattering numbers are the
danger, is not.

### 3.3 The `0.629` reliability puzzle resolves, and then does not

`STATE.md` §8 lists as unresolved: the reliability figure 0.629 *"does not
reproduce (plug-in gives 0.276 midpoint / 0.296 top)"*, flagged but not
corrected.

The flag is itself a category error, of exactly the kind the project catalogues
under *never diff a single observation against an aggregate*. The two numbers
estimate different things. 0.629 is the reliability of a **7-seed mean**, and
reproduces as `1 − 0.176²/0.290² = 0.6317` from the recorded between-design and
noise standard deviations. It is the correct quantity for shrinking a 7-seed
mean, which is what it was used for. The audit's 0.276 and 0.296 are
**single-seed** reliabilities.

So the flagged discrepancy dissolves — and a real one survives underneath it.
Spearman–Brown relates the two: r₁ = 0.296 implies r₇ = **0.746**, not 0.629;
r₇ = 0.629 implies r₁ = **0.195**, not 0.296. Both directions checked. There is a
genuine inconsistency in the record, it is not the one that was flagged, and it
is a two-line check for which the project already has a test idiom
(`tests/test_invariants.py:177`, `test_spearman_brown_roundtrip`).

---

## 4. Where the effort went that should not have

**The Blackwell detour.** The *diagnosis* was exemplary: Gate 0 failed by
arithmetic in about 25 minutes, inside its own 30-minute timebox, having
established that `get_arch_list()` shows no PTX entries, that both a cuBLAS
matmul and a plain ReLU fail with `no kernel image`, and that DGL silently
clobbered the CUDA build of torch. That is a feasibility gate working correctly.

The criticism is everything after. Having established that the GPU cannot run the
stack, the project spent a session building a **CPU port**: seven dedicated
scripts, three dependency walls worked around including an NVTX shim in
`sitecustomize.py`, and a measured throughput projecting 20 backbones at 16
hours. The whole thing was obsoleted the same day by renting an `sm_86` RTX 3090
for **$2.82 over 5.5 hours**, on which upstream's own pins install and run
untouched. The decision rule should fire at the Gate 0 failure, not after the
port: read the pin, read the architecture, spend three dollars.

The second-order cost is easy to miss and larger than the first. The detour
pushed Challenge 2's design work to day 8, which is *why* `recycling_steps` was
inherited, *why* the pilot was sized as a tooling demonstration rather than a
campaign, and *why* the pod volume was left unretrieved overnight. A dead end
does not only cost its own hours; it compresses everything downstream into a
window where every shortcut is forced.

**Idle GPU from a bug already written down.** `pgrep -f` self-matching cost
**4 h 22 m** of idle GPU across three separate instances. Every one of them
occurred *after* the rule had been recorded in `LEARNINGS.md`. Separately, idle
pod billing consumed roughly **$1.25 — 42% of the entire cloud spend**, more than
the pilot that produced Challenge 2.

I reproduced this bug myself while writing this chapter. Verifying the claim in
§3.1, I ran `pkill -f "from itertools import product"` to clear a slow search;
the pattern matched *its own command line* and killed the shell that issued it,
exit 144. Seventh instance, first one not committed by the project author. The
lesson generalises past its instance: **a lesson recorded in prose is not a
lesson mechanised.** The fix — gate on artefacts, never on process tables — was
written into a hook only after the sixth occurrence, and the hook is what
actually stops it.

**Optimising a component that could not move the result.** *"Redesign the
light-chain CDRs"* appeared in three documents and was echoed by two independent
reviewers over two days. The refutation is two lines of arithmetic that were
available the whole time: NetSolP aggregates as `min(VH, VL)`; the shipped
design's VH is **0.699** against a Good edge of **0.70**; therefore the maximum
over all possible light chains of `min(0.699, VL)` is 0.699, and the band cannot
move — **by 0.001**. The empirical half was free too, NetSolP being
sequence-only: 24 ProteinMPNN light chains moved VL by **+0.023** against a
required **+0.131**, none reached the edge, and all 24 introduced new CDR
liabilities.

> Under a `min` aggregator, effort on anything but the current argmin is wasted,
> and effort on the argmin is wasted past the point where it stops being the
> argmin. Compute the ceiling before recommending the work.

---

## 5. Documentation: the charge, and the defence

The raw figures invite a charge of over-documentation. Markdown runs to 18,789
lines against 18,020 lines of Python — a ratio of **1.04 : 1** — of which only
**518 lines, 2.9% of the Python, are tests**, written on the final day.

I do not think the charge holds, and the evidence is specific. Essentially every
correction in this project was found by *re-reading its own written record
against fresh data*, not by a tool. The −0.081 → −0.289 reversal was findable
because `results/ensemble_power.md` had recorded the exact partial correlation
and its n. The allocation claim was refuted because **the refuting row was
printed directly above it in the same file**. The 0.849-versus-0.856 withdrawal
happened because `results/m3_winner.md` recorded that 0.856 was an eight-seed
mean. None of those are recoverable from code. The same project with the same
code and no write-ups ships all of them silently.

The counter-argument deserves its strongest form: 62 results files is a surface
over which corrections must be propagated by hand, and **that propagation
demonstrably failed**. `PROJECT-STORY.md` — the file `README.md:13` designates as
the entry point — still presents the refuted aromatic filter as a success, still
carries the corrected allocation claim, still quotes the superseded score 87.5,
and still says *"No antibodies designed yet."* `results/calibration.md` ships an
empty results table beside power language for a design it has three observations
of. `STATE.md` carries the stale 96.0 from §3.2.

But the remedy for that is not less prose. It is **fewer places where a number is
authoritative**: one machine-readable results store that the prose reads from,
plus tests. The project reached this conclusion itself on day 9 — *"prose cannot
fail a build"*. The correct criticism is not *too much documentation*; it is
**documentation used as the storage medium for facts that belonged in a database
with a checker.**

---

## 6. The epistemics, and where I come down

The project's own thesis is *confidence is not truth*. Did it live up to it?

**What nine days established about whether these molecules bind: nothing.** The
project says so — *"Neither 96.0 is evidence of binding. Both are
self-consistency scores."* The SKEMPI retrospective is the proof: of five mutants
that experimentally abolish binding, four score essentially like the wild type,
and NL31A, at a measured ΔΔG of **+21.8 kcal/mol**, scores ipSAE **0.917**
against the wild type's **0.903**. The pipeline rates a known non-binder above
the real complex.

What the nine days *did* establish is a set of bounded negative results about the
measurement stack, and these are the actual deliverable:

1. Four of five hard cutoffs reject **0 of 6** known-wrong antibodies; viability
   rests on ipSAE alone.
2. Under the shipped default of one diffusion sample, **HyHEL-10 — an
   anti-lysozyme antibody — sweeps the entire gate set** as a PD-1 binder.
3. Five of eight rubric metrics are constants; the harness ranks on three; one of
   the three is blind to the epitope.
4. The predictor's median DockQ on genuinely novel antibody–antigen pairs is
   **0.291**.
5. A mutation that abolishes binding scores above the wild type on the primary
   gate.

That list is worth more than either composite score. **And the presentation
inverts it.** Both `STATE.md` and `README.md` lead with a table of scores and put
the epistemics in a block quote below. A reader who stops at the first table
learns the one thing the project does not believe.

### Healthy self-correction, or a biased generator?

Twenty-four withdrawals is unusual and good. But `results/audit_2026-09-20.md`
records something that cannot be waved away: *"Fourth overstatement of the day,
fourth toward a more interesting finding."*

Noise is symmetric. Four errors in one day all pointing the same direction is not
noise — it is a property of the generating process, and the process is
identifiable. The project writes its narrative *as it computes*, so the first
plausible mechanism gets committed to prose, and prose has momentum. Three
signatures support this: small-n nulls promoted to named rules twice, one of
which removed an entire axis from selection; a mechanism asserted before being
tested and later conceded as false in general; and three truncation errors in a
single day, in a project whose own `LEARNINGS.md` carries that exact rule.

**My position.** Both readings are true and the second dominates. The audits are
load-bearing, and they are **not independent of the generator** — same person,
same session, same pull toward the interesting reading. The audit-of-the-audit
finding proves it directly: the script written to catch *"the newest claim
carries the error"* carried the error on its first run. A self-correcting system
with a directional generator and a correlated corrector converges somewhere
better than the generator alone, but not to the truth, and it converges slowly
and expensively. A large fraction of days 7 through 9 went on unwinding days 2
through 6.

The genuinely admirable move is that the project ended up **measuring its own
error rate**, which almost nothing does. The mistake was what it did with that
measurement: it added more correctors instead of changing the generator. That is
the wrong intervention point.

### The rule that would have helped

The bar for writing a number into a results file should have been a four-field
stamp, mechanically checkable:

> **No number enters a results file without: (1) its `n`; (2) its estimand in
> words — "single seed", "7-seed mean", "pool mean", "median of 5 diffusion
> samples"; (3) the effect it could have detected at that `n`; (4) its
> provenance — which script, which run directory.**

Every withdrawal in this project is prevented or trivialised by one of those four
fields. Fields (1) and (3) kill both small-n nulls and the "shrinkage validated
to 0.001" claim. Field (2) kills the 0.849-versus-0.856 confusion outright *and*
the 0.629-versus-0.296 confusion that is still live today. Field (4) kills the
shipped-package error where **0.712 was quoted for the design when it is the pool
mean** — the design's own value is 0.625.

The project half-invented this rule: the pre-registration files carry the
detectable effect. It simply never applied it to numbers outside a pre-registered
experiment, which is where all the withdrawals came from.

### Goodhart

Optimising a rubric the project says does not measure binding was the **wrong
allocation and the right instrument**, and those separate cleanly.

*Right instrument*: you cannot credibly critique a rubric you have not maximised.
Demonstrating that the reachable ceiling is 95.0 under midpoint bands, that 20%
of the rubric is pinned at Medium for any pembrolizumab-framework Fab including
pembrolizumab itself, and that novelty is banded so 69% and 15% identity score
identically — none of that is available to someone who did not push the number.
The 96.0 is an *artefact of the critique*. Leading with it is the error, not
computing it.

*Wrong allocation*: the marginal fold spent moving 87.5 → 96.0 bought a
convention change and two band crossings. The marginal fold spent on the negative
control bought the HyHEL-10 result. **Eight folds against roughly eight hundred.**

---

## 7. What a professional lab would say

**Impressed by:** the post-cutoff test done properly — release date not
deposition, cutoff read from the primary PDF, CDR-H3 novelty rather than
whole-chain identity, antibody and antigen screened separately; the SKEMPI
retrospective, published null; the epitope knockout with a matched control and
dose–response; and the contact-count prediction of which developability fix is
safe, tested in both directions.

**Would call naive:** treating ipSAE as a binding gate when the project's own
data shows it floors at zero and manufactures a discontinuity the underlying
model does not have (fifteen designs at exactly 0.000 carry ipTM 0.556–0.674);
ranking on PRODIGY ΔG, a contact-count regression over an unminimised predicted
pose, with no Rosetta or FoldX cross-check; **one predictor family for all nine
days**, so every number is one model's opinion and single-model pathologies like
the recycling artefact go undetected; no relaxation before scoring contacts, SASA
or ΔG.

**Would say is simply missing:** a grep across the entire project for
`SPR|BLI|affinity maturation|wet lab|molecular dynamics|Rosetta|FoldX|MM-GBSA`
returns **one hit**, a GitHub URL. There is no experimental validation path of
any kind — no expression construct, no SPR or BLI plan, no cost estimate — in a
project whose central thesis is that computation cannot establish binding. No
affinity maturation; the designs are single-shot outputs. No molecular dynamics,
so the CDR-H3 heterogeneity work is a *sampler* proxy for flexibility rather than
a physical one. Developability stops at sequence motifs: no predicted Tm, no
aggregation propensity, no hydrophobic-patch or self-interaction proxies, no
MHC-II immunogenicity scoring.

---

## 8. Twelve recommendations, ranked by damage prevented over cost

1. **Measure every metric's ICC and dynamic range on the first baseline pool,
   before sizing any campaign.** Zero new folds. Would have redesigned the
   239-fold campaign, the 140-fold reseed and the allocation study — call it
   300–500 folds and two sessions.
2. **Write five invariant tests and `git init` before the first script.** Ninety
   minutes. Would have prevented selecting the shipped design under a convention
   the config did not declare.
3. **Vary every inherited parameter once, deliberately, before interpreting any
   unanimous result.** Six to ten folds per campaign. Would have prevented the
   0/30 withdrawal and a week of gate results a wrong antibody could pass.
4. **Run the cheapest experiment with the largest consequence first: does a
   known-wrong input clear the gate?** Eight folds, thirty minutes.
5. **Stamp every number with n, estimand, detectable effect and provenance.** A
   convention plus a lint script. Prevents or trivialises most of the
   withdrawals.
6. **Price the hardware a pinned stack was built for, in the first ten minutes.**
   Three dollars. Saves a session and the downstream compression.
7. **Compute the ceiling of any aggregator before recommending work on one of its
   arguments.** Two lines of arithmetic.
8. **One machine-readable results store; prose reads from it and never duplicates
   it.** A day of plumbing, amortised over at least four manual propagation
   passes, one of which failed.
9. **Spend the last 10% of budget on the control that could falsify, not on the
   score.** The decoy-patch control remains unrun and is still the only design
   that could falsify the conditioning result.
10. **Lead with the negative results; put the score in an appendix.** Free.
11. **Cross-check any ranking metric against a second predictor family before
    ranking on it.** One install and one panel refold.
12. **Write the one-page experimental validation plan even with no lab.** An
    hour. Converts *"we cannot know whether it binds"* from a limitation into a
    costed next step, which is the first question any reviewer asks.

---

## What to take away

Almost everything that took nine days to learn was learnable in two, and the
project's own record proves it: the negative control cost eight folds, the metric
ICCs cost zero, the light-chain refutation cost zero, the nivolumab diagnosis
cost no GPU time at all, and the diffusion-sample envelope cost fifty-four
seconds. The expensive things — 1,266 folds, an allocation theory, a
winner's-curse estimator, a shortlist-depth simulation — were all answers to
*how precisely am I measuring?*, asked before anyone had established that the
thing being measured carried signal.

The single transferable lesson is therefore not any individual bug. It is an
ordering rule:

> **Establish that your measurement carries signal before you spend anything
> improving its precision. Run the cheap falsifying experiment first, because it
> is the one that can make all the expensive work unnecessary.**

The project's greatest strength is that it eventually asked the right question
about itself, in writing, repeatedly, and paid to answer it. Its greatest
weakness is that it asked in the reverse of cost order. That ordering, not any
individual defect, is the thing worth teaching — and it is the reason this
chapter exists rather than a list of bugs.

See [[08-what-broke|the full failure catalogue]] for the incident-level record,
[[04-measurement-theory|the measurement theory]] for the reliability machinery
discussed in §3.3, [[06-allocation-and-selection|allocation and selection]] for
the banding mathematics of §3.1, and [[11-study-plan|the study plan]] for how to
practise avoiding all of it.
