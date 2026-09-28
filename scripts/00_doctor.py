#!/usr/bin/env python3
"""Environment preflight for the Locksmith hackathon pipeline.

Checks every assumption the pipeline rests on, and fails loudly rather than
letting a broken environment produce plausible-looking numbers later.

Exit 0 = all checks REQUIRED BY THE CHOSEN SCOPE pass.  Exit 1 = at least one failed.

    uv run python scripts/00_doctor.py --scope validate   # re-derive the package's scores
    uv run python scripts/00_doctor.py --scope fold       # run folds on the GPU
    uv run python scripts/00_doctor.py                    # both (default)

WHY THERE ARE SCOPES, AND WHY THIS FILE WAS WRONG UNTIL 2026-09-28
------------------------------------------------------------------
Until this rewrite every external tool -- `DockQ`, `prodigy`, `ipsae.py`, `anarcii`,
`freesasa` -- was `required=False`, so a machine with none of them installed printed
"All required checks passed."  Meanwhile "running inside project venv" WAS required,
and tested `"locksmith" in sys.prefix`, so renaming the clone directory failed the
preflight for the one reason that does not matter.

The required set was in fact BACKWARDS.  README ss"Reproducing it" points a grader at
this script from the *validator* section, promising it "checks all four before you
spend time".  But `scripts/58_validate_submission.py` imports
`dockq, ipsae, netsolp, novelty, plddt, prodigy, sasa` and -- verified by grep on
2026-09-28 -- touches CUDA nowhere.  So validation needs the four external tools and
no GPU, while this file required a GPU and none of the tools.  It could not fail for
a grader missing everything it actually needed, and did fail for a grader whose only
sin was a CPU.

A third gap, which STATE.md ss7 did not name: the README tells you to install ~4.7 GB
of NetSolP ONNX models, `scripts/58` imports `netsolp`, and this script checked it
**zero** times.

That is this project's own "a check that cannot fail is not evidence", applied to its
own preflight -- so the fix is a required set per scope, not a longer list.

NetSolP's location and model choice are IMPORTED from `locksmith.metrics.netsolp`
rather than repeated here.  A config value and a hardcoded constant encoding the same
convention will diverge; this file is not allowed to be the copy that rots.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

PASS, FAIL, WARN = "\033[32m  ok  \033[0m", "\033[31m FAIL \033[0m", "\033[33m warn \033[0m"
_failed: list[str] = []
_scope_ids: set[str] = set()

# Which check ids are REQUIRED in which scope.  A check whose id appears in no set is
# advisory everywhere and prints `warn` -- that is a deliberate statement that the
# pipeline runs without it, not an oversight.
#
#   fold      -- generating structures on the GPU.  Blackwell sm_120 needs CUDA >= 12.8.
#   validate  -- re-deriving the package's scores from the package's own files.  CPU only.
#
# `disk` sits in `fold` alone: a fold campaign writes tens of GB of npz/PDB, a
# validation run writes a temp directory and deletes it.
REQUIRED: dict[str, set[str]] = {
    "fold": {
        "python312", "locksmith_import",
        "torch_import", "torch_version", "torch_cu128",
        "cuda_available", "sm120", "matmul",
        "disk",
    },
    "validate": {
        "python312", "locksmith_import",
        "dockq", "prodigy", "ipsae", "anarcii", "freesasa",
        "netsolp_models", "netsolp_python",
        "dockq_reference",
    },
}
REQUIRED["all"] = REQUIRED["fold"] | REQUIRED["validate"]


def check(cid: str, name: str, ok: bool, detail: str = "") -> bool:
    required = cid in _scope_ids
    mark = PASS if ok else (FAIL if required else WARN)
    print(f"[{mark}] {name:<42} {detail}")
    if not ok and required:
        _failed.append(name)
    return ok


def section(title: str) -> None:
    print(f"\n\033[1m{title}\033[0m")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scope", choices=("fold", "validate", "all"), default="all",
                    help="which job you are about to run; decides what is REQUIRED "
                         "(default: all)")
    args = ap.parse_args()
    global _scope_ids
    _scope_ids = REQUIRED[args.scope]
    print(f"\033[1mscope: {args.scope}\033[0m  "
          f"({len(_scope_ids)} required checks; everything else is advisory)")

    section("Python")
    v = sys.version_info
    check("python312", "python 3.12.x", (v.major, v.minor) == (3, 12),
          f"{v.major}.{v.minor}.{v.micro}")

    # The functional invariant, not a substring of a path.  The question is never
    # "is this venv called locksmith" -- it is "if I `import locksmith`, do I get THIS
    # checkout".  The old test (`"locksmith" in sys.prefix`) answered neither: it
    # passed for any venv with a matching name and failed for a correct checkout in a
    # renamed directory.
    try:
        import locksmith
        mod = Path(locksmith.__file__).resolve()
        check("locksmith_import", "`import locksmith` resolves to this checkout",
              REPO in mod.parents, str(mod))
    except ImportError as exc:
        check("locksmith_import", "`import locksmith` resolves to this checkout",
              False, f"not importable: {exc}  (run `uv sync`)")

    section("GPU / CUDA  (Blackwell sm_120 needs CUDA >= 12.8)")
    try:
        import torch
    except ImportError:
        check("torch_import", "torch importable", False, "not installed")
        return finish(args.scope)

    check("torch_import", "torch importable", True, torch.__version__)
    check("torch_version", "torch >= 2.7", torch.__version__ >= "2.7", torch.__version__)
    check("torch_cu128", "built against cu128+",
          (torch.version.cuda or "0") >= "12.8", f"cuda {torch.version.cuda}")
    check("cuda_available", "cuda.is_available()", torch.cuda.is_available())

    if torch.cuda.is_available():
        arches = torch.cuda.get_arch_list()
        check("sm120", "sm_120 in arch list", "sm_120" in arches,
              " ".join(a for a in arches if "sm_1" in a))
        # PTX is the JIT fallback for architectures the build predates. An entry like
        # `sm_90` is SASS for that chip only; `compute_90` is PTX the driver can lower to
        # a newer arch at load. Measured 2026-09-20: torch cu118 and cu124 both ship
        # `PTX entries: NONE`, which is exactly why they die on sm_120 with
        # "no kernel image is available for execution on the device" -- there is nothing
        # to JIT. Not required here (we run a native sm_120 build) but reported, because
        # its absence is what makes an otherwise-plausible older stack unusable.
        ptx = [a for a in arches if a.startswith("compute")]
        check("ptx", "PTX fallback present", bool(ptx),
              ", ".join(ptx) or "NONE (no JIT to newer archs)")
        props = torch.cuda.get_device_properties(0)
        check("device", "device visible", True,
              f"{props.name}  {props.total_memory / 1024**3:.1f} GiB  "
              f"sm_{props.major}{props.minor}")

        # A real matmul. is_available() and arch_list can both be true on a build
        # that then produces garbage or throws at kernel launch time.
        try:
            g = torch.Generator(device="cuda").manual_seed(0)
            a = torch.randn(4096, 4096, device="cuda", dtype=torch.float32, generator=g)
            b = torch.randn(4096, 4096, device="cuda", dtype=torch.float32, generator=g)
            gpu = (a @ b).cpu()
            cpu = a.cpu() @ b.cpu()
            err = (gpu - cpu).abs().max().item()
            check("matmul", "4096^2 fp32 matmul matches CPU", err < 1e-2,
                  f"max abs err {err:.2e}")
        except Exception as exc:  # noqa: BLE001
            check("matmul", "4096^2 fp32 matmul matches CPU", False,
                  f"{type(exc).__name__}: {exc}")

        try:
            x = torch.randn(2048, 2048, device="cuda", dtype=torch.bfloat16)
            _ = (x @ x).float().sum().item()
            check("bf16", "bf16 matmul runs", True, "available for tier-A screening")
        except Exception as exc:  # noqa: BLE001
            check("bf16", "bf16 matmul runs", False, f"{type(exc).__name__}")
    else:
        # Say so explicitly. Without this line a CPU box prints nothing between
        # `cuda.is_available()` and the memory section, which reads as "checks passed".
        check("sm120", "sm_120 in arch list", False, "skipped: no CUDA device")
        check("matmul", "4096^2 fp32 matmul matches CPU", False, "skipped: no CUDA device")

    section("Memory  (see PLAN.md 2.3)")
    mem = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k, _, rest = line.partition(":")
        mem[k] = int(rest.split()[0]) // 1024  # MiB
    total, avail = mem["MemTotal"], mem["MemAvailable"]
    swap = mem["SwapTotal"]
    check("ram", "RAM available >= 8 GiB", avail >= 8192,
          f"{avail} MiB free of {total} MiB  "
          f"{'(close Brave/Zoom/Slack/Discord before batch runs)' if avail < 8192 else ''}")
    check("swap", "swap >= 16 GiB (OOM insurance)", swap >= 16384,
          f"{swap} MiB — grow /swap.img before overnight batches" if swap < 16384 else f"{swap} MiB")
    free_gb = shutil.disk_usage(".").free / 1024**3
    check("disk", "disk free >= 50 GiB", free_gb >= 50, f"{free_gb:.0f} GiB")

    section("Scoring tools  (isolated envs — numpy pins conflict)")
    for cid, tool, why in [("dockq", "DockQ", "needs numpy<2"),
                           ("prodigy", "prodigy", "needs numpy>=2")]:
        p = shutil.which(tool)
        check(cid, f"{tool} on PATH", p is not None, p or f"uv tool install  ({why})")

    ipsae_py = REPO / "vendor/ipsae/ipsae.py"
    check("ipsae", "ipsae.py vendored", ipsae_py.exists(),
          str(ipsae_py) if ipsae_py.exists()
          else "git clone DunbrackLab/IPSAE at pinned commit -> vendor/")

    for cid, note in [("anarcii", "IMGT numbering"), ("freesasa", "CDR SASA")]:
        try:
            __import__(cid)
            check(cid, f"{cid} importable", True, note)
        except ImportError:
            check(cid, f"{cid} importable", False, f"not installed ({note})")

    # Imported, never re-declared: `MODEL_TYPE` is a recorded convention (ESM1b is the
    # only variant that passes pembrolizumab, our positive control) and the two paths
    # are overridable by env var. Reading them from the module means this check follows
    # NETSOLP_DIR / NETSOLP_PYTHON wherever the operator points them.
    section("NetSolP  (solubility; CPU-only ONNX, ~4.7 GB)")
    try:
        from locksmith.metrics.netsolp import MODEL_TYPE, NETSOLP_DIR, NETSOLP_PYTHON
        models = sorted(Path(NETSOLP_DIR).glob("models/*.onnx"))
        check("netsolp_models", f"NetSolP models ({MODEL_TYPE})", bool(models),
              f"{len(models)} .onnx in {NETSOLP_DIR}" if models
              else f"none under {NETSOLP_DIR}/models — see BUILD.md §6b")
        check("netsolp_python", "NetSolP interpreter", Path(NETSOLP_PYTHON).exists(),
              str(NETSOLP_PYTHON))
    except ImportError as exc:
        check("netsolp_models", "NetSolP models", False, f"cannot import metric: {exc}")
        check("netsolp_python", "NetSolP interpreter", False, "unknown")

    section("Reference structures")
    # The DockQ reference is the validator's one unavoidable external input and is the
    # default of `scripts/58_validate_submission.py --reference`. It is TRACKED, so its
    # absence means a broken checkout rather than a skipped fetch -- hence required in
    # `validate` where the four raw PDBs below are not.
    ref = REPO / "data/refs/prepared/5ggs_ABZ.pdb"
    check("dockq_reference", "DockQ reference 5ggs_ABZ.pdb", ref.exists(),
          f"{ref.stat().st_size // 1024} KiB" if ref.exists() else f"missing: {ref}")

    # Fetched by 01_fetch_refs.py and .gitignored, so a fresh clone legitimately lacks
    # them and the validator never reads them. Advisory in every scope.
    for pdb in ("5GGS", "5DK3", "5IUS", "5WT9"):
        f = REPO / "data/refs" / f"{pdb.lower()}.pdb"
        check(f"ref_{pdb.lower()}", f"{pdb}", f.exists(),
              f"{f.stat().st_size // 1024} KiB" if f.exists() else "run 01_fetch_refs.py")

    return finish(args.scope)


def finish(scope: str) -> int:
    print()
    if _failed:
        print(f"\033[31m{len(_failed)} required check(s) failed for scope "
              f"'{scope}':\033[0m " + ", ".join(_failed))
        return 1
    print(f"\033[32mAll checks required for scope '{scope}' passed.\033[0m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
