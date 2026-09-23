# Methods and limitations — LOCKSMITH_DEV, Challenge 1

## Read this first

This submission's design clears all eight hard cutoffs and scores 96.0/100. **We do
not think that number means the design is good, and the evidence for that is ours.**

Three controls we ran on our own pipeline:

1. **Epitope knockout.** Deleting PD-1's binding face (527 heavy-atom contacts) against a
   matched off-interface control: ipSAE and interface pLDDT respond strongly (17x and 64x
   their own seed sd). **PRODIGY ΔG and the contact count do not** — and ΔG carries the
   largest single share of our ranking's variance.
2. **Measured affinity.** 45 point mutants of a different antibody-antigen complex (3HFM)
   with experimental ΔΔG from SKEMPI 2.0: **no metric tracks affinity** (bound: no monotone
   effect stronger than ρ ≈ 0.41 at n=45). Mutations that abolish binding score like the
   wild type — `NL31A` at ΔΔG +21.8 kcal/mol gives ipSAE 0.917 against the wild type's 0.903.
3. **Composition-matched null.** Permuting a design's CDR-H3 residue order — identical
   length, composition, aromatic count and charge — costs 0.118 DockQ (28/30 paired wins,
   p=2.4e-06). But **15 of 30 scrambles land inside our pool's DockQ range**, and none
   exceeds its median.

**What this licenses:** the pipeline distinguishes a destroyed interface from an intact
one. It cannot rank two intact ones by affinity. **Any ranking within our viable pool is
not supported by our own metrics**, and we do not claim it.

## Specificity

The design shows predicted cross-reactivity with **TIM-3**, a human checkpoint receptor
with the same Ig V-set fold as PD-1: ipSAE **0.513** (n=8 seeds) against pembrolizumab's
**0.331** and a real TIM-3 binder's **0.682** (Mann-Whitney p=0.038, bootstrap 95% CI on
the difference [+0.045, +0.320]). This trips the failure condition we pre-registered
before running the panel. It travels with the design.

## Developability

NetSolP is **0.569**, Medium band, under `min(VH, VL)` aggregation.
The two chains are **VH = 0.699, VL = 0.569**.

This is mostly not a property of our design: ProteinMPNN redesigns only the heavy-chain
CDRs, so the light chain is pembrolizumab's in all 239 designs and scores 0.569 on the Fv.
Under `min` aggregation it caps every design we could ever make this way, so the composite
is pinned at Medium regardless of the heavy chain.

**One correction we owe the reader, because our own earlier wording invited the wrong
inference.** Across the 239-design pool, 168 (70%) have VH >= 0.70, the Good edge. **This
design is not one of them: its VH is 0.699** -- 0.001 below the edge, and below
pembrolizumab's own VH of 0.733. Quoting the pool statistic next to this design implied
its heavy chain cleared Good. It does not, and the margin is far smaller than anything we
can resolve. The fix is still light-chain CDR redesign; we did not do it.

## How novel is this, really

`cdrh3_identity` is **38.5%** and scores Good. That is the metric
§6.3.1 asks for, and we report it. **It is not a fair summary of how different this
antibody is from Keytruda, and we would rather say so than let the number speak.**

Measured against pembrolizumab over the same 232-residue heavy-chain construct:

| quantity | value |
|---|---|
| substitutions | **15** |
| whole-chain identity | **93.5%** |
| designable positions changed | **15 of 29** |
| CDR-H1 | `GYTFTNYY` -> `KSDMENNY` (6 changes) |
| CDR-H2 | `INPSNGGT` -> `INPLNGGT` (**1** change) |
| CDR-H3 | `ARRDYRFDMGFDY` -> `ALRPRDVDRGFYK` (8 changes) |

The light chain is pembrolizumab's, unchanged. So a reader who opens the FASTA sees a
nearly-identical antibody with one substantially rewritten loop, and §3.1's phrase
"significant sequence novelty" would be generous. The novelty score is real but it is
concentrated almost entirely in CDR-H3, which is what the rubric measures and weights.

## Liabilities we can see in the sequence

**CDR-H3 net charge is +2** (4 basic: R, R, R, K; 2 acidic: D, D) where pembrolizumab's
CDR-H3 is **0** (3 basic, 3 acidic). High positive charge in the CDRs is one of the
better-established sequence predictors of polyreactivity and fast clearance. We report
predicted TIM-3 cross-reactivity above as a specificity finding; **we did not connect the
two until after the design was chosen, and we do not claim the charge causes the
cross-reactivity** -- it is one observation and one prediction, not a demonstrated
mechanism. It is stated here because it was computable from the sequence for free, before
any structure existed, and nothing in the rubric would have surfaced it.

Aromatic content of CDR-H3 is **2** (F, Y) against pembrolizumab's **4** (Y, F, F, Y).
Tyr/Trp enrichment is among the most robust compositional features of natural paratopes,
so this is a direction worth justifying rather than a neutral fact.

**And our own aromatic filter does not justify it.** We had a CDR-H3 filter that kept
designs with ≤1 aromatic and that beat an equal-budget random subset at p<0.0001. On
2026-09-22 we re-ran that test with each scored metric as the outcome: it wins on
**2 of 6**, DockQ-to-the-parent-crystal and interface pLDDT, and **both are properties of
the structure predictor rather than of the interface**. Contact count runs the other way —
filtered designs make ~1.8 **fewer** heavy-atom contacts, which is what one should expect
from selecting against large aromatic side chains. We have withdrawn that filter as a
design rule.

## Developability liabilities in this design, found by our own scan

Handbook §9.2 asks for no NG/DG deamidation motifs in CDRs. **This design carries `NG` at
heavy chain position 55, inside CDR-H2.**

It is pembrolizumab's own motif, not one we introduced — but both positions sat inside the
29 IMGT positions we made designable, so removing it was free and we did not take it. Our
redesign changed CDR-H2 at exactly one position (S54L) and left `N55-G56` intact.

Also present and worth stating: `M29` in CDR-H1, introduced by our redesign alongside the
inherited `M34` (§9.2: no exposed methionines in CDRs) — though measured CDR-H1 hydrophobic
exposure is low at 79 Å², so this is a soft flag. The unpaired cysteine the scan reports is
an artefact of the handbook's own §4.2.2 construct (truncated hinge), not of our design.

Found by `src/locksmith/metrics/liabilities.py`, which was specified in our build plan,
never written, and only built on 2026-09-22 after an independent reviewer found two
glycosylation sequons in our Challenge 2 design. The scan is now part of the repository and
regression-tested.

## Method

Fixed-backbone ProteinMPNN redesign of the 29 IMGT heavy-chain CDR positions of
pembrolizumab on PDB 5GGS, sampled across four temperatures (239 designs), folded as Fab
complexes with **Boltz-2** and scored with the handbook's stack. Selection used a
continuous surrogate because the rubric composite takes only three distinct values across
our pool. The named design was re-scored on fresh seeds.

**Predictor deviation (§8.1).** The handbook lists AlphaFold-Multimer as required for PAE.
We used Boltz-2 and convert its PAE to the AlphaFold-style JSON in `structures/`. We
verified AlphaFold2 could not be used here: without an MSA it cannot fold these complexes
(pLDDT 37, ipTM 0.11, interpenetrating chains), and a public-server MSA would disclose an
unpublished design.

**Construct.** Chains are the handbook's §4.2.2 sequences exactly — which are 5GGS's
SEQRES, including the His-tag on the heavy chain. Our earlier folds used 5GGS's
*coordinate* sequences, 10 residues shorter at the antigen's termini; re-folding on the
handbook constructs moved DockQ by −0.034 and changed no band.

## Known ambiguities in the rubric, and what we chose

| ambiguity | handbook | our choice | cost if wrong |
|---|---|---|---|
| band → 0-10 value | ranges only, "Good (9-10)" | `top` | 84.0 / 90.0 / 96.0 across readings |
| DockQ over 3 interfaces | "a docking quality score" | `global` (tool's own Total) | one band |
| NetSolP chain combination | "combined into a single value" | `min` | none here; both bands equal |
| CDR SASA scope | "the CDR loops (paratope)" | all six CDRs | none; Good either way |

Full audit: `results/handbook_conformance.md`.
