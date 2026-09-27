# Batching is 1.65× and produces different structures. Staggering is safe and 1.30×.

**2026-09-24.** Both arms, same 4 designs, diffed byte-for-byte against stored serial
artefacts. Serial folds are bit-identical (`runs/determinism/`), so this is a straight diff.

## The two-phase profile that motivated both

A serial fold is 171 s, and the phases are cleanly separated:

```
  t=0–78 s     GPU 0 MiB, utilisation 0–5%     CPU: model load + featurisation
  t=78–171 s   GPU 5,342–5,392 MiB, 98–100%    GPU: trunk + diffusion
```

**46% of every fold does not touch the GPU.** The "53.5% mean utilisation" reported earlier
was not a half-stalled GPU — it was a GPU idle for the first 78 seconds.

## Results

| arm | total | per fold | speedup | GPU peak | max CUDA procs | RSS peak |
|---|---|---|---|---|---|---|
| serial (reference) | — | 171.0 s | 1.00× | 5,392 MiB | 1 | — |
| **batching** (1 invocation, dir of 4) | 414.0 s | 103.5 s | **1.65×** | 8,202 MiB | 1 | 8,444 MB |
| **staggering** (2 workers, 80 s offset) | 526.6 s | 131.7 s | **1.30×** | **5,558 MiB** | 2 | 11,751 MB |

## Byte verification — and this is the result that matters

| arm | bytes identical | PAE identical | max Δxyz |
|---|---|---|---|
| staggering | **4/4 designs** | **4/4** | **0.000 Å** |
| batching | **1/4** | 1/4 | **72–89 Å** |

**Batching changes the science.** Chain names and lengths are identical, so this is not a
comparison artefact:

| design | ipSAE serial | ipSAE batched | Δ |
|---|---|---|---|
| bb_1_0 | 0.6089 | **0.8912** | **+0.28** |
| bb_2_0 | 0.2993 | **0.0233** | **−0.28** |
| bb_3_0 | 0.8162 | 0.8162 | 0.000 |
| bb_4_0 | 0.3071 | **0.0117** | **−0.30** |

One design gains 0.28, two collapse by ~0.29, one is untouched.

> **Mechanism WITHDRAWN 2026-09-26.** This paragraph asserted that Boltz pads a batch to
> its longest sequence and that a design's score therefore depends on which other designs
> share its batch. **The four folds ran 94 s apart, so no batch ever formed** — padding
> cannot be the explanation. The corruption is real and the arm stays disqualified; **the
> cause is unknown and we are not going to invent one.** See
> [the register, §B9](retractions.md).

That is disqualifying regardless of speed. A sweep run this way would produce numbers that
cannot be compared with the re-screen, the paired test, the matched control, or each other
— and the corruption is invisible: every file is present, every score is plausible, and one
design in four is bit-perfect.

## Staggering works exactly as designed, and the memory proves it

Peak GPU memory across both processes was **5,558 MiB** — only 166 MiB above a *single*
fold — despite **27 sampled seconds with two CUDA processes resident**. The second process
was in its CPU phase (0 MiB on the GPU) whenever the first was computing. The GPU phases
never coincided, so the feared ~11.5 GiB transient never occurred.

Headroom against the 12,227 MiB card: **6,669 MiB**. The concern that motivated the iGPU
question does not arise.

Its speedup is only 1.30× rather than the 1.84× the phase profile predicts, because the
offset drifts as folds finish at slightly different times and the phases partially
re-align, costing contention.

## Decision

Pre-registered rule: *either arm ≥1.5×, byte-identical, and ≥1 GB headroom → A+B+C;
otherwise A+B serially.*

- **Batching**: 1.65× ✓, headroom ✓, **byte-identical ✗** → rejected
- **Staggering**: byte-identical ✓, headroom ✓, **1.30× < 1.5×** ✗

**Neither qualifies. Running A+B serially.**

## What this says about faster hardware

The A100 estimates quoted earlier were overstated, and by a knowable amount. A faster card
shortens the **93-second GPU phase** and leaves the **78-second CPU phase** alone. Even an
infinitely fast GPU caps the speedup at 171/78 = **2.2×**, and a realistic 2× on the GPU
half gives 171 → 124.5 s, i.e. **1.37×**, not the 1.5–2× extrapolated from raw specs.

**The binding constraint on this pipeline is CPU-side model loading, not GPU throughput.**
