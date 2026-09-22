# Gate 0-CPU and Gate 0b — RFantibody on CPU, measured — 2026-09-21

**Verdict: Gate 0 PASS. Gate 0b PASS. One backbone = ~19.5 min on this CPU.**

## Gate 0 — verified by arithmetic, not by flags

Environment: `~/.venvs/rfab-cpu`, isolated. `~/.venvs/locksmith` untouched and re-verified
by `scripts/00_doctor.py` (all required checks pass) after the install.

```
torch 2.2.1+cpu   cuda=None   is_available=False
[ ok ] torch CPU matmul exact vs numpy; max abs err 0.00e+00
[ ok ] relu correct                       <- the op that died on GPU with 'no kernel image'
[ ok ] DGL 2.1.0 message-pass -> [4,1,2,3] (expected [4,1,2,3])
[ ok ] e3nn 0.6.0 tensor product -> (5,2), all finite
```

All four RFantibody modules import: rfdiffusion `model_runners`, rfdiffusion `utils`,
`proteinmpnn`, rf2 `predict`. All four weight files load and contain tensors
(5998 / 8044 / 118 / 8042) — checked by loading, not by `ls`.

### Three walls hit, all environmental, none requiring a port

1. **PyPI's DGL ships no torch-2.3 ABI.** `dgl` 2.1.0 from PyPI bundles
   `libgraphbolt_pytorch_<v>.so` for torch **2.0.0-2.2.1 only**; RFantibody pins
   `torch==2.3.*`. Resolved by using torch **2.2.1+cpu** — RFantibody was installed
   `--no-deps` so its pin binds nothing, and all four modules import and run.

   > **CORRECTION (same day).** I first wrote here that *"DGL has never published a
   > torch-2.3 build on any channel."* **That is false.** `data.dgl.ai/wheels/torch-2.3/`
   > lists **dgl 2.2.0, 2.2.1, 2.3.0, 2.4.0 and 2.5.0**, and RFantibody's own
   > `pyproject.toml` pins `dgl-2.4.0+cu118` from exactly that index. The 2.4.0 and 2.5.0
   > wheels there carry **no CUDA tag**, which in DGL's layout means the CPU build (the
   > CUDA ones sit under `cu118/`, `cu121/` with `+cuXXX` local versions), so a CPU
   > torch-2.3 DGL very likely exists and the downgrade may be unnecessary.
   >
   > **How the error was made, which is the reusable part:** I read that index through
   > `grep ... | head -8`, and the first eight matches were all `dgl-2.2.0`. Truncation
   > read as the complete answer. This is verbatim the standing rule — *"`grep…|head` lies
   > TWICE - the piped exit status, and truncation reads as fixed"* - and I broke it while
   > writing a document whose whole purpose is measured claims.
   >
   > Not retested yet: the measurement run was live in this environment and reinstalling
   > torch under it would have destroyed the number being collected. **Status: torch 2.2.1
   > works and is what every figure below was measured on.** Matching upstream's 2.3.1 pin
   > is available and untested.
2. `torchdata==0.11.0` removed `torchdata.datapipes`, which DGL 2.x imports → `torchdata==0.7.1`.
   Plus a missing `pydantic`.
3. **`torch.cuda.nvtx` raises on a CPU-only build.** NVIDIA's vendored SE3Transformer
   (`include/SE3Transformer/.../basis.py:32`, `layers/convolution.py:34`) does
   `from torch.cuda.nvtx import range as nvtx_range` and wraps every layer in it.
   NVTX is profiler annotation — no computation, no tensor touched. Disabled by a **runtime
   null-context shim in our own launcher** (`scripts/65_rfdiff_cpu.py`), applied before
   rfantibody imports because those modules bind `range` at import time. **No vendored file
   is modified and nothing is recompiled**, so the "no porting" kill criterion is not
   triggered — but it is a judgment call and is recorded as one.

### A CPU-only torch is load-bearing, not hygiene
RFdiffusion (`model_runners.py:48-52`), ProteinMPNN (`proteinmpnn_interface_design.py:85-90`)
and RF2 (`rf2_predict.py:32`) all branch on `torch.cuda.is_available()` — the call that
returned **True in two dead environments on 2026-09-20**. A CUDA-enabled torch here sends
every stage down the GPU path to die on `sm_120`. The CPU wheel makes it False by construction.

## The target was specified as the wrong molecule — caught before the run

Every planning document said *"5GGS chain C relabelled to T"*. **5GGS chain C is a second
copy of pembrolizumab's heavy chain.** The crystal holds two Fab copies (A/B, C/D) and two
PD-1 copies (**Y/Z**). The phrase conflated the handbook's *submission* convention
(A=heavy, B=light, C=antigen — true of complexes we generate) with the crystal's chain IDs.

| 5IUS PD-L1 footprint aligned to | identity | residues mapped |
|---|---|---|
| 5GGS chain Y (PD-1) | **90.2%** | 26/26 |
| 5GGS chain Z (PD-1) | **90.1%** | 26/26 |
| 5GGS chain C (heavy) | **15.4%** | **26/26** |

**All three report 26/26 mapped — coverage is not the check, identity is.** `io/pdb.py`'s
module docstring already warned of exactly this ("getting this wrong does not raise an
error"); Challenge 1 correctly uses `data/refs/prepared/5ggs_ABZ.pdb`. Only the prose was
wrong, and prose is what an unattended job follows.

Target built from `5ggs_ABZ.pdb` chain C (PD-1, 113 aa, numbering 31–143, relabelled from
Z) → chain T at `~/.cache/rfantibody/inputs/pd1_T.pdb`. **All 26 footprint residues resolve.**

This mattered: `ab_pose.py:105-110` matches hotspots on `(chain, pdb_resnum)` and **silently
skips misses**. Wrong numbering ⇒ zero hotspots ⇒ unconditioned generation wearing the
target's name, with no error. The run log confirms **26 "Using ... as a hotspot"** lines.

## Gate 0b — the number

Measured on an otherwise-idle box, `OMP_NUM_THREADS=24`, 24 cores, system
353 residues (113 target + ~240 scFv framework).

| Quantity | Measured |
|---|---|
| **sec / diffusion step** | **23.37** (median 23.47, sd **0.53**, min 22.5, max 24.2) |
| steps per backbone | 50 (RFdiffusion default) |
| **min / backbone** | **≈19.5** (+ ~4 min one-off model load per invocation) |
| RAM in use during run | 6.1 GB of 15.6 GB; **9.5 GB still available** |
| load average | 10.85 on 24 cores — effective parallelism ≈11, not 24 |

**RAM is not the binding constraint.** The pre-run worry (RFantibody's own `--memory 10g`
Docker baseline, ~11 GB available) did not bite: actual usage is 6.1 GB. Boltz can run
concurrently on the GPU.

Step time is remarkably stable (sd 0.53 s = 2.3% of mean), so the projection is sound.

### What this implies for a night
`N` backbones ≈ `4 + 19.5N` minutes. A 14-hour window ⇒ **~42 backbones** of diffusion,
before MPNN (cheap) and RF2 (a fold, not yet timed on CPU).

## Gate 0b, part 2 — the full pipeline, measured end to end

All three stages ran on the one backbone. **This is the first complete Challenge 2
pass: dock -> sequence -> independent filter.**

| Stage | Measured | Notes |
|---|---|---|
| RFdiffusion, 1 backbone | **19.5 min** diffusion, 23.5 min wall | 23.37 s/step x 50, + ~4 min one-off model load |
| Backbone artefact | **valid** | 1328 atoms; H:115 L:104 **T:113** res; no NaN; 0 duplicate coords; extent 54x58x49 A |
| ProteinMPNN, 4 sequences | **2 s** | negligible; drops out of the budget entirely |
| RF2, 4 designs, 10 recycles | **28 min 23 s = 7.1 min/design** | 4/4 succeeded, exit 0, spacing dead even (6.6/7.0/7.0/7.0) |
| **Per backbone, full config** | **~48 min** | 19.5 + 0.03 + 28.4 |

Resource use: RF2 peak RSS **2.59 GB** for the parent process; system-wide the RF2
stage ran at **9.9 GB used / 5.7 GB free**, versus 6.1 GB during diffusion. CPU 1132%
throughout -- **~11 effective cores of 24**, identical to the diffusion stage, so
`OMP_NUM_THREADS=24` is not buying what it claims at either stage.

### Budget
`N` backbones, full config (4 seqs, 10 recycles, RF2 kept) = **N x 48 min**.
- 20 backbones -> **~16 h**
- a 14 h window -> **~17 backbones**

> **A projection of mine was wrong and is corrected here.** I derived RF2 at
> "~4 min/sequence" from RFdiffusion's measured 23.4 s per network pass x 10 recycles
> on the same 353-residue system. Measured: **7.1 min**, so the derivation was **1.75x
> optimistic**, and the 20-backbone estimate moved 12 h -> 16 h. Same shape as the fold
> batching projection (predicted 1.8x, measured 1.16x). It was flagged as unverified when
> given, which is the only reason it did not steer a schedule.

### Two environment facts the CLI forces
RFantibody's CLI spawns every stage as a **subprocess** (`cmd = ['python', script_path]`
at `src/rfantibody/cli/inference.py:103, 249, 397`). Consequences:
1. A bare `python` must be on PATH -- invoking the venv interpreter by absolute path is
   not enough, and the subprocess dies with `FileNotFoundError: 'python'`.
2. An in-process NVTX shim **cannot reach the subprocess**. The shim therefore lives in
   `sitecustomize.py` inside `~/.venvs/rfab-cpu/lib/python3.10/site-packages/`, which every
   interpreter started from that venv imports automatically. Still no vendored file is
   modified and nothing is recompiled.

### Process failure: `pgrep -f` self-matched for the FIFTH time, costing 1 h 22 min
The timing chain waited with `while pgrep -f "65_rfdiff_cpu"; do sleep 20; done`. That
matched **a stale harness shell whose argv still contained the string**, because the
launcher had been created by a heredoc inside `bash -c`. The backbone had exited at
09:58:38; the loop waited on a ghost until 11:23, exit code **144** -- the documented
signature. The rule this violates was written into the run prompt by the same author
hours earlier. **Fix: the artefact on disk is the completion signal, never a process
pattern.** Related: `setsid` detaches, so `$!` returns a parent that exits immediately --
waiting on it returns instantly and falsely reports completion.

## Honest limits

- **Not yet measured:** peak RSS from `/usr/bin/time -v`, the tier-0 determinism control
  (same seed twice — required before the B3 canary means anything, since CPU reductions are
  thread-count dependent), output-structure validation (residue counts, loop lengths, NaN
  check), and **RF2 CPU throughput**, which is a fold and could dominate the budget.
- **Effective parallelism is ~11 of 24 cores**, so `OMP_NUM_THREADS=24` is not buying what
  it claims. Untuned; a lower setting may cost nothing and free cores for other stages.
- Timing is from a **quiet machine**. Contention cost 2.3× on fold rate on 2026-09-20;
  size from a contended re-measure, not from this number.
- This is **one backbone**. Step time is stable within it, but between-backbone variance
  (loop lengths are sampled per design) is unmeasured.
