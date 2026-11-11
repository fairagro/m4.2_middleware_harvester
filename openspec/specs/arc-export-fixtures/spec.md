# ARC Export Fixtures

## Purpose

Gates representative per-RDI RO-Crate fixtures with the same DataHUB `arc-export` check (via shared arc-validation)
under `system_local` tests and a Docker-capable CI job, so client CI catches export failures before upload.

## Requirements

### Requirement: Per-RDI RO-Crate fixtures exist for active mapper families

The repository SHALL commit at least one representative RO-Crate fixture per active mapper family covered by this
capability (INSPIRE, Schema.org/generic, Regal). Each fixture SHALL be stored under a stable per-RDI path suitable for
tests (for example `tests/fixtures/arc_export/<rdi>/…`). Fixtures MAY use Git LFS when size warrants it.

#### Scenario: Three family fixtures present

- **WHEN** a developer inspects the fixture tree for this capability
- **THEN** there is at least one RO-Crate artifact for an INSPIRE-shaped RDI, one for a Schema.org/generic-shaped RDI,
  and one for a Regal-shaped RDI

### Requirement: system_local tests validate fixtures with shared arc-export check

Pytest tests marked `system_local` SHALL run the shared RO-Crate arc-export validation against each committed fixture. A
passing fixture MUST report success; a failing fixture MUST fail the test with a readable cause excerpt from the
validator (not a bare Docker exit code alone).

#### Scenario: Valid fixture passes

- **WHEN** `system_local` tests run with Docker available and a known-good fixture
- **THEN** validation succeeds for that fixture

#### Scenario: Invalid fixture fails with excerpt

- **WHEN** validation fails for a fixture
- **THEN** the test failure includes a readable cause excerpt from the validator result

### Requirement: Default local gates do not require Docker for these tests

Commit-stage and pre-push pytest invocations that already exclude `system_local` MUST continue to succeed without Docker
and without pulling or running `arc-export`. Operators MUST be able to run the suite explicitly with `system_local`
selected when Docker is available.

#### Scenario: Pre-push stays Docker-free

- **WHEN** pre-push runs its default pytest marker expression excluding `system_local`
- **THEN** the arc-export fixture tests are not executed

### Requirement: CI runs arc-export fixture tests with Docker

A Feature-PR CI path with Docker available SHALL execute the `system_local` arc-export fixture suite. The `arc-export`
image reference SHOULD be overridable (for example via `FAIRAGRO_ARC_EXPORT_IMAGE`) and SHOULD be pinned for
reproducibility in CI (digest recommended).

#### Scenario: Feature PR job runs the suite

- **WHEN** a Feature PR changes code and the arc-export fixture CI job runs
- **THEN** the `system_local` fixture suite is executed against Docker

### Requirement: Document how to add a fixture after a DataHUB failure

Project documentation SHALL state that these tests need Docker, and SHALL describe how to add a new per-RDI fixture when
a production or DataHUB `arc-export` failure appears (failing test first, then mapping fix).

#### Scenario: Doc covers Docker and regression loop

- **WHEN** a developer reads the documented arc-export fixture guidance
- **THEN** Docker requirement and the “add fixture on DataHUB failure” loop are described
