# Designing anti-PD-1 antibodies, and stress-testing the rubric that scores them

Computational antibody design for the Locksmith Bio × IBAB EC *De Novo Antibody Design
Hackathon*: redesign pembrolizumab's binding loops, and design a complete VH/VL antibody
against PD-1 from scratch. Everything here ran on **one laptop GPU** (RTX 5070 Ti, 16 GB)
plus **$2.82** of rented compute.

The designs score 94.0 and 93.6 out of 100 on the organisers' rubric. **That is the least
interesting thing in this repository**, and the reason why is the point of the project:

> Six of the eight scored metrics are computed from files the entrant generates. The
> organisers do not re-fold the designs. So the structure predictor is a *scored
> component*, and a high score is partly a statement about your own confidence in
> yourself.

So the first thing built was not a design. It was the evaluator — and then the controls
that try to break it.

---

## The three findings worth your time

**1. An antibody that cannot bind PD-1 passes the rubric's hard gates.**
HyHEL-10 is raised against hen egg lysozyme. Docked against PD-1 through this identical
pipeline it clears **all five** of the handbook's §7.2 cutoffs on `model_0` — ipSAE 0.609,
ΔG −12.4 kcal/mol, 77 contacts, interface pLDDT 85.0, CDR SASA 1084 Å². Across six wrong
antibodies, **four of the five gates reject 0 of 6**. ΔG, contacts, interface pLDDT and
CDR SASA measure *that a complex was built*, not that it is the right one, so §7.2 rests
on ipSAE alone — and even there cetuximab's median lands **0.006** under the cutoff.

The mechanism matters: Boltz-2 defaults to `diffusion_samples=1` and ranks its outputs by
its own confidence, so `model_0` is **an argmax by construction, not a sample**. HyHEL-10's
*median* over five samples is 0.219. A default setting turned a distribution into its
maximum, silently, for every number this project produced for a week.
→ [`results/negative_control.md`](results/negative_control.md)

**2. A silently discarded input inverted a ranking — it did not merely add noise.**
Boltz compares an MSA's query length against the input chain and, on mismatch, **discards
the alignment and folds single-sequence**, announcing it only on stdout, which the harness
captured and threw away. Every Challenge 2 fold for nine days paired a 123-residue antigen
with a 113-residue cached alignment.

Isolated as a 2×2 on ipSAE: with a correct alignment **0.012** both before and after the
variable under test; without it, **0.773 / 0.686**. The no-MSA cells reproduce the
project's entire historical envelope, which is how the condition was identified at all.
Re-screening all 30 designs against a correct alignment promoted a design that had ranked
**29th of 30**, while the packaged one fell **0.864 → 0.013** from 1st.
→ [`results/msa_silently_discarded.md`](results/msa_silently_discarded.md)

**3. A 1.65× speed-up was measured corrupting structures and thrown away.**
Boltz pads a batch to its longest sequence, so a design's score depends on **which other
designs share its batch**. Against byte-identical serial references: 1 of 4 structures
reproduced, ipSAE moved by up to **0.30**, atoms by **72–89 Å**. All files present, all
scores plausible. The staggered alternative is byte-identical 4 of 4 at 1.30×, below the
pre-registered 1.5× bar, so folding runs serially.
→ [`results/throughput_arms.md`](results/throughput_arms.md)

---

## The designs

| | design | composite | viable | notes |
|---|---|---|---|---|
| **Challenge 1** | `mpnn_T0.5_s104_036` + `N55Q` | **94.0** | ✅ | CDR-H3 `ALRPRDVDRGFYK`, 38.5% identity to pembrolizumab |
| **Challenge 2** | `bb_8_0` | **93.6** | ✅ 5/5 samples | de novo VH/VL, CDR-H3 18.2% to human germline |

Selected from **239** Challenge 1 designs (four ProteinMPNN temperatures, *all* folded
rather than filtered, so every filter stays evaluable offline and non-circularly) and
**144** Challenge 2 folds over 18 epitope-conditioned backbones.

**Read the Challenge 1 DockQ as `0.799579`, not `0.800`.** It bands *medium*, 0.00042
below the Good edge. This scored 96.0 for nine days because the metric parsed DockQ's
**printed** summary, which rounds to 3 dp. Two points came from a `printf`. A project
arguing the rubric is gameable cannot keep them.
→ [`docs/lecture/CORRECTIONS.md`](docs/lecture/CORRECTIONS.md) §C3

---

## What this does *not* establish

Stated plainly, because the rest of the repo is an argument for stating it plainly:

- **No wet-lab validation.** Nothing here was expressed, purified or measured.
- **No binding claim.** ipSAE 0.904 means Boltz places the antibody on PD-1 with high
  confidence. Against 40 real crystal structures that confidence tracks pose accuracy at
  **ρ = +0.702** — which is why it is worth reading — but it is not an affinity
  measurement, and this project's SKEMPI work found **no metric in the stack tracks
  measured ΔΔG**.
- **Error rates are quoted per threshold or not at all.** The ipSAE ≥ 0.60 gate gives 0%
  FP / 58.3% FN at DockQ ≥ 0.23, and 12.5% FP / 25.0% FN at DockQ ≥ 0.49. An earlier
  version of the shipped document paired the 0% with the 25% — the flattering half of
  each, reachable at neither. It survived four audits.
- **The scores are self-reported** against a rubric this repo demonstrates is weak on four
  of five gates.

---

## Being wrong, on the record

[**`results/retractions.md`**](results/retractions.md) enumerates **20 claims this project
withdrew, refuted or superseded**, plus **5 figures flagged as not reproducing** — each
with the number that replaced it, the file that settles it, and any document still
carrying the stale wording.

It includes claims that were mine and confidently stated: a filter that beat 10,000 random
subsets at p<0.0001 and is still refuted, because the outcome variable was a property of
the predictor; two small-sample nulls promoted to rules and reversed at n=239; a shrinkage
correction that landed within 0.001 of prediction and **still cannot be called validated**,
because one fold with sd 0.467 cannot discriminate it (that needs k ≈ 73).

A **FLAGGED** status exists specifically for numbers known not to reproduce and
deliberately *not* replaced by a best guess — because a guess entered into a record is
indistinguishable from a measurement a week later.

---

## Layout

| Path | Contents |
|---|---|
| `src/locksmith/` | The library — folding, metrics, scoring, selection, packaging (**34** modules). |
| `scripts/` | **102** numbered drivers, one per experiment, in the order they were run. |
| `tests/` | Invariant suite (34 tests). Several exist because the bug they pin actually happened. |
| `results/` | **73** result write-ups, including **13** pre-registrations. |
| `docs/lecture/` | A 12-chapter course (~79k words) teaching the project from first principles. |
| `docs/sessions/` | **25** self-contained session docs — what was built, and what broke. |
| `knowledge/` | 14 teaching notes on the biology, method and toolchain. |
| `submission/` | The packaged deliverable, rebuilt by generators — nothing here is hand-edited. |
| `config/metrics.yaml` | Every scoring convention, each with the evidence that chose it. |

---

## Reproducing it

```bash
uv sync                                   # Blackwell needs the pinned cu128 index
uv run pytest tests/                      # 34 invariant tests
uv run python scripts/58_validate_submission.py submission/RYAN_BINNY
```

The validator takes **only the packaged folder**. It imports nothing from `runs/`, reads
no cached score, and re-derives every metric from the three files per design; its one
external input is the DockQ reference (PDB 5GGS), passed as an argument so it cannot
silently fall back on ours. A correct package exits 0; lowercasing a single FASTA header
exits 1 and names the violated handbook section.

*Validate the artifacts, not the pipeline that produced them* — a check that reuses your
own intermediate state proves nothing about what an evaluator sees.

---

## Where to start reading

1. [`STATE.md`](STATE.md) — current state: verified, trusted, blocked, what is left.
2. [`results/retractions.md`](results/retractions.md) — **before trusting any number here.**
3. [`docs/lecture/README.md`](docs/lecture/README.md) — the course, if you want the whole
   argument; [`CORRECTIONS.md`](docs/lecture/CORRECTIONS.md) first.
4. [`docs/sessions/README.md`](docs/sessions/README.md) — the working arc, one line per day.

**On this repository's prose:** its errors cluster in sentences, not in code. A
documentation guard found a shipped file asserting seven metrics of a design no longer in
the package. Where a results file and a generated artefact disagree, **the artefact is
right** — it was recomputed; the sentence was copied.

---

## Notes

- **Not a contest entry.** The handbook's deadline (14 December 2025) had passed before
  this work began. It is a methods exercise against a real, specified brief.
- The submission package was built under the placeholder team name `LOCKSMITH_DEV` until
  2026-09-26; session docs and results files written before then use those paths.
- The organisers' handbook is **not** redistributed here — see [`source/`](source/).
  Everything the code depends on was extracted into
  [the spec session doc](docs/sessions/2026-09-14-antibody-hackathon-spec-and-scoring.md).
- Code is MIT ([`LICENSE`](LICENSE)). Reference structures are from the RCSB PDB.
