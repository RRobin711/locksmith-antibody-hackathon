---
date: 2026-09-15
tags: [project, problem, coding, python, learning]
status: living
---

Tags: [[Problem|problems and debugging]] · [[Coding|coding]] · [[Python|Python]] · [[Learning|things I'm learning]]

# The Environment Saga

**Why this note exists:** roughly half the elapsed time on day one went into getting software to
run at all, not into science. That is normal and worth documenting honestly, because the
failures were instructive and because someone reproducing this work will hit the same walls.

Each section follows the same shape: **symptom → real cause → fix → what it generalises to.**

---

## 1. The numpy fault line

**Symptom:** installing the scoring tools produced an unsatisfiable dependency conflict.

**Real cause:** the tools disagree about a foundational library.

| Tool | Requires |
|---|---|
| PRODIGY (binding energy) | `numpy >= 2` |
| DockQ (pose comparison) | `numpy < 2` |
| Boltz-2 (structure prediction) | `numpy < 2` |

NumPy 2.0 was a breaking release. These are not negotiable pins; they reflect genuine
incompatibilities. **The tools physically cannot share an environment.**

**Fix:** four isolated Python environments — one for our own code, one each for the conflicting
tools — with our metric modules invoking them as subprocesses and parsing their output.

**Why this turned out to be right rather than merely necessary:** the organisers recompute six
of the eight metrics from our submitted files. So *version agreement with them* matters more
than convenience. Separate environments let each tool be pinned independently to whatever
version we think they run. The subprocess boundary is not a workaround to apologise for; it is
the mechanism that makes independent pinning possible.

It also paid off twice — the architecture was designed for two conflicting tools, and absorbed
a third without any change when Boltz turned out to need `numpy < 2` as well.

**Generalises to:** when a dependency conflict is genuine, process isolation beats version
negotiation — and often buys you something you wanted anyway.

---

## 2. A C extension needing headers we didn't have

**Symptom:** `freesasa` (surface area calculation) failed to build: *"you need a library that
provides Python.h"*.

**Real cause:** it compiles from C source and needs Python's development headers. The system
Python ships without them; installing them requires root.

**Fix:** rather than requiring `sudo`, we rebuilt the environment on `uv`'s **managed** CPython,
which ships headers. Previously downloaded packages came from cache, so the rebuild cost
seconds.

**Generalises to:** a managed toolchain-provided interpreter is often a cleaner escape from
system-package problems than escalating privileges.

---

## 3. The four-attempt fold

Getting one structure prediction to run took four attempts, each failing for a genuinely
different reason. This is the part most worth reading.

### Attempt 1 — host RAM exhausted

**Symptom:** the job was killed partway through.

**Real cause:** the machine has 15 GiB of RAM and roughly 9 GB was held by a browser and chat
applications. Boltz loads about 4 GB of model weights on top.

**My contribution, stated plainly:** I was simultaneously running three separate decompressions
of a 6 GB archive to inspect its contents. Each streams the whole file. That page-cache churn,
on top of the model loading, is what tipped it over. I should have extracted once, and certainly
not while a memory-sensitive job was starting.

**What survived:** the model weights and the sequence alignments had already downloaded and were
cached, so the expensive parts did not need repeating.

### Attempt 2 — a missing GPU kernel, reported as success

**Symptom:** `ModuleNotFoundError: No module named 'cuequivariance_torch'` — **and exit code 0**.

**Real cause:** Boltz offers optional CUDA kernels for one of its expensive operations. I had
deliberately skipped installing them, reasoning they might not support our GPU's new
architecture and would fail in a harder-to-diagnose way. Boltz tried to import them anyway
rather than falling back.

**Fix:** `--no_kernels`, forcing the pure-PyTorch path. Slower, but it runs.

### Attempt 3 — GPU memory exhausted, also reported as success

**Symptom:** again exit 0, this time with a `100%` progress bar and, buried in the log:

```
OOM on device 0 while trying to allocate 1616904192 bytes
free: 882376704, total: 12346195968
| WARNING: ran out of memory, skipping batch
Number of failed examples: 1
```

**Real cause:** **GPU VRAM**, not host RAM. Two entirely different resources, and I had been
treating "out of memory" as one problem. All the swap work in §4 addressed the *host* side; the
actual wall was the graphics card. Swap cannot help with VRAM at all.

**Fix — and this is the satisfying part:** the memory went into the sequence alignments, and
Boltz was building deep ones for all three chains. But
[[How Structure Prediction Works|antibody chains should not have alignments at all]]. Removing
them was **both the scientifically correct protocol and a two-thirds cut in the memory that was
blowing up** — right thing and cheap thing coinciding.

### Attempt 4 — success

34 seconds. Structure, confidence matrix, and per-residue confidence all written.

### Postscript — scoring then failed on a filename

Not a fold failure, but part of the same evening: the ipSAE tool located its confidence data by
string-substituting the filename, and our copy-and-rename broke it. Covered as trap #7 in
[[Eight Silent Failures|the traps note]].

**What the four attempts generalise to:** "out of memory" is at least two different problems on
a GPU machine, and they have different fixes. And **three of the four failures reported success
or said nothing useful** — which is what turned "check the artefacts, not the exit code" from a
nice principle into a hard rule.

---

## 4. The swap detour

**Symptom:** after the first kill, we wanted more memory headroom so long jobs could survive a
spike instead of dying.

**Background:** **swap** is disk space the kernel uses as overflow when RAM fills. Pages that
aren't being actively used get written out to make room. It is much slower than RAM, but the
alternative when everything is full is that the kernel picks a process and kills it.

**First attempt, and why it stalled:** the obvious approach is to resize the existing 8 GB swap
file, which requires turning swap off first. But `swapoff` has to fault **every swapped-out page
back into RAM**, one at a time — 3.2 GB of it. That takes minutes and looks exactly like a hang.
Interrupting it left swap enabled (safely — the subsequent commands correctly refused to touch a
live swap file) but unresized.

**The real fix:** don't resize. **Linux happily uses multiple swap files**, so add a second one
alongside the first. No `swapoff`, no waiting, no risk:

```bash
sudo fallocate -l 16G /swap2.img
sudo chmod 600 /swap2.img
sudo mkswap /swap2.img
sudo swapon /swap2.img
```

About five seconds, because `fallocate` on ext4 reserves extents without writing anything.
Result: 8 + 16 = **24 GB total swap**.

We also set `vm.swappiness=10`. The default of 60 makes the kernel swap fairly eagerly even when
RAM is available, which is backwards for this workload — paging during inference is brutally
slow. We want swap sitting there as emergency overflow, not as routine paging.

**Generalises to:** when the obvious operation is slow because it must migrate state, look for
the version that adds capacity instead of moving it. *Additive beats mutative* — and this is a
general pattern, not a Linux one.

---

## 5. Two mistakes of mine worth recording

**Killing my own shell.** Cleaning up an orphaned process, I ran `pgrep -f 'bolt[z]'` — using a
character class specifically so the pattern would not match the command running it, a trick
already documented in my own notes. Then I undermined it by writing the plain word in an `echo`
in the *same* command. My shell's command line contained the literal string, the regex matched
it, and I killed myself. Exit 144.

**The trick only works if you apply it everywhere in the command, not just at the pgrep.** The
robust version excludes `$$` and `$PPID` explicitly and keeps the literal string out entirely.

**Assuming instead of measuring.** The three concurrent archive scans in §3 were not a tooling
failure; they were me being careless about resource contention while a fragile job was starting.

Both are in here because [[Eight Silent Failures|the traps note]] would be dishonest if it only
catalogued other people's software behaving badly.

---

## 6. What the environment cost, and what it bought

Roughly half of day one. In exchange:

- a verified GPU stack on a brand-new architecture (Blackwell needs CUDA ≥ 12.8; verified not by
  `is_available()` but by a real matrix multiplication checked against the CPU)
- four isolated environments that will absorb further conflicts without redesign
- 24 GB of swap, so long jobs no longer die on a spike
- **34 seconds per fold** — which, against our compute budget, is roughly 4,700 folds rather
  than the 1,400–1,800 we had planned for, on the *slow* code path

That last number changes the design space materially. It is the kind of thing you only learn by
getting the environment working and measuring, rather than estimating.

---

**Related:** [[Eight Silent Failures|the scientific traps]] ·
[[How Structure Prediction Works|what the folding model does with all that memory]]
