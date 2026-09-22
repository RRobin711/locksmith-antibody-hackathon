---
date: 2026-09-17
tags: [project, protein-design, structure-prediction, problem, learning]
status: living
---

Tags: [[Protein Design|protein design]] · [[Structure Prediction|structure prediction]] · [[Problem|debugging]] · [[Learning|things I'm learning]]

# The memorisation test, and what it cost Challenge 2

> ⚠️ **SUPERSEDED IN PART — read [[2026-09-17-validating-the-inputs-and-withdrawing-a-result|the validation doc]] first.**
> Four of the five targets were folded from coordinate-derived sequences with internal loops
> spliced out. Re-run from SEQRES: the verdict is **MARGINAL, not FAIL** (median Fab DockQ
> **0.291**, not 0.157); the ipSAE 'calibration collapse' is **withdrawn** (Spearman **+0.900**,
> not +0.308); and the two 'confident but completely wrong' predictions were **artefacts**. The
> wrong-epitope structural observation stands; the inference that ipSAE cannot detect it does not.
> The method, pre-registration and target selection below are unaffected.

**Session:** 2026-09-17. **Result:** the post-cutoff test **fails** on the pre-registered
criterion. Boltz-2 does not recover antibody–antigen binding modes on complexes it has not
seen, and ipSAE's apparent calibration does not survive the move to novel structures.
**Prerequisites:** [[2026-09-17-the-fv-screen-fails-and-ipsae-is-a-liveness-test|the panel doc]] for the ipSAE↔DockQ curve this is tested against. Everything needed is restated below.

---

## 1. Why this test existed

Every empirical claim in this project traced to 5GGS, released 2017 and therefore inside
Boltz-2's training data. The caveat had been carried honestly since 2026-09-15, but it had
become load-bearing for two things:

1. **Challenge 2's viability**, which requires placing an antibody the model has never seen.
2. **The finding from earlier today** that ipSAE is a liveness test rather than a ranking
   metric — derived entirely from mutants of a memorised complex.

If confidence behaves differently on novel structures, the second is an artefact rather than a
property, and the first has no support at all.

---

## 2. Establishing the cutoff, and the method

**Boltz-2's cutoff is 2023-06-01 on PDB *release* date.** Read out of the paper directly rather
than taken from a search summary, because this project has been burned by a web summariser
inventing numbers from a PDF before:

> "We use every PDB structure up to the training date cutoff of 06/01/2023."
> "...all entries from the MD datasets correspond to PDB structures released before the
>  validation cutoff date of 2023-06-01"

The second sentence is what fixes it to release rather than deposition date. Margin adopted:
targets released **≥ 2024-01-01**, at least seven months clear.

Everything below was **pre-registered** in `results/prereg_post_cutoff_test.md` before target
selection and before any fold — the pass/marginal/fail bands, the curve comparison, and the
declared limits of what n=5 could detect.

### 2.1 The scope check, which changed the design

The brief proposed folding as Fab and comparing to the panel curve with residual sd 0.043. But
0.043 is the **Fv** curve; the Fab curve's residual sd is **0.088**. Minimum detectable offset
(two-sided, α=0.05, power 0.80):

| n targets | vs Fv curve (sd 0.043) | vs Fab curve (sd 0.088) |
|---|---|---|
| 3 | 0.076 | 0.157 |
| **5** | **0.062** | **0.128** |
| 8 | 0.053 | 0.109 |

Fab-only at n=4 gives MDE **0.140** — unable to detect even the AF2-sized offset of 0.131. The
test as scoped would have been close to useless. So **both constructs** were folded and the Fv
comparison made primary.

Why the Fv curve is tighter even though Fv ipSAE is the *less reliable* instrument (seed
reliability 0.607 vs 0.965): the Fv's elbow noise is **correlated between ipSAE and DockQ**,
because both are read off the same structure, so a wobbly elbow moves a point *along* the curve
rather than off it. Fv is a poor absolute instrument and a good relative one. This does not
conflict with G1c, which concerned ranking.

---

## 3. Target selection — where the test lives or dies

63 RCSB hits (release ≥ 2024-01-01, ≥3 protein entities, ≤3.2 Å) → 28 after filtering to exactly
three entities, ≤700 residues, antigen ≥60 aa, and no promiscuous antigen (lysozyme, spike, HA,
gp120, SARS, HIV, influenza).

**Full-chain identity is the wrong novelty measure and nearly told us nothing.** Every antibody
shares framework, so the closest pre-cutoff relative was 0.86–0.94 identical for *all twelve*
shortlisted candidates — none near the 0.95 rejection bar. Useless as a discriminator.

**CDR-H3 identity separates them properly.** For each candidate the heavy chain was searched
against the PDB, hits filtered to release < 2023-06-01, the twelve closest fetched, and each
numbered with ANARCII to extract CDR-H3. That spread the pool from 21.4% to 70.0%.

| PDB | released | antigen | class | Fab res | CDR-H3 novelty |
|---|---|---|---|---|---|
| 9JBQ | 2024-09-11 | PcrV | bacterial (*P. aeruginosa*) | 555 | **21.4%** |
| 9BQW | 2025-08-06 | Decorin-binding protein A | bacterial (*Borrelia*) | 560 | **28.6%** |
| 8TBB | 2024-08-28 | TIM-3 | human checkpoint | 541 | **31.2%** |
| 9W43 | 2026-07-01 | PD-1 | human checkpoint | 507 | **38.5%** |
| 8RWB | 2025-02-12 | ULBP6 | human MHC-I-like | 601 | **44.4%** |

Chain roles were assigned by **ANARCII, not by PDB chain labels**, because TIM-3, PD-1 and ULBP6
are all Ig-superfamily and number as antibody-like; `MIN_V_DOMAIN_SCORE = 25` is what keeps an
antigen out of the antibody slot. Measured: true V domains scored 30.2–31.0, every antigen 0.0.

9VXL was rejected *before folding* on VRAM (670 res → ~10.8 GB predicted of 12.2 GB available).
9W43 is reported separately as well as pooled: its antigen is PD-1, which is thoroughly
represented pre-cutoff, making it simultaneously the most **deployment-relevant** point (novel
antibody, known target — exactly Challenge 1 and 2) and the most **flattered**.

---

## 4. The result

Ten folds, Fv and Fab, seed 1, untemplated, antibody chains `empty` MSA, existing driver, no
special-casing. DockQ here is **genuine accuracy** — each target against its own released
crystal, same molecule, answer the model has not seen.

| target | Fv DockQ | Fv ipSAE | Fab DockQ | Fab ipSAE |
|---|---|---|---|---|
| 9JBQ | 0.074 | 0.000 | 0.061 | 0.128 |
| 9BQW | 0.053 | 0.000 | 0.064 | **0.707** |
| 8TBB | **0.852** | 0.674 | **0.676** | 0.579 |
| 9W43 | 0.070 | **0.722** | 0.157 | 0.104 |
| 8RWB | 0.236 | 0.319 | 0.291 | 0.353 |
| *5GGS (memorised)* | *0.820* | *0.841* | *0.818* | *0.807* |

### 4.1 Level — Challenge 2 go/no-go: **FAIL**

Median Fab DockQ **0.157**, 1/5 ≥ 0.49. The pre-registered FAIL band was median < 0.23.
Median Fv DockQ 0.074.

**A drop of 0.661 DockQ from the memorised complex.** Four of five fall below 0.23, the CAPRI
*acceptable* floor — the binding mode is not recovered at all, not merely recovered imprecisely.
The single success (8TBB: Fv 0.852, Fab 0.676) proves the pipeline is capable, so these are
model failures and not harness failures.

**The 0.820 on 5GGS was substantially retrieval.** That number never generalised, and now it is
measured rather than suspected.

### 4.2 Relationship — the calibration does not survive

The pre-registration asked: on the curve, above it, or below it? **None of those.** The
relationship collapses.

| | Fv | Fab |
|---|---|---|
| mean residual | −0.213 (**−9.6 SE**) | −0.131 (**−2.9 SE**) |
| residual sd of the new points | **0.294** vs panel 0.043 → **6.9× inflation** | **0.256** vs 0.088 → **2.9×** |
| Spearman ipSAE↔DockQ | **+0.308** (p=0.61) | **+0.200** (p=0.75) |
| *panel comparison* | *+0.815* | *+0.754* |

The mean sits below the curve, but that description is misleading: the spread explodes and one
point sits **+6.2 sd above**. It is not a shifted calibration; it is the absence of one. The
panel's R² of 0.919 describes behaviour on a memorised complex and nothing else.

### 4.3 The failure mode that matters

| | ipSAE | DockQ | |
|---|---|---|---|
| 9W43 Fv | **0.722** | **0.070** | confident, completely wrong |
| 9BQW Fab | **0.707** | **0.064** | confident, completely wrong |
| 8TBB Fv | 0.674 | **0.852** | the only correct prediction — scores *lower* than both failures |

**ipSAE ranks two catastrophically wrong predictions above the only correct one.** Both clear the
rubric's 0.60 cutoff; one clears 0.70. A funnel keyed on ipSAE promotes both and discards nothing.

---

## 5. Why ipSAE is fooled — the mechanism

The failures are **not** failures to dock:

| prediction | Ab–Ag contacts <5 Å | min distance | DockQ |
|---|---|---|---|
| 9JBQ Fab | 428 | 1.6 Å | 0.061 |
| 9BQW Fab | 470 | 2.0 Å | 0.064 |
| 9W43 Fab | 608 | 2.2 Å | 0.157 |
| 8RWB Fab | 544 | 1.8 Å | 0.291 |
| 8TBB Fab | 629 | 1.7 Å | 0.676 |

Every failed prediction builds a **large, well-packed interface**. The model docks confidently to
the *wrong epitope or the wrong orientation*. And that is precisely why ipSAE cannot catch it:
**ipSAE scores the interface the model built, and the PAE is the model's opinion of its own
output.** A confidently-built wrong interface is, to ipSAE, indistinguishable from a confidently-
built right one. No PAE-derived metric can see that an epitope is wrong, because nothing in the
PAE knows where the epitope should have been.

**This is the transferable point.** A self-assessed confidence metric cannot detect a
systematically wrong answer that the model is confident about. It measures internal consistency,
not correctness. Detecting wrong-epitope docking needs *external* evidence — a different
predictor, an orthogonal assay, or a known epitope constraint.

### 5.1 It is not about antibody novelty

- Fv: Spearman(CDR-H3 novelty, DockQ) = +0.300, p = 0.62
- Fab: +0.700, p = 0.19

If anything the sign is positive. The most novel antibody (9JBQ, 21.4%) and the least (8RWB,
44.4%) both failed; the success sits in the middle. Antibody–antigen docking is simply hard once
the answer is not in the training set. **Nothing about a better-chosen design would have fixed
these predictions.**

---

## 6. What this costs the project

**Challenge 2 (M4) should not proceed as designed.** It asks the pipeline to invent an antibody
against a specified epitope and validate it computationally. The validation step is now measured
to fail: on novel complexes the predictor puts the antibody in the wrong place 4 times in 5, and
the confidence metric intended to catch that instead rewards it. Generating designs whose only
evidence is Boltz ipSAE would produce numbers with no demonstrated relationship to truth.

Per the milestone's own framing, **a characterised failure is a legitimate M4 outcome** and this
is a well-characterised one, obtained for 82 minutes of GPU time rather than a full campaign.

**Challenge 1 is damaged but not dead.** It is template-protected — the reference structure is
supplied — so predictions are anchored to a known binding mode rather than having to discover
one. But two of its supports are gone: DockQ against the 5GGS crystal is no longer independent
evidence of anything (the model has seen that crystal), and ipSAE cannot be trusted to rank.
Selection should lean on the binding gates that do not derive from PAE, and on the fact that
Challenge 1 designs are *perturbations of a known binder* rather than novel placements.

**Note the most deployment-relevant point is a failure.** 9W43 is a novel antibody against PD-1 —
the project's actual antigen, thoroughly memorised. Fab DockQ **0.157**. A memorised antigen did
not rescue a novel antibody.

---

## 7. Pushback on the brief

**The target-selection criteria were nearly self-defeating, in the way the brief suspected.** The
instruction to "prefer targets with no close relative in the PDB" is not satisfiable for
antibodies: framework conservation puts every antibody at 86–94% identity to something
pre-cutoff. Had that been applied literally as a full-chain filter, either zero targets would
have qualified or the filter would have passed everything depending on the threshold. The measure
has to be CDR-specific, and saying so is most of the work.

**The "avoid ubiquitous antigens" criterion pulls against deployment relevance.** The most
informative single target, 9W43, has a thoroughly memorised antigen — and it is informative
*because* that mirrors the real task. A strict reading would have excluded it and lost the most
transferable data point. Antigen memorisation and antibody memorisation should be screened
separately, not merged into one exclusion.

**n=5 was adequate here only because the effect was enormous.** The pre-registration declared MDE
0.062 against the Fv curve and accepted an ambiguous outcome in advance. The observed effect was
not subtle — residual spread inflated 6.9×, individual points at −10.8 and +6.2 sd — so n=5
settled it easily. Had the true effect been a 0.05 shift, this design would have returned
"ambiguous" and that would have been the honest answer. **The pre-registration is what makes that
statement credible**, since the bands were fixed before any number existed.

**One retry, disclosed.** `9w43__fv__s1` failed on a transient MMseqs2 server error
(`tarfile.ReadError: not a gzip file`) and was re-run once with identical settings. That is a
re-run of a network failure, not a settings change; no other fold was repeated and no target was
added, removed or substituted after any result was seen.

---

## 8. State after this session

**The post-cutoff test is closed: FAIL**, on the pre-registered criterion, with the mechanism
identified.

**Scope now attached to every earlier empirical claim.** DockQ 0.820, ipSAE 0.841, the
ipSAE↔DockQ curve, the liveness finding and the AF2 offset all describe behaviour **on a
memorised complex**. §4.2 shows that at least the calibration does not transfer.

**Recommended next decisions — for the user, not made here.**
1. Drop or radically rescope M4 (Challenge 2), recording the characterised failure as its result.
2. Re-plan Challenge 1 selection around non-PAE evidence.
3. If cross-predictor consensus is to be the external check §5 argues for, it needs a predictor
   that runs on designs — which AF2 cannot do without a local MSA database. Chai-1 is the
   candidate.

**Unchanged and still open.** Fold batching (~1.8×). M2 baselines and the funnel. `select/`,
`submit/`, `validate/` remain empty.
