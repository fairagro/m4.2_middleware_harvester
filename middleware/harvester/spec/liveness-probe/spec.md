# Liveness Probe

The harvester runs as a Kubernetes CronJob. Because CronJob pods have no
readiness concept, a liveness probe is the only mechanism for Kubernetes to
detect and kill a hung or deadlocked pod. The probe must work inside a
minimal Alpine container with no Python interpreter.

## Requirements

### Heartbeat loop (harvester process)

- [ ] The orchestrator starts a background task that touches a configurable
      file path immediately on startup and then once every `heartbeat_interval`
      seconds for the duration of the harvest run.
- [ ] The background task is cancelled (not awaited) when the orchestrator
      finishes, so it cannot block process exit.
- [ ] `heartbeat_path` and `heartbeat_interval` are fields on `Config` with
      defaults of `/tmp/harvester-live` and `30` seconds respectively.
- [ ] `heartbeat_interval` must be ≥ 1 second.

### Healthcheck binary

- [ ] A standalone `healthcheck` binary is compiled via PyInstaller and
      installed at `/middleware/harvester/healthcheck` in the container image.
- [ ] The binary accepts `--path` (required) and `--max-age` (optional, default
      300 seconds) as command-line arguments.
- [ ] It exits `0` if the file at `--path` exists and its mtime is within
      `--max-age` seconds of the current time.
- [ ] It exits `1` if the file is absent or its mtime is older than `--max-age`
      seconds.
- [ ] The binary has no runtime dependency on Python, shell, or any middleware
      library.

### Kubernetes integration

- [ ] The Helm chart's `values.yaml` includes a `livenessProbe` block that
      invokes the binary via `exec` (no shell wrapper).
- [ ] `--path` in the probe command must match `heartbeat_path` in
      `config.yaml`; this coupling is documented in `values.yaml`.
- [ ] The `livenessProbe` block is optional in the Helm chart template
      (`{{- with .Values.livenessProbe }}`), so it can be omitted when not
      needed.

## Edge Cases

File does not exist at first probe → exit 1.

File exists from a previous run but has not been refreshed → exit 1 once age
exceeds `--max-age`.

Harvester completes normally before the first probe fires → heartbeat file
retains its mtime from the last touch; probe passes until `--max-age` expires,
by which point the pod has already exited.

Orchestrator raises an unhandled exception → heartbeat task is cancelled as
part of normal Python cleanup; file is not touched further; probe eventually
fails and Kubernetes kills the pod.
