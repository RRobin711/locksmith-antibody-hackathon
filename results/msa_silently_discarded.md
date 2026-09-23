# Every Challenge 2 number came from a fold with no antigen alignment

**2026-09-23.** This supersedes the earlier version of this file, which reported the
discard as a defect in the *shipped* fold only. Measurement shows it affected **every
Challenge 2 fold this project ever ran**, and that the design's viability is an artefact
of it.

## The result

Four folds, one script, identical driver / seed / sampling depth / flags. Only the design
and the presence of an antigen alignment vary. Median of five diffusion samples:

| | antigen MSA **used** | antigen MSA **absent** |
|---|---|---|
| **baseline** (pre-sequon-fix) | **0.012** | **0.773** (0.736–0.864) |
| **S→A** (the shipped design) | **0.012** | **0.686** (0.619–0.781) |

Supporting metrics move together: with the alignment absent, ~97 heavy-atom contacts,
ΔG ≈ −11 to −12, interface pLDDT ≈ 84. With it present, ~70 contacts, ΔG ≈ −10,
interface pLDDT ≈ 73.

**The mutation is irrelevant to the effect.** Both designs read 0.012 with an alignment
and both read high without one. The earlier reading — that S→A specifically required the
MSA's absence — is wrong and is withdrawn. What suppresses the interface is giving the
antigen evolutionary information at all.

**The no-MSA cells reproduce the project's historical numbers exactly.** `base_nomsa`
returns 0.736–0.864, which is the envelope recorded for this design in the r10 screening
and the diffusion-samples run. So these are not new folds disagreeing with old ones; they
are the same condition, reproduced.

## Every Challenge 2 fold was in the no-MSA condition

The FASTAs are unambiguous. `runs/challenge2_fold_r10/*/**.fasta` — the screening that
produced "1 of 30 designs clears" — carry:

```
>C|protein|/home/rrobin711/.cache/locksmith/msa/pd1_5ggs.csv
DSPDRPWNPPTFSPALLVVTEGDNATFT…          (123 residues)
```

and `pd1_5ggs.csv` has a **113**-residue query. Boltz's featurizer compares
`len(residues) == len(first_residues)`, and on mismatch prints
`Warning: MSA does not match input sequence, creating dummy.` and calls `dummy_msa`. The
check is on **length alone**; the cached query is an exact substring of the antigen at
offset 5 and is treated exactly like an unrelated sequence.

Warning counts: `runs/sequon_fix.log` **2** (both arms), `runs/diffusion_samples.log`
**1** (the Challenge 2 arm; the Challenge 1 arm used a server MSA and is unaffected).

## Why nobody saw it — three independent layers

1. **The warning went into a captured pipe.** `fold()` runs boltz with
   `subprocess.run(capture_output=True)` and surfaces stdout only when `assert_artefacts`
   raises. A fold that *succeeds* discards its own warnings.
   `runs/challenge2_refold_r10.log` is **34 lines containing zero boltz output**.
2. **The artefact suggests the opposite.** The processed `msa/*.npz` still records 1024
   sequences at width 113, because the discard happens later, at featurisation. Inspecting
   the file implies the alignment was used.
3. **Nothing failed.** Exit 0, every expected file present, every metric computable, the
   composite in the Good band.

## What this invalidates

- **"1 of 30 designs clears the gates"** — measured entirely in the no-MSA condition.
  With an alignment, the design that cleared scores **0.012**.
- **The shipped Challenge 2 design is not viable under a correct fold.** ipSAE 0.012
  against a 0.60 cutoff.
- **"S→A costs 4.8 composite points."** Withdrawn twice over: the arms differed in
  construct and alignment as well as sequence, and the 2×2 now shows the mutation
  contributes almost nothing in either column.

## What survives

- **`N→Q` kills the interface where `S→A` does not**, *within the no-MSA condition* where
  both were measured (0.014 vs 0.619–0.781). The contact-count rule that predicted it is
  untouched. Whether it holds with an alignment present is **not known** — both cells of
  that comparison would now read ≈0.012, so the experiment cannot be re-run meaningfully
  on this design.
- **Challenge 1 is unaffected.** Its folds used a server-derived MSA matched to its own
  antigen; `runs/diffusion_samples.log` shows the warning once, for the Challenge 2 arm
  only.
- **Every calibration-panel and negative-control fold in this session is unaffected** —
  the panel queries the server per antigen, and the negative control's 113-mer matches its
  cached query exactly (0 warnings in either log).

## What it does *not* establish

That the design cannot bind. ipSAE 0.012 means **Boltz will not place this antibody on
PD-1 when it has evolutionary information about the antigen** — a statement about the
predictor's confidence, not an experiment. But it removes the only evidence the project
had in the other direction, and it removes it for every Challenge 2 number simultaneously.

The honest summary is that **Challenge 2 has no surviving computational evidence of
binding**, and the epitope-targeting evidence (17/18 backbones beating a contiguous-patch
null) is unaffected because it is geometric and does not depend on a fold.

## The guards

Two, because the first only covers the pairing we now know about:

- `write_input` **raises** when a cached alignment's query length differs from the antigen
  (`allow_msa_mismatch=True` for `scripts/94`/`95`, which reproduce it deliberately).
  Pinned by `test_write_input_refuses_an_msa_that_boltz_would_discard`.
- `fold()` **scans captured stdout** and raises on `MSA does not match input sequence` or
  `Number of failed examples`, because a warning nobody reads is not a warning. Pinned by
  `test_fold_raises_on_a_boltz_warning_that_only_reaches_stdout`.

## The transferable principle

**A tool that degrades instead of failing will produce your best-looking numbers.** Boltz
had three reasonable options on a mismatched alignment — error, re-align, or drop it — and
chose the one that keeps running. Every layer downstream then made the choice invisible:
captured stdout, an artefact written before the decision, and a successful exit.

Check, for anything expensive you depend on, **what it does when its input is wrong**, and
verify from the output that it did what you asked rather than something adjacent. Here the
question "was the MSA actually used?" was never asked in six days, and the answer was one
`grep` away in a log that was never written.
