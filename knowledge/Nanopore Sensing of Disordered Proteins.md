---
date: 2026-09-15
tags: [project, nanopore, idp, protein-design, locksmith-bio, learning]
status: living
---

Tags: [[Nanopore|nanopore sensing]] · [[IDP|intrinsically disordered proteins]] · [[Protein Design|de novo protein design]] · [[Locksmith Bio|Locksmith Bio]] · [[Learning|things I'm learning]]

# Nanopore Sensing of Disordered Proteins

The second half of the reading Ajitesh sent. Where
[the IDP notes](Intrinsically%20Disordered%20Proteins.md) establish *why* ensemble-averaged
measurements fail for disordered proteins, these two papers are the *measurement answer*:
instruments that read one molecule at a time and therefore return a distribution.

**Sources.** Shaji, Jain, Puthumadathil, Jana et al. 2026, *Nature Nanotechnology*,
doi:10.1038/s41565-026-02265-3 (**full 24-page PDF read**); Peng, Usami, Nakada, Sekiya et al.
2025, *ACS Nano* 19(49):41789–41802, doi:10.1021/acsnano.5c15080 (**abstract only** — ACS returned
403; abstract recovered via Europe PMC, so treat all Peng detail below as abstract-level).

---

## 1. How a nanopore sensor works, from first principles

Put a single protein pore in a lipid bilayer separating two chambers of salt solution. Apply a
voltage across the membrane. Ions flow through the pore and you measure the resulting **ionic
current** — typically tens to hundreds of picoamps.

Now add an analyte. When a single molecule enters the pore it partially occludes the channel and
the current drops. Two numbers fall out of each such event:

- **Blockade amplitude** — how much current was displaced, which tracks the molecule's excluded
  volume and its charge distribution inside the pore.
- **Dwell time** — how long it stayed, which tracks binding affinity and how it threads through.

Together they are a fingerprint. Crucially, **every event is one molecule.** You are not measuring
a population average; you are building a histogram of individual molecules, which is precisely the
capability Chen & Kriwacki identified as missing for IDPs. A heterogeneous mixture of monomers,
oligomers and fibrils shows up as *separate clusters* in amplitude–dwell-time space rather than as
a single smeared mean.

**Conductance** is quoted in siemens (S); these pores are in the nanosiemens range, measured in a
defined salt background because conductance scales with ionic strength — hence the convention of
reporting "in 1 M KCl".

## 2. Shaji et al. 2026 — a self-assembling α-helical pore for biomarker profiling

Most workhorse biological nanopores are **β-barrels** (α-haemolysin, MspA, aerolysin). α-Helical
pores are attractive instead because they offer flexibility, finer control of pore diameter and
engineerable charge selectivity — but, as the authors put it, "their rational design and assembly
remain challenging".

**What they built.** A single peptide, **pPorA**, derived from the porin PorACj, self-assembles
into flexible α-helical nanopores that insert into lipid membranes. The system has an unusual
property: **one oligomeric state yields two pore architectures**, which they call **S-pores** (small
conductance) and **L-pores** (large conductance).

By incorporating **unnatural amino acids** they engineered small- and large-diameter variants with
single-channel conductances of **2.4 nS and 3.5 nS in 1 M KCl** respectively, while retaining a
common **octameric** architecture. That is the notable design result: diameter tuned without
changing subunit stoichiometry.

**What they detected.**

| Analyte | Pore | Result |
|---|---|---|
| Sugars, peptide enantiomers | both | baseline demonstration of discrimination |
| **α-synuclein** variants (Parkinson's) | **L-pores** | including a pathogenic **C-terminal deletion mutant at KD ≈ 20 nM** |
| α-syn species in heterogeneous mixtures | L-pores | **charge-resolved identification** via selective electrostatic trapping of the α-syn **N-terminus** |
| α-syn aggregation over time, ± inhibitor | L-pores | resolved the pathway **monomer → toxic oligomer → fibril** |
| **Humanin** (apoptosis), **SOD1** peptides (ALS) | **S-pores** | smaller IDP biomarkers, showing size-tuned sensing |

The aggregation-pathway result is the one with the most obvious translational reach: the authors
state it "establishes a platform for **screening therapeutic drugs that selectively block toxic
α-syn oligomers**". Aggregation is a *kinetic, heterogeneous* process — exactly the thing bulk
assays average into uselessness.

**What they say is still weak** (stated in their own Conclusion, worth recording because papers
rarely volunteer this):

- The **MD simulations rely on approximations**, specifically "simple pore models and high electric
  fields" — the simulated fields exceed physiological conditions to get events to happen on
  simulable timescales.
- **No experimental structures of these pores exist**, which "has limited elucidation of the
  molecular determinants governing their sensing mechanism". They are engineering a device whose
  atomic structure they have not solved.
- They propose that "α-helical pore design rules can be refined through **computational design**"
  as the path forward.

## 3. Peng et al. 2025 — fully de novo α-helical nanopores

Where Shaji et al. *derive* their peptide from a natural porin, Peng et al. design theirs from
scratch. Their stated gap: "de novo α-helical nanopores with sufficiently large dimensions to
accommodate single-molecule sensing have not been previously reported."

**The design principle** is helix-packing motifs — short sequence patterns that make two
transmembrane helices pack against each other at a defined crossing angle. They use **GX₆G** and
**GX₃G** (glycine, six or three arbitrary residues, glycine). The small side chain of glycine lets
helix backbones approach closely; the spacing sets the register. Two designs follow, named **FFK**
and **LEK**.

**Results:** both form high-conductance nanopores in lipid membranes. **FFK** shows *multiple*
conductance states; **LEK** forms *more monodisperse* pores. Both assemble by a **stepwise
monomer-joining** mechanism, with FFK's assembly and disassembly dynamics significantly faster.
For sensing, both detect cyclodextrin derivatives, and LEK additionally senses poly-L-lysine.

The monodispersity difference is the practically important finding. A sensor with multiple
conductance states requires you to disentangle "which pore state am I in" from "which analyte is
in it" — a nuisance variable sitting directly on top of your signal.

## 4. Why this pairing was on the reading list

Read together the two papers sketch a research programme:

1. IDPs are the disease-relevant targets, and they demand **single-molecule** measurement (§1).
2. α-Helical pores are the promising instrument class but are **hard to design** (Shaji).
3. Shaji's route is *derive from nature and engineer* — with unnatural amino acids for diameter
   control, and an admitted gap where structural and computational design rules should be.
4. Peng's route is **design from scratch** — and it works, at the cost of less mature performance.
5. Shaji's own stated next step is precisely Peng's method: refine α-helical pore design rules
   **through computational design**.

## 5. The connection to the hackathon nobody would state out loud

The ACS Nano paper is **de novo protein design**. Not antibody design — nanopore design — but the
same discipline, the same question (can we specify a sequence that folds and functions as
intended?), and increasingly the same toolkit.

So the hackathon is not a detour from Locksmith's science. It is the **same capability aimed at a
different molecule**: theirs makes sensors for disordered proteins, ours makes binders for a
folded one. A pitch that notices this — that positions the antibody work as a demonstration of a
design capability the company's own roadmap explicitly asks for — lands differently from one that
just reports metrics.

See the company-context note *(that note is kept private and is not in this repository)* for how far that inference can
honestly be pushed, [the design-problem note](De%20Novo%20Design%20and%20the%20Two%20Challenges.md) for what
de novo design means in our case, and [the project story](../PROJECT-STORY.md) for the arc.
