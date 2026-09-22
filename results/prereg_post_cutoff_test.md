# Pre-registration — the post-training-cutoff test

**Written 2026-09-17, BEFORE target selection and before any fold was run.** Nothing
below was chosen after seeing a result. Git is not in use here, so the guarantee is
the timestamp and the fact that `runs/postcutoff/` did not exist when this was written.

## 1. The question

Every empirical claim in this project traces to 5GGS (released 2017), which is inside
Boltz-2's training data. Two things depend on whether those claims survive on molecules
the model has never seen:

1. **Challenge 2 viability** — it requires placing an antibody the model has not
   memorised. DockQ 0.820 on a memorised complex is no evidence for that.
2. **The 2026-09-17 finding** that ipSAE is a liveness test rather than a ranking
   metric. It was derived from mutants of a memorised complex. If confidence behaves
   differently on novel structures, that finding is an artefact, not a property.

## 2. Boltz-2's training cutoff — established, not assumed

**2023-06-01, on PDB RELEASE date.** Verified by reading the Boltz-2 paper directly
(`jeremywohlwend.com/assets/boltz2.pdf`), not from a search summary:

> "We use every PDB structure up to the training date cutoff of 06/01/2023."  (A.1, PDB data)
> "...all entries from the MD datasets correspond to PDB structures released before the
>  validation cutoff date of 2023-06-01"  (A.1)

The second quotation is what fixes it to *release* date rather than deposition date.
Installed model is `boltz 2.2.1`.

**Margin adopted: targets must have been RELEASED on or after 2024-01-01**, i.e. at least
7 months clear of the cutoff, to absorb any ambiguity about point releases or data
refreshes.

## 3. Target selection criteria — fixed in advance

1. Protein antibody–antigen complex (Fab or Fv + protein antigen) solved by X-ray or cryo-EM.
2. **PDB initial release date ≥ 2024-01-01.**
3. Antigen is a protein, and **not** a promiscuous benchmark antigen — lysozyme, HIV gp120,
   influenza HA, SARS-CoV-2 spike RBD are excluded. A memorised antigen flatters the result
   even when the antibody is novel.
4. **Novelty screen:** for each target, the maximum sequence identity of its heavy chain
   to any antibody chain in a pre-cutoff PDB entry is measured and reported. A target whose
   antibody has a ≥95% identical pre-cutoff relative is rejected as partly retrieval.
   The closest identity found is reported for every target, accepted or rejected.
5. Total complex ≤ ~700 residues, so the Fab fold fits 12 GB VRAM (measured: 549 res -> 7.6 GB).
6. **n = 5** targets. Not 3, not 4 — see §5.

## 4. Analysis, fixed in advance

### 4.1 Level — the Challenge 2 go/no-go

Median DockQ across the 5 targets, Fab construct, against the released crystal:

| band | criterion | reading |
|---|---|---|
| **PASS** | median ≥ 0.49 **and** ≥3/5 targets individually ≥ 0.49 | the plan's G1b bar; CAPRI medium quality |
| **MARGINAL** | median in [0.23, 0.49) | CAPRI acceptable but below the project's bar |
| **FAIL** | median < 0.23 | the binding mode is not recovered |

Separately and regardless of band: the drop from 5GGS's 0.820 is reported. A "pass" at
0.55 is still a large degradation and must be described as one.

### 4.2 Relationship — does the ipSAE calibration survive?

Each target folded as **both Fv and Fab** and compared against the construct's OWN curve,
fitted on the 14-variant panel (seed 1):

| curve | fit | residual sd | n |
|---|---|---|---|
| **Fv (PRIMARY)** | ipSAE = 0.421 + 0.527 x DockQ | **0.043** | 14 |
| Fab (secondary) | ipSAE = 0.364 + 0.566 x DockQ | **0.088** | 14 |

Verdict on the mean residual of the 5 new points, in units of its own standard error:

- **ON THE CURVE**: |mean residual| < 2 SE -> calibration survives novel structures; the
  liveness finding generalises.
- **ABOVE**: mean residual > +2 SE -> ipSAE is *more* optimistic on unseen molecules than
  the panel showed. Strengthens the liveness finding and worsens the Challenge 2 outlook.
- **BELOW**: mean residual < -2 SE -> ipSAE is more conservative on novel structures.

Residuals reported per target in sd units, as was done for the AF2 point (which sat 3.1 sd low).

## 5. Power — and what this test CANNOT do

Minimum detectable offset, two-sided alpha=0.05, power 0.80, using
`MDE ~ 2.80 * sd * sqrt(1/n_new + 1/n_curve)`:

| n targets | vs Fv curve | vs Fab curve |
|---|---|---|
| 3 | 0.076 | 0.157 |
| 4 | 0.068 | 0.140 |
| **5** | **0.062** | **0.128** |
| 8 | 0.053 | 0.109 |

**This is why both constructs are folded and why the Fv comparison is primary.** Folding
as Fab alone, as originally scoped, would give MDE 0.140 at n=4 -- unable to reliably
detect even the AF2-sized offset of 0.131. The test would have been close to useless.

The Fv curve is tighter (0.043 vs 0.088) even though Fv ipSAE is the *less reliable*
instrument (seed reliability 0.607 vs 0.965). This is not a contradiction: the Fv's elbow
noise is correlated between ipSAE and DockQ, because both are computed from the same
structure, so a wobbly elbow moves a point ALONG the curve rather than off it. Fv is a poor
absolute instrument and a good relative one. G1c's Fab-only decision concerned *ranking*
and is unaffected.

**Declared in advance:** at n=5 a null result means **"no offset larger than ~0.062"**, NOT
"no offset". An offset of 0.03-0.05 is real and undetectable here. If the result is
ambiguous that is an accepted outcome and will be reported as ambiguous. The MDE formula
also ignores the leverage term `(x0 - xbar)^2 / Sxx`, so it is mildly optimistic if the new
targets' DockQ values cluster far from the panel's mean DockQ; the realised leverage will
be reported.

## 6. Run protocol

Seed 1, one fold per target per construct, untemplated, antibody chains `empty` MSA, cached
antigen MSA where the antigen is the same (it is not -- each target has its own antigen, so
each gets its own alignment from the MMseqs2 server; all targets are PUBLISHED structures so
the server is a fair use here, unlike for designs).

Existing driver (`src/locksmith/fold/boltz.py`) and scoring path
(`scripts/07_score_panel.py` logic). **No special-casing.** Failures are reported, not retried
with different settings.

**No target will be added, removed or substituted after any result is seen.**
