# Constrained re-design: 18 of 18 backbones yield a §9.2-clean sequence

**2026-09-23.** Sequence-only, CPU, ~3.5 minutes for the whole measurement. No folds, no GPU,
no money.

## The result

| | |
|---|---|
| backbones producing a §9.2-clean sequence | **18 / 18 (100%)** |
| attempts needed | median **1**, max **3** |
| distribution | 11× attempt 1, 6× attempt 2, 1× attempt 3 |
| per-backbone time | 6–21 s |
| *compare:* unconstrained generation avoiding these motifs | **5 / 30 sequences (17%)** |

## Why those two numbers are not in conflict

**17% is the rate at which a sequence happens to avoid the motifs. 100% is the rate at
which a backbone can be made to.** They measure different things and only the second one
matters for campaign design.

The loop: generate 8 sequences on a backbone; scan for N-X-S/T sequons and NG/DG motifs
**inside CDRs**; if a sequence is clean, stop; otherwise forbid the offending residue **at
those positions only** and re-sample, accumulating constraints. ProteinMPNN re-picks the
surrounding residues under the constraint rather than having one residue swapped underneath
a finished sequence.

That distinction is the whole finding. The fix arms
([all three collapsed](liability_fix_arms.md), including one at zero contacts) tested
**post-hoc point mutation breaking a joint optimisation**. This tests whether a clean
sequence *exists* on the backbone. It does, essentially always, and usually on the first try.

## What this settles for the campaign

**The liability requirement goes in at generation and the gate question disappears.**
Nothing is discarded, so the anti-selection risk measured on the existing pool — where a
hard gate kept 5 of 30 sequences and all five scored ipSAE 0.000, dropped group
significantly higher at p=0.015 — never arises. We are not filtering the network's output;
we are constraining its input and letting it route around.

Cost to the campaign: **negligible.** A median of one extra sampling pass, seconds per
backbone, entirely on CPU, before any GPU time is spent.

## What it does NOT establish

**That the clean sequences bind.** This measures only that §9.2-clean sequences exist on
these backbones and are easy to reach. Whether constrained sequences fold to viable
interfaces is unmeasured and requires GPU time — it is the campaign's actual question, not
this one's.

There is a real reason for caution: the constraint removes asparagine at specific CDR
positions, and Asn is a workhorse paratope residue. The network compensating at
*neighbouring* positions is exactly what should happen, but whether the compensated
interface is as good is an empirical question. **The honest expectation is that constrained
sequences fold somewhat worse than unconstrained ones on average**, and the campaign should
measure that rather than assume the constraint is free in binding terms as well as in
compute terms.

## Five bugs on the way to this number, all silent, all mine

Recorded because four of the five produced plausible output and the fifth only failed on
the fifth backbone:

1. **Chain labels.** `liabilities` says `'heavy'`/`'light'`; ProteinMPNN's `omit_AA_dict`
   is keyed by chain **letter**. Keys never matched, `tied_featurize` applied no
   constraint, and the loop silently degraded to plain resampling while printing per-backbone
   results.
2. **`pkill -f` self-match**, exit 144 — the eighth instance on this project. It killed the
   shell mid-patch, so the fix never reached disk.
3. **Unverified patch.** I then launched the script assuming the patch had applied. It had
   not. Patches are now verified with a grep before the run.
4. **The separator that isn't there.** `generate_sequences` returns masked chains
   **concatenated with no delimiter** — a single 231-character string for a 122+109 Fv.
   `s.split("/")` gave one element, `if len(parts) < 2: continue` skipped **every** sequence,
   and the run reported **0/18 clean** having scanned nothing. That reads exactly like
   "these backbones cannot produce clean sequences" — the finding that would have killed
   the campaign.
5. **Missing chains in `omit_AA_dict`.** `tied_featurize` indexes every chain letter without
   guarding, so a chain with no constraints needs an explicit empty list. Failed loudly, and
   only on the first backbone whose violations fell on one chain.

**What caught #4 was a disagreement between two numbers that should have matched:** the
scan reproduced 5/30 clean on the original sequences *exactly*, which proved the scan right
and therefore the sampling wrong. Without that anchor the 0/18 was entirely believable.

**The guard that now exists:** after any constrained attempt, the loop asserts the
forbidden residue is **absent** at the constrained position and exits if not. Absence of an
error is not evidence a constraint applied — the same principle the campaign plan demands
for the MSA, which I wrote down and then failed to apply to my own code.
