---
date: 2026-09-16
tags: [project, protein-design, structure-prediction, problem, learning]
status: living
---

Tags: [[Protein Design|protein design]] · [[Structure Prediction|structure prediction]] · [[Problem|debugging]] · [[Learning|things I'm learning]]

# The first real prediction, and the four attempts it took

**Session:** 2026-09-15 evening → 2026-09-16 early. **Gates closed:** G1a, G1b, G1e (DockQ half).
**Prerequisite:** [the environment and scoring-harness doc](2026-09-15-environment-and-imgt-numbering-foundations.md). This doc restates what it needs and links rather than repeating.

---

## 1. What this session had to answer

The project's deepest scientific risk, stated as a question: **can a structure-prediction model
recover a known antibody–antigen binding pose when it is not shown the answer?**

Challenge 1 does not depend on this — it hands us the reference structure as a template.
Challenge 2 entirely does: there is no template, and nothing to compare against. If the model
cannot rediscover a structure that already exists, it certainly cannot validate one that never
has.

The test: give the model nothing but the amino-acid sequences of pembrolizumab and PD-1, and
compare its prediction to the crystal structure (PDB 5GGS).

## 2. The configuration that worked — exact, reproducible

```
boltz predict data/fold_inputs/5ggs_fv_singleseq.fasta \
  --out_dir runs/fold/5ggs_fv_ss \
  --output_format pdb --write_full_pae --use_msa_server \
  --diffusion_samples 1 --recycling_steps 3 --seed 1 \
  --accelerator gpu --num_workers 0 --no_kernels --max_msa_seqs 1024
```

Input, in Boltz FASTA form (`>CHAIN|entity|msa`; the literal token `empty` means *no alignment
for this chain*):

```
>A|protein|empty     VH, 119 aa
>B|protein|empty     VL, 111 aa
>C|protein|          PD-1, 113 aa   (alignment fetched from the ColabFold server)
```

343 residues total. **Wall clock: 34 seconds** on an RTX 5070 Ti Laptop (Blackwell, `sm_120`,
11.5 GiB usable VRAM), on the *pure-PyTorch* path with the optimised CUDA kernels disabled.

Three flags are load-bearing and each was learned the hard way — see §4.

## 3. The result

| metric | value | band | reference |
|---|---|---|---|
| **DockQ** vs crystal | **0.820** | good (≥0.80) | 0.867 between two crystal copies |
| **ipSAE** | **0.841** | good (≥0.80) | undefined on crystals |
| **interface pLDDT** | **94.4** | good (>80) | undefined on crystals |
| ΔG | −12.8 kcal/mol | good (≤−12) | −14.3 on the crystal |
| interface contacts | 106 | good (>25) | 102 |
| CDR SASA | 1444 Å² | good (>600) | 1564 |
| CDR-H3 identity | 100% | **fails, correctly** | it *is* pembrolizumab |

Per-interface DockQ: heavy–antigen **0.838**, light–antigen **0.820**, both CAPRI *High quality*.
iRMSD ≈ 1.1 Å, fnat 0.86–0.88 — interface atoms land about one ångström from their
crystallographic positions and ~87% of the real contacts are reproduced.

**The prediction recovers the pose about as well as a second copy of the real crystal does.**

### 3.1 What this does NOT establish — read before quoting the number

**5GGS was published in 2017 and is almost certainly in Boltz-2's training data.** This is
therefore partly *retrieval*, not clean prediction. The model may be recalling a structure it has
seen rather than deriving one.

- **Established:** the pipeline works end to end (fold → PAE → ipSAE → score), and the harness
  produces sensible numbers on a *predicted* structure, which it had never done before.
- **Not established:** that the model can place a never-before-seen antibody onto PD-1 — exactly
  what Challenge 2 requires.

The honest test is a complex released **after** the model's training cutoff. **Not yet run.**
Until it is, Challenge 2 confidence is discounted and independent evidence (cross-predictor
consensus, specificity controls) carries proportionally more weight.

A plausible-but-wrong version of this result would look identical on every number here. That is
the point of [the confidence-is-not-truth argument](../../knowledge/Confidence%20Is%20Not%20Truth.md).

## 4. The four attempts, and what each cost

Getting one prediction took four runs failing for four unrelated reasons. Three of the four
**reported success or said nothing useful.**

| # | Symptom | Real cause | Exit code |
|---|---|---|---|
| 1 | killed mid-run | **host RAM** exhausted | killed |
| 2 | traceback, no output | `cuequivariance_torch` missing | **0** |
| 3 | `100%` bar, no output | **GPU VRAM** exhausted | **0** |
| 4 | — | worked | 0 |

### 4.1 Attempt 1 — host RAM, and my own contribution

15 GiB total, ~9 GB held by a browser and chat apps, Boltz loading ~4 GB of weights. I made it
worse by running three separate `tar tzf` passes over a 6 GB archive at the same time — each
streams the whole file. Avoidable, and entirely mine.

Cached and therefore not repeated: the model weights (`boltz2_conf.ckpt` 2.29 GB,
`boltz2_aff.ckpt` 2.06 GB) and the sequence alignments.

### 4.2 Attempt 2 — an optional kernel that was not optional

`ModuleNotFoundError: No module named 'cuequivariance_torch'`, **exit 0**.

Boltz ships optional CUDA kernels for the triangular multiplicative update, an expensive
Evoformer operation. I had deliberately skipped `boltz[cuda]`, reasoning the kernels might lack
Blackwell support and fail more obscurely. Boltz imported them anyway rather than falling back.

**Fix:** `--no_kernels`. Cost: the slower pure-PyTorch path — which still gives 34 s, so chasing
the kernels on a brand-new architecture is not currently worth the compatibility risk.

### 4.3 Attempt 3 — the wrong kind of memory

```
OOM on device 0 while trying to allocate 1616904192 bytes
free: 882376704, total: 12346195968
| WARNING: ran out of memory, skipping batch
Number of failed examples: 1
```

**GPU VRAM**, not host RAM. I had been treating "out of memory" as one problem; it is two, with
different fixes, and all the swap work addressed only the host side.

**The fix was the scientifically correct protocol.** An MSA (multiple sequence alignment) is a
stack of evolutionarily related sequences; folding models use it because positions that touch in
3D co-vary across species. Memory scales with alignment depth × length, and Boltz was building
deep alignments for **all three chains**.

But **a drug and its target have not co-evolved** — there is no evolutionary record of
pembrolizumab binding PD-1. A paired antibody–antigen alignment therefore contains no interface
signal. It is why IgFold and ABodyBuilder2 work from single sequences. Setting the antibody
chains to `empty` was simultaneously correct and roughly a two-thirds cut in the memory that was
blowing up.

*When the right thing and the cheap thing coincide, the right thing was usually right for a
structural reason.*

### 4.4 The invariant this produced

**Exit code is not a success signal.** Two of the three failures returned 0. A resumable batch
keyed on exit status would mark them complete and skip them forever, leaving silent holes that
surface much later as *"why do I have 200 designs and 40 scores?"*

> A fold counts as successful only when the expected `*_model_0.pdb` **and** the PAE file both
> exist and parse. Never when the process merely returned.

Recorded in `BUILD.md` §8. Same family as the mislabelled-telemetry incident in `LEARNINGS.md`,
one level nastier: there a subprocess died and the parent carried on; here the subprocess
*claims* it succeeded.

## 5. ipSAE's filename coupling

Scoring then failed with an empty results table and no error. Cause, from the vendored script:

```python
plddt_file_path = pae_file_path.replace("pae", "plddt")
```

ipSAE locates the per-residue confidence array by **string-substituting the PAE filename**. We
had copied the outputs to a working directory under new names; the sibling was unfindable, so it
wrote a **zero-byte** table and exited cleanly.

**Invariant:** a Boltz PAE must keep its `pae_<name>_model_<n>.npz` name *and* keep
`plddt_<name>_model_<n>.npz` beside it. `metrics/ipsae.py` now checks for the sibling and returns
a descriptive skip, and treats an empty table as an error with stderr attached.

Caught only because our parser was strict enough to crash on an empty file. A more forgiving
parser would have produced a missing value with no explanation.

## 6. Calibration points worth carrying forward

- **A correct pose scores ipSAE 0.841.** The good band starts at 0.80, so a genuinely correct
  interface sits only *just* inside it. **ipSAE much above 0.85 on a designed molecule warrants
  suspicion, not celebration.**
- **Boltz's own summary reported iptm 0.948 where ipSAE read 0.841** on the same structure.
  Different scales measuring related things; not interchangeable. The competition's thresholds
  were calibrated on AlphaFold's PAE, so Boltz-derived ipSAE remains **provisional** until the
  two are compared on one structure (gate G1d, not yet run).
- **Predicted ΔG −12.8 vs crystal −14.3** on the *same molecule* — a 1.5 kcal/mol gap, inside
  PRODIGY's stated RMSE. Concrete demonstration that ΔG is **ordinal**, useful for ranking and
  for the ≤−6 gate, not for quoting an affinity.
- **The heavy–light interface scored worst** (DockQ 0.791) despite the *lowest* positional error
  (iRMSD 0.251 Å). Geometrically right, different contact set — the under-constrained Fv elbow,
  appearing in real data before we went looking. Supports
  [the Fv-screen/Fab-confirm protocol](../../knowledge/Screening%20on%20Fv%20Confirming%20on%20Fab.md).

## 7. Compute budget, revised

34 s per Fv fold against ~45 GPU-hours ≈ **4,700 folds**, versus the 1,400–1,800 the plan
budgeted. The funnel can be several times wider than designed. Measured on the slow path, so this
is a floor.

## 8. Also this session: the documentation pass

Thirteen teaching notes plus a narrative spine, written for a reader new to structural biology —
see [the knowledge index](../../knowledge/README.md) and
[the project story](../../PROJECT-STORY.md). Frontmatter retrofitted to match
`.claude/rules/vault-notes.md` (date / tags / status, two-axis tags, named links only).

One mechanical lesson worth keeping: **17 wikilinks were broken by line-wrapping.** Hard-wrapping
prose at 100 characters split `[[Note Name|alias]]` across a newline, which Obsidian does not
resolve — they render as plain text with no error. Repaired with a regex joining any wikilink
containing a newline. A hazard specific to writing wrapped Markdown with wikilinks.

## 9. What is stubbed or unproven

- **NetSolP is downloaded (6.05 GB) but not installed.** Until it runs, the harness reports
  viability as `None`, never `True` — it refuses to assert a design passes all eight gates having
  measured seven.
- **G1c (Fv↔Fab rank correlation) not run.** The screening protocol's core assumption is untested.
- **G1d (Boltz vs AlphaFold ipSAE offset) not run.** Boltz ipSAE values remain provisional.
- **The post-training-cutoff test is not run.** §3.1.
- No designs generated. No baselines. The funnel does not exist.
