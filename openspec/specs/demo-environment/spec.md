# Demo Environment

## Purpose

Provide a one-command, self-contained local environment that demonstrates
the full INSPIRE-to-ARC pipeline end-to-end without requiring production
credentials or mTLS certificates.

## Requirements

### Requirement: Start with a single command:
The system SHALL ensure that start with a single command:.

#### Scenario: Satisfies — Start with a single command:
- **WHEN** the conditions described by this requirement apply
- **THEN** Start with a single command:

### Requirement: Run a mock Middleware API (middleware-api) that accepts ARC RO-Crate
The system SHALL ensure that run a mock Middleware API (`middleware-api`) that accepts ARC RO-Crate.

#### Scenario: Satisfies — Run a mock Middleware API (middleware-api) that accepts ARC RO-Crate
- **WHEN** the conditions described by this requirement apply
- **THEN** Run a mock Middleware API (`middleware-api`) that accepts ARC RO-Crate

### Requirement: Run the harvester against the public GeoNode demo CSW endpoint
The system SHALL ensure that run the `harvester` against the public GeoNode demo CSW endpoint.

#### Scenario: Satisfies — Run the harvester against the public GeoNode demo CSW endpoint
- **WHEN** the conditions described by this requirement apply
- **THEN** Run the `harvester` against the public GeoNode demo CSW endpoint

### Requirement: Limit the harvest to 5 records via max_records so the…
The system SHALL ensure that limit the harvest to 5 records via `max_records` so the demo completes quickly.

#### Scenario: Satisfies — Limit the harvest to 5 records via max_records so the…
- **WHEN** the conditions described by this requirement apply
- **THEN** Limit the harvest to 5 records via `max_records` so the demo completes quickly

### Requirement: Harvester exits 0 when all records are processed; compose exits…
The system SHALL ensure that harvester exits 0 when all records are processed; compose exits with.

#### Scenario: Satisfies — Harvester exits 0 when all records are processed; compose exits…
- **WHEN** the conditions described by this requirement apply
- **THEN** Harvester exits 0 when all records are processed; compose exits with

### Requirement: Written ARC files are accessible on the host via a…
The system SHALL ensure that written ARC files are accessible on the host via a bind-mounted.

#### Scenario: Satisfies — Written ARC files are accessible on the host via a…
- **WHEN** the conditions described by this requirement apply
- **THEN** Written ARC files are accessible on the host via a bind-mounted

### Requirement: File ownership of output files matches the host user (via
The system SHALL ensure that file ownership of output files matches the host user (via.

#### Scenario: Satisfies — File ownership of output files matches the host user (via
- **WHEN** the conditions described by this requirement apply
- **THEN** File ownership of output files matches the host user (via

### Requirement: No credentials, encrypted files, or mTLS certificates required
The system SHALL ensure that no credentials, encrypted files, or mTLS certificates required.

#### Scenario: Satisfies — No credentials, encrypted files, or mTLS certificates required
- **WHEN** the conditions described by this requirement apply
- **THEN** No credentials, encrypted files, or mTLS certificates required

### Requirement: Edge case — ARC identifier in payload is unsafe (path traversal attempt)
The system SHALL handle this edge case: when ARC identifier in payload is unsafe (path traversal attempt), then mock API falls back to a random ID, logs to console, does not write outside `demo_output/`.

#### Scenario: Edge case — ARC identifier in payload is unsafe (path traversal attempt)
- **WHEN** ARC identifier in payload is unsafe (path traversal attempt)
- **THEN** mock API falls back to a random ID, logs to console, does not write outside `demo_output/`

### Requirement: Edge case — Demo_output/ doesn't exist
The system SHALL handle this edge case: when `demo_output/` doesn't exist, then mock API creates it on first request.

#### Scenario: Edge case — Demo_output/ doesn't exist
- **WHEN** `demo_output/` doesn't exist
- **THEN** mock API creates it on first request

### Requirement: Edge case — CSW endpoint is unavailable
The system SHALL handle this edge case: when CSW endpoint is unavailable, then harvester exits non-zero with a clear log message from the `ConnectionError` raised by `CSWClient.connect()`.

#### Scenario: Edge case — CSW endpoint is unavailable
- **WHEN** CSW endpoint is unavailable
- **THEN** harvester exits non-zero with a clear log message from the `ConnectionError` raised by `CSWClient.connect()`

## Out of Scope

Production credentials, sops-encrypted secrets, mTLS, and full-size CSW
harvesting are the responsibility of the dev environment (`compose.yaml`),
not this demo.

The demo requires outbound network access to the public GeoNode demo CSW
endpoint. No local CSW mock is provided.
