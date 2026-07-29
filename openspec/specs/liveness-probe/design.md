# Liveness Probe — Design

## Architecture Overview

Two independent components cooperate to implement the liveness signal:

```text
┌──────────────────────────────────────────────┐
│ harvester process                            │
│                                              │
│  run_orchestrator()                          │
│    └─ asyncio.create_task(_heartbeat_loop()) │
│         touches  ──────────────────────────────────► /tmp/harvester-live
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ Kubernetes exec probe (separate process)     │
│                                              │
│  /middleware/harvester/healthcheck           │
│    --path=/tmp/harvester-live                │
│    reads mtime ◄───────────────────────────────────  /tmp/harvester-live
│    exits 0 / 1 ──────────────────────────────────► kubelet
└──────────────────────────────────────────────┘
```

The two components share only the file path. There is no IPC, no shared
memory, and no network connection between them.

## Key Decisions

1. **File mtime as the liveness signal**
   — Kubernetes `exec` probes run in a new process with no access to the
   harvester's memory or asyncio event loop. A file on a shared filesystem
   (tmpfs) is the simplest mechanism that crosses the process boundary.
   The mtime timestamp carries the "last alive at" information without any
   additional protocol.

2. **PyInstaller `--onefile` binary for the healthcheck**
   — The runtime container is minimal Alpine with no Python interpreter. A
   compiled single-file binary requires zero runtime dependencies and starts
   in milliseconds, making it suitable for frequent probe calls. The
   alternative of embedding a Python interpreter in the image was rejected
   because it would increase image size and attack surface significantly.

3. **`--path` is a required argument with no default**
   — Providing a default would create a silent coupling between the compiled
   binary constant and the operator's `config.yaml`. Making the argument
   required forces the caller (the probe definition in `values.yaml`) to be
   explicit, so any mismatch between probe and config is immediately visible.

4. **`_DEFAULT_MAX_AGE = 300` seconds**
   — 300 seconds covers 10× the default `heartbeat_interval` of 30 seconds,
   giving the probe enough tolerance for temporarily slow harvests without
   masking genuine hangs. Operators can override it via `--max-age` in
   `values.yaml`.

5. **`asyncio.create_task` + `cancel()` for the heartbeat loop**
   — The heartbeat loop must run concurrently with the harvest without
   blocking it. An `asyncio` background task achieves this within the
   existing event loop. `cancel()` (not `await`) is called after the
   orchestrator finishes: the loop contains no cleanup logic, so
   cancellation is safe and immediate. Awaiting the cancelled task would
   only slow down normal exit.

6. **No config parsing in the healthcheck binary**
   — Reading the harvester's YAML config would require Pydantic, a YAML
   parser, and the entire `middleware.shared` stack — contradicting the
   goal of a dependency-free binary. The `--path` argument in `values.yaml`
   carries a comment that names the corresponding `config.yaml` field,
   making the coupling explicit without coupling the code.

7. **`livenessProbe` is optional in the Helm template**
   — Wrapping the block in `{{- with .Values.livenessProbe }}` allows
   operators to omit the probe entirely (e.g. in local dev or short-lived
   test runs) without patching the template.
