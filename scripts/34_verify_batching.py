#!/usr/bin/env python3
"""Acceptance test for batched folding, in three tiers.

WHY THREE AND NOT TWO. The brief specified byte-identity at batch 1 and statistical
equivalence above it. That is right, but it is not *interpretable* on its own: if
byte-identity fails at batch 1, we cannot tell whether the batching code changed the
result or whether Boltz simply is not bitwise reproducible run-to-run on this GPU.
So tier 0 establishes that first, by running the EXISTING single-fold path twice on
the same design and seed. Only if tier 0 shows determinism does a tier-1 failure
implicate the new code.

  tier 0  determinism control : single path, same design+seed, run twice
  tier 1  byte-identity       : batch-of-1 vs single path, same design+seed
  tier 2  equivalence at N>1  : batch-of-6 vs single path, DockQ within +/-0.054
                                (3 x the measured 0.018 seed sd)
  tier 3  speed               : per-fold wall clock, batched vs single

Uses a seed NOT used elsewhere (11) so nothing here can be mistaken for campaign data,
and writes to runs/batch_verify/ which no analysis reads.

Writes results/m3_batching.md.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path

from locksmith.config import load
from locksmith.fold import boltz as single
from locksmith.fold.batch import BatchItem, fold_batch
from locksmith.metrics import dockq as dockq_metric
from locksmith.types import Provenance, Structure

POOL = Path("designs/wide_temp/designs.json")
OUT = Path("runs/batch_verify")
REPORT = Path("results/m3_batching.md")
NATIVE = Structure(pdb=Path("data/refs/prepared/5ggs_ABZ.pdb"),
                   provenance=Provenance.EXPERIMENT, label="5GGS")
SEED = 11
N_BATCH = 6


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def dq(pdb: Path, pae: Path, label: str, cfg) -> float:
    st = Structure(pdb=pdb, provenance=Provenance.PREDICTION, pae=pae,
                   label=label, predictor="boltz2")
    return dockq_metric.compute(
        st, NATIVE,
        allowed_mismatches=cfg.conventions["dockq_allowed_mismatches"])["dockq"].value


def main() -> int:
    cfg = load()
    pool = json.loads(POOL.read_text())
    items = pool[:N_BATCH]
    a = items[0]
    L, w = [], None
    L = []
    w = L.append
    w("# Does batched folding reproduce the single-fold path?")
    w("")
    w(f"`scripts/34_verify_batching.py`, seed {SEED} (used nowhere else so these folds "
      f"cannot be mistaken for campaign data).")
    w("")

    # ---- tier 0: is the single path even deterministic? ----
    print("tier 0: determinism control (2 single folds)...", flush=True)
    r0a = single.fold(f"{a['design_id'].replace('.','p')}__v0a", a["heavy"], a["light"],
                      a["antigen"], out_root=OUT, construct="fab", seed=SEED)
    r0b = single.fold(f"{a['design_id'].replace('.','p')}__v0b", a["heavy"], a["light"],
                      a["antigen"], out_root=OUT, construct="fab", seed=SEED)
    det = sha(r0a.pdb) == sha(r0b.pdb)
    w("## Tier 0 — is the single-fold path itself reproducible?")
    w("")
    w(f"Same design, same seed, two separate invocations of the EXISTING path.")
    w("")
    w(f"| run | PDB sha256 (16) | seconds |")
    w(f"|---|---|---|")
    w(f"| a | `{sha(r0a.pdb)}` | {r0a.seconds:.0f} |")
    w(f"| b | `{sha(r0b.pdb)}` | {r0b.seconds:.0f} |")
    w("")
    w(f"**Bitwise reproducible: {det}.** " + (
        "So byte-identity is a meaningful acceptance test for the batching code, and a "
        "tier-1 failure would implicate that code rather than the GPU."
        if det else
        "Boltz is NOT bitwise reproducible run-to-run on this GPU even through the "
        "unchanged path, so byte-identity CANNOT be used as an acceptance test for "
        "batching — a mismatch at tier 1 would be uninterpretable. Tier 1 is therefore "
        "reported but not treated as a gate, and tier 2's equivalence test carries the "
        "verdict. This is exactly why tier 0 exists."))
    w("")

    # ---- tier 1: batch of 1 ----
    print("tier 1: batch-of-1...", flush=True)
    b1 = fold_batch([BatchItem(f"{a['design_id'].replace('.','p')}__v1", a["heavy"],
                               a["light"], a["antigen"])],
                    out_root=OUT, seed=SEED, construct="fab")
    k1 = next(iter(b1.results))
    same1 = sha(b1.results[k1].pdb) == sha(r0a.pdb)
    w("## Tier 1 — batch of 1 against the single path")
    w("")
    w(f"| path | PDB sha256 (16) |")
    w(f"|---|---|")
    w(f"| single | `{sha(r0a.pdb)}` |")
    w(f"| batch-of-1 | `{sha(b1.results[k1].pdb)}` |")
    w("")
    w(f"**Identical: {same1}.**" + ("" if det else
      " (Not a gate — tier 0 showed the path is not bitwise reproducible anyway.)"))
    w("")

    # ---- tier 2: batch of N ----
    print(f"tier 2: batch-of-{N_BATCH}...", flush=True)
    bN = fold_batch([BatchItem(f"{d['design_id'].replace('.','p')}__v2", d["heavy"],
                               d["light"], d["antigen"]) for d in items],
                    out_root=OUT, seed=SEED, construct="fab")
    print("  scoring batch members against single-path folds...", flush=True)
    rows = []
    for d in items:
        lab = f"{d['design_id'].replace('.','p')}__v2"
        if lab not in bN.results:
            rows.append((d["design_id"], None, None, None))
            continue
        s = single.fold(f"{d['design_id'].replace('.','p')}__v2s", d["heavy"], d["light"],
                        d["antigen"], out_root=OUT, construct="fab", seed=SEED)
        db = dq(bN.results[lab].pdb, bN.results[lab].pae, lab, cfg)
        ds = dq(s.pdb, s.pae, lab + "s", cfg)
        rows.append((d["design_id"], ds, db, db - ds))
    w(f"## Tier 2 — batch of {N_BATCH}, DockQ equivalence")
    w("")
    w("Tolerance is **±0.054 DockQ**, three times the measured 0.018 seed sd. Kernel "
      "selection depends on tensor shape, so a batched forward pass can differ in the "
      "low-order bits even at a fixed seed; the question is whether it differs by more "
      "than the noise we already tolerate between seeds.")
    w("")
    w("| design | DockQ single | DockQ batched | Δ | within ±0.054 |")
    w("|---|---|---|---|---|")
    ok2 = True
    for did, ds, db, delta in rows:
        if ds is None:
            w(f"| {did} | — | **FAILED IN BATCH** | — | ✗ |"); ok2 = False; continue
        good = abs(delta) <= 0.054
        ok2 &= good
        w(f"| {did} | {ds:.3f} | {db:.3f} | {delta:+.3f} | {'✓' if good else '✗'} |")
    w("")
    w(f"**Equivalent: {ok2}.**  Batch failures: {len(bN.failures)}"
      + (f" — {list(bN.failures)}" if bN.failures else ""))
    w("")

    # ---- tier 3: speed ----
    single_mean = (r0a.seconds + r0b.seconds) / 2
    speedup = single_mean / bN.per_fold_seconds if bN.results else float("nan")
    w("## Tier 3 — the speed-up, measured")
    w("")
    w("| quantity | value |")
    w("|---|---|")
    w(f"| single-fold wall clock (mean of 2) | {single_mean:.0f} s |")
    w(f"| batch of {N_BATCH}: total | {bN.seconds:.0f} s |")
    w(f"| batch of {N_BATCH}: per fold | **{bN.per_fold_seconds:.0f} s** |")
    w(f"| **speed-up** | **{speedup:.2f}x** |")
    w("")
    w(f"Projected against the ~1.8x that justified building this: "
      f"{'met' if speedup >= 1.7 else 'BELOW the projection'}. "
      f"At {bN.per_fold_seconds:.0f} s/fold the 239-design primary arm would take "
      f"{239*bN.per_fold_seconds/3600:.1f} h instead of {239*single_mean/3600:.1f} h.")
    w("")
    verdict = (det and same1 and ok2) if det else ok2
    w(f"## Verdict: {'ACCEPTED' if verdict else 'NOT ACCEPTED'}")
    w("")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0 if verdict else 1


if __name__ == "__main__":
    sys.exit(main())
