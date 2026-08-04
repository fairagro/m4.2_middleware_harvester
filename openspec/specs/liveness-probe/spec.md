# Liveness Probe

## Purpose

The harvester runs as a Kubernetes CronJob. Because CronJob pods have no
readiness concept, a liveness probe is the only mechanism for Kubernetes to
detect and kill a hung or deadlocked pod. The probe must work inside a
minimal Alpine container with no Python interpreter.

## Requirements

### Requirement: The orchestrator starts a background task that touches a configurable
The system SHALL ensure that the orchestrator starts a background task that touches a configurable.

#### Scenario: Satisfies — The orchestrator starts a background task that touches a configurable
- **WHEN** the conditions described by this requirement apply
- **THEN** The orchestrator starts a background task that touches a configurable

### Requirement: The background task is cancelled (not awaited) when the orchestrator
The background task SHALL be cancelled (not awaited) when the orchestrator.

#### Scenario: Satisfies — The background task is cancelled (not awaited) when the orchestrator
- **WHEN** the conditions described by this requirement apply
- **THEN** The background task is cancelled (not awaited) when the orchestrator

### Requirement: Heartbeat_path and heartbeat_interval are fields on Config with
The system SHALL ensure that `heartbeat_path` and `heartbeat_interval` are fields on `Config` with.

#### Scenario: Satisfies — Heartbeat_path and heartbeat_interval are fields on Config with
- **WHEN** the conditions described by this requirement apply
- **THEN** `heartbeat_path` and `heartbeat_interval` are fields on `Config` with

### Requirement: Heartbeat_interval must be ≥ 1 second
The system SHALL ensure that `heartbeat_interval` must be ≥ 1 second.

#### Scenario: Satisfies — Heartbeat_interval must be ≥ 1 second
- **WHEN** the conditions described by this requirement apply
- **THEN** `heartbeat_interval` must be ≥ 1 second

### Requirement: A standalone healthcheck binary is compiled via PyInstaller and
The system SHALL ensure that a standalone `healthcheck` binary is compiled via PyInstaller and.

#### Scenario: Satisfies — A standalone healthcheck binary is compiled via PyInstaller and
- **WHEN** the conditions described by this requirement apply
- **THEN** A standalone `healthcheck` binary is compiled via PyInstaller and

### Requirement: The binary accepts --path (required) and --max-age (optional, default
The system SHALL ensure that the binary accepts `--path` (required) and `--max-age` (optional, default.

#### Scenario: Satisfies — The binary accepts --path (required) and --max-age (optional, default
- **WHEN** the conditions described by this requirement apply
- **THEN** The binary accepts `--path` (required) and `--max-age` (optional, default

### Requirement: It exits 0 if the file at --path exists and…
The system SHALL ensure that it exits `0` if the file at `--path` exists and its mtime is within.

#### Scenario: Satisfies — It exits 0 if the file at --path exists and…
- **WHEN** the conditions described by this requirement apply
- **THEN** It exits `0` if the file at `--path` exists and its mtime is within

### Requirement: It exits 1 if the file is absent or its…
The system SHALL ensure that it exits `1` if the file is absent or its mtime is older than `--max-age`.

#### Scenario: Satisfies — It exits 1 if the file is absent or its…
- **WHEN** the conditions described by this requirement apply
- **THEN** It exits `1` if the file is absent or its mtime is older than `--max-age`

### Requirement: The binary has no runtime dependency on Python, shell, or…
The system SHALL ensure that the binary has no runtime dependency on Python, shell, or any middleware.

#### Scenario: Satisfies — The binary has no runtime dependency on Python, shell, or…
- **WHEN** the conditions described by this requirement apply
- **THEN** The binary has no runtime dependency on Python, shell, or any middleware

### Requirement: The Helm chart's values.yaml includes a livenessProbe block that
The system SHALL ensure that the Helm chart's `values.yaml` includes a `livenessProbe` block that.

#### Scenario: Satisfies — The Helm chart's values.yaml includes a livenessProbe block that
- **WHEN** the conditions described by this requirement apply
- **THEN** The Helm chart's `values.yaml` includes a `livenessProbe` block that

### Requirement: --path in the probe command must match heartbeat_path in
The system SHALL ensure that `--path` in the probe command must match `heartbeat_path` in.

#### Scenario: Satisfies — --path in the probe command must match heartbeat_path in
- **WHEN** the conditions described by this requirement apply
- **THEN** `--path` in the probe command must match `heartbeat_path` in

### Requirement: The livenessProbe block is optional in the Helm chart template
The `livenessProbe` block SHALL be optional in the Helm chart template.

#### Scenario: Satisfies — The livenessProbe block is optional in the Helm chart template
- **WHEN** the conditions described by this requirement apply
- **THEN** The `livenessProbe` block is optional in the Helm chart template

### Requirement: Edge case — File does not exist at first probe
The system SHALL handle this edge case: when File does not exist at first probe, then exit 1.

#### Scenario: Edge case — File does not exist at first probe
- **WHEN** File does not exist at first probe
- **THEN** exit 1

### Requirement: Edge case — File exists from a previous run but has not been…
The system SHALL handle this edge case: when File exists from a previous run but has not been refreshed, then exit 1 once age exceeds `--max-age`.

#### Scenario: Edge case — File exists from a previous run but has not been…
- **WHEN** File exists from a previous run but has not been refreshed
- **THEN** exit 1 once age exceeds `--max-age`

### Requirement: Edge case — Harvester completes normally before the first probe fires
The system SHALL handle this edge case: when Harvester completes normally before the first probe fires, then heartbeat file retains its mtime from the last touch; probe passes until `--max-age` expires, by which point the pod has already exited.

#### Scenario: Edge case — Harvester completes normally before the first probe fires
- **WHEN** Harvester completes normally before the first probe fires
- **THEN** heartbeat file retains its mtime from the last touch; probe passes until `--max-age` expires, by which point the pod has already exited

### Requirement: Edge case — Orchestrator raises an unhandled exception
The system SHALL handle this edge case: when Orchestrator raises an unhandled exception, then heartbeat task is cancelled as part of normal Python cleanup; file is not touched further; probe eventually fails and Kubernetes kills the pod.

#### Scenario: Edge case — Orchestrator raises an unhandled exception
- **WHEN** Orchestrator raises an unhandled exception
- **THEN** heartbeat task is cancelled as part of normal Python cleanup; file is not touched further; probe eventually fails and Kubernetes kills the pod
