# Principles (payload / module graph)

## Purpose

Normative module-dependency and extension-point rules for the shared `middleware.payload` package. Narrative product
overlay remains in `openspec/principles.md`.

## Requirements

### Requirement: Shared payload package owns cross-cutting mappers

The system SHALL provide a `middleware.payload` workspace package that owns intermediate-payload contracts
(`PayloadKind`, `ParsedPayload`) and shared `DataMapper` implementations (including RDF `LinkedDataMapper` /
`StableGraph` and vocabulary mappers). Shared discovery-unit types and `PayloadParser` implementations SHALL live in
`middleware.parsing` (not in `middleware.payload` and not in a single protocol plugin). Protocol plugins MAY depend on
`middleware.payload` and `middleware.parsing`. `middleware.payload` MUST NOT depend on `middleware.parsing` or on
protocol plugin packages (`inspire`, `linked_data`, `generic`, …). The orchestrator MAY depend on `middleware.payload`
for mapper config types and on `middleware.parsing` when validating parser registries.

#### Scenario: Dependency direction

- **WHEN** module dependencies are reviewed
- **THEN** plugins import `middleware.payload` for mapping and `middleware.parsing` for parsers/discovery units, and
  `middleware.payload` does not import those plugins or `middleware.parsing`

#### Scenario: Parsing package is the parser home

- **WHEN** a shared PayloadParser is registered
- **THEN** it is owned by `middleware.parsing` and selectable via the repository `parser.type` value without residing
  under `middleware.generic`

### Requirement: Extension point for new mapper types

When adding a new vocabulary→ARC mapper that reuses an existing `PayloadKind`, implementations SHALL register a new
mapper type in `middleware.payload` and expose it via repository `mapper.type`, without requiring orchestrator changes
beyond config schema registration of mapper config fields if needed.

#### Scenario: New rdf_graph mapper

- **WHEN** a new RDF vocabulary mapper is added for `PayloadKind.rdf_graph`
- **THEN** it is registered in `middleware.payload` and selectable via `mapper.type`
