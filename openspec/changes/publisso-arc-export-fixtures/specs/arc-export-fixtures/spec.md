## MODIFIED Requirements

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

#### Scenario: Edal real-data suite is multi-case

- **WHEN** the edal real-data suite has landed under the arc-export fixture tree
- **THEN** more than one real mapped RO-Crate case is present for edal under
  `fixtures/arc_export/edal/<case-id>/ro-crate-metadata.json` (or a single case is explicitly documented as temporarily
  covering the full curated breadth with a follow-up to expand), docs/`README` state which e!DAL input features each
  file covers (for example license placeholder, person/ORCID or flat address, organization-only, DOI/`@id` edges), and
  `docs/arc-export-fixtures.md` no longer lists edal as deferred-only

#### Scenario: Publisso real-data suite is multi-case

- **WHEN** the publisso real-data suite has landed under the arc-export fixture tree
- **THEN** more than one real mapped RO-Crate case is present for publisso under
  `fixtures/arc_export/publisso/<case-id>/ro-crate-metadata.json` (or a single case is explicitly documented as
  temporarily covering the full curated breadth with a follow-up to expand), docs/`README` state which Regal/PUBLISSO
  input features each file covers (for example person/agent given-name edges, license, subjects±DDC, funding), the
  optional root smoke crate MAY remain, and `docs/arc-export-fixtures.md` no longer lists publisso as deferred-only

#### Scenario: Synthetic-only Investigation is not sufficient for a landed real-data suite

- **WHEN** a landed real-data suite folder for an active RDI is inspected
- **THEN** at least one fixture in that suite MUST originate from a real source record mapping (smoke crates alone do
  not satisfy the suite)
