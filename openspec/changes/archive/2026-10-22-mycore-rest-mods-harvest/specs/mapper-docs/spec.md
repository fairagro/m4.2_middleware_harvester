## MODIFIED Requirements

### Requirement: Central mapper documentation layout

The system SHALL keep authoritative source→ARC mapping documents under `docs/mappers/`, with one base document per
productive format/vocabulary mapper and optional RDI override documents under `docs/mappers/rdi/`. Base documents MUST
describe the full mapping for that mapper. RDI override documents MUST describe only deltas relative to a named base
(`builds_on`) and MUST NOT restate the entire base mapping. Productive base mappers documented this way include at least
Schema.org, Regal, INSPIRE, PhenoRoam, CKAN `ckanext-dcat`, and MODS (`mods.md` / `mods_general`).

#### Scenario: Base mapper document location

- **WHEN** a productive base mapper (Schema.org, Regal, INSPIRE, PhenoRoam, CKAN `ckanext-dcat`, or MODS) is documented
- **THEN** its authoritative field tables and mapping rules live under `docs/mappers/` (not under a legacy flat
  `docs/*_mapping.md` path)

#### Scenario: RDI overlay is delta-only

- **WHEN** an RDI-specific mapping document is published under `docs/mappers/rdi/`
- **THEN** it declares which base mapper it builds on and lists only overrides, additional source conventions, disabled
  base rules, and additional refusal/skip rules

#### Scenario: MODS base document

- **WHEN** `mods_general` is a productive mapper
- **THEN** `docs/mappers/mods.md` exists as its authoritative base mapping document
