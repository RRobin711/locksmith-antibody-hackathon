# Two findings from the matched control that belong in the argument

**2026-09-23.** Both come from folding real antibodies against the handbook's own
123-residue PD-1 construct, under a verified-used alignment, recycling 10, 5 diffusion
samples. Neither is about our designs, which is what makes them worth more.

---

## 1. An anti-HER2 antibody clears the viability cutoff on one draw of five

**Trastuzumab against PD-1**, per-sample ipSAE:

| model_0 | model_1 | model_2 | model_3 | model_4 | median |
|---|---|---|---|---|---|
| **0.740** | 0.210 | 0.057 | 0.000 | 0.000 | **0.057** |

Its best sample is **0.740**, comfortably over the §7.2 cutoff of 0.60. Its median is
**0.057**, at the floor.

Trastuzumab is a licensed anti-HER2 antibody. It has no relationship to PD-1. Under a
**correct alignment**, on the **handbook's own antigen construct**, at the sampling depth
this project now uses, it produces one draw in five that the rubric would certify as
viable.

**This is the argmax hazard measured on a negative control rather than on our own
designs**, which is what makes it the strongest version of the finding in the project.
Every previous demonstration — `model_0` being Boltz's own top-ranked output, 5 of 30
re-screen designs having a sample above 0.60 while 1 clears on the median — was measured
on molecules we made. This one is measured on a molecule that is definitively wrong, and
it still passes one time in five.

`diffusion_samples=1` returns Boltz's top-ranked model, which is an argmax by
construction. On this evidence a single-sample run has a real chance of certifying an
anti-HER2 antibody as a PD-1 binder.

**This is the direct argument for median-of-five as the selection rule**, and it is why
every number in this submission is reported as a median with its spread rather than as the
model the package ships.

---

## 2. A licensed anti-PD-1 drug is non-viable on the construct the handbook specifies

**Nivolumab**, folded on the handbook's 123-residue antigen:

| construct | nivolumab median ipSAE | verdict |
|---|---|---|
| handbook 123-mer (`DSPDRP…`) | **0.474** | **FAILS §7.2** |
| repaired 119-mer (`LDSPDR…`) | **0.691** | passes |

Nivolumab is an approved checkpoint inhibitor whose target is PD-1. It fails the
handbook's own viability gate on the handbook's own antigen — and recovers as soon as six
residues are restored to the N-terminus.

**The epitope analysis predicted this before either fold existed.** Nivolumab's epitope is
14 residues, of which **L25 D26 S27 P28 D29 R30** are the N-terminal `LDSPDR` segment. The
handbook construct begins at `DSPDRP`, covering 13 of 14 and missing **L25**. The
113-residue construct used for screening covers only 8 of 14 (57.1%), which is why
nivolumab scored **0.017** there. Pembrolizumab's 26-residue epitope is 100% inside all
three constructs, which is why it scores 0.843–0.877 regardless and why the truncation was
invisible for the entire project.

**This is a criticism of the rubric grounded in a real drug rather than in a metric
argument.** The handbook specifies an antigen construct; that construct cannot serve one of
the two licensed antibodies against its own target. A team evaluating a nivolumab-like
epitope would be marked non-viable for choosing a clinically validated binding site.

The pairing is the point. **0.474 on the specified construct, 0.691 on the repaired one,
same antibody, same pipeline, six residues apart.**
