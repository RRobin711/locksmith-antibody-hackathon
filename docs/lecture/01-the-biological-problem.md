---
date: 2026-09-23
tags: [project, lecture, learning, antibody, protein-design]
status: review
---

# 01 — The Biological Problem

> ⚠️ **Challenge 2's computational evidence was withdrawn on 2026-09-23** — every Challenge 2 fold used a silently discarded antigen alignment. See [corrections C1 and C2, and what they do and do not invalidate](CORRECTIONS.md) — C2 also refutes the contact-count rule this course calls its best finding. Challenge 1 is unaffected.

**What this chapter teaches.** Why anyone would want to design an anti-PD-1 antibody at all, and
what "designing" one has to mean if the result is to be a drug rather than a number. We start from
the cell biology — what a T cell is, what the PD-1 brake does, how a tumour pulls it — and build up
through antibody architecture, residue numbering, and the specific patch of protein surface this
project aimed at, to the six chemical liabilities that decide whether a molecule survives contact
with a manufacturing plant. Then we look at what the campaign actually found: two glycosylation
sequons sitting on the binding residues, a sixty-fold difference between two textbook-equivalent
fixes, and a cross-reactivity failure. The chapter ends with the uncomfortable part — a careful
account of what a score of 96.0 out of 100 does and does not tell you about whether the molecule
binds. It does not tell you much. Companion chapters:
[how the scoring harness that produced those numbers was built](02-the-engineering-problem.md)
and [which tool computed which number and how it lies](03-the-toolchain.md) .

No prior biology is assumed. Every term is defined at first use and collected in
[the glossary](10-glossary.md).

---

## 1. The brake on the immune system

A **T cell** is a white blood cell that patrols the body looking for cells that should not be
there. T cells are genuinely capable of recognising and killing cancer cells; this is not
speculative, and it is the entire premise of the drug class we are about to discuss
(`knowledge/PD-1 and Checkpoint Blockade.md:18-34`).

Because an immune system that kills without restraint would destroy its host, T cells carry
inhibitory receptors — molecular brakes. The one that matters here is **PD-1**, short for
*Programmed cell Death protein 1*. It is a receptor on the T-cell surface, and its job is
*peripheral tolerance*: it stops your immune system attacking your own tissue. Structurally, PD-1
is a type-I transmembrane protein of the CD28/immunoglobulin superfamily: a single extracellular
**IgV domain** (a β-sandwich fold we will meet again in §4.5), a transmembrane helix, and a
cytoplasmic tail carrying two signalling motifs, an ITIM and an ITSM. When PD-1's ligand engages
it, the ITSM recruits the phosphatase SHP-2, which strips phosphate groups off the T cell's own
activating machinery — most importantly CD28 — damping the PI3K/AKT and Ras/ERK pathways. The
project's own notes stop at "the T cell calms down", which is correct but coarse; the intracellular
detail is supplied here because you need it to understand why blocking the *outside* of the
receptor is sufficient.

The ligand is **PD-L1** (*Programmed Death-Ligand 1*). Healthy cells display PD-L1 as a
"stand down" signal. The system works.

### 1.1 How a tumour exploits it

Many tumours **upregulate** PD-L1 — and crucially, often *in response to being attacked*. T cells
attacking a tumour release interferon-gamma (IFN-γ); the tumour answers by displaying more PD-L1.
The cycle recorded in `knowledge/PD-1 and Checkpoint Blockade.md:38-51` runs:

1. A T cell finds the tumour and attacks.
2. The tumour covers itself in PD-L1.
3. PD-L1 presses PD-1.
4. The T cell becomes **exhausted** — it stops multiplying, stops releasing killing signals, stops
   killing.
5. The tumour survives.

The project's image for this is exact: *the tumour has essentially shown the immune system a forged
ID card.* Because the PD-L1 is produced in reaction to inflammation rather than being a constitutive
trait of the tumour, this is called **adaptive immune resistance**
(`docs/sessions/2026-09-14-antibody-hackathon-spec-and-scoring.md:47-56`).

### 1.2 Checkpoint blockade

A **checkpoint** is one of these natural brakes. **Checkpoint blockade** means using a drug to
physically get in the way of the brake being applied. In the project's words: *"If you make a
molecule that sticks to PD-1 and covers the exact patch where PD-L1 would attach, PD-L1 can no
longer reach it. The brake is never applied"* (`:55-64`).

The framing that matters, and that beginners consistently get wrong: **the drug does not attack the
tumour; it attacks the tumour's defence.** All the killing is done by the patient's own immune
system. This is why responses to checkpoint inhibitors can be durable in a way that cytotoxic
chemotherapy responses are not — you are not depleting a drug, you are restoring a capability.

Mechanistically the drug is a **competitive inhibitor**: it binds a surface of PD-1 that overlaps
the PD-L1 binding site, so the two cannot both be there
(`docs/sessions/2026-09-14-...:62-63`). Note the word *overlaps*. We will quantify it in §5, and the
degree of overlap turns out to be surprisingly modest.

### 1.3 Why the target is validated

**Pembrolizumab** (trade name Keytruda) is a licensed anti-PD-1 antibody. Two numbers carry the
argument (`knowledge/PD-1 and Checkpoint Blockade.md:66-78`):

- **Kd ≈ 29 pM.** Kd is the *dissociation constant*: the concentration of free drug at which half
  the target molecules are occupied. Lower means tighter. To calibrate: a weak protein–protein
  interaction might be micromolar (µM), which is a *millionfold* looser than 29 picomolar.
- **Over $25 billion a year in sales.** It is one of the most commercially and clinically successful
  drugs ever made.

Format matters too. Pembrolizumab is a **humanised IgG4κ** antibody, made by **CDR grafting** —
mouse binding loops transplanted onto a human framework, then the framework optimised
(`docs/sessions/2026-09-14-...:61-63, 99-102`). That classical humanisation route is precisely what
the de novo challenge is asking us to replace. The IgG4 isotype is chosen because IgG4 is poor at
Fc effector functions: you do not want to kill the T cells you are trying to unleash. (The project
works only on Fv and Fab fragments and never discusses isotype, so this is context rather than
finding.)

A second approved anti-PD-1 antibody, **nivolumab** (PDB entry 5WT9), is used throughout as an
independent real solution to the same problem — a second right answer, which is useful precisely
because it is different from the first.

---

## 2. Antibody architecture from zero

An antibody is a **Y-shaped protein** built from four polypeptide chains: two identical **heavy
chains** (~50 kDa each) and two identical **light chains** (~25 kDa each). The two tips of the Y
grab the target; the stem is what the rest of the immune system reads. Because the two arms are
identical, an antibody has two identical binding sites — it is *bivalent*.

Chains are made of **domains**: semi-independent folded units. The domain at the very tip of each
arm is the **variable domain** (**VH** on the heavy chain, **VL** on the light) and it differs
enormously between antibodies. Everything behind it is **constant** (CH1, CL, and so on) and nearly
identical within an antibody class.

### 2.1 Fv, Fab, IgG

| Term | Contents | Size as used here |
|---|---|---|
| **Fv** (fragment variable) | VH + VL only — the minimal binding unit | ~230 residues (this project: 119 + 111) |
| **Fab** (fragment antigen-binding) | VH + CH1 + VL + CL — one whole arm | ~436 residues (this project: 219 + 217) |
| full IgG | two Fabs plus the Fc stem | never folded in this project |

(`knowledge/Antibody Architecture.md:46-49`; chain lengths from `data/fold_inputs/manifest.json`:
Fab = 219 + 217 + 113 = 549 residues with antigen; Fv = 119 + 111 + 113 = 343.)

The trade-off is stated precisely in the project: structure-prediction cost grows faster than
linearly with size, so folding an Fv is much cheaper — but the constant domains physically **clamp
the VH/VL elbow angle**, so a bare Fv has an under-constrained wobble that a Fab does not. This is
not a theoretical worry: in the project's very first prediction, the VH/VL interface was the
*worst*-scoring part of the model (`:57-58`), and the wobble later showed up as raw measurement
noise — see [the Fv-versus-Fab reliability measurement](04-measurement-theory.md) , where
Fv [ipSAE](03-the-toolchain.md#43-ipsae-interface-confidence-from-the-pae)
seed [reliability](04-measurement-theory.md#13-reliability) is 0.607 against the Fab's 0.965.

### 2.2 The six CDR loops

Contact with the target is made by six short, floppy loops called the **CDRs**
(*Complementarity-Determining Regions*): H1, H2, H3 on the heavy chain, L1, L2, L3 on the light.
Two more terms you cannot do without:

- the **paratope** is the antibody surface that touches the target;
- the **epitope** is the target surface that gets touched.

Everything in the variable domain that is not CDR is **framework** — scaffolding that holds the
loops in the right relative positions. In design work the framework is usually held fixed and only
the CDRs are changed (`knowledge/Antibody Architecture.md:62-75`).

The six loops are not equal. The handbook's own per-loop table
(`docs/sessions/2026-09-14-...:78-88`) rates H1 and H2 "moderate" in variability, L1 moderate, L3
moderate with additional VH/VL interface duty, **L2 "limited direct contact" and low variability**,
and **H3 "very high" and the primary specificity determinant**.

### 2.3 Why CDR-H3 dominates — and the reason is genetic, not structural

Five of the six loops are encoded more or less directly in the germline: you inherit them. CDR-H3
is not. It is assembled by **V(D)J recombination** — three gene segments (V, D, J) are cut out of
the genome and spliced together, with random nucleotide addition and deletion at *both* junctions.
That junctional diversity produces enormous variation in **both sequence and length**, far more
than the somatic hypermutation that diversifies the other five loops.

The consequences are recorded at `knowledge/Antibody Architecture.md:79-92`: CDR-H3 contributes
**30–50% of the paratope surface**, is the primary determinant of what the antibody recognises, and
is the hardest loop both to design and to predict.

Measured on two approved drugs (`:96-99`):

- pembrolizumab CDR-H3 = `ARRDYRFDMGFDY`, **13 residues**
- nivolumab CDR-H3 = `ATNDDY`, **6 residues**

Both bind PD-1; both work in patients. The reading the project takes from this is genuinely
encouraging for de novo design: **PD-1 can be bound by radically different loop architectures**, so
there is not one narrow correct answer to find.

(For completeness, pembrolizumab's light-chain CDRs as measured by [ANARCII](03-the-toolchain.md#45-anarcii-208-imgt-numbering-and-the-antigen-it-numbered-as-an-antibody) on both 5GGS copies:
CDR-L1 `KGVSTSGYSY`, CDR-L2 `LAS`, CDR-L3 `QHSRDLPLT` — `docs/sessions/2026-09-15-...:133`.)

The genetic story also explains why structure prediction struggles here, which becomes central in
§7: modern folding models learn contacts partly from **co-evolution** across homologous sequences,
and a loop generated by random splicing has no homologues to co-evolve with.

### 2.4 Numbering schemes, and why the novelty gate depends on one

If two antibodies have different CDR-H3 lengths, "residue 100" in one is not the structural
equivalent of "residue 100" in the other. Raw sequential position is meaningless across antibodies.
A **numbering scheme** fixes this by assigning canonical positions, inserting gaps and insertion
codes so that structurally equivalent positions get the same number in every antibody
(`knowledge/Antibody Architecture.md:105-115`).

The competition specifies **IMGT**, in which `CDR1 = 27–38`, `CDR2 = 56–65`, `CDR3 = 105–117`, with
the conserved cysteine at 104 (`config/metrics.yaml` `numbering_scheme: imgt`;
`src/locksmith/numbering.py:4-6`).

**This is part of the metric definition, not an implementation detail.** A different scheme (Kabat,
Chothia) extracts a different substring from the same chain and therefore computes a different
identity against the same reference. The project hit this concretely: an early estimate put
pembrolizumab's CDR-H3 at **11** residues, `RDYRFDMGFDY` — that is the **Kabat** boundary. IMGT
includes the preceding `AR`, making it **13**.

Why it matters is arithmetic. Length is the *denominator* of percent identity. With 13 residues,
identity moves in exact steps of 1/13 ≈ 7.7%:

- one substitution → 92.3% identity, which clears the `<95%` hard cutoff;
- four substitutions → 69.2%, which clears the `<70%` Good-band edge.

With 11 residues the steps are 1/11 ≈ 9.1% and the thresholds fall in different places. A scheme
choice made in a config file therefore decides whether a given design passes a gate. This is the
first instance of a theme that runs through
[the engineering chapter](02-the-engineering-problem.md) : conventions the specification
leaves open
are load-bearing, and the honest response is to name them, not to pick one silently.

### 2.5 The IgV fold, and the trap it set

PD-1 belongs to the **immunoglobulin superfamily** and has an **IgV fold** — the same β-sandwich
architecture as an antibody variable domain, by shared evolutionary ancestry. The practical
consequence is startling: **ANARCII, the antibody-numbering tool, confidently numbered PD-1 as an
antibody chain and assigned it CDRs** (`knowledge/Antibody Architecture.md:149-160`).

That is not a bug. A tool trained to recognise V domains recognises PD-1 because, by fold, PD-1 *is*
one. The separation is available but only if you look: real antibody domains scored 30.8–30.9 on
ANARCII's confidence measure and PD-1 scored 15.8–16.2, so `src/locksmith/numbering.py:51-57` sets
`MIN_V_DOMAIN_SCORE = 25.0` and documents it as "load-bearing, not cosmetic". Without that
threshold, the antigen is silently classified as an antibody chain and every downstream CDR metric
is computed on the wrong molecule.

The biological reading matters beyond the tooling, and the project drew it: if PD-1's binding face
is an IgV face, then the surfaces a designed paratope might *accidentally* recognise are other IgV
domains. That is exactly why the specificity panel (§6.4) includes an Ig V-set decoy — and exactly
which decoy failed.

---

## 3. The epitope: which 26 residues

This is the single most load-bearing biological number the project generated.

### 3.1 The PD-L1 footprint on PD-1

Measured by `src/locksmith/design/epitope.py` in PDB entry **5IUS** (PD-1 bound to PD-L1), at a
**5 Å heavy-atom** criterion, chain A against chains C/D, **PD-L1's footprint on PD-1 is 26
residues** (`results/epitope.md:11-13`):

```
H64 V66 H68 E70 S73 G74 Q75 T76 D77 T78 L79 A80 A81 D85 P89 G90 Q91
C123 G124 I126 L128 I132 I134 K135 E136 R139
```

These fall into two spatial clusters — roughly 64–91 (the C'D loop region) and 123–139 — which is
"consistent with PD-L1 engaging one face of the PD-1 IgV β-sandwich" (`:15-16`).

### 3.2 Pembrolizumab's own epitope, and the 58% figure

Measured the same way in **5GGS** (pembrolizumab Fab bound to PD-1), **pembrolizumab's epitope on
PD-1 is 27 residues** (`results/epitope.md:36-38`):

```
S60 S62 F63 V64 N66 Y68 Q75 T76 D77 K78 A81 F82 P83 E84 D85 R86 S87 Q88 P89 G90
I126 L128 A129 K131 A132 Q133 I134
```

**Overlap: 15 shared residues.** Therefore:

- **15/26 = 57.7%, i.e. ~58% of the PD-L1 site is covered by pembrolizumab**;
- **15/27 = 56% of pembrolizumab's own epitope lies on the PD-L1 site** (`:40-45`).

Why bother computing this? Because it converts a near-meaningless binary question — *does the
design overlap the PD-L1 site?*, which a single shared residue would pass — into a calibrated one:
*does the design achieve PD-L1-site coverage comparable to a drug that works in patients?*, target
~58% (`results/epitope.md:51-58`).

It also teaches something about the mechanism. Pembrolizumab does **not** bury the whole PD-L1
site. It parks over a little more than half of it, and roughly half of its own contacts sit on
adjacent surface that PD-L1 never touches. **Competitive blockade does not require complete
occlusion.** That is not obvious a priori and it changes what a designer should aim for.

### 3.3 The alignment that made the mapping non-trivial

5IUS and 5GGS **do not carry the same PD-1 sequence**. Aligned identity is **90.1% over 111
residues** — roughly eleven differences (`results/epitope.md:18-29`). Residue numbers are therefore
*not* transferable between the two entries. The 26-residue footprint measured in 5IUS was carried
across to 5GGS numbering by **explicit pairwise sequence alignment**, and all 26 residues transfer
cleanly.

Assuming transferability would have produced a wrong epitope with no error raised anywhere — one of
the project's catalogued "[silent failures](08-what-broke.md#class-1-silent-failures)". It also carries a caveat the project states rather than
buries: if 5IUS uses an engineered or stabilised PD-1 variant, its PD-L1 binding mode may differ
subtly from wild type.

The four reference structures used throughout are 5GGS (pembrolizumab + PD-1, the answer key),
5DK3 (pembrolizumab alone), 5IUS (PD-1 + PD-L1, which defines the site to block) and 5WT9
(nivolumab + PD-1).

### 3.4 A six-residue hole nobody noticed for nine days

Every fold in the project used a **113-residue PD-1 construct beginning `PWNPP`**, inherited from
the 5GGS entry and never re-examined (`results/negative_control.md:83-92`).

Measured against each reference antibody's own crystal at a 4.5 Å criterion, pembrolizumab's
epitope is 24 residues and nivolumab's is 14. (The 24-versus-27 discrepancy for pembrolizumab is
the distance cutoff — 4.5 Å here versus 5 Å in §3.1 — not a contradiction.) Of those:

- pembrolizumab: **24/24 (100%)** inside the folded construct;
- nivolumab: **8/14 (57.1%)** — the construct is missing `LDSPDR`, PD-1 residues **25–30**.

So when nivolumab, a licensed anti-PD-1 antibody, failed the pipeline's own positive control at
ipSAE 0.017, the reason was not that the pipeline was broken. **The molecule it was docked against
does not contain the surface it binds.** The truncation was invisible for the entire project
because *the only reference antibody ever folded was the one incapable of detecting it.*

Worse, and explicitly flagged: **the construct folded is not the construct submitted.** The shipped
FASTA antigen begins `DSPDRPWNPP…` — a 123-residue construct covering 92.9% of nivolumab's epitope.
"Every number in this submission was measured on a molecule 6 residues shorter than the one shipped
beside it."

The transferable principle: *a positive control chosen because it is convenient tests the thing it
shares with your pipeline, not the thing it differs on.* See
[the full failure catalogue](08-what-broke.md).

### 3.5 Does either design actually block PD-L1?

The rubric never asks. The project added the check anyway (`results/pdl1_competition.md`):
superpose each design's PD-1 onto 5IUS, carry the Fv with it, and measure overlap with PD-L1. A
**clash** is a heavy-atom distance below 3.0 Å — under the van der Waals sum, so the two atoms
cannot coexist; a **contact** is 4.5 Å. In 5IUS, PD-L1 contributes 18 interface residues and PD-1
contributes 23.

| | Cα RMSD over 106 PD-1 residues | Fv↔PD-L1 clashes <3 Å | PD-L1 footprint occluded |
|---|---|---|---|
| Challenge 1 | 1.80 Å | **2007** | **16/18 (89%)** |
| Challenge 2 | 1.79 Å | **4522** | **17/18 (94%)** |

Both designs are geometrically incompatible with PD-L1 binding: both would be checkpoint inhibitors
*if the predicted pose is right*. The project states the conditional plainly: *"It is a conditional
statement — if it binds as predicted, then it blocks — and the antecedent is exactly what this
project has spent a week failing to establish"* (`:19`). Two approximations travel with it: PD-1's
own in-vivo glycosylation (N49/N58/N74/N116) is modelled bare, and the analysis is rigid-body,
ignoring conformational change on binding.

---

## 4. What "designing an antibody" must achieve

The organisers' framing sentence, quoted throughout the project, is: *"Can we computationally design
antibodies that don't just bind, but that look like real drugs?"* (`README.md:6-7`).

The reason is attrition. A traditional antibody programme takes **18–36 months** from target to
clinical candidate with **>90% attrition** — and, as the project's notes put it, *"the attrition is
not mostly a binding problem — plenty of molecules bind. It is a developability problem: the
molecule aggregates, it is immunogenic, it cannot be manufactured at 1 g/L, it deamidates on the
shelf"* (`docs/sessions/2026-09-14-...:41-45`). Hence a rubric in which **40% of the score is
non-binding**: binding 0.60, developability 0.20, novelty 0.20.

Six requirements, and what the project could and could not measure against each:

1. **Affinity** — bind tightly. Proxied by [PRODIGY](03-the-toolchain.md#42-prodigy-240-δg-and-contacts) ΔG and, indirectly, by ipSAE and heavy-atom
   contact counts. §7 shows how badly these proxies track measured affinity.
2. **Specificity** — bind *only* PD-1. Not in the rubric at all. The project added a five-antigen
   panel (§6.4) and failed it.
3. **Functional mechanism** — occlude the PD-L1 site. Also not in the rubric. Added as §3.5.
4. **Developability** — solubility and aggregation propensity ([NetSolP](03-the-toolchain.md#44-netsolp-10-sequence-only-solubility-and-a-positive-control-that-chose-the-model)), no N-glycosylation sequons
   in the Fv, no NG/DG deamidation–isomerisation motifs in CDRs, no exposed Met/Trp in CDRs, sane pI
   and net charge (`src/locksmith/metrics/liabilities.py:34-48`).
5. **Manufacturability** — NetSolP is the only proxy, and it is trained for solubility **in
   *E. coli*** while therapeutic antibodies are made in mammalian cells. The project states the
   domain mismatch rather than pretending it away (`knowledge/The Eight Metrics.md:180-184`).
   Solubility problems account for roughly 30% of candidate failures in manufacturing development.
6. **Immunogenicity** — addressed only by construction. Both designs sit on human or humanised
   frameworks: Challenge 1 keeps pembrolizumab's humanised framework; Challenge 2's framework is the
   humanised **4D5-8 (trastuzumab) Fv**, with **VH framework 86/86 identical and VL framework 80/80
   identical** to trastuzumab. The project warns explicitly that this makes "humanness and framework
   metrics look excellent: they are a marketed antibody's."

What is covered *nowhere*: thermostability (Tm), viscosity at high concentration, FcRn-mediated
serum half-life, off-target tissue cross-reactivity in a real assay, and proper immunogenicity
prediction by MHC-II epitope scanning. These are the next tier of real developability, and stating
their absence is part of the honest account.

---

## 5. The two challenges as biological problems

| | **Challenge 1 — "Remix Keytruda"** | **Challenge 2 — "Invent the Future"** |
|---|---|---|
| Start from | 5GGS: pembrolizumab Fab bound to PD-1 | nothing |
| Task | redesign the three heavy-chain CDRs, keep it binding | design a complete VH/VL against PD-1 |
| Problem class | fixed-backbone redesign | de novo design |
| External safety net | **DockQ** against the real crystal pose | **none** |
| Organisers' difficulty rating | ★★★☆☆ | ★★★★★ |

Two definitions, both from `knowledge/De Novo Design and the Two Challenges.md:21-42`. A
**backbone** is the chain of atoms running through the protein — its path through space, ignoring
side chains. **Fixed-backbone redesign** keeps that path exactly and changes which amino acids sit
along it: *"re-upholstering the furniture, not moving it."* It is easier than it sounds, because the
hard part — deciding the three-dimensional shape — was already solved by whoever crystallised the
structure. **De novo** design means proposing both backbone and sequence with no template: *"You are
no longer editing a known good answer; you are proposing one."*

### 5.1 The tension inside Challenge 1

Challenge 1 hands you the answer to the hardest question: what shape the antibody should be, how it
should be oriented against PD-1, which patch of PD-1 to touch. But the scoring builds in a real
conflict. **Novelty** wants CDR-H3 rewritten as much as possible (top marks below 70% identity)
while **[DockQ](03-the-toolchain.md#41-dockq-213-two-flags-that-both-default-wrong)** wants the pose unchanged (top marks at ≥0.80) — and CDR-H3 supplies 30–50% of the
contact surface. *"So you are being asked to rewrite the most important part of the interface while
leaving the interface intact. That tension is Challenge 1"* (`:64-73`).

Concretely, the redesign target is the **29 IMGT heavy-chain CDR positions of pembrolizumab**
(H1 = 8, H2 = 8, H3 = 13), sampled across four [ProteinMPNN](03-the-toolchain.md#21-proteinmpnn) temperatures to give 239 designs; the
light chain is pembrolizumab's, untouched, in all 239.

One temptation was explicitly declined (`:126-136`). Because Challenge 1 is fixed-backbone redesign
of a structure you already have, you could submit the **crystal coordinates** with a new sequence
label and score a near-perfect DockQ by construction. The project refused: the submitted confidence
matrix would not correspond to those coordinates, and "those coordinates are a *measurement of
someone else's molecule*, not a prediction of ours."

### 5.2 Why de novo is fundamentally harder

Four independent reasons, all documented:

1. **No reference means no external check.** Challenge 2 is scored on seven metrics, not eight —
   DockQ is excluded because there is nothing to compare against. The shipped scores file states the
   consequence flatly: *"DockQ was the only metric that compares the prediction to anything
   external… A confidently wrong pose scores exactly like a right one."*
2. **Antibody–antigen prediction is the documented weak spot of folding models, and the reason is
   the same genetics that makes CDR-H3 powerful.** MSA-based predictors learn contacts from
   correlated mutation across homologous sequences; a junctionally randomised loop has no
   homologues, so *"there is no evolutionary family of related sequences for the model to learn
   from"* (`knowledge/De Novo Design...:89-93`).
3. **Measured, not assumed.** Five complexes released clear of [Boltz-2](03-the-toolchain.md#31-boltz-2-the-primary-predictor)'s verified **2023-06-01**
   PDB-*release*-date cutoff, each with CDR-H3 ≤44.4% identical to anything pre-cutoff, gave a
   **median Fab DockQ of 0.157** against 5GGS's 0.818. That result was **partly withdrawn** when an
   input bug was found (antigen sequences built from coordinates had internal loops spliced out);
   the corrected median is **0.291** and the verdict moved FAIL → MARGINAL. Even corrected, the most
   deployment-relevant row is **9W43, a post-cutoff human PD-1 complex, Fab DockQ 0.157** — the
   predictor fails on a novel antibody against this very antigen. See
   [how the post-cutoff panel was constructed and screened](05-experiment-design.md).
4. **Confidence is not correctness, and selection is optimisation.** Six of the eight metrics are
   computed from files the team generates itself, so "a confidently wrong answer scores well"; and
   generating thousands of candidates and picking the best-scoring one *is* a hill-climb executed in
   one parallel step — the **[winner's curse](06-allocation-and-selection.md#3-winners-curse)** — so "the score we report for our chosen design is
   systematically optimistic, and the harder we screen, the worse it gets"
   (`knowledge/Confidence Is Not Truth.md:17-31, 57-70`). Quantified in
   [the selection chapter](06-allocation-and-selection.md).

### 5.3 What "de novo" honestly means here

`submission/.../Challenge2/docs/methods_and_limitations.md:107-119` says it outright: **"The
framework is not ours and is not designed."** All six CDRs of both chains were designed de novo onto
the humanised 4D5-8 (trastuzumab) Fv; the frameworks were carried over unchanged. "Using a fixed
humanised framework is standard practice and is what 'de novo antibody design' operationally means
with current tooling — the novelty lives in the CDRs and the pose."

For Challenge 2 the generative backbone model ([RFdiffusion](03-the-toolchain.md#22-rfdiffusion-via-rfantibody), via RFantibody) was **conditioned on the
26-residue PD-L1 competitive footprint**: you tell the model which residues on the target to aim at,
and it proposes loops that reach them. Biologically, this is how you convert "bind PD-1" into "bind
the functionally relevant face of PD-1" — the difference between a checkpoint inhibitor and an inert
binder. The statistics of whether the conditioning worked, including a claim that was superseded by
a better null, are in [the experiment-design chapter](05-experiment-design.md) ; the
headline is that
against 2000 random *contiguous* 26-residue surface patches on the same chain, the real epitope
scored 0.712 interface fraction against the null's 0.154, with 17 of 18 backbones beating their own
null at p<0.05.

---

## 6. The biological findings, with the chemistry

### 6.1 Two N-glycosylation sequons in the Challenge 2 paratope

The Challenge 2 design that cleared the gates carried **two N-linked glycosylation sequons in its
CDRs, both on antigen-contacting residues**: `N52-V53-S54` in CDR-H2 and `N49-A50-S51` in CDR-L2.
**Neither exists in the parent scaffold; ProteinMPNN introduced both.** Handbook §9.2 states plainly
*"No N-glycosylation sequons (N-X-S/T) in Fv region."* The design shipped with them, and they were
found by an **independent reviewer**, not by the pipeline — the scanner that should have caught them
was specified at `BUILD.md:62` and was never written until the penultimate day. Its docstring now
records the lesson: *"A planned check that does not exist is indistinguishable from a check that
passed."*

**The chemistry.** N-linked glycosylation happens co-translationally in the endoplasmic reticulum.
The enzyme oligosaccharyltransferase (OST) transfers a large pre-assembled sugar (Glc₃Man₉GlcNAc₂)
from a lipid donor onto the side-chain amide nitrogen of an asparagine. The recognition motif is
**Asn-Xaa-Ser/Thr where Xaa ≠ Pro**. The mechanism requires the hydroxyl of the Ser or Thr at
position n+2 to hydrogen-bond the Asn amide and twist it into an activated conformation — the
"Asn-turn" / amide-activation model — which raises the nucleophilicity of the amide nitrogen.
Proline at n+1 rigidifies the backbone and prevents that geometry. This is exactly why the project's
regex is `N[^P][ST]`, and the code says so: *"proline at position 2 blocks the oligosaccharyl
transferase, so NPS/NPT are not sequons. This is the single most common way a naive regex
over-reports"* (`src/locksmith/metrics/liabilities.py:39-41`). Thr sequons are typically occupied
more efficiently than Ser sequons.

**Why a sequon in a paratope is disqualifying.** A glycan is enormous compared with a side chain: a
bi-antennary complex N-glycan is about 2 kDa and extends 20–30 Å. Placed on a contact-making CDR
residue it will sterically abolish or drastically alter binding — and because occupancy is partial
and glycoforms are heterogeneous, you get a *mixture* of molecules with different affinities. That
is a manufacturing (CMC) nightmare as much as a potency one.

### 6.2 The NG deamidation motif in Challenge 1's CDR-H2

The same new scanner found that Challenge 1 also failed §9.2: an **`NG` deamidation motif at heavy
55–56, inside CDR-H2**. It is **pembrolizumab's own motif** — not introduced by the redesign — but
**both positions were inside the 29 IMGT positions made designable**, "so leaving it was a choice we
did not know we were making." The redesign had changed CDR-H2 at exactly one position (S54L) and
left `N55-G56` intact.

**The chemistry.** The backbone amide nitrogen of residue n+1 attacks the side-chain carbonyl carbon
of the Asn, expelling ammonia and forming a five-membered **succinimide** (cyclic imide)
intermediate. That ring then hydrolyses at either carbonyl, giving **iso-aspartate (~3:1) or
aspartate (~1:3)**. So the product is a charge change (neutral amide → negative carboxylate) plus,
in the isoAsp case, a *backbone-length* change that inserts an extra methylene into the main chain.
In a CDR both outcomes are structurally destructive. The rate is dominated by the n+1 residue's
steric bulk, because the attacking nitrogen has to reach the carbonyl: **glycine, having no side
chain, is roughly an order of magnitude faster than anything else.** That is precisely the project's
severity table, `DEAMIDATION = {"NG": "high", "NS": "moderate", "NT": "moderate", "NN": "low",
"NH": "low"}` (`liabilities.py:43`). The parallel Asp motifs — `DG` high, `DP` an acid-cleavage site
— are **isomerisation** through the same succinimide, minus the ammonia loss.

### 6.3 N→Q versus S→A: the contact-count result

This is the project's own nomination for its best result, and it is a lesson about handbooks.

Handbook §9 Pillar 4 prescribes both fixes on one line — *"N-glycosylation: N-X-S/T (X≠P) in Fv →
N→Q or S→A mutations"* — and presents them as interchangeable. Both remove both sequons. **They are
not remotely equivalent.**

The outcome was **predicted before any folding**, from heavy-atom contacts to PD-1 measured on the
submitted structure:

| residue | contacts to PD-1 |
|---|---|
| heavy **N52** | **10** |
| heavy S54 | **0** |
| light **N49** | **19** |
| light S51 | **0** |

*The glycosylation acceptors are the binding residues.* N52 and N49 carry 29 antigen contacts
between them; the serines that complete the motifs carry none.

Then the measurement, over five diffusion samples each (`results/sequon_fix_2026-09-22.md`,
pre-registered before the folds):

| variant | mutations | sequons left | §9.2 | ipSAE over 5 samples | composite | viable |
|---|---|---|---|---|---|---|
| baseline | — | 2 | FAIL | 0.736 – **0.864** | 96.0 | 5/5 |
| **S→A** | H S54A + L S51A | **0** | PASS | 0.619 – **0.781** | **91.2** | **5/5** |
| **N→Q** | H N52Q + L N49Q | 0 | PASS | **0.013 – 0.014** | 81.6–87.6 | **0/5** |

Two of the most conservative substitutions in all of protein engineering — Asn→Gln, one methylene
longer, same amide chemistry — take ipSAE from **0.864 to 0.014**, a sixty-fold collapse
**reproducible to ±0.001** across five independent diffusion samples.

**Why Asn→Gln looks conservative on paper and is not here.** Gln is Asn plus one CH₂: same primary
amide head group, same hydrogen-bond donor/acceptor pattern, same neutrality, similar
hydrophilicity. Substitution matrices score N↔Q favourably and the pair really is interchangeable at
most surface positions. What the extra methylene changes is **geometry**: the amide is displaced
about 1.5 Å further from the backbone and gains a rotatable bond, so a hydrogen-bond network tuned
to a particular Asn χ₁/χ₂ geometry cannot simply be remade at the new distance. At a buried,
contact-dense interface position, that is the difference between a satisfied network and a
desolvated, unsatisfied polar group — which is strongly destabilising. Gln also cannot form the
Asx-turn motifs Asn makes.

**Confirmed in the opposite direction, the same day.** Challenge 1's `NG` motif has acceptor **N55
making only 3 antigen contacts** (and G56 making 0), and there `N55Q` was **free**: composite held
at 96.0, ipSAE moved 0.822 → 0.821, and the five-sample envelope was 0.044 against the baseline's
0.039.

| | mutated residue's antigen contacts | result |
|---|---|---|
| Challenge 2 `N→Q` | **10 and 19** | ipSAE 0.864 → **0.014**, dead |
| Challenge 1 `N55Q` | **3** | 0.822 → 0.821, unchanged |

**So `N→Q` is not inherently dangerous and `S→A` is not inherently safe. What predicts the outcome
is how much of the interface the mutated residue is carrying — and that is a one-minute calculation
on a structure you already have.** *"Conservative substitution" is a claim about chemistry in the
abstract, not about a particular interface.* That is the transferable principle, and it generalises
well beyond antibodies: any prescribed fix that touches a functional site is a design change and
must be adjudicated against the function, not against the prescription's word order.

Two honest footnotes. The alternative Challenge 1 fix `G56A` was rejected on three grounds:
composite 94.0, a wider envelope (0.089 against 0.044), and chemistry — deamidation happens *at* the
asparagine, and glycine at n+1 merely makes it fast, so removing the Asn eliminates the liability
while removing the Gly only slows it. (Glycine also has no Cβ and can access positive-φ Ramachandran
space, so CDR glycines are frequently doing conformational work at zero antigen contacts; the
doubled envelope is consistent with that.) And **the S→A fix was not free either, and the cost is
recorded as unexplained**: it touches zero interface contacts, yet the ipSAE envelope fell from
0.736–0.864 to 0.619–0.781. The best sample, 0.781, sits below the 0.80 Good edge, so the composite
drops 96.0 → 91.2; the worst, 0.619, sits only **0.019** above the viability cutoff of 0.60, against
the baseline's 0.136 of headroom. The plausible story is that Ser54 and Ser51 were doing
conformational work on the loops. In the project's words: *"We did not test that and we are not
asserting it."*

The decision that followed is the clearest statement of the project's values: **the S→A design at
91.2 was submitted in place of the unfixed 96.0** — "4.8 rubric points to remove a liability the
rubric does not measure. §9.2 asks for it; §5.2 does not pay for it."

### 6.4 TIM-3 cross-reactivity — a specificity failure

The named Challenge 1 design `mpnn_T0.5_s104_036`, unchanged, was folded against five antigens at
three fresh seeds each, **pre-registered before any fold ran** (`results/specificity.md`):

| antigen | role | length | ipSAE | ΔG (kcal/mol) | contacts | interface pLDDT |
|---|---|---|---|---|---|---|
| PD-1 | positive control | 113 | **0.847 ± 0.013** | −12.5 ± 0.1 | 94 ± 4 | 90.1 ± 0.4 |
| PD-L1 IgV | functional decoy | 113 | 0.000 ± 0.000 | −11.6 ± 1.5 | 74 ± 7 | 81.4 ± 2.1 |
| **TIM-3** | **Ig V-set decoy** | 110 | **0.568 ± 0.086** | **−14.1 ± 0.3** | 97 ± 8 | 85.6 ± 0.3 |
| ULBP6 | MHC-I-like decoy | 172 | 0.007 ± 0.007 | −11.8 ± 1.2 | 72 ± 12 | 81.6 ± 2.0 |
| PcrV | bacterial decoy | 134 | 0.421 ± 0.305 | −9.2 ± 0.1 | 47 ± 4 | 80.2 ± 0.5 |

The **pre-declared failure condition triggered on TIM-3**: ipSAE ≥ 0.60 *and* ΔG ≤ −10 on at least
2 of 3 seeds (0.624, 0.612, 0.469 → 2/3). Note that the arm *mean* would have passed; the rule was
written per-seed before the data existed and was applied as written.

A reference control was then added — exploratory, and labelled as such rather than folded into the
pre-registered result: antigen fixed at TIM-3, antibody varied. Our design scored **0.513** (n=8
seeds) against **pembrolizumab 0.331** (n=8) and a real TIM-3 binder, **8TBB Fab, 0.682** (n=3).
Difference (ours − pembrolizumab) **+0.182**, bootstrap 95% CI **[+0.045, +0.320]**, Mann–Whitney
**p = 0.038**. The reading: the design is TIM-3-reactive *relative to a specific antibody*.

**Why TIM-3 specifically is the dangerous decoy.** TIM-3 (gene *HAVCR2*) is another human inhibitory
checkpoint receptor on T cells, and its ectodomain is an **Ig V-set domain** — the same β-sandwich
fold family as PD-1 (§2.5). An antibody that has learned a generic IgV-face-binding mode rather than
a PD-1-specific one will cross-react. Clinically this would be serious: TIM-3 is expressed on
exhausted T cells, regulatory T cells and myeloid cells, so off-target engagement changes both the
pharmacology and the toxicity profile.

The epistemic limit the project attaches is worth memorising: *"A decoy scoring high is strong
evidence of a problem; a decoy scoring low is **weak** evidence of its absence, because a predictor
that is unreliable at novel placement scores novel pairings low whether or not they would bind."*
The supported sentence is *no evidence of gross promiscuity, from a test that could only have
detected gross promiscuity* — not *the design is specific*.

### 6.5 CDR-H3 net charge +2, and the aromatic deficit

The shipped Challenge 1 CDR-H3 is `ALRPRDVDRGFYK` against pembrolizumab's `ARRDYRFDMGFDY`, with 8 of
13 positions changed. Two sequence-level observations, both computable for free before any structure
existed (`submission/.../Challenge1/docs/methods_and_limitations.md:97-110`):

- **Net charge +2** (four basic: R, R, R, K; two acidic: D, D) where **pembrolizumab's CDR-H3 is 0**
  (three basic, three acidic). High positive charge in the CDRs is one of the better-established
  sequence predictors of polyreactivity and fast clearance.
- **Aromatic content 2** (F, Y) against **pembrolizumab's 4** (Y, F, F, Y). Tyr/Trp enrichment is
  among the most robust compositional features of natural paratopes.

**Why positive CDR charge predicts polyreactivity.** Most of the cell-surface and serum
macromolecules a therapeutic antibody meets — heparan sulfate proteoglycans, DNA, phospholipid head
groups, sialylated glycans — are polyanionic. A cationic paratope engages them non-specifically
through long-range electrostatics before any shape complementarity is required, which is most of
what "polyreactivity" is. The downstream consequences are a high polyspecificity-reagent signal,
elevated non-specific tissue uptake, and faster clearance with shorter serum half-life.

**Why Tyr/Trp dominate real paratopes.** Tyrosine and tryptophan are unusually good at antigen
recognition per residue: they are large, so one side chain covers a lot of interface area; they are
rigid aromatics, so ordering them costs little conformational entropy; their flat faces make
stacking, cation-π and CH-π interactions; and Tyr's hydroxyl plus Trp's indole NH add
hydrogen-bonding on top of the hydrophobic surface. This combination of promiscuous binding
capability with modest entropic cost is why synthetic libraries built almost entirely from Tyr and
Ser still yield high-affinity binders. Losing two of four aromatics from a 13-residue CDR-H3 is a
real interface-chemistry change, not a cosmetic one.

The honesty clause attached to the charge observation is exemplary and should be read as part of the
finding: *"we did not connect the two until after the design was chosen, and we do not claim the
charge causes the cross-reactivity — it is one observation and one prediction, not a demonstrated
mechanism. It is stated here because it was computable from the sequence for free, before any
structure existed, and nothing in the rubric would have surfaced it."*

And the project's own filter that would have *justified* fewer aromatics was **refuted**. The "G3"
filter kept designs with ≤1 aromatic per 13-residue CDR-H3 and beat 10,000 [equal-budget](05-experiment-design.md#6-equal-budget-resampling-and-varying-the-outcome) random
subsets at p<0.0001 on mean DockQ. Re-run with each of the six scored metrics as the outcome
(n=239, 10,000 resamples) it wins on **2 of 6**: `dockq` (+0.0237, p=0.0001) and `iface_plddt`
(+1.12, p=0.0001) — *both properties of the predictor rather than of the interface* — while `dg` is
p=0.064, `cdr_sasa` p=0.547, and **`contacts` runs the wrong way**, filtered designs making **1.80
fewer** heavy-atom contacts (one-sided p for "more contacts" 0.988), which is exactly what the
chemistry predicts when you select against large aromatics. The statistics were never wrong; the
outcome variable was. That analysis lives in [the critique chapter](09-critique.md).

### 6.6 ProteinMPNN's systematic developability problem

A pattern, stated twice in the project. Unconstrained ProteinMPNN put two glycosylation sequons into
the Challenge 2 paratope; and when 24 ProteinMPNN light chains were generated at T=0.1 for Challenge
1, **24 of 24 failed §9.2, each carrying 3–5 CDR liabilities**. The diagnosis:
*"ProteinMPNN optimises sequence recovery given a backbone, and solubility is simply not in its
loss."* Nor are glycosylation, deamidation, oxidation or charge. The model has no term for any
post-translational liability, so it proposes them at roughly the rate they occur in the Protein Data
Bank.

---

## 7. What the scores do and do NOT say about binding

The shipped numbers are: **Challenge 1** `mpnn_T0.5_s104_036` with the N55Q fix — CDR SASA 1596.5 Å²,
CDR-H3 identity 38.5%, 97 contacts, ΔG −13.3 kcal/mol, DockQ 0.800, interface pLDDT 88.63, ipSAE
0.821, NetSolP 0.569 → **96.0 / 100, viable**, with a five-diffusion-sample envelope of 94.0–96.0.
**Challenge 2** `bb_2_0_dldesign_1` with the S→A fix — CDR SASA 1066.5 Å², germline identity 30.0%,
97 contacts, ΔG −11.0, interface pLDDT 85.17, ipSAE 0.781, NetSolP 0.570 → **91.2 / 100, viable**,
envelope 91.2–96.0.

Here is why none of that is evidence of binding.

**First, most of the score is self-referential.** Six of the eight metrics are computed from files
the team generated; the organisers re-fold nothing. Challenge 2 loses the one external metric
entirely.

**Second — and this is the sharpest single result in the project — no metric tracks measured
affinity.** `results/skempi_validity.md` is the only experiment that compares a predicted number to
a laboratory measurement. Forty-five single mutants of **3HFM** (the HyHEL-10 Fab against hen
egg-white lysozyme) with experimental ΔΔG values from SKEMPI 2.0 were folded at one seed.
Correlations with measured ΔΔG:

| metric | correlation with experimental ΔΔG |
|---|---|
| PRODIGY ΔG | **+0.221** |
| ipSAE | **+0.059** |
| DockQ | **−0.101** |
| interface pLDDT | **+0.047** |
| contacts | **−0.246** |

Several have the *wrong sign*. At n=45 the smallest effect detectable at 80% power is ρ ≈ **0.41**,
so this null means "no monotone relationship stronger than that" — stated, as it should be, with its
detectable effect beside it. Crucially the metrics *are* moving: between-mutant standard deviation
is 19.5× the seed sd for ipSAE and 82.9× for interface pLDDT. They are simply not moving *with the
measured affinity*.

Most damning: of the five mutants that experimentally abolish binding, **four score essentially like
the wild type**. **`NL31A` has ΔΔG +21.8 kcal/mol — binding is gone — and scores ipSAE 0.917 against
the wild type's 0.903.** The pipeline rates a non-binder *above* the real complex.

**Third, an antibody against hen egg lysozyme cleared every hard cutoff as a PD-1 binder.** Six
irrelevant antibodies (trastuzumab, bevacizumab, cetuximab, CR9114, BO2C11, HyHEL-10) were docked
onto the identical 113-residue PD-1 construct with identical settings. On `model_0` — the model a
default `diffusion_samples=1` run returns — **HyHEL-10 cleared all five §7.2 hard cutoffs**: ipSAE
0.609, ΔG −12.4 kcal/mol, 77 contacts, interface pLDDT 85.0, CDR SASA 1084 Å². Its **median over
five samples is 0.219**, so it fails comfortably once you actually sample.

The mechanism is the argmax. Boltz orders its diffusion outputs by its own confidence, so `model_0`
is the *maximum* of five draws, and the maximum of five draws from a broad low distribution
routinely lands above a threshold the distribution's centre is nowhere near. **The gate is not
broken. Reading the gate off a single diffusion sample is.** (See
[`diffusion_samples` as a first-class parameter](03-the-toolchain.md).)

And the generalisation is worse than the single case. **Four of the five hard cutoffs — ΔG,
contacts, interface pLDDT, CDR SASA — reject 0 of 6 known-wrong antibodies.** They are inert.
Practically, the viability decision rests on **ipSAE alone**, and even there cetuximab's median
(0.594) sits 0.006 under the cutoff. The panel's own verdict is **INCONCLUSIVE**, because one of two
positive controls (nivolumab) failed — for the construct-truncation reason in §3.4, not because the
pipeline is broken.

**Fourth, five of the eight metrics cannot rank anything, and two are pure noise.** Intraclass
correlations from 20 designs × 7 seeds against the 239-design pool: `dockq` 0.870, `iface_plddt`
0.841, `ipsae` 0.647, `dg` 0.618 — but **`contacts` 0.003 and `cdr_sasa` 0.000**, which is pure seed
noise carrying no design information. Separately, `contacts`, `iface_plddt`, `cdr_sasa` and
`cdrh3_identity` are pinned at Good across the whole pool and `netsolp` is pinned at Medium, so
**5 of the 8 rubric metrics are constants** and the eight-metric harness effectively ranks on three.

**Fifth, the predicted loops barely move from the parent crystal.** CDR-H3 Cα RMSD after framework
superposition: crystal copy-2 against copy-1, **0.183 Å**; Boltz refolding pembrolizumab's own
sequence, **0.400 Å**; the 239 designs, with CDR-H3 identity spanning 15.4–46.2%, **mean 1.119 Å**
(median 1.030, max 2.744), with **205/239 (86%) within 1.5 Å** of the crystal loop. Replacing 7–11
of 13 CDR-H3 residues moves the predicted loop only 2.80× as far from the crystal as Boltz's own
refold of the *unmodified* sequence already is. Read beside the post-cutoff median Fab DockQ of
0.291, the pool's DockQ spread looks like variation *around a memorised template* rather than
evidence about the designs.

### 7.1 What the project says it can support

`submission/.../Challenge1/docs/methods_and_limitations.md:23-25`: *"What this licenses: the
pipeline distinguishes a destroyed interface from an intact one. It cannot rank two intact ones by
affinity. **Any ranking within our viable pool is not supported by our own metrics**, and we do not
claim it."*

`submission/.../Challenge2/docs/methods_and_limitations.md:50`: *"We can support exactly one claim
about this molecule, and it is not binding"* — namely that it is aimed at the right epitope.

Two supporting controls justify even that much. An **epitope knockout** — deleting PD-1's binding
face (527 heavy-atom contacts) against a matched off-interface control — moves ipSAE and interface
pLDDT strongly (17× and 64× their own seed sd) while **PRODIGY ΔG and the contact count do not
respond at all**; and ΔG carries the largest single share of the ranking's variance. A
**composition-matched null** — permuting a design's CDR-H3 residue order, keeping length,
composition, aromatic count and charge identical — costs 0.118 DockQ (28/30 paired wins,
p = 2.4 × 10⁻⁶), but **15 of 30 scrambles land inside the pool's DockQ range**, and none exceeds its
median.

### 7.2 The variance result, which the project rates above the score

Across Boltz recycling depths 3 / 10 / 20 on the same input, a real crystallised complex (5GGS)
moves ipSAE **0.050**; the Challenge 1 design moves **0.036**; the de novo Challenge 2 design swings
**0.601** — twelve to seventeen times more — and convergence is **non-monotone**
(0.263 → 0.864 → 0.795). *"A near-native complex is essentially invariant in sampling depth; this one
is not converged at any depth we tested… The variance is the real result about de novo design; the
score is a point on it."*

---

## What to take away

1. **The drug attacks the tumour's defence, not the tumour.** Everything downstream — why occluding
   a surface patch is sufficient, why the epitope's *identity* matters more than its size — follows
   from that.
2. **A calibrated target beats a binary one.** "Overlaps the PD-L1 site" is passed by one shared
   residue. "Achieves ~58% coverage, like a drug that works" is a specification. The cost of getting
   it was one alignment and one contact calculation.
3. **Residue numbering is part of the metric definition.** IMGT versus Kabat changes CDR-H3 from 13
   residues to 11, which changes the denominator of every identity percentage and therefore which
   designs clear a gate.
4. **A prescribed fix is a design change.** N→Q and S→A sit on the same line of the handbook and
   differ by sixty-fold in outcome. The predictor of which is safe is the **contact count on the
   residue you are about to mutate**, available for free from a structure you already have. This
   generalises to every "conservative substitution" you will ever be offered.
5. **State what a null can detect.** The specificity panel's low scores on three decoys are weak
   evidence of specificity, and the project says so. The SKEMPI correlations are reported beside
   their ρ ≈ 0.41 detectable floor.
6. **A high score from a self-referential harness is not evidence of binding.** An anti-lysozyme
   antibody cleared all five hard cutoffs as a PD-1 binder, and a mutant that experimentally
   abolishes binding (ΔΔG +21.8 kcal/mol) scored *above* the wild type. Knowing that, and shipping
   it in the submission documents, is the most valuable thing in this project.

Next:
[how the scoring harness and the pipeline that feeds it were built](02-the-engineering-problem.md)
, then [the tools themselves, and where each one lies](03-the-toolchain.md) .
