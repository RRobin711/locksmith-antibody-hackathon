#!/usr/bin/env python3
"""Assemble the handbook's submission tree for Challenge 1. Writes submission/.

Challenge 2 has no design, so its folder is deliberately absent rather than empty --
an empty folder would look like an attempt that failed validation, whereas no folder
is an honest statement that nothing was submitted.

The docs/ folder carries the caveats at the front, not the back. That is a deliberate
choice: this project's strongest result is the evidence about what its own metrics can
and cannot support, and burying it would waste the only genuinely distinctive thing
here.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

from locksmith.config import load
from locksmith.metrics import dockq, ipsae, netsolp, novelty, plddt, prodigy, sasa
from locksmith.score import evaluate
from locksmith.submit import Design, build_challenge, build_zip
from locksmith.types import Provenance, Structure

# DELIBERATE PLACEHOLDER, not an unfixed §4.1 failure. §4.1 requires the master folder
# to be named exactly the team name, and an audit on 2026-09-21 correctly flagged this as
# a checklist failure *for a submission*. This project is not submitting (PLAN.md §15:
# built for the learning and as a work sample, not for a rank), so there is no team name
# to put here. Decided 2026-09-22. If that ever changes, this is the single place to
# change it -- `build_challenge` and `build_zip` both take the team name as an argument
# and the folder names are derived, so a rename is one edit plus a rebuild.
TEAM = "LOCKSMITH_DEV"
ROOT = Path("submission")

# The challenge this driver packages. `build_challenge()` and `build_zip()` in
# `submit/package.py` are already generic in the challenge number -- only this driver's
# INPUTS are Challenge 1 specific (the handbook constructs, the 5GGS native, the named
# winner), so the number lives here as a constant rather than as a literal buried at two
# call sites. Challenge 2 is packaged by `scripts/75_challenge2_package.py`, which
# reuses the same `build_challenge()`.
CHALLENGE = 1
WINNER = "mpnn_T0.5_s104_036"
NATIVE = Structure(pdb=Path("data/refs/prepared/5ggs_ABZ.pdb"),
                   provenance=Provenance.EXPERIMENT, label="5GGS")


def build_deck(path: Path, final: float, raw: dict) -> Path:
    """Delegates to `submit/deck.py`, and feeds it CHALLENGE 2's live scores too.

    The deck went stale once (it claimed no Challenge 2 design was submitted while one
    was in the package) because it was generated from Challenge 1's run only. It now
    reads Challenge 2's scores from that challenge's own scoring artefact, so a deck
    built here cannot contradict a package built by `scripts/75`.
    """
    import json
    from locksmith.submit import deck

    c1 = dict(raw); c1["final"] = final
    c2_path = Path("runs/challenge2_fold_r10/scores.jsonl")
    c2 = {}
    if c2_path.exists():
        viable = [json.loads(l) for l in c2_path.read_text().splitlines()
                  if l.strip() and json.loads(l).get("viable") is True]
        if viable:
            c2 = viable[0]
    if not c2:
        raise RuntimeError(
            "no viable Challenge 2 design found; the deck would have to state what "
            "Challenge 2 contains and cannot guess. Run scripts/80 first, or edit "
            "submit/deck.py deliberately.")
    return deck.build(path, c1=c1, c2=c2)


def main() -> int:
    cfg = load(); c = cfg.conventions
    hbc = json.loads(Path("data/refs/handbook_constructs.json").read_text())
    folds = [json.loads(l) for l in Path("runs/handbook_construct/index.jsonl").read_text().splitlines()
             if l.strip() and json.loads(l).get("ok")]
    if not folds:
        print("no handbook-construct folds; run scripts/55 first", file=sys.stderr); return 1
    f = folds[0]
    pdb, pae, plddt_npz = Path(f["pdb"]), Path(f["pae"]), Path(f["plddt"])
    conf = pdb.parent / f"confidence_{pdb.stem.replace('_model_0','')}_model_0.json"

    st = Structure(pdb=pdb, provenance=Provenance.PREDICTION, pae=pae, label=WINNER)
    raw = {k: v.value for k, v in prodigy.compute(st).items()}
    raw["ipsae"] = ipsae.compute(st, pae_cutoff=c["ipsae_pae_cutoff"],
                                 dist_cutoff=c["ipsae_dist_cutoff"])["ipsae"].value
    raw["iface_plddt"] = plddt.compute(st, cutoff=c["interface_dist_cutoff"]).value
    raw["cdr_sasa"] = sasa.compute(st)[f"cdr_sasa_{c['cdr_sasa_state']}"].value
    raw["dockq"] = dockq.compute(st, NATIVE, allowed_mismatches=c["dockq_allowed_mismatches"],
                                 interface_agg=c["dockq_interface_agg"])["dockq"].value
    raw["netsolp"] = netsolp.compute(hbc["heavy"], hbc["light"],
                                     construct=c.get("netsolp_construct", "fv"))["netsolp"].value
    raw["cdrh3_identity"] = novelty.compute(hbc["heavy"], challenge=CHALLENGE).value
    sc = evaluate(raw, challenge=CHALLENGE, cfg=cfg)

    metrics_md = ["# Our own recomputation of the eight scored metrics", "",
                  "**DockQ will not score this submission at its defaults.** It exits 1",
                  "with no output. `--allowed_mismatches` is required and the minimum",
                  "value that works is **15**, exactly the number of substitutions in this",
                  "design; we pass 40 for headroom:",
                  "",
                  "```",
                  "$ DockQ structures/design_1_complex.pdb 5ggs_ABZ.pdb",
                  "ERROR:root:For chains ['A'] no identical corresponding chain was found "
                  "between in the native.",
                  "",
                  "$ DockQ structures/design_1_complex.pdb 5ggs_ABZ.pdb \\",
                  "      --allowed_mismatches 40 --mapping ABC:ABC",
                  "Total DockQ over 3 native interfaces: 0.816 with ABC:ABC model:native mapping",
                  "```",
                  "",
                  "`--allowed_mismatches` defaults to **0**, and a redesigned CDR is by",
                  "definition not identical to the native, so the default refuses every",
                  "mutated design rather than scoring it low. `--mapping ABC:ABC` pins the",
                  "chain correspondence that §4.2.2 already fixes (A=heavy, B=light,",
                  "C=antigen); left free, DockQ searches, and a wrong mapping scores a good",
                  "design badly. Native reference: PDB **5GGS**, chains A/B/Z renamed A/B/C",
                  "(chain **C of the deposited crystal is a second copy of the antibody heavy",
                  "chain**, not the antigen -- using it silently scores the wrong interface).",
                  "",
                  f"Design `{WINNER}`, folded on the handbook's §4.2.2 constructs.",
                  f"Conventions: `band_value={cfg.band_value}`, "
                  f"`dockq_interface_agg={c['dockq_interface_agg']}`, "
                  f"`netsolp_construct={c.get('netsolp_construct')}`, "
                  f"`netsolp_chain_agg={c['netsolp_chain_agg']}`.", "",
                  "| metric | value | band | sub-score |", "|---|---|---|---|"]
    for m in sorted(raw):
        metrics_md.append(f"| `{m}` | {raw[m]:.3f} | {sc.bands.get(m,'-')} | {sc.sub.get(m,0):.1f} |")
    metrics_md += ["", f"Categories: " + ", ".join(f"{k} {v:.3f}" for k, v in sc.categories.items()),
                   "", f"**Final: {sc.final} / 100. Viable: {sc.viable}.**", "",
                   "Band values are a handbook ambiguity; see `docs/` and",
                   "`results/handbook_conformance.md`. Under the three readings the same design",
                   "scores 84.0 / 90.0 / 96.0, which is a property of the reading, not the design."]

    docs_md = f"""# Methods and limitations — {TEAM}, Challenge 1

## Read this first

This submission's design clears all eight hard cutoffs and scores {sc.final}/100. **We do
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

NetSolP is **{raw['netsolp']:.3f}**, Medium band, under `min(VH, VL)` aggregation.
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

`cdrh3_identity` is **{raw['cdrh3_identity']:.1f}%** and scores Good. That is the metric
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

## This score is an envelope too, and we measured it

Boltz's `--diffusion_samples` defaults to 1, so every pose-derived metric here came from a
single diffusion draw. Five samples from one run (MSA shared, so this is pure diffusion
variability):

| diffusion sample | 0 (submitted) | 1 | 2 | 3 | 4 | spread |
|---|---|---|---|---|---|---|
| ipSAE | 0.822 | 0.841 | 0.827 | 0.840 | 0.861 | 0.039 |
| **DockQ** | **0.816** | 0.798 | 0.801 | 0.820 | **0.711** | **0.109** |
| composite | **96.0** | 94.0 | 96.0 | 96.0 | 94.0 | **94.0–96.0** |

**ipSAE is stable and DockQ is not.** We expected the opposite — this complex is nearly
invariant to Boltz recycling depth (ipSAE range 0.036 over depths 3→20), and we predicted
in advance that it would be equally invariant here. It is not. Recycling refines a
representation the trunk has already committed to; the diffusion head **generates the
coordinates**. A memorised complex can have a confidently-determined interface and still
place its atoms differently enough between draws to move a structural comparison by 0.109
DockQ. **Confidence stability does not imply coordinate stability**, and DockQ is the only
metric scored here that reads coordinates against an external reference.

Read the score as **94.0–96.0**. The design is viable under every sample; no metric
approaches a §7.2 cutoff in any of them.

Note also that `model_0` — the submitted one — is joint-best of the five. Boltz ranks its
output by confidence, so what we submit is an argmax rather than a sample.

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
"""

    repro_md = f"""# Reproducing every number we report

Written because an independent reviewer ran the obvious command and got a crash rather
than a score. **If a number cannot be reproduced from the artefact we hand over, we have
not really handed over the number.** Everything below was executed against the files in
this package, not recalled.

## The one that fails at defaults: DockQ

```
$ DockQ structures/design_1_complex.pdb 5ggs_ABZ.pdb
ERROR:root:For chains ['A'] no identical corresponding chain was found between in the native.
$ echo $?
1
```

Exit status **1**, no score printed. **`--allowed_mismatches` is mandatory and the
minimum value that works is 15** — exactly the number of substitutions in this
design, so the flag is not arbitrary. We pass 40 for headroom. `--mapping ABC:ABC`
is *not* strictly required (DockQ resolves the same mapping on its own and returns
the identical 0.816), but we pass it because leaving the search free means a
different input could silently be scored under a different correspondence:

```
$ DockQ structures/design_1_complex.pdb 5ggs_ABZ.pdb \\
      --allowed_mismatches 40 --mapping ABC:ABC
Total DockQ over 3 native interfaces: {raw['dockq']:.3f} with ABC:ABC model:native mapping
  A,B  DockQ 0.931      (heavy-light framework -- near-perfect by construction)
  A,C  DockQ 0.723      <-- the interface the design actually creates
  B,C  DockQ 0.794
```

- `--allowed_mismatches` defaults to **0**. A redesigned CDR is not identical to the
  native by definition, so the default refuses *every* mutated design instead of scoring
  it badly. 40 is comfortably above our 15 substitutions.
- `--mapping ABC:ABC` pins the correspondence §4.2.2 already fixes (A=heavy, B=light,
  C=antigen). Left free, DockQ searches, and a wrong mapping scores a good design badly.

**Which number is "the" DockQ.** We report `{c['dockq_interface_agg']}`, DockQ v2's own
Total over the three interfaces, because that is what an organiser reads off the tool's
summary line. The handbook says only that DockQ "returns a docking quality score between
0 and 1" and does not say how to combine three interfaces. Worth knowing when comparing:
the Total averages in the **heavy-light framework interface (0.931)**, which no design
touches and which is near-perfect by construction. The interface our design is actually
responsible for is **A-C = 0.723**.

## The native reference, and a trap in it

Use PDB **5GGS** with chains **A, B, Z** renamed to A, B, C. **Chain C of the deposited
crystal is a second copy of the antibody heavy chain, not the antigen.** Scoring against
raw chain C compares our antibody to an antibody and yields a confidently wrong number.
Our prepared reference is `data/refs/prepared/5ggs_ABZ.pdb` in the repository.

## The other seven

All seven are computed from the two files in `structures/` plus `sequences/design_1.fasta`,
with the conventions named in `metrics/scores.md`. The conventions that are NOT fixed by
the handbook, and therefore change the number:

| metric | convention | our setting | why it matters |
|---|---|---|---|
| all | `band_value` | `{cfg.band_value}` | the same design scores 84.0 / 90.0 / 96.0 under the three readings |
| `dockq` | `dockq_interface_agg` | `{c['dockq_interface_agg']}` | one band |
| `netsolp` | `netsolp_construct` | `{c.get('netsolp_construct')}` | Fv, per §6.2.1; we used Fab until 2026-09-20 |
| `netsolp` | `netsolp_chain_agg` | `{c['netsolp_chain_agg']}` | VH 0.699 vs VL 0.569 -- `min` picks the light chain |
| `cdr_sasa` | `cdr_sasa_chains` | `{c.get('cdr_sasa_chains')}` | none here; Good either way |

**NetSolP model choice is not cosmetic.** NetSolP ships three predictors and on
pembrolizumab -- a licensed antibody that must pass developability -- they score
0.733 / 0.637 / 0.379 on VH against a 0.50 cutoff. Only the full ESM1b 5-fold ensemble
clears it. **`predict.py` does default to `ESM1b`, so the tool's own default is the
one that passes** — an earlier version of this document claimed the default would
fail a marketed drug, which is wrong. The point that survives is that the *choice*
is load-bearing: run the same sequence under `Distilled` or `ESM12` and both this
design and pembrolizumab drop below the 0.50 cutoff. The variant belongs in the
config with its evidence, which is where we put it.
We use **ESM1b**.

## Validating the package itself

`scripts/58_validate_submission.py` re-derives all eight metrics from **this folder
alone** -- no run directory, no cached score -- and exits non-zero on any structural
problem or failed cutoff.
"""
    d = Design(name="design_1", heavy=hbc["heavy"], light=hbc["light"],
               antigen=hbc["antigen"], pdb=pdb, pae_npz=pae, plddt_npz=plddt_npz,
               confidence_json=conf if conf.exists() else None)
    base = build_challenge(ROOT, TEAM, CHALLENGE, d, metrics_md="\n".join(metrics_md),
                           docs_md=docs_md,
                           extra_docs={"reproducing_our_numbers.md": repro_md})
    print(f"built {base}")
    deck = build_deck(ROOT / TEAM / "pitch" / f"{TEAM}_presentation.pptx", sc.final or 0.0, raw)
    print(f"built {deck}")
    z = build_zip(ROOT, TEAM)
    print(f"built {z} ({z.stat().st_size/1e6:.1f} MB)")
    print(f"\nfinal={sc.final} viable={sc.viable}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
