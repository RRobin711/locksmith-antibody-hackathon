# Calibrating the rubric against things that should fail

**2026-09-22.** Building two experiments this project should have run in its first
week: a **negative control** (does the viability gate reject an antibody that cannot
bind?) and a **calibration panel** (where do our numbers sit among real complexes?).
Plus one genuine bug found in our own resume logic, which is the most transferable part
of the session.

Self-contained: concepts are defined here from first principles. Where an earlier
session covered something more fully it is restated briefly and linked, not assumed.

---

## 1. The problem both experiments attack

Every number this project reports is **uncalibrated and unfalsified**.

*Uncalibrated*: "ipSAE 0.864" is not a result. A reader cannot know whether the metric
saturates at 0.9 or runs to 1.0, whether real antibody–antigen complexes cluster at 0.5
or 0.95, or how far 0.864 is from noise. The handbook's band edge at 0.80 is **asserted**.
Nobody has ever located it in a distribution.

*Unfalsified*: we had shown our designs **clear** the §7.2 gates. We had never shown that
anything **fails** them. A gate that nothing fails is not a filter; it is a formality.

These are the same defect seen from two sides: a threshold means nothing until you know
what sits either side of it.

### Jargon, defined once

- **ipSAE** — a confidence score derived from Boltz's **PAE** (Predicted Aligned Error:
  the model's own estimate, in ångströms, of how wrong the relative placement of two
  residues is). ipSAE applies a **hard cutoff at PAE < 10 Å** and scores only pairs
  inside it, which is why it floors hard at exactly 0.000 rather than decaying smoothly.
- **DockQ** — a 0–1 pose-accuracy score comparing a predicted complex to a **known
  crystal structure**. Unlike every other metric here it reads external truth, so it
  exists only where a crystal exists — i.e. never for a de novo design.
- **§7.2 hard cutoffs** — the handbook's pass/fail viability gate, five thresholds:
  ipSAE ≥ 0.60, ΔG ≤ −6.0 kcal/mol, contacts ≥ 10, interface pLDDT ≥ 65, CDR SASA > 250 Å².
- **Fv** — the variable domain pair (VH+VL), the ~230 residues that actually bind.
  A **Fab** additionally carries the constant domains (~440 residues total).
- **Epitope** — the residues on the antigen that the antibody touches. Here: heavy-atom
  contacts within 4.5 Å.

---

## 2. Negative control: design

**The question.** If a real antibody with a completely unrelated target is docked onto
PD-1, does it fail the gate?

**The design principle is one variable.** In the calibration panel every complex has a
different antigen, so the antigen's alignment differs row to row and is a nuisance
variable. Here the antigen is held **byte-identical**: the same 113-residue PD-1, the
same cached alignment (`data/msa_cache/pd1_5ggs.csv`, 3787 sequences), the same flags,
`recycling_steps=10`, `diffusion_samples=5`. Antibodies are trimmed to Fv by ANARCII.
**Only the antibody changes**, so any difference is attributable to it and nothing else.

| arm | antibodies | expectation |
|---|---|---|
| negative (n=6) | HyHEL-10 (lysozyme), trastuzumab (HER2), bevacizumab (VEGF-A), cetuximab (EGFR), CR9114 (influenza HA), BO2C11 (factor VIII) | FAIL |
| positive (n=2) | pembrolizumab, nivolumab | PASS |

**Why both arms are mandatory.** A uniform failure with no working positive is not
evidence of discrimination — it is evidence the pipeline is broken. This project has
already published a "0/30 viable" that was the sampler's floor rather than a finding.
The pre-registration (`results/prereg_2026-09-22_calibration_and_negative_control.md`)
fixed three rules **before** any fold completed:

1. positives pass and negatives fail → the gate discriminates;
2. any negative passes → the gate does not measure binding;
3. **any positive fails → INCONCLUSIVE**, and the negative arm licenses nothing.

**Why the point estimate was fixed in advance.** The median over five diffusion samples,
not the maximum. Choosing max-vs-median after seeing the data is exactly how a null
becomes a finding by accident.

---

## 3. Negative control: the argmax result

Boltz emits diffusion samples **ranked by its own confidence**. Therefore `model_0` under
the default `diffusion_samples=1` is **the maximum of a distribution that was never
drawn** — an order statistic, not a sample. (Established previously; see
[the diffusion-sampling experiment](../../results/diffusion_samples_2026-09-22.md).)

**HyHEL-10, an antibody raised against hen egg lysozyme, docked onto PD-1, `model_0`:**

| metric | value | §7.2 cutoff | |
|---|---|---|---|
| ipSAE | 0.609 | ≥ 0.60 | pass |
| ΔG | −12.4 kcal/mol | ≤ −6.0 | pass (**Good** band) |
| contacts | 77 | ≥ 10 | pass |
| interface pLDDT | 85.0 | ≥ 65 | pass (**Good** band) |
| CDR SASA | 1084 Å² | > 250 | pass |

**A clean sweep of the entire gate set by a molecule that cannot possibly bind.** Its
median over five samples is ipSAE **0.219** — it fails comfortably once you actually
sample. The five draws were 0.609 / 0.219 / 0.227 / 0.087 / 0.081, and Boltz's own
confidence ranking put the outlier first.

**The mechanism, stated generally.** The maximum of *k* draws from a broad low
distribution routinely exceeds a threshold the distribution's centre is nowhere near.
With five draws the expected maximum sits roughly at the 83rd percentile of the sampling
distribution. **The gate is not broken; reading it off one diffusion sample is.**

### The stronger, more general result

| §7.2 cutoff | negatives rejected (median of 5) |
|---|---|
| ipSAE ≥ 0.60 | 6/6 |
| ΔG ≤ −6.0 | **0/6** |
| contacts ≥ 10 | **0/6** |
| interface pLDDT ≥ 65 | **0/6** |
| CDR SASA > 250 Å² | **0/6** |

**Four of the five gates reject nothing.** Every irrelevant antibody clears them, because
they are satisfied by any two proteins the predictor places in contact at all. They
measure *that a complex was built*, not that it is the right one. **The §7.2 viability
decision rests on ipSAE alone**; the other four supply the appearance of a five-way check.

This is a criticism of the thresholds, not the quantities. ΔG, contact count, interface
pLDDT and buried CDR surface are fine descriptive measures — they just cannot function as
pass/fail gates at values that sit below what a docked-but-wrong complex achieves.

And the margin on the one gate that works is thin: **cetuximab's median is 0.594** against
a 0.60 cutoff. Six thousandths.

---

## 4. The positive control failed — and the diagnosis is the best part

**Nivolumab scored ipSAE 0.017** (max 0.263). Rule 3 fired: the experiment is
**inconclusive as pre-registered**, and that stands.

Two stories were available — "the pipeline is broken" and "nivolumab is a hard case" —
and **neither is evidence**. The question is answerable with **no folding at all**: take
each antibody's own crystal, list the PD-1 residues it contacts, and ask how many exist
in the construct we fold.

```
pembrolizumab (5GGS)  epitope 26 residues   folded 113-mer covers 26/26 (100%)
nivolumab     (5WT9)  epitope 14 residues   folded 113-mer covers  8/14 (57.1%)
                                            MISSING: L25 D26 S27 P28 D29 R30
```

**43% of nivolumab's binding site is not in the molecule we docked it against.** Its
epitope is dominated by PD-1's N-terminal `LDSPDR` loop; our construct begins at `PWNPP`
(residue P31).

5GGS holds **two independent copies** in the asymmetric unit and their epitopes differ —
chain Z (with Fab A/B) contacts 26 residues, chain Y (with Fab C/D) contacts 24. Both are
real; the difference is which side chains each copy resolved. The larger is used, because
for a question of the form *"how much of the epitope is missing from our construct?"* the
bigger epitope is the conservative choice. Reporting "the first chain that matched" would
have made the number depend on chain iteration order, which is not a measurement.

**Why this was invisible for the whole project.** The 113-mer was inherited from the 5GGS
(pembrolizumab) construct and never re-examined. Pembrolizumab's epitope is 100% inside
it — so *the only reference antibody ever folded was the one incapable of detecting the
truncation.* A control eliminates the confound you thought of and is silent on the one you
did not.

### The second consequence — and my own error in stating it

I first wrote that **every** fold in this project used the 113-mer, so that "every number
in the submission was measured on a molecule six residues shorter than the one shipped
beside it." **That is false and is corrected here.** The packaged Challenge 2 structure has
a 123-residue antigen; the sequon-fix run that produced it
(`runs/sequon_fix/sq_sa/sq_sa.fasta`) folded the handbook's 123-mer. I inferred "every
fold" from the screening FASTAs without checking the one that actually produced the
deliverable — the same failure I had just documented in someone else's code, committed
within the hour.

The accurate statement is narrower and still a defect:

- **screening and selection** ran on the 113-mer (`runs/batch_verify`,
  `runs/challenge2_fold_r10`), and so does tonight's negative control;
- the **shipped structures** were folded on the 123-mer.

So candidates were *ranked* against one antigen and the winner *scored* against a
different one. Nothing compared them, and the difference is invisible to pembrolizumab —
the only reference ever folded — because its epitope lies entirely within both.

### A worse consequence, and why it is being tested rather than asserted

`data/msa_cache/pd1_5ggs.csv` is aligned to the **113-residue** query. The shipped fold
passed that cache alongside the **123-residue** antigen. Boltz did not complain, and the
alignment it wrote is **113 columns wide for a 123-residue chain**
(`processed/msa/sq_sa_0.npz`, `res_end - res_start = 113`), with the cached query sitting
at **offset 5** inside the folded sequence.

Whether Boltz re-aligns the cached MSA by sequence or maps it positionally from index 0 —
in which case the antigen alignment is out of register by five residues across the whole
chain — **cannot be settled by reading the file**, which records widths and offsets but
not the mapping policy. Inferring a policy from an artefact is precisely how the three
wrong answers above were produced.

`scripts/94_msa_register.py` settles it in three folds, all else identical:

| arm | antigen | alignment | isolates |
|---|---|---|---|
| `as_shipped` | 123-mer | cached 113-column | reproduces the shipped fold |
| `matched_113` | 113-mer | cached 113-column | the **register**, alignment held fixed |
| `matched_123` | 123-mer | fresh query for that sequence | the **construct** |

Decision rule, fixed before running: `~=` means inside this design's measured diffusion
envelope (composite 91.2 on all five samples, ipSAE 0.619–0.781). If all three agree,
Boltz re-aligns and the shipped structure is sound. If `as_shipped` differs from both
others, the shipped Challenge 2 structure was predicted under a misaligned antigen
alignment and every metric derived from it inherits that — which would be the most serious
defect found in this submission.

### How far does the damage reach? Bounded, and in our favour

The same calculation run against the **PD-1/PD-L1 complex (5IUS)** — the face a checkpoint
inhibitor must occlude, and the face our Challenge 2 design was conditioned on — gives a
23-residue footprint of which the folded 113-mer contains **23/23 (100%)**. So the
truncation damages nivolumab, which binds the N-terminal loop, and touches neither
pembrolizumab's epitope nor the therapeutic target face. **Our own numbers are not
affected by it.** That is worth computing rather than assuming: the alternative — that we
had been folding against a construct missing part of our own target epitope — would have
invalidated the whole project, and it takes one script to rule out.

### Method note: match by sequence, never by residue number

Two traps were hit building this and both produce a plausible wrong number silently.

**(1) Every chain over 80 residues is not "the antibody."** In a crystal with two copies in
the asymmetric unit that sweeps in the second Fab *and the second PD-1 copy*, so
lattice-packing contacts get counted as epitope. Partners are instead required to make ≥5
contacting residues with *this* PD-1 copy, which a genuine binding partner clears easily
and a lattice neighbour does not.

**(2) A long sequence probe fails on any crystal with a disordered loop inside it.** A
single 30-residue probe silently returned "no PD-1 chain here" for 5IUS — whose PD-1 has
an unresolved gap in that window — and the entry was skipped without comment. Replaced by
six 12-mers spread along the sequence, requiring any two to match.

Epitope coverage is computed by locating the construct **inside each crystal's PD-1 chain
by exact substring match**. PD-1 is numbered differently between entries, and matching on
residue number is the identical error this project has a standing rule about for
RFdiffusion hotspots — it returns a confident zero that looks like a scientific null.

### The follow-up, labelled as such

A second experiment (not a retraction) refolds all rows against `LDSPDR` + the 113-mer =
**119 residues, PD-1 25–143** — the minimal change restoring nivolumab's epitope to
14/14 while leaving every previously-used residue in place.

The cached alignment is aligned to the 113-mer query and **cannot** be reused against a
longer one, so every row takes a fresh MMseqs2 query. That is acceptable *only because the
antigen is byte-identical across rows*, so the server returns the same alignment to each —
unlike the case the cache was built for, where differing antigens would pull differing
alignments into a ranking. The assumption is not assumed: **per-row alignment depth is
recorded and compared**, and a mismatch is reported rather than swallowed.

**Prediction, stated before the result:** if the diagnosis is right, nivolumab clears the
gate on the 119-mer and the negatives still fail. If nivolumab still fails, the diagnosis
is wrong or incomplete and gets reported as an open question.

---

## 5. The bug: a resume check that silently discarded finished work

Four driver scripts each grew this:

```python
try:
    assert_artefacts(d, label)          # WRONG — not the signature
    return True
except Exception:                       # swallows the TypeError
    return False
```

The real signature is `assert_artefacts(pdb, pae, plddt, *, label, stdout="")`. The call
raised `TypeError`; the bare `except Exception` read it as **"not folded yet."**

**Why it survived.** The failure mode is invisible *in the direction it failed*: re-doing
finished work looks exactly like doing work. It surfaced only because a log line said
`40 in panel, 0 already folded` for a panel with one complex demonstrably folded and
scored.

**The asymmetry that makes this a class of bug, not an incident.** Had the swallowed
exception meant "done", the same defect would have **skipped every fold** and produced an
empty panel that looked complete. Same typo, same `except`, opposite and far worse
outcome.

**The rule.** A resume predicate must distinguish *"the artefacts say no"* from *"the check
itself is broken."* Catch only the exception that means absence; let every other exception
propagate.

Fixed as `locksmith.fold.fold_is_complete(pred_dir, label, n_models=...)`, which catches
only `FoldFailed`, and pinned by
`tests/test_invariants.py::test_fold_is_complete_distinguishes_absent_from_broken` —
including a case asserting a monkeypatched `TypeError` **propagates** rather than
returning False. Suite: 29 → **30 tests**.

---

## 5b. The second bug: 20% of DockQ natives paired the wrong copy

`classify()` picks the first heavy chain, the first light chain and the first
non-antibody chain it meets. **Nothing required them to be the same copy.** In a crystal
with two complexes in the asymmetric unit that silently pairs an Fv from copy 1 with the
antigen of copy 2, and the resulting "native" contains no antibody–antigen interface at
all.

**Measured: 8 of 40 natives (20%) had the wrong antigen copy.**

```
7ST5 F->A (24 contacts)   8ATH A->B (15)   7Z2M G->K (25)   8EB2 A->D (17)
8DFG B->A (17)            8G4T A->F (13)   8W83 C->D (17)   8W84 C->D (18)
```

**How it was caught, and why it nearly wasn't.** 7ST5 reported no DockQ value while
scoring **ipSAE 0.819**. That combination is contradictory: a high confidence score means
the chains *are* in contact, so a missing interface had to be the native's fault rather
than the prediction's. Running DockQ by hand printed the giveaway —
`Total DockQ over 1 native interfaces`, the heavy–light framework only.

**The thing that saved this was `dockq.compute` returning `None` with a reason instead of
`0`.** A zero would have been indistinguishable from a genuine docking failure and would
have injected eight fabricated catastrophes into the panel distribution. After the fix
7ST5 scores **DockQ 0.857** — not a failure at all, but one of the best predictions in
the panel. Dropping it had been biasing the distribution *downward*.

**Scope, established rather than assumed.** This affects only the DockQ native, **not the
folds**: copies of a molecule have identical sequences, so what was folded is the right
complex either way. The same contact test doubles as a validity check on the panel itself
— a row whose folded "antigen" does not touch its Fv in the crystal would mean we had
folded a pair that is not a complex. **0 of 40 were refused**, so every row is genuine.

**The general principle.** *A metric that returns "I could not measure this" is worth far
more than one that returns a plausible number.* Three silent-failure classes turned up in
one session — a resume check reading a `TypeError` as "not done", a sequence probe reading
a disordered loop as "chain not found", and a chain selector pairing molecules that never
touch. **Every one produced a well-formed, plausible, wrong answer**, and each was caught
only by an inconsistency between two numbers that should have agreed.

---

## 5c. Two infrastructure failures overnight, and one of them refutes a rule we wrote

### `nohup setsid` does not survive systemd-oomd

The fold chain was launched with this project's documented overnight pattern:

```
nohup setsid systemd-inhibit --what=sleep:idle:handle-lid-switch --why="…" cmd > log 2>&1 &
```

At **01:06:59** it died at 31 of 40 folds. `journalctl` gives the cause exactly:

```
vte-spawn-0213d043-….scope: systemd-oomd killed 27 process(es) in this unit.
vte-spawn-0213d043-….scope: Failed with result 'oom-kill'.
    Current Memory Usage: 8.2G     Pressure: Avg10: 54.76
```

**`setsid` detaches a process from its controlling TERMINAL. It does not move it out of
the terminal's CGROUP.** systemd-oomd selects and kills by cgroup, so every `setsid`'d
child of a terminal dies with that terminal's scope. The `systemd-inhibit` in the same
pattern is orthogonal — it blocks *suspend*, not an OOM kill — so the documented pattern
protects against exactly the two failure modes that did not happen.

Machine: 15 GiB RAM, and the terminal's cgroup held Boltz plus a 6-thread scorer plus the
agent session.

**The fix is a different cgroup, not a bigger machine:**

```
systemd-run --user --unit=locksmith-folds  ./scripts/run_remaining.sh
```

A transient unit lands in `/user.slice/user-1000.slice/user@1000.service/app.slice/…`,
independent of any terminal. Sleep inhibition becomes a second unit whose lifetime is tied
to the first, rather than a wrapper inside the doomed scope.

**What made this cheap:** every stage keys resume on artefacts, so restarting cost only
the unfinished 8 folds. And note which source was right — **the log said fold 32 never
finished** (its `ok in` line was never flushed), while **the artefacts said it did**, with
all five models present and scorable. A log-keyed resume would have refolded a complete
fold; `fold_is_complete` did not. That is the §5 rule paying for itself within hours.

### `pgrep -f` self-matched for the seventh time — in my own health check

Checking whether the chain had survived, I ran `pgrep -f "boltz predict"` inside a shell
command *whose own command line contained the string `boltz predict`*. It reported the job
**ALIVE** on a machine where `ps` showed no boltz process and `nvidia-smi
--query-compute-apps` showed nothing on the GPU.

This project has a hook and six recorded instances for exactly this, and the pattern still
caught me, because a health check feels too small to need discipline. The replacement
watchdog reads the **systemd unit state**:

```
systemctl --user is-active --quiet locksmith-folds.service
```

which is authoritative, cannot match itself, and distinguishes *stopped* from *between
folds* without any string matching at all. **When a supervisor exists, ask the supervisor.**

### And the watchdog that would have caught it had died with the session

The stall watchdog armed earlier — 20 minutes without a completed fold — was a
Claude-managed background shell, so it was killed by the same OOM event as the job it
was watching. **A watchdog inside the thing it watches is not a watchdog.** The current
one is armed the same way, which is honest about its limits: it catches a hung job, not a
dead machine. Surviving the supervisor is what the systemd unit is for.

---

## 6. Calibration panel: design

40 real crystallised complexes, folded through the identical pipeline and scored on the
same six metrics, so every submission number can be quoted as a percentile.

### The split that makes it meaningful

Boltz-2's training cutoff is **2023-06-01 on PDB *release* date** (release, not
deposition; read from the paper). Mixing memorised and novel complexes produces a
distribution that means nothing, because they are different tasks:

- **pre-cutoff (n=20)** — the model has seen these. The **ceiling**: what the metrics look
  like when prediction is closer to recall.
- **post-cutoff (n=20)** — genuinely novel. The **honest bar** for a de novo design.

### Why both arms are drawn from either side of one date

Both come from **one RCSB query** sorted by release date, taking entries **nearest the
cutoff on each side**. If the pre arm were 1990s structures and the post arm 2025 ones,
they would differ in resolution, refinement practice, construct design and target fashion
as well as memorisation — and any gap would be uninterpretable. Sampling either side of a
single date makes the cutoff close to the only systematic difference. **This is the whole
design; the rest is plumbing.**

Filters, identical for both arms: ≥3 protein entities, resolution ≤ 3.0 Å, deduplicated on
antigen sequence so ten Fabs against one spike protein cannot pose as ten calibration
points.

### Construct discipline, and why each rule exists

- **Chains typed by ANARCII, never by letter.** 5GGS puts a second heavy chain in `C`.
  Chain IDs are not a convention anyone agreed to.
- **Antibodies trimmed to Fv**, because our designs are Fv. A panel folded as Fab is not
  the same pipeline — measured on the same real pair, Fab ipSAE 0.776 vs Fv 0.842.
  Trimming also discards the constant domain, where most crystallographic disorder lives.
- **Antigen rebuilt from SEQRES, trimmed to the resolved span.** A coordinate-derived
  sequence with an internal deletion is a chimera: folding it predicts a protein with a
  loop excised and the ends fused, an error that moved one DockQ **0.064 → 0.370**.
  Terminal truncation is harmless (the crystal simply did not resolve the ends) and is
  left truncated, so no GPU time is spent folding unobserved tags.

The guard bites hard and that is correct: **12 of 21 first-pass candidates had internal
gaps.** The fix is SEQRES, not relaxing the guard.

### Sampling depth

`recycling_steps=10`, `diffusion_samples=5`. Recycling 3 (the inherited default) does not
give a noisy ranking, it gives a **compressed** one — at recycling 3, 15 of 30 designs
scored exactly 0.000 and the pool read as 0/30 viable. A panel folded under-converged
would measure the sampler's floor rather than the metric's distribution.

### Reporting rules fixed in advance

- Per complex: **median over five diffusion samples** (`model_0` would compare our maximum
  to other complexes' maxima — self-consistent, but inflating everything and hiding the
  variance that matters).
- Percentiles as **ranks** ("3rd of 20"). At n=20 a percentile has 5-point resolution and
  a 95% CI near ±20 points at the median; a decimal percentile implies precision the
  sample size cannot support.
- **Power stated up front**: n=20/arm gives ~80% power for a rank-biserial around 0.6.
  **A null here means "no effect larger than large", not "no effect".** This project has
  four times reported an underpowered null as a finding.

### First data point, and what it warns about

7ZOZ (post-cutoff, real crystal): median ipSAE **0.015**, DockQ **0.377**, 59–86 contacts,
interface pLDDT 76–78. A real complex with a genuinely acceptable pose, near the ipSAE
floor. Within it, `model_3` has the **best** DockQ (0.699) and nearly the **lowest** ipSAE
(0.011).

**The expected failure mode, written before the panel finished:** if much of the
post-cutoff arm sits near the ipSAE floor, the honest conclusion is about the metric, not
the designs — and the check is whether DockQ and contact count agree. A complex with a
real interface (contacts > 40, DockQ > 0.23) and ipSAE ≈ 0 is evidence the gate is
mis-scaled, not that the crystal is wrong.

---

## 7. Honesty ledger

**Disclosed in the pre-registration:** one complex (7ZOZ) was folded and scored **before**
the document was written, as a timing test to size the GPU budget. A pre-registration
written after seeing part of the data is weaker. Mitigations: it is 1 of 40, it is absent
from the negative control, and every threshold used (0.60; DockQ 0.23/0.49/0.80) is
pre-existing — from handbook §7.2 and the CAPRI convention, not chosen that night.

**What a passing negative control would still not establish.** It shows the metric
separates cognate from non-cognate pairs. It says **nothing** about ranking among
plausible designs — measured failing directly: ipSAE wandered within ±0.04 while DockQ
fell 0.820 → 0.601, and the highest ipSAE in that panel belonged to a variant with a
*worse* pose than the wild type. Discrimination and ranking are different properties.

**What a high calibration percentile would not establish.** Not that the design binds.
Only that the predictor is as confident about our molecule as about real complexes it has
never seen — a statement about the predictor. The one metric reading external truth is
DockQ, and for a de novo design there is no crystal, so it is **absent exactly where it
would matter most.**

**A packaging gap found and deliberately NOT fixed mid-run.** Three modules this code
imports are absent from `[project.dependencies]`: **`gemmi`** (used pervasively),
**`python-pptx`** (the deck builder — a scored deliverable whose builder therefore cannot
run from a clean checkout), and **`scipy`** (present only in the `analysis` extra while
the report path imports it directly). `gemmi` and `scipy` arrive transitively today, which
is why nothing has failed; a transitive dependency is not a declared one and can vanish on
any upstream release.

It was left unfixed *during* the run on purpose. The fold chain invokes `uv run` at each
stage transition, and editing `pyproject.toml` makes the next such call re-sync the
virtualenv underneath a job that is mid-flight. That is the same hazard as editing a script
a running job shells out to — this project has already corrupted a dataset that way,
recording idle GPU traces still labelled `ml_training`. **The environment is part of the
running job.** Fixed after the chain completed.

**Stubbed / crude, stated plainly.**
- Follow-up rows take a **fresh MSA** rather than a cached one. Mitigated by identical
  antigens and a recorded depth check, not eliminated.
- The panel's antigen MSAs come from the **public MMseqs2 server**. Fine here — every
  sequence is already public in the PDB — but it is why the PD-1 alignment is cached for
  design work.
- **n=20 per arm** is small. Percentiles are reported as ranks for that reason.
- Panel DockQ natives are Fv-trimmed from the crystal. Antigen chains in the native retain
  their unresolved gaps while the model has the SEQRES-filled span, so DockQ aligns over
  common residues (`dockq_allowed_mismatches: 40`). Rows where DockQ refuses are reported
  as missing, never as zero.

---

## 8. Transferable principles

1. **A threshold means nothing until something has failed it.** Build the negative control
   before trusting any gate. Here it cost eight folds and ~25 minutes.
2. **A ranked generative output is an order statistic, not a sample.** If a tool sorts its
   outputs by confidence, the first one is a maximum. Draw more than one.
3. **Score every gate against the negatives, not just the headline one.** Four of five
   here reject nothing — invisible until something that should fail was run through them.
4. **When a control fails, ask *why* from data before deciding what it means.** "The
   positive failed so the panel is broken" and "...so ignore it" are equally unjustified.
   Here crystallography answered it with zero GPU time and turned a failed control into
   the session's most useful finding.
5. **A control is silent on the confound you did not think of** — and a reference that
   cannot detect a defect will never reveal it. Pembrolizumab could not see the truncation
   because its epitope is entirely inside the construct.
6. **A resume predicate must distinguish "not done" from "the check is broken."** Catch
   only the exception meaning absence; let the rest propagate. The inverted version of this
   bug silently produces empty results that look complete.
7. **When comparing across a boundary, match everything except the boundary.** Sampling
   both arms either side of one date is what makes the pre/post comparison mean anything.
8. **Prefer a metric that can say "I could not measure this."** `None` with a reason
   caught a 20% native-pairing error; a plausible `0` would have buried it as eight
   genuine docking failures.
9. **Cross-check two numbers that must agree.** Every silent failure this session was
   found by a contradiction — high ipSAE with no DockQ, a "done" fold reported as not
   done — never by reading the failing component directly.
10. **`setsid` detaches from the terminal, not the cgroup.** On a systemd-oomd system a
    background job launched from a terminal dies when that terminal's scope is killed.
    Use `systemd-run --user` for anything that must outlive the session.
11. **When a supervisor exists, ask the supervisor.** `systemctl is-active` cannot
    self-match the way `pgrep -f` can, and distinguishes stopped from idle.
12. **Verify what you fold is what you ship** — and check that the alignment you cached
    is the one the tool actually used. Nothing here compared the folding construct
   to the submitted one, for the entire project.
