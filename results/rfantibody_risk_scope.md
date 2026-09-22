# Route A (RFantibody) — risk scope before any install

Written 2026-09-20. **Nothing has been installed.** This exists so the decision to spend
days on Route A is made against measured facts rather than against the day-1 risk register's
one-line "High".

---

## 1. The finding that reframes everything

RFantibody's `pyproject.toml` pins its whole stack to **CUDA 11.8**:

```
requires-python = "==3.10.*"
torch == 2.3.*            [index: https://download.pytorch.org/whl/cu118]
cuda-python == 11.8
dgl @ https://data.dgl.ai/wheels/torch-2.3/cu118/dgl-2.4.0+cu118-cp310-...whl
e3nn
include/SE3Transformer/se3_transformer   (vendored)
```

This machine is an **RTX 5070 Ti Laptop, compute capability 12.0 (`sm_120`, Blackwell)**,
driver 595.84.

**CUDA 11.8 predates Blackwell and cannot target `sm_120` at all.** This is stronger than
the usual "old wheels are risky": PTX forward-JIT lets a binary built for an older *virtual*
architecture run on a newer GPU only within the same CUDA major version. CUDA 11 has no
`compute_120` and emits no PTX that a 12.x driver can lower to it. So the shipped
environment will not run here — that is now a fact, not a risk to be managed.

The follow-on question is whether a *modified* stack can. Checked directly:

| | available? |
|---|---|
| DGL official wheels, cu128 | **no** — `data.dgl.ai/wheels/torch-2.4/cu128` returns HTTP 403 |
| DGL official wheels, cu126 | **no** — 403 |
| DGL official wheels, cu124 | yes — `dgl-2.4.0+cu124-cp310`, built against torch 2.4 |
| DGL on PyPI | Windows wheels only, v2.2.1 |

So the newest CUDA DGL exists for is **12.4**, and `sm_120` needs 12.8. DGL is the hard
dependency — the SE3-Transformer builds its equivariant attention on DGL graphs — so it
gates the whole route.

**GATE 0 RUN 2026-09-20 — RESULT: FAIL. The section below was written before the test;
the measured outcome is in §1a and supersedes the speculation.**

**One genuine unknown remained, and it was cheap to resolve:** CUDA *minor*-version
compatibility does permit PTX JIT within 12.x. If the cu124 wheels ship `compute_90` PTX,
the 595.84 driver may JIT them to `sm_120` at load. They may equally ship SASS only, in
which case it fails with `no kernel image is available for execution on the device`. That
is a 30-minute test, not an argument.

### 1a. Gate 0, measured

Two throwaway environments, both tested with real arithmetic rather than
`torch.cuda.is_available()` — which returned **True in both cases while nothing worked**.

**Shipped stack — torch 2.3.1+cu118:**

```
is_available: True
arch list   : sm_50 sm_60 sm_70 sm_75 sm_80 sm_86 sm_37 sm_90
PTX entries : NONE
cuBLAS matmul      -> CUDA error: no kernel image is available for execution on the device
elementwise kernel -> CUDA error: no kernel image is available for execution on the device
```

**Best available modified stack — DGL 2.4.0+cu124:**

```
torch: 2.4.0+cu121          <- NOT what was requested; see below
arch list   : sm_50 ... sm_90
PTX entries : NONE
cuBLAS matmul       -> no kernel image is available for execution on the device
dgl GPU message-pass -> no kernel image is available for execution on the device
```

Three things are now settled rather than argued:

1. **No PTX is shipped in any of these wheels.** `get_arch_list()` contains no `compute_*`
   entry, so the PTX forward-JIT route that exists in principle is simply not available
   here — there is nothing for the driver to lower to `sm_120`.
2. **The failure is total, not partial.** It is not only cuBLAS: a plain elementwise ReLU
   fails too. There is no "most of it works" configuration to salvage.
3. **DGL pins `torch==2.4.0` exactly and clobbered the cu124 torch** with the generic PyPI
   build on install. So "bring your own newer torch" is not available either — the DGL
   wheel drags the torch version with it. That closes the last local workaround short of
   compiling DGL from source, which is porting and is excluded by kill criterion 2 (and
   there is no `nvcc` on this machine in any case).

**Gate 0 therefore fails and the decision moves to G1 (cloud).** Elapsed: ~25 minutes,
inside the 30-minute box. Both probe environments were created outside the vault and
deleted afterwards (9.8 GB reclaimed).

---

## 2. Risks, each with a detection and a fallback

| # | risk | evidence | detect by | mitigation / fallback |
|---|---|---|---|---|
| **R1** | **DGL/SE3 cannot execute on `sm_120`** | cu118 pinned; no DGL past cu124 | Gate 0 below, 30 min | Run RFdiffusion off this GPU (R2) or on CPU (R3) |
| **R2** | Docker GPU path unavailable | `docker info` lists runtimes `runc` only; **nvidia-container-toolkit not installed**; `apptainer`/`singularity` absent | already confirmed | Needs `sudo apt install nvidia-container-toolkit` — **you must run it, sudo prompts**. But note a container does *not* fix R1: a cu118 image still has no `sm_120` kernels |
| **R3** | CPU fallback too slow | RFdiffusion is minutes/backbone on GPU | time 1 backbone on CPU | Cap N at what fits a night; 8–16 backbones is still a real result |
| **R4** | **8 GB of weights land inside the synced vault** | Syncthing relays via the phone; a 6.05 GB blob previously stalled the whole vault at 0.47% and blocked the Windows machine | check path before download | Install to `~/.local/share/locksmith/RFantibody`, weights outside the vault. **Non-negotiable** |
| **R5** | 12 GB VRAM insufficient | RFantibody's own Docker baseline is `--memory 10g` (host RAM, not VRAM) | first real run | Target is small (PD-1, 123 aa) + Fv framework ≈ 350 res; should fit. Reduce batch/diffusion steps if not |
| **R6** | Python 3.10 vs the project's 3.12 | `requires-python = "==3.10.*"` | n/a | `uv` provisions 3.10 in its own venv; keep it fully separate from `~/.venvs/locksmith`. No interaction |
| **R7** | HLT format and epitope spec wrong | inputs are chains renamed H/L/T plus PDB REMARKs giving 1-indexed CDR loop positions | validate on the shipped example first | Convert with the repo's `chothia_to_HLT.py`; hotspots are the PD-L1 footprint on PD-1, which we already extracted from 5IUS |
| **R8** | Chain-naming collision downstream | RFantibody uses **H/L/T**, the handbook and our pipeline use **A/B/C** | packaging assertions already catch it | `submit/package.py` compares every chain residue-by-residue against the FASTA and raises |
| **R9** | Unbounded debugging | the failure mode that actually costs days | wall clock | Hard kill criteria in §4 |

---

## 3. The option I had not considered, and it is probably the answer

**Run RFantibody where its stack is supported, and keep scoring here.**

RFantibody's cu118 pin is only a problem because of *this* GPU. On any Turing/Ampere/Ada
card — Colab's T4 (`sm_75`, 16 GB), L4, or an A100 — the shipped environment installs and
runs exactly as documented, with no porting at all. The pipeline splits cleanly:

- **Off-machine:** RFdiffusion → ProteinMPNN → RF2. Produces backbones and sequences.
- **On this machine:** fold the resulting VH/VL/antigen complexes with Boltz-2 and score
  them with the harness we have already built, validated and packaged.

This removes R1, R2, R3 and R5 in one move, and costs a free Colab session. The only new
risks are session timeouts (checkpoint outputs to Drive) and the disclosure question —
which does not apply here, since PD-1 and the frameworks are public and nothing proprietary
leaves the machine.

It also preserves the thing Route A was chosen for: the design is genuinely produced by
target-conditioned backbone diffusion, so it is Challenge 2 as specified, not Challenge 1's
method relabelled.

---

## 4. Staged plan, with kill criteria

Each gate is time-boxed. Missing a gate means moving to the next row, **not** debugging past
the box.

| gate | what | box | pass → | fail → |
|---|---|---|---|---|
| **G0** | Local feasibility probe: install `torch 2.4+cu124` + `dgl 2.4+cu124` in a throwaway venv, run one DGL op and one SE3 attention layer on the GPU | **30 min** | local GPU path; go to G2 | G1 |
| **G1** | Stand up RFantibody on a free cloud T4/L4 per its own README, run the shipped example to completion | **2 h** | cloud path; go to G2 | G1b |
| **G1b** | CPU-only locally: `uv sync` with CPU wheels, time one backbone | **1 h** | reduced-N overnight run | **STOP** — write the declined-with-reasons outcome |
| **G2** | Prepare inputs: PD-1 target in HLT, epitope hotspots from the 5IUS PD-L1 footprint, framework choice | **2 h** | G3 | STOP |
| **G3** | Generate 20 backbones → MPNN → RF2 filter | **3 h** | G4 | STOP |
| **G4** | Fold survivors with Boltz-2 here, score with our harness, apply the §7.2 cutoffs | **3 h** | G5 | report what failed |
| **G5** | Germline novelty metric (does not exist; blocks any Challenge 2 score), then package | **4 h** | done | — |

**Hard kill criteria, agreed now rather than at 2 a.m.:**

1. More than **one working day** total on installation across G0+G1+G1b → stop and write the
   declined outcome. The scope doc already has the three measurements that justify it.
2. Any step that needs a kernel rebuild, a patched DGL, or a compiler flag → stop. That is
   porting, not installing, and it is not what the remaining time is for.
3. If G3 produces backbones but RF2 rejects all of them → that is a **result**, report it;
   do not tune until something passes.

**Realistic totals:** cloud path ≈ **1.5–2 days**. Local-GPU path (if G0 passes) ≈ 1.5 days.
CPU path ≈ 2 days for a much smaller N. Declined outcome ≈ half a day.

---

## 5. What I need from you

- **R2/R4 need sudo or a decision, not code:** installing `nvidia-container-toolkit` prompts
  for a password. My recommendation is **don't** — it only matters for the Docker path, and
  the Docker path does not solve R1.
- **Cloud is the recommended route.** If you are happy for a Colab session to be used, say
  so and G0/G1 start there; nothing proprietary is involved.

## 6. The caveat that survives whichever route runs

Everything measured today still applies to whatever Route A produces. Challenge 2 has **no
DockQ**, so nothing in its rubric can detect a wrong pose; Boltz-2's median DockQ on
post-cutoff complexes is **0.291**; and SKEMPI showed no metric in the stack tracks measured
affinity, with PRODIGY ΔG failing the epitope-knockout control outright. A Challenge 2
design will therefore be reported as *"produced by target-conditioned diffusion, clears the
§7.2 cutoffs, and is not supported by evidence that it binds"* — the same honesty the
Challenge 1 docs carry. Route A buys a design made the way the handbook asks. It does not
buy confidence in it.
