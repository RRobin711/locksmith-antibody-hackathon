---
date: 2026-09-16
tags: [project, protein-design, structure-prediction, problem, learning]
status: living
---

Tags: [[Protein Design|protein design]] · [[Structure Prediction|structure prediction]] · [[Problem|debugging]] · [[Learning|things I'm learning]]

# Installing the last two M1 dependencies, and the control that changed the answer

**Session:** 2026-09-16 afternoon. **Closed:** the NetSolP half of G1e. **Advanced but
did not close:** G1d. **Retired:** the JAX-on-Blackwell risk.
**Prerequisite:** [[2026-09-16-first-prediction-and-the-four-attempt-fold|the first-prediction doc]]
for the Boltz-2 baseline numbers this session compares against. Everything needed
is restated below.

---

## 1. What this session had to do

Milestone M1 ("predictor qualification") had three open items, two of which were
pure installs that had been deferred:

1. **NetSolP** — the eighth and last metric. Until it runs, the harness reports
   developability as `None`, so `viable` can never return `True` and *no design can
   be certified as gate-clearing*. It blocks M2 onward mechanically.
2. **ColabFold / AlphaFold2** — needed for **Gate 1d**, the cross-calibration that
   decides whether the rubric's AF2-derived ipSAE thresholds may be applied to
   Boltz-2 output.

Both are installed and verified. The second produced a result whose first reading
was wrong, and the section on why is the part of this document worth keeping.

---

## 2. NetSolP

### 2.1 What it actually is

NetSolP-1.0 (DTU) predicts, from sequence alone, whether a protein will be
**soluble when expressed recombinantly in *E. coli***. That target matters and is
returned to in §2.4. Architecture: an ESM protein language model produces a
per-residue embedding; a small classifier head pools it to one logit; a sigmoid
maps that to [0, 1].

The distribution ships **quantized ONNX** exports of the whole stack, backbone
included. Three consequences, all good:

- No PyTorch model weights and no ESM checkpoint download are needed.
- Inference is **CPU-only** via `onnxruntime`, so it runs *concurrently with GPU
  folding* and never contends for the fold queue.
- `torch` is still required, but only for `torch.utils.data.DataLoader` and the
  tokeniser in `data.py`, so the **CPU wheel** suffices. This is why the env below
  does not pull the 3 GB CUDA build.

`fair-esm` is required for an unobvious reason: the tokeniser alphabet ships as a
**pickle of an `esm.data.Alphabet` instance**, so the class must be importable for
`pickle.load` to reconstruct it. Nothing else in the package is used.

### 2.2 The install, exactly

The tarball `netsolp-1.0.ALL.tar.gz` (6,050,225,681 bytes) was already downloaded
to `vendor/netsolp/`. It contains 22 ONNX models — two prediction heads
(Solubility, Usability) × two backbones × 5 cross-validation folds, plus two
distilled singles. Only a subset is needed, so it is extracted selectively:

```
~/.local/share/locksmith/netsolp/    predict.py, data.py, models/*.onnx   4.7 GB
~/.venvs/netsolp/                    onnxruntime, fair-esm, torch-CPU, pandas, numpy 2
```

```bash
uv venv ~/.venvs/netsolp --python 3.12
uv pip install --python ~/.venvs/netsolp/bin/python \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  torch onnxruntime numpy pandas fair-esm
```

Resolved versions: `torch 2.14.0+cpu`, `onnxruntime 1.30.0`, `numpy 2.5.2`,
`pandas 3.0.5`, `fair-esm 2.0.0`. A 2021 codebase running unmodified under numpy 2
and pandas 3 was not a given; it works because `predict.py` touches only
`DataFrame`, `merge` and `to_csv`.

**Both paths are outside the vault, deliberately.** The vault syncs to the Windows
machine, where 4.7 GB of Linux-built ONNX and a Linux venv are pure cost. Override
with `NETSOLP_DIR` / `NETSOLP_PYTHON`.

### 2.3 The discovery: the positive control failed

The harness's central calibration idea is that **pembrolizumab — a licensed drug —
must pass every binding and developability gate and fail only novelty.** It is the
positive control. So the first thing run through NetSolP was pembrolizumab.

It failed. Solubility 0.379 (VH) and 0.346 (VL) against a hard cutoff of **0.50**.

A marketed antibody scoring as insoluble is not a result, it is a symptom. Two
unspecified choices turned out to control the verdict:

**Choice 1 — which of the three predictors.** `--MODEL_TYPE` accepts `ESM12`
(5-fold ensemble on the small ESM-1 12-layer backbone), `ESM1b` (5-fold ensemble on
the large ESM-1b backbone) and `Distilled` (a single distillation of ESM1b). The
README notes only that "ESM1b is better but much slower".

**Choice 2 — what sequence to submit.** A design is two chains. Does one score VH
and VL separately? Concatenated? As an scFv with a `(G4S)3` linker? As full Fab
chains?

Measured, all combinations, pembrolizumab, cutoff 0.50:

| input | ESM1b (5-fold) | ESM1b distilled | ESM12 (5-fold) |
|---|---|---|---|
| VH | **0.733** | 0.637 | 0.379 |
| VL | **0.569** | 0.463 ✗ | 0.346 ✗ |
| VH+VL concatenated | **0.686** | 0.551 | 0.340 ✗ |
| scFv VH-(G4S)3-VL | **0.678** | 0.558 | 0.371 ✗ |
| scFv VL-(G4S)3-VH | **0.705** | 0.584 | 0.358 ✗ |
| Fab heavy | **0.623** | 0.491 ✗ | 0.352 ✗ |
| Fab light | **0.626** | 0.448 ✗ | 0.312 ✗ |
| Fab H+L concatenated | **0.623** | 0.465 ✗ | 0.353 ✗ |

The full **ESM1b 5-fold ensemble passes under every convention** (0.569–0.733). The
other two fail a licensed drug under most of them. That is decisive, and it is why
`netsolp_model_type: ESM1b` is now a recorded convention in `config/metrics.yaml`
rather than a default left wherever the CLI happened to point.

The cost of being right: **~11 s/sequence** for ESM1b across 24 threads versus ~2 s
for ESM12. Paid on CPU alongside GPU folding, so it is off the critical path.

**Aggregation across the two chains** is set to `min`, on the argument that a
design is only as soluble as its worst chain. For pembrolizumab that gives
min(0.733, 0.569) = **0.569** — passes the 0.50 cutoff, lands in the *medium* band
(good starts at 0.70). Recorded as `netsolp_chain_agg`, because it is a judgement
and not a fact.

### 2.4 What is genuinely shaky here, stated plainly

**NetSolP predicts E. coli expression solubility. Therapeutic antibodies are not
made in E. coli** — they are made in mammalian cells (CHO), precisely because
antibody domains need disulfide bonds and glycosylation machinery that E. coli
lacks. Antibody variable domains are *famous* for going into inclusion bodies.

So it is entirely possible that the ESM12 number (0.35, "insoluble") is the
*honest* answer to the question NetSolP was trained to answer, and that pembrolizumab
passes on ESM1b for reasons unrelated to being a good drug. The rubric names
NetSolP, so NetSolP is what we report — but the metric is a weak proxy for
antibody developability, and the ESM1b choice above is justified by *"the positive
control must pass"*, not by evidence that ESM1b models antibodies better.

This is an argument from calibration, not from biology. It is the right call for
reproducing the rubric and it should not be oversold as anything more.

A second caution: a poly-glutamine 50-mer, run as a sanity control, scored **0.749**
— *more soluble* than pembrolizumab's VH. PolyQ is the textbook aggregation motif.
It is also nothing like NetSolP's training distribution, so this is out-of-domain
behaviour rather than a demonstrated bug, but it is a concrete reminder that the
number is a classifier output and not a measurement.

### 2.5 The module

`src/locksmith/metrics/netsolp.py` replaces the stub. It shells out to `predict.py`
in the NetSolP env, then **asserts on the artefact**: the CSV must exist, contain a
row per submitted sequence, and carry a parseable float. The exit code is never
consulted, per the invariant this project earned the hard way when `boltz predict`
exited 0 after a fatal CUDA OOM.

Verified through the harness itself:

```
value   = 0.569
detail  = ESM1b min(H=0.733, L=0.569)
passes cutoff 0.5 = True   band = medium
```

**The NetSolP half of G1e is closed. `viable` can now return `True`.**

---

## 3. ColabFold, and a risk that turned out not to be one

### 3.1 JAX on Blackwell

PLAN §15.2 made Boltz-2 the primary predictor partly because "JAX-on-Blackwell is
unproven" — AlphaFold runs on JAX, and this machine's RTX 5070 Ti Laptop GPU is
Blackwell (`sm_120`), which needs CUDA ≥ 12.8. The same constraint already forced a
cu128 pin for PyTorch.

Installed without conda, matching this project's isolated-venv pattern:

```bash
uv venv ~/.venvs/colabfold --python 3.11
uv pip install --python ~/.venvs/colabfold/bin/python "colabfold[alphafold]" "jax[cuda12]"
```

Resolved: `colabfold 1.6.3`, `alphafold-colabfold 2.3.20`, `jax/jaxlib 0.10.2`,
`dm-haiku 0.0.17`. Weights: `python -m colabfold.download`, 18 parameter files,
5.3 GB, landing in `~/.cache/colabfold/params/` — note that it **ignores `--data`**
for the download location.

Verified the way this project insists on: **a real matmul, not `is_available()`**,
because Blackwell wheels install cleanly and then fail at kernel launch.

```
jax 0.10.2   devices: [CudaDevice(id=0)]   NVIDIA GeForce RTX 5070 Ti Laptop GPU
2048×2048 float32 matmul, max abs err vs numpy: 0.0280
```

The 0.028 error is TF32 default precision on tensor cores, not a correctness
problem — float32 TF32 matmuls carry ~10 bits of mantissa. **The risk is retired:
JAX runs real kernels on this GPU.**

### 3.2 The fold

```bash
colabfold_batch --model-type alphafold2_multimer_v3 \
  --num-models 1 --num-recycle 3 --random-seed 1 \
  --data ~/.cache/colabfold  data/fold_inputs/5ggs_fv_colabfold.fasta  runs/colabfold/5ggs_fv
```

ColabFold's complex convention is chains joined by `:` on **one line** of a single
FASTA record. 343 residues, converged in 2 recycles, **28.9 s** of GPU time plus
about 3 minutes waiting on the MSA server. Final pLDDT 94.4, pTM 0.917, ipTM 0.891.

**Operational warning worth writing down:** the default `--msa-mode` sends the query
sequences to the **public MMseqs2 server**. Harmless for pembrolizumab and PD-1,
which are published. It would be an **undisclosed release of a novel design** later
in the project. Use `--msa-mode single_sequence`, or host the database, before any
designed sequence is folded this way.

---

## 4. Gate 1d, and the control that changed the answer

### 4.1 The question

The rubric bands ipSAE at **≥0.60 to pass** and **≥0.80 for good**. Those numbers
come from a metric developed on *AlphaFold's* PAE. Boltz-2's PAE comes from a
different confidence head. Applying one model's thresholds to another's output is
an unchecked assumption sitting under every viability decision — the same class of
error as reading a crystal B-factor as if it were pLDDT.

### 4.2 The measurement

Same complex, same vendored `ipsae.py`, same 10/15 cutoffs, `Type = max` rows:

| interface | AF2-multimer_v3 | Boltz-2 | difference |
|---|---|---|---|
| A–B heavy–light *(not scored)* | 0.864 | 0.941 | +0.077 |
| **A–C heavy–antigen** | **0.654** | **0.841** | **+0.187** |
| **B–C light–antigen** | **0.615** | **0.827** | **+0.211** |

By the handbook's rule (best antibody-vs-antigen row): AF2 reports **0.654**, a
*medium* band clearing the cutoff by 0.054. Boltz reports **0.841**, comfortably
*good*. **The same molecule, the same metric, two bands apart.**

### 4.3 The obvious conclusion, and why it is wrong

The tempting reading: *Boltz inflates ipSAE by about 0.19; discount it and move on.*

That reading fails one control. **Is the AF2 structure actually as good?**

| | DockQ vs 5GGS crystal | heavy–antigen | light–antigen |
|---|---|---|---|
| Boltz-2 | **0.820** | 0.838 | 0.820 |
| AF2-multimer_v3 | **0.690** | 0.698 | 0.690 |

It is not. AF2 built a measurably worse pose — both CAPRI-acceptable, but 0.820 is
*High* quality and 0.690 is *Medium*. **So some of the ipSAE gap is deserved.** A
confidence metric that returns a lower number on a less accurate structure is the
metric working correctly, not a scale offset.

At n = 1 the two explanations — "different PAE scale" and "Boltz modelled this
particular complex better" — are perfectly confounded, and they push in the same
direction. **G1d is therefore advanced but not resolved**, and recording it as
resolved would have been the actual error this session was at risk of making.

A second confound: the MSA treatments are not matched. AF2 received deep alignments
for all three chains; Boltz received none for the antibody and PD-1 capped at 1024.
Each is that tool's intended production protocol, so the comparison is
*operationally* meaningful — what our pipeline reports versus what the thresholds
were calibrated on — but it is mechanistically uninterpretable.

### 4.4 What would resolve it

Fold **n ≥ 8 complexes spanning a range of quality** with both predictors, then
regress ipSAE on DockQ separately for each. The offset the rubric needs is the gap
between the two fitted lines **at matched DockQ** — a quantity a single point cannot
estimate. Now cheap: 34 s/fold on Boltz, ~30 s on AF2 once MSAs are cached.

### 4.5 The operating rule until then

Treat Boltz ipSAE as **provisional and probably optimistic**. The one measurement
places a Boltz 0.80 near an AF2 0.61 — at the cutoff, not in the good band. Do not
let a Boltz ipSAE in the 0.80s alone justify calling a design good; lean on the
binding gates that do not depend on PAE, and on cross-predictor consensus.

---

## 5. Transferable principles

**A positive control that fails is a configuration bug until proven otherwise.**
Pembrolizumab scoring 0.379 was not a fact about pembrolizumab. Running the control
*first*, before any design, is what converted an unspecified CLI default into a
recorded decision. Had NetSolP been wired up with its default model and pointed
straight at designs, every design would have failed developability and it would have
looked exactly like a design problem.

**When a tool offers variants, the variant choice is data, not a default.** Three
NetSolP predictors disagree by up to 0.38 on the same sequence — larger than the
distance from the cutoff to the good band. Anything that can move a verdict across a
threshold belongs in the config file with the evidence attached.

**Before attributing a difference between two systems to the systems, check they
were solving the problem equally well.** The ipSAE gap looked like a calibration
offset and was partly a quality difference. The control cost one DockQ run and
inverted the conclusion. Generally: when comparing two estimators' *confidence*,
first compare their *accuracy* — otherwise deserved differences get booked as bias.

**Confounded at n=1 means unresolved, not "resolved with a caveat".** Two
explanations pushing the same direction cannot be separated by one measurement. The
honest output is a named follow-up experiment with its sample size.

**Verify GPU stacks with arithmetic, not with availability calls.** `jax.devices()`
returning a CUDA device and `is_available()` returning True are both satisfied by
wheels that fail at kernel launch on `sm_120`.

---

## 6. A vault-hygiene problem this surfaced

`vendor/netsolp/netsolp-1.0.ALL.tar.gz` is **6.05 GB sitting inside the synced
vault** -- 98% of the vault by size, three orders of magnitude larger than anything
else in it.

The vault syncs by **Syncthing** (`.stfolder` at the root, `*.sync-conflict-<date>-<deviceid>`
files). Checking the actual share list was worth doing, because the topology is not the
obvious one: Linux and Windows are a **dual boot on the same physical machine**, so they
can never be online together and cannot sync to each other directly. The vault is relayed
through **"Robin S26", the user's phone** -- the only always-on peer, and therefore a single
point of failure for the whole setup.

The phone was sitting at **0.47% complete, still needing 6.12 GB**. So the archive was not
merely wasteful: everything must transit the phone to reach Windows, which makes **the
phone's free space the ceiling on the entire vault**, and the tarball was blocking the path
to the Windows side entirely.

Fixed by creating `/.stignore` at the vault root:

```
/7- Projects/locksmith-antibody-hackathon/vendor/netsolp
```

**Scoped to `vendor/netsolp`, deliberately not to `vendor/`.** `vendor/ipsae/ipsae.py`
is load-bearing -- `src/locksmith/metrics/ipsae.py` shells out to it -- so excluding
the parent would have silently broken the harness on every other device, and the
breakage would have appeared as a missing file rather than as a sync decision.

Measured effect, after `POST /rest/db/scan`:

| | before | after |
|---|---|---|
| folder size in the index | 6.15 GB | **0.10 GB** |
| files | 1806 | 1805 |
| phone completion | 0.47%, needs 6.12 GB | **27.9%, needs 0.074 GB** |

Confirmed by API that `vendor/ipsae/ipsae.py` is still indexed and not ignored, that
the tarball is flagged `ignored: true` and **not** `deleted`, and that the file is
untouched on disk.

**Two Syncthing properties worth remembering.** `.stignore` is **per-device and is
not itself synced** -- every device needs its own copy. And ignoring is not deleting:
the bytes stay where they are, which is why this was a safe, reversible fix rather
than a destructive one.

---

## 7. State after this session

**Closed.** NetSolP installed, wired, validated against the positive control; the
NetSolP half of G1e is green and `viable` can return `True`. ColabFold/AF2 installed
and folding on GPU; the JAX-on-Blackwell risk is retired.

**Open in M1.**
- **G1c** (Fv↔Fab ipSAE rank correlation, ρ ≥ 0.6 over ≥10 designs) — untouched. It
  needs ≥10 designs, which couples it to M2.
- **G1d** — one data point and a control that complicates it; needs n ≥ 8 (§4.4).
- **The post-training-cutoff test** — 5GGS is from 2017 and near-certainly in both
  models' training data, so neither DockQ number tests novel placement.

**Unbuilt.** `src/locksmith/{fold,select,submit,validate}/` still contain only
`__init__.py`. No designs, no baselines. M2 has not started.
