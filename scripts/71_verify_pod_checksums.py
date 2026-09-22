#!/usr/bin/env python3
"""Complete the server-side sha256 pass over the retrieved Challenge 2 artefacts.

WHY THIS EXISTS SEPARATELY FROM THE DOWNLOAD. The 2026-09-22 transfer succeeded and the
VERIFICATION did not: Jupyter 502'd part way through, and RunPod later reported the cause
as an OOM kill on a pod that had been started via the "use CPUs" fallback with **0 vCPU
and 0 GB RAM**. The bytes are already on disk. What is missing is the independent
evidence that they are the right bytes, and byte-size plus parse checks are a DIFFERENT
kind of evidence, not a substitute.

DESIGN, driven by exactly how the last attempt failed:

  * **Checkpoint every hash the moment it lands.** v1 wrote its manifest only at the end,
    so one transient failure at file ~130 destroyed every checksum it had computed. Here
    each result is appended to a JSONL immediately and `fsync`ed. A later run resumes.
  * **Resume, never restart.** A partial pass with 200/256 verified beats three clean
    starts that each die at 130.
  * **Cache the directory walk.** The walk itself costs API calls; once we know the file
    list we persist it and do not re-walk on resume.
  * **Bounded.** Honours a wall-clock deadline passed in by the caller and exits cleanly
    when it is hit, leaving the checkpoint intact.
  * **Announce liveness.** Writes progress to stdout AND touches the checkpoint, so an
    external watcher can ask "is the output file still growing" rather than inspecting
    process tables (`pgrep` has self-matched on this project five times, and `setsid`
    makes `$!` meaningless).

Usage:
    python scripts/71_verify_pod_checksums.py --deadline-epoch <unix-ts> [--token TOK]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = "https://nbjjg5n8ias0tt-8888.proxy.runpod.net"
DST = Path("runs/challenge2_pod")
CKPT = DST / "CHECKSUMS.jsonl"          # append-only, one verified file per line
FILELIST = DST / "FILELIST.json"        # cached walk, so resume costs no API calls
DONE = DST / "CHECKSUMS.DONE"           # sentinel an external watcher can poll
SKIP_PREFIX = ("workspace/lock/RFantibody",)


def _auth(url: str, token: str) -> str:
    """Token goes in the QUERY STRING, not an Authorization header.

    The header form worked on 2026-09-22 and returns 403 after the pod restart --
    same token, same pod, different Jupyter auth handling. Verified by probe:
    `/api/status` -> 403 with the header, 200 with `?token=`. Worth recording because
    a 403 reads as "credential expired" and would have sent us hunting for a new token
    that does not exist.
    """
    return f"{url}{'&' if '?' in url else '?'}token={token}"


def curl_json(url: str, token: str, timeout: int = 90) -> dict | None:
    r = subprocess.run(["curl", "-sS", "-m", str(timeout), _auth(url, token)],
                       capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return None


def service_up(token: str) -> bool:
    return curl_json(f"{BASE}/api/status", token, timeout=25) is not None


def wait_for_service(token: str, deadline: float, gap: int = 20) -> bool:
    while time.time() < deadline:
        if service_up(token):
            return True
        time.sleep(gap)
    return False


def walk(path: str, token: str, out: list, deadline: float) -> None:
    """Depth-first listing. Retries a failed directory a few times before giving up."""
    node = None
    for i in range(5):
        if time.time() > deadline:
            return
        node = curl_json(f"{BASE}/api/contents/{path}?content=1", token)
        if node is not None:
            break
        time.sleep(3 * (i + 1))
    if node is None:
        raise RuntimeError(f"could not list {path}")
    for c in node.get("content", []):
        if any(c["path"].startswith(s) for s in SKIP_PREFIX):
            continue
        if c["type"] == "directory":
            walk(c["path"], token, out, deadline)
        else:
            out.append({"path": c["path"], "size": c.get("size")})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deadline-epoch", type=float, required=True,
                    help="hard stop; the pod-uptime budget is owned by the caller")
    ap.add_argument("--token", default=os.environ.get("JUP_TOKEN", ""))
    a = ap.parse_args()
    token, deadline = a.token, a.deadline_epoch
    if not token:
        print("no jupyter token", file=sys.stderr)
        return 2

    DST.mkdir(parents=True, exist_ok=True)
    DONE.unlink(missing_ok=True)

    print(f"[{time.strftime('%H:%M:%S')}] waiting for jupyter "
          f"(budget ends {time.strftime('%H:%M:%S', time.localtime(deadline))})",
          flush=True)
    if not wait_for_service(token, deadline):
        print("jupyter never answered inside the budget", flush=True)
        return 3
    print(f"[{time.strftime('%H:%M:%S')}] service up", flush=True)

    # ---- file list (cached) ----
    if FILELIST.exists():
        files = json.loads(FILELIST.read_text())
        print(f"resuming with cached list of {len(files)} files", flush=True)
    else:
        files = []
        for root in ("workspace/c2", "workspace/lock"):
            walk(root, token, files, deadline)
        files.sort(key=lambda f: f["path"])
        FILELIST.write_text(json.dumps(files, indent=1))
        print(f"walked {len(files)} files", flush=True)

    # ---- resume set ----
    done: dict[str, dict] = {}
    if CKPT.exists():
        for line in CKPT.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r.get("match"):
                    done[r["path"]] = r
    print(f"already verified: {len(done)}/{len(files)}", flush=True)

    todo = [f for f in files if f["path"] not in done]
    verified, mismatched, unreachable = len(done), [], []

    with CKPT.open("a") as ck:
        for i, f in enumerate(todo, 1):
            if time.time() > deadline:
                print(f"[{time.strftime('%H:%M:%S')}] DEADLINE reached; stopping with "
                      f"{verified}/{len(files)} verified", flush=True)
                break
            rel = f["path"]
            local = DST / rel[len("workspace/"):]

            meta = None
            for attempt in range(4):
                meta = curl_json(f"{BASE}/api/contents/{rel}?content=0&hash=1", token)
                if meta is not None and meta.get("hash"):
                    break
                time.sleep(2 * (attempt + 1))
            if meta is None or not meta.get("hash"):
                unreachable.append(rel)
                print(f"  [{i}/{len(todo)}] UNREACHABLE {rel}", flush=True)
                continue

            if not local.exists():
                subprocess.run(["curl", "-sS", "-m", "600", "--fail",
                                _auth(f"{BASE}/files/{rel}", token), "-o", str(local)])
            got = (hashlib.sha256(local.read_bytes()).hexdigest()
                   if local.exists() else None)
            match = got == meta["hash"]
            if not match:
                mismatched.append(rel)

            rec = {"path": rel, "size": meta.get("size"),
                   "sha256_pod": meta["hash"], "sha256_local": got, "match": match}
            ck.write(json.dumps(rec) + "\n")
            ck.flush()
            os.fsync(ck.fileno())          # so an external watcher sees it grow
            verified += match
            if i % 10 == 0 or i == len(todo):
                print(f"  [{i}/{len(todo)}] verified={verified}/{len(files)} "
                      f"mismatch={len(mismatched)} unreachable={len(unreachable)}",
                      flush=True)

    complete = verified == len(files)
    summary = {"total": len(files), "verified": verified,
               "mismatched": mismatched, "unreachable": unreachable,
               "complete": complete,
               "finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    (DST / "CHECKSUM_SUMMARY.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary, indent=1), flush=True)

    if complete:
        DONE.write_text(json.dumps(summary, indent=1))
        print("PASS COMPLETE -- pod may be stopped", flush=True)
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
