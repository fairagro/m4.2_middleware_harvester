# Proposal

## Why

Operators need the same PEP 440 harvester version in the end-of-run harvest report that is already logged at job start
(#508). Shared `HarvestReport.software_version` / JSON-LD `schema:instrument` shipped in API #598 / #645 and is on PyPI
as `fairagro-middleware-shared` **14.2.0**. Start log and CLI `--version` are already in-tree; only report wiring and
the dependency bump remain.

## What Changes

- Bump `fairagro-middleware-shared` (and lockfile) to **≥14.2.0** so `HarvestReport.software_version` is available.
- When creating the run `HarvestReport`, set `software_version` to `importlib.metadata.version("harvester")` (same
  string as the start log / `--version`).
- Unit coverage that the orchestrator/report path stamps the version onto the report (and that emitted JSON-LD includes
  it when using the shared serializer).
- OpenSpec delta under `harvest-report` for the harvester drive obligation.

**Non-goals:** Changing shared report schema (owned by the API). Replacing the existing start log or `--version` CLI.
Local serializer wrappers (spike on #598; not needed now that shared ships the field).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `harvest-report`: Require the harvester to set shared `HarvestReport.software_version` to the installed `harvester`
  distribution version for every run that creates a report.

## Impact

- `middleware/harvester` orchestrator (+ tests); possibly `main` only if wiring is clearer there
- `uv.lock` / package deps for `fairagro-middleware-shared`
- OpenSpec `harvest-report` delta
- Follow-up: close #508 on merge; sibling sql-to-arc #287 remains separate
