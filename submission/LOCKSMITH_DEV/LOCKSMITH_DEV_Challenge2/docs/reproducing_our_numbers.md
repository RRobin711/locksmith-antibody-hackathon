# Reproducing every number we report — Challenge 2

Written because a reviewer should be able to re-derive our numbers from what we handed
over, and because Challenge 1 ships this file and Challenge 2 did not.

## Seven metrics, not eight

§5.2 applies DockQ to Challenge 1 only — a de novo design has no reference structure. So
`DockQ` is absent here, and with it **the only metric in the rubric that compares the
prediction to anything external.** Every number below is computed from the two files in
`structures/`, which we generated. A confidently wrong pose scores exactly like a right one.

| metric | source | our value |
|---|---|---|
| `ipsae` | `vendor/ipsae/ipsae.py` on the PAE JSON + PDB, cutoffs 10/15 | 0.904 |
| `dg`, `contacts` | PRODIGY, chain selection `A,B` vs `C` | -10.9, 99 |
| `iface_plddt` | mean B-factor over interface residues, 5.0 Å heavy-atom | 88.62 |
| `cdr_sasa` | freesasa over the six CDRs, `bound` state | 1110.5 |
| `netsolp` | NetSolP **ESM1b** (the tool's own default), Fv, `min` over chains | 0.555 |
| `cdrh3_identity` | **human germline**, not Keytruda — see below | 18.2% |

## The one that needs explaining: novelty against germline

§6.3.1 scores Challenge 2 novelty as CDR-H3 identity *"compared to human germline CDR
sequences"*, and does not say how. **CDR-H3 has no single germline template**: it spans the
V(D)J junction, and the N-region insertions have no germline counterpart at all. So the
metric is a best-match search, not a string comparison, and the convention has to be
declared.

Ours (`src/locksmith/metrics/germline.py`): best **exact V prefix** + best **D substring,
3 forward reading frames** + best **exact J suffix**, non-overlapping, scored as
`covered / len(query)`. V is a prefix and J a suffix because exonuclease trimming removes
segment *ends*; D is a substring because it is trimmed at both ends and read in any frame.

**The convention moves the number.** Scoring the same CDR-H3 as best global-alignment
identity against any single germline segment (`best_segment`) gives **27.3%**, where
the V(D)J-coverage reading we report as `cdrh3_identity` gives **18.2%**.
Both readings are defensible against §6.3.1's wording and **both are far inside the Good
band (<70%) and the <95% cutoff**, so nothing about the score turns on it. We record the
disagreement rather than hide it.

Validated on cases whose answers are derivable: a verbatim germline junction scores
**100.0%**, and **242 of 249** IGHV alleles return themselves (the 7 others are exact ties).

## Verifying the package end to end

```
uv run python scripts/58_validate_submission.py submission/LOCKSMITH_DEV
```

Reads **only** this folder — no run directory, no cached score — and re-derives all seven
metrics. Exits non-zero on any structural problem or failed cutoff.

## Provenance

Backbones came from RFdiffusion/RFantibody on a rented RTX 3090 and were retrieved to local
disk; **all 258 artefact files are sha256-verified against the server**. The structure here
was folded locally with Boltz-2 at `recycling_steps=10`, seed 1, `diffusion_samples` 5 with
`model_0` submitted. **Both of those settings move the score** — see
`methods_and_limitations.md`, which gives the measured envelopes rather than a single
number.
