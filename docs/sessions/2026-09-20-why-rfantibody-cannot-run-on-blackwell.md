# Session 2026-09-20 — Why RFantibody cannot run on this GPU, measured

## 0. Session at a glance

Challenge 2 was chosen to be attempted properly (Route A: RFdiffusion/RFantibody, the
method the handbook's "blank canvas, de novo" language actually describes). Before
installing anything, the risks were scoped; one of them turned out to be decidable in
25 minutes, and the answer was no. Output: a measured feasibility verdict, a risk register
with kill criteria, and a concrete off-machine plan. **No design was produced and no
campaign was started.**

## 1. The problem this session addressed

Challenge 2 (§3.2 of the handbook) asks for *"Blank canvas — design from scratch"* and
*"a complete VH/VL antibody **de novo**"*. Two routes had been costed:

- **A** — RFantibody: target-conditioned diffusion of CDR **backbones** against the
  epitope, then sequence design, then structure filtering.
- **B** — graft a germline framework and design CDR **sequences** with ProteinMPNN on an
  inherited backbone geometry.

B is what Challenge 1 already did, pointed at a different framework. It generates no new
loop conformations, so it is not what §3.2 asks for; putting it in the Challenge 2 folder
would invite the obvious question. A was chosen. The question this session answers is
whether A can run on the hardware available.

## 2. Concepts introduced (first principles)

### 2.1 How a CUDA binary knows which GPU it can run on

An NVIDIA GPU has a **compute capability**, written `sm_XY` — `sm_90` is Hopper, `sm_120`
is Blackwell, and this machine's RTX 5070 Ti Laptop is `sm_120` (reported by
`torch.cuda.get_device_capability()` as `(12, 0)`).

A compiled CUDA program ships a **fatbinary** containing some mixture of two things:

- **SASS** — actual machine code for one specific `sm_XY`. Fast, and it runs on that
  architecture only.
- **PTX** — a virtual assembly for a *virtual* architecture, written `compute_XY`. The GPU
  driver can **JIT-compile** PTX at load time into SASS for whatever real GPU is present.

The compatibility rule that follows:

> **SASS is backwards-compatible within a major architecture family. PTX is
> forwards-compatible to architectures that did not exist when it was compiled** — provided
> the shipping binary actually contains PTX, and provided the compiling toolkit's PTX ISA
> is one the driver understands.

That proviso is the whole story of this session. A build with `sm_90` SASS and no PTX
simply has nothing to offer a `sm_120` device, and the driver reports
`CUDA error: no kernel image is available for execution on the device`.

In PyTorch, `torch.cuda.get_arch_list()` prints exactly what a build contains. Entries like
`sm_90` are SASS; an entry like `compute_90` would be PTX. **If there is no `compute_*`
entry, there is no JIT fallback.**

### 2.2 Why `torch.cuda.is_available()` is not a capability check

`is_available()` returns True when a CUDA driver and a visible device are present. It does
**not** check that the installed binaries contain kernels for that device. The project has
a standing rule from earlier work — *verify with arithmetic, never `is_available()`* — and
this session is its cleanest demonstration: `is_available()` returned **True** in two
environments in which literally every kernel failed, including a plain ReLU.

### 2.3 Why a Docker container does not fix an architecture mismatch

Containers isolate userspace, not the GPU's instruction set. An image built against CUDA
11.8 contains 11.8's SASS and libraries; running it on a Blackwell card changes nothing
about which kernels exist. Containers solve dependency conflicts, not compute-capability
gaps. (Separately, this machine cannot run GPU containers at all: `docker info` lists only
the `runc` runtime and `nvidia-container-toolkit` is not installed.)

## 3. What was built — mechanism, not narrative

Two throwaway probe environments, created **outside the synced vault** at
`~/.venvs/rfab-probe{118,124}` and deleted afterwards (9.8 GB reclaimed). The vault syncs
via Syncthing through a phone relay, and a multi-GB blob inside it previously stalled the
whole vault at 0.47% complete; large transient environments must never live there.

**Probe 1 — the stack RFantibody actually pins.** From its `pyproject.toml`:

```
requires-python = "==3.10.*"
torch == 2.3.*                 [index https://download.pytorch.org/whl/cu118]
cuda-python == 11.8
dgl @ https://data.dgl.ai/wheels/torch-2.3/cu118/dgl-2.4.0+cu118-cp310-...whl
e3nn
include/SE3Transformer/se3_transformer    (vendored)
```

```
uv venv --python 3.10 ~/.venvs/rfab-probe118
uv pip install --index-url https://download.pytorch.org/whl/cu118 "torch==2.3.*"
```

**Probe 2 — the newest stack DGL offers.** Wheel availability was checked directly against
the index rather than assumed:

| index | HTTP |
|---|---|
| `data.dgl.ai/wheels/torch-2.4/cu128` | **403 — does not exist** |
| `data.dgl.ai/wheels/torch-2.4/cu126` | **403 — does not exist** |
| `data.dgl.ai/wheels/torch-2.4/cu124` | 200 |
| `data.dgl.ai/wheels/torch-2.4/cu121` | 200 |

So CUDA **12.4** is the ceiling for official DGL, and `sm_120` requires **12.8**.

The test in both environments was arithmetic, not introspection: a 512×512 float32 matmul
compared against numpy (exercises cuBLAS), and a plain elementwise ReLU (exercises
PyTorch's own kernels). Probe 2 additionally ran a DGL GPU message-pass
(`g.update_all(fn.copy_u, fn.sum)` on a 3-node graph) because DGL's own CUDA kernels — not
just torch's — are what SE3-Transformer depends on.

## 4. Design decisions

| decision | alternatives | why | cost to reverse |
|---|---|---|---|
| Probe before installing | install and see | The full install is ~10 GB, weights included, and would have taken hours to fail. The probe isolates the one question that decides everything. | none |
| Test with arithmetic | `is_available()`, `get_arch_list()` alone | `is_available()` returned True in both failing environments. `get_arch_list()` is necessary but not sufficient — it tells you what is *shipped*, not whether the driver will accept it. | none |
| Probe envs outside the vault | anywhere convenient | Syncthing relays through a phone; 11 GB inside the vault would have blocked the Windows machine. | expensive — a stalled relay is hours to clear |
| Do **not** install nvidia-container-toolkit | install it, try the Docker route | Requires sudo (user action), and a cu118 image has no `sm_120` kernels either, so it cannot fix the actual problem. | trivial |
| Target the **PD-L1 competitive footprint** for hotspots, not pembrolizumab's epitope | pembrolizumab's epitope | §3.2 permits either. The PD-L1 footprint is the one that actually blocks the checkpoint; it was already extracted from 5IUS and mapped to 5GGS by explicit alignment (the two entries are only 90.1% identical, so it was not assumed). | cheap — it is one CLI argument |
| Use RFantibody's shipped `hu-4D5-8_Fv.pdb` framework | pembrolizumab's framework | Makes the Challenge 2 design independent of Challenge 1's scaffold, so "de novo" is defensible rather than Challenge 1 relabelled. | cheap |
| RF2 as cloud **filter**, Boltz-2 as the scoring fold | score on RF2's own output | Both challenges then rest on one predictor, so their numbers are comparable. | cheap |

## 5. What went wrong

**I asserted the conclusion before measuring it, and the reasoning was wrong even though
the conclusion was right.** I wrote that CUDA 11.8 "cannot target `sm_120`" and that "no
PTX JIT path exists from CUDA 11". The second clause is false as a general statement — PTX
forward-compatibility is exactly the mechanism that would allow it. When challenged with
*"are you sure this isn't an optimisation problem"*, the honest answer was that I had
argued, not tested.

The measurement then showed the conclusion holds **for a different reason than I gave**:
the wheels ship no PTX at all (`PTX entries: NONE`), so the forward-compat mechanism has
nothing to work with. Right answer, wrong derivation, and I would not have known which
without running it.

This was the fifth correction in a single day and the first in the *conservative*
direction — the previous four all overstated a finding. The general lesson is not "be less
confident"; it is that **a claim about a mechanism and a claim about an outcome are
different claims, and only one of them was cheap to test.**

## 6. Degenerate and failure cases

**Both probes failed identically**, which is itself the informative part:

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
torch       : 2.4.0+cu121        <- see below
arch list   : sm_50 ... sm_90
PTX entries : NONE
cuBLAS matmul        -> no kernel image is available for execution on the device
dgl GPU message-pass -> no kernel image is available for execution on the device
```

Three failure modes worth naming:

1. **Total, not partial.** It is not only cuBLAS: a plain elementwise ReLU fails. There is
   no "most of it works, avoid matmuls" configuration to salvage.
2. **`is_available()` is True in both.** A plausible-but-wrong result here looks like a
   green setup check followed by a crash hours into a run.
3. **DGL pins `torch==2.4.0` exactly and silently replaced the cu124 torch** with the
   generic PyPI build (cu121) during install. This is the one that closes the door: the
   obvious workaround — "install DGL, then force a newer torch" — is unavailable, because
   the DGL wheel drags a specific torch version with it. The only remaining local option is
   compiling DGL from source against cu128, which needs a CUDA toolkit (`nvcc` is not
   installed) and is porting rather than installing.

## 7. Verification — how we know it works

The verdict is a **negative** result, so "verification" means showing the test could have
detected success:

- The **same two arithmetic tests pass** in the project's working environment
  (`~/.venvs/locksmith`, torch 2.11.0+cu128, `arch list` contains `sm_120`). The probe
  harness is therefore sensitive to the thing it is testing.
- The error is the specific CUDA diagnostic for a missing kernel image, not a generic
  import or driver failure.
- `get_arch_list()` independently corroborates the mechanism: no `compute_*` entry means no
  PTX, which is exactly why no JIT occurs.

**What healthy looks like** if the cloud route is tried: `nvidia-smi` reports a T4/L4/A10
(`sm_75`/`sm_89`/`sm_86`), `get_arch_list()` contains that architecture, and both arithmetic
tests pass before any weights are downloaded.

## 8. Honest assessment

**Solid.** The feasibility question is closed with measurements rather than opinion, inside
its 30-minute box, with the environments cleaned up. The failure mode is understood at the
mechanism level, not just observed.

**Crude.** One thing was *not* checked and could in principle soften the verdict:
RFantibody lists **e3nn** alongside DGL, and if its SE3 layers can run through e3nn with
DGL confined to CPU graph bookkeeping, the wall might be thinner than measured. That is a
real open question and it is recorded rather than dismissed.

**Unproven.** The runtime estimate for the cloud route — 8–15 min per backbone on a T4 for
a ~345-residue system, from the README's stated O(N²) scaling and no published benchmark —
is an estimate. It decides whether 30 or 100 backbones fit a session, so the plan makes
timing one backbone the first action after install rather than a thing discovered at hour
three.

**Not attempted.** No cloud run, no design, no Challenge 2 entry. The germline CDR-H3
novelty metric still does not exist and blocks any Challenge 2 score regardless of route.

## 9. Next steps

1. **Germline novelty metric** (~half a day). Blocks everything; needed for any route;
   independent of the hardware question.
2. **Pick a service.** RunPod/Vast (~£3, no session limit, a real terminal) or Kaggle
   (free, 12-hour sessions) — both beat free Colab's ~4 hours for a job this shape.
3. **Build inputs**: PD-1 from 5GGS chain C relabelled to chain `T`, hotspot string from
   the 26-residue PD-L1 footprint, framework `hu-4D5-8_Fv.pdb`.
4. **Run the pilot**: 30 backbones × 4 sequences, RF2 filter, bring sequences home.
5. **Fold and score here** with Boltz-2 and the existing harness, then package with the
   builder and validator, which already handle `challenge=2` correctly.

## 10. Glossary

**Compute capability / `sm_XY`** — the instruction-set generation of an NVIDIA GPU;
`sm_120` is Blackwell.
**SASS** — architecture-specific GPU machine code; runs only on the architecture it was
compiled for.
**PTX / `compute_XY`** — a virtual ISA that the driver can JIT-compile to a real
architecture at load time, including architectures newer than the compiler.
**Fatbinary** — the container inside a CUDA library holding SASS for several architectures
and, optionally, PTX.
**DGL** — Deep Graph Library; provides the graph message-passing kernels that
SE3-Transformer's equivariant attention is built on.
**SE3-Transformer** — the rotation-equivariant attention module inside RFdiffusion.
**HLT format** — RFantibody's input convention: a PDB with chains renamed H (heavy),
L (light), T (target), plus REMARKs giving 1-indexed CDR loop positions.
**Quiver (`.qv`)** — RFantibody's batch container for many structures in one file.
**Hotspot** — a target residue the diffusion model is conditioned to build an interface
against; passed as `-h "T64,T66,..."`.
