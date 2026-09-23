---
date: 2026-09-23
tags: [project, lecture, learning, resource, coding, structure-prediction]
status: review
---

# 03 — The Toolchain

> ⚠️ **Challenge 2's computational evidence was withdrawn on 2026-09-23** — every Challenge 2 fold used a silently discarded antigen alignment. See [[CORRECTIONS|corrections C1 and C2, and what they do and do not invalidate]] — C2 also refutes the contact-count rule this course calls its best finding. Challenge 1 is unaffected.

**What this chapter teaches.** Every piece of third-party software the campaign depended on: what it
computes, exactly how it was invoked, and the specific way it goes wrong. The organising claim is
that **a tool's defaults encode its author's assumed use case, not yours**, and that almost every
tool here had at least one default that was wrong for this project and silent about it. We then work
through three infrastructure stories in full, because each is a complete, transferable lesson: the
numpy 2.0 fault line and why isolated environments are architecture rather than workaround; the
Blackwell saga, which is the best worked example you will find of *verify with arithmetic, not with
introspection*; and the local workflow — overnight jobs, resumability, and a process-table idiom that
idled a GPU for four and a quarter hours. We finish with a costs-and-timings table.

Companion chapters: [[02-the-engineering-problem|the pipeline these tools plug into]] and
[[01-the-biological-problem|what the numbers are supposed to mean biologically]].

---

## 1. The version ledger

Read from the live filesystem, not from a requirements file.

| Tool | Version / commit | Where it lives | Role |
|---|---|---|---|
| **Boltz-2** | `boltz 2.2.1` (torch 2.14.0, numpy 1.26.4) | `~/.local/share/uv/tools/boltz/`; weights 7.6 GB at `~/.boltz/` | primary structure predictor; every scored fold |
| **ProteinMPNN** | commit `8907e667…`, 2023-06-27; weights `v_48_020` | `~/.local/share/locksmith/ProteinMPNN/` | fixed-backbone sequence design (both challenges) |
| **RFantibody** (RFdiffusion + ProteinMPNN + RF2) | upstream repo, installed `--no-deps` | `~/.venvs/rfab-cpu` locally; the rented pod | de novo backbone diffusion (Challenge 2) |
| **ColabFold / AF2** | `colabfold 1.6.3`, `alphafold-colabfold 2.3.20`, jax 0.10.2 (cuda12); 5.3 GB weights | `~/.venvs/colabfold` | consensus / cross-calibration predictor |
| **DockQ** | `dockq 2.1.3` (numpy 1.26.4) | `~/.local/share/uv/tools/dockq/` | pose comparison against 5GGS (Challenge 1 only) |
| **PRODIGY** | `prodigy_prot 2.4.0` (numpy 2.4.6) | `~/.local/share/uv/tools/prodigy-prot/` | ΔG (kcal·mol⁻¹) and intermolecular contact count |
| **ipSAE** | vendored at commit `6174cf9e71cb1bd660cc805856a18c4871a6dec3` (2026-01-03) | `vendor/ipsae/ipsae.py`, 45,140 B | interface confidence from the PAE matrix |
| **NetSolP-1.0** (DTU) | source dated 2021; quantized ONNX, 4.7 GB | `~/.local/share/locksmith/netsolp/`, runtime `~/.venvs/netsolp` | sequence-only solubility |
| **ANARCII** | `anarcii 2.0.8` | `~/.venvs/locksmith` | IMGT numbering, CDR extraction |
| **gemmi** | 0.7.5 (main), 0.6.5 (inside boltz's env) | | PDB/mmCIF I/O, `NeighborSearch` for interfaces |
| **freesasa** | 2.2.1 | | CDR SASA (Å²) |
| **Biopython / biotite** | 1.88 / 1.7.1 (main) | | pairwise alignment for identity metrics |
| **python-pptx** | 1.0.2 | main env | the 3-minute pitch deck, generated in code |
| **torch (main env)** | **2.11.0+cu128**, numpy 2.5.3 | `~/.venvs/locksmith` | |
| **Python / uv** | CPython 3.12.13, `requires-python = ">=3.12,<3.13"`; uv 0.10.9 | | every environment and tool install |

**Notably not used:** no DSSP anywhere — secondary structure was never needed. SASA is freesasa and
interface detection is a gemmi `NeighborSearch` at a 5.0 Å heavy-atom cutoff. **Chai-1** was scoped
as a third consensus predictor (`BUILD.md:295`) and **never built**; `src/locksmith/fold/` contains
only `boltz.py`, `colabfold.py`, `batch.py` and `__init__.py`. Stating that plainly is part of the
inventory: a planned component that does not exist is indistinguishable from one that passed.

---

## 2. Generators

### 2.1 ProteinMPNN

**What it does.** Fixed-backbone sequence design: given 3-D coordinates, sample amino-acid sequences
likely to fold to them.

**How it was used.** Challenge 1: redesign the **29 IMGT heavy-chain CDR positions** (H1 = 8,
H2 = 8, H3 = 13), located by ANARCII rather than by a hardcoded residue range. Held fixed: the rest
of the heavy chain, the **whole light chain**, and the **whole antigen** — because "ProteinMPNN will
happily redesign any chain it is given, and redesigning PD-1 would produce a molecule that binds a
protein nobody has" (`src/locksmith/design/mpnn.py:8-18`).

**Invocation** (`mpnn.py:116-126`, run with `cwd=MPNN_DIR`):

```
python protein_mpnn_run.py --pdb_path <abs> --pdb_path_chains A
   --chain_id_jsonl chains.jsonl --fixed_positions_jsonl fixed.jsonl
   --out_folder <out> --num_seq_per_target N --sampling_temp T --seed S --batch_size 1
```

**Temperature is the novelty dial.** T ∈ {0.1, 0.2, 0.3, 0.5}, giving design IDs of the form
`mpnn_T0.5_s104_036`. At the default 0.1, MPNN recovers native-like residues, so CDR-H3 identity may
fail the `<95%` novelty gate; the project reported `seq_recovery` per design rather than tuning the
temperature to hit a gate. The M3 primary arm was 239 designs: **T=0.1 × 60 (seed 101), T=0.2 × 59
(seed 102), T=0.3 × 60 (seed 103), T=0.5 × 60 (seed 104)**.

**The limitation that shaped the whole campaign.** ProteinMPNN is fixed-backbone and therefore
**cannot vary CDR loop length**. Since CDR-H3 length is one of the most important axes of antibody
diversity ([[01-the-biological-problem|and the one V(D)J recombination varies most]]), this means
the length axis "is a new generator, not an arm" — you cannot explore it without RFdiffusion. It was
left unexplored, and the project says so.

**Gotchas.** (a) MPNN writes the **native sequence first** in its output FASTA and then one record
per sample, so the parser skips `records[0]`. (b) Success is asserted on the artefact `seqs/<name>.fa`,
never on the exit code. (c) The returned heavy-chain length is asserted equal to the input length,
because an indel means the design was built against the wrong frame. (d) Fixed-position lists are
**1-based** over the chain's residues while `cdr_positions()` returns 0-based indices — an explicit,
commented off-by-one boundary in the code. (e) **Solubility is not in its loss** — nor is
glycosylation, [[01-the-biological-problem#6.2 The NG deamidation motif in Challenge 1's CDR-H2|deamidation]], oxidation or charge. It proposes post-translational liabilities at
roughly the rate they occur in the PDB, which is how two [[01-the-biological-problem#6.1 Two N-glycosylation sequons in the Challenge 2 paratope|glycosylation sequons]] reached a shipped
paratope.

A design-time trap worth carrying: `MpnnDesign` **names its fields by ROLE, not by chain**, so in the
light-chain arm, reading `.light` "would have screened the heavy chain 24× and *confirmed* the null
under test."

**Cost.** Four sequences from one backbone on 24 CPU cores: **2 seconds**. Negligible; it drops out
of the budget entirely.

### 2.2 RFdiffusion via RFantibody

**What it does.** Target-conditioned diffusion of antibody **CDR backbones** against a specified
epitope, then ProteinMPNN sequence design, then RoseTTAFold2 filtering. The equivariant core is an
**SE3-Transformer** whose message-passing kernels come from **DGL** — a detail that becomes load-
bearing in §6.

**Why this route.** The alternative — graft a germline framework and design CDR *sequences* with
ProteinMPNN on inherited geometry — "generates no new loop conformations, so it is not what §3.2 asks
for; putting it in the Challenge 2 folder would invite the obvious question."

**Framework.** RFantibody's shipped `hu-4D5-8_Fv.pdb` (humanised trastuzumab Fv), deliberately **not**
pembrolizumab's framework, "so 'de novo' is defensible rather than Challenge 1 relabelled."

**Input format.** **HLT**: a PDB with chains renamed H (heavy), L (light), **T (target)**, plus
`REMARK` records giving 1-indexed CDR loop positions. The batch container is a **Quiver (`.qv`)**
file.

**Hotspot conditioning.** The 26-residue PD-L1 competitive footprint on PD-1, extracted from 5IUS and
mapped onto 5GGS by explicit alignment, passed on the CLI as `-h "T64,T66,..."`.

**Three gotchas, each of which produces a plausible wrong answer rather than an error.**

1. `ab_pose.py:105-110` matches hotspots on `(chain, pdb_resnum)` and **silently skips misses**. Wrong
   numbering ⇒ zero hotspots ⇒ unconditioned generation wearing the target's name, with no error.
   Mitigation: the run log is grepped for exactly **26 "Using … as a hotspot"** lines. But note the
   epistemic limit, established in [[05-experiment-design|the experiment chapter]]: *"26/26 hotspots
   resolved" proves the tool RECEIVED your conditioning, not that it changed the output.* A
   manipulation check that cannot fail is not evidence; you still need an unconditioned arm or a
   patch null.
2. **RFdiffusion renumbers its output continuously across chains.** Measured on `gate0b_0.pdb`:
   H = 1–115, L = 116–219, **T = 220–332**, where the input PD-1 was numbered 31–143. A conditioning
   check keyed on `(chain, resnum)` therefore reports "zero hotspot contacts" for a perfectly good
   dock. Pass hotspots as **0-based ordinals within the target chain**.
3. **A near-miss caught before the run.** Every planning document said "5GGS chain C relabelled to T".
   **5GGS chain C is a second copy of pembrolizumab's heavy chain**; the PD-1 copies are chains Y and
   Z. Identity of the 5IUS PD-L1 footprint against each: chain Y **90.2%**, chain Z **90.1%**, chain C
   **15.4%** — and *all three report 26/26 residues mapped*. **Coverage is not the check; identity
   is.** The target actually built was 5GGS chain Z, 113 residues, author numbering 31–143.

**Two facts the CLI forces.** RFantibody spawns every stage as a **subprocess** using
`cmd = ['python', script_path]`, so a bare `python` must be on PATH — an absolute venv interpreter is
not enough, and the subprocess dies with `FileNotFoundError: 'python'`. And because an in-process
shim cannot reach a subprocess, any monkeypatch has to live in `sitecustomize.py` inside the venv's
`site-packages`.

### 2.3 RoseTTAFold2 — a filter, not a scorer

RF2 was run on the pod to filter MPNN sequences before bringing them home; **Boltz-2 remained the
scoring fold**, "so both challenges rest on one predictor and their numbers are comparable." That is
a deliberate comparability decision, not laziness.

The pod-side finding that justified keeping RF2 out of the scoring: its `interaction_pae` **cannot
rank docks** — [[04-measurement-theory#2. The intraclass correlation, and metrics that turn out to be constants|intraclass correlation]] **−0.113** against a detectable floor of 0.317 at n=10, k=3 —
and it disagreed with the eventual Boltz pose by **24.9 Å** on one design. A metric with negative ICC
is not a weak ranker; it is noise.

---

## 3. Folding

### 3.1 Boltz-2 — the primary predictor

Every flag was bought with a failure, and the docstring says which
(`src/locksmith/fold/boltz.py:1-28, 95-104`):

```
boltz predict <fasta> --out_dir <d> --output_format pdb --write_full_pae
  --diffusion_samples N --recycling_steps R --seed S
  --accelerator gpu --num_workers 0 --no_kernels --max_msa_seqs 1024
  [--use_msa_server]      # only when antigen_msa is None
```

| flag | why |
|---|---|
| `--no_kernels` | the optimised CUDA kernels need `cuequivariance_torch`; its absence produced a `ModuleNotFoundError` **inside the prediction loop, and exit 0**. Pure PyTorch is slower and works. |
| `--num_workers 0` | dataloader workers multiply host RAM; a fold was OOM-killed by the kernel with workers > 0 |
| `--max_msa_seqs 1024` | caps the antigen alignment depth |
| antibody MSA = literal `empty` | an antibody and its antigen have not co-evolved, so an antibody alignment carries no interface signal — and dropping two of three chains' MSAs **cut VRAM by about two-thirds and fixed a CUDA OOM**. Correct protocol and cheap protocol coinciding. |

Defaults in the driver: `construct="fv"`, `seed=1`, `diffusion_samples=1`, `recycling_steps=3`.

**The space-in-path trap.** Boltz's input is `>CHAIN|entity|msa` on one line, and its FASTA parser
**splits the MSA field on whitespace**. With the project root at `/home/rrobin711/Obsidian Personal/…`
it reported `FileNotFoundError: MSA file /home/rrobin711/Obsidian not found.`, then **printed a 100%
progress bar, initialised the GPU and carried on**. Fix: `_stage()` copies the MSA to
`~/.cache/locksmith/msa/` and *raises* if a space survives. The distinguishing detail: argv is safe
because the shell quotes it; a path inside a FASTA, YAML or config field is not.

**MSA caching, for two reasons — one scientific, one about disclosure.** `data/msa_cache/pd1_5ggs.csv`
holds **3,787 sequences**. (i) Every variant in a ranking panel must see the *identical* antigen
alignment, or the alignment drifts between designs and injects uncontrolled variance into the very
quantity being ranked. (ii) `--use_msa_server` uploads any chain with a blank MSA field to the
**public ColabFold MMseqs2 server**; the cache removes the server from the loop entirely, which is
"the only way to be sure a designed sequence never leaves the machine."

**`recycling_steps` is a first-class parameter, and inheriting it caused the project's biggest single
error.** The driver default is 3. At recycling 3, Challenge 2 scored **0/30 viable** — best ipSAE
0.372 against a 0.60 gate, with **15 of 30 at exactly 0.000**. That pile-up at the floor was the
tell, and it was written up before anyone looked. **WITHDRAWN.** Re-folded at **recycling 10**, one
design moved **0.263 → 0.864 / 0.842 / 0.856** across three seeds while four of the other top five
moved sideways or down. At recycling 3 the ranking was *actively misleading*: the design that clears
ranked 2nd; the one ranked 1st still fails. An under-converged predictor does not give you a noisy
ranking, it gives you a **compressed** one.

Two corrections travel with that result and both matter. First, at **recycling 20** the same design
gives ipSAE 0.795 / 0.883 / 0.731 across seeds — composite 93.6 / 96.0 / 93.6 — so convergence is
**non-monotone** (0.263 → 0.864 → 0.795) and the honest report is an envelope, 93.6–96.0. Second, the
first write-up said extra recycling "resolves" the pool; the pool data does not support that — mean
0.0640 → 0.0646, median 0.0056 → 0.0050, **still 15/30 at exactly zero**, and an r3↔r10 rank
correlation of only **0.432**. What survives is: *check convergence before interpreting a unanimous
failure — and "it changed when I sampled harder" is not the same as "it has now converged."*

**`diffusion_samples` defaults to 1, and Boltz orders its models by its own confidence.** Therefore
`model_0` at `diffusion_samples=1` is an **[[06-allocation-and-selection#5. Order statistics: when your prediction is silently a maximum|argmax by construction]]** — the maximum of a distribution
that was never drawn. Every pose-derived number the project reported for a week (ipSAE, DockQ, ΔG,
contacts, interface pLDDT, CDR SASA) was an order statistic. Measured at 5 samples: Challenge 1 moved
ipSAE 0.039 but **DockQ 0.109**, turning 96.0 into a **94.0–96.0** envelope; the de novo design moved
ipSAE 0.128, with 3 of 5 falling to Medium (**91.2–96.0**). Note that confidence stability does not
imply coordinate stability — ipSAE was steady on Challenge 1 while DockQ, the only metric reading
coordinates against an external reference, was not.

**And it costs almost nothing to know this: five samples took 2 m 54 s against roughly 2 m for one**,
because the MSA, trunk and recycling are shared and only the diffusion head reruns. That is the
single best cost-benefit ratio in the whole toolchain, and it went unclaimed for a week.

**Fab, not Fv.** The planned "cheap Fv screen → expensive Fab confirm" funnel was killed by
measurement: Fv ipSAE seed [[04-measurement-theory#1.3 Reliability|reliability]] **0.607** versus Fab **0.965** — the unclamped VH/VL elbow
shows up directly as measurement noise. Matching Fab precision needs ≥4 Fv seeds, which is **2.9× the
Fab's wall clock**, so the 2.5× residue saving inverts. *Any time a cheap proxy gates an expensive
measurement, the proxy's failures are invisible by construction.*

**Batching.** `src/locksmith/fold/batch.py` feeds Boltz a directory of inputs so the fixed
per-invocation cost (checkpoint load, featuriser build, antigen-MSA parse) is paid once. Projected
1.8× in the docstring; **measured 1.16×** — 84 s → 72 s per fold, i.e. 434 s for a batch of 6 — saving
0.8 h on a 239-fold arm rather than 2.4 h. That decomposes into a **fixed per-invocation cost of
≈14 s and a marginal fold of ≈70 s**, so batch 12 would give ~70.8 s (1.19×) and larger batches buy
almost nothing. The code was correct and accepted; the *justification* was the least-examined number
in the argument. `--seed` is **invocation-level, not per-record**, so `fold_batch` takes a single
`seed` argument "so that this is impossible to get wrong silently"; duplicate labels raise; and
artefacts are asserted **per label** so a half-failed batch costs one fold, not N. The acceptance test
is deliberately three-tier: **tier 0** a determinism control (run the *unmodified* path twice on the
same seed), **tier 1** byte-identity at batch 1, **tier 2** statistical equivalence above it (DockQ
within **±0.054 = 3× the 0.018 seed sd**) — because cuDNN and cuBLAS select kernels by tensor shape
and the tool may not be bitwise deterministic at all. *Without tier 0 you will blame your own code or
exonerate it with equal justification and no evidence.*

**Training cutoff.** Boltz-2's is **2023-06-01 on PDB *release* date** — release, not deposition —
read from the paper's own text rather than from a search summary. 5GGS was released in 2017 and is
therefore almost certainly memorised, so DockQ 0.820 on it is partly retrieval.

### 3.2 ColabFold / AlphaFold2-multimer

**Invocation** (`src/locksmith/fold/colabfold.py:47-56`):

```
colabfold_batch --model-type alphafold2_multimer_v3 --num-models N --num-recycle R
  --random-seed S --msa-mode <mode> --data ~/.cache/colabfold <fasta> <outdir>
```

with complexes given as one line, chains joined by `:`.

**A disclosure guard written in code, not prose.** The default `--msa-mode mmseqs2_uniref_env`
**uploads the query to the public MMseqs2 server.** For pembrolizumab/PD-1 that is harmless; for a
designed sequence it is an irreversible disclosure of unpublished work, and it is the *default*. So
`msa_mode` defaults to `single_sequence` and any server mode **raises** unless
`allow_public_server=True` is passed explicitly.

**Why it cannot fold designs.** AF2 **cannot fold complexes without an MSA**: single-sequence mode
gives pLDDT **37**, ipTM **0.11**, and interpenetrating chains at 0.5–0.9 Å. So "cross-validate with
AF2" and "never send an unpublished design to a public server" are in direct conflict unless you host
a local sequence database — and ColabFold's local MSA databases are about **2.2 TB** against 776 GB
free. AF2 therefore stayed a cross-calibration instrument on *published* sequences and never became a
second scorer.

**Second gotcha:** `python -m colabfold.download` **ignores `--data`** and always writes to
`~/.cache/colabfold/params/` (18 files, 5.3 GB). Point `colabfold_batch --data` there rather than
assuming your chosen directory was used.

**The cross-calibration finding, which is a methodological lesson.** Boltz ipSAE 0.841 versus AF2
0.654 on the same complex looked like a PAE scale offset — until DockQ showed AF2's pose was
genuinely worse (0.690 versus 0.820), so part of the gap was *deserved*. **When comparing two
estimators' confidence, first compare their accuracy**, or honest differences get booked as bias. And
at n=1 with two explanations pushing the same direction, the correct verdict is "unresolved", not
"resolved with a caveat".

---

## 4. Scoring

### 4.1 DockQ 2.1.3 — two flags that both default wrong

DockQ compares a predicted complex to an experimental one, returning a 0–1 score with CAPRI classes:
High ≥ 0.80, Medium 0.49–0.80, Acceptable 0.23–0.49, Incorrect below.

- **`--allowed_mismatches` defaults to 0.** DockQ assumes model-versus-experiment of the *same*
  complex, so any substitution reads as "you paired the wrong chains" and it **refuses to score**:
  `ERROR: For chains ['A'] no identical corresponding chain was found`, **exit 1, no output**. Every
  Challenge 1 design is pembrolizumab with mutated CDRs, so at the default *every design the pipeline
  produces* returns `None` → `viable=None` → nothing selectable, with no error anywhere. **Measured:
  four substitutions is already enough to trigger it** — and four substitutions is the *minimum* for
  full novelty marks, so it would have failed on the first design worth having. Config sets 40; the
  shipped documentation records that the true minimum for this design is **15 — exactly its
  substitution count** (one reviewer reported 5; that is wrong).
- **A counter-intuitive asymmetry, recorded:** insertions and deletions are handled fine by the
  alignment; **only substitutions trip the check.** The stress test that found this mutated residue
  *names* while leaving coordinates byte-identical, and inverted the prediction: `del2` and `ins2`
  scored **1.000**, while `sub4` and `sub8` failed entirely.
- **`--mapping ABC:ABC`** pins chain correspondence. Left free, DockQ searches, and a wrong mapping
  "would score a good design badly — discarding a winner for a reason invisible in the output." It is
  not *strictly* required here (DockQ auto-resolves to the same 0.816) but is passed so a different
  input cannot silently be scored under a different correspondence.
- **A reference-structure trap.** In the deposited 5GGS crystal, **chain C is a second copy of the
  antibody heavy chain, not the antigen** — the antigen is chain Z — so the reference is prepared as
  chains A/B/**Z** renamed A/B/C. Worse, the two complex copies are paired *crosswise*: A/B binds Z
  and C/D binds Y. The natural reading of the labels gives an extracted "complex" with **zero**
  antibody–antigen contact, and PRODIGY refused it with `No contacts found`. Worse still, the
  **largest non-antibody interface in that crystal is between the two light chains — 64 residues,
  larger than either real epitope** — pure crystal packing, so a heuristic like "take the biggest
  interface that isn't heavy–light" would have selected a lattice artefact as the binding site.
  Determine pairing by measuring contacts, never by reading labels; and `extract_complex()` **returns
  the mapping it applied**, because once written, the mapping is not recoverable from the file.
- **Aggregation over three interfaces is a convention, not a fact.** On the winner (A–B 0.939,
  A–C 0.755, B–C 0.855): `min` 0.755 (**Medium**), `mean` 0.805, `global` 0.850, `max` 0.855 (all
  **Good**). Three of four readings put the same design a band higher — worth +2.5 final points under
  midpoint. The default is now `global`, DockQ v2's own "Total DockQ", because that is what an
  evaluator gets by running the tool and reading the summary. The caveat travels with it: `global`
  averages in the **heavy–light framework interface at 0.931**, which no design touches and which is
  near-perfect by construction. On the shipped structure the interface the design is actually
  responsible for is **A–C = 0.723**, and the submission documents break it out: A–B 0.931,
  A–C 0.723, B–C 0.794, Total 0.800.

**The flags now ship inside the package.** `metrics/scores.md` and `docs/reproducing_our_numbers.md`
both print the failing default run verbatim and then the working invocation. *Ship the flags your own
tool needs, inside the package* — otherwise an evaluator reproducing your numbers gets exit 1 and no
output, and concludes your files are broken.

### 4.2 PRODIGY 2.4.0 — ΔG and contacts

**Invocation, always explicit:** `prodigy <pdb> --selection A,B C --temperature 25.0`.

**The gotcha.** Run **without** `--selection` on a three-chain file, PRODIGY silently scores a
different interface — on 5GGS it returned a confident **−16.3 kcal/mol** for the **heavy–light**
interface, which is entirely plausible for an antibody–antigen interface and therefore undetectable
by inspection. *"When a tool has to choose something you care about and you didn't specify it, it
chose. Find out what."*

**What it is.** PRODIGY is a linear regression on contact counts. That has a consequence the rubric
ignores: **ΔG and contacts are not independent evidence**, despite occupying two of the six binding
slots.

**Validity findings, which are damning.** In the epitope-knockout test — deleting PD-1's binding face,
527 heavy-atom contacts, against a matched off-interface control — **ΔG and the contact count did not
respond at all**, while ipSAE and interface pLDDT responded at 17× and 64× their own seed sd. And ΔG
carries the largest single share of the ranking's variance. Separately, `contacts` has an intraclass
correlation of **0.003** and `cdr_sasa` of **0.000** against the 239-design pool: pure sampler noise,
carrying no design information. One more withdrawal worth recording: PRODIGY's predicted Kd of 34 pM
against pembrolizumab's measured 29 pM was initially reported as validation and **withdrawn as
validation** — the agreement is well inside the tool's own 1.5–2 kcal/mol error, so it validates the
plumbing, not the accuracy.

### 4.3 ipSAE — interface confidence from the PAE

**What it computes.** An interface-restricted score derived from the **Predicted Aligned Error**
matrix — the predictor's uncertainty about where the chains sit *relative to each other*. It is the
only one of the eight metrics computed from the PAE; the other six read coordinates or sequence.

**Invocation:** `python vendor/ipsae/ipsae.py <pae> <pdb> <pae_cutoff> <dist_cutoff>` with
**pae_cutoff = 10 Å** and **dist_cutoff = 15 Å**, both taken from the repository's documented
examples because the handbook specifies neither. The harness keeps rows with `Type == max` whose
chain pair intersects the antibody chains and contains the antigen, and takes the best.

**The filename-coupling trap, in full.** `ipsae.py` locates the pLDDT array by **string-substituting
the PAE path** — literally `pae_file.replace("pae", "plddt")`. A Boltz PAE must therefore keep its
`pae_<name>_model_<n>.npz` name **and** keep `plddt_<name>_model_<n>.npz` as a sibling in the same
directory. Rename or relocate either — or even use a run label that happens to contain the substring
`pae` — and ipsae **writes an EMPTY table and exits 0**. Three defences ship: the metric checks the
sibling exists before invoking; `fold()` **raises if the label contains `pae` or `plddt`**; and
`fold/__init__.py` returns paths *in place* and never copies or renames them, with the comment
`DO NOT "TIDY" THE OUTPUT`. It also litters `.txt` and `.pml` files beside whatever PDB it is handed,
which is why the validator works on an isolated copy.

**What it is, epistemically.** **A liveness test, not a ranking metric.** Its correlation with
structural correctness was carried by deliberately dead poly-Gly control designs: among live designs
the Fab R² against DockQ collapses **0.755 → 0.263** with the slope flattening 3×, and the *highest*
ipSAE in the panel (0.867) belonged to a variant with DockQ 0.742 against the wild type's 0.820.
Report it, gate at 0.60, never rank on it. *Confidence metrics are liveness tests until proven to be
ranking metrics.*

**A hard-cutoff artefact.** The apparent "bimodality" of the Challenge 2 pool — 15 designs at exactly
0.000 — is an artefact of ipSAE's **hard PAE cutoff**. Those designs carry ipTM 0.556–0.674, an
ordinary continuum. On `bb_10_0_dldesign_0`: 61 heavy-atom contacts, ΔG −9.6, interface pLDDT 75.7,
**ipSAE 0.000 — because not one cross-chain residue pair has PAE below 10 Å (minimum 18.40 Å)**.
Verified genuine rather than the empty-table failure: ipsae wrote a full 14-line table and scored the
heavy–light interface at 0.876.

**A withdrawn discrepancy, worth the space because the lesson is generic.** It was reported that
`ipsae.py` had a code-path difference — the AlphaFold-style JSON route gave 0.8491 while "the npz
path" gave 0.8560. **Withdrawn.** Both routes agree to five decimals per chain pair (A–C 0.823561
versus 0.823574; the residual is 2-decimal-place PAE rounding in the writer). The 0.8560 was an
**8-seed mean** from a results table; seed 1 alone is 0.8491. *A value quoted from a results table is
an aggregate until proven otherwise — read its n.*

### 4.4 NetSolP-1.0 — sequence-only solubility, and a positive control that chose the model

**Architecture.** An ESM-based classifier distributed as **quantized ONNX**, so inference needs no GPU
and no ESM backbone weights — only `onnxruntime` plus `fair-esm` for the tokeniser alphabet. It
therefore runs on **CPU concurrently with GPU folding** and never contends for the fold queue. The
torch in its environment is the **CPU wheel deliberately**.

**Three variants, and they disagree about a licensed drug.** Measured on pembrolizumab against the
0.50 cutoff:

| construct | ESM1b (5-fold) | ESM1b-distilled | ESM12 (5-fold) |
|---|---|---|---|
| VH | **0.733** | 0.637 | 0.379 |
| VL | **0.569** | 0.463 | 0.346 |
| Fab heavy | **0.623** | 0.491 | 0.352 |
| Fab light | **0.626** | 0.448 | 0.312 |

Only the full **ESM1b 5-fold ensemble** clears the cutoff everywhere. The other two **fail a marketed
antibody** — a false negative that would have silently discarded good designs and *would have looked
exactly like a design problem rather than a configuration one.* Hence ESM1b is a recorded convention
carrying its evidence, not a constant buried in code. Cost: **~11 s/sequence over 24 threads versus
~2 s for ESM12**, paid on CPU off the GPU critical path.

**One self-correction to record.** The project initially wrote that "the CLI default would have failed
a marketed drug." That claim was itself **withdrawn**: the CLI default *is* ESM1b, which passes. The
surviving, still-valuable claim is narrower — anything that can move a result across a threshold
belongs in the config file with the evidence attached.

**Construct convention, resolved late.** The handbook says **Fv (VH+VL)** twice; the code fed it full
**Fab** chains until 2026-09-20 — the function parameters were even named `fv_heavy`/`fv_light` and
the callers ignored that. It changes the numbers *and which chain limits*: Fab 0.623/0.626 (heavy
limits) versus Fv 0.733/0.569 (**light** limits). Chain aggregation is `min` — "a design is only as
soluble as its worst chain" — so pembrolizumab scores min(0.733, 0.569) = 0.569.

**And the recommendation that followed was refuted by arithmetic, for zero GPU folds.** "Redesign the
light-chain CDRs, that is where the deficit is" sat in three project documents and was echoed by two
independent reviewers. It is wrong twice. **(1) The ceiling is the other chain**: VH is 0.699 against
a Good edge of 0.70, so `max over all light chains of min(0.699, VL) = 0.699` — the band cannot move,
**by 0.001**. **(2) The sampler cannot do it anyway**: 24 ProteinMPNN light chains at T=0.1 moved VL
from 0.5690 to at best **0.5920 (+0.023) against a required +0.131**, **0/24** reached the edge, and
**24/24 introduced new CDR liabilities.** *Under a `min` aggregator, effort on anything but the
current argmin is wasted, and effort on the argmin is wasted past the point where it stops being the
argmin.* A live documentation inconsistency is worth flagging: `netsolp.py:66-70` still ends with the
refuted recommendation; the results files carry `⚠ CORRECTED 2026-09-22` banners but the module
docstring was never updated.

### 4.5 ANARCII 2.0.8 — IMGT numbering, and the antigen it numbered as an antibody

**What it does.** Assigns IMGT positions to an antibody V domain, so CDR ranges name the same
structural element across antibodies of different loop length. Ranges used: **CDR1 27–38, CDR2 56–65,
CDR3 105–117**.

**The gotcha.** PD-1 is an immunoglobulin-superfamily member with an **[[01-the-biological-problem#2.5 The IgV fold, and the trap it set|IgV fold]]**, so ANARCII
recognises it as antibody-like and happily assigns it CDRs. Measured on 5GGS and 5WT9: true V domains
score **30.8–30.9**; PD-1 scores **15.8–16.2**. A permissive threshold silently classifies the
*antigen* as an antibody chain and every downstream CDR metric is then computed on the wrong
molecule. Mitigation: `MIN_V_DOMAIN_SCORE = 25.0`, documented as "load-bearing, not cosmetic."

**Also used as a germline source:** ANARCI's `germlines.py` (IMGT-gapped, 128-position alignment)
supplies the V and J segments for the Challenge 2 germline database.

### 4.6 The novelty metrics: one metric, two references

**Challenge 1** — CDR-H3 identity to Keytruda's `ARRDYRFDMGFDY`. Identity is computed over a **global
alignment** (Biopython `PairwiseAligner`, match 1 / mismatch 0 / gap open −1 / extend −0.5) with
denominator `max(len(query), len(reference))`, because a designed loop may differ in *length* —
nivolumab's CDR-H3 is 6 residues.

**Challenge 2** — CDR-H3 identity to **human germline**, which does not exist as a single string,
because CDR-H3 *is* the V(D)J junction: `IMGT 105-117 = [V 3'-end][N1][D, any frame, trimmed][N2]
[J 5'-end]`, and the N regions are non-templated with no germline counterpart at all. The database
`data/germline/human_igh.json` holds **249 V**, **76 D** (alleles × 3 forward frames) and **14 J**
entries. Measured composition: IGHV contributes 2–3 residues (`AR` in 173 of 249 human alleles), IGHJ
3 residues (`FDY`, `MDV`, `FDP`, …), IGHD 3–12. D segments are translated in all three forward frames
because D genuinely is read in any frame in vivo.

Two conventions are both reported: `best_segment` (literal, and *bounded low by construction* — a
13-mer against a 3-mer `FDY` can never exceed 3/13, so it is nearly a constant) and `vdj_coverage`
(the biologically faithful one, and primary). The docstring says the important thing:
**"NEITHER IS A NOVELTY TEST"** — a loop can be 0% germline-covered and still be a trivial copy of a
published antibody. It is the metric the handbook names, scored as specified, and no more. The
consequence: **the `<95%` gate is free for Challenge 2**, because roughly 5 of 13 positions are
germline-templated before any D match, so every human antibody scores well under 95%.

One correction: it was claimed the germline metric "cannot separate pembrolizumab from a shuffle of
it". **False and withdrawn** — pembrolizumab at 53.8% is the **maximum of 2000 scrambles** (about
+5.3 sd, p ≈ 1/2000), so the metric discriminates decisively.

A genuine near-miss lives here too: until 2026-09-22 every caller got Keytruda, so **a Challenge 2
design would have been scored against the wrong reference with no error**, producing a plausible
number for the wrong question.

### 4.7 gemmi, freesasa, and the interface definition

**Interface residues** = any residue with a heavy atom within **5.0 Å** of the other side, via
`gemmi.NeighborSearch(model, st.cell, cutoff).populate()`. One implementation is shared by interface
pLDDT, CDR SASA and the epitope-overlap check, "because an off-by-one silently changes the answer."

**CDR SASA** via freesasa 2.2.1, summing `residueAreas()` over CDR residues. **Both states are always
computed** — `cdr_sasa_bound`, `cdr_sasa_unbound` (antigen deleted via a gemmi chain-clone into a
fresh structure) and `cdr_sasa_buried` (the difference) — because the handbook does not say which it
means, and the two **conflict in sign with the contacts metric**: a better-buried interface means more
contacts but *less* bound CDR SASA.

**Interface pLDDT** reads the B-factor column, where AlphaFold and Boltz write pLDDT on a 0–100 scale,
and **refuses to run on anything not declared a prediction**. The reason is the sharpest small trap in
the project: a crystal structure's B-factor column holds thermal displacement in Å², commonly 10–80 —
*numerically indistinguishable from a plausible pLDDT*, and with the opposite sign convention (low
B-factor = well ordered = good; low pLDDT = uncertain = bad). Guarded by a `types.Provenance` enum
whose `Structure.__post_init__` raises if a prediction has no PAE or an experiment has one.

**A gemmi ordering bug invisible on the first test file.** A structure-loading call raised
`RuntimeError: missing entity_type in chain A` because two library calls were in the wrong order:
`setup_entities()` must come *before* `remove_ligands_and_waters()`. It **worked on 5GGS** (which
carries the metadata) and failed only on **5WT9** (which does not). *"A pipeline step that works on
your first test file has been tested once, not validated."*

### 4.8 The sequence-liability scanner

`src/locksmith/metrics/liabilities.py` scans for N-X-S/T glycosylation sequons
(`SEQUON = re.compile(r"(?=(N[^P][ST]))")`), NG/DG deamidation and isomerisation motifs, exposed Met,
pI and net charge, with severity as motif risk class × CDR-versus-framework context.

It exists late and is the project's own counterexample. `BUILD.md:62` specified it in the build plan
and **it was never written** until an independent reviewer found two N-linked glycosylation sequons in
the shipped Challenge 2 design's CDRs, both on antigen-contacting residues. Its docstring records the
lesson: **"A planned check that does not exist is indistinguishable from a check that passed."** The
chemistry and the sixty-fold difference between the two prescribed fixes are in
[[01-the-biological-problem|the biology chapter]].

---

## 5. The numpy 2.0 fault line, and isolation as architecture

| Tool | Requires | Installed numpy |
|---|---|---|
| PRODIGY (`prodigy-prot` 2.4.0) | `numpy >= 2` | 2.4.6 |
| DockQ 2.1.3 | `numpy < 2` | 1.26.4 |
| Boltz-2 2.2.1 | `numpy < 2` | 1.26.4 |
| main project env | `numpy >= 2` | 2.5.3 |

NumPy 2.0 was a breaking release. These are not negotiable pins; they reflect genuine
incompatibilities. **The tools physically cannot share an environment.**

**The answer is `uv tool install` per conflicting tool**, each getting its own environment *plus a CLI
shim on PATH*; `metrics/dockq.py` and `metrics/prodigy.py` shell out and parse stdout (DockQ's parser
uses three compiled regexes). The project is emphatic that this is not a workaround to apologise for:
*"the subprocess boundary is not a workaround to apologise for — it is what lets us pin each tool to
the organisers' likely version independently."* That matters concretely, because the organisers
recompute six of the eight metrics from the submitted files, so **version agreement with them beats
convenience for us.** And the architecture "paid off twice — it was designed for two conflicting tools
and absorbed a third without any change when Boltz turned out to need `numpy < 2` as well."

The layout as planned versus as it exists is worth recording as an honest documentation-drift note.
`BUILD.md` names five environments; on disk there are **four hand-made venvs**
(`~/.venvs/{locksmith, netsolp, colabfold, rfab-cpu}`) **plus three uv-tool environments**
(`~/.local/share/uv/tools/{dockq, prodigy-prot, boltz}`) = **seven Python environments**, not four or
five. The functional grouping BUILD.md describes is correct; the paths are not.

**Everything heavy lives outside the vault, deliberately.** Weights at `~/.boltz` (7.6 GB),
`~/.cache/colabfold/params` (5.3 GB), `~/.local/share/locksmith/netsolp` (4.7 GB) and
`~/.local/share/locksmith/ProteinMPNN`. The reason is the vault's Syncthing topology: it syncs to a
Windows machine that cannot use any of it, relaying through a phone, so **the phone's free space is
the ceiling on the whole vault**. The one bulk blob that did live inside — a 6.05 GB NetSolP source
tarball — was 98% of the vault and had the relay stuck at **0.47% complete needing 6.12 GB**. One
`/.stignore` pattern took the folder to 0.10 GB, **scoped to `vendor/netsolp` and NOT to `vendor/`**,
because `vendor/ipsae/ipsae.py` is shelled out to by the harness and excluding its parent would have
broken the harness on every other device — looking like a missing file rather than a sync decision.

Two more environment traps for the inventory. **`freesasa` needs `Python.h`**: it compiles from C
source and the system Python ships without development headers, which would need root. The fix was to
rebuild on **uv's managed CPython**, which ships headers — *a managed toolchain-provided interpreter
is often a cleaner escape from system-package problems than escalating privileges.* And **ANARCI
requires HMMER**, an external binary that is not in its Python metadata.

---

## 6. The Blackwell saga

This is the best worked example in the project of a single discipline: **verify with arithmetic, not
with introspection.**

### 6.1 The pin and the hardware

RFantibody's own `pyproject.toml` requires Python 3.10 exactly, `torch == 2.3.*` from the **cu118**
index, `cuda-python == 11.8`, `dgl 2.4.0+cu118` from a pinned wheel URL, `e3nn`, and a vendored NVIDIA
`SE3Transformer`. The local GPU is an **RTX 5070 Ti Laptop**, 12,227 MiB VRAM, driver 595.84, compute
capability **(12, 0) = `sm_120` (Blackwell)**, which needs CUDA ≥ 12.8.

### 6.2 SASS versus PTX — the mechanism you need

A CUDA fatbinary carries some mixture of two things:

- **SASS** — machine code for one specific `sm_XY` architecture, backwards-compatible only within a
  major family.
- **PTX** — a *virtual* instruction set, labelled `compute_XY`, which the driver can **JIT-compile at
  load time** into SASS for a GPU newer than the compiler that produced it.

In PyTorch, `torch.cuda.get_arch_list()` prints exactly what a build contains: `sm_90` is SASS,
`compute_90` would be PTX. **If there is no `compute_*` entry, there is no JIT fallback**, and the
driver reports `CUDA error: no kernel image is available for execution on the device`.

### 6.3 The probes

Two **throwaway** probe environments were built *outside* the synced vault and deleted afterwards
(9.8 GB reclaimed). They were tested with **arithmetic**: a 512×512 fp32 matmul checked against numpy
(exercises cuBLAS), a plain elementwise **ReLU** (exercises PyTorch's own kernels), and in probe 2 a
DGL GPU message-pass on a 3-node graph (because DGL's own CUDA kernels, not just torch's, are what the
SE3-Transformer needs).

```
# torch 2.3.1+cu118
is_available: True
arch list   : sm_50 sm_60 sm_70 sm_75 sm_80 sm_86 sm_37 sm_90
PTX entries : NONE
cuBLAS matmul      -> CUDA error: no kernel image is available for execution on the device
elementwise kernel -> CUDA error: no kernel image is available for execution on the device
```

```
# DGL 2.4.0+cu124
torch       : 2.4.0+cu121        <- NOT what was requested
arch list   : sm_50 ... sm_90
PTX entries : NONE
cuBLAS matmul        -> no kernel image is available for execution on the device
dgl GPU message-pass -> no kernel image is available for execution on the device
```

**Three failure modes, named.**

1. **Total, not partial.** Not only cuBLAS — a plain **ReLU** fails. There is no "most of it works,
   avoid matmuls" configuration to salvage.
2. **`is_available()` returns True in both dead environments.** It returns True when a driver and a
   visible device are present; it does *not* check that the installed binaries contain kernels for
   that device. "A plausible-but-wrong result here looks like a green setup check followed by a crash
   hours into a run."
3. **DGL pins `torch==2.4.0` exactly and silently replaced the requested cu124 torch with the generic
   PyPI cu121 build during install.** This is the one that closes the door: the obvious workaround —
   install DGL, then force a newer torch — is unavailable, because the wheel drags a specific torch
   version with it. After any install that touches a framework, print the framework's real version
   *and build tag*.

**DGL's ceiling, checked against the index rather than assumed:**

| index | HTTP |
|---|---|
| `data.dgl.ai/wheels/torch-2.4/cu128` | **403 — does not exist** |
| `data.dgl.ai/wheels/torch-2.4/cu126` | **403 — does not exist** |
| `data.dgl.ai/wheels/torch-2.4/cu124` | 200 |
| `data.dgl.ai/wheels/torch-2.4/cu121` | 200 |

CUDA **12.4** is the ceiling for official DGL; `sm_120` requires **12.8**.

**Why Docker does not help.** *"Containers isolate userspace, not the GPU's instruction set. An image
built against CUDA 11.8 contains 11.8's SASS and libraries; running it on a Blackwell card changes
nothing about which kernels exist."* Separately, this machine cannot run GPU containers at all —
`docker info` lists only the `runc` runtime and `nvidia-container-toolkit` is not installed. Installing
it was declined because it needs sudo *and* would not fix the actual problem.

**Verification that the negative result is a real measurement.** The same two arithmetic tests
**pass** in `~/.venvs/locksmith` (torch 2.11.0+cu128, arch list contains `sm_120`), so the probe
harness is sensitive to the thing it is testing; the error is the specific CUDA missing-kernel
diagnostic rather than a generic import or driver failure; and `get_arch_list()` independently
corroborates the mechanism. "What healthy looks like" for the cloud route was written down *in
advance*: `nvidia-smi` reports a T4/L4/A10, `get_arch_list()` contains that architecture, and both
arithmetic tests pass **before any weights are downloaded**.

**A self-correction inside the result**, which is the most instructive part. The author "asserted the
conclusion before measuring it, and the reasoning was wrong even though the conclusion was right":
the claim that "no PTX JIT path exists from CUDA 11" is **false as a general statement** — PTX
forward-compatibility is exactly the mechanism that would allow it. The measurement showed the
conclusion holds for a **different reason**: these wheels ship no PTX at all. *"A claim about a
mechanism and a claim about an outcome are different claims, and only one of them was cheap to
test."*

The whole feasibility question cost **25–30 minutes and produced no install**, because probing was
chosen over installing: "the full install is ~10 GB, weights included, and would have taken hours to
fail."

### 6.4 The interim CPU route, and the three walls

Before renting, an all-CPU route was built at `~/.venvs/rfab-cpu` (Python 3.10, `rfantibody`
installed `--no-deps` "because its pins are the thing we are routing around") and verified again by
arithmetic: CPU matmul exact versus numpy (max abs err 0.00e+00), ReLU correct (the op that died on
GPU), DGL message-pass returning the expected `[4,1,2,3]`, e3nn tensor product finite, and all four
weight files *checked by loading, not by `ls`*. It hit three walls, all environmental and none
requiring a port: **PyPI's `dgl` 2.1.0 bundles `libgraphbolt_pytorch_<v>.so` for torch 2.0.0–2.2.1
only** against RFantibody's `torch == 2.3.*` pin (resolved by torch 2.2.1+cpu);
**`torchdata == 0.11.0` removed `torchdata.datapipes`** which DGL 2.x imports (pin
`torchdata == 0.7.1`); and **`torch.cuda.nvtx` raises on a CPU-only build**, because NVIDIA's
vendored SE3Transformer does `from torch.cuda.nvtx import range` **unconditionally** at
`basis.py:32` and wraps every layer in it. NVTX is profiler annotation — no computation — so it was
disabled by a runtime null-context shim in `sitecustomize.py` inside the venv's `site-packages`
(an in-process shim cannot reach RFantibody's subprocesses). No vendored file was modified and
nothing was recompiled, so the "no porting" kill criterion held, "but it is a judgment call and is
recorded as one."

**A correction inside that work, and the reusable part is the cause.** The write-up first claimed
*"DGL has never published a torch-2.3 build on any channel."* **False** —
`data.dgl.ai/wheels/torch-2.3/` lists dgl 2.2.0, 2.2.1, 2.3.0, 2.4.0 and 2.5.0. The index had been
read through `grep … | head -8` and the first eight matches were all `dgl-2.2.0`: **truncation read
as the complete answer.**

One subtlety that reads as hygiene and is actually load-bearing: **a CPU-only torch is required, not
merely tidy.** RFdiffusion, ProteinMPNN and RF2 **all branch on `torch.cuda.is_available()`** — the
call that returned True in two dead environments. A CUDA-enabled torch here sends every stage down
the GPU path to die on `sm_120`. The CPU wheel makes `is_available()` False *by construction*.

### 6.5 The resolution

Rent an `sm_86` RTX 3090. **Upstream's own pins install and run untouched. $2.82 for 5.5 hours.** The
entire workaround stack — the torch downgrade, the `torchdata` pin, the NVTX shim — was unnecessary.

**The transferable principle: before porting a pinned stack, price an hour of the hardware it was
pinned for.**

One open thread was recorded rather than dismissed: RFantibody lists **e3nn** alongside DGL, and if
its SE3 layers can run through e3nn with DGL confined to CPU graph bookkeeping, the wall might be
thinner than measured. Untested.

### 6.6 The preflight that encodes all of it

`scripts/00_doctor.py` exits 0 only if every required check passes: Python is 3.12.x; running inside
the project venv; `torch >= 2.7` built against cu128+; `cuda.is_available()`; **`sm_120` in
`get_arch_list()`**; **PTX fallback present** (reported, not required, "because its absence is what
makes an otherwise-plausible older stack unusable"); device visible with name, VRAM and `sm_XY`; **a
real 4096² fp32 matmul matched against the CPU with `max abs err < 1e-2`** ("`is_available()` and
`arch_list` can both be true on a build that then produces garbage or throws at kernel launch time");
a bf16 matmul (optional); RAM ≥ 8 GiB available; **swap ≥ 16 GiB**; disk ≥ 50 GiB; `DockQ` and
`prodigy` on PATH; `vendor/ipsae/ipsae.py` present; `anarcii` and `freesasa` importable; and the four
reference PDBs present.

---

## 7. Cloud infrastructure and data integrity

The Challenge 2 generation ran on a RunPod RTX 3090 at about $0.50/hour. Three lessons came back with
the artefacts, and all three are about *transfers*, not about GPUs.

**Verify what a "start without a GPU" fallback actually gives you.** RunPod's "Start Pod using CPUs"
mode provisioned **vCPU 0, Memory 0 GB**, and the Jupyter server was OOM-killed while serving a
recursive directory walk — which is why the first checksum pass 502'd after about 130 of 256 files.
*"A provider's 'start without a GPU' fallback is not the same machine minus the GPU."*

**Authentication forms are not interchangeable.** After a pod restart the Jupyter token must be passed
as a **query parameter**: `?token=<t>` returns 200, while the `Authorization: token <t>` header form
returns **403 with the same valid token**. A 403 reads as "credential expired" and sends you looking
in entirely the wrong place.

**Checksum every transfer you did not stream, and length is not the check.** Typing 11,096 base64
characters into a browser terminal delivered **11,092** — four characters lost, detected only because
the md5 disagreed (`cbe1fd8d…` versus `2fe94432…`). A separate 20 KB heredoc paste truncated
*mid-word* and left the shell waiting inside the heredoc. A JupyterLab file upload transferred the
same bytes exactly. **Prefer one HTTP POST over paste or keystroke simulation above about 1 KB, and
compare hashes, not lengths.**

The eventual pass was **258/258 files verified, 0 mismatched, 0 unreachable**, with hashes computed
**server-side** by the Jupyter contents API so they are genuinely independent of the local copy, and a
manifest written incrementally with an `fsync` per record so a crash cannot lose the work already
done. Details and the exit criteria are in
[[02-the-engineering-problem|the reproducibility section of the engineering chapter]].

One cost lesson: the pod was left idle for about 2.5 hours (≈ $1.25) and, worse, was **stopped without
retrieving 443 MB of artefacts**, which left every Challenge 2 headline number temporarily
unfalsifiable prose. Retrieval then became its own multi-day sub-project.

---

## 8. Local workflow

### 8.1 The overnight-job pattern

```
nohup setsid systemd-inhibit --what=sleep:idle:handle-lid-switch --why="<reason>" \
      <cmd> > job.log 2>&1 &
```

`setsid` detaches from the terminal so closing a shell cannot kill the job; `systemd-inhibit` blocks
suspend (verify with `systemd-inhibit --list`).

`scripts/run_m3_overnight.sh` shows the discipline concretely:

- **Fold first, score second** — "if the night is cut short, folds are what cannot be recreated
  cheaply, and scoring is 19 s/fold that can run any time afterwards."
- **`set -e` is deliberately NOT used** (only `set -u`): "a non-zero scorer must not discard the
  folding that already succeeded."
- The script prints `nvidia-smi` memory and `free -g` at start, timestamps every stage with `date -Is`,
  records each stage's exit code, and finishes by counting lines in the jsonl stores.
- All orchestration shells **strictly serialise GPU work**, because "two Boltz processes on a 12 GB
  card is a CUDA OOM that exits 0 and looks like a completed fold."
- A second-stage script is launched separately rather than appended, because **bash reads a script
  incrementally from disk** — editing a running script corrupts it. The companion rule: **never edit a
  script a running batch shells out to.**

### 8.2 Resumability by construction

Every expensive call is keyed by `hash(sequence, predictor, params)`, and anything already on disk is
skipped. Every completed fold is appended to `index.jsonl` the moment it lands, so a suspend, an OOM
kill or a Ctrl-C costs at most the fold in flight. The predicate is
`fold_is_complete(pred_dir, label, n_models=...)`, and it keys on **artefacts** — because
`boltz predict` exits 0 after fatal errors, so completion cannot be judged on exit status. The
enumeration `assert_artefacts` rejects: missing PDB / PAE / pLDDT, a 0-byte PDB, a PDB with no `ATOM`
records, a truncated `.npz` that exists but fails at read time, a non-square PAE, and a missing pLDDT
sibling. **Existence is not enough.**

### 8.3 Shuffled fold order — a statistics decision disguised as scheduling

The 239-design pool is built arm by arm, so the natural order folds all of T=0.1, then all of T=0.2,
and so on. Any run that did not reach the end would then yield a pool with the low-temperature arms
complete and the high-temperature arm **missing entirely** — which does not merely shrink n, it
*destroys the temperature comparison the arm exists to make*. Shuffling with `random.Random(0)` makes
**any prefix of the run a balanced random sample across all four arms**, so a partial night is still
analysable and an interruption costs precision rather than the experiment. The seed is fixed so a
restart continues the same shuffled sequence rather than re-randomising into a fresh bias.

The complementary decision from the same document: **fold everything, unfiltered** (~30 extra folds,
about 23 minutes), because "folding only the survivors makes [the filter question] unanswerable — you
can never see what you discarded, so any cost claim is circular."

### 8.4 The `pgrep -f` self-match, six times, 4 h 22 m of idle GPU

| # | where | cost |
|---|---|---|
| 1–2 | `pgrep -f 'bolt[z]'` — the bracket trick was undermined by writing the plain word in an `echo` **in the same command**, so the shell's own command line matched. Killed my own shell, **exit 144**, twice. | — |
| 3 | A SKEMPI chain waited on `pgrep -f "scripts/run_validity\.sh"`; the pattern could not match the `pgrep` itself but **matched a stale shell's argv**. "The guard was against the wrong object: not the filename, the argv." | **2 h 39 m** |
| 4 | Noted at `scripts/63_gate0b_chain.sh:5` — "self-matched a 4th time on 2026-09-21" | — |
| 5 | `while pgrep -f "65_rfdiff_cpu"; do sleep 20; done` matched a stale harness shell whose argv still contained the string, because the launcher had been created by a **heredoc inside `bash -c`**. The backbone exited at 09:58:38; the loop waited on a ghost until 11:23. Exit 144. | **1 h 22 m** |
| 6 | `while pgrep -f "[7]3_challenge2_score.py"` — the **heredoc that created the script** was still the command line of a live parent shell, so the bracketed literal matched from another process's cmdline. | **21 min** |

**Total measured idle ≈ 4 h 22 m**, on a project whose entire GPU budget was about 45 hours — roughly
10% of the budget spent waiting on ghosts.

The fix, now written into three separate files: **"A file on disk is the signal."** Gate long jobs on
a sentinel artefact, never on a process table — which is also why the checksum watcher polls
`CHECKSUMS.DONE` and why the checksum manifest is written incrementally. A related trap in the same
family: **`setsid` detaches, so `$!` returns a parent that exits immediately** — waiting on it returns
instantly and *falsely reports completion*.

### 8.5 Memory, swap, and CPU contention

The machine has 24 CPU cores and **15 GiB usable RAM**, of which roughly 9.3 GB was routinely held by
desktop applications. The operating rule for batch nights: close the chat apps, run from a TTY, grow
swap.

**Swap: additive beats mutative.** Resizing the existing 8 GB swapfile requires `swapoff`, which
**faults every swapped-out page back into RAM one at a time** — 3.2 GB took minutes and looked exactly
like a hang; interrupting it left swap enabled but unresized. The real fix is to add a second
swapfile: `fallocate -l 16G /swap2.img && chmod 600 && mkswap && swapon`, about **five seconds**,
because `fallocate` on ext4 reserves extents without writing. Total 24 GB, with `vm.swappiness=10` so
swap is emergency overflow rather than routine paging. Swap here is *insurance against the OOM killer
terminating a six-hour batch*, not performance.

**CPU contention is real and `nice` does not fix it.** NetSolP sets
`intra_op_num_threads = os.cpu_count()` and ran at 395–1568% CPU, stalling GPU-bound folds **3.5×**
(307 s against 86–97 s once contending applications were closed). `nice` does not help because the
thread count is fixed at process start.

**And "out of memory" is at least two different problems on a GPU machine, with different fixes.** The
project's first fold took four attempts: a **host-RAM** kill (15 GiB machine, ~9 GB held by desktop
apps, Boltz loading ~4 GB of weights, plus three concurrent decompressions of a 6 GB archive); a
`ModuleNotFoundError: cuequivariance_torch` **exiting 0** (fixed by `--no_kernels`); a **GPU VRAM**
OOM printing `OOM on device 0 … 1616904192 bytes; free 882376704, total 12346195968` and
`Number of failed examples: 1` **under a 100% progress bar**, also **exiting 0** (fixed by dropping
the antibody MSAs — correct protocol *and* a two-thirds VRAM cut); and then success in **34 s**. All
the swap work had addressed the wrong one of the two memory resources.
*"Three of the four failures reported success or said nothing useful"* — which is what turned "check
the artefacts, not the exit code" from a nice principle into a hard rule. See
[[02-the-engineering-problem|the full catalogue of exit-0 failures]].

---

## 9. Costs and timings

All measured, with the conditions attached, because most of these numbers move by 1.5× depending on
machine load.

| Quantity | Measured value | Conditions |
|---|---|---|
| **Boltz Fab fold, per invocation** | **126 s** | one design, one seed, cached 3,787-sequence MSA |
| Boltz Fv fold, per invocation | 92 s (median 104, range 42–143) | 1.6× fewer residues, yet only 27% faster — the fixed per-call cost dominates |
| Boltz fold, M3 arm in practice | **median 84 s** (239 folds in **6.0 h**) | quiet machine |
| Boltz fold, contended machine | 133–150 s | desktop apps running |
| Boltz fold, best case ever recorded | 34 s | the first successful fold; this is the *fold*, not the *invocation* |
| Batched folding | 72 s/fold at batch 6 (434 s total) = **1.16×** | fixed ≈14 s/invocation + marginal ≈70 s/fold |
| 5 diffusion samples vs 1 | **2 m 54 s vs ~2 m** | MSA, trunk and recycling are shared |
| Scoring, per fold | 19 s | 6 parallel workers, CPU |
| NetSolP, per sequence | ~11 s (ESM1b) vs ~2 s (ESM12) | 24 CPU threads, off the GPU critical path |
| ProteinMPNN, 4 sequences from one backbone | **2 s** | 24 CPU cores — negligible |
| RFdiffusion on CPU, per diffusion step | **23.37 s** (median 23.47, sd 0.53 = 2.3% of mean) | 24 cores, `OMP_NUM_THREADS=24`, load average 10.85 — effective parallelism ≈11, not 24 |
| RFdiffusion on CPU, per backbone | ≈19.5 min (50 steps) + ~4 min one-off model load | |
| RF2 on CPU, per design | **7.1 min** (4 designs in 28 m 23 s) | a projection of "~4 min/sequence" was **1.75× optimistic** and moved a 20-backbone estimate 12 h → 16 h |
| Full local CPU pipeline, per backbone | ≈48 min (19.5 diffusion + 0.03 MPNN + 28.4 RF2) | 20 backbones ⇒ ~16 h |
| **Rented RTX 3090 (RunPod, `sm_86`)** | **$2.82 for 5.5 h** at ~$0.50/h | 18 conditioned + 18 unconditioned backbones, 30 sequences, 30 RF2 predictions, **zero failures** |
| Idle pod billing | ≈ $1.25 for ~2.5 h | avoidable, and avoided thereafter |
| Blackwell feasibility probe | **25–30 min**, no install | versus a ~10 GB install that would have taken hours to fail |
| **Total GPU budget** | ~**45 GPU-hours** = 162,000 s (5 batch nights × ~9 h) | |
| Fold budget at the planning figure (34 s) | ~4,700 folds | **wrong** — 34 s was the fold, not the invocation |
| Fold budget at the measured figure (126 s) | **~1,290 folds** | a 3.6× collapse caused by omitting a per-call constant from the model |
| GPU time lost to `pgrep -f` self-matching | **≈4 h 22 m** | ~10% of the whole budget |
| Model PDBs produced | **1,274** across 42 run directories, **3.6 GB** | `diffusion_samples=5` writes 5 models per invocation, so this over-counts distinct folds |

The single most useful line in that table is the third pair. **The budget collapsed by 3.6× because a
per-call constant had been omitted from the model** — the plan costed the *fold* and the reality
charged for the *invocation*. Batching was the obvious remedy and returned 1.16×, not the projected
1.8×. *Measure a deferred optimisation's projected payoff before letting the projection justify a
schedule.*

---

## What to take away

1. **A tool's defaults encode its author's assumed use case, not yours.** DockQ's mismatch policy
   refuses every design you will ever produce; PRODIGY silently picks an interface; ColabFold uploads
   your unpublished sequence; NetSolP ships three models that disagree about a licensed drug; Boltz
   returns an argmax and calls it a sample. Read every default of every tool before trusting it, and
   run your positive control through the tool before you trust its verdict.
2. **Verify with arithmetic, never with introspection.** `torch.cuda.is_available()` returned **True**
   in two environments where a plain ReLU failed. `get_arch_list()` told you why — `PTX entries:
   NONE` — and a 4096² matmul checked against the CPU tells you whether it actually works.
3. **Isolation is architecture, not a workaround.** The numpy 2.0 split forced `uv tool install` per
   tool with subprocess boundaries; that same design independently bought version-pinning against
   whatever the grader runs, and absorbed a third conflicting tool without a change.
4. **Before porting a pinned stack, price an hour of the hardware it was pinned for.** $2.82 deleted a
   workaround stack that had already cost days.
5. **Gate long jobs on artefacts, never on process tables.** `pgrep -f` self-matches in at least six
   distinct ways, including from the heredoc that wrote your script. A file on disk is the signal.
6. **Checksum every transfer you did not stream, and compare hashes rather than lengths.** 11,092 of
   11,096 characters arrived; only the md5 noticed.
7. **Additive beats mutative** — add a second swapfile in five seconds rather than `swapoff`-resizing
   for minutes.
8. **Measure the deferred optimisation before its projection justifies a schedule.** 1.8× projected,
   1.16× measured, on a number that had been load-bearing in scheduling arguments for two days.

Next: [[04-measurement-theory|how reliability, attenuation and range restriction were measured]], and
[[08-what-broke|the full catalogue of what went wrong and what it cost]].
