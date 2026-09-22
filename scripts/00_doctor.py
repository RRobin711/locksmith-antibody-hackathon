#!/usr/bin/env python3
"""Environment preflight for the Locksmith hackathon pipeline.

Checks every assumption the pipeline rests on, and fails loudly rather than
letting a broken environment produce plausible-looking numbers later.

Exit 0 = all REQUIRED checks pass.  Exit 1 = at least one required check failed.
Run:  uv run scripts/00_doctor.py
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

PASS, FAIL, WARN = "\033[32m  ok  \033[0m", "\033[31m FAIL \033[0m", "\033[33m warn \033[0m"
_failed: list[str] = []


def check(name: str, ok: bool, detail: str = "", required: bool = True) -> bool:
    mark = PASS if ok else (FAIL if required else WARN)
    print(f"[{mark}] {name:<42} {detail}")
    if not ok and required:
        _failed.append(name)
    return ok


def section(title: str) -> None:
    print(f"\n\033[1m{title}\033[0m")


def main() -> int:
    section("Python")
    v = sys.version_info
    check("python 3.12.x", (v.major, v.minor) == (3, 12), f"{v.major}.{v.minor}.{v.micro}")
    check("running inside project venv",
          "locksmith" in sys.prefix, sys.prefix)

    section("GPU / CUDA  (Blackwell sm_120 needs CUDA >= 12.8)")
    try:
        import torch
    except ImportError:
        check("torch importable", False, "not installed")
        return finish()

    check("torch >= 2.7", torch.__version__ >= "2.7", torch.__version__)
    check("built against cu128+",
          (torch.version.cuda or "0") >= "12.8", f"cuda {torch.version.cuda}")
    check("cuda.is_available()", torch.cuda.is_available())

    if torch.cuda.is_available():
        arches = torch.cuda.get_arch_list()
        check("sm_120 in arch list", "sm_120" in arches, " ".join(a for a in arches if "sm_1" in a))
        # PTX is the JIT fallback for architectures the build predates. An entry like
        # `sm_90` is SASS for that chip only; `compute_90` is PTX the driver can lower to
        # a newer arch at load. Measured 2026-09-20: torch cu118 and cu124 both ship
        # `PTX entries: NONE`, which is exactly why they die on sm_120 with
        # "no kernel image is available for execution on the device" -- there is nothing
        # to JIT. Not required here (we run a native sm_120 build) but reported, because
        # its absence is what makes an otherwise-plausible older stack unusable.
        ptx = [a for a in arches if a.startswith("compute")]
        check("PTX fallback present", bool(ptx), ", ".join(ptx) or "NONE (no JIT to newer archs)",
              required=False)
        props = torch.cuda.get_device_properties(0)
        check("device visible", True, f"{props.name}  {props.total_memory / 1024**3:.1f} GiB  "
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
            check("4096^2 fp32 matmul matches CPU", err < 1e-2, f"max abs err {err:.2e}")
        except Exception as exc:  # noqa: BLE001
            check("4096^2 fp32 matmul matches CPU", False, f"{type(exc).__name__}: {exc}")

        try:
            x = torch.randn(2048, 2048, device="cuda", dtype=torch.bfloat16)
            _ = (x @ x).float().sum().item()
            check("bf16 matmul runs", True, "available for tier-A screening", required=False)
        except Exception as exc:  # noqa: BLE001
            check("bf16 matmul runs", False, f"{type(exc).__name__}", required=False)

    section("Memory  (see PLAN.md 2.3)")
    mem = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k, _, rest = line.partition(":")
        mem[k] = int(rest.split()[0]) // 1024  # MiB
    total, avail = mem["MemTotal"], mem["MemAvailable"]
    swap = mem["SwapTotal"]
    check("RAM available >= 8 GiB", avail >= 8192,
          f"{avail} MiB free of {total} MiB  "
          f"{'(close Brave/Zoom/Slack/Discord before batch runs)' if avail < 8192 else ''}",
          required=False)
    check("swap >= 16 GiB (OOM insurance)", swap >= 16384,
          f"{swap} MiB — grow /swap.img before overnight batches" if swap < 16384 else f"{swap} MiB",
          required=False)
    free_gb = shutil.disk_usage(".").free / 1024**3
    check("disk free >= 50 GiB", free_gb >= 50, f"{free_gb:.0f} GiB")

    section("Scoring tools  (isolated envs — numpy pins conflict)")
    for tool, why in [("DockQ", "needs numpy<2"), ("prodigy", "needs numpy>=2")]:
        p = shutil.which(tool)
        check(f"{tool} on PATH", p is not None, p or f"uv tool install  ({why})", required=False)

    check("ipsae.py vendored", Path("vendor/ipsae/ipsae.py").exists(),
          "git clone DunbrackLab/IPSAE at pinned commit -> vendor/", required=False)

    for mod, note in [("anarcii", "IMGT numbering"), ("freesasa", "CDR SASA")]:
        try:
            __import__(mod)
            check(f"{mod} importable", True, note, required=False)
        except ImportError:
            check(f"{mod} importable", False, f"not installed ({note})", required=False)

    section("Reference structures")
    for pdb in ("5GGS", "5DK3", "5IUS", "5WT9"):
        f = Path("data/refs") / f"{pdb.lower()}.pdb"
        check(f"{pdb}", f.exists(),
              f"{f.stat().st_size // 1024} KiB" if f.exists() else "run 01_fetch_refs.py",
              required=False)

    return finish()


def finish() -> int:
    print()
    if _failed:
        print(f"\033[31m{len(_failed)} required check(s) failed:\033[0m " + ", ".join(_failed))
        return 1
    print("\033[32mAll required checks passed.\033[0m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
