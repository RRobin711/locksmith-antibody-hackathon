---
date: 2026-09-15
tags: [project, idp, structural-biology, locksmith-bio, learning]
status: living
---

Tags: [[IDP|intrinsically disordered proteins]] · [[Structural Biology|structural biology]] · [[Locksmith Bio|Locksmith Bio]] · [[Learning|things I'm learning]]

# Intrinsically Disordered Proteins

Background reading Ajitesh sent ahead of the [[../PLAN|Locksmith Bio antibody hackathon]].
Not the hackathon task — antibodies are well-folded — but this is the science the company
is built on, and §4 below argues the connection is much tighter than it first looks.

**Sources.** Uversky 2019, *Frontiers in Physics* 7:10 ([full text read](https://doi.org/10.3389/fphy.2019.00010));
Kulkarni et al. 2022, *Biophysics Reviews* 3(1):011306, doi:10.1063/5.0080512 (**abstract only** —
AIP returned 403, so anything below attributed to Kulkarni comes from the published abstract);
Chen & Kriwacki 2018, *J Mol Biol* 430(16):2275–2277, PMC7086911 (full text read — note this is an
**editorial introducing a special issue**, not a review, despite being sent as "a third IDP overview").

---

## 1. The dogma being broken

Anfinsen's dogma, the organising principle of protein science for over a century: **a protein's
amino-acid sequence determines a unique three-dimensional structure, and that structure
determines its function.** Sequence → fold → function. Christian Anfinsen won the 1972 Nobel for
showing a denatured ribonuclease refolds spontaneously to its active form, so the folding
instructions must live in the sequence itself.

Uversky's opening sentence names the mental image this produces: the **"lock-and-key" model** —
a rigid, precisely shaped protein meeting a precisely shaped partner. Hold onto that phrase; it
comes back in [[Locksmith Bio — Company Context|why the company is called what it is]].

**Intrinsically disordered proteins (IDPs)** break it. They are functional proteins that never
adopt a unique structure. **Intrinsically disordered protein regions (IDPRs)** are the same thing
embedded inside an otherwise-folded protein — most real proteins are hybrids.

## 2. How common, and why that matters

From Uversky's survey of the computational literature:

- IDPs and IDPRs occur in **every proteome analysed** across all kingdoms of life, and in every
  viral proteome analysed so far.
- The fraction of sequences carrying **long IDPRs (≥30 residues)** is roughly comparable between
  bacteria and archaea, and **drastically higher in eukaryotes**.
- Disorder abundance **increases with organism complexity**. The proposed reason is that
  eukaryotic cellular signalling leans heavily on disordered proteins.
- Only a small fraction of proteins with solved crystal structures in the PDB contain *no*
  disorder at all.

That last point carries a methodological sting worth internalising: **the PDB is a biased
sample.** A structure gets solved when a molecule holds still. Disorder is under-represented in
the very database that trained our intuitions — and, not incidentally, trained AlphaFold.

A further trap Uversky flags: presence in the PDB does not prove a protein is ordered, because an
IDP can undergo **induced folding** on binding a partner. Crystallise the complex and you see a
well-defined structure; the free protein was a cloud.

## 3. The reframe that makes IDPs less paradoxical

The naïve reading is that IDPs *violate* Anfinsen. Kulkarni et al. argue the opposite and it is
the more useful framing:

> IDPs "exist as ensembles that sample a quasi-continuum of rapidly interconverting conformations
> and, as such, may represent proteins at the extreme limit of the Anfinsen postulate."

The sequence still determines the outcome. It just determines an **ensemble** rather than a single
minimum. In energy-landscape terms, a folded protein sits in a deep, steeply funnelled well; an
IDP has a **weakly funnelled** landscape — many shallow minima, rapid interconversion, no single
reference conformation. Kulkarni notes this makes the usual landscape analysis awkward precisely
because "in the absence of a reference conformation" it is hard to choose reaction coordinates.

Downstream consequences they draw out:

- IDP conformational dynamics contribute **conformational noise** in the cell.
- Dysregulated IDPs increase that noise and produce **"promiscuous" interactions**.
- That rewires the **protein interaction network (PIN)**, which is how cells produce context-
  appropriate responses — implicating IDPs in cellular decision-making and phenotypic switching.

So disorder is not sloppiness that evolution failed to clean up. It is a mechanism. A molecule
with no fixed shape can bind many partners, integrate multiple signals, and respond to
post-translational modifications by shifting the *population* of its conformers.

## 4. The measurement problem — the part that matters most

Chen & Kriwacki state it plainly, and this is the single most transferable idea in the reading:

> "A major challenge in establishing disorder–function relationships for IDPs is that their
> heterogeneous conformations are often incompletely characterized **due to use of experimental
> methods that provide only ensemble-averaged structural parameters.**"

If a molecule is genuinely a distribution over conformations, then **the mean is not a summary of
it — the mean is an artefact.** Average a population that spends half its time extended and half
compact and you report a middling conformation that no individual molecule ever occupies.

Their prescription is methods that report **distributions rather than averages**:

- **Single-molecule methods** — smFRET (they cite Holmstrom et al. on hepatitis C virus core
  protein), and increasingly in living cells. Also the natural home of
  [[Nanopore Sensing of Disordered Proteins|nanopore sensing, which reads one molecule at a time]].
- **Scattering** — SAXS/SANS, which constrain the maximum dimensions of the conformer population
  and can be used to *restrain* computed ensembles rather than fit a single structure.
- **Computation** — molecular dynamics with improved force fields and enhanced sampling. They are
  explicit that both force fields and sampling need further work to produce "accurate and
  well-converged structural ensembles that reflect experimental data".

## 5. Disease and druggability

IDPs are implicated in neurodegeneration, many cancers, and diabetes. Concrete mechanisms from
the special issue Chen & Kriwacki introduce:

- **β-synuclein** engages in transient, multivalent interactions with **α-synuclein** to *inhibit*
  its aggregation (Williams et al.).
- **α-synuclein/tau** heterotypic assembly is promoted by electrostatic interactions between them,
  accelerating misfolding (Bhasne et al.).
- **Fuzziness** (Fuxreiter) — complexes that remain dynamic and heterogeneous *after* binding.
  A "fuzzy complex" has no single bound structure either.

On druggability the field has moved: intrinsically disordered transcription factors "are not
undruggable as commonly thought". The emerging conceptual frame is **structural ensemble
modulation** (Heller et al.) — a small molecule does not lock an IDP into one shape, it *shifts the
populations* within the ensemble. The therapeutic object is a distribution, so the therapeutic
action is a reweighting.

## 6. Uversky's closing position

Worth quoting because it sets the tone of the whole field:

> "From the viewpoint of order-based functionality, IDPs/IDPRs represent a complete disaster. They
> contradict to the basic logics of the 'lock-and-key'-centered protein functionality and break
> multiple rules devised by the researchers studying structure, folding, and functions of ordered
> proteins."

He lists what they do that ordered proteins should not be able to: respond strongly to
environmental cues, fold *differently* depending on which partner they meet, fold only partially
while binding, or bind tightly with **no** binding-induced folding at all.

---

## 7. The transferable principle

**When the object you are studying is a distribution, a point estimate plus a confidence number
is not a description of it — it is a category error.**

This generalises far past biophysics. It is the same mistake as reporting a model's accuracy
without its error distribution, or a latency p50 without the tail. The IDP field is essentially a
twenty-year worked example of what it costs to notice this late.

**And it applies directly to the hackathon** — see
[[Antibody Architecture|why CDR-H3 is the most variable part of the molecule]] and
[[../PROJECT-STORY|the project story]] for the wider arc. The evaluation rubric asks for one `complex.pdb` —
a single set of coordinates — plus a PAE matrix, and scores the interface confidence. But
**CDR-H3, the loop that determines antibody specificity, is the most conformationally variable
element in the entire antibody repertoire.** Representing it as one static structure with a scalar
confidence is exactly the modelling failure described in §4.

That is the argument for the ensemble workstream — see
[[Confidence Is Not Truth|the note on why confidence scores are not evidence]] and
[[../PLAN|§10.1 of the delivery plan]]: sample CDR-H3 across seeds and predictors, report the
conformational spread, and show whether the designed interface is supported by a converged loop
or by one lucky sample. It is a stronger claim than ipSAE can make, and it is stated in the
vocabulary of the people reading the pitch.
