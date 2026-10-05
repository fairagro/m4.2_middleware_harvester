# Spec Delta

## Purpose

Defines where mapper documentation lives, how base vs RDI-override documents are structured, and that those Markdown
files are the authoritative source→ARC contract and the intended (not yet automated) input for future code generation.

## ADDED Requirements

### Requirement: Central mapper documentation layout

The system SHALL keep authoritative source→ARC mapping documents under `docs/mappers/`, with one base document per
productive format/vocabulary mapper and optional RDI override documents under `docs/mappers/rdi/`. Base documents MUST
describe the full mapping for that mapper. RDI override documents MUST describe only deltas relative to a named base
(`builds_on`) and MUST NOT restate the entire base mapping.

#### Scenario: Base mapper document location

- **WHEN** a productive base mapper (Schema.org, Regal, INSPIRE, PhenoRoam, or CKAN `ckanext-dcat`) is documented
- **THEN** its authoritative field tables and mapping rules live under `docs/mappers/` (not under a legacy flat
  `docs/*_mapping.md` path)

#### Scenario: RDI overlay is delta-only

- **WHEN** an RDI-specific mapping document is published under `docs/mappers/rdi/`
- **THEN** it declares which base mapper it builds on and lists only overrides, additional source conventions, disabled
  base rules, and additional refusal/skip rules

### Requirement: Mapping documents speak payload semantics, not StableGraph

Mapping documents under `docs/mappers/` MUST describe source semantics in the mapper's payload language (RDF vocabulary
terms, `InspireRecord` fields, or `phenoroam_record` fields) and ARC targets. They MUST NOT prescribe StableGraph /
`ResourceView` implementation details. Feature specs MAY assume stable RDF access (for example a canonical literal)
without documenting the access layer.

#### Scenario: StableGraph stays out of mapping docs

- **WHEN** a contributor documents a Schema.org or Regal field mapping
- **THEN** the mapping document names RDF predicates and ARC targets, not StableGraph APIs

### Requirement: Mapping Markdown is authoritative and generation input

Every productive DataMapper MUST reference exactly one authoritative mapping document under `docs/mappers/` (a base
document, or a base plus an RDI override pair). Feature specs MUST link to those documents and MUST NOT duplicate field
tables. The Markdown documents SHALL be treated as the intended input for a future code generator; this repository MUST
NOT require an implemented generator for the documentation layout to be valid.

#### Scenario: Spec links instead of restating tables

- **WHEN** a mapping-domain feature spec cites field placement rules
- **THEN** it references the corresponding `docs/mappers/` document rather than copying the field table

#### Scenario: Code generation remains future work

- **WHEN** the mapper-docs layout is adopted
- **THEN** no automated Markdown→mapper code generator is required to exist; the generation-input role is documented
  only
