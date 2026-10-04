# GPU run brief — the two validity controls

> **SUPERSEDED 2026-10-03. Neither control needed a rented GPU, and this brief is the
> document that said they did.** Control 1 (the decoy patch) **ran locally on CPU for $0**
> on 2026-09-28, hours after this was written. Control 2's sequencing step is **also free**:
> RFantibody's bundled ProteinMPNN falls back to CPU and does all 144 sequences in about
> **2.4 minutes** — verified 2026-10-03 by running it (2 sequences in 1 second). §2 below is wrong and is kept, struck
> through, because *how* it was wrong is the lesson: the pin it cites is real, the
> conclusion drawn from it is not, and the project had already proved so five days earlier.
> See [register §B12](../results/retractions.md).

**Written 2026-09-28. Nothing here has been run. Everything that could be done without a
GPU already has been**, so this is a single pod session with the analysis pre-written and
the outcome pre-registered.

---

## 1. What it costs, from measured rates rather than brackets

`STATE.md` carried "~2–4 GPU-hours". That was never measured. From
`runs/challenge2_pod/c2/backbones.jsonl`, the 2026-09-21 run timed **10 backbones**:

| quantity | measured |
|---|---|
| per backbone | mean **161 s**, median 148 s, min 141 s, max 288 s |
| 18 decoy backbones | **0.81 GPU-hours** |
| ProteinMPNN, 30 designs | **41 s** |
| pilot's realised price | $2.82 for 5.5 h ≈ **$0.51/GPU-hour** |
| **this session** | **≈ 1 GPU-hour, ≈ $0.50** plus setup |

The estimate fell because **the decoy control needs RFdiffusion only**. Targeting is
measured on *backbones* — `scripts/70`, `94` and `95` all parse `bb/*.pdb` — so the decoy
arm needs no ProteinMPNN and no RF2. That is most of the old estimate gone.

> A bracketed figure in this project has been wrong by 1.75× before (RF2 at "4 min/sequence"
> measured 7.1). These are timings off the previous run of the same command on the same
> stack, which is the closest thing available to a measurement.

---

## 2. Why a rented card at all

Not capability. **Your RTX 5070 Ti is too new.** RFantibody pins `torch==2.3.*`, PyPI's DGL
ships `libgraphbolt_pytorch_<v>.so` for 2.0.0–2.2.1 only, and those wheels carry **no PTX**,
so there is no forward-JIT to `sm_120`. Verified in the pod logs: RFdiffusion, ProteinMPNN
and RF2 all come from that stack. Boltz-2 is unaffected and runs locally on Blackwell.

| step | tool | where this brief said | **where it actually runs** |
|---|---|---|---|
| decoy backbones | RFdiffusion | ~~rented sm_86~~ | **local CPU, $0** — `~/.venvs/rfab-cpu`, ~26 min/backbone. Done 2026-09-28 |
| sequences for the unconditioned arm | ProteinMPNN | ~~rented sm_86~~ | **local CPU, $0** — falls back at `proteinmpnn_interface_design.py:85-90`; 2 sequences in 1 s |
| fold + score | Boltz-2 | local, free | local, free ✅ the only row that was right |

**Why the error was plausible, and why that is not an excuse.** The pin is real:
RFantibody requires `torch==2.3.*`, DGL ships no matching ABI, and those wheels carry no
PTX, so nothing reaches `sm_120`. Every clause is true and the conclusion still does not
follow, because *CPU* was never in the comparison. The one genuine obstacle is unrelated to
the device — the CLI subprocesses a bare `python` (`cli/inference.py:294`), so without the
venv's `bin` on `PATH` it dies with `FileNotFoundError: 'python'`, which looks nothing like
a device problem.

**One option worth pricing first.** The *standalone* ProteinMPNN builds on modern torch and
would make the sequencing step free. The cost is that the conditioned arm used RFantibody's
bundled copy, so the two arms would no longer be tool-matched — an uncontrolled difference
between arms is exactly the defect this project keeps finding elsewhere. Matched and rented
is defensible; free and unmatched is defensible only if the result says so.

---

## 3. Control 1 — the decoy patch. The only outstanding way to be wrong.

Every test run so far compares the conditioned arm against a resampled null **on the same
structures**. None of them can separate

- *"the hotspots steered RFdiffusion to the face we named"*, from
- *"RFdiffusion docks antibodies on that face of PD-1 anyway"*,

because nothing has ever asked it for a different face. Note this got *more* important on
2026-09-28, not less: under a size- and shape-matched null the conditioning result
strengthened to **18/18** ([§D4](../results/retractions.md)), so the observational route is
exhausted.

**The decoy is already selected and verified on CPU** — [`results/decoy_patch.md`](../results/decoy_patch.md):

| property | epitope | decoy |
|---|---|---|
| residues | 26 | **26** |
| RMS spread | 9.85 Å | **10.15 Å** (matched ±0.5 Å) |
| overlap | — | **0 residues** |
| angle about the centroid | 0° | **165.9°** |
| the 18 existing conditioned backbones score | 0.712 | **0.000** |

That last row is the one that makes the run interpretable: an arm aimed at the real epitope
never touches the decoy, so the two faces separate **in practice**, not just on paper.

**Known limitation, recorded rather than designed away.** The nearest decoy↔epitope residue
pair is **4.9 Å** centroid to centroid (mean 19.4 Å) — the patches share an edge, so a dock
straddling the boundary could partially satisfy both. Pushing them further apart on a
113-residue IgV domain costs either the size match or the spread match.

### Pre-registered reading, fixed before the run

| outcome | meaning |
|---|---|
| high on decoy, low on epitope | conditioning works; the published result is about our hotspots |
| **both low** | the decoy face is not dockable — **INCONCLUSIVE, not a pass** |
| epitope still ≈ 0.712 | **the published result is refuted** — it was reading RFdiffusion's prior |

The middle row is the one that matters and it is why this is written down now: a null result
here does **not** rescue the claim.

---

## 4. Control 2 — finish the unconditioned arm

18 unconditioned backbones already exist (`runs/challenge2_pod/c2/unconditioned/`). Their
targeting baseline is **already computed locally** —
[`results/unconditioned_baseline.md`](../results/unconditioned_baseline.md):

| arm | n | mean `frac_iface_on_epitope` | sd |
|---|---|---|---|
| conditioned | 18 | **0.712** | 0.113 |
| unconditioned | 18 | **0.500** | 0.168 |

(0.500 reproduces the 0.501 the 2026-09-21 pilot reported. It is not zero and should not be:
the epitope is 26 of 113 residues, so a random patch captures roughly a quarter of any
interface — the denominator, not a result.)

What is missing is **scores**: ipSAE, DockQ, interface pLDDT. Without them the conditioned
pool's flat ~8% viability per sequence (χ² = 22.91 on 17 df, p = 0.152) cannot be told apart
from "the `interaction_pae` selection was noise (ICC 0.000) and the pool was never sorted".

---

## 5. Running it

```bash
# 1. On the pod, after pod/00_setup.sh has built inputs/pd1_T.pdb and framework.pdb:
scp pod/inputs_decoy_hotspots.txt  pod:$RFAB/inputs/decoy_hotspots.txt
scp -r runs/challenge2_pod/c2/unconditioned/*.pdb  pod:/workspace/c2_decoy/uncond_bb/

# 2. One command. Resumable — it keys on artefacts, so a dropped connection costs nothing.
bash pod/02_decoy.sh                      # ~1 GPU-hour

# 3. Retrieve, then locally:
uv run python scripts/95_decoy_patch_control.py --analyse runs/challenge2_decoy/bb
```

**Retrieve `$WORK/bb`, `$WORK/seq_uncond`, `$WORK/*.jsonl` and `$WORK/logs`** — the logs
matter, because this is the project where a tool announced that it had discarded an input on
a stdout stream the harness threw away.

Before deleting the pod, checksum what you pulled (`scripts/71_verify_pod_checksums.py`
matched 258/258 last time).

---

## 6. What is stubbed, plainly

- **Nothing here folds anything.** Folding the unconditioned sequences reuses the existing,
  validated path (`scripts/72_challenge2_fold.py`), whose input directory is hardcoded to
  the conditioned arm's `seq/`. Either parameterise it or stage the new sequences into that
  layout. Writing a second, untested fold driver to save one edit would be worse.
- **`pod/02_decoy.sh` has never executed.** It is `01_run.sh` with the decoy hotspots, block
  A trimmed to RFdiffusion, and a ProteinMPNN block added; `bash -n` passes and the ordinals
  are asserted equal to `results/decoy_patch.json`, but that is syntax and consistency, not a
  run.
- **The 4.9 Å shared edge** between the patches (§3) is a real limitation, not a rounding
  detail.
