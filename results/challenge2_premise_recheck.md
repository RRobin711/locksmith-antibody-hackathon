# Re-examining the premise: does the case for Challenge 2 still stand?
**2026-09-21.** Prompted by Lecture 8's decision-drift entry. Reconstructed from
`results/challenge2_scope.md`, `PLAN.md` and the session log — not from memory.

## What the original decline actually said (2026-09-20)

`results/challenge2_scope.md` recommended: **"Do the germline novelty metric. Do not run
either design campaign."** Its own framing of the reasoning matters:

> *"The reasoning is this project's own evidence, not schedule pressure."*

Three objections, all about **what a Challenge 2 score could mean**, none about feasibility:

1. **Challenge 2 removes the only metric that can detect a wrong pose.** No DockQ, so
   nothing in the rubric compares the prediction to anything external. Cited evidence: the
   novelty probe's arms B and C carry *identical* `cdrh3_identity` (53.8%), the same band
   and the same contribution to `final`, while differing by **227 antigen contacts**.
2. **The predictor is measurably unreliable at exactly this task.** Median Fab DockQ
   **0.291** on five complexes released after Boltz-2's verified cutoff — the de novo
   placement problem, measured, on this hardware.
3. **SKEMPI bounds what a Challenge 2 score could mean.** No metric tracks measured
   affinity; ΔG failed the epitope-knockout control outright. So a design clearing
   ipSAE ≥ 0.60 and ΔG ≤ −6 clears two numbers shown not to report binding.

Conclusion: *"a Challenge 2 submission would be 100 points of score attached to no evidence."*

## Each objection, one at a time

| # | Objection | Status | Detail |
|---|---|---|---|
| 1 | no external pose check | **narrowed by argument** | We built `pod/check_backbone.py`: deterministic, non-self-referential, works at n=1. But **audit 10.6, written by me, says it tests conditioning, not binding.** It answers "did the diffusion aim where told", not "is the pose right". Two designs can both contact hotspots with entirely different, both-wrong poses. The objection is narrowed, not answered. |
| 2 | Boltz median DockQ 0.291 post-cutoff | **never revisited** | Nothing since has re-measured it. RF2 as an independent filter is new, but **audit 10.5 says model agreement is not validation** — shared PDB training data, correlated errors expected. The 0.291 applies exactly as it did. |
| 3 | SKEMPI: nothing tracks affinity | **never revisited, and now worse** | See below. |

**What WAS answered by measurement: feasibility.** The scope doc costed Route A at
*"1–3 days, high risk"* and said *"install risk is the whole story."* That is now resolved —
RFantibody runs, measured end to end at 48 min/backbone on CPU, with a native install path
on any pre-Blackwell GPU.

> **But feasibility was never the basis of the decision.** The decline was explicitly
> evidential. **We spent three days resolving the objection that was not load-bearing.**
> That is the drift, stated precisely: each step answered the previous step's blocker, and
> the blocker chain began at *"can we run it"* when the decision had been made on
> *"should we, given what a score would mean."*

## The harder half: what has strengthened the case AGAINST

Three things, none of which has been weighed anywhere:

1. **Challenge 2's own novelty metric turned out to be free.** We built the germline metric
   *because the decline told us to* — and validating it produced finding 5.5: pembrolizumab's
   CDR-H3 scores **53.8%** to germline against a **<95%** cutoff, so the gate is free.
   *(An earlier version of this line claimed the metric "cannot distinguish a therapeutic's
   loop from a shuffle of it". That was **false and is withdrawn**: the 2000 scrambles have
   mean 21.5%, sd 6.1%; pembrolizumab at 53.8% is the MAXIMUM of those draws, ~+5.3 sd out,
   empirical p ~ 1/2000. The metric discriminates decisively. The error was comparing a
   single observation to the MAXIMUM of an aggregate — the project's own catalogued
   mistake.)* The scope doc's own arithmetic notes that with DockQ gone,
   novelty is worth **2.4×** any single binding metric in Challenge 2. **We have now shown
   that 2.4×-weighted metric cannot distinguish a licensed therapeutic's loop from a shuffle
   of it.** This is a fourth metric shown not to mean what it says, and unlike the others it
   is specifically a *Challenge 2* metric.
2. **The metric-validity audit landed after the decline and makes objection 3 stronger**, not
   weaker: four of eight metrics constant, contacts ICC 0.003, CDR SASA 0.000, ΔG blind to
   527 deleted contacts and scoring the winner better against TIM-3 than against PD-1.
3. **There may be no valid selection rule at all** (audit 10.1). The decline did not
   anticipate this. We discovered we cannot rank the output, and today's prereg picks a rule
   *tactically* without asking whether the exercise still clears the original bar.

**Has any of this been weighed against the original decision? No.** `challenge2_scope.md`
has not been revisited since 2026-09-20 17:26. Nothing in the intervening work went back to
it.

## State of play, as it is

**We are not submitting.** `PLAN.md` §15: *"We are not submitting to this hackathon. Ajitesh
shared it; we are doing it for the learning and to produce something genuinely good for a
potential collaborator. The value is the quality of the science, not a rank."* **So "100 of
250 points" is not a real quantity for us** — there is no scoreboard. The handoff document
leans on that framing and should not.

**Unestablished, flagged rather than reasoned around:**

- **Per-backbone wall-clock on an A5000.** Everything downstream is bracketed off an
  unmeasured figure. The last bracketed figure in this project (RF2 at 4 min/sequence)
  measured **7.1** — 1.75× off.
- **Pod setup wall-clock.** 1–1.5 h is an estimate; no pod has been run.
- **Gate pass rate.** Completely unknown.
- **Whether ICC ≥ 0.32**, i.e. whether *any* selection rule exists.
- **Whether there is a live deadline.** `PLAN.md:507` lists "live deadline" as a question to
  *ask Ajitesh*. It was never answered. There is no deadline on record.

**Cost from here:** pilot ~1 h and **~$0.27**. Production at N=30, if the bracket holds,
perhaps 3–4 h and a further ~$1–2. **Cash is trivial (~$2–5 all in). The real cost is
session hours** — writing `02_production.sh`, analysis, packaging, docs.

**What it adds beyond the finished package and the deck:** a demonstration that we can drive
RFdiffusion/RFantibody — genuine tooling competence, which neither the Challenge 1 package
nor the deck shows. **What it does not add:** a validated design. §7.4 already concedes this.

**What it costs the deck if it overruns:** much less than 24 h ago, because the outline now
exists and slide 5 is deliberately fillable. **That risk is largely retired** — by sequencing
the deck first.

## Verdict

**The case to proceed stands — but it is a different and much smaller case than the one we
have been walking toward, and it justifies the pilot block only.**

It is *not* "Challenge 2 is worth 100 points." It is: *a ~1-hour, ~$0.30 pilot demonstrates
we can drive the real de novo tooling, and slide 5 improves if it lands.* That case is
forward-looking and survives on its own.

**The sharpest point: the pilot block already delivers the entire thing that justifies
proceeding.** Ten backbones through diffusion → MPNN → RF2, with the conditioning check and
the timing, *is* the demonstration of tooling competence. Production at N=30 adds a design we
cannot rank (10.1), cannot validate (objections 1–3, unrefuted), and will not submit (§15).

**So: run the pilot. The case for production does not currently stand independent of
momentum, and should be re-decided on the pilot's numbers against the original three
objections — not against whether the pilot itself succeeded.** A successful pilot is
evidence the tooling works. It is not evidence that a Challenge 2 design would mean anything,
because the three objections were never about the tooling.

*"We already wrote the scripts" is not a reason. "The marginal cost is now $0.30 and an
hour" is one — but it buys the demonstration, not the campaign.*
