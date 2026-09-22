# Reading the Locksmith Bio antibody hackathon spec: what is actually being scored

**Date:** 2026-09-14
**Session goal:** stand up the project folder and extract a build-ready specification
from the organisers' handbook, so that later sessions design molecules rather than
re-read the PDF.
**Source of every number below:** `source/antibody-design-hackathon-handbook.pdf`
(plain-text extraction alongside it as `.txt`). Nothing here is invented; where the
handbook is silent or self-contradictory this document says so explicitly.

---

## 0. Glossary (terms defined on first use, gathered here for reference)

| Term | Meaning |
|---|---|
| **Antibody / IgG** | Y-shaped immune protein: two identical *heavy chains* (~50 kDa) + two identical *light chains* (~25 kDa). |
| **Fv** | *Variable fragment* — the VH + VL domain pair. The minimal antigen-binding unit. |
| **Fab** | *Fragment antigen-binding* — Fv plus the first constant domains (CH1 + CL). Bigger than Fv. |
| **VH / VL** | Variable domain of the heavy / light chain. |
| **CDR** | *Complementarity-Determining Region* — one of 3 hypervariable loops per chain that touch the antigen. Six total: H1, H2, H3, L1, L2, L3. |
| **Paratope** | The antibody surface that contacts antigen (mostly CDR loops). |
| **Epitope** | The antigen surface that the paratope contacts. |
| **Antigen** | The target molecule. Here: the extracellular domain of human PD-1. |
| **Kd** | Dissociation constant, units of concentration. *Lower = tighter binding.* |
| **ΔG** | Binding free energy, kcal/mol. *More negative = tighter binding.* Related to Kd by ΔG = RT·ln(Kd). |
| **pLDDT** | AlphaFold's per-residue confidence, 0–100. Higher = model is sure about local geometry. |
| **PAE** | *Predicted Aligned Error* — AlphaFold's residue-pair error matrix, in Å. Low inter-chain PAE = the model is confident about how the two chains sit relative to each other. |
| **SASA** | *Solvent Accessible Surface Area*, Å². How much of a surface a water molecule can reach. |
| **IMGT numbering** | A standardised residue-numbering scheme for antibodies that makes "CDR-H3" a well-defined position range across different antibodies. |
| **Germline** | The un-mutated antibody gene sequence a human is born with, before somatic hypermutation. |
| **CMC** | *Chemistry, Manufacturing and Controls* — the industrial pipeline that turns a sequence into vials. Where most "good binders" die. |

---

## 1. What this competition actually asks

The organisers' framing sentence is: *"Can we computationally design antibodies that
don't just bind, but that look like real drugs?"*

That sentence is the whole design brief, and it is worth taking literally. A traditional
antibody programme takes 18–36 months from target to clinical candidate with **>90%
attrition**. The attrition is not mostly a binding problem — plenty of molecules bind.
It is a *developability* problem: the molecule aggregates, it is immunogenic, it cannot
be manufactured at 1 g/L, it deamidates on the shelf. So the scoring here deliberately
refuses to reward affinity alone. 40% of the score is non-binding.

**Target system: the PD-1/PD-L1 immune checkpoint.**

The mechanism, in four steps, because the epitope choice in Challenge 2 depends on
understanding it:

1. Tumour cells upregulate **PD-L1** on their surface, typically in response to the
   inflammatory cytokine IFN-γ. (This is the tumour reacting to being attacked.)
2. PD-L1 engages **PD-1**, an inhibitory receptor on tumour-infiltrating T cells.
3. That engagement delivers an inhibitory signal — the T cell becomes *exhausted*:
   reduced proliferation, reduced cytokine output, reduced killing.
4. An **anti-PD-1 antibody** that physically blocks the PD-1/PD-L1 contact removes the
   brake and restores anti-tumour T-cell activity.

The clinical proof point is **pembrolizumab (Keytruda®)**, a humanised IgG4κ anti-PD-1
antibody, Kd ≈ **29 pM** for human PD-1, >$25 bn/year in sales. Its mechanism is
*competitive inhibition*: it binds a loop of PD-1 that overlaps the PD-L1 binding site.

**The transferable principle:** when a scoring function is multi-objective by design,
the winning strategy is almost never to maximise the headline metric. It is to find the
feasible region where *every* constraint is satisfied, and then optimise within it. The
hard-cutoff structure in §5 below makes this mathematically explicit — see §6.

---

## 2. Antibody architecture, and why CDR-H3 gets its own scoring category

Six CDR loops form the paratope, but they are not equal:

| Region | Location | Function | Variability |
|---|---|---|---|
| CDR-H1 | Heavy chain loop 1 | Antigen contact, shape complementarity | Moderate |
| CDR-H2 | Heavy chain loop 2 | Antigen contact, interface area | Moderate |
| **CDR-H3** | **Heavy chain loop 3** | **Primary specificity determinant** | **Very high** |
| CDR-L1 | Light chain loop 1 | Antigen contact | Moderate |
| CDR-L2 | Light chain loop 2 | Limited direct contact | Low |
| CDR-L3 | Light chain loop 3 | Antigen contact, VH/VL interface | Moderate |

CDR-H3 is the outlier for a genetic reason: it is generated by **VDJ recombination** at
the junction of three separate gene segments, with nucleotide addition and deletion at
both junctions. That junctional diversity produces enormous variation in both sequence
*and loop length* — far more than somatic hypermutation alone gives the other five
loops. Consequence: CDR-H3 contributes **30–50% of the paratope surface area** and is
the dominant specificity determinant.

This is why the novelty metric (20% of the score) looks *only* at CDR-H3. If you changed
five loops but left CDR-H3 alone, you would not have designed a new antibody in the sense
the organisers care about.

Pembrolizumab itself was made by **CDR grafting**: mouse CDRs transplanted onto a human
framework, then the framework optimised. That is the classical humanisation route and it
is the thing Challenge 2 is asking us to replace with de novo design.

---

## 3. The two challenges

| | **Challenge 1: Remix Keytruda** | **Challenge 2: Invent the Future** |
|---|---|---|
| Difficulty (organisers') | ★★★☆☆ | ★★★★★ |
| Starting point | PDB **5GGS** (Keytruda Fab + PD-1) | Blank canvas |
| Objective | Redesign heavy-chain CDRs (H1, H2, H3), keep binding | Design a complete VH/VL de novo |
| Distinguishing metric | **DockQ** + ipSAE | ipSAE only (no reference structure) |
| Max score | 100 | 100 |

**Total = Challenge 1 (100) + Challenge 2 (100) + Presentation (50) = 250 points.**

Both challenges are optional in the sense that the submission checklist says
`TEAM_NAME_Challenge1/ and/or TEAM_NAME_Challenge2/`. **One design only per challenge** —
there is no "submit ten, keep the best". That single constraint is the most important
strategic fact in the whole handbook: it converts the problem from *generate-and-rank*
into *generate, rank internally, and bet on one*. All the selection pressure has to be
applied by our own local re-implementation of their metrics.

For Challenge 2 the epitope is a free choice: same epitope as pembrolizumab, a different
one, or a multi-epitope approach. Nothing in the scoring rewards blocking PD-L1
specifically — ΔG and ipSAE do not know what a checkpoint is. A design that binds the
back of PD-1 tightly scores the same as one that blocks the interface. Worth knowing;
worth *not* exploiting if the pitch (50 points, human judges) is meant to be defensible.

---

## 4. The scoring function, exactly

### 4.1 Category weights

| Category | Weight | Component metrics |
|---|---|---|
| Binding & structure quality | **60%** | ipSAE, DockQ*, ΔG, contacts, interface pLDDT, CDR SASA |
| Developability | **20%** | NetSolP solubility score |
| Novelty | **20%** | CDR-H3 sequence identity |

\* DockQ is computed for Challenge 1 only.

### 4.2 The formula

```
Final Score (0–100) = [ 0.60 × Binding_struct + 0.20 × Developability
                        + 0.20 × Novelty ] × 10
```

where each of the three category terms is on a **0–10** scale. The pipeline description
(step 6) says category scores are formed by **averaging the 0–10 sub-scores of the
metrics within that category**. So:

- `Binding_struct` (Challenge 1) = mean of 6 sub-scores: ipSAE, DockQ, ΔG, contacts,
  interface pLDDT, CDR SASA.
- `Binding_struct` (Challenge 2) = mean of **5** sub-scores (no DockQ).
- `Developability` = the single NetSolP sub-score.
- `Novelty` = the single CDR-H3-identity sub-score.

The ×10 at the end is what takes a 0–10 weighted average onto the 0–100 point scale.

**Worked example (Challenge 2).** Suppose a design scores ipSAE 9, ΔG 7, contacts 9,
interface pLDDT 8, CDR SASA 6 → `Binding_struct = (9+7+9+8+6)/5 = 7.8`. NetSolP lands at
0.72 → `Developability = 9`. CDR-H3 identity to germline is 62% → `Novelty = 10`.

```
Final = [0.60 × 7.8 + 0.20 × 9 + 0.20 × 10] × 10
      = [4.68 + 1.80 + 2.00] × 10
      = 8.48 × 10 = 84.8 points
```

Note what that arithmetic implies: **the two single-metric categories are worth 40% of
the score between them, and each is far easier to max out than the six-metric binding
average.** Novelty is nearly free — push CDR-H3 identity below 70% and take 10/10. A
NetSolP of 0.70 also takes 10/10 and is a sequence-only property, cheap to screen in
bulk before any structure prediction. Meanwhile the binding average is dragged down by
its worst member, because it is a *mean over six*. Improving the weakest binding
sub-score from 5 to 9 is worth `0.60 × (4/6) × 10 = 4.0` points; improving an already-good
one is worth nothing. **Optimise the minimum of the binding sub-scores, not the mean.**

### 4.3 Metric bands (raw value → 0–10 sub-score)

| Metric | Good (9–10) | Medium (6–8) | Poor (0–5) | Min required | Applies to |
|---|---|---|---|---|---|
| ipSAE | ≥ 0.80 | 0.60 – 0.80 | < 0.60 | ≥ 0.60 | Both |
| DockQ | ≥ 0.80 | 0.49 – 0.80 | < 0.49 | ≥ 0.23 | Ch 1 only |
| ΔG (kcal/mol) | ≤ −12 | −10 to −12 | > −10 | ≤ −6 | Both |
| Interface contacts | > 25 | 15 – 25 | < 15 | ≥ 10 | Both |
| Interface pLDDT | > 80 | 70 – 80 | < 70 | ≥ 65 | Both |
| CDR SASA (Å²) | > 600 | 300 – 600 | < 300 | > 250 | Both |
| NetSolP | ≥ 0.70 | 0.50 – 0.70 | < 0.50 | ≥ 0.50 | Both |
| CDR-H3 identity | < 70% | 70 – 90% | > 90% | < 95% | Both |

The band edges are stated as closed/overlapping intervals in the handbook (e.g. ipSAE
"≥0.80" good and "0.60–0.80" medium both contain 0.80). Do not design to sit exactly on
a boundary; the tie-breaking rule is unspecified and we should not be the team that
discovers it the hard way.

---

## 5. The hard cutoffs — a viability gate, not a penalty

This is the part that changes how we should search.

> **Designs failing ANY minimum threshold are marked non-viable and ranked *below all
> viable designs*.**

| Metric | Minimum | Consequence of failure |
|---|---|---|
| ipSAE | ≥ 0.60 | Interface not confident → non-viable |
| DockQ (Ch 1) | ≥ 0.23 | CAPRI "Incorrect" → non-viable |
| ΔG | ≤ −6 kcal/mol | Weak predicted binding → non-viable |
| Contacts | ≥ 10 | Insufficient interface → non-viable |
| Interface pLDDT | ≥ 65 | Low-confidence structure → non-viable |
| CDR SASA | > 250 Å² | CDRs not accessible → non-viable |
| NetSolP | ≥ 0.50 | Poor solubility → non-viable |
| CDR-H3 identity | < 95% | Trivial clone → non-viable |

Eight independent gates, all of which must pass. Combined with **one submission per
challenge**, the objective is not "maximise expected score" — it is closer to
**"maximise score subject to a high probability that all eight gates pass."** A design
predicted at 92 points that sits at ipSAE 0.61 is a worse bet than one predicted at 80
with ipSAE 0.78, because our local metric estimates will not agree perfectly with the
organisers' pipeline run, and any disagreement that crosses a gate costs *everything*,
not a few points.

**Practical consequence for later sessions:** build margin into every gate, and quantify
the local-vs-official reproduction error before choosing. The relevant question is not
"what does my design score?" but "how far is my design from the nearest cliff, in units
of my own measurement noise?"

**Transferable principle:** whenever a scoring system combines a continuous score with
hard feasibility gates and allows only one submission, the optimisation target changes
from the score to a *risk-adjusted* score. This is the same structure as a
constrained-optimisation problem where constraint violation is infinitely penalised, and
it shows up far outside biology — deployment gates in ML, compliance thresholds, and
any "you get one shot" submission process.

### 5.1 A note on the per-challenge criteria lists

§3.1 and §3.2 of the handbook list only a *subset* of the cutoffs per challenge
(Challenge 1 mentions novelty, DockQ, ipSAE, NetSolP; Challenge 2 mentions novelty,
ipSAE, ΔG, NetSolP). The pipeline section's table marks contacts, interface pLDDT and
CDR SASA as applying to **both**. **Treat §7.2 (the table above) as authoritative** — it
is the one that describes what the automated pipeline actually does, and it is strictly
the more demanding reading. Designing to the weaker list risks non-viability on a gate
we chose to ignore.

---

## 6. What each metric actually measures

**ipSAE — interaction prediction Score from Aligned Errors.** Derived from the AlphaFold
**PAE matrix**: for each residue pair (i, j), PAE[i][j] is the model's expected
positional error (Å) of residue j when the structure is aligned on residue i. For a
*complex*, the inter-chain block of that matrix is the interesting part — if the model
genuinely knows how the two chains dock, the inter-chain errors are small. ipSAE
condenses that into a 0–1 interface-confidence value. The pipeline runs ipSAE on
`design_X_pae.json` + `design_X_complex.pdb`, **reads rows with `Type = max` for
antibody-vs-antigen chain pairs, and takes the best ipSAE among them.** That detail
matters: it is a max over chain pairings, so a strong VH–antigen interface can carry the
score even if VL contributes little.

*What it does not measure:* whether the binding is real. It measures whether the
predictor is *self-consistent*. A confidently-predicted wrong answer scores well. This is
the single biggest known weakness of the whole evaluation, and it is why ΔG (a separate,
physics-flavoured estimate) is in the rubric alongside it.

**DockQ (Challenge 1 only).** Compares our complex to the reference Keytruda–PD-1
structure (5GGS) and returns 0–1, mapped to **CAPRI** quality classes: High ≥ 0.80,
Medium 0.49–0.80, Acceptable 0.23–0.49, Incorrect < 0.23. It is a *pose-preservation*
check: did the redesigned antibody keep binding the same way the original did.

**The central tension of Challenge 1 lives here.** Novelty wants CDR-H3 identity < 70%
(for 10/10); DockQ wants the binding pose unchanged (≥ 0.80 for 10/10). CDR-H3 supplies
30–50% of the paratope. Rewriting it aggressively while holding the pose fixed is the
actual scientific difficulty of Challenge 1, and any approach that trivially satisfies
one will fail the other. Expect to trade: e.g. accept DockQ in the Medium band (6–8) to
buy Novelty 10/10. Run the arithmetic per candidate — with six binding sub-scores,
losing 3 points on DockQ costs `0.60 × (3/6) × 10 = 3.0` final points, while gaining 4 on
Novelty is worth `0.20 × 4 × 10 = 8.0`. **Novelty is worth roughly 2.7× more per
sub-score point than any single binding metric in Challenge 1** (and 2.2× in
Challenge 2, where the binding mean is over five). That asymmetry is the most exploitable
feature of this rubric.

**ΔG — binding free energy, kcal/mol.** Computed by **PRODIGY** on the complex PDB;
PRODIGY predicts affinity from interface contact composition rather than from a full
force field. More negative = stronger. Therapeutic antibodies need nM–pM affinity
(pembrolizumab: 29 pM). Note ΔG here is computed from *our* predicted structure — so a
bad structure gives a confidently wrong ΔG. It is "physics-based" only in the sense that
it is not the same failure mode as ipSAE; it is not an independent measurement.

**Interface contacts.** Count of intermolecular antibody–antigen atom contacts. Proxy for
buried surface area. Also PRODIGY-derived, so contacts and ΔG are strongly correlated by
construction — they are *not* two independent votes, despite occupying two of the six
binding slots.

**Interface pLDDT.** Mean AlphaFold per-residue confidence over interface residues, 0–100.
Low values indicate local disorder or uncertainty. Note that flexible CDR-H3 loops are
*intrinsically* lower-pLDDT than framework regions, so this metric structurally penalises
long, unusual H3 loops — another quiet pull against aggressive novelty.

**CDR SASA, Å².** Total solvent-accessible surface area of the CDR loops. CDR residues are
identified by **IMGT-style numbering**, then SASA computed over those atoms. Rationale:
buried or occluded CDRs cannot engage antigen. Bands: > 600 Å² good, 300–600 medium,
< 300 poor, > 250 required.

*Caution:* SASA is computed on the complex PDB. Whether the pipeline computes CDR SASA in
the bound state (where the paratope is partly buried by antigen, lowering SASA) or on the
isolated antibody chains is **not specified in the handbook**. These give materially
different numbers — a well-buried, high-contact interface would *reduce* bound-state CDR
SASA, putting this metric in direct opposition to the contacts metric. This is an open
question to resolve empirically before optimising against it; see §9.

**NetSolP — solubility, 0–1.** A sequence-only predictor of the probability that the Fv
expresses and stays soluble. Run on the **Fv sequence extracted from the FASTA**, with
per-chain scores combined into one value per design. Why it is 20% of the score on its
own: solubility problems cause roughly **30% of candidate failures during CMC**. It is
the cheapest possible filter — no structure needed — so it should run first, on every
candidate, before anything expensive.

**CDR-H3 identity, %.** CDR-H3 is located by IMGT-like patterns, aligned to a reference,
and percent identity computed. Reference differs by challenge: **Keytruda's CDR-H3 for
Challenge 1, human germline CDR sequences for Challenge 2.**

---

## 7. Submission format — where teams get disqualified

The handbook's own words: submissions that do not follow the exact structure "will fail
automated validation and may be disqualified." Missing files = disqualification. This is
mechanical and therefore entirely preventable; it should be a scripted check, not a human
one.

```
TEAM_NAME.zip
└── TEAM_NAME/
    ├── TEAM_NAME_Challenge1/
    │   ├── structures/
    │   │   ├── design_X_complex.pdb
    │   │   └── design_X_pae.json
    │   ├── sequences/
    │   │   └── design_X.fasta
    │   ├── metrics/        (optional — our own CSVs/tables)
    │   └── docs/           (optional — methods, README; judges read these)
    ├── TEAM_NAME_Challenge2/     (same layout)
    └── pitch/
        └── TEAM_NAME_presentation.pptx
```

**Invariants that must hold, and what breaks if they don't:**

1. **Master folder name == TEAM_NAME exactly**, and the zip is `TEAM_NAME.zip`.
   Violation → automated validation fails.
2. **`design_X` prefix is free-form but must match across all three files** of a design
   (`design_X_complex.pdb` ↔ `design_X_pae.json` ↔ `design_X.fasta`). Violation → the
   pipeline cannot pair structure with PAE; metrics cannot be computed.
3. **The FASTA contains exactly three records with exactly these headers:**
   `>Heavy_Chain`, `>Light_Chain`, `>Antigen`. Violation → sequence-derived metrics
   (NetSolP, CDR-H3 novelty) fail.
4. **Chain assignment in the PDB: Chain A = heavy, Chain B = light, Chain C = antigen.**
   Violation → the pipeline pairs the wrong chains when computing interface metrics; this
   is the failure mode most likely to produce *plausible but meaningless* scores rather
   than an obvious error.
5. **One design per challenge.** No hedging.

The handbook's example heavy chain runs past the variable domain into CH1 and ends in a
**His-tag (`…HHHHHH`)** — i.e. the example is a **Fab**, not an Fv, and carries a
purification tag. But NetSolP is documented as running on the **Fv (VH+VL)**. So the
pipeline is expected to *extract* the Fv from whatever we submit. Open question (§9):
whether to submit Fab-length chains matching their example, or Fv-only. Their example is
the safer precedent.

---

## 8. Recommended toolchain

Only the "used in pipeline" tools bind us; the rest are our choice.

**Structure prediction (must produce a PAE file — this is non-negotiable, since
`design_X_pae.json` is required):** AlphaFold-Multimer via ColabFold/LocalColabFold,
AlphaFold3 via AlphaFold Server, IgFold (antibody-specific), ABodyBuilder2, ESMFold
(single-chain, fast).

Note that IgFold/ABodyBuilder2/ESMFold do not natively emit AlphaFold-style PAE JSON;
the required artefact effectively pins the final structure step to an
AlphaFold-Multimer-class predictor even if faster tools are used for iteration.

**Generative design:** ProteinMPNN (fixed-backbone sequence design — the natural fit for
Challenge 1's "redesign CDRs on an existing scaffold"), LigandMPNN (interface-aware,
conditions on the binding partner), RFdiffusion (de novo backbone generation conditioned
on a target — the natural fit for Challenge 2), ESM-IF (inverse folding),
AbLang/AntiBERTy (antibody language models for generation and scoring).

**Evaluation — in the official pipeline:** ipSAE, DockQ (Ch1), PRODIGY, NetSolP.
**Optional:** FoldX (ΔΔG mutation scanning), Rosetta interface analysis, CamSol,
TANGO/Aggrescan, TAP, IgBLAST/ANARCI.

We should re-implement the four pipeline tools locally. Not optional — see §5, the whole
strategy depends on knowing our margin to each gate before we submit.

**Reference structures:** 5GGS (pembrolizumab Fab + PD-1, 2.0 Å — *the* primary
reference), 5DK3 (pembrolizumab Fab alone, 2.3 Å), 5IUS (PD-1/PD-L1 complex, 2.45 Å —
use this to define the epitope we need to block), 5WT9 (nivolumab–PD-1, 2.4 Å — a second,
independent anti-PD-1 solution to learn from).

---

## 9. Developability beyond the scored metric

NetSolP is the only *scored* developability term, but the handbook lists six pillars, and
the pitch is judged by humans who will know them. Concretely actionable during design:

- **Solubility:** NetSolP ≥ 0.50 (required), CamSol > 1.0 (recommended).
- **Aggregation:** TANGO total < 500; also Aggrescan, SAP.
- **Immunogenicity:** NetMHCIIpan / IEDB for T-cell epitopes; humanisation score > 85%.
- **Chemical stability — the concrete motif rules, which are cheap string checks:**
  - Deamidation: `NG, NS, NT, NH, ND` → consider N→Q
  - Isomerisation: `DG, DS, DT, DD, DH` → consider D→E
  - Oxidation: exposed `M, W, H, C` → bury, or M→L
  - N-glycosylation sequon: `N-X-S/T` where X ≠ P, anywhere in the Fv → N→Q or S→A
- **Humanisation:** preferred frameworks IGHV1-69, IGHV3-23, IGHV4-59, IGKV1-39,
  IGLV1-51; T20 score > 80; IgBLAST/IMGT DomainGapAlign for germline assignment.
- **Manufacturability:** titre > 1 g/L, Tm > 65 °C, pI 6–9, viscosity < 20 cP at
  150 mg/mL.

**These motif rules are a ~20-line filter and should run on every generated sequence
before any structure prediction.** They cost nothing and they are exactly the kind of
thing that makes a 3-minute pitch credible to a judge who does this for a living.

---

## 10. Open questions and contradictions found in the handbook

Logged because they are cheap to resolve by asking the organisers and expensive to
discover late.

1. **Dates do not match the calendar.** The handbook is titled *11–14 December 2025* and
   the stated deadline is **14 December 2025, 12:00 noon IST**. Today is **2026-09-14** —
   the file was downloaded today but describes an event nine months past. Either this is
   an archived handbook being used as a reference for a *re-run*, or the dates are stale
   boilerplate for an upcoming edition. **Resolve this first: it determines whether this
   project has a deadline at all.**
2. **Presentation length is stated twice, differently.** §4.4 says "3 minutes maximum";
   the §4.5 checklist says "5 min, PPT format". §11.4 repeats "3-minute". Prepare for
   **3 minutes** (the majority reading and the stricter one), with material to expand to 5.
3. **CDR SASA: bound or unbound?** Not specified whether SASA is computed on the complex
   with the antigen present. The two readings conflict in sign with the contacts metric
   (see §6). Determine empirically by computing both on the 5GGS reference and seeing
   which lands in a sensible band.
4. **Fab or Fv for submission?** The example FASTA is Fab-length with a His-tag, but
   NetSolP is documented as running on Fv. Follow the example unless told otherwise.
5. **Band-edge tie-breaking** is undefined (e.g. ipSAE exactly 0.80). Avoid the edges.
6. **Per-challenge criteria lists are incomplete** relative to the pipeline's cutoff
   table (§5.1). Assume the stricter table.
7. **Contacts and ΔG are not independent** — both come from PRODIGY on the same interface
   — yet they occupy two of six binding slots. This means the binding category is
   effectively weighted toward PRODIGY's view of the interface more than the metric count
   suggests.

---

## 11. What a healthy design looks like, concretely

A Challenge 2 candidate we would be willing to submit:

- ipSAE ≥ 0.80, comfortably above the 0.60 gate (margin > 0.15)
- ΔG ≤ −12 kcal/mol (gate is −6; a design sitting at −7 is one prediction-noise event
  from non-viable)
- Interface contacts > 25
- Interface pLDDT > 80
- CDR SASA > 600 Å²
- NetSolP ≥ 0.70
- CDR-H3 identity to germline < 70%
- Zero N-glycosylation sequons in the Fv, no NG/DG motifs in CDRs, no exposed Met in CDRs
- Predicted pI in 6–9

That profile scores 10/10 on every band and clears every gate with margin. It is the
target, not the expectation.

---

## 12. What is not done yet

Stated plainly so nothing here oversells:

- **No design work has happened.** This session produced the project skeleton and this
  specification only.
- **No tool has been installed or run.** ColabFold, ProteinMPNN, RFdiffusion, PRODIGY,
  ipSAE, NetSolP, DockQ are all unavailable locally at time of writing.
- **The local scoring harness does not exist.** §5 argues it is the critical path; it is
  entirely unwritten.
- **No reference structure has been downloaded.** 5GGS et al. are named only.
- **GPU feasibility is unassessed.** The machine is an RTX 5070 Ti Laptop (Blackwell,
  `sm_120`) which requires CUDA ≥ 12.8 / torch ≥ 2.7-cu128 — relevant to every one of
  these tools, and a known trap from previous work on this machine.
- **Every number in this document is transcribed from the handbook, not verified against
  a running pipeline.** The organisers' implementation is the ground truth; this is our
  reading of their description of it.
