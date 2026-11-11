# ARC Export Fixtures

## Purpose

Gates representative per-RDI RO-Crate fixtures with the same DataHUB `arc-export` check (via shared arc-validation)
under `system_local` tests and a Docker-capable CI job, so client CI catches export failures before upload.

## Requirements

### Requirement: Per-RDI RO-Crate fixtures exist for active mapper families

The repository SHALL commit RO-Crate fixtures under a stable per-RDI path (for example
`tests/fixtures/arc_export/<rdi>/…`) for each **active RDI** used in harvest comparison configs (enabled entries in
`dev_environment/config.all-rdis.yaml`, plus any RDI this capability explicitly tracks as active). Fixtures MAY use Git
LFS when size warrants it. Technology family (INSPIRE, Schema.org, Regal, DCAT, OAI-PMH, …) MUST NOT be used as a
substitute for a missing per-RDI suite: RDIs that share a mapper family MAY still require distinct fixture sets. Minimal
synthetic smoke crates MAY remain alongside real-data sets.

#### Scenario: Three family fixtures present

- **WHEN** a developer inspects the fixture tree for this capability
- **THEN** there is at least one RO-Crate artifact for an INSPIRE-shaped RDI, one for a Schema.org/generic-shaped RDI,
  and one for a Regal-shaped RDI

#### Scenario: Active RDI folders are present when suites are claimed complete

- **WHEN** a developer inspects the fixture tree after all planned RDI suites for this capability have landed
- **THEN** there is at least one RO-Crate artifact path for each active RDI covered by the landed suites (not merely one
  folder per technology family)

#### Scenario: Three family smoke fixtures remain allowed

- **WHEN** only the MVP smoke crates for bonares / openagrar / publisso exist and real-data suites for other RDIs are
  still deferred
- **THEN** the smoke crates alone MUST still satisfy the historical three-family presence check used by `system_local`
  until those RDIs’ real-data suites replace or extend them

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

### Requirement: Real-data fixture sets MUST cover RDI input feature breadth

For each active RDI whose real-data suite has landed, the repository MUST commit a **set** of RO-Crate fixtures derived
from **real** source records (live or archived harvest inputs) mapped through the real client mapping path — not
synthetic one-field Investigations. The set MUST exercise the feature breadth of that RDI’s input shapes as used in
harvest/mapping (contacts, licenses, keywords, spatial, nested plugin fields, and other RDI-specific edges as
applicable). Project documentation MUST describe which cases each fixture file covers. Prefer failing-test-first when a
production or `arc-export` gap appears.

#### Scenario: Bonares real-data suite is multi-case

- **WHEN** the bonares real-data suite has landed under the arc-export fixture tree
- **THEN** more than one real mapped RO-Crate case is present for bonares (or a single case is explicitly documented as
  temporarily covering the full curated breadth with a follow-up to expand), and docs state which input features each
  file covers

#### Scenario: Synthetic-only Investigation is not sufficient for a landed real-data suite

- **WHEN** a landed real-data suite folder for an active RDI is inspected
- **THEN** at least one fixture in that suite MUST originate from a real source record mapping (smoke crates alone do
  not satisfy the suite)

### Requirement: Document real-data fixture generation and redaction

`docs/arc-export-fixtures.md` MUST describe how to generate real-data fixtures (curate source → map via real client path
→ commit), when to use Git LFS, and any redaction/anonymisation rules. The existing Docker / regression-loop guidance
MUST remain.

#### Scenario: Doc covers generation and redaction

- **WHEN** a developer reads `docs/arc-export-fixtures.md`
- **THEN** real-data generation, optional LFS, redaction notes, and the DataHUB failure add-fixture loop are described
