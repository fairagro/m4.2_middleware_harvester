# Demo Environment

## Purpose

Provide a one-command, self-contained local environment that demonstrates the
full INSPIRE-to-ARC pipeline end-to-end without requiring production
credentials or mTLS certificates.

## Requirements

### Requirement: Start with a single compose command

The system SHALL start the demo with:

`docker compose -f dev_environment/compose.demo.yaml up --build`

#### Scenario: Operator starts the demo

- **WHEN** an operator runs the compose command above from the repository root
- **THEN** the mock API and harvester services start without additional setup
  steps

### Requirement: Mock Middleware API

The system SHALL run a mock Middleware API (`middleware-api`) that accepts ARC
RO-Crate uploads and writes them under the host-visible
`dev_environment/demo_output/` directory (bind-mounted to `/data/arcs` in the
container).

#### Scenario: Successful upload is written locally

- **WHEN** the harvester uploads an ARC to the mock API
- **THEN** the ARC files appear under `dev_environment/demo_output/`

### Requirement: Public GeoNode demo CSW

The system SHALL run the harvester against the public GeoNode demo CSW endpoint
`https://stable.demo.geonode.org/catalogue/csw`.

#### Scenario: Configured CSW URL

- **WHEN** `dev_environment/config.demo.yaml` is used
- **THEN** `inspire.csw_url` points at the public GeoNode demo catalogue

### Requirement: Limit harvest size

The system SHALL limit the harvest to 5 records via `max_records` so the demo
completes quickly.

#### Scenario: Five-record cap

- **WHEN** the demo config is loaded
- **THEN** `max_records` is `5`

### Requirement: Exit codes

The harvester SHALL exit `0` when all configured records are processed
successfully. Compose SHALL propagate the harvester exit code when run with
`--exit-code-from harvester`.

#### Scenario: Successful demo run

- **WHEN** the harvester finishes without repository-level failure
- **THEN** the harvester process exit code is `0`

### Requirement: Host-visible output ownership

Written ARC files MUST be accessible on the host via the bind-mounted
`dev_environment/demo_output/` volume. File ownership SHOULD match the host
user via `LOCAL_UID` / `LOCAL_GID` environment variables.

#### Scenario: LOCAL_UID/LOCAL_GID applied

- **WHEN** `LOCAL_UID` and `LOCAL_GID` are set for the mock API container
- **THEN** written output under `demo_output/` is chowned to that uid/gid

### Requirement: No production secrets

The demo MUST NOT require credentials, sops-encrypted files, or mTLS client
certificates.

#### Scenario: Plain compose demo

- **WHEN** an operator starts `compose.demo.yaml`
- **THEN** no `client.key` / sops / mTLS material is required

### Requirement: Edge case — unsafe ARC identifier

When an ARC identifier in the upload payload is unsafe (path traversal or
disallowed characters), the mock API MUST fall back to a random ID, log to the
console, and MUST NOT write outside `demo_output/`.

#### Scenario: Path traversal attempt

- **WHEN** the payload identifier contains `../` or other unsafe path content
- **THEN** the mock API stores under a safe random id inside `demo_output/`

### Requirement: Edge case — missing demo_output directory

When `demo_output/` does not exist, the mock API MUST create it on first
request.

#### Scenario: First write creates directory

- **WHEN** the output directory is absent at startup
- **THEN** the first successful upload creates it

### Requirement: Edge case — CSW unavailable

When the CSW endpoint is unavailable, the harvester MUST exit non-zero with a
clear log message stemming from the connection failure raised by
`CSWClient.connect()`.

#### Scenario: Unreachable CSW

- **WHEN** the configured CSW host cannot be reached
- **THEN** the harvester exits non-zero and logs the connection failure

## Out of Scope

Production credentials, sops-encrypted secrets, mTLS, and full-size CSW
harvesting belong to the broader `dev_environment/compose.yaml` setup, not this
demo.

The demo requires outbound network access to the public GeoNode demo CSW
endpoint. No local CSW mock is provided.
