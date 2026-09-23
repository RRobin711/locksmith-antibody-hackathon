# 08 — What Broke: a failure catalogue organised by generating mechanism

## What this chapter teaches

[[07-the-campaign|The campaign chapter]] told you what happened in order. This one takes the
same nine days apart along a different axis: **how things failed**, and — the part that
generalises — **what generated each kind of failure**.

A flat list of a hundred bugs teaches nothing; you cannot carry it. What you can carry is a
small number of *generators*, each of which produced several incidents in one project and will
produce several in yours. There are eight of them here, and by the end you should be able to
name each one, recognise it in the wild, and say what mechanism (not what resolution) removes
it.

Two framing commitments, both taken from the project's own documents. First, nothing is
softened. The project's own record does not soften, and the honesty is the asset:
`docs/sessions/2026-09-22-published-withdrawn-and-the-fix-that-killed-the-antibody.md:313`
records *"Four published claims withdrawn in one session … a reviewer counts the rate at which
claims need correcting, not just whether they were eventually caught."* Second, where a number
was corrected, **both the original and the correction appear**. A catalogue that only lists
final values teaches you that the project was right; a catalogue that lists both teaches you
how it got there.

---

## How this catalogue was built and counted

The underlying audit read `STATE.md`, all 22 session docs, the four audit files and both
knowledge notes, then grepped the whole tree (excluding `.venv/` and `vendor/`) for
`WITHDRAWN|CORRECTED|SUPERSEDED|REFUTED|reversed|was wrong|my own error|inverted|overstat|
retract|never existed` — **217 hits across 60 files**.

Six classes, **≈104 recorded incidents in nine days**:

| class | what it is | count |
|---|---|---|
| 1 | **Silent failures** — code that ran, exited 0, produced a confident wrong number | **26** |
| 2 | **Claims published then withdrawn or reversed** | **24** |
| 3 | **Controls that passed and were blind** | **4** |
| 4 | **Infrastructure and environment losses** | **19** |
| 5 | **Process and judgement errors** | **22** |
| 6 | **Everything else, including defects still live in the tree** | **9** |

Two counting caveats, stated because they matter for how you read the numbers. Class 2's count
of 24 treats the three-deep chain W4 → W4b → W4c as three separate claims, which is right: each
was published, each was wrong. And the class totals are one reader's grouping; every individual
incident is the project's own, recorded in its own files.

---

## Class 1 — Silent failures

**Definition: code that ran, exited 0, and produced a number in the right range, with the right
units, computed on the wrong thing.** This is the class the project cares most about, and its
own seed note (`knowledge/Eight Silent Failures.md`) has eight. A full audit found twenty-six.

### The catalogue

| # | Incident | What it produced | Real cause | How it was caught |
|---|---|---|---|---|
| S1 | **B-factor / pLDDT field reuse** | a well-formed number in range | PDB column 11 holds atomic displacement (Å², 10–80, *low = good*) in a crystal and pLDDT (0–100, *low = bad*) in a prediction — **sign-inverted meanings in one field** | anticipated at type-design time, never suffered |
| S2 | **ANARCII numbers PD-1 as an antibody** | `CDR3=GAISLAPKA` for the antigen | PD-1 has an **IgV fold**; by fold it *is* a V domain. Correct behaviour on out-of-distribution input | printing numbering for *every* chain. True V domains score 30.7–30.9; PD-1 scores 15.8–16.2 |
| S3 | **Crosswise-paired chains in 5GGS** | a "complex" with **zero** antibody–antigen contacts | two copies; labels suggest A/B↔Y, C/D↔Z. Truth is **A/B↔Z, C/D↔Y** | PRODIGY refused: `No contacts found for selection` |
| S4 | **Crystal packing larger than the epitope** | would have been selected as the binding site | **B–D = 64 contacting residues** between the two *light* chains, against real epitopes of 41/39 | the same contact analysis |
| S5 | **PRODIGY chose its own interface** | a confident **−16.3 kcal/mol** | run on a 3-chain file without `--selection`, it scored the **heavy–light** interface *inside* the antibody | only because S3's explicit selection was failing while the implicit one succeeded |
| S6 | **DockQ's zero-mismatch default** | `ERROR: For chains ['A'] no identical corresponding chain was found`, exit 1, **no output** | `--allowed_mismatches` defaults to 0; every Challenge 1 design *is* pembrolizumab with mutated loops | a deliberate stress test |
| S6b | **The stress test inverted its own prediction** | — | indels **pass** (`del2` 1.000, `ins2` 1.000, chain reorder 1.000); only **substitutions** trip the check | the test itself |
| S7 | **Boltz exits 0 after `ModuleNotFoundError: cuequivariance_torch`** | exit 0, no structure | optional CUDA kernels absent; Boltz imports them rather than falling back | checking for output files |
| S8 | **Boltz exits 0 after CUDA OOM** | exit 0, `100%\|██████\|`, buried `OOM on device 0 … 1616904192 bytes` | **VRAM**, not host RAM | reading the log, not the status |
| S9 | **Boltz killed by host-RAM exhaustion** | job killed partway | 15 GiB box, ~9 GB browser/chat, +4 GB weights, +**three concurrent decompressions of a 6 GB archive** | — |
| S10 | **Boltz exits 0 on an MSA path truncated at a space** | `FileNotFoundError: MSA file /home/rrobin711/Obsidian not found.` → **then a 100% bar, GPU init, and carried on** | the vault is `…/Obsidian Personal/…` and Boltz's FASTA MSA field splits on whitespace | — (`src/locksmith/fold/boltz.py:41-47`) |
| S11 | **ipSAE writes an empty table and exits 0** | zero-byte results file, exit 0 | `ipsae.py` finds pLDDT by `pae_file.replace("pae","plddt")`; files had been renamed | **luck** — our parser crashed on an empty file |
| S12 | **gemmi ordering bug invisible on the first test file** | `RuntimeError: missing entity_type in chain A` | `remove_ligands_and_waters()` needs `setup_entities()` first. **Worked on 5GGS**, failed on 5WT9 | running the whole reference set instead of one file |
| S13 | **`chains()` built sequences from COORDINATES** | folds completed, structures confident, DockQ plausible | unresolved residues are absent, so flanks fuse: **a chimera with internal loops deleted** | a control *not in the brief* (`results/postcutoff_result.md:96-140`) |
| S14 | **Resume keyed on a row existing** | a re-run would skip all 239 designs **forever** | the predicate was "has a row" — and **an error row is a row** | reading the log (`…2026-09-19-…:261-285`) |
| S15 | **A stage that failed 239/239 returned exit 0** | shell logged `exit=0` | no `return 1 if n_err else 0` | same |
| S16 | **`ProcessPoolExecutor` fork killed 239/239 CUDA workers** | `RuntimeError: Cannot re-initialize CUDA in forked subprocess` | `fork` is the Linux default; the removed process boundary was load-bearing | reading the log |
| S17 | **A resume check swallowed a `TypeError`** | `40 in panel, 0 already folded` for a panel with folds on disk | four drivers called `assert_artefacts(d, label)` — wrong signature — under `except Exception` | a log line contradicting known state (`src/locksmith/fold/__init__.py:88-119`) |
| S17b | **The inverted twin** | — | had the swallowed exception meant *"done"*, the same typo would have **skipped every fold and produced an empty panel that looked complete** | reasoning, recorded in the docstring |
| S18 | **`np.True_ is True` is `False`** | seven genuine passes printed **PASS** *and* were listed **UNVERIFIABLE** | the summary tested `ok is True`; numpy returns `np.bool_` | the audit of the audit (`results/audit_of_audit_2026-09-22.md:29-35`) |
| S19 | **`MpnnDesign` names fields by ROLE, not chain** | reading `d.light` returns the **heavy** chain when `design_chain="B"` | locals inside `generate()` are named for the *default* use | **luck** — an unrelated unpacking crash (`…2026-09-22-fixing-liabilities-…:224-244`) |
| S20 | **Variable shadowing: `c = cfg.conventions` vs `c = cond.get(bb)`** | `KeyError: 'ipsae_pae_cutoff'` | a new binding `c` collided with a per-backbone rebinding | it crashed — **which was luck** |
| S21 | **RF2 score parser broke at the first `ATOM`** | *"0 backbones with ≥2 designs"* | RF2 writes its `SCORE` lines at **line 5190**, *after* the coordinates | the count was implausible (`results/challenge2_pilot.md:91-99`) |
| S22 | **A dead failure-reporting branch, written while fixing a failure-reporting bug** | none — no mismatch occurred | a conditional-expression precedence error made `bad.append` **unreachable on a mismatch** | code review (`…the-first-test-file-…:369-384`) |
| S23 | **`select/surrogate.py` hardcoded band anchors the config had changed** | rankings silently wrong; **the shipped winner was selected on it** | `surrogate.py:46` held `2.5, 7.0, 9.5` while `config/metrics.yaml:7` had said `band_value: top` since 2026-09-20 | an adversarial judge |
| S24 | **`dockq.compute`'s signature default contradicted config** | a full band of score | `interface_agg: str = "min"` against a declared `global`: **0.755 vs 0.850** | the new test suite |
| S25 | **A generated document contradicted itself** | `results/specificity.md` printed the 3-seed TIM-3 mean **0.568** beside the author's 8-seed **0.513** | `_reference_controls()` iterated only the reference arms, so **five folds made to power that comparison sat unread in the same file** | noticing the two numbers |
| S26 | **The validator littered the package it validated** | three stray files in `structures/` | `ipsae.py` writes scratch `.txt`/`.pml` next to the PDB it is handed | inspection |

### The classification that matters: how it announced itself

Sorting by announcement rather than by subsystem is what makes this class teachable.

- **Crashed or refused** — the *good* failure: S3, S6, S12, S17, S20, S21. Six of twenty-six.
- **Announced by luck** — a strict parser, an unrelated crash, an implausible count: S11, S19,
  S22. Three.
- **Did not announce at all**: S1, S2, S4, S5, S7, S8, S10, S13, S14, S15, S16, S18, S23, S24,
  S25. Fifteen.

(The arithmetic does not exhaust the table: S9, S26 and the two sub-rows S6b/S17b are
unclassified. That is the audit's own gap and is left visible rather than smoothed.)

**Fifteen of twenty-six would have handed over a number in the right range, with the right
units, computed on the wrong thing.** Three of the original eight were caught *only* because
the harness was being run on structures whose answers were already known — the
"build the judge before the contestant" discipline. **On a novel design there would have been
nothing to notice.**

### The mechanisms, taught one at a time

**The most expensive one: a sequence built from coordinates (S13).** A crystal structure's
coordinate records contain only the atoms the crystallographers could *see*. Residues present
in the protein but disordered in the lattice are simply absent from the file. If you build a
sequence by walking the residues in the coordinate block, the flanking residues on either side
of a disordered loop concatenate, and you produce a sequence describing **a protein with a loop
excised and its ends fused** — a chimera. Nothing errors. The fold completes, the structure is
confident, DockQ returns a plausible number. Measured: 9W43's antigen was folded as **83 aa
against a true 115**, losing 32 residues *across the epitope face*; 9BQW's lost 19 across its
epitope. Re-folding 9BQW from SEQRES moved DockQ **0.064 → 0.370** and flipped a milestone
verdict. The fix distinguishes two cases that look alike and are not: `seq_for_folding()`
**raises on an internal deletion** and **permits terminal truncation**, because a truncation
leaves no gap in the author residue numbering and removes nothing from the middle of a fold.
Both are detectable from author numbering alone, without fetching SEQRES. The transferable
form: **a large interface at near-zero DockQ is as easily your input preparation as the model's
error — check the question you asked before you doubt the answer.**

**A tool's default encodes its author's use case, not yours (S5, S6, S24, and NetSolP's model
variant).** PRODIGY run on a three-chain file without `--selection` does not fail; it *chooses*,
and on 5GGS it chose the heavy–light interface inside the antibody and returned **−16.3
kcal/mol**, a value entirely plausible for an antibody–antigen interface and therefore
undetectable by inspection. DockQ's `--allowed_mismatches` defaults to **0** because DockQ's
authors compare a model to an experiment of the *same* complex; every Challenge 1 design is
pembrolizumab with 29 mutated CDR positions, so at the default DockQ refuses to score **every
design the project produced** — `viable=None`, nothing selectable. (Worth knowing: **4
substitutions is already enough to trigger it**, while insertions and deletions pass cleanly,
the opposite of the intuitive expectation, because indels do not create mismatches *at aligned
positions*.) The project's own phrasing is the rule: *when a tool has to choose something you
care about and you didn't specify it, it chose. Find out what.*

**A convention encoded in two places will diverge (S23, S24).** These are the same bug and they
are the most expensive pair in the class. `select/surrogate.py:46` hardcoded the band anchors
`2.5, 7.0, 9.5` — the *midpoints* — while `config/metrics.yaml:7` had declared `band_value: top`
since 2026-09-20. The surrogate never read config. Because the anchors set the slopes of the
interpolation segments, moving them changes the **slope ratio** from 4.5/2.5 = **1.8** to
3.0/2.0 = **1.5**, and non-uniform slopes *reorder*: under the declared convention the shipped
winner falls **1st → 4th**, **18 of 20 designs change rank**, Spearman between the two rankings
**0.755**. The config file had explicitly asserted the choice *"CANNOT change the ordering of
two designs"* — true of the banded `final`, false of the surrogate actually used to rank.
`dockq.compute` is the same defect one layer down: a signature default `interface_agg="min"`
restating a convention the config declared as `global`, worth **0.755 vs 0.850**, a full band.
The project's post-mortem is exact: *"a signature default that restates a convention is a second
source of truth, and the second one rots."* The generalising fix is not discipline; it is an
assertion tying the two representations together, which is what
`test_surrogate_anchors_match_config_band_values` now is.

**A resume predicate is a failure detector, and it fails in both directions (S14, S17,
S17b).** Three instances in nine days. S14 asked "does this design have a row in the output?" —
and an error row is a row, so 239 error rows read as 239 completed designs and a re-run would
have skipped the whole pool *forever*, leaving a file that looks complete. S17 is the mirror:
four drivers called `assert_artefacts(d, label)` when the real signature is
`assert_artefacts(pdb, pae, plddt, *, label, stdout="")`, so **every call raised `TypeError`**
and a bare `except Exception` read it as "not folded yet", producing wasted refolds and the
log line `40 in panel, 0 already folded` for a panel with folds demonstrably on disk. S17b is
why this is a class rather than an incident: had the swallowed exception defaulted to *"done"*
instead, the identical typo would have **skipped every fold and produced an empty panel that
looked complete**. The fix is narrow catching — `fold_is_complete()` catches **only**
`FoldFailed`, with a test that monkeypatches a `TypeError` and asserts it **propagates**.

**Exit status is not a result (S7, S8, S10, S15).** `boltz predict` exits 0 after a missing
`cuequivariance_torch` import, after a CUDA OOM printed under a `100%` progress bar with
`Number of failed examples: 1` buried in the log, and after an MSA path truncated at a space —
in the last case printing `FileNotFoundError: MSA file /home/rrobin711/Obsidian not found.`,
*then* a 100% bar, *then* initialising the GPU, then carrying on. That last one deserves its own
sentence because it generalises beyond this tool: **argv is safe because the shell quotes it; a
path inside a FASTA, YAML or config field is not.** Boltz's input line is
`>CHAIN|entity|<msa-path>` and its parser splits on whitespace. The mitigation
(`src/locksmith/fold/boltz.py:41-47`) copies any MSA to `~/.cache/locksmith/msa` and **raises if
a space survives**. And a stage that failed 239 of 239 returned exit 0 because nobody wrote
`return 1 if n_err else 0`. The contract the project settled on is `assert_artefacts()`, which
rejects a missing PDB/PAE/pLDDT, a zero-byte PDB, a PDB with no `ATOM` records, a `.npz` that
exists but fails at read time, a non-square PAE, and a missing pLDDT sibling. **Existence is not
enough, and exit 0 is not evidence.**

**And the rule demonstrates itself on itself: the canonical exit-0 list is mis-enumerated, and a
test pins the error.** `src/locksmith/fold/__init__.py:9-11` — the module docstring that exists
to state this invariant — says *"three of four failed Boltz runs exited 0 — a missing CUDA
kernel, a host-RAM kill, and a CUDA OOM"*, and `tests/test_invariants.py:398-401` repeats the
host-RAM kill in its own four-item list. **The host-RAM kill did not exit 0.** The primary
session doc records attempt 1 as *killed* — the kernel's OOM killer sends `SIGKILL`, which is
emphatically a non-zero status and is the one failure in that evening that announced itself
honestly. The session index for 2026-09-16 states the membership correctly: *"Four fold
failures — host RAM, missing CUDA kernel, GPU VRAM, and ipSAE's filename coupling — three of
which exited 0."* Subtract the one that was killed and the three genuine exit-0 cases are the
missing `cuequivariance_torch` import, the CUDA VRAM OOM, and **ipSAE's empty-table failure**
(S11) — which is the member the docstring drops.

Nothing downstream is wrong because of this: `assert_artefacts()` catches all of these cases and
more, and the test that carries the bad enumeration in its comment tests the right behaviour. But
it is worth sitting with, because it is this chapter's thesis reproduced in miniature. The
project's single most-repeated engineering lesson, written into the docstring of the module that
enforces it and into the comment above the test that pins it, **gets its own evidence wrong in
both places** — and the error propagated from prose into a test, which is exactly the direction
this project spent day 9 trying to make safe. A convention encoded in two places diverged
(generator 2); the wrong version was mechanised. *Mechanising a lesson protects the behaviour. It
does not check the story you told yourself about why.*

**Filename coupling (S11).** `ipsae.py` locates its pLDDT array by string-substituting the PAE
path: `pae_file.replace("pae", "plddt")`. A Boltz PAE must therefore keep its
`pae_<name>_model_<n>.npz` name *and* keep `plddt_<name>_model_<n>.npz` as a sibling in the same
directory. Rename or relocate either and ipsae **writes an empty table and exits 0**. Any label
containing the substring `pae` also breaks it. Three defences now ship, including `fold()`
refusing such a label and `fold/__init__.py` returning paths *in place* with the comment
"DO NOT 'TIDY' THE OUTPUT". The transferable point: **never normalise a third-party tool's
output filenames until you have read how it finds its own siblings.**

---

## Class 2 — Claims published, then withdrawn or reversed

Twenty-four, and the table below is grouped **by the generator of the error** rather than
chronologically, because the generators are what you can carry away. Every row gives the
original number, the corrected number, and why the first was wrong.

### Generator (i) — a small-*n* null read as evidence of absence

This is the project's single most productive error, and its own diagnosis is the sharpest
sentence in the record: *"this project already knows this failure mode — `LEARNINGS.md` carries
'measure the noise floor before comparing any correlation to a threshold'. **The rule was
applied to positive findings and not to nulls.**"* Four were corrected in one day, 2026-09-20.

| # | Published | Corrected | Why the first was wrong |
|---|---|---|---|
| W4 | *"Mean loop pLDDT is blind to conformational heterogeneity"* — ρ **−0.168**, p=0.69, **n=8**; *"the spine of the planned pitch"* | ρ **−0.432**, p=2.9e−12, **n=239** | an n=8 correlation has a 95% CI **roughly ±0.7 wide**. A wide interval around zero was read as evidence of absence |
| W4b | *"…and it is refuted; the earlier reading was noise read as an effect"* | **also too strong, withdrawn the same session.** The defensible figure is **−0.23 to −0.35**; the n=8 finding was *underpowered, not wrong* — −0.168 and −0.233 are statistically indistinguishable | the −0.432 headline shares seed 1 between pLDDT and the k=2 spread. Disjoint estimate (pLDDT from seed 1, spread from seeds 2–3, n=84): **−0.233** |
| W4c | *"…inflated by roughly a third"* | the genuine circular inflation is about **13%** | the "one third" figure did not itself account for attenuation |
| W5 | *"The ensemble carries no information the sequence didn't"* — partial **−0.081**, p=0.62, **n=40**; **a selection axis was deleted on this** | **−0.289** (p=5.7e−06) at n=239; **−0.303** on the same T=0.1 arm | identical error to W4 |
| W5b | *"The aromatic-fraction result reverses"* | **wrong — it replicates to 0.002**: aromatics→DockQ raw −0.536 → **−0.535**; controlling spread −0.410 → **−0.408** | the morning summary tested a **different outcome variable** (spread, not DockQ) than the claim it contradicted |
| W19 | *"The design **is** TIM-3-reactive; the escape is closed"* — ipSAE 0.568 vs pembrolizumab 0.323, non-overlapping at n=3 | **overstated.** At n=8: ours **0.513**, p=0.038 vs pembrolizumab, p=0.024 vs a real binder. **Intermediate, not a near-binder** | with 3 v 3 the **smallest attainable two-sided Mann–Whitney p is exactly 0.100** — and 0.100 is what was measured. *The test was at its ceiling before it began* |
| — | `interaction_pae` *"ICC 0.000 ⇒ CANNOT rank, DELETED"* | softened to **undetected**: measured ICC **−0.113** against a **detectable floor of 0.317** at n=10, k=3, since `F_crit(0.05, 9, 20) = 2.393` | same |

**The rule, and it is one sentence.** A null is only meaningful as *"no effect larger than x"*,
where *x* is the effect detectable at the *n* you actually have. **State the detectable effect
beside every null, or do not report the null.** Note also the W4 → W4b → W4c chain: three
successive statements of one finding, each wrong, each overcorrecting the last. The discipline
that stops this is not more scepticism; it is computing the interval first. See
[[04-measurement-theory|attenuation, reliability, and why an n=8 interval spans ±0.7]].

### Generator (ii) — a single observation compared against an aggregate

Three instances, and the second was committed *after* the first had been written into
`LEARNINGS.md`.

| # | Published | Corrected | Why |
|---|---|---|---|
| W8 | *"ipSAE 0.8491 from our JSON vs 0.8560 from the npz — a code-path split in `ipsae.py`"* | **no difference.** Both routes agree to five decimals per chain pair (A–C **0.823561** vs **0.823574**; residual = 2-dp PAE rounding). **0.8560 was the 8-seed mean**; seed 1 alone is 0.8491 | a single observation compared to an aggregate without checking which was which |
| W13 | *"The germline metric cannot distinguish a licensed therapeutic's loop from a permutation of its own residues"* — **on slide 4 of the pitch** | **exactly backwards.** Scrambles (n=2000): mean **21.5%**, sd **6.1%**. Pembrolizumab at **53.8%** is the **maximum of 2000 draws**, ≈ **+5.3 sd**, p ≈ **1/2000** | compared a single observation to the **maximum** of an aggregate and concluded equivalence |
| P10 | *"real epitope 0.712"* printed under a heading about **this design**, inside the shipped package | 0.712 is the **18-backbone pool mean**. The design's own backbone is **0.625** — *below the pool median of 0.684* — and on the submitted re-dock it is **0.581** | the project's own catalogued error, committed in the deliverable (`submission/LOCKSMITH_DEV/LOCKSMITH_DEV_Challenge2/docs/methods_and_limitations.md:57-64`, now corrected in place with all three numbers) |

**Mechanical guard, from the project:** *a value quoted from a results table is an aggregate
until proven otherwise — read its n.*

### Generator (iii) — a setting inherited across a change of problem, and a mechanism asserted before testing

| # | Published | Corrected | Why |
|---|---|---|---|
| W9 | Challenge 2: **`0/30` viable**, all failing ipSAE, best **0.372**, median 0.006 — written up with a long essay on metric design | **1/30.** At recycling 10, `bb_2_0_dldesign_1` moves **0.263 → 0.864 / 0.842 / 0.856** across three seeds, above the positive control's 0.842 on a real crystallised pair | `recycling_steps=3` inherited from Challenge 1 and never re-examined. **The tell was in the data that was written up: 15 of 30 at exactly 0.000** |
| W9b | *"Extra recycling resolves the pool"* (the correction to W9) | **the pool data does not support that either.** r3: mean 0.0640, median 0.0056, **15/30 zeros**. r10: mean 0.0646, median 0.0050, **still 15/30 zeros**. r3↔r10 rank correlation **0.432** | the pile-up tell cited as evidence of under-sampling **applies identically at recycling 10**. What survives is narrower: *"it changed when I sampled harder" ≠ "it has converged"* |
| W10 | *"The Challenge 2 distribution is bimodal — twenty-nine it will not place at all"* | **an artefact of ipSAE's hard PAE<10 Å cutoff.** The 15 designs at ipSAE *exactly* 0.000 carry **ipTM 0.556–0.674**, an ordinary continuum. Largest-gap ratio **3.56 on ipSAE, 2.12 on ipTM** | nobody had opened Boltz's own `confidence_*.json`. **A statement about the metric reported as a statement about the molecules** |
| W11 | *"everything else ≤ 0.161"* for the Ch2 pool | **false — third place is 0.311** (`bb_9_0_dldesign_1`) | omitted from the table because it never entered the top-5 reseed set — **having been excluded by the recycling-3 ranking that had just been declared misleading** |
| W18 | *"No PTX JIT path exists from CUDA 11 to `sm_120`"* — asserted as the mechanism | **false as a general statement.** PTX forward-compatibility is exactly that mechanism. The conclusion held **for a different reason**: the wheels ship **`PTX entries: NONE`**, so forward-JIT has nothing to lower | argued instead of tested. *"A claim about a mechanism and a claim about an outcome are different claims, and only one of them was cheap to test"* |

### Generator (iv) — a convention that lived in two places, or in none

| # | Published | Corrected | Why |
|---|---|---|---|
| W15 | *"ProteinMPNN degraded developability in 239/239 cases"*; *"20% of the rubric is an unreachable ceiling"* | **superseded.** On Fv: pembrolizumab VH **0.733** / VL **0.569**; designs' VH **0.6677–0.7424**; **168/239 (70%) have VH in the Good band**; 4 beat the parent | computed on **Fab** chains where the handbook specifies **Fv**, twice. On Fab the heavy chain looked limiting (0.623 vs 0.626); **on Fv the ordering reverses.** *A convention error does not merely shift a number; it can invert the causal story you tell about it* |
| W16 | The submitted Challenge 1 winner was the best design | under the **declared** convention the shipped design falls **1st → 4th**; **18 of 20 change rank**; Spearman **0.755** | S23. Changing the anchors changes the interpolation **slope ratio** 1.8 → 1.5, and non-uniform slopes reorder. **Not swapped**, deliberately: the 1st–4th gap is **0.191** against a pooled seed sd of **0.226** |

Two further convention facts belong here even though they were never wrong claims, because they
size the class: four band edges were treated as inclusive where the handbook is strict, and the
band→score mapping remains the project's own invention — the same design scores **81.0 / 87.5 /
94.0** under bottom / midpoint / top, i.e. **12 points of pure convention**, with the handbook's
stated maximum of 100 unreachable under midpoints.

### Generator (v) — a projection quoted as a measurement

| # | Published | Corrected | Why |
|---|---|---|---|
| W21 | Compute budget **~4,700 folds** (34 s/fold) | **~1,290 Fab folds.** 34 s is the *fold*; a `boltz predict` **invocation** costs **92 s (Fv) / 126 s (Fab)** — ~60 s of checkpoint load and MSA parsing dominates | measured the inner loop and quoted it as the outer. A **3.6×** overestimate that shaped the design space for a day |
| W22 | Batching will recover **~1.8×** — used in scheduling arguments for two days | measured **1.16×** (84 s → 72 s/fold); saves 0.8 h on a 239-fold arm, not 2.4 h | an unmeasured split between per-fold and per-invocation time. *"The least-examined number in the argument"* |
| W23 | RF2 at **~4 min/sequence** (derived from 23.4 s/pass × 10 recycles) | measured **7.1 min/design**; the 20-backbone estimate moved **12 h → 16 h** | derived instead of measured; **1.75× optimistic** |
| W17 | *"The fold rate is 140 s/fold — the 84 s figure is a 1.65× sizing error"* | **withdrawn.** The completed arm folded **239 in 6.0 h at median 84 s** | the 133–150 s medians came from **contended** runs, sampled while the author ran analyses on the same box. **A correctly-labelled estimate was overridden with contaminated data** |

Note the direction: **three of four projections ran optimistic by 1.5–1.8×**, and the fourth was
a pessimistic "correction" built on contaminated samples. Projections in this project were not
noisy; they were biased.

### Generator (vi) — the right test on the wrong outcome variable

This is the most instructive entry in the whole chapter, because **more statistics could not
have caught it.**

| # | Published | Corrected | Why |
|---|---|---|---|
| W12 | **The G3 CDR-H3 aromatic filter PASSES**: beats 10,000 equal-budget random subsets at **p<0.0001**, +0.0241 mean DockQ. A headline for four days | **REFUTED as a design rule.** Re-run with each of six scored metrics as the outcome (n=239, 10,000 resamples) it wins on **2 of 6** — `dockq` (+0.0237, p=0.0001) and `iface_plddt` (+1.12, p=0.0001) — **both properties of the PREDICTOR**. `dg` p=0.064, `ipsae` p=0.241, `cdr_sasa` p=0.547, and **`contacts` runs the wrong way: −1.80 contacts, one-sided p 0.988** | the statistics were sound; the **outcome variable** never supported the conclusion. DockQ here is *pose retention against the parent crystal*; interface pLDDT is *Boltz's own confidence*. **A metric gaming its own scorer.** Neither quantity even exists for a de novo target |
| W14 | *"Redesign the light-chain CDRs"* — in three documents, echoed by two independent reviewers for ~5 days | **REFUTED twice over.** (i) NetSolP aggregates as `min(VH,VL)` and **VH = 0.699 against a Good edge of 0.70**, so a perfect light chain cannot move the band — **by 0.001**. (ii) 24 ProteinMPNN light chains moved VL **0.5690 → 0.5920 (+0.023) against a required +0.131**; **0/24** reached the edge; **24/24 introduced new CDR liabilities** | two lines of arithmetic available the whole time. And ProteinMPNN optimises *sequence recovery given a backbone* — **solubility is not in its loss**. Cost of the refutation: **zero GPU folds** |
| W24 | The novelty-probe extrapolation — designs in this identity band will reach DockQ 0.80 | **withdrawn as a prediction.** Arms B and C, matched at 53.8% identity and differing by **227 antigen contacts**, returned a null at **+0.032 DockQ**; the target was missed by **0.043** | an extrapolation from a headroom audit, not a measurement |

W12's judge did not find it with a better test. A reviewer noticed that the rule **selects
against Tyr and Trp**, among the most robust compositional facts in antibody biology, and
that contradiction is what prompted re-running the same test against every other outcome
available. **When a result survives a good null but contradicts a strong prior, vary the
*outcome*, not the test.** As a footnote on cost: the filter would also have discarded the
project's own winner, whose CDR-H3 aromatic count is 2 against a threshold of ≤1.

W20, for completeness, belongs to no generator except optimism: PRODIGY's predicted Kd of 34 pM
against pembrolizumab's measured 29 pM was written up as *validation of accuracy* on
2026-09-15 and corrected on 2026-09-16 — PRODIGY's own RMSE makes a single-point agreement
uninformative. **A positive control shows the pipeline is wired correctly. It is not a precision
claim.**

---

## Class 3 — Controls that passed and were blind

Four, and they are the most teachable material in the project, because each one *worked* —
correctly eliminated the confound it was built for — and was then read as general reassurance.

| # | Control | What it correctly established | What it was blind to | Cost |
|---|---|---|---|---|
| **C1** | **Challenge 2 positive control** — wild-type pembrolizumab through the identical call | the **Fv construct is not the problem**: Fab **0.776**, Fv **0.842**, both clearing pre-registered bars of ≥0.75 and ≥0.60. A well-grounded hypothesis, since G1c had concluded "Fab-only" on reliability grounds and Challenge 2 was folded as Fv without revisiting it | **it ran at `recycling_steps=3` too.** It could not see the one variable that mattered | it printed *"0/30 is a real property of the designs"* — **wrong within the hour**, and that verdict was published |
| **C2** | The negative-control panel's **positive arm** | the gate set exercised against things that should fail | **nivolumab scored ipSAE 0.017** (max 0.263); pre-registered Rule 3 fired, INCONCLUSIVE. Diagnosis with **zero GPU time**: the 113-residue PD-1 construct covers **24/24 of pembrolizumab's epitope but only 8/14 of nivolumab's**, missing `L25 D26 S27 P28 D29 R30` — **43% of nivolumab's binding site absent from the molecule we docked it against** | *"the only reference antibody ever folded was the one incapable of detecting the truncation"* — the 113-mer was inherited from 5GGS and never re-examined for the whole project |
| **C3** | The **`26/26 hotspots resolved`** manipulation check | RFdiffusion **received** the conditioning — `ab_pose.parse_hotspots` matches `(chain, pdb_resnum)` and **silently skips misses**, so the count is worth asserting | it says **nothing** about whether conditioning changed the output. *"A manipulation check that cannot fail is not evidence"* | the arm that was run (no-hotspots) is **the wrong null**; the decoy-patch arm on the opposite face costs the same and **was never run** |
| **C4** | The **contiguous-patch null** (C3's replacement) | deterministic per backbone, no stopping rule; real epitope **0.712** vs patch null **0.154**, **17/18 backbones at p<0.05** | the drawn patches are **more compact than the real epitope** — mean RMS spread **7.73 Å** vs the PD-L1 footprint's **10.08 Å** (uniform draws 13.21 Å), plausibly **anti-conservative by an unquantified amount** | the honest phrasing is *"a compact 26-residue patch elsewhere"*, not *"an epitope-like patch elsewhere"*. Shape-matching is cheap and **has not been done** |

**C1 is the centrepiece.** Read the shape of it carefully, because it is exactly the shape of a
control you will build. A plausible confound was identified (the Fv construct, on the strength
of a real earlier finding that Fv ipSAE reliability is 0.607 against Fab's 0.965). A control was
designed that could genuinely have caught it. It ran, it passed, the confound was correctly
eliminated — and because a control passing *feels* like reassurance, it was allowed to license a
much broader verdict about the pool. That verdict was wrong within the hour, and had already
been published.

> **The class principle, in the project's own words:** *"A control eliminates the confound you
> thought of and is silent on the one you did not; a passing control reads as general
> reassurance and is nothing of the kind."*

The sharper corollary comes from C2: **a reference that cannot detect a defect will never reveal
it.** Choose controls that *could* have failed for the reason you fear, not only for the reason
you suspect.

**Two near-misses belong here.** The epitope-knockout control passed for ipSAE (17.1× its own
seed sd) and interface pLDDT (64.0×) and correctly showed PRODIGY ΔG (0.9×) and contacts (1.2×)
are **blind to the interface** — with ΔG carrying the largest single share of the ranking
variance. But the same two metrics that *passed* the knockout **failed SKEMPI with the wrong
sign**: across 45 single mutants with experimental ΔΔG, ipSAE ρ = **+0.300** and interface pLDDT
**+0.275** on the reliable subset, when both should be negative. `NL31A` abolishes binding
(ΔΔG **+21.81 kcal/mol**) and scores ipSAE **0.917**, *above* the wild type's 0.903; `KY96M`
(ΔΔG +28.35) gets a **more favourable** ΔG than the real complex. **Four of five
binding-abolishing mutants score like the wild type.** A control can pass one falsification and
fail another that matters more.

---

## Class 4 — Infrastructure and environment losses

Nineteen. `knowledge/The Environment Saga.md` opens with the honest headline: **roughly half the
elapsed time on day one went into getting software to run at all.**

| # | Incident | Real cause | Cost |
|---|---|---|---|
| I1 | **The numpy 2.0 fault line** | PRODIGY needs `numpy>=2`; **DockQ** and **Boltz-2** need `numpy<2`. Genuine incompatibilities, not negotiable pins | part of day one — and it *bought* independent pinning to whatever version a grader runs, and absorbed Boltz as a third conflict with no redesign |
| I2 | **`freesasa` will not build** | compiles from C; system Python ships no dev headers; installing them needs root | seconds, once diagnosed: rebuild on uv's managed CPython 3.12.13 |
| I3 | **The four-attempt fold** | (1) host RAM exhausted; (2) `ModuleNotFoundError: cuequivariance_torch`, **exit 0**; (3) **CUDA VRAM** OOM, **exit 0** under a 100% bar; (4) success in **34 s** | an evening. **Three of four reported success or said nothing useful** |
| I4 | **The swap detour** | `swapoff` must fault **every** swapped page back one at a time — 3.2 GB took minutes and looked like a hang | minutes lost, then ~5 s for the additive fix (8 + 16 = **24 GB**, `vm.swappiness=10`) |
| I5 | **Blackwell kills RFantibody** | RFantibody pins `torch==2.3.*`/cu118; the GPU is **`sm_120`**. Failure is **total, not partial** — a plain ReLU fails, not just cuBLAS. `is_available()` returned **True**. `PTX entries: NONE`, so no forward-JIT. Docker cannot help: it isolates userspace, not the instruction set | **Gate 0 FAIL in 25 minutes**, because the probe ran *before* the ~10 GB install |
| I6 | **DGL silently downgraded torch** | `dgl-2.4.0+cu124` **pins `torch==2.4.0` exactly**, printing `- torch==2.4.1+cu124 / + torch==2.4.0` and leaving the **generic cu121 PyPI build** in place | closed the "install the library, then force a newer torch" workaround entirely |
| I7 | **Official DGL wheels top out at cu124** | `torch-2.4/cu128` → **403**; cu126 → **403**; cu124 → 200. `sm_120` needs 12.8 | closed the route |
| I8 | **CPU contention cost 2.3× on fold rate** | first fold **307 s** against 84 s; **not thermal** (GPU 100% at 765 MHz, 49 °C). NetSolP at **395–1568%** CPU plus a browser at 44% CPU / 6.4 GB RSS of 15 GB | at 195–307 s only **~95 of 239** folds would have completed by 07:30; quiet, all 239 did |
| I9 | **`pgrep -f` self-match, 3rd instance** | the wait pattern was `scripts/run_validity\.sh`; the script had been created by a **heredoc inside `bash -c`**, so the launcher shell's argv contained the entire script body — it matched its own grandparent | **2 h 39 min** of idle GPU (`…2026-09-20-auditing-the-judge-…:339`) |
| I10 | **`pgrep -f` self-match, 5th instance** | `while pgrep -f "65_rfdiff_cpu"` matched a **stale harness shell whose argv still contained the string**. Backbone exited 09:58:38; the loop waited on a ghost until 11:23. Exit **144** | **1 h 22 min** (`results/gate0_cpu.md:152`) |
| I11 | **`pgrep -f` self-match, 6th instance** | the heredoc that created the script was still a live parent's command line, so the bracketed literal `[7]3_challenge2_score.py` matched **from another process's cmdline**. The bracket trick stops self-matching by `pgrep`; it does not stop this | **21 min**, written *after being told to check artefacts* |
| I12 | **Keystroke transfer dropped 4 of 11,096 characters** | typing base64 into a browser terminal delivered **11,092**; a 20 KB heredoc paste **truncated mid-word**. Detected **only by md5** | *"a checksum is the only thing that separates 'arrived' from 'arrived intact'"* |
| I13 | **Idle pod billing** | the pilot finished at 01:36; nothing happened until 04:08 because the session **waited to be prompted instead of polling** | **~2.5 h ≈ $1.25 — 42% of the entire cloud spend, more than the pilot's own compute** ($2.82 for 5.5 h) (`results/challenge2_pilot.md:100`) |
| I14 | **The pod was stopped without retrieving the data** | 36 backbones, 30 sequences, 30 RF2 predictions — **443 MB** — left on a stopped volume. *"d=1.47, ICC=0.000 and 24.9 Å exist only as prose in a markdown file"* | a day of unfalsifiable headline claims; a paid restart to retrieve 256 files / 427 MB |
| I15 | **Jupyter 502'd mid-checksum-walk** | RunPod's **"Start Pod using CPUs"** fallback provisioned **vCPU 0, Memory 0 GB**; Jupyter was OOM-killed serving a recursive directory walk, ~130 of 256 files verified | the integrity row stayed **amber** for a day. *A provider's "start without a GPU" fallback is not the same machine minus the GPU* |
| I16 | **The retrieval script had no retries and lost its manifest** | one transient empty response 130 files in killed it with `JSONDecodeError`; `pull.py` v1 wrote the manifest **only at the end** | every checksum computed was lost. *The project's own "make the job resumable" rule was applied to overnight GPU jobs and not to a ten-minute download* |
| I17 | **A session crash killed both GPU jobs mid-flight** | neither had produced an artefact yet; both *were* resume-on-artefact, which bought nothing | *"resume-on-artefact protects completed work; it does nothing for work in flight, and a long first fold is exactly the window where a crash costs most"* |
| I18 | **Three self-inflicted pod-run failures** | (a) `uv: command not found` — `00_setup.sh` exported `$HOME/.local/bin` to PATH, `01_run.sh` did not; (b) `Could not override 'inference.seed'` — **RFantibody has no `seed` key**, it was invented rather than read from the schema; (c) the RF2 parser bug | seconds each, because the **artefact assertion** caught them. (a) and (b) are **inventing an interface instead of reading the schema** |
| I19 | **A5000 and pod-migration instances unavailable** | capacity | forced I15's zero-allocation pod |

**Total dollars: $2.82 for 5.5 h of useful RTX 3090 time, against ~$1.25 of idle billing.** The
cloud spend was **42% waste**, and the waste was caused by a turn-taking pattern, not by
hardware.

**Total hours from one bug pattern: 4 h 22 min**, to which we return in the frequency analysis.

---

## Class 5 — Process and judgement errors

Twenty-two. These are the ones no test can catch, which is precisely why they are worth reading.

| # | Error | Consequence | Principle |
|---|---|---|---|
| P1 | `recycling_steps=3` inherited from Challenge 1 and never re-examined | the published `0/30` | **a setting inherited across a different kind of problem is a hypothesis, not a default** |
| P2 | The Fv/Fab decision inherited the same way | *caught* — this is what C1 was built to test, and the construct was exonerated | same class as P1; the difference is that P2 was suspected and P1 was not |
| P3 | Antigen-only MSA for a de novo VH/VL | listed at `STATE.md:350` as step 2 of the shortest path forward; **never tested** | third instance of the same class |
| P4 | The 113-residue antigen construct inherited for the whole project | 43% of nivolumab's epitope absent; and **the construct we fold is not the construct we submit** — the shipped FASTA carries a **123-residue** PD-1 including `DSPDRP` | **verify that what you fold is what you ship** |
| P5 | A signal noticed and dropped | the author's PAE diagnostic flagged `bb_2_0_dldesign_1` at **81.4%** of cross-chain pairs under 10 Å — by far the highest of nine. It was noted, then `0/30` was written up. **It is the design that clears** | a diagnostic is only a control if you act on it *before* writing the conclusion |
| P6 | Optional stopping | interim look at **n=10 v 5** (d=0.96), extended to **18 v 18**, tested at nominal α. *"The reported p = 0.0016 is not the true type-I rate and d = 1.47 is upward-biased"*; CI **[0.733, 2.216]** | conceded in full and **replaced** by a deterministic per-backbone null computed free on data already on disk |
| P7 | Asserting a mechanism before testing it | W18 — right answer, wrong derivation | *a claim about a mechanism and a claim about an outcome are different claims* |
| P8 | Convention-mixing **inside the document reporting convention-mixing** | shortlist single-seed reliability written as **0.28** — the `midpoint` value quoted in a `top` context. It is **0.296** | caught by the audit-of-the-audit |
| P9 | A reference to a file that never existed, **shipped inside the submission** | `methods_and_limitations.md` cited `results/g3_verdict_reexamined.md`, written into the package during a previous pass; **the file was never created** | a dangling citation in a deliverable |
| P10 | A pool mean quoted for an individual design, **inside the shipped package** | see Generator (ii) | the project's own catalogued error, committed in the deliverable |
| P11 | *"Chosen by a fixed rule"* | the pre-registered Challenge 2 selection rule **sorted a list of length one**; under its own key this design's backbone ranks **below 12 of 18** | a claim of principled selection where no selection occurred |
| P12 | Two more false statements in shipped docs | *"the CLI default would fail a marketed drug"* — **NetSolP's `predict.py` defaults to `ESM1b`, which passes**; and *"the two DockQ flags are mandatory"* — only `--allowed_mismatches` is, true minimum **15** (the design's substitution count), not 40 | two overclaims in a package whose selling point is its honesty (`submission/.../reproducing_our_numbers.md:70-77`) |
| P13 | The deck contradicted the package | the shipped `.pptx` said *"No design submitted"* for Challenge 2 while the package contained a Challenge 2 design scoring 96.0 | **both structural reviewers rated it the most severe defect in the submission.** The packager rebuilt the zip and not the slides; the validator *"has never read the `.pptx`"* |
| P14 | Three days resolving an objection that was not load-bearing | Challenge 2 was declined on **evidential** grounds; the work that followed answered **feasibility** | *"the blocker chain began at 'can we run it' when the decision had been made on 'should we'"* — re-read the decision, not the last blocker |
| P15 | `BUILD.md:62` promised `liabilities.py`; it was never written | **two glycosylation sequons shipped in the Challenge 2 paratope.** When finally written it found them *and* an `NG` motif in Challenge 1 no reviewer had flagged | **a build plan is not a build**; *a planned check that does not exist is indistinguishable from a check that passed* |
| P16 | A pre-registration written after part of the data was seen | 7ZOZ was folded and scored **before** the calibration prereg, as a timing test | disclosed in an "honesty ledger"; **disclosure is the mitigation, not a fix** |
| P17 | A verdict branch decided by the wrong metric | the ablation's generated verdict was decided on `contacts`. Per metric: DockQ hotspots/controls **34×**, ipSAE **5.7×**, ΔG **0.6×**, contacts **0.3×** | a single-branch verdict on a multi-metric experiment hides which metric decided |
| P18 | A verdict threshold that was a fraction of the mean, not of the noise | `abs(effect) > 2% of the mean` **passed PRODIGY ΔG on a +0.333 kcal/mol shift smaller than its own seed sd**, producing a table that contradicted the prose beneath it | **the yardstick must be the measurement's noise, never a percentage of its level** |
| P19 | "Designable" assumed to mean "will change" | at T=0.3, arm A returned **92.3% identity** — one of four positions actually changed. *"The arm would have run all night and tested nothing, while looking like it had worked"* | `--omit_AA_jsonl` forbids the native residue, making identity exact by construction (re-run gave exactly 69.2 / 53.8 / 53.8) |
| P20 | The 2σ margin rule justified by the wrong mechanism | the rule assumed the organisers re-fold. **They do not** — given the same PDB and PAE, the metrics are deterministic. What varies is **implementation**, not prediction noise. And the rule may have been unsatisfiable: 2σ above a 0.60 gate demands **0.80–1.00** | *"A constraint that nothing satisfies is not a constraint, it is a bug"* — replaced by vendored pinned tools plus a margin of ≥20% of band width |
| P21 | An interesting result got an essay before it got a convergence check | `0/30` *"was interesting, and that was the trap"* | **the more interesting a null, the earlier the sampling check** |
| P22 | A test written too strong, and the value was finding out | the first anchor-agreement test asserted equality at **every** anchor and failed on four metrics — for a reason other than the bug it was written for: four Good edges are **strict** (`contacts > 25`, `iface_plddt > 80`, `cdr_sasa > 600`, `cdrh3_identity < 70`), so a value *on* the edge is Medium in the report and Good in the surrogate. **Not measure-zero** — `contacts` is an integer, so "exactly 25" is ordinary | "fixing" it would have produced a **non-monotone** surrogate that decreases as the metric improves. Correct the docstring, scope the test, pin the known divergence separately |

Also in this class, and worth keeping: **ordering the night's jobs by value was wrong.** The
brief put the 4.6 h ensemble job first *"because it is the valuable one"*. It ran **last** — the
two ~46-minute tails risk only their own tail, while the big shuffled job **degrades
gracefully**: losing 46 minutes moves *n* from ~239 to ~200 and the detectable effect by about
0.01, against a 100% chance of losing a whole result the other way. **Run the job that degrades
gracefully last.**

---

## Class 6 — Everything else, including defects still live in the tree

| # | Finding | Label |
|---|---|---|
| X1 | **A withdrawn claim survives, bolded, in the same paragraph as its own withdrawal.** `results/challenge2_premise_recheck.md:53-62` marks the germline-scramble claim (W13) *"false and is withdrawn"*, then two lines later restates it in bold: *"**We have now shown that 2.4×-weighted metric cannot distinguish a licensed therapeutic's loop from a shuffle of it.**"* A reader skimming bold text gets the refuted version | **VERIFIED, live** |
| X2 | **The NetSolP `LEARNINGS.md` entry still carries the claim the submission retracted.** `LEARNINGS.md` asserts *"The CLI default would have failed every design"*; `submission/.../reproducing_our_numbers.md:71-73` says the opposite — *"`predict.py` does default to `ESM1b`, so the tool's own default is the one that passes"*. The correction was propagated into the package and **not** into the reusable-knowledge file | **VERIFIED, live** |
| X3 | **The same entry mixes chains in its headline triple.** It quotes NetSolP variants as *"0.379 / 0.463 / 0.733"*. The real table (`docs/sessions/2026-09-16-netsolp-…:110-113`) is **VH 0.733 / 0.637 / 0.379** and **VL 0.569 / 0.463 / 0.346**. The published triple is ESM12-**VH**, Distilled-**VL**, ESM1b-**VH** — three variants across two chains. The migration log's proposed replacement test repeats the error | **VERIFIED, live** |
| X4 | `results/audit_2026-09-20.md` Check F still recommends light-chain redesign beneath a correct **REFUTED** banner | **VERIFIED** — presentation risk, same shape as X1 |
| X5 | **The reliability figure 0.629 does not reproduce and has never been corrected.** No standard estimator tried reproduces it; the plug-in gives **0.276** under `midpoint` and **0.296** under `top`. Flagged, not corrected (`STATE.md:332`) — *"guessing would add a fifth number to a project already carrying four"* | **VERIFIED, open** |
| X6 | `tests/test_invariants.py:182` documents a second non-reproducing figure: *"0.689 does not reproduce the published 3-seed 0.849; 0.653 does"* | **VERIFIED, open** |

**A test suite that passes proves nothing about itself.** The project ran a **mutation test**
(`results/mutation_test_2026-09-22.md`): five bugs reintroduced, five *localised* failures
(5 / 1 / 1 / 1 / 2 tests red), suite green after each restore. *"A green suite is a claim about
the code; a suite shown to go red on reintroduced defects is evidence about the suite."* What it
does **not** establish is stated too: five invariants pinned, nothing touching the scoring maths
beyond band edges.

**And the structural fact underneath all of Class 6:** the project had no tests and no version
control for its first eight days. `tests/` and `git` both arrive on **2026-09-22** (first commit
`f28870d`, 249 files). Until then *"every correction this project had ever made lived in prose,
and prose cannot fail a build."*

---

## Four findings that are recorded nowhere in the project

These are not in `STATE.md`'s open-items list, not in any results file's caveat block, and not
in the migration log. They are flagged here because a reader rebuilding from the docs alone
would otherwise inherit them silently.

1. **`results/challenge2_premise_recheck.md:53-62` re-states a withdrawn germline claim in bold,
   two lines after withdrawing it** (X1 above). The withdrawal is a parenthetical; the refuted
   version is the bolded sentence. Anyone skimming gets the wrong one.

2. **`LEARNINGS.md` still carries a NetSolP claim the submission retracted** (X2). The reusable
   knowledge file — the one loaded into every future session — asserts something the shipped
   package explicitly corrects. This is the propagation failure in its purest form: the fix went
   to the deliverable and not to the memory.

3. **That entry's "0.379 / 0.463 / 0.733" mixes VH and VL across three variants** (X3). It reads
   as one construct scored three ways. It is ESM12-VH, Distilled-VL and ESM1b-VH. The
   *conclusion* it supports — that only the ESM1b 5-fold ensemble passes a licensed antibody
   everywhere — is correct, and is exactly why the error is hard to see: the triple looks like
   evidence for a true claim. The proposed promotion test in the migration log repeats the
   mistake, which means the error was about to be mechanised.

4. **The project folded a 113-mer and shipped a 123-mer, and the two were never compared across
   the pipeline.** One qualification, in the project's favour and worth stating precisely: the
   2026-09-20 conformance session *did* re-fold the Challenge 1 finalist on the handbook's own
   constructs across 3 seeds and measured **DockQ −0.034 with no metric crossing a band edge**.
   What was never compared is everything else — the 239-design pool, the negative control, the
   calibration panel — and, more importantly, the *coverage* consequence for any epitope other
   than pembrolizumab's: the 113-mer holds **24/24 of pembrolizumab's epitope but only 8/14 of
   nivolumab's**. The finalist check answers "does the score move?"; it does not answer "is the
   antigen complete?", and the second question is the one that invalidated a control.

---

## Frequency analysis: where the systematic weakness was

Raw class counts mislead, because several incidents share one generator. Grouping by mechanism
is what locates the weakness.

| generator | instances | evidence |
|---|---|---|
| **1. A small-*n* null read as evidence of absence** | **≥6** | W4 (n=8, −0.168 → −0.432), W5 (n=40, −0.081 → −0.289), W19 (n=3, attainable p floor 0.100), `interaction_pae` ICC (n=10, detectable floor 0.317), the pilot's two-arm conditioning test, the "no code-path difference" chain. **Four corrected in a single day** |
| **2. A convention encoded twice, or nowhere** | **≥7** | S23 surrogate anchors vs config; S24 DockQ `interface_agg`; W15 Fab-vs-Fv; four band edges inclusive where the handbook is strict; the missing `design_X_pae.json`; the band→score mapping worth **12 points**; P8's midpoint-in-a-top-context |
| **3. A setting or construct inherited across a change of problem** | **≥5** | P1 `recycling_steps=3`; P2 Fv/Fab; P3 antigen-only MSA; P4 the 113-mer (**whole project**); `diffusion_samples=1` |
| **4. Exit code or row existence trusted instead of an artefact** | **≥6** | S7, S8, S10 (three Boltz exit-0s), S14 (rows), S15 (exit 0 after 239/239 failures), S17 (`TypeError` read as absence) |
| **5. `pgrep -f` self-matching** | **7** (3 in this project) | I9 **2 h 39 min**, I10 **1 h 22 min** + exit 144, I11 **21 min**; a seventh during the writing of this course |
| **6. A single observation compared to an aggregate** | **3** | W8 (seed 1 vs an 8-seed mean), W13 (pembrolizumab vs the max of 2000 scrambles), P10 (pool mean for one design, **in the shipped package**) |
| **7. A projection quoted as a measurement** | **4** | W21 (4,700 → ~1,290 folds), W22 (1.8× → 1.16×), W23 (4 min → 7.1 min), W17 (a "correction" that was itself wrong) |
| **8. A tool's default silently choosing for you** | **4** | S5 PRODIGY's interface, S6 DockQ's zero mismatches, NetSolP's model variant (**0.35 spread, wider than the cutoff-to-Good span**), `diffusion_samples=1` returning an **argmax by construction** |

### What this says

**The weakness was not the statistics and not the engineering craft.** The statistical work is
unusually careful — attenuation corrections, pre-registration, equal-budget resampling nulls,
mutation-tested tests — and when a result was attacked with the right instrument it usually
survived. The aromatic→DockQ correlation replicated to **0.002** on 239 independent designs; the
conditioning result survived the replacement of its own test by a stricter one.

**The weakness is inherited state that was never re-examined, and asymmetric scepticism.**

Generators 2, 3 and 8 are one thing seen three ways: **a value chosen once, for one purpose, in
one place, that travelled into a context where it was wrong — and nothing in the system could
notice, because the value lived in prose, in a signature default, or in a tool's defaults rather
than in an assertion.** `recycling_steps=3` cost a published `0/30`. The 113-mer cost a failed
positive control and the fact that what was folded was never what was shipped. The surrogate
anchors cost the identity of the winner. **Every one was free to check and none of them was,
until something downstream broke.**

Generator 1 is the asymmetry, and it is the cleanest self-diagnosis in the record: scepticism was
**directional**. Positive findings got noise floors, Fisher-z intervals, attenuation corrections
and reliability estimates; nulls got published. *"The rule was applied to positive findings and
not to nulls."* One sentence of discipline fixes it: **state the detectable effect beside every
null, or do not report the null.**

**Generator 5 is the purest measurement in this chapter, and it deserves its own paragraph.**
`pgrep -f` matches against a process's full command line, which means a wait loop gated on a
pattern can match a shell whose own argv contains that pattern — its own parent, its own
grandparent, or a stale harness process. The bracket trick (`[7]3_script.py`) defeats
self-matching *by the `pgrep` invocation itself* and does nothing about a heredoc that left the
whole script body inside a live parent's command line. Three instances in this project cost
**2 h 39 min + 1 h 22 min + 21 min = 4 h 22 min of idle GPU** — more than the entire Challenge 2
GPU rental. And the decisive fact: **all three occurred after the rule had already been written
down**, in the author's own notes before the project began and again in the project's own run
prompt. It stopped only when it became `.claude/hooks/pkill-guard.sh` — a mechanism, not a
sentence.

A seventh instance occurred **during the writing of this course**:
`pkill -f "from itertools import product"` matched its own command line and killed the shell that
issued it, exit **144**. That is the instance which makes the point the first six could not. The
lesson had by then been written down at least three times, taught in a chapter, and cited by
number — and it still fired. The hook is what stopped it. **A lesson recorded is not a lesson
mechanised**, and the gap between the two is measured in this project at four and a half hours of
idle GPU plus one dead shell. The same arithmetic holds for generator 2: S23 and S24 stopped
being possible on **2026-09-22**, the day `tests/test_invariants.py` existed, and not one day
earlier despite being documented for days.

**The generator that did the most damage per incident is the one no amount of statistics
reaches: W12.** The aromatic filter passed a rigorous, correctly-specified, correctly-nulled test
at p<0.0001 — and was refuted by asking the *same* test about a **different outcome variable**.
That failure mode cannot be caught by more seeds, more power, or a better null. It is caught only
by asking **what is this number actually *of*?** — which is also the question behind W15 (Fab
versus Fv inverts the causal story), behind the SKEMPI result (metrics that pass an epitope
knockout fail affinity with the wrong sign), and behind the project's closing honest claim:

> *"Our pipeline produces CDR-redesigned variants that a structure predictor scores as retaining
> pembrolizumab's binding mode, with reproducible design-to-design differences of unknown
> physical meaning."* — `results/audit_2026-09-20.md`, Construct validity

Not "we designed an antibody", and not "these designs bind PD-1". That the project ends able to
write that sentence, after nine days and a hundred-odd recorded failures, is the result.

---

## What to take away

**Sort your failures by how they announce themselves, not by subsystem.** Six of twenty-six
silent failures crashed or refused, which is the *good* outcome; three were caught by luck;
fifteen said nothing at all. Design for the fifteen: assert on artefacts, not exit codes; assert
that two encodings of one convention agree; assert that a resume predicate keys on the thing you
need rather than on a record existing.

**A null is a claim and needs the same power standard as a positive.** Four published nulls were
corrected in one day. The fix costs one clause: *no effect larger than x, where x is what this n
could detect.*

**A passing control is evidence about one confound and nothing else.** C1 correctly exonerated
the Fv construct and printed a verdict that was wrong within the hour, because it ran at the
setting that was actually the problem. Choose controls that *could* have failed for the reason
you fear.

**Read an aggregate's `n` before you compare anything to it.** Three instances, the third inside
the shipped deliverable, the second committed after the first had been written into the project's
permanent notes.

**A recorded lesson is not a mechanised one.** 4 h 22 min of idle GPU from one `pgrep` pattern,
all of it after the rule was written down — and a seventh instance fired while this course was
being written, killing the shell that issued it with exit 144. A ten-line hook stopped what three
write-ups could not. If a lesson matters, the next thing you write is the test or the hook, not a
better sentence about it. And check the story the mechanism tells: the module docstring enforcing
this project's most-repeated rule mis-enumerates its own evidence, and a test propagated the
error.

**And the question that no statistical machinery answers: what is this number actually of?**
Pose retention against a parent crystal is not binding. A predictor's own confidence is not
accuracy. A metric that passes an epitope knockout can still rank binding-abolishing mutants
above the wild type. Ask what the outcome variable *is* before you optimise against it.

Continue with [[09-critique|the adversarial reading of what the nine days established]], or go
back to [[05-experiment-design|how to design a control that could actually fail]].
