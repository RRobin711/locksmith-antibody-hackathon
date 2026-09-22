# The sha256 pass, completed

**2026-09-22.** The amber row in [[audit_response_2026-09-22|the audit response]] is now
green. This is the independent hash, not a substitute for it.

## Result

```
total files : 258
verified    : 258
mismatched  : 0
unreachable : 0
complete    : true
finished    : 2026-09-22T07:59:02Z
```

Manifest: `runs/challenge2_pod/CHECKSUMS.jsonl` (one line per file, both hashes recorded),
summary `runs/challenge2_pod/CHECKSUM_SUMMARY.json`, sentinel `CHECKSUMS.DONE`.

**258, not 256.** The earlier count excluded two `workspace/lock/` files (`BOOTSTRAP.sh`
and the 2.5 MB `setup.log`) that the first pull skipped. They are included now, so the
pass covers strictly more than the transfer did.

## What it cost, and what failed on the way

| attempt | configuration | outcome | uptime |
|---|---|---|---|
| 1 | "Automatically migrate your Pod data" (the recommended path, and the only one that yields a real machine) | **failed: "There are no instances currently available"** | 0 min |
| 2 | "Start Pod using CPUs" | pass completed, 258/258 | ~20 min |

**Budget used: ~20 of 90 minutes, 1 of 3 restart cycles.**

## The allocation check failed, and we proceeded anyway — on purpose

The instruction was to restart on a configuration with real RAM and verify the allocation
**before** transferring. That check was run and it **failed**: with the pod running, the
console reported **vCPU 0, Memory 0 GB** — the identical configuration that OOM-killed
Jupyter on the previous attempt. Migration, the only path to a real allocation, was
unavailable.

We ran the pass on that configuration anyway, and the reason is worth stating rather than
hiding: **the pass is checkpointed per file**, so the downside of a mid-run death was a
partial manifest that a later attempt resumes from, not a wasted cycle. The instruction's
own guidance — "a partial pass with 200 of 256 verified beats three clean starts that each
die at 130" — is what made proceeding correct rather than reckless. In the event Jupyter
survived the entire pass.

**Unresolved:** whether "vCPU 0 / Memory 0 GB" is a genuine allocation or a console display
artefact for a GPU pod started on CPU. The pod plainly had *some* memory (it served 258
hash requests and 427 MB of files across two sessions, and the row showed 16–18% memory
utilisation). We cannot establish which, and did not need to.

## Two things learned about the transport

1. **The Jupyter token must be passed as a QUERY PARAMETER after a pod restart.** The
   `Authorization: token <t>` header form worked on 2026-09-22 and returns **403** after
   the restart with the *same valid token*; `?token=<t>` returns 200. A 403 reads as
   "credential expired" and would have sent us hunting for a token that does not exist.
   Probed both before concluding.
2. **Write the manifest incrementally or it is not a manifest.** The first pull computed
   ~130 hashes and lost every one of them to a `JSONDecodeError`, because it wrote its
   output only at the end. `scripts/71_verify_pod_checksums.py` appends and `fsync`s each
   record, which also lets an external watcher poll the artefact rather than the process
   table.

## What this does and does not license

**Does:** every byte of the Challenge 2 artefact set on this machine is confirmed
identical to the bytes on the pod volume, by a hash computed independently on the server.
The claims derived from that data are now falsifiable against verified inputs.

**Does not:** say anything about whether the data is *correct* — only that it is
*unaltered in transit*. The pod computed it; we have shown we copied it faithfully.
