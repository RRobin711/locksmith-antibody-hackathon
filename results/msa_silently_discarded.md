# The shipped Challenge 2 structure was folded with no antigen alignment

**2026-09-23.** Found while chasing an unrelated inconsistency in the deck. This is the
most serious defect found in the submission, and it is a *silent* one: nothing failed,
nothing scored zero, and every artefact looks normal.

## The finding

`data/msa_cache/pd1_5ggs.csv` is a multiple sequence alignment whose query is the
**113-residue** PD-1 construct beginning `PWNPP`. The fold that produced the shipped
Challenge 2 structure (`scripts/82_sequon_fix.py`, the S→A sequon fix) passed that cache
alongside the handbook's **123-residue** antigen beginning `DSPDRP`.

Boltz did not error. It **discarded the alignment and replaced it with a dummy**, so the
antigen was effectively folded in single-sequence mode.

## The mechanism, read from the source rather than inferred

`boltz/data/feature/featurizerv2.py`, the block that attaches an MSA to a chain:

```python
warning = "Warning: MSA does not match input sequence, creating dummy."
if len(residues) == len(first_residues):
    ...                      # lengths agree: use the MSA (MET/UNK mismatches tolerated)
else:
    print(warning, "2", ...)
    msa[chain_id] = dummy_msa(residues)      # lengths differ: THROW THE MSA AWAY
```

The check is on **length alone**. There is no re-alignment and no attempt to locate the
query inside the input; a query that is a perfect substring of the input at offset 5 is
treated exactly like an unrelated sequence. The failure is announced on stdout and
nowhere else — no exception, no non-zero exit, no marker in any output file.

## The evidence

| observation | value |
|---|---|
| cached MSA query length | **113** residues (`PWNPPTFSPALL…`) |
| antigen folded in `sq_sa` | **123** residues (`DSPDRPWNPPTFSPALL…`) |
| query located inside the antigen | offset **5**, exact substring |
| processed alignment width written | **113** columns for a 123-residue chain |
| `"MSA does not match input sequence"` in `runs/sequon_fix.log` | **2** (one per arm), branch **`2`** = the length-mismatch path |
| same warning in any 113-mer fold log | **0** |

The processed `msa/sq_sa_0.npz` still records 1024 sequences at width 113 — the discard
happens at *featurisation*, in memory, after that file is written. **Reading the processed
MSA would have suggested the alignment was used.** Only the stdout warning and the source
tell the truth.

## What it invalidates, and what it does not

**Invalidated: the claim that the S→A sequon fix costs 4.8 composite points.**
That number compares:

- the **baseline** at 96.0 — folded in `runs/diffusion_samples/ds_ch2` on the **113-mer**
  with the cached MSA **in use**, and
- the **S→A variant** at 91.2 — folded in `runs/sequon_fix` on the **123-mer** with the
  MSA **silently discarded**.

Three things change between those arms at once: the two serine mutations, the antigen
construct (113 → 123), and the presence of the antigen alignment. The 4.8-point cost is
attributed entirely to the mutations and **cannot be**, on this evidence. The session doc
that recorded the cost as "unexplained" was closer to right than the confident version.

**Not invalidated: `N→Q` kills the interface while `S→A` does not.** Both arms ran in the
same script, same construct, same discarded MSA, so the comparison between them is
internally valid. ipSAE 0.864 → 0.014 for `N→Q` against 0.619–0.781 for `S→A` stands, and
so does the contact-count rule that predicted it.

**Not yet known: whether the shipped structure is materially worse for it.** An antibody
chain carries `empty` by design in this pipeline — an antibody and its antigen have not
co-evolved — so the question is only what the *antigen's* alignment was worth.
`scripts/94_msa_register.py` measures it directly, three folds, all else identical:

| arm | antigen | alignment | isolates |
|---|---|---|---|
| `as_shipped` | 123-mer | cached (discarded → none) | reproduces the shipped fold |
| `matched_113` | 113-mer | cached (used) | the alignment, at the screening construct |
| `matched_123` | 123-mer | fresh query for that sequence | the alignment, at the shipped construct |

`as_shipped` vs `matched_123` isolates the alignment at constant construct, which is the
quantity that matters. Decision rule fixed before running: `~=` means inside this design's
measured diffusion envelope (composite 91.2 on all five samples, ipSAE 0.619–0.781).

## How it was found, and why that matters

Not by looking for it. The chain was: a deck slide contradicted itself on Challenge 2's
score (96.0 on slide 1, 91.2 on slide 8) → tracing that showed the deck read a *run
directory* rather than the *package* → sweeping for the same number elsewhere found an
overstated envelope inside the shipped docs → checking which construct produced the
shipped structure showed it was the 123-mer, not the 113-mer I had claimed → which made
the cached 113-column MSA an obvious mismatch → which the source and the log confirmed.

**Five inconsistencies deep, starting from a cosmetic one.** The transferable point is that
the cheap contradiction was worth chasing: a number that disagrees with itself is the only
free evidence you get that something upstream is wrong.

## The guard

A length mismatch between a cached alignment and the sequence it is handed to is now an
error rather than a warning on someone else's stdout:
`locksmith.fold.boltz.write_input` refuses to write a FASTA whose antigen length differs
from its cached MSA's query length. Pinned by
`tests/test_invariants.py::test_write_input_refuses_an_msa_that_boltz_would_discard`.
