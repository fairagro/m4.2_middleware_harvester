# Proposal

## Why

#546: when a plugin yields a repository-level `HarvesterError` (e.g. _Protocol discovery failed_) and its stream then
ends, the harvester still completes the API harvest. The harvest report records the repository failure, but the API
shows the harvest as COMPLETED, so the two disagree and a broken run looks like a good one. The spike on #546 (API
14.0.0) showed the RDI dump itself is safe either way: finalize rebuilds it from all stored ARCs, and a failed harvest
neither finalizes nor removes the ARCs it already stored.

## What Changes

- When a repository-level error was recorded for a repository, its API harvest ends as FAILED instead of COMPLETED, also
  when ARCs were submitted before the error.
- ARCs the API accepted before the error still count as harvested; the report keeps exactly one repository failure (the
  plugin's error), with no extra upload-aborted issue.
- Record-level errors (`RecordProcessingError`) keep the current behaviour: the harvest completes.
- **Non-goals:** removing ARCs that disappeared upstream from the dump; detecting a stream that ends early without an
  error; `arcs_missing` semantics; an API-side guard against empty catalogs (decided on #546).

## Capabilities

### New Capabilities

- (none)

### Modified Capabilities

- `harvest-report`: a recorded repository-level issue fails the API harvest; reporting of already accepted ARCs is
  unchanged.

## Impact

- `middleware/harvester` upload / reporting path and its tests. No config, API or plugin contract changes.
